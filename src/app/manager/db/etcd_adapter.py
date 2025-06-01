import json
import time
from typing import Any

import etcd3
import pandas as pd
from src.app.config.log import get_logger
from src.app.core.scenario_steps import CreateTableStep, InsertDataStep, QueryStep
from src.app.manager.db.base_adapter import BaseAdapter
from src.app.manager.db.utils import generate_csv

logger = get_logger(__name__)


class EtcdAdapter(BaseAdapter):
    """
    Адаптер key-value уровня etcd.
    Сохраняем каждую «строку» как JSON в ключе <table>:row:<n>,
    схему – в <table>:schema.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 2379,
        user: str | None = None,
        password: str | None = None,
        timeout: int = 5,
    ) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.timeout = timeout
        self.client: etcd3.Etcd3Client | None = None

    # ---------- infra ----------
    def connect(self, **kwargs) -> None:
        try:
            self.client = etcd3.client(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                timeout=self.timeout,
            )
            # «ping»
            self.client.status()
            logger.info("Подключение к etcd %s:%s успешно.", self.host, self.port)
        except Exception as e:  # gRPC ошибки идут как generic Exception
            logger.exception("Ошибка при подключении к etcd: %s", e)
            raise ConnectionError("Не удалось подключиться к etcd.") from e

    def test_connection(self, retries: int = 5, delay: int = 2) -> bool:
        if not self.client:
            logger.error("etcd client не инициализирован. Сначала вызовите connect().")
            return False

        for attempt in range(1, retries + 1):
            try:
                self.client.status()
                return True
            except Exception as e:
                logger.warning("Провал status() (попытка %d): %s", attempt, e)
                time.sleep(delay)
        return False

    # ---------- «DDL» ----------
    def create_table(self, create_table_step: CreateTableStep) -> None:
        """
        Храним схему как JSON-строку; etcd – schemaless,
        но для унификации этого достаточно.
        """
        self._require_client()

        schema_key = f"{create_table_step.table_name}:schema"
        schema_json = json.dumps(
            {c: d.data_type for c, d in create_table_step.columns.items()},
        )
        self.client.put(schema_key, schema_json)
        logger.info("Схема %s записана: %s", schema_key, schema_json)

    def drop_table_if_exists(self, table_name: str) -> None:
        """Удаляем и схему, и все строки row:* одним delete_prefix."""
        self._require_client()

        self.client.delete_prefix(f"{table_name}:")
        logger.info("Удалён префикс %s:* (таблица очищена).", table_name)

    # ---------- «DML» ----------
    def insert_data(self, insert_step: InsertDataStep) -> None:
        """
        CSV-генератор → JSON-объекты → put с префиксом row:<idx>.
        Используем batch через transact() для ускорения.
        """
        self._require_client()

        csv_file = generate_csv(insert_step.num_records, insert_step.columns)
        df = pd.read_csv(csv_file)

        # etcd транзакция ограничена 128 операций. Разобьём на чанки.
        BATCH = 120
        for start in range(0, len(df), BATCH):
            ops = []
            for idx, row in df.iloc[start : start + BATCH].iterrows():
                key = f"{insert_step.table_name}:row:{idx}"
                ops.append(
                    self.client.transactions.put(
                        key,
                        row.to_json(date_format="iso"),
                    ),
                )
            self.client.transaction(
                compare=[],
                success=ops,
                failure=[],
            )
        logger.info("Вставлено %d строк(и) в %s.", len(df), insert_step.table_name)

    # ---------- «SQL» / QueryStep ----------
    def execute_query(self, query_step: QueryStep) -> Any:
        """
        Мини-парсер CLI-команд etcdctl-стиля:
          * GET <key>
          * RANGE <prefix>
          * DELETE <key|prefix>
        Команды чувствительны к регистру.
        """
        self._require_client()

        tokens = query_step.query.strip().split(maxsplit=1)
        if not tokens:
            logger.warning("Пустой запрос etcd.")
            return None

        cmd = tokens[0].upper()
        arg = tokens[1] if len(tokens) > 1 else ""

        try:
            if cmd == "GET":
                value, _ = self.client.get(arg)
                return value.decode() if value else None

            if cmd == "RANGE":
                return [
                    (k.decode(), v.decode()) for k, v in self.client.get_prefix(arg)
                ]

            if cmd == "DELETE":
                if arg.endswith("*"):
                    prefix = arg[:-1]
                    return self.client.delete_prefix(prefix)
                return self.client.delete(arg)

            raise ValueError(f"Неизвестная команда: {cmd}")

        except Exception as e:
            logger.exception(
                "Ошибка при выполнении etcd-команды '%s': %s",
                query_step.query,
                e,
            )
            raise

    # ---------- util ----------
    def _require_client(self) -> None:
        if not self.client:
            raise ConnectionError("etcd client не создан: вызовите connect().")

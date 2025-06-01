import json
import time
from typing import Any

import pandas as pd
import redis
from src.app.config.log import get_logger
from src.app.core.scenario_steps import CreateTableStep, InsertDataStep, QueryStep
from src.app.manager.db.base_adapter import BaseAdapter
from src.app.manager.db.utils import generate_csv

logger = get_logger(__name__)


class RedisAdapter(BaseAdapter):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
    ) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.client: redis.Redis | None = None

    def connect(self, **kwargs) -> None:
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                ssl_cert_reqs=None,
                decode_responses=True,
            )
            self.client.ping()
            logger.info("Подключение к Redis %s:%s успешно.", self.host, self.port)
        except redis.RedisError as e:
            logger.exception("Ошибка при подключении к Redis: %s", e)
            raise ConnectionError("Не удалось подключиться к Redis.") from e

    def test_connection(self, retries: int = 5, delay: int = 2) -> bool:
        if not self.client:
            logger.error("Redis client не инициализирован ‒ вызовите connect().")
            return False

        for attempt in range(1, retries + 1):
            try:
                self.client.ping()
                return True
            except redis.RedisError as e:
                logger.warning("PING к Redis не прошёл (попытка %d): %s", attempt, e)
                time.sleep(delay)
        return False

    def create_table(self, create_table_step: CreateTableStep) -> None:
        """Храним схему в ключе <table>:schema"""
        self._require_client()

        key = f"{create_table_step.table_name}:schema"
        schema = {
            col: col_def.data_type for col, col_def in create_table_step.columns.items()
        }
        self.client.set(key, json.dumps(schema))
        logger.info("Схема %s создана/заменена.", key)

    def drop_table_if_exists(self, table_name: str) -> None:
        """Удаляем и схему, и все строки table_name:*."""
        self._require_client()

        pipe = self.client.pipeline()
        pipe.delete(f"{table_name}:schema")

        # собираем все ключи пачкой и удаляем
        for k in self.client.scan_iter(match=f"{table_name}:row:*"):
            pipe.delete(k)
        pipe.execute()
        logger.info("Таблица %s удалена (с ключами row:*).", table_name)

    def insert_data(self, insert_step: InsertDataStep) -> None:
        self._require_client()

        csv_file = generate_csv(insert_step.num_records, insert_step.columns)
        df = pd.read_csv(csv_file)

        pipe = self.client.pipeline()
        for idx, row in df.iterrows():
            key = f"{insert_step.table_name}:row:{idx}"
            pipe.hset(key, mapping=row.astype(str).to_dict())
        pipe.execute()
        logger.info("Вставлено %d строк(и) в %s.", len(df), insert_step.table_name)

    def execute_query(self, query_step: QueryStep) -> Any:
        """
        Пользователь передаёт строку ровно в том же виде,
        как в redis-cli. Мы разбираем её на токены и прокидываем
        в .execute_command().
        Пример: 'HGET users:row:0 name'
        """
        self._require_client()

        cmd_line = query_step.query.strip()
        if not cmd_line:
            logger.warning("Пустой запрос получен.")
            return None

        try:
            tokens = cmd_line.split()
            command, *args = tokens
            result = self.client.execute_command(command, *args)
            logger.info("Redis-команда выполнена: %s", cmd_line)
            return result
        except redis.RedisError as e:
            logger.exception(
                "Ошибка при выполнении Redis-команды '%s': %s",
                cmd_line,
                e,
            )
            raise

    def _require_client(self) -> None:
        if not self.client:
            raise ConnectionError("Redis client не создан: вызовите connect().")

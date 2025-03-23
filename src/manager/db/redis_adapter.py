import time
from typing import Any

import pandas as pd
import redis

from src.config.log import get_logger
from src.manager.db.base_adapter import BaseAdapter
from src.schemas.enums import DataType

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
        self.client = None

    def connect(self, **kwargs) -> None:
        """
        Подключаемся к Redis по заданному хосту и порту.
        """

        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
            )
            # Проверим подключение, выполнив простую команду
            self.client.ping()
            logger.info(f"Подключение к Redis {self.host}:{self.port} успешно.")
        except redis.RedisError as e:
            logger.exception(f"Ошибка при подключении к Redis: {e}")
            msg = "Не удалось подключиться к Redis."
            raise ConnectionError(msg)

    def test_connection(self, retries: int = 5, delay: int = 2) -> bool:
        """
        Аналогично SQLAdapter, несколько попыток проверить подключение (PING).
        """
        if not self.client:
            logger.error("Redis client не инициализирован. Сначала вызовите connect().")
            return False

        for attempt in range(retries):
            try:
                self.client.ping()
                logger.info("Подключение к Redis успешно.")
                return True
            except redis.RedisError as e:
                logger.warning(f"Ошибка при PING к Redis (попытка {attempt+1}): {e}")
                time.sleep(delay)

        logger.error(f"Не удалось подключиться к Redis за {retries} попыток.")
        return False

    def create_table(self, table_name: str, columns: dict[str, DataType]) -> None:
        """
        У Redis нет понятия таблиц, но для демонстрации мы можем:
        1) Создать некий HSET (таблицу) с ключом table_name;
        2) Хранить список полей columns в неком ключе metadata.

        В реальном проекте придется адаптировать под нужный use-case.
        """
        if not self.client:
            msg = "Redis client не создан. Вызовите connect()."
            raise ConnectionError(msg)

        # Например, сохраним в специальном ключе: f"{table_name}:schema"
        schema_key = f"{table_name}:schema"
        columns_str = ",".join([f"{col}:{typ}" for col, typ in columns.items()])
        try:
            self.client.set(schema_key, columns_str)
            logger.info(
                f"Имитация создания структуры '{table_name}' в Redis: {columns_str}",
            )
        except redis.RedisError as e:
            logger.exception(f"Ошибка при имитации create_table для Redis: {e}")

    def drop_table_if_exists(self, table_name: str) -> None:
        """
        Имитация 'удаления таблицы' — удаляем все ключи, связанные с table_name.
        """
        if not self.client:
            msg = "Redis client не создан. Вызовите connect()."
            raise ConnectionError(msg)

        # Удаляем metadata ключ
        schema_key = f"{table_name}:schema"
        try:
            self.client.delete(schema_key)
            logger.info(f"Удалена схема '{schema_key}' в Redis (если существовала).")
        except redis.RedisError as e:
            logger.exception(f"Ошибка при удалении схемы {schema_key}: {e}")

        # Опционально: если мы храним сами данные в виде (table_name:rowN), то их тоже нужно удалить
        # ...

    def insert_data(self, table_name: str, df: pd.DataFrame) -> None:
        """
        Так как Redis не SQL, сделаем упрощенный пример:
        Каждая строка df станет записью в HSET, ключ: f'{table_name}:rowN'
        """
        if not self.client:
            msg = "Redis client не создан. Вызовите connect()."
            raise ConnectionError(msg)

        try:
            for idx, row in df.iterrows():
                key = f"{table_name}:row:{idx}"
                # Преобразуем row в словарь
                row_dict = row.to_dict()
                # Записываем HSET
                self.client.hset(
                    name=key,
                    mapping={str(k): str(v) for k, v in row_dict.items()},
                )
            logger.info(f"Вставлено {len(df)} строк(и) в {table_name} (Redis).")
        except redis.RedisError as e:
            logger.exception(f"Ошибка при вставке данных в Redis: {e}")

    def execute_query(self, query: str) -> Any:
        """
        В Redis нет SQL-запросов, поэтому либо нужно интерпретировать запросы
        (что сложно), либо предоставлять другой метод для работы.

        Для примера вернем заглушку.
        """
        logger.warning("Redis не поддерживает SQL. Метод execute_query вернет None.")
        return None

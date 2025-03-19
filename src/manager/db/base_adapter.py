from typing import Any

import pandas as pd

from src.config.log import get_logger

logger = get_logger(__name__)


class BaseAdapter:
    def __init__(self) -> None:
        pass

    def connect(self, **kwargs) -> None:
        """Устанавливает подключение к базе данных / серверу."""
        raise NotImplementedError

    def test_connection(self, retries: int = 5, delay: int = 2) -> bool:
        """
        Тест подключения к БД/сервису.
        """
        raise NotImplementedError

    def create_table(self, table_name: str, columns: dict[str, str]) -> None:
        """
        Создание таблицы или эквивалентной структуры (если NoSQL).
        """
        raise NotImplementedError

    def drop_table_if_exists(self, table_name: str) -> None:
        """Удалить таблицу/структуру, если существует."""
        raise NotImplementedError

    def insert_data(self, table_name: str, df: pd.DataFrame) -> None:
        """Вставка данных из DataFrame."""
        raise NotImplementedError

    def execute_query(self, query: str) -> Any:
        """Выполнить запрос и вернуть результат (если есть)."""
        raise NotImplementedError

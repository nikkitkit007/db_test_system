from typing import Any

from src.config.log import get_logger
from src.core.scenario_steps import CreateTableStep, InsertDataStep, QueryStep

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

    def create_table(self, create_table_step: CreateTableStep) -> None:
        """
        Создание таблицы или эквивалентной структуры (если NoSQL).
        """
        raise NotImplementedError

    def drop_table_if_exists(self, table_name: str) -> None:
        """Удалить таблицу/структуру, если существует."""
        raise NotImplementedError

    def insert_data(
        self,
        insert_step: InsertDataStep,
    ) -> None:
        raise NotImplementedError

    def execute_query(self, query_step: QueryStep) -> Any:
        """Выполнить запрос и вернуть результат (если есть)."""
        raise NotImplementedError

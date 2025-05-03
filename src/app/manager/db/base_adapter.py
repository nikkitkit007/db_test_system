from abc import ABC
from typing import Any

from src.app.config.log import get_logger
from src.app.core.scenario_steps import CreateTableStep, InsertDataStep, QueryStep

logger = get_logger(__name__)


class BaseAdapter(ABC):
    def __init__(self) -> None:
        pass

    def connect(self, **kwargs) -> None:
        raise NotImplementedError

    def test_connection(self, retries: int = 5, delay: int = 2) -> bool:
        raise NotImplementedError

    def create_table(self, create_table_step: CreateTableStep) -> None:
        raise NotImplementedError

    def drop_table_if_exists(self, table_name: str) -> None:
        raise NotImplementedError

    def insert_data(
        self,
        insert_step: InsertDataStep,
    ) -> None:
        raise NotImplementedError

    def execute_query(self, query_step: QueryStep) -> Any:
        raise NotImplementedError

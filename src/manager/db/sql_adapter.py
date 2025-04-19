import time
from functools import wraps
from typing import Any

import pandas as pd
from sqlalchemy import (
    Column,
    MetaData,
    Table,
    create_engine,
    text,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from src.config.log import get_logger
from src.core.scenario_steps import CreateTableStep, InsertDataStep, QueryStep
from src.manager.db.base_adapter import BaseAdapter
from src.manager.db.utils import generate_csv
from src.schemas.enums import sql_type_mapping

logger = get_logger(__name__)


def require_engine(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not getattr(self, "engine", None):
            msg = "Движок не создан. Сначала вызовите connect()."
            raise ConnectionError(msg)
        return method(self, *args, **kwargs)

    return wrapper


class SQLAdapter(BaseAdapter):
    def __init__(
        self,
        db_type: str,
        driver: str | None = None,
        username: str | None = None,
        password: str | None = None,
        host: str | None = None,
        port: str | None = None,
        db_name: str | None = None,
    ) -> None:
        super().__init__()
        self.db_type = db_type.lower().strip()
        self.driver = (driver or "").strip()
        self.username = username or ""
        self.password = password or ""
        self.host = host or ""
        self.port = port or 0
        self.db_name = db_name or ""
        self.engine = None
        self.Session = None
        self.metadata = MetaData()

    def connect(self, **kwargs) -> None:
        """
        Создаёт движок (engine) с помощью SQLAlchemy и проверяет подключение.
        """
        # Формируем db_scheme
        if "+" in self.db_type or self.driver:
            db_scheme = self.db_type
            if self.driver and "+" not in db_scheme:
                db_scheme = f"{self.db_type}+{self.driver}"
        else:
            db_scheme = self.db_type

        # Формируем URL подключения
        if self.db_type.startswith("sqlite"):
            db_url = f"sqlite:///{self.db_name}"
        else:
            db_url = f"{db_scheme}://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"

        try:
            self.engine = create_engine(db_url)
            self.Session = sessionmaker(bind=self.engine)
            logger.info(f"Создан движок для {db_url}")
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка при создании engine: {e}")
            raise

        time.sleep(2)
        if not self.test_connection():
            msg = f"Не удалось подключиться к базе {db_url}."
            raise ConnectionError(msg)

    @require_engine
    def test_connection(self, retries: int = 6, delay: int = 2) -> bool:
        for attempt in range(1, retries + 1):
            try:
                with self.engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                logger.info("Подключение к базе данных успешно.")
                return True
            except SQLAlchemyError as e:
                logger.warning(f"Ошибка при подключении (попытка {attempt}): {e}")
                time.sleep(delay)

        logger.error(f"Не удалось подключиться к базе за {retries} попыток.")
        return False

    @require_engine
    def create_table(self, create_table_step: CreateTableStep) -> None:
        table_name = create_table_step.table_name
        self.drop_table_if_exists(table_name)

        table_columns = (
            Column(
                column_name,
                sql_type_mapping[col_def.data_type.lower()],
                primary_key=col_def.primary_key,
            )
            for column_name, col_def in create_table_step.columns.items()
        )
        table = Table(
            table_name,
            self.metadata,
            *table_columns,
            extend_existing=True,
        )

        try:
            table.create(self.engine)
            logger.info(f"Таблица {table_name} создана.")
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка при создании таблицы {table_name}: {e}")

    @require_engine
    def drop_table_if_exists(self, table_name: str) -> None:
        table = Table(table_name, self.metadata)
        try:
            table.drop(self.engine, checkfirst=True)
            logger.info(f"Таблица {table_name} удалена (если существовала).")
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка при удалении таблицы {table_name}: {e}")

    @require_engine
    def insert_data(
        self,
        insert_step: InsertDataStep,
    ) -> None:
        table_name = insert_step.table_name
        columns = insert_step.columns
        num_records = insert_step.num_records

        csv_file = generate_csv(num_records, columns)
        df = pd.read_csv(csv_file)
        try:
            df.to_sql(table_name, self.engine, if_exists="append", index=False)
            logger.info(f"Данные вставлены в таблицу {table_name}.")
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка при вставке данных в {table_name}: {e}")

    @require_engine
    def execute_query(self, query_step: QueryStep) -> Any:
        result = None
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query_step.query))
            logger.info(f"Запрос выполнен: {query_step.query}")
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка при выполнении запроса: {e}")

        return result

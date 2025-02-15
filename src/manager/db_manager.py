import time
from typing import Any

import pandas as pd
from sqlalchemy import Column, Date, Integer, MetaData, String, Table, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from src.config.log import get_logger

logger = get_logger(__name__)

type_mapping = {
    "int": Integer,
    "str": String,
    "date": Date,
}


class DatabaseManager:
    def __init__(
            self,
            db_type: str,
            username: str,
            password: str,
            host: str,
            port: int,
            db_name: str,
    ) -> None:
        self.db_type = db_type
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.db_name = db_name
        self.engine = self.create_engine()
        self.Session = sessionmaker(bind=self.engine)
        self.metadata = MetaData()

        if not self.test_connection():
            logger.error("Не удалось подключиться к базе данных после нескольких попыток.")
            msg = "Failed to connect to the database."
            raise ConnectionError(msg)

    def create_engine(self):
        db_url = f"{self.db_type}://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"
        return create_engine(db_url)

    def create_table(self, table_name: str, columns: dict[str, str]) -> None:
        self.drop_table_if_exists(table_name)

        table_columns = (Column(column_name, type_mapping[column_type.lower()]) for column_name, column_type in
                         columns.items())
        table = Table(
            table_name,
            self.metadata,
            *table_columns,
            extend_existing=True,
        )
        table.create(self.engine)
        logger.info(f"Таблица {table_name} создана.")

    def insert_data(self, table_name: str, df: pd.DataFrame) -> None:
        """
        Вставляет данные в таблицу из DataFrame.
        """
        try:
            df.to_sql(table_name, self.engine, if_exists="append", index=False)
            logger.info(f"Данные вставлены в таблицу {table_name}.")
        except SQLAlchemyError as e:
            logger.info(f"Ошибка при вставке данных в {table_name}: {e}")

    def execute_query(self, query: str) -> Any:
        """
        Выполняет SQL-запрос.
        """
        result = None
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
            logger.info(f"Запрос выполнен: {query}")
        except SQLAlchemyError as e:
            logger.info(f"Ошибка при выполнении запроса: {e}")

        return result

    def drop_table_if_exists(self, table_name: str) -> None:
        """
        Удаляет таблицу, если она существует.
        """
        table = Table(table_name, self.metadata)
        try:
            table.drop(self.engine, checkfirst=True)
            logger.info(f"Таблица {table_name} удалена.")
        except SQLAlchemyError as e:
            logger.info(f"Ошибка при удалении таблицы: {e}")

    def test_connection(self, retries: int = 5, delay: int = 2) -> bool:
        """
        Тестирует подключение к базе данных.
        """
        conn_error = None
        for _attempt in range(retries):
            try:
                with self.engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                    logger.info("Подключение к базе данных успешно.")
                    return True
            except SQLAlchemyError:
                time.sleep(delay)
        logger.info(f"Ошибка при подключении к базе данных: {conn_error}")
        return False


if __name__ == "__main__":
    db_image = "postgres:latest"
    db_container_name = "postgres_test"
    db_name = "test_db"
    db_user = "user"
    db_password = "example"
    db_host = "localhost"
    db_port = 5432

    # Параметры подключения к базе данных
    db_manager = DatabaseManager(
        db_type="postgresql",
        username=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        db_name=db_name,
    )
    # Тест подключения
    if db_manager.test_connection():
        logger.info("Тест подключения прошел успешно.")
    else:
        logger.info("Тест подключения не удался.")

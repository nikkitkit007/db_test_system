import time
from typing import Any

import pandas as pd
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    text,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from src.config.log import get_logger
from src.manager.db.base_adapter import BaseAdapter
from src.schemas.enums import DataType
from src.utils import generate_csv

logger = get_logger(__name__)

type_mapping = {"int": Integer, "str": String, "date": Date, "bool": Boolean}


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
        """
        :param db_type: например, 'postgresql', 'mysql', 'sqlite' и т.д.
        :param driver:  например, 'psycopg2' для postgresql, 'pymysql' для mysql.
        :param username: имя пользователя
        :param password: пароль
        :param host:     хост
        :param port:     порт
        :param db_name:  имя БД (или путь к файлу, если sqlite)
        """
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

        # Опционально: можем вызывать test_connection здесь
        if not self.test_connection():
            msg = f"Не удалось подключиться к базе {db_url}."
            raise ConnectionError(msg)

    def test_connection(self, retries: int = 5, delay: int = 2) -> bool:
        """
        Тест подключения: делаем несколько попыток выполнить SELECT 1.
        """
        if not self.engine:
            logger.error("Engine не инициализирован. Сначала вызовите connect()")
            return False
        time.sleep(1)
        for attempt in range(retries):
            try:
                with self.engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                logger.info("Подключение к базе данных успешно.")
                return True
            except SQLAlchemyError as e:
                logger.warning(f"Ошибка при подключении (попытка {attempt + 1}): {e}")
                time.sleep(delay)

        logger.error(f"Не удалось подключиться к базе за {retries} попыток.")
        return False

    def create_table(self, table_name: str, columns: dict[str, DataType]) -> None:
        """
        Создаёт таблицу с указанными колонками (dict column_name -> type).
        """
        if not self.engine:
            msg = "Движок не создан. Сначала вызовите connect()."
            raise ConnectionError(msg)

        self.drop_table_if_exists(table_name)

        table_columns = (
            Column(column_name, type_mapping[column_type.lower()])
            for column_name, column_type in columns.items()
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

    def drop_table_if_exists(self, table_name: str) -> None:
        """
        Удаляет таблицу, если существует.
        """
        if not self.engine:
            msg = "Движок не создан. Сначала вызовите connect()."
            raise ConnectionError(msg)

        table = Table(table_name, self.metadata)
        try:
            table.drop(self.engine, checkfirst=True)
            logger.info(f"Таблица {table_name} удалена (если существовала).")
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка при удалении таблицы {table_name}: {e}")

    def insert_data(
        self,
        table_name: str,
        columns: dict[str, DataType],
        num_records: int,
    ) -> None:
        """
        Вставляет данные из DataFrame в указанную таблицу (append-режим).
        """
        if not self.engine:
            msg = "Движок не создан. Сначала вызовите connect()."
            raise ConnectionError(msg)

        csv_file = generate_csv(num_records, columns)
        df = pd.read_csv(csv_file)
        try:
            df.to_sql(table_name, self.engine, if_exists="append", index=False)
            logger.info(f"Данные вставлены в таблицу {table_name}.")
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка при вставке данных в {table_name}: {e}")

    def execute_query(self, query: str) -> Any:
        """
        Выполняет SQL-запрос и возвращает результат (CursorResult).
        """
        if not self.engine:
            msg = "Движок не создан. Сначала вызовите connect()."
            raise ConnectionError(msg)

        result = None
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
            logger.info(f"Запрос выполнен: {query}")
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка при выполнении запроса: {e}")

        return result

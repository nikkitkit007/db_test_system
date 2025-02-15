import json
import sqlite3
from contextlib import contextmanager
from sqlite3 import Error

from sqlalchemy import create_engine, select
from sqlalchemy.orm import scoped_session, sessionmaker

from src.config.config import settings
from src.config.log import get_logger
from src.storage.model import DockerImage, TestResults

logger = get_logger(__name__)


class SQLiteManager:
    def __init__(self, db_file: str) -> None:
        self.db_file = db_file
        # self.conn = self.create_connection()
        self.engine = create_engine(db_file)
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    @contextmanager
    def session_scope(self):
        """Контекстный менеджер для сессии."""
        session = self.Session()
        session.expire_on_commit = False
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.exception(f"Ошибка при работе с сессией: {e}")
            raise
        finally:
            session.close()

    def create_connection(self):
        """Создание соединения с базой данных SQLite"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            logger.info(f"Соединение с базой данных SQLite {self.db_file} установлено.")
        except Error as e:
            logger.info(f"Ошибка при соединении с базой данных SQLite: {e}")
        return conn

    def insert_result(
        self,
        timestamp: str,
        db_image: str,
        operation: str,
        num_records: int,
        data_types: str,
        execution_time: float,
        memory_used: float,
    ):
        """Вставка записи в таблицу результатов тестов"""
        with self.session_scope() as session:
            new_result = TestResults(
                timestamp=timestamp,
                db_image=db_image,
                operation=operation,
                num_records=num_records,
                data_types=data_types,
                execution_time=execution_time,
                memory_used=memory_used,
            )
            session.add(new_result)
            logger.info("Запись успешно добавлена в базу данных.")
            return new_result.id

    def delete_result(self, record_id: int) -> None:
        """Удаление записи из таблицы результатов тестов по ID"""
        with self.session_scope() as session:
            result = session.get(TestResults, record_id)
            if result:
                session.delete(result)
                logger.info(f"Запись с ID {record_id} удалена из базы данных.")
            else:
                logger.warning(f"Запись с ID {record_id} не найдена.")

    def select_all_results(self) -> list[TestResults]:
        """Выбор всех записей из таблицы результатов тестов"""
        with self.session_scope() as session:
            results = session.scalars(select(TestResults)).all()
            logger.info("Получены все записи из базы данных.")
            return results

    def select_result_by_id(self, id: int):
        """Выбор записи из таблицы результатов тестов по ID"""
        with self.session_scope() as session:
            result = session.get(TestResults, id)
            if result:
                logger.info(f"Запись с ID {id} получена из базы данных.")
            else:
                logger.warning(f"Запись с ID {id} не найдена.")
            return result

    # -------------------------------------------------------------------------
    # Методы для работы с Docker-образами (DockerImage)
    # -------------------------------------------------------------------------

    def add_docker_image(self, name: str) -> int:
        """Добавляет новый Docker-образ в базу данных."""
        with self.session_scope() as session:
            if session.query(DockerImage).filter(DockerImage.name == name).first():
                msg = f"Образ с именем '{name}' уже существует."
                raise ValueError(msg)
            new_image = DockerImage(name=name)
            session.add(new_image)
            session.flush()  # Генерирует ID новой записи
            logger.info(f"Добавлен новый образ: {name}")
            return new_image.id

    def get_all_docker_images(self) -> list[DockerImage]:
        """Возвращает список всех Docker-образов."""
        with self.session_scope() as session:
            return session.query(DockerImage).all()

    def delete_docker_image(self, image_id: int) -> None:
        """Удаляет Docker-образ по ID."""
        with self.session_scope() as session:
            image = session.get(DockerImage, image_id)
            if not image:
                msg = f"Образ с ID {image_id} не найден."
                raise ValueError(msg)
            session.delete(image)
            logger.info(f"Удален образ с ID: {image_id}")

    def get_image_by_name(self, name: str):
        """Возвращает Docker-образ по имени."""
        with self.session_scope() as session:
            image = session.query(DockerImage).filter(DockerImage.name == name).first()
            if not image:
                msg = f"Образ с именем '{name}' не найден."
                raise ValueError(msg)
            return image

    def add_or_update_db_config(self, name: str, config_dict: dict) -> None:
        """
        Добавляет или обновляет JSON-конфигурацию (DB_CONFIGS-подобную) для Docker-образа.
        :param name: название Docker-образа
        :param config_dict: словарь вида:
            {
              "db_type": "...",
              "default_user": "...",
              "default_password": "...",
              "default_port": 1234,
              "default_db": "...",
              "env": {...},
              ...
            }
        """
        with self.session_scope() as session:
            image = session.query(DockerImage).filter(DockerImage.name == name).first()
            image.config = json.dumps(config_dict)
            logger.info(f"Обновлен config у Docker-образа '{name}'.")

    def get_db_config(self, name: str) -> dict:
        """
        Возвращает конфигурацию (JSON -> dict) для указанного Docker-образа.
        :param name: название Docker-образа
        :return: словарь config
        """
        image = self.get_image_by_name(name)
        return json.loads(image.config) if image.config else {}


sqlite_manager = SQLiteManager(settings.SQLITE_DB_URL)

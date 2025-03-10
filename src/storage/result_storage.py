from sqlalchemy import select

from src.config.config import settings
from src.config.log import get_logger
from src.storage.db import SQLiteDB
from src.storage.model import TestResults

logger = get_logger(__name__)


class ResultStorage(SQLiteDB):

    def insert_result(self, test_result: TestResults):
        """Вставка записи в таблицу результатов тестов"""
        with self.session_scope() as session:
            session.add(test_result)
            logger.info("Запись успешно добавлена в базу данных.")
            return test_result.id

    def delete_result(self, record_id: int) -> None:
        """Удаление записи из таблицы результатов тестов по ID"""
        with self.session_scope() as session:
            result = session.get(TestResults, record_id)
            if result:
                session.delete(result)
                logger.info(f"Запись с ID {record_id} удалена из базы данных.")
            else:
                logger.warning(f"Запись с ID {record_id} не найдена.")

    def select_all_results(self, db_image: str = None, operation: str = None) -> list[TestResults]:
        """Выбор всех записей из таблицы результатов тестов с опциональными фильтрами."""
        with self.session_scope() as session:
            query = select(TestResults)
            if db_image:
                query = query.where(TestResults.db_image == db_image)
            if operation:
                query = query.where(TestResults.operation == operation)
            results = session.scalars(query).all()
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

    def get_distinct_db_images(self):
        with self.session_scope() as session:
            rows = (
                session.query(TestResults.db_image)
                .distinct()
                .order_by(TestResults.db_image)
                .all()
            )
        return [row[0] for row in rows]

    def get_distinct_operations(self):
        with self.session_scope() as session:
            rows = (
                session.query(TestResults.operation)
                .distinct()
                .order_by(TestResults.operation)
                .all()
            )
        return [row[0] for row in rows]


result_manager = ResultStorage(settings.SQLITE_DB_URL)

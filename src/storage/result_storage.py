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


result_manager = ResultStorage(settings.SQLITE_DB_URL)

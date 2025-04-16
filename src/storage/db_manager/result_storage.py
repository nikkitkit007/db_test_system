from sqlalchemy import select

from src.config.config import settings
from src.config.log import get_logger
from src.storage.db_manager.db import SQLiteDB
from src.storage.model import TestResults

logger = get_logger(__name__)


class ResultStorage(SQLiteDB):

    def insert_result(self, test_result: TestResults):
        with self.session_scope() as session:
            session.add(test_result)
            return test_result.id

    def delete_result(self, record_id: int) -> None:
        with self.session_scope() as session:
            result = session.get(TestResults, record_id)
            if result:
                session.delete(result)

    def select_all_results(
        self,
        db_image: str | None = None,
        operation: str | None = None,
        sort: str | None = None,
        order: str | None = None,
    ) -> list[TestResults]:
        with self.session_scope() as session:
            query = select(TestResults)
            if db_image:
                query = query.where(TestResults.db_image == db_image)
            if operation:
                query = query.where(TestResults.operation == operation)

            if sort:
                sort_col = getattr(TestResults, sort, None)
                if sort_col is not None:
                    if order and order.lower() == "desc":
                        query = query.order_by(sort_col.desc())
                    else:
                        query = query.order_by(sort_col.asc())
            else:
                query = query.order_by(TestResults.timestamp.desc())
            return session.scalars(query).all()

    def select_result_by_id(self, result_id: int) -> TestResults:
        with self.session_scope() as session:
            return session.get(TestResults, result_id)

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

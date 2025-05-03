from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from src.app.config.log import get_logger

logger = get_logger(__name__)


class SQLiteDB:
    def __init__(self, db_file: str) -> None:
        self.db_file = db_file
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

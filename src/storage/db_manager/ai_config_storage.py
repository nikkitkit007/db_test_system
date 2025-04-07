import json
from typing import Any

from src.config.config import settings
from src.config.log import get_logger
from src.storage.db_manager.db import SQLiteDB
from src.storage.model import DockerImage, AiConfig

logger = get_logger(__name__)


class AiConfigStorage(SQLiteDB):
    def get_all_ai_configs(self) -> list[AiConfig]:
        with self.session_scope() as session:
            return session.query(AiConfig).all()

    def get_ai_config(
        self,
        ai_config_id: int | None = None,
        name: str | None = None,
    ) -> AiConfig:
        if ai_config_id is not None:
            query_filter = AiConfig.id == ai_config_id
        elif name is not None:
            query_filter = AiConfig.name == name
        else:
            msg = "Not filters"
            raise Exception(msg)

        with self.session_scope() as session:
            return session.query(AiConfig).filter(query_filter).first()

    def add_ai_config(self, ai_config: AiConfig) -> AiConfig:
        with self.session_scope() as session:
            session.add(ai_config)
            session.flush()
            return ai_config

    def update_ai_config(self, ai_config: AiConfig) -> AiConfig:
        with self.session_scope() as session:
            updated_ai_config = session.merge(ai_config)
            session.flush()
            return updated_ai_config

    def delete_ai_config(self, ai_config_id: int) -> None:
        with self.session_scope() as session:
            ai_config = session.get(AiConfig, ai_config_id)
            if not ai_config:
                msg = f"Конфиг с ID {ai_config_id} не найден."
                raise ValueError(msg)
            session.delete(ai_config)


ai_config_db_manager = AiConfigStorage(settings.SQLITE_DB_URL)

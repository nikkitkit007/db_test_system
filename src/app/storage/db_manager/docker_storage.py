import datetime
import json
from typing import Any

from src.app.config.config import settings
from src.app.config.log import get_logger
from src.app.storage.db_manager.db import SQLiteDB
from src.app.storage.model import DockerImage

logger = get_logger(__name__)


class DockerStorage(SQLiteDB):

    def add_docker_image(self, docker_image: DockerImage) -> DockerImage:
        with self.session_scope() as session:
            session.add(docker_image)
            session.flush()
            return docker_image

    def get_all_docker_images(self) -> list[DockerImage]:
        with self.session_scope() as session:
            return session.query(DockerImage).all()

    def delete_docker_image(self, image_id: int) -> None:
        with self.session_scope() as session:
            image = session.get(DockerImage, image_id)
            if not image:
                msg = f"Образ с ID {image_id} не найден."
                raise ValueError(msg)
            session.delete(image)

    def get_image(
        self,
        image_id: int | None = None,
        config_name: str | None = None,
    ) -> DockerImage:
        if image_id is not None:
            query_filter = DockerImage.id == image_id
        elif config_name is not None:
            query_filter = DockerImage.config_name == config_name
        else:
            msg = "Not filters"
            raise Exception(msg)

        with self.session_scope() as session:
            image = session.query(DockerImage).filter(query_filter).first()
            if not image:
                msg = f"Образ с именем конфигурации '{config_name}' не найден."
                raise ValueError(msg)
            return image

    def add_or_update_db_config(self, config_name: str, config_dict: dict) -> None:
        with self.session_scope() as session:
            image = (
                session.query(DockerImage)
                .filter(DockerImage.config_name == config_name)
                .first()
            )
            if not image:
                msg = f"Образ с именем конфигурации '{config_name}' не найден."
                raise ValueError(
                    msg,
                )
            image.config = json.dumps(config_dict)
            image.updated_at = datetime.datetime.now(datetime.UTC)
            logger.info(f"Обновлен config у Docker-образа '{config_name}'.")

    def get_db_config(self, config_name: str) -> dict[str, Any]:
        image = self.get_image(config_name=config_name)
        return json.loads(image.config) if image.config else {}

    def update_docker_image(self, docker_image: DockerImage) -> DockerImage:
        with self.session_scope() as session:
            existing = session.get(DockerImage, docker_image.id)
            if not existing:
                msg = f"Образ с ID {docker_image.id} не найден."
                raise ValueError(msg)

            existing.image_name = docker_image.image_name
            existing.config_name = docker_image.config_name

            if isinstance(docker_image.config, dict):
                existing.config = json.dumps(docker_image.config)
            else:
                existing.config = docker_image.config

            existing.updated_at = datetime.datetime.now(datetime.UTC)
            session.flush()
            logger.info(f"Обновлен Docker-образ с ID {docker_image.id}.")
            return existing


docker_db_manager = DockerStorage(settings.SQLITE_DB_URL)

import json
from typing import Any

from src.config.config import settings
from src.config.log import get_logger
from src.storage.db_manager.db import SQLiteDB
from src.storage.model import DockerImage

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

    def get_image(self, image_id: int | None = None, name: str | None = None):
        if image_id is not None:
            query_filter = DockerImage.id == image_id
        elif name is not None:
            query_filter = DockerImage.name == name
        else:
            msg = "Not filters"
            raise Exception(msg)

        with self.session_scope() as session:
            image = session.query(DockerImage).filter(query_filter).first()
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

    def get_db_config(self, db_image_name: str) -> dict[str, Any]:
        image = self.get_image(name=db_image_name)
        return json.loads(image.config) if image.config else {}


docker_db_manager = DockerStorage(settings.SQLITE_DB_URL)

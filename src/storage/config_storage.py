import json
from typing import Any

from src.config.config import settings
from src.config.log import get_logger
from src.storage.db import SQLiteDB
from src.storage.model import DockerImage

logger = get_logger(__name__)


class ConfigStorage(SQLiteDB):

    # -------------------------------------------------------------------------
    # Методы для работы с Docker-образами (DockerImage)
    # -------------------------------------------------------------------------

    def add_docker_image(self, name: str) -> DockerImage:
        """Добавляет новый Docker-образ в базу данных."""
        with self.session_scope() as session:
            if session.query(DockerImage).filter(DockerImage.name == name).first():
                msg = f"Образ с именем '{name}' уже существует."
                raise ValueError(msg)
            new_image = DockerImage(name=name)
            session.add(new_image)
            session.flush()  # Генерирует ID новой записи
            logger.info(f"Добавлен новый образ: {name}")
            return new_image

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

    def get_db_config(self, db_image_name: str) -> dict[str, Any]:
        image = self.get_image_by_name(db_image_name)
        return json.loads(image.config) if image.config else {}


config_manager = ConfigStorage(settings.SQLITE_DB_URL)

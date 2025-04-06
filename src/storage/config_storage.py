import json
from typing import Any

from src.config.config import settings
from src.config.log import get_logger
from src.storage.db import SQLiteDB
from src.storage.model import AiConfig, DockerImage, Scenario

logger = get_logger(__name__)


class ConfigStorage(SQLiteDB):

    # -------------------------------------------------------------------------
    # Методы для работы с Docker-образами (DockerImage)
    # -------------------------------------------------------------------------

    def add_docker_image(self, docker_image: DockerImage) -> DockerImage:
        """Добавляет новый Docker-образ в базу данных."""
        with self.session_scope() as session:
            session.add(docker_image)
            session.flush()  # Генерирует ID новой записи
            logger.info(f"Добавлен новый образ: {docker_image.name}")
            return docker_image

    def get_all_docker_images(self) -> list[DockerImage]:
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

    def get_image(self, image_id: int | None = None, name: str | None = None):
        """Возвращает Docker-образ по имени."""
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

    # -------------------------------------------------------------------------
    # Методы для работы с Scenario
    # -------------------------------------------------------------------------

    def get_all_scenarios(self) -> list[Scenario]:
        with self.session_scope() as session:
            return session.query(Scenario).all()

    def get_scenario(
        self,
        scenario_id: int | None = None,
        name: str | None = None,
    ) -> Scenario:
        if scenario_id is not None:
            query_filter = Scenario.id == scenario_id
        elif name is not None:
            query_filter = Scenario.name == name
        else:
            msg = "Not filters"
            raise Exception(msg)

        with self.session_scope() as session:
            return session.query(Scenario).filter(query_filter).first()

    def add_scenario(self, scenario: Scenario) -> Scenario:
        with self.session_scope() as session:
            session.add(scenario)
            session.flush()  # Генерирует ID новой записи
            logger.info(f"Добавлен новый сценарий: {scenario.name}")
            return scenario

    def update_scenario(self, scenario: Scenario) -> Scenario:
        with self.session_scope() as session:
            updated_scenario = session.merge(scenario)
            session.flush()
            logger.info(f"Обновлен {updated_scenario.name}")
            return updated_scenario

    def delete_scenario(self, scenario_id: int) -> None:
        with self.session_scope() as session:
            image = session.get(Scenario, scenario_id)
            if not image:
                msg = f"Образ с ID {scenario_id} не найден."
                raise ValueError(msg)
            session.delete(image)
            logger.info(f"Удален образ с ID: {scenario_id}")

    # -------------------------------------------------------------------------
    # Методы для работы с AI
    # -------------------------------------------------------------------------

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
            logger.info(f"Добавлен новый конфиг: {ai_config.name}")
            return ai_config

    def update_ai_config(self, ai_config: AiConfig) -> AiConfig:
        with self.session_scope() as session:
            updated_ai_config = session.merge(ai_config)
            session.flush()
            logger.info(f"Обновлен {updated_ai_config.name}")
            return updated_ai_config

    def delete_ai_config(self, ai_config_id: int) -> None:
        with self.session_scope() as session:
            ai_config = session.get(AiConfig, ai_config_id)
            if not ai_config:
                msg = f"Конфиг с ID {ai_config_id} не найден."
                raise ValueError(msg)
            session.delete(ai_config)
            logger.info(f"Удален конфиг с ID: {ai_config_id}")


config_manager = ConfigStorage(settings.SQLITE_DB_URL)

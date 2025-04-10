import time

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container
from docker.models.images import Image

from src.config.log import get_logger
from src.manager.db_manager import DatabaseManager

logger = get_logger(__name__)


class DockerManager:
    def __init__(self) -> None:
        self.client = docker.from_env()

    def pull_image(self, image_name: str) -> Image | None:
        """
        Загружает образ из Docker Hub.
        """
        logger.info(f"Загрузка образа {image_name}...")
        try:
            image = self.client.images.pull(image_name)
            logger.info(f"Образ {image_name} успешно загружен.")
            return image
        except docker.errors.ImageNotFound:
            logger.exception(f"Образ {image_name} не найден в Docker Hub.")
        except docker.errors.APIError as e:
            logger.exception(f"Ошибка API при загрузке образа {image_name}: {e}")
        except DockerException as e:
            logger.exception(f"Общая ошибка при загрузке образа {image_name}: {e}")
        return None

    def run_container(
        self,
        image_name: str,
        container_name: str,
        ports: dict | None = None,
        environment: dict | None = None,
    ) -> Container | None:
        """
        Запускает контейнер с указанным образом.

        :param image_name: Название образа Docker.
        :param container_name: Название контейнера.
        :param ports: Словарь портов для проброса (например, {"5432/tcp": 5432}).
        :param environment: Словарь переменных окружения для контейнера.
        :return: Объект контейнера или None в случае ошибки.
        """
        ports = ports or {}
        try:
            self.remove_container_if_exists(container_name)

            logger.info(f"Запуск контейнера {container_name} с образом {image_name}...")
            container = self.client.containers.run(
                image=image_name,
                name=container_name,
                ports=ports,
                environment=environment,
                detach=True,
            )
            self.wait_for_container_ready(container, ports)
            logger.info(f"Контейнер {container_name} запущен.")
            return container
        except DockerException as e:
            logger.exception(f"Ошибка при запуске контейнера: {e}")
            return None

    def stop_container(self, container_name: str) -> None:
        """
        Останавливает и удаляет указанный контейнер.

        :param container_name: Название контейнера.
        """
        try:
            container = self.client.containers.get(container_name)
            self._stop_and_remove_container(container)
            logger.info(f"Контейнер {container_name} остановлен и удален.")
        except NotFound:
            logger.warning(f"Контейнер {container_name} не найден.")
        except DockerException as e:
            logger.exception(f"Ошибка при остановке контейнера: {e}")

    def list_containers(self, with_stopped: bool = True) -> list:
        """
        Возвращает список всех контейнеров.

        :param with_stopped: Если True, возвращаются все контейнеры, включая остановленные.
        """
        try:
            return self.client.containers.list(all=with_stopped)
        except DockerException as e:
            logger.exception(f"Ошибка при получении списка контейнеров: {e}")
            return []

    def remove_container_if_exists(self, container_name: str) -> None:
        """
        Удаляет контейнер, если он существует.

        :param container_name: Название контейнера.
        """
        try:
            container = self.client.containers.get(container_name)
            self._stop_and_remove_container(container)
            logger.info(f"Контейнер {container_name} остановлен и удален.")
        except NotFound:
            logger.info(f"Контейнер {container_name} не найден. Ничего не удалено.")
        except DockerException as e:
            logger.exception(f"Ошибка при удалении контейнера: {e}")

    @staticmethod
    def _stop_and_remove_container(container: Container) -> None:
        try:
            container.stop()
            container.remove()
        except DockerException as e:
            logger.exception(f"Ошибка при остановке/удалении контейнера: {e}")

    def wait_for_container_ready(
        self,
        container: Container,
        ports: dict,
        timeout: int = 20,
    ) -> bool:
        """
        Ожидание готовности контейнера.

        :param container: Объект контейнера.
        :param ports: Словарь портов для проверки готовности.
        :param timeout: Время ожидания в секундах.
        :raises TimeoutError: Если контейнер не готов в течение заданного времени.
        :return: True, если контейнер готов.
        """
        logger.info(f"Ожидание готовности контейнера {container.name}...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            container.reload()  # Обновляем статус контейнера
            if container.status == "running":
                try:
                    for port in ports:
                        if self.client.api.port(container.id, port):
                            logger.info(f"Контейнер {container.name} готов.")
                            return True
                except DockerException:
                    pass
            time.sleep(1)
        msg = f"Контейнер {container.name} не готов в течение {timeout} секунд."
        logger.error(msg)
        raise TimeoutError(msg)


# Пример использования модуля
if __name__ == "__main__":
    logger.info("test docker load")
    db_image = "postgres:latest"
    db_container_name = "postgres_test"
    db_name = "test_db"
    db_user = "user"
    db_password = "example"
    db_host = "localhost"
    db_port = 5432

    manager = DockerManager()
    # print(manager.list_containers())

    # Загрузка образа PostgreSQL
    postgres_image = manager.pull_image(db_image)

    # Запуск контейнера PostgreSQL
    postgres_container = manager.run_container(
        image_name=db_image,
        container_name=db_container_name,
        ports={"5432/tcp": db_port},
        environment={
            "POSTGRES_DB": db_name,
            "POSTGRES_USER": db_user,
            "POSTGRES_PASSWORD": db_password,
        },
    )

    time.sleep(10)  # Небольшая пауза для инициализации контейнера

    # Параметры подключения к базе данных
    db_manager = DatabaseManager(
        db_type="postgresql",
        username=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        db_name=db_name,
    )
    # Тест подключения
    if db_manager.test_connection():
        logger.info("Подключение к базе данных успешно.")
    else:
        logger.error("Не удалось подключиться к базе данных.")

    # print(manager.list_containers())

    # Список всех контейнеров

    # Остановка и удаление контейнера
    # manager.stop_container("postgres_test")

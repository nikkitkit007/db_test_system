import time

import docker
from docker.errors import DockerException

from src.config.log import get_logger
from src.manager.db_manager import DatabaseManager

logger = get_logger(__name__)


class DockerManager:
    def __init__(self):
        self.client = docker.from_env()

    def pull_image(self, image_name: str):
        """
        Загружает образ из Docker Hub.

        :param image_name: Название образа Docker
        :return: Объект образа или None в случае ошибки
        """
        try:
            logger.info(f"Загрузка образа {image_name}...")
            image = self.client.images.pull(image_name)
            logger.info(f"Образ {image_name} загружен.")
            return image
        except DockerException as e:
            logger.info(f"Ошибка при загрузке образа: {e}")
            return None

    def run_container(self, image_name: str, container_name: str, ports: dict = None, environment: dict = None):
        """
        Запускает контейнер с указанным образом.

        :param image_name: Название образа Docker
        :param container_name: Название контейнера
        :param ports: Словарь портов для проброса (например, {"5432/tcp": 5432})
        :param environment: Словарь переменных окружения для контейнера
        :return: Объект контейнера или None в случае ошибки
        """
        try:
            logger.info(f"Проверка существования контейнера {container_name}...")
            self.remove_container_if_exists(container_name)

            logger.info(f"Запуск контейнера {container_name} с образом {image_name}...")
            container = self.client.containers.run(
                image_name,
                name=container_name,
                ports=ports,
                environment=environment,
                detach=True
            )
            logger.info(f"Контейнер {container_name} запущен.")
            self.wait_for_container_ready(container_name, ports)
            return container
        except DockerException as e:
            logger.info(f"Ошибка при запуске контейнера: {e}")
            return None

    def stop_container(self, container_name: str):
        """
        Останавливает и удаляет указанный контейнер.

        :param container_name: Название контейнера
        """
        try:
            logger.info(f"Остановка контейнера {container_name}...")
            container = self.client.containers.get(container_name)
            container.stop()
            container.remove()
            logger.info(f"Контейнер {container_name} остановлен и удален.")
        except DockerException as e:
            logger.info(f"Ошибка при остановке контейнера: {e}")

    def list_containers(self, all: bool = True):
        """
        Возвращает список всех контейнеров.

        :param all: Если True, возвращает все контейнеры, включая остановленные
        :return: Список объектов контейнеров
        """
        try:
            containers = self.client.containers.list(all=all)
            return containers
        except DockerException as e:
            logger.info(f"Ошибка при получении списка контейнеров: {e}")
            return []

    def remove_container_if_exists(self, container_name: str):
        """
        Удаляет контейнер, если он существует.

        :param container_name: Название контейнера
        """
        try:
            container = self.client.containers.get(container_name)
            container.stop()
            container.remove()
            logger.info(f"Контейнер {container_name} остановлен и удален.")
        except docker.errors.NotFound:
            logger.info(f"Контейнер {container_name} не найден. Ничего не удалено.")
        except DockerException as e:
            logger.info(f"Ошибка при удалении контейнера: {e}")

    def wait_for_container_ready(self, container_name: str, ports: dict, timeout: int = 60):
        """
        Ожидание готовности контейнера.

        :param container_name: Название контейнера
        :param ports: Словарь портов для проверки готовности
        :param timeout: Время ожидания в секундах
        :raises TimeoutError: Если контейнер не готов в течение заданного времени
        """
        logger.info(f"Ожидание готовности контейнера {container_name}...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            container = self.client.containers.get(container_name)
            if container.status == 'running':
                try:
                    for port, host_port in ports.items():
                        if self.client.api.port(container.id, port):
                            logger.info(f"Контейнер {container_name} готов.")
                            return True
                except DockerException:
                    pass
            time.sleep(1)
        raise TimeoutError(f"Контейнер {container_name} не готов в течение {timeout} секунд.")


# Пример использования модуля
if __name__ == "__main__":
    logger.info('test docker load')
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
        environment={"POSTGRES_DB": db_name, "POSTGRES_USER": db_user, "POSTGRES_PASSWORD": db_password}
    )

    time.sleep(10)  # Небольшая пауза для инициализации контейнера

    # Параметры подключения к базе данных
    db_manager = DatabaseManager(
        db_type='postgresql',
        username=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        db_name=db_name
    )
    # Тест подключения
    if db_manager.test_connection():
        logger.info("Тест подключения прошел успешно.")
    else:
        logger.info("Тест подключения не удался.")

    # print(manager.list_containers())

    # Список всех контейнеров

    # Остановка и удаление контейнера
    # manager.stop_container("postgres_test")

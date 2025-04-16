import threading
import time
from dataclasses import dataclass

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container
from docker.models.images import Image

from src.config.log import get_logger
from src.schemas.test_init import DockerHostConfig

logger = get_logger(__name__)


@dataclass
class PeakStats:
    max_mem: int = 0  # максимальное значение memory_stats.usage (байт)
    max_cpu_percent: float = 0.0  # максимальный CPU% за интервал

    @property
    def max_mem_mb(self) -> float:
        """Возвращает max_mem в мегабайтах."""
        return self.max_mem / 1024 / 1024


class DockerManager:
    def __init__(self, host_config: DockerHostConfig | None = None, **kwargs) -> None:
        """
        Инициализация DockerManager.

        :param host_config: Конфигурация для подключения к Docker хосту
        :param kwargs: Дополнительные параметры для docker.from_env()
        """
        self._host_config = host_config
        try:
            if host_config and host_config.base_url:
                # Создаем конфигурацию TLS если нужно
                tls_config = None
                if all(
                    [
                        host_config.tls_ca_cert,
                        host_config.tls_client_cert,
                        host_config.tls_client_key,
                    ],
                ):
                    tls_config = docker.tls.TLSConfig(
                        ca_cert=host_config.tls_ca_cert,
                        client_cert=(
                            host_config.tls_client_cert,
                            host_config.tls_client_key,
                        ),
                        verify=host_config.tls_verify,
                    )

                # Подключение к удаленному хосту
                self.client = docker.DockerClient(
                    base_url=host_config.base_url,
                    tls=tls_config,
                    version=host_config.version,
                    timeout=host_config.timeout,
                )
            else:
                # Подключение к локальному хосту
                self.client = docker.from_env(**kwargs)

            # Проверяем подключение
            self.client.ping()
            logger.info("Успешное подключение к Docker daemon")

        except docker.errors.DockerException as e:
            logger.exception(f"Ошибка при подключении к Docker daemon: {e}")
            raise

        self.container_name = None
        self.container = None
        self._stop_event = threading.Event()
        self._stats_thread: threading.Thread | None = None
        self._peak_stats = PeakStats()

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
            self.container_name = container_name
            self.container = container
            return container
        except DockerException as e:
            logger.exception(f"Ошибка при запуске контейнера: {e}")
            return None

    def stop_container(self) -> None:
        try:
            container = self.client.containers.get(self.container_name)
            self._stop_and_remove_container(container)
            logger.info(f"Контейнер {self.container_name} остановлен и удален.")
        except NotFound:
            logger.warning(f"Контейнер {self.container_name} не найден.")
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

    def get_container_stats(self, start: bool = False) -> PeakStats | None:
        """
        Если start=True, запускаем поток для мониторинга.
        Если start=False, останавливаем поток и возвращаем пиковые значения.
        """
        if start:
            # Сбрасываем старые данные
            self._peak_stats = PeakStats()
            self._stop_event.clear()

            self._stats_thread = threading.Thread(
                target=self._measure_peaks,
                args=(self._stop_event,),
                daemon=True,
            )
            self._stats_thread.start()
            return None

        # Останавливаем сбор статистики и ждём поток
        if self._stats_thread and self._stats_thread.is_alive():
            self._stop_event.set()
            self._stats_thread.join()
        return self._peak_stats

    def _measure_peaks(self, stop_event: threading.Event) -> None:
        """
        Слушаем docker stats в режиме stream=True. Отслеживаем максимальное usage и CPU%.
        """
        prev_total_usage = None
        prev_system_usage = None

        for raw in self.container.stats(decode=True, stream=True):
            # 1. Проверка памяти
            mem_usage = raw["memory_stats"]["usage"]
            self._peak_stats.max_mem = max(mem_usage, self._peak_stats.max_mem)

            # 2. Проверка CPU
            cpu_stats = raw.get("cpu_stats", {})
            total_usage = cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            system_usage = cpu_stats.get("system_cpu_usage", 0)
            online_cpus = cpu_stats.get(
                "online_cpus",
                1,
            )  # сколько CPU доступно контейнеру

            # Рассчитываем CPU%, если есть предыдущее состояние
            if (prev_total_usage is not None) and (prev_system_usage is not None):
                cpu_delta = total_usage - prev_total_usage
                system_delta = system_usage - prev_system_usage
                # Если оба дельта > 0, считаем процент
                if cpu_delta > 0 and system_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
                    self._peak_stats.max_cpu_percent = max(
                        cpu_percent,
                        self._peak_stats.max_cpu_percent,
                    )

            # Обновляем «предыдущее» состояние
            prev_total_usage = total_usage
            prev_system_usage = system_usage

            # Если попросили остановиться — выходим из цикла
            if stop_event.is_set():
                break

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

    def get_host(self) -> str:
        """
        Возвращает хост для подключения к БД.
        Если используется удаленный Docker, возвращает хост из base_url.
        В противном случае возвращает 'localhost'.
        """
        if (
            hasattr(self, "_host_config")
            and self._host_config
            and self._host_config.base_url
        ):
            # Если используется удаленный Docker, берем хост из base_url
            return self._host_config.base_url.split("://")[1].split(":")[0]
        return "localhost"

    def scan_host_containers(self) -> list[dict]:
        """
        Сканирует хост и возвращает информацию о всех контейнерах.

        :return: Список словарей с информацией о контейнерах
        """
        try:
            containers = self.client.containers.list(all=True)
            container_info = []

            for container in containers:
                container_info.append(
                    {
                        "id": container.id,
                        "name": container.name,
                        "status": container.status,
                        "image": (
                            container.image.tags[0]
                            if container.image.tags
                            else "untagged"
                        ),
                        "ports": container.ports,
                        "created": container.attrs["Created"],
                        "state": container.attrs["State"],
                        "labels": container.labels,
                    },
                )

            return container_info
        except DockerException as e:
            logger.exception(f"Ошибка при сканировании контейнеров: {e}")
            return []

    def connect_to_container(self, container_id_or_name: str) -> bool:
        """
        Подключается к существующему контейнеру.

        :param container_id_or_name: ID или имя контейнера
        :return: True если подключение успешно, False в противном случае
        """
        try:
            container = self.client.containers.get(container_id_or_name)
            if container.status != "running":
                logger.warning(f"Контейнер {container_id_or_name} не запущен")
                return False

            self.container = container
            self.container_name = container.name
            logger.info(f"Успешно подключено к контейнеру {container_id_or_name}")
            return True
        except NotFound:
            logger.exception(f"Контейнер {container_id_or_name} не найден")
            return False
        except DockerException as e:
            logger.exception(
                f"Ошибка при подключении к контейнеру {container_id_or_name}: {e}",
            )
            return False

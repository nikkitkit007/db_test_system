import threading
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container
from docker.models.images import Image

from src.config.log import get_logger
from src.schemas.schema import DockerHostConfig

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
    def __init__(
        self,
        host_config: DockerHostConfig | None = None,
        log_fn: callable(str) = None,
        **kwargs,
    ) -> None:
        """
        Инициализация DockerManager.
        """
        self._host_config = host_config
        self._tls_config = None
        self.log_fn = log_fn or (lambda _: None)
        try:
            if host_config and host_config.base_url:
                self._tls_config = _create_tls_config(host_config)

                self.client = docker.DockerClient(
                    base_url=host_config.base_url,
                    tls=self._tls_config,
                    version=host_config.version,
                    timeout=host_config.timeout,
                )
            else:
                # Подключение к локальному хосту
                self.client = docker.from_env(**kwargs)

            self.client.ping()
            self.send_log("✅ Успешное подключение к Docker daemon", log_level="info")
        except docker.errors.DockerException as e:
            self.send_log(
                f"Ошибка при подключении к Docker daemon: {e}",
                log_level="exception",
            )
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
        try:
            image = self.client.images.pull(image_name)
            self.send_log(f"✅ Образ {image_name} успешно загружен.", log_level="info")
            return image
        except docker.errors.ImageNotFound:
            self.send_log(
                f"Образ {image_name} не найден в Docker Hub.",
                log_level="exception",
            )
        except docker.errors.APIError as e:
            self.send_log(
                f"Ошибка API при загрузке образа {image_name}: {e}",
                log_level="exception",
            )
        except DockerException as e:
            self.send_log(
                f"Общая ошибка при загрузке образа {image_name}: {e}",
                log_level="exception",
            )
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
        """
        ports = ports or {}
        try:
            self.remove_container_if_exists(container_name)

            container = self.client.containers.run(
                image=image_name,
                name=container_name,
                ports=ports,
                environment=environment,
                detach=True,
            )
            self.wait_for_container_ready(container, ports)
            self.send_log(f"✅ Контейнер {container_name} запущен.")
            self.container_name = container_name
            self.container = container
            return container
        except DockerException as e:
            self.send_log(
                f"❌ Ошибка при запуске контейнера: {e}",
                log_level="exception",
            )
            return None

    def stop_container(
        self,
        *,
        stop: bool = True,
        remove: bool = False,
    ) -> None:
        try:
            container = self.client.containers.get(self.container_name)
            self._stop_and_remove_container(container, stop=stop, remove=remove)
        except NotFound:
            self.send_log(
                f"⚠️ Контейнер {self.container_name} не найден.",
                log_level="warning",
            )

        except DockerException as e:
            self.send_log(
                f"❌ Ошибка при остановке контейнера: {e}",
                log_level="exception",
            )

    def list_containers(self, *, with_stopped: bool = True) -> list:
        """
        Возвращает список всех контейнеров.
        """
        return self.client.containers.list(all=with_stopped)

    def remove_container_if_exists(self, container_name: str) -> None:
        """
        Удаляет контейнер, если он существует.
        """
        try:
            container = self.client.containers.get(container_name)
            self._stop_and_remove_container(container, stop=False, remove=True)
        except NotFound:
            self.send_log(
                f"⚠️ Контейнер {container_name} не найден. Ничего не удалено.",
                log_level="info",
            )

        except DockerException as e:
            self.send_log(
                f"❌ Ошибка при удалении контейнера: {e}",
                log_level="exception",
            )

    def get_container_stats(self, *, start: bool = False) -> PeakStats | None:
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

    def _stop_and_remove_container(
        self,
        container: Container,
        *,
        stop: bool = True,
        remove: bool = True,
    ) -> None:
        try:
            if remove:
                container.stop()
                container.remove()
                self.send_log(f"✅ Контейнер {container.name} удален.")
            elif stop:
                container.stop()
                self.send_log(f"✅ Контейнер {container.name} остановлен.")
        except DockerException as e:
            self.send_log(
                f"❌ Ошибка при остановке/удалении контейнера: {e}",
                log_level="exception",
            )

    def wait_for_container_ready(
        self,
        container: Container,
        ports: dict,
        timeout: int = 20,
    ) -> bool:
        """
        Ожидание готовности контейнера.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            container.reload()
            if container.status == "running":
                try:
                    for port in ports:
                        if self.client.api.port(container.id, port):
                            self.send_log(f"✅ Контейнер {container.name} готов.")
                            return True
                except DockerException:
                    pass
            time.sleep(1)

        self.send_log(
            f"❌ Контейнер {container.name} не готов в течение {timeout} секунд.",
            log_level="error",
        )
        raise TimeoutError

    def get_host(self) -> str:
        """
        Возвращает хост для подключения к БД.
        - При tcp://... отдаёт имя/IP хоста.
        - При unix:// или npipe:// — 'localhost'.
        """
        base = getattr(self, "_host_config", None)
        if not base or not base.base_url:
            return "localhost"

        parsed = urlparse(base.base_url)
        scheme = parsed.scheme.lower()
        if scheme in ("unix", "npipe"):
            return "localhost"

        return parsed.hostname or "localhost"

    def scan_host_containers(self) -> list[dict]:
        """
        Сканирует хост и возвращает информацию о всех контейнерах.
        """
        containers = self.list_containers(with_stopped=True)

        container_info = []

        for container in containers:
            container_info.append(
                {
                    "id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "image": (
                        container.image.tags[0] if container.image.tags else "untagged"
                    ),
                    "ports": container.ports,
                    "created": container.attrs["Created"],
                    "state": container.attrs["State"],
                    "labels": container.labels,
                },
            )

        return container_info

    def connect_to_container(self, container_id_or_name: str) -> bool:
        """
        Подключается к существующему контейнеру.
        """
        try:
            container = self.client.containers.get(container_id_or_name)
            if container.status != "running":
                self.send_log(
                    f"⚠️ Контейнер {container_id_or_name} не запущен",
                    log_level="warning",
                )
                return False

            self.container = container
            self.container_name = container.name
            self.send_log(f"✅ Успешно подключено к контейнеру {container_id_or_name}")
            return True
        except NotFound:
            logger.exception(f"⚠️ Контейнер {container_id_or_name} не найден")
            return False
        except DockerException as e:
            self.send_log(
                f"❌ Ошибка при подключении к контейнеру {container_id_or_name}: {e}",
                log_level="exception",
            )
            return False

    def send_log(self, msg: str, log_level: str = "info") -> None:
        # ✅ ❌ ⚠️
        if log_level == "info":
            self.log_fn(msg)
            logger.info(msg)
        if log_level == "exception":
            self.log_fn(msg)
            logger.exception(msg)
        if log_level == "error":
            self.log_fn(msg)
            logger.error(msg)
        if log_level == "warning":
            self.log_fn(msg)
            logger.warning(msg)


def _create_tls_config(host_config: DockerHostConfig) -> docker.tls.TLSConfig | None:
    """Создает конфигурацию TLS для Docker клиента."""
    if not all(
        [
            host_config.tls_ca_cert,
            host_config.tls_client_cert,
            host_config.tls_client_key,
        ],
    ):
        return None

    return docker.tls.TLSConfig(
        ca_cert=host_config.tls_ca_cert,
        client_cert=(host_config.tls_client_cert, host_config.tls_client_key),
        verify=host_config.tls_verify,
    )

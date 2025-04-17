import re
import time

from src.config.log import get_logger
from src.core.scenario_steps import ScenarioStep, StepType
from src.manager.db.base_adapter import BaseAdapter
from src.manager.db.redis_adapter import RedisAdapter
from src.manager.db.sql_adapter import SQLAdapter
from src.manager.docker_manager import DockerManager, _create_tls_config
from src.schemas.test_init import DbTestConf
from src.storage.db_manager.result_storage import result_manager
from src.storage.model import TestResults

logger = get_logger(__name__)


def run_test(db_test_conf: DbTestConf) -> None:
    """
    Основной метод для запуска теста
    """
    # Создаем конфигурацию TLS если нужно
    tls_cfg = (
        _create_tls_config(db_test_conf.docker_host)
        if db_test_conf.docker_host
        else None
    )

    docker_manager = DockerManager(
        host_config=db_test_conf.docker_host,
        tls_config=tls_cfg,
    )

    db_image = db_test_conf.db_config.image_name
    config = db_test_conf.db_config.get_config_as_json()

    # Подтягиваем Docker-образ (если отсутствует локально — docker pull)
    docker_manager.pull_image(db_image)

    # Получаем конфигурацию для данного образа (порт, тип БД и т. д.)

    # Формируем имя контейнера, переменные окружения, порты и т. д.
    container_name = f"{_clear_container_name(db_image)}_test"
    environment = config.get("env", {})
    exposed_port = config["port"]
    ports = {exposed_port: exposed_port}  # Проброс порта 1:1

    # Определяем хост для подключения к БД
    db_host = docker_manager.get_host()

    # 1) Запускаем контейнер ( detach=True внутри run_container )
    docker_manager.run_container(
        image_name=db_image,
        container_name=container_name,
        environment=environment,
        ports=ports,
    )

    # 2) Определяем, какой адаптер использовать (SQLAdapter, RedisAdapter, ...)
    db_type = config["db_type"].lower()

    if db_type in ["postgresql", "mysql", "sqlite", "mssql"]:
        adapter = SQLAdapter(
            db_type=db_type,
            driver=config.get("driver"),
            username=config.get("user"),
            password=config.get("password"),
            host=db_host,
            port=exposed_port,
            db_name=config.get("db"),
        )
    elif db_type == "redis":
        adapter = RedisAdapter(
            host=db_host,
            port=exposed_port,
            password=config.get("password"),
            db=0,
        )
    else:
        # Если есть другие NoSQL/ in-memory, обрабатываем их здесь
        msg = f"Неизвестный/неподдерживаемый тип БД: {db_type}"
        raise ValueError(msg)

    # 3) Подключаемся к базе через адаптер
    adapter.connect()

    # 4) Выполняем непосредственно тест (замеряем время, память)
    _run_scenario_steps(adapter, docker_manager, db_test_conf)

    # 5) Останавливаем контейнер (при желании можно оставить на отладку)
    docker_manager.stop_container()


def _run_scenario_steps(
    adapter: BaseAdapter,
    docker_manager: DockerManager,
    db_test_conf: DbTestConf,
) -> None:

    for step in db_test_conf.scenario_steps:
        if step.measure:
            docker_manager.get_container_stats(start=True)
            time_start = time.perf_counter()
            _execute_step(adapter, step)
            test_time = time.perf_counter() - time_start
            stats_on_finish = docker_manager.get_container_stats(start=False)

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            result_manager.insert_result(
                TestResults(
                    timestamp=timestamp,
                    db_image=db_test_conf.db_config.image_name,
                    operation=step.step_type.value,
                    num_records=getattr(step, "num_records", 0),
                    step_description=str(step),
                    execution_time=test_time,
                    memory_used=stats_on_finish.max_mem_mb,
                    cpu_percent=stats_on_finish.max_cpu_percent,
                ),
            )
        else:
            _execute_step(adapter, step)


def _execute_step(adapter: BaseAdapter, step: ScenarioStep) -> None:
    if step.step_type == StepType.create:
        adapter.create_table(step)

    elif step.step_type == StepType.insert:
        adapter.insert_data(step)

    elif step.step_type == StepType.query:
        adapter.execute_query(step)

    else:
        msg = f"Неизвестный шаг: {type(step).__name__}"
        raise NotImplementedError(msg)


def _clear_container_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "_", name)

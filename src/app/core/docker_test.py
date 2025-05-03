import re
import time

from src.app.core.scenario_steps import ScenarioStep, StepType
from src.app.manager.db.base_adapter import BaseAdapter
from src.app.manager.db.redis_adapter import RedisAdapter
from src.app.manager.db.sql_adapter import SQLAdapter
from src.app.manager.docker_manager import DockerManager
from src.app.schemas.schema import DbTestConf
from src.app.storage.db_manager.result_storage import result_manager
from src.app.storage.model import TestResults


def run_test(db_test_conf: DbTestConf, log_fn: callable(str)) -> None:
    """
    Основной метод для запуска теста
    """
    docker_manager = DockerManager(
        host_config=db_test_conf.docker_host,
        log_fn=log_fn,
    )

    db_image = db_test_conf.db_config.image_name
    config = db_test_conf.db_config.get_config_as_json()

    docker_manager.pull_image(db_image)

    # Получаем конфигурацию для данного образа (порт, тип БД и т. д.)
    # Формируем имя контейнера, переменные окружения, порты и т. д.
    container_name = f"{_clear_container_name(db_image)}_test"
    environment = config.get("env", {})
    exposed_port = config["port"]
    ports = {exposed_port: exposed_port}

    # Определяем хост для подключения к БД
    db_host = docker_manager.get_host()

    # 1) Запускаем контейнер
    if db_test_conf.test_system_config.use_existing:
        log_fn(
            f"🛠 Пытаемся подключиться к существующему контейнеру '{container_name}'…",
        )
        connected = docker_manager.connect_to_container(container_name)
        if connected:
            log_fn(f"✅ Подключились к контейнеру '{container_name}'.")
        else:
            log_fn(f"❗ Контейнер '{container_name}' не запущен, запускаем новый.")
            docker_manager.run_container(
                image_name=db_image,
                container_name=container_name,
                ports=ports,
                environment=environment,
            )
    else:
        log_fn(f"🚀 Запускаем контейнер '{container_name}' с образом '{db_image}'…")
        docker_manager.run_container(
            image_name=db_image,
            container_name=container_name,
            ports=ports,
            environment=environment,
        )

    # 2) Определяем, какой адаптер использовать (SQLAdapter, RedisAdapter, ...)
    db_type = config["db_type"].lower()

    adapter = _get_db_adapter(config, db_host, db_type, exposed_port)

    # 3) Подключаемся к базе через адаптер
    adapter.connect()

    # 4) Выполняем непосредственно тест (замеряем время, память)
    _run_scenario_steps(adapter, docker_manager, db_test_conf, log_fn=log_fn)

    # 5) Останавливаем контейнер
    test_system_config = db_test_conf.test_system_config
    docker_manager.stop_container(
        stop=test_system_config.stop_after,
        remove=test_system_config.remove_after,
    )


def _get_db_adapter(config, db_host, db_type, exposed_port) -> BaseAdapter:
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
    return adapter


def _run_scenario_steps(
    adapter: BaseAdapter,
    docker_manager: DockerManager,
    db_test_conf: DbTestConf,
    log_fn: callable(str),
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

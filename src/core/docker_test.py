import time

import psutil

from src.config.log import get_logger
from src.manager.db_manager import DatabaseManager
from src.manager.docker_manager import DockerManager
from src.schemas.test_init import DbTestConf
from src.storage.config_storage import config_manager
from src.storage.model import TestResults
from src.storage.result_storage import result_manager
from src.utils import (
    clear_container_name,
    generate_csv,
    load_csv_to_db,
)

logger = get_logger(__name__)


def run_test(db_test_conf: DbTestConf) -> None:
    # Получаем образ и его конфигурацию
    docker_manager = DockerManager()
    db_image = db_test_conf.db_image

    docker_manager.pull_image(db_image)
    config = config_manager.get_db_config(db_image)

    container_name = f"{clear_container_name(db_image)}_test"
    environment = config.get("env", {})
    ports = {config["port"]: config["port"]}

    # Запускаем контейнер с БД
    docker_manager.run_container(
        db_image,
        container_name,
        environment=environment,
        ports=ports,
    )
    db_manager = DatabaseManager(
        db_type=config["db_type"],
        username=config["user"],
        password=config["password"],
        host="localhost",
        port=config["port"],
        db_name=config["db"],
    )
    _prepare_db(db_manager, db_test_conf)
    _load_test(db_manager, db_test_conf)


def _prepare_db(db_manager: DatabaseManager, db_test_conf: DbTestConf) -> None:
    # Генерируем тестовые данные и загружаем их в БД

    test_data_conf = db_test_conf.test_data_conf
    csv_file = generate_csv(test_data_conf.num_records, test_data_conf.data_types)
    load_csv_to_db(csv_file, db_manager)


def _load_test(db_manager: DatabaseManager, db_test_conf: DbTestConf) -> None:
    process = psutil.Process()
    memory_before = process.memory_info().rss

    start_time = time.perf_counter()
    db_manager.execute_query("select * from test_tbl")
    end_time = time.perf_counter()

    memory_after = process.memory_info().rss

    execution_time = round(end_time - start_time, 5)
    memory_used = round((memory_after - memory_before) / 1024 / 1024, 5)

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    data_types = ",".join(db_test_conf.test_data_conf.data_types)

    result_manager.insert_result(
        TestResults(
            timestamp=timestamp,
            db_image=db_test_conf.db_image,
            operation=db_test_conf.operation,
            num_records=db_test_conf.test_data_conf.num_records,
            data_types=data_types,
            execution_time=execution_time,
            memory_used=memory_used,
        ),
    )

    logger.info(f"Execution time: {execution_time} seconds")
    logger.info(f"Memory used: {memory_used} MB")

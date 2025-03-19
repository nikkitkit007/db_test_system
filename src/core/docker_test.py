import time

import psutil

from src.config.log import get_logger
from src.manager.db.redis_adapter import RedisAdapter
from src.manager.db.sql_adapter import SQLAdapter
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
    """
    Основной метод для запуска теста:
    1) Получаем образ и его конфигурацию (порт, env, логин/пароль и т. д.).
    2) Запускаем Docker-контейнер с этой БД.
    3) Создаем нужный адаптер (SQL, Redis...), подключаемся к БД внутри контейнера.
    4) Выполняем сценарий: подготовка, загрузка данных, запросы.
    5) Замеряем время и память, логируем результаты в SQLite.
    6) Останавливаем контейнер.
    """

    # Инициализируем менеджер Docker
    docker_manager = DockerManager()
    db_image = db_test_conf.db_image

    # Подтягиваем Docker-образ (если отсутствует локально — docker pull)
    docker_manager.pull_image(db_image)

    # Получаем конфигурацию для данного образа (порт, тип БД и т. д.)
    config = config_manager.get_db_config(db_image)

    # Формируем имя контейнера, переменные окружения, порты и т. д.
    container_name = f"{clear_container_name(db_image)}_test"
    environment = config.get("env", {})
    exposed_port = config["port"]
    ports = {exposed_port: exposed_port}  # Проброс порта 1:1

    # 1) Запускаем контейнер ( detach=True внутри run_container )
    docker_manager.run_container(
        image_name=db_image,
        container_name=container_name,
        environment=environment,
        ports=ports,
    )

    # 2) Определяем, какой адаптер использовать (SQLAdapter, RedisAdapter, ...)
    db_type = config["db_type"].lower()

    # Например, sql_db_types = ["postgresql", "mysql", "sqlite", "mssql"] и т.д.
    if db_type in ["postgresql", "mysql", "sqlite", "mssql"]:
        adapter = SQLAdapter(
            db_type=db_type,
            driver=config.get("driver"),
            username=config.get("user"),
            password=config.get("password"),
            host="localhost",  # контейнер прокидывает порт на локалхост
            port=exposed_port,
            db_name=config.get("db"),
        )
    elif db_type == "redis":
        adapter = RedisAdapter(
            host="localhost",
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

    # 4) Выполняем подготовительный этап: создание структуры / генерация CSV / вставка данных
    _prepare_db(adapter, db_test_conf)

    # 5) Выполняем непосредственно тест (замеряем время, память)
    _load_test(adapter, db_test_conf)

    # 6) Останавливаем контейнер (при желании можно оставить на отладку)
    docker_manager.stop_container(container_name)


def _prepare_db(adapter, db_test_conf: DbTestConf) -> None:
    """
    Подготовка базы к тесту:
    - Генерируем CSV-файл с тестовыми данными (N записей, нужные типы).
    - Для SQLAdapter можно создать таблицу, для RedisAdapter – псевдо-таблицу (ключ: value).
    - Вставляем данные.
    """
    test_data_conf = db_test_conf.test_data_conf
    # Генерация CSV (искусственные данные)
    csv_file = generate_csv(
        num_records=test_data_conf.num_records,
        data_types=test_data_conf.data_types,
    )

    # Если это SQL-база, можем создать таблицу (test_tbl).
    # В реальном проекте можно взять структуру из test_data_conf
    if hasattr(adapter, "create_table"):
        # Допустим, test_data_conf.data_types может быть ["str","int","date"],
        # и нам нужно соотнести с названиями колонок:
        columns_mapping = {
            "col_str": "str",
            "col_int": "int",
            "col_date": "date",
        }
        adapter.create_table("test_tbl", columns_mapping)

    # Вставка данных (для Redis это тоже будет работать, только адаптер сделает HSET)
    # Вариант 1: вызвать нашу удобную функцию load_csv_to_db (если она внутри использует adapter)
    load_csv_to_db(csv_file, adapter)

    # Вариант 2: самостоятельно преобразовать CSV -> DataFrame -> adapter.insert_data(...)
    #  df = pd.read_csv(csv_file)
    #  adapter.insert_data("test_tbl", df)


def _load_test(adapter, db_test_conf: DbTestConf) -> None:
    """
    Измеряем производительность:
    - Начало (memory_before, time_before)
    - Выполняем какую-то операцию/запрос (напр. SELECT * или GET/SET для Redis).
    - Фиксируем memory_after, time_after
    - Сохраняем результат
    """
    process = psutil.Process()
    memory_before = process.memory_info().rss
    start_time = time.perf_counter()

    # Для SQL: adapter.execute_query("SELECT * FROM test_tbl")
    # Для Redis: adapter.execute_query("не даст результата, т. к. заглушка")
    #            В реальном коде делаем что-то вроде get/set?
    adapter.execute_query("SELECT * FROM test_tbl")

    end_time = time.perf_counter()
    memory_after = process.memory_info().rss

    execution_time = round(end_time - start_time, 5)
    memory_used = round((memory_after - memory_before) / 1024 / 1024, 5)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    data_types = ",".join(db_test_conf.test_data_conf.data_types)

    # Сохраняем результат в БД (SQLite)
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

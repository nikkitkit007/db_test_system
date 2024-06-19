import random
import string
import time

import pandas as pd
import psutil

from log import get_logger
from manager.db_manager import DatabaseManager
from functools import wraps

logger = get_logger(__name__)


def generate_csv(file_name, num_records, data_types):
    data = []
    type_map = {
        'int': lambda: random.randint(1, 1000),
        'str': lambda: ''.join(random.choices(string.ascii_letters, k=10)),
        'date': lambda: pd.Timestamp('today').strftime("%Y-%m-%d")
    }
    for _ in range(num_records):
        row = {f'col_{i + 1}': type_map[dt]() for i, dt in enumerate(data_types)}
        data.append(row)

    df = pd.DataFrame(data)
    df.to_csv(file_name, index=False)

    logger.info(f'CSV file {file_name} with {num_records} records generated.')


def measure_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        process = psutil.Process()
        memory_before = process.memory_info().rss

        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()

        memory_after = process.memory_info().rss

        execution_time = end_time - start_time
        memory_used = memory_after - memory_before

        logger.info(f"Execution time: {round(execution_time, 5)} seconds")
        logger.info(f"Memory used: {round(memory_used / 1024 / 1024, 5)} MB")

        return result
    return wrapper


@measure_performance
def load_csv_to_db(csv_file: str, db_manager: DatabaseManager, table_name: str):
    """
    Загружает данные из CSV файла в базу данных.

    :param csv_file: Название CSV файла
    :param db_manager: Объект DatabaseManager для взаимодействия с базой данных
    :param table_name: Название таблицы в базе данных
    """
    df = pd.read_csv(csv_file)
    columns = {col: 'str' for col in df.columns}  # Используем 'str' для простоты
    db_manager.create_table(table_name, columns)
    db_manager.insert_data(table_name, df)


def execute_and_measure(db_manager, query):
    process = psutil.Process()
    memory_before = process.memory_info().rss

    start_time = time.time()
    db_manager.execute_query(query)     # exec
    end_time = time.time()

    memory_after = process.memory_info().rss

    execution_time = end_time - start_time
    memory_used = memory_after - memory_before

    logger.info(f"Execution time: {execution_time} seconds")
    logger.info(f"Memory used: {memory_used / 1024 / 1024} MB")

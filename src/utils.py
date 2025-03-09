import random
import re
import string
import time

import pandas as pd
import psutil

from manager.db_manager import DatabaseManager
from src.config.log import get_logger
from src.schemas.enums import DataType

logger = get_logger(__name__)


def generate_csv(file_name: str, num_records: int, data_types: list[DataType]) -> None:
    data = []
    type_map = {
        DataType.int: lambda: random.randint(1, 1000),
        DataType.str: lambda: "".join(random.choices(string.ascii_letters, k=10)),
        DataType.date: lambda: pd.Timestamp("today").strftime("%Y-%m-%d"),
    }
    for _ in range(num_records):
        row = {
            f"col_{i + 1}": type_map.get(dt, type_map[DataType.str])()
            for i, dt in enumerate(data_types)
        }
        data.append(row)

    df = pd.DataFrame(data)
    df.to_csv(file_name, index=False)

    logger.info(f"CSV file {file_name} with {num_records} records generated.")


def load_csv_to_db(csv_file: str, db_manager: DatabaseManager, table_name: str) -> None:
    """
    Загружает данные из CSV файла в базу данных.

    :param csv_file: Название CSV файла
    :param db_manager: Объект DatabaseManager для взаимодействия с базой данных
    :param table_name: Название таблицы в базе данных
    """
    df = pd.read_csv(csv_file)
    columns = {col: "str" for col in df.columns}  # Используем 'str' для простоты
    db_manager.create_table(table_name, columns)
    db_manager.insert_data(table_name, df)


def execute_and_measure(db_manager, query) -> None:
    process = psutil.Process()
    memory_before = process.memory_info().rss

    start_time = time.time()
    db_manager.execute_query(query)  # exec
    end_time = time.time()

    memory_after = process.memory_info().rss

    execution_time = end_time - start_time
    memory_used = memory_after - memory_before

    logger.info(f"Execution time: {execution_time} seconds")
    logger.info(f"Memory used: {memory_used / 1024 / 1024} MB")


def clear_container_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "_", name)

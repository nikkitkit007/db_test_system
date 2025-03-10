import random
import re
import string

import pandas as pd

from manager.db_manager import DatabaseManager
from src.config.log import get_logger
from src.schemas.enums import DataType

logger = get_logger(__name__)


def generate_csv(
    num_records: int,
    data_types: list[DataType],
    file_name: str | None = None,
) -> str:
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
    if not file_name:
        file_name = "test_data_file.csv"
    df.to_csv(file_name, index=False)

    logger.info(f"CSV file {file_name} with {num_records} records generated.")
    return file_name


def load_csv_to_db(
    csv_file: str,
    db_manager: DatabaseManager,
    table_name: str = "test_tbl",
) -> None:
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


def clear_container_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "_", name)

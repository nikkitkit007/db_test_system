import random
import re
import secrets
import string

import pandas as pd

from src.config.log import get_logger
from src.schemas.enums import DataType

logger = get_logger(__name__)


def generate_csv(
    num_records: int,
    data_types: dict[str, DataType],
    file_name: str | None = None,
) -> str:
    data = []
    type_map = {
        DataType.int: lambda: secrets.randbelow(10000),
        DataType.str: lambda: "".join(random.choices(string.ascii_letters, k=10)),
        DataType.date: lambda: pd.Timestamp("today").strftime("%Y-%m-%d"),
        DataType.bool: lambda: secrets.choice([True, False]),
        DataType.float: lambda: secrets.randbelow(100000),
    }
    for _ in range(num_records):
        row = {
            col: type_map.get(dt_type, type_map[DataType.str])()
            for col, dt_type in data_types.items()
        }
        data.append(row)

    df = pd.DataFrame(data)
    if not file_name:
        file_name = "test_data_file.csv"
    df.to_csv(file_name, index=False)

    logger.info(f"CSV file {file_name} with {num_records} records generated.")
    return file_name


def clear_container_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "_", name)

import random
import secrets
import string

import numpy as np
import pandas as pd

from src.config.log import get_logger
from src.schemas.enums import DataType

logger = get_logger(__name__)


def generate_csv(
    num_records: int,
    data_types: dict[str, DataType],
    file_name: str | None = None,
) -> str:
    data = {
        col: (
            np.random.randint(0, 10000, num_records)
            if dt_type == DataType.int else
            np.random.uniform(0, 100000, num_records)
            if dt_type == DataType.float else
            np.random.choice([True, False], num_records)
            if dt_type == DataType.bool else
            np.full(num_records, pd.Timestamp("today").strftime("%Y-%m-%d"))
            if dt_type == DataType.date else
            ["".join(random.choices(string.ascii_letters, k=10)) for _ in range(num_records)]
        )
        for col, dt_type in data_types.items()
    }
    df = pd.DataFrame(data)
    if not file_name:
        file_name = "test_data_file.csv"
    df.to_csv(file_name, index=False)

    logger.info(f"CSV file {file_name} with {num_records} records generated.")
    return file_name

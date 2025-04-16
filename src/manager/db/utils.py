import string

import numpy as np
import pandas as pd

from src.config.log import get_logger
from src.core.scenario_steps import ColumnDefinition
from src.schemas.enums import DataType

logger = get_logger(__name__)


def generate_csv(
    num_records: int,
    data_types: dict[str, ColumnDefinition],
    file_name: str | None = None,
) -> str:
    data = {
        col: _generate_column_values(
            col_definition.data_type,
            num_records,
            col_definition.primary_key,
        )
        for col, col_definition in data_types.items()
    }
    df = pd.DataFrame(data)
    if not file_name:
        file_name = "test_data_file.csv"
    df.to_csv(file_name, index=False)

    logger.info(f"CSV file {file_name} with {num_records} records generated.")
    return file_name


def _generate_column_values(dt: str, num_records: int, unique: bool):
    if dt == DataType.int:
        if unique:
            return np.random.choice(
                np.arange(num_records + 1),
                size=num_records,
                replace=False,
            )
        return np.random.randint(0, 1000000, size=num_records)
    if dt == DataType.float:
        if unique:
            return np.random.choice(
                np.arange(num_records + 1),
                size=num_records,
                replace=False,
            ).astype(np.float64)
        return np.random.uniform(0, 1000000, size=num_records)
    if dt == DataType.bool:
        if unique:
            if num_records > 2:
                msg = "Невозможно сгенерировать более 2 уникальных булевых значений."
                raise ValueError(
                    msg,
                )
            return np.array([True, False])[:num_records]
        return np.random.choice([True, False], size=num_records)
    if dt == DataType.date:
        if unique:
            return (
                pd.date_range(
                    start=pd.Timestamp("today"),
                    periods=num_records,
                    freq="D",
                )
                .strftime("%Y-%m-%d")
                .tolist()
            )
        return np.full(num_records, pd.Timestamp("today").strftime("%Y-%m-%d"))
    if dt == DataType.str:
        if unique:
            return np.char.add("str_", np.arange(num_records).astype(str))
        letters = np.array(list(string.ascii_letters))
        indices = np.random.randint(0, len(letters), size=(num_records, 10))
        return np.apply_along_axis(lambda row: "".join(row), 1, letters[indices])
    letters = np.array(list(string.ascii_letters))
    indices = np.random.randint(0, len(letters), size=(num_records, 10))
    return np.apply_along_axis(lambda row: "".join(row), 1, letters[indices])

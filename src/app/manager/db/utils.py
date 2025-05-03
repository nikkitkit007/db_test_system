import string

import numpy as np
import pandas as pd
from src.app.config.log import get_logger
from src.app.core.scenario_steps import ColumnDefinition
from src.app.schemas.enums import DataType

logger = get_logger(__name__)


def generate_csv(
    num_records: int,
    data_types: dict[str, ColumnDefinition],
    file_name: str = "test_data_file.csv",
) -> str:
    data = {
        col: _generate_column_values(
            col_definition.data_type,
            num_records,
            unique=col_definition.primary_key,
        )
        for col, col_definition in data_types.items()
    }
    test_data_df = pd.DataFrame(data)
    test_data_df.to_csv(file_name, index=False)

    logger.info(f"CSV file {file_name} with {num_records} records generated.")
    return file_name


def _generate_column_values(dt: str, num_records: int, *, unique: bool):
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

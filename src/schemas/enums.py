import enum
from enum import auto

from sqlalchemy import Boolean, Date, Float, Integer


class AutoName(enum.Enum):

    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name

    def __str__(self) -> str:
        return self._name_


class DataType(str, AutoName):
    str = auto()
    int = auto()
    float = auto()
    date = auto()
    bool = auto()


sql_type_mapping = {
    "int": Integer,
    # "str": Text,
    "date": Date,
    "bool": Boolean,
    "float": Float,
}

data_type_list = [item.value for item in DataType]

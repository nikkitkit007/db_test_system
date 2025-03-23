import enum
from enum import auto


class AutoName(enum.Enum):

    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name

    def __str__(self) -> str:
        return self._name_


class DataType(str, AutoName):
    str = auto()
    int = auto()
    date = auto()
    bool = auto()

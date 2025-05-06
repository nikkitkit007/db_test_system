import enum
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict
from src.app.schemas.enums import DataType


class StepType(enum.Enum):
    insert = "insert"
    create = "create"
    query = "query"


class ScenarioStep(BaseModel):
    model_config = ConfigDict(json_encoders={StepType: lambda v: v.value})

    step_type: StepType
    measure: bool = False

    def __str__(self) -> str:
        return f"{self.step_type.value}"


@dataclass
class ColumnDefinition:
    data_type: DataType
    primary_key: bool = False


class CreateTableStep(ScenarioStep):
    step_type: StepType = StepType.create
    table_name: str
    columns: dict[str, ColumnDefinition]

    def __str__(self) -> str:
        columns_str = {
            col_name: f"{col_def.data_type} {'(PK)' if col_def.primary_key else ''}".strip()
            for col_name, col_def in self.columns.items()
        }
        return f"Имя таблицы: {self.table_name}. (Колонки={columns_str})"


class InsertDataStep(ScenarioStep):
    step_type: StepType = StepType.insert

    table_name: str
    num_records: int
    columns: dict[str, ColumnDefinition]

    def __str__(self) -> str:
        return f"Имя таблицы={self.table_name}, Число записей={self.num_records}"


class QueryStep(ScenarioStep):
    step_type: StepType = StepType.query

    query: str
    thread_count: int
    request_count: int

    def __str__(self) -> str:
        return f"Запрос: {self.query}"


def deserialize_step(data: dict):
    step_type = data.get("step_type")
    measure = data.get("measure", False)
    if step_type == StepType.create.value:
        return CreateTableStep(
            table_name=data["table_name"],
            columns=data["columns"],
            measure=measure,
        )
    if step_type == StepType.insert.value:
        return InsertDataStep(
            table_name=data["table_name"],
            num_records=data["num_records"],
            columns=data["columns"],
            measure=measure,
        )
    if step_type == StepType.query.value:
        return QueryStep(
            query=data["query"],
            thread_count=data.get("thread_count", 1),
            request_count=data.get("request_count", 1),
            measure=measure,
        )
    msg = f"Неизвестный тип шага: {step_type}"
    raise ValueError(msg)

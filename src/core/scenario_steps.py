import enum

from pydantic import BaseModel, ConfigDict

from src.schemas.enums import DataType


class StepType(enum.Enum):
    insert = "insert"
    create = "create"
    query = "query"


class ScenarioStep(BaseModel):
    """
    Базовый класс шага сценария (абстрактный).
    """

    model_config = ConfigDict(json_encoders={StepType: lambda v: v.value})

    step_type: StepType
    measure: bool = False

    def __str__(self) -> str:
        return f"{self.step_type.value}"


class CreateTableStep(ScenarioStep):
    step_type: StepType = StepType.create
    table_name: str
    columns: dict[str, DataType]

    def __str__(self) -> str:
        columns = {
            col_name: data_type.value for col_name, data_type in self.columns.items()
        }
        return f"Имя таблицы: {self.table_name}. (Колонки={columns})"


class InsertDataStep(ScenarioStep):
    step_type: StepType = StepType.insert

    table_name: str
    num_records: int
    columns: dict[str, DataType]

    def __str__(self) -> str:
        return f"Имя таблицы={self.table_name}, Число записей={self.num_records}, Колонки={self.columns}"


class QueryStep(ScenarioStep):
    step_type: StepType = StepType.query

    query: str

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
            measure=measure,
        )
    msg = f"Неизвестный тип шага: {step_type}"
    raise ValueError(msg)

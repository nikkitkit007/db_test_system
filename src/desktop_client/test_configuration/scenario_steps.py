import enum

from src.schemas.enums import DataType


class StepType(enum.Enum):
    insert = "insert"
    create = "create"
    query = "query"


class ScenarioStep:
    """
    Базовый класс шага сценария (абстрактный).
    """

    def __init__(self, step_type: StepType, measure: bool = False) -> None:
        self.step_type = step_type
        self.measure = measure

    def __str__(self) -> str:
        # Отобразим во время отладки флаг measure
        measure_flag = "[M]" if self.measure else "[ ]"
        return f"{measure_flag} {self.step_type}"


class CreateTableStep(ScenarioStep):
    def __init__(
        self,
        table_name: str,
        columns: dict[str, DataType],
        measure: bool = False,
    ) -> None:
        super().__init__(StepType.create, measure)
        self.table_name = table_name
        self.columns = columns

    def __str__(self) -> str:
        measure_flag = "[M]" if self.measure else "[ ]"
        return f"{measure_flag} CreateTable: {self.table_name} (cols={self.columns})"


class InsertDataStep(ScenarioStep):
    def __init__(
        self,
        table_name: str,
        num_records: int,
        columns: dict[str, DataType],
        measure: bool = False,
    ) -> None:
        super().__init__(StepType.insert, measure)
        self.table_name = table_name
        self.num_records = num_records
        self.columns = columns

    def __str__(self) -> str:
        measure_flag = "[M]" if self.measure else "[ ]"
        return (
            f"{measure_flag} InsertData: table={self.table_name}, "
            f"num_records={self.num_records}, "
            f"columns={self.columns}"
        )


class QueryStep(ScenarioStep):
    def __init__(self, query: str, measure: bool = False) -> None:
        super().__init__(StepType.query, measure)
        self.query = query

    def __str__(self) -> str:
        measure_flag = "[M]" if self.measure else "[ ]"
        return f"{measure_flag} Query: {self.query}"

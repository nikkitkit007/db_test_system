class ScenarioStep:
    """
    Базовый класс шага сценария (абстрактный).
    """

    def __init__(self, step_type: str, measure: bool = False) -> None:
        self.step_type = step_type
        # measure=True означает, что этот шаг участвует в замере производительности
        self.measure = measure

    def __str__(self) -> str:
        # Отобразим во время отладки флаг measure
        measure_flag = "[M]" if self.measure else "[ ]"
        return f"{measure_flag} {self.step_type}"


class CreateTableStep(ScenarioStep):
    def __init__(
        self,
        table_name: str,
        columns: dict[str, str],
        measure: bool = False,
    ) -> None:
        super().__init__("Create Table", measure)
        self.table_name = table_name
        self.columns = columns  # {"col1": "int", "col2": "str", ...}

    def __str__(self) -> str:
        measure_flag = "[M]" if self.measure else "[ ]"
        return f"{measure_flag} CreateTable: {self.table_name} (cols={self.columns})"


class InsertDataStep(ScenarioStep):
    def __init__(
        self,
        table_name: str,
        num_records: int,
        measure: bool = False,
    ) -> None:
        super().__init__("Insert Data", measure)
        self.table_name = table_name
        self.num_records = num_records

    def __str__(self) -> str:
        measure_flag = "[M]" if self.measure else "[ ]"
        return (
            f"{measure_flag} InsertData: table={self.table_name}, "
            f"num_records={self.num_records}"
        )


class QueryStep(ScenarioStep):
    def __init__(self, query: str, measure: bool = False) -> None:
        super().__init__("Query", measure)
        self.query = query

    def __str__(self) -> str:
        measure_flag = "[M]" if self.measure else "[ ]"
        return f"{measure_flag} Query: {self.query}"

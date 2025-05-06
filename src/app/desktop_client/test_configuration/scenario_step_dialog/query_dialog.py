from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)
from src.app.core.llm.predictor import get_tables_list, possible_llm
from src.app.core.scenario_steps import CreateTableStep


class SelectTableStepsDialog(QDialog):
    def __init__(self, table_steps: list[CreateTableStep], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Выберите таблицы для создания")
        self.table_steps = table_steps  # исходный список шагов
        self.list_widget = QListWidget()
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout()

        instruction_label = QLabel("Отметьте таблицы, которые необходимо оставить:")
        layout.addWidget(instruction_label)

        for step in self.table_steps:
            item = QListWidgetItem(str(step))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)  # по умолчанию все выбраны
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self.setLayout(layout)

    def get_selected_steps(self):
        selected_steps = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_steps.append(self.table_steps[i])
        return selected_steps


class QueryDialog(QDialog):
    def __init__(
        self,
        query: str = "",
        parent=None,
        initial_threads: int = 1,
        initial_requests: int = 1,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("SQL Query")
        self.query = query or "SELECT * FROM table;"

        # LLM-селектор и кнопка анализа
        self.llm_selector = QComboBox()
        self.llm_selector.addItems(possible_llm)
        self.analyze_query_for_init_button = QPushButton(
            "Проанализировать запрос для создания схемы данных",
        )
        self.create_table_steps_for_run_query: list = []

        self.text_edit = QTextEdit()

        self.thread_count_box = QSpinBox()
        self.thread_count_box.setRange(1, 100)
        self.thread_count_box.setValue(initial_threads)

        self.request_count_box = QSpinBox()
        self.request_count_box.setRange(1, 10000)
        self.request_count_box.setValue(initial_requests)

        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout()

        # SQL-запрос
        layout.addWidget(QLabel("Введите SQL-запрос:"))
        self.text_edit.setPlainText(self.query)
        layout.addWidget(self.text_edit)

        # LLM + анализ
        h_llm = QHBoxLayout()
        h_llm.addWidget(QLabel("LLM-провайдер:"))
        h_llm.addWidget(self.llm_selector)
        h_llm.addWidget(self.analyze_query_for_init_button)
        layout.addLayout(h_llm)
        self.analyze_query_for_init_button.clicked.connect(self.analyze_query_for_init)

        # Параметры нагрузки
        h_load = QHBoxLayout()
        h_load.addWidget(QLabel("Потоков:"))
        h_load.addWidget(self.thread_count_box)
        h_load.addSpacing(20)
        h_load.addWidget(QLabel("Запросов:"))
        h_load.addWidget(self.request_count_box)
        layout.addLayout(h_load)

        # ОК/Отмена
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self.setLayout(layout)

    def analyze_query_for_init(self) -> None:
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.create_table_steps_for_run_query = get_tables_list(
                self.text_edit.toPlainText(),
                self.llm_selector.currentText(),
            )
        finally:
            QApplication.restoreOverrideCursor()

        dlg = SelectTableStepsDialog(self.create_table_steps_for_run_query, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.create_table_steps_for_run_query = dlg.get_selected_steps()

    def get_data(self) -> tuple[str, list, int, int]:
        """
        Возвращает:
          - текст SQL-запроса,
          - список CreateTableStep,
          - число потоков,
          - число запросов.
        """
        sql = self.text_edit.toPlainText().strip()
        return (
            sql,
            self.create_table_steps_for_run_query,
            self.thread_count_box.value(),
            self.request_count_box.value(),
        )

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout, QComboBox, QHBoxLayout,
)

from src.core.llm.predictor import possible_llm, get_tables_list
from src.core.scenario_steps import CreateTableStep


class SelectTableStepsDialog(QDialog):
    def __init__(self, table_steps: list[CreateTableStep], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Выберите таблицы для создания")
        self.table_steps = table_steps  # исходный список шагов
        self.list_widget = QListWidget()
        self.initUI()

    def initUI(self) -> None:
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
    def __init__(self, query: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("SQL Query")
        self.query = query or "SELECT * FROM table;"

        self.llm_selector = QComboBox()
        self.llm_selector.addItems(possible_llm)

        self.analyze_query_for_init_button = QPushButton(
            "Проанализировать запрос для создания схемы данных",
        )
        self.create_table_steps_for_run_query = []
        self.text_edit = QTextEdit()

        self.initUI()

    def initUI(self) -> None:
        layout = QVBoxLayout()

        instruction_label = QLabel("Введите SQL-запрос:")
        layout.addWidget(instruction_label)

        self.text_edit.setPlainText(self.query)

        layout.addWidget(self.text_edit)

        # Горизонтальный контейнер для выпадающего списка и кнопки
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.llm_selector)
        h_layout.addWidget(self.analyze_query_for_init_button)
        layout.addLayout(h_layout)

        self.analyze_query_for_init_button.clicked.connect(self.analyze_query_for_init)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self.setLayout(layout)

    def get_data(self) -> tuple[str, list]:
        sql_query = self.text_edit.toPlainText().strip()
        return sql_query, self.create_table_steps_for_run_query

    def analyze_query_for_init(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        llm = self.llm_selector.currentText()
        try:
            self.create_table_steps_for_run_query = get_tables_list(
                self.text_edit.toPlainText(),
                llm
            )
        finally:
            QApplication.restoreOverrideCursor()

        select_dialog = SelectTableStepsDialog(
            self.create_table_steps_for_run_query or [],
            self,
        )
        if select_dialog.exec() == QDialog.DialogCode.Accepted:
            self.create_table_steps_for_run_query = select_dialog.get_selected_steps()
        return self.create_table_steps_for_run_query

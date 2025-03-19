from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.desktop_client.test_configuration.scenario_steps import (
    CreateTableStep,
    InsertDataStep,
    QueryStep,
    ScenarioStep,
)


class CreateTableDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Table Step")
        self.table_name = ""
        self.columns = {}
        self.initUI()

    def initUI(self) -> None:
        layout = QFormLayout()
        self.line_table_name = QLineEdit()
        layout.addRow("Имя таблицы:", self.line_table_name)
        self.line_columns = QLineEdit()
        self.line_columns.setPlaceholderText("col1:int, col2:str, col3:date")
        layout.addRow("Колонки (col:type):", self.line_columns)
        btnBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        btnBox.accepted.connect(self.accept)
        btnBox.rejected.connect(self.reject)
        layout.addWidget(btnBox)
        self.setLayout(layout)

    def accept(self) -> None:
        self.table_name = self.line_table_name.text().strip()
        cols_text = self.line_columns.text().strip()
        self.columns = {}
        if cols_text:
            pairs = [pair.strip() for pair in cols_text.split(",")]
            for p in pairs:
                if ":" in p:
                    col, typ = p.split(":", 1)
                    self.columns[col.strip()] = typ.strip()
        super().accept()

    def get_data(self):
        return self.table_name, self.columns


class InsertDataDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Insert Data Step")
        self.table_name = ""
        self.num_records = 0
        self.data_types = []

        self.line_table_name = QLineEdit()
        self.spin_num_records = QSpinBox()
        self.line_data_types = QLineEdit()

        self.initUI()

    def initUI(self) -> None:
        layout = QFormLayout()
        layout.addRow("Имя таблицы:", self.line_table_name)
        self.spin_num_records.setRange(1, 1000000)
        layout.addRow("Количество записей:", self.spin_num_records)
        self.line_data_types.setPlaceholderText("int, str, date")
        layout.addRow("Типы данных:", self.line_data_types)
        btnBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        btnBox.accepted.connect(self.accept)
        btnBox.rejected.connect(self.reject)
        layout.addWidget(btnBox)
        self.setLayout(layout)

    def accept(self) -> None:
        self.table_name = self.line_table_name.text().strip()
        self.num_records = self.spin_num_records.value()
        types_raw = self.line_data_types.text().split(",")
        self.data_types = [t.strip() for t in types_raw if t.strip()]
        super().accept()

    def get_data(self):
        return self.table_name, self.num_records, self.data_types


class ScenarioStepItemWidget(QWidget):
    """
    Виджет-обёртка, который будет помещаться в QListWidgetItem.
    Содержит:
    - QLabel для описания шага
    - QCheckBox для флага measure
    """

    def __init__(self, step: ScenarioStep, parent=None) -> None:
        super().__init__(parent)
        self.step = step
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)

        self.label = QLabel(str(self.step))
        # сам чекбокс
        self.chk_measure = QCheckBox("Замерить?")
        self.chk_measure.setChecked(self.step.measure)
        self.chk_measure.stateChanged.connect(self.on_check_changed)

        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.chk_measure)
        self.setLayout(layout)

    def on_check_changed(self, state) -> None:
        self.step.measure = state == Qt.CheckState.Checked
        # Обновим текст label
        self.label.setText(str(self.step))

    def update_contents(self) -> None:
        """
        Если нужно обновлять после изменения step извне.
        """
        self.chk_measure.setChecked(self.step.measure)
        self.label.setText(str(self.step))


class ScenarioBuilderWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.steps = []
        self.step_list = QListWidget()
        self.btn_create_table = QPushButton("Добавить шаг: Создать таблицу")
        self.btn_insert_data = QPushButton("Добавить шаг: Наполнить таблицу")
        self.btn_add_query = QPushButton("Добавить шаг: Запрос")
        self.initUI()

    def initUI(self) -> None:
        layout = QVBoxLayout()

        # Кнопки добавления
        add_layout = QHBoxLayout()

        add_layout.addWidget(self.btn_create_table)
        add_layout.addWidget(self.btn_insert_data)
        add_layout.addWidget(self.btn_add_query)

        self.btn_create_table.clicked.connect(self.add_create_table_step)
        self.btn_insert_data.clicked.connect(self.add_insert_data_step)
        self.btn_add_query.clicked.connect(self.add_query_step)

        layout.addLayout(add_layout)

        # QListWidget
        self.step_list.setDragEnabled(True)
        self.step_list.setAcceptDrops(True)
        self.step_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.step_list.setDefaultDropAction(Qt.DropAction.MoveAction)

        self.step_list.installEventFilter(self)

        layout.addWidget(self.step_list)
        self.setLayout(layout)

    def eventFilter(self, source, event):
        if source is self.step_list and event.type() == QEvent.Type.Drop:
            result = super().eventFilter(source, event)
            self.reorder_steps_by_list()
            return result
        return super().eventFilter(source, event)

    def reorder_steps_by_list(self) -> None:
        """
        После Drag&Drop мы проходимся по QListWidgetItem-ам и восстанавливаем порядок self.steps
        в соответствии с визуальным порядком.
        """
        new_steps = []
        for i in range(self.step_list.count()):
            item = self.step_list.item(i)
            widget = self.step_list.itemWidget(item)
            if widget and hasattr(widget, "step"):
                new_steps.append(widget.step)
        self.steps = new_steps

    # -------------------------------------------
    # МЕТОДЫ ДОБАВЛЕНИЯ ШАГОВ
    # -------------------------------------------
    def add_create_table_step(self) -> None:
        dialog = CreateTableDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            table_name, columns = dialog.get_data()
            step = CreateTableStep(table_name, columns, measure=False)
            self.steps.append(step)
            self.add_step_to_list(step)

    def add_insert_data_step(self) -> None:
        dialog = InsertDataDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            table_name, num_records, data_types = dialog.get_data()
            step = InsertDataStep(table_name, num_records, measure=False)
            self.steps.append(step)
            self.add_step_to_list(step)

    def add_query_step(self) -> None:
        text, ok = QInputDialog.getMultiLineText(
            self,
            "SQL Query",
            "Введите SQL-запрос:",
            "SELECT * FROM table;",
        )
        if ok and text.strip():
            step = QueryStep(text.strip(), measure=False)
            self.steps.append(step)
            self.add_step_to_list(step)

    def add_step_to_list(self, step: ScenarioStep) -> None:
        """
        Создаём QListWidgetItem и помещаем в него ScenarioStepItemWidget.
        """
        item = QListWidgetItem(self.step_list)
        widget = ScenarioStepItemWidget(step)
        item.setSizeHint(widget.sizeHint())
        self.step_list.addItem(item)
        self.step_list.setItemWidget(item, widget)

    def update_step_list(self) -> None:
        """
        Полная перезагрузка списка из self.steps (если понадобится).
        """
        self.step_list.clear()
        for step in self.steps:
            item = QListWidgetItem()
            widget = ScenarioStepItemWidget(step)
            item.setSizeHint(widget.sizeHint())
            self.step_list.addItem(item)
            self.step_list.setItemWidget(item, widget)

    def get_scenario_steps(self):
        """
        Возвращает список шагов. (Перед запуском теста вызывайте reorder_steps_by_list()
        чтобы гарантировать, что порядок актуален.)
        """
        self.reorder_steps_by_list()
        return self.steps

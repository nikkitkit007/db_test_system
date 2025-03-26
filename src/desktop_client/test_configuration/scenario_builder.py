from pydantic import BaseModel
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.core.scenario_steps import (
    CreateTableStep,
    InsertDataStep,
    QueryStep,
    ScenarioStep,
    StepType,
)
from src.schemas.enums import DataType


class TableInfo(BaseModel):
    columns: dict[str, DataType]


class CreateTableDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Table Step")
        self.table_name = ""
        self.columns = {}
        self.column_fields = []  # список для хранения полей колонок
        self.line_table_name = QLineEdit()
        self.columns_layout = QVBoxLayout()

        self.initUI()

    def initUI(self) -> None:
        main_layout = QVBoxLayout()

        # Поле ввода имени таблицы
        form_layout = QFormLayout()
        form_layout.addRow("Имя таблицы:", self.line_table_name)
        main_layout.addLayout(form_layout)

        # Область для колонок
        main_layout.addLayout(self.columns_layout)

        # Кнопка добавления новой колонки
        add_col_button = QPushButton("➕ Добавить колонку")
        add_col_button.clicked.connect(self.add_column_field)
        main_layout.addWidget(add_col_button)

        # Кнопки OK / Cancel
        btnBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        btnBox.accepted.connect(self.accept)
        btnBox.rejected.connect(self.reject)
        main_layout.addWidget(btnBox)

        self.setLayout(main_layout)

    def add_column_field(self) -> None:
        col_layout = QHBoxLayout()

        col_name_edit = QLineEdit()
        col_name_edit.setPlaceholderText("Имя колонки")

        col_type_combo = QComboBox()
        col_type_combo.addItems(["int", "str", "float", "bool", "date"])

        col_layout.addWidget(QLabel("Имя:"))
        col_layout.addWidget(col_name_edit)
        col_layout.addWidget(QLabel("Тип:"))
        col_layout.addWidget(col_type_combo)

        container = QWidget()
        container.setLayout(col_layout)
        self.columns_layout.addWidget(container)

        self.column_fields.append((col_name_edit, col_type_combo))

    def accept(self) -> None:
        self.table_name = self.line_table_name.text().strip()
        self.columns = {}
        for name_edit, type_combo in self.column_fields:
            name = name_edit.text().strip()
            typ = type_combo.currentText().strip()
            if name:
                self.columns[name] = typ
        super().accept()

    def get_data(self):
        return self.table_name, self.columns


class InsertDataDialog(QDialog):
    def __init__(self, table_names: list[str], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Insert Data Step")
        self.table_name = ""
        self.num_records = 0
        self.data_types = []

        self.combo_table_name = QComboBox()
        self.combo_table_name.addItems(table_names)

        self.spin_num_records = QSpinBox()
        self.spin_num_records.setRange(1, 10000000)

        self.initUI()

    def initUI(self) -> None:
        layout = QFormLayout()
        layout.addRow("Имя таблицы:", self.combo_table_name)
        layout.addRow("Количество записей:", self.spin_num_records)

        btnBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        btnBox.accepted.connect(self.accept)
        btnBox.rejected.connect(self.reject)
        layout.addWidget(btnBox)
        self.setLayout(layout)

    def accept(self) -> None:
        self.table_name = self.combo_table_name.currentText().strip()
        self.num_records = self.spin_num_records.value()
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
        self.step.measure = state == Qt.CheckState.Checked.value
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
        self.table_infos: dict[str, TableInfo] = {}

        self.step_list = QListWidget()
        self.step_list.itemDoubleClicked.connect(self.edit_step)

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

    def edit_step(self, item: QListWidgetItem) -> None:
        widget = self.step_list.itemWidget(item)
        if not widget or not hasattr(widget, "step"):
            return

        step = widget.step

        if step.step_type == StepType.create:
            dialog = CreateTableDialog(self)
            dialog.line_table_name.setText(step.table_name)
            for col, typ in step.columns.items():
                dialog.add_column_field()
                name_edit, type_combo = dialog.column_fields[-1]
                name_edit.setText(col)
                index = type_combo.findText(typ)
                if index >= 0:
                    type_combo.setCurrentIndex(index)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                table_name, columns = dialog.get_data()
                step.table_name = table_name
                step.columns = columns
            self._update_tables_info()

        elif step.step_type == StepType.insert:
            table_names = list(self.table_infos.keys())
            dialog = InsertDataDialog(table_names, self)
            dialog.combo_table_name.setObjectName(step.table_name)
            dialog.spin_num_records.setValue(step.num_records)
            # Заполнение data_types при необходимости
            if dialog.exec() == QDialog.DialogCode.Accepted:
                table_name, num_records, data_types = dialog.get_data()
                step.table_name = table_name
                step.num_records = num_records
                # step.data_types = data_types  # если поле есть

        elif step.step_type == StepType.query:
            text, ok = QInputDialog.getMultiLineText(
                self,
                "Редактировать SQL-запрос",
                "Введите SQL-запрос:",
                step.query,
            )
            if ok and text.strip():
                step.query = text.strip()

        # Обновляем UI
        self.update_step_list()

    # -------------------------------------------
    # МЕТОДЫ ДОБАВЛЕНИЯ ШАГОВ
    # -------------------------------------------
    def add_create_table_step(self) -> None:
        dialog = CreateTableDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            table_name, columns = dialog.get_data()
            if not columns:
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    f"Добавьте атрибуты таблицы <{table_name}>!",
                )
                return
            step = CreateTableStep(table_name, columns, measure=False)
            self.steps.append(step)
            self.add_step_to_list(step)
            self._update_tables_info()

    def add_insert_data_step(self) -> None:
        table_names = list(self.table_infos.keys())
        dialog = InsertDataDialog(table_names, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            table_name, num_records, data_types = dialog.get_data()
            columns = self.table_infos[table_name].columns
            if columns is None:
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    f"Сначала нужно создать таблицу <{table_name}>!",
                )
                return

            step = InsertDataStep(
                table_name,
                num_records,
                columns=columns,
                measure=False,
            )
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

    def _update_tables_info(self):
        self.table_infos = {}
        for step in self.steps:
            if step.step_type == StepType.create:
                self.table_infos[step.table_name] = TableInfo(columns=step.columns)

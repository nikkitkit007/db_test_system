from functools import partial

from pydantic import BaseModel
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from src.app.core.scenario_steps import (
    ColumnDefinition,
    CreateTableStep,
    InsertDataStep,
    QueryStep,
    ScenarioStep,
    StepType,
)
from src.app.desktop_client.test_configuration.scenario_step_dialog.create_table_dialog import (
    CreateTableDialog,
)
from src.app.desktop_client.test_configuration.scenario_step_dialog.insert_data_dialog import (
    InsertDataDialog,
)
from src.app.desktop_client.test_configuration.scenario_step_dialog.query_dialog import (
    QueryDialog,
)


class TableInfo(BaseModel):
    columns: dict[str, ColumnDefinition]


class DraggableTableWidget(QTableWidget):
    def __init__(self, scenario_builder, parent=None) -> None:
        super().__init__(parent)
        self.scenario_builder = scenario_builder

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def dropEvent(self, event) -> None:
        if event.source() and self.isAncestorOf(event.source()):
            super().dropEvent(event)
            return
        selected_rows = sorted({i.row() for i in self.selectedItems()})
        if not selected_rows:
            event.ignore()
            return

        target_row = self.indexAt(event.position().toPoint()).row()
        if target_row == -1:
            target_row = self.rowCount()

        steps = self.scenario_builder.steps

        to_move = [steps[r] for r in reversed(selected_rows)]
        for r in reversed(selected_rows):
            del steps[r]

        num_removed_before = sum(1 for r in selected_rows if r < target_row)
        new_target_row = max(0, target_row - num_removed_before)

        for obj in reversed(to_move):
            steps.insert(new_target_row, obj)

        event.accept()

        self.scenario_builder.update_step_table()


class ScenarioBuilderWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.steps = []
        self.table_infos: dict[str, TableInfo] = {}

        # Setup table
        self.step_table = DraggableTableWidget(self)
        self.step_table.setColumnCount(5)
        self.step_table.hideColumn(4)
        self.step_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows,
        )
        self.step_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers,
        )
        self.step_table.cellDoubleClicked.connect(
            self.on_cell_double_clicked,
        )

        # Buttons
        self.btn_create_table = QPushButton()
        self.btn_insert_data = QPushButton()
        self.btn_add_query = QPushButton()

        # Build UI and then translate
        self.init_ui()
        self.retranslateUi()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        add_layout = QHBoxLayout()
        add_layout.addWidget(self.btn_create_table)
        add_layout.addWidget(self.btn_insert_data)
        add_layout.addWidget(self.btn_add_query)
        layout.addLayout(add_layout)

        self.btn_create_table.clicked.connect(self.add_create_table_step)
        self.btn_insert_data.clicked.connect(self.add_insert_data_step)
        self.btn_add_query.clicked.connect(self.add_query_step)

        layout.addWidget(self.step_table)
        self.setLayout(layout)

    def retranslateUi(self) -> None:
        headers = [
            self.tr("Учитывать"),
            self.tr("Тип операции"),
            self.tr("Доп информация"),
            self.tr("Удалить"),
        ]
        self.step_table.setHorizontalHeaderLabels(headers)

        self.btn_create_table.setText(self.tr("Создать таблицу"))
        self.btn_insert_data.setText(self.tr("Наполнить таблицу"))
        self.btn_add_query.setText(self.tr("Запрос"))

    def on_cell_double_clicked(self, row: int, column: int) -> None:
        if row < len(self.steps):
            self.edit_step(row)

    def edit_step(self, row: int) -> None:
        step = self.steps[row]

        if step.step_type == StepType.create:
            dialog = CreateTableDialog(self)
            dialog.line_table_name.setText(step.table_name)
            for col, col_def in step.columns.items():
                dialog.add_column_field()
                name_edit, type_combo, pk_flag = dialog.column_fields[-1]
                name_edit.setText(col)
                index = type_combo.findText(col_def.data_type)
                pk_flag.setChecked(col_def.primary_key)
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
            if dialog.exec() == QDialog.DialogCode.Accepted:
                table_name, num_records, data_types = dialog.get_data()
                step.table_name = table_name
                step.num_records = num_records
        elif step.step_type == StepType.query:
            dialog = QueryDialog(
                query=step.query,
                initial_threads=step.thread_count,
                initial_requests=step.request_count,
                parent=self,
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                query, additional_steps, thread_count, request_count = dialog.get_data()
                step.query = query
                step.thread_count = thread_count
                step.request_count = request_count

        self.update_step_table()

    def set_scenario(self, scenario_steps: list[ScenarioStep]) -> None:
        self.steps = scenario_steps
        self.update_step_table()
        self._update_tables_info()

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
            step = CreateTableStep(
                table_name=table_name,
                columns=columns,
                measure=False,
            )
            self.steps.append(step)
            self.update_step_table()
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
                table_name=table_name,
                num_records=num_records,
                columns=columns,
                measure=False,
            )
            self.steps.append(step)
            self.update_step_table()

    def add_query_step(self) -> None:
        dialog = QueryDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            query, additional_steps, thread_count, request_count = dialog.get_data()
            step = QueryStep(
                query=query,
                thread_count=thread_count,
                request_count=request_count,
                measure=False,
            )
            if additional_steps:
                for add_step in additional_steps:
                    updated = False
                    for existing_step in self.steps:
                        if (
                            existing_step.step_type == StepType.create
                            and existing_step.table_name == add_step.table_name
                        ):
                            existing_step.columns.update(add_step.columns)
                            updated = True
                            break
                    if not updated:
                        self.steps.append(add_step)
            self.steps.append(step)
            self.update_step_table()

    def update_step_table(self) -> None:
        self.step_table.setRowCount(0)
        for idx, step in enumerate(self.steps):
            self.step_table.insertRow(idx)

            # Колонка "Учитывать": CheckBox
            chk_box = QCheckBox()
            chk_box.setChecked(step.measure)
            chk_box.stateChanged.connect(
                lambda state, s=step: setattr(
                    s,
                    "measure",
                    state == Qt.CheckState.Checked.value,
                ),
            )
            self.step_table.setCellWidget(idx, 0, chk_box)

            # Колонка "Тип операции": тип шага (create, insert, query)
            op_item = QTableWidgetItem(step.step_type.value)
            # Сохраняем объект шага в ячейке (UserRole)
            op_item.setData(Qt.ItemDataRole.UserRole, step)
            self.step_table.setItem(idx, 1, op_item)

            # Колонка "Доп информация": краткое описание шага
            info_item = QTableWidgetItem(str(step))
            self.step_table.setItem(idx, 2, info_item)

            # Колонка "Удалить": кнопка удаления
            btn_delete = QPushButton("Удалить")
            btn_delete.clicked.connect(partial(self.delete_step_by_step, step))
            self.step_table.setCellWidget(idx, 3, btn_delete)

            # Скрытая колонка (индекс 4): храним объект шага
            hidden_item = QTableWidgetItem()
            hidden_item.setData(Qt.ItemDataRole.UserRole, step)
            self.step_table.setItem(idx, 4, hidden_item)

        self.step_table.resizeColumnsToContents()

    def delete_step_by_step(self, step: ScenarioStep) -> None:
        if step in self.steps:
            self.steps.remove(step)
            self.update_step_table()

    def get_scenario_steps(self):
        return self.steps

    def _update_tables_info(self) -> None:
        self.table_infos = {}
        for step in self.steps:
            if step.step_type == StepType.create:
                self.table_infos[step.table_name] = TableInfo(columns=step.columns)

    def clear(self) -> None:
        self.steps = []
        self.table_infos = {}
        self.step_table.setRowCount(0)

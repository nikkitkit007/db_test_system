from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from src.core.scenario_steps import ColumnDefinition
from src.schemas.enums import data_type_list


class CreateTableDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Table Step")
        self.table_name = ""
        self.columns = {}
        self.column_fields: list[tuple[QLineEdit, QComboBox, QCheckBox]] = (
            []
        )  # список для хранения полей колонок
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
        col_type_combo.addItems(data_type_list)

        pk_checkbox = QCheckBox("PK")

        col_layout.addWidget(QLabel("Имя:"))
        col_layout.addWidget(col_name_edit)
        col_layout.addWidget(QLabel("Тип:"))
        col_layout.addWidget(col_type_combo)
        col_layout.addWidget(pk_checkbox)

        container = QWidget()
        container.setLayout(col_layout)
        self.columns_layout.addWidget(container)

        self.column_fields.append((col_name_edit, col_type_combo, pk_checkbox))

    def accept(self) -> None:
        self.table_name = self.line_table_name.text().strip()
        self.columns = {}
        for name_edit, type_combo, pk_checkbox in self.column_fields:
            name = name_edit.text().strip()
            typ = type_combo.currentText().strip()
            primary_key = pk_checkbox.isChecked()
            if name:
                self.columns[name] = ColumnDefinition(
                    data_type=typ,
                    primary_key=primary_key,
                )
        super().accept()

    def get_data(self) -> tuple[str, dict[str, ColumnDefinition]]:
        return self.table_name, self.columns

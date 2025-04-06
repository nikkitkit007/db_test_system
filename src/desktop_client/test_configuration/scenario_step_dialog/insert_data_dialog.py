from PyQt6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QSpinBox


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

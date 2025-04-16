from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget, QMessageBox,
)


class ScanHostDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Сканирование Docker‑хоста")
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        # Ввод хоста
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("Хост (tcp://host:port):"))
        self.host_edit = QLineEdit()
        self.host_edit.setText("tcp://localhost:2375")

        host_layout.addWidget(self.host_edit)
        self.scan_btn = QPushButton("Сканировать")
        host_layout.addWidget(self.scan_btn)
        layout.addLayout(host_layout)

        # Таблица с чекбоксами
        self.table = QTableWidget(0, 3, self)
        self.table.setHorizontalHeaderLabels(["", "Имя контейнера", "Образ"])
        self.table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
        )
        layout.addWidget(self.table, 1)

        # Кнопка добавить
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        self.add_selected_btn = QPushButton("Добавить выбранные")
        btn_layout.addWidget(self.add_selected_btn)
        layout.addLayout(btn_layout)

        # Сигналы
        self.scan_btn.clicked.connect(self.on_scan)
        self.add_selected_btn.clicked.connect(self.accept)

        # Результат
        self.containers: list[dict] = []

    def on_scan(self) -> None:
        """Вызывается по нажатию 'Сканировать' — ставим host, вызываем DockerManager."""
        from src.manager.docker_manager import DockerManager
        from src.schemas.test_init import DockerHostConfig

        host_url = self.host_edit.text().strip()
        if not host_url:
            return  # можно добавить QMessageBox.warning

        cfg = DockerHostConfig(base_url=host_url)
        mgr = DockerManager(host_config=cfg)
        try:
            containers = mgr.scan_host_containers()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сканирования", str(e))
            return

        # Обновляем таблицу
        self.table.setRowCount(0)
        self.containers = containers
        for i, c in enumerate(containers):
            self.table.insertRow(i)
            # чекбокс
            chk = QCheckBox()
            cell = QWidget()
            lay = QHBoxLayout(cell)
            lay.addWidget(chk)
            lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.setContentsMargins(0, 0, 0, 0)
            cell.setLayout(lay)
            self.table.setCellWidget(i, 0, cell)
            # имя и образ
            self.table.setItem(i, 1, QTableWidgetItem(c["name"]))
            self.table.setItem(i, 2, QTableWidgetItem(c["image"]))

    def selected_containers(self) -> list[dict]:
        """Вернёт список отмеченных пользователем контейнеров."""
        result = []
        for row in range(self.table.rowCount()):
            # достаём наш виджет‑чекбокс
            cell = self.table.cellWidget(row, 0)
            chk: QCheckBox = cell.layout().itemAt(0).widget()
            if chk.isChecked():
                result.append(self.containers[row])
        return result

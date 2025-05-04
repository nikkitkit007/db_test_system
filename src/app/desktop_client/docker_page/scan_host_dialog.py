from docker.errors import DockerException
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from src.app.manager.docker_manager import DockerManager
from src.app.schemas.schema import DockerHostConfig


class ScanHostDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # Виджеты и компоновка
        self.host_label = QLabel()
        self.host_edit = QLineEdit()
        self.scan_btn = QPushButton()
        self.table = QTableWidget(0, 3)
        self.add_selected_btn = QPushButton()

        self.containers: list[dict] = []

        self.init_ui()
        self.retranslateUi()

    def init_ui(self) -> None:
        self.resize(600, 400)
        layout = QVBoxLayout(self)

        # ─── Ввод хоста ───
        host_layout = QHBoxLayout()
        host_layout.addWidget(self.host_label)
        host_layout.addWidget(self.host_edit)
        host_layout.addWidget(self.scan_btn)
        layout.addLayout(host_layout)

        # ─── Таблица с чекбоксами ───
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

        # ─── Кнопка добавить ───
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.add_selected_btn)
        layout.addLayout(btn_layout)

        # Сигналы
        self.scan_btn.clicked.connect(self.on_scan)
        self.add_selected_btn.clicked.connect(self.accept)

    def retranslateUi(self) -> None:
        # Заголовок окна
        self.setWindowTitle(self.tr("Сканирование Docker‑хоста"))

        # Метка и кнопки
        self.host_label.setText(self.tr("Хост (tcp://host:port):"))
        # дефолт текста
        self.host_edit.setText(self.tr("tcp://localhost:2375"))
        self.scan_btn.setText(self.tr("Сканировать"))
        self.add_selected_btn.setText(self.tr("Добавить выбранные"))

        # Заголовки таблицы
        headers = [
            "",
            self.tr("Имя контейнера"),
            self.tr("Образ"),
        ]
        self.table.setHorizontalHeaderLabels(headers)

    def on_scan(self) -> None:
        """
        Сначала пытаемся соединиться с Docker.
        Если в поле хоста пусто или стоит tcp://localhost:2375,
        используем локальное подключение через docker.from_env().
        Иначе — через DockerHostConfig(base_url=...).
        """
        host_url = self.host_edit.text().strip()
        use_local = host_url in ("", "tcp://localhost:2375")

        # Создаём менеджер
        try:
            if use_local:
                mgr = DockerManager(host_config=None, timeout=3)
            else:
                cfg = DockerHostConfig(
                    base_url=host_url,
                    # TLS-поля в этом диалоге мы не вводим, поэтому None
                    tls_ca_cert=None,
                    tls_client_cert=None,
                    tls_client_key=None,
                    tls_verify=True,
                )
                mgr = DockerManager(host_config=cfg, timeout=3)
        except DockerException as e:
            QMessageBox.critical(self, "Ошибка подключения", str(e))
            return

        # Получаем список контейнеров
        try:
            containers = mgr.scan_host_containers()
        except DockerException as e:
            QMessageBox.critical(self, "Ошибка сканирования", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Неожиданная ошибка", str(e))
            return

        if not containers:
            QMessageBox.information(
                self,
                "Результат",
                "Контейнеры не найдены или нет доступа к Docker‑демону.",
            )
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
            cell = self.table.cellWidget(row, 0)
            chk: QCheckBox = cell.layout().itemAt(0).widget()
            if chk.isChecked():
                result.append(self.containers[row])
        return result

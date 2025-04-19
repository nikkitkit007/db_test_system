import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt6.sip import isdeleted

from src.config.config import settings
from src.config.log import get_logger
from src.desktop_client.config import PageIndex
from src.desktop_client.docker_page.docker_config import docker_image_icon_path
from src.desktop_client.test_runner import DockerTestRunner
from src.schemas.schema import DockerHostConfig, TestSystemConfig
from src.storage.db_manager.docker_storage import docker_db_manager
from src.storage.db_manager.scenario_storage import scenario_db_manager

test_config_icon_path = os.path.join(settings.ICONS_PATH, "test_config_icon.svg")

logger = get_logger(__name__)


@dataclass
class TestHandle:
    thread: QThread
    worker: object  # DockerTestRunner
    tab_index: int


class ConfigApp(QWidget):
    test_completed = pyqtSignal()

    def __init__(self, stacked_widget: QStackedWidget) -> None:
        super().__init__()
        self.db_image_label = QLabel("Выберите образ СУБД:")
        self.db_image_combo = QComboBox()
        self.scenario_label = QLabel("Выберите Сценарий тестирования:")
        self.scenario_combo = QComboBox()
        self.operation_combo = QComboBox()
        self.records_spinbox = QSpinBox()
        self.data_types_edit = QLineEdit()
        self.stacked_widget: QStackedWidget | None = None

        # Добавляем радиокнопки для выбора типа подключения
        self.create_new_db_radio = QRadioButton("Создать новую БД")
        self.connect_existing_db_radio = QRadioButton("Подключиться к существующей БД")
        self.create_new_db_radio.setChecked(True)
        self.stop_radio = QCheckBox("Остановить контейнер по завершении")
        self.remove_radio = QCheckBox("Удалить контейнер после остановки")

        self.stop_radio.setChecked(True)
        self.remove_radio.setChecked(False)
        self.remove_radio.toggled.connect(
            lambda state: self.stop_radio.setChecked(True) if state else None,
        )

        # Радиокнопки для выбора Docker‑хоста
        self.local_docker_radio = QRadioButton("Локальный Docker")
        self.remote_docker_radio = QRadioButton("Удалённый Docker")
        self.local_docker_radio.setChecked(True)
        # Поля для подключения к существующей БД
        self.docker_endpoint_label = QLabel("Docker‑хост:")
        self.docker_endpoint_edit = QLineEdit()
        self.docker_endpoint_edit.setText("tcp://localhost:2375")
        self.docker_endpoint_edit.setPlaceholderText("или unix:///var/run/docker.sock")

        self.add_image_button = QPushButton("Добавить новый образ")
        self.add_scenario_button = QPushButton("Добавить новый сценарий")
        self.start_button = QPushButton("Запустить тест")

        self.stacked_widget = stacked_widget

        # self.thread = None
        # self.worker = None
        self.tests = []  # список словарей {thread, worker, log_widget}
        self.log_tabs = QTabWidget()

        self.initUI()

        self.load_docker_images()
        self.load_scenarios()

    def initUI(self) -> None:
        self.setWindowTitle("Docker Configurator")
        main_layout = QVBoxLayout(self)
        QFont("Arial", 14)

        # ─── Блок: подключение к Docker ───
        docker_host_group = QGroupBox("Подключение к Docker")
        host_layout = QGridLayout()
        # радиокнопки локального/удалённого Docker
        self.local_docker_radio = QRadioButton("Локальный Docker")
        self.remote_docker_radio = QRadioButton("Удалённый Docker")
        self.local_docker_radio.setChecked(True)
        host_layout.addWidget(self.local_docker_radio, 0, 0)
        host_layout.addWidget(self.remote_docker_radio, 0, 1)
        # строка ввода endpoint
        self.docker_endpoint_label = QLabel("Docker‑хост:")
        self.docker_endpoint_edit = QLineEdit("tcp://localhost:2375")
        self.docker_endpoint_edit.setPlaceholderText("или unix:///var/run/docker.sock")
        host_layout.addWidget(self.docker_endpoint_label, 1, 0)
        host_layout.addWidget(self.docker_endpoint_edit, 1, 1, 1, 2)
        docker_host_group.setLayout(host_layout)
        main_layout.addWidget(docker_host_group)

        # скрываем endpoint при локальном режиме
        self.docker_endpoint_label.hide()
        self.docker_endpoint_edit.hide()
        # показываем только когда переключились на “Удалённый Docker”
        self.remote_docker_radio.toggled.connect(
            lambda remote: (
                self.docker_endpoint_label.setVisible(remote),
                self.docker_endpoint_edit.setVisible(remote),
            ),
        )

        db_mode_group = QGroupBox("Режим подключения к БД")
        db_mode_layout = QHBoxLayout()
        db_mode_layout.addWidget(self.create_new_db_radio)
        db_mode_layout.addWidget(self.connect_existing_db_radio)
        db_mode_group.setLayout(db_mode_layout)
        main_layout.addWidget(db_mode_group)

        # ─── Блок: выбор образа ───
        docker_group = QGroupBox("Образы Docker")
        docker_layout = QHBoxLayout()
        docker_layout.addWidget(self.db_image_label)
        docker_layout.addWidget(self.db_image_combo)
        docker_layout.addWidget(self.add_image_button)
        docker_group.setLayout(docker_layout)
        main_layout.addWidget(docker_group)

        # ─── Блок: действие после теста ───
        action_group = QGroupBox("Действие по выполнении")
        action_layout = QHBoxLayout()
        self.stop_radio.setChecked(True)
        action_layout.addWidget(self.stop_radio)
        action_layout.addWidget(self.remove_radio)
        action_group.setLayout(action_layout)
        main_layout.addWidget(action_group)

        # ─── Блок: сценарии ───
        scenario_group = QGroupBox("Сценарии тестирования")
        scenario_layout = QHBoxLayout()
        scenario_layout.addWidget(self.scenario_label)
        scenario_layout.addWidget(self.scenario_combo)
        scenario_layout.addWidget(self.add_scenario_button)
        scenario_group.setLayout(scenario_layout)
        main_layout.addWidget(scenario_group)

        main_layout.addStretch()

        # ─── Кнопка запуска и вкладки с логами ───
        self.start_button.clicked.connect(self.start_process)
        main_layout.addWidget(self.start_button)
        self.log_tabs.setTabsClosable(True)
        self.log_tabs.tabCloseRequested.connect(self.close_log_tab)
        main_layout.addWidget(self.log_tabs, 3)

        self.setLayout(main_layout)

    def on_docker_mode_changed(self, remote: bool) -> None:
        """Показывает поле endpoint только в режиме 'Удалённый Docker'."""
        self.docker_endpoint_label.setVisible(remote)
        self.docker_endpoint_edit.setVisible(remote)

    def open_scenario_builder(self) -> None:
        self.stacked_widget.setCurrentIndex(PageIndex.scenario_page)

    def open_docker_config_builder(self) -> None:
        self.stacked_widget.setCurrentIndex(PageIndex.docker_page)

    def load_docker_images(self) -> None:
        self.db_image_combo.clear()
        icon = QIcon(docker_image_icon_path)
        images = docker_db_manager.get_all_docker_images()
        for image in images:
            display_text = f"{image.image_name}  ({image.config_name})"
            self.db_image_combo.addItem(icon, display_text, userData=image.config_name)

            raw = image.config or {}
            if isinstance(raw, str):
                try:
                    cfg = json.loads(raw)
                except json.JSONDecodeError:
                    cfg = {}
            else:
                cfg = raw

            tooltip = (
                f"Config Name: {image.config_name}\n"
                f"Image:       {image.image_name}\n"
                f"Host:        {cfg.get('host', '')}\n"
                f"Port:        {cfg.get('port', '')}\n"
                f"User:        {cfg.get('user', '')}\n"
                f"DB:          {cfg.get('db', '')}\n"
                f"Env:         {json.dumps(cfg.get('env', {}), ensure_ascii=False)}"
            )
            idx = self.db_image_combo.count() - 1
            self.db_image_combo.setItemData(idx, tooltip, Qt.ItemDataRole.ToolTipRole)

    def load_scenarios(self) -> None:
        scenarios = scenario_db_manager.get_all_scenarios()
        self.scenario_combo.clear()
        for scenario in scenarios:
            self.scenario_combo.addItem(scenario.name)

    def start_process(self) -> None:
        QMessageBox.information(self, "Информация", "Тест успешно запущен!")
        try:
            self.run_test_in_thread()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка запуска теста: {e}")
            logger.exception(f"Ошибка запуска теста: {e}")

    def run_test_in_thread(self) -> None:
        # 1) собираем входные данные
        scenario = scenario_db_manager.get_scenario(
            name=self.scenario_combo.currentText(),
        )
        selected_cfg = self.db_image_combo.currentData()

        test_system_config = TestSystemConfig(
            use_existing=self.connect_existing_db_radio.isChecked(),
            stop_after=self.stop_radio.isChecked(),
            remove_after=self.remove_radio.isChecked(),
        )

        if self.remote_docker_radio.isChecked():
            base = self.docker_endpoint_edit.text().strip()
        else:
            base = None
        docker_host_config = DockerHostConfig(base_url=base)

        # 2) создаём объекты
        thread = QThread(self)
        worker = DockerTestRunner(
            db_config=docker_db_manager.get_image(config_name=selected_cfg),
            scenario_steps=scenario.get_steps(),
            test_system_config=test_system_config,
            docker_host=docker_host_config,
        )
        worker.moveToThread(thread)

        # 3) отдельная вкладка‑лог
        log_widget = QPlainTextEdit()
        log_widget.setReadOnly(True)
        tab_name = f"{scenario.name} @ {datetime.now(UTC).strftime('%H:%M:%S')}"
        tab_idx = self.log_tabs.addTab(log_widget, tab_name)
        self.log_tabs.setCurrentIndex(tab_idx)

        handle = TestHandle(thread=thread, worker=worker, tab_index=tab_idx)
        self.tests.append(handle)

        # 5) соединяем сигналы
        worker.log.connect(log_widget.appendPlainText)
        thread.started.connect(worker.run)

        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        worker.error.connect(lambda msg: QMessageBox.critical(self, "Ошибка", msg))
        worker.finished.connect(lambda w=worker: self.on_test_finished(w))

        # 6) запускаем
        thread.start()

    def on_test_finished(self, finished_worker) -> None:
        for h in self.tests:
            if h.worker is finished_worker:
                txt = self.log_tabs.tabText(h.tab_index)
                if not txt.endswith(" ✅"):
                    self.log_tabs.setTabText(h.tab_index, txt + " ✅")
                break
        self.test_completed.emit()

    def close_log_tab(self, index: int) -> None:
        handle = next((h for h in self.tests if h.tab_index == index), None)
        if handle is None:
            self.log_tabs.removeTab(index)
            return

        thread = handle.thread
        if thread and not isdeleted(thread) and thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Тест ещё выполняется",
                "Остановить тест и закрыть вкладку?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            try:
                thread.requestInterruption()
                thread.quit()
                thread.wait(2000)
            except RuntimeError:
                # объект уже удалён — игнорируем
                pass

        self.log_tabs.removeTab(index)
        self.tests.remove(handle)

        for h in self.tests:
            if h.tab_index > index:
                h.tab_index -= 1

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.load_docker_images()
        self.load_scenarios()

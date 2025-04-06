import os

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.config.config import settings
from src.config.log import get_logger
from src.desktop_client.config import PageIndex
from src.desktop_client.test_runner import DockerTestRunner
from src.storage.config_storage import config_manager

test_config_icon_path = os.path.join(settings.ICONS_PATH, "test_config_icon.svg")

logger = get_logger(__name__)


class ConfigApp(QWidget):
    test_completed = pyqtSignal()  # Сигнал для обновления результатов

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

        self.add_image_button = QPushButton("Добавить новый образ")
        self.add_scenario_button = QPushButton("Добавить новый сценарий")
        self.start_button = QPushButton("Запустить тест")

        self.stacked_widget = stacked_widget  # Ссылка на QStackedWidget

        self.thread = None
        self.worker = None

        self.initUI()

        self.load_docker_images()
        self.load_scenarios()

    def initUI(self) -> None:
        self.setWindowTitle("Docker Configurator")
        layout = QVBoxLayout()
        QFont("Arial", 14)

        # ---------------- Группа: Образы Docker ----------------
        docker_group = QGroupBox("Образы Docker")
        docker_layout = QGridLayout()
        docker_group.setLayout(docker_layout)

        self.add_image_button.clicked.connect(self.open_docker_config_builder)

        docker_layout.addWidget(self.db_image_label, 0, 0)
        docker_layout.addWidget(self.db_image_combo, 0, 1)
        docker_layout.addWidget(self.add_image_button, 0, 2)

        layout.addWidget(docker_group)

        # ---------------- Группа: Сценарии тестирования ----------------
        scenario_group = QGroupBox("Сценарии тестирования")
        scenario_layout = QGridLayout()
        scenario_group.setLayout(scenario_layout)

        self.add_scenario_button.clicked.connect(self.open_scenario_builder)

        scenario_layout.addWidget(self.scenario_label, 0, 0)
        scenario_layout.addWidget(self.scenario_combo, 0, 1)
        scenario_layout.addWidget(self.add_scenario_button, 0, 2)

        layout.addWidget(scenario_group)

        layout.addStretch()

        # Кнопка запуска
        self.start_button.clicked.connect(self.start_process)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def open_scenario_builder(self) -> None:
        """
        Переключает отображение на страницу ScenarioBuilderPage.
        """
        self.stacked_widget.setCurrentIndex(PageIndex.scenario_page)

    def open_docker_config_builder(self) -> None:
        self.stacked_widget.setCurrentIndex(PageIndex.docker_page)

    def load_docker_images(self) -> None:
        """Загружает образы Docker из базы данных в выпадающий список."""
        docker_images = config_manager.get_all_docker_images()
        self.db_image_combo.clear()
        for image in docker_images:
            self.db_image_combo.addItem(image.name)

    def load_scenarios(self) -> None:
        scenarios = config_manager.get_all_scenarios()
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
        if self.thread is not None and self.thread.isRunning():
            QMessageBox.warning(self, "Предупреждение", "Тест уже выполняется!")
            return

        scenario = config_manager.get_scenario(name=self.scenario_combo.currentText())

        self.thread = QThread(self)
        self.worker = DockerTestRunner(
            db_image=self.db_image_combo.currentText(),
            scenario_steps=scenario.get_steps(),
            parent=None,
        )
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.finished.connect(self.on_test_finished)
        self.thread.start()

    def on_test_finished(self) -> None:
        self.test_completed.emit()
        logger.info("🟢 Тест завершён.")
        self.thread = None
        self.worker = None

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.load_docker_images()
        self.load_scenarios()

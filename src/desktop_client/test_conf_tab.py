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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.config.config import settings
from src.config.log import get_logger
from src.desktop_client.config import PageIndex
from src.desktop_client.test_configuration.scenario_builder import ScenarioBuilderWidget
from src.desktop_client.test_runner import DockerTestRunner
from src.storage.config_storage import config_manager

test_config_icon_path = os.path.join(settings.ICONS_PATH, "test_config_icon.svg")

logger = get_logger(__name__)


class ScenarioBuilderPage(QWidget):
    steps_updated = pyqtSignal(list)

    def __init__(self, stacked_widget: QStackedWidget) -> None:
        super().__init__()
        self.stacked_widget = stacked_widget
        self.scenario_builder = ScenarioBuilderWidget(self)
        self.back_button = QPushButton("Назад")

        self.initUI()

    def initUI(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self.scenario_builder)
        self.back_button.clicked.connect(self.go_back)
        layout.addWidget(self.back_button)

        self.setLayout(layout)

    def go_back(self) -> None:
        """Возвращает пользователя в ConfigApp."""
        if self.stacked_widget is not None:
            self.steps_updated.emit(self.scenario_builder.get_scenario_steps())
            self.stacked_widget.setCurrentIndex(PageIndex.config_app)


class ConfigApp(QWidget):
    test_completed = pyqtSignal()  # Сигнал для обновления результатов

    def __init__(self, stacked_widget: QStackedWidget) -> None:
        super().__init__()
        self.db_image_label = QLabel("Выберите образ СУБД:")
        self.db_image_combo = QComboBox()
        self.operation_combo = QComboBox()
        self.records_spinbox = QSpinBox()
        self.data_types_edit = QLineEdit()
        self.stacked_widget: QStackedWidget | None = None

        self.add_image_button = QPushButton("Добавить новый образ")
        self.open_scenario_builder_btn = QPushButton("Открыть конструктор сценариев")
        self.preview_text = QTextEdit()
        self.start_button = QPushButton("Запустить тест")

        self.stacked_widget = stacked_widget  # Ссылка на QStackedWidget

        self.thread = None
        self.worker = None

        self.initUI()
        self.reset_parameters()
        self.load_docker_images()

        self.steps_from_scenario = []

    def update_steps(self, steps: list) -> None:
        self.steps_from_scenario = steps
        self.update_preview()

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

        # --- Кнопка открытия конструктора сценариев ---
        self.open_scenario_builder_btn.clicked.connect(self.open_scenario_builder)
        layout.addWidget(self.open_scenario_builder_btn)

        # Группа: Предварительный просмотр
        preview_group = QGroupBox("Предварительный просмотр конфигурации")
        preview_layout = QVBoxLayout()
        preview_group.setLayout(preview_layout)

        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)

        layout.addWidget(preview_group)

        # Кнопка запуска
        self.start_button.clicked.connect(self.start_process)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def open_scenario_builder(self) -> None:
        """
        Переключает отображение на страницу ScenarioBuilderPage.
        """
        self.stacked_widget.setCurrentIndex(PageIndex.scenario_builder_page)

    def open_docker_config_builder(self) -> None:
        self.stacked_widget.setCurrentIndex(PageIndex.docker_page)

    def reset_parameters(self) -> None:
        self.db_image = ""
        self.operation = ""
        self.num_records = 0
        self.data_types = []

    def load_docker_images(self) -> None:
        """Загружает образы Docker из базы данных в выпадающий список."""
        docker_images = config_manager.get_all_docker_images()
        self.db_image_combo.clear()
        for image in docker_images:
            self.db_image_combo.addItem(image.name)

    def update_preview(self) -> None:
        self.db_image = self.db_image_combo.currentText()
        self.operation = self.operation_combo.currentText()
        self.num_records = self.records_spinbox.value()
        self.data_types = self.data_types_edit.text()

        steps_info = "\n".join([str(step) for step in self.steps_from_scenario])
        preview = (
            f"""Образ СУБД: {self.db_image}
{steps_info}
""")
        self.preview_text.setText(preview)

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

        self.thread = QThread(self)
        self.worker = DockerTestRunner(
            db_image=self.db_image,
            scenario_steps=self.steps_from_scenario,
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

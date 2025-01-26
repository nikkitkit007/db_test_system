from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.config.log import get_logger
from src.manager.db_manager import DatabaseManager
from src.manager.docker_manager import DockerManager
from src.storage.test_result_storage import sqlite_manager
from src.utils import clear_container_name, generate_csv, load_csv_to_db, measure_performance

logger = get_logger(__name__)


class ConfigApp(QWidget):
    test_completed = pyqtSignal()  # Сигнал для обновления результатов

    def __init__(self) -> None:
        super().__init__()
        self.docker_manager = DockerManager()
        self.initUI()
        self.reset_parameters()
        self.load_docker_images()

    def initUI(self) -> None:
        self.setWindowTitle("Docker Configurator")
        layout = QVBoxLayout()
        QFont("Arial", 14)

        # Группа: Образы Docker
        docker_group = QGroupBox("Образы Docker")
        docker_layout = QGridLayout()
        docker_group.setLayout(docker_layout)

        # Выбор Docker-образа
        self.db_image_label = QLabel("Выберите образ СУБД:")
        self.db_image_combo = QComboBox()
        docker_layout.addWidget(self.db_image_label, 0, 0)
        docker_layout.addWidget(self.db_image_combo, 0, 1)

        # Добавление пользовательских образов
        self.custom_image_label = QLabel("Добавить пользовательский образ:")
        self.custom_image_edit = QLineEdit()
        self.custom_image_edit.setPlaceholderText("Например: custom/image:tag")
        self.add_image_button = QPushButton("Добавить")
        self.add_image_button.clicked.connect(self.add_custom_image)
        self.delete_image_button = QPushButton("Удалить")
        self.delete_image_button.clicked.connect(self.delete_custom_image)

        docker_layout.addWidget(self.custom_image_label, 1, 0)
        docker_layout.addWidget(self.custom_image_edit, 1, 1)
        docker_layout.addWidget(self.add_image_button, 2, 0)
        docker_layout.addWidget(self.delete_image_button, 2, 1)

        layout.addWidget(docker_group)

        # Группа: Параметры теста
        test_group = QGroupBox("Параметры теста")
        test_layout = QGridLayout()
        test_group.setLayout(test_layout)

        # Тип операции
        self.operation_label = QLabel("Выберите тип операции:")
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["INSERT", "SELECT", "JOIN"])
        test_layout.addWidget(self.operation_label, 0, 0)
        test_layout.addWidget(self.operation_combo, 0, 1)

        # Количество записей
        self.records_label = QLabel("Количество записей:")
        self.records_spinbox = QSpinBox()
        self.records_spinbox.setRange(1, 100000)
        test_layout.addWidget(self.records_label, 1, 0)
        test_layout.addWidget(self.records_spinbox, 1, 1)

        # Типы данных
        self.data_types_label = QLabel("Типы данных (через запятую):")
        self.data_types_edit = QLineEdit()
        self.data_types_edit.setPlaceholderText("Например: int, str, date")
        test_layout.addWidget(self.data_types_label, 2, 0)
        test_layout.addWidget(self.data_types_edit, 2, 1)

        layout.addWidget(test_group)

        # Группа: Предварительный просмотр
        preview_group = QGroupBox("Предварительный просмотр конфигурации")
        preview_layout = QVBoxLayout()
        preview_group.setLayout(preview_layout)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)

        layout.addWidget(preview_group)

        # Кнопка запуска
        self.start_button = QPushButton("Запустить тест")
        self.start_button.clicked.connect(self.start_process)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def reset_parameters(self) -> None:
        self.db_image = ""
        self.operation = ""
        self.num_records = 0
        self.data_types = []

    def load_docker_images(self) -> None:
        """Загружает образы Docker из базы данных в выпадающий список."""
        try:
            docker_images = sqlite_manager.get_all_docker_images()  # Получаем все образы
            self.db_image_combo.clear()  # Очищаем список
            for image in docker_images:
                self.db_image_combo.addItem(image.name)  # Добавляем образы в список
            logger.info("Docker-образы успешно загружены в интерфейс.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить Docker-образы: {e!s}")
            logger.exception(f"Ошибка при загрузке Docker-образов: {e}")

    def add_custom_image(self) -> None:
        custom_image = self.custom_image_edit.text().strip()
        if not custom_image:
            QMessageBox.warning(self, "Ошибка", "Имя образа не может быть пустым.")
            return
        sqlite_manager.add_docker_image(name=custom_image)
        logger.info(f"Добавлен образ: {custom_image}")
        self.db_image_combo.addItem(custom_image)
        QMessageBox.information(self, "Успех", f"Образ '{custom_image}' добавлен.")

    def delete_custom_image(self) -> None:
        selected_image = self.db_image_combo.currentText()
        if not selected_image:
            QMessageBox.warning(self, "Ошибка", "Выберите образ для удаления.")
            return
        logger.info(f"Удален образ: {selected_image}")
        self.db_image_combo.removeItem(self.db_image_combo.currentIndex())
        QMessageBox.information(self, "Успех", f"Образ '{selected_image}' удален.")

    def update_preview(self) -> None:
        self.db_image = self.db_image_combo.currentText()
        self.operation = self.operation_combo.currentText()
        self.num_records = self.records_spinbox.value()
        self.data_types = self.data_types_edit.text()

        preview = (
            f"Образ СУБД: {self.db_image}\n"
            f"Тип операции: {self.operation}\n"
            f"Количество записей: {self.num_records}\n"
            f"Типы данных: {self.data_types}"
        )
        self.preview_text.setText(preview)

    def start_process(self) -> None:
        self.update_preview()
        QMessageBox.information(self, "Информация", "Тест успешно запущен!")
        try:
            self.db_image = self.db_image_combo.currentText()
            self.operation = self.operation_combo.currentText()
            self.num_records = self.records_spinbox.value()
            self.data_types = [dt.strip() for dt in self.data_types_edit.text().split(",") or []]

            if not self.data_types:
                msg = "Список типов данных пуст."
                raise ValueError(msg)

            logger.info(f"Запуск теста с образом: {self.db_image}, операция: {self.operation}")
            self.setup_docker_and_test()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка запуска теста: {e!s}")
            logger.exception(f"Ошибка запуска теста: {e}")

    def setup_docker_and_test(self) -> None:
        self.docker_manager.pull_image(self.db_image)
        container_name = f"{clear_container_name(self.db_image)}_test"
        self.docker_manager.run_container(self.db_image, container_name)
        self.generate_and_test()
        generate_csv("test_data.csv", self.num_records, self.data_types)
        db_manager = DatabaseManager(
            db_type="postgresql", username="user", password="password",
            host="localhost", port=5432, db_name="test_db",
        )
        self.load_test("test_data.csv", db_manager, "test_table")
        self.test_completed.emit()

    @measure_performance(sqlite_manager)
    def load_test(self, csv_file, db_manager, table) -> None:
        load_csv_to_db(csv_file, db_manager, table)

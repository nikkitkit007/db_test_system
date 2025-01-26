import sys

from PyQt5.QtWidgets import (
    QApplication, QLabel, QVBoxLayout, QWidget, QComboBox,
    QSpinBox, QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal
import logging

from src.utils import generate_csv, clear_container_name, load_csv_to_db, measure_performance
from src.manager.db_manager import DatabaseManager
from src.manager.docker_manager import DockerManager
from src.storage.test_result_storage import sqlite_manager

logger = logging.getLogger(__name__)


class ConfigApp(QWidget):
    test_completed = pyqtSignal()  # Сигнал для обновления результатов

    def __init__(self):
        super().__init__()
        self.initUI()
        self.docker_manager = DockerManager()
        self.reset_parameters()

    def initUI(self):
        self.setWindowTitle("Docker Configurator")
        layout = QVBoxLayout()
        font = QFont("Arial", 14)

        # Заголовок
        header = QLabel("Настройка тестирования СУБД")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(header)

        # Выбор Docker-образа
        self.db_image_label = QLabel("Выберите образ СУБД:")
        self.db_image_label.setFont(font)
        self.db_image_combo = QComboBox()
        self.db_image_combo.addItems(["postgres:latest", "mysql:latest", "sqlite:latest"])
        layout.addWidget(self.db_image_label)
        layout.addWidget(self.db_image_combo)

        # Тип операции
        self.operation_label = QLabel("Выберите тип операции:")
        self.operation_label.setFont(font)
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["INSERT", "SELECT", "JOIN"])
        layout.addWidget(self.operation_label)
        layout.addWidget(self.operation_combo)

        # Количество записей
        self.records_label = QLabel("Количество записей:")
        self.records_label.setFont(font)
        self.records_spinbox = QSpinBox()
        self.records_spinbox.setRange(1, 100000)
        layout.addWidget(self.records_label)
        layout.addWidget(self.records_spinbox)

        # Типы данных
        self.data_types_label = QLabel("Типы данных (через запятую):")
        self.data_types_label.setFont(font)
        self.data_types_edit = QLineEdit()
        self.data_types_edit.setPlaceholderText("Например: int, str, date")
        layout.addWidget(self.data_types_label)
        layout.addWidget(self.data_types_edit)

        # Кнопка запуска
        self.start_button = QPushButton("Запустить тест")
        self.start_button.clicked.connect(self.start_process)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def reset_parameters(self):
        self.db_image = ""
        self.operation = ""
        self.num_records = 0
        self.data_types = []

    def start_process(self):
        try:
            self.db_image = self.db_image_combo.currentText()
            self.operation = self.operation_combo.currentText()
            self.num_records = self.records_spinbox.value()
            self.data_types = [dt.strip() for dt in self.data_types_edit.text().split(",")]

            if not self.data_types:
                raise ValueError("Список типов данных пуст.")

            logger.info(f"Запуск теста с образом: {self.db_image}, операция: {self.operation}")
            self.setup_docker_and_test()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка запуска теста: {str(e)}")
            logger.error(f"Ошибка запуска теста: {e}")

    def setup_docker_and_test(self):
        self.docker_manager.pull_image(self.db_image)
        container_name = f"{clear_container_name(self.db_image)}_test"
        self.docker_manager.run_container(self.db_image, container_name)
        self.generate_and_test()

    def generate_and_test(self):
        generate_csv("test_data.csv", self.num_records, self.data_types)
        db_manager = DatabaseManager(
            db_type="postgresql", username="user", password="password",
            host="localhost", port=5432, db_name="test_db"
        )
        self.load_test("test_data.csv", db_manager, "test_table")
        self.test_completed.emit()

    @measure_performance(sqlite_manager)
    def load_test(self, csv_file, db_manager, table):
        load_csv_to_db(csv_file, db_manager, table)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ConfigApp()
    ex.show()
    sys.exit(app.exec_())

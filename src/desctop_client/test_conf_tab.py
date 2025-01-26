import logging

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

logger = logging.getLogger(__name__)


class ConfigApp(QWidget):
    test_completed = pyqtSignal()  # Сигнал для обновления результатов

    def __init__(self) -> None:
        super().__init__()
        self.initUI()
        self.reset_parameters()

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

    def add_custom_image(self) -> None:
        custom_image = self.custom_image_edit.text().strip()
        if not custom_image:
            QMessageBox.warning(self, "Ошибка", "Имя образа не может быть пустым.")
            return
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

    def start_process(self) -> None:
        self.update_preview()
        QMessageBox.information(self, "Информация", "Тест успешно запущен!")

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

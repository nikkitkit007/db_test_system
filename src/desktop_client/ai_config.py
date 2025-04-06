import json
import os

from PyQt6.QtWidgets import (
    QComboBox,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.config.config import settings

ai_config_icon_path = os.path.join(settings.ICONS_PATH, "docker_icon.svg")


class AiConfigPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.combo_provider = QComboBox()
        self.json_text_edit = QPlainTextEdit()
        self.btn_validate_json = QPushButton("Проверить JSON")
        self.btn_save_ai_config = QPushButton("Сохранить конфигурацию")
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Заголовок или инструкция (опционально)
        label_provider = QLabel("Выберите провайдера AI:")
        layout.addWidget(label_provider)

        # Выпадающий список для выбора провайдера
        self.combo_provider.addItems(["OpenAI", "ygpt"])  # Добавьте при необходимости
        layout.addWidget(self.combo_provider)

        # Заголовок для конфигурации (опционально)
        label_json = QLabel("Введите JSON-конфигурацию:")
        layout.addWidget(label_json)

        # Поле для ввода JSON
        self.json_text_edit.setPlaceholderText(
            '{\n    "api_key": "your-key-here",\n    "other_param": "value"\n}'
        )
        layout.addWidget(self.json_text_edit)

        # (Опциональная) Кнопка проверки JSON
        self.btn_validate_json.clicked.connect(self.validate_json)
        layout.addWidget(self.btn_validate_json)

        self.btn_save_ai_config.clicked.connect(self.save_ai_config)
        layout.addWidget(self.btn_save_ai_config)

        # Устанавливаем layout
        self.setLayout(layout)

    def validate_json(self) -> None:
        """Простая проверка на валидный JSON, показываем результат в QMessageBox."""
        text = self.json_text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Предупреждение", "Поле JSON пустое.")
            return
        try:
            json.loads(text)
            QMessageBox.information(self, "Проверка", "JSON синтаксически корректен.")
        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self, "Ошибка JSON", f"Не удалось разобрать JSON:\n{e!s}"
            )

    def save_ai_config(self):
        ...

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
from src.app.config.config import settings
from src.app.core.llm.predictor import possible_llm
from src.app.storage.db_manager.ai_config_storage import ai_config_db_manager
from src.app.storage.model import AiConfig

ai_config_icon_path = os.path.join(settings.ICONS_PATH, "ai_config_icon.svg")


class AiConfigPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.combo_provider = QComboBox()
        self.json_text_edit = QPlainTextEdit()
        self.btn_validate_json = QPushButton(self.tr("Проверить JSON"))
        self.btn_save_ai_config = QPushButton(self.tr("Сохранить конфигурацию"))
        self.label_provider = QLabel(self.tr("Выберите провайдера AI:"))
        self.label_json = QLabel(self.tr("Введите JSON-конфигурацию:"))

        self.init_ui()
        self.retranslateUi()
        self.load_ai_config()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(self.label_provider)

        self.combo_provider.addItems(possible_llm)
        layout.addWidget(self.combo_provider)

        self.combo_provider.currentIndexChanged.connect(self.load_ai_config)
        layout.addWidget(self.label_json)

        self.json_text_edit.setPlaceholderText(
            '{\n    "api_key": "your-key-here",\n    "other_param": "value"\n}',
        )
        layout.addWidget(self.json_text_edit)

        self.btn_save_ai_config.clicked.connect(self.save_ai_config)
        layout.addWidget(self.btn_save_ai_config)

        self.setLayout(layout)

    def save_ai_config(self) -> None:
        text = self.json_text_edit.toPlainText().strip()
        valid_json = self._validate_json(text)
        if valid_json is None:
            return

        ai_config = AiConfig(
            name=self.combo_provider.currentText(),
            config=text,
        )

        existing_config = ai_config_db_manager.get_ai_config(name=ai_config.name)
        if existing_config is None:
            ai_config_db_manager.add_ai_config(ai_config)
        else:
            existing_config.config = ai_config.config
            ai_config_db_manager.update_ai_config(existing_config)

    def retranslateUi(self) -> None:
        """
        Переустанавливает все текстовые элементы UI согласно текущему переводчику.
        """
        # Метки
        self.label_provider.setText(self.tr("Выберите провайдера AI:"))
        self.label_json.setText(self.tr("Введите JSON-конфигурацию:"))

        # Кнопки
        self.btn_validate_json.setText(self.tr("Проверить JSON"))
        self.btn_save_ai_config.setText(self.tr("Сохранить конфигурацию"))

    def load_ai_config(self) -> None:
        provider_name = self.combo_provider.currentText()
        ai_config = ai_config_db_manager.get_ai_config(name=provider_name)
        if ai_config is None:
            self.json_text_edit.setPlainText("")
            return
        try:
            text = json.dumps(
                json.loads(ai_config.config),
                indent=4,
                ensure_ascii=False,
            )
            self.json_text_edit.setPlainText(text)
        except TypeError as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось преобразовать конфиг в JSON:\n{e!s}",
            )
            return

    def _validate_json(self, text: str) -> None | str:
        if not text:
            QMessageBox.warning(self, "Предупреждение", "Поле JSON пустое.")
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self,
                "Ошибка JSON",
                f"Не удалось разобрать JSON:\n{e!s}",
            )
            return None

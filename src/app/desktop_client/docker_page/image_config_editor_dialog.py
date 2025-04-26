import json

from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class ConfigEditorDialog(QDialog):
    """
    Диалоговое окно для просмотра/редактирования конфигурации Docker-образа.
    """

    def __init__(self, parent=None, image_name="", config_dict=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Редактирование конфигурации: {image_name}")
        self.image_name = image_name
        self.original_config = config_dict if config_dict else {}
        self.edited_config = {}
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        # Поля для основных ключей
        self.db_type_edit = QLineEdit(self)
        self.driver = QLineEdit(self)
        self.user_edit = QLineEdit(self)
        self.password_edit = QLineEdit(self)
        self.port_edit = QLineEdit(self)
        self.db_edit = QLineEdit(self)
        self.env_edit = QTextEdit(self)  # env может быть крупным JSON

        # Заполняем начальными значениями (если есть)
        self.db_type_edit.setText(self.original_config.get("db_type", ""))
        self.driver.setText(self.original_config.get("driver", ""))
        self.user_edit.setText(self.original_config.get("user", ""))
        self.password_edit.setText(self.original_config.get("password", ""))
        self.port_edit.setText(str(self.original_config.get("port", "")))
        self.db_edit.setText(self.original_config.get("db", ""))

        # Преобразуем словарь env в JSON-строку, чтобы пользователь мог редактировать
        env_dict = self.original_config.get("env", {})
        env_json_str = json.dumps(env_dict, indent=2, ensure_ascii=False)
        self.env_edit.setPlainText(env_json_str)

        form_layout.addRow("db_type:", self.db_type_edit)
        form_layout.addRow("driver:", self.driver)
        form_layout.addRow("user:", self.user_edit)
        form_layout.addRow("password:", self.password_edit)
        form_layout.addRow("port:", self.port_edit)
        form_layout.addRow("db:", self.db_edit)
        form_layout.addRow(QLabel("env (JSON):"), self.env_edit)

        layout.addLayout(form_layout)

        # Кнопки "Сохранить" и "Отмена"
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить", self)
        cancel_btn = QPushButton("Отмена", self)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)

        save_btn.clicked.connect(self.save_and_close)
        cancel_btn.clicked.connect(self.reject)

        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.resize(400, 400)

    def save_and_close(self) -> None:
        """
        Читаем поля формы, собираем dict. Если всё ок — принимаем диалог,
        иначе выводим сообщение об ошибке.
        """
        db_type_val = self.db_type_edit.text().strip()
        driver = self.driver.text().strip()
        user_val = self.user_edit.text().strip()
        password_val = self.password_edit.text().strip()
        port_val_str = self.port_edit.text().strip()
        dbname_val = self.db_edit.text().strip()
        env_json_str = self.env_edit.toPlainText()

        # Проверяем и конвертируем порт
        try:
            port_val = int(port_val_str)
        except ValueError:
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Некорректное значение порта: {port_val_str}",
            )
            return

        try:
            env_dict = json.loads(env_json_str) if env_json_str else {}
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка в JSON env: {e}")
            return

        # Собираем словарь
        self.edited_config = {
            "db_type": db_type_val,
            "driver": driver,
            "user": user_val,
            "password": password_val,
            "port": port_val,
            "db": dbname_val,
            "env": env_dict,
        }

        self.accept()  # Закрываем диалог с результатом Accepted

    def get_config(self) -> dict:
        """Возвращает итоговый config, который собрали из полей."""
        return self.edited_config

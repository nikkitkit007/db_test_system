import os

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QIcon
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

from src.config.config import settings
from src.config.log import get_logger
from src.core.docker_test import run_test
from src.desctop_client.image_config_editor_dialog import ConfigEditorDialog
from src.schemas.test_init import DbTestConf, DbTestDataConf
from src.storage.config_storage import config_manager

logger = get_logger(__name__)

# DB_CONFIGS = {
#     # PostgreSQL официальные образы, например "postgres:latest"
#     "postgres": {
#         "db_type": "postgresql",
#         "default_user": "postgres",
#         "default_password": "password",
#         "default_port": 5432,
#         "default_db": "test_db",
#         # Зависит от того, как у вас в Dockerfile/образе обозначены переменные
#         "env": {
#             "POSTGRES_USER": "postgres",
#             "POSTGRES_PASSWORD": "password",
#             "POSTGRES_DB": "test_db",
#         },
#     },
#     # MySQL официальные образы, например "mysql:latest"
#     "mysql": {
#         "db_type": "mysql",
#         "default_user": "root",
#         "default_password": "password",
#         "default_port": 3306,
#         "default_db": "test_db",
#         "env": {
#             "MYSQL_ROOT_PASSWORD": "password",
#             "MYSQL_DATABASE": "test_db",
#         },
#     },
#     # Пример для MongoDB — если захотите добавить NoSQL
#     "mongo": {
#         "db_type": "mongodb",
#         "default_user": "root",
#         "default_password": "password",
#         "default_port": 27017,
#         "default_db": "admin",
#         "env": {
#             "MONGO_INITDB_ROOT_USERNAME": "root",
#             "MONGO_INITDB_ROOT_PASSWORD": "password",
#         },
#     },
#     # Можно завести "по умолчанию" или "user_defined" для прочих случаев
#     "default": {
#         "db_type": "postgresql",
#         "default_user": "user",
#         "default_password": "password",
#         "default_port": 5432,
#         "default_db": "test_db",
#         "env": {},
#     },
# }

test_config_icon = QIcon(os.path.join(settings.ICONS_PATH, "test_config_icon.svg"))


class DockerTestWorker(QObject):
    finished = pyqtSignal()
    # Можно добавить дополнительные сигналы для прогресса, ошибок и т.д.

    def __init__(
        self,
        db_image,
        num_records,
        data_types,
        operation,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.db_image = db_image
        self.num_records = num_records
        self.data_types = data_types
        self.operation = operation

    @pyqtSlot()
    def run(self) -> None:
        try:
            run_test(
                DbTestConf(
                    db_image=self.db_image,
                    operation=self.operation,
                    test_data_conf=DbTestDataConf(
                        data_types=self.data_types,
                        num_records=self.num_records,
                    ),
                ),
            )
        except Exception as e:
            logger.exception("Ошибка в DockerTestWorker: %s", e)
        finally:
            self.finished.emit()


class ConfigApp(QWidget):
    test_completed = pyqtSignal()  # Сигнал для обновления результатов

    def __init__(self) -> None:
        super().__init__()
        self.initUI()
        self.reset_parameters()
        self.load_docker_images()

    def initUI(self) -> None:
        self.setWindowTitle("Docker Configurator")
        layout = QVBoxLayout()
        QFont("Arial", 14)

        # ---------------- Группа: Образы Docker ----------------
        docker_group = QGroupBox("Образы Docker")
        docker_layout = QGridLayout()
        docker_group.setLayout(docker_layout)

        # Выбор Docker-образа
        self.db_image_label = QLabel("Выберите образ СУБД:")
        self.db_image_combo = QComboBox()
        docker_layout.addWidget(self.db_image_label, 0, 0)
        docker_layout.addWidget(self.db_image_combo, 0, 1)

        # Кнопки добавления / удаления / редактирования образа
        self.custom_image_label = QLabel("Добавить пользовательский образ:")
        self.custom_image_edit = QLineEdit()
        self.custom_image_edit.setPlaceholderText("Например: custom/image:tag")
        self.add_image_button = QPushButton("Добавить")
        self.add_image_button.clicked.connect(self.add_custom_image)

        self.delete_image_button = QPushButton("Удалить")
        self.delete_image_button.clicked.connect(self.delete_custom_image)

        # Новая кнопка «Редактировать конфигурацию»
        self.edit_config_button = QPushButton("Редактировать конфигурацию")
        self.edit_config_button.clicked.connect(self.edit_selected_image_config)

        docker_layout.addWidget(self.custom_image_label, 1, 0)
        docker_layout.addWidget(self.custom_image_edit, 1, 1)
        docker_layout.addWidget(self.add_image_button, 2, 0)
        docker_layout.addWidget(self.delete_image_button, 2, 1)
        docker_layout.addWidget(self.edit_config_button, 3, 0, 1, 2)

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
            docker_images = (
                config_manager.get_all_docker_images()
            )  # Получаем все образы
            self.db_image_combo.clear()  # Очищаем список
            for image in docker_images:
                self.db_image_combo.addItem(image.name)  # Добавляем образы в список
            logger.info("Docker-образы успешно загружены в интерфейс.")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось загрузить Docker-образы: {e!s}",
            )
            logger.exception(f"Ошибка при загрузке Docker-образов: {e}")

    def add_custom_image(self) -> None:
        custom_image = self.custom_image_edit.text().strip()
        if not custom_image:
            QMessageBox.warning(self, "Ошибка", "Имя образа не может быть пустым.")
            return
        config_manager.add_docker_image(name=custom_image)
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
            self.data_types = [
                dt.strip()
                for dt in self.data_types_edit.text().split(",")
                if dt.strip()
            ]

            if not self.data_types:
                msg = "Список типов данных пуст."
                raise ValueError(msg)

            logger.info(
                f"Запуск теста с образом: {self.db_image}, операция: {self.operation}",
            )

            self.run_test_in_thread()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка запуска теста: {e!s}")
            logger.exception(f"Ошибка запуска теста: {e}")

    def run_test_in_thread(self) -> None:
        self.thread = QThread()
        # Создаем экземпляр нового рабочего объекта
        self.worker = DockerTestWorker(
            db_image=self.db_image,
            num_records=self.num_records,
            data_types=self.data_types,
            operation=self.operation,
        )
        # Перемещаем объект в отдельный поток
        self.worker.moveToThread(self.thread)
        # При запуске потока вызываем run() нашего рабочего объекта
        self.thread.started.connect(self.worker.run)
        # Когда работа завершена, завершаем поток и очищаем объекты
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        # После завершения теста можно уведомить другие компоненты приложения
        self.worker.finished.connect(self.on_test_finished)
        self.thread.start()

    def on_test_finished(self) -> None:
        # Вызываем сигнал, на который подписаны, например, другие вкладки (TestResultsApp)
        self.test_completed.emit()

    def edit_selected_image_config(self) -> None:
        """
        Открывает диалоговое окно для редактирования конфигурации
        текущего выбранного Docker-образа.
        """
        selected_image = self.db_image_combo.currentText()
        if not selected_image:
            QMessageBox.warning(self, "Ошибка", "Не выбран образ для редактирования.")
            return

        # Пытаемся получить текущий config из БД
        try:
            config_dict = config_manager.get_db_config(selected_image)
        except ValueError:
            # Если конфигурации нет, вернём пустой словарь
            config_dict = {}

        # Создаём и отображаем диалог
        dialog = ConfigEditorDialog(
            self,
            image_name=selected_image,
            config_dict=config_dict,
        )
        if dialog.exec_():  # Если пользователь нажал "Сохранить"
            new_config = dialog.get_config_dict()
            # Сохраняем в БД
            config_manager.add_or_update_db_config(selected_image, new_config)
            QMessageBox.information(
                self,
                "Успех",
                f"Конфигурация для {selected_image} обновлена.",
            )

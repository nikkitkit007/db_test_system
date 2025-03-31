import json
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.config.config import settings
from src.desktop_client.image_config_editor_dialog import ConfigEditorDialog
from src.storage.config_storage import config_manager
from src.storage.model import DockerImage

docker_image_icon_path = os.path.join(settings.ICONS_PATH, "docker_icon.svg")


class DockerImagesPage(QWidget):
    """
    Страница с отображением всех Docker-образов и информацией о выбранном контейнере.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.docker_list: QListWidget = QListWidget()
        self.container_info = QTextEdit()
        self.custom_image_edit = QLineEdit()

        self.add_image_button = QPushButton("Добавить")
        self.delete_image_button = QPushButton("Удалить")
        self.edit_config_button = QPushButton("Редактировать")

        self.initUI()

    def initUI(self) -> None:
        main_layout = QHBoxLayout(self)  # Разделение списка и информации

        # 🔹 Левая часть – список Docker-образов
        self.docker_list.itemClicked.connect(
            self.display_container_info,
        )  # Обработчик клика
        self.load_docker_images()  # Заполняем список образами
        main_layout.addWidget(self.docker_list, 2)  # Занимает 2 части от 3

        # 🔹 Правая часть – Информация о выбранном контейнере
        right_panel = QVBoxLayout()

        # Группа информации
        details_group = QGroupBox("Информация о контейнере")
        details_layout = QVBoxLayout()

        self.container_info.setReadOnly(True)
        details_layout.addWidget(self.container_info)

        details_group.setLayout(details_layout)
        right_panel.addWidget(details_group)

        # 🔹 Панель управления образами (кнопки)
        manage_group = QGroupBox("Управление образами")
        manage_layout = QGridLayout()

        self.custom_image_edit.setPlaceholderText("custom/image:tag")

        manage_layout.addWidget(QLabel("Добавить новый образ:"), 0, 0)
        manage_layout.addWidget(self.custom_image_edit, 0, 1)
        manage_layout.addWidget(self.add_image_button, 1, 0)
        manage_layout.addWidget(self.delete_image_button, 1, 1)
        manage_layout.addWidget(self.edit_config_button, 2, 0, 1, 2)

        manage_group.setLayout(manage_layout)
        right_panel.addWidget(manage_group)

        main_layout.addLayout(right_panel, 3)  # Правая панель занимает 3 части от 5

        self.setLayout(main_layout)

        self.add_image_button.clicked.connect(self.add_docker_image)
        self.delete_image_button.clicked.connect(self.delete_docker_image)
        self.edit_config_button.clicked.connect(self.edit_docker_config)

    def load_docker_images(self) -> None:
        docker_images = config_manager.get_all_docker_images()
        self.docker_list.clear()
        for image in docker_images:
            self._add_image_to_list(image)

    def _add_image_to_list(self, image: DockerImage) -> None:
        item = QListWidgetItem(image.name)
        item.setData(Qt.ItemDataRole.UserRole, image.id)
        self.docker_list.addItem(item)

    def display_container_info(self, item) -> None:
        container_name = item.text()
        image_config = config_manager.get_db_config(container_name)
        info_text = json.dumps(
            image_config,
            indent=4,
            ensure_ascii=False,
            sort_keys=True,
        )

        self.container_info.setText(info_text)

    def add_docker_image(self) -> None:
        new_image = self.custom_image_edit.text().strip()
        if not new_image:
            QMessageBox.warning(self, "Ошибка", "Введите имя образа.")
            return
        image = config_manager.add_docker_image(DockerImage(name=new_image))
        self._add_image_to_list(image)
        QMessageBox.information(
            self,
            "Добавлено",
            f"Образ {new_image} успешно добавлен.",
        )

    def delete_docker_image(self) -> None:
        selected_item = self.docker_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Ошибка", "Выберите образ для удаления.")
            return
        config_manager.delete_docker_image(
            image_id=selected_item.data(Qt.ItemDataRole.UserRole),
        )
        self.docker_list.takeItem(self.docker_list.row(selected_item))
        QMessageBox.information(
            self,
            "Удалено",
            f"Образ {selected_item.text()} удален.",
        )

    def edit_docker_config(self) -> None:
        """
        Открывает диалоговое окно для редактирования конфигурации
        текущего выбранного Docker-образа.
        """
        selected_image_name = self.docker_list.currentItem().text()
        if not selected_image_name:
            QMessageBox.warning(self, "Ошибка", "Не выбран образ для редактирования.")
            return

        config_dict = config_manager.get_db_config(selected_image_name)

        # Создаём и отображаем диалог
        dialog = ConfigEditorDialog(
            self,
            image_name=selected_image_name,
            config_dict=config_dict,
        )
        if dialog.exec():  # Если пользователь нажал "Сохранить"
            new_config = dialog.get_config_dict()
            config_manager.add_or_update_db_config(selected_image_name, new_config)
            QMessageBox.information(
                self,
                "Успех",
                f"Конфигурация для {selected_image_name} обновлена.",
            )

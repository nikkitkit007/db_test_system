import json
import os
from typing import Literal

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from src.app.config.config import settings
from src.app.desktop_client.docker_page.image_config_editor_dialog import (
    ConfigEditorDialog,
)
from src.app.desktop_client.docker_page.scan_host_dialog import ScanHostDialog
from src.app.storage.db_manager.docker_storage import docker_db_manager
from src.app.storage.model import DockerImage

docker_image_icon_path = os.path.join(settings.ICONS_PATH, "docker_icon.svg")


class DockerImagesPage(QWidget):
    """
    Страница с отображением всех Docker‑образов и панелью конфигурации.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # Основные виджеты
        self.docker_table = QTableWidget()
        self.connection_info = QTextEdit()

        # Кнопки тулбара
        self.add_config_button = QPushButton("Добавить образ")
        self.scan_host_button = QPushButton("Сканировать хост")
        self.delete_config_button = QPushButton("Удалить конфиг(и)")

        self.initUI()
        self.load_docker_images()

    def initUI(self) -> None:
        main_layout = QVBoxLayout(self)

        # ─── Панель инструментов ───
        toolbar = QHBoxLayout()
        toolbar.addWidget(self.add_config_button)
        toolbar.addStretch(1)
        toolbar.addWidget(self.scan_host_button)
        toolbar.addWidget(self.delete_config_button)
        main_layout.addLayout(toolbar)

        # ─── Список образов ───
        containers_group = QGroupBox("Список контейнеров")
        containers_layout = QVBoxLayout()
        self.docker_table.setColumnCount(4)
        self.docker_table.setHorizontalHeaderLabels(
            ["Конфиг", "Образ", "Создан", "Обновлен"],
        )
        self.docker_table.horizontalHeader().setStretchLastSection(True)
        self.docker_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows,
        )
        self.docker_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.docker_table.itemSelectionChanged.connect(self.display_container_info)
        self.docker_table.itemDoubleClicked.connect(self.on_table_double_click)

        containers_layout.addWidget(self.docker_table)
        containers_group.setLayout(containers_layout)
        main_layout.addWidget(containers_group, 2)

        # ─── Информация / Конфигурация ───
        config_group = QGroupBox("Информация / Конфигурация")
        config_layout = QVBoxLayout()
        self.connection_info.setReadOnly(True)
        config_layout.addWidget(self.connection_info)
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group, 3)

        self.setLayout(main_layout)

        # ─── Сигналы ───
        self.add_config_button.clicked.connect(self.add_docker_image)
        self.scan_host_button.clicked.connect(self.open_scan_dialog)
        self.delete_config_button.clicked.connect(self.delete_selected_config)

    def load_docker_images(self) -> None:
        """Загружает все сохранённые Docker‑образы из БД."""
        try:
            images = docker_db_manager.get_all_docker_images()
            self.docker_table.setRowCount(0)
            for img in images:
                self._add_image_to_table(img, item_type="existing")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке образов: {e}")

    def _add_image_to_table(
        self,
        image: DockerImage | dict,
        item_type: Literal["existing", "scanned"] = "existing",
    ) -> None:
        """Добавляет в таблицу либо сохранённый образ, либо просканированный контейнер."""
        row = self.docker_table.rowCount()
        self.docker_table.insertRow(row)

        if isinstance(image, DockerImage):
            # сохранённый образ
            cfg_item = QTableWidgetItem(image.config_name)
            name_item = QTableWidgetItem(image.image_name)
            created_item = QTableWidgetItem(str(image.created_at))
            updated_item = QTableWidgetItem(str(image.updated_at))
            data = image.id
        else:
            # просканированный контейнер
            cfg_item = QTableWidgetItem("-")
            name_item = QTableWidgetItem(image["name"])
            created_item = QTableWidgetItem(image.get("created", ""))
            updated_item = QTableWidgetItem("-")
            data = image

        for col, item in enumerate([cfg_item, name_item, created_item, updated_item]):
            item.setData(Qt.ItemDataRole.UserRole, data)
            # визуальный маркер для сканированных
            if item_type == "scanned":
                item.setBackground(Qt.GlobalColor.lightGray)
            self.docker_table.setItem(row, col, item)

    def on_table_double_click(self, item: QTableWidgetItem) -> None:
        """При двойном клике открываем редактор конфига."""
        row = item.row()
        # Вытащим UserRole из первой колонки
        data = self.docker_table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        if isinstance(data, dict):
            # Просканированный контейнер: сначала сохраняем его как новый образ
            container = data
            image_name = container.get("image", "")
            # Запрос уникального имени конфига
            config_name, ok = QInputDialog.getText(
                self,
                "Имя конфигурации",
                "Введите уникальное имя конфига:",
                QLineEdit.EchoMode.Normal,
                f"{image_name.replace('/', '_')}_cfg",
            )
            if not ok or not config_name.strip():
                return

            # Запускаем редактор на пустом конфиге
            dialog = ConfigEditorDialog(self, image_name=image_name, config_dict={})
            if dialog.exec() == QDialog.DialogCode.Accepted:
                cfg = dialog.get_config()
                docker_image = DockerImage(
                    image_name=image_name,
                    config_name=config_name,
                    config=json.dumps(cfg),
                )
                docker_db_manager.add_docker_image(docker_image)
                self.load_docker_images()

        else:
            # Существующий образ — редактируем его конфиг
            config_name = self.docker_table.item(row, 0).text()
            try:
                docker_image = docker_db_manager.get_image(config_name=config_name)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", str(e))
                return

            raw = docker_image.config or {}
            cfg = json.loads(raw) if isinstance(raw, str) else raw

            dialog = ConfigEditorDialog(
                self,
                image_name=docker_image.image_name,
                config_dict=cfg,
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_cfg = dialog.get_config()
                docker_image.config = json.dumps(new_cfg)
                docker_db_manager.update_docker_image(docker_image)
                self.load_docker_images()

    def display_container_info(self) -> None:
        """Показывает детали выбранного образа или контейнера."""
        try:
            items = self.docker_table.selectedItems()
            if not items:
                self.connection_info.clear()
                return

            data = items[0].data(Qt.ItemDataRole.UserRole)
            if isinstance(data, dict):
                # просканированный контейнер
                info = {
                    "Имя": data.get("name", ""),
                    "ID": data.get("id", ""),
                    "Образ": data.get("image", ""),
                    "Команда": data.get("command", ""),
                    "Создан": data.get("created", ""),
                    "Порты": data.get("ports", ""),
                    "Состояние": data.get("state", ""),
                }
            else:
                # сохранённый образ
                img = docker_db_manager.get_image(config_name=items[0].text())
                raw = img.config or {}
                cfg = json.loads(raw) if isinstance(raw, str) else raw
                info = {
                    "db_type": cfg.get("db_type", ""),
                    "driver": cfg.get("driver", ""),
                    "user": cfg.get("user", ""),
                    "password": cfg.get("password", ""),
                    "port": cfg.get("port", ""),
                    "db": cfg.get("db", ""),
                    "env": cfg.get("env", {}),
                }

            self.connection_info.setText(
                json.dumps(info, indent=4, ensure_ascii=False, sort_keys=True),
            )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка отображения: {e}")

    def add_docker_image(self) -> None:
        """Добавляет новый образ: запрашиваем имя, открываем редактор конфига."""
        image_name, ok = QInputDialog.getText(
            self,
            "Новый образ",
            "Введите имя Docker‑образа (например nginx:latest):",
            QLineEdit.EchoMode.Normal,
        )
        if not ok or not image_name.strip():
            return

        # Генерим предложенное имя конфига
        config_name, ok2 = QInputDialog.getText(
            self,
            "Имя конфигурации",
            "Введите уникальное имя конфига:",
            QLineEdit.EchoMode.Normal,
            f"{image_name.replace('/', '_')}_cfg",
        )
        if not ok2 or not config_name.strip():
            return

        # Открываем редактор для заполнения полей
        dialog = ConfigEditorDialog(self, image_name=image_name, config_dict={})
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cfg = dialog.get_config()
            docker_image = DockerImage(
                image_name=image_name,
                config_name=config_name,
                config=json.dumps(cfg),
            )
            docker_db_manager.add_docker_image(docker_image)
            self.load_docker_images()

    def delete_selected_config(self) -> None:
        """Массовое удаление выбранных строк и конфига в БД для сохранённых."""
        selected = self.docker_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите строку(и) для удаления.")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить выбранные записи?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # делаем в обратном порядке, чтобы индексы не съехали
        for idx in sorted(selected, key=lambda mi: mi.row(), reverse=True):
            row = idx.row()
            item = self.docker_table.item(row, 0)
            data = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(data, int):
                try:
                    docker_db_manager.delete_docker_image(data)
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Ошибка",
                        f"Не удалось удалить из БД: {e}",
                    )
                    continue
            self.docker_table.removeRow(row)

    def open_scan_dialog(self) -> None:
        """Открывает диалог сканирования и добавляет выбранные контейнеры."""
        dialog = ScanHostDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.selected_containers()
            if not selected:
                QMessageBox.information(
                    self,
                    "Нечего добавлять",
                    "Отметьте контейнеры.",
                )
                return
            for c in selected:
                self._add_image_to_table(c, item_type="scanned")
            QMessageBox.information(
                self,
                "Готово",
                f"Добавлено {len(selected)} контейнеров.",
            )

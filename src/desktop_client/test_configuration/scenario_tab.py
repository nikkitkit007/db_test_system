import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.config.config import settings
from src.desktop_client.test_configuration.scenario_builder import ScenarioBuilderWidget
from src.storage.db_manager.scenario_storage import scenario_db_manager
from src.storage.model import Scenario

scenario_icon_path = os.path.join(settings.ICONS_PATH, "scenario.svg")


class ScenarioPage(QWidget):

    def __init__(self, stacked_widget: QStackedWidget = None, parent=None) -> None:
        super().__init__(parent)
        self.stacked_widget = stacked_widget
        self.new_scenario_button = QPushButton("Новый сценарий")
        self.scenario_list = QListWidget()
        self.scenario_name_edit = QLineEdit()
        self.scenario_builder_page = ScenarioBuilderPage(self.stacked_widget)

        self.save_button = QPushButton("Сохранить")
        self.delete_button = QPushButton("Удалить")

        self.initUI()
        self.load_scenarios()

    def initUI(self) -> None:
        # Основной горизонтальный layout с QSplitter для динамического изменения размера
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Левая часть: список сценариев
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(self.new_scenario_button)
        left_layout.addWidget(self.scenario_list)
        self.new_scenario_button.clicked.connect(self.create_new_scenario)
        self.scenario_list.itemClicked.connect(self.load_scenario_into_builder)
        splitter.addWidget(left_widget)
        splitter.setStretchFactor(0, 1)

        # Правая часть: вертикальный layout с полем ввода, конструктором и кнопкой
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Поле ввода имени сценария (верхняя часть правой панели)
        self.scenario_name_edit.setPlaceholderText("Введите имя сценария...")
        right_layout.addWidget(self.scenario_name_edit)

        # Оборачиваем ScenarioBuilderPage в QScrollArea,
        # чтобы он масштабировался и прокручивался при необходимости
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.scenario_builder_page)
        right_layout.addWidget(scroll_area, 1)  # растяжимый блок

        # Кнопка «Сохранить» (нижняя часть)
        right_layout.addWidget(self.save_button)
        right_layout.addWidget(self.delete_button)

        self.save_button.clicked.connect(self.save_scenario)
        self.delete_button.clicked.connect(self.delete_scenario)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 2)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def load_scenarios(self) -> None:
        """Загружает список сценариев из базы данных."""
        scenarios = scenario_db_manager.get_all_scenarios()
        self.scenario_list.clear()
        for scenario in scenarios:
            self._add_scenario_to_list(scenario)

    def create_new_scenario(self) -> None:
        """
        Очищает правую панель для создания нового сценария.
        """
        self.scenario_list.clearSelection()
        self.scenario_name_edit.clear()
        self.scenario_builder_page.scenario_builder.clear()
        self.scenario_name_edit.setFocus()

    def _add_scenario_to_list(self, scenario: Scenario) -> None:
        item = QListWidgetItem(scenario.name)
        item.setData(Qt.ItemDataRole.UserRole, scenario.id)
        self.scenario_list.addItem(item)

    def load_scenario_into_builder(self, item: QListWidgetItem) -> None:
        scenario_id = item.data(Qt.ItemDataRole.UserRole)
        scenario = scenario_db_manager.get_scenario(scenario_id)
        if scenario:
            self.scenario_name_edit.setText(scenario.name)
            self.scenario_builder_page.scenario_builder.set_scenario(
                scenario.get_steps(),
            )
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить сценарий.")

    def save_scenario(self) -> None:
        scenario_name = self.scenario_name_edit.text().strip()
        if not scenario_name:
            QMessageBox.warning(self, "Ошибка", "Введите имя сценария.")
            return

        steps = self.scenario_builder_page.scenario_builder.get_scenario_steps()

        scenario = scenario_db_manager.get_scenario(name=scenario_name)
        if scenario:
            # Обновляем сценарий
            scenario.set_steps(steps)
            scenario_db_manager.update_scenario(scenario)
            QMessageBox.information(
                self,
                "Успех",
                f"Сценарий '{scenario_name}' обновлен.",
            )
        else:
            # Создаем новый сценарий
            scenario = Scenario(name=scenario_name)
            scenario.set_steps(steps)
            scenario_db_manager.add_scenario(scenario)
            QMessageBox.information(
                self,
                "Успех",
                f"Сценарий '{scenario_name}' создан.",
            )
            self._add_scenario_to_list(scenario)

    def delete_scenario(self) -> None:
        scenario = self.scenario_list.currentItem()
        if not scenario:
            QMessageBox.warning(self, "Ошибка", "Выберете сценарий для удаления.")
            return

        scenario_db_manager.delete_scenario(
            scenario_id=scenario.data(Qt.ItemDataRole.UserRole),
        )
        self.scenario_list.takeItem(self.scenario_list.row(scenario))
        self.scenario_name_edit.clear()
        self.scenario_builder_page.scenario_builder.clear()

        QMessageBox.information(
            self,
            "Удалено",
            f"Сценарий {scenario.text()} удален.",
        )


class ScenarioBuilderPage(QWidget):
    steps_updated = pyqtSignal(list)

    def __init__(self, stacked_widget: QStackedWidget) -> None:
        super().__init__()
        self.stacked_widget = stacked_widget
        self.scenario_builder = ScenarioBuilderWidget(self)

        self.initUI()

    def initUI(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self.scenario_builder)

        self.setLayout(layout)

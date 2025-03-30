import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget, QScrollArea, QSplitter,
)

from src.config.config import settings
from src.desktop_client.test_conf_tab import ScenarioBuilderPage
from src.storage.config_storage import config_manager
from src.storage.model import Scenario

scenario_icon_path = os.path.join(settings.ICONS_PATH, "scenario.svg")


class ScenarioPage(QWidget):

    def __init__(self, stacked_widget: QStackedWidget = None, parent=None) -> None:
        super().__init__(parent)
        self.stacked_widget = stacked_widget
        self.scenario_list = QListWidget()
        self.scenario_name_edit = QLineEdit()
        self.scenario_builder_page = ScenarioBuilderPage(self.stacked_widget)
        self.save_button = QPushButton("Сохранить")

        self.initUI()
        self.load_scenarios()

    def initUI(self) -> None:
        # Основной горизонтальный layout с QSplitter для динамического изменения размера
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Левая часть: список сценариев
        self.scenario_list.itemClicked.connect(self.load_scenario_into_builder)
        splitter.addWidget(self.scenario_list)
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
        self.save_button.clicked.connect(self.save_scenario)
        right_layout.addWidget(self.save_button)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 2)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def load_scenarios(self) -> None:
        """Загружает список сценариев из базы данных."""
        scenarios = config_manager.get_all_scenarios()
        self.scenario_list.clear()
        for scenario in scenarios:
            self._add_scenario_to_list(scenario)

    def _add_scenario_to_list(self, scenario: Scenario) -> None:
        item = QListWidgetItem(scenario.name)
        item.setData(Qt.ItemDataRole.UserRole, scenario.id)
        self.scenario_list.addItem(item)

    def load_scenario_into_builder(self, item: QListWidgetItem) -> None:
        scenario_id = item.data(Qt.ItemDataRole.UserRole)
        scenario = config_manager.get_scenario(scenario_id)
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

        scenario = config_manager.get_scenario(name=scenario_name)
        if scenario:
            # Обновляем сценарий
            scenario.set_steps(steps)
            config_manager.update_scenario(scenario)
            QMessageBox.information(
                self,
                "Успех",
                f"Сценарий '{scenario_name}' обновлен.",
            )
        else:
            # Создаем новый сценарий
            scenario = Scenario(name=scenario_name)
            scenario.set_steps(steps)
            config_manager.add_scenario(scenario)
            QMessageBox.information(
                self,
                "Успех",
                f"Сценарий '{scenario_name}' создан.",
            )
            self._add_scenario_to_list(scenario)

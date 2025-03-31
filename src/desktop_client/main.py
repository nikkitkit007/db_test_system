from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.config.app_styles import style_sheet
from src.desktop_client.config import PageIndex
from src.desktop_client.docker_config import DockerImagesPage, docker_image_icon_path
from src.desktop_client.results.test_result_tab import TestResultsApp, results_icon_path
from src.desktop_client.test_conf_tab import (
    ConfigApp,
    ScenarioBuilderPage,
    test_config_icon_path,
)
from src.desktop_client.test_configuration.scenario_tab import (
    ScenarioPage,
    scenario_icon_path,
)


class MainApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Database Test System")
        self.resize(900, 700)

        # Настройка центрального виджета и основного лейаута
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Параметры боковой панели
        self.expanded_width = 200
        self.collapsed_width = 50
        self.sidebar_expanded = True

        # Создаём боковую панель (sidebar)
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setMinimumWidth(self.expanded_width)
        self.sidebar.setMaximumWidth(self.expanded_width)

        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_layout.setSpacing(0)

        # Навигационное дерево
        self.nav_tree = QTreeWidget()
        self.nav_tree.setHeaderHidden(True)

        # Пункт «Конфигурации» (топ‐уровень)
        self.config_item = QTreeWidgetItem(self.nav_tree, ["Тестирование"])
        self.config_item.setIcon(0, QIcon(test_config_icon_path))

        # Пункт «Сценарии» (топ‐уровень)
        self.scenario_item = QTreeWidgetItem(self.nav_tree, ["Сценарии"])
        self.scenario_item.setIcon(0, QIcon(scenario_icon_path))

        # Пункт «Результаты» (топ‐уровень)
        self.results_item = QTreeWidgetItem(self.nav_tree, ["Результаты"])
        self.results_item.setIcon(0, QIcon(results_icon_path))

        # Пункт «Система» (топ‐уровень)
        self.system_item = QTreeWidgetItem(self.nav_tree, ["Система"])
        self.system_item.setIcon(0, QIcon(test_config_icon_path))
        self.system_item.setExpanded(True)

        # Дочерний пункт: «Образы Docker»
        self.docker_item = QTreeWidgetItem(self.system_item, ["Образы Docker"])
        self.docker_item.setIcon(0, QIcon(docker_image_icon_path))

        # Обработка кликов по элементам
        self.nav_tree.itemClicked.connect(self.on_tree_item_clicked)

        # Добавляем дерево в лейаут боковой панели
        self.sidebar_layout.addWidget(self.nav_tree)

        # Spacer + кнопка сворачивания
        spacer = QSpacerItem(
            20,
            20,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )
        self.sidebar_layout.addSpacerItem(spacer)

        self.btn_toggle = QToolButton()
        self.btn_toggle.setText("Collapse")
        self.btn_toggle.clicked.connect(self.toggle_sidebar)
        self.sidebar_layout.addWidget(self.btn_toggle)

        # Основной QStackedWidget (справа)
        self.stacked_widget = QStackedWidget()
        self.config_app = ConfigApp(self.stacked_widget)
        self.scenario_builder_page = ScenarioBuilderPage(self.stacked_widget)
        self.test_results_app = TestResultsApp()
        self.docker_page = DockerImagesPage()
        self.scenario_page = ScenarioPage()

        # # Добавляем страницы в QStackedWidget
        self.stacked_widget.addWidget(self.config_app)
        self.stacked_widget.addWidget(self.scenario_builder_page)
        self.stacked_widget.addWidget(self.test_results_app)
        self.stacked_widget.addWidget(self.docker_page)
        self.stacked_widget.addWidget(self.scenario_page)

        # Собираем всё в общий лейаут
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stacked_widget)
        self.setCentralWidget(main_widget)

        self.apply_styles()

    def on_tree_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Переключаем QStackedWidget в зависимости от выбранного пункта.
        """
        if item == self.docker_item:
            # «Образы Docker» (index 3)
            self.stacked_widget.setCurrentIndex(PageIndex.docker_page)
        elif item == self.config_item:
            # «Конфигурации» (index 0)
            self.stacked_widget.setCurrentIndex(PageIndex.config_app)
        elif item == self.results_item:
            # «Результаты» (index 2)
            self.stacked_widget.setCurrentIndex(PageIndex.test_results_app)
        elif item == self.scenario_item:
            # «Сценарии» (index 4)
            self.stacked_widget.setCurrentIndex(PageIndex.scenario_page)
        elif item == self.system_item:
            pass  # По клику на «Система» ничего не делаем
        else:
            pass

    def toggle_sidebar(self) -> None:
        """
        Сворачивает/разворачивает боковую панель. При сворачивании оставляются
        только значки верхнего уровня, текст скрывается, дочерние пункты прячутся.
        """
        if self.sidebar_expanded:
            # Сворачиваем
            self.sidebar_expanded = False
            self.sidebar.setMinimumWidth(self.collapsed_width)
            self.sidebar.setMaximumWidth(self.collapsed_width)
            self.btn_toggle.setText("Expand")
            self._update_nav_tree_collapsed(collapsed=True)
            self.nav_tree.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
            )
        else:
            # Разворачиваем
            self.sidebar_expanded = True
            self.sidebar.setMinimumWidth(self.expanded_width)
            self.sidebar.setMaximumWidth(self.expanded_width)
            self.btn_toggle.setText("Свернуть")
            self._update_nav_tree_collapsed(collapsed=False)
            self.nav_tree.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded,
            )

    def _update_nav_tree_collapsed(self, collapsed: bool) -> None:
        """
        При collapsed=True скрывает текст и дочерние пункты верхнеуровневых элементов.
        При collapsed=False восстанавливает текст и показывает дочерние пункты.
        """
        for i in range(self.nav_tree.topLevelItemCount()):
            item = self.nav_tree.topLevelItem(i)
            if collapsed:
                # Сохраняем оригинальный текст, если ещё не сохранён
                if item.data(0, Qt.ItemDataRole.UserRole) is None:
                    item.setData(0, Qt.ItemDataRole.UserRole, item.text(0))
                item.setText(0, "")
                # Скрываем дочерние элементы
                for j in range(item.childCount()):
                    item.child(j).setHidden(True)
            else:
                # Восстанавливаем оригинальный текст
                original = item.data(0, Qt.ItemDataRole.UserRole)
                if original is not None:
                    item.setText(0, original)
                # Показываем дочерние элементы
                for j in range(item.childCount()):
                    item.child(j).setHidden(False)

    def apply_styles(self) -> None:
        self.setStyleSheet(style_sheet)

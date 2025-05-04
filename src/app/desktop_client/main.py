import os

from PyQt6.QtCore import QCoreApplication, Qt, QTranslator
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QButtonGroup,
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
from src.app.config.app_styles import lang_button_style, style_sheet
from src.app.config.config import settings
from src.app.desktop_client.ai_config_page.ai_config import (
    AiConfigPage,
    ai_config_icon_path,
)
from src.app.desktop_client.config import PageIndex
from src.app.desktop_client.docker_page.docker_config import (
    DockerImagesPage,
    docker_image_icon_path,
)
from src.app.desktop_client.results.test_result_tab import (
    TestResultsApp,
    results_icon_path,
)
from src.app.desktop_client.test_conf_tab import (
    ConfigApp,
    test_config_icon_path,
)
from src.app.desktop_client.test_configuration.scenario_tab import (
    ScenarioBuilderPage,
    ScenarioPage,
    scenario_icon_path,
)

app_config_icon_path = os.path.join(settings.ICONS_PATH, "app_config_icon.svg")
app_icon_path = os.path.join(settings.ICONS_PATH, "app_main_icon.svg")


class MainApp(QMainWindow):
    def __init__(self, translators: tuple, current_translator: QTranslator) -> None:
        super().__init__()
        self.translators = translators
        self.current_translator = current_translator

        self.setWindowTitle("Database Test System")
        self.setWindowIcon(QIcon(app_icon_path))

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
        self.config_item = QTreeWidgetItem(self.nav_tree, [self.tr("Тестирование")])
        self.config_item.setIcon(0, QIcon(test_config_icon_path))

        # Пункт «Сценарии» (топ‐уровень)
        self.scenario_item = QTreeWidgetItem(self.nav_tree, [self.tr("Сценарии")])
        self.scenario_item.setIcon(0, QIcon(scenario_icon_path))

        # Пункт «Результаты» (топ‐уровень)
        self.results_item = QTreeWidgetItem(self.nav_tree, [self.tr("Результаты")])
        self.results_item.setIcon(0, QIcon(results_icon_path))

        # Пункт «Система» (топ‐уровень)
        self.system_item = QTreeWidgetItem(self.nav_tree, [self.tr("Система")])
        self.system_item.setIcon(0, QIcon(app_config_icon_path))
        self.system_item.setExpanded(True)

        # Дочерний пункт: «Образы Docker»
        self.docker_item = QTreeWidgetItem(self.system_item, [self.tr("Образы Docker")])
        self.docker_item.setIcon(0, QIcon(docker_image_icon_path))
        # Дочерний пункт: «AI»
        self.ai_item = QTreeWidgetItem(self.system_item, [self.tr("AI подключение")])
        self.ai_item.setIcon(0, QIcon(ai_config_icon_path))

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

        # Виджет для кнопок RU/EN
        lang_widget = QWidget()
        self.lang_widget = lang_widget
        lang_layout = QHBoxLayout(lang_widget)
        lang_layout.setContentsMargins(5, 5, 5, 5)
        lang_layout.setSpacing(5)

        # Кнопки
        self.btn_ru = QToolButton()
        self.btn_ru.setText("RU")
        self.btn_ru.setCheckable(True)
        self.btn_ru.setChecked(True)  # по умолчанию RU

        self.btn_en = QToolButton()
        self.btn_en.setText("EN")
        self.btn_en.setCheckable(True)

        self.btn_ru.setCheckable(True)
        self.btn_ru.setAutoRaise(False)
        self.btn_en.setCheckable(True)
        self.btn_en.setAutoRaise(False)

        # Группа, чтобы только одна кнопка могла быть нажата
        self.lang_group = QButtonGroup(self)
        self.lang_group.setExclusive(True)
        self.lang_group.addButton(self.btn_ru)
        self.lang_group.addButton(self.btn_en)
        self.btn_ru.setChecked(True)

        self.btn_ru.setStyleSheet(lang_button_style)
        self.btn_en.setStyleSheet(lang_button_style)
        # Добавляем в layout
        lang_layout.addWidget(self.btn_ru)
        lang_layout.addWidget(self.btn_en)
        self.sidebar_layout.addWidget(lang_widget)

        # --- Затем кнопка сворачивания ---
        self.btn_toggle = QToolButton()
        self.btn_toggle.setText(self.tr("Свернуть"))
        self.btn_toggle.clicked.connect(self.toggle_sidebar)
        self.sidebar_layout.addWidget(self.btn_toggle)

        # Основной QStackedWidget (справа)
        self.stacked_widget = QStackedWidget()
        self.config_app = ConfigApp(self.stacked_widget)
        self.scenario_builder_page = ScenarioBuilderPage(self.stacked_widget)
        self.test_results_app = TestResultsApp()
        self.docker_page = DockerImagesPage()
        self.ai_page = AiConfigPage()
        self.scenario_page = ScenarioPage()

        # # Добавляем страницы в QStackedWidget
        for item in (
            self.config_app,
            self.scenario_builder_page,
            self.test_results_app,
            self.docker_page,
            self.scenario_page,
            self.ai_page,
        ):
            self.stacked_widget.addWidget(item)

        # Собираем всё в общий лейаут
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stacked_widget)
        self.setCentralWidget(main_widget)

        self.apply_styles()
        self.btn_ru.clicked.connect(lambda: self.on_language_changed("ru"))
        self.btn_en.clicked.connect(lambda: self.on_language_changed("en"))

    def on_tree_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Переключаем QStackedWidget в зависимости от выбранного пункта.
        """
        if item == self.docker_item:
            self.stacked_widget.setCurrentIndex(PageIndex.docker_page)
        elif item == self.config_item:
            self.stacked_widget.setCurrentIndex(PageIndex.config_app)
        elif item == self.results_item:
            self.stacked_widget.setCurrentIndex(PageIndex.test_results_app)
        elif item == self.scenario_item:
            self.stacked_widget.setCurrentIndex(PageIndex.scenario_page)
        elif item == self.system_item:
            pass
        elif item == self.ai_item:
            self.stacked_widget.setCurrentIndex(PageIndex.ai_config_page)
        else:
            pass

    def on_language_changed(self, lang_code: str) -> None:
        QCoreApplication.instance().removeTranslator(self.current_translator)

        # 2) ставим новый
        new_tr = self.translators[0] if lang_code == "ru" else self.translators[1]
        QCoreApplication.instance().installTranslator(new_tr)
        self.current_translator = new_tr

        # 3) обновляем все надписи в UI
        self.retranslateUi()
        # и для каждой страницы в stacked_widget, если у них есть retranslateUi():
        for page in (
            self.config_app,
            self.scenario_builder_page,
            self.test_results_app,
            self.docker_page,
            self.scenario_page,
            self.ai_page,
        ):
            if hasattr(page, "retranslateUi"):
                page.retranslateUi()

    def retranslateUi(self) -> None:
        # кнопки
        self.btn_toggle.setText(self.tr("Свернуть"))
        self.btn_ru.setText(self.tr("RU"))
        self.btn_en.setText(self.tr("EN"))

        # и теперь пункты меню
        self.config_item.setText(0, self.tr("Тестирование"))
        self.scenario_item.setText(0, self.tr("Сценарии"))
        self.results_item.setText(0, self.tr("Результаты"))
        self.system_item.setText(0, self.tr("Система"))
        self.docker_item.setText(0, self.tr("Образы Docker"))
        self.ai_item.setText(0, self.tr("AI подключение"))

    def toggle_sidebar(self) -> None:
        if self.sidebar_expanded:
            self.sidebar_expanded = False
            self.sidebar.setMinimumWidth(self.collapsed_width)
            self.sidebar.setMaximumWidth(self.collapsed_width)
            self.btn_toggle.setText("<->")
            self._update_nav_tree_collapsed(collapsed=True)
            self.nav_tree.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
            )
            self.lang_widget.hide()
        else:
            self.sidebar_expanded = True
            self.sidebar.setMinimumWidth(self.expanded_width)
            self.sidebar.setMaximumWidth(self.expanded_width)
            self.btn_toggle.setText(self.tr("Свернуть"))
            self._update_nav_tree_collapsed(collapsed=False)
            self.nav_tree.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded,
            )
            self.lang_widget.show()

    def _update_nav_tree_collapsed(self, collapsed: bool) -> None:
        for i in range(self.nav_tree.topLevelItemCount()):
            item = self.nav_tree.topLevelItem(i)
            if collapsed:
                if item.data(0, Qt.ItemDataRole.UserRole) is None:
                    item.setData(0, Qt.ItemDataRole.UserRole, item.text(0))
                item.setText(0, "")
                for j in range(item.childCount()):
                    item.child(j).setHidden(True)
            else:
                original = item.data(0, Qt.ItemDataRole.UserRole)
                if original is not None:
                    item.setText(0, original)
                for j in range(item.childCount()):
                    item.child(j).setHidden(False)

    def apply_styles(self) -> None:
        self.setStyleSheet(style_sheet)

import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from config.config import settings
from desctop_client.test_conf_tab import ConfigApp
from desctop_client.test_result_tab import TestResultsApp


class MainApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Database Test System")
        self.resize(900, 700)

        self.initUI()
        self.apply_styles()  # Применение стилей

    def initUI(self) -> None:
        # Центральный виджет и макет
        central_widget = QWidget()
        layout = QVBoxLayout()

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(True)  # Возможность перетаскивать вкладки

        # Добавляем вкладки
        self.test_config_app = ConfigApp()
        self.test_results_app = TestResultsApp()

        test_config_icon = QIcon(os.path.join(settings.ICONS_PATH, "test_config_icon.webp"))
        results_icon = QIcon(os.path.join(settings.ICONS_PATH, "results_icon.svg"))

        self.tabs.addTab(self.test_config_app, test_config_icon, "Test Configurator")
        self.tabs.addTab(self.test_results_app, results_icon, "Test Results")

        # Добавляем вкладки в макет
        layout.addWidget(self.tabs)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Подключение сигнала test_completed к методу load_results
        self.test_config_app.test_completed.connect(self.test_results_app.load_results)

    def apply_styles(self) -> None:
        """Применение стилей через Qt Style Sheets"""
        style_sheet = """
            QMainWindow {
                background-color: #f9f9f9;
            }

            QTabWidget::pane {
                border: 1px solid #aaa;
                background-color: #ffffff;
            }

            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #ccc;
                padding: 10px;
                min-width: 150px;
                font-family: Arial;
                font-size: 14px;
            }

            QTabBar::tab:selected {
                background: #c0d0ff;
                font-weight: bold;
                border-bottom: 2px solid #5a7dff;
            }

            QTabBar::tab:hover {
                background: #d0e0ff;
            }

            QWidget {
                font-family: Arial;
                font-size: 14px;
                color: #333333;
            }

            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #000000;
            }

            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }

            QPushButton:hover {
                background-color: #45a049;
            }

            QLineEdit, QSpinBox, QComboBox {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 5px;
                background-color: #ffffff;
            }

            QTableWidget {
                gridline-color: #cccccc;
                border: 1px solid #ccc;
                background-color: #f9f9f9;
            }

            QTableWidget QHeaderView::section {
                background-color: #e0e0e0;
                border: 1px solid #ccc;
                padding: 5px;
                font-weight: bold;
            }

            QListWidget {
                border: 1px solid #ccc;
                background-color: #ffffff;
            }
        """
        self.setStyleSheet(style_sheet)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec_())

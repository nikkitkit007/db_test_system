from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from desctop_client.test_conf_tab import ConfigApp, test_config_icon
from desctop_client.test_result_tab import TestResultsApp, results_icon
from src.config.app_styles import style_sheet


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

        self.tabs.addTab(self.test_config_app, test_config_icon, "Test Configurator")
        self.tabs.addTab(self.test_results_app, results_icon, "Test Results")

        # Добавляем вкладки в макет
        layout.addWidget(self.tabs)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Подключение сигнала test_completed к методу load_results
        self.test_config_app.test_completed.connect(self.test_results_app.load_results)

    def apply_styles(self) -> None:
        self.setStyleSheet(style_sheet)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec_())

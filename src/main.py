from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from desctop_client.test_conf_tab import ConfigApp
from desctop_client.test_result_tab import TestResultsApp


class MainApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Database Test System")
        self.setGeometry(100, 100, 800, 600)

        self.initUI()
        self.apply_styles()  # Применение стилей

    def initUI(self) -> None:
        central_widget = QWidget()
        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.test_config_app = ConfigApp()
        self.test_results_app = TestResultsApp()

        self.tabs.addTab(self.test_config_app, "Docker Configurator")
        self.tabs.addTab(self.test_results_app, "Test Results")

        layout.addWidget(self.tabs)
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)

        # Подключение сигнала test_completed к методу load_results
        self.test_config_app.test_completed.connect(self.test_results_app.load_results)

    def apply_styles(self):
        """Применение стилей через Qt Style Sheets"""
        style_sheet = """
            QMainWindow {
                background-color: #f0f0f0;
            }

            QTabWidget::pane {
                border: 1px solid #ccc;
                background-color: #ffffff;
            }

            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #ccc;
                padding: 10px;
                min-width: 120px;
                font-family: Arial;
                font-size: 14px;
            }

            QTabBar::tab:selected {
                background: #d0d0ff;
                font-weight: bold;
            }

            QTabBar::tab:hover {
                background: #c0c0f0;
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

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget

from desctop_client.test_conf_tab import ConfigApp
from desctop_client.test_result_tab import TestResultsApp


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Database Test System')
        self.setGeometry(100, 100, 800, 600)

        self.initUI()

    def initUI(self):
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


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec_())

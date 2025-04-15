import sys

from PyQt6.QtWidgets import (
    QApplication,
)

from src.desktop_client.main import MainApp


def start_app():
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    start_app()

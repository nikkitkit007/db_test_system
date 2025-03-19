import sys

from PyQt6.QtWidgets import (
    QApplication,
)

from src.desktop_client.main import MainApp

if __name__ == "__main__":

    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec())

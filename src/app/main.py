import sys

from PyQt6.QtCore import QTranslator
from PyQt6.QtWidgets import (
    QApplication,
)
from src.app.desktop_client.main import MainApp


def start_app() -> None:
    app = QApplication(sys.argv)

    tr_ru = QTranslator(app)
    tr_ru.load("translations/app_ru.qm")
    tr_en = QTranslator(app)
    tr_en.load("translations/app_en.qm")

    app.installTranslator(tr_ru)

    main_app = MainApp(translators=(tr_ru, tr_en), current_translator=tr_ru)
    main_app.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    start_app()

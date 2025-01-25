import sys

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QSpinBox, QLineEdit, QPushButton, QApplication

from src.config.config import settings
from src.config.log import get_logger
from src.manager.db_manager import DatabaseManager
from src.manager.docker_manager import DockerManager
from src.storage.test_result_storage import sqlite_manager
from src.utils import load_csv_to_db, generate_csv, measure_performance

logger = get_logger(__name__)


class ConfigApp(QWidget):

    test_completed = pyqtSignal()  # Добавляем сигнал

    def __init__(self, ):
        super().__init__()
        self.initUI()
        self.docker_manager = DockerManager()

        self.db_image = ''
        self.operation = ''
        self.num_records = ''
        self.data_types = []

    def initUI(self):
        self.setWindowTitle('Docker Configurator')

        layout = QVBoxLayout()

        # Font settings
        font = QFont('Arial', 14)

        # Dropdown for selecting DB image
        self.db_image_label = QLabel('Select Database Image:')
        self.db_image_label.setFont(font)
        self.db_image_combo = QComboBox()
        self.db_image_combo.setFont(font)
        self.db_image_combo.addItems(['postgres:latest', 'mysql:latest', 'sqlite:latest'])

        layout.addWidget(self.db_image_label)
        layout.addWidget(self.db_image_combo)

        # Dropdown for selecting operation type
        self.operation_label = QLabel('Select Operation Type:')
        self.operation_label.setFont(font)
        self.operation_combo = QComboBox()
        self.operation_combo.setFont(font)
        self.operation_combo.addItems(['JOIN', 'INSERT'])

        layout.addWidget(self.operation_label)
        layout.addWidget(self.operation_combo)

        # SpinBox for number of records
        self.records_label = QLabel('Number of Records:')
        self.records_label.setFont(font)
        self.records_spinbox = QSpinBox()
        self.records_spinbox.setFont(font)
        self.records_spinbox.setRange(1, 1000000)
        self.records_spinbox.setValue(1000)

        layout.addWidget(self.records_label)
        layout.addWidget(self.records_spinbox)

        # LineEdit for data types
        self.data_types_label = QLabel('Data Types (comma separated):')
        self.data_types_label.setFont(font)
        self.data_types_edit = QLineEdit()
        self.data_types_edit.setFont(font)
        self.data_types_edit.setPlaceholderText('e.g., int,str,date')

        layout.addWidget(self.data_types_label)
        layout.addWidget(self.data_types_edit)

        # Button to start the process
        self.start_button = QPushButton('Start')
        self.start_button.setFont(font)
        self.start_button.clicked.connect(self.start_process)

        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def start_process(self):
        self.db_image = self.db_image_combo.currentText()
        self.operation = self.operation_combo.currentText()
        self.num_records = self.records_spinbox.value()
        self.data_types = self.data_types_edit.text()

        # Преобразование строки типов данных в список
        self.data_types = [dt.strip() for dt in self.data_types.split(',')]

        logger.info(f'Selected DB Image: {self.db_image}')
        logger.info(f'Selected Operation: {self.operation}')
        logger.info(f'Number of Records: {self.num_records}')
        logger.info(f'Data Types: {self.data_types}')

        # Docker container setup
        db_name = 'test_db'
        user = 'user'
        password = 'example'
        host = 'localhost'
        port = 5432

        self.docker_manager.pull_image(self.db_image)

        # Запуск контейнера
        self.docker_manager.run_container(
            image_name=self.db_image,
            container_name=f"{self.db_image}_test",
            ports={"5432/tcp": port},
            environment={"POSTGRES_DB": db_name, "POSTGRES_USER": user, "POSTGRES_PASSWORD": password}
        )

        self.generate_csv_and_load_data(db_name, user, password, host,
                                        port)

    def generate_csv_and_load_data(self,
                                   db_name: str, user: str, password: str, host: str, port: int):
        generate_csv(settings.CSV_FILE_WITH_TEST_DATA, self.num_records, self.data_types)

        # Параметры подключения к базе данных
        db_manager = DatabaseManager(
            db_type='postgresql',
            username=user,
            password=password,
            host=host,
            port=port,
            db_name=db_name
        )

        self.load_test(settings.CSV_FILE_WITH_TEST_DATA, db_manager, 'test_table')

        logger.info('Process completed.')
        self.test_completed.emit()  # Испускание сигнала по завершении теста

    @measure_performance(sqlite_manager)
    def load_test(self, csv_file, db_manager, table):
        # Загрузка данных в базу данных
        load_csv_to_db(csv_file, db_manager, table)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ConfigApp()
    ex.show()
    sys.exit(app.exec_())

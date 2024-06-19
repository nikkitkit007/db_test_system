import sys

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QSpinBox, QLineEdit, QPushButton, QApplication

from log import get_logger
from manager.db_manager import DatabaseManager
from manager.docker_manager import DockerManager
from utils import load_csv_to_db, execute_and_measure, generate_csv


logger = get_logger(__name__)


class DockerConfigApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

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
        self.db_image_combo.addItems(['postgres:latest', 'mysql:latest', 'mariadb:latest'])

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
        db_image = self.db_image_combo.currentText()
        operation = self.operation_combo.currentText()
        num_records = self.records_spinbox.value()
        data_types_input = self.data_types_edit.text()

        # Преобразование строки типов данных в список
        data_types = [dt.strip() for dt in data_types_input.split(',')]

        print(f'Selected DB Image: {db_image}')
        print(f'Selected Operation: {operation}')
        print(f'Number of Records: {num_records}')
        print(f'Data Types: {data_types}')

        # Docker container setup
        db_name = 'test_db'
        user = 'user'
        password = 'example'
        host = 'localhost'
        port = 5432

        docker_manager = DockerManager()
        docker_manager.pull_image(db_image)

        # Запуск контейнера
        docker_manager.run_container(
            image_name=db_image,
            container_name="postgres_test",
            ports={"5432/tcp": port},
            environment={"POSTGRES_DB": db_name, "POSTGRES_USER": user, "POSTGRES_PASSWORD": password}
        )

        self.generate_csv_and_load_data(db_image, operation, num_records, data_types, db_name, user, password, host,
                                        port)

    def generate_csv_and_load_data(self, db_image: str, operation: str, num_records: int, data_types: list,
                                   db_name: str, user: str, password: str, host: str, port: int):
        # Генерация CSV
        csv_file = 'test_data.csv'
        generate_csv(csv_file, num_records, data_types)

        # Параметры подключения к базе данных
        db_manager = DatabaseManager(
            db_type='postgresql',
            username=user,
            password=password,
            host=host,
            port=port,
            db_name=db_name
        )

        # Загрузка данных в базу данных
        load_csv_to_db(csv_file, db_manager, 'test_table')

        print('Process completed.')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DockerConfigApp()
    ex.show()
    sys.exit(app.exec_())

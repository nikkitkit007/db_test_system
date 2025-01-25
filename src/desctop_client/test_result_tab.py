import sys

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox, QTableWidgetItem, QTableWidget

from src.storage.test_result_storage import sqlite_manager


class TestResultsApp(QWidget):
    def __init__(self, ):
        super().__init__()

        self.initUI()
        self.load_results()

    def initUI(self):
        self.setWindowTitle('Test Results Manager')

        layout = QVBoxLayout()

        font = QFont('Arial', 14)

        # List Widget for displaying test results
        self.results_list = QListWidget()
        self.results_list.setFont(font)
        self.results_list.itemClicked.connect(self.display_result_details)

        layout.addWidget(self.results_list)

        # Table for displaying selected test result details
        self.details_label = QLabel('Test Details:')
        self.details_label.setFont(font)
        layout.addWidget(self.details_label)

        self.details_table = QTableWidget()
        self.details_table.setFont(font)
        self.details_table.setColumnCount(7)
        self.details_table.setHorizontalHeaderLabels(
            ['Timestamp', 'DB Image', 'Operation', 'Num Records', 'Data Types', 'Execution Time', 'Memory Used'])
        self.details_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.details_table)

        # Button to delete selected test result
        self.delete_button = QPushButton('Delete Selected Result')
        self.delete_button.setFont(font)
        self.delete_button.clicked.connect(self.delete_selected_result)

        layout.addWidget(self.delete_button)

        self.setLayout(layout)

    def load_results(self):
        """ Загружает результаты тестов из базы данных и отображает их в списке """
        self.results_list.clear()
        results = sqlite_manager.select_all_results()
        for result in results:
            self.results_list.addItem(
                f"ID: {result[0]}, Timestamp: {result[1]}, DB Image: {result[2]}, Operation: {result[3]}")

    def display_result_details(self, item):
        """ Отображает детали выбранного результата теста """
        result_id = int(item.text().split(",")[0].split(":")[1].strip())
        result = sqlite_manager.select_result_by_id(result_id)

        # Очистка таблицы перед добавлением новых данных
        self.details_table.setRowCount(0)

        if result:
            self.details_table.setRowCount(1)
            self.details_table.setItem(0, 0, QTableWidgetItem(result[1]))
            self.details_table.setItem(0, 1, QTableWidgetItem(result[2]))
            self.details_table.setItem(0, 2, QTableWidgetItem(result[3]))
            self.details_table.setItem(0, 3, QTableWidgetItem(str(result[4])))
            self.details_table.setItem(0, 4, QTableWidgetItem(result[5]))
            self.details_table.setItem(0, 5, QTableWidgetItem(str(result[6])))
            self.details_table.setItem(0, 6, QTableWidgetItem(str(result[7])))

    def delete_selected_result(self):
        """ Удаляет выбранный результат теста """
        selected_item = self.results_list.currentItem()
        if selected_item:
            result_id = int(selected_item.text().split(",")[0].split(":")[1].strip())
            sqlite_manager.delete_result(result_id)
            self.load_results()
            QMessageBox.information(self, "Success", "Result deleted successfully!")
        else:
            QMessageBox.warning(self, "Warning", "No result selected to delete!")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TestResultsApp()
    ex.show()
    sys.exit(app.exec_())

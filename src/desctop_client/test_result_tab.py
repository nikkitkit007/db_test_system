from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
)
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt

from src.storage.test_result_storage import sqlite_manager


class TestResultsApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_results()

    def initUI(self):
        layout = QVBoxLayout()
        font = QFont("Arial", 14)

        # Заголовок
        header = QLabel("Результаты тестирования")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(header)

        # Список результатов
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.display_result_details)
        layout.addWidget(self.results_list)

        # Таблица с деталями
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(7)
        self.details_table.setHorizontalHeaderLabels(
            ["Timestamp", "DB Image", "Operation", "Num Records", "Data Types", "Exec Time", "Memory"]
        )
        layout.addWidget(self.details_table)

        # Кнопки
        self.delete_button = QPushButton("Удалить результат")
        self.delete_button.clicked.connect(self.delete_selected_result)
        layout.addWidget(self.delete_button)

        self.visualize_button = QPushButton("Визуализировать")
        self.visualize_button.clicked.connect(self.visualize_results)
        layout.addWidget(self.visualize_button)

        self.setLayout(layout)

    def load_results(self):
        """Загружает результаты тестов и отображает их в списке."""
        self.results_list.clear()
        results = sqlite_manager.select_all_results()
        for result in results:
            self.results_list.addItem(f"ID: {result.id}, Timestamp: {result.timestamp}")

    def display_result_details(self, item):
        """Отображает детали выбранного результата теста"""
        result_id = int(item.text().split(",")[0].split(":")[1].strip())
        result = sqlite_manager.select_result_by_id(result_id)

        self.details_table.setRowCount(0)
        if result:
            self.details_table.setRowCount(1)
            self.details_table.setItem(0, 0, QTableWidgetItem(str(result.id)))
            self.details_table.setItem(0, 1, QTableWidgetItem(result.timestamp))
            self.details_table.setItem(0, 2, QTableWidgetItem(result.db_image))
            self.details_table.setItem(0, 3, QTableWidgetItem(result.operation))
            self.details_table.setItem(0, 4, QTableWidgetItem(str(result.num_records)))
            self.details_table.setItem(0, 5, QTableWidgetItem(result.data_types))
            self.details_table.setItem(0, 6, QTableWidgetItem(f"{result.execution_time:.2f}"))
            self.details_table.setItem(0, 7, QTableWidgetItem(f"{result.memory_used:.2f}"))

    def delete_selected_result(self):
        selected_item = self.results_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Ошибка", "Выберите результат для удаления.")
            return

        result_id = int(selected_item.text().split(",")[0].split(":")[1].strip())
        sqlite_manager.delete_result(result_id)
        self.load_results()

    def visualize_results(self):
        results = sqlite_manager.select_all_results()
        if not results:
            QMessageBox.warning(self, "Ошибка", "Нет данных для визуализации.")
            return

        timestamps = [result.timestamp for result in results]
        exec_times = [result.execution_time for result in results]

        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, exec_times, marker='o')
        plt.xlabel("Время")
        plt.ylabel("Время выполнения")
        plt.title("Визуализация времени выполнения")
        plt.grid(True)
        plt.show()


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     ex = TestResultsApp()
#     ex.show()
#     sys.exit(app.exec_())

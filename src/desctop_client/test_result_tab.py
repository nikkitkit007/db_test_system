import matplotlib.pyplot as plt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QComboBox,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.storage.test_result_storage import sqlite_manager


class TestResultsApp(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.initUI()
        self.load_results()

    def initUI(self) -> None:
        layout = QVBoxLayout()
        QFont("Arial", 14)

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
            ["Timestamp", "DB Image", "Operation", "Num Records", "Data Types", "Exec Time", "Memory"],
        )
        layout.addWidget(self.details_table)

        # Комбобокс для выбора типа визуализации
        self.visualization_type = QComboBox()
        self.visualization_type.addItems(["Время выполнения", "Распределение операций", "Количество записей"])
        layout.addWidget(self.visualization_type)

        # Кнопки
        self.delete_button = QPushButton("Удалить результат")
        self.delete_button.clicked.connect(self.delete_selected_result)
        layout.addWidget(self.delete_button)

        self.visualize_button = QPushButton("Визуализировать")
        self.visualize_button.clicked.connect(self.visualize_results)
        layout.addWidget(self.visualize_button)

        self.setLayout(layout)

    def load_results(self) -> None:
        """Загружает результаты тестов и отображает их в списке."""
        self.results_list.clear()
        results = sqlite_manager.select_all_results()
        for result in results:
            self.results_list.addItem(f"ID: {result.id}, Timestamp: {result.timestamp}")

    def display_result_details(self, item) -> None:
        """Отображает детали выбранного результата теста"""
        result_id = int(item.text().split(",")[0].split(":")[1].strip())
        result = sqlite_manager.select_result_by_id(result_id)

        self.details_table.setRowCount(0)
        if result:
            self.details_table.setRowCount(1)
            self.details_table.setItem(0, 0, QTableWidgetItem(result.timestamp))
            self.details_table.setItem(0, 1, QTableWidgetItem(result.db_image))
            self.details_table.setItem(0, 2, QTableWidgetItem(result.operation))
            self.details_table.setItem(0, 3, QTableWidgetItem(str(result.num_records)))
            self.details_table.setItem(0, 4, QTableWidgetItem(result.data_types))
            self.details_table.setItem(0, 5, QTableWidgetItem(f"{result.execution_time:.2f}"))
            self.details_table.setItem(0, 6, QTableWidgetItem(f"{result.memory_used:.2f}"))

    def delete_selected_result(self) -> None:
        selected_item = self.results_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Ошибка", "Выберите результат для удаления.")
            return

        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите удалить выбранный результат?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            result_id = int(selected_item.text().split(",")[0].split(":")[1].strip())
            sqlite_manager.delete_result(result_id)
            self.load_results()

    def visualize_results(self) -> None:
        """Визуализирует данные на основе выбранного типа визуализации"""
        results = sqlite_manager.select_all_results()
        if not results:
            QMessageBox.warning(self, "Ошибка", "Нет данных для визуализации.")
            return

        vis_type = self.visualization_type.currentText()

        if vis_type == "Время выполнения":
            self.plot_execution_time(results)
        elif vis_type == "Распределение операций":
            self.plot_operation_distribution(results)
        elif vis_type == "Количество записей":
            self.plot_record_count_distribution(results)

    def plot_execution_time(self, results) -> None:
        """График времени выполнения"""
        timestamps = [result.timestamp for result in results]
        exec_times = [result.execution_time for result in results]

        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, exec_times, marker="o", label="Время выполнения")
        plt.xlabel("Время")
        plt.ylabel("Время выполнения (секунды)")
        plt.title("Визуализация времени выполнения")
        plt.legend()
        plt.grid(True)
        plt.show()

    def plot_operation_distribution(self, results) -> None:
        """Круговая диаграмма распределения операций"""
        operations = [result.operation for result in results]
        operation_counts = {op: operations.count(op) for op in set(operations)}

        plt.figure(figsize=(8, 8))
        plt.pie(operation_counts.values(), labels=operation_counts.keys(), autopct="%1.1f%%", startangle=140)
        plt.title("Распределение операций")
        plt.show()

    def plot_record_count_distribution(self, results) -> None:
        """Гистограмма количества записей"""
        num_records = [result.num_records for result in results]

        plt.figure(figsize=(10, 6))
        plt.hist(num_records, bins=10, color="skyblue", edgecolor="black")
        plt.xlabel("Количество записей")
        plt.ylabel("Частота")
        plt.title("Гистограмма количества записей")
        plt.grid(axis="y")
        plt.show()

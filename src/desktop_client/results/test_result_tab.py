import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.config.config import settings
from src.desktop_client.results.visualizer import TestResultsVisualizer
from src.storage.result_storage import result_manager

results_icon_path = os.path.join(settings.ICONS_PATH, "results_icon.svg")


class TestResultsApp(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.initUI()
        # Загрузим в фильтры уникальные значения db_image и operation
        self.load_filter_values()
        self.visualizer = TestResultsVisualizer()
        # Сразу загрузим результаты (без фильтров)
        self.load_results()

    def initUI(self) -> None:
        """Создаёт интерфейс вкладки «Test Results» с фильтрами, списком и визуализацией."""
        main_layout = QVBoxLayout()
        QFont("Arial", 14)

        # === Блок фильтров ===
        filter_group = QGroupBox("Фильтр результатов")
        filter_layout = QHBoxLayout()

        # Фильтр по db_image
        self.db_image_label = QLabel("DB Image:")
        self.db_image_filter_combo = QComboBox()
        # По умолчанию — «Все»
        self.db_image_filter_combo.addItem("Все", "")

        filter_layout.addWidget(self.db_image_label)
        filter_layout.addWidget(self.db_image_filter_combo)

        # Фильтр по operation
        self.operation_label = QLabel("Operation:")
        self.operation_filter_combo = QComboBox()
        # По умолчанию — «Все»
        self.operation_filter_combo.addItem("Все", "")

        filter_layout.addWidget(self.operation_label)
        filter_layout.addWidget(self.operation_filter_combo)

        # Кнопка «Применить»
        self.apply_filter_button = QPushButton("Применить")
        self.apply_filter_button.clicked.connect(self.apply_filter)
        filter_layout.addWidget(self.apply_filter_button)

        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)

        # === Группа «Результаты тестирования» ===
        results_group = QGroupBox("Результаты тестирования")
        results_layout = QVBoxLayout()

        # Список результатов
        self.results_list = QListWidget()
        self.results_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection,
        )
        self.results_list.itemClicked.connect(self.display_result_details)
        results_layout.addWidget(self.results_list)

        # Кнопка удаления
        self.delete_button = QPushButton("Удалить результат(ы)")
        self.delete_button.clicked.connect(self.delete_selected_results)
        results_layout.addWidget(self.delete_button)

        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)

        # === Таблица с деталями выбранного результата ===
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(7)
        self.details_table.setHorizontalHeaderLabels(
            [
                "Timestamp",
                "DB Image",
                "Operation",
                "Num Records",
                "Test info",
                "Exec Time",
                "Memory",
            ],
        )
        main_layout.addWidget(self.details_table)

        # === Блок управления визуализацией ===
        visualization_layout = QHBoxLayout()

        self.visualization_type = QComboBox()
        self.visualization_type.addItems(
            ["Время выполнения", "Распределение операций", "Количество записей"],
        )
        visualization_layout.addWidget(self.visualization_type)

        self.visualize_button = QPushButton("Визуализировать")
        self.visualize_button.clicked.connect(self.visualize_results)
        visualization_layout.addWidget(self.visualize_button)

        main_layout.addLayout(visualization_layout)
        self.setLayout(main_layout)

    # ---------------------------------------------------------------------
    # Методы для фильтрации
    # ---------------------------------------------------------------------
    def load_filter_values(self) -> None:
        """
        Заполняет комбобоксы уникальными значениями db_image и operation,
        чтобы пользователь мог выбирать фильтры.
        """
        # Получаем все уникальные db_image и заполняем
        db_images = result_manager.get_distinct_db_images()  # Предполагаемый метод
        for dbi in db_images:
            self.db_image_filter_combo.addItem(dbi, dbi)

        # Получаем все уникальные operation и заполняем
        operations = result_manager.get_distinct_operations()  # Предполагаемый метод
        for op in operations:
            self.operation_filter_combo.addItem(op, op)

    def apply_filter(self) -> None:
        """
        Считывает выбранные значения из фильтров и загружает результаты.
        """
        selected_db_image = self.db_image_filter_combo.currentData()
        selected_operation = self.operation_filter_combo.currentData()

        # Вызываем load_results с нужными параметрами
        self.load_results(db_image=selected_db_image, operation=selected_operation)

    # ---------------------------------------------------------------------
    # Методы для загрузки/отображения результатов
    # ---------------------------------------------------------------------
    def load_results(
        self,
        db_image: str | None = None,
        operation: str | None = None,
    ) -> None:
        """
        Загружает результаты тестов из БД с учётом фильтров и отображает их в списке.
        Если db_image или operation пустые, фильтр не применяется.
        """
        self.results_list.clear()
        results = result_manager.select_all_results(
            db_image=db_image,
            operation=operation,
        )
        # предполагается, что select_all_results умеет применять фильтры
        for result in results:
            item_text = f"ID: {result.id}, Timestamp: {result.timestamp}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, result.id)
            self.results_list.addItem(item)

        # После перезагрузки списка очистим детали (на случай, если пользователь
        # смотрел детали предыдущего фильтра)
        self.details_table.setRowCount(0)

    def display_result_details(self, item: QListWidgetItem) -> None:
        """Отображает детали выбранного результата теста."""
        if not item:
            return

        result_id = item.data(Qt.ItemDataRole.UserRole)
        result = result_manager.select_result_by_id(result_id)

        self.details_table.setRowCount(0)
        if result:
            self.details_table.setRowCount(1)
            self.details_table.setItem(0, 0, QTableWidgetItem(result.timestamp))
            self.details_table.setItem(0, 1, QTableWidgetItem(result.db_image))
            self.details_table.setItem(0, 2, QTableWidgetItem(result.operation))
            self.details_table.setItem(0, 3, QTableWidgetItem(str(result.num_records)))
            self.details_table.setItem(0, 4, QTableWidgetItem(result.step_description))
            self.details_table.setItem(
                0,
                5,
                QTableWidgetItem(f"{result.execution_time:.2f}"),
            )
            self.details_table.setItem(
                0,
                6,
                QTableWidgetItem(f"{result.memory_used:.2f}"),
            )

    def delete_selected_results(self) -> None:
        """Удаляет выбранные результаты из БД и обновляет список."""
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите результат(ы) для удаления.")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить выбранные результаты?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                result_id = item.data(Qt.ItemDataRole.UserRole)
                result_manager.delete_result(result_id)
            self.load_results()  # Перезагружаем без фильтров или с текущими — на ваше усмотрение
            self.details_table.setRowCount(0)

    def visualize_results(self) -> None:
        """Визуализирует данные на основе выбранного типа визуализации."""
        # Можно брать текущие фильтры, чтобы визуализировать только отфильтрованные результаты
        db_image_filter = self.db_image_filter_combo.currentData()
        operation_filter = self.operation_filter_combo.currentData()

        results = result_manager.select_all_results(
            db_image=db_image_filter,
            operation=operation_filter,
        )
        if not results:
            QMessageBox.warning(self, "Ошибка", "Нет данных для визуализации.")
            return

        vis_type = self.visualization_type.currentText()
        if vis_type == "Время выполнения":
            self.visualizer.plot_execution_time(results)
        elif vis_type == "Распределение операций":
            self.visualizer.plot_operation_distribution(results)
        elif vis_type == "Количество записей":
            self.visualizer.plot_record_count_distribution(results)

import os

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from src.app.config.config import settings
from src.app.desktop_client.results.visualizer import (
    Diagram,
    TestResultsVisualizer,
    diagrams,
)
from src.app.storage.db_manager.result_storage import result_manager

results_icon_path = os.path.join(settings.ICONS_PATH, "results_icon.svg")


class TestResultsApp(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.initUI()
        self.load_possible_filter_key_values()
        self.visualizer = TestResultsVisualizer()
        self.get_results()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(5000)
        self.refresh_timer.timeout.connect(self.on_timer_refresh)
        self.refresh_timer.start()

    def initUI(self) -> None:
        """Создаёт интерфейс вкладки «Test Results» с фильтрами, таблицей и визуализацией."""
        main_layout = QVBoxLayout()
        QFont("Arial", 14)

        # === Блок фильтров ===
        filter_group = QGroupBox("Фильтр результатов")
        filter_layout = QHBoxLayout()

        # Фильтр по db_image
        self.db_image_label = QLabel("Docker образ:")
        self.db_image_filter_combo = QComboBox()
        self.db_image_filter_combo.addItem("Все", "")
        filter_layout.addWidget(self.db_image_label)
        filter_layout.addWidget(self.db_image_filter_combo)

        # Фильтр по operation
        self.operation_label = QLabel("Операция:")
        self.operation_filter_combo = QComboBox()
        self.operation_filter_combo.addItem("Все", "")
        filter_layout.addWidget(self.operation_label)
        filter_layout.addWidget(self.operation_filter_combo)

        # Кнопка «Применить»
        self.apply_filter_button = QPushButton("Применить")
        self.apply_filter_button.clicked.connect(self.get_results)
        filter_layout.addWidget(self.apply_filter_button)

        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)

        # === Группа «Результаты тестирования» (используется таблица) ===
        results_group = QGroupBox("Результаты тестирования")
        results_layout = QVBoxLayout()

        self.results_table = QTableWidget()
        self.results_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows,
        )
        self.results_table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection,
        )
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels(
            [
                "Timestamp",
                "DB Image",
                "Operation",
                "Num Records",
                "Test info",
                "Exec Time",
                "Memory",
                "CPU %",
            ],
        )
        self.results_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows,
        )
        results_layout.addWidget(self.results_table)

        # Кнопка удаления
        self.delete_button = QPushButton("Удалить результат(ы)")
        self.delete_button.clicked.connect(self.delete_selected_results)
        results_layout.addWidget(self.delete_button)

        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)

        # === Блок управления визуализацией ===
        visualization_layout = QHBoxLayout()

        self.visualization_type = QComboBox()
        self.visualization_type.addItems(diagrams)
        visualization_layout.addWidget(self.visualization_type)

        self.visualize_button = QPushButton("Визуализировать")
        self.visualize_button.clicked.connect(self.visualize_results)
        visualization_layout.addWidget(self.visualize_button)

        main_layout.addLayout(visualization_layout)
        self.setLayout(main_layout)

    # ---------------------------------------------------------------------
    # Методы для фильтрации
    # ---------------------------------------------------------------------
    def load_possible_filter_key_values(self) -> None:
        """
        Заполняет комбобоксы уникальными значениями db_image и operation,
        чтобы пользователь мог выбирать фильтры.
        """
        for dbi in result_manager.get_distinct_db_images():
            self.db_image_filter_combo.addItem(dbi, dbi)

        for operator in result_manager.get_distinct_operations():
            self.operation_filter_combo.addItem(operator, operator)

    def get_results(self) -> None:
        self.load_results(
            db_image=self.db_image_filter_combo.currentData(),
            operation=self.operation_filter_combo.currentData(),
        )

    # ---------------------------------------------------------------------
    # Методы для загрузки/отображения результатов
    # ---------------------------------------------------------------------
    def load_results(
        self,
        db_image: str | None = None,
        operation: str | None = None,
    ) -> None:
        results = result_manager.select_all_results(
            db_image=db_image,
            operation=operation,
        )
        # Обновляем таблицу
        self.results_table.setRowCount(0)
        self.results_table.setRowCount(len(results))
        for row, result in enumerate(results):
            # Создаём ячейку для Timestamp и сохраняем result.id в данных ячейки
            item_timestamp = QTableWidgetItem(result.timestamp)
            item_timestamp.setData(Qt.ItemDataRole.UserRole, result.id)
            self.results_table.setItem(row, 0, item_timestamp)
            self.results_table.setItem(row, 1, QTableWidgetItem(result.db_image))
            self.results_table.setItem(row, 2, QTableWidgetItem(result.operation))
            self.results_table.setItem(
                row,
                3,
                QTableWidgetItem(str(result.num_records)),
            )
            self.results_table.setItem(
                row,
                4,
                QTableWidgetItem(result.step_description),
            )
            self.results_table.setItem(
                row,
                5,
                QTableWidgetItem(f"{result.execution_time:.2f}"),
            )
            self.results_table.setItem(
                row,
                6,
                QTableWidgetItem(f"{result.memory_used:.2f}"),
            )
            self.results_table.setItem(
                row,
                7,
                QTableWidgetItem(f"{result.cpu_percent:.2f}"),
            )

    def delete_selected_results(self) -> None:
        selected_indexes = self.results_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Ошибка", "Выберите результат(ы) для удаления.")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить выбранные результаты?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            for model_index in selected_indexes:
                row = model_index.row()
                result_id = self.results_table.item(row, 0).data(
                    Qt.ItemDataRole.UserRole,
                )
                result_manager.delete_result(result_id)
            self.get_results()

    def on_timer_refresh(self) -> None:
        """
        Каждые 5 секунд обновляем таблицу результатов,
        используя текущие фильтры и восстанавливая выделенные строки.
        """
        # Сохраняем id выбранных результатов
        selected_ids = []
        for model_index in self.results_table.selectionModel().selectedRows():
            row = model_index.row()
            item = self.results_table.item(row, 0)
            if item:
                selected_ids.append(item.data(Qt.ItemDataRole.UserRole))

        # Сохраняем выбранные значения фильтров
        old_db_image_data = self.db_image_filter_combo.currentData()
        old_operation_data = self.operation_filter_combo.currentData()

        # --- Обновляем db_image_filter_combo ---
        self.db_image_filter_combo.blockSignals(True)
        self.db_image_filter_combo.clear()
        self.db_image_filter_combo.addItem("Все", "")
        for dbi in result_manager.get_distinct_db_images():
            self.db_image_filter_combo.addItem(dbi, dbi)
        index_db_image = self.db_image_filter_combo.findData(old_db_image_data)
        if index_db_image >= 0:
            self.db_image_filter_combo.setCurrentIndex(index_db_image)
        else:
            self.db_image_filter_combo.setCurrentIndex(0)
        self.db_image_filter_combo.blockSignals(False)

        # --- Обновляем operation_filter_combo ---
        self.operation_filter_combo.blockSignals(True)
        self.operation_filter_combo.clear()
        self.operation_filter_combo.addItem("Все", "")
        for op in result_manager.get_distinct_operations():
            self.operation_filter_combo.addItem(op, op)
        index_op = self.operation_filter_combo.findData(old_operation_data)
        if index_op >= 0:
            self.operation_filter_combo.setCurrentIndex(index_op)
        else:
            self.operation_filter_combo.setCurrentIndex(0)
        self.operation_filter_combo.blockSignals(False)

        # Обновляем таблицу с результатами
        self.get_results()

        # Восстанавливаем выделение строк по сохранённым id
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 0)
            if item and (item.data(Qt.ItemDataRole.UserRole) in selected_ids):
                self.results_table.selectRow(row)

    def visualize_results(self) -> None:
        """Визуализирует данные на основе выбранного типа визуализации."""
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
        if vis_type == Diagram.RESOURCE_USAGE_BY_DB.value:
            self.visualizer.plot_resource_usage_by_db(results)
        elif vis_type == Diagram.RECORDS_VS_EXECUTION_TIME.value:
            self.visualizer.plot_records_vs_execution_time(results)
        elif vis_type == Diagram.EXECUTION_TIME_DISTRIBUTION.value:
            self.visualizer.plot_execution_time_distribution(results)

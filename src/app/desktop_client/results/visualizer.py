import enum

import numpy as np
from matplotlib import pyplot as plt


class Diagram(enum.Enum):
    RESOURCE_USAGE_BY_DB = "Потребление памяти и CPU по БД"
    EXECUTION_TIME_DISTRIBUTION = "Распределение времени выполнения по операциям"
    RECORDS_VS_EXECUTION_TIME = "Связь между количеством записей и временем выполнения"


diagrams = [diagram.value for diagram in Diagram]


class TestResultsVisualizer:
    @staticmethod
    def plot_resource_usage_by_db(results) -> None:
        """
        Строит столбчатую диаграмму, показывающую среднее потребление памяти и CPU для каждого образа БД.
        """
        # Группируем данные по db_image
        groups = {}
        for res in results:
            groups.setdefault(res.db_image, {"memory": [], "cpu": []})
            if res.memory_used is not None:
                groups[res.db_image]["memory"].append(res.memory_used)
            if res.cpu_percent is not None:
                groups[res.db_image]["cpu"].append(res.cpu_percent)

        db_images = list(groups.keys())
        avg_memory = [
            np.mean(groups[db]["memory"]) if groups[db]["memory"] else 0
            for db in db_images
        ]
        avg_cpu = [
            np.mean(groups[db]["cpu"]) if groups[db]["cpu"] else 0 for db in db_images
        ]

        ind = np.arange(len(db_images))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(ind - width / 2, avg_memory, width, label="Memory (MB)")
        ax.bar(ind + width / 2, avg_cpu, width, label="CPU (%)")

        ax.set_ylabel("Среднее значение")
        ax.set_title("Потребление памяти и CPU по образам БД")
        ax.set_xticks(ind)
        ax.set_xticklabels(db_images, rotation=45, ha="right")
        ax.legend()

        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_execution_time_distribution(results) -> None:
        """
        Строит ящичковую диаграмму (boxplot) распределения времени выполнения для каждой операции.
        """
        # Группируем время выполнения по операциям
        data = {}
        for res in results:
            if res.operation not in data:
                data[res.operation] = []
            if res.execution_time is not None:
                data[res.operation].append(res.execution_time)

        operations = list(data.keys())
        values = [data[op] for op in operations]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.boxplot(values, labels=operations)
        ax.set_xlabel("Операция")
        ax.set_ylabel("Время выполнения (сек)")
        ax.set_title("Распределение времени выполнения по операциям")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_records_vs_execution_time(results) -> None:
        """
        Строит scatter plot для анализа зависимости времени выполнения от количества записей.
        """
        records = []
        exec_times = []
        for res in results:
            if res.num_records is not None and res.execution_time is not None:
                records.append(res.num_records)
                exec_times.append(res.execution_time)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(records, exec_times, alpha=0.7)
        ax.set_xlabel("Количество записей")
        ax.set_ylabel("Время выполнения (сек)")
        ax.set_title("Зависимость времени выполнения от количества записей")
        plt.tight_layout()
        plt.show()

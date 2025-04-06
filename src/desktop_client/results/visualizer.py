import datetime

from matplotlib import pyplot as plt

from src.storage.model import TestResults


class TestResultsVisualizer:
    @staticmethod
    def plot_execution_time(results: list[TestResults]) -> None:
        timestamps = [
            datetime.datetime.fromisoformat(result.timestamp) for result in results
        ]
        exec_times = [result.execution_time for result in results]

        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, exec_times, marker="o", label="Время выполнения")
        plt.xlabel("Время")
        plt.ylabel("Время выполнения (секунды)")
        plt.title("Визуализация времени выполнения")
        plt.legend()
        plt.grid(True)
        plt.show()

    @staticmethod
    def plot_operation_distribution(results: list[TestResults]) -> None:
        operations = [result.operation for result in results]
        operation_counts = {op: operations.count(op) for op in set(operations)}

        plt.figure(figsize=(8, 8))
        plt.pie(
            list(operation_counts.values()),
            labels=list(operation_counts.keys()),
            autopct="%1.1f%%",
            startangle=140,
        )
        plt.title("Распределение операций")
        plt.show()

    @staticmethod
    def plot_record_count_distribution(results: list[TestResults]) -> None:
        num_records = [result.num_records for result in results]

        plt.figure(figsize=(10, 6))
        plt.hist(num_records, bins=10, color="skyblue", edgecolor="black")
        plt.xlabel("Количество записей")
        plt.ylabel("Частота")
        plt.title("Гистограмма количества записей")
        plt.grid(axis="y")
        plt.show()

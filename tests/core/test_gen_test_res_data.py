import random
from datetime import datetime

from src.storage.test_result_storage import sqlite_manager


def test_generate_test_results(num_results: int = 10) -> None:
    """
    Генерирует временные результаты тестов и сохраняет их в базе данных.

    :param num_results: Количество результатов для генерации.
    """
    db_images = ["postgres:latest", "mysql:latest", "sqlite:latest"]
    operations = ["INSERT", "SELECT", "JOIN"]
    data_types_list = ["int, str", "int, str, date", "float, str, bool"]

    for _ in range(num_results):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db_image = random.choice(db_images)
        operation = random.choice(operations)
        num_records = random.randint(100, 10000)
        data_types = random.choice(data_types_list)
        execution_time = round(
            random.uniform(0.1, 5.0),
            2,
        )  # Время выполнения в секундах
        memory_used = round(
            random.uniform(50.0, 200.0),
            2,
        )  # Использованная память в МБ

        # Вставка в базу данных
        sqlite_manager.insert_result(
            timestamp=timestamp,
            db_image=db_image,
            operation=operation,
            num_records=num_records,
            data_types=data_types,
            execution_time=execution_time,
            memory_used=memory_used,
        )

    test_results = sqlite_manager.select_all_results()
    assert len(test_results) == num_results

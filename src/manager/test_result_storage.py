import sqlite3
from sqlite3 import Error

from src.config.log import get_logger

logger = get_logger(__name__)


class SQLiteManager:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.conn = self.create_connection()

    def create_connection(self):
        """ Создание соединения с базой данных SQLite """
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            logger.info(f"Соединение с базой данных SQLite {self.db_file} установлено.")
        except Error as e:
            logger.info(f"Ошибка при соединении с базой данных SQLite: {e}")
        return conn

    def create_table(self):
        """ Создание таблицы для хранения результатов тестов """
        create_table_sql = """ CREATE TABLE IF NOT EXISTS test_results (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    timestamp TEXT NOT NULL,
                                    db_image TEXT NOT NULL,
                                    operation TEXT NOT NULL,
                                    num_records INTEGER NOT NULL,
                                    data_types TEXT NOT NULL,
                                    execution_time REAL,
                                    memory_used REAL
                                ); """
        try:
            c = self.conn.cursor()
            c.execute(create_table_sql)
            logger.info("Таблица test_results создана.")
        except Error as e:
            logger.info(f"Ошибка при создании таблицы: {e}")

    def insert_result(self, timestamp: str, db_image: str, operation: str, num_records: int, data_types: str,
                      execution_time: float, memory_used: float):
        """ Вставка записи в таблицу результатов тестов """
        sql = ''' INSERT INTO test_results(timestamp, db_image, operation, num_records, data_types, execution_time, memory_used)
                  VALUES(?,?,?,?,?,?,?) '''
        cur = self.conn.cursor()
        cur.execute(sql, (timestamp, db_image, operation, num_records, data_types, execution_time, memory_used))
        self.conn.commit()
        return cur.lastrowid

    def delete_result(self, id: int):
        """ Удаление записи из таблицы результатов тестов по ID """
        sql = 'DELETE FROM test_results WHERE id=?'
        cur = self.conn.cursor()
        cur.execute(sql, (id,))
        self.conn.commit()

    def select_all_results(self):
        """ Выбор всех записей из таблицы результатов тестов """
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM test_results")
        rows = cur.fetchall()
        return rows

    def select_result_by_id(self, id: int):
        """ Выбор записи из таблицы результатов тестов по ID """
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM test_results WHERE id=?", (id,))
        row = cur.fetchone()
        return row


sqlite_manager = SQLiteManager("test_results.db")
# sqlite_manager.create_table()


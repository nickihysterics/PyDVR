import sqlite3

class Database:
    @staticmethod
    def start_database():
        """
        Инициализирует базу данных и вставляет значения настроек записи по умолчанию, если записей нет.
        """
        Database.initialize_database()
        with sqlite3.connect('PyDVR.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM recording_settings')
            count = cursor.fetchone()[0]

            if count == 0:
                conn.execute(''' 
                    INSERT INTO recording_settings (id, destination, record_length, auto_delete, auto_delete_days, enable_record)
                    VALUES (1, 'C:\\RecVid', 60, FALSE, 7, FALSE)
                ''')

    @staticmethod
    def initialize_database():
        """
        Инициализирует базу данных, создавая таблицы, если они не существуют.
        """
        with sqlite3.connect('PyDVR.db') as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS recording_settings (
                    id INTEGER PRIMARY KEY,
                    destination TEXT NOT NULL DEFAULT 'C:\\RecVid',
                    record_length INTEGER NOT NULL DEFAULT 60,
                    auto_delete BOOLEAN NOT NULL DEFAULT FALSE,
                    auto_delete_days INTEGER NOT NULL DEFAULT 7,
                    enable_record BOOLEAN NOT NULL DEFAULT FALSE
                )
            ''')

    @staticmethod
    def insert_recording_settings(destination, record_length, auto_delete, auto_delete_days, enable_record):
        """
        Вставляет или заменяет настройки записи в базе данных.
        """
        with sqlite3.connect('PyDVR.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO recording_settings (id, destination, record_length, auto_delete, auto_delete_days, enable_record)
                VALUES ((SELECT id FROM recording_settings LIMIT 1), ?, ?, ?, ?, ?)
            ''', (destination, record_length, auto_delete, auto_delete_days, enable_record))
            conn.commit()

    @staticmethod
    def get_recording_settings():
        """
        Получает последние настройки записи из базы данных.
        """
        with sqlite3.connect('PyDVR.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT destination, record_length, auto_delete, auto_delete_days, enable_record FROM recording_settings ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            return result
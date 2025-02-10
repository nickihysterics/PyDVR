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

            # Проверяем, есть ли записи в recording_settings
            cursor.execute('SELECT COUNT(*) FROM recording_settings')
            count = cursor.fetchone()[0]
            if count == 0:
                conn.execute('''
                    INSERT INTO recording_settings (id, destination, record_length, auto_delete, auto_delete_days, enable_record)
                    VALUES (1, 'C:\\RecVid', 60, FALSE, 7, FALSE)
                ''')

            # Проверяем, есть ли записи в camera_settings
            cursor.execute('SELECT COUNT(*) FROM camera_settings')
            count = cursor.fetchone()[0]
            if count == 0:
                conn.execute('''
                    INSERT INTO camera_settings (id, camera_index, mirror)
                    VALUES (1, 0, FALSE)
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
            conn.execute('''
                CREATE TABLE IF NOT EXISTS camera_settings (
                    id INTEGER PRIMARY KEY,
                    camera_index INTEGER NOT NULL DEFAULT 0,
                    mirror BOOLEAN NOT NULL DEFAULT FALSE
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
    def update_camera_settings(camera_index, mirror):
        """
        Обновляет настройки камеры в базе данных или создаёт запись, если её ещё нет.
        """
        with sqlite3.connect('PyDVR.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM camera_settings LIMIT 1')
            result = cursor.fetchone()
    
            if result:
                # Если запись существует, обновляем её
                cursor.execute('''
                    UPDATE camera_settings 
                    SET camera_index = ?, mirror = ? 
                    WHERE id = ?
                ''', (camera_index, mirror, result[0]))
            else:
                # Если записи нет, создаём новую
                cursor.execute('''
                    INSERT INTO camera_settings (camera_index, mirror)
                    VALUES (?, ?)
                ''', (camera_index, mirror))
    
            conn.commit()

    @staticmethod
    def get_camera_settings():
        """
        Получает последние настройки камеры из базы данных.
        """
        with sqlite3.connect('PyDVR.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT camera_index, mirror FROM camera_settings ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            return result

    @staticmethod
    def get_recording_settings():
        """
        Получает последние настройки записи из базы данных.
        """
        with sqlite3.connect('PyDVR.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT destination, record_length, auto_delete, auto_delete_days, enable_record
                FROM recording_settings ORDER BY id DESC LIMIT 1
            ''')
            result = cursor.fetchone()
            return result
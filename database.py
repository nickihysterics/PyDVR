import sqlite3

class Database:
    @staticmethod
    def start_database():
        Database.initialize_database()
        with sqlite3.connect('PyDVR.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM recording_settings')
            count = cursor.fetchone()[0]

            if count == 0:
                conn.execute('''
                    INSERT INTO recording_settings (id, destination, record_length, auto_delete, auto_delete_days, enable_record)
                    VALUES (1, 'C:\\RecVid', 60, "TRUE", 7, "TRUE")
                ''')

    @staticmethod
    def initialize_database():
        with sqlite3.connect('PyDVR.db') as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS camera_settings (
                    id INTEGER PRIMARY KEY,
                    ip TEXT NOT NULL,
                    login TEXT NOT NULL,
                    password TEXT NOT NULL
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS recording_settings (
                    id INTEGER PRIMARY KEY,
                    destination TEXT NOT NULL DEFAULT 'C:\\RecVid',
                    record_length INTEGER NOT NULL DEFAULT 60,
                    auto_delete BOOLEAN NOT NULL DEFAULT "TRUE",
                    auto_delete_days INTEGER NOT NULL DEFAULT 7,
                    enable_record BOOLEAN NOT NULL DEFAULT "TRUE"
                )
            ''')

    @staticmethod
    def insert_camera_settings(ip, login, password):
        with sqlite3.connect('PyDVR.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO camera_settings (id, ip, login, password)
                VALUES (1, ?, ?, ?)
            ''', (ip, login, password))
            conn.commit()

    @staticmethod
    def get_camera_settings():
        with sqlite3.connect('PyDVR.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ip, login, password FROM camera_settings ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            return result

    @staticmethod
    def insert_recording_settings(destination, record_length, auto_delete, auto_delete_days, enable_record):
        with sqlite3.connect('PyDVR.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO recording_settings (id, destination, record_length, auto_delete, auto_delete_days, enable_record)
                VALUES ((SELECT id FROM recording_settings LIMIT 1), ?, ?, ?, ?, ?)
            ''', (destination, record_length, auto_delete, auto_delete_days, enable_record))
            conn.commit()

    @staticmethod
    def get_recording_settings():
        with sqlite3.connect('PyDVR.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT destination, record_length, auto_delete, auto_delete_days, enable_record FROM recording_settings ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            return result
import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QAction, QMessageBox, QSpinBox, QCheckBox, QFileDialog
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import cv2
from database import Database
import logging
import os
import datetime

class VideoThread(QThread):
    '''Поток для обработки видеопотока и передачи кадров в основной поток'''
    frame_update_signal = pyqtSignal(object)
    '''Сигнал для передачи обновлений кадра в основной поток'''
    reconnect_required_signal = pyqtSignal()
    '''Сигнал для указания на необходимость реконнекта'''

    def __init__(self, parent=None):
        '''Инициализация объекта VideoThread'''
        super().__init__(parent)
        self.cap = None
        self.running = False
        self.reconnecting = False

    def run(self):
        '''Основной метод потока, обрабатывающий видеопоток'''
        try:
            while self.running:
                ret, frame = self.cap.read()
                if ret:
                    self.frame_update_signal.emit(frame)
                else:
                    self.handle_error("Failed to read frame")
        except Exception as e:
            self.handle_error(f"Error in VideoThread: {str(e)}")

    def handle_error(self, error_text):
        '''Обработка ошибок и инициация процесса реконнекта'''
        logging.error(error_text)
        if not self.reconnecting:
            self.reconnecting = True
            print('Reconnect initiated')
            self.reconnect_required_signal.emit()

    def disconnect(self):
        '''Остановка потока и освобождение ресурсов захвата видео'''
        self.running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.wait()

    def reconnect(self):
        '''Процесс реконнекта'''
        if self.reconnecting:
            logging.warning("Reconnecting to the video stream...")
            self.disconnect()
            time.sleep(5)
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            self.frame_update_signal.emit(None)
            self.connect_to_camera(*self.current_settings)
            self.reconnecting = False

    def connect_to_camera(self, ip, login, password):
        '''Подключение камеры, выполнение в цикле с повторными попытками при неудаче'''
        while True:
            try:
                self.cap = cv2.VideoCapture(f"rtsp://{login}:{password}@{ip}:554/onvif1")

                if self.cap.isOpened():
                    self.running = True
                    self.current_settings = (ip, login, password)
                    self.start()
                else:
                    self.reconnect_required_signal.emit()
                break
            except Exception as e:
                self.handle_error(f"Error connecting to the camera: {str(e)}")
                time.sleep(10)

    def start_video_stream(self, ip, login, password):
        '''Запуск видеопотока'''
        try:
            self.cap = cv2.VideoCapture(f"rtsp://{login}:{password}@{ip}:554/onvif1")

            if self.cap.isOpened():
                self.running = True
                self.current_settings = (ip, login, password)
                self.start()
            else:
                self.reconnect_required_signal.emit()
        except Exception as e:
            logging.error(f"Error starting video stream: {str(e)}")

    def stop_video_stream(self):
        '''Остановка видеопотока'''
        self.running = False
        self.wait()

class CameraSettingsDialog(QMainWindow):
    '''Диалоговое окно для настроек камеры'''
    def __init__(self, video_thread, parent=None):
        '''Инициализация диалогового окна'''
        super().__init__(parent)
        self.video_thread = video_thread
        
        self.setWindowTitle("Настройки камеры")
        self.setGeometry(100, 100, 500, 300)
        self.setFixedSize(300, 200)
        
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout()
        
        self.setup_camera_tab()
        
        self.central_widget.setLayout(self.main_layout)
        
        icon = QIcon('icons/settings_icon.ico')
        self.setWindowIcon(icon)

    def setup_camera_tab(self):
        '''Настройка внешнего вида вкладки с настройками камеры'''
        self.ip_label = QLabel("IP-адрес:")
        self.ip_edit = QLineEdit()
        self.login_label = QLabel("Логин:")
        self.login_edit = QLineEdit()
        self.password_label = QLabel("Пароль:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        self.connect_button = QPushButton("Подключиться", self)
        self.connect_button.clicked.connect(self.connect_to_camera)
        
        self.main_layout.addWidget(self.ip_label)
        self.main_layout.addWidget(self.ip_edit)
        self.main_layout.addWidget(self.login_label)
        self.main_layout.addWidget(self.login_edit)
        self.main_layout.addWidget(self.password_label)
        self.main_layout.addWidget(self.password_edit)
        self.main_layout.addWidget(self.connect_button)

    def connect_to_camera(self):
        '''Метод для подключения камеры по указанным параметрам'''
        try:
            ip = self.ip_edit.text()
            login = self.login_edit.text()
            password = self.password_edit.text()
            
            if not ip or not login or not password:
                QMessageBox.warning(self, "Предупреждение", "Введите IP, логин и пароль.")
                return

            self.video_thread.start_video_stream(ip, login, password)
            self.hide()
        except Exception as e:
            logging.error(f"Unexpected error connecting to the camera: {str(e)}")
            self.video_thread.reconnect()

class RecordingSettingsDialog(QMainWindow):
    '''Диалоговое окно для настроек записи видео'''
    def __init__(self, parent=None):
        '''Инициализация диалогового окна'''
        super().__init__(parent)

        self.setWindowTitle("Настройки записи")
        self.setGeometry(100, 100, 500, 300)
        self.setFixedSize(300, 300)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout()

        self.setup_recording_tab()

        self.central_widget.setLayout(self.main_layout)

        self.load_recording_settings()
        icon = QIcon('icons/settings_icon.ico')
        self.setWindowIcon(icon)

    def setup_recording_tab(self):
        '''Настройка внешнего вида вкладки с настройками записи видео'''
        self.destination_label = QLabel("Место хранения:")
        self.destination_edit = QLineEdit()
        self.browse_button = QPushButton("Обзор", self)
        self.browse_button.clicked.connect(self.browse_destination)

        self.record_length_label = QLabel("Длительность видео (минуты):")
        self.record_length_spinbox = QSpinBox()
        self.record_length_spinbox.setMinimum(1)
        self.record_length_spinbox.setMaximum(600)

        self.auto_delete_checkbox = QCheckBox("Включить автоматическое удаление")
        self.auto_delete_days_label = QLabel("Автоматическое удаление через (дни):")
        self.auto_delete_days_spinbox = QSpinBox()
        self.auto_delete_days_spinbox.setMinimum(1)
        self.auto_delete_days_spinbox.setMaximum(365)

        self.enable_record_checkbox = QCheckBox("Включить запись")

        self.apply_button = QPushButton("Применить", self)
        self.apply_button.clicked.connect(self.apply_recording_settings)

        self.main_layout.addWidget(self.destination_label)
        self.main_layout.addWidget(self.destination_edit)
        self.main_layout.addWidget(self.browse_button)
        self.main_layout.addWidget(self.record_length_label)
        self.main_layout.addWidget(self.record_length_spinbox)
        self.main_layout.addWidget(self.enable_record_checkbox)        
        self.main_layout.addWidget(self.auto_delete_days_label)
        self.main_layout.addWidget(self.auto_delete_days_spinbox)
        self.main_layout.addWidget(self.auto_delete_checkbox)
        self.main_layout.addWidget(self.apply_button)

    def browse_destination(self):
        '''Метод для выбора папки для сохранения записей'''
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
        if folder_path:
            folder_path = folder_path.replace("/", "\\")  
            self.destination_edit.setText(folder_path)

    def apply_recording_settings(self):
        '''Метод для применения настроек записи'''
        try:
            destination = self.destination_edit.text()

            if not os.path.exists(destination):
                QMessageBox.warning(self, "Ошибка", "Путь не существует или программа не имеет доступа.")
                return

            record_length = self.record_length_spinbox.value()
            auto_delete = self.auto_delete_checkbox.isChecked()
            auto_delete_days = self.auto_delete_days_spinbox.value()
            enable_record = self.enable_record_checkbox.isChecked()

            Database.insert_recording_settings(destination, record_length, auto_delete, auto_delete_days, enable_record)

            QMessageBox.information(self, "Успешно!", "Настройки записи применены.")
            self.close()
        except Exception as e:
            logging.error(f"Ошибка сохранения настроек: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")

    def load_recording_settings(self):
        '''Метод для загрузки текущих настроек записи'''
        try:
            destination, record_length, auto_delete, auto_delete_days, enable_record = Database.get_recording_settings()

            self.destination_edit.setText(destination)
            self.record_length_spinbox.setValue(record_length)
            self.auto_delete_checkbox.setChecked(bool(auto_delete))
            self.auto_delete_days_spinbox.setValue(auto_delete_days)
            self.enable_record_checkbox.setChecked(bool(enable_record))
        except Exception as e:
            logging.error(f"Ошибка загрузки настроек записи: {str(e)}")

class MainApplication(QMainWindow):
    '''Главное приложение'''

    def __init__(self):
        '''Инициализация главного окна приложения'''
        super().__init__()

        try:
            os.makedirs("C:\\RecVid")
        except:
            pass

        icon = QIcon('icons/main_icon.ico')
        self.setWindowIcon(icon)

        self.setWindowTitle("PyDVRforIPCam")
        self.setFixedSize(1200, 697)
        self.setGeometry(100, 100, 1200, 750)

        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")

        camera_settings_action = QAction("Настройки камеры", self)
        camera_settings_action.triggered.connect(self.show_camera_settings_dialog)
        file_menu.addAction(camera_settings_action)

        recording_settings_action = QAction("Настройки записи", self)
        recording_settings_action.triggered.connect(self.show_recording_settings_dialog)
        file_menu.addAction(recording_settings_action)

        self.video_thread = VideoThread(self)
        self.video_thread.frame_update_signal.connect(self.update_video_frame)
        self.video_thread.reconnect_required_signal.connect(self.handle_reconnect_required)
        self.cap = None

        self.camera_settings_dialog = CameraSettingsDialog(self.video_thread, self)
        self.recording_settings_dialog = RecordingSettingsDialog(self)

        self.video_widget = QLabel(self)
        self.video_widget.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.video_widget)

        current_settings = Database.get_camera_settings()
        if current_settings:
            ip, login, password = current_settings
            self.start_video_stream(ip, login, password)
        else:
            ip, login, password = "", "", ""

        self.camera_settings_dialog.ip_edit.setText(ip)
        self.camera_settings_dialog.login_edit.setText(login)
        self.camera_settings_dialog.password_edit.setText(password)

        self.recording_settings = Database.get_recording_settings()

    def show_camera_settings_dialog(self):
        '''Отображение диалога настроек камеры'''
        self.camera_settings_dialog.show()
        self.recording_settings_dialog.hide()

    def show_recording_settings_dialog(self):
        '''Отображение диалога настроек записи'''
        self.recording_settings_dialog.show()
        self.camera_settings_dialog.hide()

    def start_video_stream(self, ip, login, password):
        '''Запуск видеопотока'''
        try:
            self.video_thread.start_video_stream(ip, login, password)
        except Exception as e:
            logging.error(f"Error starting video stream: {str(e)}")
            self.handle_video_thread_error(str(e))  # Обработка ошибки

    def update_video_frame(self, frame):
        '''Обновление кадра на виджете'''
        if frame is not None:
            self.update_frame(frame)
            self.record_video(frame)

    def update_frame(self, frame):
        '''Обновление виджета с кадром'''
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = frame.shape

        aspect_ratio = w / h

        new_width = min(self.video_widget.width(), int(self.video_widget.height() * aspect_ratio))
        new_height = min(self.video_widget.height(), int(self.video_widget.width() / aspect_ratio))

        scaled_frame = cv2.resize(frame, (new_width, new_height))

        bytes_per_line = ch * new_width

        img = QImage(scaled_frame.data, new_width, new_height, bytes_per_line, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(img)

        self.video_widget.setPixmap(pixmap)

    def record_video(self, frame):
        '''Запись видео'''
        try:
            if True:
                destination, record_length, auto_delete, auto_delete_days, enable_record = Database.get_recording_settings()
                width = 1920
                height = 1080

                if enable_record:
                    current_time = datetime.datetime.now()
                    elapsed_time = current_time - self.start_time if hasattr(self, 'start_time') else datetime.timedelta(0)

                    if not hasattr(self, 'out') or elapsed_time.total_seconds() >= 60 * record_length or self.out is None:
                        if hasattr(self, 'out') and self.out:
                            self.out.release()

                        file_pattern = os.path.join(destination, '%d.%m.%Y_%H.%M.%S.avi')
                        self.out = cv2.VideoWriter(current_time.strftime(file_pattern), cv2.VideoWriter_fourcc(*'XVID'), 20.0, (int(width), int(height)))
                        self.start_time = datetime.datetime.now()

                    self.out.write(frame)
                else:
                    self.out = None

                if auto_delete:
                    self.delete_old_videos(destination, auto_delete_days)
        except Exception as e:
            logging.error(f"Ошибка записи видео: {str(e)}")

    def delete_old_videos(self, folder, days):
        '''Удаление старых видеофайлов'''
        try:
            current_time = datetime.datetime.now()

            for file_name in os.listdir(folder):
                file_path = os.path.join(folder, file_name)

                file_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))

                if (current_time - file_time).days >= days:
                    os.remove(file_path)
        except Exception as e:
            logging.error(f"Ошибка удаления старых видео: {str(e)}")

    def handle_video_thread_error(self, error_text):
        '''Обработка ошибки видеопотока'''
        logging.error(f"Error in VideoThread: {error_text}")
        self.video_thread.reconnect()

    def handle_reconnect_required(self):
        '''Обработка запроса на реконнект видеопотока'''
        self.video_thread.reconnect()

if __name__ == '__main__':
    '''Запуск приложения'''
    app = QApplication(sys.argv)
    main_app = MainApplication()
    main_app.show()
    sys.exit(app.exec_())
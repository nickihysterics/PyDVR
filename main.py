import sys
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QAction, QSizePolicy, QMessageBox, QSpinBox, QCheckBox, QFileDialog
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter
from PyQt5.QtCore import Qt, QTimer
import cv2
from database import Database
import logging
import os
import datetime
#Test
Database.start_database()

class CameraSettingsDialog(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Настройки Камеры")
        self.setGeometry(100, 100, 500, 300)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout()

        self.setup_camera_tab()

        self.central_widget.setLayout(self.main_layout)

    def setup_camera_tab(self):
        self.ip_label = QLabel("IP-адрес:")
        self.ip_edit = QLineEdit()
        self.login_label = QLabel("Логин:")
        self.login_edit = QLineEdit()
        self.password_label = QLabel("Пароль:")
        self.password_edit = QLineEdit()

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
        ip = self.ip_edit.text()
        login = self.login_edit.text()
        password = self.password_edit.text()

        try:
            Database.insert_camera_settings(ip, login, password)
            self.close()
            main_app.start_video_stream(ip, login, password)
        except Exception as e:
            logging.error(f"Error connecting to the camera: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

class RecordingSettingsDialog(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Настройки Записи")
        self.setGeometry(100, 100, 500, 300)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout()

        self.setup_recording_tab()

        self.central_widget.setLayout(self.main_layout)

        self.load_recording_settings()

    def setup_recording_tab(self):
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
        self.main_layout.addWidget(self.auto_delete_checkbox)
        self.main_layout.addWidget(self.auto_delete_days_label)
        self.main_layout.addWidget(self.auto_delete_days_spinbox)
        self.main_layout.addWidget(self.enable_record_checkbox)
        self.main_layout.addWidget(self.apply_button)

    def browse_destination(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения", options=options)
        if folder_path:
            self.destination_edit.setText(folder_path)

    def apply_recording_settings(self):
        try:
            destination = self.destination_edit.text()
            record_length = self.record_length_spinbox.value()
            auto_delete = self.auto_delete_checkbox.isChecked()
            auto_delete_days = self.auto_delete_days_spinbox.value()
            enable_record = self.enable_record_checkbox.isChecked()

            Database.insert_recording_settings(destination, record_length, auto_delete, auto_delete_days, enable_record)
            QMessageBox.information(self, "Success", "Recording settings applied successfully.")
        except Exception as e:
            logging.error(f"Error applying recording settings: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def load_recording_settings(self):
        try:
            destination, record_length, auto_delete, auto_delete_days, enable_record = Database.get_recording_settings()
            self.destination_edit.setText(destination)
            self.record_length_spinbox.setValue(record_length)
            self.auto_delete_checkbox.setChecked(bool(auto_delete))
            self.auto_delete_days_spinbox.setValue(auto_delete_days)
            self.enable_record_checkbox.setChecked(bool(enable_record))
        except Exception as e:
            logging.error(f"Error loading recording settings: {str(e)}")

class MainApplication(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Приложение настроек камеры PyQT5")
        self.setFixedSize(1200, 750)
        self.setGeometry(100, 100, 1200, 750)

        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")

        camera_settings_action = QAction("Настройки Камеры", self)
        camera_settings_action.triggered.connect(self.show_camera_settings_dialog)
        file_menu.addAction(camera_settings_action)

        recording_settings_action = QAction("Настройки Записи", self)
        recording_settings_action.triggered.connect(self.show_recording_settings_dialog)
        file_menu.addAction(recording_settings_action)

        self.camera_settings_dialog = CameraSettingsDialog(self)
        self.recording_settings_dialog = RecordingSettingsDialog(self)

        self.video_widget = QLabel(self)
        self.video_widget.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.video_widget)

        self.video_timer = QTimer(self)
        self.video_timer.timeout.connect(self.update_video_frame)
        self.cap = None

        current_settings = Database.get_camera_settings()
        if current_settings:
            ip, login, password = current_settings
            self.start_video_stream(ip, login, password)  # автоматическое подключение

        self.camera_settings_dialog.ip_edit.setText(ip)
        self.camera_settings_dialog.login_edit.setText(login)
        self.camera_settings_dialog.password_edit.setText(password)

        self.recording_settings = Database.get_recording_settings()

    def show_camera_settings_dialog(self):
        self.camera_settings_dialog.show()
        self.recording_settings_dialog.hide()

    def show_recording_settings_dialog(self):
        self.recording_settings_dialog.show()
        self.camera_settings_dialog.hide()

    def start_video_stream(self, ip, login, password):
        try:
            self.cap = cv2.VideoCapture(f"rtsp://{login}:{password}@{ip}:554/onvif1")
            if self.cap.isOpened():
                self.video_timer.start(33)
            else:
                QMessageBox.warning(self, "Ошибка подключения", "Не удалось подключиться к камере. Проверьте введенные данные.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")

    def update_video_frame(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.update_frame(frame)
                self.record_video(frame)

    def update_frame(self, frame):
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
        try:
            if self.cap is not None and self.cap.isOpened():
                destination, record_length, auto_delete, auto_delete_days, enable_record = self.recording_settings

                if enable_record:
                    current_time = datetime.datetime.now()
                    elapsed_time = current_time - self.start_time if hasattr(self, 'start_time') else datetime.timedelta(0)

                    if not hasattr(self, 'out') or elapsed_time.total_seconds() >= 60 * record_length:
                        if hasattr(self, 'out'):
                            self.out.release()

                        file_pattern = os.path.join(destination, '%d.%m.%Y-%H.%M.avi')
                        self.out = cv2.VideoWriter(current_time.strftime(file_pattern), cv2.VideoWriter_fourcc(*'XVID'), 20.0, (1920, 1080))
                        self.start_time = datetime.datetime.now()

                    self.out.write(frame)

                    if auto_delete:
                        self.delete_old_videos(destination, auto_delete_days)
        except Exception as e:
            logging.error(f"Error recording video: {str(e)}")


    def delete_old_videos(self, folder, days):
        try:
            current_time = datetime.datetime.now()
            for file_name in os.listdir(folder):
                file_path = os.path.join(folder, file_name)
                file_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                if (current_time - file_time).days >= days:
                    os.remove(file_path)
        except Exception as e:
            logging.error(f"Error deleting old videos: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_app = MainApplication()
    main_app.show()
    sys.exit(app.exec_())

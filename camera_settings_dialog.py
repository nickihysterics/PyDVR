import logging
import cv2
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox, QCheckBox
)
from PyQt5.QtCore import pyqtSignal
from database import Database  # Подключаем модуль работы с базой данных

class CameraSettingsDialog(QMainWindow):
    camera_connected_signal = pyqtSignal()

    def __init__(self, video_thread, parent=None):
        super().__init__(parent)
        self.video_thread = video_thread
        self.setWindowTitle("Настройки камеры")
        self.setFixedSize(400, 300)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout()

        # Метка и выпадающий список для выбора камеры
        self.label = QLabel("Выберите источник камеры:", self)
        self.main_layout.addWidget(self.label)

        self.source_selector = QComboBox(self)
        self.main_layout.addWidget(self.source_selector)

        # Чекбокс для выбора "Отзеркалить картинку"
        self.mirror_checkbox = QCheckBox("Отзеркалить картинку", self)
        self.main_layout.addWidget(self.mirror_checkbox)

        # Кнопка для подключения к выбранному источнику
        self.connect_button = QPushButton("Подключиться", self)
        self.connect_button.clicked.connect(self.connect_to_selected_camera)
        self.main_layout.addWidget(self.connect_button)

        self.central_widget.setLayout(self.main_layout)

        self.populate_camera_sources()
        self.load_settings()  # Загружаем сохраненные настройки

        self.camera_connected_signal.connect(self.hide_window)

    def populate_camera_sources(self):
        """ Проверяет наличие доступных камер и заполняет выпадающий список. """
        self.source_selector.clear()
        available_cameras = []
        for index in range(10):  # Пробуем проверять до 10 камер
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                available_cameras.append(index)
                self.source_selector.addItem(f"Камера {index}", index)
                cap.release()

        if not available_cameras:
            self.source_selector.addItem("Камеры не найдены", -1)
            self.connect_button.setDisabled(True)
        else:
            self.connect_button.setDisabled(False)

    def load_settings(self):
        """ Загружает настройки камеры из базы данных через модуль Database. """
        settings = Database.get_camera_settings()
        if settings:
            camera_index, mirror = settings
            index = self.source_selector.findData(camera_index)
            if index != -1:
                self.source_selector.setCurrentIndex(index)
            self.mirror_checkbox.setChecked(bool(mirror))

    def save_settings(self, camera_index, mirror):
        """ Сохраняет настройки камеры через модуль Database. """
        Database.update_camera_settings(camera_index, mirror)

    def connect_to_selected_camera(self):
        """ Подключается к выбранному источнику камеры и сохраняет настройки в БД. """
        selected_index = self.source_selector.currentData()
        if selected_index == -1:
            QMessageBox.warning(self, "Ошибка", "Нет доступных камер для подключения.")
            return

        mirror_enabled = self.mirror_checkbox.isChecked()

        try:
            if self.video_thread.running:
                self.video_thread.stop_video_stream()

            # Запуск видеопотока с выбранным индексом камеры и флагом отзеркаливания
            self.video_thread.start_video_stream(selected_index, mirror=mirror_enabled)
            self.save_settings(selected_index, mirror_enabled)  # Сохранить настройки в БД
            logging.info(f"Подключение к камере {selected_index} успешно.")
            self.camera_connected_signal.emit()
        except Exception as e:
            logging.error(f"Ошибка при подключении к камере {selected_index}: {str(e)}")
            self.video_thread.reconnect()
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться к камере {selected_index}: {str(e)}")

    def hide_window(self):
        """ Скрывает окно после успешного подключения к камере. """
        logging.info("Скрываю окно настроек камеры...")
        QMessageBox.information(self, "Успешно", "Камера подключена и настройки сохранены.")
        self.hide()

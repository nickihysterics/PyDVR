import logging
import cv2
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox
from PyQt5.QtCore import pyqtSignal, QTimer

class CameraSettingsDialog(QMainWindow):
    # Сигнал, который будет сообщать о успешном подключении
    camera_connected_signal = pyqtSignal()

    def __init__(self, video_thread, parent=None):
        """
        Диалоговое окно для управления настройками камеры.
        
        Параметры:
        - video_thread: ссылка на поток видео (VideoThread) для управления видеопотоком.
        - parent: родительский элемент окна (обычно это главное окно приложения).
        """
        super().__init__(parent)
        self.video_thread = video_thread
        self.setWindowTitle("Настройки камеры")
        self.setFixedSize(400, 300)

        # Центральный виджет и основной макет
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout()

        # Метка для описания выбора источника
        self.label = QLabel("Выберите источник камеры:", self)
        self.main_layout.addWidget(self.label)

        # Выпадающий список для выбора источника камеры
        self.source_selector = QComboBox(self)
        self.main_layout.addWidget(self.source_selector)

        # Кнопка для подключения к выбранному источнику
        self.connect_button = QPushButton("Подключиться", self)
        self.connect_button.clicked.connect(self.connect_to_selected_camera)
        self.main_layout.addWidget(self.connect_button)

        # Устанавливаем основной макет для центрального виджета
        self.central_widget.setLayout(self.main_layout)

        # Заполняем список доступных камер
        self.populate_camera_sources()

        # Подключаем сигнал, который будет скрывать окно после подключения
        self.camera_connected_signal.connect(self.hide_window)

    def populate_camera_sources(self):
        """
        Проверяет наличие доступных камер и заполняет выпадающий список.
        """
        self.source_selector.clear()
        available_cameras = []
        for index in range(5):  # Проверяем первые 5 индексов камер
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

    def connect_to_selected_camera(self):
        """
        Подключается к выбранному источнику камеры.
        Если соединение успешно, окно скрывается.
        Если нет, логирует ошибку.
        """
        selected_index = self.source_selector.currentData()
        if selected_index == -1:
            QMessageBox.warning(self, "Ошибка", "Нет доступных камер для подключения.")
            return
        
        try:
            # Останавливаем текущий поток, если он запущен
            if self.video_thread.running:
                self.video_thread.stop_video_stream()

            # Запускаем новый поток с выбранным индексом камеры
            self.video_thread.start_video_stream(selected_index)

            # Используем сигнал, чтобы скрыть окно после подключения
            logging.info(f"Подключение к камере {selected_index} успешно.")
            self.camera_connected_signal.emit()  # Здесь мы отправляем сигнал

        except Exception as e:
            logging.error(f"Ошибка при подключении к камере {selected_index}: {str(e)}")
            self.video_thread.reconnect()

    def hide_window(self):
        """
        Скрывает окно после успешного подключения к камере.
        """
        logging.info("Скрываю окно настроек камеры...")
        self.hide()  # Скрытие окна после подключения

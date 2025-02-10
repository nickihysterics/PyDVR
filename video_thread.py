import time                                   # Для измерения времени записи
import datetime                               # Для работы с датой и временем (форматирование имени файла)
import logging                                # Для логирования ошибок и событий
import cv2                                    # OpenCV для работы с видеопотоком
from PyQt5.QtCore import QThread, pyqtSignal  # QThread для работы в отдельном потоке, pyqtSignal для сигналов

from database import Database

class VideoThread(QThread):
    frame_update_signal = pyqtSignal(object)
    reconnect_required_signal = pyqtSignal()

    def __init__(self, parent=None):
        """ Инициализация видеопотока с настройками из базы данных PyDVR.db. """
        super().__init__(parent)
        self.cap = None
        self.running = False
        self.writer = None

        # Получаем настройки записи
        recording_settings = Database.get_recording_settings()
        if recording_settings:
            self.video_file_path = recording_settings[0]
            self.record_length = recording_settings[1]
            self.auto_delete = recording_settings[2]
            self.auto_delete_days = recording_settings[3]
            self.enable_record = recording_settings[4]

        # Получаем настройки камеры (camera_index и mirror)
        camera_settings = Database.get_camera_settings()
        if camera_settings:
            self.camera_index = camera_settings[0]
            self.mirror_video = camera_settings[1]  # Флаг зеркалирования видео

    def run(self):
        """ Основной метод потока для считывания кадров и записи видео. """
        try:
            self.start_time = time.time()
            while self.running:
                ret, frame = self.cap.read()
                if ret:
                    if self.mirror_video:  # Проверяем флаг зеркалирования
                        frame = cv2.flip(frame, 1)  # Зеркалируем кадр по горизонтали

                    self.frame_update_signal.emit(frame)  # Отправляем кадр для обновления интерфейса

                    if self.writer:
                        self.writer.write(frame)  # Сохраняем кадр в файл

                    if time.time() - self.start_time >= self.record_length * 60:  # Проверка времени записи
                        self.stop_video_stream()
                        self.start_video_stream()
                else:
                    self.handle_error("Failed to read frame")
        except Exception as e:
            self.handle_error(f"Error in VideoThread: {str(e)}")

    def start_video_stream(self):
        """ Запуск видеопотока и настройка параметров записи. """
        try:
            self.cap = cv2.VideoCapture(self.camera_index)  # Используем camera_index из настроек камеры
            if self.cap.isOpened():
                frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fourcc = cv2.VideoWriter_fourcc(*'XVID')

                current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                self.video_file_path = f'{self.video_file_path}\\{current_time}.avi'

                self.writer = cv2.VideoWriter(self.video_file_path, fourcc, 20.0, (frame_width, frame_height))
                self.running = True
                self.start_time = time.time()
                self.start()
            else:
                self.reconnect_required_signal.emit()
        except Exception as e:
            logging.error(f"Error starting video stream: {str(e)}")

    def stop_video_stream(self):
        """ Останавливает видеопоток и освобождает ресурсы. """
        self.running = False
        if self.writer:
            self.writer.release()
        if self.cap is not None:
            self.cap.release()
        self.wait()

    def handle_error(self, error_text):
        """ Обработка ошибок и логирование. """
        logging.error(error_text)
        self.reconnect_required_signal.emit()

    def reconnect(self):
        """ Переподключение камеры после ошибки. """
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(self.camera_index)  # Повторное подключение с использованием camera_index
        self.running = True
        self.start()
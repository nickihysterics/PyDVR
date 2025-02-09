import time                                   # Для измерения времени записи
import datetime                               # Для работы с датой и временем (форматирование имени файла)
import logging                                # Для логирования ошибок и событий
import cv2                                    # OpenCV для работы с видеопотоком
from PyQt5.QtCore import QThread, pyqtSignal  # QThread для работы в отдельном потоке, pyqtSignal для сигналов

from database import Database

class VideoThread(QThread):
    """
    Класс для работы с видеопотоком в отдельном потоке.
    Обрабатывает видеозапись с камеры, сохраняет видео в файл и отправляет сигналы обновления кадров.
    """
    frame_update_signal = pyqtSignal(object)  # Сигнал для передачи нового кадра (тип object — любой объект)
    reconnect_required_signal = pyqtSignal()  # Сигнал для уведомления о необходимости переподключения камеры

    def __init__(self, parent=None):
        """ Инициализация видеопотока с настройками из базы данных PyDVR.db. """
        super().__init__(parent)
        self.cap = None
        self.running = False
        self.writer = None

        # Получаем настройки записи из базы данных
        settings = Database.get_recording_settings()
        if settings:
            self.video_file_path = settings[0]  # Путь для сохранения записанного видео
            self.record_length = settings[1]    # Длительность записи в минутах
            self.auto_delete = settings[2]      # Флаг автоматического удаления
            self.auto_delete_days = settings[3] # Количество дней для автоудаления
            self.enable_record = settings[4]    # Флаг включения записи

    def run(self):
        """
        Основной метод потока. Выполняется при запуске потока.
        Считывает кадры из видеопотока и сохраняет их в файл.
        """
        try:
            self.start_time = time.time()  # Время начала записи
            while self.running:  # Основной цикл записи
                ret, frame = self.cap.read()  # Считываем кадр с камеры
                if ret:
                    self.frame_update_signal.emit(frame)  # Отправляем кадр через сигнал для обновления интерфейса
                    if self.writer:  # Если запись активна, сохраняем кадр в файл
                        self.writer.write(frame)
                    
                    # Проверяем, истекло ли время записи
                    if time.time() - self.start_time >= self.record_length:
                        self.stop_video_stream()  # Останавливаем текущую запись
                        self.start_video_stream()  # Перезапускаем запись с новым файлом
                else:
                    self.handle_error("Failed to read frame")  # Обработка ошибки при чтении кадра
        except Exception as e:
            self.handle_error(f"Error in VideoThread: {str(e)}")  # Логируем любые исключения

    def start_video_stream(self):
        """
        Запуск видеопотока и настройка параметров записи.
        Создает новый файл для записи и запускает поток.
        """
        try:
            self.cap = cv2.VideoCapture(0)  # Подключаемся к камере (0 — первая доступная камера)
            if self.cap.isOpened():  # Проверяем, успешно ли подключились
                frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # Ширина кадра
                frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # Высота кадра
                fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Кодек для записи видео (XVID)
                
                # Формируем уникальное имя файла на основе текущего времени
                current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                # self.video_file_path = f'{self.video_file_path}\\{current_time}.avi'
                
                # Создаем объект VideoWriter для записи видео
                self.writer = cv2.VideoWriter(self.video_file_path, fourcc, 20.0, (frame_width, frame_height))
                self.running = True  # Устанавливаем флаг, что поток работает
                self.start_time = time.time()  # Обновляем время начала записи
                self.start()  # Запускаем метод run() в новом потоке
            else:
                self.reconnect_required_signal.emit()  # Если не удалось подключиться, отправляем сигнал для реконнекта
        except Exception as e:
            logging.error(f"Error starting video stream: {str(e)}")  # Логируем ошибки

    def stop_video_stream(self):
        """
        Останавливает видеопоток и освобождает ресурсы.
        Закрывает файл записи и завершает поток.
        """
        self.running = False  # Останавливаем цикл в методе run()
        if self.writer:
            self.writer.release()  # Закрываем файл записи
        if self.cap is not None:
            self.cap.release()  # Освобождаем камеру
        self.wait()  # Ожидаем завершения потока

    def handle_error(self, error_text):
        """
        Обработка ошибок и логирование.
        Отправляет сигнал о необходимости переподключения камеры.
        
        :param error_text: Текст ошибки для записи в лог
        """
        logging.error(error_text)  # Записываем ошибку в лог
        self.reconnect_required_signal.emit()  # Отправляем сигнал для реконнекта

    def reconnect(self):
        """
        Переподключение камеры после ошибки.
        Освобождает текущий видеопоток и повторно подключается.
        """
        if self.cap is not None:
            self.cap.release()  # Освобождаем текущий объект захвата
        self.cap = cv2.VideoCapture(0)  # Повторное подключение к камере
        self.running = True  # Устанавливаем флаг, что поток снова работает
        self.start()  # Перезапускаем метод run() в новом потоке
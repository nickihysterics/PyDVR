import sys                                                              # Для работы с системными параметрами и завершения приложения
import os                                                               # Для работы с файловой системой (создание папок)
import logging                                                          # Для ведения логов и записи ошибок
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QAction  # Основные виджеты PyQt5
from PyQt5.QtGui import QIcon, QImage, QPixmap                          # Для отображения иконок и изображений
from PyQt5.QtCore import Qt                                             # Для управления атрибутами выравнивания и флагами
from video_thread import VideoThread                                    # Поток обработки видеопотока (вынесен в отдельный модуль)
from camera_settings_dialog import CameraSettingsDialog                 # Окно настроек камеры (в отдельном модуле)
from recording_settings_dialog import RecordingSettingsDialog           # Окно настроек записи (в отдельном модуле)
from database import Database                                           # Модуль для работы с базой данных

Database.start_database()  # Инициализация базы данных

class MainApplication(QMainWindow):
    """
    Основной класс приложения, который создает главное окно и управляет взаимодействием между различными компонентами.
    """
    def __init__(self):
        """Инициализация основного окна приложения и его компонентов."""
        super().__init__()  # Инициализация базового класса QMainWindow
        self.init_ui()      # Метод для настройки интерфейса

        # Создаем экземпляр видеопотока для обработки видеозаписи
        self.video_thread = VideoThread(self)
        self.video_thread.frame_update_signal.connect(self.update_video_frame)               # Сигнал обновления кадра
        self.video_thread.reconnect_required_signal.connect(self.handle_reconnect_required)  # Сигнал необходимости реконнекта

        # Создаем окна для настроек камеры и записи
        self.camera_settings_dialog = CameraSettingsDialog(self.video_thread, self)
        self.recording_settings_dialog = RecordingSettingsDialog(self)

    def init_ui(self):
        """
        Настройка графического интерфейса главного окна.
        Создает меню, иконки и основной виджет для отображения видео.
        """
        # Устанавливаем параметры главного окна
        self.setWindowTitle("PyDVRforWebCam")  # Заголовок окна
        self.setFixedSize(1200, 750)  # Фиксированный размер окна
        self.setGeometry(100, 100, 1200, 750)  # Позиция и размер окна при запуске
        self.setWindowIcon(QIcon('icons/main_icon.ico'))  # Устанавливаем иконку окна

        # Создание меню
        menubar = self.menuBar()  # Создаем менюбар
        file_menu = menubar.addMenu("Файл")  # Добавляем пункт меню "Файл"

        # Добавление действия "Настройки камеры" в меню
        camera_settings_action = QAction("Настройки камеры", self)
        camera_settings_action.triggered.connect(self.show_camera_settings_dialog)  # Привязываем действие к методу
        file_menu.addAction(camera_settings_action)  # Добавляем действие в меню

        # Добавление действия "Настройки записи" в меню
        recording_settings_action = QAction("Настройки записи", self)
        recording_settings_action.triggered.connect(self.show_recording_settings_dialog)  # Привязываем действие к методу
        file_menu.addAction(recording_settings_action)  # Добавляем действие в меню

        # Создание виджета для отображения видеопотока
        self.video_widget = QLabel(self)
        self.video_widget.setAlignment(Qt.AlignCenter)  # Выравнивание по центру
        self.setCentralWidget(self.video_widget)  # Устанавливаем как центральный виджет

    def show_camera_settings_dialog(self):
        """
        Показать окно настроек камеры.
        Скрывает окно настроек записи, чтобы они не перекрывали друг друга.
        """
        self.camera_settings_dialog.show()
        self.recording_settings_dialog.hide()

    def show_recording_settings_dialog(self):
        """
        Показать окно настроек записи.
        Скрывает окно настроек камеры.
        """
        self.recording_settings_dialog.show()
        self.camera_settings_dialog.hide()

    def update_video_frame(self, frame):
        """
        Обновить отображаемый кадр на виджете видео.
        Этот метод вызывается при получении нового кадра от видеопотока.
        
        :param frame: Кадр, полученный из видеопотока (в формате numpy array)
        """
        if frame is not None:
            self.update_frame(frame)  # Вызов вспомогательного метода для обработки и отображения кадра

    def update_frame(self, frame):
        """
        Обработка и отображение кадра на виджете QLabel.
        Преобразует кадр из формата OpenCV в формат, подходящий для QPixmap.
        
        :param frame: Кадр в формате numpy array
        """
        import cv2  # Импортируем OpenCV здесь, чтобы избежать проблем с зависимостями

        # Преобразуем кадр из BGR (формат OpenCV) в RGB (формат QImage)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Получаем размеры кадра
        h, w, ch = frame.shape
        bytes_per_line = ch * w  # Количество байт в строке изображения
        
        # Создаем QImage из данных кадра
        img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Преобразуем QImage в QPixmap и устанавливаем его на QLabel
        pixmap = QPixmap.fromImage(img)
        self.video_widget.setPixmap(pixmap)

    def handle_reconnect_required(self):
        """
        Обработка сигнала необходимости реконнекта.
        Запускает процесс переподключения видеопотока.
        """
        self.video_thread.reconnect()

if __name__ == "__main__":
    """
    Точка входа в приложение.
    Настраиваем логирование, создаем экземпляр QApplication и запускаем главное окно приложения.
    """
    logging.basicConfig(filename="app.log", level=logging.DEBUG)  # Настройка логирования, запись в файл "app.log"

    app = QApplication(sys.argv)  # Создаем экземпляр приложения
    window = MainApplication()  # Создаем главное окно
    window.show()  # Показываем главное окно
    sys.exit(app.exec_())  # Запускаем цикл обработки событий приложения
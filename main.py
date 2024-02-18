import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QAction, QMessageBox, QSpinBox, QCheckBox, QFileDialog
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import cv2
from database import Database
import logging
import os
import datetime

Database.start_database()

class VideoThread(QThread):
    # Сигнал, который будет отправлен при обновлении кадра
    frame_update_signal = pyqtSignal(object)

    def __init__(self, parent=None):
        '''
        Конструктор класса VideoThread.

        Args:
            parent (QObject): Родительский объект (по умолчанию - None).
        '''
        super().__init__(parent)
        # Объект видеозахвата, используемый для чтения видеопотока
        self.cap = None
        # Флаг, указывающий на то, выполняется ли видеопоток в данный момент
        self.running = False

    def run(self):
        '''
        Метод, который выполняется при запуске видеопотока.

        Внутри цикла while проверяется флаг `self.running`, и при его значении True
        происходит чтение кадра из видеозахвата (self.cap.read()).
        
        Если чтение проходит успешно (ret=True), то отправляется сигнал frame_update_signal
        с полученным кадром.

        Если возникает исключение, ошибка логгируется с использованием модуля logging.

        '''
        try:
            while self.running:
                ret, frame = self.cap.read()
                if ret:
                    self.frame_update_signal.emit(frame)
        except Exception as e:
            # Логгирование ошибки, если она произошла внутри видеопотока
            logging.error(f"Error in VideoThread123123: {str(e)}")

    def start_video_stream(self, ip, login, password):
        '''
        Метод для начала воспроизведения видеопотока.

        Args:
            ip (str): IP-адрес камеры.
            login (str): Логин для доступа к камере.
            password (str): Пароль для доступа к камере.
        '''
        try:
            # Создание объекта видеозахвата с использованием RTSP-протокола
            self.cap = cv2.VideoCapture(f"rtsp://{login}:{password}@{ip}:554/onvif1")
            
            # Проверка успешности открытия видеозахвата
            if self.cap.isOpened():
                # Если успешно, установка флага running в True и запуск видеопотока, передает значение настроек камеры в базу данных
                self.running = True
                Database.insert_camera_settings(ip, login, password)
                self.start()
            else:
                # Если открытие не удалось, установка флага running в False,
                # освобождение видеозахвата и отправка сигнала с None для обновления интерфейса
                self.running = False
                self.cap.release()
                self.cap = None
                self.frame_update_signal.emit(None)
                logging.warning("Failed to open video stream.")
        except Exception as e:
            # Логгирование ошибки, если она произошла при открытии видеопотока
            logging.error(f"Error starting video stream: {str(e)}")

    def stop_video_stream(self):
        '''
        Метод для остановки видеопотока.

        Выставляет флаг `self.running` в False и ожидает завершения потока с использованием `self.wait()`.
        '''
        self.running = False
        self.wait()

class CameraSettingsDialog(QMainWindow):
    def __init__(self, parent=None):
        '''
        Создание окна "Настройки камеры".
        
        Args:
            parent: Родительское окно (по умолчанию None).
        '''
        super().__init__(parent)

        # Установка заголовка и размеров окна
        self.setWindowTitle("Настройки камеры")
        self.setGeometry(100, 100, 500, 300)
        self.setFixedSize(300, 200)

        # Создание центрального виджета и установка его в качестве центрального виджета окна
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Создание вертикального компоновщика для центрального виджета
        self.main_layout = QVBoxLayout()

        # Инициализация вкладки с настройками камеры
        self.setup_camera_tab()

        # Установка компоновщика для центрального виджета
        self.central_widget.setLayout(self.main_layout)

        # Установка иконки окна
        icon = QIcon('settings_icon.ico')
        self.setWindowIcon(icon)


    def setup_camera_tab(self):
        '''
        Инициализация дизайна вкладки "Настройки камеры".

        Создает и размещает виджеты интерфейса для ввода IP-адреса, логина, пароля
        и кнопки "Подключиться" на вкладке "Настройки камеры".
        '''
        # Создание виджетов интерфейса
        self.ip_label = QLabel("IP-адрес:")
        self.ip_edit = QLineEdit()
        self.login_label = QLabel("Логин:")
        self.login_edit = QLineEdit()
        self.password_label = QLabel("Пароль:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        # Кнопка "Подключиться" с привязкой метода connect_to_camera при клике
        self.connect_button = QPushButton("Подключиться", self)
        self.connect_button.clicked.connect(self.connect_to_camera)

        # Размещение виджетов на вкладке с использованием вертикального компоновщика
        self.main_layout.addWidget(self.ip_label)
        self.main_layout.addWidget(self.ip_edit)
        self.main_layout.addWidget(self.login_label)
        self.main_layout.addWidget(self.login_edit)
        self.main_layout.addWidget(self.password_label)
        self.main_layout.addWidget(self.password_edit)
        self.main_layout.addWidget(self.connect_button)


    def connect_to_camera(self):
        '''
        Метод для подключения к камере.

        Получает значения IP-адреса, логина и пароля из соответствующих полей ввода,
        а затем вызывает метод start_video_stream главного приложения (main_app) для начала
        видеопотока с использованием заданных параметров. В случае ошибки выводит сообщение об ошибке.
        '''
        # Получение значений IP-адреса, логина и пароля из полей ввода
        ip = self.ip_edit.text()
        login = self.login_edit.text()
        password = self.password_edit.text()

        try:
            # Вызов метода главного приложения для начала видеопотока
            main_app.start_video_stream(ip, login, password)
            # Закрытие окна настроек камеры
            self.close()
        except Exception as e:
            # Вывод сообщения об ошибке в случае неудачного подключения
            logging.error(f"Ошибка подключения к камере: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")


class RecordingSettingsDialog(QMainWindow):
    def __init__(self, parent=None):
        '''
        Инициализация окна "Настройки записи".

        Устанавливает заголовок окна, размеры и иконку. Создает центральный виджет и устанавливает
        его для текущего окна. Инициализирует основной вертикальный макет и настраивает вкладку записи.

        Загружает настройки записи из базы данных и устанавливает их в соответствующих виджетах.

        Args:
            parent: Родительское окно, если оно есть.
        '''
        super().__init__(parent)

        # Установка заголовка, размеров и иконки окна
        self.setWindowTitle("Настройки записи")
        self.setGeometry(100, 100, 500, 300)
        self.setFixedSize(300, 300)

        # Создание центрального виджета и его установка
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Инициализация основного вертикального макета
        self.main_layout = QVBoxLayout()

        # Настройка вкладки записи
        self.setup_recording_tab()

        # Установка макета для центрального виджета
        self.central_widget.setLayout(self.main_layout)

        # Загрузка настроек записи и установка иконки
        self.load_recording_settings()
        icon = QIcon('settings_icon.ico')
        self.setWindowIcon(icon)


    def setup_recording_tab(self):
        '''
        Настройка вкладки "Настройки записи".

        Создает элементы управления для настройки записи, такие как место хранения, длительность видео,
        автоматическое удаление и включение записи. Привязывает соответствующие методы к кнопкам и
        устанавливает их в вертикальный макет.

        '''
        # Создание виджетов для настройки записи
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

        # Добавление виджетов в вертикальный макет
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
        '''
        Действие для кнопки "Обзор".

        Открывает диалоговое окно выбора папки и устанавливает выбранный путь в соответствующее
        поле ввода "Место хранения". Заменяет обратные слеши на прямые.

        '''
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
        if folder_path:
            folder_path = folder_path.replace("/", "\\")  # Замена обратных слешей на прямые
            self.destination_edit.setText(folder_path)

    def apply_recording_settings(self):
        '''
        Применение настроек записи
        '''
        try:
            # Получаем значения из соответствующих элементов пользовательского интерфейса
            destination = self.destination_edit.text()

            # Проверяем, существует ли указанный путь
            if not os.path.exists(destination):
                QMessageBox.warning(self, "Ошибка", "Путь не существует или программа не имеет доступа.")
                return

            record_length = self.record_length_spinbox.value()
            auto_delete = self.auto_delete_checkbox.isChecked()
            auto_delete_days = self.auto_delete_days_spinbox.value()
            enable_record = self.enable_record_checkbox.isChecked()

            # Вставляем настройки записи в базу данных
            Database.insert_recording_settings(destination, record_length, auto_delete, auto_delete_days, enable_record)

            # Выводим информационное окно об успешном применении настроек
            QMessageBox.information(self, "Успешно!", "Настройки записи применены.")
            self.close()
        except Exception as e:
            # Логируем ошибку и выводим критическое окно с ошибкой
            logging.error(f"Ошибка сохранения настроек: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")


    def load_recording_settings(self):
        '''
        Загрузка настроек записи из БД
        '''
        try:
            # Получаем настройки записи из базы данных
            destination, record_length, auto_delete, auto_delete_days, enable_record = Database.get_recording_settings()

            # Устанавливаем значения элементов интерфейса в соответствии с полученными настройками
            self.destination_edit.setText(destination)
            self.record_length_spinbox.setValue(record_length)
            self.auto_delete_checkbox.setChecked(bool(auto_delete))
            self.auto_delete_days_spinbox.setValue(auto_delete_days)
            self.enable_record_checkbox.setChecked(bool(enable_record))
        except Exception as e:
            # Логируем ошибку, если возникает проблема с загрузкой настроек из базы данных
            logging.error(f"Ошибка загрузки настроек записи: {str(e)}")

class MainApplication(QMainWindow):
    def __init__(self):
        super().__init__()

        # Создание директории для сохранения видео, если она не существует
        try:
            os.makedirs("C:\\RecVid")
        except:
            pass

        # Установка иконки главного окна
        icon = QIcon('main_icon.ico')
        self.setWindowIcon(icon)

        # Установка заголовка и размеров главного окна
        self.setWindowTitle("PyDVRforIPCam")
        self.setFixedSize(1200, 750)
        self.setGeometry(100, 100, 1200, 750)

        # Создание меню "Файл"
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")

        # Добавление действия "Настройки камеры" в меню "Файл"
        camera_settings_action = QAction("Настройки камеры", self)
        camera_settings_action.triggered.connect(self.show_camera_settings_dialog)
        file_menu.addAction(camera_settings_action)

        # Добавление действия "Настройки записи" в меню "Файл"
        recording_settings_action = QAction("Настройки записи", self)
        recording_settings_action.triggered.connect(self.show_recording_settings_dialog)
        file_menu.addAction(recording_settings_action)

        # Создание диалоговых окон для настроек камеры и записи
        self.camera_settings_dialog = CameraSettingsDialog(self)
        self.recording_settings_dialog = RecordingSettingsDialog(self)

        # Создание виджета для отображения видео
        self.video_widget = QLabel(self)
        self.video_widget.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.video_widget)

        # Создание потока для обновления видео
        self.video_thread = VideoThread(self)
        self.video_thread.frame_update_signal.connect(self.update_video_frame)
        self.cap = None

        # Получение текущих настроек камеры из базы данных и запуск видеопотока
        current_settings = Database.get_camera_settings()
        if current_settings:
            ip, login, password = current_settings
            self.start_video_stream(ip, login, password)
        else:
            ip, login, password = "", "", ""

        # Установка значений настроек камеры в соответствующие поля диалогового окна
        self.camera_settings_dialog.ip_edit.setText(ip)
        self.camera_settings_dialog.login_edit.setText(login)
        self.camera_settings_dialog.password_edit.setText(password)

        # Получение текущих настроек записи из базы данных
        self.recording_settings = Database.get_recording_settings()


    def show_camera_settings_dialog(self):
        # Отображение диалогового окна настроек камеры
        self.camera_settings_dialog.show()

        # Скрытие диалогового окна настроек записи
        self.recording_settings_dialog.hide()


    def show_recording_settings_dialog(self):
        # Отображение диалогового окна настроек записи
        self.recording_settings_dialog.show()
    
        # Скрытие диалогового окна настроек камеры
        self.camera_settings_dialog.hide()


    def start_video_stream(self, ip:str, login:str, password:str):
        # Запуск видеопотока, передача параметров IP-адреса, логина и пароля
        self.video_thread.start_video_stream(ip, login, password)


    def update_video_frame(self, frame):
        # Если кадр не является None
        if frame is not None:
            # Обновление отображаемого кадра
            self.update_frame(frame)
            # Запись видео, если включена функция записи
            self.record_video(frame)



    def update_frame(self, frame):
        '''
        Обновление фрейма
        '''
        # Преобразование цветового пространства из BGR в RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = frame.shape

        # Расчет соотношения сторон фрейма
        aspect_ratio = w / h
        # Вычисление новых размеров для отображения
        new_width = min(self.video_widget.width(), int(self.video_widget.height() * aspect_ratio))
        new_height = min(self.video_widget.height(), int(self.video_widget.width() / aspect_ratio))

        # Изменение размеров фрейма
        scaled_frame = cv2.resize(frame, (new_width, new_height))

        # Вычисление количества байт на строку изображения
        bytes_per_line = ch * new_width
        # Создание объекта QImage из массива байт
        img = QImage(scaled_frame.data, new_width, new_height, bytes_per_line, QImage.Format_RGB888)
        # Создание QPixmap из QImage
        pixmap = QPixmap.fromImage(img)

        # Установка QPixmap в виджет для отображения
        self.video_widget.setPixmap(pixmap)


    def record_video(self, frame):
        '''
        Запись видео
        '''
        try:
            # Проверка, открыта ли камера и доступна ли запись
            #print(self.cap, self.cap.isOpened())
            if True:
                # Получение текущих настроек записи из базы данных
                destination, record_length, auto_delete, auto_delete_days, enable_record = Database.get_recording_settings()
                width = 1920
                height = 1080

                # Проверка, включена ли запись
                if enable_record:
                    current_time = datetime.datetime.now()
                    elapsed_time = current_time - self.start_time if hasattr(self, 'start_time') else datetime.timedelta(0)

                    # Проверка, нужно ли создавать новый файл для записи
                    if not hasattr(self, 'out') or elapsed_time.total_seconds() >= 60 * record_length or self.out is None:

                        # Закрытие предыдущего файла, если он открыт
                        if hasattr(self, 'out') and self.out:
                            self.out.release()

                        # Формирование имени файла с учетом шаблона времени
                        file_pattern = os.path.join(destination, '%d.%m.%Y_%H.%M.%S.avi')
                        # Создание нового объекта VideoWriter
                        self.out = cv2.VideoWriter(current_time.strftime(file_pattern), cv2.VideoWriter_fourcc(*'XVID'), 20.0, (int(width), int(height)))
                        self.start_time = datetime.datetime.now()

                    # Запись текущего фрейма в файл
                    self.out.write(frame)
                else:
                    # Закрытие VideoWriter, если запись выключена
                    self.out = None

                # Проверка, нужно ли удалять старые видеофайлы
                if auto_delete:
                    self.delete_old_videos(destination, auto_delete_days)
        except Exception as e:
            # Обработка ошибок и логирование
            logging.error(f"Ошибка записи видео: {str(e)}")

    def delete_old_videos(self, folder:str, days:int):
        '''
        Автоматическое удаление старых видео
        '''
        try:
            # Получение текущего времени
            current_time = datetime.datetime.now()

            # Проход по всем файлам в указанной директории
            for file_name in os.listdir(folder):
                file_path = os.path.join(folder, file_name)

                # Получение времени создания файла
                file_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))

                # Проверка, насколько давно файл был создан
                if (current_time - file_time).days >= days:
                    # Удаление файла, если его возраст превышает указанное количество дней
                    os.remove(file_path)
        except Exception as e:
            # Обработка ошибок и логирование
            logging.error(f"Ошибка удаления старых видео: {str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_app = MainApplication()
    main_app.show()
    sys.exit(app.exec_())
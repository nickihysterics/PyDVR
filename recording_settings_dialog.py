from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QCheckBox, QMessageBox, QFileDialog
from PyQt5.QtGui import QIcon, QImage, QPixmap     
import logging
import os
from database import Database

class RecordingSettingsDialog(QMainWindow): 
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
                try:
                    os.makedirs(destination)
                    QMessageBox.information(self, "Информация", f"Папка для записи создана:\n{destination}")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось создать папку для записи:\n{destination}\n{str(e)}")
                    return  # Не сохраняем настройки, если создать папку не удалось

            record_length = self.record_length_spinbox.value() * 60  # Переводим в секунды
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
            self.record_length_spinbox.setValue(record_length // 60)  # Длительность в минутах
            self.auto_delete_checkbox.setChecked(bool(auto_delete))
            self.auto_delete_days_spinbox.setValue(auto_delete_days)
            self.enable_record_checkbox.setChecked(bool(enable_record))
        except Exception as e:
            logging.error(f"Ошибка загрузки настроек записи: {str(e)}")
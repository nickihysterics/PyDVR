# PyDVRforIPCam

PyDVRforIPCam is a simple Python application designed for streaming video from an IP camera and recording it locally. It utilizes the PyQt5 library for the graphical user interface and OpenCV for video processing.

## Features

- **Camera Settings:** Configure IP address, login, and password for connecting to the IP camera.
- **Recording Settings:** Set the destination folder, recording duration, enable automatic deletion of old videos, and enable/disable recording.
- **Video Streaming:** Stream video from the configured IP camera.
- **Video Recording:** Record video with specified settings and automatically delete old videos if enabled.

## Getting Started

### Prerequisites

- Python 3.6 or later
- PyQt5
- OpenCV
- SQLite3

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/your_username/PyDVRforIPCam.git
    ```

2. Install dependencies:

    ```bash
    pip install PyQt5 opencv-python
    ```

3. Run the application:

    ```bash
    cd PyDVRforIPCam
    python main.py
    ```

## Usage

1. Launch the application and configure camera settings via the "Camera Settings" menu option.
2. Configure recording settings via the "Recording Settings" menu option.
3. Start the video stream by clicking the "Connect" button in the camera settings dialog.
4. The main window will display the live video stream.
5. Videos will be recorded based on the specified recording settings.

## Contributing

Contributions are welcome! Please follow the [contribution guidelines](CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the PyQt5 and OpenCV developers for their excellent libraries.

## Troubleshooting

If you encounter any issues or have questions, please [open an issue](https://github.com/your_username/PyDVRforIPCam/issues).

---

# PyDVRforIPCam

PyDVRforIPCam - простое приложение на Python для трансляции видео с IP-камеры и записи его локально. Для создания графического интерфейса используется библиотека PyQt5, а для обработки видео - OpenCV.

## Возможности

- **Настройки камеры:** Конфигурируйте IP-адрес, логин и пароль для подключения к IP-камере.
- **Настройки записи:** Установите папку назначения, длительность записи, включите автоматическое удаление старых видео и включите/отключите запись.
- **Видео-трансляция:** Транслируйте видео с настроенной IP-камеры.
- **Запись видео:** Записывайте видео с заданными настройками и автоматически удаляйте старые видео при необходимости.

## Начало работы

### Необходимые компоненты

- Python 3.6 или более поздняя версия
- PyQt5
- OpenCV
- SQLite3

### Установка

1. Клонируйте репозиторий:

    ```bash
    git clone https://github.com/your_username/PyDVRforIPCam.git
    ```

2. Установите зависимости:

    ```bash
    pip install PyQt5 opencv-python
    ```

3. Запустите приложение:

    ```bash
    cd PyDVRforIPCam
    python main.py
    ```

## Использование

1. Запустите приложение и настройте параметры камеры через меню "Настройки камеры".
2. Настройте параметры записи через меню "Настройки записи".
3. Начните трансляцию видео, нажав кнопку "Подключиться" в диалоговом окне настроек камеры.
4. Основное окно отобразит текущую трансляцию видео.
5. Видео будет записываться в соответствии с указанными настройками записи.

## Содействие

Содействие приветствуется! Пожалуйста, следуйте [руководству по внесению вклада](CONTRIBUTING.md).

## Лицензия

Этот проект распространяется под лицензией MIT - подробности см. в файле [LICENSE](LICENSE).

## Благодарности

Благодарим разработчиков PyQt5 и OpenCV за их отличные библиотеки.

## Устранение неполадок

Если у вас возникнут проблемы или возникнут вопросы, пожалуйста, [откройте задачу](https://github.com/your_username/PyDVRforIPCam/issues).

'''
Приложение "Видеотека фильмов"

Это десктопное приложение для управления личной коллекцией фильмов.
Позволяет хранить информацию о фильмах в базе данных SQLite,
добавлять постеры, искать фильмы и просматривать детальную информацию.

Основные возможности:
- Добавление фильмов с полной информацией
- Загрузка и отображение постеров фильмов
- Редактирование существующих фильмов
- Удаление фильмов с подтверждением
- Поиск по названию фильма
- Фильтрация по жанру
- Просмотр детальной информации в отдельном окне
- Сортировка списка фильмов
- Просмотр статистики коллекции
- Экспорт списка фильмов в CSV
- Импорт данных из внешних источников
- Система рекомендаций фильмов
- Резервное копирование базы данных
'''

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from main_window import MainWindow


def check_requirements():
    # Проверка наличия необходимых компонентов
    required_folders = ['ui', 'posters']
    required_files = [
        'ui/main_window.ui',
        'ui/add_edit_dialog.ui',
        'ui/details_dialog.ui'
    ]
    
    # Создаём папки если их нет
    for folder in required_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Создана папка: {folder}")
    
    # Проверяем наличие UI файлов
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"ОШИБКА: Не найден файл {file_path}")
            return False
    
    return True


def setup_application_style(app):
    # Настройка стиля приложения
    app.setStyle('Fusion')
    
    # Настраиваем палитру цветов
    from PyQt6.QtGui import QPalette, QColor
    palette = QPalette()
    
    # Основные цвета
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))  # Цвет текста в таблице
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(76, 163, 224))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    
    app.setPalette(palette)


def main():
    # Главная функция запуска приложения
    if not check_requirements():
        sys.exit(1)
    
    # Создаём приложение
    app = QApplication(sys.argv)
    
    # Устанавливаем название и версию
    app.setApplicationName("Видеотека фильмов")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("movie-library-pyqt")
    
    # Настраиваем стиль
    setup_application_style(app)
    
    # Создаём и показываем главное окно
    window = MainWindow()
    window.show()
    
    # Запускаем цикл обработки событий
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

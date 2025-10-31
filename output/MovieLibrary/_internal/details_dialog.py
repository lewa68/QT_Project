'''
Модуль диалога детальной информации о фильме.
Отображает полную информацию о фильме с постером.
'''

import os
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from database import Database


class DetailsDialog(QDialog):
    # Диалог для просмотра детальной информации о фильме
    
    def __init__(self, database: Database, movie_id: int, parent=None):
        super().__init__(parent)
        # Загружаем интерфейс из ui файла
        uic.loadUi('ui/details_dialog.ui', self)
        
        self.db = database
        self.movie_id = movie_id
        
        # Загружаем и отображаем данные фильма
        self.load_movie_data()
        
        # Подключаем кнопку закрытия
        self.closeButton.clicked.connect(self.accept)
    
    def load_movie_data(self):
        # Загрузка и отображение информации о фильме
        movie = self.db.get_movie_by_id(self.movie_id)
        
        if not movie:
            QMessageBox.critical(self, "Ошибка", "Фильм не найден в базе данных")
            self.reject()
            return
        
        # Распаковываем данные
        movie_id, title, year, genre, director, rating, duration, description, poster_path = movie
        
        # Устанавливаем заголовок окна
        self.setWindowTitle(f"Информация о фильме: {title}")
        
        # Заполняем текстовые поля
        self.titleLabel.setText(title if title else "Не указано")
        self.yearLabel.setText(str(year) if year else "Не указан")
        self.genreLabel.setText(genre if genre else "Не указан")
        self.directorLabel.setText(director if director else "Не указан")
        self.ratingLabel.setText(f"{rating}/10" if rating else "Не указан")
        
        # Форматируем длительность в часы и минуты
        if duration:
            hours = duration // 60
            minutes = duration % 60
            if hours > 0:
                duration_text = f"{hours} ч {minutes} мин ({duration} мин)"
            else:
                duration_text = f"{minutes} мин"
            self.durationLabel.setText(duration_text)
        else:
            self.durationLabel.setText("Не указана")
        
        # Устанавливаем описание
        if description:
            self.descriptionTextEdit.setPlainText(description)
        else:
            self.descriptionTextEdit.setPlainText("Описание отсутствует")
        
        # Загружаем постер если он есть
        if poster_path and os.path.exists(poster_path):
            pixmap = QPixmap(poster_path)
            
            if not pixmap.isNull():
                # Масштабируем постер с сохранением пропорций
                scaled_pixmap = pixmap.scaled(
                    self.posterLabel.width(),
                    self.posterLabel.height(),
                    Qt.AspectRatioMode.KeepAspectRatio
                )
                self.posterLabel.setPixmap(scaled_pixmap)
            else:
                self.posterLabel.setText("Ошибка загрузки постера")
        else:
            self.posterLabel.setText("Постер отсутствует")

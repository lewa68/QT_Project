'''
Модуль диалога добавления и редактирования фильма.
Позволяет вводить и изменять информацию о фильме.
'''

import os
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QMessageBox, QFileDialog
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from database import Database


class AddEditDialog(QDialog):
    # Диалог для добавления и редактирования фильма
    
    def __init__(self, database: Database, movie_id: int = None, parent=None):
        super().__init__(parent)
        # Загружаем интерфейс из ui файла
        uic.loadUi('ui/add_edit_dialog.ui', self)
        
        self.db = database
        self.movie_id = movie_id
        self.poster_path = ""
        
        # Настраиваем окно в зависимости от режима
        if self.movie_id is None:
            self.setWindowTitle("Добавить фильм")
        else:
            self.setWindowTitle("Редактировать фильм")
            self.load_movie_data()
        
        # Подключаем сигналы
        self.connect_signals()
    
    def connect_signals(self):
        # Подключение сигналов к слотам
        self.selectPosterButton.clicked.connect(self.select_poster)
        self.saveButton.clicked.connect(self.save_movie)
        self.cancelButton.clicked.connect(self.reject)
    
    def load_movie_data(self):
        # Загрузка данных фильма для редактирования
        movie = self.db.get_movie_by_id(self.movie_id)
        
        if not movie:
            QMessageBox.critical(self, "Ошибка", "Фильм не найден в базе данных")
            self.reject()
            return
        
        # Заполняем поля формы
        self.titleLineEdit.setText(movie[1] if movie[1] else "")
        self.yearSpinBox.setValue(movie[2] if movie[2] else 2000)
        self.genreComboBox.setCurrentText(movie[3] if movie[3] else "")
        self.directorLineEdit.setText(movie[4] if movie[4] else "")
        self.ratingSpinBox.setValue(movie[5] if movie[5] else 0.0)
        self.durationSpinBox.setValue(movie[6] if movie[6] else 0)
        self.descriptionTextEdit.setPlainText(movie[7] if movie[7] else "")
        
        # Сохраняем путь к постеру
        self.poster_path = movie[8] if movie[8] else ""
        
        # Показываем постер если есть
        if self.poster_path and os.path.exists(self.poster_path):
            pixmap = QPixmap(self.poster_path)
            # Масштабируем постер с сохранением пропорций
            scaled_pixmap = pixmap.scaled(
                self.posterPreviewLabel.width(),
                self.posterPreviewLabel.height(),
                Qt.AspectRatioMode.KeepAspectRatio
            )
            self.posterPreviewLabel.setPixmap(scaled_pixmap)
            self.posterLineEdit.setText(os.path.basename(self.poster_path))
        else:
            self.posterPreviewLabel.setText("Нет постера")
            self.posterLineEdit.clear()
    
    def select_poster(self):
        # Выбор файла постера
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите постер",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if not file_path:
            return
        
        # Сохраняем путь
        self.poster_path = file_path
        
        # Отображаем постер
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Предупреждение", "Не удалось загрузить изображение")
            return
        
        # Масштабируем постер
        scaled_pixmap = pixmap.scaled(
            self.posterPreviewLabel.width(),
            self.posterPreviewLabel.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        )
        self.posterPreviewLabel.setPixmap(scaled_pixmap)
        self.posterLineEdit.setText(os.path.basename(file_path))
    
    def validate_inputs(self) -> bool:
        # Проверка корректности введенных данных
        title = self.titleLineEdit.text().strip()
        if not title:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите название фильма")
            self.titleLineEdit.setFocus()
            return False
        
        # Проверяем год
        year = self.yearSpinBox.value()
        if year < 1800 or year > 2100:
            QMessageBox.warning(self, "Ошибка", "Год должен быть в диапазоне 1800-2100")
            self.yearSpinBox.setFocus()
            return False
        
        # Проверяем жанр
        genre = self.genreComboBox.currentText().strip()
        if not genre:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите или выберите жанр фильма")
            self.genreComboBox.setFocus()
            return False
        
        # Проверяем режиссёра
        director = self.directorLineEdit.text().strip()
        if not director:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите имя режиссёра")
            self.directorLineEdit.setFocus()
            return False
        
        # Проверяем рейтинг
        rating = self.ratingSpinBox.value()
        if rating < 0 or rating > 10:
            QMessageBox.warning(self, "Ошибка", "Рейтинг должен быть от 0 до 10")
            self.ratingSpinBox.setFocus()
            return False
        
        # Проверяем длительность
        duration = self.durationSpinBox.value()
        if duration <= 0:
            QMessageBox.warning(self, "Ошибка", "Длительность должна быть больше 0")
            self.durationSpinBox.setFocus()
            return False
        
        return True
    
    def save_movie(self):
        # Сохранение данных фильма
        if not self.validate_inputs():
            return
        
        # Собираем данные из формы
        title = self.titleLineEdit.text().strip()
        year = self.yearSpinBox.value()
        genre = self.genreComboBox.currentText().strip()
        director = self.directorLineEdit.text().strip()
        rating = self.ratingSpinBox.value()
        duration = self.durationSpinBox.value()
        description = self.descriptionTextEdit.toPlainText().strip()
        
        # Копируем постер в папку posters если выбран новый файл
        if self.poster_path and not self.poster_path.startswith("posters/"):
            poster_filename = self.copy_poster_to_folder(self.poster_path)
            if poster_filename:
                self.poster_path = poster_filename
        
        # Сохраняем в базу данных
        if self.movie_id is None:
            # Добавление нового фильма
            success = self.db.add_movie(
                title, year, genre, director, 
                rating, duration, description, self.poster_path
            )
            
            if success:
                QMessageBox.information(self, "Успех", "Фильм успешно добавлен")
                self.accept()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось добавить фильм")
        else:
            # Обновление существующего фильма
            success = self.db.update_movie(
                self.movie_id, title, year, genre, director,
                rating, duration, description, self.poster_path
            )
            
            if success:
                QMessageBox.information(self, "Успех", "Фильм успешно обновлён")
                self.accept()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось обновить фильм")
    
    def copy_poster_to_folder(self, source_path: str) -> str:
        # Копирование постера в папку проекта
        import shutil
        
        # Создаём папку posters если её нет
        if not os.path.exists("posters"):
            os.makedirs("posters")
        
        # Генерируем имя файла
        filename = os.path.basename(source_path)
        dest_path = os.path.join("posters", filename)
        
        # Если файл уже существует, добавляем номер
        base_name, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            new_filename = f"{base_name}_{counter}{ext}"
            dest_path = os.path.join("posters", new_filename)
            counter += 1
        
        try:
            # Копируем файл
            shutil.copy2(source_path, dest_path)
            return dest_path
        except Exception as e:
            QMessageBox.warning(
                self,
                "Предупреждение",
                f"Не удалось скопировать постер: {str(e)}\nБудет использован оригинальный путь."
            )
            return source_path

'''
Модуль главного окна приложения.
Отвечает за отображение списка фильмов, поиск, фильтрацию и управление записями.
'''

from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt
from database import Database
from add_edit_dialog import AddEditDialog
from details_dialog import DetailsDialog


class MainWindow(QMainWindow):
    # Главное окно приложения Видеотека
    
    def __init__(self):
        super().__init__()
        # Загружаем интерфейс из ui файла
        uic.loadUi('ui/main_window.ui', self)
        
        # Инициализируем базу данных
        self.db = Database()
        
        # Настраиваем таблицу
        self.setup_table()
        
        # Подключаем сигналы к слотам
        self.connect_signals()
        
        # Заполняем фильтр жанров
        self.setup_genre_filter()
        
        # Загружаем все фильмы при запуске
        self.load_movies()
    
    def setup_table(self):
        # Настройка таблицы фильмов
        headers = ['ID', 'Название', 'Год', 'Жанр', 'Режиссёр', 'Рейтинг', 'Длительность', 'Описание', 'Постер']
        self.moviesTable.setColumnCount(len(headers))
        self.moviesTable.setHorizontalHeaderLabels(headers)
        
        # Скрываем столбцы ID, Описание и Постер
        self.moviesTable.hideColumn(0)  # ID
        self.moviesTable.hideColumn(7)  # Описание
        self.moviesTable.hideColumn(8)  # Путь к постеру
        
        # Растягиваем столбец Название
        self.moviesTable.setColumnWidth(1, 250)
        
        # Делаем таблицу нередактируемой
        self.moviesTable.setEditTriggers(self.moviesTable.EditTrigger.NoEditTriggers)
        
        # Выделение целой строки
        self.moviesTable.setSelectionBehavior(self.moviesTable.SelectionBehavior.SelectRows)
        self.moviesTable.setSelectionMode(self.moviesTable.SelectionMode.SingleSelection)
    
    def setup_genre_filter(self):
        # Заполнение выпадающего списка жанров из таблицы genres
        genres = self.db.get_all_genres()
        
        # Добавляем в комбобокс
        self.genreComboBox.clear()
        self.genreComboBox.addItem("Все жанры")
        for genre_id, genre_name in genres:
            self.genreComboBox.addItem(genre_name)
    
    def connect_signals(self):
        # Подключение всех сигналов к слотам
        self.addButton.clicked.connect(self.add_movie)
        self.editButton.clicked.connect(self.edit_movie)
        self.deleteButton.clicked.connect(self.delete_movie)
        self.viewButton.clicked.connect(self.view_details)
        self.refreshButton.clicked.connect(self.refresh_data)
        self.exportButton.clicked.connect(self.export_to_csv)
        self.statsButton.clicked.connect(self.show_statistics)
        
        # Поиск при вводе текста
        self.searchLineEdit.textChanged.connect(self.search_movies)
        
        # Фильтр жанров
        self.genreComboBox.currentTextChanged.connect(self.search_movies)
        
        # Двойной клик по строке для просмотра деталей
        self.moviesTable.doubleClicked.connect(self.view_details)
    
    def load_movies(self, movies=None):
        # Загрузка фильмов в таблицу
        if movies is None:
            movies = self.db.get_all_movies()
        
        # Очищаем таблицу
        self.moviesTable.setRowCount(0)
        
        # Заполняем таблицу данными
        for row_num, movie in enumerate(movies):
            self.moviesTable.insertRow(row_num)
            
            # Заполняем каждую ячейку
            for col_num, data in enumerate(movie):
                item = QTableWidgetItem(str(data) if data is not None else '')
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.moviesTable.setItem(row_num, col_num, item)
        
        # Обновляем счетчик фильмов в статус-баре
        self.statusBar().showMessage(f"Всего фильмов: {len(movies)}")
    
    def search_movies(self):
        # Поиск и фильтрация фильмов
        search_text = self.searchLineEdit.text().strip()
        genre = self.genreComboBox.currentText()
        
        # Выполняем поиск в базе
        movies = self.db.search_movies(search_text, genre)
        
        # Загружаем результаты в таблицу
        self.load_movies(movies)
    
    def add_movie(self):
        # Открытие диалога добавления фильма
        dialog = AddEditDialog(self.db, parent=self)
        if dialog.exec():
            self.refresh_data()
    
    def edit_movie(self):
        # Открытие диалога редактирования фильма
        selected_row = self.moviesTable.currentRow()
        
        if selected_row < 0:
            QMessageBox.warning(self, "Предупреждение", 
                              "Пожалуйста, выберите фильм для редактирования")
            return
        
        # Получаем ID фильма из скрытого столбца
        movie_id = int(self.moviesTable.item(selected_row, 0).text())
        
        # Открываем диалог редактирования
        dialog = AddEditDialog(self.db, movie_id, parent=self)
        if dialog.exec():
            self.refresh_data()
    
    def delete_movie(self):
        # Удаление фильма с подтверждением
        selected_row = self.moviesTable.currentRow()
        
        if selected_row < 0:
            QMessageBox.warning(self, "Предупреждение", 
                              "Пожалуйста, выберите фильм для удаления")
            return
        
        # Получаем название фильма для подтверждения
        movie_title = self.moviesTable.item(selected_row, 1).text()
        movie_id = int(self.moviesTable.item(selected_row, 0).text())
        
        # Запрашиваем подтверждение
        reply = QMessageBox.question(
            self, 
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить фильм '{movie_title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_movie(movie_id):
                QMessageBox.information(self, "Успех", "Фильм успешно удалён")
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось удалить фильм")
    
    def view_details(self):
        # Просмотр детальной информации о фильме
        selected_row = self.moviesTable.currentRow()
        
        if selected_row < 0:
            QMessageBox.warning(self, "Предупреждение", 
                              "Пожалуйста, выберите фильм для просмотра")
            return
        
        # Получаем ID фильма
        movie_id = int(self.moviesTable.item(selected_row, 0).text())
        
        # Открываем окно деталей
        dialog = DetailsDialog(self.db, movie_id, parent=self)
        dialog.exec()
    
    def refresh_data(self):
        # Обновление данных в таблице
        self.searchLineEdit.clear()
        self.genreComboBox.setCurrentIndex(0)
        
        # Обновляем фильтр жанров
        self.setup_genre_filter()
        
        # Перезагружаем все фильмы
        self.load_movies()
    
    def export_to_csv(self):
        # Экспорт списка фильмов в CSV файл
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт в CSV",
            "movies_export.csv",
            "CSV файлы (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            # Получаем все фильмы
            movies = self.db.get_all_movies()
            
            # Записываем в файл
            with open(file_path, 'w', encoding='utf-8') as f:
                # Заголовок
                f.write("ID;Название;Год;Жанр;Режиссёр;Рейтинг;Длительность;Описание;Постер\n")
                
                # Данные
                for movie in movies:
                    row = []
                    for field in movie:
                        if field is None:
                            row.append('')
                        else:
                            # Экранируем точку с запятой
                            row.append(str(field).replace(';', ','))
                    
                    f.write(';'.join(row) + '\n')
            
            QMessageBox.information(
                self,
                "Успех",
                f"Список фильмов успешно экспортирован в:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось экспортировать данные:\n{str(e)}"
            )
    
    def show_statistics(self):
        # Отображение статистики коллекции
        stats = self.db.get_statistics()
        
        # Формируем текст сообщения
        message = f"""
<h3>Статистика коллекции</h3>

<b>Общая информация:</b><br>
• Всего фильмов: {stats['total']}<br>
• Средний рейтинг: {stats['avg_rating']}<br>
• Общая длительность: {stats['total_duration']} мин ({stats['total_duration'] // 60} ч {stats['total_duration'] % 60} мин)<br>
• Средняя длительность: {stats['avg_duration']} мин<br>
<br>
"""
        
        # Лучший фильм
        if stats['best_movie']:
            message += f"<b>Лучший фильм по рейтингу:</b><br>"
            message += f"• {stats['best_movie']['title']} ({stats['best_movie']['rating']})<br><br>"
        
        # По жанрам
        if stats['by_genre']:
            message += f"<b>По жанрам:</b><br>"
            for genre, count in sorted(stats['by_genre'].items()):
                message += f"• {genre}: {count}<br>"
            message += "<br>"
        
        # По годам
        if stats['by_year']:
            message += f"<b>По годам выпуска:</b><br>"
            for year, count in sorted(stats['by_year'].items(), reverse=True):
                message += f"• {year}: {count}<br>"
        
        # Показываем диалог
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Статистика")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(message)
        msg_box.exec()
    
    def closeEvent(self, event):
        # Обработка закрытия окна
        self.db.close()
        event.accept()

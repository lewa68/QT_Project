'''
Модуль для работы с базой данных SQLite.
Управляет всеми операциями с данными о фильмах.
'''

import sqlite3
from typing import List, Tuple, Optional, Dict


class Database:
    # Класс для работы с базой данных фильмов
    
    def __init__(self, db_name: str = "movies.db"):
        # Инициализация подключения к базе данных
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        self.connect()
        self.create_table()
    
    def connect(self):
        # Создание подключения к SQLite
        try:
            self.connection = sqlite3.connect(self.db_name)
            self.cursor = self.connection.cursor()
            print(f"Подключение к базе данных {self.db_name} установлено")
        except sqlite3.Error as e:
            print(f"Ошибка подключения к БД: {e}")
    
    def create_table(self):
        # Создание таблицы genres если её нет
        create_genres_query = """
        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """
        
        # Создание таблицы movies если её нет
        create_movies_query = """
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            year INTEGER,
            genre_id INTEGER,
            director TEXT,
            rating REAL,
            duration INTEGER,
            description TEXT,
            poster_path TEXT,
            FOREIGN KEY (genre_id) REFERENCES genres(id)
        )
        """
        try:
            self.cursor.execute(create_genres_query)
            self.cursor.execute(create_movies_query)
            self.connection.commit()
            print("Таблицы movies и genres созданы или уже существуют")
            
            # Проверяем, есть ли старая структура (genre как TEXT)
            self.cursor.execute("PRAGMA table_info(movies)")
            columns = [row[1] for row in self.cursor.fetchall()]
            if 'genre' in columns:
                print("Обнаружена старая структура БД, выполняем миграцию...")
                self._migrate_to_genres()
            else:
                # Заполняем базовые жанры если таблица пустая
                self._init_default_genres()
        except sqlite3.Error as e:
            print(f"Ошибка создания таблиц: {e}")
    
    def _migrate_to_genres(self):
        # Миграция старой структуры с genre TEXT на genre_id INTEGER
        try:
            # Получаем все уникальные жанры из старой таблицы
            self.cursor.execute("SELECT DISTINCT genre FROM movies WHERE genre IS NOT NULL")
            old_genres = [row[0] for row in self.cursor.fetchall()]
            
            # Добавляем их в таблицу genres
            for genre_name in old_genres:
                self.cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (genre_name,))
            
            # Создаем временную таблицу с новой структурой
            self.cursor.execute("""
                CREATE TABLE movies_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    year INTEGER,
                    genre_id INTEGER,
                    director TEXT,
                    rating REAL,
                    duration INTEGER,
                    description TEXT,
                    poster_path TEXT,
                    FOREIGN KEY (genre_id) REFERENCES genres(id)
                )
            """)
            
            # Копируем данные со связыванием жанров
            self.cursor.execute("""
                INSERT INTO movies_new (id, title, year, genre_id, director, rating, duration, description, poster_path)
                SELECT m.id, m.title, m.year, g.id, m.director, m.rating, m.duration, m.description, m.poster_path
                FROM movies m
                LEFT JOIN genres g ON m.genre = g.name
            """)
            
            # Удаляем старую таблицу и переименовываем новую
            self.cursor.execute("DROP TABLE movies")
            self.cursor.execute("ALTER TABLE movies_new RENAME TO movies")
            
            self.connection.commit()
            print("Миграция базы данных завершена успешно")
        except sqlite3.Error as e:
            print(f"Ошибка миграции: {e}")
            self.connection.rollback()
    
    def _init_default_genres(self):
        # Инициализация базовых жанров
        default_genres = [
            'Драма', 'Боевик', 'Комедия', 'Триллер', 'Фантастика',
            'Ужасы', 'Детектив', 'Мелодрама', 'Приключения', 'Криминал'
        ]
        try:
            for genre in default_genres:
                self.cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (genre,))
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Ошибка инициализации жанров: {e}")
    
    def get_or_create_genre(self, genre_name: str) -> int:
        # Получение ID жанра или создание нового если не существует
        try:
            # Ищем существующий жанр
            self.cursor.execute("SELECT id FROM genres WHERE name = ?", (genre_name,))
            result = self.cursor.fetchone()
            
            if result:
                return result[0]
            else:
                # Создаем новый жанр
                self.cursor.execute("INSERT INTO genres (name) VALUES (?)", (genre_name,))
                self.connection.commit()
                return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Ошибка работы с жанром: {e}")
            return None
    
    def get_all_genres(self) -> List[Tuple]:
        # Получение всех жанров
        try:
            self.cursor.execute("SELECT id, name FROM genres ORDER BY name")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Ошибка получения жанров: {e}")
            return []
    
    def get_genre_name_by_id(self, genre_id: int) -> str:
        # Получение названия жанра по ID
        try:
            self.cursor.execute("SELECT name FROM genres WHERE id = ?", (genre_id,))
            result = self.cursor.fetchone()
            return result[0] if result else ""
        except sqlite3.Error as e:
            print(f"Ошибка получения названия жанра: {e}")
            return ""
    
    def add_movie(self, title: str, year: int, genre: str, director: str, 
                  rating: float, duration: int, description: str, poster_path: str) -> bool:
        # Добавление нового фильма в базу
        try:
            # Получаем или создаем жанр
            genre_id = self.get_or_create_genre(genre)
            if genre_id is None:
                return False
            
            insert_query = """
            INSERT INTO movies (title, year, genre_id, director, rating, duration, description, poster_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(insert_query, 
                              (title, year, genre_id, director, rating, duration, description, poster_path))
            self.connection.commit()
            print(f"Фильм '{title}' добавлен в базу данных")
            return True
        except sqlite3.Error as e:
            print(f"Ошибка добавления фильма: {e}")
            return False
    
    def get_all_movies(self) -> List[Tuple]:
        # Получение всех фильмов из базы с названиями жанров
        select_query = """
        SELECT m.id, m.title, m.year, g.name, m.director, m.rating, m.duration, m.description, m.poster_path
        FROM movies m
        LEFT JOIN genres g ON m.genre_id = g.id
        ORDER BY m.title
        """
        try:
            self.cursor.execute(select_query)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Ошибка получения списка фильмов: {e}")
            return []
    
    def get_movie_by_id(self, movie_id: int) -> Optional[Tuple]:
        # Получение фильма по ID с названием жанра
        select_query = """
        SELECT m.id, m.title, m.year, g.name, m.director, m.rating, m.duration, m.description, m.poster_path
        FROM movies m
        LEFT JOIN genres g ON m.genre_id = g.id
        WHERE m.id = ?
        """
        try:
            self.cursor.execute(select_query, (movie_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Ошибка получения фильма: {e}")
            return None
    
    def update_movie(self, movie_id: int, title: str, year: int, genre: str, 
                    director: str, rating: float, duration: int, 
                    description: str, poster_path: str) -> bool:
        # Обновление данных существующего фильма
        try:
            # Получаем или создаем жанр
            genre_id = self.get_or_create_genre(genre)
            if genre_id is None:
                return False
            
            update_query = """
            UPDATE movies 
            SET title = ?, year = ?, genre_id = ?, director = ?, 
                rating = ?, duration = ?, description = ?, poster_path = ?
            WHERE id = ?
            """
            self.cursor.execute(update_query, 
                              (title, year, genre_id, director, rating, duration, 
                               description, poster_path, movie_id))
            self.connection.commit()
            print(f"Фильм с ID {movie_id} обновлён")
            return True
        except sqlite3.Error as e:
            print(f"Ошибка обновления фильма: {e}")
            return False
    
    def delete_movie(self, movie_id: int) -> bool:
        # Удаление фильма из базы
        delete_query = "DELETE FROM movies WHERE id = ?"
        try:
            self.cursor.execute(delete_query, (movie_id,))
            self.connection.commit()
            print(f"Фильм с ID {movie_id} удалён")
            return True
        except sqlite3.Error as e:
            print(f"Ошибка удаления фильма: {e}")
            return False
    
    def search_movies(self, search_text: str = "", genre: str = "Все жанры") -> List[Tuple]:
        # Поиск и фильтрация фильмов
        query = """
        SELECT m.id, m.title, m.year, g.name, m.director, m.rating, m.duration, m.description, m.poster_path
        FROM movies m
        LEFT JOIN genres g ON m.genre_id = g.id
        WHERE 1=1
        """
        params = []
        
        # Фильтр по жанру
        if genre != "Все жанры":
            query += " AND g.name = ?"
            params.append(genre)
        
        query += " ORDER BY m.title"
        
        try:
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            # Фильтрация по названию
            if search_text:
                search_lower = search_text.lower()
                results = [
                    movie for movie in results 
                    if search_lower in movie[1].lower()  # movie[1] это title
                ]
            
            return results
        except sqlite3.Error as e:
            print(f"Ошибка поиска фильмов: {e}")
            return []
    
    def get_movies_sorted(self, column: str, ascending: bool = True) -> List[Tuple]:
        '''
        Получение фильмов с сортировкой по указанному столбцу.
        Защита от SQL инъекций через проверку имени столбца.
        '''
        valid_columns = ['title', 'year', 'genre', 'director', 'rating', 'duration']
        if column not in valid_columns:
            column = 'title'
        
        # Используем псевдоним для genre (g.name)
        if column == 'genre':
            column = 'g.name'
        else:
            column = f'm.{column}'
        
        order = 'ASC' if ascending else 'DESC'
        query = f"""
        SELECT m.id, m.title, m.year, g.name, m.director, m.rating, m.duration, m.description, m.poster_path
        FROM movies m
        LEFT JOIN genres g ON m.genre_id = g.id
        ORDER BY {column} {order}
        """
        
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Ошибка сортировки фильмов: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        # Получение статистики по коллекции фильмов
        stats = {
            'total': 0,
            'by_genre': {},
            'avg_rating': 0.0,
            'total_duration': 0,
            'avg_duration': 0,
            'best_movie': None,
            'by_year': {}
        }
        
        try:
            # Общее количество фильмов
            self.cursor.execute("SELECT COUNT(*) FROM movies")
            stats['total'] = self.cursor.fetchone()[0]
            
            # Количество по жанрам
            self.cursor.execute("""
                SELECT g.name, COUNT(*) 
                FROM movies m
                LEFT JOIN genres g ON m.genre_id = g.id
                GROUP BY g.name
            """)
            for genre, count in self.cursor.fetchall():
                stats['by_genre'][genre if genre else 'Без жанра'] = count
            
            # Средний рейтинг
            self.cursor.execute("SELECT AVG(rating) FROM movies")
            avg_rating = self.cursor.fetchone()[0]
            stats['avg_rating'] = round(avg_rating, 2) if avg_rating else 0.0
            
            # Общая длительность
            self.cursor.execute("SELECT SUM(duration) FROM movies")
            total_duration = self.cursor.fetchone()[0]
            stats['total_duration'] = total_duration if total_duration else 0
            
            # Средняя длительность
            if stats['total'] > 0:
                stats['avg_duration'] = round(stats['total_duration'] / stats['total'])
            
            # Лучший фильм по рейтингу
            self.cursor.execute("SELECT title, rating FROM movies ORDER BY rating DESC LIMIT 1")
            best = self.cursor.fetchone()
            if best:
                stats['best_movie'] = {'title': best[0], 'rating': best[1]}
            
            # Количество по годам
            self.cursor.execute("SELECT year, COUNT(*) FROM movies GROUP BY year ORDER BY year DESC")
            for year, count in self.cursor.fetchall():
                stats['by_year'][year] = count
            
            return stats
        except sqlite3.Error as e:
            print(f"Ошибка получения статистики: {e}")
            return stats
    
    def get_movies_by_year_range(self, start_year: int, end_year: int) -> List[Tuple]:
        # Получение фильмов за определенный период
        query = """
        SELECT m.id, m.title, m.year, g.name, m.director, m.rating, m.duration, m.description, m.poster_path
        FROM movies m
        LEFT JOIN genres g ON m.genre_id = g.id
        WHERE m.year BETWEEN ? AND ? 
        ORDER BY m.year DESC, m.title
        """
        try:
            self.cursor.execute(query, (start_year, end_year))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Ошибка фильтрации по годам: {e}")
            return []
    
    def get_movies_by_rating_range(self, min_rating: float, max_rating: float) -> List[Tuple]:
        # Получение фильмов с рейтингом в указанном диапазоне
        query = """
        SELECT m.id, m.title, m.year, g.name, m.director, m.rating, m.duration, m.description, m.poster_path
        FROM movies m
        LEFT JOIN genres g ON m.genre_id = g.id
        WHERE m.rating BETWEEN ? AND ? 
        ORDER BY m.rating DESC
        """
        try:
            self.cursor.execute(query, (min_rating, max_rating))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Ошибка фильтрации по рейтингу: {e}")
            return []
    
    def close(self):
        # Закрытие соединения с базой данных
        if self.connection:
            self.connection.close()
            print("Соединение с базой данных закрыто")

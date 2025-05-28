import sqlite3
from contextlib import closing

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            ''')
            # Search history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    query TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            # Favorites
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    movie_title TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(user_id, movie_title)
                )
            ''')
            conn.commit()

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def create_user(self, username, password_hash):
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                         (username, password_hash))
            conn.commit()

    def get_user(self, username):
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            return cursor.fetchone()

    def add_search_history(self, user_id, query):
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO search_history (user_id, query) VALUES (?, ?)',
                         (user_id, query))
            conn.commit()

    def get_search_history(self, user_id, limit=10):
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT query, timestamp 
                FROM search_history 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (user_id, limit))
            return cursor.fetchall()

    def add_favorite(self, user_id, movie_title):
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO favorites (user_id, movie_title) 
                VALUES (?, ?)
            ''', (user_id, movie_title))
            conn.commit()

    def remove_favorite(self, user_id, movie_title):
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM favorites 
                WHERE user_id = ? AND movie_title = ?
            ''', (user_id, movie_title))
            conn.commit()

    def get_favorites(self, user_id):
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT movie_title 
                FROM favorites 
                WHERE user_id = ? 
                ORDER BY timestamp DESC
            ''', (user_id,))
            return [row[0] for row in cursor.fetchall()]
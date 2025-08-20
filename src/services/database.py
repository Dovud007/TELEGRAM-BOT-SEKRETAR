# ПРОВЕРЬТЕ, ЧТО ВАШ ФАЙЛ ВЫГЛЯДИТ ИМЕННО ТАК:

import sqlite3
from datetime import datetime

DB_PATH = '../database.db' # Путь к файлу БД. '../' означает "на одну папку выше"

def get_connection():
    """Устанавливает соединение с базой данных."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Позволяет обращаться к колонкам по имени
    return conn

def init_db():
    """Создает таблицы в базе данных, если они еще не существуют."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Создаем таблицу для расходов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Создаем таблицу для событий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            event_time TIMESTAMP NOT NULL,
            reminded BOOLEAN DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()
    print("База данных успешно инициализирована.")

def add_expense(amount: float, category: str):
    """Добавляет новую запись о расходе в базу данных."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO expenses (amount, category) VALUES (?, ?)", (amount, category))
    conn.commit()
    conn.close()

def add_event(event_name: str, event_time: datetime):
    """Добавляет новое событие в базу данных."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (event_name, event_time) VALUES (?, ?)", (event_name, event_time))
    conn.commit()
    conn.close()

def get_expenses_for_period(start_date: datetime, end_date: datetime):
    """Возвращает список расходов за указанный период."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, amount, category, created_at FROM expenses WHERE created_at BETWEEN ? AND ?",
        (start_date, end_date)
    )
    expenses = cursor.fetchall()
    conn.close()
    return expenses
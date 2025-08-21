import pandas as pd
import os
import tempfile
from typing import List
import sqlite3

def create_excel_report(expenses: List[sqlite3.Row]) -> str:
    """
    Создает Excel-отчет на основе списка расходов.

    :param expenses: Список объектов sqlite3.Row, каждый из которых представляет расход.
    :return: Путь к созданному Excel-файлу.
    """
    # Преобразуем список sqlite3.Row в список словарей для удобства
    expenses_dict = [dict(row) for row in expenses]

    # Создаем DataFrame из списка словарей
    df = pd.DataFrame(expenses_dict)

    # Переименовываем колонки для лучшей читаемости в отчете
    df.rename(columns={
        'id': 'ID',
        'amount': 'Сумма',
        'category': 'Категория',
        'created_at': 'Дата'
    }, inplace=True)

    # Форматируем колонку с датой, убирая время
    if not df.empty:
        df['Дата'] = pd.to_datetime(df['Дата']).dt.strftime('%Y-%m-%d')

    # Создаем временный файл для отчета
    # tempfile.mkstemp() возвращает кортеж (дескриптор, путь)
    _, file_path = tempfile.mkstemp(suffix='.xlsx')

    # Сохраняем DataFrame в Excel-файл
    df.to_excel(file_path, index=False, sheet_name='Расходы')

    return file_path

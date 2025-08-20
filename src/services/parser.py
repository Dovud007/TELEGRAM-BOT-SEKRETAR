def parse_expense_text(text: str) -> tuple[float, str] | None:
    """
    Пытается извлечь сумму и категорию из текста.
    Текст может быть от команды ('/expense 500 Обед') или от голоса ('расход 500 Обед').
    Возвращает кортеж (сумма, категория) или None, если формат неверный.
    """
    parts = text.lower().split()
    
    # Ищем ключевое слово 'расход' или команду '/expense'
    # Это позволяет функции работать и с текстом, и с голосом
    if '/expense' not in parts and 'расход' not in parts:
        return None

    # Находим индекс ключевого слова, чтобы взять следующие за ним слова
    try:
        if '/expense' in parts:
            start_index = parts.index('/expense') + 1
        else: # 'расход'
            start_index = parts.index('расход') + 1

        # Проверяем, есть ли после команды хотя бы 2 слова (сумма и категория)
        if len(parts) < start_index + 2:
            return None

        amount_str = parts[start_index]
        category = " ".join(parts[start_index + 1:])
        
        amount = float(amount_str)
        
        return amount, category.capitalize()

    except (ValueError, IndexError):
        # Если не удалось преобразовать сумму в число или другие ошибки
        return None
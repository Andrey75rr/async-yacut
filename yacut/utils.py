import random
import string

from .models import URLMap

RESERVED_IDS = {'files'}
SHORT_ID_CHARS = string.ascii_letters + string.digits
SHORT_ID_LENGTH = 6


def get_unique_short_id(length=SHORT_ID_LENGTH):
    """Генерирует случайный короткий идентификатор."""
    return ''.join(random.choice(SHORT_ID_CHARS) for _ in range(length))


def is_short_id_taken(short_id):
    """Возвращает True, если ID уже занят (в БД или зарезервирован)."""
    if short_id in RESERVED_IDS:
        return True
    return URLMap.query.filter_by(short=short_id).first() is not None


def generate_unique_short_id():
    """Генерирует уникальный короткий идентификатор, не занятый в БД."""
    while True:
        short_id = get_unique_short_id()
        if not is_short_id_taken(short_id):
            return short_id

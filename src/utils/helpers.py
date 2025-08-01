"""
Helper functions for data processing
"""

import re
from typing import Union, Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta, time
from dataclasses import dataclass

from ..config.constants import Timeframe


def parse_datetime(time_obj: Union[str, datetime, int, float]) -> datetime:
    """
    Парсинг времени из различных форматов
    
    Args:
        time_obj: Время в различных форматах
        
    Returns:
        datetime объект в UTC
    """
    if isinstance(time_obj, datetime):
        # Если уже datetime, убеждаемся что в UTC
        if time_obj.tzinfo is None:
            return time_obj.replace(tzinfo=timezone.utc)
        return time_obj.astimezone(timezone.utc)
    
    elif isinstance(time_obj, str):
        # Парсим строку
        if time_obj.endswith('Z'):
            # ISO формат с Z
            return datetime.fromisoformat(time_obj.replace('Z', '+00:00'))
        elif '+' in time_obj:
            # ISO формат с timezone
            return datetime.fromisoformat(time_obj)
        else:
            # Пробуем различные форматы
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%d',
                '%H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(time_obj, fmt)
                    if fmt == '%H:%M:%S':
                        # Если только время, добавляем сегодняшнюю дату
                        today = datetime.now(timezone.utc).date()
                        dt = datetime.combine(today, dt.time())
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            
            raise ValueError(f"Unable to parse datetime string: {time_obj}")
    
    elif isinstance(time_obj, (int, float)):
        # Unix timestamp
        return datetime.fromtimestamp(time_obj, tz=timezone.utc)
    
    else:
        raise ValueError(f"Unsupported time format: {type(time_obj)}")


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Форматирование datetime в строку
    
    Args:
        dt: datetime объект
        format_str: Строка формата
        
    Returns:
        Отформатированная строка
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime(format_str)


def get_utc_now() -> datetime:
    """Получить текущее время в UTC"""
    return datetime.now(timezone.utc)


def round_to_timeframe(dt: datetime, timeframe: Timeframe) -> datetime:
    """
    Округление времени до границы таймфрейма
    
    Args:
        dt: datetime объект
        timeframe: Таймфрейм
        
    Returns:
        Округленное время
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    minutes = timeframe.minutes
    
    # Округляем до минут
    dt = dt.replace(second=0, microsecond=0)
    
    # Округляем до границы таймфрейма
    total_minutes = dt.hour * 60 + dt.minute
    rounded_minutes = (total_minutes // minutes) * minutes
    
    return dt.replace(hour=rounded_minutes // 60, minute=rounded_minutes % 60)


def get_timeframe_boundaries(
    dt: datetime, 
    timeframe: Timeframe
) -> tuple[datetime, datetime]:
    """
    Получить границы таймфрейма для указанного времени
    
    Args:
        dt: datetime объект
        timeframe: Таймфрейм
        
    Returns:
        Кортеж (начало_таймфрейма, конец_таймфрейма)
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    start = round_to_timeframe(dt, timeframe)
    end = start + timedelta(minutes=timeframe.minutes)
    
    return start, end


def calculate_seconds_until_next_timeframe(
    timeframe: Timeframe, 
    current_time: Optional[datetime] = None
) -> int:
    """
    Вычислить секунды до следующего таймфрейма
    
    Args:
        timeframe: Таймфрейм
        current_time: Текущее время (если None, используется текущее)
        
    Returns:
        Количество секунд до следующего таймфрейма
    """
    if current_time is None:
        current_time = get_utc_now()
    
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    
    next_boundary = round_to_timeframe(current_time, timeframe) + timedelta(minutes=timeframe.minutes)
    
    return int((next_boundary - current_time).total_seconds())


def is_market_open(
    current_time: Optional[datetime] = None,
    start_time: time = time(0, 0),
    end_time: time = time(23, 59)
) -> bool:
    """
    Проверить открыт ли рынок
    
    Args:
        current_time: Текущее время
        start_time: Время открытия рынка
        end_time: Время закрытия рынка
        
    Returns:
        True если рынок открыт
    """
    if current_time is None:
        current_time = get_utc_now()
    
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    
    current_time_only = current_time.time()
    
    if start_time <= end_time:
        # Обычный день (например, 09:00 - 17:00)
        return start_time <= current_time_only <= end_time
    else:
        # Переход через полночь (например, 22:00 - 06:00)
        return current_time_only >= start_time or current_time_only <= end_time


def validate_symbol(symbol: str) -> bool:
    """
    Валидация символа валютной пары
    
    Args:
        symbol: Символ для валидации
        
    Returns:
        True если символ валиден
    """
    # Паттерн для валютных пар: XXX_YYY
    pattern = r'^[A-Z]{3}_[A-Z]{3}$'
    return bool(re.match(pattern, symbol))


def validate_timeframe(timeframe_str: str) -> bool:
    """
    Валидация строки таймфрейма
    
    Args:
        timeframe_str: Строка таймфрейма
        
    Returns:
        True если таймфрейм валиден
    """
    valid_timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1', 'MN1']
    return timeframe_str in valid_timeframes


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Разбить список на чанки
    
    Args:
        lst: Исходный список
        chunk_size: Размер чанка
        
    Returns:
        Список чанков
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Безопасное преобразование в float
    
    Args:
        value: Значение для преобразования
        default: Значение по умолчанию
        
    Returns:
        float значение
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Безопасное преобразование в int
    
    Args:
        value: Значение для преобразования
        default: Значение по умолчанию
        
    Returns:
        int значение
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Вычислить процентное изменение
    
    Args:
        old_value: Старое значение
        new_value: Новое значение
        
    Returns:
        Процентное изменение
    """
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100


def format_number(number: float, decimals: int = 5) -> str:
    """
    Форматирование числа с указанным количеством знаков после запятой
    
    Args:
        number: Число для форматирования
        decimals: Количество знаков после запятой
        
    Returns:
        Отформатированная строка
    """
    return f"{number:.{decimals}f}"


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Объединение словарей
    
    Args:
        *dicts: Словари для объединения
        
    Returns:
        Объединенный словарь
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


@dataclass
class TimeRange:
    """Диапазон времени"""
    start: datetime
    end: datetime
    
    def __post_init__(self):
        if self.start.tzinfo is None:
            self.start = self.start.replace(tzinfo=timezone.utc)
        if self.end.tzinfo is None:
            self.end = self.end.replace(tzinfo=timezone.utc)
    
    def contains(self, dt: datetime) -> bool:
        """Проверить содержит ли диапазон указанное время"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return self.start <= dt <= self.end
    
    def duration(self) -> timedelta:
        """Получить длительность диапазона"""
        return self.end - self.start
    
    def duration_seconds(self) -> int:
        """Получить длительность в секундах"""
        return int(self.duration().total_seconds()) 
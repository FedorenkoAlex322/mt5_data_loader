"""
Constants and enums for the trading system
"""

from enum import Enum, auto
from typing import Dict, Any


class Timeframe(Enum):
    """Таймфреймы для торговли"""
    M5 = auto()
    M15 = auto()
    M30 = auto()
    H1 = auto()
    H4 = auto()
    D1 = auto()
    
    @property
    def minutes(self) -> int:
        """Возвращает количество минут в таймфрейме"""
        return {
            Timeframe.M5: 5,
            Timeframe.M15: 15,
            Timeframe.M30: 30,
            Timeframe.H1: 60,
            Timeframe.H4: 240,
            Timeframe.D1: 1440,
        }[self]
    
    @property
    def id(self) -> int:
        """Возвращает ID таймфрейма в базе данных"""
        return {
            Timeframe.M5: 3,
            Timeframe.M15: 4,
            Timeframe.M30: 8,
            Timeframe.H1: 5,
            Timeframe.H4: 6,
            Timeframe.D1: 7,
        }[self]
    
    @property
    def oanda_format(self) -> str:
        """Возвращает формат таймфрейма для OANDA API"""
        return {
            Timeframe.M5: "M5",
            Timeframe.M15: "M15",
            Timeframe.M30: "M30",
            Timeframe.H1: "H1",
            Timeframe.H4: "H4",
            Timeframe.D1: "D",
        }[self]
    
    @property
    def description(self) -> str:
        """Возвращает описание таймфрейма"""
        return {
            Timeframe.M5: "5 минут",
            Timeframe.M15: "15 минут",
            Timeframe.M30: "30 минут",
            Timeframe.H1: "1 час",
            Timeframe.H4: "4 часа",
            Timeframe.D1: "1 день",
        }[self]


class SystemStatus(Enum):
    """Статусы системы"""
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"


class NotificationType(Enum):
    """Типы уведомлений"""
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    TRADE_OPEN = "trade_open"
    TRADE_CLOSE = "trade_close"
    ERROR = "error"
    WARNING = "warning"
    ANALYSIS = "analysis"
    HEARTBEAT = "heartbeat"


# Константы для MT5
MT5_TIMEFRAME_MAPPING = {
    Timeframe.M5: 5,      # mt5.TIMEFRAME_M5
    Timeframe.M15: 15,    # mt5.TIMEFRAME_M15
    Timeframe.M30: 30,    # mt5.TIMEFRAME_M30
    Timeframe.H1: 16385,  # mt5.TIMEFRAME_H1
    Timeframe.H4: 16388,  # mt5.TIMEFRAME_H4
    Timeframe.D1: 16408,  # mt5.TIMEFRAME_D1
}

# Стандартные торговые пары (в формате OANDA)
STANDARD_CURRENCY_PAIRS = [
    'EUR_USD',
    'GBP_USD', 
    'USD_JPY',
    'USD_CHF',
    'USD_CAD',
    'AUD_USD',
    'NZD_USD',
    'EUR_GBP',
    'EUR_JPY',
    'EUR_CHF',
    'EUR_CAD',
    'EUR_AUD',
    'EUR_NZD',
    'GBP_JPY',
    'GBP_CHF',
    'GBP_CAD',
    'GBP_AUD',
    'GBP_NZD',
    'CHF_JPY',
    'CAD_JPY',
    'AUD_JPY',
    'AUD_CAD',
    'AUD_CHF',
    'AUD_NZD',
    'NZD_JPY',
    'NZD_CAD',
    'NZD_CHF',
    'CAD_CHF'
]

# Функция для генерации возможных вариантов названий символа в MT5
def generate_mt5_symbol_variants(symbol: str) -> list:
    """
    Генерирует возможные варианты названий символа для поиска в MT5
    
    Args:
        symbol: Символ в формате OANDA (например, 'EUR_USD')
        
    Returns:
        Список возможных вариантов названий для MT5
    """
    # Убираем подчеркивание
    no_underscore = symbol.replace('_', '')
    
    # Различные варианты написания
    variants = [
        no_underscore,           # EURUSD
        no_underscore.upper(),   # EURUSD
        no_underscore.lower(),   # eurusd
        symbol.replace('_', ''), # EURUSD
        symbol.replace('_', '.'), # EUR.USD
        symbol.replace('_', '').lower() + '.sml',  # eurusd.sml
        symbol.replace('_', '').upper() + '.sml',  # EURUSD.sml
        symbol.replace('_', '').lower() + '.raw',  # eurusd.raw
        symbol.replace('_', '').upper() + '.raw',  # EURUSD.raw
        symbol.replace('_', '').lower() + '.pro',  # eurusd.pro
        symbol.replace('_', '').upper() + '.pro',  # EURUSD.pro
    ]
    
    return list(set(variants))  # Убираем дубликаты 
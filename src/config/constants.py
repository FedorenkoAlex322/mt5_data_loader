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

# Базовый маппинг символов OANDA -> MT5
OANDA_TO_MT5_SYMBOL_MAPPING = {
    'EUR_USD': 'EURUSD',
    'GBP_USD': 'GBPUSD',
    'USD_JPY': 'USDJPY',
    'USD_CHF': 'USDCHF',
    'USD_CAD': 'USDCAD',
    'AUD_USD': 'AUDUSD',
    'NZD_USD': 'NZDUSD',
    'EUR_GBP': 'EURGBP',
    'EUR_JPY': 'EURJPY',
    'EUR_CHF': 'EURCHF',
    'EUR_CAD': 'EURCAD',
    'EUR_AUD': 'EURAUD',
    'EUR_NZD': 'EURNZD',
    'GBP_JPY': 'GBPJPY',
    'GBP_CHF': 'GBPCHF',
    'GBP_CAD': 'GBPCAD',
    'GBP_AUD': 'GBPAUD',
    'GBP_NZD': 'GBPNZD',
    'CHF_JPY': 'CHFJPY',
    'CAD_JPY': 'CADJPY',
    'AUD_JPY': 'AUDJPY',
    'AUD_CAD': 'AUDCAD',
    'AUD_CHF': 'AUDCHF',
    'AUD_NZD': 'AUDNZD',
    'NZD_JPY': 'NZDJPY',
    'NZD_CAD': 'NZDCAD',
    'NZD_CHF': 'NZDCHF',
    'CAD_CHF': 'CADCHF'
} 
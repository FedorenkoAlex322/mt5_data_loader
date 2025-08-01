"""
Trading Data Loader - система загрузки торговых данных с MetaTrader5
"""

__version__ = "1.0.0"
__author__ = "Trading System Developer"

# Экспортируем основные компоненты для удобства импорта
from .config.settings import Settings, get_settings, CurrencyPair
from .config.constants import Timeframe, SystemStatus, NotificationType
from .core.database import DatabaseManager
from .core.mt5_client import MT5Client
from .core.telegram_notifier import TelegramNotifier
from .data.real_time_updater import RealTimeDataUpdater
from .data.historical_loader import HistoricalDataLoader
from .data.candle_processor import CandleProcessor
from .utils.logging import setup_logging, get_logger
from .utils.helpers import parse_datetime, format_datetime, get_utc_now

__all__ = [
    # Config
    "Settings", "get_settings", "CurrencyPair", "Timeframe", "SystemStatus", "NotificationType",
    # Core
    "DatabaseManager", "MT5Client", "TelegramNotifier",
    # Data
    "RealTimeDataUpdater", "HistoricalDataLoader", "CandleProcessor",
    # Utils
    "setup_logging", "get_logger", "parse_datetime", "format_datetime", "get_utc_now"
] 
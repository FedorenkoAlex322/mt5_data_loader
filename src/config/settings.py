"""
Configuration settings using Pydantic
"""

import os
from typing import List, Dict, Optional, Any, Union
from datetime import time
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

from .constants import Timeframe, SystemStatus, NotificationType, STANDARD_CURRENCY_PAIRS

# Загружаем переменные окружения из .env файла
env_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(env_file_path)


class CurrencyPair:
    """Конфигурация валютной пары"""
    def __init__(
        self,
        symbol: str,
        symbol_id: int,
        enabled: bool = True,
        priority: int = 1,
        pip_size: float = 0.0001,
        min_trade_size: int = 1,
        description: str = ""
    ):
        self.symbol = symbol
        self.symbol_id = symbol_id
        self.enabled = enabled
        self.priority = priority
        self.pip_size = pip_size
        self.min_trade_size = min_trade_size
        self.description = description


class Settings(BaseSettings):
    """Основные настройки приложения"""

    # База данных
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="trading_system", env="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: Optional[str] = Field(default=None, env="POSTGRES_PASSWORD")
    postgres_timezone: str = Field(default="UTC", env="POSTGRES_TIMEZONE")
    
    # MetaTrader5
    mt5_login: Optional[int] = Field(default=None, env="MT5_LOGIN")
    mt5_password: Optional[str] = Field(default=None, env="MT5_PASSWORD")
    mt5_server: Optional[str] = Field(default=None, env="MT5_SERVER")
    mt5_terminal_path: Optional[str] = Field(default=None, env="MT5_TERMINAL_PATH")
    mt5_rate_limit_delay: float = Field(default=0.1, env="MT5_RATE_LIMIT_DELAY")
    
    # Telegram
    telegram_token: Optional[str] = Field(default=None, env="TELEGRAM_TOKEN")
    telegram_chat_id: Optional[str] = Field(default=None, env="TELEGRAM_CHAT_ID")
    telegram_topics: Any = Field(
        default={
            "trades": 223,
            "system": 1528,
            "analysis": 222,
            "pending_orders": 1662
        },
        env="TELEGRAM_TOPICS"
    )
    telegram_retry_attempts: int = Field(default=3, env="TELEGRAM_RETRY_ATTEMPTS")
    
    # Обновление данных
    update_interval: int = Field(default=60, env="UPDATE_INTERVAL")
    candles_to_fetch: int = Field(default=1000, env="CANDLES_TO_FETCH")
    parallel_downloads: bool = Field(default=True, env="PARALLEL_DOWNLOADS")
    max_workers: int = Field(default=3, env="MAX_WORKERS")
    max_retries: int = Field(default=5, env="MAX_RETRIES")
    retry_interval: int = Field(default=30, env="RETRY_INTERVAL")
    smart_schedule_mode: bool = Field(default=False, env="SMART_SCHEDULE_MODE")
    
    # Логирование
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    log_max_file_size: int = Field(default=10*1024*1024, env="LOG_MAX_FILE_SIZE")
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Мониторинг
    heartbeat_interval: int = Field(default=3600, env="HEARTBEAT_INTERVAL")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8000, env="METRICS_PORT")
    
    # Торговые часы
    trading_start_time: str = Field(default="00:00", env="TRADING_START_TIME")
    trading_end_time: str = Field(default="23:59", env="TRADING_END_TIME")
    trading_timezone: str = Field(default="UTC", env="TRADING_TIMEZONE")

    model_config = ConfigDict(
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator('telegram_topics')
    @classmethod
    def parse_telegram_topics(cls, v):
        if isinstance(v, str):
            topics = {}
            for item in v.split(','):
                if ':' in item:
                    key, value = item.split(':')
                    topics[key.strip()] = int(value.strip())
            return topics
        return v
    
    @property
    def database(self):
        return {
            'host': self.postgres_host, 'port': self.postgres_port,
            'database': self.postgres_db, 'user': self.postgres_user,
            'password': self.postgres_password, 'timezone': self.postgres_timezone
        }
    
    @property
    def mt5(self):
        return {
            'login': self.mt5_login, 'password': self.mt5_password,
            'server': self.mt5_server, 'terminal_path': self.mt5_terminal_path,
            'rate_limit_delay': self.mt5_rate_limit_delay
        }
    
    @property
    def telegram(self):
        return {
            'bot_token': self.telegram_token, 'chat_id': self.telegram_chat_id,
            'topics': self.telegram_topics, 'retry_attempts': self.telegram_retry_attempts
        }
    
    @property
    def data_update(self):
        return {
            'update_interval': self.update_interval, 'candles_to_fetch': self.candles_to_fetch,
            'parallel_downloads': self.parallel_downloads, 'max_workers': self.max_workers,
            'max_retries': self.max_retries, 'retry_interval': self.retry_interval,
            'smart_schedule_mode': self.smart_schedule_mode,
            'timeframe_schedules': {
                "M5": {"enabled": True, "interval_minutes": 5},
                "M15": {"enabled": True, "interval_minutes": 15},
                "M30": {"enabled": True, "interval_minutes": 30},
                "H1": {"enabled": True, "interval_minutes": 60},
                "H4": {"enabled": True, "interval_minutes": 240},
                "D1": {"enabled": True, "interval_minutes": 1440},
            }
        }
    
    @property
    def logging(self):
        return {
            'level': self.log_level, 'format': self.log_format,
            'max_file_size': self.log_max_file_size, 'backup_count': self.log_backup_count
        }
    
    @property
    def monitoring(self):
        return {
            'heartbeat_interval': self.heartbeat_interval, 'enable_metrics': self.enable_metrics,
            'metrics_port': self.metrics_port
        }
    
    @property
    def trading_hours(self):
        from datetime import time # Import time here
        return {
            'start_time': time.fromisoformat(self.trading_start_time),
            'end_time': time.fromisoformat(self.trading_end_time),
            'timezone': self.trading_timezone
        }
    
    @property
    def currency_pairs(self) -> List[CurrencyPair]:
        """Возвращает список торговых пар из стандартного списка"""
        # Маппинг символов на их ID в базе данных (можно вынести в конфигурацию)
        symbol_id_mapping = {
            'EUR_USD': 7,
            'GBP_USD': 6,
            'USD_CAD': 9,
            'USD_CHF': 10,
            'USD_JPY': 8,
            'AUD_USD': 11,
            'NZD_USD': 12,
            'EUR_GBP': 13,
            'EUR_JPY': 14,
            'GBP_JPY': 15,
        }
        
        # Описания торговых пар
        symbol_descriptions = {
            'EUR_USD': "Евро / Доллар США",
            'GBP_USD': "Фунт / Доллар США", 
            'USD_CAD': "Доллар США / Канадский доллар",
            'USD_CHF': "Доллар США / Швейцарский франк",
            'USD_JPY': "Доллар США / Японская иена",
            'AUD_USD': "Австралийский доллар / Доллар США",
            'NZD_USD': "Новозеландский доллар / Доллар США",
            'EUR_GBP': "Евро / Британский фунт",
            'EUR_JPY': "Евро / Японская иена",
            'GBP_JPY': "Британский фунт / Японская иена",
        }
        
        pairs = []
        for symbol in STANDARD_CURRENCY_PAIRS:
            symbol_id = symbol_id_mapping.get(symbol, 0)  # 0 если ID не найден
            description = symbol_descriptions.get(symbol, f"Торговая пара {symbol}")
            
            # По умолчанию включаем только основные пары
            enabled = symbol in ['EUR_USD', 'GBP_USD', 'USD_CAD', 'USD_CHF', 'USD_JPY']
            
            pairs.append(CurrencyPair(
                symbol=symbol,
                symbol_id=symbol_id,
                enabled=enabled,
                priority=1 if enabled else 2,
                pip_size=0.0001,
                min_trade_size=1,
                description=description
            ))
        
        return pairs
    
    @property
    def active_timeframes(self) -> List[Timeframe]:
        return [Timeframe.M5, Timeframe.M15, Timeframe.M30, Timeframe.H1, Timeframe.H4]
    
    @property
    def trading_timeframe(self) -> Timeframe:
        return Timeframe.M5


# Глобальная переменная для хранения экземпляра настроек
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Получение экземпляра настроек (singleton)"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reload_settings() -> Settings:
    """Перезагрузка настроек из файла"""
    global _settings_instance
    _settings_instance = Settings()
    return _settings_instance 
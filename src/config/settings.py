"""
Configuration settings using Pydantic
"""

import os
from typing import List, Dict, Optional, Any
from datetime import time
from pydantic import Field, validator
from pydantic_settings import BaseSettings

from .constants import Timeframe, SystemStatus, NotificationType


class DatabaseConfig(BaseSettings):
    """Конфигурация базы данных"""
    host: str = Field(default="localhost", env="POSTGRES_HOST")
    port: int = Field(default=5432, env="POSTGRES_PORT")
    database: str = Field(default="trading_system", env="POSTGRES_DB")
    user: str = Field(default="postgres", env="POSTGRES_USER")
    password: Optional[str] = Field(default=None, env="POSTGRES_PASSWORD")
    timezone: str = Field(default="UTC", env="POSTGRES_TIMEZONE")
    
    class Config:
        env_file = ".env"


class MT5Config(BaseSettings):
    """Конфигурация MetaTrader5"""
    login: Optional[int] = Field(default=None, env="MT5_LOGIN")
    password: Optional[str] = Field(default=None, env="MT5_PASSWORD")
    server: Optional[str] = Field(default=None, env="MT5_SERVER")
    terminal_path: Optional[str] = Field(default=None, env="MT5_TERMINAL_PATH")
    rate_limit_delay: float = Field(default=0.1, description="Задержка между запросами к MT5")
    
    class Config:
        env_file = ".env"


class TelegramConfig(BaseSettings):
    """Конфигурация Telegram уведомлений"""
    bot_token: Optional[str] = Field(default=None, env="TELEGRAM_TOKEN")
    chat_id: Optional[str] = Field(default=None, env="TELEGRAM_CHAT_ID")
    topics: Dict[str, int] = Field(
        default={
            "trades": 223,
            "system": 1528,
            "analysis": 222,
            "pending_orders": 1662
        },
        env="TELEGRAM_TOPICS"
    )
    retry_attempts: int = Field(default=3, description="Количество попыток отправки")
    
    @validator('topics', pre=True)
    def parse_topics(cls, v):
        if isinstance(v, str):
            # Парсим строку вида "trades:223,system:1528"
            topics = {}
            for item in v.split(','):
                if ':' in item:
                    key, value = item.split(':')
                    topics[key.strip()] = int(value.strip())
            return topics
        return v
    
    class Config:
        env_file = ".env"


class CurrencyPair(BaseSettings):
    """Конфигурация валютной пары"""
    symbol: str = Field(description="Символ валютной пары (например, EUR_USD)")
    symbol_id: int = Field(description="ID символа в базе данных")
    enabled: bool = Field(default=True, description="Активна ли пара")
    priority: int = Field(default=1, description="Приоритет загрузки (1 = высший)")
    pip_size: float = Field(default=0.0001, description="Размер пипса")
    min_trade_size: int = Field(default=1, description="Минимальный размер сделки")
    description: str = Field(description="Описание валютной пары")


class DataUpdateConfig(BaseSettings):
    """Конфигурация обновления данных"""
    update_interval: int = Field(default=60, description="Интервал обновления в секундах")
    candles_to_fetch: int = Field(default=1000, description="Количество свечей для загрузки")
    parallel_downloads: bool = Field(default=True, description="Параллельная загрузка")
    max_workers: int = Field(default=3, description="Максимальное количество потоков")
    max_retries: int = Field(default=5, description="Максимальное количество попыток")
    retry_interval: int = Field(default=30, description="Интервал между попытками в секундах")
    smart_schedule_mode: bool = Field(default=False, description="Умный режим расписания")
    
    # Расписание для умного режима
    timeframe_schedules: Dict[str, Dict[str, Any]] = Field(
        default={
            "M5": {"enabled": True, "interval_minutes": 5},
            "M15": {"enabled": True, "interval_minutes": 15},
            "M30": {"enabled": True, "interval_minutes": 30},
            "H1": {"enabled": True, "interval_minutes": 60},
            "H4": {"enabled": True, "interval_minutes": 240},
            "D1": {"enabled": True, "interval_minutes": 1440},
        }
    )
    
    class Config:
        env_file = ".env"


class LoggingConfig(BaseSettings):
    """Конфигурация логирования"""
    level: str = Field(default="INFO", description="Уровень логирования")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Формат логов"
    )
    max_file_size: int = Field(default=10*1024*1024, description="Максимальный размер файла лога (10MB)")
    backup_count: int = Field(default=5, description="Количество файлов бэкапа")
    
    class Config:
        env_file = ".env"


class MonitoringConfig(BaseSettings):
    """Конфигурация мониторинга"""
    heartbeat_interval: int = Field(default=3600, description="Интервал heartbeat в секундах")
    enable_metrics: bool = Field(default=True, description="Включить метрики")
    metrics_port: int = Field(default=8000, description="Порт для метрик")
    
    class Config:
        env_file = ".env"


class TradingHoursConfig(BaseSettings):
    """Конфигурация торговых часов"""
    start_time: time = Field(default=time(0, 0), description="Время начала торгов (UTC)")
    end_time: time = Field(default=time(23, 59), description="Время окончания торгов (UTC)")
    timezone: str = Field(default="UTC", description="Часовой пояс")
    
    class Config:
        env_file = ".env"


class Settings(BaseSettings):
    """Основные настройки приложения"""
    
    # Конфигурации компонентов
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    mt5: MT5Config = Field(default_factory=MT5Config)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    data_update: DataUpdateConfig = Field(default_factory=DataUpdateConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    trading_hours: TradingHoursConfig = Field(default_factory=TradingHoursConfig)
    
    # Валютные пары
    currency_pairs: List[CurrencyPair] = Field(
        default=[
            CurrencyPair(
                symbol="EUR_USD",
                symbol_id=7,
                enabled=True,
                priority=1,
                pip_size=0.0001,
                min_trade_size=1,
                description="Евро / Доллар США"
            ),
            CurrencyPair(
                symbol="GBP_USD",
                symbol_id=6,
                enabled=True,
                priority=1,
                pip_size=0.0001,
                min_trade_size=1,
                description="Фунт / Доллар США"
            ),
            CurrencyPair(
                symbol="USD_CAD",
                symbol_id=9,
                enabled=True,
                priority=1,
                pip_size=0.0001,
                min_trade_size=1,
                description="Доллар США / Канадский доллар"
            ),
            CurrencyPair(
                symbol="USD_CHF",
                symbol_id=10,
                enabled=True,
                priority=1,
                pip_size=0.0001,
                min_trade_size=1,
                description="Доллар США / Швейцарский франк"
            ),
        ]
    )
    
    # Активные таймфреймы
    active_timeframes: List[Timeframe] = Field(
        default=[Timeframe.M5, Timeframe.M15, Timeframe.M30, Timeframe.H1, Timeframe.H4],
        description="Активные таймфреймы для загрузки"
    )
    
    # Торговый таймфрейм
    trading_timeframe: Timeframe = Field(
        default=Timeframe.M5,
        description="Основной торговый таймфрейм"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton для настроек
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Получение экземпляра настроек (singleton)"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reload_settings() -> Settings:
    """Перезагрузка настроек"""
    global _settings_instance
    _settings_instance = Settings()
    return _settings_instance 
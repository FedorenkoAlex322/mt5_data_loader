"""
Logging configuration and setup
"""

import logging
import logging.handlers
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import structlog

from ..config.settings import get_settings


def setup_logging(config: Dict[str, Any]) -> None:
    """
    Настройка логирования
    
    Args:
        config: Словарь с конфигурацией логирования
    """
    # Настройка structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Настройка базового логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.get('level', 'INFO').upper()))
    
    # Очистка существующих обработчиков
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Создание форматтера
    formatter = logging.Formatter(
        config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Файловый обработчик с ротацией
    try:
        import os
        # Создаем папку logs если её нет
        os.makedirs('logs', exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/trading_system.log',
            maxBytes=config.get('max_file_size', 10*1024*1024),  # 10MB
            backupCount=config.get('backup_count', 5),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not setup file logging: {e}")
    
    # Настройка логгеров для внешних библиотек
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('psycopg2').setLevel(logging.WARNING)
    logging.getLogger('MetaTrader5').setLevel(logging.WARNING)


def setup_utc_logging(config: Dict[str, Any]) -> None:
    """
    Настройка логирования с UTC временем
    
    Args:
        config: Словарь с конфигурацией логирования
    """
    # Настройка structlog с UTC временем
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Настройка базового логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.get('level', 'INFO').upper()))
    
    # Очистка существующих обработчиков
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Создание форматтера с UTC временем
    formatter = logging.Formatter(
        '%(asctime)s UTC - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    formatter.converter = lambda *args: datetime.now(timezone.utc).timetuple()
    
    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Файловый обработчик с ротацией
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/trading_system.log',
            maxBytes=config.get('max_file_size', 10*1024*1024),  # 10MB
            backupCount=config.get('backup_count', 5),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not setup file logging: {e}")
    
    # Настройка логгеров для внешних библиотек
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('psycopg2').setLevel(logging.WARNING)
    logging.getLogger('MetaTrader5').setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Получение логгера с именем
    
    Args:
        name: Имя логгера
        
    Returns:
        Настроенный логгер
    """
    return structlog.get_logger(name)


def get_structured_logger(name: str) -> structlog.BoundLogger:
    """
    Получение структурированного логгера
    
    Args:
        name: Имя логгера
        
    Returns:
        Структурированный логгер
    """
    return structlog.get_logger(name)


def log_function_call(func_name: str, **kwargs):
    """
    Декоратор для логирования вызовов функций
    
    Args:
        func_name: Имя функции
        **kwargs: Аргументы функции
    """
    def decorator(func):
        def wrapper(*args, **kwds):
            logger = get_logger(func.__module__)
            logger.info(
                f"Calling {func_name}",
                function=func_name,
                args=args,
                kwargs=kwds
            )
            try:
                result = func(*args, **kwds)
                logger.info(
                    f"{func_name} completed successfully",
                    function=func_name
                )
                return result
            except Exception as e:
                logger.error(
                    f"{func_name} failed",
                    function=func_name,
                    error=str(e)
                )
                raise
        return wrapper
    return decorator


def setup_default_logging():
    """Настройка логирования по умолчанию"""
    try:
        settings = get_settings()
        setup_logging(settings.logging)
    except Exception as e:
        # Fallback на базовое логирование
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logging.warning(f"Failed to setup structured logging: {e}") 
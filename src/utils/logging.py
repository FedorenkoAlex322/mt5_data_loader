"""
Structured logging configuration
"""

import sys
import logging
from datetime import datetime, timezone
from typing import Optional
from logging.handlers import RotatingFileHandler

import structlog
from structlog.stdlib import LoggerFactory

from ..config.settings import LoggingConfig


def setup_logging(config: LoggingConfig) -> None:
    """
    Настройка структурированного логирования
    
    Args:
        config: Конфигурация логирования
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
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Настройка стандартного logging
    logging.basicConfig(
        format=config.format,
        level=getattr(logging, config.level.upper()),
        handlers=[
            RotatingFileHandler(
                'trading_system.log',
                maxBytes=config.max_file_size,
                backupCount=config.backup_count,
                encoding='utf-8'
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Получить логгер с указанным именем
    
    Args:
        name: Имя логгера
        
    Returns:
        Структурированный логгер
    """
    return structlog.get_logger(name)


class UTCFormatter(logging.Formatter):
    """Форматтер для отображения времени в UTC"""
    
    def formatTime(self, record, datefmt=None):
        # Используем UTC время вместо местного
        ct = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return ct.strftime(datefmt)
        else:
            return ct.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'


def setup_utc_logging(config: LoggingConfig) -> None:
    """
    Настройка логирования с UTC временем
    
    Args:
        config: Конфигурация логирования
    """
    # Создаем UTC formatter
    formatter = UTCFormatter(config.format)
    
    # Настраиваем основной логгер
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.level.upper()))
    
    # File handler с ротацией
    file_handler = RotatingFileHandler(
        'trading_system.log',
        maxBytes=config.max_file_size,
        backupCount=config.backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def log_function_call(func):
    """Декоратор для логирования вызовов функций"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(
            "Function called",
            function=func.__name__,
            args=args,
            kwargs=kwargs
        )
        try:
            result = func(*args, **kwargs)
            logger.debug(
                "Function completed",
                function=func.__name__,
                result_type=type(result).__name__
            )
            return result
        except Exception as e:
            logger.error(
                "Function failed",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    return wrapper


def log_execution_time(func):
    """Декоратор для логирования времени выполнения функций"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = datetime.now(timezone.utc)
        
        logger.debug(
            "Function execution started",
            function=func.__name__,
            start_time=start_time
        )
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.now(timezone.utc)
            execution_time = (end_time - start_time).total_seconds()
            
            logger.debug(
                "Function execution completed",
                function=func.__name__,
                execution_time_seconds=execution_time,
                end_time=end_time
            )
            
            return result
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            execution_time = (end_time - start_time).total_seconds()
            
            logger.error(
                "Function execution failed",
                function=func.__name__,
                execution_time_seconds=execution_time,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    return wrapper 
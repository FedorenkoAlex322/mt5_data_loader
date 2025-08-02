#!/usr/bin/env python3
"""
Script for running real-time data updater
"""

import sys
import os
import signal
from pathlib import Path

# Добавляем корень проекта в путь для импорта
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import get_settings
from src.utils.logging import setup_logging, get_logger
from src.data.real_time_updater import RealTimeDataUpdater


def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    logger = get_logger(__name__)
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Основная функция"""
    logger = None
    try:
        # Настройка обработки сигналов
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Загрузка настроек
        print("Loading settings...")
        settings = get_settings()
        
        # Настройка логирования
        print("Setting up logging...")
        setup_logging(settings.logging)
        logger = get_logger(__name__)
        
        logger.info("Starting real-time data updater")
        logger.info(f"Configuration loaded: {len(settings.currency_pairs)} pairs, {len(settings.active_timeframes)} timeframes")
        
        # Создание и запуск обновлятеля данных
        print("Initializing data updater...")
        updater = RealTimeDataUpdater(settings)
        print("Starting data updater...")
        updater.run()
        
    except KeyboardInterrupt:
        if logger:
            logger.info("Shutdown requested by user")
        else:
            print("Shutdown requested by user")
    except Exception as e:
        if logger:
            logger.error("Critical error", error=str(e))
        else:
            print(f"Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
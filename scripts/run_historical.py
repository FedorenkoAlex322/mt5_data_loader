#!/usr/bin/env python3
"""
Script for running historical data loader
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Добавляем корень проекта в путь для импорта
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import get_settings
from src.utils.logging import setup_logging, get_logger
from src.data.historical_loader import HistoricalDataLoader


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description="Historical data loader for MT5")
    
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date (YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--end-date", 
        type=str,
        required=True,
        help="End date (YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--symbols",
        type=str,
        nargs="+",
        help="Specific symbols to load (default: all enabled)"
    )
    
    parser.add_argument(
        "--timeframes",
        type=str,
        nargs="+",
        help="Specific timeframes to load (default: all active)"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel processing"
    )
    
    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
        help="Maximum number of parallel workers"
    )
    
    return parser.parse_args()


def main():
    """Основная функция"""
    try:
        # Парсинг аргументов
        args = parse_arguments()
        
        # Загрузка настроек
        settings = get_settings()
        
        # Настройка логирования
        setup_logging(settings.logging)
        logger = get_logger(__name__)
        
        # Парсинг дат
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        
        # Фильтрация символов и таймфреймов если указаны
        if args.symbols:
            settings.currency_pairs = [p for p in settings.currency_pairs if p.symbol in args.symbols]
        
        if args.timeframes:
            from src.config.constants import Timeframe
            timeframe_map = {tf.value: tf for tf in Timeframe}
            settings.active_timeframes = [timeframe_map[tf] for tf in args.timeframes if tf in timeframe_map]
        
        logger.info("Starting historical data loader")
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"Symbols: {[p.symbol for p in settings.currency_pairs]}")
        logger.info(f"Timeframes: {[tf.value for tf in settings.active_timeframes]}")
        logger.info(f"Parallel: {args.parallel}")
        
        # Создание и запуск загрузчика
        loader = HistoricalDataLoader(
            settings=settings,
            start_date=start_date,
            end_date=end_date,
            parallel=args.parallel,
            max_workers=args.max_workers
        )
        
        loader.run()
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error("Critical error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main() 
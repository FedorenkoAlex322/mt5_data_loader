"""
Test imports to ensure all modules can be imported correctly
"""

import sys
import os
from pathlib import Path

# Добавляем корень проекта в путь для импорта
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_config_imports():
    """Тест импортов конфигурации"""
    try:
        from src.config.settings import Settings, get_settings, CurrencyPair
        from src.config.constants import Timeframe, SystemStatus, NotificationType
        print("✅ Config imports successful")
        return True
    except Exception as e:
        print(f"❌ Config imports failed: {e}")
        return False


def test_core_imports():
    """Тест импортов основных компонентов"""
    try:
        from src.core.database import DatabaseManager
        from src.core.mt5_client import MT5Client
        from src.core.telegram_notifier import TelegramNotifier
        print("✅ Core imports successful")
        return True
    except Exception as e:
        print(f"❌ Core imports failed: {e}")
        return False


def test_data_imports():
    """Тест импортов обработки данных"""
    try:
        from src.data.real_time_updater import RealTimeDataUpdater
        from src.data.historical_loader import HistoricalDataLoader
        from src.data.candle_processor import CandleProcessor
        print("✅ Data imports successful")
        return True
    except Exception as e:
        print(f"❌ Data imports failed: {e}")
        return False


def test_utils_imports():
    """Тест импортов утилит"""
    try:
        from src.utils.logging import setup_logging, get_logger
        from src.utils.helpers import parse_datetime, format_datetime, get_utc_now
        print("✅ Utils imports successful")
        return True
    except Exception as e:
        print(f"❌ Utils imports failed: {e}")
        return False


def test_package_imports():
    """Тест импортов из основного пакета"""
    try:
        from src import (
            Settings, get_settings, CurrencyPair, Timeframe, SystemStatus,
            DatabaseManager, MT5Client, TelegramNotifier,
            RealTimeDataUpdater, HistoricalDataLoader, CandleProcessor,
            setup_logging, get_logger
        )
        print("✅ Package imports successful")
        return True
    except Exception as e:
        print(f"❌ Package imports failed: {e}")
        return False


def test_basic_settings():
    """Тест базового создания настроек без валидации"""
    try:
        from src.config.settings import Settings
        
        # Создаем настройки с минимальными данными
        settings = Settings(
            postgres_password="test",
            mt5_terminal_path="test",
            telegram_token="test",
            telegram_chat_id="test"
        )
        print(f"✅ Basic settings created: {len(settings.currency_pairs)} pairs, {len(settings.active_timeframes)} timeframes")
        return True
    except Exception as e:
        print(f"❌ Basic settings creation failed: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🧪 Testing imports...")
    print("=" * 50)
    
    tests = [
        test_config_imports,
        test_core_imports,
        test_data_imports,
        test_utils_imports,
        test_package_imports,
        test_basic_settings
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Project structure is correct.")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
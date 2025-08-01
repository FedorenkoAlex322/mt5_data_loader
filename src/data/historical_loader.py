"""
Historical data loader for MT5
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from ..config.settings import Settings, CurrencyPair
from ..config.constants import Timeframe
from ..core.database import DatabaseManager
from ..core.mt5_client import MT5Client
from ..core.telegram_notifier import TelegramNotifier
from ..data.candle_processor import CandleProcessor
from ..utils.logging import get_logger


@dataclass
class LoadResult:
    """Результат загрузки для одной комбинации"""
    symbol: str
    timeframe: Timeframe
    success: bool
    candles_count: int
    error_message: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class HistoricalDataLoader:
    """Загрузчик исторических данных"""
    
    def __init__(
        self,
        settings: Settings,
        start_date: datetime,
        end_date: datetime,
        parallel: bool = False,
        max_workers: int = 3
    ):
        self.settings = settings
        self.start_date = start_date
        self.end_date = end_date
        self.parallel = parallel
        self.max_workers = max_workers
        
        # Инициализация компонентов
        self.logger = get_logger(__name__)
        self.db_manager = DatabaseManager(settings.database)
        self.mt5_client = MT5Client(settings.mt5)
        self.telegram = TelegramNotifier(settings.telegram)
        self.candle_processor = CandleProcessor()
        
        # Статистика
        self.stats = {
            'total_combinations': 0,
            'successful_combinations': 0,
            'failed_combinations': 0,
            'total_candles': 0,
            'start_time': None,
            'end_time': None
        }
    
    def run(self) -> None:
        """Основной метод запуска загрузки"""
        self.logger.info("Starting historical data loader")
        self.logger.info(f"Date range: {self.start_date} to {self.end_date}")
        
        # Инициализация статистики
        self.stats['start_time'] = datetime.now()
        
        # Проверка подключений
        if not self._check_connections():
            self.logger.error("Connection check failed")
            return
        
        # Создание комбинаций для загрузки
        combinations = self._create_combinations()
        self.stats['total_combinations'] = len(combinations)
        
        self.logger.info(f"Created {len(combinations)} combinations for loading")
        
        # Отправка уведомления о начале
        self._send_start_notification(combinations)
        
        # Загрузка данных
        if self.parallel:
            results = self._load_parallel(combinations)
        else:
            results = self._load_sequential(combinations)
        
        # Обработка результатов
        self._process_results(results)
        
        # Завершение
        self.stats['end_time'] = datetime.now()
        self._send_completion_notification()
        
        self.logger.info("Historical data loading completed")
        self._print_summary()
    
    def _check_connections(self) -> bool:
        """Проверка подключений к БД и MT5"""
        try:
            # Проверка БД
            if not self.db_manager.test_connection():
                self.logger.error("Database connection test failed")
                return False
            
            # Проверка MT5
            if not self.mt5_client.test_connection():
                self.logger.error("MT5 connection test failed")
                return False
            
            # Проверка Telegram
            if not self.telegram.test_connection():
                self.logger.warning("Telegram connection test failed")
            
            self.logger.info("All connections verified")
            return True
            
        except Exception as e:
            self.logger.error("Connection check failed", error=str(e))
            return False
    
    def _create_combinations(self) -> List[Dict[str, Any]]:
        """Создание комбинаций пар/таймфреймов для загрузки"""
        combinations = []
        
        enabled_pairs = [p for p in self.settings.currency_pairs if p.enabled]
        
        for pair in enabled_pairs:
            for timeframe in self.settings.active_timeframes:
                combination = {
                    'symbol': pair.symbol,
                    'symbol_id': pair.symbol_id,
                    'timeframe': timeframe,
                    'timeframe_id': timeframe.id,
                    'priority': pair.priority
                }
                combinations.append(combination)
        
        # Сортировка по приоритету
        combinations.sort(key=lambda x: x['priority'])
        
        return combinations
    
    def _load_sequential(self, combinations: List[Dict[str, Any]]) -> List[LoadResult]:
        """Последовательная загрузка данных"""
        results = []
        
        for i, combination in enumerate(combinations, 1):
            self.logger.info(
                f"Loading {i}/{len(combinations)}: {combination['symbol']} {combination['timeframe'].value}"
            )
            
            result = self._load_single_combination(combination)
            results.append(result)
            
            # Небольшая пауза между запросами
            time.sleep(0.1)
        
        return results
    
    def _load_parallel(self, combinations: List[Dict[str, Any]]) -> List[LoadResult]:
        """Параллельная загрузка данных"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Создаем задачи
            future_to_combination = {
                executor.submit(self._load_single_combination, combo): combo 
                for combo in combinations
            }
            
            # Обрабатываем результаты по мере завершения
            for i, future in enumerate(as_completed(future_to_combination), 1):
                combination = future_to_combination[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    self.logger.info(
                        f"Completed {i}/{len(combinations)}: {combination['symbol']} {combination['timeframe'].value}"
                    )
                    
                except Exception as e:
                    self.logger.error(
                        f"Failed to load {combination['symbol']} {combination['timeframe'].value}",
                        error=str(e)
                    )
                    
                    result = LoadResult(
                        symbol=combination['symbol'],
                        timeframe=combination['timeframe'],
                        success=False,
                        candles_count=0,
                        error_message=str(e)
                    )
                    results.append(result)
        
        return results
    
    def _load_single_combination(self, combination: Dict[str, Any]) -> LoadResult:
        """Загрузка данных для одной комбинации"""
        symbol = combination['symbol']
        timeframe = combination['timeframe']
        symbol_id = combination['symbol_id']
        
        try:
            self.logger.debug(
                f"Loading {symbol} {timeframe.value} from {self.start_date} to {self.end_date}"
            )
            
            # Загрузка свечей из MT5
            candles = self.mt5_client.fetch_candles(
                symbol=symbol,
                timeframe=timeframe,
                from_time=self.start_date,
                to_time=self.end_date
            )
            
            if not candles:
                self.logger.warning(f"No candles received for {symbol} {timeframe.value}")
                return LoadResult(
                    symbol=symbol,
                    timeframe=timeframe,
                    success=True,
                    candles_count=0,
                    start_time=self.start_date,
                    end_time=self.end_date
                )
            
            # Валидация и фильтрация свечей
            valid_candles = []
            for candle in candles:
                if self.candle_processor.validate_candle_data(candle):
                    valid_candles.append(candle)
            
            if not valid_candles:
                self.logger.warning(f"No valid candles for {symbol} {timeframe.value}")
                return LoadResult(
                    symbol=symbol,
                    timeframe=timeframe,
                    success=True,
                    candles_count=0,
                    start_time=self.start_date,
                    end_time=self.end_date
                )
            
            # Удаление дубликатов
            unique_candles = self.candle_processor.remove_duplicates(valid_candles)
            
            # Обработка свечей для БД
            processed_candles = self.candle_processor.process_mt5_candles(
                unique_candles, 
                symbol_id
            )
            
            # Конвертация в формат для БД
            db_tuples = self.candle_processor.convert_to_db_tuples(processed_candles)
            
            # Вставка в БД
            inserted_count = self.db_manager.insert_candles_batch(db_tuples)
            
            # Статистика по времени
            timestamps = [c.timestamp for c in unique_candles]
            start_time = min(timestamps)
            end_time = max(timestamps)
            
            self.logger.info(
                f"Loaded {symbol} {timeframe.value}: {inserted_count} candles",
                symbol=symbol,
                timeframe=timeframe.value,
                candles_count=inserted_count,
                time_range=f"{start_time} - {end_time}"
            )
            
            return LoadResult(
                symbol=symbol,
                timeframe=timeframe,
                success=True,
                candles_count=inserted_count,
                start_time=start_time,
                end_time=end_time
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to load {symbol} {timeframe.value}",
                error=str(e)
            )
            
            return LoadResult(
                symbol=symbol,
                timeframe=timeframe,
                success=False,
                candles_count=0,
                error_message=str(e)
            )
    
    def _process_results(self, results: List[LoadResult]) -> None:
        """Обработка результатов загрузки"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        self.stats['successful_combinations'] = len(successful)
        self.stats['failed_combinations'] = len(failed)
        self.stats['total_candles'] = sum(r.candles_count for r in successful)
        
        # Логирование результатов
        self.logger.info(
            "Loading results",
            total_combinations=len(results),
            successful=len(successful),
            failed=len(failed),
            total_candles=self.stats['total_candles']
        )
        
        # Детали по неудачным загрузкам
        if failed:
            self.logger.warning("Failed combinations:")
            for result in failed:
                self.logger.warning(
                    f"  {result.symbol} {result.timeframe.value}: {result.error_message}"
                )
    
    def _send_start_notification(self, combinations: List[Dict[str, Any]]) -> None:
        """Отправка уведомления о начале загрузки"""
        try:
            symbols = list(set(c['symbol'] for c in combinations))
            timeframes = list(set(c['timeframe'].value for c in combinations))
            
            message = (
                f"📥 <b>Начало загрузки исторических данных</b>\n"
                f"📅 Период: {self.start_date.strftime('%Y-%m-%d')} - {self.end_date.strftime('%Y-%m-%d')}\n"
                f"💱 Пар: {len(symbols)} ({', '.join(symbols[:5])}{'...' if len(symbols) > 5 else ''})\n"
                f"📊 Таймфреймы: {', '.join(timeframes)}\n"
                f"🔢 Комбинаций: {len(combinations)}\n"
                f"⚡ Режим: {'Параллельный' if self.parallel else 'Последовательный'}"
            )
            
            self.telegram.send_message(message, "system")
            
        except Exception as e:
            self.logger.error("Failed to send start notification", error=str(e))
    
    def _send_completion_notification(self) -> None:
        """Отправка уведомления о завершении загрузки"""
        try:
            duration = self.stats['end_time'] - self.stats['start_time']
            
            message = (
                f"✅ <b>Загрузка исторических данных завершена</b>\n"
                f"⏱️ Время выполнения: {str(duration).split('.')[0]}\n"
                f"📊 Результаты:\n"
                f"  • Комбинаций: {self.stats['total_combinations']}\n"
                f"  • Успешных: {self.stats['successful_combinations']}\n"
                f"  • Ошибок: {self.stats['failed_combinations']}\n"
                f"  • Свечей: {self.stats['total_candles']:,}"
            )
            
            self.telegram.send_message(message, "system")
            
        except Exception as e:
            self.logger.error("Failed to send completion notification", error=str(e))
    
    def _print_summary(self) -> None:
        """Вывод сводки результатов"""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        print("\n" + "="*60)
        print("📊 СВОДКА ЗАГРУЗКИ ИСТОРИЧЕСКИХ ДАННЫХ")
        print("="*60)
        print(f"📅 Период: {self.start_date.strftime('%Y-%m-%d')} - {self.end_date.strftime('%Y-%m-%d')}")
        print(f"⏱️ Время выполнения: {str(duration).split('.')[0]}")
        print(f"🔢 Всего комбинаций: {self.stats['total_combinations']}")
        print(f"✅ Успешных: {self.stats['successful_combinations']}")
        print(f"❌ Ошибок: {self.stats['failed_combinations']}")
        print(f"💾 Загружено свечей: {self.stats['total_candles']:,}")
        
        if self.stats['total_combinations'] > 0:
            success_rate = (self.stats['successful_combinations'] / self.stats['total_combinations']) * 100
            print(f"📈 Процент успеха: {success_rate:.1f}%")
        
        print("="*60)
    
    def close(self) -> None:
        """Закрытие соединений"""
        try:
            self.db_manager.close()
            self.mt5_client.close()
            self.telegram.close()
        except Exception as e:
            self.logger.error("Error during cleanup", error=str(e))
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 
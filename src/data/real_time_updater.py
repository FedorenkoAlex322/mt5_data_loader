"""
Real-time data updater for MT5
"""

import time
import signal
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from ..config.settings import Settings, CurrencyPair
from ..config.constants import Timeframe, SystemStatus
from ..core.database import DatabaseManager
from ..core.mt5_client import MT5Client
from ..core.telegram_notifier import TelegramNotifier
from ..data.candle_processor import CandleProcessor
from ..utils.logging import get_logger
from ..utils.helpers import get_utc_now, calculate_seconds_until_next_timeframe


@dataclass
class UpdateResult:
    """Результат обновления для одной комбинации"""
    symbol: str
    timeframe: Timeframe
    success: bool
    new_candles: int
    error_message: Optional[str] = None
    last_candle_time: Optional[datetime] = None


class RealTimeDataUpdater:
    """Обновлятель данных в реальном времени"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Инициализация компонентов
        self.logger = get_logger(__name__)
        self.db_manager = DatabaseManager(settings.database)
        self.mt5_client = MT5Client(settings.mt5)
        self.telegram = TelegramNotifier(settings.telegram)
        self.candle_processor = CandleProcessor()
        
        # Состояние системы
        self.running = False
        self.status = SystemStatus.STOPPED
        
        # Статистика
        self.stats = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'total_candles': 0,
            'start_time': None,
            'last_update_time': None,
            'pair_stats': {}
        }
        
        # Настройка обработки сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def run(self) -> None:
        """Основной цикл работы"""
        self.logger.info("Starting real-time data updater")
        
        # Инициализация статистики
        self.stats['start_time'] = get_utc_now()
        
        # Проверка подключений
        if not self._check_connections():
            self.logger.error("Connection check failed")
            return
        
        # Отправка уведомления о запуске
        self._send_start_notification()
        
        # Выполнение первоначальной загрузки истории
        self._initial_history_download()
        
        # Основной цикл обновления
        self.running = True
        self.status = SystemStatus.RUNNING
        
        failed_attempts = 0
        max_retries = self.settings.data_update.max_retries
        last_heartbeat = get_utc_now()
        heartbeat_interval = self.settings.monitoring.heartbeat_interval
        
        while self.running:
            try:
                cycle_start = get_utc_now()
                
                # Выбор режима обновления
                if self.settings.data_update.smart_schedule_mode:
                    success = self._smart_update_cycle()
                else:
                    success = self._update_cycle()
                
                # Обновление статистики
                if success:
                    failed_attempts = 0
                    self.stats['successful_updates'] += 1
                else:
                    failed_attempts += 1
                    self.stats['failed_updates'] += 1
                
                self.stats['total_updates'] += 1
                self.stats['last_update_time'] = get_utc_now()
                
                # Проверка максимального количества ошибок
                if failed_attempts >= max_retries:
                    self.logger.error(f"Reached maximum failed attempts ({max_retries})")
                    self._send_error_notification(f"Maximum failed attempts: {max_retries}")
                    break
                
                # Heartbeat
                if (get_utc_now() - last_heartbeat).total_seconds() >= heartbeat_interval:
                    self._send_heartbeat()
                    last_heartbeat = get_utc_now()
                
                # Ожидание до следующего обновления
                if success:
                    if self.settings.data_update.smart_schedule_mode:
                        wait_seconds = self._calculate_next_schedule_wait()
                        self.logger.info(f"Waiting {wait_seconds}s until next schedule")
                        time.sleep(wait_seconds)
                    else:
                        time.sleep(self.settings.data_update.update_interval)
                else:
                    retry_delay = self.settings.data_update.retry_interval * min(failed_attempts, 5)
                    self.logger.warning(f"Waiting {retry_delay}s after error (attempt {failed_attempts}/{max_retries})")
                    time.sleep(retry_delay)
                
            except KeyboardInterrupt:
                self.logger.info("Received shutdown signal")
                break
            except Exception as e:
                self.logger.error("Unexpected error in update cycle", error=str(e))
                failed_attempts += 1
                time.sleep(self.settings.data_update.retry_interval)
        
        # Завершение работы
        self._shutdown()
    
    def _check_connections(self) -> bool:
        """Проверка подключений"""
        try:
            if not self.db_manager.test_connection():
                self.logger.error("Database connection test failed")
                return False
            
            if not self.mt5_client.test_connection():
                self.logger.error("MT5 connection test failed")
                return False
            
            if not self.telegram.test_connection():
                self.logger.warning("Telegram connection test failed")
            
            self.logger.info("All connections verified")
            return True
            
        except Exception as e:
            self.logger.error("Connection check failed", error=str(e))
            return False
    
    def _create_combinations(self) -> List[Dict[str, Any]]:
        """Создание комбинаций для обновления"""
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
    
    def _update_cycle(self) -> bool:
        """Один цикл обновления"""
        try:
            cycle_start = get_utc_now()
            
            # Создание комбинаций
            combinations = self._create_combinations()
            
            # Обновление данных
            if self.settings.data_update.parallel_downloads:
                results = self._update_parallel(combinations)
            else:
                results = self._update_sequential(combinations)
            
            # Обработка результатов
            self._process_update_results(results)
            
            # Отправка уведомления
            cycle_duration = (get_utc_now() - cycle_start).total_seconds()
            self._send_update_notification(results, cycle_duration)
            
            return True
            
        except Exception as e:
            self.logger.error("Update cycle failed", error=str(e))
            return False
    
    def _smart_update_cycle(self) -> bool:
        """Умный цикл обновления с расписанием по таймфреймам"""
        try:
            cycle_start = get_utc_now()
            
            # Определение активных таймфреймов для текущего времени
            active_timeframes = self._get_active_timeframes_now()
            
            if not active_timeframes:
                self.logger.debug("No active timeframes for current time")
                return True
            
            # Группировка комбинаций по таймфреймам
            combinations = self._create_combinations()
            grouped_combinations = self._group_combinations_by_timeframes(combinations, active_timeframes)
            
            # Обновление по группам
            timeframe_results = []
            for timeframe in active_timeframes:
                if timeframe in grouped_combinations:
                    result = self._update_timeframe_group(timeframe, grouped_combinations[timeframe])
                    timeframe_results.append(result)
            
            # Отправка уведомления
            cycle_duration = (get_utc_now() - cycle_start).total_seconds()
            self._send_smart_update_notification(active_timeframes, timeframe_results, cycle_duration)
            
            return True
            
        except Exception as e:
            self.logger.error("Smart update cycle failed", error=str(e))
            return False
    
    def _update_sequential(self, combinations: List[Dict[str, Any]]) -> List[UpdateResult]:
        """Последовательное обновление"""
        results = []
        
        for i, combination in enumerate(combinations, 1):
            self.logger.debug(
                f"Updating {i}/{len(combinations)}: {combination['symbol']} {combination['timeframe'].value}"
            )
            
            result = self._update_single_combination(combination)
            results.append(result)
            
            # Небольшая пауза между запросами
            time.sleep(0.1)
        
        return results
    
    def _update_parallel(self, combinations: List[Dict[str, Any]]) -> List[UpdateResult]:
        """Параллельное обновление"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.settings.data_update.max_workers) as executor:
            future_to_combination = {
                executor.submit(self._update_single_combination, combo): combo 
                for combo in combinations
            }
            
            for future in as_completed(future_to_combination):
                combination = future_to_combination[future]
                
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(
                        f"Failed to update {combination['symbol']} {combination['timeframe'].value}",
                        error=str(e)
                    )
                    
                    result = UpdateResult(
                        symbol=combination['symbol'],
                        timeframe=combination['timeframe'],
                        success=False,
                        new_candles=0,
                        error_message=str(e)
                    )
                    results.append(result)
        
        return results
    
    def _update_single_combination(self, combination: Dict[str, Any]) -> UpdateResult:
        """Обновление одной комбинации"""
        symbol = combination['symbol']
        timeframe = combination['timeframe']
        symbol_id = combination['symbol_id']
        
        try:
            # Получение времени последней свечи в БД
            last_db_time = self.db_manager.get_last_candle_time(symbol_id, timeframe.id)
            
            # Определение времени для запроса
            from_time = last_db_time if last_db_time else (get_utc_now() - timedelta(days=1))
            
            # Загрузка свечей из MT5
            candles = self.mt5_client.fetch_candles(
                symbol=symbol,
                timeframe=timeframe,
                from_time=from_time
            )
            
            if not candles:
                return UpdateResult(
                    symbol=symbol,
                    timeframe=timeframe,
                    success=True,
                    new_candles=0,
                    last_candle_time=last_db_time
                )
            
            # Фильтрация новых свечей
            new_candles = self.candle_processor.filter_new_candles(candles, last_db_time)
            
            if not new_candles:
                return UpdateResult(
                    symbol=symbol,
                    timeframe=timeframe,
                    success=True,
                    new_candles=0,
                    last_candle_time=last_db_time
                )
            
            # Валидация свечей
            valid_candles = []
            for candle in new_candles:
                if self.candle_processor.validate_candle_data(candle):
                    valid_candles.append(candle)
            
            if not valid_candles:
                return UpdateResult(
                    symbol=symbol,
                    timeframe=timeframe,
                    success=True,
                    new_candles=0,
                    last_candle_time=last_db_time
                )
            
            # Обработка и вставка в БД
            processed_candles = self.candle_processor.process_mt5_candles(valid_candles, symbol_id)
            db_tuples = self.candle_processor.convert_to_db_tuples(processed_candles)
            inserted_count = self.db_manager.insert_candles_batch(db_tuples)
            
            # Обновление статистики
            self._update_pair_stats(symbol, timeframe, inserted_count)
            
            # Новое время последней свечи
            new_last_time = max(c.timestamp for c in valid_candles)
            
            self.logger.info(
                f"Updated {symbol} {timeframe.value}: {inserted_count} new candles",
                symbol=symbol,
                timeframe=timeframe.value,
                new_candles=inserted_count,
                last_time=new_last_time
            )
            
            return UpdateResult(
                symbol=symbol,
                timeframe=timeframe,
                success=True,
                new_candles=inserted_count,
                last_candle_time=new_last_time
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to update {symbol} {timeframe.value}",
                error=str(e)
            )
            
            return UpdateResult(
                symbol=symbol,
                timeframe=timeframe,
                success=False,
                new_candles=0,
                error_message=str(e)
            )
    
    def _get_active_timeframes_now(self) -> List[Timeframe]:
        """Получение активных таймфреймов для текущего времени"""
        active_timeframes = []
        current_time = get_utc_now()
        
        for timeframe in self.settings.active_timeframes:
            if timeframe.name in self.settings.data_update.timeframe_schedules:
                schedule = self.settings.data_update.timeframe_schedules[timeframe.name]
                
                if schedule.get('enabled', True):
                    # Проверяем нужно ли обновлять этот таймфрейм сейчас
                    if self._should_update_timeframe_now(timeframe, current_time):
                        active_timeframes.append(timeframe)
        
        return active_timeframes
    
    def _should_update_timeframe_now(self, timeframe: Timeframe, current_time: datetime) -> bool:
        """Проверка нужно ли обновлять таймфрейм сейчас"""
        if timeframe.name not in self.settings.data_update.timeframe_schedules:
            return False
        
        schedule = self.settings.data_update.timeframe_schedules[timeframe.name]
        interval_minutes = schedule.get('interval_minutes', timeframe.minutes)
        
        # Вычисляем время до следующего обновления
        wait_seconds = calculate_seconds_until_next_timeframe(timeframe, current_time)
        
        # Если до следующего обновления меньше минуты, считаем что нужно обновлять
        return wait_seconds < 60
    
    def _group_combinations_by_timeframes(
        self, 
        combinations: List[Dict[str, Any]], 
        active_timeframes: List[Timeframe]
    ) -> Dict[Timeframe, List[Dict[str, Any]]]:
        """Группировка комбинаций по таймфреймам"""
        grouped = {}
        
        for combination in combinations:
            timeframe = combination['timeframe']
            if timeframe in active_timeframes:
                if timeframe not in grouped:
                    grouped[timeframe] = []
                grouped[timeframe].append(combination)
        
        return grouped
    
    def _update_timeframe_group(
        self, 
        timeframe: Timeframe, 
        combinations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Обновление группы комбинаций одного таймфрейма"""
        results = self._update_parallel(combinations)
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        total_candles = sum(r.new_candles for r in successful)
        
        return {
            'timeframe': timeframe,
            'combinations_count': len(combinations),
            'successful_count': len(successful),
            'failed_count': len(failed),
            'total_candles': total_candles,
            'results': results
        }
    
    def _process_update_results(self, results: List[UpdateResult]) -> None:
        """Обработка результатов обновления"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        total_candles = sum(r.new_candles for r in successful)
        self.stats['total_candles'] += total_candles
        
        self.logger.info(
            "Update cycle completed",
            total_combinations=len(results),
            successful=len(successful),
            failed=len(failed),
            new_candles=total_candles
        )
    
    def _update_pair_stats(self, symbol: str, timeframe: Timeframe, candles_count: int) -> None:
        """Обновление статистики по паре"""
        pair_key = f"{symbol}_{timeframe.value}"
        
        if pair_key not in self.stats['pair_stats']:
            self.stats['pair_stats'][pair_key] = {
                'total_candles': 0,
                'last_update': None,
                'errors': 0
            }
        
        self.stats['pair_stats'][pair_key]['total_candles'] += candles_count
        self.stats['pair_stats'][pair_key]['last_update'] = get_utc_now()
    
    def _initial_history_download(self) -> None:
        """Первоначальная загрузка истории"""
        self.logger.info("Performing initial history download")
        
        try:
            # Загружаем данные за последние N дней для всех комбинаций
            days_back = 7  # Можно вынести в настройки
            start_date = get_utc_now() - timedelta(days=days_back)
            
            combinations = self._create_combinations()
            
            for combination in combinations:
                symbol = combination['symbol']
                timeframe = combination['timeframe']
                symbol_id = combination['symbol_id']
                
                # Проверяем есть ли уже данные
                existing_count = self.db_manager.get_candles_count(symbol_id, timeframe.id)
                
                if existing_count == 0:
                    self.logger.info(f"Loading initial history for {symbol} {timeframe.value}")
                    
                    candles = self.mt5_client.fetch_candles(
                        symbol=symbol,
                        timeframe=timeframe,
                        from_time=start_date,
                        to_time=get_utc_now()
                    )
                    
                    if candles:
                        valid_candles = [c for c in candles if self.candle_processor.validate_candle_data(c)]
                        processed_candles = self.candle_processor.process_mt5_candles(valid_candles, symbol_id)
                        db_tuples = self.candle_processor.convert_to_db_tuples(processed_candles)
                        inserted_count = self.db_manager.insert_candles_batch(db_tuples)
                        
                        self.logger.info(f"Loaded {inserted_count} initial candles for {symbol} {timeframe.value}")
                
                time.sleep(0.1)  # Небольшая пауза
            
            self.logger.info("Initial history download completed")
            
        except Exception as e:
            self.logger.error("Initial history download failed", error=str(e))
    
    def _calculate_next_schedule_wait(self) -> int:
        """Вычисление времени ожидания до следующего расписания"""
        current_time = get_utc_now()
        min_wait = float('inf')
        
        for timeframe in self.settings.active_timeframes:
            if timeframe.name in self.settings.data_update.timeframe_schedules:
                wait_seconds = calculate_seconds_until_next_timeframe(timeframe, current_time)
                min_wait = min(min_wait, wait_seconds)
        
        return int(min_wait) if min_wait != float('inf') else 60
    
    def _send_start_notification(self) -> None:
        """Отправка уведомления о запуске"""
        try:
            combinations = self._create_combinations()
            symbols = list(set(c['symbol'] for c in combinations))
            timeframes = list(set(c['timeframe'].value for c in combinations))
            
            system_info = {
                'start_time': get_utc_now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'pairs': ', '.join(symbols[:5]) + ('...' if len(symbols) > 5 else ''),
                'timeframes': ', '.join(timeframes),
                'combinations_count': len(combinations),
                'mode': 'Smart Schedule' if self.settings.data_update.smart_schedule_mode else f'Fixed {self.settings.data_update.update_interval}s'
            }
            
            self.telegram.send_system_start(system_info)
            
        except Exception as e:
            self.logger.error("Failed to send start notification", error=str(e))
    
    def _send_update_notification(self, results: List[UpdateResult], duration: float) -> None:
        """Отправка уведомления об обновлении"""
        try:
            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]
            total_candles = sum(r.new_candles for r in successful)
            
            update_info = {
                'timestamp': get_utc_now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'duration': f"{duration:.1f}s",
                'new_candles': total_candles,
                'successful_pairs': len(successful),
                'errors': len(failed)
            }
            
            self.telegram.send_update_notification(update_info)
            
        except Exception as e:
            self.logger.error("Failed to send update notification", error=str(e))
    
    def _send_smart_update_notification(
        self, 
        active_timeframes: List[Timeframe], 
        timeframe_results: List[Dict[str, Any]], 
        duration: float
    ) -> None:
        """Отправка уведомления об умном обновлении"""
        try:
            total_candles = sum(r['total_candles'] for r in timeframe_results)
            total_combinations = sum(r['combinations_count'] for r in timeframe_results)
            successful_combinations = sum(r['successful_count'] for r in timeframe_results)
            
            message = (
                f"📈 <b>Умное обновление данных</b>\n"
                f"🕐 {get_utc_now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                f"⏱️ Длительность: {duration:.1f}s\n"
                f"📊 Активные таймфреймы: {', '.join(tf.value for tf in active_timeframes)}\n"
                f"💾 Новых свечей: {total_candles}\n"
                f"✅ Успешных комбинаций: {successful_combinations}/{total_combinations}"
            )
            
            self.telegram.send_message(message, "system")
            
        except Exception as e:
            self.logger.error("Failed to send smart update notification", error=str(e))
    
    def _send_heartbeat(self) -> None:
        """Отправка heartbeat"""
        try:
            uptime = get_utc_now() - self.stats['start_time']
            
            stats = {
                'timestamp': get_utc_now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'uptime': str(uptime).split('.')[0],
                'cycles': self.stats['total_updates'],
                'successful_cycles': self.stats['successful_updates'],
                'candles_last_hour': self._get_candles_last_hour(),
                'active_pairs': len(self.stats['pair_stats'])
            }
            
            self.telegram.send_heartbeat(stats)
            
        except Exception as e:
            self.logger.error("Failed to send heartbeat", error=str(e))
    
    def _send_error_notification(self, error_message: str) -> None:
        """Отправка уведомления об ошибке"""
        try:
            error_info = {
                'timestamp': get_utc_now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'error_type': 'System Error',
                'message': error_message,
                'component': 'RealTimeDataUpdater'
            }
            
            self.telegram.send_error_notification(error_info)
            
        except Exception as e:
            self.logger.error("Failed to send error notification", error=str(e))
    
    def _get_candles_last_hour(self) -> int:
        """Получение количества свечей за последний час"""
        try:
            one_hour_ago = get_utc_now() - timedelta(hours=1)
            total_candles = 0
            
            for pair_key, stats in self.stats['pair_stats'].items():
                if stats['last_update'] and stats['last_update'] > one_hour_ago:
                    total_candles += stats['total_candles']
            
            return total_candles
        except Exception:
            return 0
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def _shutdown(self) -> None:
        """Завершение работы"""
        self.logger.info("Shutting down real-time data updater")
        self.status = SystemStatus.STOPPING
        
        try:
            # Отправка уведомления об остановке
            uptime = get_utc_now() - self.stats['start_time']
            
            system_info = {
                'stop_time': get_utc_now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'uptime': str(uptime).split('.')[0],
                'cycles': self.stats['total_updates'],
                'successful_cycles': self.stats['successful_updates'],
                'candles_count': self.stats['total_candles'],
                'errors_count': self.stats['failed_updates']
            }
            
            self.telegram.send_system_stop(system_info)
            
        except Exception as e:
            self.logger.error("Failed to send shutdown notification", error=str(e))
        
        # Закрытие соединений
        try:
            self.db_manager.close()
            self.mt5_client.close()
            self.telegram.close()
        except Exception as e:
            self.logger.error("Error during cleanup", error=str(e))
        
        self.status = SystemStatus.STOPPED
        self.logger.info("Real-time data updater stopped")
    
    def close(self) -> None:
        """Закрытие соединений"""
        self._shutdown()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 
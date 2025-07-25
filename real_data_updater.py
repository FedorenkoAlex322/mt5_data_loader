#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загрузчик данных в реальном времени для торговой системы Ишимоку
Обновляет данные для множественных валютных пар и таймфреймов из OANDA API
Поддерживает: M5, M15, M30, H1, H4 для настраиваемого списка валютных пар
"""

import sys
import os
import time
import logging
import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional, Tuple
import signal
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

# Импортируем конфигурацию
from real_config import (
    get_active_config, NOTIFICATION_TYPES, 
    get_all_combinations, get_enabled_pairs, get_timeframe_by_name,
    get_data_download_combinations, get_all_pairs
)

# Настройка логирования
class UTCFormatter(logging.Formatter):
    """Кастомный форматтер для отображения времени в UTC"""
    def formatTime(self, record, datefmt=None):
        # Используем UTC время вместо местного
        ct = datetime.utcfromtimestamp(record.created)
        if datefmt:
            return ct.strftime(datefmt)
        else:
            return ct.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'

def setup_logging(config):
    """Настройка системы логирования"""
    log_config = config['logging']
    
    # Создаем UTC formatter
    formatter = UTCFormatter(log_config['format'])
    
    # Настраиваем основной логгер
    logger = logging.getLogger('MultiPairDataUpdater')
    logger.setLevel(getattr(logging, log_config['level']))
    
    # File handler с ротацией
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        'real_data_updater.log',
        maxBytes=log_config['max_file_size'],
        backupCount=log_config['backup_count'],
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

class TelegramNotifier:
    """Класс для отправки уведомлений в Telegram"""

    def __init__(self, config, logger):
        self.config = config['telegram']
        self.logger = logger
        self.session = requests.Session()

    def send_message(self, message: str, topic_type: str = 'system'):
        """Отправка сообщения в Telegram"""
        try:
            topic_id = self.config['topics'].get(topic_type, self.config['topics']['system'])

            url = f"https://api.telegram.org/bot{self.config['bot_token']}/sendMessage"

            data = {
                'chat_id': self.config['chat_id'],
                'text': message,
                'parse_mode': 'HTML',
                'message_thread_id': topic_id
            }

            for attempt in range(self.config['retry_attempts']):
                try:
                    response = self.session.post(url, json=data, timeout=10)
                    if response.status_code == 200:
                        return True
                    else:
                        self.logger.warning(f"Telegram API помилка: {response.status_code}")

                except requests.RequestException as e:
                    self.logger.warning(f"Помилка відправки в Telegram (спроба {attempt + 1}): {e}")

                if attempt < self.config['retry_attempts'] - 1:
                    time.sleep(self.config['retry_delay'])

            return False

        except Exception as e:
            self.logger.error(f"Критична помилка Telegram: {e}")
            return False

class MultiPairDataUpdater:
    """Основной класс загрузчика данных для множественных пар"""
    
    def __init__(self):
        self.config = get_active_config()
        self.logger = setup_logging(self.config)
        
        self.running = False
        self.db_connection = None
        self.combinations = self.config['data_download_combinations']
        
        # OANDA API настройки
        self.oanda_session = requests.Session()
        self.oanda_session.headers.update({
            'Authorization': f"Bearer {self.config['oanda']['api_key']}",
            'Content-Type': 'application/json'
        })
        
        # Статистика
        self.stats = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'start_time': None,
            'last_update_time': None,
            'pair_stats': {}
        }
        
        # Настройка обработки сигналов для корректного завершения
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("🚀 Ініціалізація багатопарного завантажувача даних завершена")
        self.logger.info(f"📊 Буде оброблятися {len(self.combinations)} комбінацій пар/таймфреймів")
        self.logger.info(f"💱 Всього валютних пар: {len(get_all_pairs())} (включаючи неактивні)")
        self.logger.info(f"📈 Активних таймфреймів: {len(self.config['active_timeframes'])}")
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        self.logger.info(f"📡 Отримано сигнал {signum}, зупиняємо систему...")
        self.running = False
    
    def connect_to_database(self):
        """Подключение к базе данных"""
        try:
            db_config = self.config['database']
            self.db_connection = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )
            self.db_connection.autocommit = False
            
            # Устанавливаем UTC
            cursor = self.db_connection.cursor()
            cursor.execute("SET timezone = 'UTC'")
            cursor.close()
            
            self.logger.info("✅ Підключення до бази даних встановлено")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Помилка підключення до БД: {e}")
            self.telegram.send_message(
                f"❌ <b>Помилка підключення до бази даних</b>\n{str(e)[:200]}", 
                'system'
            )
            return False
    
    def get_last_candle_time(self, combination: Dict) -> Optional[datetime]:
        """Получение времени последней свечи для конкретной комбинации пара/таймфрейм"""
        try:
            cursor = self.db_connection.cursor()
            query = """
                SELECT MAX(timestamp) AT TIME ZONE 'UTC' as utc_timestamp
                FROM market_data.candles 
                WHERE symbol_id = %s AND timeframe_id = %s
            """
            cursor.execute(query, (combination['symbol_id'], combination['timeframe_id']))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result and result[0]:
                # Принудительно устанавливаем UTC timezone
                last_time = result[0]
                from datetime import timezone
                if last_time.tzinfo is None:
                    last_time = last_time.replace(tzinfo=timezone.utc)
                elif last_time.tzinfo != timezone.utc:
                    # Конвертируем в UTC если другой timezone
                    last_time = last_time.astimezone(timezone.utc)
                
                self.logger.debug(f"📅 Остання свічка {combination['symbol']} {combination['timeframe']}: {last_time} UTC")
                return last_time
            else:
                self.logger.warning(f"⚠️ Свічки для {combination['symbol']} {combination['timeframe']} не знайдені")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Помилка отримання останньої свічки {combination['symbol']} {combination['timeframe']}: {e}")
            return None
    
    def parse_oanda_time(self, time_str: str) -> datetime:
        """Парсинг времени OANDA в формате UTC"""
        try:
            # OANDA формат: 2023-01-11T15:27:00.000000000Z
            if '.' in time_str:
                date_part, microsec_part = time_str.split('.')
                microsec_part = microsec_part[:6].ljust(6, '0')
                time_str = f"{date_part}.{microsec_part}Z"
            
            time_str = time_str.replace('Z', '+00:00')
            return datetime.fromisoformat(time_str)
            
        except Exception as e:
            self.logger.error(f"❌ Помилка парсингу часу: {time_str}, {e}")
            raise
    
    def fetch_new_candles(self, from_time: datetime, combination: Dict, last_db_time: Optional[datetime] = None, to_time: Optional[datetime] = None) -> List[Dict]:
        """Загрузка новых свечей с OANDA API для конкретной пары/таймфрейма"""
        try:
            # Запрашиваем свечи начиная с последней известной (включительно)
            from_time_str = from_time.isoformat().replace('+00:00', 'Z')
            
            params = {
                'granularity': combination['oanda_format'],
                'from': from_time_str,
            }
            
            if to_time:
                # Если указан to_time (для загрузки истории), используем его
                to_time_str = to_time.isoformat().replace('+00:00', 'Z')
                params['to'] = to_time_str
            else:
                # Для обычного режима используем count
                params['count'] = self.config['data_update']['candles_to_fetch']
            
            url = f"{self.config['oanda']['api_url']}/v3/instruments/{combination['symbol']}/candles"
            
            self.logger.debug(f"📥 {combination['symbol']} {combination['timeframe']}: запит з {from_time_str}")
            
            response = self.oanda_session.get(
                url, 
                params=params, 
                timeout=self.config['oanda']['request_timeout']
            )
            
            # Добавляем задержку для соблюдения лимитов API
            time.sleep(self.config['oanda']['rate_limit_delay'])
            
            if response.status_code == 200:
                data = response.json()
                candles = data.get('candles', [])
                
                self.logger.info(f"📥 {combination['symbol']} {combination['timeframe']}: OANDA повернув {len(candles)} свічок")
                
                # Приводим from_time к правильному формату ПЕРЕД циклом
                from datetime import timezone
                if from_time.tzinfo is None:
                    from_time = from_time.replace(tzinfo=timezone.utc)
                
                # Анализируем полученные свечи
                complete_candles = []
                incomplete_candles = []
                new_candles = []
                
                for candle in candles:
                    candle_time = self.parse_oanda_time(candle['time'])
                    is_complete = candle.get('complete', True)
                    
                    if is_complete:
                        complete_candles.append(candle)
                        
                        # Фильтруем новые свечи: если есть last_db_time, берем только после него
                        # если нет - берем все (первоначальная загрузка)
                        if last_db_time is None:
                            new_candles.append(candle)
                        elif candle_time > last_db_time:
                            # Берем только свечи строго после последней в БД
                            new_candles.append(candle)
                    else:
                        incomplete_candles.append(candle)
                
                # Детальная статистика
                self.logger.debug(f"📥 {combination['symbol']} {combination['timeframe']}: отримано {len(candles)} всього свічок, завершених {len(complete_candles)}")
                if last_db_time:
                    self.logger.debug(f"🕐 {combination['symbol']} {combination['timeframe']}: фільтр після {last_db_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                else:
                    self.logger.debug(f"🕐 {combination['symbol']} {combination['timeframe']}: початкове завантаження без фільтру")
                
                if new_candles:
                    first_new = self.parse_oanda_time(new_candles[0]['time'])
                    last_new = self.parse_oanda_time(new_candles[-1]['time'])
                    self.logger.info(f"📈 {combination['symbol']} {combination['timeframe']}: знайдено {len(new_candles)} нових свічок ({first_new.strftime('%H:%M')} - {last_new.strftime('%H:%M')} UTC)")
                else:
                    if complete_candles:
                        last_candle = self.parse_oanda_time(complete_candles[-1]['time'])
                        self.logger.info(f"ℹ️ {combination['symbol']} {combination['timeframe']}: нових свічок немає (остання в OANDA: {last_candle.strftime('%Y-%m-%d %H:%M:%S')} UTC)")
                    else:
                        self.logger.info(f"ℹ️ {combination['symbol']} {combination['timeframe']}: немає завершених свічок від OANDA")
                
                # Прогноз следующей свечи только для коротких таймфреймов
                if incomplete_candles and combination['timeframe'] in ['M5', 'M15']:
                    next_candle_time = self.parse_oanda_time(incomplete_candles[0]['time'])
                    tf_config = get_timeframe_by_name(combination['timeframe'])
                    expected_completion = next_candle_time + timedelta(minutes=tf_config['minutes'])
                    minutes_left = (expected_completion - datetime.utcnow().replace(tzinfo=expected_completion.tzinfo)).total_seconds() / 60
                    self.logger.debug(f"⏰ {combination['symbol']} {combination['timeframe']}: наступна свічка ~{minutes_left:.1f} хв")
                
                return new_candles
                
            else:
                self.logger.error(f"❌ {combination['symbol']} {combination['timeframe']}: OANDA API помилка {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ {combination['symbol']} {combination['timeframe']}: помилка завантаження - {e}")
            return []
    
    def prepare_candle_data(self, candles: List[Dict], combination: Dict) -> List[tuple]:
        """Подготовка данных свечей для вставки в БД"""
        prepared_data = []
        
        for candle in candles:
            try:
                timestamp = self.parse_oanda_time(candle['time'])
                
                mid_data = candle.get('mid', {})
                open_price = float(mid_data.get('o', 0))
                high_price = float(mid_data.get('h', 0))
                low_price = float(mid_data.get('l', 0))
                close_price = float(mid_data.get('c', 0))
                volume = int(candle.get('volume', 0))
                
                record = (
                    combination['symbol_id'],
                    combination['timeframe_id'],
                    timestamp,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume
                )
                
                prepared_data.append(record)
                
            except Exception as e:
                self.logger.error(f"❌ {combination['symbol']} {combination['timeframe']}: помилка обробки свічки - {e}")
                continue
        
        return prepared_data
    
    def insert_candles_to_db(self, candle_data: List[tuple], combination: Dict) -> bool:
        """Вставка новых свечей в базу данных для конкретной пары/таймфрейма"""
        if not candle_data:
            self.logger.debug(f"💾 {combination['symbol']} {combination['timeframe']}: немає даних для вставки")
            return True
        
        try:
            cursor = self.db_connection.cursor()
            
            # Логируем что именно пытаемся вставить
            if candle_data:
                first_timestamp = candle_data[0][2]  # timestamp is 3rd element
                last_timestamp = candle_data[-1][2]
                self.logger.debug(f"💾 {combination['symbol']} {combination['timeframe']}: спроба вставки {len(candle_data)} свічок від {first_timestamp.strftime('%Y-%m-%d %H:%M:%S')} до {last_timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            insert_query = """
                INSERT INTO market_data.candles 
                (symbol_id, timeframe_id, timestamp, open, high, low, close, volume)
                VALUES %s
                ON CONFLICT (symbol_id, timeframe_id, timestamp) DO NOTHING
            """
            
            execute_values(cursor, insert_query, candle_data, page_size=100)
            
            # Получаем количество реально вставленных записей
            inserted_count = cursor.rowcount
            
            self.db_connection.commit()
            cursor.close()
            
            if inserted_count > 0:
                self.logger.info(f"✅ {combination['symbol']} {combination['timeframe']}: вставлено {inserted_count} свічок")
                
                # Обновляем статистику
                pair_key = f"{combination['symbol']}_{combination['timeframe']}"
                if pair_key not in self.stats['pair_stats']:
                    self.stats['pair_stats'][pair_key] = {
                        'total_candles': 0,
                        'last_update': None,
                        'errors': 0
                    }
                
                self.stats['pair_stats'][pair_key]['total_candles'] += inserted_count
                self.stats['pair_stats'][pair_key]['last_update'] = datetime.utcnow()
            else:
                # Логируем даже когда ничего не вставлено (все дубли)
                skipped_count = len(candle_data)
                self.logger.info(f"⏭️ {combination['symbol']} {combination['timeframe']}: {skipped_count} свічок пропущено (дублі в БД)")
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ {combination['symbol']} {combination['timeframe']}: помилка вставки в БД - {e}")
            self.db_connection.rollback()
            
            # Обновляем статистику ошибок
            pair_key = f"{combination['symbol']}_{combination['timeframe']}"
            if pair_key not in self.stats['pair_stats']:
                self.stats['pair_stats'][pair_key] = {'total_candles': 0, 'last_update': None, 'errors': 0}
            self.stats['pair_stats'][pair_key]['errors'] += 1
            
            return False
    
    def update_single_combination(self, combination: Dict) -> bool:
        """Обновление данных для одной комбинации пары/таймфрейма"""
        try:
            self.logger.info(f"🔄 Оновлення {combination['symbol']} {combination['timeframe']}...")
            
            # Получаем время последней свечи
            last_candle_time = self.get_last_candle_time(combination)
            
            if last_candle_time is None:
                # Если нет данных, начинаем с 24 часов назад
                from datetime import timezone
                last_candle_time = (datetime.utcnow() - timedelta(hours=24)).replace(tzinfo=timezone.utc)
                self.logger.warning(f"⚠️ {combination['symbol']} {combination['timeframe']}: починаємо з 24 годин тому")
                request_from_time = last_candle_time
            else:
                # Если есть данные, запрашиваем начиная с последней свечи
                request_from_time = last_candle_time
                self.logger.info(f"🔍 {combination['symbol']} {combination['timeframe']}: остання свічка в БД {last_candle_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            # Загружаем новые свечи
            new_candles = self.fetch_new_candles(request_from_time, combination, last_candle_time)
            
            if new_candles:
                # Подготавливаем и вставляем данные
                prepared_data = self.prepare_candle_data(new_candles, combination)
                success = self.insert_candles_to_db(prepared_data, combination)
                self.logger.debug(f"💾 {combination['symbol']} {combination['timeframe']}: підготовлено {len(prepared_data)} записів для вставки")
                return success
            else:
                self.logger.debug(f"ℹ️ {combination['symbol']} {combination['timeframe']}: нових свічок немає")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ {combination['symbol']} {combination['timeframe']}: помилка оновлення - {e}")
            return False
    
    def update_all_combinations_sequential(self) -> Dict:
        """Последовательное обновление всех комбинаций"""
        results = {
            'successful': 0,
            'failed': 0,
            'total_candles': 0,
            'details': []
        }
        
        for combination in self.combinations:
            try:
                success = self.update_single_combination(combination)
                
                if success:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                
                # Небольшая задержка между парами
                if self.config['data_update'].get('stagger_delay', 0) > 0:
                    time.sleep(self.config['data_update']['stagger_delay'])
                
            except Exception as e:
                self.logger.error(f"❌ Критична помилка для {combination['symbol']} {combination['timeframe']}: {e}")
                results['failed'] += 1
        
        # Подсчитываем общее количество новых свечей
        for pair_key, stats in self.stats['pair_stats'].items():
            if stats['last_update'] and (datetime.utcnow() - stats['last_update']).seconds < 300:  # За последние 5 минут
                results['total_candles'] += stats.get('total_candles', 0)
        
        return results
    
    def update_all_combinations_parallel(self) -> Dict:
        """Параллельное обновление всех комбинаций"""
        results = {
            'successful': 0,
            'failed': 0,
            'total_candles': 0,
            'details': []
        }
        
        max_workers = min(
            self.config['data_update'].get('max_workers', 3),
            len(self.combinations)
        )
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Запускаем задачи
            future_to_combination = {
                executor.submit(self.update_single_combination, combination): combination
                for combination in self.combinations
            }
            
            # Собираем результаты
            completed = 0
            total = len(self.combinations)
            for future in as_completed(future_to_combination):
                combination = future_to_combination[future]
                completed += 1
                
                try:
                    success = future.result()
                    if success:
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                    
                    # Логируем прогресс каждые 10 завершенных задач
                    if completed % 10 == 0 or completed == total:
                        self.logger.info(f"📊 Прогрес: {completed}/{total} комбінацій завершено")
                        
                except Exception as e:
                    self.logger.error(f"❌ Помилка в потоці для {combination['symbol']} {combination['timeframe']}: {e}")
                    results['failed'] += 1
        
        return results
    
    def update_cycle(self):
        """Один цикл обновления данных для всех пар и таймфреймов"""
        try:
            self.stats['total_updates'] += 1
            cycle_start_time = datetime.utcnow()
            
            self.logger.info(f"🔄 Початок циклу оновлення #{self.stats['total_updates']}")
            
            # Выбираем метод обновления: параллельный или последовательный
            if self.config['data_update'].get('parallel_downloads', True):
                max_workers = min(
                    self.config['data_update'].get('max_workers', 3),
                    len(self.combinations)
                )
                self.logger.info(f"🔄 Паралельне оновлення: {len(self.combinations)} комбінацій, {max_workers} потоків")
                results = self.update_all_combinations_parallel()
            else:
                self.logger.info(f"🔄 Послідовне оновлення: {len(self.combinations)} комбінацій")
                results = self.update_all_combinations_sequential()
            
            cycle_duration = (datetime.utcnow() - cycle_start_time).total_seconds()
            
            # Обновляем общую статистику
            if results['failed'] == 0:
                self.stats['successful_updates'] += 1
            else:
                self.stats['failed_updates'] += 1
            
            self.stats['last_update_time'] = datetime.utcnow()
            
            # Логируем результаты
            self.logger.info(
                f"✅ Цикл #{self.stats['total_updates']} завершено за {cycle_duration:.1f}с: "
                f"успішно={results['successful']}, помилок={results['failed']}, "
                f"нових свічок={results['total_candles']}"
            )
            
            # Отправляем уведомления в Telegram при наличии новых данных
            if results['total_candles'] > 0:
                self.send_update_notification(results, cycle_duration)
            
            return results['failed'] == 0
            
        except Exception as e:
            self.logger.error(f"❌ Критична помилка циклу оновлення: {e}")
            self.telegram.send_message(
                f"❌ <b>Критична помилка оновлення</b>\n{str(e)[:200]}", 
                'system'
            )
            return False
    
    def send_update_notification(self, results: Dict, cycle_duration: float):
        """Отправка уведомления об обновлении данных"""
        try:
            # Формируем детальную статистику по парам
            active_pairs = []
            for pair_key, stats in self.stats['pair_stats'].items():
                if (stats['last_update'] and 
                    (datetime.utcnow() - stats['last_update']).seconds < 300):  # За последние 5 минут
                    if stats.get('total_candles', 0) > 0:
                        active_pairs.append({
                            'name': pair_key.replace('_', ' '),
                            'candles': stats['total_candles']
                        })
            
            if active_pairs:
                pairs_text = "\n".join([f"📈 {pair['name']}: {pair['candles']} свічок" 
                                       for pair in active_pairs[:5]])  # Показываем первые 5
                
                if len(active_pairs) > 5:
                    pairs_text += f"\n... та ще {len(active_pairs) - 5} пар"
                
                message = (
                    f"📊 <b>Оновлення даних</b>\n"
                    f"🕐 {datetime.utcnow().strftime('%H:%M:%S')} UTC\n"
                    f"⏱️ Тривалість: {cycle_duration:.1f}с\n"
                    f"✅ Успішно: {results['successful']}/{len(self.combinations)}\n"
                    f"📈 Всього нових свічок: {results['total_candles']}\n\n"
                    f"{pairs_text}"
                )
                
                self.telegram.send_message(message, 'system')
        
        except Exception as e:
            self.logger.error(f"❌ Помилка відправки уведомлення: {e}")
    
    def send_heartbeat(self):
        """Отправка heartbeat сообщения"""
        try:
            uptime = datetime.utcnow() - self.stats['start_time']
            uptime_str = str(uptime).split('.')[0]  # Убираем микросекунды
            
            # Считаем общую статистику
            total_candles = sum(stats.get('total_candles', 0) 
                               for stats in self.stats['pair_stats'].values())
            
            total_errors = sum(stats.get('errors', 0) 
                              for stats in self.stats['pair_stats'].values())
            
            message = (
                f"💚 <b>Система працює</b>\n"
                f"🕐 {datetime.utcnow().strftime('%H:%M:%S')} UTC\n"
                f"⏰ Час роботи: {uptime_str}\n"
                f"🔄 Циклів оновлення: {self.stats['total_updates']}\n"
                f"📈 Активних пар: {len(get_enabled_pairs())}\n"
                f"📊 Таймфреймів: {len(self.config['active_timeframes'])}\n"
                f"💾 Завантажено свічок: {total_candles}\n"
                f"❌ Помилок: {total_errors}"
            )
            
            self.telegram.send_message(message, 'system')
            
        except Exception as e:
            self.logger.error(f"❌ Помилка heartbeat: {e}")
    
    def get_active_timeframes_now(self) -> List[str]:
        """Определение активных таймфреймов в текущий момент времени"""
        from datetime import timezone
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        
        active_timeframes = []
        schedules = self.config['data_update']['timeframe_schedules']
        target_second = self.config['data_update']['schedule_second']
        
        # Проверяем текущую секунду
        if now.second != target_second:
            self.logger.debug(f"⏰ Поточний час: {now.strftime('%H:%M:%S')} UTC, потрібна секунда: {target_second}, активних таймфреймів: 0")
            return active_timeframes
            
        current_minute = now.minute
        current_hour = now.hour
        
        for tf_name, schedule in schedules.items():
            if not schedule.get('enabled', True):
                continue
                
            interval_minutes = schedule['interval_minutes']
            
            # Проверяем подходит ли текущее время для данного таймфрейма
            if interval_minutes >= 1440:  # D1 - ежедневно в 00:02
                if current_hour == 0 and current_minute == 0:
                    active_timeframes.append(tf_name)
            elif interval_minutes >= 60:  # H1, H4 - каждые N часов в :02
                hours_interval = interval_minutes // 60
                if current_hour % hours_interval == 0 and current_minute == 0:
                    active_timeframes.append(tf_name)
            else:  # M5, M15, M30 - каждые N минут в :02
                if current_minute % interval_minutes == 0:
                    active_timeframes.append(tf_name)
        
        self.logger.info(f"⏰ Поточний час: {now.strftime('%H:%M:%S')} UTC, активні таймфрейми: {', '.join(active_timeframes) if active_timeframes else 'немає'}")
        return active_timeframes
    
    def calculate_seconds_until_next_schedule(self) -> int:
        """Вычисление секунд до следующего запланированного времени"""
        from datetime import timezone
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        
        schedules = self.config['data_update']['timeframe_schedules']
        target_second = self.config['data_update']['schedule_second']
        
        next_times = []
        
        for tf_name, schedule in schedules.items():
            if not schedule.get('enabled', True):
                continue
                
            interval_minutes = schedule['interval_minutes']
            
            # Рассчитываем следующее время для каждого таймфрейма
            if interval_minutes >= 1440:  # D1 - следующий день в 00:02
                next_time = now.replace(hour=0, minute=0, second=target_second, microsecond=0)
                if next_time <= now:
                    next_time += timedelta(days=1)
                next_times.append(next_time)
                
            elif interval_minutes >= 60:  # H1, H4 - следующий подходящий час
                hours_interval = interval_minutes // 60
                next_hour = ((now.hour // hours_interval) + 1) * hours_interval
                if next_hour >= 24:
                    next_hour = 0
                    next_time = now.replace(hour=next_hour, minute=0, second=target_second, microsecond=0) + timedelta(days=1)
                else:
                    next_time = now.replace(hour=next_hour, minute=0, second=target_second, microsecond=0)
                next_times.append(next_time)
                
            else:  # M5, M15, M30 - следующая подходящая минута
                next_minute = ((now.minute // interval_minutes) + 1) * interval_minutes
                if next_minute >= 60:
                    next_minute = 0
                    next_hour = now.hour + 1
                    if next_hour >= 24:
                        next_hour = 0
                        next_time = now.replace(hour=next_hour, minute=next_minute, second=target_second, microsecond=0) + timedelta(days=1)
                    else:
                        next_time = now.replace(hour=next_hour, minute=next_minute, second=target_second, microsecond=0)
                else:
                    next_time = now.replace(minute=next_minute, second=target_second, microsecond=0)
                next_times.append(next_time)
        
        # Находим ближайшее время
        if not next_times:
            # Если нет активных расписаний, ждем до следующей минуты
            next_time = now.replace(second=target_second, microsecond=0) + timedelta(minutes=1)
        else:
            next_time = min(next_times)
        
        seconds_until = (next_time - now).total_seconds()
        
        self.logger.info(f"⏰ Наступне оновлення: {next_time.strftime('%H:%M:%S')} UTC (через {seconds_until:.0f} секунд)")
        return max(1, int(seconds_until))
    
    def initial_history_download(self):
        """Первоначальная докачка истории для всех пар и таймфреймов"""
        if not self.config['data_update'].get('initial_history_download', True):
            self.logger.info("⏸️ Первоначальна докачка вимкнена в конфігурації")
            return
        
        self.logger.info("🔄 Початок первоначальної докачки історії...")
        
        history_days = self.config['data_update'].get('history_download_days', 30)
        from datetime import timezone
        start_date = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=history_days)
        
        total_combinations = len(self.combinations)
        successful_downloads = 0
        failed_downloads = 0
        
        # Многопоточная загрузка истории
        if self.config['data_update'].get('parallel_downloads', True):
            max_workers = min(
                self.config['data_update'].get('max_workers', 7),
                len(self.combinations)
            )
            
            self.logger.info(f"🔄 Багатопотокова докачка історії: {max_workers} потоків")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_combination = {
                    executor.submit(self.download_history_for_combination, combination, start_date): combination
                    for combination in self.combinations
                }
                
                for i, future in enumerate(as_completed(future_to_combination), 1):
                    combination = future_to_combination[future]
                    try:
                        success = future.result()
                        if success:
                            successful_downloads += 1
                        else:
                            failed_downloads += 1
                            
                        self.logger.info(f"📊 Прогрес докачки: {i}/{total_combinations} завершено")
                        
                    except Exception as e:
                        self.logger.error(f"❌ Помилка в потоці для {combination['symbol']} {combination['timeframe']}: {e}")
                        failed_downloads += 1
        else:
            # Последовательная загрузка истории
            self.logger.info(f"🔄 Послідовна докачка історії")
            
            for i, combination in enumerate(self.combinations, 1):
                try:
                    self.logger.info(f"📥 Докачка історії {i}/{total_combinations}: {combination['symbol']} {combination['timeframe']}")
                    success = self.download_history_for_combination(combination, start_date)
                    
                    if success:
                        successful_downloads += 1
                    else:
                        failed_downloads += 1
                        
                except Exception as e:
                    self.logger.error(f"❌ Помилка докачки для {combination['symbol']} {combination['timeframe']}: {e}")
                    failed_downloads += 1
        
        self.logger.info(f"✅ Первоначальна докачка завершена: успішно={successful_downloads}, помилок={failed_downloads}")
        
        # Отправляем уведомление о завершении докачки
        message = (
            f"📊 <b>Первоначальна докачка завершена</b>\n"
            f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"✅ Успішно: {successful_downloads}\n"
            f"❌ Помилок: {failed_downloads}\n"
            f"📈 Всього комбінацій: {total_combinations}\n"
            f"⏰ Історія: {history_days} днів"
        )
        
        self.telegram.send_message(message, 'system')
    
    def download_history_for_combination(self, combination: Dict, start_date: datetime) -> bool:
        """Загрузка истории для одной комбинации пары/таймфрейма"""
        try:
            self.logger.info(f"📥 Докачка історії: {combination['symbol']} {combination['timeframe']}")
            
            # Получаем время последней свечи
            last_candle_time = self.get_last_candle_time(combination)
            
            if last_candle_time is None:
                # Если данных нет, качаем с start_date
                download_from = start_date
                self.logger.info(f"📊 {combination['symbol']} {combination['timeframe']}: немає даних, завантажуємо з {start_date.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            elif last_candle_time < start_date:
                # Если данные старые, качаем с start_date
                download_from = start_date
                self.logger.info(f"📊 {combination['symbol']} {combination['timeframe']}: старі дані, завантажуємо з {start_date.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            else:
                # Если данные свежие, качаем с последней свечи
                download_from = last_candle_time
                self.logger.info(f"📊 {combination['symbol']} {combination['timeframe']}: свіжі дані, завантажуємо з {last_candle_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            # Загружаем данные порциями
            from datetime import timezone
            current_date = download_from
            end_date = datetime.utcnow().replace(tzinfo=timezone.utc)
            total_loaded = 0
            
            while current_date < end_date:
                # Определяем размер порции в зависимости от таймфрейма
                if combination['timeframe'] == 'M5':
                    chunk_days = 7  # 7 дней для M5
                elif combination['timeframe'] == 'M15':
                    chunk_days = 15  # 15 дней для M15
                elif combination['timeframe'] == 'M30':
                    chunk_days = 30  # 30 дней для M30
                elif combination['timeframe'] == 'H1':
                    chunk_days = 60  # 60 дней для H1
                elif combination['timeframe'] == 'H4':
                    chunk_days = 120  # 120 дней для H4
                elif combination['timeframe'] == 'D1':
                    chunk_days = 365  # 365 дней для D1
                else:
                    chunk_days = 30  # По умолчанию
                
                chunk_end = min(current_date + timedelta(days=chunk_days), end_date)
                
                # Загружаем порцию (без фильтрации для истории)
                new_candles = self.fetch_new_candles(current_date, combination, None, chunk_end)
                
                if new_candles:
                    # Подготавливаем и вставляем данные
                    prepared_data = self.prepare_candle_data(new_candles, combination)
                    self.insert_candles_to_db(prepared_data, combination)
                    total_loaded += len(new_candles)
                
                current_date = chunk_end
                
                # Небольшая задержка между запросами для соблюдения лимитов API
                time.sleep(self.config['oanda']['rate_limit_delay'])
            
            if total_loaded > 0:
                self.logger.info(f"✅ {combination['symbol']} {combination['timeframe']}: завантажено {total_loaded} свічок")
            else:
                self.logger.debug(f"ℹ️ {combination['symbol']} {combination['timeframe']}: немає нових даних")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Помилка докачки для {combination['symbol']} {combination['timeframe']}: {e}")
            return False
    
    def group_combinations_by_timeframes(self, active_timeframes: List[str]) -> Dict[str, List[Dict]]:
        """Группировка комбинаций по активным таймфреймам"""
        grouped = {}
        all_pairs = get_all_pairs()
        
        for tf_name in active_timeframes:
            # Находим конфигурацию таймфрейма
            tf_config = get_timeframe_by_name(tf_name)
            if not tf_config:
                continue
                
            combinations = []
            for pair in all_pairs:
                combinations.append({
                    'symbol': pair['symbol'],
                    'symbol_id': pair['symbol_id'],
                    'timeframe': tf_name,
                    'timeframe_id': tf_config['id'],
                    'oanda_format': tf_config['oanda_format'],
                    'priority': pair['priority'],
                    'enabled': pair['enabled'],
                    'description': f"{pair['description']} {tf_config['description']}"
                })
            
            grouped[tf_name] = combinations
            
        return grouped
    
    def update_timeframe_group(self, timeframe: str, combinations: List[Dict]) -> Dict:
        """Обновление данных для группы пар одного таймфрейма"""
        self.logger.info(f"🔄 Оновлення таймфрейму {timeframe}: {len(combinations)} пар")
        
        results = {
            'timeframe': timeframe,
            'successful': 0,
            'failed': 0,
            'total_candles': 0,
            'details': []
        }
        
        if self.config['data_update'].get('parallel_downloads', True):
            # Параллельное обновление пар в таймфрейме
            max_workers = min(
                self.config['data_update'].get('max_workers', 7),
                len(combinations)
            )
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_combination = {
                    executor.submit(self.update_single_combination, combination): combination
                    for combination in combinations
                }
                
                for future in as_completed(future_to_combination):
                    combination = future_to_combination[future]
                    try:
                        success = future.result()
                        if success:
                            results['successful'] += 1
                        else:
                            results['failed'] += 1
                            
                    except Exception as e:
                        self.logger.error(f"❌ Помилка в потоці для {combination['symbol']} {combination['timeframe']}: {e}")
                        results['failed'] += 1
        else:
            # Последовательное обновление пар в таймфрейме
            for combination in combinations:
                try:
                    success = self.update_single_combination(combination)
                    if success:
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                    
                    # Небольшая задержка между парами
                    if self.config['data_update'].get('stagger_delay', 0) > 0:
                        time.sleep(self.config['data_update']['stagger_delay'])
                        
                except Exception as e:
                    self.logger.error(f"❌ Критична помилка для {combination['symbol']} {combination['timeframe']}: {e}")
                    results['failed'] += 1
        
        # Подсчитываем новые свечи для этого таймфрейма
        for pair_key, stats in self.stats['pair_stats'].items():
            if (timeframe in pair_key and stats['last_update'] and 
                (datetime.utcnow() - stats['last_update']).seconds < 300):  # За последние 5 минут
                results['total_candles'] += stats.get('total_candles', 0)
        
        self.logger.info(f"✅ Таймфрейм {timeframe}: успішно={results['successful']}, помилок={results['failed']}, нових свічок={results['total_candles']}")
        return results
    
    def smart_update_cycle(self):
        """Умный цикл обновления данных по расписанию таймфреймов"""
        try:
            self.stats['total_updates'] += 1
            cycle_start_time = datetime.utcnow()
            
            # Определяем активные таймфреймы
            active_timeframes = self.get_active_timeframes_now()
            

            
            if not active_timeframes:
                self.logger.info("ℹ️ Немає активних таймфреймів в поточний момент")
                return True
            
            self.logger.info(f"🔄 Розумний цикл #{self.stats['total_updates']}: активні таймфрейми {', '.join(active_timeframes)}")
            
            # Группируем комбинации по таймфреймам
            grouped_combinations = self.group_combinations_by_timeframes(active_timeframes)
            
            total_successful = 0
            total_failed = 0
            total_new_candles = 0
            timeframe_results = []
            
            # Обрабатываем каждый таймфрейм
            for timeframe, combinations in grouped_combinations.items():
                if not combinations:
                    continue
                    
                try:
                    result = self.update_timeframe_group(timeframe, combinations)
                    timeframe_results.append(result)
                    
                    total_successful += result['successful']
                    total_failed += result['failed']
                    total_new_candles += result['total_candles']
                    
                    # Задержка между группами таймфреймов
                    if (self.config['data_update'].get('batch_delay_between_groups', 0) > 0 and
                        timeframe != list(grouped_combinations.keys())[-1]):  # Не последний
                        time.sleep(self.config['data_update']['batch_delay_between_groups'])
                        
                except Exception as e:
                    self.logger.error(f"❌ Критична помилка для таймфрейму {timeframe}: {e}")
                    total_failed += len(combinations)
            
            cycle_duration = (datetime.utcnow() - cycle_start_time).total_seconds()
            
            # Обновляем общую статистику
            if total_failed == 0:
                self.stats['successful_updates'] += 1
            else:
                self.stats['failed_updates'] += 1
                
            self.stats['last_update_time'] = datetime.utcnow()
            
            # Логируем результаты
            tf_summary = ", ".join([f"{r['timeframe']}({r['successful']}/{len(grouped_combinations[r['timeframe']])})" 
                                   for r in timeframe_results])
            
            self.logger.info(
                f"✅ Розумний цикл #{self.stats['total_updates']} завершено за {cycle_duration:.1f}с: "
                f"таймфрейми=[{tf_summary}], нових свічок={total_new_candles}"
            )
            
            # Отправляем уведомления в Telegram при наличии новых данных
            if total_new_candles > 0:
                self.send_smart_update_notification(active_timeframes, timeframe_results, cycle_duration)
            
            return total_failed == 0
            
        except Exception as e:
            self.logger.error(f"❌ Критична помилка розумного циклу оновлення: {e}")
            self.telegram.send_message(
                f"❌ <b>Критична помилка розумного оновлення</b>\n{str(e)[:200]}", 
                'system'
            )
            return False
    
    def send_smart_update_notification(self, active_timeframes: List[str], timeframe_results: List[Dict], cycle_duration: float):
        """Отправка уведомления об умном обновлении данных"""
        try:
            tf_details = []
            total_candles = 0
            
            for result in timeframe_results:
                if result['total_candles'] > 0:
                    tf_details.append(f"📊 {result['timeframe']}: {result['total_candles']} свічок ({result['successful']}/{result['successful']+result['failed']} пар)")
                    total_candles += result['total_candles']
            
            if tf_details:
                message = (
                    f"🧠 <b>Розумне оновлення</b>\n"
                    f"🕐 {datetime.utcnow().strftime('%H:%M:%S')} UTC\n"
                    f"⏱️ Тривалість: {cycle_duration:.1f}с\n"
                    f"📈 Активні таймфрейми: {', '.join(active_timeframes)}\n"
                    f"💾 Всього нових свічок: {total_candles}\n\n"
                    f"{chr(10).join(tf_details)}"
                )
                
                self.telegram.send_message(message, 'system')
        
        except Exception as e:
            self.logger.error(f"❌ Помилка відправки розумного уведомлення: {e}")
    
    def run(self):
        """Основной цикл работы багатопарного загрузчика"""
        self.logger.info("🚀 Запуск багатопарного завантажувача даних")
        
        # Подключаемся к базе данных
        if not self.connect_to_database():
            return
        
        # Инициализируем статистику
        self.stats['start_time'] = datetime.utcnow()
        
        # Отправляем уведомление о запуске
        all_pairs = get_all_pairs()
        pairs_text = ", ".join([pair['symbol'] for pair in all_pairs])
        timeframes_text = ", ".join(self.config['active_timeframes'])
        
        smart_schedule_mode = self.config['data_update'].get('smart_schedule_mode', False)
        
        if smart_schedule_mode:
            active_schedules = []
            for tf, schedule in self.config['data_update']['timeframe_schedules'].items():
                if schedule.get('enabled', True):
                    active_schedules.append(f"{tf}(кожні {schedule['interval_minutes']}хв)")
            schedule_text = f"Розумний режим: {', '.join(active_schedules)}"
        else:
            schedule_text = f"Інтервал {self.config['data_update']['update_interval']}с"
        
        download_text = "Паралельний" if self.config['data_update'].get('parallel_downloads', True) else "Послідовний"
        
        startup_message = (
            f"🚀 <b>Багатопарний завантажувач запущено</b>\n"
            f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"💱 Валютні пари: {pairs_text}\n"
            f"📊 Таймфрейми: {timeframes_text}\n"
            f"🔢 Комбінацій: {len(self.combinations)}\n"
            f"⏱️ Режим: {schedule_text}\n"
            f"🔄 Завантаження: {download_text}"
        )
        
        self.telegram.send_message(startup_message, 'system')
        
        # Выполняем первоначальную докачку истории
        self.initial_history_download()
        
        # Принудительно запускаем первый цикл обновления для проверки
        self.logger.info("🚀 Примусовий запуск першого циклу оновлення...")
        self.update_cycle()
        
        self.running = True
        failed_attempts = 0
        max_retries = self.config['data_update']['max_retries']
        last_heartbeat = datetime.utcnow()
        heartbeat_interval = self.config['monitoring'].get('heartbeat_interval', 3600)  # 1 час по умолчанию
        smart_schedule_mode = self.config['data_update'].get('smart_schedule_mode', False)
        
        while self.running:
            try:
                # Выбираем режим обновления в зависимости от конфигурации
                if smart_schedule_mode:
                    success = self.smart_update_cycle()
                else:
                    success = self.update_cycle()
                
                if success:
                    failed_attempts = 0
                else:
                    failed_attempts += 1
                    if failed_attempts >= max_retries:
                        self.logger.error(f"❌ Досягнуто максимум невдалих спроб ({max_retries})")
                        self.telegram.send_message(
                            f"🛑 <b>Завантажувач зупинено</b>\n"
                            f"❌ Досягнуто максимум помилок: {max_retries}\n"
                            f"📊 Статистика: {self.stats['successful_updates']}/{self.stats['total_updates']} успішних циклів", 
                            'system'
                        )
                        break
                
                # Проверяем нужно ли отправить heartbeat
                if (datetime.utcnow() - last_heartbeat).seconds >= heartbeat_interval:
                    self.send_heartbeat()
                    last_heartbeat = datetime.utcnow()
                
                # Спим до следующего обновления
                if success:
                    if smart_schedule_mode:
                        # В умном режиме ждем до следующего запланированного времени
                        wait_seconds = self.calculate_seconds_until_next_schedule()
                        self.logger.info(f"⏳ Очікування {wait_seconds}с до наступного розкладу...")
                        time.sleep(wait_seconds)
                    else:
                        # В обычном режиме используем фиксированный интервал
                        time.sleep(self.config['data_update']['update_interval'])
                else:
                    # Увеличиваем интервал при ошибках
                    retry_delay = self.config['data_update']['retry_interval'] * min(failed_attempts, 5)
                    self.logger.warning(f"⏳ Пауза {retry_delay}с після помилки (спроба {failed_attempts}/{max_retries})")
                    time.sleep(retry_delay)
                
            except KeyboardInterrupt:
                self.logger.info("⏹️ Отримано сигнал зупинки")
                break
            except Exception as e:
                self.logger.error(f"❌ Неочікувана помилка: {e}")
                failed_attempts += 1
                time.sleep(self.config['data_update']['retry_interval'])
        
        self.running = False
        uptime = datetime.utcnow() - self.stats['start_time'] if self.stats['start_time'] else timedelta(0)
        
        self.logger.info(f"🛑 Завантажувач зупинено після {uptime}")
        
        # Закрываем соединение с БД
        if self.db_connection:
            self.db_connection.close()
        
        # Финальная статистика
        total_candles = sum(stats.get('total_candles', 0) for stats in self.stats['pair_stats'].values())
        total_errors = sum(stats.get('errors', 0) for stats in self.stats['pair_stats'].values())
        
        # Отправляем уведомление об остановке
        shutdown_message = (
            f"🛑 <b>Завантажувач зупинено</b>\n"
            f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"⏰ Час роботи: {str(uptime).split('.')[0]}\n"
            f"🔄 Циклів: {self.stats['total_updates']}\n"
            f"✅ Успішних: {self.stats['successful_updates']}\n"
            f"💾 Завантажено свічок: {total_candles}\n"
            f"❌ Помилок: {total_errors}"
        )
        
        self.telegram.send_message(shutdown_message, 'system')

def main():
    """Главная функция"""
    try:
        print("🚀 Ініціалізація багатопарного завантажувача даних...")
        updater = MultiPairDataUpdater()
        
        # Проверяем конфигурацию
        all_pairs = get_all_pairs()
        if not all_pairs:
            print("❌ Помилка: Не налаштовано жодної валютної пари!")
            print("   Перевірте конфігурацію CURRENCY_PAIRS в real_config.py")
            sys.exit(1)
        
        combinations = updater.combinations
        if not combinations:
            print("❌ Помилка: Не знайдено комбінацій пар/таймфреймів для завантаження!")
            print("   Перевірте конфігурацію ACTIVE_TIMEFRAMES в real_config.py")
            sys.exit(1)
        
        enabled_pairs = get_enabled_pairs()
        disabled_pairs = [p for p in all_pairs if not p['enabled']]
        
        print(f"✅ Налаштовано {len(all_pairs)} валютних пар (активних: {len(enabled_pairs)}, неактивних: {len(disabled_pairs)})")
        print(f"✅ Налаштовано {len(updater.config['active_timeframes'])} таймфреймів")
        print(f"✅ Всього комбінацій для завантаження: {len(combinations)}")
        print("\n📊 Комбінації для завантаження:")
        for combo in combinations[:10]:  # Показываем первые 10
            status = "✅" if combo['enabled'] else "⚠️"
            print(f"   {status} {combo['symbol']} {combo['timeframe']} (ID: {combo['symbol_id']}/{combo['timeframe_id']})")
        
        if len(combinations) > 10:
            print(f"   ... та ще {len(combinations) - 10} комбінацій")
        
        smart_schedule_mode = updater.config['data_update'].get('smart_schedule_mode', False)
        print(f"\n🔄 Режим завантаження: {'Паралельний' if updater.config['data_update'].get('parallel_downloads', True) else 'Послідовний'}")
        if smart_schedule_mode:
            active_schedules = []
            for tf, schedule in updater.config['data_update']['timeframe_schedules'].items():
                if schedule.get('enabled', True):
                    active_schedules.append(f"{tf}(кожні {schedule['interval_minutes']}хв)")
            print(f"⏱️  Режим роботи: Розумний розклад - {', '.join(active_schedules)}")
        else:
            print(f"⏱️  Інтервал оновлення: {updater.config['data_update']['update_interval']} секунд")
        print("\n🚀 Запуск системи...")
        
        updater.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Зупинка за запитом користувача")
    except Exception as e:
        print(f"💥 Критична помилка ініціалізації: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 
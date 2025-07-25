#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Завантажувач історичних даних для багатопарної торгової системи
Завантажує дані з лютого 2025 року по всіх активних валютних парах та таймфреймах
"""

import sys
import os
import time
import logging
import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta, timezone
import json
from typing import List, Dict, Optional, Tuple
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed

# Імпортуємо нову конфігурацію
from real_config import (
    get_active_config, get_all_combinations, get_enabled_pairs,
    TIMEFRAMES, CURRENCY_PAIRS, ACTIVE_TIMEFRAMES
)

# Налаштування періоду завантаження
START_DATE = '2025-07-01'  # Початок завантаження
END_DATE = '2025-07-07'    # Кінець завантаження (до сьогодні)

# Налаштування завантаження
BATCH_SIZE = 5000          # Максимум свічок за один запит до OANDA (не використовується з from+to)
MAX_WORKERS = 5            # Кількість паралельних потоків (зменшено для стабільності)
REQUEST_DELAY = 2          # Затримка між запитами (секунди) (збільшено для стабільності)

class HistoricalDataLoader:
    """Завантажувач історичних даних"""
    
    def __init__(self):
        self.config = get_active_config()
        self.setup_logging()
        
        self.db_connection = None
        self.combinations = get_all_combinations()
        self.stats = {
            'total_combinations': len(self.combinations),
            'completed': 0,
            'total_candles_loaded': 0,
            'total_candles_skipped': 0,
            'errors': 0
        }
        
        # OANDA API налаштування
        self.oanda_session = requests.Session()
        self.oanda_session.headers.update({
            'Authorization': f"Bearer {self.config['oanda']['api_key']}",
            'Content-Type': 'application/json'
        })
        
        self.logger.info("🚀 Ініціалізація завантажувача історичних даних")
        self.logger.info(f"📅 Період: {START_DATE} - {END_DATE}")
        self.logger.info(f"🔢 Комбінацій: {len(self.combinations)}")
    
    def setup_logging(self):
        """Налаштування логування"""
        # Створюємо логгер
        self.logger = logging.getLogger('HistoricalDataLoader')
        self.logger.setLevel(logging.INFO)
        
        # Форматтер
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # File handler
        file_handler = logging.FileHandler('historical_data_loader.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def connect_to_database(self):
        """Підключення до бази даних"""
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
            
            # Встановлюємо UTC
            cursor = self.db_connection.cursor()
            cursor.execute("SET timezone = 'UTC'")
            cursor.close()
            
            self.logger.info("✅ Підключення до бази даних встановлено")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Помилка підключення до БД: {e}")
            return False
    
    def check_existing_data(self, combination: Dict, start_date: str, end_date: str) -> Tuple[int, datetime, datetime]:
        """Перевіряє існуючі дані і визначає що потрібно завантажити"""
        try:
            cursor = self.db_connection.cursor()
            
            # Перевіряємо кількість існуючих записів
            count_query = """
                SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
                FROM market_data.candles
                WHERE symbol_id = %s AND timeframe_id = %s
                AND timestamp >= %s AND timestamp <= %s
            """
            
            cursor.execute(count_query, (
                combination['symbol_id'],
                combination['timeframe_id'],
                start_date,
                end_date
            ))
            
            result = cursor.fetchone()
            cursor.close()
            
            existing_count = result[0] if result[0] else 0
            min_time = result[1] if result[1] else None
            max_time = result[2] if result[2] else None
            
            return existing_count, min_time, max_time
            
        except Exception as e:
            self.logger.error(f"❌ Помилка перевірки існуючих даних: {e}")
            return 0, None, None
    
    def fetch_oanda_data(self, combination: Dict, start_time: str, end_time: str) -> List[Dict]:
        """Завантаження даних з OANDA API"""
        try:
            # Використовуємо from + to БЕЗ count (правильний формат для OANDA API)
            params = {
                'granularity': combination['oanda_format'],
                'from': start_time,
                'to': end_time
            }
            
            url = f"{self.config['oanda']['api_url']}/v3/instruments/{combination['symbol']}/candles"
            
            self.logger.debug(f"📥 {combination['symbol']} {combination['timeframe']}: запит {start_time} → {end_time}")
            
            response = self.oanda_session.get(url, params=params, timeout=30)
            
            # Додаємо затримку
            time.sleep(REQUEST_DELAY)
            
            if response.status_code == 200:
                data = response.json()
                candles = data.get('candles', [])
                
                # Фільтруємо тільки завершені свічки
                complete_candles = [c for c in candles if c.get('complete', True)]
                
                self.logger.debug(f"📊 {combination['symbol']} {combination['timeframe']}: отримано {len(complete_candles)} свічок")
                
                return complete_candles
            else:
                # Детальне логування помилки
                try:
                    error_data = response.json()
                    self.logger.error(f"❌ OANDA API помилка {response.status_code} для {combination['symbol']} {combination['timeframe']}: {error_data}")
                except:
                    self.logger.error(f"❌ OANDA API помилка {response.status_code} для {combination['symbol']} {combination['timeframe']}")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Помилка завантаження з OANDA: {e}")
            return []
    
    def parse_oanda_time(self, time_str: str) -> datetime:
        """Парсинг часу OANDA в UTC формат"""
        try:
            if '.' in time_str:
                date_part, microsec_part = time_str.split('.')
                microsec_part = microsec_part[:6].ljust(6, '0')
                time_str = f"{date_part}.{microsec_part}Z"
            
            time_str = time_str.replace('Z', '+00:00')
            return datetime.fromisoformat(time_str)
            
        except Exception as e:
            self.logger.error(f"❌ Помилка парсингу часу: {time_str}, {e}")
            raise
    
    def prepare_candle_data(self, candles: List[Dict], combination: Dict) -> List[tuple]:
        """Підготовка даних свічок для вставки в БД"""
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
                self.logger.error(f"❌ Помилка обробки свічки: {e}")
                continue
        
        return prepared_data
    
    def insert_candles_to_db(self, candle_data: List[tuple]) -> int:
        """Вставка свічок в БД з ігноруванням дублів"""
        if not candle_data:
            return 0
        
        try:
            cursor = self.db_connection.cursor()
            
            insert_query = """
                INSERT INTO market_data.candles 
                (symbol_id, timeframe_id, timestamp, open, high, low, close, volume)
                VALUES %s
                ON CONFLICT (symbol_id, timeframe_id, timestamp) DO NOTHING
            """
            
            execute_values(cursor, insert_query, candle_data, page_size=1000)
            
            # Отримуємо кількість реально вставлених записів
            inserted_count = cursor.rowcount
            
            self.db_connection.commit()
            cursor.close()
            
            return inserted_count
            
        except Exception as e:
            self.logger.error(f"❌ Помилка вставки в БД: {e}")
            self.db_connection.rollback()
            return 0
    
    def load_combination_data(self, combination: Dict) -> Dict:
        """Завантаження даних для однієї комбінації пара/таймфрейм"""
        start_time = time.time()
        
        try:
            self.logger.info(f"📥 Початок завантаження {combination['symbol']} {combination['timeframe']}")
            
            # Перевіряємо існуючі дані
            existing_count, min_time, max_time = self.check_existing_data(
                combination, START_DATE, END_DATE
            )
            
            self.logger.info(f"📊 {combination['symbol']} {combination['timeframe']}: існує {existing_count} записів")
            
            # Розраховуємо періоди для завантаження
            start_dt = datetime.fromisoformat(START_DATE).replace(tzinfo=timezone.utc)
            end_dt = datetime.fromisoformat(END_DATE).replace(tzinfo=timezone.utc)
            
            total_loaded = 0
            total_skipped = 0
            
            # Завантажуємо блоками
            current_start = start_dt
            
            while current_start < end_dt:
                # Розраховуємо кінець блоку (максимум 7 днів для стабільності)
                current_end = min(current_start + timedelta(days=7), end_dt)
                
                # Завантажуємо блок з OANDA
                candles = self.fetch_oanda_data(
                    combination,
                    current_start.isoformat().replace('+00:00', 'Z'),
                    current_end.isoformat().replace('+00:00', 'Z')
                )
                
                if candles:
                    # Підготовляємо дані
                    prepared_data = self.prepare_candle_data(candles, combination)
                    
                    # Вставляємо в БД
                    inserted_count = self.insert_candles_to_db(prepared_data)
                    
                    total_loaded += inserted_count
                    total_skipped += len(prepared_data) - inserted_count
                    
                    self.logger.info(f"📈 {combination['symbol']} {combination['timeframe']}: {current_start.date()} - {current_end.date()}: +{inserted_count} свічок")
                
                # Переходимо до наступного блоку
                current_start = current_end
            
            duration = time.time() - start_time
            
            result = {
                'symbol': combination['symbol'],
                'timeframe': combination['timeframe'],
                'loaded': total_loaded,
                'skipped': total_skipped,
                'duration': duration,
                'success': True
            }
            
            self.logger.info(f"✅ {combination['symbol']} {combination['timeframe']}: завершено за {duration:.1f}с, +{total_loaded} свічок")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ {combination['symbol']} {combination['timeframe']}: помилка - {e}")
            return {
                'symbol': combination['symbol'],
                'timeframe': combination['timeframe'],
                'loaded': 0,
                'skipped': 0,
                'duration': time.time() - start_time,
                'success': False,
                'error': str(e)
            }
    
    def run_parallel_loading(self):
        """Паралельне завантаження всіх комбінацій"""
        self.logger.info(f"🚀 Початок паралельного завантаження з {MAX_WORKERS} потоками")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Запускаємо завдання
            future_to_combination = {
                executor.submit(self.load_combination_data, combination): combination
                for combination in self.combinations
            }
            
            # Збираємо результати
            for future in as_completed(future_to_combination):
                combination = future_to_combination[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    self.stats['completed'] += 1
                    if result['success']:
                        self.stats['total_candles_loaded'] += result['loaded']
                        self.stats['total_candles_skipped'] += result['skipped']
                    else:
                        self.stats['errors'] += 1
                    
                    # Показуємо прогрес
                    progress = (self.stats['completed'] / self.stats['total_combinations']) * 100
                    self.logger.info(f"📊 Прогрес: {self.stats['completed']}/{self.stats['total_combinations']} ({progress:.1f}%)")
                    
                except Exception as e:
                    self.logger.error(f"❌ Помилка в потоці для {combination['symbol']} {combination['timeframe']}: {e}")
                    self.stats['errors'] += 1
        
        return results
    
    def print_final_report(self, results: List[Dict]):
        """Друк фінального звіту"""
        self.logger.info("\n" + "="*80)
        self.logger.info("📋 ФІНАЛЬНИЙ ЗВІТ ЗАВАНТАЖЕННЯ ІСТОРИЧНИХ ДАНИХ")
        self.logger.info("="*80)
        
        # Загальна статистика
        self.logger.info(f"📅 Період: {START_DATE} - {END_DATE}")
        self.logger.info(f"🔢 Комбінацій: {self.stats['total_combinations']}")
        self.logger.info(f"✅ Успішно: {self.stats['completed'] - self.stats['errors']}")
        self.logger.info(f"❌ Помилок: {self.stats['errors']}")
        self.logger.info(f"📈 Завантажено нових свічок: {self.stats['total_candles_loaded']:,}")
        self.logger.info(f"⏭️ Пропущено (дублі): {self.stats['total_candles_skipped']:,}")
        
        # Деталі по парам
        self.logger.info("\n📊 ДЕТАЛІ ПО ПАРАМ:")
        self.logger.info("-" * 80)
        
        # Групуємо по парам
        pairs_stats = {}
        for result in results:
            if result['success']:
                symbol = result['symbol']
                if symbol not in pairs_stats:
                    pairs_stats[symbol] = {'loaded': 0, 'skipped': 0, 'timeframes': 0}
                
                pairs_stats[symbol]['loaded'] += result['loaded']
                pairs_stats[symbol]['skipped'] += result['skipped']
                pairs_stats[symbol]['timeframes'] += 1
        
        for symbol, stats in pairs_stats.items():
            self.logger.info(f"   {symbol:<8}: {stats['timeframes']} таймфреймів, +{stats['loaded']:,} свічок, ~{stats['skipped']:,} дублів")
        
        self.logger.info("="*80)
        self.logger.info("🎉 Завантаження історичних даних завершено!")

def main():
    """Головна функція"""
    try:
        print("🚀 Завантажувач історичних даних для багатопарної системи")
        print(f"📅 Період: {START_DATE} - {END_DATE}")
        print(f"🔢 Таймфреймы: {', '.join(ACTIVE_TIMEFRAMES)}")
        print(f"💱 Пари: {', '.join([p['symbol'] for p in get_enabled_pairs()])}")
        print()
        
        # Підтвердження запуску
        response = input("Продовжити завантаження? (y/N): ")
        if response.lower() != 'y':
            print("❌ Завантаження скасовано")
            return
        
        # Створюємо завантажувач
        loader = HistoricalDataLoader()
        
        # Підключаємося до БД
        if not loader.connect_to_database():
            print("❌ Не вдалося підключитися до бази даних")
            return
        
        # Запускаємо завантаження
        start_time = time.time()
        results = loader.run_parallel_loading()
        total_time = time.time() - start_time
        
        # Друкуємо звіт
        loader.print_final_report(results)
        loader.logger.info(f"⏱️ Загальний час виконання: {total_time:.1f} секунд")
        
        # Закриваємо з'єднання
        if loader.db_connection:
            loader.db_connection.close()
        
    except KeyboardInterrupt:
        print("\n🛑 Завантаження перервано користувачем")
    except Exception as e:
        print(f"💥 Критична помилка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
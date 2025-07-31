#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Завантажувач історичних даних з MetaTrader 5 для багатопарної торгової системи
"""

import sys
import os
import time
import logging
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import MetaTrader5 as mt5
import threading

# Імпортуємо конфігурацію
from real_config import (
    get_active_config, get_all_combinations, get_enabled_pairs,
    get_timeframe_by_name
)

# Налаштування періоду завантаження
START_DATE = '2025-07-01'
END_DATE = '2025-07-07'

MAX_WORKERS = 3
REQUEST_DELAY = 0.5  # пауза між запитами до MT5


class HistoricalDataLoaderMT5:
    def __init__(self):
        self.config = get_active_config()
        self.logger = self.setup_logging()
        self.combinations = get_all_combinations()
        self.db_connection = None
        self.mt5_initialized = False
        self.mt5_lock = threading.Lock()

        self._initialize_mt5()  # Инициализируем MT5 перед вызовом symbols_get
        self.symbol_mapping = self._create_symbol_mapping()
        self.timeframe_mapping = {
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }

        self.logger.info(f"📅 Період: {START_DATE} → {END_DATE}")
        self.logger.info(f"🔢 Комбінацій: {len(self.combinations)}")


    def setup_logging(self):
        logger = logging.getLogger('HistoricalMT5Loader')
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        fh = logging.FileHandler('historical_mt5_loader.log', encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        return logger

    def _initialize_mt5(self):
        with self.mt5_lock:
            if self.mt5_initialized:
                return True
            mt5_config = self.config.get('mt5', {})
            if not mt5.initialize(path=mt5_config.get('terminal_path')):
                self.logger.error(f"❌ Не вдалося ініціалізувати MT5: {mt5.last_error()}")
                return False
            self.mt5_initialized = True
            self.logger.info("✅ MT5 ініціалізовано")
            return True

    def _create_symbol_mapping(self) -> Dict[str, str]:
        base_mapping = {
            'EUR_USD': 'EURUSD', 'GBP_USD': 'GBPUSD', 'USD_JPY': 'USDJPY',
            'USD_CHF': 'USDCHF', 'USD_CAD': 'USDCAD', 'AUD_USD': 'AUDUSD',
            'NZD_USD': 'NZDUSD', 'EUR_GBP': 'EURGBP', 'EUR_JPY': 'EURJPY',
            'EUR_CHF': 'EURCHF', 'EUR_CAD': 'EURCAD', 'EUR_AUD': 'EURAUD',
            'EUR_NZD': 'EURNZD', 'GBP_JPY': 'GBPJPY', 'GBP_CHF': 'GBPCHF',
            'GBP_CAD': 'GBPCAD', 'GBP_AUD': 'GBPAUD', 'GBP_NZD': 'GBPNZD',
            'CHF_JPY': 'CHFJPY', 'CAD_JPY': 'CADJPY', 'AUD_JPY': 'AUDJPY',
            'AUD_CAD': 'AUDCAD', 'AUD_CHF': 'AUDCHF', 'AUD_NZD': 'AUDNZD',
            'NZD_JPY': 'NZDJPY', 'NZD_CAD': 'NZDCAD', 'NZD_CHF': 'NZDCHF',
            'CAD_CHF': 'CADCHF'
        }

        available_symbols = [s.name for s in mt5.symbols_get()]
        mapping = {}
        for oanda_sym, mt5_base in base_mapping.items():
            matches = [s for s in available_symbols if s.startswith(mt5_base)]
            mapping[oanda_sym] = matches[0] if matches else mt5_base
        return mapping

    def connect_to_database(self) -> bool:
        try:
            db = self.config['database']
            self.db_connection = psycopg2.connect(
                host=db['host'],
                port=db['port'],
                database=db['database'],
                user=db['user'],
                password=db['password']
            )
            self.db_connection.autocommit = False
            cursor = self.db_connection.cursor()
            cursor.execute("SET timezone = 'UTC'")
            cursor.close()
            self.logger.info("✅ Підключено до бази даних")
            return True
        except Exception as e:
            self.logger.error(f"❌ Помилка підключення до БД: {e}")
            return False

    def fetch_mt5_data(self, combination: Dict, start_dt: datetime, end_dt: datetime) -> List[Dict]:
        try:
            symbol = self.symbol_mapping.get(combination['symbol'], combination['symbol'].replace('_', ''))
            timeframe = self.timeframe_mapping.get(combination['timeframe'], mt5.TIMEFRAME_M5)

            if not mt5.symbol_select(symbol, True):
                self.logger.warning(f"⚠️ Неможливо вибрати символ {symbol}")
                return []

            rates = mt5.copy_rates_range(symbol, timeframe, start_dt, end_dt)
            time.sleep(REQUEST_DELAY)

            if rates is None:
                self.logger.warning(f"⚠️ MT5 не повернув жодної свічки для {symbol}")
                return []

            if len(rates) == 0:
                self.logger.info(f"ℹ️ Немає свічок для {symbol} з {start_dt.date()} до {end_dt.date()}")
                return []

            return rates
        except Exception as e:
            self.logger.error(f"❌ Помилка завантаження MT5: {e}")
            return []

    def prepare_candle_data(self, rates, combination) -> List[tuple]:
        prepared = []
        for rate in rates:
            try:
                timestamp = datetime.fromtimestamp(int(rate['time']), tz=timezone.utc)
                record = (
                    int(combination['symbol_id']),
                    int(combination['timeframe_id']),
                    timestamp,
                    float(rate['open']),
                    float(rate['high']),
                    float(rate['low']),
                    float(rate['close']),
                    float(rate['tick_volume'])
                )
                prepared.append(record)
            except Exception as e:
                self.logger.error(f"❌ Помилка обробки свічки: {e}")
        return prepared

    def insert_candles_to_db(self, data: List[tuple]) -> int:
        if not data:
            return 0
        try:
            cursor = self.db_connection.cursor()
            query = """
                INSERT INTO market_data.candles 
                (symbol_id, timeframe_id, timestamp, open, high, low, close, volume)
                VALUES %s
                ON CONFLICT (symbol_id, timeframe_id, timestamp) DO NOTHING
            """
            execute_values(cursor, query, data, page_size=500)
            count = cursor.rowcount
            self.db_connection.commit()
            cursor.close()
            return count
        except Exception as e:
            self.logger.error(f"❌ Помилка вставки в БД: {e}")
            self.db_connection.rollback()
            return 0

    def load_combination(self, combination: Dict) -> Dict:
        try:
            self.logger.info(f"📥 {combination['symbol']} {combination['timeframe']}")
            start_dt = datetime.fromisoformat(START_DATE).replace(tzinfo=timezone.utc)
            end_dt = datetime.fromisoformat(END_DATE).replace(tzinfo=timezone.utc)

            total_inserted = 0
            while start_dt < end_dt:
                chunk_end = min(start_dt + timedelta(days=7), end_dt)
                rates = self.fetch_mt5_data(combination, start_dt, chunk_end)
                data = self.prepare_candle_data(rates, combination)
                inserted = self.insert_candles_to_db(data)
                total_inserted += inserted

                self.logger.info(f"📈 {combination['symbol']} {combination['timeframe']}: {start_dt.date()} → {chunk_end.date()} — {inserted} свічок")

                start_dt = chunk_end

            return {
                'symbol': combination['symbol'],
                'timeframe': combination['timeframe'],
                'inserted': total_inserted,
                'success': True
            }
        except Exception as e:
            self.logger.error(f"❌ Помилка: {combination['symbol']} {combination['timeframe']}: {e}")
            return {
                'symbol': combination['symbol'],
                'timeframe': combination['timeframe'],
                'inserted': 0,
                'success': False
            }

    def run_parallel(self):
        self.logger.info(f"🚀 Початок завантаження з {MAX_WORKERS} потоками")
        results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(self.load_combination, combo): combo
                for combo in self.combinations
            }
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        return results

    def print_summary(self, results: List[Dict]):
        total = len(results)
        success = sum(1 for r in results if r['success'])
        candles = sum(r['inserted'] for r in results)
        self.logger.info("📋 Підсумок завантаження")
        self.logger.info(f"✅ Успішно: {success}/{total}")
        self.logger.info(f"📈 Вставлено свічок: {candles:,}")
        self.logger.info("🎉 Завантаження завершено")

    def close(self):
        if self.db_connection:
            self.db_connection.close()
        if self.mt5_initialized:
            mt5.shutdown()
            self.logger.info("🔌 MT5 відключено")


def main():
    print(f"🚀 Завантаження історичних даних з MT5")
    print(f"📅 Період: {START_DATE} → {END_DATE}")

    proceed = input("Продовжити? (y/N): ")
    if proceed.lower() != 'y':
        print("❌ Скасовано")
        return

    loader = HistoricalDataLoaderMT5()
    if not loader.connect_to_database():
        return

    start_time = time.time()
    results = loader.run_parallel()
    loader.print_summary(results)
    loader.close()
    print(f"⏱️ Завершено за {time.time() - start_time:.1f} секунд")


if __name__ == "__main__":
    main()

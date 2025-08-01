"""
Candle data processing utilities
"""

from typing import List, Tuple, Dict, Any
from datetime import datetime, timezone
from dataclasses import dataclass

from ..config.constants import Timeframe
from ..core.mt5_client import MT5Candle
from ..utils.logging import get_logger


@dataclass
class ProcessedCandle:
    """Обработанная свеча для вставки в БД"""
    symbol_id: int
    timeframe_id: int
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class CandleProcessor:
    """Процессор для обработки свечей"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def process_mt5_candles(
        self, 
        candles: List[MT5Candle], 
        symbol_id: int
    ) -> List[ProcessedCandle]:
        """
        Обработка свечей MT5 для вставки в БД
        
        Args:
            candles: Список свечей MT5
            symbol_id: ID символа в БД
            
        Returns:
            Список обработанных свечей
        """
        processed_candles = []
        
        for candle in candles:
            try:
                processed_candle = ProcessedCandle(
                    symbol_id=symbol_id,
                    timeframe_id=candle.timeframe.id,
                    timestamp=candle.timestamp,
                    open=candle.open,
                    high=candle.high,
                    low=candle.low,
                    close=candle.close,
                    volume=candle.volume
                )
                processed_candles.append(processed_candle)
                
            except Exception as e:
                self.logger.error(
                    "Failed to process candle",
                    symbol=candle.symbol,
                    timeframe=candle.timeframe.value,
                    timestamp=candle.timestamp,
                    error=str(e)
                )
                continue
        
        self.logger.debug(
            "Candles processed",
            input_count=len(candles),
            processed_count=len(processed_candles)
        )
        
        return processed_candles
    
    def convert_to_db_tuples(
        self, 
        processed_candles: List[ProcessedCandle]
    ) -> List[Tuple]:
        """
        Конвертация обработанных свечей в кортежи для БД
        
        Args:
            processed_candles: Список обработанных свечей
            
        Returns:
            Список кортежей для вставки в БД
        """
        db_tuples = []
        
        for candle in processed_candles:
            db_tuple = (
                candle.symbol_id,
                candle.timeframe_id,
                candle.timestamp,
                candle.open,
                candle.high,
                candle.low,
                candle.close,
                candle.volume
            )
            db_tuples.append(db_tuple)
        
        return db_tuples
    
    def filter_new_candles(
        self, 
        candles: List[MT5Candle], 
        last_db_time: datetime
    ) -> List[MT5Candle]:
        """
        Фильтрация новых свечей (после последнего времени в БД)
        
        Args:
            candles: Список свечей
            last_db_time: Время последней свечи в БД
            
        Returns:
            Список новых свечей
        """
        if last_db_time is None:
            return candles
        
        # Убеждаемся что last_db_time в UTC
        if last_db_time.tzinfo is None:
            last_db_time = last_db_time.replace(tzinfo=timezone.utc)
        
        new_candles = []
        for candle in candles:
            if candle.timestamp > last_db_time:
                new_candles.append(candle)
        
        self.logger.debug(
            "Candles filtered",
            total_candles=len(candles),
            new_candles=len(new_candles),
            last_db_time=last_db_time
        )
        
        return new_candles
    
    def validate_candle_data(self, candle: MT5Candle) -> bool:
        """
        Валидация данных свечи
        
        Args:
            candle: Свеча для валидации
            
        Returns:
            True если свеча валидна
        """
        try:
            # Проверяем что все цены положительные
            if any(price <= 0 for price in [candle.open, candle.high, candle.low, candle.close]):
                self.logger.warning(
                    "Invalid candle prices",
                    symbol=candle.symbol,
                    timeframe=candle.timeframe.value,
                    timestamp=candle.timestamp,
                    prices=[candle.open, candle.high, candle.low, candle.close]
                )
                return False
            
            # Проверяем что high >= low
            if candle.high < candle.low:
                self.logger.warning(
                    "High price less than low price",
                    symbol=candle.symbol,
                    timeframe=candle.timeframe.value,
                    timestamp=candle.timestamp,
                    high=candle.high,
                    low=candle.low
                )
                return False
            
            # Проверяем что open и close находятся между high и low
            if not (candle.low <= candle.open <= candle.high):
                self.logger.warning(
                    "Open price outside high-low range",
                    symbol=candle.symbol,
                    timeframe=candle.timeframe.value,
                    timestamp=candle.timestamp,
                    open=candle.open,
                    high=candle.high,
                    low=candle.low
                )
                return False
            
            if not (candle.low <= candle.close <= candle.high):
                self.logger.warning(
                    "Close price outside high-low range",
                    symbol=candle.symbol,
                    timeframe=candle.timeframe.value,
                    timestamp=candle.timestamp,
                    close=candle.close,
                    high=candle.high,
                    low=candle.low
                )
                return False
            
            # Проверяем объем
            if candle.volume < 0:
                self.logger.warning(
                    "Negative volume",
                    symbol=candle.symbol,
                    timeframe=candle.timeframe.value,
                    timestamp=candle.timestamp,
                    volume=candle.volume
                )
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Error validating candle",
                symbol=candle.symbol,
                timeframe=candle.timeframe.value,
                timestamp=candle.timestamp,
                error=str(e)
            )
            return False
    
    def calculate_candle_statistics(
        self, 
        candles: List[MT5Candle]
    ) -> Dict[str, Any]:
        """
        Вычисление статистики по свечам
        
        Args:
            candles: Список свечей
            
        Returns:
            Словарь со статистикой
        """
        if not candles:
            return {
                'count': 0,
                'time_range': None,
                'avg_volume': 0,
                'price_range': None
            }
        
        # Временной диапазон
        timestamps = [c.timestamp for c in candles]
        start_time = min(timestamps)
        end_time = max(timestamps)
        
        # Объемы
        volumes = [c.volume for c in candles]
        avg_volume = sum(volumes) / len(volumes) if volumes else 0
        
        # Ценовой диапазон
        all_prices = []
        for candle in candles:
            all_prices.extend([candle.open, candle.high, candle.low, candle.close])
        
        min_price = min(all_prices)
        max_price = max(all_prices)
        
        return {
            'count': len(candles),
            'time_range': {
                'start': start_time,
                'end': end_time,
                'duration_hours': (end_time - start_time).total_seconds() / 3600
            },
            'avg_volume': avg_volume,
            'price_range': {
                'min': min_price,
                'max': max_price,
                'spread': max_price - min_price
            }
        }
    
    def group_candles_by_timeframe(
        self, 
        candles: List[MT5Candle]
    ) -> Dict[Timeframe, List[MT5Candle]]:
        """
        Группировка свечей по таймфреймам
        
        Args:
            candles: Список свечей
            
        Returns:
            Словарь с группированными свечами
        """
        grouped = {}
        
        for candle in candles:
            if candle.timeframe not in grouped:
                grouped[candle.timeframe] = []
            grouped[candle.timeframe].append(candle)
        
        # Сортируем свечи в каждой группе по времени
        for timeframe in grouped:
            grouped[timeframe].sort(key=lambda x: x.timestamp)
        
        return grouped
    
    def remove_duplicates(
        self, 
        candles: List[MT5Candle]
    ) -> List[MT5Candle]:
        """
        Удаление дубликатов свечей
        
        Args:
            candles: Список свечей
            
        Returns:
            Список свечей без дубликатов
        """
        seen = set()
        unique_candles = []
        
        for candle in candles:
            # Создаем ключ для идентификации дубликатов
            key = (candle.symbol, candle.timeframe, candle.timestamp)
            
            if key not in seen:
                seen.add(key)
                unique_candles.append(candle)
        
        removed_count = len(candles) - len(unique_candles)
        if removed_count > 0:
            self.logger.info(
                "Duplicates removed",
                original_count=len(candles),
                unique_count=len(unique_candles),
                removed_count=removed_count
            )
        
        return unique_candles 
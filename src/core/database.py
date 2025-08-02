"""
Database manager for PostgreSQL
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
import logging
from contextlib import contextmanager

from ..utils.logging import get_logger


class DatabaseConnectionError(Exception):
    """Ошибка подключения к базе данных"""
    pass


class DatabaseQueryError(Exception):
    """Ошибка выполнения запроса к базе данных"""
    pass


class DatabaseManager:
    """Менеджер подключений к базе данных PostgreSQL"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация менеджера БД
        
        Args:
            config: Словарь с конфигурацией БД
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.connection_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """Инициализация пула соединений"""
        try:
            # Уменьшаем размер пула для предотвращения исчерпания подключений
            self.connection_pool = pool.SimpleConnectionPool(
                minconn=1,      # Минимальное количество соединений
                maxconn=10,     # Максимальное количество соединений (уменьшено с 50)
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            self.logger.info("Database connection pool initialized with maxconn=10")
        except Exception as e:
            self.logger.error("Failed to initialize database connection pool", error=str(e))
            raise DatabaseConnectionError(f"Failed to initialize connection pool: {e}")
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для получения соединения из пула"""
        if self.connection_pool is None:
            raise DatabaseConnectionError("Connection pool not initialized")
        
        conn = None
        try:
            conn = self.connection_pool.getconn()
            if conn is None:
                raise DatabaseConnectionError("Connection pool exhausted")
            yield conn
        except Exception as e:
            self.logger.error("Failed to get connection from pool", error=str(e))
            raise DatabaseConnectionError(f"Failed to get connection: {e}")
        finally:
            if conn is not None:
                try:
                    # Проверяем состояние соединения перед возвратом в пул
                    if conn.closed:
                        self.logger.warning("Connection was closed, not returning to pool")
                    else:
                        self.connection_pool.putconn(conn)
                except Exception as e:
                    self.logger.error("Error returning connection to pool", error=str(e))
    
    def get_cursor(self, conn):
        """Получение курсора с поддержкой словарей"""
        return conn.cursor(cursor_factory=RealDictCursor)
    
    def test_connection(self) -> bool:
        """Тестирование подключения к БД"""
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result is not None
        except Exception as e:
            self.logger.error("Database connection test failed", error=str(e))
            return False
    
    def get_last_candle_time(self, symbol_id: int, timeframe_id: int) -> Optional[datetime]:
        """
        Получение времени последней свечи для пары и таймфрейма
        
        Args:
            symbol_id: ID символа
            timeframe_id: ID таймфрейма
            
        Returns:
            Время последней свечи или None
        """
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cursor:
                    query = """
                        SELECT timestamp 
                        FROM market_data.candles 
                        WHERE symbol_id = %s AND timeframe_id = %s 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """
                    cursor.execute(query, (symbol_id, timeframe_id))
                    result = cursor.fetchone()
                    
                    if result:
                        return result['timestamp']
                    return None
                    
        except Exception as e:
            self.logger.error(
                "Failed to get last candle time",
                symbol_id=symbol_id,
                timeframe_id=timeframe_id,
                error=str(e)
            )
            raise DatabaseQueryError(f"Failed to get last candle time: {e}")
    
    def insert_candles_batch(self, candles_data: List[Tuple]) -> int:
        """
        Пакетная вставка свечей
        
        Args:
            candles_data: Список кортежей с данными свечей
            
        Returns:
            Количество вставленных записей
        """
        if not candles_data:
            return 0
        
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cursor:
                    query = """
                        INSERT INTO market_data.candles 
                        (symbol_id, timeframe_id, timestamp, open, high, low, close, volume)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol_id, timeframe_id, timestamp) 
                        DO UPDATE SET
                            open = EXCLUDED.open,
                            high = EXCLUDED.high,
                            low = EXCLUDED.low,
                            close = EXCLUDED.close,
                            volume = EXCLUDED.volume
                    """
                    
                    cursor.executemany(query, candles_data)
                    conn.commit()
                    
                    inserted_count = len(candles_data)
                    self.logger.debug(
                        "Candles batch inserted",
                        count=inserted_count
                    )
                    
                    return inserted_count
                    
        except Exception as e:
            self.logger.error(
                "Failed to insert candles batch",
                count=len(candles_data),
                error=str(e)
            )
            raise DatabaseQueryError(f"Failed to insert candles batch: {e}")
    
    def get_candles_count(self, symbol_id: int, timeframe_id: int) -> int:
        """
        Получение количества свечей для пары и таймфрейма
        
        Args:
            symbol_id: ID символа
            timeframe_id: ID таймфрейма
            
        Returns:
            Количество свечей
        """
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cursor:
                    query = """
                        SELECT COUNT(*) as count
                        FROM market_data.candles 
                        WHERE symbol_id = %s AND timeframe_id = %s
                    """
                    cursor.execute(query, (symbol_id, timeframe_id))
                    result = cursor.fetchone()
                    
                    return result['count'] if result else 0
                    
        except Exception as e:
            self.logger.error(
                "Failed to get candles count",
                symbol_id=symbol_id,
                timeframe_id=timeframe_id,
                error=str(e)
            )
            raise DatabaseQueryError(f"Failed to get candles count: {e}")
    
    def get_candles_range(
        self, 
        symbol_id: int, 
        timeframe_id: int, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Получение свечей в диапазоне времени
        
        Args:
            symbol_id: ID символа
            timeframe_id: ID таймфрейма
            start_time: Время начала
            end_time: Время окончания
            
        Returns:
            Список свечей
        """
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cursor:
                    query = """
                        SELECT symbol_id, timeframe_id, timestamp, open, high, low, close, volume
                        FROM market_data.candles 
                        WHERE symbol_id = %s AND timeframe_id = %s 
                        AND timestamp BETWEEN %s AND %s
                        ORDER BY timestamp
                    """
                    cursor.execute(query, (symbol_id, timeframe_id, start_time, end_time))
                    results = cursor.fetchall()
                    
                    return [dict(row) for row in results]
                    
        except Exception as e:
            self.logger.error(
                "Failed to get candles range",
                symbol_id=symbol_id,
                timeframe_id=timeframe_id,
                start_time=start_time,
                end_time=end_time,
                error=str(e)
            )
            raise DatabaseQueryError(f"Failed to get candles range: {e}")
    
    def cleanup_old_candles(self, days_to_keep: int = 30) -> int:
        """
        Очистка старых свечей
        
        Args:
            days_to_keep: Количество дней для хранения
            
        Returns:
            Количество удаленных записей
        """
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cursor:
                    query = """
                        DELETE FROM market_data.candles 
                        WHERE timestamp < NOW() - INTERVAL '%s days'
                    """
                    cursor.execute(query, (days_to_keep,))
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    self.logger.info(
                        "Old candles cleaned up",
                        deleted_count=deleted_count,
                        days_to_keep=days_to_keep
                    )
                    
                    return deleted_count
                    
        except Exception as e:
            self.logger.error(
                "Failed to cleanup old candles",
                days_to_keep=days_to_keep,
                error=str(e)
            )
            raise DatabaseQueryError(f"Failed to cleanup old candles: {e}")
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Получение статуса пула соединений"""
        if self.connection_pool is None:
            return {"status": "not_initialized"}
        
        try:
            return {
                "status": "active",
                "minconn": self.connection_pool.minconn,
                "maxconn": self.connection_pool.maxconn,
                "closed": self.connection_pool.closed
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def close(self) -> None:
        """Закрытие пула соединений"""
        if self.connection_pool is not None:
            try:
                self.connection_pool.closeall()
                self.logger.info("Database connection pool closed")
            except Exception as e:
                self.logger.error("Error closing connection pool", error=str(e))
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 
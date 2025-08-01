"""
Database management with connection pooling
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from contextlib import contextmanager
from datetime import datetime, timezone
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import execute_values, RealDictCursor
from psycopg2.extensions import connection, cursor

from ..config.settings import DatabaseConfig
from ..utils.logging import get_logger


class DatabaseConnectionError(Exception):
    """Ошибка подключения к базе данных"""
    pass


class DatabaseQueryError(Exception):
    """Ошибка выполнения запроса к базе данных"""
    pass


class DatabaseManager:
    """Менеджер базы данных с пулом соединений"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self.pool: Optional[SimpleConnectionPool] = None
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """Инициализация пула соединений"""
        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                options=f"-c timezone={self.config.timezone}"
            )
            self.logger.info(
                "Database pool initialized",
                host=self.config.host,
                database=self.config.database,
                max_connections=10
            )
        except Exception as e:
            self.logger.error("Failed to initialize database pool", error=str(e))
            raise DatabaseConnectionError(f"Failed to initialize database pool: {e}")
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для получения соединения из пула"""
        conn = None
        try:
            conn = self.pool.getconn()
            conn.autocommit = False
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error("Database operation failed", error=str(e))
            raise DatabaseQueryError(f"Database operation failed: {e}")
        finally:
            if conn:
                self.pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, connection: connection):
        """Контекстный менеджер для получения курсора"""
        cursor_obj = None
        try:
            cursor_obj = connection.cursor(cursor_factory=RealDictCursor)
            yield cursor_obj
        finally:
            if cursor_obj:
                cursor_obj.close()
    
    def test_connection(self) -> bool:
        """Тестирование подключения к базе данных"""
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    return result is not None
        except Exception as e:
            self.logger.error("Database connection test failed", error=str(e))
            return False
    
    def get_last_candle_time(self, symbol_id: int, timeframe_id: int) -> Optional[datetime]:
        """Получить время последней свечи для пары/таймфрейма"""
        query = """
            SELECT timestamp 
            FROM market_data.candles 
            WHERE symbol_id = %s AND timeframe_id = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    cur.execute(query, (symbol_id, timeframe_id))
                    result = cur.fetchone()
                    
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
    
    def insert_candles_batch(
        self, 
        candles_data: List[Tuple], 
        batch_size: int = 1000
    ) -> int:
        """
        Пакетная вставка свечей в базу данных
        
        Args:
            candles_data: Список кортежей с данными свечей
            batch_size: Размер пакета для вставки
            
        Returns:
            Количество вставленных записей
        """
        if not candles_data:
            return 0
        
        insert_query = """
            INSERT INTO market_data.candles 
            (symbol_id, timeframe_id, timestamp, open, high, low, close, volume)
            VALUES %s
            ON CONFLICT (symbol_id, timeframe_id, timestamp) DO NOTHING
        """
        
        total_inserted = 0
        
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    # Разбиваем данные на пакеты
                    for i in range(0, len(candles_data), batch_size):
                        batch = candles_data[i:i + batch_size]
                        
                        execute_values(
                            cur, 
                            insert_query, 
                            batch, 
                            page_size=batch_size
                        )
                        
                        inserted_count = cur.rowcount
                        total_inserted += inserted_count
                        
                        self.logger.debug(
                            "Batch inserted",
                            batch_size=len(batch),
                            inserted=inserted_count,
                            total_inserted=total_inserted
                        )
                
                conn.commit()
                
                self.logger.info(
                    "Candles batch insert completed",
                    total_records=len(candles_data),
                    inserted_records=total_inserted,
                    skipped_records=len(candles_data) - total_inserted
                )
                
                return total_inserted
                
        except Exception as e:
            self.logger.error(
                "Failed to insert candles batch",
                total_records=len(candles_data),
                error=str(e)
            )
            raise DatabaseQueryError(f"Failed to insert candles batch: {e}")
    
    def get_candles_count(self, symbol_id: int, timeframe_id: int) -> int:
        """Получить количество свечей для пары/таймфрейма"""
        query = """
            SELECT COUNT(*) as count
            FROM market_data.candles 
            WHERE symbol_id = %s AND timeframe_id = %s
        """
        
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    cur.execute(query, (symbol_id, timeframe_id))
                    result = cur.fetchone()
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
        end_time: datetime,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Получить свечи за период времени"""
        query = """
            SELECT timestamp, open, high, low, close, volume
            FROM market_data.candles 
            WHERE symbol_id = %s 
                AND timeframe_id = %s 
                AND timestamp >= %s 
                AND timestamp <= %s
            ORDER BY timestamp ASC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    cur.execute(query, (symbol_id, timeframe_id, start_time, end_time))
                    results = cur.fetchall()
                    
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
        """Удалить старые свечи (старше указанного количества дней)"""
        query = """
            DELETE FROM market_data.candles 
            WHERE timestamp < NOW() - INTERVAL '%s days'
        """
        
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    cur.execute(query, (days_to_keep,))
                    deleted_count = cur.rowcount
                
                conn.commit()
                
                self.logger.info(
                    "Old candles cleanup completed",
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
    
    def close(self) -> None:
        """Закрыть пул соединений"""
        if self.pool:
            self.pool.closeall()
            self.logger.info("Database pool closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 
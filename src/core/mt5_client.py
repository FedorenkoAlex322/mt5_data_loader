"""
MetaTrader5 client wrapper
"""

import time
import threading
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass

import MetaTrader5 as mt5

from ..config.settings import MT5Config
from ..config.constants import Timeframe, MT5_TIMEFRAME_MAPPING, OANDA_TO_MT5_SYMBOL_MAPPING
from ..utils.logging import get_logger


class MT5ConnectionError(Exception):
    """Ошибка подключения к MT5"""
    pass


class MT5QueryError(Exception):
    """Ошибка выполнения запроса к MT5"""
    pass


@dataclass
class MT5Candle:
    """Свеча MT5"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    symbol: str
    timeframe: Timeframe


class MT5Client:
    """Клиент для работы с MetaTrader5"""
    
    def __init__(self, config: MT5Config):
        self.config = config
        self.logger = get_logger(__name__)
        self.initialized = False
        self.lock = threading.Lock()
        self.symbol_mapping: Dict[str, str] = {}
        self._initialize()
    
    def _initialize(self) -> None:
        """Инициализация подключения к MT5"""
        try:
            with self.lock:
                if self.initialized:
                    return
                
                # Инициализация MT5
                if not mt5.initialize(path=self.config.terminal_path):
                    error_code, error_msg = mt5.last_error()
                    raise MT5ConnectionError(f"MT5 initialization failed: {error_code} - {error_msg}")
                
                # Авторизация если указаны учетные данные
                if self.config.login and self.config.password and self.config.server:
                    if not mt5.login(
                        login=self.config.login,
                        password=self.config.password,
                        server=self.config.server
                    ):
                        error_code, error_msg = mt5.last_error()
                        raise MT5ConnectionError(f"MT5 login failed: {error_code} - {error_msg}")
                    
                    account_info = mt5.account_info()
                    if account_info:
                        self.logger.info(
                            "MT5 connected successfully",
                            login=account_info.login,
                            server=account_info.server,
                            balance=account_info.balance
                        )
                    else:
                        self.logger.warning("Failed to get account info")
                else:
                    self.logger.info("MT5 initialized without authentication")
                
                # Создание маппинга символов
                self._create_symbol_mapping()
                
                self.initialized = True
                self.logger.info("MT5 client initialized successfully")
                
        except Exception as e:
            self.logger.error("Failed to initialize MT5 client", error=str(e))
            self._shutdown()
            raise MT5ConnectionError(f"Failed to initialize MT5 client: {e}")
    
    def _create_symbol_mapping(self) -> None:
        """Создание маппинга символов OANDA -> MT5"""
        try:
            available_symbols = [s.name for s in mt5.symbols_get()]
            self.logger.debug(f"Available MT5 symbols: {len(available_symbols)}")
            
            for oanda_symbol, base_name in OANDA_TO_MT5_SYMBOL_MAPPING.items():
                # Ищем совпадения по началу имени (учитываем суффиксы)
                matches = [s for s in available_symbols if s.startswith(base_name)]
                if matches:
                    selected = matches[0]
                    self.symbol_mapping[oanda_symbol] = selected
                    self.logger.debug(f"Symbol mapping: {oanda_symbol} -> {selected}")
                else:
                    # Если не найдено, используем базовое имя
                    self.symbol_mapping[oanda_symbol] = base_name
                    self.logger.warning(f"Symbol not found in MT5: {oanda_symbol}, using base name: {base_name}")
            
            self.logger.info(f"Symbol mapping created: {len(self.symbol_mapping)} pairs")
            
        except Exception as e:
            self.logger.error("Failed to create symbol mapping", error=str(e))
            raise MT5ConnectionError(f"Failed to create symbol mapping: {e}")
    
    def _get_mt5_timeframe(self, timeframe: Timeframe) -> int:
        """Получить MT5 timeframe ID"""
        return MT5_TIMEFRAME_MAPPING.get(timeframe, mt5.TIMEFRAME_M15)
    
    def _get_mt5_symbol(self, oanda_symbol: str) -> str:
        """Получить MT5 символ по OANDA символу"""
        return self.symbol_mapping.get(oanda_symbol, oanda_symbol)
    
    def ensure_symbol_selected(self, symbol: str) -> bool:
        """Убедиться что символ выбран в Market Watch"""
        try:
            if not mt5.symbol_select(symbol, True):
                error_code, error_msg = mt5.last_error()
                self.logger.warning(
                    "Failed to select symbol in Market Watch",
                    symbol=symbol,
                    error_code=error_code,
                    error_msg=error_msg
                )
                return False
            return True
        except Exception as e:
            self.logger.error("Error selecting symbol", symbol=symbol, error=str(e))
            return False
    
    def fetch_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        from_time: datetime,
        to_time: Optional[datetime] = None,
        count: Optional[int] = None
    ) -> List[MT5Candle]:
        """
        Получить свечи из MT5
        
        Args:
            symbol: Символ валютной пары
            timeframe: Таймфрейм
            from_time: Время начала
            to_time: Время окончания (если None, используется текущее время)
            count: Количество свечей (используется только если to_time=None)
            
        Returns:
            Список свечей MT5
        """
        try:
            if not self.initialized:
                self._initialize()
            
            mt5_symbol = self._get_mt5_symbol(symbol)
            mt5_timeframe = self._get_mt5_timeframe(timeframe)
            
            # Убеждаемся что символ выбран
            if not self.ensure_symbol_selected(mt5_symbol):
                return []
            
            # Определяем параметры запроса
            if to_time is not None:
                # Загрузка истории с указанным диапазоном
                rates = mt5.copy_rates_range(mt5_symbol, mt5_timeframe, from_time, to_time)
            else:
                # Загрузка последних N свечей
                current_time = datetime.now(timezone.utc)
                if count:
                    rates = mt5.copy_rates_from(mt5_symbol, mt5_timeframe, current_time, count)
                else:
                    rates = mt5.copy_rates_range(mt5_symbol, mt5_timeframe, from_time, current_time)
            
            if rates is None:
                error_code, error_msg = mt5.last_error()
                self.logger.error(
                    "MT5 returned no data",
                    symbol=mt5_symbol,
                    timeframe=timeframe.value,
                    error_code=error_code,
                    error_msg=error_msg
                )
                return []
            
            # Преобразуем данные MT5 в наши объекты
            candles = []
            for rate in rates:
                candle_time = datetime.fromtimestamp(rate['time'], tz=timezone.utc)
                
                candle = MT5Candle(
                    timestamp=candle_time,
                    open=float(rate['open']),
                    high=float(rate['high']),
                    low=float(rate['low']),
                    close=float(rate['close']),
                    volume=int(rate['tick_volume']),
                    symbol=symbol,
                    timeframe=timeframe
                )
                candles.append(candle)
            
            self.logger.debug(
                "Candles fetched successfully",
                symbol=symbol,
                timeframe=timeframe.value,
                count=len(candles),
                from_time=from_time,
                to_time=to_time
            )
            
            # Добавляем задержку для снижения нагрузки
            time.sleep(self.config.rate_limit_delay)
            
            return candles
            
        except Exception as e:
            self.logger.error(
                "Failed to fetch candles",
                symbol=symbol,
                timeframe=timeframe.value,
                error=str(e)
            )
            raise MT5QueryError(f"Failed to fetch candles: {e}")
    
    def fetch_latest_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int = 1000
    ) -> List[MT5Candle]:
        """Получить последние N свечей"""
        current_time = datetime.now(timezone.utc)
        return self.fetch_candles(symbol, timeframe, current_time, count=count)
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о символе"""
        try:
            mt5_symbol = self._get_mt5_symbol(symbol)
            symbol_info = mt5.symbol_info(mt5_symbol)
            
            if symbol_info is None:
                return None
            
            return {
                'name': symbol_info.name,
                'point': symbol_info.point,
                'digits': symbol_info.digits,
                'spread': symbol_info.spread,
                'trade_mode': symbol_info.trade_mode,
                'start_time': symbol_info.start_time,
                'expiration_time': symbol_info.expiration_time,
                'trade_stops_level': symbol_info.trade_stops_level,
                'trade_freeze_level': symbol_info.trade_freeze_level,
            }
            
        except Exception as e:
            self.logger.error("Failed to get symbol info", symbol=symbol, error=str(e))
            return None
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Получить информацию о торговом счете"""
        try:
            account_info = mt5.account_info()
            if account_info is None:
                return None
            
            return {
                'login': account_info.login,
                'server': account_info.server,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'margin_free': account_info.margin_free,
                'profit': account_info.profit,
                'currency': account_info.currency,
            }
            
        except Exception as e:
            self.logger.error("Failed to get account info", error=str(e))
            return None
    
    def test_connection(self) -> bool:
        """Тестирование подключения к MT5"""
        try:
            if not self.initialized:
                self._initialize()
            
            # Проверяем что можем получить информацию о счете
            account_info = self.get_account_info()
            return account_info is not None
            
        except Exception as e:
            self.logger.error("MT5 connection test failed", error=str(e))
            return False
    
    def _shutdown(self) -> None:
        """Завершение работы с MT5"""
        try:
            with self.lock:
                if self.initialized:
                    mt5.shutdown()
                    self.initialized = False
                    self.logger.info("MT5 connection closed")
        except Exception as e:
            self.logger.error("Error during MT5 shutdown", error=str(e))
    
    def close(self) -> None:
        """Закрыть соединение с MT5"""
        self._shutdown()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 
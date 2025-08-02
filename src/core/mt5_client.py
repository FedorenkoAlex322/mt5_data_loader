"""
MetaTrader5 client for data fetching
"""

import MetaTrader5 as mt5
import threading
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from dataclasses import dataclass

from ..config.constants import Timeframe, MT5_TIMEFRAME_MAPPING, STANDARD_CURRENCY_PAIRS, generate_mt5_symbol_variants
from ..utils.logging import get_logger


class MT5ConnectionError(Exception):
    """Ошибка подключения к MT5"""
    pass


class MT5QueryError(Exception):
    """Ошибка запроса к MT5"""
    pass


@dataclass
class MT5Candle:
    """Свеча MT5"""
    symbol: str
    timeframe: Timeframe
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class MT5Client:
    """Клиент для работы с MetaTrader5"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация клиента MT5
        
        Args:
            config: Словарь с конфигурацией MT5
        """
        self.config = config
        self.logger = get_logger(__name__)
        self._lock = threading.Lock()
        self._symbol_mapping = {}
        self._initialize()
    
    def _initialize(self) -> None:
        """Инициализация подключения к MT5"""
        try:
            # Инициализация MT5
            if not mt5.initialize(
                path=self.config.get('terminal_path'),
                login=self.config.get('login'),
                password=self.config.get('password'),
                server=self.config.get('server')
            ):
                raise MT5ConnectionError(f"MT5 initialization failed: {mt5.last_error()}")
            
            # Создание маппинга символов
            self._create_symbol_mapping()
            
            self.logger.info("MT5 client initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize MT5 client", error=str(e))
            raise MT5ConnectionError(f"MT5 initialization failed: {e}")
    
    def _create_symbol_mapping(self) -> None:
        """Создание маппинга символов OANDA -> MT5"""
        self._symbol_mapping = {}
        
        # Получаем доступные символы из MT5
        available_symbols = [s.name for s in mt5.symbols_get()]
        self.logger.info(f"Available MT5 symbols: {available_symbols[:10]}...")  # Показываем первые 10
        
        # Для каждой стандартной торговой пары ищем соответствующий символ в MT5
        for oanda_symbol in STANDARD_CURRENCY_PAIRS:
            mt5_symbol = self._find_mt5_symbol(oanda_symbol, available_symbols)
            if mt5_symbol:
                self._symbol_mapping[oanda_symbol] = mt5_symbol
                self.logger.info(f"Mapped {oanda_symbol} -> {mt5_symbol}")
            else:
                self.logger.warning(f"Could not find MT5 symbol for {oanda_symbol}")
        
        # Логируем итоговый маппинг
        self.logger.info(f"Created {len(self._symbol_mapping)} symbol mappings")
        for oanda_symbol, mt5_symbol in self._symbol_mapping.items():
            self.logger.debug(f"  {oanda_symbol} -> {mt5_symbol}")
    
    def _find_mt5_symbol(self, oanda_symbol: str, available_symbols: list) -> str:
        """
        Поиск соответствующего символа MT5 для OANDA символа
        
        Args:
            oanda_symbol: Символ в формате OANDA (например, 'EUR_USD')
            available_symbols: Список доступных символов в MT5
            
        Returns:
            Найденный символ MT5 или None
        """
        # Генерируем возможные варианты названий
        variants = generate_mt5_symbol_variants(oanda_symbol)
        
        # Ищем точное совпадение
        for variant in variants:
            if variant in available_symbols:
                return variant
        
        # Если точное совпадение не найдено, ищем частичные совпадения
        base_currencies = oanda_symbol.split('_')
        if len(base_currencies) == 2:
            base, quote = base_currencies
            
            # Ищем символы, содержащие обе валюты
            for symbol in available_symbols:
                symbol_lower = symbol.lower()
                if (base.lower() in symbol_lower and quote.lower() in symbol_lower):
                    self.logger.info(f"Found partial match for {oanda_symbol}: {symbol}")
                    return symbol
        
        return None
    
    def _get_mt5_timeframe(self, timeframe: Timeframe) -> int:
        """Получение MT5 таймфрейма"""
        return MT5_TIMEFRAME_MAPPING.get(timeframe, mt5.TIMEFRAME_M5)
    
    def _get_mt5_symbol(self, symbol: str) -> str:
        """Получение MT5 символа"""
        mt5_symbol = self._symbol_mapping.get(symbol)
        if mt5_symbol is None:
            self.logger.warning(f"No MT5 mapping found for {symbol}, using original symbol")
            # Добавляем отладочную информацию
            self.logger.debug(f"Available mappings: {list(self._symbol_mapping.keys())}")
            return symbol
        return mt5_symbol
    
    def ensure_symbol_selected(self, symbol: str) -> bool:
        """
        Убедиться что символ выбран в MT5
        
        Args:
            symbol: Символ для выбора (уже в MT5 формате)
            
        Returns:
            True если символ выбран успешно
        """
        try:
            # Проверяем доступность символа
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                self.logger.warning(f"Symbol {symbol} not found in MT5")
                return False
            
            # Выбираем символ если не выбран
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    self.logger.error(f"Failed to select symbol {symbol}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error ensuring symbol selection: {e}")
            return False
    
    def fetch_candles(
        self, 
        symbol: str, 
        timeframe: Timeframe, 
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        count: int = 1000
    ) -> List[MT5Candle]:
        """
        Загрузка свечей из MT5
        
        Args:
            symbol: Символ валютной пары
            timeframe: Таймфрейм
            from_time: Время начала (если None, загружаем последние count свечей)
            to_time: Время окончания (если None, используется текущее время)
            count: Количество свечей для загрузки
            
        Returns:
            Список свечей
        """
        with self._lock:
            try:
                mt5_symbol = self._get_mt5_symbol(symbol)
                mt5_timeframe = self._get_mt5_timeframe(timeframe)
                
                # Убеждаемся что символ выбран
                if not self.ensure_symbol_selected(mt5_symbol):
                    raise MT5QueryError(f"Symbol {mt5_symbol} not available")
                
                # Определяем параметры запроса
                if from_time is None:
                    # Загружаем последние свечи
                    rates = mt5.copy_rates_from_pos(mt5_symbol, mt5_timeframe, 0, count)
                else:
                    # Загружаем свечи за период
                    if to_time is None:
                        to_time = datetime.now(timezone.utc)
                    
                    rates = mt5.copy_rates_range(mt5_symbol, mt5_timeframe, from_time, to_time)
                
                if rates is None or len(rates) == 0:
                    self.logger.warning(f"No candles received for {symbol} {timeframe.value}")
                    return []
                
                # Конвертируем в наши объекты
                candles = []
                for rate in rates:
                    candle = MT5Candle(
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=datetime.fromtimestamp(rate['time'], tz=timezone.utc),
                        open=float(rate['open']),
                        high=float(rate['high']),
                        low=float(rate['low']),
                        close=float(rate['close']),
                        volume=int(rate['tick_volume'])
                    )
                    candles.append(candle)
                
                self.logger.debug(
                    f"Fetched {len(candles)} candles for {symbol} {timeframe.value}"
                )
                
                return candles
                
            except Exception as e:
                self.logger.error(
                    f"Failed to fetch candles for {symbol} {timeframe.value}",
                    error=str(e)
                )
                raise MT5QueryError(f"Failed to fetch candles: {e}")
    
    def fetch_latest_candles(
        self, 
        symbol: str, 
        timeframe: Timeframe, 
        count: int = 1
    ) -> List[MT5Candle]:
        """
        Загрузка последних свечей
        
        Args:
            symbol: Символ валютной пары
            timeframe: Таймфрейм
            count: Количество свечей
            
        Returns:
            Список последних свечей
        """
        return self.fetch_candles(symbol, timeframe, count=count)
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о символе
        
        Args:
            symbol: Символ валютной пары
            
        Returns:
            Информация о символе или None
        """
        try:
            mt5_symbol = self._get_mt5_symbol(symbol)
            symbol_info = mt5.symbol_info(mt5_symbol)
            
            if symbol_info is None:
                return None
            
            return {
                'symbol': symbol_info.name,
                'digits': symbol_info.digits,
                'spread': symbol_info.spread,
                'trade_mode': symbol_info.trade_mode,
                'volume_min': symbol_info.volume_min,
                'volume_max': symbol_info.volume_max,
                'volume_step': symbol_info.volume_step,
                'point': symbol_info.point,
                'tick_value': symbol_info.tick_value,
                'tick_size': symbol_info.tick_size,
                'contract_size': symbol_info.trade_contract_size,
                'margin_initial': symbol_info.margin_initial,
                'margin_maintenance': symbol_info.margin_maintenance
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get symbol info for {symbol}", error=str(e))
            return None
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Получение информации об аккаунте
        
        Returns:
            Информация об аккаунте или None
        """
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
                'leverage': account_info.leverage,
                'trade_mode': account_info.trade_mode
            }
            
        except Exception as e:
            self.logger.error("Failed to get account info", error=str(e))
            return None
    
    def test_connection(self) -> bool:
        """Тестирование подключения к MT5"""
        try:
            # Проверяем что MT5 инициализирован
            if not mt5.terminal_info():
                return False
            
            # Проверяем что можем получить информацию об аккаунте
            account_info = self.get_account_info()
            return account_info is not None
            
        except Exception as e:
            self.logger.error("MT5 connection test failed", error=str(e))
            return False
    
    def _shutdown(self) -> None:
        """Завершение работы MT5"""
        try:
            mt5.shutdown()
            self.logger.info("MT5 client shutdown")
        except Exception as e:
            self.logger.error("Error during MT5 shutdown", error=str(e))
    
    def close(self) -> None:
        """Закрытие соединения"""
        self._shutdown()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 
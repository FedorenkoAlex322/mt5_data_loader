"""
Telegram notification system
"""

import time
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config.settings import TelegramConfig
from ..config.constants import NotificationType
from ..utils.logging import get_logger


class TelegramNotificationError(Exception):
    """Ошибка отправки уведомления в Telegram"""
    pass


class TelegramNotifier:
    """Класс для отправки уведомлений в Telegram"""
    
    def __init__(self, config: TelegramConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Создание HTTP сессии с retry логикой"""
        session = requests.Session()
        
        # Настройка retry стратегии
        retry_strategy = Retry(
            total=self.config.retry_attempts,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "POST"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def send_message(
        self, 
        message: str, 
        topic_type: str = "system",
        parse_mode: str = "HTML"
    ) -> bool:
        """
        Отправить сообщение в Telegram
        
        Args:
            message: Текст сообщения
            topic_type: Тип топика (system, trades, analysis, etc.)
            parse_mode: Режим парсинга (HTML, Markdown)
            
        Returns:
            True если сообщение отправлено успешно
        """
        try:
            topic_id = self.config.topics.get(topic_type, self.config.topics.get("system", None))
            
            url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"
            
            data = {
                'chat_id': self.config.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            if topic_id:
                data['message_thread_id'] = topic_id
            
            self.logger.debug(
                "Sending Telegram message",
                topic_type=topic_type,
                topic_id=topic_id,
                message_length=len(message)
            )
            
            response = self.session.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self.logger.debug("Telegram message sent successfully")
                    return True
                else:
                    error_msg = result.get('description', 'Unknown error')
                    self.logger.error(
                        "Telegram API error",
                        error=error_msg,
                        status_code=response.status_code
                    )
                    return False
            else:
                self.logger.error(
                    "Failed to send Telegram message",
                    status_code=response.status_code,
                    response_text=response.text
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error("Network error sending Telegram message", error=str(e))
            return False
        except Exception as e:
            self.logger.error("Unexpected error sending Telegram message", error=str(e))
            return False
    
    def send_system_start(self, system_info: Dict[str, Any]) -> bool:
        """Отправить уведомление о запуске системы"""
        message = (
            f"🚀 <b>Система запущена</b>\n"
            f"🕐 {system_info.get('start_time', 'N/A')}\n"
            f"💱 Валютные пары: {system_info.get('pairs', 'N/A')}\n"
            f"📊 Таймфреймы: {system_info.get('timeframes', 'N/A')}\n"
            f"🔢 Комбинаций: {system_info.get('combinations_count', 'N/A')}\n"
            f"⏱️ Режим: {system_info.get('mode', 'N/A')}"
        )
        
        return self.send_message(message, "system")
    
    def send_system_stop(self, system_info: Dict[str, Any]) -> bool:
        """Отправить уведомление об остановке системы"""
        message = (
            f"🛑 <b>Система остановлена</b>\n"
            f"🕐 {system_info.get('stop_time', 'N/A')}\n"
            f"⏰ Время работы: {system_info.get('uptime', 'N/A')}\n"
            f"🔄 Циклов: {system_info.get('cycles', 'N/A')}\n"
            f"✅ Успешных: {system_info.get('successful_cycles', 'N/A')}\n"
            f"💾 Загружено свечей: {system_info.get('candles_count', 'N/A')}\n"
            f"❌ Ошибок: {system_info.get('errors_count', 'N/A')}"
        )
        
        return self.send_message(message, "system")
    
    def send_error_notification(self, error_info: Dict[str, Any]) -> bool:
        """Отправить уведомление об ошибке"""
        message = (
            f"❌ <b>Ошибка системы</b>\n"
            f"🕐 {error_info.get('timestamp', 'N/A')}\n"
            f"🔍 Тип: {error_info.get('error_type', 'N/A')}\n"
            f"📝 Описание: {error_info.get('message', 'N/A')}\n"
            f"📍 Компонент: {error_info.get('component', 'N/A')}"
        )
        
        return self.send_message(message, "system")
    
    def send_heartbeat(self, stats: Dict[str, Any]) -> bool:
        """Отправить heartbeat с статистикой"""
        message = (
            f"💓 <b>Heartbeat</b>\n"
            f"🕐 {stats.get('timestamp', 'N/A')}\n"
            f"⏰ Время работы: {stats.get('uptime', 'N/A')}\n"
            f"🔄 Циклов: {stats.get('cycles', 'N/A')}\n"
            f"✅ Успешных: {stats.get('successful_cycles', 'N/A')}\n"
            f"💾 Свечей за час: {stats.get('candles_last_hour', 'N/A')}\n"
            f"📊 Активных пар: {stats.get('active_pairs', 'N/A')}"
        )
        
        return self.send_message(message, "system")
    
    def send_update_notification(self, update_info: Dict[str, Any]) -> bool:
        """Отправить уведомление об обновлении данных"""
        message = (
            f"📈 <b>Обновление данных</b>\n"
            f"🕐 {update_info.get('timestamp', 'N/A')}\n"
            f"⏱️ Длительность: {update_info.get('duration', 'N/A')}\n"
            f"💾 Новых свечей: {update_info.get('new_candles', 'N/A')}\n"
            f"✅ Успешных пар: {update_info.get('successful_pairs', 'N/A')}\n"
            f"❌ Ошибок: {update_info.get('errors', 'N/A')}"
        )
        
        return self.send_message(message, "system")
    
    def send_trade_notification(self, trade_info: Dict[str, Any]) -> bool:
        """Отправить уведомление о сделке"""
        direction_emoji = "📈" if trade_info.get('direction') == 'BUY' else "📉"
        
        message = (
            f"{direction_emoji} <b>Сделка {trade_info.get('direction', 'N/A')}</b>\n"
            f"💱 {trade_info.get('symbol', 'N/A')}\n"
            f"💰 Объем: {trade_info.get('volume', 'N/A')}\n"
            f"💵 Цена: {trade_info.get('price', 'N/A')}\n"
            f"📊 Таймфрейм: {trade_info.get('timeframe', 'N/A')}\n"
            f"🕐 Время: {trade_info.get('timestamp', 'N/A')}"
        )
        
        return self.send_message(message, "trades")
    
    def send_analysis_notification(self, analysis_info: Dict[str, Any]) -> bool:
        """Отправить уведомление об анализе"""
        message = (
            f"📊 <b>Анализ рынка</b>\n"
            f"💱 {analysis_info.get('symbol', 'N/A')}\n"
            f"📈 Сигнал: {analysis_info.get('signal', 'N/A')}\n"
            f"📊 Таймфрейм: {analysis_info.get('timeframe', 'N/A')}\n"
            f"🎯 Уверенность: {analysis_info.get('confidence', 'N/A')}%\n"
            f"📝 Комментарий: {analysis_info.get('comment', 'N/A')}\n"
            f"🕐 Время: {analysis_info.get('timestamp', 'N/A')}"
        )
        
        return self.send_message(message, "analysis")
    
    def test_connection(self) -> bool:
        """Тестирование подключения к Telegram API"""
        try:
            url = f"https://api.telegram.org/bot{self.config.bot_token}/getMe"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    bot_info = result.get('result', {})
                    self.logger.info(
                        "Telegram connection test successful",
                        bot_name=bot_info.get('first_name'),
                        bot_username=bot_info.get('username')
                    )
                    return True
            
            self.logger.error(
                "Telegram connection test failed",
                status_code=response.status_code,
                response_text=response.text
            )
            return False
            
        except Exception as e:
            self.logger.error("Telegram connection test failed", error=str(e))
            return False
    
    def close(self) -> None:
        """Закрыть HTTP сессию"""
        if self.session:
            self.session.close()
            self.logger.debug("Telegram session closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 
"""
Telegram notification system
"""

import requests
import time
from typing import Dict, Any, Optional
from urllib.parse import urljoin

from ..utils.logging import get_logger


class TelegramNotificationError(Exception):
    """Ошибка отправки уведомления в Telegram"""
    pass


class TelegramNotifier:
    """Отправка уведомлений в Telegram"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация Telegram уведомлений
        
        Args:
            config: Словарь с конфигурацией Telegram
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.base_url = "https://api.telegram.org/bot{}/".format(config.get('bot_token', ''))
        self.chat_id = config.get('chat_id')
        self.topics = config.get('topics', {})
        self.retry_attempts = config.get('retry_attempts', 3)
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Создание HTTP сессии с retry логикой"""
        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TradingSystem/1.0'
        })
        return session
    
    def send_message(self, message: str, topic: str = "system") -> bool:
        """
        Отправка сообщения в Telegram
        
        Args:
            message: Текст сообщения
            topic: Тема сообщения (system, trades, analysis, etc.)
            
        Returns:
            True если сообщение отправлено успешно
        """
        if not self.config.get('bot_token') or not self.chat_id:
            self.logger.warning("Telegram not configured, skipping message")
            return False
        
        try:
            # Определяем thread_id для топика
            thread_id = self.topics.get(topic, None)
            
            # Параметры запроса
            params = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            if thread_id:
                params['message_thread_id'] = thread_id
            
            # Отправка с retry логикой
            for attempt in range(self.retry_attempts):
                try:
                    response = self.session.post(
                        urljoin(self.base_url, "sendMessage"),
                        json=params,
                        timeout=10
                    )
                    response.raise_for_status()
                    
                    self.logger.debug(
                        "Message sent successfully",
                        topic=topic,
                        message_length=len(message)
                    )
                    return True
                    
                except requests.exceptions.RequestException as e:
                    if attempt < self.retry_attempts - 1:
                        self.logger.warning(
                            f"Failed to send message (attempt {attempt + 1}/{self.retry_attempts})",
                            error=str(e)
                        )
                        time.sleep(2 ** attempt)  # Экспоненциальная задержка
                    else:
                        raise
            
        except Exception as e:
            self.logger.error(
                "Failed to send Telegram message",
                topic=topic,
                error=str(e)
            )
            raise TelegramNotificationError(f"Failed to send message: {e}")
    
    def send_system_start(self, system_info: Dict[str, Any]) -> bool:
        """Отправка уведомления о запуске системы"""
        message = (
            f"🚀 <b>Система запущена</b>\n"
            f"🕐 {system_info.get('start_time', 'N/A')}\n"
            f"💱 Пар: {system_info.get('pairs', 'N/A')}\n"
            f"📊 Таймфреймы: {system_info.get('timeframes', 'N/A')}\n"
            f"🔢 Комбинаций: {system_info.get('combinations_count', 'N/A')}\n"
            f"⚡ Режим: {system_info.get('mode', 'N/A')}"
        )
        return self.send_message(message, "system")
    
    def send_system_stop(self, system_info: Dict[str, Any]) -> bool:
        """Отправка уведомления об остановке системы"""
        message = (
            f"🛑 <b>Система остановлена</b>\n"
            f"🕐 {system_info.get('stop_time', 'N/A')}\n"
            f"⏱️ Время работы: {system_info.get('uptime', 'N/A')}\n"
            f"🔄 Циклов: {system_info.get('cycles', 'N/A')}\n"
            f"✅ Успешных: {system_info.get('successful_cycles', 'N/A')}\n"
            f"💾 Свечей: {system_info.get('candles_count', 'N/A')}\n"
            f"❌ Ошибок: {system_info.get('errors_count', 'N/A')}"
        )
        return self.send_message(message, "system")
    
    def send_error_notification(self, error_info: Dict[str, Any]) -> bool:
        """Отправка уведомления об ошибке"""
        message = (
            f"❌ <b>Ошибка системы</b>\n"
            f"🕐 {error_info.get('timestamp', 'N/A')}\n"
            f"🔧 Компонент: {error_info.get('component', 'N/A')}\n"
            f"📝 Тип: {error_info.get('error_type', 'N/A')}\n"
            f"💬 Сообщение: {error_info.get('message', 'N/A')}"
        )
        return self.send_message(message, "system")
    
    def send_heartbeat(self, stats: Dict[str, Any]) -> bool:
        """Отправка heartbeat уведомления"""
        message = (
            f"💓 <b>Heartbeat</b>\n"
            f"🕐 {stats.get('timestamp', 'N/A')}\n"
            f"⏱️ Время работы: {stats.get('uptime', 'N/A')}\n"
            f"🔄 Циклов: {stats.get('cycles', 'N/A')}\n"
            f"✅ Успешных: {stats.get('successful_cycles', 'N/A')}\n"
            f"💾 Свечей за час: {stats.get('candles_last_hour', 'N/A')}\n"
            f"💱 Активных пар: {stats.get('active_pairs', 'N/A')}"
        )
        return self.send_message(message, "system")
    
    def send_update_notification(self, update_info: Dict[str, Any]) -> bool:
        """Отправка уведомления об обновлении данных"""
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
        """Отправка уведомления о сделке"""
        message = (
            f"💰 <b>Сделка {trade_info.get('action', 'N/A')}</b>\n"
            f"💱 {trade_info.get('symbol', 'N/A')}\n"
            f"📊 Объем: {trade_info.get('volume', 'N/A')}\n"
            f"💵 Цена: {trade_info.get('price', 'N/A')}\n"
            f"📈 Прибыль: {trade_info.get('profit', 'N/A')}\n"
            f"🕐 {trade_info.get('timestamp', 'N/A')}"
        )
        return self.send_message(message, "trades")
    
    def send_analysis_notification(self, analysis_info: Dict[str, Any]) -> bool:
        """Отправка уведомления об анализе"""
        message = (
            f"📊 <b>Анализ рынка</b>\n"
            f"💱 {analysis_info.get('symbol', 'N/A')}\n"
            f"📈 Сигнал: {analysis_info.get('signal', 'N/A')}\n"
            f"💪 Сила: {analysis_info.get('strength', 'N/A')}\n"
            f"📝 Описание: {analysis_info.get('description', 'N/A')}\n"
            f"🕐 {analysis_info.get('timestamp', 'N/A')}"
        )
        return self.send_message(message, "analysis")
    
    def test_connection(self) -> bool:
        """Тестирование подключения к Telegram"""
        try:
            if not self.config.get('bot_token') or not self.chat_id:
                return False
            
            response = self.session.get(
                urljoin(self.base_url, "getMe"),
                timeout=10
            )
            response.raise_for_status()
            
            bot_info = response.json()
            if bot_info.get('ok'):
                self.logger.info(
                    "Telegram connection test successful",
                    bot_name=bot_info['result'].get('first_name', 'Unknown')
                )
                return True
            
            return False
            
        except Exception as e:
            self.logger.error("Telegram connection test failed", error=str(e))
            return False
    
    def close(self) -> None:
        """Закрытие HTTP сессии"""
        try:
            self.session.close()
            self.logger.info("Telegram notifier session closed")
        except Exception as e:
            self.logger.error("Error closing Telegram session", error=str(e))
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 
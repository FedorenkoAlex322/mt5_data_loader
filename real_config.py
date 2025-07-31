# -*- coding: utf-8 -*-

from dotenv import load_dotenv
import os
load_dotenv()

"""
Конфигурация для реал-тайм торговой системы Ишимоку
Все времена в UTC, все сообщения на украинском языке
Поддержка множественных валютных пар и таймфреймов
"""

from datetime import datetime

# ==================== ВАЛЮТНЫЕ ПАРЫ И ТАЙМФРЕЙМЫ ====================
# Поддерживаемые таймфреймы с их ID в базе данных
TIMEFRAMES = {
    'M5': {
        'id': 3,
        'oanda_format': 'M5',
        'minutes': 5,
        'description': '5 минут'
    },
    'M15': {
        'id': 4, 
        'oanda_format': 'M15',
        'minutes': 15,
        'description': '15 минут'
    },
    'M30': {
        'id': 8,
        'oanda_format': 'M30', 
        'minutes': 30,
        'description': '30 минут'
    },
    'H1': {
        'id': 5,
        'oanda_format': 'H1',
        'minutes': 60,
        'description': '1 час'
    },
    'H4': {
        'id': 6,
        'oanda_format': 'H4',
        'minutes': 240,
        'description': '4 часа'
    },
    'D1': {
        'id': 7,
        'oanda_format': 'D',
        'minutes': 1440,
        'description': '1 день'
    }
}

# Конфигурация валютных пар для загрузки данных
CURRENCY_PAIRS = [
    {
        'symbol': 'EUR_USD',
        'symbol_id': 7,
        'enabled': True,
        'priority': 1,  # Приоритет загрузки (1 = высший)
        'pip_size': 0.0001,
        'min_trade_size': 1,
        'description': 'Евро / Доллар США'
    },
    {
        'symbol': 'GBP_USD', 
        'symbol_id': 6,
        'enabled': True,
        'priority': 1,
        'pip_size': 0.0001,
        'min_trade_size': 1,
        'description': 'Фунт / Доллар США'
    },
    {
        'symbol': 'USD_CAD',
        'symbol_id': 9, 
        'enabled': True,
        'priority': 1,
        'pip_size': 0.0001,
        'min_trade_size': 1,
        'description': 'Доллар США / Канадский доллар'
    },
    {
        'symbol': 'USD_CHF',
        'symbol_id': 10,
        'enabled': True,  # Отключена по умолчанию
        'priority': 1,
        'pip_size': 0.0001,
        'min_trade_size': 1,
        'description': 'Доллар США / Швейцарский франк'
    },
    {
        'symbol': 'NZD_USD',
        'symbol_id': 11,
        'enabled': False,  # Отключена по умолчанию
        'priority': 5,
        'pip_size': 0.0001,
        'min_trade_size': 1,
        'description': 'Новозеландский доллар / Доллар США'
    },
    {
        'symbol': 'AUD_USD',
        'symbol_id': 8,
        'enabled': True,  # Отключена по умолчанию
        'priority': 1,
        'pip_size': 0.0001,
        'min_trade_size': 1,
        'description': 'Новозеландский доллар / Доллар США'
    },
    {
        'symbol': 'EUR_GBP',
        'symbol_id': 12,
        'enabled': True,  # Отключена по умолчанию
        'priority': 1,
        'pip_size': 0.0001,
        'min_trade_size': 1,
        'description': 'Евро / Фунт Стерлингов'
    },
    {
        'symbol': 'EUR_JPY',
        'symbol_id': 13,
        'enabled': False,  # Отключена - японская валюта
        'priority': 6,
        'pip_size': 0.01,
        'min_trade_size': 1,
        'description': 'Евро / Японская иена'
    },
    {
        'symbol': 'GBP_CHF',
        'symbol_id': 14,
        'enabled': False,  # Отключена по умолчанию
        'priority': 6,
        'pip_size': 0.0001,
        'min_trade_size': 1,
        'description': 'Фунт / Швейцарский франк'
    },
    {
        'symbol': 'CHF_JPY',
        'symbol_id': 15,
        'enabled': False,  # Отключена - японская валюта
        'priority': 6,
        'pip_size': 0.01,
        'min_trade_size': 1,
        'description': 'Швейцарский франк / Японская иена'
    },
    {
        'symbol': 'AUD_NZD',
        'symbol_id': 16,
        'enabled': False,  # Отключена по умолчанию
        'priority': 6,
        'pip_size': 0.0001,
        'min_trade_size': 1,
        'description': 'Новозеландский доллар / Доллар США'
    },
    {
        'symbol': 'EUR_AUD',
        'symbol_id': 17,
        'enabled': True,  # Отключена по умолчанию
        'priority': 1,
        'pip_size': 0.0001,
        'min_trade_size': 1,
        'description': 'Новозеландский доллар / Доллар США'
    },
    {
        'symbol': 'GBP_AUD',
        'symbol_id': 18,
        'enabled': True,  # Отключена по умолчанию
        'priority': 1,
        'pip_size': 0.0001,
        'min_trade_size': 1,
        'description': 'Новозеландский доллар / Доллар США'
    },
    {
        'symbol': 'USD_TRY',
        'symbol_id': 19,
        'enabled': False,  # Отключена - турецкая валюта
        'priority': 6,
        'pip_size': 0.0001,
        'min_trade_size': 1,
        'description': 'Доллар США / Турецкая лира'
    },
    {
        'symbol': 'USD_ZAR',
        'symbol_id': 20,
        'enabled': False,  # Отключена по умолчанию
        'priority': 6,
        'pip_size': 0.0001,
        'min_trade_size': 1,
        'description': 'Доллар США / Южноафриканский рэнд'
    },
    {
        'symbol': 'USD_SGD',
        'symbol_id': 21,
        'enabled': False,  # Отключена - сингапурская валюта
        'priority': 6,
        'pip_size': 0.0001,
        'min_trade_size': 1,
        'description': 'Доллар США / Сингапурский доллар'
    },
    {
        'symbol': 'EUR_NOK',
        'symbol_id': 22,
        'enabled': False,  # Отключена по умолчанию
        'priority': 6,
        'pip_size': 0.0001,
        'min_trade_size': 1,
        'description': 'Новозеландский доллар / Доллар США'
    }
]

# Активные таймфреймы для загрузки (можно настроить какие нужны)
ACTIVE_TIMEFRAMES = ['M5', 'M15', 'M30', 'H1', 'H4', 'D1']

# ==================== ТОРГОВАЯ СИСТЕМА ====================
# Таймфрейм для мультипарной торговой системы (только один!)
TRADING_TIMEFRAME_ID = 4  # ID таймфрейма для торговли (4 = M15)

# Примеры ID таймфреймов:
# 3 = M5 (5 минут)
# 4 = M15 (15 минут) 
# 5 = H1 (1 час)
# 6 = H4 (4 часа)
# 8 = M30 (30 минут)

# ==================== ОСНОВНЫЕ НАСТРОЙКИ ====================
REAL_SYSTEM_CONFIG = {
    'name': 'Ишимоку Multi-Pair Real-Time System',
    'version': '2.0.0',
    'timezone': 'UTC',  # Все времена в UTC
    'multi_pair_mode': True,  # Режим множественных пар
}

# ==================== ОБНОВЛЕНИЕ ДАННЫХ ====================
DATA_UPDATE_CONFIG = {
    'update_interval': 60,  # Интервал обновления данных (секунды) - уменьшено для снижения нагрузки
    'retry_interval': 60,    # Интервал повтора при ошибке (секунды)
    'max_retries': 5,        # Максимальное количество попыток
    'candles_to_fetch': 1000, # Количество свечей для загрузки за раз - уменьшено для снижения нагрузки
    'parallel_downloads': True,  # Параллельная загрузка пар
    'max_workers': 5,        # Максимум потоков для параллельной загрузки - увеличено для ускорения
    'stagger_delay': 0.2,    # Задержка между запуском загрузки пар (секунды)
    
    # Умное расписание по таймфреймам
    'smart_schedule_mode': False,   # Включить умное расписание
    'schedule_second': 4,          # Секунда для запуска (все таймфреймы в :02 секунды)
    'initial_history_download': False,  # Включить первоначальную докачку истории
    'history_download_days': 30,       # Количество дней истории для докачки
    
    # Расписание для каждого таймфрейма
    'timeframe_schedules': {
        'M5': {
            'interval_minutes': 5,     # Каждые 5 минут
            'offset_seconds': 2,       # В :02 секунды
            'enabled': True
        },
        'M15': {
            'interval_minutes': 15,    # Каждые 15 минут  
            'offset_seconds': 2,       # В :02 секунды
            'enabled': True
        },
        'M30': {
            'interval_minutes': 30,    # Каждые 30 минут
            'offset_seconds': 2,       # В :02 секунды
            'enabled': True
        },
        'H1': {
            'interval_minutes': 60,    # Каждый час
            'offset_seconds': 2,       # В :02 секунды
            'enabled': True
        },
        'H4': {
            'interval_minutes': 240,   # Каждые 4 часа
            'offset_seconds': 2,       # В :02 секунды
            'enabled': True
        },
        'D1': {
            'interval_minutes': 1440,  # Каждый день (24 часа * 60 минут)
            'offset_seconds': 2,       # В :02 секунды
            'enabled': True
        }
    },
    
    # Настройки группировки и оптимизации
    'group_concurrent_timeframes': True,  # Группировать совпадающие таймфреймы
    'batch_delay_between_groups': 1,      # Задержка между группами таймфреймов (секунды)
    'max_pairs_per_batch': 17,            # Максимум пар в одном батче (все наши пары)
}

# ==================== MT5 API ====================

MT5_CONFIG = {
    'login': os.getenv("NT5_LOGIN"),
    'password': os.getenv("NT5_PASSWORD"),
    'server': os.getenv("NT5_SERVER"),
    'terminal_path': os.getenv("NT5_TERMINAL_PATH")
}


# ==================== ТОРГОВЫЕ НАСТРОЙКИ ====================
TRADING_CONFIG = {
    'max_concurrent_positions': 1,  # Максимум одна позиция
    'max_trades_per_cycle': 10,      # Максимум сделок за один цикл проверки
    'position_sizing': {
        'method': 'risk_percentage',  # Метод расчета размера позиции: 'risk_percentage' или 'fixed_investment'
        'investment_percentage': 1.5,  # Процент от баланса для инвестиции в сделку
        'risk_percentage': 0.1,        # Процент риска от баланса (для risk_percentage метода)
        'max_position_size': 2000000,  # 🔧 УВЕЛИЧЕНО: Максимальный размер позиции (до 20 стандартных лотов)
        'min_position_size': 1,        # Минимальный размер позиции (единицы)
    },
    # 🔥 НОВАЯ ПРОАКТИВНАЯ СТРАТЕГИЯ: Только лимитные ордера
    'proactive_limit_strategy': {
        'enabled': True,                         # Включить проактивную стратегию
        'market_orders_disabled': True,          # ПОЛНОСТЬЮ отключить market ордера
        'entry_point': 'kijun_line',            # Точка входа: всегда на линии Kijun
        'create_on_stable_kijun': True,          # Создавать ордер при стабильном Kijun
        'infinite_lifetime': True,               # Бесконечное время жизни (до отмены по условиям)
        'dynamic_modification': True,            # Динамическая модификация цены
        'signal_prioritization': True,           # Приоритизация сигналов по силе
        'higher_timeframe_check': True,          # Проверка подтверждения на старшем ТФ
        
        # 🆕 СТАБИЛЬНОСТЬ KIJUN для проактивной стратегии
        'kijun_stability_tolerance': 1.0,        # Допустимое отклонение Kijun в пипсах
        'min_tk_distance_pips': 5,               # Минимальное расстояние T-K для создания ордера
        'max_tk_distance_pips': 50,              # Максимальное расстояние T-K для создания ордера
        'entry_delta': 0.0002,                   # 🆕 ДЕЛЬТА ВХОДА: LONG=Kijun+дельта, SHORT=Kijun-дельта (1 пипс)
        
        # Управление модификациями
        'modification_settings': {
            'max_modifications_per_order': 5,    # Максимум модификаций одного ордера
            'modification_interval_seconds': 60, # Минимальный интервал между модификациями
        },
        
        # Приоритизация сигналов
        'signal_scoring': {
            'enabled': True,                     # Включить систему scoring
            'min_score_for_creation': 40,        # Минимальный score для создания ордера
            'tenkan_kijun_distance_weight': 40,  # Вес расстояния T-K (из 100)
            'cloud_position_weight': 30,         # Вес позиции облака
            'filters_weight': 30,                # Вес дополнительных фильтров
        },
        
        # Многоуровневый мониторинг
        'multi_timeframe': {
            'enabled': True,                     # Включить проверку старшего ТФ
            'higher_timeframe_id': 5,            # 🔧 ИСПРАВЛЕНО: H1 для подтверждения M15 сигналов (было 4=M15)
            'require_confirmation': False,        # НЕ требовать подтверждения (только для анализа)
            'conflicting_signal_action': 'warn', # 'warn', 'cancel', 'ignore'
        }
    },
    'smart_entry': {
        'enabled': False,  # 🔥 ОТКЛЮЧЕНО: заменено на proactive_limit_strategy
        'max_distance_for_market_order': 3,    # Неиспользуется в новой стратегии
        'pending_order_lifetime': 20,         # Неиспользуется в новой стратегии
        'condition_recheck_interval': 10,      # Интервал переоценки условий (минуты)
        'min_distance_for_pending': 4,         # Неиспользуется в новой стратегии
        'max_distance_for_pending': 50,        # Неиспользуется в новой стратегии
        'recheck_filters': True,                # Переоценивать фильтры Ишимоку при проверке
        'recheck_ichimoku_signal': True,        # Переоценивать сигнал Tenkan-Kijun при проверке
        'cancel_on_signal_change': True,        # Отменять ордер при изменении сигнала
    },
    'stop_loss': {
        'method': 'fixed',            # Метод расчета стоп-лосса (синхронизировано с бэктестом)
        'fixed_pips': 12,            # Фиксированный SL в пунктах (синхронизировано с бэктестом)
        'atr_multiplier': 1.5,        # Множитель ATR для SL
        'min_sl_pips': 8,           # Минимальный SL в пунктах
        'max_sl_pips': 50,           # Максимальный SL в пунктах
    },
    'take_profit': {
        'enabled': False,  # 🚫 ОТКЛЮЧЕНО: трейлинг стоп обеспечивает лучшее управление прибылью
        'risk_reward_ratio': 1.5,    # Соотношение риск/прибыль (не используется при enabled: False)
    },
    'trailing_stop': {
        'enabled': True,
        'mode': 'close',             # 'close' или 'extremum' (синхронизировано с бэктестом)
        'activation_profit': 0.1,      # 🔧 ИСПРАВЛЕНО для M15: Прибыль для активации (пункты) (было 0.1)
        'trailing_distance': 0.7,      # 🔧 ИСПРАВЛЕНО для M15: Дистанция трейлинга (пункты) (было 0.3)
        'ignore_take_profit': True,   # Игнорировать TP при активном трейлинге (синхронизировано с бэктестом)
        'move_to_breakeven': True,    # Переміщення в беззбиток (из бэктеста)
        'breakeven_profit': 12         # 🔧 ОПТИМИЗИРОВАНО: раньше беззбиток для защиты прибыли
    }
}

# ==================== УПРАВЛЕНИЕ РИСКАМИ ====================
RISK_MANAGEMENT = {
    'max_daily_loss': 500.0,        # Максимальный дневной убыток (USD)
    'max_drawdown': 20.0,           # Максимальная просадка (%)
    'min_balance': 1000.0,          # Минимальный баланс для торговли (USD)
    'daily_profit_target': 200.0,   # Дневная цель прибыли (USD)
    'stop_on_target': False,        # Остановить торговлю при достижении цели
    'cooling_period': 3600,         # Период охлаждения после больших убытков (секунды)
}

# ==================== ТЕЛЕГРАМ УВЕДОМЛЕНИЯ ====================
topics_raw = os.getenv("TELEGRAM_TOPICS")
topics = dict(item.split(":") for item in topics_raw.split(","))
topics = {k: int(v) for k, v in topics.items()}
TELEGRAM_CONFIG = {
    'bot_token': os.getenv("TELEGRAM_TOKEN"),
    'chat_id': os.getenv("TELEGRAM_CHAT_ID"),
    'topics': topics,
    'retry_attempts': 3,
    'retry_delay': 5,
    # Настройки фильтрации уведомлений
    'analysis_filter': {
        'send_all_signals': False,      # True = все проверки, False = только разрешенные к входу
        'send_only_tradeable': True,    # Отправлять только сигналы с разрешением на торговлю
        'disable_analysis_messages': True,  # 🔧 ОТКЛЮЧИТЬ отправку детальных анализов в топик 222
    },
}

# ==================== БАЗА ДАННЫХ ====================
DATABASE_CONFIG = {
    'host': os.getenv("POSTGRES_HOST"),
    'port': os.getenv("POSTGRES_PORT"),
    'database': os.getenv("POSTGRES_DB"),
    'user': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD"),
    'timezone': os.getenv("POSTGRES_TIMEZONE"),  # Принудительно устанавливаем UTC
}

# ==================== РАСЧЕТ ИНДИКАТОРОВ ====================
INDICATORS_CONFIG = {
    'ichimoku': {
        'tenkan_period': 9,
        'kijun_period': 26,
        'senkou_b_period': 52,
        'displacement': 26,
        'min_lines_distance': 3,    # Уменьшил с 5 до 3 для более точного расчета
        'entry_slippage_pips': 0,
    },
    'min_bars_required': 150,  # Минимум баров для корректных расчетов
}

# ==================== ФИЛЬТРЫ ИШИМОКУ ====================
ICHIMOKU_FILTERS = {
    'enabled': True,               # Включить систему фильтров для анализа
    'min_score_threshold': 60,     # Минимальный порог для прохождения фильтров
    
    # 🔥 НОВЫЙ ФИЛЬТР #0: Стабильность Kijun (ВЫСШИЙ ПРИОРИТЕТ)
    'kijun_stability': {
        'enabled': True,             # Включить фильтр стабильности Kijun
        'critical': True,            # 🆕 КРИТИЧНЫЙ фильтр - блокирует всё если не прошел
        'tolerance_pips': 0.5,       # 🔧 ТЕСТ: 0.5 пипса = 5 пунктов для EUR/USD (было 0.2)
        'modification_tolerance': 0.5, # 🆕 До 0.5п - модифицируем ордер
        'cancellation_threshold': 1.0, # 🆕 Свыше 1п - отменяем ордер
        'wait_for_stable': True,     # Ждать стабилизации Kijun перед входом
        'auto_modify_order': True,   # 🆕 Автоматически модифицировать ордер при небольших изменениях
        'description': 'Проверка стабильности Kijun между текущей и предыдущей свечами'
    },
    
    # 🆕 ФИЛЬТР #1: Расстояние Tenkan-Kijun (КРИТИЧНЫЙ)
    'tenkan_kijun_distance': {
        'enabled': True,             # Включить фильтр расстояния
        'critical': True,            # 🆕 КРИТИЧНЫЙ фильтр
        'min_distance_pips': 5,      # Минимальное расстояние T-K в пипсах
        'max_distance_pips': 50,     # Максимальное расстояние T-K в пипсах
        'optimal_range_min': 10,     # Оптимальный диапазон начало
        'optimal_range_max': 30,     # Оптимальный диапазон конец
        'description': 'Проверка расстояния между Tenkan и Kijun'
    },
    
    # 🆕 ФИЛЬТР #2: Направление сигнала (КРИТИЧНЫЙ)
    'signal_direction': {
        'enabled': True,             # Включить фильтр направления
        'critical': True,            # 🆕 КРИТИЧНЫЙ фильтр
        'require_clear_signal': True, # Требовать четкого сигнала (не нейтрального)
        'description': 'Проверка направления сигнала Tenkan-Kijun'
    },
    
    # 🎯 ФИЛЬТР #1: Позиция относительно облака
    'kumo_position': {
        'enabled': True,           # Включить фильтр позиции
        'critical': False,         # 🆕 НЕ критичный фильтр (только для анализа)
        'long_above_kumo': True,   # Long только выше облака
        'short_below_kumo': True,  # Short только ниже облака  
        'avoid_inside_kumo': True, # НЕ торговать внутри облака
        'buffer_pips': 3,          # Буфер от границы облака (синхронизировано с бэктестом)
        'description': 'Проверка позиции цены относительно облака'
    },
    
    # 🎯 ФИЛЬТР #2: Направление облака
    'kumo_direction': {
        'enabled': True,                # Включить фильтр направления
        'critical': False,              # 🆕 НЕ критичный фильтр (только для анализа)
        'bullish_kumo_long_only': True,  # Long только при зеленом облаке
        'bearish_kumo_short_only': True, # Short только при красном облаке
        'check_future_kumo': True,       # Проверять будущее облако (как в бэктесте)
        'description': 'Проверка направления (цвета) облака Ишимоку'
    },
    
    # 🎯 ФИЛЬТР #3: Толщина облака  
    'kumo_thickness': {
        'enabled': True,            # Включить фильтр толщины
        'critical': False,          # 🆕 НЕ критичный фильтр (только для анализа)
        'min_thickness_pips': 10,   # Минимальная толщина облака (синхронизировано с бэктестом)
        'thick_threshold_pips': 20, # Порог толстого облака (синхронизировано с бэктестом)
        'avoid_thin_kumo': True,    # Избегать тонкое облако
        'description': 'Проверка толщины облака Ишимоку'
    },
    
    # 🎯 ФИЛЬТР #4: Chikou Span (из бэктеста: +3-5% винрейт)
    'chikou_span': {
        'enabled': True,                 # Включить фильтр Chikou (активируем как в бэктесте)
        'critical': False,               # 🆕 НЕ критичный по умолчанию (можно включить для тестирования)
        'chikou_above_price_long': True,  # Long: Chikou выше цены 26 баров назад
        'chikou_below_price_short': True, # Short: Chikou ниже цены 26 баров назад
        'chikou_clear_space': True,       # Chikou в свободном пространстве
        'min_distance_pips': 10,         # 🆕 Минимальное расстояние для "свободного пространства"
        'description': 'Проверка позиции Chikou Span относительно исторических данных'
    },
    
    # 🎯 ФИЛЬТР #5: Направление Kijun (отключен для простоты)
    'kijun_direction': {
        'enabled': False,            # Включить фильтр направления Kijun
        'long_rising_kijun': True,   # Long только при растущем Kijun
        'short_falling_kijun': True, # Short только при падающем Kijun
        'min_angle_pips': 3,         # Минимальный угол наклона
        'check_periods': 3,          # Проверять направление за N баров
    },
    
    # 🎯 ФИЛЬТР #6: Качество касания (отключен для простоты)
    'kijun_touch_quality': {
        'enabled': False,            # Включить фильтр качества касания
        'max_touches_in_period': 2,  # Максимум касаний за период
        'period_bars': 20,           # Период для подсчета касаний
        'min_time_between_bars': 5,  # Минимум баров между касаниями
        'clean_touch_only': True,    # Только "чистые" касания
    }
}

# ==================== ЛОГИРОВАНИЕ ====================
LOGGING_CONFIG = {
    'level': 'INFO',
    'file': 'real_trading_system.log',
    'max_file_size': 50 * 1024 * 1024,  # 50MB
    'backup_count': 5,
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
}

# ==================== МОНИТОРИНГ СИСТЕМЫ ====================
MONITORING_CONFIG = {
    'heartbeat_interval': 300,  # Интервал heartbeat (секунды)
    'candle_check_interval': 30,  # Интервал проверки новых свечей (секунды)
    'performance_tracking': True,
    'trade_analytics': True,
    'save_analytics_interval': 3600,  # Сохранение аналитики (секунды)
}

# ==================== РЕЖИМЫ РАБОТЫ ====================
OPERATION_MODES = {
    'live_trading': True,       # Реальная торговля
    'paper_trading': False,     # Бумажная торговля
    'analysis_only': False,     # Только анализ без торговли
    'maintenance_mode': False,  # Режим обслуживания
}

# ==================== ВРЕМЕННЫЕ ФИЛЬТРЫ ====================
TRADING_HOURS = {
    'enabled': False,  # Отключено - торгуем круглосуточно
    'start_hour': 8,   # Начало торговли (UTC)
    'end_hour': 17,    # Конец торговли (UTC)
    'trading_days': [0, 1, 2, 3, 4],  # Пн-Пт (0=Понедельник)
}

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def get_enabled_pairs():
    """Получение списка включенных валютных пар"""
    return [pair for pair in CURRENCY_PAIRS if pair['enabled']]

def get_all_pairs():
    """Получение списка ВСЕХ валютных пар независимо от enabled статуса"""
    return CURRENCY_PAIRS

def get_pair_by_symbol(symbol: str):
    """Получение конфигурации пары по символу"""
    for pair in CURRENCY_PAIRS:
        if pair['symbol'] == symbol:
            return pair
    return None

def get_pair_by_id(symbol_id: int):
    """Получение конфигурации пары по ID"""
    for pair in CURRENCY_PAIRS:
        if pair['symbol_id'] == symbol_id:
            return pair
    return None

def get_timeframe_by_name(timeframe_name: str):
    """Получение конфигурации таймфрейма по имени"""
    return TIMEFRAMES.get(timeframe_name)

def get_all_combinations():
    """Получение всех активных комбинаций пар и таймфреймов"""
    combinations = []
    enabled_pairs = get_enabled_pairs()
    
    # Находим таймфрейм по ID
    trading_timeframe = None
    trading_timeframe_name = None
    
    for tf_name, tf_config in TIMEFRAMES.items():
        if tf_config['id'] == TRADING_TIMEFRAME_ID:
            trading_timeframe = tf_config
            trading_timeframe_name = tf_name
            break
    
    if not trading_timeframe:
        raise ValueError(f"Таймфрейм с ID {TRADING_TIMEFRAME_ID} не найден в конфигурации TIMEFRAMES")
    
    # Создаем комбинации только для одного торгового таймфрейма
    for pair in enabled_pairs:
        combinations.append({
            'symbol': pair['symbol'],
            'symbol_id': pair['symbol_id'],
            'timeframe': trading_timeframe_name,
            'timeframe_id': trading_timeframe['id'],
            'oanda_format': trading_timeframe['oanda_format'],
            'priority': pair['priority'],
            'description': f"{pair['description']} {trading_timeframe['description']}"
        })
    
    # Сортируем по приоритету пары
    combinations.sort(key=lambda x: x['priority'])
    return combinations

def get_pair_combinations(symbol: str):
    """Получение всех таймфреймов для конкретной пары"""
    pair = get_pair_by_symbol(symbol)
    if not pair or not pair['enabled']:
        return []
    
    combinations = []
    for tf_name in ACTIVE_TIMEFRAMES:
        tf_config = TIMEFRAMES[tf_name]
        combinations.append({
            'symbol': symbol,
            'symbol_id': pair['symbol_id'],
            'timeframe': tf_name,
            'timeframe_id': tf_config['id'],
            'oanda_format': tf_config['oanda_format'],
            'description': f"{pair['description']} {tf_config['description']}"
        })
    
    return combinations

def get_data_download_combinations():
    """Получение ВСЕХ комбинаций пар и таймфреймов для загрузки данных (независимо от enabled статуса)"""
    combinations = []
    all_pairs = get_all_pairs()  # Берем ВСЕ пары, не только enabled
    
    # Создаем комбинации для всех пар и всех активных таймфреймов
    for pair in all_pairs:
        for tf_name in ACTIVE_TIMEFRAMES:
            tf_config = TIMEFRAMES[tf_name]
            combinations.append({
                'symbol': pair['symbol'],
                'symbol_id': pair['symbol_id'],
                'timeframe': tf_name,
                'timeframe_id': tf_config['id'],
                'oanda_format': tf_config['oanda_format'],
                'priority': pair['priority'],
                'enabled': pair['enabled'],  # Сохраняем статус для информации
                'description': f"{pair['description']} {tf_config['description']}"
            })
    
    # Сортируем по приоритету пары
    combinations.sort(key=lambda x: x['priority'])
    return combinations

# ==================== ФУНКЦИИ ВАЛИДАЦИИ ====================
def validate_config():
    """Проверка корректности конфигурации"""
    errors = []
    
    # Проверяем обязательные параметры
    if not OANDA_CONFIG.get('api_key'):
        errors.append("OANDA API ключ не указан")
    
    if not TELEGRAM_CONFIG.get('bot_token'):
        errors.append("Telegram bot token не указан")
    
    if RISK_MANAGEMENT['max_drawdown'] <= 0:
        errors.append("Максимальная просадка должна быть больше 0")
    
    if TRADING_CONFIG['position_sizing']['risk_percentage'] <= 0:
        errors.append("Процент риска должен быть больше 0")
    
    # Проверяем валютные пары
    enabled_pairs = get_enabled_pairs()
    if not enabled_pairs:
        errors.append("Нет включенных валютных пар")
    
    # Проверяем таймфреймы
    if not ACTIVE_TIMEFRAMES:
        errors.append("Нет активных таймфреймов")
    
    for tf_name in ACTIVE_TIMEFRAMES:
        if tf_name not in TIMEFRAMES:
            errors.append(f"Неизвестный таймфрейм: {tf_name}")
    
    return errors

def get_active_config():
    """Получение активной конфигурации с валидацией"""
    errors = validate_config()
    if errors:
        raise ValueError(f"Ошибки конфигурации: {'; '.join(errors)}")
    
    # Для совместимости с однопарной системой добавляем параметры первой пары
    primary_pair = get_enabled_pairs()[0] if get_enabled_pairs() else CURRENCY_PAIRS[0]
    primary_timeframe_name = None
    for tf_name, tf_config in TIMEFRAMES.items():
        if tf_config['id'] == TRADING_TIMEFRAME_ID:
            primary_timeframe_name = tf_name
            break
    
    # Создаем секцию system для совместимости с real.py
    system_config = REAL_SYSTEM_CONFIG.copy()
    system_config.update({
        'symbol': primary_pair['symbol'],
        'symbol_id': primary_pair['symbol_id'],
        'timeframe': primary_timeframe_name or 'M15',
        'timeframe_id': TRADING_TIMEFRAME_ID,
    })
    
    return {
        'system': system_config,
        'data_update': DATA_UPDATE_CONFIG,
        'mt5' : MT5_CONFIG,
        'trading': TRADING_CONFIG,
        'risk': RISK_MANAGEMENT,
        'telegram': TELEGRAM_CONFIG,
        'database': DATABASE_CONFIG,
        'indicators': INDICATORS_CONFIG,
        'ichimoku_filters': ICHIMOKU_FILTERS,
        'logging': LOGGING_CONFIG,
        'monitoring': MONITORING_CONFIG,
        'operation': OPERATION_MODES,
        'trading_hours': TRADING_HOURS,
        # Новые секции для мульти-пар режима
        'currency_pairs': CURRENCY_PAIRS,
        'timeframes': TIMEFRAMES,
        'active_timeframes': ACTIVE_TIMEFRAMES,
        'trading_timeframe_id': TRADING_TIMEFRAME_ID,
        'combinations': get_all_combinations(),
        'data_download_combinations': get_data_download_combinations(),
    }

# ==================== КОНСТАНТЫ ====================
# Статусы системы
SYSTEM_STATUS = {
    'STARTING': 'STARTING',
    'RUNNING': 'RUNNING',
    'STOPPING': 'STOPPING',
    'STOPPED': 'STOPPED',
    'ERROR': 'ERROR',
    'MAINTENANCE': 'MAINTENANCE'
}

# Типы уведомлений
NOTIFICATION_TYPES = {
    'SYSTEM_START': 'system_start',
    'SYSTEM_STOP': 'system_stop',
    'TRADE_OPEN': 'trade_open',
    'TRADE_CLOSE': 'trade_close',
    'ERROR': 'error',
    'WARNING': 'warning',
    'ANALYSIS': 'analysis',
    'HEARTBEAT': 'heartbeat'
}

 
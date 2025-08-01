# Trading Data Loader

Система загрузки торговых данных с MetaTrader5 для анализа и торговли.

## 🚀 Возможности

- **Реальное время**: Загрузка данных в реальном времени с MetaTrader5
- **Исторические данные**: Загрузка исторических данных за указанный период
- **Множественные пары**: Поддержка множественных валютных пар
- **Множественные таймфреймы**: Поддержка различных таймфреймов (M5, M15, M30, H1, H4, D1)
- **Уведомления**: Интеграция с Telegram для уведомлений
- **Мониторинг**: Система мониторинга и логирования
- **Модульная архитектура**: Чистая и расширяемая архитектура

## 📁 Структура проекта

```
oanda_api/
├── src/                    # Исходный код
│   ├── core/              # Основные компоненты
│   │   ├── database.py    # Управление базой данных
│   │   ├── mt5_client.py  # Клиент MetaTrader5
│   │   └── telegram_notifier.py # Уведомления Telegram
│   ├── data/              # Обработка данных
│   │   ├── real_time_updater.py    # Обновление в реальном времени
│   │   ├── historical_loader.py    # Загрузка исторических данных
│   │   └── candle_processor.py     # Обработка свечей
│   ├── config/            # Конфигурация
│   │   ├── settings.py    # Настройки приложения
│   │   └── constants.py   # Константы и перечисления
│   └── utils/             # Утилиты
│       ├── logging.py     # Система логирования
│       └── helpers.py     # Вспомогательные функции
├── scripts/               # Скрипты запуска
│   ├── run_real_time.py   # Запуск в реальном времени
│   └── run_historical.py  # Загрузка исторических данных
├── tests/                 # Тесты
├── requirements.txt       # Зависимости
├── .env                   # Переменные окружения
└── README.md             # Документация
```

## 🛠️ Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd oanda_api
```

### 2. Создание виртуального окружения

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate     # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` на основе примера:

```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=trading_system
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_TIMEZONE=UTC

# Telegram
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_TOPICS=trades:223,system:1528,analysis:222,pending_orders:1662

# MetaTrader5
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_server
MT5_TERMINAL_PATH=C:\Program Files\MetaTrader5\terminal64.exe
```

### 5. Настройка базы данных

Запустите PostgreSQL и создайте базу данных:

```sql
CREATE DATABASE trading_system;
```

Затем выполните SQL скрипт для создания таблиц:

```bash
psql -d trading_system -f structure.sql
```

## 🚀 Использование

### Запуск в реальном времени

```bash
python scripts/run_real_time.py
```

### Загрузка исторических данных

```bash
# Загрузка за последние 7 дней
python scripts/run_historical.py

# Загрузка за указанный период
python scripts/run_historical.py --start-date 2024-01-01 --end-date 2024-01-31

# Загрузка конкретных пар и таймфреймов
python scripts/run_historical.py --symbols EUR_USD,GBP_USD --timeframes M5,M15,H1

# Параллельная загрузка
python scripts/run_historical.py --parallel --max-workers 5
```

## ⚙️ Конфигурация

### Настройка валютных пар

Отредактируйте файл `src/config/settings.py`:

```python
currency_pairs: List[CurrencyPair] = [
    CurrencyPair(
        symbol="EUR_USD",
        symbol_id=7,
        enabled=True,
        priority=1,
        pip_size=0.0001,
        min_trade_size=1,
        description="Евро / Доллар США"
    ),
    # Добавьте другие пары...
]
```

### Настройка таймфреймов

```python
active_timeframes: List[Timeframe] = [
    Timeframe.M5,
    Timeframe.M15,
    Timeframe.M30,
    Timeframe.H1,
    Timeframe.H4
]
```

### Настройка обновления данных

```python
data_update: DataUpdateConfig = DataUpdateConfig(
    update_interval=60,  # секунды
    candles_to_fetch=1000,
    parallel_downloads=True,
    max_workers=3,
    smart_schedule_mode=False
)
```

## 📊 Мониторинг

### Логи

Логи сохраняются в файл `trading_system.log` с ротацией.

### Telegram уведомления

Система отправляет уведомления в Telegram:
- Запуск/остановка системы
- Ошибки и предупреждения
- Статистика обновлений
- Heartbeat сообщения

### Метрики

Система собирает метрики производительности:
- Количество загруженных свечей
- Время выполнения операций
- Количество ошибок
- Статистика по парам и таймфреймам

## 🔧 Разработка

### Структура кода

Проект использует:
- **Pydantic** для валидации конфигурации
- **Structlog** для структурированного логирования
- **Connection pooling** для работы с базой данных
- **Thread-safe** операции с MT5
- **Retry логика** для надежности

### Добавление новых компонентов

1. Создайте новый модуль в соответствующей папке
2. Добавьте импорт в `__init__.py`
3. Напишите тесты в папке `tests/`
4. Обновите документацию

### Тестирование

```bash
# Запуск всех тестов
pytest

# Запуск с покрытием
pytest --cov=src

# Запуск конкретного теста
pytest tests/test_database.py::test_connection
```

## 🐛 Устранение неполадок

### Проблемы с MT5

1. Убедитесь что MetaTrader5 запущен
2. Проверьте путь к терминалу в `.env`
3. Проверьте учетные данные для входа

### Проблемы с базой данных

1. Убедитесь что PostgreSQL запущен
2. Проверьте подключение к базе данных
3. Проверьте права доступа пользователя

### Проблемы с Telegram

1. Проверьте токен бота
2. Убедитесь что бот добавлен в чат
3. Проверьте ID чата

## 📝 Лицензия

MIT License

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📞 Поддержка

Для вопросов и поддержки создайте Issue в репозитории. 
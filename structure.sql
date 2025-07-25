--
-- PostgreSQL database dump
--

-- Dumped from database version 17.4 (Ubuntu 17.4-1.pgdg22.04+2)
-- Dumped by pg_dump version 17.4 (Ubuntu 17.4-1.pgdg22.04+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: indicators; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA indicators;



--
-- Name: SCHEMA indicators; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA indicators IS 'Хранит рассчитанные технические индикаторы по разным таймфреймам';


--
-- Name: market_data; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA market_data;



--
-- Name: SCHEMA market_data; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA market_data IS 'Хранит сырые данные, полученные с биржи (свечи, стакан, сделки)';


--
-- Name: predictions; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA predictions;



--
-- Name: SCHEMA predictions; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA predictions IS 'Хранит данные о прогнозах, сделанных АИ системой';


--
-- Name: system_log; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA system_log;



--
-- Name: SCHEMA system_log; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA system_log IS 'Хранит системный журнал событий, ошибок и метрик производительности';


--
-- Name: verification; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA verification;


--
-- Name: SCHEMA verification; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA verification IS 'Хранит данные о проверке прогнозов и статистику';


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: general_metrics; Type: TABLE; Schema: indicators; Owner: postgres
--

CREATE TABLE indicators.general_metrics (
    metrics_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    current_price numeric(18,8) NOT NULL,
    support_levels numeric(18,8)[] NOT NULL,
    resistance_levels numeric(18,8)[] NOT NULL,
    atr numeric(10,4),
    atr_percent numeric(10,4),
    volatility_interpretation character varying(30),
    atr_change numeric(10,4),
    volatility_trend character varying(30),
    historical_volatility numeric(10,4),
    hv_interpretation character varying(30),
    fear_greed_index integer,
    fear_greed_interpretation character varying(30),
    price_change_24h numeric(10,4),
    buy_sell_ratio numeric(10,4),
    trade_velocity numeric(10,4),
    large_buys integer,
    large_sells integer,
    total_volume numeric(18,8),
    avg_trade_size numeric(18,8),
    volume_interpretation character varying(50),
    spread_pct numeric(10,6),
    spread_absolute numeric(18,8),
    spread_ticks integer,
    tick_size numeric(18,8),
    depth_1pct numeric(10,2),
    order_imbalance numeric(5,2),
    order_imbalance_interpretation character varying(50),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT general_metrics_fear_greed_index_check CHECK (((fear_greed_index >= 0) AND (fear_greed_index <= 100))),
    CONSTRAINT general_metrics_order_imbalance_check CHECK (((order_imbalance >= ('-1'::integer)::numeric) AND (order_imbalance <= (1)::numeric)))
);


--
-- Name: general_metrics_metrics_id_seq; Type: SEQUENCE; Schema: indicators; Owner: postgres
--

CREATE SEQUENCE indicators.general_metrics_metrics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: general_metrics_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: indicators; Owner: postgres
--

ALTER SEQUENCE indicators.general_metrics_metrics_id_seq OWNED BY indicators.general_metrics.metrics_id;


--
-- Name: h1_trend_indicators; Type: TABLE; Schema: indicators; Owner: postgres
--

CREATE TABLE indicators.h1_trend_indicators (
    indicator_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    ema_20 numeric(18,8),
    ema_20_interpretation character varying(30),
    macd numeric(10,4),
    macd_interpretation character varying(30),
    adx numeric(10,4),
    adx_interpretation character varying(30),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);



--
-- Name: h1_trend_indicators_indicator_id_seq; Type: SEQUENCE; Schema: indicators; Owner: postgres
--

CREATE SEQUENCE indicators.h1_trend_indicators_indicator_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: h1_trend_indicators_indicator_id_seq; Type: SEQUENCE OWNED BY; Schema: indicators; Owner: postgres
--

ALTER SEQUENCE indicators.h1_trend_indicators_indicator_id_seq OWNED BY indicators.h1_trend_indicators.indicator_id;


--
-- Name: m15_oscillators; Type: TABLE; Schema: indicators; Owner: postgres
--

CREATE TABLE indicators.m15_oscillators (
    oscillator_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    rsi_14 numeric(10,4),
    rsi_14_interpretation character varying(30),
    stoch_k numeric(10,4),
    stoch_d numeric(10,4),
    stoch_interpretation character varying(30),
    cci numeric(10,4),
    cci_interpretation character varying(30),
    willr numeric(10,4),
    willr_interpretation character varying(30),
    mfi numeric(10,4),
    mfi_interpretation character varying(30),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);



--
-- Name: m15_oscillators_oscillator_id_seq; Type: SEQUENCE; Schema: indicators; Owner: postgres
--

CREATE SEQUENCE indicators.m15_oscillators_oscillator_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: m15_oscillators_oscillator_id_seq; Type: SEQUENCE OWNED BY; Schema: indicators; Owner: postgres
--

ALTER SEQUENCE indicators.m15_oscillators_oscillator_id_seq OWNED BY indicators.m15_oscillators.oscillator_id;


--
-- Name: m15_trend_indicators; Type: TABLE; Schema: indicators; Owner: postgres
--

CREATE TABLE indicators.m15_trend_indicators (
    indicator_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    sma_20 numeric(18,8),
    sma_20_interpretation character varying(30),
    ema_20 numeric(18,8),
    ema_20_interpretation character varying(30),
    macd numeric(10,4),
    macd_interpretation character varying(30),
    adx numeric(10,4),
    adx_interpretation character varying(30),
    bb_upper numeric(18,8),
    bb_middle numeric(18,8),
    bb_lower numeric(18,8),
    bb_width numeric(10,4),
    bb_interpretation character varying(30),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: m15_trend_indicators_indicator_id_seq; Type: SEQUENCE; Schema: indicators; Owner: postgres
--

CREATE SEQUENCE indicators.m15_trend_indicators_indicator_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: m15_trend_indicators_indicator_id_seq; Type: SEQUENCE OWNED BY; Schema: indicators; Owner: postgres
--

ALTER SEQUENCE indicators.m15_trend_indicators_indicator_id_seq OWNED BY indicators.m15_trend_indicators.indicator_id;


--
-- Name: m1_special_indicators; Type: TABLE; Schema: indicators; Owner: postgres
--

CREATE TABLE indicators.m1_special_indicators (
    indicator_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    ema_8 numeric(18,8),
    ema_21 numeric(18,8),
    ema_cross_interpretation character varying(30),
    rsi_7 numeric(10,4),
    rsi_7_interpretation character varying(30),
    bb_width numeric(10,4),
    bb_interpretation character varying(30),
    roc_5 numeric(10,4),
    roc_interpretation character varying(30),
    volume_last_15m numeric(18,8),
    volume_last_30m numeric(18,8),
    avg_volume_per_minute numeric(18,8),
    volume_acceleration numeric(10,4),
    volume_interpretation character varying(30),
    doji_count integer,
    hammer_count integer,
    shooting_star_count integer,
    total_reversal_patterns integer,
    pattern_interpretation character varying(50),
    impulse_candles integer,
    impulse_interpretation character varying(30),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: m1_special_indicators_indicator_id_seq; Type: SEQUENCE; Schema: indicators; Owner: postgres
--

CREATE SEQUENCE indicators.m1_special_indicators_indicator_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: m1_special_indicators_indicator_id_seq; Type: SEQUENCE OWNED BY; Schema: indicators; Owner: postgres
--

ALTER SEQUENCE indicators.m1_special_indicators_indicator_id_seq OWNED BY indicators.m1_special_indicators.indicator_id;


--
-- Name: m1_standard_indicators; Type: TABLE; Schema: indicators; Owner: postgres
--

CREATE TABLE indicators.m1_standard_indicators (
    indicator_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    sma_20 numeric(18,8),
    ema_20 numeric(18,8),
    macd numeric(10,4),
    macd_interpretation character varying(30),
    rsi_14 numeric(10,4),
    stoch_k numeric(10,4),
    stoch_d numeric(10,4),
    stoch_interpretation character varying(30),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: m1_standard_indicators_indicator_id_seq; Type: SEQUENCE; Schema: indicators; Owner: postgres
--

CREATE SEQUENCE indicators.m1_standard_indicators_indicator_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: m1_standard_indicators_indicator_id_seq; Type: SEQUENCE OWNED BY; Schema: indicators; Owner: postgres
--

ALTER SEQUENCE indicators.m1_standard_indicators_indicator_id_seq OWNED BY indicators.m1_standard_indicators.indicator_id;


--
-- Name: m3_oscillators; Type: TABLE; Schema: indicators; Owner: postgres
--

CREATE TABLE indicators.m3_oscillators (
    oscillator_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    rsi_14 numeric(10,4),
    rsi_14_interpretation character varying(30),
    stoch_k numeric(10,4),
    stoch_d numeric(10,4),
    stoch_interpretation character varying(30),
    cci numeric(10,4),
    cci_interpretation character varying(30),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);



--
-- Name: m3_oscillators_oscillator_id_seq; Type: SEQUENCE; Schema: indicators; Owner: postgres
--

CREATE SEQUENCE indicators.m3_oscillators_oscillator_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: m3_oscillators_oscillator_id_seq; Type: SEQUENCE OWNED BY; Schema: indicators; Owner: postgres
--

ALTER SEQUENCE indicators.m3_oscillators_oscillator_id_seq OWNED BY indicators.m3_oscillators.oscillator_id;


--
-- Name: m3_trend_indicators; Type: TABLE; Schema: indicators; Owner: postgres
--

CREATE TABLE indicators.m3_trend_indicators (
    indicator_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    sma_20 numeric(18,8),
    sma_20_interpretation character varying(30),
    ema_20 numeric(18,8),
    ema_20_interpretation character varying(30),
    macd numeric(10,4),
    macd_interpretation character varying(30),
    adx numeric(10,4),
    adx_interpretation character varying(30),
    bb_upper numeric(18,8),
    bb_middle numeric(18,8),
    bb_lower numeric(18,8),
    bb_width numeric(10,4),
    bb_interpretation character varying(30),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: m3_trend_indicators_indicator_id_seq; Type: SEQUENCE; Schema: indicators; Owner: postgres
--

CREATE SEQUENCE indicators.m3_trend_indicators_indicator_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: m3_trend_indicators_indicator_id_seq; Type: SEQUENCE OWNED BY; Schema: indicators; Owner: postgres
--

ALTER SEQUENCE indicators.m3_trend_indicators_indicator_id_seq OWNED BY indicators.m3_trend_indicators.indicator_id;


--
-- Name: m5_oscillators; Type: TABLE; Schema: indicators; Owner: postgres
--

CREATE TABLE indicators.m5_oscillators (
    oscillator_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    rsi_14 numeric(10,4),
    rsi_14_interpretation character varying(30),
    stoch_k numeric(10,4),
    stoch_d numeric(10,4),
    stoch_interpretation character varying(30),
    cci numeric(10,4),
    cci_interpretation character varying(30),
    willr numeric(10,4),
    willr_interpretation character varying(30),
    mfi numeric(10,4),
    mfi_interpretation character varying(30),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: m5_oscillators_oscillator_id_seq; Type: SEQUENCE; Schema: indicators; Owner: postgres
--

CREATE SEQUENCE indicators.m5_oscillators_oscillator_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: m5_oscillators_oscillator_id_seq; Type: SEQUENCE OWNED BY; Schema: indicators; Owner: postgres
--

ALTER SEQUENCE indicators.m5_oscillators_oscillator_id_seq OWNED BY indicators.m5_oscillators.oscillator_id;


--
-- Name: m5_trend_indicators; Type: TABLE; Schema: indicators; Owner: postgres
--

CREATE TABLE indicators.m5_trend_indicators (
    indicator_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    sma_20 numeric(18,8),
    sma_20_interpretation character varying(30),
    ema_20 numeric(18,8),
    ema_20_interpretation character varying(30),
    macd numeric(10,4),
    macd_interpretation character varying(30),
    adx numeric(10,4),
    adx_interpretation character varying(30),
    bb_upper numeric(18,8),
    bb_middle numeric(18,8),
    bb_lower numeric(18,8),
    bb_width numeric(10,4),
    bb_interpretation character varying(30),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: m5_trend_indicators_indicator_id_seq; Type: SEQUENCE; Schema: indicators; Owner: postgres
--

CREATE SEQUENCE indicators.m5_trend_indicators_indicator_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: m5_trend_indicators_indicator_id_seq; Type: SEQUENCE OWNED BY; Schema: indicators; Owner: postgres
--

ALTER SEQUENCE indicators.m5_trend_indicators_indicator_id_seq OWNED BY indicators.m5_trend_indicators.indicator_id;


--
-- Name: candles; Type: TABLE; Schema: market_data; Owner: postgres
--

CREATE TABLE market_data.candles (
    candle_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    timeframe_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    open numeric(18,8) NOT NULL,
    high numeric(18,8) NOT NULL,
    low numeric(18,8) NOT NULL,
    close numeric(18,8) NOT NULL,
    volume numeric(18,8) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    close_time timestamp with time zone,
    quote_asset_volume numeric(18,8),
    number_of_trades integer,
    taker_buy_base_asset_volume numeric(18,8),
    taker_buy_quote_asset_volume numeric(18,8),
    price_change numeric(10,4),
    volatility numeric(10,8)
);


--
-- Name: COLUMN candles.close_time; Type: COMMENT; Schema: market_data; Owner: postgres
--

COMMENT ON COLUMN market_data.candles.close_time IS 'Время закрытия свечи';


--
-- Name: COLUMN candles.quote_asset_volume; Type: COMMENT; Schema: market_data; Owner: postgres
--

COMMENT ON COLUMN market_data.candles.quote_asset_volume IS 'Объем в котировочном активе';


--
-- Name: COLUMN candles.number_of_trades; Type: COMMENT; Schema: market_data; Owner: postgres
--

COMMENT ON COLUMN market_data.candles.number_of_trades IS 'Количество сделок в свече';


--
-- Name: COLUMN candles.taker_buy_base_asset_volume; Type: COMMENT; Schema: market_data; Owner: postgres
--

COMMENT ON COLUMN market_data.candles.taker_buy_base_asset_volume IS 'Объем покупок taker в базовом активе';


--
-- Name: COLUMN candles.taker_buy_quote_asset_volume; Type: COMMENT; Schema: market_data; Owner: postgres
--

COMMENT ON COLUMN market_data.candles.taker_buy_quote_asset_volume IS 'Объем покупок taker в котировочном активе';


--
-- Name: COLUMN candles.price_change; Type: COMMENT; Schema: market_data; Owner: postgres
--

COMMENT ON COLUMN market_data.candles.price_change IS 'Изменение цены за период свечи в процентах';


--
-- Name: COLUMN candles.volatility; Type: COMMENT; Schema: market_data; Owner: postgres
--

COMMENT ON COLUMN market_data.candles.volatility IS 'Волатильность за период свечи';


--
-- Name: candles_candle_id_seq; Type: SEQUENCE; Schema: market_data; Owner: postgres
--

CREATE SEQUENCE market_data.candles_candle_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: candles_candle_id_seq; Type: SEQUENCE OWNED BY; Schema: market_data; Owner: postgres
--

ALTER SEQUENCE market_data.candles_candle_id_seq OWNED BY market_data.candles.candle_id;


--
-- Name: order_book; Type: TABLE; Schema: market_data; Owner: postgres
--

CREATE TABLE market_data.order_book (
    order_book_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    snapshot jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: order_book_order_book_id_seq; Type: SEQUENCE; Schema: market_data; Owner: postgres
--

CREATE SEQUENCE market_data.order_book_order_book_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: order_book_order_book_id_seq; Type: SEQUENCE OWNED BY; Schema: market_data; Owner: postgres
--

ALTER SEQUENCE market_data.order_book_order_book_id_seq OWNED BY market_data.order_book.order_book_id;


--
-- Name: symbols; Type: TABLE; Schema: market_data; Owner: postgres
--

CREATE TABLE market_data.symbols (
    symbol_id integer NOT NULL,
    symbol character varying(20) NOT NULL,
    base_asset character varying(10) NOT NULL,
    quote_asset character varying(10) NOT NULL,
    tick_size numeric(18,8) NOT NULL,
    min_lot_size numeric(18,8) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: symbols_symbol_id_seq; Type: SEQUENCE; Schema: market_data; Owner: postgres
--

CREATE SEQUENCE market_data.symbols_symbol_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: symbols_symbol_id_seq; Type: SEQUENCE OWNED BY; Schema: market_data; Owner: postgres
--

ALTER SEQUENCE market_data.symbols_symbol_id_seq OWNED BY market_data.symbols.symbol_id;


--
-- Name: tickers; Type: TABLE; Schema: market_data; Owner: postgres
--

CREATE TABLE market_data.tickers (
    ticker_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    last_price numeric(18,8) NOT NULL,
    price_change_24h_percent numeric(10,2) NOT NULL,
    high_24h numeric(18,8) NOT NULL,
    low_24h numeric(18,8) NOT NULL,
    volume_24h numeric(18,8) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    quote_volume_24h numeric(18,8),
    trades_count_24h integer,
    is_tradable boolean DEFAULT true
);


--
-- Name: COLUMN tickers.quote_volume_24h; Type: COMMENT; Schema: market_data; Owner: postgres
--

COMMENT ON COLUMN market_data.tickers.quote_volume_24h IS 'Объем в котировочном активе за 24 часа';


--
-- Name: COLUMN tickers.trades_count_24h; Type: COMMENT; Schema: market_data; Owner: postgres
--

COMMENT ON COLUMN market_data.tickers.trades_count_24h IS 'Количество сделок за 24 часа';


--
-- Name: COLUMN tickers.is_tradable; Type: COMMENT; Schema: market_data; Owner: postgres
--

COMMENT ON COLUMN market_data.tickers.is_tradable IS 'Доступен ли символ для торговли';


--
-- Name: tickers_ticker_id_seq; Type: SEQUENCE; Schema: market_data; Owner: postgres
--

CREATE SEQUENCE market_data.tickers_ticker_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tickers_ticker_id_seq; Type: SEQUENCE OWNED BY; Schema: market_data; Owner: postgres
--

ALTER SEQUENCE market_data.tickers_ticker_id_seq OWNED BY market_data.tickers.ticker_id;


--
-- Name: timeframes; Type: TABLE; Schema: market_data; Owner: postgres
--

CREATE TABLE market_data.timeframes (
    timeframe_id integer NOT NULL,
    name character varying(10) NOT NULL,
    minutes integer NOT NULL,
    description character varying(100)
);


--
-- Name: timeframes_timeframe_id_seq; Type: SEQUENCE; Schema: market_data; Owner: postgres
--

CREATE SEQUENCE market_data.timeframes_timeframe_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: timeframes_timeframe_id_seq; Type: SEQUENCE OWNED BY; Schema: market_data; Owner: postgres
--

ALTER SEQUENCE market_data.timeframes_timeframe_id_seq OWNED BY market_data.timeframes.timeframe_id;


--
-- Name: trades; Type: TABLE; Schema: market_data; Owner: postgres
--

CREATE TABLE market_data.trades (
    trade_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    exchange_trade_id character varying(100) NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    price numeric(18,8) NOT NULL,
    quantity numeric(18,8) NOT NULL,
    is_buyer_maker boolean NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: trades_trade_id_seq; Type: SEQUENCE; Schema: market_data; Owner: postgres
--

CREATE SEQUENCE market_data.trades_trade_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: trades_trade_id_seq; Type: SEQUENCE OWNED BY; Schema: market_data; Owner: postgres
--

ALTER SEQUENCE market_data.trades_trade_id_seq OWNED BY market_data.trades.trade_id;


--
-- Name: ai_predictions; Type: TABLE; Schema: predictions; Owner: postgres
--

CREATE TABLE predictions.ai_predictions (
    prediction_id bigint NOT NULL,
    prompt_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    timeframe_id integer NOT NULL,
    direction character varying(10) NOT NULL,
    confidence integer,
    horizon integer NOT NULL,
    horizon_unit character varying(10) NOT NULL,
    action character varying(10),
    entry_price numeric(18,8),
    entry_type character varying(10),
    position_size numeric(5,2),
    stop_loss numeric(18,8),
    take_profit_1 numeric(18,8),
    take_profit_2 numeric(18,8),
    take_profit_3 numeric(18,8),
    risk_reward_ratio numeric(5,2),
    risk_level character varying(10),
    expected_volatility character varying(50),
    key_levels numeric(18,8)[],
    market_context text,
    timeframe_alignment character varying(50),
    ai_response_text text NOT NULL,
    analysis_summary text,
    current_market_conditions text,
    technical_analysis text,
    trade_recommendation text,
    risk_management text,
    additional_notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ai_predictions_action_check CHECK (((action)::text = ANY ((ARRAY['buy'::character varying, 'sell'::character varying, 'hold'::character varying])::text[]))),
    CONSTRAINT ai_predictions_confidence_check CHECK (((confidence >= 0) AND (confidence <= 100))),
    CONSTRAINT ai_predictions_direction_check CHECK (((direction)::text = ANY ((ARRAY['up'::character varying, 'down'::character varying, 'sideways'::character varying])::text[]))),
    CONSTRAINT ai_predictions_entry_type_check CHECK (((entry_type)::text = ANY ((ARRAY['market'::character varying, 'limit'::character varying])::text[]))),
    CONSTRAINT ai_predictions_horizon_unit_check CHECK (((horizon_unit)::text = ANY ((ARRAY['minutes'::character varying, 'hours'::character varying, 'days'::character varying])::text[]))),
    CONSTRAINT ai_predictions_risk_level_check CHECK (((risk_level)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying])::text[])))
);


--
-- Name: ai_predictions_prediction_id_seq; Type: SEQUENCE; Schema: predictions; Owner: postgres
--

CREATE SEQUENCE predictions.ai_predictions_prediction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ai_predictions_prediction_id_seq; Type: SEQUENCE OWNED BY; Schema: predictions; Owner: postgres
--

ALTER SEQUENCE predictions.ai_predictions_prediction_id_seq OWNED BY predictions.ai_predictions.prediction_id;


--
-- Name: prompt_templates; Type: TABLE; Schema: predictions; Owner: postgres
--

CREATE TABLE predictions.prompt_templates (
    template_id integer NOT NULL,
    name character varying(100) NOT NULL,
    template_text text NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: prompt_templates_template_id_seq; Type: SEQUENCE; Schema: predictions; Owner: postgres
--

CREATE SEQUENCE predictions.prompt_templates_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: prompt_templates_template_id_seq; Type: SEQUENCE OWNED BY; Schema: predictions; Owner: postgres
--

ALTER SEQUENCE predictions.prompt_templates_template_id_seq OWNED BY predictions.prompt_templates.template_id;


--
-- Name: sent_prompts; Type: TABLE; Schema: predictions; Owner: postgres
--

CREATE TABLE predictions.sent_prompts (
    prompt_id bigint NOT NULL,
    template_id integer NOT NULL,
    symbol_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    full_prompt_text text NOT NULL,
    technical_data jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: sent_prompts_prompt_id_seq; Type: SEQUENCE; Schema: predictions; Owner: postgres
--

CREATE SEQUENCE predictions.sent_prompts_prompt_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sent_prompts_prompt_id_seq; Type: SEQUENCE OWNED BY; Schema: predictions; Owner: postgres
--

ALTER SEQUENCE predictions.sent_prompts_prompt_id_seq OWNED BY predictions.sent_prompts.prompt_id;


--
-- Name: signal_data; Type: TABLE; Schema: public; Owner: skomax_skomax
--

CREATE TABLE public.signal_data (
    id integer NOT NULL,
    signal_id integer NOT NULL,
    timeframe_id integer NOT NULL,
    candle_open numeric(10,5) NOT NULL,
    candle_high numeric(10,5) NOT NULL,
    candle_low numeric(10,5) NOT NULL,
    candle_close numeric(10,5) NOT NULL,
    signal_type character varying(10) NOT NULL,
    signal_direction character varying(20) NOT NULL,
    chikou_span_filter numeric(5,2) NOT NULL,
    kijun_value numeric(10,5) NOT NULL,
    tenkan_value numeric(10,5) NOT NULL,
    tk_distance numeric(10,2) NOT NULL,
    cloud_color character varying(20) NOT NULL,
    price_vs_cloud character varying(20) NOT NULL,
    cloud_thickness numeric(10,2) NOT NULL,
    rsi_14 numeric(5,2) NOT NULL,
    m30_chikou_span_filter numeric(5,2),
    m30_kijun_value numeric(10,5),
    m30_tenkan_value numeric(10,5),
    m30_tk_distance numeric(10,2),
    m30_signal_direction character varying(20),
    m30_cloud_color character varying(20),
    m30_price_vs_cloud character varying(20),
    m30_cloud_thickness numeric(10,2),
    m30_rsi_14 numeric(5,2),
    h1_chikou_span_filter numeric(5,2),
    h1_kijun_value numeric(10,5),
    h1_tenkan_value numeric(10,5),
    h1_tk_distance numeric(10,2),
    h1_signal_direction character varying(20),
    h1_cloud_color character varying(20),
    h1_price_vs_cloud character varying(20),
    h1_cloud_thickness numeric(10,2),
    h1_rsi_14 numeric(5,2),
    h4_chikou_span_filter numeric(5,2),
    h4_kijun_value numeric(10,5),
    h4_tenkan_value numeric(10,5),
    h4_tk_distance numeric(10,2),
    h4_signal_direction character varying(20),
    h4_cloud_color character varying(20),
    h4_price_vs_cloud character varying(20),
    h4_cloud_thickness numeric(10,2),
    h4_rsi_14 numeric(5,2),
    d1_chikou_span_filter numeric(5,2),
    d1_kijun_value numeric(10,5),
    d1_tenkan_value numeric(10,5),
    d1_tk_distance numeric(10,2),
    d1_signal_direction character varying(20),
    d1_cloud_color character varying(20),
    d1_price_vs_cloud character varying(20),
    d1_cloud_thickness numeric(10,2),
    d1_rsi_14 numeric(5,2),
    candle_close_timestamp timestamp without time zone,
    pnl numeric(15,5),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    candle_timestamp timestamp without time zone,
    ichimoku_data jsonb,
    volume bigint
);


ALTER TABLE public.signal_data OWNER TO skomax_skomax;

--
-- Name: TABLE signal_data; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON TABLE public.signal_data IS 'Детальные данные сигналов включая OHLC и индикаторы';


--
-- Name: COLUMN signal_data.chikou_span_filter; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signal_data.chikou_span_filter IS 'Фильтр 4 - Chikou Span: +1.0 когда выше значения 26 позиций назад, -1.0 когда ниже';


--
-- Name: COLUMN signal_data.tk_distance; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signal_data.tk_distance IS 'Расстояние между Tenkan и Kijun в пипсах';


--
-- Name: COLUMN signal_data.cloud_color; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signal_data.cloud_color IS 'Цвет облака Ишимоку: GREEN (бычье), RED (медвежье), NEUTRAL';


--
-- Name: COLUMN signal_data.price_vs_cloud; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signal_data.price_vs_cloud IS 'Положение цены относительно облака: ABOVE_CLOUD, BELOW_CLOUD, INSIDE_CLOUD';


--
-- Name: COLUMN signal_data.cloud_thickness; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signal_data.cloud_thickness IS 'Толщина облака Ишимоку в пипсах';


--
-- Name: COLUMN signal_data.pnl; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signal_data.pnl IS 'Прибыль/убыток по сделке в валюте счета';


--
-- Name: COLUMN signal_data.ichimoku_data; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signal_data.ichimoku_data IS 'JSON с полными данными индикатора Ишимоку';


--
-- Name: signal_data_id_seq; Type: SEQUENCE; Schema: public; Owner: skomax_skomax
--

CREATE SEQUENCE public.signal_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.signal_data_id_seq OWNER TO skomax_skomax;

--
-- Name: signal_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: skomax_skomax
--

ALTER SEQUENCE public.signal_data_id_seq OWNED BY public.signal_data.id;


--
-- Name: signals; Type: TABLE; Schema: public; Owner: skomax_skomax
--

CREATE TABLE public.signals (
    id integer NOT NULL,
    broker_order_id character varying(100) NOT NULL,
    symbol_id integer NOT NULL,
    created_timestamp timestamp without time zone NOT NULL,
    order_status integer DEFAULT 1 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    position_id character varying(50),
    execution_time timestamp without time zone,
    execution_price numeric(10,5),
    units_executed integer,
    exit_time timestamp without time zone,
    exit_price numeric(10,5),
    realized_pl numeric(10,2),
    spread_cost numeric(10,2),
    financing numeric(10,2),
    close_reason character varying(100),
    pips_movement numeric(10,2),
    trailing_modifications integer,
    signal_strength_score integer,
    signal_strength_label character varying(20),
    higher_tf_signal integer,
    higher_tf_confirmation character varying(50),
    combination_key character varying(50),
    status character varying(20) DEFAULT 'created'::character varying,
    ichimoku_signal integer,
    tenkan_value numeric(10,5),
    kijun_value numeric(10,5),
    entry_reason text,
    signal_time timestamp without time zone,
    timeframe_id integer,
    direction character varying(10),
    entry_price numeric(10,5),
    stop_loss numeric(10,5),
    take_profit numeric(10,5),
    units integer
);


ALTER TABLE public.signals OWNER TO skomax_skomax;

--
-- Name: TABLE signals; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON TABLE public.signals IS 'Основная таблица сигналов с полной аналитической информацией';


--
-- Name: COLUMN signals.broker_order_id; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.broker_order_id IS 'ID ордера в брокере OANDA';


--
-- Name: COLUMN signals.order_status; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.order_status IS 'Статус ордера: 1 - создан, 0 - отменен';


--
-- Name: COLUMN signals.position_id; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.position_id IS 'ID позиции после исполнения';


--
-- Name: COLUMN signals.execution_time; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.execution_time IS 'Время исполнения';


--
-- Name: COLUMN signals.execution_price; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.execution_price IS 'Цена исполнения';


--
-- Name: COLUMN signals.units_executed; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.units_executed IS 'Исполненный размер';


--
-- Name: COLUMN signals.exit_time; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.exit_time IS 'Время закрытия';


--
-- Name: COLUMN signals.exit_price; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.exit_price IS 'Цена закрытия';


--
-- Name: COLUMN signals.realized_pl; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.realized_pl IS 'Реализованная прибыль/убыток';


--
-- Name: COLUMN signals.spread_cost; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.spread_cost IS 'Стоимость спреда';


--
-- Name: COLUMN signals.financing; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.financing IS 'Финансирование';


--
-- Name: COLUMN signals.close_reason; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.close_reason IS 'Причина закрытия';


--
-- Name: COLUMN signals.pips_movement; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.pips_movement IS 'Движение в пипсах';


--
-- Name: COLUMN signals.trailing_modifications; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.trailing_modifications IS 'Количество модификаций трейлинга';


--
-- Name: COLUMN signals.signal_strength_score; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.signal_strength_score IS 'Оценка силы сигнала от 0 до 100';


--
-- Name: COLUMN signals.signal_strength_label; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.signal_strength_label IS 'Метка силы сигнала';


--
-- Name: COLUMN signals.higher_tf_signal; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.higher_tf_signal IS 'Сигнал старшего ТФ';


--
-- Name: COLUMN signals.higher_tf_confirmation; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.higher_tf_confirmation IS 'Подтверждение старшего ТФ';


--
-- Name: COLUMN signals.combination_key; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.combination_key IS 'Ключ комбинации';


--
-- Name: COLUMN signals.status; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.status IS 'Статус сигнала';


--
-- Name: COLUMN signals.ichimoku_signal; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.ichimoku_signal IS 'Сигнал Ишимоку: 1 (LONG), -1 (SHORT), 0 (нейтральный)';


--
-- Name: COLUMN signals.tenkan_value; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.tenkan_value IS 'Значение Tenkan';


--
-- Name: COLUMN signals.kijun_value; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.kijun_value IS 'Значение Kijun';


--
-- Name: COLUMN signals.entry_reason; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.entry_reason IS 'Причина создания сигнала';


--
-- Name: COLUMN signals.signal_time; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.signal_time IS 'Время создания сигнала';


--
-- Name: COLUMN signals.timeframe_id; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.timeframe_id IS 'ID таймфрейма в БД';


--
-- Name: COLUMN signals.direction; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.direction IS 'Направление: LONG или SHORT';


--
-- Name: COLUMN signals.entry_price; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.entry_price IS 'Цена входа';


--
-- Name: COLUMN signals.stop_loss; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.stop_loss IS 'Стоп-лосс';


--
-- Name: COLUMN signals.take_profit; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.take_profit IS 'Тейк-профит';


--
-- Name: COLUMN signals.units; Type: COMMENT; Schema: public; Owner: skomax_skomax
--

COMMENT ON COLUMN public.signals.units IS 'Размер позиции';


--
-- Name: signals_id_seq; Type: SEQUENCE; Schema: public; Owner: skomax_skomax
--

CREATE SEQUENCE public.signals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.signals_id_seq OWNER TO skomax_skomax;

--
-- Name: signals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: skomax_skomax
--

ALTER SEQUENCE public.signals_id_seq OWNED BY public.signals.id;


--
-- Name: errors; Type: TABLE; Schema: system_log; Owner: postgres
--

CREATE TABLE system_log.errors (
    error_id bigint NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    error_type character varying(50) NOT NULL,
    severity character varying(20) NOT NULL,
    description text NOT NULL,
    stack_trace text,
    resolution text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT errors_severity_check CHECK (((severity)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying, 'critical'::character varying])::text[])))
);


--
-- Name: errors_error_id_seq; Type: SEQUENCE; Schema: system_log; Owner: postgres
--

CREATE SEQUENCE system_log.errors_error_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: errors_error_id_seq; Type: SEQUENCE OWNED BY; Schema: system_log; Owner: postgres
--

ALTER SEQUENCE system_log.errors_error_id_seq OWNED BY system_log.errors.error_id;


--
-- Name: events; Type: TABLE; Schema: system_log; Owner: postgres
--

CREATE TABLE system_log.events (
    event_id bigint NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    event_type character varying(50) NOT NULL,
    status character varying(20) NOT NULL,
    message text NOT NULL,
    details jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT events_status_check CHECK (((status)::text = ANY ((ARRAY['success'::character varying, 'warning'::character varying, 'error'::character varying])::text[])))
);


--
-- Name: events_event_id_seq; Type: SEQUENCE; Schema: system_log; Owner: postgres
--

CREATE SEQUENCE system_log.events_event_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: events_event_id_seq; Type: SEQUENCE OWNED BY; Schema: system_log; Owner: postgres
--

ALTER SEQUENCE system_log.events_event_id_seq OWNED BY system_log.events.event_id;


--
-- Name: performance_metrics; Type: TABLE; Schema: system_log; Owner: postgres
--

CREATE TABLE system_log.performance_metrics (
    metric_id bigint NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    cpu_usage numeric(5,2),
    memory_usage numeric(10,2),
    data_processing_time integer,
    ai_response_time integer,
    database_metrics jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: performance_metrics_metric_id_seq; Type: SEQUENCE; Schema: system_log; Owner: postgres
--

CREATE SEQUENCE system_log.performance_metrics_metric_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: performance_metrics_metric_id_seq; Type: SEQUENCE OWNED BY; Schema: system_log; Owner: postgres
--

ALTER SEQUENCE system_log.performance_metrics_metric_id_seq OWNED BY system_log.performance_metrics.metric_id;


--
-- Name: backtesting_statistics; Type: TABLE; Schema: verification; Owner: skomax_skomax
--

CREATE TABLE verification.backtesting_statistics (
    id integer NOT NULL,
    symbol character varying(20) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    total_predictions integer NOT NULL,
    successful_predictions integer NOT NULL,
    failed_predictions integer NOT NULL,
    success_rate numeric(5,2) NOT NULL,
    details jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE verification.backtesting_statistics OWNER TO skomax_skomax;

--
-- Name: backtesting_statistics_id_seq; Type: SEQUENCE; Schema: verification; Owner: skomax_skomax
--

CREATE SEQUENCE verification.backtesting_statistics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE verification.backtesting_statistics_id_seq OWNER TO skomax_skomax;

--
-- Name: backtesting_statistics_id_seq; Type: SEQUENCE OWNED BY; Schema: verification; Owner: skomax_skomax
--

ALTER SEQUENCE verification.backtesting_statistics_id_seq OWNED BY verification.backtesting_statistics.id;


--
-- Name: prediction_results; Type: TABLE; Schema: verification; Owner: postgres
--

CREATE TABLE verification.prediction_results (
    result_id bigint NOT NULL,
    prediction_id bigint NOT NULL,
    verification_status character varying(20) NOT NULL,
    outcome character varying(20),
    price_reached_target boolean,
    direction_correct boolean,
    max_profit_reached numeric(10,4),
    max_loss_reached numeric(10,4),
    time_to_target integer,
    time_to_stop integer,
    tp_levels_reached boolean[],
    trade_duration integer,
    verification_timestamp timestamp with time zone NOT NULL,
    verification_data jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT prediction_results_outcome_check CHECK (((outcome)::text = ANY ((ARRAY['successful'::character varying, 'partially_successful'::character varying, 'unsuccessful'::character varying])::text[]))),
    CONSTRAINT prediction_results_verification_status_check CHECK (((verification_status)::text = ANY ((ARRAY['pending'::character varying, 'verified'::character varying, 'failed'::character varying])::text[])))
);


--
-- Name: prediction_results_result_id_seq; Type: SEQUENCE; Schema: verification; Owner: postgres
--

CREATE SEQUENCE verification.prediction_results_result_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: prediction_results_result_id_seq; Type: SEQUENCE OWNED BY; Schema: verification; Owner: postgres
--

ALTER SEQUENCE verification.prediction_results_result_id_seq OWNED BY verification.prediction_results.result_id;


--
-- Name: prediction_statistics; Type: TABLE; Schema: verification; Owner: postgres
--

CREATE TABLE verification.prediction_statistics (
    stats_id bigint NOT NULL,
    symbol_id integer NOT NULL,
    timeframe_id integer NOT NULL,
    start_period timestamp with time zone NOT NULL,
    end_period timestamp with time zone NOT NULL,
    ai_analysis_accuracy numeric(5,2),
    directional_accuracy numeric(5,2),
    profit_factor numeric(10,4),
    win_rate numeric(5,2),
    average_profit numeric(10,4),
    average_loss numeric(10,4),
    risk_reward_achieved numeric(5,2),
    total_predictions integer NOT NULL,
    successful_predictions integer NOT NULL,
    unsuccessful_predictions integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);



--
-- Name: prediction_statistics_stats_id_seq; Type: SEQUENCE; Schema: verification; Owner: postgres
--

CREATE SEQUENCE verification.prediction_statistics_stats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: prediction_statistics_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: verification; Owner: postgres
--

ALTER SEQUENCE verification.prediction_statistics_stats_id_seq OWNED BY verification.prediction_statistics.stats_id;


--
-- Name: general_metrics metrics_id; Type: DEFAULT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.general_metrics ALTER COLUMN metrics_id SET DEFAULT nextval('indicators.general_metrics_metrics_id_seq'::regclass);


--
-- Name: h1_trend_indicators indicator_id; Type: DEFAULT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.h1_trend_indicators ALTER COLUMN indicator_id SET DEFAULT nextval('indicators.h1_trend_indicators_indicator_id_seq'::regclass);


--
-- Name: m15_oscillators oscillator_id; Type: DEFAULT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m15_oscillators ALTER COLUMN oscillator_id SET DEFAULT nextval('indicators.m15_oscillators_oscillator_id_seq'::regclass);


--
-- Name: m15_trend_indicators indicator_id; Type: DEFAULT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m15_trend_indicators ALTER COLUMN indicator_id SET DEFAULT nextval('indicators.m15_trend_indicators_indicator_id_seq'::regclass);


--
-- Name: m1_special_indicators indicator_id; Type: DEFAULT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m1_special_indicators ALTER COLUMN indicator_id SET DEFAULT nextval('indicators.m1_special_indicators_indicator_id_seq'::regclass);


--
-- Name: m1_standard_indicators indicator_id; Type: DEFAULT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m1_standard_indicators ALTER COLUMN indicator_id SET DEFAULT nextval('indicators.m1_standard_indicators_indicator_id_seq'::regclass);


--
-- Name: m3_oscillators oscillator_id; Type: DEFAULT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m3_oscillators ALTER COLUMN oscillator_id SET DEFAULT nextval('indicators.m3_oscillators_oscillator_id_seq'::regclass);


--
-- Name: m3_trend_indicators indicator_id; Type: DEFAULT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m3_trend_indicators ALTER COLUMN indicator_id SET DEFAULT nextval('indicators.m3_trend_indicators_indicator_id_seq'::regclass);


--
-- Name: m5_oscillators oscillator_id; Type: DEFAULT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m5_oscillators ALTER COLUMN oscillator_id SET DEFAULT nextval('indicators.m5_oscillators_oscillator_id_seq'::regclass);


--
-- Name: m5_trend_indicators indicator_id; Type: DEFAULT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m5_trend_indicators ALTER COLUMN indicator_id SET DEFAULT nextval('indicators.m5_trend_indicators_indicator_id_seq'::regclass);


--
-- Name: candles candle_id; Type: DEFAULT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.candles ALTER COLUMN candle_id SET DEFAULT nextval('market_data.candles_candle_id_seq'::regclass);


--
-- Name: order_book order_book_id; Type: DEFAULT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.order_book ALTER COLUMN order_book_id SET DEFAULT nextval('market_data.order_book_order_book_id_seq'::regclass);


--
-- Name: symbols symbol_id; Type: DEFAULT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.symbols ALTER COLUMN symbol_id SET DEFAULT nextval('market_data.symbols_symbol_id_seq'::regclass);


--
-- Name: tickers ticker_id; Type: DEFAULT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.tickers ALTER COLUMN ticker_id SET DEFAULT nextval('market_data.tickers_ticker_id_seq'::regclass);


--
-- Name: timeframes timeframe_id; Type: DEFAULT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.timeframes ALTER COLUMN timeframe_id SET DEFAULT nextval('market_data.timeframes_timeframe_id_seq'::regclass);


--
-- Name: trades trade_id; Type: DEFAULT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.trades ALTER COLUMN trade_id SET DEFAULT nextval('market_data.trades_trade_id_seq'::regclass);


--
-- Name: ai_predictions prediction_id; Type: DEFAULT; Schema: predictions; Owner: postgres
--

ALTER TABLE ONLY predictions.ai_predictions ALTER COLUMN prediction_id SET DEFAULT nextval('predictions.ai_predictions_prediction_id_seq'::regclass);


--
-- Name: prompt_templates template_id; Type: DEFAULT; Schema: predictions; Owner: postgres
--

ALTER TABLE ONLY predictions.prompt_templates ALTER COLUMN template_id SET DEFAULT nextval('predictions.prompt_templates_template_id_seq'::regclass);


--
-- Name: sent_prompts prompt_id; Type: DEFAULT; Schema: predictions; Owner: postgres
--

ALTER TABLE ONLY predictions.sent_prompts ALTER COLUMN prompt_id SET DEFAULT nextval('predictions.sent_prompts_prompt_id_seq'::regclass);


--
-- Name: signal_data id; Type: DEFAULT; Schema: public; Owner: skomax_skomax
--

ALTER TABLE ONLY public.signal_data ALTER COLUMN id SET DEFAULT nextval('public.signal_data_id_seq'::regclass);


--
-- Name: signals id; Type: DEFAULT; Schema: public; Owner: skomax_skomax
--

ALTER TABLE ONLY public.signals ALTER COLUMN id SET DEFAULT nextval('public.signals_id_seq'::regclass);


--
-- Name: errors error_id; Type: DEFAULT; Schema: system_log; Owner: postgres
--

ALTER TABLE ONLY system_log.errors ALTER COLUMN error_id SET DEFAULT nextval('system_log.errors_error_id_seq'::regclass);


--
-- Name: events event_id; Type: DEFAULT; Schema: system_log; Owner: postgres
--

ALTER TABLE ONLY system_log.events ALTER COLUMN event_id SET DEFAULT nextval('system_log.events_event_id_seq'::regclass);


--
-- Name: performance_metrics metric_id; Type: DEFAULT; Schema: system_log; Owner: postgres
--

ALTER TABLE ONLY system_log.performance_metrics ALTER COLUMN metric_id SET DEFAULT nextval('system_log.performance_metrics_metric_id_seq'::regclass);


--
-- Name: backtesting_statistics id; Type: DEFAULT; Schema: verification; Owner: skomax_skomax
--

ALTER TABLE ONLY verification.backtesting_statistics ALTER COLUMN id SET DEFAULT nextval('verification.backtesting_statistics_id_seq'::regclass);


--
-- Name: prediction_results result_id; Type: DEFAULT; Schema: verification; Owner: postgres
--

ALTER TABLE ONLY verification.prediction_results ALTER COLUMN result_id SET DEFAULT nextval('verification.prediction_results_result_id_seq'::regclass);


--
-- Name: prediction_statistics stats_id; Type: DEFAULT; Schema: verification; Owner: postgres
--

ALTER TABLE ONLY verification.prediction_statistics ALTER COLUMN stats_id SET DEFAULT nextval('verification.prediction_statistics_stats_id_seq'::regclass);


--
-- Name: general_metrics general_metrics_pkey; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.general_metrics
    ADD CONSTRAINT general_metrics_pkey PRIMARY KEY (metrics_id);


--
-- Name: general_metrics general_metrics_symbol_id_timestamp_key; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.general_metrics
    ADD CONSTRAINT general_metrics_symbol_id_timestamp_key UNIQUE (symbol_id, "timestamp");


--
-- Name: h1_trend_indicators h1_trend_indicators_pkey; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.h1_trend_indicators
    ADD CONSTRAINT h1_trend_indicators_pkey PRIMARY KEY (indicator_id);


--
-- Name: h1_trend_indicators h1_trend_indicators_symbol_id_timestamp_key; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.h1_trend_indicators
    ADD CONSTRAINT h1_trend_indicators_symbol_id_timestamp_key UNIQUE (symbol_id, "timestamp");


--
-- Name: m15_oscillators m15_oscillators_pkey; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m15_oscillators
    ADD CONSTRAINT m15_oscillators_pkey PRIMARY KEY (oscillator_id);


--
-- Name: m15_oscillators m15_oscillators_symbol_id_timestamp_key; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m15_oscillators
    ADD CONSTRAINT m15_oscillators_symbol_id_timestamp_key UNIQUE (symbol_id, "timestamp");


--
-- Name: m15_trend_indicators m15_trend_indicators_pkey; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m15_trend_indicators
    ADD CONSTRAINT m15_trend_indicators_pkey PRIMARY KEY (indicator_id);


--
-- Name: m15_trend_indicators m15_trend_indicators_symbol_id_timestamp_key; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m15_trend_indicators
    ADD CONSTRAINT m15_trend_indicators_symbol_id_timestamp_key UNIQUE (symbol_id, "timestamp");


--
-- Name: m1_special_indicators m1_special_indicators_pkey; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m1_special_indicators
    ADD CONSTRAINT m1_special_indicators_pkey PRIMARY KEY (indicator_id);


--
-- Name: m1_special_indicators m1_special_indicators_symbol_id_timestamp_key; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m1_special_indicators
    ADD CONSTRAINT m1_special_indicators_symbol_id_timestamp_key UNIQUE (symbol_id, "timestamp");


--
-- Name: m1_standard_indicators m1_standard_indicators_pkey; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m1_standard_indicators
    ADD CONSTRAINT m1_standard_indicators_pkey PRIMARY KEY (indicator_id);


--
-- Name: m1_standard_indicators m1_standard_indicators_symbol_id_timestamp_key; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m1_standard_indicators
    ADD CONSTRAINT m1_standard_indicators_symbol_id_timestamp_key UNIQUE (symbol_id, "timestamp");


--
-- Name: m3_oscillators m3_oscillators_pkey; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m3_oscillators
    ADD CONSTRAINT m3_oscillators_pkey PRIMARY KEY (oscillator_id);


--
-- Name: m3_oscillators m3_oscillators_symbol_id_timestamp_key; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m3_oscillators
    ADD CONSTRAINT m3_oscillators_symbol_id_timestamp_key UNIQUE (symbol_id, "timestamp");


--
-- Name: m3_trend_indicators m3_trend_indicators_pkey; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m3_trend_indicators
    ADD CONSTRAINT m3_trend_indicators_pkey PRIMARY KEY (indicator_id);


--
-- Name: m3_trend_indicators m3_trend_indicators_symbol_id_timestamp_key; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m3_trend_indicators
    ADD CONSTRAINT m3_trend_indicators_symbol_id_timestamp_key UNIQUE (symbol_id, "timestamp");


--
-- Name: m5_oscillators m5_oscillators_pkey; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m5_oscillators
    ADD CONSTRAINT m5_oscillators_pkey PRIMARY KEY (oscillator_id);


--
-- Name: m5_oscillators m5_oscillators_symbol_id_timestamp_key; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m5_oscillators
    ADD CONSTRAINT m5_oscillators_symbol_id_timestamp_key UNIQUE (symbol_id, "timestamp");


--
-- Name: m5_trend_indicators m5_trend_indicators_pkey; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m5_trend_indicators
    ADD CONSTRAINT m5_trend_indicators_pkey PRIMARY KEY (indicator_id);


--
-- Name: m5_trend_indicators m5_trend_indicators_symbol_id_timestamp_key; Type: CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m5_trend_indicators
    ADD CONSTRAINT m5_trend_indicators_symbol_id_timestamp_key UNIQUE (symbol_id, "timestamp");


--
-- Name: candles candles_pkey; Type: CONSTRAINT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.candles
    ADD CONSTRAINT candles_pkey PRIMARY KEY (candle_id);


--
-- Name: candles candles_symbol_id_timeframe_id_timestamp_key; Type: CONSTRAINT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.candles
    ADD CONSTRAINT candles_symbol_id_timeframe_id_timestamp_key UNIQUE (symbol_id, timeframe_id, "timestamp");


--
-- Name: order_book order_book_pkey; Type: CONSTRAINT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.order_book
    ADD CONSTRAINT order_book_pkey PRIMARY KEY (order_book_id);


--
-- Name: symbols symbols_pkey; Type: CONSTRAINT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.symbols
    ADD CONSTRAINT symbols_pkey PRIMARY KEY (symbol_id);


--
-- Name: symbols symbols_symbol_key; Type: CONSTRAINT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.symbols
    ADD CONSTRAINT symbols_symbol_key UNIQUE (symbol);


--
-- Name: tickers tickers_pkey; Type: CONSTRAINT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.tickers
    ADD CONSTRAINT tickers_pkey PRIMARY KEY (ticker_id);


--
-- Name: timeframes timeframes_name_key; Type: CONSTRAINT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.timeframes
    ADD CONSTRAINT timeframes_name_key UNIQUE (name);


--
-- Name: timeframes timeframes_pkey; Type: CONSTRAINT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.timeframes
    ADD CONSTRAINT timeframes_pkey PRIMARY KEY (timeframe_id);


--
-- Name: trades trades_pkey; Type: CONSTRAINT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.trades
    ADD CONSTRAINT trades_pkey PRIMARY KEY (trade_id);


--
-- Name: ai_predictions ai_predictions_pkey; Type: CONSTRAINT; Schema: predictions; Owner: postgres
--

ALTER TABLE ONLY predictions.ai_predictions
    ADD CONSTRAINT ai_predictions_pkey PRIMARY KEY (prediction_id);


--
-- Name: ai_predictions ai_predictions_prompt_id_symbol_id_key; Type: CONSTRAINT; Schema: predictions; Owner: postgres
--

ALTER TABLE ONLY predictions.ai_predictions
    ADD CONSTRAINT ai_predictions_prompt_id_symbol_id_key UNIQUE (prompt_id, symbol_id);


--
-- Name: prompt_templates prompt_templates_name_key; Type: CONSTRAINT; Schema: predictions; Owner: postgres
--

ALTER TABLE ONLY predictions.prompt_templates
    ADD CONSTRAINT prompt_templates_name_key UNIQUE (name);


--
-- Name: prompt_templates prompt_templates_pkey; Type: CONSTRAINT; Schema: predictions; Owner: postgres
--

ALTER TABLE ONLY predictions.prompt_templates
    ADD CONSTRAINT prompt_templates_pkey PRIMARY KEY (template_id);


--
-- Name: sent_prompts sent_prompts_pkey; Type: CONSTRAINT; Schema: predictions; Owner: postgres
--

ALTER TABLE ONLY predictions.sent_prompts
    ADD CONSTRAINT sent_prompts_pkey PRIMARY KEY (prompt_id);


--
-- Name: signal_data signal_data_pkey; Type: CONSTRAINT; Schema: public; Owner: skomax_skomax
--

ALTER TABLE ONLY public.signal_data
    ADD CONSTRAINT signal_data_pkey PRIMARY KEY (id);


--
-- Name: signals signals_broker_order_id_key; Type: CONSTRAINT; Schema: public; Owner: skomax_skomax
--

ALTER TABLE ONLY public.signals
    ADD CONSTRAINT signals_broker_order_id_key UNIQUE (broker_order_id);


--
-- Name: signals signals_pkey; Type: CONSTRAINT; Schema: public; Owner: skomax_skomax
--

ALTER TABLE ONLY public.signals
    ADD CONSTRAINT signals_pkey PRIMARY KEY (id);


--
-- Name: errors errors_pkey; Type: CONSTRAINT; Schema: system_log; Owner: postgres
--

ALTER TABLE ONLY system_log.errors
    ADD CONSTRAINT errors_pkey PRIMARY KEY (error_id);


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: system_log; Owner: postgres
--

ALTER TABLE ONLY system_log.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (event_id);


--
-- Name: performance_metrics performance_metrics_pkey; Type: CONSTRAINT; Schema: system_log; Owner: postgres
--

ALTER TABLE ONLY system_log.performance_metrics
    ADD CONSTRAINT performance_metrics_pkey PRIMARY KEY (metric_id);


--
-- Name: backtesting_statistics backtesting_statistics_pkey; Type: CONSTRAINT; Schema: verification; Owner: skomax_skomax
--

ALTER TABLE ONLY verification.backtesting_statistics
    ADD CONSTRAINT backtesting_statistics_pkey PRIMARY KEY (id);


--
-- Name: prediction_results prediction_results_pkey; Type: CONSTRAINT; Schema: verification; Owner: postgres
--

ALTER TABLE ONLY verification.prediction_results
    ADD CONSTRAINT prediction_results_pkey PRIMARY KEY (result_id);


--
-- Name: prediction_results prediction_results_prediction_id_key; Type: CONSTRAINT; Schema: verification; Owner: postgres
--

ALTER TABLE ONLY verification.prediction_results
    ADD CONSTRAINT prediction_results_prediction_id_key UNIQUE (prediction_id);


--
-- Name: prediction_statistics prediction_statistics_pkey; Type: CONSTRAINT; Schema: verification; Owner: postgres
--

ALTER TABLE ONLY verification.prediction_statistics
    ADD CONSTRAINT prediction_statistics_pkey PRIMARY KEY (stats_id);


--
-- Name: prediction_statistics prediction_statistics_symbol_id_timeframe_id_start_period_e_key; Type: CONSTRAINT; Schema: verification; Owner: postgres
--

ALTER TABLE ONLY verification.prediction_statistics
    ADD CONSTRAINT prediction_statistics_symbol_id_timeframe_id_start_period_e_key UNIQUE (symbol_id, timeframe_id, start_period, end_period);


--
-- Name: idx_general_metrics_symbol_timestamp; Type: INDEX; Schema: indicators; Owner: postgres
--

CREATE INDEX idx_general_metrics_symbol_timestamp ON indicators.general_metrics USING btree (symbol_id, "timestamp");


--
-- Name: idx_h1_trend_symbol_timestamp; Type: INDEX; Schema: indicators; Owner: postgres
--

CREATE INDEX idx_h1_trend_symbol_timestamp ON indicators.h1_trend_indicators USING btree (symbol_id, "timestamp");


--
-- Name: idx_m15_oscillators_symbol_timestamp; Type: INDEX; Schema: indicators; Owner: postgres
--

CREATE INDEX idx_m15_oscillators_symbol_timestamp ON indicators.m15_oscillators USING btree (symbol_id, "timestamp");


--
-- Name: idx_m15_trend_symbol_timestamp; Type: INDEX; Schema: indicators; Owner: postgres
--

CREATE INDEX idx_m15_trend_symbol_timestamp ON indicators.m15_trend_indicators USING btree (symbol_id, "timestamp");


--
-- Name: idx_m1_special_symbol_timestamp; Type: INDEX; Schema: indicators; Owner: postgres
--

CREATE INDEX idx_m1_special_symbol_timestamp ON indicators.m1_special_indicators USING btree (symbol_id, "timestamp");


--
-- Name: idx_m1_standard_symbol_timestamp; Type: INDEX; Schema: indicators; Owner: postgres
--

CREATE INDEX idx_m1_standard_symbol_timestamp ON indicators.m1_standard_indicators USING btree (symbol_id, "timestamp");


--
-- Name: idx_m3_oscillators_symbol_timestamp; Type: INDEX; Schema: indicators; Owner: postgres
--

CREATE INDEX idx_m3_oscillators_symbol_timestamp ON indicators.m3_oscillators USING btree (symbol_id, "timestamp");


--
-- Name: idx_m3_trend_symbol_timestamp; Type: INDEX; Schema: indicators; Owner: postgres
--

CREATE INDEX idx_m3_trend_symbol_timestamp ON indicators.m3_trend_indicators USING btree (symbol_id, "timestamp");


--
-- Name: idx_m5_oscillators_symbol_timestamp; Type: INDEX; Schema: indicators; Owner: postgres
--

CREATE INDEX idx_m5_oscillators_symbol_timestamp ON indicators.m5_oscillators USING btree (symbol_id, "timestamp");


--
-- Name: idx_m5_trend_symbol_timestamp; Type: INDEX; Schema: indicators; Owner: postgres
--

CREATE INDEX idx_m5_trend_symbol_timestamp ON indicators.m5_trend_indicators USING btree (symbol_id, "timestamp");


--
-- Name: idx_candles_symbol_timeframe; Type: INDEX; Schema: market_data; Owner: postgres
--

CREATE INDEX idx_candles_symbol_timeframe ON market_data.candles USING btree (symbol_id, timeframe_id);


--
-- Name: idx_candles_timestamp; Type: INDEX; Schema: market_data; Owner: postgres
--

CREATE INDEX idx_candles_timestamp ON market_data.candles USING btree ("timestamp");


--
-- Name: idx_order_book_symbol_timestamp; Type: INDEX; Schema: market_data; Owner: postgres
--

CREATE INDEX idx_order_book_symbol_timestamp ON market_data.order_book USING btree (symbol_id, "timestamp");


--
-- Name: idx_tickers_symbol_timestamp; Type: INDEX; Schema: market_data; Owner: postgres
--

CREATE INDEX idx_tickers_symbol_timestamp ON market_data.tickers USING btree (symbol_id, "timestamp");


--
-- Name: idx_trades_symbol_timestamp; Type: INDEX; Schema: market_data; Owner: postgres
--

CREATE INDEX idx_trades_symbol_timestamp ON market_data.trades USING btree (symbol_id, "timestamp");


--
-- Name: idx_predictions_symbol_timestamp; Type: INDEX; Schema: predictions; Owner: postgres
--

CREATE INDEX idx_predictions_symbol_timestamp ON predictions.ai_predictions USING btree (symbol_id, "timestamp");


--
-- Name: idx_predictions_timeframe; Type: INDEX; Schema: predictions; Owner: postgres
--

CREATE INDEX idx_predictions_timeframe ON predictions.ai_predictions USING btree (timeframe_id);


--
-- Name: idx_signal_data_candle_close_timestamp; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signal_data_candle_close_timestamp ON public.signal_data USING btree (candle_close_timestamp);


--
-- Name: idx_signal_data_candle_timestamp; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signal_data_candle_timestamp ON public.signal_data USING btree (candle_timestamp);


--
-- Name: idx_signal_data_pnl; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signal_data_pnl ON public.signal_data USING btree (pnl);


--
-- Name: idx_signal_data_pnl_timestamp; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signal_data_pnl_timestamp ON public.signal_data USING btree (pnl, candle_close_timestamp);


--
-- Name: idx_signal_data_signal_direction; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signal_data_signal_direction ON public.signal_data USING btree (signal_direction);


--
-- Name: idx_signal_data_signal_id; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signal_data_signal_id ON public.signal_data USING btree (signal_id);


--
-- Name: idx_signal_data_signal_type; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signal_data_signal_type ON public.signal_data USING btree (signal_type);


--
-- Name: idx_signal_data_symbol_timeframe; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signal_data_symbol_timeframe ON public.signal_data USING btree (signal_id, timeframe_id);


--
-- Name: idx_signal_data_timeframe_id; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signal_data_timeframe_id ON public.signal_data USING btree (timeframe_id);


--
-- Name: idx_signal_data_type_direction; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signal_data_type_direction ON public.signal_data USING btree (signal_type, signal_direction);


--
-- Name: idx_signals_broker_order_id; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signals_broker_order_id ON public.signals USING btree (broker_order_id);


--
-- Name: idx_signals_created_timestamp; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signals_created_timestamp ON public.signals USING btree (created_timestamp);


--
-- Name: idx_signals_order_status; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signals_order_status ON public.signals USING btree (order_status);


--
-- Name: idx_signals_position_id; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signals_position_id ON public.signals USING btree (position_id);


--
-- Name: idx_signals_signal_time; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signals_signal_time ON public.signals USING btree (signal_time);


--
-- Name: idx_signals_status; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signals_status ON public.signals USING btree (status);


--
-- Name: idx_signals_symbol_id; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signals_symbol_id ON public.signals USING btree (symbol_id);


--
-- Name: idx_signals_symbol_timeframe; Type: INDEX; Schema: public; Owner: skomax_skomax
--

CREATE INDEX idx_signals_symbol_timeframe ON public.signals USING btree (symbol_id, timeframe_id);


--
-- Name: symbols update_symbols_updated_at; Type: TRIGGER; Schema: market_data; Owner: postgres
--

CREATE TRIGGER update_symbols_updated_at BEFORE UPDATE ON market_data.symbols FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: prompt_templates update_prompt_templates_updated_at; Type: TRIGGER; Schema: predictions; Owner: postgres
--

CREATE TRIGGER update_prompt_templates_updated_at BEFORE UPDATE ON predictions.prompt_templates FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: prediction_results update_prediction_results_updated_at; Type: TRIGGER; Schema: verification; Owner: postgres
--

CREATE TRIGGER update_prediction_results_updated_at BEFORE UPDATE ON verification.prediction_results FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: prediction_statistics update_prediction_statistics_updated_at; Type: TRIGGER; Schema: verification; Owner: postgres
--

CREATE TRIGGER update_prediction_statistics_updated_at BEFORE UPDATE ON verification.prediction_statistics FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: general_metrics general_metrics_symbol_id_fkey; Type: FK CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.general_metrics
    ADD CONSTRAINT general_metrics_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: h1_trend_indicators h1_trend_indicators_symbol_id_fkey; Type: FK CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.h1_trend_indicators
    ADD CONSTRAINT h1_trend_indicators_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: m15_oscillators m15_oscillators_symbol_id_fkey; Type: FK CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m15_oscillators
    ADD CONSTRAINT m15_oscillators_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: m15_trend_indicators m15_trend_indicators_symbol_id_fkey; Type: FK CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m15_trend_indicators
    ADD CONSTRAINT m15_trend_indicators_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: m1_special_indicators m1_special_indicators_symbol_id_fkey; Type: FK CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m1_special_indicators
    ADD CONSTRAINT m1_special_indicators_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: m1_standard_indicators m1_standard_indicators_symbol_id_fkey; Type: FK CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m1_standard_indicators
    ADD CONSTRAINT m1_standard_indicators_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: m3_oscillators m3_oscillators_symbol_id_fkey; Type: FK CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m3_oscillators
    ADD CONSTRAINT m3_oscillators_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: m3_trend_indicators m3_trend_indicators_symbol_id_fkey; Type: FK CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m3_trend_indicators
    ADD CONSTRAINT m3_trend_indicators_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: m5_oscillators m5_oscillators_symbol_id_fkey; Type: FK CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m5_oscillators
    ADD CONSTRAINT m5_oscillators_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: m5_trend_indicators m5_trend_indicators_symbol_id_fkey; Type: FK CONSTRAINT; Schema: indicators; Owner: postgres
--

ALTER TABLE ONLY indicators.m5_trend_indicators
    ADD CONSTRAINT m5_trend_indicators_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: candles candles_symbol_id_fkey; Type: FK CONSTRAINT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.candles
    ADD CONSTRAINT candles_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: candles candles_timeframe_id_fkey; Type: FK CONSTRAINT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.candles
    ADD CONSTRAINT candles_timeframe_id_fkey FOREIGN KEY (timeframe_id) REFERENCES market_data.timeframes(timeframe_id);


--
-- Name: order_book order_book_symbol_id_fkey; Type: FK CONSTRAINT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.order_book
    ADD CONSTRAINT order_book_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: tickers tickers_symbol_id_fkey; Type: FK CONSTRAINT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.tickers
    ADD CONSTRAINT tickers_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: trades trades_symbol_id_fkey; Type: FK CONSTRAINT; Schema: market_data; Owner: postgres
--

ALTER TABLE ONLY market_data.trades
    ADD CONSTRAINT trades_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: ai_predictions ai_predictions_prompt_id_fkey; Type: FK CONSTRAINT; Schema: predictions; Owner: postgres
--

ALTER TABLE ONLY predictions.ai_predictions
    ADD CONSTRAINT ai_predictions_prompt_id_fkey FOREIGN KEY (prompt_id) REFERENCES predictions.sent_prompts(prompt_id);


--
-- Name: ai_predictions ai_predictions_symbol_id_fkey; Type: FK CONSTRAINT; Schema: predictions; Owner: postgres
--

ALTER TABLE ONLY predictions.ai_predictions
    ADD CONSTRAINT ai_predictions_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: ai_predictions ai_predictions_timeframe_id_fkey; Type: FK CONSTRAINT; Schema: predictions; Owner: postgres
--

ALTER TABLE ONLY predictions.ai_predictions
    ADD CONSTRAINT ai_predictions_timeframe_id_fkey FOREIGN KEY (timeframe_id) REFERENCES market_data.timeframes(timeframe_id);


--
-- Name: sent_prompts sent_prompts_symbol_id_fkey; Type: FK CONSTRAINT; Schema: predictions; Owner: postgres
--

ALTER TABLE ONLY predictions.sent_prompts
    ADD CONSTRAINT sent_prompts_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: sent_prompts sent_prompts_template_id_fkey; Type: FK CONSTRAINT; Schema: predictions; Owner: postgres
--

ALTER TABLE ONLY predictions.sent_prompts
    ADD CONSTRAINT sent_prompts_template_id_fkey FOREIGN KEY (template_id) REFERENCES predictions.prompt_templates(template_id);


--
-- Name: signal_data signal_data_signal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skomax_skomax
--

ALTER TABLE ONLY public.signal_data
    ADD CONSTRAINT signal_data_signal_id_fkey FOREIGN KEY (signal_id) REFERENCES public.signals(id) ON DELETE CASCADE;


--
-- Name: prediction_results prediction_results_prediction_id_fkey; Type: FK CONSTRAINT; Schema: verification; Owner: postgres
--

ALTER TABLE ONLY verification.prediction_results
    ADD CONSTRAINT prediction_results_prediction_id_fkey FOREIGN KEY (prediction_id) REFERENCES predictions.ai_predictions(prediction_id);


--
-- Name: prediction_statistics prediction_statistics_symbol_id_fkey; Type: FK CONSTRAINT; Schema: verification; Owner: postgres
--

ALTER TABLE ONLY verification.prediction_statistics
    ADD CONSTRAINT prediction_statistics_symbol_id_fkey FOREIGN KEY (symbol_id) REFERENCES market_data.symbols(symbol_id);


--
-- Name: prediction_statistics prediction_statistics_timeframe_id_fkey; Type: FK CONSTRAINT; Schema: verification; Owner: postgres
--

ALTER TABLE ONLY verification.prediction_statistics
    ADD CONSTRAINT prediction_statistics_timeframe_id_fkey FOREIGN KEY (timeframe_id) REFERENCES market_data.timeframes(timeframe_id);


--
-- Name: SCHEMA indicators; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA indicators TO skomax_skomax;


--
-- Name: SCHEMA market_data; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA market_data TO skomax_skomax;


--
-- Name: SCHEMA predictions; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA predictions TO skomax_skomax;


--
-- Name: SCHEMA system_log; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA system_log TO skomax_skomax;


--
-- Name: SCHEMA verification; Type: ACL; Schema: -; Owner: postgres
--

GRANT ALL ON SCHEMA verification TO skomax_skomax;


--
-- Name: TABLE general_metrics; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,TRUNCATE,UPDATE ON TABLE indicators.general_metrics TO skomax_skomax;


--
-- Name: SEQUENCE general_metrics_metrics_id_seq; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE indicators.general_metrics_metrics_id_seq TO skomax_skomax;


--
-- Name: TABLE h1_trend_indicators; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,TRUNCATE,UPDATE ON TABLE indicators.h1_trend_indicators TO skomax_skomax;


--
-- Name: SEQUENCE h1_trend_indicators_indicator_id_seq; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE indicators.h1_trend_indicators_indicator_id_seq TO skomax_skomax;


--
-- Name: TABLE m15_oscillators; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,TRUNCATE,UPDATE ON TABLE indicators.m15_oscillators TO skomax_skomax;


--
-- Name: SEQUENCE m15_oscillators_oscillator_id_seq; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE indicators.m15_oscillators_oscillator_id_seq TO skomax_skomax;


--
-- Name: TABLE m15_trend_indicators; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,TRUNCATE,UPDATE ON TABLE indicators.m15_trend_indicators TO skomax_skomax;


--
-- Name: SEQUENCE m15_trend_indicators_indicator_id_seq; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE indicators.m15_trend_indicators_indicator_id_seq TO skomax_skomax;


--
-- Name: TABLE m1_special_indicators; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,TRUNCATE,UPDATE ON TABLE indicators.m1_special_indicators TO skomax_skomax;


--
-- Name: SEQUENCE m1_special_indicators_indicator_id_seq; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE indicators.m1_special_indicators_indicator_id_seq TO skomax_skomax;


--
-- Name: TABLE m1_standard_indicators; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,TRUNCATE,UPDATE ON TABLE indicators.m1_standard_indicators TO skomax_skomax;


--
-- Name: SEQUENCE m1_standard_indicators_indicator_id_seq; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE indicators.m1_standard_indicators_indicator_id_seq TO skomax_skomax;


--
-- Name: TABLE m3_oscillators; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,TRUNCATE,UPDATE ON TABLE indicators.m3_oscillators TO skomax_skomax;


--
-- Name: SEQUENCE m3_oscillators_oscillator_id_seq; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE indicators.m3_oscillators_oscillator_id_seq TO skomax_skomax;


--
-- Name: TABLE m3_trend_indicators; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,TRUNCATE,UPDATE ON TABLE indicators.m3_trend_indicators TO skomax_skomax;


--
-- Name: SEQUENCE m3_trend_indicators_indicator_id_seq; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE indicators.m3_trend_indicators_indicator_id_seq TO skomax_skomax;


--
-- Name: TABLE m5_oscillators; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,TRUNCATE,UPDATE ON TABLE indicators.m5_oscillators TO skomax_skomax;


--
-- Name: SEQUENCE m5_oscillators_oscillator_id_seq; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE indicators.m5_oscillators_oscillator_id_seq TO skomax_skomax;


--
-- Name: TABLE m5_trend_indicators; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,TRUNCATE,UPDATE ON TABLE indicators.m5_trend_indicators TO skomax_skomax;


--
-- Name: SEQUENCE m5_trend_indicators_indicator_id_seq; Type: ACL; Schema: indicators; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE indicators.m5_trend_indicators_indicator_id_seq TO skomax_skomax;


--
-- Name: TABLE candles; Type: ACL; Schema: market_data; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE market_data.candles TO skomax_skomax;


--
-- Name: SEQUENCE candles_candle_id_seq; Type: ACL; Schema: market_data; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE market_data.candles_candle_id_seq TO skomax_skomax;


--
-- Name: TABLE order_book; Type: ACL; Schema: market_data; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE market_data.order_book TO skomax_skomax;


--
-- Name: SEQUENCE order_book_order_book_id_seq; Type: ACL; Schema: market_data; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE market_data.order_book_order_book_id_seq TO skomax_skomax;


--
-- Name: TABLE symbols; Type: ACL; Schema: market_data; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE market_data.symbols TO skomax_skomax;


--
-- Name: SEQUENCE symbols_symbol_id_seq; Type: ACL; Schema: market_data; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE market_data.symbols_symbol_id_seq TO skomax_skomax;


--
-- Name: TABLE tickers; Type: ACL; Schema: market_data; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE market_data.tickers TO skomax_skomax;


--
-- Name: SEQUENCE tickers_ticker_id_seq; Type: ACL; Schema: market_data; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE market_data.tickers_ticker_id_seq TO skomax_skomax;


--
-- Name: TABLE timeframes; Type: ACL; Schema: market_data; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE market_data.timeframes TO skomax_skomax;


--
-- Name: SEQUENCE timeframes_timeframe_id_seq; Type: ACL; Schema: market_data; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE market_data.timeframes_timeframe_id_seq TO skomax_skomax;


--
-- Name: TABLE trades; Type: ACL; Schema: market_data; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE market_data.trades TO skomax_skomax;


--
-- Name: SEQUENCE trades_trade_id_seq; Type: ACL; Schema: market_data; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE market_data.trades_trade_id_seq TO skomax_skomax;


--
-- Name: TABLE ai_predictions; Type: ACL; Schema: predictions; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE predictions.ai_predictions TO skomax_skomax;


--
-- Name: SEQUENCE ai_predictions_prediction_id_seq; Type: ACL; Schema: predictions; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE predictions.ai_predictions_prediction_id_seq TO skomax_skomax;


--
-- Name: TABLE prompt_templates; Type: ACL; Schema: predictions; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE predictions.prompt_templates TO skomax_skomax;


--
-- Name: SEQUENCE prompt_templates_template_id_seq; Type: ACL; Schema: predictions; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE predictions.prompt_templates_template_id_seq TO skomax_skomax;


--
-- Name: TABLE sent_prompts; Type: ACL; Schema: predictions; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE predictions.sent_prompts TO skomax_skomax;


--
-- Name: SEQUENCE sent_prompts_prompt_id_seq; Type: ACL; Schema: predictions; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE predictions.sent_prompts_prompt_id_seq TO skomax_skomax;


--
-- Name: TABLE errors; Type: ACL; Schema: system_log; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE system_log.errors TO skomax_skomax;


--
-- Name: SEQUENCE errors_error_id_seq; Type: ACL; Schema: system_log; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE system_log.errors_error_id_seq TO skomax_skomax;


--
-- Name: TABLE events; Type: ACL; Schema: system_log; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE system_log.events TO skomax_skomax;


--
-- Name: SEQUENCE events_event_id_seq; Type: ACL; Schema: system_log; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE system_log.events_event_id_seq TO skomax_skomax;


--
-- Name: TABLE performance_metrics; Type: ACL; Schema: system_log; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE system_log.performance_metrics TO skomax_skomax;


--
-- Name: SEQUENCE performance_metrics_metric_id_seq; Type: ACL; Schema: system_log; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE system_log.performance_metrics_metric_id_seq TO skomax_skomax;


--
-- Name: TABLE prediction_results; Type: ACL; Schema: verification; Owner: postgres
--

GRANT ALL ON TABLE verification.prediction_results TO skomax_skomax;


--
-- Name: SEQUENCE prediction_results_result_id_seq; Type: ACL; Schema: verification; Owner: postgres
--

GRANT ALL ON SEQUENCE verification.prediction_results_result_id_seq TO skomax_skomax;


--
-- Name: TABLE prediction_statistics; Type: ACL; Schema: verification; Owner: postgres
--

GRANT ALL ON TABLE verification.prediction_statistics TO skomax_skomax;


--
-- Name: SEQUENCE prediction_statistics_stats_id_seq; Type: ACL; Schema: verification; Owner: postgres
--

GRANT ALL ON SEQUENCE verification.prediction_statistics_stats_id_seq TO skomax_skomax;


--
-- PostgreSQL database dump complete
--


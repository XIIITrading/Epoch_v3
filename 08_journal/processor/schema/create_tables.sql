-- =============================================================================
-- Epoch Trading Journal - M1 Bar Tables
-- Separate from backtest m1_bars / m1_indicator_bars tables
-- =============================================================================

-- Journal M1 Bars (raw OHLCV from Polygon)
CREATE TABLE IF NOT EXISTS journal_m1_bars (
    -- PRIMARY KEY
    id                  BIGSERIAL PRIMARY KEY,

    -- IDENTIFICATION
    ticker              VARCHAR(10) NOT NULL,
    bar_date            DATE NOT NULL,
    bar_time            TIME WITHOUT TIME ZONE NOT NULL,
    bar_timestamp       TIMESTAMPTZ NOT NULL,

    -- OHLCV DATA
    open                DECIMAL(12, 4) NOT NULL,
    high                DECIMAL(12, 4) NOT NULL,
    low                 DECIMAL(12, 4) NOT NULL,
    close               DECIMAL(12, 4) NOT NULL,
    volume              BIGINT NOT NULL,

    -- ADDITIONAL POLYGON DATA
    vwap                DECIMAL(12, 4),
    transactions        INTEGER,

    -- METADATA
    fetched_at          TIMESTAMPTZ DEFAULT NOW(),

    -- CONSTRAINTS
    CONSTRAINT journal_m1_bars_unique_bar UNIQUE (ticker, bar_timestamp)
);

-- Indexes for journal_m1_bars
CREATE INDEX IF NOT EXISTS idx_journal_m1_bars_ticker_date
    ON journal_m1_bars (ticker, bar_date);

CREATE INDEX IF NOT EXISTS idx_journal_m1_bars_ticker_date_time
    ON journal_m1_bars (ticker, bar_date, bar_time);

CREATE INDEX IF NOT EXISTS idx_journal_m1_bars_date
    ON journal_m1_bars (bar_date);


-- Journal M1 Indicator Bars (pre-computed indicators for ramp-up chart)
CREATE TABLE IF NOT EXISTS journal_m1_indicator_bars (
    -- PRIMARY KEY: ticker + bar_date + bar_time
    ticker              VARCHAR(10) NOT NULL,
    bar_date            DATE NOT NULL,
    bar_time            TIME WITHOUT TIME ZONE NOT NULL,

    -- OHLCV DATA
    open                NUMERIC(12, 4) NOT NULL,
    high                NUMERIC(12, 4) NOT NULL,
    low                 NUMERIC(12, 4) NOT NULL,
    close               NUMERIC(12, 4) NOT NULL,
    volume              BIGINT NOT NULL,

    -- Price Indicators
    vwap                NUMERIC(12, 4),
    sma9                NUMERIC(12, 4),
    sma21               NUMERIC(12, 4),
    sma_spread          NUMERIC(12, 4),
    sma_momentum_ratio  NUMERIC(10, 6),
    sma_momentum_label  VARCHAR(15),

    -- Volume Indicators
    vol_roc             NUMERIC(10, 4),
    vol_delta           NUMERIC(12, 2),
    cvd_slope           NUMERIC(10, 6),

    -- Multi-timeframe Structure
    h4_structure        VARCHAR(10),
    h1_structure        VARCHAR(10),
    m15_structure       VARCHAR(10),
    m5_structure        VARCHAR(10),
    m1_structure        VARCHAR(10),

    -- Health Score (0-10)
    health_score        INTEGER,

    -- Entry Qualifier Indicators (EPCH v1.0)
    candle_range_pct    NUMERIC(10, 6),
    long_score          INTEGER,
    short_score         INTEGER,

    -- Metadata
    bars_in_calculation INTEGER,
    calculated_at       TIMESTAMPTZ DEFAULT NOW(),

    -- PRIMARY KEY
    CONSTRAINT journal_m1_indicator_bars_pkey
        PRIMARY KEY (ticker, bar_date, bar_time)
);

-- Indexes for journal_m1_indicator_bars
CREATE INDEX IF NOT EXISTS idx_journal_m1_indicator_bars_ticker_date
    ON journal_m1_indicator_bars (ticker, bar_date);

CREATE INDEX IF NOT EXISTS idx_journal_m1_indicator_bars_date
    ON journal_m1_indicator_bars (bar_date);

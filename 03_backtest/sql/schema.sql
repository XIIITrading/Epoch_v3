-- ============================================================================
-- EPOCH TRADING SYSTEM - Backtest Module Schema
-- v4.1 - Entry Detection + M1 Bar Storage + M1 Indicator Bars
-- XIII Trading LLC
-- ============================================================================

-- ============================================================================
-- TABLE 1: trades_2
-- Entry detection results from EPCH1-4 models on S15 bars
-- ============================================================================

CREATE TABLE IF NOT EXISTS trades_2 (
    trade_id    VARCHAR PRIMARY KEY,
    date        DATE NOT NULL,
    ticker      VARCHAR NOT NULL,
    model       VARCHAR NOT NULL,       -- EPCH1, EPCH2, EPCH3, EPCH4
    zone_type   VARCHAR NOT NULL,       -- PRIMARY, SECONDARY
    direction   VARCHAR NOT NULL,       -- LONG, SHORT
    zone_high   NUMERIC,
    zone_low    NUMERIC,
    entry_price NUMERIC,
    entry_time  TIME,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trades_2_date ON trades_2 (date);
CREATE INDEX IF NOT EXISTS idx_trades_2_ticker ON trades_2 (ticker);
CREATE INDEX IF NOT EXISTS idx_trades_2_model ON trades_2 (model);

-- ============================================================================
-- TABLE 2: m1_bars_2
-- 1-minute bar data from Polygon API
-- Prior day 16:00 ET through trade day 16:00 ET
-- ============================================================================

CREATE TABLE IF NOT EXISTS m1_bars_2 (
    id              BIGSERIAL PRIMARY KEY,
    ticker          VARCHAR(10) NOT NULL,
    bar_date        DATE NOT NULL,              -- Trade date (all bars grouped here)
    bar_time        TIME NOT NULL,              -- Bar start time (ET)
    bar_timestamp   TIMESTAMPTZ NOT NULL,       -- Full timestamp with timezone
    open            NUMERIC(12, 4) NOT NULL,
    high            NUMERIC(12, 4) NOT NULL,
    low             NUMERIC(12, 4) NOT NULL,
    close           NUMERIC(12, 4) NOT NULL,
    volume          BIGINT NOT NULL,
    vwap            NUMERIC(12, 4),
    transactions    INTEGER,
    fetched_at      TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT m1_bars_2_unique_bar UNIQUE (ticker, bar_timestamp)
);

CREATE INDEX IF NOT EXISTS idx_m1_bars_2_ticker_date ON m1_bars_2 (ticker, bar_date);
CREATE INDEX IF NOT EXISTS idx_m1_bars_2_ticker_date_time ON m1_bars_2 (ticker, bar_date, bar_time);
CREATE INDEX IF NOT EXISTS idx_m1_bars_2_date ON m1_bars_2 (bar_date);
CREATE INDEX IF NOT EXISTS idx_m1_bars_2_ticker ON m1_bars_2 (ticker);

-- ============================================================================
-- TABLE 3: m1_indicator_bars_2
-- Pre-computed 1-minute indicator bars
-- Reads from m1_bars_2, computes 22 indicators + composite scores
-- Data range: Prior day 16:00 ET -> Trade day 16:00 ET (matches m1_bars_2)
-- Pipeline: trades_2 -> m1_bars_2 -> m1_indicator_bars_2
-- ============================================================================

CREATE TABLE IF NOT EXISTS m1_indicator_bars_2 (
    ticker VARCHAR(10) NOT NULL,
    bar_date DATE NOT NULL,
    bar_time TIME WITHOUT TIME ZONE NOT NULL,

    -- OHLCV (from m1_bars_2)
    open NUMERIC(12, 4) NOT NULL,
    high NUMERIC(12, 4) NOT NULL,
    low NUMERIC(12, 4) NOT NULL,
    close NUMERIC(12, 4) NOT NULL,
    volume BIGINT NOT NULL,

    -- Entry Qualifier Standard Indicators
    candle_range_pct NUMERIC(10, 6),       -- (high-low)/close * 100
    vol_delta_raw NUMERIC(12, 2),          -- Single bar delta: ((2*(close-low)/(high-low))-1)*volume
    vol_delta_roll NUMERIC(12, 2),         -- 5-bar rolling sum of raw delta
    vol_roc NUMERIC(10, 4),               -- ((vol-avg20)/avg20)*100
    sma9 NUMERIC(12, 4),                  -- 9-period SMA
    sma21 NUMERIC(12, 4),                 -- 21-period SMA
    sma_config VARCHAR(10),               -- BULL, BEAR, FLAT
    sma_spread_pct NUMERIC(10, 6),        -- abs(sma9-sma21)/close*100
    price_position VARCHAR(10),           -- ABOVE, BTWN, BELOW

    -- Extended Indicators
    vwap NUMERIC(12, 4),                  -- Cumulative session VWAP
    sma_spread NUMERIC(12, 4),            -- sma9 - sma21 (signed)
    sma_momentum_ratio NUMERIC(10, 6),    -- Current abs spread / abs spread 10 bars ago
    sma_momentum_label VARCHAR(15),       -- WIDENING, NARROWING, STABLE
    cvd_slope NUMERIC(10, 6),             -- Normalized CVD slope (15-bar window)

    -- Multi-timeframe Structure (fractal BOS/ChoCH method)
    h4_structure VARCHAR(10),             -- BULL, BEAR, NEUTRAL
    h1_structure VARCHAR(10),
    m15_structure VARCHAR(10),
    m5_structure VARCHAR(10),
    m1_structure VARCHAR(10),

    -- Composite Scores
    health_score INTEGER,                 -- 0-10 direction-agnostic quality score
    long_score INTEGER,                   -- 0-7 long composite score
    short_score INTEGER,                  -- 0-7 short composite score

    -- Metadata
    bars_in_calculation INTEGER,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT m1_indicator_bars_2_pkey PRIMARY KEY (ticker, bar_date, bar_time)
);

CREATE INDEX IF NOT EXISTS idx_m1_indicator_bars_2_ticker_date
    ON m1_indicator_bars_2 (ticker, bar_date);

CREATE INDEX IF NOT EXISTS idx_m1_indicator_bars_2_date
    ON m1_indicator_bars_2 (bar_date);

CREATE INDEX IF NOT EXISTS idx_m1_indicator_bars_2_structure
    ON m1_indicator_bars_2 (ticker, bar_date, m1_structure, m5_structure);

CREATE INDEX IF NOT EXISTS idx_m1_indicator_bars_2_sma_config
    ON m1_indicator_bars_2 (ticker, bar_date, sma_config, price_position);

-- ============================================================================
-- JOURNAL TABLE 2: j_m1_indicator_bars
-- Pre-computed 1-minute indicator bars for journal trades
-- 22 indicators + multi-TF structure + composite scores
-- Mirrors m1_indicator_bars_2 from backtest
-- Pipeline: journal_trades -> j_m1_bars -> j_m1_indicator_bars
-- ============================================================================

CREATE TABLE IF NOT EXISTS j_m1_indicator_bars (
    ticker VARCHAR(10) NOT NULL,
    bar_date DATE NOT NULL,
    bar_time TIME WITHOUT TIME ZONE NOT NULL,

    -- OHLCV (from j_m1_bars)
    open NUMERIC(12, 4) NOT NULL,
    high NUMERIC(12, 4) NOT NULL,
    low NUMERIC(12, 4) NOT NULL,
    close NUMERIC(12, 4) NOT NULL,
    volume BIGINT NOT NULL,

    -- Entry Qualifier Standard Indicators
    candle_range_pct NUMERIC(10, 6),       -- (high-low)/close * 100
    vol_delta_raw NUMERIC(12, 2),          -- Single bar delta
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

    -- ATR values (multi-timeframe)
    atr_m1 NUMERIC(12, 6),
    atr_m5 NUMERIC(12, 6),
    atr_m15 NUMERIC(12, 6),

    -- Metadata
    bars_in_calculation INTEGER,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT j_m1_indicator_bars_pkey PRIMARY KEY (ticker, bar_date, bar_time)
);

CREATE INDEX IF NOT EXISTS idx_j_m1_ind_bars_ticker_date
    ON j_m1_indicator_bars (ticker, bar_date);
CREATE INDEX IF NOT EXISTS idx_j_m1_ind_bars_date
    ON j_m1_indicator_bars (bar_date);
CREATE INDEX IF NOT EXISTS idx_j_m1_ind_bars_structure
    ON j_m1_indicator_bars (ticker, bar_date, m1_structure, m5_structure);
CREATE INDEX IF NOT EXISTS idx_j_m1_ind_bars_sma_config
    ON j_m1_indicator_bars (ticker, bar_date, sma_config, price_position);

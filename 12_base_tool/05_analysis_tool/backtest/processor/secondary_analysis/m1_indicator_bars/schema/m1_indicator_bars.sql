-- M1 Indicator Bars Schema
-- 1-minute bars with pre-computed indicators for ramp-up analysis
-- Similar to m5_indicator_bars but at 1-minute resolution

CREATE TABLE IF NOT EXISTS m1_indicator_bars (
    ticker VARCHAR(10) NOT NULL,
    bar_date DATE NOT NULL,
    bar_time TIME WITHOUT TIME ZONE NOT NULL,
    open NUMERIC(12, 4) NOT NULL,
    high NUMERIC(12, 4) NOT NULL,
    low NUMERIC(12, 4) NOT NULL,
    close NUMERIC(12, 4) NOT NULL,
    volume BIGINT NOT NULL,

    -- Price Indicators
    vwap NUMERIC(12, 4),
    sma9 NUMERIC(12, 4),
    sma21 NUMERIC(12, 4),
    sma_spread NUMERIC(12, 4),
    sma_momentum_ratio NUMERIC(10, 6),
    sma_momentum_label VARCHAR(15),

    -- Volume Indicators
    vol_roc NUMERIC(10, 4),
    vol_delta NUMERIC(12, 2),
    cvd_slope NUMERIC(10, 6),

    -- Multi-timeframe Structure
    h4_structure VARCHAR(10),
    h1_structure VARCHAR(10),
    m15_structure VARCHAR(10),
    m5_structure VARCHAR(10),
    m1_structure VARCHAR(10),

    -- Health Score (0-10)
    health_score INTEGER,

    -- Entry Qualifier Indicators (EPCH v1.0)
    candle_range_pct NUMERIC(10, 6),  -- Candle range as % of price
    long_score INTEGER,                -- LONG composite score (0-7)
    short_score INTEGER,               -- SHORT composite score (0-7)

    -- Metadata
    bars_in_calculation INTEGER,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT m1_indicator_bars_pkey PRIMARY KEY (ticker, bar_date, bar_time)
) TABLESPACE pg_default;

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_m1_indicator_bars_ticker_date
    ON m1_indicator_bars USING btree (ticker, bar_date) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_m1_indicator_bars_date
    ON m1_indicator_bars USING btree (bar_date) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_m1_indicator_bars_structure
    ON m1_indicator_bars USING btree (ticker, bar_date, m1_structure, m5_structure) TABLESPACE pg_default;

-- Comment
COMMENT ON TABLE m1_indicator_bars IS 'Pre-computed 1-minute indicator bars for ramp-up chart analysis in training module';

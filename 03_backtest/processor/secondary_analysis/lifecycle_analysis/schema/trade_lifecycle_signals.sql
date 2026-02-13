-- =============================================================================
-- EPOCH TRADING SYSTEM - TRADE LIFECYCLE SIGNALS TABLE
-- =============================================================================
-- Stores derived indicator signals for each trade's lifecycle phases:
--   RAMPUP  = 30 M1 bars before entry
--   ENTRY   = snapshot at entry bar
--   POST    = 30 M1 bars after entry
--
-- Each row = one trade. Columns encode the trend signal, entry level,
-- and flip detection for each M1 indicator across lifecycle phases.
-- =============================================================================

DROP TABLE IF EXISTS trade_lifecycle_signals;

CREATE TABLE trade_lifecycle_signals (
    -- Primary key
    trade_id            VARCHAR(100) PRIMARY KEY,

    -- Trade context
    ticker              VARCHAR(10) NOT NULL,
    date                DATE NOT NULL,
    entry_time          TIME NOT NULL,
    direction           VARCHAR(10) NOT NULL,
    model               VARCHAR(10) NOT NULL,
    is_winner           BOOLEAN NOT NULL,

    -- M1 bars found for this trade
    rampup_bars_found   INTEGER NOT NULL DEFAULT 0,
    post_entry_bars_found INTEGER NOT NULL DEFAULT 0,

    -- =================================================================
    -- RAMPUP TREND SIGNALS (30-bar M1 window before entry)
    -- Values: INCREASING, DECREASING, FLAT, INC_THEN_DEC,
    --         DEC_THEN_INC, VOLATILE, INSUFFICIENT
    -- =================================================================
    rampup_candle_range_pct     VARCHAR(20),
    rampup_vol_delta            VARCHAR(20),
    rampup_vol_roc              VARCHAR(20),
    rampup_cvd_slope            VARCHAR(20),
    rampup_sma_spread           VARCHAR(20),
    rampup_sma_momentum_ratio   VARCHAR(20),
    rampup_health_score         VARCHAR(20),
    rampup_long_score           VARCHAR(20),
    rampup_short_score          VARCHAR(20),

    -- =================================================================
    -- ENTRY LEVEL SIGNALS (snapshot at entry bar)
    -- Values: indicator-specific level labels (see config.py)
    -- =================================================================
    entry_candle_range_pct      VARCHAR(20),
    entry_vol_delta             VARCHAR(20),
    entry_vol_roc               VARCHAR(20),
    entry_cvd_slope             VARCHAR(20),
    entry_sma_spread            VARCHAR(20),
    entry_sma_momentum_ratio    VARCHAR(20),
    entry_health_score          VARCHAR(20),
    entry_long_score            VARCHAR(20),
    entry_short_score           VARCHAR(20),

    -- Entry categorical snapshots
    entry_sma_momentum_label    VARCHAR(20),
    entry_m1_structure          VARCHAR(20),
    entry_m5_structure          VARCHAR(20),
    entry_m15_structure         VARCHAR(20),
    entry_h1_structure          VARCHAR(20),
    entry_h4_structure          VARCHAR(20),

    -- =================================================================
    -- POST-ENTRY TREND SIGNALS (30-bar M1 window after entry)
    -- Values: same as rampup signals
    -- =================================================================
    post_candle_range_pct       VARCHAR(20),
    post_vol_delta              VARCHAR(20),
    post_vol_roc                VARCHAR(20),
    post_cvd_slope              VARCHAR(20),
    post_sma_spread             VARCHAR(20),
    post_sma_momentum_ratio     VARCHAR(20),
    post_health_score           VARCHAR(20),
    post_long_score             VARCHAR(20),
    post_short_score            VARCHAR(20),

    -- =================================================================
    -- FLIP SIGNALS (sign changes during rampup)
    -- Values: NO_FLIP, FLIP_TO_POSITIVE, FLIP_TO_NEGATIVE,
    --         MULTIPLE_FLIPS, INSUFFICIENT, N/A
    -- =================================================================
    flip_vol_delta              VARCHAR(20),
    flip_cvd_slope              VARCHAR(20),
    flip_sma_spread             VARCHAR(20),

    -- =================================================================
    -- M5 PROGRESSION CONTEXT
    -- =================================================================
    m5_health_at_entry          INTEGER,
    m5_health_at_end            INTEGER,
    m5_health_trend             VARCHAR(20),
    m5_bars_total               INTEGER DEFAULT 0,

    -- Metadata
    calculated_at               TIMESTAMPTZ DEFAULT NOW(),
    calculation_version         VARCHAR(10) DEFAULT '1.0'
);

-- Indexes for common query patterns
CREATE INDEX idx_lifecycle_ticker_date ON trade_lifecycle_signals(ticker, date);
CREATE INDEX idx_lifecycle_direction ON trade_lifecycle_signals(direction);
CREATE INDEX idx_lifecycle_model ON trade_lifecycle_signals(model);
CREATE INDEX idx_lifecycle_winner ON trade_lifecycle_signals(is_winner);
CREATE INDEX idx_lifecycle_rampup_candle ON trade_lifecycle_signals(rampup_candle_range_pct);
CREATE INDEX idx_lifecycle_rampup_vol_delta ON trade_lifecycle_signals(rampup_vol_delta);
CREATE INDEX idx_lifecycle_entry_health ON trade_lifecycle_signals(entry_health_score);
CREATE INDEX idx_lifecycle_flip_vol_delta ON trade_lifecycle_signals(flip_vol_delta);

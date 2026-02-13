-- ============================================================================
-- EPOCH TRADING SYSTEM - RAMP-UP ANALYSIS TABLES
-- Pre-calculated indicator progression for Claude Code analysis
-- XIII Trading LLC
-- ============================================================================

-- ============================================================================
-- TABLE: ramp_up_macro
-- One row per trade with summary metrics
-- ============================================================================
CREATE TABLE IF NOT EXISTS ramp_up_macro (
    -- Primary Key
    trade_id VARCHAR(50) PRIMARY KEY,

    -- Stop Analysis Configuration
    stop_type VARCHAR(20) NOT NULL,
    lookback_bars INTEGER NOT NULL,

    -- Trade Identity (from trades table)
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    model VARCHAR(10) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    entry_time TIME NOT NULL,

    -- Outcome Metrics (from stop_analysis table)
    outcome VARCHAR(10) NOT NULL,  -- WIN, LOSS, PARTIAL
    mfe_distance DECIMAL(10, 4),
    r_achieved DECIMAL(10, 4),

    -- Entry Bar Snapshot (bar 0) - Raw indicator values at entry
    entry_candle_range_pct DECIMAL(10, 4),
    entry_vol_delta DECIMAL(15, 4),
    entry_vol_roc DECIMAL(10, 4),
    entry_sma_spread DECIMAL(10, 6),
    entry_sma_momentum_ratio DECIMAL(10, 4),
    entry_m15_structure VARCHAR(10),
    entry_h1_structure VARCHAR(10),
    entry_long_score INTEGER,
    entry_short_score INTEGER,

    -- Ramp Averages (bars -15 to -1)
    ramp_avg_candle_range_pct DECIMAL(10, 4),
    ramp_avg_vol_delta DECIMAL(15, 4),
    ramp_avg_vol_roc DECIMAL(10, 4),
    ramp_avg_sma_spread DECIMAL(10, 6),
    ramp_avg_sma_momentum_ratio DECIMAL(10, 4),
    ramp_avg_long_score DECIMAL(10, 4),
    ramp_avg_short_score DECIMAL(10, 4),

    -- Ramp Trends (Linear regression classification: RISING, FALLING, FLAT)
    ramp_trend_candle_range_pct VARCHAR(10),
    ramp_trend_vol_delta VARCHAR(10),
    ramp_trend_vol_roc VARCHAR(10),
    ramp_trend_sma_spread VARCHAR(10),
    ramp_trend_sma_momentum_ratio VARCHAR(10),
    ramp_trend_long_score VARCHAR(10),
    ramp_trend_short_score VARCHAR(10),

    -- Ramp Momentum (First-half vs Second-half: BUILDING, FADING, STABLE)
    ramp_momentum_candle_range_pct VARCHAR(10),
    ramp_momentum_vol_delta VARCHAR(10),
    ramp_momentum_vol_roc VARCHAR(10),
    ramp_momentum_sma_spread VARCHAR(10),
    ramp_momentum_sma_momentum_ratio VARCHAR(10),
    ramp_momentum_long_score VARCHAR(10),
    ramp_momentum_short_score VARCHAR(10),

    -- Structure Consistency (for categorical indicators)
    ramp_structure_m15 VARCHAR(20),  -- CONSISTENT_BULL, CONSISTENT_BEAR, MIXED, FLIP_TO_BULL, etc.
    ramp_structure_h1 VARCHAR(20),

    -- Metadata
    bars_analyzed INTEGER,  -- Actual bars found (may be < lookback_bars)
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_ramp_up_macro_date ON ramp_up_macro(date);
CREATE INDEX IF NOT EXISTS idx_ramp_up_macro_model ON ramp_up_macro(model);
CREATE INDEX IF NOT EXISTS idx_ramp_up_macro_direction ON ramp_up_macro(direction);
CREATE INDEX IF NOT EXISTS idx_ramp_up_macro_outcome ON ramp_up_macro(outcome);
CREATE INDEX IF NOT EXISTS idx_ramp_up_macro_stop_type ON ramp_up_macro(stop_type);

-- Composite index for filtering
CREATE INDEX IF NOT EXISTS idx_ramp_up_macro_model_direction_outcome
    ON ramp_up_macro(model, direction, outcome);

-- ============================================================================
-- TABLE: ramp_up_progression
-- 16 rows per trade (bars -15 to 0)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ramp_up_progression (
    -- Composite Primary Key
    trade_id VARCHAR(50) NOT NULL,
    bars_to_entry INTEGER NOT NULL,  -- -15, -14, ... -1, 0

    -- Bar Time
    bar_time TIME NOT NULL,

    -- Raw Indicator Values at this bar
    candle_range_pct DECIMAL(10, 4),
    vol_delta DECIMAL(15, 4),
    vol_roc DECIMAL(10, 4),
    sma_spread DECIMAL(10, 6),
    sma_momentum_ratio DECIMAL(10, 4),
    m15_structure VARCHAR(10),
    h1_structure VARCHAR(10),
    long_score INTEGER,
    short_score INTEGER,

    -- Metadata
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Primary Key
    PRIMARY KEY (trade_id, bars_to_entry)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_ramp_up_progression_trade_id
    ON ramp_up_progression(trade_id);
CREATE INDEX IF NOT EXISTS idx_ramp_up_progression_bars_to_entry
    ON ramp_up_progression(bars_to_entry);

-- Foreign key (optional, depends on your setup)
-- ALTER TABLE ramp_up_progression
--     ADD CONSTRAINT fk_ramp_up_progression_trade
--     FOREIGN KEY (trade_id) REFERENCES trades(trade_id);

-- ============================================================================
-- VIEW: v_ramp_up_analysis
-- Combined view for easy querying
-- ============================================================================
CREATE OR REPLACE VIEW v_ramp_up_analysis AS
SELECT
    m.trade_id,
    m.date,
    m.ticker,
    m.model,
    m.direction,
    m.entry_time,
    m.outcome,
    m.mfe_distance,
    m.r_achieved,
    m.stop_type,

    -- Entry bar values
    m.entry_long_score,
    m.entry_short_score,
    m.entry_vol_roc,
    m.entry_sma_spread,

    -- Ramp metrics
    m.ramp_avg_long_score,
    m.ramp_avg_short_score,
    m.ramp_avg_vol_roc,

    -- Trends
    m.ramp_trend_long_score,
    m.ramp_trend_short_score,
    m.ramp_trend_vol_roc,

    -- Momentum
    m.ramp_momentum_long_score,
    m.ramp_momentum_short_score,
    m.ramp_momentum_vol_roc,

    -- Structure
    m.ramp_structure_h1,
    m.ramp_structure_m15,

    m.bars_analyzed
FROM ramp_up_macro m;

-- ============================================================================
-- VIEW: v_ramp_up_summary_by_trend
-- Aggregate win rates by trend patterns
-- ============================================================================
CREATE OR REPLACE VIEW v_ramp_up_summary_by_trend AS
SELECT
    model,
    direction,
    ramp_trend_long_score,
    ramp_trend_vol_roc,
    COUNT(*) as total_trades,
    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
    ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) as win_rate,
    ROUND(AVG(r_achieved), 2) as avg_r_achieved
FROM ramp_up_macro
WHERE outcome IN ('WIN', 'LOSS')
GROUP BY model, direction, ramp_trend_long_score, ramp_trend_vol_roc
ORDER BY model, direction, win_rate DESC;

-- ============================================================================
-- VIEW: v_ramp_up_summary_by_momentum
-- Aggregate win rates by momentum patterns
-- ============================================================================
CREATE OR REPLACE VIEW v_ramp_up_summary_by_momentum AS
SELECT
    model,
    direction,
    ramp_momentum_long_score,
    ramp_momentum_vol_roc,
    COUNT(*) as total_trades,
    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
    ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) as win_rate,
    ROUND(AVG(r_achieved), 2) as avg_r_achieved
FROM ramp_up_macro
WHERE outcome IN ('WIN', 'LOSS')
GROUP BY model, direction, ramp_momentum_long_score, ramp_momentum_vol_roc
ORDER BY model, direction, win_rate DESC;

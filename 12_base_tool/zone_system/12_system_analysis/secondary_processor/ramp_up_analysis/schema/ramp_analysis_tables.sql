-- ============================================================================
-- EPOCH TRADING SYSTEM - RAMP-UP INDICATOR ANALYSIS TABLES
-- Derivative analysis tables for Claude Code review
-- XIII Trading LLC
-- ============================================================================

-- ============================================================================
-- TABLE 1: ramp_analysis_direction
-- Aggregates by trade direction (Long vs Short)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ramp_analysis_direction (
    id SERIAL PRIMARY KEY,
    direction VARCHAR(10) NOT NULL,  -- LONG, SHORT
    total_trades INTEGER NOT NULL,
    wins INTEGER NOT NULL,
    losses INTEGER NOT NULL,
    win_rate DECIMAL(5, 4),  -- e.g., 0.5234 = 52.34%
    avg_r_achieved DECIMAL(10, 4),
    avg_mfe_distance DECIMAL(10, 4),
    is_significant BOOLEAN DEFAULT TRUE,  -- FALSE if < 30 trades
    stop_type VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(direction, stop_type)
);

-- ============================================================================
-- TABLE 2: ramp_analysis_trade_type
-- Aggregates by continuation vs rejection
-- ============================================================================
CREATE TABLE IF NOT EXISTS ramp_analysis_trade_type (
    id SERIAL PRIMARY KEY,
    trade_type VARCHAR(20) NOT NULL,  -- CONTINUATION, REJECTION
    models VARCHAR(50) NOT NULL,  -- "EPCH1,EPCH3" or "EPCH2,EPCH4"
    total_trades INTEGER NOT NULL,
    wins INTEGER NOT NULL,
    losses INTEGER NOT NULL,
    win_rate DECIMAL(5, 4),
    avg_r_achieved DECIMAL(10, 4),
    avg_mfe_distance DECIMAL(10, 4),
    is_significant BOOLEAN DEFAULT TRUE,
    stop_type VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(trade_type, stop_type)
);

-- ============================================================================
-- TABLE 3: ramp_analysis_model
-- Aggregates by individual model
-- ============================================================================
CREATE TABLE IF NOT EXISTS ramp_analysis_model (
    id SERIAL PRIMARY KEY,
    model VARCHAR(10) NOT NULL,  -- EPCH1, EPCH2, EPCH3, EPCH4
    trade_type VARCHAR(20) NOT NULL,  -- CONTINUATION or REJECTION
    zone_type VARCHAR(20) NOT NULL,  -- PRIMARY or SECONDARY
    total_trades INTEGER NOT NULL,
    wins INTEGER NOT NULL,
    losses INTEGER NOT NULL,
    win_rate DECIMAL(5, 4),
    avg_r_achieved DECIMAL(10, 4),
    avg_mfe_distance DECIMAL(10, 4),
    is_significant BOOLEAN DEFAULT TRUE,
    stop_type VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(model, stop_type)
);

-- ============================================================================
-- TABLE 4: ramp_analysis_model_direction
-- Aggregates by model + direction (8 combinations)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ramp_analysis_model_direction (
    id SERIAL PRIMARY KEY,
    model VARCHAR(10) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    trade_type VARCHAR(20) NOT NULL,
    zone_type VARCHAR(20) NOT NULL,
    total_trades INTEGER NOT NULL,
    wins INTEGER NOT NULL,
    losses INTEGER NOT NULL,
    win_rate DECIMAL(5, 4),
    avg_r_achieved DECIMAL(10, 4),
    avg_mfe_distance DECIMAL(10, 4),
    is_significant BOOLEAN DEFAULT TRUE,
    stop_type VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(model, direction, stop_type)
);

-- ============================================================================
-- TABLE 5: ramp_analysis_indicator_trend
-- Win rates by indicator trend state (RISING, FALLING, FLAT)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ramp_analysis_indicator_trend (
    id SERIAL PRIMARY KEY,
    grouping_type VARCHAR(30) NOT NULL,  -- direction, trade_type, model, model_direction
    grouping_value VARCHAR(30) NOT NULL,  -- e.g., "LONG", "CONTINUATION", "EPCH1", "EPCH1_LONG"
    indicator VARCHAR(50) NOT NULL,  -- vol_delta, vol_roc, sma_spread, long_score, short_score, etc.
    trend_state VARCHAR(10) NOT NULL,  -- RISING, FALLING, FLAT
    total_trades INTEGER NOT NULL,
    wins INTEGER NOT NULL,
    losses INTEGER NOT NULL,
    win_rate DECIMAL(5, 4),
    baseline_win_rate DECIMAL(5, 4),  -- win rate for the grouping overall
    lift_vs_baseline DECIMAL(5, 4),  -- win_rate - baseline_win_rate
    is_significant BOOLEAN DEFAULT TRUE,
    stop_type VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(grouping_type, grouping_value, indicator, trend_state, stop_type)
);

CREATE INDEX IF NOT EXISTS idx_ramp_analysis_indicator_trend_grouping
    ON ramp_analysis_indicator_trend(grouping_type, grouping_value);
CREATE INDEX IF NOT EXISTS idx_ramp_analysis_indicator_trend_indicator
    ON ramp_analysis_indicator_trend(indicator);

-- ============================================================================
-- TABLE 6: ramp_analysis_indicator_momentum
-- Win rates by indicator momentum state (BUILDING, FADING, STABLE)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ramp_analysis_indicator_momentum (
    id SERIAL PRIMARY KEY,
    grouping_type VARCHAR(30) NOT NULL,
    grouping_value VARCHAR(30) NOT NULL,
    indicator VARCHAR(50) NOT NULL,
    momentum_state VARCHAR(10) NOT NULL,  -- BUILDING, FADING, STABLE
    total_trades INTEGER NOT NULL,
    wins INTEGER NOT NULL,
    losses INTEGER NOT NULL,
    win_rate DECIMAL(5, 4),
    baseline_win_rate DECIMAL(5, 4),
    lift_vs_baseline DECIMAL(5, 4),
    is_significant BOOLEAN DEFAULT TRUE,
    stop_type VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(grouping_type, grouping_value, indicator, momentum_state, stop_type)
);

CREATE INDEX IF NOT EXISTS idx_ramp_analysis_indicator_momentum_grouping
    ON ramp_analysis_indicator_momentum(grouping_type, grouping_value);
CREATE INDEX IF NOT EXISTS idx_ramp_analysis_indicator_momentum_indicator
    ON ramp_analysis_indicator_momentum(indicator);

-- ============================================================================
-- TABLE 7: ramp_analysis_structure_consistency
-- Win rates by structure consistency state
-- ============================================================================
CREATE TABLE IF NOT EXISTS ramp_analysis_structure_consistency (
    id SERIAL PRIMARY KEY,
    grouping_type VARCHAR(30) NOT NULL,
    grouping_value VARCHAR(30) NOT NULL,
    indicator VARCHAR(50) NOT NULL,  -- m15_structure, h1_structure
    consistency_state VARCHAR(20) NOT NULL,  -- CONSISTENT_BULL, CONSISTENT_BEAR, MIXED, FLIP_TO_BULL, FLIP_TO_BEAR
    total_trades INTEGER NOT NULL,
    wins INTEGER NOT NULL,
    losses INTEGER NOT NULL,
    win_rate DECIMAL(5, 4),
    baseline_win_rate DECIMAL(5, 4),
    lift_vs_baseline DECIMAL(5, 4),
    is_significant BOOLEAN DEFAULT TRUE,
    stop_type VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(grouping_type, grouping_value, indicator, consistency_state, stop_type)
);

CREATE INDEX IF NOT EXISTS idx_ramp_analysis_structure_grouping
    ON ramp_analysis_structure_consistency(grouping_type, grouping_value);

-- ============================================================================
-- TABLE 8: ramp_analysis_entry_snapshot
-- Win rates by entry bar indicator values (bucketed)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ramp_analysis_entry_snapshot (
    id SERIAL PRIMARY KEY,
    grouping_type VARCHAR(30) NOT NULL,
    grouping_value VARCHAR(30) NOT NULL,
    indicator VARCHAR(50) NOT NULL,  -- long_score, short_score, vol_roc, vol_delta
    bucket VARCHAR(30) NOT NULL,  -- e.g., "LOW (0-2)", "MID (3-4)", "HIGH (5-7)"
    bucket_min DECIMAL(15, 4),  -- numeric range start
    bucket_max DECIMAL(15, 4),  -- numeric range end
    total_trades INTEGER NOT NULL,
    wins INTEGER NOT NULL,
    losses INTEGER NOT NULL,
    win_rate DECIMAL(5, 4),
    baseline_win_rate DECIMAL(5, 4),
    lift_vs_baseline DECIMAL(5, 4),
    is_significant BOOLEAN DEFAULT TRUE,
    stop_type VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(grouping_type, grouping_value, indicator, bucket, stop_type)
);

CREATE INDEX IF NOT EXISTS idx_ramp_analysis_entry_snapshot_grouping
    ON ramp_analysis_entry_snapshot(grouping_type, grouping_value);
CREATE INDEX IF NOT EXISTS idx_ramp_analysis_entry_snapshot_indicator
    ON ramp_analysis_entry_snapshot(indicator);

-- ============================================================================
-- TABLE 9: ramp_analysis_progression_avg
-- Average indicator values at each bar position, by outcome
-- ============================================================================
CREATE TABLE IF NOT EXISTS ramp_analysis_progression_avg (
    id SERIAL PRIMARY KEY,
    grouping_type VARCHAR(30) NOT NULL,
    grouping_value VARCHAR(30) NOT NULL,
    outcome VARCHAR(10) NOT NULL,  -- WIN, LOSS
    bars_to_entry INTEGER NOT NULL,  -- -15 to 0
    avg_candle_range_pct DECIMAL(10, 4),
    avg_vol_delta DECIMAL(15, 4),
    avg_vol_roc DECIMAL(10, 4),
    avg_sma_spread DECIMAL(10, 6),
    avg_sma_momentum_ratio DECIMAL(10, 4),
    avg_long_score DECIMAL(10, 4),
    avg_short_score DECIMAL(10, 4),
    sample_size INTEGER NOT NULL,
    is_significant BOOLEAN DEFAULT TRUE,
    stop_type VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(grouping_type, grouping_value, outcome, bars_to_entry, stop_type)
);

CREATE INDEX IF NOT EXISTS idx_ramp_analysis_progression_avg_grouping
    ON ramp_analysis_progression_avg(grouping_type, grouping_value);
CREATE INDEX IF NOT EXISTS idx_ramp_analysis_progression_avg_outcome
    ON ramp_analysis_progression_avg(outcome);

-- ============================================================================
-- TABLE 10: ramp_analysis_progression_patterns
-- Representative sequences for pattern analysis
-- ============================================================================
CREATE TABLE IF NOT EXISTS ramp_analysis_progression_patterns (
    id SERIAL PRIMARY KEY,
    pattern_id VARCHAR(50) NOT NULL,  -- unique identifier for the pattern
    grouping_type VARCHAR(30) NOT NULL,
    grouping_value VARCHAR(30) NOT NULL,
    outcome VARCHAR(10) NOT NULL,  -- WIN, LOSS
    trade_ids TEXT[] NOT NULL,  -- array of trade IDs in this pattern
    sample_size INTEGER NOT NULL,
    pattern_sequence JSONB NOT NULL,  -- bar-by-bar indicator values
    pattern_description TEXT,  -- human-readable description
    is_significant BOOLEAN DEFAULT TRUE,
    stop_type VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(pattern_id, stop_type)
);

CREATE INDEX IF NOT EXISTS idx_ramp_analysis_progression_patterns_grouping
    ON ramp_analysis_progression_patterns(grouping_type, grouping_value);
CREATE INDEX IF NOT EXISTS idx_ramp_analysis_progression_patterns_outcome
    ON ramp_analysis_progression_patterns(outcome);

-- ============================================================================
-- VIEW: v_ramp_analysis_summary
-- Quick overview of all analysis tables
-- ============================================================================
CREATE OR REPLACE VIEW v_ramp_analysis_summary AS
SELECT
    'direction' as analysis_type,
    COUNT(*) as row_count,
    SUM(total_trades) as total_trades,
    MAX(calculated_at) as last_updated
FROM ramp_analysis_direction
UNION ALL
SELECT
    'trade_type',
    COUNT(*),
    SUM(total_trades),
    MAX(calculated_at)
FROM ramp_analysis_trade_type
UNION ALL
SELECT
    'model',
    COUNT(*),
    SUM(total_trades),
    MAX(calculated_at)
FROM ramp_analysis_model
UNION ALL
SELECT
    'model_direction',
    COUNT(*),
    SUM(total_trades),
    MAX(calculated_at)
FROM ramp_analysis_model_direction
UNION ALL
SELECT
    'indicator_trend',
    COUNT(*),
    SUM(total_trades),
    MAX(calculated_at)
FROM ramp_analysis_indicator_trend
UNION ALL
SELECT
    'indicator_momentum',
    COUNT(*),
    SUM(total_trades),
    MAX(calculated_at)
FROM ramp_analysis_indicator_momentum
UNION ALL
SELECT
    'structure_consistency',
    COUNT(*),
    SUM(total_trades),
    MAX(calculated_at)
FROM ramp_analysis_structure_consistency
UNION ALL
SELECT
    'entry_snapshot',
    COUNT(*),
    SUM(total_trades),
    MAX(calculated_at)
FROM ramp_analysis_entry_snapshot
UNION ALL
SELECT
    'progression_avg',
    COUNT(*),
    SUM(sample_size),
    MAX(calculated_at)
FROM ramp_analysis_progression_avg
UNION ALL
SELECT
    'progression_patterns',
    COUNT(*),
    SUM(sample_size),
    MAX(calculated_at)
FROM ramp_analysis_progression_patterns;

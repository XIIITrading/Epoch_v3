-- DOW AI Context Tables
-- Epoch Trading System v1 - XIII Trading LLC
-- Created: 2026-01-22
--
-- These tables store aggregated historical data for DOW AI prompts.
-- Populated weekly via refresh_ai_context.py workflow.

-- =============================================================================
-- Table 1: ai_model_stats
-- Performance metrics by EPCH model (1-4) and direction (LONG/SHORT)
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_model_stats (
    id SERIAL PRIMARY KEY,
    model VARCHAR(10) NOT NULL,           -- EPCH1, EPCH2, EPCH3, EPCH4
    direction VARCHAR(10) NOT NULL,        -- LONG, SHORT
    total_trades INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    win_rate DECIMAL(5,2) NOT NULL DEFAULT 0,
    avg_mfe_r DECIMAL(5,2),               -- Average MFE in R-multiples
    avg_mae_r DECIMAL(5,2),               -- Average MAE in R-multiples
    best_stop_type VARCHAR(30),           -- Best performing stop type
    best_stop_win_rate DECIMAL(5,2),      -- Win rate with best stop
    avg_time_to_target_min INTEGER,       -- Average time to target in minutes
    date_from DATE NOT NULL,              -- Start of data range
    date_to DATE NOT NULL,                -- End of data range
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_model_direction UNIQUE(model, direction)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_ai_model_stats_model ON ai_model_stats(model);
CREATE INDEX IF NOT EXISTS idx_ai_model_stats_direction ON ai_model_stats(direction);

COMMENT ON TABLE ai_model_stats IS 'Aggregated performance metrics by EPCH model and direction for DOW AI prompts';
COMMENT ON COLUMN ai_model_stats.model IS 'EPCH model code: EPCH1 (Primary Continuation), EPCH2 (Primary Reversal), EPCH3 (Secondary Continuation), EPCH4 (Secondary Reversal)';
COMMENT ON COLUMN ai_model_stats.avg_mfe_r IS 'Average Maximum Favorable Excursion in R-multiples (how far price moved in favor before exit)';
COMMENT ON COLUMN ai_model_stats.avg_mae_r IS 'Average Maximum Adverse Excursion in R-multiples (how far price moved against before recovery)';


-- =============================================================================
-- Table 2: ai_indicator_edges
-- Validated indicator edges from 03_indicators edge testing
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_indicator_edges (
    id SERIAL PRIMARY KEY,
    indicator VARCHAR(50) NOT NULL,        -- candle_range, volume_delta, etc.
    segment VARCHAR(50) NOT NULL,          -- ALL, LONG, SHORT, EPCH1, etc.
    test_name VARCHAR(100),                -- Specific test name if applicable
    has_edge BOOLEAN NOT NULL DEFAULT FALSE,
    p_value DECIMAL(10,8),                 -- Statistical p-value
    effect_size_pp DECIMAL(6,2) NOT NULL,  -- Effect size in percentage points
    confidence VARCHAR(10) NOT NULL,       -- HIGH, MEDIUM, LOW
    baseline_win_rate DECIMAL(5,2),        -- Baseline win rate for comparison
    edge_win_rate DECIMAL(5,2),            -- Win rate when edge condition met
    favorable_condition TEXT,              -- e.g., "Range >= 0.15%"
    unfavorable_condition TEXT,            -- e.g., "Range < 0.12%"
    recommendation TEXT,                   -- Action recommendation
    sample_size INTEGER,                   -- Number of trades in test
    validation_date DATE,                  -- When this edge was validated
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_indicator_segment UNIQUE(indicator, segment, test_name)
);

-- Indexes for filtering
CREATE INDEX IF NOT EXISTS idx_ai_indicator_edges_indicator ON ai_indicator_edges(indicator);
CREATE INDEX IF NOT EXISTS idx_ai_indicator_edges_has_edge ON ai_indicator_edges(has_edge);
CREATE INDEX IF NOT EXISTS idx_ai_indicator_edges_segment ON ai_indicator_edges(segment);

COMMENT ON TABLE ai_indicator_edges IS 'Validated indicator edges from statistical testing (CALC-011 framework)';
COMMENT ON COLUMN ai_indicator_edges.effect_size_pp IS 'Effect size in percentage points (pp) - win rate difference from baseline';
COMMENT ON COLUMN ai_indicator_edges.confidence IS 'Confidence level based on sample size: HIGH (>=100), MEDIUM (>=30), LOW (<30)';


-- =============================================================================
-- Table 3: ai_zone_performance
-- Win rates by zone type, score bucket, and direction
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_zone_performance (
    id SERIAL PRIMARY KEY,
    zone_type VARCHAR(20) NOT NULL,        -- primary, secondary
    score_bucket VARCHAR(20) NOT NULL,     -- low (0-4), mid (5-8), high (9+)
    direction VARCHAR(10) NOT NULL,        -- LONG, SHORT
    total_trades INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    win_rate DECIMAL(5,2) NOT NULL DEFAULT 0,
    avg_r_achieved DECIMAL(5,2),           -- Average R-multiple achieved
    avg_bounce_pct DECIMAL(5,2),           -- Average bounce from zone
    date_from DATE NOT NULL,               -- Start of data range
    date_to DATE NOT NULL,                 -- End of data range
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_zone_score_direction UNIQUE(zone_type, score_bucket, direction)
);

-- Indexes for filtering
CREATE INDEX IF NOT EXISTS idx_ai_zone_perf_type ON ai_zone_performance(zone_type);
CREATE INDEX IF NOT EXISTS idx_ai_zone_perf_direction ON ai_zone_performance(direction);

COMMENT ON TABLE ai_zone_performance IS 'Historical zone performance by type, score bucket, and direction';
COMMENT ON COLUMN ai_zone_performance.score_bucket IS 'Zone score grouping: low (0-4), mid (5-8), high (9+) based on confluence score';


-- =============================================================================
-- Verification queries (run after creation)
-- =============================================================================
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public' AND table_name LIKE 'ai_%';
--
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'ai_model_stats';

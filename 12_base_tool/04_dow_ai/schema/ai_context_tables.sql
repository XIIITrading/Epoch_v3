-- ============================================================================
-- EPOCH DOW AI CONTEXT TABLES
-- Purpose: Store aggregated data for AI prompt enhancement
-- Created: January 20, 2026
-- ============================================================================

-- ============================================================================
-- TABLE 1: ai_model_stats
-- Purpose: Aggregated performance metrics by EPCH model
-- Updated: Weekly (after backtest completion)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ai_model_stats (
    model VARCHAR(10) PRIMARY KEY,          -- EPCH1, EPCH2, EPCH3, EPCH4

    -- Core Performance Metrics
    total_trades INTEGER NOT NULL DEFAULT 0,
    win_rate DECIMAL(5,2),                  -- Percentage (0-100)
    avg_mfe_r DECIMAL(5,2),                 -- Average max favorable excursion in R
    avg_mae_r DECIMAL(5,2),                 -- Average max adverse excursion in R
    avg_pnl_r DECIMAL(5,2),                 -- Average P&L in R

    -- Time Metrics
    avg_time_to_mfe_minutes INTEGER,        -- Minutes from entry to MFE
    avg_time_to_target_minutes INTEGER,     -- Minutes from entry to target
    avg_hold_duration_minutes INTEGER,      -- Average trade duration

    -- Stop Analysis
    best_stop_type VARCHAR(20),             -- zone_buffer, prior_m1, prior_m5, etc.
    best_stop_win_rate DECIMAL(5,2),        -- Win rate with best stop type

    -- Health Score Correlation
    avg_health_score_winners DECIMAL(3,1),  -- Average health for winning trades
    avg_health_score_losers DECIMAL(3,1),   -- Average health for losing trades
    health_score_threshold DECIMAL(3,1),    -- Recommended minimum health score

    -- Direction Breakdown
    long_win_rate DECIMAL(5,2),
    short_win_rate DECIMAL(5,2),
    long_trade_count INTEGER,
    short_trade_count INTEGER,

    -- Metadata
    data_start_date DATE,
    data_end_date DATE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE ai_model_stats IS 'Aggregated EPCH model performance for DOW AI prompts';

-- ============================================================================
-- TABLE 2: ai_indicator_edges
-- Purpose: Validated indicator thresholds from weekly edge testing
-- Updated: Weekly (after indicator validation runs)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ai_indicator_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Indicator Identification
    indicator VARCHAR(50) NOT NULL,         -- e.g., candle_range, vol_delta, h1_structure
    direction VARCHAR(10) NOT NULL,         -- LONG, SHORT, ALL
    trade_type VARCHAR(15) NOT NULL,        -- CONTINUATION, REJECTION, ALL

    -- Edge Specification
    threshold_type VARCHAR(20),             -- gte, lte, eq, between, category
    threshold_value VARCHAR(100),           -- e.g., "0.15", "POSITIVE", "Q4-Q5"
    threshold_display VARCHAR(100),         -- Human readable: ">= 0.15%", "POSITIVE"

    -- Statistical Metrics
    baseline_win_rate DECIMAL(5,2),         -- Overall win rate without filter
    edge_win_rate DECIMAL(5,2),             -- Win rate with this edge applied
    effect_size_pp DECIMAL(5,2),            -- Percentage points improvement

    -- Validation Quality
    confidence VARCHAR(10),                 -- HIGH, MEDIUM, LOW
    p_value DECIMAL(10,8),                  -- Statistical significance
    sample_size INTEGER,                    -- Number of trades in sample

    -- Action Guidance
    action VARCHAR(20),                     -- PROCEED, SKIP, CONFIRM, CAUTION
    is_paradox BOOLEAN DEFAULT FALSE,       -- Counter-intuitive finding

    -- Documentation
    notes TEXT,
    validation_date DATE,
    source_file VARCHAR(255),               -- Path to edge test result

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint
    CONSTRAINT uq_indicator_edge UNIQUE (indicator, direction, trade_type, threshold_value)
);

COMMENT ON TABLE ai_indicator_edges IS 'Validated indicator edges from CALC-011 testing';

-- Create index for common queries
CREATE INDEX idx_indicator_edges_direction ON ai_indicator_edges(direction);
CREATE INDEX idx_indicator_edges_confidence ON ai_indicator_edges(confidence);
CREATE INDEX idx_indicator_edges_action ON ai_indicator_edges(action);

-- ============================================================================
-- TABLE 3: ai_zone_performance
-- Purpose: Historical zone performance by rank
-- Updated: Weekly or Monthly
-- ============================================================================

CREATE TABLE IF NOT EXISTS ai_zone_performance (
    zone_rank VARCHAR(5) PRIMARY KEY,       -- L1, L2, L3, L4, L5

    -- Core Metrics
    total_trades INTEGER NOT NULL DEFAULT 0,
    win_rate DECIMAL(5,2),
    avg_pnl_r DECIMAL(5,2),

    -- Zone Interaction
    avg_bounce_pct DECIMAL(5,2),            -- Average price bounce from zone
    avg_penetration_pct DECIMAL(5,2),       -- Average penetration into zone
    avg_retest_count DECIMAL(3,1),          -- Average number of zone tests

    -- Timing
    avg_hold_duration_minutes INTEGER,
    avg_time_to_target_minutes INTEGER,

    -- Score Range
    min_score DECIMAL(5,2),
    max_score DECIMAL(5,2),

    -- Quality Recommendation
    recommendation VARCHAR(50),             -- BEST, GOOD, MODERATE, LOW, WORST

    -- Metadata
    data_start_date DATE,
    data_end_date DATE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE ai_zone_performance IS 'Zone rank performance for quality assessment';

-- ============================================================================
-- TABLE 4: ai_recommendations
-- Purpose: Log all DOW AI recommendations for feedback loop
-- Updated: Real-time (after each analysis)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ai_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Trade Identification
    trade_id VARCHAR(50),                   -- NULL if trade not taken, linked to trades table if taken
    analysis_time TIMESTAMPTZ NOT NULL,

    -- Setup Details
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10) NOT NULL,         -- LONG, SHORT
    zone_type VARCHAR(15) NOT NULL,         -- PRIMARY, SECONDARY
    zone_rank VARCHAR(5),                   -- L1-L5
    model_code VARCHAR(10) NOT NULL,        -- EPCH_01, EPCH_02, EPCH_03, EPCH_04

    -- Current Indicators at Analysis
    current_price DECIMAL(12,4),
    health_score INTEGER,
    candle_range_pct DECIMAL(5,4),
    vol_delta_5bar DECIMAL(15,2),
    vol_roc_pct DECIMAL(8,2),
    cvd_slope VARCHAR(20),
    sma_config VARCHAR(20),
    h1_structure VARCHAR(20),

    -- Claude's Analysis
    confidence VARCHAR(10),                 -- HIGH, MEDIUM, LOW
    confidence_score DECIMAL(3,1),          -- Numeric 0-10
    recommendation VARCHAR(50),             -- TAKE_TRADE, WAIT_FOR_CONFIRMATION, SKIP
    entry_triggers TEXT,                    -- What Claude said to watch for
    invalidation_levels TEXT,               -- Where the setup fails
    full_response TEXT,                     -- Complete Claude response (for debugging)

    -- User Action
    user_action VARCHAR(20),                -- TAKEN, SKIPPED, MODIFIED
    user_notes TEXT,

    -- Outcome Tracking (Updated later)
    outcome VARCHAR(20),                    -- WIN, LOSS, BREAKEVEN, PENDING, NOT_TAKEN
    actual_pnl_r DECIMAL(5,2),
    exit_reason VARCHAR(30),
    outcome_updated_at TIMESTAMPTZ,

    -- Prompt Version Tracking
    prompt_version VARCHAR(20),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE ai_recommendations IS 'All DOW AI recommendations for feedback loop tracking';

-- Create indexes for common queries
CREATE INDEX idx_recommendations_ticker ON ai_recommendations(ticker);
CREATE INDEX idx_recommendations_date ON ai_recommendations(analysis_time);
CREATE INDEX idx_recommendations_model ON ai_recommendations(model_code);
CREATE INDEX idx_recommendations_outcome ON ai_recommendations(outcome);
CREATE INDEX idx_recommendations_confidence ON ai_recommendations(confidence);
CREATE INDEX idx_recommendations_trade_id ON ai_recommendations(trade_id);

-- ============================================================================
-- TABLE 5: ai_prompt_history
-- Purpose: Track prompt template versions and their effectiveness
-- Updated: When prompt templates are modified
-- ============================================================================

CREATE TABLE IF NOT EXISTS ai_prompt_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Version Identification
    prompt_version VARCHAR(20) NOT NULL,    -- e.g., "1.0.0", "1.1.0"
    prompt_type VARCHAR(20) NOT NULL,       -- entry, exit
    prompt_hash VARCHAR(64),                -- SHA256 hash of template for change detection

    -- Deployment Info
    deployed_at TIMESTAMPTZ NOT NULL,
    retired_at TIMESTAMPTZ,                 -- NULL if currently active
    is_active BOOLEAN DEFAULT TRUE,

    -- Performance Metrics (calculated from ai_recommendations)
    trades_analyzed INTEGER DEFAULT 0,
    trades_taken INTEGER DEFAULT 0,
    trades_won INTEGER DEFAULT 0,
    recommendation_accuracy DECIMAL(5,2),   -- % of HIGH confidence that were winners
    avg_confidence_score DECIMAL(3,1),

    -- Template Content
    template_changes TEXT,                  -- Description of what changed

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_prompt_version UNIQUE (prompt_version, prompt_type)
);

COMMENT ON TABLE ai_prompt_history IS 'Prompt template version tracking for A/B testing';

-- ============================================================================
-- VIEW: v_ai_context_summary
-- Purpose: Quick overview of AI context data for monitoring
-- ============================================================================

CREATE OR REPLACE VIEW v_ai_context_summary AS
SELECT
    'Model Stats' as category,
    COUNT(*) as record_count,
    MAX(updated_at) as last_updated
FROM ai_model_stats
UNION ALL
SELECT
    'Indicator Edges' as category,
    COUNT(*) as record_count,
    MAX(updated_at) as last_updated
FROM ai_indicator_edges
UNION ALL
SELECT
    'Zone Performance' as category,
    COUNT(*) as record_count,
    MAX(updated_at) as last_updated
FROM ai_zone_performance
UNION ALL
SELECT
    'Recommendations' as category,
    COUNT(*) as record_count,
    MAX(created_at) as last_updated
FROM ai_recommendations
UNION ALL
SELECT
    'Prompt History' as category,
    COUNT(*) as record_count,
    MAX(created_at) as last_updated
FROM ai_prompt_history;

-- ============================================================================
-- VIEW: v_recommendation_accuracy
-- Purpose: Calculate recommendation accuracy by model and confidence
-- ============================================================================

CREATE OR REPLACE VIEW v_recommendation_accuracy AS
SELECT
    model_code,
    confidence,
    COUNT(*) as total_recommendations,
    COUNT(CASE WHEN user_action = 'TAKEN' THEN 1 END) as trades_taken,
    COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
    COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
    ROUND(
        COUNT(CASE WHEN outcome = 'WIN' THEN 1 END)::DECIMAL /
        NULLIF(COUNT(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 END), 0) * 100,
        2
    ) as win_rate_pct,
    ROUND(
        COUNT(CASE WHEN user_action = 'TAKEN' THEN 1 END)::DECIMAL /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) as take_rate_pct
FROM ai_recommendations
WHERE outcome IS NOT NULL AND outcome != 'PENDING'
GROUP BY model_code, confidence
ORDER BY model_code,
    CASE confidence WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 WHEN 'LOW' THEN 3 END;

-- ============================================================================
-- FUNCTION: update_recommendation_outcome
-- Purpose: Update recommendation with trade outcome
-- ============================================================================

CREATE OR REPLACE FUNCTION update_recommendation_outcome(
    p_recommendation_id UUID,
    p_trade_id VARCHAR,
    p_outcome VARCHAR,
    p_actual_pnl_r DECIMAL,
    p_exit_reason VARCHAR
)
RETURNS VOID AS $$
BEGIN
    UPDATE ai_recommendations
    SET
        trade_id = p_trade_id,
        outcome = p_outcome,
        actual_pnl_r = p_actual_pnl_r,
        exit_reason = p_exit_reason,
        outcome_updated_at = NOW(),
        updated_at = NOW()
    WHERE id = p_recommendation_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNCTION: get_model_context
-- Purpose: Get aggregated model context for prompt injection
-- ============================================================================

CREATE OR REPLACE FUNCTION get_model_context(p_model VARCHAR)
RETURNS TABLE (
    model VARCHAR,
    total_trades INTEGER,
    win_rate DECIMAL,
    avg_mfe_r DECIMAL,
    avg_mae_r DECIMAL,
    avg_time_to_mfe_minutes INTEGER,
    best_stop_type VARCHAR,
    best_stop_win_rate DECIMAL,
    health_score_threshold DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ms.model,
        ms.total_trades,
        ms.win_rate,
        ms.avg_mfe_r,
        ms.avg_mae_r,
        ms.avg_time_to_mfe_minutes,
        ms.best_stop_type,
        ms.best_stop_win_rate,
        ms.health_score_threshold
    FROM ai_model_stats ms
    WHERE ms.model = p_model;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNCTION: get_indicator_edges
-- Purpose: Get relevant indicator edges for a direction/trade type
-- ============================================================================

CREATE OR REPLACE FUNCTION get_indicator_edges(
    p_direction VARCHAR,
    p_trade_type VARCHAR DEFAULT 'ALL'
)
RETURNS TABLE (
    indicator VARCHAR,
    threshold_display VARCHAR,
    edge_win_rate DECIMAL,
    effect_size_pp DECIMAL,
    action VARCHAR,
    is_paradox BOOLEAN,
    notes TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ie.indicator,
        ie.threshold_display,
        ie.edge_win_rate,
        ie.effect_size_pp,
        ie.action,
        ie.is_paradox,
        ie.notes
    FROM ai_indicator_edges ie
    WHERE ie.confidence = 'HIGH'
      AND (ie.direction = p_direction OR ie.direction = 'ALL')
      AND (ie.trade_type = p_trade_type OR ie.trade_type = 'ALL')
    ORDER BY ie.effect_size_pp DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGER: Auto-update updated_at timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_model_stats_updated
    BEFORE UPDATE ON ai_model_stats
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_indicator_edges_updated
    BEFORE UPDATE ON ai_indicator_edges
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_zone_performance_updated
    BEFORE UPDATE ON ai_zone_performance
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_recommendations_updated
    BEFORE UPDATE ON ai_recommendations
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_prompt_history_updated
    BEFORE UPDATE ON ai_prompt_history
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ============================================================================
-- INITIAL DATA: Zone Performance (based on historical analysis)
-- ============================================================================

INSERT INTO ai_zone_performance (zone_rank, total_trades, win_rate, recommendation, min_score, max_score)
VALUES
    ('L5', 0, 55.0, 'BEST - High priority', 12.0, 999.0),
    ('L4', 0, 50.0, 'GOOD - Standard entry', 9.0, 11.99),
    ('L3', 0, 45.0, 'MODERATE - Needs confirmation', 6.0, 8.99),
    ('L2', 0, 40.0, 'LOW - Extra caution', 3.0, 5.99),
    ('L1', 0, 35.0, 'WORST - Often skip', 0.0, 2.99)
ON CONFLICT (zone_rank) DO NOTHING;

-- ============================================================================
-- GRANT PERMISSIONS (adjust as needed for your setup)
-- ============================================================================

-- Grant access to authenticated users (Supabase default role)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO authenticated;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

COMMENT ON SCHEMA public IS 'Epoch DOW AI Context Tables - Version 1.0';

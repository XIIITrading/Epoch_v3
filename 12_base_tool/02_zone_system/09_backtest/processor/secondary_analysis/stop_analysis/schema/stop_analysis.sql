-- ============================================================================
-- Epoch Trading System - Table: stop_analysis
-- Stop Type Analysis (CALC-009) - Trade Outcomes by Stop Type
-- XIII Trading LLC
--
-- PURPOSE:
--   Stores calculated stop prices and simulated outcomes for 6 different
--   stop placement methods. This is the foundation for determining which
--   stop type provides the best risk-adjusted returns.
--
-- STOP TYPES:
--   1. zone_buffer  - Zone Boundary + 5% Buffer (Default)
--   2. prior_m1     - Prior M1 Bar High/Low (Tightest)
--   3. prior_m5     - Prior M5 Bar High/Low
--   4. m5_atr       - M5 ATR (1.1x), Close-based
--   5. m15_atr      - M15 ATR (1.1x), Close-based
--   6. fractal      - M5 Fractal High/Low (Market Structure)
--
-- DATA SOURCES:
--   - Trade metadata: trades table
--   - MFE/MAE potential: mfe_mae_potential table
--   - M1 bars: m1_bars table
--   - M5 bars: m5_trade_bars table
--
-- Version: 1.0.0
-- ============================================================================

CREATE TABLE IF NOT EXISTS stop_analysis (
    -- =========================================================================
    -- COMPOSITE PRIMARY KEY
    -- =========================================================================
    id SERIAL,
    trade_id VARCHAR(50) NOT NULL,
    stop_type VARCHAR(20) NOT NULL,  -- zone_buffer, prior_m1, prior_m5, m5_atr, m15_atr, fractal

    PRIMARY KEY (trade_id, stop_type),

    -- =========================================================================
    -- TRADE IDENTIFICATION (copied from trades for query convenience)
    -- =========================================================================
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10) NOT NULL,  -- LONG, SHORT
    model VARCHAR(10),  -- EPCH01, EPCH02, EPCH03, EPCH04

    -- =========================================================================
    -- ENTRY REFERENCE
    -- =========================================================================
    entry_time TIME NOT NULL,
    entry_price DECIMAL(12, 4) NOT NULL,
    zone_low DECIMAL(12, 4),
    zone_high DECIMAL(12, 4),

    -- =========================================================================
    -- STOP CALCULATION RESULTS
    -- =========================================================================
    stop_price DECIMAL(12, 4),  -- Calculated stop price for this stop type
    stop_distance DECIMAL(12, 4),  -- abs(entry_price - stop_price)
    stop_distance_pct DECIMAL(8, 4),  -- (stop_distance / entry_price) * 100

    -- =========================================================================
    -- OUTCOME SIMULATION RESULTS
    -- =========================================================================
    stop_hit BOOLEAN,  -- Was stop triggered?
    stop_hit_time TIME,  -- When was stop triggered?

    -- MFE data (from mfe_mae_potential)
    mfe_price DECIMAL(12, 4),  -- Maximum favorable price
    mfe_time TIME,  -- Time of MFE
    mfe_distance DECIMAL(12, 4),  -- Distance from entry to MFE

    -- R calculation
    r_achieved DECIMAL(10, 4),  -- R-multiple achieved (MFE/stop_distance or -1 if stopped)

    -- Outcome classification
    outcome VARCHAR(10),  -- WIN (R >= 1), LOSS (stopped), PARTIAL (0 < R < 1)

    -- =========================================================================
    -- TRIGGER TYPE METADATA
    -- =========================================================================
    trigger_type VARCHAR(20),  -- 'price_based' or 'close_based'
    -- Price-based: zone_buffer, prior_m1, prior_m5, fractal (triggers on price touch)
    -- Close-based: m5_atr, m15_atr (triggers only on bar close)

    -- =========================================================================
    -- SYSTEM METADATA
    -- =========================================================================
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- =========================================================================
    -- CONSTRAINTS
    -- =========================================================================
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE,

    CONSTRAINT valid_stop_type CHECK (stop_type IN (
        'zone_buffer', 'prior_m1', 'prior_m5', 'm5_atr', 'm15_atr', 'fractal'
    )),
    CONSTRAINT valid_outcome CHECK (outcome IS NULL OR outcome IN ('WIN', 'LOSS', 'PARTIAL')),
    CONSTRAINT valid_trigger_type CHECK (trigger_type IS NULL OR trigger_type IN ('price_based', 'close_based'))
);

-- ============================================================================
-- INDEXES
-- ============================================================================
-- Primary lookups
CREATE INDEX IF NOT EXISTS idx_sa_trade_id ON stop_analysis(trade_id);
CREATE INDEX IF NOT EXISTS idx_sa_stop_type ON stop_analysis(stop_type);
CREATE INDEX IF NOT EXISTS idx_sa_date ON stop_analysis(date DESC);
CREATE INDEX IF NOT EXISTS idx_sa_ticker ON stop_analysis(ticker);
CREATE INDEX IF NOT EXISTS idx_sa_model ON stop_analysis(model);
CREATE INDEX IF NOT EXISTS idx_sa_direction ON stop_analysis(direction);
CREATE INDEX IF NOT EXISTS idx_sa_outcome ON stop_analysis(outcome);

-- Composite indexes for analysis
CREATE INDEX IF NOT EXISTS idx_sa_stop_type_outcome ON stop_analysis(stop_type, outcome);
CREATE INDEX IF NOT EXISTS idx_sa_stop_type_model ON stop_analysis(stop_type, model);
CREATE INDEX IF NOT EXISTS idx_sa_stop_type_direction ON stop_analysis(stop_type, direction);
CREATE INDEX IF NOT EXISTS idx_sa_model_direction ON stop_analysis(model, direction);
CREATE INDEX IF NOT EXISTS idx_sa_date_stop_type ON stop_analysis(date, stop_type);

-- R-multiple queries
CREATE INDEX IF NOT EXISTS idx_sa_r_achieved ON stop_analysis(r_achieved);
CREATE INDEX IF NOT EXISTS idx_sa_stop_distance_pct ON stop_analysis(stop_distance_pct);

-- ============================================================================
-- UPDATE TRIGGER
-- ============================================================================
DROP TRIGGER IF EXISTS update_stop_analysis_updated_at ON stop_analysis;
CREATE TRIGGER update_stop_analysis_updated_at
    BEFORE UPDATE ON stop_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE stop_analysis IS 'Stop type analysis: calculates 6 stop types per trade and simulates outcomes. Foundation for CALC-009.';
COMMENT ON COLUMN stop_analysis.stop_type IS 'Stop method: zone_buffer, prior_m1, prior_m5, m5_atr, m15_atr, fractal';
COMMENT ON COLUMN stop_analysis.stop_price IS 'Calculated stop price for this stop type';
COMMENT ON COLUMN stop_analysis.stop_distance IS 'Dollar distance from entry to stop (1R unit)';
COMMENT ON COLUMN stop_analysis.stop_distance_pct IS 'Stop distance as percentage of entry price';
COMMENT ON COLUMN stop_analysis.stop_hit IS 'Whether the stop was triggered during the trade';
COMMENT ON COLUMN stop_analysis.r_achieved IS 'R-multiple achieved: MFE/stop_distance for non-stopped, -1 for stopped before MFE';
COMMENT ON COLUMN stop_analysis.outcome IS 'WIN (R>=1), LOSS (stopped), PARTIAL (0<R<1)';
COMMENT ON COLUMN stop_analysis.trigger_type IS 'price_based (triggers on touch) or close_based (triggers on bar close)';

-- ============================================================================
-- ANALYSIS VIEWS
-- ============================================================================

-- Summary by stop type
CREATE OR REPLACE VIEW v_stop_analysis_summary AS
SELECT
    stop_type,
    COUNT(*) as total_trades,
    COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
    COUNT(*) FILTER (WHERE outcome = 'LOSS') as losses,
    COUNT(*) FILTER (WHERE outcome = 'PARTIAL') as partials,
    ROUND(100.0 * COUNT(*) FILTER (WHERE outcome = 'WIN') / NULLIF(COUNT(*), 0), 2) as win_rate_pct,
    ROUND(AVG(stop_distance_pct), 2) as avg_stop_pct,
    ROUND(AVG(r_achieved) FILTER (WHERE outcome = 'WIN'), 2) as avg_r_winners,
    ROUND(AVG(r_achieved), 2) as avg_r_all,
    -- Expectancy = (win_rate * avg_r_winners) - (loss_rate * 1.0)
    ROUND(
        (COUNT(*) FILTER (WHERE outcome = 'WIN')::decimal / NULLIF(COUNT(*), 0) *
         COALESCE(AVG(r_achieved) FILTER (WHERE outcome = 'WIN'), 0)) -
        (COUNT(*) FILTER (WHERE outcome = 'LOSS')::decimal / NULLIF(COUNT(*), 0) * 1.0),
        3
    ) as expectancy
FROM stop_analysis
WHERE stop_price IS NOT NULL
GROUP BY stop_type
ORDER BY expectancy DESC;

-- Summary by stop type and model
CREATE OR REPLACE VIEW v_stop_analysis_by_model AS
SELECT
    stop_type,
    model,
    COUNT(*) as total_trades,
    ROUND(100.0 * COUNT(*) FILTER (WHERE outcome = 'WIN') / NULLIF(COUNT(*), 0), 2) as win_rate_pct,
    ROUND(AVG(stop_distance_pct), 2) as avg_stop_pct,
    ROUND(AVG(r_achieved) FILTER (WHERE outcome = 'WIN'), 2) as avg_r_winners,
    ROUND(
        (COUNT(*) FILTER (WHERE outcome = 'WIN')::decimal / NULLIF(COUNT(*), 0) *
         COALESCE(AVG(r_achieved) FILTER (WHERE outcome = 'WIN'), 0)) -
        (COUNT(*) FILTER (WHERE outcome = 'LOSS')::decimal / NULLIF(COUNT(*), 0) * 1.0),
        3
    ) as expectancy
FROM stop_analysis
WHERE stop_price IS NOT NULL
GROUP BY stop_type, model
ORDER BY stop_type, model;

-- Summary by stop type and direction
CREATE OR REPLACE VIEW v_stop_analysis_by_direction AS
SELECT
    stop_type,
    direction,
    COUNT(*) as total_trades,
    ROUND(100.0 * COUNT(*) FILTER (WHERE outcome = 'WIN') / NULLIF(COUNT(*), 0), 2) as win_rate_pct,
    ROUND(AVG(stop_distance_pct), 2) as avg_stop_pct,
    ROUND(AVG(r_achieved) FILTER (WHERE outcome = 'WIN'), 2) as avg_r_winners,
    ROUND(
        (COUNT(*) FILTER (WHERE outcome = 'WIN')::decimal / NULLIF(COUNT(*), 0) *
         COALESCE(AVG(r_achieved) FILTER (WHERE outcome = 'WIN'), 0)) -
        (COUNT(*) FILTER (WHERE outcome = 'LOSS')::decimal / NULLIF(COUNT(*), 0) * 1.0),
        3
    ) as expectancy
FROM stop_analysis
WHERE stop_price IS NOT NULL
GROUP BY stop_type, direction
ORDER BY stop_type, direction;

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================
/*

-- 1. Compare all stop types
SELECT * FROM v_stop_analysis_summary;

-- 2. Find best stop type by expectancy
SELECT
    stop_type,
    total_trades,
    win_rate_pct,
    avg_stop_pct,
    expectancy
FROM v_stop_analysis_summary
ORDER BY expectancy DESC
LIMIT 1;

-- 3. Compare stop types for a specific model
SELECT * FROM v_stop_analysis_by_model
WHERE model = 'EPCH01'
ORDER BY expectancy DESC;

-- 4. Compare performance by direction
SELECT * FROM v_stop_analysis_by_direction
ORDER BY stop_type, direction;

-- 5. Detailed trade-level analysis for zone_buffer stop
SELECT
    trade_id,
    ticker,
    date,
    model,
    direction,
    entry_price,
    stop_price,
    stop_distance_pct,
    stop_hit,
    r_achieved,
    outcome
FROM stop_analysis
WHERE stop_type = 'zone_buffer'
ORDER BY date DESC, entry_time DESC
LIMIT 50;

-- 6. Find trades where fractal stop would have been better than zone_buffer
SELECT
    z.trade_id,
    z.ticker,
    z.date,
    z.outcome as zone_outcome,
    z.r_achieved as zone_r,
    f.outcome as fractal_outcome,
    f.r_achieved as fractal_r,
    f.r_achieved - z.r_achieved as r_improvement
FROM stop_analysis z
JOIN stop_analysis f ON z.trade_id = f.trade_id
WHERE z.stop_type = 'zone_buffer'
  AND f.stop_type = 'fractal'
  AND f.r_achieved > z.r_achieved
ORDER BY r_improvement DESC
LIMIT 20;

*/

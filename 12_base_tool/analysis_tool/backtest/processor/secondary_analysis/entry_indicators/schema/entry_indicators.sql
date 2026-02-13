-- ============================================================================
-- EPOCH TRADING SYSTEM - TABLE: entry_indicators
-- Entry Indicator Snapshots for Trade Analysis
-- XIII Trading LLC
--
-- PURPOSE:
--   Stores indicator snapshots calculated at the M1 bar prior to trade entry.
--   Provides the data foundation for CALC-005 through CALC-008 (Indicator Analysis).
--
-- DATA SOURCE:
--   - Trade metadata: mfe_mae_potential table
--   - M1 bars: m1_bars table (or Polygon API fallback)
--   - HTF bars: Polygon API for structure detection
--
-- CALCULATION METHODOLOGY:
--   For each trade, find the last complete M1 bar before entry_time.
--   Aggregate M1 bars to M5 for indicator calculations.
--   Use HTF bars (M15, H1, H4) for structure detection.
--
-- Version: 1.0.0
-- ============================================================================

CREATE TABLE IF NOT EXISTS entry_indicators (
    -- =========================================================================
    -- PRIMARY KEY & FOREIGN KEY
    -- =========================================================================
    trade_id VARCHAR(50) NOT NULL,

    -- =========================================================================
    -- TRADE CONTEXT (denormalized for query performance)
    -- =========================================================================
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    model VARCHAR(10) NULL,
    entry_time TIME WITHOUT TIME ZONE NOT NULL,
    entry_price NUMERIC(12, 4) NOT NULL,

    -- =========================================================================
    -- INDICATOR BAR REFERENCE
    -- =========================================================================
    indicator_bar_time TIME WITHOUT TIME ZONE NULL,
    indicator_methodology VARCHAR(20) DEFAULT 'M1_PRIOR',

    -- =========================================================================
    -- STRUCTURE FACTORS (4 points possible)
    -- =========================================================================
    h4_structure VARCHAR(10) NULL,
    h4_structure_healthy BOOLEAN NULL,
    h1_structure VARCHAR(10) NULL,
    h1_structure_healthy BOOLEAN NULL,
    m15_structure VARCHAR(10) NULL,
    m15_structure_healthy BOOLEAN NULL,
    m5_structure VARCHAR(10) NULL,
    m5_structure_healthy BOOLEAN NULL,

    -- =========================================================================
    -- VOLUME FACTORS (3 points possible)
    -- =========================================================================
    vol_roc NUMERIC(10, 4) NULL,
    vol_roc_healthy BOOLEAN NULL,
    vol_delta NUMERIC(12, 2) NULL,
    vol_delta_healthy BOOLEAN NULL,
    cvd_slope NUMERIC(10, 6) NULL,
    cvd_slope_healthy BOOLEAN NULL,

    -- =========================================================================
    -- PRICE/SMA FACTORS (3 points possible)
    -- =========================================================================
    sma9 NUMERIC(12, 4) NULL,
    sma21 NUMERIC(12, 4) NULL,
    sma_spread NUMERIC(12, 4) NULL,
    sma_alignment VARCHAR(10) NULL,
    sma_alignment_healthy BOOLEAN NULL,
    sma_momentum NUMERIC(10, 6) NULL,
    sma_momentum_label VARCHAR(15) NULL,
    sma_momentum_healthy BOOLEAN NULL,
    vwap NUMERIC(12, 4) NULL,
    vwap_position VARCHAR(10) NULL,
    vwap_healthy BOOLEAN NULL,

    -- =========================================================================
    -- COMPOSITE HEALTH SCORE
    -- =========================================================================
    health_score INTEGER NULL,
    health_label VARCHAR(15) NULL,

    -- =========================================================================
    -- FACTOR GROUP SUMMARIES
    -- =========================================================================
    structure_score INTEGER NULL,
    volume_score INTEGER NULL,
    price_score INTEGER NULL,

    -- =========================================================================
    -- METADATA
    -- =========================================================================
    bars_used INTEGER NULL,
    calculation_version VARCHAR(10) NULL DEFAULT '1.0',
    calculated_at TIMESTAMPTZ NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL DEFAULT NOW(),

    -- =========================================================================
    -- CONSTRAINTS
    -- =========================================================================
    CONSTRAINT entry_indicators_pkey PRIMARY KEY (trade_id),
    CONSTRAINT entry_indicators_trade_id_fkey FOREIGN KEY (trade_id)
        REFERENCES trades (trade_id) ON DELETE CASCADE
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Standard filters
CREATE INDEX IF NOT EXISTS idx_ei_date ON entry_indicators (date DESC);
CREATE INDEX IF NOT EXISTS idx_ei_ticker ON entry_indicators (ticker);
CREATE INDEX IF NOT EXISTS idx_ei_model ON entry_indicators (model);
CREATE INDEX IF NOT EXISTS idx_ei_direction ON entry_indicators (direction);
CREATE INDEX IF NOT EXISTS idx_ei_health_score ON entry_indicators (health_score);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_ei_ticker_date ON entry_indicators (ticker, date DESC);
CREATE INDEX IF NOT EXISTS idx_ei_model_direction ON entry_indicators (model, direction);
CREATE INDEX IF NOT EXISTS idx_ei_date_model ON entry_indicators (date, model);
CREATE INDEX IF NOT EXISTS idx_ei_model_health ON entry_indicators (model, health_score);
CREATE INDEX IF NOT EXISTS idx_ei_direction_health ON entry_indicators (direction, health_score);

-- Factor group indexes
CREATE INDEX IF NOT EXISTS idx_ei_structure_score ON entry_indicators (structure_score);
CREATE INDEX IF NOT EXISTS idx_ei_volume_score ON entry_indicators (volume_score);
CREATE INDEX IF NOT EXISTS idx_ei_price_score ON entry_indicators (price_score);

-- ============================================================================
-- UPDATE TRIGGER
-- ============================================================================
DROP TRIGGER IF EXISTS update_entry_indicators_updated_at ON entry_indicators;
CREATE TRIGGER update_entry_indicators_updated_at
    BEFORE UPDATE ON entry_indicators
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE entry_indicators IS 'Indicator snapshots at trade entry for CALC-005 through CALC-008 analysis';
COMMENT ON COLUMN entry_indicators.indicator_bar_time IS 'Time of the M1 bar used for indicator calculation (bar before entry)';
COMMENT ON COLUMN entry_indicators.indicator_methodology IS 'Method used: M1_PRIOR = last complete M1 bar before entry';
COMMENT ON COLUMN entry_indicators.health_score IS 'Composite score 0-10 based on all 10 factors';
COMMENT ON COLUMN entry_indicators.structure_score IS 'Sum of healthy structure factors (0-4)';
COMMENT ON COLUMN entry_indicators.volume_score IS 'Sum of healthy volume factors (0-3)';
COMMENT ON COLUMN entry_indicators.price_score IS 'Sum of healthy price/SMA factors (0-3)';

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================
/*

-- 1. Health score distribution by model
SELECT
    model,
    health_label,
    COUNT(*) as trades,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY model), 1) as pct
FROM entry_indicators
GROUP BY model, health_label
ORDER BY model, health_score DESC;

-- 2. Win rate by health score bucket
SELECT
    ei.health_label,
    COUNT(*) as trades,
    SUM(CASE WHEN mp.is_winner THEN 1 ELSE 0 END) as wins,
    ROUND(SUM(CASE WHEN mp.is_winner THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
FROM entry_indicators ei
JOIN mfe_mae_potential mp ON ei.trade_id = mp.trade_id
GROUP BY ei.health_label
ORDER BY MIN(ei.health_score);

-- 3. Factor importance (which factors correlate with wins)
SELECT
    'vol_roc_healthy' as factor,
    vol_roc_healthy as healthy,
    COUNT(*) as trades,
    ROUND(AVG(CASE WHEN mp.is_winner THEN 1.0 ELSE 0.0 END) * 100, 1) as win_rate
FROM entry_indicators ei
JOIN mfe_mae_potential mp ON ei.trade_id = mp.trade_id
WHERE vol_roc_healthy IS NOT NULL
GROUP BY vol_roc_healthy

UNION ALL

SELECT
    'sma_alignment_healthy' as factor,
    sma_alignment_healthy as healthy,
    COUNT(*) as trades,
    ROUND(AVG(CASE WHEN mp.is_winner THEN 1.0 ELSE 0.0 END) * 100, 1) as win_rate
FROM entry_indicators ei
JOIN mfe_mae_potential mp ON ei.trade_id = mp.trade_id
WHERE sma_alignment_healthy IS NOT NULL
GROUP BY sma_alignment_healthy

ORDER BY factor, healthy;

-- 4. Structure alignment by model
SELECT
    model,
    h4_structure,
    h1_structure,
    m15_structure,
    m5_structure,
    COUNT(*) as trades
FROM entry_indicators
WHERE h4_structure IS NOT NULL
GROUP BY model, h4_structure, h1_structure, m15_structure, m5_structure
ORDER BY model, trades DESC;

*/

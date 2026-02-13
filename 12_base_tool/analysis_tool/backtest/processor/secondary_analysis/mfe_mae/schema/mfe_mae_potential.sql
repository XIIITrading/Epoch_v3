-- ============================================================================
-- Epoch Trading System - Table: mfe_mae_potential
-- MFE/MAE Potential Analysis (Entry to End-of-Day)
-- XIII Trading LLC
--
-- PURPOSE:
--   Stores POTENTIAL MFE/MAE calculations measuring from entry time to 15:30 ET.
--   This supplements the REALIZED MFE/MAE (entry to exit) stored in optimal_trade.
--
--   Realized MFE/MAE (optimal_trade): "What happened during the trade?"
--   Potential MFE/MAE (this table):   "What was possible in the market?"
--
-- DATA SOURCE:
--   - Trade metadata: Supabase `trades` table
--   - Price data: Polygon.io 1-minute bars
--
-- CALCULATION:
--   For each trade, fetches 1-min bars from entry_time to 15:30 ET and finds:
--   - MFE: Maximum favorable price movement (high for LONG, low for SHORT)
--   - MAE: Maximum adverse price movement (low for LONG, high for SHORT)
--   Both expressed as R-multiples using: (price - entry_price) / stop_distance
--
-- Version: 1.0.0
-- ============================================================================

CREATE TABLE IF NOT EXISTS mfe_mae_potential (
    -- =========================================================================
    -- PRIMARY KEY
    -- =========================================================================
    trade_id VARCHAR(50) PRIMARY KEY,  -- References trades.trade_id

    -- =========================================================================
    -- TRADE IDENTIFICATION (copied from trades for query convenience)
    -- =========================================================================
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10) NOT NULL,  -- LONG, SHORT
    model VARCHAR(10),  -- EPCH1, EPCH2, EPCH3, EPCH4

    -- =========================================================================
    -- ENTRY REFERENCE (from trades table)
    -- =========================================================================
    entry_time TIME NOT NULL,
    entry_price DECIMAL(12, 4) NOT NULL,
    stop_price DECIMAL(12, 4) NOT NULL,
    stop_distance DECIMAL(12, 4) NOT NULL,  -- abs(entry_price - stop_price)

    -- =========================================================================
    -- POTENTIAL MFE (Maximum Favorable Excursion: Entry to 15:30)
    -- =========================================================================
    mfe_r_potential DECIMAL(10, 4),  -- MFE in R-multiples
    mfe_potential_price DECIMAL(12, 4),  -- Price at MFE
    mfe_potential_time TIME,  -- Time when MFE occurred

    -- =========================================================================
    -- POTENTIAL MAE (Maximum Adverse Excursion: Entry to 15:30)
    -- =========================================================================
    mae_r_potential DECIMAL(10, 4),  -- MAE in R-multiples (always positive)
    mae_potential_price DECIMAL(12, 4),  -- Price at MAE
    mae_potential_time TIME,  -- Time when MAE occurred

    -- =========================================================================
    -- CALCULATION METADATA
    -- =========================================================================
    bars_analyzed INTEGER,  -- Number of 1-min bars in calculation
    eod_cutoff TIME DEFAULT '15:30:00',  -- End of day cutoff used

    -- =========================================================================
    -- COMPARISON METRICS (for analysis convenience)
    -- =========================================================================
    -- These are populated if the corresponding trades data is available
    mfe_r_realized DECIMAL(10, 4),  -- Realized MFE (from optimal_trade, if available)
    mae_r_realized DECIMAL(10, 4),  -- Realized MAE (from optimal_trade, if available)
    pnl_r DECIMAL(10, 4),  -- Final P&L in R (from trades)
    is_winner BOOLEAN,  -- From trades.is_winner

    -- =========================================================================
    -- DERIVED METRICS
    -- =========================================================================
    -- Potential capture: How much of the potential was captured?
    -- mfe_capture_potential = pnl_r / mfe_r_potential (for winners)
    -- This shows if we're leaving money on the table

    -- =========================================================================
    -- SYSTEM METADATA
    -- =========================================================================
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- =========================================================================
    -- CONSTRAINTS
    -- =========================================================================
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
);

-- ============================================================================
-- INDEXES
-- ============================================================================
-- Primary lookups
CREATE INDEX IF NOT EXISTS idx_mmp_date ON mfe_mae_potential(date DESC);
CREATE INDEX IF NOT EXISTS idx_mmp_ticker ON mfe_mae_potential(ticker);
CREATE INDEX IF NOT EXISTS idx_mmp_model ON mfe_mae_potential(model);
CREATE INDEX IF NOT EXISTS idx_mmp_direction ON mfe_mae_potential(direction);
CREATE INDEX IF NOT EXISTS idx_mmp_winner ON mfe_mae_potential(is_winner);

-- Composite indexes for analysis
CREATE INDEX IF NOT EXISTS idx_mmp_ticker_date ON mfe_mae_potential(ticker, date DESC);
CREATE INDEX IF NOT EXISTS idx_mmp_model_winner ON mfe_mae_potential(model, is_winner);
CREATE INDEX IF NOT EXISTS idx_mmp_date_model ON mfe_mae_potential(date, model);

-- R-multiple range queries
CREATE INDEX IF NOT EXISTS idx_mmp_mfe_r ON mfe_mae_potential(mfe_r_potential);
CREATE INDEX IF NOT EXISTS idx_mmp_mae_r ON mfe_mae_potential(mae_r_potential);

-- ============================================================================
-- UPDATE TRIGGER
-- ============================================================================
DROP TRIGGER IF EXISTS update_mfe_mae_potential_updated_at ON mfe_mae_potential;
CREATE TRIGGER update_mfe_mae_potential_updated_at
    BEFORE UPDATE ON mfe_mae_potential
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE mfe_mae_potential IS 'Potential MFE/MAE from entry to EOD (15:30). Supplements realized MFE/MAE in optimal_trade.';
COMMENT ON COLUMN mfe_mae_potential.mfe_r_potential IS 'Maximum favorable excursion in R-multiples from entry to 15:30';
COMMENT ON COLUMN mfe_mae_potential.mae_r_potential IS 'Maximum adverse excursion in R-multiples from entry to 15:30 (always positive)';
COMMENT ON COLUMN mfe_mae_potential.mfe_potential_price IS 'The price level where MFE occurred';
COMMENT ON COLUMN mfe_mae_potential.mae_potential_price IS 'The price level where MAE occurred';
COMMENT ON COLUMN mfe_mae_potential.stop_distance IS 'Dollar distance from entry to stop, used as 1R unit';
COMMENT ON COLUMN mfe_mae_potential.bars_analyzed IS 'Number of 1-minute bars from entry_time to eod_cutoff';
COMMENT ON COLUMN mfe_mae_potential.mfe_r_realized IS 'Realized MFE (entry to exit) from optimal_trade for comparison';
COMMENT ON COLUMN mfe_mae_potential.mae_r_realized IS 'Realized MAE (entry to exit) from optimal_trade for comparison';

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================
/*

-- 1. Compare potential vs realized MFE by model
SELECT
    model,
    COUNT(*) as trades,
    ROUND(AVG(mfe_r_potential), 2) as avg_mfe_potential,
    ROUND(AVG(mfe_r_realized), 2) as avg_mfe_realized,
    ROUND(AVG(mfe_r_potential - COALESCE(mfe_r_realized, 0)), 2) as avg_missed_r
FROM mfe_mae_potential
WHERE mfe_r_potential IS NOT NULL
GROUP BY model
ORDER BY model;

-- 2. Find trades where we left significant money on the table
SELECT
    trade_id,
    ticker,
    date,
    model,
    pnl_r,
    mfe_r_potential,
    ROUND(mfe_r_potential - pnl_r, 2) as left_on_table
FROM mfe_mae_potential
WHERE is_winner = TRUE
  AND mfe_r_potential > pnl_r + 1.0  -- Left more than 1R on the table
ORDER BY (mfe_r_potential - pnl_r) DESC
LIMIT 20;

-- 3. Analyze exit timing effectiveness
SELECT
    model,
    is_winner,
    COUNT(*) as trades,
    ROUND(AVG(pnl_r / NULLIF(mfe_r_potential, 0)) * 100, 1) as pct_mfe_captured
FROM mfe_mae_potential
WHERE mfe_r_potential > 0
GROUP BY model, is_winner
ORDER BY model, is_winner DESC;

-- 4. Distribution of potential MFE
SELECT
    CASE
        WHEN mfe_r_potential < 1 THEN '< 1R'
        WHEN mfe_r_potential < 2 THEN '1-2R'
        WHEN mfe_r_potential < 3 THEN '2-3R'
        WHEN mfe_r_potential < 5 THEN '3-5R'
        ELSE '5R+'
    END as mfe_bucket,
    COUNT(*) as trades,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct
FROM mfe_mae_potential
WHERE mfe_r_potential IS NOT NULL
GROUP BY 1
ORDER BY MIN(mfe_r_potential);

*/

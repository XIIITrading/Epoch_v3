-- ============================================================================
-- Epoch Trading System - Table: optimal_trade (v2.0.0)
-- Points-Based 4-row analysis view per trade (ENTRY, MFE, MAE, EXIT)
-- XIII Trading LLC
-- ============================================================================
--
-- PURPOSE: Enables pattern discovery for optimal exit identification
-- Each row captures indicator state at a key moment in the trade lifecycle.
--
-- KEY CHANGES FROM V1:
--   - Win condition: mfe_time < mae_time (temporal, not P&L based)
--   - P&L in POINTS (absolute $) instead of R-multiples
--   - Exit is fixed at 15:30 ET
--   - MFE/MAE times from mfe_mae_potential table
--   - Indicators from m5_trade_bars table
--
-- ============================================================================

-- Drop existing table and recreate with new schema
DROP TABLE IF EXISTS optimal_trade CASCADE;

CREATE TABLE optimal_trade (
    -- =========================================================================
    -- PRIMARY KEY
    -- =========================================================================
    trade_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(10) NOT NULL,  -- ENTRY, MFE, MAE, EXIT

    -- =========================================================================
    -- TRADE IDENTIFICATION
    -- =========================================================================
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10) NOT NULL,   -- LONG, SHORT
    model VARCHAR(10),                -- EPCH1, EPCH2, EPCH3, EPCH4

    -- =========================================================================
    -- WIN CONDITION (temporal: mfe_time < mae_time)
    -- =========================================================================
    win INTEGER NOT NULL,  -- 1 if mfe_time < mae_time, else 0 (ties = loss)

    -- =========================================================================
    -- EVENT TIMING
    -- =========================================================================
    event_time TIME NOT NULL,
    bars_from_entry INTEGER NOT NULL,  -- M5 bars since entry (0 for ENTRY)

    -- =========================================================================
    -- PRICE DATA (Points-based, not R-multiples)
    -- =========================================================================
    entry_price DECIMAL(12,4) NOT NULL,      -- Entry price (same for all 4 events)
    price_at_event DECIMAL(12,4) NOT NULL,   -- Price at this event
    points_at_event DECIMAL(12,4) NOT NULL,  -- price_at_event - entry_price (direction adjusted)

    -- =========================================================================
    -- FINAL OUTCOME (on all events for convenience)
    -- =========================================================================
    actual_points DECIMAL(12,4) NOT NULL,    -- Points at EXIT (15:30 close)

    -- =========================================================================
    -- HEALTH METRICS (from m5_trade_bars)
    -- =========================================================================
    health_score INTEGER,              -- Health score (0-10)
    health_label VARCHAR(15),          -- CRITICAL, WEAK, MODERATE, STRONG
    health_delta INTEGER,              -- health_score - entry_health_score
    health_summary VARCHAR(15),        -- IMPROVING, DEGRADING, STABLE

    -- =========================================================================
    -- COMPONENT SCORES (from m5_trade_bars)
    -- =========================================================================
    structure_score INTEGER,
    volume_score INTEGER,
    price_score INTEGER,

    -- =========================================================================
    -- PRICE INDICATORS (from m5_trade_bars)
    -- =========================================================================
    vwap DECIMAL(12,4),
    sma9 DECIMAL(12,4),
    sma21 DECIMAL(12,4),
    sma_spread DECIMAL(12,4),          -- SMA9 - SMA21
    sma_momentum_ratio DECIMAL(10,6),
    sma_momentum_label VARCHAR(15),    -- WIDENING, NARROWING, FLAT

    -- =========================================================================
    -- VOLUME INDICATORS (from m5_trade_bars)
    -- =========================================================================
    vol_roc DECIMAL(10,4),             -- Volume ROC % vs 20-bar avg
    vol_delta DECIMAL(12,2),           -- Bar delta
    cvd_slope DECIMAL(10,6),           -- Normalized CVD slope

    -- =========================================================================
    -- STRUCTURE INDICATORS (from m5_trade_bars)
    -- =========================================================================
    m5_structure VARCHAR(10),          -- BULL, BEAR, NEUTRAL
    m15_structure VARCHAR(10),
    h1_structure VARCHAR(10),
    h4_structure VARCHAR(10),

    -- =========================================================================
    -- HEALTHY FLAGS (from m5_trade_bars)
    -- =========================================================================
    sma_alignment_healthy BOOLEAN,
    sma_momentum_healthy BOOLEAN,
    vwap_healthy BOOLEAN,
    vol_roc_healthy BOOLEAN,
    vol_delta_healthy BOOLEAN,
    cvd_slope_healthy BOOLEAN,
    m5_structure_healthy BOOLEAN,
    m15_structure_healthy BOOLEAN,
    h1_structure_healthy BOOLEAN,
    h4_structure_healthy BOOLEAN,

    -- =========================================================================
    -- METADATA
    -- =========================================================================
    calculated_at TIMESTAMPTZ DEFAULT NOW(),

    -- =========================================================================
    -- CONSTRAINTS
    -- =========================================================================
    PRIMARY KEY (trade_id, event_type),
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Primary lookups
CREATE INDEX idx_optimal_trade_trade_id ON optimal_trade(trade_id);
CREATE INDEX idx_optimal_trade_event_type ON optimal_trade(event_type);
CREATE INDEX idx_optimal_trade_date ON optimal_trade(date DESC);

-- Filtering
CREATE INDEX idx_optimal_trade_win ON optimal_trade(win);
CREATE INDEX idx_optimal_trade_ticker ON optimal_trade(ticker);
CREATE INDEX idx_optimal_trade_direction ON optimal_trade(direction);
CREATE INDEX idx_optimal_trade_model ON optimal_trade(model);
CREATE INDEX idx_optimal_trade_health ON optimal_trade(health_score);

-- Composite indexes for analysis queries
CREATE INDEX idx_optimal_trade_event_win ON optimal_trade(event_type, win);
CREATE INDEX idx_optimal_trade_ticker_date ON optimal_trade(ticker, date DESC);
CREATE INDEX idx_optimal_trade_model_win ON optimal_trade(model, win);

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE optimal_trade IS 'Points-based 4-row analysis view per trade (v2.0.0)';
COMMENT ON COLUMN optimal_trade.event_type IS 'Key event: ENTRY, MFE, MAE, EXIT';
COMMENT ON COLUMN optimal_trade.win IS '1 if mfe_time < mae_time, else 0 (temporal win condition)';
COMMENT ON COLUMN optimal_trade.points_at_event IS 'Absolute $ movement from entry (direction-adjusted)';
COMMENT ON COLUMN optimal_trade.actual_points IS 'Final points at 15:30 exit (same for all 4 rows)';
COMMENT ON COLUMN optimal_trade.health_delta IS 'health_score - entry_health_score';
COMMENT ON COLUMN optimal_trade.health_summary IS 'IMPROVING (delta >= 2), DEGRADING (delta <= -2), STABLE';

-- ============================================================================
-- Event Type Reference (v2.0.0)
-- ============================================================================
-- ENTRY - Trade entry moment
--         event_time = trades.entry_time
--         price_at_event = trades.entry_price
--         points_at_event = 0
--         Indicators from m5_trade_bars at floored M5 bar
--
-- MFE   - Maximum Favorable Excursion (entry to 15:30)
--         event_time = mfe_mae_potential.mfe_potential_time
--         price_at_event = mfe_mae_potential.mfe_potential_price
--         points_at_event = favorable movement in $
--         Indicators from m5_trade_bars at floored M5 bar
--
-- MAE   - Maximum Adverse Excursion (entry to 15:30)
--         event_time = mfe_mae_potential.mae_potential_time
--         price_at_event = mfe_mae_potential.mae_potential_price
--         points_at_event = adverse movement in $ (negative)
--         Indicators from m5_trade_bars at floored M5 bar
--
-- EXIT  - Fixed 15:30 ET exit
--         event_time = 15:30:00
--         price_at_event = close price of 15:30 bar
--         points_at_event = final P&L in $
--         Indicators from m5_trade_bars at 15:30 bar
-- ============================================================================

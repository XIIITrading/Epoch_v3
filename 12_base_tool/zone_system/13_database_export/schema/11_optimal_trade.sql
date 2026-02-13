-- ============================================================================
-- Epoch Trading System - Table 11: optimal_trade
-- Simplified 4-row analysis view per trade (ENTRY, MFE, MAE, EXIT).
-- Source: optimal_trade worksheet (v4.0.0: columns A-AB, 28 columns)
--
-- PURPOSE: Enables pattern discovery for optimal exit identification
-- Each row captures indicator state at a key moment in the trade lifecycle.
-- ============================================================================

CREATE TABLE IF NOT EXISTS optimal_trade (
    -- Composite Primary Key
    trade_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(10) NOT NULL,  -- ENTRY, MFE, MAE, EXIT

    -- =========================================================================
    -- COLUMNS A-F: TRADE IDENTIFICATION (6 columns)
    -- =========================================================================
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10),  -- LONG, SHORT
    model VARCHAR(10),  -- EPCH1, EPCH2, EPCH3, EPCH4
    win INTEGER,  -- 1=Win, 0=Loss

    -- =========================================================================
    -- COLUMNS G-K: EVENT IDENTIFICATION (5 columns)
    -- event_type is part of PK above
    -- =========================================================================
    event_time TIME,
    bars_from_entry INTEGER,  -- M5 bars since entry
    price_at_event DECIMAL(10, 2),
    r_at_event DECIMAL(10, 2),  -- R-multiple at this event

    -- =========================================================================
    -- COLUMNS L-N: HEALTH METRICS (3 columns)
    -- =========================================================================
    health_score INTEGER,  -- Health score (0-10)
    health_delta INTEGER,  -- Change from entry health
    health_summary VARCHAR(15),  -- IMPROVING, DEGRADING, STABLE

    -- =========================================================================
    -- COLUMNS O-R: INDICATOR VALUES (4 columns)
    -- =========================================================================
    vwap DECIMAL(10, 2),
    sma9 DECIMAL(10, 2),
    sma21 DECIMAL(10, 2),
    sma_spread DECIMAL(10, 4),  -- SMA9 - SMA21

    -- =========================================================================
    -- COLUMNS S-U: SMA & VOLUME ANALYSIS (3 columns)
    -- =========================================================================
    sma_momentum VARCHAR(15),  -- WIDENING, NARROWING, FLAT
    vol_roc DECIMAL(10, 4),  -- Volume ROC % vs 20-bar avg
    vol_delta DECIMAL(12, 2),  -- Bar delta

    -- =========================================================================
    -- COLUMN V: CVD (1 column)
    -- =========================================================================
    cvd_slope DECIMAL(10, 4),  -- Normalized CVD slope

    -- =========================================================================
    -- COLUMNS W-Z: STRUCTURE (4 columns)
    -- =========================================================================
    m5_structure VARCHAR(10),  -- BULL, BEAR, NEUTRAL
    m15_structure VARCHAR(10),  -- BULL, BEAR, NEUTRAL
    h1_structure VARCHAR(10),  -- BULL, BEAR, NEUTRAL
    h4_structure VARCHAR(10),  -- BULL, BEAR, NEUTRAL

    -- =========================================================================
    -- COLUMNS AA-AB: TRADE OUTCOME (2 columns)
    -- =========================================================================
    actual_r DECIMAL(10, 2),  -- Final R achieved
    exit_reason VARCHAR(20),  -- STOP, TARGET_3R, TARGET_CALC, CHOCH, EOD

    -- =========================================================================
    -- System Metadata
    -- =========================================================================
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    PRIMARY KEY (trade_id, event_type),
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_optimal_trade_trade ON optimal_trade(trade_id);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_date ON optimal_trade(date DESC);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_event_type ON optimal_trade(event_type);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_ticker ON optimal_trade(ticker);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_direction ON optimal_trade(direction);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_win ON optimal_trade(win);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_health ON optimal_trade(health_score);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_r ON optimal_trade(r_at_event);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_model ON optimal_trade(model);

-- Composite indexes for analysis queries
CREATE INDEX IF NOT EXISTS idx_optimal_trade_event_win ON optimal_trade(event_type, win);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_ticker_date ON optimal_trade(ticker, date DESC);

-- Update trigger
DROP TRIGGER IF EXISTS update_optimal_trade_updated_at ON optimal_trade;
CREATE TRIGGER update_optimal_trade_updated_at
    BEFORE UPDATE ON optimal_trade
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE optimal_trade IS 'Simplified 4-row analysis view per trade (v4.0.0)';
COMMENT ON COLUMN optimal_trade.event_type IS 'Key event: ENTRY (trade start), MFE (max favorable), MAE (max adverse), EXIT (trade end)';
COMMENT ON COLUMN optimal_trade.health_delta IS 'Positive = improved since entry, negative = degraded';
COMMENT ON COLUMN optimal_trade.health_summary IS 'IMPROVING if health_delta > 0, DEGRADING if < 0, STABLE if = 0';
COMMENT ON COLUMN optimal_trade.r_at_event IS 'R-multiple at this specific event moment';
COMMENT ON COLUMN optimal_trade.actual_r IS 'Final trade R-multiple (same for all 4 rows of a trade)';

-- ============================================================================
-- Event Type Reference (v4.0.0)
-- ============================================================================
-- ENTRY - First moment of trade, captures entry conditions
-- MFE   - Maximum Favorable Excursion, best R achieved during trade
-- MAE   - Maximum Adverse Excursion, worst R achieved during trade
-- EXIT  - Final moment of trade, captures exit conditions
--
-- Analysis Use Cases:
-- 1. Compare indicator state at ENTRY vs EXIT to find exit signals
-- 2. Compare MFE indicator state to find "should have exited" patterns
-- 3. Compare MAE indicator state to find "held through pain" patterns
-- 4. Filter by win/loss to find winning vs losing patterns
-- ============================================================================

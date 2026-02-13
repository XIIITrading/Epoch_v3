-- ============================================================================
-- Epoch Trading System - Table 06: setups
-- Primary and Secondary setup assignments per ticker per day.
-- Source: Analysis worksheet (rows 31-40 for primary, secondary)
-- ============================================================================

CREATE TABLE IF NOT EXISTS setups (
    -- Composite Primary Key
    date DATE NOT NULL,
    ticker_id VARCHAR(10) NOT NULL,  -- t1, t2, ... t10
    setup_type VARCHAR(10) NOT NULL,  -- PRIMARY or SECONDARY

    -- Ticker Info
    ticker VARCHAR(10) NOT NULL,

    -- Direction
    direction VARCHAR(10),  -- Bull, Bear

    -- Zone Reference
    zone_id VARCHAR(50),  -- Links to zones table
    hvn_poc DECIMAL(10, 2),
    zone_high DECIMAL(10, 2),
    zone_low DECIMAL(10, 2),

    -- Target Info
    target_id VARCHAR(20),  -- POC ID or '4R_calc'
    target_price DECIMAL(10, 2),
    risk_reward DECIMAL(10, 2),  -- R:R ratio

    -- PineScript String (for TradingView)
    pinescript_6 TEXT,  -- 6-value format: PriHigh,PriLow,PriTarget,SecHigh,SecLow,SecTarget
    pinescript_16 TEXT,  -- 16-value format (includes 10 POCs)

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    PRIMARY KEY (date, ticker_id, setup_type),
    FOREIGN KEY (date) REFERENCES daily_sessions(date) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_setups_ticker ON setups(ticker);
CREATE INDEX IF NOT EXISTS idx_setups_date ON setups(date DESC);
CREATE INDEX IF NOT EXISTS idx_setups_direction ON setups(direction);
CREATE INDEX IF NOT EXISTS idx_setups_type ON setups(setup_type);

-- Update trigger
DROP TRIGGER IF EXISTS update_setups_updated_at ON setups;
CREATE TRIGGER update_setups_updated_at
    BEFORE UPDATE ON setups
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE setups IS 'Primary and Secondary trading setups per ticker per day';
COMMENT ON COLUMN setups.setup_type IS 'PRIMARY (aligned with composite) or SECONDARY (counter-trend)';
COMMENT ON COLUMN setups.target_id IS 'POC ID used as target, or 4R_calc if no POC found';
COMMENT ON COLUMN setups.risk_reward IS 'Calculated R:R ratio (reward / risk)';
COMMENT ON COLUMN setups.pinescript_6 IS 'TradingView-ready string: PriHigh,PriLow,PriTarget,SecHigh,SecLow,SecTarget';

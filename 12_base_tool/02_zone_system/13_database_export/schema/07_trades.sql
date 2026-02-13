-- ============================================================================
-- Epoch Trading System - Table 07: trades
-- Core trade log from backtest module.
-- Source: backtest worksheet (columns A-U)
-- ============================================================================

CREATE TABLE IF NOT EXISTS trades (
    -- Primary Key
    trade_id VARCHAR(50) PRIMARY KEY,  -- Format: {ticker}_{MMDDYY}_{model}_{HHMM}

    -- Date (for foreign key and partitioning)
    date DATE NOT NULL,

    -- Trade Identification
    ticker VARCHAR(10) NOT NULL,
    model VARCHAR(10) NOT NULL,  -- EPCH1, EPCH2, EPCH3, EPCH4
    zone_type VARCHAR(10),  -- PRIMARY, SECONDARY
    direction VARCHAR(10),  -- LONG, SHORT

    -- Zone Boundaries
    zone_high DECIMAL(10, 2),
    zone_low DECIMAL(10, 2),

    -- Entry
    entry_price DECIMAL(10, 2),
    entry_time TIME,

    -- Stop Loss
    stop_price DECIMAL(10, 2),

    -- Targets
    target_3r DECIMAL(10, 2),  -- 3R target
    target_calc DECIMAL(10, 2),  -- Calculated target from Module 07
    target_used DECIMAL(10, 2),  -- Actual target used (max/min of 3R and calc)

    -- Exit
    exit_price DECIMAL(10, 2),
    exit_time TIME,
    exit_reason VARCHAR(20),  -- STOP, TARGET_3R, TARGET_CALC, CHOCH, EOD

    -- P&L
    pnl_dollars DECIMAL(10, 2),
    pnl_r DECIMAL(10, 2),  -- P&L in R-multiples
    risk DECIMAL(10, 2),  -- Dollar risk per share

    -- Outcome
    is_winner BOOLEAN,  -- TRUE if pnl_r > 0

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    FOREIGN KEY (date) REFERENCES daily_sessions(date) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(date DESC);
CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trades(ticker);
CREATE INDEX IF NOT EXISTS idx_trades_model ON trades(model);
CREATE INDEX IF NOT EXISTS idx_trades_direction ON trades(direction);
CREATE INDEX IF NOT EXISTS idx_trades_exit_reason ON trades(exit_reason);
CREATE INDEX IF NOT EXISTS idx_trades_winner ON trades(is_winner);
CREATE INDEX IF NOT EXISTS idx_trades_ticker_date ON trades(ticker, date DESC);

-- Update trigger
DROP TRIGGER IF EXISTS update_trades_updated_at ON trades;
CREATE TRIGGER update_trades_updated_at
    BEFORE UPDATE ON trades
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE trades IS 'Core trade log from backtest module';
COMMENT ON COLUMN trades.trade_id IS 'Unique identifier: {ticker}_{MMDDYY}_{model}_{HHMM}';
COMMENT ON COLUMN trades.model IS 'Entry model: EPCH1/2=Primary zone, EPCH3/4=Secondary zone';
COMMENT ON COLUMN trades.exit_reason IS 'STOP, TARGET_3R, TARGET_CALC, CHOCH (structure reversal), EOD (end of day)';
COMMENT ON COLUMN trades.pnl_r IS 'Profit/Loss in R-multiples (risk units)';
COMMENT ON COLUMN trades.target_used IS 'Actual target: max(3R, calc) for longs, min for shorts';

-- ============================================================================
-- Epoch Trading System - Options Analysis Table
-- Secondary Analysis Module
-- Source: Options data from Polygon API for completed trades
-- ============================================================================

-- Note: This table already exists in production with the schema provided.
-- This file is for reference and schema recreation if needed.

CREATE TABLE IF NOT EXISTS options_analysis (
    -- Primary Key (references trades table)
    trade_id VARCHAR(50) PRIMARY KEY,

    -- Trade Identification (denormalized for query convenience)
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10),  -- LONG, SHORT
    entry_date DATE NOT NULL,
    entry_time TIME,
    entry_price DECIMAL(10, 2),

    -- Options Contract Details
    options_ticker VARCHAR(30),  -- Full options ticker (e.g., O:AAPL250117C00175000)
    strike DECIMAL(10, 2),
    expiration DATE,
    contract_type VARCHAR(10),  -- CALL, PUT

    -- Options Entry/Exit
    option_entry_price DECIMAL(10, 4),
    option_entry_time TIME,
    option_exit_price DECIMAL(10, 4),
    option_exit_time TIME,

    -- P&L Metrics
    pnl_dollars DECIMAL(12, 2),  -- Dollar P&L per contract
    pnl_percent DECIMAL(10, 4),  -- Percentage return on premium
    option_r DECIMAL(10, 2),  -- R-multiple for options trade
    net_return DECIMAL(10, 4),  -- Net return percentage

    -- Comparison to Underlying
    underlying_r DECIMAL(10, 2),  -- Underlying trade R-multiple
    r_multiplier DECIMAL(10, 2),  -- Options R / Underlying R

    -- Outcome
    win INTEGER,  -- 1 = win, 0 = loss

    -- Processing Status
    status VARCHAR(20),  -- SUCCESS, NO_CHAIN, NO_CONTRACT, NO_BARS, etc.

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Foreign Key
    CONSTRAINT options_analysis_trade_id_fkey
        FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_options_analysis_ticker
    ON options_analysis(ticker);

CREATE INDEX IF NOT EXISTS idx_options_analysis_date
    ON options_analysis(entry_date DESC);

CREATE INDEX IF NOT EXISTS idx_options_analysis_win
    ON options_analysis(win);

CREATE INDEX IF NOT EXISTS idx_options_analysis_contract_type
    ON options_analysis(contract_type);

CREATE INDEX IF NOT EXISTS idx_options_analysis_status
    ON options_analysis(status);

-- Update trigger
DROP TRIGGER IF EXISTS update_options_analysis_updated_at ON options_analysis;
CREATE TRIGGER update_options_analysis_updated_at
    BEFORE UPDATE ON options_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE options_analysis IS 'Options trade analysis for completed backtest trades';
COMMENT ON COLUMN options_analysis.trade_id IS 'References trades.trade_id';
COMMENT ON COLUMN options_analysis.option_r IS 'Options P&L expressed as R-multiple relative to underlying risk';
COMMENT ON COLUMN options_analysis.r_multiplier IS 'Ratio of options R to underlying R (>1 = outperformed)';
COMMENT ON COLUMN options_analysis.status IS 'Processing status: SUCCESS, NO_CHAIN, NO_CONTRACT, NO_BARS, etc.';

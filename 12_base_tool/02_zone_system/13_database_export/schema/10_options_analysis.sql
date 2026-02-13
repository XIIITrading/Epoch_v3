-- ============================================================================
-- Epoch Trading System - Table 10: options_analysis
-- Options overlay analysis (1:1 relationship with trades).
-- Source: options_analysis worksheet (v1.0: columns A-V, 22 columns)
--
-- Analyzes hypothetical options trades based on equity entry/exit signals.
-- ============================================================================

CREATE TABLE IF NOT EXISTS options_analysis (
    -- Primary Key (same as trades - 1:1 relationship)
    trade_id VARCHAR(50) PRIMARY KEY,

    -- =========================================================================
    -- Trade Identification (columns A-F) - from backtest
    -- =========================================================================
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10),  -- LONG, SHORT
    entry_date DATE NOT NULL,
    entry_time TIME,
    entry_price DECIMAL(10, 2),  -- Underlying entry price

    -- =========================================================================
    -- Contract Selection (columns G-J) - from Polygon API
    -- =========================================================================
    options_ticker VARCHAR(50),  -- Full options ticker (e.g., O:AAPL250117C00175000)
    strike DECIMAL(10, 2),  -- Selected strike price
    expiration DATE,  -- Contract expiration date
    contract_type VARCHAR(10),  -- CALL, PUT

    -- =========================================================================
    -- Options Trade Data (columns K-N) - from Polygon API bars
    -- =========================================================================
    option_entry_price DECIMAL(10, 4),  -- Options premium at entry (15-second bar close)
    option_entry_time TIME,  -- Matched options bar timestamp
    option_exit_price DECIMAL(10, 4),  -- Options premium at exit (5-minute bar close)
    option_exit_time TIME,  -- Matched options bar timestamp

    -- =========================================================================
    -- P&L Metrics (columns O-R) - derived
    -- =========================================================================
    pnl_dollars DECIMAL(12, 2),  -- Dollar P&L per contract ((exit - entry) * 100)
    pnl_percent DECIMAL(10, 4),  -- Percentage return on premium
    option_r DECIMAL(10, 4),  -- R-multiple for options trade
    net_return DECIMAL(10, 4),  -- Net return percentage (same as pnl_percent)

    -- =========================================================================
    -- Comparison Metrics (columns S-U) - derived
    -- =========================================================================
    underlying_r DECIMAL(10, 4),  -- Original underlying trade R-multiple
    r_multiplier DECIMAL(10, 4),  -- Option_R / Underlying_R (>1 = options outperformed)
    win INTEGER,  -- 1=Win (P&L > 0), 0=Loss

    -- =========================================================================
    -- Status (column V)
    -- =========================================================================
    status VARCHAR(20),  -- SUCCESS, INVALID_DATA, NO_CHAIN, NO_CONTRACT, NO_ENTRY_BARS, NO_EXIT_BARS, NO_MATCHING_BARS

    -- =========================================================================
    -- System Metadata
    -- =========================================================================
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_options_analysis_ticker ON options_analysis(ticker);
CREATE INDEX IF NOT EXISTS idx_options_analysis_date ON options_analysis(entry_date DESC);
CREATE INDEX IF NOT EXISTS idx_options_analysis_win ON options_analysis(win);
CREATE INDEX IF NOT EXISTS idx_options_analysis_status ON options_analysis(status);
CREATE INDEX IF NOT EXISTS idx_options_analysis_contract_type ON options_analysis(contract_type);
CREATE INDEX IF NOT EXISTS idx_options_analysis_r_multiplier ON options_analysis(r_multiplier);

-- Update trigger
DROP TRIGGER IF EXISTS update_options_analysis_updated_at ON options_analysis;
CREATE TRIGGER update_options_analysis_updated_at
    BEFORE UPDATE ON options_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE options_analysis IS 'Options overlay analysis with 1:1 relationship to trades (v1.0)';
COMMENT ON COLUMN options_analysis.options_ticker IS 'Full Polygon options ticker format: O:SYMBOL{YYMMDD}{C/P}{STRIKE*1000}';
COMMENT ON COLUMN options_analysis.option_r IS 'Options R = Options Dollar P&L / (Underlying Risk * 100)';
COMMENT ON COLUMN options_analysis.r_multiplier IS 'Leverage ratio: >1 means options outperformed underlying';
COMMENT ON COLUMN options_analysis.status IS 'Processing status: SUCCESS or error code explaining why options data unavailable';

-- ============================================================================
-- Status Code Reference
-- ============================================================================
-- SUCCESS: Trade processed successfully with options data
-- INVALID_DATA: Missing required trade data (price, date, ticker)
-- NO_CHAIN: No options chain available for this underlying
-- NO_CONTRACT: No suitable contract found matching selection criteria
-- NO_ENTRY_BARS: No 15-second bars available at entry time
-- NO_EXIT_BARS: No 5-minute bars available at exit time
-- NO_MATCHING_BARS: Could not match bars to entry/exit times
-- ============================================================================

-- ============================================================================
-- Contract Selection Logic Reference
-- ============================================================================
-- Selection Method: FIRST_ITM (First In-The-Money)
-- Contract Type: CALL for LONG trades, PUT for SHORT trades
-- Strike Selection:
--   LONG calls: Highest strike below entry price
--   SHORT puts: Lowest strike above entry price
-- Expiration: First expiration at least 2 days after exit date
-- ============================================================================

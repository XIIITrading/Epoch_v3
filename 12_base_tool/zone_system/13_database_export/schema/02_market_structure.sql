-- ============================================================================
-- Epoch Trading System - Table 02: market_structure
-- Market structure data for indices (SPY/QQQ/DIA) and user tickers.
-- Source: market_overview worksheet (rows 29-31 for indices, 36-45 for tickers)
-- ============================================================================

CREATE TABLE IF NOT EXISTS market_structure (
    -- Composite Primary Key
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,

    -- Ticker metadata
    ticker_id VARCHAR(10),  -- t1, t2, ... t10 or SPY, QQQ, DIA
    is_index BOOLEAN DEFAULT FALSE,  -- TRUE for SPY/QQQ/DIA
    scan_price DECIMAL(10, 2),

    -- Daily (D1) Structure
    d1_direction VARCHAR(10),  -- Bull, Bull+, Bear, Bear+, Neutral
    d1_strong DECIMAL(10, 2),  -- Strong level price
    d1_weak DECIMAL(10, 2),    -- Weak level price

    -- 4-Hour (H4) Structure
    h4_direction VARCHAR(10),
    h4_strong DECIMAL(10, 2),
    h4_weak DECIMAL(10, 2),

    -- 1-Hour (H1) Structure
    h1_direction VARCHAR(10),
    h1_strong DECIMAL(10, 2),
    h1_weak DECIMAL(10, 2),

    -- 15-Minute (M15) Structure
    m15_direction VARCHAR(10),
    m15_strong DECIMAL(10, 2),
    m15_weak DECIMAL(10, 2),

    -- Composite Direction (weighted average)
    composite_direction VARCHAR(10),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    PRIMARY KEY (date, ticker),
    FOREIGN KEY (date) REFERENCES daily_sessions(date) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_market_structure_ticker ON market_structure(ticker);
CREATE INDEX IF NOT EXISTS idx_market_structure_date ON market_structure(date DESC);
CREATE INDEX IF NOT EXISTS idx_market_structure_composite ON market_structure(composite_direction);

-- Update trigger
DROP TRIGGER IF EXISTS update_market_structure_updated_at ON market_structure;
CREATE TRIGGER update_market_structure_updated_at
    BEFORE UPDATE ON market_structure
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE market_structure IS 'Multi-timeframe market structure for indices and tickers';
COMMENT ON COLUMN market_structure.is_index IS 'TRUE for SPY/QQQ/DIA, FALSE for user tickers';
COMMENT ON COLUMN market_structure.composite_direction IS 'Weighted direction: D1(1.5) + H4(1.5) + H1(1.0) + M15(0.5)';
COMMENT ON COLUMN market_structure.d1_strong IS 'Daily strong structure level (resistance in bear, support in bull)';
COMMENT ON COLUMN market_structure.d1_weak IS 'Daily weak structure level';

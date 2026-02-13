-- ============================================================================
-- EPOCH TRADING SYSTEM - M1 BARS TABLE
-- XIII Trading LLC
-- ============================================================================
--
-- PURPOSE:
--   Store 1-minute (M1) bar data from Polygon API for trade analysis.
--   Enables accurate stop/target simulation by providing bar-by-bar price data.
--
-- KEY USE CASES:
--   1. CALC-004 Simulated Outcomes - Walk bars chronologically to determine
--      if stop or target was hit first at arbitrary levels
--   2. Future indicator backtesting on bar data
--   3. Pattern recognition and price action analysis
--
-- DATA SOURCE:
--   Polygon.io API - 1-minute aggregated bars
--   Fetched for all unique (ticker, date) combinations in the trades table
--
-- ============================================================================

-- Drop existing table if it exists (for clean recreation)
DROP TABLE IF EXISTS m1_bars CASCADE;

-- Create the m1_bars table
CREATE TABLE m1_bars (
    -- =========================================================================
    -- PRIMARY KEY: Composite of ticker + bar timestamp
    -- =========================================================================
    id                  BIGSERIAL PRIMARY KEY,

    -- =========================================================================
    -- IDENTIFICATION
    -- =========================================================================
    ticker              VARCHAR(10) NOT NULL,          -- Stock symbol (e.g., SPY, QQQ)
    bar_date            DATE NOT NULL,                 -- Trading date
    bar_time            TIME NOT NULL,                 -- Bar start time (ET)
    bar_timestamp       TIMESTAMPTZ NOT NULL,          -- Full timestamp with timezone

    -- =========================================================================
    -- OHLCV DATA
    -- =========================================================================
    open                DECIMAL(12, 4) NOT NULL,       -- Bar open price
    high                DECIMAL(12, 4) NOT NULL,       -- Bar high price
    low                 DECIMAL(12, 4) NOT NULL,       -- Bar low price
    close               DECIMAL(12, 4) NOT NULL,       -- Bar close price
    volume              BIGINT NOT NULL,               -- Bar volume

    -- =========================================================================
    -- ADDITIONAL POLYGON DATA
    -- =========================================================================
    vwap                DECIMAL(12, 4),                -- Volume-weighted average price
    transactions        INTEGER,                        -- Number of transactions

    -- =========================================================================
    -- METADATA
    -- =========================================================================
    fetched_at          TIMESTAMPTZ DEFAULT NOW(),     -- When this bar was fetched

    -- =========================================================================
    -- CONSTRAINTS
    -- =========================================================================
    CONSTRAINT m1_bars_unique_bar UNIQUE (ticker, bar_timestamp)
);

-- ============================================================================
-- INDEXES FOR COMMON QUERY PATTERNS
-- ============================================================================

-- Primary lookup: Get bars for a ticker on a specific date
CREATE INDEX idx_m1_bars_ticker_date
    ON m1_bars (ticker, bar_date);

-- Time-range queries within a day
CREATE INDEX idx_m1_bars_ticker_date_time
    ON m1_bars (ticker, bar_date, bar_time);

-- Date-only queries (for batch processing checks)
CREATE INDEX idx_m1_bars_date
    ON m1_bars (bar_date);

-- Ticker-only queries
CREATE INDEX idx_m1_bars_ticker
    ON m1_bars (ticker);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE m1_bars IS
    'Stores 1-minute bar data from Polygon API for trade analysis and stop/target simulation';

COMMENT ON COLUMN m1_bars.ticker IS 'Stock symbol (uppercase)';
COMMENT ON COLUMN m1_bars.bar_date IS 'Trading date in ET';
COMMENT ON COLUMN m1_bars.bar_time IS 'Bar start time in ET (HH:MM:SS)';
COMMENT ON COLUMN m1_bars.bar_timestamp IS 'Full timestamp with timezone for precise ordering';
COMMENT ON COLUMN m1_bars.open IS 'Bar opening price';
COMMENT ON COLUMN m1_bars.high IS 'Bar high price - used for LONG MFE, SHORT MAE detection';
COMMENT ON COLUMN m1_bars.low IS 'Bar low price - used for SHORT MFE, LONG MAE detection';
COMMENT ON COLUMN m1_bars.close IS 'Bar closing price';
COMMENT ON COLUMN m1_bars.volume IS 'Number of shares traded in this bar';
COMMENT ON COLUMN m1_bars.vwap IS 'Volume-weighted average price for this bar';
COMMENT ON COLUMN m1_bars.transactions IS 'Number of transactions in this bar';
COMMENT ON COLUMN m1_bars.fetched_at IS 'Timestamp when this bar was fetched from Polygon';

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================
/*
-- Get all bars for SPY on a specific date
SELECT * FROM m1_bars
WHERE ticker = 'SPY' AND bar_date = '2025-12-30'
ORDER BY bar_time;

-- Get bars from entry time to EOD for a trade
SELECT * FROM m1_bars
WHERE ticker = 'SPY'
  AND bar_date = '2025-12-30'
  AND bar_time >= '10:15:00'
  AND bar_time <= '15:30:00'
ORDER BY bar_time;

-- Check which dates are already loaded for a ticker
SELECT DISTINCT bar_date FROM m1_bars
WHERE ticker = 'SPY'
ORDER BY bar_date;

-- Count bars per ticker-date (should be ~360-390 per trading day)
SELECT ticker, bar_date, COUNT(*) as bar_count
FROM m1_bars
GROUP BY ticker, bar_date
ORDER BY bar_date DESC, ticker;

-- Find first bar where price dropped below a threshold (for stop detection)
SELECT * FROM m1_bars
WHERE ticker = 'SPY'
  AND bar_date = '2025-12-30'
  AND bar_time >= '10:15:00'
  AND low <= 450.00  -- Example stop price
ORDER BY bar_time
LIMIT 1;
*/

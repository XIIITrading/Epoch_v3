-- ============================================================================
-- Epoch Trading System - Table 01: daily_sessions
-- Root table for all daily data. One row per trading day.
-- ============================================================================

CREATE TABLE IF NOT EXISTS daily_sessions (
    -- Primary Key
    date DATE PRIMARY KEY,

    -- Session Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Tickers analyzed this session (comma-separated list)
    tickers_analyzed TEXT,
    ticker_count INTEGER,

    -- Overall market context (from SPY/QQQ/DIA composite)
    market_composite VARCHAR(10),  -- Bull, Bull+, Bear, Bear+, Neutral

    -- Summary statistics for the day
    total_zones INTEGER,
    total_trades INTEGER,
    total_wins INTEGER,
    total_losses INTEGER,
    net_pnl_r DECIMAL(10, 2),
    win_rate DECIMAL(5, 2),

    -- Export metadata
    export_source VARCHAR(50) DEFAULT 'epoch_v1.xlsx',
    export_version VARCHAR(20)
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_daily_sessions_created_at ON daily_sessions(created_at DESC);

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_daily_sessions_updated_at ON daily_sessions;
CREATE TRIGGER update_daily_sessions_updated_at
    BEFORE UPDATE ON daily_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE daily_sessions IS 'Root table for Epoch trading sessions. One row per trading day.';
COMMENT ON COLUMN daily_sessions.date IS 'Trading date (primary key)';
COMMENT ON COLUMN daily_sessions.market_composite IS 'Overall market direction from index analysis';
COMMENT ON COLUMN daily_sessions.tickers_analyzed IS 'Comma-separated list of tickers analyzed';

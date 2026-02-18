-- ============================================================================
-- JOURNAL TABLE 1: j_m1_bars
-- 1-minute bar data from Polygon API for journal trades
-- Prior day 16:00 ET through trade day 16:00 ET
-- Mirrors m1_bars_2 from backtest, sourced from journal_trades
-- ============================================================================

CREATE TABLE IF NOT EXISTS j_m1_bars (
    id              BIGSERIAL PRIMARY KEY,
    ticker          VARCHAR(10) NOT NULL,
    bar_date        DATE NOT NULL,              -- Trade date (all bars grouped here)
    bar_time        TIME NOT NULL,              -- Bar start time (ET)
    bar_timestamp   TIMESTAMPTZ NOT NULL,       -- Full timestamp with timezone
    open            NUMERIC(12, 4) NOT NULL,
    high            NUMERIC(12, 4) NOT NULL,
    low             NUMERIC(12, 4) NOT NULL,
    close           NUMERIC(12, 4) NOT NULL,
    volume          BIGINT NOT NULL,
    vwap            NUMERIC(12, 4),
    transactions    INTEGER,
    fetched_at      TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT j_m1_bars_unique_bar UNIQUE (ticker, bar_timestamp)
);

CREATE INDEX IF NOT EXISTS idx_j_m1_bars_ticker_date ON j_m1_bars (ticker, bar_date);
CREATE INDEX IF NOT EXISTS idx_j_m1_bars_ticker_date_time ON j_m1_bars (ticker, bar_date, bar_time);
CREATE INDEX IF NOT EXISTS idx_j_m1_bars_date ON j_m1_bars (bar_date);
CREATE INDEX IF NOT EXISTS idx_j_m1_bars_ticker ON j_m1_bars (ticker);

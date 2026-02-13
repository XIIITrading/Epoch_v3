-- ============================================================================
-- EPOCH TRADING SYSTEM - trades_2 Table
-- Entry detection results (v4.0)
-- XIII Trading LLC
-- ============================================================================

CREATE TABLE trades_2 (
    trade_id    VARCHAR PRIMARY KEY,
    date        DATE NOT NULL,
    ticker      VARCHAR NOT NULL,
    model       VARCHAR NOT NULL,
    zone_type   VARCHAR NOT NULL,
    direction   VARCHAR NOT NULL,
    zone_high   NUMERIC,
    zone_low    NUMERIC,
    entry_price NUMERIC,
    entry_time  TIME,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Index for date-based lookups and cleanup
CREATE INDEX idx_trades_2_date ON trades_2 (date);

-- Index for filtering by ticker
CREATE INDEX idx_trades_2_ticker ON trades_2 (ticker);

-- Index for filtering by model
CREATE INDEX idx_trades_2_model ON trades_2 (model);

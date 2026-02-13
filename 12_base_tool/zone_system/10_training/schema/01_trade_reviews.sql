-- ============================================================================
-- Epoch Trading System - Table: trade_reviews
-- Stores user assessments for flash card training system.
-- Source: 10_training module
-- ============================================================================

CREATE TABLE IF NOT EXISTS trade_reviews (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key to trades
    trade_id VARCHAR(50) NOT NULL REFERENCES trades(trade_id) ON DELETE CASCADE,

    -- Outcome classification (set on insert based on trade P&L)
    actual_outcome TEXT CHECK (actual_outcome IN ('winner', 'loser', 'breakeven')),

    -- User notes
    notes TEXT,

    -- Trade Quality Flags
    good_trade BOOLEAN DEFAULT FALSE,
    signal_aligned BOOLEAN DEFAULT FALSE,
    confirmation_required BOOLEAN DEFAULT FALSE,

    -- Stop Placement Flags
    prior_candle_stop BOOLEAN DEFAULT FALSE,
    two_candle_stop BOOLEAN DEFAULT FALSE,
    atr_stop BOOLEAN DEFAULT FALSE,
    zone_edge_stop BOOLEAN DEFAULT FALSE,

    -- Entry Attempt (1, 2, or 3)
    entry_attempt INTEGER CHECK (entry_attempt IS NULL OR entry_attempt BETWEEN 1 AND 3),

    -- Trade Context Flags
    with_trend BOOLEAN DEFAULT FALSE,
    counter_trend BOOLEAN DEFAULT FALSE,

    -- Outcome Details
    stopped_by_wick BOOLEAN DEFAULT FALSE,

    -- Timestamps
    reviewed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Prevent duplicate reviews (one per trade)
    UNIQUE(trade_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_trade_reviews_trade_id ON trade_reviews(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_reviews_reviewed_at ON trade_reviews(reviewed_at DESC);
CREATE INDEX IF NOT EXISTS idx_trade_reviews_actual_outcome ON trade_reviews(actual_outcome);
CREATE INDEX IF NOT EXISTS idx_trade_reviews_good_trade ON trade_reviews(good_trade) WHERE good_trade = TRUE;

-- Comments
COMMENT ON TABLE trade_reviews IS 'User assessments for flash card training system';
COMMENT ON COLUMN trade_reviews.actual_outcome IS 'Actual trade outcome: winner, loser, or breakeven';
COMMENT ON COLUMN trade_reviews.good_trade IS 'User marked this as a good trade setup';
COMMENT ON COLUMN trade_reviews.signal_aligned IS 'Entry signals were aligned';
COMMENT ON COLUMN trade_reviews.confirmation_required IS 'Trade needed additional confirmation';
COMMENT ON COLUMN trade_reviews.prior_candle_stop IS 'Stop placed at prior candle level';
COMMENT ON COLUMN trade_reviews.two_candle_stop IS 'Stop placed at two candle level';
COMMENT ON COLUMN trade_reviews.atr_stop IS 'Stop placed using ATR calculation';
COMMENT ON COLUMN trade_reviews.zone_edge_stop IS 'Stop placed at zone edge';
COMMENT ON COLUMN trade_reviews.entry_attempt IS 'Which entry attempt (1st, 2nd, or 3rd)';
COMMENT ON COLUMN trade_reviews.with_trend IS 'Trade was with the trend';
COMMENT ON COLUMN trade_reviews.counter_trend IS 'Trade was counter trend';
COMMENT ON COLUMN trade_reviews.stopped_by_wick IS 'Trade was stopped out by a wick';

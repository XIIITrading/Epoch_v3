-- ============================================================================
-- Epoch Trading System - Table: trade_reviews
-- Stores user assessments for flash card training system.
-- Source: 10_training module
--
-- v2 schema: simplified review fields
--   would_trade (bool), accuracy (bool), quality (bool), stop_placement (enum),
--   context (enum), post_stop_win (bool)
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

    -- Trade (would I have taken this trade?)
    would_trade BOOLEAN DEFAULT FALSE,

    -- Accuracy (True/False)
    accuracy BOOLEAN DEFAULT FALSE,

    -- Quality (True/False)
    quality BOOLEAN DEFAULT FALSE,

    -- Stop Placement (single select)
    stop_placement TEXT CHECK (stop_placement IS NULL OR stop_placement IN (
        'prior_candle', 'two_candle', 'atr_stop', 'zone_edge'
    )),

    -- Context (single select)
    context TEXT CHECK (context IS NULL OR context IN (
        'with_trend', 'counter_trend', 'in_range', 'break_range', 'wick_stop'
    )),

    -- Post Stop Win (True/False)
    post_stop_win BOOLEAN DEFAULT FALSE,

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

-- Comments
COMMENT ON TABLE trade_reviews IS 'User assessments for flash card training system (v2)';
COMMENT ON COLUMN trade_reviews.actual_outcome IS 'Actual trade outcome: winner, loser, or breakeven';
COMMENT ON COLUMN trade_reviews.would_trade IS 'Would the reviewer have taken this trade?';
COMMENT ON COLUMN trade_reviews.accuracy IS 'Did trader predict direction correctly?';
COMMENT ON COLUMN trade_reviews.quality IS 'Was this a quality trade setup?';
COMMENT ON COLUMN trade_reviews.stop_placement IS 'Stop type used: prior_candle, two_candle, atr_stop, zone_edge';
COMMENT ON COLUMN trade_reviews.context IS 'Trade context: with_trend, counter_trend, in_range, break_range, wick_stop';
COMMENT ON COLUMN trade_reviews.post_stop_win IS 'Did the trade win after stop was hit?';

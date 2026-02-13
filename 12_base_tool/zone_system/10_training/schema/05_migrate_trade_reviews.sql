-- ============================================================================
-- Epoch Trading System - Migration: trade_reviews
-- Updates trade_reviews table to match current code expectations.
-- Run this ONCE to migrate existing table.
-- ============================================================================

-- Step 1: Drop the generated column and user_read (no longer used)
-- Note: Must drop read_correct first since it depends on user_read
ALTER TABLE trade_reviews DROP COLUMN IF EXISTS read_correct;
ALTER TABLE trade_reviews DROP COLUMN IF EXISTS user_read;
ALTER TABLE trade_reviews DROP COLUMN IF EXISTS evaluation_time_seconds;

-- Step 2: Make actual_outcome nullable (it's set from trade data, not required on insert)
ALTER TABLE trade_reviews ALTER COLUMN actual_outcome DROP NOT NULL;

-- Step 3: Add new columns for review flags
-- Trade Quality Flags
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS good_trade BOOLEAN DEFAULT FALSE;
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS signal_aligned BOOLEAN DEFAULT FALSE;
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS confirmation_required BOOLEAN DEFAULT FALSE;

-- Stop Placement Flags
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS prior_candle_stop BOOLEAN DEFAULT FALSE;
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS two_candle_stop BOOLEAN DEFAULT FALSE;
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS atr_stop BOOLEAN DEFAULT FALSE;
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS zone_edge_stop BOOLEAN DEFAULT FALSE;

-- Entry Attempt (1, 2, or 3)
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS entry_attempt INTEGER;
ALTER TABLE trade_reviews ADD CONSTRAINT chk_entry_attempt
    CHECK (entry_attempt IS NULL OR entry_attempt BETWEEN 1 AND 3);

-- Trade Context Flags
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS with_trend BOOLEAN DEFAULT FALSE;
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS counter_trend BOOLEAN DEFAULT FALSE;

-- Outcome Details
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS stopped_by_wick BOOLEAN DEFAULT FALSE;

-- Timestamps (add if missing)
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

-- Step 4: Drop old indexes that reference removed columns
DROP INDEX IF EXISTS idx_trade_reviews_user_read;
DROP INDEX IF EXISTS idx_trade_reviews_read_correct;

-- Step 5: Add new indexes
CREATE INDEX IF NOT EXISTS idx_trade_reviews_good_trade
    ON trade_reviews(good_trade) WHERE good_trade = TRUE;
CREATE INDEX IF NOT EXISTS idx_trade_reviews_reviewed_at
    ON trade_reviews(reviewed_at DESC);

-- Step 6: Update comments
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

-- Verification query (run manually to confirm)
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'trade_reviews'
-- ORDER BY ordinal_position;

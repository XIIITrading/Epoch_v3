-- ============================================================================
-- Migration: trade_reviews v1 -> v2
-- Simplified review fields
-- Run this ONCE against the existing database
-- ============================================================================

-- Add new columns
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS would_trade BOOLEAN DEFAULT FALSE;
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS quality BOOLEAN DEFAULT FALSE;
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS stop_placement TEXT;
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS context TEXT;
ALTER TABLE trade_reviews ADD COLUMN IF NOT EXISTS post_stop_win BOOLEAN DEFAULT FALSE;

-- Migrate existing data: map old booleans to new enum values
-- Stop placement: take the first checked option
UPDATE trade_reviews SET stop_placement = CASE
    WHEN prior_candle_stop = TRUE THEN 'prior_candle'
    WHEN two_candle_stop = TRUE THEN 'two_candle'
    WHEN atr_stop = TRUE THEN 'atr_stop'
    WHEN zone_edge_stop = TRUE THEN 'zone_edge'
    ELSE NULL
END
WHERE stop_placement IS NULL;

-- Context: take the first checked option
UPDATE trade_reviews SET context = CASE
    WHEN with_trend = TRUE THEN 'with_trend'
    WHEN counter_trend = TRUE THEN 'counter_trend'
    WHEN stopped_by_wick = TRUE THEN 'wick_stop'
    ELSE NULL
END
WHERE context IS NULL;

-- Quality: map from good_trade
UPDATE trade_reviews SET quality = good_trade WHERE quality = FALSE;

-- Add constraints on new columns
ALTER TABLE trade_reviews ADD CONSTRAINT chk_stop_placement
    CHECK (stop_placement IS NULL OR stop_placement IN (
        'prior_candle', 'two_candle', 'atr_stop', 'zone_edge'
    ));

ALTER TABLE trade_reviews ADD CONSTRAINT chk_context
    CHECK (context IS NULL OR context IN (
        'with_trend', 'counter_trend', 'in_range', 'break_range', 'wick_stop'
    ));

-- NOTE: Old columns are left in place for backward compatibility.
-- They can be dropped manually once migration is verified:
--   ALTER TABLE trade_reviews DROP COLUMN IF EXISTS tape_confirmation;
--   ALTER TABLE trade_reviews DROP COLUMN IF EXISTS good_trade;
--   ALTER TABLE trade_reviews DROP COLUMN IF EXISTS signal_aligned;
--   ALTER TABLE trade_reviews DROP COLUMN IF EXISTS confirmation_required;
--   ALTER TABLE trade_reviews DROP COLUMN IF EXISTS prior_candle_stop;
--   ALTER TABLE trade_reviews DROP COLUMN IF EXISTS two_candle_stop;
--   ALTER TABLE trade_reviews DROP COLUMN IF EXISTS atr_stop;
--   ALTER TABLE trade_reviews DROP COLUMN IF EXISTS zone_edge_stop;
--   ALTER TABLE trade_reviews DROP COLUMN IF EXISTS entry_attempt;
--   ALTER TABLE trade_reviews DROP COLUMN IF EXISTS with_trend;
--   ALTER TABLE trade_reviews DROP COLUMN IF EXISTS counter_trend;
--   ALTER TABLE trade_reviews DROP COLUMN IF EXISTS stopped_by_wick;

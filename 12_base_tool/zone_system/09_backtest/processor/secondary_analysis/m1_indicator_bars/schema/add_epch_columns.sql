-- Migration: Add EPCH v1.0 columns to m1_indicator_bars
-- Run this to add the new columns to an existing table

-- Add new columns if they don't exist
ALTER TABLE m1_indicator_bars
    ADD COLUMN IF NOT EXISTS candle_range_pct NUMERIC(10, 6),
    ADD COLUMN IF NOT EXISTS long_score INTEGER,
    ADD COLUMN IF NOT EXISTS short_score INTEGER;

-- Update existing rows to calculate candle_range_pct
-- Formula: (high - low) / close * 100
UPDATE m1_indicator_bars
SET candle_range_pct = ((high - low) / NULLIF(close, 0)) * 100
WHERE candle_range_pct IS NULL;

-- Update long_score based on indicator values
-- Scoring: Candle Range >= 0.15% (+2), Vol ROC >= 30% (+1), abs(vol_delta) > 100000 (+1), SMA spread >= 0.15% (+1)
-- Max 5 without H1 structure
UPDATE m1_indicator_bars
SET long_score =
    CASE WHEN candle_range_pct >= 0.15 THEN 2 ELSE 0 END +
    CASE WHEN vol_roc >= 30 THEN 1 ELSE 0 END +
    CASE WHEN ABS(vol_delta) > 100000 THEN 1 ELSE 0 END +
    CASE WHEN close > 0 AND ABS(sma_spread) / close * 100 >= 0.15 THEN 1 ELSE 0 END
WHERE long_score IS NULL;

-- Update short_score based on indicator values
-- Scoring: Candle Range >= 0.15% (+2), Vol ROC >= 30% (+1), vol_delta > 0 (+1), sma_spread > 0 (+1)
-- Max 5 without H1 structure
UPDATE m1_indicator_bars
SET short_score =
    CASE WHEN candle_range_pct >= 0.15 THEN 2 ELSE 0 END +
    CASE WHEN vol_roc >= 30 THEN 1 ELSE 0 END +
    CASE WHEN vol_delta > 0 THEN 1 ELSE 0 END +
    CASE WHEN sma_spread > 0 THEN 1 ELSE 0 END
WHERE short_score IS NULL;

-- Verify the update
SELECT
    COUNT(*) as total_rows,
    COUNT(candle_range_pct) as rows_with_candle_range,
    COUNT(long_score) as rows_with_long_score,
    COUNT(short_score) as rows_with_short_score
FROM m1_indicator_bars;

-- ============================================================================
-- Epoch Trading System - Table: trades_m5_r_win
-- Unified Canonical Trade Outcomes - ATR R-Target + Zone Buffer Fallback
-- XIII Trading LLC
--
-- PURPOSE:
--   Single source of truth for trade outcomes across all EPOCH modules.
--   Combines trades metadata with r_win_loss ATR-based outcomes (5,415 trades)
--   and zone_buffer fallback outcomes (25 trades without r_win_loss records).
--
--   This table replaces direct queries to trades.is_winner and provides:
--   1. Canonical outcome (WIN/LOSS) using the best-performing stop methodology
--   2. Original zone_buffer fields preserved with zb_ prefix for comparison
--   3. Pre-computed convenience fields (reached_2r, reached_3r, minutes_to_r1)
--   4. outcome_method flag for audit trail (atr_r_target vs zone_buffer_fallback)
--
-- OUTCOME LOGIC:
--   ATR trades (outcome_method = 'atr_r_target'):
--     WIN:  R1 target hit before stop (price high/low touches R1+)
--     LOSS: Stop hit before R1 (M1 close beyond stop level)
--     WIN:  Neither R1 nor stop by 15:30 and price > entry (EOD_WIN)
--     LOSS: Neither R1 nor stop by 15:30 and price <= entry (EOD_LOSS)
--     Same-candle conflict: stop takes priority => LOSS
--
--   Zone Buffer Fallback trades (outcome_method = 'zone_buffer_fallback'):
--     Same logic as ATR but using zone_buffer stop price and close-based detection.
--     Stop = zone_low - (zone_distance * 5%) for LONG
--     Stop = zone_high + (zone_distance * 5%) for SHORT
--     1R = abs(entry_price - stop_price)
--     Exit reasons prefixed with ZB_ (ZB_R_TARGET, ZB_STOP, ZB_EOD_WIN, ZB_EOD_LOSS)
--
-- DATA SOURCES:
--   - trades table (trade metadata, zone boundaries, original outcomes)
--   - r_win_loss table (ATR-based outcomes for 5,415 trades)
--   - m1_bars table (M1 candle data for zone_buffer fallback simulation)
--
-- DOWNSTREAM CONSUMERS:
--   - 02_dow_ai: TradeLoaderV3, DualPassAnalyzer, AccuracyReporter
--   - 05_system_analysis: Trade statistics, Indicator analysis, Monte AI
--   - 06_training: Trade model, StatsPanel, FlashcardUI
--
-- Version: 1.0.0
-- ============================================================================

CREATE TABLE IF NOT EXISTS trades_m5_r_win (
    -- =========================================================================
    -- PRIMARY KEY
    -- =========================================================================
    id SERIAL,
    trade_id VARCHAR(50) NOT NULL,

    PRIMARY KEY (trade_id),

    -- =========================================================================
    -- TRADE IDENTIFICATION (from trades table)
    -- =========================================================================
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    model VARCHAR(10),               -- EPCH01, EPCH02, EPCH03, EPCH04
    zone_type VARCHAR(20),           -- primary, secondary
    direction VARCHAR(10) NOT NULL,  -- LONG, SHORT

    -- =========================================================================
    -- ZONE BOUNDARIES (from trades table)
    -- =========================================================================
    zone_high DECIMAL(12, 4),
    zone_low DECIMAL(12, 4),

    -- =========================================================================
    -- ENTRY (from trades table)
    -- =========================================================================
    entry_price DECIMAL(12, 4) NOT NULL,
    entry_time TIME NOT NULL,

    -- =========================================================================
    -- ORIGINAL ZONE BUFFER FIELDS (preserved with zb_ prefix)
    -- =========================================================================
    zb_stop_price DECIMAL(12, 4),    -- Original zone_buffer stop price
    zb_target_3r DECIMAL(12, 4),     -- Original 3R target
    zb_exit_price DECIMAL(12, 4),    -- Original exit price
    zb_exit_time TIME,               -- Original exit time
    zb_exit_reason VARCHAR(50),      -- Original exit reason
    zb_pnl_dollars DECIMAL(12, 4),   -- Original P&L in dollars
    zb_pnl_r DECIMAL(10, 4),        -- Original P&L in R-multiples
    zb_is_winner BOOLEAN,            -- Original is_winner from trades

    -- =========================================================================
    -- CANONICAL STOP CALCULATION (from r_win_loss or zone_buffer fallback)
    -- =========================================================================
    m5_atr_value DECIMAL(12, 4),       -- Raw M5 ATR(14) value at entry (NULL for fallback)
    stop_price DECIMAL(12, 4),          -- Canonical stop price used for outcome
    stop_distance DECIMAL(12, 4),       -- Distance from entry to stop = 1R distance
    stop_distance_pct DECIMAL(8, 4),    -- (stop_distance / entry_price) * 100

    -- =========================================================================
    -- R-LEVEL TARGET PRICES (from r_win_loss, NULL for fallback except r1)
    -- =========================================================================
    r1_price DECIMAL(12, 4),  -- entry +/- 1R
    r2_price DECIMAL(12, 4),  -- entry +/- 2R
    r3_price DECIMAL(12, 4),  -- entry +/- 3R
    r4_price DECIMAL(12, 4),  -- entry +/- 4R
    r5_price DECIMAL(12, 4),  -- entry +/- 5R

    -- =========================================================================
    -- R-LEVEL HIT TRACKING (from r_win_loss, NULL for fallback except r1)
    -- =========================================================================
    r1_hit BOOLEAN DEFAULT FALSE,
    r1_time TIME,
    r1_bars_from_entry INTEGER,

    r2_hit BOOLEAN DEFAULT FALSE,
    r2_time TIME,
    r2_bars_from_entry INTEGER,

    r3_hit BOOLEAN DEFAULT FALSE,
    r3_time TIME,
    r3_bars_from_entry INTEGER,

    r4_hit BOOLEAN DEFAULT FALSE,
    r4_time TIME,
    r4_bars_from_entry INTEGER,

    r5_hit BOOLEAN DEFAULT FALSE,
    r5_time TIME,
    r5_bars_from_entry INTEGER,

    -- =========================================================================
    -- STOP HIT TRACKING
    -- =========================================================================
    stop_hit BOOLEAN DEFAULT FALSE,
    stop_hit_time TIME,
    stop_hit_bars_from_entry INTEGER,

    -- =========================================================================
    -- CANONICAL OUTCOME
    -- =========================================================================
    max_r_achieved INTEGER DEFAULT 0,      -- Highest R-level reached (0-5)
    outcome VARCHAR(10) NOT NULL,          -- WIN, LOSS (canonical)
    exit_reason VARCHAR(20) NOT NULL,      -- R_TARGET, STOP, EOD_WIN, EOD_LOSS, ZB_R_TARGET, ZB_STOP, ZB_EOD_WIN, ZB_EOD_LOSS
    eod_price DECIMAL(12, 4),              -- Price at 15:30 (for EOD exits)

    -- =========================================================================
    -- COMPUTED / CONVENIENCE FIELDS
    -- =========================================================================
    outcome_method VARCHAR(25) NOT NULL,   -- 'atr_r_target' or 'zone_buffer_fallback'
    is_winner BOOLEAN NOT NULL,            -- outcome = 'WIN' (canonical boolean)
    pnl_r DECIMAL(10, 4),                 -- Continuous R-multiple
    reached_2r BOOLEAN DEFAULT FALSE,      -- Convenience: r2_hit
    reached_3r BOOLEAN DEFAULT FALSE,      -- Convenience: r3_hit
    minutes_to_r1 INTEGER,                -- Minutes from entry to R1 hit (M1 bars)

    -- =========================================================================
    -- SYSTEM METADATA
    -- =========================================================================
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- =========================================================================
    -- CONSTRAINTS
    -- =========================================================================
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE,

    CONSTRAINT tmrw_valid_outcome CHECK (outcome IN ('WIN', 'LOSS')),
    CONSTRAINT tmrw_valid_exit_reason CHECK (exit_reason IN (
        'R_TARGET', 'STOP', 'EOD_WIN', 'EOD_LOSS',
        'ZB_R_TARGET', 'ZB_STOP', 'ZB_EOD_WIN', 'ZB_EOD_LOSS'
    )),
    CONSTRAINT tmrw_valid_outcome_method CHECK (outcome_method IN (
        'atr_r_target', 'zone_buffer_fallback'
    )),
    CONSTRAINT tmrw_valid_max_r CHECK (max_r_achieved >= 0 AND max_r_achieved <= 5)
);

-- ============================================================================
-- INDEXES
-- ============================================================================
-- Primary lookups
CREATE INDEX IF NOT EXISTS idx_tmrw_trade_id ON trades_m5_r_win(trade_id);
CREATE INDEX IF NOT EXISTS idx_tmrw_date ON trades_m5_r_win(date DESC);
CREATE INDEX IF NOT EXISTS idx_tmrw_ticker ON trades_m5_r_win(ticker);
CREATE INDEX IF NOT EXISTS idx_tmrw_model ON trades_m5_r_win(model);
CREATE INDEX IF NOT EXISTS idx_tmrw_direction ON trades_m5_r_win(direction);
CREATE INDEX IF NOT EXISTS idx_tmrw_outcome ON trades_m5_r_win(outcome);
CREATE INDEX IF NOT EXISTS idx_tmrw_outcome_method ON trades_m5_r_win(outcome_method);
CREATE INDEX IF NOT EXISTS idx_tmrw_is_winner ON trades_m5_r_win(is_winner);

-- Composite indexes for analysis
CREATE INDEX IF NOT EXISTS idx_tmrw_model_outcome ON trades_m5_r_win(model, outcome);
CREATE INDEX IF NOT EXISTS idx_tmrw_model_is_winner ON trades_m5_r_win(model, is_winner);
CREATE INDEX IF NOT EXISTS idx_tmrw_direction_outcome ON trades_m5_r_win(direction, outcome);
CREATE INDEX IF NOT EXISTS idx_tmrw_model_direction ON trades_m5_r_win(model, direction);
CREATE INDEX IF NOT EXISTS idx_tmrw_date_outcome ON trades_m5_r_win(date, outcome);
CREATE INDEX IF NOT EXISTS idx_tmrw_max_r ON trades_m5_r_win(max_r_achieved);
CREATE INDEX IF NOT EXISTS idx_tmrw_exit_reason ON trades_m5_r_win(exit_reason);

-- R-level hit analysis
CREATE INDEX IF NOT EXISTS idx_tmrw_r1_hit ON trades_m5_r_win(r1_hit);
CREATE INDEX IF NOT EXISTS idx_tmrw_r2_hit ON trades_m5_r_win(r2_hit);
CREATE INDEX IF NOT EXISTS idx_tmrw_r3_hit ON trades_m5_r_win(r3_hit);

-- ============================================================================
-- UPDATE TRIGGER
-- ============================================================================
DROP TRIGGER IF EXISTS update_trades_m5_r_win_updated_at ON trades_m5_r_win;
CREATE TRIGGER update_trades_m5_r_win_updated_at
    BEFORE UPDATE ON trades_m5_r_win
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE trades_m5_r_win IS 'Unified canonical trade outcomes: ATR R-target (primary) with zone buffer fallback. Single source of truth for all downstream systems.';
COMMENT ON COLUMN trades_m5_r_win.outcome_method IS 'atr_r_target = from r_win_loss (M5 ATR 14-period, 1.1x), zone_buffer_fallback = recalculated with close-based stop';
COMMENT ON COLUMN trades_m5_r_win.is_winner IS 'Canonical boolean: outcome = WIN. Use this instead of trades.is_winner.';
COMMENT ON COLUMN trades_m5_r_win.pnl_r IS 'Continuous R-multiple: WIN R_TARGET = max_r_achieved, LOSS STOP = -1.0, EOD = price_change / stop_distance';
COMMENT ON COLUMN trades_m5_r_win.zb_is_winner IS 'Original is_winner from trades table (zone_buffer stop methodology). Preserved for comparison.';
COMMENT ON COLUMN trades_m5_r_win.stop_price IS 'Canonical stop price: ATR-based or zone_buffer-based depending on outcome_method';
COMMENT ON COLUMN trades_m5_r_win.stop_distance IS 'Dollar distance from entry to stop = 1R unit';
COMMENT ON COLUMN trades_m5_r_win.reached_2r IS 'Convenience: same as r2_hit. Did trade reach 2R target?';
COMMENT ON COLUMN trades_m5_r_win.reached_3r IS 'Convenience: same as r3_hit. Did trade reach 3R target?';
COMMENT ON COLUMN trades_m5_r_win.minutes_to_r1 IS 'Minutes from entry to R1 hit (= r1_bars_from_entry since M1 bars are 1-minute)';
COMMENT ON COLUMN trades_m5_r_win.exit_reason IS 'R_TARGET/STOP/EOD_WIN/EOD_LOSS (ATR) or ZB_R_TARGET/ZB_STOP/ZB_EOD_WIN/ZB_EOD_LOSS (fallback)';

-- ============================================================================
-- ANALYSIS VIEWS
-- ============================================================================

-- Overall summary
CREATE OR REPLACE VIEW v_trades_m5_r_win_summary AS
SELECT
    COUNT(*) as total_trades,
    COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
    COUNT(*) FILTER (WHERE outcome = 'LOSS') as losses,
    ROUND(100.0 * COUNT(*) FILTER (WHERE outcome = 'WIN') / NULLIF(COUNT(*), 0), 2) as win_rate_pct,
    ROUND(AVG(stop_distance_pct), 2) as avg_stop_pct,
    ROUND(AVG(max_r_achieved), 2) as avg_max_r,
    -- R-level hit rates
    ROUND(100.0 * COUNT(*) FILTER (WHERE r1_hit) / NULLIF(COUNT(*), 0), 2) as r1_hit_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE r2_hit) / NULLIF(COUNT(*), 0), 2) as r2_hit_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE r3_hit) / NULLIF(COUNT(*), 0), 2) as r3_hit_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE r4_hit) / NULLIF(COUNT(*), 0), 2) as r4_hit_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE r5_hit) / NULLIF(COUNT(*), 0), 2) as r5_hit_pct,
    -- Exit reason breakdown
    COUNT(*) FILTER (WHERE exit_reason = 'R_TARGET') as r_target_exits,
    COUNT(*) FILTER (WHERE exit_reason = 'STOP') as stop_exits,
    COUNT(*) FILTER (WHERE exit_reason IN ('EOD_WIN', 'ZB_EOD_WIN')) as eod_win_exits,
    COUNT(*) FILTER (WHERE exit_reason IN ('EOD_LOSS', 'ZB_EOD_LOSS')) as eod_loss_exits,
    COUNT(*) FILTER (WHERE exit_reason = 'ZB_R_TARGET') as zb_r_target_exits,
    COUNT(*) FILTER (WHERE exit_reason = 'ZB_STOP') as zb_stop_exits,
    -- Outcome method breakdown
    COUNT(*) FILTER (WHERE outcome_method = 'atr_r_target') as atr_count,
    COUNT(*) FILTER (WHERE outcome_method = 'zone_buffer_fallback') as zb_fallback_count,
    -- Expectancy
    ROUND(AVG(pnl_r), 4) as avg_pnl_r,
    ROUND(
        (COUNT(*) FILTER (WHERE outcome = 'WIN')::decimal / NULLIF(COUNT(*), 0) *
         COALESCE(AVG(max_r_achieved) FILTER (WHERE outcome = 'WIN'), 0)) -
        (COUNT(*) FILTER (WHERE outcome = 'LOSS')::decimal / NULLIF(COUNT(*), 0) * 1.0),
        3
    ) as expectancy
FROM trades_m5_r_win;

-- Summary by model
CREATE OR REPLACE VIEW v_trades_m5_r_win_by_model AS
SELECT
    model,
    COUNT(*) as total_trades,
    COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
    COUNT(*) FILTER (WHERE outcome = 'LOSS') as losses,
    ROUND(100.0 * COUNT(*) FILTER (WHERE outcome = 'WIN') / NULLIF(COUNT(*), 0), 2) as win_rate_pct,
    ROUND(AVG(max_r_achieved), 2) as avg_max_r,
    ROUND(100.0 * COUNT(*) FILTER (WHERE r1_hit) / NULLIF(COUNT(*), 0), 2) as r1_hit_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE r2_hit) / NULLIF(COUNT(*), 0), 2) as r2_hit_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE r3_hit) / NULLIF(COUNT(*), 0), 2) as r3_hit_pct,
    ROUND(AVG(pnl_r), 4) as avg_pnl_r,
    ROUND(
        (COUNT(*) FILTER (WHERE outcome = 'WIN')::decimal / NULLIF(COUNT(*), 0) *
         COALESCE(AVG(max_r_achieved) FILTER (WHERE outcome = 'WIN'), 0)) -
        (COUNT(*) FILTER (WHERE outcome = 'LOSS')::decimal / NULLIF(COUNT(*), 0) * 1.0),
        3
    ) as expectancy,
    COUNT(*) FILTER (WHERE outcome_method = 'zone_buffer_fallback') as fallback_count
FROM trades_m5_r_win
GROUP BY model
ORDER BY model;

-- Summary by direction
CREATE OR REPLACE VIEW v_trades_m5_r_win_by_direction AS
SELECT
    direction,
    COUNT(*) as total_trades,
    COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
    COUNT(*) FILTER (WHERE outcome = 'LOSS') as losses,
    ROUND(100.0 * COUNT(*) FILTER (WHERE outcome = 'WIN') / NULLIF(COUNT(*), 0), 2) as win_rate_pct,
    ROUND(AVG(max_r_achieved), 2) as avg_max_r,
    ROUND(100.0 * COUNT(*) FILTER (WHERE r1_hit) / NULLIF(COUNT(*), 0), 2) as r1_hit_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE r2_hit) / NULLIF(COUNT(*), 0), 2) as r2_hit_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE r3_hit) / NULLIF(COUNT(*), 0), 2) as r3_hit_pct,
    ROUND(AVG(pnl_r), 4) as avg_pnl_r,
    ROUND(
        (COUNT(*) FILTER (WHERE outcome = 'WIN')::decimal / NULLIF(COUNT(*), 0) *
         COALESCE(AVG(max_r_achieved) FILTER (WHERE outcome = 'WIN'), 0)) -
        (COUNT(*) FILTER (WHERE outcome = 'LOSS')::decimal / NULLIF(COUNT(*), 0) * 1.0),
        3
    ) as expectancy
FROM trades_m5_r_win
GROUP BY direction
ORDER BY direction;

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================
/*

-- 1. Overall unified summary
SELECT * FROM v_trades_m5_r_win_summary;

-- 2. Win rate by model
SELECT * FROM v_trades_m5_r_win_by_model;

-- 3. Outcome method breakdown
SELECT
    outcome_method,
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE is_winner) as wins,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_winner) / COUNT(*), 2) as win_rate
FROM trades_m5_r_win
GROUP BY outcome_method;

-- 4. Compare canonical vs original zone_buffer outcomes
SELECT
    outcome as canonical_outcome,
    zb_is_winner as original_zb_winner,
    COUNT(*) as trade_count
FROM trades_m5_r_win
GROUP BY outcome, zb_is_winner
ORDER BY outcome, zb_is_winner;

-- 5. Trades that flipped from LOSS to WIN under ATR methodology
SELECT trade_id, ticker, date, model, direction,
       zb_is_winner, is_winner, outcome_method, exit_reason
FROM trades_m5_r_win
WHERE zb_is_winner = FALSE AND is_winner = TRUE
ORDER BY date;

-- 6. Zone buffer fallback trades
SELECT trade_id, ticker, date, model, direction,
       outcome, exit_reason, pnl_r
FROM trades_m5_r_win
WHERE outcome_method = 'zone_buffer_fallback'
ORDER BY date;

-- 7. Downstream query pattern (replaces SELECT ... FROM trades WHERE is_winner)
SELECT trade_id, date, ticker, model, direction,
       is_winner, pnl_r, outcome, outcome_method
FROM trades_m5_r_win
WHERE date BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY date, entry_time;

*/

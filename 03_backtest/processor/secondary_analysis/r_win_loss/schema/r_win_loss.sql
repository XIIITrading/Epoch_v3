-- ============================================================================
-- Epoch Trading System - Table: r_win_loss
-- R Win/Loss Analysis - ATR-Based R-Multiple Target Evaluation
-- XIII Trading LLC
--
-- PURPOSE:
--   Evaluates each trade using M5 ATR (14-period, 1.1x) as the stop/risk unit.
--   Tracks whether price reached 1R through 5R targets before being stopped out.
--   Uses M1 candle fidelity for target detection (high/low touch) and close-based
--   stop trigger (M1 close beyond stop level).
--
-- WIN/LOSS LOGIC:
--   WIN:  R1 target hit before stop (price high/low touches R1+)
--   LOSS: Stop hit before R1 (M1 close beyond stop level)
--   LOSS: Neither R1 nor stop by 15:30 and price < entry (or == entry)
--   WIN:  Neither R1 nor stop by 15:30 and price > entry
--
--   Same-candle conflict: If an M1 candle shows both R-level hit AND close
--   beyond stop, the trade is marked as LOSS (stopped out).
--
-- DATA SOURCES:
--   - Trade metadata: trades table
--   - M1 bars: m1_bars table (for bar-by-bar simulation)
--   - M5 trade bars: m5_trade_bars table (for ATR calculation)
--   - M5 indicator bars: m5_indicator_bars table (for ATR calculation)
--
-- Version: 1.0.0
-- ============================================================================

CREATE TABLE IF NOT EXISTS r_win_loss (
    -- =========================================================================
    -- PRIMARY KEY
    -- =========================================================================
    id SERIAL,
    trade_id VARCHAR(50) NOT NULL,

    PRIMARY KEY (trade_id),

    -- =========================================================================
    -- TRADE IDENTIFICATION (denormalized from trades for query convenience)
    -- =========================================================================
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10) NOT NULL,  -- LONG, SHORT
    model VARCHAR(10),  -- EPCH01, EPCH02, EPCH03, EPCH04

    -- =========================================================================
    -- ENTRY REFERENCE
    -- =========================================================================
    entry_time TIME NOT NULL,
    entry_price DECIMAL(12, 4) NOT NULL,

    -- =========================================================================
    -- ATR STOP CALCULATION
    -- =========================================================================
    m5_atr_value DECIMAL(12, 4),       -- Raw M5 ATR(14) value at entry
    stop_price DECIMAL(12, 4),          -- entry -/+ (ATR * 1.1) depending on direction
    stop_distance DECIMAL(12, 4),       -- abs(entry - stop) = 1R distance
    stop_distance_pct DECIMAL(8, 4),    -- (stop_distance / entry_price) * 100

    -- =========================================================================
    -- R-LEVEL TARGET PRICES
    -- =========================================================================
    r1_price DECIMAL(12, 4),  -- entry +/- 1R
    r2_price DECIMAL(12, 4),  -- entry +/- 2R
    r3_price DECIMAL(12, 4),  -- entry +/- 3R
    r4_price DECIMAL(12, 4),  -- entry +/- 4R
    r5_price DECIMAL(12, 4),  -- entry +/- 5R

    -- =========================================================================
    -- R-LEVEL HIT TRACKING (sequential - each level tracked independently)
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
    -- OUTCOME
    -- =========================================================================
    max_r_achieved INTEGER DEFAULT 0,      -- Highest R-level reached before stop (0-5)
    outcome VARCHAR(10) NOT NULL,          -- WIN, LOSS
    exit_reason VARCHAR(20) NOT NULL,      -- R_TARGET, STOP, EOD_WIN, EOD_LOSS
    eod_price DECIMAL(12, 4),              -- Price at 15:30 (for EOD exits)

    -- =========================================================================
    -- SYSTEM METADATA
    -- =========================================================================
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- =========================================================================
    -- CONSTRAINTS
    -- =========================================================================
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE,

    CONSTRAINT valid_outcome CHECK (outcome IN ('WIN', 'LOSS')),
    CONSTRAINT valid_exit_reason CHECK (exit_reason IN ('R_TARGET', 'STOP', 'EOD_WIN', 'EOD_LOSS')),
    CONSTRAINT valid_max_r CHECK (max_r_achieved >= 0 AND max_r_achieved <= 5)
);

-- ============================================================================
-- INDEXES
-- ============================================================================
-- Primary lookups
CREATE INDEX IF NOT EXISTS idx_rwl_trade_id ON r_win_loss(trade_id);
CREATE INDEX IF NOT EXISTS idx_rwl_date ON r_win_loss(date DESC);
CREATE INDEX IF NOT EXISTS idx_rwl_ticker ON r_win_loss(ticker);
CREATE INDEX IF NOT EXISTS idx_rwl_model ON r_win_loss(model);
CREATE INDEX IF NOT EXISTS idx_rwl_direction ON r_win_loss(direction);
CREATE INDEX IF NOT EXISTS idx_rwl_outcome ON r_win_loss(outcome);

-- Composite indexes for analysis
CREATE INDEX IF NOT EXISTS idx_rwl_model_outcome ON r_win_loss(model, outcome);
CREATE INDEX IF NOT EXISTS idx_rwl_direction_outcome ON r_win_loss(direction, outcome);
CREATE INDEX IF NOT EXISTS idx_rwl_model_direction ON r_win_loss(model, direction);
CREATE INDEX IF NOT EXISTS idx_rwl_date_outcome ON r_win_loss(date, outcome);
CREATE INDEX IF NOT EXISTS idx_rwl_max_r ON r_win_loss(max_r_achieved);
CREATE INDEX IF NOT EXISTS idx_rwl_exit_reason ON r_win_loss(exit_reason);

-- R-level hit analysis
CREATE INDEX IF NOT EXISTS idx_rwl_r1_hit ON r_win_loss(r1_hit);
CREATE INDEX IF NOT EXISTS idx_rwl_r2_hit ON r_win_loss(r2_hit);
CREATE INDEX IF NOT EXISTS idx_rwl_r3_hit ON r_win_loss(r3_hit);

-- ============================================================================
-- UPDATE TRIGGER
-- ============================================================================
DROP TRIGGER IF EXISTS update_r_win_loss_updated_at ON r_win_loss;
CREATE TRIGGER update_r_win_loss_updated_at
    BEFORE UPDATE ON r_win_loss
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE r_win_loss IS 'R Win/Loss analysis: evaluates trades using M5 ATR stop with R-multiple targets (1R-5R). 1 row per trade.';
COMMENT ON COLUMN r_win_loss.m5_atr_value IS 'Raw 14-period ATR on M5 bars at entry time';
COMMENT ON COLUMN r_win_loss.stop_price IS 'M5 ATR stop price: entry -/+ (ATR * 1.1)';
COMMENT ON COLUMN r_win_loss.stop_distance IS 'Dollar distance from entry to stop = 1R unit';
COMMENT ON COLUMN r_win_loss.r1_hit IS 'Did price reach 1R target before stop?';
COMMENT ON COLUMN r_win_loss.r1_time IS 'Time when R1 was first reached';
COMMENT ON COLUMN r_win_loss.r1_bars_from_entry IS 'M1 bars from entry to R1 hit';
COMMENT ON COLUMN r_win_loss.max_r_achieved IS 'Highest R-level reached before stop (0 = none, 5 = max)';
COMMENT ON COLUMN r_win_loss.outcome IS 'WIN if R1+ hit before stop, LOSS if stopped or EOD unfavorable';
COMMENT ON COLUMN r_win_loss.exit_reason IS 'R_TARGET (R1+ hit), STOP (stopped out), EOD_WIN (15:30 price > entry), EOD_LOSS (15:30 price <= entry)';
COMMENT ON COLUMN r_win_loss.eod_price IS 'Last M1 close at or before 15:30 for EOD exits';

-- ============================================================================
-- ANALYSIS VIEWS
-- ============================================================================

-- Overall summary
CREATE OR REPLACE VIEW v_r_win_loss_summary AS
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
    COUNT(*) FILTER (WHERE exit_reason = 'EOD_WIN') as eod_win_exits,
    COUNT(*) FILTER (WHERE exit_reason = 'EOD_LOSS') as eod_loss_exits,
    -- Expectancy: (win_rate * avg_winner_R) - (loss_rate * 1R)
    ROUND(
        (COUNT(*) FILTER (WHERE outcome = 'WIN')::decimal / NULLIF(COUNT(*), 0) *
         COALESCE(AVG(max_r_achieved) FILTER (WHERE outcome = 'WIN'), 0)) -
        (COUNT(*) FILTER (WHERE outcome = 'LOSS')::decimal / NULLIF(COUNT(*), 0) * 1.0),
        3
    ) as expectancy
FROM r_win_loss
WHERE stop_price IS NOT NULL;

-- Summary by model
CREATE OR REPLACE VIEW v_r_win_loss_by_model AS
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
    ROUND(
        (COUNT(*) FILTER (WHERE outcome = 'WIN')::decimal / NULLIF(COUNT(*), 0) *
         COALESCE(AVG(max_r_achieved) FILTER (WHERE outcome = 'WIN'), 0)) -
        (COUNT(*) FILTER (WHERE outcome = 'LOSS')::decimal / NULLIF(COUNT(*), 0) * 1.0),
        3
    ) as expectancy
FROM r_win_loss
WHERE stop_price IS NOT NULL
GROUP BY model
ORDER BY model;

-- Summary by direction
CREATE OR REPLACE VIEW v_r_win_loss_by_direction AS
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
    ROUND(
        (COUNT(*) FILTER (WHERE outcome = 'WIN')::decimal / NULLIF(COUNT(*), 0) *
         COALESCE(AVG(max_r_achieved) FILTER (WHERE outcome = 'WIN'), 0)) -
        (COUNT(*) FILTER (WHERE outcome = 'LOSS')::decimal / NULLIF(COUNT(*), 0) * 1.0),
        3
    ) as expectancy
FROM r_win_loss
WHERE stop_price IS NOT NULL
GROUP BY direction
ORDER BY direction;

-- Summary by max R achieved (distribution)
CREATE OR REPLACE VIEW v_r_win_loss_r_distribution AS
SELECT
    max_r_achieved,
    COUNT(*) as trade_count,
    ROUND(100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0), 2) as pct_of_total,
    COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
    COUNT(*) FILTER (WHERE outcome = 'LOSS') as losses
FROM r_win_loss
WHERE stop_price IS NOT NULL
GROUP BY max_r_achieved
ORDER BY max_r_achieved;

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================
/*

-- 1. Overall R win/loss summary
SELECT * FROM v_r_win_loss_summary;

-- 2. Win rate by model
SELECT * FROM v_r_win_loss_by_model;

-- 3. R-level distribution
SELECT * FROM v_r_win_loss_r_distribution;

-- 4. Trades that reached R3+
SELECT
    trade_id, ticker, date, model, direction,
    entry_price, stop_price, max_r_achieved,
    r1_time, r2_time, r3_time, outcome
FROM r_win_loss
WHERE max_r_achieved >= 3
ORDER BY date DESC;

-- 5. Stopped trades that reached R1 first (shows trades with profit opportunity)
SELECT
    trade_id, ticker, date, model, direction,
    entry_price, stop_price,
    r1_time, stop_hit_time, max_r_achieved, outcome
FROM r_win_loss
WHERE r1_hit = TRUE AND stop_hit = TRUE
ORDER BY date DESC;

-- 6. EOD exits (neither target nor stop)
SELECT
    trade_id, ticker, date, direction,
    entry_price, eod_price, exit_reason, outcome
FROM r_win_loss
WHERE exit_reason IN ('EOD_WIN', 'EOD_LOSS')
ORDER BY date DESC;

*/

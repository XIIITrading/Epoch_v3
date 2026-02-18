-- ============================================================================
-- JOURNAL TABLE 5: j_trades_m5_r_win
-- Consolidated Trade Outcomes (Denormalized) for journal trades
-- Joins journal_trades + j_m5_atr_stop + j_m1_bars into flat table
-- Extended with journal-specific columns (actual exit data, PnL, FIFO data)
-- Mirrors trades_m5_r_win_2 from backtest + journal extras
-- Pipeline: journal_trades + j_m5_atr_stop + j_m1_bars -> j_trades_m5_r_win
-- ============================================================================

CREATE TABLE IF NOT EXISTS j_trades_m5_r_win (
    -- Trade identification (from journal_trades)
    trade_id                VARCHAR(50) PRIMARY KEY,
    trade_date              DATE NOT NULL,
    ticker                  VARCHAR(10) NOT NULL,
    direction               VARCHAR(10) NOT NULL,          -- LONG, SHORT
    model                   VARCHAR(10),                    -- Nullable
    zone_type               VARCHAR(10),                    -- PRIMARY, SECONDARY (from zones join)
    account                 VARCHAR(50),                    -- SIM / LIVE

    -- Zone boundaries (from zones table)
    zone_high               DECIMAL(12, 4),
    zone_low                DECIMAL(12, 4),

    -- Entry (from journal_trades)
    entry_price             DECIMAL(12, 4) NOT NULL,
    entry_time              TIME NOT NULL,
    entry_qty               INTEGER,
    trade_seq               INTEGER,                        -- FIFO sequence number

    -- Actual exit data (from journal_trades -- real trade exits)
    exit_price              DECIMAL(12, 4),                 -- Actual VWAP exit price
    exit_time               TIME,                           -- Actual last exit time
    exit_qty                INTEGER,
    exit_portions_json      JSONB,                          -- Individual exit fills

    -- Actual P&L (from journal_trades)
    pnl_dollars             DECIMAL(12, 4),                 -- Per-share P&L
    pnl_total               DECIMAL(12, 4),                 -- Total dollar P&L

    -- M5 ATR stop calculation (from j_m5_atr_stop)
    m5_atr_value            DECIMAL(12, 6),                 -- M5 ATR(14) at entry
    stop_price              DECIMAL(12, 4),                 -- Entry -/+ M5 ATR
    stop_distance           DECIMAL(12, 6),                 -- abs(entry - stop) = 1R
    stop_distance_pct       DECIMAL(8, 4),                  -- (stop_distance / entry) * 100

    -- R-level target prices (from j_m5_atr_stop)
    r1_price                DECIMAL(12, 4),
    r2_price                DECIMAL(12, 4),
    r3_price                DECIMAL(12, 4),
    r4_price                DECIMAL(12, 4),
    r5_price                DECIMAL(12, 4),

    -- R-level hit tracking (from j_m5_atr_stop)
    r1_hit                  BOOLEAN DEFAULT FALSE,
    r1_time                 TIME,
    r1_bars_from_entry      INTEGER,

    r2_hit                  BOOLEAN DEFAULT FALSE,
    r2_time                 TIME,
    r2_bars_from_entry      INTEGER,

    r3_hit                  BOOLEAN DEFAULT FALSE,
    r3_time                 TIME,
    r3_bars_from_entry      INTEGER,

    r4_hit                  BOOLEAN DEFAULT FALSE,
    r4_time                 TIME,
    r4_bars_from_entry      INTEGER,

    r5_hit                  BOOLEAN DEFAULT FALSE,
    r5_time                 TIME,
    r5_bars_from_entry      INTEGER,

    -- Stop hit tracking (from j_m5_atr_stop)
    stop_hit                BOOLEAN DEFAULT FALSE,
    stop_hit_time           TIME,
    stop_hit_bars_from_entry INTEGER,

    -- Outcome (derived)
    max_r_achieved          INTEGER DEFAULT -1,
    outcome                 VARCHAR(10) NOT NULL,           -- WIN, LOSS
    exit_reason             VARCHAR(20) NOT NULL,           -- STOP_HIT, R5_HIT, EOD_WIN, EOD_LOSS
    is_winner               BOOLEAN NOT NULL,
    pnl_r                   DECIMAL(8, 2),
    outcome_method          VARCHAR(20) NOT NULL DEFAULT 'M5_ATR',

    -- EOD price (from j_m1_bars last bar)
    eod_price               DECIMAL(12, 4),

    -- Convenience flags (derived)
    reached_2r              BOOLEAN DEFAULT FALSE,
    reached_3r              BOOLEAN DEFAULT FALSE,
    minutes_to_r1           INTEGER,

    -- Timestamps
    calculated_at           TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Primary lookups
CREATE INDEX IF NOT EXISTS idx_j_tmrw_date ON j_trades_m5_r_win (trade_date);
CREATE INDEX IF NOT EXISTS idx_j_tmrw_ticker ON j_trades_m5_r_win (ticker);
CREATE INDEX IF NOT EXISTS idx_j_tmrw_outcome ON j_trades_m5_r_win (outcome);
CREATE INDEX IF NOT EXISTS idx_j_tmrw_max_r ON j_trades_m5_r_win (max_r_achieved);
CREATE INDEX IF NOT EXISTS idx_j_tmrw_date_outcome ON j_trades_m5_r_win (trade_date, outcome);
CREATE INDEX IF NOT EXISTS idx_j_tmrw_direction ON j_trades_m5_r_win (direction);
CREATE INDEX IF NOT EXISTS idx_j_tmrw_account ON j_trades_m5_r_win (account);

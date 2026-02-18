-- ============================================================================
-- JOURNAL TABLE 3: j_m1_atr_stop
-- M1 ATR Stop Analysis - R-Multiple Target Evaluation for journal trades
-- Evaluates each trade using M1 ATR(14) as stop/risk unit (1R).
-- Mirrors m1_atr_stop_2 from backtest
-- Pipeline: journal_trades + j_m1_bars + j_m1_indicator_bars -> j_m1_atr_stop
-- ============================================================================

CREATE TABLE IF NOT EXISTS j_m1_atr_stop (
    -- PRIMARY KEY
    trade_id VARCHAR(50) NOT NULL,
    PRIMARY KEY (trade_id),

    -- TRADE IDENTIFICATION (denormalized from journal_trades)
    trade_date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10) NOT NULL,      -- LONG, SHORT
    model VARCHAR(10),                   -- Nullable (journal trades may not have model)

    -- ENTRY REFERENCE
    entry_time TIME NOT NULL,
    entry_price DECIMAL(12, 4) NOT NULL,
    m1_entry_candle_adj TIME,            -- Entry time truncated to M1 candle

    -- M1 ATR STOP CALCULATION
    m1_atr_value DECIMAL(12, 6),         -- Raw M1 ATR(14) value at entry candle
    stop_price DECIMAL(12, 4),           -- entry -/+ m1_atr depending on direction
    stop_distance DECIMAL(12, 6),        -- abs(entry - stop) = 1R distance
    stop_distance_pct DECIMAL(8, 4),     -- (stop_distance / entry_price) * 100

    -- R-LEVEL TARGET PRICES
    r1_price DECIMAL(12, 4),
    r2_price DECIMAL(12, 4),
    r3_price DECIMAL(12, 4),
    r4_price DECIMAL(12, 4),
    r5_price DECIMAL(12, 4),

    -- R-LEVEL HIT TRACKING
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

    -- STOP HIT TRACKING
    stop_hit BOOLEAN DEFAULT FALSE,
    stop_time TIME,
    stop_bars_from_entry INTEGER,

    -- OUTCOME
    max_r INTEGER DEFAULT -1,            -- -1=LOSS, 1-5=highest R-level reached
    result VARCHAR(10) NOT NULL,         -- WIN, LOSS

    -- SYSTEM METADATA
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- CONSTRAINTS (no FK to journal_trades since it uses ON CONFLICT upsert)
    CONSTRAINT j_m1as_valid_result CHECK (result IN ('WIN', 'LOSS')),
    CONSTRAINT j_m1as_valid_max_r CHECK (max_r >= -1 AND max_r <= 5)
);

CREATE INDEX IF NOT EXISTS idx_j_m1as_date ON j_m1_atr_stop(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_j_m1as_ticker ON j_m1_atr_stop(ticker);
CREATE INDEX IF NOT EXISTS idx_j_m1as_direction ON j_m1_atr_stop(direction);
CREATE INDEX IF NOT EXISTS idx_j_m1as_result ON j_m1_atr_stop(result);
CREATE INDEX IF NOT EXISTS idx_j_m1as_max_r ON j_m1_atr_stop(max_r);

-- ============================================================================
-- JOURNAL TABLE 6: j_m1_trade_indicator
-- Single M1 bar snapshot at entry (last completed bar before entry candle)
-- Denormalized with trade context + outcome for indicator analysis
-- Mirrors m1_trade_indicator_2 from backtest
-- Pipeline: journal_trades + j_m5_atr_stop + j_m1_indicator_bars -> j_m1_trade_indicator
-- ============================================================================

CREATE TABLE IF NOT EXISTS j_m1_trade_indicator (
    -- Trade Reference
    trade_id            VARCHAR(50) NOT NULL PRIMARY KEY,

    -- Trade Context (from journal_trades)
    ticker              VARCHAR(10) NOT NULL,
    trade_date          DATE NOT NULL,
    direction           VARCHAR(10) NOT NULL,       -- LONG / SHORT
    model               VARCHAR(10),                -- Nullable
    entry_time          TIME NOT NULL,
    entry_price         NUMERIC(12, 4),

    -- Trade Outcome (from j_m5_atr_stop)
    is_winner           BOOLEAN NOT NULL,
    pnl_r               NUMERIC(8, 2),
    max_r_achieved      INTEGER,

    -- Bar Identification (M1 bar that closed just before entry candle)
    bar_date            DATE NOT NULL,
    bar_time            TIME NOT NULL,

    -- OHLCV
    open                NUMERIC(12, 4),
    high                NUMERIC(12, 4),
    low                 NUMERIC(12, 4),
    close               NUMERIC(12, 4),
    volume              BIGINT,

    -- Core Indicators (from j_m1_indicator_bars)
    candle_range_pct    NUMERIC(10, 6),
    vol_delta_raw       NUMERIC(12, 2),
    vol_delta_roll      NUMERIC(12, 2),
    vol_roc             NUMERIC(10, 4),
    sma9                NUMERIC(12, 4),
    sma21               NUMERIC(12, 4),
    sma_config          VARCHAR(10),
    sma_spread_pct      NUMERIC(10, 6),
    sma_momentum_label  VARCHAR(15),
    price_position      VARCHAR(10),
    cvd_slope           NUMERIC(10, 6),

    -- Multi-Timeframe Structure
    m5_structure        VARCHAR(10),
    m15_structure       VARCHAR(10),
    h1_structure        VARCHAR(10),

    -- Composite Scores
    health_score        INTEGER,
    long_score          INTEGER,
    short_score         INTEGER,

    -- Metadata
    calculated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_j_trade_ind_ticker_date ON j_m1_trade_indicator (ticker, trade_date);
CREATE INDEX IF NOT EXISTS idx_j_trade_ind_direction ON j_m1_trade_indicator (direction);
CREATE INDEX IF NOT EXISTS idx_j_trade_ind_winner ON j_m1_trade_indicator (is_winner);
CREATE INDEX IF NOT EXISTS idx_j_trade_ind_date ON j_m1_trade_indicator (trade_date);

-- ============================================================================
-- JOURNAL TABLE 8: j_m1_post_trade_indicator
-- 25 M1 bars after entry (bar_sequence 0=entry candle, 24=25th bar after)
-- Trade outcome stamped on every row for easy aggregation
-- Mirrors m1_post_trade_indicator_2 from backtest
-- Pipeline: journal_trades + j_m5_atr_stop + j_m1_indicator_bars -> j_m1_post_trade_indicator
-- ============================================================================

CREATE TABLE IF NOT EXISTS j_m1_post_trade_indicator (
    -- Trade Reference
    trade_id            VARCHAR(50) NOT NULL,

    -- Bar Identification
    bar_sequence        INTEGER NOT NULL,           -- 0 (entry candle) to 24
    ticker              VARCHAR(10) NOT NULL,
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

    -- Trade Outcome Context (from j_m5_atr_stop, stamped on every row)
    is_winner           BOOLEAN,
    pnl_r               NUMERIC(8, 2),
    max_r_achieved      INTEGER,

    -- Metadata
    calculated_at       TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (trade_id, bar_sequence)
);

CREATE INDEX IF NOT EXISTS idx_j_post_trade_trade ON j_m1_post_trade_indicator (trade_id);
CREATE INDEX IF NOT EXISTS idx_j_post_trade_ticker_date ON j_m1_post_trade_indicator (ticker, bar_date);
CREATE INDEX IF NOT EXISTS idx_j_post_trade_winner ON j_m1_post_trade_indicator (is_winner);

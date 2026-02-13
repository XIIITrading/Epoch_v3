-- ============================================================================
-- Epoch Trading System - Table 12: trade_bars
-- Granular trade bar data (many:1 relationship with trades).
-- Source: trade_bars worksheet (v1.2.0: columns A-AG, 33 columns)
--
-- This is the GRANULAR SOURCE OF TRUTH for all trade analysis.
-- Contains ALL M5 bars within each trade with full indicator snapshots.
-- Enables SQL-based derivative calculations (MFE/MAE, patterns, ML training).
-- ============================================================================

CREATE TABLE IF NOT EXISTS trade_bars (
    -- Composite Primary Key
    trade_id VARCHAR(50) NOT NULL,
    event_seq INTEGER NOT NULL,  -- Sequence within trade (1, 2, 3...)

    -- =========================================================================
    -- Trade Identification (columns A-B)
    -- =========================================================================
    date DATE,

    -- =========================================================================
    -- Bar Identification (columns C-F)
    -- =========================================================================
    event_time TIME,
    bars_from_entry INTEGER,  -- M5 bars since entry (0 = entry bar)
    event_type VARCHAR(15),  -- ENTRY, IN_TRADE, EXIT

    -- =========================================================================
    -- OHLCV (columns G-K)
    -- =========================================================================
    open_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    close_price DECIMAL(10, 2),
    volume INTEGER,

    -- =========================================================================
    -- R-Value (column L)
    -- =========================================================================
    r_at_event DECIMAL(10, 4),  -- R-multiple at this bar's close

    -- =========================================================================
    -- Health Score (column M)
    -- =========================================================================
    health_score INTEGER,  -- Health score at bar (0-10)

    -- =========================================================================
    -- Price Indicators (columns N-P)
    -- =========================================================================
    vwap DECIMAL(10, 2),
    sma9 DECIMAL(10, 2),
    sma21 DECIMAL(10, 2),

    -- =========================================================================
    -- Volume Indicators (columns Q-S)
    -- =========================================================================
    vol_roc DECIMAL(10, 4),  -- Volume ROC % vs 20-bar avg
    vol_delta DECIMAL(12, 2),  -- Bar delta (bar_position method)
    cvd_slope DECIMAL(10, 4),  -- Normalized CVD slope

    -- =========================================================================
    -- SMA Analysis (columns T-U)
    -- =========================================================================
    sma_spread DECIMAL(10, 4),  -- SMA9 - SMA21
    sma_momentum VARCHAR(15),  -- WIDENING, NARROWING, FLAT

    -- =========================================================================
    -- Multi-Timeframe Structure (columns V-Y)
    -- =========================================================================
    m5_structure VARCHAR(10),  -- BULL, BEAR, NEUTRAL
    m15_structure VARCHAR(10),  -- BULL, BEAR, NEUTRAL
    h1_structure VARCHAR(10),  -- BULL, BEAR, NEUTRAL
    h4_structure VARCHAR(10),  -- BULL, BEAR, NEUTRAL

    -- =========================================================================
    -- Health Summary (column Z)
    -- =========================================================================
    health_summary VARCHAR(15),  -- STRONG, MODERATE, WEAK, CRITICAL

    -- =========================================================================
    -- Trade Context (columns AA-AG)
    -- Denormalized for query convenience
    -- =========================================================================
    ticker VARCHAR(10),
    direction VARCHAR(5),  -- LONG, SHORT
    model VARCHAR(50),
    win INTEGER,  -- 1=Win, 0=Loss
    actual_r DECIMAL(10, 4),  -- Final R-multiple of trade
    exit_reason VARCHAR(50),
    entry_health INTEGER,  -- Health score at entry

    -- =========================================================================
    -- System Metadata
    -- =========================================================================
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    PRIMARY KEY (trade_id, event_seq),
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_trade_bars_trade ON trade_bars(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_bars_date ON trade_bars(date);
CREATE INDEX IF NOT EXISTS idx_trade_bars_ticker ON trade_bars(ticker);
CREATE INDEX IF NOT EXISTS idx_trade_bars_event_type ON trade_bars(event_type);
CREATE INDEX IF NOT EXISTS idx_trade_bars_r ON trade_bars(r_at_event);
CREATE INDEX IF NOT EXISTS idx_trade_bars_health ON trade_bars(health_score);
CREATE INDEX IF NOT EXISTS idx_trade_bars_win ON trade_bars(win);
CREATE INDEX IF NOT EXISTS idx_trade_bars_direction ON trade_bars(direction);
CREATE INDEX IF NOT EXISTS idx_trade_bars_model ON trade_bars(model);

-- Composite indexes for analysis queries
CREATE INDEX IF NOT EXISTS idx_trade_bars_trade_seq ON trade_bars(trade_id, event_seq);
CREATE INDEX IF NOT EXISTS idx_trade_bars_date_ticker ON trade_bars(date, ticker);
CREATE INDEX IF NOT EXISTS idx_trade_bars_win_direction ON trade_bars(win, direction);

-- Update trigger
DROP TRIGGER IF EXISTS update_trade_bars_updated_at ON trade_bars;
CREATE TRIGGER update_trade_bars_updated_at
    BEFORE UPDATE ON trade_bars
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE trade_bars IS 'Granular M5 bar data for all trades with indicator snapshots (v1.2.0)';
COMMENT ON COLUMN trade_bars.event_seq IS 'Sequence number within trade (1=first bar, ascending)';
COMMENT ON COLUMN trade_bars.bars_from_entry IS '0 at entry, increments by 1 for each subsequent M5 bar';
COMMENT ON COLUMN trade_bars.event_type IS 'ENTRY for first bar, EXIT for last bar, IN_TRADE for bars between';
COMMENT ON COLUMN trade_bars.r_at_event IS 'Running R-multiple at bar close (positive = favorable, negative = adverse)';
COMMENT ON COLUMN trade_bars.health_score IS 'DOW_AI aligned health score (0-10) at this bar';
COMMENT ON COLUMN trade_bars.health_summary IS 'STRONG (8-10), MODERATE (5-7), WEAK (2-4), CRITICAL (0-1)';
COMMENT ON COLUMN trade_bars.entry_health IS 'Health score at trade entry, for delta calculations';

-- ============================================================================
-- Example Derivative Queries
-- ============================================================================
--
-- MFE (Maximum Favorable Excursion):
--   SELECT trade_id, MAX(r_at_event) as mfe
--   FROM trade_bars
--   WHERE direction = 'LONG'
--   GROUP BY trade_id;
--
-- MAE (Maximum Adverse Excursion):
--   SELECT trade_id, MIN(r_at_event) as mae
--   FROM trade_bars
--   WHERE direction = 'LONG'
--   GROUP BY trade_id;
--
-- Health at MFE:
--   SELECT tb.trade_id, tb.health_score as health_at_mfe
--   FROM trade_bars tb
--   INNER JOIN (
--       SELECT trade_id, MAX(r_at_event) as mfe
--       FROM trade_bars WHERE direction = 'LONG'
--       GROUP BY trade_id
--   ) m ON tb.trade_id = m.trade_id AND tb.r_at_event = m.mfe;
--
-- Bars to MFE:
--   SELECT tb.trade_id, tb.bars_from_entry as bars_to_mfe
--   FROM trade_bars tb
--   INNER JOIN (
--       SELECT trade_id, MAX(r_at_event) as mfe
--       FROM trade_bars WHERE direction = 'LONG'
--       GROUP BY trade_id
--   ) m ON tb.trade_id = m.trade_id AND tb.r_at_event = m.mfe;
-- ============================================================================

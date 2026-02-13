-- ============================================================================
-- EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
-- M5 Trade Bars - Database Schema
-- XIII Trading LLC
-- ============================================================================
--
-- Trade-specific M5 bars from entry to 15:30 with health scoring and
-- MFE/MAE event marking.
--
-- Version: 1.0.0
-- ============================================================================

-- Drop table if exists (for development)
-- DROP TABLE IF EXISTS m5_trade_bars CASCADE;

CREATE TABLE IF NOT EXISTS m5_trade_bars (
    -- Primary Key (composite)
    trade_id VARCHAR(50) NOT NULL,
    bar_seq INTEGER NOT NULL,           -- Sequential within trade (0, 1, 2...)

    -- Bar Identification
    bar_time TIME NOT NULL,
    bars_from_entry INTEGER NOT NULL,   -- 0 at entry bar
    event_type VARCHAR(10) NOT NULL,    -- ENTRY, IN_TRADE, MFE, MAE, MFE_MAE

    -- Trade Context (denormalized)
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    model VARCHAR(10),

    -- OHLCV
    open DECIMAL(12, 4) NOT NULL,
    high DECIMAL(12, 4) NOT NULL,
    low DECIMAL(12, 4) NOT NULL,
    close DECIMAL(12, 4) NOT NULL,
    volume BIGINT NOT NULL,

    -- Price Indicators
    vwap DECIMAL(12, 4),
    sma9 DECIMAL(12, 4),
    sma21 DECIMAL(12, 4),
    sma_spread DECIMAL(12, 4),
    sma_alignment VARCHAR(10),          -- BULL or BEAR
    sma_alignment_healthy BOOLEAN,
    sma_momentum_ratio DECIMAL(10, 6),
    sma_momentum_label VARCHAR(15),
    sma_momentum_healthy BOOLEAN,
    vwap_position VARCHAR(10),          -- ABOVE or BELOW
    vwap_healthy BOOLEAN,

    -- Volume Indicators
    vol_roc DECIMAL(10, 4),
    vol_roc_healthy BOOLEAN,
    vol_delta DECIMAL(12, 2),
    vol_delta_healthy BOOLEAN,
    cvd_slope DECIMAL(10, 6),
    cvd_slope_healthy BOOLEAN,

    -- Structure
    h4_structure VARCHAR(10),
    h4_structure_healthy BOOLEAN,
    h1_structure VARCHAR(10),
    h1_structure_healthy BOOLEAN,
    m15_structure VARCHAR(10),
    m15_structure_healthy BOOLEAN,
    m5_structure VARCHAR(10),
    m5_structure_healthy BOOLEAN,

    -- Composite Health Score
    health_score INTEGER,               -- 0-10
    health_label VARCHAR(15),           -- CRITICAL, WEAK, MODERATE, STRONG
    structure_score INTEGER,            -- 0-4
    volume_score INTEGER,               -- 0-3
    price_score INTEGER,                -- 0-3

    -- Metadata
    calculated_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (trade_id, bar_seq),
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for querying by trade_id (common access pattern)
CREATE INDEX IF NOT EXISTS idx_m5_trade_bars_trade_id
ON m5_trade_bars (trade_id);

-- Index for querying by event type (MFE/MAE analysis)
CREATE INDEX IF NOT EXISTS idx_m5_trade_bars_event_type
ON m5_trade_bars (event_type);

-- Index for querying by ticker and date
CREATE INDEX IF NOT EXISTS idx_m5_trade_bars_ticker_date
ON m5_trade_bars (ticker, date);

-- Index for health score analysis
CREATE INDEX IF NOT EXISTS idx_m5_trade_bars_health
ON m5_trade_bars (trade_id, health_score);

-- Index for direction-based queries
CREATE INDEX IF NOT EXISTS idx_m5_trade_bars_direction
ON m5_trade_bars (direction, event_type);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE m5_trade_bars IS
'Trade-specific M5 bars from entry time to 15:30 ET.
Includes full indicator snapshots, direction-specific health scoring,
and MFE/MAE event marking from mfe_mae_potential table.';

COMMENT ON COLUMN m5_trade_bars.bar_seq IS 'Sequential bar number within trade (0 = entry bar)';
COMMENT ON COLUMN m5_trade_bars.bars_from_entry IS 'Number of 5-minute intervals from entry (0 at entry)';
COMMENT ON COLUMN m5_trade_bars.event_type IS 'Bar event: ENTRY (first bar), MFE, MAE, MFE_MAE (both), or IN_TRADE';
COMMENT ON COLUMN m5_trade_bars.sma_alignment IS 'SMA9 vs SMA21: BULL (9>21) or BEAR (9<21)';
COMMENT ON COLUMN m5_trade_bars.sma_alignment_healthy IS 'True if SMA alignment matches trade direction';
COMMENT ON COLUMN m5_trade_bars.vwap_position IS 'Price vs VWAP: ABOVE or BELOW';
COMMENT ON COLUMN m5_trade_bars.vwap_healthy IS 'True if VWAP position matches trade direction';
COMMENT ON COLUMN m5_trade_bars.health_score IS 'Composite score 0-10 based on 10 factors';
COMMENT ON COLUMN m5_trade_bars.health_label IS 'CRITICAL (0-3), WEAK (4-5), MODERATE (6-7), STRONG (8-10)';
COMMENT ON COLUMN m5_trade_bars.structure_score IS 'Sum of 4 structure factors (H4, H1, M15, M5)';
COMMENT ON COLUMN m5_trade_bars.volume_score IS 'Sum of 3 volume factors (vol_roc, vol_delta, cvd_slope)';
COMMENT ON COLUMN m5_trade_bars.price_score IS 'Sum of 3 price factors (sma_alignment, sma_momentum, vwap)';

-- ============================================================================
-- EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
-- M5 Indicator Bars - Database Schema
-- XIII Trading LLC
-- ============================================================================
--
-- Direction-agnostic M5 bars with full indicators for all ticker+dates.
-- Provides foundation data that can be reused across multiple analyses.
--
-- Version: 1.0.0
-- ============================================================================

-- Drop table if exists (for development)
-- DROP TABLE IF EXISTS m5_indicator_bars CASCADE;

CREATE TABLE IF NOT EXISTS m5_indicator_bars (
    -- Primary Key (composite)
    ticker VARCHAR(10) NOT NULL,
    bar_date DATE NOT NULL,
    bar_time TIME NOT NULL,

    -- OHLCV
    open DECIMAL(12, 4) NOT NULL,
    high DECIMAL(12, 4) NOT NULL,
    low DECIMAL(12, 4) NOT NULL,
    close DECIMAL(12, 4) NOT NULL,
    volume BIGINT NOT NULL,

    -- Price Indicators (direction-agnostic)
    vwap DECIMAL(12, 4),
    sma9 DECIMAL(12, 4),
    sma21 DECIMAL(12, 4),
    sma_spread DECIMAL(12, 4),          -- SMA9 - SMA21
    sma_momentum_ratio DECIMAL(10, 6),  -- Current/Previous spread ratio
    sma_momentum_label VARCHAR(15),     -- WIDENING, NARROWING, STABLE

    -- Volume Indicators (direction-agnostic)
    vol_roc DECIMAL(10, 4),             -- Volume ROC %
    vol_delta DECIMAL(12, 2),           -- Rolling volume delta
    cvd_slope DECIMAL(10, 6),           -- CVD linear regression slope

    -- Structure (direction-agnostic labels)
    h4_structure VARCHAR(10),           -- BULL, BEAR, NEUTRAL
    h1_structure VARCHAR(10),
    m15_structure VARCHAR(10),
    m5_structure VARCHAR(10),

    -- Metadata
    bars_in_calculation INTEGER,        -- Number of prior bars used
    calculated_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (ticker, bar_date, bar_time)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for querying by ticker and date (common access pattern)
CREATE INDEX IF NOT EXISTS idx_m5_indicator_bars_ticker_date
ON m5_indicator_bars (ticker, bar_date);

-- Index for querying by date (for batch operations)
CREATE INDEX IF NOT EXISTS idx_m5_indicator_bars_date
ON m5_indicator_bars (bar_date);

-- Index for structure analysis queries
CREATE INDEX IF NOT EXISTS idx_m5_indicator_bars_structure
ON m5_indicator_bars (ticker, bar_date, m5_structure, h1_structure);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE m5_indicator_bars IS
'Direction-agnostic M5 bars with full indicators for all ticker+dates from trades table.
Full trading day coverage: 09:30 to 16:00 ET (~78 bars per ticker-date).
Used as foundation data for multiple analyses.';

COMMENT ON COLUMN m5_indicator_bars.sma_spread IS 'SMA9 minus SMA21 - positive means SMA9 above SMA21';
COMMENT ON COLUMN m5_indicator_bars.sma_momentum_ratio IS 'Ratio of current spread to spread N bars ago';
COMMENT ON COLUMN m5_indicator_bars.sma_momentum_label IS 'WIDENING (trend strengthening), NARROWING (trend weakening), or STABLE';
COMMENT ON COLUMN m5_indicator_bars.vol_roc IS 'Volume Rate of Change - percentage above/below baseline average';
COMMENT ON COLUMN m5_indicator_bars.vol_delta IS 'Rolling sum of bar deltas (buying - selling pressure estimate)';
COMMENT ON COLUMN m5_indicator_bars.cvd_slope IS 'Slope of CVD over window, normalized by average volume';
COMMENT ON COLUMN m5_indicator_bars.h4_structure IS 'H4 market structure: BULL, BEAR, or NEUTRAL';
COMMENT ON COLUMN m5_indicator_bars.h1_structure IS 'H1 market structure: BULL, BEAR, or NEUTRAL';
COMMENT ON COLUMN m5_indicator_bars.m15_structure IS 'M15 market structure: BULL, BEAR, or NEUTRAL';
COMMENT ON COLUMN m5_indicator_bars.m5_structure IS 'M5 market structure: BULL, BEAR, or NEUTRAL';
COMMENT ON COLUMN m5_indicator_bars.bars_in_calculation IS 'Number of M5 bars available for calculation at this point';

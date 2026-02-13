-- ============================================================================
-- Epoch Trading System - Migration Script v2.1
-- Drops and recreates tables with updated schemas
--
-- Run this script to update your database to support:
-- - trade_entry_events with win column (v4.1)
-- - trade_exit_events with win column (v3.2)
-- - optimal_trade table (v4.0.0) - NEW
-- - options_analysis table (v1.0)
--
-- WARNING: This will DELETE all data in these tables!
-- ============================================================================

-- Drop tables in dependency order (child tables first)
DROP TABLE IF EXISTS options_analysis CASCADE;
DROP TABLE IF EXISTS optimal_trade CASCADE;
DROP TABLE IF EXISTS trade_exit_events CASCADE;
DROP TABLE IF EXISTS trade_entry_events CASCADE;

-- Now recreate them by running the individual schema files
-- (The statements below are copied from the individual schema files)

-- ============================================================================
-- Table 08: trade_entry_events (v4.1)
-- ============================================================================
CREATE TABLE IF NOT EXISTS trade_entry_events (
    -- Primary Key (same as trades - 1:1 relationship)
    trade_id VARCHAR(50) PRIMARY KEY,

    -- VWAP Analysis (columns B-E)
    entry_vwap DECIMAL(10, 2),
    entry_vs_vwap VARCHAR(10),
    vwap_diff DECIMAL(10, 4),
    vwap_pct DECIMAL(10, 4),

    -- SMA Analysis (columns F-M)
    entry_sma9 DECIMAL(10, 2),
    entry_vs_sma9 VARCHAR(10),
    entry_sma21 DECIMAL(10, 2),
    entry_vs_sma21 VARCHAR(10),
    sma9_vs_sma21 VARCHAR(10),
    sma_spread DECIMAL(10, 4),
    sma_spread_momentum VARCHAR(15),
    cross_price_estimate DECIMAL(10, 2),

    -- Volume Analysis - DOW_AI (columns N-V)
    entry_volume INTEGER,
    vol_roc DECIMAL(10, 4),
    vol_roc_signal VARCHAR(15),
    vol_baseline_avg DECIMAL(12, 2),
    vol_delta_signal VARCHAR(15),
    cvd_trend VARCHAR(10),
    cvd_slope DECIMAL(10, 4),
    relative_volume DECIMAL(10, 4),

    -- Volume Analysis - Legacy
    avg_volume_5 DECIMAL(12, 2),
    volume_delta_pct DECIMAL(10, 2),
    volume_trend VARCHAR(15),
    prior_bar_qual VARCHAR(15),
    vol_delta_class VARCHAR(10),
    vol_delta_value INTEGER,

    -- Multi-Timeframe Structure
    m5_structure VARCHAR(10),
    m15_structure VARCHAR(10),
    h1_structure VARCHAR(10),
    h4_structure VARCHAR(10),
    structure_align_score INTEGER,
    dominant_structure VARCHAR(10),
    m5_last_break VARCHAR(20),
    m15_last_break VARCHAR(20),
    m5_pct_to_strong DECIMAL(10, 4),
    m5_pct_to_weak DECIMAL(10, 4),

    -- Entry Health Score
    health_score INTEGER,
    health_max INTEGER DEFAULT 10,
    health_pct DECIMAL(5, 2),
    health_label VARCHAR(15),

    -- Alignment Flags - DOW_AI
    htf_aligned BOOLEAN,
    mtf_aligned BOOLEAN,
    vol_aligned BOOLEAN,
    ind_aligned BOOLEAN,

    -- Alignment Flags - Legacy
    vwap_aligned BOOLEAN,
    trend_aligned BOOLEAN,
    structure_aligned BOOLEAN,

    -- Processing Metadata
    enrichment_time TIMESTAMPTZ,
    status VARCHAR(10),
    error_message TEXT,

    -- Trade Outcome (v4.1)
    win INTEGER,

    -- System Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_trade_entry_events_health ON trade_entry_events(health_score);
CREATE INDEX IF NOT EXISTS idx_trade_entry_events_health_label ON trade_entry_events(health_label);
CREATE INDEX IF NOT EXISTS idx_trade_entry_events_structure ON trade_entry_events(dominant_structure);
CREATE INDEX IF NOT EXISTS idx_trade_entry_events_win ON trade_entry_events(win);
CREATE INDEX IF NOT EXISTS idx_trade_entry_events_htf_aligned ON trade_entry_events(htf_aligned);
CREATE INDEX IF NOT EXISTS idx_trade_entry_events_vol_aligned ON trade_entry_events(vol_aligned);

DROP TRIGGER IF EXISTS update_trade_entry_events_updated_at ON trade_entry_events;
CREATE TRIGGER update_trade_entry_events_updated_at
    BEFORE UPDATE ON trade_entry_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Table 09: trade_exit_events (v3.2)
-- ============================================================================
CREATE TABLE IF NOT EXISTS trade_exit_events (
    -- Composite Primary Key
    trade_id VARCHAR(50) NOT NULL,
    event_seq INTEGER NOT NULL,

    -- Core Identification
    event_time TIME,
    bars_from_entry INTEGER,
    bars_from_mfe INTEGER,

    -- Event Details
    event_type VARCHAR(30) NOT NULL,
    from_state VARCHAR(50),
    to_state VARCHAR(50),

    -- Position at Event
    price_at_event DECIMAL(10, 2),
    r_at_event DECIMAL(10, 2),
    health_score INTEGER,
    health_delta INTEGER,

    -- Price Indicators
    vwap DECIMAL(10, 2),
    sma9 DECIMAL(10, 2),
    sma21 DECIMAL(10, 2),

    -- Volume Analysis
    volume INTEGER,
    vol_roc DECIMAL(10, 4),
    vol_delta DECIMAL(12, 2),
    cvd_slope DECIMAL(10, 4),

    -- SMA Analysis
    sma_spread DECIMAL(10, 4),
    sma_momentum VARCHAR(15),

    -- Multi-Timeframe Structure
    m5_structure VARCHAR(10),
    m15_structure VARCHAR(10),
    h1_structure VARCHAR(10),
    h4_structure VARCHAR(10),

    -- Swing Levels
    swing_high DECIMAL(10, 2),
    swing_low DECIMAL(10, 2),
    bars_since_swing INTEGER,

    -- Refined Exit Events
    health_summary VARCHAR(15),
    event_priority VARCHAR(10),
    indicator_changed TEXT,

    -- Trade Outcome (v3.2)
    win INTEGER,

    -- System Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (trade_id, event_seq),
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_trade_exit_events_trade ON trade_exit_events(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_exit_events_type ON trade_exit_events(event_type);
CREATE INDEX IF NOT EXISTS idx_trade_exit_events_r ON trade_exit_events(r_at_event);
CREATE INDEX IF NOT EXISTS idx_trade_exit_events_health ON trade_exit_events(health_score);
CREATE INDEX IF NOT EXISTS idx_trade_exit_events_priority ON trade_exit_events(event_priority);
CREATE INDEX IF NOT EXISTS idx_trade_exit_events_win ON trade_exit_events(win);

DROP TRIGGER IF EXISTS update_trade_exit_events_updated_at ON trade_exit_events;
CREATE TRIGGER update_trade_exit_events_updated_at
    BEFORE UPDATE ON trade_exit_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Table 10: options_analysis (v1.0)
-- ============================================================================
CREATE TABLE IF NOT EXISTS options_analysis (
    -- Primary Key
    trade_id VARCHAR(50) PRIMARY KEY,

    -- Trade Identification
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10),
    entry_date DATE NOT NULL,
    entry_time TIME,
    entry_price DECIMAL(10, 2),

    -- Contract Selection
    options_ticker VARCHAR(30),
    strike DECIMAL(10, 2),
    expiration DATE,
    contract_type VARCHAR(10),

    -- Options Trade Data
    option_entry_price DECIMAL(10, 4),
    option_entry_time TIME,
    option_exit_price DECIMAL(10, 4),
    option_exit_time TIME,

    -- P&L Metrics
    pnl_dollars DECIMAL(12, 2),
    pnl_percent DECIMAL(10, 4),
    option_r DECIMAL(10, 2),
    net_return DECIMAL(10, 4),

    -- Comparison Metrics
    underlying_r DECIMAL(10, 2),
    r_multiplier DECIMAL(10, 2),
    win INTEGER,

    -- Status
    status VARCHAR(20),

    -- System Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_options_analysis_ticker ON options_analysis(ticker);
CREATE INDEX IF NOT EXISTS idx_options_analysis_date ON options_analysis(entry_date DESC);
CREATE INDEX IF NOT EXISTS idx_options_analysis_win ON options_analysis(win);
CREATE INDEX IF NOT EXISTS idx_options_analysis_contract_type ON options_analysis(contract_type);

DROP TRIGGER IF EXISTS update_options_analysis_updated_at ON options_analysis;
CREATE TRIGGER update_options_analysis_updated_at
    BEFORE UPDATE ON options_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Table 11: optimal_trade (v4.0.0) - NEW
-- ============================================================================
CREATE TABLE IF NOT EXISTS optimal_trade (
    -- Composite Primary Key
    trade_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(10) NOT NULL,

    -- Trade Identification
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10),
    model VARCHAR(10),
    win INTEGER,

    -- Event Identification
    event_time TIME,
    bars_from_entry INTEGER,
    price_at_event DECIMAL(10, 2),
    r_at_event DECIMAL(10, 2),

    -- Health Metrics
    health_score INTEGER,
    health_delta INTEGER,
    health_summary VARCHAR(15),

    -- Indicator Values
    vwap DECIMAL(10, 2),
    sma9 DECIMAL(10, 2),
    sma21 DECIMAL(10, 2),
    sma_spread DECIMAL(10, 4),

    -- SMA & Volume Analysis
    sma_momentum VARCHAR(15),
    vol_roc DECIMAL(10, 4),
    vol_delta DECIMAL(12, 2),

    -- CVD
    cvd_slope DECIMAL(10, 4),

    -- Structure
    m5_structure VARCHAR(10),
    m15_structure VARCHAR(10),
    h1_structure VARCHAR(10),
    h4_structure VARCHAR(10),

    -- Trade Outcome
    actual_r DECIMAL(10, 2),
    exit_reason VARCHAR(20),

    -- System Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (trade_id, event_type),
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_optimal_trade_trade ON optimal_trade(trade_id);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_date ON optimal_trade(date DESC);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_event_type ON optimal_trade(event_type);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_ticker ON optimal_trade(ticker);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_direction ON optimal_trade(direction);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_win ON optimal_trade(win);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_health ON optimal_trade(health_score);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_r ON optimal_trade(r_at_event);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_model ON optimal_trade(model);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_event_win ON optimal_trade(event_type, win);
CREATE INDEX IF NOT EXISTS idx_optimal_trade_ticker_date ON optimal_trade(ticker, date DESC);

DROP TRIGGER IF EXISTS update_optimal_trade_updated_at ON optimal_trade;
CREATE TRIGGER update_optimal_trade_updated_at
    BEFORE UPDATE ON optimal_trade
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Done!
-- ============================================================================
SELECT 'Migration v2.1 complete. Tables recreated:' AS status;
SELECT '  - trade_entry_events (v4.1 with win column)' AS table_updated;
SELECT '  - trade_exit_events (v3.2 with win column)' AS table_updated;
SELECT '  - options_analysis (v1.0)' AS table_updated;
SELECT '  - optimal_trade (v4.0.0 - NEW)' AS table_updated;

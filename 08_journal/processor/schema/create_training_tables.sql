-- =============================================================================
-- Epoch Trading Journal - Training Flashcard Tables
-- Mirrors backtest secondary analysis tables for journal trade data
--
-- Prerequisite: journal_trades, journal_m1_bars, journal_m1_indicator_bars
-- Gate: Only populated for trades where stop_price IS NOT NULL
--
-- Usage:
--   psql -f processor/schema/create_training_tables.sql
--   Or: python processor/run_training_processors.py --create-tables
-- =============================================================================


-- =============================================================================
-- 1. journal_entry_indicators
-- Full indicator snapshot at entry time (from journal_m1_indicator_bars)
-- =============================================================================

CREATE TABLE IF NOT EXISTS journal_entry_indicators (
    -- PRIMARY KEY
    trade_id            VARCHAR(60) NOT NULL PRIMARY KEY,

    -- TRADE CONTEXT (denormalized)
    trade_date          DATE NOT NULL,
    ticker              VARCHAR(10) NOT NULL,
    direction           VARCHAR(10),
    entry_time          TIME WITHOUT TIME ZONE,
    entry_price         NUMERIC(12, 4),

    -- INDICATOR BAR REFERENCE
    indicator_bar_time  TIME WITHOUT TIME ZONE,

    -- PRICE INDICATORS
    vwap                NUMERIC(12, 4),
    sma9                NUMERIC(12, 4),
    sma21               NUMERIC(12, 4),
    sma_spread          NUMERIC(12, 4),
    sma_momentum_ratio  NUMERIC(10, 6),
    sma_momentum_label  VARCHAR(15),

    -- VOLUME INDICATORS
    vol_roc             NUMERIC(10, 4),
    vol_delta           NUMERIC(12, 2),
    cvd_slope           NUMERIC(10, 6),

    -- STRUCTURE
    h4_structure        VARCHAR(10),
    h1_structure        VARCHAR(10),
    m15_structure       VARCHAR(10),
    m5_structure        VARCHAR(10),
    m1_structure        VARCHAR(10),

    -- HEALTH SCORE (0-10)
    health_score        INTEGER,

    -- ENTRY QUALIFIER INDICATORS
    candle_range_pct    NUMERIC(10, 6),
    long_score          INTEGER,
    short_score         INTEGER,

    -- COMPONENT SCORES
    structure_score     INTEGER,
    volume_score        INTEGER,
    price_score         INTEGER,

    -- METADATA
    calculated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jrnl_ei_trade_date
    ON journal_entry_indicators (trade_date);
CREATE INDEX IF NOT EXISTS idx_jrnl_ei_ticker
    ON journal_entry_indicators (ticker);
CREATE INDEX IF NOT EXISTS idx_jrnl_ei_health
    ON journal_entry_indicators (health_score);


-- =============================================================================
-- 2. journal_mfe_mae_potential
-- MFE/MAE in R-multiples from M1 bars between entry and exit
-- =============================================================================

CREATE TABLE IF NOT EXISTS journal_mfe_mae_potential (
    -- PRIMARY KEY
    trade_id            VARCHAR(60) NOT NULL PRIMARY KEY,

    -- TRADE CONTEXT
    trade_date          DATE NOT NULL,
    ticker              VARCHAR(10) NOT NULL,
    direction           VARCHAR(10) NOT NULL,
    entry_time          TIME WITHOUT TIME ZONE NOT NULL,
    entry_price         NUMERIC(12, 4) NOT NULL,
    exit_time           TIME WITHOUT TIME ZONE,
    exit_price          NUMERIC(12, 4),

    -- STOP REFERENCE
    stop_price          NUMERIC(12, 4) NOT NULL,
    stop_distance       NUMERIC(12, 4) NOT NULL,

    -- MFE (Max Favorable Excursion)
    mfe_r               NUMERIC(10, 4),
    mfe_price           NUMERIC(12, 4),
    mfe_time            TIME WITHOUT TIME ZONE,
    mfe_bar_index       INTEGER,

    -- MAE (Max Adverse Excursion)
    mae_r               NUMERIC(10, 4),
    mae_price           NUMERIC(12, 4),
    mae_time            TIME WITHOUT TIME ZONE,
    mae_bar_index       INTEGER,

    -- TEMPORAL WIN CONDITION
    temporal_win        BOOLEAN,

    -- METADATA
    bars_analyzed       INTEGER,
    calculated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jrnl_mfe_mae_trade_date
    ON journal_mfe_mae_potential (trade_date);
CREATE INDEX IF NOT EXISTS idx_jrnl_mfe_mae_ticker
    ON journal_mfe_mae_potential (ticker);


-- =============================================================================
-- 3. journal_r_levels
-- R-level prices and hit tracking using user-set stop_price
-- =============================================================================

CREATE TABLE IF NOT EXISTS journal_r_levels (
    -- PRIMARY KEY
    trade_id            VARCHAR(60) NOT NULL PRIMARY KEY,

    -- TRADE CONTEXT
    trade_date          DATE NOT NULL,
    ticker              VARCHAR(10) NOT NULL,
    direction           VARCHAR(10) NOT NULL,
    entry_price         NUMERIC(12, 4) NOT NULL,
    stop_price          NUMERIC(12, 4) NOT NULL,
    stop_distance       NUMERIC(12, 4) NOT NULL,

    -- R-LEVEL PRICES
    r1_price            NUMERIC(12, 4),
    r2_price            NUMERIC(12, 4),
    r3_price            NUMERIC(12, 4),

    -- R-LEVEL HIT TRACKING
    r1_hit              BOOLEAN DEFAULT FALSE,
    r1_hit_time         TIME WITHOUT TIME ZONE,
    r1_hit_bar_index    INTEGER,

    r2_hit              BOOLEAN DEFAULT FALSE,
    r2_hit_time         TIME WITHOUT TIME ZONE,
    r2_hit_bar_index    INTEGER,

    r3_hit              BOOLEAN DEFAULT FALSE,
    r3_hit_time         TIME WITHOUT TIME ZONE,
    r3_hit_bar_index    INTEGER,

    -- STOP HIT TRACKING
    stop_hit            BOOLEAN DEFAULT FALSE,
    stop_hit_time       TIME WITHOUT TIME ZONE,

    -- OUTCOME
    max_r_achieved      NUMERIC(10, 4),
    pnl_r               NUMERIC(10, 4),
    outcome             VARCHAR(10),
    is_winner           BOOLEAN,

    -- METADATA
    bars_analyzed       INTEGER,
    calculated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jrnl_r_levels_trade_date
    ON journal_r_levels (trade_date);
CREATE INDEX IF NOT EXISTS idx_jrnl_r_levels_ticker
    ON journal_r_levels (ticker);
CREATE INDEX IF NOT EXISTS idx_jrnl_r_levels_outcome
    ON journal_r_levels (outcome);


-- =============================================================================
-- 4. journal_optimal_trade
-- Indicator snapshots at critical trade events
-- Events: ENTRY, MFE, MAE, EXIT, R1_CROSS, R2_CROSS, R3_CROSS
-- =============================================================================

CREATE TABLE IF NOT EXISTS journal_optimal_trade (
    -- COMPOSITE PRIMARY KEY
    trade_id            VARCHAR(60) NOT NULL,
    event_type          VARCHAR(10) NOT NULL,

    PRIMARY KEY (trade_id, event_type),

    -- TRADE CONTEXT
    trade_date          DATE NOT NULL,
    ticker              VARCHAR(10) NOT NULL,
    direction           VARCHAR(10),
    model               VARCHAR(10),

    -- WIN CONDITION (temporal: mfe_time < mae_time)
    win                 INTEGER,

    -- EVENT TIMING
    event_time          TIME WITHOUT TIME ZONE,
    bars_from_entry     INTEGER,

    -- PRICE DATA
    entry_price         NUMERIC(12, 4),
    price_at_event      NUMERIC(12, 4),
    points_at_event     NUMERIC(10, 4),

    -- HEALTH METRICS
    health_score        INTEGER,
    health_label        VARCHAR(15),
    health_delta        INTEGER,
    health_summary      VARCHAR(15),

    -- COMPONENT SCORES
    structure_score     INTEGER,
    volume_score        INTEGER,
    price_score         INTEGER,

    -- PRICE INDICATORS
    vwap                NUMERIC(12, 4),
    sma9                NUMERIC(12, 4),
    sma21               NUMERIC(12, 4),
    sma_spread          NUMERIC(12, 4),
    sma_momentum_ratio  NUMERIC(10, 6),
    sma_momentum_label  VARCHAR(15),

    -- VOLUME INDICATORS
    vol_roc             NUMERIC(10, 4),
    vol_delta           NUMERIC(12, 2),
    cvd_slope           NUMERIC(10, 6),

    -- STRUCTURE
    m1_structure        VARCHAR(10),
    m15_structure       VARCHAR(10),
    h1_structure        VARCHAR(10),
    h4_structure        VARCHAR(10),

    -- HEALTHY FLAGS
    sma_alignment_healthy   BOOLEAN,
    sma_momentum_healthy    BOOLEAN,
    vwap_healthy            BOOLEAN,
    vol_roc_healthy         BOOLEAN,
    vol_delta_healthy       BOOLEAN,
    cvd_slope_healthy       BOOLEAN,

    -- METADATA
    calculated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jrnl_opt_trade_id
    ON journal_optimal_trade (trade_id);
CREATE INDEX IF NOT EXISTS idx_jrnl_opt_event_type
    ON journal_optimal_trade (event_type);
CREATE INDEX IF NOT EXISTS idx_jrnl_opt_trade_date
    ON journal_optimal_trade (trade_date);
CREATE INDEX IF NOT EXISTS idx_jrnl_opt_health
    ON journal_optimal_trade (health_score);


-- =============================================================================
-- 5. journal_trade_reviews
-- 14-boolean flashcard review form (matches 06_training trade_reviews schema)
-- =============================================================================

CREATE TABLE IF NOT EXISTS journal_trade_reviews (
    -- PRIMARY KEY
    trade_id            VARCHAR(60) NOT NULL PRIMARY KEY,

    -- OUTCOME ASSESSMENT
    actual_outcome      VARCHAR(15) CHECK (actual_outcome IN ('winner', 'loser', 'breakeven')),

    -- JOURNAL NOTES (maps to Notion Section 10)
    notes               TEXT,                -- What did I learn from this trade?
    notes_differently   TEXT,                -- What would I do differently?
    notes_pattern       TEXT,                -- Pattern recognition notes
    notes_observations  TEXT,                -- Additional observations

    -- ACCURACY & CONFIRMATION
    accuracy            BOOLEAN DEFAULT FALSE,
    tape_confirmation   BOOLEAN DEFAULT FALSE,

    -- TRADE QUALITY
    good_trade          BOOLEAN DEFAULT FALSE,
    signal_aligned      BOOLEAN DEFAULT FALSE,
    confirmation_required BOOLEAN DEFAULT FALSE,

    -- STOP PLACEMENT
    prior_candle_stop   BOOLEAN DEFAULT FALSE,
    two_candle_stop     BOOLEAN DEFAULT FALSE,
    atr_stop            BOOLEAN DEFAULT FALSE,
    zone_edge_stop      BOOLEAN DEFAULT FALSE,

    -- ENTRY ATTEMPT
    entry_attempt       INTEGER CHECK (entry_attempt IS NULL OR entry_attempt BETWEEN 1 AND 3),

    -- TRADE CONTEXT
    with_trend          BOOLEAN DEFAULT FALSE,
    counter_trend       BOOLEAN DEFAULT FALSE,

    -- OUTCOME DETAILS
    stopped_by_wick     BOOLEAN DEFAULT FALSE,

    -- TIMESTAMPS
    reviewed_at         TIMESTAMPTZ DEFAULT NOW(),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jrnl_reviews_reviewed
    ON journal_trade_reviews (reviewed_at);

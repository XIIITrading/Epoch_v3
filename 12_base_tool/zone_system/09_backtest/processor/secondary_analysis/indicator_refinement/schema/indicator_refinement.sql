-- ============================================================================
-- EPOCH TRADING SYSTEM - MODULE 09: SECONDARY ANALYSIS
-- Indicator Refinement - Database Schema
-- XIII Trading LLC
-- ============================================================================
--
-- Table for storing Continuation/Rejection indicator scores.
-- Based on Epoch Indicator Model Specification v1.0 (January 12, 2026).
--
-- Trade Classification:
--   - CONTINUATION trades (EPCH01/EPCH03): With-trend, scored 0-10
--   - REJECTION trades (EPCH02/EPCH04): Counter-trend/exhaustion, scored 0-11
--
-- Version: 1.0.0
-- ============================================================================

CREATE TABLE IF NOT EXISTS indicator_refinement (
    -- =========================================================================
    -- PRIMARY KEY
    -- =========================================================================
    trade_id VARCHAR(50) NOT NULL PRIMARY KEY,

    -- =========================================================================
    -- DENORMALIZED TRADE CONTEXT (for query efficiency)
    -- =========================================================================
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10) NOT NULL,           -- LONG, SHORT
    model VARCHAR(10) NOT NULL,               -- EPCH01, EPCH02, EPCH03, EPCH04
    entry_time TIME NOT NULL,
    entry_price NUMERIC(12, 4) NOT NULL,

    -- =========================================================================
    -- TRADE CLASSIFICATION
    -- =========================================================================
    trade_type VARCHAR(15) NOT NULL,          -- CONTINUATION, REJECTION

    -- =========================================================================
    -- CONTINUATION INDICATORS (CONT-01 to CONT-04)
    -- Total: 0-10 points
    -- =========================================================================

    -- CONT-01: Multi-Timeframe Alignment Score (0-4 points)
    -- 4 = Full alignment (STRONG)
    -- 3 = Minor divergence (ACCEPTABLE)
    -- 2 = Split alignment (WEAK)
    -- 0-1 = Counter-trend (AVOID for continuation)
    mtf_align_score INTEGER,
    mtf_h4_aligned BOOLEAN,                   -- H4 aligned with direction?
    mtf_h1_aligned BOOLEAN,                   -- H1 aligned with direction?
    mtf_m15_aligned BOOLEAN,                  -- M15 aligned with direction?
    mtf_m5_aligned BOOLEAN,                   -- M5 aligned with direction?

    -- CONT-02: SMA Momentum Score (0-2 points)
    -- 2 = Strong momentum (spread aligned AND widening)
    -- 1 = Partial momentum
    -- 0 = No momentum confirmation
    sma_mom_score INTEGER,
    sma_spread NUMERIC(12, 6),                -- SMA9 - SMA21
    sma_spread_pct NUMERIC(12, 6),            -- Spread as % of price
    sma_spread_roc NUMERIC(12, 4),            -- Rate of change of spread
    sma_spread_aligned BOOLEAN,               -- Spread positive (LONG) / negative (SHORT)
    sma_spread_expanding BOOLEAN,             -- ROC > 5% (LONG) / < -5% (SHORT)

    -- CONT-03: Volume Thrust Score (0-2 points)
    -- 2 = Strong volume confirmation
    -- 1 = Partial confirmation
    -- 0 = No volume support
    vol_thrust_score INTEGER,
    vol_roc NUMERIC(10, 4),                   -- Current volume vs 20-bar avg
    vol_delta_5 NUMERIC(12, 4),               -- Sum of bar deltas over 5 bars
    vol_roc_strong BOOLEAN,                   -- vol_roc > 20%
    vol_delta_aligned BOOLEAN,                -- Delta aligned with direction

    -- CONT-04: Pullback Quality Score (0-2 points)
    -- 2 = High quality pullback (low delta absorption)
    -- 1 = Acceptable pullback or not in pullback
    -- 0 = Poor pullback quality (reversal risk)
    pullback_score INTEGER,
    in_pullback BOOLEAN,                      -- Currently in pullback?
    pullback_delta_ratio NUMERIC(8, 4),       -- pullback_delta / thrust_delta

    -- CONTINUATION COMPOSITE (0-10)
    continuation_score INTEGER,
    continuation_label VARCHAR(10),           -- STRONG, GOOD, WEAK, AVOID

    -- =========================================================================
    -- REJECTION INDICATORS (REJ-01 to REJ-05)
    -- Total: 0-11 points
    -- =========================================================================

    -- REJ-01: Structure Divergence Score (0-2 points)
    -- 2 = Ideal exhaustion setup (HTF trend, LTF overextension)
    -- 1 = Partial setup
    -- 0 = No divergence signal
    struct_div_score INTEGER,
    htf_aligned BOOLEAN,                      -- H4/H1 aligned with trade
    ltf_divergent BOOLEAN,                    -- M5/M15 divergent from trade

    -- REJ-02: SMA Exhaustion Score (0-3 points)
    -- 3 = Strong exhaustion (tight AND contracting)
    -- 2 = Good exhaustion signal
    -- 1 = Partial exhaustion
    -- 0 = No exhaustion (trend still strong)
    sma_exhst_score INTEGER,
    sma_spread_contracting BOOLEAN,           -- ROC < -10%
    sma_spread_very_tight BOOLEAN,            -- spread_pct < Q1 threshold (0.15%)
    sma_spread_tight BOOLEAN,                 -- spread_pct < Q2 threshold (0.25%)

    -- REJ-03: Delta Absorption Score (0-2 points)
    -- 2 = Strong absorption (high delta, low price move)
    -- 1 = Moderate absorption
    -- 0 = Normal delta/price relationship
    delta_abs_score INTEGER,
    absorption_ratio NUMERIC(10, 4),          -- delta_normalized / price_change_pct

    -- REJ-04: Volume Climax Score (0-2 points)
    -- 2 = Volume climax signal (spike or declining from high)
    -- 1 = Partial signal
    -- 0 = No climax indication
    vol_climax_score INTEGER,
    vol_roc_q5 BOOLEAN,                       -- vol_roc > 50% (top quintile)
    vol_declining BOOLEAN,                    -- vol_roc < vol_roc_prev

    -- REJ-05: CVD Extreme Score (0-2 points)
    -- 2 = Extreme CVD (strong exhaustion signal)
    -- 1 = Moderate extreme
    -- 0 = CVD in normal range
    cvd_extr_score INTEGER,
    cvd_slope NUMERIC(18, 6),                 -- Linear regression slope (can be large)
    cvd_slope_normalized NUMERIC(18, 6),      -- Normalized CVD slope
    cvd_extreme BOOLEAN,                      -- In Q1 (LONG) or Q5 (SHORT)

    -- REJECTION COMPOSITE (0-11)
    rejection_score INTEGER,
    rejection_label VARCHAR(10),              -- STRONG, GOOD, WEAK, AVOID

    -- =========================================================================
    -- OUTCOME VALIDATION (populated by later analysis)
    -- =========================================================================
    trade_outcome VARCHAR(10),                -- WIN, LOSS, PARTIAL
    outcome_validated BOOLEAN DEFAULT FALSE,

    -- =========================================================================
    -- METADATA
    -- =========================================================================
    calculation_version VARCHAR(10) DEFAULT '1.0',
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- =========================================================================
    -- CONSTRAINTS
    -- =========================================================================
    CONSTRAINT indicator_refinement_fkey
        FOREIGN KEY (trade_id) REFERENCES trades (trade_id) ON DELETE CASCADE
);

-- ============================================================================
-- INDEXES (for common query patterns)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_indref_date ON indicator_refinement (date DESC);
CREATE INDEX IF NOT EXISTS idx_indref_ticker ON indicator_refinement (ticker);
CREATE INDEX IF NOT EXISTS idx_indref_model ON indicator_refinement (model);
CREATE INDEX IF NOT EXISTS idx_indref_type ON indicator_refinement (trade_type);
CREATE INDEX IF NOT EXISTS idx_indref_cont_score ON indicator_refinement (continuation_score);
CREATE INDEX IF NOT EXISTS idx_indref_rej_score ON indicator_refinement (rejection_score);
CREATE INDEX IF NOT EXISTS idx_indref_cont_label ON indicator_refinement (continuation_label);
CREATE INDEX IF NOT EXISTS idx_indref_rej_label ON indicator_refinement (rejection_label);

-- ============================================================================
-- UPDATE TRIGGER (auto-update updated_at timestamp)
-- ============================================================================
CREATE OR REPLACE FUNCTION update_indicator_refinement_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS indicator_refinement_updated ON indicator_refinement;
CREATE TRIGGER indicator_refinement_updated
    BEFORE UPDATE ON indicator_refinement
    FOR EACH ROW
    EXECUTE FUNCTION update_indicator_refinement_timestamp();

-- ============================================================================
-- TABLE COMMENTS
-- ============================================================================
COMMENT ON TABLE indicator_refinement IS 'Continuation/Rejection indicator scores for trade qualification (Epoch Indicator Model v1.0)';

COMMENT ON COLUMN indicator_refinement.trade_type IS 'CONTINUATION (EPCH01/03) or REJECTION (EPCH02/04)';
COMMENT ON COLUMN indicator_refinement.continuation_score IS 'Composite score 0-10 for continuation trades (MTF + SMA + Volume + Pullback)';
COMMENT ON COLUMN indicator_refinement.rejection_score IS 'Composite score 0-11 for rejection trades (Structure + Exhaustion + Absorption + Climax + CVD)';
COMMENT ON COLUMN indicator_refinement.continuation_label IS 'STRONG (8-10), GOOD (6-7), WEAK (4-5), AVOID (0-3)';
COMMENT ON COLUMN indicator_refinement.rejection_label IS 'STRONG (9-11), GOOD (6-8), WEAK (4-5), AVOID (0-3)';

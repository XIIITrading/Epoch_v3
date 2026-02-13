-- ============================================================================
-- EPOCH TRADING SYSTEM - MIGRATION: ai_predictions v1 -> v2
-- Drops old table and recreates with live DOW AI format
-- XIII Trading LLC
--
-- WARNING: This will DELETE all existing data in ai_predictions
-- ============================================================================

-- Drop existing table and all dependencies
DROP TABLE IF EXISTS ai_predictions CASCADE;

-- Recreate with new schema (live DOW AI format)
CREATE TABLE ai_predictions (
    -- =========================================================================
    -- PRIMARY KEY
    -- =========================================================================
    id SERIAL PRIMARY KEY,

    -- =========================================================================
    -- TRADE REFERENCE
    -- =========================================================================
    trade_id VARCHAR(50) NOT NULL UNIQUE,

    -- =========================================================================
    -- TRADE CONTEXT (denormalized for query performance)
    -- =========================================================================
    ticker VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    direction VARCHAR(10) NOT NULL,
    model VARCHAR(10) NOT NULL,
    zone_type VARCHAR(20) NOT NULL,
    entry_price NUMERIC(12, 4),
    entry_time TIME WITHOUT TIME ZONE,

    -- =========================================================================
    -- AI PREDICTION (matches live DOW AI format exactly)
    -- =========================================================================
    prediction VARCHAR(20) NOT NULL,           -- 'TRADE' or 'NO_TRADE'
    confidence VARCHAR(10) NOT NULL,           -- 'HIGH', 'MEDIUM', 'LOW'
    reasoning TEXT,                            -- Full response from Claude

    -- =========================================================================
    -- LIVE-FORMAT INDICATORS (matches Entry Qualifier exactly)
    -- =========================================================================
    -- Candle Range
    candle_pct NUMERIC(6, 4),                  -- e.g., 0.18 (percentage)b
    candle_status VARCHAR(10),                 -- 'GOOD', 'OK', 'SKIP'

    -- Volume Delta
    vol_delta NUMERIC(15, 2),                  -- e.g., 45000
    vol_delta_status VARCHAR(15),              -- 'FAVORABLE', 'NEUTRAL', 'WEAK'

    -- Volume ROC
    vol_roc NUMERIC(10, 2),                    -- e.g., 65 (percentage)
    vol_roc_status VARCHAR(15),                -- 'ELEVATED', 'NORMAL'

    -- SMA Configuration
    sma VARCHAR(10),                           -- 'BULL', 'BEAR', 'NEUT'

    -- H1 Structure
    h1_struct VARCHAR(10),                     -- 'BULL', 'BEAR', 'NEUT'

    -- Summary snapshot
    snapshot TEXT,                             -- 2-3 sentence summary

    -- =========================================================================
    -- ACTUAL OUTCOME (from trades table)
    -- =========================================================================
    actual_outcome VARCHAR(10),               -- 'WIN' or 'LOSS'
    actual_pnl_r NUMERIC(6, 2),

    -- =========================================================================
    -- PREDICTION ACCURACY
    -- =========================================================================
    prediction_correct BOOLEAN,

    -- =========================================================================
    -- METADATA
    -- =========================================================================
    prompt_version VARCHAR(10) DEFAULT 'v2.0',
    model_used VARCHAR(50) DEFAULT 'claude-sonnet-4-20250514',
    tokens_input INTEGER,
    tokens_output INTEGER,
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- =========================================================================
    -- CONSTRAINTS
    -- =========================================================================
    CONSTRAINT ai_predictions_trade_id_fkey FOREIGN KEY (trade_id)
        REFERENCES trades (trade_id) ON DELETE CASCADE,
    CONSTRAINT ai_predictions_prediction_check
        CHECK (prediction IN ('TRADE', 'NO_TRADE')),
    CONSTRAINT ai_predictions_confidence_check
        CHECK (confidence IN ('HIGH', 'MEDIUM', 'LOW')),
    CONSTRAINT ai_predictions_outcome_check
        CHECK (actual_outcome IN ('WIN', 'LOSS', NULL)),
    CONSTRAINT ai_predictions_candle_status_check
        CHECK (candle_status IN ('GOOD', 'OK', 'SKIP', NULL)),
    CONSTRAINT ai_predictions_vol_delta_status_check
        CHECK (vol_delta_status IN ('FAVORABLE', 'NEUTRAL', 'WEAK', NULL)),
    CONSTRAINT ai_predictions_vol_roc_status_check
        CHECK (vol_roc_status IN ('ELEVATED', 'NORMAL', NULL)),
    CONSTRAINT ai_predictions_sma_check
        CHECK (sma IN ('BULL', 'BEAR', 'NEUT', NULL)),
    CONSTRAINT ai_predictions_h1_struct_check
        CHECK (h1_struct IN ('BULL', 'BEAR', 'NEUT', NULL))
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Standard filters
CREATE INDEX idx_aip_date ON ai_predictions (trade_date DESC);
CREATE INDEX idx_aip_ticker ON ai_predictions (ticker);
CREATE INDEX idx_aip_model ON ai_predictions (model);
CREATE INDEX idx_aip_direction ON ai_predictions (direction);
CREATE INDEX idx_aip_prediction ON ai_predictions (prediction);
CREATE INDEX idx_aip_confidence ON ai_predictions (confidence);
CREATE INDEX idx_aip_correct ON ai_predictions (prediction_correct);

-- Composite indexes for accuracy analysis
CREATE INDEX idx_aip_pred_correct ON ai_predictions (prediction, prediction_correct);
CREATE INDEX idx_aip_model_correct ON ai_predictions (model, prediction_correct);
CREATE INDEX idx_aip_conf_correct ON ai_predictions (confidence, prediction_correct);

-- Live-format indicator indexes
CREATE INDEX idx_aip_candle_status ON ai_predictions (candle_status);
CREATE INDEX idx_aip_vol_delta_status ON ai_predictions (vol_delta_status);
CREATE INDEX idx_aip_vol_roc_status ON ai_predictions (vol_roc_status);
CREATE INDEX idx_aip_sma ON ai_predictions (sma);
CREATE INDEX idx_aip_h1_struct ON ai_predictions (h1_struct);

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE ai_predictions IS 'AI-generated trade predictions matching live DOW AI format';
COMMENT ON COLUMN ai_predictions.prediction IS 'DOW AI recommendation: TRADE or NO_TRADE';
COMMENT ON COLUMN ai_predictions.confidence IS 'Overall confidence: HIGH, MEDIUM, LOW';
COMMENT ON COLUMN ai_predictions.prediction_correct IS 'TRUE if TRADE=WIN or NO_TRADE=LOSS';
COMMENT ON COLUMN ai_predictions.candle_pct IS 'Candle range percentage (5-bar avg)';
COMMENT ON COLUMN ai_predictions.candle_status IS 'GOOD (>=0.15%), OK (0.12-0.15%), SKIP (<0.12%)';
COMMENT ON COLUMN ai_predictions.vol_delta IS 'Volume delta (5-bar avg)';
COMMENT ON COLUMN ai_predictions.vol_delta_status IS 'FAVORABLE, NEUTRAL, or WEAK based on direction';
COMMENT ON COLUMN ai_predictions.vol_roc IS 'Volume ROC percentage (5-bar avg)';
COMMENT ON COLUMN ai_predictions.vol_roc_status IS 'ELEVATED (>=30%) or NORMAL (<30%)';
COMMENT ON COLUMN ai_predictions.sma IS 'SMA configuration: BULL, BEAR, or NEUT';
COMMENT ON COLUMN ai_predictions.h1_struct IS 'H1 market structure: BULL, BEAR, or NEUT';
COMMENT ON COLUMN ai_predictions.snapshot IS '2-3 sentence trade summary';

-- ============================================================================
-- ACCURACY CALCULATION TRIGGER
-- ============================================================================
CREATE OR REPLACE FUNCTION calculate_prediction_correct()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.prediction = 'TRADE' AND NEW.actual_outcome = 'WIN' THEN
        NEW.prediction_correct := TRUE;
    ELSIF NEW.prediction = 'NO_TRADE' AND NEW.actual_outcome = 'LOSS' THEN
        NEW.prediction_correct := TRUE;
    ELSIF NEW.actual_outcome IS NOT NULL THEN
        NEW.prediction_correct := FALSE;
    ELSE
        NEW.prediction_correct := NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_calculate_prediction_correct ON ai_predictions;
CREATE TRIGGER trigger_calculate_prediction_correct
    BEFORE INSERT OR UPDATE ON ai_predictions
    FOR EACH ROW
    EXECUTE FUNCTION calculate_prediction_correct();

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
SELECT 'ai_predictions table recreated with live DOW AI format (v2.0)' as status;

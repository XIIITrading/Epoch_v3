-- ============================================================================
-- DOW AI v3.0 Schema Migration
-- Dual-Pass Analysis System
-- ============================================================================
--
-- This migration creates:
-- 1. dual_pass_analysis table - stores both pass results with computed metrics
-- 2. v_dual_pass_accuracy view - quick accuracy comparison
-- 3. Adds user_notes to ai_predictions for live entry qualifier
--
-- Run this in Supabase SQL Editor
-- ============================================================================

-- ============================================================================
-- PART 1: Create dual_pass_analysis table
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.dual_pass_analysis (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    trade_id VARCHAR(50) UNIQUE NOT NULL,

    -- Trade Identification (from trades table)
    ticker VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    entry_time TIME WITHOUT TIME ZONE NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('LONG', 'SHORT')),
    entry_price NUMERIC(12, 4),

    -- Trade Context (from trades table)
    model VARCHAR(10),                -- EPCH1, EPCH2, EPCH3, EPCH4
    zone_type VARCHAR(20),            -- PRIMARY, SECONDARY

    -- Pass 1: Trader's Eye (Raw M1 bars + indicators, no backtested context)
    pass1_decision VARCHAR(10) CHECK (pass1_decision IN ('TRADE', 'NO_TRADE')),
    pass1_confidence VARCHAR(10) CHECK (pass1_confidence IN ('HIGH', 'MEDIUM', 'LOW')),
    pass1_reasoning TEXT,
    pass1_tokens_input INTEGER,
    pass1_tokens_output INTEGER,
    pass1_latency_ms INTEGER,

    -- Pass 2: System Decision (Raw M1 bars + indicators + backtested edges)
    pass2_decision VARCHAR(10) CHECK (pass2_decision IN ('TRADE', 'NO_TRADE')),
    pass2_confidence VARCHAR(10) CHECK (pass2_confidence IN ('HIGH', 'MEDIUM', 'LOW')),
    pass2_reasoning TEXT,
    pass2_tokens_input INTEGER,
    pass2_tokens_output INTEGER,
    pass2_latency_ms INTEGER,

    -- Extracted Indicators from Pass 2 Response
    -- (Claude extracts these from the M1 bar data)
    candle_pct NUMERIC(8, 4),
    candle_status VARCHAR(15) CHECK (candle_status IN ('FAVORABLE', 'NEUTRAL', 'UNFAVORABLE', 'SKIP')),
    vol_delta NUMERIC(15, 2),
    vol_delta_status VARCHAR(15) CHECK (vol_delta_status IN ('ALIGNED', 'NEUTRAL', 'OPPOSING')),
    vol_roc NUMERIC(10, 2),
    vol_roc_status VARCHAR(15) CHECK (vol_roc_status IN ('ELEVATED', 'NORMAL', 'LOW')),
    sma_spread NUMERIC(10, 4),
    sma_status VARCHAR(15) CHECK (sma_status IN ('ALIGNED', 'NEUTRAL', 'OPPOSING')),
    h1_structure VARCHAR(10),
    h1_status VARCHAR(15) CHECK (h1_status IN ('ALIGNED', 'NEUTRAL', 'OPPOSING')),

    -- Agreement Metric (computed)
    passes_agree BOOLEAN GENERATED ALWAYS AS (pass1_decision = pass2_decision) STORED,

    -- Actual Outcome (from trades table)
    actual_outcome VARCHAR(10) CHECK (actual_outcome IN ('WIN', 'LOSS')),
    actual_pnl_r NUMERIC(6, 2),

    -- Correctness (computed after outcome known)
    -- TRADE prediction is correct if outcome is WIN
    -- NO_TRADE prediction is correct if outcome is LOSS
    pass1_correct BOOLEAN GENERATED ALWAYS AS (
        CASE
            WHEN actual_outcome IS NULL THEN NULL
            WHEN pass1_decision = 'TRADE' AND actual_outcome = 'WIN' THEN TRUE
            WHEN pass1_decision = 'NO_TRADE' AND actual_outcome = 'LOSS' THEN TRUE
            ELSE FALSE
        END
    ) STORED,

    pass2_correct BOOLEAN GENERATED ALWAYS AS (
        CASE
            WHEN actual_outcome IS NULL THEN NULL
            WHEN pass2_decision = 'TRADE' AND actual_outcome = 'WIN' THEN TRUE
            WHEN pass2_decision = 'NO_TRADE' AND actual_outcome = 'LOSS' THEN TRUE
            ELSE FALSE
        END
    ) STORED,

    -- Disagreement Analysis (who was right when they disagreed?)
    disagreement_winner VARCHAR(15) GENERATED ALWAYS AS (
        CASE
            WHEN pass1_decision = pass2_decision THEN NULL  -- They agreed
            WHEN pass1_decision = 'TRADE' AND actual_outcome = 'WIN' THEN 'PASS1'
            WHEN pass1_decision = 'NO_TRADE' AND actual_outcome = 'LOSS' THEN 'PASS1'
            WHEN pass2_decision = 'TRADE' AND actual_outcome = 'WIN' THEN 'PASS2'
            WHEN pass2_decision = 'NO_TRADE' AND actual_outcome = 'LOSS' THEN 'PASS2'
            ELSE 'BOTH_WRONG'
        END
    ) STORED,

    -- Metadata
    prompt_version VARCHAR(10) DEFAULT 'v3.0',
    model_used VARCHAR(50) DEFAULT 'claude-sonnet-4-20250514',
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign Key to trades table
    CONSTRAINT dual_pass_trade_id_fkey FOREIGN KEY (trade_id)
        REFERENCES trades(trade_id) ON DELETE CASCADE
) TABLESPACE pg_default;

-- ============================================================================
-- PART 2: Create indexes for common queries
-- ============================================================================

-- Primary lookup indexes
CREATE INDEX IF NOT EXISTS idx_dpa_trade_date ON public.dual_pass_analysis(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_dpa_ticker ON public.dual_pass_analysis(ticker);
CREATE INDEX IF NOT EXISTS idx_dpa_direction ON public.dual_pass_analysis(direction);
CREATE INDEX IF NOT EXISTS idx_dpa_model ON public.dual_pass_analysis(model);

-- Analysis indexes
CREATE INDEX IF NOT EXISTS idx_dpa_passes_agree ON public.dual_pass_analysis(passes_agree);
CREATE INDEX IF NOT EXISTS idx_dpa_pass1_correct ON public.dual_pass_analysis(pass1_correct);
CREATE INDEX IF NOT EXISTS idx_dpa_pass2_correct ON public.dual_pass_analysis(pass2_correct);
CREATE INDEX IF NOT EXISTS idx_dpa_disagreement ON public.dual_pass_analysis(disagreement_winner)
    WHERE disagreement_winner IS NOT NULL;

-- Confidence analysis
CREATE INDEX IF NOT EXISTS idx_dpa_pass1_confidence ON public.dual_pass_analysis(pass1_confidence);
CREATE INDEX IF NOT EXISTS idx_dpa_pass2_confidence ON public.dual_pass_analysis(pass2_confidence);

-- Indicator analysis (Pass 2 extracted)
CREATE INDEX IF NOT EXISTS idx_dpa_h1_status ON public.dual_pass_analysis(h1_status);
CREATE INDEX IF NOT EXISTS idx_dpa_sma_status ON public.dual_pass_analysis(sma_status);
CREATE INDEX IF NOT EXISTS idx_dpa_candle_status ON public.dual_pass_analysis(candle_status);

-- ============================================================================
-- PART 3: Create accuracy comparison view
-- ============================================================================

CREATE OR REPLACE VIEW public.v_dual_pass_accuracy AS
SELECT
    direction,
    COUNT(*) AS total_trades,

    -- Pass 1 (Trader's Eye) metrics
    SUM(CASE WHEN pass1_decision = 'TRADE' THEN 1 ELSE 0 END) AS pass1_trade_calls,
    ROUND(SUM(CASE WHEN pass1_decision = 'TRADE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pass1_trade_rate_pct,
    SUM(CASE WHEN pass1_correct THEN 1 ELSE 0 END) AS pass1_correct_count,
    ROUND(AVG(CASE WHEN pass1_correct THEN 1.0 ELSE 0.0 END) * 100, 1) AS pass1_accuracy_pct,

    -- Pass 2 (System Decision) metrics
    SUM(CASE WHEN pass2_decision = 'TRADE' THEN 1 ELSE 0 END) AS pass2_trade_calls,
    ROUND(SUM(CASE WHEN pass2_decision = 'TRADE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pass2_trade_rate_pct,
    SUM(CASE WHEN pass2_correct THEN 1 ELSE 0 END) AS pass2_correct_count,
    ROUND(AVG(CASE WHEN pass2_correct THEN 1.0 ELSE 0.0 END) * 100, 1) AS pass2_accuracy_pct,

    -- Agreement metrics
    SUM(CASE WHEN passes_agree THEN 1 ELSE 0 END) AS agreements,
    ROUND(AVG(CASE WHEN passes_agree THEN 1.0 ELSE 0.0 END) * 100, 1) AS agreement_rate_pct,

    -- When disagreed, who won?
    SUM(CASE WHEN disagreement_winner = 'PASS1' THEN 1 ELSE 0 END) AS pass1_wins_disagreement,
    SUM(CASE WHEN disagreement_winner = 'PASS2' THEN 1 ELSE 0 END) AS pass2_wins_disagreement,
    SUM(CASE WHEN disagreement_winner = 'BOTH_WRONG' THEN 1 ELSE 0 END) AS both_wrong_disagreement

FROM public.dual_pass_analysis
WHERE actual_outcome IS NOT NULL
GROUP BY direction;

COMMENT ON VIEW public.v_dual_pass_accuracy IS
'DOW AI v3.0 - Comparison of Pass 1 (Trader''s Eye) vs Pass 2 (System Decision) accuracy';

-- ============================================================================
-- PART 4: Create detailed analysis view
-- ============================================================================

CREATE OR REPLACE VIEW public.v_dual_pass_detailed AS
SELECT
    direction,
    model,

    -- Total counts
    COUNT(*) AS total_trades,
    SUM(CASE WHEN actual_outcome = 'WIN' THEN 1 ELSE 0 END) AS actual_wins,
    ROUND(AVG(CASE WHEN actual_outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 1) AS base_win_rate,

    -- Pass 1 breakdown
    SUM(CASE WHEN pass1_decision = 'TRADE' THEN 1 ELSE 0 END) AS pass1_trades,
    SUM(CASE WHEN pass1_decision = 'TRADE' AND actual_outcome = 'WIN' THEN 1 ELSE 0 END) AS pass1_trade_wins,
    ROUND(
        CASE WHEN SUM(CASE WHEN pass1_decision = 'TRADE' THEN 1 ELSE 0 END) > 0
        THEN SUM(CASE WHEN pass1_decision = 'TRADE' AND actual_outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0
             / SUM(CASE WHEN pass1_decision = 'TRADE' THEN 1 ELSE 0 END)
        ELSE 0 END, 1
    ) AS pass1_trade_win_rate,

    -- Pass 2 breakdown
    SUM(CASE WHEN pass2_decision = 'TRADE' THEN 1 ELSE 0 END) AS pass2_trades,
    SUM(CASE WHEN pass2_decision = 'TRADE' AND actual_outcome = 'WIN' THEN 1 ELSE 0 END) AS pass2_trade_wins,
    ROUND(
        CASE WHEN SUM(CASE WHEN pass2_decision = 'TRADE' THEN 1 ELSE 0 END) > 0
        THEN SUM(CASE WHEN pass2_decision = 'TRADE' AND actual_outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0
             / SUM(CASE WHEN pass2_decision = 'TRADE' THEN 1 ELSE 0 END)
        ELSE 0 END, 1
    ) AS pass2_trade_win_rate,

    -- Improvement metrics
    ROUND(AVG(CASE WHEN pass2_correct THEN 1.0 ELSE 0.0 END) * 100, 1)
        - ROUND(AVG(CASE WHEN pass1_correct THEN 1.0 ELSE 0.0 END) * 100, 1) AS pass2_accuracy_lift_pp

FROM public.dual_pass_analysis
WHERE actual_outcome IS NOT NULL
GROUP BY direction, model
ORDER BY direction, model;

COMMENT ON VIEW public.v_dual_pass_detailed IS
'DOW AI v3.0 - Detailed breakdown by direction and model';

-- ============================================================================
-- PART 5: Add user_notes to ai_predictions for live entry qualifier
-- ============================================================================

-- Add user_notes column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ai_predictions'
        AND column_name = 'user_notes'
    ) THEN
        ALTER TABLE public.ai_predictions
        ADD COLUMN user_notes TEXT;

        COMMENT ON COLUMN public.ai_predictions.user_notes IS
        'User observations/notes entered before AI analysis (live entry qualifier)';
    END IF;
END $$;

-- ============================================================================
-- PART 6: Analysis Queries (save these for reference)
-- ============================================================================

-- Query 1: Overall accuracy comparison
-- SELECT * FROM v_dual_pass_accuracy;

-- Query 2: When passes disagree, who's right more often?
/*
SELECT
    disagreement_winner,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct
FROM dual_pass_analysis
WHERE NOT passes_agree AND actual_outcome IS NOT NULL
GROUP BY disagreement_winner
ORDER BY count DESC;
*/

-- Query 3: Confidence calibration - is HIGH confidence actually more accurate?
/*
SELECT
    'Pass 1' as pass_type,
    pass1_confidence as confidence,
    COUNT(*) as predictions,
    ROUND(AVG(CASE WHEN pass1_correct THEN 1.0 ELSE 0.0 END) * 100, 1) as accuracy_pct
FROM dual_pass_analysis
WHERE pass1_confidence IS NOT NULL AND actual_outcome IS NOT NULL
GROUP BY pass1_confidence

UNION ALL

SELECT
    'Pass 2' as pass_type,
    pass2_confidence as confidence,
    COUNT(*) as predictions,
    ROUND(AVG(CASE WHEN pass2_correct THEN 1.0 ELSE 0.0 END) * 100, 1) as accuracy_pct
FROM dual_pass_analysis
WHERE pass2_confidence IS NOT NULL AND actual_outcome IS NOT NULL
GROUP BY pass2_confidence
ORDER BY pass_type, confidence;
*/

-- Query 4: Where did backtested edges help most? (Pass 2 correct, Pass 1 wrong)
/*
SELECT
    direction,
    h1_status,
    sma_status,
    COUNT(*) as trades,
    SUM(CASE WHEN pass2_correct AND NOT pass1_correct THEN 1 ELSE 0 END) as context_helped,
    SUM(CASE WHEN pass1_correct AND NOT pass2_correct THEN 1 ELSE 0 END) as context_hurt
FROM dual_pass_analysis
WHERE actual_outcome IS NOT NULL
GROUP BY direction, h1_status, sma_status
HAVING COUNT(*) >= 5
ORDER BY context_helped DESC;
*/

-- Query 5: Sample disagreement cases for manual review
/*
SELECT
    trade_id, ticker, direction, trade_date, entry_time,
    pass1_decision, pass1_confidence, pass1_reasoning,
    pass2_decision, pass2_confidence, pass2_reasoning,
    actual_outcome, disagreement_winner
FROM dual_pass_analysis
WHERE NOT passes_agree
ORDER BY trade_date DESC
LIMIT 20;
*/

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

COMMENT ON TABLE public.dual_pass_analysis IS
'DOW AI v3.0 dual-pass analysis results comparing:
- Pass 1 (Trader''s Eye): Raw M1 bars with indicators, no backtested context
- Pass 2 (System Decision): Raw M1 bars + learned edges from backtesting
Used to measure the value of backtested knowledge in prediction accuracy.';

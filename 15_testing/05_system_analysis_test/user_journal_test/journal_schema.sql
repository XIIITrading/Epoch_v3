-- =============================================================================
-- User Journal Schema — Subjective Selection Journal
-- =============================================================================
-- Stores the Q&A responses from the daily selection process.
-- Each row = one ticker selection event with subjective reasoning.
-- Combined with objective data (zones, structure, bar_data) for aggregate analysis.
--
-- Run this once in Supabase SQL Editor to create the table.
-- =============================================================================

CREATE TABLE IF NOT EXISTS journal_selections (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    ticker          VARCHAR(10) NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    -- Selection metadata
    selection_type  VARCHAR(20) NOT NULL,        -- 'SELECTED' or 'SKIPPED'
    selection_rank  INTEGER,                      -- 1-10 order of conviction (1=highest)

    -- Subjective Q&A responses
    thesis          TEXT,                          -- Why did you select/skip this ticker?
    directional_bias VARCHAR(20),                 -- BULL, BEAR, NEUTRAL
    bias_reasoning  TEXT,                          -- What drives your directional bias?
    confidence      INTEGER CHECK (confidence BETWEEN 1 AND 5),  -- 1=low, 5=high
    invalidation    TEXT,                          -- What would invalidate this pick?
    zone_focus      TEXT,                          -- Which zone are you watching and why?
    concerns        TEXT,                          -- Any hesitation or red flags?
    market_context  TEXT,                          -- Overall market read for the day

    -- Post-session review (filled end-of-day)
    actual_outcome  VARCHAR(20),                  -- WIN, LOSS, NO_TRADE, MISSED
    outcome_notes   TEXT,                          -- What happened and what did you learn?
    hindsight_score INTEGER CHECK (hindsight_score BETWEEN 1 AND 5),  -- Was this a good pick in hindsight?

    -- Constraints
    UNIQUE(date, ticker)
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_journal_date ON journal_selections(date);
CREATE INDEX IF NOT EXISTS idx_journal_ticker ON journal_selections(ticker);
CREATE INDEX IF NOT EXISTS idx_journal_type ON journal_selections(selection_type);
CREATE INDEX IF NOT EXISTS idx_journal_confidence ON journal_selections(confidence);

-- =============================================================================
-- Daily Market Context (one row per trading day)
-- =============================================================================
CREATE TABLE IF NOT EXISTS journal_daily_context (
    date            DATE PRIMARY KEY,
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    -- Pre-market read
    market_regime   VARCHAR(20),                  -- BULL, BEAR, NEUTRAL, CHOPPY
    key_events      TEXT,                          -- News, earnings, FOMC, etc.
    spy_bias        VARCHAR(20),                   -- BULL, BEAR, NEUTRAL
    overall_plan    TEXT,                          -- What's your plan for today?

    -- Post-session review
    session_grade   VARCHAR(2),                    -- A, B, C, D, F
    session_notes   TEXT,                          -- What went well / what didn't
    rule_adherence  INTEGER CHECK (rule_adherence BETWEEN 1 AND 5),  -- Did you follow your rules?
    emotional_state VARCHAR(20)                    -- CALM, ANXIOUS, CONFIDENT, TILTED, FOCUSED
);

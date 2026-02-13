-- ============================================================================
-- Epoch Trading System - Table: trade_analysis
-- Stores Claude AI analysis responses for trades.
-- Source: 10_training module
-- ============================================================================

CREATE TABLE IF NOT EXISTS trade_analysis (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key to trades
    trade_id VARCHAR(50) NOT NULL REFERENCES trades(trade_id) ON DELETE CASCADE,

    -- Analysis type: pre_trade or post_trade
    analysis_type TEXT NOT NULL CHECK (analysis_type IN ('pre_trade', 'post_trade')),

    -- The prompt that was sent to Claude (for reference)
    prompt_text TEXT,

    -- Claude's analysis response (markdown format)
    response_text TEXT NOT NULL,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- One analysis per type per trade
    UNIQUE(trade_id, analysis_type)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_trade_analysis_trade_id ON trade_analysis(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_analysis_type ON trade_analysis(analysis_type);
CREATE INDEX IF NOT EXISTS idx_trade_analysis_created_at ON trade_analysis(created_at DESC);

-- Comments
COMMENT ON TABLE trade_analysis IS 'Claude AI analysis responses for trades';
COMMENT ON COLUMN trade_analysis.analysis_type IS 'Type of analysis: pre_trade or post_trade';
COMMENT ON COLUMN trade_analysis.prompt_text IS 'The prompt sent to Claude (optional, for reference)';
COMMENT ON COLUMN trade_analysis.response_text IS 'Claude response in markdown format';

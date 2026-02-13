-- ============================================================================
-- Epoch Trading System - Table 04: hvn_pocs
-- High Volume Node Point of Control levels per ticker per day.
-- Source: bar_data worksheet, time_hvn section (rows 59-68)
-- ============================================================================

CREATE TABLE IF NOT EXISTS hvn_pocs (
    -- Composite Primary Key
    date DATE NOT NULL,
    ticker_id VARCHAR(10) NOT NULL,  -- t1, t2, ... t10

    -- Ticker Info
    ticker VARCHAR(10) NOT NULL,

    -- Epoch Analysis Period
    epoch_start_date DATE,  -- User-defined start date for volume analysis

    -- HVN POC Levels (ranked by volume, non-overlapping)
    poc_1 DECIMAL(10, 2),  -- Highest volume POC
    poc_2 DECIMAL(10, 2),
    poc_3 DECIMAL(10, 2),
    poc_4 DECIMAL(10, 2),
    poc_5 DECIMAL(10, 2),
    poc_6 DECIMAL(10, 2),
    poc_7 DECIMAL(10, 2),
    poc_8 DECIMAL(10, 2),
    poc_9 DECIMAL(10, 2),
    poc_10 DECIMAL(10, 2),  -- 10th highest volume POC

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    PRIMARY KEY (date, ticker_id),
    FOREIGN KEY (date) REFERENCES daily_sessions(date) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_hvn_pocs_ticker ON hvn_pocs(ticker);
CREATE INDEX IF NOT EXISTS idx_hvn_pocs_date ON hvn_pocs(date DESC);

-- Update trigger
DROP TRIGGER IF EXISTS update_hvn_pocs_updated_at ON hvn_pocs;
CREATE TRIGGER update_hvn_pocs_updated_at
    BEFORE UPDATE ON hvn_pocs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE hvn_pocs IS 'High Volume Node POC levels from epoch volume profile analysis';
COMMENT ON COLUMN hvn_pocs.epoch_start_date IS 'Start date for the volume profile epoch analysis';
COMMENT ON COLUMN hvn_pocs.poc_1 IS 'Highest volume POC level';
COMMENT ON COLUMN hvn_pocs.poc_10 IS '10th highest volume POC level (non-overlapping with others)';

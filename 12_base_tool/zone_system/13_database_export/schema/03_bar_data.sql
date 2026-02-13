-- ============================================================================
-- Epoch Trading System - Table 03: bar_data
-- OHLC, ATR, Options levels, and Camarilla pivots per ticker per day.
-- Source: bar_data worksheet (wide format - all metrics in one row)
-- ============================================================================

CREATE TABLE IF NOT EXISTS bar_data (
    -- Composite Primary Key
    date DATE NOT NULL,
    ticker_id VARCHAR(10) NOT NULL,  -- t1, t2, ... t10

    -- Ticker Info
    ticker VARCHAR(10) NOT NULL,
    price DECIMAL(10, 2),  -- Current/closing price

    -- Monthly OHLC (Current Month)
    m1_open DECIMAL(10, 2),
    m1_high DECIMAL(10, 2),
    m1_low DECIMAL(10, 2),
    m1_close DECIMAL(10, 2),

    -- Monthly OHLC (Prior Month)
    m1_prior_open DECIMAL(10, 2),
    m1_prior_high DECIMAL(10, 2),
    m1_prior_low DECIMAL(10, 2),
    m1_prior_close DECIMAL(10, 2),

    -- Weekly OHLC (Current Week)
    w1_open DECIMAL(10, 2),
    w1_high DECIMAL(10, 2),
    w1_low DECIMAL(10, 2),
    w1_close DECIMAL(10, 2),

    -- Weekly OHLC (Prior Week)
    w1_prior_open DECIMAL(10, 2),
    w1_prior_high DECIMAL(10, 2),
    w1_prior_low DECIMAL(10, 2),
    w1_prior_close DECIMAL(10, 2),

    -- Daily OHLC (Current Day)
    d1_open DECIMAL(10, 2),
    d1_high DECIMAL(10, 2),
    d1_low DECIMAL(10, 2),
    d1_close DECIMAL(10, 2),

    -- Daily OHLC (Prior Day)
    d1_prior_open DECIMAL(10, 2),
    d1_prior_high DECIMAL(10, 2),
    d1_prior_low DECIMAL(10, 2),
    d1_prior_close DECIMAL(10, 2),

    -- Overnight Levels
    d1_overnight_high DECIMAL(10, 2),
    d1_overnight_low DECIMAL(10, 2),

    -- Options Levels (op_01 through op_10)
    op_01 DECIMAL(10, 2),
    op_02 DECIMAL(10, 2),
    op_03 DECIMAL(10, 2),
    op_04 DECIMAL(10, 2),
    op_05 DECIMAL(10, 2),
    op_06 DECIMAL(10, 2),
    op_07 DECIMAL(10, 2),
    op_08 DECIMAL(10, 2),
    op_09 DECIMAL(10, 2),
    op_10 DECIMAL(10, 2),

    -- ATR Values
    m5_atr DECIMAL(10, 4),
    m15_atr DECIMAL(10, 4),
    h1_atr DECIMAL(10, 4),
    d1_atr DECIMAL(10, 4),

    -- Daily Camarilla Pivots
    d1_cam_s6 DECIMAL(10, 2),
    d1_cam_s4 DECIMAL(10, 2),
    d1_cam_s3 DECIMAL(10, 2),
    d1_cam_r3 DECIMAL(10, 2),
    d1_cam_r4 DECIMAL(10, 2),
    d1_cam_r6 DECIMAL(10, 2),

    -- Weekly Camarilla Pivots
    w1_cam_s6 DECIMAL(10, 2),
    w1_cam_s4 DECIMAL(10, 2),
    w1_cam_s3 DECIMAL(10, 2),
    w1_cam_r3 DECIMAL(10, 2),
    w1_cam_r4 DECIMAL(10, 2),
    w1_cam_r6 DECIMAL(10, 2),

    -- Monthly Camarilla Pivots
    m1_cam_s6 DECIMAL(10, 2),
    m1_cam_s4 DECIMAL(10, 2),
    m1_cam_s3 DECIMAL(10, 2),
    m1_cam_r3 DECIMAL(10, 2),
    m1_cam_r4 DECIMAL(10, 2),
    m1_cam_r6 DECIMAL(10, 2),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    PRIMARY KEY (date, ticker_id),
    FOREIGN KEY (date) REFERENCES daily_sessions(date) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_bar_data_ticker ON bar_data(ticker);
CREATE INDEX IF NOT EXISTS idx_bar_data_date ON bar_data(date DESC);

-- Update trigger
DROP TRIGGER IF EXISTS update_bar_data_updated_at ON bar_data;
CREATE TRIGGER update_bar_data_updated_at
    BEFORE UPDATE ON bar_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE bar_data IS 'Wide-format OHLC, ATR, Options, and Camarilla data per ticker per day';
COMMENT ON COLUMN bar_data.ticker_id IS 'Ticker position identifier (t1-t10)';
COMMENT ON COLUMN bar_data.d1_atr IS 'Daily Average True Range';
COMMENT ON COLUMN bar_data.d1_cam_s3 IS 'Daily Camarilla S3 = Close - (Range * 0.5)';
COMMENT ON COLUMN bar_data.d1_cam_r3 IS 'Daily Camarilla R3 = Close + (Range * 0.5)';

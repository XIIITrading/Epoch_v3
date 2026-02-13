-- ============================================================================
-- Epoch Trading System - Table 05: zones
-- All confluence zones (raw_zones + zone_results combined).
-- Source: raw_zones worksheet (all L1-L5) and zone_results worksheet (filtered)
-- ============================================================================

CREATE TABLE IF NOT EXISTS zones (
    -- Composite Primary Key
    date DATE NOT NULL,
    zone_id VARCHAR(50) NOT NULL,  -- Unique zone identifier

    -- Ticker Info
    ticker_id VARCHAR(10) NOT NULL,
    ticker VARCHAR(10) NOT NULL,

    -- Zone Pricing
    price DECIMAL(10, 2),  -- Current price at time of calculation
    hvn_poc DECIMAL(10, 2),  -- HVN POC anchor for this zone
    zone_high DECIMAL(10, 2),
    zone_low DECIMAL(10, 2),

    -- Zone Classification
    direction VARCHAR(10),  -- Bull, Bear
    rank VARCHAR(5),  -- L1, L2, L3, L4, L5
    score DECIMAL(10, 2),  -- Confluence score
    overlap_count INTEGER,  -- Number of overlapping levels

    -- Confluence Details (stored as text, can be parsed)
    confluences TEXT,  -- Comma-separated list of confluence factors

    -- Filtering Status (from zone_results)
    is_filtered BOOLEAN DEFAULT FALSE,  -- TRUE if passed Module 06 filtering

    -- Setup Markers (from Module 07)
    is_epch_bull BOOLEAN DEFAULT FALSE,  -- Marked as bull POC anchor
    is_epch_bear BOOLEAN DEFAULT FALSE,  -- Marked as bear POC anchor
    epch_bull_price DECIMAL(10, 2),
    epch_bear_price DECIMAL(10, 2),
    epch_bull_target DECIMAL(10, 2),
    epch_bear_target DECIMAL(10, 2),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    PRIMARY KEY (date, zone_id),
    FOREIGN KEY (date) REFERENCES daily_sessions(date) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_zones_ticker ON zones(ticker);
CREATE INDEX IF NOT EXISTS idx_zones_date ON zones(date DESC);
CREATE INDEX IF NOT EXISTS idx_zones_rank ON zones(rank);
CREATE INDEX IF NOT EXISTS idx_zones_filtered ON zones(is_filtered) WHERE is_filtered = TRUE;
CREATE INDEX IF NOT EXISTS idx_zones_ticker_date ON zones(ticker, date DESC);

-- Update trigger
DROP TRIGGER IF EXISTS update_zones_updated_at ON zones;
CREATE TRIGGER update_zones_updated_at
    BEFORE UPDATE ON zones
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE zones IS 'All confluence zones with scoring, ranking, and setup markers';
COMMENT ON COLUMN zones.zone_id IS 'Unique zone identifier (format varies by source)';
COMMENT ON COLUMN zones.rank IS 'Zone quality rank: L5=BEST, L4, L3, L2, L1=WORST';
COMMENT ON COLUMN zones.score IS 'Weighted confluence score (higher = stronger zone)';
COMMENT ON COLUMN zones.confluences IS 'Comma-separated list of levels that contribute to this zone';
COMMENT ON COLUMN zones.is_filtered IS 'TRUE if zone passed proximity and rank filtering (L2+, within 2 ATR)';
COMMENT ON COLUMN zones.is_epch_bull IS 'TRUE if marked as bull POC anchor by Module 07';

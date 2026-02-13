-- ============================================================================
-- Epoch Trading System - Table: trade_images
-- Stores Bookmap and other image references for trades.
-- Source: 09_training module
-- ============================================================================

CREATE TABLE IF NOT EXISTS trade_images (
    -- Primary Key (one image set per trade)
    trade_id VARCHAR(50) PRIMARY KEY REFERENCES trades(trade_id) ON DELETE CASCADE,

    -- Bookmap snapshot URL (Supabase storage or external)
    bookmap_url TEXT,

    -- Image type for future expansion
    image_type TEXT DEFAULT 'bookmap' CHECK (image_type IN ('bookmap', 'dom', 'footprint', 'other')),

    -- When the snapshot was captured during the trade
    capture_time TIME,

    -- Notes about the image
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_trade_images_image_type ON trade_images(image_type);

-- Update trigger
DROP TRIGGER IF EXISTS update_trade_images_updated_at ON trade_images;
CREATE TRIGGER update_trade_images_updated_at
    BEFORE UPDATE ON trade_images
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE trade_images IS 'Bookmap and other image references for trades';
COMMENT ON COLUMN trade_images.bookmap_url IS 'URL to Bookmap snapshot image';
COMMENT ON COLUMN trade_images.image_type IS 'Type of image: bookmap, dom, footprint, other';
COMMENT ON COLUMN trade_images.capture_time IS 'Time during trade when image was captured';

-- Add Notion sync tracking to journal_trades
-- Safe to run multiple times (IF NOT EXISTS)
--
-- Usage:
--   psql -f processor/schema/add_notion_tracking.sql
--   OR: python scripts/generate_trade_report.py --create-tables

ALTER TABLE journal_trades
    ADD COLUMN IF NOT EXISTS notion_page_id    VARCHAR(36),
    ADD COLUMN IF NOT EXISTS notion_url         TEXT,
    ADD COLUMN IF NOT EXISTS notion_synced_at   TIMESTAMPTZ;

-- Partial index for fast "unsynced" queries
CREATE INDEX IF NOT EXISTS idx_journal_trades_notion_unsync
    ON journal_trades (notion_page_id)
    WHERE notion_page_id IS NULL;

-- Index for stale-sync detection (resync mode)
CREATE INDEX IF NOT EXISTS idx_journal_trades_notion_stale
    ON journal_trades (notion_synced_at, updated_at)
    WHERE notion_page_id IS NOT NULL;

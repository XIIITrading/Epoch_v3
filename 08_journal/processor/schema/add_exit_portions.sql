-- Add JSONB column for FIFO exit portions to journal_trades
-- Stores individual exit fills: [{"price": 399.21, "qty": 4, "time": "10:17:08"}, ...]
-- Used by M1 Journal Chart to render multiple exit triangles per trade

ALTER TABLE journal_trades ADD COLUMN IF NOT EXISTS exit_portions_json JSONB;

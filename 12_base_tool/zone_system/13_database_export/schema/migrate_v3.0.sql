-- ============================================================================
-- Epoch Trading System - Migration v3.0.0
-- Removes deprecated entry/exit events tables, adds trade_bars
--
-- IMPORTANT: Run this BEFORE running the new export!
-- ============================================================================

-- ============================================================================
-- Step 1: Drop deprecated tables
-- ============================================================================
-- These tables are being replaced by trade_bars for granular analysis

DROP TABLE IF EXISTS trade_exit_events CASCADE;
DROP TABLE IF EXISTS trade_entry_events CASCADE;

-- ============================================================================
-- Step 2: Create trade_bars table
-- ============================================================================
-- See 12_trade_bars.sql for full schema
-- The table will be created automatically by the exporter if it doesn't exist

-- ============================================================================
-- Verification
-- ============================================================================
-- After running this migration, verify:
-- 1. trade_entry_events table no longer exists
-- 2. trade_exit_events table no longer exists
-- 3. Run the database export to create and populate trade_bars
-- ============================================================================

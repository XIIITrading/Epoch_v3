-- ============================================================================
-- Migration: Remove proximity_group column from zones table
--
-- This column was an internal calculation used only for filtering/sorting
-- and is never populated from Excel data. Always NULL.
--
-- Run this in Supabase SQL Editor:
-- ============================================================================

ALTER TABLE zones DROP COLUMN IF EXISTS proximity_group;

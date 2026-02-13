-- ============================================================================
-- EPOCH TRADING SYSTEM - OPTIONS MFE/MAE POTENTIAL TABLE
-- Stores options price excursions from entry to 15:30 ET
-- XIII Trading LLC
-- ============================================================================
--
-- This table mirrors mfe_mae_potential but for OPTIONS contracts.
-- All MFE/MAE values are measured in POINTS (price movement) and PERCENTAGE.
--
-- MFE = Maximum Favorable Excursion (price moved in our favor)
-- MAE = Maximum Adverse Excursion (price moved against us)
--
-- For OPTIONS (we always BUY, never short):
--   - MFE = highest price - entry price (we want price UP)
--   - MAE = entry price - lowest price (price DOWN is adverse)
--
-- ============================================================================

-- Drop table if exists (for clean recreation)
-- DROP TABLE IF EXISTS public.op_mfe_mae_potential;

CREATE TABLE IF NOT EXISTS public.op_mfe_mae_potential (
    -- Primary Key
    trade_id VARCHAR(50) PRIMARY KEY,

    -- Trade Metadata (from trades table)
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10),
    model VARCHAR(20),

    -- Options Contract Info (from options_analysis table)
    options_ticker VARCHAR(30) NOT NULL,
    strike NUMERIC(10, 2),
    expiration DATE,
    contract_type VARCHAR(10),  -- CALL or PUT

    -- Entry Event
    entry_time TIME,
    option_entry_price NUMERIC(10, 4),

    -- MFE Event (Max Favorable Excursion)
    -- For options: highest price reached (we want UP)
    mfe_points NUMERIC(10, 4),          -- highest - entry (always positive)
    mfe_price NUMERIC(10, 4),           -- Option price at MFE
    mfe_time TIME,                      -- When MFE occurred
    mfe_pct NUMERIC(10, 4),             -- MFE as % of entry price

    -- MAE Event (Max Adverse Excursion)
    -- For options: lowest price reached (DOWN is adverse)
    mae_points NUMERIC(10, 4),          -- entry - lowest (always positive)
    mae_price NUMERIC(10, 4),           -- Option price at MAE
    mae_time TIME,                      -- When MAE occurred
    mae_pct NUMERIC(10, 4),             -- MAE as % of entry price

    -- Exit Event (15:30 ET)
    exit_price NUMERIC(10, 4),          -- Option price at 15:30 ET
    exit_time TIME DEFAULT '15:30:00',  -- Always 15:30
    exit_points NUMERIC(10, 4),         -- exit - entry (can be negative)
    exit_pct NUMERIC(10, 4),            -- Exit P&L as % of entry price

    -- Comparison to Underlying (from mfe_mae_potential)
    underlying_mfe_pct NUMERIC(10, 4),
    underlying_mae_pct NUMERIC(10, 4),
    underlying_exit_pct NUMERIC(10, 4),

    -- Metadata
    bars_analyzed INT,
    eod_cutoff TIME DEFAULT '15:30:00',
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Foreign Key
    CONSTRAINT op_mfe_mae_potential_trade_fkey
        FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_op_mfe_mae_date
    ON public.op_mfe_mae_potential(date DESC);

CREATE INDEX IF NOT EXISTS idx_op_mfe_mae_ticker
    ON public.op_mfe_mae_potential(ticker);

CREATE INDEX IF NOT EXISTS idx_op_mfe_mae_model
    ON public.op_mfe_mae_potential(model);

CREATE INDEX IF NOT EXISTS idx_op_mfe_mae_contract_type
    ON public.op_mfe_mae_potential(contract_type);

CREATE INDEX IF NOT EXISTS idx_op_mfe_mae_direction
    ON public.op_mfe_mae_potential(direction);

-- Table comment
COMMENT ON TABLE public.op_mfe_mae_potential IS
    'Options MFE/MAE from entry to 15:30 ET - mirrors mfe_mae_potential for shares';

-- Column comments
COMMENT ON COLUMN public.op_mfe_mae_potential.mfe_points IS
    'Max favorable excursion in points (highest - entry, always positive)';
COMMENT ON COLUMN public.op_mfe_mae_potential.mae_points IS
    'Max adverse excursion in points (entry - lowest, always positive)';
COMMENT ON COLUMN public.op_mfe_mae_potential.exit_points IS
    'Exit P&L in points (exit - entry, can be negative for losses)';
COMMENT ON COLUMN public.op_mfe_mae_potential.mfe_pct IS
    'MFE as percentage of entry price';
COMMENT ON COLUMN public.op_mfe_mae_potential.mae_pct IS
    'MAE as percentage of entry price';
COMMENT ON COLUMN public.op_mfe_mae_potential.exit_pct IS
    'Exit P&L as percentage of entry price';

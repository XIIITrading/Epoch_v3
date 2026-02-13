-- =============================================================================
-- EPOCH 10_machine_learning - Claude Trade Export View
-- =============================================================================
-- Purpose: Single optimized view for Claude analysis exports
-- Source:  trades_m5_r_win as SOLE SOURCE OF TRUTH (no trades table)
-- Usage:   SELECT * FROM v_claude_trade_export WHERE date = '2026-01-31'
-- =============================================================================

CREATE OR REPLACE VIEW v_claude_trade_export AS
SELECT
    -- Trade Identity (from trades_m5_r_win)
    m.trade_id,
    m.date,
    m.ticker,
    m.model,
    m.direction,

    -- Zone Context
    m.zone_type,
    m.zone_high,
    m.zone_low,
    (m.zone_high + m.zone_low) / 2 as zone_mid,

    -- Entry Details
    m.entry_price,
    m.entry_time,

    -- Canonical Outcome (SINGLE SOURCE OF TRUTH)
    m.is_winner,
    m.outcome,
    m.pnl_r,
    m.exit_reason,
    m.outcome_method,

    -- Stop Details
    m.stop_price,
    m.stop_distance,
    m.stop_distance_pct,
    m.m5_atr_value,

    -- R-Level Tracking
    m.r1_price,
    m.r2_price,
    m.r3_price,
    m.r4_price,
    m.r5_price,
    m.r1_hit,
    m.r2_hit,
    m.r3_hit,
    m.r4_hit,
    m.r5_hit,
    m.r1_time,
    m.r2_time,
    m.r3_time,
    m.r1_bars_from_entry,
    m.r2_bars_from_entry,
    m.r3_bars_from_entry,
    m.max_r_achieved,
    m.reached_2r,
    m.reached_3r,
    m.minutes_to_r1,

    -- Stop Hit Details
    m.stop_hit,
    m.stop_hit_time,
    m.stop_hit_bars_from_entry,

    -- Zone Buffer (legacy stop reference)
    m.zb_stop_price,
    m.zb_exit_price,
    m.zb_exit_reason,
    m.zb_pnl_r,
    m.zb_is_winner,

    -- Entry Indicators
    ei.health_score,
    ei.health_label,
    ei.h4_structure,
    ei.h1_structure,
    ei.m15_structure,
    ei.m5_structure,
    ei.vol_roc,
    ei.vol_delta,
    ei.cvd_slope,
    ei.sma9,
    ei.sma21,
    ei.sma_spread,
    ei.sma_momentum_label,
    ei.vwap,

    -- Calculated Fields
    CASE
        WHEN m.model IN ('EPCH1', 'EPCH3') THEN 'continuation'
        ELSE 'rejection'
    END as trade_type,

    CASE
        WHEN m.model IN ('EPCH1', 'EPCH2') THEN 'primary'
        ELSE 'secondary'
    END as zone_classification,

    -- MFE/MAE (from potential table)
    mfe.mfe_r_potential,
    mfe.mae_r_potential,
    mfe.mfe_potential_time,
    mfe.mae_potential_time

FROM trades_m5_r_win m
LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
LEFT JOIN mfe_mae_potential mfe ON m.trade_id = mfe.trade_id;

-- =============================================================================
-- Usage Examples:
-- =============================================================================
--
-- Get all trades for a date:
-- SELECT * FROM v_claude_trade_export WHERE date = '2026-01-31';
--
-- Get winners only:
-- SELECT * FROM v_claude_trade_export WHERE is_winner = true;
--
-- Get by model:
-- SELECT * FROM v_claude_trade_export WHERE model = 'EPCH1';
--
-- Get with H1 NEUTRAL (strongest edge):
-- SELECT * FROM v_claude_trade_export WHERE h1_structure = 'NEUTRAL';
--
-- Get multi-R winners:
-- SELECT * FROM v_claude_trade_export WHERE max_r_achieved >= 3;
-- =============================================================================

-- ============================================================================
-- Epoch Trading System - Views and Functions for Training Module
-- Source: 10_training module
-- ============================================================================

-- Drop existing functions first (required when changing return types)
DROP FUNCTION IF EXISTS get_calibration_stats();
DROP FUNCTION IF EXISTS get_recent_calibration_stats(INTEGER);
DROP FUNCTION IF EXISTS get_review_summary();
DROP FUNCTION IF EXISTS get_review_stats_by_flag();
DROP FUNCTION IF EXISTS get_stop_placement_stats();
DROP FUNCTION IF EXISTS get_entry_attempt_stats();

-- ============================================================================
-- View: unreviewed_trades
-- Convenience view for fetching trades that haven't been reviewed yet.
-- Joins with optimal_trade to include MFE/MAE metrics.
-- ============================================================================

CREATE OR REPLACE VIEW unreviewed_trades AS
SELECT
    t.trade_id,
    t.date,
    t.ticker,
    t.model,
    t.zone_type,
    t.direction,
    t.zone_high,
    t.zone_low,
    t.entry_price,
    t.entry_time,
    t.stop_price,
    t.target_3r,
    t.target_calc,
    t.target_used,
    t.exit_price,
    t.exit_time,
    t.exit_reason,
    t.pnl_dollars,
    t.pnl_r,
    t.risk,
    t.is_winner,
    -- MFE from optimal_trade
    ot_mfe.r_at_event AS mfe_r,
    ot_mfe.bars_from_entry AS mfe_bars,
    ot_mfe.event_time AS mfe_time,
    ot_mfe.price_at_event AS mfe_price,
    ot_mfe.health_score AS mfe_health,
    -- MAE from optimal_trade
    ot_mae.r_at_event AS mae_r,
    ot_mae.bars_from_entry AS mae_bars,
    ot_mae.event_time AS mae_time,
    ot_mae.price_at_event AS mae_price,
    ot_mae.health_score AS mae_health,
    -- Entry health from optimal_trade
    ot_entry.health_score AS entry_health,
    -- Bookmap URL from trade_images
    ti.bookmap_url
FROM trades t
LEFT JOIN trade_reviews r ON t.trade_id = r.trade_id
LEFT JOIN optimal_trade ot_mfe ON t.trade_id = ot_mfe.trade_id AND ot_mfe.event_type = 'MFE'
LEFT JOIN optimal_trade ot_mae ON t.trade_id = ot_mae.trade_id AND ot_mae.event_type = 'MAE'
LEFT JOIN optimal_trade ot_entry ON t.trade_id = ot_entry.trade_id AND ot_entry.event_type = 'ENTRY'
LEFT JOIN trade_images ti ON t.trade_id = ti.trade_id
WHERE r.id IS NULL;

COMMENT ON VIEW unreviewed_trades IS 'Trades that have not been reviewed yet, with MFE/MAE metrics';


-- ============================================================================
-- View: reviewed_trades
-- Trades that HAVE been reviewed, with review data for analysis.
-- ============================================================================

CREATE OR REPLACE VIEW reviewed_trades AS
SELECT
    t.trade_id,
    t.date,
    t.ticker,
    t.model,
    t.zone_type,
    t.direction,
    t.zone_high,
    t.zone_low,
    t.entry_price,
    t.entry_time,
    t.exit_price,
    t.exit_time,
    t.exit_reason,
    t.pnl_r,
    t.is_winner,
    -- MFE/MAE
    ot_mfe.r_at_event AS mfe_r,
    ot_mae.r_at_event AS mae_r,
    -- Review data
    r.actual_outcome,
    r.notes AS review_notes,
    r.reviewed_at,
    -- Review flags
    r.good_trade,
    r.signal_aligned,
    r.confirmation_required,
    r.prior_candle_stop,
    r.two_candle_stop,
    r.atr_stop,
    r.zone_edge_stop,
    r.entry_attempt,
    r.with_trend,
    r.counter_trend,
    r.stopped_by_wick
FROM trades t
INNER JOIN trade_reviews r ON t.trade_id = r.trade_id
LEFT JOIN optimal_trade ot_mfe ON t.trade_id = ot_mfe.trade_id AND ot_mfe.event_type = 'MFE'
LEFT JOIN optimal_trade ot_mae ON t.trade_id = ot_mae.trade_id AND ot_mae.event_type = 'MAE';

COMMENT ON VIEW reviewed_trades IS 'Trades that have been reviewed, with review data and MFE/MAE metrics';


-- ============================================================================
-- Function: get_review_stats_by_flag
-- Returns statistics grouped by each review flag.
-- ============================================================================

CREATE OR REPLACE FUNCTION get_review_stats_by_flag()
RETURNS TABLE (
    flag_name TEXT,
    total_flagged BIGINT,
    winners BIGINT,
    losers BIGINT,
    win_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'good_trade'::TEXT AS flag_name,
           count(*) FILTER (WHERE r.good_trade) AS total_flagged,
           count(*) FILTER (WHERE r.good_trade AND t.is_winner) AS winners,
           count(*) FILTER (WHERE r.good_trade AND NOT t.is_winner) AS losers,
           ROUND(
               count(*) FILTER (WHERE r.good_trade AND t.is_winner)::NUMERIC /
               NULLIF(count(*) FILTER (WHERE r.good_trade)::NUMERIC, 0),
               3
           ) AS win_rate
    FROM trade_reviews r
    JOIN trades t ON r.trade_id = t.trade_id

    UNION ALL

    SELECT 'signal_aligned'::TEXT,
           count(*) FILTER (WHERE r.signal_aligned),
           count(*) FILTER (WHERE r.signal_aligned AND t.is_winner),
           count(*) FILTER (WHERE r.signal_aligned AND NOT t.is_winner),
           ROUND(
               count(*) FILTER (WHERE r.signal_aligned AND t.is_winner)::NUMERIC /
               NULLIF(count(*) FILTER (WHERE r.signal_aligned)::NUMERIC, 0),
               3
           )
    FROM trade_reviews r
    JOIN trades t ON r.trade_id = t.trade_id

    UNION ALL

    SELECT 'with_trend'::TEXT,
           count(*) FILTER (WHERE r.with_trend),
           count(*) FILTER (WHERE r.with_trend AND t.is_winner),
           count(*) FILTER (WHERE r.with_trend AND NOT t.is_winner),
           ROUND(
               count(*) FILTER (WHERE r.with_trend AND t.is_winner)::NUMERIC /
               NULLIF(count(*) FILTER (WHERE r.with_trend)::NUMERIC, 0),
               3
           )
    FROM trade_reviews r
    JOIN trades t ON r.trade_id = t.trade_id

    UNION ALL

    SELECT 'counter_trend'::TEXT,
           count(*) FILTER (WHERE r.counter_trend),
           count(*) FILTER (WHERE r.counter_trend AND t.is_winner),
           count(*) FILTER (WHERE r.counter_trend AND NOT t.is_winner),
           ROUND(
               count(*) FILTER (WHERE r.counter_trend AND t.is_winner)::NUMERIC /
               NULLIF(count(*) FILTER (WHERE r.counter_trend)::NUMERIC, 0),
               3
           )
    FROM trade_reviews r
    JOIN trades t ON r.trade_id = t.trade_id

    UNION ALL

    SELECT 'stopped_by_wick'::TEXT,
           count(*) FILTER (WHERE r.stopped_by_wick),
           count(*) FILTER (WHERE r.stopped_by_wick AND t.is_winner),
           count(*) FILTER (WHERE r.stopped_by_wick AND NOT t.is_winner),
           ROUND(
               count(*) FILTER (WHERE r.stopped_by_wick AND t.is_winner)::NUMERIC /
               NULLIF(count(*) FILTER (WHERE r.stopped_by_wick)::NUMERIC, 0),
               3
           )
    FROM trade_reviews r
    JOIN trades t ON r.trade_id = t.trade_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_review_stats_by_flag IS 'Returns win rate statistics for each review flag';


-- ============================================================================
-- Function: get_stop_placement_stats
-- Returns statistics grouped by stop placement type.
-- ============================================================================

CREATE OR REPLACE FUNCTION get_stop_placement_stats()
RETURNS TABLE (
    stop_type TEXT,
    total_count BIGINT,
    winners BIGINT,
    losers BIGINT,
    win_rate NUMERIC,
    avg_mfe NUMERIC,
    avg_mae NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'prior_candle'::TEXT AS stop_type,
           count(*) FILTER (WHERE r.prior_candle_stop) AS total_count,
           count(*) FILTER (WHERE r.prior_candle_stop AND t.is_winner) AS winners,
           count(*) FILTER (WHERE r.prior_candle_stop AND NOT t.is_winner) AS losers,
           ROUND(
               count(*) FILTER (WHERE r.prior_candle_stop AND t.is_winner)::NUMERIC /
               NULLIF(count(*) FILTER (WHERE r.prior_candle_stop)::NUMERIC, 0),
               3
           ) AS win_rate,
           ROUND(AVG(ot_mfe.r_at_event) FILTER (WHERE r.prior_candle_stop), 2) AS avg_mfe,
           ROUND(AVG(ot_mae.r_at_event) FILTER (WHERE r.prior_candle_stop), 2) AS avg_mae
    FROM trade_reviews r
    JOIN trades t ON r.trade_id = t.trade_id
    LEFT JOIN optimal_trade ot_mfe ON t.trade_id = ot_mfe.trade_id AND ot_mfe.event_type = 'MFE'
    LEFT JOIN optimal_trade ot_mae ON t.trade_id = ot_mae.trade_id AND ot_mae.event_type = 'MAE'

    UNION ALL

    SELECT 'two_candle'::TEXT,
           count(*) FILTER (WHERE r.two_candle_stop),
           count(*) FILTER (WHERE r.two_candle_stop AND t.is_winner),
           count(*) FILTER (WHERE r.two_candle_stop AND NOT t.is_winner),
           ROUND(
               count(*) FILTER (WHERE r.two_candle_stop AND t.is_winner)::NUMERIC /
               NULLIF(count(*) FILTER (WHERE r.two_candle_stop)::NUMERIC, 0),
               3
           ),
           ROUND(AVG(ot_mfe.r_at_event) FILTER (WHERE r.two_candle_stop), 2),
           ROUND(AVG(ot_mae.r_at_event) FILTER (WHERE r.two_candle_stop), 2)
    FROM trade_reviews r
    JOIN trades t ON r.trade_id = t.trade_id
    LEFT JOIN optimal_trade ot_mfe ON t.trade_id = ot_mfe.trade_id AND ot_mfe.event_type = 'MFE'
    LEFT JOIN optimal_trade ot_mae ON t.trade_id = ot_mae.trade_id AND ot_mae.event_type = 'MAE'

    UNION ALL

    SELECT 'atr_stop'::TEXT,
           count(*) FILTER (WHERE r.atr_stop),
           count(*) FILTER (WHERE r.atr_stop AND t.is_winner),
           count(*) FILTER (WHERE r.atr_stop AND NOT t.is_winner),
           ROUND(
               count(*) FILTER (WHERE r.atr_stop AND t.is_winner)::NUMERIC /
               NULLIF(count(*) FILTER (WHERE r.atr_stop)::NUMERIC, 0),
               3
           ),
           ROUND(AVG(ot_mfe.r_at_event) FILTER (WHERE r.atr_stop), 2),
           ROUND(AVG(ot_mae.r_at_event) FILTER (WHERE r.atr_stop), 2)
    FROM trade_reviews r
    JOIN trades t ON r.trade_id = t.trade_id
    LEFT JOIN optimal_trade ot_mfe ON t.trade_id = ot_mfe.trade_id AND ot_mfe.event_type = 'MFE'
    LEFT JOIN optimal_trade ot_mae ON t.trade_id = ot_mae.trade_id AND ot_mae.event_type = 'MAE'

    UNION ALL

    SELECT 'zone_edge'::TEXT,
           count(*) FILTER (WHERE r.zone_edge_stop),
           count(*) FILTER (WHERE r.zone_edge_stop AND t.is_winner),
           count(*) FILTER (WHERE r.zone_edge_stop AND NOT t.is_winner),
           ROUND(
               count(*) FILTER (WHERE r.zone_edge_stop AND t.is_winner)::NUMERIC /
               NULLIF(count(*) FILTER (WHERE r.zone_edge_stop)::NUMERIC, 0),
               3
           ),
           ROUND(AVG(ot_mfe.r_at_event) FILTER (WHERE r.zone_edge_stop), 2),
           ROUND(AVG(ot_mae.r_at_event) FILTER (WHERE r.zone_edge_stop), 2)
    FROM trade_reviews r
    JOIN trades t ON r.trade_id = t.trade_id
    LEFT JOIN optimal_trade ot_mfe ON t.trade_id = ot_mfe.trade_id AND ot_mfe.event_type = 'MFE'
    LEFT JOIN optimal_trade ot_mae ON t.trade_id = ot_mae.trade_id AND ot_mae.event_type = 'MAE';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_stop_placement_stats IS 'Returns performance statistics by stop placement type';


-- ============================================================================
-- Function: get_entry_attempt_stats
-- Returns statistics grouped by entry attempt number.
-- ============================================================================

CREATE OR REPLACE FUNCTION get_entry_attempt_stats()
RETURNS TABLE (
    entry_attempt INTEGER,
    total_count BIGINT,
    winners BIGINT,
    losers BIGINT,
    win_rate NUMERIC,
    avg_r NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.entry_attempt,
        count(*) AS total_count,
        count(*) FILTER (WHERE t.is_winner) AS winners,
        count(*) FILTER (WHERE NOT t.is_winner) AS losers,
        ROUND(
            count(*) FILTER (WHERE t.is_winner)::NUMERIC /
            NULLIF(count(*)::NUMERIC, 0),
            3
        ) AS win_rate,
        ROUND(AVG(t.pnl_r), 2) AS avg_r
    FROM trade_reviews r
    JOIN trades t ON r.trade_id = t.trade_id
    WHERE r.entry_attempt IS NOT NULL
    GROUP BY r.entry_attempt
    ORDER BY r.entry_attempt;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_entry_attempt_stats IS 'Returns performance statistics by entry attempt number';


-- ============================================================================
-- Function: get_review_summary
-- Returns overall review summary statistics.
-- ============================================================================

CREATE OR REPLACE FUNCTION get_review_summary()
RETURNS TABLE (
    total_reviews BIGINT,
    good_trades BIGINT,
    signal_aligned_trades BIGINT,
    with_trend_trades BIGINT,
    counter_trend_trades BIGINT,
    reviews_today BIGINT,
    reviews_this_week BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        count(*) AS total_reviews,
        count(*) FILTER (WHERE r.good_trade) AS good_trades,
        count(*) FILTER (WHERE r.signal_aligned) AS signal_aligned_trades,
        count(*) FILTER (WHERE r.with_trend) AS with_trend_trades,
        count(*) FILTER (WHERE r.counter_trend) AS counter_trend_trades,
        count(*) FILTER (WHERE r.reviewed_at::DATE = CURRENT_DATE) AS reviews_today,
        count(*) FILTER (WHERE r.reviewed_at >= CURRENT_DATE - INTERVAL '7 days') AS reviews_this_week
    FROM trade_reviews r;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_review_summary IS 'Returns overall review summary statistics';

-- =============================================================================
-- EPOCH 10_machine_learning - Edge Summary View
-- =============================================================================
-- Purpose: Pre-aggregated edge analysis for quick Claude consumption
-- Source:  trades_m5_r_win as SOLE SOURCE OF TRUTH (no trades table)
-- Usage:   SELECT * FROM v_edge_summary;
-- =============================================================================

CREATE OR REPLACE VIEW v_edge_summary AS

-- Baseline metrics (all trades from canonical table)
WITH baseline AS (
    SELECT
        COUNT(*) as total_trades,
        ROUND(
            SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
            / NULLIF(COUNT(*), 0) * 100, 1
        ) as baseline_win_rate,
        ROUND(AVG(m.pnl_r)::numeric, 3) as baseline_avg_r
    FROM trades_m5_r_win m
),

-- H1 Structure edge
h1_edge AS (
    SELECT
        'H1 Structure' as edge_name,
        ei.h1_structure as edge_value,
        COUNT(*) as trades,
        ROUND(
            SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
            / NULLIF(COUNT(*), 0) * 100, 1
        ) as win_rate,
        ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r
    FROM trades_m5_r_win m
    LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
    WHERE ei.h1_structure IS NOT NULL
    GROUP BY ei.h1_structure
),

-- Health Score tiers
health_edge AS (
    SELECT
        'Health Score' as edge_name,
        CASE
            WHEN ei.health_score >= 8 THEN 'STRONG (8-10)'
            WHEN ei.health_score >= 6 THEN 'MODERATE (6-7)'
            WHEN ei.health_score >= 4 THEN 'WEAK (4-5)'
            ELSE 'CRITICAL (0-3)'
        END as edge_value,
        COUNT(*) as trades,
        ROUND(
            SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
            / NULLIF(COUNT(*), 0) * 100, 1
        ) as win_rate,
        ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r
    FROM trades_m5_r_win m
    LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
    WHERE ei.health_score IS NOT NULL
    GROUP BY edge_value
),

-- Model performance
model_edge AS (
    SELECT
        'Entry Model' as edge_name,
        m.model as edge_value,
        COUNT(*) as trades,
        ROUND(
            SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
            / NULLIF(COUNT(*), 0) * 100, 1
        ) as win_rate,
        ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r
    FROM trades_m5_r_win m
    GROUP BY m.model
),

-- Direction performance
direction_edge AS (
    SELECT
        'Direction' as edge_name,
        m.direction as edge_value,
        COUNT(*) as trades,
        ROUND(
            SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
            / NULLIF(COUNT(*), 0) * 100, 1
        ) as win_rate,
        ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r
    FROM trades_m5_r_win m
    GROUP BY m.direction
)

-- Combine all edges with baseline comparison
SELECT
    e.edge_name,
    e.edge_value,
    e.trades,
    e.win_rate,
    e.avg_r,
    b.baseline_win_rate,
    ROUND(e.win_rate - b.baseline_win_rate, 1) as effect_size_pp,
    CASE
        WHEN e.trades >= 100 THEN 'HIGH'
        WHEN e.trades >= 30 THEN 'MEDIUM'
        ELSE 'LOW'
    END as confidence
FROM (
    SELECT * FROM h1_edge
    UNION ALL
    SELECT * FROM health_edge
    UNION ALL
    SELECT * FROM model_edge
    UNION ALL
    SELECT * FROM direction_edge
) e
CROSS JOIN baseline b
ORDER BY e.edge_name, e.edge_value;

-- =============================================================================
-- Usage Examples:
-- =============================================================================
--
-- Get all edge summaries:
-- SELECT * FROM v_edge_summary;
--
-- Get only significant edges (> 3pp effect):
-- SELECT * FROM v_edge_summary WHERE ABS(effect_size_pp) > 3;
--
-- Get high-confidence edges:
-- SELECT * FROM v_edge_summary WHERE confidence = 'HIGH';
-- =============================================================================

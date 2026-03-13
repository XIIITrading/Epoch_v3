"""
Step 3: Market Structure vs Outcomes
=====================================
Answers: Does market structure alignment predict trade outcomes?
Do trades aligned with D1 direction outperform counter-trend?
Does agreement between D1 and H1 matter?

Output: data_journal_results/step3_market_structure.md
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db import query, query_one, INDEX_TICKERS
from output import ResultsWriter


def run():
    w = ResultsWriter('step3_market_structure.md')
    w.header('Step 3: Market Structure vs Outcomes')
    w.text('Does market structure alignment predict trade outcomes?')
    w.text('')

    # ================================================================
    # SECTION 1: Data Shape
    # ================================================================
    w.section('1. Data Shape')

    shape = query_one('''
        SELECT COUNT(*) as total_rows, COUNT(DISTINCT date) as days,
               COUNT(DISTINCT ticker) as tickers
        FROM setups
    ''')
    w.metric('Setup Rows', shape['total_rows'])
    w.metric('Setup Days', shape['days'])
    w.metric('Setup Tickers', shape['tickers'])
    w.text('')

    join_stats = query_one('''
        SELECT COUNT(DISTINCT t.trade_id) as trades_with_setup
        FROM trades_m5_r_win_2 t
        INNER JOIN setups s ON t.date = s.date AND t.ticker = s.ticker
            AND LOWER(t.zone_type) = LOWER(s.setup_type)
    ''')
    w.metric('Trades with Setup Match', join_stats['trades_with_setup'])
    w.text('')

    # ================================================================
    # SECTION 2: Win Rate by Setup Direction
    # ================================================================
    w.section('2. Win Rate by Setup Direction')

    rows = query('''
        SELECT s.direction, COUNT(DISTINCT t.trade_id) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        INNER JOIN setups s ON t.date = s.date AND t.ticker = s.ticker
            AND LOWER(t.zone_type) = LOWER(s.setup_type)
        GROUP BY s.direction ORDER BY s.direction
    ''')
    w.table(
        ['Direction', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['direction'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 3: Trade Direction Alignment with Setup Direction
    # ================================================================
    w.section('3. Trade Direction vs Setup Direction (Alignment)')
    w.text('Does trading WITH the setup direction outperform counter-direction?')
    w.text('')

    rows = query('''
        SELECT
            CASE
                WHEN t.direction = s.direction THEN 'ALIGNED'
                ELSE 'COUNTER'
            END as alignment,
            COUNT(DISTINCT t.trade_id) as trades,
            ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        INNER JOIN setups s ON t.date = s.date AND t.ticker = s.ticker
            AND LOWER(t.zone_type) = LOWER(s.setup_type)
        WHERE s.direction IS NOT NULL
        GROUP BY alignment ORDER BY alignment
    ''')
    w.table(
        ['Alignment', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['alignment'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 4: Primary vs Secondary Setups
    # ================================================================
    w.section('4. Primary (With-Trend) vs Secondary (Counter-Trend)')

    rows = query('''
        SELECT t.zone_type,
               COUNT(DISTINCT t.trade_id) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        GROUP BY t.zone_type ORDER BY t.zone_type
    ''')
    w.table(
        ['Zone Type', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['zone_type'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 5: Direction + Model Combination
    # ================================================================
    w.section('5. Direction x Model Performance Matrix')
    w.text('Which direction + entry model combinations work best?')
    w.text('')

    rows = query('''
        SELECT t.direction, t.model,
               COUNT(*) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        GROUP BY t.direction, t.model ORDER BY t.direction, t.model
    ''')
    w.table(
        ['Direction', 'Model', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['direction'], r['model'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'left', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 6: Zone Type + Model Combination
    # ================================================================
    w.section('6. Zone Type x Model Performance Matrix')
    w.text('Primary vs Secondary across all 4 entry models.')
    w.text('')

    rows = query('''
        SELECT t.zone_type, t.model,
               COUNT(*) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        GROUP BY t.zone_type, t.model ORDER BY t.zone_type, t.model
    ''')
    w.table(
        ['Zone Type', 'Model', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['zone_type'], r['model'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'left', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 7: Risk-Reward from Setups
    # ================================================================
    w.section('7. Setup Risk-Reward vs Actual Outcomes')
    w.text('Does the calculated R:R at setup time predict actual max R achieved?')
    w.text('')

    rows = query('''
        SELECT
            CASE
                WHEN s.risk_reward >= 3.0 THEN '3.0+ R:R'
                WHEN s.risk_reward >= 2.0 THEN '2.0-3.0 R:R'
                WHEN s.risk_reward >= 1.5 THEN '1.5-2.0 R:R'
                WHEN s.risk_reward >= 1.0 THEN '1.0-1.5 R:R'
                ELSE '< 1.0 R:R'
            END as rr_range,
            CASE
                WHEN s.risk_reward >= 3.0 THEN 1
                WHEN s.risk_reward >= 2.0 THEN 2
                WHEN s.risk_reward >= 1.5 THEN 3
                WHEN s.risk_reward >= 1.0 THEN 4
                ELSE 5
            END as sort_order,
            COUNT(DISTINCT t.trade_id) as trades,
            ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_actual_r,
            ROUND(AVG(s.risk_reward), 2) as avg_setup_rr
        FROM trades_m5_r_win_2 t
        INNER JOIN setups s ON t.date = s.date AND t.ticker = s.ticker
            AND LOWER(t.zone_type) = LOWER(s.setup_type)
        WHERE s.risk_reward IS NOT NULL
        GROUP BY rr_range, sort_order ORDER BY sort_order
    ''')
    w.table(
        ['Setup R:R', 'Trades', 'Win Rate %', 'Avg Actual R', 'Avg Setup R:R'],
        [[r['rr_range'], r['trades'], r['win_rate'], r['avg_actual_r'], r['avg_setup_rr']] for r in rows],
        ['left', 'right', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 8: Your Picks — Structure Alignment
    # ================================================================
    w.section('8. Your Final 4: Structure Alignment')
    w.text('Were your selected tickers more aligned with setup direction?')
    w.text('')

    rows = query('''
        SELECT
            CASE
                WHEN EXISTS (SELECT 1 FROM ticker_analysis ta WHERE ta.date = t.date AND ta.ticker = t.ticker)
                THEN 'YOUR PICKS'
                ELSE 'SKIPPED'
            END as selection,
            CASE WHEN t.direction = s.direction THEN 'ALIGNED' ELSE 'COUNTER' END as alignment,
            COUNT(DISTINCT t.trade_id) as trades,
            ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        INNER JOIN setups s ON t.date = s.date AND t.ticker = s.ticker
            AND LOWER(t.zone_type) = LOWER(s.setup_type)
        WHERE t.date IN (SELECT DISTINCT date FROM ticker_analysis WHERE date IN (SELECT DISTINCT date FROM trades_m5_r_win_2))
        AND t.ticker NOT IN ('SPY', 'QQQ', 'DIA')
        AND s.direction IS NOT NULL
        GROUP BY selection, alignment ORDER BY selection DESC, alignment
    ''')
    w.table(
        ['Selection', 'Alignment', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['selection'], r['alignment'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'left', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 9: Key Findings
    # ================================================================
    w.section('9. Key Findings')
    w.text('**Review the tables above to answer:**')
    w.text('1. Does ALIGNED outperform COUNTER? By how much?')
    w.text('2. Which direction + model combo is the sweet spot?')
    w.text('3. Does setup R:R predict actual R achieved?')
    w.text('4. Were your picks structurally better-aligned than skipped tickers?')
    w.text('5. Should you filter out counter-trend setups entirely, or do they add value?')
    w.text('')

    w.divider()
    w.save()


if __name__ == '__main__':
    run()

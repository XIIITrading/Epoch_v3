"""
Step 2: Zone Quality vs Outcomes
=================================
Answers: Do higher-tier zones (T3) actually produce better outcomes?
Does zone confluence score, rank, and overlap count predict win rate?

Joins trades_m5_r_win_2 back to zones table via date + ticker to measure
how zone characteristics at screening time correlate with trade results.

Output: data_journal_results/step2_zone_quality.md
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db import query, query_one, INDEX_TICKERS
from output import ResultsWriter


def run():
    w = ResultsWriter('step2_zone_quality.md')
    w.header('Step 2: Zone Quality vs Outcomes')
    w.text('Do higher-quality zones predict better trade outcomes?')
    w.text('')

    # ================================================================
    # SECTION 1: Data Shape — Zones Table
    # ================================================================
    w.section('1. Data Shape')

    shape = query_one('''
        SELECT COUNT(*) as total_zones, COUNT(DISTINCT date) as days,
               COUNT(DISTINCT ticker_id) as tickers,
               MIN(date) as first_date, MAX(date) as last_date
        FROM zones
    ''')
    w.metric('Total Zones', shape['total_zones'])
    w.metric('Zone Days', shape['days'])
    w.metric('Zone Tickers', shape['tickers'])
    w.metric('Zone Date Range', f'{shape["first_date"]} to {shape["last_date"]}')
    w.text('')

    # Check join coverage (trades -> setups -> zones)
    join_stats = query_one('''
        SELECT COUNT(DISTINCT t.trade_id) as trades_with_zones,
               (SELECT COUNT(*) FROM trades_m5_r_win_2) as total_trades
        FROM trades_m5_r_win_2 t
        INNER JOIN setups s ON t.date = s.date AND t.ticker = s.ticker
            AND LOWER(t.zone_type) = LOWER(s.setup_type)
        INNER JOIN zones z ON s.date = z.date AND s.zone_id = z.zone_id
            AND z.ticker = s.ticker
    ''')
    w.metric('Trades with Zone Match', f'{join_stats["trades_with_zones"]} / {join_stats["total_trades"]}')
    w.text('')

    # ================================================================
    # SECTION 2: Win Rate by Zone Tier
    # ================================================================
    w.section('2. Win Rate by Zone Tier')
    w.text('Zones are classified T3 (institutional/L4-L5), T2 (medium/L3), T1 (lower/L1-L2).')
    w.text('Does T3 actually outperform T1?')
    w.text('')

    rows = query('''
        SELECT
            CASE
                WHEN z.rank IN ('L4', 'L5') THEN 'T3 (Institutional)'
                WHEN z.rank = 'L3' THEN 'T2 (Medium)'
                ELSE 'T1 (Lower)'
            END as tier,
            CASE WHEN z.rank IN ('L4', 'L5') THEN 1 WHEN z.rank = 'L3' THEN 2 ELSE 3 END as sort_order,
            COUNT(DISTINCT t.trade_id) as trades,
            ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r,
            COUNT(DISTINCT z.zone_id) as zones_used
        FROM trades_m5_r_win_2 t
        INNER JOIN setups s ON t.date = s.date AND t.ticker = s.ticker
            AND LOWER(t.zone_type) = LOWER(s.setup_type)
        INNER JOIN zones z ON s.date = z.date AND s.zone_id = z.zone_id
            AND z.ticker = s.ticker
        WHERE z.rank IS NOT NULL
        GROUP BY tier, sort_order ORDER BY sort_order
    ''')
    w.table(
        ['Tier', 'Trades', 'Win Rate %', 'Avg R', 'Zones'],
        [[r['tier'], r['trades'], r['win_rate'], r['avg_max_r'], r['zones_used']] for r in rows],
        ['left', 'right', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 3: Win Rate by Zone Rank (L1-L5)
    # ================================================================
    w.section('3. Win Rate by Zone Rank')
    w.text('Ranks: L5 (>=12.0 score), L4 (>=9.0), L3 (>=6.0), L2 (>=3.0), L1 (<3.0)')
    w.text('')

    rows = query('''
        SELECT z.rank as zone_rank, COUNT(DISTINCT t.trade_id) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        INNER JOIN setups s ON t.date = s.date AND t.ticker = s.ticker
            AND LOWER(t.zone_type) = LOWER(s.setup_type)
        INNER JOIN zones z ON s.date = z.date AND s.zone_id = z.zone_id
            AND z.ticker = s.ticker
        WHERE z.rank IS NOT NULL
        GROUP BY z.rank ORDER BY z.rank
    ''')
    w.table(
        ['Rank', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['zone_rank'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 4: Win Rate by Overlap Count (Confluence Density)
    # ================================================================
    w.section('4. Win Rate by Overlap Count (Confluence Density)')
    w.text('Does more confluence (more technical levels inside the zone) predict wins?')
    w.text('')

    rows = query('''
        SELECT z.overlap_count, COUNT(DISTINCT t.trade_id) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        INNER JOIN setups s ON t.date = s.date AND t.ticker = s.ticker
            AND LOWER(t.zone_type) = LOWER(s.setup_type)
        INNER JOIN zones z ON s.date = z.date AND s.zone_id = z.zone_id
            AND z.ticker = s.ticker
        WHERE z.overlap_count IS NOT NULL
        GROUP BY z.overlap_count ORDER BY z.overlap_count
    ''')
    w.table(
        ['Overlaps', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['overlap_count'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['right', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 5: Win Rate by Zone Score Ranges
    # ================================================================
    w.section('5. Win Rate by Zone Score Ranges')

    rows = query('''
        SELECT
            CASE
                WHEN z.score >= 12.0 THEN '12+ (L5)'
                WHEN z.score >= 9.0 THEN '9-12 (L4)'
                WHEN z.score >= 6.0 THEN '6-9 (L3)'
                WHEN z.score >= 3.0 THEN '3-6 (L2)'
                ELSE '0-3 (L1)'
            END as score_range,
            CASE
                WHEN z.score >= 12.0 THEN 1
                WHEN z.score >= 9.0 THEN 2
                WHEN z.score >= 6.0 THEN 3
                WHEN z.score >= 3.0 THEN 4
                ELSE 5
            END as sort_order,
            COUNT(DISTINCT t.trade_id) as trades,
            ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r,
            ROUND(AVG(z.score), 2) as avg_score
        FROM trades_m5_r_win_2 t
        INNER JOIN setups s ON t.date = s.date AND t.ticker = s.ticker
            AND LOWER(t.zone_type) = LOWER(s.setup_type)
        INNER JOIN zones z ON s.date = z.date AND s.zone_id = z.zone_id
            AND z.ticker = s.ticker
        WHERE z.score IS NOT NULL
        GROUP BY score_range, sort_order ORDER BY sort_order
    ''')
    w.table(
        ['Score Range', 'Trades', 'Win Rate %', 'Avg R', 'Avg Score'],
        [[r['score_range'], r['trades'], r['win_rate'], r['avg_max_r'], r['avg_score']] for r in rows],
        ['left', 'right', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 6: Confluence Type Breakdown
    # ================================================================
    w.section('6. Confluence Type Analysis')
    w.text('Which confluence types appear in winning vs losing trade zones?')
    w.text('(Parsing the confluences text field for pattern matching)')
    w.text('')

    # Check if confluences field exists and has data
    conf_check = query_one('''
        SELECT COUNT(*) as with_conf
        FROM zones WHERE confluences IS NOT NULL AND confluences != ''
    ''')
    w.metric('Zones with Confluences Data', conf_check['with_conf'])
    w.text('')

    if conf_check['with_conf'] and conf_check['with_conf'] > 0:
        # Options confluence
        w.subsection('Zones with Options Confluence')
        rows = query('''
            SELECT
                CASE WHEN z.confluences ILIKE '%%option%%' THEN 'Has Options' ELSE 'No Options' END as has_options,
                COUNT(DISTINCT t.trade_id) as trades,
                ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
                ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
            FROM trades_m5_r_win_2 t
            INNER JOIN setups s ON t.date = s.date AND t.ticker = s.ticker
                AND LOWER(t.zone_type) = LOWER(s.setup_type)
            INNER JOIN zones z ON s.date = z.date AND s.zone_id = z.zone_id
                AND z.ticker = s.ticker
            WHERE z.confluences IS NOT NULL
            GROUP BY has_options ORDER BY has_options
        ''')
        w.table(
            ['Options', 'Trades', 'Win Rate %', 'Avg R'],
            [[r['has_options'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
            ['left', 'right', 'right', 'right']
        )

        # Camarilla monthly confluence
        w.subsection('Zones with Camarilla Monthly Confluence')
        rows = query('''
            SELECT
                CASE WHEN z.confluences ILIKE '%%cam_m%%' OR z.confluences ILIKE '%%camarilla_monthly%%'
                     THEN 'Has Cam Monthly' ELSE 'No Cam Monthly' END as has_cam_m,
                COUNT(DISTINCT t.trade_id) as trades,
                ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
                ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
            FROM trades_m5_r_win_2 t
            INNER JOIN setups s ON t.date = s.date AND t.ticker = s.ticker
                AND LOWER(t.zone_type) = LOWER(s.setup_type)
            INNER JOIN zones z ON s.date = z.date AND s.zone_id = z.zone_id
                AND z.ticker = s.ticker
            WHERE z.confluences IS NOT NULL
            GROUP BY has_cam_m ORDER BY has_cam_m
        ''')
        w.table(
            ['Cam Monthly', 'Trades', 'Win Rate %', 'Avg R'],
            [[r['has_cam_m'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
            ['left', 'right', 'right', 'right']
        )

        # Structure level confluence
        w.subsection('Zones with Structure Level Confluence')
        rows = query('''
            SELECT
                CASE WHEN z.confluences ILIKE '%%structure%%' OR z.confluences ILIKE '%%strong%%' OR z.confluences ILIKE '%%weak%%'
                     THEN 'Has Structure' ELSE 'No Structure' END as has_structure,
                COUNT(DISTINCT t.trade_id) as trades,
                ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
                ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
            FROM trades_m5_r_win_2 t
            INNER JOIN setups s ON t.date = s.date AND t.ticker = s.ticker
                AND LOWER(t.zone_type) = LOWER(s.setup_type)
            INNER JOIN zones z ON s.date = z.date AND s.zone_id = z.zone_id
                AND z.ticker = s.ticker
            WHERE z.confluences IS NOT NULL
            GROUP BY has_structure ORDER BY has_structure
        ''')
        w.table(
            ['Structure', 'Trades', 'Win Rate %', 'Avg R'],
            [[r['has_structure'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
            ['left', 'right', 'right', 'right']
        )

    # ================================================================
    # SECTION 7: Zone Quality for Your Picks vs Skipped
    # ================================================================
    w.section('7. Zone Quality: Your Final 4 vs Skipped Tickers')
    w.text('Did your selected tickers have higher-quality zones than the ones you skipped?')
    w.text('')

    rows = query('''
        SELECT
            CASE
                WHEN EXISTS (SELECT 1 FROM ticker_analysis ta WHERE ta.date = t.date AND ta.ticker = t.ticker)
                THEN 'YOUR PICKS'
                ELSE 'SKIPPED'
            END as selection,
            ROUND(AVG(z.score), 2) as avg_zone_score,
            ROUND(AVG(z.overlap_count), 2) as avg_overlaps,
            COUNT(DISTINCT t.trade_id) as trades,
            ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        INNER JOIN setups s ON t.date = s.date AND t.ticker = s.ticker
            AND LOWER(t.zone_type) = LOWER(s.setup_type)
        INNER JOIN zones z ON s.date = z.date AND s.zone_id = z.zone_id
            AND z.ticker = s.ticker
        WHERE t.date IN (SELECT DISTINCT date FROM ticker_analysis WHERE date IN (SELECT DISTINCT date FROM trades_m5_r_win_2))
        AND t.ticker NOT IN ('SPY', 'QQQ', 'DIA')
        GROUP BY selection ORDER BY selection DESC
    ''')
    w.table(
        ['Selection', 'Avg Score', 'Avg Overlaps', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['selection'], r['avg_zone_score'], r['avg_overlaps'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 8: Key Findings
    # ================================================================
    w.section('8. Key Findings')
    w.text('Summary of zone quality impact on trade outcomes:')
    w.text('')
    w.text('**Review the tables above to answer:**')
    w.text('1. Do T3 zones win more than T1 zones? By how much?')
    w.text('2. Does overlap count (confluence density) linearly predict win rate?')
    w.text('3. Is there a score threshold below which zones should be filtered out?')
    w.text('4. Do options confluences add edge?')
    w.text('5. Did your picks have objectively better zone quality than skipped tickers?')
    w.text('')

    w.divider()
    w.save()


if __name__ == '__main__':
    run()

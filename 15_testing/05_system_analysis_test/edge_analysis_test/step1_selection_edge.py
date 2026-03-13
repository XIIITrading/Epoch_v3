"""
Step 1: Selection Edge Analysis
================================
Answers: Do your manually selected tickers show edge vs the full universe?
Does your down-selection from 10 -> 4 improve or hurt performance?

Three-tier comparison:
  Tier A — Full Universe (all trades_m5_r_win_2)
  Tier B — Your 10 Custom Picks (non-index tickers that went through pipeline)
  Tier C — Your Final 4 (tickers saved in ticker_analysis via Dashboard)
  Index  — SPY/QQQ/DIA (automatic, always included)

Output: edge_analysis_results/step1_selection_edge.md
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db import query, query_one, INDEX_TICKERS
from output import ResultsWriter


def run():
    w = ResultsWriter('step1_selection_edge.md')
    w.header('Step 1: Selection Edge Analysis')
    w.text('Do your manually selected tickers show edge? Does down-selecting to 4 improve it?')
    w.text('')

    # ================================================================
    # SECTION 1: Data Shape
    # ================================================================
    w.section('1. Data Shape')

    shape = query_one('''
        SELECT MIN(date) as first_date, MAX(date) as last_date,
               COUNT(DISTINCT date) as days, COUNT(*) as total_trades,
               COUNT(DISTINCT ticker) as unique_tickers
        FROM trades_m5_r_win_2
    ''')
    w.metric('Date Range', f'{shape["first_date"]} to {shape["last_date"]}')
    w.metric('Trading Days', shape['days'])
    w.metric('Total Trades', shape['total_trades'])
    w.metric('Unique Tickers', shape['unique_tickers'])
    w.text('')

    ta_shape = query_one('''
        SELECT COUNT(*) as rows, COUNT(DISTINCT date) as days,
               COUNT(DISTINCT ticker) as tickers,
               MIN(date) as first_date, MAX(date) as last_date
        FROM ticker_analysis
    ''')
    w.metric('Ticker Analysis Rows', ta_shape['rows'])
    w.metric('Ticker Analysis Days', ta_shape['days'])
    w.metric('Ticker Analysis Tickers', ta_shape['tickers'])
    w.metric('Ticker Analysis Range', f'{ta_shape["first_date"]} to {ta_shape["last_date"]}')
    w.text('')

    overlap = query_one('''
        SELECT COUNT(DISTINCT t.date) as days
        FROM trades_m5_r_win_2 t
        INNER JOIN ticker_analysis ta ON t.date = ta.date
    ''')
    w.metric('Overlapping Days (trades + selections)', overlap['days'])
    w.text('')

    # ================================================================
    # SECTION 2: Tier A — Full Universe Baseline
    # ================================================================
    w.section('2. Tier A: Full Universe Baseline')

    tier_a = query_one('''
        SELECT COUNT(*) as trades,
               SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
               SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
               ROUND(AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2
    ''')
    w.metric('Total Trades', tier_a['trades'])
    w.metric('Wins / Losses', f'{tier_a["wins"]} / {tier_a["losses"]}')
    w.metric('Win Rate', tier_a['win_rate'], '%')
    w.metric('Avg Max R', tier_a['avg_max_r'])
    w.text('')

    # By model
    w.subsection('By Model')
    rows = query('''
        SELECT model, COUNT(*) as trades,
               ROUND(AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2
        GROUP BY model ORDER BY model
    ''')
    w.table(
        ['Model', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['model'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right']
    )

    # By direction
    w.subsection('By Direction')
    rows = query('''
        SELECT direction, COUNT(*) as trades,
               ROUND(AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2
        GROUP BY direction ORDER BY direction
    ''')
    w.table(
        ['Direction', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['direction'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right']
    )

    # By zone type
    w.subsection('By Zone Type')
    rows = query('''
        SELECT zone_type, COUNT(*) as trades,
               ROUND(AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2
        GROUP BY zone_type ORDER BY zone_type
    ''')
    w.table(
        ['Zone Type', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['zone_type'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right']
    )

    # By entry hour
    w.subsection('By Entry Hour')
    rows = query('''
        SELECT EXTRACT(HOUR FROM entry_time::time) as hour,
               COUNT(*) as trades,
               ROUND(AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2
        WHERE entry_time IS NOT NULL
        GROUP BY hour ORDER BY hour
    ''')
    w.table(
        ['Hour', 'Trades', 'Win Rate %', 'Avg R'],
        [[f'{int(r["hour"]):02d}:00', r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right']
    )

    # Index vs Custom
    w.subsection('Index vs Custom')
    rows = query('''
        SELECT CASE WHEN ticker IN %s THEN 'INDEX' ELSE 'CUSTOM' END as grp,
               COUNT(*) as trades,
               ROUND(AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(max_r_achieved, 0)), 2) as avg_max_r,
               COUNT(DISTINCT ticker) as tickers
        FROM trades_m5_r_win_2
        GROUP BY grp ORDER BY grp
    ''', (INDEX_TICKERS,))
    w.table(
        ['Group', 'Trades', 'Win Rate %', 'Avg R', 'Tickers'],
        [[r['grp'], r['trades'], r['win_rate'], r['avg_max_r'], r['tickers']] for r in rows],
        ['left', 'right', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 3: All Tickers Ranked
    # ================================================================
    w.section('3. All Tickers Ranked by Trade Count')
    rows = query('''
        SELECT ticker, COUNT(*) as trades,
               ROUND(AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(max_r_achieved, 0)), 2) as avg_max_r,
               CASE WHEN ticker IN %s THEN 'INDEX' ELSE 'CUSTOM' END as type
        FROM trades_m5_r_win_2
        GROUP BY ticker ORDER BY trades DESC
    ''', (INDEX_TICKERS,))
    w.table(
        ['Ticker', 'Type', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['ticker'], r['type'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'left', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 4: Tier B — Your 10 Custom Picks
    # ================================================================
    w.section('4. Tier B: Your 10 Custom Picks (Non-Index)')

    tier_b = query_one('''
        SELECT COUNT(*) as trades,
               SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
               ROUND(AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(max_r_achieved, 0)), 2) as avg_max_r,
               COUNT(DISTINCT ticker) as tickers, COUNT(DISTINCT date) as days
        FROM trades_m5_r_win_2
        WHERE ticker NOT IN %s
    ''', (INDEX_TICKERS,))
    w.metric('Trades', tier_b['trades'])
    w.metric('Wins', tier_b['wins'])
    w.metric('Win Rate', tier_b['win_rate'], '%')
    w.metric('Avg Max R', tier_b['avg_max_r'])
    w.metric('Unique Tickers', tier_b['tickers'])
    w.metric('Trading Days', tier_b['days'])
    w.text('')

    # Tier B by model
    w.subsection('Tier B by Model')
    rows = query('''
        SELECT model, COUNT(*) as trades,
               ROUND(AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2
        WHERE ticker NOT IN %s
        GROUP BY model ORDER BY model
    ''', (INDEX_TICKERS,))
    w.table(
        ['Model', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['model'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right']
    )

    # Tier B by zone type
    w.subsection('Tier B by Zone Type')
    rows = query('''
        SELECT zone_type, COUNT(*) as trades,
               ROUND(AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2
        WHERE ticker NOT IN %s
        GROUP BY zone_type ORDER BY zone_type
    ''', (INDEX_TICKERS,))
    w.table(
        ['Zone Type', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['zone_type'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right']
    )

    # Daily breakdown: Index vs Custom
    w.subsection('Daily Breakdown: Index vs Custom')
    rows = query('''
        SELECT date,
               CASE WHEN ticker IN %s THEN 'INDEX' ELSE 'CUSTOM' END as grp,
               COUNT(*) as trades,
               ROUND(AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2
        GROUP BY date, grp ORDER BY date, grp
    ''', (INDEX_TICKERS,))
    w.table(
        ['Date', 'Group', 'Trades', 'Win Rate %', 'Avg R'],
        [[str(r['date']), r['grp'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'left', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 5: Tier C — Your Final 4 Down-Selections
    # ================================================================
    w.section('5. Tier C: Your Final 4 Down-Selections')

    # All selections with trade matches
    w.subsection('All Selections with Trade Matches')
    rows = query('''
        SELECT ta.date, ta.ticker, ta.direction,
               COUNT(t.trade_id) as trades,
               SUM(CASE WHEN t.outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM ticker_analysis ta
        LEFT JOIN trades_m5_r_win_2 t ON ta.date = t.date AND ta.ticker = t.ticker
        GROUP BY ta.date, ta.ticker, ta.direction
        ORDER BY ta.date, ta.ticker
    ''')
    table_rows = []
    for r in rows:
        trades = r['trades'] or 0
        if trades == 0:
            table_rows.append([str(r['date']), r['ticker'], r['direction'], 0, 'N/A', 'N/A', 'NO TRADES'])
        else:
            wr = float(r['win_rate'])
            tag = 'STRONG' if wr >= 55 else ('OK' if wr >= 45 else 'WEAK')
            table_rows.append([str(r['date']), r['ticker'], r['direction'], trades, r['win_rate'], r['avg_max_r'], tag])
    w.table(
        ['Date', 'Ticker', 'Direction', 'Trades', 'Win Rate %', 'Avg R', 'Verdict'],
        table_rows,
        ['left', 'left', 'left', 'right', 'right', 'right', 'left']
    )

    # Tier C aggregate
    tier_c = query_one('''
        SELECT COUNT(*) as trades,
               SUM(CASE WHEN t.outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r,
               COUNT(DISTINCT t.ticker) as tickers, COUNT(DISTINCT t.date) as days
        FROM trades_m5_r_win_2 t
        INNER JOIN ticker_analysis ta ON t.date = ta.date AND t.ticker = ta.ticker
    ''')
    w.subsection('Tier C Aggregate')
    w.metric('Trades', tier_c['trades'])
    w.metric('Wins', tier_c['wins'])
    w.metric('Win Rate', tier_c['win_rate'], '%')
    w.metric('Avg Max R', tier_c['avg_max_r'])
    w.metric('Unique Tickers', tier_c['tickers'])
    w.metric('Days with Data', tier_c['days'])
    w.text('')

    # Tier C by model
    w.subsection('Tier C by Model')
    rows = query('''
        SELECT t.model, COUNT(*) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        INNER JOIN ticker_analysis ta ON t.date = ta.date AND t.ticker = ta.ticker
        GROUP BY t.model ORDER BY t.model
    ''')
    w.table(
        ['Model', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['model'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right']
    )

    # Tier C by zone type
    w.subsection('Tier C by Zone Type')
    rows = query('''
        SELECT t.zone_type, COUNT(*) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        INNER JOIN ticker_analysis ta ON t.date = ta.date AND t.ticker = ta.ticker
        GROUP BY t.zone_type ORDER BY t.zone_type
    ''')
    w.table(
        ['Zone Type', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['zone_type'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 6: Same-Day Tier Comparison (Apples to Apples)
    # ================================================================
    w.section('6. Same-Day Tier Comparison')
    w.text('Comparing tiers ONLY on days where Tier C selections exist (apples to apples).')
    w.text('')

    rows = query('''
        SELECT 'A: Full Universe' as tier, 1 as sort_order,
               COUNT(*) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        WHERE t.date IN (SELECT DISTINCT date FROM ticker_analysis WHERE date IN (SELECT DISTINCT date FROM trades_m5_r_win_2))
        UNION ALL
        SELECT 'B: Your 10 Custom' as tier, 2 as sort_order,
               COUNT(*) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        WHERE t.date IN (SELECT DISTINCT date FROM ticker_analysis WHERE date IN (SELECT DISTINCT date FROM trades_m5_r_win_2))
        AND t.ticker NOT IN ('SPY','QQQ','DIA')
        UNION ALL
        SELECT 'C: Your Final 4' as tier, 3 as sort_order,
               COUNT(*) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        INNER JOIN ticker_analysis ta ON t.date = ta.date AND t.ticker = ta.ticker
        UNION ALL
        SELECT 'IDX: SPY/QQQ/DIA' as tier, 4 as sort_order,
               COUNT(*) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        WHERE t.date IN (SELECT DISTINCT date FROM ticker_analysis WHERE date IN (SELECT DISTINCT date FROM trades_m5_r_win_2))
        AND t.ticker IN ('SPY','QQQ','DIA')
        ORDER BY sort_order
    ''')

    tier_a_wr = None
    table_rows = []
    for r in rows:
        wr = float(r['win_rate'])
        if tier_a_wr is None:
            tier_a_wr = wr
            delta = '--'
        else:
            diff = wr - tier_a_wr
            delta = f'{diff:+.2f}pp'
        table_rows.append([r['tier'], r['trades'], r['win_rate'], r['avg_max_r'], delta])

    w.table(
        ['Tier', 'Trades', 'Win Rate %', 'Avg R', 'Edge vs A'],
        table_rows,
        ['left', 'right', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 7: Your Picks vs What You Skipped
    # ================================================================
    w.section('7. Your Picks vs What You Skipped (Custom Only, Same Days)')

    rows = query('''
        SELECT
            CASE
                WHEN EXISTS (SELECT 1 FROM ticker_analysis ta WHERE ta.date = t.date AND ta.ticker = t.ticker)
                THEN 'YOUR PICKS'
                ELSE 'SKIPPED'
            END as selection,
            COUNT(*) as trades,
            ROUND(AVG(CASE WHEN t.outcome = %s THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r,
            COUNT(DISTINCT t.ticker) as tickers
        FROM trades_m5_r_win_2 t
        WHERE t.date IN (SELECT DISTINCT date FROM ticker_analysis WHERE date IN (SELECT DISTINCT date FROM trades_m5_r_win_2))
        AND t.ticker NOT IN (%s, %s, %s)
        GROUP BY selection ORDER BY selection DESC
    ''', ('WIN', 'SPY', 'QQQ', 'DIA'))
    w.table(
        ['Selection', 'Trades', 'Win Rate %', 'Avg R', 'Tickers'],
        [[r['selection'], r['trades'], r['win_rate'], r['avg_max_r'], r['tickers']] for r in rows],
        ['left', 'right', 'right', 'right', 'right']
    )

    # What you left on the table — detail
    w.subsection('Tickers You Left on the Table (Detail)')
    rows = query('''
        SELECT t.date, t.ticker,
               COUNT(*) as trades,
               ROUND(AVG(CASE WHEN t.outcome = %s THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        WHERE t.date IN (SELECT DISTINCT date FROM ticker_analysis WHERE date IN (SELECT DISTINCT date FROM trades_m5_r_win_2))
        AND t.ticker NOT IN (%s, %s, %s)
        AND NOT EXISTS (
            SELECT 1 FROM ticker_analysis ta WHERE ta.date = t.date AND ta.ticker = t.ticker
        )
        GROUP BY t.date, t.ticker
        ORDER BY t.date, win_rate DESC
    ''', ('WIN', 'SPY', 'QQQ', 'DIA'))
    table_rows = []
    for r in rows:
        wr = float(r['win_rate'])
        tag = 'STRONG' if wr >= 55 else ('OK' if wr >= 45 else 'WEAK')
        table_rows.append([str(r['date']), r['ticker'], r['trades'], r['win_rate'], r['avg_max_r'], tag])
    w.table(
        ['Date', 'Ticker', 'Trades', 'Win Rate %', 'Avg R', 'Verdict'],
        table_rows,
        ['left', 'left', 'right', 'right', 'right', 'left']
    )

    # ================================================================
    # SECTION 8: Key Findings
    # ================================================================
    w.section('8. Key Findings')

    # Calculate deltas
    a_wr = float(tier_a['win_rate'])
    b_wr = float(tier_b['win_rate'])
    c_wr = float(tier_c['win_rate']) if tier_c['trades'] > 0 else 0
    a_r = float(tier_a['avg_max_r'])
    b_r = float(tier_b['avg_max_r'])
    c_r = float(tier_c['avg_max_r']) if tier_c['trades'] > 0 else 0

    w.text(f'1. **Full Universe Baseline**: {a_wr}% WR, {a_r} avg R across {tier_a["trades"]} trades')
    w.text(f'2. **Your 10 Custom Picks (Tier B)**: {b_wr}% WR ({b_wr - a_wr:+.2f}pp vs baseline), {b_r} avg R')
    w.text(f'3. **Your Final 4 (Tier C)**: {c_wr}% WR ({c_wr - a_wr:+.2f}pp vs baseline), {c_r} avg R')
    w.text(f'4. **Down-Selection Edge (C vs B)**: {c_wr - b_wr:+.2f}pp win rate, {c_r - b_r:+.2f} avg R')
    w.text('')

    if c_wr > b_wr:
        w.text('**CONCLUSION**: Your down-selection from 10 to 4 ADDS edge. Your judgment is filtering signal from noise.')
    elif c_wr < b_wr:
        w.text('**CONCLUSION**: Your down-selection from 10 to 4 REMOVES edge. You may be over-filtering good setups.')
    else:
        w.text('**CONCLUSION**: Your down-selection is neutral. Consider whether the extra filtering step is worth the effort.')
    w.text('')

    if tier_c['days'] and int(tier_c['days']) < 5:
        w.text(f'**CAVEAT**: Only {tier_c["days"]} overlapping day(s) with both selections and backtest data. '
               f'These findings need more data to confirm. Keep saving daily selections to build the dataset.')
    w.text('')

    w.divider()
    w.text(f'*Analysis covers {shape["days"]} trading days from {shape["first_date"]} to {shape["last_date"]}*')

    w.save()


if __name__ == '__main__':
    run()

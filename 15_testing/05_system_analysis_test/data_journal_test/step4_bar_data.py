"""
Step 4: Bar Data Characteristics vs Outcomes
==============================================
Answers: Do observable characteristics at screening time (ATR, overnight range,
proximity to key levels) predict trade outcomes?

These are the metrics that COULD be captured at screening time but currently
aren't persisted. This analysis determines which ones are worth adding.

Output: data_journal_results/step4_bar_data.md
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db import query, query_one, INDEX_TICKERS
from output import ResultsWriter


def run():
    w = ResultsWriter('step4_bar_data.md')
    w.header('Step 4: Bar Data Characteristics vs Outcomes')
    w.text('Which observable market characteristics at screening time predict wins?')
    w.text('')

    # ================================================================
    # SECTION 1: Data Shape — Bar Data Table
    # ================================================================
    w.section('1. Data Shape')

    shape = query_one('''
        SELECT COUNT(*) as total_rows, COUNT(DISTINCT date) as days,
               COUNT(DISTINCT ticker_id) as tickers
        FROM bar_data
    ''')
    w.metric('Bar Data Rows', shape['total_rows'])
    w.metric('Bar Data Days', shape['days'])
    w.metric('Bar Data Tickers', shape['tickers'])
    w.text('')

    join_stats = query_one('''
        SELECT COUNT(DISTINCT t.trade_id) as trades_with_bar_data
        FROM trades_m5_r_win_2 t
        INNER JOIN bar_data b ON t.date = b.date AND t.ticker = b.ticker
    ''')
    w.metric('Trades with Bar Data Match', join_stats['trades_with_bar_data'])
    w.text('')

    # ================================================================
    # SECTION 2: D1 ATR Ranges vs Outcomes
    # ================================================================
    w.section('2. D1 ATR Ranges vs Outcomes')
    w.text('Do higher-ATR (more volatile) tickers produce better or worse results?')
    w.text('')

    rows = query('''
        SELECT
            CASE
                WHEN b.d1_atr >= 10.0 THEN '$10+ ATR'
                WHEN b.d1_atr >= 5.0 THEN '$5-10 ATR'
                WHEN b.d1_atr >= 3.0 THEN '$3-5 ATR'
                WHEN b.d1_atr >= 1.0 THEN '$1-3 ATR'
                ELSE '< $1 ATR'
            END as atr_range,
            CASE
                WHEN b.d1_atr >= 10.0 THEN 1
                WHEN b.d1_atr >= 5.0 THEN 2
                WHEN b.d1_atr >= 3.0 THEN 3
                WHEN b.d1_atr >= 1.0 THEN 4
                ELSE 5
            END as sort_order,
            COUNT(DISTINCT t.trade_id) as trades,
            ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r,
            COUNT(DISTINCT t.ticker) as tickers
        FROM trades_m5_r_win_2 t
        INNER JOIN bar_data b ON t.date = b.date AND t.ticker = b.ticker
        WHERE b.d1_atr IS NOT NULL AND b.d1_atr > 0
        GROUP BY atr_range, sort_order ORDER BY sort_order
    ''')
    w.table(
        ['ATR Range', 'Trades', 'Win Rate %', 'Avg R', 'Tickers'],
        [[r['atr_range'], r['trades'], r['win_rate'], r['avg_max_r'], r['tickers']] for r in rows],
        ['left', 'right', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 3: ATR as % of Price (Normalized Volatility)
    # ================================================================
    w.section('3. ATR as % of Price (Normalized Volatility)')
    w.text('Normalizes ATR by price so $5 stocks and $500 stocks are comparable.')
    w.text('')

    rows = query('''
        SELECT
            CASE
                WHEN (b.d1_atr / NULLIF(b.price, 0)) * 100 >= 5.0 THEN '5%+ (Very High Vol)'
                WHEN (b.d1_atr / NULLIF(b.price, 0)) * 100 >= 3.0 THEN '3-5% (High Vol)'
                WHEN (b.d1_atr / NULLIF(b.price, 0)) * 100 >= 2.0 THEN '2-3% (Medium Vol)'
                WHEN (b.d1_atr / NULLIF(b.price, 0)) * 100 >= 1.0 THEN '1-2% (Normal Vol)'
                ELSE '< 1% (Low Vol)'
            END as vol_bucket,
            CASE
                WHEN (b.d1_atr / NULLIF(b.price, 0)) * 100 >= 5.0 THEN 1
                WHEN (b.d1_atr / NULLIF(b.price, 0)) * 100 >= 3.0 THEN 2
                WHEN (b.d1_atr / NULLIF(b.price, 0)) * 100 >= 2.0 THEN 3
                WHEN (b.d1_atr / NULLIF(b.price, 0)) * 100 >= 1.0 THEN 4
                ELSE 5
            END as sort_order,
            COUNT(DISTINCT t.trade_id) as trades,
            ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        INNER JOIN bar_data b ON t.date = b.date AND t.ticker = b.ticker
        WHERE b.d1_atr IS NOT NULL AND b.d1_atr > 0 AND b.price > 0
        GROUP BY vol_bucket, sort_order ORDER BY sort_order
    ''')
    w.table(
        ['Volatility', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['vol_bucket'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 4: Overnight Range vs Outcomes
    # ================================================================
    w.section('4. Overnight Range vs Outcomes')
    w.text('Does a wide overnight range (gap) predict better or worse intraday entries?')
    w.text('')

    rows = query('''
        SELECT
            CASE
                WHEN b.d1_overnight_high IS NOT NULL AND b.d1_overnight_low IS NOT NULL
                     AND b.d1_atr > 0
                THEN
                    CASE
                        WHEN ((b.d1_overnight_high - b.d1_overnight_low) / b.d1_atr) >= 1.5 THEN '1.5+ ATR (Wide Gap)'
                        WHEN ((b.d1_overnight_high - b.d1_overnight_low) / b.d1_atr) >= 1.0 THEN '1.0-1.5 ATR'
                        WHEN ((b.d1_overnight_high - b.d1_overnight_low) / b.d1_atr) >= 0.5 THEN '0.5-1.0 ATR'
                        ELSE '< 0.5 ATR (Tight)'
                    END
                ELSE 'NO DATA'
            END as on_range,
            CASE
                WHEN b.d1_overnight_high IS NOT NULL AND b.d1_overnight_low IS NOT NULL
                     AND b.d1_atr > 0
                THEN
                    CASE
                        WHEN ((b.d1_overnight_high - b.d1_overnight_low) / b.d1_atr) >= 1.5 THEN 1
                        WHEN ((b.d1_overnight_high - b.d1_overnight_low) / b.d1_atr) >= 1.0 THEN 2
                        WHEN ((b.d1_overnight_high - b.d1_overnight_low) / b.d1_atr) >= 0.5 THEN 3
                        ELSE 4
                    END
                ELSE 5
            END as sort_order,
            COUNT(DISTINCT t.trade_id) as trades,
            ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        INNER JOIN bar_data b ON t.date = b.date AND t.ticker = b.ticker
        WHERE b.d1_atr IS NOT NULL AND b.d1_atr > 0
        GROUP BY on_range, sort_order ORDER BY sort_order
    ''')
    w.table(
        ['Overnight Range', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['on_range'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 5: Price Level ($) vs Outcomes
    # ================================================================
    w.section('5. Price Level vs Outcomes')
    w.text('Do higher-priced or lower-priced stocks perform differently?')
    w.text('')

    rows = query('''
        SELECT
            CASE
                WHEN b.price >= 500 THEN '$500+'
                WHEN b.price >= 200 THEN '$200-500'
                WHEN b.price >= 100 THEN '$100-200'
                WHEN b.price >= 50 THEN '$50-100'
                WHEN b.price >= 20 THEN '$20-50'
                ELSE '< $20'
            END as price_range,
            CASE
                WHEN b.price >= 500 THEN 1
                WHEN b.price >= 200 THEN 2
                WHEN b.price >= 100 THEN 3
                WHEN b.price >= 50 THEN 4
                WHEN b.price >= 20 THEN 5
                ELSE 6
            END as sort_order,
            COUNT(DISTINCT t.trade_id) as trades,
            ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r,
            COUNT(DISTINCT t.ticker) as tickers
        FROM trades_m5_r_win_2 t
        INNER JOIN bar_data b ON t.date = b.date AND t.ticker = b.ticker
        WHERE b.price IS NOT NULL AND b.price > 0
        GROUP BY price_range, sort_order ORDER BY sort_order
    ''')
    w.table(
        ['Price Range', 'Trades', 'Win Rate %', 'Avg R', 'Tickers'],
        [[r['price_range'], r['trades'], r['win_rate'], r['avg_max_r'], r['tickers']] for r in rows],
        ['left', 'right', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 6: Proximity to Prior Day Levels
    # ================================================================
    w.section('6. Proximity to Prior Day Close')
    w.text('How far from prior day close was entry? (as % of ATR)')
    w.text('')

    rows = query('''
        SELECT
            CASE
                WHEN b.d1_prior_close IS NOT NULL AND b.d1_atr > 0
                THEN
                    CASE
                        WHEN ABS(b.price - b.d1_prior_close) / b.d1_atr >= 2.0 THEN '2+ ATR from PDC'
                        WHEN ABS(b.price - b.d1_prior_close) / b.d1_atr >= 1.0 THEN '1-2 ATR from PDC'
                        WHEN ABS(b.price - b.d1_prior_close) / b.d1_atr >= 0.5 THEN '0.5-1 ATR from PDC'
                        ELSE '< 0.5 ATR from PDC'
                    END
                ELSE 'NO DATA'
            END as proximity,
            CASE
                WHEN b.d1_prior_close IS NOT NULL AND b.d1_atr > 0
                THEN
                    CASE
                        WHEN ABS(b.price - b.d1_prior_close) / b.d1_atr >= 2.0 THEN 1
                        WHEN ABS(b.price - b.d1_prior_close) / b.d1_atr >= 1.0 THEN 2
                        WHEN ABS(b.price - b.d1_prior_close) / b.d1_atr >= 0.5 THEN 3
                        ELSE 4
                    END
                ELSE 5
            END as sort_order,
            COUNT(DISTINCT t.trade_id) as trades,
            ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        INNER JOIN bar_data b ON t.date = b.date AND t.ticker = b.ticker
        WHERE b.d1_atr IS NOT NULL AND b.d1_atr > 0
        GROUP BY proximity, sort_order ORDER BY sort_order
    ''')
    w.table(
        ['Proximity to PDC', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['proximity'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 7: Your Picks — Bar Data Profile
    # ================================================================
    w.section('7. Your Final 4: Bar Data Profile vs Skipped')
    w.text('Did your selected tickers have different ATR/price/gap profiles?')
    w.text('')

    rows = query('''
        SELECT
            CASE
                WHEN EXISTS (SELECT 1 FROM ticker_analysis ta WHERE ta.date = t.date AND ta.ticker = t.ticker)
                THEN 'YOUR PICKS'
                ELSE 'SKIPPED'
            END as selection,
            ROUND(AVG(b.d1_atr), 2) as avg_atr,
            ROUND(AVG(b.price), 2) as avg_price,
            ROUND(AVG(CASE WHEN b.d1_atr > 0 THEN (b.d1_atr / b.price) * 100 END), 2) as avg_atr_pct,
            ROUND(AVG(CASE WHEN b.d1_overnight_high IS NOT NULL AND b.d1_overnight_low IS NOT NULL AND b.d1_atr > 0
                            THEN (b.d1_overnight_high - b.d1_overnight_low) / b.d1_atr END), 2) as avg_on_range_atr,
            COUNT(DISTINCT t.trade_id) as trades,
            ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM trades_m5_r_win_2 t
        INNER JOIN bar_data b ON t.date = b.date AND t.ticker = b.ticker
        WHERE t.date IN (SELECT DISTINCT date FROM ticker_analysis WHERE date IN (SELECT DISTINCT date FROM trades_m5_r_win_2))
        AND t.ticker NOT IN ('SPY', 'QQQ', 'DIA')
        GROUP BY selection ORDER BY selection DESC
    ''')
    w.table(
        ['Selection', 'Avg ATR', 'Avg Price', 'ATR %', 'O/N Range (ATR)', 'Trades', 'WR %', 'Avg R'],
        [[r['selection'], r['avg_atr'], r['avg_price'], r['avg_atr_pct'],
          r['avg_on_range_atr'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'right', 'right', 'right', 'right', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 8: Key Findings
    # ================================================================
    w.section('8. Key Findings')
    w.text('**Review the tables above to answer:**')
    w.text('1. Is there an ATR sweet spot? (too low = no movement, too high = noise)')
    w.text('2. Does overnight gap size help or hurt?')
    w.text('3. Do certain price ranges consistently outperform?')
    w.text('4. Does proximity to prior day close matter?')
    w.text('5. What bar data characteristics should become screener filters?')
    w.text('')
    w.text('**Metrics Worth Persisting (if they show edge):**')
    w.text('- D1 ATR % of price (normalized volatility)')
    w.text('- Overnight range as ATR multiple')
    w.text('- Distance from prior day close as ATR multiple')
    w.text('- Price level bucket')
    w.text('')

    w.divider()
    w.save()


if __name__ == '__main__':
    run()

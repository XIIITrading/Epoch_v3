"""
Journal Aggregate Analysis — Subjective vs Objective
======================================================
Cross-references your subjective journal entries (confidence, thesis, bias)
against actual trade outcomes to surface blind spots and patterns.

This is the "weekly review" script — run it with Claude to get insights.

Output: journal_results/journal_aggregate.md
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from db import query, query_one

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'journal_results')


class ResultsWriter:
    """Minimal results writer for journal analysis."""

    def __init__(self, filename: str):
        os.makedirs(RESULTS_DIR, exist_ok=True)
        self.filepath = os.path.join(RESULTS_DIR, filename)
        self.lines = []

    def header(self, title: str):
        from datetime import datetime
        self._write(f'# {title}')
        self._write(f'> Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self._write('')

    def section(self, title: str):
        self._write(f'## {title}')
        self._write('')

    def subsection(self, title: str):
        self._write(f'### {title}')
        self._write('')

    def text(self, line: str = ''):
        self._write(line)

    def metric(self, label: str, value, unit: str = ''):
        display = f'{value}{unit}' if unit else str(value)
        self._write(f'- **{label}**: {display}')

    def table(self, headers, rows, alignments=None):
        if not rows:
            self._write('*No data*')
            self._write('')
            return
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        self._write('| ' + ' | '.join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers)) + ' |')
        if alignments:
            parts = []
            for i, a in enumerate(alignments):
                w = col_widths[i]
                parts.append('-' * (w - 1) + ':' if a == 'right' else '-' * w)
            self._write('| ' + ' | '.join(parts) + ' |')
        else:
            self._write('| ' + ' | '.join('-' * w for w in col_widths) + ' |')
        for row in rows:
            self._write('| ' + ' | '.join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + ' |')
        self._write('')

    def divider(self):
        self._write('---')
        self._write('')

    def save(self):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.lines))
        print(f'\n[SAVED] {self.filepath}')

    def _write(self, line):
        print(line)
        self.lines.append(line)


def run():
    w = ResultsWriter('journal_aggregate.md')
    w.header('Journal Aggregate Analysis — Subjective vs Objective')
    w.text('Cross-referencing your stated reasoning against actual outcomes.')
    w.text('')

    # ================================================================
    # SECTION 1: Journal Data Shape
    # ================================================================
    w.section('1. Journal Data Shape')

    shape = query_one('''
        SELECT COUNT(*) as total_entries,
               COUNT(DISTINCT date) as days,
               COUNT(DISTINCT ticker) as tickers,
               SUM(CASE WHEN selection_type = 'SELECTED' THEN 1 ELSE 0 END) as selected,
               SUM(CASE WHEN selection_type = 'SKIPPED' THEN 1 ELSE 0 END) as skipped
        FROM journal_selections
    ''')
    if not shape or shape['total_entries'] == 0:
        w.text('**No journal entries found.** Run journal_session.py first to record selections.')
        w.save()
        return

    w.metric('Total Entries', shape['total_entries'])
    w.metric('Journal Days', shape['days'])
    w.metric('Unique Tickers', shape['tickers'])
    w.metric('Selected', shape['selected'])
    w.metric('Skipped', shape['skipped'])
    w.text('')

    # ================================================================
    # SECTION 2: Confidence vs Outcomes
    # ================================================================
    w.section('2. Confidence Level vs Actual Outcomes')
    w.text('Does your confidence rating predict actual win rate?')
    w.text('')

    rows = query('''
        SELECT j.confidence,
               COUNT(DISTINCT t.trade_id) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r,
               COUNT(DISTINCT j.ticker) as tickers
        FROM journal_selections j
        LEFT JOIN trades_m5_r_win_2 t ON j.date = t.date AND j.ticker = t.ticker
        WHERE j.selection_type = 'SELECTED' AND j.confidence IS NOT NULL
        GROUP BY j.confidence ORDER BY j.confidence
    ''')
    w.table(
        ['Confidence', 'Trades', 'Win Rate %', 'Avg R', 'Tickers'],
        [[r['confidence'], r['trades'] or 0, r['win_rate'] or 'N/A', r['avg_max_r'] or 'N/A', r['tickers']] for r in rows],
        ['right', 'right', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 3: Directional Bias Accuracy
    # ================================================================
    w.section('3. Directional Bias Accuracy')
    w.text('When you say BULL, do the LONG trades actually win more?')
    w.text('')

    rows = query('''
        SELECT j.directional_bias, t.direction,
               COUNT(DISTINCT t.trade_id) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM journal_selections j
        INNER JOIN trades_m5_r_win_2 t ON j.date = t.date AND j.ticker = t.ticker
        WHERE j.selection_type = 'SELECTED' AND j.directional_bias IS NOT NULL
        GROUP BY j.directional_bias, t.direction ORDER BY j.directional_bias, t.direction
    ''')
    w.table(
        ['Your Bias', 'Trade Dir', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['directional_bias'], r['direction'], r['trades'], r['win_rate'], r['avg_max_r']] for r in rows],
        ['left', 'left', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 4: Skipped Ticker Performance
    # ================================================================
    w.section('4. Tickers You Skipped — Did You Miss Edge?')

    rows = query('''
        SELECT j.ticker, j.date,
               j.thesis as skip_reason,
               COUNT(DISTINCT t.trade_id) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM journal_selections j
        LEFT JOIN trades_m5_r_win_2 t ON j.date = t.date AND j.ticker = t.ticker
        WHERE j.selection_type = 'SKIPPED'
        GROUP BY j.ticker, j.date, j.thesis
        ORDER BY j.date, j.ticker
    ''')
    w.table(
        ['Ticker', 'Date', 'Skip Reason', 'Trades', 'Win Rate %', 'Avg R'],
        [[r['ticker'], str(r['date']), (r['skip_reason'] or '')[:50], r['trades'] or 0,
          r['win_rate'] or 'N/A', r['avg_max_r'] or 'N/A'] for r in rows],
        ['left', 'left', 'left', 'right', 'right', 'right']
    )

    # ================================================================
    # SECTION 5: Hindsight Score vs Actual Outcomes
    # ================================================================
    w.section('5. Hindsight Score Calibration')
    w.text('Does your post-session hindsight score match actual R achieved?')
    w.text('')

    rows = query('''
        SELECT j.hindsight_score,
               COUNT(*) as entries,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as actual_wr,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r
        FROM journal_selections j
        LEFT JOIN trades_m5_r_win_2 t ON j.date = t.date AND j.ticker = t.ticker
        WHERE j.hindsight_score IS NOT NULL
        GROUP BY j.hindsight_score ORDER BY j.hindsight_score
    ''')
    if rows:
        w.table(
            ['Hindsight', 'Entries', 'Actual WR %', 'Avg R'],
            [[r['hindsight_score'], r['entries'], r['actual_wr'] or 'N/A', r['avg_max_r'] or 'N/A'] for r in rows],
            ['right', 'right', 'right', 'right']
        )
    else:
        w.text('*No hindsight scores recorded yet.*')
        w.text('')

    # ================================================================
    # SECTION 6: Emotional State vs Performance
    # ================================================================
    w.section('6. Session Emotional State vs Performance')

    rows = query('''
        SELECT dc.emotional_state,
               COUNT(DISTINCT t.trade_id) as trades,
               ROUND(AVG(CASE WHEN t.outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
               ROUND(AVG(COALESCE(t.max_r_achieved, 0)), 2) as avg_max_r,
               ROUND(AVG(dc.rule_adherence), 1) as avg_rule_adherence
        FROM journal_daily_context dc
        INNER JOIN trades_m5_r_win_2 t ON dc.date = t.date
        INNER JOIN journal_selections j ON j.date = dc.date AND j.ticker = t.ticker
            AND j.selection_type = 'SELECTED'
        WHERE dc.emotional_state IS NOT NULL
        GROUP BY dc.emotional_state ORDER BY dc.emotional_state
    ''')
    if rows:
        w.table(
            ['Emotional State', 'Trades', 'Win Rate %', 'Avg R', 'Rule Adherence'],
            [[r['emotional_state'], r['trades'], r['win_rate'], r['avg_max_r'], r['avg_rule_adherence']] for r in rows],
            ['left', 'right', 'right', 'right', 'right']
        )
    else:
        w.text('*No emotional state data recorded yet.*')
        w.text('')

    # ================================================================
    # SECTION 7: Key Insights for Claude
    # ================================================================
    w.section('7. Key Questions for Claude Analysis')
    w.text('**Based on the data above, Claude should address:**')
    w.text('1. Is your confidence calibrated? (high confidence = higher WR?)')
    w.text('2. Is your directional bias accurate? (BULL bias → LONG wins?)')
    w.text('3. Are you skipping tickers that would have been profitable?')
    w.text('4. What common themes appear in your skip reasons for missed winners?')
    w.text('5. Does your emotional state on a given day predict session quality?')
    w.text('6. What patterns in your thesis language correlate with wins vs losses?')
    w.text('')

    w.divider()
    w.save()


if __name__ == '__main__':
    run()

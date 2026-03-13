"""
Daily Journal Session — Subjective Q&A Workflow
=================================================
Walks through canned questions for each ticker selection.
Designed to be run by Claude (via Skill) or interactively.

Two modes:
  1. CLI mode: python journal_session.py  (interactive prompts)
  2. Claude mode: import and call record_selection() / record_daily_context()

Output: Writes to Supabase journal_selections + journal_daily_context tables.
"""
import sys
import os
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(__file__))
from db import execute, query, query_one


# ================================================================
# CANNED QUESTIONS — Selection Journal
# ================================================================
SELECTION_QUESTIONS = [
    {
        'field': 'thesis',
        'question': 'Why did you select this ticker today? What is your thesis?',
        'hint': 'e.g., "Strong D1 bull structure, gapping up 3% on earnings beat, T3 zone at 182.50"'
    },
    {
        'field': 'directional_bias',
        'question': 'What is your directional bias?',
        'options': ['BULL', 'BEAR', 'NEUTRAL'],
        'hint': 'Your expected direction for this ticker today'
    },
    {
        'field': 'bias_reasoning',
        'question': 'What drives your directional bias?',
        'hint': 'e.g., "D1+H4 aligned bull, above VWAP, strong overnight volume"'
    },
    {
        'field': 'confidence',
        'question': 'Confidence level (1-5)?',
        'options': ['1 (Low)', '2', '3 (Medium)', '4', '5 (High)'],
        'hint': '1=barely qualifies, 5=textbook setup'
    },
    {
        'field': 'invalidation',
        'question': 'What would invalidate this pick?',
        'hint': 'e.g., "Break below 180.00 D1 strong level, or SPY reversal below 520"'
    },
    {
        'field': 'zone_focus',
        'question': 'Which zone are you watching and why?',
        'hint': 'e.g., "Primary zone at 182.50 (T3, 5 confluences including monthly OHLC + options)"'
    },
    {
        'field': 'concerns',
        'question': 'Any hesitation or red flags?',
        'hint': 'e.g., "Earnings volatility could overshoot zones, FOMC tomorrow"'
    },
]

SKIP_QUESTIONS = [
    {
        'field': 'thesis',
        'question': 'Why did you skip this ticker?',
        'hint': 'e.g., "Choppy structure, low confluence zones, already extended"'
    },
    {
        'field': 'concerns',
        'question': 'What specifically concerned you?',
        'hint': 'e.g., "D1 neutral, no clear direction, zones too far from price"'
    },
]

DAILY_CONTEXT_QUESTIONS = [
    {
        'field': 'market_regime',
        'question': 'What is the overall market regime today?',
        'options': ['BULL', 'BEAR', 'NEUTRAL', 'CHOPPY'],
    },
    {
        'field': 'key_events',
        'question': 'Any key events today? (earnings, FOMC, CPI, etc.)',
        'hint': 'Leave blank if nothing notable'
    },
    {
        'field': 'spy_bias',
        'question': 'SPY directional bias?',
        'options': ['BULL', 'BEAR', 'NEUTRAL'],
    },
    {
        'field': 'overall_plan',
        'question': 'What is your plan for today?',
        'hint': 'e.g., "Focus on LONG setups in tech, avoid counter-trend, tight stops"'
    },
]

POST_SESSION_QUESTIONS = [
    {
        'field': 'actual_outcome',
        'question': 'What was the actual outcome for this ticker?',
        'options': ['WIN', 'LOSS', 'NO_TRADE', 'MISSED'],
    },
    {
        'field': 'outcome_notes',
        'question': 'What happened? What did you learn?',
        'hint': 'e.g., "Zone held perfectly but I was too late on entry. Need to set alerts."'
    },
    {
        'field': 'hindsight_score',
        'question': 'In hindsight, was this a good pick? (1-5)',
        'options': ['1 (Bad pick)', '2', '3 (Neutral)', '4', '5 (Great pick)'],
    },
]

SESSION_REVIEW_QUESTIONS = [
    {
        'field': 'session_grade',
        'question': 'Grade your session today (A/B/C/D/F)',
        'options': ['A', 'B', 'C', 'D', 'F'],
    },
    {
        'field': 'session_notes',
        'question': 'What went well and what didn\'t?',
    },
    {
        'field': 'rule_adherence',
        'question': 'How well did you follow your rules? (1-5)',
        'options': ['1 (Broke rules)', '2', '3 (Mostly followed)', '4', '5 (Perfect adherence)'],
    },
    {
        'field': 'emotional_state',
        'question': 'What was your emotional state?',
        'options': ['CALM', 'ANXIOUS', 'CONFIDENT', 'TILTED', 'FOCUSED'],
    },
]


# ================================================================
# DATA RECORDING FUNCTIONS (used by Claude Skill)
# ================================================================

def record_selection(session_date: date, ticker: str, selection_type: str,
                     selection_rank: int = None, **responses):
    """
    Record a single ticker selection with subjective responses.

    Args:
        session_date: Trading date
        ticker: Ticker symbol
        selection_type: 'SELECTED' or 'SKIPPED'
        selection_rank: Conviction rank (1=highest) for SELECTED tickers
        **responses: Field responses from SELECTION_QUESTIONS
                     (thesis, directional_bias, bias_reasoning, confidence,
                      invalidation, zone_focus, concerns, market_context)
    """
    fields = ['date', 'ticker', 'selection_type', 'selection_rank']
    values = [session_date, ticker, selection_type, selection_rank]

    valid_fields = {'thesis', 'directional_bias', 'bias_reasoning', 'confidence',
                    'invalidation', 'zone_focus', 'concerns', 'market_context'}

    for field, value in responses.items():
        if field in valid_fields and value is not None:
            fields.append(field)
            values.append(value)

    placeholders = ', '.join(['%s'] * len(values))
    field_names = ', '.join(fields)
    update_fields = ', '.join(f'{f} = EXCLUDED.{f}' for f in fields if f not in ('date', 'ticker'))

    sql = f'''
        INSERT INTO journal_selections ({field_names})
        VALUES ({placeholders})
        ON CONFLICT (date, ticker) DO UPDATE SET {update_fields}
    '''
    return execute(sql, values)


def record_daily_context(session_date: date, **responses):
    """Record daily market context."""
    fields = ['date']
    values = [session_date]

    valid_fields = {'market_regime', 'key_events', 'spy_bias', 'overall_plan'}

    for field, value in responses.items():
        if field in valid_fields and value is not None:
            fields.append(field)
            values.append(value)

    placeholders = ', '.join(['%s'] * len(values))
    field_names = ', '.join(fields)
    update_fields = ', '.join(f'{f} = EXCLUDED.{f}' for f in fields if f != 'date')

    sql = f'''
        INSERT INTO journal_daily_context ({field_names})
        VALUES ({placeholders})
        ON CONFLICT (date) DO UPDATE SET {update_fields}
    '''
    return execute(sql, values)


def record_post_session(session_date: date, ticker: str, **responses):
    """Record post-session review for a ticker."""
    updates = []
    values = []

    valid_fields = {'actual_outcome', 'outcome_notes', 'hindsight_score'}

    for field, value in responses.items():
        if field in valid_fields and value is not None:
            updates.append(f'{field} = %s')
            values.append(value)

    if not updates:
        return 0

    values.extend([session_date, ticker])
    sql = f'''
        UPDATE journal_selections SET {', '.join(updates)}
        WHERE date = %s AND ticker = %s
    '''
    return execute(sql, values)


def record_session_review(session_date: date, **responses):
    """Record end-of-day session review."""
    updates = []
    values = []

    valid_fields = {'session_grade', 'session_notes', 'rule_adherence', 'emotional_state'}

    for field, value in responses.items():
        if field in valid_fields and value is not None:
            updates.append(f'{field} = %s')
            values.append(value)

    if not updates:
        return 0

    values.append(session_date)
    sql = f'''
        UPDATE journal_daily_context SET {', '.join(updates)}
        WHERE date = %s
    '''
    return execute(sql, values)


# ================================================================
# CLI MODE
# ================================================================

def _ask(question_def):
    """Prompt user for a single question."""
    print(f'\n  {question_def["question"]}')
    if 'hint' in question_def:
        print(f'  (Hint: {question_def["hint"]})')
    if 'options' in question_def:
        for i, opt in enumerate(question_def['options'], 1):
            print(f'    {i}. {opt}')
        choice = input('  > ').strip()
        if choice.isdigit() and 1 <= int(choice) <= len(question_def['options']):
            raw = question_def['options'][int(choice) - 1]
            # Extract just the value part (before any parenthetical)
            return raw.split(' (')[0].strip()
        return choice
    return input('  > ').strip()


def cli_session():
    """Run interactive CLI journal session."""
    session_date = date.today()
    print(f'\n{"=" * 60}')
    print(f'  DAILY JOURNAL SESSION — {session_date}')
    print(f'{"=" * 60}')

    # Daily context first
    print(f'\n--- MARKET CONTEXT ---')
    context = {}
    for q in DAILY_CONTEXT_QUESTIONS:
        answer = _ask(q)
        if answer:
            context[q['field']] = answer
    record_daily_context(session_date, **context)
    print('\n  [Saved daily context]')

    # Selected tickers
    print(f'\n--- SELECTED TICKERS ---')
    selected = input('\n  Enter your selected tickers (comma-separated): ').strip()
    if selected:
        tickers = [t.strip().upper() for t in selected.split(',')]
        for rank, ticker in enumerate(tickers, 1):
            print(f'\n  --- {ticker} (Rank #{rank}) ---')
            responses = {}
            for q in SELECTION_QUESTIONS:
                answer = _ask(q)
                if answer:
                    responses[q['field']] = int(answer) if q['field'] == 'confidence' else answer
            responses['market_context'] = context.get('overall_plan', '')
            record_selection(session_date, ticker, 'SELECTED', rank, **responses)
            print(f'  [Saved {ticker}]')

    # Skipped tickers
    print(f'\n--- SKIPPED TICKERS ---')
    skipped = input('\n  Enter skipped tickers (comma-separated, or blank): ').strip()
    if skipped:
        tickers = [t.strip().upper() for t in skipped.split(',')]
        for ticker in tickers:
            print(f'\n  --- {ticker} (SKIPPED) ---')
            responses = {}
            for q in SKIP_QUESTIONS:
                answer = _ask(q)
                if answer:
                    responses[q['field']] = answer
            record_selection(session_date, ticker, 'SKIPPED', **responses)
            print(f'  [Saved {ticker}]')

    print(f'\n{"=" * 60}')
    print(f'  SESSION RECORDED — {session_date}')
    print(f'{"=" * 60}\n')


if __name__ == '__main__':
    cli_session()

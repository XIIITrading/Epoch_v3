---
name: user-journal
description: Run the daily selection journal Q&A session — walk through canned questions about ticker selections, record reasoning to Supabase, and optionally run aggregate analysis. Use when asked to journal, record selections, do daily review, or run journal analysis.
allowed-tools: Bash(python *), Bash(cd *), Read, AskUserQuestion
---

# User Journal — Daily Selection Q&A

## Overview

This skill runs a two-part journaling workflow:
1. **Pre-market Q&A** — Walk through ticker selections with canned questions
2. **Post-session review** — Record outcomes and hindsight scores
3. **Aggregate analysis** — Cross-reference subjective data against actual outcomes

## Pre-Market Session Flow

Walk the user through these questions for EACH of their selected tickers (typically 4):

### Daily Context (once per day)
1. What is the overall market regime today? (BULL / BEAR / NEUTRAL / CHOPPY)
2. Any key events today? (earnings, FOMC, CPI, etc.)
3. SPY directional bias? (BULL / BEAR / NEUTRAL)
4. What is your plan for today?

### Per Ticker — SELECTED (for each of the ~4 picks)
1. **Thesis**: Why did you select this ticker today?
2. **Directional Bias**: BULL / BEAR / NEUTRAL
3. **Bias Reasoning**: What drives your directional bias?
4. **Confidence** (1-5): 1=barely qualifies, 5=textbook setup
5. **Invalidation**: What would invalidate this pick?
6. **Zone Focus**: Which zone are you watching and why?
7. **Concerns**: Any hesitation or red flags?

### Per Ticker — SKIPPED (for notable skips from the 10)
1. **Skip Reason**: Why did you skip this ticker?
2. **Concerns**: What specifically concerned you?

## Recording Data

After collecting responses, save to Supabase using the journal_session module:

```python
import sys
sys.path.insert(0, r'C:\XIIITradingSystems\Epoch_v3\15_testing\05_system_analysis_test\user_journal_test')
from journal_session import record_selection, record_daily_context, record_post_session, record_session_review
from datetime import date

# Record daily context
record_daily_context(date.today(),
    market_regime='BULL',
    spy_bias='BULL',
    key_events='FOMC minutes at 2pm',
    overall_plan='Focus on LONG setups in tech')

# Record a selected ticker
record_selection(date.today(), 'AMD', 'SELECTED', selection_rank=1,
    thesis='Strong D1 bull, gapping up 2.5% on AI news',
    directional_bias='BULL',
    bias_reasoning='D1+H4 aligned, above VWAP',
    confidence=4,
    invalidation='Break below 165.00 D1 strong',
    zone_focus='Primary at 172.50, T3 with 5 confluences',
    concerns='FOMC might cause volatility')

# Record a skipped ticker
record_selection(date.today(), 'HIMS', 'SKIPPED',
    thesis='Choppy D1 structure, low confluence zones',
    concerns='No clear direction, zones too far from price')
```

## Post-Session Review

At end of day, walk through post-session questions:

### Per Ticker
1. **Outcome**: WIN / LOSS / NO_TRADE / MISSED
2. **Outcome Notes**: What happened? What did you learn?
3. **Hindsight Score** (1-5): Was this a good pick in hindsight?

### Session Review (once per day)
1. **Session Grade**: A / B / C / D / F
2. **Session Notes**: What went well / what didn't
3. **Rule Adherence** (1-5): How well did you follow your rules?
4. **Emotional State**: CALM / ANXIOUS / CONFIDENT / TILTED / FOCUSED

## Aggregate Analysis

Run the aggregate analysis to cross-reference journal data with outcomes:

!`cd C:\XIIITradingSystems\Epoch_v3\15_testing\05_system_analysis_test\user_journal_test && python journal_analysis.py`

Then read `journal_results/journal_aggregate.md` and provide insights on:
- Is confidence calibrated? (higher confidence = higher WR?)
- Is directional bias accurate?
- What patterns in skip reasons correlate with missed winners?
- Does emotional state predict session quality?

## Supabase Schema

Tables: `journal_selections`, `journal_daily_context`
Schema file: `C:\XIIITradingSystems\Epoch_v3\15_testing\05_system_analysis_test\user_journal_test\journal_schema.sql`

**IMPORTANT**: Run the schema SQL in Supabase SQL Editor before first use.

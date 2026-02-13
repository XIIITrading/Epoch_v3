# DOW AI v3.0 - Implementation Brief for Claude Desktop

## Objective
Build a DOW AI system where Claude receives raw market data + learned context, then applies its own reasoning to make TRADE/NO_TRADE decisions. No prescriptive rules or calculated recommendations - just data and context.

---

## Current Problem
- v2.0.1 achieved 84% overall accuracy but became too restrictive
- Only 25% of analyses result in TRADE recommendations
- When Claude says TRADE, hit rate is only 50% (coin flip)
- Root cause: Prompt provides too many rules/thresholds that make Claude a calculator, not an analyst

---

## Proposed Architecture: v3.0

### What Claude Receives

**1. TRADE SETUP (Raw Facts)**
```
Ticker: AMD
Direction: LONG
Entry Price: $125.45
Date/Time: 2026-01-24 14:05

M1 Indicator Bars (last 15 bars before entry):
- Bar 1: O:125.20 H:125.35 L:125.15 C:125.30 | Vol:45000 | Delta:+12000 | ROC:+25%
- Bar 2: ...
- [Full 15-bar dataset]

Entry Indicators (from entry_indicators table):
- SMA Alignment: BULL
- H1 Structure: BULL
- Health Score: 7/10
```

**2. LEARNED CONTEXT (Updated from backtesting)**

Historical edges discovered through statistical testing (3,615 trades analyzed):

**Structure Edge** (Most Predictive - 153 tests, 47 significant):
- H1 Structure aligned with direction: +36.0pp above baseline
- H1 Structure Alignment score: +26.2pp
- M15 Structure Direction: +22.6pp

**SMA Edge** (63 tests, 10 significant):
- SMA Spread Magnitude (wider = stronger): +16.4pp
- SMA Momentum (widening vs narrowing): +5.0pp

**Candle Range Edge** (63 tests, 40 significant):
- Range >= 0.18%: +19.1pp
- Range >= 0.15%: +15.7pp
- Range >= 0.12%: +13.5pp
- Below 0.12%: Absorption zone - reduced edge

**Volume Delta Edge** (36 tests, 7 significant):
- Delta aligned with direction: +4.2pp
- High magnitude delta (top quintile): +9.7pp (ALL), +16.7pp (LONG)

**Volume ROC Edge** (54 tests, 7 significant):
- ROC >= 30%: +4.3pp (ALL), +6.6pp (SHORT)
- High magnitude ROC (top quintile): +14.5pp (SHORT)

**3. MODEL BASELINE PERFORMANCE**

| Model | Direction | Trades | Base WR | Best WR (w/ stop) |
|-------|-----------|--------|---------|-------------------|
| EPCH1 | LONG | 94 | 42.6% | 46.8% |
| EPCH1 | SHORT | 94 | 41.5% | 48.9% |
| EPCH2 | LONG | 931 | 43.2% | 53.2% |
| EPCH2 | SHORT | 993 | 45.7% | 52.0% |
| EPCH3 | LONG | 74 | 40.5% | 48.7% |
| EPCH3 | SHORT | 65 | 53.9% | 66.2% |
| EPCH4 | LONG | 676 | 45.6% | 57.8% |
| EPCH4 | SHORT | 688 | 42.2% | 56.3% |

**4. ZONE PERFORMANCE**

Primary Zones:
- LONG: Low=43.9%, Mid=74.2%, High=24.7%
- SHORT: Low=45.0%, Mid=64.1%, High=41.4%

Secondary Zones:
- LONG: Low=46.1%, Mid=59.8%, High=36.9%
- SHORT: Low=44.4%, Mid=47.3%, High=40.0%

---

## What Claude Does NOT Receive
- No "WHEN TO SAY TRADE" rules
- No "WHEN TO SAY NO_TRADE" rules
- No thresholds presented as blockers
- No pre-calculated status labels (FAVORABLE/NEUTRAL/WEAK)
- No alignment scores
- No recommendations

---

## The Ask to Claude

```
You are DOW, analyzing a potential trade entry.

Review the raw M1 bars and entry indicators. Consider the learned edges
from our backtesting - these show what conditions have historically
improved win rates above baseline.

Based on your analysis of this specific setup against the learned patterns,
provide your assessment:

DECISION: [TRADE / NO_TRADE]
CONFIDENCE: [HIGH / MEDIUM / LOW]

KEY FACTORS: [What you observed in the data that drove your decision]
```

---

## Implementation Components

### Files to Modify

1. **dow_helper_prompt.py**
   - New template: `DOW_PROMPT_TEMPLATE_V3`
   - New builder: `build_prompt_v3()`
   - Passes raw M1 bars, not averages
   - Passes full context files, not summaries
   - No rules/thresholds in prompt

2. **batch_analyze.py**
   - Add `--v3` flag
   - Pass raw bar data to prompt
   - Keep parsing logic for TRADE/NO_TRADE extraction

3. **Context Files** (unchanged structure, continuously updated)
   - `indicator_edges.json` - edges from 03_indicators testing
   - `model_stats.json` - baseline performance by model/direction
   - `zone_performance.json` - win rates by zone position

### Data Flow

```
[M1 Bars from DB] ─────────────┐
                               │
[Entry Indicators from DB] ────┼──► [Prompt Builder v3] ──► [Claude API]
                               │
[Context Files (JSON)] ────────┘
                                           │
                                           ▼
                                    [TRADE/NO_TRADE]
                                    [Confidence]
                                    [Key Factors]
```

---

## Success Metrics

Target for v3.0:
- TRADE call rate: 40-60% (not 25%)
- When Claude says TRADE, win rate: >55% (not 50%)
- When Claude says NO_TRADE, loss rate: >55%
- Overall accuracy: Maintain 65%+

---

## Questions for Implementation

1. Should M1 bars be presented as raw OHLCV or include calculated fields (delta, ROC)?
2. How many M1 bars? Current: 15 bars (~15 min ramp-up)
3. Should we include the specific model (EPCH1-4) being traded?
4. Format preference for bars: Table, JSON, or compact text?

---

## Continuous Learning Loop

```
[Live Trading]
      │
      ▼
[Trade Outcomes recorded]
      │
      ▼
[Backtest Analysis] ──► Updates indicator_edges.json
      │                         model_stats.json
      │                         zone_performance.json
      ▼
[DOW AI reads updated context]
      │
      ▼
[Improved decisions over time]
```

The context files ARE the learned knowledge. Claude applies reasoning. Together = adaptive system.

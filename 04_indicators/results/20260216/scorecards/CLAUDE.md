# Scorecard Analysis - Claude Code Instructions

## What These Files Are
Scorecards rank the top 5 indicators for each of 4 trade types based on
statistical edge (effect size + significance). They tell you which indicators
to check BEFORE taking a specific type of trade.

## File Index
- `tier_ranking.md` -- Full ranking of all 11 indicators across all 4 trade types
- `long_continuation.md` -- Scorecard for LONG + EPCH1/EPCH3 trades
- `short_continuation.md` -- Scorecard for SHORT + EPCH1/EPCH3 trades
- `long_rejection.md` -- Scorecard for LONG + EPCH2/EPCH4 trades
- `short_rejection.md` -- Scorecard for SHORT + EPCH2/EPCH4 trades
- `rubric_summary.md` -- Master overview with cross-type patterns

## How to Read a Scorecard
Each scorecard has:
1. **Trade Type Context** -- direction, models, sample size, baseline win rate
2. **Top 5 Indicators** -- ranked by tier (S/A/B/C), each with:
   - Binary signal: a YES/NO rule (e.g., "TAKE when h1_structure = BEAR")
   - Effect size: how many percentage points this signal adds/removes
   - Ramp-up pattern: what to watch in the 10 bars before entry
3. **Pre-Entry Checklist** -- the 5 signals as a decision tree

## Tier Definitions
| Tier | Effect Size | P-Value | Meaning |
|------|------------|---------|---------|
| S | >= 15pp | < 0.01 | Elite -- always check this indicator |
| A | >= 8pp | < 0.05 | Strong -- high-confidence filter |
| B | >= 4pp | < 0.05 | Moderate -- useful confirmation |
| C | >= 2pp | < 0.10 | Weak -- marginal edge, use as tiebreaker |
| Rejected | below thresholds | -- | Not actionable for this trade type |

## How to Interpret Effect Size
Effect size is the spread (in percentage points) between the best and worst
states/quintiles of an indicator. Example: if h1_structure BEAR = 68% WR
and BULL = 45% WR, effect size = 23pp.

## How to Interpret Ramp-Up Divergence
For continuous indicators, the ramp-up divergence shows how differently
winners and losers behave in the 10 minutes before entry. Positive means
winners have higher values. Larger magnitude = stronger pre-entry signal.

## Degradation Flags
Lines marked with [DEGRADED] indicate the indicator's edge has weakened
compared to the prior analysis run. Possible causes:
- Market regime change
- Sample size change
- Random variation

When you see degradation, DO NOT automatically remove the indicator.
Instead, flag it for the user to review.

## Workflow: Updating Scorecards
1. User runs: `python 04_indicators/runner.py --compare <prior_dir>`
2. Claude Code reads the new scorecards
3. If degradation flags exist, summarize them for the user
4. User decides whether to adjust trading rules
5. Claude Code NEVER changes scorecard files directly -- only the runner does

## The 5-Indicator Limit
Each scorecard includes exactly the top 5 (or fewer if insufficient data).
This is intentional -- a trader cannot realistically check more than 5
indicators in real-time. If an indicator is not in the top 5, it is either
redundant with a stronger indicator or not statistically significant for
that trade type.

## Trade Type Definitions
- **Long Continuation**: LONG direction + EPCH1 (Primary) or EPCH3 (Secondary)
- **Short Continuation**: SHORT direction + EPCH1 (Primary) or EPCH3 (Secondary)
- **Long Rejection**: LONG direction + EPCH2 (Primary) or EPCH4 (Secondary)
- **Short Rejection**: SHORT direction + EPCH2 (Primary) or EPCH4 (Secondary)

## Binary Signal Format
Signals use this pattern:
- `TAKE when <indicator> = <state>` -- favorable condition, look for this
- `SKIP when <indicator> = <state>` -- unfavorable condition, avoid this
- For continuous indicators, signals reference quintile ranges
- Ramp-up context describes what the indicator should be DOING (building,
  accelerating, compressing) not just its value at one point

## CRITICAL: Relative vs Absolute Benchmarks

### Indicators that are already relative (safe to compare across tickers):
- `candle_range_pct` -- ATR-normalized percentage ✅
- `sma_spread_pct` -- percentage spread between SMAs ✅
- `vol_roc` -- percentage rate of change ✅
- All categorical indicators (sma_config, m5_structure, etc.) ✅

### Indicators that are ABSOLUTE (ticker-dependent, NOT portable):
- `vol_delta_roll` -- raw volume delta in contracts/shares ❌
- `cvd_slope` -- raw CVD slope in absolute units ❌

**Rules for absolute indicators:**
1. The quintile ranges shown in scorecards (e.g., Q1 = -812,397 to -338,684)
   are fitted to the CURRENT dataset and ticker(s). They are NOT universal
   thresholds.
2. When evaluating a new trade, use the **quintile rank** (Q1/Q2/Q3/Q4/Q5)
   as the signal -- not the raw boundary values.
3. "Q1" means "bottom 20% of this indicator's own recent distribution."
   The actual numbers will differ across tickers due to liquidity differences.
4. To apply these signals to a different ticker, re-run the scorecard analysis
   on that ticker's data. Never carry raw vol_delta_roll or cvd_slope
   boundaries from one ticker to another.
5. When Claude Code references these indicators in trade evaluation, say
   "Volume Delta is in the lowest quintile of its recent range" -- NOT
   "Volume Delta is below -338,684."

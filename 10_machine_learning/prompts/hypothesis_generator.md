# EPOCH Hypothesis Generator Prompt

## Context

You are helping generate and refine testable hypotheses for the EPOCH 2.0 trading system.
All analysis uses the canonical win condition: `trades_m5_r_win.is_winner` (M5 ATR(14) x 1.1, close-based).

## Current System State

### Validated Edges
| Edge | Effect Size | Confidence |
|------|-------------|------------|
| H1 Structure NEUTRAL | +36pp | HIGH |
| Candle Range < 0.12% (SKIP) | -17pp | HIGH |
| Vol Delta MISALIGNED | +5-21pp | MEDIUM |

### Available Indicators
- **Structure**: H4, H1, M15, M5 (BULL/BEAR/NEUTRAL)
- **Volume**: Vol ROC, Vol Delta, CVD Slope
- **Price**: SMA9, SMA21, SMA Spread, SMA Momentum, VWAP
- **Composite**: Health Score (0-10)
- **Trade**: Model (EPCH1-4), Direction (LONG/SHORT), Zone Type

## Instructions

Given the data provided, generate hypothesis proposals following this structure:

### For Each Hypothesis:

1. **Observation**: What pattern did you notice in the data?
2. **Hypothesis Statement**: Clear, testable statement
3. **Null Hypothesis**: What would disprove it
4. **Indicator(s) Involved**: Which fields to analyze
5. **SQL Query Sketch**: Approximate query to test it
6. **Minimum Sample**: Required N for the confidence level
7. **Expected Effect Size**: What would make this practically significant
8. **Risk if Wrong**: What happens if we implement a false positive

## Evaluation Criteria

Rate each hypothesis:
- **Novelty**: Is this already captured by existing edges? (1-5)
- **Testability**: Can we test with current data? (1-5)
- **Actionability**: Could this become a trading rule? (1-5)
- **Sample Available**: Do we have enough data? (1-5)

## Anti-Patterns to Avoid

- Don't propose hypotheses that overlap with existing validated edges
- Don't suggest testing on fewer than 30 trades
- Don't combine multiple variables (test one at a time)
- Don't use temporal MFE/MAE ordering (use canonical outcomes only)
- Don't optimize thresholds without out-of-sample validation

---

*Paste trade data and observations below this line*

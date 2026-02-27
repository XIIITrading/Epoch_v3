# 05 - Composite Setup Analysis: Multi-Indicator Scoring

Tests how indicators work together to identify ideal entry setups.
Setup score is 0-7 based on favorable conditions present at entry.

## Setup Score Components (0-7)

- +1 if Candle Range >= 0.15%
- +1 if Vol ROC >= 30%
- +1 if SMA Spread >= 0.15%
- +1 if SMA Config aligned with direction (BULL/LONG or BEAR/SHORT)
- +1 if M5 Structure aligned with direction
- +1 if H1 Structure is NEUTRAL
- +1 if CVD Slope aligned with direction (>0.1 for LONG, <-0.1 for SHORT)

## Setup Score Distribution & Win Rate

| Score | Trades | Wins | Win Rate | Avg R |
|-------|--------|------|----------|-------|
| 0 | 183 | 113 | 61.7% | 1.20 |
| 1 | 448 | 214 | 47.8% | 0.70 |
| 2 | 631 | 302 | 47.9% | 0.78 |
| 3 | 720 | 348 | 48.3% | 0.82 |
| 4 | 465 | 216 | 46.5% | 0.73 |
| 5 | 201 | 85 | 42.3% | 0.39 |
| 6 | 78 | 43 | 55.1% | 0.55 |
| 7 | 9 | 7 | 77.8% | 1.78 |

## Indicator State Combinations

Win rate for specific indicator state combinations (min 20 trades).

### Top 10 Combinations (Highest Win Rate)

| SMA Config | H1 | M15 | Vol ROC | Candle | Trades | Win Rate | Avg R |
|------------|-----|-----|---------|--------|--------|----------|-------|
| BEAR | BEAR | BEAR | ELEVATED | NORMAL | 111 | 66.7% | 1.22 |
| BULL | BULL | BEAR | NORMAL | NORMAL | 163 | 63.8% | 1.18 |
| BEAR | BEAR | BEAR | ELEVATED | ABSORPTION | 38 | 63.2% | 0.84 |
| BULL | BULL | BEAR | ELEVATED | NORMAL | 64 | 60.9% | 1.66 |
| BULL | BULL | BULL | NORMAL | ABSORPTION | 52 | 57.7% | 1.23 |
| BEAR | BEAR | BULL | NORMAL | ABSORPTION | 82 | 57.3% | 1.07 |
| BEAR | BEAR | BEAR | NORMAL | ABSORPTION | 210 | 56.2% | 0.84 |
| BULL | BEAR | BEAR | ELEVATED | NORMAL | 43 | 55.8% | 1.44 |
| BULL | BULL | BULL | ELEVATED | NORMAL | 45 | 53.3% | 1.36 |
| BULL | BEAR | BULL | NORMAL | NORMAL | 46 | 52.2% | 1.17 |

### Bottom 10 Combinations (Lowest Win Rate)

| SMA Config | H1 | M15 | Vol ROC | Candle | Trades | Win Rate | Avg R |
|------------|-----|-----|---------|--------|--------|----------|-------|
| BULL | BEAR | BULL | ELEVATED | NORMAL | 25 | 44.0% | 0.68 |
| BULL | BULL | BEAR | NORMAL | LOW | 31 | 41.9% | 0.13 |
| BEAR | BULL | BULL | NORMAL | NORMAL | 126 | 40.5% | 0.30 |
| BEAR | BULL | BEAR | NORMAL | NORMAL | 112 | 39.3% | 0.54 |
| BEAR | BULL | BULL | NORMAL | ABSORPTION | 72 | 37.5% | 0.03 |
| BULL | BEAR | BEAR | ELEVATED | ABSORPTION | 23 | 34.8% | 0.65 |
| BEAR | BULL | BEAR | ELEVATED | NORMAL | 59 | 33.9% | 0.42 |
| BEAR | BULL | BEAR | NORMAL | LOW | 23 | 26.1% | -0.09 |
| BEAR | BEAR | BULL | ELEVATED | NORMAL | 40 | 20.0% | -0.03 |
| BEAR | BULL | BEAR | NORMAL | ABSORPTION | 62 | 16.1% | -0.39 |

## Key Observations for AI Analysis

When analyzing composite setup data, consider:
1. **Optimal score**: What setup score threshold gives the best risk-adjusted returns?
2. **Diminishing returns**: Does win rate plateau after a certain score?
3. **Required conditions**: Are there any must-have conditions regardless of score?
4. **Avoid combinations**: Which specific combos should be filtered out entirely?
5. **Actionable rules**: Propose 2-3 concrete pre-entry filter rules based on this data.
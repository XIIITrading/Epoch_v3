# EPOCH System Analysis - Summary Report

*Generated: 2026-02-07 07:35 | All trades in database*

---

## Stop Type Comparison

Compares 6 stop placement methods to show the trade-off between tighter stops (higher win rate, smaller gains) and wider stops (lower win rate, larger gains per winner).

*44,574 stop analysis records across 7,634 trades, ranked by Win Rate %*

| Stop Type | n | Avg Stop % | Stop Hit % | Win Rate % | Avg R (Win) | Avg R (All) | Net R (MFE) | Expectancy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| M5 ATR (Close) | 7,606 | 0.60% | 62.0% | 53.1% | +3.14R | +1.59R | +12072.58R | +1.466 |
| M15 ATR (Close) | 7,242 | 0.95% | 39.0% | 43.0% | +2.43R | +1.22R | +8807.74R | +0.986 |
| Zone + 5% Buffer | 7,634 | 0.71% | 60.2% | 42.7% | +2.64R | +1.12R | +8535.92R | +0.935 |
| Prior M5 H/L | 7,606 | 0.38% | 85.6% | 33.0% | +6.20R | +1.56R | +11844.24R | +1.505 |
| M5 Fractal H/L | 6,863 | 1.40% | 63.2% | 28.1% | +3.61R | +0.84R | +5793.95R | +0.683 |
| Prior M1 H/L | 7,623 | 0.19% | 91.5% | 26.9% | +9.15R | +1.79R | +13683.08R | +1.776 |

## Win Rate by Model

Shows how each entry model (EPCH01-04) performs under each stop type, revealing which models carry the edge and which are a drag.

### M5 ATR (Close)
*7,606 trades | Overall Win Rate: 53.1%*

| Model | Wins | Losses | Total | Win % | Avg R (Win) | Avg R (All) | Expectancy |
|---|---:|---:|---:|---:|---:|---:|---:|
| EPCH01 | 181 | 76 | 362 | 50.0% | +0.80R | +0.41R | +0.192 |
| EPCH02 | 1,981 | 761 | 3,742 | 52.9% | +0.82R | +0.44R | +0.233 |
| EPCH03 | 154 | 45 | 274 | 56.2% | +0.83R | +0.51R | +0.302 |
| EPCH04 | 1,725 | 658 | 3,228 | 53.4% | +0.84R | +0.46R | +0.245 |

### M15 ATR (Close)
*7,242 trades | Overall Win Rate: 43.0%*

| Model | Wins | Losses | Total | Win % | Avg R (Win) | Avg R (All) | Expectancy |
|---|---:|---:|---:|---:|---:|---:|---:|
| EPCH01 | 151 | 25 | 328 | 46.0% | +0.73R | +0.58R | +0.258 |
| EPCH02 | 1,502 | 193 | 3,587 | 41.9% | +0.71R | +0.61R | +0.242 |
| EPCH03 | 110 | 20 | 247 | 44.5% | +0.73R | +0.57R | +0.245 |
| EPCH04 | 1,352 | 190 | 3,080 | 43.9% | +0.71R | +0.60R | +0.251 |

### Zone + 5% Buffer
*7,634 trades | Overall Win Rate: 42.7%*

| Model | Wins | Losses | Total | Win % | Avg R (Win) | Avg R (All) | Expectancy |
|---|---:|---:|---:|---:|---:|---:|---:|
| EPCH01 | 157 | 106 | 367 | 42.8% | +0.80R | +0.27R | +0.052 |
| EPCH02 | 1,644 | 614 | 3,752 | 43.8% | +0.77R | +0.47R | +0.172 |
| EPCH03 | 128 | 68 | 279 | 45.9% | +0.80R | +0.34R | +0.123 |
| EPCH04 | 1,328 | 667 | 3,236 | 41.0% | +0.75R | +0.39R | +0.104 |

### Prior M5 H/L
*7,606 trades | Overall Win Rate: 33.0%*

| Model | Wins | Losses | Total | Win % | Avg R (Win) | Avg R (All) | Expectancy |
|---|---:|---:|---:|---:|---:|---:|---:|
| EPCH01 | 135 | 132 | 362 | 37.3% | +0.77R | +0.11R | -0.079 |
| EPCH02 | 1,182 | 2,127 | 3,742 | 31.6% | +0.86R | -0.21R | -0.297 |
| EPCH03 | 118 | 81 | 274 | 43.1% | +0.80R | +0.25R | +0.048 |
| EPCH04 | 1,076 | 1,789 | 3,228 | 33.3% | +0.87R | -0.17R | -0.264 |

### M5 Fractal H/L
*6,863 trades | Overall Win Rate: 28.1%*

| Model | Wins | Losses | Total | Win % | Avg R (Win) | Avg R (All) | Expectancy |
|---|---:|---:|---:|---:|---:|---:|---:|
| EPCH01 | 75 | 45 | 301 | 24.9% | +0.58R | +0.33R | -0.006 |
| EPCH02 | 950 | 1,105 | 3,390 | 28.0% | +0.68R | +0.12R | -0.136 |
| EPCH03 | 72 | 46 | 240 | 30.0% | +0.64R | +0.31R | +0.000 |
| EPCH04 | 831 | 1,075 | 2,932 | 28.3% | +0.68R | +0.06R | -0.174 |

### Prior M1 H/L
*7,623 trades | Overall Win Rate: 26.8%*

| Model | Wins | Losses | Total | Win % | Avg R (Win) | Avg R (All) | Expectancy |
|---|---:|---:|---:|---:|---:|---:|---:|
| EPCH01 | 127 | 198 | 365 | 34.8% | +0.86R | -0.15R | -0.244 |
| EPCH02 | 943 | 2,637 | 3,748 | 25.2% | +0.92R | -0.43R | -0.471 |
| EPCH03 | 100 | 141 | 278 | 36.0% | +0.88R | -0.08R | -0.192 |
| EPCH04 | 875 | 2,217 | 3,232 | 27.1% | +0.93R | -0.39R | -0.433 |

## Win Rate by Model-Direction

Splits each model by LONG and SHORT to expose directional bias — a model may look average overall but have a strong edge in one direction.

| Stop Type | EPCH01-L | EPCH01-S | EPCH02-L | EPCH02-S | EPCH03-L | EPCH03-S | EPCH04-L | EPCH04-S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| M5 ATR (Close) | 47.2% | 52.7% | 52.0% | 53.9% | 50.0% | 62.5% | 49.7% | 56.9% |
| M15 ATR (Close) | 42.2% | 49.7% | 39.6% | 44.0% | 36.3% | 52.8% | 36.6% | 50.7% |
| Zone + 5% Buffer | 40.7% | 44.9% | 40.4% | 47.1% | 39.7% | 52.2% | 37.2% | 44.6% |
| Prior M5 H/L | 30.3% | 44.0% | 29.9% | 33.3% | 39.9% | 46.3% | 33.6% | 33.1% |
| M5 Fractal H/L | 22.2% | 27.4% | 26.5% | 29.5% | 24.2% | 35.8% | 21.5% | 34.7% |
| Prior M1 H/L | 28.9% | 40.5% | 24.2% | 26.1% | 33.3% | 39.4% | 28.1% | 26.1% |

## MFE/MAE Sequence Analysis

Answers whether trades move favorably before adversely after entry — high P(MFE First) means the trade works in your direction before pulling back.

*7,634 trades analyzed*

### Overall

| Metric | Value |
|---|---:|
| P(MFE First) | 49.0% |
| MFE First Count | 3,738 |
| MAE First Count | 3,896 |
| Median Time to MFE | 58 min |
| Median Time to MAE | 56 min |
| MFE within 30 min | 37.1% |
| MFE within 60 min | 51.0% |

### By Model-Direction

*Ranked by P(MFE First) — higher = trade works in your favor sooner*

| Model | Direction | n | P(MFE First) | Med Time MFE | Med Time MAE | Time Delta | Confidence |
|---|---|---:|---:|---:|---:|---:|---|
| EPCH03 | LONG | 141 | 56.0% | 36 min | 64 min | +41 min | MEDIUM |
| EPCH01 | LONG | 182 | 55.5% | 68 min | 85 min | +37 min | MEDIUM |
| EPCH02 | SHORT | 1,918 | 50.5% | 57 min | 71 min | +4 min | HIGH |
| EPCH02 | LONG | 1,834 | 48.6% | 55 min | 58 min | -8 min | HIGH |
| EPCH04 | LONG | 1,555 | 48.2% | 50 min | 54 min | -1 min | HIGH |
| EPCH01 | SHORT | 185 | 47.6% | 82 min | 42 min | -19 min | MEDIUM |
| EPCH04 | SHORT | 1,681 | 47.5% | 68 min | 48 min | -24 min | HIGH |
| EPCH03 | SHORT | 138 | 44.9% | 79 min | 34 min | -26 min | MEDIUM |

# Indicator Momentum Analysis

## Metadata
- **Generated**: 2026-01-19 17:38:38
- **Stop Type**: m5_atr

## Overview
This analysis shows win rates when each indicator's **momentum** (first-half vs second-half of ramp period) is BUILDING, FADING, or STABLE.

- **BUILDING**: Second half average > First half average (indicator accelerating toward entry)
- **FADING**: Second half average < First half average (indicator decelerating toward entry)
- **STABLE**: Minimal change between halves

## Data by Model + Direction

### EPCH1_LONG (Baseline: 57.6%)

| Indicator | Momentum | N | Win Rate | Lift |
|-----------|----------|---|----------|------|
| candle_range_pct | BUILDING | 11* | 63.6% | +6.1% |
| candle_range_pct | FADING | 13* | 61.5% | +4.0% |
| candle_range_pct | STABLE | 9* | 44.4% | -13.1% |
| long_score | BUILDING | 18* | 50.0% | -7.6% |
| long_score | FADING | 10* | 70.0% | +12.4% |
| long_score | STABLE | 5* | 60.0% | +2.4% |
| short_score | BUILDING | 17* | 41.2% | -16.4% |
| short_score | FADING | 8* | 87.5% | +29.9% |
| short_score | STABLE | 8* | 62.5% | +4.9% |
| sma_momentum_ratio | BUILDING | 19* | 47.4% | -10.2% |
| sma_momentum_ratio | FADING | 14* | 71.4% | +13.8% |
| sma_spread | BUILDING | 17* | 47.1% | -10.5% |
| sma_spread | FADING | 15* | 73.3% | +15.8% |
| sma_spread | STABLE | 1* | 0.0% | -57.6% |
| vol_delta | BUILDING | 20* | 40.0% | -17.6% |
| vol_delta | FADING | 11* | 90.9% | +33.3% |
| vol_delta | STABLE | 2* | 50.0% | -7.6% |
| vol_roc | BUILDING | 18* | 50.0% | -7.6% |
| vol_roc | FADING | 15* | 66.7% | +9.1% |
| vol_roc | STABLE | 1* | 100.0% | +31.8% |

### EPCH1_SHORT (Baseline: 65.8%)

| Indicator | Momentum | N | Win Rate | Lift |
|-----------|----------|---|----------|------|
| candle_range_pct | BUILDING | 21* | 76.2% | +10.3% |
| candle_range_pct | FADING | 14* | 50.0% | -15.8% |
| candle_range_pct | STABLE | 6* | 66.7% | +0.8% |
| long_score | BUILDING | 23* | 78.3% | +12.4% |
| long_score | FADING | 11* | 54.6% | -11.3% |
| long_score | STABLE | 7* | 42.9% | -23.0% |
| short_score | BUILDING | 22* | 90.9% | +25.1% |
| short_score | FADING | 15* | 40.0% | -25.8% |
| short_score | STABLE | 4* | 25.0% | -40.8% |
| sma_momentum_ratio | BUILDING | 21* | 61.9% | -4.0% |
| sma_momentum_ratio | FADING | 17* | 64.7% | -1.2% |
| sma_momentum_ratio | STABLE | 2* | 100.0% | +34.2% |
| sma_spread | BUILDING | 19* | 73.7% | +7.8% |
| sma_spread | FADING | 19* | 57.9% | -8.0% |
| sma_spread | STABLE | 3* | 66.7% | +0.8% |
| vol_delta | BUILDING | 15* | 73.3% | +7.5% |
| vol_delta | FADING | 25* | 64.0% | -1.8% |
| vol_delta | STABLE | 1* | 0.0% | -65.8% |
| vol_roc | BUILDING | 23* | 65.2% | -0.6% |
| vol_roc | FADING | 14* | 71.4% | +5.6% |
| vol_roc | STABLE | 4* | 50.0% | -15.8% |

### EPCH2_LONG (Baseline: 57.4%)

| Indicator | Momentum | N | Win Rate | Lift |
|-----------|----------|---|----------|------|
| candle_range_pct | BUILDING | 139 | 67.6% | +10.3% |
| candle_range_pct | FADING | 140 | 57.9% | +0.5% |
| candle_range_pct | STABLE | 108 | 43.5% | -13.8% |
| long_score | BUILDING | 169 | 55.0% | -2.3% |
| long_score | FADING | 150 | 59.3% | +2.0% |
| long_score | STABLE | 68 | 58.8% | +1.5% |
| short_score | BUILDING | 170 | 60.0% | +2.6% |
| short_score | FADING | 150 | 58.0% | +0.6% |
| short_score | STABLE | 67 | 49.2% | -8.1% |
| sma_momentum_ratio | BUILDING | 167 | 56.9% | -0.5% |
| sma_momentum_ratio | FADING | 209 | 57.9% | +0.5% |
| sma_momentum_ratio | STABLE | 11* | 54.6% | -2.8% |
| sma_spread | BUILDING | 191 | 57.1% | -0.3% |
| sma_spread | FADING | 170 | 57.1% | -0.3% |
| sma_spread | STABLE | 26* | 61.5% | +4.2% |
| vol_delta | BUILDING | 173 | 54.9% | -2.4% |
| vol_delta | FADING | 195 | 61.0% | +3.7% |
| vol_delta | STABLE | 19* | 42.1% | -15.3% |
| vol_roc | BUILDING | 186 | 58.1% | +0.7% |
| vol_roc | FADING | 192 | 57.3% | -0.1% |
| vol_roc | STABLE | 9* | 44.4% | -12.9% |

### EPCH2_SHORT (Baseline: 64.7%)

| Indicator | Momentum | N | Win Rate | Lift |
|-----------|----------|---|----------|------|
| candle_range_pct | BUILDING | 115 | 64.4% | -0.4% |
| candle_range_pct | FADING | 173 | 68.8% | +4.1% |
| candle_range_pct | STABLE | 106 | 58.5% | -6.2% |
| long_score | BUILDING | 158 | 62.7% | -2.1% |
| long_score | FADING | 163 | 59.5% | -5.2% |
| long_score | STABLE | 73 | 80.8% | +16.1% |
| short_score | BUILDING | 163 | 68.7% | +4.0% |
| short_score | FADING | 175 | 61.7% | -3.0% |
| short_score | STABLE | 56 | 62.5% | -2.2% |
| sma_momentum_ratio | BUILDING | 193 | 64.2% | -0.5% |
| sma_momentum_ratio | FADING | 181 | 64.6% | -0.1% |
| sma_momentum_ratio | STABLE | 18* | 66.7% | +2.0% |
| sma_spread | BUILDING | 176 | 65.9% | +1.2% |
| sma_spread | FADING | 205 | 62.4% | -2.3% |
| sma_spread | STABLE | 12* | 83.3% | +18.6% |
| vol_delta | BUILDING | 216 | 69.0% | +4.3% |
| vol_delta | FADING | 167 | 58.7% | -6.0% |
| vol_delta | STABLE | 11* | 72.7% | +8.0% |
| vol_roc | BUILDING | 185 | 58.4% | -6.3% |
| vol_roc | FADING | 191 | 70.2% | +5.4% |
| vol_roc | STABLE | 17* | 70.6% | +5.9% |

### EPCH3_LONG (Baseline: 71.0%)

| Indicator | Momentum | N | Win Rate | Lift |
|-----------|----------|---|----------|------|
| candle_range_pct | BUILDING | 11* | 54.6% | -16.4% |
| candle_range_pct | FADING | 12* | 75.0% | +4.0% |
| candle_range_pct | STABLE | 8* | 87.5% | +16.5% |
| long_score | BUILDING | 17* | 64.7% | -6.3% |
| long_score | FADING | 9* | 66.7% | -4.3% |
| long_score | STABLE | 5* | 100.0% | +29.0% |
| short_score | BUILDING | 13* | 53.8% | -17.1% |
| short_score | FADING | 10* | 80.0% | +9.0% |
| short_score | STABLE | 8* | 87.5% | +16.5% |
| sma_momentum_ratio | BUILDING | 16* | 68.8% | -2.2% |
| sma_momentum_ratio | FADING | 14* | 71.4% | +0.5% |
| sma_momentum_ratio | STABLE | 1* | 100.0% | +29.0% |
| sma_spread | BUILDING | 17* | 70.6% | -0.4% |
| sma_spread | FADING | 13* | 69.2% | -1.7% |
| sma_spread | STABLE | 1* | 100.0% | +29.0% |
| vol_delta | BUILDING | 18* | 77.8% | +6.8% |
| vol_delta | FADING | 11* | 54.6% | -16.4% |
| vol_delta | STABLE | 2* | 100.0% | +29.0% |
| vol_roc | BUILDING | 10* | 50.0% | -21.0% |
| vol_roc | FADING | 21* | 81.0% | +10.0% |

### EPCH3_SHORT (Baseline: 81.2%)

| Indicator | Momentum | N | Win Rate | Lift |
|-----------|----------|---|----------|------|
| candle_range_pct | BUILDING | 13* | 76.9% | -4.3% |
| candle_range_pct | FADING | 13* | 76.9% | -4.3% |
| candle_range_pct | STABLE | 6* | 100.0% | +18.8% |
| long_score | BUILDING | 18* | 88.9% | +7.6% |
| long_score | FADING | 11* | 72.7% | -8.5% |
| long_score | STABLE | 3* | 66.7% | -14.6% |
| short_score | BUILDING | 12* | 83.3% | +2.1% |
| short_score | FADING | 13* | 69.2% | -12.0% |
| short_score | STABLE | 7* | 100.0% | +18.8% |
| sma_momentum_ratio | BUILDING | 19* | 79.0% | -2.3% |
| sma_momentum_ratio | FADING | 12* | 83.3% | +2.1% |
| sma_momentum_ratio | STABLE | 1* | 100.0% | +18.8% |
| sma_spread | BUILDING | 11* | 81.8% | +0.6% |
| sma_spread | FADING | 17* | 76.5% | -4.8% |
| sma_spread | STABLE | 4* | 100.0% | +18.8% |
| vol_delta | BUILDING | 14* | 78.6% | -2.7% |
| vol_delta | FADING | 17* | 82.4% | +1.1% |
| vol_delta | STABLE | 1* | 100.0% | +18.8% |
| vol_roc | BUILDING | 14* | 92.9% | +11.6% |
| vol_roc | FADING | 17* | 70.6% | -10.7% |
| vol_roc | STABLE | 1* | 100.0% | +18.8% |

### EPCH4_LONG (Baseline: 73.6%)

| Indicator | Momentum | N | Win Rate | Lift |
|-----------|----------|---|----------|------|
| candle_range_pct | BUILDING | 127 | 77.2% | +3.5% |
| candle_range_pct | FADING | 122 | 77.9% | +4.2% |
| candle_range_pct | STABLE | 119 | 65.6% | -8.1% |
| long_score | BUILDING | 175 | 72.6% | -1.1% |
| long_score | FADING | 136 | 69.8% | -3.8% |
| long_score | STABLE | 57 | 86.0% | +12.3% |
| short_score | BUILDING | 150 | 76.0% | +2.4% |
| short_score | FADING | 153 | 68.6% | -5.0% |
| short_score | STABLE | 65 | 80.0% | +6.4% |
| sma_momentum_ratio | BUILDING | 163 | 76.7% | +3.0% |
| sma_momentum_ratio | FADING | 195 | 70.3% | -3.4% |
| sma_momentum_ratio | STABLE | 10* | 90.0% | +16.4% |
| sma_spread | BUILDING | 148 | 79.7% | +6.1% |
| sma_spread | FADING | 196 | 71.9% | -1.7% |
| sma_spread | STABLE | 24* | 50.0% | -23.6% |
| vol_delta | BUILDING | 177 | 76.3% | +2.6% |
| vol_delta | FADING | 183 | 70.5% | -3.2% |
| vol_delta | STABLE | 8* | 87.5% | +13.9% |
| vol_roc | BUILDING | 188 | 70.7% | -2.9% |
| vol_roc | FADING | 163 | 77.3% | +3.7% |
| vol_roc | STABLE | 17* | 70.6% | -3.0% |

### EPCH4_SHORT (Baseline: 70.1%)

| Indicator | Momentum | N | Win Rate | Lift |
|-----------|----------|---|----------|------|
| candle_range_pct | BUILDING | 113 | 69.0% | -1.1% |
| candle_range_pct | FADING | 117 | 68.4% | -1.8% |
| candle_range_pct | STABLE | 78 | 74.4% | +4.2% |
| long_score | BUILDING | 126 | 73.0% | +2.9% |
| long_score | FADING | 126 | 67.5% | -2.7% |
| long_score | STABLE | 56 | 69.6% | -0.5% |
| short_score | BUILDING | 140 | 65.0% | -5.1% |
| short_score | FADING | 117 | 68.4% | -1.8% |
| short_score | STABLE | 51 | 88.2% | +18.1% |
| sma_momentum_ratio | BUILDING | 141 | 68.1% | -2.0% |
| sma_momentum_ratio | FADING | 156 | 71.8% | +1.7% |
| sma_momentum_ratio | STABLE | 11* | 72.7% | +2.6% |
| sma_spread | BUILDING | 143 | 70.6% | +0.5% |
| sma_spread | FADING | 144 | 66.0% | -4.2% |
| sma_spread | STABLE | 21* | 95.2% | +25.1% |
| vol_delta | BUILDING | 147 | 68.7% | -1.4% |
| vol_delta | FADING | 151 | 72.2% | +2.1% |
| vol_delta | STABLE | 10* | 60.0% | -10.1% |
| vol_roc | BUILDING | 138 | 70.3% | +0.2% |
| vol_roc | FADING | 162 | 70.4% | +0.2% |
| vol_roc | STABLE | 8* | 62.5% | -7.6% |


## Claude Analysis Instructions
Analyze the momentum data to identify:
1. Which momentum patterns are most predictive of wins?
2. Does BUILDING momentum in long_score predict Long wins?
3. Does FADING vol_delta predict Rejection trade wins (absorption pattern)?
4. Differences between Continuation and Rejection models

*Note: Rows marked with * have fewer than 30 trades.*

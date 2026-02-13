# Indicator Trend Analysis

## Metadata
- **Generated**: 2026-01-19 17:38:38
- **Stop Type**: m5_atr

## Overview
This analysis shows win rates when each indicator's **trend** (linear regression over ramp period) is RISING, FALLING, or FLAT.

A positive **Lift** means the win rate is higher than the baseline for that grouping.

## Key Indicators
- **vol_delta**: Volume buy/sell differential trend
- **vol_roc**: Volume rate of change trend
- **long_score**: Composite long score trend
- **short_score**: Composite short score trend
- **sma_spread**: SMA spread trend
- **candle_range_pct**: Candle range trend

## Data by Model + Direction

### EPCH1_LONG (Baseline: 57.6%)

| Indicator | Trend | N | Win Rate | Lift |
|-----------|-------|---|----------|------|
| candle_range_pct | FALLING | 14* | 50.0% | -7.6% |
| candle_range_pct | FLAT | 6* | 66.7% | +9.1% |
| candle_range_pct | RISING | 13* | 61.5% | +4.0% |
| long_score | FALLING | 11* | 72.7% | +15.2% |
| long_score | FLAT | 2* | 0.0% | -57.6% |
| long_score | RISING | 20* | 55.0% | -2.6% |
| short_score | FALLING | 11* | 72.7% | +15.2% |
| short_score | FLAT | 2* | 0.0% | -57.6% |
| short_score | RISING | 20* | 55.0% | -2.6% |
| sma_momentum_ratio | FALLING | 14* | 71.4% | +13.8% |
| sma_momentum_ratio | FLAT | 1* | 100.0% | +42.4% |
| sma_momentum_ratio | RISING | 18* | 44.4% | -13.1% |
| sma_spread | FALLING | 15* | 66.7% | +9.1% |
| sma_spread | RISING | 18* | 50.0% | -7.6% |
| vol_delta | FALLING | 8* | 87.5% | +29.9% |
| vol_delta | FLAT | 2* | 50.0% | -7.6% |
| vol_delta | RISING | 23* | 47.8% | -9.8% |
| vol_roc | FALLING | 13* | 69.2% | +11.7% |
| vol_roc | FLAT | 5* | 60.0% | +2.4% |
| vol_roc | RISING | 15* | 46.7% | -10.9% |

### EPCH1_SHORT (Baseline: 65.8%)

| Indicator | Trend | N | Win Rate | Lift |
|-----------|-------|---|----------|------|
| candle_range_pct | FALLING | 16* | 43.8% | -22.1% |
| candle_range_pct | FLAT | 3* | 66.7% | +0.8% |
| candle_range_pct | RISING | 22* | 81.8% | +16.0% |
| long_score | FALLING | 15* | 53.3% | -12.5% |
| long_score | FLAT | 2* | 0.0% | -65.8% |
| long_score | RISING | 24* | 79.2% | +13.3% |
| short_score | FALLING | 16* | 37.5% | -28.4% |
| short_score | FLAT | 1* | 0.0% | -65.8% |
| short_score | RISING | 24* | 87.5% | +21.6% |
| sma_momentum_ratio | FALLING | 17* | 64.7% | -1.2% |
| sma_momentum_ratio | FLAT | 2* | 100.0% | +34.2% |
| sma_momentum_ratio | RISING | 21* | 61.9% | -4.0% |
| sma_spread | FALLING | 21* | 61.9% | -4.0% |
| sma_spread | RISING | 20* | 70.0% | +4.2% |
| vol_delta | FALLING | 24* | 62.5% | -3.4% |
| vol_delta | FLAT | 2* | 50.0% | -15.8% |
| vol_delta | RISING | 15* | 73.3% | +7.5% |
| vol_roc | FALLING | 17* | 64.7% | -1.2% |
| vol_roc | FLAT | 2* | 100.0% | +34.2% |
| vol_roc | RISING | 22* | 63.6% | -2.2% |

### EPCH2_LONG (Baseline: 57.4%)

| Indicator | Trend | N | Win Rate | Lift |
|-----------|-------|---|----------|------|
| candle_range_pct | FALLING | 168 | 56.0% | -1.4% |
| candle_range_pct | FLAT | 48 | 54.2% | -3.2% |
| candle_range_pct | RISING | 171 | 59.6% | +2.3% |
| long_score | FALLING | 178 | 59.0% | +1.6% |
| long_score | FLAT | 31 | 48.4% | -9.0% |
| long_score | RISING | 178 | 57.3% | -0.1% |
| short_score | FALLING | 172 | 57.6% | +0.2% |
| short_score | FLAT | 24* | 45.8% | -11.5% |
| short_score | RISING | 191 | 58.6% | +1.3% |
| sma_momentum_ratio | FALLING | 202 | 56.4% | -0.9% |
| sma_momentum_ratio | FLAT | 16* | 56.2% | -1.1% |
| sma_momentum_ratio | RISING | 169 | 58.6% | +1.2% |
| sma_spread | FALLING | 180 | 56.7% | -0.7% |
| sma_spread | FLAT | 6* | 66.7% | +9.3% |
| sma_spread | RISING | 201 | 57.7% | +0.4% |
| vol_delta | FALLING | 192 | 58.8% | +1.5% |
| vol_delta | FLAT | 21* | 33.3% | -24.0% |
| vol_delta | RISING | 174 | 58.6% | +1.3% |
| vol_roc | FALLING | 180 | 57.8% | +0.4% |
| vol_roc | FLAT | 31 | 51.6% | -5.8% |
| vol_roc | RISING | 176 | 58.0% | +0.6% |

### EPCH2_SHORT (Baseline: 64.7%)

| Indicator | Trend | N | Win Rate | Lift |
|-----------|-------|---|----------|------|
| candle_range_pct | FALLING | 223 | 67.7% | +3.0% |
| candle_range_pct | FLAT | 37 | 51.4% | -13.4% |
| candle_range_pct | RISING | 134 | 63.4% | -1.3% |
| long_score | FALLING | 196 | 65.8% | +1.1% |
| long_score | FLAT | 27* | 55.6% | -9.2% |
| long_score | RISING | 171 | 64.9% | +0.2% |
| short_score | FALLING | 197 | 58.9% | -5.8% |
| short_score | FLAT | 14* | 78.6% | +13.8% |
| short_score | RISING | 183 | 70.0% | +5.2% |
| sma_momentum_ratio | FALLING | 173 | 64.2% | -0.6% |
| sma_momentum_ratio | FLAT | 30 | 73.3% | +8.6% |
| sma_momentum_ratio | RISING | 189 | 63.5% | -1.2% |
| sma_spread | FALLING | 207 | 63.3% | -1.4% |
| sma_spread | FLAT | 7* | 85.7% | +21.0% |
| sma_spread | RISING | 179 | 65.4% | +0.6% |
| vol_delta | FALLING | 180 | 57.8% | -6.9% |
| vol_delta | FLAT | 16* | 62.5% | -2.2% |
| vol_delta | RISING | 198 | 71.2% | +6.5% |
| vol_roc | FALLING | 182 | 72.5% | +7.8% |
| vol_roc | FLAT | 31 | 61.3% | -3.4% |
| vol_roc | RISING | 180 | 57.2% | -7.5% |

### EPCH3_LONG (Baseline: 71.0%)

| Indicator | Trend | N | Win Rate | Lift |
|-----------|-------|---|----------|------|
| candle_range_pct | FALLING | 14* | 71.4% | +0.5% |
| candle_range_pct | FLAT | 3* | 100.0% | +29.0% |
| candle_range_pct | RISING | 14* | 64.3% | -6.7% |
| long_score | FALLING | 11* | 72.7% | +1.8% |
| long_score | FLAT | 1* | 100.0% | +29.0% |
| long_score | RISING | 19* | 68.4% | -2.6% |
| short_score | FALLING | 14* | 78.6% | +7.6% |
| short_score | FLAT | 1* | 100.0% | +29.0% |
| short_score | RISING | 16* | 62.5% | -8.5% |
| sma_momentum_ratio | FALLING | 13* | 69.2% | -1.7% |
| sma_momentum_ratio | FLAT | 2* | 100.0% | +29.0% |
| sma_momentum_ratio | RISING | 16* | 68.8% | -2.2% |
| sma_spread | FALLING | 14* | 71.4% | +0.5% |
| sma_spread | RISING | 17* | 70.6% | -0.4% |
| vol_delta | FALLING | 9* | 44.4% | -26.5% |
| vol_delta | FLAT | 6* | 83.3% | +12.4% |
| vol_delta | RISING | 16* | 81.2% | +10.3% |
| vol_roc | FALLING | 21* | 81.0% | +10.0% |
| vol_roc | FLAT | 1* | 100.0% | +29.0% |
| vol_roc | RISING | 9* | 44.4% | -26.5% |

### EPCH3_SHORT (Baseline: 81.2%)

| Indicator | Trend | N | Win Rate | Lift |
|-----------|-------|---|----------|------|
| candle_range_pct | FALLING | 13* | 76.9% | -4.3% |
| candle_range_pct | FLAT | 2* | 100.0% | +18.8% |
| candle_range_pct | RISING | 17* | 82.4% | +1.1% |
| long_score | FALLING | 14* | 71.4% | -9.8% |
| long_score | FLAT | 1* | 100.0% | +18.8% |
| long_score | RISING | 17* | 88.2% | +7.0% |
| short_score | FALLING | 16* | 68.8% | -12.5% |
| short_score | FLAT | 3* | 66.7% | -14.6% |
| short_score | RISING | 13* | 100.0% | +18.8% |
| sma_momentum_ratio | FALLING | 11* | 81.8% | +0.6% |
| sma_momentum_ratio | FLAT | 3* | 100.0% | +18.8% |
| sma_momentum_ratio | RISING | 18* | 77.8% | -3.5% |
| sma_spread | FALLING | 20* | 80.0% | -1.2% |
| sma_spread | FLAT | 1* | 100.0% | +18.8% |
| sma_spread | RISING | 11* | 81.8% | +0.6% |
| vol_delta | FALLING | 19* | 84.2% | +3.0% |
| vol_delta | FLAT | 1* | 100.0% | +18.8% |
| vol_delta | RISING | 12* | 75.0% | -6.2% |
| vol_roc | FALLING | 17* | 70.6% | -10.7% |
| vol_roc | RISING | 15* | 93.3% | +12.1% |

### EPCH4_LONG (Baseline: 73.6%)

| Indicator | Trend | N | Win Rate | Lift |
|-----------|-------|---|----------|------|
| candle_range_pct | FALLING | 174 | 72.4% | -1.2% |
| candle_range_pct | FLAT | 39 | 84.6% | +11.0% |
| candle_range_pct | RISING | 155 | 72.3% | -1.4% |
| long_score | FALLING | 167 | 74.2% | +0.6% |
| long_score | FLAT | 18* | 72.2% | -1.4% |
| long_score | RISING | 183 | 73.2% | -0.4% |
| short_score | FALLING | 184 | 72.3% | -1.4% |
| short_score | FLAT | 15* | 66.7% | -7.0% |
| short_score | RISING | 169 | 75.7% | +2.1% |
| sma_momentum_ratio | FALLING | 183 | 70.0% | -3.7% |
| sma_momentum_ratio | FLAT | 25* | 80.0% | +6.4% |
| sma_momentum_ratio | RISING | 160 | 76.9% | +3.2% |
| sma_spread | FALLING | 203 | 70.9% | -2.7% |
| sma_spread | FLAT | 7* | 85.7% | +12.1% |
| sma_spread | RISING | 158 | 76.6% | +2.9% |
| vol_delta | FALLING | 171 | 73.1% | -0.5% |
| vol_delta | FLAT | 21* | 66.7% | -7.0% |
| vol_delta | RISING | 176 | 75.0% | +1.4% |
| vol_roc | FALLING | 157 | 77.7% | +4.1% |
| vol_roc | FLAT | 21* | 66.7% | -7.0% |
| vol_roc | RISING | 190 | 71.0% | -2.6% |

### EPCH4_SHORT (Baseline: 70.1%)

| Indicator | Trend | N | Win Rate | Lift |
|-----------|-------|---|----------|------|
| candle_range_pct | FALLING | 152 | 71.7% | +1.6% |
| candle_range_pct | FLAT | 28* | 60.7% | -9.4% |
| candle_range_pct | RISING | 128 | 70.3% | +0.2% |
| long_score | FALLING | 149 | 68.5% | -1.7% |
| long_score | FLAT | 18* | 66.7% | -3.5% |
| long_score | RISING | 141 | 72.3% | +2.2% |
| short_score | FALLING | 146 | 72.6% | +2.5% |
| short_score | FLAT | 19* | 68.4% | -1.7% |
| short_score | RISING | 143 | 67.8% | -2.3% |
| sma_momentum_ratio | FALLING | 143 | 72.7% | +2.6% |
| sma_momentum_ratio | FLAT | 31 | 67.7% | -2.4% |
| sma_momentum_ratio | RISING | 134 | 67.9% | -2.2% |
| sma_spread | FALLING | 154 | 67.5% | -2.6% |
| sma_spread | FLAT | 2* | 100.0% | +29.9% |
| sma_spread | RISING | 152 | 72.4% | +2.2% |
| vol_delta | FALLING | 145 | 75.2% | +5.0% |
| vol_delta | FLAT | 15* | 66.7% | -3.5% |
| vol_delta | RISING | 148 | 65.5% | -4.6% |
| vol_roc | FALLING | 149 | 69.1% | -1.0% |
| vol_roc | FLAT | 20* | 65.0% | -5.1% |
| vol_roc | RISING | 139 | 71.9% | +1.8% |


## Claude Analysis Instructions
Analyze the trend data and identify:
1. Which indicators have the most predictive trend patterns per model+direction?
2. Are there "universal" patterns (e.g., RISING vol_delta always good)?
3. Specific trend combinations that significantly outperform baseline
4. Patterns that differ between Continuation and Rejection models

*Note: Rows marked with * have fewer than 30 trades and may not be statistically significant.*

# Entry Bar Snapshot Analysis

## Metadata
- **Generated**: 2026-01-19 17:38:38
- **Stop Type**: m5_atr

## Overview
This analysis shows win rates based on indicator values **at the entry bar** (bar 0), bucketed into ranges.

This answers: "Given the indicator value at the moment of entry, what is the win probability?"

## Data by Model + Direction

### EPCH1_LONG (Baseline: 57.6%)

| Indicator | Bucket | N | Win Rate | Lift |
|-----------|--------|---|----------|------|
| candle_range_pct | HIGH (0.20+) | 18* | 61.1% | +3.5% |
| candle_range_pct | LOW (<0.10) | 3* | 100.0% | +42.4% |
| candle_range_pct | MID (0.10-0.20) | 12* | 41.7% | -15.9% |
| long_score | HIGH (5-7) | 11* | 54.6% | -3.0% |
| long_score | LOW (0-2) | 11* | 72.7% | +15.2% |
| long_score | MID (3-4) | 11* | 45.4% | -12.1% |
| short_score | HIGH (5-7) | 14* | 42.9% | -14.7% |
| short_score | LOW (0-2) | 6* | 66.7% | +9.1% |
| short_score | MID (3-4) | 13* | 69.2% | +11.7% |
| vol_delta | STRONG NEG | 1* | 100.0% | +42.4% |
| vol_delta | STRONG POS | 21* | 57.1% | -0.4% |
| vol_delta | WEAK NEG | 2* | 50.0% | -7.6% |
| vol_delta | WEAK POS | 9* | 55.6% | -2.0% |
| vol_roc | HIGH (30+) | 21* | 52.4% | -5.2% |
| vol_roc | LOW (0-30) | 6* | 66.7% | +9.1% |
| vol_roc | NEGATIVE | 6* | 66.7% | +9.1% |

### EPCH1_SHORT (Baseline: 65.8%)

| Indicator | Bucket | N | Win Rate | Lift |
|-----------|--------|---|----------|------|
| candle_range_pct | HIGH (0.20+) | 29* | 75.9% | +10.0% |
| candle_range_pct | LOW (<0.10) | 3* | 66.7% | +0.8% |
| candle_range_pct | MID (0.10-0.20) | 9* | 33.3% | -32.5% |
| long_score | HIGH (5-7) | 4* | 75.0% | +9.2% |
| long_score | LOW (0-2) | 12* | 41.7% | -24.2% |
| long_score | MID (3-4) | 25* | 76.0% | +10.2% |
| short_score | HIGH (5-7) | 3* | 100.0% | +34.2% |
| short_score | LOW (0-2) | 14* | 35.7% | -30.1% |
| short_score | MID (3-4) | 24* | 79.2% | +13.3% |
| vol_delta | STRONG NEG | 19* | 68.4% | +2.6% |
| vol_delta | STRONG POS | 3* | 100.0% | +34.2% |
| vol_delta | WEAK NEG | 12* | 50.0% | -15.8% |
| vol_delta | WEAK POS | 7* | 71.4% | +5.6% |
| vol_roc | HIGH (30+) | 21* | 71.4% | +5.6% |
| vol_roc | LOW (0-30) | 5* | 40.0% | -25.8% |
| vol_roc | NEGATIVE | 15* | 66.7% | +0.8% |

### EPCH2_LONG (Baseline: 57.4%)

| Indicator | Bucket | N | Win Rate | Lift |
|-----------|--------|---|----------|------|
| candle_range_pct | HIGH (0.20+) | 137 | 69.3% | +12.0% |
| candle_range_pct | LOW (<0.10) | 150 | 48.7% | -8.7% |
| candle_range_pct | MID (0.10-0.20) | 100 | 54.0% | -3.4% |
| long_score | HIGH (5-7) | 14* | 71.4% | +14.1% |
| long_score | LOW (0-2) | 234 | 51.7% | -5.6% |
| long_score | MID (3-4) | 139 | 65.5% | +8.1% |
| short_score | HIGH (5-7) | 17* | 70.6% | +13.2% |
| short_score | LOW (0-2) | 222 | 53.2% | -4.2% |
| short_score | MID (3-4) | 148 | 62.2% | +4.8% |
| vol_delta | STRONG NEG | 66 | 59.1% | +1.7% |
| vol_delta | STRONG POS | 77 | 53.2% | -4.1% |
| vol_delta | WEAK NEG | 107 | 57.9% | +0.6% |
| vol_delta | WEAK POS | 137 | 58.4% | +1.0% |
| vol_roc | HIGH (30+) | 90 | 62.2% | +4.9% |
| vol_roc | LOW (0-30) | 68 | 66.2% | +8.8% |
| vol_roc | NEGATIVE | 229 | 52.8% | -4.5% |

### EPCH2_SHORT (Baseline: 64.7%)

| Indicator | Bucket | N | Win Rate | Lift |
|-----------|--------|---|----------|------|
| candle_range_pct | HIGH (0.20+) | 160 | 83.1% | +18.4% |
| candle_range_pct | LOW (<0.10) | 97 | 46.4% | -18.3% |
| candle_range_pct | MID (0.10-0.20) | 137 | 56.2% | -8.5% |
| long_score | HIGH (5-7) | 12* | 83.3% | +18.6% |
| long_score | LOW (0-2) | 222 | 53.6% | -11.1% |
| long_score | MID (3-4) | 160 | 78.8% | +14.0% |
| short_score | HIGH (5-7) | 18* | 61.1% | -3.6% |
| short_score | LOW (0-2) | 207 | 52.2% | -12.6% |
| short_score | MID (3-4) | 169 | 80.5% | +15.8% |
| vol_delta | STRONG NEG | 57 | 66.7% | +2.0% |
| vol_delta | STRONG POS | 61 | 65.6% | +0.8% |
| vol_delta | WEAK NEG | 151 | 60.3% | -4.5% |
| vol_delta | WEAK POS | 125 | 68.8% | +4.1% |
| vol_roc | HIGH (30+) | 89 | 62.9% | -1.8% |
| vol_roc | LOW (0-30) | 77 | 61.0% | -3.7% |
| vol_roc | NEGATIVE | 227 | 66.5% | +1.8% |

### EPCH3_LONG (Baseline: 71.0%)

| Indicator | Bucket | N | Win Rate | Lift |
|-----------|--------|---|----------|------|
| candle_range_pct | HIGH (0.20+) | 18* | 72.2% | +1.2% |
| candle_range_pct | LOW (<0.10) | 3* | 100.0% | +29.0% |
| candle_range_pct | MID (0.10-0.20) | 10* | 60.0% | -11.0% |
| long_score | HIGH (5-7) | 7* | 85.7% | +14.8% |
| long_score | LOW (0-2) | 10* | 80.0% | +9.0% |
| long_score | MID (3-4) | 14* | 57.1% | -13.8% |
| short_score | HIGH (5-7) | 10* | 50.0% | -21.0% |
| short_score | LOW (0-2) | 7* | 85.7% | +14.8% |
| short_score | MID (3-4) | 14* | 78.6% | +7.6% |
| vol_delta | STRONG NEG | 3* | 66.7% | -4.3% |
| vol_delta | STRONG POS | 15* | 66.7% | -4.3% |
| vol_delta | WEAK NEG | 3* | 100.0% | +29.0% |
| vol_delta | WEAK POS | 10* | 70.0% | -1.0% |
| vol_roc | HIGH (30+) | 16* | 56.2% | -14.7% |
| vol_roc | LOW (0-30) | 4* | 100.0% | +29.0% |
| vol_roc | NEGATIVE | 11* | 81.8% | +10.8% |

### EPCH3_SHORT (Baseline: 81.2%)

| Indicator | Bucket | N | Win Rate | Lift |
|-----------|--------|---|----------|------|
| candle_range_pct | HIGH (0.20+) | 18* | 88.9% | +7.6% |
| candle_range_pct | LOW (<0.10) | 8* | 75.0% | -6.2% |
| candle_range_pct | MID (0.10-0.20) | 6* | 66.7% | -14.6% |
| long_score | HIGH (5-7) | 4* | 100.0% | +18.8% |
| long_score | LOW (0-2) | 16* | 68.8% | -12.5% |
| long_score | MID (3-4) | 12* | 91.7% | +10.4% |
| short_score | LOW (0-2) | 20* | 75.0% | -6.2% |
| short_score | MID (3-4) | 12* | 91.7% | +10.4% |
| vol_delta | STRONG NEG | 17* | 82.4% | +1.1% |
| vol_delta | STRONG POS | 1* | 100.0% | +18.8% |
| vol_delta | WEAK NEG | 12* | 75.0% | -6.2% |
| vol_delta | WEAK POS | 2* | 100.0% | +18.8% |
| vol_roc | HIGH (30+) | 14* | 92.9% | +11.6% |
| vol_roc | LOW (0-30) | 9* | 66.7% | -14.6% |
| vol_roc | NEGATIVE | 9* | 77.8% | -3.5% |

### EPCH4_LONG (Baseline: 73.6%)

| Indicator | Bucket | N | Win Rate | Lift |
|-----------|--------|---|----------|------|
| candle_range_pct | HIGH (0.20+) | 178 | 80.9% | +7.3% |
| candle_range_pct | LOW (<0.10) | 84 | 70.2% | -3.4% |
| candle_range_pct | MID (0.10-0.20) | 106 | 64.2% | -9.5% |
| long_score | HIGH (5-7) | 22* | 90.9% | +17.3% |
| long_score | LOW (0-2) | 168 | 64.9% | -8.8% |
| long_score | MID (3-4) | 178 | 79.8% | +6.1% |
| short_score | HIGH (5-7) | 29* | 75.9% | +2.2% |
| short_score | LOW (0-2) | 170 | 67.1% | -6.6% |
| short_score | MID (3-4) | 169 | 79.9% | +6.2% |
| vol_delta | STRONG NEG | 61 | 82.0% | +8.3% |
| vol_delta | STRONG POS | 69 | 78.3% | +4.6% |
| vol_delta | WEAK NEG | 103 | 65.0% | -8.6% |
| vol_delta | WEAK POS | 135 | 74.1% | +0.4% |
| vol_roc | HIGH (30+) | 104 | 74.0% | +0.4% |
| vol_roc | LOW (0-30) | 58 | 74.1% | +0.5% |
| vol_roc | NEGATIVE | 206 | 73.3% | -0.3% |

### EPCH4_SHORT (Baseline: 70.1%)

| Indicator | Bucket | N | Win Rate | Lift |
|-----------|--------|---|----------|------|
| candle_range_pct | HIGH (0.20+) | 133 | 75.2% | +5.1% |
| candle_range_pct | LOW (<0.10) | 66 | 56.1% | -14.1% |
| candle_range_pct | MID (0.10-0.20) | 109 | 72.5% | +2.4% |
| long_score | HIGH (5-7) | 14* | 100.0% | +29.9% |
| long_score | LOW (0-2) | 154 | 61.7% | -8.4% |
| long_score | MID (3-4) | 140 | 76.4% | +6.3% |
| short_score | HIGH (5-7) | 18* | 72.2% | +2.1% |
| short_score | LOW (0-2) | 145 | 68.3% | -1.8% |
| short_score | MID (3-4) | 145 | 71.7% | +1.6% |
| vol_delta | STRONG NEG | 54 | 92.6% | +22.5% |
| vol_delta | STRONG POS | 60 | 78.3% | +8.2% |
| vol_delta | WEAK NEG | 95 | 63.2% | -7.0% |
| vol_delta | WEAK POS | 99 | 59.6% | -10.5% |
| vol_roc | HIGH (30+) | 83 | 63.9% | -6.3% |
| vol_roc | LOW (0-30) | 55 | 78.2% | +8.0% |
| vol_roc | NEGATIVE | 170 | 70.6% | +0.5% |


## Claude Analysis Instructions
Analyze entry bar values to identify:
1. Optimal score ranges for entry (e.g., long_score 5-7 for Long trades)
2. Vol_delta magnitude thresholds that improve win rates
3. Entry bar "red flags" that should prevent entry
4. Model-specific entry criteria

*Note: Rows marked with * have fewer than 30 trades.*

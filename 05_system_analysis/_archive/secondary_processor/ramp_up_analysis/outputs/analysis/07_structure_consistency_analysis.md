# Structure Consistency Analysis

## Metadata
- **Generated**: 2026-01-19 17:38:38
- **Stop Type**: m5_atr

## Overview
This analysis shows win rates based on M15 and H1 **structure consistency** during the ramp period.

### Consistency States
- **CONSISTENT_BULL**: Structure bullish for 80%+ of ramp bars
- **CONSISTENT_BEAR**: Structure bearish for 80%+ of ramp bars
- **FLIP_TO_BULL**: Structure changed from bearish to bullish during ramp
- **FLIP_TO_BEAR**: Structure changed from bullish to bearish during ramp
- **MIXED**: No clear pattern

## Data by Model + Direction

### EPCH1_LONG (Baseline: 57.6%)

| Timeframe | Consistency | N | Win Rate | Lift |
|-----------|-------------|---|----------|------|
| H1 | CONSISTENT_BEAR | 15* | 60.0% | +2.4% |
| H1 | CONSISTENT_BULL | 18* | 55.6% | -2.0% |
| M15 | CONSISTENT_BEAR | 18* | 66.7% | +9.1% |
| M15 | CONSISTENT_BULL | 14* | 50.0% | -7.6% |
| M15 | FLIP_TO_BULL | 1* | 0.0% | -57.6% |

### EPCH1_SHORT (Baseline: 65.8%)

| Timeframe | Consistency | N | Win Rate | Lift |
|-----------|-------------|---|----------|------|
| H1 | CONSISTENT_BEAR | 11* | 54.6% | -11.3% |
| H1 | CONSISTENT_BULL | 30 | 70.0% | +4.2% |
| M15 | CONSISTENT_BEAR | 12* | 50.0% | -15.8% |
| M15 | CONSISTENT_BULL | 29* | 72.4% | +6.6% |

### EPCH2_LONG (Baseline: 57.4%)

| Timeframe | Consistency | N | Win Rate | Lift |
|-----------|-------------|---|----------|------|
| H1 | CONSISTENT_BEAR | 231 | 66.2% | +8.9% |
| H1 | CONSISTENT_BULL | 153 | 43.1% | -14.2% |
| H1 | FLIP_TO_BULL | 3* | 100.0% | +42.6% |
| M15 | CONSISTENT_BEAR | 233 | 52.4% | -5.0% |
| M15 | CONSISTENT_BULL | 144 | 65.3% | +7.9% |
| M15 | FLIP_TO_BEAR | 4* | 50.0% | -7.4% |
| M15 | FLIP_TO_BULL | 6* | 66.7% | +9.3% |

### EPCH2_SHORT (Baseline: 64.7%)

| Timeframe | Consistency | N | Win Rate | Lift |
|-----------|-------------|---|----------|------|
| H1 | CONSISTENT_BEAR | 129 | 54.3% | -10.5% |
| H1 | CONSISTENT_BULL | 262 | 70.2% | +5.5% |
| H1 | FLIP_TO_BULL | 3* | 33.3% | -31.4% |
| M15 | CONSISTENT_BEAR | 100 | 38.0% | -26.7% |
| M15 | CONSISTENT_BULL | 287 | 73.9% | +9.2% |
| M15 | FLIP_TO_BEAR | 6* | 66.7% | +2.0% |
| M15 | FLIP_TO_BULL | 1* | 100.0% | +35.3% |

### EPCH3_LONG (Baseline: 71.0%)

| Timeframe | Consistency | N | Win Rate | Lift |
|-----------|-------------|---|----------|------|
| H1 | CONSISTENT_BEAR | 23* | 69.6% | -1.4% |
| H1 | CONSISTENT_BULL | 8* | 75.0% | +4.0% |
| M15 | CONSISTENT_BEAR | 18* | 61.1% | -9.9% |
| M15 | CONSISTENT_BULL | 12* | 91.7% | +20.7% |
| M15 | FLIP_TO_BEAR | 1* | 100.0% | +23.1% |
| M15 | FLIP_TO_BULL | 1* | 0.0% | -71.0% |

### EPCH3_SHORT (Baseline: 81.2%)

| Timeframe | Consistency | N | Win Rate | Lift |
|-----------|-------------|---|----------|------|
| H1 | CONSISTENT_BEAR | 11* | 81.8% | +0.6% |
| H1 | CONSISTENT_BULL | 21* | 81.0% | -0.3% |
| M15 | CONSISTENT_BEAR | 14* | 78.6% | -2.7% |
| M15 | CONSISTENT_BULL | 17* | 82.4% | +1.1% |
| M15 | FLIP_TO_BEAR | 1* | 100.0% | +18.8% |

### EPCH4_LONG (Baseline: 73.6%)

| Timeframe | Consistency | N | Win Rate | Lift |
|-----------|-------------|---|----------|------|
| H1 | CONSISTENT_BEAR | 171 | 66.1% | -7.6% |
| H1 | CONSISTENT_BULL | 195 | 80.0% | +6.4% |
| H1 | FLIP_TO_BULL | 2* | 100.0% | +26.4% |
| M15 | CONSISTENT_BEAR | 156 | 59.6% | -14.0% |
| M15 | CONSISTENT_BULL | 204 | 85.8% | +12.1% |
| M15 | FLIP_TO_BEAR | 3* | 66.7% | -7.0% |
| M15 | FLIP_TO_BULL | 5* | 20.0% | -53.6% |

### EPCH4_SHORT (Baseline: 70.1%)

| Timeframe | Consistency | N | Win Rate | Lift |
|-----------|-------------|---|----------|------|
| H1 | CONSISTENT_BEAR | 145 | 77.9% | +7.8% |
| H1 | CONSISTENT_BULL | 159 | 62.3% | -7.9% |
| H1 | FLIP_TO_BULL | 4* | 100.0% | +29.9% |
| M15 | CONSISTENT_BEAR | 148 | 72.3% | +2.2% |
| M15 | CONSISTENT_BULL | 152 | 69.1% | -1.0% |
| M15 | FLIP_TO_BEAR | 5* | 20.0% | -50.1% |
| M15 | FLIP_TO_BULL | 3* | 100.0% | +29.9% |


## Claude Analysis Instructions
Analyze structure consistency patterns:
1. Does consistent structure alignment with trade direction improve win rates?
2. Are FLIP patterns (structure changing) predictive for any model?
3. Which timeframe (M15 vs H1) is more predictive?
4. Do Rejection trades benefit from counter-structure setups?

*Note: Rows marked with * have fewer than 30 trades.*

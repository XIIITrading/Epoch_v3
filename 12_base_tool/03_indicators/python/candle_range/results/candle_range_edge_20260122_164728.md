# Candle Range Edge Analysis Report (CALC-011)

**Generated:** 2026-01-22 16:47:28
**Data Range:** 2025-12-15 to 2026-01-22
**Total Trades:** 3,610
**Stop Type:** zone_buffer
**Baseline Win Rate:** 44.2%

**Candle Range Statistics:**
- Mean: 0.232%
- Median: 0.159%
- Std Dev: 0.249%

**Data Source:** `m1_indicator_bars` table - using OHLC from prior M1 bar before entry

**Candle Range Calculation:** `(high - low) / open * 100`

---

## Model Legend

| Model | Description |
|-------|-------------|
| EPCH1 | Primary Continuation |
| EPCH2 | Primary Rejection |
| EPCH3 | Secondary Continuation |
| EPCH4 | Secondary Rejection |

---

## Executive Summary

### Overall

| Test | Segment | Edge? | Conf | Effect | p-value |
|------|---------|-------|------|--------|---------|
| Absorption Zone (<0.12%) | ALL | **YES** | HIGH | 13.5pp | 0.0000 |
| Range Threshold (0.12%) | ALL | **YES** | HIGH | 13.5pp | 0.0000 |
| Range Threshold (0.15%) | ALL | **YES** | HIGH | 15.7pp | 0.0000 |
| Range Threshold (0.18%) | ALL | **YES** | HIGH | 19.1pp | 0.0000 |
| Range Threshold (0.2%) | ALL | **YES** | HIGH | 18.4pp | 0.0000 |
| Range Magnitude (Quintiles) | ALL | **YES** | HIGH | 19.0pp | 0.0374 |
| Range Category (5-tier) | ALL | NO | HIGH | 19.7pp | 0.1881 |

### By Direction

| Test | Segment | Edge? | Conf | Effect | p-value |
|------|---------|-------|------|--------|---------|
| Absorption Zone (<0.12%) | LONG | **YES** | HIGH | 14.3pp | 0.0000 |
| Range Threshold (0.12%) | LONG | **YES** | HIGH | 14.3pp | 0.0000 |
| Range Threshold (0.15%) | LONG | **YES** | HIGH | 16.2pp | 0.0000 |
| Range Threshold (0.18%) | LONG | **YES** | HIGH | 19.3pp | 0.0000 |
| Range Threshold (0.2%) | LONG | **YES** | HIGH | 19.8pp | 0.0000 |
| Range Magnitude (Quintiles) | LONG | NO | HIGH | 22.0pp | 0.1881 |
| Range Category (5-tier) | LONG | **YES** | MEDIUM | 20.9pp | 0.0374 |
| Absorption Zone (<0.12%) | SHORT | **YES** | HIGH | 12.9pp | 0.0000 |
| Range Threshold (0.12%) | SHORT | **YES** | HIGH | 12.9pp | 0.0000 |
| Range Threshold (0.15%) | SHORT | **YES** | HIGH | 15.3pp | 0.0000 |
| Range Threshold (0.18%) | SHORT | **YES** | HIGH | 19.0pp | 0.0000 |
| Range Threshold (0.2%) | SHORT | **YES** | HIGH | 17.2pp | 0.0000 |
| Range Magnitude (Quintiles) | SHORT | NO | HIGH | 15.1pp | 0.1041 |
| Range Category (5-tier) | SHORT | NO | MEDIUM | 18.7pp | 0.2848 |

### By Trade Type

| Test | Segment | Edge? | Conf | Effect | p-value |
|------|---------|-------|------|--------|---------|
| Absorption Zone (<0.12%) | CONTINUATION (Combined) | NO | MEDIUM | 8.6pp | 0.2204 |
| Range Threshold (0.12%) | CONTINUATION (Combined) | NO | MEDIUM | 8.6pp | 0.2204 |
| Range Threshold (0.15%) | CONTINUATION (Combined) | NO | HIGH | 7.1pp | 0.2562 |
| Range Threshold (0.18%) | CONTINUATION (Combined) | **YES** | HIGH | 13.4pp | 0.0198 |
| Range Threshold (0.2%) | CONTINUATION (Combined) | **YES** | HIGH | 14.4pp | 0.0120 |
| Range Magnitude (Quintiles) | CONTINUATION (Combined) | NO | MEDIUM | 15.1pp | 0.3217 |
| Range Category (5-tier) | CONTINUATION (Combined) | NO | LOW | 13.7pp | 0.7471 |
| Absorption Zone (<0.12%) | REJECTION (Combined) | **YES** | HIGH | 14.0pp | 0.0000 |
| Range Threshold (0.12%) | REJECTION (Combined) | **YES** | HIGH | 14.0pp | 0.0000 |
| Range Threshold (0.15%) | REJECTION (Combined) | **YES** | HIGH | 16.6pp | 0.0000 |
| Range Threshold (0.18%) | REJECTION (Combined) | **YES** | HIGH | 19.8pp | 0.0000 |
| Range Threshold (0.2%) | REJECTION (Combined) | **YES** | HIGH | 18.9pp | 0.0000 |
| Range Magnitude (Quintiles) | REJECTION (Combined) | **YES** | HIGH | 21.1pp | 0.0374 |
| Range Category (5-tier) | REJECTION (Combined) | **YES** | HIGH | 20.4pp | 0.0000 |

### By Model - Continuation

| Test | Segment | Edge? | Conf | Effect | p-value |
|------|---------|-------|------|--------|---------|
| Absorption Zone (<0.12%) | EPCH1 (Primary Cont.) | NO | MEDIUM | 1.8pp | 0.9858 |
| Range Threshold (0.12%) | EPCH1 (Primary Cont.) | NO | MEDIUM | 1.8pp | 0.9858 |
| Range Threshold (0.15%) | EPCH1 (Primary Cont.) | NO | MEDIUM | 0.5pp | 1.0000 |
| Range Threshold (0.18%) | EPCH1 (Primary Cont.) | NO | MEDIUM | 5.3pp | 0.5597 |
| Range Threshold (0.2%) | EPCH1 (Primary Cont.) | NO | MEDIUM | 10.3pp | 0.2014 |
| Range Magnitude (Quintiles) | EPCH1 (Primary Cont.) | NO | MEDIUM | 13.1pp | 0.2848 |
| Range Category (5-tier) | EPCH1 (Primary Cont.) | NO | LOW | 6.4pp | 0.8729 |
| Absorption Zone (<0.12%) | EPCH3 (Secondary Cont.) | NO | MEDIUM | 17.2pp | 0.0901 |
| Range Threshold (0.12%) | EPCH3 (Secondary Cont.) | NO | MEDIUM | 17.2pp | 0.0901 |
| Range Threshold (0.15%) | EPCH3 (Secondary Cont.) | NO | MEDIUM | 16.5pp | 0.0800 |
| Range Threshold (0.18%) | EPCH3 (Secondary Cont.) | **YES** | MEDIUM | 25.1pp | 0.0051 |
| Range Threshold (0.2%) | EPCH3 (Secondary Cont.) | **YES** | MEDIUM | 20.6pp | 0.0239 |
| Range Magnitude (Quintiles) | EPCH3 (Secondary Cont.) | NO | LOW | 10.7pp | 0.1041 |
| Range Category (5-tier) | EPCH3 (Secondary Cont.) | NO | LOW | 22.7pp | 0.2848 |

### By Model - Rejection

| Test | Segment | Edge? | Conf | Effect | p-value |
|------|---------|-------|------|--------|---------|
| Absorption Zone (<0.12%) | EPCH2 (Primary Rej.) | **YES** | HIGH | 7.9pp | 0.0008 |
| Range Threshold (0.12%) | EPCH2 (Primary Rej.) | **YES** | HIGH | 7.9pp | 0.0008 |
| Range Threshold (0.15%) | EPCH2 (Primary Rej.) | **YES** | HIGH | 11.0pp | 0.0000 |
| Range Threshold (0.18%) | EPCH2 (Primary Rej.) | **YES** | HIGH | 13.9pp | 0.0000 |
| Range Threshold (0.2%) | EPCH2 (Primary Rej.) | **YES** | HIGH | 13.4pp | 0.0000 |
| Range Magnitude (Quintiles) | EPCH2 (Primary Rej.) | NO | HIGH | 12.2pp | 0.1881 |
| Range Category (5-tier) | EPCH2 (Primary Rej.) | NO | MEDIUM | 13.2pp | 0.1881 |
| Absorption Zone (<0.12%) | EPCH4 (Secondary Rej.) | **YES** | HIGH | 22.4pp | 0.0000 |
| Range Threshold (0.12%) | EPCH4 (Secondary Rej.) | **YES** | HIGH | 22.4pp | 0.0000 |
| Range Threshold (0.15%) | EPCH4 (Secondary Rej.) | **YES** | HIGH | 24.4pp | 0.0000 |
| Range Threshold (0.18%) | EPCH4 (Secondary Rej.) | **YES** | HIGH | 28.2pp | 0.0000 |
| Range Threshold (0.2%) | EPCH4 (Secondary Rej.) | **YES** | HIGH | 26.9pp | 0.0000 |
| Range Magnitude (Quintiles) | EPCH4 (Secondary Rej.) | **YES** | HIGH | 32.5pp | 0.0374 |
| Range Category (5-tier) | EPCH4 (Secondary Rej.) | **YES** | MEDIUM | 30.5pp | 0.0374 |

---

## Key Findings (Edges Detected)

- **ALL** - Absorption Zone (<0.12%): 13.5pp advantage (p=0.0000)
- **ALL** - Range Threshold (0.12%): 13.5pp advantage (p=0.0000)
- **ALL** - Range Threshold (0.15%): 15.7pp advantage (p=0.0000)
- **ALL** - Range Threshold (0.18%): 19.1pp advantage (p=0.0000)
- **ALL** - Range Threshold (0.2%): 18.4pp advantage (p=0.0000)
- **ALL** - Range Magnitude (Quintiles): 19.0pp advantage (p=0.0374)
- **LONG** - Absorption Zone (<0.12%): 14.3pp advantage (p=0.0000)
- **LONG** - Range Threshold (0.12%): 14.3pp advantage (p=0.0000)
- **LONG** - Range Threshold (0.15%): 16.2pp advantage (p=0.0000)
- **LONG** - Range Threshold (0.18%): 19.3pp advantage (p=0.0000)
- **LONG** - Range Threshold (0.2%): 19.8pp advantage (p=0.0000)
- **LONG** - Range Category (5-tier): 20.9pp advantage (p=0.0374)
- **SHORT** - Absorption Zone (<0.12%): 12.9pp advantage (p=0.0000)
- **SHORT** - Range Threshold (0.12%): 12.9pp advantage (p=0.0000)
- **SHORT** - Range Threshold (0.15%): 15.3pp advantage (p=0.0000)
- **SHORT** - Range Threshold (0.18%): 19.0pp advantage (p=0.0000)
- **SHORT** - Range Threshold (0.2%): 17.2pp advantage (p=0.0000)
- **CONTINUATION (Combined)** - Range Threshold (0.18%): 13.4pp advantage (p=0.0198)
- **CONTINUATION (Combined)** - Range Threshold (0.2%): 14.4pp advantage (p=0.0120)
- **REJECTION (Combined)** - Absorption Zone (<0.12%): 14.0pp advantage (p=0.0000)
- **REJECTION (Combined)** - Range Threshold (0.12%): 14.0pp advantage (p=0.0000)
- **REJECTION (Combined)** - Range Threshold (0.15%): 16.6pp advantage (p=0.0000)
- **REJECTION (Combined)** - Range Threshold (0.18%): 19.8pp advantage (p=0.0000)
- **REJECTION (Combined)** - Range Threshold (0.2%): 18.9pp advantage (p=0.0000)
- **REJECTION (Combined)** - Range Magnitude (Quintiles): 21.1pp advantage (p=0.0374)
- **REJECTION (Combined)** - Range Category (5-tier): 20.4pp advantage (p=0.0000)
- **EPCH3 (Secondary Cont.)** - Range Threshold (0.18%): 25.1pp advantage (p=0.0051)
- **EPCH3 (Secondary Cont.)** - Range Threshold (0.2%): 20.6pp advantage (p=0.0239)
- **EPCH2 (Primary Rej.)** - Absorption Zone (<0.12%): 7.9pp advantage (p=0.0008)
- **EPCH2 (Primary Rej.)** - Range Threshold (0.12%): 7.9pp advantage (p=0.0008)
- **EPCH2 (Primary Rej.)** - Range Threshold (0.15%): 11.0pp advantage (p=0.0000)
- **EPCH2 (Primary Rej.)** - Range Threshold (0.18%): 13.9pp advantage (p=0.0000)
- **EPCH2 (Primary Rej.)** - Range Threshold (0.2%): 13.4pp advantage (p=0.0000)
- **EPCH4 (Secondary Rej.)** - Absorption Zone (<0.12%): 22.4pp advantage (p=0.0000)
- **EPCH4 (Secondary Rej.)** - Range Threshold (0.12%): 22.4pp advantage (p=0.0000)
- **EPCH4 (Secondary Rej.)** - Range Threshold (0.15%): 24.4pp advantage (p=0.0000)
- **EPCH4 (Secondary Rej.)** - Range Threshold (0.18%): 28.2pp advantage (p=0.0000)
- **EPCH4 (Secondary Rej.)** - Range Threshold (0.2%): 26.9pp advantage (p=0.0000)
- **EPCH4 (Secondary Rej.)** - Range Magnitude (Quintiles): 32.5pp advantage (p=0.0374)
- **EPCH4 (Secondary Rej.)** - Range Category (5-tier): 30.5pp advantage (p=0.0374)

---

## Detailed Results

### Overall

#### ALL

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 1,339 | 478 | 35.7% | -8.5pp |
| NORMAL | 2,271 | 1,118 | 49.2% | +5.0pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 13.5pp
- **Confidence:** HIGH
- **Verdict:** SKIP FILTER VALIDATED - Absorption zone (35.7% WR) underperforms normal (49.2% WR). Effect: 13.5pp

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 2,271 | 1,118 | 49.2% | +5.0pp |
| SMALL_<0.12% | 1,339 | 478 | 35.7% | -8.5pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 13.5pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 13.5pp

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 1,888 | 976 | 51.7% | +7.5pp |
| SMALL_<0.15% | 1,722 | 620 | 36.0% | -8.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 15.7pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 15.7pp

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 1,560 | 859 | 55.1% | +10.8pp |
| SMALL_<0.18% | 2,050 | 737 | 36.0% | -8.3pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 19.1pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 19.1pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 1,407 | 780 | 55.4% | +11.2pp |
| SMALL_<0.20% | 2,203 | 816 | 37.0% | -7.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 18.4pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 18.4pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 722 | 270 | 37.4% | -6.8pp |
| Q2 | 722 | 243 | 33.7% | -10.6pp |
| Q3 | 722 | 281 | 38.9% | -5.3pp |
| Q4 | 722 | 395 | 54.7% | +10.5pp |
| Q5_Largest | 722 | 407 | 56.4% | +12.2pp |

- **Test Type:** spearman
- **P-value:** 0.0374
- **Effect Size:** 19.0pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - larger candle range correlates with higher win rate (r=0.900)

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 153 | 79 | 51.6% | +7.4pp |
| MEDIUM | 328 | 117 | 35.7% | -8.5pp |
| SMALL | 383 | 142 | 37.1% | -7.1pp |
| VERY_LARGE | 1,407 | 780 | 55.4% | +11.2pp |
| VERY_SMALL | 1,339 | 478 | 35.7% | -8.5pp |

- **Test Type:** spearman
- **P-value:** 0.1881
- **Effect Size:** 19.7pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.1881)

### By Direction

#### LONG

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 736 | 262 | 35.6% | -8.3pp |
| NORMAL | 1,035 | 516 | 49.9% | +5.9pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 14.3pp
- **Confidence:** HIGH
- **Verdict:** SKIP FILTER VALIDATED - Absorption zone (35.6% WR) underperforms normal (49.9% WR). Effect: 14.3pp

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 1,035 | 516 | 49.9% | +5.9pp |
| SMALL_<0.12% | 736 | 262 | 35.6% | -8.3pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 14.3pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 14.3pp

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 857 | 448 | 52.3% | +8.4pp |
| SMALL_<0.15% | 914 | 330 | 36.1% | -7.8pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 16.2pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 16.2pp

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 708 | 393 | 55.5% | +11.6pp |
| SMALL_<0.18% | 1,063 | 385 | 36.2% | -7.7pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 19.3pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 19.3pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 644 | 364 | 56.5% | +12.6pp |
| SMALL_<0.20% | 1,127 | 414 | 36.7% | -7.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 19.8pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 19.8pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 356 | 137 | 38.5% | -5.4pp |
| Q2 | 353 | 114 | 32.3% | -11.6pp |
| Q3 | 354 | 134 | 37.9% | -6.1pp |
| Q4 | 354 | 179 | 50.6% | +6.6pp |
| Q5_Largest | 354 | 214 | 60.5% | +16.5pp |

- **Test Type:** spearman
- **P-value:** 0.1881
- **Effect Size:** 22.0pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.1881)

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 64 | 29 | 45.3% | +1.4pp |
| MEDIUM | 149 | 55 | 36.9% | -7.0pp |
| SMALL | 178 | 68 | 38.2% | -5.7pp |
| VERY_LARGE | 644 | 364 | 56.5% | +12.6pp |
| VERY_SMALL | 736 | 262 | 35.6% | -8.3pp |

- **Test Type:** spearman
- **P-value:** 0.0374
- **Effect Size:** 20.9pp
- **Confidence:** MEDIUM
- **Verdict:** EDGE DETECTED - larger range category correlates with higher win rate (r=0.900)

#### SHORT

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 603 | 216 | 35.8% | -8.7pp |
| NORMAL | 1,236 | 602 | 48.7% | +4.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 12.9pp
- **Confidence:** HIGH
- **Verdict:** SKIP FILTER VALIDATED - Absorption zone (35.8% WR) underperforms normal (48.7% WR). Effect: 12.9pp

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 1,236 | 602 | 48.7% | +4.2pp |
| SMALL_<0.12% | 603 | 216 | 35.8% | -8.7pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 12.9pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 12.9pp

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 1,031 | 528 | 51.2% | +6.7pp |
| SMALL_<0.15% | 808 | 290 | 35.9% | -8.6pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 15.3pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 15.3pp

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 852 | 466 | 54.7% | +10.2pp |
| SMALL_<0.18% | 987 | 352 | 35.7% | -8.8pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 19.0pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 19.0pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 763 | 416 | 54.5% | +10.0pp |
| SMALL_<0.20% | 1,076 | 402 | 37.4% | -7.1pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 17.2pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 17.2pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 368 | 141 | 38.3% | -6.2pp |
| Q2 | 368 | 118 | 32.1% | -12.4pp |
| Q3 | 367 | 155 | 42.2% | -2.3pp |
| Q4 | 369 | 208 | 56.4% | +11.9pp |
| Q5_Largest | 367 | 196 | 53.4% | +8.9pp |

- **Test Type:** spearman
- **P-value:** 0.1041
- **Effect Size:** 15.1pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.1041)

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 89 | 50 | 56.2% | +11.7pp |
| MEDIUM | 179 | 62 | 34.6% | -9.8pp |
| SMALL | 205 | 74 | 36.1% | -8.4pp |
| VERY_LARGE | 763 | 416 | 54.5% | +10.0pp |
| VERY_SMALL | 603 | 216 | 35.8% | -8.7pp |

- **Test Type:** spearman
- **P-value:** 0.2848
- **Effect Size:** 18.7pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.2848)

### By Trade Type

#### CONTINUATION (Combined)

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 80 | 30 | 37.5% | -6.5pp |
| NORMAL | 247 | 114 | 46.1% | +2.1pp |

- **Test Type:** chi_square
- **P-value:** 0.2204
- **Effect Size:** 8.6pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.2204)

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 247 | 114 | 46.1% | +2.1pp |
| SMALL_<0.12% | 80 | 30 | 37.5% | -6.5pp |

- **Test Type:** chi_square
- **P-value:** 0.2204
- **Effect Size:** 8.6pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.2204)

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 208 | 97 | 46.6% | +2.6pp |
| SMALL_<0.15% | 119 | 47 | 39.5% | -4.5pp |

- **Test Type:** chi_square
- **P-value:** 0.2562
- **Effect Size:** 7.1pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.2562)

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 175 | 88 | 50.3% | +6.3pp |
| SMALL_<0.18% | 152 | 56 | 36.8% | -7.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0198
- **Effect Size:** 13.4pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 13.4pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 164 | 84 | 51.2% | +7.2pp |
| SMALL_<0.20% | 163 | 60 | 36.8% | -7.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0120
- **Effect Size:** 14.4pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 14.4pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 66 | 25 | 37.9% | -6.2pp |
| Q2 | 65 | 24 | 36.9% | -7.1pp |
| Q3 | 65 | 24 | 36.9% | -7.1pp |
| Q4 | 65 | 36 | 55.4% | +11.3pp |
| Q5_Largest | 66 | 35 | 53.0% | +9.0pp |

- **Test Type:** spearman
- **P-value:** 0.3217
- **Effect Size:** 15.1pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.3217)

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 11 | 4 | 36.4% | -7.7pp |
| MEDIUM | 33 | 9 | 27.3% | -16.8pp |
| SMALL | 39 | 17 | 43.6% | -0.4pp |
| VERY_LARGE | 164 | 84 | 51.2% | +7.2pp |
| VERY_SMALL | 80 | 30 | 37.5% | -6.5pp |

- **Test Type:** spearman
- **P-value:** 0.7471
- **Effect Size:** 13.7pp
- **Confidence:** LOW
- **Verdict:** INSUFFICIENT DATA - Need more trades for reliable conclusion

#### REJECTION (Combined)

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 1,259 | 448 | 35.6% | -8.6pp |
| NORMAL | 2,024 | 1,004 | 49.6% | +5.4pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 14.0pp
- **Confidence:** HIGH
- **Verdict:** SKIP FILTER VALIDATED - Absorption zone (35.6% WR) underperforms normal (49.6% WR). Effect: 14.0pp

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 2,024 | 1,004 | 49.6% | +5.4pp |
| SMALL_<0.12% | 1,259 | 448 | 35.6% | -8.6pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 14.0pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 14.0pp

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 1,680 | 879 | 52.3% | +8.1pp |
| SMALL_<0.15% | 1,603 | 573 | 35.8% | -8.5pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 16.6pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 16.6pp

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 1,385 | 771 | 55.7% | +11.4pp |
| SMALL_<0.18% | 1,898 | 681 | 35.9% | -8.3pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 19.8pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 19.8pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 1,243 | 696 | 56.0% | +11.8pp |
| SMALL_<0.20% | 2,040 | 756 | 37.1% | -7.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 18.9pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 18.9pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 657 | 243 | 37.0% | -7.2pp |
| Q2 | 656 | 221 | 33.7% | -10.5pp |
| Q3 | 657 | 255 | 38.8% | -5.4pp |
| Q4 | 656 | 351 | 53.5% | +9.3pp |
| Q5_Largest | 657 | 382 | 58.1% | +13.9pp |

- **Test Type:** spearman
- **P-value:** 0.0374
- **Effect Size:** 21.1pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - larger candle range correlates with higher win rate (r=0.900)

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 142 | 75 | 52.8% | +8.6pp |
| MEDIUM | 295 | 108 | 36.6% | -7.6pp |
| SMALL | 344 | 125 | 36.3% | -7.9pp |
| VERY_LARGE | 1,243 | 696 | 56.0% | +11.8pp |
| VERY_SMALL | 1,259 | 448 | 35.6% | -8.6pp |

- **Test Type:** spearman
- **P-value:** 0.0000
- **Effect Size:** 20.4pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - larger range category correlates with higher win rate (r=1.000)

### By Model - Continuation

#### EPCH1 (Primary Cont.)

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 37 | 15 | 40.5% | -1.5pp |
| NORMAL | 151 | 64 | 42.4% | +0.4pp |

- **Test Type:** chi_square
- **P-value:** 0.9858
- **Effect Size:** 1.8pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.9858)

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 151 | 64 | 42.4% | +0.4pp |
| SMALL_<0.12% | 37 | 15 | 40.5% | -1.5pp |

- **Test Type:** chi_square
- **P-value:** 0.9858
- **Effect Size:** 1.8pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.9858)

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 128 | 54 | 42.2% | +0.2pp |
| SMALL_<0.15% | 60 | 25 | 41.7% | -0.4pp |

- **Test Type:** chi_square
- **P-value:** 1.0000
- **Effect Size:** 0.5pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=1.0000)

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 106 | 47 | 44.3% | +2.3pp |
| SMALL_<0.18% | 82 | 32 | 39.0% | -3.0pp |

- **Test Type:** chi_square
- **P-value:** 0.5597
- **Effect Size:** 5.3pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.5597)

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 98 | 46 | 46.9% | +4.9pp |
| SMALL_<0.20% | 90 | 33 | 36.7% | -5.4pp |

- **Test Type:** chi_square
- **P-value:** 0.2014
- **Effect Size:** 10.3pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.2014)

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 38 | 16 | 42.1% | +0.1pp |
| Q2 | 37 | 14 | 37.8% | -4.2pp |
| Q3 | 38 | 11 | 28.9% | -13.1pp |
| Q4 | 37 | 17 | 46.0% | +3.9pp |
| Q5_Largest | 38 | 21 | 55.3% | +13.2pp |

- **Test Type:** spearman
- **P-value:** 0.2848
- **Effect Size:** 13.1pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.2848)

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 8 | 1 | 12.5% | -29.5pp |
| MEDIUM | 22 | 7 | 31.8% | -10.2pp |
| SMALL | 23 | 10 | 43.5% | +1.5pp |
| VERY_LARGE | 98 | 46 | 46.9% | +4.9pp |
| VERY_SMALL | 37 | 15 | 40.5% | -1.5pp |

- **Test Type:** spearman
- **P-value:** 0.8729
- **Effect Size:** 6.4pp
- **Confidence:** LOW
- **Verdict:** INSUFFICIENT DATA - Need more trades for reliable conclusion

#### EPCH3 (Secondary Cont.)

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 43 | 15 | 34.9% | -11.9pp |
| NORMAL | 96 | 50 | 52.1% | +5.3pp |

- **Test Type:** chi_square
- **P-value:** 0.0901
- **Effect Size:** 17.2pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.0901)

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 96 | 50 | 52.1% | +5.3pp |
| SMALL_<0.12% | 43 | 15 | 34.9% | -11.9pp |

- **Test Type:** chi_square
- **P-value:** 0.0901
- **Effect Size:** 17.2pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.0901)

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 80 | 43 | 53.8% | +7.0pp |
| SMALL_<0.15% | 59 | 22 | 37.3% | -9.5pp |

- **Test Type:** chi_square
- **P-value:** 0.0800
- **Effect Size:** 16.5pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.0800)

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 69 | 41 | 59.4% | +12.7pp |
| SMALL_<0.18% | 70 | 24 | 34.3% | -12.5pp |

- **Test Type:** chi_square
- **P-value:** 0.0051
- **Effect Size:** 25.1pp
- **Confidence:** MEDIUM
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 25.1pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 66 | 38 | 57.6% | +10.8pp |
| SMALL_<0.20% | 73 | 27 | 37.0% | -9.8pp |

- **Test Type:** chi_square
- **P-value:** 0.0239
- **Effect Size:** 20.6pp
- **Confidence:** MEDIUM
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 20.6pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 28 | 12 | 42.9% | -3.9pp |
| Q2 | 28 | 8 | 28.6% | -18.2pp |
| Q3 | 27 | 12 | 44.4% | -2.3pp |
| Q4 | 28 | 18 | 64.3% | +17.5pp |
| Q5_Largest | 28 | 15 | 53.6% | +6.8pp |

- **Test Type:** spearman
- **P-value:** 0.1041
- **Effect Size:** 10.7pp
- **Confidence:** LOW
- **Verdict:** INSUFFICIENT DATA - Need more trades for reliable conclusion

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 3 | 3 | 100.0% | +53.2pp |
| MEDIUM | 11 | 2 | 18.2% | -28.6pp |
| SMALL | 16 | 7 | 43.8% | -3.0pp |
| VERY_LARGE | 66 | 38 | 57.6% | +10.8pp |
| VERY_SMALL | 43 | 15 | 34.9% | -11.9pp |

- **Test Type:** spearman
- **P-value:** 0.2848
- **Effect Size:** 22.7pp
- **Confidence:** LOW
- **Verdict:** INSUFFICIENT DATA - Need more trades for reliable conclusion

### By Model - Rejection

#### EPCH2 (Primary Rej.)

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 721 | 285 | 39.5% | -5.0pp |
| NORMAL | 1,201 | 570 | 47.5% | +3.0pp |

- **Test Type:** chi_square
- **P-value:** 0.0008
- **Effect Size:** 7.9pp
- **Confidence:** HIGH
- **Verdict:** SKIP FILTER VALIDATED - Absorption zone (39.5% WR) underperforms normal (47.5% WR). Effect: 7.9pp

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 1,201 | 570 | 47.5% | +3.0pp |
| SMALL_<0.12% | 721 | 285 | 39.5% | -5.0pp |

- **Test Type:** chi_square
- **P-value:** 0.0008
- **Effect Size:** 7.9pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 7.9pp

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 1,001 | 498 | 49.8% | +5.3pp |
| SMALL_<0.15% | 921 | 357 | 38.8% | -5.7pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 11.0pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 11.0pp

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 826 | 433 | 52.4% | +7.9pp |
| SMALL_<0.18% | 1,096 | 422 | 38.5% | -6.0pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 13.9pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 13.9pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 738 | 389 | 52.7% | +8.2pp |
| SMALL_<0.20% | 1,184 | 466 | 39.4% | -5.1pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 13.4pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 13.4pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 385 | 157 | 40.8% | -3.7pp |
| Q2 | 384 | 144 | 37.5% | -7.0pp |
| Q3 | 384 | 150 | 39.1% | -5.4pp |
| Q4 | 386 | 201 | 52.1% | +7.6pp |
| Q5_Largest | 383 | 203 | 53.0% | +8.5pp |

- **Test Type:** spearman
- **P-value:** 0.1881
- **Effect Size:** 12.2pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.1881)

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 88 | 44 | 50.0% | +5.5pp |
| MEDIUM | 175 | 65 | 37.1% | -7.3pp |
| SMALL | 200 | 72 | 36.0% | -8.5pp |
| VERY_LARGE | 738 | 389 | 52.7% | +8.2pp |
| VERY_SMALL | 721 | 285 | 39.5% | -5.0pp |

- **Test Type:** spearman
- **P-value:** 0.1881
- **Effect Size:** 13.2pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.1881)

#### EPCH4 (Secondary Rej.)

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 538 | 163 | 30.3% | -13.6pp |
| NORMAL | 823 | 434 | 52.7% | +8.9pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 22.4pp
- **Confidence:** HIGH
- **Verdict:** SKIP FILTER VALIDATED - Absorption zone (30.3% WR) underperforms normal (52.7% WR). Effect: 22.4pp

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 823 | 434 | 52.7% | +8.9pp |
| SMALL_<0.12% | 538 | 163 | 30.3% | -13.6pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 22.4pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 22.4pp

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 679 | 381 | 56.1% | +12.2pp |
| SMALL_<0.15% | 682 | 216 | 31.7% | -12.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 24.4pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 24.4pp

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 559 | 338 | 60.5% | +16.6pp |
| SMALL_<0.18% | 802 | 259 | 32.3% | -11.6pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 28.2pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 28.2pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 505 | 307 | 60.8% | +16.9pp |
| SMALL_<0.20% | 856 | 290 | 33.9% | -10.0pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 26.9pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 26.9pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 273 | 88 | 32.2% | -11.6pp |
| Q2 | 272 | 77 | 28.3% | -15.6pp |
| Q3 | 272 | 103 | 37.9% | -6.0pp |
| Q4 | 272 | 153 | 56.2% | +12.4pp |
| Q5_Largest | 272 | 176 | 64.7% | +20.8pp |

- **Test Type:** spearman
- **P-value:** 0.0374
- **Effect Size:** 32.5pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - larger candle range correlates with higher win rate (r=0.900)

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 54 | 31 | 57.4% | +13.5pp |
| MEDIUM | 120 | 43 | 35.8% | -8.0pp |
| SMALL | 144 | 53 | 36.8% | -7.1pp |
| VERY_LARGE | 505 | 307 | 60.8% | +16.9pp |
| VERY_SMALL | 538 | 163 | 30.3% | -13.6pp |

- **Test Type:** spearman
- **P-value:** 0.0374
- **Effect Size:** 30.5pp
- **Confidence:** MEDIUM
- **Verdict:** EDGE DETECTED - larger range category correlates with higher win rate (r=0.900)

---

## Recommendations

### Implement
1. **Absorption Zone (<0.12%) (ALL)**: SKIP FILTER VALIDATED - Absorption zone (35.7% WR) underperforms normal (49.2% WR). Effect: 13.5pp
1. **Range Threshold (0.12%) (ALL)**: EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 13.5pp
1. **Range Threshold (0.15%) (ALL)**: EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 15.7pp
1. **Range Threshold (0.18%) (ALL)**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 19.1pp
1. **Range Threshold (0.2%) (ALL)**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 18.4pp
1. **Range Magnitude (Quintiles) (ALL)**: EDGE DETECTED - larger candle range correlates with higher win rate (r=0.900)
1. **Absorption Zone (<0.12%) (LONG)**: SKIP FILTER VALIDATED - Absorption zone (35.6% WR) underperforms normal (49.9% WR). Effect: 14.3pp
1. **Range Threshold (0.12%) (LONG)**: EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 14.3pp
1. **Range Threshold (0.15%) (LONG)**: EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 16.2pp
1. **Range Threshold (0.18%) (LONG)**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 19.3pp
1. **Range Threshold (0.2%) (LONG)**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 19.8pp
1. **Range Category (5-tier) (LONG)**: EDGE DETECTED - larger range category correlates with higher win rate (r=0.900)
1. **Absorption Zone (<0.12%) (SHORT)**: SKIP FILTER VALIDATED - Absorption zone (35.8% WR) underperforms normal (48.7% WR). Effect: 12.9pp
1. **Range Threshold (0.12%) (SHORT)**: EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 12.9pp
1. **Range Threshold (0.15%) (SHORT)**: EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 15.3pp
1. **Range Threshold (0.18%) (SHORT)**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 19.0pp
1. **Range Threshold (0.2%) (SHORT)**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 17.2pp
1. **Range Threshold (0.18%) (CONTINUATION (Combined))**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 13.4pp
1. **Range Threshold (0.2%) (CONTINUATION (Combined))**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 14.4pp
1. **Absorption Zone (<0.12%) (REJECTION (Combined))**: SKIP FILTER VALIDATED - Absorption zone (35.6% WR) underperforms normal (49.6% WR). Effect: 14.0pp
1. **Range Threshold (0.12%) (REJECTION (Combined))**: EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 14.0pp
1. **Range Threshold (0.15%) (REJECTION (Combined))**: EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 16.6pp
1. **Range Threshold (0.18%) (REJECTION (Combined))**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 19.8pp
1. **Range Threshold (0.2%) (REJECTION (Combined))**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 18.9pp
1. **Range Magnitude (Quintiles) (REJECTION (Combined))**: EDGE DETECTED - larger candle range correlates with higher win rate (r=0.900)
1. **Range Category (5-tier) (REJECTION (Combined))**: EDGE DETECTED - larger range category correlates with higher win rate (r=1.000)
1. **Range Threshold (0.18%) (EPCH3 (Secondary Cont.))**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 25.1pp
1. **Range Threshold (0.2%) (EPCH3 (Secondary Cont.))**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 20.6pp
1. **Absorption Zone (<0.12%) (EPCH2 (Primary Rej.))**: SKIP FILTER VALIDATED - Absorption zone (39.5% WR) underperforms normal (47.5% WR). Effect: 7.9pp
1. **Range Threshold (0.12%) (EPCH2 (Primary Rej.))**: EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 7.9pp
1. **Range Threshold (0.15%) (EPCH2 (Primary Rej.))**: EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 11.0pp
1. **Range Threshold (0.18%) (EPCH2 (Primary Rej.))**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 13.9pp
1. **Range Threshold (0.2%) (EPCH2 (Primary Rej.))**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 13.4pp
1. **Absorption Zone (<0.12%) (EPCH4 (Secondary Rej.))**: SKIP FILTER VALIDATED - Absorption zone (30.3% WR) underperforms normal (52.7% WR). Effect: 22.4pp
1. **Range Threshold (0.12%) (EPCH4 (Secondary Rej.))**: EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 22.4pp
1. **Range Threshold (0.15%) (EPCH4 (Secondary Rej.))**: EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 24.4pp
1. **Range Threshold (0.18%) (EPCH4 (Secondary Rej.))**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 28.2pp
1. **Range Threshold (0.2%) (EPCH4 (Secondary Rej.))**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 26.9pp
1. **Range Magnitude (Quintiles) (EPCH4 (Secondary Rej.))**: EDGE DETECTED - larger candle range correlates with higher win rate (r=0.900)
1. **Range Category (5-tier) (EPCH4 (Secondary Rej.))**: EDGE DETECTED - larger range category correlates with higher win rate (r=0.900)

### No Action Needed
- Range Category (5-tier) (ALL): NO EDGE - Not statistically significant (p=0.1881)
- Range Magnitude (Quintiles) (LONG): NO EDGE - Not statistically significant (p=0.1881)
- Range Magnitude (Quintiles) (SHORT): NO EDGE - Not statistically significant (p=0.1041)
- Range Category (5-tier) (SHORT): NO EDGE - Not statistically significant (p=0.2848)
- Absorption Zone (<0.12%) (CONTINUATION (Combined)): NO EDGE - Not statistically significant (p=0.2204)
- Range Threshold (0.12%) (CONTINUATION (Combined)): NO EDGE - Not statistically significant (p=0.2204)
- Range Threshold (0.15%) (CONTINUATION (Combined)): NO EDGE - Not statistically significant (p=0.2562)
- Range Magnitude (Quintiles) (CONTINUATION (Combined)): NO EDGE - Not statistically significant (p=0.3217)
- Absorption Zone (<0.12%) (EPCH1 (Primary Cont.)): NO EDGE - Not statistically significant (p=0.9858)
- Range Threshold (0.12%) (EPCH1 (Primary Cont.)): NO EDGE - Not statistically significant (p=0.9858)
- Range Threshold (0.15%) (EPCH1 (Primary Cont.)): NO EDGE - Not statistically significant (p=1.0000)
- Range Threshold (0.18%) (EPCH1 (Primary Cont.)): NO EDGE - Not statistically significant (p=0.5597)
- Range Threshold (0.2%) (EPCH1 (Primary Cont.)): NO EDGE - Not statistically significant (p=0.2014)
- Range Magnitude (Quintiles) (EPCH1 (Primary Cont.)): NO EDGE - Not statistically significant (p=0.2848)
- Absorption Zone (<0.12%) (EPCH3 (Secondary Cont.)): NO EDGE - Not statistically significant (p=0.0901)
- Range Threshold (0.12%) (EPCH3 (Secondary Cont.)): NO EDGE - Not statistically significant (p=0.0901)
- Range Threshold (0.15%) (EPCH3 (Secondary Cont.)): NO EDGE - Not statistically significant (p=0.0800)
- Range Magnitude (Quintiles) (EPCH2 (Primary Rej.)): NO EDGE - Not statistically significant (p=0.1881)
- Range Category (5-tier) (EPCH2 (Primary Rej.)): NO EDGE - Not statistically significant (p=0.1881)

### Needs More Data
- Range Category (5-tier) (CONTINUATION (Combined)): Insufficient sample size for conclusion
- Range Category (5-tier) (EPCH1 (Primary Cont.)): Insufficient sample size for conclusion
- Range Magnitude (Quintiles) (EPCH3 (Secondary Cont.)): Insufficient sample size for conclusion
- Range Category (5-tier) (EPCH3 (Secondary Cont.)): Insufficient sample size for conclusion

---

## PyQt Tool Integration

### Standalone Candle Range Filters

| Filter | Condition | Action | Expected WR |
|--------|-----------|--------|-------------|
| Large Range | Range >= 0.15% | +1 point | 51-53% |
| Small Range | Range < 0.12% | -1 point (caution) | 37-38% |
| Very Large Range | Range >= 0.20% | +2 points | 55%+ |

### Composite Signal Filters (combine with Volume indicators)

| Filter | Condition | Action | Expected WR |
|--------|-----------|--------|-------------|
| Momentum | High Vol + Range >= 0.15% | TAKE (Rejection) | 58-60% |
| Absorption | High Vol + Range < 0.12% | SKIP | 35% |

---

## Statistical Notes

- **Significance Level:** alpha = 0.05
- **Effect Size Threshold:** 3.0pp minimum for practical significance
- **Confidence Levels:**
  - HIGH: >=100 trades per group
  - MEDIUM: >=30 trades per group
  - LOW: <30 trades per group (insufficient)

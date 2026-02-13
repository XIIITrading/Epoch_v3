# Candle Range Edge Analysis Report (CALC-011)

**Generated:** 2026-01-17 11:44:07
**Data Range:** 2025-12-15 to 2026-01-16
**Total Trades:** 2,788
**Stop Type:** zone_buffer
**Baseline Win Rate:** 44.4%

**Candle Range Statistics:**
- Mean: 0.223%
- Median: 0.154%
- Std Dev: 0.228%

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
| Absorption Zone (<0.12%) | ALL | **YES** | HIGH | 18.0pp | 0.0000 |
| Range Threshold (0.12%) | ALL | **YES** | HIGH | 18.0pp | 0.0000 |
| Range Threshold (0.15%) | ALL | **YES** | HIGH | 20.0pp | 0.0000 |
| Range Threshold (0.18%) | ALL | **YES** | HIGH | 21.4pp | 0.0000 |
| Range Threshold (0.2%) | ALL | **YES** | HIGH | 21.0pp | 0.0000 |
| Range Magnitude (Quintiles) | ALL | **YES** | HIGH | 28.7pp | 0.0000 |
| Range Category (5-tier) | ALL | **YES** | HIGH | 24.1pp | 0.0000 |

### By Direction

| Test | Segment | Edge? | Conf | Effect | p-value |
|------|---------|-------|------|--------|---------|
| Absorption Zone (<0.12%) | LONG | **YES** | HIGH | 19.5pp | 0.0000 |
| Range Threshold (0.12%) | LONG | **YES** | HIGH | 19.5pp | 0.0000 |
| Range Threshold (0.15%) | LONG | **YES** | HIGH | 21.3pp | 0.0000 |
| Range Threshold (0.18%) | LONG | **YES** | HIGH | 23.1pp | 0.0000 |
| Range Threshold (0.2%) | LONG | **YES** | HIGH | 23.4pp | 0.0000 |
| Range Magnitude (Quintiles) | LONG | **YES** | HIGH | 29.9pp | 0.0374 |
| Range Category (5-tier) | LONG | **YES** | MEDIUM | 26.5pp | 0.0000 |
| Absorption Zone (<0.12%) | SHORT | **YES** | HIGH | 16.3pp | 0.0000 |
| Range Threshold (0.12%) | SHORT | **YES** | HIGH | 16.3pp | 0.0000 |
| Range Threshold (0.15%) | SHORT | **YES** | HIGH | 18.6pp | 0.0000 |
| Range Threshold (0.18%) | SHORT | **YES** | HIGH | 19.8pp | 0.0000 |
| Range Threshold (0.2%) | SHORT | **YES** | HIGH | 18.5pp | 0.0000 |
| Range Magnitude (Quintiles) | SHORT | **YES** | HIGH | 24.6pp | 0.0000 |
| Range Category (5-tier) | SHORT | **YES** | MEDIUM | 21.6pp | 0.0000 |

### By Trade Type

| Test | Segment | Edge? | Conf | Effect | p-value |
|------|---------|-------|------|--------|---------|
| Absorption Zone (<0.12%) | CONTINUATION (Combined) | NO | MEDIUM | 11.4pp | 0.1248 |
| Range Threshold (0.12%) | CONTINUATION (Combined) | NO | MEDIUM | 11.4pp | 0.1248 |
| Range Threshold (0.15%) | CONTINUATION (Combined) | NO | HIGH | 11.3pp | 0.0889 |
| Range Threshold (0.18%) | CONTINUATION (Combined) | **YES** | HIGH | 16.3pp | 0.0105 |
| Range Threshold (0.2%) | CONTINUATION (Combined) | **YES** | HIGH | 17.6pp | 0.0054 |
| Range Magnitude (Quintiles) | CONTINUATION (Combined) | NO | MEDIUM | 22.2pp | 0.2189 |
| Range Category (5-tier) | CONTINUATION (Combined) | NO | LOW | 17.7pp | 0.7471 |
| Absorption Zone (<0.12%) | REJECTION (Combined) | **YES** | HIGH | 18.7pp | 0.0000 |
| Range Threshold (0.12%) | REJECTION (Combined) | **YES** | HIGH | 18.7pp | 0.0000 |
| Range Threshold (0.15%) | REJECTION (Combined) | **YES** | HIGH | 21.0pp | 0.0000 |
| Range Threshold (0.18%) | REJECTION (Combined) | **YES** | HIGH | 22.1pp | 0.0000 |
| Range Threshold (0.2%) | REJECTION (Combined) | **YES** | HIGH | 21.5pp | 0.0000 |
| Range Magnitude (Quintiles) | REJECTION (Combined) | **YES** | HIGH | 29.4pp | 0.0000 |
| Range Category (5-tier) | REJECTION (Combined) | **YES** | HIGH | 24.9pp | 0.0000 |

### By Model - Continuation

| Test | Segment | Edge? | Conf | Effect | p-value |
|------|---------|-------|------|--------|---------|
| Absorption Zone (<0.12%) | EPCH1 (Primary Cont.) | NO | MEDIUM | 3.4pp | 0.8806 |
| Range Threshold (0.12%) | EPCH1 (Primary Cont.) | NO | MEDIUM | 3.4pp | 0.8806 |
| Range Threshold (0.15%) | EPCH1 (Primary Cont.) | NO | MEDIUM | 4.8pp | 0.6922 |
| Range Threshold (0.18%) | EPCH1 (Primary Cont.) | NO | MEDIUM | 5.9pp | 0.5760 |
| Range Threshold (0.2%) | EPCH1 (Primary Cont.) | NO | MEDIUM | 12.5pp | 0.1674 |
| Range Magnitude (Quintiles) | EPCH1 (Primary Cont.) | NO | LOW | 23.3pp | 0.2848 |
| Range Category (5-tier) | EPCH1 (Primary Cont.) | NO | LOW | 9.0pp | 0.8729 |
| Absorption Zone (<0.12%) | EPCH3 (Secondary Cont.) | NO | MEDIUM | 20.9pp | 0.0528 |
| Range Threshold (0.12%) | EPCH3 (Secondary Cont.) | NO | MEDIUM | 20.9pp | 0.0528 |
| Range Threshold (0.15%) | EPCH3 (Secondary Cont.) | **YES** | MEDIUM | 19.8pp | 0.0486 |
| Range Threshold (0.18%) | EPCH3 (Secondary Cont.) | **YES** | MEDIUM | 29.6pp | 0.0021 |
| Range Threshold (0.2%) | EPCH3 (Secondary Cont.) | **YES** | MEDIUM | 24.4pp | 0.0129 |
| Range Magnitude (Quintiles) | EPCH3 (Secondary Cont.) | NO | LOW | 25.0pp | 0.1114 |
| Range Category (5-tier) | EPCH3 (Secondary Cont.) | NO | LOW | 27.7pp | 0.2848 |

### By Model - Rejection

| Test | Segment | Edge? | Conf | Effect | p-value |
|------|---------|-------|------|--------|---------|
| Absorption Zone (<0.12%) | EPCH2 (Primary Rej.) | **YES** | HIGH | 15.3pp | 0.0000 |
| Range Threshold (0.12%) | EPCH2 (Primary Rej.) | **YES** | HIGH | 15.3pp | 0.0000 |
| Range Threshold (0.15%) | EPCH2 (Primary Rej.) | **YES** | HIGH | 18.5pp | 0.0000 |
| Range Threshold (0.18%) | EPCH2 (Primary Rej.) | **YES** | HIGH | 19.8pp | 0.0000 |
| Range Threshold (0.2%) | EPCH2 (Primary Rej.) | **YES** | HIGH | 20.2pp | 0.0000 |
| Range Magnitude (Quintiles) | EPCH2 (Primary Rej.) | **YES** | HIGH | 28.3pp | 0.0000 |
| Range Category (5-tier) | EPCH2 (Primary Rej.) | **YES** | MEDIUM | 22.2pp | 0.0000 |
| Absorption Zone (<0.12%) | EPCH4 (Secondary Rej.) | **YES** | HIGH | 23.1pp | 0.0000 |
| Range Threshold (0.12%) | EPCH4 (Secondary Rej.) | **YES** | HIGH | 23.1pp | 0.0000 |
| Range Threshold (0.15%) | EPCH4 (Secondary Rej.) | **YES** | HIGH | 24.1pp | 0.0000 |
| Range Threshold (0.18%) | EPCH4 (Secondary Rej.) | **YES** | HIGH | 25.0pp | 0.0000 |
| Range Threshold (0.2%) | EPCH4 (Secondary Rej.) | **YES** | HIGH | 23.0pp | 0.0000 |
| Range Magnitude (Quintiles) | EPCH4 (Secondary Rej.) | **YES** | HIGH | 31.5pp | 0.0000 |
| Range Category (5-tier) | EPCH4 (Secondary Rej.) | **YES** | MEDIUM | 28.2pp | 0.0374 |

---

## Key Findings (Edges Detected)

- **ALL** - Absorption Zone (<0.12%): 18.0pp advantage (p=0.0000)
- **ALL** - Range Threshold (0.12%): 18.0pp advantage (p=0.0000)
- **ALL** - Range Threshold (0.15%): 20.0pp advantage (p=0.0000)
- **ALL** - Range Threshold (0.18%): 21.4pp advantage (p=0.0000)
- **ALL** - Range Threshold (0.2%): 21.0pp advantage (p=0.0000)
- **ALL** - Range Magnitude (Quintiles): 28.7pp advantage (p=0.0000)
- **ALL** - Range Category (5-tier): 24.1pp advantage (p=0.0000)
- **LONG** - Absorption Zone (<0.12%): 19.5pp advantage (p=0.0000)
- **LONG** - Range Threshold (0.12%): 19.5pp advantage (p=0.0000)
- **LONG** - Range Threshold (0.15%): 21.3pp advantage (p=0.0000)
- **LONG** - Range Threshold (0.18%): 23.1pp advantage (p=0.0000)
- **LONG** - Range Threshold (0.2%): 23.4pp advantage (p=0.0000)
- **LONG** - Range Magnitude (Quintiles): 29.9pp advantage (p=0.0374)
- **LONG** - Range Category (5-tier): 26.5pp advantage (p=0.0000)
- **SHORT** - Absorption Zone (<0.12%): 16.3pp advantage (p=0.0000)
- **SHORT** - Range Threshold (0.12%): 16.3pp advantage (p=0.0000)
- **SHORT** - Range Threshold (0.15%): 18.6pp advantage (p=0.0000)
- **SHORT** - Range Threshold (0.18%): 19.8pp advantage (p=0.0000)
- **SHORT** - Range Threshold (0.2%): 18.5pp advantage (p=0.0000)
- **SHORT** - Range Magnitude (Quintiles): 24.6pp advantage (p=0.0000)
- **SHORT** - Range Category (5-tier): 21.6pp advantage (p=0.0000)
- **CONTINUATION (Combined)** - Range Threshold (0.18%): 16.3pp advantage (p=0.0105)
- **CONTINUATION (Combined)** - Range Threshold (0.2%): 17.6pp advantage (p=0.0054)
- **REJECTION (Combined)** - Absorption Zone (<0.12%): 18.7pp advantage (p=0.0000)
- **REJECTION (Combined)** - Range Threshold (0.12%): 18.7pp advantage (p=0.0000)
- **REJECTION (Combined)** - Range Threshold (0.15%): 21.0pp advantage (p=0.0000)
- **REJECTION (Combined)** - Range Threshold (0.18%): 22.1pp advantage (p=0.0000)
- **REJECTION (Combined)** - Range Threshold (0.2%): 21.5pp advantage (p=0.0000)
- **REJECTION (Combined)** - Range Magnitude (Quintiles): 29.4pp advantage (p=0.0000)
- **REJECTION (Combined)** - Range Category (5-tier): 24.9pp advantage (p=0.0000)
- **EPCH3 (Secondary Cont.)** - Range Threshold (0.15%): 19.8pp advantage (p=0.0486)
- **EPCH3 (Secondary Cont.)** - Range Threshold (0.18%): 29.6pp advantage (p=0.0021)
- **EPCH3 (Secondary Cont.)** - Range Threshold (0.2%): 24.4pp advantage (p=0.0129)
- **EPCH2 (Primary Rej.)** - Absorption Zone (<0.12%): 15.3pp advantage (p=0.0000)
- **EPCH2 (Primary Rej.)** - Range Threshold (0.12%): 15.3pp advantage (p=0.0000)
- **EPCH2 (Primary Rej.)** - Range Threshold (0.15%): 18.5pp advantage (p=0.0000)
- **EPCH2 (Primary Rej.)** - Range Threshold (0.18%): 19.8pp advantage (p=0.0000)
- **EPCH2 (Primary Rej.)** - Range Threshold (0.2%): 20.2pp advantage (p=0.0000)
- **EPCH2 (Primary Rej.)** - Range Magnitude (Quintiles): 28.3pp advantage (p=0.0000)
- **EPCH2 (Primary Rej.)** - Range Category (5-tier): 22.2pp advantage (p=0.0000)
- **EPCH4 (Secondary Rej.)** - Absorption Zone (<0.12%): 23.1pp advantage (p=0.0000)
- **EPCH4 (Secondary Rej.)** - Range Threshold (0.12%): 23.1pp advantage (p=0.0000)
- **EPCH4 (Secondary Rej.)** - Range Threshold (0.15%): 24.1pp advantage (p=0.0000)
- **EPCH4 (Secondary Rej.)** - Range Threshold (0.18%): 25.0pp advantage (p=0.0000)
- **EPCH4 (Secondary Rej.)** - Range Threshold (0.2%): 23.0pp advantage (p=0.0000)
- **EPCH4 (Secondary Rej.)** - Range Magnitude (Quintiles): 31.5pp advantage (p=0.0000)
- **EPCH4 (Secondary Rej.)** - Range Category (5-tier): 28.2pp advantage (p=0.0374)

---

## Detailed Results

### Overall

#### ALL

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 1,066 | 355 | 33.3% | -11.1pp |
| NORMAL | 1,722 | 883 | 51.3% | +6.9pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 18.0pp
- **Confidence:** HIGH
- **Verdict:** SKIP FILTER VALIDATED - Absorption zone (33.3% WR) underperforms normal (51.3% WR). Effect: 18.0pp

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 1,722 | 883 | 51.3% | +6.9pp |
| SMALL_<0.12% | 1,066 | 355 | 33.3% | -11.1pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 18.0pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 18.0pp

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 1,425 | 772 | 54.2% | +9.8pp |
| SMALL_<0.15% | 1,363 | 466 | 34.2% | -10.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 20.0pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 20.0pp

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 1,178 | 669 | 56.8% | +12.4pp |
| SMALL_<0.18% | 1,610 | 569 | 35.3% | -9.1pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 21.4pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 21.4pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 1,059 | 608 | 57.4% | +13.0pp |
| SMALL_<0.20% | 1,729 | 630 | 36.4% | -8.0pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 21.0pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 21.0pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 558 | 180 | 32.3% | -12.1pp |
| Q2 | 557 | 187 | 33.6% | -10.8pp |
| Q3 | 558 | 231 | 41.4% | -3.0pp |
| Q4 | 557 | 300 | 53.9% | +9.5pp |
| Q5_Largest | 558 | 340 | 60.9% | +16.5pp |

- **Test Type:** spearman
- **P-value:** 0.0000
- **Effect Size:** 28.7pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - larger candle range correlates with higher win rate (r=1.000)

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 119 | 61 | 51.3% | +6.9pp |
| MEDIUM | 247 | 103 | 41.7% | -2.7pp |
| SMALL | 297 | 111 | 37.4% | -7.0pp |
| VERY_LARGE | 1,059 | 608 | 57.4% | +13.0pp |
| VERY_SMALL | 1,066 | 355 | 33.3% | -11.1pp |

- **Test Type:** spearman
- **P-value:** 0.0000
- **Effect Size:** 24.1pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - larger range category correlates with higher win rate (r=1.000)

### By Direction

#### LONG

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 546 | 172 | 31.5% | -11.8pp |
| NORMAL | 831 | 424 | 51.0% | +7.7pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 19.5pp
- **Confidence:** HIGH
- **Verdict:** SKIP FILTER VALIDATED - Absorption zone (31.5% WR) underperforms normal (51.0% WR). Effect: 19.5pp

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 831 | 424 | 51.0% | +7.7pp |
| SMALL_<0.12% | 546 | 172 | 31.5% | -11.8pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 19.5pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 19.5pp

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 690 | 372 | 53.9% | +10.6pp |
| SMALL_<0.15% | 687 | 224 | 32.6% | -10.7pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 21.3pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 21.3pp

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 564 | 321 | 56.9% | +13.6pp |
| SMALL_<0.18% | 813 | 275 | 33.8% | -9.5pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 23.1pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 23.1pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 510 | 296 | 58.0% | +14.8pp |
| SMALL_<0.20% | 867 | 300 | 34.6% | -8.7pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 23.4pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 23.4pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 276 | 89 | 32.2% | -11.0pp |
| Q2 | 275 | 85 | 30.9% | -12.4pp |
| Q3 | 275 | 105 | 38.2% | -5.1pp |
| Q4 | 276 | 146 | 52.9% | +9.6pp |
| Q5_Largest | 275 | 171 | 62.2% | +18.9pp |

- **Test Type:** spearman
- **P-value:** 0.0374
- **Effect Size:** 29.9pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - larger candle range correlates with higher win rate (r=0.900)

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 54 | 25 | 46.3% | +3.0pp |
| MEDIUM | 126 | 51 | 40.5% | -2.8pp |
| SMALL | 141 | 52 | 36.9% | -6.4pp |
| VERY_LARGE | 510 | 296 | 58.0% | +14.8pp |
| VERY_SMALL | 546 | 172 | 31.5% | -11.8pp |

- **Test Type:** spearman
- **P-value:** 0.0000
- **Effect Size:** 26.5pp
- **Confidence:** MEDIUM
- **Verdict:** EDGE DETECTED - larger range category correlates with higher win rate (r=1.000)

#### SHORT

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 520 | 183 | 35.2% | -10.3pp |
| NORMAL | 891 | 459 | 51.5% | +6.0pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 16.3pp
- **Confidence:** HIGH
- **Verdict:** SKIP FILTER VALIDATED - Absorption zone (35.2% WR) underperforms normal (51.5% WR). Effect: 16.3pp

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 891 | 459 | 51.5% | +6.0pp |
| SMALL_<0.12% | 520 | 183 | 35.2% | -10.3pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 16.3pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 16.3pp

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 735 | 400 | 54.4% | +8.9pp |
| SMALL_<0.15% | 676 | 242 | 35.8% | -9.7pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 18.6pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 18.6pp

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 614 | 348 | 56.7% | +11.2pp |
| SMALL_<0.18% | 797 | 294 | 36.9% | -8.6pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 19.8pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 19.8pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 549 | 312 | 56.8% | +11.3pp |
| SMALL_<0.20% | 862 | 330 | 38.3% | -7.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 18.5pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 18.5pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 283 | 97 | 34.3% | -11.2pp |
| Q2 | 282 | 100 | 35.5% | -10.0pp |
| Q3 | 282 | 124 | 44.0% | -1.5pp |
| Q4 | 282 | 155 | 55.0% | +9.5pp |
| Q5_Largest | 282 | 166 | 58.9% | +13.4pp |

- **Test Type:** spearman
- **P-value:** 0.0000
- **Effect Size:** 24.6pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - larger candle range correlates with higher win rate (r=1.000)

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 65 | 36 | 55.4% | +9.9pp |
| MEDIUM | 121 | 52 | 43.0% | -2.5pp |
| SMALL | 156 | 59 | 37.8% | -7.7pp |
| VERY_LARGE | 549 | 312 | 56.8% | +11.3pp |
| VERY_SMALL | 520 | 183 | 35.2% | -10.3pp |

- **Test Type:** spearman
- **P-value:** 0.0000
- **Effect Size:** 21.6pp
- **Confidence:** MEDIUM
- **Verdict:** EDGE DETECTED - larger range category correlates with higher win rate (r=1.000)

### By Trade Type

#### CONTINUATION (Combined)

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 72 | 25 | 34.7% | -8.4pp |
| NORMAL | 195 | 90 | 46.1% | +3.1pp |

- **Test Type:** chi_square
- **P-value:** 0.1248
- **Effect Size:** 11.4pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.1248)

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 195 | 90 | 46.1% | +3.1pp |
| SMALL_<0.12% | 72 | 25 | 34.7% | -8.4pp |

- **Test Type:** chi_square
- **P-value:** 0.1248
- **Effect Size:** 11.4pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.1248)

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 162 | 77 | 47.5% | +4.5pp |
| SMALL_<0.15% | 105 | 38 | 36.2% | -6.9pp |

- **Test Type:** chi_square
- **P-value:** 0.0889
- **Effect Size:** 11.3pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.0889)

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 135 | 69 | 51.1% | +8.0pp |
| SMALL_<0.18% | 132 | 46 | 34.9% | -8.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0105
- **Effect Size:** 16.3pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 16.3pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 126 | 66 | 52.4% | +9.3pp |
| SMALL_<0.20% | 141 | 49 | 34.8% | -8.3pp |

- **Test Type:** chi_square
- **P-value:** 0.0054
- **Effect Size:** 17.6pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 17.6pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 54 | 20 | 37.0% | -6.0pp |
| Q2 | 54 | 20 | 37.0% | -6.0pp |
| Q3 | 52 | 16 | 30.8% | -12.3pp |
| Q4 | 53 | 27 | 50.9% | +7.9pp |
| Q5_Largest | 54 | 32 | 59.3% | +16.2pp |

- **Test Type:** spearman
- **P-value:** 0.2189
- **Effect Size:** 22.2pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.2189)

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 9 | 3 | 33.3% | -9.7pp |
| MEDIUM | 27 | 8 | 29.6% | -13.4pp |
| SMALL | 33 | 13 | 39.4% | -3.7pp |
| VERY_LARGE | 126 | 66 | 52.4% | +9.3pp |
| VERY_SMALL | 72 | 25 | 34.7% | -8.4pp |

- **Test Type:** spearman
- **P-value:** 0.7471
- **Effect Size:** 17.7pp
- **Confidence:** LOW
- **Verdict:** INSUFFICIENT DATA - Need more trades for reliable conclusion

#### REJECTION (Combined)

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 994 | 330 | 33.2% | -11.3pp |
| NORMAL | 1,527 | 793 | 51.9% | +7.4pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 18.7pp
- **Confidence:** HIGH
- **Verdict:** SKIP FILTER VALIDATED - Absorption zone (33.2% WR) underperforms normal (51.9% WR). Effect: 18.7pp

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 1,527 | 793 | 51.9% | +7.4pp |
| SMALL_<0.12% | 994 | 330 | 33.2% | -11.3pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 18.7pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 18.7pp

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 1,263 | 695 | 55.0% | +10.5pp |
| SMALL_<0.15% | 1,258 | 428 | 34.0% | -10.5pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 21.0pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 21.0pp

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 1,043 | 600 | 57.5% | +13.0pp |
| SMALL_<0.18% | 1,478 | 523 | 35.4% | -9.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 22.1pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 22.1pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 933 | 542 | 58.1% | +13.5pp |
| SMALL_<0.20% | 1,588 | 581 | 36.6% | -8.0pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 21.5pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 21.5pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 505 | 161 | 31.9% | -12.7pp |
| Q2 | 504 | 173 | 34.3% | -10.2pp |
| Q3 | 504 | 206 | 40.9% | -3.7pp |
| Q4 | 504 | 274 | 54.4% | +9.8pp |
| Q5_Largest | 504 | 309 | 61.3% | +16.8pp |

- **Test Type:** spearman
- **P-value:** 0.0000
- **Effect Size:** 29.4pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - larger candle range correlates with higher win rate (r=1.000)

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 110 | 58 | 52.7% | +8.2pp |
| MEDIUM | 220 | 95 | 43.2% | -1.4pp |
| SMALL | 264 | 98 | 37.1% | -7.4pp |
| VERY_LARGE | 933 | 542 | 58.1% | +13.5pp |
| VERY_SMALL | 994 | 330 | 33.2% | -11.3pp |

- **Test Type:** spearman
- **P-value:** 0.0000
- **Effect Size:** 24.9pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - larger range category correlates with higher win rate (r=1.000)

### By Model - Continuation

#### EPCH1 (Primary Cont.)

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 34 | 13 | 38.2% | -2.6pp |
| NORMAL | 113 | 47 | 41.6% | +0.8pp |

- **Test Type:** chi_square
- **P-value:** 0.8806
- **Effect Size:** 3.4pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.8806)

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 113 | 47 | 41.6% | +0.8pp |
| SMALL_<0.12% | 34 | 13 | 38.2% | -2.6pp |

- **Test Type:** chi_square
- **P-value:** 0.8806
- **Effect Size:** 3.4pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.8806)

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 94 | 40 | 42.5% | +1.7pp |
| SMALL_<0.15% | 53 | 20 | 37.7% | -3.1pp |

- **Test Type:** chi_square
- **P-value:** 0.6922
- **Effect Size:** 4.8pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.6922)

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 78 | 34 | 43.6% | +2.8pp |
| SMALL_<0.18% | 69 | 26 | 37.7% | -3.1pp |

- **Test Type:** chi_square
- **P-value:** 0.5760
- **Effect Size:** 5.9pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.5760)

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 72 | 34 | 47.2% | +6.4pp |
| SMALL_<0.20% | 75 | 26 | 34.7% | -6.1pp |

- **Test Type:** chi_square
- **P-value:** 0.1674
- **Effect Size:** 12.5pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.1674)

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 30 | 11 | 36.7% | -4.1pp |
| Q2 | 29 | 10 | 34.5% | -6.3pp |
| Q3 | 29 | 9 | 31.0% | -9.8pp |
| Q4 | 29 | 12 | 41.4% | +0.6pp |
| Q5_Largest | 30 | 18 | 60.0% | +19.2pp |

- **Test Type:** spearman
- **P-value:** 0.2848
- **Effect Size:** 23.3pp
- **Confidence:** LOW
- **Verdict:** INSUFFICIENT DATA - Need more trades for reliable conclusion

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 6 | 0 | 0.0% | -40.8pp |
| MEDIUM | 16 | 6 | 37.5% | -3.3pp |
| SMALL | 19 | 7 | 36.8% | -4.0pp |
| VERY_LARGE | 72 | 34 | 47.2% | +6.4pp |
| VERY_SMALL | 34 | 13 | 38.2% | -2.6pp |

- **Test Type:** spearman
- **P-value:** 0.8729
- **Effect Size:** 9.0pp
- **Confidence:** LOW
- **Verdict:** INSUFFICIENT DATA - Need more trades for reliable conclusion

#### EPCH3 (Secondary Cont.)

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 38 | 12 | 31.6% | -14.3pp |
| NORMAL | 82 | 43 | 52.4% | +6.6pp |

- **Test Type:** chi_square
- **P-value:** 0.0528
- **Effect Size:** 20.9pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.0528)

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 82 | 43 | 52.4% | +6.6pp |
| SMALL_<0.12% | 38 | 12 | 31.6% | -14.3pp |

- **Test Type:** chi_square
- **P-value:** 0.0528
- **Effect Size:** 20.9pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.0528)

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 68 | 37 | 54.4% | +8.6pp |
| SMALL_<0.15% | 52 | 18 | 34.6% | -11.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0486
- **Effect Size:** 19.8pp
- **Confidence:** MEDIUM
- **Verdict:** EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 19.8pp

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 57 | 35 | 61.4% | +15.6pp |
| SMALL_<0.18% | 63 | 20 | 31.8% | -14.1pp |

- **Test Type:** chi_square
- **P-value:** 0.0021
- **Effect Size:** 29.6pp
- **Confidence:** MEDIUM
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 29.6pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 54 | 32 | 59.3% | +13.4pp |
| SMALL_<0.20% | 66 | 23 | 34.9% | -11.0pp |

- **Test Type:** chi_square
- **P-value:** 0.0129
- **Effect Size:** 24.4pp
- **Confidence:** MEDIUM
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 24.4pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 24 | 9 | 37.5% | -8.3pp |
| Q2 | 24 | 7 | 29.2% | -16.7pp |
| Q3 | 24 | 9 | 37.5% | -8.3pp |
| Q4 | 24 | 15 | 62.5% | +16.7pp |
| Q5_Largest | 24 | 15 | 62.5% | +16.7pp |

- **Test Type:** spearman
- **P-value:** 0.1114
- **Effect Size:** 25.0pp
- **Confidence:** LOW
- **Verdict:** INSUFFICIENT DATA - Need more trades for reliable conclusion

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 3 | 3 | 100.0% | +54.2pp |
| MEDIUM | 11 | 2 | 18.2% | -27.7pp |
| SMALL | 14 | 6 | 42.9% | -3.0pp |
| VERY_LARGE | 54 | 32 | 59.3% | +13.4pp |
| VERY_SMALL | 38 | 12 | 31.6% | -14.3pp |

- **Test Type:** spearman
- **P-value:** 0.2848
- **Effect Size:** 27.7pp
- **Confidence:** LOW
- **Verdict:** INSUFFICIENT DATA - Need more trades for reliable conclusion

### By Model - Rejection

#### EPCH2 (Primary Rej.)

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 560 | 192 | 34.3% | -9.2pp |
| NORMAL | 853 | 423 | 49.6% | +6.1pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 15.3pp
- **Confidence:** HIGH
- **Verdict:** SKIP FILTER VALIDATED - Absorption zone (34.3% WR) underperforms normal (49.6% WR). Effect: 15.3pp

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 853 | 423 | 49.6% | +6.1pp |
| SMALL_<0.12% | 560 | 192 | 34.3% | -9.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 15.3pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 15.3pp

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 700 | 370 | 52.9% | +9.3pp |
| SMALL_<0.15% | 713 | 245 | 34.4% | -9.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 18.5pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 18.5pp

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 571 | 316 | 55.3% | +11.8pp |
| SMALL_<0.18% | 842 | 299 | 35.5% | -8.0pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 19.8pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 19.8pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 506 | 286 | 56.5% | +13.0pp |
| SMALL_<0.20% | 907 | 329 | 36.3% | -7.3pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 20.2pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 20.2pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 283 | 90 | 31.8% | -11.7pp |
| Q2 | 282 | 103 | 36.5% | -7.0pp |
| Q3 | 283 | 107 | 37.8% | -5.7pp |
| Q4 | 282 | 145 | 51.4% | +7.9pp |
| Q5_Largest | 283 | 170 | 60.1% | +16.5pp |

- **Test Type:** spearman
- **P-value:** 0.0000
- **Effect Size:** 28.3pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - larger candle range correlates with higher win rate (r=1.000)

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 65 | 30 | 46.1% | +2.6pp |
| MEDIUM | 129 | 54 | 41.9% | -1.7pp |
| SMALL | 153 | 53 | 34.6% | -8.9pp |
| VERY_LARGE | 506 | 286 | 56.5% | +13.0pp |
| VERY_SMALL | 560 | 192 | 34.3% | -9.2pp |

- **Test Type:** spearman
- **P-value:** 0.0000
- **Effect Size:** 22.2pp
- **Confidence:** MEDIUM
- **Verdict:** EDGE DETECTED - larger range category correlates with higher win rate (r=1.000)

#### EPCH4 (Secondary Rej.)

**Absorption Zone (<0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABSORPTION | 434 | 138 | 31.8% | -14.0pp |
| NORMAL | 674 | 370 | 54.9% | +9.1pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 23.1pp
- **Confidence:** HIGH
- **Verdict:** SKIP FILTER VALIDATED - Absorption zone (31.8% WR) underperforms normal (54.9% WR). Effect: 23.1pp

**Range Threshold (0.12%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.12% | 674 | 370 | 54.9% | +9.1pp |
| SMALL_<0.12% | 434 | 138 | 31.8% | -14.0pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 23.1pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 23.1pp

**Range Threshold (0.15%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.15% | 563 | 325 | 57.7% | +11.9pp |
| SMALL_<0.15% | 545 | 183 | 33.6% | -12.3pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 24.1pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 24.1pp

**Range Threshold (0.18%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.18% | 472 | 284 | 60.2% | +14.3pp |
| SMALL_<0.18% | 636 | 224 | 35.2% | -10.6pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 25.0pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 25.0pp

**Range Threshold (0.2%)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE_>=0.20% | 427 | 256 | 60.0% | +14.1pp |
| SMALL_<0.20% | 681 | 252 | 37.0% | -8.8pp |

- **Test Type:** chi_square
- **P-value:** 0.0000
- **Effect Size:** 23.0pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 23.0pp

**Range Magnitude (Quintiles)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Smallest | 222 | 70 | 31.5% | -14.3pp |
| Q2 | 221 | 70 | 31.7% | -14.2pp |
| Q3 | 222 | 102 | 46.0% | +0.1pp |
| Q4 | 221 | 126 | 57.0% | +11.2pp |
| Q5_Largest | 222 | 140 | 63.1% | +17.2pp |

- **Test Type:** spearman
- **P-value:** 0.0000
- **Effect Size:** 31.5pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - larger candle range correlates with higher win rate (r=1.000)

**Range Category (5-tier)**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| LARGE | 45 | 28 | 62.2% | +16.4pp |
| MEDIUM | 91 | 41 | 45.0% | -0.8pp |
| SMALL | 111 | 45 | 40.5% | -5.3pp |
| VERY_LARGE | 427 | 256 | 60.0% | +14.1pp |
| VERY_SMALL | 434 | 138 | 31.8% | -14.0pp |

- **Test Type:** spearman
- **P-value:** 0.0374
- **Effect Size:** 28.2pp
- **Confidence:** MEDIUM
- **Verdict:** EDGE DETECTED - larger range category correlates with higher win rate (r=0.900)

---

## Recommendations

### Implement
1. **Absorption Zone (<0.12%) (ALL)**: SKIP FILTER VALIDATED - Absorption zone (33.3% WR) underperforms normal (51.3% WR). Effect: 18.0pp
1. **Range Threshold (0.12%) (ALL)**: EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 18.0pp
1. **Range Threshold (0.15%) (ALL)**: EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 20.0pp
1. **Range Threshold (0.18%) (ALL)**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 21.4pp
1. **Range Threshold (0.2%) (ALL)**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 21.0pp
1. **Range Magnitude (Quintiles) (ALL)**: EDGE DETECTED - larger candle range correlates with higher win rate (r=1.000)
1. **Range Category (5-tier) (ALL)**: EDGE DETECTED - larger range category correlates with higher win rate (r=1.000)
1. **Absorption Zone (<0.12%) (LONG)**: SKIP FILTER VALIDATED - Absorption zone (31.5% WR) underperforms normal (51.0% WR). Effect: 19.5pp
1. **Range Threshold (0.12%) (LONG)**: EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 19.5pp
1. **Range Threshold (0.15%) (LONG)**: EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 21.3pp
1. **Range Threshold (0.18%) (LONG)**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 23.1pp
1. **Range Threshold (0.2%) (LONG)**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 23.4pp
1. **Range Magnitude (Quintiles) (LONG)**: EDGE DETECTED - larger candle range correlates with higher win rate (r=0.900)
1. **Range Category (5-tier) (LONG)**: EDGE DETECTED - larger range category correlates with higher win rate (r=1.000)
1. **Absorption Zone (<0.12%) (SHORT)**: SKIP FILTER VALIDATED - Absorption zone (35.2% WR) underperforms normal (51.5% WR). Effect: 16.3pp
1. **Range Threshold (0.12%) (SHORT)**: EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 16.3pp
1. **Range Threshold (0.15%) (SHORT)**: EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 18.6pp
1. **Range Threshold (0.18%) (SHORT)**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 19.8pp
1. **Range Threshold (0.2%) (SHORT)**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 18.5pp
1. **Range Magnitude (Quintiles) (SHORT)**: EDGE DETECTED - larger candle range correlates with higher win rate (r=1.000)
1. **Range Category (5-tier) (SHORT)**: EDGE DETECTED - larger range category correlates with higher win rate (r=1.000)
1. **Range Threshold (0.18%) (CONTINUATION (Combined))**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 16.3pp
1. **Range Threshold (0.2%) (CONTINUATION (Combined))**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 17.6pp
1. **Absorption Zone (<0.12%) (REJECTION (Combined))**: SKIP FILTER VALIDATED - Absorption zone (33.2% WR) underperforms normal (51.9% WR). Effect: 18.7pp
1. **Range Threshold (0.12%) (REJECTION (Combined))**: EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 18.7pp
1. **Range Threshold (0.15%) (REJECTION (Combined))**: EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 21.0pp
1. **Range Threshold (0.18%) (REJECTION (Combined))**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 22.1pp
1. **Range Threshold (0.2%) (REJECTION (Combined))**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 21.5pp
1. **Range Magnitude (Quintiles) (REJECTION (Combined))**: EDGE DETECTED - larger candle range correlates with higher win rate (r=1.000)
1. **Range Category (5-tier) (REJECTION (Combined))**: EDGE DETECTED - larger range category correlates with higher win rate (r=1.000)
1. **Range Threshold (0.15%) (EPCH3 (Secondary Cont.))**: EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 19.8pp
1. **Range Threshold (0.18%) (EPCH3 (Secondary Cont.))**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 29.6pp
1. **Range Threshold (0.2%) (EPCH3 (Secondary Cont.))**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 24.4pp
1. **Absorption Zone (<0.12%) (EPCH2 (Primary Rej.))**: SKIP FILTER VALIDATED - Absorption zone (34.3% WR) underperforms normal (49.6% WR). Effect: 15.3pp
1. **Range Threshold (0.12%) (EPCH2 (Primary Rej.))**: EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 15.3pp
1. **Range Threshold (0.15%) (EPCH2 (Primary Rej.))**: EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 18.5pp
1. **Range Threshold (0.18%) (EPCH2 (Primary Rej.))**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 19.8pp
1. **Range Threshold (0.2%) (EPCH2 (Primary Rej.))**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 20.2pp
1. **Range Magnitude (Quintiles) (EPCH2 (Primary Rej.))**: EDGE DETECTED - larger candle range correlates with higher win rate (r=1.000)
1. **Range Category (5-tier) (EPCH2 (Primary Rej.))**: EDGE DETECTED - larger range category correlates with higher win rate (r=1.000)
1. **Absorption Zone (<0.12%) (EPCH4 (Secondary Rej.))**: SKIP FILTER VALIDATED - Absorption zone (31.8% WR) underperforms normal (54.9% WR). Effect: 23.1pp
1. **Range Threshold (0.12%) (EPCH4 (Secondary Rej.))**: EDGE DETECTED - Range < 0.12% = SKIP (absorption zone). Effect: 23.1pp
1. **Range Threshold (0.15%) (EPCH4 (Secondary Rej.))**: EDGE DETECTED - Range >= 0.15% = TAKE. Effect: 24.1pp
1. **Range Threshold (0.18%) (EPCH4 (Secondary Rej.))**: EDGE DETECTED - Range >= 0.18% = TAKE. Effect: 25.0pp
1. **Range Threshold (0.2%) (EPCH4 (Secondary Rej.))**: EDGE DETECTED - Range >= 0.2% = TAKE. Effect: 23.0pp
1. **Range Magnitude (Quintiles) (EPCH4 (Secondary Rej.))**: EDGE DETECTED - larger candle range correlates with higher win rate (r=1.000)
1. **Range Category (5-tier) (EPCH4 (Secondary Rej.))**: EDGE DETECTED - larger range category correlates with higher win rate (r=0.900)

### No Action Needed
- Absorption Zone (<0.12%) (CONTINUATION (Combined)): NO EDGE - Not statistically significant (p=0.1248)
- Range Threshold (0.12%) (CONTINUATION (Combined)): NO EDGE - Not statistically significant (p=0.1248)
- Range Threshold (0.15%) (CONTINUATION (Combined)): NO EDGE - Not statistically significant (p=0.0889)
- Range Magnitude (Quintiles) (CONTINUATION (Combined)): NO EDGE - Not statistically significant (p=0.2189)
- Absorption Zone (<0.12%) (EPCH1 (Primary Cont.)): NO EDGE - Not statistically significant (p=0.8806)
- Range Threshold (0.12%) (EPCH1 (Primary Cont.)): NO EDGE - Not statistically significant (p=0.8806)
- Range Threshold (0.15%) (EPCH1 (Primary Cont.)): NO EDGE - Not statistically significant (p=0.6922)
- Range Threshold (0.18%) (EPCH1 (Primary Cont.)): NO EDGE - Not statistically significant (p=0.5760)
- Range Threshold (0.2%) (EPCH1 (Primary Cont.)): NO EDGE - Not statistically significant (p=0.1674)
- Absorption Zone (<0.12%) (EPCH3 (Secondary Cont.)): NO EDGE - Not statistically significant (p=0.0528)
- Range Threshold (0.12%) (EPCH3 (Secondary Cont.)): NO EDGE - Not statistically significant (p=0.0528)

### Needs More Data
- Range Category (5-tier) (CONTINUATION (Combined)): Insufficient sample size for conclusion
- Range Magnitude (Quintiles) (EPCH1 (Primary Cont.)): Insufficient sample size for conclusion
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

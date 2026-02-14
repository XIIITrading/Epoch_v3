# VWAP Edge Analysis Report (CALC-011)

**Generated:** 2026-01-15 14:20:10
**Data Range:** 2025-12-15 to 2026-01-14
**Total Trades:** 2,394
**Stop Type:** zone_buffer
**Baseline Win Rate:** 43.9%

---

## Executive Summary

| Test | Segment | Edge Detected | Confidence | Effect Size |
|------|---------|---------------|------------|-------------|
| VWAP Side (Above/Below) | ALL | NO | HIGH | 4.0pp |
| VWAP Alignment | ALL | NO | HIGH | 3.2pp |
| VWAP Distance (Quintiles) | ALL | NO | HIGH | 3.5pp |
| VWAP Side (Above/Below) | CONTINUATION | NO | HIGH | 3.1pp |
| VWAP Alignment | CONTINUATION | NO | MEDIUM | 2.4pp |
| VWAP Distance (Quintiles) | CONTINUATION | NO | MEDIUM | 22.7pp |
| VWAP Side (Above/Below) | REJECTION | YES | HIGH | 4.7pp |
| VWAP Alignment | REJECTION | NO | HIGH | 3.6pp |
| VWAP Distance (Quintiles) | REJECTION | NO | HIGH | 1.9pp |
| VWAP Side (Above/Below) | LONG | NO | HIGH | 0.6pp |
| VWAP Alignment | LONG | NO | HIGH | 0.6pp |
| VWAP Distance (Quintiles) | LONG | NO | HIGH | 3.2pp |
| VWAP Side (Above/Below) | SHORT | YES | HIGH | 7.1pp |
| VWAP Alignment | SHORT | YES | HIGH | 7.1pp |
| VWAP Distance (Quintiles) | SHORT | NO | HIGH | 3.8pp |

**Key Findings:**
- VWAP Side (Above/Below) (REJECTION): 4.7pp win rate advantage (p=0.0305)
- VWAP Side (Above/Below) (SHORT): 7.1pp win rate advantage (p=0.0165)
- VWAP Alignment (SHORT): 7.1pp win rate advantage (p=0.0165)

---

## Detailed Results

### VWAP Side (Above/Below)

**Segment: ALL**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABOVE | 1,265 | 579 | 45.8% | +1.9pp |
| BELOW | 1,129 | 472 | 41.8% | -2.1pp |

- **Test Type:** chi_square
- **P-value:** 0.0562
- **Effect Size:** 4.0pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.0562)

**Segment: CONTINUATION**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABOVE | 123 | 52 | 42.3% | -1.4pp |
| BELOW | 108 | 49 | 45.4% | +1.6pp |

- **Test Type:** chi_square
- **P-value:** 0.7338
- **Effect Size:** 3.1pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.7338)

**Segment: REJECTION**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABOVE | 1,142 | 527 | 46.1% | +2.2pp |
| BELOW | 1,021 | 423 | 41.4% | -2.5pp |

- **Test Type:** chi_square
- **P-value:** 0.0305
- **Effect Size:** 4.7pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Implement filter (p=0.0305, effect=4.7pp)

**Segment: LONG**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABOVE | 737 | 329 | 44.6% | +0.2pp |
| BELOW | 468 | 206 | 44.0% | -0.4pp |

- **Test Type:** chi_square
- **P-value:** 0.8786
- **Effect Size:** 0.6pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.8786)

**Segment: SHORT**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ABOVE | 528 | 250 | 47.4% | +4.0pp |
| BELOW | 661 | 266 | 40.2% | -3.2pp |

- **Test Type:** chi_square
- **P-value:** 0.0165
- **Effect Size:** 7.1pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Implement filter (p=0.0165, effect=7.1pp)

### VWAP Alignment

**Segment: ALL**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ALIGNED | 1,398 | 595 | 42.6% | -1.3pp |
| MISALIGNED | 996 | 456 | 45.8% | +1.9pp |

- **Test Type:** chi_square
- **P-value:** 0.1275
- **Effect Size:** 3.2pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.1275)

**Segment: CONTINUATION**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ALIGNED | 195 | 86 | 44.1% | +0.4pp |
| MISALIGNED | 36 | 15 | 41.7% | -2.1pp |

- **Test Type:** chi_square
- **P-value:** 0.9300
- **Effect Size:** 2.4pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.9300)

**Segment: REJECTION**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ALIGNED | 1,203 | 509 | 42.3% | -1.6pp |
| MISALIGNED | 960 | 441 | 45.9% | +2.0pp |

- **Test Type:** chi_square
- **P-value:** 0.1000
- **Effect Size:** 3.6pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.1000)

**Segment: LONG**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ALIGNED | 737 | 329 | 44.6% | +0.2pp |
| MISALIGNED | 468 | 206 | 44.0% | -0.4pp |

- **Test Type:** chi_square
- **P-value:** 0.8786
- **Effect Size:** 0.6pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.8786)

**Segment: SHORT**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| ALIGNED | 661 | 266 | 40.2% | -3.2pp |
| MISALIGNED | 528 | 250 | 47.4% | +4.0pp |

- **Test Type:** chi_square
- **P-value:** 0.0165
- **Effect Size:** 7.1pp
- **Confidence:** HIGH
- **Verdict:** EDGE DETECTED - Implement filter (p=0.0165, effect=7.1pp)

### VWAP Distance (Quintiles)

**Segment: ALL**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Closest | 479 | 231 | 48.2% | +4.3pp |
| Q2 | 479 | 175 | 36.5% | -7.4pp |
| Q3 | 478 | 195 | 40.8% | -3.1pp |
| Q4 | 479 | 202 | 42.2% | -1.7pp |
| Q5_Farthest | 479 | 248 | 51.8% | +7.9pp |

- **Test Type:** spearman
- **P-value:** 0.5046
- **Effect Size:** 3.5pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.5046)

**Segment: CONTINUATION**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Closest | 37 | 11 | 29.7% | -14.0pp |
| Q2 | 45 | 22 | 48.9% | +5.2pp |
| Q3 | 39 | 15 | 38.5% | -5.3pp |
| Q4 | 47 | 20 | 42.5% | -1.2pp |
| Q5_Farthest | 63 | 33 | 52.4% | +8.7pp |

- **Test Type:** spearman
- **P-value:** 0.1881
- **Effect Size:** 22.7pp
- **Confidence:** MEDIUM
- **Verdict:** NO EDGE - Not statistically significant (p=0.1881)

**Segment: REJECTION**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Closest | 442 | 220 | 49.8% | +5.8pp |
| Q2 | 434 | 153 | 35.2% | -8.7pp |
| Q3 | 439 | 180 | 41.0% | -2.9pp |
| Q4 | 432 | 182 | 42.1% | -1.8pp |
| Q5_Farthest | 416 | 215 | 51.7% | +7.8pp |

- **Test Type:** spearman
- **P-value:** 0.5046
- **Effect Size:** 1.9pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.5046)

**Segment: LONG**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Closest | 186 | 90 | 48.4% | +4.0pp |
| Q2 | 245 | 93 | 38.0% | -6.4pp |
| Q3 | 268 | 113 | 42.2% | -2.2pp |
| Q4 | 285 | 125 | 43.9% | -0.5pp |
| Q5_Farthest | 221 | 114 | 51.6% | +7.2pp |

- **Test Type:** spearman
- **P-value:** 0.5046
- **Effect Size:** 3.2pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.5046)

**Segment: SHORT**

| Group | Trades | Wins | Win Rate | vs Baseline |
|-------|--------|------|----------|-------------|
| Q1_Closest | 293 | 141 | 48.1% | +4.7pp |
| Q2 | 234 | 82 | 35.0% | -8.4pp |
| Q3 | 210 | 82 | 39.0% | -4.3pp |
| Q4 | 194 | 77 | 39.7% | -3.7pp |
| Q5_Farthest | 258 | 134 | 51.9% | +8.5pp |

- **Test Type:** spearman
- **P-value:** 0.5046
- **Effect Size:** 3.8pp
- **Confidence:** HIGH
- **Verdict:** NO EDGE - Not statistically significant (p=0.5046)

---

## Recommendations

### Implement
1. **VWAP Side (Above/Below) (REJECTION)**: EDGE DETECTED - Implement filter (p=0.0305, effect=4.7pp)
1. **VWAP Side (Above/Below) (SHORT)**: EDGE DETECTED - Implement filter (p=0.0165, effect=7.1pp)
1. **VWAP Alignment (SHORT)**: EDGE DETECTED - Implement filter (p=0.0165, effect=7.1pp)

### No Action Needed
- VWAP Side (Above/Below) (ALL): NO EDGE - Not statistically significant (p=0.0562)
- VWAP Alignment (ALL): NO EDGE - Not statistically significant (p=0.1275)
- VWAP Distance (Quintiles) (ALL): NO EDGE - Not statistically significant (p=0.5046)
- VWAP Side (Above/Below) (CONTINUATION): NO EDGE - Not statistically significant (p=0.7338)
- VWAP Alignment (CONTINUATION): NO EDGE - Not statistically significant (p=0.9300)
- VWAP Distance (Quintiles) (CONTINUATION): NO EDGE - Not statistically significant (p=0.1881)
- VWAP Alignment (REJECTION): NO EDGE - Not statistically significant (p=0.1000)
- VWAP Distance (Quintiles) (REJECTION): NO EDGE - Not statistically significant (p=0.5046)
- VWAP Side (Above/Below) (LONG): NO EDGE - Not statistically significant (p=0.8786)
- VWAP Alignment (LONG): NO EDGE - Not statistically significant (p=0.8786)
- VWAP Distance (Quintiles) (LONG): NO EDGE - Not statistically significant (p=0.5046)
- VWAP Distance (Quintiles) (SHORT): NO EDGE - Not statistically significant (p=0.5046)

---

## Statistical Notes

- **Significance Level:** alpha = 0.05
- **Effect Size Threshold:** 3.0pp minimum for practical significance
- **Confidence Levels:**
  - HIGH: >=100 trades per group
  - MEDIUM: >=30 trades per group
  - LOW: <30 trades per group (insufficient)

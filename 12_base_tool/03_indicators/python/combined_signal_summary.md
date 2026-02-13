# Combined Indicator Signal Summary

## Overview

This document provides actionable trading signals by combining all validated indicators from the CALC-011 Edge Testing Framework. Analysis covers 4 core indicators tested across 2,788 trades from 2025-12-15 to 2026-01-16.

**Generated:** 2026-01-17
**Baseline Win Rate:** 44.4%

---

## Indicators Analyzed

| Indicator | Module | Primary Edge | Best For |
|-----------|--------|--------------|----------|
| **Bar Range** | `candle_range\` | 18-31pp | ALL trades (direction-agnostic) |
| **Volume ROC** | `volume_roc\` | 11-19pp | ALL trades (magnitude-based) |
| **Volume Delta** | `volume_delta\` | 13-21pp | LONG: magnitude, SHORT: sign |
| **CVD Slope** | `cvd_slope\` | 15-27pp | SHORT trades only |

---

## Direction-Specific Indicator Effectiveness

| Indicator | LONG Trades | SHORT Trades |
|-----------|-------------|--------------|
| **Bar Range** | Works equally (18-29pp) | Works equally (16-24pp) |
| **Vol ROC** | Works equally (11-19pp) | Works equally (11-19pp) |
| **Vol Delta** | Magnitude matters (Q4-Q5 = +20pp) | Sign matters (POSITIVE = +10-21pp) |
| **CVD Slope** | **NO EDGE** | **STRONG EDGE** (+15-27pp) |

### Key Finding: Direction Matters for Order Flow Indicators

- **Bar Range and Vol ROC** are direction-agnostic - use the same filters for LONG and SHORT
- **Vol Delta** requires different filters: LONG uses magnitude, SHORT uses sign/alignment
- **CVD Slope** is SHORT-only - provides no edge for LONG trades

---

## Signal Matrix by Direction × Trade Type

### LONG CONTINUATION (EPCH1 + EPCH3)

| Indicator | Ideal Signal | Expected WR | Effect | Status |
|-----------|--------------|-------------|--------|--------|
| **Bar Range** | >= 0.18% | 51-61% | +16-30pp | TAKE |
| **Vol ROC** | Q4-Q5 (High Volume) | ~50% | +5-7pp | TAKE |
| **Vol Delta** | Q4-Q5 Magnitude | 53-57% | +13-20pp | TAKE |
| **CVD Slope** | - | - | - | IGNORE |

**SKIP Filter:** Bar Range < 0.12% → 31.5% WR

**Recommended Logic:**
```
IF Bar Range >= 0.18% AND Vol Delta Q4-Q5:
    → TAKE (Expected WR: 55-60%)

IF Bar Range < 0.12%:
    → SKIP (Expected WR: 31.5%)
```

---

### SHORT CONTINUATION (EPCH1 + EPCH3)

| Indicator | Ideal Signal | Expected WR | Effect | Status |
|-----------|--------------|-------------|--------|--------|
| **Bar Range** | >= 0.15% | 54% | +18pp | TAKE |
| **Vol ROC** | Q4-Q5 (High Volume) | ~50% | +5-7pp | TAKE |
| **Vol Delta** | POSITIVE delta | 50.7% | +10.7pp | TAKE |
| **CVD Slope** | POSITIVE slope | 53% | +15pp | TAKE |

**SKIP Filter:** Bar Range < 0.12% → 35.2% WR

**Recommended Logic:**
```
IF Bar Range >= 0.15% AND CVD Slope POSITIVE:
    → TAKE (Expected WR: 53-55%)

IF Bar Range >= 0.15% AND Vol Delta POSITIVE:
    → TAKE (Expected WR: 51-54%)

IF Bar Range < 0.12%:
    → SKIP (Expected WR: 35.2%)
```

---

### LONG REJECTION (EPCH2 + EPCH4)

| Indicator | Ideal Signal | Expected WR | Effect | Status |
|-----------|--------------|-------------|--------|--------|
| **Bar Range** | >= 0.15% | 55% | +21pp | TAKE |
| **Vol ROC** | Q4-Q5 (High Volume) | ~51% | +6-8pp | TAKE |
| **Vol Delta** | Q4-Q5 Magnitude | 50-58% | +14.9pp | TAKE |
| **CVD Slope** | - | - | - | IGNORE |

**SKIP Filter:** Bar Range < 0.12% → 33.2% WR

**Recommended Logic:**
```
IF Bar Range >= 0.15% AND Vol Delta Q4-Q5:
    → TAKE (Expected WR: 55-58%)

IF Bar Range >= 0.20%:
    → STRONG TAKE (Expected WR: 58%)

IF Bar Range < 0.12%:
    → SKIP (Expected WR: 33.2%)
```

---

### SHORT REJECTION (EPCH2 + EPCH4)

| Indicator | Ideal Signal | Expected WR | Effect | Status |
|-----------|--------------|-------------|--------|--------|
| **Bar Range** | >= 0.15% | 55% | +21pp | TAKE |
| **Vol ROC** | Q4-Q5 (High Volume) | ~51% | +6-8pp | TAKE |
| **Vol Delta** | POSITIVE delta | 56% | +21pp | TAKE |
| **CVD Slope** | POSITIVE / EXTREME_POS | 53-62% | +15-27pp | STRONG TAKE |

**SKIP Filter:** Bar Range < 0.12% → 33.2% WR

**Recommended Logic:**
```
IF Bar Range >= 0.15% AND CVD Slope EXTREME_POS:
    → STRONG TAKE (Expected WR: 60-62%)

IF Bar Range >= 0.15% AND CVD Slope POSITIVE:
    → TAKE (Expected WR: 55-58%)

IF Bar Range >= 0.15% AND Vol Delta POSITIVE:
    → TAKE (Expected WR: 55-56%)

IF Bar Range < 0.12%:
    → SKIP (Expected WR: 33.2%)
```

---

## Simplified Decision Tree

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ENTRY DECISION TREE                          │
└─────────────────────────────────────────────────────────────────────┘

STEP 1: CHECK ABSORPTION ZONE (Universal SKIP)
├── IF Bar Range < 0.12%
│   └── SKIP TRADE (31-35% WR regardless of other signals)
│
STEP 2: CHECK DIRECTION
├── IF LONG:
│   ├── Bar Range >= 0.15%        → +1 point
│   ├── Bar Range >= 0.20%        → +1 bonus point
│   ├── Vol ROC Q4-Q5             → +1 point
│   ├── Vol Delta Q4-Q5 magnitude → +1 point
│   └── CVD Slope                 → IGNORE (no edge)
│
├── IF SHORT:
│   ├── Bar Range >= 0.15%        → +1 point
│   ├── Bar Range >= 0.20%        → +1 bonus point
│   ├── Vol ROC Q4-Q5             → +1 point
│   ├── Vol Delta POSITIVE        → +1 point
│   ├── CVD Slope POSITIVE        → +1 point
│   └── CVD Slope EXTREME_POS     → +1 bonus point (62% WR)
│
STEP 3: SCORE THRESHOLD
├── REJECTION trades: Take if score >= 3
└── CONTINUATION trades: Take if score >= 2
```

---

## Paradoxical Findings (Validated)

### The MISALIGNED Advantage

Both Volume Delta and CVD Slope show a consistent paradox: entering AGAINST recent order flow produces better results than entering WITH it.

| Indicator | Direction | Finding | Effect |
|-----------|-----------|---------|--------|
| **Vol Delta** | SHORT | POSITIVE delta wins (not NEGATIVE) | +10.7pp |
| **CVD Slope** | SHORT | POSITIVE slope wins (not NEGATIVE) | +15.3pp |
| **Vol Delta** | ALL | MISALIGNED outperforms ALIGNED | +6.5pp |
| **CVD Slope** | ALL | MISALIGNED outperforms ALIGNED | +6.9pp |

**Interpretation:** Entering against order flow momentum captures exhaustion/reversal points. When everyone is buying (positive delta/slope), SHORT trades win more - likely because the buying exhausts and reverses.

---

## Composite Signals

### Momentum Signal (TAKE)

**Definition:** High Volume + Large Range

| Component | Threshold |
|-----------|-----------|
| Volume (any indicator) | Q4-Q5 magnitude OR Vol ROC >= 30% |
| Bar Range | >= 0.15% (Rejection) or >= 0.18% (Continuation) |

**Result:** 55-60% WR depending on trade type

### Absorption Signal (SKIP)

**Definition:** High Volume + Small Range

| Component | Threshold |
|-----------|-----------|
| Volume (any indicator) | Q4-Q5 magnitude OR Vol ROC >= 30% |
| Bar Range | < 0.12% |

**Result:** 31-35% WR → ALWAYS SKIP

### Extreme Scenarios

| Scenario | Win Rate | Trades | Action |
|----------|----------|--------|--------|
| SHORT + Large Range + EXTREME_POS CVD | 62% | 140 | STRONG TAKE |
| SHORT + Momentum + POSITIVE delta | 56% | 400 | TAKE |
| LONG + Large Range + Q5 Vol Delta | 58% | 350 | TAKE |
| ANY + Absorption Zone | 33% | 600 | SKIP |
| SHORT + Absorption + BUYING_PRESSURE | 21% | 38 | STRONG SKIP |

---

## PyQt Implementation Recommendations

### Indicator Weights by Direction

#### LONG Trades

| Indicator | Weight | Condition | Notes |
|-----------|--------|-----------|-------|
| Bar Range | 2 | >= 0.15% | Strongest single indicator |
| Bar Range | 1 (bonus) | >= 0.20% | Additional point |
| Vol Delta Magnitude | 1 | Q4-Q5 | Works for LONG |
| Vol ROC Magnitude | 1 | Q4-Q5 | Works for LONG |
| CVD Slope | 0 | - | Do not score |

#### SHORT Trades

| Indicator | Weight | Condition | Notes |
|-----------|--------|-----------|-------|
| Bar Range | 2 | >= 0.15% | Strongest single indicator |
| Bar Range | 1 (bonus) | >= 0.20% | Additional point |
| Vol Delta Sign | 1 | POSITIVE | Paradoxical but validated |
| Vol ROC Magnitude | 1 | Q4-Q5 | Works for SHORT |
| CVD Slope Direction | 1 | POSITIVE | Strong SHORT signal |
| CVD Slope Category | 1 (bonus) | EXTREME_POS | 62% WR |

### Skip Filters (Mandatory)

| Filter | Condition | Action | Priority |
|--------|-----------|--------|----------|
| Absorption | Range < 0.12% | BLOCK trade | 1 (highest) |

---

## Summary Table

| Trade Type | Direction | Key Indicators | Take Threshold | Skip Threshold |
|------------|-----------|----------------|----------------|----------------|
| Continuation | LONG | Range, Vol Delta Mag | Range >= 0.18% | Range < 0.12% |
| Continuation | SHORT | Range, CVD Slope, Vol Delta Sign | Range >= 0.15% + POSITIVE slope | Range < 0.12% |
| Rejection | LONG | Range, Vol Delta Mag | Range >= 0.15% | Range < 0.12% |
| Rejection | SHORT | Range, CVD Slope, Vol Delta Sign | Range >= 0.15% + POSITIVE slope | Range < 0.12% |

---

## Data Sources

- **Trades Table:** 2,788 trades (2025-12-15 to 2026-01-16)
- **Indicator Data:** `m1_indicator_bars` table (prior M1 bar before entry)
- **Win Definition:** `stop_analysis` with `stop_type = 'zone_buffer'`
- **Statistical Tests:** Chi-square (p < 0.05), Spearman correlation
- **Confidence Level:** HIGH (>= 100 trades per group)

---

## Reference

- **Indicator Validation Pipeline:** `Indicator_Validation_Pipeline.md`
- **Volume Delta Module:** `volume_delta\volume_delta_edge.py`
- **Volume ROC Module:** `volume_roc\volume_roc_edge.py`
- **Candle Range Module:** `candle_range\candle_range_edge.py`
- **CVD Slope Module:** `cvd_slope\cvd_slope_edge.py`

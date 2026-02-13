# EPOCH Trading System: Indicator Decision Rubric
**Date**: January 20, 2026 | **Based on**: 1,594 analyzed trades | **Stop Type**: M5 ATR

---

## Executive Summary

**Core Finding**: Secondary zone trades dramatically outperform Primary zone trades. SHORT direction holds edge across most models except EPCH4 where LONG outperforms.

| Tier | Model + Direction | Win Rate | Avg R | Action |
|------|-------------------|----------|-------|--------|
| **A** | EPCH3_SHORT | 81.2% | 2.90R | Full size, aggressive |
| **A** | EPCH4_LONG | 73.6% | 2.05R | Full size |
| **B** | EPCH4_SHORT | 70.1% | 2.12R | Standard size |
| **B** | EPCH3_LONG | 71.0% | 1.78R | Standard size |
| **C** | EPCH1_SHORT | 65.8% | 1.84R | Reduced size, need filters |
| **C** | EPCH2_SHORT | 64.7% | 1.50R | Reduced size, need filters |
| **D** | EPCH1_LONG | 57.6% | 1.21R | Skip or minimum size |
| **D** | EPCH2_LONG | 57.4% | 1.22R | Skip or minimum size |

---

## Model-Specific Entry Filters

### EPCH1: Primary Zone Continuation

**EPCH1_SHORT** (65.8% baseline → **87.5%** with filters)
| Checkpoint | Requirement | Lift |
|------------|-------------|------|
| ✓ candle_range_pct | HIGH (0.20+) at entry | +10.0pp |
| ✓ short_score trend | RISING into entry | +21.6pp |
| ✓ short_score momentum | BUILDING (2nd half > 1st half) | +25.1pp |
| ✓ candle_range_pct momentum | BUILDING | +10.3pp |

**EPCH1_LONG** (57.6% baseline → **90.9%** with filters) *Low sample, use caution*
| Checkpoint | Requirement | Lift |
|------------|-------------|------|
| ✓ vol_delta trend | FALLING (absorption pattern) | +29.9pp |
| ✓ vol_delta momentum | FADING | +33.3pp |
| ✓ short_score momentum | FADING | +29.9pp |
| ✓ sma_spread momentum | FADING | +15.8pp |

**Signature Pattern**: EPCH1_LONG wins show delta flip: positive → negative (absorption) → strong positive at entry. Losses show monotonic positive delta with no absorption phase.

---

### EPCH2: Primary Zone Rejection

**EPCH2_SHORT** (64.7% baseline → **83.1%** with filters)
| Checkpoint | Requirement | Lift |
|------------|-------------|------|
| ✓ candle_range_pct | HIGH (0.20+) at entry | +18.4pp |
| ✓ H1 Structure | CONSISTENT_BULL (trade against) | +5.5pp |
| ✓ M15 Structure | CONSISTENT_BULL | +9.2pp |
| ✓ vol_delta trend | RISING | +6.5pp |
| ✓ vol_roc trend | FALLING (exhaustion) | +7.8pp |
| ✓ long_score momentum | STABLE | +16.1pp |

**EPCH2_LONG** (57.4% baseline → **66.2%** with filters)
| Checkpoint | Requirement | Lift |
|------------|-------------|------|
| ✓ H1 Structure | CONSISTENT_BEAR (trade against) | +8.9pp |
| ✓ candle_range_pct | HIGH (0.20+) at entry | +12.0pp |
| ✓ candle_range_pct momentum | BUILDING | +10.3pp |
| ✗ AVOID | H1 CONSISTENT_BULL | -14.2pp |

**Critical Rule**: EPCH2 trades AGAINST structure. Trading WITH structure alignment destroys edge:
- EPCH2_LONG + H1_BULL = 43.1% (SKIP)
- EPCH2_SHORT + M15_BEAR = 38.0% (SKIP)

---

### EPCH3: Secondary Zone Continuation

**EPCH3_SHORT** (81.2% baseline → **100%** with filters) *Low sample*
| Checkpoint | Requirement | Lift |
|------------|-------------|------|
| ✓ short_score trend | RISING | +18.8pp |
| ✓ vol_roc momentum | BUILDING | +11.6pp |
| ✓ candle_range_pct | HIGH (0.20+) at entry | +7.6pp |

**EPCH3_LONG** (71.0% baseline → **81.2%** with filters) *Low sample*
| Checkpoint | Requirement | Lift |
|------------|-------------|------|
| ✓ vol_delta trend | RISING | +10.3pp |
| ✓ vol_delta momentum | BUILDING | +6.8pp |
| ✓ M15 Structure | CONSISTENT_BULL | +20.7pp |
| ✓ vol_roc trend | FALLING | +10.0pp |

---

### EPCH4: Secondary Zone Rejection

**EPCH4_LONG** (73.6% baseline → **85.8%** with filters)
| Checkpoint | Requirement | Lift |
|------------|-------------|------|
| ✓ M15 Structure | CONSISTENT_BULL (trade with) | +12.1pp |
| ✓ H1 Structure | CONSISTENT_BULL | +6.4pp |
| ✓ candle_range_pct | HIGH (0.20+) at entry | +7.3pp |
| ✓ sma_spread momentum | BUILDING | +6.1pp |
| ✓ long_score momentum | STABLE | +12.3pp |

**EPCH4_SHORT** (70.1% baseline → **92.6%** with single filter)
| Checkpoint | Requirement | Lift |
|------------|-------------|------|
| ✓ vol_delta at entry | STRONG NEGATIVE | +22.5pp |
| ✓ H1 Structure | CONSISTENT_BEAR (trade with) | +7.8pp |
| ✓ short_score momentum | STABLE | +18.1pp |
| ✓ sma_spread momentum | STABLE | +25.1pp |

**Critical Rule**: EPCH4 trades WITH structure (opposite of EPCH2). Structure alignment confirms the bounce back toward macro trend.

---

## Quick Reference: Entry Bar Thresholds

### Universal Edge Boosters
| Indicator | Threshold | Effect |
|-----------|-----------|--------|
| candle_range_pct | ≥ 0.20 | +5 to +18pp across all models |
| Score at entry | MID (3-4) | Outperforms extremes by +6-16pp |
| Score trend | Aligned with direction | +5-22pp |

### Model-Specific vol_delta Rules
| Model | Direction | Optimal vol_delta Pattern |
|-------|-----------|---------------------------|
| EPCH1 | LONG | FALLING trend, FADING momentum (absorption) |
| EPCH1 | SHORT | RISING trend, BUILDING momentum |
| EPCH2 | SHORT | RISING trend, BUILDING momentum |
| EPCH2 | LONG | Either direction works if structure correct |
| EPCH3 | LONG | RISING trend, BUILDING momentum |
| EPCH3 | SHORT | FALLING trend |
| EPCH4 | LONG | BUILDING momentum |
| EPCH4 | SHORT | STRONG NEGATIVE at entry bar |

---

## Pre-Entry Checklist (Use This Tomorrow)

### Step 1: Identify Model + Direction
Price approaching HVN zone → Determine EPCH model → Note direction

### Step 2: Check Tier Rating
- **Tier A/B**: Proceed to filters
- **Tier C**: Need 2+ filters confirmed
- **Tier D**: Skip unless all filters green

### Step 3: Validate Structure Alignment
| Model | Required Structure |
|-------|-------------------|
| EPCH2 | AGAINST (Bull structure for SHORT, Bear for LONG) |
| EPCH4 | WITH (Bull structure for LONG, Bear for SHORT) |
| EPCH1/3 | Less critical, slight preference for alignment |

### Step 4: Check Entry Bar Conditions
- [ ] candle_range_pct ≥ 0.20?
- [ ] Score in MID range (3-4) or trending correctly?
- [ ] vol_delta pattern matches model requirement?

### Step 5: Size Position
| Filters Passed | Position Size |
|----------------|---------------|
| All (3+) | Full size |
| 2 of 3 | 75% size |
| 1 of 3 | 50% size |
| 0 | No trade |

---

## Red Flags (Immediate Skip)

| Condition | Action |
|-----------|--------|
| EPCH2_LONG + H1 CONSISTENT_BULL | NO TRADE (43% WR) |
| EPCH2_SHORT + M15 CONSISTENT_BEAR | NO TRADE (38% WR) |
| candle_range_pct LOW (<0.10) on EPCH2 | NO TRADE (-18pp) |
| Score at extreme (0-2 or 5-7) for wrong direction | Reduce size |
| Structure FLIP during ramp (FLIP_TO_BEAR/BULL) | Extra caution |

---

## Progression Signatures (What Winning Trades Look Like)

**EPCH2_SHORT Win Signature**:
- Candle range expanding: 0.25 → 0.27 at entry (vs 0.13 → 0.16 on losses)
- SMA spread negative but converging toward zero
- Vol_roc showing consistent positive values
- Short_score building throughout ramp

**EPCH4_LONG Win Signature**:
- SMA spread starts negative (-0.05) at bar -15
- Vol_delta flips from negative to positive around bar -8
- Candle range expands in final 5 bars
- Long_score stable or slightly building

**EPCH4_SHORT Win Signature (Highest Single-Filter WR)**:
- Vol_delta STRONG NEGATIVE at entry = 92.6% win rate
- SMA spread positive and stable
- Scores stable (not volatile)

---

*Document generated from analysis of 1,594 trades across 8 model+direction combinations. Low-sample findings (N<30) marked with caution. Update thresholds as sample sizes grow.*
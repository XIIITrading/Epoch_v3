# EPOCH SYSTEM ANALYSIS
## Indicator Analysis & Optimization Roadmap — January 2026

---

## 1. Current Status

### Analysis Complete

The Epoch Trading System has completed comprehensive analysis across four calculation modules (CALC-005 through CALC-008) covering 2,043 trades from December 15, 2025 through January 12, 2026. This analysis examined Health Score correlation, factor importance, indicator progression patterns, and rejection trade dynamics.

### Critical Finding: Health Score Design Flaw

The 10-factor Health Score system shows **near-zero predictive power** (r = 0.018, p = 0.40). The root cause has been identified: the system applies identical indicator logic to both continuation and rejection trades, when these trade types require **opposite indicator signals**.

### Key Metrics Summary

| Metric | Current Value | Assessment |
|--------|---------------|------------|
| Total Trades Analyzed | 2,043 | Sufficient for system-level conclusions |
| Health Score Correlation | r = 0.018 | No predictive power |
| Overall Win Rate | 55.4% | Baseline performance |
| Best Stop Type | M5 ATR (Close) | +1.310 expectancy |
| Inverted Factors | 6 of 10 | Requires dual scoring system |

### Stop Type Analysis Results

The current default stop (Zone + 5% Buffer) significantly underperforms alternatives:

| Stop Type | Expectancy | Win Rate | Avg Stop % |
|-----------|------------|----------|------------|
| Prior M1 H/L | +1.583 | 27.8% | 0.18% |
| Prior M5 H/L | +1.363 | 34.0% | 0.36% |
| **M5 ATR (Close)** | **+1.310** | **55.0%** | **0.59%** |
| M5 Fractal H/L | +1.224 | 26.3% | 0.83% |
| Zone + 5% Buffer (current) | +0.953 | 45.3% | 0.66% |
| M15 ATR (Close) | +0.790 | 36.4% | 1.00% |

**Recommendation:** Switch to M5 ATR (Close) — 37% expectancy improvement, +9.7pp win rate improvement.

### Factor Inversion Discovery

Six of ten Health Score factors show **inverted effects** between continuation and rejection trades:

| Factor | Continuation Lift | Rejection Lift | Inverted? |
|--------|-------------------|----------------|-----------|
| H1 Structure | +25.3pp | -6.2pp | **YES** |
| M5 Structure | +9.1pp | -0.4pp | **YES** |
| CVD Slope | +23.2pp | -2.2pp | **YES** |
| SMA Alignment | +19.3pp | -4.9pp | **YES** |
| SMA Momentum | -0.7pp | +10.2pp | **YES** |
| VWAP Position | +16.5pp | -13.2pp | **YES** |

---

## 2. Priority Process Improvements

### Priority 1: Implement Dual Scoring System (HIGH CONFIDENCE)

**Problem:** Single Health Score applied to all trades cancels out predictive effects.

**Solution:** Create separate scoring systems:

#### Continuation Score (EPCH01, EPCH03)
Factors with positive lift for continuation trades:
- Volume ROC (+21.3pp)
- CVD Slope (+23.2pp)
- SMA Alignment (+19.3pp)
- H1 Structure (+25.3pp)
- Volume Delta (+12.8pp)
- VWAP Position (+16.5pp)
- M5 Structure (+9.1pp)

#### Rejection Exhaustion Score (EPCH02, EPCH04)
Use **quintile-based exhaustion detection**:
- CVD Slope in **lowest quintile** = +1 point (+15.6pp lift, 71.4% win rate)
- SMA Spread in **lowest quintile** = +1 point (+14.2pp lift, 70.0% win rate)
- Volume ROC in **highest quintile** = +1 point (+10.4pp lift, 66.2% win rate)
- SMA Momentum widening = +1 point (+10.2pp lift)

**Implementation Complexity:** MEDIUM  
**Expected Impact:** HIGH

---

### Priority 2: Remove Dead Factors (HIGH CONFIDENCE)

Three factors provide zero predictive value across all trade types:

| Factor | Overall Lift | Action |
|--------|-------------|--------|
| Volume Delta | +0.9pp | REMOVE |
| CVD Slope (binary logic) | +0.0pp | REPLACE with quintile logic |
| M5 Structure | +0.6pp | REMOVE from rejection scoring |

**Implementation Complexity:** LOW  
**Expected Impact:** MEDIUM (reduces noise)

---

### Priority 3: Switch Default Stop Type (HIGH CONFIDENCE)

**Current:** Zone + 5% Buffer (+0.953 expectancy, 45.3% win rate)  
**Recommended:** M5 ATR (Close) (+1.310 expectancy, 55.0% win rate)

**Change Required:** Update DOW AI configuration only — no structural code changes.

**Implementation Complexity:** LOW  
**Expected Impact:** HIGH (+37% expectancy improvement)

---

### Priority 4: Implement Early Exit Warning (MEDIUM CONFIDENCE)

**Signal:** Health Score drop of ≥2 points within 5 bars

**Performance:**
- Captures 27.5% of losing trades
- Only 9.6% false positive rate
- +17.8pp separation between losers and winners

**Implementation:**
```python
IF bars_from_entry <= 5 AND health_delta <= -2:
    TRIGGER early_exit_warning = TRUE
    ACTION: Tighten stop to breakeven OR exit at next resistance
```

**Implementation Complexity:** LOW  
**Expected Impact:** MEDIUM

---

## 3. Extended Next Steps

### Phase 1: Implementation (Weeks 1-2)

| Task | Complexity | Impact |
|------|------------|--------|
| Update DOW AI to use M5 ATR (Close) as default stop | Low | High |
| Create Rejection Exhaustion Score module (3 factors) | Medium | High |
| Remove dead factors from scoring calculation | Low | Medium |
| Add early exit warning logic (-2 delta in 5 bars) | Low | Medium |
| Deploy changes to paper trading environment | Low | — |

### Phase 2: Validation (Weeks 3-6)

**Parallel Backtests:**
1. Current unified Health Score
2. New dual scoring system
3. Rejection-only exhaustion score

**Target:** 100+ trades per scoring methodology

**Key Validations:**
- Confirm EPCH02 LONG at CRITICAL scores maintains 70.6% win rate
- Investigate EPCH02 SHORT anomaly (CRITICAL: 41.6% vs MODERATE: 75.5%)
- Test quintile boundary optimization (Q1 vs Q1+Q2)

### Phase 3: Data Collection (Weeks 7-12)

**Objective:** Build full Q1 2026 dataset (January-March)

**Rationale:** Current holiday period data may not represent normal market behavior.

**Model-Specific Targets:**
| Model | Current n | Target n | Status |
|-------|-----------|----------|--------|
| EPCH01 | 96 | 200+ | Insufficient — continue collection |
| EPCH02 | 968 | — | Sufficient for analysis |
| EPCH03 | 99 | 200+ | Insufficient — continue collection |
| EPCH04 | 923 | — | Sufficient for analysis |

**Monitoring:**
- EPCH03 LONG shows concerning 0.81 MFE/MAE ratio (adverse > favorable)
- Consider temporary suspension from live trading
- Maintain data collection in paper mode

### Phase 4: Optimization (Q2 2026)

With validated dual scoring and full-quarter data:

1. **Quintile Boundary Optimization**
   - Test Q1 (lowest 20%) vs Q1+Q2 (lowest 40%)
   - Determine optimal exhaustion threshold

2. **Time-of-Day Analysis**
   - Morning reversals vs afternoon continuation
   - Session-specific indicator weighting

3. **Continuation Model Deep Dive**
   - Dedicated factor analysis for EPCH01/03
   - Implement continuation-specific scoring once n > 200

4. **Direction-Specific Refinement**
   - LONG trades show 1.28 MFE/MAE vs 1.01 for SHORT
   - Consider separate thresholds by direction

---

## Summary: DOW AI Configuration Changes

### Immediate Changes (Priority 1-3)

```yaml
# DOW AI Configuration Updates

stop_type:
  default: "M5_ATR_CLOSE"  # Changed from ZONE_5PCT_BUFFER
  
scoring_system:
  mode: "DUAL"  # Changed from UNIFIED
  
  continuation_score:  # EPCH01, EPCH03
    factors:
      - volume_roc
      - cvd_slope
      - sma_alignment
      - h1_structure
      - volume_delta
      - vwap_position
      - m5_structure
    
  rejection_exhaustion_score:  # EPCH02, EPCH04
    factors:
      - cvd_slope_q1      # Lowest quintile = +1
      - sma_spread_q1     # Lowest quintile = +1
      - volume_roc_q5     # Highest quintile = +1
      - sma_momentum      # Widening = +1

removed_factors:
  - volume_delta (from rejection)
  - cvd_slope_binary (replaced with quintile)
  - m5_structure (from rejection)

early_exit_warning:
  enabled: true
  threshold: -2
  window_bars: 5
  action: "TIGHTEN_STOP_TO_BREAKEVEN"
```

---

## Bottom Line

The Health Score system isn't fundamentally broken — it's misapplied. Continuation trades need momentum confirmation (trend alignment, CVD rising, SMA expanding). Rejection trades need exhaustion confirmation (trend overextension, CVD extreme, SMA contracting).

By applying the same logic to both, the system achieves near-zero predictive power because the effects cancel out. Implementing dual scoring should unlock significant edge, particularly for the high-volume rejection models (EPCH02/04) that comprise 90%+ of trades.

---

*Prepared by Monte AI — January 12, 2026*
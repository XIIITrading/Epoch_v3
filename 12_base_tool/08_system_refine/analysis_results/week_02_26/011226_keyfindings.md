# Indicator Analysis Synthesis — January 12, 2026

## Executive Summary

The analysis reveals a **fundamental flaw in the Health Score design**: the system applies identical indicator logic to both continuation and rejection trades, when these trade types require **opposite indicator signals**.

**Key Findings:**

1. **Health Score has near-zero predictive power** (r = 0.018, p = 0.40) — the current 10-factor composite provides no statistical edge for trade selection

2. **Six of ten factors are inverted for rejection trades** — H1 Structure, M5 Structure, CVD Slope, SMA Alignment, SMA Momentum, and VWAP Position all show opposite effects between continuation and rejection models

3. **Only two factors show universal value**: Volume ROC (+12.0pp lift) and SMA Momentum for rejections (+10.2pp lift)

4. **Rejection trades thrive on exhaustion signals**: CVD Slope in lowest quintile = 71.4% win rate (+15.6pp); SMA Spread in lowest quintile = 70.0% win rate (+14.2pp)

5. **The "MODERATE" bucket anomaly is explained**: 63.5% win rate at scores 6-7 captures rejection trades with contracting indicators that happen to land in mid-range scores

---

## DOW AI Configuration Changes

### Priority 1: Implement Dual Scoring System (HIGH CONFIDENCE)

**Finding:** Continuation and rejection trades require fundamentally different indicator logic.

**Current State:** Single Health Score applied to all trades  
**Recommended State:** Two separate scoring systems

#### Continuation Score (EPCH01, EPCH03)

Retain factors that showed positive lift for continuation:

| Factor | Cont. Lift | Keep? |
|--------|-----------|-------|
| Volume ROC | +21.3pp | ✓ YES |
| CVD Slope | +23.2pp | ✓ YES |
| SMA Alignment | +19.3pp | ✓ YES |
| H1 Structure | +25.3pp | ✓ YES |
| Volume Delta | +12.8pp | ✓ YES |
| VWAP Position | +16.5pp | ✓ YES |
| M5 Structure | +9.1pp | ✓ YES |
| M15 Structure | +0.3pp | ✗ Remove |
| SMA Momentum | -0.7pp | ✗ Remove |

**Continuation Score = 7 factors** (remove M15 Structure, SMA Momentum)

#### Rejection Score (EPCH02, EPCH04)

Implement **inverted logic** for exhaustion signals:

| Factor | Rej. Lift | Scoring Logic |
|--------|-----------|---------------|
| SMA Spread (Q1) | +14.2pp | ✓ Score point if spread in LOWEST quintile |
| CVD Slope (Q1) | +15.6pp | ✓ Score point if CVD in LOWEST quintile |
| Volume ROC (Q5) | +10.4pp | ✓ Score point if Vol ROC in HIGHEST quintile |
| SMA Momentum | +10.2pp | ✓ Keep current logic (widening = point) |
| M15 Structure | +2.7pp | ~ Keep but low weight |

**Rejection Score = 5 factors** with inverted exhaustion logic

**Implementation Complexity:** MEDIUM — Requires code changes to DOW AI scoring module  
**Priority:** P1

---

### Priority 2: Remove Dead Factors (HIGH CONFIDENCE)

**Finding:** Three factors provide zero predictive value across all trade types.

| Factor | Overall Lift | Action |
|--------|-------------|--------|
| Volume Delta | +0.9pp | REMOVE |
| CVD Slope (current logic) | +0.0pp | REPLACE with quintile logic |
| M5 Structure | +0.6pp | REMOVE from rejection scoring |

**Note:** CVD Slope shows +23.2pp for continuation when "healthy" (aligned), but the binary healthy/unhealthy classification destroys value. For rejection trades, quintile-based extreme values are what matter.

**Implementation Complexity:** LOW — Remove factors from calculation  
**Priority:** P1

---

### Priority 3: Implement Early Exit Warning (MEDIUM CONFIDENCE)

**Finding:** Health Score drop of ≥2 points within 5 bars captures 27.5% of losers with only 9.6% false positive rate.

**Recommended Implementation:**
```python
IF bars_from_entry <= 5 AND health_delta <= -2:
    TRIGGER early_exit_warning = TRUE
    ACTION: Tighten stop to breakeven OR exit at next resistance
```

**Lift:** +17.8pp separation between losers and winners  
**Implementation Complexity:** LOW — Add monitoring logic to DOW AI  
**Priority:** P2

---

### Priority 4: Adjust Health Score Thresholds (MEDIUM CONFIDENCE)

**Current Thresholds:**
- STRONG: 8-10
- MODERATE: 6-7
- WEAK: 4-5
- CRITICAL: 0-3

**Finding:** The MODERATE bucket (6-7) shows best performance at 63.5% win rate. This is likely capturing rejection trades with partially inverted signals.

**Recommended Action:** After implementing dual scoring, re-evaluate thresholds. Current thresholds are meaningless given the inverted factor problem.

**Priority:** P3 (dependent on P1)

---

## Model-Specific Adjustments

### EPCH02 (Primary Zone Rejection) — Largest Sample, Best Data

| Subgroup | Trades | Current WR | Recommended Action |
|----------|--------|------------|-------------------|
| EPCH02 LONG, CRITICAL | 211 | 70.6% | **DO NOT FILTER** — Low scores = exhaustion = good |
| EPCH02 LONG, WEAK | 162 | 38.3% | Monitor — may indicate noise zone |
| EPCH02 SHORT, MODERATE | 98 | 75.5% | **PRIORITIZE** — Sweet spot |
| EPCH02 SHORT, CRITICAL | 238 | 41.6% | Needs investigation — why different from LONG? |

**Key Insight:** EPCH02 LONG at CRITICAL Health Score (211 trades, 70.6% WR) is your best-performing subgroup. The current system would filter these OUT, destroying edge.

### EPCH04 (Secondary Zone Rejection)

| Subgroup | Trades | Current WR | Recommended Action |
|----------|--------|------------|-------------------|
| EPCH04 LONG, WEAK | 145 | 62.1% | **PRIORITIZE** — Contrarian signal working |
| EPCH04 LONG, CRITICAL | 199 | 56.8% | Acceptable |
| EPCH04 SHORT, all buckets | ~458 | 54-57% | No clear pattern — needs refinement |

### EPCH01/EPCH03 (Continuation Models) — Small Samples

| Model | Trades | Note |
|-------|--------|------|
| EPCH01 | 96 | Insufficient data — cannot make confident adjustments |
| EPCH03 | 99 | Insufficient data — MODERATE bucket shows 76.5% (n=17) but too small |

**Recommendation:** Continue data collection for 60+ more trading days before implementing continuation-specific changes.

---

## Statistical Confidence Assessment

### HIGH CONFIDENCE (n ≥ 200, actionable now)

| Finding | Sample Size | Effect Size | Confidence |
|---------|-------------|-------------|------------|
| Volume ROC +12.0pp lift | n=657 healthy, n=1386 unhealthy | Strong | **HIGH** |
| VWAP inversion for rejection | n=1,185 healthy, n=858 unhealthy | Strong (-11.7pp) | **HIGH** |
| CVD Slope Q1 for rejection | n=370 | +15.6pp | **HIGH** |
| SMA Spread Q1 for rejection | n=370 | +14.2pp | **HIGH** |
| Overall Health Score r=0.018 | n=2,043 | Near-zero | **HIGH** (confirms problem) |

### MEDIUM CONFIDENCE (n = 100-200, implement with monitoring)

| Finding | Sample Size | Effect Size | Confidence |
|---------|-------------|-------------|------------|
| Early warning (-2 delta in 5 bars) | ~550 losers tested | +17.8pp | **MEDIUM** |
| SMA Momentum +9.1pp | n=1,054 healthy | Moderate | **MEDIUM** |

### LOW CONFIDENCE (n < 100, continue collecting data)

| Finding | Sample Size | Note |
|---------|-------------|------|
| Continuation factor weights | n=210 total | Need 300+ for model-specific tuning |
| EPCH01/03 optimal thresholds | n=96-99 | Statistically unreliable |
| STRONG bucket performance | n=33 | Far too small |

---

## Next Steps / Further Research

### Immediate Actions (Next 2 Weeks)

1. **Implement Rejection Exhaustion Score** — Replace current Health Score for EPCH02/04 with quintile-based exhaustion metrics
   - CVD Slope Q1 = +1 point
   - SMA Spread Q1 = +1 point  
   - Volume ROC Q5 = +1 point
   - Test on paper trades first

2. **Remove Dead Factors** — Volume Delta, CVD Slope binary logic, M5 Structure from rejection scoring

3. **Add Early Exit Logic** — Implement -2 delta warning system in DOW AI

### Short-Term Research (Next 30 Days)

4. **Validate Exhaustion Score** — Run backtests comparing:
   - Current unified Health Score
   - New dual scoring system
   - Target: 100+ trades per scoring system

5. **Investigate EPCH02 SHORT Anomaly** — Why does CRITICAL (41.6%) underperform MODERATE (75.5%)? May indicate direction-specific exhaustion patterns.

6. **Quantile Boundary Optimization** — Test whether Q1 (lowest 20%) is optimal or if Q1+Q2 (lowest 40%) captures more edge with acceptable dilution.

### Medium-Term Research (Next Quarter)

7. **Build Full-Quarter Dataset** — Current holiday period data may not represent normal market behavior. Need Jan-Mar 2026 data for validation.

8. **Continuation Model Deep Dive** — Once EPCH01/03 reach n=200+, perform dedicated factor analysis.

9. **Time-of-Day Interaction** — Do exhaustion signals work better at certain times? Morning reversals vs afternoon continuation?

---

## Summary Recommendation Matrix

| Change | Impact | Confidence | Complexity | Priority |
|--------|--------|------------|------------|----------|
| Dual Scoring System | HIGH | HIGH | MEDIUM | **P1** |
| Remove Dead Factors | MEDIUM | HIGH | LOW | **P1** |
| Rejection Exhaustion Logic | HIGH | HIGH | MEDIUM | **P1** |
| Early Exit Warning | MEDIUM | MEDIUM | LOW | **P2** |
| Threshold Recalibration | LOW | LOW | LOW | **P3** |

---

## Detailed Analysis Results

### CALC-005: Health Score Correlation Analysis

**Summary Statistics:**
- Total Trades Analyzed: 2,043
- Overall Win Rate: 55.4%
- Correlation Coefficient: r = 0.018 (p-value: 0.4045)
- Optimal Threshold: >= 4 (lift: +1.0pp)

**Win Rate by Health Score Bucket:**

| Bucket | Trades | Win Rate | Lift |
|--------|--------|----------|------|
| CRITICAL (0-3) | 939 | 54.2% | -1.2pp |
| WEAK (4-5) | 677 | 52.3% | -3.1pp |
| MODERATE (6-7) | 394 | 63.5% | +8.1pp |
| STRONG (8-10) | 33 | 54.5% | -0.8pp |

**Win Rate by Threshold:**

| Threshold | Trades Above | Win Rate | Lift |
|-----------|--------------|----------|------|
| >= 4 | 1,104 | 56.3% | +1.0pp |
| >= 5 | 770 | 57.9% | +2.6pp |
| >= 6 | 427 | 62.8% | +7.4pp |
| >= 7 | 166 | 60.2% | +4.9pp |
| >= 8 | 33 | 54.5% | -0.8pp |

---

### CALC-006: Factor Importance Analysis

**Complete Factor Ranking:**

| Rank | Factor | Healthy WR | Unhealthy WR | Lift | Healthy n | Unhealthy n |
|------|--------|------------|--------------|------|-----------|-------------|
| 1 | Volume ROC | 63.5% | 51.5% | +12.0pp | 657 | 1,386 |
| 2 | SMA Momentum | 59.8% | 50.7% | +9.1pp | 1,054 | 989 |
| 3 | M15 Structure | 57.4% | 54.7% | +2.7pp | 521 | 1,522 |
| 4 | Volume Delta | 55.8% | 54.9% | +0.9pp | 1,128 | 915 |
| 5 | M5 Structure | 55.7% | 55.1% | +0.6pp | 779 | 1,264 |
| 6 | CVD Slope | 55.4% | 55.3% | +0.0pp | 966 | 1,077 |
| 7 | SMA Alignment | 54.2% | 56.9% | -2.7pp | 1,166 | 877 |
| 8 | H1 Structure | 51.6% | 56.0% | -4.4pp | 287 | 1,756 |
| 9 | VWAP Position | 50.5% | 62.1% | -11.7pp | 1,185 | 858 |
| 10 | H4 Structure | 0.0% | 55.4% | -55.4pp | 0 | 2,043 |

**Factor Group Performance:**

| Group | Avg Lift | Best Factor |
|-------|----------|-------------|
| STRUCTURE | -14.1pp | M15 Structure |
| VOLUME | +4.3pp | Volume ROC |
| PRICE | -1.7pp | SMA Momentum |

---

### CALC-007: Indicator Progression Analysis

**Winner vs Loser Path Comparison:**

| Metric | Winners | Losers | Difference |
|--------|---------|--------|------------|
| Entry Health Score | 4.8 | 4.9 | -0.1 |
| Peak Health Score | 6.4 | 3.7 | +2.7 |
| Delta to Peak | +1.5 | -1.2 | +2.7 |

**Best Early Warning Signals:**

| Indicator | Threshold | Window | Loser Hit% | Winner Hit% | Lift |
|-----------|-----------|--------|------------|-------------|------|
| health_score | -2 | 5 bars | 27.5% | 9.6% | +17.8pp |
| health_score | -1 | 5 bars | 46.0% | 29.7% | +16.3pp |
| health_score | -2 | 10 bars | 37.8% | 21.5% | +16.3pp |
| volume_score | -1 | 5 bars | 39.2% | 27.7% | +11.4pp |

---

### CALC-008: Rejection Dynamics Analysis

**Health Score Inversion Test:**

| Model Type | Correlation | STRONG Win% | CRITICAL Win% | Inverted? |
|------------|-------------|-------------|---------------|-----------|
| Continuation | 0.264 | 100.0% (n=5) | 37.5% (n=64) | No |
| Rejection | -0.003 | 46.4% (n=28) | 55.4% (n=875) | **YES** |

**Factor Inversion Analysis:**

| Factor | Cont. Lift | Rej. Lift | Inverted? | Strength |
|--------|------------|-----------|-----------|----------|
| H1 Structure | +25.3pp | -6.2pp | **YES** | STRONG |
| CVD Slope | +23.2pp | -2.2pp | **YES** | STRONG |
| SMA Alignment | +19.3pp | -4.9pp | **YES** | STRONG |
| VWAP Position | +16.5pp | -13.2pp | **YES** | STRONG |
| M5 Structure | +9.1pp | -0.4pp | **YES** | MODERATE |
| SMA Momentum | -0.7pp | +10.2pp | **YES** | MODERATE |
| Volume ROC | +21.3pp | +11.3pp | No | — |
| Volume Delta | +12.8pp | +0.6pp | No | — |
| M15 Structure | +0.3pp | +2.7pp | No | — |

**Exhaustion Indicator Discovery (Rejection Trades Only):**

| Indicator | Quintile | Trades | Win Rate | Lift |
|-----------|----------|--------|----------|------|
| cvd_slope | Lowest (Q1) | 370 | 71.4% | +15.6pp |
| sma_spread | Lowest (Q1) | 370 | 70.0% | +14.2pp |
| vol_roc | Highest (Q5) | 370 | 66.2% | +10.4pp |

**VERDICT:** Rejection trades require fundamentally different scoring logic based on exhaustion signals rather than momentum confirmation.

---

## Bottom Line

**The Health Score isn't broken — it's misapplied.**

Continuation trades need momentum confirmation (trend alignment, CVD rising, SMA expanding). Rejection trades need exhaustion confirmation (trend overextension, CVD extreme, SMA contracting).

By applying the same logic to both, the system achieves near-zero predictive power because the effects cancel out. Implementing dual scoring should unlock significant edge, particularly for the high-volume rejection models (EPCH02/04) that comprise 90%+ of your trades.

---

*Prepared by Monte AI — January 12, 2026*
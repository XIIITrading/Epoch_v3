# Indicator Playbook: CONT / REJECT Signal Mapping

> **Purpose**: Maps each indicator's real-time behavior to either a Continuation (CONT) or Rejection (REJECT) signal.
> **Owner**: Human-maintained, Claude-referenced
> **Last Updated**: 2026-02-01
> **Data Source**: trade_lifecycle_signals table (5,922 trades, 54.0% baseline WR)
> **Method**: M1 indicator bar analysis of 30-bar ramp-up sequences before entry
>
> This is NOT about whether an indicator is "healthy." It's about reading what the indicators
> are telling you about whether price is setting up to continue through or reject from the zone.

---

## How to Use This Playbook

When you're watching a setup develop in real time, check each indicator below.
For each one, ask: "Is this indicator telling me continuation or rejection?"

- **+1 CONT**: Evidence that price will drive through the zone
- **+1 REJECT**: Evidence that price will bounce off / reverse from the zone
- **0 NEUTRAL**: No clear signal either way

Tally them up. If CONT > REJECT, favor continuation entries (EPCH1/EPCH3).
If REJECT > CONT, favor rejection entries (EPCH2/EPCH4).

---

## Indicator Signals

### 1. Market Structure (M15 / H1 / H4)

M15 structure is the single strongest directional filter in the data.

**At entry (snapshot from M1 bars):**

| Signal | WR | Edge | N |
|--------|----:|-----:|---:|
| M15 BULL | 58.5% | +4.5pp | 2,887 |
| M15 BEAR | 49.8% | -4.3pp | 3,035 |
| M1 NEUTRAL | 60.5% | +6.4pp | 531 |
| M5 NEUTRAL | 42.5% | -11.5pp | 160 |

**Interpretation**: M15 aligned with trade direction = +1 CONT. M15 opposing = +1 REJECT. M5 NEUTRAL at entry is a strong avoid signal (-11.5pp). M1 NEUTRAL at entry is actually positive (+6.4pp) -- suggests a pause/consolidation before a move.

H1 and H4 at entry show minimal differentiation (<2pp) -- not reliable standalone signals.

---

### 2. Candle Range / Price Expansion (Ramp-Up Pattern)

**What the M1 bars actually show before winning trades:**

| Rampup Trend | WR | Edge | N |
|-------------|----:|-----:|---:|
| FLAT | 60.6% | +6.5pp | 464 |
| INC_THEN_DEC | 58.8% | +4.8pp | 971 |
| DECREASING | 49.3% | -4.7pp | 1,868 |
| VOLATILE | 58.2% | +4.2pp | 641 |

**Direction-specific (SHORT trades ramp-up):**

| Rampup Trend | WR | Edge | N |
|-------------|----:|-----:|---:|
| VOLATILE | 64.2% | +10.2pp | 349 |
| INC_THEN_DEC | 62.5% | +8.5pp | 483 |
| FLAT | 60.1% | +6.1pp | 258 |
| DECREASING | 49.2% | -4.8pp | 998 |

**The absorption-to-rejection pattern is real**: For shorts, candle range that increases then decreases (INC_THEN_DEC = price expanded then compressed at the zone) shows +8.5pp edge. VOLATILE candle range for shorts is even stronger at +10.2pp.

**Signal mapping:**
- Candle range FLAT or INC_THEN_DEC in ramp-up -> +1 CONT (zone holding, compression before move)
- Candle range DECREASING consistently -> +1 REJECT risk (momentum dying)
- For SHORTS: Candle range VOLATILE or INC_THEN_DEC -> +1 CONT (strong +10pp edge)
- For LONGS: Candle range FLAT -> +1 CONT (+7.1pp edge)

---

### 3. Volume Delta (Ramp-Up Pattern)

**What vol delta actually does before winning trades:**

| Rampup Trend | WR | Edge | N |
|-------------|----:|-----:|---:|
| FLAT | 48.1% | -6.0pp | 412 |
| INC_THEN_DEC | 58.3% | +4.3pp | 797 |
| DECREASING | 50.2% | -3.8pp | 1,739 |
| DEC_THEN_INC | 57.6% | +3.6pp | 727 |
| INCREASING | 56.2% | +2.2pp | 1,812 |

**SHORT trades specifically:**

| Rampup Trend | WR | Edge | N |
|-------------|----:|-----:|---:|
| INC_THEN_DEC | 63.3% | +9.3pp | 387 |
| DEC_THEN_INC | 60.7% | +6.7pp | 382 |
| DECREASING | 48.5% | -5.5pp | 949 |
| INCREASING | 59.4% | +5.4pp | 921 |
| FLAT | 49.8% | -4.3pp | 215 |

**Flip detection (ramp-up):**

| Signal | WR | Edge | N |
|--------|----:|-----:|---:|
| CVD FLIP_TO_NEGATIVE | 47.9% | -6.1pp | 753 |
| CVD FLIP_TO_POSITIVE | 56.9% | +2.8pp | 795 |
| CVD NO_FLIP | 55.8% | +1.8pp | 573 |

**Signal mapping:**
- Vol delta INC_THEN_DEC or DEC_THEN_INC (showing reversal pattern) -> +1 CONT
- Vol delta FLAT -> +1 REJECT risk (-6.0pp, no energy)
- Vol delta DECREASING -> +1 REJECT risk (momentum draining)
- CVD flip to negative during ramp-up -> strong warning (-6.1pp)

---

### 4. Volume ROC (Rate of Change)

**Ramp-up trend:**

| Rampup Trend | WR | Edge | N |
|-------------|----:|-----:|---:|
| INC_THEN_DEC | 58.5% | +4.4pp | 862 |
| INCREASING | 57.2% | +3.2pp | 1,045 |
| DECREASING | 50.7% | -3.3pp | 2,040 |

**Post-entry (what happens to vol ROC after entry):**

| Post Trend | WR | Edge | N |
|-----------|----:|-----:|---:|
| DEC_THEN_INC | 60.0% | +5.9pp | 1,259 |
| VOLATILE | 47.5% | -6.5pp | 568 |

**SHORT ramp-up specifically:**

| Rampup Trend | WR | Edge | N |
|-------------|----:|-----:|---:|
| INC_THEN_DEC | 64.3% | +10.2pp | 442 |

**Signal mapping:**
- Vol ROC increasing or peaking then declining -> +1 CONT (volume arrived, confirming move)
- Vol ROC decreasing consistently -> +1 REJECT risk (no energy behind the approach)
- For SHORTS: Vol ROC INC_THEN_DEC is a +10.2pp signal -- volume surged then pulled back before entry

---

### 5. CVD Slope (Cumulative Volume Delta)

**Ramp-up trend:**

| Rampup Trend | WR | Edge | N |
|-------------|----:|-----:|---:|
| INC_THEN_DEC | 59.2% | +5.2pp | 392 |
| VOLATILE | 48.4% | -5.6pp | 64 |

**SHORT ramp-up specifically:**

| Rampup Trend | WR | Edge | N |
|-------------|----:|-----:|---:|
| INC_THEN_DEC | 64.5% | +10.5pp | 228 |
| FLAT | 40.4% | -13.6pp | 47 |

**Post-entry:**

| Post Trend | WR | Edge | N |
|-----------|----:|-----:|---:|
| DEC_THEN_INC | 44.3% | -9.8pp | 357 |
| FLAT | 61.9% | +7.9pp | 84 |

**Signal mapping:**
- CVD slope showing reversal pattern (INC_THEN_DEC) -> +1 CONT (+5.2pp overall, +10.5pp for shorts)
- CVD slope VOLATILE -> +1 REJECT risk (-5.6pp)
- CVD slope FLAT during ramp-up for SHORTS -> strong REJECT (-13.6pp, no order flow conviction)
- Post-entry: CVD reversing (DEC_THEN_INC) is a bad sign (-9.8pp)

---

### 6. SMA Spread (Ramp-Up Pattern)

**Ramp-up trend:**

| Rampup Trend | WR | Edge | N |
|-------------|----:|-----:|---:|
| FLAT | 72.3% | +18.3pp | 65 |
| VOLATILE | 58.1% | +4.0pp | 31 |
| INCREASING | 52.7% | -1.3pp | 2,598 |
| DECREASING | 55.2% | +1.2pp | 2,569 |

**SHORT ramp-up specifically:**

| Rampup Trend | WR | Edge | N |
|-------------|----:|-----:|---:|
| FLAT | 77.4% | +23.4pp | 31 |
| DECREASING | 58.2% | +4.2pp | 1,339 |

**LONG ramp-up specifically:**

| Rampup Trend | WR | Edge | N |
|-------------|----:|-----:|---:|
| FLAT | 67.6% | +13.6pp | 34 |

**At entry (level):**

| Level | WR | Edge | N |
|-------|----:|-----:|---:|
| WIDE_BEAR | 56.5% | +2.5pp | 2,077 |
| NARROW_BEAR | 52.3% | -1.8pp | 1,060 |
| WIDE_BULL | 52.9% | -1.2pp | 1,816 |

**Signal mapping:**
- SMA spread FLAT in ramp-up -> **STRONGEST SIGNAL: +18.3pp overall, +23.4pp for shorts**. This means the SMAs have converged and are sitting still -- a compressed spring about to release.
- SMA spread FLAT -> +1 CONT (very high conviction)
- SMA spread WIDE_BEAR at entry -> mild +1 CONT for shorts (+2.5pp)

---

### 7. SMA Momentum Ratio

**Ramp-up trend:**

| Rampup Trend | WR | Edge | N |
|-------------|----:|-----:|---:|
| FLAT | 46.8% | -7.2pp | 111 |

**LONG ramp-up:**

| Rampup Trend | WR | Edge | N |
|-------------|----:|-----:|---:|
| FLAT | 40.6% | -13.4pp | 69 |
| DEC_THEN_INC | 59.8% | +5.8pp | 234 |

**Post-entry:**

| Post Trend | WR | Edge | N |
|-----------|----:|-----:|---:|
| FLAT | 67.6% | +13.5pp | 111 |
| VOLATILE | 39.1% | -14.9pp | 46 |

**Signal mapping:**
- SMA momentum FLAT during ramp-up -> +1 REJECT risk (-7.2pp) -- no trend strength developing
- SMA momentum DEC_THEN_INC for LONGS -> +1 CONT (+5.8pp) -- momentum recovering
- Post-entry: SMA momentum becoming VOLATILE is a very bad sign (-14.9pp)
- Post-entry: SMA momentum staying FLAT is very positive (+13.5pp)

---

### 8. Health Score / Continuation Score

**Ramp-up trend:**

| Rampup Trend | WR | Edge | N |
|-------------|----:|-----:|---:|
| DECREASING | 37.8% | -16.2pp | 45 |
| DEC_THEN_INC | 57.0% | +3.0pp | 435 |
| INCREASING | 56.1% | +2.1pp | 82 |

**SHORT ramp-up:**

| Rampup Trend | WR | Edge | N |
|-------------|----:|-----:|---:|
| DECREASING | 33.3% | -20.7pp | 30 |
| DEC_THEN_INC | 60.5% | +6.5pp | 233 |
| VOLATILE | 60.4% | +6.4pp | 139 |
| INC_THEN_DEC | 59.4% | +5.4pp | 254 |

**At entry (level):**

| Level | WR | Edge | N |
|-------|----:|-----:|---:|
| CRITICAL | 46.3% | -7.7pp | 298 |
| STRONG | 55.7% | +1.7pp | 2,072 |
| WEAK | 55.4% | +1.4pp | 1,744 |
| MODERATE | 52.0% | -2.0pp | 1,808 |

**M5 progression (during trade):**

| Trend | WR | Edge | N |
|-------|----:|-----:|---:|
| DECREASING | 17.1% | -36.9pp | 76 |
| VOLATILE | 58.0% | +3.9pp | 666 |
| DEC_THEN_INC | 57.1% | +3.0pp | 878 |

**Signal mapping:**
- Health score DECREASING in ramp-up -> **STRONG AVOID (-16.2pp, -20.7pp for shorts)**
- Health score CRITICAL at entry -> +1 REJECT (-7.7pp)
- Health score DEC_THEN_INC -> +1 CONT (recovering from a dip = healthy)
- M5 health DECREASING during trade -> 17.1% WR, strongest negative signal in entire dataset (-36.9pp)
- M5 health VOLATILE during trade -> +1 CONT (oscillating health = normal winning trade behavior)

---

### 9. Long Score / Short Score

**Ramp-up short_score INCREASING:**

| Signal | WR | Edge | N |
|--------|----:|-----:|---:|
| short_score INCREASING | 62.7% | +8.7pp | 67 |
| short_score DEC_THEN_INC | 48.9% | -5.2pp | 706 |
| short_score VOLATILE | 49.0% | -5.0pp | 388 |

**Post-entry long_score DECREASING:**

| Signal | WR | Edge | N |
|--------|----:|-----:|---:|
| long_score DECREASING | 38.6% | -15.5pp | 83 |

**Signal mapping:**
- Short score INCREASING in ramp-up -> +1 CONT for shorts (+8.7pp)
- Short score DEC_THEN_INC or VOLATILE -> +1 REJECT risk (-5pp each)
- Post-entry long_score DECREASING -> strong exit signal (-15.5pp)

---

## Key Combination Patterns

These indicator pairs create compound edges far exceeding single-indicator signals:

| Combination | WR | Edge | N |
|------------|----:|-----:|---:|
| vol_delta INC + cvd_slope INC_THEN_DEC | 83.3% | +29.3pp | 60 |
| candle_range INC_THEN_DEC + vol_delta INC_THEN_DEC | 75.0% | +21.0pp | 128 |
| sma_spread INC_THEN_DEC + vol_delta INCREASING | 75.4% | +21.4pp | 65 |
| candle_range INC_THEN_DEC + vol_delta VOLATILE | 26.5% | -27.5pp | 83 |
| candle_range DEC_THEN_INC + vol_delta FLAT | 23.7% | -30.4pp | 93 |
| CRITICAL health + EXPLOSIVE candle | 31.2% | -22.8pp | 32 |
| cvd FLIP_TO_POSITIVE + vol_delta INC_THEN_DEC | 72.6% | +18.6pp | 124 |
| EXPLOSIVE candle + MILD_SELL vol_delta at entry | 66.3% | +12.3pp | 202 |

**The 83% pattern**: Vol delta increasing while CVD slope shows INC_THEN_DEC (order flow building but cumulative flow reversing pattern) -> 83.3% WR. This is the strongest compound signal in the data.

**The 24% avoid pattern**: Candle range declining then increasing while vol delta is flat -> 23.7% WR. Price expanding without volume conviction = trap.

---

## Scoring Summary Template

Use this when evaluating a setup in real time:

```
Setup: [TICKER] [LONG/SHORT] at [Zone Type]
Date: ____  Time: ____

CONT  REJECT  NEUTRAL  Indicator
----  ------  -------  ---------
 [ ]   [ ]     [ ]     M15 Structure (vs direction)
 [ ]   [ ]     [ ]     Candle Range ramp-up pattern
 [ ]   [ ]     [ ]     Vol Delta ramp-up pattern
 [ ]   [ ]     [ ]     Vol ROC ramp-up pattern
 [ ]   [ ]     [ ]     CVD Slope ramp-up pattern
 [ ]   [ ]     [ ]     SMA Spread ramp-up (FLAT = strong CONT)
 [ ]   [ ]     [ ]     SMA Momentum ramp-up
 [ ]   [ ]     [ ]     Health Score ramp-up trend
 [ ]   [ ]     [ ]     Direction Score (long_score / short_score)

CONT Total:  ___
REJECT Total: ___

Recommendation: CONTINUATION / REJECTION / NO TRADE
```

**Quick Disqualifiers (immediate NO TRADE):**
- Health score DECREASING in ramp-up (-16.2pp)
- M5 NEUTRAL at entry (-11.5pp)
- CRITICAL health + EXPLOSIVE candle range at entry (-22.8pp)
- Candle range DECREASING + vol delta FLAT (-30.4pp)

---

## Open Questions for Further Analysis

1. ~~Can we detect the absorption-to-expansion sequence from M1 bar data programmatically?~~ **ANSWERED**: INC_THEN_DEC candle range pattern captures this. +4.8pp overall, +8.5pp for shorts.
2. **Interaction effects**: The combination patterns section above answers this partially. Vol delta + CVD slope and candle range + vol delta are the strongest pairs.
3. **Time-of-day**: Does the CONT/REJECT balance shift during the session? (Not yet tested)
4. **Dynamic weighting**: Should SMA spread FLAT (+18.3pp) carry 3x weight vs M15 structure (+4.5pp)?

---

*This playbook is the source of truth for how indicators map to CONT/REJECT signals.*
*All findings are backed by statistical analysis of 5,922 trades from the trade_lifecycle_signals table.*
*Updated by the trader based on real-time observation and validated by statistical analysis.*
*Claude references this document during analysis cycles.*

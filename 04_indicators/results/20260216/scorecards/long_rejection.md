# Scorecard: Long Rejection

**Direction:** LONG | **Models:** EPCH2, EPCH4
**Trades:** 545 | **Win Rate:** 52.5% | **Avg R:** 1.09
**Generated:** 2026-02-16 07:30:06

---

## Top 5 Indicators

### #1: Candle Range % (Tier S -- 25.3pp effect)
- **Confidence:** HIGH
- **Signal:** TAKE when candle_range_pct in Q1 (0.0000 to 0.0857)
- **Avoid:** SKIP when candle_range_pct in Q5 (0.4530 to 3.6583)
- **Best state:** Q1 (0.0000 to 0.0857) = 66.1% WR (109 trades)
- **Worst state:** Q5 (0.4530 to 3.6583) = 40.7% WR (108 trades)
- **P-value:** 0.009740
- **Ramp-up pattern:** Winners show lower values in last 10 bars. Divergence: -0.045527. decelerating (-0.002644/bar)

### #2: Volume ROC (Tier S -- 22.1pp effect)
- **Confidence:** HIGH
- **Signal:** TAKE when vol_roc in Q3 (-14.8940 to 5.8057)
- **Avoid:** SKIP when vol_roc in Q4 (5.8144 to 33.8266)
- **Best state:** Q3 (-14.8940 to 5.8057) = 63.9% WR (108 trades)
- **Worst state:** Q4 (5.8144 to 33.8266) = 41.8% WR (110 trades)
- **P-value:** 0.008549
- **Ramp-up pattern:** Winners show lower values in last 10 bars. Divergence: -187.364372. accelerating (+16.318185/bar)

### #3: SMA Configuration (Tier S -- 21.2pp effect)
- **Confidence:** HIGH
- **Signal:** TAKE when sma_config = BULL
- **Avoid:** SKIP when sma_config = BEAR
- **Best state:** BULL = 61.5% WR (314 trades)
- **Worst state:** BEAR = 40.3% WR (231 trades)
- **P-value:** 0.000001
- **Ramp-up pattern:** N/A (categorical indicator)

### #4: M15 Structure (Tier S -- 20.4pp effect)
- **Confidence:** HIGH
- **Signal:** TAKE when m15_structure = BEAR
- **Avoid:** SKIP when m15_structure = BULL
- **Best state:** BEAR = 61.3% WR (310 trades)
- **Worst state:** BULL = 40.9% WR (235 trades)
- **P-value:** 0.000003
- **Ramp-up pattern:** N/A (categorical indicator)

### #5: H1 Structure (Tier S -- 17.6pp effect)
- **Confidence:** HIGH
- **Signal:** TAKE when h1_structure = BEAR
- **Avoid:** SKIP when h1_structure = BULL
- **Best state:** BEAR = 62.3% WR (239 trades)
- **Worst state:** BULL = 44.8% WR (306 trades)
- **P-value:** 0.000066
- **Ramp-up pattern:** N/A (categorical indicator)

---

## Pre-Entry Checklist

Before entering a **Long Rejection** trade:

1. [ ] TAKE when candle_range_pct in Q1 (0.0000 to 0.0857)  (S-tier, +25pp)
2. [ ] TAKE when vol_roc in Q3 (-14.8940 to 5.8057)  (S-tier, +22pp)
3. [ ] TAKE when sma_config = BULL  (S-tier, +21pp)
4. [ ] TAKE when m15_structure = BEAR  (S-tier, +20pp)
5. [ ] TAKE when h1_structure = BEAR  (S-tier, +18pp)

**Minimum:** Pass 4 of 5 for HIGH confidence
**Acceptable:** Pass 3 of 5 for MODERATE confidence
**Skip trade if:** Fail #1 (Candle Range %) AND #2 (Volume ROC)

## Remaining Indicators (Not in Top 5)

| Indicator | Tier | Confidence | Effect | P-Value | Reason |
|-----------|------|------------|--------|---------|--------|
| Price Position | S | HIGH | 16.9pp | 0.001955 | Outside top 5 by ranking |
| SMA Spread % | Rejected | HIGH | 13.9pp | 0.466612 | Not significant (p=0.4666) |
| CVD Slope | Rejected | HIGH | 10.0pp | 0.121804 | Not significant (p=0.1218) |
| SMA Momentum | Rejected | HIGH | 6.5pp | 0.665555 | Not significant (p=0.6656) |
| M5 Structure | Rejected | HIGH | 4.1pp | 0.394998 | Not significant (p=0.3950) |
| Volume Delta (5-bar) | Rejected | HIGH | 3.1pp | 0.950269 | Not significant (p=0.9503) |

# Scorecard: Long Continuation

**Direction:** LONG | **Models:** EPCH1, EPCH3
**Trades:** 43 | **Win Rate:** 48.8% | **Avg R:** 1.44
**Generated:** 2026-02-16 07:30:06

> **LOW DATA WARNING:** This trade type has 43 trades. Results are directional but not yet statistically validated. Indicators marked [LOW_DATA] need more trades to confirm.


---

## Top 5 Indicators

### #1: H1 Structure (Tier C -- 30.7pp effect)
- **Confidence:** HIGH
- **Signal:** TAKE when h1_structure = BEAR
- **Avoid:** SKIP when h1_structure = BULL
- **Best state:** BEAR = 66.7% WR (18 trades)
- **Worst state:** BULL = 36.0% WR (25 trades)
- **P-value:** 0.093845
- **Ramp-up pattern:** N/A (categorical indicator)

### #2: Volume Delta (5-bar) (Tier Rejected -- 49.2pp effect)  [LOW_DATA]
- **Confidence:** LOW_DATA
- **Signal:** TAKE when vol_delta_roll in Q3 (29478.3900 to 133468.1700)
- **Avoid:** SKIP when vol_delta_roll in Q2 (9351.4700 to 22899.5100)
- **Best state:** Q3 (29478.3900 to 133468.1700) = 77.8% WR (9 trades)
- **Worst state:** Q2 (9351.4700 to 22899.5100) = 28.6% WR (7 trades)
- **P-value:** 0.652996
- **Ramp-up pattern:** Winners show lower values in last 10 bars. Divergence: -76505.563481. decelerating (-3958.225024/bar)

### #3: SMA Spread % (Tier Rejected -- 41.7pp effect)  [LOW_DATA]
- **Confidence:** LOW_DATA
- **Signal:** TAKE when sma_spread_pct in Q4 (0.3012 to 0.4573)
- **Avoid:** SKIP when sma_spread_pct in Q5 (0.4847 to 0.9846)
- **Best state:** Q4 (0.3012 to 0.4573) = 75.0% WR (8 trades)
- **Worst state:** Q5 (0.4847 to 0.9846) = 33.3% WR (9 trades)
- **P-value:** 0.855369
- **Ramp-up pattern:** Winners show lower values in last 10 bars. Divergence: -0.034459. accelerating (+0.017600/bar)

### #4: CVD Slope (Tier Rejected -- 41.7pp effect)  [LOW_DATA]
- **Confidence:** LOW_DATA
- **Signal:** TAKE when cvd_slope in Q3 (0.0196 to 0.1705)
- **Avoid:** SKIP when cvd_slope in Q2 (-0.0346 to 0.0155)
- **Best state:** Q3 (0.0196 to 0.1705) = 66.7% WR (9 trades)
- **Worst state:** Q2 (-0.0346 to 0.0155) = 25.0% WR (8 trades)
- **P-value:** 0.761291
- **Ramp-up pattern:** Winners show higher values in last 10 bars. Divergence: +0.031641. decelerating (-0.003963/bar)

### #5: Price Position (Tier Rejected -- 35.9pp effect)  [LOW_DATA]
- **Confidence:** LOW_DATA
- **Signal:** TAKE when price_position = ABOVE
- **Avoid:** SKIP when price_position = BTWN
- **Best state:** ABOVE = 55.9% WR (34 trades)
- **Worst state:** BTWN = 20.0% WR (5 trades)
- **P-value:** 0.197001
- **Ramp-up pattern:** N/A (categorical indicator)

---

## Pre-Entry Checklist

Before entering a **Long Continuation** trade:

1. [ ] TAKE when h1_structure = BEAR  (C-tier, +31pp)
2. [ ] TAKE when vol_delta_roll in Q3 (29478.3900 to 133468.1700)  (Rejected-tier, +49pp) [LOW_DATA]
3. [ ] TAKE when sma_spread_pct in Q4 (0.3012 to 0.4573)  (Rejected-tier, +42pp) [LOW_DATA]
4. [ ] TAKE when cvd_slope in Q3 (0.0196 to 0.1705)  (Rejected-tier, +42pp) [LOW_DATA]
5. [ ] TAKE when price_position = ABOVE  (Rejected-tier, +36pp) [LOW_DATA]

**Minimum:** Pass 4 of 5 for HIGH confidence
**Acceptable:** Pass 3 of 5 for MODERATE confidence
**Skip trade if:** Fail #1 (H1 Structure) AND #2 (Volume Delta (5-bar))

## Remaining Indicators (Not in Top 5)

| Indicator | Tier | Confidence | Effect | P-Value | Reason |
|-----------|------|------------|--------|---------|--------|
| Volume ROC | Rejected | LOW_DATA | 33.3pp | 0.855369 | Not significant (p=0.8554) |
| Candle Range % | Rejected | LOW_DATA | 29.2pp | 0.855369 | Not significant (p=0.8554) |
| SMA Configuration | Rejected | HIGH | 24.7pp | 0.264789 | Not significant (p=0.2648) |
| M5 Structure | Rejected | HIGH | 18.2pp | 0.444455 | Not significant (p=0.4445) |
| SMA Momentum | Rejected | LOW_DATA | 17.1pp | 0.729984 | Not significant (p=0.7300) |
| M15 Structure | Rejected | HIGH | 2.6pp | 1.000000 | Not significant (p=1.0000) |

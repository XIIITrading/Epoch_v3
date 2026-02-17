# Scorecard: Short Rejection

**Direction:** SHORT | **Models:** EPCH2, EPCH4
**Trades:** 492 | **Win Rate:** 58.3% | **Avg R:** 1.36
**Generated:** 2026-02-16 07:30:06

---

## Top 5 Indicators

### #1: M5 Structure (Tier S -- 29.6pp effect)
- **Confidence:** HIGH
- **Signal:** TAKE when m5_structure = BULL
- **Avoid:** SKIP when m5_structure = BEAR
- **Best state:** BULL = 74.3% WR (226 trades)
- **Worst state:** BEAR = 44.7% WR (266 trades)
- **P-value:** 0.000000
- **Ramp-up pattern:** N/A (categorical indicator)

### #2: CVD Slope (Tier S -- 27.4pp effect)
- **Confidence:** HIGH
- **Signal:** TAKE when cvd_slope in Q1 (-0.5586 to -0.1695)
- **Avoid:** SKIP when cvd_slope in Q4 (0.0678 to 0.2224)
- **Best state:** Q1 (-0.5586 to -0.1695) = 71.7% WR (99 trades)
- **Worst state:** Q4 (0.0678 to 0.2224) = 44.3% WR (97 trades)
- **P-value:** 0.000044
- **Ramp-up pattern:** Winners show higher values in last 10 bars. Divergence: +0.029887. accelerating (+0.010183/bar)

### #3: Price Position (Tier C -- 14.2pp effect)
- **Confidence:** HIGH
- **Signal:** TAKE when price_position = BTWN
- **Avoid:** SKIP when price_position = BELOW
- **Best state:** BTWN = 66.4% WR (116 trades)
- **Worst state:** BELOW = 52.2% WR (159 trades)
- **P-value:** 0.062263
- **Ramp-up pattern:** N/A (categorical indicator)

### #4: SMA Configuration (Tier C -- 9.0pp effect)
- **Confidence:** HIGH
- **Signal:** TAKE when sma_config = BULL
- **Avoid:** SKIP when sma_config = BEAR
- **Best state:** BULL = 62.6% WR (257 trades)
- **Worst state:** BEAR = 53.6% WR (235 trades)
- **P-value:** 0.052679
- **Ramp-up pattern:** N/A (categorical indicator)

### #5: Volume Delta (5-bar) (Tier Rejected -- 31.4pp effect)
- **Confidence:** HIGH
- **Signal:** TAKE when vol_delta_roll in Q2 (-67814.5900 to -19692.3900)
- **Avoid:** SKIP when vol_delta_roll in Q3 (-17240.2600 to 33157.4700)
- **Best state:** Q2 (-67814.5900 to -19692.3900) = 71.4% WR (98 trades)
- **Worst state:** Q3 (-17240.2600 to 33157.4700) = 40.0% WR (100 trades)
- **P-value:** 0.148647
- **Ramp-up pattern:** Winners show higher values in last 10 bars. Divergence: +34367.330329. decelerating (-7707.671369/bar)

---

## Pre-Entry Checklist

Before entering a **Short Rejection** trade:

1. [ ] TAKE when m5_structure = BULL  (S-tier, +30pp)
2. [ ] TAKE when cvd_slope in Q1 (-0.5586 to -0.1695)  (S-tier, +27pp)
3. [ ] TAKE when price_position = BTWN  (C-tier, +14pp)
4. [ ] TAKE when sma_config = BULL  (C-tier, +9pp)
5. [ ] TAKE when vol_delta_roll in Q2 (-67814.5900 to -19692.3900)  (Rejected-tier, +31pp)

**Minimum:** Pass 4 of 5 for HIGH confidence
**Acceptable:** Pass 3 of 5 for MODERATE confidence
**Skip trade if:** Fail #1 (M5 Structure) AND #2 (CVD Slope)

## Remaining Indicators (Not in Top 5)

| Indicator | Tier | Confidence | Effect | P-Value | Reason |
|-----------|------|------------|--------|---------|--------|
| SMA Spread % | Rejected | HIGH | 19.7pp | 0.551219 | Not significant (p=0.5512) |
| Candle Range % | Rejected | HIGH | 18.7pp | 0.745073 | Not significant (p=0.7451) |
| SMA Momentum | Rejected | HIGH | 14.5pp | 0.306564 | Not significant (p=0.3066) |
| Volume ROC | Rejected | HIGH | 10.9pp | 0.323955 | Not significant (p=0.3240) |
| M15 Structure | Rejected | HIGH | 2.5pp | 0.635108 | Not significant (p=0.6351) |
| H1 Structure | Rejected | HIGH | 1.9pp | 0.751108 | Not significant (p=0.7511) |

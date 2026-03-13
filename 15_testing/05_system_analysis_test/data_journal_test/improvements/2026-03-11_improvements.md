# Improvements Log — 2026-03-11

> Data: 3,999 trades | 47 zone days | 905 zone-matched trades
> Date Range: 2025-12-15 to 2026-03-11

---

## IMP-001: Zone Score Floor Filter

**Source:** Step 2 — Zone Quality vs Outcomes
**Finding:** Zones below L3 (score < 6.0) are net losers at 22.53% WR / -0.20R. Zones at L3+ run 45-59% WR / +0.73-1.18R.
**Data:**

| Tier | Trades | Win Rate | Avg R |
|------|--------|----------|-------|
| T3 (L4-L5) | 226 | 52.65% | +0.97R |
| T2 (L3) | 376 | 45.48% | +0.73R |
| T1 (L1-L2) | 303 | 25.08% | -0.10R |

**Proposed Change:** Hard floor — exclude zones with score < 6.0 from setup generation.
**Impact Estimate:** Removes ~33% of zone-matched trades (303/905), all with negative expectancy.
**Confidence:** HIGH (905 trades, clear monotonic relationship)
**Status:** IMPLEMENTED (2026-03-11)
**Implementation:** Added `MIN_ZONE_SCORE = 6.0` in `weights.py`. Zone filter Step 1.5 in `calculators/zone_filter.py` removes all zones below L3 before proximity/overlap processing. Affects filtered zones, Primary/Secondary setups, and Supabase export.

---

## IMP-002: L4 Sweet Spot (Score 9.0-12.0)

**Source:** Step 2 — Zone Score Ranges
**Finding:** L4 (score 9-12) has the highest win rate at 59.35% / +0.80R. L5 (12+) drops to 44.66% — possible overfitting or small sample.
**Data:**

| Score Range | Trades | Win Rate | Avg R |
|-------------|--------|----------|-------|
| 9-12 (L4) | 123 | 59.35% | +0.80R |
| 12+ (L5) | 103 | 44.66% | +1.18R |

**Proposed Change:** Flag L4 zones as highest conviction. Investigate why L5 WR drops (higher R suggests they win big when they win).
**Confidence:** MEDIUM (123 trades for L4, 103 for L5 — need more data)
**Status:** PROPOSED

---

## IMP-003: Overlap Count 6-7 Optimal Range

**Source:** Step 2 — Confluence Density
**Finding:** 7 overlaps = 55.66% WR / +1.80R (106 trades). Below 4 overlaps drops sharply. Above 9 gets noisy.
**Data:**

| Overlaps | Trades | Win Rate | Avg R |
|----------|--------|----------|-------|
| 2 | 176 | 17.05% | -0.57R |
| 4 | 114 | 38.60% | +0.37R |
| 6 | 223 | 44.84% | +0.83R |
| 7 | 106 | 55.66% | +1.80R |

**Proposed Change:** Prefer zones with 5-7 overlaps. Flag zones with < 4 overlaps as low confidence.
**Confidence:** MEDIUM (trend is clear but not perfectly monotonic)
**Status:** PROPOSED

---

## IMP-004: Structure Confluence Adds Edge

**Source:** Step 2 — Confluence Type Analysis
**Finding:** Zones with structure-level confluences outperform: 46.36% WR vs 37.48% (+8.88pp).
**Data:**

| Structure | Trades | Win Rate | Avg R |
|-----------|--------|----------|-------|
| Has Structure | 302 | 46.36% | +0.94R |
| No Structure | 603 | 37.48% | +0.30R |

**Proposed Change:** Weight structure-level confluences higher in zone scoring. Prioritize zones that include strong/weak high references.
**Confidence:** HIGH (905 trades, clear split)
**Status:** PROPOSED

---

## IMP-005: Options/Camarilla Confluence Data Gap

**Source:** Step 2 — Confluence Type Analysis
**Finding:** Zero zones matched for options or camarilla_monthly confluence keywords. These confluence types are either not being stored in the `confluences` text field or use different naming.
**Proposed Change:** Audit the zone pipeline to verify options and cam_monthly confluences are persisted in the `confluences` field. If they are scored but not named, update the text storage.
**Confidence:** N/A (data quality issue, not a performance finding)
**Status:** RESOLVED (2026-03-11) — Not a bug. Confluences use abbreviated display names (`OP1`-`OP10` for options, `M S3`/`M R6` etc. for monthly camarilla) per `ZONE_NAME_MAP` in `weights.py`. The analysis script searched for literal "options" and "camarilla_monthly" which don't appear. Fix belongs in the analysis query, not the pipeline.

---

## IMP-006: SECONDARY Zones Outperform PRIMARY

**Source:** Step 3 — Market Structure
**Finding:** Counter-trend (SECONDARY) setups outperform with-trend (PRIMARY): 48.74% / +0.90R vs 45.90% / +0.69R.
**Data:**

| Zone Type | Trades | Win Rate | Avg R |
|-----------|--------|----------|-------|
| SECONDARY | 2,376 | 48.74% | +0.90R |
| PRIMARY | 1,623 | 45.90% | +0.69R |

**Proposed Change:** Do NOT filter out secondary zones. They are additive. Consider equal weighting or slight preference for secondary setups.
**Confidence:** HIGH (3,999 trades, statistically meaningful gap)
**Status:** PROPOSED

---

## IMP-007: EPCH2 Model Underperformance

**Source:** Step 3 — Direction x Model Matrix
**Finding:** EPCH2 is the weakest model across both directions. LONG EPCH2: 44.68% / +0.78R. SHORT EPCH2: 46.79% / +0.55R. EPCH4 and EPCH3 outperform.
**Data:**

| Model | Trades | Avg WR | Avg R |
|-------|--------|--------|-------|
| EPCH1 | 120 | 49.2% | +0.85R |
| EPCH2 | 1,503 | 45.6% | +0.68R |
| EPCH3 | 186 | 47.3% | +0.89R |
| EPCH4 | 2,190 | 48.9% | +0.90R |

**Proposed Change:** Deprioritize EPCH2 entries or require higher zone quality for EPCH2 triggers. EPCH4 should be the default preferred model.
**Confidence:** HIGH (1,503 EPCH2 trades — large sample, consistent underperformance)
**Status:** PROPOSED

---

## IMP-008: ATR Floor Filter ($5+ ATR)

**Source:** Step 4 — D1 ATR Ranges
**Finding:** Sub-$5 ATR tickers underperform significantly. $3-5 ATR: 29.57% WR / +0.05R. $1-3 ATR: 42.49% / +0.51R. Above $5: ~49% WR / +0.85R.
**Data:**

| ATR Range | Trades | Win Rate | Avg R |
|-----------|--------|----------|-------|
| $10+ | 1,395 | 48.96% | +0.83R |
| $5-10 | 2,185 | 48.79% | +0.90R |
| $3-5 | 186 | 29.57% | +0.05R |
| $1-3 | 233 | 42.49% | +0.51R |

**Proposed Change:** Hard floor — exclude tickers with D1 ATR < $5.00 from the screener.
**Impact Estimate:** Removes ~10% of trades (419/3,999), mostly low-expectancy.
**Confidence:** HIGH (clear breakpoint at $5 ATR)
**Status:** PROPOSED

---

## IMP-009: Price Floor Filter ($100+)

**Source:** Step 4 — Price Level
**Finding:** Sub-$50 tickers are losers. $500+ stocks dominate at 61.16% WR / +1.41R. Clear performance gradient by price.
**Data:**

| Price | Trades | Win Rate | Avg R |
|-------|--------|----------|-------|
| $500+ | 739 | 61.16% | +1.41R |
| $200-500 | 2,047 | 45.58% | +0.66R |
| $100-200 | 770 | 44.81% | +0.92R |
| $50-100 | 297 | 42.42% | +0.48R |
| < $50 | 146 | 32.19% | +0.03R |

**Proposed Change:** Soft floor at $100 (flag below), hard floor at $50 (exclude). Prioritize $200+ tickers.
**Confidence:** HIGH (clear gradient, large samples per bucket)
**Status:** PROPOSED

---

## IMP-010: Overnight Range Sweet Spot (1.0-1.5 ATR)

**Source:** Step 4 — Overnight Range
**Finding:** 1.0-1.5 ATR overnight range is the best bucket: 63.00% WR / +1.93R. Wide gaps (1.5+ ATR) hurt. Your picks average 1.19 — right in the sweet spot.
**Data:**

| O/N Range | Trades | Win Rate | Avg R |
|-----------|--------|----------|-------|
| 1.0-1.5 ATR | 100 | 63.00% | +1.93R |
| 0.5-1.0 ATR | 976 | 47.75% | +1.05R |
| < 0.5 ATR | 2,519 | 48.23% | +0.74R |
| 1.5+ ATR | 404 | 39.36% | +0.43R |

**Proposed Change:** Flag tickers with 1.0-1.5 ATR overnight range as high priority. Warn on 1.5+ ATR gaps.
**Confidence:** MEDIUM (100 trades in sweet spot — directionally strong but needs more data)
**Status:** PROPOSED

---

## IMP-011: Normalized Volatility — Moderate Vol Wins

**Source:** Step 4 — ATR % of Price
**Finding:** 1-2% ATR/price (Normal Vol) is the best at 55.60% / +1.25R. Your picks average 5.54% — you're over-indexing on high vol.
**Data:**

| ATR/Price | Trades | Win Rate | Avg R |
|-----------|--------|----------|-------|
| 1-2% | 937 | 55.60% | +1.25R |
| 3-5% | 993 | 52.17% | +0.87R |
| 5%+ | 1,530 | 42.22% | +0.64R |

**Proposed Change:** Add ATR/price as a screening metric. Prefer 1-3% range. Flag 5%+ as high risk.
**Confidence:** HIGH (937+ trades per bucket, clear inverse relationship)
**Status:** PROPOSED

---

## IMP-012: PDC Proximity — Farther is Better

**Source:** Step 4 — Proximity to Prior Day Close
**Finding:** Trades farther from prior day close win more. 0.5-1 ATR from PDC: 54.84% / +1.24R vs < 0.5 ATR: 45.99% / +0.73R.
**Data:**

| Proximity | Trades | Win Rate | Avg R |
|-----------|--------|----------|-------|
| 2+ ATR | 30 | 73.33% | +2.23R |
| 1-2 ATR | 52 | 65.38% | +1.46R |
| 0.5-1 ATR | 516 | 54.84% | +1.24R |
| < 0.5 ATR | 3,401 | 45.99% | +0.73R |

**Proposed Change:** Add PDC distance as a screening flag. Prefer entries 0.5+ ATR from prior day close.
**Confidence:** MEDIUM (top buckets have small samples — 30 and 52 trades — but gradient is monotonic)
**Status:** PROPOSED

---

## Summary: Priority Implementation Order

| Priority | IMP | Change | Impact | Confidence |
|----------|-----|--------|--------|------------|
| 1 | IMP-001 | Zone score floor >= 6.0 | Remove 33% of losing trades | IMPLEMENTED |
| 2 | IMP-008 | ATR floor $5+ | Remove 10% low-expectancy | HIGH |
| 3 | IMP-009 | Price floor $100+ | Clear performance gradient | HIGH |
| 4 | IMP-007 | Deprioritize EPCH2 | Weakest model by WR and R | HIGH |
| 5 | IMP-011 | ATR/price 1-3% preferred | Best risk-adjusted bucket | HIGH |
| 6 | IMP-004 | Weight structure confluence | +8.88pp WR edge | HIGH |
| 7 | IMP-006 | Keep SECONDARY setups | Counter-trend adds value | HIGH |
| 8 | IMP-010 | O/N range 1.0-1.5 ATR flag | Best single bucket | MEDIUM |
| 9 | IMP-012 | PDC proximity 0.5+ ATR | Monotonic gradient | MEDIUM |
| 10 | IMP-003 | Overlap 5-7 preferred | Trend visible, not linear | MEDIUM |
| 11 | IMP-002 | L4 as highest conviction | L5 WR drop needs investigation | MEDIUM |
| 12 | IMP-005 | Audit confluence text storage | Data gap, not performance | RESOLVED |

# Weekly Aggregation Report

**Week**: 2026-01-26 to 2026-01-30
**Generated**: 2026-02-01T07:29:34.039678
**Win Condition**: m5_atr (ATR(14) x 1.1, close-based)
**Data Source**: trades_m5_r_win (sole source of truth)

---

## Weekly Summary

| Metric | Value |
|--------|-------|
| Total Trades | 2307 |
| Winners | 1180 |
| Win Rate | 51.1% |
| Total R | +1239.89 |
| Expectancy | 0.537R | 

---

## Daily Breakdown

| Date | Trades | Winners | Win Rate | Total R | Avg R |
|------|--------|---------|----------|---------|-------|
| 2026-01-26 | 273 | 182 | 66.7% | +213.31 | +0.781 |
| 2026-01-27 | 283 | 192 | 67.8% | +300.03 | +1.060 |
| 2026-01-28 | 455 | 188 | 41.3% | +116.08 | +0.255 |
| 2026-01-29 | 814 | 384 | 47.2% | +249.66 | +0.307 |
| 2026-01-30 | 482 | 234 | 48.5% | +360.81 | +0.749 |

---

## Model Performance

| Model | Trades | Winners | Win Rate | Total R |
|-------|--------|---------|----------|---------|
| EPCH1 | 84 | 48 | 57.1% | +55.39 |
| EPCH2 | 951 | 538 | 56.6% | +697.22 |
| EPCH3 | 93 | 44 | 47.3% | +44.23 |
| EPCH4 | 1179 | 550 | 46.6% | +443.06 |

---

## Edge Effectiveness: H1 Structure

| H1 Structure | Trades | Winners | Win Rate | Avg R |
|-------------|--------|---------|----------|-------|
| BEAR | 391 | 218 | 55.8% | +0.766 |
| BULL | 410 | 213 | 52.0% | +0.399 |
| NEUTRAL | 1506 | 749 | 49.7% | +0.516 |

---

## Health Score Distribution

| Health Tier | Trades | Winners | Win Rate | Avg R |
|-------------|--------|---------|----------|-------|
| CRITICAL (0-3) | 945 | 455 | 48.1% | +0.362 |
| MODERATE (6-7) | 557 | 365 | 65.5% | +1.250 |
| STRONG (8-10) | 26 | 21 | 80.8% | +1.500 |
| WEAK (4-5) | 779 | 339 | 43.5% | +0.208 |

---

## Validated Edges Status

| Edge | Expected Effect | This Week Status |
|------|----------------|------------------|
| H1 Structure NEUTRAL | +36.0pp | Review in audit |
| Absorption Zone Skip | -17.0pp | Review in audit |
| Volume Delta Paradox | +13.0pp | Review in audit |

---

## Notes

- All outcomes from `trades_m5_r_win.is_winner` (sole source)
- Edge criteria: p < 0.05, effect > 3.0pp
- Use this report with `/prompts/edge_audit.md` for weekly Claude analysis

---

*Generated: 2026-02-01T07:29:34.039678*

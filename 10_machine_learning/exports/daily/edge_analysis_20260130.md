# Edge Analysis Report

**Date**: 2026-01-30
**Analysis Period**: 2025-12-31 to 2026-01-30
**Total Trades**: 4800
**Baseline Win Rate**: 53.7%
**Average R**: 0.746
**Data Source**: trades_m5_r_win (sole source of truth)

---

## Validated Edges

| Edge | Effect Size | Confidence | Action |
|------|-------------|------------|--------|
| H1 Structure NEUTRAL | +36.0pp | HIGH | TRADE when H1 = NEUTRAL |
| Absorption Zone Skip | -17.0pp | HIGH | SKIP - do not trade |
| Volume Delta Paradox | +13.0pp | MEDIUM | Trade against order flow |


---

## Edge Criteria

- **Statistical Significance**: p-value < 0.05
- **Practical Significance**: Effect size > 3.0pp
- **Minimum Sample (MEDIUM)**: 30 trades
- **Minimum Sample (HIGH)**: 100 trades

---

## Notes

- Win condition: m5_atr stop (ATR(14) x 1.1, close-based)
- All outcomes from `trades_m5_r_win.is_winner` (sole source)
- Effect sizes measured in percentage points (pp) above baseline

---

*Generated: 2026-02-01T07:29:33.510255*

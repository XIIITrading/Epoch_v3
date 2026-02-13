# System Edge Refinement Log

> Living document tracking approved refinements to the EPOCH trading system edge model.
> Updated weekly as part of the ML analysis cycle.
> Source of truth: `trades_m5_r_win` | Analysis engine: Claude Code

---

## Approved Refinements

### R001 — Rename Health Score to Continuation Score (CONT)
**Date**: 2026-02-01
**Status**: APPROVED
**Rationale**: The existing 10-factor health score directly correlates with continuation trade performance. When indicators align (high score), continuation entries (EPCH1/EPCH3) dramatically outperform rejection entries. The score measures "how aligned is everything in one direction" — which is the definition of a continuation setup.

**Key evidence** (30-day window, 47 trades with score >= 8):
- Continuation models: 81.8% WR (+28.1pp vs baseline), Avg R +1.455
- Rejection models: 69.4% WR (+15.7pp vs baseline), Avg R +1.131
- SHORT trades with STRONG score: 87.0% WR (+32.5pp)

**Implementation**: Overlay in 10_machine_learning only. The database field `health_score` and `entry_indicators` table remain unchanged. The ML module interprets health_score as CONT score.

**What this changes for live trading**: When the score is high (8+), favor continuation entries. The score is telling you "everything is aligned in one direction" — that's a continuation signal, not just a generic "good setup" signal.

---

### R002 — M15 Structure as Primary Filter
**Date**: 2026-02-01
**Status**: APPROVED
**Rationale**: M15 structure is the single strongest directional filter in the system.
- M15 BULL: 59.6% WR, +5.9pp, 1,574 trades, p < 0.0001 (HIGH confidence)
- M15 BEAR: 45.1% WR, -8.6pp, 1,553 trades, p < 0.0001 (HIGH confidence)

The spread between BULL and BEAR is 14.5 percentage points — the widest of any single indicator.

**What this changes for live trading**: M15 structure should be the first thing you check. If M15 is BEAR, you need strong offsetting factors to take the trade. If M15 is BULL, you have structural support.

---

### R003 — Retire Original Three Validated Edges
**Date**: 2026-02-01
**Status**: PENDING REVIEW
**Rationale**: All three original validated edges (H1 NEUTRAL +36pp, Absorption Zone Skip -17pp, Volume Delta Paradox +13pp) were validated against the old `trades` table win logic. Against `trades_m5_r_win` (canonical):
- H1 NEUTRAL: INCONCLUSIVE (-1.0pp, p=0.37)
- Absorption Zone Skip: DEGRADED (sign reversed, now +7.1pp)
- Volume Delta Paradox: DEGRADED (sign reversed, now -2.0pp)

**Action needed**: Remove these from config.py VALIDATED_EDGES. They are artifacts of the old win calculation.

---

### R004 — Build CONT/REJECT Scoring Overlay
**Date**: 2026-02-01
**Status**: IN PROGRESS
**Rationale**: The existing health score tells you how many indicators are "healthy" (aligned with trade direction). But it doesn't distinguish between indicators that signal continuation vs rejection. The new model interprets each indicator's behavior pattern to output:
- CONT score: How many indicators suggest price will continue through the zone
- REJECT score: How many indicators suggest price will reject from the zone

**Reference**: See `docs/indicator_playbook.md` for the full signal mapping.

**Implementation approach**: Analysis overlay in 10_machine_learning. Raw indicator values from `entry_indicators` are re-interpreted through the CONT/REJECT lens. The database health_score field is unchanged.

---

## Weekly Update Log

### Week of 2026-01-27

**Cycle run**: 2026-02-01
**Baseline**: 4,800 trades | 53.7% WR | +0.746R avg | 1.886R std

**Edge health check**:
| Edge | Status | Stored | Current |
|------|--------|--------|---------|
| H1 Structure NEUTRAL | INCONCLUSIVE | +36.0pp | -1.0pp |
| Absorption Zone Skip | DEGRADED | -17.0pp | +7.1pp |
| Volume Delta Paradox | DEGRADED | +13.0pp | -2.0pp |

**New edges discovered**: 9 (all statistically significant)
| Edge | Effect | Confidence | Trades |
|------|--------|------------|--------|
| Continuation Score STRONG (8-10) | +18.6pp | MEDIUM | 47 |
| Continuation Score MODERATE (6-7) | +9.5pp | HIGH | 996 |
| M15 Structure BEAR | -8.6pp | HIGH | 1,553 |
| Stop Distance TIGHT (<0.12%) | +7.0pp | HIGH | 275 |
| M15 Structure BULL | +5.9pp | HIGH | 1,574 |
| H1 Structure BEAR | +5.4pp | HIGH | 745 |
| Continuation Score WEAK (4-5) | -3.8pp | HIGH | 1,677 |
| SMA Alignment BULL | -3.8pp | HIGH | 2,324 |
| SMA Alignment BEAR | +3.5pp | HIGH | 2,476 |

**Deep dive — Continuation Score STRONG by sub-group**:
| Sub-group | Trades | WR | Effect vs baseline |
|-----------|--------|----|--------------------|
| SHORT | 23 | 87.0% | +32.5pp |
| LONG | 24 | 58.3% | +5.5pp |
| CONTINUATION model | 11 | 81.8% | +28.1pp |
| REJECTION model | 36 | 69.4% | +15.7pp |
| PRIMARY zone | 33 | 72.7% | +17.6pp |
| SECONDARY zone | 14 | 71.4% | +19.4pp |

**Key insight**: The continuation score's strongest effect is on SHORT trades with continuation models. This suggests the score is most predictive when everything aligns bearish — possibly because bearish alignment is less ambiguous than bullish in the current market environment.

**Pending actions**:
- Remove 3 degraded original edges from config.py
- Review 9 new edges for approval
- Build CONT/REJECT scoring overlay
- Begin documenting indicator behavior patterns in playbook

---

*This document is updated weekly. Each cycle appends a new weekly entry below.*
*Previous weeks remain for historical reference.*

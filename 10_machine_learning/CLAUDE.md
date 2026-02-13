# EPOCH 2.0 Trading System - Claude Code Context

> **Module**: 10_machine_learning
> **Purpose**: Closed-loop ML system for continuous edge improvement
> **Orchestrator**: Claude Code (autonomous analysis engine)
> **Last Updated**: 2026-02-01

---

## Architecture: Closed-Loop ML System

```
EXPORT -> VALIDATE-EDGES -> ANALYZE -> HYPOTHESIZE -> TEST -> UPDATE STATE
  ^                                                              |
  +--------------------------------------------------------------+
```

### Autonomy Model
| Level | Actions | Trigger |
|-------|---------|---------|
| **Autonomous** | Export, analyze, hypothesize, test, validate, status | Claude Code runs directly |
| **Flag + Pause** | New validated edge, degraded edge | Written to pending_edges.json |
| **Human Required** | approve-edge, remove-edge | User command only |

---

## Commands Reference

```bash
# Data Export
python scripts/run_ml_workflow.py daily                      # Export today's trades
python scripts/run_ml_workflow.py weekly                     # Weekly aggregation
python scripts/run_ml_workflow.py full                       # Both daily + weekly

# Analysis (Autonomous)
python scripts/run_ml_workflow.py validate-edges             # Check validated edge health
python scripts/run_ml_workflow.py analyze                    # Full system analysis + indicator scan
python scripts/run_ml_workflow.py hypothesize                # Discover + auto-test new edges
python scripts/run_ml_workflow.py test-hypothesis H001       # Test specific hypothesis
python scripts/run_ml_workflow.py cycle                      # Full closed-loop (all of the above)
python scripts/run_ml_workflow.py status                     # Print system status

# Human Approval (Modifies config.py)
python scripts/run_ml_workflow.py approve-edge H001          # Promote validated edge
python scripts/run_ml_workflow.py remove-edge "Edge Name"    # Remove degraded edge

# Options
--days 30          # Lookback period (default: 30)
--start 2026-01-01 # Override start date
--end 2026-01-31   # Override end date
--date 2026-01-31  # Target date for export
```

---

## Win Condition (CANONICAL)

| Parameter | Value | Source |
|-----------|-------|--------|
| **Table** | `trades_m5_r_win` | Sole source of truth |
| **Stop Type** | M5 ATR(14) x 1.1 | Close-based trigger |
| **Win** | MFE >= 1R before stop hit | Price-based MFE check |
| **Loss** | Stop hit before reaching 1R | Close-based stop trigger |

**Critical**: Always use `trades_m5_r_win.is_winner`. Never use `trades.is_winner`.

---

## Entry Models

| Model | Type | Zone | Description |
|-------|------|------|-------------|
| EPCH1 | Continuation | Primary | Price traverses through primary zone |
| EPCH2 | Rejection | Primary | Price wicks into zone, closes outside |
| EPCH3 | Continuation | Secondary | Price traverses through secondary zone |
| EPCH4 | Rejection | Secondary | Price wicks into zone, closes outside |

---

## Statistical Framework

**Edge Criteria** (all three required):
- p-value < 0.05 (statistical significance via chi-squared)
- Effect size > 3.0pp (practical significance)
- Sample >= 30 trades (MEDIUM) / >= 100 trades (HIGH)

**Edge Health Classification**:
- **HEALTHY**: Within 5pp of stored value, same sign
- **WEAKENING**: Same sign but >5pp lower than stored
- **DEGRADED**: Sign reversed or p > 0.05
- **INCONCLUSIVE**: p > 0.20

**Hypothesis Lifecycle**: PROPOSED -> TESTING -> VALIDATED / REJECTED / INCONCLUSIVE

---

## State Files

### Machine-Readable (Source of Truth)
```
state/system_state.json         # Baseline metrics, edge health, drift alerts
state/hypothesis_tracker.json   # All hypotheses with test results
state/pending_edges.json        # Edges awaiting human approval
state/changelog/                # Dated JSON entries
```

### Auto-Generated (Human-Readable)
```
state/system_state.md           # Generated from system_state.json
state/hypothesis_tracker.md     # Generated from hypothesis_tracker.json
```

### Analysis Archive
```
analysis/edge_audits/           # Edge validation & analysis reports
analysis/hypotheses/            # Individual hypothesis test results
analysis/patterns/              # Pattern discovery reports
```

### Exports
```
exports/daily/trades_YYYYMMDD.json       # Trade data
exports/daily/edge_analysis_YYYYMMDD.md  # Edge analysis
exports/daily/system_metrics_YYYYMMDD.json # System metrics
exports/weekly/weekly_report_YYYYMMDD.md  # Weekly summary
```

---

## Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/run_ml_workflow.py` | Master orchestrator (all modes) |
| `scripts/export_for_claude.py` | Data export from trades_m5_r_win |
| `scripts/weekly_aggregation.py` | Weekly summary generation |
| `scripts/edge_validator.py` | Validates VALIDATED_EDGES health |
| `scripts/analysis_engine.py` | Baseline + indicator scan + drift detection |
| `scripts/hypothesis_engine.py` | Discover, propose, test hypotheses |
| `scripts/statistical_tests.py` | Chi-squared, Fisher's exact, effect size |
| `scripts/state_manager.py` | JSON state management + MD generation |

---

## Config.py Key Sections

- **VALIDATED_EDGES**: Currently validated edges (modified by approve/remove)
- **EDGE_DEFINITIONS**: SQL queries for validating each edge
- **INDICATOR_SCAN_QUERIES**: SQL queries for each indicator column (hypothesis discovery)
- **EDGE_CRITERIA**: Statistical thresholds (p < 0.05, effect > 3pp, N >= 30)
- **CANONICAL_OUTCOME**: Win condition definition

---

## Database Quick Reference

### Primary Tables
| Table | Purpose |
|-------|---------|
| `trades_m5_r_win` | **SOLE SOURCE** - canonical outcomes |
| `entry_indicators` | Indicator snapshots at trade entry |
| `mfe_mae_potential` | Price excursion data |

### SQL Views (installed in Supabase)
| View | Purpose |
|------|---------|
| `v_claude_trade_export` | Pre-joined trade + indicators + MFE/MAE |
| `v_edge_summary` | Pre-aggregated edge analysis with baseline |

---

## Anti-Patterns

- Using `trades.is_winner` instead of `trades_m5_r_win.is_winner`
- Over-optimizing on samples < 30 trades
- Changing multiple parameters simultaneously
- Approving edges without reviewing test results
- Ignoring DEGRADED flags on validated edges
- Running approve-edge/remove-edge without understanding the data

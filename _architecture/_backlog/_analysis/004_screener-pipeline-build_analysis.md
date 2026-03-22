# Analysis: Screener Pipeline Build — Bucket-Based Pre-Computation & Morning Screener Workflow

**Seed**: `_seeds/004-screener-pipeline-build.md`
**Analyzed**: 2026-03-22
**System Areas**: `01_application/`, `00_shared/indicators/`, `02_dow_ai/entry_qualifier/`, Supabase tables (`bar_data`, `hvn_pocs`, `market_structure`, `zones`, `setups`)
**Data Contract**: `_analysis/003_screener-bucket-audit_analysis.md` (completed 2026-03-22)

---

## 1. Infrastructure Snapshot

### What Exists Today

The screener pipeline lives in `01_application/` and runs as a **single monolithic pass** during pre-market. There is no scheduling — Silva launches the app, enters tickers, and the system computes everything from scratch for each ticker.

**Pipeline Runner** (`core/pipeline_runner.py`, 360 lines):
- Sequential, linear execution: index tickers first, then custom tickers one-by-one
- 6 stages per ticker: Market Structure → Bar Data → HVN → Zones → Filter → Setups
- Each stage is blocking — stage N+1 waits for stage N to finish
- One ticker failing does not stop the pipeline (graceful degradation)
- Progress callback reports 0-100% to the UI

**Supabase Exporter** (`data/supabase_exporter.py`, 720 lines):
- Runs AFTER the pipeline completes — separate step, not interleaved
- Cleans up existing data for the session date, then upserts results
- Uses ON CONFLICT DO UPDATE (idempotent) on all 5 tables
- Still uses raw psycopg2 (V1 debt — not the shared Supabase client)

**Polygon API Clients** (three separate implementations):
- `00_shared/data/polygon/client.py` (346 lines) — shared V2 client, `requests`-based, 0.1s rate limit
- `01_application/data/polygon_client.py` (753 lines) — V1 module client, uses `polygon` SDK, 0.25s rate limit, 5-day chunking for minute bars
- `02_dow_ai/entry_qualifier/data/api_client.py` (359 lines) — lightweight real-time client, `requests`-based, 0.1s rate limit

**Entry Qualifier** (`02_dow_ai/entry_qualifier/`):
- QThread-based polling: one DataWorker per ticker, refreshes every 60 seconds
- Synced to minute boundaries + 5-second delay (waits for Polygon candle finalization)
- Hard limit: `MAX_TICKERS = 4` (in `eq_config.py`)
- All indicators computed in-memory from fresh Polygon data — no Supabase reads
- Smart caching: M1 fresh every cycle, H1 cached per hour, M5/M15 cached per bar period
- Global structure caches shared across all workers (avoids duplicate fetches)

**Key constraint**: Everything is computed live. The pipeline takes 30-45 minutes of active work because monthly OHLC, weekly OHLC, ATR, Camarilla, volume profiles, market structure, zone scoring, and setup generation all happen in one pass every morning.

### What Would Change

This seed introduces **four time-based execution buckets** that split the monolithic pipeline into scheduled components. The core change: most data that doesn't change intraday gets pre-computed into Supabase on a schedule, so the morning session becomes a fast query rather than a full computation.

**New components:**

1. **Bucket Scheduler** — New orchestration layer in `01_application/` that knows which calculations to run based on time-of-day. Could be a single script with mode flags, a cron-triggered runner, or separate scripts per bucket.

2. **Bucket A Runner (Weekly)** — Computes monthly/weekly OHLC, Camarilla, W1/M1 market structure, universe selection, epoch anchor detection. Runs Saturday/Sunday.

3. **Bucket B Runner (Nightly)** — Computes D1 OHLC, all ATR, D1 Camarilla, options OI, PDV volume profile, HVN POCs, D1/H4/H1/M15 market structure, zone scoring, setup generation. Runs after 20:00 ET.

4. **Bucket C Runner (Morning)** — Computes pre-market high/low, pre-market volume profile (PMPOC/PMVAH/PMVAL), current price snapshot. Queries Bucket B data from Supabase. Runs manually when Silva sits down (auto-trigger at 07:30 ET is a future enhancement requiring always-on deployment).

5. **Pre-Market Query Layer** — New Supabase reader that loads all pre-computed data for the screener display. Replaces the current "compute everything" approach with "query everything."

6. **Morning Screener Table** — New app in `01_application/` that displays a one-row-per-ticker summary: RVOL, GAP, D1/H1/M15 structure. Reads from Supabase (Buckets A/B/C). Silva uses this to identify the best 4 candidates.

7. **Chart Visualization with Levels** — The existing visualization workflow in `01_application/` displays charts with all pre-computed levels (Camarilla, HVN POCs, zones, H4 supply/demand zones) already plotted. Silva cycles through candidate tickers, reads the charts, confirms selections, and is ready to trade.

8. **New Calculations** (10 items from Seed 003 audit):
   - C1-C6: Pre-market high/low, PMPOC/PMVAH/PMVAL, current price
   - A5-A6: W1/M1 market structure
   - A7: Universe ticker list (Seed 005 — Silva provides)
   - A8: Epoch anchor auto-detection (existing `find_max_volume_anchor()`)

### What It Connects To

**Upstream**:
- Polygon.io API (bar data for all buckets)
- Supabase (read pre-computed data in Buckets A/B/C)
- Seed 003 audit document (data contract — defines every calculation and its bucket)

**Downstream**:
- `02_dow_ai/entry_qualifier/` — future work: reads pre-computed context, scales to 50 tickers (OUT OF SCOPE for this seed)
- `03_backtest/` — reads zones and setups (no change to contract, same tables)
- `05_system_analysis/` — reads bar_data, market_structure (no change to contract)
- Monday.com board (METHOD.01 items depend on screener functionality)

### End-State Morning Workflow

```
NIGHT BEFORE:
  Silva triggers Bucket B (nightly) → all daily data computed into Supabase
  Silva checks completion before bed

MORNING:
  Silva sits down → triggers Bucket C (morning) → pre-market data added
  Opens screener table → scans RVOL, GAP, D1/H1/M15 structure across universe
  Identifies top candidates → opens chart view with levels + H4 S/D zones
  Cycles through charts → picks best 4 tickers → ready to trade

TARGET: <10 minutes from sitting down to selections made
```

---

## 2. Questions for Silva — RESOLVED (2026-03-22)

### Q1: How should the bucket runners be triggered?
**RESOLVED: Hybrid — manual first.**
CLI with mode flags (`python run_pipeline.py --bucket nightly`). Silva triggers manually to start. Windows Task Scheduler can be added later when the workflow is proven. No auto-scheduling in v1.

### Q2: Should Bucket C (Morning) be automatic or interactive?
**RESOLVED: Manual trigger initially.**
Auto-pull at 07:30 ET is the goal, but requires an always-on deployment (Railway or similar) which does not exist today. Start with manual trigger — Silva runs Bucket C when sitting down at the computer. Auto-scheduling is a future enhancement once infrastructure allows.

### Q3: What are the exact criteria for 50-ticker universe selection?
**RESOLVED: Deferred to Seed 005.**
Universe selection is its own seed. Silva will provide the preliminary ticker list from the daily click-through view. Seed 004 builds the infrastructure that consumes whatever universe list Seed 005 defines.

### Q4: What defines the epoch anchor auto-detection threshold?
**RESOLVED: Use existing "High Volume Day within 6 Months" from the market screener.**
The `max_volume` preset in `market_screener.py` already implements this via `find_max_volume_anchor()`. No new algorithm needed — the bucket runner calls the existing function per ticker in the universe.

### Q5: Should the overnight window be aligned to the pre-market definition?
**RESOLVED: Yes — canonical pre-market window is 16:00–07:30 ET.**
Updated from the Seed 003 definition (was 16:01–07:00 ET). The existing overnight calculation (20:00–12:00 UTC) should be updated to match this canonical window. All Bucket C calculations use 16:00 ET prior day to 07:30 ET current day.

### Q6: For the 50-ticker live scanner, what is the minimum viable display?
**RESOLVED: Screener table with specific columns.**
One-row-per-ticker summary table showing:
- **RVOL** — Relative volume (premarket 04:00–09:00 vs 12-day avg). EXISTS in `structure_screener.py:fetch_minute_data()`
- **GAP** — Gap % from prior close. EXISTS in `structure_screener.py:score_gap()`
- **D1 Structure** — Daily structure classification (Bull/Bear/Out/Neutral + strong/weak). EXISTS in `structure_screener.py:classify_ticker()`
- **H1 Structure** — Hourly direction + strong/weak levels. EXISTS in Bucket B `market_structure`
- **M15 Structure** — 15-min direction + strong/weak levels. EXISTS in Bucket B `market_structure`
- *(Additional columns to be added later per Silva)*

**Key finding**: The existing Structure Screener (`01_application/ui/tabs/structure_screener.py`) already implements all five of these columns. The new app can reuse its calculation functions directly.

### Q7: Should the 50-ticker scanner be a separate application?
**RESOLVED: Yes — separate app in `C:\XIIITradingSystems\Method_v1\01_application\`.**
Entry Qualifier stays as-is for focused 4-ticker deep analysis. The universe scanner is a new application that feeds the morning decision process. Two-tier workflow: Universe Scanner identifies candidates → Silva promotes to Entry Qualifier for live monitoring.

### Q8: Should we build in phases?
**RESOLVED: Yes — phased build confirmed.**
Phase 1 (bucket runners) → Phase 2 (EQ Supabase integration) → Phase 3 (50-ticker scanner app).

### Q9: What's the rollback plan if the nightly runner fails?
**RESOLVED: Manual fallback — run the standard process.**
Silva checks before bed that the nightly run completed. If it failed, runs the standard monolithic pipeline in the morning as-is. No automated alerting needed in v1 — the check is manual.

### Remaining Open Items
- **Seed 005**: Universe ticker list (Silva to provide from daily click-through view)
- **Pre-market window update**: Seed 003 audit references 16:01–07:00 ET — needs correction to 16:00–07:30 ET

---

## 3. Proposed Approach

### Option A: Phased Build — Infrastructure First (Recommended)

Build the bucket scheduling infrastructure in three phases, each delivering standalone value:

**Phase 1: Bucket Runners (A + B + C) — Core Infrastructure**

Refactor the existing pipeline runner to support bucket-mode execution. The 6-stage pipeline already exists — the work is splitting it into time-appropriate groups and adding a scheduling layer.

| Component | What It Does | New Code | Reuses |
|-----------|-------------|----------|--------|
| `bucket_runner.py` | CLI entry point: `--bucket weekly/nightly/morning` | ~150 lines | — |
| `bucket_a_weekly.py` | Runs stages 1-2 for weekly data (M1/W1 OHLC, Camarilla) | ~200 lines | `bar_data.py`, `market_structure.py` |
| `bucket_b_nightly.py` | Runs all 6 stages for daily data | ~250 lines | Entire existing pipeline |
| `bucket_c_morning.py` | Computes pre-market data, queries nightly results | ~300 lines | `volume_profile.py` (shared), new PM calculations |
| `pre_market_query.py` | Reads all pre-computed data from Supabase for display | ~200 lines | — |
| CLI wrapper scripts | `.bat` scripts for each bucket (manual trigger) | 3 files | — |

**Estimated**: ~1,100 lines new code, 2-3 Claude Code sessions

**Phase 2: Morning Screener Table** (separate app in `01_application/`)

New PyQt6 application: one-row-per-ticker screener table that reads pre-computed Supabase data. Silva scans this table to identify the best 4 candidates. Reuses calculation functions from the existing Structure Screener (`structure_screener.py`).

| Component | What It Does | New Code | Reuses |
|-----------|-------------|----------|--------|
| `morning_screener/main.py` | App entry point | ~100 lines | — |
| `morning_screener/ui/screener_table.py` | Table: RVOL, GAP, D1/H1/M15 structure per ticker | ~400 lines | `structure_screener.py` scoring/classification |
| `morning_screener/data/screener_loader.py` | Reads Supabase (Bucket A/B/C data) + computes RVOL/GAP from PM bars | ~300 lines | `pre_market_query.py` from Phase 1 |
| Epoch auto-detection integration | Call existing `find_max_volume_anchor()` per ticker | ~50 lines | `market_screener.py:find_max_volume_anchor()` |

**Key reuse finding**: The existing Structure Screener (`structure_screener.py`) already computes RVOL, GAP, D1 structure classification, and composite scoring. The new app wraps these with a Supabase-first data layer.

**Estimated**: ~850 lines new code, 1-2 Claude Code sessions

**Phase 3: Chart Visualization with Levels**

Ensure the existing visualization workflow in `01_application/` displays charts for each candidate ticker with all pre-computed levels plotted: Camarilla pivots, HVN POCs, scored zones, H4 supply/demand zones, pre-market high/low. Silva cycles through these charts, confirms selections, and is ready to trade.

| Component | What It Does | New Code | Reuses |
|-----------|-------------|----------|--------|
| Chart level overlay | Plot all Supabase-stored levels on TradingView-style charts | TBD — depends on current chart implementation | Existing visualization in `01_application/` |
| H4 supply/demand zones | Overlay H4 structure zones (strong/weak levels from market_structure) | ~100 lines | `market_structure.py` H4 data in Supabase |
| Pre-market levels | Add PMH/PML/PMPOC/PMVAH/PMVAL to chart overlay | ~50 lines | Bucket C data in Supabase |
| Candidate cycling | Navigate between selected tickers from screener table | ~100 lines | — |

**Note**: Phase 3 scope depends on what the current chart/visualization implementation already supports. Needs a detailed review of the existing charting code before estimating.

**Estimated**: ~250-400 lines, 1 Claude Code session (pending chart implementation review)

**Total estimated scope: 4-6 Claude Code sessions across 3 phases**

Trade-offs:
- (+) Each phase delivers value independently
- (+) Phase 1 solves the computation bottleneck (30-45 min → data already in Supabase)
- (+) Phase 2 gives Silva the decision-making tool (screener table)
- (+) Phase 3 completes the end-to-end workflow (charts with levels → ready to trade)
- (+) All work stays within `01_application/` — no Entry Qualifier changes needed
- (+) Entry Qualifier live scaling becomes a separate future seed when ready

### Scope Boundary: What This Seed Does NOT Include

The following are explicitly **out of scope** for Seed 004 and will be addressed in future seeds:

- **Entry Qualifier Supabase integration** — Modifying the EQ to read pre-computed data (future seed)
- **50-ticker live real-time scanning** — Polling M1 bars during market hours for the full universe (future seed)
- **Automated scheduling** — Railway/always-on deployment for auto-triggering buckets (future enhancement)
- **Bucket D (real-time indicators)** — Candle range, volume delta, volume ROC, EMA config remain in the Entry Qualifier as-is

### Recommendation: Option A (Phased Build — Morning Workflow Focus)

All three phases deliver the same end goal: Silva sits down, data is ready, screener table shows candidates, charts have levels plotted, picks 4 tickers, ready to trade. Each phase adds a layer to that workflow.

---

## 4. Impact Map

### New/Modified Tables

| Table | Action | Written By | Read By | Purpose |
|-------|--------|-----------|---------|---------|
| `bar_data` | MODIFY (new columns) | Bucket C runner | 02_dow_ai, 05_system_analysis | Add: `pm_high`, `pm_low`, `pm_poc`, `pm_vah`, `pm_val`, `pm_price` |
| `bar_data` | EXISTING | Bucket A + B runners | All downstream | No schema change — same 67 columns |
| `hvn_pocs` | EXISTING | Bucket B runner | 02_dow_ai, 05_system_analysis | No schema change |
| `market_structure` | MODIFY (new columns) | Bucket A runner | 02_dow_ai, 05_system_analysis | Add: `w1_direction`, `w1_strong`, `w1_weak`, `m1_direction`, `m1_strong`, `m1_weak` |
| `zones` | EXISTING | Bucket B runner | 03_backtest, 02_dow_ai | No schema change |
| `setups` | EXISTING | Bucket B runner | 03_backtest, 02_dow_ai | No schema change |
| `screener_universe` | CREATE | Bucket A runner | All bucket runners | New: `ticker`, `added_date`, `sector`, `avg_volume`, `status`, `epoch_anchor_date` |

### New/Modified Files

| File | Module | Phase | Purpose |
|------|--------|-------|---------|
| `core/bucket_runner.py` | 01_application | 1 | CLI entry point for bucket-mode execution |
| `core/bucket_a_weekly.py` | 01_application | 1 | Weekly computation runner |
| `core/bucket_b_nightly.py` | 01_application | 1 | Nightly computation runner |
| `core/bucket_c_morning.py` | 01_application | 1 | Morning pre-market runner (manual trigger) |
| `data/pre_market_query.py` | 01_application | 1 | Supabase query layer for pre-computed data |
| `calculators/pre_market_calculator.py` | 01_application | 1 | PM high/low, PM volume profile (16:00–07:30 ET) |
| `scripts/run_weekly.bat` | 01_application | 1 | CLI wrapper for Bucket A |
| `scripts/run_nightly.bat` | 01_application | 1 | CLI wrapper for Bucket B |
| `scripts/run_morning.bat` | 01_application | 1 | CLI wrapper for Bucket C |
| `morning_screener/main.py` | 01_application | 2 | Morning screener app entry point |
| `morning_screener/ui/screener_table.py` | 01_application | 2 | Table: RVOL, GAP, D1/H1/M15 structure per ticker |
| `morning_screener/data/screener_loader.py` | 01_application | 2 | Reads Supabase + computes RVOL/GAP from PM bars |
| Chart level overlay (TBD) | 01_application | 3 | Plot all levels on charts for candidate tickers |

### Architecture Document Updates Required

- [ ] SYSTEM_MAP.md: Add bucket scheduler and morning screener app to 01_application description
- [ ] DATA_FLOW.md: Add `screener_universe` table, add `pm_*` columns to bar_data, add `w1_*/m1_*` columns to market_structure, document bucket timing
- [ ] PIPELINE.md: Major rewrite — replace single Phase 1 with three timed buckets (A/B/C), add morning screener workflow, update dependency graph
- [ ] 01_application/CLAUDE.md: Add bucket runner architecture, morning screener app, new calculators, CLI scripts

---

## 5. Dependencies & Sequencing

### Must Exist First

- **Seed 003 (Screener Bucket Audit)** — COMPLETE. Provides the data contract (45 calculations, bucket assignments, field inventory). This analysis references it directly.
- **Seed 002 (Architecture Baseline Audit)** — Batch 1 DONE. The 01_application CLAUDE.md update from Batch 2 would be helpful but is not blocking — this analysis contains the pipeline runner details.
- **Polygon API access** — Massive tier must remain active for 50-ticker polling budget.

### Blocks Other Work

- **Seed 001 (Base Ticker Universe)** — Partially subsumed. Universe selection infrastructure lives in Seed 004 (Bucket A runner reads from `screener_universe` table). The actual ticker list definition is now **Seed 005** (separated per Silva's direction).
- **Monday.com METHOD.01 items** — Universe selection, screener merge, AI shortlist all depend on bucket infrastructure being in place.
- **Future indicator edge testing (04_indicators)** — More tickers in the universe means more data flowing into backtest and edge analysis. The bucket infrastructure is a prerequisite for scaling that pipeline.

### Related Backlog Items

| ID | Name | Relationship |
|----|------|-------------|
| 001 | Base Ticker Universe | **Partially subsumed** — infrastructure in 004, ticker list definition moved to Seed 005 |
| 002 | Architecture Baseline Audit | Parallel — 01_application CLAUDE.md update benefits from this analysis |
| 003 | Screener Data Bucket Audit | **Upstream dependency** — COMPLETE. Data contract input for this spec |
| 005 | Universe Ticker List | **New** — Silva provides preliminary list from daily click-through view. Seed 004 Bucket A consumes this list |

---

## 6. Estimated Scope

### Complexity: LARGE

- Cross-module changes (01_application + 02_dow_ai)
- New scheduling infrastructure (bucket runners + Windows Task Scheduler)
- New Supabase table (`screener_universe`) + column additions to 2 existing tables
- New calculations (pre-market volume profile, W1/M1 structure, universe selection, epoch detection)
- Entry Qualifier architecture modification (Supabase read integration)
- Potential new application or major UI rework (50-ticker scanner)

### Estimated Claude Code Sessions

| Phase | Sessions | Delivers |
|-------|----------|----------|
| Phase 1: Bucket runners (A+B+C) | 2-3 | All data pre-computed in Supabase before morning |
| Phase 2: Morning screener table | 1-2 | Screener table (RVOL, GAP, D1/H1/M15 structure) — pick candidates |
| Phase 3: Chart visualization + levels | 1 | Charts with all levels + H4 S/D zones — confirm selections, ready to trade |
| **Total** | **4-6** | **Complete morning workflow: sit down → screener → charts → 4 tickers → trade** |

### Implementation Priority Within Phases

**Phase 1 Build Order** (each step adds value):
1. `bucket_b_nightly.py` — Highest value. Existing 6-stage pipeline just needs a headless CLI wrapper. Most data is already computed here.
2. `bucket_a_weekly.py` — Monthly/weekly OHLC + Camarilla. Straightforward extraction from existing `bar_data.py`.
3. `bucket_c_morning.py` + `pre_market_calculator.py` — New calculations (PM high/low, PM volume profile). Depends on B being in Supabase.
4. `pre_market_query.py` — Query layer that replaces the current compute-everything approach in the screener UI.
5. Windows Task Scheduler scripts — Wire up automated triggering.

**Phase 2 Build Order**:
1. Morning screener app scaffold (PyQt6 main window + table view)
2. Supabase loader — reads Bucket B structure + Bucket C pre-market data
3. RVOL/GAP calculation from pre-market bars (reuse Structure Screener functions)
4. Table display with sorting/filtering by column
5. Test with Silva's universe tickers (from Seed 005)

**Phase 3 Build Order** (pending chart implementation review):
1. Audit existing chart/visualization code in `01_application/`
2. Ensure all Supabase-stored levels render on charts (Camarilla, HVN POCs, zones)
3. Add H4 supply/demand zone overlay (strong/weak levels from market_structure)
4. Add pre-market levels (PMH/PML/PMPOC/PMVAH/PMVAL)
5. Candidate cycling — navigate between selected tickers from screener table

---

## 7. Technical Design Notes

### Existing Pipeline Reuse Strategy

The existing 6-stage pipeline (`pipeline_runner.py`) already does everything Bucket B needs. The approach is NOT to rewrite the calculators — it's to add a scheduling wrapper that calls them in the right order at the right time.

```
TODAY:
  Silva launches app → PipelineRunner.run() → compute everything → export to Supabase

FUTURE:
  Bucket B (20:00 ET, automated):
    bucket_b_nightly.py → PipelineRunner.run(tickers=universe) → export to Supabase

  Bucket C (07:00 ET, manual or auto):
    bucket_c_morning.py → compute PM data → query Bucket B from Supabase → display

  Morning session:
    Silva opens app → pre_market_query.py → reads everything from Supabase → instant
```

### Polygon API Budget for Bucket Runners

Bucket runners are batch operations, not real-time polling. API budget is generous:

| Bucket | Tickers | Calls per Ticker | Total Calls | Time at 0.25s | Frequency |
|--------|---------|-----------------|-------------|---------------|-----------|
| A (Weekly) | ~50 | ~5 (W1, M1 bars + structure) | ~250 | ~63 seconds | Once/week |
| B (Nightly) | ~50 | ~15 (D1, H4, H1, M15 bars + structure + options + volume profile) | ~750 | ~188 seconds (~3 min) | Once/day |
| C (Morning) | ~50 | ~2 (PM M1 bars + current price) | ~100 | ~25 seconds | Once/morning |

Total nightly API time: ~3 minutes. Well within Polygon Massive tier limits. No batching optimization needed for v1.

### Supabase Exporter Migration

The current exporter uses raw psycopg2 (V1 debt). The bucket runners should use the shared Supabase client (`from shared.data.supabase import get_client`). This is an opportunity to migrate the exporter to V2 patterns as part of the bucket runner work, rather than propagating the V1 debt into new code.

### Pre-Market Volume Profile Calculation

The shared library at `00_shared/indicators/core/volume_profile.py` has the `compute_volume_profile()` function that returns POC, VAH, and VAL. For Bucket C, we need to:
1. Fetch M1 bars from 16:01 ET prior day to 07:00 ET current day
2. Pass them to the existing volume profile function
3. Store results as `pm_poc`, `pm_vah`, `pm_val` in `bar_data`

No new algorithm needed — just a new data window passed to existing infrastructure.

---

## STATUS: AWAITING SILVA REVIEW — All 9 questions resolved (2026-03-22)

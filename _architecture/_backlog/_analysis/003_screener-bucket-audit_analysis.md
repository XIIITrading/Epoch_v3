# Analysis: Screener Data Bucket Audit & Workflow Definition

**Seed**: `_seeds/003-screener-calculation-audit.md`
**Analyzed**: 2026-03-22
**System Areas**: `01_application/`, `00_shared/indicators/`, `02_dow_ai/`, Supabase tables (`bar_data`, `hvn_pocs`, `market_structure`, `zones`, `setups`)

---

## 1. Infrastructure Snapshot

### What Exists Today

The zone analysis pipeline lives entirely in `01_application/` and runs as a single sequential process during pre-market (Phase 1 in PIPELINE.md). There is **no bucket-based scheduling** today — everything runs in one pass when Silva launches the app and processes tickers.

**Five Supabase tables** are written by the pipeline:

| Table | Fields | Primary Writer | Timing Today |
|-------|--------|---------------|--------------|
| `bar_data` | 70+ columns | `01_application/data/supabase_exporter.py` | Pre-market, single pass |
| `hvn_pocs` | 14 columns | Same exporter | Pre-market, single pass |
| `market_structure` | 15 columns | Same exporter | Pre-market, single pass |
| `zones` | 17+ columns | Same exporter | Pre-market, single pass |
| `setups` | 14 columns | Same exporter | Pre-market, single pass |

**The pipeline has 6 stages**, each with a dedicated calculator:

1. **Market Structure** (`calculators/market_structure.py`) — Fractal detection across D1/H4/H1/M15
2. **Bar Data** (`calculators/bar_data.py`, 661 lines) — OHLC, ATR, Camarilla, Options, PD Volume Profile
3. **HVN POCs** (`calculators/hvn_identifier.py`) — $0.01 granularity volume profile, top 10 POCs
4. **Zone Confluence** (`calculators/zone_calculator.py`) — 60+ level scoring with bucket-max system
5. **Zone Filtering** (`calculators/zone_filter.py`) — Proximity, overlap elimination, tier classification
6. **Setup Analysis** (`calculators/setup_analyzer.py`) — Target selection via 3R/4R cascade

**The real-time Entry Qualifier** (`02_dow_ai/entry_qualifier/`) computes 5 indicators per M1 bar during the live session. These do NOT read from Supabase — they fetch fresh data from Polygon.io every 60 seconds. The canonical indicator implementations live in `00_shared/indicators/`.

**Key architectural note**: The LONG/SHORT composite scores (0-7) referenced in the seed's Bucket D were **deprecated in SWH-6 (February 2026)**. The `scores.py` functions now return 0. The system replaced them with multi-timeframe fractal structure analysis (H1/M5/M15).

### What Would Change

This is a **read-only audit** — no code changes, no schema modifications. The output is a single analysis document that becomes the authoritative data contract for the screener pipeline.

The audit document will be the **input specification** for Seed 004 (screener pipeline build), which WILL introduce bucket-based scheduling, new calculations, and potentially new tables.

### What It Connects To

- **Upstream**: Polygon.io API (bar data source), Supabase schema (confirmation source)
- **Downstream**: Seed 004 (screener pipeline build) — blocked until this audit is complete

---

## 2. Questions for Silva — Resolved

### Resolved During Review (2026-03-22)

1. **Universe Selection**: 50-ticker target — exact number to be determined by data. **OPEN for Seed 004.**

2. **Epoch Anchor Auto-Detection**: 20% threshold and "all others" definition — **OPEN for Seed 004.** Flagged as a parameter to validate.

3. **SMA 9 / SMA 21 → EMA 9 / EMA 21**: **RESOLVED.** Silva specified EMA (not SMA) for the nightly pull. However, during further review Silva moved EMA out of all pre-computed buckets. **EMA 9/21 is Bucket D (Real-Time) only** — computed live as part of the existing SMA/EMA config indicator. No nightly EMA pre-computation.

4. **"Current D1 High / Low / Open"**: **RESOLVED implicitly.** In Bucket B (Nightly, after 20:00 ET), "current" means the session that just closed. These are the most recent completed D1 values.

5. **Pre-Market Volume Profile time range**: **RESOLVED.** Pre-market = 16:00 ET prior day to 07:30 ET current day. This is broader than the current overnight window (20:00 UTC to 12:00 UTC) and should be the canonical pre-market definition going forward.

6. **Deprecated LONG/SHORT scores**: **RESOLVED.** All current scores are deprecated for the screener. Bucket D uses **raw fractal structure labels** (BULL/BEAR/NEUTRAL) + strong/weak levels for M5, M15, and H1. No composite scoring system.

7. **W1 and M1 Market Structure**: Marked as **NEW** in Bucket A. The shared library's fractal implementation (`calculate_structure_from_bars()`) works on any timeframe — W1/M1 bars just need to be fetched and passed. No new algorithm required.

8. **Supabase Schema Query**: **RESOLVED.** Ran live against Supabase. All 5 tables confirmed — codebase exports match schema exactly. See Section 4a.

9. **Codebase vs Epoch_v1**: **RESOLVED implicitly.** Method_v1 `01_application/` is fully functional V2 code. Audit based on Method_v1 only.

### Remaining Open Questions (Deferred to Seed 004)

- Exact 50-ticker universe criteria and screening logic
- Epoch anchor auto-detection threshold validation approach
- Overnight window alignment (current 20:00–12:00 UTC vs new 16:00–07:30 ET definition)
- Scheduling mechanism for Bucket A/B/C (cron, manual trigger, or hybrid)

---

## 3. Proposed Approach

### Option A: Full Audit in One Document (Recommended)

Execute the audit as a single comprehensive markdown document with four sections matching the seed's desired outcome:

1. **Field Inventory** — Enumerate every column from both codebase (export functions) and Supabase schema query, cross-referenced
2. **Bucket Assignment** — Classify each field into A/B/C/D based on calculation timing requirements and data dependencies
3. **Gap Analysis** — Compare the seed's desired data points against the field inventory, marking EXISTS / PARTIAL / NEW
4. **Source Map** — Link each confirmed field to its source file, function, and line number

The codebase exploration is already ~80% complete from this analysis session. Remaining work is the Supabase schema confirmation and final gap reconciliation.

### Option B: Two-Phase Audit (Codebase First, Schema Second)

Split into two passes:
- Phase A: Codebase-only audit (can be done immediately)
- Phase B: Supabase schema confirmation + reconciliation (requires live query)

**Recommendation: Option A** — the codebase exploration is done, and a single query to Supabase confirms everything. No reason to split.

---

## 4a. Supabase Schema Confirmation (Live Query — 2026-03-22)

Schema query executed against live Supabase (`information_schema.columns`). All 5 tables confirmed:

| Table | Supabase Columns | Codebase Export Fields | Match |
|-------|-----------------|----------------------|-------|
| `bar_data` | 67 (65 data + `created_at`, `updated_at`) | 65 data fields in `_export_bar_data()` | **Exact match** |
| `hvn_pocs` | 16 (14 data + timestamps) | 14 data fields in `_export_hvn_pocs()` | **Exact match** |
| `market_structure` | 20 (18 data + timestamps) | 18 data fields in `_export_market_structure()` | **Exact match** |
| `zones` | 22 (20 data + timestamps) | 20 data fields in `_export_zones()` | **Exact match** |
| `setups` | 16 (14 data + timestamps) | 14 data fields in `_export_setup()` | **Exact match** |

No orphaned columns. No missing fields. Schema and codebase are in full agreement.

---

## 4. Confirmed Field Inventory (Codebase + Supabase Verified)

These findings are confirmed from both the export functions in `supabase_exporter.py` AND the live Supabase schema query.

### bar_data — 70+ Fields Confirmed

| Category | Fields | Source File | Bucket Assignment |
|----------|--------|-------------|-------------------|
| **Identifiers** | `date`, `ticker_id`, `ticker`, `price` | `supabase_exporter.py:238` | N/A (key fields) |
| **Monthly OHLC (Current)** | `m1_open`, `m1_high`, `m1_low`, `m1_close` | `bar_data.py:calculate_monthly_metrics` | A — Weekly |
| **Monthly OHLC (Prior)** | `m1_prior_open`, `m1_prior_high`, `m1_prior_low`, `m1_prior_close` | Same | A — Weekly |
| **Weekly OHLC (Current)** | `w1_open`, `w1_high`, `w1_low`, `w1_close` | `bar_data.py:calculate_weekly_metrics` | A — Weekly |
| **Weekly OHLC (Prior)** | `w1_prior_open`, `w1_prior_high`, `w1_prior_low`, `w1_prior_close` | Same | A — Weekly |
| **Daily OHLC (Current)** | `d1_open`, `d1_high`, `d1_low`, `d1_close` | `bar_data.py:calculate_daily_metrics` | B — Nightly |
| **Daily OHLC (Prior)** | `d1_prior_open`, `d1_prior_high`, `d1_prior_low`, `d1_prior_close` | Same | B — Nightly |
| **Overnight** | `d1_overnight_high`, `d1_overnight_low` | `bar_data.py:calculate_overnight_metrics` | C — Morning |
| **ATR (Multi-TF)** | `m5_atr`, `m15_atr`, `h1_atr`, `d1_atr` | `bar_data.py:calculate_*_atr` | B — Nightly (all, including D1 per Silva) |
| **Camarilla Daily** | `d1_cam_s6`, `d1_cam_s4`, `d1_cam_s3`, `d1_cam_r3`, `d1_cam_r4`, `d1_cam_r6` | `bar_data.py:calculate_camarilla_levels` | B — Nightly |
| **Camarilla Weekly** | `w1_cam_s6`, `w1_cam_s4`, `w1_cam_s3`, `w1_cam_r3`, `w1_cam_r4`, `w1_cam_r6` | Same | A — Weekly |
| **Camarilla Monthly** | `m1_cam_s6`, `m1_cam_s4`, `m1_cam_s3`, `m1_cam_r3`, `m1_cam_r4`, `m1_cam_r6` | Same | A — Weekly |
| **Options Levels** | `op_01` through `op_10` | `options_calculator.py` | B — Nightly |
| **Prior Day Volume Profile** | `pd_vp_poc`, `pd_vp_vah`, `pd_vp_val` | `bar_data.py:calculate_prior_day_volume_profile` | B — Nightly |

**Missing from bar_data (Not Currently Computed)**: M1 ATR (exists in calculator but not exported to bar_data — verify)

### hvn_pocs — 14 Fields

| Field | Source | Bucket Assignment |
|-------|--------|-------------------|
| `date`, `ticker_id`, `ticker` | Key fields | N/A |
| `epoch_start_date` | User-provided anchor date | A — Weekly (when auto-detected) |
| `poc_1` through `poc_10` | `hvn_identifier.py:_select_pocs_no_overlap` | B — Nightly (epoch-anchored, recalculated nightly) |

### market_structure — 15 Fields

| Field | Source | Bucket Assignment |
|-------|--------|-------------------|
| `date`, `ticker`, `ticker_id`, `is_index`, `scan_price` | Key/context fields | N/A |
| `d1_direction`, `d1_strong`, `d1_weak` | `market_structure.py` (250-day lookback) | B — Nightly |
| `h4_direction`, `h4_strong`, `h4_weak` | Same (100-day lookback) | B — Nightly |
| `h1_direction`, `h1_strong`, `h1_weak` | Same (50-day lookback) | B — Nightly (or C — Morning) |
| `m15_direction`, `m15_strong`, `m15_weak` | Same (15-day lookback) | C — Morning |
| `composite_direction` | Weighted: D1×1.5, H4×1.5, H1×1.0, M15×0.5 | B — Nightly |

### zones — 17+ Fields

| Field | Source | Bucket Assignment |
|-------|--------|-------------------|
| Key fields | `zone_id`, `ticker_id`, `ticker`, `date`, `price` | N/A |
| Zone boundaries | `hvn_poc`, `zone_high`, `zone_low` | B — Nightly |
| Classification | `direction`, `rank` (L1-L5), `score`, `overlap_count` | B — Nightly |
| Confluences | `confluences` (comma-separated list) | B — Nightly |
| Flags | `is_filtered`, `is_epch_bull`, `is_epch_bear` | B — Nightly |
| Targets | `epch_bull_price`, `epch_bear_price`, `epch_bull_target`, `epch_bear_target` | B — Nightly |

### setups — 14 Fields

| Field | Source | Bucket Assignment |
|-------|--------|-------------------|
| Key fields | `date`, `ticker_id`, `ticker`, `setup_type` | N/A |
| Direction | `direction`, `zone_id` | B — Nightly |
| Zone | `hvn_poc`, `zone_high`, `zone_low` | B — Nightly |
| Targets | `target_id`, `target_price`, `risk_reward` | B — Nightly |
| PineScript | `pinescript_6`, `pinescript_16` | B — Nightly |

---

## 5. Preliminary Gap Analysis (Desired vs Existing)

### Bucket A — Weekly

| Desired Data Point | Status | Notes |
|-------------------|--------|-------|
| M1 OHLC (current + prior) | **EXISTS** | `bar_data.py:calculate_monthly_metrics` |
| W1 OHLC (current + prior) | **EXISTS** | `bar_data.py:calculate_weekly_metrics` |
| W1 Market Structure (BOS/CHoCH) | **NEW** | Current structure only does D1/H4/H1/M15 — W1 not implemented |
| M1 Market Structure (BOS/CHoCH) | **NEW** | Same — Monthly structure not implemented |
| ATR across M1–D1 | **EXISTS** | M5, M15, H1, D1 ATR all exist. M1 ATR in calculator but export status needs Supabase confirmation |
| EMA 9 / EMA 21 | **EXISTS (Bucket D only)** | Shared library has EMA via `sma.py:ema_df()`. Not pre-computed — lives in Bucket D real-time only per Silva |
| 50-ticker universe selection | **NEW** | No batch universe selection logic exists. Current: manual scan + select |
| Epoch anchor auto-detection | **NEW** | Currently manual. Seed describes automation rule |

### Bucket B — Nightly

| Desired Data Point | Status | Notes |
|-------------------|--------|-------|
| D1 OHLC (prior day) | **EXISTS** | `bar_data.py:calculate_daily_metrics` |
| Camarilla Pivots (S3/S4/S6, R3/R4/R6) | **EXISTS** | All three timeframes (D1/W1/M1) |
| Options OI levels (op_01–op_10) | **EXISTS** | `options_calculator.py` |
| PDV POC / VAH / VAL | **EXISTS** | `bar_data.py:calculate_prior_day_volume_profile` |
| HVN POC (top 10, epoch-anchored) | **EXISTS** | `hvn_identifier.py` |
| VbP Profile (epoch-anchored) | **EXISTS** | Same as HVN — built from full epoch volume profile |
| Current D1 H/L/O | **EXISTS** | `d1_open`, `d1_high`, `d1_low` in bar_data |
| Current W1 H/O/L | **EXISTS** | `w1_open`, `w1_high`, `w1_low` in bar_data |
| Zone confluence scoring | **EXISTS** | `zone_calculator.py` — full bucket-max system |
| Setup generation | **EXISTS** | `setup_analyzer.py` — direction, targets, R:R |

### Bucket C — Morning Session (07:00–08:00 ET)

| Desired Data Point | Status | Notes |
|-------------------|--------|-------|
| Pre-Market High (PMH) | **NEW** | Not currently computed. Would need pre-market M1 bars |
| Pre-Market Low (PML) | **NEW** | Same |
| Pre-Market VAH (PMVAH) | **NEW** | Volume profile on pre-market bars — new calculation |
| Pre-Market VAL (PMVAL) | **NEW** | Same |
| Pre-Market POC (PMPOC) | **NEW** | Same — shared library volume_profile can do this |
| Current Price at 07:30 ET | **NEW** | Simple API fetch — not currently scheduled |
| HVN POCs (query from nightly) | **EXISTS** | Data in Supabase — just needs a query |
| Zone levels (query from nightly) | **EXISTS** | Same |
| Structure levels (query from nightly) | **EXISTS** | Same |
| Camarilla pivots (query from nightly) | **EXISTS** | Same |

### Bucket D — Real-Time

| Desired Data Point | Status | Notes |
|-------------------|--------|-------|
| Candle Range % | **EXISTS** | `shared/indicators/core/candle_range.py` via Entry Qualifier |
| Volume Delta (5-bar rolling) | **EXISTS** | `shared/indicators/core/volume_delta.py` |
| Volume ROC (vs 20-bar trailing) | **EXISTS** | `shared/indicators/core/volume_roc.py` |
| SMA Config (SMA9 vs SMA21) | **EXISTS** | `shared/indicators/core/sma.py` |
| H1 Market Structure | **EXISTS** | `shared/indicators/structure/market_structure.py` (cached, hourly refresh) |
| M5 Structure — raw label + levels | **EXISTS** | `shared/indicators/structure/market_structure.py` (cached, 5-min refresh). Returns direction + strong_level + weak_level |
| M15 Structure — raw label + levels | **EXISTS** | Same (cached, 15-min refresh) |
| ~~LONG/SHORT composite scores (0-7)~~ | **DEPRECATED** | SWH-6 removed. `scores.py` returns 0. Replaced by M5/M15/H1 raw structure labels above |

**Bucket D Scaling Note (50-Ticker Live Scanner):** With Buckets A/B/C pre-computing all higher-timeframe data into Supabase, the real-time scanner becomes lightweight — only M1 bar fetches + 7 indicator calculations per ticker. At Polygon's 0.25s rate limit, 50 tickers = 12.5 seconds of M1 fetches per 60-second cycle. Structure refreshes (M5 every 5min, M15 every 15min, H1 hourly) add 12.5 seconds each but only fire periodically. This makes scaling the Entry Qualifier from 4 tickers to the full 50-ticker universe architecturally feasible. Design details deferred to Seed 004.

---

## 6. Impact Map

### New/Modified Tables

| Table | Action | Written By | Read By | Purpose |
|-------|--------|-----------|---------|---------|
| None | — | — | — | Read-only audit — no table changes |

### New/Modified Files

| File | Module | Purpose |
|------|--------|---------|
| `_backlog/_analysis/003_screener-bucket-audit.md` | `_architecture` | Audit deliverable (this is the spec output) |

### Architecture Document Updates Required

- [ ] DATA_FLOW.md: Replace "~70 fields" description with confirmed field list (enumerated in audit)
- [ ] SYSTEM_MAP.md: No changes needed (audit is read-only)
- [ ] PIPELINE.md: No changes (bucket scheduling is Seed 004 scope)
- [ ] 01_application CLAUDE.md: Update from stub to proper module context (Seed 002 scope — already active)

---

## 7. Dependencies & Sequencing

### Must Exist First

- **Supabase access**: Need to run `information_schema.columns` query to confirm live schema matches codebase exports
- **Seed 002 (Architecture Baseline Audit)**: Batch 1 is DONE, which covered the architecture docs. Module CLAUDE.md updates are in progress. No hard dependency — this audit can proceed independently.

### Blocks Other Work

- **Seed 004 (Screener Pipeline Build)**: Cannot be specced without this audit. The audit output becomes the data contract.
- **METHOD.01 items on Monday.com**: Universe selection, screener merge, AI shortlist — all depend on knowing what exists

### Related Backlog Items

| ID | Name | Relationship |
|----|------|-------------|
| 001 | Base Ticker Universe | Overlaps with Bucket A "50-ticker universe selection" — Seed 004 will subsume this |
| 002 | Architecture Baseline Audit | Parallel work — 01_application CLAUDE.md update will benefit from this audit's findings |
| 004 | Screener Pipeline Build | Direct downstream — this audit is the data contract input for Seed 004 |

---

## 8. Estimated Scope

### Complexity: SMALL-MEDIUM

This is a documentation task, not a code build:
- Codebase analysis: Complete (3 parallel agent explorations)
- Supabase schema query: Complete (all 5 tables confirmed)
- Silva's bucket decisions: Resolved
- Gap reconciliation and formatting: Complete

### Estimated Claude Code Sessions: 1 (completed in current session)

---

## 9. Finalized Bucket Assignments (Silva-Approved)

### Bucket A — Weekly (Saturday/Sunday after Friday close)

| # | Calculation | Status | Source |
|---|------------|--------|--------|
| A1 | M1 (Monthly) OHLC — current + prior | EXISTS | `bar_data.py:calculate_monthly_metrics` |
| A2 | W1 (Weekly) OHLC — current + prior | EXISTS | `bar_data.py:calculate_weekly_metrics` |
| A3 | Monthly Camarilla (S3/S4/S6, R3/R4/R6) | EXISTS | `bar_data.py:calculate_camarilla_levels` |
| A4 | Weekly Camarilla (S3/S4/S6, R3/R4/R6) | EXISTS | `bar_data.py:calculate_camarilla_levels` |
| A5 | W1 Market Structure (direction + strong/weak) | **NEW** | Shared library supports — pass W1 bars |
| A6 | M1 Market Structure (direction + strong/weak) | **NEW** | Shared library supports — pass M1 bars |
| A7 | 50-ticker universe selection | **NEW** | No implementation exists |
| A8 | Epoch anchor auto-detection | **NEW** | Currently manual — needs automation rule |

### Bucket B — Nightly (After 20:00 ET)

| # | Calculation | Status | Source |
|---|------------|--------|--------|
| B1 | D1 OHLC — prior day | EXISTS | `bar_data.py:calculate_daily_metrics` |
| B2 | D1 ATR (24 daily bars) | EXISTS | `bar_data.py:calculate_d1_atr` |
| B3 | H1 ATR | EXISTS | `bar_data.py:calculate_h1_atr` |
| B4 | M15 ATR | EXISTS | `bar_data.py:calculate_m15_atr` |
| B5 | M5 ATR | EXISTS | `bar_data.py:calculate_m5_atr` |
| B6 | D1 Camarilla (S3/S4/S6, R3/R4/R6) | EXISTS | `bar_data.py:calculate_camarilla_levels` |
| B7 | Options OI levels (op_01–op_10) | EXISTS | `options_calculator.py` |
| B8 | PDV POC / VAH / VAL | EXISTS | `bar_data.py:calculate_prior_day_volume_profile` |
| B9 | HVN POCs (top 10, epoch-anchored) | EXISTS | `hvn_identifier.py` |
| B10 | D1 Market Structure (direction + strong/weak) | EXISTS | `market_structure.py` |
| B11 | H4 Market Structure (direction + strong/weak) | EXISTS | `market_structure.py` |
| B12 | H1 Market Structure (direction + strong/weak) | EXISTS | `market_structure.py` |
| B13 | M15 Market Structure (direction + strong/weak) | EXISTS | `market_structure.py` |
| B14 | Composite structure direction | EXISTS | Weighted: D1×1.5, H4×1.5, H1×1.0, M15×0.5 |
| B15 | Zone confluence scoring (60+ levels, bucket-max) | EXISTS | `zone_calculator.py` |
| B16 | Zone filtering (proximity, tier, overlap) | EXISTS | `zone_filter.py` |
| B17 | Setup generation (direction, targets, R:R) | EXISTS | `setup_analyzer.py` |
| B18 | Current D1 High/Low/Open (session just closed) | EXISTS | `bar_data.py:calculate_daily_metrics` |
| B19 | Current W1 High/Open/Low | EXISTS | `bar_data.py:calculate_weekly_metrics` |

### Bucket C — Morning Session (16:00 ET prior day → 07:30 ET current day)

| # | Calculation | Status | Source |
|---|------------|--------|--------|
| C1 | Pre-Market High (PMH) | **NEW** | Max high from 16:01 ET prior → 07:00 ET |
| C2 | Pre-Market Low (PML) | **NEW** | Min low from same window |
| C3 | Pre-Market POC (PMPOC) | **NEW** | `shared/indicators/core/volume_profile.py` can compute |
| C4 | Pre-Market VAH (PMVAH) | **NEW** | Same |
| C5 | Pre-Market VAL (PMVAL) | **NEW** | Same |
| C6 | Current price at ~07:00 ET | **NEW** | Simple latest bar close from Polygon |
| C7 | Overnight High/Low | EXISTS | `bar_data.py` — window needs alignment to 16:00–07:30 ET |
| C8 | HVN POCs (query Bucket B) | EXISTS | Read-only Supabase query |
| C9 | Zone levels (query Bucket B) | EXISTS | Read-only Supabase query |
| C10 | Structure levels (query Bucket B) | EXISTS | Read-only Supabase query |
| C11 | Camarilla pivots (query Bucket B) | EXISTS | Read-only Supabase query |

### Bucket D — Real-Time (09:30–16:00 ET, scalable to 50 tickers)

| # | Calculation | Status | Source |
|---|------------|--------|--------|
| D1 | Candle Range % | EXISTS | `shared/indicators/core/candle_range.py` |
| D2 | Volume Delta (5-bar rolling) | EXISTS | `shared/indicators/core/volume_delta.py` |
| D3 | Volume ROC (vs 20-bar trailing avg) | EXISTS | `shared/indicators/core/volume_roc.py` |
| D4 | EMA 9 / EMA 21 spread + config | EXISTS | `shared/indicators/core/sma.py:ema_df()` |
| D5 | H1 Structure — raw label + strong/weak levels | EXISTS | `shared/indicators/structure/market_structure.py` |
| D6 | M15 Structure — raw label + strong/weak levels | EXISTS | Same |
| D7 | M5 Structure — raw label + strong/weak levels | EXISTS | Same |

### Summary

| Bucket | EXISTS | NEW | Total |
|--------|--------|-----|-------|
| A — Weekly | 4 | 4 | 8 |
| B — Nightly | 19 | 0 | 19 |
| C — Morning | 5 | 6 | 11 |
| D — Real-Time | 7 | 0 | 7 |
| **Total** | **35** | **10** | **45** |

---

## STATUS: COMPLETE — APPROVED BY SILVA

**Completed**: 2026-03-22
**Supabase Schema**: Confirmed — all 5 tables match codebase exactly
**Bucket Assignments**: Finalized with Silva's input
**Next Step**: Seed 004 (Screener Pipeline Build) uses this document as the authoritative data contract

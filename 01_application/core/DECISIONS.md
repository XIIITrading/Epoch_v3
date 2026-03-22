# DECISIONS.md — Seed 004 Phase 1 (Bucket Runners)

## What Was Built

Three bucket runners that pre-compute the screener pipeline data on a schedule, so Silva's morning session becomes a query instead of a full computation run.

**Bucket B (Nightly)** wraps the existing 6-stage pipeline (market structure → bar data → HVN → zones → filter → setups) in a headless CLI runner. Double-click `run_nightly.bat` after market close, and all data for every universe ticker lands in Supabase's 5 tables. This is the highest-value piece — it's what eliminates the 30-minute compute time in the morning.

**Bucket A (Weekly)** resolves epoch anchors automatically (finds the highest-volume day in 6 months, same logic as the "Max Volume" preset in the screener), calculates W1 and M1 fractal market structure (using the shared library that already works for D1/H4/H1/M15), and then runs the full nightly pipeline on top. Run this on the weekend.

**Bucket C (Morning)** fetches pre-market M1 bars from 16:00 ET prior day to 07:30 ET current day, computes the pre-market high/low, pre-market volume profile (POC/VAH/VAL), and captures the current price. These values are written to the existing bar_data rows that nightly created.

**Query Layer** (`pre_market_query.py`) reads all 5 Supabase tables for a given date and ticker list, returning a single data structure that the Phase 2 screener table and Phase 3 chart visualization will consume.

## How It Connects

- **Reads from**: Polygon.io API (bar data), `config/universe_tickers.txt` (ticker list until Seed 005)
- **Writes to**: All 5 existing Supabase tables (`bar_data`, `hvn_pocs`, `market_structure`, `zones`, `setups`) plus the new `screener_universe` table
- **Downstream**: Phase 2 (screener table) and Phase 3 (chart visualization) will read from `pre_market_query.py`
- **Does not break**: The backtest pipeline (03_backtest) reads zones/setups — those table contracts are unchanged

## Test Results

- Nightly runner tested with SPY, QQQ, DIA on 2026-03-20
- All 6 pipeline stages completed successfully for all 3 tickers
- bar_data, hvn_pocs, zones, setups exported to Supabase
- market_structure export partially failed due to existing V1 exporter bug (delete-before-insert pattern loses data when re-insert fails on dict-format results)
- Total runtime: 203 seconds for 3 index tickers (options calculator is the bottleneck at ~60s per ticker)

## Deviations from Spec

- The existing `supabase_exporter.py` uses a delete-then-insert pattern instead of true upserts for the full result set. This means if the INSERT fails after the DELETE, data is lost for that date. The bucket runners work correctly — this is existing V1 debt that predates our changes.

## Open Questions for Silva

1. **Export robustness**: The existing exporter deletes all data for a date before re-inserting. Should we fix this as part of Phase 1 (wrap in transaction, only commit if all inserts succeed), or defer to Phase 2?
2. **Universe tickers**: The 3-ticker test (SPY/QQQ/DIA) worked. When you're ready, add your daily click-through tickers to `config/universe_tickers.txt` so we can test with the full set. Seed 005 will automate this.
3. **Options calculator speed**: ~60 seconds per ticker for options OI. For a 50-ticker universe, that's ~50 minutes just for options. Should we parallelize this or make it optional for non-primary tickers?

## Architecture Document Updates Required

- [ ] DATA_FLOW.md: Add screener_universe table, add pm_* columns to bar_data, add w1/m1 columns to market_structure
- [ ] PIPELINE.md: Add Bucket A/B/C execution flow
- [ ] SYSTEM_MAP.md: Add bucket runner to 01_application
- [ ] 01_application CLAUDE.md: Update with bucket runner context

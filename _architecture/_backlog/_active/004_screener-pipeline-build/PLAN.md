# PLAN.md — Seed 004 Phase 1 (Bucket Runners)

## SPEC REFERENCE
Seed 004 analysis (`_analysis/004_screener-pipeline-build_analysis.md`), approved 2026-03-22.
Data contract: Seed 003 audit (`_analysis/003_screener-bucket-audit_analysis.md`).

## MODULE LOCATION
`C:\XIIITradingSystems\Method_v1\01_application\`
- New files in `core/`, `data/`, `calculators/`, `config/`, `scripts/`

## INPUTS
- **Polygon.io API**: Daily, hourly, minute, weekly, monthly bars for universe tickers
- **Supabase `screener_universe` table** (or fallback `config/universe_tickers.txt`): Ticker list + epoch anchor dates
- **Existing calculator functions**: All 7 calculators in `01_application/calculators/` (bar_data, market_structure, hvn_identifier, zone_calculator, zone_filter, setup_analyzer, options_calculator)
- **Shared indicator library**: `volume_profile.py` for PM profile, `market_structure.py` for W1/M1 structure

## TRANSFORM
1. **Bucket A (Weekly)**: Fetches weekly/monthly bars → computes OHLC, Camarilla, W1/M1 fractal structure → upserts to Supabase
2. **Bucket B (Nightly)**: Calls existing PipelineRunner.run() headless → exports via existing supabase_exporter → all 5 tables populated
3. **Bucket C (Morning)**: Fetches M1 bars for 16:00–07:30 ET window → computes PMH/PML/PMPOC/PMVAH/PMVAL/price → upserts pm_* columns to bar_data
4. **Query Layer**: Reads all pre-computed data from Supabase for downstream use (Phase 2 screener, Phase 3 charts)

## OUTPUTS
- **Supabase `bar_data`**: Existing 67 columns + 6 new pm_* columns
- **Supabase `market_structure`**: Existing 20 columns + 6 new w1_*/m1_* columns
- **Supabase `hvn_pocs`**: No change (written by Bucket B)
- **Supabase `zones`**: No change (written by Bucket B)
- **Supabase `setups`**: No change (written by Bucket B)
- **Supabase `screener_universe`**: New table (ticker, anchor date, status)

## DOWNSTREAM IMPACT
- Phase 2 (Morning Screener Table): reads from `pre_market_query.py`
- Phase 3 (Chart Visualization): reads from `pre_market_query.py`
- `03_backtest`: reads zones/setups — no contract change
- `05_system_analysis`: reads bar_data/market_structure — gains new columns but no breaking change

## V2 COMPLIANCE
- All new code uses `from shared.data.supabase import get_client`
- All new code uses `from shared.config import credentials`
- Bucket B calls existing PipelineRunner (which uses existing polygon_client and supabase_exporter — V1 psycopg2 debt, not propagated)
- New Bucket A and C upserts use shared Supabase client

## ASSUMPTIONS
- Polygon Massive tier rate limits are sufficient for batch processing ~50 tickers nightly (~3 min total API time)
- The existing PipelineRunner.run() works correctly when called without a QThread (headless mode) — needs verification
- W1/M1 bars from Polygon are available via the existing `fetch_weekly_bars()` and `fetch_monthly_bars()` methods
- `shared.indicators.structure.get_market_structure()` works correctly on W1/M1 bar data (designed for any timeframe but not tested on weekly/monthly)

## OPEN QUESTIONS
- None — all 9 questions resolved by Silva on 2026-03-22

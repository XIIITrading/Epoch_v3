# Implementation Spec: Screener Pipeline Build — Phase 1 (Bucket Runners)

**Seed**: 004
**Phase**: 1 of 3
**Approved**: 2026-03-22
**Module**: `01_application/`
**Estimated Sessions**: 2-3

---

## Objective

Add bucket-mode execution to the existing pipeline so that the 6-stage analysis (market structure → bar data → HVN → zones → filter → setups) can be triggered by time-bucket (weekly, nightly, morning) instead of only through the GUI. All data lands in the same 5 Supabase tables. The morning session becomes a query, not a computation.

---

## What Gets Built

### 1. `core/bucket_runner.py` — CLI Entry Point (~150 lines)

**Purpose**: Single CLI script that routes to the correct bucket based on `--bucket` flag.

**Interface**:
```
python -m core.bucket_runner --bucket nightly
python -m core.bucket_runner --bucket weekly
python -m core.bucket_runner --bucket morning
```

**Behavior**:
- Reads universe tickers from Supabase `screener_universe` table (or falls back to a local ticker list file if table doesn't exist yet — Seed 005 populates this)
- Routes to the appropriate bucket runner
- Logs start/end times, ticker count, success/failure count to stdout
- Returns exit code 0 on success, 1 on any ticker failures

**Imports**:
```python
from core.bucket_a_weekly import run_weekly
from core.bucket_b_nightly import run_nightly
from core.bucket_c_morning import run_morning
```

**Fallback ticker list**: Until Seed 005 populates `screener_universe`, the runner reads from `config/universe_tickers.txt` — one ticker per line, optional comma-separated anchor date (same format as the market screener input: `TICKER,YYYY-MM-DD`).

---

### 2. `core/bucket_a_weekly.py` — Weekly Runner (~200 lines)

**Purpose**: Compute data that only changes at weekly/monthly boundaries. Runs Saturday/Sunday (manual trigger).

**Calculations** (from Seed 003 Bucket A):

| # | Calculation | Source Function | Notes |
|---|------------|-----------------|-------|
| A1-A2 | M1 OHLC (current + prior) | `calculators.bar_data.calculate_monthly_metrics()` | Pass monthly bars from Polygon |
| A3-A4 | W1 OHLC (current + prior) | `calculators.bar_data.calculate_weekly_metrics()` | Pass weekly bars from Polygon |
| A5 | Monthly Camarilla | `calculators.bar_data.calculate_camarilla_levels()` | Uses prior M1 OHLC |
| A6 | Weekly Camarilla | Same | Uses prior W1 OHLC |
| A7 | W1 Market Structure | `shared.indicators.structure.get_market_structure()` | Pass W1 bars — shared library supports any timeframe |
| A8 | M1 Market Structure | Same | Pass M1 bars |
| A9 | Epoch anchor auto-detection | `calculators.anchor_resolver.find_max_volume_anchor()` | Existing function, 6-month lookback, 20% threshold |

**Flow**:
```python
def run_weekly(tickers: List[Dict], analysis_date: date) -> Dict:
    """
    tickers: [{"ticker": "AAPL", "anchor_date": date(...)}, ...]
    Returns: {"success": int, "failed": int, "errors": [...]}
    """
    for ticker_input in tickers:
        # 1. Resolve epoch anchor if needed
        anchor_date = find_max_volume_anchor(ticker, analysis_date)

        # 2. Fetch W1 and M1 bars from Polygon
        w1_bars = client.fetch_weekly_bars(ticker, start, end)
        m1_bars = client.fetch_monthly_bars(ticker, start, end)

        # 3. Calculate weekly/monthly OHLC + Camarilla
        # Reuse existing bar_data.py functions

        # 4. Calculate W1/M1 market structure
        # Use shared.indicators.structure.get_market_structure()

        # 5. Upsert to Supabase (bar_data + market_structure tables)
```

**Supabase writes**:
- `bar_data`: monthly/weekly OHLC + Camarilla columns (existing columns, new timing)
- `market_structure`: new columns `w1_direction`, `w1_strong`, `w1_weak`, `m1_direction`, `m1_strong`, `m1_weak`
- `screener_universe`: update `epoch_anchor_date` per ticker

**Schema change required**: Add 6 columns to `market_structure` table:
```sql
ALTER TABLE market_structure ADD COLUMN w1_direction INTEGER;
ALTER TABLE market_structure ADD COLUMN w1_strong NUMERIC;
ALTER TABLE market_structure ADD COLUMN w1_weak NUMERIC;
ALTER TABLE market_structure ADD COLUMN m1_direction INTEGER;
ALTER TABLE market_structure ADD COLUMN m1_strong NUMERIC;
ALTER TABLE market_structure ADD COLUMN m1_weak NUMERIC;
```

---

### 3. `core/bucket_b_nightly.py` — Nightly Runner (~250 lines)

**Purpose**: Compute all daily data after market close. This is the heaviest bucket — essentially the existing 6-stage pipeline running headless for the full universe.

**Calculations** (from Seed 003 Bucket B — 19 items, all EXISTS):

| # | Calculation | Source |
|---|------------|--------|
| B1 | D1 OHLC (prior day) | `bar_data.py:calculate_daily_metrics` |
| B2-B5 | ATR (D1, H1, M15, M5) | `bar_data.py:calculate_*_atr` |
| B6 | D1 Camarilla | `bar_data.py:calculate_camarilla_levels` |
| B7 | Options OI (op_01–op_10) | `options_calculator.py` |
| B8 | PDV POC/VAH/VAL | `bar_data.py:calculate_prior_day_volume_profile` |
| B9 | HVN POCs (top 10) | `hvn_identifier.py` |
| B10-B13 | D1/H4/H1/M15 Market Structure | `market_structure.py` |
| B14 | Composite direction | `market_structure.py` (weighted) |
| B15-B16 | Zone scoring + filtering | `zone_calculator.py`, `zone_filter.py` |
| B17 | Setup generation | `setup_analyzer.py` |
| B18-B19 | Current D1/W1 OHLC | `bar_data.py` |

**Key design decision**: The nightly runner wraps the existing `PipelineRunner._process_single_ticker()`. No calculator refactoring needed.

**Flow**:
```python
def run_nightly(tickers: List[Dict], analysis_date: date) -> Dict:
    """
    Wraps existing PipelineRunner for headless execution.
    """
    runner = PipelineRunner(progress_callback=_cli_progress)
    results = runner.run(tickers, analysis_date)

    # Export to Supabase using existing exporter
    from data.supabase_exporter import export_to_supabase
    stats = export_to_supabase(results)

    return {"success": stats.tickers_processed, "failed": stats.errors, ...}
```

**Why this works**: The existing pipeline already does everything Bucket B needs. The nightly runner is a thin CLI wrapper around `PipelineRunner.run()` + `export_to_supabase()`. No new calculators. No new tables. The only difference from the GUI path is: no QThread, no UI progress bar, headless execution.

**Supabase writes**: All 5 existing tables — `bar_data`, `hvn_pocs`, `market_structure`, `zones`, `setups`. Same ON CONFLICT upserts as today.

---

### 4. `core/bucket_c_morning.py` — Morning Runner (~300 lines)

**Purpose**: Compute pre-market data using bars from 16:00 ET prior day to 07:30 ET current day. Also queries nightly results from Supabase for the morning screener.

**Calculations** (from Seed 003 Bucket C — 6 NEW items):

| # | Calculation | Implementation |
|---|------------|----------------|
| C1 | Pre-Market High (PMH) | `max(high)` across PM bars |
| C2 | Pre-Market Low (PML) | `min(low)` across PM bars |
| C3 | Pre-Market POC (PMPOC) | `shared.indicators.core.volume_profile.compute_volume_profile()` on PM bars |
| C4 | Pre-Market VAH (PMVAH) | Same function returns VAH |
| C5 | Pre-Market VAL (PMVAL) | Same function returns VAL |
| C6 | Current price at trigger time | Latest bar close from Polygon |

**Pre-market bar window**: 16:00 ET prior day to 07:30 ET current day
- Convert to UTC for Polygon API: 20:00 UTC prior day to 11:30 UTC current day (EST) or 21:00 UTC to 12:30 UTC (EDT)
- Use `01_application/data/polygon_client.py:fetch_minute_bars_chunked()` with 1-min multiplier
- Filter bars by the ET window after fetching

**Flow**:
```python
def run_morning(tickers: List[Dict], analysis_date: date) -> Dict:
    """
    tickers: universe list
    analysis_date: today
    """
    for ticker_input in tickers:
        # 1. Fetch M1 bars for pre-market window (16:00 ET prior → 07:30 ET today)
        pm_bars = client.fetch_minute_bars_chunked(
            ticker, pm_start, pm_end, multiplier=1
        )

        # 2. Calculate PMH, PML
        pm_high = pm_bars['high'].max()
        pm_low = pm_bars['low'].min()

        # 3. Calculate PM volume profile (POC, VAH, VAL)
        from shared.indicators.core.volume_profile import compute_volume_profile
        profile = compute_volume_profile(pm_bars)
        pm_poc = profile['poc']
        pm_vah = profile['vah']
        pm_val = profile['val']

        # 4. Get current price (latest bar close)
        current_price = pm_bars.iloc[-1]['close']

        # 5. Upsert to bar_data table (new pm_* columns)
```

**Schema change required**: Add 6 columns to `bar_data` table:
```sql
ALTER TABLE bar_data ADD COLUMN pm_high NUMERIC;
ALTER TABLE bar_data ADD COLUMN pm_low NUMERIC;
ALTER TABLE bar_data ADD COLUMN pm_poc NUMERIC;
ALTER TABLE bar_data ADD COLUMN pm_vah NUMERIC;
ALTER TABLE bar_data ADD COLUMN pm_val NUMERIC;
ALTER TABLE bar_data ADD COLUMN pm_price NUMERIC;
```

**Supabase writes**: `bar_data` table only (adds pm_* columns to existing rows written by Bucket B).

---

### 5. `data/pre_market_query.py` — Supabase Query Layer (~200 lines)

**Purpose**: Single module that reads all pre-computed data from Supabase for a given date and ticker list. Used by the morning screener (Phase 2) and the chart visualization (Phase 3).

**Interface**:
```python
def load_pre_market_data(tickers: List[str], date: date) -> Dict[str, TickerData]:
    """
    Returns all pre-computed data for each ticker, keyed by ticker symbol.

    TickerData contains:
    - bar_data: Dict (all 70+ fields from bar_data table)
    - hvn_pocs: List[float] (poc_1 through poc_10)
    - market_structure: Dict (all timeframe directions + strong/weak levels)
    - zones: List[Dict] (filtered zones with scores)
    - setups: List[Dict] (primary + secondary setups)
    """
```

**Implementation**: Uses shared Supabase client (V2 pattern):
```python
from shared.data.supabase import get_client
client = get_client()

# Query each table for the given date + tickers
bar_data = client.table('bar_data').select('*').eq('date', date).in_('ticker', tickers).execute()
# ... same for other tables
```

---

### 6. `config/universe_tickers.txt` — Fallback Ticker List

**Purpose**: Simple text file with one ticker per line. Used until Seed 005 populates the `screener_universe` Supabase table.

**Format**:
```
SPY
QQQ
DIA
AAPL,2025-06-15
MSFT,2025-09-03
NVDA
INTC,2025-12-24
```

Tickers without dates use `find_max_volume_anchor()` for epoch detection.

---

### 7. `scripts/run_weekly.bat`, `run_nightly.bat`, `run_morning.bat`

**Purpose**: CLI wrappers Silva can double-click or run from terminal.

**Example** (`run_nightly.bat`):
```batch
@echo off
cd /d C:\XIIITradingSystems\Method_v1\01_application
python -m core.bucket_runner --bucket nightly
pause
```

---

### 8. New Supabase Table: `screener_universe`

**Purpose**: Stores the active ticker universe. Written by Bucket A (weekly). Read by all bucket runners.

```sql
CREATE TABLE screener_universe (
    ticker TEXT PRIMARY KEY,
    added_date DATE NOT NULL,
    sector TEXT,
    avg_volume NUMERIC,
    status TEXT DEFAULT 'active',  -- 'active' or 'inactive'
    epoch_anchor_date DATE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

Until Seed 005 populates this, the bucket runner reads from `config/universe_tickers.txt`.

---

## Integration Points

### Existing Code Reused (Not Modified)

| File | What's Reused |
|------|--------------|
| `core/pipeline_runner.py` | `PipelineRunner.run()` — called by Bucket B nightly runner |
| `calculators/bar_data.py` | All OHLC, ATR, Camarilla, volume profile functions |
| `calculators/market_structure.py` | D1/H4/H1/M15 structure calculation |
| `calculators/hvn_identifier.py` | HVN POC calculation |
| `calculators/zone_calculator.py` | Zone confluence scoring |
| `calculators/zone_filter.py` | Zone filtering |
| `calculators/setup_analyzer.py` | Setup generation |
| `calculators/options_calculator.py` | Options OI levels |
| `calculators/anchor_resolver.py` | `find_max_volume_anchor()` for epoch detection |
| `data/supabase_exporter.py` | `export_to_supabase()` — called by Bucket B |
| `data/polygon_client.py` | All Polygon API methods |
| `shared/indicators/core/volume_profile.py` | `compute_volume_profile()` for PM volume profile |
| `shared/indicators/structure/market_structure.py` | `get_market_structure()` for W1/M1 structure |

### Existing Code Modified

| File | Change | Reason |
|------|--------|--------|
| `data/supabase_exporter.py` | Add `pm_*` columns to `_export_bar_data()` | Bucket C writes pre-market data to existing bar_data rows |
| `data/supabase_exporter.py` | Add `w1_*/m1_*` columns to `_export_market_structure()` | Bucket A writes weekly/monthly structure |

### New Supabase Schema Changes

| Table | Change | Migration |
|-------|--------|-----------|
| `bar_data` | Add 6 columns: `pm_high`, `pm_low`, `pm_poc`, `pm_vah`, `pm_val`, `pm_price` | ALTER TABLE |
| `market_structure` | Add 6 columns: `w1_direction`, `w1_strong`, `w1_weak`, `m1_direction`, `m1_strong`, `m1_weak` | ALTER TABLE |
| `screener_universe` | New table | CREATE TABLE |

---

## V2 Compliance

- All new files import from `shared.config` and `shared.data.supabase`
- `pre_market_query.py` uses `get_client()` (V2 Supabase client)
- Bucket runners use `get_client()` for reading `screener_universe`
- Bucket B nightly calls existing `export_to_supabase()` (which currently uses psycopg2 — V1 debt, not propagated into new code)
- New upserts in Bucket A and Bucket C use the shared Supabase client with ON CONFLICT handling

---

## Error Handling

- Each ticker is isolated — one failure doesn't stop the batch (matches existing PipelineRunner pattern)
- Options calculation failure is non-blocking (matches existing behavior)
- Polygon API failures: 3 retries with exponential backoff (existing pattern)
- Bucket runner logs total success/fail counts at end of run
- Exit code 0 = all tickers succeeded, exit code 1 = one or more failed (so Silva can see at a glance)

---

## Testing Plan

1. **Bucket B (nightly)**: Run for 3 known tickers. Compare Supabase output against current GUI pipeline output for same tickers and date. All 5 tables should match exactly.
2. **Bucket A (weekly)**: Run for same 3 tickers. Verify W1/M1 OHLC, Camarilla, and new W1/M1 structure columns are populated.
3. **Bucket C (morning)**: Run for same 3 tickers. Verify pm_* columns are populated in bar_data. Verify PMH/PML match manual calculation from PM bars.
4. **pre_market_query.py**: Query data written by Buckets A/B/C. Verify all fields are present and non-null.
5. **Full sequence**: Run A → B → C in order for the 3 test tickers. Verify the complete data set is in Supabase.

---

## Build Order

1. **`config/universe_tickers.txt`** — Create with 3 test tickers (SPY, AAPL, INTC)
2. **Schema migrations** — Add columns to `bar_data` and `market_structure`, create `screener_universe`
3. **`core/bucket_b_nightly.py`** — Highest value, simplest (wraps existing pipeline)
4. **`core/bucket_runner.py`** — CLI entry point with `--bucket` routing
5. **`scripts/run_nightly.bat`** — Test the full nightly flow end-to-end
6. **`core/bucket_a_weekly.py`** — Weekly calculations (new W1/M1 structure)
7. **`core/bucket_c_morning.py`** + **`calculators/pre_market_calculator.py`** — Pre-market data
8. **`data/pre_market_query.py`** — Query layer for downstream phases
9. **Modify `supabase_exporter.py`** — Add new columns to export functions
10. **Test full A → B → C sequence**

---

## What Phase 2 Needs From Phase 1

The morning screener table (Phase 2) depends on:
- `pre_market_query.py` returning complete data for all universe tickers
- Bucket B having run successfully (nightly data in Supabase)
- Bucket C having run successfully (pre-market data in Supabase)
- `screener_universe` table or `universe_tickers.txt` populated with ticker list

---

*This spec covers Phase 1 only. Phase 2 (Morning Screener Table) and Phase 3 (Chart Visualization) will be specced after Phase 1 is built and tested.*

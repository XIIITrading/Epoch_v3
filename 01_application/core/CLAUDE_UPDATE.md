# CLAUDE_UPDATE.md — Seed 004 Phase 1

## Module Context Update

### New Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `core/bucket_runner.py` | 165 | CLI entry point — routes --bucket flag to A/B/C runners |
| `core/bucket_a_weekly.py` | 215 | Weekly runner — epoch anchors, W1/M1 structure, then nightly |
| `core/bucket_b_nightly.py` | 95 | Nightly runner — wraps PipelineRunner.run() + export |
| `core/bucket_c_morning.py` | 240 | Morning runner — PM bars, volume profile, price snapshot |
| `data/pre_market_query.py` | 170 | Supabase query layer — reads all 5 tables per date/tickers |
| `config/universe_tickers.txt` | 6 | Fallback ticker list (SPY, QQQ, DIA) |
| `scripts/run_nightly.bat` | 8 | Windows launcher for nightly bucket |
| `scripts/run_weekly.bat` | 8 | Windows launcher for weekly bucket |
| `scripts/run_morning.bat` | 8 | Windows launcher for morning bucket |

### Modified Files

| File | Change |
|------|--------|
| `data/supabase_exporter.py` | Added pm_* (6 fields) and w1/m1 (6 fields) to export functions |

### New Supabase Tables/Columns

| Table | Change |
|-------|--------|
| `bar_data` | +6 columns: `pm_high`, `pm_low`, `pm_poc`, `pm_vah`, `pm_val`, `pm_price` |
| `market_structure` | +6 columns: `w1_direction`, `w1_strong`, `w1_weak`, `m1_direction`, `m1_strong`, `m1_weak` |
| `screener_universe` | New table: `ticker`, `added_date`, `sector`, `avg_volume`, `status`, `epoch_anchor_date` |

## Integration Points

### CLI Interface
```
python -m core.bucket_runner --bucket nightly [--date YYYY-MM-DD] [--tickers path]
python -m core.bucket_runner --bucket weekly [--date YYYY-MM-DD]
python -m core.bucket_runner --bucket morning [--date YYYY-MM-DD]
```

### Query Layer
```python
from data.pre_market_query import load_pre_market_data, check_nightly_status
data = load_pre_market_data(["AAPL", "MSFT"], date(2026, 3, 22))
status = check_nightly_status(["AAPL", "MSFT"], date(2026, 3, 22))
```

### Ticker Loading
```python
from core.bucket_runner import load_universe_tickers
tickers = load_universe_tickers(analysis_date)
# Returns: [{"ticker": "SPY", "anchor_date": date, "needs_auto_anchor": bool}, ...]
```

## Known Limitations

- Options calculator is the bottleneck (~60s per ticker) — limits practical universe to ~50 tickers in a nightly window
- Existing exporter uses delete-then-insert, not true upserts — partial failures can lose data
- W1/M1 structure untested with real weekly/monthly bars (shared library should work but needs validation)
- Morning runner (Bucket C) untested with live pre-market bars (market was closed during testing)

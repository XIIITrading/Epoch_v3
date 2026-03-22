# 01_application — AI Context

## Purpose
Pre-market zone analysis application. Screens tickers, constructs volume profiles, identifies
high-probability supply/demand zones, scores zone confluence, generates setups, and exports to
Supabase. Also runs the bucket-based pre-computation pipeline for overnight/morning data prep.

## Status: V2 Active

## Key Subsystems

### GUI Application (PyQt6)
- `ui/tabs/market_screener.py` — Main screener with ticker input, analysis trigger, export
- `ui/tabs/structure_screener.py` — Market structure + RVOL/GAP scoring
- `ui/tabs/pre_market_report.py` — Pre-market chart with H4 S/D zone overlays

### Pipeline (6 stages, called by GUI or bucket runners)
- `core/pipeline_runner.py` — Orchestrates all 6 stages per ticker
  - Stage 1: `calculators/market_structure.py` — D1/H4/H1/M15 fractal detection
  - Stage 2: `calculators/bar_data.py` (661 lines) — OHLC, ATR, Camarilla, overnight, PDV profile
  - Stage 2b: `calculators/options_calculator.py` — Top 10 options OI strikes
  - Stage 3: `calculators/hvn_identifier.py` — Epoch volume profile, top 10 HVN POCs
  - Stage 4: `calculators/zone_calculator.py` — 60+ level confluence scoring, bucket-max system
  - Stage 5: `calculators/zone_filter.py` — Score floor (L3+), proximity (2x D1 ATR), dedup
  - Stage 6: `calculators/setup_analyzer.py` — Direction, targets (3R/4R cascade), R:R
- `calculators/anchor_resolver.py` — High Volume Day epoch auto-detection (6mo, 20% threshold)
- `weights.py` — Confluence weights, ranking thresholds, tier mapping

### Bucket Runners (Seed 004 — Built 2026-03-22)
- `core/bucket_runner.py` — CLI entry point (`--bucket weekly|nightly|morning`)
- `core/bucket_a_weekly.py` — Weekly: epoch anchors, W1/M1 structure, then nightly
- `core/bucket_b_nightly.py` — Nightly: parallel options (4 workers), headless pipeline, export
- `core/bucket_c_morning.py` — Morning: PM bars 16:00-07:30 ET, volume profile, price snapshot
- `scripts/run_weekly.bat`, `run_nightly.bat`, `run_morning.bat` — CLI launchers
- `config/universe_tickers.txt` — 48-ticker universe fallback

### Data Layer
- `data/supabase_exporter.py` — Exports to 5 Supabase tables (per-ticker savepoint isolation)
- `data/pre_market_query.py` — Read-only query layer for all 5 tables
- `data/polygon_client.py` — Polygon.io API client with caching
- `data/cache_manager.py` — Local cache for API responses

## Supabase Tables Written
- `bar_data` — ~76 columns (OHLC, ATR, Camarilla, Options, PDV, pm_* pre-market)
- `hvn_pocs` — Top 10 epoch-anchored HVN POC levels
- `market_structure` — D1/H4/H1/M15 + W1/M1 directions and strong/weak levels
- `zones` — Scored confluence zones with tier and proximity
- `setups` — Primary/secondary setups with direction, targets, R:R
- `screener_universe` — Active ticker list with epoch anchor dates

## Import Patterns
```python
# Pipeline
from core.pipeline_runner import PipelineRunner
from calculators.bar_data import calculate_bar_data
from calculators.market_structure import calculate_market_structure

# Bucket runners
from core.bucket_runner import load_universe_tickers
from core.bucket_b_nightly import run_nightly

# Data
from data.supabase_exporter import export_to_supabase
from data.pre_market_query import load_pre_market_data, check_nightly_status
```

## Configuration
- `config.py` — API keys, DB config, filter thresholds, zone settings, anchor presets
- `config/universe_tickers.txt` — Ticker list (one per line, optional comma-separated anchor date)

## CLI Commands
```bash
# Bucket runners (from 01_application/ directory)
python -m core.bucket_runner --bucket nightly [--date YYYY-MM-DD]
python -m core.bucket_runner --bucket weekly [--date YYYY-MM-DD]
python -m core.bucket_runner --bucket morning [--date YYYY-MM-DD]
```

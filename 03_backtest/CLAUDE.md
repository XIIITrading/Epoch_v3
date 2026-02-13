# 03_backtest - Backtest Runner v4.0

## Module Overview

PyQt6-based backtest runner for detecting trade entries using S15 bars and EPCH1-4 models. Fetches zones from Supabase, runs entry detection, and exports detected entries to the `trades_2` table. Exit management and P&L calculation are handled by secondary processors downstream.

## Architecture

```
03_backtest/
├── app.py                    # Module launcher entry point
├── config.py                 # Module configuration
├── CLAUDE.md                 # AI context documentation
├── README.md                 # Human documentation
├── backtest_gui/
│   ├── __init__.py
│   ├── main.py               # PyQt6 app entry point
│   ├── main_window.py        # Main window with terminal output
│   └── styles.py             # Dark theme stylesheet
├── scripts/
│   ├── __init__.py
│   └── run_backtest.py       # CLI entry detection runner
├── engine/
│   ├── __init__.py
│   ├── trade_simulator.py    # Entry collection (EntryRecord)
│   └── entry_models.py       # EPCH1-4 entry detection
├── models/
│   ├── __init__.py
│   └── exit_models.py        # (Legacy - not used in core pipeline)
└── data/
    ├── __init__.py
    ├── zone_loader.py        # ZoneData dataclass
    ├── supabase_zone_loader.py  # Load zones from Supabase
    ├── m5_fetcher.py         # Polygon M5 bar data (used by secondary processors)
    ├── s15_fetcher.py        # Polygon S15 bar data
    └── trades_exporter.py    # Export to Supabase trades_2 table
```

## Entry Points

```bash
# Launch GUI (primary usage)
python 03_backtest/app.py

# CLI mode (for automation)
python 03_backtest/scripts/run_backtest.py 2026-01-20
python 03_backtest/scripts/run_backtest.py 2026-01-20 --dry-run
python 03_backtest/scripts/run_backtest.py 2026-01-20 --no-export
```

## Entry Detection Model

The backtest core uses S15 (15-second) bars for high-granularity entry detection:
- **S15 bars**: Scanned for zone touches using EPCH1-4 models
- **No exit management**: Exits are handled by secondary processors

### Entry Models (EPCH1-4)

| Code | Name | Zone Type | Pattern |
|------|------|-----------|---------|
| EPCH1 | Primary Continuation | Primary | Price traverses through zone |
| EPCH2 | Primary Rejection | Primary | Price rejects from zone boundary |
| EPCH3 | Secondary Continuation | Secondary | Price traverses through zone |
| EPCH4 | Secondary Rejection | Secondary | Price rejects from zone boundary |

## Configuration (config.py)

Key settings:
- `SUPABASE_*` - Database connection
- `POLYGON_API_KEY` - Market data API
- `ENTRY_START_TIME` / `ENTRY_END_TIME` - Entry window (09:30-15:30 ET)
- `ENTRY_MODELS` - EPCH1-4 model definitions

## GUI Features

- **Date Selection**: Single date picker for backtest date
- **Terminal Output**: Real-time progress with color coding
- **Progress Bar**: Tracks completion via `[X/N]` pattern
- **Control Buttons**: RUN BACKTEST, STOP, CLEAR ENTRIES

## Data Flow

1. **Load Zones**: Fetch primary/secondary zones from Supabase `setups` table
2. **Fetch S15 Bars**: Get 15-second bar data from Polygon API
3. **Detect Entries**: Scan S15 bars for zone touches (EPCH1-4)
4. **Export Entries**: Upsert detected entries to Supabase `trades_2` table

## Database Tables

### Input: `setups`
- Zone definitions with bias, levels, targets

### Output: `trades_2`
- trade_id, date, ticker, model, zone_type, direction
- zone_high, zone_low, entry_price, entry_time
- created_at, updated_at

## Dependencies

- PyQt6 (GUI framework)
- psycopg2 (PostgreSQL)
- requests (Polygon API)
- pytz (timezone handling)

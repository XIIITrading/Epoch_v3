# 02_dow_ai - AI Context

## Module Purpose
Claude-powered trading assistant with PyQt6 tools for real-time analysis and batch testing.

## Tools

### Entry Qualifier (`entry_qualifier/`)
- **Unchanged from V1** - Direct copy, no modifications
- Real-time indicator display for up to 6 tickers
- Refreshes on minute boundaries during market hours
- DOW AI query integration for entry analysis
- Health score calculation (10-factor system)

### DOW Analysis (`dow_analysis/`)
- **New in V2** - Clean PyQt6 interface
- Batch size selector: 50, 250, 500, 1000 trades
- Terminal-style output (80% of screen)
- Runs `batch_analyzer/scripts/run_batch.py` via QProcess
- Modes: Claude API, Rule-Based, Dry Run

### Batch Analyzer (`batch_analyzer/`)
- Backend for batch analysis
- Trade loading from Supabase
- Claude API integration for predictions
- Accuracy tracking and reporting

## Key Files

```
app.py                           # Module launcher with tool selection
entry_qualifier/main.py          # Entry Qualifier entry point
dow_analysis/main.py             # DOW Analysis entry point
dow_analysis/main_window.py      # DOW Analysis main window
batch_analyzer/scripts/run_batch.py  # Batch analysis script
batch_analyzer/config.py         # API keys, model selection
```

## Running

```bash
python app.py                    # Launcher GUI
python app.py --entry-qualifier  # Direct to Entry Qualifier
python app.py --dow-analysis     # Direct to DOW Analysis
```

## Configuration

### Batch Analyzer Config (`batch_analyzer/config.py`)
- `CLAUDE_MODEL`: Model for batch predictions
- `DB_CONFIG`: Supabase connection settings
- `BATCH_SIZE`: Checkpoint frequency
- `M1_RAMPUP_BARS`: Bars to include in analysis

### Entry Qualifier Config (`entry_qualifier/eq_config.py`)
- `MAX_TICKERS`: Maximum concurrent tickers (6)
- `REFRESH_INTERVAL_MS`: Update frequency (60000ms)
- `ROLLING_BARS`: Bars to display (25)

## Dependencies
- PyQt6 for UI
- anthropic for Claude API
- psycopg2-binary for Supabase
- pandas for data manipulation

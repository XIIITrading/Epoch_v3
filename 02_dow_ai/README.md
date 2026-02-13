# 02_dow_ai

Epoch Trading System - DOW AI Module

## Overview

Claude-powered trading assistant with two PyQt6 tools:

1. **Entry Qualifier** - Real-time indicator display for live trading
2. **DOW Analysis** - Batch analyzer with terminal output for testing DOW implementations

## Quick Start

```bash
# Launch the module launcher (choose tool from GUI)
python app.py

# Or launch tools directly:
python app.py --entry-qualifier   # Entry Qualifier tool
python app.py --dow-analysis      # DOW Analysis tool

# Or run tools independently:
python entry_qualifier/main.py
python dow_analysis/main.py
```

## Tools

### Entry Qualifier
- Displays rolling indicator data for up to 6 tickers
- Real-time updates on minute boundaries during market hours
- DOW AI query integration for entry analysis
- Health score calculation with 10-factor system

### DOW Analysis
- Batch size selection: 50, 250, 500, 1000 trades
- Three modes:
  - **Claude API**: Uses Claude AI for predictions (costs tokens)
  - **Rule-Based**: Uses rule-based predictions (no API calls)
  - **Dry Run**: Preview what would be processed (no changes)
- Terminal-style output (80% of screen)
- Real-time progress tracking
- Stop/resume capability

## Folder Structure

```
02_dow_ai/
├── app.py                 # Module launcher
├── entry_qualifier/       # Entry Qualifier tool (unchanged from V1)
│   ├── main.py
│   ├── eq_config.py
│   ├── ai/
│   ├── calculations/
│   ├── data/
│   └── ui/
├── dow_analysis/          # DOW Analysis tool (new in V2)
│   ├── main.py
│   ├── main_window.py
│   └── styles.py
├── batch_analyzer/        # Batch analysis backend
│   ├── config.py
│   ├── analyzer/
│   ├── data/
│   ├── models/
│   ├── prompts/
│   ├── reports/
│   └── scripts/
└── ai_context/            # AI context and prompts
```

## Configuration

API keys and database credentials are configured in:
- `batch_analyzer/config.py` - Batch analyzer settings
- `entry_qualifier/eq_config.py` - Entry qualifier settings

## Dependencies

- PyQt6 >= 6.4.0
- anthropic
- pandas
- psycopg2-binary

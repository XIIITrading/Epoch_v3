# Epoch Training Module

Flash card review system for deliberate practice of trade evaluation.

## Overview

This module presents historical trades in a "flashcard" format where you evaluate setups at the right edge (entry moment) BEFORE seeing outcomes. Over hundreds of repetitions, this builds calibrated intuition for trade quality.

## Features

- **Multi-timeframe charts** (H1, M15, M5) with zone overlays
- **Evaluate mode**: See trade at entry, assess Strong/Weak/No Trade
- **Reveal mode**: See full trade with MFE/MAE markers and outcome
- **Calibration tracking**: Monitor your accuracy by assessment type
- **Bookmap integration**: View order flow snapshots (when available)
- **Queue shuffling**: Prevent temporal memory leakage

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up database schema (one-time)
python run_schema.py
```

## Usage

```bash
# Start the app (Option 1 - via launcher)
python app.py

# Start the app (Option 2 - direct streamlit)
streamlit run streamlit_app.py
```

## How It Works

### Evaluate Mode
1. Trade is shown at entry moment (right edge)
2. You see: zones, entry price, historical context
3. You DON'T see: exit, outcome, MFE/MAE
4. Commit your assessment: Strong, Weak, or No Trade

### Reveal Mode
1. Full trade is shown (entry through exit)
2. MFE (Maximum Favorable Excursion) marked
3. MAE (Maximum Adverse Excursion) marked
4. Outcome statistics displayed
5. Feedback on whether your read was correct
6. Add notes and advance to next trade

### Calibration Metrics

- **Strong Setup accuracy**: % of "Strong" calls that were winners
- **Weak Setup accuracy**: % of "Weak" calls that were losers
- **No Trade accuracy**: % of "No Trade" calls that were losers/breakeven

Target: >60% accuracy indicates good pattern recognition.

## Data Requirements

The module requires trade data in Supabase:
- `trades` table with entry/exit data
- `optimal_trade` table with MFE/MAE events
- `zones` table with zone boundaries

Run the database export (Module 11) to populate these tables.

## File Structure

```
06_training/
├── app.py                  # Python launcher (runs Streamlit)
├── streamlit_app.py        # Main Streamlit application
├── config.py               # Configuration settings
├── run_schema.py           # Database schema setup
├── requirements.txt        # Python dependencies
├── components/
│   ├── flashcard_ui.py     # Evaluate/reveal state machine
│   ├── charts.py           # Plotly chart builder
│   ├── stats_panel.py      # Trade statistics display
│   ├── calibration_tracker.py  # Performance metrics
│   ├── navigation.py       # Sidebar filters
│   └── bookmap_viewer.py   # Image viewer
├── data/
│   ├── supabase_client.py  # Database operations
│   ├── polygon_client.py   # Bar data fetching
│   └── cache_manager.py    # Data caching
├── models/
│   ├── trade.py            # Trade dataclasses
│   └── review.py           # Review dataclasses
└── schema/
    ├── 01_trade_reviews.sql    # Reviews table
    ├── 02_trade_images.sql     # Bookmap images table
    └── 03_views_and_functions.sql  # Views and functions
```

## Keyboard Shortcuts

- **A**: Strong Setup
- **B**: Weak Setup
- **C**: No Trade
- **→** / **Space**: Next Trade
- **N**: Focus Notes field

## Version History

- **1.0.0**: Initial release with core flashcard functionality

## Author

XIII Trading LLC

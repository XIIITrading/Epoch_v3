# Epoch Trading System v2.0
XIII Trading LLC

## Overview
The Epoch System identifies institutional commitment within user-defined market regimes by analyzing high-volume nodes at precise $0.01 price granularity.

## V2 Architecture

```
Epoch/
├── 00_shared/              # Shared infrastructure (installable package)
│   ├── config/             # Credentials and configuration
│   ├── data/               # Polygon and Supabase clients
│   ├── indicators/         # Shared indicator library
│   ├── models/             # Pydantic data models
│   ├── ui/                 # PyQt6 components
│   └── utils/              # Utility functions
│
├── 01_application/         # Main trading application
├── 02_dow_ai/             # AI trading assistant
├── 03_backtest/           # Backtesting engine
├── 04_indicators/         # Edge testing framework
├── 05_system_analysis/    # Statistical analysis
├── 06_training/           # Training module
├── 07_market_analysis/    # Historical journals
│
└── launcher.py            # Master launcher
```

## Installation

1. Install the shared package:
```bash
cd C:\XIIITradingSystems\Epoch
pip install -e ./00_shared
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Master Launcher
```bash
python launcher.py
```

### Individual Modules
```bash
python 01_application/app.py
python 02_dow_ai/app.py
python 03_backtest/app.py
python 04_indicators/app.py
python 05_system_analysis/app.py
python 06_training/app.py
```

## V1 Compatibility
The original V1 codebase is preserved at:
```
C:\XIIITradingSystems\Epoch_v1
```

Use V1 for live trading until V2 migration is complete.

## Documentation
- See each module's README.md for module-specific documentation
- See CLAUDE.md files for AI assistant context
- See `/00_shared/docs/` for system architecture docs

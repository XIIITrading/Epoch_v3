# 00_shared - Epoch Shared Infrastructure

This package provides centralized infrastructure for all Epoch Trading System modules.

## Installation

```bash
cd C:\XIIITradingSystems\Epoch
pip install -e ./00_shared
```

## Components

### Config
Centralized configuration and credentials.

```python
from shared.config import POLYGON_API_KEY, SUPABASE_DB_CONFIG, ANTHROPIC_API_KEY
from shared.config import EpochConfig, MarketConfig
```

### Data Layer
Unified data access for Polygon and Supabase.

```python
from shared.data.polygon import PolygonClient
from shared.data.supabase import SupabaseClient

# Get market data
client = PolygonClient()
df = client.get_bars("AAPL", "5min", "2024-01-01", "2024-01-31")

# Get database data
with SupabaseClient() as db:
    zones = db.get_zones("AAPL")
```

### Indicators
Shared indicator library used across all modules.

```python
from shared.indicators.core import sma, vwap, atr, volume_delta
from shared.indicators.structure import get_market_structure
from shared.indicators.health import calculate_health_score
```

### UI Components
PyQt6 components with consistent dark theme styling.

```python
from shared.ui import BaseWindow, DARK_STYLESHEET, COLORS

class MyWindow(BaseWindow):
    def __init__(self):
        super().__init__(title="My Module")
        # UI setup here
```

## Directory Structure

```
00_shared/
├── config/
│   ├── credentials.py    # API keys and DB credentials
│   ├── epoch_config.py   # System configuration
│   └── market_config.py  # Market hours and timing
│
├── data/
│   ├── polygon/          # Polygon.io client
│   └── supabase/         # Supabase client
│
├── indicators/
│   ├── core/             # Core indicators (SMA, VWAP, ATR, etc.)
│   ├── structure/        # Market structure detection
│   └── health/           # Health scoring
│
├── models/               # Shared Pydantic models
│
├── ui/
│   ├── base_window.py    # Base PyQt window
│   ├── styles.py         # Dark theme stylesheet
│   ├── widgets/          # Reusable widgets
│   └── charts/           # Chart components
│
├── utils/                # Utility functions
│
└── docs/                 # Documentation
```

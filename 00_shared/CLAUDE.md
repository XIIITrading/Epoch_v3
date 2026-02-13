# 00_shared - AI Context

## Purpose
Centralized shared infrastructure for all Epoch Trading System modules.

## Key Files

### Configuration
- `config/credentials.py` - API keys for Polygon, Supabase, Anthropic
- `config/epoch_config.py` - System-wide settings and constants
- `config/market_config.py` - Market hours and timing utilities

### Data Layer
- `data/polygon/client.py` - Polygon.io API client for market data
- `data/supabase/client.py` - Supabase PostgreSQL client for database

### Indicators
All modules use these shared indicator implementations:
- `indicators/core/sma.py` - SMA and spread calculations
- `indicators/core/vwap.py` - Volume-weighted average price
- `indicators/core/atr.py` - Average true range
- `indicators/core/volume_delta.py` - Volume delta calculations
- `indicators/core/volume_roc.py` - Volume rate of change
- `indicators/core/cvd.py` - Cumulative volume delta
- `indicators/core/candle_range.py` - Candle range analysis
- `indicators/structure/market_structure.py` - Fractal-based structure
- `indicators/health/health_score.py` - 10-factor health scoring

### UI
- `ui/base_window.py` - Base PyQt6 window class
- `ui/styles.py` - Dark theme stylesheet and colors

## Import Patterns
```python
# Config
from shared.config import POLYGON_API_KEY, EpochConfig, MarketConfig

# Data
from shared.data.polygon import PolygonClient
from shared.data.supabase import SupabaseClient

# Indicators
from shared.indicators.core import sma, vwap, atr
from shared.indicators.structure import get_market_structure
from shared.indicators.health import calculate_health_score

# UI
from shared.ui import BaseWindow, COLORS, DARK_STYLESHEET
```

## Modification Guidelines
- All API keys are in `credentials.py` - update there only
- Indicator logic changes affect ALL modules - test thoroughly
- UI style changes affect ALL modules - maintain consistency

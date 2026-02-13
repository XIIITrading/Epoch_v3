# Epoch Trading System v2.0 - AI Context

## System Purpose
Institutional-grade trading analysis platform for identifying high-probability trading zones through high-volume node analysis.

## Architecture Overview

### Shared Infrastructure (00_shared/)
All modules import from this centralized package:
- **config/** - Credentials and system configuration
- **data/** - Polygon.io and Supabase clients
- **indicators/** - Shared indicator calculations
- **ui/** - PyQt6 base components and styling
- **models/** - Pydantic data models
- **utils/** - Common utilities

### Modules
1. **01_application/** - Main trading app with 8-stage zone pipeline
2. **02_dow_ai/** - Claude-powered trading assistant (has PyQt already)
3. **03_backtest/** - Trade simulation with 13 secondary processors
4. **04_indicators/** - Edge testing framework for 7 indicators
5. **05_system_analysis/** - Monte Carlo and statistical analysis
6. **06_training/** - Interactive training with flashcards
7. **07_market_analysis/** - Historical trade journals by month

## Key Design Decisions

### Centralization
- Single source for credentials (00_shared/config/credentials.py)
- Single indicator library (00_shared/indicators/)
- Single data layer (00_shared/data/)
- Consistent UI styling (00_shared/ui/)

### Module Independence
- Each module can run standalone via `python XX_module/app.py`
- Master launcher at `launcher.py`
- Modules import from `shared.*` namespace

### V1 Preservation
- V1 is fully preserved at `C:\XIIITradingSystems\Epoch_v1`
- V1 should be used for live trading until V2 migration is complete
- V2 modules are 1:1 copies with no calculation changes

## Import Patterns
```python
# Always use these patterns in V2 modules
from shared.config import POLYGON_API_KEY, EpochConfig
from shared.data.polygon import PolygonClient
from shared.data.supabase import SupabaseClient
from shared.indicators.core import sma, vwap, atr
from shared.ui import BaseWindow, COLORS
```

## Migration Status
- [x] 00_shared - Core infrastructure complete
- [x] 01_application - Complete (8-stage zone pipeline with PyQt)
- [ ] 02_dow_ai - Pending (template for PyQt)
- [ ] 03_backtest - Pending
- [ ] 04_indicators - Pending
- [x] 05_system_analysis - Complete (Hybrid approach: V1 calculations + PNG export + PyQt viewer)
- [ ] 06_training - Pending
- [ ] 07_market_analysis - Pending

## 05_system_analysis Architecture
Uses a hybrid approach for visualization:
1. **chart_exporter.py** - Uses V1 Plotly chart logic, exports to PNG via kaleido
2. **app.py** - PyQt6 viewer that displays exported PNG images
3. Connects to V1 Supabase client for data loading
4. Charts are identical to Streamlit version (same Plotly code)

## File Naming Conventions
- `app.py` - Main PyQt application entry point
- `runner.py` - CLI/batch processing entry point
- `config.py` - Module-specific configuration
- `README.md` - Human documentation
- `CLAUDE.md` - AI context documentation

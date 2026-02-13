# Epoch Analysis Tool - Session-by-Session Implementation Guide

This guide provides detailed instructions for each development session. Claude Code should follow these steps sequentially.

---

## Key Design Requirements

### Input Structure
The app accepts **10 ticker rows**, each with:
- Ticker symbol (e.g., NVDA)
- Custom anchor date (e.g., 2024-11-01)

### Calculation Runs
When user clicks "Run Analysis", the system runs **4 calculations per ticker**:

| Run | Anchor Date | UI Tabs | PDF Report |
|-----|-------------|---------|------------|
| 1. Custom | User-provided date | Yes | Yes |
| 2. Prior Day | Previous trading day | Yes | No (Phase 2) |
| 3. Prior Week | Previous Friday | Yes | No (Phase 2) |
| 4. Prior Month | Last day of prior month | Yes | No (Phase 2) |

**UI Structure:**
- All 4 anchor types have their own viewable tabs
- Sidebar selector to switch between: Custom / Prior Day / Prior Week / Prior Month
- Each view shows: Market Overview, Bar Data, Raw Zones, Zone Results, Analysis

**PDF Generation:**
- Phase 1: PDF report (from `08_visualization` logic) runs only for Custom anchor
- Phase 2: Add PDF generation for preset anchors after testing

### Self-Contained Module
All code is **ported** into `05_analysis_tool`. No imports from `02_zone_system` or `01_market_scanner` at runtime.

---

## How to Use This Guide

1. Start each session by reading the relevant section
2. Complete all tasks in order
3. Run validation checkpoints before proceeding
4. Document any issues in the Post-Session Notes
5. Do not skip sessions - dependencies build on each other

---

# SESSION 1: Project Setup & Data Models

## Objective
Create the project foundation: directory structure, dependencies, configuration, and data models.

## Step 1.1: Create Directory Structure

```bash
cd C:\XIIITradingSystems\Epoch\05_analysis_tool

# Create all directories
mkdir config
mkdir core
mkdir data
mkdir calculators
mkdir pages
mkdir components
mkdir utils
```

## Step 1.2: Create requirements.txt

Create file: `C:\XIIITradingSystems\Epoch\05_analysis_tool\requirements.txt`

```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
pydantic>=2.0.0
polygon-api-client>=1.12.0
plotly>=5.18.0
pytz>=2023.3
python-dotenv>=1.0.0
pandas-market-calendars>=4.3.0
requests>=2.31.0
```

## Step 1.3: Create config/__init__.py

Create file: `C:\XIIITradingSystems\Epoch\05_analysis_tool\config\__init__.py`

```python
from .settings import *
from .weights import *
```

## Step 1.4: Create config/settings.py

Create file: `C:\XIIITradingSystems\Epoch\05_analysis_tool\config\settings.py`

```python
"""
Application settings and configuration.
"""
from pathlib import Path
from datetime import date, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent.parent
EPOCH_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data" / "cache"
ZONE_SYSTEM_DIR = EPOCH_ROOT / "02_zone_system"
MARKET_SCANNER_DIR = EPOCH_ROOT / "01_market_scanner"

# Create cache directory
DATA_DIR.mkdir(parents=True, exist_ok=True)

# API Configuration
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")

# Default Filter Thresholds
DEFAULT_MIN_ATR = 2.0
DEFAULT_MIN_PRICE = 10.0
DEFAULT_MIN_GAP_PERCENT = 2.0

# Zone Calculation
ZONE_ATR_DIVISOR = 2.0  # Zone = POC ± (M15_ATR / 2)
MAX_ZONES_PER_TICKER = 10
PROXIMITY_ATR_MULTIPLIER = 2.0  # Zones within 2 ATR of price

# Anchor Date Presets
ANCHOR_PRESETS = {
    "prior_day": "Previous Trading Day Close",
    "prior_week": "Previous Week Close (Friday)",
    "prior_month": "Previous Month Close",
    "ytd": "Year to Date (Jan 1)",
    "custom": "Custom Date"
}

# Index Tickers (always analyzed for market structure)
INDEX_TICKERS = ["SPY", "QQQ", "DIA"]

# UI Configuration
MAX_TICKERS = 10
DEFAULT_TICKER_LIST = "sp500"

# Cache TTL (seconds)
CACHE_TTL_INTRADAY = 3600  # 1 hour
CACHE_TTL_DAILY = 86400    # 24 hours
```

## Step 1.5: Create config/weights.py

Create file: `C:\XIIITradingSystems\Epoch\05_analysis_tool\config\weights.py`

Copy the weights configuration from `02_zone_system/05_raw_zones/epoch_config.py`:

```python
"""
Zone calculation weights and thresholds.
Ported from: 02_zone_system/05_raw_zones/epoch_config.py
"""

# POC Base Weights (by volume rank)
EPOCH_POC_BASE_WEIGHTS = {
    'hvn_poc1': 3.0,
    'hvn_poc2': 2.5,
    'hvn_poc3': 2.0,
    'hvn_poc4': 1.5,
    'hvn_poc5': 1.0,
    'hvn_poc6': 0.8,
    'hvn_poc7': 0.6,
    'hvn_poc8': 0.4,
    'hvn_poc9': 0.2,
    'hvn_poc10': 0.1
}

# Zone Weights (confluence level weights)
ZONE_WEIGHTS = {
    # Monthly Levels
    'm1_01': {'weight': 3.0, 'category': 'm1', 'con_type': 'monthly_level'},
    'm1_02': {'weight': 3.0, 'category': 'm1', 'con_type': 'monthly_level'},
    'm1_03': {'weight': 3.0, 'category': 'm1', 'con_type': 'monthly_level'},
    'm1_04': {'weight': 3.0, 'category': 'm1', 'con_type': 'monthly_level'},

    # Weekly Levels
    'w1_01': {'weight': 2.0, 'category': 'w1', 'con_type': 'weekly_level'},
    'w1_02': {'weight': 2.0, 'category': 'w1', 'con_type': 'weekly_level'},
    'w1_03': {'weight': 2.0, 'category': 'w1', 'con_type': 'weekly_level'},
    'w1_04': {'weight': 2.0, 'category': 'w1', 'con_type': 'weekly_level'},

    # Daily Levels
    'd1_01': {'weight': 1.0, 'category': 'd1', 'con_type': 'daily_level'},
    'd1_02': {'weight': 1.0, 'category': 'd1', 'con_type': 'daily_level'},
    'd1_03': {'weight': 1.0, 'category': 'd1', 'con_type': 'daily_level'},
    'd1_04': {'weight': 1.0, 'category': 'd1', 'con_type': 'daily_level'},

    # Prior Period - Daily
    'd1_po': {'weight': 1.0, 'category': 'd1', 'con_type': 'prior_daily'},
    'd1_ph': {'weight': 1.0, 'category': 'd1', 'con_type': 'prior_daily'},
    'd1_pl': {'weight': 1.0, 'category': 'd1', 'con_type': 'prior_daily'},
    'd1_pc': {'weight': 1.0, 'category': 'd1', 'con_type': 'prior_daily'},
    'd1_onh': {'weight': 1.0, 'category': 'd1', 'con_type': 'prior_daily'},
    'd1_onl': {'weight': 1.0, 'category': 'd1', 'con_type': 'prior_daily'},

    # Prior Period - Weekly
    'w1_po': {'weight': 2.0, 'category': 'w1', 'con_type': 'prior_weekly'},
    'w1_ph': {'weight': 2.0, 'category': 'w1', 'con_type': 'prior_weekly'},
    'w1_pl': {'weight': 2.0, 'category': 'w1', 'con_type': 'prior_weekly'},
    'w1_pc': {'weight': 2.0, 'category': 'w1', 'con_type': 'prior_weekly'},

    # Prior Period - Monthly
    'm1_po': {'weight': 3.0, 'category': 'm1', 'con_type': 'prior_monthly'},
    'm1_ph': {'weight': 3.0, 'category': 'm1', 'con_type': 'prior_monthly'},
    'm1_pl': {'weight': 3.0, 'category': 'm1', 'con_type': 'prior_monthly'},
    'm1_pc': {'weight': 3.0, 'category': 'm1', 'con_type': 'prior_monthly'},

    # Options Levels
    'op_01': {'weight': 2.5, 'category': 'opt', 'con_type': 'options_level'},
    'op_02': {'weight': 2.5, 'category': 'opt', 'con_type': 'options_level'},
    'op_03': {'weight': 2.0, 'category': 'opt', 'con_type': 'options_level'},
    'op_04': {'weight': 2.0, 'category': 'opt', 'con_type': 'options_level'},
    'op_05': {'weight': 1.5, 'category': 'opt', 'con_type': 'options_level'},
    'op_06': {'weight': 1.5, 'category': 'opt', 'con_type': 'options_level'},
    'op_07': {'weight': 1.0, 'category': 'opt', 'con_type': 'options_level'},
    'op_08': {'weight': 1.0, 'category': 'opt', 'con_type': 'options_level'},
    'op_09': {'weight': 0.5, 'category': 'opt', 'con_type': 'options_level'},
    'op_10': {'weight': 0.5, 'category': 'opt', 'con_type': 'options_level'},

    # Market Structure Levels
    'd1_s': {'weight': 1.5, 'category': 'd1', 'con_type': 'market_structure_daily'},
    'd1_w': {'weight': 1.5, 'category': 'd1', 'con_type': 'market_structure_daily'},
    'h4_s': {'weight': 1.25, 'category': 'h4', 'con_type': 'market_structure_h4'},
    'h4_w': {'weight': 1.25, 'category': 'h4', 'con_type': 'market_structure_h4'},
    'h1_s': {'weight': 1.0, 'category': 'h1', 'con_type': 'market_structure_hourly'},
    'h1_w': {'weight': 1.0, 'category': 'h1', 'con_type': 'market_structure_hourly'},
    'm15_s': {'weight': 0.75, 'category': 'm15', 'con_type': 'market_structure_m15'},
    'm15_w': {'weight': 0.75, 'category': 'm15', 'con_type': 'market_structure_m15'},
}

# Camarilla Level Weights
CAM_WEIGHTS = {
    # Daily
    'd1_s6': {'weight': 1.0, 'category': 'd1', 'con_type': 'daily_cam'},
    'd1_s4': {'weight': 1.0, 'category': 'd1', 'con_type': 'daily_cam'},
    'd1_s3': {'weight': 1.0, 'category': 'd1', 'con_type': 'daily_cam'},
    'd1_r3': {'weight': 1.0, 'category': 'd1', 'con_type': 'daily_cam'},
    'd1_r4': {'weight': 1.0, 'category': 'd1', 'con_type': 'daily_cam'},
    'd1_r6': {'weight': 1.0, 'category': 'd1', 'con_type': 'daily_cam'},
    # Weekly
    'w1_s6': {'weight': 2.0, 'category': 'w1', 'con_type': 'weekly_cam'},
    'w1_s4': {'weight': 2.0, 'category': 'w1', 'con_type': 'weekly_cam'},
    'w1_s3': {'weight': 2.0, 'category': 'w1', 'con_type': 'weekly_cam'},
    'w1_r3': {'weight': 2.0, 'category': 'w1', 'con_type': 'weekly_cam'},
    'w1_r4': {'weight': 2.0, 'category': 'w1', 'con_type': 'weekly_cam'},
    'w1_r6': {'weight': 2.0, 'category': 'w1', 'con_type': 'weekly_cam'},
    # Monthly
    'm1_s6': {'weight': 3.0, 'category': 'm1', 'con_type': 'monthly_cam'},
    'm1_s4': {'weight': 3.0, 'category': 'm1', 'con_type': 'monthly_cam'},
    'm1_s3': {'weight': 3.0, 'category': 'm1', 'con_type': 'monthly_cam'},
    'm1_r3': {'weight': 3.0, 'category': 'm1', 'con_type': 'monthly_cam'},
    'm1_r4': {'weight': 3.0, 'category': 'm1', 'con_type': 'monthly_cam'},
    'm1_r6': {'weight': 3.0, 'category': 'm1', 'con_type': 'monthly_cam'},
}

# Bucket Weights (max contribution per category)
BUCKET_WEIGHTS = {
    'monthly_level': 3.0,
    'weekly_level': 2.0,
    'daily_level': 1.0,
    'daily_cam': 1.0,
    'weekly_cam': 2.0,
    'monthly_cam': 3.0,
    'prior_daily': 1.0,
    'prior_weekly': 2.0,
    'prior_monthly': 3.0,
    'options_level': 2.5,
    'market_structure_daily': 1.5,
    'market_structure_h4': 1.25,
    'market_structure_hourly': 1.0,
    'market_structure_m15': 0.75,
}

# Ranking Thresholds (L1-L5)
RANKING_SCORE_THRESHOLDS = {
    'L5': 12.0,
    'L4': 9.0,
    'L3': 6.0,
    'L2': 3.0,
    'L1': 0.0
}

# Tier Mapping
TIER_MAP = {
    'L1': 'T1',
    'L2': 'T1',
    'L3': 'T2',
    'L4': 'T3',
    'L5': 'T3'
}

# Zone Name Mapping (for readable confluence output)
ZONE_NAME_MAP = {
    'm1_01': 'M Open', 'm1_02': 'M High', 'm1_03': 'M Low', 'm1_04': 'M Close',
    'm1_po': 'PM Open', 'm1_ph': 'PM High', 'm1_pl': 'PM Low', 'm1_pc': 'PM Close',
    'w1_01': 'W Open', 'w1_02': 'W High', 'w1_03': 'W Low', 'w1_04': 'W Close',
    'w1_po': 'PW Open', 'w1_ph': 'PW High', 'w1_pl': 'PW Low', 'w1_pc': 'PW Close',
    'd1_01': 'D Open', 'd1_02': 'D High', 'd1_03': 'D Low', 'd1_04': 'D Close',
    'd1_po': 'PD Open', 'd1_ph': 'PD High', 'd1_pl': 'PD Low', 'd1_pc': 'PD Close',
    'd1_onh': 'ON High', 'd1_onl': 'ON Low',
    'd1_s6': 'D S6', 'd1_s4': 'D S4', 'd1_s3': 'D S3',
    'd1_r3': 'D R3', 'd1_r4': 'D R4', 'd1_r6': 'D R6',
    'w1_s6': 'W S6', 'w1_s4': 'W S4', 'w1_s3': 'W S3',
    'w1_r3': 'W R3', 'w1_r4': 'W R4', 'w1_r6': 'W R6',
    'm1_s6': 'M S6', 'm1_s4': 'M S4', 'm1_s3': 'M S3',
    'm1_r3': 'M R3', 'm1_r4': 'M R4', 'm1_r6': 'M R6',
    'op_01': 'OP1', 'op_02': 'OP2', 'op_03': 'OP3', 'op_04': 'OP4', 'op_05': 'OP5',
    'op_06': 'OP6', 'op_07': 'OP7', 'op_08': 'OP8', 'op_09': 'OP9', 'op_10': 'OP10',
    'd1_s': 'D1 Strong', 'd1_w': 'D1 Weak',
    'h4_s': 'H4 Strong', 'h4_w': 'H4 Weak',
    'h1_s': 'H1 Strong', 'h1_w': 'H1 Weak',
    'm15_s': 'M15 Strong', 'm15_w': 'M15 Weak',
}
```

## Step 1.6: Create core/data_models.py

Create file: `C:\XIIITradingSystems\Epoch\05_analysis_tool\core\data_models.py`

```python
"""
Pydantic data models for the Epoch Analysis Tool.
These replace the Excel cell structures with typed Python objects.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, datetime
from enum import Enum


class Direction(str, Enum):
    BULL_PLUS = "Bull+"
    BULL = "Bull"
    NEUTRAL = "Neutral"
    BEAR = "Bear"
    BEAR_PLUS = "Bear+"
    ERROR = "ERROR"


class Rank(str, Enum):
    L5 = "L5"
    L4 = "L4"
    L3 = "L3"
    L2 = "L2"
    L1 = "L1"


class Tier(str, Enum):
    T3 = "T3"  # High Quality (L4, L5)
    T2 = "T2"  # Medium Quality (L3)
    T1 = "T1"  # Lower Quality (L1, L2)


class TickerInput(BaseModel):
    """Input for a single ticker analysis."""
    ticker: str
    analysis_date: date
    anchor_date: date  # Epoch start date
    price: Optional[float] = None


class MarketStructure(BaseModel):
    """Market structure analysis for a ticker."""
    ticker: str
    datetime: datetime
    price: float

    # D1 Timeframe
    d1_direction: Direction = Direction.NEUTRAL
    d1_strong: Optional[float] = None
    d1_weak: Optional[float] = None

    # H4 Timeframe
    h4_direction: Direction = Direction.NEUTRAL
    h4_strong: Optional[float] = None
    h4_weak: Optional[float] = None

    # H1 Timeframe
    h1_direction: Direction = Direction.NEUTRAL
    h1_strong: Optional[float] = None
    h1_weak: Optional[float] = None

    # M15 Timeframe
    m15_direction: Direction = Direction.NEUTRAL
    m15_strong: Optional[float] = None
    m15_weak: Optional[float] = None

    # Composite
    composite: Direction = Direction.NEUTRAL

    def calculate_composite(self) -> Direction:
        """Calculate composite direction from all timeframes."""
        weights = {'d1': 1.5, 'h4': 1.5, 'h1': 1.0, 'm15': 0.5}
        score = 0.0

        for tf, weight in weights.items():
            direction = getattr(self, f"{tf}_direction")
            if direction in [Direction.BULL, Direction.BULL_PLUS]:
                score += weight
            elif direction in [Direction.BEAR, Direction.BEAR_PLUS]:
                score -= weight

        max_score = sum(weights.values())  # 4.5

        if score >= 3.5:
            return Direction.BULL_PLUS
        elif score > 0:
            return Direction.BULL
        elif score <= -3.5:
            return Direction.BEAR_PLUS
        elif score < 0:
            return Direction.BEAR
        else:
            return Direction.NEUTRAL


class OHLCData(BaseModel):
    """OHLC data for a period."""
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None


class BarData(BaseModel):
    """Complete bar data for a ticker (replaces bar_data sheet)."""
    ticker: str
    ticker_id: str
    analysis_date: date

    # Current price
    price: float

    # Monthly OHLC
    m1_current: OHLCData = Field(default_factory=OHLCData)
    m1_prior: OHLCData = Field(default_factory=OHLCData)

    # Weekly OHLC
    w1_current: OHLCData = Field(default_factory=OHLCData)
    w1_prior: OHLCData = Field(default_factory=OHLCData)

    # Daily OHLC
    d1_current: OHLCData = Field(default_factory=OHLCData)
    d1_prior: OHLCData = Field(default_factory=OHLCData)

    # Overnight
    overnight_high: Optional[float] = None
    overnight_low: Optional[float] = None

    # Options levels (top 10 by OI)
    options_levels: List[float] = Field(default_factory=list)

    # ATR values
    m5_atr: Optional[float] = None
    m15_atr: Optional[float] = None
    h1_atr: Optional[float] = None
    d1_atr: Optional[float] = None

    # Camarilla levels
    camarilla_daily: Dict[str, float] = Field(default_factory=dict)
    camarilla_weekly: Dict[str, float] = Field(default_factory=dict)
    camarilla_monthly: Dict[str, float] = Field(default_factory=dict)

    def get_all_levels(self) -> Dict[str, float]:
        """Get all technical levels as a flat dictionary."""
        levels = {}

        # Monthly
        levels['m1_01'] = self.m1_current.open
        levels['m1_02'] = self.m1_current.high
        levels['m1_03'] = self.m1_current.low
        levels['m1_04'] = self.m1_current.close
        levels['m1_po'] = self.m1_prior.open
        levels['m1_ph'] = self.m1_prior.high
        levels['m1_pl'] = self.m1_prior.low
        levels['m1_pc'] = self.m1_prior.close

        # Weekly
        levels['w1_01'] = self.w1_current.open
        levels['w1_02'] = self.w1_current.high
        levels['w1_03'] = self.w1_current.low
        levels['w1_04'] = self.w1_current.close
        levels['w1_po'] = self.w1_prior.open
        levels['w1_ph'] = self.w1_prior.high
        levels['w1_pl'] = self.w1_prior.low
        levels['w1_pc'] = self.w1_prior.close

        # Daily
        levels['d1_01'] = self.d1_current.open
        levels['d1_02'] = self.d1_current.high
        levels['d1_03'] = self.d1_current.low
        levels['d1_04'] = self.d1_current.close
        levels['d1_po'] = self.d1_prior.open
        levels['d1_ph'] = self.d1_prior.high
        levels['d1_pl'] = self.d1_prior.low
        levels['d1_pc'] = self.d1_prior.close

        # Overnight
        levels['d1_onh'] = self.overnight_high
        levels['d1_onl'] = self.overnight_low

        # Options
        for i, level in enumerate(self.options_levels, 1):
            levels[f'op_{i:02d}'] = level

        # Camarilla
        levels.update(self.camarilla_daily)
        levels.update(self.camarilla_weekly)
        levels.update(self.camarilla_monthly)

        return {k: v for k, v in levels.items() if v is not None}


class HVNResult(BaseModel):
    """HVN POC calculation result."""
    ticker: str
    start_date: date
    end_date: date
    bars_analyzed: int = 0

    # 10 POCs ranked by volume (poc1 = highest volume)
    pocs: List[float] = Field(default_factory=list)

    def get_poc(self, rank: int) -> Optional[float]:
        """Get POC by rank (1-10)."""
        if 1 <= rank <= len(self.pocs):
            return self.pocs[rank - 1]
        return None


class RawZone(BaseModel):
    """A single confluence zone before filtering."""
    ticker: str
    ticker_id: str
    analysis_date: date
    price: float
    direction: Direction

    zone_id: str
    poc_rank: int  # 1-10
    hvn_poc: float
    zone_high: float
    zone_low: float

    overlaps: int = 0
    score: float = 0.0
    rank: Rank = Rank.L1
    confluences: List[str] = Field(default_factory=list)

    @property
    def confluences_str(self) -> str:
        """Get confluences as comma-separated string."""
        return ", ".join(self.confluences)


class FilteredZone(RawZone):
    """A zone after filtering with tier and setup flags."""
    tier: Tier = Tier.T1

    # Setup flags
    is_bull_poc: bool = False
    is_bear_poc: bool = False

    # Target info (populated in setup analysis)
    bull_target: Optional[float] = None
    bear_target: Optional[float] = None


class Setup(BaseModel):
    """A trading setup (primary or secondary)."""
    ticker: str
    ticker_id: str
    direction: Direction

    zone_id: str
    hvn_poc: float
    zone_high: float
    zone_low: float
    tier: Tier

    target_id: Optional[str] = None
    target: Optional[float] = None
    risk_reward: Optional[float] = None

    @property
    def setup_string(self) -> str:
        """Generate PineScript-ready setup string."""
        return f"{self.ticker}|{self.direction.value}|{self.hvn_poc}|{self.zone_high}|{self.zone_low}|{self.target}"


class AnalysisResult(BaseModel):
    """Complete analysis result for a ticker."""
    ticker_input: TickerInput
    market_structure: Optional[MarketStructure] = None
    bar_data: Optional[BarData] = None
    hvn_result: Optional[HVNResult] = None
    raw_zones: List[RawZone] = Field(default_factory=list)
    filtered_zones: List[FilteredZone] = Field(default_factory=list)
    primary_setup: Optional[Setup] = None
    secondary_setup: Optional[Setup] = None


class ScanResult(BaseModel):
    """Market scanner result row."""
    rank: int
    ticker: str
    ticker_id: str
    price: float
    gap_percent: float

    overnight_volume: int
    prior_overnight_volume: int
    relative_overnight_volume: float
    relative_volume: float

    short_interest: Optional[float] = None
    days_to_cover: Optional[float] = None

    ranking_score: float
    atr: float
    prior_close: float

    scan_date: date
    scan_time: str
```

## Step 1.7: Create core/__init__.py

Create file: `C:\XIIITradingSystems\Epoch\05_analysis_tool\core\__init__.py`

```python
from .data_models import *
```

## Step 1.8: Create Placeholder Files

Create empty `__init__.py` files in all directories:

```python
# data/__init__.py
# calculators/__init__.py
# pages/__init__.py
# components/__init__.py
# utils/__init__.py
```

Each file can just contain:
```python
# Placeholder - will be populated in later sessions
```

## Step 1.9: Validation

Run these checks:

```bash
cd C:\XIIITradingSystems\Epoch\05_analysis_tool

# Install dependencies (using system Python)
pip install -r requirements.txt

# Test imports
python -c "from config import settings, weights; print('Config OK')"
python -c "from core.data_models import TickerInput, BarData, RawZone; print('Models OK')"
```

## Session 1 Checklist

- [ ] All directories created
- [ ] requirements.txt created and installs successfully
- [ ] config/settings.py created with all settings
- [ ] config/weights.py created with all weights from epoch_config.py
- [ ] core/data_models.py created with all Pydantic models
- [ ] All __init__.py files created
- [ ] Import tests pass

---

# SESSION 2: Polygon Client & Data Fetching

## Objective
Create the data layer that fetches market data from Polygon API.

## Step 2.1: Create data/polygon_client.py

Create file: `C:\XIIITradingSystems\Epoch\05_analysis_tool\data\polygon_client.py`

```python
"""
Polygon API client wrapper.
Provides unified interface for all market data fetching.
"""
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
import time

import pandas as pd
from polygon import RESTClient
from polygon.rest.models import Agg

from config.settings import POLYGON_API_KEY

logger = logging.getLogger(__name__)


class PolygonClient:
    """Wrapper for Polygon.io API calls."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or POLYGON_API_KEY
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not set. Add to .env file.")
        self.client = RESTClient(self.api_key)
        self._last_call_time = 0
        self._rate_limit_delay = 0.25  # 4 calls per second for free tier

    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        elapsed = time.time() - self._last_call_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_call_time = time.time()

    def fetch_daily_bars(
        self,
        ticker: str,
        start_date: date,
        end_date: date = None
    ) -> pd.DataFrame:
        """
        Fetch daily OHLCV bars.

        Args:
            ticker: Stock symbol
            start_date: Start date
            end_date: End date (defaults to today)

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        end_date = end_date or date.today()
        self._rate_limit()

        try:
            aggs = list(self.client.list_aggs(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                from_=start_date.isoformat(),
                to=end_date.isoformat(),
                limit=50000
            ))

            if not aggs:
                logger.warning(f"No daily data for {ticker}")
                return pd.DataFrame()

            data = [{
                'timestamp': datetime.fromtimestamp(a.timestamp / 1000),
                'open': a.open,
                'high': a.high,
                'low': a.low,
                'close': a.close,
                'volume': a.volume
            } for a in aggs]

            df = pd.DataFrame(data)
            df['date'] = df['timestamp'].dt.date
            return df.sort_values('timestamp').reset_index(drop=True)

        except Exception as e:
            logger.error(f"Error fetching daily bars for {ticker}: {e}")
            return pd.DataFrame()

    def fetch_minute_bars(
        self,
        ticker: str,
        start_date: date,
        end_date: date = None,
        multiplier: int = 1
    ) -> pd.DataFrame:
        """
        Fetch minute-level bars.

        Args:
            ticker: Stock symbol
            start_date: Start date
            end_date: End date
            multiplier: Bar size in minutes (1, 5, 15, etc.)

        Returns:
            DataFrame with OHLCV data
        """
        end_date = end_date or date.today()
        self._rate_limit()

        try:
            aggs = list(self.client.list_aggs(
                ticker=ticker,
                multiplier=multiplier,
                timespan="minute",
                from_=start_date.isoformat(),
                to=end_date.isoformat(),
                limit=50000
            ))

            if not aggs:
                logger.warning(f"No minute data for {ticker}")
                return pd.DataFrame()

            data = [{
                'timestamp': datetime.fromtimestamp(a.timestamp / 1000),
                'open': a.open,
                'high': a.high,
                'low': a.low,
                'close': a.close,
                'volume': a.volume
            } for a in aggs]

            return pd.DataFrame(data).sort_values('timestamp').reset_index(drop=True)

        except Exception as e:
            logger.error(f"Error fetching minute bars for {ticker}: {e}")
            return pd.DataFrame()

    def fetch_minute_bars_chunked(
        self,
        ticker: str,
        start_date: date,
        end_date: date = None,
        chunk_days: int = 5
    ) -> pd.DataFrame:
        """
        Fetch minute bars in chunks to handle large date ranges.
        Polygon has limits on data returned per request.
        """
        end_date = end_date or date.today()
        all_data = []

        current_start = start_date
        while current_start < end_date:
            current_end = min(current_start + timedelta(days=chunk_days), end_date)

            chunk = self.fetch_minute_bars(ticker, current_start, current_end)
            if not chunk.empty:
                all_data.append(chunk)

            current_start = current_end + timedelta(days=1)

        if not all_data:
            return pd.DataFrame()

        return pd.concat(all_data, ignore_index=True).drop_duplicates(
            subset=['timestamp']
        ).sort_values('timestamp').reset_index(drop=True)

    def fetch_options_chain(
        self,
        ticker: str,
        expiration_date: date = None
    ) -> pd.DataFrame:
        """
        Fetch options chain for a ticker.

        Args:
            ticker: Stock symbol
            expiration_date: Options expiration date (nearest if not specified)

        Returns:
            DataFrame with strike, type (call/put), open_interest
        """
        self._rate_limit()

        try:
            # Get options contracts
            contracts = list(self.client.list_options_contracts(
                underlying_ticker=ticker,
                expiration_date_gte=date.today().isoformat(),
                limit=1000
            ))

            if not contracts:
                logger.warning(f"No options contracts for {ticker}")
                return pd.DataFrame()

            data = []
            for c in contracts:
                data.append({
                    'ticker': c.ticker,
                    'strike': c.strike_price,
                    'expiration': c.expiration_date,
                    'type': c.contract_type
                })

            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"Error fetching options for {ticker}: {e}")
            return pd.DataFrame()

    def fetch_short_interest(self, ticker: str) -> Optional[Dict]:
        """Fetch short interest data for a ticker."""
        self._rate_limit()

        try:
            # Note: Short interest requires Polygon subscription
            # This is a placeholder - implement based on your data source
            return None
        except Exception as e:
            logger.error(f"Error fetching short interest for {ticker}: {e}")
            return None

    def get_previous_close(self, ticker: str) -> Optional[float]:
        """Get previous day's close price."""
        self._rate_limit()

        try:
            prev = self.client.get_previous_close_agg(ticker)
            if prev and prev.results:
                return prev.results[0].close
            return None
        except Exception as e:
            logger.error(f"Error fetching prev close for {ticker}: {e}")
            return None
```

## Step 2.2: Create data/cache_manager.py

Create file: `C:\XIIITradingSystems\Epoch\05_analysis_tool\data\cache_manager.py`

```python
"""
File-based caching for API responses.
Reduces API calls and improves performance.
"""
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional
import pickle

import pandas as pd

from config.settings import DATA_DIR, CACHE_TTL_DAILY, CACHE_TTL_INTRADAY

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages file-based caching of API responses."""

    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or DATA_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, *args) -> str:
        """Generate cache key from arguments."""
        key_str = "_".join(str(a) for a in args)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]

    def _get_cache_path(self, key: str, extension: str = "pkl") -> Path:
        """Get path for cache file."""
        return self.cache_dir / f"{key}.{extension}"

    def _is_valid(self, cache_path: Path, ttl_seconds: int) -> bool:
        """Check if cache file is still valid."""
        if not cache_path.exists():
            return False

        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        return age.total_seconds() < ttl_seconds

    def get_dataframe(
        self,
        key: str,
        ttl_seconds: int = CACHE_TTL_DAILY
    ) -> Optional[pd.DataFrame]:
        """Retrieve cached DataFrame."""
        cache_path = self._get_cache_path(key, "parquet")

        if self._is_valid(cache_path, ttl_seconds):
            try:
                return pd.read_parquet(cache_path)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
                return None
        return None

    def set_dataframe(self, key: str, df: pd.DataFrame):
        """Cache a DataFrame."""
        cache_path = self._get_cache_path(key, "parquet")
        try:
            df.to_parquet(cache_path)
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    def get_object(
        self,
        key: str,
        ttl_seconds: int = CACHE_TTL_DAILY
    ) -> Optional[Any]:
        """Retrieve cached Python object."""
        cache_path = self._get_cache_path(key, "pkl")

        if self._is_valid(cache_path, ttl_seconds):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
                return None
        return None

    def set_object(self, key: str, obj: Any):
        """Cache a Python object."""
        cache_path = self._get_cache_path(key, "pkl")
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(obj, f)
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    def clear(self, pattern: str = "*"):
        """Clear cache files matching pattern."""
        for path in self.cache_dir.glob(pattern):
            try:
                path.unlink()
            except Exception as e:
                logger.warning(f"Could not delete {path}: {e}")

    def clear_expired(self, ttl_seconds: int = CACHE_TTL_DAILY):
        """Remove all expired cache files."""
        for path in self.cache_dir.iterdir():
            if not self._is_valid(path, ttl_seconds):
                try:
                    path.unlink()
                except Exception:
                    pass


# Global cache instance
cache = CacheManager()
```

## Step 2.3: Create data/ticker_manager.py

Create file: `C:\XIIITradingSystems\Epoch\05_analysis_tool\data\ticker_manager.py`

```python
"""
Ticker list management.
Loads and manages stock ticker lists (S&P 500, NASDAQ 100, etc.)
"""
import json
import logging
from pathlib import Path
from typing import List, Set
from datetime import datetime, timedelta

import requests

from config.settings import DATA_DIR, MARKET_SCANNER_DIR

logger = logging.getLogger(__name__)


class TickerManager:
    """Manages ticker lists for scanning and analysis."""

    # Default ticker list file location (from market scanner)
    TICKER_FILE = MARKET_SCANNER_DIR / "data" / "ticker_lists" / "tickers.json"
    LOCAL_CACHE = DATA_DIR / "tickers.json"

    # Staleness threshold
    STALE_DAYS = 90

    def __init__(self):
        self._tickers: dict = {}
        self._load_tickers()

    def _load_tickers(self):
        """Load tickers from file."""
        # Try main ticker file first
        if self.TICKER_FILE.exists():
            try:
                with open(self.TICKER_FILE, 'r') as f:
                    self._tickers = json.load(f)
                logger.info(f"Loaded tickers from {self.TICKER_FILE}")
                return
            except Exception as e:
                logger.warning(f"Could not load {self.TICKER_FILE}: {e}")

        # Fall back to local cache
        if self.LOCAL_CACHE.exists():
            try:
                with open(self.LOCAL_CACHE, 'r') as f:
                    self._tickers = json.load(f)
                logger.info(f"Loaded tickers from cache")
                return
            except Exception as e:
                logger.warning(f"Could not load cache: {e}")

        # Initialize with defaults
        self._tickers = {
            "sp500": [],
            "nasdaq100": [],
            "russell2000": [],
            "last_updated": None
        }

    def get_list(self, list_name: str) -> List[str]:
        """
        Get ticker list by name.

        Args:
            list_name: One of 'sp500', 'nasdaq100', 'russell2000'

        Returns:
            List of ticker symbols
        """
        return self._tickers.get(list_name, [])

    def get_sp500(self) -> List[str]:
        """Get S&P 500 tickers."""
        return self.get_list("sp500")

    def get_nasdaq100(self) -> List[str]:
        """Get NASDAQ 100 tickers."""
        return self.get_list("nasdaq100")

    def get_russell2000(self) -> List[str]:
        """Get Russell 2000 tickers."""
        return self.get_list("russell2000")

    def is_stale(self) -> bool:
        """Check if ticker data is stale."""
        last_updated = self._tickers.get("last_updated")
        if not last_updated:
            return True

        try:
            update_date = datetime.fromisoformat(last_updated)
            return (datetime.now() - update_date).days > self.STALE_DAYS
        except Exception:
            return True

    def validate_tickers(self, tickers: List[str]) -> List[str]:
        """
        Validate and normalize ticker symbols.

        Args:
            tickers: List of ticker symbols

        Returns:
            List of valid, normalized tickers
        """
        valid = []
        for t in tickers:
            t = t.strip().upper()
            # Basic validation: 1-5 chars, alphanumeric
            if 1 <= len(t) <= 5 and t.isalnum():
                valid.append(t)
            else:
                logger.warning(f"Invalid ticker: {t}")
        return valid

    def parse_ticker_input(self, input_str: str) -> List[str]:
        """
        Parse ticker input string.

        Accepts:
        - Comma-separated: "AAPL, MSFT, GOOGL"
        - Space-separated: "AAPL MSFT GOOGL"
        - Newline-separated

        Returns:
            List of normalized ticker symbols
        """
        # Replace common separators with comma
        normalized = input_str.replace('\n', ',').replace(';', ',').replace(' ', ',')
        tickers = [t.strip() for t in normalized.split(',') if t.strip()]
        return self.validate_tickers(tickers)


# Global instance
ticker_manager = TickerManager()
```

## Step 2.4: Update data/__init__.py

```python
from .polygon_client import PolygonClient
from .cache_manager import CacheManager, cache
from .ticker_manager import TickerManager, ticker_manager
```

## Step 2.5: Validation

Create a test script: `C:\XIIITradingSystems\Epoch\05_analysis_tool\test_data_layer.py`

```python
"""Test the data layer components."""
from datetime import date, timedelta
from data.polygon_client import PolygonClient
from data.cache_manager import cache
from data.ticker_manager import ticker_manager

def test_polygon():
    print("Testing Polygon client...")
    client = PolygonClient()

    # Test daily bars
    start = date.today() - timedelta(days=30)
    df = client.fetch_daily_bars("SPY", start)
    print(f"  Daily bars: {len(df)} rows")
    assert len(df) > 0, "No daily data returned"

    # Test minute bars
    start = date.today() - timedelta(days=5)
    df = client.fetch_minute_bars("SPY", start)
    print(f"  Minute bars: {len(df)} rows")
    assert len(df) > 0, "No minute data returned"

    print("  Polygon client OK!")

def test_cache():
    print("Testing cache manager...")
    import pandas as pd

    # Test DataFrame caching
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    cache.set_dataframe("test_df", df)
    loaded = cache.get_dataframe("test_df")
    assert loaded is not None, "Cache retrieval failed"
    assert len(loaded) == 3, "Wrong data returned"

    # Test object caching
    obj = {"key": "value", "num": 42}
    cache.set_object("test_obj", obj)
    loaded = cache.get_object("test_obj")
    assert loaded == obj, "Object cache failed"

    print("  Cache manager OK!")

def test_ticker_manager():
    print("Testing ticker manager...")

    # Test parsing
    tickers = ticker_manager.parse_ticker_input("AAPL, MSFT, GOOGL")
    assert tickers == ["AAPL", "MSFT", "GOOGL"], "Parsing failed"

    # Test validation
    valid = ticker_manager.validate_tickers(["AAPL", "invalid!!!", "MSFT"])
    assert valid == ["AAPL", "MSFT"], "Validation failed"

    print("  Ticker manager OK!")

if __name__ == "__main__":
    test_cache()
    test_ticker_manager()
    test_polygon()  # Run last - requires API key
    print("\nAll tests passed!")
```

Run: `python test_data_layer.py`

## Session 2 Checklist

- [ ] data/polygon_client.py created with all fetch methods
- [ ] data/cache_manager.py created with caching logic
- [ ] data/ticker_manager.py created with list management
- [ ] data/__init__.py updated
- [ ] Test script passes all checks
- [ ] Polygon API returns valid data

---

# SESSION 3-15: Remaining Sessions

The remaining sessions follow the same detailed pattern. Continue with:

- **Session 3:** Port bar data calculators
- **Session 4:** Port HVN identifier with parameterized anchor date
- **Session 5:** Port zone calculator
- **Session 6:** Port zone filter and setup analyzer
- **Session 7:** Create Streamlit app shell
- **Session 8:** Create market_overview page
- **Session 9:** Create bar_data and raw_zones pages
- **Session 10:** Create zone_results and analysis pages
- **Session 11:** Create scanner page
- **Session 12:** Add batch analysis feature
- **Session 13:** Add export functionality
- **Session 14:** Integration testing
- **Session 15:** UI polish and documentation

Each session should be executed in order, with validation checkpoints before proceeding.

---

## Quick Reference: Existing Code Locations

When porting code, reference these source files:

| Component | Source Location |
|-----------|-----------------|
| M1 Metrics | `02_zone_system/03_bar_data/calculations/m1_metrics.py` |
| W1 Metrics | `02_zone_system/03_bar_data/calculations/w1_metrics.py` |
| D1 Metrics | `02_zone_system/03_bar_data/calculations/d1_metrics.py` |
| ON Metrics | `02_zone_system/03_bar_data/calculations/on_calculator.py` |
| ATR Calculator | `02_zone_system/03_bar_data/calculations/atr_calculator.py` |
| Camarilla | `02_zone_system/03_bar_data/calculations/camarilla_calculator.py` |
| Options | `02_zone_system/03_bar_data/calculations/options_calculator.py` |
| HVN Identifier | `02_zone_system/04_hvn_identifier/calculations/epoch_hvn_identifier.py` |
| Zone Engine | `02_zone_system/05_raw_zones/epoch_calc_engine.py` |
| Zone Filter | `02_zone_system/06_zone_results/zone_filter.py` |
| Setup Analyzer | `02_zone_system/07_setup_analysis/epoch_setup_analyzer.py` |
| Market Structure | `02_zone_system/01_market_structure/` |
| Scanner | `01_market_scanner/scanners/two_phase_scanner.py` |

---

**End of Session Guide**

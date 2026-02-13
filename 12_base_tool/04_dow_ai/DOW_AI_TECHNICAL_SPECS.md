# DOW AI Trading Assistant - Technical Specifications
## Epoch Trading System v1 - XIII Trading LLC

**Version:** 1.0
**Last Updated:** 2025-12-19
**Purpose:** Comprehensive technical reference for Claude AI to continue development

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [File Structure](#3-file-structure)
4. [Data Flow](#4-data-flow)
5. [10-Step Analysis Methodology](#5-10-step-analysis-methodology)
6. [Known Issues & Required Fixes](#6-known-issues--required-fixes)
7. [Planned Features](#7-planned-features)
8. [API Reference](#8-api-reference)
9. [Configuration](#9-configuration)
10. [Command Reference](#10-command-reference)

---

## 1. System Overview

### Purpose
DOW AI is a terminal-based AI trading assistant that:
- Fetches multi-timeframe market data from Polygon.io API
- Reads zone definitions and levels from Excel (epoch_v1.xlsm)
- Performs technical analysis using the 10-Step Methodology
- Uses Claude AI to generate trading recommendations
- Outputs formatted analysis to terminal

### Core Workflow
```
User Command → CLI Parser → Data Aggregation → 10-Step Analysis → Claude AI → Terminal Output
```

### Technology Stack
- **Python 3.10+**
- **Click** - CLI framework
- **Pandas/NumPy** - Data processing
- **xlwings** - Excel integration (requires Excel to be open)
- **Anthropic SDK** - Claude AI integration
- **Rich** - Terminal formatting
- **Polygon.io** - Market data API

---

## 2. Architecture

### Component Diagram
```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLI LAYER                                  │
│  main.py → cli.py (Click commands: entry, exit, models, welcome)    │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       ANALYSIS LAYER                                 │
│  aggregator.py - Main orchestrator for 10-Step Methodology          │
│  ├── Coordinates data fetching                                       │
│  ├── Runs all calculations                                           │
│  ├── Builds prompts for Claude                                       │
│  └── Returns complete analysis results                               │
└─────────────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────────┐
│   DATA LAYER     │ │ CALCULATIONS     │ │    CLAUDE LAYER          │
│                  │ │                  │ │                          │
│ polygon_fetcher  │ │ market_structure │ │ claude_client.py         │
│ - M1,M5,M15,H1,H4│ │ - BOS/ChoCH      │ │ - Anthropic API wrapper  │
│                  │ │ - Strong/Weak    │ │                          │
│ epoch_reader     │ │                  │ │ prompts/                 │
│ - Zones (Excel)  │ │ volume_analysis  │ │ - entry_prompt.py        │
│ - HVN POCs       │ │ - Delta, ROC     │ │ - exit_prompt.py         │
│ - Camarilla      │ │ - CVD trend      │ │                          │
│ - ATR            │ │                  │ │                          │
│                  │ │ moving_averages  │ │                          │
│                  │ │ - SMA9/SMA21     │ │                          │
│                  │ │ - Spread trend   │ │                          │
│                  │ │                  │ │                          │
│                  │ │ vwap.py          │ │                          │
│                  │ │ - Session VWAP   │ │                          │
│                  │ │                  │ │                          │
│                  │ │ patterns.py      │ │                          │
│                  │ │ - Candlestick    │ │                          │
└──────────────────┘ └──────────────────┘ └──────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        OUTPUT LAYER                                  │
│  terminal.py - Rich library formatting (tables, panels, colors)     │
│  debug/ - Timestamped debug files with full prompt + response       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. File Structure

```
C:\XIIITradingSystems\Epoch\04_dow_ai\
├── main.py                    # Entry point
├── cli.py                     # Click CLI with entry/exit commands
├── config.py                  # Central configuration
├── launcher.bat               # Windows batch launcher
├── requirements.txt           # Python dependencies
│
├── data/
│   ├── polygon_fetcher.py     # Polygon.io API client
│   ├── epoch_reader.py        # Excel workbook reader (xlwings)
│   └── data_models.py         # Pydantic data models
│
├── calculations/
│   ├── market_structure.py    # BOS/ChoCH fractal detection
│   ├── volume_analysis.py     # Volume delta, ROC, CVD
│   ├── moving_averages.py     # SMA9/SMA21 calculations
│   ├── vwap.py                # Session VWAP
│   └── patterns.py            # Candlestick pattern detection
│
├── analysis/
│   ├── aggregator.py          # MAIN ORCHESTRATOR
│   ├── claude_client.py       # Anthropic API wrapper
│   └── prompts/
│       ├── entry_prompt.py    # Entry analysis template
│       └── exit_prompt.py     # Exit analysis template
│
├── output/
│   └── terminal.py            # Rich terminal formatting
│
├── debug/                     # Debug output files
│   └── debug_{timestamp}_{mode}_{ticker}.txt
│
└── tests/
    └── test_zone_reading.py   # Zone reading tests
```

---

## 4. Data Flow

### Entry Analysis Flow

```python
# 1. CLI receives command
entry MSFT long primary -d 2025-12-19-10:00

# 2. cli.py parses arguments
ticker = "MSFT"
direction = "long"
zone_type = "primary"
dt_str = "2025-12-19-10:00"  # parsed to datetime

# 3. aggregator.run_entry_analysis() orchestrates:

# Step 1: Get zone from Excel
zone = epoch.get_primary_zone(ticker)
# Returns: {zone_id, direction, hvn_poc, zone_high, zone_low, target, r_r, ...}

# Step 2: Fetch Polygon data
bar_data = polygon.fetch_multi_timeframe(ticker, ['M1','M5','M15','H1','H4'])
# Returns: Dict[str, DataFrame] with OHLCV data

# Step 3: Calculate model
model_code, model_name, trade_type = classify_model(zone_type, zone.direction, direction)
# Returns: ('EPCH_01', 'Primary Continuation', 'continuation')

# Step 4: Price-to-zone relationship
price_zone_rel = get_price_zone_relationship(current_price, zone)
# Returns: {position: 'ABOVE'/'BELOW'/'INSIDE', distance, description}

# Step 5: Market structure (Steps 1-4 of 10-step)
structure = structure_calc.calculate_multi_timeframe(bar_data)
# Returns: Dict[tf, MarketStructureResult]

# Step 6: Volume analysis (Steps 5-7 of 10-step)
volume = volume_analyzer.analyze(bar_data['M1'])
m5_volume = volume_analyzer.analyze(bar_data['M5'])
m15_volume = volume_analyzer.analyze(bar_data['M15'])
# Returns: VolumeResult with delta, ROC, CVD

# Step 7: Pattern detection
patterns = pattern_detector.detect_multi_timeframe(bar_data)
# Returns: Dict[tf, List[PatternResult]]

# Step 8: Supporting levels from Excel
atr = epoch.read_atr(ticker)
hvn_pocs = epoch.read_hvn_pocs(ticker)
camarilla = epoch.read_camarilla_levels(ticker)

# **MISSING: SMA and VWAP calculations** (see Issue #1)

# Step 9: Build prompt
prompt = build_entry_prompt(ticker, direction, zone_type, ...)

# Step 10: Send to Claude
claude_response = claude.analyze(prompt)

# 4. Return result dict with all data + Claude response
# 5. terminal.py formats and displays output
```

---

## 5. 10-Step Analysis Methodology

### The Steps

| Step | Name | Data Source | Current Status |
|------|------|-------------|----------------|
| 1 | HTF Structure (H4 → H1) | market_structure.py | ✅ Working |
| 2 | HTF % Within Strong/Weak | market_structure.py | ✅ Working |
| 3 | MTF Structure (M15 → M5) | market_structure.py | ✅ Working |
| 4 | MTF % Within Strong/Weak | market_structure.py | ✅ Working |
| 5 | Volume ROC | volume_analysis.py | ✅ Working |
| 6 | Volume Delta (M15/M5) | volume_analysis.py | ✅ Working |
| 7 | CVD Direction + Trend | volume_analysis.py | ✅ Working |
| 8 | SMA9/SMA21 Alignment | moving_averages.py | ❌ **NOT PASSED TO PROMPT** |
| 9 | SMA Spread (momentum) | moving_averages.py | ❌ **NOT PASSED TO PROMPT** |
| 10 | VWAP Location | vwap.py | ❌ **NOT PASSED TO PROMPT** |

### Model Classification Logic

```python
def classify_model(zone_type, zone_direction, trade_direction):
    """
    zone_type: 'primary' or 'secondary'
    zone_direction: 'Bull', 'Bear', 'Bull+', 'Bear+' (from Excel)
    trade_direction: 'long' or 'short'

    Logic:
    - Trading WITH zone direction = CONTINUATION
      (bullish zone + long) OR (bearish zone + short)

    - Trading AGAINST zone direction = REVERSAL
      (bullish zone + short) OR (bearish zone + long)

    Results:
    - EPCH_01: Primary Continuation
    - EPCH_02: Primary Reversal
    - EPCH_03: Secondary Continuation
    - EPCH_04: Secondary Reversal
    """
```

---

## 6. Known Issues & Required Fixes

### Issue #1: SMA and VWAP Not Passed to Entry Prompt (CRITICAL)

**Problem:** The `run_entry_analysis()` method in `aggregator.py` does NOT calculate or pass SMA/VWAP data to the entry prompt. Claude sees Steps 8-10 as "DATA MISSING".

**Current Code (aggregator.py lines 282-464):**
```python
def run_entry_analysis(self, ticker, direction, zone_type, analysis_datetime=None):
    # ... fetches data, calculates structure, volume, patterns ...

    # MISSING: These calculations exist but are NOT called:
    # smas = self.sma_analyzer.calculate_multi_timeframe(bar_data)  # NOT HERE
    # vwap_result = self.vwap_calc.analyze(bar_data['M1'])          # NOT HERE

    # The entry prompt is built WITHOUT SMA/VWAP data
    prompt = build_entry_prompt(
        # ... no sma or vwap parameters ...
    )
```

**Compare with exit analysis (lines 527-531):**
```python
# Exit DOES calculate SMA and VWAP:
smas = self.sma_analyzer.calculate_multi_timeframe({
    'M5': bar_data.get('M5'),
    'M15': bar_data.get('M15')
})
vwap_result = self.vwap_calc.analyze(bar_data['M1'], current_price)
```

---

## EXACT FIX INSTRUCTIONS

### Step 1: Modify `aggregator.py` - Add SMA/VWAP Calculations

**Location:** `analysis/aggregator.py` in `run_entry_analysis()` method

Add AFTER the volume analysis section (around line 370) and BEFORE building the prompt:

```python
# ===== ADD THIS BLOCK =====
# Calculate SMA indicators (for Steps 8-9)
if self.verbose:
    debug_print("Calculating SMA indicators...")
smas = self.sma_analyzer.calculate_multi_timeframe({
    'M5': bar_data.get('M5'),
    'M15': bar_data.get('M15')
})

# Calculate VWAP (for Step 10)
if self.verbose:
    debug_print("Calculating VWAP...")
vwap_result = self.vwap_calc.analyze(bar_data.get('M1'), current_price)
# ===== END BLOCK =====
```

Then update the `build_entry_prompt()` call to include the new parameters:

```python
prompt = build_entry_prompt(
    ticker=ticker,
    direction=direction,
    zone_type=zone_type,
    zone=zone,
    price_zone_rel=price_zone_rel,
    model_code=model_code,
    model_name=model_name,
    trade_type=trade_type,
    current_price=current_price,
    analysis_time=analysis_time,
    structure=structure,
    volume=volume,
    m5_volume=m5_volume,
    m15_volume=m15_volume,
    patterns=patterns,
    atr=atr,
    hvn_pocs=hvn_pocs,
    camarilla=camarilla,
    all_zones=all_zones,
    smas=smas,              # ADD THIS
    vwap_result=vwap_result  # ADD THIS
)
```

Also add to the result dict:

```python
result = {
    # ... existing fields ...
    'smas': smas,
    'vwap': vwap_result,
}
```

---

### Step 2: Modify `entry_prompt.py` - Add SMA/VWAP Sections

**Location:** `analysis/prompts/entry_prompt.py`

**2a. Add SMA/VWAP section to template (after SUPPORTING LEVELS):**

```python
SMA ANALYSIS:
{sma_section}

VWAP ANALYSIS:
{vwap_section}
```

**2b. Update function signature:**

```python
def build_entry_prompt(
    ticker: str,
    direction: str,
    zone_type: str,
    zone: dict,
    price_zone_rel: dict,
    model_code: str,
    model_name: str,
    trade_type: str,
    current_price: float,
    analysis_time: str,
    structure: dict,
    volume,
    m5_volume,
    m15_volume,
    patterns: dict,
    atr: float,
    hvn_pocs: list,
    camarilla: dict,
    all_zones: dict,
    smas: dict = None,        # ADD THIS
    vwap_result = None        # ADD THIS
) -> str:
```

**2c. Add formatting code in function body:**

```python
# Format SMA section
sma_lines = []
if smas:
    for tf in ['M5', 'M15']:
        if tf in smas:
            s = smas[tf]
            sma_lines.append(
                f"{tf}: SMA9 ${s.sma9:.2f} | SMA21 ${s.sma21:.2f} | {s.alignment} | Spread: {s.spread_trend}"
            )
sma_section = "\n".join(sma_lines) if sma_lines else "DATA NOT AVAILABLE"

# Format VWAP section
if vwap_result and vwap_result.vwap > 0:
    vwap_section = (
        f"Session VWAP: ${vwap_result.vwap:.2f}\n"
        f"Price vs VWAP: {vwap_result.side} by ${abs(vwap_result.price_diff):.2f} ({vwap_result.price_pct:+.2f}%)"
    )
else:
    vwap_section = "DATA NOT AVAILABLE"
```

**2d. Add to template format call:**

```python
return ENTRY_PROMPT_TEMPLATE.format(
    # ... existing parameters ...
    sma_section=sma_section,
    vwap_section=vwap_section
)
```

---

### Step 3: Verify Imports in aggregator.py

Ensure these imports exist at the top of `aggregator.py`:

```python
from calculations.moving_averages import MovingAverageAnalyzer
from calculations.vwap import VWAPCalculator
```

And that the class initializes them:

```python
class AnalysisAggregator:
    def __init__(self, verbose: bool = None):
        # ... existing code ...
        self.sma_analyzer = MovingAverageAnalyzer(verbose=self.verbose)
        self.vwap_calc = VWAPCalculator(verbose=self.verbose)
```

---

### Data Classes Reference

**SMAResult (from moving_averages.py):**
```python
@dataclass
class SMAResult:
    sma9: float           # 9-period SMA value
    sma21: float          # 21-period SMA value
    spread: float         # sma9 - sma21
    spread_trend: str     # 'WIDENING', 'NARROWING', 'FLAT'
    alignment: str        # 'BULLISH', 'BEARISH', 'NEUTRAL'
    cross_price_estimate: Optional[float] = None
```

**VWAPResult (from vwap.py):**
```python
@dataclass
class VWAPResult:
    vwap: float           # Session VWAP value
    price_diff: float     # current_price - vwap
    price_pct: float      # percentage difference
    side: str             # 'ABOVE', 'BELOW', 'AT'
```

---

**Files to modify:**
- `analysis/aggregator.py` - Add calculations to run_entry_analysis()
- `analysis/prompts/entry_prompt.py` - Add SMA/VWAP to template and build function
- `output/terminal.py` - Display SMA/VWAP in output (optional, for debugging)

---

### Issue #2: Entry Prompt Template Missing SMA/VWAP Sections

**Problem:** The entry prompt template asks Claude to analyze Steps 8-10 but doesn't provide the data.

**Current Template (entry_prompt.py):**
```python
ENTRY_PROMPT_TEMPLATE = """
...
STEP 8: SMA9/SMA21 Alignment - In line with {direction}?
STEP 9: SMA Spread - Diverging (momentum) or converging (exhaustion)?
STEP 10: VWAP Location - Price above or below VWAP?
...
"""
# No SMA_SECTION or VWAP_SECTION in the template
```

**Required Fix:**
Add to template:
```python
SMA ANALYSIS:
- M5:  SMA9: ${m5_sma9:.2f} | SMA21: ${m5_sma21:.2f} | {m5_alignment} | Spread: {m5_spread_trend}
- M15: SMA9: ${m15_sma9:.2f} | SMA21: ${m15_sma21:.2f} | {m15_alignment} | Spread: {m15_spread_trend}

VWAP:
- Session VWAP: ${vwap:.2f}
- Price vs VWAP: {vwap_side} by ${vwap_diff:.2f} ({vwap_pct:.2f}%)
```

---

## 7. Planned Features

### Feature #1: Post-Analysis Follow-Up Questions

**Description:** After Claude provides analysis, prompt user for two follow-up decisions:

1. **Trade Taken?** - Did the user take the trade based on the analysis?
   - If YES: Record entry price, time, position size
   - If NO: Record reason (e.g., "alignment score too low", "missed entry")

2. **Upload to Supabase?** - Should this analysis be saved to cloud database?
   - If YES: Upload full analysis data + user decision
   - If NO: Keep only local debug file

**Implementation Approach:**
```python
# In cli.py after print_entry_analysis(result):

# Follow-up question 1: Trade taken?
trade_taken = click.confirm("Did you take this trade?", default=False)

if trade_taken:
    entry_price = click.prompt("Entry price", type=float, default=result['current_price'])
    position_size = click.prompt("Position size (shares)", type=int, default=100)
    result['trade_taken'] = {
        'taken': True,
        'entry_price': entry_price,
        'position_size': position_size,
        'entry_time': datetime.now()
    }
else:
    reason = click.prompt("Reason for not taking trade", default="")
    result['trade_taken'] = {
        'taken': False,
        'reason': reason
    }

# Follow-up question 2: Upload to Supabase?
if click.confirm("Upload analysis to Supabase?", default=True):
    upload_to_supabase(result)
```

---

### Feature #2: Supabase Integration

**Description:** Store analysis results in Supabase for:
- Historical performance tracking
- Win/loss ratio by model type
- Pattern recognition of successful setups
- Backtesting journal

**Required Tables:**

```sql
-- Table: analyses
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Request data
    ticker VARCHAR(10) NOT NULL,
    direction VARCHAR(10) NOT NULL,  -- 'long' or 'short'
    zone_type VARCHAR(20) NOT NULL,  -- 'primary' or 'secondary'
    model_code VARCHAR(10) NOT NULL, -- 'EPCH_01', etc.
    model_name VARCHAR(50) NOT NULL,
    trade_type VARCHAR(20) NOT NULL, -- 'continuation' or 'reversal'

    -- Analysis timestamp
    analysis_time TIMESTAMP WITH TIME ZONE NOT NULL,
    is_historical BOOLEAN DEFAULT FALSE,

    -- Price data
    current_price DECIMAL(10,2) NOT NULL,
    zone_low DECIMAL(10,2),
    zone_high DECIMAL(10,2),
    hvn_poc DECIMAL(10,2),
    target_price DECIMAL(10,2),
    r_r DECIMAL(5,2),

    -- Zone relationship
    price_position VARCHAR(10),  -- 'ABOVE', 'BELOW', 'INSIDE'
    price_distance DECIMAL(10,2),

    -- Claude analysis
    claude_response TEXT,
    alignment_score INTEGER,  -- 0-10
    confidence VARCHAR(10),   -- 'HIGH', 'MEDIUM', 'LOW'

    -- Trade decision
    trade_taken BOOLEAN DEFAULT FALSE,
    entry_price DECIMAL(10,2),
    position_size INTEGER,
    not_taken_reason TEXT,

    -- Full data (JSON)
    full_result JSONB,
    prompt_sent TEXT
);

-- Table: trade_outcomes (for completed trades)
CREATE TABLE trade_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES analyses(id),

    exit_time TIMESTAMP WITH TIME ZONE,
    exit_price DECIMAL(10,2),
    exit_reason VARCHAR(50),  -- 'target', 'stop', 'manual', 'trail'

    pnl_dollars DECIMAL(10,2),
    pnl_percent DECIMAL(5,2),
    r_multiple DECIMAL(5,2),

    notes TEXT
);

-- Index for common queries
CREATE INDEX idx_analyses_ticker ON analyses(ticker);
CREATE INDEX idx_analyses_model ON analyses(model_code);
CREATE INDEX idx_analyses_date ON analyses(analysis_time);
CREATE INDEX idx_analyses_trade_taken ON analyses(trade_taken);
```

**Required New Files:**
```
04_dow_ai/
├── database/
│   ├── __init__.py
│   ├── supabase_client.py   # Supabase connection and CRUD
│   └── models.py            # SQLAlchemy/Pydantic models
```

**Supabase Client Implementation:**
```python
# database/supabase_client.py
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

class SupabaseClient:
    def __init__(self):
        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def upload_analysis(self, result: dict) -> str:
        """Upload analysis result, return record ID."""
        data = {
            'ticker': result['ticker'],
            'direction': result['direction'],
            'zone_type': result['zone_type'],
            'model_code': result['model_code'],
            # ... map all fields ...
            'full_result': result,
            'prompt_sent': result.get('prompt', '')
        }
        response = self.client.table('analyses').insert(data).execute()
        return response.data[0]['id']

    def record_trade_outcome(self, analysis_id: str, outcome: dict):
        """Record trade outcome for an analysis."""
        data = {
            'analysis_id': analysis_id,
            'exit_price': outcome['exit_price'],
            'exit_time': outcome['exit_time'],
            'pnl_dollars': outcome['pnl'],
            # ... etc
        }
        self.client.table('trade_outcomes').insert(data).execute()
```

---

## 8. API Reference

### Polygon Fetcher

```python
class PolygonFetcher:
    def fetch_bars(ticker: str, timeframe: str, end_datetime=None, bars_needed=None) -> pd.DataFrame
    def fetch_multi_timeframe(ticker: str, timeframes: list, end_datetime=None) -> Dict[str, pd.DataFrame]
    def get_current_price(ticker: str, at_datetime=None) -> float
```

### Epoch Reader (Excel)

```python
class EpochReader:
    def connect() -> bool
    def get_primary_zone(ticker: str) -> Optional[dict]
    def get_secondary_zone(ticker: str) -> Optional[dict]
    def get_both_zones(ticker: str) -> dict
    def read_hvn_pocs(ticker: str) -> List[float]
    def read_atr(ticker: str) -> Optional[float]
    def read_camarilla_levels(ticker: str) -> Optional[dict]
```

### Analysis Aggregator

```python
class AnalysisAggregator:
    def run_entry_analysis(ticker, direction, zone_type, analysis_datetime=None) -> dict
    def run_exit_analysis(ticker, exit_action, zone_type, analysis_datetime=None) -> dict
    def classify_model(zone_type, zone_direction, trade_direction) -> tuple
```

### Calculation Classes

```python
class MarketStructureCalculator:
    def calculate(df: pd.DataFrame) -> MarketStructureResult
    def calculate_multi_timeframe(data: Dict[str, pd.DataFrame]) -> Dict[str, MarketStructureResult]

class VolumeAnalyzer:
    def analyze(df: pd.DataFrame) -> VolumeResult

class MovingAverageAnalyzer:
    def calculate_smas(df: pd.DataFrame) -> SMAResult
    def calculate_multi_timeframe(data: Dict[str, pd.DataFrame]) -> Dict[str, SMAResult]

class VWAPCalculator:
    def calculate_vwap(df: pd.DataFrame) -> float
    def analyze(df: pd.DataFrame, current_price=None) -> VWAPResult

class PatternDetector:
    def detect_patterns(df: pd.DataFrame) -> List[PatternResult]
    def detect_multi_timeframe(data: Dict[str, pd.DataFrame]) -> Dict[str, List[PatternResult]]
```

---

## 9. Configuration

### config.py Key Settings

```python
# Paths
BASE_DIR = Path(r"C:\XIIITradingSystems\Epoch")
EXCEL_FILEPATH = BASE_DIR / "epoch_v1.xlsm"
DOW_DIR = BASE_DIR / "04_dow_ai"
DEBUG_DIR = DOW_DIR / "debug"

# API Keys
POLYGON_API_KEY = "..."
ANTHROPIC_API_KEY = "..."

# Claude Settings
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 1500

# Timeframes
TIMEFRAMES = {
    'M1': {'multiplier': 1, 'timespan': 'minute', 'bars_needed': 50},
    'M5': {'multiplier': 5, 'timespan': 'minute', 'bars_needed': 100},
    'M15': {'multiplier': 15, 'timespan': 'minute', 'bars_needed': 100},
    'H1': {'multiplier': 1, 'timespan': 'hour', 'bars_needed': 100},
    'H4': {'multiplier': 4, 'timespan': 'hour', 'bars_needed': 50},
}

# Excel Mappings (Analysis worksheet)
ANALYSIS_REFS = {
    'primary': {'start_row': 31, 'end_row': 40, 'columns': {
        'ticker': 'B', 'direction': 'C', 'ticker_id': 'D', 'zone_id': 'E',
        'hvn_poc': 'F', 'zone_high': 'G', 'zone_low': 'H', 'tier': 'I',
        'target_id': 'J', 'target': 'K', 'r_r': 'L'
    }},
    'secondary': {'start_row': 31, 'end_row': 40, 'columns': {
        'ticker': 'N', 'direction': 'O', ...
    }},
}

# Model Definitions
MODELS = {
    'EPCH_01': {'name': 'Primary Continuation', 'zone_type': 'primary', 'trade_type': 'continuation'},
    'EPCH_02': {'name': 'Primary Reversal', 'zone_type': 'primary', 'trade_type': 'reversal'},
    'EPCH_03': {'name': 'Secondary Continuation', 'zone_type': 'secondary', 'trade_type': 'continuation'},
    'EPCH_04': {'name': 'Secondary Reversal', 'zone_type': 'secondary', 'trade_type': 'reversal'},
}
```

---

## 10. Command Reference

### Entry Analysis
```bash
# Live analysis
entry TICKER DIRECTION ZONE
entry NVDA long primary
entry TSLA short secondary

# Historical analysis
entry TICKER DIRECTION ZONE -d YYYY-MM-DD-HH:MM
entry MSFT long primary -d 2025-12-19-10:00
```

### Exit Analysis
```bash
# Live analysis
exit TICKER ACTION ZONE
exit TSLA sell primary      # Close long position
exit NVDA cover secondary   # Close short position

# Historical analysis
exit TICKER ACTION ZONE -d YYYY-MM-DD-HH:MM
exit TSLA sell primary -d 2025-12-19-14:30
```

### Other Commands
```bash
models    # List available EPCH models
welcome   # Show welcome message and help
quit      # Exit launcher
```

---

## Summary of Priority Tasks

1. **[CRITICAL] Fix SMA/VWAP in Entry Analysis**
   - Add calculations to `aggregator.py:run_entry_analysis()`
   - Update `entry_prompt.py` with SMA/VWAP sections
   - Update `terminal.py` to display SMA/VWAP

2. **[HIGH] Add Follow-Up Questions**
   - Trade taken? (Y/N with details)
   - Upload to Supabase? (Y/N)

3. **[MEDIUM] Implement Supabase Integration**
   - Create database client
   - Create tables in Supabase
   - Add upload functionality

---

*Document generated for Claude AI development assistance*

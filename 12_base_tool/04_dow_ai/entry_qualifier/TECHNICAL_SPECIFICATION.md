# Entry Qualifier - Technical Specification

**Version:** 1.0
**Date:** 2026-01-17
**System:** Epoch Trading System v1 - XIII Trading LLC

---

## Overview

The Entry Qualifier is a PyQt6-based real-time trading indicator dashboard that displays rolling 1-minute bar data with calculated indicators for up to 6 tickers. It implements the EPCH Indicators v1.0 specification for zone-based trade evaluation.

---

## Architecture

### Directory Structure

```
entry_qualifier/
├── main.py                     # Application entry point
├── eq_config.py                # Configuration constants
├── requirements.txt            # Python dependencies
├── README.md                   # User documentation
├── TECHNICAL_SPECIFICATION.md  # This file
├── calculations/
│   ├── __init__.py             # Module exports
│   ├── candle_range.py         # Candle range % calculation
│   ├── volume_delta.py         # Volume delta calculation
│   ├── volume_roc.py           # Volume ROC calculation
│   ├── sma_config.py           # SMA configuration calculation
│   ├── h1_structure.py         # H1 market structure analysis
│   └── scores.py               # LONG/SHORT composite scoring
├── data/
│   ├── __init__.py
│   ├── api_client.py           # Polygon API client
│   ├── data_worker.py          # QThread data fetcher
│   └── market_hours.py         # Market hours utilities
└── ui/
    ├── __init__.py
    ├── main_window.py          # Main application window
    ├── ticker_panel.py         # Individual ticker display panel
    ├── ticker_dialog.py        # Add ticker dialog
    └── styles.py               # Dark theme stylesheet
```

---

## Configuration (`eq_config.py`)

| Constant | Value | Description |
|----------|-------|-------------|
| `ROLLING_BARS` | 25 | Number of bars displayed per ticker |
| `REFRESH_INTERVAL_MS` | 60000 | Refresh interval (1 minute) |
| `VOL_DELTA_ROLL_PERIOD` | 5 | Rolling period for volume delta |
| `VOL_ROC_LOOKBACK` | 20 | Lookback period for volume ROC |
| `H1_BARS_NEEDED` | 25 | H1 bars for structure analysis |
| `MAX_TICKERS` | 6 | Maximum simultaneous tickers |
| `PREFETCH_BARS` | 50 | Bars fetched to ensure valid calculations |

---

## Indicator Calculations

### 1. Candle Range (`calculations/candle_range.py`)

**Formula:** `(high - low) / close * 100`

**Output:** Percentage value (e.g., 0.15 for 0.15%)

**Thresholds:**
| Range | Classification | Action |
|-------|----------------|--------|
| < 0.12% | Absorption Zone | SKIP (dim column) |
| 0.12% - 0.15% | Low Range | Caution |
| >= 0.15% | Normal/High | Trade |

**Functions:**
- `calculate_candle_range_pct(high, low, close)` → float
- `is_absorption_zone(candle_range_pct)` → bool
- `calculate_all_candle_ranges(bars)` → List[dict]

---

### 2. Volume Delta (`calculations/volume_delta.py`)

**Formula (Bar Position Method):**
```
position = (2 * (close - low) / (high - low)) - 1
delta = position * volume
```

**Output:** Net volume (positive = buying, negative = selling)

**Functions:**
- `calculate_bar_delta(open, high, low, close, volume)` → float
- `calculate_rolling_delta(raw_deltas, period)` → float
- `calculate_all_deltas(bars, roll_period)` → List[dict]

---

### 3. Volume ROC (`calculations/volume_roc.py`)

**Formula:** `((current_volume - avg_volume) / avg_volume) * 100`

**Lookback:** 20 bars (configurable)

**Thresholds:**
| ROC | Classification |
|-----|----------------|
| >= 50% | High volume |
| >= 30% | Elevated volume (confirmation) |
| 0% - 30% | Normal volume |
| < 0% | Declining volume |

**Functions:**
- `calculate_volume_roc(current_volume, avg_volume)` → float
- `calculate_all_volume_roc(bars, lookback)` → List[dict]
- `is_elevated_volume(volume_roc)` → bool

---

### 4. SMA Configuration (`calculations/sma_config.py`)

**Components:**
- **SMA9:** 9-period simple moving average
- **SMA21:** 21-period simple moving average
- **Config:** BULLISH (SMA9 > SMA21) or BEARISH (SMA9 < SMA21)
- **Spread:** `abs(SMA9 - SMA21) / price * 100`

**Enums:**
```python
class SMAConfig(Enum):
    BULLISH = "BULL"
    BEARISH = "BEAR"
    NEUTRAL = "FLAT"

class PricePosition(Enum):
    ABOVE_BOTH = "ABOVE"
    BETWEEN = "BTWN"
    BELOW_BOTH = "BELOW"
```

**Display Format:** `"BULL 0.15%"` or `"BEAR 0.08%"`

**Functions:**
- `calculate_sma(prices, period)` → float
- `get_sma_config(sma9, sma21)` → SMAConfig
- `calculate_sma_spread_pct(sma9, sma21, price)` → float
- `calculate_all_sma_configs(bars)` → List[dict]

---

### 5. H1 Structure (`calculations/h1_structure.py`)

**Method:** Swing high/low analysis on H1 timeframe

**Logic:**
- Compare first half vs second half of lookback period
- Higher high + higher low = BULL
- Lower high + lower low = BEAR
- Mixed signals = NEUTRAL

**Enum:**
```python
class MarketStructure(Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    NEUTRAL = "NEUT"
```

**Caching:**
- `H1StructureCache` class stores H1 bars per ticker
- Refreshes when new H1 candle closes (hourly)
- Minimizes API calls

**Functions:**
- `calculate_structure(bars, lookback)` → MarketStructure
- `calculate_structure_for_bars(h1_bars, m1_bars)` → List[dict]

---

### 6. Composite Scores (`calculations/scores.py`)

#### LONG Score (0-7 points)

| Condition | Points |
|-----------|--------|
| Candle Range >= 0.15% | +2 |
| H1 Structure = NEUTRAL | +2 |
| Volume ROC >= 30% | +1 |
| High magnitude Vol Delta (>100k) | +1 |
| Wide SMA spread (>= 0.15%) | +1 |

#### SHORT Score (0-7 points) - Note Paradoxes

| Condition | Points |
|-----------|--------|
| Candle Range >= 0.15% | +2 |
| H1 Structure = NEUTRAL | +2 |
| Volume ROC >= 30% | +1 |
| Vol Delta POSITIVE (paradox) | +1 |
| SMA Config = BULLISH (paradox) | +1 |

**Score Interpretation:**
| Score | Signal Strength |
|-------|-----------------|
| 0-2 | Weak (red) |
| 3-4 | Moderate (yellow) |
| 5-7 | Strong (green) |

---

## Data Flow

### Startup Sequence

```
1. MainWindow initialized
2. Timer syncs to next minute boundary
3. User adds ticker via TickerDialog
4. DataWorker spawned for ticker
5. M1 bars fetched (50 bars)
6. H1 bars fetched (25 bars, cached)
7. All calculations performed
8. TickerPanel updated
```

### Refresh Cycle (Every Minute)

```
1. Timer fires at :00 seconds
2. For each active ticker:
   a. Fetch latest M1 bars
   b. Check H1 cache (refresh if new hour)
   c. Calculate all indicators
   d. Update panel display
3. Reset countdown timer
```

### H1 Cache Strategy

```
Initial Load:
  - Fetch 25 H1 bars on first ticker add

Hourly Refresh:
  - Check if current H1 timestamp > cached timestamp
  - If yes, fetch fresh H1 data
  - Cache is per-ticker

Cache Miss:
  - Return NEUTRAL structure for all bars
```

---

## UI Components

### TickerPanel Layout

**Table Dimensions:** 7 rows x 26 columns (25 data + 1 label)

| Row | Indicator | Display Format | Color Logic |
|-----|-----------|----------------|-------------|
| 0 | Candle % | `0.18%` | Green >=0.15%, Gray 0.12-0.15%, Red <0.12% |
| 1 | Vol Δ | `+2.5M`, `-800k` | Green positive, Red negative |
| 2 | Vol ROC | `+45%`, `-12%` | Green >=30%, Gray 0-30%, Red <0% |
| 3 | SMA | `BULL 0.15%` | Green BULL, Red BEAR, Gray FLAT |
| 4 | H1 Struct | `NEUT`, `BULL` | Cyan NEUT, Green BULL, Red BEAR |
| 5 | LONG | `5` | Green 5-7, Yellow 3-4, Red 0-2 |
| 6 | SHORT | `6` | Green 5-7, Yellow 3-4, Red 0-2 |

### Absorption Zone Dimming

When `candle_range < 0.12%`:
- Entire column background: `#1a1a1a`
- All text color: `#4a4a4a`
- Visual signal to skip this bar

### Column Headers

Labels from `-24` to `0` (oldest to newest), with `0` being the current bar.

---

## Color Scheme (`ui/styles.py`)

### Base Colors

| Color | Hex | Usage |
|-------|-----|-------|
| Background | `#000000` | Main background |
| Border | `#2a2a4a` | Panel borders |
| Text Primary | `#e8e8e8` | Main text |
| Text Secondary | `#a0a0a0` | Labels |
| Text Muted | `#707070` | Placeholder |

### Indicator Colors

| Color | Hex | Usage |
|-------|-----|-------|
| Positive | `#26a69a` | Green (bullish/good) |
| Negative | `#ef5350` | Red (bearish/bad) |
| Neutral | `#9E9E9E` | Gray (neutral) |
| Cyan Highlight | `#00BCD4` | H1 NEUTRAL (best) |

### Score Backgrounds

| Score | Hex | Color |
|-------|-----|-------|
| 5-7 | `#1B5E20` | Dark green |
| 3-4 | `#F57F17` | Amber |
| 0-2 | `#B71C1C` | Dark red |

### Dimmed (Absorption)

| Element | Hex |
|---------|-----|
| Background | `#1a1a1a` |
| Text | `#4a4a4a` |

---

## API Integration (`data/api_client.py`)

### Polygon.io Endpoints

**M1 Bars:**
```
GET /v2/aggs/ticker/{ticker}/range/1/minute/{from}/{to}
```

**H1 Bars:**
```
GET /v2/aggs/ticker/{ticker}/range/1/hour/{from}/{to}
```

### Rate Limiting

- Delay between requests: configurable via `API_RATE_LIMIT_DELAY`
- Max retries: `API_MAX_RETRIES`
- Retry delay: `API_RETRY_DELAY`

### Error Handling

| Error | User Message |
|-------|--------------|
| timeout | "API Timeout" |
| network | "Network Error" |
| api_error | "API Error" |
| no_data | "No Data Available" |
| rate_limit | "Rate Limited" |

---

## Threading Model

### Main Thread
- PyQt6 event loop
- UI rendering
- Timer management

### DataWorker (QThread)
- API requests
- Indicator calculations
- Emits signals on completion

### Signals

```python
data_ready = pyqtSignal(str, list)      # ticker, processed_bars
error_occurred = pyqtSignal(str, str)   # ticker, error_message
validation_result = pyqtSignal(str, bool)  # ticker, is_valid
```

---

## Dependencies

```
PyQt6>=6.4.0
requests>=2.28.0
pytz>=2022.1
```

---

## Future Enhancements

1. **Zone Integration:** Connect to zone database for context
2. **Alert System:** Notifications for high-score signals
3. **Historical Playback:** Review past sessions
4. **Multi-Timeframe:** Add M5, M15 structure views
5. **Export:** Save session data to CSV/database

---

## References

- `epch_indicators_01.md` - EPCH Indicators v1.0 specification
- `Indicator_Validation_Pipeline.md` - Edge analysis methodology
- Polygon.io API documentation

---

*Document generated: 2026-01-17*

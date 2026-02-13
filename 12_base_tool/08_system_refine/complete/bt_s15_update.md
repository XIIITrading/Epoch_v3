> *Purpose:* The purpose of this document is to outline an update to the existing back test engine to allow for a more refined analysis. The primary adjustment to the analysis will be driven by a reduced entry aggregate bar. The aggregate bar will move from M5 to S15 close. While this will increase the amount of trades that will be available, it will also ensure that more refined entry points are outlined, and breakout trades from zones will be captured.

*Dev Rules:*

1. Do not generate any code without my explicit instructions
2. Do not assume anything (naming convention, modules, directories). Ask for clarification or for files you would like to read directly.
3. Always include .txt documentation at the end in two files
   1. AI readable and understandable with enough description and specific script context to be used in other AI conversations without having to provide the dull script directory.
   2. Human readable version to reviewed by me, with the intent to teach me how the script works and how I would implement it elsewhere as I learn to code Python.

*Description:*

Current Implementation:

- Zone-Based Entry System: The model tests 4 entry strategies (EPCH1-4) against pre-calculated morning zones. EPCH1/EPCH3 are "continuation" entries (price traverses through a zone), while EPCH2/EPCH4 are "rejection" entries (price bounces off a zone). Primary zones use EPCH1/2, secondary zones use EPCH3/4.
- M5 Entry Criteria - Close-Based Triggers: All entries require the M5 candle to close beyond the zone boundary (wicks alone don't trigger). For continuations, price must close on the opposite side of the zone from where it originated. For rejections, price enters the zone but closes back on the same side it came from. A "price origin detection" algorithm ensures mutual exclusivity (EPCH1 and EPCH2 never fire on the same candle).
- 4-Stage Pipeline Architecture: The backtester runs sequentially through: (1) Trade simulation against M5 data, (2) Entry enrichment with a 10-factor health score (multi-timeframe structure, volume analysis, SMA alignment, VWAP location), (3) Exit event tracking bar-by-bar, and (4) Optimal trade analysis with expanded decision-point views.
- Exit Priority System: Trades exit in strict priority order: Stop Loss first (zone boundary - $0.05 buffer), then Target (max of calculated target or 3R), then CHoCH (change of character via fractal-based market structure reversal), and finally EOD forced exit at 15:50 ET.
- Health Score Methodology: Entry quality is assessed using a 0-10 DOW_AI scoring system across 10 factors: 4 timeframe structure checks (H4/H1/M15/M5), 3 volume metrics (ROC, Delta, CVD), 2 SMA factors (alignment + spread momentum), and VWAP location. Scores classify as STRONG (8-10), MODERATE (6-7), WEAK (4-5), or CRITICAL (0-3).

Adjusted Implementation:

- Entry Trigger Change: Instead of waiting for an M5 candle to close beyond the zone boundary, entries would trigger on the first S15 bar that closes beyond the zone. This provides ~20x faster entry detection (15 seconds vs 5 minutes), allowing trades to capture more of the initial move when price breaks through or rejects from a zone.
- Data Infrastructure Requirements: The system would need a new data source for 15-second bars. Polygon API supports second-level aggregates, but this would require significant API call volume (~1,560 bars per ticker per trading day vs ~78 for M5). Rate limiting, caching, and potentially a real-time WebSocket feed would need consideration.
- Price Origin Detection Adaptation: The mutual exclusivity logic (determining if price "came from above" or "came from below" a zone) would need to scan S15 bars instead of M5. The lookback window (currently 50 M5 bars = ~4 hours) might need adjustment to an equivalent S15 count (~1,000 bars) to maintain the same temporal coverage.
- Stop Placement Remains Zone-Based: The stop logic (zone_low - $0.05 for longs, zone_high + $0.05 for shorts) would remain unchanged since stops are tied to zone structure, not entry bar structure. However, the entry price captured would likely be closer to the zone boundary, potentially reducing initial risk (R) per trade.
- Exit/Indicator Implications: While entries shift to S15, exits (CHoCH, Target, Stop) and indicators (SMA9, SMA21, VWAP) would likely remain on M5 to avoid noise. This creates a hybrid model: S15 for entry precision, M5 for trade management. The health score calculations would need clarification on which timeframe feeds them.

*Code:*

### 1. Data Fetcher (m5_fetcher.py) - PRIMARY CHANGE

| **Change**     | **Details**                                                                       |
| -------------- | --------------------------------------------------------------------------------- |
| API Endpoint   | Change range/5/minute → range/15/second                                           |
| Class Rename   | M5Fetcher → S15Fetcher (or create new class)                                      |
| Dataclass      | M5Bar → S15Bar (or generic Bar)                                                   |
| Premarket Bars | Increase MIN_PREMARKET_BARS from 50 → 800+ (16x more bars for same time coverage) |

```python
# Current (line 129):
url = f"{BASE_URL}/v2/aggs/ticker/{ticker}/range/5/minute/{from_date}/{to_date}"

# New:
url = f"{BASE_URL}/v2/aggs/ticker/{ticker}/range/15/second/{from_date}/{to_date}"
```

---

### 2. Configuration ([config.py](http://config.py)) - TUNING REQUIRED

| **Setting**    | **Current** | **New Value** | **Reason**                                                                  |
| -------------- | ----------- | ------------- | --------------------------------------------------------------------------- |
| FRACTAL_LENGTH | 5           | 20-30         | CHoCH lookback: 5 M5 bars = 25 min; need ~20 S15 bars for ~5 min equivalent |
| BAR_TIMEFRAME  | 5 (minutes) | 15 (seconds)  | New timeframe definition                                                    |

---

### 3. **Entry Models (entry_models.py) - LOOKBACK ADJUSTMENT**

| **Setting**       | **Current** | **New Value** | **Reason**                                                                      |
| ----------------- | ----------- | ------------- | ------------------------------------------------------------------------------- |
| MAX_LOOKBACK_BARS | 50          | 800           | Price origin detection needs same historical window (50 × 5 min = 800 × 15 sec) |

## **Good News: The entry detection logic itself (EPCH1-4) is 100% timeframe-agnostic - it uses bar OHLC properties only, no changes needed to the algorithm.**

### 4. **Backtest Runner (backtest_runner.py) - IMPORT UPDATES**

```python
# Change imports and instantiation:
from data.s15_fetcher import S15Fetcher  # was m5_fetcher

s15_fetcher = S15Fetcher(POLYGON_API_KEY)  # was M5Fetcher
bars = s15_fetcher.fetch_bars_extended(ticker, date)
```

## The bar processing loop requires **no changes** - it's already timeframe-agnostic.

### 5. **Exit Models (exit_models.py) - NAMING ONLY**

| **Change**   | **Details**                                            |
| ------------ | ------------------------------------------------------ |
| Class Rename | M5StructureTracker → S15StructureTracker               |
| Logic        | **No changes** - CHoCH detection is timeframe-agnostic |

---

### Files Requiring Changes (Priority Order)

| **Priority**  | **File**                      | **Change Type**                      |
| ------------- | ----------------------------- | ------------------------------------ |
| **Critical**  | data/m5_fetcher.py            | API endpoint, class/dataclass rename |
| **Critical**  | [config.py](http://config.py) | FRACTAL_LENGTH, timeframe settings   |
| **Critical**  | models/entry_models.py        | MAX_LOOKBACK_BARS increase           |
| **Important** | backtest_runner.py            | Import statements, fetcher init      |
| **Cosmetic**  | models/exit_models.py         | Class rename                         |
| **Cosmetic**  | engine/trade_simulator.py     | Comments only                        |

---

### Key Risks & Considerations

| **Risk**              | **Mitigation**                                                                            |
| --------------------- | ----------------------------------------------------------------------------------------- |
| **API Rate Limits**   | ~1,560 S15 bars/ticker/day vs 78 M5 bars; may need caching or WebSocket                   |
| **Signal Noise**      | S15 is noisier; may generate more false entries                                           |
| **CHoCH Sensitivity** | Fractal-based CHoCH on 15-sec bars catches micro-reversals; tune FRACTAL_LENGTH carefully |
| **Performance**       | 16x more bars to process per backtest run                                                 |
| **Polygon Support**   | Verify Polygon API supports 15-second aggregates (likely yes, down to 1-second)           |

> *Additional Notes:*
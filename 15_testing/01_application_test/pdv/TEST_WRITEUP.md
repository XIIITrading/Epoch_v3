# Prior Day Value (PDV) - Test Write-Up

**Module:** `00_shared/calculations/pdv/`
**Test:** `15_testing/01_application_test/pdv/test_pdv.py`
**Notion Task:** [XIII.METHOD.01] Prior Day Value
**Author:** XIII Trading LLC
**Date:** 2026-03-16

---

## Purpose

Determine if the current pre-market price (08:00 ET) is aligned with the prior day's value area relative to the market structure direction. Bull structure should have price above prior day value; Bear structure should have price below.

---

## Running the Test

```bash
# Interactive mode (prompts for ticker and date)
python 15_testing/01_application_test/pdv/test_pdv.py

# Direct mode
python 15_testing/01_application_test/pdv/test_pdv.py AAPL 2026-03-14
```

**Terminal will:**
1. Request ticker symbol
2. Request analysis date (YYYY-MM-DD)
3. Display all calculated results

---

## Output Fields

| # | Field | Description | Source |
|---|-------|-------------|--------|
| a | **PD POC** | Prior day's Point of Control — the price level with the highest traded volume during 04:00–20:00 ET | 5-min bars → Leviathan volume profile (30 zones, $0.01 granularity) |
| b | **PD VAH** | Prior day's Value Area High — the upper boundary of the 70% volume concentration around the POC | Same volume profile, expanding outward from POC until 70% of total volume is captured |
| c | **PD VAL** | Prior day's Value Area Low — the lower boundary of the 70% volume concentration around the POC | Same as above |
| d | **Price @ 08:00** | Close of the last available bar before 08:00 ET on the analysis date | 5-min bars (pre-market), fallback to H1 bars |
| e | **D1 ATR** | 14-period daily Average True Range (SMA method) | Daily OHLC bars, standard TR = max(H-L, |H-Cp|, |L-Cp|) |
| f | **D1 ATR High** | Price @ 08:00 + D1 ATR — upper envelope of "normal" daily range | Calculated: `price_at_0800 + d1_atr` |
| g | **D1 ATR Low** | Price @ 08:00 - D1 ATR — lower envelope of "normal" daily range | Calculated: `price_at_0800 - d1_atr` |
| h | **Direction** | Composite market structure direction at 08:00 ET (Bull / Bear / Neutral) | Fractal detection across D1 (1.5x), H4 (1.5x), H1 (1.0x), M15 (0.5x) with end_timestamp cutoff |
| i | **Alignment** | Whether price position relative to value area aligns with structure direction | See alignment logic below |

---

## Calculation Details

### 1. Prior Day Volume Profile

**Input:** 5-minute bars from the prior trading day, 04:00–20:00 ET (full extended session)

**Method:** Leviathan Volume Profile (shared library: `shared.indicators.core.volume_profile`)
- Session high/low defines the price range
- Range is divided into 30 equal zones
- Volume is distributed across zones based on where each bar's OHLC range falls
- Buy volume = bars where close > open; Sell volume = bars where close ≤ open

**Output:**
- **POC** = midpoint price of the zone with the highest total volume
- **Value Area** = expand outward from POC zone, adding adjacent zones alternately (higher volume side first), until 70% of total session volume is captured
  - **VAH** = top of the highest included zone
  - **VAL** = bottom of the lowest included zone

### 2. Price at 08:00 ET

Fetches 5-minute bars from the prior day through 08:00 ET on the analysis date. Returns the close of the last bar before the cutoff. This captures overnight/pre-market pricing.

**Fallback:** If no 5-min bars are available, tries hourly bars.

### 3. D1 ATR (14-period)

Standard ATR calculation:
```
True Range[i] = max(
    High[i] - Low[i],
    |High[i] - Close[i-1]|,
    |Low[i] - Close[i-1]|
)

D1 ATR = SMA(True Range, 14)
```

Uses daily bars with sufficient lookback (period × 2 + 10 days for weekends/holidays).

### 4. Market Structure Direction

Uses `MarketStructureCalculator` from `01_application/calculators/market_structure.py`:
- Fractal detection (5-bar pattern) per timeframe
- Identifies BOS (Break of Structure) and ChoCH (Change of Character)
- Weighted composite: D1 (1.5) + H4 (1.5) + H1 (1.0) + M15 (0.5)
- Data cut off at 08:00 ET via `end_timestamp`

**Simplified output:** "Bull" (Bull+ or Bull), "Bear" (Bear+ or Bear), or "Neutral"

### 5. Alignment Logic

```
Step 1: Determine price position relative to Value Area
  - ABOVE: price > VAH
  - BELOW: price < VAL
  - INSIDE: VAL ≤ price ≤ VAH

Step 2: Determine alignment
  - Bull direction + price ABOVE VA  → ALIGNED
  - Bear direction + price BELOW VA  → ALIGNED
  - Price INSIDE VA (any direction)  → ALIGNED
  - All other combinations           → NOT ALIGNED

Step 3: Determine Optimal vs Extended
  - Distance = price distance from nearest VA boundary
    - If ABOVE: distance = price - VAH
    - If BELOW: distance = VAL - price
    - If INSIDE: distance = 0
  - If distance ≤ D1 ATR → OPTIMAL
  - If distance > D1 ATR → EXTENDED
```

**Result combinations:**
| Alignment | Classification | Meaning |
|-----------|---------------|---------|
| Aligned (Optimal) | Best case | Price above/below value in direction of structure, within normal range |
| Aligned (Extended) | Caution | Price aligned with structure but stretched beyond 1 ATR from value |
| Not Aligned (Optimal) | Counter-trend | Price on wrong side of value for the structure, but within normal range |
| Not Aligned (Extended) | Worst case | Price on wrong side AND stretched beyond 1 ATR |

---

## Example Output

```
  ========================================================
    Prior Day Value Analysis — AAPL (2026-03-14)
  ========================================================

    Prior Day:        2026-03-13

    PD POC:           $171.25
    PD VAH:           $172.80
    PD VAL:           $169.50

    Price @ 08:00:    $173.15
    D1 ATR:           $3.42
    D1 ATR High:      $176.57
    D1 ATR Low:       $169.73

    Direction:        Bull
    Alignment:        Aligned (Optimal)

  ========================================================
```

**Interpretation:** AAPL's prior day value area was $169.50–$172.80 with POC at $171.25. At 08:00 ET, price is $173.15 — above the value area. Market structure is Bull. Since price is above value and structure is bullish, this is **Aligned**. The distance from VAH ($173.15 - $172.80 = $0.35) is well within the D1 ATR of $3.42, so it's **Optimal**.

---

## File Structure

```
00_shared/calculations/pdv/
├── __init__.py          # Package exports: calculate_pdv, PDVResult, Alignment
└── calculator.py        # Core calculation logic (all 7 steps)

15_testing/01_application_test/pdv/
├── test_pdv.py          # Interactive terminal test
└── TEST_WRITEUP.md      # This document
```

---

## Dependencies

- `shared.indicators.core.volume_profile` — Leviathan VP methodology (POC, VAH, VAL)
- `shared.indicators.config` — Volume profile configuration (resolution, value_area_pct)
- `01_application.data` — Polygon client (fetch_minute_bars, fetch_daily_bars, fetch_hourly_bars)
- `01_application.calculators.market_structure` — MarketStructureCalculator

---

## Future Integration Points

Once validated, these results should be integrated into:
1. **Zone confluence scoring** — Add PD VP POC/VAH/VAL to `BarData.get_all_levels()` with appropriate weights in `weights.py`
2. **Composite scoring** — Add 0–15 point alignment bonus to ticker selection scoring
3. **UI table columns** — `prior_day_value` and `value_alignment` columns in results tables
4. **Supabase export** — Push PD POC, VAH, VAL, and alignment to database

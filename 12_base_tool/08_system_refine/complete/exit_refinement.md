> *Purpose:*

> The purpose of this update is to improve and refine the total number of lines that are produced as a result of the exit events to a more useable amount. In it's current iteration, each change in indicator value is being tracked, however, with the update of the 10 indicator methodology the events should be refined to show a reduction or increase in the indicator value. This will be more useful during the trading day as the indicators can be monitored outside of the normal exit methodologies (3R, M5 CHoCH, EOD)

*Dev Rules:*

1. Do not generate any code without my explicit instructions
2. Do not assume anything (naming convention, modules, directories). Ask for clarification or for files you would like to read directly.
3. Always include .txt documentation at the end in two files
   1. AI readable and understandable with enough description and specific script context to be used in other AI conversations without having to provide the dull script directory.
   2. Human readable version to reviewed by me, with the intent to teach me how the script works and how I would implement it elsewhere as I learn to code Python.

*Description:*

Location: `C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\processor\exit_events\`

Documentation Output: `C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\reports\`

---

## Confirmed Implementation Decisions

| Question | Decision |
|----------|----------|
| Column Schema | Add 3 new columns: AC (Health_Summary), AD (Event_Priority), AE (Indicator_Changed) - Total 31 columns (A-AE) |
| MFE/MAE Placement | Chronological order based on when each extreme was reached (MAE first if it occurred first, MFE first if it occurred first) |
| HEALTH_CHANGE Granularity | Every single point change fires a separate event (7→6 fires, then 6→5 fires separately) |
| Health Score Tracking | Each change tracked separately as individual line items from entry to exit for deterioration analysis |
| Structure Flip Confirmation | Fire immediately (no 2-bar delay - swing confirmation already built into swing_detector.py) |
| Volume Events | Option C - Partial alignment captured only in health score, only VOLUME_ALIGNED/VOLUME_OPPOSED for full alignment |
| Backward Compatibility | Deprecate old event types with # DEPRECATED comments, do not delete |
| Indicator Identification | New column AE (Indicator_Changed) explicitly identifies which indicator(s) caused each health score change |

---

## New Column Schema (31 Columns, A-AE)

| Column | Name | Description |
|--------|------|-------------|
| A | Trade_ID | Join key (NOT unique) |
| B | Event_Seq | Event sequence (1,2,3...) |
| C | Event_Time | When event occurred |
| D | Bars_From_Entry | Bars since entry |
| E | Bars_From_MFE | Bars since MFE |
| F | Event_Type | Type of event |
| G | From_State | Previous state |
| H | To_State | New state |
| I | Price_at_Event | Price at event |
| J | R_at_Event | R-multiple at event |
| K | Health_Score | Health (0-10) |
| L | Health_Delta | Change from entry |
| M | VWAP | VWAP value |
| N | SMA9 | SMA9 value |
| O | SMA21 | SMA21 value |
| P | Volume | Bar volume |
| Q | Vol_ROC | Volume ROC % |
| R | Vol_Delta | Bar delta |
| S | CVD_Slope | CVD slope |
| T | SMA_Spread | SMA9 - SMA21 |
| U | SMA_Momentum | WIDENING/NARROWING/FLAT |
| V | M5_Structure | M5 direction |
| W | M15_Structure | M15 direction |
| X | H1_Structure | H1 direction |
| Y | H4_Structure | H4 direction |
| Z | Swing_High | M5 swing high |
| AA | Swing_Low | M5 swing low |
| AB | Bars_Since_Swing | Bars since swing |
| **AC** | **Health_Summary** | **IMPROVING / DEGRADING / STABLE** |
| **AD** | **Event_Priority** | **HIGH / MEDIUM / LOW** |
| **AE** | **Indicator_Changed** | **Which indicator(s) caused health change (comma-separated if multiple)** |

---

## Refined Event Types (Post-Implementation)

### Active Event Types
| Event Type | Priority | Description |
|------------|----------|-------------|
| ENTRY | HIGH | First event for every trade (event_seq = 1) |
| EXIT | HIGH | Final event for every trade |
| MFE | HIGH | Single event showing final Maximum Favorable Excursion |
| MAE | HIGH | Single event showing final Maximum Adverse Excursion |
| HEALTH_CHANGE | LOW/MEDIUM | Health score changed (MEDIUM if 2+ points, LOW if 1 point) |
| HEALTH_STRONG | HIGH | Score crossed from <8 to 8+ |
| HEALTH_WEAK | HIGH | Score crossed from >3 to 3 or below |
| HEALTH_CRITICAL | HIGH | Score crossed to 0 |
| M5_FLIP_BULL | HIGH | M5 structure flipped bullish |
| M5_FLIP_BEAR | HIGH | M5 structure flipped bearish |
| M15_FLIP_BULL | HIGH | M15 structure flipped bullish |
| M15_FLIP_BEAR | HIGH | M15 structure flipped bearish |
| H1_FLIP_BULL | HIGH | H1 structure flipped bullish |
| H1_FLIP_BEAR | HIGH | H1 structure flipped bearish |
| H4_FLIP_BULL | HIGH | H4 structure flipped bullish |
| H4_FLIP_BEAR | HIGH | H4 structure flipped bearish |
| VOLUME_ALIGNED | MEDIUM | All 3 volume factors now support trade direction |
| VOLUME_OPPOSED | MEDIUM | All 3 volume factors now oppose trade direction |

### Deprecated Event Types (Retained for Backward Compatibility)
- VWAP_LOST, VWAP_REGAIN
- SMA9_LOST, SMA9_REGAIN, SMA21_LOST, SMA21_REGAIN, SMA_CROSS_BULL, SMA_CROSS_BEAR
- SMA_SPREAD_WIDEN, SMA_SPREAD_NARROW, SMA_SPREAD_FLAT
- HIGHER_HIGH, LOWER_HIGH, HIGHER_LOW, LOWER_LOW
- M15_HIGHER_HIGH, M15_LOWER_HIGH, M15_HIGHER_LOW, M15_LOWER_LOW
- H1_HIGHER_HIGH, H1_LOWER_HIGH, H1_HIGHER_LOW, H1_LOWER_LOW
- VOL_ROC_ABOVE, VOL_ROC_BELOW, VOL_DELTA_BULL, VOL_DELTA_BEAR
- CVD_RISING, CVD_FALLING, CVD_FLAT
- VOLUME_SPIKE, VOLUME_DRY, VOLUME_NORMAL

---

## Indicator_Changed Column Values

The AE column will use these standardized identifiers:

| Identifier | Corresponds To | Health Factor |
|------------|----------------|---------------|
| H4_STRUCTURE | Column Y | Factor 1 |
| H1_STRUCTURE | Column X | Factor 2 |
| M15_STRUCTURE | Column W | Factor 3 |
| M5_STRUCTURE | Column V | Factor 4 |
| VOL_ROC | Column Q | Factor 5 |
| VOL_DELTA | Column R | Factor 6 |
| CVD | Column S | Factor 7 |
| SMA_ALIGN | Columns N, O | Factor 8 |
| SMA_MOMENTUM | Column U | Factor 9 |
| VWAP | Column M | Factor 10 |

Multiple simultaneous changes: `"VWAP,M5_STRUCTURE"` (comma-separated, no spaces)

---

Current Implementation:

- Bar-by-Bar State Tracking with Exhaustive Event Detection: The system processes each M5 bar from entry to exit, comparing the current state against the previous state snapshot. Every state change triggers an event - including each individual MFE/MAE update, every VWAP cross, each SMA cross, all volume ROC threshold crossings, CVD slope changes, SMA momentum shifts, and every swing point confirmation across M5/M15/H1 timeframes. This results in a high volume of events because the detection is optimized for completeness rather than significance.
- 10-Factor Health Score Recalculated Every Bar: Each bar recalculates all 10 DOW_AI health factors (H4/H1/M15/M5 structure, Volume ROC, Volume Delta, CVD, SMA Alignment, SMA Momentum, VWAP) and fires events whenever any factor crosses its threshold. This includes minor oscillations like CVD slope bouncing between 0.09 and 0.11 (triggering CVD_RISING/CVD_FLAT repeatedly) or SMA momentum toggling between WIDENING/NARROWING/FLAT.
- MFE/MAE Events Fire on Every New Extreme: Currently in event_detector.py:574-614, MFE fires whenever curr_mfe != prev_mfe and MAE fires whenever curr_mae != prev_mae. This means every tick higher (for longs) generates a new MFE event, and every tick lower generates a new MAE event - producing potentially dozens of MFE/MAE rows per trade as price grinds in the favorable/adverse direction.
- Granular Indicator Crossover Events: The system fires separate events for each indicator relationship: VWAP_LOST/REGAIN, SMA9_LOST/REGAIN, SMA21_LOST/REGAIN, SMA_CROSS_BULL/BEAR, VOL_ROC_ABOVE/BELOW, VOL_DELTA_BULL/BEAR, CVD_RISING/FALLING/FLAT, SMA_SPREAD_WIDEN/NARROW/FLAT. Price oscillating around any threshold (e.g., bouncing above/below VWAP) generates multiple events.
- Structure Events at Multiple Timeframes: The system detects swing point events (HIGHER_HIGH, LOWER_HIGH, HIGHER_LOW, LOWER_LOW) and structure flip events (M5_FLIP_BULL/BEAR, M15_FLIP_BULL/BEAR, H1_FLIP_BULL/BEAR, H4_FLIP_BULL/BEAR) across all timeframes. Each confirmed swing generates an event, even when it doesn't change the overall structure direction.

Refinement Plan:

- Consolidate MFE/MAE to Single Final Events: Modify event_detector.py:574-614 to remove the bar-by-bar MFE/MAE firing logic. Instead, capture MFE/MAE data in state_tracker.py throughout the trade but only emit a single MFE event and single MAE event at trade exit (in exit_event_tracker.py:818-837). The final EXIT event row will include the MFE/MAE prices in the existing columns, and two dedicated MFE/MAE summary rows will be added immediately before the EXIT row showing the final extreme price, R-value, and bar index where it occurred.
- Replace Granular Indicator Events with Health Score Delta Events: Instead of firing VWAP_LOST, SMA9_REGAIN, VOL_ROC_ABOVE, etc. as individual events, create a new consolidated event type HEALTH_CHANGE that fires when the 10-factor health score changes by +1 or -1 points. The from_state field will show the previous score (e.g., "7") and to_state will show the new score (e.g., "6"). The existing indicator columns (M-AB) already capture the full state at each event, so the specific indicator causing the change can be derived.
- Add Health Score Threshold Events for Significant Transitions: Create three new threshold-based events: HEALTH_STRONG (score crosses from <8 to 8+), HEALTH_WEAK (score crosses from >3 to 3 or below), and HEALTH_CRITICAL (score crosses from >0 to 0). These fire only once per threshold crossing per direction, providing clear signals for the key health state transitions that matter during live trading.
- Retain Structure Flip Events, Remove Swing Point Events: Keep the directional flip events (M5_FLIP_BULL, M5_FLIP_BEAR, M15_FLIP_BULL, M15_FLIP_BEAR, H1_FLIP_BULL, H1_FLIP_BEAR, H4_FLIP_BULL, H4_FLIP_BEAR) as these represent meaningful structure changes. Remove or deprecate the granular swing events (HIGHER_HIGH, LOWER_HIGH, HIGHER_LOW, LOWER_LOW, M15_HIGHER_HIGH, etc.) since these are intermediate steps that don't change the overall structure direction. The swing data remains available in columns Z-AB for analysis.
- Implement 2-Bar Confirmation for Indicator Crossovers: Add debouncing logic in state_tracker.py to require 2 consecutive bars of confirmation before an indicator state change is considered valid. Track pending_state_changes with a bar counter, and only update the actual state (and potentially fire an event) when the new state persists for 2 bars. This prevents oscillation noise from price bouncing around VWAP, SMA9, or other thresholds.
- Create Summary Health Delta Column: Add a new column Health_Summary (or repurpose an existing column) that shows the net health change direction: "IMPROVING" (health increased since last event), "DEGRADING" (health decreased), or "STABLE" (no change). This provides at-a-glance context for each event row without needing to compare health scores manually.
- Consolidate Volume Events to Significant Transitions Only: Replace the current 6 volume event types (VOL_ROC_ABOVE, VOL_ROC_BELOW, VOL_DELTA_BULL, VOL_DELTA_BEAR, CVD_RISING, CVD_FALLING, CVD_FLAT) with 2 summary events: VOLUME_ALIGNED (all 3 volume factors now support trade direction) and VOLUME_OPPOSED (all 3 volume factors now oppose trade direction). Partial alignment states are captured in the health score but don't generate separate events.
- Add Event Priority/Severity Classification: Introduce an Event_Priority field with values HIGH (structure flips, health threshold crossings, EXIT), MEDIUM (health score changes of 2+ points), and LOW (single-point health changes). This allows filtering the event log during live trading to show only high-priority alerts while retaining the full granular data for post-trade analysis.
- Preserve ENTRY and EXIT as Bookend Events: Keep the ENTRY event (event_seq=1) and EXIT event (final event_seq) unchanged as they provide essential trade context. Ensure ENTRY captures the initial 10-factor health snapshot and EXIT captures final health, total bars, final R, and references to when MFE/MAE occurred. These remain the anchors for XLOOKUP joins with backtest and entry_events worksheets.
- Update exit_events_map.json and Writer for New Schema: Modify exit_events_map.json to document the new reduced event type list and add the new fields (Health_Summary, Event_Priority). Update exit_events_writer.py column mappings if new columns are added. Deprecate but don't delete the old event types from the EventType enum to maintain backward compatibility with historical data, marking them with # DEPRECATED comments.
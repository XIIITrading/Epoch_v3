# EPOCH 2.0 - Entry Model Specifications

> All entry models are zone-based. Zones are identified in pre-market by `01_application`
> and trades are simulated in `03_backtest`.

---

## Zone Types

### Primary Zone
- **Source**: Highest-scoring HVN (High Volume Node) from volume profile analysis
- **Identification**: Pre-market by `01_application`
- **Properties**: zone_high, zone_low, hvn_poc (point of control)
- **Models**: EPCH1 (continuation), EPCH2 (rejection)

### Secondary Zone
- **Source**: Second-highest-scoring HVN
- **Identification**: Pre-market by `01_application`
- **Models**: EPCH3 (continuation), EPCH4 (rejection)

---

## Entry Models

### EPCH1 - Primary Zone Continuation
- **Type**: Continuation
- **Zone**: Primary
- **Description**: Price traverses through the primary zone
- **Entry Trigger**: Bar closes beyond zone in the direction of approach
- **Direction Logic**:
  - LONG: Price approaches from below, closes above zone_high
  - SHORT: Price approaches from above, closes below zone_low

### EPCH2 - Primary Zone Rejection
- **Type**: Rejection
- **Zone**: Primary
- **Description**: Price wicks into zone but closes outside
- **Entry Trigger**: Bar wicks into zone but closes on the approach side
- **Direction Logic**:
  - LONG: Price approaches from above, wicks below zone_low, closes above
  - SHORT: Price approaches from below, wicks above zone_high, closes below

### EPCH3 - Secondary Zone Continuation
- **Type**: Continuation
- **Zone**: Secondary
- **Description**: Same logic as EPCH1 but for secondary zone

### EPCH4 - Secondary Zone Rejection
- **Type**: Rejection
- **Zone**: Secondary
- **Description**: Same logic as EPCH2 but for secondary zone

---

## Price Origin Detection

When a bar opens inside the zone, the system cannot determine direction from that bar alone.

**Solution**: Look back up to 1,000 bars to find the last close outside the zone.
- If last close was above zone -> price is approaching from above
- If last close was below zone -> price is approaching from below

---

## Trade Direction Assignment

| Approach From | Model Type | Direction |
|--------------|------------|-----------|
| Below | Continuation | LONG |
| Below | Rejection | SHORT |
| Above | Continuation | SHORT |
| Above | Rejection | LONG |

---

## Stop Types (Applied After Entry)

| Stop Type | Trigger | Canonical? |
|-----------|---------|-----------|
| zone_buffer | Price hits zone edge + 5% buffer | No |
| prior_m1 | Price hits prior M1 bar high/low | No |
| prior_m5 | Price hits prior M5 bar high/low | No |
| **m5_atr** | **Close beyond M5 ATR(14) x 1.1** | **YES** |
| m15_atr | Close beyond M15 ATR(14) x 1.1 | No |
| fractal | Price hits M5 fractal high/low | No |

---

## Win Condition (Canonical)

- **Stop**: M5 ATR(14) x 1.1, close-based trigger
- **Win**: MFE (Maximum Favorable Excursion) >= 1R before stop hit
- **Loss**: Stop hit before reaching 1R
- **Table**: `trades_m5_r_win`
- **Field**: `is_winner` (boolean)

---

## R-Multiple Tracking

- **1R**: Stop distance (entry to stop)
- **2R**: 2x stop distance in profit direction
- **3R**: 3x stop distance in profit direction
- **Fields**: `reached_2r`, `reached_3r` (boolean)
- **pnl_r**: Final P&L expressed in R-multiples

---

## Database Tables

### trades
Core trade records created by `03_backtest`:
```sql
trade_id, date, ticker, model, direction,
entry_price, entry_time, exit_price, exit_time,
exit_reason, zone_high, zone_low, zone_type, pnl_r
```

### trades_m5_r_win
Canonical outcomes using M5 ATR stop:
```sql
trade_id, is_winner, outcome, pnl_r,
stop_price, stop_distance, r1_price, r2_price, r3_price,
reached_2r, reached_3r, outcome_method
```

### setups
Zone definitions from `01_application`:
```sql
ticker, date, setup_type (PRIMARY/SECONDARY),
direction, zone_high, zone_low, hvn_poc,
target, r_r
```

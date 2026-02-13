# trades_m5_r_win Integration Map

## AI Context for Claude Code

This document is the integration reference for migrating all EPOCH downstream systems
to use the `trades_m5_r_win` table as the single canonical source of trade outcomes.

**Table Location**: Supabase PostgreSQL (`trades_m5_r_win`)
**Processor Location**: `03_backtest/processor/secondary_analysis/trades_unified/`
**Run Command**: `python run_all.py --only 15` or `python runner.py --verbose`

---

## Table Overview

| Metric | Value |
|--------|-------|
| Total Rows | 5,440 (1:1 with trades table) |
| ATR Records | 5,415 (`outcome_method = 'atr_r_target'`) |
| Fallback Records | 25 (`outcome_method = 'zone_buffer_fallback'`) |
| Win Rate | 54.50% (canonical) vs 35.92% (old zone_buffer) |
| Expectancy | +0.681R (canonical) vs +0.02R (old zone_buffer) |

**Why this table exists**: The original `trades.is_winner` used a zone_buffer stop
methodology with price-based (intrabar wick) stop triggers that produced unreliable
outcomes. The ATR M5 methodology using close-based stops and R-target exits produces
significantly more accurate outcome classification. This table consolidates both
methodologies with a clear priority: ATR first, zone_buffer fallback only for the
25 trades that lack r_win_loss records.

---

## Schema Reference

### Primary Key & Identification
```
trade_id        VARCHAR(50) PK    -- Same as trades.trade_id
date            DATE              -- Trade date
ticker          VARCHAR(10)       -- Stock symbol
model           VARCHAR(10)       -- EPCH01, EPCH02, EPCH03, EPCH04
zone_type       VARCHAR(20)       -- primary, secondary
direction       VARCHAR(10)       -- LONG, SHORT
```

### Entry & Zone Data (from trades)
```
entry_price     DECIMAL(12,4)     -- Entry price
entry_time      TIME              -- Entry time
zone_high       DECIMAL(12,4)     -- Zone upper boundary
zone_low        DECIMAL(12,4)     -- Zone lower boundary
```

### Original Zone Buffer Fields (preserved, zb_ prefix)
```
zb_stop_price   DECIMAL(12,4)     -- Original trades.stop_price
zb_target_3r    DECIMAL(12,4)     -- Original trades.target_3r
zb_exit_price   DECIMAL(12,4)     -- Original trades.exit_price
zb_exit_time    TIME              -- Original trades.exit_time
zb_exit_reason  VARCHAR(50)       -- Original trades.exit_reason
zb_pnl_dollars  DECIMAL(12,4)     -- Original trades.pnl_dollars
zb_pnl_r        DECIMAL(10,4)     -- Original trades.pnl_r
zb_is_winner    BOOLEAN           -- Original trades.is_winner
```

### Canonical Stop & R-Level Data
```
m5_atr_value        DECIMAL(12,4)  -- M5 ATR(14) at entry (NULL for fallback)
stop_price          DECIMAL(12,4)  -- Canonical stop price used
stop_distance       DECIMAL(12,4)  -- 1R distance in dollars
stop_distance_pct   DECIMAL(8,4)   -- Stop distance as % of entry
r1_price - r5_price DECIMAL(12,4)  -- R-level target prices
r1_hit - r5_hit     BOOLEAN        -- Did price reach each R-level?
r1_time - r5_time   TIME           -- Time of each R-level hit
r1_bars_from_entry  INTEGER        -- M1 bars from entry to R1
  ... (through r5_bars_from_entry)
stop_hit            BOOLEAN        -- Was stop triggered?
stop_hit_time       TIME           -- Time of stop trigger
stop_hit_bars_from_entry INTEGER   -- M1 bars from entry to stop
```

### Canonical Outcome (USE THESE FIELDS)
```
outcome         VARCHAR(10)       -- 'WIN' or 'LOSS' (canonical)
exit_reason     VARCHAR(20)       -- R_TARGET, STOP, EOD_WIN, EOD_LOSS,
                                  -- ZB_R_TARGET, ZB_STOP, ZB_EOD_WIN, ZB_EOD_LOSS
max_r_achieved  INTEGER           -- Highest R-level reached (0-5)
eod_price       DECIMAL(12,4)     -- Price at 15:30 for EOD exits
```

### Convenience Fields (USE THESE for common queries)
```
outcome_method  VARCHAR(25)       -- 'atr_r_target' or 'zone_buffer_fallback'
is_winner       BOOLEAN           -- outcome = 'WIN' (canonical boolean)
pnl_r           DECIMAL(10,4)     -- Continuous R-multiple
reached_2r      BOOLEAN           -- Same as r2_hit
reached_3r      BOOLEAN           -- Same as r3_hit
minutes_to_r1   INTEGER           -- Minutes from entry to R1 hit
```

---

## Field Mapping: Old -> New

### From trades table
| Old Query | Old Field | New Query | New Field | Notes |
|-----------|-----------|-----------|-----------|-------|
| `trades` | `is_winner` | `trades_m5_r_win` | `is_winner` | **Canonical boolean** |
| `trades` | `pnl_r` | `trades_m5_r_win` | `pnl_r` | Continuous R-multiple |
| `trades` | `stop_price` | `trades_m5_r_win` | `zb_stop_price` | Preserved with zb_ prefix |
| `trades` | `exit_reason` | `trades_m5_r_win` | `zb_exit_reason` | Preserved with zb_ prefix |
| `trades` | `exit_price` | `trades_m5_r_win` | `zb_exit_price` | Preserved with zb_ prefix |

### From r_win_loss table
| Old Query | Old Field | New Query | New Field | Notes |
|-----------|-----------|-----------|-----------|-------|
| `r_win_loss` | `outcome` | `trades_m5_r_win` | `outcome` | Same field, canonical |
| `r_win_loss` | `exit_reason` | `trades_m5_r_win` | `exit_reason` | Same values |
| `r_win_loss` | `max_r_achieved` | `trades_m5_r_win` | `max_r_achieved` | Same field |
| `r_win_loss` | `stop_price` | `trades_m5_r_win` | `stop_price` | Canonical stop |

### New convenience fields (no old equivalent)
| New Field | Derivation | Use Case |
|-----------|-----------|----------|
| `outcome_method` | `'atr_r_target'` or `'zone_buffer_fallback'` | Audit trail |
| `reached_2r` | `r2_hit` | Quick filter |
| `reached_3r` | `r3_hit` | Quick filter |
| `minutes_to_r1` | `r1_bars_from_entry` (M1 = 1 minute) | Speed analysis |

---

## System-by-System Migration

### 02_dow_ai (DOW AI Trading Assistant)

**Priority**: HIGH - blocks DOW AI v3.0

#### File: `batch_analyzer/data/trade_loader_v3.py`
**Lines 72-87** - SQL query that loads trades for analysis

**Current Code**:
```python
query = """
    SELECT
        t.trade_id,
        t.date as trade_date,
        t.ticker,
        t.direction,
        t.model,
        t.zone_type,
        t.entry_price,
        t.entry_time,
        t.is_winner,
        t.pnl_r
    FROM trades t
    JOIN entry_indicators ei ON t.trade_id = ei.trade_id
    WHERE ei.health_score IS NOT NULL
"""
```

**Change To**:
```python
query = """
    SELECT
        t.trade_id,
        t.date as trade_date,
        t.ticker,
        t.direction,
        t.model,
        t.zone_type,
        t.entry_price,
        t.entry_time,
        tu.is_winner,
        tu.pnl_r,
        tu.outcome,
        tu.outcome_method,
        tu.max_r_achieved
    FROM trades t
    JOIN trades_m5_r_win tu ON t.trade_id = tu.trade_id
    JOIN entry_indicators ei ON t.trade_id = ei.trade_id
    WHERE ei.health_score IS NOT NULL
"""
```

**Why**: Replaces `t.is_winner` and `t.pnl_r` with canonical values from `trades_m5_r_win`.

#### File: `ai_context/prompt_v3.py`
**Line 88** - TradeForAnalysis dataclass

**No code change needed** - the `is_winner` and `pnl_r` fields flow from
`trade_loader_v3.py`. The `actual_outcome` property derives from `is_winner`:
```python
@property
def actual_outcome(self) -> str:
    return 'WIN' if self.is_winner else 'LOSS'
```
This will automatically use the canonical outcome once the loader is updated.

#### File: `batch_analyzer/data/prediction_storage.py`
**Line 62** - Stores outcome in ai_predictions

**No code change needed** - reads `trade.is_winner` which will already be canonical.

#### File: `batch_analyzer/reports/accuracy_report.py`
**Lines 26-32** - Queries ai_predictions.actual_outcome

**No code change needed** - reads from `ai_predictions` table. The backfill
SQL below updates these historical records.

#### Backfill SQL (run once after migration):
```sql
-- Update ai_predictions with canonical outcomes
UPDATE ai_predictions ap
SET
    actual_outcome = CASE WHEN tu.is_winner THEN 'WIN' ELSE 'LOSS' END,
    actual_pnl_r = tu.pnl_r
FROM trades_m5_r_win tu
WHERE ap.trade_id = tu.trade_id
  AND (ap.actual_outcome IS DISTINCT FROM (CASE WHEN tu.is_winner THEN 'WIN' ELSE 'LOSS' END)
       OR ap.actual_pnl_r IS DISTINCT FROM tu.pnl_r);

-- Update dual_pass_analysis with canonical outcomes
UPDATE dual_pass_analysis dpa
SET actual_outcome = CASE WHEN tu.is_winner THEN 'WIN' ELSE 'LOSS' END
FROM trades_m5_r_win tu
WHERE dpa.trade_id = tu.trade_id
  AND dpa.actual_outcome IS DISTINCT FROM (CASE WHEN tu.is_winner THEN 'WIN' ELSE 'LOSS' END);
```

---

### 05_system_analysis (Statistical Dashboard)

**Priority**: MEDIUM - improves analysis accuracy

#### File: `data/supabase_client.py`
Multiple methods query trade outcomes. The system_analysis module already has
a stop type selector that can choose between stop types. The migration here
is to make `trades_m5_r_win` the **default** outcome source.

**Method: `fetch_trades()` / general trade queries**

**Current Pattern**:
```python
query = "SELECT * FROM trades WHERE ..."
```

**Change To**:
```python
query = """
    SELECT t.*, tu.is_winner as canonical_winner, tu.pnl_r as canonical_pnl_r,
           tu.outcome, tu.outcome_method, tu.max_r_achieved,
           tu.reached_2r, tu.reached_3r, tu.minutes_to_r1
    FROM trades t
    JOIN trades_m5_r_win tu ON t.trade_id = tu.trade_id
    WHERE ...
"""
```

**Method: `fetch_entry_indicators()` - Indicator analysis**

**Current Code** (app.py ~line 987):
```python
# Merges stop_outcomes_map into entry_df
if trade_id in stop_outcomes_map:
    entry_df['is_winner'] = stop_outcomes_map[trade_id]['is_winner']
```

**Change To**:
```python
# Use trades_m5_r_win as default (no stop selector needed for default)
# Still allow stop_analysis override via UI selector
entry_df['is_winner'] = tu_outcomes_map[trade_id]['is_winner']
```

**Method: Monte AI prompts** (`monte_ai/prompts.py`)

The prompt data will automatically use canonical outcomes once the upstream
data loading is updated. No prompt template changes needed.

---

### 06_training (Interactive Training Module)

**Priority**: MEDIUM - improves training accuracy

#### File: `data/supabase_client.py`
**Line 96** - `fetch_trades()` method

**Current Code**:
```python
query = "SELECT t.* FROM trades t ..."
```

**Change To**:
```python
query = """
    SELECT t.*,
           tu.is_winner as canonical_winner,
           tu.pnl_r as canonical_pnl_r,
           tu.outcome as canonical_outcome,
           tu.outcome_method
    FROM trades t
    JOIN trades_m5_r_win tu ON t.trade_id = tu.trade_id
    ...
"""
```

#### File: `models/trade.py`
**Line 75** - `Trade.from_db_row()` method

**Current Code**:
```python
is_winner=row.get('is_winner', False),
```

**Change To**:
```python
is_winner=row.get('canonical_winner', row.get('is_winner', False)),
```

This provides backward compatibility: uses canonical if available, falls back
to original if the query hasn't been updated yet.

#### File: `models/trade.py`
**Lines 408-414** - `TradeWithMetrics.is_winner_r` property

**Current Code**:
```python
@property
def is_winner_r(self) -> bool:
    return self.pnl_r > 0
```

**Change To**:
```python
@property
def is_winner_r(self) -> bool:
    # Use canonical pnl_r from trades_m5_r_win if available
    canonical = getattr(self, 'canonical_pnl_r', None)
    if canonical is not None:
        return canonical > 0
    return self.pnl_r > 0
```

#### File: `components/stats_panel.py`
**Line 39** - Display win/loss

**No code change needed** - reads `trade.is_winner_r` which will use canonical
values once the model is updated.

---

## Query Patterns

### Basic Outcome Query (replaces `SELECT ... FROM trades WHERE is_winner`)
```python
# Python pattern
query = """
    SELECT trade_id, date, ticker, model, direction,
           is_winner, pnl_r, outcome, outcome_method
    FROM trades_m5_r_win
    WHERE date BETWEEN %s AND %s
    ORDER BY date, entry_time
"""
```

### Win Rate by Model
```python
query = "SELECT * FROM v_trades_m5_r_win_by_model"
```

### Overall Summary
```python
query = "SELECT * FROM v_trades_m5_r_win_summary"
```

### Join with Other Tables (e.g., entry_indicators)
```python
query = """
    SELECT ei.*, tu.is_winner, tu.pnl_r, tu.outcome
    FROM entry_indicators ei
    JOIN trades_m5_r_win tu ON ei.trade_id = tu.trade_id
    WHERE tu.date BETWEEN %s AND %s
"""
```

### Filter Fallback Trades
```python
query = """
    SELECT * FROM trades_m5_r_win
    WHERE outcome_method = 'zone_buffer_fallback'
"""
```

### Compare Canonical vs Original
```python
query = """
    SELECT
        trade_id, ticker, date,
        zb_is_winner as original,
        is_winner as canonical,
        outcome_method
    FROM trades_m5_r_win
    WHERE zb_is_winner != is_winner
    ORDER BY date
"""
```

---

## Migration Checklist

### Phase 1: Infrastructure (COMPLETE)
- [x] Create `trades_m5_r_win` table schema
- [x] Build secondary processor (Step 15)
- [x] Register in `run_all.py`
- [x] Populate table (5,440 records)
- [x] Validate data integrity
- [x] Create this integration document

### Phase 2: DOW AI Migration
- [ ] Update `trade_loader_v3.py` SQL query
- [ ] Run backfill SQL for `ai_predictions`
- [ ] Run backfill SQL for `dual_pass_analysis`
- [ ] Test batch analyzer with canonical outcomes
- [ ] Verify accuracy report reflects new win rates

### Phase 3: System Analysis Migration
- [ ] Update `supabase_client.py` to default to `trades_m5_r_win`
- [ ] Update indicator analysis merge logic
- [ ] Test Monte AI prompts with canonical outcomes
- [ ] Verify dashboard charts reflect new data

### Phase 4: Training Module Migration
- [ ] Update `supabase_client.py` fetch_trades query
- [ ] Update `Trade.from_db_row()` to use canonical_winner
- [ ] Test flashcard UI with canonical outcomes
- [ ] Verify stats panel accuracy

### Phase 5: Validation
- [ ] Run full backtest pipeline: `python run_all.py`
- [ ] Verify Step 15 runs successfully after Step 14
- [ ] Compare win rates across all modules (should match)
- [ ] Verify no module still reads `trades.is_winner` directly

---

## Rollback Plan

The `trades_m5_r_win` table is purely additive. No existing tables are modified.

**To rollback**:
```sql
DROP TABLE IF EXISTS trades_m5_r_win CASCADE;
```

This drops the table and all dependent views. Downstream systems would need
their queries reverted to use `trades.is_winner` directly.

**To refresh data** (e.g., after r_win_loss reprocessing):
```sql
TRUNCATE trades_m5_r_win;
```
Then re-run: `python runner.py --verbose`

---

## Technical Notes

1. **Idempotent**: The processor uses `NOT EXISTS` for incremental processing
   and `ON CONFLICT DO UPDATE` for upserts. Safe to re-run at any time.

2. **Dependencies**: Step 15 depends on Step 14 (r_win_loss) and Step 1 (m1_bars).
   Must run after both complete.

3. **Performance**: Full population takes ~5 seconds for 5,440 trades.
   Incremental runs (new trades only) are near-instant.

4. **Fallback logic**: Uses close-based stop detection (matching ATR methodology).
   Zone buffer stop = `zone_low - (zone_distance * 5%)` for LONG.
   Only tracks R1 (not R2-R5) for fallback trades.

5. **pnl_r calculation**:
   - ATR WIN + R_TARGET: `max_r_achieved` (integer 1-5)
   - ATR LOSS + STOP: `-1.0`
   - ATR EOD: `(price_change) / stop_distance` (direction-adjusted)
   - Fallback WIN: `+1.0`
   - Fallback LOSS: `-1.0`

# EPOCH 2.0 - Indicator Definitions

> All indicators are calculated in `00_shared/indicators/` and stored in `entry_indicators` table.

---

## Structure Indicators

### H4 Structure
- **Source**: H4 (4-hour) bars
- **Values**: BULL / BEAR / NEUTRAL
- **Calculation**: Market structure detection using fractal highs/lows
- **Fractal Length**: 5 bars each side
- **Logic**:
  - BULL: Higher highs and higher lows
  - BEAR: Lower highs and lower lows
  - NEUTRAL: Mixed or transitioning

### H1 Structure
- **Source**: H1 (1-hour) bars
- **Values**: BULL / BEAR / NEUTRAL
- **Validated Edge**: NEUTRAL = +36pp (HIGH confidence)
- **Key Finding**: Trades taken when H1 is NEUTRAL perform significantly better

### M15 Structure
- **Source**: M15 (15-minute) bars
- **Values**: BULL / BEAR / NEUTRAL

### M5 Structure
- **Source**: M5 (5-minute) bars
- **Values**: BULL / BEAR / NEUTRAL

---

## Volume Indicators

### Volume ROC (Rate of Change)
- **Calculation**: Current volume vs baseline average
- **Baseline Period**: 20 bars
- **Thresholds**:
  - NORMAL: < 30%
  - ELEVATED: >= 30% (momentum present)
  - HIGH: >= 50% (strong momentum)

### Volume Delta
- **Calculation**: Buy volume - Sell volume (tick-level estimation)
- **Rolling Period**: 5 bars
- **Alignment**: Compared to trade direction
  - ALIGNED: Delta matches trade direction
  - MISALIGNED: Delta opposes trade direction
- **Validated Edge**: MISALIGNED = +5-21pp (MEDIUM confidence)
- **Magnitude Threshold**: 100,000 shares

### CVD Slope (Cumulative Volume Delta)
- **Calculation**: Linear regression slope of CVD over window
- **Window**: 15 bars
- **Thresholds**:
  - FALLING: < -0.1
  - FLAT: -0.1 to +0.1
  - RISING: > +0.1

---

## Price Indicators

### SMA9 / SMA21
- **Calculation**: Simple Moving Average
- **Periods**: 9 and 21
- **Source**: M5 close prices

### SMA Spread
- **Calculation**: |SMA9 - SMA21| / ((SMA9 + SMA21) / 2) * 100
- **Unit**: Percentage
- **Thresholds**:
  - NARROW: < 0.15%
  - WIDE: >= 0.15% (strong trend)

### SMA Momentum
- **Calculation**: Current spread / Spread 10 bars ago
- **Lookback**: 10 bars
- **Labels**:
  - WIDENING: ratio > 1.1x (trend strengthening)
  - NARROWING: ratio < 0.9x (trend weakening)
  - STABLE: 0.9x - 1.1x

### VWAP (Volume Weighted Average Price)
- **Calculation**: Cumulative (price * volume) / Cumulative volume
- **Reset**: Daily (market open)
- **Usage**: Price position relative to VWAP indicates institutional bias

---

## Composite Indicators

### Health Score (0-10)
- **Components**:
  - **Structure (0-4)**: H4 + H1 + M15 + M5 alignment with trade direction
  - **Volume (0-3)**: Vol ROC healthy + Vol Delta aligned + CVD slope aligned
  - **Price (0-3)**: SMA alignment + SMA momentum + VWAP position
- **Thresholds**:
  - STRONG: 8-10
  - MODERATE: 6-7
  - WEAK: 4-5
  - CRITICAL: 0-3
- **All weights**: 1.0 (equal weighting)

---

## Candle-Level Indicators

### Candle Range Percentage
- **Calculation**: (High - Low) / Open * 100
- **Unit**: Percentage
- **Thresholds**:
  - ABSORPTION: < 0.12% -> SKIP (universal filter)
  - LOW: 0.12% - 0.15%
  - NORMAL: >= 0.15% (tradeable)
  - HIGH: >= 0.20% (strong signal)
- **Validated Edge**: < 0.12% = -17pp, 33% WR (HIGH confidence)

---

## Database Storage

All entry-time indicators are stored in `entry_indicators` table:
```sql
SELECT
    trade_id,
    health_score, health_label,
    h4_structure, h1_structure, m15_structure, m5_structure,
    vol_roc, vol_delta, cvd_slope,
    sma9, sma21, sma_spread, sma_momentum_label,
    vwap
FROM entry_indicators
WHERE trade_id = 'xxx';
```

Bar-level indicators are in `m5_indicator_bars` and `m1_indicator_bars` tables.

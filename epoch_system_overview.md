# Epoch Trading System v1.0
## XIII Trading LLC - System Documentation

---

# Table of Contents

1. [System Overview](#1-system-overview)
2. [Module 01: Market Scanner](#2-module-01-market-scanner)
3. [Module 02: Zone System Pipeline](#3-module-02-zone-system-pipeline)
   - [01: Market Structure](#31-market-structure)
   - [02: Ticker Structure](#32-ticker-structure)
   - [03: Bar Data](#33-bar-data)
   - [04: HVN Identifier](#34-hvn-identifier)
   - [05: Raw Zones](#35-raw-zones)
   - [06: Zone Results](#36-zone-results)
   - [07: Setup Analysis](#37-setup-analysis)
   - [08: Visualization](#38-visualization)
4. [Module 09: Backtesting Engine](#4-module-09-backtesting-engine)
   - [Entry Events Processor](#41-entry-events-processor)
   - [Exit Events Processor](#42-exit-events-processor)
   - [Optimal Trade Analysis](#43-optimal-trade-analysis)
   - [Options Analysis](#44-options-analysis)

---

# 1. System Overview

The **Epoch Trading System** is a comprehensive institutional-grade trading analysis platform designed for identifying high-probability trading zones based on volume profile analysis and multi-timeframe confluence. The system processes market data through a sequential pipeline that identifies High Volume Nodes (HVNs), creates trading zones, ranks them by confluence scoring, and provides backtesting capabilities with detailed trade analysis.

## Core Philosophy

Unlike traditional systems that use timeframe-based weighting (e.g., daily, weekly, monthly HVNs), Epoch uses **volume-rank-based scoring**. The highest volume POCs (Points of Control) receive the highest base scores regardless of when they formed, emphasizing that price levels with the most trading activity create the strongest support/resistance.

## Key Differentiators

- **Volume-First Approach**: Zone scoring based on actual volume concentration rather than arbitrary timeframe importance
- **Hybrid Backtesting Model**: S15 (15-second) entries with M5 (5-minute) exit management for precise entry timing
- **10-Factor Health Scoring**: DOW_AI methodology for consistent trade quality assessment
- **Multi-Timeframe Structure Analysis**: H4, H1, M15, M5 alignment tracking
- **Options Integration**: Full options analysis pipeline for P&L conversion

---

# 2. Module 01: Market Scanner

**Location**: `01_market_scanner/`

The Market Scanner is the entry point for ticker selection, using a sophisticated two-phase filtering and scoring system.

## Two-Phase Filtering Process

### Phase 1: Coarse Filter (Eliminate Non-Candidates)
Quickly eliminates tickers that don't meet basic requirements:
- **Minimum Price**: Default $5.00 (eliminates penny stocks)
- **Minimum Average Volume**: Default 1,000,000 shares/day
- **Minimum Market Cap**: Default $500M (eliminates micro-caps)
- **Maximum Price**: Optional ceiling filter

### Phase 2: Scoring Engine (Quality Ranking)
Surviving tickers receive a composite score based on weighted criteria:

| Criterion | Description | Weight |
|-----------|-------------|--------|
| **Liquidity Score** | Volume relative to threshold | 25% |
| **Volatility Score** | ATR% within optimal range | 20% |
| **Price Action Score** | Clean price movement patterns | 20% |
| **Sector Score** | Sector momentum/strength | 15% |
| **Technical Score** | Key level proximity | 20% |

### Scoring Formula

```
Composite Score = (Liquidity * 0.25) + (Volatility * 0.20) + (PriceAction * 0.20)
                + (Sector * 0.15) + (Technical * 0.20)
```

### Filter Profiles

Pre-configured profiles for different trading styles:
- **Default**: Standard filtering (Min: $5, Vol: 1M)
- **High Volume**: Aggressive liquidity focus (Vol: 2M+)
- **Mid Cap**: Balance of liquidity and opportunity
- **Conservative**: Tighter criteria for lower risk

---

# 3. Module 02: Zone System Pipeline

The Zone System is an 8-stage pipeline that transforms raw market data into actionable trading zones.

## 3.1 Market Structure

**Location**: `02_zone_system/01_market_structure/`

Calculates overall market structure using fractal-based detection.

### Fractal Detection Algorithm

Uses a 5-bar fractal pattern (configurable via `fractal_length`):
- **Bullish Fractal** (Swing Low): Middle bar low is lower than N bars on either side
- **Bearish Fractal** (Swing High): Middle bar high is higher than N bars on either side

### Structure Break Detection

- **BOS (Break of Structure)**: Price closes beyond the previous fractal in the current trend direction
- **ChoCH (Change of Character)**: Price closes beyond a fractal against the current trend direction

### Structure States

| State | Code | Description |
|-------|------|-------------|
| Bullish | 1 | Price making higher highs, higher lows |
| Bearish | -1 | Price making lower highs, lower lows |
| Neutral | 0 | No confirmed structure |

---

## 3.2 Ticker Structure

**Location**: `02_zone_system/02_ticker_structure/`

Calculates per-ticker market structure across multiple timeframes using the same fractal-based methodology.

### Timeframes Analyzed

| Timeframe | Code | Lookback Period | Min Bars Required |
|-----------|------|-----------------|-------------------|
| H4 | 4-hour | 100 days | 100 bars |
| H1 | 1-hour | 50 days | 150 bars |
| M15 | 15-minute | 15 days | 100 bars |
| M5 | 5-minute | 5 days | 50 bars |

### Output Fields

- **Direction**: BULL, BEAR, or NEUTRAL
- **Strong Level**: Key invalidation level (swing low for bulls, swing high for bears)
- **Weak Level**: Continuation level (recent high for bulls, recent low for bears)
- **Last Break Type**: BOS or ChoCH

---

## 3.3 Bar Data

**Location**: `02_zone_system/03_bar_data/`

Provides all technical calculations required for zone analysis.

### ATR Calculation (Average True Range)

```
True Range = max(
    high - low,                    # Current bar range
    abs(high - prior_close),       # Gap up consideration
    abs(low - prior_close)         # Gap down consideration
)

ATR = SMA(True Range, period)      # Default period: 14
```

### Supported ATR Timeframes

| Code | Timeframe | Purpose |
|------|-----------|---------|
| d1_atr | Daily | Zone sizing, target calculation |
| h4_atr | 4-Hour | HTF zone reference |
| h1_atr | Hourly | MTF zone reference |
| m15_atr | 15-Minute | Zone boundary precision |
| m5_atr | 5-Minute | Entry zone sizing |

### Camarilla Pivot Calculations

```
# Daily Camarilla Levels
Range = Prior High - Prior Low

R6 = (Prior High / Prior Low) * Prior Close  # Extended resistance
R4 = Prior Close + (Range * 1.1/2)           # Strong resistance
R3 = Prior Close + (Range * 1.1/4)           # Primary resistance

S3 = Prior Close - (Range * 1.1/4)           # Primary support
S4 = Prior Close - (Range * 1.1/2)           # Strong support
S6 = Prior Close - (R6 - Prior Close)        # Extended support
```

---

## 3.4 HVN Identifier

**Location**: `02_zone_system/04_hvn_identifier/`

Identifies the top 10 High Volume Nodes (POCs) within the user-defined Epoch period.

### Volume Profile Construction

1. **Price Bucketing**: Divide price range into $0.01 buckets
2. **Volume Attribution**: Assign bar volume to touched price levels using bar position weighting
3. **POC Identification**: Find local maxima in volume profile
4. **Ranking**: Sort POCs by total volume (highest first)

### Output: Top 10 POCs

| Rank | Weight | Description |
|------|--------|-------------|
| POC1 | 3.0 | Highest volume node |
| POC2 | 2.5 | Second highest |
| POC3 | 2.0 | Third highest |
| POC4 | 1.5 | Fourth highest |
| POC5 | 1.0 | Fifth highest |
| POC6 | 0.8 | Sixth highest |
| POC7 | 0.6 | Seventh highest |
| POC8 | 0.4 | Eighth highest |
| POC9 | 0.2 | Ninth highest |
| POC10 | 0.1 | Tenth highest |

---

## 3.5 Raw Zones

**Location**: `02_zone_system/05_raw_zones/`

Creates raw trading zones by combining HVN POCs with confluence analysis from multiple level types.

### Zone Construction

Each zone is built around a POC with boundaries calculated using ATR:
```
Zone High = POC Price + (M15 ATR * 0.5)
Zone Low = POC Price - (M15 ATR * 0.5)
```

### Confluence Categories and Weights

| Category | Examples | Weight | Bucket Max |
|----------|----------|--------|------------|
| **Monthly Levels** | M Open, M High, M Low, M Close | 3.0 | 3.0 |
| **Weekly Levels** | W Open, W High, W Low, W Close | 2.0 | 2.0 |
| **Daily Levels** | D Open, D High, D Low, D Close | 1.0 | 1.0 |
| **Options Levels** | OP1-OP10 (GEX strikes) | 2.5-0.5 | 2.5 |
| **Monthly Camarilla** | M S6, M S4, M S3, M R3, M R4, M R6 | 3.0 | 3.0 |
| **Weekly Camarilla** | W S6, W S4, W S3, W R3, W R4, W R6 | 2.0 | 2.0 |
| **Daily Camarilla** | D S6, D S4, D S3, D R3, D R4, D R6 | 1.0 | 1.0 |
| **Prior Period Daily** | PD Open, PD High, PD Low, PD Close, ON High, ON Low | 1.0 | 1.0 |
| **Prior Period Weekly** | PW Open, PW High, PW Low, PW Close | 2.0 | 2.0 |
| **Prior Period Monthly** | PM Open, PM High, PM Low, PM Close | 3.0 | 3.0 |
| **Market Structure D1** | D1 Strong, D1 Weak | 1.5 | 1.5 |
| **Market Structure H4** | H4 Strong, H4 Weak | 1.25 | 1.25 |
| **Market Structure H1** | H1 Strong, H1 Weak | 1.0 | 1.0 |
| **Market Structure M15** | M15 Strong, M15 Weak | 0.75 | 0.75 |

### Zone Scoring Formula

```
Total Score = Base POC Weight + Sum(Confluence Weights)

Where:
- Base POC Weight = EPOCH_POC_BASE_WEIGHTS[poc_rank]  # 3.0 to 0.1
- Confluence Weight = min(level_weight, bucket_max)   # Capped per category
```

---

## 3.6 Zone Results

**Location**: `02_zone_system/06_zone_results/`

Filters and ranks zones to produce the final Primary and Secondary zones.

### Zone Ranking Thresholds (L1-L5)

| Rank | Score Threshold | Quality |
|------|-----------------|---------|
| **L5** | >= 12.0 | BEST - Highest confluence |
| **L4** | >= 9.0 | HIGH - Strong confluence |
| **L3** | >= 6.0 | MODERATE - Decent confluence |
| **L2** | >= 3.0 | LOW - Minimal confluence |
| **L1** | < 3.0 | WORST - Single factor only |

### Zone Selection Logic

1. Rank all zones by total score
2. **Primary Zone**: Highest scoring zone (L4 or L5 preferred)
3. **Secondary Zone**: Second highest scoring zone with sufficient separation

### Filtering Criteria

- Minimum score threshold (configurable)
- Minimum distance from current price
- Maximum distance from current price (relevance filter)
- Non-overlapping requirement for Primary/Secondary

---

## 3.7 Setup Analysis

**Location**: `02_zone_system/07_setup_analysis/`

Generates the final setup string for TradingView PineScript visualization.

### Setup String Format (16 Values)

```
POC1,POC2,POC3,POC4,POC5,POC6,POC7,POC8,POC9,POC10,PRIMARY_HIGH,PRIMARY_LOW,SECONDARY_HIGH,SECONDARY_LOW,PRIMARY_TARGET,SECONDARY_TARGET
```

### Example

```
125.50,122.30,128.75,120.00,131.20,118.50,133.00,116.80,135.25,114.50,124.80,123.20,121.50,120.00,127.50,124.50
```

---

## 3.8 Visualization

**Location**: `02_zone_system/08_visualization/`

Streamlit-based visualization application for chart generation.

### Features

- **H4 Candlestick Charts**: 120 bars (~75 trading days)
- **Volume-by-Price (VbP)**: Full epoch volume profile
- **Zone Overlays**: Primary (solid) and Secondary (dashed) zones
- **POC Lines**: All 10 POCs from Module 04
- **Target Lines**: Calculated targets for each zone
- **Dark Theme**: Professional trading interface

### Chart Components

| Element | Color | Description |
|---------|-------|-------------|
| Primary Zone | Cyan | Highest scoring zone |
| Secondary Zone | Yellow | Second highest zone |
| POC Lines | White (dashed) | Volume concentration levels |
| VbP Profile | Gradient | Volume distribution |
| Targets | Green/Red | Directional targets |

---

# 4. Module 09: Backtesting Engine

**Location**: `02_zone_system/09_backtest/`

The backtesting engine simulates trade execution using a hybrid timeframe model.

## Core Architecture

### Hybrid S15/M5 Model (v3.0)

| Function | Timeframe | Purpose |
|----------|-----------|---------|
| **Entry Detection** | S15 (15-second) | Precise entry timing near zone boundaries |
| **Exit Management** | M5 (5-minute) | Stable exit execution (Stop, Target, CHoCH, EOD) |

### Trade ID Format

```
{TICKER}_{MMDDYY}_{MODEL}_{HHMM}
Example: LLY_120925_EPCH2_1450
```

### Entry Models

| Model | Code | Description |
|-------|------|-------------|
| EPCH1 | 1 | Primary zone continuation |
| EPCH2 | 2 | Primary zone rejection |
| EPCH3 | 3 | Secondary zone continuation |
| EPCH4 | 4 | Secondary zone rejection |

### Exit Priority (Highest to Lowest)

1. **STOP**: Stop loss hit (always -1R when `ASSUME_STOP_FILL_AT_PRICE=True`)
2. **TARGET_3R**: 3R target hit
3. **TARGET_CALC**: Calculated target hit (based on confluence)
4. **CHOCH**: Change of Character (M5 structure break)
5. **EOD**: End of Day (force close at 15:50 ET)

### P&L Calculation

```
# LONG trade
PnL_Dollars = Exit_Price - Entry_Price
Risk = Entry_Price - Stop_Price
PnL_R = PnL_Dollars / Risk

# SHORT trade
PnL_Dollars = Entry_Price - Exit_Price
Risk = Stop_Price - Entry_Price
PnL_R = PnL_Dollars / Risk
```

---

## 4.1 Entry Events Processor

**Location**: `09_backtest/processor/entry_events/`

Enriches each trade with detailed entry analysis using the DOW_AI 10-step methodology.

### DOW_AI 10-Factor Health Score

| Step | Factor | Weight | Healthy Condition |
|------|--------|--------|-------------------|
| 1 | H4 Structure | 1 | Aligned with trade direction |
| 2 | H1 Structure | 1 | Aligned with trade direction |
| 3 | M15 Structure | 1 | Aligned with trade direction |
| 4 | M5 Structure | 1 | Aligned with trade direction |
| 5 | Volume ROC | 1 | > +20% above 20-bar average |
| 6 | Volume Delta | 1 | Positive for LONG, Negative for SHORT |
| 7 | CVD Direction | 1 | Rising for LONG, Falling for SHORT |
| 8 | SMA Alignment | 1 | SMA9 > SMA21 for LONG (inverse for SHORT) |
| 9 | SMA Spread Momentum | 1 | WIDENING (spread increasing) |
| 10 | VWAP Location | 1 | Above VWAP for LONG (inverse for SHORT) |

### Health Labels

| Score Range | Label | Interpretation |
|-------------|-------|----------------|
| 8-10 | STRONG | High probability setup |
| 6-7 | MODERATE | Acceptable setup |
| 4-5 | WEAK | Caution advised |
| 0-3 | CRITICAL | Avoid or reduce size |

### Volume Delta Calculation (Bar Position Method)

```
bar_position = (close - low) / (high - low)    # 0 to 1
delta_multiplier = (2 * bar_position) - 1       # -1 to 1
bar_delta = volume * delta_multiplier
```

### CVD Slope Calculation

```
# Cumulative Volume Delta over 15 bars
CVD = cumsum(bar_deltas[-15:])

# Linear regression slope
slope = linear_regression_slope(CVD)

# Normalize to -1 to 1 range
normalized_slope = slope / cvd_range
```

### Alignment Groups

| Group | Components | Purpose |
|-------|------------|---------|
| **HTF Aligned** | H4 + H1 | Higher timeframe confirmation |
| **MTF Aligned** | M15 + M5 | Mid-timeframe confirmation |
| **Volume Aligned** | ROC + Delta + CVD | Volume confirmation |
| **Indicator Aligned** | SMA + VWAP | Technical confirmation |

---

## 4.2 Exit Events Processor

**Location**: `09_backtest/processor/exit_events/`

Tracks trade events throughout the lifecycle, from entry to exit.

### Event Types Tracked

| Event Type | Description | Priority |
|------------|-------------|----------|
| ENTRY | Initial trade entry | 1 |
| MFE | Maximum Favorable Excursion | 2 |
| MAE | Maximum Adverse Excursion | 2 |
| HEALTH_CHANGE | Health score changed | 3 |
| STRUCTURE_CHANGE | M5 structure changed | 4 |
| INDICATOR_CHANGE | Key indicator crossed | 5 |
| EXIT | Trade exit | 1 |

### Health Tracking (Continuous)

The exit events processor recalculates the 10-factor health score at each M5 bar, tracking:
- Health score progression (entry to exit)
- Health delta (change from previous bar)
- Degradation events (health score drops)
- Recovery events (health score improves)

### MFE/MAE Analysis

```
# Maximum Favorable Excursion (MFE)
# LONG: Highest price relative to entry between entry and exit
# SHORT: Lowest price relative to entry between entry and exit

# Maximum Adverse Excursion (MAE)
# LONG: Lowest price relative to entry between entry and exit (if stop hit, use stop price)
# SHORT: Highest price relative to entry between entry and exit (if stop hit, use stop price)
```

### Output: 32 Columns per Event

Includes: Trade ID, Event Sequence, Event Time, Bars from Entry, Event Type, Price, R-multiple, Health Score, All Indicator Values, Structure States, Swing Levels

---

## 4.3 Optimal Trade Analysis

**Location**: `09_backtest/processor/optimal_trade/`

Creates a simplified 4-row view for each trade focusing on key moments.

### Key Moments Captured

| Row | Event Type | Purpose |
|-----|------------|---------|
| 1 | ENTRY | Indicator state at trade entry |
| 2 | MFE | Indicator state at best point |
| 3 | MAE | Indicator state at worst point |
| 4 | EXIT | Indicator state at trade exit |

### Analysis Metrics

**MFE Capture Analysis**:
```
Capture Rate = (Actual Exit R / MFE R) * 100
R Left on Table = MFE R - Actual Exit R
```

**Timing Analysis**:
- Average bars to MFE
- Average bars to MAE
- Average bars to Exit

**Health Progression**:
- Average entry health
- Average MFE health
- Average exit health

### Pattern Discovery

Enables analysis questions such as:
- What indicator states predict early MFE achievement?
- Which health score threshold optimizes exit timing?
- How does structure alignment correlate with MFE capture rate?

---

## 4.4 Options Analysis

**Location**: `09_backtest/processor/options_analysis/`

Converts equity trade results into options P&L analysis.

### Contract Selection Algorithm

1. **Direction Mapping**: LONG -> CALL, SHORT -> PUT
2. **Strike Selection**: ATM or 1-strike ITM
3. **Expiration Selection**: Current week expiration (minimum 2 DTE); if less than 2 DTE, select next week's expiration
4. **Liquidity Filter**: Minimum open interest threshold

### Data Requirements

| Data Type | Timeframe | Purpose |
|-----------|-----------|---------|
| Options Chain | Trade Date | Contract selection |
| Entry Bars | S15 (15-second) | Entry price discovery |
| Exit Bars | M5 (5-minute) | Exit price discovery |

### P&L Calculations

```
# Options P&L
PnL_Dollars = (Exit_Premium - Entry_Premium) * 100
PnL_Percent = (Exit_Premium - Entry_Premium) / Entry_Premium * 100

# Options R-Multiple (using underlying risk)
Option_R = Options_PnL_Dollars / Underlying_Risk_Dollars
```

### Output Metrics

| Metric | Description |
|--------|-------------|
| Options Ticker | Full options symbol |
| Strike | Selected strike price |
| Contract Type | CALL or PUT |
| Entry Premium | Premium at entry time |
| Exit Premium | Premium at exit time |
| PnL Dollars | Gross profit/loss |
| PnL Percent | Percentage return |
| Option R | R-multiple (options basis) |
| Outperformed | Did options outperform equity? |

### Summary Statistics

- Win Rate (options basis)
- Average P&L (dollars and percent)
- Average R-multiple
- Outperformance ratio (% of trades where options beat equity)

---

# Appendix A: Configuration Reference

## Excel Workbook

**Primary Workbook**: `epoch_v1.xlsm`

### Worksheets

| Sheet | Purpose |
|-------|---------|
| Analysis | Zone analysis results |
| backtest | Trade results |
| entry_events | Entry enrichment data |
| exit_events | Exit event tracking |
| optimal_trade | 4-row trade analysis |
| options_analysis | Options P&L analysis |

## API Requirements

- **Polygon.io API**: Market data (price, volume, options)
- **xlwings**: Excel integration

## Directory Structure

```
Epoch/
    01_market_scanner/
        config/
            filter_profiles.py
        filters/
            criteria.py
            scoring_engine.py
            two_phase_filter.py

    02_zone_system/
        01_market_structure/
        02_ticker_structure/
        03_bar_data/
            calculations/
                atr_calculator.py
                camarilla_calculator.py
        04_hvn_identifier/
        05_raw_zones/
            epoch_calc_engine.py
            epoch_config.py
        06_zone_results/
            zone_filter.py
        07_setup_analysis/
            epoch_setup_analyzer.py
        08_visualization/
            app.py
        09_backtest/
            backtest_runner.py
            config.py
            credentials.py
            data/
                m5_fetcher.py
                s15_fetcher.py
            engine/
                trade_simulator.py
            processor/
                entry_events/
                    entry_runner.py
                    entry_enrichment.py
                    structure_analyzer.py
                exit_events/
                    exit_runner.py
                    health_calculator_v2.py
                optimal_trade/
                    optimal_runner.py
                options_analysis/
                    options_runner.py

    epoch_v1.xlsm
```

---

# Appendix B: Quick Start Guide

## Daily Workflow

1. **Market Scanner** (Module 01)
   - Run to identify top ticker candidates
   - Review composite scores and select tickers

2. **Zone Analysis** (Modules 01-07)
   - Execute modules sequentially via Excel macros or Python
   - Review generated zones in visualization

3. **Visualization** (Module 08)
   - Launch Streamlit app: `streamlit run app.py`
   - Generate pre-market or post-market reports

4. **Backtesting** (Module 09)
   - Run backtest: `python backtest_runner.py`
   - Run entry enrichment: `python entry_runner.py`
   - Run exit events: `python exit_runner.py`
   - Run optimal trade analysis: `python optimal_runner.py`
   - Run options analysis: `python options_runner.py`

---

**Document Version**: 1.0
**Last Updated**: December 2025
**XIII Trading LLC**

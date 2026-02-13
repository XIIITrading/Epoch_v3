# EPOCH Backtest Visualization Module

## Overview

Module 09 visualization component for the EPOCH Trading System. Provides 4-quadrant trade visualization with PDF export capabilities.

## Features

- **4-Quadrant Layout** (Landscape Page):
  - Top Left: Trade metrics table
  - Top Right: M5 candlestick chart (09:00-16:00 ET)
  - Bottom Left: H1 chart (last 5 trading days)
  - Bottom Right: M15 chart (last 3 trading days)

- **Chart Elements**:
  - Candlesticks with proper coloring
  - VWAP (anchored to pre-market start each day)
  - 9 EMA and 21 EMA
  - Volume bars (separate subplot, no overlap with candles)
  - Primary and Secondary zones
  - HVN POC levels (from hvn_identifier)
  - Entry/Exit markers with stop and target lines

- **Export Options**:
  - Single trade PDF export
  - Batch export with summary page

## Directory Structure

```
09_backtest/visualization/
├── backtest_viz_app.py          # Main Streamlit application
├── requirements.txt             # Python dependencies
├── README.md                    # This file
│
├── config/
│   └── backtest_config.py       # Configuration settings
│
├── data_readers/
│   ├── backtest_reader.py       # Read trades from Excel backtest sheet
│   └── chart_data_fetcher.py    # Fetch OHLCV data from Polygon API
│
├── charts/
│   └── trade_chart_builder.py   # Build 4-quadrant visualization
│
└── export/
    └── pdf_exporter.py          # PDF export (single and batch)
```

## Installation

1. **Copy files** to: `C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\visualization\`

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Polygon API key** is configured in:
   `C:\XIIITradingSystems\Epoch\02_zone_system\04_hvn_identifier\calculations\credentials.py`

## Usage

### Running the Streamlit App

```bash
cd C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\visualization
streamlit run backtest_viz_app.py
```

### Visualization Modes

The app provides a radio button toggle for different visualization modes:
- **Backtest Results**: Trade visualization from backtest worksheet
- **Pre-Market Zones**: Morning zone calculations (integrates with existing)
- **Post-Market Review**: EOD review (integrates with existing)

### Workflow

1. Ensure `epoch_v1.xlsm` is **open in Excel**
2. Run the Streamlit app
3. Click **"Load Data"** to read trades from the backtest worksheet
4. Use filters to narrow down trades by:
   - Ticker
   - Model (EPCH1-4)
   - Direction (LONG/SHORT)
   - Zone Type (PRIMARY/SECONDARY)
   - Date Range
   - Result (Winners/Losers)
5. Select a trade from the list to view visualization
6. Export individual trades or batch export filtered results

## Data Source

### Backtest Worksheet Columns (A:T)

| Column | Field | Description |
|--------|-------|-------------|
| A | Date | Trade date (YYYY-MM-DD) |
| B | Ticker | Stock symbol |
| C | Model | EPCH1, EPCH2, EPCH3, EPCH4 |
| D | Zone_Type | PRIMARY or SECONDARY |
| E | Direction | LONG or SHORT |
| F | Zone_High | Zone upper boundary |
| G | Zone_Low | Zone lower boundary |
| H | Entry_Price | Trade entry price |
| I | Entry_Time | Entry timestamp (HH:MM:SS) |
| J | Stop_Price | Stop loss price |
| K | Target_3R | 3R target price |
| L | Target_Calc | Calculated target price |
| M | Target_Used | '3R' or 'CALC' |
| N | Exit_Price | Trade exit price |
| O | Exit_Time | Exit timestamp (HH:MM:SS) |
| P | Exit_Reason | STOP, TARGET_3R, TARGET_CALC, EOD |
| Q | PnL_$ | Dollar P&L |
| R | PnL_R | R-multiple P&L |
| S | Risk | Dollar risk per trade |
| T | Win | TRUE/FALSE |

## Chart Time Windows

| Chart | Timeframe | Window |
|-------|-----------|--------|
| M5 | 5-minute | Trade day 09:00-16:00 ET |
| H1 | 1-hour | Last 5 trading days |
| M15 | 15-minute | Last 3 trading days |

## VWAP Calculation

VWAP is anchored to pre-market start (04:00 ET) each day and runs through end of after-hours (20:00 ET). This matches the standard Epoch VWAP behavior.

## Color Scheme

| Element | Color |
|---------|-------|
| Primary Zone | Blue (#90bff9) |
| Secondary Zone | Red (#faa1a4) |
| VWAP | Orange (#ff9800) |
| 9 EMA | Blue (#2196f3) |
| 21 EMA | Purple (#9c27b0) |
| Bullish Candle | Green (#26a69a) |
| Bearish Candle | Red (#ef5350) |
| Stop Line | Orange (#ff5722) |
| Target Line | Green (#4caf50) |
| HVN POC | White dashed (#ffffff, 30% opacity) |

## Dependencies

- **pandas**: Data manipulation
- **numpy**: Numerical operations
- **matplotlib**: Chart generation
- **xlwings**: Excel integration
- **streamlit**: Web application
- **requests**: API calls to Polygon
- **pytz**: Timezone handling

## Integration Notes

This module lives within Module 09 (Backtest) and integrates with:
- **Module 04 (HVN Identifier)**: Reads HVN POC levels from bar_data worksheet
- **Module 09 (Backtest)**: Reads trade results from backtest worksheet
- **Existing Visualization**: Integrates as a toggle option (radio button)

## Troubleshooting

### "Could not connect to Excel"
- Ensure `epoch_v1.xlsm` is open in Excel (not just the file path existing)
- Close and reopen if Excel was restarted

### "No trades found"
- Verify the backtest worksheet has data in columns A:T
- Check that row 1 contains headers

### "No chart data"
- Verify Polygon API key is valid
- Check internet connection
- Some tickers may not have extended hours data

### "Chart looks empty"
- Check that the trade date is a valid trading day
- Verify the ticker exists in Polygon's database

## Future Enhancements

- [ ] Add market context indicators (once statistically validated)
- [ ] Interactive charts with Plotly
- [ ] Trade replay/playback feature
- [ ] Performance analytics dashboard

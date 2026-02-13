# Module 08: Visualization

**Location:** `C:\XIIITradingSystems\Epoch\02_zone_system\08_visualization\`

**Purpose:** Generate visual reports for trading setups with market structure, zone analysis, and price charts.

---

## Overview

Module 08 is a Streamlit-based visualization tool that creates comprehensive trading reports by combining:

- Excel data from Modules 01-07 (market structure, zones, setups)
- Live M5 price data from Polygon.io
- Volume profile analysis

## Features

- **Market Structure Display**: SPY, QQQ, DIA direction across D1, H4, H1, M15
- **Ticker Structure**: Direction + Strong/Weak levels per timeframe
- **Zone Results Table**: Filtered L2-L5 zones with POC, range, rank, score
- **Setup Analysis**: Primary (blue) and Secondary (red) setups with targets
- **M5 Candlestick Chart**: Last 90 bars with zone overlays
- **Volume Profile**: Session-based VP sidebar
- **PineScript String Output**: Ready to paste into TradingView indicator
- **PNG Export**: Download charts for documentation

---

## Directory Structure

```
08_visualization/
├── config/
│   └── visualization_config.py    # Colors, paths, settings
├── data_readers/
│   ├── excel_reader.py            # Read from Epoch workbook
│   └── polygon_fetcher.py         # Fetch M5 bars + build VP
├── charts/
│   └── chart_builder.py           # Matplotlib chart generation
├── cell_maps/
│   └── visualization_map.json     # Excel cell references
├── app.py                         # Streamlit application
├── credentials_template.py        # API key template
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

---

## Setup

### 1. Install Dependencies

```bash
cd C:\XIIITradingSystems\Epoch\02_zone_system\08_visualization
pip install -r requirements.txt
```

### 2. Configure Credentials

```bash
# Copy template
copy credentials_template.py credentials.py

# Edit credentials.py and add your Polygon API key
```

### 3. Verify Workbook Path

In `config/visualization_config.py`, ensure `WORKBOOK_PATH` points to your workbook:

```python
WORKBOOK_PATH = Path(r"C:\XIIITradingSystems\Epoch\epoch_v1.xlsm")
```

---

## Usage

### Run the Streamlit App

```bash
cd C:\XIIITradingSystems\Epoch\02_zone_system\08_visualization
streamlit run app.py
```

This opens the visualization interface in your browser (typically `http://localhost:8501`).

### Workflow

1. **Ensure Excel workbook is open** (`epoch_v1.xlsm`)
2. **Run Modules 01-07** to populate data
3. **Click "Generate All Reports"** in the sidebar
4. **Select ticker** from dropdown
5. **Toggle Pre-market/Post-market** as needed
6. **Add notes** in the text area
7. **Download PNG** using the export button

---

## Data Sources

### From Excel (via xlwings)

| Worksheet | Data |
|-----------|------|
| `market_overview` | Index ETF direction (rows 29-31), Ticker structure (rows 36-45) |
| `bar_data` | Current price (E4:E13), D1 ATR (T73:T82) |
| `zone_results` | Filtered zones (L2-L5) |
| `Analysis` | Setup strings (B44:C53), Primary/Secondary setups |

### From Polygon.io

- Last 90 M5 bars for each ticker
- Volume profile calculated at $0.01 granularity

---

## Color Scheme

Matches PineScript indicator colors:

| Element | Color | Hex |
|---------|-------|-----|
| Primary Zone | Blue | `#90bff9` |
| Secondary Zone | Red | `#faa1a4` |
| Pivot Zone | Purple | `#b19cd9` |
| Bull Direction | Teal | `#26a69a` |
| Bear Direction | Red | `#ef5350` |

---

## PineScript Integration

The setup string output format:
```
PrimaryHigh,PrimaryLow,PrimaryTarget,SecondaryHigh,SecondaryLow,SecondaryTarget
```

Example: `445.23,442.77,461.16,430.45,427.99,419.11`

Paste directly into the TradingView "Meridian - Primary Zones" indicator.

---

## Troubleshooting

### "Failed to connect to workbook"
- Ensure `epoch_v1.xlsm` is open in Excel
- Check the workbook path in `visualization_config.py`

### "No data returned for ticker"
- Verify your Polygon API key in `credentials.py`
- Check API rate limits (5 calls/minute for free tier)

### Charts not displaying
- Ensure all modules (01-07) have been run
- Check that zone_results worksheet has data

---

## Dependencies

- Python 3.8+
- pandas, numpy, requests
- xlwings (Excel integration)
- matplotlib (charting)
- streamlit (web interface)

---

*Module 08 | Epoch Trading System v1.0 | XIII Trading LLC*

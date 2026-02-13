# EPOCH Trading System - Module 10: Analysis Export

## Overview

Module 10 provides two core capabilities for the EPOCH Trading System:

1. **Daily JSON Export** - Generates a structured JSON file after each backtest that can be shared with Claude for AI-assisted analysis and feedback
2. **Historical Database** - Accumulates daily results in SQLite for long-term pattern analysis and strategy optimization

## Directory Structure

```
C:\XIIITradingSystems\Epoch\02_zone_system\10_setup_analysis\
├── config.py              # Configuration: paths, API keys, Excel mappings
├── excel_reader.py        # Reads backtest results from epoch_v1.xlsm
├── polygon_fetcher.py     # Fetches M5 bar data and VIX from Polygon
├── daily_exporter.py      # Generates structured JSON output
├── history_manager.py     # SQLite database operations
├── run_analysis.py        # Main runner script
├── README.md              # This file
├── requirements.txt       # Python dependencies
└── output/
    ├── daily/             # Daily JSON files
    └── epoch_history.db   # SQLite database
```

## Installation

1. Copy all files to `C:\XIIITradingSystems\Epoch\02_zone_system\10_setup_analysis\`

2. Install required packages:
```bash
pip install openpyxl requests
pip install pyperclip  # Optional: for clipboard support
```

3. Configure your Polygon API key:
   - Set environment variable: `POLYGON_API_KEY=your_key_here`
   - Or edit `config.py` directly

## Usage

### Process Today's Backtest
```bash
python run_analysis.py
```

### Process Specific Date
```bash
python run_analysis.py --date 2025-12-04
```

### Skip Polygon API (Testing/Offline)
```bash
python run_analysis.py --skip-polygon
```

### Generate Historical Report
```bash
python run_analysis.py --report
```

### Copy JSON to Clipboard
```bash
python run_analysis.py --copy
```

### View Configuration
```bash
python run_analysis.py --config
```

## Output: Daily JSON Structure

The daily JSON export includes:

```json
{
  "meta": {
    "date": "2025-12-04",
    "generated_at": "2025-12-04T16:05:00",
    "epoch_version": "1.0",
    "tickers_analyzed": 9
  },
  
  "market_context": {
    "spy_direction": "Bull",
    "spy_open": 605.50,
    "spy_close": 608.20,
    "vix_level": 14.5
  },
  
  "zone_analysis": {
    "AAPL": {
      "direction": "Bull",
      "primary_zone": {...},
      "secondary_zone": {...},
      "is_flip_zone": false,
      "price_action": {...}
    }
  },
  
  "trades": [...],
  "no_trades": [...],
  
  "statistics": {
    "overall": {...},
    "by_model": {...},
    "by_direction": {...},
    "by_zone_type": {...}
  },
  
  "validation_checks": {
    "flip_zones_detected": [...],
    "anomalies": [...]
  },
  
  "m5_price_data": {
    "summary": {...}
  }
}
```

## Database: SQLite Schema

The historical database contains these tables:

- **daily_summary** - One row per backtest day with aggregate stats
- **trades** - Individual trade records
- **no_trades** - Setups that didn't trigger
- **zones** - Zone configurations by day/ticker
- **model_stats** - Per-model statistics by day
- **price_action** - Daily OHLCV and metrics by ticker

### Example Queries

```sql
-- Model performance
SELECT model, COUNT(*) as trades, 
       ROUND(SUM(is_win)*100.0/COUNT(*),1) as win_rate,
       ROUND(SUM(pnl_r),2) as total_r
FROM trades GROUP BY model;

-- Performance on Bull days
SELECT COUNT(*) as trades, 
       ROUND(SUM(t.is_win)*100.0/COUNT(*),1) as win_rate
FROM trades t
JOIN daily_summary ds ON t.date = ds.date
WHERE ds.spy_direction = 'Bull';

-- Best performing day
SELECT date, total_trades, win_rate, net_pnl_r
FROM daily_summary
ORDER BY net_pnl_r DESC LIMIT 5;
```

## How to Use with Claude

1. Run the analysis after your backtest completes:
   ```bash
   python run_analysis.py
   ```

2. Open the generated JSON file from `output/daily/`

3. Copy the entire JSON content

4. Paste into a new Claude chat with a prompt like:
   
   > "Here are today's EPOCH backtest results. Please analyze the performance, identify patterns, and suggest any refinements to the zone calculations or entry models."

## Configuration

Edit `config.py` to adjust:

- File paths
- Excel cell mappings (if your workbook differs)
- Validation thresholds
- API settings

### Excel Column Mappings

The default mappings assume:
- Trade log: Columns A-S
- No-trade log: Columns AA-AN
- Summary: Columns U-V
- Analysis sheet primary zones: B31:K40
- Analysis sheet secondary zones: M31:V40
- Market overview ticker structure: Rows 36-45

## Future Enhancements

Planned for future versions:
- VWAP levels and deviations
- EMA 9/21 for momentum/trend
- ATR for volatility
- RSI for momentum
- Time-of-day analysis
- Supabase cloud integration

## Troubleshooting

**"Workbook not found"**
- Verify `EXCEL_WORKBOOK` path in `config.py`
- Ensure the workbook isn't open in Excel (use `data_only=True`)

**"API request failed"**
- Check your Polygon API key
- Use `--skip-polygon` to process without market data

**"No trades found"**
- Verify the backtest sheet has data in the expected columns
- Check that you ran the Module 09 backtest first

## Version History

- **1.0** (2025-12-04) - Initial release with JSON export and SQLite storage
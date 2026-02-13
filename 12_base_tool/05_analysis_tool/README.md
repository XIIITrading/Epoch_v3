# Epoch Analysis Tool

A Streamlit-based trading analysis tool that identifies high-volume nodes (HVN) and confluence zones for trading setups.

## Overview

The Epoch Analysis Tool replaces the Excel-based UI with a modern web interface, providing:

- **Market Structure Analysis** - Multi-timeframe fractal analysis (D1, H4, H1, M15)
- **Bar Data Calculation** - OHLC, ATR, Camarilla pivots across timeframes
- **HVN Identification** - Top 10 volume-ranked POCs using minute-bar volume profiles
- **Zone Calculation** - Confluence scoring with technical level overlaps
- **Setup Analysis** - Primary/Secondary trading setups with targets and R:R
- **PDF Export** - Generate analysis reports for offline review

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Polygon.io API key (for market data)

### Installation

1. Navigate to the analysis tool directory:
   ```bash
   cd C:\XIIITradingSystems\Epoch\05_analysis_tool
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your Polygon API key in `.env`:
   ```
   POLYGON_API_KEY=your_api_key_here
   ```

4. Run the application:
   ```bash
   streamlit run app.py
   ```

5. Open your browser to `http://localhost:8501`

## Usage Guide

### Analysis Mode

1. **Enter Tickers** - Add up to 10 tickers in the sidebar (one per row)
2. **Set Anchor Dates** - Each ticker has its own custom anchor date for HVN calculation
3. **Click Run Analysis** - The pipeline processes all tickers

#### Index Tickers
SPY, QQQ, and DIA are automatically analyzed with a **Prior Month** anchor date to provide market context.

### Scanner Mode

1. Select **Scanner** in the top mode selector
2. Choose a ticker list (S&P 500 or NASDAQ 100)
3. Set filter thresholds (min ATR, min price, min gap %)
4. Click **Run Scan** to find opportunities
5. Select tickers and click **Send to Analysis** to analyze them

### Batch Analysis

1. Enable **Batch Analysis Mode** in the sidebar
2. Select anchor presets (Prior Day, Prior Week, Prior Month, YTD)
3. Click **Run Batch Analysis**
4. Use the **Comparison** tab to find common POCs across timeframes

## Results Tabs

| Tab | Description |
|-----|-------------|
| **Market Overview** | Index and ticker market structure tables |
| **Bar Data** | OHLC, ATR, Camarilla pivots, HVN POCs |
| **Raw Zones** | All confluence zones with scoring |
| **Zone Results** | Filtered zones with tier classification |
| **Analysis** | Primary/Secondary setups with targets |
| **Summary** | Quick overview per ticker |
| **Visualization** | Chart preview and PDF export |

## Pipeline Stages

```
TickerInput (ticker + anchor_date)
    |
    v
BarData (calculate_bar_data)
    -> OHLC, ATR, Camarilla, Price
    |
    v
HVNResult (calculate_hvn)
    -> 10 volume-ranked POCs
    |
    v
RawZones (calculate_zones)
    -> Confluence scoring (L1-L5 ranks)
    |
    v
FilteredZones (filter_zones)
    -> Tiering (T1-T3) + Bull/Bear POCs
    |
    v
Setups (analyze_setups)
    -> Primary + Secondary with targets & R:R
```

## Configuration

### Zone Scoring

| Rank | Min Score | Tier |
|------|-----------|------|
| L5 | 12.0 | T3 (Best) |
| L4 | 9.0 | T3 |
| L3 | 6.0 | T2 |
| L2 | 3.0 | T1 |
| L1 | 0.0 | T1 |

### Anchor Date Presets

| Preset | Description |
|--------|-------------|
| Prior Day | Previous trading day |
| Prior Week | Previous Friday |
| Prior Month | Last day of previous month |
| YTD | January 1 of current year |
| Custom | User-specified date |

## Troubleshooting

### Common Issues

**"No data available for ticker"**
- Check if the ticker symbol is correct
- Verify your Polygon API key is valid
- Market may be closed (try a previous trading day)

**"Pipeline Error"**
- Clear the cache: Delete files in `.cache/` directory
- Check internet connection
- Verify anchor date is a valid trading day

**Slow Performance**
- First run for a ticker fetches data from API
- Subsequent runs use cached data (39x faster)
- 10 tickers should complete in under 60 seconds

### Cache Management

The tool caches API responses to improve performance:

```bash
# View cache stats
# (displayed on welcome screen)

# Clear cache manually
rm -rf .cache/
```

## File Structure

```
05_analysis_tool/
├── app.py                    # Main Streamlit entry point
├── requirements.txt          # Dependencies
├── .env                      # API keys (not in git)
├── .streamlit/
│   └── config.toml          # Theme configuration
├── config/
│   ├── settings.py          # App configuration
│   ├── weights.py           # Zone scoring weights
│   └── visualization_config.py
├── core/
│   ├── data_models.py       # Pydantic models
│   ├── state_manager.py     # Session state
│   └── pipeline_runner.py   # Pipeline orchestration
├── data/
│   ├── polygon_client.py    # API wrapper
│   └── cache_manager.py     # Caching layer
├── calculators/
│   ├── bar_data.py          # OHLC, ATR, Camarilla
│   ├── hvn_identifier.py    # HVN POC calculation
│   ├── zone_calculator.py   # Confluence zones
│   ├── zone_filter.py       # Filtering and tiering
│   ├── setup_analyzer.py    # Setup analysis
│   ├── market_structure.py  # Market structure
│   └── scanner.py           # Market scanner
├── pages/
│   ├── 1_market_overview.py
│   ├── 2_bar_data.py
│   ├── 3_raw_zones.py
│   ├── 4_zone_results.py
│   ├── analysis.py
│   ├── visualization.py
│   └── scanner.py
├── components/
│   ├── ticker_input.py
│   ├── data_tables.py
│   ├── chart_builder.py
│   └── pdf_generator.py
└── tests/
    └── test_integration.py
```

## Development

### Running Tests

```bash
cd C:\XIIITradingSystems\Epoch\05_analysis_tool
pytest tests/ -v
```

### Validation Against Original System

```bash
# Run comparison with original Excel system
python compare_tsla.py

# Compare outputs manually
python C:\XIIITradingSystems\Epoch\02_zone_system\compare_tsla_original.py
```

## Version History

- **v1.0** (2026-01-18) - Initial release
  - Full pipeline implementation
  - 7-tab results interface
  - Scanner integration
  - Batch analysis mode
  - PDF export

---

**Document Version:** 1.0
**Last Updated:** 2026-01-18

# Epoch Entry Qualifier v1.0

A PyQt6 desktop application that displays rolling indicator data for up to 6 tickers to assist with trade entry qualification. Data refreshes every 60 seconds from Polygon REST API.

## Features

- **Rolling 25-bar display** - Shows the most recent 25 M1 (1-minute) bars with shift-left behavior
- **Volume Delta indicators** - Raw single-bar and rolling 5-bar sum calculations
- **Score placeholders** - Continuation and Rejection scores ready for future indicator integration
- **Market hours awareness** - Pauses updates when market is closed (weekends, holidays, after 8pm ET)
- **Minute-synchronized refresh** - Updates at the top of each minute (:01, :02, etc.) for consistent data
- **Dark trading terminal theme** - Professional dark UI optimized for trading workflows
- **Pre-population on startup** - Fetches historical bars to immediately fill the rolling window

## Installation

1. Navigate to the entry_qualifier directory:
   ```
   cd C:\XIIITradingSystems\Epoch\04_dow_ai\entry_qualifier
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Ensure the Polygon API key is configured in the parent config.py:
   ```
   C:\XIIITradingSystems\Epoch\04_dow_ai\config.py
   ```

## Usage

Run the application:
```
python main.py
```

### Adding Tickers

1. Click the "+ Add Ticker" button
2. Enter a valid ticker symbol (e.g., SPY, QQQ, AAPL)
3. The ticker will be validated against the Polygon API
4. Historical data is fetched to pre-populate the rolling window

### Removing Tickers

Click the X button on any ticker panel to remove it.

## Data Display

Each ticker panel shows 4 rows of data:

| Row | Label | Description |
|-----|-------|-------------|
| 1 | Cont Score | Continuation score (0-10) - placeholder returns 0 |
| 2 | Rej Score | Rejection score (0-10) - placeholder returns 0 |
| 3 | Vol Delta (Raw) | Single bar volume delta estimate |
| 4 | Vol Delta (Roll) | Rolling 5-bar sum of volume deltas |

### Column Headers

- Columns -24 through 0 represent bars from oldest to newest
- The rightmost column shows row labels

### Conditional Formatting

**Scores (Cont/Rej):**
- Green background: Score >= 7
- Yellow background: Score 4-6
- Red background: Score <= 3

**Volume Delta:**
- Green text: Positive value (buying pressure)
- Red text: Negative value (selling pressure)
- Gray text: Zero/neutral

### Number Formatting

- Values >= 1,000,000: Displayed as XM (e.g., +2M)
- Values >= 1,000: Displayed as Xk (e.g., +45k)
- Values < 1,000: Displayed as whole number

## Market Hours

The application tracks US equity market hours (Eastern Time):

| Session | Hours |
|---------|-------|
| Pre-Market | 4:00 AM - 9:30 AM |
| Regular | 9:30 AM - 4:00 PM |
| After-Hours | 4:00 PM - 8:00 PM |
| Closed | 8:00 PM - 4:00 AM |

Updates pause automatically when the market is closed (including weekends and holidays).

## Configuration

Edit `entry_qualifier/eq_config.py` to modify settings:

```python
ROLLING_BARS = 25           # Number of bars to display
REFRESH_INTERVAL_MS = 60000 # Refresh interval (60 seconds)
VOL_DELTA_ROLL_PERIOD = 5   # Rolling period for Vol Delta
MAX_TICKERS = 6             # Maximum tickers allowed
PREFETCH_BARS = 30          # Bars to fetch for pre-population
```

## File Structure

```
entry_qualifier/
├── main.py                  # Application entry point
├── eq_config.py             # Entry qualifier configuration
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── ui/
│   ├── __init__.py
│   ├── main_window.py       # Main window class
│   ├── ticker_panel.py      # Single ticker panel widget
│   ├── ticker_dialog.py     # Add ticker dialog
│   └── styles.py            # Dark theme stylesheet
├── data/
│   ├── __init__.py
│   ├── api_client.py        # Polygon API wrapper
│   ├── data_worker.py       # QThread for async fetching
│   └── market_hours.py      # Market open/close logic
└── calculations/
    ├── __init__.py
    ├── volume_delta.py      # Vol delta calculations
    └── scores.py            # Score calculations (placeholder)
```

## Calculations

### Volume Delta (Raw)

Estimates buying/selling pressure using the bar position method:

```python
position = (2 * (close - low) / bar_range) - 1  # Range: -1 to +1
delta = position * volume
```

- Close at high = All buying (+volume)
- Close at low = All selling (-volume)
- Close at midpoint = Neutral (0)

### Volume Delta (Roll)

Rolling 5-bar sum of raw deltas:

```python
roll_delta = sum(raw_deltas[-5:])
```

## Future Extensions

- Additional indicator rows (CVD Slope, SMA Momentum, Vol ROC, etc.)
- Model-specific scoring (EPCH1-4 logic)
- Direction context input (LONG/SHORT for each ticker)
- Zone context integration
- Alert sounds/notifications
- DOW AI terminal integration
- Historical data export

## Troubleshooting

### "No data available" error
- Check if the ticker is valid
- Verify the market has been open recently for that ticker
- Check your internet connection

### "API Timeout" error
- Check your internet connection
- The Polygon API may be experiencing issues

### Data not updating
- Verify the market is open (check Market status in status bar)
- Check for error messages in the status bar

## Version History

- **v1.0** - Initial release with Volume Delta indicators and placeholder scores

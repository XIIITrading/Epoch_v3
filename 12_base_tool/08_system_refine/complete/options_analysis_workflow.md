# Options Analysis Workflow Implementation Plan

**Version:** 1.1
**Date:** 2025-12-23
**Author:** Claude AI / XIII Trading LLC
**Status:** IMPLEMENTED

---

## IMPLEMENTATION COMPLETE

The options analysis workflow has been implemented with the following files:

```
02_zone_system/09_backtest/processor/options_analysis/
├── __init__.py              # Module exports
├── options_config.py        # Configuration settings
├── options_fetcher.py       # Polygon options API client
├── contract_selector.py     # Modifiable ITM selection logic
├── options_calculator.py    # R and Net Returns calculations
├── options_events_writer.py # Excel output writer
└── options_runner.py        # Main orchestrator (Stage 5)
```

### Key Features:
- **Single contract per trade** (simplified approach)
- **Modifiable selection logic** in `contract_selector.py` (change SELECTION_METHOD)
- **R-Multiple calculation** for options trades
- **Net Returns calculation** (percentage return on premium)
- **Comparison to underlying** trade performance

### To Run:
```powershell
cd C:\XIIITradingSystems\Epoch
.\venv\Scripts\Activate.ps1
python .\02_zone_system\09_backtest\processor\options_analysis\options_runner.py
```

### Output:
- Creates `options_analysis` worksheet with 22 columns
- Includes R, Net Returns, and comparison metrics
- Summary statistics at bottom of data

---

## 1. Executive Summary

This document outlines the implementation plan for an Options Analysis Workflow that extends the existing Epoch backtest system. The workflow will:

1. Read completed trades from the existing backtest pipeline (entry/exit events)
2. Identify the appropriate options contract (first in-the-money) for each trade
3. Fetch options OHLC data at matching timeframes (S15 for entries, M5 for exits)
4. Calculate options P&L and compare to underlying equity performance
5. Output results to a new `options_analysis` worksheet

---

## 2. Background & Existing System

### 2.1 Current Backtest Pipeline

The Epoch backtest system operates in 4 stages:

| Stage | Module | Output |
|-------|--------|--------|
| 1 | `backtest_runner.py` | `backtest` worksheet (21 columns) |
| 2 | `entry_runner.py` | `entry_events` worksheet (44 columns) |
| 3 | `exit_runner.py` | `exit_events` worksheet (32 columns per event) |
| 4 | `optimal_runner.py` | `optimal_trade` worksheet |

### 2.2 Key Data Available from Backtest

From `backtest` worksheet (columns A-U):
```
trade_id      (A)  Format: {ticker}_{MMDDYY}_{model}_{HHMM}
date          (B)  Trade date
ticker        (C)  Underlying symbol (e.g., AAPL, LLY)
direction     (F)  LONG or SHORT
entry_price   (I)  Close price of entry bar
entry_time    (J)  Entry timestamp (HH:MM)
exit_price    (O)  Close price of exit bar
exit_time     (P)  Exit timestamp
win           (U)  1=Win, 0=Loss
```

### 2.3 API Integration Pattern

The existing system uses Polygon.io REST API with:
- Rate limiting: 0.25 seconds between calls
- Caching by `{ticker}_{date}` to minimize redundant fetches
- Credentials stored in `credentials.py`

---

## 3. Options Data Provider

### 3.1 API Endpoint

**Custom Bars (OHLC) for Options:**
```
GET /v2/aggs/ticker/{optionsTicker}/range/{multiplier}/{timespan}/{from}/{to}
```

**Parameters:**
- `optionsTicker`: Options contract symbol (e.g., `O:SPY251219C00650000`)
- `multiplier`: Bar size multiplier (e.g., `15` for 15-second, `5` for 5-minute)
- `timespan`: `second` or `minute`
- `from`/`to`: Date range (YYYY-MM-DD or millisecond timestamp)

**Response Fields:**
- `o`: Open price
- `h`: High price
- `l`: Low price
- `c`: Close price
- `v`: Volume
- `vw`: Volume weighted average price
- `n`: Number of transactions
- `t`: Unix millisecond timestamp

### 3.2 Options Chain Snapshot

**Endpoint to find available contracts:**
```
GET /v3/snapshot/options/{underlyingAsset}
```

**Useful Query Parameters:**
- `expiration_date`: Filter by YYYY-MM-DD
- `strike_price`: Filter by specific strike
- `contract_type`: `call` or `put`
- `limit`: Max 250 results

**Response includes:**
- Greeks (delta, gamma, theta, vega)
- Implied volatility
- Open interest
- Latest quote and trade

### 3.3 Data Latency

Per the plan tier (Options Starter):
- **Recency:** 15-minute delayed data
- **History:** 2 years (back to June 2, 2014)

**Important:** Since this is backtesting historical data, the 15-minute delay does not affect results.

---

## 4. Options Ticker Symbol Format

### 4.1 Construction

Options ticker format: `O:{UNDERLYING}{YYMMDD}{C/P}{STRIKE*1000}`

| Component | Format | Example |
|-----------|--------|---------|
| Prefix | `O:` | `O:` |
| Underlying | 1-5 characters | `AAPL` |
| Expiration | YYMMDD | `251219` (Dec 19, 2025) |
| Type | C=Call, P=Put | `C` |
| Strike | 8 digits (strike * 1000) | `00650000` ($650) |

### 4.2 Examples

| Description | Ticker Symbol |
|-------------|---------------|
| SPY $650 Call, Dec 19, 2025 | `O:SPY251219C00650000` |
| AAPL $175 Put, Jan 17, 2025 | `O:AAPL250117P00175000` |
| LLY $800 Call, Dec 20, 2024 | `O:LLY241220C00800000` |

### 4.3 Strike Price Formula

```python
# Encode strike price to 8-digit format
def encode_strike(strike_price: float) -> str:
    return f"{int(strike_price * 1000):08d}"

# Decode from ticker
def decode_strike(strike_str: str) -> float:
    return int(strike_str) / 1000.0

# Examples:
# $50.00  -> "00050000"
# $175.50 -> "00175500"
# $1250   -> "01250000"
```

---

## 5. Contract Selection Logic

### 5.1 First In-The-Money (ITM) Strategy

The goal is to select the options contract that is **first in the money** at the time of entry:

**For LONG trades (buying calls):**
- ITM Call = Strike < Entry Price
- Select the call with strike just below entry price (highest ITM strike)

**For SHORT trades (buying puts):**
- ITM Put = Strike > Entry Price
- Select the put with strike just above entry price (lowest ITM strike)

### 5.2 Selection Algorithm

```python
def select_itm_contract(
    underlying_price: float,
    direction: str,  # "LONG" or "SHORT"
    available_strikes: List[float],
    expiration_date: str  # YYYY-MM-DD
) -> Optional[str]:
    """
    Select first ITM contract for the trade.

    Args:
        underlying_price: Entry price of underlying
        direction: Trade direction
        available_strikes: List of available strike prices
        expiration_date: Target expiration date

    Returns:
        Options ticker symbol or None if not found
    """
    if direction == "LONG":
        # For longs: Buy call with strike < price (ITM call)
        # Select highest strike that is still ITM
        itm_strikes = [s for s in available_strikes if s < underlying_price]
        if not itm_strikes:
            return None
        selected_strike = max(itm_strikes)  # First ITM = closest to ATM
        contract_type = "C"
    else:
        # For shorts: Buy put with strike > price (ITM put)
        # Select lowest strike that is still ITM
        itm_strikes = [s for s in available_strikes if s > underlying_price]
        if not itm_strikes:
            return None
        selected_strike = min(itm_strikes)  # First ITM = closest to ATM
        contract_type = "P"

    return build_options_ticker(
        underlying=underlying,
        expiration=expiration_date,
        contract_type=contract_type,
        strike=selected_strike
    )
```

### 5.3 Expiration Selection

For backtesting, select the nearest weekly/monthly expiration that is:
1. **After the trade exit date** (contract must be valid through trade duration)
2. **Preferably 2-7 days after exit** (avoid extreme time decay at expiration)

```python
def select_expiration(
    trade_date: date,
    exit_date: date,
    available_expirations: List[date]
) -> Optional[date]:
    """
    Select appropriate expiration for the trade.

    Rules:
    1. Must expire AFTER exit_date
    2. Prefer closest expiration that gives 2+ days buffer
    """
    valid_expirations = [
        exp for exp in available_expirations
        if exp > exit_date
    ]

    if not valid_expirations:
        return None

    # Sort and take closest
    valid_expirations.sort()
    return valid_expirations[0]
```

---

## 6. Data Fetching Architecture

### 6.1 Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Options Analysis Workflow                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐     ┌──────────────────┐                  │
│  │  Backtest Data   │────▶│  Trade Reader    │                  │
│  │  (Excel)         │     │                  │                  │
│  └──────────────────┘     └────────┬─────────┘                  │
│                                    │                             │
│                                    ▼                             │
│                          ┌──────────────────┐                   │
│                          │ Contract Selector│                   │
│                          │ (ITM Logic)      │                   │
│                          └────────┬─────────┘                   │
│                                   │                              │
│              ┌────────────────────┼────────────────────┐        │
│              ▼                    ▼                    ▼        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ Options Chain    │  │ Entry Bar Fetch  │  │ Exit Bar Fetch│ │
│  │ Snapshot         │  │ (S15 bars)       │  │ (M5 bars)     │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
│              │                    │                    │        │
│              └────────────────────┼────────────────────┘        │
│                                   ▼                              │
│                          ┌──────────────────┐                   │
│                          │ P&L Calculator   │                   │
│                          └────────┬─────────┘                   │
│                                   │                              │
│                                   ▼                              │
│                          ┌──────────────────┐                   │
│                          │ Excel Writer     │                   │
│                          │ (options_analysis)│                  │
│                          └──────────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 API Request Flow

```python
# For each trade:
# 1. Get options chain to find available strikes/expirations
chain = fetch_options_chain(
    underlying=ticker,
    trade_date=entry_date,
    contract_type="call" if direction == "LONG" else "put"
)

# 2. Select appropriate contract
contract_ticker = select_itm_contract(
    underlying_price=entry_price,
    direction=direction,
    available_strikes=chain.strikes,
    expiration_date=selected_expiration
)

# 3. Fetch entry bar (15-second)
entry_bars = fetch_options_bars(
    options_ticker=contract_ticker,
    multiplier=15,
    timespan="second",
    from_date=entry_date,
    to_date=entry_date
)

# 4. Fetch exit bars (5-minute)
exit_bars = fetch_options_bars(
    options_ticker=contract_ticker,
    multiplier=5,
    timespan="minute",
    from_date=exit_date,
    to_date=exit_date
)
```

### 6.3 Caching Strategy

Similar to M5 fetcher, cache by:
- **Options chain:** `{underlying}_{date}` - one chain fetch per underlying per day
- **Options bars:** `{contract_ticker}_{date}` - one fetch per contract per day

```python
class OptionsDataCache:
    def __init__(self):
        self.chain_cache = {}    # {ticker_date: chain_data}
        self.bars_cache = {}     # {contract_date: bars}

    def get_chain(self, underlying: str, date: str) -> Optional[ChainData]:
        key = f"{underlying}_{date}"
        return self.chain_cache.get(key)

    def set_chain(self, underlying: str, date: str, data: ChainData):
        key = f"{underlying}_{date}"
        self.chain_cache[key] = data
```

---

## 7. File Structure

### 7.1 New Module Location

```
02_zone_system/09_backtest/processor/options_analysis/
├── __init__.py
├── options_runner.py           # Main orchestrator (Stage 5)
├── options_fetcher.py          # Polygon options API client
├── contract_selector.py        # ITM contract selection logic
├── options_calculator.py       # P&L and Greeks calculations
├── options_events_writer.py    # Excel output writer
└── options_config.py           # Options-specific configuration
```

### 7.2 Integration with Existing Pipeline

Update `bt_runner.py` to include Stage 5:

```python
# bt_runner.py additions
from processor.options_analysis.options_runner import run_options_analysis

def run_full_pipeline():
    # Existing stages 1-4
    run_backtest()
    run_entry_events()
    run_exit_events()
    run_optimal_trade()

    # NEW: Stage 5 - Options Analysis
    run_options_analysis()
```

---

## 8. Output Schema

### 8.1 New Worksheet: `options_analysis`

| Column | Name | Description |
|--------|------|-------------|
| A | trade_id | Join key to backtest |
| B | ticker | Underlying symbol |
| C | direction | LONG or SHORT |
| D | entry_date | Trade date |
| E | entry_time | Entry time (HH:MM:SS) |
| F | entry_price | Underlying entry price |
| G | options_ticker | Full options ticker symbol |
| H | strike | Strike price |
| I | expiration | Expiration date (YYYY-MM-DD) |
| J | contract_type | CALL or PUT |
| K | option_entry_price | Options price at entry |
| L | option_entry_time | Matched options bar timestamp |
| M | option_entry_volume | Volume at entry bar |
| N | option_entry_iv | Implied volatility at entry |
| O | option_entry_delta | Delta at entry |
| P | exit_time | Exit time |
| Q | option_exit_price | Options price at exit |
| R | option_exit_time | Matched options bar timestamp |
| S | option_exit_volume | Volume at exit bar |
| T | option_pnl_dollars | P&L per contract ($) |
| U | option_pnl_pct | P&L percentage |
| V | underlying_pnl_r | Underlying P&L in R |
| W | contracts_simulated | Number of contracts (1) |
| X | status | SUCCESS, NO_DATA, NO_CONTRACT |
| Y | error_message | Error details if applicable |
| Z | processing_time | ISO timestamp |

### 8.2 Summary Statistics

Below the data, include:
- Total trades processed
- Successful options matches
- Failed matches (no data/no contract)
- Average options P&L vs underlying P&L
- Win rate comparison (options vs underlying)

---

## 9. Implementation Phases

### Phase 1: Core Infrastructure
1. Create `options_fetcher.py` - API client for Polygon options
2. Create `contract_selector.py` - ITM selection logic
3. Create `options_config.py` - Configuration settings
4. Add unit tests for ticker symbol construction

### Phase 2: Data Processing
1. Create `options_runner.py` - Main orchestrator
2. Create `options_calculator.py` - P&L calculations
3. Implement caching for options chain and bars
4. Handle missing data scenarios

### Phase 3: Output & Integration
1. Create `options_events_writer.py` - Excel output
2. Update `bt_runner.py` to include Stage 5
3. Create summary statistics
4. Add documentation

### Phase 4: Testing & Refinement
1. Test with sample trades
2. Validate P&L calculations
3. Handle edge cases (no ITM strikes, illiquid options)
4. Performance optimization

---

## 10. Key Considerations

### 10.1 Handling Missing Data

Options markets are less liquid than equities. Handle these scenarios:

1. **No options trading at entry time:**
   - Use closest available bar before entry
   - Flag as "interpolated"

2. **No ITM strikes available:**
   - Fall back to ATM (at-the-money)
   - Or flag trade as "no_contract"

3. **Wide bid-ask spreads:**
   - Use mid-price: `(bid + ask) / 2`
   - Or use VWAP from bar data

### 10.2 Liquidity Filters

Consider filtering out illiquid options:
```python
MIN_VOLUME = 10           # Minimum daily volume
MIN_OPEN_INTEREST = 100   # Minimum open interest
MAX_SPREAD_PCT = 5.0      # Maximum bid-ask spread %
```

### 10.3 Greeks Tracking (Future Enhancement)

For more advanced analysis, track Greeks at entry:
- Delta: Directional exposure
- Gamma: Rate of delta change
- Theta: Time decay per day
- Vega: Volatility sensitivity

This enables analysis of:
- How much of P&L came from delta vs theta
- Whether high IV hurt or helped
- Optimal strikes based on delta

### 10.4 Position Sizing (Future Enhancement)

For realistic backtesting, consider:
- Standard contract size: 100 shares
- Maximum position size based on account
- Margin requirements for ITM options

---

## 11. Example Trade Flow

### 11.1 Sample Trade from Backtest

```
trade_id:     LLY_122325_EPCH2_1450
ticker:       LLY
date:         2025-12-23
direction:    LONG
entry_price:  $798.50
entry_time:   14:50:00
exit_price:   $802.75
exit_time:    15:15:00
pnl_r:        0.85
win:          1
```

### 11.2 Options Workflow

1. **Get Options Chain for LLY on 2025-12-23:**
   - Available strikes: 790, 795, 800, 805, 810...
   - Available expirations: 2025-12-27, 2025-01-03...

2. **Select ITM Contract:**
   - Direction: LONG -> Need ITM Call
   - Entry price: $798.50
   - ITM strikes (strike < price): 790, 795
   - First ITM = $795 (closest to ATM)
   - Expiration: 2025-12-27 (first after exit date)
   - **Contract: O:LLY251227C00795000**

3. **Fetch Entry Bar (S15):**
   ```
   GET /v2/aggs/ticker/O:LLY251227C00795000/range/15/second/2025-12-23/2025-12-23
   ```
   - Find bar closest to 14:50:00
   - Entry options price: $8.50

4. **Fetch Exit Bar (M5):**
   ```
   GET /v2/aggs/ticker/O:LLY251227C00795000/range/5/minute/2025-12-23/2025-12-23
   ```
   - Find bar closest to 15:15:00
   - Exit options price: $12.25

5. **Calculate P&L:**
   ```
   Options P&L = ($12.25 - $8.50) / $8.50 = +44.1%
   Options P&L per contract = $375 ((12.25 - 8.50) * 100)
   Underlying P&L = ($802.75 - $798.50) / $798.50 = +0.53%
   ```

### 11.3 Output Row

```
trade_id:           LLY_122325_EPCH2_1450
ticker:             LLY
direction:          LONG
options_ticker:     O:LLY251227C00795000
strike:             795.00
expiration:         2025-12-27
contract_type:      CALL
option_entry_price: 8.50
option_exit_price:  12.25
option_pnl_dollars: 375.00
option_pnl_pct:     44.12
underlying_pnl_r:   0.85
status:             SUCCESS
```

---

## 12. API Rate Limiting

### 12.1 Request Patterns

Per trade, the workflow makes up to 3 API calls:
1. Options chain snapshot (once per underlying per day)
2. Entry bars fetch (S15)
3. Exit bars fetch (M5)

### 12.2 Rate Limit Configuration

```python
# options_config.py
API_DELAY = 0.25          # 0.25s = 4 requests/second
MAX_RETRIES = 3
RETRY_DELAY = 2.0
REQUEST_TIMEOUT = 30      # seconds
```

### 12.3 Estimated Processing Time

For 100 unique tickers with 200 trades:
- Chain fetches: 100 * 0.25s = 25 seconds
- Entry bars: 200 * 0.25s = 50 seconds
- Exit bars: 200 * 0.25s = 50 seconds
- **Total: ~2 minutes** (with caching)

---

## 13. Error Handling

### 13.1 Error Categories

| Category | Handling |
|----------|----------|
| NO_CHAIN | No options chain available for underlying |
| NO_STRIKES | No ITM strikes available at entry price |
| NO_EXPIRY | No valid expiration after trade exit |
| NO_ENTRY_BAR | No options bar at entry time |
| NO_EXIT_BAR | No options bar at exit time |
| API_ERROR | Polygon API returned error |
| RATE_LIMIT | Exceeded API rate limit |

### 13.2 Graceful Degradation

```python
def process_trade(trade: dict) -> OptionsResult:
    try:
        chain = fetch_chain(trade['ticker'], trade['date'])
        if not chain:
            return OptionsResult(status="NO_CHAIN")

        contract = select_contract(chain, trade)
        if not contract:
            return OptionsResult(status="NO_CONTRACT")

        entry_bar = fetch_entry_bar(contract, trade['entry_time'])
        exit_bar = fetch_exit_bar(contract, trade['exit_time'])

        if not entry_bar:
            return OptionsResult(status="NO_ENTRY_BAR")
        if not exit_bar:
            return OptionsResult(status="NO_EXIT_BAR")

        return calculate_pnl(entry_bar, exit_bar, trade)

    except APIError as e:
        return OptionsResult(status="API_ERROR", error=str(e))
```

---

## 14. Testing Plan

### 14.1 Unit Tests

1. **Ticker Construction:**
   ```python
   assert build_options_ticker("AAPL", "2025-01-17", "C", 175.00) == "O:AAPL250117C00175000"
   assert build_options_ticker("SPY", "2025-12-19", "P", 650.00) == "O:SPY251219P00650000"
   ```

2. **Strike Selection:**
   ```python
   # LONG trade at $100
   strikes = [95, 97.5, 100, 102.5, 105]
   assert select_itm_strike("LONG", 100.0, strikes) == 97.5

   # SHORT trade at $100
   assert select_itm_strike("SHORT", 100.0, strikes) == 102.5
   ```

3. **P&L Calculation:**
   ```python
   assert calculate_options_pnl(entry=5.0, exit=7.5, contracts=1) == 250.0
   ```

### 14.2 Integration Tests

1. Process 10 historical trades end-to-end
2. Verify Excel output matches expected format
3. Test error handling with missing data scenarios

### 14.3 Validation

1. Spot-check P&L against manual calculations
2. Compare options P&L correlation with underlying P&L
3. Verify no look-ahead bias in expiration selection

---

## 15. Documentation Deliverables

Upon completion, create:

### 15.1 AI-Readable Documentation
`C:\XIIITradingSystems\Epoch\02_zone_system\13_documentation\15_bt_options_analysis.txt`
- Full technical specification
- API endpoints and parameters
- Data flow diagrams
- Code examples

### 15.2 Human-Readable Guide
`C:\XIIITradingSystems\Epoch\02_zone_system\13_documentation\15_bt_options_analysis_guide.txt`
- Overview of options analysis workflow
- How to run the analysis
- How to interpret results
- Troubleshooting guide

---

## 16. Future Enhancements

### 16.1 Near-Term
- Add Greeks tracking (delta, theta, IV)
- Support for ATM contracts (not just ITM)
- Add spread strategies (vertical spreads)

### 16.2 Long-Term
- Real-time options signal generation
- Options-specific entry/exit criteria
- Multi-leg strategy analysis
- Integration with live trading

---

## 17. Approval & Next Steps

### 17.1 Questions for User

1. **Contract Selection:**
   - Confirm ITM selection logic (first ITM = closest to ATM)?
   - Should we fall back to ATM if no ITM available?

2. **Expiration Selection:**
   - Preference for weekly vs monthly expirations?
   - Minimum days to expiration requirement?

3. **Data Handling:**
   - Acceptable to skip trades with no options data?
   - Should we interpolate missing bars?

4. **Output:**
   - Additional columns needed in output?
   - Summary statistics requirements?

### 17.2 Implementation Order

Once approved:
1. Create Phase 1 files (options_fetcher, contract_selector, config)
2. Test API integration with sample data
3. Create Phase 2 files (runner, calculator, caching)
4. Test with 10-20 historical trades
5. Create Phase 3 files (writer, bt_runner integration)
6. Full pipeline test
7. Documentation

---

## 18. References

### 18.1 API Documentation
- [Polygon Options Custom Bars](https://massive.com/docs/rest/options/aggregates/custom-bars)
- [Polygon Options Chain Snapshot](https://massive.com/docs/rest/options/snapshots/option-chain-snapshot)
- [How to Read Options Ticker](https://polygon.io/blog/how-to-read-a-stock-options-ticker)

### 18.2 Existing Epoch Modules
- `02_zone_system/09_backtest/data/m5_fetcher.py` - Pattern for API fetching
- `02_zone_system/09_backtest/processor/entry_events/entry_runner.py` - Pipeline pattern
- `02_zone_system/13_documentation/12_bt_entry_events.txt` - Documentation format

---

**End of Implementation Plan**

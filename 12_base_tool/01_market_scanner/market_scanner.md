================================================================================
EPOCH TRADING SYSTEM - MODULE 01: MARKET SCANNER
XIII Trading LLC | Documentation v1.0
================================================================================

PURPOSE
-------
Pre-market and overnight stock scanner that identifies high-potential trading
candidates from S&P 500, NASDAQ 100, Russell 2000, or all US equities. Uses
two-phase filtering (hard filters then ranking) based on ATR, price, gap
percentage, overnight volume, and short interest. Outputs ranked results to
Excel for integration with Epoch trading workbook.

DIRECTORY
---------
01_market_scanner/

================================================================================
FILE INVENTORY
================================================================================

FILE: scan_runner.py
--------------------
Role: PRIMARY ENTRY POINT - Main execution script for Epoch v1 integration.

Command Line Arguments:
  --date: Scan date (YYYY-MM-DD), defaults to today
  --list: Ticker list (SP500, NASDAQ100, RUSSELL2000, DOW30, ALL_US_EQUITIES)
  --min-atr: Minimum ATR dollars (default: $2.00)
  --min-price: Minimum stock price (default: $10.00)
  --min-gap: Minimum gap percent (default: 2.0%)
  --excel-path: Output workbook path
  --summary: Read existing scan data instead of running new scan

Execution Flow:
  1. Parse CLI arguments
  2. Create FilterPhase with hard filter thresholds
  3. Create RankingWeights for phase 2 scoring
  4. Initialize TwoPhaseScanner
  5. Run scan for specified date
  6. Export results to Excel (max 20 rows)
  7. Display summary statistics

Default Configuration:
  - Excel Path: C:\XIIITradingSystems\Epoch\epoch_v1.xlsm
  - Ticker List: SP500
  - Min ATR: $2.00
  - Min Price: $10.00
  - Min Gap: 2%

Request this file for: CLI usage, default settings, main workflow issues.

--------------------------------------------------------------------------------

FILE: credentials.py
--------------------
Role: API credential storage for Polygon.io.

Contains:
  - POLYGON_API_KEY: API key for Polygon.io data access

Request this file for: API authentication issues, key rotation.

--------------------------------------------------------------------------------

FILE: config/scanner_config.py
------------------------------
Role: Central configuration hub - global settings and paths.

Contains:
  - BASE_DIR: Root directory for market scanner
  - CACHE_DIR, OUTPUT_DIR, TEMPLATES_DIR: Subdirectory paths
  - POLYGON_API_KEY: From credentials.py or environment
  - SUPABASE_URL, SUPABASE_KEY: Optional database integration
  - DEFAULT_PARALLEL_WORKERS: 10 (concurrent API calls)
  - DEFAULT_LOOKBACK_DAYS: 14 (historical data window)
  - PREMARKET_START_UTC: 4:00 AM ET (08:00 UTC winter, 09:00 UTC summer)
  - MARKET_OPEN_UTC: 9:30 AM ET (13:30 UTC winter, 14:30 UTC summer)
  - DEFAULT_UPDATE_FREQUENCY: 90 days (ticker list staleness)

Request this file for: Path configurations, parallel processing tuning,
market timing adjustments, external service credentials.

--------------------------------------------------------------------------------

FILE: config/filter_profiles.py
-------------------------------
Role: Predefined filter strategy configurations for different scan types.

Profiles Available:
  STRICT:
    price_min: $20, price_max: $300
    avg_volume_min: 2,000,000
    min_atr: $2.00, min_atr_percent: 1.5%

  RELAXED:
    price_min: $5, price_max: $500
    avg_volume_min: 500,000
    min_atr: $0.50, min_atr_percent: 0.5%

  MOMENTUM:
    Focus on high volatility
    min_atr: $3.00, min_atr_percent: 2.0%

  PENNY_STOCKS:
    price_min: $1, price_max: $10
    avg_volume_min: 5,000,000
    min_atr: $0.10, min_atr_percent: 3.0%

  GAP_UP / GAP_DOWN / LARGE_GAP:
    Specialized for gap trading strategies
    Large gap: 5%+ threshold

Request this file for: Adding new filter profiles, adjusting thresholds.

--------------------------------------------------------------------------------

FILE: data/ticker_manager.py
----------------------------
Role: Ticker list management and maintenance.

Enum TickerList:
  SP500, NASDAQ100, RUSSELL2000, DOW30, ALL_US_EQUITIES

Class: TickerManager
  get_tickers(ticker_list) -> list[str]:
    - Retrieves ticker list with staleness checking
    - Warns if list > 90 days old

  get_all_us_equities() -> list[str]:
    - Fetches from Polygon API (paginated)
    - 24-hour cache for performance

  update_tickers(ticker_list) -> None:
    - Updates lists from external sources (Wikipedia, Polygon)

  verify_ticker(ticker, ticker_list) -> bool:
    - Checks if ticker is in specified list

Storage: tickers.json in cache directory

Request this file for: Ticker list updates, adding new indices, staleness issues.

--------------------------------------------------------------------------------

FILE: data/fetchers.py
----------------------
Role: Data fetching abstraction layer for market data.

Abstract Interface: DataFetcherInterface
  fetch_historical(ticker, days) -> DataFrame
  fetch_intraday(ticker, date, interval) -> DataFrame

Class: PolygonDataFetcher
  - Wraps 09_data_server module for caching
  - Validates and fills data gaps
  - Returns empty DataFrame on errors

Request this file for: Data source issues, adding new data providers.

--------------------------------------------------------------------------------

FILE: data/overnight_fetcher.py
-------------------------------
Role: Calculate overnight trading volume metrics.

Time Windows (UTC):
  Current Overnight: Prior day 20:01 to current day 12:00
  Prior Overnight: 2 days ago 20:01 to 1 day ago 12:00
  Prior Regular Hours: 1 day ago 13:30 to 20:00

Class: OvernightFetcher
  fetch_overnight_volumes(ticker, date) -> dict:
    Returns:
      current_overnight_volume: Volume in current overnight session
      prior_overnight_volume: Volume in prior overnight session
      prior_regular_volume: Volume in prior regular session
      current_price: Most recent price

Data Source: 1-minute intraday bars from Polygon

Request this file for: Overnight volume calculation issues, time window adjustments.

--------------------------------------------------------------------------------

FILE: data/short_interest_fetcher.py
------------------------------------
Role: Fetch and cache short interest data from Polygon.

Class: ShortInterestFetcher
  load_short_data_for_tickers(tickers, date) -> None:
    - Targeted fetch for specific tickers (optimized)
    - Early exit when all target tickers found
    - 1-hour cache with date validation

  fetch_short_interest(ticker, date) -> dict:
    Returns:
      short_interest_percent: % of float shorted
      short_shares: Number of shares short
      days_to_cover: Days to cover short position
      data_date: Date of short interest data

Request this file for: Short interest data issues, cache management.

--------------------------------------------------------------------------------

FILE: filters/base_filter.py
----------------------------
Role: Abstract base class defining filter interface.

Methods:
  apply_filters(df) -> DataFrame
  validate_data(df) -> bool
  get_filter_summary() -> dict

Request this file for: Adding new filter types.

--------------------------------------------------------------------------------

FILE: filters/criteria.py
-------------------------
Role: Filter criteria configuration dataclass.

Class: FilterCriteria
  Parameters:
    price_min, price_max: Price range filter
    avg_volume_min: Minimum average daily volume
    premarket_volume_min: Minimum premarket volume
    dollar_volume_ratio_min: Minimum dollar volume ratio
    min_atr: Minimum ATR in dollars
    min_atr_percent: Minimum ATR as percentage
    min_gap_percent: Minimum gap percentage
    gap_direction: 'up', 'down', or 'both'
    market_cap_min: Optional minimum market cap

  Methods:
    to_dict(): For logging
    from_profile(profile_name): Create from predefined profiles

Request this file for: Filter configuration, adding new criteria.

--------------------------------------------------------------------------------

FILE: filters/two_phase_filter.py
---------------------------------
Role: Two-phase filtering parameter definitions.

Dataclass: FilterPhase (Hard Filters)
  min_atr: $2.00 (default)
  min_price: $10.00 (default)
  min_gap_percent: 2.0% (default)

Dataclass: RankingWeights (Soft Ranking)
  overnight_volume: 1.0
  relative_overnight_volume: 1.0
  relative_volume: 1.0
  gap_magnitude: 1.0
  short_interest: 1.0

Request this file for: Adjusting hard filter thresholds, ranking weight tuning.

--------------------------------------------------------------------------------

FILE: filters/premarket_filter.py
---------------------------------
Role: Pre-market filtering implementation.

Class: PremarketFilter
  apply_filters(df, criteria) -> DataFrame:
    - Applies FilterCriteria to market data
    - Combines filters with AND logic
    - Logs pass rates for each stage

  rank_by_interest(df, top_n) -> DataFrame:
    - Ranks passing stocks by interest score
    - Returns top N stocks

Request this file for: Filter logic issues, pass rate debugging.

--------------------------------------------------------------------------------

FILE: filters/scoring_engine.py
-------------------------------
Role: Interest score calculation engine.

Class: ScoringEngine
  Score Components (0-100 scale):
    1. Premarket Volume Ratio: 40% weight (default)
    2. ATR Percentage: 25% weight
    3. Dollar Volume: 20% weight
    4. Premarket Volume Absolute: 10% weight (log scale)
    5. Price-ATR Sweet Spot Bonus: 5% weight (2-5% ATR range)
    6. Gap Magnitude: 0% default (35% for gap scans)

  Methods:
    calculate_scores(df) -> DataFrame:
      - Computes all score components
      - Returns weighted total score

    rank_by_score(df) -> DataFrame:
      - Sorts and ranks by score

    explain_score(row) -> str:
      - Detailed breakdown for single stock

Request this file for: Score weighting adjustments, adding new score components.

--------------------------------------------------------------------------------

FILE: scanners/base_scanner.py
------------------------------
Role: Abstract base class for scanner implementations.

Methods:
  run_scan(date) -> DataFrame
  get_summary_stats(results) -> dict
  export_results(results, format) -> None

Request this file for: Adding new scanner types.

--------------------------------------------------------------------------------

FILE: scanners/premarket_scanner.py
-----------------------------------
Role: Comprehensive pre-market stock scanner.

Class: PremarketScanner
  __init__(ticker_list, criteria, parallel_workers=10):
    - Configures scan parameters
    - Sets up parallel processing

  run_scan(scan_date=None) -> DataFrame:
    1. Load ticker list
    2. Fetch historical data (14 days) per ticker in parallel
    3. Calculate ATR (14-period EMA of true range)
    4. Calculate average volume (20-day)
    5. Fetch premarket data (4:00 AM - scan time)
    6. Calculate gap percentage
    7. Apply all filter criteria
    8. Calculate interest scores
    9. Return ranked results

  Output Columns:
    rank, ticker, ticker_id, price, gap_percent, premarket_volume,
    atr, atr_percent, avg_volume, interest_score

  Special Features:
    - ticker_id format: AAPL.081125 (ticker.MMDDYY)
    - ThreadPoolExecutor for parallel data fetching
    - Progress callbacks for real-time updates
    - Market cap filtering for ALL_US_EQUITIES scans

Request this file for: Premarket scan logic, metric calculations, parallel processing.

--------------------------------------------------------------------------------

FILE: scanners/two_phase_scanner.py
-----------------------------------
Role: Two-phase scanner with hard filters and ranking.

Class: TwoPhaseScanner
  __init__(filter_phase, ranking_weights, ticker_list):
    - Configures hard filter thresholds
    - Sets ranking weight configuration

  run_scan(scan_date) -> DataFrame:

    PHASE 1 - Hard Filtering:
      1. Load short interest data for target tickers
      2. For each ticker in parallel:
         a. Fetch 20 days historical data
         b. Calculate ATR (14-period EMA)
         c. If ATR < min_atr: SKIP
         d. Fetch overnight volumes (specific time windows)
         e. Calculate current price and gap
         f. If price < min_price: SKIP
         g. If gap < min_gap_percent: SKIP
         h. Get short interest from cache
      3. Return passing tickers with all metrics

    PHASE 2 - Ranking:
      1. Calculate relative metrics:
         - relative_overnight_volume = current_overnight / prior_overnight
         - relative_volume = current_overnight / prior_regular_hours
      2. Normalize each metric to 0-100 scale
      3. Calculate weighted ranking score
      4. Sort by: current_overnight_volume DESC, ranking_score DESC
      5. Add rank column

  Output Columns:
    rank, ticker, current_price, gap_percent, current_overnight_volume,
    prior_overnight_volume, relative_overnight_volume, relative_volume,
    short_interest, days_to_cover, ranking_score, atr, prior_close,
    scan_date, scan_time

Request this file for: Two-phase logic, ranking calculations, filter sequence.

--------------------------------------------------------------------------------

FILE: outputs/excel_exporter.py
-------------------------------
Role: Excel output via xlwings with named ranges.

Target Workbook: epoch_v1.xlsm
Worksheet: market_overview
Named Ranges:
  - scanner_results_headers: B3:Q3 (column headers)
  - scanner_results: B4:Q23 (data, max 20 rows)

Class: ExcelExporter
  export_to_epoch(df, excel_path) -> bool:
    - Clears existing data in B4:Q23
    - Writes up to 20 rows of scan results
    - Data-only export (preserves formatting)
    - Auto-creates named ranges if missing
    - Converts percentages to decimal format

  get_scan_summary(excel_path) -> DataFrame:
    - Reads existing scan data from workbook

Export Columns (16 fields):
  B: rank
  C: ticker
  D: ticker_id
  E: current_price
  F: gap_percent
  G: current_overnight_volume
  H: prior_overnight_volume
  I: relative_overnight_volume
  J: relative_volume
  K: short_interest
  L: days_to_cover
  M: ranking_score
  N: atr
  O: prior_close
  P: scan_date
  Q: scan_time

Request this file for: Excel output issues, named range configuration, column mapping.

--------------------------------------------------------------------------------

FILE: outputs/exporters.py
--------------------------
Role: Multiple output format support.

Classes:
  CSVExporter:
    - Exports to timestamped CSV files
    - Default path: output/scans/

  MarkdownExporter:
    - Generates markdown reports with tables
    - Highlights top 3 stocks (medal emojis)
    - Includes filter criteria and summary

  SupabaseExporter:
    - Pushes results to Supabase database
    - Batch inserts (100 records per batch)
    - Updates active flag for versioning

Request this file for: Adding new output formats, export issues.

--------------------------------------------------------------------------------

FILE: outputs/formatters.py
---------------------------
Role: Console output formatting.

Class: ReportFormatter
  format_console_output(df) -> str:
    - Tabular display for terminal

  format_score_explanation(row) -> str:
    - Score component breakdown

Request this file for: Console display formatting.

--------------------------------------------------------------------------------

FILE: utils/market_timing.py
----------------------------
Role: Market hours and trading day utilities.

Uses: pandas-market-calendars for NYSE schedule

Functions:
  is_market_open(datetime) -> bool:
    - Check if market is currently trading

  is_premarket(datetime) -> bool:
    - Check if in premarket session (4:00 AM - 9:30 AM ET)

  get_next_market_open() -> datetime:
    - Next market open time

  get_previous_trading_day(date) -> date:
    - Last trading day (handles holidays/weekends)

Request this file for: Market timing issues, holiday handling.

--------------------------------------------------------------------------------

FILE: utils/validation.py
-------------------------
Role: Data validation utilities.

Class: DataValidator
  validate_ohlcv(df) -> tuple[bool, list[str]]:
    - Validates daily bars (H >= L, non-negative, no nulls)
    - Returns validation status and error list

  validate_scan_data(df) -> tuple[bool, list[str]]:
    - Validates scan results (required columns, data types)
    - Returns validation status and error list

Request this file for: Data quality issues, adding validation rules.

--------------------------------------------------------------------------------

FILE: scripts/run_scan.py
-------------------------
Role: Script to run PremarketScanner with filter profiles.

Features:
  - Multiple output formats: console, CSV, Markdown, Supabase
  - Filter profile selection (strict, relaxed, momentum, etc.)
  - Configurable top N results
  - Parallel data fetching

Request this file for: Running premarket scans, output format options.

--------------------------------------------------------------------------------

FILE: scripts/run_two_phase_scan.py
-----------------------------------
Role: Script to run TwoPhaseScanner with detailed output.

Features:
  - Detailed console output during execution
  - Phase-by-phase progress reporting
  - CSV export with full metric breakdown

Request this file for: Running two-phase scans, debugging scan execution.

--------------------------------------------------------------------------------

FILE: scripts/update_tickers.py
-------------------------------
Role: Ticker list maintenance script.

Features:
  - Updates S&P 500 list from Wikipedia
  - Compares current vs. new lists
  - Shows additions/removals before applying

Request this file for: Keeping ticker lists current.

================================================================================
EXCEL OUTPUT STRUCTURE
================================================================================

Worksheet: market_overview
Named Range: scanner_results (B4:Q23)
Max Rows: 20

Column Layout:
  B: Rank (1-20)
  C: Ticker symbol
  D: Ticker ID (AAPL.081125 format)
  E: Current price
  F: Gap percent (decimal: 0.05 = 5%)
  G: Current overnight volume
  H: Prior overnight volume
  I: Relative overnight volume (ratio)
  J: Relative volume (ratio)
  K: Short interest percent (decimal)
  L: Days to cover
  M: Ranking score (0-100)
  N: ATR (dollars)
  O: Prior close
  P: Scan date (YYYY-MM-DD)
  Q: Scan time (HH:MM)

================================================================================
KEY CONCEPTS
================================================================================

TWO-PHASE FILTERING
- Phase 1 (Hard Filters): Binary pass/fail on ATR, price, gap
- Phase 2 (Ranking): Score remaining candidates on multiple metrics
- Rationale: Quickly eliminate non-candidates, then rank viable ones

ATR CALCULATION
- 14-period Exponential Moving Average of True Range
- True Range = max(H-L, |H-prior_close|, |L-prior_close|)
- Used as volatility filter and for ATR% calculation

OVERNIGHT VOLUME WINDOWS
- Current Overnight: Prior day 4:01 PM to current day 8:00 AM ET
- Prior Overnight: Same window, one day earlier
- Prior Regular: Prior day 9:30 AM to 4:00 PM ET
- Relative metrics compare current activity to historical norms

GAP CALCULATION
- Gap % = (Current Price - Prior Close) / Prior Close * 100
- Calculated from overnight session close vs prior day close
- Absolute value used for filtering (direction-agnostic by default)

RANKING SCORE
- Normalized 0-100 scale for each metric
- Weighted combination based on RankingWeights configuration
- Default weights equally balance volume, relative volume, gap, and short interest

TICKER ID FORMAT
- Format: TICKER.MMDDYY (e.g., AAPL.081125)
- Unique identifier combining ticker and scan date
- Used for tracking and database integration

================================================================================
DEPENDENCIES
================================================================================

Python Packages:
  - pandas >= 2.0.0, numpy >= 1.24.0 (data handling)
  - polygon-api-client >= 1.12.0 (market data API)
  - aiohttp >= 3.9.0 (async HTTP)
  - xlwings >= 0.30.0 (Excel integration)
  - python-dotenv >= 1.0.0 (configuration)
  - pytz >= 2023.3 (timezone handling)
  - pandas-market-calendars >= 4.3.0 (trading calendar)
  - requests, beautifulsoup4, lxml (web scraping for ticker updates)
  - pyarrow (data processing)
  - supabase >= 2.0.0 (optional database export)

External:
  - Polygon.io API (requires valid API key)
  - Excel workbook: C:\XIIITradingSystems\Epoch\epoch_v1.xlsm
  - Worksheet 'market_overview' with named range 'scanner_results'
  - 09_data_server module for cached data fetching

================================================================================
COMMON MODIFICATION SCENARIOS
================================================================================

Change hard filter thresholds:
  -> filters/two_phase_filter.py: FilterPhase dataclass defaults
  -> scan_runner.py: CLI argument defaults

Adjust ranking weights:
  -> filters/two_phase_filter.py: RankingWeights dataclass
  -> scanners/two_phase_scanner.py: Phase 2 scoring logic

Add new ticker list:
  -> data/ticker_manager.py: Add to TickerList enum
  -> data/ticker_manager.py: Add fetch logic in get_tickers()

Change Excel output location:
  -> scan_runner.py: --excel-path default
  -> outputs/excel_exporter.py: Named range definitions

Modify overnight time windows:
  -> data/overnight_fetcher.py: Time window constants

Add new filter criteria:
  -> filters/criteria.py: Add parameter to FilterCriteria
  -> filters/premarket_filter.py: Add filter logic

Add new ranking metric:
  -> filters/two_phase_filter.py: Add to RankingWeights
  -> scanners/two_phase_scanner.py: Add calculation in Phase 2

Change ATR period:
  -> scanners/premarket_scanner.py: _calculate_atr() method
  -> scanners/two_phase_scanner.py: ATR calculation logic

================================================================================
USAGE EXAMPLES
================================================================================

Run default scan (S&P 500, $2 ATR, $10 min price, 2% gap):
  python scan_runner.py

Run scan for specific date:
  python scan_runner.py --date 2025-01-15

Run with NASDAQ 100 and stricter filters:
  python scan_runner.py --list NASDAQ100 --min-atr 3.00 --min-gap 3.0

Read existing scan summary:
  python scan_runner.py --summary

Update ticker lists:
  python scripts/update_tickers.py

================================================================================
END OF DOCUMENTATION
================================================================================

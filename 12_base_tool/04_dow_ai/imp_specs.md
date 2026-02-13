DOW AI Trading Assistant - Implementation Specification
Overview
Purpose: Claude-integrated terminal tool for entry/exit trade analysis
Location: C:\XIIITradingSystems\Epoch\04_dow_ai\
Interface: Standalone terminal application (separate from IDE)

Model Definitions
ModelTypeZoneTrading LogicEPCH_01ContinuationPrimaryPrice moves through zone in trend directionEPCH_02ReversalPrimaryPrice reverses at zone (mean reversion)EPCH_03ContinuationSecondaryPrice moves through secondary zone with trendEPCH_04ReversalSecondaryPrice reverses at secondary zone

CLI Commands
bash# Entry Analysis (Live)
dow entry TSLA long EPCH_01

# Entry Analysis (Historical Backtest)
dow entry TSLA long EPCH_01 --datetime "2024-12-03 10:30"

# Exit Analysis (Live) - "sell" indicates closing a long position
dow exit TSLA sell EPCH_01

# Exit Analysis (Historical Backtest)
dow exit TSLA sell EPCH_01 --datetime "2024-12-03 14:45"

# Exit Analysis - "cover" indicates closing a short position
dow exit TSLA cover EPCH_02
```

---

### Directory Structure
```
C:\XIIITradingSystems\Epoch\
├── 04_dow_ai/
│   ├── __init__.py
│   ├── main.py                      # Entry point for standalone app
│   ├── cli.py                       # Click/Typer CLI definition
│   ├── config.py                    # API keys, paths, thresholds
│   ├── launcher.bat                 # Windows batch launcher
│   ├── launcher.ps1                 # PowerShell launcher
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── polygon_fetcher.py       # Live/historical bar data
│   │   ├── epoch_reader.py          # Read zones, bar_data from Excel
│   │   └── data_models.py           # Pydantic models for data structures
│   │
│   ├── calculations/
│   │   ├── __init__.py
│   │   ├── market_structure.py      # Multi-TF BOS/ChoCH calculator
│   │   ├── volume_analysis.py       # Delta, ROC, CVD
│   │   └── patterns.py              # Candlestick pattern detection
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── aggregator.py            # Compile all signals
│   │   ├── claude_client.py         # Anthropic API integration
│   │   └── prompts/
│   │       ├── __init__.py
│   │       ├── entry_prompt.py      # Entry analysis prompt template
│   │       └── exit_prompt.py       # Exit analysis prompt template
│   │
│   └── output/
│       ├── __init__.py
│       └── terminal.py              # Rich library formatting
│
├── 02_zone_system/                  # Existing Epoch modules
│   └── ...
│
└── epoch_v1.xlsm                    # Excel workbook (xlwings)

File Specifications
config.py
python"""
DOW AI Configuration
Central configuration for all settings, API keys, and paths.
"""
from pathlib import Path

# =============================================================================
# PATHS
# =============================================================================
BASE_DIR = Path(r"C:\XIIITradingSystems\Epoch")
EXCEL_FILEPATH = BASE_DIR / "epoch_v1.xlsm"
DOW_DIR = BASE_DIR / "04_dow_ai"

# =============================================================================
# API KEYS
# =============================================================================
POLYGON_API_KEY = "your_polygon_api_key_here"
ANTHROPIC_API_KEY = "your_anthropic_api_key_here"

# =============================================================================
# POLYGON SETTINGS
# =============================================================================
POLYGON_BASE_URL = "https://api.polygon.io"
API_RATE_LIMIT_DELAY = 0.25  # seconds between calls

# Timeframe configurations for market structure
TIMEFRAMES = {
    'M5': {'multiplier': 5, 'timespan': 'minute', 'bars_needed': 100},
    'M15': {'multiplier': 15, 'timespan': 'minute', 'bars_needed': 100},
    'H1': {'multiplier': 1, 'timespan': 'hour', 'bars_needed': 100},
    'H4': {'multiplier': 4, 'timespan': 'hour', 'bars_needed': 50},
}

# Lookback periods for data fetching (in days)
DATA_LOOKBACK = {
    'M1': 2,
    'M5': 5,
    'M15': 10,
    'H1': 30,
    'H4': 60,
}

# =============================================================================
# MARKET STRUCTURE SETTINGS
# =============================================================================
FRACTAL_LENGTH = 5  # Bars each side for fractal detection

# =============================================================================
# VOLUME ANALYSIS SETTINGS
# =============================================================================
VOLUME_DELTA_BARS = 5        # Rolling window for delta
VOLUME_ROC_BASELINE = 20     # Bars for average volume baseline
CVD_WINDOW = 15              # Bars for CVD trend analysis

# =============================================================================
# CLAUDE SETTINGS
# =============================================================================
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # Fast for live trading
# CLAUDE_MODEL = "claude-opus-4-20250514"  # Use for deeper analysis if needed
CLAUDE_MAX_TOKENS = 1500

# =============================================================================
# EXCEL CELL MAPPINGS (from Epoch system)
# =============================================================================
EXCEL_WORKSHEETS = {
    'market_overview': 'market_overview',
    'bar_data': 'bar_data',
    'zone_results': 'zone_results',
    'analysis': 'Analysis',
}

# zone_results columns
ZONE_RESULTS_COLUMNS = {
    'ticker_id': 'A',
    'ticker': 'B',
    'date': 'C',
    'price': 'D',
    'direction': 'E',
    'zone_id': 'F',
    'hvn_poc': 'G',
    'zone_high': 'H',
    'zone_low': 'I',
    'overlaps': 'J',
    'score': 'K',
    'rank': 'L',
    'confluences': 'M',
    'epch_bull': 'N',
    'epch_bear': 'O',
    'epch_bull_price': 'P',
    'epch_bear_price': 'Q',
    'epch_bull_target': 'R',
    'epch_bear_target': 'S',
}

# bar_data references
BAR_DATA_REFS = {
    'ticker_structure': {'start_row': 4, 'end_row': 13},
    'time_hvn': {'start_row': 59, 'end_row': 68},
    'on_options_metrics': {'start_row': 73, 'end_row': 82},
    'camarilla': {'start_row': 86, 'end_row': 95},
}

# Analysis worksheet references
ANALYSIS_REFS = {
    'primary': {'start_row': 31, 'end_row': 40, 'start_col': 'B', 'end_col': 'K'},
    'secondary': {'start_row': 31, 'end_row': 40, 'start_col': 'M', 'end_col': 'V'},
}

# =============================================================================
# MODEL DEFINITIONS
# =============================================================================
MODELS = {
    'EPCH_01': {
        'name': 'Primary Continuation',
        'zone_type': 'primary',
        'trade_type': 'continuation',
        'description': 'Continuation through primary zone in trend direction'
    },
    'EPCH_02': {
        'name': 'Primary Reversal',
        'zone_type': 'primary',
        'trade_type': 'reversal',
        'description': 'Reversal/mean reversion at primary zone'
    },
    'EPCH_03': {
        'name': 'Secondary Continuation',
        'zone_type': 'secondary',
        'trade_type': 'continuation',
        'description': 'Continuation through secondary zone with trend'
    },
    'EPCH_04': {
        'name': 'Secondary Reversal',
        'zone_type': 'secondary',
        'trade_type': 'reversal',
        'description': 'Reversal at secondary zone'
    },
}

# =============================================================================
# TIMEZONE
# =============================================================================
TIMEZONE = 'America/New_York'  # Eastern Time

data/data_models.py
python"""
Pydantic data models for structured data throughout DOW.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Literal
from datetime import datetime

class BarData(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class MarketStructureResult(BaseModel):
    timeframe: str
    direction: Literal['BULL', 'BEAR', 'NEUTRAL']
    strong_level: Optional[float]
    weak_level: Optional[float]
    last_break: Optional[Literal['BOS', 'ChoCH']]
    last_break_price: Optional[float]

class VolumeAnalysis(BaseModel):
    delta_5bar: float
    delta_signal: Literal['Bullish', 'Bearish', 'Neutral']
    roc_percent: float
    roc_signal: Literal['Above Avg', 'Below Avg', 'Average']
    cvd_trend: Literal['Rising', 'Falling', 'Flat']

class CandlestickPattern(BaseModel):
    timeframe: str
    pattern: str
    price: float
    bars_ago: int

class ZoneContext(BaseModel):
    zone_id: str
    rank: str
    zone_high: float
    zone_low: float
    hvn_poc: float
    score: float
    confluences: str
    target: Optional[float]
    target_rr: Optional[float]

class AnalysisRequest(BaseModel):
    ticker: str
    mode: Literal['entry', 'exit']
    direction: Literal['long', 'short', 'sell', 'cover']
    model: str
    analysis_datetime: Optional[datetime] = None  # None = live

class AnalysisResult(BaseModel):
    request: AnalysisRequest
    current_price: float
    zone_context: Optional[ZoneContext]
    market_structure: Dict[str, MarketStructureResult]
    volume_analysis: VolumeAnalysis
    patterns: List[CandlestickPattern]
    claude_response: str
    timestamp: datetime

data/polygon_fetcher.py
python"""
Polygon.io data fetcher for live and historical bar data.
Supports backtesting mode with specific datetime.
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict
import time
import pytz

from config import (
    POLYGON_API_KEY, 
    POLYGON_BASE_URL, 
    API_RATE_LIMIT_DELAY,
    TIMEFRAMES,
    DATA_LOOKBACK,
    TIMEZONE
)

class PolygonFetcher:
    """Fetches bar data from Polygon.io API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or POLYGON_API_KEY
        self.base_url = POLYGON_BASE_URL
        self.tz = pytz.timezone(TIMEZONE)
        self._last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        elapsed = time.time() - self._last_request_time
        if elapsed < API_RATE_LIMIT_DELAY:
            time.sleep(API_RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()
    
    def _make_request(self, url: str, params: dict) -> Optional[dict]:
        """Make API request with retry logic."""
        self._rate_limit()
        params['apiKey'] = self.api_key
        
        for attempt in range(3):
            try:
                response = requests.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    print(f"API Error: {response.status_code} - {response.text}")
                    return None
            except Exception as e:
                print(f"Request error: {e}")
                if attempt < 2:
                    time.sleep(1)
        return None
    
    def fetch_bars(
        self, 
        ticker: str, 
        timeframe: str,
        end_datetime: Optional[datetime] = None,
        bars_needed: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        Fetch bar data for a ticker and timeframe.
        
        Args:
            ticker: Stock symbol (e.g., 'TSLA')
            timeframe: One of 'M1', 'M5', 'M15', 'H1', 'H4'
            end_datetime: End time for data (None = now)
            bars_needed: Number of bars to fetch
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        # Get timeframe config
        if timeframe == 'M1':
            multiplier = 1
            timespan = 'minute'
        else:
            tf_config = TIMEFRAMES.get(timeframe)
            if not tf_config:
                print(f"Unknown timeframe: {timeframe}")
                return None
            multiplier = tf_config['multiplier']
            timespan = tf_config['timespan']
        
        # Calculate date range
        if end_datetime is None:
            end_datetime = datetime.now(self.tz)
        
        lookback_days = DATA_LOOKBACK.get(timeframe, 30)
        start_datetime = end_datetime - timedelta(days=lookback_days)
        
        # Format dates for API
        from_date = start_datetime.strftime('%Y-%m-%d')
        to_date = end_datetime.strftime('%Y-%m-%d')
        
        # Build URL
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        
        params = {
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }
        
        data = self._make_request(url, params)
        if not data or 'results' not in data:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data['results'])
        df = df.rename(columns={
            't': 'timestamp',
            'o': 'open',
            'h': 'high',
            'l': 'low',
            'c': 'close',
            'v': 'volume'
        })
        
        # Convert timestamp from milliseconds to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df['timestamp'] = df['timestamp'].dt.tz_convert(TIMEZONE)
        
        # Filter to bars before end_datetime (for backtesting)
        if end_datetime:
            end_dt_aware = end_datetime if end_datetime.tzinfo else self.tz.localize(end_datetime)
            df = df[df['timestamp'] <= end_dt_aware]
        
        # Return most recent bars_needed
        return df.tail(bars_needed).reset_index(drop=True)
    
    def fetch_multi_timeframe(
        self, 
        ticker: str, 
        timeframes: list = None,
        end_datetime: Optional[datetime] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple timeframes.
        
        Returns:
            Dict mapping timeframe -> DataFrame
        """
        if timeframes is None:
            timeframes = ['M1', 'M5', 'M15', 'H1', 'H4']
        
        results = {}
        for tf in timeframes:
            df = self.fetch_bars(ticker, tf, end_datetime)
            if df is not None and not df.empty:
                results[tf] = df
        
        return results
    
    def get_current_price(
        self, 
        ticker: str, 
        at_datetime: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Get the current (or historical) price.
        
        For live: returns last M1 close
        For backtest: returns M1 close at specified datetime
        """
        df = self.fetch_bars(ticker, 'M1', at_datetime, bars_needed=5)
        if df is not None and not df.empty:
            return float(df.iloc[-1]['close'])
        return None

data/epoch_reader.py
python"""
Reader for Epoch Excel workbook data.
Extracts zones, bar_data, and analysis info using xlwings.
"""
import xlwings as xw
import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime

from config import (
    EXCEL_FILEPATH,
    EXCEL_WORKSHEETS,
    ZONE_RESULTS_COLUMNS,
    BAR_DATA_REFS,
    ANALYSIS_REFS
)

class EpochReader:
    """Reads data from the Epoch Excel workbook."""
    
    def __init__(self, filepath: str = None):
        self.filepath = filepath or str(EXCEL_FILEPATH)
        self._wb = None
    
    def connect(self) -> bool:
        """Connect to open Excel workbook."""
        try:
            self._wb = xw.Book(self.filepath)
            return True
        except Exception as e:
            print(f"Error connecting to Excel: {e}")
            print("Ensure epoch_v1.xlsm is open in Excel.")
            return False
    
    def _get_worksheet(self, name: str):
        """Get worksheet by name."""
        ws_name = EXCEL_WORKSHEETS.get(name, name)
        return self._wb.sheets[ws_name]
    
    def read_zone_results(self, ticker: str = None) -> pd.DataFrame:
        """
        Read filtered zones from zone_results worksheet.
        
        Args:
            ticker: Optional filter by ticker symbol
        
        Returns:
            DataFrame with all zone data
        """
        ws = self._get_worksheet('zone_results')
        
        # Find last row with data
        last_row = 2
        while ws.range(f'A{last_row}').value is not None:
            last_row += 1
            if last_row > 500:
                break
        last_row -= 1
        
        if last_row < 2:
            return pd.DataFrame()
        
        # Read data range
        data_range = ws.range(f'A2:S{last_row}').value
        
        # Handle single row
        if last_row == 2:
            data_range = [data_range]
        
        # Build DataFrame
        columns = [
            'ticker_id', 'ticker', 'date', 'price', 'direction',
            'zone_id', 'hvn_poc', 'zone_high', 'zone_low', 'overlaps',
            'score', 'rank', 'confluences', 'epch_bull', 'epch_bear',
            'epch_bull_price', 'epch_bear_price', 'epch_bull_target', 'epch_bear_target'
        ]
        
        df = pd.DataFrame(data_range, columns=columns)
        
        # Clean data types
        numeric_cols = ['price', 'hvn_poc', 'zone_high', 'zone_low', 'overlaps', 
                        'score', 'epch_bull_price', 'epch_bear_price',
                        'epch_bull_target', 'epch_bear_target']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Filter by ticker if specified
        if ticker:
            df = df[df['ticker'].str.upper() == ticker.upper()]
        
        return df
    
    def get_primary_zone(self, ticker: str, direction: str) -> Optional[Dict]:
        """
        Get the primary zone for a ticker and direction.
        
        Args:
            ticker: Stock symbol
            direction: 'long' or 'short'
        
        Returns:
            Dict with zone info or None
        """
        df = self.read_zone_results(ticker)
        if df.empty:
            return None
        
        # Primary zone is marked in epch_bull (long) or epch_bear (short)
        if direction.lower() in ['long', 'buy']:
            zone_df = df[df['epch_bull'] == 'X']
            target_col = 'epch_bull_target'
        else:
            zone_df = df[df['epch_bear'] == 'X']
            target_col = 'epch_bear_target'
        
        if zone_df.empty:
            return None
        
        zone = zone_df.iloc[0]
        return {
            'zone_id': zone['zone_id'],
            'rank': zone['rank'],
            'zone_high': zone['zone_high'],
            'zone_low': zone['zone_low'],
            'hvn_poc': zone['hvn_poc'],
            'score': zone['score'],
            'confluences': zone['confluences'],
            'target': zone[target_col],
            'direction': direction
        }
    
    def get_secondary_zone(self, ticker: str, direction: str) -> Optional[Dict]:
        """
        Get the secondary zone for a ticker and direction.
        Secondary is the opposite direction zone used for counter-trend.
        """
        # Secondary uses opposite direction
        opp_direction = 'short' if direction.lower() in ['long', 'buy'] else 'long'
        return self.get_primary_zone(ticker, opp_direction)
    
    def read_hvn_pocs(self, ticker: str) -> List[float]:
        """
        Read HVN POC levels from bar_data (time_hvn section).
        
        Returns:
            List of up to 10 POC prices
        """
        ws = self._get_worksheet('bar_data')
        
        # Find ticker row in time_hvn section (rows 59-68)
        for row in range(59, 69):
            cell_ticker = ws.range(f'C{row}').value
            if cell_ticker and cell_ticker.upper() == ticker.upper():
                # Read POCs from columns F-O
                pocs = []
                for col in 'FGHIJKLMNO':
                    val = ws.range(f'{col}{row}').value
                    if val is not None:
                        pocs.append(float(val))
                return pocs
        
        return []
    
    def read_camarilla_levels(self, ticker: str) -> Dict[str, float]:
        """
        Read Camarilla pivot levels from bar_data.
        
        Returns:
            Dict with d1_s6, d1_s4, d1_s3, d1_r3, d1_r4, d1_r6, etc.
        """
        ws = self._get_worksheet('bar_data')
        
        # Find ticker row in add_metrics section (rows 86-95)
        for row in range(86, 96):
            cell_ticker = ws.range(f'C{row}').value
            if cell_ticker and cell_ticker.upper() == ticker.upper():
                return {
                    'd1_s6': ws.range(f'E{row}').value,
                    'd1_s4': ws.range(f'F{row}').value,
                    'd1_s3': ws.range(f'G{row}').value,
                    'd1_r3': ws.range(f'H{row}').value,
                    'd1_r4': ws.range(f'I{row}').value,
                    'd1_r6': ws.range(f'J{row}').value,
                    'w1_s6': ws.range(f'K{row}').value,
                    'w1_s4': ws.range(f'L{row}').value,
                    'w1_s3': ws.range(f'M{row}').value,
                    'w1_r3': ws.range(f'N{row}').value,
                    'w1_r4': ws.range(f'O{row}').value,
                    'w1_r6': ws.range(f'P{row}').value,
                }
        
        return {}
    
    def read_atr(self, ticker: str) -> Optional[float]:
        """Read D1 ATR from bar_data on_options_metrics section."""
        ws = self._get_worksheet('bar_data')
        
        for row in range(73, 83):
            cell_ticker = ws.range(f'C{row}').value
            if cell_ticker and cell_ticker.upper() == ticker.upper():
                return ws.range(f'T{row}').value
        
        return None
    
    def read_analysis_setups(self, ticker: str) -> Dict:
        """
        Read primary and secondary setups from Analysis worksheet.
        
        Returns:
            Dict with 'primary' and 'secondary' setup info
        """
        ws = self._get_worksheet('analysis')
        
        result = {'primary': None, 'secondary': None}
        
        # Search primary section (B31:K40)
        for row in range(31, 41):
            cell_ticker = ws.range(f'B{row}').value
            if cell_ticker and cell_ticker.upper() == ticker.upper():
                result['primary'] = {
                    'ticker': ws.range(f'B{row}').value,
                    'direction': ws.range(f'C{row}').value,
                    'ticker_id': ws.range(f'D{row}').value,
                    'zone_id': ws.range(f'E{row}').value,
                    'hvn_poc': ws.range(f'F{row}').value,
                    'zone_high': ws.range(f'G{row}').value,
                    'zone_low': ws.range(f'H{row}').value,
                    'target_id': ws.range(f'I{row}').value,
                    'target': ws.range(f'J{row}').value,
                    'r_r': ws.range(f'K{row}').value,
                }
                break
        
        # Search secondary section (M31:V40)
        for row in range(31, 41):
            cell_ticker = ws.range(f'M{row}').value
            if cell_ticker and cell_ticker.upper() == ticker.upper():
                result['secondary'] = {
                    'ticker': ws.range(f'M{row}').value,
                    'direction': ws.range(f'N{row}').value,
                    'ticker_id': ws.range(f'O{row}').value,
                    'zone_id': ws.range(f'P{row}').value,
                    'hvn_poc': ws.range(f'Q{row}').value,
                    'zone_high': ws.range(f'R{row}').value,
                    'zone_low': ws.range(f'S{row}').value,
                    'target_id': ws.range(f'T{row}').value,
                    'target': ws.range(f'U{row}').value,
                    'r_r': ws.range(f'V{row}').value,
                }
                break
        
        return result

calculations/market_structure.py
python"""
Market Structure Calculator for multiple timeframes.
Calculates BOS/ChoCH, strong/weak levels using fractal-based analysis.
Adapted from Epoch market_structure_calculator.py for real-time use.
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from config import FRACTAL_LENGTH

@dataclass
class StructureResult:
    direction: str  # 'BULL', 'BEAR', 'NEUTRAL'
    strong_level: Optional[float]
    weak_level: Optional[float]
    last_break: Optional[str]  # 'BOS' or 'ChoCH'
    last_break_price: Optional[float]

class MarketStructureCalculator:
    """
    Calculates market structure (BOS/ChoCH) for any timeframe.
    """
    
    def __init__(self, fractal_length: int = None):
        self.fractal_length = fractal_length or FRACTAL_LENGTH
    
    def _detect_fractals(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        Detect bullish and bearish fractals.
        
        Bullish fractal: Local LOW (swing low)
        Bearish fractal: Local HIGH (swing high)
        """
        p = self.fractal_length // 2
        n = len(df)
        
        bullish_fractals = pd.Series([False] * n, index=df.index)
        bearish_fractals = pd.Series([False] * n, index=df.index)
        
        for i in range(p, n - p):
            # Check for bullish fractal (swing low)
            is_bullish = True
            current_low = df.iloc[i]['low']
            for j in range(1, p + 1):
                if df.iloc[i - j]['low'] <= current_low or df.iloc[i + j]['low'] <= current_low:
                    is_bullish = False
                    break
            bullish_fractals.iloc[i] = is_bullish
            
            # Check for bearish fractal (swing high)
            is_bearish = True
            current_high = df.iloc[i]['high']
            for j in range(1, p + 1):
                if df.iloc[i - j]['high'] >= current_high or df.iloc[i + j]['high'] >= current_high:
                    is_bearish = False
                    break
            bearish_fractals.iloc[i] = is_bearish
        
        return bullish_fractals, bearish_fractals
    
    def calculate(self, df: pd.DataFrame) -> StructureResult:
        """
        Calculate market structure from bar data.
        
        Args:
            df: DataFrame with columns: open, high, low, close, volume
        
        Returns:
            StructureResult with direction, levels, and last break info
        """
        if df is None or len(df) < self.fractal_length + 5:
            return StructureResult(
                direction='NEUTRAL',
                strong_level=None,
                weak_level=None,
                last_break=None,
                last_break_price=None
            )
        
        df = df.copy().reset_index(drop=True)
        
        # Detect fractals
        bullish_fractals, bearish_fractals = self._detect_fractals(df)
        
        # Track structure
        structure = 0  # 1 = Bull, -1 = Bear, 0 = Neutral
        upper_fractal = None
        lower_fractal = None
        last_break = None
        last_break_price = None
        bull_weak_high = None
        bear_weak_low = None
        
        for i in range(len(df)):
            close = df.iloc[i]['close']
            high = df.iloc[i]['high']
            low = df.iloc[i]['low']
            
            # Update fractal levels
            if bearish_fractals.iloc[i]:
                upper_fractal = df.iloc[i]['high']
            if bullish_fractals.iloc[i]:
                lower_fractal = df.iloc[i]['low']
            
            # Check for structure breaks
            if upper_fractal is not None and close > upper_fractal:
                if structure == 1:
                    last_break = 'BOS'
                else:
                    last_break = 'ChoCH'
                last_break_price = upper_fractal
                structure = 1
                bull_weak_high = high
                upper_fractal = None
            
            if lower_fractal is not None and close < lower_fractal:
                if structure == -1:
                    last_break = 'BOS'
                else:
                    last_break = 'ChoCH'
                last_break_price = lower_fractal
                structure = -1
                bear_weak_low = low
                lower_fractal = None
            
            # Track weak levels (continuation targets)
            if structure == 1 and high > (bull_weak_high or 0):
                bull_weak_high = high
            if structure == -1 and low < (bear_weak_low or float('inf')):
                bear_weak_low = low
        
        # Determine final values
        if structure == 1:
            direction = 'BULL'
            strong_level = lower_fractal  # Support (if broken = ChoCH)
            weak_level = bull_weak_high   # Continuation target
        elif structure == -1:
            direction = 'BEAR'
            strong_level = upper_fractal  # Resistance (if broken = ChoCH)
            weak_level = bear_weak_low    # Continuation target
        else:
            direction = 'NEUTRAL'
            strong_level = None
            weak_level = None
        
        return StructureResult(
            direction=direction,
            strong_level=strong_level,
            weak_level=weak_level,
            last_break=last_break,
            last_break_price=last_break_price
        )
    
    def calculate_multi_timeframe(
        self, 
        data: Dict[str, pd.DataFrame]
    ) -> Dict[str, StructureResult]:
        """
        Calculate structure for multiple timeframes.
        
        Args:
            data: Dict mapping timeframe -> DataFrame
        
        Returns:
            Dict mapping timeframe -> StructureResult
        """
        results = {}
        for tf, df in data.items():
            results[tf] = self.calculate(df)
        return results

calculations/volume_analysis.py
python"""
Volume Analysis: Delta, Rate of Change, Cumulative Volume Delta.
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass

from config import VOLUME_DELTA_BARS, VOLUME_ROC_BASELINE, CVD_WINDOW

@dataclass
class VolumeResult:
    delta_5bar: float
    delta_signal: str  # 'Bullish', 'Bearish', 'Neutral'
    roc_percent: float
    roc_signal: str    # 'Above Avg', 'Below Avg', 'Average'
    cvd_trend: str     # 'Rising', 'Falling', 'Flat'
    cvd_values: list   # Last N CVD values for context

class VolumeAnalyzer:
    """
    Analyzes volume metrics for trading signals.
    """
    
    def __init__(
        self, 
        delta_bars: int = None,
        roc_baseline: int = None,
        cvd_window: int = None
    ):
        self.delta_bars = delta_bars or VOLUME_DELTA_BARS
        self.roc_baseline = roc_baseline or VOLUME_ROC_BASELINE
        self.cvd_window = cvd_window or CVD_WINDOW
    
    def calculate_bar_delta(self, row: pd.Series) -> float:
        """
        Calculate volume delta for a single bar using close position.
        
        Green bar (close > open): positive delta
        Red bar (close < open): negative delta
        Weighted by close position within range.
        """
        open_price = row['open']
        high = row['high']
        low = row['low']
        close = row['close']
        volume = row['volume']
        
        # Avoid division by zero
        bar_range = high - low
        if bar_range == 0:
            return volume if close >= open_price else -volume
        
        # Position of close within bar (0 = at low, 1 = at high)
        position = (close - low) / bar_range
        
        # Convert to -1 to +1 range
        delta_multiplier = (2 * position) - 1
        
        return volume * delta_multiplier
    
    def calculate_rolling_delta(self, df: pd.DataFrame, bars: int = None) -> float:
        """
        Calculate rolling volume delta over N bars.
        """
        bars = bars or self.delta_bars
        recent = df.tail(bars)
        
        total_delta = sum(self.calculate_bar_delta(row) for _, row in recent.iterrows())
        return total_delta
    
    def calculate_volume_roc(self, df: pd.DataFrame) -> Tuple[float, float]:
        """
        Calculate volume rate of change vs baseline average.
        
        Returns:
            (roc_percent, baseline_avg)
        """
        if len(df) < self.roc_baseline + 1:
            return 0.0, 0.0
        
        # Current bar volume
        current_volume = df.iloc[-1]['volume']
        
        # Baseline average (excluding current bar)
        baseline = df.iloc[-(self.roc_baseline + 1):-1]['volume'].mean()
        
        if baseline == 0:
            return 0.0, 0.0
        
        roc = ((current_volume - baseline) / baseline) * 100
        return roc, baseline
    
    def calculate_cvd(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate Cumulative Volume Delta series.
        """
        deltas = df.apply(self.calculate_bar_delta, axis=1)
        return deltas.cumsum()
    
    def determine_cvd_trend(self, df: pd.DataFrame) -> str:
        """
        Determine CVD trend over the window period.
        Uses linear regression slope.
        """
        cvd = self.calculate_cvd(df)
        recent_cvd = cvd.tail(self.cvd_window).values
        
        if len(recent_cvd) < 3:
            return 'Flat'
        
        # Simple slope calculation
        x = np.arange(len(recent_cvd))
        slope = np.polyfit(x, recent_cvd, 1)[0]
        
        # Normalize by range
        cvd_range = recent_cvd.max() - recent_cvd.min()
        if cvd_range == 0:
            return 'Flat'
        
        normalized_slope = slope / cvd_range * len(recent_cvd)
        
        if normalized_slope > 0.1:
            return 'Rising'
        elif normalized_slope < -0.1:
            return 'Falling'
        else:
            return 'Flat'
    
    def analyze(self, df: pd.DataFrame) -> VolumeResult:
        """
        Complete volume analysis.
        
        Args:
            df: DataFrame with OHLCV data (M1 bars recommended)
        
        Returns:
            VolumeResult with all metrics
        """
        # Rolling delta
        delta = self.calculate_rolling_delta(df)
        if delta > 0:
            delta_signal = 'Bullish'
        elif delta < 0:
            delta_signal = 'Bearish'
        else:
            delta_signal = 'Neutral'
        
        # Volume ROC
        roc, baseline = self.calculate_volume_roc(df)
        if roc > 20:
            roc_signal = 'Above Avg'
        elif roc < -20:
            roc_signal = 'Below Avg'
        else:
            roc_signal = 'Average'
        
        # CVD trend
        cvd_trend = self.determine_cvd_trend(df)
        cvd_series = self.calculate_cvd(df)
        cvd_values = cvd_series.tail(self.cvd_window).tolist()
        
        return VolumeResult(
            delta_5bar=delta,
            delta_signal=delta_signal,
            roc_percent=roc,
            roc_signal=roc_signal,
            cvd_trend=cvd_trend,
            cvd_values=cvd_values
        )

calculations/patterns.py
python"""
Candlestick Pattern Detection.
Detects: Engulfing, Doji, Double Top/Bottom
"""
import pandas as pd
from typing import List
from dataclasses import dataclass

@dataclass
class PatternResult:
    pattern: str
    price: float
    bars_ago: int
    direction: str  # 'bullish' or 'bearish'

class PatternDetector:
    """
    Detects candlestick patterns in bar data.
    """
    
    def __init__(self, doji_threshold: float = 0.1):
        """
        Args:
            doji_threshold: Max body/range ratio for doji (default 10%)
        """
        self.doji_threshold = doji_threshold
    
    def _body_size(self, row: pd.Series) -> float:
        """Calculate absolute body size."""
        return abs(row['close'] - row['open'])
    
    def _range_size(self, row: pd.Series) -> float:
        """Calculate bar range (high - low)."""
        return row['high'] - row['low']
    
    def _is_bullish(self, row: pd.Series) -> bool:
        """Check if bar is bullish (green)."""
        return row['close'] > row['open']
    
    def _is_bearish(self, row: pd.Series) -> bool:
        """Check if bar is bearish (red)."""
        return row['close'] < row['open']
    
    def detect_doji(self, df: pd.DataFrame, lookback: int = 5) -> List[PatternResult]:
        """
        Detect doji candles (small body relative to range).
        """
        patterns = []
        recent = df.tail(lookback)
        
        for i, (idx, row) in enumerate(recent.iterrows()):
            bars_ago = lookback - i - 1
            range_size = self._range_size(row)
            
            if range_size == 0:
                continue
            
            body_ratio = self._body_size(row) / range_size
            
            if body_ratio <= self.doji_threshold:
                patterns.append(PatternResult(
                    pattern='Doji',
                    price=row['close'],
                    bars_ago=bars_ago,
                    direction='neutral'
                ))
        
        return patterns
    
    def detect_engulfing(self, df: pd.DataFrame, lookback: int = 5) -> List[PatternResult]:
        """
        Detect bullish and bearish engulfing patterns.
        """
        patterns = []
        recent = df.tail(lookback + 1)  # Need one extra for comparison
        
        for i in range(1, len(recent)):
            bars_ago = lookback - i
            if bars_ago < 0:
                continue
            
            prev = recent.iloc[i - 1]
            curr = recent.iloc[i]
            
            # Bullish engulfing: previous red, current green engulfs
            if (self._is_bearish(prev) and self._is_bullish(curr) and
                curr['open'] <= prev['close'] and curr['close'] >= prev['open']):
                patterns.append(PatternResult(
                    pattern='Bullish Engulfing',
                    price=curr['close'],
                    bars_ago=bars_ago,
                    direction='bullish'
                ))
            
            # Bearish engulfing: previous green, current red engulfs
            if (self._is_bullish(prev) and self._is_bearish(curr) and
                curr['open'] >= prev['close'] and curr['close'] <= prev['open']):
                patterns.append(PatternResult(
                    pattern='Bearish Engulfing',
                    price=curr['close'],
                    bars_ago=bars_ago,
                    direction='bearish'
                ))
        
        return patterns
    
    def detect_double_top(self, df: pd.DataFrame, tolerance: float = 0.002) -> List[PatternResult]:
        """
        Detect double top pattern (two similar highs).
        
        Args:
            tolerance: Price tolerance for matching highs (default 0.2%)
        """
        patterns = []
        
        if len(df) < 10:
            return patterns
        
        recent = df.tail(20)
        highs = recent['high'].values
        
        # Find local peaks
        peaks = []
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
        
        # Check for double top
        for i in range(len(peaks) - 1):
            idx1, high1 = peaks[i]
            idx2, high2 = peaks[i + 1]
            
            # Check if highs are similar
            if abs(high1 - high2) / high1 <= tolerance:
                bars_ago = len(recent) - idx2 - 1
                patterns.append(PatternResult(
                    pattern='Double Top',
                    price=(high1 + high2) / 2,
                    bars_ago=bars_ago,
                    direction='bearish'
                ))
        
        return patterns
    
    def detect_double_bottom(self, df: pd.DataFrame, tolerance: float = 0.002) -> List[PatternResult]:
        """
        Detect double bottom pattern (two similar lows).
        """
        patterns = []
        
        if len(df) < 10:
            return patterns
        
        recent = df.tail(20)
        lows = recent['low'].values
        
        # Find local troughs
        troughs = []
        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        # Check for double bottom
        for i in range(len(troughs) - 1):
            idx1, low1 = troughs[i]
            idx2, low2 = troughs[i + 1]
            
            if abs(low1 - low2) / low1 <= tolerance:
                bars_ago = len(recent) - idx2 - 1
                patterns.append(PatternResult(
                    pattern='Double Bottom',
                    price=(low1 + low2) / 2,
                    bars_ago=bars_ago,
                    direction='bullish'
                ))
        
        return patterns
    
    def detect_all(self, df: pd.DataFrame) -> List[PatternResult]:
        """
        Run all pattern detections.
        """
        all_patterns = []
        all_patterns.extend(self.detect_doji(df))
        all_patterns.extend(self.detect_engulfing(df))
        all_patterns.extend(self.detect_double_top(df))
        all_patterns.extend(self.detect_double_bottom(df))
        
        # Sort by bars_ago (most recent first)
        all_patterns.sort(key=lambda x: x.bars_ago)
        
        return all_patterns
    
    def detect_multi_timeframe(
        self, 
        data: dict
    ) -> dict:
        """
        Detect patterns across multiple timeframes.
        
        Args:
            data: Dict mapping timeframe -> DataFrame
        
        Returns:
            Dict mapping timeframe -> List[PatternResult]
        """
        results = {}
        for tf, df in data.items():
            results[tf] = self.detect_all(df)
        return results

analysis/prompts/entry_prompt.py
python"""
Entry analysis prompt template for Claude.
"""

ENTRY_PROMPT_TEMPLATE = """You are DOW, an AI trading assistant for intraday analysis. You are analyzing a potential {direction} entry for {ticker} using model {model_name}.

MODEL CONTEXT:
{model_description}

CURRENT MARKET STATE:
- Ticker: {ticker}
- Current Price: ${current_price:.2f}
- Analysis Time: {analysis_time}

ZONE CONTEXT:
{zone_context}

MARKET STRUCTURE (Multi-Timeframe):
{structure_table}

VOLUME ANALYSIS (Last 15-20 M1 Bars):
- Volume Delta (5-bar): {delta_5bar:+,.0f} ({delta_signal})
- Volume ROC: {roc_percent:+.1f}% vs 20-bar avg ({roc_signal})
- CVD Trend: {cvd_trend}

CANDLESTICK PATTERNS DETECTED:
{patterns_list}

SUPPORTING DATA:
- D1 ATR: ${atr:.2f}
- HVN POC Levels: {hvn_pocs}
- Camarilla Levels: {camarilla}

---

Provide analysis in this EXACT format:

RECOMMENDATION: [ENTRY NOW / WAIT / NO TRADE]
CONFIDENCE: [HIGH/MEDIUM/LOW] ([X]/5 signals aligned)

CURRENT ASSESSMENT:
[List 3-5 bullet points with ✓ for aligned signals, ✗ for opposing signals, ⚠ for caution]

{wait_section}

IF TRIGGERED:
  Entry Zone:  $X.XX - $X.XX
  Stop:        $X.XX (reasoning)
  Target 1:    $X.XX (level name)
  Target 2:    $X.XX (level name)

Keep response concise - trader is actively monitoring markets."""

WAIT_SECTION_TEMPLATE = """ENTRY TRIGGER NEEDED:
[List specific conditions that would trigger entry - price levels, structure breaks, volume confirmation]
"""

def build_entry_prompt(
    ticker: str,
    direction: str,
    model: str,
    model_description: str,
    current_price: float,
    analysis_time: str,
    zone_context: str,
    structure_table: str,
    delta_5bar: float,
    delta_signal: str,
    roc_percent: float,
    roc_signal: str,
    cvd_trend: str,
    patterns_list: str,
    atr: float,
    hvn_pocs: str,
    camarilla: str,
    include_wait_section: bool = True
) -> str:
    """Build the complete entry prompt."""
    
    wait_section = WAIT_SECTION_TEMPLATE if include_wait_section else ""
    
    return ENTRY_PROMPT_TEMPLATE.format(
        ticker=ticker,
        direction=direction.upper(),
        model_name=model,
        model_description=model_description,
        current_price=current_price,
        analysis_time=analysis_time,
        zone_context=zone_context,
        structure_table=structure_table,
        delta_5bar=delta_5bar,
        delta_signal=delta_signal,
        roc_percent=roc_percent,
        roc_signal=roc_signal,
        cvd_trend=cvd_trend,
        patterns_list=patterns_list,
        atr=atr,
        hvn_pocs=hvn_pocs,
        camarilla=camarilla,
        wait_section=wait_section
    )

analysis/prompts/exit_prompt.py
python"""
Exit analysis prompt template for Claude.
"""

EXIT_PROMPT_TEMPLATE = """You are DOW, an AI trading assistant for intraday analysis. You are analyzing a potential exit for a {position_type} position in {ticker}.

POSITION CONTEXT:
- Ticker: {ticker}
- Position: {position_type}
- Exit Action: {exit_action}
- Model Used: {model_name}

CURRENT MARKET STATE:
- Current Price: ${current_price:.2f}
- Target Price: ${target_price:.2f} ({target_id})
- Distance to Target: ${distance_to_target:.2f} ({distance_percent:.1f}%)
- Analysis Time: {analysis_time}

ZONE CONTEXT:
{zone_context}

MARKET STRUCTURE (Multi-Timeframe):
{structure_table}

VOLUME ANALYSIS:
- Volume Delta (5-bar): {delta_5bar:+,.0f} ({delta_signal})
- Volume ROC: {roc_percent:+.1f}% vs 20-bar avg ({roc_signal})
- CVD Trend: {cvd_trend}

CANDLESTICK PATTERNS DETECTED:
{patterns_list}

KEY LEVELS:
- HVN POCs: {hvn_pocs}
- Strong Levels (potential reversals): {strong_levels}
- Weak Levels (continuation targets): {weak_levels}

---

Provide analysis in this EXACT format:

RECOMMENDATION: [FULL EXIT / PARTIAL EXIT (X%) / HOLD / TRAIL STOP]
CONFIDENCE: [HIGH/MEDIUM/LOW]

ASSESSMENT:
[List 3-5 bullet points with ⚠ for exit signals, ✓ for hold signals]

ACTION:
[Specific action steps - price levels for exits, stop adjustments]

HOLD TRIGGERS (if recommending hold or partial):
[What would need to happen to continue holding / add to position]

Keep response concise - trader is actively monitoring markets."""

def build_exit_prompt(
    ticker: str,
    position_type: str,  # 'LONG' or 'SHORT'
    exit_action: str,    # 'SELL' or 'COVER'
    model_name: str,
    current_price: float,
    target_price: float,
    target_id: str,
    analysis_time: str,
    zone_context: str,
    structure_table: str,
    delta_5bar: float,
    delta_signal: str,
    roc_percent: float,
    roc_signal: str,
    cvd_trend: str,
    patterns_list: str,
    hvn_pocs: str,
    strong_levels: str,
    weak_levels: str
) -> str:
    """Build the complete exit prompt."""
    
    distance_to_target = abs(target_price - current_price)
    distance_percent = (distance_to_target / current_price) * 100
    
    return EXIT_PROMPT_TEMPLATE.format(
        ticker=ticker,
        position_type=position_type,
        exit_action=exit_action,
        model_name=model_name,
        current_price=current_price,
        target_price=target_price,
        target_id=target_id,
        distance_to_target=distance_to_target,
        distance_percent=distance_percent,
        analysis_time=analysis_time,
        zone_context=zone_context,
        structure_table=structure_table,
        delta_5bar=delta_5bar,
        delta_signal=delta_signal,
        roc_percent=roc_percent,
        roc_signal=roc_signal,
        cvd_trend=cvd_trend,
        patterns_list=patterns_list,
        hvn_pocs=hvn_pocs,
        strong_levels=strong_levels,
        weak_levels=weak_levels
    )

analysis/claude_client.py
python"""
Claude API client for DOW analysis.
"""
import anthropic
from typing import Optional

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS

class ClaudeClient:
    """
    Client for Claude API interactions.
    """
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or ANTHROPIC_API_KEY
        self.model = model or CLAUDE_MODEL
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def analyze(self, prompt: str, max_tokens: int = None) -> str:
        """
        Send prompt to Claude and get response.
        
        Args:
            prompt: The analysis prompt
            max_tokens: Max response tokens (default from config)
        
        Returns:
            Claude's response text
        """
        max_tokens = max_tokens or CLAUDE_MAX_TOKENS
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        
        except anthropic.APIError as e:
            return f"API Error: {e}"
        except Exception as e:
            return f"Error: {e}"

analysis/aggregator.py
python"""
Aggregator: Compiles all data and calculations for Claude prompt.
"""
from datetime import datetime
from typing import Dict, Optional
import pytz

from config import MODELS, TIMEZONE

from data.polygon_fetcher import PolygonFetcher
from data.epoch_reader import EpochReader
from calculations.market_structure import MarketStructureCalculator
from calculations.volume_analysis import VolumeAnalyzer
from calculations.patterns import PatternDetector
from analysis.claude_client import ClaudeClient
from analysis.prompts.entry_prompt import build_entry_prompt
from analysis.prompts.exit_prompt import build_exit_prompt

class AnalysisAggregator:
    """
    Aggregates all data sources and calculations for analysis.
    """
    
    def __init__(self):
        self.polygon = PolygonFetcher()
        self.epoch = EpochReader()
        self.structure_calc = MarketStructureCalculator()
        self.volume_analyzer = VolumeAnalyzer()
        self.pattern_detector = PatternDetector()
        self.claude = ClaudeClient()
        self.tz = pytz.timezone(TIMEZONE)
    
    def _format_structure_table(self, structure: Dict) -> str:
        """Format market structure as ASCII table."""
        lines = ["         Direction    Strong Level    Weak Level    Last Break"]
        for tf in ['M5', 'M15', 'H1', 'H4']:
            if tf in structure:
                s = structure[tf]
                strong = f"${s.strong_level:.2f}" if s.strong_level else "N/A"
                weak = f"${s.weak_level:.2f}" if s.weak_level else "N/A"
                break_info = f"{s.last_break} {'↑' if s.direction == 'BULL' else '↓'}" if s.last_break else "N/A"
                lines.append(f"{tf:<8} {s.direction:<12} {strong:<15} {weak:<13} {break_info}")
        return "\n".join(lines)
    
    def _format_patterns(self, patterns: Dict) -> str:
        """Format patterns as list."""
        lines = []
        for tf in ['M5', 'M15', 'H1']:
            if tf in patterns and patterns[tf]:
                for p in patterns[tf][:2]:  # Max 2 per timeframe
                    ago = "current bar" if p.bars_ago == 0 else f"{p.bars_ago} bars ago"
                    lines.append(f"{tf}:  {p.pattern} @ ${p.price:.2f} ({ago})")
        
        if not lines:
            lines.append("None detected")
        
        return "\n".join(lines)
    
    def _format_zone_context(self, zone: Optional[Dict], direction: str) -> str:
        """Format zone information."""
        if not zone:
            return "No active zone identified for this ticker/direction"
        
        return f"""Active Zone:     {zone['rank']} | ${zone['zone_low']:.2f} - ${zone['zone_high']:.2f} | HVN POC: ${zone['hvn_poc']:.2f}
Zone Score:      {zone['score']} | Confluences: {zone['confluences']}
{direction.title()} Target:     ${zone['target']:.2f}"""
    
    def run_entry_analysis(
        self,
        ticker: str,
        direction: str,
        model: str,
        analysis_datetime: Optional[datetime] = None
    ) -> Dict:
        """
        Run complete entry analysis.
        
        Args:
            ticker: Stock symbol
            direction: 'long' or 'short'
            model: 'EPCH_01', 'EPCH_02', 'EPCH_03', or 'EPCH_04'
            analysis_datetime: Specific time for backtest (None = live)
        
        Returns:
            Dict with all analysis data and Claude response
        """
        # Connect to Excel
        if not self.epoch.connect():
            return {"error": "Could not connect to Excel workbook"}
        
        # Determine analysis time
        if analysis_datetime:
            analysis_time = analysis_datetime
        else:
            analysis_time = datetime.now(self.tz)
        
        # Get model info
        model_info = MODELS.get(model, MODELS['EPCH_01'])
        
        # Fetch live/historical data from Polygon
        bar_data = self.polygon.fetch_multi_timeframe(
            ticker, 
            ['M1', 'M5', 'M15', 'H1', 'H4'],
            analysis_time
        )
        
        if not bar_data or 'M1' not in bar_data:
            return {"error": f"Could not fetch bar data for {ticker}"}
        
        # Get current price
        current_price = float(bar_data['M1'].iloc[-1]['close'])
        
        # Read zone data from Excel
        zone_type = model_info['zone_type']
        if zone_type == 'primary':
            zone = self.epoch.get_primary_zone(ticker, direction)
        else:
            zone = self.epoch.get_secondary_zone(ticker, direction)
        
        # Calculate market structure
        structure = self.structure_calc.calculate_multi_timeframe({
            tf: df for tf, df in bar_data.items() if tf != 'M1'
        })
        
        # Volume analysis on M1 data
        volume = self.volume_analyzer.analyze(bar_data['M1'])
        
        # Pattern detection
        patterns = self.pattern_detector.detect_multi_timeframe({
            tf: df for tf, df in bar_data.items() if tf in ['M5', 'M15', 'H1']
        })
        
        # Get additional levels from Excel
        atr = self.epoch.read_atr(ticker) or 2.0
        hvn_pocs = self.epoch.read_hvn_pocs(ticker)
        camarilla = self.epoch.read_camarilla_levels(ticker)
        
        # Build prompt
        prompt = build_entry_prompt(
            ticker=ticker,
            direction=direction,
            model=model,
            model_description=model_info['description'],
            current_price=current_price,
            analysis_time=analysis_time.strftime("%Y-%m-%d %H:%M:%S ET"),
            zone_context=self._format_zone_context(zone, direction),
            structure_table=self._format_structure_table(structure),
            delta_5bar=volume.delta_5bar,
            delta_signal=volume.delta_signal,
            roc_percent=volume.roc_percent,
            roc_signal=volume.roc_signal,
            cvd_trend=volume.cvd_trend,
            patterns_list=self._format_patterns(patterns),
            atr=atr,
            hvn_pocs=", ".join([f"${p:.2f}" for p in hvn_pocs[:5]]) if hvn_pocs else "N/A",
            camarilla=f"S3: ${camarilla.get('d1_s3', 0):.2f}, R3: ${camarilla.get('d1_r3', 0):.2f}" if camarilla else "N/A"
        )
        
        # Get Claude analysis
        claude_response = self.claude.analyze(prompt)
        
        return {
            "ticker": ticker,
            "direction": direction,
            "model": model,
            "current_price": current_price,
            "analysis_time": analysis_time,
            "zone": zone,
            "structure": structure,
            "volume": volume,
            "patterns": patterns,
            "atr": atr,
            "hvn_pocs": hvn_pocs,
            "camarilla": camarilla,
            "claude_response": claude_response,
            "prompt": prompt  # For debugging
        }
    
    def run_exit_analysis(
        self,
        ticker: str,
        exit_action: str,  # 'sell' or 'cover'
        model: str,
        analysis_datetime: Optional[datetime] = None
    ) -> Dict:
        """
        Run complete exit analysis.
        
        Args:
            ticker: Stock symbol
            exit_action: 'sell' (close long) or 'cover' (close short)
            model: Model used for entry
            analysis_datetime: Specific time for backtest (None = live)
        
        Returns:
            Dict with all analysis data and Claude response
        """
        # Connect to Excel
        if not self.epoch.connect():
            return {"error": "Could not connect to Excel workbook"}
        
        # Determine position type from exit action
        position_type = "LONG" if exit_action.lower() == "sell" else "SHORT"
        direction = "long" if position_type == "LONG" else "short"
        
        # Determine analysis time
        if analysis_datetime:
            analysis_time = analysis_datetime
        else:
            analysis_time = datetime.now(self.tz)
        
        # Get model info
        model_info = MODELS.get(model, MODELS['EPCH_01'])
        
        # Fetch data
        bar_data = self.polygon.fetch_multi_timeframe(
            ticker,
            ['M1', 'M5', 'M15', 'H1', 'H4'],
            analysis_time
        )
        
        if not bar_data or 'M1' not in bar_data:
            return {"error": f"Could not fetch bar data for {ticker}"}
        
        current_price = float(bar_data['M1'].iloc[-1]['close'])
        
        # Get zone and target from Excel
        zone_type = model_info['zone_type']
        if zone_type == 'primary':
            zone = self.epoch.get_primary_zone(ticker, direction)
        else:
            zone = self.epoch.get_secondary_zone(ticker, direction)
        
        # Get target from Analysis worksheet
        analysis_setups = self.epoch.read_analysis_setups(ticker)
        setup = analysis_setups.get('primary') if zone_type == 'primary' else analysis_setups.get('secondary')
        
        target_price = zone['target'] if zone else current_price
        target_id = setup.get('target_id', 'Unknown') if setup else 'Unknown'
        
        # Calculate structure
        structure = self.structure_calc.calculate_multi_timeframe({
            tf: df for tf, df in bar_data.items() if tf != 'M1'
        })
        
        # Volume analysis
        volume = self.volume_analyzer.analyze(bar_data['M1'])
        
        # Patterns
        patterns = self.pattern_detector.detect_multi_timeframe({
            tf: df for tf, df in bar_data.items() if tf in ['M5', 'M15', 'H1']
        })
        
        # Get levels
        hvn_pocs = self.epoch.read_hvn_pocs(ticker)
        
        # Collect strong/weak levels from structure
        strong_levels = []
        weak_levels = []
        for tf, s in structure.items():
            if s.strong_level:
                strong_levels.append(f"{tf}: ${s.strong_level:.2f}")
            if s.weak_level:
                weak_levels.append(f"{tf}: ${s.weak_level:.2f}")
        
        # Build prompt
        prompt = build_exit_prompt(
            ticker=ticker,
            position_type=position_type,
            exit_action=exit_action.upper(),
            model_name=model,
            current_price=current_price,
            target_price=target_price,
            target_id=target_id,
            analysis_time=analysis_time.strftime("%Y-%m-%d %H:%M:%S ET"),
            zone_context=self._format_zone_context(zone, direction),
            structure_table=self._format_structure_table(structure),
            delta_5bar=volume.delta_5bar,
            delta_signal=volume.delta_signal,
            roc_percent=volume.roc_percent,
            roc_signal=volume.roc_signal,
            cvd_trend=volume.cvd_trend,
            patterns_list=self._format_patterns(patterns),
            hvn_pocs=", ".join([f"${p:.2f}" for p in hvn_pocs[:5]]) if hvn_pocs else "N/A",
            strong_levels=", ".join(strong_levels) if strong_levels else "N/A",
            weak_levels=", ".join(weak_levels) if weak_levels else "N/A"
        )
        
        # Get Claude analysis
        claude_response = self.claude.analyze(prompt)
        
        return {
            "ticker": ticker,
            "position_type": position_type,
            "exit_action": exit_action,
            "model": model,
            "current_price": current_price,
            "target_price": target_price,
            "target_id": target_id,
            "analysis_time": analysis_time,
            "zone": zone,
            "structure": structure,
            "volume": volume,
            "patterns": patterns,
            "claude_response": claude_response,
            "prompt": prompt
        }

output/terminal.py
python"""
Rich terminal output formatting for DOW.
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from datetime import datetime

console = Console()

def print_header(ticker: str, mode: str, direction: str, model: str, analysis_time: datetime):
    """Print analysis header."""
    title = f"DOW ANALYSIS: {ticker} | {mode.upper()} {direction.upper()} | MODEL: {model}"
    timestamp = analysis_time.strftime("%Y-%m-%d %H:%M:%S ET")
    
    console.print()
    console.print("═" * 70, style="bold blue")
    console.print(title, style="bold white")
    console.print(f"Timestamp: {timestamp}", style="dim")
    console.print("═" * 70, style="bold blue")

def print_section(title: str):
    """Print section divider."""
    console.print()
    console.print("─" * 70, style="dim")
    console.print(title, style="bold cyan")
    console.print("─" * 70, style="dim")

def print_current_price(price: float):
    """Print current price prominently."""
    console.print(f"\nCURRENT PRICE: ${price:.2f}", style="bold yellow")

def print_zone_context(zone: dict):
    """Print zone information."""
    print_section("ZONE CONTEXT")
    
    if not zone:
        console.print("No active zone identified", style="dim red")
        return
    
    console.print(f"Active Zone:     {zone['rank']} | ${zone['zone_low']:.2f} - ${zone['zone_high']:.2f} | HVN POC: ${zone['hvn_poc']:.2f}")
    console.print(f"Zone Score:      {zone['score']} | Confluences: {zone['confluences']}")
    if zone.get('target'):
        console.print(f"Target:          ${zone['target']:.2f}")

def print_structure_table(structure: dict):
    """Print market structure table."""
    print_section("MARKET STRUCTURE")
    
    table = Table(box=box.SIMPLE)
    table.add_column("TF", style="cyan", width=6)
    table.add_column("Direction", width=12)
    table.add_column("Strong Level", width=14)
    table.add_column("Weak Level", width=14)
    table.add_column("Last Break", width=12)
    
    for tf in ['M5', 'M15', 'H1', 'H4']:
        if tf in structure:
            s = structure[tf]
            
            # Color direction
            dir_style = "green" if s.direction == "BULL" else "red" if s.direction == "BEAR" else "yellow"
            direction = Text(s.direction, style=dir_style)
            
            strong = f"${s.strong_level:.2f}" if s.strong_level else "N/A"
            weak = f"${s.weak_level:.2f}" if s.weak_level else "N/A"
            
            if s.last_break:
                arrow = "↑" if s.direction == "BULL" else "↓"
                break_text = f"{s.last_break} {arrow}"
            else:
                break_text = "N/A"
            
            table.add_row(tf, direction, strong, weak, break_text)
    
    console.print(table)

def print_volume_analysis(volume):
    """Print volume analysis section."""
    print_section("VOLUME ANALYSIS (Last 15 M1 Bars)")
    
    # Delta
    delta_style = "green" if volume.delta_signal == "Bullish" else "red" if volume.delta_signal == "Bearish" else "yellow"
    console.print(f"Volume Delta (5-bar):    {volume.delta_5bar:+,.0f} ({volume.delta_signal})", style=delta_style)
    
    # ROC
    roc_style = "green" if volume.roc_signal == "Above Avg" else "red" if volume.roc_signal == "Below Avg" else "yellow"
    console.print(f"Volume ROC:              {volume.roc_percent:+.1f}% vs 20-bar avg ({volume.roc_signal})", style=roc_style)
    
    # CVD
    cvd_style = "green" if volume.cvd_trend == "Rising" else "red" if volume.cvd_trend == "Falling" else "yellow"
    console.print(f"CVD Trend:               {volume.cvd_trend}", style=cvd_style)

def print_patterns(patterns: dict):
    """Print candlestick patterns."""
    print_section("CANDLESTICK PATTERNS")
    
    found = False
    for tf in ['M5', 'M15', 'H1']:
        if tf in patterns and patterns[tf]:
            for p in patterns[tf][:2]:
                ago = "current bar" if p.bars_ago == 0 else f"{p.bars_ago} bars ago"
                style = "green" if p.direction == "bullish" else "red" if p.direction == "bearish" else "yellow"
                console.print(f"{tf}:  {p.pattern} @ ${p.price:.2f} ({ago})", style=style)
                found = True
    
    if not found:
        console.print("None detected", style="dim")

def print_claude_analysis(response: str):
    """Print Claude's analysis in a panel."""
    console.print()
    console.print("═" * 70, style="bold green")
    console.print("CLAUDE ANALYSIS", style="bold green")
    console.print("═" * 70, style="bold green")
    console.print()
    console.print(response)
    console.print()
    console.print("═" * 70, style="bold green")

def print_entry_analysis(result: dict):
    """Print complete entry analysis."""
    print_header(
        result['ticker'],
        'ENTRY',
        result['direction'],
        result['model'],
        result['analysis_time']
    )
    
    print_current_price(result['current_price'])
    print_zone_context(result.get('zone'))
    print_structure_table(result['structure'])
    print_volume_analysis(result['volume'])
    print_patterns(result['patterns'])
    print_claude_analysis(result['claude_response'])

def print_exit_analysis(result: dict):
    """Print complete exit analysis."""
    print_header(
        result['ticker'],
        'EXIT',
        result['exit_action'],
        result['model'],
        result['analysis_time']
    )
    
    print_current_price(result['current_price'])
    
    # Target info
    target = result.get('target_price', 0)
    distance = abs(target - result['current_price'])
    distance_pct = (distance / result['current_price']) * 100
    console.print(f"TARGET:          ${target:.2f} ({result.get('target_id', 'N/A')}) | {distance_pct:.1f}% away", style="bold")
    
    print_zone_context(result.get('zone'))
    print_structure_table(result['structure'])
    print_volume_analysis(result['volume'])
    print_patterns(result['patterns'])
    print_claude_analysis(result['claude_response'])

def print_error(message: str):
    """Print error message."""
    console.print(f"\n[bold red]ERROR:[/bold red] {message}")

cli.py
python"""
DOW CLI - Command Line Interface
"""
import click
from datetime import datetime
import pytz

from config import MODELS, TIMEZONE
from analysis.aggregator import AnalysisAggregator
from output.terminal import print_entry_analysis, print_exit_analysis, print_error

@click.group()
def cli():
    """DOW AI Trading Assistant - Entry/Exit Analysis"""
    pass

@cli.command()
@click.argument('ticker')
@click.argument('direction', type=click.Choice(['long', 'short'], case_sensitive=False))
@click.argument('model', type=click.Choice(['EPCH_01', 'EPCH_02', 'EPCH_03', 'EPCH_04'], case_sensitive=False))
@click.option('--datetime', 'dt_str', default=None, help='Historical datetime (ET): "YYYY-MM-DD HH:MM"')
def entry(ticker: str, direction: str, model: str, dt_str: str):
    """
    Analyze potential entry.
    
    Examples:
    
        dow entry TSLA long EPCH_01
        
        dow entry NVDA short EPCH_02 --datetime "2024-12-03 10:30"
    """
    # Parse datetime if provided
    analysis_dt = None
    if dt_str:
        try:
            tz = pytz.timezone(TIMEZONE)
            analysis_dt = tz.localize(datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))
        except ValueError:
            print_error(f"Invalid datetime format. Use: YYYY-MM-DD HH:MM")
            return
    
    # Run analysis
    aggregator = AnalysisAggregator()
    result = aggregator.run_entry_analysis(
        ticker=ticker.upper(),
        direction=direction.lower(),
        model=model.upper(),
        analysis_datetime=analysis_dt
    )
    
    if 'error' in result:
        print_error(result['error'])
        return
    
    print_entry_analysis(result)

@cli.command()
@click.argument('ticker')
@click.argument('action', type=click.Choice(['sell', 'cover'], case_sensitive=False))
@click.argument('model', type=click.Choice(['EPCH_01', 'EPCH_02', 'EPCH_03', 'EPCH_04'], case_sensitive=False))
@click.option('--datetime', 'dt_str', default=None, help='Historical datetime (ET): "YYYY-MM-DD HH:MM"')
def exit(ticker: str, action: str, model: str, dt_str: str):
    """
    Analyze potential exit.
    
    Actions:
    
        sell  - Close a LONG position
        
        cover - Close a SHORT position
    
    Examples:
    
        dow exit TSLA sell EPCH_01
        
        dow exit NVDA cover EPCH_02 --datetime "2024-12-03 14:45"
    """
    # Parse datetime if provided
    analysis_dt = None
    if dt_str:
        try:
            tz = pytz.timezone(TIMEZONE)
            analysis_dt = tz.localize(datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))
        except ValueError:
            print_error(f"Invalid datetime format. Use: YYYY-MM-DD HH:MM")
            return
    
    # Run analysis
    aggregator = AnalysisAggregator()
    result = aggregator.run_exit_analysis(
        ticker=ticker.upper(),
        exit_action=action.lower(),
        model=model.upper(),
        analysis_datetime=analysis_dt
    )
    
    if 'error' in result:
        print_error(result['error'])
        return
    
    print_exit_analysis(result)

@cli.command()
def models():
    """List available trading models."""
    click.echo("\nAvailable Models:\n")
    for model_id, info in MODELS.items():
        click.echo(f"  {model_id}: {info['name']}")
        click.echo(f"           {info['description']}")
        click.echo()

if __name__ == '__main__':
    cli()

main.py
python"""
DOW AI Trading Assistant - Main Entry Point
"""
from cli import cli

if __name__ == '__main__':
    cli()

launcher.bat (Windows Batch Launcher)
batch@echo off
title DOW AI Trading Assistant
cd /d C:\XIIITradingSystems\Epoch
call venv\Scripts\activate.bat

:menu
cls
echo.
echo ========================================
echo   DOW AI TRADING ASSISTANT
echo ========================================
echo.
echo Commands:
echo   dow entry [TICKER] [long/short] [MODEL]
echo   dow exit [TICKER] [sell/cover] [MODEL]
echo   dow models (list available models)
echo.
echo Add --datetime "YYYY-MM-DD HH:MM" for backtest
echo.
echo Type 'quit' to exit
echo ========================================
echo.

set /p cmd="dow "
if /i "%cmd%"=="quit" goto end
if /i "%cmd%"=="exit" goto end
if /i "%cmd%"=="" goto menu

python 04_dow_ai\main.py %cmd%
echo.
pause
goto menu

:end
echo Goodbye!

launcher.ps1 (PowerShell Launcher)
powershell# DOW AI Trading Assistant Launcher
$Host.UI.RawUI.WindowTitle = "DOW AI Trading Assistant"
Set-Location "C:\XIIITradingSystems\Epoch"
& ".\venv\Scripts\Activate.ps1"

function Show-Menu {
    Clear-Host
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   DOW AI TRADING ASSISTANT" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  entry [TICKER] [long/short] [MODEL]"
    Write-Host "  exit [TICKER] [sell/cover] [MODEL]"
    Write-Host "  models (list available models)"
    Write-Host ""
    Write-Host "Add --datetime `"YYYY-MM-DD HH:MM`" for backtest"
    Write-Host ""
    Write-Host "Type 'quit' to exit"
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

while ($true) {
    Show-Menu
    $input = Read-Host "dow"
    
    if ($input -eq "quit" -or $input -eq "exit") {
        Write-Host "Goodbye!" -ForegroundColor Green
        break
    }
    
    if ($input -ne "") {
        $args = $input -split " "
        python 04_dow_ai\main.py @args
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
}
```

---

### Requirements

Create `04_dow_ai/requirements.txt`:
```
anthropic>=0.18.0
click>=8.0.0
pandas>=2.0.0
numpy>=1.24.0
requests>=2.28.0
xlwings>=0.30.0
pytz>=2023.3
rich>=13.0.0
pydantic>=2.0.0
```

---

### Installation Instructions for Claude Code
```
1. Create directory structure:
   mkdir C:\XIIITradingSystems\Epoch\04_dow_ai
   mkdir C:\XIIITradingSystems\Epoch\04_dow_ai\data
   mkdir C:\XIIITradingSystems\Epoch\04_dow_ai\calculations
   mkdir C:\XIIITradingSystems\Epoch\04_dow_ai\analysis
   mkdir C:\XIIITradingSystems\Epoch\04_dow_ai\analysis\prompts
   mkdir C:\XIIITradingSystems\Epoch\04_dow_ai\output

2. Create all files as specified above

3. Install dependencies:
   cd C:\XIIITradingSystems\Epoch
   .\venv\Scripts\Activate.ps1
   pip install -r 04_dow_ai\requirements.txt

4. Update config.py with actual API keys:
   - POLYGON_API_KEY
   - ANTHROPIC_API_KEY

5. Create desktop shortcut to launcher.bat or launcher.ps1

6. Test:
   python 04_dow_ai\main.py entry TSLA long EPCH_01

Testing Checklist

 Polygon data fetching (live and historical)
 Excel connection and zone reading
 Market structure calculation across timeframes
 Volume delta, ROC, CVD calculations
 Pattern detection
 Claude API integration
 Entry analysis end-to-end
 Exit analysis end-to-end
 Historical backtest mode
 Standalone launcher
Footprint Chart Implementation Specification - Phased Guide
Version: 2.0 (Phased Implementation)
Date: December 29, 2025
Implementation Plan: XIII-002

Table of Contents

Executive Summary
Architecture Overview
Phase 0: Environment Setup
Phase 1: Data Models
Phase 2: API Integration
Phase 3: Processing Engine
Phase 4: Supabase Caching
Phase 5: Visualization
Phase 6: Streamlit Integration
Phase 7: Polish & Enhancements
Testing Guidelines
Appendices


Executive Summary
This specification extends the Epoch 1.0 trade review system with footprint chart visualization. The system fetches tick-level trades and NBBO quotes from Massive.com (formerly Polygon), classifies each trade as buyer or seller initiated, and renders a traditional footprint chart showing bid/ask volume distribution per 1-minute bar for the 15 bars prior to trade entry.
Key Features

Dynamic tick sizing: ATR-based (1-minute ATR ÷ 20 levels)
Trade classification: Match each trade to concurrent NBBO for bid/ask assignment
Traditional footprint layout: Bid column | Price | Ask column per bar
POC identification: Highest volume price per bar highlighted
Imbalance detection: 300% threshold for diagonal imbalances
Supabase caching: Store processed footprint data to avoid re-fetching

Implementation Approach
This specification is organized into 8 phases (XIII-002.01 through XIII-002.08). Each phase is self-contained with:

Clear prerequisites
Specific deliverables
Code examples
Acceptance criteria


Architecture Overview
System Diagram
┌─────────────────────────────────────────────────────────────────┐
│                    TRADE REVIEW DASHBOARD                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    M15 CHART + ZONES                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    H1 CHART + ZONES                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              FOOTPRINT CHART (15 x 1-MIN BARS)          │◄── NEW
│  │  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐      │
│  │  │ Bar │ Bar │ Bar │ Bar │ Bar │ Bar │ ... │Entry│      │
│  │  │  1  │  2  │  3  │  4  │  5  │  6  │     │ Bar │      │
│  │  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘      │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  STATISTICS TABLE                        │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
Data Flow Pipeline
Trade Entry Timestamp
        │
        ▼
Calculate Time Window: entry_time - 15min → entry_time
        │
        ├──────────────────┬──────────────────┐
        ▼                  ▼                  ▼
   Fetch 1-Min Bars    Fetch Trades      Fetch Quotes
   (for ATR calc)      (Massive API)     (Massive API)
        │                  │                  │
        ▼                  └────────┬─────────┘
   Calculate ATR                    ▼
   tick_size = ATR/20     Trade Classification Engine
        │                 (match trade → NBBO at timestamp)
        │                          │
        └────────────┬─────────────┘
                     ▼
            Aggregate by Bar + Price Level
                     │
                     ▼
            ┌────────────────────┐
            │  FootprintBar[]    │
            │  - price_levels[]  │
            │  - POC             │
            │  - imbalances[]    │
            │  - bar_delta       │
            └────────────────────┘
                     │
                     ▼
            Cache to Supabase
                     │
                     ▼
            Render Plotly Footprint
Final Project Structure
epoch_review/
├── app.py                          # Main entry (integrate footprint in Phase 6)
├── components/
│   ├── __init__.py
│   ├── charts.py                   # Existing M15/H1 charts
│   ├── footprint_panel.py          # NEW in Phase 6
│   └── ...
├── footprint/                      # NEW module
│   ├── __init__.py                 # Phase 0
│   ├── config.py                   # Phase 0
│   ├── models.py                   # Phase 1
│   ├── massive_client.py           # Phase 2
│   ├── classifier.py               # Phase 2
│   ├── builder.py                  # Phase 3
│   ├── cache.py                    # Phase 4
│   └── visualization.py            # Phase 5
├── data/
│   ├── polygon_client.py           # Existing - reuse auth
│   ├── supabase_client.py          # Existing - reuse connection
│   └── ...
└── requirements.txt                # Update in Phase 0

PHASE 0: Environment Setup (XIII-002.01)
Prerequisites

Existing Epoch 1.0 project structure
Python 3.8+
Access to Polygon API key (already configured)

Tasks

Create footprint/ directory structure and init.py files
Update requirements.txt (plotly, pytz) and install dependencies
Create footprint/config.py with constants from spec

Deliverables
1. Create Directory Structure
bashmkdir -p footprint
touch footprint/__init__.py
touch footprint/config.py
```

#### 2. Update requirements.txt
Add these lines:
```
plotly>=5.18.0
pytz>=2023.3
Then install:
bashpip install -r requirements.txt
3. Create Configuration File
File: footprint/config.py
python"""
Footprint Chart Configuration
Centralized constants for footprint chart generation
"""

# API Configuration
MASSIVE_BASE_URL = "https://api.polygon.io"

# Footprint Parameters
FOOTPRINT_CONFIG = {
    'bar_count': 15,              # Number of 1-min bars before entry
    'imbalance_threshold': 3.0,   # 300% for diagonal imbalance detection
    'tick_levels': 20,            # ATR / this value = tick size
    'atr_period': 14,             # ATR calculation period
}

# Tick Size Minimums (based on price level)
TICK_MINIMUMS = {
    'sub_dollar': 0.0001,    # Price < $1
    'default': 0.01,          # Price >= $1
}

# Visualization Colors
FOOTPRINT_COLORS = {
    'background': '#131722',
    'grid': '#1e222d',
    'text': '#d1d4dc',
    'bid': '#ef5350',              # Red for selling
    'ask': '#26a69a',              # Green for buying
    'poc': '#ffeb3b',              # Yellow highlight
    'imbalance_buy': '#00e676',    # Bright green
    'imbalance_sell': '#ff1744',   # Bright red
    'neutral': '#666666'
}

# Chart Dimensions
CHART_CONFIG = {
    'default_height': 450,
    'bar_width': 80,      # pixels
    'cell_height': 20,    # pixels
}

# Rate Limiting
API_RATE_LIMIT = {
    'delay_between_requests': 0.1,  # seconds
    'max_records_per_request': 50000,
}
4. Initialize Module
File: footprint/__init__.py
python"""
Footprint Chart Module
Provides tick-level market microstructure analysis for trade review
"""

from .config import (
    FOOTPRINT_CONFIG,
    FOOTPRINT_COLORS,
    CHART_CONFIG,
    TICK_MINIMUMS,
    API_RATE_LIMIT,
    MASSIVE_BASE_URL,
)

__version__ = '1.0.0'
__all__ = [
    'FOOTPRINT_CONFIG',
    'FOOTPRINT_COLORS',
    'CHART_CONFIG',
    'TICK_MINIMUMS',
    'API_RATE_LIMIT',
    'MASSIVE_BASE_URL',
]
Acceptance Criteria

 footprint/ directory exists with __init__.py and config.py
 Dependencies installed without errors
 Can run: python -c "from footprint import FOOTPRINT_CONFIG; print(FOOTPRINT_CONFIG)"
 No import errors when running existing project


PHASE 1: Data Models (XIII-002.02)
Prerequisites

Phase 0 completed
Understanding of Python dataclasses
Familiarity with type hints

Tasks

Create TradeSide enum and ClassifiedTrade dataclass in models.py
Create PriceLevel dataclass with delta/total_volume properties
Create Imbalance dataclass and test instances
Create FootprintBar with calculate_poc(), calculate_bar_delta(), detect_imbalances()
Create FootprintData with to_cache_dict() and from_cache_dict() methods
Test round-trip serialization for all models

Implementation
File: footprint/models.py
python"""
Data models for footprint chart representation
All structures needed to represent tick-level market data
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum


class TradeSide(Enum):
    """Trade classification based on aggressor side."""
    BID = "bid"          # Seller-initiated (hit bid)
    ASK = "ask"          # Buyer-initiated (lift ask)
    NEUTRAL = "neutral"  # Between bid/ask, unclear


@dataclass
class ClassifiedTrade:
    """
    Single trade with bid/ask classification.
    
    Attributes:
        timestamp: Trade execution time (nanosecond precision)
        price: Execution price
        size: Number of shares
        side: Classification as BID/ASK/NEUTRAL
        exchange: Exchange ID
        conditions: Trade condition codes
    """
    timestamp: datetime
    price: float
    size: int
    side: TradeSide
    exchange: int
    conditions: List[int] = field(default_factory=list)


@dataclass
class PriceLevel:
    """
    Volume aggregation at a single price within a bar.
    
    Represents the bid and ask volume executed at a specific price level
    during a 1-minute bar.
    """
    price: float
    bid_volume: int = 0          # Seller-initiated volume
    ask_volume: int = 0          # Buyer-initiated volume
    trade_count: int = 0
    
    @property
    def delta(self) -> int:
        """
        Net buying/selling pressure.
        Positive = buying pressure, Negative = selling pressure
        """
        return self.ask_volume - self.bid_volume
    
    @property
    def total_volume(self) -> int:
        """Total volume at this price level."""
        return self.bid_volume + self.ask_volume


@dataclass
class Imbalance:
    """
    Detected diagonal imbalance between price levels.
    
    An imbalance occurs when one side's volume at a price is significantly
    greater than the opposite side's volume at an adjacent price.
    """
    price: float
    direction: str               # 'buy' or 'sell'
    ratio: float                 # e.g., 3.5 means 350%
    strong_side_volume: int
    weak_side_volume: int


@dataclass
class FootprintBar:
    """
    Complete footprint data for a single 1-minute bar.
    
    Contains all price levels with bid/ask volume, calculated POC,
    delta, and detected imbalances.
    """
    bar_start: datetime
    bar_end: datetime
    open: float
    high: float
    low: float
    close: float
    
    tick_size: float             # ATR/20 for this bar's context
    price_levels: Dict[float, PriceLevel] = field(default_factory=dict)
    
    # Computed properties
    poc_price: Optional[float] = None       # Point of Control
    bar_delta: int = 0                      # Net delta for entire bar
    imbalances: List[Imbalance] = field(default_factory=list)
    
    def calculate_poc(self):
        """
        Find price with highest total volume (Point of Control).
        Sets self.poc_price to the price level with maximum volume.
        """
        if not self.price_levels:
            return
        self.poc_price = max(
            self.price_levels.keys(),
            key=lambda p: self.price_levels[p].total_volume
        )
    
    def calculate_bar_delta(self):
        """
        Sum delta across all price levels.
        Positive = net buying, Negative = net selling
        """
        self.bar_delta = sum(
            level.delta for level in self.price_levels.values()
        )
    
    def detect_imbalances(self, threshold: float = 3.0):
        """
        Detect diagonal imbalances between adjacent price levels.
        
        A buy imbalance: ask_volume[price] / bid_volume[price - tick] >= threshold
        A sell imbalance: bid_volume[price] / ask_volume[price + tick] >= threshold
        
        Args:
            threshold: Minimum ratio to qualify as imbalance (default 3.0 = 300%)
        """
        self.imbalances = []
        sorted_prices = sorted(self.price_levels.keys())
        
        for i, price in enumerate(sorted_prices):
            level = self.price_levels[price]
            
            # Check for buy imbalance (compare to price below)
            if i > 0:
                lower_price = sorted_prices[i - 1]
                lower_level = self.price_levels[lower_price]
                if lower_level.bid_volume > 0:
                    ratio = level.ask_volume / lower_level.bid_volume
                    if ratio >= threshold:
                        self.imbalances.append(Imbalance(
                            price=price,
                            direction='buy',
                            ratio=ratio,
                            strong_side_volume=level.ask_volume,
                            weak_side_volume=lower_level.bid_volume
                        ))
            
            # Check for sell imbalance (compare to price above)
            if i < len(sorted_prices) - 1:
                upper_price = sorted_prices[i + 1]
                upper_level = self.price_levels[upper_price]
                if upper_level.ask_volume > 0:
                    ratio = level.bid_volume / upper_level.ask_volume
                    if ratio >= threshold:
                        self.imbalances.append(Imbalance(
                            price=price,
                            direction='sell',
                            ratio=ratio,
                            strong_side_volume=level.bid_volume,
                            weak_side_volume=upper_level.ask_volume
                        ))


@dataclass
class FootprintData:
    """
    Complete footprint dataset for a trade review.
    
    Contains all 15 bars of footprint data plus metadata.
    Supports serialization for Supabase caching.
    """
    trade_id: str
    symbol: str
    entry_time: datetime
    bars: List[FootprintBar] = field(default_factory=list)
    
    # Metadata
    atr_1min: float = 0.0
    tick_size: float = 0.0
    total_trades_processed: int = 0
    total_quotes_processed: int = 0
    
    def to_cache_dict(self) -> dict:
        """
        Serialize for Supabase storage.
        
        Returns:
            Dictionary ready for JSONB storage
        """
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'entry_time': self.entry_time.isoformat(),
            'atr_1min': self.atr_1min,
            'tick_size': self.tick_size,
            'total_trades': self.total_trades_processed,
            'total_quotes': self.total_quotes_processed,
            'bars': [self._bar_to_dict(bar) for bar in self.bars]
        }
    
    def _bar_to_dict(self, bar: FootprintBar) -> dict:
        """Convert single bar to dictionary."""
        return {
            'bar_start': bar.bar_start.isoformat(),
            'bar_end': bar.bar_end.isoformat(),
            'ohlc': [bar.open, bar.high, bar.low, bar.close],
            'tick_size': bar.tick_size,
            'poc_price': bar.poc_price,
            'bar_delta': bar.bar_delta,
            'price_levels': {
                str(price): {
                    'bid': level.bid_volume,
                    'ask': level.ask_volume,
                    'count': level.trade_count
                }
                for price, level in bar.price_levels.items()
            },
            'imbalances': [
                {
                    'price': imb.price,
                    'direction': imb.direction,
                    'ratio': imb.ratio
                }
                for imb in bar.imbalances
            ]
        }
    
    @classmethod
    def from_cache_dict(cls, data: dict) -> 'FootprintData':
        """
        Deserialize from Supabase storage.
        
        Args:
            data: Dictionary from JSONB column
            
        Returns:
            Reconstructed FootprintData object
        """
        fp = cls(
            trade_id=data['trade_id'],
            symbol=data['symbol'],
            entry_time=datetime.fromisoformat(data['entry_time']),
            atr_1min=data['atr_1min'],
            tick_size=data['tick_size'],
            total_trades_processed=data['total_trades'],
            total_quotes_processed=data['total_quotes']
        )
        
        for bar_data in data['bars']:
            bar = FootprintBar(
                bar_start=datetime.fromisoformat(bar_data['bar_start']),
                bar_end=datetime.fromisoformat(bar_data['bar_end']),
                open=bar_data['ohlc'][0],
                high=bar_data['ohlc'][1],
                low=bar_data['ohlc'][2],
                close=bar_data['ohlc'][3],
                tick_size=bar_data['tick_size'],
                poc_price=bar_data['poc_price'],
                bar_delta=bar_data['bar_delta']
            )
            
            # Reconstruct price levels
            for price_str, level_data in bar_data['price_levels'].items():
                price = float(price_str)
                bar.price_levels[price] = PriceLevel(
                    price=price,
                    bid_volume=level_data['bid'],
                    ask_volume=level_data['ask'],
                    trade_count=level_data['count']
                )
            
            # Reconstruct imbalances
            for imb_data in bar_data['imbalances']:
                bar.imbalances.append(Imbalance(
                    price=imb_data['price'],
                    direction=imb_data['direction'],
                    ratio=imb_data['ratio'],
                    strong_side_volume=0,  # Not stored in cache
                    weak_side_volume=0
                ))
            
            fp.bars.append(bar)
        
        return fp
Testing Examples
Create a test file to verify models work:
File: footprint/test_models.py (optional, for validation)
python"""Quick tests for data models"""

from models import PriceLevel, FootprintBar, FootprintData, TradeSide, ClassifiedTrade
from datetime import datetime
import pytz

ET = pytz.timezone('America/New_York')

def test_price_level():
    """Test PriceLevel calculations"""
    level = PriceLevel(price=150.0, bid_volume=500, ask_volume=800)
    assert level.delta == 300, f"Expected delta 300, got {level.delta}"
    assert level.total_volume == 1300, f"Expected total 1300, got {level.total_volume}"
    print("✓ PriceLevel tests passed")

def test_footprint_bar():
    """Test FootprintBar methods"""
    bar = FootprintBar(
        bar_start=ET.localize(datetime(2025, 1, 1, 9, 30)),
        bar_end=ET.localize(datetime(2025, 1, 1, 9, 31)),
        open=150.0, high=150.5, low=149.5, close=150.2,
        tick_size=0.01
    )
    
    # Add some price levels
    bar.price_levels[150.0] = PriceLevel(150.0, bid_volume=500, ask_volume=300)
    bar.price_levels[150.1] = PriceLevel(150.1, bid_volume=200, ask_volume=800)
    
    bar.calculate_poc()
    assert bar.poc_price == 150.1, "POC should be 150.1 (highest volume)"
    
    bar.calculate_bar_delta()
    assert bar.bar_delta == 400, f"Expected delta 400, got {bar.bar_delta}"
    
    print("✓ FootprintBar tests passed")

def test_serialization():
    """Test round-trip serialization"""
    bar = FootprintBar(
        bar_start=ET.localize(datetime(2025, 1, 1, 9, 30)),
        bar_end=ET.localize(datetime(2025, 1, 1, 9, 31)),
        open=150.0, high=150.5, low=149.5, close=150.2,
        tick_size=0.01
    )
    bar.price_levels[150.0] = PriceLevel(150.0, bid_volume=500, ask_volume=300)
    bar.calculate_poc()
    bar.calculate_bar_delta()
    
    fp_data = FootprintData(
        trade_id='test-123',
        symbol='SPY',
        entry_time=ET.localize(datetime(2025, 1, 1, 9, 31)),
        bars=[bar],
        atr_1min=0.5,
        tick_size=0.01
    )
    
    # Serialize
    cached = fp_data.to_cache_dict()
    
    # Deserialize
    restored = FootprintData.from_cache_dict(cached)
    
    assert restored.symbol == 'SPY'
    assert len(restored.bars) == 1
    assert restored.bars[0].poc_price == 150.0
    assert restored.bars[0].bar_delta == 200
    
    print("✓ Serialization tests passed")

if __name__ == '__main__':
    test_price_level()
    test_footprint_bar()
    test_serialization()
    print("\n✅ All model tests passed!")
Acceptance Criteria

 All dataclasses create without errors
 PriceLevel delta and total_volume properties work correctly
 FootprintBar calculate_poc() identifies highest volume price
 FootprintBar calculate_bar_delta() sums deltas correctly
 FootprintBar detect_imbalances() finds diagonal imbalances
 FootprintData serialization round-trip preserves all data
 Run: python footprint/test_models.py passes all tests


PHASE 2: API Integration (XIII-002.03)
Prerequisites

Phase 1 completed
Existing Polygon API key available
Understanding of REST APIs and pagination

Tasks

Create MassiveTickClient class and implement fetch_trades() with pagination
Add rate limiting (0.1s) and test SPY trades fetch
Implement fetch_quotes() and fetch_bars() methods
Implement _request() error handling and test quotes/bars
Create TradeClassifier class with binary search quote lookup
Implement classify() method and _tick_rule() for mid-spread trades
Test trade classification accuracy

Implementation
Part 1: Massive API Client
File: footprint/massive_client.py
python"""
Massive.com API Client for tick-level data
Extends existing Polygon integration for trades and quotes
"""

import os
import time
import requests
from datetime import datetime
from typing import Iterator, List, Dict
import pytz

from .config import MASSIVE_BASE_URL, API_RATE_LIMIT

ET = pytz.timezone('America/New_York')


class MassiveTickClient:
    """
    Client for fetching tick-level trades and quotes from Massive.com API.
    
    IMPORTANT: Reuses POLYGON_API_KEY from environment.
    The API is still accessed via polygon.io domain despite Massive rebrand.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize client.
        
        Args:
            api_key: Polygon API key (defaults to POLYGON_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not found in environment")
        
        self.base_url = MASSIVE_BASE_URL
        self.session = requests.Session()
        self.session.params = {'apiKey': self.api_key}
        self.rate_limit_delay = API_RATE_LIMIT['delay_between_requests']
    
    def fetch_trades(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 50000
    ) -> Iterator[Dict]:
        """
        Fetch all trades for a symbol within a time window.
        
        Handles pagination automatically via next_url.
        
        Args:
            symbol: Stock ticker (e.g., 'SPY', 'AAPL')
            start_time: Start of window (ET timezone aware)
            end_time: End of window (ET timezone aware)
            limit: Max results per request (max 50000)
        
        Yields:
            Trade records with: price, size, sip_timestamp, conditions, exchange
            
        Example:
            client = MassiveTickClient()
            for trade in client.fetch_trades('SPY', start, end):
                print(f"Trade at {trade['price']}, size {trade['size']}")
        """
        # Convert to nanosecond timestamps
        start_ns = int(start_time.timestamp() * 1e9)
        end_ns = int(end_time.timestamp() * 1e9)
        
        url = f"{self.base_url}/v3/trades/{symbol}"
        params = {
            'timestamp.gte': start_ns,
            'timestamp.lt': end_ns,
            'limit': limit,
            'sort': 'timestamp',
            'order': 'asc'
        }
        
        page_count = 0
        while url:
            response = self._request(url, params)
            
            results = response.get('results', [])
            if not results:
                break
            
            for trade in results:
                yield trade
            
            # Handle pagination
            url = response.get('next_url')
            params = {}  # next_url includes all params
            
            page_count += 1
            if page_count % 10 == 0:
                print(f"  Fetched {page_count} pages of trades...")
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
    
    def fetch_quotes(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 50000
    ) -> Iterator[Dict]:
        """
        Fetch NBBO quotes for a symbol within a time window.
        
        Args:
            symbol: Stock ticker
            start_time: Start of window (ET timezone aware)
            end_time: End of window (ET timezone aware)
            limit: Max results per request
        
        Yields:
            Quote records with: bid_price, bid_size, ask_price, ask_size, sip_timestamp
            
        Example:
            for quote in client.fetch_quotes('SPY', start, end):
                print(f"Bid: {quote['bid_price']}, Ask: {quote['ask_price']}")
        """
        start_ns = int(start_time.timestamp() * 1e9)
        end_ns = int(end_time.timestamp() * 1e9)
        
        url = f"{self.base_url}/v3/quotes/{symbol}"
        params = {
            'timestamp.gte': start_ns,
            'timestamp.lt': end_ns,
            'limit': limit,
            'sort': 'timestamp',
            'order': 'asc'
        }
        
        page_count = 0
        while url:
            response = self._request(url, params)
            
            results = response.get('results', [])
            if not results:
                break
            
            for quote in results:
                yield quote
            
            url = response.get('next_url')
            params = {}
            
            page_count += 1
            if page_count % 10 == 0:
                print(f"  Fetched {page_count} pages of quotes...")
            
            time.sleep(self.rate_limit_delay)
    
    def fetch_bars(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        timespan: str = 'minute',
        multiplier: int = 1
    ) -> List[Dict]:
        """
        Fetch aggregated bars (for ATR calculation).
        
        Args:
            symbol: Stock ticker
            start_time: Start of window
            end_time: End of window
            timespan: 'minute', 'hour', 'day'
            multiplier: Bar size multiplier
        
        Returns:
            List of bar records with OHLCV data (t, o, h, l, c, v)
            
        Example:
            bars = client.fetch_bars('SPY', start, end, 'minute', 1)
            for bar in bars:
                print(f"OHLC: {bar['o']}, {bar['h']}, {bar['l']}, {bar['c']}")
        """
        start_str = start_time.strftime('%Y-%m-%d')
        end_str = end_time.strftime('%Y-%m-%d')
        
        url = (
            f"{self.base_url}/v2/aggs/ticker/{symbol}/range/"
            f"{multiplier}/{timespan}/{start_str}/{end_str}"
        )
        
        params = {
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }
        
        response = self._request(url, params)
        return response.get('results', [])
    
    def _request(self, url: str, params: dict = None) -> dict:
        """
        Make API request with error handling.
        
        Args:
            url: Full URL or endpoint
            params: Query parameters
            
        Returns:
            Parsed JSON response
            
        Raises:
            requests.exceptions.RequestException on API errors
        """
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 429:
                print(f"Rate limit hit, waiting 60s...")
                time.sleep(60)
                return self._request(url, params)
            else:
                print(f"HTTP Error {resp.status_code}: {e}")
                return {'results': [], 'error': str(e)}
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return {'results': [], 'error': str(e)}
Part 2: Trade Classifier
File: footprint/classifier.py
python"""
Trade Classification Engine
Matches trades to NBBO quotes for bid/ask classification
"""

import bisect
from datetime import datetime
from typing import List, Optional

from .models import ClassifiedTrade, TradeSide


class TradeClassifier:
    """
    Classify trades as buyer or seller initiated by matching to NBBO.
    
    Algorithm:
    1. Build sorted list of quotes by timestamp
    2. For each trade, binary search for most recent quote
    3. Compare trade price to bid/ask:
       - price >= ask → buyer initiated (ASK)
       - price <= bid → seller initiated (BID)  
       - between → use tick rule or mark NEUTRAL
       
    Example:
        quotes = list(client.fetch_quotes('SPY', start, end))
        classifier = TradeClassifier(quotes)
        
        for trade in trades:
            classified = classifier.classify(trade)
            print(f"Trade side: {classified.side}")
    """
    
    def __init__(self, quotes: List[dict]):
        """
        Initialize with quotes list.
        
        Args:
            quotes: List of quote dicts from API with sip_timestamp, 
                   bid_price, ask_price
        """
        # Sort quotes by timestamp for binary search
        sorted_quotes = sorted(quotes, key=lambda q: q['sip_timestamp'])
        
        self.timestamps = [q['sip_timestamp'] for q in sorted_quotes]
        self.quotes = sorted_quotes
        self.last_trade_price: Optional[float] = None
        
        if not quotes:
            print("Warning: TradeClassifier initialized with no quotes")
    
    def classify(self, trade: dict) -> ClassifiedTrade:
        """
        Classify a single trade.
        
        Args:
            trade: Trade dict from API with sip_timestamp, price, size
        
        Returns:
            ClassifiedTrade with side assignment (BID/ASK/NEUTRAL)
        """
        trade_ts = trade['sip_timestamp']
        trade_price = trade['price']
        trade_size = trade['size']
        
        # Find most recent quote before this trade
        quote_idx = bisect.bisect_right(self.timestamps, trade_ts) - 1
        
        if quote_idx < 0:
            # No quote before this trade - use tick rule
            side = self._tick_rule(trade_price)
        else:
            quote = self.quotes[quote_idx]
            bid = quote.get('bid_price', 0)
            ask = quote.get('ask_price', float('inf'))
            
            # Classify based on price relative to bid/ask
            if trade_price >= ask:
                side = TradeSide.ASK  # Buyer lifted the offer
            elif trade_price <= bid:
                side = TradeSide.BID  # Seller hit the bid
            else:
                # Between bid and ask - use tick rule
                side = self._tick_rule(trade_price)
        
        self.last_trade_price = trade_price
        
        return ClassifiedTrade(
            timestamp=datetime.fromtimestamp(trade_ts / 1e9, tz=pytz.UTC),
            price=trade_price,
            size=trade_size,
            side=side,
            exchange=trade.get('exchange', 0),
            conditions=trade.get('conditions', [])
        )
    
    def _tick_rule(self, price: float) -> TradeSide:
        """
        Tick rule: Compare to last trade price.
        
        - Up tick → buyer initiated (ASK)
        - Down tick → seller initiated (BID)
        - No change → NEUTRAL
        
        Args:
            price: Current trade price
            
        Returns:
            TradeSide classification
        """
        if self.last_trade_price is None:
            return TradeSide.NEUTRAL
        
        if price > self.last_trade_price:
            return TradeSide.ASK
        elif price < self.last_trade_price:
            return TradeSide.BID
        else:
            return TradeSide.NEUTRAL
Testing Example
Create a simple test to verify API and classification:
File: footprint/test_api.py (optional, for validation)
python"""Test API integration and trade classification"""

from massive_client import MassiveTickClient
from classifier import TradeClassifier
from datetime import datetime, timedelta
import pytz

ET = pytz.timezone('America/New_York')

def test_fetch_data():
    """Test fetching trades and quotes"""
    client = MassiveTickClient()
    
    # Use a recent market day, 1 minute of data
    end_time = ET.localize(datetime(2024, 12, 20, 9, 31))  # Adjust to recent date
    start_time = end_time - timedelta(minutes=1)
    
    print(f"Fetching SPY data from {start_time} to {end_time}")
    
    # Fetch trades
    print("\nFetching trades...")
    trades = list(client.fetch_trades('SPY', start_time, end_time))
    print(f"✓ Fetched {len(trades)} trades")
    if trades:
        print(f"  First trade: ${trades[0]['price']} x {trades[0]['size']}")
    
    # Fetch quotes
    print("\nFetching quotes...")
    quotes = list(client.fetch_quotes('SPY', start_time, end_time))
    print(f"✓ Fetched {len(quotes)} quotes")
    if quotes:
        print(f"  First quote: ${quotes[0]['bid_price']} / ${quotes[0]['ask_price']}")
    
    # Test classification
    if trades and quotes:
        print("\nTesting classification...")
        classifier = TradeClassifier(quotes)
        
        # Classify first 5 trades
        for i, trade in enumerate(trades[:5]):
            classified = classifier.classify(trade)
            print(f"  Trade {i+1}: ${classified.price} x {classified.size} → {classified.side.value}")
        
        print("✓ Classification working")
    
    return len(trades) > 0 and len(quotes) > 0

def test_bars():
    """Test fetching bars for ATR"""
    client = MassiveTickClient()
    
    end_time = ET.localize(datetime(2024, 12, 20, 9, 31))
    start_time = end_time - timedelta(minutes=30)
    
    print(f"\nFetching 1-min bars from {start_time} to {end_time}")
    bars = client.fetch_bars('SPY', start_time, end_time, 'minute', 1)
    
    print(f"✓ Fetched {len(bars)} bars")
    if bars:
        print(f"  First bar: O:{bars[0]['o']}, H:{bars[0]['h']}, L:{bars[0]['l']}, C:{bars[0]['c']}")
    
    return len(bars) > 0

if __name__ == '__main__':
    print("Testing Massive API Client...")
    print("=" * 50)
    
    try:
        data_ok = test_fetch_data()
        bars_ok = test_bars()
        
        if data_ok and bars_ok:
            print("\n✅ All API tests passed!")
        else:
            print("\n⚠️  Some tests failed - check API key and date")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
Acceptance Criteria

 MassiveTickClient can fetch trades with pagination
 MassiveTickClient can fetch quotes with pagination
 MassiveTickClient can fetch 1-min bars
 Rate limiting works (0.1s delay between requests)
 TradeClassifier correctly classifies trades against NBBO
 Tick rule works for trades between bid/ask
 Run: python footprint/test_api.py successfully fetches data

Note: Adjust the test date in test_api.py to a recent market day when running.

PHASE 3: Processing Engine (XIII-002.04)
Prerequisites

Phase 2 completed
Understanding of ATR calculation
Familiarity with time-based data aggregation

Tasks

Create FootprintBuilder skeleton and implement _calculate_atr() method
Implement _calculate_tick_size() (ATR/20 with minimums) and test
Implement _build_bars() skeleton with 15x FootprintBar creation
Implement _round_to_tick() helper and test bar timestamps
Complete trade assignment logic in _build_bars()
Aggregate bid/ask volume per price level and handle neutral trades
Test volume aggregation accuracy
Implement build() main orchestration method
Calculate POC, delta, imbalances for all bars
Test end-to-end footprint build for real trade

Implementation
File: footprint/builder.py
python"""
Footprint Builder - Main Processing Pipeline
Orchestrates the complete footprint data construction
"""

from datetime import datetime, timedelta
from typing import List, Optional
import pytz

from .models import FootprintData, FootprintBar, PriceLevel, TradeSide
from .massive_client import MassiveTickClient
from .classifier import TradeClassifier
from .config import FOOTPRINT_CONFIG, TICK_MINIMUMS

ET = pytz.timezone('America/New_York')


class FootprintBuilder:
    """
    Build FootprintData from Massive API tick data.
    
    Workflow:
    1. Calculate time window (15 bars before entry)
    2. Fetch 1-min bars for ATR calculation
    3. Fetch trades and quotes for window
    4. Classify trades using NBBO
    5. Aggregate into FootprintBar objects
    6. Calculate POC, delta, imbalances
    
    Example:
        builder = FootprintBuilder()
        footprint = builder.build(
            trade_id='abc-123',
            symbol='SPY',
            entry_time=datetime(2025, 1, 15, 10, 30, tzinfo=ET)
        )
    """
    
    def __init__(
        self,
        client: MassiveTickClient = None,
        bar_count: int = None,
        imbalance_threshold: float = None
    ):
        """
        Initialize builder.
        
        Args:
            client: MassiveTickClient instance (creates new if None)
            bar_count: Number of bars to analyze (default from config)
            imbalance_threshold: Imbalance detection threshold (default from config)
        """
        self.client = client or MassiveTickClient()
        self.bar_count = bar_count or FOOTPRINT_CONFIG['bar_count']
        self.imbalance_threshold = (
            imbalance_threshold or FOOTPRINT_CONFIG['imbalance_threshold']
        )
        self.atr_period = FOOTPRINT_CONFIG['atr_period']
    
    def build(
        self,
        trade_id: str,
        symbol: str,
        entry_time: datetime
    ) -> FootprintData:
        """
        Build complete footprint data for a trade.
        
        This is the main entry point for footprint generation.
        
        Args:
            trade_id: UUID of the trade record
            symbol: Stock ticker (e.g., 'SPY')
            entry_time: Trade entry timestamp (ET timezone aware)
        
        Returns:
            FootprintData with all bars populated and metrics calculated
        """
        # Ensure timezone aware
        if entry_time.tzinfo is None:
            entry_time = ET.localize(entry_time)
        
        # Calculate window: bar_count minutes before entry
        window_start = entry_time - timedelta(minutes=self.bar_count)
        window_end = entry_time
        
        print(f"\n{'='*60}")
        print(f"Building footprint for {symbol}")
        print(f"Window: {window_start.strftime('%Y-%m-%d %H:%M')} → "
              f"{window_end.strftime('%H:%M')} ET")
        print(f"{'='*60}")
        
        # Step 1: Fetch 1-min bars for ATR calculation
        # Need extra bars for proper ATR (use 30 bars = 2x ATR period)
        atr_start = entry_time - timedelta(minutes=30)
        print(f"\n[1/5] Fetching bars for ATR calculation...")
        bars = self.client.fetch_bars(
            symbol, atr_start, window_end, 'minute', 1
        )
        print(f"      Retrieved {len(bars)} bars")
        
        atr = self._calculate_atr(bars)
        tick_size = self._calculate_tick_size(atr, bars)
        
        print(f"      ATR (1-min): ${atr:.4f}")
        print(f"      Tick size: ${tick_size:.4f}")
        
        # Step 2: Fetch trades
        print(f"\n[2/5] Fetching trades...")
        trades = list(self.client.fetch_trades(symbol, window_start, window_end))
        print(f"      Retrieved {len(trades):,} trades")
        
        # Step 3: Fetch quotes
        print(f"\n[3/5] Fetching quotes...")
        quotes = list(self.client.fetch_quotes(symbol, window_start, window_end))
        print(f"      Retrieved {len(quotes):,} quotes")
        
        # Step 4: Classify trades
        print(f"\n[4/5] Classifying trades...")
        classifier = TradeClassifier(quotes)
        classified_trades = [classifier.classify(t) for t in trades]
        
        # Count classifications
        bid_count = sum(1 for t in classified_trades if t.side == TradeSide.BID)
        ask_count = sum(1 for t in classified_trades if t.side == TradeSide.ASK)
        neutral_count = sum(1 for t in classified_trades if t.side == TradeSide.NEUTRAL)
        print(f"      Bid: {bid_count:,}, Ask: {ask_count:,}, Neutral: {neutral_count:,}")
        
        # Step 5: Build bar structure
        print(f"\n[5/5] Aggregating into {self.bar_count} footprint bars...")
        footprint_bars = self._build_bars(
            classified_trades, bars, window_start, window_end, tick_size
        )
        
        # Step 6: Calculate metrics
        for i, bar in enumerate(footprint_bars):
            bar.calculate_poc()
            bar.calculate_bar_delta()
            bar.detect_imbalances(self.imbalance_threshold)
        
        print(f"      Complete!")
        print(f"\n{'='*60}")
        
        return FootprintData(
            trade_id=trade_id,
            symbol=symbol,
            entry_time=entry_time,
            bars=footprint_bars,
            atr_1min=atr,
            tick_size=tick_size,
            total_trades_processed=len(trades),
            total_quotes_processed=len(quotes)
        )
    
    def _calculate_atr(self, bars: List[dict], period: int = None) -> float:
        """
        Calculate Average True Range from bars.
        
        True Range = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        
        Args:
            bars: List of OHLC bars from API
            period: ATR period (default from config)
            
        Returns:
            Average True Range value
        """
        if not period:
            period = self.atr_period
        
        if len(bars) < 2:
            return 0.01  # Default minimum
        
        true_ranges = []
        for i in range(1, len(bars)):
            high = bars[i]['h']
            low = bars[i]['l']
            prev_close = bars[i-1]['c']
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        if not true_ranges:
            return 0.01
        
        # Use last 'period' TRs or all if fewer
        recent_trs = true_ranges[-period:]
        return sum(recent_trs) / len(recent_trs)
    
    def _calculate_tick_size(self, atr: float, bars: List[dict]) -> float:
        """
        Calculate tick size as ATR / 20.
        
        Apply minimum tick based on price level:
        - Price < $1: min tick $0.0001
        - Price >= $1: min tick $0.01
        
        Args:
            atr: Calculated ATR value
            bars: OHLC bars (for price context)
            
        Returns:
            Tick size for price level rounding
        """
        if not bars:
            return TICK_MINIMUMS['default']
        
        # Get typical price from recent bars
        recent_close = bars[-1]['c'] if bars else 100
        
        # Calculate ATR-based tick
        atr_tick = atr / FOOTPRINT_CONFIG['tick_levels']
        
        # Apply minimums based on price
        if recent_close < 1:
            min_tick = TICK_MINIMUMS['sub_dollar']
        else:
            min_tick = TICK_MINIMUMS['default']
        
        # Round to sensible precision
        tick = max(atr_tick, min_tick)
        
        # Round to nearest cent or sub-cent
        if tick >= 0.01:
            tick = round(tick, 2)
        else:
            tick = round(tick, 4)
        
        return tick
    
    def _build_bars(
        self,
        trades: List,
        ohlc_bars: List[dict],
        window_start: datetime,
        window_end: datetime,
        tick_size: float
    ) -> List[FootprintBar]:
        """
        Build FootprintBar objects from classified trades.
        
        Aligns trades to 1-minute bars and aggregates by price level.
        
        Args:
            trades: List of ClassifiedTrade objects
            ohlc_bars: OHLC data from API for structure
            window_start: Start of analysis window
            window_end: End of analysis window
            tick_size: Price rounding precision
            
        Returns:
            List of FootprintBar objects with populated price levels
        """
        # Create bar lookup from OHLC data
        bar_lookup = {}
        for bar in ohlc_bars:
            bar_time = datetime.fromtimestamp(bar['t'] / 1000, tz=ET)
            bar_lookup[bar_time] = bar
        
        # Initialize footprint bars
        footprint_bars = []
        current_time = window_start.replace(second=0, microsecond=0)
        
        while current_time < window_end:
            bar_end = current_time + timedelta(minutes=1)
            
            # Get OHLC if available
            ohlc = bar_lookup.get(current_time, {})
            
            fp_bar = FootprintBar(
                bar_start=current_time,
                bar_end=bar_end,
                open=ohlc.get('o', 0),
                high=ohlc.get('h', 0),
                low=ohlc.get('l', 0),
                close=ohlc.get('c', 0),
                tick_size=tick_size
            )
            footprint_bars.append(fp_bar)
            current_time = bar_end
        
        # Assign trades to bars and price levels
        for trade in trades:
            # Ensure timezone aware
            trade_time = trade.timestamp
            if trade_time.tzinfo is None:
                trade_time = ET.localize(trade_time)
            else:
                trade_time = trade_time.astimezone(ET)
            
            # Find containing bar
            bar_idx = None
            for i, bar in enumerate(footprint_bars):
                if bar.bar_start <= trade_time < bar.bar_end:
                    bar_idx = i
                    break
            
            if bar_idx is None:
                continue  # Trade outside window
            
            bar = footprint_bars[bar_idx]
            
            # Round price to tick size
            price_level = self._round_to_tick(trade.price, tick_size)
            
            # Get or create price level
            if price_level not in bar.price_levels:
                bar.price_levels[price_level] = PriceLevel(price=price_level)
            
            level = bar.price_levels[price_level]
            level.trade_count += 1
            
            # Aggregate volume by side
            if trade.side == TradeSide.BID:
                level.bid_volume += trade.size
            elif trade.side == TradeSide.ASK:
                level.ask_volume += trade.size
            else:
                # Split neutral evenly
                level.bid_volume += trade.size // 2
                level.ask_volume += trade.size - (trade.size // 2)
        
        return footprint_bars
    
    def _round_to_tick(self, price: float, tick_size: float) -> float:
        """
        Round price to nearest tick size.
        
        Args:
            price: Raw price
            tick_size: Rounding precision
            
        Returns:
            Price rounded to tick size
        """
        return round(round(price / tick_size) * tick_size, 4)
Testing Example
File: footprint/test_builder.py (optional, for validation)
python"""Test footprint builder end-to-end"""

from builder import FootprintBuilder
from datetime import datetime
import pytz

ET = pytz.timezone('America/New_York')

def test_build_footprint():
    """Test complete footprint build"""
    builder = FootprintBuilder()
    
    # Use a recent market day
    entry_time = ET.localize(datetime(2024, 12, 20, 10, 0))  # Adjust date
    
    try:
        footprint = builder.build(
            trade_id='test-001',
            symbol='SPY',
            entry_time=entry_time
        )
        
        print(f"\n✅ Footprint built successfully!")
        print(f"   Symbol: {footprint.symbol}")
        print(f"   Bars: {len(footprint.bars)}")
        print(f"   ATR: ${footprint.atr_1min:.4f}")
        print(f"   Tick: ${footprint.tick_size:.4f}")
        print(f"   Trades processed: {footprint.total_trades_processed:,}")
        print(f"   Quotes processed: {footprint.total_quotes_processed:,}")
        
        # Show first bar details
        if footprint.bars:
            bar = footprint.bars[0]
            print(f"\n   First bar ({bar.bar_start.strftime('%H:%M')}):")
            print(f"     Price levels: {len(bar.price_levels)}")
            print(f"     POC: ${bar.poc_price:.2f}" if bar.poc_price else "     POC: None")
            print(f"     Delta: {bar.bar_delta:+,}")
            print(f"     Imbalances: {len(bar.imbalances)}")
        
        return True
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Testing Footprint Builder...")
    print("=" * 60)
    test_build_footprint()
Acceptance Criteria

 FootprintBuilder._calculate_atr() returns reasonable ATR values
 FootprintBuilder._calculate_tick_size() applies correct minimums
 FootprintBuilder._build_bars() creates exactly 15 bars
 Bars have correct start/end timestamps
 Trades are assigned to correct bars
 Price levels aggregate bid/ask volume correctly
 Neutral trades are split 50/50
 POC is calculated for each bar
 Bar delta is calculated correctly
 Imbalances are detected when threshold met
 Run: python footprint/test_builder.py successfully builds footprint

CHECKPOINT: You can now build complete footprint data from API!

PHASE 4: Supabase Caching (XIII-002.05)
Prerequisites

Phase 3 completed
Supabase project exists
Access to Supabase client from existing infrastructure

Tasks

Write and run SQL migration for footprint_cache table
Create footprint_exists() helper function and test
Create FootprintCache class with get() method
Implement save(), exists(), delete() methods
Test save/retrieve cycle with real footprint data

Implementation
Part 1: Database Schema
File: migrations/create_footprint_cache.sql (create in your migrations folder)
sql-- Footprint Cache Table
-- Store processed footprint data to avoid re-fetching from Massive API

CREATE TABLE IF NOT EXISTS footprint_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id UUID NOT NULL,  -- References trades(id), but we won't enforce FK for flexibility
    symbol TEXT NOT NULL,
    entry_time TIMESTAMPTZ NOT NULL,
    
    -- Processing metadata
    atr_1min NUMERIC(10, 6),
    tick_size NUMERIC(10, 6),
    total_trades_processed INTEGER,
    total_quotes_processed INTEGER,
    
    -- Serialized footprint data (JSONB for query flexibility)
    bars_data JSONB NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Prevent duplicate entries
    UNIQUE(trade_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_footprint_cache_trade_id 
    ON footprint_cache(trade_id);

CREATE INDEX IF NOT EXISTS idx_footprint_cache_symbol_time 
    ON footprint_cache(symbol, entry_time DESC);

-- Helper function to check existence
CREATE OR REPLACE FUNCTION footprint_exists(p_trade_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM footprint_cache WHERE trade_id = p_trade_id
    );
END;
$$ LANGUAGE plpgsql;

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_footprint_cache_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_footprint_cache_updated_at
    BEFORE UPDATE ON footprint_cache
    FOR EACH ROW
    EXECUTE FUNCTION update_footprint_cache_updated_at();

-- Grant permissions (adjust role as needed)
-- ALTER TABLE footprint_cache OWNER TO your_role;

COMMENT ON TABLE footprint_cache IS 'Cached footprint chart data to avoid re-fetching tick data from Massive API';
COMMENT ON COLUMN footprint_cache.bars_data IS '15x 1-minute bars with price level volumes, POC, delta, and imbalances';
To run migration:

Copy SQL to Supabase SQL Editor
Execute
Verify table created: SELECT * FROM footprint_cache LIMIT 0;

Part 2: Cache Manager
File: footprint/cache.py
python"""
Supabase Caching Layer for Footprint Data
Avoids expensive API re-fetching
"""

from datetime import datetime
from typing import Optional
from supabase import Client

from .models import FootprintData


class FootprintCache:
    """
    Cache footprint data in Supabase to avoid re-fetching.
    
    IMPORTANT: Reuse existing Supabase client from your infrastructure.
    
    Example:
        from data.supabase_client import get_supabase_client
        
        supabase = get_supabase_client()
        cache = FootprintCache(supabase)
        
        # Check cache
        footprint = cache.get(trade_id)
        if footprint is None:
            # Build and save
            footprint = builder.build(...)
            cache.save(footprint)
    """
    
    def __init__(self, supabase: Client):
        """
        Initialize cache with Supabase client.
        
        Args:
            supabase: Existing Supabase client from your infrastructure
        """
        self.supabase = supabase
        self.table_name = 'footprint_cache'
    
    def get(self, trade_id: str) -> Optional[FootprintData]:
        """
        Retrieve cached footprint data for a trade.
        
        Args:
            trade_id: Trade UUID
            
        Returns:
            FootprintData if cached, None if not found
        """
        try:
            result = self.supabase.table(self.table_name) \
                .select('*') \
                .eq('trade_id', trade_id) \
                .execute()
            
            if not result.data:
                return None
            
            row = result.data[0]
            
            # Reconstruct FootprintData from cached JSONB
            cache_dict = {
                'trade_id': row['trade_id'],
                'symbol': row['symbol'],
                'entry_time': row['entry_time'],
                'atr_1min': float(row['atr_1min']) if row['atr_1min'] else 0.0,
                'tick_size': float(row['tick_size']) if row['tick_size'] else 0.0,
                'total_trades': row['total_trades_processed'] or 0,
                'total_quotes': row['total_quotes_processed'] or 0,
                'bars': row['bars_data']
            }
            
            return FootprintData.from_cache_dict(cache_dict)
        
        except Exception as e:
            print(f"Error retrieving from cache: {e}")
            return None
    
    def save(self, footprint: FootprintData):
        """
        Save footprint data to cache.
        
        Uses upsert to handle re-processing (overwrites if exists).
        
        Args:
            footprint: Complete FootprintData object
        """
        try:
            cache_dict = footprint.to_cache_dict()
            
            self.supabase.table(self.table_name).upsert({
                'trade_id': footprint.trade_id,
                'symbol': footprint.symbol,
                'entry_time': footprint.entry_time.isoformat(),
                'atr_1min': footprint.atr_1min,
                'tick_size': footprint.tick_size,
                'total_trades_processed': footprint.total_trades_processed,
                'total_quotes_processed': footprint.total_quotes_processed,
                'bars_data': cache_dict['bars']
            }).execute()
            
            print(f"✓ Cached footprint for trade {footprint.trade_id}")
        
        except Exception as e:
            print(f"Error saving to cache: {e}")
            # Don't raise - caching failure shouldn't break the app
    
    def exists(self, trade_id: str) -> bool:
        """
        Check if footprint data is cached.
        
        Args:
            trade_id: Trade UUID
            
        Returns:
            True if cached, False otherwise
        """
        try:
            result = self.supabase.rpc(
                'footprint_exists', 
                {'p_trade_id': trade_id}
            ).execute()
            return result.data if result.data else False
        except Exception as e:
            print(f"Error checking cache: {e}")
            return False
    
    def delete(self, trade_id: str):
        """
        Delete cached footprint data.
        
        Useful for forcing re-processing or cleanup.
        
        Args:
            trade_id: Trade UUID
        """
        try:
            self.supabase.table(self.table_name) \
                .delete() \
                .eq('trade_id', trade_id) \
                .execute()
            
            print(f"✓ Deleted cached footprint for trade {trade_id}")
        except Exception as e:
            print(f"Error deleting from cache: {e}")
    
    def count(self) -> int:
        """
        Get count of cached footprints.
        
        Returns:
            Number of cached footprints
        """
        try:
            result = self.supabase.table(self.table_name) \
                .select('id', count='exact') \
                .execute()
            return result.count if hasattr(result, 'count') else 0
        except Exception as e:
            print(f"Error counting cache: {e}")
            return 0
Testing Example
File: footprint/test_cache.py (optional, for validation)
python"""Test Supabase caching"""

from cache import FootprintCache
from builder import FootprintBuilder
from datetime import datetime
import pytz

# Import your existing Supabase client
# Adjust this import to match your project structure
from data.supabase_client import get_supabase_client

ET = pytz.timezone('America/New_York')

def test_cache_workflow():
    """Test complete cache workflow"""
    # Get Supabase client
    supabase = get_supabase_client()
    cache = FootprintCache(supabase)
    
    print(f"Current cache count: {cache.count()}")
    
    # Test trade
    test_trade_id = 'test-cache-001'
    
    # Check if exists
    print(f"\nChecking cache for {test_trade_id}...")
    if cache.exists(test_trade_id):
        print("  Already cached - deleting for test")
        cache.delete(test_trade_id)
    
    # Build footprint
    print("\nBuilding footprint...")
    builder = FootprintBuilder()
    entry_time = ET.localize(datetime(2024, 12, 20, 10, 0))  # Adjust date
    
    footprint = builder.build(
        trade_id=test_trade_id,
        symbol='SPY',
        entry_time=entry_time
    )
    
    # Save to cache
    print("\nSaving to cache...")
    cache.save(footprint)
    
    # Retrieve from cache
    print("\nRetrieving from cache...")
    cached_footprint = cache.get(test_trade_id)
    
    if cached_footprint:
        print("✓ Retrieved from cache")
        print(f"  Symbol: {cached_footprint.symbol}")
        print(f"  Bars: {len(cached_footprint.bars)}")
        print(f"  ATR: ${cached_footprint.atr_1min:.4f}")
        print(f"  Matches original: {len(cached_footprint.bars) == len(footprint.bars)}")
        
        # Clean up
        print("\nCleaning up test data...")
        cache.delete(test_trade_id)
        
        return True
    else:
        print("❌ Failed to retrieve from cache")
        return False

if __name__ == '__main__':
    print("Testing Footprint Cache...")
    print("=" * 60)
    test_cache_workflow()
Acceptance Criteria

 footprint_cache table exists in Supabase
 footprint_exists() function works
 FootprintCache.save() stores data
 FootprintCache.get() retrieves data
 Retrieved data matches original (round-trip)
 FootprintCache.exists() returns correct boolean
 FootprintCache.delete() removes data
 Run: python footprint/test_cache.py completes successfully

CHECKPOINT: Caching working - API fetching only needed once per trade!

PHASE 5: Visualization (XIII-002.06)
Prerequisites

Phase 4 completed
Understanding of Plotly
Familiarity with heatmap/chart visualization

Tasks

Create FootprintRenderer class with color scheme
Implement render() skeleton and _empty_chart()
Test empty chart rendering
Implement _render_bar() with bid/ask column drawing
Implement _get_intensity_color() for volume opacity
Add price labels and bar delta annotations
Test single bar rendering visually
Add POC diamond markers (yellow)
Add imbalance highlighting (bright green/red)
Add hover tooltips and test complete chart

Implementation
File: footprint/visualization.py
python"""
Plotly Footprint Renderer
Traditional footprint chart visualization for Streamlit
"""

import plotly.graph_objects as go
from typing import Optional

from .models import FootprintData, FootprintBar
from .config import FOOTPRINT_COLORS, CHART_CONFIG


class FootprintRenderer:
    """
    Render FootprintData as traditional footprint chart.
    
    Layout per bar:
    ┌─────────────────┐
    │ Bid │ Price│ Ask│
    │ Vol │      │ Vol│
    ├─────┼──────┼────┤
    │ 500 │150.05│ 800│ ← POC highlighted
    │ 300 │150.00│ 200│
    │ 100 │149.95│ 150│
    └─────┴──────┴────┘
    
    Example:
        renderer = FootprintRenderer()
        fig = renderer.render(footprint_data)
        fig.show()  # Or use in Streamlit: st.plotly_chart(fig)
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize renderer.
        
        Args:
            config: Optional config overrides (uses CHART_CONFIG defaults)
        """
        self.config = config or CHART_CONFIG
        self.colors = FOOTPRINT_COLORS
        self.bar_width = self.config.get('bar_width', 80) / 100  # Convert to plot units
    
    def render(
        self,
        footprint: FootprintData,
        height: int = None
    ) -> go.Figure:
        """
        Render complete footprint chart.
        
        Args:
            footprint: FootprintData object with all bars
            height: Chart height in pixels (default from config)
        
        Returns:
            Plotly Figure object ready for display
        """
        if not footprint.bars:
            return self._empty_chart("No footprint data available")
        
        height = height or self.config['default_height']
        
        # Calculate layout dimensions
        n_bars = len(footprint.bars)
        
        # Find global price range across all bars
        all_prices = []
        for bar in footprint.bars:
            all_prices.extend(bar.price_levels.keys())
        
        if not all_prices:
            return self._empty_chart("No trade data in window")
        
        min_price = min(all_prices)
        max_price = max(all_prices)
        tick_size = footprint.tick_size
        
        # Create figure
        fig = go.Figure()
        
        # Render each bar
        for bar_idx, bar in enumerate(footprint.bars):
            self._render_bar(fig, bar, bar_idx, min_price, max_price, tick_size)
        
        # Update layout
        fig.update_layout(
            height=height,
            paper_bgcolor=self.colors['background'],
            plot_bgcolor=self.colors['background'],
            font=dict(color=self.colors['text'], size=10),
            showlegend=False,
            margin=dict(l=60, r=20, t=50, b=60),
            hovermode='closest',
            xaxis=dict(
                title="Time",
                showgrid=True,
                gridcolor=self.colors['grid'],
                tickmode='array',
                tickvals=list(range(n_bars)),
                ticktext=[
                    bar.bar_start.strftime('%H:%M') 
                    for bar in footprint.bars
                ],
                range=[-0.5, n_bars - 0.5]
            ),
            yaxis=dict(
                title="Price",
                showgrid=True,
                gridcolor=self.colors['grid'],
                tickformat='.2f',
                range=[min_price - tick_size * 2, max_price + tick_size * 2]
            ),
            title=dict(
                text=(
                    f"<b>Footprint Chart</b> - {footprint.symbol} | "
                    f"Tick: ${tick_size:.4f} | "
                    f"{footprint.total_trades_processed:,} trades"
                ),
                x=0.5,
                xanchor='center',
                font=dict(size=14)
            )
        )
        
        return fig
    
    def _render_bar(
        self,
        fig: go.Figure,
        bar: FootprintBar,
        bar_idx: int,
        min_price: float,
        max_price: float,
        tick_size: float
    ):
        """
        Render a single footprint bar.
        
        Draws bid column (left, red), ask column (right, green),
        POC markers, and bar delta.
        """
        if not bar.price_levels:
            return
        
        # Find max volume for color intensity scaling within this bar
        max_vol = max(
            max(level.bid_volume, level.ask_volume)
            for level in bar.price_levels.values()
        ) or 1
        
        # Create set of imbalance prices for highlighting
        buy_imbalance_prices = {
            imb.price for imb in bar.imbalances if imb.direction == 'buy'
        }
        sell_imbalance_prices = {
            imb.price for imb in bar.imbalances if imb.direction == 'sell'
        }
        
        # Render each price level
        for price, level in bar.price_levels.items():
            # Determine if special highlighting needed
            is_poc = (price == bar.poc_price)
            has_buy_imbalance = price in buy_imbalance_prices
            has_sell_imbalance = price in sell_imbalance_prices
            
            # Calculate color intensities
            bid_intensity = level.bid_volume / max_vol
            ask_intensity = level.ask_volume / max_vol
            
            # Get colors (override for imbalances)
            bid_color = self._get_intensity_color(
                self.colors['imbalance_sell'] if has_sell_imbalance 
                else self.colors['bid'],
                bid_intensity if not has_sell_imbalance else 1.0
            )
            
            ask_color = self._get_intensity_color(
                self.colors['imbalance_buy'] if has_buy_imbalance 
                else self.colors['ask'],
                ask_intensity if not has_buy_imbalance else 1.0
            )
            
            # Draw bid cell (left of center)
            fig.add_trace(go.Scatter(
                x=[bar_idx - self.bar_width/2, bar_idx - 0.02],
                y=[price, price],
                mode='lines+text',
                line=dict(color=bid_color, width=18),
                text=[f"{level.bid_volume:,}" if level.bid_volume > 0 else "", ""],
                textposition="middle center",
                textfont=dict(size=8, color='white'),
                hovertemplate=(
                    f"<b>{bar.bar_start.strftime('%H:%M')}</b><br>"
                    f"Price: ${price:.2f}<br>"
                    f"Bid Volume: {level.bid_volume:,}<br>"
                    f"<extra></extra>"
                ),
                showlegend=False
            ))
            
            # Draw ask cell (right of center)
            fig.add_trace(go.Scatter(
                x=[bar_idx + 0.02, bar_idx + self.bar_width/2],
                y=[price, price],
                mode='lines+text',
                line=dict(color=ask_color, width=18),
                text=["", f"{level.ask_volume:,}" if level.ask_volume > 0 else ""],
                textposition="middle center",
                textfont=dict(size=8, color='white'),
                hovertemplate=(
                    f"<b>{bar.bar_start.strftime('%H:%M')}</b><br>"
                    f"Price: ${price:.2f}<br>"
                    f"Ask Volume: {level.ask_volume:,}<br>"
                    f"<extra></extra>"
                ),
                showlegend=False
            ))
            
            # POC marker
            if is_poc:
                fig.add_trace(go.Scatter(
                    x=[bar_idx],
                    y=[price],
                    mode='markers',
                    marker=dict(
                        symbol='diamond',
                        size=10,
                        color=self.colors['poc'],
                        line=dict(color=self.colors['background'], width=1)
                    ),
                    hovertemplate=(
                        f"<b>Point of Control</b><br>"
                        f"${price:.2f}<br>"
                        f"Total Volume: {level.total_volume:,}<br>"
                        f"<extra></extra>"
                    ),
                    showlegend=False
                ))
        
        # Add bar delta annotation at top
        if bar.price_levels:
            max_bar_price = max(bar.price_levels.keys())
            delta_color = self.colors['ask'] if bar.bar_delta > 0 else self.colors['bid']
            
            fig.add_annotation(
                x=bar_idx,
                y=max_bar_price + tick_size * 1.5,
                text=f"Δ {bar.bar_delta:+,}",
                font=dict(size=9, color=delta_color, family='monospace'),
                showarrow=False,
                bgcolor=self.colors['background'],
                bordercolor=delta_color,
                borderwidth=1,
                borderpad=2
            )
    
    def _get_intensity_color(self, base_color: str, intensity: float) -> str:
        """
        Adjust color intensity based on volume.
        
        Higher volume = more saturated color.
        
        Args:
            base_color: Hex color code (e.g., '#ef5350')
            intensity: 0.0 to 1.0
            
        Returns:
            RGBA color string
        """
        # Intensity range: 0.3 (light) to 1.0 (full)
        alpha = 0.3 + (intensity * 0.7)
        
        # Convert hex to RGB
        r = int(base_color[1:3], 16)
        g = int(base_color[3:5], 16)
        b = int(base_color[5:7], 16)
        
        return f'rgba({r},{g},{b},{alpha})'
    
    def _empty_chart(self, message: str) -> go.Figure:
        """
        Return empty chart with message.
        
        Args:
            message: Message to display
            
        Returns:
            Plotly figure with centered message
        """
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text=message,
            font=dict(size=16, color=self.colors['text']),
            showarrow=False,
            xref='paper', yref='paper'
        )
        fig.update_layout(
            height=200,
            paper_bgcolor=self.colors['background'],
            plot_bgcolor=self.colors['background'],
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            margin=dict(l=20, r=20, t=20, b=20)
        )
        return fig


def render_footprint_streamlit(footprint: FootprintData, height: int = None) -> go.Figure:
    """
    Convenience function for Streamlit integration.
    
    Usage in Streamlit:
        from footprint.visualization import render_footprint_streamlit
        
        fig = render_footprint_streamlit(footprint_data)
        st.plotly_chart(fig, use_container_width=True)
    
    Args:
        footprint: FootprintData object
        height: Chart height in pixels
        
    Returns:
        Plotly Figure
    """
    renderer = FootprintRenderer()
    return renderer.render(footprint, height)


def render_heatmap_view(footprint: FootprintData, height: int = None) -> go.Figure:
    """
    Alternative visualization: Delta heatmap.
    
    X-axis: Time (bars)
    Y-axis: Price
    Color: Delta (green positive, red negative)
    
    Args:
        footprint: FootprintData object
        height: Chart height in pixels
        
    Returns:
        Plotly Figure with heatmap
    """
    import numpy as np
    
    if not footprint.bars:
        return FootprintRenderer()._empty_chart("No data")
    
    height = height or CHART_CONFIG['default_height']
    
    # Build price list
    all_prices = set()
    for bar in footprint.bars:
        all_prices.update(bar.price_levels.keys())
    
    sorted_prices = sorted(all_prices)
    n_prices = len(sorted_prices)
    n_bars = len(footprint.bars)
    
    # Create delta matrix
    delta_matrix = np.zeros((n_prices, n_bars))
    
    for bar_idx, bar in enumerate(footprint.bars):
        for price_idx, price in enumerate(sorted_prices):
            if price in bar.price_levels:
                delta_matrix[price_idx, bar_idx] = bar.price_levels[price].delta
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=delta_matrix,
        x=[bar.bar_start.strftime('%H:%M') for bar in footprint.bars],
        y=[f"${p:.2f}" for p in sorted_prices],
        colorscale=[
            [0, FOOTPRINT_COLORS['bid']],      # Red for negative
            [0.5, FOOTPRINT_COLORS['grid']],   # Dark for neutral
            [1, FOOTPRINT_COLORS['ask']]       # Green for positive
        ],
        zmid=0,
        colorbar=dict(
            title="Delta",
            titlefont=dict(color=FOOTPRINT_COLORS['text']),
            tickfont=dict(color=FOOTPRINT_COLORS['text'])
        ),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Price: %{y}<br>"
            "Delta: %{z:+,}<br>"
            "<extra></extra>"
        )
    ))
    
    fig.update_layout(
        height=height,
        title=dict(
            text=f"<b>Delta Heatmap</b> - {footprint.symbol}",
            x=0.5,
            xanchor='center',
            font=dict(size=14, color=FOOTPRINT_COLORS['text'])
        ),
        paper_bgcolor=FOOTPRINT_COLORS['background'],
        plot_bgcolor=FOOTPRINT_COLORS['background'],
        font=dict(color=FOOTPRINT_COLORS['text']),
        xaxis=dict(
            title="Time",
            gridcolor=FOOTPRINT_COLORS['grid']
        ),
        yaxis=dict(
            title="Price",
            gridcolor=FOOTPRINT_COLORS['grid']
        )
    )
    
    return fig
Testing Example
Create a simple visualization test:
File: footprint/test_visualization.py (optional)
python"""Test footprint visualization"""

from visualization import FootprintRenderer, render_heatmap_view
from builder import FootprintBuilder
from datetime import datetime
import pytz

ET = pytz.timezone('America/New_York')

def test_render():
    """Test footprint rendering"""
    # Build footprint
    builder = FootprintBuilder()
    entry_time = ET.localize(datetime(2024, 12, 20, 10, 0))  # Adjust date
    
    footprint = builder.build(
        trade_id='test-viz',
        symbol='SPY',
        entry_time=entry_time
    )
    
    # Render traditional footprint
    print("Rendering footprint chart...")
    renderer = FootprintRenderer()
    fig = renderer.render(footprint)
    fig.write_html('footprint_test.html')
    print("✓ Saved to footprint_test.html")
    
    # Render heatmap
    print("\nRendering heatmap...")
    fig_heatmap = render_heatmap_view(footprint)
    fig_heatmap.write_html('heatmap_test.html')
    print("✓ Saved to heatmap_test.html")
    
    print("\n✅ Open the HTML files in a browser to view charts")

if __name__ == '__main__':
    test_render()
Acceptance Criteria

 FootprintRenderer creates figure without errors
 Empty chart displays message correctly
 Bid columns render on left (red)
 Ask columns render on right (green)
 Volume intensity affects color opacity
 Price labels display correctly
 Bar delta annotations appear at top of bars
 POC shows yellow diamond at correct price
 Imbalances show bright colors
 Hover tooltips work and show details
 Heatmap view renders delta distribution
 Run: python footprint/test_visualization.py generates viewable HTML charts

CHECKPOINT: Full footprint visualization working!

PHASE 6: Streamlit Integration (XIII-002.07)
Prerequisites

Phase 5 completed
Existing Streamlit trade review app
Access to Supabase client in app

Tasks

Create render_footprint_panel() in components/footprint_panel.py
Add cache check, spinner, and metadata display
Add imbalance details expander
Test panel in standalone Streamlit app
Import and integrate footprint panel in main app.py
Test with multiple trades and verify cache behavior

Implementation
File: components/footprint_panel.py
python"""
Footprint Panel Component
Streamlit component for displaying footprint charts in trade review
"""

import streamlit as st
from typing import Optional
from datetime import datetime

# Adjust these imports to match your project structure
from footprint.builder import FootprintBuilder
from footprint.cache import FootprintCache
from footprint.visualization import render_footprint_streamlit, render_heatmap_view
from footprint.models import FootprintData


def render_footprint_panel(
    trade_id: str,
    symbol: str,
    entry_time: datetime,
    supabase_client,
    show_heatmap_toggle: bool = True
):
    """
    Render footprint chart panel in trade review.
    
    Integrates between M15/H1 charts and statistics table.
    Handles cache checking, data building, and visualization.
    
    Args:
        trade_id: UUID of the trade
        symbol: Stock ticker (e.g., 'SPY')
        entry_time: Trade entry timestamp
        supabase_client: Existing Supabase client from app
        show_heatmap_toggle: Whether to show view toggle (default True)
        
    Example:
        In your main app.py:
        
        render_footprint_panel(
            trade_id=current_trade.id,
            symbol=current_trade.symbol,
            entry_time=current_trade.entry_time,
            supabase_client=supabase,
            show_heatmap_toggle=True
        )
    """
    st.markdown("---")
    st.markdown("### 📊 Footprint Analysis")
    st.caption("15-minute order flow analysis prior to trade entry")
    
    # Initialize cache
    cache = FootprintCache(supabase_client)
    
    # Check cache first
    footprint: Optional[FootprintData] = cache.get(trade_id)
    
    if footprint is None:
        # Need to build footprint
        with st.spinner("🔄 Building footprint chart (fetching tick data)..."):
            try:
                builder = FootprintBuilder()
                footprint = builder.build(trade_id, symbol, entry_time)
                
                # Cache for future use
                cache.save(footprint)
                
                st.success(
                    f"✓ Processed {footprint.total_trades_processed:,} trades, "
                    f"{footprint.total_quotes_processed:,} quotes"
                )
            except Exception as e:
                st.error(f"❌ Error building footprint: {e}")
                st.info(
                    "This could be due to:\n"
                    "- No market data available for this timestamp\n"
                    "- API rate limits\n"
                    "- Network issues"
                )
                return
    else:
        st.caption("📦 Loaded from cache")
    
    # View toggle (optional)
    view_type = "Footprint"  # Default
    if show_heatmap_toggle:
        col1, col2, col_spacer = st.columns([1, 1, 6])
        with col1:
            if st.button("📈 Footprint", use_container_width=True, key=f"fp_btn_{trade_id}"):
                view_type = "Footprint"
        with col2:
            if st.button("🔥 Heatmap", use_container_width=True, key=f"hm_btn_{trade_id}"):
                view_type = "Heatmap"
    
    # Display metadata metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("1-Min ATR", f"${footprint.atr_1min:.4f}")
    
    with col2:
        st.metric("Tick Size", f"${footprint.tick_size:.4f}")
    
    with col3:
        # Calculate total delta across all bars
        total_delta = sum(bar.bar_delta for bar in footprint.bars)
        delta_icon = "🟢" if total_delta > 0 else "🔴" if total_delta < 0 else "⚪"
        st.metric("Total Delta", f"{delta_icon} {total_delta:+,}")
    
    with col4:
        # Count imbalances
        total_imbalances = sum(len(bar.imbalances) for bar in footprint.bars)
        st.metric("Imbalances", total_imbalances)
    
    # Render appropriate chart
    if view_type == "Heatmap":
        fig = render_heatmap_view(footprint, height=450)
    else:
        fig = render_footprint_streamlit(footprint, height=450)
    
    st.plotly_chart(fig, use_container_width=True, key=f"footprint_chart_{trade_id}")
    
    # Imbalance details (expandable)
    if any(bar.imbalances for bar in footprint.bars):
        with st.expander("🔍 Imbalance Details", expanded=False):
            for bar in footprint.bars:
                if bar.imbalances:
                    st.markdown(f"**{bar.bar_start.strftime('%H:%M')}**")
                    for imb in bar.imbalances:
                        icon = "🟢" if imb.direction == 'buy' else "🔴"
                        st.markdown(
                            f"  {icon} **${imb.price:.2f}** - "
                            f"{imb.direction.upper()} imbalance "
                            f"({imb.ratio:.1f}x threshold)"
                        )
    
    # Optional: Add refresh button
    col_left, col_right = st.columns([6, 1])
    with col_right:
        if st.button("🔄 Refresh", key=f"refresh_{trade_id}"):
            cache.delete(trade_id)
            st.rerun()


def render_footprint_panel_simple(
    trade_id: str,
    symbol: str,
    entry_time: datetime,
    supabase_client
):
    """
    Simplified version without view toggle.
    
    Use this for a cleaner interface if you don't need heatmap view.
    """
    render_footprint_panel(
        trade_id=trade_id,
        symbol=symbol,
        entry_time=entry_time,
        supabase_client=supabase_client,
        show_heatmap_toggle=False
    )
Integration in Main App
In your main app.py (after H1 chart, before statistics):
python# ... existing imports ...
from components.footprint_panel import render_footprint_panel

# ... existing code for M15 chart ...
# ... existing code for H1 chart ...

# NEW: Footprint panel
try:
    render_footprint_panel(
        trade_id=current_trade.id,  # Adjust to your trade object
        symbol=current_trade.symbol,
        entry_time=current_trade.entry_time,
        supabase_client=supabase,  # Your existing Supabase client
        show_heatmap_toggle=True
    )
except Exception as e:
    st.warning(f"Footprint chart unavailable: {e}")

# ... existing statistics table code ...
Standalone Test App
Create a test app to verify panel works:
File: test_footprint_app.py (at project root)
python"""
Standalone test app for footprint panel
Run with: streamlit run test_footprint_app.py
"""

import streamlit as st
from datetime import datetime
import pytz

from components.footprint_panel import render_footprint_panel
from data.supabase_client import get_supabase_client  # Adjust import

ET = pytz.timezone('America/New_York')

st.set_page_config(page_title="Footprint Test", layout="wide")

st.title("Footprint Panel Test")

# Test inputs
col1, col2 = st.columns(2)
with col1:
    symbol = st.text_input("Symbol", "SPY")
    date = st.date_input("Entry Date", datetime(2024, 12, 20))  # Adjust
with col2:
    time = st.time_input("Entry Time", datetime.strptime("10:00", "%H:%M").time())
    trade_id = st.text_input("Trade ID", "test-standalone-001")

if st.button("Generate Footprint", type="primary"):
    # Combine date and time
    entry_datetime = ET.localize(datetime.combine(date, time))
    
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Render panel
    render_footprint_panel(
        trade_id=trade_id,
        symbol=symbol,
        entry_time=entry_datetime,
        supabase_client=supabase,
        show_heatmap_toggle=True
    )
Acceptance Criteria

 footprint_panel.py imports without errors
 Panel displays spinner during build
 Panel shows cache hit message on second load
 Metadata metrics display correctly (ATR, tick, delta, imbalances)
 Chart renders within panel
 Imbalance expander shows details when present
 View toggle switches between footprint and heatmap
 Refresh button clears cache and rebuilds
 Run: streamlit run test_footprint_app.py works
 Integration in main app.py displays panel correctly
 First load takes 30-60s (API fetch)
 Second load <1s (cache hit)

CHECKPOINT: Footprint fully integrated into Streamlit app!

PHASE 7: Polish & Enhancements (XIII-002.08)
Prerequisites

Phase 6 completed
Footprint working in production app

Tasks

Implement render_heatmap_view() alternative visualization (already done in Phase 5)
Add view toggle (Footprint/Heatmap) to panel (already done in Phase 6)
Add try/except error handling to API calls
Add logging statements and graceful error messages
Create README.md and document configuration options
Add docstrings to key functions

Implementation
Part 1: Enhanced Error Handling
Update footprint/massive_client.py with better error messages:
python# Add to MassiveTickClient._request method:

def _request(self, url: str, params: dict = None) -> dict:
    """Make API request with comprehensive error handling."""
    try:
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 429:
            print(f"⚠️  Rate limit hit, waiting 60s...")
            time.sleep(60)
            return self._request(url, params)
        elif resp.status_code == 401:
            print(f"❌ Authentication failed - check POLYGON_API_KEY")
            return {'results': [], 'error': 'Authentication failed'}
        elif resp.status_code == 404:
            print(f"❌ Endpoint not found: {url}")
            return {'results': [], 'error': 'Endpoint not found'}
        else:
            print(f"❌ HTTP Error {resp.status_code}: {e}")
            return {'results': [], 'error': f'HTTP {resp.status_code}'}
    except requests.exceptions.Timeout:
        print(f"⏱️  Request timeout after 30s")
        return {'results': [], 'error': 'Timeout'}
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        return {'results': [], 'error': str(e)}
Update footprint/builder.py with better validation:
python# Add to FootprintBuilder.build method (at the start):

def build(self, trade_id: str, symbol: str, entry_time: datetime) -> FootprintData:
    """Build complete footprint data for a trade."""
    
    # Validation
    if not symbol:
        raise ValueError("Symbol is required")
    if not entry_time:
        raise ValueError("Entry time is required")
    
    # Ensure timezone aware
    if entry_time.tzinfo is None:
        entry_time = ET.localize(entry_time)
    
    # Validate entry time is during market hours (9:30 AM - 4:00 PM ET)
    if entry_time.hour < 9 or (entry_time.hour == 9 and entry_time.minute < 30):
        raise ValueError(f"Entry time {entry_time} is before market open (9:30 AM ET)")
    if entry_time.hour >= 16:
        raise ValueError(f"Entry time {entry_time} is after market close (4:00 PM ET)")
    
    # ... rest of method
Part 2: Logging
Create logging configuration:
File: footprint/logger.py
python"""
Logging configuration for footprint module
"""

import logging
import sys

def setup_logger(name: str = 'footprint', level: int = logging.INFO):
    """
    Setup logger for footprint module.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# Default logger
logger = setup_logger()
Update builder to use logging:
python# In footprint/builder.py, add at top:
from .logger import logger

# Replace print statements with logger:
logger.info(f"Building footprint for {symbol}")
logger.info(f"Window: {window_start} → {window_end}")
logger.info(f"Retrieved {len(bars)} bars")
logger.info(f"ATR: ${atr:.4f}, Tick: ${tick_size:.4f}")
logger.warning(f"No trades found in window")  # For warnings
logger.error(f"Failed to fetch data: {e}")  # For errors
Part 3: Documentation
File: footprint/README.md
markdown# Footprint Chart Module

Provides tick-level market microstructure analysis for trade review in the Epoch 1.0 system.

## Overview

The footprint chart visualizes order flow by showing bid and ask volume at each price level for the 15 minutes prior to trade entry. This helps identify absorption, aggressive buying/selling, and order flow imbalances that may indicate continuation or reversal.

## Features

- **Tick-level data**: Fetches trades and quotes from Massive.com API
- **Trade classification**: Matches trades to NBBO for bid/ask identification
- **Dynamic tick sizing**: ATR-based price level granularity
- **POC detection**: Identifies highest volume price per bar
- **Imbalance detection**: Highlights 300%+ diagonal imbalances
- **Supabase caching**: Stores processed data to avoid re-fetching
- **Dual visualization**: Traditional footprint and delta heatmap

## Installation

### Dependencies
```bash
pip install plotly>=5.18.0 pytz>=2023.3
```

### Database Setup

Run the migration:
```sql
-- See migrations/create_footprint_cache.sql
```

### Environment Variables

Requires existing `POLYGON_API_KEY` environment variable.

## Usage

### Basic Usage
```python
from footprint.builder import FootprintBuilder
from footprint.cache import FootprintCache
from footprint.visualization import render_footprint_streamlit
from datetime import datetime
import pytz

ET = pytz.timezone('America/New_York')

# Build footprint
builder = FootprintBuilder()
footprint = builder.build(
    trade_id='abc-123',
    symbol='SPY',
    entry_time=ET.localize(datetime(2025, 1, 15, 10, 30))
)

# Render
fig = render_footprint_streamlit(footprint)
fig.show()
```

### With Caching
```python
from footprint.cache import FootprintCache
from data.supabase_client import get_supabase_client

supabase = get_supabase_client()
cache = FootprintCache(supabase)

# Check cache
footprint = cache.get(trade_id)
if footprint is None:
    # Build and cache
    footprint = builder.build(trade_id, symbol, entry_time)
    cache.save(footprint)
```

### In Streamlit
```python
from components.footprint_panel import render_footprint_panel

render_footprint_panel(
    trade_id=trade.id,
    symbol=trade.symbol,
    entry_time=trade.entry_time,
    supabase_client=supabase
)
```

## Configuration

See `footprint/config.py` for customization options:
```python
FOOTPRINT_CONFIG = {
    'bar_count': 15,              # Number of 1-min bars
    'imbalance_threshold': 3.0,   # 300% threshold
    'tick_levels': 20,            # ATR/20 = tick size
    'atr_period': 14,             # ATR calculation period
}

FOOTPRINT_COLORS = {
    'bid': '#ef5350',             # Red for selling
    'ask': '#26a69a',             # Green for buying
    'poc': '#ffeb3b',             # Yellow for POC
    # ... more colors
}
```

## Architecture

### Module Structure
```
footprint/
├── __init__.py          # Module exports
├── config.py            # Configuration constants
├── models.py            # Data structures
├── massive_client.py    # API client
├── classifier.py        # Trade classification
├── builder.py           # Main pipeline
├── cache.py             # Supabase caching
├── visualization.py     # Plotly rendering
└── logger.py            # Logging setup
```

### Data Flow

1. **Fetch Data**: Trades, quotes, and bars from Massive API
2. **Classify Trades**: Match to NBBO for bid/ask determination
3. **Aggregate**: Group by bar and price level
4. **Calculate**: POC, delta, imbalances
5. **Cache**: Store in Supabase
6. **Visualize**: Render as footprint or heatmap

## API Reference

### FootprintBuilder

Main orchestration class.
```python
builder = FootprintBuilder(
    client=None,                  # Optional MassiveTickClient
    bar_count=15,                 # Number of bars
    imbalance_threshold=3.0       # Imbalance threshold
)

footprint = builder.build(
    trade_id='abc-123',
    symbol='SPY',
    entry_time=datetime(...)
)
```

### FootprintCache

Supabase caching layer.
```python
cache = FootprintCache(supabase_client)

# Check cache
exists = cache.exists(trade_id)

# Get cached data
footprint = cache.get(trade_id)

# Save data
cache.save(footprint)

# Delete cache
cache.delete(trade_id)
```

### FootprintRenderer

Plotly visualization.
```python
renderer = FootprintRenderer()
fig = renderer.render(footprint, height=450)
```

## Performance

### API Limits
- Rate limit: ~100 requests/minute (max tier)
- Pagination: 50K records per request
- Processing time: 30-60s first load

### Caching
- First load: 30-60s (API fetch)
- Cached load: <500ms (Supabase retrieval)
- Storage: ~50-100KB per footprint (compressed)

## Interpretation Guide

### Footprint Elements

- **Bid column (left, red)**: Seller-initiated volume
- **Ask column (right, green)**: Buyer-initiated volume
- **POC (yellow diamond)**: Highest volume price
- **Delta (top)**: Net buying (+) or selling (-) pressure
- **Imbalances (bright colors)**: 300%+ diagonal ratios

### Trading Signals

- **Absorption**: High volume at price with low delta
- **Breakout**: Stacked imbalances in one direction
- **Reversal**: POC migration + opposite delta
- **Continuation**: Aligned imbalances + delta direction

## Troubleshooting

### "No market data available"
- Check that entry_time is during market hours (9:30-16:00 ET)
- Verify date is a trading day
- Ensure symbol is valid

### "API Error 401"
- Check `POLYGON_API_KEY` environment variable
- Verify API key is active

### "Rate limit hit"
- Wait 60s for automatic retry
- Reduce concurrent requests

### "Cached data corrupted"
- Delete cache: `cache.delete(trade_id)`
- Rebuild: System will re-fetch from API

## Testing
```bash
# Test models
python footprint/test_models.py

# Test API
python footprint/test_api.py

# Test builder
python footprint/test_builder.py

# Test cache
python footprint/test_cache.py

# Test visualization
python footprint/test_visualization.py

# Test Streamlit panel
streamlit run test_footprint_app.py
```

## Support

For issues or questions:
1. Check this README
2. Review code comments
3. Check logs for error messages

## Changelog

### v1.0.0 (2025-12-29)
- Initial implementation
- 15-bar footprint with bid/ask classification
- ATR-based tick sizing
- POC and imbalance detection
- Supabase caching
- Plotly visualization
- Streamlit integration
Part 4: Final Code Review Checklist
Create a checklist for code quality:
File: footprint/CHECKLIST.md
markdown# Footprint Module - Code Quality Checklist

## Code Quality
- [ ] All functions have docstrings
- [ ] Type hints on all function signatures
- [ ] No hardcoded values (use config.py)
- [ ] Error handling on all API calls
- [ ] Logging instead of print statements
- [ ] No dead code or commented blocks

## Testing
- [ ] All test files pass
- [ ] Tested with multiple symbols
- [ ] Tested with different time windows
- [ ] Tested cache hit/miss scenarios
- [ ] Tested error conditions

## Performance
- [ ] API rate limiting working
- [ ] Caching reduces load times
- [ ] No memory leaks in long sessions
- [ ] Reasonable rendering time (<2s)

## Documentation
- [ ] README.md complete
- [ ] All public functions documented
- [ ] Configuration options explained
- [ ] Integration guide clear

## Integration
- [ ] Works in main Streamlit app
- [ ] No conflicts with existing code
- [ ] Reuses existing Supabase client
- [ ] Follows project conventions

## User Experience
- [ ] Loading spinners show progress
- [ ] Error messages are helpful
- [ ] Cache status visible to user
- [ ] Charts render correctly
- [ ] Hover tooltips work
```

### Acceptance Criteria
- [ ] All API calls have try/except error handling
- [ ] Logging configured and working
- [ ] README.md complete with examples
- [ ] All public functions have docstrings
- [ ] Type hints on all function signatures
- [ ] Code quality checklist completed
- [ ] No print statements (replaced with logger)
- [ ] Error messages are user-friendly
- [ ] Module can be imported and used independently

**FINAL CHECKPOINT:** Footprint module complete and production-ready!

---

## Testing Guidelines

### Unit Testing

Each phase should include basic tests to verify functionality before moving to the next phase.

### Integration Testing

After Phase 6, test the complete workflow:

1. **New Trade Test**
   - Select a trade with no cached footprint
   - Verify 30-60s build time
   - Verify all 15 bars populated
   - Verify POC and imbalances calculated

2. **Cached Trade Test**
   - Reload same trade
   - Verify <1s load time
   - Verify data matches original

3. **Multiple Symbols Test**
   - Test with SPY, QQQ, AAPL
   - Verify different tick sizes
   - Verify volume scales appropriately

4. **Error Handling Test**
   - Try non-existent symbol
   - Try pre-market timestamp
   - Try weekend date
   - Verify graceful error messages

### Performance Testing

Monitor these metrics:

- **API Fetch Time**: Should be 30-60s for 15 minutes of SPY
- **Cache Save Time**: Should be <1s
- **Cache Retrieve Time**: Should be <500ms
- **Render Time**: Should be <2s

### Visual Verification

For each test footprint, verify:

- [ ] Bid columns are red and on left
- [ ] Ask columns are green and on right
- [ ] Volume intensity varies correctly
- [ ] POC marker appears at highest volume
- [ ] Imbalances highlighted in bright colors
- [ ] Bar delta matches visual inspection
- [ ] Hover tooltips show correct data

---

## Appendices

### Appendix A: Massive.com API Reference

#### Trades Endpoint
```
GET /v3/trades/{stockTicker}
```

**Parameters:**
- `timestamp.gte`: Start time (nanoseconds)
- `timestamp.lt`: End time (nanoseconds)
- `limit`: Max 50000
- `sort`: 'timestamp'
- `order`: 'asc' or 'desc'

**Response Fields:**
- `price`: Trade price
- `size`: Volume
- `sip_timestamp`: Nanosecond timestamp
- `participant_timestamp`: Exchange timestamp
- `exchange`: Exchange ID
- `conditions`: Trade condition codes

#### Quotes Endpoint
```
GET /v3/quotes/{stockTicker}
```

**Response Fields:**
- `bid_price`: Best bid
- `bid_size`: Bid size (shares)
- `ask_price`: Best ask
- `ask_size`: Ask size (shares)
- `sip_timestamp`: Nanosecond timestamp

#### Bars Endpoint
```
GET /v2/aggs/ticker/{stockTicker}/range/{multiplier}/{timespan}/{from}/{to}
Response Fields:

t: Timestamp (milliseconds)
o: Open
h: High
l: Low
c: Close
v: Volume

Appendix B: Interpreting Footprint Charts
Key Concepts
Point of Control (POC)

Highest volume price in the bar
Indicates fair value or acceptance area
POC migration shows value area movement

Delta

Net buying (+) or selling (-) pressure
Large positive delta = aggressive buying
Large negative delta = aggressive selling

Imbalances

Diagonal volume ratio >300%
Buy imbalance: ask volume >> bid volume below
Sell imbalance: bid volume >> ask volume above
Indicates order flow direction and momentum

Absorption

High volume with low delta
Buyers/sellers absorbing opposite side
Often precedes reversals

Common Patterns
Bullish Signals

Stacked buy imbalances
POC migrating higher
Positive delta on breakout bars
Absorption of selling below support

Bearish Signals

Stacked sell imbalances
POC migrating lower
Negative delta on breakdown bars
Absorption of buying above resistance

Reversal Signals

High volume absorption
Delta divergence from price
Imbalance stacking reverses
POC stops migrating

Appendix C: Troubleshooting Common Issues
"Module not found" Errors
bash# Verify installation
pip list | grep plotly
pip list | grep pytz

# Reinstall if needed
pip install -r requirements.txt
API Authentication Errors
bash# Check environment variable
echo $POLYGON_API_KEY

# Set if missing
export POLYGON_API_KEY="your_key_here"
Supabase Connection Errors
python# Test connection
from data.supabase_client import get_supabase_client

supabase = get_supabase_client()
result = supabase.table('footprint_cache').select('*').limit(1).execute()
print(f"Connection OK: {len(result.data)} rows")
Visualization Not Displaying
python# Test in isolation
from footprint.visualization import FootprintRenderer

renderer = FootprintRenderer()
fig = renderer._empty_chart("Test")
fig.write_html('test.html')
# Open test.html in browser

Implementation Summary
This specification provides a complete, phased implementation guide for adding footprint charts to the Epoch 1.0 trade review system.
Total Phases: 8 (XIII-002.01 through XIII-002.08)
Estimated Time: 15-18 hours of focused development
Key Milestones:

Phase 1: Data structures complete
Phase 3: Can build footprint from API
Phase 4: Caching reduces load times
Phase 5: Charts render correctly
Phase 6: Integrated in Streamlit app
Phase 7: Production-ready polish

Success Criteria:

Footprint displays for any trade
First load <60s, cached load <1s
All 15 bars populated and accurate
POC, delta, imbalances calculated correctly
Charts render in Streamlit without errors
Cache reduces redundant API calls

Next Steps After Implementation:

Gather user feedback on visualization
Consider additional features (volume profile, TPO charts)
Optimize for larger time windows if needed
Add export functionality if requested


Conclusion
This specification provides everything needed to implement the footprint chart feature. Each phase is self-contained with clear deliverables, code examples, and acceptance criteria. Follow the phases in order, and test each phase before moving to the next.
Good luck with the implementation!
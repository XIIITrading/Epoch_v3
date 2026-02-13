"""
================================================================================
EPOCH TRADING SYSTEM - OPTIONS DATA FETCHER
Polygon.io Options API Integration
XIII Trading LLC
================================================================================

Fetches options chain snapshots and OHLC bar data from Polygon.io API.

Endpoints Used:
- /v3/snapshot/options/{underlyingAsset} - Options chain snapshot
- /v2/aggs/ticker/{optionsTicker}/range/{multiplier}/{timespan}/{from}/{to} - OHLC bars

================================================================================
"""

import requests
import time as time_module
from datetime import datetime, date, time, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import pytz

# Handle both relative and absolute imports
try:
    from .config import (
        POLYGON_BASE_URL,
        POLYGON_API_KEY,
        API_DELAY,
        API_RETRIES,
        API_RETRY_DELAY,
        REQUEST_TIMEOUT,
        ENTRY_BAR_MULTIPLIER,
        ENTRY_BAR_TIMESPAN,
        EXIT_BAR_MULTIPLIER,
        EXIT_BAR_TIMESPAN,
        VERBOSE
    )
except ImportError:
    from config import (
        POLYGON_BASE_URL,
        POLYGON_API_KEY,
        API_DELAY,
        API_RETRIES,
        API_RETRY_DELAY,
        REQUEST_TIMEOUT,
        ENTRY_BAR_MULTIPLIER,
        ENTRY_BAR_TIMESPAN,
        EXIT_BAR_MULTIPLIER,
        EXIT_BAR_TIMESPAN,
        VERBOSE
    )


@dataclass
class OptionsBar:
    """Single options OHLC bar."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    transactions: Optional[int] = None


@dataclass
class OptionsContract:
    """Options contract details from chain snapshot."""
    ticker: str                    # Full options ticker (e.g., O:AAPL250117C00175000)
    underlying: str                # Underlying symbol (e.g., AAPL)
    strike: float                  # Strike price
    expiration: date               # Expiration date
    contract_type: str             # "call" or "put"

    # Snapshot data (may be None if not available)
    last_price: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None


@dataclass
class OptionsChain:
    """Options chain for an underlying asset."""
    underlying: str
    snapshot_time: datetime
    contracts: List[OptionsContract] = field(default_factory=list)

    def get_strikes(self, contract_type: str = None) -> List[float]:
        """Get unique strike prices, optionally filtered by contract type."""
        contracts = self.contracts
        if contract_type:
            contracts = [c for c in contracts if c.contract_type == contract_type]
        return sorted(set(c.strike for c in contracts))

    def get_expirations(self) -> List[date]:
        """Get unique expiration dates."""
        return sorted(set(c.expiration for c in self.contracts))

    def get_contract(self, strike: float, expiration: date, contract_type: str) -> Optional[OptionsContract]:
        """Find a specific contract by strike, expiration, and type."""
        for c in self.contracts:
            if c.strike == strike and c.expiration == expiration and c.contract_type == contract_type:
                return c
        return None


class OptionsFetcher:
    """
    Fetches options data from Polygon.io API.

    Handles:
    - Options chain snapshots (available strikes, expirations, Greeks)
    - Options OHLC bars (15-second for entries, 5-minute for exits)
    - Rate limiting and retries
    - Caching to minimize API calls
    """

    EASTERN = pytz.timezone('America/New_York')

    def __init__(self, api_key: str = None, verbose: bool = None):
        """
        Initialize the fetcher.

        Args:
            api_key: Polygon API key (defaults to config)
            verbose: Enable verbose logging (defaults to config)
        """
        self.api_key = api_key or POLYGON_API_KEY
        self.verbose = verbose if verbose is not None else VERBOSE
        self.last_request_time = 0

        # Caches
        self._chain_cache: Dict[str, OptionsChain] = {}  # {underlying_date: chain}
        self._bars_cache: Dict[str, List[OptionsBar]] = {}  # {ticker_date_timeframe: bars}

    def _log(self, message: str):
        """Log message if verbose."""
        if self.verbose:
            print(f"  {message}")

    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        elapsed = time_module.time() - self.last_request_time
        if elapsed < API_DELAY:
            time_module.sleep(API_DELAY - elapsed)
        self.last_request_time = time_module.time()

    def _make_request(self, url: str, params: dict) -> Optional[dict]:
        """Make API request with retries."""
        params['apiKey'] = self.api_key

        for attempt in range(API_RETRIES):
            try:
                self._rate_limit()
                response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)

                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') in ['OK', 'DELAYED', 'SUCCESS']:
                        return data
                    elif self.verbose:
                        self._log(f"API status: {data.get('status')}")
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    self._log(f"Rate limited, waiting {API_RETRY_DELAY}s...")
                    time_module.sleep(API_RETRY_DELAY)
                    continue
                elif self.verbose:
                    self._log(f"API error: {response.status_code}")

            except Exception as e:
                if self.verbose:
                    self._log(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < API_RETRIES - 1:
                    time_module.sleep(API_RETRY_DELAY)

        return None

    def _parse_date(self, date_input) -> date:
        """Parse various date formats to date object."""
        if isinstance(date_input, date) and not isinstance(date_input, datetime):
            return date_input
        if isinstance(date_input, datetime):
            return date_input.date()
        if isinstance(date_input, str):
            if '-' in date_input:
                return datetime.strptime(date_input[:10], '%Y-%m-%d').date()
            elif '/' in date_input:
                parts = date_input.split('/')
                if len(parts[2]) == 4:
                    return datetime.strptime(date_input, '%m/%d/%Y').date()
                else:
                    return datetime.strptime(date_input, '%m/%d/%y').date()
        raise ValueError(f"Cannot parse date: {date_input}")

    def fetch_options_chain(
        self,
        underlying: str,
        trade_date: str,
        contract_type: str = None,
        expiration_date: str = None
    ) -> Optional[OptionsChain]:
        """
        Fetch options chain snapshot for an underlying.

        Args:
            underlying: Underlying ticker symbol (e.g., AAPL)
            trade_date: Date for the snapshot (YYYY-MM-DD)
            contract_type: Optional filter - "call" or "put"
            expiration_date: Optional filter - specific expiration (YYYY-MM-DD)

        Returns:
            OptionsChain object or None if not available
        """
        trade_dt = self._parse_date(trade_date)
        cache_key = f"{underlying}_{trade_dt}"

        # Check cache
        if cache_key in self._chain_cache:
            chain = self._chain_cache[cache_key]
            # Apply filters to cached data
            if contract_type or expiration_date:
                filtered = OptionsChain(
                    underlying=chain.underlying,
                    snapshot_time=chain.snapshot_time,
                    contracts=[]
                )
                for c in chain.contracts:
                    if contract_type and c.contract_type != contract_type:
                        continue
                    if expiration_date:
                        exp_dt = self._parse_date(expiration_date)
                        if c.expiration != exp_dt:
                            continue
                    filtered.contracts.append(c)
                return filtered
            return chain

        # Fetch from API
        url = f"{POLYGON_BASE_URL}/v3/snapshot/options/{underlying}"
        params = {
            'limit': 250,
            'order': 'asc',
            'sort': 'strike_price'
        }

        if contract_type:
            params['contract_type'] = contract_type
        if expiration_date:
            params['expiration_date'] = expiration_date

        self._log(f"Fetching options chain for {underlying}...")

        all_contracts = []
        next_url = None

        # Handle pagination
        while True:
            if next_url:
                # For pagination, use the next_url directly
                data = self._make_request(next_url, {'apiKey': self.api_key})
            else:
                data = self._make_request(url, params)

            if not data:
                break

            results = data.get('results', [])
            for result in results:
                details = result.get('details', {})
                day = result.get('day', {})
                greeks = result.get('greeks', {})

                contract = OptionsContract(
                    ticker=details.get('ticker', ''),
                    underlying=underlying,
                    strike=float(details.get('strike_price', 0)),
                    expiration=self._parse_date(details.get('expiration_date', '1900-01-01')),
                    contract_type=details.get('contract_type', '').lower(),
                    last_price=day.get('close'),
                    bid=result.get('last_quote', {}).get('bid'),
                    ask=result.get('last_quote', {}).get('ask'),
                    volume=day.get('volume'),
                    open_interest=details.get('open_interest'),
                    implied_volatility=greeks.get('implied_volatility'),
                    delta=greeks.get('delta'),
                    gamma=greeks.get('gamma'),
                    theta=greeks.get('theta'),
                    vega=greeks.get('vega')
                )
                all_contracts.append(contract)

            # Check for more pages
            next_url = data.get('next_url')
            if not next_url:
                break

        if not all_contracts:
            self._log(f"No options contracts found for {underlying}")
            return None

        chain = OptionsChain(
            underlying=underlying,
            snapshot_time=datetime.now(self.EASTERN),
            contracts=all_contracts
        )

        # Cache the full chain (without filters)
        if not contract_type and not expiration_date:
            self._chain_cache[cache_key] = chain

        self._log(f"Found {len(all_contracts)} contracts for {underlying}")

        return chain

    def fetch_options_bars(
        self,
        options_ticker: str,
        trade_date: str,
        multiplier: int,
        timespan: str
    ) -> List[OptionsBar]:
        """
        Fetch OHLC bars for an options contract.

        Args:
            options_ticker: Full options ticker (e.g., O:AAPL250117C00175000)
            trade_date: Date to fetch bars for (YYYY-MM-DD)
            multiplier: Bar size multiplier (e.g., 15 for 15-second)
            timespan: "second" or "minute"

        Returns:
            List of OptionsBar objects
        """
        trade_dt = self._parse_date(trade_date)
        date_str = trade_dt.strftime('%Y-%m-%d')
        cache_key = f"{options_ticker}_{date_str}_{multiplier}_{timespan}"

        # Check cache
        if cache_key in self._bars_cache:
            return self._bars_cache[cache_key]

        # Ensure O: prefix
        if not options_ticker.startswith('O:'):
            options_ticker = f"O:{options_ticker}"

        url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{options_ticker}/range/{multiplier}/{timespan}/{date_str}/{date_str}"
        params = {
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }

        self._log(f"Fetching {multiplier}-{timespan} bars for {options_ticker}...")

        data = self._make_request(url, params)

        if not data or 'results' not in data:
            self._log(f"No bars found for {options_ticker}")
            return []

        bars = []
        for result in data['results']:
            ts = datetime.fromtimestamp(result['t'] / 1000, tz=self.EASTERN)
            bar = OptionsBar(
                timestamp=ts,
                open=result['o'],
                high=result['h'],
                low=result['l'],
                close=result['c'],
                volume=int(result.get('v', 0)),
                vwap=result.get('vw'),
                transactions=result.get('n')
            )
            bars.append(bar)

        # Cache
        self._bars_cache[cache_key] = bars

        self._log(f"Fetched {len(bars)} bars for {options_ticker}")

        return bars

    def fetch_entry_bars(self, options_ticker: str, trade_date: str) -> List[OptionsBar]:
        """Fetch 15-second bars for entry analysis."""
        return self.fetch_options_bars(
            options_ticker=options_ticker,
            trade_date=trade_date,
            multiplier=ENTRY_BAR_MULTIPLIER,
            timespan=ENTRY_BAR_TIMESPAN
        )

    def fetch_exit_bars(self, options_ticker: str, trade_date: str) -> List[OptionsBar]:
        """Fetch 5-minute bars for exit analysis."""
        return self.fetch_options_bars(
            options_ticker=options_ticker,
            trade_date=trade_date,
            multiplier=EXIT_BAR_MULTIPLIER,
            timespan=EXIT_BAR_TIMESPAN
        )

    def get_bar_at_time(
        self,
        bars: List[OptionsBar],
        target_time: time,
        target_date: date = None
    ) -> Optional[OptionsBar]:
        """
        Find the bar at the exact target time, or the nearest bar if no exact match.

        Args:
            bars: List of OptionsBar objects
            target_time: Target time to find
            target_date: Optional date filter

        Returns:
            OptionsBar at target_time (exact match preferred), or nearest bar
        """
        if not bars:
            return None

        # Filter by date if specified
        filtered_bars = bars
        if target_date:
            filtered_bars = [b for b in bars if b.timestamp.date() == target_date]
            if not filtered_bars:
                return None

        # First, try to find an exact match
        for bar in filtered_bars:
            bar_time = bar.timestamp.time()
            if bar_time == target_time:
                return bar

        # No exact match - find the nearest bar
        nearest_bar = None
        min_diff = None

        for bar in filtered_bars:
            bar_time = bar.timestamp.time()
            # Calculate time difference in seconds
            bar_seconds = bar_time.hour * 3600 + bar_time.minute * 60 + bar_time.second
            target_seconds = target_time.hour * 3600 + target_time.minute * 60 + target_time.second
            diff = abs(bar_seconds - target_seconds)

            if min_diff is None or diff < min_diff:
                min_diff = diff
                nearest_bar = bar

        return nearest_bar

    def clear_cache(self):
        """Clear all cached data."""
        self._chain_cache.clear()
        self._bars_cache.clear()


def build_options_ticker(
    underlying: str,
    expiration: date,
    contract_type: str,
    strike: float
) -> str:
    """
    Build an options ticker symbol.

    Format: O:{UNDERLYING}{YYMMDD}{C/P}{STRIKE*1000}

    Args:
        underlying: Underlying symbol (e.g., AAPL)
        expiration: Expiration date
        contract_type: "call" or "put" (or "C"/"P")
        strike: Strike price

    Returns:
        Options ticker (e.g., O:AAPL250117C00175000)
    """
    # Format expiration as YYMMDD
    exp_str = expiration.strftime('%y%m%d')

    # Contract type
    if contract_type.lower() in ['call', 'c']:
        type_char = 'C'
    else:
        type_char = 'P'

    # Strike: multiply by 1000 and format as 8 digits
    strike_int = int(strike * 1000)
    strike_str = f"{strike_int:08d}"

    return f"O:{underlying}{exp_str}{type_char}{strike_str}"


def parse_options_ticker(ticker: str) -> dict:
    """
    Parse an options ticker symbol into components.

    Args:
        ticker: Options ticker (e.g., O:AAPL250117C00175000)

    Returns:
        Dict with underlying, expiration, contract_type, strike
    """
    # Remove O: prefix if present
    if ticker.startswith('O:'):
        ticker = ticker[2:]

    # Find where the date starts (first digit after letters)
    i = 0
    while i < len(ticker) and not ticker[i].isdigit():
        i += 1

    underlying = ticker[:i]
    rest = ticker[i:]

    # YYMMDD (6 chars) + C/P (1 char) + strike (8 chars)
    exp_str = rest[:6]
    contract_type = 'call' if rest[6] == 'C' else 'put'
    strike = int(rest[7:]) / 1000.0

    # Parse expiration
    expiration = datetime.strptime(exp_str, '%y%m%d').date()

    return {
        'underlying': underlying,
        'expiration': expiration,
        'contract_type': contract_type,
        'strike': strike,
        'ticker': f"O:{ticker}"
    }

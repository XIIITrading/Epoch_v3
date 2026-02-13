"""
Ticker List Management
Epoch Trading System v2.0 - XIII Trading LLC

Manages ticker lists for various markets and indices.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum
import warnings
import json
from pathlib import Path
import logging

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scanner.config import scanner_config
from config import POLYGON_API_KEY

logger = logging.getLogger(__name__)


class TickerList(Enum):
    """Available ticker lists."""
    SP500 = "sp500"
    NASDAQ100 = "nasdaq100"
    RUSSELL2000 = "russell2000"
    DOW30 = "dow30"
    ALL_US_EQUITIES = "all_us_equities"


class TickerManager:
    """Manages ticker lists for various indices."""

    def __init__(self):
        self.data_dir = scanner_config.TICKER_DATA_DIR
        self.data_dir.mkdir(exist_ok=True)
        self._ticker_data = self._load_ticker_data()
        self._all_equities_cache = None
        self._all_equities_cache_time = None

    def _load_ticker_data(self) -> Dict:
        """Load ticker data from file."""
        data_file = self.data_dir / "tickers.json"

        if data_file.exists():
            with open(data_file, 'r') as f:
                return json.load(f)
        else:
            # Initialize with default S&P 500 list
            return {
                "sp500": {
                    "last_updated": "2025-01-26",
                    "tickers": self._get_default_sp500_tickers()
                }
            }

    def get_tickers(self, ticker_list: Optional[TickerList] = None,
                    check_staleness: bool = True) -> List[str]:
        """Get tickers for specified list."""
        if ticker_list is None or ticker_list == TickerList.ALL_US_EQUITIES:
            return self.get_all_us_equities()

        list_name = ticker_list.value

        if list_name not in self._ticker_data:
            raise ValueError(f"Ticker list '{list_name}' not found")

        data = self._ticker_data[list_name]

        if check_staleness:
            self._check_staleness(list_name, data['last_updated'])

        return data['tickers'].copy()

    def get_all_us_equities(self,
                            min_market_cap: Optional[float] = None,
                            min_price: float = 1.0,
                            cache_hours: int = 24) -> List[str]:
        """
        Fetch all active US equities from Polygon.

        Args:
            min_market_cap: Minimum market cap filter
            min_price: Minimum price filter
            cache_hours: Hours to cache the ticker list

        Returns:
            List of ticker symbols
        """
        # Check cache
        if (self._all_equities_cache is not None and
                self._all_equities_cache_time is not None):

            time_since_cache = datetime.now() - self._all_equities_cache_time
            if time_since_cache < timedelta(hours=cache_hours):
                logger.info(f"Using cached all equities list ({len(self._all_equities_cache)} tickers)")
                return self._all_equities_cache.copy()

        logger.info("Fetching all US equities from Polygon...")

        try:
            from polygon import RESTClient

            client = RESTClient(POLYGON_API_KEY)

            all_tickers = []

            # Fetch tickers with pagination
            params = {
                'market': 'stocks',
                'active': True,
                'limit': 1000,
                'order': 'asc',
                'sort': 'ticker'
            }

            next_url = None
            page_count = 0

            while True:
                if next_url:
                    response = client._session.get(next_url)
                    data = response.json()
                else:
                    response = client.list_tickers(**params)
                    data = response.__dict__ if hasattr(response, '__dict__') else response

                if 'results' in data:
                    for ticker_info in data['results']:
                        # Filter criteria
                        if ticker_info.get('type') != 'CS':  # Common Stock only
                            continue

                        if ticker_info.get('currency_name') != 'usd':
                            continue

                        # Add to list
                        all_tickers.append(ticker_info['ticker'])

                page_count += 1
                logger.debug(f"Fetched page {page_count}, total tickers: {len(all_tickers)}")

                # Check for next page
                if 'next_url' in data and data['next_url']:
                    next_url = data['next_url']
                else:
                    break

                # Safety limit
                if page_count > 20:
                    logger.warning("Reached page limit, stopping ticker fetch")
                    break

            # Cache the results
            self._all_equities_cache = all_tickers
            self._all_equities_cache_time = datetime.now()

            logger.info(f"Fetched {len(all_tickers)} US equity tickers")

            # Save to file for reference
            cache_file = self.data_dir / "all_us_equities_cache.json"
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'count': len(all_tickers),
                    'tickers': all_tickers
                }, f, indent=2)

            return all_tickers

        except Exception as e:
            logger.error(f"Failed to fetch all US equities: {e}")

            # Try to load from cache file as fallback
            cache_file = self.data_dir / "all_us_equities_cache.json"
            if cache_file.exists():
                logger.info("Loading from cache file as fallback")
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    return data['tickers']

            # Last resort - return major indices combined
            logger.warning("Falling back to combined major indices")
            combined = set()
            for list_type in ['sp500', 'nasdaq100', 'russell2000']:
                if list_type in self._ticker_data:
                    combined.update(self._ticker_data[list_type]['tickers'])

            return sorted(list(combined))

    def update_tickers(self, ticker_list: TickerList, tickers: List[str]):
        """Update ticker list."""
        list_name = ticker_list.value

        self._ticker_data[list_name] = {
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "tickers": sorted(tickers)
        }

        # Save to file
        self._save_ticker_data()

    def _save_ticker_data(self):
        """Save ticker data to file."""
        data_file = self.data_dir / "tickers.json"
        with open(data_file, 'w') as f:
            json.dump(self._ticker_data, f, indent=2)

    def _check_staleness(self, list_name: str, last_updated: str):
        """Check if ticker list needs updating."""
        last_update = datetime.strptime(last_updated, "%Y-%m-%d")
        days_since_update = (datetime.now() - last_update).days

        if days_since_update > scanner_config.UPDATE_FREQUENCY_DAYS:
            warnings.warn(
                f"\n{'=' * 60}\n"
                f"WARNING: {list_name.upper()} list is {days_since_update} days old!\n"
                f"Last updated: {last_updated}\n"
                f"{'=' * 60}\n",
                UserWarning,
                stacklevel=3
            )

    def verify_ticker(self, ticker: str, ticker_list: TickerList) -> bool:
        """Check if a ticker is in the specified list."""
        tickers = self.get_tickers(ticker_list, check_staleness=False)
        return ticker.upper() in tickers

    def _get_default_sp500_tickers(self) -> List[str]:
        """Get default S&P 500 tickers."""
        return [
            'A', 'AAL', 'AAP', 'AAPL', 'ABBV', 'ABC', 'ABMD', 'ABT', 'ACGL', 'ACN',
            'ADBE', 'ADI', 'ADM', 'ADP', 'ADSK', 'AEE', 'AEP', 'AES', 'AFL', 'AIG',
            'AIZ', 'AJG', 'AKAM', 'ALB', 'ALGN', 'ALK', 'ALL', 'ALLE', 'AMAT', 'AMCR',
            'AMD', 'AME', 'AMGN', 'AMP', 'AMT', 'AMTM', 'AMZN', 'ANET', 'ANSS', 'AON',
            'AOS', 'APA', 'APD', 'APH', 'APO', 'APTV', 'ARE', 'ATO', 'AVB', 'AVGO',
            'AVY', 'AWK', 'AXON', 'AXP', 'AZO', 'BA', 'BAC', 'BALL', 'BAX', 'BBWI',
            'BBY', 'BDX', 'BEN', 'BF-B', 'BG', 'BIIB', 'BIO', 'BK', 'BKNG', 'BKR',
            'BLDR', 'BLK', 'BMY', 'BR', 'BRK-B', 'BRO', 'BSX', 'BWA', 'BX', 'BXP',
            'C', 'CAG', 'CAH', 'CARR', 'CAT', 'CB', 'CBOE', 'CBRE', 'CCI', 'CCL',
            'CDAY', 'CDNS', 'CDW', 'CE', 'CEG', 'CF', 'CFG', 'CHD', 'CHRW', 'CHTR',
            'CI', 'CINF', 'CL', 'CLX', 'CMA', 'CMCSA', 'CME', 'CMG', 'CMI', 'CMS',
            'CNC', 'CNP', 'COF', 'COO', 'COP', 'COR', 'COST', 'CPAY', 'CPB', 'CPRT',
            'CPT', 'CRL', 'CRM', 'CRWD', 'CSCO', 'CSGP', 'CSX', 'CTAS', 'CTLT', 'CTRA',
            'CTSH', 'CTVA', 'CVS', 'CVX', 'CZR', 'D', 'DAL', 'DD', 'DE', 'DECK',
            'DFS', 'DG', 'DGX', 'DHI', 'DHR', 'DIS', 'DISH', 'DLR', 'DLTR', 'DOC',
            'DOV', 'DOW', 'DPZ', 'DRI', 'DTE', 'DUK', 'DVA', 'DVN', 'DXCM', 'EA',
            'EBAY', 'ECL', 'ED', 'EFX', 'EG', 'EIX', 'EL', 'ELV', 'EMN', 'EMR',
            'ENPH', 'EOG', 'EPAM', 'EQIX', 'EQR', 'EQT', 'ERIE', 'ES', 'ESS', 'ETN',
            'ETR', 'ETSY', 'EVRG', 'EW', 'EXC', 'EXPD', 'EXPE', 'EXR', 'F', 'FANG',
            'FAST', 'FCX', 'FDS', 'FDX', 'FE', 'FFIV', 'FI', 'FICO', 'FIS', 'FITB',
            'FLT', 'FMC', 'FOX', 'FOXA', 'FRT', 'FSLR', 'FTNT', 'FTV', 'GD', 'GDDY',
            'GE', 'GEHC', 'GEN', 'GEV', 'GILD', 'GIS', 'GL', 'GLW', 'GM', 'GNRC',
            'GOOG', 'GOOGL', 'GPC', 'GPN', 'GRMN', 'GS', 'GWW', 'HAL', 'HAS', 'HBAN',
            'HCA', 'HD', 'HES', 'HIG', 'HII', 'HLT', 'HOLX', 'HON', 'HPE', 'HPQ',
            'HRL', 'HSIC', 'HST', 'HSY', 'HUBB', 'HUM', 'HWM', 'IBM', 'ICE', 'IDXX',
            'IEX', 'IFF', 'ILMN', 'INCY', 'INTC', 'INTU', 'INVH', 'IP', 'IPG', 'IQV',
            'IR', 'IRM', 'ISRG', 'IT', 'ITW', 'IVZ', 'J', 'JBHT', 'JBL', 'JCI',
            'JKHY', 'JNJ', 'JNPR', 'JPM', 'K', 'KDP', 'KEY', 'KEYS', 'KHC', 'KIM',
            'KKR', 'KLAC', 'KMB', 'KMI', 'KMX', 'KO', 'KR', 'KVUE', 'L', 'LDOS',
            'LEN', 'LH', 'LHX', 'LII', 'LIN', 'LKQ', 'LLY', 'LMT', 'LNT', 'LOW',
            'LRCX', 'LULU', 'LUV', 'LVS', 'LW', 'LYB', 'LYV', 'MA', 'MAA', 'MAR',
            'MAS', 'MBC', 'MCD', 'MCHP', 'MCK', 'MCO', 'MDLZ', 'MDT', 'MET', 'META',
            'MGM', 'MHK', 'MKC', 'MKTX', 'MLM', 'MMC', 'MMM', 'MNST', 'MO', 'MOH',
            'MOS', 'MPC', 'MPWR', 'MRK', 'MRNA', 'MRO', 'MS', 'MSCI', 'MSFT', 'MSI',
            'MTB', 'MTCH', 'MTD', 'MU', 'NCLH', 'NDAQ', 'NDSN', 'NEE', 'NEM', 'NFLX',
            'NI', 'NKE', 'NOC', 'NOW', 'NRG', 'NSC', 'NTAP', 'NTRS', 'NUE', 'NVDA',
            'NVR', 'NWS', 'NWSA', 'NXPI', 'O', 'ODFL', 'OKE', 'OMC', 'ON', 'ORCL',
            'ORLY', 'OTIS', 'OXY', 'PANW', 'PARA', 'PAYC', 'PAYX', 'PCAR', 'PCG', 'PEAK',
            'PEG', 'PEP', 'PFE', 'PFG', 'PG', 'PGR', 'PH', 'PHM', 'PKG', 'PLD',
            'PLTR', 'PM', 'PNC', 'PNR', 'PNW', 'PODD', 'POOL', 'PPG', 'PPL', 'PRU',
            'PSA', 'PSX', 'PTC', 'PWR', 'PXD', 'PYPL', 'QCOM', 'QRVO', 'RCL', 'REG',
            'REGN', 'RF', 'RHI', 'RJF', 'RL', 'RMD', 'ROK', 'ROL', 'ROP', 'ROST',
            'RSG', 'RTX', 'RVTY', 'SBAC', 'SBUX', 'SCHW', 'SHW', 'SJM', 'SLB', 'SMCI',
            'SNA', 'SNPS', 'SO', 'SOLV', 'SPG', 'SPGI', 'SRE', 'STE', 'STLD', 'STT',
            'STX', 'STZ', 'SWK', 'SWKS', 'SYF', 'SYK', 'SYY', 'T', 'TAP', 'TDG',
            'TDY', 'TECH', 'TEL', 'TER', 'TFC', 'TFX', 'TGT', 'TJX', 'TMO', 'TMUS',
            'TPL', 'TPR', 'TRGP', 'TRMB', 'TROW', 'TRV', 'TSCO', 'TSLA', 'TSN', 'TT',
            'TTWO', 'TXN', 'TXT', 'TYL', 'UAL', 'UBER', 'UDR', 'UHS', 'ULTA', 'UNH',
            'UNP', 'UPS', 'URI', 'USB', 'V', 'VICI', 'VLO', 'VLTO', 'VMC', 'VRSK',
            'VRSN', 'VRTX', 'VST', 'VTR', 'VTRS', 'VZ', 'WAB', 'WAT', 'WBA', 'WBD',
            'WDC', 'WDAY', 'WEC', 'WELL', 'WFC', 'WM', 'WMB', 'WMT', 'WRB', 'WRK',
            'WST', 'WTW', 'WY', 'WYNN', 'XEL', 'XOM', 'XRAY', 'XYL', 'YUM', 'ZBH',
            'ZBRA', 'ZION', 'ZTS'
        ]


# Global instance
ticker_manager = TickerManager()

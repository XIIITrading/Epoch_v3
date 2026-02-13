"""
Ticker list management.
Loads and manages stock ticker lists (S&P 500, NASDAQ 100, etc.)
"""
import json
import logging
from pathlib import Path
from typing import List, Set, Optional
from datetime import datetime, timedelta

import requests

from config import DATA_DIR

# Market scanner directory (not needed for basic operation)
MARKET_SCANNER_DIR = DATA_DIR / "scanner"

logger = logging.getLogger(__name__)


# Common ticker lists (built-in defaults)
DEFAULT_SP500_TICKERS = [
    "AAPL", "ABBV", "ABT", "ACN", "ADBE", "ADI", "ADP", "ADSK", "AEP", "AFL",
    "AIG", "AMAT", "AMD", "AMGN", "AMT", "AMZN", "ANET", "AVGO", "AXP", "BA",
    "BAC", "BDX", "BIIB", "BK", "BKNG", "BLK", "BMY", "BSX", "C", "CAT",
    "CCL", "CDNS", "CL", "CMCSA", "CME", "CMG", "COF", "COP", "COST", "CRM",
    "CSCO", "CSX", "CVS", "CVX", "D", "DE", "DG", "DHR", "DIS", "DUK",
    "EA", "EMR", "ENPH", "EOG", "EQR", "EW", "EXC", "F", "FCX", "FDX",
    "FSLR", "GD", "GE", "GILD", "GM", "GOOG", "GOOGL", "GS", "HD", "HON",
    "IBM", "ICE", "INTC", "INTU", "ISRG", "JCI", "JNJ", "JPM", "KHC", "KMB",
    "KO", "LLY", "LMT", "LOW", "LRCX", "LUV", "MA", "MAR", "MCD", "MCHP",
    "MCK", "MCO", "MDLZ", "MDT", "MET", "META", "MMC", "MMM", "MO", "MRK",
    "MS", "MSFT", "MU", "NEE", "NFLX", "NKE", "NOC", "NOW", "NSC", "NVDA",
    "ORCL", "OXY", "PANW", "PEP", "PFE", "PG", "PGR", "PLD", "PM", "PNC",
    "PYPL", "QCOM", "REGN", "ROP", "RTX", "SBUX", "SCHW", "SHW", "SLB", "SNPS",
    "SO", "SPG", "SPGI", "SRE", "T", "TFC", "TGT", "TJX", "TMO", "TMUS",
    "TRV", "TSLA", "TXN", "UNH", "UNP", "UPS", "USB", "V", "VLO", "VRTX",
    "VZ", "WBA", "WFC", "WMT", "XOM", "ZTS"
]

DEFAULT_NASDAQ100_TICKERS = [
    "AAPL", "ABNB", "ADBE", "ADI", "ADP", "ADSK", "AEP", "AMAT", "AMD", "AMGN",
    "AMZN", "ANSS", "ASML", "AVGO", "AZN", "BIIB", "BKNG", "BKR", "CDNS", "CEG",
    "CHTR", "CMCSA", "COST", "CPRT", "CRWD", "CSCO", "CSGP", "CSX", "CTAS", "CTSH",
    "DDOG", "DLTR", "DXCM", "EA", "EBAY", "ENPH", "EXC", "FANG", "FAST", "FTNT",
    "GEHC", "GFS", "GILD", "GOOG", "GOOGL", "HON", "IDXX", "ILMN", "INTC", "INTU",
    "ISRG", "JD", "KDP", "KHC", "KLAC", "LRCX", "LCID", "LULU", "MAR", "MCHP",
    "MDLZ", "MELI", "META", "MNST", "MRNA", "MRVL", "MSFT", "MU", "NFLX", "NVDA",
    "NXPI", "ODFL", "ON", "ORLY", "PANW", "PAYX", "PCAR", "PDD", "PEP", "PYPL",
    "QCOM", "REGN", "RIVN", "ROST", "SBUX", "SIRI", "SNPS", "SPLK", "TEAM", "TMUS",
    "TSLA", "TTD", "TXN", "VRSK", "VRTX", "WBA", "WBD", "WDAY", "XEL", "ZM", "ZS"
]


class TickerManager:
    """Manages ticker lists for scanning and analysis."""

    # File locations
    TICKER_FILE = MARKET_SCANNER_DIR / "data" / "ticker_lists" / "tickers.json"
    LOCAL_CACHE = DATA_DIR / "tickers.json"

    # How often to refresh ticker lists
    STALE_DAYS = 90

    def __init__(self):
        """Initialize ticker manager and load ticker lists."""
        self._tickers: dict = {}
        self._load_tickers()

    def _load_tickers(self):
        """Load tickers from file or use built-in defaults."""
        # Try main ticker file from market scanner
        if self.TICKER_FILE.exists():
            try:
                with open(self.TICKER_FILE, 'r') as f:
                    self._tickers = json.load(f)
                logger.info(f"Loaded tickers from {self.TICKER_FILE}")
                return
            except Exception as e:
                logger.warning(f"Could not load {self.TICKER_FILE}: {e}")

        # Try local cache
        if self.LOCAL_CACHE.exists():
            try:
                with open(self.LOCAL_CACHE, 'r') as f:
                    self._tickers = json.load(f)
                logger.info("Loaded tickers from local cache")
                return
            except Exception as e:
                logger.warning(f"Could not load cache: {e}")

        # Use built-in defaults
        logger.info("Using built-in ticker lists")
        self._tickers = {
            "sp500": DEFAULT_SP500_TICKERS,
            "nasdaq100": DEFAULT_NASDAQ100_TICKERS,
            "russell2000": [],  # Would need to be loaded from external source
            "last_updated": datetime.now().isoformat()
        }

    def save_tickers(self):
        """Save current ticker lists to local cache."""
        try:
            self._tickers["last_updated"] = datetime.now().isoformat()
            with open(self.LOCAL_CACHE, 'w') as f:
                json.dump(self._tickers, f, indent=2)
            logger.info("Saved tickers to local cache")
        except Exception as e:
            logger.error(f"Could not save tickers: {e}")

    # =========================================================================
    # TICKER LIST ACCESS
    # =========================================================================

    def get_list(self, list_name: str) -> List[str]:
        """
        Get ticker list by name.

        Args:
            list_name: One of 'sp500', 'nasdaq100', 'russell2000'

        Returns:
            List of ticker symbols
        """
        return self._tickers.get(list_name, [])

    def get_sp500(self) -> List[str]:
        """Get S&P 500 tickers."""
        return self.get_list("sp500")

    def get_nasdaq100(self) -> List[str]:
        """Get NASDAQ 100 tickers."""
        return self.get_list("nasdaq100")

    def get_russell2000(self) -> List[str]:
        """Get Russell 2000 tickers."""
        return self.get_list("russell2000")

    def get_all_tickers(self) -> List[str]:
        """Get unique tickers from all lists."""
        all_tickers = set()
        for key in ["sp500", "nasdaq100", "russell2000"]:
            all_tickers.update(self._tickers.get(key, []))
        return sorted(list(all_tickers))

    # =========================================================================
    # TICKER VALIDATION
    # =========================================================================

    def is_stale(self) -> bool:
        """Check if ticker data is stale and needs refresh."""
        last_updated = self._tickers.get("last_updated")
        if not last_updated:
            return True

        try:
            update_date = datetime.fromisoformat(last_updated)
            return (datetime.now() - update_date).days > self.STALE_DAYS
        except Exception:
            return True

    def validate_ticker(self, ticker: str) -> bool:
        """
        Validate a single ticker symbol.

        Args:
            ticker: Ticker symbol to validate

        Returns:
            True if valid, False otherwise
        """
        ticker = ticker.strip().upper()
        # Basic validation: 1-5 chars, alphanumeric (allowing . for BRK.B etc)
        if not ticker:
            return False
        if len(ticker) > 5:
            return False
        # Allow alphanumeric and dots
        return all(c.isalnum() or c == '.' for c in ticker)

    def validate_tickers(self, tickers: List[str]) -> List[str]:
        """
        Validate and normalize a list of ticker symbols.

        Args:
            tickers: List of ticker symbols

        Returns:
            List of valid, normalized tickers
        """
        valid = []
        for t in tickers:
            t = t.strip().upper()
            if self.validate_ticker(t):
                valid.append(t)
            else:
                logger.warning(f"Invalid ticker: {t}")
        return valid

    def parse_ticker_input(self, input_str: str) -> List[str]:
        """
        Parse ticker input string from user.

        Accepts:
        - Comma-separated: "AAPL, MSFT, GOOGL"
        - Space-separated: "AAPL MSFT GOOGL"
        - Newline-separated
        - Semicolon-separated

        Args:
            input_str: Raw input string from user

        Returns:
            List of normalized ticker symbols
        """
        if not input_str:
            return []

        # Replace common separators with comma
        normalized = input_str.replace('\n', ',').replace(';', ',').replace(' ', ',')

        # Split and clean
        tickers = [t.strip() for t in normalized.split(',') if t.strip()]

        return self.validate_tickers(tickers)

    # =========================================================================
    # TICKER INFORMATION
    # =========================================================================

    def is_index_ticker(self, ticker: str) -> bool:
        """Check if ticker is a market index (SPY, QQQ, DIA)."""
        return ticker.upper() in ["SPY", "QQQ", "DIA", "IWM"]

    def get_index_tickers(self) -> List[str]:
        """Get list of index tickers."""
        return ["SPY", "QQQ", "DIA"]

    def in_sp500(self, ticker: str) -> bool:
        """Check if ticker is in S&P 500."""
        return ticker.upper() in self._tickers.get("sp500", [])

    def in_nasdaq100(self, ticker: str) -> bool:
        """Check if ticker is in NASDAQ 100."""
        return ticker.upper() in self._tickers.get("nasdaq100", [])


# Global singleton instance
ticker_manager = TickerManager()


def parse_tickers(input_str: str) -> List[str]:
    """
    Convenience function to parse ticker input.

    Args:
        input_str: Raw input string

    Returns:
        List of validated ticker symbols
    """
    return ticker_manager.parse_ticker_input(input_str)

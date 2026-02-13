"""
Short Interest Fetcher
Epoch Trading System v2.0 - XIII Trading LLC

Fetches short interest data from Polygon API.
"""
import logging
from typing import Dict, List, Set
from datetime import datetime, timedelta
from polygon import RESTClient

logger = logging.getLogger(__name__)


class ShortInterestFetcher:
    """Fetches short interest data from Polygon API for specific tickers only."""

    def __init__(self, api_key: str):
        self.client = RESTClient(api_key)
        self.cache = {}
        self.cache_date = None
        self.cached_tickers = set()

    def load_short_data_for_tickers(self,
                                    tickers: List[str],
                                    reference_date: datetime = None,
                                    force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Load short interest data ONLY for specified tickers as of reference date.

        Args:
            tickers: List of tickers to fetch (e.g., S&P 500 list)
            reference_date: Get short interest as of this date (defaults to today)
            force_refresh: Force reload even if cached

        Returns:
            Dict mapping ticker to short interest data
        """
        if reference_date is None:
            reference_date = datetime.now()

        ticker_set = set(tickers)

        # Check cache validity
        if not force_refresh and self.cache and self.cache_date:
            same_date = self.cache_date.date() == reference_date.date()
            has_all_tickers = ticker_set.issubset(self.cached_tickers)
            recent = datetime.now() - self.cache_date < timedelta(hours=1)

            if same_date and has_all_tickers and recent:
                logger.info(f"Using cached short interest for {len(tickers)} tickers")
                return {ticker: self.cache.get(ticker, self._empty_short_data_dict())
                        for ticker in tickers}

        logger.info(f"Fetching short interest for {len(tickers)} tickers as of {reference_date.date()}")

        # Clear cache for new fetch
        ticker_data = {}
        found_tickers = set()
        processed_records = 0

        # Convert tickers to uppercase for matching
        ticker_set_upper = {t.upper() for t in ticker_set}

        try:
            # Fetch with date filter
            for item in self.client.list_short_interest(
                    settlement_date_lte=reference_date.strftime('%Y-%m-%d'),
                    limit=1000,
                    sort="ticker.asc,settlement_date.desc"
            ):
                ticker = item.ticker.upper()
                processed_records += 1

                # Only process if it's one of our target tickers AND we haven't seen it yet
                if ticker in ticker_set_upper and ticker not in found_tickers:
                    ticker_data[ticker] = {
                        'short_interest': item.short_interest,
                        'days_to_cover': getattr(item, 'days_to_cover', 0),
                        'avg_daily_volume': getattr(item, 'avg_daily_volume', 0),
                        'settlement_date': getattr(item, 'settlement_date', None)
                    }
                    found_tickers.add(ticker)

                    # Log progress
                    if len(found_tickers) % 50 == 0:
                        logger.debug(f"Found {len(found_tickers)}/{len(tickers)} tickers...")

                    # Early exit if we found all our tickers
                    if len(found_tickers) == len(ticker_set_upper):
                        logger.info(f"Found all {len(found_tickers)} tickers after {processed_records} records")
                        break

                # Safety limit - stop if we've processed too many records
                if processed_records > 50000:
                    logger.warning(f"Processed {processed_records} records, stopping search")
                    break

            # Log which tickers were not found
            not_found = ticker_set_upper - found_tickers
            if not_found:
                logger.info(f"No short interest data for {len(not_found)} tickers: {list(not_found)[:10]}...")

            logger.info(f"Found short interest for {len(found_tickers)}/{len(tickers)} tickers")

            # Update cache
            self.cache = ticker_data
            self.cache_date = datetime.now()
            self.cached_tickers = found_tickers

            # Return data for all requested tickers (empty data for not found)
            return {ticker: ticker_data.get(ticker.upper(), self._empty_short_data_dict())
                    for ticker in tickers}

        except Exception as e:
            logger.error(f"Error loading short interest: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {ticker: self._empty_short_data_dict() for ticker in tickers}

    def fetch_short_interest(self, ticker: str, reference_date: datetime = None) -> Dict:
        """
        Get short interest for a specific ticker from cached data.

        Args:
            ticker: Stock symbol
            reference_date: Not used here since data is pre-loaded

        Returns:
            Dict with short interest metrics
        """
        ticker = ticker.upper()

        if ticker in self.cache:
            data = self.cache[ticker]

            # Calculate short percentage
            short_percent = self._calculate_short_percent(ticker, data.get('short_interest', 0))

            return {
                'short_interest_percent': short_percent,
                'short_interest_shares': data.get('short_interest', 0),
                'days_to_cover': data.get('days_to_cover', 0),
                'avg_daily_volume': data.get('avg_daily_volume', 0),
                'data_date': data.get('settlement_date')
            }

        return self._empty_short_data()

    def _calculate_short_percent(self, ticker: str, short_shares: float) -> float:
        """
        Calculate short interest as percentage.
        Using DTC * 3 as rough estimate.
        """
        if short_shares == 0:
            return 0

        # Get days to cover from cache
        dtc = self.cache.get(ticker, {}).get('days_to_cover', 0)

        if dtc > 0:
            # Rough formula: DTC * 3 = approximate short %
            return min(dtc * 3, 40)  # Cap at 40%

        return 0

    def _empty_short_data(self) -> Dict:
        """Return empty short data structure for API response."""
        return {
            'short_interest_percent': 0,
            'short_interest_shares': 0,
            'days_to_cover': 0,
            'avg_daily_volume': 0,
            'data_date': None
        }

    def _empty_short_data_dict(self) -> Dict:
        """Return empty short data structure for internal storage."""
        return {
            'short_interest': 0,
            'days_to_cover': 0,
            'avg_daily_volume': 0,
            'settlement_date': None
        }

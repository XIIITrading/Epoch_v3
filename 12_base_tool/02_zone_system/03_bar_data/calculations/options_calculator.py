# Update: calculations/options_levels/options_calculator.py

"""
Options Levels Calculator for Meridian Trading System
Identifies top 10 options strikes by open interest to use as confluence zones
"""

from polygon import RESTClient
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptionsLevelsCalculator:
    """
    Calculates top options strike levels based on open interest
    These levels act as price magnets due to gamma hedging and pinning effects
    """

    def __init__(self, api_key: str = None):
        """Initialize with Polygon API key"""
        if not api_key:
            try:
                import sys
                root_dir = Path(__file__).parent.parent.parent
                sys.path.insert(0, str(root_dir))

                from credentials import POLYGON_API_KEY
                api_key = POLYGON_API_KEY

            except ImportError as e:
                logger.error(f"No API key provided and credentials.py not found: {e}")
                raise ValueError("Polygon API key required")

        self.client = RESTClient(api_key)
        logger.info("Options calculator initialized")

    def calculate_top_options_levels(self,
                                     ticker: str,
                                     date_str: str,
                                     last_price: float = None,
                                     num_levels: int = 10,
                                     price_range_pct: float = 0.15) -> Dict:
        """
        Main method to get top options levels by open interest

        Args:
            ticker: Stock symbol (e.g., "AAPL")
            date_str: Reference date in YYYY-MM-DD format
            last_price: Current stock price (optional, will fetch if not provided)
            num_levels: Number of top strike levels to return (default 10)
            price_range_pct: Percentage range around current price to consider (default 15%)

        Returns:
            Dictionary with opt_01 through opt_10 keys containing strike prices
        """
        try:
            logger.info(f"Calculating options levels for {ticker} on {date_str}")

            # Get current price if not provided
            if not last_price:
                last_price = self._get_current_price(ticker)
                if not last_price:
                    logger.error(f"Could not determine price for {ticker}")
                    return self._empty_results()

            logger.info(f"Using price: ${last_price:.2f}")

            # Get next 4 expiration dates
            expiration_dates = self._get_nearest_expirations(date_str, count=4)
            logger.info(f"Checking expirations: {expiration_dates}")

            # Collect all options data
            all_strikes_data = {}

            for exp_date in expiration_dates:
                strikes_for_exp = self._fetch_options_for_expiration(
                    ticker, exp_date, last_price, price_range_pct
                )

                # Aggregate open interest by strike
                for strike, oi in strikes_for_exp.items():
                    if strike in all_strikes_data:
                        all_strikes_data[strike] += oi
                    else:
                        all_strikes_data[strike] = oi

            # Sort strikes by total open interest
            sorted_strikes = sorted(
                all_strikes_data.items(),
                key=lambda x: x[1],
                reverse=True
            )[:num_levels]

            # Format results with naming convention
            results = {}
            for i, (strike, oi) in enumerate(sorted_strikes, 1):
                results[f'opt_{i:02d}'] = float(strike)
                results[f'opt_{i:02d}_oi'] = int(oi)

            # Fill remaining slots with 0
            for i in range(len(sorted_strikes) + 1, num_levels + 1):
                results[f'opt_{i:02d}'] = 0.0
                results[f'opt_{i:02d}_oi'] = 0

            logger.info(f"Found {len(sorted_strikes)} significant options levels")
            return results

        except Exception as e:
            logger.error(f"Error calculating options levels: {str(e)}")
            return self._empty_results()

    def _fetch_options_for_expiration(self,
                                      ticker: str,
                                      exp_date: str,
                                      last_price: float,
                                      price_range_pct: float) -> Dict[float, int]:
        """
        Fetch options data for a specific expiration date
        """
        strikes_data = {}

        try:
            # Calculate price range to filter strikes
            min_strike = last_price * (1 - price_range_pct)
            max_strike = last_price * (1 + price_range_pct)

            logger.info(f"  Fetching options for {exp_date} (strikes ${min_strike:.0f}-${max_strike:.0f})")

            # List all options contracts for this expiration
            contracts = list(self.client.list_options_contracts(  # <-- FIXED: self.client
                underlying_ticker=ticker,
                expiration_date=exp_date,
                strike_price_gte=min_strike,
                strike_price_lte=max_strike,
                limit=500
            ))

            logger.info(f"    Found {len(contracts)} contracts")

            contracts_with_oi = 0

            # Process each contract
            for contract in contracts:
                try:
                    # Get snapshot using correct positional arguments
                    snapshot = self.client.get_snapshot_option(
                        ticker,  # underlying ticker (positional)
                        contract.ticker  # option ticker (positional)
                    )

                    # Access open_interest directly from snapshot
                    if snapshot and hasattr(snapshot, 'open_interest'):
                        oi = snapshot.open_interest

                        if oi and oi > 0:
                            strike = float(contract.strike_price)
                            oi_int = int(oi)

                            # Aggregate calls and puts at same strike
                            if strike in strikes_data:
                                strikes_data[strike] += oi_int
                            else:
                                strikes_data[strike] = oi_int

                            contracts_with_oi += 1

                except Exception as e:
                    # Continue if individual contract fails
                    continue

            logger.info(f"    Processed {len(contracts)} contracts, {contracts_with_oi} had open interest")
            logger.info(f"    Found {len(strikes_data)} unique strikes with OI")

        except Exception as e:
            logger.error(f"  Error fetching options for {exp_date}: {str(e)}")

        return strikes_data

    def _get_nearest_expirations(self, date_str: str, count: int = 4) -> List[str]:
        """Get the nearest option expiration dates (Fridays)"""
        reference_date = datetime.strptime(date_str, "%Y-%m-%d")

        expirations = []
        current_date = reference_date

        while len(expirations) < count:
            # Calculate days until next Friday (weekday 4)
            days_ahead = 4 - current_date.weekday()
            if days_ahead <= 0:
                days_ahead += 7

            next_friday = current_date + timedelta(days=days_ahead)
            expirations.append(next_friday.strftime("%Y-%m-%d"))

            # Move to next week
            current_date = next_friday + timedelta(days=1)

        return expirations

    def _get_current_price(self, ticker: str) -> Optional[float]:
        """Get current price for ticker from Polygon"""
        try:
            # Try to get data from the last few days
            for days_back in range(5):
                check_date = (datetime.now() - timedelta(days=days_back))
                date_str = check_date.strftime("%Y-%m-%d")

                response = self.client.get_aggs(
                    ticker=ticker,
                    multiplier=1,
                    timespan="day",
                    from_=date_str,
                    to=date_str,
                    adjusted=True,
                    limit=1
                )

                if response and len(response) > 0:
                    return float(response[0].close)

        except Exception as e:
            logger.error(f"Could not fetch price for {ticker}: {e}")

        return None

    def _empty_results(self) -> Dict:
        """Return empty results structure with all zeros"""
        results = {}
        for i in range(1, 11):
            results[f'opt_{i:02d}'] = 0.0
            results[f'opt_{i:02d}_oi'] = 0
        return results
"""
Options Levels Calculator for Epoch Analysis Tool

Ported from: 02_zone_system/03_bar_data/calculations/options_calculator.py

Identifies top 10 options strikes by open interest to use as confluence zones.
These levels act as price magnets due to gamma hedging and pinning effects.

Supports market time mode (Pre-Market/Post-Market/Live) via end_timestamp
parameter to ensure price is fetched at the correct cutoff time.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from data import get_polygon_client

logger = logging.getLogger(__name__)


class OptionsCalculator:
    """
    Calculates top options strike levels based on open interest.
    These levels act as price magnets due to gamma hedging and pinning effects.
    """

    def __init__(self):
        """Initialize with Polygon client."""
        self.client = get_polygon_client()

    def calculate_options_levels(
        self,
        ticker: str,
        analysis_date: date,
        last_price: float = None,
        num_levels: int = 10,
        price_range_pct: float = 0.15,
        end_timestamp: datetime = None
    ) -> List[float]:
        """
        Get top options levels by open interest.

        Args:
            ticker: Stock symbol (e.g., "AAPL")
            analysis_date: Reference date
            last_price: Current stock price (optional, will fetch if not provided)
            num_levels: Number of top strike levels to return (default 10)
            price_range_pct: Percentage range around current price to consider (default 15%)
            end_timestamp: Optional precise end timestamp for pre/post market mode.
                          If provided and last_price is None, uses price at this
                          timestamp instead of current price.

        Returns:
            List of top strike prices sorted by open interest (highest OI first)
        """
        try:
            logger.info(f"Calculating options levels for {ticker}")

            # Get current price if not provided (respects market time mode)
            if not last_price:
                last_price = self.client.get_current_price(ticker, end_timestamp=end_timestamp)
                if not last_price:
                    logger.warning(f"Could not determine price for {ticker}, skipping options")
                    return []

            logger.debug(f"  Using price: ${last_price:.2f}")

            # Get next 4 expiration dates
            date_str = analysis_date.strftime("%Y-%m-%d")
            expiration_dates = self._get_nearest_expirations(date_str, count=4)
            logger.debug(f"  Checking expirations: {expiration_dates}")

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

            # Return just the strike prices (not OI)
            result = [float(strike) for strike, oi in sorted_strikes]

            logger.info(f"  Found {len(result)} significant options levels for {ticker}")
            return result

        except Exception as e:
            logger.error(f"Error calculating options levels for {ticker}: {str(e)}")
            return []

    def _fetch_options_for_expiration(
        self,
        ticker: str,
        exp_date: str,
        last_price: float,
        price_range_pct: float
    ) -> Dict[float, int]:
        """
        Fetch options data for a specific expiration date.

        Returns:
            Dict mapping strike price to total open interest
        """
        strikes_data = {}

        try:
            # Calculate price range to filter strikes
            min_strike = last_price * (1 - price_range_pct)
            max_strike = last_price * (1 + price_range_pct)

            logger.debug(f"    Fetching options for {exp_date} (strikes ${min_strike:.0f}-${max_strike:.0f})")

            # Use polygon client's raw client for options
            raw_client = self.client.client

            # List all options contracts for this expiration
            contracts = list(raw_client.list_options_contracts(
                underlying_ticker=ticker,
                expiration_date=exp_date,
                strike_price_gte=min_strike,
                strike_price_lte=max_strike,
                limit=500
            ))

            logger.debug(f"      Found {len(contracts)} contracts")

            contracts_with_oi = 0

            # Process each contract
            for contract in contracts:
                try:
                    # Get snapshot for open interest
                    snapshot = raw_client.get_snapshot_option(
                        ticker,  # underlying ticker
                        contract.ticker  # option ticker
                    )

                    # Access open_interest from snapshot
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

                except Exception:
                    # Continue if individual contract fails
                    continue

            logger.debug(f"      {contracts_with_oi} contracts had open interest")

        except Exception as e:
            logger.debug(f"    Error fetching options for {exp_date}: {str(e)}")

        return strikes_data

    def _get_nearest_expirations(self, date_str: str, count: int = 4) -> List[str]:
        """Get the nearest option expiration dates (Fridays)."""
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


# =========================================================================
# CONVENIENCE FUNCTION
# =========================================================================

def calculate_options_levels(
    ticker: str,
    analysis_date: date,
    last_price: float = None,
    num_levels: int = 10,
    end_timestamp: datetime = None
) -> List[float]:
    """
    Calculate top options levels by open interest.

    Args:
        ticker: Stock symbol
        analysis_date: Reference date
        last_price: Current stock price (optional)
        num_levels: Number of levels to return (default 10)
        end_timestamp: Optional precise end timestamp for pre/post market mode.
                      If provided and last_price is None, uses price at this
                      timestamp instead of current price.

    Returns:
        List of top strike prices sorted by open interest
    """
    calc = OptionsCalculator()
    return calc.calculate_options_levels(
        ticker=ticker,
        analysis_date=analysis_date,
        last_price=last_price,
        num_levels=num_levels,
        end_timestamp=end_timestamp
    )

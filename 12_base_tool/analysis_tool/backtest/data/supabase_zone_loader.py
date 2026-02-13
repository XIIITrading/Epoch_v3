"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: BACKTESTER v2.0
Supabase Zone Loader - Load Zone Data from Supabase
XIII Trading LLC
================================================================================

Loads Primary and Secondary zone data from Supabase setups table.
Alternative to Excel-based zone_loader.py for automated backtesting workflow.

Usage:
    loader = SupabaseZoneLoader('2026-01-20')
    primary_zones = loader.load_primary_zones()
    secondary_zones = loader.load_secondary_zones()
================================================================================
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, datetime
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass

# Import the same ZoneData structure for compatibility
# Handle both relative and absolute imports
try:
    from .zone_loader import ZoneData
except ImportError:
    from zone_loader import ZoneData

# Database configuration (same as analysis_tool exporter)
SUPABASE_HOST = "db.pdbmcskznoaiybdiobje.supabase.co"
SUPABASE_PORT = 5432
SUPABASE_DATABASE = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "guid-saltation-covet"

DB_CONFIG = {
    "host": SUPABASE_HOST,
    "port": SUPABASE_PORT,
    "database": SUPABASE_DATABASE,
    "user": SUPABASE_USER,
    "password": SUPABASE_PASSWORD,
    "sslmode": "require"
}


class SupabaseZoneLoader:
    """
    Loads zone data from Supabase setups table.

    Compatible interface with ExcelZoneLoader - returns same ZoneData objects.
    """

    def __init__(self, trade_date: str, verbose: bool = True):
        """
        Initialize with a specific trading date.

        Args:
            trade_date: Trading date in YYYY-MM-DD format or date object
            verbose: Whether to print loading information
        """
        self.verbose = verbose
        self.conn = None

        # Parse date
        if isinstance(trade_date, date):
            self.trade_date = trade_date
        elif isinstance(trade_date, str):
            self.trade_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
        else:
            raise ValueError(f"Invalid date format: {trade_date}")

        self._connect()

    def _connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            if self.verbose:
                print(f"  Connected to Supabase")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Supabase: {e}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_trading_date(self) -> Optional[str]:
        """
        Return the trading date in YYYY-MM-DD format.

        Returns:
            Date string in YYYY-MM-DD format
        """
        return self.trade_date.strftime('%Y-%m-%d')

    def load_primary_zones(self) -> List[ZoneData]:
        """Load all Primary zones from Supabase setups table."""
        return self._load_zones_by_type('PRIMARY')

    def load_secondary_zones(self) -> List[ZoneData]:
        """Load all Secondary zones from Supabase setups table."""
        return self._load_zones_by_type('SECONDARY')

    def _load_zones_by_type(self, setup_type: str) -> List[ZoneData]:
        """
        Load zones of a specific type from Supabase.

        Args:
            setup_type: 'PRIMARY' or 'SECONDARY'

        Returns:
            List of ZoneData objects
        """
        query = """
            SELECT
                ticker,
                ticker_id,
                zone_id,
                direction,
                hvn_poc,
                zone_high,
                zone_low,
                target_id,
                target_price,
                risk_reward
            FROM setups
            WHERE date = %s
              AND setup_type = %s
            ORDER BY ticker
        """

        zones = []

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (self.trade_date, setup_type))
                rows = cur.fetchall()

            for row in rows:
                # Skip if missing critical data
                zone_high = self._safe_float(row.get('zone_high'))
                zone_low = self._safe_float(row.get('zone_low'))

                if zone_high is None or zone_low is None:
                    if self.verbose:
                        print(f"  Skipping {setup_type} {row.get('ticker')}: missing zone_high or zone_low")
                    continue

                # Validate and swap if needed
                if zone_high < zone_low:
                    if self.verbose:
                        print(f"  Warning {setup_type} {row.get('ticker')}: zone_high < zone_low, swapping")
                    zone_high, zone_low = zone_low, zone_high

                hvn_poc = self._safe_float(row.get('hvn_poc')) or (zone_high + zone_low) / 2
                target = self._safe_float(row.get('target_price'))

                zone = ZoneData(
                    ticker=str(row.get('ticker', '')),
                    ticker_id=str(row.get('ticker_id', '')),
                    zone_id=str(row.get('zone_id', '')),
                    direction=str(row.get('direction', '')),
                    hvn_poc=hvn_poc,
                    zone_high=zone_high,
                    zone_low=zone_low,
                    tier=None,  # Not stored in setups table
                    target_id=str(row.get('target_id', '')) if row.get('target_id') else None,
                    target=target,
                    rr=self._safe_float(row.get('risk_reward')),
                    zone_type=setup_type
                )
                zones.append(zone)

                if self.verbose:
                    target_str = f"${target:.2f}" if target else "None"
                    print(f"  Loaded {setup_type}: {zone.ticker} "
                          f"Zone: ${zone.zone_low:.2f}-${zone.zone_high:.2f} "
                          f"Target: {target_str}")

        except Exception as e:
            print(f"  Error loading {setup_type} zones: {e}")
            if self.conn:
                self.conn.rollback()

        return zones

    def load_all_zones(self) -> Tuple[List[ZoneData], List[ZoneData]]:
        """Load all zones (primary and secondary)"""
        primary = self.load_primary_zones()
        secondary = self.load_secondary_zones()
        return primary, secondary

    def get_zones_for_ticker(self, ticker: str) -> Tuple[Optional[ZoneData], Optional[ZoneData]]:
        """
        Get Primary and Secondary zones for a specific ticker.

        Returns: (primary_zone, secondary_zone) - either can be None
        """
        primary_zones, secondary_zones = self.load_all_zones()

        primary = next((z for z in primary_zones if z.ticker.upper() == ticker.upper()), None)
        secondary = next((z for z in secondary_zones if z.ticker.upper() == ticker.upper()), None)

        return primary, secondary

    def get_zone_dict(self, zone: ZoneData) -> Dict:
        """Convert ZoneData to dict format for TradeSimulator"""
        return {
            'zone_high': zone.zone_high,
            'zone_low': zone.zone_low,
            'hvn_poc': zone.hvn_poc,
            'target': zone.target
        }

    def get_available_dates(self, limit: int = 30) -> List[date]:
        """
        Get list of dates that have setups data in Supabase.

        Args:
            limit: Maximum number of dates to return

        Returns:
            List of dates with setup data, most recent first
        """
        query = """
            SELECT DISTINCT date
            FROM setups
            ORDER BY date DESC
            LIMIT %s
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (limit,))
                rows = cur.fetchall()
            return [row[0] for row in rows]

        except Exception as e:
            print(f"  Error fetching available dates: {e}")
            return []

    def get_setup_count(self) -> Dict[str, int]:
        """
        Get count of setups for the trading date.

        Returns:
            Dict with 'primary' and 'secondary' counts
        """
        query = """
            SELECT setup_type, COUNT(*) as count
            FROM setups
            WHERE date = %s
            GROUP BY setup_type
        """

        result = {'PRIMARY': 0, 'SECONDARY': 0}

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (self.trade_date,))
                rows = cur.fetchall()

            for row in rows:
                result[row['setup_type']] = row['count']

        except Exception as e:
            print(f"  Error counting setups: {e}")

        return result

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """Safely convert to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


def test_connection(trade_date: str = None) -> bool:
    """
    Test Supabase connection and show available data.

    Args:
        trade_date: Optional date to query (YYYY-MM-DD), defaults to today

    Returns:
        True if connection successful
    """
    if trade_date is None:
        trade_date = date.today().strftime('%Y-%m-%d')

    print(f"\n{'='*60}")
    print(f"SUPABASE ZONE LOADER TEST")
    print(f"{'='*60}")
    print(f"Trading Date: {trade_date}")

    try:
        with SupabaseZoneLoader(trade_date) as loader:
            # Show available dates
            dates = loader.get_available_dates(10)
            print(f"\nRecent dates with setups:")
            for d in dates[:5]:
                print(f"  - {d}")

            # Show counts for requested date
            counts = loader.get_setup_count()
            print(f"\nSetups for {trade_date}:")
            print(f"  PRIMARY:   {counts['PRIMARY']}")
            print(f"  SECONDARY: {counts['SECONDARY']}")

            if counts['PRIMARY'] > 0 or counts['SECONDARY'] > 0:
                print(f"\n--- Loading Zones ---")
                primary, secondary = loader.load_all_zones()

                print(f"\nLoaded {len(primary)} PRIMARY zones")
                print(f"Loaded {len(secondary)} SECONDARY zones")

                return True
            else:
                print(f"\nNo setups found for {trade_date}")
                return True

    except Exception as e:
        print(f"\nConnection failed: {e}")
        return False


if __name__ == "__main__":
    import sys

    # Allow passing date as command line argument
    if len(sys.argv) > 1:
        test_date = sys.argv[1]
    else:
        test_date = None

    success = test_connection(test_date)
    print(f"\n{'='*60}")
    print(f"Test {'PASSED' if success else 'FAILED'}")
    print(f"{'='*60}")

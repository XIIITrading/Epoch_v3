"""
DOW AI - Supabase Reader
Epoch Trading System v2.0 - XIII Trading LLC

Reads zone data, bar_data, and analysis info from Supabase.
Drop-in replacement for EpochReader (Excel-based) with the same interface.
"""
import psycopg2
import psycopg2.extras
import pandas as pd
from typing import Optional, Dict, List, Any
from datetime import datetime, date
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import VERBOSE, debug_print

# =============================================================================
# Supabase Configuration
# =============================================================================
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


class SupabaseReader:
    """
    Reads data from Supabase PostgreSQL database.
    Drop-in replacement for EpochReader with identical interface.

    Usage:
        reader = SupabaseReader()
        if reader.connect():
            zone = reader.get_primary_zone('AAPL')
            pocs = reader.read_hvn_pocs('AAPL')
    """

    def __init__(self, session_date: date = None, verbose: bool = None):
        """
        Initialize Supabase reader.

        Args:
            session_date: Trading session date (defaults to today)
            verbose: Enable verbose output (uses config if not provided)
        """
        self.session_date = session_date or date.today()
        self.verbose = verbose if verbose is not None else VERBOSE
        self._conn = None
        self._cursor = None

        if self.verbose:
            debug_print(f"SupabaseReader initialized for date: {self.session_date}")

    def connect(self) -> bool:
        """
        Connect to Supabase PostgreSQL database.

        Returns:
            True if connected successfully, False otherwise
        """
        try:
            self._conn = psycopg2.connect(**DB_CONFIG)
            self._cursor = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            if self.verbose:
                debug_print(f"Connected to Supabase: {SUPABASE_HOST}")
            return True

        except Exception as e:
            if self.verbose:
                debug_print(f"Error connecting to Supabase: {e}")
            print(f"\nERROR: Could not connect to Supabase database.")
            print(f"Check your network connection and credentials.")
            return False

    def close(self):
        """Close database connection."""
        if self._cursor:
            self._cursor.close()
        if self._conn:
            self._conn.close()
        if self.verbose:
            debug_print("Supabase connection closed")

    def set_session_date(self, session_date: date):
        """Update the session date for queries."""
        self.session_date = session_date
        if self.verbose:
            debug_print(f"Session date set to: {self.session_date}")

    # =========================================================================
    # ZONE DATA (from zones table)
    # =========================================================================

    def read_zone_results(self, ticker: str = None) -> pd.DataFrame:
        """
        Read filtered zones from zones table.

        Args:
            ticker: Optional filter by ticker symbol

        Returns:
            DataFrame with all zone data
        """
        query = """
            SELECT
                ticker_id, ticker, date, price, direction, zone_id,
                hvn_poc, zone_high, zone_low, overlap_count as overlaps,
                score, rank, confluences,
                is_epch_bull as epch_bull, is_epch_bear as epch_bear,
                epch_bull_price, epch_bear_price,
                epch_bull_target, epch_bear_target
            FROM zones
            WHERE date = %s
        """
        params = [self.session_date]

        if ticker:
            query += " AND UPPER(ticker) = UPPER(%s)"
            params.append(ticker)

        query += " ORDER BY ticker, score DESC"

        try:
            self._cursor.execute(query, params)
            rows = self._cursor.fetchall()

            if not rows:
                if self.verbose:
                    debug_print(f"No zones found for date {self.session_date}")
                return pd.DataFrame()

            df = pd.DataFrame(rows)

            if self.verbose:
                debug_print(f"Read {len(df)} zones from Supabase")

            return df

        except Exception as e:
            if self.verbose:
                debug_print(f"Error reading zones: {e}")
            return pd.DataFrame()

    def get_primary_zone(self, ticker: str, direction: str = None) -> Optional[Dict]:
        """
        Get PRIMARY zone from setups table.
        These are WITH-TREND setups (EPCH_01, EPCH_02).

        Args:
            ticker: Stock symbol
            direction: Not used (direction is in the data), kept for compatibility

        Returns:
            Dict with zone info or None
        """
        query = """
            SELECT
                ticker, direction, ticker_id, zone_id,
                hvn_poc, zone_high, zone_low,
                target_id, target_price as target, risk_reward as r_r
            FROM setups
            WHERE date = %s
              AND UPPER(ticker) = UPPER(%s)
              AND setup_type = 'PRIMARY'
        """

        try:
            self._cursor.execute(query, [self.session_date, ticker])
            row = self._cursor.fetchone()

            if not row:
                if self.verbose:
                    debug_print(f"No PRIMARY zone found for {ticker}")
                return None

            if self.verbose:
                debug_print(f"Found PRIMARY zone for {ticker}: {row['zone_id']}")

            return {
                'ticker': row['ticker'],
                'direction': row['direction'] or '',
                'ticker_id': row['ticker_id'],
                'zone_id': row['zone_id'] or '',
                'hvn_poc': float(row['hvn_poc']) if row['hvn_poc'] else None,
                'zone_high': float(row['zone_high']) if row['zone_high'] else None,
                'zone_low': float(row['zone_low']) if row['zone_low'] else None,
                'tier': '',  # Not in setups table
                'target_id': row['target_id'] or '',
                'target': float(row['target']) if row['target'] else None,
                'r_r': float(row['r_r']) if row['r_r'] else None,
                'zone_type': 'primary',
                'setup_type': 'with-trend',
                'rank': row['zone_id'] or '',
                'score': 0.0,
                'confluences': ''
            }

        except Exception as e:
            if self.verbose:
                debug_print(f"Error getting primary zone: {e}")
            return None

    def get_secondary_zone(self, ticker: str, direction: str = None) -> Optional[Dict]:
        """
        Get SECONDARY zone from setups table.
        These are COUNTER-TREND setups (EPCH_03, EPCH_04).

        Args:
            ticker: Stock symbol
            direction: Not used (direction is in the data), kept for compatibility

        Returns:
            Dict with zone info or None
        """
        query = """
            SELECT
                ticker, direction, ticker_id, zone_id,
                hvn_poc, zone_high, zone_low,
                target_id, target_price as target, risk_reward as r_r
            FROM setups
            WHERE date = %s
              AND UPPER(ticker) = UPPER(%s)
              AND setup_type = 'SECONDARY'
        """

        try:
            self._cursor.execute(query, [self.session_date, ticker])
            row = self._cursor.fetchone()

            if not row:
                if self.verbose:
                    debug_print(f"No SECONDARY zone found for {ticker}")
                return None

            if self.verbose:
                debug_print(f"Found SECONDARY zone for {ticker}: {row['zone_id']}")

            return {
                'ticker': row['ticker'],
                'direction': row['direction'] or '',
                'ticker_id': row['ticker_id'],
                'zone_id': row['zone_id'] or '',
                'hvn_poc': float(row['hvn_poc']) if row['hvn_poc'] else None,
                'zone_high': float(row['zone_high']) if row['zone_high'] else None,
                'zone_low': float(row['zone_low']) if row['zone_low'] else None,
                'tier': '',  # Not in setups table
                'target_id': row['target_id'] or '',
                'target': float(row['target']) if row['target'] else None,
                'r_r': float(row['r_r']) if row['r_r'] else None,
                'zone_type': 'secondary',
                'setup_type': 'counter-trend',
                'rank': row['zone_id'] or '',
                'score': 0.0,
                'confluences': ''
            }

        except Exception as e:
            if self.verbose:
                debug_print(f"Error getting secondary zone: {e}")
            return None

    def get_zone_for_model(self, ticker: str, model: str) -> Optional[Dict]:
        """
        Get the appropriate zone based on EPCH model.

        Args:
            ticker: Stock symbol
            model: EPCH_01, EPCH_02, EPCH_03, or EPCH_04

        Returns:
            Dict with zone info or None
        """
        model = model.upper()

        if model in ['EPCH_01', 'EPCH_02']:
            zone = self.get_primary_zone(ticker)
            if zone:
                zone['models'] = 'EPCH_01 (continuation) | EPCH_02 (reversal)'
            return zone

        elif model in ['EPCH_03', 'EPCH_04']:
            zone = self.get_secondary_zone(ticker)
            if zone:
                zone['models'] = 'EPCH_03 (continuation) | EPCH_04 (reversal)'
            return zone

        else:
            if self.verbose:
                debug_print(f"Unknown model: {model}, defaulting to primary")
            return self.get_primary_zone(ticker)

    def get_zone_for_ticker(self, ticker: str) -> Optional[Dict]:
        """
        Get the primary zone for a ticker (used by entry qualifier).

        Args:
            ticker: Stock symbol

        Returns:
            Dict with zone info or None
        """
        return self.get_primary_zone(ticker)

    def get_both_zones(self, ticker: str) -> Dict[str, Optional[Dict]]:
        """
        Get BOTH primary and secondary zones for complete analysis.

        Args:
            ticker: Stock symbol

        Returns:
            Dict with 'primary' and 'secondary' keys
        """
        return {
            'primary': self.get_primary_zone(ticker),
            'secondary': self.get_secondary_zone(ticker)
        }

    # =========================================================================
    # BAR DATA (from bar_data table)
    # =========================================================================

    def read_hvn_pocs(self, ticker: str) -> List[float]:
        """
        Read HVN POC levels from hvn_pocs table.

        Args:
            ticker: Stock symbol

        Returns:
            List of up to 10 POC prices
        """
        query = """
            SELECT poc_1, poc_2, poc_3, poc_4, poc_5,
                   poc_6, poc_7, poc_8, poc_9, poc_10
            FROM hvn_pocs
            WHERE date = %s AND UPPER(ticker) = UPPER(%s)
        """

        try:
            self._cursor.execute(query, [self.session_date, ticker])
            row = self._cursor.fetchone()

            if not row:
                if self.verbose:
                    debug_print(f"No HVN POCs found for {ticker}")
                return []

            # Collect non-null POCs
            pocs = []
            for i in range(1, 11):
                val = row.get(f'poc_{i}')
                if val is not None:
                    pocs.append(float(val))

            if self.verbose:
                debug_print(f"Read {len(pocs)} HVN POCs for {ticker}")

            return pocs

        except Exception as e:
            if self.verbose:
                debug_print(f"Error reading HVN POCs: {e}")
            return []

    def read_camarilla_levels(self, ticker: str) -> Dict[str, Optional[float]]:
        """
        Read Camarilla pivot levels from bar_data table.

        Args:
            ticker: Stock symbol

        Returns:
            Dict with d1_s6, d1_s4, d1_s3, d1_r3, d1_r4, d1_r6, etc.
        """
        query = """
            SELECT
                d1_cam_s6, d1_cam_s4, d1_cam_s3, d1_cam_r3, d1_cam_r4, d1_cam_r6,
                w1_cam_s6, w1_cam_s4, w1_cam_s3, w1_cam_r3, w1_cam_r4, w1_cam_r6,
                m1_cam_s6, m1_cam_s4, m1_cam_s3, m1_cam_r3, m1_cam_r4, m1_cam_r6
            FROM bar_data
            WHERE date = %s AND UPPER(ticker) = UPPER(%s)
        """

        try:
            self._cursor.execute(query, [self.session_date, ticker])
            row = self._cursor.fetchone()

            if not row:
                if self.verbose:
                    debug_print(f"No Camarilla levels found for {ticker}")
                return {}

            # Convert to the format expected by DOW_AI (d1_s6 instead of d1_cam_s6)
            result = {}
            for key, val in row.items():
                # Convert d1_cam_s6 -> d1_s6
                new_key = key.replace('_cam_', '_')
                result[new_key] = float(val) if val is not None else None

            return result

        except Exception as e:
            if self.verbose:
                debug_print(f"Error reading Camarilla levels: {e}")
            return {}

    def read_atr(self, ticker: str, timeframe: str = 'd1') -> Optional[float]:
        """
        Read ATR from bar_data table.

        Args:
            ticker: Stock symbol
            timeframe: ATR timeframe ('m5', 'm15', 'h1', 'd1')

        Returns:
            ATR value or None
        """
        atr_col = f'{timeframe}_atr'
        query = f"""
            SELECT {atr_col}
            FROM bar_data
            WHERE date = %s AND UPPER(ticker) = UPPER(%s)
        """

        try:
            self._cursor.execute(query, [self.session_date, ticker])
            row = self._cursor.fetchone()

            if not row:
                if self.verbose:
                    debug_print(f"No ATR found for {ticker}")
                return None

            val = row.get(atr_col)
            return float(val) if val is not None else None

        except Exception as e:
            if self.verbose:
                debug_print(f"Error reading ATR: {e}")
            return None

    def read_overnight_levels(self, ticker: str) -> Dict[str, Optional[float]]:
        """
        Read overnight high/low from bar_data table.

        Args:
            ticker: Stock symbol

        Returns:
            Dict with 'd1_onh' and 'd1_onl'
        """
        query = """
            SELECT d1_overnight_high, d1_overnight_low
            FROM bar_data
            WHERE date = %s AND UPPER(ticker) = UPPER(%s)
        """

        try:
            self._cursor.execute(query, [self.session_date, ticker])
            row = self._cursor.fetchone()

            if not row:
                return {}

            return {
                'd1_onh': float(row['d1_overnight_high']) if row['d1_overnight_high'] else None,
                'd1_onl': float(row['d1_overnight_low']) if row['d1_overnight_low'] else None
            }

        except Exception as e:
            if self.verbose:
                debug_print(f"Error reading overnight levels: {e}")
            return {}

    # =========================================================================
    # ANALYSIS DATA (from setups table)
    # =========================================================================

    def read_analysis_setups(self, ticker: str) -> Dict[str, Optional[Dict]]:
        """
        Read primary and secondary setups from setups table.

        Args:
            ticker: Stock symbol

        Returns:
            Dict with 'primary' and 'secondary' setup info
        """
        return {
            'primary': self.get_primary_zone(ticker),
            'secondary': self.get_secondary_zone(ticker)
        }

    # =========================================================================
    # MARKET OVERVIEW (from market_structure table)
    # =========================================================================

    def read_market_structure(self, ticker: str) -> Dict[str, Any]:
        """
        Read market structure from market_structure table.

        Args:
            ticker: Stock symbol

        Returns:
            Dict with direction and levels for each timeframe
        """
        query = """
            SELECT
                scan_price as price,
                d1_direction, d1_strong, d1_weak,
                h4_direction, h4_strong, h4_weak,
                h1_direction, h1_strong, h1_weak,
                m15_direction, m15_strong, m15_weak,
                composite_direction
            FROM market_structure
            WHERE date = %s AND UPPER(ticker) = UPPER(%s)
        """

        try:
            self._cursor.execute(query, [self.session_date, ticker])
            row = self._cursor.fetchone()

            if not row:
                if self.verbose:
                    debug_print(f"No market structure found for {ticker}")
                return {}

            return {
                'price': float(row['price']) if row['price'] else None,
                'd1': {
                    'direction': row['d1_direction'],
                    'strong': float(row['d1_strong']) if row['d1_strong'] else None,
                    'weak': float(row['d1_weak']) if row['d1_weak'] else None,
                },
                'h4': {
                    'direction': row['h4_direction'],
                    'strong': float(row['h4_strong']) if row['h4_strong'] else None,
                    'weak': float(row['h4_weak']) if row['h4_weak'] else None,
                },
                'h1': {
                    'direction': row['h1_direction'],
                    'strong': float(row['h1_strong']) if row['h1_strong'] else None,
                    'weak': float(row['h1_weak']) if row['h1_weak'] else None,
                },
                'm15': {
                    'direction': row['m15_direction'],
                    'strong': float(row['m15_strong']) if row['m15_strong'] else None,
                    'weak': float(row['m15_weak']) if row['m15_weak'] else None,
                },
                'composite': row['composite_direction'],
            }

        except Exception as e:
            if self.verbose:
                debug_print(f"Error reading market structure: {e}")
            return {}

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_available_tickers(self) -> List[str]:
        """
        Get list of tickers available for the session date.

        Returns:
            List of ticker symbols
        """
        query = """
            SELECT DISTINCT ticker
            FROM setups
            WHERE date = %s
            ORDER BY ticker
        """

        try:
            self._cursor.execute(query, [self.session_date])
            rows = self._cursor.fetchall()
            return [row['ticker'] for row in rows]
        except Exception as e:
            if self.verbose:
                debug_print(f"Error getting tickers: {e}")
            return []

    def get_latest_session_date(self) -> Optional[date]:
        """
        Get the most recent session date in the database.

        Returns:
            Most recent date or None
        """
        query = "SELECT MAX(date) as latest FROM daily_sessions"

        try:
            self._cursor.execute(query)
            row = self._cursor.fetchone()
            return row['latest'] if row else None
        except Exception as e:
            if self.verbose:
                debug_print(f"Error getting latest date: {e}")
            return None


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("SUPABASE READER - STANDALONE TEST")
    print("=" * 60)

    reader = SupabaseReader(verbose=True)

    # Test connection
    print("\n[TEST 1] Connecting to Supabase...")
    if not reader.connect():
        print("  FAILED: Could not connect to Supabase")
        sys.exit(1)
    print("  SUCCESS: Connected to Supabase\n")

    # Get latest session date
    print("[TEST 2] Getting latest session date...")
    latest_date = reader.get_latest_session_date()
    if latest_date:
        print(f"  Latest session: {latest_date}")
        reader.set_session_date(latest_date)
    else:
        print("  No sessions found in database")
        reader.close()
        sys.exit(1)

    # Get available tickers
    print("\n[TEST 3] Getting available tickers...")
    tickers = reader.get_available_tickers()
    print(f"  Found {len(tickers)} tickers: {tickers[:5]}...")

    if tickers:
        test_ticker = tickers[0]

        # Test zone reading
        print(f"\n[TEST 4] Reading zone_results for {test_ticker}...")
        df = reader.read_zone_results(test_ticker)
        print(f"  Found {len(df)} zones")

        # Test primary zone
        print(f"\n[TEST 5] Getting primary zone for {test_ticker}...")
        zone = reader.get_primary_zone(test_ticker)
        if zone:
            print(f"  Zone ID: {zone['zone_id']}")
            print(f"  Range: ${zone['zone_low']:.2f} - ${zone['zone_high']:.2f}")
            print(f"  HVN POC: ${zone['hvn_poc']:.2f}")
            print(f"  Target: ${zone['target']:.2f}" if zone['target'] else "  Target: N/A")
        else:
            print("  No primary zone found")

        # Test HVN POCs
        print(f"\n[TEST 6] Reading HVN POCs for {test_ticker}...")
        pocs = reader.read_hvn_pocs(test_ticker)
        if pocs:
            print(f"  POCs: {['${:.2f}'.format(p) for p in pocs[:5]]}")
        else:
            print("  No POCs found")

        # Test Camarilla
        print(f"\n[TEST 7] Reading Camarilla levels for {test_ticker}...")
        cam = reader.read_camarilla_levels(test_ticker)
        if cam:
            print(f"  D1 S3: ${cam.get('d1_s3', 'N/A')}")
            print(f"  D1 R3: ${cam.get('d1_r3', 'N/A')}")
        else:
            print("  No Camarilla levels found")

        # Test ATR
        print(f"\n[TEST 8] Reading D1 ATR for {test_ticker}...")
        atr = reader.read_atr(test_ticker, 'd1')
        if atr:
            print(f"  D1 ATR: ${atr:.2f}")
        else:
            print("  No ATR found")

        # Test market structure
        print(f"\n[TEST 9] Reading market structure for {test_ticker}...")
        structure = reader.read_market_structure(test_ticker)
        if structure:
            print(f"  D1: {structure['d1']['direction']}")
            print(f"  H4: {structure['h4']['direction']}")
            print(f"  Composite: {structure['composite']}")
        else:
            print("  No market structure found")

    reader.close()
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

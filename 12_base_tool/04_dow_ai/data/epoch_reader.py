"""
DOW AI - Epoch Excel Reader
Epoch Trading System v1 - XIII Trading LLC

Reads zone data, bar_data, and analysis info from the Epoch Excel workbook.
Uses xlwings to connect to the open workbook.
"""
import xlwings as xw
import pandas as pd
from typing import Optional, Dict, List, Any
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    EXCEL_FILEPATH,
    EXCEL_WORKSHEETS,
    TICKER_ROWS,
    BAR_DATA_COLUMNS,
    ZONE_RESULTS_COLUMNS,
    ANALYSIS_REFS,
    MARKET_OVERVIEW_COLUMNS,
    MARKET_OVERVIEW_ROWS,
    VERBOSE,
    debug_print
)


class EpochReader:
    """
    Reads data from the Epoch Excel workbook using xlwings.
    Workbook must be open in Excel for xlwings to connect.
    """

    def __init__(self, filepath: str = None, verbose: bool = None):
        """
        Initialize Epoch reader.

        Args:
            filepath: Path to Excel workbook (uses config if not provided)
            verbose: Enable verbose output (uses config if not provided)
        """
        self.filepath = filepath or str(EXCEL_FILEPATH)
        self.verbose = verbose if verbose is not None else VERBOSE
        self._wb = None

        if self.verbose:
            debug_print("EpochReader initialized")

    def connect(self) -> bool:
        """
        Connect to the open Excel workbook.

        Returns:
            True if connected successfully, False otherwise
        """
        try:
            self._wb = xw.Book(self.filepath)
            if self.verbose:
                debug_print(f"Connected to Excel: {self.filepath}")
            return True
        except Exception as e:
            if self.verbose:
                debug_print(f"Error connecting to Excel: {e}")
            print(f"\nERROR: Could not connect to Excel workbook.")
            print(f"Ensure '{self.filepath}' is open in Excel.")
            return False

    def _get_worksheet(self, name: str):
        """Get worksheet by name."""
        ws_name = EXCEL_WORKSHEETS.get(name, name)
        try:
            return self._wb.sheets[ws_name]
        except Exception as e:
            if self.verbose:
                debug_print(f"Worksheet '{ws_name}' not found: {e}")
            return None

    def _find_ticker_row(self, section: str, ticker: str) -> Optional[int]:
        """
        Find the row number for a ticker in a section.

        Args:
            section: Section name (e.g., 'ticker_structure', 'time_hvn')
            ticker: Stock symbol to find

        Returns:
            Row number or None if not found
        """
        ws = self._get_worksheet('bar_data')
        if ws is None:
            return None

        rows = TICKER_ROWS.get(section, {})
        ticker_col = BAR_DATA_COLUMNS.get(section, {}).get('ticker', 'C')

        for slot, row in rows.items():
            cell_ticker = ws.range(f'{ticker_col}{row}').value
            if cell_ticker and str(cell_ticker).upper() == ticker.upper():
                return row

        return None

    # =========================================================================
    # ZONE DATA (zone_results worksheet)
    # =========================================================================

    def read_zone_results(self, ticker: str = None) -> pd.DataFrame:
        """
        Read filtered zones from zone_results worksheet.

        Args:
            ticker: Optional filter by ticker symbol

        Returns:
            DataFrame with all zone data
        """
        ws = self._get_worksheet('zone_results')
        if ws is None:
            return pd.DataFrame()

        # Find last row with data
        last_row = 2
        while ws.range(f'A{last_row}').value is not None:
            last_row += 1
            if last_row > 500:
                break
        last_row -= 1

        if last_row < 2:
            if self.verbose:
                debug_print("No data in zone_results")
            return pd.DataFrame()

        # Read data range (A2:T{last_row})
        data_range = ws.range(f'A2:T{last_row}').value

        # Handle single row
        if last_row == 2:
            data_range = [data_range]

        # Build DataFrame with column names from config
        columns = list(ZONE_RESULTS_COLUMNS.keys())
        df = pd.DataFrame(data_range, columns=columns)

        # Clean data types
        numeric_cols = ['price', 'hvn_poc', 'zone_high', 'zone_low', 'overlaps',
                        'score', 'epch_bull_price', 'epch_bear_price',
                        'epch_bull_target', 'epch_bear_target']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Filter by ticker if specified
        if ticker:
            df = df[df['ticker'].astype(str).str.upper() == ticker.upper()]

        if self.verbose:
            debug_print(f"Read {len(df)} zones from zone_results")

        return df

    def get_primary_zone(self, ticker: str, direction: str = None) -> Optional[Dict]:
        """
        Get PRIMARY zone from Analysis worksheet (B31:L40).
        These are WITH-TREND setups (EPCH_01, EPCH_02).

        Args:
            ticker: Stock symbol
            direction: Not used (direction is in the data), kept for compatibility

        Returns:
            Dict with zone info or None
        """
        ws = self._get_worksheet('analysis')
        if ws is None:
            return None

        # Search PRIMARY section (B31:L40)
        for row in range(31, 41):
            cell_ticker = ws.range(f'B{row}').value
            if cell_ticker and str(cell_ticker).upper() == ticker.upper():
                zone_direction = ws.range(f'C{row}').value
                hvn_poc = ws.range(f'F{row}').value
                zone_high = ws.range(f'G{row}').value
                zone_low = ws.range(f'H{row}').value

                # Skip if no zone data
                if hvn_poc is None or zone_high is None or zone_low is None:
                    continue

                target_val = ws.range(f'K{row}').value

                if self.verbose:
                    debug_print(f"Found PRIMARY zone for {ticker}: {ws.range(f'E{row}').value}")

                return {
                    'ticker': str(cell_ticker),
                    'direction': str(zone_direction) if zone_direction else '',
                    'ticker_id': ws.range(f'D{row}').value,
                    'zone_id': str(ws.range(f'E{row}').value or ''),
                    'hvn_poc': float(hvn_poc),
                    'zone_high': float(zone_high),
                    'zone_low': float(zone_low),
                    'tier': str(ws.range(f'I{row}').value or ''),
                    'target_id': str(ws.range(f'J{row}').value or ''),
                    'target': float(target_val) if target_val else None,
                    'r_r': ws.range(f'L{row}').value,
                    'zone_type': 'primary',
                    'setup_type': 'with-trend',
                    'rank': str(ws.range(f'E{row}').value or ''),  # zone_id as rank
                    'score': 0.0,  # Not in analysis worksheet
                    'confluences': ''  # Not in analysis worksheet
                }

        if self.verbose:
            debug_print(f"No PRIMARY zone found for {ticker}")
        return None

    def get_secondary_zone(self, ticker: str, direction: str = None) -> Optional[Dict]:
        """
        Get SECONDARY zone from Analysis worksheet (N31:X40).
        These are COUNTER-TREND setups (EPCH_03, EPCH_04).

        Args:
            ticker: Stock symbol
            direction: Not used (direction is in the data), kept for compatibility

        Returns:
            Dict with zone info or None
        """
        ws = self._get_worksheet('analysis')
        if ws is None:
            return None

        # Search SECONDARY section (N31:X40)
        for row in range(31, 41):
            cell_ticker = ws.range(f'N{row}').value
            if cell_ticker and str(cell_ticker).upper() == ticker.upper():
                zone_direction = ws.range(f'O{row}').value
                hvn_poc = ws.range(f'R{row}').value
                zone_high = ws.range(f'S{row}').value
                zone_low = ws.range(f'T{row}').value

                # Skip if no zone data
                if hvn_poc is None or zone_high is None or zone_low is None:
                    continue

                target_val = ws.range(f'W{row}').value

                if self.verbose:
                    debug_print(f"Found SECONDARY zone for {ticker}: {ws.range(f'Q{row}').value}")

                return {
                    'ticker': str(cell_ticker),
                    'direction': str(zone_direction) if zone_direction else '',
                    'ticker_id': ws.range(f'P{row}').value,
                    'zone_id': str(ws.range(f'Q{row}').value or ''),
                    'hvn_poc': float(hvn_poc),
                    'zone_high': float(zone_high),
                    'zone_low': float(zone_low),
                    'tier': str(ws.range(f'U{row}').value or ''),
                    'target_id': str(ws.range(f'V{row}').value or ''),
                    'target': float(target_val) if target_val else None,
                    'r_r': ws.range(f'X{row}').value,
                    'zone_type': 'secondary',
                    'setup_type': 'counter-trend',
                    'rank': str(ws.range(f'Q{row}').value or ''),  # zone_id as rank
                    'score': 0.0,  # Not in analysis worksheet
                    'confluences': ''  # Not in analysis worksheet
                }

        if self.verbose:
            debug_print(f"No SECONDARY zone found for {ticker}")
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
            # Primary zone (with-trend)
            zone = self.get_primary_zone(ticker)
            if zone:
                zone['models'] = 'EPCH_01 (continuation) | EPCH_02 (reversal)'
            return zone

        elif model in ['EPCH_03', 'EPCH_04']:
            # Secondary zone (counter-trend)
            zone = self.get_secondary_zone(ticker)
            if zone:
                zone['models'] = 'EPCH_03 (continuation) | EPCH_04 (reversal)'
            return zone

        else:
            if self.verbose:
                debug_print(f"Unknown model: {model}, defaulting to primary")
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
    # BAR DATA (bar_data worksheet)
    # =========================================================================

    def read_hvn_pocs(self, ticker: str) -> List[float]:
        """
        Read HVN POC levels from bar_data (time_hvn section).

        Args:
            ticker: Stock symbol

        Returns:
            List of up to 10 POC prices
        """
        ws = self._get_worksheet('bar_data')
        if ws is None:
            return []

        row = self._find_ticker_row('time_hvn', ticker)
        if row is None:
            if self.verbose:
                debug_print(f"Ticker {ticker} not found in time_hvn")
            return []

        # Read POCs from columns F-O
        pocs = []
        for col in 'FGHIJKLMNO':
            val = ws.range(f'{col}{row}').value
            if val is not None and val != '':
                try:
                    pocs.append(float(val))
                except (ValueError, TypeError):
                    pass

        if self.verbose:
            debug_print(f"Read {len(pocs)} HVN POCs for {ticker}")

        return pocs

    def read_camarilla_levels(self, ticker: str) -> Dict[str, Optional[float]]:
        """
        Read Camarilla pivot levels from bar_data (add_metrics section).

        Args:
            ticker: Stock symbol

        Returns:
            Dict with d1_s6, d1_s4, d1_s3, d1_r3, d1_r4, d1_r6, etc.
        """
        ws = self._get_worksheet('bar_data')
        if ws is None:
            return {}

        row = self._find_ticker_row('add_metrics', ticker)
        if row is None:
            if self.verbose:
                debug_print(f"Ticker {ticker} not found in add_metrics")
            return {}

        cols = BAR_DATA_COLUMNS['add_metrics']
        result = {}

        for key, col in cols.items():
            if key in ['ticker_id', 'ticker', 'date']:
                continue
            val = ws.range(f'{col}{row}').value
            result[key] = float(val) if val is not None else None

        return result

    def read_atr(self, ticker: str, timeframe: str = 'd1') -> Optional[float]:
        """
        Read ATR from bar_data (on_options_metrics section).

        Args:
            ticker: Stock symbol
            timeframe: ATR timeframe ('m5', 'm15', 'h1', 'd1')

        Returns:
            ATR value or None
        """
        ws = self._get_worksheet('bar_data')
        if ws is None:
            return None

        row = self._find_ticker_row('on_options_metrics', ticker)
        if row is None:
            if self.verbose:
                debug_print(f"Ticker {ticker} not found in on_options_metrics")
            return None

        atr_col = BAR_DATA_COLUMNS['on_options_metrics'].get(f'{timeframe}_atr', 'T')
        val = ws.range(f'{atr_col}{row}').value

        return float(val) if val is not None else None

    def read_overnight_levels(self, ticker: str) -> Dict[str, Optional[float]]:
        """
        Read overnight high/low from bar_data.

        Args:
            ticker: Stock symbol

        Returns:
            Dict with 'd1_onh' and 'd1_onl'
        """
        ws = self._get_worksheet('bar_data')
        if ws is None:
            return {}

        row = self._find_ticker_row('on_options_metrics', ticker)
        if row is None:
            return {}

        return {
            'd1_onh': ws.range(f'E{row}').value,
            'd1_onl': ws.range(f'F{row}').value
        }

    # =========================================================================
    # ANALYSIS DATA (analysis worksheet)
    # =========================================================================

    def read_analysis_setups(self, ticker: str) -> Dict[str, Optional[Dict]]:
        """
        Read primary and secondary setups from analysis worksheet.

        Args:
            ticker: Stock symbol

        Returns:
            Dict with 'primary' and 'secondary' setup info
        """
        ws = self._get_worksheet('analysis')
        if ws is None:
            return {'primary': None, 'secondary': None}

        result = {'primary': None, 'secondary': None}

        # Search primary section
        primary_cfg = ANALYSIS_REFS['primary']
        for row in range(primary_cfg['start_row'], primary_cfg['end_row'] + 1):
            cell_ticker = ws.range(f"{primary_cfg['columns']['ticker']}{row}").value
            if cell_ticker and str(cell_ticker).upper() == ticker.upper():
                result['primary'] = {}
                for key, col in primary_cfg['columns'].items():
                    result['primary'][key] = ws.range(f'{col}{row}').value
                break

        # Search secondary section
        secondary_cfg = ANALYSIS_REFS['secondary']
        for row in range(secondary_cfg['start_row'], secondary_cfg['end_row'] + 1):
            cell_ticker = ws.range(f"{secondary_cfg['columns']['ticker']}{row}").value
            if cell_ticker and str(cell_ticker).upper() == ticker.upper():
                result['secondary'] = {}
                for key, col in secondary_cfg['columns'].items():
                    result['secondary'][key] = ws.range(f'{col}{row}').value
                break

        return result

    # =========================================================================
    # MARKET OVERVIEW (market_overview worksheet)
    # =========================================================================

    def read_market_structure(self, ticker: str) -> Dict[str, Any]:
        """
        Read market structure from market_overview worksheet.

        Args:
            ticker: Stock symbol

        Returns:
            Dict with direction and levels for each timeframe
        """
        ws = self._get_worksheet('market_overview')
        if ws is None:
            return {}

        # Find ticker row
        rows = MARKET_OVERVIEW_ROWS['ticker_structure']
        row = None

        for slot, r in rows.items():
            cell_ticker = ws.range(f"C{r}").value
            if cell_ticker and str(cell_ticker).upper() == ticker.upper():
                row = r
                break

        if row is None:
            if self.verbose:
                debug_print(f"Ticker {ticker} not found in market_overview")
            return {}

        cols = MARKET_OVERVIEW_COLUMNS
        return {
            'price': ws.range(f"{cols['price']}{row}").value,
            'd1': {
                'direction': ws.range(f"{cols['d1_dir']}{row}").value,
                'strong': ws.range(f"{cols['d1_s']}{row}").value,
                'weak': ws.range(f"{cols['d1_w']}{row}").value,
            },
            'h4': {
                'direction': ws.range(f"{cols['h4_dir']}{row}").value,
                'strong': ws.range(f"{cols['h4_s']}{row}").value,
                'weak': ws.range(f"{cols['h4_w']}{row}").value,
            },
            'h1': {
                'direction': ws.range(f"{cols['h1_dir']}{row}").value,
                'strong': ws.range(f"{cols['h1_s']}{row}").value,
                'weak': ws.range(f"{cols['h1_w']}{row}").value,
            },
            'm15': {
                'direction': ws.range(f"{cols['m15_dir']}{row}").value,
                'strong': ws.range(f"{cols['m15_s']}{row}").value,
                'weak': ws.range(f"{cols['m15_w']}{row}").value,
            },
            'composite': ws.range(f"{cols['composite']}{row}").value,
        }


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("EPOCH READER - STANDALONE TEST")
    print("=" * 60)
    print(f"\nEnsure {EXCEL_FILEPATH} is open in Excel.\n")

    reader = EpochReader(verbose=True)

    # Test connection
    print("[TEST 1] Connecting to Excel...")
    if not reader.connect():
        print("  FAILED: Could not connect to Excel")
        print("  Make sure epoch_v1.xlsm is open!")
        sys.exit(1)
    print("  SUCCESS: Connected to Excel\n")

    # Test zone reading
    print("[TEST 2] Reading zone_results...")
    df = reader.read_zone_results()
    print(f"  Found {len(df)} total zones")
    if not df.empty:
        tickers = df['ticker'].unique()
        print(f"  Tickers: {list(tickers)[:5]}...")

    # Test primary zone for first ticker
    if not df.empty:
        test_ticker = str(df.iloc[0]['ticker'])
        print(f"\n[TEST 3] Getting primary zone for {test_ticker} long...")
        zone = reader.get_primary_zone(test_ticker, 'long')
        if zone:
            print(f"  Zone ID: {zone['zone_id']}")
            print(f"  Range: ${zone['zone_low']:.2f} - ${zone['zone_high']:.2f}")
            print(f"  HVN POC: ${zone['hvn_poc']:.2f}")
            print(f"  Target: ${zone['target']:.2f}" if zone['target'] else "  Target: N/A")
        else:
            print("  No primary zone found")

        # Test HVN POCs
        print(f"\n[TEST 4] Reading HVN POCs for {test_ticker}...")
        pocs = reader.read_hvn_pocs(test_ticker)
        if pocs:
            print(f"  POCs: {['${:.2f}'.format(p) for p in pocs[:5]]}")
        else:
            print("  No POCs found")

        # Test Camarilla
        print(f"\n[TEST 5] Reading Camarilla levels for {test_ticker}...")
        cam = reader.read_camarilla_levels(test_ticker)
        if cam:
            print(f"  D1 S3: ${cam.get('d1_s3', 'N/A')}")
            print(f"  D1 R3: ${cam.get('d1_r3', 'N/A')}")
        else:
            print("  No Camarilla levels found")

        # Test ATR
        print(f"\n[TEST 6] Reading D1 ATR for {test_ticker}...")
        atr = reader.read_atr(test_ticker, 'd1')
        if atr:
            print(f"  D1 ATR: ${atr:.2f}")
        else:
            print("  No ATR found")

        # Test analysis setups
        print(f"\n[TEST 7] Reading analysis setups for {test_ticker}...")
        setups = reader.read_analysis_setups(test_ticker)
        if setups['primary']:
            print(f"  Primary: {setups['primary'].get('direction')} -> ${setups['primary'].get('target', 'N/A')}")
        else:
            print("  No primary setup found")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

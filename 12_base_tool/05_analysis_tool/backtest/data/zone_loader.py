"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 09: BACKTESTER v2.0
Zone Loader - Load Zone Data from Excel
XIII Trading LLC
================================================================================

Loads Primary and Secondary zone data from Analysis worksheet.
Extracts trading date from ticker_id format (e.g., "AMZN_120525" = 12/05/25)
================================================================================
"""
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    WORKSHEETS, VERBOSE,
    ANALYSIS_PRIMARY_START_ROW, ANALYSIS_PRIMARY_END_ROW, ANALYSIS_PRIMARY_COLUMNS,
    ANALYSIS_SECONDARY_START_ROW, ANALYSIS_SECONDARY_END_ROW, ANALYSIS_SECONDARY_COLUMNS
)


@dataclass
class ZoneData:
    """Zone data structure"""
    ticker: str
    ticker_id: str  # String format like "AMZN_120525"
    zone_id: Optional[str]  # Can be string like "Z1" or int
    direction: str  # 'Bull', 'Bear', etc.
    hvn_poc: float
    zone_high: float
    zone_low: float
    tier: Optional[str]  # T1, T2, T3
    target_id: Optional[str]
    target: Optional[float]
    rr: Optional[float]
    zone_type: str  # 'PRIMARY' or 'SECONDARY'


class ZoneLoader:
    """
    Loads zone data from Excel workbook.
    
    Reads Primary zones from rows 31-40, columns B-L
    Reads Secondary zones from rows 31-40, columns N-X
    """
    
    def __init__(self, workbook):
        """
        Initialize with xlwings workbook reference.
        
        Args:
            workbook: xlwings Book object
        """
        self.wb = workbook
        self.ws = workbook.sheets[WORKSHEETS['analysis']]
    
    def get_trading_date(self) -> Optional[str]:
        """
        Extract trading date from the first valid ticker_id.
        
        ticker_id format: "TICKER_MMDDYY" (e.g., "AMZN_120525" = 12/05/25)
        
        Returns:
            Date string in YYYY-MM-DD format, or None if not found
        """
        cols = ANALYSIS_PRIMARY_COLUMNS
        
        for row in range(ANALYSIS_PRIMARY_START_ROW, ANALYSIS_PRIMARY_END_ROW + 1):
            ticker_id = self.ws.range(f"{cols['ticker_id']}{row}").value
            
            if ticker_id and isinstance(ticker_id, str) and '_' in ticker_id:
                try:
                    # Extract date portion after underscore
                    date_part = ticker_id.split('_')[1]
                    
                    if len(date_part) == 6:
                        # Parse MMDDYY format
                        month = int(date_part[0:2])
                        day = int(date_part[2:4])
                        year = int(date_part[4:6])
                        
                        # Convert 2-digit year to 4-digit (assume 2000s)
                        full_year = 2000 + year
                        
                        # Format as YYYY-MM-DD
                        date_str = f"{full_year}-{month:02d}-{day:02d}"
                        
                        if VERBOSE:
                            print(f"  Extracted trading date: {date_str} from {ticker_id}")
                        
                        return date_str
                        
                except (ValueError, IndexError) as e:
                    if VERBOSE:
                        print(f"  Warning: Could not parse date from ticker_id '{ticker_id}': {e}")
                    continue
        
        return None
    
    def load_primary_zones(self) -> List[ZoneData]:
        """Load all Primary zones from Analysis worksheet"""
        zones = []
        cols = ANALYSIS_PRIMARY_COLUMNS
        
        for row in range(ANALYSIS_PRIMARY_START_ROW, ANALYSIS_PRIMARY_END_ROW + 1):
            ticker = self.ws.range(f"{cols['ticker']}{row}").value
            
            if not ticker:
                continue
            
            try:
                # Read required fields
                zone_high = self._safe_float(self.ws.range(f"{cols['zone_high']}{row}").value)
                zone_low = self._safe_float(self.ws.range(f"{cols['zone_low']}{row}").value)
                hvn_poc = self._safe_float(self.ws.range(f"{cols['hvn_poc']}{row}").value)
                
                # Skip if missing critical zone data
                if zone_high is None or zone_low is None:
                    if VERBOSE:
                        print(f"  Skipping PRIMARY row {row}: missing zone_high or zone_low")
                    continue
                
                # Read optional fields
                target = self._safe_float(self.ws.range(f"{cols['target']}{row}").value)
                
                zone = ZoneData(
                    ticker=str(ticker),
                    ticker_id=str(self.ws.range(f"{cols['ticker_id']}{row}").value or ''),
                    zone_id=str(self.ws.range(f"{cols['zone_id']}{row}").value or ''),
                    direction=str(self.ws.range(f"{cols['direction']}{row}").value or ''),
                    hvn_poc=hvn_poc or (zone_high + zone_low) / 2,
                    zone_high=zone_high,
                    zone_low=zone_low,
                    tier=str(self.ws.range(f"{cols['tier']}{row}").value or ''),
                    target_id=str(self.ws.range(f"{cols['target_id']}{row}").value or ''),
                    target=target,
                    rr=self._safe_float(self.ws.range(f"{cols['rr']}{row}").value),
                    zone_type='PRIMARY'
                )
                zones.append(zone)
                
                if VERBOSE:
                    target_str = f"${target:.2f}" if target else "None"
                    print(f"  Loaded PRIMARY: {zone.ticker} "
                          f"Zone: ${zone.zone_low:.2f}-${zone.zone_high:.2f} "
                          f"Target: {target_str}")
                    
            except (TypeError, ValueError) as e:
                if VERBOSE:
                    print(f"  Warning: Could not load Primary zone at row {row}: {e}")
                continue
        
        return zones
    
    def load_secondary_zones(self) -> List[ZoneData]:
        """Load all Secondary zones from Analysis worksheet"""
        zones = []
        cols = ANALYSIS_SECONDARY_COLUMNS
        
        for row in range(ANALYSIS_SECONDARY_START_ROW, ANALYSIS_SECONDARY_END_ROW + 1):
            ticker = self.ws.range(f"{cols['ticker']}{row}").value
            
            if not ticker:
                continue
            
            try:
                # Read required fields
                zone_high = self._safe_float(self.ws.range(f"{cols['zone_high']}{row}").value)
                zone_low = self._safe_float(self.ws.range(f"{cols['zone_low']}{row}").value)
                hvn_poc = self._safe_float(self.ws.range(f"{cols['hvn_poc']}{row}").value)
                
                # Skip if missing critical zone data
                if zone_high is None or zone_low is None:
                    if VERBOSE:
                        print(f"  Skipping SECONDARY row {row}: missing zone_high or zone_low")
                    continue
                
                # Validate zone (high should be > low)
                if zone_high < zone_low:
                    if VERBOSE:
                        print(f"  Warning SECONDARY row {row}: zone_high ({zone_high}) < zone_low ({zone_low}), swapping")
                    zone_high, zone_low = zone_low, zone_high
                
                # Read optional fields
                target = self._safe_float(self.ws.range(f"{cols['target']}{row}").value)
                
                zone = ZoneData(
                    ticker=str(ticker),
                    ticker_id=str(self.ws.range(f"{cols['ticker_id']}{row}").value or ''),
                    zone_id=str(self.ws.range(f"{cols['zone_id']}{row}").value or ''),
                    direction=str(self.ws.range(f"{cols['direction']}{row}").value or ''),
                    hvn_poc=hvn_poc or (zone_high + zone_low) / 2,
                    zone_high=zone_high,
                    zone_low=zone_low,
                    tier=str(self.ws.range(f"{cols['tier']}{row}").value or ''),
                    target_id=str(self.ws.range(f"{cols['target_id']}{row}").value or ''),
                    target=target,
                    rr=self._safe_float(self.ws.range(f"{cols['rr']}{row}").value),
                    zone_type='SECONDARY'
                )
                zones.append(zone)
                
                if VERBOSE:
                    target_str = f"${target:.2f}" if target else "None"
                    print(f"  Loaded SECONDARY: {zone.ticker} "
                          f"Zone: ${zone.zone_low:.2f}-${zone.zone_high:.2f} "
                          f"Target: {target_str}")
                    
            except (TypeError, ValueError) as e:
                if VERBOSE:
                    print(f"  Warning: Could not load Secondary zone at row {row}: {e}")
                continue
        
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
        
        primary = next((z for z in primary_zones if z.ticker == ticker), None)
        secondary = next((z for z in secondary_zones if z.ticker == ticker), None)
        
        return primary, secondary
    
    def get_zone_dict(self, zone: ZoneData) -> Dict:
        """Convert ZoneData to dict format for TradeSimulator"""
        return {
            'zone_high': zone.zone_high,
            'zone_low': zone.zone_low,
            'hvn_poc': zone.hvn_poc,
            'target': zone.target
        }
    
    def debug_columns(self, row: int = 31):
        """Debug helper to print what's in each column for a given row"""
        print(f"\n=== DEBUG: Column contents at row {row} ===")
        print("\nPRIMARY columns (B-L):")
        for name, col in ANALYSIS_PRIMARY_COLUMNS.items():
            val = self.ws.range(f"{col}{row}").value
            print(f"  {name} ({col}): {val}")
        
        print("\nSECONDARY columns (N-X):")
        for name, col in ANALYSIS_SECONDARY_COLUMNS.items():
            val = self.ws.range(f"{col}{row}").value
            print(f"  {name} ({col}): {val}")
        print("=" * 50)
    
    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """Safely convert to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    
    @staticmethod
    def _safe_int(value) -> Optional[int]:
        """Safely convert to int"""
        if value is None or value == '':
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None


if __name__ == "__main__":
    print("Zone Loader module - run backtest_runner.py to execute")
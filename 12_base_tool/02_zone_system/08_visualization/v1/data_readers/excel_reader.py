# excel_reader.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\08_visualization\data_readers\
# Purpose: Read data from Epoch Excel workbook for visualization

"""
Excel Reader for Module 08 Visualization

Reads from:
- market_overview: Index and ticker market structure
- bar_data: Current price and ATR values
- zone_results: Filtered L2-L5 zones
- Analysis: Setup strings and primary/secondary setups
"""

import xlwings as xw
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging
import sys
from pathlib import Path

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.visualization_config import (
    WORKBOOK_PATH, WORKSHEETS, INDEX_ROWS, TICKER_ROWS, COLORS
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class MarketStructure:
    """Market structure for index ETFs"""
    ticker: str
    d1_dir: str
    h4_dir: str
    h1_dir: str
    m15_dir: str
    composite: str


@dataclass
class TickerStructure:
    """Ticker structure with strong/weak levels"""
    ticker_id: str
    ticker: str
    date: str
    price: float
    d1_dir: str
    d1_strong: float
    d1_weak: float
    h4_dir: str
    h4_strong: float
    h4_weak: float
    h1_dir: str
    h1_strong: float
    h1_weak: float
    m15_dir: str
    m15_strong: float
    m15_weak: float
    composite: str
    d1_atr: float = 0.0
    m5_atr: float = 0.0


@dataclass
class ZoneResult:
    """Single zone from zone_results worksheet"""
    ticker_id: str
    ticker: str
    date: str
    price: float
    direction: str
    zone_id: str
    hvn_poc: float
    zone_high: float
    zone_low: float
    overlaps: int
    score: float
    rank: str
    confluences: str


@dataclass
class SetupData:
    """Setup analysis data for a ticker"""
    ticker: str
    setup_string: str
    primary_high: float = 0.0
    primary_low: float = 0.0
    primary_target: float = 0.0
    secondary_high: float = 0.0
    secondary_low: float = 0.0
    secondary_target: float = 0.0
    primary_direction: str = ""
    primary_zone_id: str = ""
    primary_rr: str = ""
    secondary_direction: str = ""
    secondary_zone_id: str = ""
    secondary_rr: str = ""
    
    def parse_string(self):
        """Parse the setup string into component values"""
        if not self.setup_string or self.setup_string == "0,0,0,0,0,0":
            return
        try:
            values = [float(x.strip()) for x in self.setup_string.split(',')]
            if len(values) >= 6:
                self.primary_high = values[0]
                self.primary_low = values[1]
                self.primary_target = values[2]
                self.secondary_high = values[3]
                self.secondary_low = values[4]
                self.secondary_target = values[5]
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse setup string '{self.setup_string}': {e}")


@dataclass
class VisualizationData:
    """Complete data package for one ticker's visualization"""
    ticker: str
    ticker_id: str
    market_structure: List[MarketStructure]
    ticker_structure: TickerStructure
    zones: List[ZoneResult]
    setup: SetupData
    

# =============================================================================
# EXCEL READER CLASS
# =============================================================================

class EpochExcelReader:
    """Read visualization data from Epoch workbook"""
    
    def __init__(self, workbook_path: str = None):
        """
        Initialize reader with workbook path.
        
        Args:
            workbook_path: Path to epoch_v1.xlsm. If None, uses config default.
        """
        self.workbook_path = Path(workbook_path) if workbook_path else WORKBOOK_PATH
        self.wb = None
        self._cache = {}
    
    def connect(self) -> bool:
        """Connect to the open Excel workbook"""
        try:
            self.wb = xw.Book(str(self.workbook_path))
            logger.info(f"Connected to workbook: {self.workbook_path.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to workbook: {e}")
            logger.error("Ensure the workbook is open in Excel")
            return False
    
    def read_all_tickers(self) -> Dict[str, VisualizationData]:
        """
        Read data for all tickers in the workbook.
        
        Returns:
            Dict mapping ticker symbol to VisualizationData
        """
        if not self.wb:
            if not self.connect():
                return {}
        
        result = {}
        
        # Get market structure (same for all tickers)
        market_structure = self._read_market_structure()
        
        # Get all zone results
        all_zones = self._read_zone_results()
        
        # Get setup strings
        setup_strings = self._read_setup_strings()
        
        # Get primary/secondary setup details
        primary_setups, secondary_setups = self._read_setup_details()
        
        # Read each ticker slot
        for slot in range(1, 11):
            ticker_data = self._read_ticker_structure(slot)
            
            if ticker_data and ticker_data.ticker:
                ticker = ticker_data.ticker.upper()
                
                # Filter zones for this ticker
                ticker_zones = [z for z in all_zones if z.ticker.upper() == ticker]
                
                # Get setup data
                setup = setup_strings.get(ticker, SetupData(ticker=ticker, setup_string=""))
                
                # Add primary/secondary details
                if ticker in primary_setups:
                    p = primary_setups[ticker]
                    setup.primary_direction = p.get('direction', '')
                    setup.primary_zone_id = p.get('zone_id', '')
                    setup.primary_rr = p.get('rr', '')
                
                if ticker in secondary_setups:
                    s = secondary_setups[ticker]
                    setup.secondary_direction = s.get('direction', '')
                    setup.secondary_zone_id = s.get('zone_id', '')
                    setup.secondary_rr = s.get('rr', '')
                
                result[ticker] = VisualizationData(
                    ticker=ticker,
                    ticker_id=ticker_data.ticker_id,
                    market_structure=market_structure,
                    ticker_structure=ticker_data,
                    zones=ticker_zones,
                    setup=setup
                )
                
                logger.info(f"Loaded data for {ticker}: {len(ticker_zones)} zones")
        
        return result
    
    def _read_market_structure(self) -> List[MarketStructure]:
        """Read index ETF market structure from market_overview"""
        ws = self.wb.sheets[WORKSHEETS['market_overview']]
        result = []
        
        for ticker, row in INDEX_ROWS.items():
            try:
                ms = MarketStructure(
                    ticker=ticker,
                    d1_dir=self._safe_read(ws, f'F{row}', ''),
                    h4_dir=self._safe_read(ws, f'I{row}', ''),
                    h1_dir=self._safe_read(ws, f'L{row}', ''),
                    m15_dir=self._safe_read(ws, f'O{row}', ''),
                    composite=self._safe_read(ws, f'R{row}', '')
                )
                result.append(ms)
            except Exception as e:
                logger.warning(f"Failed to read market structure for {ticker}: {e}")
        
        return result
    
    def _read_ticker_structure(self, slot: int) -> Optional[TickerStructure]:
        """Read ticker structure for a specific slot (1-10)"""
        ws_overview = self.wb.sheets[WORKSHEETS['market_overview']]
        ws_bar = self.wb.sheets[WORKSHEETS['bar_data']]
        
        row_overview = TICKER_ROWS['market_overview'][f't{slot}']
        row_ticker = TICKER_ROWS['bar_data_ticker'][f't{slot}']
        row_atr = TICKER_ROWS['bar_data_atr'][f't{slot}']
        
        try:
            ticker = self._safe_read(ws_overview, f'C{row_overview}', '')
            if not ticker:
                return None
            
            return TickerStructure(
                ticker_id=self._safe_read(ws_overview, f'B{row_overview}', ''),
                ticker=ticker,
                date=str(self._safe_read(ws_overview, f'D{row_overview}', '')),
                price=self._safe_read(ws_bar, f'E{row_ticker}', 0.0),
                d1_dir=self._safe_read(ws_overview, f'F{row_overview}', ''),
                d1_strong=self._safe_read(ws_overview, f'G{row_overview}', 0.0),
                d1_weak=self._safe_read(ws_overview, f'H{row_overview}', 0.0),
                h4_dir=self._safe_read(ws_overview, f'I{row_overview}', ''),
                h4_strong=self._safe_read(ws_overview, f'J{row_overview}', 0.0),
                h4_weak=self._safe_read(ws_overview, f'K{row_overview}', 0.0),
                h1_dir=self._safe_read(ws_overview, f'L{row_overview}', ''),
                h1_strong=self._safe_read(ws_overview, f'M{row_overview}', 0.0),
                h1_weak=self._safe_read(ws_overview, f'N{row_overview}', 0.0),
                m15_dir=self._safe_read(ws_overview, f'O{row_overview}', ''),
                m15_strong=self._safe_read(ws_overview, f'P{row_overview}', 0.0),
                m15_weak=self._safe_read(ws_overview, f'Q{row_overview}', 0.0),
                composite=self._safe_read(ws_overview, f'R{row_overview}', ''),
                d1_atr=self._safe_read(ws_bar, f'T{row_atr}', 0.0),
                m5_atr=self._safe_read(ws_bar, f'Q{row_atr}', 0.0)
            )
        except Exception as e:
            logger.warning(f"Failed to read ticker structure for slot {slot}: {e}")
            return None
    
    def _read_zone_results(self) -> List[ZoneResult]:
        """Read all zones from zone_results worksheet"""
        ws = self.wb.sheets[WORKSHEETS['zone_results']]
        zones = []
        
        # Read data starting from row 2
        row = 2
        max_empty = 3  # Stop after 3 empty rows
        empty_count = 0
        
        while empty_count < max_empty:
            ticker_id = self._safe_read(ws, f'A{row}', '')
            
            if not ticker_id:
                empty_count += 1
                row += 1
                continue
            
            empty_count = 0
            
            try:
                zone = ZoneResult(
                    ticker_id=ticker_id,
                    ticker=self._safe_read(ws, f'B{row}', ''),
                    date=str(self._safe_read(ws, f'C{row}', '')),
                    price=self._safe_read(ws, f'D{row}', 0.0),
                    direction=self._safe_read(ws, f'E{row}', ''),
                    zone_id=self._safe_read(ws, f'F{row}', ''),
                    hvn_poc=self._safe_read(ws, f'G{row}', 0.0),
                    zone_high=self._safe_read(ws, f'H{row}', 0.0),
                    zone_low=self._safe_read(ws, f'I{row}', 0.0),
                    overlaps=int(self._safe_read(ws, f'J{row}', 0)),
                    score=self._safe_read(ws, f'K{row}', 0.0),
                    rank=self._safe_read(ws, f'L{row}', ''),
                    confluences=self._safe_read(ws, f'M{row}', '')
                )
                zones.append(zone)
            except Exception as e:
                logger.warning(f"Failed to read zone at row {row}: {e}")
            
            row += 1
        
        logger.info(f"Read {len(zones)} zones from zone_results")
        return zones
    
    def _read_setup_strings(self) -> Dict[str, SetupData]:
        """Read setup strings from Analysis worksheet"""
        ws = self.wb.sheets[WORKSHEETS['analysis']]
        result = {}
        
        for slot in range(1, 11):
            row = TICKER_ROWS['analysis_strings'][f't{slot}']
            
            ticker = self._safe_read(ws, f'B{row}', '')
            if not ticker:
                continue
            
            ticker = ticker.upper()
            setup_string = self._safe_read(ws, f'C{row}', '')
            
            setup = SetupData(ticker=ticker, setup_string=str(setup_string) if setup_string else "")
            setup.parse_string()
            result[ticker] = setup
        
        return result
    
    def _read_setup_details(self) -> Tuple[Dict, Dict]:
        """Read primary and secondary setup details from Analysis worksheet"""
        ws = self.wb.sheets[WORKSHEETS['analysis']]
        primary = {}
        secondary = {}
        
        # Primary section: B31:K40
        for row in range(31, 41):
            ticker = self._safe_read(ws, f'B{row}', '')
            if not ticker:
                continue
            ticker = ticker.upper()
            
            primary[ticker] = {
                'direction': self._safe_read(ws, f'C{row}', ''),
                'zone_id': self._safe_read(ws, f'E{row}', ''),
                'hvn_poc': self._safe_read(ws, f'F{row}', 0.0),
                'zone_high': self._safe_read(ws, f'G{row}', 0.0),
                'zone_low': self._safe_read(ws, f'H{row}', 0.0),
                'target': self._safe_read(ws, f'J{row}', 0.0),
                'rr': str(self._safe_read(ws, f'K{row}', ''))
            }
        
        # Secondary section: M31:V40
        for row in range(31, 41):
            ticker = self._safe_read(ws, f'M{row}', '')
            if not ticker:
                continue
            ticker = ticker.upper()
            
            secondary[ticker] = {
                'direction': self._safe_read(ws, f'N{row}', ''),
                'zone_id': self._safe_read(ws, f'P{row}', ''),
                'hvn_poc': self._safe_read(ws, f'Q{row}', 0.0),
                'zone_high': self._safe_read(ws, f'R{row}', 0.0),
                'zone_low': self._safe_read(ws, f'S{row}', 0.0),
                'target': self._safe_read(ws, f'U{row}', 0.0),
                'rr': str(self._safe_read(ws, f'V{row}', ''))
            }
        
        return primary, secondary
    
    def _safe_read(self, ws, cell: str, default):
        """Safely read a cell value with default fallback"""
        try:
            value = ws.range(cell).value
            if value is None:
                return default
            return value
        except Exception:
            return default


# =============================================================================
# STANDALONE TEST
# =============================================================================

def main():
    """Test the Excel reader"""
    reader = EpochExcelReader()
    
    if not reader.connect():
        print("Failed to connect to workbook. Ensure it's open.")
        return
    
    data = reader.read_all_tickers()
    
    print(f"\n{'='*60}")
    print(f"Loaded {len(data)} tickers")
    print(f"{'='*60}")
    
    for ticker, viz_data in data.items():
        print(f"\n{ticker}:")
        print(f"  Composite: {viz_data.ticker_structure.composite}")
        print(f"  Price: ${viz_data.ticker_structure.price:.2f}")
        print(f"  ATR: ${viz_data.ticker_structure.d1_atr:.2f}")
        print(f"  Zones: {len(viz_data.zones)}")
        print(f"  Setup String: {viz_data.setup.setup_string}")


if __name__ == "__main__":
    main()

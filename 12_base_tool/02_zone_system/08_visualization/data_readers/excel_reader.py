# excel_reader.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\08_visualization\data_readers\
# Purpose: Read data from Epoch Excel workbook for visualization

"""
Excel Reader for Module 08 Visualization - V1.1

V1.1 CHANGES:
- zone_results now includes tier column at N
- Analysis Primary section: B31:L40 (tier at column I)
- Analysis Secondary section: N31:X40 (tier at column U)

Reads from:
- market_overview: Index and ticker market structure
- bar_data: Current price and ATR values
- zone_results: Filtered L1-L5 zones (V1.1: all zones with tier classification)
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
    WORKBOOK_PATH, WORKSHEETS, INDEX_ROWS, TICKER_ROWS, COLORS,
    TIME_HVN_COLUMNS
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# V1.1 COLUMN MAPPINGS
# =============================================================================

# Zone Results columns (V1.1: A-N, tier added at N)
ZONE_RESULTS_COLUMNS = {
    'ticker_id': 'A',
    'ticker': 'B',
    'date': 'C',
    'price': 'D',
    'direction': 'E',
    'zone_id': 'F',
    'hvn_poc': 'G',
    'zone_high': 'H',
    'zone_low': 'I',
    'overlaps': 'J',
    'score': 'K',
    'rank': 'L',
    'confluences': 'M',
    'tier': 'N'  # V1.1: New tier column
}

# Analysis Primary section (V1.1: B31:L40, tier at I)
ANALYSIS_PRIMARY_COLUMNS = {
    'ticker': 'B',
    'direction': 'C',
    'ticker_id': 'D',
    'zone_id': 'E',
    'hvn_poc': 'F',
    'zone_high': 'G',
    'zone_low': 'H',
    'tier': 'I',        # V1.1: New tier column
    'target_id': 'J',   # V1.1: Shifted from I
    'target': 'K',      # V1.1: Shifted from J
    'r_r': 'L'          # V1.1: Shifted from K
}

# Analysis Secondary section (V1.1: N31:X40, tier at U)
ANALYSIS_SECONDARY_COLUMNS = {
    'ticker': 'N',      # V1.1: Shifted from M
    'direction': 'O',   # V1.1: Shifted from N
    'ticker_id': 'P',   # V1.1: Shifted from O
    'zone_id': 'Q',     # V1.1: Shifted from P
    'hvn_poc': 'R',     # V1.1: Shifted from Q
    'zone_high': 'S',   # V1.1: Shifted from R
    'zone_low': 'T',    # V1.1: Shifted from S
    'tier': 'U',        # V1.1: New tier column
    'target_id': 'V',   # V1.1: Shifted from T
    'target': 'W',      # V1.1: Shifted from U
    'r_r': 'X'          # V1.1: Shifted from V
}

ANALYSIS_SETUP_START_ROW = 31
ANALYSIS_SETUP_END_ROW = 40


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
    """Single zone from zone_results worksheet - V1.1 with tier"""
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
    tier: str = ""  # V1.1: New tier field (T1/T2/T3)


@dataclass
class SetupData:
    """Setup analysis data for a ticker - V1.1 with tier"""
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
    primary_tier: str = ""      # V1.1: New tier field
    primary_confluences: str = ""  # V1.2: Confluences from zone_results
    secondary_direction: str = ""
    secondary_zone_id: str = ""
    secondary_rr: str = ""
    secondary_tier: str = ""    # V1.1: New tier field
    secondary_confluences: str = ""  # V1.2: Confluences from zone_results
    
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
class EpochData:
    """Epoch HVN data from Module 04 (time_hvn section)"""
    ticker: str
    start_date: str
    hvn_pocs: List[float] = field(default_factory=list)  # 10 POCs from Module 04
    
    @property
    def has_data(self) -> bool:
        """Check if epoch data is populated"""
        return bool(self.start_date and any(p > 0 for p in self.hvn_pocs))


@dataclass
class VisualizationData:
    """Complete data package for one ticker's visualization"""
    ticker: str
    ticker_id: str
    market_structure: List[MarketStructure]
    ticker_structure: TickerStructure
    zones: List[ZoneResult]
    setup: SetupData
    epoch: EpochData = None
    
    @property
    def full_pinescript_string(self) -> str:
        """
        Generate the full 16-value PineScript string:
        PrimaryHigh,PrimaryLow,PrimaryTarget,SecondaryHigh,SecondaryLow,SecondaryTarget,POC1,...,POC10
        """
        # Start with the 6 setup values
        values = [
            self.setup.primary_high,
            self.setup.primary_low,
            self.setup.primary_target,
            self.setup.secondary_high,
            self.setup.secondary_low,
            self.setup.secondary_target
        ]
        
        # Add 10 POC values (or 0 if not available)
        if self.epoch and self.epoch.hvn_pocs:
            for i in range(10):
                if i < len(self.epoch.hvn_pocs):
                    values.append(self.epoch.hvn_pocs[i])
                else:
                    values.append(0.0)
        else:
            # No epoch data - add 10 zeros
            values.extend([0.0] * 10)
        
        # Format as comma-separated string
        return ",".join(f"{v:.2f}" if v != 0 else "0" for v in values)
    

# =============================================================================
# EXCEL READER CLASS - V1.1
# =============================================================================

class EpochExcelReader:
    """Read visualization data from Epoch workbook - V1.1 compatible"""
    
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
        
        # Get all zone results (V1.1: includes tier)
        all_zones = self._read_zone_results()
        
        # Get setup strings
        setup_strings = self._read_setup_strings()
        
        # Get primary/secondary setup details (V1.1: updated column mappings)
        primary_setups, secondary_setups = self._read_setup_details_v11()
        
        # Get epoch data (start dates and HVN POCs from Module 04)
        epoch_data_dict = self._read_epoch_data()
        
        # Read each ticker slot
        for slot in range(1, 11):
            ticker_data = self._read_ticker_structure(slot)
            
            if ticker_data and ticker_data.ticker:
                ticker = ticker_data.ticker.upper()
                
                # Filter zones for this ticker
                ticker_zones = [z for z in all_zones if z.ticker.upper() == ticker]
                
                # Get setup data
                setup = setup_strings.get(ticker, SetupData(ticker=ticker, setup_string=""))
                
                # Add primary/secondary details (V1.1: includes tier, V1.2: includes confluences)
                if ticker in primary_setups:
                    p = primary_setups[ticker]
                    setup.primary_direction = str(p.get('direction', '') or '')
                    setup.primary_zone_id = str(p.get('zone_id', '') or '')
                    setup.primary_rr = str(p.get('r_r', '') or '')
                    setup.primary_tier = str(p.get('tier', '') or '')  # V1.1
                    # Also get zone values directly from Analysis sheet
                    if p.get('zone_high', 0) > 0:
                        setup.primary_high = float(p.get('zone_high', 0) or 0)
                        setup.primary_low = float(p.get('zone_low', 0) or 0)
                        setup.primary_target = float(p.get('target', 0) or 0)
                    # V1.2: Look up confluences from zone_results
                    primary_zone_id = setup.primary_zone_id
                    for z in ticker_zones:
                        if z.zone_id == primary_zone_id:
                            setup.primary_confluences = z.confluences or ''
                            break

                if ticker in secondary_setups:
                    s = secondary_setups[ticker]
                    setup.secondary_direction = str(s.get('direction', '') or '')
                    setup.secondary_zone_id = str(s.get('zone_id', '') or '')
                    setup.secondary_rr = str(s.get('r_r', '') or '')
                    setup.secondary_tier = str(s.get('tier', '') or '')  # V1.1
                    # Also get zone values directly from Analysis sheet
                    if s.get('zone_high', 0) > 0:
                        setup.secondary_high = float(s.get('zone_high', 0) or 0)
                        setup.secondary_low = float(s.get('zone_low', 0) or 0)
                        setup.secondary_target = float(s.get('target', 0) or 0)
                    # V1.2: Look up confluences from zone_results
                    secondary_zone_id = setup.secondary_zone_id
                    for z in ticker_zones:
                        if z.zone_id == secondary_zone_id:
                            setup.secondary_confluences = z.confluences or ''
                            break
                
                # Get epoch data for this ticker
                epoch = epoch_data_dict.get(ticker, EpochData(ticker=ticker, start_date=""))
                
                result[ticker] = VisualizationData(
                    ticker=ticker,
                    ticker_id=ticker_data.ticker_id,
                    market_structure=market_structure,
                    ticker_structure=ticker_data,
                    zones=ticker_zones,
                    setup=setup,
                    epoch=epoch
                )
                
                # V1.1: Log tier info
                pri_tier = setup.primary_tier or "N/A"
                sec_tier = setup.secondary_tier or "N/A"
                logger.info(f"Loaded data for {ticker}: {len(ticker_zones)} zones, "
                           f"epoch={epoch.start_date}, pri_tier={pri_tier}, sec_tier={sec_tier}")
        
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
        """Read all zones from zone_results worksheet - V1.1 with tier"""
        ws = self.wb.sheets[WORKSHEETS['zone_results']]
        zones = []
        
        # Read data starting from row 2
        row = 2
        max_empty = 3  # Stop after 3 empty rows
        empty_count = 0
        
        while empty_count < max_empty:
            ticker_id = self._safe_read(ws, f"{ZONE_RESULTS_COLUMNS['ticker_id']}{row}", '')
            
            if not ticker_id:
                empty_count += 1
                row += 1
                continue
            
            empty_count = 0
            
            try:
                zone = ZoneResult(
                    ticker_id=ticker_id,
                    ticker=self._safe_read(ws, f"{ZONE_RESULTS_COLUMNS['ticker']}{row}", ''),
                    date=str(self._safe_read(ws, f"{ZONE_RESULTS_COLUMNS['date']}{row}", '')),
                    price=self._safe_read(ws, f"{ZONE_RESULTS_COLUMNS['price']}{row}", 0.0),
                    direction=self._safe_read(ws, f"{ZONE_RESULTS_COLUMNS['direction']}{row}", ''),
                    zone_id=self._safe_read(ws, f"{ZONE_RESULTS_COLUMNS['zone_id']}{row}", ''),
                    hvn_poc=self._safe_read(ws, f"{ZONE_RESULTS_COLUMNS['hvn_poc']}{row}", 0.0),
                    zone_high=self._safe_read(ws, f"{ZONE_RESULTS_COLUMNS['zone_high']}{row}", 0.0),
                    zone_low=self._safe_read(ws, f"{ZONE_RESULTS_COLUMNS['zone_low']}{row}", 0.0),
                    overlaps=int(self._safe_read(ws, f"{ZONE_RESULTS_COLUMNS['overlaps']}{row}", 0)),
                    score=self._safe_read(ws, f"{ZONE_RESULTS_COLUMNS['score']}{row}", 0.0),
                    rank=self._safe_read(ws, f"{ZONE_RESULTS_COLUMNS['rank']}{row}", ''),
                    confluences=self._safe_read(ws, f"{ZONE_RESULTS_COLUMNS['confluences']}{row}", ''),
                    tier=self._safe_read(ws, f"{ZONE_RESULTS_COLUMNS['tier']}{row}", '')  # V1.1
                )
                zones.append(zone)
            except Exception as e:
                logger.warning(f"Failed to read zone at row {row}: {e}")
            
            row += 1
        
        logger.info(f"Read {len(zones)} zones from zone_results (V1.1 with tier)")
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
    
    def _read_setup_details_v11(self) -> Tuple[Dict, Dict]:
        """
        V1.1: Read primary and secondary setup details with updated column mappings.
        
        Primary: B31:L40 (tier at column I)
        Secondary: N31:X40 (tier at column U)
        
        Returns:
            Tuple of (primary_dict, secondary_dict) with all fields including tier
        """
        ws = self.wb.sheets[WORKSHEETS['analysis']]
        primary = {}
        secondary = {}
        
        for row in range(ANALYSIS_SETUP_START_ROW, ANALYSIS_SETUP_END_ROW + 1):
            # Primary section: B-L (V1.1 columns)
            ticker = self._safe_read(ws, f"{ANALYSIS_PRIMARY_COLUMNS['ticker']}{row}", '')
            if ticker:
                ticker = ticker.upper()
                primary[ticker] = {
                    'direction': self._safe_read(ws, f"{ANALYSIS_PRIMARY_COLUMNS['direction']}{row}", ''),
                    'ticker_id': self._safe_read(ws, f"{ANALYSIS_PRIMARY_COLUMNS['ticker_id']}{row}", ''),
                    'zone_id': self._safe_read(ws, f"{ANALYSIS_PRIMARY_COLUMNS['zone_id']}{row}", ''),
                    'hvn_poc': self._safe_read(ws, f"{ANALYSIS_PRIMARY_COLUMNS['hvn_poc']}{row}", 0),
                    'zone_high': self._safe_read(ws, f"{ANALYSIS_PRIMARY_COLUMNS['zone_high']}{row}", 0),
                    'zone_low': self._safe_read(ws, f"{ANALYSIS_PRIMARY_COLUMNS['zone_low']}{row}", 0),
                    'tier': self._safe_read(ws, f"{ANALYSIS_PRIMARY_COLUMNS['tier']}{row}", ''),  # V1.1
                    'target_id': self._safe_read(ws, f"{ANALYSIS_PRIMARY_COLUMNS['target_id']}{row}", ''),
                    'target': self._safe_read(ws, f"{ANALYSIS_PRIMARY_COLUMNS['target']}{row}", 0),
                    'r_r': self._safe_read(ws, f"{ANALYSIS_PRIMARY_COLUMNS['r_r']}{row}", '')
                }
            
            # Secondary section: N-X (V1.1 columns)
            ticker2 = self._safe_read(ws, f"{ANALYSIS_SECONDARY_COLUMNS['ticker']}{row}", '')
            if ticker2:
                ticker2 = ticker2.upper()
                secondary[ticker2] = {
                    'direction': self._safe_read(ws, f"{ANALYSIS_SECONDARY_COLUMNS['direction']}{row}", ''),
                    'ticker_id': self._safe_read(ws, f"{ANALYSIS_SECONDARY_COLUMNS['ticker_id']}{row}", ''),
                    'zone_id': self._safe_read(ws, f"{ANALYSIS_SECONDARY_COLUMNS['zone_id']}{row}", ''),
                    'hvn_poc': self._safe_read(ws, f"{ANALYSIS_SECONDARY_COLUMNS['hvn_poc']}{row}", 0),
                    'zone_high': self._safe_read(ws, f"{ANALYSIS_SECONDARY_COLUMNS['zone_high']}{row}", 0),
                    'zone_low': self._safe_read(ws, f"{ANALYSIS_SECONDARY_COLUMNS['zone_low']}{row}", 0),
                    'tier': self._safe_read(ws, f"{ANALYSIS_SECONDARY_COLUMNS['tier']}{row}", ''),  # V1.1
                    'target_id': self._safe_read(ws, f"{ANALYSIS_SECONDARY_COLUMNS['target_id']}{row}", ''),
                    'target': self._safe_read(ws, f"{ANALYSIS_SECONDARY_COLUMNS['target']}{row}", 0),
                    'r_r': self._safe_read(ws, f"{ANALYSIS_SECONDARY_COLUMNS['r_r']}{row}", '')
                }
        
        return primary, secondary
    
    def _read_epoch_data(self) -> Dict[str, EpochData]:
        """
        Read epoch start dates and HVN POCs from time_hvn section.
        
        Reads from bar_data worksheet:
        - Rows 59-68 (t1-t10)
        - Column C: ticker
        - Column E: start_date
        - Columns F-O: hvn_poc1 through hvn_poc10
        
        Returns:
            Dict mapping ticker symbol to EpochData
        """
        ws = self.wb.sheets[WORKSHEETS['bar_data']]
        result = {}
        
        for slot in range(1, 11):
            row = TICKER_ROWS['time_hvn'][f't{slot}']
            
            try:
                ticker = self._safe_read(ws, f"{TIME_HVN_COLUMNS['ticker']}{row}", '')
                if not ticker:
                    continue
                
                ticker = ticker.upper()
                
                # Read start_date
                start_date_val = self._safe_read(ws, f"{TIME_HVN_COLUMNS['start_date']}{row}", '')
                
                # Convert date to string if it's a datetime
                if hasattr(start_date_val, 'strftime'):
                    start_date = start_date_val.strftime('%Y-%m-%d')
                elif start_date_val:
                    start_date = str(start_date_val)
                else:
                    start_date = ''
                
                # Read 10 POCs
                hvn_pocs = []
                for i in range(1, 11):
                    col = TIME_HVN_COLUMNS[f'hvn_poc{i}']
                    poc = self._safe_read(ws, f"{col}{row}", 0.0)
                    hvn_pocs.append(float(poc) if poc else 0.0)
                
                result[ticker] = EpochData(
                    ticker=ticker,
                    start_date=start_date,
                    hvn_pocs=hvn_pocs
                )
                
                poc_count = sum(1 for p in hvn_pocs if p > 0)
                logger.debug(f"Read epoch for {ticker}: start={start_date}, {poc_count} POCs")
                
            except Exception as e:
                logger.warning(f"Failed to read epoch data for slot {slot}: {e}")
        
        return result
    
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
    """Test the Excel reader - V1.1"""
    reader = EpochExcelReader()
    
    if not reader.connect():
        print("Failed to connect to workbook. Ensure it's open.")
        return
    
    data = reader.read_all_tickers()
    
    print(f"\n{'='*60}")
    print(f"Loaded {len(data)} tickers (V1.1 with tier support)")
    print(f"{'='*60}")
    
    for ticker, viz_data in data.items():
        print(f"\n{ticker}:")
        print(f"  Composite: {viz_data.ticker_structure.composite}")
        print(f"  Price: ${viz_data.ticker_structure.price:.2f}")
        print(f"  ATR: ${viz_data.ticker_structure.d1_atr:.2f}")
        print(f"  Zones: {len(viz_data.zones)}")
        print(f"  Primary Tier: {viz_data.setup.primary_tier or 'N/A'}")
        print(f"  Secondary Tier: {viz_data.setup.secondary_tier or 'N/A'}")
        print(f"  Setup String: {viz_data.setup.setup_string}")
        
        # Show zone tiers
        if viz_data.zones:
            tier_counts = {}
            for z in viz_data.zones:
                tier = z.tier or 'Unknown'
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
            print(f"  Zone Tiers: {tier_counts}")


if __name__ == "__main__":
    main()

# summary_exporter.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\08_visualization\
# Purpose: Standalone runner to export visualization summary to Excel for Supabase

"""
Module 08 Summary Exporter - V1.1

Standalone script that:
1. Reads all visualization data (same as Streamlit app)
2. Compiles into a summary table
3. Writes to Analysis worksheet starting at B2
4. Ready for Supabase export

V1.1 CHANGES:
- Updated Analysis column references for tier column addition
- Primary section: B31:L40 (includes tier at column I)
- Secondary section: N31:X40 (includes tier at column U)
- Reads zone_high, zone_low, target directly from Analysis sheet
- Builds PineScript string from actual data, not pre-computed cells

Run: python summary_exporter.py
"""

import xlwings as xw
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
import sys
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR = Path(r"C:\XIIITradingSystems\Epoch")
MODULE_DIR = BASE_DIR / "02_zone_system" / "08_visualization"
WORKBOOK_NAME = "epoch_v1.xlsm"
WORKBOOK_PATH = BASE_DIR / WORKBOOK_NAME

WORKSHEETS = {
    'market_overview': 'market_overview',
    'bar_data': 'bar_data',
    'zone_results': 'zone_results',
    'analysis': 'Analysis'
}

INDEX_ROWS = {'SPY': 29, 'QQQ': 30, 'DIA': 31}

TICKER_ROWS = {
    'market_overview': {f't{i}': 35 + i for i in range(1, 11)},
    'bar_data_ticker': {f't{i}': 3 + i for i in range(1, 11)},
    'bar_data_atr': {f't{i}': 72 + i for i in range(1, 11)},
    'time_hvn': {f't{i}': 58 + i for i in range(1, 11)},
    'analysis_strings': {f't{i}': 43 + i for i in range(1, 11)}
}

TIME_HVN_COLUMNS = {
    'ticker': 'C', 'start_date': 'E',
    'hvn_poc1': 'F', 'hvn_poc2': 'G', 'hvn_poc3': 'H', 'hvn_poc4': 'I', 'hvn_poc5': 'J',
    'hvn_poc6': 'K', 'hvn_poc7': 'L', 'hvn_poc8': 'M', 'hvn_poc9': 'N', 'hvn_poc10': 'O'
}

# =============================================================================
# V1.1 ANALYSIS SHEET COLUMN MAPPINGS
# =============================================================================

# Primary section: B31:L40 (rows 31-40, 11 columns with tier)
ANALYSIS_PRIMARY_COLUMNS = {
    'ticker': 'B',
    'direction': 'C',
    'ticker_id': 'D',
    'zone_id': 'E',
    'hvn_poc': 'F',
    'zone_high': 'G',
    'zone_low': 'H',
    'tier': 'I',
    'target_id': 'J',
    'target': 'K',
    'r_r': 'L'
}

# Secondary section: N31:X40 (rows 31-40, 11 columns with tier)
ANALYSIS_SECONDARY_COLUMNS = {
    'ticker': 'N',
    'direction': 'O',
    'ticker_id': 'P',
    'zone_id': 'Q',
    'hvn_poc': 'R',
    'zone_high': 'S',
    'zone_low': 'T',
    'tier': 'U',
    'target_id': 'V',
    'target': 'W',
    'r_r': 'X'
}

ANALYSIS_SETUP_START_ROW = 31
ANALYSIS_SETUP_END_ROW = 40

# Summary output location
SUMMARY_START_ROW = 2
SUMMARY_START_COL = 'B'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class TickerSummary:
    """Complete summary for one ticker"""
    # Basic info
    ticker: str
    ticker_id: str
    date: str
    price: float
    
    # Market structure
    composite: str
    d1_dir: str
    h4_dir: str
    h1_dir: str
    m15_dir: str
    
    # ATR values
    d1_atr: float
    m5_atr: float
    
    # Primary setup
    pri_dir: str
    pri_zone: str
    pri_poc: float
    pri_high: float
    pri_low: float
    pri_target: float
    pri_tier: str
    pri_rr: str
    
    # Secondary setup
    sec_dir: str
    sec_zone: str
    sec_poc: float
    sec_high: float
    sec_low: float
    sec_target: float
    sec_tier: str
    sec_rr: str
    
    # Zone summary
    zone_count: int
    top_zone_id: str
    top_zone_poc: float
    top_zone_rank: str
    top_zone_score: float
    
    # Epoch data
    epoch_start: str
    poc1: float
    poc2: float
    poc3: float
    poc4: float
    poc5: float
    poc6: float
    poc7: float
    poc8: float
    poc9: float
    poc10: float
    
    # PineScript strings
    pinescript_6: str   # Original 6-value format
    pinescript_16: str  # Full 16-value format with POCs
    
    # Timestamp
    export_time: str


# =============================================================================
# EXCEL READER (UPDATED FOR V1.1)
# =============================================================================

class SummaryExcelReader:
    """Read data for summary export - V1.1 compatible"""
    
    def __init__(self, workbook_path: Path = None):
        self.workbook_path = workbook_path or WORKBOOK_PATH
        self.wb = None
    
    def connect(self) -> bool:
        """Connect to open Excel workbook"""
        try:
            self.wb = xw.Book(str(self.workbook_path))
            logger.info(f"Connected to: {self.workbook_path.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            logger.error("Ensure the workbook is open in Excel")
            return False
    
    def _safe_read(self, ws, cell: str, default):
        """Safe cell read with fallback"""
        try:
            value = ws.range(cell).value
            return default if value is None else value
        except:
            return default
    
    def _safe_float(self, value, default=0.0) -> float:
        """Safe float conversion"""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def read_all_summaries(self) -> List[TickerSummary]:
        """Read and compile all ticker summaries"""
        if not self.wb:
            if not self.connect():
                return []
        
        ws_overview = self.wb.sheets[WORKSHEETS['market_overview']]
        ws_bar = self.wb.sheets[WORKSHEETS['bar_data']]
        ws_zones = self.wb.sheets[WORKSHEETS['zone_results']]
        ws_analysis = self.wb.sheets[WORKSHEETS['analysis']]
        
        # Read all zones first
        all_zones = self._read_all_zones(ws_zones)
        
        # V1.1: Read primary/secondary setup details with correct column mappings
        primary_setups, secondary_setups = self._read_setup_details_v11(ws_analysis)
        
        summaries = []
        export_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for slot in range(1, 11):
            row_overview = TICKER_ROWS['market_overview'][f't{slot}']
            row_ticker = TICKER_ROWS['bar_data_ticker'][f't{slot}']
            row_atr = TICKER_ROWS['bar_data_atr'][f't{slot}']
            row_hvn = TICKER_ROWS['time_hvn'][f't{slot}']
            
            ticker = self._safe_read(ws_overview, f'C{row_overview}', '')
            if not ticker:
                continue
            
            ticker = ticker.upper()
            
            # Basic info
            ticker_id = self._safe_read(ws_overview, f'B{row_overview}', '')
            date_val = self._safe_read(ws_overview, f'D{row_overview}', '')
            date_str = date_val.strftime('%Y-%m-%d') if hasattr(date_val, 'strftime') else str(date_val)
            price = self._safe_float(self._safe_read(ws_bar, f'E{row_ticker}', 0))
            
            # Market structure
            composite = self._safe_read(ws_overview, f'R{row_overview}', '')
            d1_dir = self._safe_read(ws_overview, f'F{row_overview}', '')
            h4_dir = self._safe_read(ws_overview, f'I{row_overview}', '')
            h1_dir = self._safe_read(ws_overview, f'L{row_overview}', '')
            m15_dir = self._safe_read(ws_overview, f'O{row_overview}', '')
            
            # ATR
            d1_atr = self._safe_float(self._safe_read(ws_bar, f'T{row_atr}', 0))
            m5_atr = self._safe_float(self._safe_read(ws_bar, f'Q{row_atr}', 0))
            
            # V1.1: Get primary setup from Analysis sheet
            pri_dir, pri_zone, pri_poc, pri_high, pri_low, pri_target, pri_tier, pri_rr = '', '', 0.0, 0.0, 0.0, 0.0, '', ''
            if ticker in primary_setups:
                p = primary_setups[ticker]
                pri_dir = str(p.get('direction', '') or '')
                pri_zone = str(p.get('zone_id', '') or '')
                pri_poc = self._safe_float(p.get('hvn_poc', 0))
                pri_high = self._safe_float(p.get('zone_high', 0))
                pri_low = self._safe_float(p.get('zone_low', 0))
                pri_target = self._safe_float(p.get('target', 0))
                pri_tier = str(p.get('tier', '') or '')
                pri_rr = str(p.get('r_r', '') or '')
            
            # V1.1: Get secondary setup from Analysis sheet
            sec_dir, sec_zone, sec_poc, sec_high, sec_low, sec_target, sec_tier, sec_rr = '', '', 0.0, 0.0, 0.0, 0.0, '', ''
            if ticker in secondary_setups:
                s = secondary_setups[ticker]
                sec_dir = str(s.get('direction', '') or '')
                sec_zone = str(s.get('zone_id', '') or '')
                sec_poc = self._safe_float(s.get('hvn_poc', 0))
                sec_high = self._safe_float(s.get('zone_high', 0))
                sec_low = self._safe_float(s.get('zone_low', 0))
                sec_target = self._safe_float(s.get('target', 0))
                sec_tier = str(s.get('tier', '') or '')
                sec_rr = str(s.get('r_r', '') or '')
            
            # Zone summary
            ticker_zones = [z for z in all_zones if z['ticker'].upper() == ticker]
            zone_count = len(ticker_zones)
            top_zone_id, top_zone_poc, top_zone_rank, top_zone_score = '', 0.0, '', 0.0
            if ticker_zones:
                top = ticker_zones[0]  # First zone (highest ranked)
                top_zone_id = top['zone_id'].replace(f'{ticker}_', '')
                top_zone_poc = top['hvn_poc']
                top_zone_rank = top['rank']
                top_zone_score = top['score']
            
            # Epoch data
            epoch_start_val = self._safe_read(ws_bar, f"E{row_hvn}", '')
            epoch_start = epoch_start_val.strftime('%Y-%m-%d') if hasattr(epoch_start_val, 'strftime') else str(epoch_start_val or '')
            
            pocs = []
            for i in range(1, 11):
                col = TIME_HVN_COLUMNS[f'hvn_poc{i}']
                poc_val = self._safe_float(self._safe_read(ws_bar, f"{col}{row_hvn}", 0))
                pocs.append(poc_val)
            
            # Build 6-value PineScript string (zone values only)
            pinescript_6_vals = [pri_high, pri_low, pri_target, sec_high, sec_low, sec_target]
            pinescript_6 = ",".join(f"{v:.2f}" if v != 0 else "0" for v in pinescript_6_vals)
            
            # Build 16-value PineScript string (zones + POCs)
            pinescript_16_vals = pinescript_6_vals + pocs
            pinescript_16 = ",".join(f"{v:.2f}" if v != 0 else "0" for v in pinescript_16_vals)
            
            summary = TickerSummary(
                ticker=ticker,
                ticker_id=ticker_id,
                date=date_str,
                price=price,
                composite=str(composite or ''),
                d1_dir=str(d1_dir or ''),
                h4_dir=str(h4_dir or ''),
                h1_dir=str(h1_dir or ''),
                m15_dir=str(m15_dir or ''),
                d1_atr=d1_atr,
                m5_atr=m5_atr,
                pri_dir=pri_dir,
                pri_zone=pri_zone,
                pri_poc=pri_poc,
                pri_high=pri_high,
                pri_low=pri_low,
                pri_target=pri_target,
                pri_tier=pri_tier,
                pri_rr=pri_rr,
                sec_dir=sec_dir,
                sec_zone=sec_zone,
                sec_poc=sec_poc,
                sec_high=sec_high,
                sec_low=sec_low,
                sec_target=sec_target,
                sec_tier=sec_tier,
                sec_rr=sec_rr,
                zone_count=zone_count,
                top_zone_id=top_zone_id,
                top_zone_poc=top_zone_poc,
                top_zone_rank=str(top_zone_rank or ''),
                top_zone_score=top_zone_score,
                epoch_start=epoch_start,
                poc1=pocs[0], poc2=pocs[1], poc3=pocs[2], poc4=pocs[3], poc5=pocs[4],
                poc6=pocs[5], poc7=pocs[6], poc8=pocs[7], poc9=pocs[8], poc10=pocs[9],
                pinescript_6=pinescript_6,
                pinescript_16=pinescript_16,
                export_time=export_time
            )
            summaries.append(summary)
            logger.info(f"Read summary for {ticker}: {zone_count} zones, composite={composite}, pri_high={pri_high:.2f}, sec_high={sec_high:.2f}")
        
        return summaries
    
    def _read_all_zones(self, ws) -> List[Dict]:
        """Read all zones from zone_results (V1.1: includes tier at column N)"""
        zones = []
        row = 2
        empty_count = 0
        
        while empty_count < 3:
            ticker_id = self._safe_read(ws, f'A{row}', '')
            if not ticker_id:
                empty_count += 1
                row += 1
                continue
            
            empty_count = 0
            zones.append({
                'ticker_id': ticker_id,
                'ticker': self._safe_read(ws, f'B{row}', ''),
                'zone_id': self._safe_read(ws, f'F{row}', ''),
                'hvn_poc': self._safe_float(self._safe_read(ws, f'G{row}', 0)),
                'zone_high': self._safe_float(self._safe_read(ws, f'H{row}', 0)),
                'zone_low': self._safe_float(self._safe_read(ws, f'I{row}', 0)),
                'score': self._safe_float(self._safe_read(ws, f'K{row}', 0)),
                'rank': self._safe_read(ws, f'L{row}', ''),
                'tier': self._safe_read(ws, f'N{row}', '')  # V1.1: Added tier
            })
            row += 1
        
        return zones
    
    def _read_setup_details_v11(self, ws):
        """
        V1.1: Read primary and secondary setup details with correct column mappings.
        
        Primary: B31:L40
        Secondary: N31:X40
        
        Returns all fields including zone_high, zone_low, target, tier.
        """
        primary, secondary = {}, {}
        
        for row in range(ANALYSIS_SETUP_START_ROW, ANALYSIS_SETUP_END_ROW + 1):
            # Primary: B-L (V1.1 columns)
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
                    'tier': self._safe_read(ws, f"{ANALYSIS_PRIMARY_COLUMNS['tier']}{row}", ''),
                    'target_id': self._safe_read(ws, f"{ANALYSIS_PRIMARY_COLUMNS['target_id']}{row}", ''),
                    'target': self._safe_read(ws, f"{ANALYSIS_PRIMARY_COLUMNS['target']}{row}", 0),
                    'r_r': self._safe_read(ws, f"{ANALYSIS_PRIMARY_COLUMNS['r_r']}{row}", '')
                }
            
            # Secondary: N-X (V1.1 columns)
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
                    'tier': self._safe_read(ws, f"{ANALYSIS_SECONDARY_COLUMNS['tier']}{row}", ''),
                    'target_id': self._safe_read(ws, f"{ANALYSIS_SECONDARY_COLUMNS['target_id']}{row}", ''),
                    'target': self._safe_read(ws, f"{ANALYSIS_SECONDARY_COLUMNS['target']}{row}", 0),
                    'r_r': self._safe_read(ws, f"{ANALYSIS_SECONDARY_COLUMNS['r_r']}{row}", '')
                }
        
        return primary, secondary


# =============================================================================
# SUMMARY WRITER (UPDATED FOR V1.1)
# =============================================================================

class SummaryWriter:
    """Write summary tables to Excel - V1.1 compatible with tier columns"""
    
    # Table 1: B2 to AB (28 columns) - Core trading data (added tier columns)
    HEADERS_TABLE1 = [
        'Ticker', 'Ticker_ID', 'Date', 'Price', 'Composite',
        'D1_Dir', 'H4_Dir', 'H1_Dir', 'M15_Dir', 'D1_ATR', 'M5_ATR',
        'Pri_Dir', 'Pri_Zone', 'Pri_POC', 'Pri_High', 'Pri_Low', 'Pri_Target', 'Pri_Tier', 'Pri_RR',
        'Sec_Dir', 'Sec_Zone', 'Sec_POC', 'Sec_High', 'Sec_Low', 'Sec_Target', 'Sec_Tier', 'Sec_RR',
        'Zone_Count'
    ]
    
    # Table 2: B14+ - Zone details, Epoch POCs, PineScript strings
    HEADERS_TABLE2 = [
        'Ticker', 'Ticker_ID', 'Date',
        'Top_Zone_ID', 'Top_Zone_POC', 'Top_Zone_Rank', 'Top_Zone_Score',
        'Epoch_Start', 'POC1', 'POC2', 'POC3', 'POC4', 'POC5', 'POC6', 'POC7', 'POC8', 'POC9', 'POC10',
        'PineScript_6', 'PineScript_16', 'Export_Time'
    ]
    
    # Header formatting colors
    HEADER_BG_COLOR = (64, 64, 64)      # RGB dark gray
    HEADER_TEXT_COLOR = (242, 242, 242)  # RGB light gray/white
    
    def __init__(self, workbook_path: Path = None):
        self.workbook_path = workbook_path or WORKBOOK_PATH
        self.wb = None
    
    def connect(self) -> bool:
        """Connect to workbook"""
        try:
            self.wb = xw.Book(str(self.workbook_path))
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def write_summary(self, summaries: List[TickerSummary], start_row: int = 2, start_col: str = 'B'):
        """Write summary tables to Analysis worksheet"""
        if not self.wb:
            if not self.connect():
                return False
        
        ws = self.wb.sheets[WORKSHEETS['analysis']]
        
        # Clear existing summary areas
        # Table 1: B2:AC12 (expanded for tier columns)
        # Table 2: B14:V24
        try:
            ws.range('B2:AC12').clear_contents()
            ws.range('B14:V24').clear_contents()
        except:
            pass
        
        # =====================================================================
        # TABLE 1: B2+ (Core Trading Data with Tier)
        # =====================================================================
        table1_row = 2
        
        # Write Table 1 headers
        for i, header in enumerate(self.HEADERS_TABLE1):
            col = self._get_col_letter(1 + i)  # Start at B (index 1)
            ws.range(f"{col}{table1_row}").value = header
        
        # Format Table 1 headers
        end_col_t1 = self._get_col_letter(1 + len(self.HEADERS_TABLE1) - 1)
        header1_range = ws.range(f"B{table1_row}:{end_col_t1}{table1_row}")
        header1_range.font.bold = True
        header1_range.color = self.HEADER_BG_COLOR
        header1_range.font.color = self.HEADER_TEXT_COLOR
        
        # Write Table 1 data
        for row_idx, summary in enumerate(summaries):
            data_row = table1_row + 1 + row_idx
            
            values = [
                summary.ticker, summary.ticker_id, summary.date, summary.price, summary.composite,
                summary.d1_dir, summary.h4_dir, summary.h1_dir, summary.m15_dir, summary.d1_atr, summary.m5_atr,
                summary.pri_dir, summary.pri_zone, summary.pri_poc, summary.pri_high, summary.pri_low, summary.pri_target, summary.pri_tier, summary.pri_rr,
                summary.sec_dir, summary.sec_zone, summary.sec_poc, summary.sec_high, summary.sec_low, summary.sec_target, summary.sec_tier, summary.sec_rr,
                summary.zone_count
            ]
            
            for col_idx, value in enumerate(values):
                col = self._get_col_letter(1 + col_idx)  # Start at B
                ws.range(f"{col}{data_row}").value = value
        
        logger.info(f"Table 1 written to Analysis!B{table1_row}:{end_col_t1}{table1_row + len(summaries)}")
        
        # =====================================================================
        # TABLE 2: B14+ (Zone Details, Epoch POCs, PineScript)
        # =====================================================================
        table2_row = 14
        
        # Write Table 2 headers
        for i, header in enumerate(self.HEADERS_TABLE2):
            col = self._get_col_letter(1 + i)  # Start at B
            ws.range(f"{col}{table2_row}").value = header
        
        # Format Table 2 headers
        end_col_t2 = self._get_col_letter(1 + len(self.HEADERS_TABLE2) - 1)
        header2_range = ws.range(f"B{table2_row}:{end_col_t2}{table2_row}")
        header2_range.font.bold = True
        header2_range.color = self.HEADER_BG_COLOR
        header2_range.font.color = self.HEADER_TEXT_COLOR
        
        # Write Table 2 data
        for row_idx, summary in enumerate(summaries):
            data_row = table2_row + 1 + row_idx
            
            values = [
                summary.ticker, summary.ticker_id, summary.date,
                summary.top_zone_id, summary.top_zone_poc, summary.top_zone_rank, summary.top_zone_score,
                summary.epoch_start, summary.poc1, summary.poc2, summary.poc3, summary.poc4, summary.poc5,
                summary.poc6, summary.poc7, summary.poc8, summary.poc9, summary.poc10,
                summary.pinescript_6, summary.pinescript_16, summary.export_time
            ]
            
            for col_idx, value in enumerate(values):
                col = self._get_col_letter(1 + col_idx)  # Start at B
                ws.range(f"{col}{data_row}").value = value
        
        logger.info(f"Table 2 written to Analysis!B{table2_row}:{end_col_t2}{table2_row + len(summaries)}")
        
        return True
    
    def _get_col_letter(self, col_num: int) -> str:
        """Convert column number (0-indexed) to Excel column letter"""
        if col_num < 26:
            return chr(ord('A') + col_num)
        else:
            first = col_num // 26 - 1
            second = col_num % 26
            return chr(ord('A') + first) + chr(ord('A') + second)


# =============================================================================
# MAIN RUNNER
# =============================================================================

def main():
    """Main entry point for summary export"""
    print("=" * 70)
    print("EPOCH VISUALIZATION SUMMARY EXPORTER - V1.1")
    print("XIII Trading LLC")
    print("=" * 70)
    print()
    print("V1.1 Changes:")
    print("  - Updated for tier column addition in Analysis sheet")
    print("  - Primary: B31:L40, Secondary: N31:X40")
    print("  - Reads zone_high, zone_low, target directly from Analysis")
    print("  - PineScript strings built from actual data")
    print()
    
    # Check workbook path
    if not WORKBOOK_PATH.exists():
        print(f"ERROR: Workbook not found at {WORKBOOK_PATH}")
        print("Please ensure the workbook exists and try again.")
        return False
    
    print(f"Workbook: {WORKBOOK_PATH}")
    print(f"Output: Analysis worksheet")
    print(f"  Table 1: B2+  (Core trading data with tier)")
    print(f"  Table 2: B14+ (Zone details, Epoch POCs, PineScript)")
    print()
    
    # Read summaries
    print("Reading visualization data...")
    reader = SummaryExcelReader()
    if not reader.connect():
        return False
    
    summaries = reader.read_all_summaries()
    
    if not summaries:
        print("ERROR: No ticker data found")
        return False
    
    print(f"Found {len(summaries)} tickers")
    print()
    
    # Preview PineScript strings
    print("PineScript 16-Value Strings Preview:")
    print("-" * 50)
    for s in summaries:
        print(f"  {s.ticker}: {s.pinescript_16[:60]}...")
    print()
    
    # Write to Excel
    print("Writing summary tables to Analysis worksheet...")
    writer = SummaryWriter()
    if not writer.connect():
        return False
    
    success = writer.write_summary(summaries, start_row=2, start_col='B')
    
    if success:
        print()
        print("=" * 70)
        print("SUCCESS!")
        print()
        print("TABLE 1 (B2+) - Core Trading Data (V1.1 with Tier):")
        print(f"  Columns: {len(SummaryWriter.HEADERS_TABLE1)}")
        for i, h in enumerate(SummaryWriter.HEADERS_TABLE1):
            col = writer._get_col_letter(1 + i)
            print(f"    {col}: {h}")
        print()
        print("TABLE 2 (B14+) - Zone Details & Epoch POCs:")
        print(f"  Columns: {len(SummaryWriter.HEADERS_TABLE2)}")
        for i, h in enumerate(SummaryWriter.HEADERS_TABLE2):
            col = writer._get_col_letter(1 + i)
            print(f"    {col}: {h}")
        print()
        print(f"Rows per table: {len(summaries)} tickers + 1 header")
        print()
        print("Ready for Supabase export!")
        print("=" * 70)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
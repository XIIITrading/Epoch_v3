"""
Module 10: Excel Reader (xlwings version)
Reads backtest results and zone data from epoch_v1.xlsm

Uses xlwings to read from live Excel instance (consistent with other EPOCH modules).
Works whether workbook is open or closed.

UPDATED: V1.1 compatibility - Tier column included
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from pathlib import Path
import xlwings as xw

from config import (
    EXCEL_WORKBOOK,
    SHEET_ANALYSIS, SHEET_BACKTEST, SHEET_MARKET,
    SHEET_ENTRY_EVENTS, SHEET_EXIT_EVENTS, SHEET_OPTIMAL_TRADE,
    ANALYSIS_PRIMARY, ANALYSIS_SECONDARY,
    MARKET_OVERVIEW, BACKTEST_TRADES, BACKTEST_NO_TRADES,
    ENTRY_EVENTS, EXIT_EVENTS, OPTIMAL_TRADE,
    MODEL_NAMES, WIN_VALUES
)


@dataclass
class Trade:
    """Single trade record from backtest sheet (v2.3 format)."""
    trade_id: str         # v2.3: NEW - format: ticker_MMDDYY_model_HHMM
    date: str
    ticker: str
    model: str
    model_name: str
    zone_type: str
    direction: str
    zone_high: float
    zone_low: float
    entry_price: float
    entry_time: str
    stop_price: float
    target_3r: float      # v2.3: renamed from target_2r
    target_calc: float
    target_used: float    # v2.3: NEW
    exit_price: float
    exit_time: str
    exit_reason: str
    pnl_dollars: float
    pnl_r: float
    risk: float           # v2.3: NEW
    is_win: bool


@dataclass
class NoTrade:
    """Non-triggered setup from backtest sheet."""
    date: str
    ticker: str
    model: str
    model_name: str
    zone_type: str
    direction: str
    zone_high: float
    zone_low: float
    reason: str
    day_high: float
    day_low: float
    day_open: float
    day_close: float
    zone_touched: bool
    bars_in_zone: int


@dataclass
class ZoneData:
    """Zone configuration from analysis sheet (V1.1 - includes Tier)."""
    ticker: str
    direction: str
    zone_high: float
    zone_low: float
    hvn_poc: float
    tier: str           # V1.1: T1, T2, or T3
    target: float
    rr_ratio: float


@dataclass
class MarketStructure:
    """Market structure data for a ticker."""
    ticker: str
    composite: str
    d1_dir: str
    h4_dir: str
    h1_dir: str
    m15_dir: str


@dataclass
class EntryEvent:
    """Entry enrichment data from entry_events sheet (v3 lean)."""
    trade_id: str
    # Price Position
    entry_vwap: float
    entry_vs_vwap: str
    entry_sma9: float
    entry_vs_sma9: str
    entry_sma21: float
    entry_vs_sma21: str
    sma9_vs_sma21: str
    # Volume Analysis
    entry_volume: int
    avg_volume_5: float
    volume_delta_pct: float
    volume_trend: str
    relative_volume: float
    prior_bar_qual: str
    vol_delta_class: str
    vol_delta_value: int
    # Multi-Timeframe Structure
    m5_structure: str
    m15_structure: str
    h1_structure: str
    h4_structure: str
    structure_align: int
    dominant_struct: str
    m5_last_break: str
    m15_last_break: str
    # Health Score
    health_score: int
    health_max: int
    health_pct: float
    health_label: str
    # Alignment Flags
    vwap_aligned: bool
    trend_aligned: bool
    structure_aligned: bool
    # Metadata
    status: str
    error: str


@dataclass
class ExitEvent:
    """Single event from exit_events sheet (v2 lean)."""
    trade_id: str
    # Event Timing
    event_seq: int
    event_time: str
    bars_from_entry: int
    bars_from_mfe: int
    # Event Details
    event_type: str
    from_state: str
    to_state: str
    # Position at Event
    price_at_event: float
    r_at_event: float
    health_score: int
    health_delta: int
    # Indicator Values
    vwap: float
    sma9: float
    sma21: float
    volume: int
    swing_high: float
    swing_low: float


@dataclass
class OptimalTrade:
    """Optimal exit analysis from optimal_trade sheet."""
    trade_id: str
    optimal_exit_price: float
    optimal_exit_time: str
    optimal_exit_reason: str
    optimal_pnl_r: float
    mfe_price: float
    mfe_time: str
    mfe_r: float
    mae_price: float
    mae_time: str
    mae_r: float
    capture_efficiency: float
    notes: str


class ExcelReader:
    """
    Reads data from EPOCH Excel workbook using xlwings.
    
    Connects to open workbook if available, otherwise opens the file.
    This ensures we read live data even if the workbook hasn't been saved.
    """
    
    def __init__(self, workbook_path: Path = None):
        self.workbook_path = workbook_path or EXCEL_WORKBOOK
        self._wb = None
        self._app = None
        self._opened_by_us = False
    
    def _get_workbook(self) -> xw.Book:
        """
        Get workbook connection - prefer already-open workbook.
        
        Returns:
            xlwings Book object
        """
        if self._wb is not None:
            return self._wb
        
        workbook_name = self.workbook_path.name
        
        # First, try to connect to already-open workbook
        try:
            for app in xw.apps:
                for book in app.books:
                    if book.name.lower() == workbook_name.lower():
                        self._wb = book
                        self._app = app
                        self._opened_by_us = False
                        print(f"  Connected to open workbook: {workbook_name}")
                        return self._wb
        except Exception:
            pass
        
        # If not open, open it ourselves
        try:
            self._wb = xw.Book(str(self.workbook_path))
            self._app = self._wb.app
            self._opened_by_us = True
            print(f"  Opened workbook: {self.workbook_path}")
            return self._wb
        except Exception as e:
            raise FileNotFoundError(f"Could not open workbook: {self.workbook_path}\n{e}")
    
    def close(self):
        """Close workbook only if we opened it."""
        if self._wb and self._opened_by_us:
            try:
                self._wb.close()
                print("  Closed workbook")
            except Exception:
                pass
        self._wb = None
        self._app = None
    
    def _get_cell(self, sheet: xw.Sheet, col: str, row: int) -> Any:
        """Get cell value from xlwings sheet."""
        return sheet.range(f"{col}{row}").value
    
    def _safe_float(self, value, default: float = 0.0) -> float:
        """Convert value to float safely."""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_int(self, value, default: int = 0) -> int:
        """Convert value to int safely."""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_str(self, value, default: str = "") -> str:
        """Convert value to string safely."""
        if value is None:
            return default
        return str(value).strip()
    
    def _safe_bool(self, value, default: bool = False) -> bool:
        """Convert value to bool, handling W/L format."""
        if value is None:
            return default
        if value in WIN_VALUES:
            return True
        return False
    
    def _format_time(self, value) -> str:
        """
        Format time value to HH:MM string.
        
        Handles:
        - datetime objects
        - Excel serial numbers (fractions of day, e.g., 0.5 = 12:00)
        - String times
        """
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%H:%M")
        if isinstance(value, str):
            return value
        
        # Handle Excel serial number (fraction of day)
        # 0.0 = midnight, 0.5 = noon, 0.75 = 6:00 PM
        try:
            serial = float(value)
            if 0 <= serial < 1:
                total_seconds = serial * 24 * 60 * 60
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                return f"{hours:02d}:{minutes:02d}"
        except (ValueError, TypeError):
            pass
        
        return str(value)
    
    def _format_date(self, value) -> str:
        """Format date value to string."""
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        return str(value)
    
    def _get_model_name(self, model_value: str) -> str:
        """Convert model number to full name."""
        model_str = self._safe_str(model_value)
        return MODEL_NAMES.get(model_str, model_str)
    
    def read_trades(self, target_date: str) -> List[Trade]:
        """Read all trades for a specific date (v2.3 format with trade_id)."""
        wb = self._get_workbook()
        sheet = wb.sheets[SHEET_BACKTEST]
        cfg = BACKTEST_TRADES
        
        trades = []
        for row in range(cfg["start_row"], cfg["start_row"] + cfg["max_rows"]):
            # v2.3: Date is now in column B
            date_val = self._get_cell(sheet, cfg["date"], row)
            if date_val is None:
                continue
            
            row_date = self._format_date(date_val)
            if row_date != target_date:
                continue
            
            model_raw = self._safe_str(self._get_cell(sheet, cfg["model"], row))
            
            trade = Trade(
                trade_id=self._safe_str(self._get_cell(sheet, cfg["trade_id"], row)),  # v2.3
                date=row_date,
                ticker=self._safe_str(self._get_cell(sheet, cfg["ticker"], row)),
                model=model_raw,
                model_name=self._get_model_name(model_raw),
                zone_type=self._safe_str(self._get_cell(sheet, cfg["zone_type"], row)),
                direction=self._safe_str(self._get_cell(sheet, cfg["direction"], row)),
                zone_high=self._safe_float(self._get_cell(sheet, cfg["zone_high"], row)),
                zone_low=self._safe_float(self._get_cell(sheet, cfg["zone_low"], row)),
                entry_price=self._safe_float(self._get_cell(sheet, cfg["entry_price"], row)),
                entry_time=self._format_time(self._get_cell(sheet, cfg["entry_time"], row)),
                stop_price=self._safe_float(self._get_cell(sheet, cfg["stop_price"], row)),
                target_3r=self._safe_float(self._get_cell(sheet, cfg["target_3r"], row)),  # v2.3
                target_calc=self._safe_float(self._get_cell(sheet, cfg["target_calc"], row)),
                target_used=self._safe_float(self._get_cell(sheet, cfg["target_used"], row)),  # v2.3
                exit_price=self._safe_float(self._get_cell(sheet, cfg["exit_price"], row)),
                exit_time=self._format_time(self._get_cell(sheet, cfg["exit_time"], row)),
                exit_reason=self._safe_str(self._get_cell(sheet, cfg["exit_reason"], row)),
                pnl_dollars=self._safe_float(self._get_cell(sheet, cfg["pnl_dollars"], row)),
                pnl_r=self._safe_float(self._get_cell(sheet, cfg["pnl_r"], row)),
                risk=self._safe_float(self._get_cell(sheet, cfg["risk"], row)),  # v2.3
                is_win=self._safe_bool(self._get_cell(sheet, cfg["is_win"], row)),
            )
            trades.append(trade)
        
        return trades
    
    def read_no_trades(self, target_date: str) -> List[NoTrade]:
        """Read all no-trade entries for a specific date."""
        wb = self._get_workbook()
        sheet = wb.sheets[SHEET_BACKTEST]
        cfg = BACKTEST_NO_TRADES
        
        no_trades = []
        for row in range(cfg["start_row"], cfg["start_row"] + cfg["max_rows"]):
            date_val = self._get_cell(sheet, cfg["date"], row)
            if date_val is None:
                continue
            
            row_date = self._format_date(date_val)
            if row_date != target_date:
                continue
            
            model_raw = self._safe_str(self._get_cell(sheet, cfg["model"], row))
            
            # Handle zone_touched which might be TRUE/FALSE or Yes/No
            touched_val = self._get_cell(sheet, cfg["zone_touched"], row)
            zone_touched = False
            if touched_val is not None:
                if isinstance(touched_val, bool):
                    zone_touched = touched_val
                elif str(touched_val).upper() in ["TRUE", "YES", "1", "Y"]:
                    zone_touched = True
            
            no_trade = NoTrade(
                date=row_date,
                ticker=self._safe_str(self._get_cell(sheet, cfg["ticker"], row)),
                model=model_raw,
                model_name=self._get_model_name(model_raw),
                zone_type=self._safe_str(self._get_cell(sheet, cfg["zone_type"], row)),
                direction=self._safe_str(self._get_cell(sheet, cfg["direction"], row)),
                zone_high=self._safe_float(self._get_cell(sheet, cfg["zone_high"], row)),
                zone_low=self._safe_float(self._get_cell(sheet, cfg["zone_low"], row)),
                reason=self._safe_str(self._get_cell(sheet, cfg["reason"], row)),
                day_high=self._safe_float(self._get_cell(sheet, cfg["day_high"], row)),
                day_low=self._safe_float(self._get_cell(sheet, cfg["day_low"], row)),
                day_open=self._safe_float(self._get_cell(sheet, cfg["day_open"], row)),
                day_close=self._safe_float(self._get_cell(sheet, cfg["day_close"], row)),
                zone_touched=zone_touched,
                bars_in_zone=self._safe_int(self._get_cell(sheet, cfg["bars_in_zone"], row)),
            )
            no_trades.append(no_trade)
        
        return no_trades
    
    def read_zones(self) -> Dict[str, Dict[str, ZoneData]]:
        """Read primary and secondary zones from analysis sheet (V1.1 with Tier)."""
        wb = self._get_workbook()
        sheet = wb.sheets[SHEET_ANALYSIS]
        
        zones = {}
        
        # Read primary zones (V1.1: B31:L40)
        cfg = ANALYSIS_PRIMARY
        for row in range(cfg["start_row"], cfg["end_row"] + 1):
            ticker = self._safe_str(self._get_cell(sheet, cfg["ticker"], row))
            if not ticker:
                continue
            
            if ticker not in zones:
                zones[ticker] = {}
            
            zones[ticker]["primary"] = ZoneData(
                ticker=ticker,
                direction=self._safe_str(self._get_cell(sheet, cfg["direction"], row)),
                zone_high=self._safe_float(self._get_cell(sheet, cfg["zone_high"], row)),
                zone_low=self._safe_float(self._get_cell(sheet, cfg["zone_low"], row)),
                hvn_poc=self._safe_float(self._get_cell(sheet, cfg["hvn_poc"], row)),
                tier=self._safe_str(self._get_cell(sheet, cfg["tier"], row)),  # V1.1
                target=self._safe_float(self._get_cell(sheet, cfg["target"], row)),
                rr_ratio=self._safe_float(self._get_cell(sheet, cfg["rr_ratio"], row)),
            )
        
        # Read secondary zones (V1.1: N31:X40)
        cfg = ANALYSIS_SECONDARY
        for row in range(cfg["start_row"], cfg["end_row"] + 1):
            ticker = self._safe_str(self._get_cell(sheet, cfg["ticker"], row))
            if not ticker:
                continue
            
            if ticker not in zones:
                zones[ticker] = {}
            
            zones[ticker]["secondary"] = ZoneData(
                ticker=ticker,
                direction=self._safe_str(self._get_cell(sheet, cfg["direction"], row)),
                zone_high=self._safe_float(self._get_cell(sheet, cfg["zone_high"], row)),
                zone_low=self._safe_float(self._get_cell(sheet, cfg["zone_low"], row)),
                hvn_poc=self._safe_float(self._get_cell(sheet, cfg["hvn_poc"], row)),
                tier=self._safe_str(self._get_cell(sheet, cfg["tier"], row)),  # V1.1
                target=self._safe_float(self._get_cell(sheet, cfg["target"], row)),
                rr_ratio=self._safe_float(self._get_cell(sheet, cfg["rr_ratio"], row)),
            )
        
        return zones
    
    def read_market_structure(self) -> Dict[str, MarketStructure]:
        """Read market structure for all tickers from market_overview."""
        wb = self._get_workbook()
        sheet = wb.sheets[SHEET_MARKET]
        cfg = MARKET_OVERVIEW
        
        structures = {}
        
        for row in range(cfg["user_start_row"], cfg["user_end_row"] + 1):
            ticker = self._safe_str(self._get_cell(sheet, cfg["ticker"], row))
            if not ticker:
                continue
            
            structures[ticker] = MarketStructure(
                ticker=ticker,
                composite=self._safe_str(self._get_cell(sheet, cfg["composite"], row)),
                d1_dir=self._safe_str(self._get_cell(sheet, cfg["d1_dir"], row)),
                h4_dir=self._safe_str(self._get_cell(sheet, cfg["h4_dir"], row)),
                h1_dir=self._safe_str(self._get_cell(sheet, cfg["h1_dir"], row)),
                m15_dir=self._safe_str(self._get_cell(sheet, cfg["m15_dir"], row)),
            )
        
        return structures
    
    def get_spy_direction(self) -> str:
        """Get SPY composite direction from market overview."""
        structures = self.read_market_structure()
        if "SPY" in structures:
            return structures["SPY"].composite
        return "Unknown"
    
    def get_tickers_analyzed(self) -> List[str]:
        """Get list of tickers from zones."""
        zones = self.read_zones()
        return sorted(zones.keys())
    
    def get_trading_date(self) -> Optional[str]:
        """
        Extract trading date from ticker_id in the Analysis sheet.
        
        Ticker ID format: {TICKER}_{MMDDYY} e.g., 'AMD_121225' → '2025-12-12'
        
        Returns:
            Date string in YYYY-MM-DD format, or None if not found
        """
        wb = self._get_workbook()
        sheet = wb.sheets[SHEET_ANALYSIS]
        cfg = ANALYSIS_PRIMARY
        
        # Look for first valid ticker_id
        for row in range(cfg["start_row"], cfg["end_row"] + 1):
            ticker_id = self._safe_str(self._get_cell(sheet, cfg["ticker_id"], row))
            
            if ticker_id and '_' in ticker_id:
                try:
                    # Extract date portion after underscore
                    date_part = ticker_id.split('_')[-1]
                    
                    if len(date_part) == 6:
                        # Format: MMDDYY
                        month = int(date_part[0:2])
                        day = int(date_part[2:4])
                        year = int(date_part[4:6])
                        
                        # Convert 2-digit year to 4-digit (assumes 20xx)
                        year = 2000 + year
                        
                        return f"{year}-{month:02d}-{day:02d}"
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _sheet_exists(self, sheet_name: str) -> bool:
        """Check if a worksheet exists in the workbook."""
        wb = self._get_workbook()
        return sheet_name in [s.name.lower() for s in wb.sheets]
    
    def read_entry_events(self, target_date: str = None) -> Dict[str, EntryEvent]:
        """
        Read entry enrichment data from entry_events sheet.
        
        Args:
            target_date: Optional date filter (reads all if None)
            
        Returns:
            Dict mapping trade_id to EntryEvent
        """
        if not self._sheet_exists(SHEET_ENTRY_EVENTS):
            print(f"  Warning: '{SHEET_ENTRY_EVENTS}' worksheet not found")
            return {}
        
        wb = self._get_workbook()
        sheet = wb.sheets[SHEET_ENTRY_EVENTS]
        cfg = ENTRY_EVENTS
        
        events = {}
        for row in range(cfg["start_row"], cfg["start_row"] + cfg["max_rows"]):
            trade_id = self._safe_str(self._get_cell(sheet, cfg["trade_id"], row))
            if not trade_id:
                continue
            
            # Optional date filter (extract date from trade_id: ticker_MMDDYY_model_HHMM)
            if target_date:
                try:
                    parts = trade_id.split('_')
                    if len(parts) >= 2:
                        date_part = parts[1]  # MMDDYY
                        if len(date_part) == 6:
                            month = int(date_part[0:2])
                            day = int(date_part[2:4])
                            year = 2000 + int(date_part[4:6])
                            trade_date = f"{year}-{month:02d}-{day:02d}"
                            if trade_date != target_date:
                                continue
                except (ValueError, IndexError):
                    pass
            
            events[trade_id] = EntryEvent(
                trade_id=trade_id,
                # Price Position
                entry_vwap=self._safe_float(self._get_cell(sheet, cfg["entry_vwap"], row)),
                entry_vs_vwap=self._safe_str(self._get_cell(sheet, cfg["entry_vs_vwap"], row)),
                entry_sma9=self._safe_float(self._get_cell(sheet, cfg["entry_sma9"], row)),
                entry_vs_sma9=self._safe_str(self._get_cell(sheet, cfg["entry_vs_sma9"], row)),
                entry_sma21=self._safe_float(self._get_cell(sheet, cfg["entry_sma21"], row)),
                entry_vs_sma21=self._safe_str(self._get_cell(sheet, cfg["entry_vs_sma21"], row)),
                sma9_vs_sma21=self._safe_str(self._get_cell(sheet, cfg["sma9_vs_sma21"], row)),
                # Volume Analysis
                entry_volume=self._safe_int(self._get_cell(sheet, cfg["entry_volume"], row)),
                avg_volume_5=self._safe_float(self._get_cell(sheet, cfg["avg_volume_5"], row)),
                volume_delta_pct=self._safe_float(self._get_cell(sheet, cfg["volume_delta_pct"], row)),
                volume_trend=self._safe_str(self._get_cell(sheet, cfg["volume_trend"], row)),
                relative_volume=self._safe_float(self._get_cell(sheet, cfg["relative_volume"], row)),
                prior_bar_qual=self._safe_str(self._get_cell(sheet, cfg["prior_bar_qual"], row)),
                vol_delta_class=self._safe_str(self._get_cell(sheet, cfg["vol_delta_class"], row)),
                vol_delta_value=self._safe_int(self._get_cell(sheet, cfg["vol_delta_value"], row)),
                # Multi-Timeframe Structure
                m5_structure=self._safe_str(self._get_cell(sheet, cfg["m5_structure"], row)),
                m15_structure=self._safe_str(self._get_cell(sheet, cfg["m15_structure"], row)),
                h1_structure=self._safe_str(self._get_cell(sheet, cfg["h1_structure"], row)),
                h4_structure=self._safe_str(self._get_cell(sheet, cfg["h4_structure"], row)),
                structure_align=self._safe_int(self._get_cell(sheet, cfg["structure_align"], row)),
                dominant_struct=self._safe_str(self._get_cell(sheet, cfg["dominant_struct"], row)),
                m5_last_break=self._safe_str(self._get_cell(sheet, cfg["m5_last_break"], row)),
                m15_last_break=self._safe_str(self._get_cell(sheet, cfg["m15_last_break"], row)),
                # Health Score
                health_score=self._safe_int(self._get_cell(sheet, cfg["health_score"], row)),
                health_max=self._safe_int(self._get_cell(sheet, cfg["health_max"], row), default=7),
                health_pct=self._safe_float(self._get_cell(sheet, cfg["health_pct"], row)),
                health_label=self._safe_str(self._get_cell(sheet, cfg["health_label"], row)),
                # Alignment Flags
                vwap_aligned=self._safe_bool(self._get_cell(sheet, cfg["vwap_aligned"], row)),
                trend_aligned=self._safe_bool(self._get_cell(sheet, cfg["trend_aligned"], row)),
                structure_aligned=self._safe_bool(self._get_cell(sheet, cfg["structure_aligned"], row)),
                # Metadata
                status=self._safe_str(self._get_cell(sheet, cfg["status"], row)),
                error=self._safe_str(self._get_cell(sheet, cfg["error"], row)),
            )
        
        return events
    
    def read_exit_events(self, target_date: str = None) -> Dict[str, List[ExitEvent]]:
        """
        Read exit event timeline from exit_events sheet.
        
        Args:
            target_date: Optional date filter (reads all if None)
            
        Returns:
            Dict mapping trade_id to list of ExitEvents (multiple events per trade)
        """
        if not self._sheet_exists(SHEET_EXIT_EVENTS):
            print(f"  Warning: '{SHEET_EXIT_EVENTS}' worksheet not found")
            return {}
        
        wb = self._get_workbook()
        sheet = wb.sheets[SHEET_EXIT_EVENTS]
        cfg = EXIT_EVENTS
        
        events = {}
        for row in range(cfg["start_row"], cfg["start_row"] + cfg["max_rows"]):
            trade_id = self._safe_str(self._get_cell(sheet, cfg["trade_id"], row))
            if not trade_id:
                continue
            
            # Optional date filter
            if target_date:
                try:
                    parts = trade_id.split('_')
                    if len(parts) >= 2:
                        date_part = parts[1]
                        if len(date_part) == 6:
                            month = int(date_part[0:2])
                            day = int(date_part[2:4])
                            year = 2000 + int(date_part[4:6])
                            trade_date = f"{year}-{month:02d}-{day:02d}"
                            if trade_date != target_date:
                                continue
                except (ValueError, IndexError):
                    pass
            
            event = ExitEvent(
                trade_id=trade_id,
                # Event Timing
                event_seq=self._safe_int(self._get_cell(sheet, cfg["event_seq"], row)),
                event_time=self._format_time(self._get_cell(sheet, cfg["event_time"], row)),
                bars_from_entry=self._safe_int(self._get_cell(sheet, cfg["bars_from_entry"], row)),
                bars_from_mfe=self._safe_int(self._get_cell(sheet, cfg["bars_from_mfe"], row)),
                # Event Details
                event_type=self._safe_str(self._get_cell(sheet, cfg["event_type"], row)),
                from_state=self._safe_str(self._get_cell(sheet, cfg["from_state"], row)),
                to_state=self._safe_str(self._get_cell(sheet, cfg["to_state"], row)),
                # Position at Event
                price_at_event=self._safe_float(self._get_cell(sheet, cfg["price_at_event"], row)),
                r_at_event=self._safe_float(self._get_cell(sheet, cfg["r_at_event"], row)),
                health_score=self._safe_int(self._get_cell(sheet, cfg["health_score"], row)),
                health_delta=self._safe_int(self._get_cell(sheet, cfg["health_delta"], row)),
                # Indicator Values
                vwap=self._safe_float(self._get_cell(sheet, cfg["vwap"], row)),
                sma9=self._safe_float(self._get_cell(sheet, cfg["sma9"], row)),
                sma21=self._safe_float(self._get_cell(sheet, cfg["sma21"], row)),
                volume=self._safe_int(self._get_cell(sheet, cfg["volume"], row)),
                swing_high=self._safe_float(self._get_cell(sheet, cfg["swing_high"], row)),
                swing_low=self._safe_float(self._get_cell(sheet, cfg["swing_low"], row)),
            )
            
            # Group by trade_id (multiple events per trade)
            if trade_id not in events:
                events[trade_id] = []
            events[trade_id].append(event)
        
        # Sort events by event_seq within each trade
        for trade_id in events:
            events[trade_id].sort(key=lambda e: e.event_seq)
        
        return events
    
    def read_optimal_trades(self, target_date: str = None) -> Dict[str, OptimalTrade]:
        """
        Read optimal exit analysis from optimal_trade sheet.
        
        Args:
            target_date: Optional date filter (reads all if None)
            
        Returns:
            Dict mapping trade_id to OptimalTrade
        """
        if not self._sheet_exists(SHEET_OPTIMAL_TRADE):
            print(f"  Warning: '{SHEET_OPTIMAL_TRADE}' worksheet not found")
            return {}
        
        wb = self._get_workbook()
        sheet = wb.sheets[SHEET_OPTIMAL_TRADE]
        cfg = OPTIMAL_TRADE
        
        trades = {}
        for row in range(cfg["start_row"], cfg["start_row"] + cfg["max_rows"]):
            trade_id = self._safe_str(self._get_cell(sheet, cfg["trade_id"], row))
            if not trade_id:
                continue
            
            # Optional date filter
            if target_date:
                try:
                    parts = trade_id.split('_')
                    if len(parts) >= 2:
                        date_part = parts[1]
                        if len(date_part) == 6:
                            month = int(date_part[0:2])
                            day = int(date_part[2:4])
                            year = 2000 + int(date_part[4:6])
                            trade_date = f"{year}-{month:02d}-{day:02d}"
                            if trade_date != target_date:
                                continue
                except (ValueError, IndexError):
                    pass
            
            trades[trade_id] = OptimalTrade(
                trade_id=trade_id,
                optimal_exit_price=self._safe_float(self._get_cell(sheet, cfg["optimal_exit_price"], row)),
                optimal_exit_time=self._format_time(self._get_cell(sheet, cfg["optimal_exit_time"], row)),
                optimal_exit_reason=self._safe_str(self._get_cell(sheet, cfg["optimal_exit_reason"], row)),
                optimal_pnl_r=self._safe_float(self._get_cell(sheet, cfg["optimal_pnl_r"], row)),
                mfe_price=self._safe_float(self._get_cell(sheet, cfg["mfe_price"], row)),
                mfe_time=self._format_time(self._get_cell(sheet, cfg["mfe_time"], row)),
                mfe_r=self._safe_float(self._get_cell(sheet, cfg["mfe_r"], row)),
                mae_price=self._safe_float(self._get_cell(sheet, cfg["mae_price"], row)),
                mae_time=self._format_time(self._get_cell(sheet, cfg["mae_time"], row)),
                mae_r=self._safe_float(self._get_cell(sheet, cfg["mae_r"], row)),
                capture_efficiency=self._safe_float(self._get_cell(sheet, cfg["capture_efficiency"], row)),
                notes=self._safe_str(self._get_cell(sheet, cfg["notes"], row)),
            )
        
        return trades


def main():
    """Test the Excel reader."""
    from datetime import date
    
    print("=" * 60)
    print("Testing Excel Reader (xlwings V1.1 - with Tier)")
    print("=" * 60)
    print(f"Workbook: {EXCEL_WORKBOOK}")
    
    reader = ExcelReader()
    
    try:
        # Test reading zones
        print("\n--- Zones (V1.1 with Tier) ---")
        zones = reader.read_zones()
        if zones:
            for ticker, zone_data in zones.items():
                print(f"\n{ticker}:")
                if "primary" in zone_data:
                    p = zone_data["primary"]
                    print(f"  Primary: {p.zone_high:.2f} - {p.zone_low:.2f} | POC: {p.hvn_poc:.2f} | Tier: {p.tier} | Target: {p.target:.2f} | R:R: {p.rr_ratio:.2f}")
                if "secondary" in zone_data:
                    s = zone_data["secondary"]
                    print(f"  Secondary: {s.zone_high:.2f} - {s.zone_low:.2f} | POC: {s.hvn_poc:.2f} | Tier: {s.tier} | Target: {s.target:.2f} | R:R: {s.rr_ratio:.2f}")
        else:
            print("  No zones found - is the Analysis sheet populated?")
        
        # Test market structure
        print("\n--- Market Structure ---")
        structures = reader.read_market_structure()
        for ticker, ms in structures.items():
            print(f"  {ticker}: {ms.composite} (D1:{ms.d1_dir} H4:{ms.h4_dir} H1:{ms.h1_dir} M15:{ms.m15_dir})")
        
        # Test SPY direction
        print(f"\nSPY Direction: {reader.get_spy_direction()}")
        
        # Test trades for today
        today = date.today().strftime("%Y-%m-%d")
        print(f"\n--- Trades for {today} ---")
        trades = reader.read_trades(today)
        if trades:
            for t in trades:
                win_str = "W" if t.is_win else "L"
                print(f"  {t.trade_id}: {t.model_name} {t.direction} → {t.pnl_r:+.2f}R [{win_str}]")
        else:
            print("  No trades found for today")
        
        print(f"\nTotal trades: {len(trades)}")
        print(f"Total tickers with zones: {len(zones)}")
        
    finally:
        reader.close()
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
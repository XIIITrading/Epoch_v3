"""
Epoch Backtest Journal - Indicator Edge Calculator
Analyzes indicator effectiveness by model type and direction.

For continuation models (EPCH1, EPCH3): Expects momentum-aligned indicators
For reversal models (EPCH2, EPCH4): Expects exhaustion/turn signals

Segments trades into 8 groups: Model (EPCH1-4) × Direction (LONG/SHORT)
Calculates win rate for each indicator state within each segment.
"""

import xlwings as xw
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
import sys

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import EpochDatabase


# =============================================================================
# CONFIGURATION
# =============================================================================

# Model classifications
CONTINUATION_MODELS = ["EPCH1", "EPCH3"]
REVERSAL_MODELS = ["EPCH2", "EPCH4"]
ALL_MODELS = ["EPCH1", "EPCH2", "EPCH3", "EPCH4"]
DIRECTIONS = ["LONG", "SHORT"]

# Indicator definitions with possible states
INDICATORS = {
    "entry_vs_vwap": ["ABOVE", "BELOW"],
    "entry_vs_sma9": ["ABOVE", "BELOW"],
    "entry_vs_sma21": ["ABOVE", "BELOW"],
    "sma9_vs_sma21": ["BULLISH", "BEARISH"],
    "volume_trend": ["INCREASING", "DECREASING", "FLAT"],
    "prior_bar_qual": ["FAVORABLE", "NEUTRAL", "UNFAVORABLE"],
    "vol_delta_class": ["BULL", "BEAR", "NEUTRAL"],
    "m5_structure": ["BULL", "BEAR", "NEUTRAL"],
    "m15_structure": ["BULL", "BEAR", "NEUTRAL"],
    "h1_structure": ["BULL", "BEAR", "NEUTRAL"],
    "h4_structure": ["BULL", "BEAR", "NEUTRAL"],
    "dominant_structure": ["BULL", "BEAR"],
}

# Display names for indicators
INDICATOR_DISPLAY = {
    "entry_vs_vwap": "VWAP Position",
    "entry_vs_sma9": "vs SMA9",
    "entry_vs_sma21": "vs SMA21",
    "sma9_vs_sma21": "SMA Stack",
    "volume_trend": "Volume Trend",
    "prior_bar_qual": "Prior Bar",
    "vol_delta_class": "Vol Delta",
    "m5_structure": "M5 Struct",
    "m15_structure": "M15 Struct",
    "h1_structure": "H1 Struct",
    "h4_structure": "H4 Struct",
    "dominant_structure": "Dom Struct",
}

# 3-letter codes for compact display
INDICATOR_CODE = {
    "entry_vs_vwap": "VWP",
    "entry_vs_sma9": "SM9",
    "entry_vs_sma21": "S21",
    "sma9_vs_sma21": "STK",
    "volume_trend": "VOL",
    "prior_bar_qual": "PBQ",
    "vol_delta_class": "VDC",
    "m5_structure": "M5S",
    "m15_structure": "M15",
    "h1_structure": "H1S",
    "h4_structure": "H4S",
    "dominant_structure": "DOM",
}

STATE_CODE = {
    "ABOVE": "ABV",
    "BELOW": "BLW",
    "BULLISH": "BUL",
    "BEARISH": "BER",
    "BULL": "BUL",
    "BEAR": "BER",
    "NEUTRAL": "NEU",
    "INCREASING": "INC",
    "DECREASING": "DEC",
    "FLAT": "FLT",
    "FAVORABLE": "FAV",
    "UNFAVORABLE": "UNF",
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class IndicatorStateStats:
    """Statistics for a single indicator state within a segment."""
    indicator: str
    state: str
    trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    avg_pnl_r: float = 0.0
    total_pnl_r: float = 0.0


@dataclass
class SegmentStats:
    """Statistics for a model-direction segment."""
    model: str
    direction: str
    model_type: str  # "CONTINUATION" or "REVERSAL"
    trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    avg_pnl_r: float = 0.0
    indicator_stats: Dict[str, Dict[str, IndicatorStateStats]] = field(default_factory=dict)
    # indicator_stats[indicator_name][state] = IndicatorStateStats


@dataclass
class IndicatorEdge:
    """Edge calculation for an indicator within a segment."""
    indicator: str
    display_name: str
    code: str  # 3-letter indicator code
    best_state: str
    best_state_code: str  # 3-letter state code
    best_win_rate: float
    worst_state: str
    worst_win_rate: float
    edge: float  # best_win_rate - worst_win_rate
    best_trades: int
    best_avg_pnl_r: float


@dataclass
class IndicatorEdgeData:
    """Complete analysis results."""
    segments: Dict[Tuple[str, str], SegmentStats] = field(default_factory=dict)
    # Key: (model, direction), e.g., ("EPCH1", "LONG")
    
    # Pre-calculated edges for easy access
    segment_edges: Dict[Tuple[str, str], List[IndicatorEdge]] = field(default_factory=dict)
    # Key: (model, direction), Value: List of IndicatorEdge sorted by edge desc


# =============================================================================
# CALCULATOR CLASS
# =============================================================================

class IndicatorEdgeCalculator:
    """
    Calculates indicator edge statistics by model type and direction.
    
    Outputs to bt_journal.xlsx analysis sheet in range H9:AF40.
    
    Layout:
        H9:O9     - Segment headers (EPCH1-L, EPCH1-S, ... EPCH4-S)
        H10:O10   - Baseline win rates per segment
        H11:O11   - Trade counts per segment
        
        H13:O25   - Indicator Edge Matrix (win rates by indicator state)
        
        H27:O40   - Top 5 Indicators per Segment (ranked by edge)
        
        Q9:AF25   - Optimal Entry Profiles per model type
    """
    
    # Excel file path
    EXCEL_PATH = Path(r"C:\XIIITradingSystems\Epoch\02_zone_system\12_bt_journal\bt_journal.xlsx")
    
    # Sheet name
    SHEET_NAME = "analysis"
    
    # Starting positions
    START_ROW = 9
    START_COL = "H"  # Column 8
    
    # Cell references for key outputs
    CELLS = {
        # Headers and segment summary (row 9-12)
        "segment_header_row": 9,
        "segment_header_start": "I",
        "baseline_wr_row": 10,
        "trade_count_row": 11,
        "model_type_row": 12,
        
        # Indicator matrix (rows 14-26)
        "matrix_header_row": 13,
        "matrix_start_row": 14,
        "matrix_indicator_col": "H",
        "matrix_data_start": "I",
        
        # Top indicators section (rows 28-40)
        "top_header_row": 28,
        "top_start_row": 29,
        
        # Optimal profiles section (columns R onwards)
        "profile_start_col": "R",
        "profile_start_row": 9,
    }
    
    def __init__(self, db: EpochDatabase = None, workbook: xw.Book = None):
        """
        Initialize calculator.
        
        Args:
            db: Database connection. Creates new if not provided.
            workbook: xlwings Book object. If None, will connect to the file.
        """
        self.db = db or EpochDatabase()
        self._external_wb = workbook is not None
        self._wb = workbook
    
    def _connect_excel(self) -> xw.Book:
        """Connect to the Excel workbook."""
        if self._wb is None:
            self._wb = xw.Book(str(self.EXCEL_PATH))
        return self._wb
    
    def calculate(self) -> IndicatorEdgeData:
        """
        Pull trades from database and calculate indicator edge statistics.
        
        Returns:
            IndicatorEdgeData object containing all calculated statistics.
        """
        # Get trades with entry event data
        trades = self.db.get_trades_with_entry_events()
        
        if not trades:
            return IndicatorEdgeData()
        
        # Initialize result container
        result = IndicatorEdgeData()
        
        # Initialize segments
        for model in ALL_MODELS:
            for direction in DIRECTIONS:
                model_type = "CONTINUATION" if model in CONTINUATION_MODELS else "REVERSAL"
                result.segments[(model, direction)] = SegmentStats(
                    model=model,
                    direction=direction,
                    model_type=model_type,
                    indicator_stats={ind: {} for ind in INDICATORS.keys()}
                )
        
        # Process each trade
        for trade in trades:
            model = trade.get("model")
            direction = (trade.get("direction") or "").upper()
            
            if model not in ALL_MODELS or direction not in DIRECTIONS:
                continue
            
            segment = result.segments[(model, direction)]
            segment.trades += 1
            
            is_winner = trade.get("is_winner", False)
            pnl_r = float(trade.get("pnl_r", 0) or 0)
            
            if is_winner:
                segment.wins += 1
            else:
                segment.losses += 1
            
            # Process each indicator
            for indicator, states in INDICATORS.items():
                value = trade.get(indicator)
                if value is None:
                    continue
                
                value_upper = str(value).upper()
                
                # Initialize state stats if needed
                if value_upper not in segment.indicator_stats[indicator]:
                    segment.indicator_stats[indicator][value_upper] = IndicatorStateStats(
                        indicator=indicator,
                        state=value_upper
                    )
                
                state_stats = segment.indicator_stats[indicator][value_upper]
                state_stats.trades += 1
                state_stats.total_pnl_r += pnl_r
                
                if is_winner:
                    state_stats.wins += 1
                else:
                    state_stats.losses += 1
        
        # Calculate derived statistics
        for key, segment in result.segments.items():
            # Segment win rate
            if segment.trades > 0:
                segment.win_rate = segment.wins / segment.trades
            
            # Indicator state win rates
            for indicator, states_dict in segment.indicator_stats.items():
                for state, stats in states_dict.items():
                    if stats.trades > 0:
                        stats.win_rate = stats.wins / stats.trades
                        stats.avg_pnl_r = stats.total_pnl_r / stats.trades
            
            # Calculate edges for this segment
            result.segment_edges[key] = self._calculate_segment_edges(segment)
        
        return result
    
    def _calculate_segment_edges(self, segment: SegmentStats) -> List[IndicatorEdge]:
        """Calculate indicator edges for a segment, sorted by edge descending."""
        edges = []
        
        for indicator, states_dict in segment.indicator_stats.items():
            if not states_dict:
                continue
            
            # Find best and worst states
            valid_states = [(s, st) for s, st in states_dict.items() if st.trades >= 3]
            
            if len(valid_states) < 2:
                continue
            
            best = max(valid_states, key=lambda x: x[1].win_rate)
            worst = min(valid_states, key=lambda x: x[1].win_rate)
            
            edge = best[1].win_rate - worst[1].win_rate
            
            edges.append(IndicatorEdge(
                indicator=indicator,
                display_name=INDICATOR_DISPLAY.get(indicator, indicator),
                code=INDICATOR_CODE.get(indicator, indicator[:3].upper()),
                best_state=best[0],
                best_state_code=STATE_CODE.get(best[0], best[0][:3].upper()),
                best_win_rate=best[1].win_rate,
                worst_state=worst[0],
                worst_win_rate=worst[1].win_rate,
                edge=edge,
                best_trades=best[1].trades,
                best_avg_pnl_r=best[1].avg_pnl_r
            ))
        
        # Sort by edge descending
        edges.sort(key=lambda x: x.edge, reverse=True)
        return edges
    
    def write_to_excel(self, data: IndicatorEdgeData) -> None:
        """
        Write indicator edge statistics to Excel cells.
        Only writes DATA - headers are manually formatted in Excel.
        
        Args:
            data: IndicatorEdgeData object containing statistics to write.
        """
        wb = self._connect_excel()
        ws = wb.sheets[self.SHEET_NAME]
        
        # Clear only DATA ranges (preserve headers)
        # Section 1: Segment data (I10:P12)
        ws.range("I10:P12").clear_contents()
        # Section 2: Win rate matrix data (I16:P27)
        ws.range("I16:P27").clear_contents()
        # Section 3: Top 5 data (I31:P35)
        ws.range("I31:P35").clear_contents()
        # Section 4: Optimal profiles data (new locations)
        ws.range("H40:J44").clear_contents()   # CONTINUATION LONGS
        ws.range("M40:O44").clear_contents()   # CONTINUATION SHORTS
        ws.range("H48:J52").clear_contents()   # REVERSAL LONGS
        ws.range("M48:O52").clear_contents()   # REVERSAL SHORTS
        
        # Build segment column mapping
        col = 9  # Column I
        segment_cols = {}
        for model in ALL_MODELS:
            for direction in DIRECTIONS:
                segment_key = (model, direction)
                segment_cols[segment_key] = col
                col += 1
        
        # =====================================================================
        # SECTION 1: Segment Summary DATA (I10:P12)
        # Headers in row 9 and column H are pre-formatted in Excel
        # =====================================================================
        
        for segment_key, segment in data.segments.items():
            col = segment_cols[segment_key]
            ws.range((10, col)).value = f"{segment.win_rate*100:.0f}%"
            ws.range((11, col)).value = segment.trades
            ws.range((12, col)).value = "CONT" if segment.model_type == "CONTINUATION" else "REV"
        
        # =====================================================================
        # SECTION 2: Indicator Win Rate Matrix DATA (I16:P27)
        # Headers in rows 14-15 and column H are pre-formatted in Excel
        # =====================================================================
        
        row = 16
        
        # Key indicators (12 rows: 16-27)
        key_indicators = [
            ("entry_vs_vwap", "ABOVE"),
            ("entry_vs_vwap", "BELOW"),
            ("sma9_vs_sma21", "BULLISH"),
            ("sma9_vs_sma21", "BEARISH"),
            ("vol_delta_class", "BULL"),
            ("vol_delta_class", "BEAR"),
            ("prior_bar_qual", "FAVORABLE"),
            ("prior_bar_qual", "UNFAVORABLE"),
            ("m5_structure", "BULL"),
            ("m5_structure", "BEAR"),
            ("h1_structure", "BULL"),
            ("h1_structure", "BEAR"),
        ]
        
        for indicator, state in key_indicators:
            for segment_key, col in segment_cols.items():
                segment = data.segments[segment_key]
                state_stats = segment.indicator_stats.get(indicator, {}).get(state)
                
                # Minimum 2 trades to show win rate
                if state_stats and state_stats.trades >= 2:
                    ws.range((row, col)).value = f"{state_stats.win_rate*100:.0f}%"
                else:
                    ws.range((row, col)).value = "-"
            
            row += 1
        
        # =====================================================================
        # SECTION 3: Top 5 Indicators DATA (I31:P35)
        # Headers in rows 29-30 and column H are pre-formatted in Excel
        # Format: "VWP:ABV +24%" (code:state_code +edge%)
        # =====================================================================
        
        for rank in range(1, 6):
            row = 30 + rank
            
            for segment_key, col in segment_cols.items():
                edges = data.segment_edges.get(segment_key, [])
                if rank <= len(edges):
                    edge = edges[rank - 1]
                    # Compact format: CODE:STATE +XX%
                    cell_value = f"{edge.code}:{edge.best_state_code} +{edge.edge*100:.0f}%"
                    ws.range((row, col)).value = cell_value
        
        # =====================================================================
        # SECTION 4: Optimal Entry Profiles DATA
        # Headers are pre-formatted in Excel
        # CONTINUATION: row 40-44, REVERSAL: row 48-52
        # LONGS at H-J (col 8-10), SHORTS at M-O (col 13-15)
        # =====================================================================
        
        # Profile definitions: (data_start_row, base_col, models, direction)
        # Column H=8, Column M=13
        profiles = [
            (40, 8, ["EPCH1", "EPCH3"], "LONG"),    # CONTINUATION LONGS (H40:J44)
            (40, 13, ["EPCH1", "EPCH3"], "SHORT"),  # CONTINUATION SHORTS (M40:O44)
            (48, 8, ["EPCH2", "EPCH4"], "LONG"),    # REVERSAL LONGS (H48:J52)
            (48, 13, ["EPCH2", "EPCH4"], "SHORT"),  # REVERSAL SHORTS (M48:O52)
        ]
        
        for data_start_row, base_col, models, direction in profiles:
            # Aggregate edges across the models in this group
            aggregated_edges = {}
            for model in models:
                segment_key = (model, direction)
                for edge in data.segment_edges.get(segment_key, []):
                    key = (edge.indicator, edge.best_state)
                    if key not in aggregated_edges:
                        aggregated_edges[key] = {
                            "code": edge.code,
                            "state_code": edge.best_state_code,
                            "edges": []
                        }
                    aggregated_edges[key]["edges"].append(edge.edge)
            
            # Calculate average edge and sort
            sorted_edges = []
            for key, info in aggregated_edges.items():
                avg_edge = sum(info["edges"]) / len(info["edges"])
                sorted_edges.append((info["code"], info["state_code"], avg_edge))
            
            sorted_edges.sort(key=lambda x: x[2], reverse=True)
            
            # Write top 5 data rows
            for i, (code, state_code, avg_edge) in enumerate(sorted_edges[:5]):
                r = data_start_row + i
                ws.range((r, base_col)).value = code
                ws.range((r, base_col + 1)).value = state_code
                ws.range((r, base_col + 2)).value = f"{avg_edge*100:.0f}%"
    
    def print_results(self, data: IndicatorEdgeData, verbose: bool = True):
        """
        Print indicator edge statistics to console.
        
        Args:
            data: IndicatorEdgeData object.
            verbose: If True, print header and formatting.
        """
        if verbose:
            print()
            print("=" * 80)
            print("INDICATOR EDGE ANALYSIS")
            print("=" * 80)
            print()
        
        # Segment summary
        print("SEGMENT SUMMARY:")
        print("-" * 80)
        print(f"{'Segment':<12} {'Type':<12} {'Trades':>8} {'Wins':>8} {'Win%':>8}")
        print("-" * 80)
        
        for (model, direction), segment in sorted(data.segments.items()):
            short_dir = "L" if direction == "LONG" else "S"
            segment_name = f"{model}-{short_dir}"
            print(
                f"{segment_name:<12} "
                f"{segment.model_type:<12} "
                f"{segment.trades:>8} "
                f"{segment.wins:>8} "
                f"{segment.win_rate:>8.1%}"
            )
        
        print()
        
        # Top indicators per segment type
        if verbose:
            print("TOP INDICATORS BY EDGE:")
            print("-" * 80)
            
            for (model, direction), edges in sorted(data.segment_edges.items()):
                short_dir = "L" if direction == "LONG" else "S"
                segment_name = f"{model}-{short_dir}"
                print(f"\n{segment_name}:")
                
                for i, edge in enumerate(edges[:5], 1):
                    print(
                        f"  {i}. {edge.display_name}={edge.best_state} "
                        f"(WR: {edge.best_win_rate:.0%}, Edge: +{edge.edge*100:.0f}%, "
                        f"n={edge.best_trades})"
                    )
        
        if verbose:
            print()
            print("=" * 80)
            print()
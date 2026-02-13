"""
================================================================================
EPOCH TRADING SYSTEM - BACKTEST REPORT GENERATOR
================================================================================
Generates a comprehensive .txt report for Claude AI analysis after backtest
execution. Includes raw data and summaries from all modules.

Output: results/ subdirectory (relative to this script)

Usage:
    Called automatically by bt_runner.py after all modules complete.
================================================================================
"""

import xlwings as xw
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


# ============================================================================
# CONFIGURATION
# ============================================================================

RESULTS_DIR = Path(__file__).parent / "results"
WORKBOOK_NAME = "epoch_v1.xlsm"

# Column definitions for each worksheet
BACKTEST_HEADERS = [
    "trade_id", "date", "ticker", "model", "zone_type", "direction",
    "zone_high", "zone_low", "entry_price", "entry_time", "stop_price",
    "target_3r", "target_calc", "target_used", "exit_price", "exit_time",
    "exit_reason", "pnl_dollars", "pnl_r", "risk", "win"
]

ENTRY_EVENTS_HEADERS = [
    "trade_id", "ticker", "date", "direction", "entry_time", "entry_price",
    "stop_price", "risk_dollars", "h4_structure", "h4_trend_strength",
    "h1_structure", "h1_trend_strength", "m15_structure", "m15_trend_strength",
    "m5_structure", "m5_trend_strength", "vol_roc", "vol_roc_signal",
    "vol_delta", "vol_delta_signal", "cvd_direction", "cvd_signal",
    "sma9", "sma21", "sma_alignment", "sma_spread", "sma_spread_momentum",
    "vwap", "vwap_position", "entry_health", "health_label",
    "htf_aligned", "mtf_aligned", "vol_aligned", "ind_aligned",
    "h4_score", "h1_score", "m15_score", "m5_score", "vol_score",
    "cvd_score", "sma_score", "vwap_score", "processing_status"
]

EXIT_EVENTS_HEADERS = [
    "trade_id", "event_seq", "event_time", "bars_from_entry", "bars_from_mfe",
    "event_type", "from_state", "to_state", "price_at_event", "r_at_event",
    "health_score", "health_delta", "vwap", "sma9", "sma21", "volume",
    "swing_high", "swing_low"
]

OPTIMAL_TRADE_HEADERS = [
    "trade_id", "ticker", "date", "direction", "model", "zone_type",
    "entry_price", "stop_price", "entry_time", "entry_health", "health_label",
    "vwap_position", "sma_trend", "m5_structure", "event_seq", "event_time",
    "r_if_exit", "health", "event_type", "price_at_event", "bars_from_entry",
    "bars_from_mfe", "actual_r", "actual_exit_reason", "health_vs_entry",
    "r_vs_actual", "is_mfe", "is_exit"
]


# ============================================================================
# DATA READER
# ============================================================================

class ExcelDataReader:
    """Reads data from Excel worksheets for report generation."""

    def __init__(self, workbook_name: str = WORKBOOK_NAME):
        self.workbook_name = workbook_name
        self._wb = None

    def connect(self) -> bool:
        """Connect to the Excel workbook."""
        try:
            self._wb = xw.books[self.workbook_name]
            return True
        except Exception as e:
            print(f"  [ERROR] Failed to connect to Excel: {e}")
            return False

    def close(self):
        """Close connection."""
        self._wb = None

    def read_worksheet(self, sheet_name: str, range_str: str) -> List[List[Any]]:
        """Read data from a worksheet range."""
        if not self._wb:
            return []

        try:
            sheet = self._wb.sheets[sheet_name]
            data = sheet.range(range_str).value

            if data is None:
                return []

            # Normalize to list of lists
            if not isinstance(data, list):
                return [[data]]
            if data and not isinstance(data[0], list):
                return [data]

            # Filter out empty rows
            rows = []
            for row in data:
                if row and row[0] is not None and str(row[0]).strip() != "":
                    rows.append(row)
                else:
                    break

            return rows
        except Exception as e:
            print(f"  [WARNING] Could not read {sheet_name}: {e}")
            return []

    def read_backtest(self) -> List[List[Any]]:
        """Read backtest worksheet data."""
        return self.read_worksheet("backtest", "A2:U1000")

    def read_entry_events(self) -> List[List[Any]]:
        """Read entry_events worksheet data."""
        return self.read_worksheet("entry_events", "A2:AQ1000")

    def read_exit_events(self) -> List[List[Any]]:
        """Read exit_events worksheet data."""
        return self.read_worksheet("exit_events", "A2:R10000")

    def read_optimal_trade(self) -> List[List[Any]]:
        """Read optimal_trade worksheet data."""
        return self.read_worksheet("optimal_trade", "A2:AB10000")


# ============================================================================
# STATISTICS CALCULATOR
# ============================================================================

class StatsCalculator:
    """Calculates summary statistics from raw data."""

    @staticmethod
    def _safe_float(val: Any) -> float:
        """Safely convert a value to float."""
        if val is None:
            return 0.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _safe_int(val: Any) -> int:
        """Safely convert a value to int."""
        if val is None:
            return 0
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return 0

    def calc_backtest_stats(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """Calculate backtest summary statistics."""
        if not rows:
            return {"total_trades": 0}

        total = len(rows)
        wins = sum(1 for r in rows if self._safe_int(r[20]) == 1)  # win column

        pnl_r_values = [self._safe_float(r[18]) for r in rows if r[18] is not None]  # pnl_r column
        total_pnl = sum(pnl_r_values) if pnl_r_values else 0

        # By model
        by_model = {}
        for r in rows:
            model = r[3] or "Unknown"
            if model not in by_model:
                by_model[model] = {"trades": 0, "wins": 0, "pnl_r": 0}
            by_model[model]["trades"] += 1
            if self._safe_int(r[20]) == 1:
                by_model[model]["wins"] += 1
            if r[18] is not None:
                by_model[model]["pnl_r"] += self._safe_float(r[18])

        # By exit reason
        by_exit = {}
        for r in rows:
            exit_reason = r[16] or "Unknown"
            if exit_reason not in by_exit:
                by_exit[exit_reason] = {"trades": 0, "pnl_r": 0}
            by_exit[exit_reason]["trades"] += 1
            if r[18] is not None:
                by_exit[exit_reason]["pnl_r"] += self._safe_float(r[18])

        # By direction
        by_direction = {}
        for r in rows:
            direction = r[5] or "Unknown"
            if direction not in by_direction:
                by_direction[direction] = {"trades": 0, "wins": 0, "pnl_r": 0}
            by_direction[direction]["trades"] += 1
            if self._safe_int(r[20]) == 1:
                by_direction[direction]["wins"] += 1
            if r[18] is not None:
                by_direction[direction]["pnl_r"] += self._safe_float(r[18])

        win_rate = (wins / total * 100) if total > 0 else 0
        avg_r = (total_pnl / total) if total > 0 else 0

        # Profit factor
        gross_profit = sum(self._safe_float(r[18]) for r in rows if r[18] is not None and self._safe_float(r[18]) > 0)
        gross_loss = abs(sum(self._safe_float(r[18]) for r in rows if r[18] is not None and self._safe_float(r[18]) < 0))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')

        return {
            "total_trades": total,
            "wins": wins,
            "losses": total - wins,
            "win_rate": win_rate,
            "total_pnl_r": total_pnl,
            "avg_r": avg_r,
            "profit_factor": profit_factor,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "by_model": by_model,
            "by_exit": by_exit,
            "by_direction": by_direction,
        }

    def calc_entry_events_stats(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """Calculate entry events summary statistics."""
        if not rows:
            return {"total_entries": 0}

        total = len(rows)

        # Health score distribution (column index 29 = entry_health)
        health_scores = [self._safe_float(r[29]) for r in rows if r[29] is not None]
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0

        # Health label distribution (column index 30 = health_label)
        health_dist = {}
        for r in rows:
            label = r[30] or "Unknown"
            health_dist[label] = health_dist.get(label, 0) + 1

        # Structure counts
        h4_bull = sum(1 for r in rows if r[8] == "BULL")
        h4_bear = sum(1 for r in rows if r[8] == "BEAR")
        h1_bull = sum(1 for r in rows if r[10] == "BULL")
        h1_bear = sum(1 for r in rows if r[10] == "BEAR")
        m5_bull = sum(1 for r in rows if r[14] == "BULL")
        m5_bear = sum(1 for r in rows if r[14] == "BEAR")

        # Alignment counts
        htf_aligned = sum(1 for r in rows if r[31] == 1 or r[31] == True)
        mtf_aligned = sum(1 for r in rows if r[32] == 1 or r[32] == True)
        vol_aligned = sum(1 for r in rows if r[33] == 1 or r[33] == True)
        ind_aligned = sum(1 for r in rows if r[34] == 1 or r[34] == True)

        return {
            "total_entries": total,
            "avg_health": avg_health,
            "health_distribution": health_dist,
            "h4_bull": h4_bull,
            "h4_bear": h4_bear,
            "h1_bull": h1_bull,
            "h1_bear": h1_bear,
            "m5_bull": m5_bull,
            "m5_bear": m5_bear,
            "htf_aligned": htf_aligned,
            "htf_aligned_pct": (htf_aligned / total * 100) if total > 0 else 0,
            "mtf_aligned": mtf_aligned,
            "mtf_aligned_pct": (mtf_aligned / total * 100) if total > 0 else 0,
            "vol_aligned": vol_aligned,
            "vol_aligned_pct": (vol_aligned / total * 100) if total > 0 else 0,
            "ind_aligned": ind_aligned,
            "ind_aligned_pct": (ind_aligned / total * 100) if total > 0 else 0,
        }

    def calc_exit_events_stats(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """Calculate exit events summary statistics."""
        if not rows:
            return {"total_events": 0}

        total = len(rows)

        # Unique trades
        trade_ids = set(r[0] for r in rows if r[0] is not None)

        # Event type distribution (column index 5 = event_type)
        event_types = {}
        for r in rows:
            event_type = r[5] or "Unknown"
            event_types[event_type] = event_types.get(event_type, 0) + 1

        # Health score stats (column index 10 = health_score)
        health_scores = [self._safe_float(r[10]) for r in rows if r[10] is not None]
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0

        # Health delta stats (column index 11 = health_delta)
        health_deltas = [self._safe_float(r[11]) for r in rows if r[11] is not None]
        degradation_events = sum(1 for d in health_deltas if d < 0)

        # MFE/MAE counts
        mfe_count = sum(1 for r in rows if r[5] and "MFE" in str(r[5]))
        mae_count = sum(1 for r in rows if r[5] and "MAE" in str(r[5]))

        return {
            "total_events": total,
            "unique_trades": len(trade_ids),
            "avg_events_per_trade": total / len(trade_ids) if trade_ids else 0,
            "event_types": event_types,
            "avg_health": avg_health,
            "degradation_events": degradation_events,
            "mfe_count": mfe_count,
            "mae_count": mae_count,
        }

    def calc_optimal_trade_stats(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """Calculate optimal trade summary statistics."""
        if not rows:
            return {"total_rows": 0}

        total = len(rows)

        # Unique trades
        trade_ids = set(r[0] for r in rows if r[0] is not None)

        # R statistics (column index 16 = r_if_exit)
        r_values = [self._safe_float(r[16]) for r in rows if r[16] is not None]
        avg_r_if_exit = sum(r_values) / len(r_values) if r_values else 0

        # Health at each point (column index 17 = health)
        health_r_map = {}
        for r in rows:
            health = self._safe_int(r[17]) if r[17] is not None else None
            r_val = self._safe_float(r[16]) if r[16] is not None else None
            if health is not None and r_val is not None:
                if health not in health_r_map:
                    health_r_map[health] = []
                health_r_map[health].append(r_val)

        health_avg_r = {}
        for h, vals in health_r_map.items():
            health_avg_r[h] = {
                "count": len(vals),
                "avg_r": sum(vals) / len(vals) if vals else 0,
                "win_rate": sum(1 for v in vals if v > 0) / len(vals) * 100 if vals else 0
            }

        # MFE rows (column index 26 = is_mfe)
        mfe_rows = [r for r in rows if self._safe_int(r[26]) == 1]
        mfe_r_values = [self._safe_float(r[16]) for r in mfe_rows if r[16] is not None]
        avg_mfe_r = sum(mfe_r_values) / len(mfe_r_values) if mfe_r_values else 0

        # Actual exit rows (column index 27 = is_exit)
        exit_rows = [r for r in rows if self._safe_int(r[27]) == 1]
        actual_r_values = [self._safe_float(r[22]) for r in exit_rows if r[22] is not None]
        avg_actual_r = sum(actual_r_values) / len(actual_r_values) if actual_r_values else 0

        # Capture rate
        capture_rate = (avg_actual_r / avg_mfe_r * 100) if avg_mfe_r > 0 else 0

        return {
            "total_rows": total,
            "unique_trades": len(trade_ids),
            "avg_bars_per_trade": total / len(trade_ids) if trade_ids else 0,
            "avg_r_if_exit": avg_r_if_exit,
            "avg_mfe_r": avg_mfe_r,
            "avg_actual_r": avg_actual_r,
            "capture_rate": capture_rate,
            "health_avg_r": health_avg_r,
        }


# ============================================================================
# REPORT GENERATOR
# ============================================================================

class ReportGenerator:
    """Generates comprehensive .txt report for Claude AI analysis."""

    def __init__(self, workbook_name: str = WORKBOOK_NAME):
        self.reader = ExcelDataReader(workbook_name)
        self.stats = StatsCalculator()
        self.report_lines: List[str] = []

    def _add_line(self, line: str = ""):
        """Add a line to the report."""
        self.report_lines.append(line)

    def _add_separator(self, char: str = "=", width: int = 80):
        """Add a separator line."""
        self._add_line(char * width)

    def _add_section_header(self, title: str):
        """Add a section header."""
        self._add_line()
        self._add_separator()
        self._add_line(title)
        self._add_separator()

    def _format_value(self, val: Any) -> str:
        """Format a value for text output."""
        if val is None:
            return ""
        if isinstance(val, float):
            return f"{val:.4f}"
        if isinstance(val, datetime):
            return val.strftime("%Y-%m-%d %H:%M:%S")
        return str(val)

    def _add_raw_data_table(self, headers: List[str], rows: List[List[Any]]):
        """Add raw data as a pipe-delimited table."""
        if not rows:
            self._add_line("No data available.")
            return

        # Header row
        self._add_line("|" + "|".join(headers) + "|")
        self._add_line("|" + "|".join(["---"] * len(headers)) + "|")

        # Data rows
        for row in rows:
            formatted = [self._format_value(v) for v in row[:len(headers)]]
            self._add_line("|" + "|".join(formatted) + "|")

    def _generate_header(self, execution_summary: Dict[str, Any]):
        """Generate report header."""
        now = datetime.now()

        self._add_separator()
        self._add_line("EPOCH BACKTEST ANALYSIS REPORT")
        self._add_line("Generated for Claude AI Review")
        self._add_separator()
        self._add_line(f"Report Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self._add_line(f"Workbook: {WORKBOOK_NAME}")
        self._add_line()
        self._add_line("PURPOSE: This report contains raw data and summary statistics from")
        self._add_line("the Epoch backtest system for validation and analysis by Claude AI.")
        self._add_line()
        self._add_line("REQUESTED ANALYSIS:")
        self._add_line("1. Validate that all calculations are correct per the methodology")
        self._add_line("2. Provide analysis synopsis of this backtest session")
        self._add_line("3. Identify any anomalies or areas for refinement")
        self._add_separator()

    def _generate_execution_summary(self, execution_summary: Dict[str, Any]):
        """Generate execution summary section."""
        self._add_section_header("SECTION 1: EXECUTION SUMMARY")

        self._add_line()
        self._add_line(f"Overall Status: {execution_summary.get('status', 'Unknown')}")
        self._add_line(f"Modules Completed: {execution_summary.get('completed', 0)}/{execution_summary.get('total_modules', 4)}")
        self._add_line(f"Total Execution Time: {execution_summary.get('total_time', 0):.1f}s")
        self._add_line()

        self._add_line("Module Timings:")
        for name, duration in execution_summary.get('module_times', {}).items():
            status = "OK" if name not in execution_summary.get('failed_modules', []) else "FAILED"
            self._add_line(f"  {name}: {duration:.1f}s [{status}]")

        self._add_line()
        self._add_line("Validation Results:")
        for name, result in execution_summary.get('validation_results', {}).items():
            self._add_line(f"  {name}: {result}")

    def _generate_backtest_section(self, rows: List[List[Any]], stats: Dict[str, Any]):
        """Generate backtest section."""
        self._add_section_header("SECTION 2: BACKTEST RESULTS")

        # Summary first
        self._add_line()
        self._add_line("SUMMARY STATISTICS")
        self._add_line("-" * 40)
        self._add_line(f"Total Trades:    {stats.get('total_trades', 0)}")
        self._add_line(f"Wins:            {stats.get('wins', 0)}")
        self._add_line(f"Losses:          {stats.get('losses', 0)}")
        self._add_line(f"Win Rate:        {stats.get('win_rate', 0):.1f}%")
        self._add_line(f"Total P&L:       {stats.get('total_pnl_r', 0):+.2f}R")
        self._add_line(f"Average R:       {stats.get('avg_r', 0):+.2f}R")
        self._add_line(f"Profit Factor:   {stats.get('profit_factor', 0):.2f}")
        self._add_line(f"Gross Profit:    {stats.get('gross_profit', 0):+.2f}R")
        self._add_line(f"Gross Loss:      {stats.get('gross_loss', 0):+.2f}R")

        self._add_line()
        self._add_line("BY MODEL:")
        for model, data in stats.get('by_model', {}).items():
            wr = (data['wins'] / data['trades'] * 100) if data['trades'] > 0 else 0
            self._add_line(f"  {model}: {data['trades']} trades, {wr:.0f}% WR, {data['pnl_r']:+.2f}R")

        self._add_line()
        self._add_line("BY EXIT REASON:")
        for reason, data in stats.get('by_exit', {}).items():
            self._add_line(f"  {reason}: {data['trades']} trades, {data['pnl_r']:+.2f}R")

        self._add_line()
        self._add_line("BY DIRECTION:")
        for direction, data in stats.get('by_direction', {}).items():
            wr = (data['wins'] / data['trades'] * 100) if data['trades'] > 0 else 0
            self._add_line(f"  {direction}: {data['trades']} trades, {wr:.0f}% WR, {data['pnl_r']:+.2f}R")

        # Raw data
        self._add_line()
        self._add_line("RAW DATA")
        self._add_line("-" * 40)
        self._add_raw_data_table(BACKTEST_HEADERS, rows)

    def _generate_entry_events_section(self, rows: List[List[Any]], stats: Dict[str, Any]):
        """Generate entry events section."""
        self._add_section_header("SECTION 3: ENTRY EVENTS RESULTS")

        # Summary
        self._add_line()
        self._add_line("SUMMARY STATISTICS")
        self._add_line("-" * 40)
        self._add_line(f"Total Entries:       {stats.get('total_entries', 0)}")
        self._add_line(f"Avg Health Score:    {stats.get('avg_health', 0):.1f}/10")

        self._add_line()
        self._add_line("HEALTH DISTRIBUTION:")
        for label, count in stats.get('health_distribution', {}).items():
            pct = (count / stats.get('total_entries', 1)) * 100
            self._add_line(f"  {label}: {count} ({pct:.1f}%)")

        self._add_line()
        self._add_line("STRUCTURE ANALYSIS:")
        self._add_line(f"  H4: {stats.get('h4_bull', 0)} BULL / {stats.get('h4_bear', 0)} BEAR")
        self._add_line(f"  H1: {stats.get('h1_bull', 0)} BULL / {stats.get('h1_bear', 0)} BEAR")
        self._add_line(f"  M5: {stats.get('m5_bull', 0)} BULL / {stats.get('m5_bear', 0)} BEAR")

        self._add_line()
        self._add_line("ALIGNMENT RATES:")
        self._add_line(f"  HTF Aligned (H4+H1):  {stats.get('htf_aligned', 0)} ({stats.get('htf_aligned_pct', 0):.1f}%)")
        self._add_line(f"  MTF Aligned (M15+M5): {stats.get('mtf_aligned', 0)} ({stats.get('mtf_aligned_pct', 0):.1f}%)")
        self._add_line(f"  Volume Aligned:       {stats.get('vol_aligned', 0)} ({stats.get('vol_aligned_pct', 0):.1f}%)")
        self._add_line(f"  Indicator Aligned:    {stats.get('ind_aligned', 0)} ({stats.get('ind_aligned_pct', 0):.1f}%)")

        # Raw data
        self._add_line()
        self._add_line("RAW DATA")
        self._add_line("-" * 40)
        self._add_raw_data_table(ENTRY_EVENTS_HEADERS, rows)

    def _generate_exit_events_section(self, rows: List[List[Any]], stats: Dict[str, Any]):
        """Generate exit events section."""
        self._add_section_header("SECTION 4: EXIT EVENTS RESULTS")

        # Summary
        self._add_line()
        self._add_line("SUMMARY STATISTICS")
        self._add_line("-" * 40)
        self._add_line(f"Total Events:        {stats.get('total_events', 0)}")
        self._add_line(f"Unique Trades:       {stats.get('unique_trades', 0)}")
        self._add_line(f"Avg Events/Trade:    {stats.get('avg_events_per_trade', 0):.1f}")
        self._add_line(f"Avg Health Score:    {stats.get('avg_health', 0):.1f}")
        self._add_line(f"Degradation Events:  {stats.get('degradation_events', 0)}")
        self._add_line(f"MFE Events:          {stats.get('mfe_count', 0)}")
        self._add_line(f"MAE Events:          {stats.get('mae_count', 0)}")

        self._add_line()
        self._add_line("EVENT TYPE DISTRIBUTION:")
        for event_type, count in sorted(stats.get('event_types', {}).items(), key=lambda x: x[1], reverse=True):
            self._add_line(f"  {event_type}: {count}")

        # Raw data
        self._add_line()
        self._add_line("RAW DATA")
        self._add_line("-" * 40)
        self._add_raw_data_table(EXIT_EVENTS_HEADERS, rows)

    def _generate_optimal_trade_section(self, rows: List[List[Any]], stats: Dict[str, Any]):
        """Generate optimal trade section."""
        self._add_section_header("SECTION 5: OPTIMAL TRADE ANALYSIS")

        # Summary
        self._add_line()
        self._add_line("SUMMARY STATISTICS")
        self._add_line("-" * 40)
        self._add_line(f"Total Decision Points: {stats.get('total_rows', 0)}")
        self._add_line(f"Unique Trades:         {stats.get('unique_trades', 0)}")
        self._add_line(f"Avg Bars per Trade:    {stats.get('avg_bars_per_trade', 0):.1f}")
        self._add_line(f"Avg R if Exit:         {stats.get('avg_r_if_exit', 0):+.2f}R")
        self._add_line(f"Avg MFE R:             {stats.get('avg_mfe_r', 0):+.2f}R")
        self._add_line(f"Avg Actual R:          {stats.get('avg_actual_r', 0):+.2f}R")
        self._add_line(f"Capture Rate:          {stats.get('capture_rate', 0):.1f}%")

        self._add_line()
        self._add_line("HEALTH SCORE -> AVERAGE R IF EXIT:")
        for health in sorted(stats.get('health_avg_r', {}).keys(), reverse=True):
            data = stats['health_avg_r'][health]
            self._add_line(f"  Health {health}: {data['count']} bars, {data['avg_r']:+.2f}R avg, {data['win_rate']:.0f}% win")

        # Raw data
        self._add_line()
        self._add_line("RAW DATA")
        self._add_line("-" * 40)
        self._add_raw_data_table(OPTIMAL_TRADE_HEADERS, rows)

    def _generate_validation_checklist(self):
        """Generate validation checklist for Claude."""
        self._add_section_header("SECTION 6: VALIDATION CHECKLIST")

        self._add_line()
        self._add_line("Please verify the following calculations and logic:")
        self._add_line()
        self._add_line("BACKTEST VALIDATION:")
        self._add_line("[ ] Win/Loss classification matches pnl_r sign (positive = win)")
        self._add_line("[ ] P&L R calculation: (exit_price - entry_price) / risk is correct")
        self._add_line("[ ] Exit reasons align with price action (stop hit, target hit, etc.)")
        self._add_line("[ ] Trade direction matches zone type logic")
        self._add_line()
        self._add_line("ENTRY EVENTS VALIDATION:")
        self._add_line("[ ] Health score (0-10) correctly sums individual factor scores")
        self._add_line("[ ] Structure labels (BULL/BEAR) match higher timeframe trends")
        self._add_line("[ ] VWAP position correctly identifies above/below")
        self._add_line("[ ] SMA alignment logic is consistent")
        self._add_line()
        self._add_line("EXIT EVENTS VALIDATION:")
        self._add_line("[ ] Event sequence is chronologically ordered")
        self._add_line("[ ] Health delta correctly shows change from previous bar")
        self._add_line("[ ] MFE/MAE events correctly identify extremes")
        self._add_line("[ ] Bars from entry count is accurate")
        self._add_line()
        self._add_line("OPTIMAL TRADE VALIDATION:")
        self._add_line("[ ] R_if_exit calculation matches price at that bar")
        self._add_line("[ ] is_mfe=1 correctly identifies maximum favorable excursion")
        self._add_line("[ ] is_exit=1 correctly identifies actual exit bar")
        self._add_line("[ ] Health_vs_entry delta is calculated correctly")

    def _generate_analysis_focus(self):
        """Generate analysis focus areas for Claude."""
        self._add_section_header("SECTION 7: ANALYSIS FOCUS AREAS")

        self._add_line()
        self._add_line("Please analyze and provide insights on:")
        self._add_line()
        self._add_line("1. TRADE QUALITY ASSESSMENT")
        self._add_line("   - Are the entry conditions (health scores) correlating with outcomes?")
        self._add_line("   - Which models are performing best/worst and why?")
        self._add_line("   - Is there a pattern in winning vs losing trades?")
        self._add_line()
        self._add_line("2. EXIT OPTIMIZATION")
        self._add_line("   - What health score threshold would optimize exits?")
        self._add_line("   - How much R is being left on the table (capture rate)?")
        self._add_line("   - Are there patterns in when MFE occurs?")
        self._add_line()
        self._add_line("3. STRUCTURAL ALIGNMENT")
        self._add_line("   - How does HTF/MTF alignment affect outcomes?")
        self._add_line("   - Are volume-aligned entries outperforming?")
        self._add_line("   - What's the optimal combination of alignment factors?")
        self._add_line()
        self._add_line("4. RISK MANAGEMENT")
        self._add_line("   - Are stops appropriately placed?")
        self._add_line("   - What's the distribution of R outcomes?")
        self._add_line("   - Any concerning patterns in large losses?")
        self._add_line()
        self._add_line("5. RECOMMENDATIONS")
        self._add_line("   - What specific refinements would improve the system?")
        self._add_line("   - Are there any obvious issues or bugs in the logic?")
        self._add_line("   - Priority areas for further development?")

    def _generate_footer(self):
        """Generate report footer."""
        self._add_line()
        self._add_separator()
        self._add_line("END OF REPORT")
        self._add_separator()

    def generate(self, execution_summary: Dict[str, Any]) -> str:
        """
        Generate the complete report.

        Args:
            execution_summary: Dictionary containing execution metadata from bt_runner

        Returns:
            The full report as a string
        """
        self.report_lines = []

        # Connect to Excel
        if not self.reader.connect():
            return "ERROR: Could not connect to Excel workbook"

        try:
            # Read all data
            print("  Reading backtest data...")
            backtest_rows = self.reader.read_backtest()

            print("  Reading entry_events data...")
            entry_events_rows = self.reader.read_entry_events()

            print("  Reading exit_events data...")
            exit_events_rows = self.reader.read_exit_events()

            print("  Reading optimal_trade data...")
            optimal_trade_rows = self.reader.read_optimal_trade()

            # Calculate statistics
            print("  Calculating statistics...")
            backtest_stats = self.stats.calc_backtest_stats(backtest_rows)
            entry_events_stats = self.stats.calc_entry_events_stats(entry_events_rows)
            exit_events_stats = self.stats.calc_exit_events_stats(exit_events_rows)
            optimal_trade_stats = self.stats.calc_optimal_trade_stats(optimal_trade_rows)

            # Generate report sections
            print("  Generating report...")
            self._generate_header(execution_summary)
            self._generate_execution_summary(execution_summary)
            self._generate_backtest_section(backtest_rows, backtest_stats)
            self._generate_entry_events_section(entry_events_rows, entry_events_stats)
            self._generate_exit_events_section(exit_events_rows, exit_events_stats)
            self._generate_optimal_trade_section(optimal_trade_rows, optimal_trade_stats)
            self._generate_validation_checklist()
            self._generate_analysis_focus()
            self._generate_footer()

            return "\n".join(self.report_lines)

        finally:
            self.reader.close()

    def save_report(self, execution_summary: Dict[str, Any]) -> Optional[Path]:
        """
        Generate and save the report to file.

        Args:
            execution_summary: Dictionary containing execution metadata

        Returns:
            Path to the saved report file, or None if failed
        """
        # Ensure results directory exists
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"bt_report_{timestamp}.txt"
        filepath = RESULTS_DIR / filename

        print(f"\nGenerating analysis report...")

        # Generate report content
        content = self.generate(execution_summary)

        if content.startswith("ERROR"):
            print(f"  {content}")
            return None

        # Write to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"  Report saved: {filepath}")
            print(f"  Size: {len(content):,} characters, {len(self.report_lines):,} lines")

            return filepath

        except Exception as e:
            print(f"  ERROR saving report: {e}")
            return None


# ============================================================================
# STANDALONE ENTRY POINT
# ============================================================================

def main():
    """Standalone entry point for testing."""
    print("=" * 70)
    print("EPOCH REPORT GENERATOR - STANDALONE MODE")
    print("=" * 70)

    # Create mock execution summary
    execution_summary = {
        "status": "SUCCESS",
        "completed": 4,
        "total_modules": 4,
        "total_time": 0,
        "module_times": {},
        "validation_results": {},
        "failed_modules": [],
    }

    generator = ReportGenerator()
    filepath = generator.save_report(execution_summary)

    if filepath:
        print(f"\nReport generated successfully: {filepath}")
    else:
        print("\nReport generation failed.")


if __name__ == "__main__":
    main()

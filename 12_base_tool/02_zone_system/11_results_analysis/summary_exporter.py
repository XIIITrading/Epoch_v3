"""
Module 10: Daily Summary Exporter
Generates condensed text summary for Claude conversation analysis.

OUTPUT: Lightweight daily summary (~2-3K tokens) suitable for chat context.
USE: Paste into Claude for daily insights without hitting context limits.
"""
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from config import OUTPUT_DIR
from excel_reader import ExcelReader, Trade, EntryEvent, ExitEvent, OptimalTrade


class DailySummaryExporter:
    """Exports condensed daily trading summary for AI analysis."""
    
    def __init__(self, target_date: str = None):
        self.target_date = target_date or date.today().strftime("%Y-%m-%d")
        self.excel_reader = ExcelReader()
    
    def export(self) -> str:
        """Generate condensed daily summary as text."""
        try:
            # Read data
            trades = self.excel_reader.read_trades(self.target_date)
            entry_events = self.excel_reader.read_entry_events(self.target_date)
            exit_events = self.excel_reader.read_exit_events(self.target_date)
            optimal_trades = self.excel_reader.read_optimal_trades(self.target_date)
            structures = self.excel_reader.read_market_structure()
            
            if not trades:
                return f"NO TRADES FOUND FOR {self.target_date}"
            
            # Build summary sections
            lines = []
            lines.append(self._header())
            lines.append(self._performance_overview(trades))
            lines.append(self._model_breakdown(trades))
            lines.append(self._direction_breakdown(trades))
            lines.append(self._exit_breakdown(trades))
            lines.append(self._confluence_analysis(trades, entry_events))
            lines.append(self._efficiency_analysis(trades, optimal_trades))
            lines.append(self._timing_analysis(trades, entry_events))
            lines.append(self._top_trades(trades))
            lines.append(self._flags_and_questions(trades, entry_events, optimal_trades))
            lines.append(self._footer())
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"ERROR GENERATING SUMMARY: {str(e)}"
    
    def _header(self) -> str:
        return f"""================================================================================
EPOCH DAILY SUMMARY | {self.target_date}
================================================================================"""

    def _footer(self) -> str:
        return f"""
================================================================================
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")} | Full data: {self.target_date}_backtest_analysis.json
================================================================================"""

    def _performance_overview(self, trades: List[Trade]) -> str:
        """Core performance metrics."""
        winners = [t for t in trades if t.is_win]
        losers = [t for t in trades if not t.is_win]
        
        total_r = sum(t.pnl_r for t in trades)
        win_r = sum(t.pnl_r for t in winners)
        loss_r = sum(t.pnl_r for t in losers)
        
        win_rate = len(winners) / len(trades) * 100 if trades else 0
        expectancy = total_r / len(trades) if trades else 0
        profit_factor = abs(win_r / loss_r) if loss_r else 0
        
        avg_win = win_r / len(winners) if winners else 0
        avg_loss = loss_r / len(losers) if losers else 0
        
        return f"""
PERFORMANCE OVERVIEW
--------------------
Trades: {len(trades)} | Wins: {len(winners)} | Losses: {len(losers)} | Win Rate: {win_rate:.1f}%
Net R: {total_r:+.2f} | Expectancy: {expectancy:+.3f}R | Profit Factor: {profit_factor:.2f}
Avg Win: {avg_win:+.2f}R | Avg Loss: {avg_loss:.2f}R"""

    def _model_breakdown(self, trades: List[Trade]) -> str:
        """Performance by entry model."""
        lines = ["\nBY MODEL", "--------"]
        
        for model in ["EPCH1", "EPCH2", "EPCH3", "EPCH4"]:
            model_trades = [t for t in trades if t.model == model]
            if not model_trades:
                continue
            
            wins = len([t for t in model_trades if t.is_win])
            net_r = sum(t.pnl_r for t in model_trades)
            win_rate = wins / len(model_trades) * 100
            exp = net_r / len(model_trades)
            
            status = "[+]" if net_r > 0 else "[-]"
            lines.append(f"{model}: {len(model_trades)} trades | {win_rate:.0f}% WR | {net_r:+.2f}R | {exp:+.3f} exp {status}")
        
        return "\n".join(lines)

    def _direction_breakdown(self, trades: List[Trade]) -> str:
        """Performance by direction."""
        lines = ["\nBY DIRECTION", "------------"]
        
        for direction in ["LONG", "SHORT"]:
            dir_trades = [t for t in trades if t.direction == direction]
            if not dir_trades:
                continue
            
            wins = len([t for t in dir_trades if t.is_win])
            net_r = sum(t.pnl_r for t in dir_trades)
            win_rate = wins / len(dir_trades) * 100
            
            status = "[+]" if net_r > 0 else "[-]"
            lines.append(f"{direction}: {len(dir_trades)} trades | {win_rate:.0f}% WR | {net_r:+.2f}R {status}")
        
        return "\n".join(lines)

    def _exit_breakdown(self, trades: List[Trade]) -> str:
        """Performance by exit type."""
        lines = ["\nBY EXIT TYPE", "------------"]
        
        exit_types = set(t.exit_reason for t in trades if t.exit_reason)
        for exit_type in sorted(exit_types):
            exit_trades = [t for t in trades if t.exit_reason == exit_type]
            wins = len([t for t in exit_trades if t.is_win])
            net_r = sum(t.pnl_r for t in exit_trades)
            win_rate = wins / len(exit_trades) * 100 if exit_trades else 0
            
            lines.append(f"{exit_type}: {len(exit_trades)} ({win_rate:.0f}% WR) | {net_r:+.2f}R")
        
        return "\n".join(lines)

    def _confluence_analysis(self, trades: List[Trade], entry_events: Dict[str, EntryEvent]) -> str:
        """Pre-computed confluence factor analysis."""
        lines = ["\nCONFLUENCE IMPACT", "-----------------"]
        
        if not entry_events:
            lines.append("(Entry enrichment data not available)")
            return "\n".join(lines)
        
        # Match trades with entry events
        matched = [(t, entry_events.get(t.trade_id)) for t in trades]
        matched = [(t, ee) for t, ee in matched if ee is not None]
        
        if not matched:
            lines.append("(No matched entry events)")
            return "\n".join(lines)
        
        # VWAP Alignment
        vwap_aligned = [(t, ee) for t, ee in matched if ee.vwap_aligned]
        vwap_not = [(t, ee) for t, ee in matched if not ee.vwap_aligned]
        
        if vwap_aligned:
            vwap_wr = len([t for t, _ in vwap_aligned if t.is_win]) / len(vwap_aligned) * 100
            vwap_r = sum(t.pnl_r for t, _ in vwap_aligned)
            lines.append(f"VWAP Aligned: {len(vwap_aligned)} trades | {vwap_wr:.0f}% WR | {vwap_r:+.2f}R")
        if vwap_not:
            vwap_not_wr = len([t for t, _ in vwap_not if t.is_win]) / len(vwap_not) * 100
            vwap_not_r = sum(t.pnl_r for t, _ in vwap_not)
            lines.append(f"VWAP Not Aligned: {len(vwap_not)} trades | {vwap_not_wr:.0f}% WR | {vwap_not_r:+.2f}R")
        
        # Trend Alignment (SMA)
        trend_aligned = [(t, ee) for t, ee in matched if ee.trend_aligned]
        trend_not = [(t, ee) for t, ee in matched if not ee.trend_aligned]
        
        if trend_aligned:
            trend_wr = len([t for t, _ in trend_aligned if t.is_win]) / len(trend_aligned) * 100
            trend_r = sum(t.pnl_r for t, _ in trend_aligned)
            lines.append(f"Trend Aligned: {len(trend_aligned)} trades | {trend_wr:.0f}% WR | {trend_r:+.2f}R")
        if trend_not:
            trend_not_wr = len([t for t, _ in trend_not if t.is_win]) / len(trend_not) * 100
            trend_not_r = sum(t.pnl_r for t, _ in trend_not)
            lines.append(f"Trend Not Aligned: {len(trend_not)} trades | {trend_not_wr:.0f}% WR | {trend_not_r:+.2f}R")
        
        # Structure Alignment
        struct_aligned = [(t, ee) for t, ee in matched if ee.structure_aligned]
        struct_not = [(t, ee) for t, ee in matched if not ee.structure_aligned]
        
        if struct_aligned:
            struct_wr = len([t for t, _ in struct_aligned if t.is_win]) / len(struct_aligned) * 100
            struct_r = sum(t.pnl_r for t, _ in struct_aligned)
            lines.append(f"Structure Aligned: {len(struct_aligned)} trades | {struct_wr:.0f}% WR | {struct_r:+.2f}R")
        if struct_not:
            struct_not_wr = len([t for t, _ in struct_not if t.is_win]) / len(struct_not) * 100
            struct_not_r = sum(t.pnl_r for t, _ in struct_not)
            lines.append(f"Structure Not Aligned: {len(struct_not)} trades | {struct_not_wr:.0f}% WR | {struct_not_r:+.2f}R")
        
        # Health Score
        lines.append("")
        for label in ["STRONG", "MODERATE", "WEAK"]:
            health_trades = [(t, ee) for t, ee in matched if ee.health_label == label]
            if health_trades:
                health_wr = len([t for t, _ in health_trades if t.is_win]) / len(health_trades) * 100
                health_r = sum(t.pnl_r for t, _ in health_trades)
                lines.append(f"Health {label}: {len(health_trades)} trades | {health_wr:.0f}% WR | {health_r:+.2f}R")
        
        # Volume Class
        lines.append("")
        for vol_class in ["LOW", "NORMAL", "HIGH", "EXTREME"]:
            vol_trades = [(t, ee) for t, ee in matched if ee.vol_delta_class == vol_class]
            if vol_trades:
                vol_wr = len([t for t, _ in vol_trades if t.is_win]) / len(vol_trades) * 100
                vol_r = sum(t.pnl_r for t, _ in vol_trades)
                lines.append(f"Volume {vol_class}: {len(vol_trades)} trades | {vol_wr:.0f}% WR | {vol_r:+.2f}R")
        
        # Full Confluence (all 3 aligned)
        full_confluence = [(t, ee) for t, ee in matched 
                          if ee.vwap_aligned and ee.trend_aligned and ee.structure_aligned]
        if full_confluence:
            lines.append("")
            fc_wr = len([t for t, _ in full_confluence if t.is_win]) / len(full_confluence) * 100
            fc_r = sum(t.pnl_r for t, _ in full_confluence)
            lines.append(f"FULL CONFLUENCE (all 3): {len(full_confluence)} trades | {fc_wr:.0f}% WR | {fc_r:+.2f}R")
        
        return "\n".join(lines)

    def _efficiency_analysis(self, trades: List[Trade], optimal_trades: Dict[str, OptimalTrade]) -> str:
        """Capture efficiency summary."""
        lines = ["\nCAPTURE EFFICIENCY", "------------------"]
        
        if not optimal_trades:
            lines.append("(Optimal trade data not available)")
            return "\n".join(lines)
        
        # Match trades with optimal data
        efficiencies = []
        potential_r = 0
        actual_r = 0
        
        for trade in trades:
            ot = optimal_trades.get(trade.trade_id)
            if ot and ot.capture_efficiency:
                efficiencies.append(ot.capture_efficiency)
            if ot and ot.optimal_pnl_r:
                potential_r += ot.optimal_pnl_r
            actual_r += trade.pnl_r
        
        if efficiencies:
            avg_eff = sum(efficiencies) / len(efficiencies) * 100
            lines.append(f"Avg Capture Efficiency: {avg_eff:.1f}%")
            lines.append(f"Actual R: {actual_r:+.2f} | Potential R: {potential_r:+.2f}")
            lines.append(f"R Left on Table: {potential_r - actual_r:.2f}")
        else:
            lines.append("(No efficiency data matched)")
        
        return "\n".join(lines)

    def _timing_analysis(self, trades: List[Trade], entry_events: Dict[str, EntryEvent]) -> str:
        """Time-based performance analysis."""
        lines = ["\nTIMING ANALYSIS", "---------------"]
        
        # Group by hour
        hour_buckets = {}
        for trade in trades:
            try:
                # Parse entry_time (HH:MM format)
                if trade.entry_time and ":" in str(trade.entry_time):
                    hour = int(str(trade.entry_time).split(":")[0])
                    if hour not in hour_buckets:
                        hour_buckets[hour] = []
                    hour_buckets[hour].append(trade)
            except:
                pass
        
        if hour_buckets:
            for hour in sorted(hour_buckets.keys()):
                bucket = hour_buckets[hour]
                wins = len([t for t in bucket if t.is_win])
                net_r = sum(t.pnl_r for t in bucket)
                wr = wins / len(bucket) * 100
                
                hour_label = f"{hour:02d}:00-{hour:02d}:59"
                status = "[+]" if net_r > 0 else "[-]" if net_r < -1 else "[~]"
                lines.append(f"{hour_label}: {len(bucket)} trades | {wr:.0f}% WR | {net_r:+.2f}R {status}")
        else:
            lines.append("(Time data not parsed)")
        
        return "\n".join(lines)

    def _top_trades(self, trades: List[Trade]) -> str:
        """Best and worst trades."""
        lines = ["\nNOTABLE TRADES", "--------------"]
        
        sorted_trades = sorted(trades, key=lambda t: t.pnl_r, reverse=True)
        
        # Top 3 winners
        lines.append("Best:")
        for t in sorted_trades[:3]:
            if t.pnl_r > 0:
                lines.append(f"  {t.trade_id}: {t.pnl_r:+.2f}R ({t.exit_reason})")
        
        # Bottom 3 losers
        lines.append("Worst:")
        for t in sorted_trades[-3:]:
            if t.pnl_r < 0:
                lines.append(f"  {t.trade_id}: {t.pnl_r:+.2f}R ({t.exit_reason})")
        
        return "\n".join(lines)

    def _flags_and_questions(self, trades: List[Trade], entry_events: Dict[str, EntryEvent], 
                            optimal_trades: Dict[str, OptimalTrade]) -> str:
        """Auto-detected patterns and questions for review."""
        lines = ["\nFLAGS & QUESTIONS", "-----------------"]
        flags = []
        
        # Check for concerning patterns
        total_r = sum(t.pnl_r for t in trades)
        winners = [t for t in trades if t.is_win]
        losers = [t for t in trades if not t.is_win]
        
        # 1. Negative day
        if total_r < 0:
            flags.append(f"[!] Negative day: {total_r:.2f}R - Review losing trades")
        
        # 2. Low win rate
        win_rate = len(winners) / len(trades) * 100 if trades else 0
        if win_rate < 35:
            flags.append(f"[!] Low win rate: {win_rate:.0f}% - Entry quality concern")
        
        # 3. CHOCH cutting winners
        choch_trades = [t for t in trades if t.exit_reason == "CHOCH"]
        if choch_trades:
            choch_winners = [t for t in choch_trades if t.is_win]
            if len(choch_winners) / len(choch_trades) > 0.6:
                flags.append(f"[?] CHOCH exiting {len(choch_winners)}/{len(choch_trades)} winners - too aggressive?")
        
        # 4. Stops dominating
        stop_trades = [t for t in trades if t.exit_reason == "STOP"]
        if len(stop_trades) / len(trades) > 0.5:
            flags.append(f"[!] {len(stop_trades)}/{len(trades)} trades stopped out - Zone quality issue?")
        
        # 5. Direction bias
        longs = [t for t in trades if t.direction == "LONG"]
        shorts = [t for t in trades if t.direction == "SHORT"]
        if longs and shorts:
            long_r = sum(t.pnl_r for t in longs)
            short_r = sum(t.pnl_r for t in shorts)
            if abs(long_r - short_r) > 5:
                better = "SHORTS" if short_r > long_r else "LONGS"
                flags.append(f"[?] Strong direction bias: {better} outperforming by {abs(long_r - short_r):.1f}R")
        
        # 6. Model underperforming
        for model in ["EPCH1", "EPCH2", "EPCH3", "EPCH4"]:
            model_trades = [t for t in trades if t.model == model]
            if len(model_trades) >= 5:
                model_r = sum(t.pnl_r for t in model_trades)
                if model_r < -2:
                    flags.append(f"[!] {model} struggling: {model_r:.2f}R from {len(model_trades)} trades")
        
        # 7. Entry quality if available
        if entry_events:
            matched = [(t, entry_events.get(t.trade_id)) for t in trades]
            weak_entries = [(t, ee) for t, ee in matched if ee and ee.health_label == "WEAK"]
            if len(weak_entries) >= 3:
                weak_r = sum(t.pnl_r for t, _ in weak_entries)
                flags.append(f"[?] {len(weak_entries)} WEAK health entries taken: {weak_r:.2f}R total")
        
        if flags:
            lines.extend(flags)
        else:
            lines.append("[OK] No major flags detected")
        
        # Questions for analysis
        lines.append("")
        lines.append("REVIEW QUESTIONS:")
        lines.append("- Which confluence factors had strongest impact today?")
        lines.append("- Should any entry filters be adjusted based on today's data?")
        lines.append("- Were stops appropriately placed or should zones be reconsidered?")
        
        return "\n".join(lines)

    def save(self, content: str) -> Path:
        """Save summary to file."""
        filename = f"{self.target_date}_daily_summary.txt"
        filepath = OUTPUT_DIR / filename
        
        # Use UTF-8 encoding for Windows compatibility
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Summary saved: {filepath}")
        return filepath


def generate_daily_summary(target_date: str = None) -> str:
    """Convenience function to generate summary."""
    exporter = DailySummaryExporter(target_date)
    summary = exporter.export()
    exporter.save(summary)
    return summary


if __name__ == "__main__":
    import sys
    
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    summary = generate_daily_summary(target_date)
    print(summary)
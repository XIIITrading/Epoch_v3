"""
Report formatting utilities.
"""
from typing import Dict, List
import pandas as pd

class ReportFormatter:
    """Format scan results for various output types."""
    
    @staticmethod
    def format_console_output(scan_results: pd.DataFrame, top_n: int = 10) -> str:
        """Format results for console display."""
        if scan_results.empty:
            return "No stocks passed filters."
        
        lines = []
        lines.append("\nTop Stocks by Interest Score:")
        lines.append("-" * 80)
        lines.append(f"{'Rank':<5} {'Ticker':<8} {'Price':<10} {'Score':<8} {'PM Vol':<12} {'PM %':<8} {'ATR %':<8}")
        lines.append("-" * 80)
        
        for _, row in scan_results.head(top_n).iterrows():
            pm_pct = (row['premarket_volume'] / row['avg_daily_volume'] * 100)
            lines.append(
                f"{row['rank']:<5} {row['ticker']:<8} ${row['price']:<9.2f} "
                f"{row['interest_score']:<8.2f} {row['premarket_volume']:>11,.0f} "
                f"{pm_pct:>7.2f}% {row['atr_percent']:>7.2f}%"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def format_score_explanation(explanation: Dict) -> str:
        """Format score explanation for display."""
        lines = []
        lines.append("\nScore Breakdown:")
        
        for component, details in explanation['components'].items():
            lines.append(
                f"  {component}: {details['contribution']:.2f} points "
                f"(raw: {details['raw_value']})"
            )
        
        lines.append(f"\nTotal Score: {explanation['total_score']:.2f}")
        
        return "\n".join(lines)
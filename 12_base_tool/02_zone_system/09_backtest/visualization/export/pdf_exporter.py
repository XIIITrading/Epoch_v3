# pdf_exporter.py
# Location: C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\visualization\export\
# Purpose: Export trade visualizations to PDF (single and batch)

"""
PDF Exporter for Trade Visualizations

Supports two export modes:
1. Single Trade: One trade per PDF with full 4-quadrant visualization
2. Batch Export: Multiple trades in one PDF with optional summary page

Uses matplotlib's PdfPages for multi-page PDF generation.
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Callable
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import config
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config.backtest_config import (
        COLORS, PAGE_WIDTH, PAGE_HEIGHT, PDF_DPI,
        SINGLE_PDF_TEMPLATE, BATCH_PDF_TEMPLATE
    )
except ImportError:
    COLORS = {'dark_bg': '#1a1a2e', 'text_primary': '#e0e0e0'}
    PAGE_WIDTH, PAGE_HEIGHT = 11.0, 8.5
    PDF_DPI = 150
    SINGLE_PDF_TEMPLATE = "{ticker}_{date}_{model}_{direction}.pdf"
    BATCH_PDF_TEMPLATE = "backtest_report_{start_date}_to_{end_date}.pdf"


# =============================================================================
# PDF EXPORTER CLASS
# =============================================================================

class BacktestPDFExporter:
    """Export trade visualizations to PDF"""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize exporter.
        
        Args:
            output_dir: Directory for PDF output (None = current directory)
        """
        if output_dir is None:
            output_dir = Path.cwd() / 'backtest_reports'
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"PDF output directory: {self.output_dir}")
    
    def export_single_trade(self, trade, chart_builder, data_provider,
                            filename: str = None) -> str:
        """
        Export a single trade visualization to PDF.
        
        Args:
            trade: TradeRecord object
            chart_builder: TradeChartBuilder instance
            data_provider: TradeChartDataProvider instance
            filename: Custom filename (None = auto-generate)
            
        Returns:
            Path to generated PDF
        """
        # Generate filename if not provided
        if filename is None:
            filename = SINGLE_PDF_TEMPLATE.format(
                ticker=trade.ticker,
                date=trade.date.replace('-', ''),
                model=trade.model,
                direction=trade.direction
            )
        
        filepath = self.output_dir / filename
        
        logger.info(f"Exporting trade: {trade.trade_id}")
        
        try:
            # Get visualization data
            viz_data = data_provider.get_trade_visualization_data(trade)
            
            # Build the chart
            fig = chart_builder.build(
                trade=trade,
                m5_bars=viz_data['m5_bars'],
                h1_bars=viz_data['h1_bars'],
                m15_bars=viz_data['m15_bars'],
                zones=viz_data['zones'],
                hvn_pocs=viz_data['hvn_pocs']
            )
            
            # Save to PDF
            fig.savefig(str(filepath), format='pdf', dpi=PDF_DPI,
                       facecolor=COLORS['dark_bg'], edgecolor='none',
                       bbox_inches='tight')
            
            # Close figure
            plt.close(fig)
            
            logger.info(f"Saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting trade {trade.trade_id}: {e}")
            raise
    
    def export_batch(self, trades: List, chart_builder, data_provider,
                     filename: str = None, include_summary: bool = True,
                     progress_callback: Callable = None) -> str:
        """
        Export multiple trades to a single PDF.
        
        Args:
            trades: List of TradeRecord objects
            chart_builder: TradeChartBuilder instance
            data_provider: TradeChartDataProvider instance
            filename: Custom filename (None = auto-generate)
            include_summary: Whether to include summary page at start
            progress_callback: Optional callback(current, total, trade) for progress
            
        Returns:
            Path to generated PDF
        """
        if not trades:
            raise ValueError("No trades to export")
        
        # Generate filename if not provided
        if filename is None:
            dates = sorted([t.date for t in trades])
            filename = BATCH_PDF_TEMPLATE.format(
                start_date=dates[0].replace('-', ''),
                end_date=dates[-1].replace('-', '')
            )
        
        filepath = self.output_dir / filename
        
        logger.info(f"Exporting batch: {len(trades)} trades to {filepath}")
        
        try:
            with PdfPages(str(filepath)) as pdf:
                # Summary page (if requested)
                if include_summary:
                    summary_fig = self._create_summary_page(trades)
                    pdf.savefig(summary_fig, facecolor=COLORS['dark_bg'])
                    plt.close(summary_fig)
                
                # Individual trade pages
                for i, trade in enumerate(trades):
                    if progress_callback:
                        progress_callback(i + 1, len(trades), trade)
                    
                    logger.info(f"Processing trade {i+1}/{len(trades)}: {trade.trade_id}")
                    
                    try:
                        # Get visualization data
                        viz_data = data_provider.get_trade_visualization_data(trade)
                        
                        # Build the chart
                        fig = chart_builder.build(
                            trade=trade,
                            m5_bars=viz_data['m5_bars'],
                            h1_bars=viz_data['h1_bars'],
                            m15_bars=viz_data['m15_bars'],
                            zones=viz_data['zones'],
                            hvn_pocs=viz_data['hvn_pocs']
                        )
                        
                        # Add to PDF
                        pdf.savefig(fig, facecolor=COLORS['dark_bg'])
                        plt.close(fig)
                        
                    except Exception as e:
                        logger.warning(f"Skipping trade {trade.trade_id}: {e}")
                        continue
                
                # Set PDF metadata
                d = pdf.infodict()
                d['Title'] = f'EPOCH Backtest Report'
                d['Author'] = 'XIII Trading LLC'
                d['Subject'] = f'Backtest results: {len(trades)} trades'
                d['CreationDate'] = datetime.now()
            
            logger.info(f"Saved batch PDF: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting batch: {e}")
            raise
    
    def _create_summary_page(self, trades: List) -> plt.Figure:
        """
        Create a summary page for batch export.
        
        Args:
            trades: List of TradeRecord objects
            
        Returns:
            matplotlib Figure with summary statistics
        """
        fig = plt.figure(figsize=(PAGE_WIDTH, PAGE_HEIGHT), 
                        facecolor=COLORS['dark_bg'])
        
        # Calculate statistics
        total_trades = len(trades)
        winners = [t for t in trades if t.win]
        losers = [t for t in trades if not t.win]
        
        win_rate = len(winners) / total_trades * 100 if total_trades > 0 else 0
        total_pnl_dollars = sum(t.pnl_dollars for t in trades)
        total_pnl_r = sum(t.pnl_r for t in trades)
        avg_pnl_r = total_pnl_r / total_trades if total_trades > 0 else 0
        
        avg_winner = sum(t.pnl_r for t in winners) / len(winners) if winners else 0
        avg_loser = sum(t.pnl_r for t in losers) / len(losers) if losers else 0
        
        gross_profit = sum(t.pnl_dollars for t in winners)
        gross_loss = abs(sum(t.pnl_dollars for t in losers))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Date range
        dates = sorted([t.date for t in trades])
        date_range = f"{dates[0]} to {dates[-1]}"
        
        # Unique tickers
        tickers = sorted(set(t.ticker for t in trades))
        
        # Model breakdown
        model_counts = {}
        for t in trades:
            model_counts[t.model] = model_counts.get(t.model, 0) + 1
        
        # Direction breakdown
        long_count = sum(1 for t in trades if t.direction == 'LONG')
        short_count = sum(1 for t in trades if t.direction == 'SHORT')
        
        # Create layout
        ax = fig.add_subplot(111)
        ax.set_facecolor(COLORS['dark_bg'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Title
        ax.text(0.5, 0.95, 'EPOCH BACKTEST REPORT', 
               color=COLORS['text_primary'], fontsize=20, fontweight='bold',
               ha='center', va='top')
        
        ax.text(0.5, 0.90, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
               color='#888888', fontsize=10, ha='center', va='top')
        
        # Overview section
        y = 0.82
        line_height = 0.035
        
        ax.text(0.1, y, 'OVERVIEW', color='#ff9800', fontsize=14, fontweight='bold')
        y -= line_height * 1.5
        
        overview_items = [
            ('Date Range:', date_range),
            ('Total Trades:', str(total_trades)),
            ('Tickers:', ', '.join(tickers[:5]) + ('...' if len(tickers) > 5 else '')),
        ]
        
        for label, value in overview_items:
            ax.text(0.1, y, label, color='#888888', fontsize=11)
            ax.text(0.35, y, value, color=COLORS['text_primary'], fontsize=11)
            y -= line_height
        
        # Performance section
        y -= line_height
        ax.text(0.1, y, 'PERFORMANCE', color='#ff9800', fontsize=14, fontweight='bold')
        y -= line_height * 1.5
        
        pnl_color = '#26a69a' if total_pnl_dollars >= 0 else '#ef5350'
        
        perf_items = [
            ('Win Rate:', f'{win_rate:.1f}%'),
            ('Total P&L ($):', f'${total_pnl_dollars:+,.2f}', pnl_color),
            ('Total P&L (R):', f'{total_pnl_r:+.2f}R', pnl_color),
            ('Avg P&L (R):', f'{avg_pnl_r:+.2f}R'),
            ('Avg Winner:', f'{avg_winner:+.2f}R'),
            ('Avg Loser:', f'{avg_loser:+.2f}R'),
            ('Profit Factor:', f'{profit_factor:.2f}'),
        ]
        
        for item in perf_items:
            label, value = item[0], item[1]
            color = item[2] if len(item) > 2 else COLORS['text_primary']
            ax.text(0.1, y, label, color='#888888', fontsize=11)
            ax.text(0.35, y, value, color=color, fontsize=11)
            y -= line_height
        
        # Breakdown section (right column)
        y = 0.82
        
        ax.text(0.55, y, 'BREAKDOWN', color='#ff9800', fontsize=14, fontweight='bold')
        y -= line_height * 1.5
        
        ax.text(0.55, y, 'By Direction:', color='#888888', fontsize=11)
        y -= line_height
        ax.text(0.6, y, f'LONG: {long_count}  |  SHORT: {short_count}', 
               color=COLORS['text_primary'], fontsize=10)
        y -= line_height * 1.5
        
        ax.text(0.55, y, 'By Model:', color='#888888', fontsize=11)
        y -= line_height
        
        for model, count in sorted(model_counts.items()):
            ax.text(0.6, y, f'{model}: {count}', color=COLORS['text_primary'], fontsize=10)
            y -= line_height
        
        # Win/Loss section
        y -= line_height
        ax.text(0.55, y, 'Results:', color='#888888', fontsize=11)
        y -= line_height
        ax.text(0.6, y, f'Winners: {len(winners)}  |  Losers: {len(losers)}',
               color=COLORS['text_primary'], fontsize=10)
        
        # Trade list preview
        y = 0.35
        ax.axhline(y + 0.02, color='#333333', linewidth=1, xmin=0.05, xmax=0.95)
        
        ax.text(0.5, y, 'TRADE LIST (first 10)', color='#ff9800', fontsize=12, 
               fontweight='bold', ha='center')
        y -= line_height * 1.5
        
        # Header
        headers = ['Date', 'Ticker', 'Model', 'Dir', 'P&L (R)', 'Result']
        x_positions = [0.08, 0.25, 0.40, 0.52, 0.65, 0.82]
        
        for header, x in zip(headers, x_positions):
            ax.text(x, y, header, color='#888888', fontsize=9, fontweight='bold')
        
        y -= line_height
        
        # Trade rows (first 10)
        for trade in trades[:10]:
            result_color = '#26a69a' if trade.win else '#ef5350'
            result_text = 'WIN' if trade.win else 'LOSS'
            
            values = [
                trade.date,
                trade.ticker,
                trade.model,
                trade.direction,
                f'{trade.pnl_r:+.2f}R',
                result_text
            ]
            colors = [
                COLORS['text_primary'],
                COLORS['text_primary'],
                COLORS['text_primary'],
                COLORS['text_primary'],
                result_color,
                result_color
            ]
            
            for val, x, col in zip(values, x_positions, colors):
                ax.text(x, y, str(val), color=col, fontsize=8)
            
            y -= line_height * 0.9
        
        if len(trades) > 10:
            ax.text(0.5, y - line_height, f'... and {len(trades) - 10} more trades',
                   color='#666666', fontsize=9, ha='center')
        
        return fig


# =============================================================================
# STANDALONE TEST
# =============================================================================

def main():
    """Test the PDF exporter with mock data"""
    
    # Create mock trade
    class MockTrade:
        trade_id = "2024-01-15_SPY_EPCH1_1"
        date = "2024-01-15"
        ticker = "SPY"
        model = "EPCH1"
        zone_type = "PRIMARY"
        direction = "LONG"
        zone_high = 475.50
        zone_low = 474.00
        zone_poc = 474.75
        entry_price = 474.50
        entry_time = "09:45:00"
        stop_price = 473.50
        target_3r = 477.50
        target_calc = 478.00
        target_used = "3R"
        target_price = 477.50
        exit_price = 476.80
        exit_time = "11:30:00"
        exit_reason = "TARGET_3R"
        pnl_dollars = 230.00
        pnl_r = 2.3
        risk = 100.00
        win = True
        is_long = True
        duration_minutes = 105
    
    # Create multiple mock trades for batch test
    trades = []
    for i in range(5):
        trade = MockTrade()
        trade.trade_id = f"2024-01-{15+i}_SPY_EPCH{(i%4)+1}_{i+1}"
        trade.date = f"2024-01-{15+i}"
        trade.model = f"EPCH{(i%4)+1}"
        trade.win = i % 2 == 0
        trade.pnl_r = 2.0 if trade.win else -1.0
        trade.pnl_dollars = 200.0 if trade.win else -100.0
        trades.append(trade)
    
    # Test summary page
    exporter = BacktestPDFExporter('/tmp/backtest_test')
    fig = exporter._create_summary_page(trades)
    fig.savefig('/tmp/backtest_test/summary_test.pdf', format='pdf',
               facecolor=COLORS['dark_bg'])
    plt.close(fig)
    
    print("Test summary page saved to /tmp/backtest_test/summary_test.pdf")


if __name__ == "__main__":
    main()

"""
PDF Generator for Epoch Analysis Tool.

Creates multi-page PDF reports from analysis results:
- One page per ticker/anchor combination
- Landscape orientation for detailed charts
- Summary page with all tickers

Uses matplotlib.backends.backend_pdf.PdfPages for PDF generation.
"""

import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from config.visualization_config import COLORS, DPI, FIGURE_WIDTH, FIGURE_HEIGHT
from components.chart_builder import AnalysisChartBuilder
from components.chart_data_fetcher import ChartDataFetcher

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generate multi-page PDF reports from analysis results."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize PDF generator.

        Args:
            output_dir: Directory for PDF output. Defaults to current directory.
        """
        self.output_dir = output_dir or Path(".")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        results: Dict[str, List[Dict]],
        filename: Optional[str] = None,
        include_summary: bool = True
    ) -> Tuple[Optional[Path], bytes]:
        """
        Generate PDF report from analysis results.

        Args:
            results: Dict with 'index' and 'custom' keys containing result lists
            filename: Optional custom filename (without extension)
            include_summary: Whether to include summary page at start

        Returns:
            Tuple of (output_path, pdf_bytes)
        """
        # Generate filename
        if not filename:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
            filename = f"epoch_analysis_report_{timestamp}"

        output_path = self.output_dir / f"{filename}.pdf"

        # Collect all successful results
        all_results = []

        # Add custom ticker results
        for result in results.get("custom", []):
            if result.get("success"):
                all_results.append(result)

        if not all_results:
            logger.warning("No successful results to include in report")
            return None, b''

        logger.info(f"Generating PDF report for {len(all_results)} tickers")

        # Create PDF in memory first
        pdf_buffer = io.BytesIO()

        with PdfPages(pdf_buffer) as pdf:
            # Summary page (optional)
            if include_summary and len(all_results) > 0:
                summary_fig = self._create_summary_page(all_results, results.get("index", []))
                pdf.savefig(
                    summary_fig, dpi=DPI, facecolor=COLORS['dark_bg'],
                    edgecolor='none', bbox_inches='tight', orientation='landscape'
                )
                plt.close(summary_fig)

            # Individual ticker pages
            for i, result in enumerate(all_results):
                ticker = result.get("ticker", "Unknown")
                logger.info(f"[{i+1}/{len(all_results)}] Building chart for {ticker}...")

                try:
                    fig = self._create_ticker_page(result)
                    if fig:
                        pdf.savefig(
                            fig, dpi=DPI, facecolor=COLORS['dark_bg'],
                            edgecolor='none', bbox_inches='tight', orientation='landscape'
                        )
                        plt.close(fig)
                except Exception as e:
                    logger.error(f"Failed to create page for {ticker}: {e}")
                    continue

        # Get PDF bytes
        pdf_buffer.seek(0)
        pdf_bytes = pdf_buffer.getvalue()

        # Also save to file
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)

        logger.info(f"PDF report saved to {output_path} ({len(pdf_bytes) / 1024:.1f} KB)")

        return output_path, pdf_bytes

    def generate_report_bytes(
        self,
        results: Dict[str, List[Dict]],
        include_summary: bool = True
    ) -> bytes:
        """
        Generate PDF report and return as bytes (for Streamlit download).

        Args:
            results: Dict with 'index' and 'custom' keys containing result lists
            include_summary: Whether to include summary page

        Returns:
            PDF file as bytes
        """
        _, pdf_bytes = self.generate_report(
            results=results,
            include_summary=include_summary
        )
        return pdf_bytes

    def _create_summary_page(
        self,
        custom_results: List[Dict],
        index_results: List[Dict]
    ) -> plt.Figure:
        """Create summary page with overview of all tickers."""
        fig = plt.figure(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT), facecolor=COLORS['dark_bg'])

        # Title
        fig.suptitle(
            'EPOCH ANALYSIS REPORT - SUMMARY',
            color=COLORS['text_primary'], fontsize=20, fontweight='bold', y=0.95
        )

        # Subtitle
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        fig.text(0.5, 0.90, f'Generated: {date_str}', color=COLORS['text_muted'],
                fontsize=12, ha='center')

        # Create axes for tables
        ax = fig.add_axes([0.05, 0.10, 0.90, 0.75])
        ax.set_facecolor(COLORS['dark_bg'])
        ax.axis('off')

        # Index tickers section
        y_pos = 0.95
        ax.text(0.05, y_pos, 'INDEX TICKERS', color=COLORS['text_muted'],
               fontsize=14, fontweight='bold', transform=ax.transAxes)

        y_pos -= 0.06
        headers = ['Ticker', 'Direction', 'Price']
        x_positions = [0.05, 0.20, 0.35]

        for i, header in enumerate(headers):
            ax.text(x_positions[i], y_pos, header, color=COLORS['text_muted'],
                   fontsize=10, fontweight='bold', transform=ax.transAxes)

        y_pos -= 0.04
        for result in index_results:
            ticker = result.get("ticker", "")
            direction = result.get("direction", "N/A")
            price = result.get("price", 0)

            ax.text(x_positions[0], y_pos, ticker, color=COLORS['text_primary'],
                   fontsize=10, transform=ax.transAxes)

            dir_color = COLORS['bull'] if 'Bull' in str(direction) else (
                COLORS['bear'] if 'Bear' in str(direction) else COLORS['neutral']
            )
            ax.text(x_positions[1], y_pos, str(direction), color=dir_color,
                   fontsize=10, fontweight='bold', transform=ax.transAxes)

            ax.text(x_positions[2], y_pos, f"${price:.2f}" if price else "-",
                   color=COLORS['text_primary'], fontsize=10, transform=ax.transAxes)

            y_pos -= 0.035

        # Custom tickers section
        y_pos -= 0.06
        ax.text(0.05, y_pos, 'CUSTOM TICKERS', color=COLORS['text_muted'],
               fontsize=14, fontweight='bold', transform=ax.transAxes)

        y_pos -= 0.06
        headers = ['Ticker', 'Direction', 'Price', 'Anchor', 'Zones', 'Bull POC', 'Bear POC']
        x_positions = [0.05, 0.15, 0.27, 0.40, 0.55, 0.65, 0.80]

        for i, header in enumerate(headers):
            ax.text(x_positions[i], y_pos, header, color=COLORS['text_muted'],
                   fontsize=10, fontweight='bold', transform=ax.transAxes)

        y_pos -= 0.04
        for result in custom_results:
            if not result.get("success"):
                continue

            ticker = result.get("ticker", "")
            direction = result.get("direction", "N/A")
            price = result.get("price", 0)
            anchor = result.get("anchor_date", "N/A")
            zones = result.get("zones_count", 0)
            bull_poc = result.get("bull_poc", "N/A")
            bear_poc = result.get("bear_poc", "N/A")

            ax.text(x_positions[0], y_pos, ticker, color=COLORS['text_primary'],
                   fontsize=10, transform=ax.transAxes)

            dir_color = COLORS['bull'] if 'Bull' in str(direction) else (
                COLORS['bear'] if 'Bear' in str(direction) else COLORS['neutral']
            )
            ax.text(x_positions[1], y_pos, str(direction), color=dir_color,
                   fontsize=10, fontweight='bold', transform=ax.transAxes)

            ax.text(x_positions[2], y_pos, f"${price:.2f}" if price else "-",
                   color=COLORS['text_primary'], fontsize=10, transform=ax.transAxes)

            ax.text(x_positions[3], y_pos, str(anchor),
                   color=COLORS['text_muted'], fontsize=9, transform=ax.transAxes)

            ax.text(x_positions[4], y_pos, str(zones),
                   color=COLORS['text_primary'], fontsize=10, transform=ax.transAxes)

            ax.text(x_positions[5], y_pos, str(bull_poc),
                   color=COLORS['bull'], fontsize=10, transform=ax.transAxes)

            ax.text(x_positions[6], y_pos, str(bear_poc),
                   color=COLORS['bear'], fontsize=10, transform=ax.transAxes)

            y_pos -= 0.035

            # Stop if we run out of space
            if y_pos < 0.05:
                ax.text(0.5, 0.02, f'... and {len(custom_results) - custom_results.index(result) - 1} more',
                       color=COLORS['text_muted'], fontsize=10, ha='center', transform=ax.transAxes)
                break

        return fig

    def _create_ticker_page(self, result: Dict) -> Optional[plt.Figure]:
        """Create a chart page for a single ticker result."""
        builder = AnalysisChartBuilder()

        try:
            # Extract data from result
            hvn_result = result.get("hvn_result")
            anchor_date = hvn_result.start_date if hvn_result else None
            ticker = result.get("ticker", "Unknown")

            # Fetch H1 candle data and volume profile for visualization
            candle_data = None
            volume_profile = None

            if anchor_date:
                try:
                    logger.info(f"  Fetching chart data for {ticker}...")
                    fetcher = ChartDataFetcher()
                    chart_data = fetcher.fetch_chart_data(
                        ticker=ticker,
                        epoch_start_date=anchor_date
                    )
                    candle_data = chart_data.candle_bars
                    volume_profile = chart_data.volume_profile
                    logger.info(f"  Got {len(candle_data)} candles, {len(volume_profile)} VP levels")
                except Exception as e:
                    logger.warning(f"  Failed to fetch chart data for {ticker}: {e}")

            fig = builder.build(
                ticker=ticker,
                anchor_date=anchor_date,
                market_structure=result.get("market_structure"),
                bar_data=result.get("bar_data"),
                hvn_result=hvn_result,
                filtered_zones=result.get("filtered_zones", []),
                primary_setup=result.get("primary_setup"),
                secondary_setup=result.get("secondary_setup"),
                candle_data=candle_data,
                volume_profile=volume_profile,
                notes="",
                preview_mode=False  # Full resolution for PDF
            )
            return fig
        except Exception as e:
            logger.error(f"Failed to build chart: {e}")
            builder.close()
            return None


def generate_pdf_report(
    results: Dict[str, List[Dict]],
    output_dir: Optional[Path] = None,
    filename: Optional[str] = None
) -> Tuple[Optional[Path], bytes]:
    """
    Convenience function to generate PDF report.

    Args:
        results: Analysis results from PipelineRunner
        output_dir: Output directory
        filename: Custom filename (without extension)

    Returns:
        Tuple of (output_path, pdf_bytes)
    """
    generator = PDFReportGenerator(output_dir)
    return generator.generate_report(results, filename)


def generate_pdf_bytes(results: Dict[str, List[Dict]]) -> bytes:
    """
    Generate PDF and return as bytes for Streamlit download.

    Args:
        results: Analysis results from PipelineRunner

    Returns:
        PDF file as bytes
    """
    generator = PDFReportGenerator()
    return generator.generate_report_bytes(results)

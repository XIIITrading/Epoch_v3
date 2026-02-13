"""
Epoch Backtest Journal - Primary vs Secondary Report Generator
Creates single-page PDF report and Excel worksheet with raw data.
Shows both "All Trades" and "Winners Only" analysis views.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for PDF generation

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import REPORTS_DIR, REPORT_DPI, REPORT_FIGSIZE
from config.theme import COLORS, FONTS, get_dark_style
from .analyzer import AnalysisResult, AnalysisView, ModelStats, ZoneTypeStats


class PrimarySecondaryReport:
    """
    Generates single-page PDF report and Excel data for Primary vs Secondary zone analysis.
    Shows both All Trades (Monte Carlo) and Winners Only views.
    """

    def __init__(self, result: AnalysisResult):
        """
        Initialize report generator.

        Args:
            result: Analysis result from PrimarySecondaryAnalyzer
        """
        self.result = result
        self._apply_theme()

    def _apply_theme(self):
        """Apply dark theme to matplotlib."""
        plt.rcParams.update(get_dark_style())
        plt.rcParams['font.family'] = FONTS['family']

    def generate_pdf_page(self, pdf: PdfPages) -> None:
        """
        Generate a single PDF page for this analysis with both views.

        Args:
            pdf: PdfPages object to add page to
        """
        fig = plt.figure(figsize=REPORT_FIGSIZE, facecolor=COLORS['dark_bg'])

        # Layout: Header on top, then two columns for All Trades vs Winners Only
        # Row 0: Header (spans both columns)
        # Row 1: All Trades Model Table | Winners Only Model Table
        # Row 2: All Trades Zone Table | Winners Only Zone Table
        # Row 3: Net R Comparison Chart (spans both columns)
        gs = fig.add_gridspec(
            nrows=4, ncols=2,
            height_ratios=[0.10, 0.30, 0.30, 0.30],
            width_ratios=[0.5, 0.5],
            hspace=0.20, wspace=0.08,
            left=0.03, right=0.97, top=0.96, bottom=0.04
        )

        # Header (spans both columns)
        ax_header = fig.add_subplot(gs[0, :])
        self._draw_header(ax_header)

        # ALL TRADES - Model Table (left, row 1)
        ax_all_model = fig.add_subplot(gs[1, 0])
        self._draw_model_table(ax_all_model, self.result.all_trades, "All Trades - By Model")

        # WINNERS ONLY - Model Table (right, row 1)
        ax_win_model = fig.add_subplot(gs[1, 1])
        self._draw_model_table(ax_win_model, self.result.winners_only, "Winners Only - By Model")

        # ALL TRADES - Zone Table (left, row 2)
        ax_all_zone = fig.add_subplot(gs[2, 0])
        self._draw_zone_table(ax_all_zone, self.result.all_trades, "All Trades - By Zone")

        # WINNERS ONLY - Zone Table (right, row 2)
        ax_win_zone = fig.add_subplot(gs[2, 1])
        self._draw_zone_table(ax_win_zone, self.result.winners_only, "Winners Only - By Zone")

        # Comparison Charts (bottom row, spans both columns)
        ax_comparison = fig.add_subplot(gs[3, :])
        self._draw_comparison_chart(ax_comparison)

        pdf.savefig(fig, facecolor=COLORS['dark_bg'], dpi=REPORT_DPI)
        plt.close(fig)

    def generate_standalone_pdf(self, output_path: Path = None) -> Path:
        """
        Generate standalone PDF report (single page).

        Args:
            output_path: Output file path. Auto-generates if not provided.

        Returns:
            Path to generated PDF file
        """
        if output_path is None:
            output_path = self._generate_output_path("pdf")

        with PdfPages(output_path) as pdf:
            self.generate_pdf_page(pdf)

        print(f"PDF generated: {output_path}")
        return output_path

    # Alias for backwards compatibility
    def generate(self, output_path: Path = None) -> Path:
        """Alias for generate_standalone_pdf."""
        return self.generate_standalone_pdf(output_path)

    def export_to_excel(self, exporter: 'ExcelExporter') -> None:
        """
        Export analysis data to Excel worksheet with both views.

        Args:
            exporter: ExcelExporter instance with open workbook
        """
        from utils.excel_export import ExcelExporter

        # Create worksheet
        ws = exporter.add_worksheet(
            name="Prim vs Sec",
            title="Primary vs Secondary Zone Analysis",
            overwrite=True
        )

        current_row = 3  # Start after title

        # Date range info
        if self.result.start_date and self.result.end_date:
            if self.result.start_date == self.result.end_date:
                date_info = f"Date: {self.result.start_date}"
            else:
                date_info = f"Date Range: {self.result.start_date} to {self.result.end_date}"
        else:
            date_info = "All Available Data"

        ws.cell(row=current_row, column=1, value=date_info)
        ws.cell(row=current_row, column=1).font = exporter.STYLES['subheader']['font']
        current_row += 2

        # ========== ALL TRADES VIEW ==========
        current_row = self._write_view_to_excel(
            ws, exporter, self.result.all_trades, current_row,
            section_title="ALL TRADES (Monte Carlo Raw)"
        )

        current_row += 1  # Add spacing between views

        # ========== WINNERS ONLY VIEW ==========
        current_row = self._write_view_to_excel(
            ws, exporter, self.result.winners_only, current_row,
            section_title="WINNERS ONLY"
        )

        # ========== RAW TRADES SECTION ==========
        if self.result.raw_trades:
            current_row += 1
            ws.cell(row=current_row, column=1, value="Raw Trade Data")
            exporter._apply_style(ws.cell(row=current_row, column=1), 'subheader')
            current_row += 1

            # Convert to DataFrame for writing
            df = pd.DataFrame(self.result.raw_trades)

            # Select columns to include
            columns_to_show = [
                'trade_id', 'date', 'ticker', 'model', 'zone_type', 'direction',
                'entry_price', 'entry_time', 'stop_price', 'exit_price', 'exit_time',
                'exit_reason', 'pnl_r', 'is_winner'
            ]
            columns_to_show = [c for c in columns_to_show if c in df.columns]
            df = df[columns_to_show]

            current_row = exporter.write_dataframe(
                ws, df,
                start_row=current_row,
                highlight_columns={'pnl_r': 'value'}
            )

        print(f"  Added worksheet: Prim vs Sec")

    def _write_view_to_excel(
        self,
        ws,
        exporter,
        view: AnalysisView,
        start_row: int,
        section_title: str
    ) -> int:
        """Write a single analysis view to Excel."""
        current_row = start_row

        # Section header (prefix with space to prevent Excel formula interpretation)
        ws.cell(row=current_row, column=1, value=f"[ {section_title} ({view.trade_count} trades) ]")
        exporter._apply_style(ws.cell(row=current_row, column=1), 'title')
        current_row += 2

        # Model Performance Table
        if view.model_stats:
            model_data = [
                {
                    'Model': s.model,
                    'Zone Type': s.zone_type,
                    'Trades': s.trades,
                    'Wins': s.wins,
                    'Losses': s.losses,
                    'Win Rate': f"{s.win_rate * 100:.1f}%",
                    'Net R': round(s.net_r, 2),
                    'Expectancy': round(s.expectancy_r, 3),
                    'Avg Win R': round(s.avg_win_r, 2),
                    'Avg Loss R': round(s.avg_loss_r, 2),
                }
                for s in view.model_stats
            ]

            current_row = exporter.write_summary_table(
                ws, model_data,
                columns=['Model', 'Zone Type', 'Trades', 'Wins', 'Losses', 'Win Rate', 'Net R', 'Expectancy', 'Avg Win R', 'Avg Loss R'],
                start_row=current_row,
                title="Performance by Model",
                highlight_columns=['Net R', 'Expectancy']
            )

        # Zone Type Summary Table
        if view.zone_stats:
            zone_data = [
                {
                    'Zone Type': s.zone_type,
                    'Models': ', '.join(s.models),
                    'Trades': s.trades,
                    'Wins': s.wins,
                    'Losses': s.losses,
                    'Win Rate': f"{s.win_rate * 100:.1f}%",
                    'Net R': round(s.net_r, 2),
                    'Expectancy': round(s.expectancy_r, 3),
                }
                for s in view.zone_stats
            ]

            total_row = None
            if view.overall_stats:
                o = view.overall_stats
                total_row = {
                    'Zone Type': 'TOTAL',
                    'Models': 'ALL',
                    'Trades': o.get('total_trades', 0),
                    'Wins': o.get('wins', 0),
                    'Losses': o.get('losses', 0),
                    'Win Rate': f"{o.get('win_rate', 0) * 100:.1f}%",
                    'Net R': round(o.get('net_r', 0), 2),
                    'Expectancy': round(o.get('expectancy_r', 0), 3),
                }

            current_row = exporter.write_summary_table(
                ws, zone_data,
                columns=['Zone Type', 'Models', 'Trades', 'Wins', 'Losses', 'Win Rate', 'Net R', 'Expectancy'],
                start_row=current_row,
                title="Summary by Zone Type",
                total_row=total_row,
                highlight_columns=['Net R', 'Expectancy']
            )

        return current_row

    def _generate_output_path(self, extension: str) -> Path:
        """Generate output path based on date range."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.result.start_date and self.result.end_date:
            if self.result.start_date == self.result.end_date:
                date_str = self.result.start_date.strftime("%Y-%m-%d")
            else:
                date_str = f"{self.result.start_date.strftime('%Y%m%d')}_to_{self.result.end_date.strftime('%Y%m%d')}"
        else:
            date_str = "all_data"
        return REPORTS_DIR / f"prim_v_sec_{date_str}_{timestamp}.{extension}"

    def _draw_header(self, ax: plt.Axes):
        """Draw report header."""
        ax.set_facecolor(COLORS['dark_bg'])
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 1.5)
        ax.axis('off')

        # Title
        ax.text(
            5, 1.1, "EPOCH TRADING SYSTEM",
            fontsize=FONTS['title_size'] + 2,
            fontweight='bold',
            color=COLORS['text_header'],
            ha='center', va='center'
        )

        # Subtitle
        ax.text(
            5, 0.65, "Primary vs Secondary Zone Performance",
            fontsize=FONTS['header_size'],
            color=COLORS['text_primary'],
            ha='center', va='center'
        )

        # Date range
        if self.result.start_date and self.result.end_date:
            if self.result.start_date == self.result.end_date:
                date_text = f"Date: {self.result.start_date.strftime('%B %d, %Y')}"
            else:
                date_text = (
                    f"{self.result.start_date.strftime('%b %d, %Y')} - "
                    f"{self.result.end_date.strftime('%b %d, %Y')} "
                    f"({self.result.total_days} days)"
                )
        else:
            date_text = "All Available Data"

        ax.text(
            5, 0.2, date_text,
            fontsize=FONTS['body_size'],
            color=COLORS['text_muted'],
            ha='center', va='center'
        )

    def _draw_model_table(self, ax: plt.Axes, view: AnalysisView, title: str):
        """Draw the model performance table for a specific view."""
        ax.set_facecolor(COLORS['dark_bg'])
        ax.axis('off')

        ax.set_title(
            title,
            fontsize=FONTS['body_size'],
            fontweight='bold',
            color=COLORS['text_header'],
            loc='left',
            pad=6
        )

        if not view.model_stats:
            ax.text(0.5, 0.5, "No trade data available",
                    fontsize=FONTS['body_size'], color=COLORS['text_muted'],
                    ha='center', va='center', transform=ax.transAxes)
            return

        columns = ['Model', 'Zone', 'Trades', 'Wins', 'Win%', 'Net R', 'Exp']
        cell_data = []
        cell_colors = []

        for i, stat in enumerate(view.model_stats):
            row = [
                stat.model,
                stat.zone_type[:3],  # Shortened: PRI/SEC
                str(stat.trades),
                str(stat.wins),
                f"{stat.win_rate * 100:.0f}%",
                f"{stat.net_r:+.1f}",
                f"{stat.expectancy_r:+.2f}"
            ]
            cell_data.append(row)

            bg_color = COLORS['table_row_alt'] if i % 2 else COLORS['table_bg']
            row_colors = [bg_color] * len(columns)

            if stat.net_r > 0:
                row_colors[5] = self._blend_color(bg_color, COLORS['positive'], 0.3)
            elif stat.net_r < 0:
                row_colors[5] = self._blend_color(bg_color, COLORS['negative'], 0.3)

            cell_colors.append(row_colors)

        table = ax.table(
            cellText=cell_data,
            colLabels=columns,
            cellLoc='center',
            loc='center',
            cellColours=cell_colors,
            colColours=[COLORS['table_header_bg']] * len(columns)
        )

        table.auto_set_font_size(False)
        table.set_fontsize(FONTS['table_size'])
        table.scale(1, 1.5)

        for key, cell in table.get_celld().items():
            cell.set_edgecolor(COLORS['table_border'])
            cell.set_text_props(color=COLORS['text_primary'])
            if key[0] == 0:
                cell.set_text_props(color=COLORS['text_header'], fontweight='bold')

    def _draw_zone_table(self, ax: plt.Axes, view: AnalysisView, title: str):
        """Draw the zone type summary table for a specific view."""
        ax.set_facecolor(COLORS['dark_bg'])
        ax.axis('off')

        ax.set_title(
            title,
            fontsize=FONTS['body_size'],
            fontweight='bold',
            color=COLORS['text_header'],
            loc='left',
            pad=6
        )

        if not view.zone_stats:
            ax.text(0.5, 0.5, "No data",
                    fontsize=FONTS['body_size'], color=COLORS['text_muted'],
                    ha='center', va='center', transform=ax.transAxes)
            return

        columns = ['Zone', 'Models', 'Trades', 'Wins', 'Win%', 'Net R', 'Exp']
        cell_data = []
        cell_colors = []

        for i, stat in enumerate(view.zone_stats):
            row = [
                stat.zone_type,
                ', '.join(stat.models),
                str(stat.trades),
                str(stat.wins),
                f"{stat.win_rate * 100:.0f}%",
                f"{stat.net_r:+.1f}",
                f"{stat.expectancy_r:+.2f}"
            ]
            cell_data.append(row)

            if stat.zone_type == "PRIMARY":
                zone_color = self._blend_color(COLORS['table_bg'], COLORS['primary_zone'], 0.12)
            else:
                zone_color = self._blend_color(COLORS['table_bg'], COLORS['secondary_zone'], 0.12)

            row_colors = [zone_color] * len(columns)
            if stat.net_r > 0:
                row_colors[5] = self._blend_color(zone_color, COLORS['positive'], 0.3)
            elif stat.net_r < 0:
                row_colors[5] = self._blend_color(zone_color, COLORS['negative'], 0.3)

            cell_colors.append(row_colors)

        # Total row
        if view.overall_stats:
            o = view.overall_stats
            total_row = [
                "TOTAL", "ALL",
                str(o.get('total_trades', 0)), str(o.get('wins', 0)),
                f"{o.get('win_rate', 0) * 100:.0f}%",
                f"{o.get('net_r', 0):+.1f}",
                f"{o.get('expectancy_r', 0):+.2f}"
            ]
            cell_data.append(total_row)

            total_color = COLORS['table_highlight']
            total_colors = [total_color] * len(columns)
            if o.get('net_r', 0) > 0:
                total_colors[5] = self._blend_color(total_color, COLORS['positive'], 0.4)
            elif o.get('net_r', 0) < 0:
                total_colors[5] = self._blend_color(total_color, COLORS['negative'], 0.4)
            cell_colors.append(total_colors)

        table = ax.table(
            cellText=cell_data,
            colLabels=columns,
            cellLoc='center',
            loc='center',
            cellColours=cell_colors,
            colColours=[COLORS['table_header_bg']] * len(columns)
        )

        table.auto_set_font_size(False)
        table.set_fontsize(FONTS['table_size'])
        table.scale(1, 1.5)

        for key, cell in table.get_celld().items():
            cell.set_edgecolor(COLORS['table_border'])
            cell.set_text_props(color=COLORS['text_primary'])
            if key[0] == 0:
                cell.set_text_props(color=COLORS['text_header'], fontweight='bold')
            if key[0] == len(cell_data):
                cell.set_text_props(fontweight='bold')

    def _draw_comparison_chart(self, ax: plt.Axes):
        """Draw side-by-side comparison of Net R by zone type for both views."""
        ax.set_facecolor(COLORS['chart_bg'])

        all_zones = self.result.all_trades.zone_stats
        win_zones = self.result.winners_only.zone_stats

        if not all_zones and not win_zones:
            ax.text(0.5, 0.5, "No data", ha='center', va='center', color=COLORS['text_muted'])
            ax.axis('off')
            return

        # Prepare data for grouped bar chart
        zone_types = ['PRIMARY', 'SECONDARY']
        x = range(len(zone_types))
        width = 0.35

        # Get Net R values for each view
        all_net_r = []
        win_net_r = []

        for zone_type in zone_types:
            all_stat = next((s for s in all_zones if s.zone_type == zone_type), None)
            win_stat = next((s for s in win_zones if s.zone_type == zone_type), None)
            all_net_r.append(all_stat.net_r if all_stat else 0)
            win_net_r.append(win_stat.net_r if win_stat else 0)

        # Create grouped bars
        bars1 = ax.bar([i - width/2 for i in x], all_net_r, width,
                       label='All Trades', color=COLORS['neutral'], edgecolor=COLORS['border'])
        bars2 = ax.bar([i + width/2 for i in x], win_net_r, width,
                       label='Winners Only', color=COLORS['positive'], edgecolor=COLORS['border'])

        # Add value labels
        for bar, value in zip(bars1, all_net_r):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + (0.2 if height >= 0 else -0.4),
                    f'{value:+.1f}R', ha='center', va='bottom' if height >= 0 else 'top',
                    fontsize=FONTS['small_size'], color=COLORS['text_primary'], fontweight='bold')

        for bar, value in zip(bars2, win_net_r):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + (0.2 if height >= 0 else -0.4),
                    f'{value:+.1f}R', ha='center', va='bottom' if height >= 0 else 'top',
                    fontsize=FONTS['small_size'], color=COLORS['text_primary'], fontweight='bold')

        ax.axhline(y=0, color=COLORS['text_muted'], linewidth=0.5)
        ax.set_title("Net R Comparison: All Trades vs Winners Only",
                     fontsize=FONTS['body_size'], color=COLORS['text_header'], pad=10)
        ax.set_ylabel("Net R", fontsize=FONTS['small_size'], color=COLORS['text_muted'])
        ax.set_xticks(x)
        ax.set_xticklabels(zone_types)
        ax.tick_params(colors=COLORS['text_muted'])
        ax.legend(loc='upper right', facecolor=COLORS['dark_bg'], edgecolor=COLORS['border'],
                  labelcolor=COLORS['text_primary'])
        ax.spines['bottom'].set_color(COLORS['border'])
        ax.spines['left'].set_color(COLORS['border'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', alpha=0.3, color=COLORS['grid'])

    def _blend_color(self, color1: str, color2: str, factor: float) -> str:
        """Blend two hex colors."""
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(*rgb)

        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)
        blended = tuple(int(rgb1[i] * (1 - factor) + rgb2[i] * factor) for i in range(3))
        return rgb_to_hex(blended)

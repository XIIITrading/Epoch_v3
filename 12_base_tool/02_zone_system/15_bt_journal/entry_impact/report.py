"""
Epoch Backtest Journal - Confluence Analysis Report Generator
Creates single-page PDF report and Excel worksheet showing direction-relative alignment.
XIII Trading LLC
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for PDF generation

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List, Dict
import pandas as pd
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import REPORTS_DIR, REPORT_DPI, REPORT_FIGSIZE
from config.theme import COLORS, FONTS, get_dark_style
from .analyzer import AnalysisResult, FactorAlignment, ConfluenceBucket


class ConfluenceReport:
    """
    Generates single-page PDF report and Excel data for Confluence Analysis.
    Shows direction-relative factor alignment and confluence curve.
    """

    def __init__(self, result: AnalysisResult):
        """
        Initialize report generator.

        Args:
            result: Analysis result from ConfluenceAnalyzer
        """
        self.result = result
        self._apply_theme()

    def _apply_theme(self):
        """Apply dark theme to matplotlib."""
        plt.rcParams.update(get_dark_style())
        plt.rcParams['font.family'] = FONTS['family']

    def generate_pdf_page(self, pdf: PdfPages) -> None:
        """
        Generate a single PDF page for this analysis.

        Args:
            pdf: PdfPages object to add page to
        """
        fig = plt.figure(figsize=REPORT_FIGSIZE, facecolor=COLORS['dark_bg'])

        # Layout:
        # Row 0: Header (10%)
        # Row 1: Summary stats (10%)
        # Row 2: Factor table (left) + Confluence chart (right) (35%)
        # Row 3: Confluence table (25%)
        # Row 4: PineScript lookup box (20%)
        gs = fig.add_gridspec(
            nrows=5, ncols=2,
            height_ratios=[0.10, 0.10, 0.35, 0.25, 0.20],
            width_ratios=[0.5, 0.5],
            hspace=0.15, wspace=0.10,
            left=0.04, right=0.96, top=0.96, bottom=0.04
        )

        # Header (spans both columns)
        ax_header = fig.add_subplot(gs[0, :])
        self._draw_header(ax_header)

        # Summary stats (spans both columns)
        ax_summary = fig.add_subplot(gs[1, :])
        self._draw_summary(ax_summary)

        # Factor alignment table (left)
        ax_factor_table = fig.add_subplot(gs[2, 0])
        self._draw_factor_table(ax_factor_table)

        # Confluence curve chart (right)
        ax_confluence_chart = fig.add_subplot(gs[2, 1])
        self._draw_confluence_chart(ax_confluence_chart)

        # Confluence score table (spans both columns)
        ax_confluence_table = fig.add_subplot(gs[3, :])
        self._draw_confluence_table(ax_confluence_table)

        # PineScript lookup box (spans both columns)
        ax_pinescript = fig.add_subplot(gs[4, :])
        self._draw_pinescript_box(ax_pinescript)

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

    def generate(self, output_path: Path = None) -> Path:
        """Alias for generate_standalone_pdf."""
        return self.generate_standalone_pdf(output_path)

    def export_to_excel(self, exporter) -> None:
        """
        Export analysis data to Excel worksheet.

        Args:
            exporter: ExcelExporter instance with open workbook
        """
        # Create worksheet
        ws = exporter.add_worksheet(
            name="Confluence",
            title="Confluence Analysis - Direction-Relative Alignment",
            overwrite=True
        )

        current_row = 3

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

        # ========== SUMMARY STATISTICS ==========
        ws.cell(row=current_row, column=1, value="Summary Statistics")
        exporter._apply_style(ws.cell(row=current_row, column=1), 'subheader')
        current_row += 1

        coverage_pct = (self.result.trades_with_entry_data / self.result.total_trades * 100) if self.result.total_trades > 0 else 0

        summary_data = [
            {'Metric': 'Total Trades', 'Value': self.result.total_trades},
            {'Metric': 'Trades with Entry Data', 'Value': self.result.trades_with_entry_data},
            {'Metric': 'Coverage %', 'Value': f"{coverage_pct:.1f}%"},
            {'Metric': 'Baseline Win Rate', 'Value': f"{self.result.baseline_win_rate * 100:.1f}%"},
            {'Metric': 'Baseline Expectancy (R)', 'Value': f"{self.result.baseline_expectancy:.3f}"},
            {'Metric': 'Score 5+ Win Rate', 'Value': f"{self.result.score_5_plus_win_rate * 100:.1f}%"},
            {'Metric': 'Score 5+ Trades', 'Value': self.result.score_5_plus_trades},
            {'Metric': 'Score 6+ Win Rate', 'Value': f"{self.result.score_6_plus_win_rate * 100:.1f}%"},
            {'Metric': 'Score 6+ Trades', 'Value': self.result.score_6_plus_trades},
            {'Metric': 'Min Score for +Expectancy', 'Value': self.result.min_score_for_positive_expectancy or 'N/A'},
        ]

        current_row = exporter.write_summary_table(
            ws, summary_data,
            columns=['Metric', 'Value'],
            start_row=current_row,
            title=None
        )

        # ========== FACTOR ALIGNMENT TABLE ==========
        if self.result.factor_alignments:
            current_row += 1
            ws.cell(row=current_row, column=1, value="Factor Alignment (Direction-Relative)")
            exporter._apply_style(ws.cell(row=current_row, column=1), 'subheader')
            current_row += 1

            alignment_data = []
            for f in self.result.factor_alignments:
                alignment_data.append({
                    'Rank': f.edge_rank,
                    'Factor': f.factor_name,
                    'Aligned': f.aligned_trades,
                    'Al. WR%': f"{f.aligned_win_rate * 100:.1f}%",
                    'Al. Exp': f"{f.aligned_avg_pnl_r:+.3f}",
                    'Misaligned': f.misaligned_trades,
                    'Mis. WR%': f"{f.misaligned_win_rate * 100:.1f}%",
                    'Mis. Exp': f"{f.misaligned_avg_pnl_r:+.3f}",
                    'Neutral': f.neutral_trades,
                    'Edge': f"{f.alignment_edge * 100:+.1f}%"
                })

            current_row = exporter.write_summary_table(
                ws, alignment_data,
                columns=['Rank', 'Factor', 'Aligned', 'Al. WR%', 'Al. Exp', 'Misaligned', 'Mis. WR%', 'Mis. Exp', 'Neutral', 'Edge'],
                start_row=current_row,
                title=None,
                highlight_columns=['Edge']
            )

        # ========== CONFLUENCE SCORE TABLE ==========
        if self.result.confluence_buckets:
            current_row += 1
            ws.cell(row=current_row, column=1, value="Confluence Score Breakdown")
            exporter._apply_style(ws.cell(row=current_row, column=1), 'subheader')
            current_row += 1

            bucket_data = []
            for b in self.result.confluence_buckets:
                bucket_data.append({
                    'Score': b.score_label,
                    'Trades': b.trade_count,
                    'Wins': b.wins,
                    'Losses': b.losses,
                    'Win Rate': f"{b.win_rate * 100:.1f}%",
                    'Avg PnL R': f"{b.avg_pnl_r:+.3f}",
                    'Total PnL R': f"{b.total_pnl_r:+.2f}"
                })

            current_row = exporter.write_summary_table(
                ws, bucket_data,
                columns=['Score', 'Trades', 'Wins', 'Losses', 'Win Rate', 'Avg PnL R', 'Total PnL R'],
                start_row=current_row,
                title=None,
                highlight_columns=['Avg PnL R', 'Total PnL R']
            )

        # ========== PINESCRIPT LOOKUP ==========
        current_row += 1
        ws.cell(row=current_row, column=1, value="PineScript Lookup")
        exporter._apply_style(ws.cell(row=current_row, column=1), 'subheader')
        current_row += 1

        lookup_text = self._generate_pinescript_lookup()
        for line in lookup_text.split('\n'):
            ws.cell(row=current_row, column=1, value=line)
            current_row += 1

        # ========== RAW DATA SECTION ==========
        if self.result.raw_data:
            current_row += 2
            ws.cell(row=current_row, column=1, value="Raw Trade Data with Alignments")
            exporter._apply_style(ws.cell(row=current_row, column=1), 'subheader')
            current_row += 1

            # Convert to DataFrame
            df = pd.DataFrame(self.result.raw_data)

            # Add alignment columns
            def get_alignment_status(row, factor):
                alignments = row.get('_alignments', {})
                alignment = alignments.get(factor, {})
                if alignment.get('neutral'):
                    return 'NEUTRAL'
                elif alignment.get('aligned'):
                    return 'ALIGNED'
                else:
                    return 'MISALIGNED'

            for factor in ['m5_structure', 'm15_structure', 'h1_structure', 'h4_structure', 'vwap', 'sma_stack', 'volume', 'volume_delta']:
                col_name = f"{factor}_aligned"
                df[col_name] = df.apply(lambda x: get_alignment_status(x, factor), axis=1)

            # Add confluence score
            df['confluence_score'] = df.apply(lambda x: x.get('_confluence_score', 0), axis=1)

            # Select columns
            columns_to_show = [
                'trade_id', 'date', 'ticker', 'direction', 'pnl_r', 'is_winner',
                'confluence_score',
                'm5_structure_aligned', 'm15_structure_aligned', 'h1_structure_aligned', 'h4_structure_aligned',
                'vwap_aligned', 'sma_stack_aligned', 'volume_aligned', 'volume_delta_aligned',
                'm5_structure', 'm15_structure', 'h1_structure', 'h4_structure',
                'entry_vs_vwap', 'sma9_vs_sma21', 'volume_trend', 'volume_delta_class'
            ]
            columns_to_show = [c for c in columns_to_show if c in df.columns]
            df = df[columns_to_show]

            current_row = exporter.write_dataframe(
                ws, df,
                start_row=current_row,
                highlight_columns={'pnl_r': 'value'}
            )

        print(f"  Added worksheet: Confluence")

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
        return REPORTS_DIR / f"confluence_{date_str}_{timestamp}.{extension}"

    def _draw_header(self, ax: plt.Axes):
        """Draw report header."""
        ax.set_facecolor(COLORS['dark_bg'])
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 1.5)
        ax.axis('off')

        ax.text(
            5, 1.1, "EPOCH TRADING SYSTEM",
            fontsize=FONTS['title_size'] + 2,
            fontweight='bold',
            color=COLORS['text_header'],
            ha='center', va='center'
        )

        ax.text(
            5, 0.65, "Confluence Analysis - Direction-Relative Alignment",
            fontsize=FONTS['header_size'],
            color=COLORS['text_primary'],
            ha='center', va='center'
        )

        if self.result.start_date and self.result.end_date:
            if self.result.start_date == self.result.end_date:
                date_text = f"Date: {self.result.start_date.strftime('%B %d, %Y')}"
            else:
                date_text = (
                    f"{self.result.start_date.strftime('%b %d, %Y')} - "
                    f"{self.result.end_date.strftime('%b %d, %Y')}"
                )
        else:
            date_text = "All Available Data"

        ax.text(
            5, 0.2, date_text,
            fontsize=FONTS['body_size'],
            color=COLORS['text_muted'],
            ha='center', va='center'
        )

    def _draw_summary(self, ax: plt.Axes):
        """Draw summary statistics bar."""
        ax.set_facecolor(COLORS['dark_bg'])
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 1)
        ax.axis('off')

        coverage = (self.result.trades_with_entry_data / self.result.total_trades * 100) if self.result.total_trades > 0 else 0

        stats = [
            (f"Trades: {self.result.total_trades}", 1.0),
            (f"With Data: {self.result.trades_with_entry_data} ({coverage:.0f}%)", 3.0),
            (f"Baseline WR: {self.result.baseline_win_rate * 100:.1f}%", 5.0),
            (f"Baseline Exp: {self.result.baseline_expectancy:+.3f}R", 7.0),
            (f"Score 5+ WR: {self.result.score_5_plus_win_rate * 100:.1f}% (n={self.result.score_5_plus_trades})", 9.5),
            (f"Score 6+ WR: {self.result.score_6_plus_win_rate * 100:.1f}% (n={self.result.score_6_plus_trades})", 12.0),
        ]

        for text, x in stats:
            ax.text(
                x, 0.5, text,
                fontsize=FONTS['body_size'] - 1,
                color=COLORS['text_primary'],
                ha='center', va='center'
            )

    def _draw_factor_table(self, ax: plt.Axes):
        """Draw the factor alignment table."""
        ax.set_facecolor(COLORS['dark_bg'])
        ax.axis('off')

        ax.set_title(
            "Factor Alignment (by Edge)",
            fontsize=FONTS['body_size'],
            fontweight='bold',
            color=COLORS['text_header'],
            loc='left',
            pad=6
        )

        if not self.result.factor_alignments:
            ax.text(0.5, 0.5, "No data available",
                    fontsize=FONTS['body_size'], color=COLORS['text_muted'],
                    ha='center', va='center', transform=ax.transAxes)
            return

        columns = ['Factor', 'Aligned', 'Al.WR%', 'Misalign', 'Mis.WR%', 'Edge']
        cell_data = []
        cell_colors = []

        for i, f in enumerate(self.result.factor_alignments):
            row = [
                f.factor_name,
                str(f.aligned_trades),
                f"{f.aligned_win_rate * 100:.0f}%",
                str(f.misaligned_trades),
                f"{f.misaligned_win_rate * 100:.0f}%",
                f"{f.alignment_edge * 100:+.1f}%"
            ]
            cell_data.append(row)

            bg_color = COLORS['table_row_alt'] if i % 2 else COLORS['table_bg']
            row_colors = [bg_color] * len(columns)

            # Highlight edge column based on value
            if f.alignment_edge > 0.10:
                row_colors[-1] = self._blend_color(bg_color, COLORS['positive'], 0.4)
            elif f.alignment_edge > 0.05:
                row_colors[-1] = self._blend_color(bg_color, COLORS['positive'], 0.2)
            elif f.alignment_edge < 0:
                row_colors[-1] = self._blend_color(bg_color, COLORS['negative'], 0.3)

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
        table.scale(1, 1.4)

        for key, cell in table.get_celld().items():
            cell.set_edgecolor(COLORS['table_border'])
            cell.set_text_props(color=COLORS['text_primary'])
            if key[0] == 0:
                cell.set_text_props(color=COLORS['text_header'], fontweight='bold')

    def _draw_confluence_chart(self, ax: plt.Axes):
        """Draw the confluence score bar chart."""
        ax.set_facecolor(COLORS['chart_bg'])

        if not self.result.confluence_buckets:
            ax.text(0.5, 0.5, "No data", ha='center', va='center', color=COLORS['text_muted'])
            ax.axis('off')
            return

        labels = [b.score_label for b in self.result.confluence_buckets]
        win_rates = [b.win_rate * 100 for b in self.result.confluence_buckets]
        trade_counts = [b.trade_count for b in self.result.confluence_buckets]

        x = range(len(labels))
        baseline = self.result.baseline_win_rate * 100

        # Color bars by performance relative to baseline
        colors = []
        for wr in win_rates:
            if wr >= baseline + 5:
                colors.append(COLORS['positive'])
            elif wr < baseline - 5:
                colors.append(COLORS['negative'])
            else:
                colors.append(COLORS['neutral'])

        bars = ax.bar(x, win_rates, color=colors, edgecolor=COLORS['border'], alpha=0.85)

        # Add labels
        for bar, wr, count in zip(bars, win_rates, trade_counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 1.5,
                    f'{wr:.0f}%\n(n={count})',
                    ha='center', va='bottom',
                    fontsize=FONTS['small_size'] - 1,
                    color=COLORS['text_primary'])

        # Baseline line
        ax.axhline(y=baseline, color=COLORS['text_muted'], linestyle='--', linewidth=1.5)

        ax.set_title("Confluence Score → Win Rate",
                     fontsize=FONTS['body_size'], color=COLORS['text_header'], pad=10)
        ax.set_ylabel("Win Rate %", fontsize=FONTS['small_size'], color=COLORS['text_muted'])
        ax.set_xlabel("Confluence Score", fontsize=FONTS['small_size'], color=COLORS['text_muted'])
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.tick_params(colors=COLORS['text_muted'])

        ax.set_ylim(0, max(win_rates) + 20)

        ax.spines['bottom'].set_color(COLORS['border'])
        ax.spines['left'].set_color(COLORS['border'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', alpha=0.3, color=COLORS['grid'])

    def _draw_confluence_table(self, ax: plt.Axes):
        """Draw the confluence score breakdown table."""
        ax.set_facecolor(COLORS['dark_bg'])
        ax.axis('off')

        ax.set_title(
            "Confluence Score Breakdown",
            fontsize=FONTS['body_size'],
            fontweight='bold',
            color=COLORS['text_header'],
            loc='left',
            pad=6
        )

        if not self.result.confluence_buckets:
            ax.text(0.5, 0.5, "No data available",
                    fontsize=FONTS['body_size'], color=COLORS['text_muted'],
                    ha='center', va='center', transform=ax.transAxes)
            return

        columns = ['Score', 'Trades', 'Wins', 'Losses', 'Win Rate', 'Avg PnL R', 'Total PnL R']
        cell_data = []
        cell_colors = []

        for i, b in enumerate(self.result.confluence_buckets):
            row = [
                b.score_label,
                str(b.trade_count),
                str(b.wins),
                str(b.losses),
                f"{b.win_rate * 100:.0f}%",
                f"{b.avg_pnl_r:+.2f}",
                f"{b.total_pnl_r:+.1f}"
            ]
            cell_data.append(row)

            bg_color = COLORS['table_row_alt'] if i % 2 else COLORS['table_bg']
            row_colors = [bg_color] * len(columns)

            # Highlight expectancy column
            if b.avg_pnl_r > 0:
                row_colors[5] = self._blend_color(bg_color, COLORS['positive'], 0.3)
            elif b.avg_pnl_r < 0:
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
        table.scale(1, 1.3)

        for key, cell in table.get_celld().items():
            cell.set_edgecolor(COLORS['table_border'])
            cell.set_text_props(color=COLORS['text_primary'])
            if key[0] == 0:
                cell.set_text_props(color=COLORS['text_header'], fontweight='bold')

    def _draw_pinescript_box(self, ax: plt.Axes):
        """Draw the PineScript lookup box."""
        ax.set_facecolor(COLORS['notes_bg'])
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Add border
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color(COLORS['border'])

        lookup_text = self._generate_pinescript_lookup()

        ax.text(
            0.02, 0.95, lookup_text,
            fontsize=FONTS['small_size'],
            fontfamily='monospace',
            color=COLORS['text_primary'],
            ha='left', va='top',
            transform=ax.transAxes
        )

    def _generate_pinescript_lookup(self) -> str:
        """Generate PineScript-ready lookup text."""
        if not self.result.confluence_buckets:
            return "// No confluence data available"

        # Build date range string
        if self.result.start_date and self.result.end_date:
            date_range = f"{self.result.start_date.strftime('%b %d')} - {self.result.end_date.strftime('%b %d, %Y')}"
        else:
            date_range = "All Data"

        lines = [
            f"// Epoch Confluence Lookup (Backtest: {date_range}, n={self.result.trades_with_entry_data})",
            "// Score -> Win Rate | Expectancy"
        ]

        # Add each score bucket
        for bucket in sorted(self.result.confluence_buckets, key=lambda x: x.score):
            marker = " <-- Min +Exp" if (self.result.min_score_for_positive_expectancy is not None 
                                          and bucket.score == self.result.min_score_for_positive_expectancy 
                                          and bucket.avg_pnl_r > 0) else ""
            lines.append(f"// {bucket.score_label}: {bucket.win_rate * 100:.0f}% | {bucket.avg_pnl_r:+.2f}R{marker}")

        lines.append(f"//")
        lines.append(f"// Score 5+: {self.result.score_5_plus_win_rate * 100:.0f}% WR (n={self.result.score_5_plus_trades})")
        lines.append(f"// Score 6+: {self.result.score_6_plus_win_rate * 100:.0f}% WR (n={self.result.score_6_plus_trades})")

        return "\n".join(lines)

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
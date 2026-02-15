"""
Epoch Trading System - Chart Preview Panel
Displays charts in paired 2-up layout plus ramp-up and post-trade indicator tables.

Layout:
  Row 1: Daily + 1-Hour  (side by side)
  Row 2: 1-Hour + 15-Minute  (side by side)
  Row 3: 5-Minute Entry + 1-Minute Action  (side by side)
  Row 4: 1-Minute Ramp-Up  (full width)
  Row 5: M1 Ramp-Up Indicators table
  Row 6: M1 Post-Trade Indicators table
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import plotly.graph_objects as go

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import TV_COLORS
from models.highlight import HighlightTrade
from ui.chart_renderer import create_chart_label, render_chart_to_label, RENDER_WIDTH, CHART_HEIGHT
from ui.rampup_table import RampUpTable
from ui.posttrade_table import PostTradeTable


class ChartPreview(QFrame):
    """Panel showing charts in paired 2-up layout with ramp-up table."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area wrapping all content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self._content_layout = QVBoxLayout(container)
        self._content_layout.setContentsMargins(8, 8, 8, 8)
        self._content_layout.setSpacing(6)

        # Trade summary header
        self._summary = QLabel("Select a highlight trade to view charts")
        self._summary.setFont(QFont("Trebuchet MS", 12))
        self._summary.setStyleSheet(f"color: {TV_COLORS['text_muted']}; padding: 8px;")
        self._summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._summary.setWordWrap(True)
        self._content_layout.addWidget(self._summary)

        _section_style = (
            f"color: {TV_COLORS['text_muted']}; font-size: 11px; "
            f"font-weight: bold; padding: 4px 8px; background: {TV_COLORS['bg_secondary']};"
        )

        # Render width for paired charts (half width each)
        self._pair_render_width = RENDER_WIDTH // 2

        # ---- Row 1: Daily + 1-Hour ----
        row1_label = QLabel("Daily  +  1-Hour")
        row1_label.setStyleSheet(_section_style)
        self._content_layout.addWidget(row1_label)

        row1 = QWidget()
        row1_layout = QHBoxLayout(row1)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(4)

        self._daily_chart = create_chart_label(min_height=200)
        self._h1_chart_row1 = create_chart_label(min_height=200)
        row1_layout.addWidget(self._daily_chart, stretch=1)
        row1_layout.addWidget(self._h1_chart_row1, stretch=1)
        self._content_layout.addWidget(row1)

        # ---- Row 2: 1-Hour + 15-Minute ----
        row2_label = QLabel("1-Hour  +  15-Minute")
        row2_label.setStyleSheet(_section_style)
        self._content_layout.addWidget(row2_label)

        row2 = QWidget()
        row2_layout = QHBoxLayout(row2)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.setSpacing(4)

        self._h1_chart_row2 = create_chart_label(min_height=200)
        self._m15_chart = create_chart_label(min_height=200)
        row2_layout.addWidget(self._h1_chart_row2, stretch=1)
        row2_layout.addWidget(self._m15_chart, stretch=1)
        self._content_layout.addWidget(row2)

        # ---- Row 3: 5-Minute Entry + 1-Minute Action ----
        row3_label = QLabel("5-Minute Entry  +  1-Minute Action")
        row3_label.setStyleSheet(_section_style)
        self._content_layout.addWidget(row3_label)

        row3 = QWidget()
        row3_layout = QHBoxLayout(row3)
        row3_layout.setContentsMargins(0, 0, 0, 0)
        row3_layout.setSpacing(4)

        self._m5_entry_chart = create_chart_label(min_height=200)
        self._m1_chart = create_chart_label(min_height=200)
        row3_layout.addWidget(self._m5_entry_chart, stretch=1)
        row3_layout.addWidget(self._m1_chart, stretch=1)
        self._content_layout.addWidget(row3)

        # ---- Row 4: 1-Minute Ramp-Up (full width) ----
        row4_label = QLabel("1-Minute Ramp-Up")
        row4_label.setStyleSheet(_section_style)
        self._content_layout.addWidget(row4_label)

        self._m1_rampup_chart = create_chart_label(min_height=250)
        self._content_layout.addWidget(self._m1_rampup_chart)

        # ---- Row 5: M1 Ramp-Up Indicator Table ----
        self._rampup_table = RampUpTable()
        self._content_layout.addWidget(self._rampup_table)

        # ---- Row 6: M1 Post-Trade Indicator Table ----
        self._posttrade_table = PostTradeTable()
        self._content_layout.addWidget(self._posttrade_table)

        self._content_layout.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def show_charts(
        self,
        daily_fig: go.Figure,
        h1_fig: go.Figure,
        m15_fig: go.Figure,
        m5_entry_fig: go.Figure,
        m1_fig: go.Figure,
        m1_rampup_fig: go.Figure,
        highlight: HighlightTrade,
        h1_prior_fig: go.Figure = None,
    ):
        """Render charts in paired 2-up layout."""
        self._update_summary(highlight)

        pair_w = self._pair_render_width
        pair_h = 340

        # Row 1: Daily + H1 Prior (sliced to 08:00-09:00 candle, prior day context)
        h1_row1 = h1_prior_fig if h1_prior_fig is not None else h1_fig
        render_chart_to_label(daily_fig, self._daily_chart, width=pair_w, height=pair_h)
        render_chart_to_label(h1_row1, self._h1_chart_row1, width=pair_w, height=pair_h)

        # Row 2: H1 (full trade day) + M15 (side by side)
        render_chart_to_label(h1_fig, self._h1_chart_row2, width=pair_w, height=pair_h)
        render_chart_to_label(m15_fig, self._m15_chart, width=pair_w, height=pair_h)

        # Row 3: M5 Entry + M1 Action (side by side)
        render_chart_to_label(m5_entry_fig, self._m5_entry_chart, width=pair_w, height=pair_h)
        render_chart_to_label(m1_fig, self._m1_chart, width=pair_w, height=pair_h)

        # Row 4: M1 Ramp-Up (full width)
        render_chart_to_label(m1_rampup_fig, self._m1_rampup_chart, width=RENDER_WIDTH, height=380)

    def show_rampup(self, df):
        """Populate the ramp-up indicator table."""
        self._rampup_table.update_data(df)

    def show_posttrade(self, df):
        """Populate the post-trade indicator table."""
        self._posttrade_table.update_data(df)

    def show_loading(self):
        """Show loading state."""
        self._summary.setText("Loading charts...")
        self._summary.setStyleSheet(f"color: {TV_COLORS['accent']}; padding: 8px;")
        self._daily_chart.setText("Loading Daily...")
        self._h1_chart_row1.setText("Loading H1...")
        self._h1_chart_row2.setText("Loading H1...")
        self._m15_chart.setText("Loading M15...")
        self._m5_entry_chart.setText("Loading M5 Entry...")
        self._m1_chart.setText("Loading M1...")
        self._m1_rampup_chart.setText("Loading M1 Ramp-Up...")
        self._rampup_table.clear()
        self._posttrade_table.clear()

    def show_placeholder(self):
        """Show placeholder state."""
        self._summary.setText("Select a highlight trade to view charts")
        self._summary.setStyleSheet(f"color: {TV_COLORS['text_muted']}; padding: 8px;")
        self._daily_chart.setText("Daily chart will appear here")
        self._h1_chart_row1.setText("H1 chart will appear here")
        self._h1_chart_row2.setText("H1 chart will appear here")
        self._m15_chart.setText("M15 chart will appear here")
        self._m5_entry_chart.setText("M5 Entry chart will appear here")
        self._m1_chart.setText("M1 chart will appear here")
        self._m1_rampup_chart.setText("M1 Ramp-Up chart will appear here")
        self._rampup_table.clear()
        self._posttrade_table.clear()

    def show_error(self, message: str):
        """Show error state."""
        self._summary.setText(f"Error: {message}")
        self._summary.setStyleSheet(f"color: {TV_COLORS['bear']}; padding: 8px;")

    def _update_summary(self, hl: HighlightTrade):
        """Update trade summary header."""
        dir_color = TV_COLORS['bull'] if hl.direction == 'LONG' else TV_COLORS['bear']
        outcome_color = TV_COLORS['bull'] if hl.is_winner else TV_COLORS['bear']
        pnl_str = f"{hl.pnl_r:+.2f}R" if hl.pnl_r else ""

        summary_html = (
            f"<span style='color:{dir_color}; font-weight:bold; font-size:16px;'>"
            f"{hl.ticker}</span>"
            f"<span style='color:{TV_COLORS['text_muted']};'>  |  {hl.date}  |  </span>"
            f"<span style='color:{dir_color};'>{hl.direction}</span>"
            f"<span style='color:{TV_COLORS['text_muted']};'>  |  {hl.model}  |  </span>"
            f"<span style='color:{outcome_color}; font-weight:bold;'>"
            f"{hl.star_display} {pnl_str}</span>"
            f"<span style='color:{TV_COLORS['text_muted']};'>  |  {hl.exit_reason}</span>"
        )

        self._summary.setText(summary_html)
        self._summary.setStyleSheet(f"color: {TV_COLORS['text_primary']}; padding: 8px;")

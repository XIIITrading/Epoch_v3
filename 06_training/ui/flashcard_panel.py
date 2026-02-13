"""
Epoch Trading System - Flashcard Panel
Central orchestrator: toggle between Pre-Trade and Post-Trade views,
assembles all sub-panels (chart, stats, events, review, bookmap, AI, indicators).

Layout matches Streamlit version 1:1:
PRE-TRADE:  Trade Info → Main Chart (M5/H1/M15) → M1 Ramp-Up → Event Table (ENTRY) → AI Prediction
POST-TRADE: Trade Info → Main Chart (M5/H1/M15) → Stats → Event Table (all) → Bookmap → Review → AI → DOW AI
"""

import logging
from datetime import datetime
from typing import Dict, Optional
import pandas as pd

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CHART_CONFIG
from models.trade import TradeWithMetrics, Zone
from data.supabase_client import SupabaseClient
from data.cache_manager import BarCache
from components.charts import build_review_chart
from components.rampup_chart import render_rampup_split

from ui.chart_renderer import (
    render_chart_to_label, create_chart_label,
    RENDER_WIDTH, MAIN_CHART_HEIGHT, RAMPUP_CHART_HEIGHT
)
from ui.rampup_table import RampUpIndicatorTable
from ui.trade_info_panel import TradeInfoPanel
from ui.event_table import EventIndicatorTable
from ui.stats_panel import StatsPanel
from ui.review_panel import ReviewPanel
from ui.bookmap_panel import BookmapPanel
from ui.indicator_panel import IndicatorPanel
from ui.dow_ai_panel import DOWAIPanel, AIPredictionDisplay

logger = logging.getLogger(__name__)


class FlashcardPanel(QFrame):
    """
    Central flashcard UI that toggles between pre-trade and post-trade views.
    Coordinates all sub-panels.
    """

    next_trade = pyqtSignal()  # Emitted after review is saved and ready for next

    def __init__(self, supabase: SupabaseClient, cache: BarCache, parent=None):
        super().__init__(parent)
        self._supabase = supabase
        self._cache = cache
        self._trade: Optional[TradeWithMetrics] = None
        self._bars: Optional[Dict[str, pd.DataFrame]] = None
        self._zones: Optional[list] = None
        self._events: Optional[Dict] = None
        self._ai_prediction: Optional[Dict] = None
        self._view_mode = 'pre_trade'
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)

        # Trade counter header
        self._counter_label = QLabel("")
        self._counter_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._counter_label.setStyleSheet("color: #e0e0e0;")
        outer.addWidget(self._counter_label)

        self._trade_header = QLabel("")
        self._trade_header.setFont(QFont("Segoe UI", 10))
        self._trade_header.setStyleSheet("color: #888888;")
        outer.addWidget(self._trade_header)

        # View toggle buttons
        toggle_row = QHBoxLayout()
        toggle_row.addStretch()

        self._pre_btn = QPushButton("Pre-Trade")
        self._pre_btn.setCheckable(True)
        self._pre_btn.setChecked(True)
        self._pre_btn.setFixedWidth(160)
        self._pre_btn.setFixedHeight(36)
        self._pre_btn.clicked.connect(lambda: self._set_view_mode('pre_trade'))

        self._post_btn = QPushButton("Post-Trade")
        self._post_btn.setCheckable(True)
        self._post_btn.setChecked(False)
        self._post_btn.setFixedWidth(160)
        self._post_btn.setFixedHeight(36)
        self._post_btn.clicked.connect(lambda: self._set_view_mode('post_trade'))

        self._update_toggle_styles()
        toggle_row.addWidget(self._pre_btn)
        toggle_row.addWidget(self._post_btn)
        toggle_row.addStretch()
        outer.addLayout(toggle_row)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self._scroll_content = QWidget()
        self._content_layout = QVBoxLayout(self._scroll_content)
        self._content_layout.setContentsMargins(0, 8, 0, 0)
        self._content_layout.setSpacing(8)

        # =====================================================================
        # Sub-panels in EXACT Streamlit order
        # All created once, shown/hidden per mode
        # =====================================================================

        # 1. Trade info (both modes)
        self._trade_info = TradeInfoPanel()
        self._content_layout.addWidget(self._trade_info)

        # 2. Main chart - M5 (full width) + H1/M15 (side by side)
        self._chart_label = create_chart_label(min_height=600)
        self._content_layout.addWidget(self._chart_label)

        # 3. M1 Ramp-up: candlestick chart + indicator table (pre-trade only)
        self._rampup_label = create_chart_label(min_height=250)
        self._content_layout.addWidget(self._rampup_label)

        self._rampup_table = RampUpIndicatorTable()
        self._content_layout.addWidget(self._rampup_table)

        # 4. Stats panel (post-trade only, appears BEFORE event table)
        self._stats_panel = StatsPanel()
        self._stats_panel.setVisible(False)
        self._content_layout.addWidget(self._stats_panel)

        # 5. Event indicators table (both modes, different columns)
        self._event_table = EventIndicatorTable()
        self._content_layout.addWidget(self._event_table)

        # 6. Bookmap viewer (post-trade only)
        self._bookmap_panel = BookmapPanel()
        self._bookmap_panel.setVisible(False)
        self._content_layout.addWidget(self._bookmap_panel)

        # 7. Review panel with checkboxes + notes + next (post-trade only)
        self._review_panel = ReviewPanel()
        self._review_panel.setVisible(False)
        self._review_panel.next_requested.connect(self._on_next_trade)
        self._content_layout.addWidget(self._review_panel)

        # 8. AI Prediction detail (pre-trade: expanded, post-trade: collapsed)
        self._pre_ai_prediction = AIPredictionDisplay()
        self._pre_ai_prediction.setVisible(False)
        self._content_layout.addWidget(self._pre_ai_prediction)

        # 9. Indicator refinement (post-trade, collapsed)
        self._indicator_panel = IndicatorPanel()
        self._indicator_panel.setVisible(False)
        self._content_layout.addWidget(self._indicator_panel)

        # 10. DOW AI Post-Trade Review (post-trade, collapsed)
        self._dow_ai_panel = DOWAIPanel()
        self._dow_ai_panel.setVisible(False)
        self._content_layout.addWidget(self._dow_ai_panel)

        self._content_layout.addStretch()

        scroll.setWidget(self._scroll_content)
        outer.addWidget(scroll, 1)

    def _update_toggle_styles(self):
        active = """
            QPushButton {
                background-color: #00C853; color: #ffffff;
                border: none; border-radius: 6px; padding: 8px 16px;
                font-size: 10pt; font-weight: bold;
            }
        """
        inactive = """
            QPushButton {
                background-color: #2a2a4e; color: #888888;
                border: 1px solid #333; border-radius: 6px; padding: 8px 16px;
                font-size: 10pt;
            }
            QPushButton:hover { background-color: #3a3a5e; color: #e0e0e0; }
        """
        self._pre_btn.setStyleSheet(active if self._view_mode == 'pre_trade' else inactive)
        self._post_btn.setStyleSheet(active if self._view_mode == 'post_trade' else inactive)
        self._pre_btn.setChecked(self._view_mode == 'pre_trade')
        self._post_btn.setChecked(self._view_mode == 'post_trade')

    def _set_view_mode(self, mode: str):
        if mode == self._view_mode:
            return
        self._view_mode = mode
        self._update_toggle_styles()
        self._render_current_view()

    def update_trade(
        self,
        trade: TradeWithMetrics,
        bars: Dict[str, pd.DataFrame],
        zones: list,
        current_index: int,
        total: int
    ):
        """Load a new trade into the flashcard panel."""
        self._trade = trade
        self._bars = bars
        self._zones = zones
        self._view_mode = 'pre_trade'
        self._update_toggle_styles()

        # Update counter
        pos = current_index + 1
        self._counter_label.setText(f"Trade {pos} of {total}")

        dir_indicator = "[LONG]" if trade.direction == 'LONG' else "[SHORT]"
        self._trade_header.setText(
            f"{trade.ticker} | {trade.date} | {trade.model} | "
            f"{dir_indicator} {trade.direction} | {trade.zone_type} | "
            f"{trade.trade_id}"
        )

        # Fetch AI prediction
        self._ai_prediction = None
        try:
            self._ai_prediction = self._supabase.fetch_ai_prediction(trade.trade_id)
        except Exception:
            pass

        # Fetch events
        self._events = None
        try:
            self._events = self._supabase.fetch_optimal_trade_events(trade.trade_id)
        except Exception:
            pass

        # Load existing review
        try:
            review = self._supabase.fetch_review(trade.trade_id)
            if review:
                self._review_panel.load_review(review)
            else:
                self._review_panel.clear()
        except Exception:
            self._review_panel.clear()

        self._render_current_view()

    def _render_current_view(self):
        """
        Render the current view mode.
        Matches Streamlit layout exactly:

        PRE-TRADE:
          1. Trade Info
          2. Main Chart (M5/H1/M15 with zones, mode=evaluate)
          3. M1 Ramp-Up Chart
          4. Event Indicators (ENTRY only)
          5. AI Prediction Detail (expanded)

        POST-TRADE:
          1. Trade Info
          2. Main Chart (M5/H1/M15 with zones + MFE/MAE/R-levels, mode=reveal)
          3. Stats Panel (P&L, MFE, MAE, Duration, R-levels)
          4. Event Indicators (all events: ENTRY, R1-R3, MAE, MFE, EXIT)
          5. Bookmap Viewer
          6. Review Panel (checkboxes, notes, Next Trade button)
          7. AI Prediction Detail (collapsed)
          8. DOW AI Post-Trade Review (collapsed)
        """
        if not self._trade:
            return

        trade = self._trade
        is_pre = self._view_mode == 'pre_trade'
        is_post = not is_pre

        # 1. Trade info (both modes)
        self._trade_info.update_trade(trade, self._ai_prediction)
        self._trade_info.setVisible(True)

        # 2. Main chart (both modes, different rendering)
        self._chart_label.setVisible(True)
        self._render_chart()

        # 3. M1 Ramp-up: chart + indicator table (pre-trade only)
        show_rampup = is_pre and trade.entry_time is not None
        self._rampup_label.setVisible(show_rampup)
        self._rampup_table.setVisible(show_rampup)
        if show_rampup:
            self._render_rampup()

        # 4. Stats panel (post-trade only, BEFORE event table)
        self._stats_panel.setVisible(is_post)
        if is_post:
            self._stats_panel.update_trade(trade)

        # 5. Event table (both modes, different columns)
        if self._events:
            self._event_table.update_events(self._events, trade, show_all_events=is_post)
        self._event_table.setVisible(self._events is not None)

        # 6. Bookmap (post-trade only)
        self._bookmap_panel.setVisible(is_post and bool(trade.bookmap_url))
        if is_post and trade.bookmap_url:
            self._bookmap_panel.update_bookmap(trade.bookmap_url)

        # 7. Review panel (post-trade only)
        self._review_panel.setVisible(is_post)

        # 8. AI Prediction detail
        #    Pre-trade: expanded, Post-trade: collapsed (handled by panel internally)
        has_ai = self._ai_prediction is not None
        self._pre_ai_prediction.setVisible(has_ai)
        if has_ai:
            self._pre_ai_prediction.update_prediction(self._ai_prediction)

        # 9. Indicator refinement (post-trade, collapsed)
        self._indicator_panel.setVisible(is_post)
        if is_post:
            try:
                refinement = self._supabase.fetch_indicator_refinement(trade.trade_id)
                self._indicator_panel.update_refinement(refinement, trade)
            except Exception:
                self._indicator_panel.update_refinement(None)

        # 10. DOW AI panel (post-trade, collapsed)
        self._dow_ai_panel.setVisible(is_post)
        if is_post:
            try:
                self._dow_ai_panel.update_trade(
                    trade=trade,
                    events=self._events or {},
                    supabase_client=self._supabase,
                    ai_prediction=self._ai_prediction
                )
            except Exception as e:
                logger.error(f"DOW AI panel error: {e}")

    def _render_chart(self):
        """Build and render the main multi-timeframe chart (M5/H1/M15 with zones)."""
        trade = self._trade
        if not trade or not self._bars:
            self._chart_label.setText("No bar data available")
            return

        try:
            if self._view_mode == 'pre_trade':
                # Slice bars to entry time only
                if trade.entry_time:
                    entry_dt = datetime.combine(trade.date, trade.entry_time)
                    bar_data = self._cache.get_bars_for_trade(trade.ticker, trade.date)
                    if bar_data:
                        sliced = self._cache.slice_bars_to_time(bar_data, end_time=entry_dt, include_end=True)
                    else:
                        sliced = self._bars
                else:
                    sliced = self._bars

                fig = build_review_chart(
                    bars=sliced,
                    trade=trade,
                    zones=self._zones,
                    mode='evaluate',
                    show_mfe_mae=False
                )
            else:
                # Post-trade: slice entry through exit + buffer
                if trade.entry_time and trade.exit_time:
                    bar_data = self._cache.get_bars_for_trade(trade.ticker, trade.date)
                    if bar_data:
                        entry_dt = datetime.combine(trade.date, trade.entry_time)
                        exit_dt = datetime.combine(trade.date, trade.exit_time)
                        reveal_bars = self._cache.slice_bars_for_reveal(
                            bar_data=bar_data,
                            entry_time=entry_dt,
                            exit_time=exit_dt,
                            context_bars=60,
                            buffer_bars=10
                        )
                    else:
                        reveal_bars = self._bars
                else:
                    reveal_bars = self._bars

                fig = build_review_chart(
                    bars=reveal_bars,
                    trade=trade,
                    zones=self._zones,
                    mode='reveal',
                    show_mfe_mae=True
                )

            render_chart_to_label(
                fig, self._chart_label,
                width=RENDER_WIDTH, height=MAIN_CHART_HEIGHT
            )
        except Exception as e:
            logger.error(f"Chart render error: {e}")
            self._chart_label.setText(f"Chart error: {e}")

    def _render_rampup(self):
        """Render M1 ramp-up: candlestick chart + PyQt indicator table."""
        trade = self._trade
        if not trade or not trade.entry_time:
            return

        try:
            fig, df = render_rampup_split(
                ticker=trade.ticker,
                trade_date=trade.date,
                entry_time=trade.entry_time,
                direction=trade.direction
            )
            if fig:
                render_chart_to_label(
                    fig, self._rampup_label,
                    width=RENDER_WIDTH, height=350
                )
                self._rampup_table.update_data(df)
            else:
                self._rampup_label.setText("M1 ramp-up chart unavailable")
                self._rampup_table.setVisible(False)
        except Exception as e:
            self._rampup_label.setText(f"M1 ramp-up error: {e}")
            self._rampup_table.setVisible(False)

    def _on_next_trade(self):
        """Save review and advance to next trade."""
        if not self._trade:
            return

        # Save review
        review = self._review_panel.get_review(self._trade)
        try:
            self._supabase.upsert_review(review)
        except Exception as e:
            logger.error(f"Failed to save review: {e}")

        # Reset state and emit
        self._review_panel.clear()
        self._view_mode = 'pre_trade'
        self._update_toggle_styles()
        self.next_trade.emit()

    def show_welcome(self):
        """Show welcome screen when no queue is loaded."""
        self._counter_label.setText("Epoch Trade Review System")
        self._trade_header.setText(
            "Load trades using the sidebar filters to begin reviewing."
        )
        # Hide all sub-panels
        for panel in [
            self._trade_info, self._chart_label, self._rampup_label,
            self._rampup_table, self._stats_panel, self._event_table,
            self._bookmap_panel, self._review_panel, self._pre_ai_prediction,
            self._indicator_panel, self._dow_ai_panel
        ]:
            panel.setVisible(False)

        self._pre_btn.setVisible(False)
        self._post_btn.setVisible(False)

    def show_completion(self, total: int):
        """Show queue completion screen."""
        self._counter_label.setText("Session Complete!")
        self._trade_header.setText(f"Reviewed {total} trades in this session.")
        for panel in [
            self._trade_info, self._chart_label, self._rampup_label,
            self._rampup_table, self._stats_panel, self._event_table,
            self._bookmap_panel, self._review_panel, self._pre_ai_prediction,
            self._indicator_panel, self._dow_ai_panel
        ]:
            panel.setVisible(False)
        self._pre_btn.setVisible(False)
        self._post_btn.setVisible(False)

    def show_loading(self):
        """Show loading state."""
        self._counter_label.setText("Loading trade data...")
        self._trade_header.setText("")

    def show_trade_panels(self):
        """Show toggle buttons (called when a trade is loaded)."""
        self._pre_btn.setVisible(True)
        self._post_btn.setVisible(True)

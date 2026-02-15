"""
Epoch Trading System - M1 Post-Trade Indicator Table (Trade Reel)
QTableWidget showing 7 indicator rows x N bar columns, from entry onward.
Entry candle is the first column, followed by the next 45 candles.

Reuses formatter/color logic from rampup_table.py.
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, time
from typing import Optional
import logging

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy,
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_CONFIG, TV_COLORS
from ui.rampup_table import (
    INDICATOR_LABELS,
    _fmt_candle_range, _color_candle_range,
    _fmt_vol_delta, _color_vol_delta,
    _fmt_vol_roc, _color_vol_roc,
    _fmt_sma, _color_sma,
    _fmt_structure, _color_structure,
)

logger = logging.getLogger(__name__)

# Entry candle + 45 candles after = 46 total columns
POSTTRADE_BARS = 46


# =============================================================================
# DATA FETCH
# =============================================================================

def fetch_posttrade_data(
    ticker: str,
    trade_date: date,
    entry_time: time,
    num_bars: int = POSTTRADE_BARS,
) -> pd.DataFrame:
    """Fetch M1 indicator bars from entry time onward (inclusive)."""
    query = """
        SELECT
            ticker, bar_date, bar_time,
            open, high, low, close, volume,
            vwap, sma9, sma21, sma_spread,
            vol_roc, vol_delta_roll,
            m5_structure, m15_structure, h1_structure,
            candle_range_pct
        FROM m1_indicator_bars_2
        WHERE ticker = %s
          AND bar_date = %s
          AND bar_time >= %s
        ORDER BY bar_time ASC
        LIMIT %s
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (ticker.upper(), trade_date, entry_time, num_bars))
            rows = cur.fetchall()
        conn.close()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame([dict(r) for r in rows])
        return df

    except Exception as e:
        logger.error(f"Error fetching post-trade data: {e}")
        return pd.DataFrame()


# =============================================================================
# QT WIDGET
# =============================================================================

class PostTradeTable(QFrame):
    """M1 post-trade indicator table: 7 rows x N bar columns, color-coded."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        self._title = QLabel("M1 Post-Trade Indicators")
        self._title.setFont(QFont("Trebuchet MS", 11, QFont.Weight.Bold))
        self._title.setStyleSheet(f"color: {TV_COLORS['text_primary']}; padding: 2px 0;")
        layout.addWidget(self._title)

        self._table = QTableWidget()
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setMinimumSectionSize(36)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {TV_COLORS['bg_primary']};
                gridline-color: {TV_COLORS['border']};
                color: {TV_COLORS['text_primary']};
                border: 1px solid {TV_COLORS['border']};
                font-size: 11pt;
            }}
            QTableWidget::item {{
                padding: 1px 2px;
            }}
            QHeaderView::section {{
                background-color: {TV_COLORS['bg_secondary']};
                color: {TV_COLORS['text_muted']};
                font-size: 11pt;
                border: 1px solid {TV_COLORS['border']};
                padding: 2px;
            }}
        """)
        layout.addWidget(self._table)

    def update_data(self, df: pd.DataFrame):
        """Populate the table from M1 indicator bar DataFrame."""
        if df is None or df.empty:
            self._table.setRowCount(0)
            self._table.setColumnCount(0)
            self._title.setText("M1 Post-Trade Indicators - No data")
            return

        num_bars = len(df)
        num_ind = len(INDICATOR_LABELS)

        self._table.setRowCount(num_ind)
        self._table.setColumnCount(num_bars)

        # Column headers = time labels; first column is entry
        time_labels = []
        for i, (_, row) in enumerate(df.iterrows()):
            bt = row.get('bar_time')
            if bt and hasattr(bt, 'strftime'):
                label = bt.strftime('%H:%M')
            else:
                label = str(bt)[:5] if bt else '-'
            # Mark the entry candle
            if i == 0:
                label = f"E {label}"
            time_labels.append(label)
        self._table.setHorizontalHeaderLabels(time_labels)

        # Row headers = indicator names
        self._table.setVerticalHeaderLabels(INDICATOR_LABELS)
        self._table.verticalHeader().setVisible(True)
        self._table.verticalHeader().setDefaultSectionSize(26)
        self._table.verticalHeader().setFixedWidth(75)
        self._table.verticalHeader().setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {TV_COLORS['bg_secondary']};
                color: {TV_COLORS['text_muted']};
                font-size: 11pt;
                font-weight: bold;
                border: 1px solid {TV_COLORS['border']};
                padding: 2px 4px;
            }}
        """)

        cell_font = QFont("Consolas", 11)
        cell_font.setBold(True)

        for col_idx, (_, row) in enumerate(df.iterrows()):
            for row_idx, ind_name in enumerate(INDICATOR_LABELS):
                value, color = self._cell(ind_name, row)
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFont(cell_font)
                item.setForeground(QColor(color))
                self._table.setItem(row_idx, col_idx, item)

        # Sizing
        header = self._table.horizontalHeader()
        header.setMinimumSectionSize(36)
        header.setDefaultSectionSize(48)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        row_h = 26
        total_h = (num_ind * row_h) + 32
        self._table.setFixedHeight(total_h)
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._title.setText(f"M1 Post-Trade Indicators (entry + {num_bars - 1} bars)")

    def clear(self):
        self._table.setRowCount(0)
        self._table.setColumnCount(0)
        self._title.setText("M1 Post-Trade Indicators")

    def _cell(self, ind_name: str, row: pd.Series) -> tuple:
        """Return (formatted_value, hex_color) for a cell."""
        if ind_name == 'Candle %':
            return _fmt_candle_range(row.get('candle_range_pct')), _color_candle_range(row.get('candle_range_pct'))
        elif ind_name == 'Vol Delta':
            return _fmt_vol_delta(row.get('vol_delta_roll')), _color_vol_delta(row.get('vol_delta_roll'))
        elif ind_name == 'Vol ROC':
            return _fmt_vol_roc(row.get('vol_roc')), _color_vol_roc(row.get('vol_roc'))
        elif ind_name == 'SMA':
            return _fmt_sma(row.get('sma_spread'), row.get('close')), _color_sma(row.get('sma_spread'))
        elif ind_name == 'M5 Struct':
            return _fmt_structure(row.get('m5_structure')), _color_structure(row.get('m5_structure'))
        elif ind_name == 'M15 Struct':
            return _fmt_structure(row.get('m15_structure')), _color_structure(row.get('m15_structure'))
        elif ind_name == 'H1 Struct':
            return _fmt_structure(row.get('h1_structure')), _color_structure(row.get('h1_structure'))
        return '-', TV_COLORS['text_muted']

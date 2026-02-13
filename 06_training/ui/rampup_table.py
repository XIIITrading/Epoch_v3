"""
Epoch Trading System - Ramp-Up Indicator Table
PyQt6 QTableWidget displaying M1 indicator metrics below the ramp-up candlestick chart.

Replaces the Plotly annotation-based table with a clean native table.
7 indicator rows × N bar columns, with color-coded cells.
"""

import pandas as pd
from typing import Optional
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.rampup_chart import (
    INDICATOR_LABELS, COLORS,
    # Formatters
    format_candle_range, format_vol_delta, format_vol_roc,
    format_sma_config, format_structure,
    # Color getters
    get_candle_range_color, get_vol_delta_color, get_vol_roc_color,
    get_sma_config_color, get_structure_color,
)


class RampUpIndicatorTable(QFrame):
    """
    PyQt table showing M1 indicator values per bar.
    Rows = 7 indicators, Columns = time bars.
    Cells are color-coded matching the Plotly annotation colors.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(20, 0, 20, 0)  # 20px left/right buffer
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._title = QLabel("M1 Ramp-Up Indicators")
        self._title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._title.setStyleSheet("color: #e0e0e0; padding: 2px 0;")
        layout.addWidget(self._title)

        self._table = QTableWidget()
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setMinimumSectionSize(40)
        self._table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a2e;
                gridline-color: #2a2a4e;
                color: #e0e0e0;
                border: 1px solid #2a2a4e;
                font-size: 10pt;
            }
            QTableWidget::item {
                padding: 1px 2px;
            }
            QHeaderView::section {
                background-color: #1a1a2e;
                color: #aaaaaa;
                font-size: 10pt;
                border: 1px solid #2a2a4e;
                padding: 2px;
            }
        """)
        layout.addWidget(self._table)

    def update_data(self, df: pd.DataFrame):
        """
        Populate the table from M1 indicator bar DataFrame.

        Args:
            df: DataFrame with columns: bar_time, candle_range_pct, vol_delta,
                vol_roc, sma_spread, close, m5_structure, m15_structure, h1_structure
        """
        if df is None or df.empty:
            self._table.setRowCount(0)
            self._table.setColumnCount(0)
            self._title.setText("M1 Ramp-Up Indicators - No data")
            return

        num_bars = len(df)
        num_indicators = len(INDICATOR_LABELS)

        self._table.setRowCount(num_indicators)
        self._table.setColumnCount(num_bars)

        # Column headers = time labels
        time_labels = []
        for _, row in df.iterrows():
            bt = row.get('bar_time')
            if bt and hasattr(bt, 'strftime'):
                time_labels.append(bt.strftime('%H:%M'))
            else:
                time_labels.append(str(bt)[:5] if bt else '-')
        self._table.setHorizontalHeaderLabels(time_labels)

        # Row headers = indicator labels
        self._table.setVerticalHeaderLabels(INDICATOR_LABELS)
        self._table.verticalHeader().setVisible(True)
        self._table.verticalHeader().setDefaultSectionSize(24)
        self._table.verticalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #1a1a2e;
                color: #aaaaaa;
                font-size: 10pt;
                font-weight: bold;
                border: 1px solid #2a2a4e;
                padding: 2px 6px;
                min-width: 70px;
            }
        """)

        cell_font = QFont("Consolas", 10)
        cell_font.setBold(True)

        # Populate cells
        for col_idx, (_, row) in enumerate(df.iterrows()):
            for row_idx, indicator_name in enumerate(INDICATOR_LABELS):
                value, color = self._get_cell_data(indicator_name, row)
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFont(cell_font)
                item.setForeground(QColor(color))
                self._table.setItem(row_idx, col_idx, item)

        # Sizing - stretch columns to fill available width
        header = self._table.horizontalHeader()
        header.setMinimumSectionSize(40)
        header.setDefaultSectionSize(52)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Set vertical header width
        self._table.verticalHeader().setFixedWidth(80)

        # Fixed height to show all rows without scrolling
        row_height = 24
        total_height = (num_indicators * row_height) + 30  # +header
        self._table.setFixedHeight(total_height)
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._title.setText(f"M1 Ramp-Up Indicators ({num_bars} bars)")

    def _get_cell_data(self, indicator_name: str, row: pd.Series) -> tuple:
        """
        Get formatted value and color for a cell.

        Returns:
            (formatted_value, hex_color)
        """
        if indicator_name == 'Candle %':
            return (
                format_candle_range(row.get('candle_range_pct')),
                get_candle_range_color(row.get('candle_range_pct'))
            )
        elif indicator_name == 'Vol Delta':
            return (
                format_vol_delta(row.get('vol_delta')),
                get_vol_delta_color(row.get('vol_delta'))
            )
        elif indicator_name == 'Vol ROC':
            return (
                format_vol_roc(row.get('vol_roc')),
                get_vol_roc_color(row.get('vol_roc'))
            )
        elif indicator_name == 'SMA':
            close = row.get('close')
            sma_spread = row.get('sma_spread')
            return (
                format_sma_config(sma_spread, close),
                get_sma_config_color(sma_spread)
            )
        elif indicator_name == 'M5 Struct':
            return (
                format_structure(row.get('m5_structure')),
                get_structure_color(row.get('m5_structure'))
            )
        elif indicator_name == 'M15 Struct':
            return (
                format_structure(row.get('m15_structure')),
                get_structure_color(row.get('m15_structure'))
            )
        elif indicator_name == 'H1 Struct':
            return (
                format_structure(row.get('h1_structure')),
                get_structure_color(row.get('h1_structure'))
            )
        else:
            return ('-', COLORS['default'])

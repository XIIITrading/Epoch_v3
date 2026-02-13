"""
================================================================================
EPOCH TRADING SYSTEM - Section Builder
XIII Trading LLC
================================================================================

Reusable report section builders for all dashboard tabs.
Extracted from overview_tab.py to enable code reuse across
Overview, Daily, Weekly, and Monthly tabs.

All 4 report sections:
    1. Stop Type Comparison
    2. Win Rate by Model
    3. Model-Direction Grid
    4. MFE/MAE Sequence Analysis

================================================================================
"""

from typing import List, Optional

from PyQt6.QtWidgets import (
    QVBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

import sys
from pathlib import Path

# Add report_viewer to path (parent of tabs/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from styles import COLORS
from data_provider import STOP_TYPE_NAMES


# ============================================================================
# Color helpers for conditional formatting
# ============================================================================

def _win_rate_color(value: float) -> QColor:
    """Color for win rate values: green >= 45%, red < 40%, neutral between."""
    if value >= 45.0:
        return QColor(COLORS['positive'])
    elif value < 40.0:
        return QColor(COLORS['negative'])
    return QColor(COLORS['text_primary'])


def _expectancy_color(value: float) -> QColor:
    """Color for expectancy: green > 0, red < 0."""
    if value > 0:
        return QColor(COLORS['positive'])
    elif value < 0:
        return QColor(COLORS['negative'])
    return QColor(COLORS['text_primary'])


def _r_value_color(value: float) -> QColor:
    """Color for R values: green > 0, red < 0."""
    if value > 0:
        return QColor(COLORS['positive'])
    elif value < 0:
        return QColor(COLORS['negative'])
    return QColor(COLORS['text_primary'])


def _pct_color(value_str: str) -> QColor:
    """Color for percentage string like '45.2%' in the grid."""
    try:
        val = float(value_str.replace('%', ''))
        return _win_rate_color(val)
    except (ValueError, AttributeError):
        return QColor(COLORS['text_muted'])


def _mfe_first_color(value: float) -> QColor:
    """Color for P(MFE First): green >= 55%, red < 45%."""
    if value >= 0.55:
        return QColor(COLORS['positive'])
    elif value < 0.45:
        return QColor(COLORS['negative'])
    return QColor(COLORS['text_primary'])


# ============================================================================
# Table creation helpers
# ============================================================================

def _create_table(headers: List[str], row_count: int = 0) -> QTableWidget:
    """Create a styled QTableWidget with no internal scrolling."""
    table = QTableWidget()
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setRowCount(row_count)

    # No internal scrolling - parent ScrollArea handles it
    table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    # Header
    header = table.horizontalHeader()
    header.setStretchLastSection(True)
    header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    # Alternating rows, read-only, row selection
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

    return table


def _set_cell(table: QTableWidget, row: int, col: int, text: str,
              color: QColor = None, align_right: bool = False):
    """Set a cell value with optional color and alignment."""
    item = QTableWidgetItem(text)

    if align_right:
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    else:
        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    if color:
        item.setForeground(color)

    table.setItem(row, col, item)


def _resize_table(table: QTableWidget):
    """Resize table height to show all rows without scrolling."""
    header_height = table.horizontalHeader().height()
    row_height = table.verticalHeader().defaultSectionSize()
    total_rows = table.rowCount()
    total_height = header_height + (row_height * total_rows) + 6
    table.setMinimumHeight(total_height)
    table.setMaximumHeight(total_height)
    table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


def _auto_resize_columns(table: QTableWidget):
    """Auto-resize all columns to content."""
    header = table.horizontalHeader()
    for i in range(table.columnCount()):
        header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
    header.setStretchLastSection(True)


# ============================================================================
# Section frame helper
# ============================================================================

def _create_section(title: str, description: str = "") -> tuple:
    """
    Create a section frame with title and optional description.

    Returns (frame, content_layout) for adding widgets.
    """
    frame = QFrame()
    frame.setObjectName("sectionFrame")

    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(8)

    # Title
    title_label = QLabel(title)
    title_label.setObjectName("sectionTitle")
    title_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
    layout.addWidget(title_label)

    # Description
    if description:
        desc_label = QLabel(description)
        desc_label.setObjectName("statusLabel")
        desc_label.setWordWrap(True)
        desc_label.setFont(QFont("Segoe UI", 9))
        layout.addWidget(desc_label)

    content = QVBoxLayout()
    content.setSpacing(10)
    layout.addLayout(content)

    return frame, content


# ============================================================================
# Layout utilities
# ============================================================================

def clear_layout(layout: QVBoxLayout):
    """Remove all widgets and spacers from a layout."""
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()


# ============================================================================
# Section builders (called by all tabs)
# ============================================================================

def build_all_sections(provider, layout: QVBoxLayout, date_label: str = None):
    """
    Build all 4 report sections into the given layout.

    Args:
        provider: DataProvider with loaded data
        layout: QVBoxLayout to add sections to
        date_label: Optional date range string (e.g. "2026-02-07" or
                    "2026-02-01 to 2026-02-07")
    """
    if date_label:
        banner = QLabel(f"Date Range: {date_label}")
        banner.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        banner.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 4px 8px;")
        layout.addWidget(banner)

    build_stop_type_comparison(provider, layout)
    build_win_rate_by_model(provider, layout)
    build_model_direction_grid(provider, layout)
    build_mfe_mae_sequence(provider, layout)


def build_stop_type_comparison(provider, layout: QVBoxLayout):
    """Build the Stop Type Comparison table."""
    df = provider.get_stop_type_comparison()
    if df is None or df.empty:
        return

    frame, content = _create_section(
        "Stop Type Comparison",
        f"{provider.record_count:,} records across {provider.trade_count:,} trades "
        f"| Ranked by Win Rate %"
    )

    headers = [
        "Stop Type", "n", "Avg Stop %", "Stop Hit %",
        "Win Rate %", "Avg R (Win)", "Avg R (All)", "Net R (MFE)", "Expectancy"
    ]
    table = _create_table(headers, len(df))

    for row_idx, (_, row) in enumerate(df.iterrows()):
        _set_cell(table, row_idx, 0, row['Stop Type'])
        _set_cell(table, row_idx, 1, f"{int(row['n']):,}", align_right=True)
        _set_cell(table, row_idx, 2, f"{row['Avg Stop %']:.2f}%", align_right=True)
        _set_cell(table, row_idx, 3, f"{row['Stop Hit %']:.1f}%", align_right=True)
        _set_cell(table, row_idx, 4, f"{row['Win Rate %']:.1f}%",
                   color=_win_rate_color(row['Win Rate %']), align_right=True)
        _set_cell(table, row_idx, 5, f"{row['Avg R (Win)']:+.2f}R",
                   color=_r_value_color(row['Avg R (Win)']), align_right=True)
        _set_cell(table, row_idx, 6, f"{row['Avg R (All)']:+.2f}R",
                   color=_r_value_color(row['Avg R (All)']), align_right=True)
        _set_cell(table, row_idx, 7, f"{row['Net R (MFE)']:+.2f}R",
                   color=_r_value_color(row['Net R (MFE)']), align_right=True)
        _set_cell(table, row_idx, 8, f"{row['Expectancy']:+.3f}",
                   color=_expectancy_color(row['Expectancy']), align_right=True)

    _auto_resize_columns(table)
    _resize_table(table)
    content.addWidget(table)
    layout.addWidget(frame)


def build_win_rate_by_model(provider, layout: QVBoxLayout):
    """Build Win Rate by Model sub-tables (one per stop type)."""
    all_models = provider.get_all_win_rate_by_model()
    if not all_models:
        return

    frame, content = _create_section(
        "Win Rate by Model",
        "How each entry model (EPCH01-04) performs under each stop type"
    )

    for stop_key in provider.get_stop_type_order():
        model_df = all_models.get(stop_key)
        if model_df is None:
            continue

        stop_name = STOP_TYPE_NAMES.get(stop_key, stop_key)
        total_trades = model_df['Total'].sum()
        total_wins = model_df['Wins'].sum()
        overall_wr = (total_wins / total_trades * 100) if total_trades > 0 else 0

        # Sub-header
        sub_header = QLabel(
            f"{stop_name}  |  {total_trades:,} trades  |  "
            f"Overall Win Rate: {overall_wr:.1f}%"
        )
        sub_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        sub_header.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 4px 0;")
        content.addWidget(sub_header)

        headers = [
            "Model", "Wins", "Losses", "Total", "Win %",
            "Avg R (Win)", "Avg R (All)", "Expectancy"
        ]
        table = _create_table(headers, len(model_df))

        for row_idx, (_, row) in enumerate(model_df.iterrows()):
            _set_cell(table, row_idx, 0, str(row['Model']))
            _set_cell(table, row_idx, 1, f"{int(row['Wins']):,}", align_right=True)
            _set_cell(table, row_idx, 2, f"{int(row['Losses']):,}", align_right=True)
            _set_cell(table, row_idx, 3, f"{int(row['Total']):,}", align_right=True)
            _set_cell(table, row_idx, 4, f"{row['Win%']:.1f}%",
                       color=_win_rate_color(row['Win%']), align_right=True)
            _set_cell(table, row_idx, 5, f"{row['Avg R (Win)']:+.2f}R",
                       color=_r_value_color(row['Avg R (Win)']), align_right=True)
            _set_cell(table, row_idx, 6, f"{row['Avg R (All)']:+.2f}R",
                       color=_r_value_color(row['Avg R (All)']), align_right=True)
            _set_cell(table, row_idx, 7, f"{row['Expectancy']:+.3f}",
                       color=_expectancy_color(row['Expectancy']), align_right=True)

        _auto_resize_columns(table)
        _resize_table(table)
        content.addWidget(table)

    layout.addWidget(frame)


def build_model_direction_grid(provider, layout: QVBoxLayout):
    """Build the 8-column Model-Direction win rate grid."""
    grid_df = provider.get_model_direction_grid()
    if grid_df is None or grid_df.empty:
        return

    frame, content = _create_section(
        "Win Rate by Model-Direction",
        "Splits each model by LONG and SHORT to expose directional bias"
    )

    headers = list(grid_df.columns)
    table = _create_table(headers, len(grid_df))

    for row_idx, (_, row) in enumerate(grid_df.iterrows()):
        for col_idx, col_name in enumerate(headers):
            val = str(row[col_name])
            if col_idx == 0:
                _set_cell(table, row_idx, col_idx, val)
            else:
                color = _pct_color(val)
                _set_cell(table, row_idx, col_idx, val,
                          color=color, align_right=True)

    _auto_resize_columns(table)
    _resize_table(table)
    content.addWidget(table)
    layout.addWidget(frame)


def build_mfe_mae_sequence(provider, layout: QVBoxLayout):
    """Build MFE/MAE Sequence Analysis tables."""
    summary = provider.get_mfe_mae_summary()
    if summary is None:
        return

    frame, content = _create_section(
        "MFE/MAE Sequence Analysis",
        f"{summary['total_trades']:,} trades | Answers whether trades move "
        f"favorably before adversely after entry"
    )

    # Overall summary - key-value table
    overall_label = QLabel("Overall")
    overall_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
    overall_label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 4px 0;")
    content.addWidget(overall_label)

    summary_headers = ["Metric", "Value"]
    summary_table = _create_table(summary_headers, 7)

    metrics = [
        ("P(MFE First)", f"{summary['mfe_first_rate']:.1%}",
         _mfe_first_color(summary['mfe_first_rate'])),
        ("MFE First Count", f"{summary['mfe_first_count']:,}", None),
        ("MAE First Count", f"{summary['mae_first_count']:,}", None),
        ("Median Time to MFE", f"{summary['median_time_to_mfe']:.0f} min", None),
        ("Median Time to MAE", f"{summary['median_time_to_mae']:.0f} min", None),
        ("MFE within 30 min", f"{summary['pct_mfe_under_30min']:.1f}%", None),
        ("MFE within 60 min", f"{summary['pct_mfe_under_60min']:.1f}%", None),
    ]

    for row_idx, (metric, value, color) in enumerate(metrics):
        _set_cell(summary_table, row_idx, 0, metric)
        _set_cell(summary_table, row_idx, 1, value, color=color, align_right=True)

    _auto_resize_columns(summary_table)
    _resize_table(summary_table)
    content.addWidget(summary_table)

    # Model-Direction breakdown
    model_df = provider.get_mfe_mae_by_model()
    if model_df is not None and not model_df.empty:
        model_label = QLabel("By Model-Direction  |  Ranked by P(MFE First)")
        model_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        model_label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 8px 0 4px 0;")
        content.addWidget(model_label)

        model_headers = [
            "Model", "Direction", "n", "P(MFE First)",
            "Med Time MFE", "Med Time MAE", "Time Delta", "Confidence"
        ]
        model_table = _create_table(model_headers, len(model_df))

        for row_idx, (_, row) in enumerate(model_df.iterrows()):
            _set_cell(model_table, row_idx, 0, str(row['model']))
            _set_cell(model_table, row_idx, 1, str(row['direction']))
            _set_cell(model_table, row_idx, 2, f"{int(row['n_trades']):,}", align_right=True)
            _set_cell(model_table, row_idx, 3, f"{row['p_mfe_first']:.1%}",
                       color=_mfe_first_color(row['p_mfe_first']), align_right=True)
            _set_cell(model_table, row_idx, 4, f"{row['median_time_mfe']:.0f} min", align_right=True)
            _set_cell(model_table, row_idx, 5, f"{row['median_time_mae']:.0f} min", align_right=True)

            delta = row['median_time_delta']
            _set_cell(model_table, row_idx, 6, f"{delta:+.0f} min",
                       color=_r_value_color(delta), align_right=True)
            _set_cell(model_table, row_idx, 7, str(row['mc_confidence']))

        _auto_resize_columns(model_table)
        _resize_table(model_table)
        content.addWidget(model_table)

    layout.addWidget(frame)

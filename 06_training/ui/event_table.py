"""
Epoch Trading System - Event Indicators Table
QTableWidget displaying indicator metrics at trade events.
"""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout, QFrame, QLabel
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt
from typing import Dict, Any, Optional


# Color helpers
def _get_health_color(score) -> str:
    if score is None:
        return "#888888"
    if score >= 8:
        return "#00C853"
    elif score >= 6:
        return "#FFC107"
    elif score >= 4:
        return "#FF9800"
    return "#FF1744"


def _get_structure_color(structure: str, direction: str) -> str:
    if not structure:
        return "#888888"
    s = structure.upper()
    if direction == 'LONG':
        if s == 'BULL':
            return "#00C853"
        elif s == 'BEAR':
            return "#FF1744"
    else:
        if s == 'BEAR':
            return "#00C853"
        elif s == 'BULL':
            return "#FF1744"
    return "#888888"


def _get_momentum_color(momentum: str) -> str:
    if not momentum:
        return "#888888"
    m = momentum.upper()
    if m == 'WIDENING':
        return "#00C853"
    elif m == 'NARROWING':
        return "#FF9800"
    return "#888888"


class EventIndicatorTable(QFrame):
    """Table showing indicator metrics at ENTRY, R1-R3, MAE, MFE, EXIT events."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._title = QLabel("Event Indicators")
        self._title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._title.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(self._title)

        self._table = QTableWidget()
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a2e;
                gridline-color: #333333;
                color: #e0e0e0;
                border: none;
            }
            QTableWidget::item {
                padding: 4px 8px;
            }
            QHeaderView::section {
                background-color: #2a2a4e;
                color: #e0e0e0;
                font-weight: bold;
                border: 1px solid #333333;
                padding: 4px 8px;
            }
        """)
        layout.addWidget(self._table)

    def update_events(
        self,
        events: Optional[Dict[str, Dict[str, Any]]],
        trade,
        show_all_events: bool = False
    ):
        """
        Populate table from events dict.

        Args:
            events: Dict keyed by event_type with indicator values
            trade: TradeWithMetrics for context
            show_all_events: If True show all events; if False only ENTRY
        """
        if not events:
            self._table.setRowCount(0)
            self._table.setColumnCount(0)
            self._title.setText("Event Indicators - No data available")
            return

        direction = trade.direction or "LONG"

        # Build event columns
        if show_all_events:
            event_order = ['ENTRY']
            if 'R1_CROSS' in events:
                event_order.append('R1_CROSS')
            if 'R2_CROSS' in events:
                event_order.append('R2_CROSS')
            if 'R3_CROSS' in events:
                event_order.append('R3_CROSS')
            event_order.extend(['MAE', 'MFE', 'EXIT'])
        else:
            event_order = ['ENTRY']

        event_labels = {
            'ENTRY': 'Entry', 'R1_CROSS': '1R', 'R2_CROSS': '2R',
            'R3_CROSS': '3R', 'MAE': 'MAE', 'MFE': 'MFE', 'EXIT': 'Exit'
        }

        # R-multiple calculator
        def calc_r(price_val):
            if price_val is None or not trade.entry_price or not trade.risk_per_share:
                return None
            if trade.risk_per_share == 0:
                return None
            entry = float(trade.entry_price)
            price = float(price_val)
            pnl = (price - entry) if trade.direction == 'LONG' else (entry - price)
            return pnl / trade.risk_per_share

        # Define metrics rows
        def fmt_time(v):
            if v is None:
                return "-"
            if hasattr(v, 'strftime'):
                return v.strftime("%H:%M")
            return str(v)[:5]

        def fmt_price(v):
            return f"${float(v):.2f}" if v is not None else "-"

        def fmt_r(v):
            r = calc_r(v)
            return f"{float(r):+.2f}R" if r is not None else "-"

        def fmt_points(v):
            return f"{float(v):+.2f} pts" if v is not None else "-"

        def fmt_health(v):
            return f"{v}/10" if v is not None else "-"

        def fmt_spread(v):
            return f"{float(v):.2f}" if v is not None else "-"

        def fmt_pct(v):
            return f"{float(v):+.1f}%" if v is not None else "-"

        def fmt_str(v):
            return v or "-"

        metrics = [
            ('Time', 'event_time', fmt_time, None),
            ('Price', 'price_at_event', fmt_price, None),
            ('R-Multiple', 'price_at_event', fmt_r, None),
            ('Points', 'points_at_event', fmt_points, None),
            ('Health', 'health_score', fmt_health, lambda v: _get_health_color(v)),
            ('VWAP', 'vwap', fmt_price, None),
            ('SMA9', 'sma9', fmt_price, None),
            ('SMA21', 'sma21', fmt_price, None),
            ('SMA Spread', 'sma_spread', fmt_spread, None),
            ('SMA Mom', 'sma_momentum_label', fmt_str, lambda v: _get_momentum_color(v)),
            ('Vol ROC', 'vol_roc', fmt_pct, None),
            ('M5', 'm5_structure', fmt_str, lambda v: _get_structure_color(v, direction)),
            ('M15', 'm15_structure', fmt_str, lambda v: _get_structure_color(v, direction)),
            ('H1', 'h1_structure', fmt_str, lambda v: _get_structure_color(v, direction)),
            ('H4', 'h4_structure', fmt_str, lambda v: _get_structure_color(v, direction)),
        ]

        # Configure table
        num_cols = len(event_order) + 1  # +1 for metric name column
        num_rows = len(metrics)

        self._table.setRowCount(num_rows)
        self._table.setColumnCount(num_cols)

        # Set headers
        headers = ['Metric'] + [event_labels.get(e, e) for e in event_order]
        self._table.setHorizontalHeaderLabels(headers)

        # Populate
        for row_idx, (metric_name, metric_key, formatter, color_fn) in enumerate(metrics):
            # Metric name column
            name_item = QTableWidgetItem(metric_name)
            name_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            name_item.setForeground(QColor("#888888"))
            self._table.setItem(row_idx, 0, name_item)

            # Event columns
            for col_idx, event_type in enumerate(event_order):
                event_data = events.get(event_type, {})
                value = event_data.get(metric_key)
                formatted = formatter(value)

                item = QTableWidgetItem(formatted)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFont(QFont("Segoe UI", 10))

                if color_fn:
                    color = color_fn(value)
                    item.setForeground(QColor(color))

                self._table.setItem(row_idx, col_idx + 1, item)

        # Resize
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for i in range(1, num_cols):
            self._table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setDefaultSectionSize(28)
        self._table.setFixedHeight(num_rows * 28 + 32)

        self._title.setText(f"Event Indicators ({len(event_order)} events)")

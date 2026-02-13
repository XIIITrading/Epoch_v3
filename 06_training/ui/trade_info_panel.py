"""
Epoch Trading System - Trade Info Panel
Horizontal header with Model, Zone Type, Zone POC, Entry, AI Prediction.
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class TradeInfoPanel(QFrame):
    """Compact trade info header row with 5 key metrics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tradeInfoPanel")
        self.setStyleSheet("""
            #tradeInfoPanel {
                background-color: #16213e;
                border: 1px solid #2a2a4e;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        self._labels = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        columns = [
            ('model', 'Model'),
            ('zone_type', 'Zone Type'),
            ('zone_poc', 'Zone POC'),
            ('entry', 'Entry'),
            ('ai_prediction', 'AI Prediction'),
        ]

        for key, title in columns:
            col = QVBoxLayout()
            col.setSpacing(2)

            header = QLabel(title)
            header.setFont(QFont("Segoe UI", 10))
            header.setStyleSheet("color: #888888;")

            value = QLabel("--")
            value.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            value.setStyleSheet("color: #ffffff;")

            col.addWidget(header)
            col.addWidget(value)
            layout.addLayout(col)

            self._labels[key] = value

    def update_trade(self, trade, ai_prediction=None):
        """
        Update all labels from a TradeWithMetrics object.

        Args:
            trade: TradeWithMetrics object
            ai_prediction: Optional dict from ai_predictions table
        """
        self._labels['model'].setText(trade.model or 'N/A')
        self._labels['zone_type'].setText(trade.zone_type or 'N/A')

        zone_mid = trade.trade.zone_mid
        self._labels['zone_poc'].setText(f"${zone_mid:.2f}" if zone_mid else "N/A")

        self._labels['entry'].setText(
            f"${trade.entry_price:.2f}" if trade.entry_price else "N/A"
        )

        # AI prediction with color coding
        if ai_prediction:
            pred = ai_prediction.get('prediction', 'N/A')
            conf = ai_prediction.get('confidence', '')

            if pred == 'TRADE':
                pred_color = '#4CAF50'
            elif pred == 'NO_TRADE':
                pred_color = '#FF5252'
            else:
                pred_color = '#888888'

            conf_colors = {'HIGH': '#4CAF50', 'MEDIUM': '#FFD700', 'LOW': '#FF9800'}
            conf_color = conf_colors.get(conf, '#888888')

            label = self._labels['ai_prediction']
            label.setText(f"{pred} ({conf})")
            label.setStyleSheet(f"color: {pred_color}; font-size: 10pt; font-weight: bold;")
        else:
            self._labels['ai_prediction'].setText("--")
            self._labels['ai_prediction'].setStyleSheet("color: #555555; font-size: 10pt; font-weight: bold;")

    def clear(self):
        """Reset all labels to default."""
        for label in self._labels.values():
            label.setText("--")
            label.setStyleSheet("color: #ffffff;")

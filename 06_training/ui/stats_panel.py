"""
Epoch Trading System - Stats Panel
Trade statistics display (P&L, MFE/MAE, Duration, R-levels).
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QGroupBox, QPushButton, QWidget
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from datetime import time


class MetricWidget(QFrame):
    """Single metric display with label, value, and delta."""

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #16213e; border-radius: 4px; padding: 6px;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        self._label = QLabel(label)
        self._label.setFont(QFont("Segoe UI", 10))
        self._label.setStyleSheet("color: #888888;")

        self._value = QLabel("--")
        self._value.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._value.setStyleSheet("color: #ffffff;")

        self._delta = QLabel("")
        self._delta.setFont(QFont("Segoe UI", 10))
        self._delta.setStyleSheet("color: #888888;")

        layout.addWidget(self._label)
        layout.addWidget(self._value)
        layout.addWidget(self._delta)

    def set_value(self, value: str, delta: str = "", positive: bool = True):
        self._value.setText(value)
        self._delta.setText(delta)
        if delta:
            color = "#26a69a" if positive else "#ef5350"
            self._delta.setStyleSheet(f"color: {color};")


class StatsPanel(QFrame):
    """Trade statistics panel with metrics, R-levels, crossings, and details."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("Trade Statistics")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(title)

        # Main metrics row (4 columns)
        metrics_row = QHBoxLayout()
        self._pnl = MetricWidget("P&L (R)")
        self._mfe = MetricWidget("MFE (R)")
        self._mae = MetricWidget("MAE (R)")
        self._duration = MetricWidget("Duration")
        metrics_row.addWidget(self._pnl)
        metrics_row.addWidget(self._mfe)
        metrics_row.addWidget(self._mae)
        metrics_row.addWidget(self._duration)
        layout.addLayout(metrics_row)

        # R-Levels row
        self._r_levels_frame = QFrame()
        self._r_levels_frame.setStyleSheet("background-color: #16213e; border-radius: 4px; padding: 6px;")
        r_layout = QVBoxLayout(self._r_levels_frame)
        r_layout.setContentsMargins(8, 6, 8, 6)

        r_title = QLabel("R-Levels (Stop = M5 ATR 1.1x)")
        r_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        r_title.setStyleSheet("color: #e0e0e0;")
        r_layout.addWidget(r_title)

        r_row = QHBoxLayout()
        self._r_labels = {}
        for key in ['stop', 'entry', '1r', '2r', '3r']:
            lbl = QLabel(f"{key.upper()}: --")
            lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            lbl.setStyleSheet("color: #e0e0e0;")
            r_row.addWidget(lbl)
            self._r_labels[key] = lbl
        r_layout.addLayout(r_row)
        layout.addWidget(self._r_levels_frame)

        # R-Level Crossings row
        self._crossings_frame = QFrame()
        self._crossings_frame.setStyleSheet("background-color: #16213e; border-radius: 4px; padding: 6px;")
        c_layout = QVBoxLayout(self._crossings_frame)
        c_layout.setContentsMargins(8, 6, 8, 6)

        c_title = QLabel("R-Level Crossings (Health at crossing)")
        c_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        c_title.setStyleSheet("color: #e0e0e0;")
        c_layout.addWidget(c_title)

        c_row = QHBoxLayout()
        self._crossing_labels = {}
        for key in ['1r', '2r', '3r']:
            lbl = QLabel(f"{key.upper()}: Not reached")
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setStyleSheet("color: #888888;")
            c_row.addWidget(lbl)
            self._crossing_labels[key] = lbl
        c_layout.addLayout(c_row)
        layout.addWidget(self._crossings_frame)

        # Collapsible details
        self._details_btn = QPushButton("Full Trade Details")
        self._details_btn.setCheckable(True)
        self._details_btn.setChecked(False)
        self._details_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a4e; color: #e0e0e0;
                border: 1px solid #333; border-radius: 4px;
                padding: 6px; text-align: left; font-weight: bold;
            }
            QPushButton:checked { background-color: #3a3a5e; }
        """)
        self._details_btn.toggled.connect(self._toggle_details)
        layout.addWidget(self._details_btn)

        self._details_frame = QFrame()
        self._details_frame.setVisible(False)
        self._details_frame.setStyleSheet("background-color: #16213e; border-radius: 4px; padding: 8px;")
        d_layout = QGridLayout(self._details_frame)
        d_layout.setSpacing(4)

        self._detail_labels = {}
        detail_fields = [
            ('model', 'Model'), ('zone_type', 'Zone Type'), ('direction', 'Direction'),
            ('zone_tier', 'Zone Tier'), ('zone_rank', 'Zone Rank'),
            ('entry_price', 'Entry'), ('entry_time', 'Entry Time'),
            ('exit_price', 'Exit'), ('exit_time', 'Exit Time'),
            ('exit_reason', 'Exit Reason'),
            ('risk', 'Risk/Share'), ('stop_price', 'Stop Price'),
            ('outcome', 'Outcome'), ('win', 'Win (R>0)'),
            ('entry_health', 'Entry Health'), ('mfe_health', 'MFE Health'),
            ('mae_health', 'MAE Health'), ('exit_health', 'Exit Health'),
            ('zone_high', 'Zone High'), ('zone_poc', 'Zone POC'), ('zone_low', 'Zone Low'),
        ]

        for i, (key, label_text) in enumerate(detail_fields):
            row = i // 3
            col = (i % 3) * 2

            lbl = QLabel(f"{label_text}:")
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setStyleSheet("color: #888888;")
            d_layout.addWidget(lbl, row, col)

            val = QLabel("--")
            val.setFont(QFont("Segoe UI", 10))
            val.setStyleSheet("color: #e0e0e0;")
            d_layout.addWidget(val, row, col + 1)
            self._detail_labels[key] = val

        layout.addWidget(self._details_frame)

    def _toggle_details(self, checked: bool):
        self._details_frame.setVisible(checked)
        arrow = "v" if checked else ">"
        self._details_btn.setText(f"{arrow} Full Trade Details")

    def update_trade(self, trade):
        """Update all stats from TradeWithMetrics."""
        # P&L
        pnl_r = trade.pnl_r
        pnl_points = trade.pnl_points or 0
        is_winner = trade.is_winner_r

        if pnl_r is not None:
            self._pnl.set_value(
                f"{pnl_r:+.2f}R",
                f"{'Winner' if is_winner else 'Loser'} ({pnl_points:+.2f} pts)",
                positive=is_winner
            )
        else:
            self._pnl.set_value(f"{pnl_points:+.2f} pts", "", positive=pnl_points >= 0)

        # MFE
        mfe_r = trade.mfe_r
        mfe_points = trade.mfe_points or 0
        if mfe_r is not None:
            delta = f"Bar {trade.mfe_bars} (+{abs(mfe_points):.2f} pts)" if trade.mfe_bars else f"+{abs(mfe_points):.2f} pts"
            self._mfe.set_value(f"+{abs(mfe_r):.2f}R", delta, positive=True)
        else:
            self._mfe.set_value(f"+{abs(mfe_points):.2f} pts", "", positive=True)

        # MAE
        mae_r = trade.mae_r
        mae_points = trade.mae_points or 0
        if mae_r is not None:
            delta = f"Bar {trade.mae_bars} ({mae_points:.2f} pts)" if trade.mae_bars else f"{mae_points:.2f} pts"
            self._mae.set_value(f"{mae_r:.2f}R", delta, positive=False)
        else:
            self._mae.set_value(f"{mae_points:.2f} pts", "", positive=False)

        # Duration
        duration = trade.duration_minutes
        if duration:
            duration_str = f"{duration // 60}h {duration % 60}m" if duration >= 60 else f"{duration}m"
        else:
            duration_str = "N/A"
        self._duration.set_value(duration_str, "EOD 15:30")

        # R-Levels
        stop = trade.default_stop_price
        self._r_labels['stop'].setText(f"Stop: ${stop:.2f}" if stop else "Stop: N/A")
        self._r_labels['stop'].setStyleSheet("color: #FF1744;")
        self._r_labels['entry'].setText(f"Entry: ${trade.entry_price:.2f}" if trade.entry_price else "Entry: N/A")
        self._r_labels['entry'].setStyleSheet("color: #00C853;")

        r1 = trade.r1_price
        self._r_labels['1r'].setText(f"1R: ${r1:.2f}" if r1 else "1R: N/A")
        self._r_labels['1r'].setStyleSheet("color: #4CAF50;")

        r2 = trade.r2_price
        self._r_labels['2r'].setText(f"2R: ${r2:.2f}" if r2 else "2R: N/A")
        self._r_labels['2r'].setStyleSheet("color: #8BC34A;")

        r3 = trade.r3_price
        self._r_labels['3r'].setText(f"3R: ${r3:.2f}" if r3 else "3R: N/A")
        self._r_labels['3r'].setStyleSheet("color: #CDDC39;")

        # R-Level Crossings
        has_crossings = trade.r1_crossed or trade.r2_crossed or trade.r3_crossed
        self._crossings_frame.setVisible(has_crossings)

        if has_crossings:
            for level, crossed, t, health, delta in [
                ('1r', trade.r1_crossed, trade.r1_time, trade.r1_health, trade.r1_health_delta),
                ('2r', trade.r2_crossed, trade.r2_time, trade.r2_health, trade.r2_health_delta),
                ('3r', trade.r3_crossed, trade.r3_time, trade.r3_health, trade.r3_health_delta),
            ]:
                if crossed:
                    health_str = f"{health}/10" if health is not None else "N/A"
                    delta_str = ""
                    if delta is not None:
                        delta_str = f" ({'+' if delta >= 0 else ''}{delta})"
                    time_str = t.strftime("%H:%M") if t else "N/A"
                    self._crossing_labels[level].setText(
                        f"{level.upper()}: {time_str} | Health: {health_str}{delta_str}"
                    )
                    self._crossing_labels[level].setStyleSheet("color: #e0e0e0;")
                else:
                    self._crossing_labels[level].setText(f"{level.upper()}: Not reached")
                    self._crossing_labels[level].setStyleSheet("color: #888888;")

        # Details
        self._detail_labels['model'].setText(str(trade.model or 'N/A'))
        self._detail_labels['zone_type'].setText(str(trade.zone_type or 'N/A'))
        self._detail_labels['direction'].setText(str(trade.direction or 'N/A'))
        self._detail_labels['zone_tier'].setText(str(trade.zone_tier or 'N/A'))
        self._detail_labels['zone_rank'].setText(str(trade.zone_rank or 'N/A'))
        self._detail_labels['entry_price'].setText(f"${trade.entry_price:.2f}" if trade.entry_price else "N/A")
        self._detail_labels['entry_time'].setText(
            trade.entry_time.strftime("%H:%M:%S ET") if trade.entry_time else "N/A"
        )
        self._detail_labels['exit_price'].setText(f"${trade.exit_price:.2f}" if trade.exit_price else "N/A")
        self._detail_labels['exit_time'].setText(
            trade.exit_time.strftime("%H:%M:%S ET") if trade.exit_time else "N/A"
        )
        self._detail_labels['exit_reason'].setText(str(trade.exit_reason or 'N/A'))
        risk = trade.risk_per_share
        self._detail_labels['risk'].setText(f"${risk:.2f}" if risk else "N/A")
        self._detail_labels['stop_price'].setText(f"${stop:.2f}" if stop else "N/A")
        self._detail_labels['outcome'].setText(trade.outcome_r)
        self._detail_labels['win'].setText("Yes" if trade.is_winner_r else "No")
        self._detail_labels['entry_health'].setText(
            f"{trade.entry_health}/10" if trade.entry_health is not None else "N/A"
        )
        self._detail_labels['mfe_health'].setText(
            f"{trade.mfe_health}/10" if trade.mfe_health is not None else "N/A"
        )
        self._detail_labels['mae_health'].setText(
            f"{trade.mae_health}/10" if trade.mae_health is not None else "N/A"
        )
        self._detail_labels['exit_health'].setText(
            f"{trade.exit_health}/10" if trade.exit_health is not None else "N/A"
        )
        self._detail_labels['zone_high'].setText(
            f"${trade.zone_high:.2f}" if trade.zone_high else "N/A"
        )
        zone_mid = trade.trade.zone_mid
        self._detail_labels['zone_poc'].setText(f"${zone_mid:.2f}" if zone_mid else "N/A")
        self._detail_labels['zone_low'].setText(
            f"${trade.zone_low:.2f}" if trade.zone_low else "N/A"
        )

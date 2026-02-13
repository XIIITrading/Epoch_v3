"""
Dashboard Tab
Epoch Trading System v2.0 - XIII Trading LLC

Summary metrics, ticker status, and TradingView export.
"""

from datetime import datetime
from typing import Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QGroupBox, QTextEdit, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.tabs.base_tab import BaseTab
from ui.styles import COLORS
from config import RISK_PER_TRADE


class DashboardTab(BaseTab):
    """
    Dashboard Tab

    Features:
    - Pipeline summary metrics
    - Ticker analysis status table
    - Zone breakdown by tier
    - Trading setups summary
    - TradingView export section
    """

    def _setup_ui(self):
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("DASHBOARD")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Metrics section
        metrics_section = self._create_metrics_section()
        layout.addWidget(metrics_section)

        # Ticker status table
        status_section = self._create_status_section()
        layout.addWidget(status_section)

        # Two-column layout for zone breakdown and setups
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)

        # Zone breakdown
        zone_section = self._create_zone_breakdown_section()
        columns_layout.addWidget(zone_section)

        # Setups summary
        setups_section = self._create_setups_section()
        columns_layout.addWidget(setups_section)

        layout.addLayout(columns_layout)

        # Share sizing section
        sizing_section = self._create_share_sizing_section()
        layout.addWidget(sizing_section)

        # TradingView export section
        tv_section = self._create_tradingview_section()
        layout.addWidget(tv_section)

        layout.addStretch()

    def _create_metrics_section(self) -> QFrame:
        """Create the summary metrics section."""
        frame = QFrame()
        frame.setObjectName("sectionFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Section title
        title = QLabel("PIPELINE SUMMARY")
        title.setObjectName("sectionLabel")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(title)

        # Metrics grid
        grid = QGridLayout()
        grid.setSpacing(20)

        # Create metric displays
        self.metric_labels = {}
        metrics = [
            ("total_tickers", "Total Tickers", "0"),
            ("successful", "Successful", "0"),
            ("failed", "Failed", "0"),
            ("total_zones", "Total Zones", "0"),
            ("setups_found", "Setups Found", "0"),
            ("analysis_date", "Analysis Date", "-"),
        ]

        for i, (key, label, default) in enumerate(metrics):
            row = i // 3
            col = i % 3

            metric_frame = QFrame()
            metric_layout = QVBoxLayout(metric_frame)
            metric_layout.setContentsMargins(12, 8, 12, 8)
            metric_layout.setSpacing(4)

            label_widget = QLabel(label)
            label_widget.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
            metric_layout.addWidget(label_widget)

            value_widget = QLabel(default)
            value_widget.setStyleSheet("font-size: 18pt; font-weight: bold;")
            metric_layout.addWidget(value_widget)

            self.metric_labels[key] = value_widget
            grid.addWidget(metric_frame, row, col)

        layout.addLayout(grid)

        return frame

    def _create_status_section(self) -> QFrame:
        """Create the ticker status table section."""
        frame, content_layout = self.create_section_frame("TICKER ANALYSIS STATUS")

        # Create table
        headers = ["Ticker", "Type", "Status", "Price", "Direction", "Zones", "Setups"]
        self.status_table = self.create_table(headers)
        content_layout.addWidget(self.status_table)

        # Placeholder message
        self.status_placeholder = QLabel("Run analysis to see ticker status")
        self.status_placeholder.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 20px;")
        self.status_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.status_placeholder)

        return frame

    def _create_zone_breakdown_section(self) -> QFrame:
        """Create the zone breakdown section."""
        frame, content_layout = self.create_section_frame("ZONE BREAKDOWN")

        # Tier breakdown
        self.tier_labels = {}
        tiers = [("T3", "T3 (Best)", COLORS['tier_t3']),
                 ("T2", "T2 (Medium)", COLORS['tier_t2']),
                 ("T1", "T1 (Basic)", COLORS['tier_t1'])]

        for tier_key, tier_label, color in tiers:
            row = QHBoxLayout()
            row.setSpacing(12)

            label = QLabel(tier_label)
            label.setStyleSheet(f"color: {color}; font-weight: bold;")
            label.setFixedWidth(100)
            row.addWidget(label)

            count = QLabel("0")
            count.setStyleSheet("font-weight: bold;")
            row.addWidget(count)

            row.addStretch()
            content_layout.addLayout(row)

            self.tier_labels[tier_key] = count

        return frame

    def _create_setups_section(self) -> QFrame:
        """Create the setups summary section."""
        frame, content_layout = self.create_section_frame("TRADING SETUPS")

        # Primary setups
        primary_header = QLabel("Primary Setups")
        primary_header.setStyleSheet(f"color: {COLORS['bull']}; font-weight: bold;")
        content_layout.addWidget(primary_header)

        self.primary_setups_label = QLabel("No setups found")
        self.primary_setups_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        content_layout.addWidget(self.primary_setups_label)

        content_layout.addSpacing(12)

        # Secondary setups
        secondary_header = QLabel("Secondary Setups")
        secondary_header.setStyleSheet(f"color: {COLORS['tier_t2']}; font-weight: bold;")
        content_layout.addWidget(secondary_header)

        self.secondary_setups_label = QLabel("No setups found")
        self.secondary_setups_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        content_layout.addWidget(self.secondary_setups_label)

        return frame

    def _create_share_sizing_section(self) -> QFrame:
        """Create the share sizing section with ATR-based position sizing."""
        frame, content_layout = self.create_section_frame(
            f"SHARE SIZING (${RISK_PER_TRADE:.0f} RISK)"
        )

        headers = [
            "Ticker", "H1 ATR", "M15 ATR", "M5 ATR",
            "Risk ($)", "M15 Shares", "M5 Shares"
        ]
        self.share_sizing_table = self.create_table(headers)
        content_layout.addWidget(self.share_sizing_table)

        self.share_sizing_placeholder = QLabel("Run analysis to see share sizing")
        self.share_sizing_placeholder.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 20px;")
        self.share_sizing_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.share_sizing_placeholder)

        return frame

    def _create_tradingview_section(self) -> QFrame:
        """Create the TradingView export section."""
        frame, content_layout = self.create_section_frame("TRADINGVIEW EXPORT")

        # Export buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.copy_pine6_btn = QPushButton("Copy PineScript 6")
        self.copy_pine6_btn.clicked.connect(self._copy_pine6)
        button_layout.addWidget(self.copy_pine6_btn)

        self.copy_pine16_btn = QPushButton("Copy PineScript 16")
        self.copy_pine16_btn.clicked.connect(self._copy_pine16)
        button_layout.addWidget(self.copy_pine16_btn)

        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.clicked.connect(self._export_csv)
        button_layout.addWidget(self.export_csv_btn)

        button_layout.addStretch()
        content_layout.addLayout(button_layout)

        # TradingView data table
        tv_headers = ["Ticker", "Pri High", "Pri Low", "Pri Target", "Sec High", "Sec Low", "Sec Target"]
        self.tv_table = self.create_table(tv_headers)
        content_layout.addWidget(self.tv_table)

        return frame

    def on_results_updated(self, results: Dict[str, Any]):
        """Handle results update."""
        if not results.get("run_complete"):
            return

        # Update metrics
        all_results = results.get("index", []) + results.get("custom", [])
        successful = sum(1 for r in all_results if r.get("success", False))
        failed = len(all_results) - successful
        total_zones = sum(len(r.get("filtered_zones", [])) for r in all_results)
        setups = sum(1 for r in all_results if r.get("primary_setup") or r.get("secondary_setup"))

        self.metric_labels["total_tickers"].setText(str(len(all_results)))
        self.metric_labels["successful"].setText(str(successful))
        self.metric_labels["successful"].setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {COLORS['status_complete']};")
        self.metric_labels["failed"].setText(str(failed))
        if failed > 0:
            self.metric_labels["failed"].setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {COLORS['status_error']};")
        self.metric_labels["total_zones"].setText(str(total_zones))
        self.metric_labels["setups_found"].setText(str(setups))

        analysis_date = results.get("analysis_date")
        if analysis_date:
            self.metric_labels["analysis_date"].setText(str(analysis_date))

        # Update status table
        self._update_status_table(all_results)

        # Update tier breakdown
        self._update_tier_breakdown(all_results)

        # Update setups
        self._update_setups(all_results)

        # Update share sizing table
        self._update_share_sizing_table(all_results)

        # Update TradingView table
        self._update_tv_table(all_results)

    def _update_status_table(self, results: List[Dict]):
        """Update the ticker status table."""
        if not results:
            self.status_placeholder.show()
            self.status_table.hide()
            return

        self.status_placeholder.hide()
        self.status_table.show()

        data = []
        colors = []

        for r in results:
            ticker = r.get("ticker", "")
            ticker_type = "Index" if r.get("is_index") else "Custom"
            success = r.get("success", False)
            status = "OK" if success else "Failed"
            price = f"${r.get('price', 0):.2f}" if r.get('price') else "-"
            direction = r.get("direction", "-")
            zones = len(r.get("filtered_zones", []))
            has_setup = "Yes" if r.get("primary_setup") or r.get("secondary_setup") else "No"

            data.append([ticker, ticker_type, status, price, direction, str(zones), has_setup])

            if not success:
                colors.append(COLORS['status_error'])
            elif has_setup == "Yes":
                colors.append(COLORS['status_complete'])
            else:
                colors.append(None)

        self.populate_table(self.status_table, data, colors)

    def _update_tier_breakdown(self, results: List[Dict]):
        """Update tier breakdown counts."""
        tier_counts = {"T3": 0, "T2": 0, "T1": 0}

        for r in results:
            for zone in r.get("filtered_zones", []):
                tier = zone.get("tier", "T1")
                if tier in tier_counts:
                    tier_counts[tier] += 1

        for tier, count in tier_counts.items():
            self.tier_labels[tier].setText(str(count))

    def _update_setups(self, results: List[Dict]):
        """Update setups summary."""
        primary_setups = []
        secondary_setups = []

        for r in results:
            ticker = r.get("ticker", "")
            if r.get("primary_setup"):
                setup = r["primary_setup"]
                primary_setups.append(f"{ticker}: {setup.get('direction', '-')} @ {setup.get('poc', '-')}")
            if r.get("secondary_setup"):
                setup = r["secondary_setup"]
                secondary_setups.append(f"{ticker}: {setup.get('direction', '-')} @ {setup.get('poc', '-')}")

        if primary_setups:
            self.primary_setups_label.setText("\n".join(primary_setups))
            self.primary_setups_label.setStyleSheet("")
        else:
            self.primary_setups_label.setText("No primary setups found")
            self.primary_setups_label.setStyleSheet(f"color: {COLORS['text_muted']};")

        if secondary_setups:
            self.secondary_setups_label.setText("\n".join(secondary_setups))
            self.secondary_setups_label.setStyleSheet("")
        else:
            self.secondary_setups_label.setText("No secondary setups found")
            self.secondary_setups_label.setStyleSheet(f"color: {COLORS['text_muted']};")

    def _update_share_sizing_table(self, results: List[Dict]):
        """Update the share sizing table with ATR-based position sizing for all tickers."""
        if not results:
            self.share_sizing_placeholder.show()
            self.share_sizing_table.hide()
            return

        data = []
        colors = []

        for r in results:
            if not r.get("success"):
                continue

            ticker = r.get("ticker", "")
            bar_data = r.get("bar_data", {})

            h1_atr = bar_data.get("h1_atr")
            m15_atr = bar_data.get("m15_atr")
            m5_atr = bar_data.get("m5_atr")

            def fmt_atr(val):
                if val is None:
                    return "-"
                return f"${val:.4f}"

            # Calculate shares for M15 and M5 based on risk
            def calc_shares(atr_val):
                if atr_val and atr_val > 0:
                    return int(RISK_PER_TRADE / atr_val)
                return None

            m15_shares = calc_shares(m15_atr)
            m5_shares = calc_shares(m5_atr)

            def fmt_shares(val):
                if val is None:
                    return "-"
                return str(val)

            data.append([
                ticker,
                fmt_atr(h1_atr),
                fmt_atr(m15_atr),
                fmt_atr(m5_atr),
                f"${RISK_PER_TRADE:.0f}",
                fmt_shares(m15_shares),
                fmt_shares(m5_shares),
            ])

            # Color code by M5 share count (primary trading timeframe)
            share_val = m5_shares if m5_shares else 0
            if share_val >= 100:
                colors.append(COLORS['status_complete'])
            elif share_val >= 50:
                colors.append(COLORS['tier_t2'])
            else:
                colors.append(COLORS['status_error'])

        if data:
            self.share_sizing_placeholder.hide()
            self.share_sizing_table.show()
            self.populate_table(self.share_sizing_table, data, colors)
        else:
            self.share_sizing_placeholder.show()
            self.share_sizing_table.hide()

    def _update_tv_table(self, results: List[Dict]):
        """Update TradingView export table."""
        data = []

        for r in results:
            if not r.get("success"):
                continue

            ticker = r.get("ticker", "")
            pri = r.get("primary_setup", {})
            sec = r.get("secondary_setup", {})

            row = [
                ticker,
                f"{pri.get('zone_high', '-')}" if pri else "-",
                f"{pri.get('zone_low', '-')}" if pri else "-",
                f"{pri.get('target', '-')}" if pri else "-",
                f"{sec.get('zone_high', '-')}" if sec else "-",
                f"{sec.get('zone_low', '-')}" if sec else "-",
                f"{sec.get('target', '-')}" if sec else "-",
            ]
            data.append(row)

        if data:
            self.populate_table(self.tv_table, data)

    def _copy_pine6(self):
        """Copy PineScript 6 format to clipboard."""
        results = self.get_all_tickers_results()
        if not results:
            QMessageBox.warning(self, "No Data", "No analysis results to export.")
            return

        lines = []
        for r in results:
            if not r.get("success"):
                continue
            ticker = r.get("ticker", "")
            pri = r.get("primary_setup", {})
            sec = r.get("secondary_setup", {})

            values = [
                pri.get("zone_high", 0) if pri else 0,
                pri.get("zone_low", 0) if pri else 0,
                pri.get("target", 0) if pri else 0,
                sec.get("zone_high", 0) if sec else 0,
                sec.get("zone_low", 0) if sec else 0,
                sec.get("target", 0) if sec else 0,
            ]
            lines.append(f"{ticker}:{','.join(str(v) for v in values)}")

        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText("\n".join(lines))
        QMessageBox.information(self, "Copied", "PineScript 6 data copied to clipboard.")

    def _copy_pine16(self):
        """Copy PineScript 16 format to clipboard."""
        results = self.get_all_tickers_results()
        if not results:
            QMessageBox.warning(self, "No Data", "No analysis results to export.")
            return

        lines = []
        for r in results:
            if not r.get("success"):
                continue
            ticker = r.get("ticker", "")
            pri = r.get("primary_setup", {})
            sec = r.get("secondary_setup", {})
            pocs = r.get("hvn_pocs", [])[:10]

            values = [
                pri.get("zone_high", 0) if pri else 0,
                pri.get("zone_low", 0) if pri else 0,
                pri.get("target", 0) if pri else 0,
                sec.get("zone_high", 0) if sec else 0,
                sec.get("zone_low", 0) if sec else 0,
                sec.get("target", 0) if sec else 0,
            ]
            # Add 10 POC prices
            for i in range(10):
                if i < len(pocs):
                    values.append(pocs[i].get("price", 0))
                else:
                    values.append(0)

            lines.append(f"{ticker}:{','.join(str(v) for v in values)}")

        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText("\n".join(lines))
        QMessageBox.information(self, "Copied", "PineScript 16 data copied to clipboard.")

    def _export_csv(self):
        """Export data to CSV file."""
        results = self.get_all_tickers_results()
        if not results:
            QMessageBox.warning(self, "No Data", "No analysis results to export.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV Files (*.csv)"
        )
        if not filename:
            return

        import csv
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Ticker", "Pri High", "Pri Low", "Pri Target",
                           "Sec High", "Sec Low", "Sec Target"])

            for r in results:
                if not r.get("success"):
                    continue
                ticker = r.get("ticker", "")
                pri = r.get("primary_setup", {})
                sec = r.get("secondary_setup", {})

                writer.writerow([
                    ticker,
                    pri.get("zone_high", "") if pri else "",
                    pri.get("zone_low", "") if pri else "",
                    pri.get("target", "") if pri else "",
                    sec.get("zone_high", "") if sec else "",
                    sec.get("zone_low", "") if sec else "",
                    sec.get("target", "") if sec else "",
                ])

        QMessageBox.information(self, "Exported", f"Data exported to {filename}")

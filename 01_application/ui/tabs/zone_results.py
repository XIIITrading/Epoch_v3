"""
Zone Results Tab
Epoch Trading System v2.0 - XIII Trading LLC

Filtered zones with tier classification.
"""

from typing import Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.tabs.base_tab import BaseTab
from ui.styles import COLORS


class ZoneResultsTab(BaseTab):
    """
    Zone Results Tab

    Displays filtered zones with:
    - Tier classification (T3=best, T2=medium, T1=basic)
    - Bull/Bear POC flags
    - ATR distance
    - Proximity groups
    """

    def _setup_ui(self):
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title with filters
        header = QHBoxLayout()
        title = QLabel("ZONE RESULTS")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.addWidget(title)

        header.addStretch()

        # Ticker filter
        header.addWidget(QLabel("Ticker:"))
        self.ticker_filter = QComboBox()
        self.ticker_filter.setMinimumWidth(120)
        self.ticker_filter.addItem("All Tickers", None)
        self.ticker_filter.currentIndexChanged.connect(self._on_filter_changed)
        header.addWidget(self.ticker_filter)

        # Tier filter
        header.addWidget(QLabel("Tier:"))
        self.tier_filter = QComboBox()
        self.tier_filter.addItems(["All", "T3", "T2", "T1"])
        self.tier_filter.currentIndexChanged.connect(self._on_filter_changed)
        header.addWidget(self.tier_filter)

        # Setup zones only
        self.setup_only = QCheckBox("Setup Zones Only")
        self.setup_only.stateChanged.connect(self._on_filter_changed)
        header.addWidget(self.setup_only)

        layout.addLayout(header)

        # Summary stats
        stats_layout = QHBoxLayout()
        self.total_label = QLabel("Total: 0")
        self.total_label.setStyleSheet("font-weight: bold;")
        stats_layout.addWidget(self.total_label)

        self.t3_label = QLabel("T3: 0")
        self.t3_label.setStyleSheet(f"color: {COLORS['tier_t3']}; font-weight: bold;")
        stats_layout.addWidget(self.t3_label)

        self.t2_label = QLabel("T2: 0")
        self.t2_label.setStyleSheet(f"color: {COLORS['tier_t2']}; font-weight: bold;")
        stats_layout.addWidget(self.t2_label)

        self.t1_label = QLabel("T1: 0")
        self.t1_label.setStyleSheet(f"color: {COLORS['tier_t1']}; font-weight: bold;")
        stats_layout.addWidget(self.t1_label)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Zones table
        zones_section = self._create_zones_section()
        layout.addWidget(zones_section)

        layout.addStretch()

    def _create_zones_section(self) -> QFrame:
        """Create the filtered zones table section."""
        frame, content_layout = self.create_section_frame("FILTERED ZONES")

        headers = [
            "Ticker", "Zone ID", "Tier", "HVN POC", "Zone High", "Zone Low",
            "Bull POC", "Bear POC", "ATR Dist", "Score", "Confluences"
        ]
        self.zones_table = self.create_table(headers)
        content_layout.addWidget(self.zones_table)

        return frame

    def on_results_updated(self, results: Dict[str, Any]):
        """Handle results update."""
        if not results.get("run_complete"):
            return

        # Update ticker filter
        all_results = results.get("index", []) + results.get("custom", [])
        self.ticker_filter.clear()
        self.ticker_filter.addItem("All Tickers", None)
        for r in all_results:
            if r.get("success"):
                self.ticker_filter.addItem(r.get("ticker", ""), r.get("ticker"))

        self._update_display(all_results)

    def _on_filter_changed(self, *args):
        """Handle filter change."""
        results = self.get_results()
        all_results = results.get("index", []) + results.get("custom", [])
        self._update_display(all_results)

    def _update_display(self, all_results: List[Dict]):
        """Update the zones display with filters applied."""
        selected_ticker = self.ticker_filter.currentData()
        selected_tier = self.tier_filter.currentText()
        setup_only = self.setup_only.isChecked()

        # Collect filtered zones
        all_zones = []
        tier_counts = {"T3": 0, "T2": 0, "T1": 0}

        for r in all_results:
            if not r.get("success"):
                continue
            ticker = r.get("ticker", "")
            if selected_ticker and ticker != selected_ticker:
                continue

            # Get setup zones for this ticker
            setup_zones = set()
            if r.get("primary_setup"):
                setup_zones.add(r["primary_setup"].get("zone_id"))
            if r.get("secondary_setup"):
                setup_zones.add(r["secondary_setup"].get("zone_id"))

            for zone in r.get("filtered_zones", []):
                tier = zone.get("tier", "T1")
                zone_id = zone.get("zone_id", "")

                # Apply tier filter
                if selected_tier != "All" and tier != selected_tier:
                    continue

                # Apply setup filter
                if setup_only and zone_id not in setup_zones:
                    continue

                # Count tiers
                if tier in tier_counts:
                    tier_counts[tier] += 1

                zone_data = {
                    "ticker": ticker,
                    "is_setup": zone_id in setup_zones,
                    **zone
                }
                all_zones.append(zone_data)

        # Update stats
        total = sum(tier_counts.values())
        self.total_label.setText(f"Total: {total}")
        self.t3_label.setText(f"T3: {tier_counts['T3']}")
        self.t2_label.setText(f"T2: {tier_counts['T2']}")
        self.t1_label.setText(f"T1: {tier_counts['T1']}")

        # Update table
        data = []
        colors = []

        for zone in all_zones:
            tier = zone.get("tier", "T1")
            confluences = zone.get("confluences", [])
            if isinstance(confluences, list):
                confluences_str = ", ".join(confluences[:3])
            else:
                confluences_str = str(confluences)

            row = [
                zone.get("ticker", ""),
                zone.get("zone_id", ""),
                tier,
                f"${zone.get('hvn_poc', 0):.2f}",
                f"${zone.get('zone_high', 0):.2f}",
                f"${zone.get('zone_low', 0):.2f}",
                "Yes" if zone.get("is_bull_poc") else "-",
                "Yes" if zone.get("is_bear_poc") else "-",
                f"{zone.get('atr_distance', 0):.2f}",
                f"{zone.get('score', 0):.1f}",
                confluences_str
            ]
            data.append(row)

            # Color by tier
            if tier == "T3":
                colors.append(COLORS['tier_t3'])
            elif tier == "T2":
                colors.append(COLORS['tier_t2'])
            elif tier == "T1":
                colors.append(COLORS['tier_t1'])
            else:
                colors.append(None)

        if data:
            self.populate_table(self.zones_table, data, colors)
        else:
            self.populate_table(self.zones_table, [["No zones match filters", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"]])

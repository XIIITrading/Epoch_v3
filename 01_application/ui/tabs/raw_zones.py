"""
Raw Zones Tab
Epoch Trading System v2.0 - XIII Trading LLC

All zone candidates before filtering.
"""

from typing import Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.tabs.base_tab import BaseTab
from ui.styles import COLORS


class RawZonesTab(BaseTab):
    """
    Raw Zones Tab

    Displays all zone candidates before filtering:
    - Zone ID and POC rank
    - HVN POC price
    - Zone High/Low boundaries
    - Overlap count (confluence)
    - Score (composite)
    - Rank (L5=highest, L4, L3)
    - Confluences
    """

    def _setup_ui(self):
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title with ticker selector
        header = QHBoxLayout()
        title = QLabel("RAW ZONES")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.addWidget(title)

        header.addStretch()

        # Filter by ticker
        header.addWidget(QLabel("Ticker:"))
        self.ticker_selector = QComboBox()
        self.ticker_selector.setMinimumWidth(120)
        self.ticker_selector.addItem("All Tickers", None)
        self.ticker_selector.currentIndexChanged.connect(self._on_filter_changed)
        header.addWidget(self.ticker_selector)

        layout.addLayout(header)

        # Summary
        self.summary_label = QLabel("No zones loaded")
        self.summary_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.summary_label)

        # Zones table
        zones_section = self._create_zones_section()
        layout.addWidget(zones_section)

        layout.addStretch()

    def _create_zones_section(self) -> QFrame:
        """Create the raw zones table section."""
        frame, content_layout = self.create_section_frame("ALL ZONE CANDIDATES")

        headers = [
            "Ticker", "Zone ID", "POC Rank", "HVN POC",
            "Zone High", "Zone Low", "Overlaps", "Score", "Rank", "Confluences"
        ]
        self.zones_table = self.create_table(headers)
        content_layout.addWidget(self.zones_table)

        return frame

    def on_results_updated(self, results: Dict[str, Any]):
        """Handle results update."""
        if not results.get("run_complete"):
            return

        # Update ticker selector
        all_results = results.get("index", []) + results.get("custom", [])
        self.ticker_selector.clear()
        self.ticker_selector.addItem("All Tickers", None)
        for r in all_results:
            if r.get("success"):
                self.ticker_selector.addItem(r.get("ticker", ""), r.get("ticker"))

        self._update_display(all_results)

    def _on_filter_changed(self, index: int):
        """Handle filter change."""
        results = self.get_results()
        all_results = results.get("index", []) + results.get("custom", [])
        self._update_display(all_results)

    def _update_display(self, all_results: List[Dict]):
        """Update the zones display."""
        selected_ticker = self.ticker_selector.currentData()

        # Collect all raw zones
        all_zones = []
        for r in all_results:
            if not r.get("success"):
                continue
            ticker = r.get("ticker", "")
            if selected_ticker and ticker != selected_ticker:
                continue

            for zone in r.get("raw_zones", []):
                zone_data = {
                    "ticker": ticker,
                    **zone
                }
                all_zones.append(zone_data)

        # Update summary
        self.summary_label.setText(f"Total raw zones: {len(all_zones)}")

        # Update table
        data = []
        colors = []

        for zone in all_zones:
            rank = zone.get("rank", "")
            confluences = zone.get("confluences", [])
            if isinstance(confluences, list):
                confluences_str = ", ".join(confluences[:3])
                if len(confluences) > 3:
                    confluences_str += f" (+{len(confluences)-3})"
            else:
                confluences_str = str(confluences)

            row = [
                zone.get("ticker", ""),
                zone.get("zone_id", ""),
                zone.get("poc_rank", ""),
                f"${zone.get('hvn_poc', 0):.2f}",
                f"${zone.get('zone_high', 0):.2f}",
                f"${zone.get('zone_low', 0):.2f}",
                str(zone.get("overlaps", 0)),
                f"{zone.get('score', 0):.1f}",
                rank,
                confluences_str
            ]
            data.append(row)

            # Color by rank
            if rank == "L5":
                colors.append(COLORS['tier_t3'])
            elif rank == "L4":
                colors.append(COLORS['tier_t2'])
            else:
                colors.append(None)

        if data:
            self.populate_table(self.zones_table, data, colors)
        else:
            self.populate_table(self.zones_table, [["No zones", "-", "-", "-", "-", "-", "-", "-", "-", "-"]])

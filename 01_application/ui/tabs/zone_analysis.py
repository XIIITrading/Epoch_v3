"""
Zone Analysis Tab
Epoch Trading System v2.0 - XIII Trading LLC

Primary and Secondary trading setups displayed on same page.
"""

from typing import Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.tabs.base_tab import BaseTab
from ui.styles import COLORS


class ZoneAnalysisTab(BaseTab):
    """
    Zone Analysis Tab

    Displays on same page:
    - Primary setups (with-trend)
    - Secondary setups (counter-trend)
    - Risk/Reward calculations
    - Position sizing
    """

    def _setup_ui(self):
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Title
        title = QLabel("ZONE ANALYSIS")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Primary setups section
        primary_section = self._create_primary_section()
        layout.addWidget(primary_section)

        # Secondary setups section
        secondary_section = self._create_secondary_section()
        layout.addWidget(secondary_section)

        # Risk sizing section
        risk_section = self._create_risk_section()
        layout.addWidget(risk_section)

        layout.addStretch()

    def _create_primary_section(self) -> QFrame:
        """Create Primary setups section."""
        frame, content_layout = self.create_section_frame("PRIMARY TRADING SETUPS (With-Trend)")

        # Summary label
        self.primary_summary = QLabel("No primary setups found")
        self.primary_summary.setStyleSheet(f"color: {COLORS['text_muted']}; margin-bottom: 8px;")
        content_layout.addWidget(self.primary_summary)

        # Table
        headers = [
            "Ticker", "Direction", "Zone ID", "HVN POC", "Zone High", "Zone Low",
            "Target", "R:R", "Tier", "Confluences"
        ]
        self.primary_table = self.create_table(headers)
        self.primary_table.setMinimumHeight(150)
        content_layout.addWidget(self.primary_table)

        return frame

    def _create_secondary_section(self) -> QFrame:
        """Create Secondary setups section."""
        frame, content_layout = self.create_section_frame("SECONDARY TRADING SETUPS (Counter-Trend)")

        # Summary label
        self.secondary_summary = QLabel("No secondary setups found")
        self.secondary_summary.setStyleSheet(f"color: {COLORS['text_muted']}; margin-bottom: 8px;")
        content_layout.addWidget(self.secondary_summary)

        # Table
        headers = [
            "Ticker", "Direction", "Zone ID", "HVN POC", "Zone High", "Zone Low",
            "Target", "R:R", "Tier", "Confluences"
        ]
        self.secondary_table = self.create_table(headers)
        self.secondary_table.setMinimumHeight(150)
        content_layout.addWidget(self.secondary_table)

        return frame

    def _create_risk_section(self) -> QFrame:
        """Create risk/position sizing section."""
        frame, content_layout = self.create_section_frame("POSITION SIZING (Based on $20 Risk)")

        headers = ["Ticker", "Direction", "Entry", "Stop", "Risk $", "Shares", "Position $"]
        self.risk_table = self.create_table(headers)
        self.risk_table.setMinimumHeight(120)
        content_layout.addWidget(self.risk_table)

        return frame

    def _clean_direction(self, direction) -> str:
        """Clean direction string."""
        if direction is None:
            return "-"
        dir_str = str(direction)
        dir_str = dir_str.replace("Direction.", "").replace("direction.", "")
        dir_str = dir_str.replace("_PLUS", "+").replace("_plus", "+")
        if dir_str.upper() in ["BULL", "BEAR", "NEUTRAL"]:
            dir_str = dir_str.capitalize()
        elif dir_str.upper() == "BULL+":
            dir_str = "Bull+"
        elif dir_str.upper() == "BEAR+":
            dir_str = "Bear+"
        return dir_str

    def _clean_tier(self, tier) -> str:
        """Clean tier string."""
        if tier is None:
            return "-"
        tier_str = str(tier)
        return tier_str.replace("Tier.", "").replace("tier.", "")

    def _clean_rank(self, rank) -> str:
        """Clean rank string."""
        if rank is None:
            return "-"
        rank_str = str(rank)
        return rank_str.replace("Rank.", "").replace("rank.", "")

    def on_results_updated(self, results: Dict[str, Any]):
        """Handle results update."""
        if not results.get("run_complete"):
            return

        all_results = results.get("index", []) + results.get("custom", [])

        # Collect setups
        primary_setups = []
        secondary_setups = []

        for r in all_results:
            if not r.get("success"):
                continue
            ticker = r.get("ticker", "")

            if r.get("primary_setup"):
                setup = dict(r["primary_setup"])  # Copy to avoid modifying original
                setup["ticker"] = ticker
                primary_setups.append(setup)

            if r.get("secondary_setup"):
                setup = dict(r["secondary_setup"])  # Copy to avoid modifying original
                setup["ticker"] = ticker
                secondary_setups.append(setup)

        # Update primary setups
        self._update_setups_table(
            self.primary_table,
            self.primary_summary,
            primary_setups,
            "primary"
        )

        # Update secondary setups
        self._update_setups_table(
            self.secondary_table,
            self.secondary_summary,
            secondary_setups,
            "secondary"
        )

        # Update risk table
        self._update_risk_table(primary_setups + secondary_setups)

    def _update_setups_table(self, table: QTableWidget, summary: QLabel,
                            setups: List[Dict], setup_type: str):
        """Update a setups table."""
        if not setups:
            summary.setText(f"No {setup_type} setups found")
            summary.setStyleSheet(f"color: {COLORS['text_muted']};")
            self.populate_table(table, [["No setups", "-", "-", "-", "-", "-", "-", "-", "-", "-"]])
            return

        summary.setText(f"{len(setups)} {setup_type} setup(s) found")
        summary.setStyleSheet(f"color: {COLORS['status_complete']}; font-weight: bold;")

        data = []
        colors = []

        for setup in setups:
            direction = self._clean_direction(setup.get("direction", "-"))
            rr = setup.get("risk_reward", 0)
            tier = self._clean_tier(setup.get("tier", "-"))

            # Get confluences
            confluences = setup.get("confluences", [])
            if isinstance(confluences, list):
                conf_str = ", ".join(str(c) for c in confluences) if confluences else "-"
            else:
                conf_str = str(confluences) if confluences else "-"

            # Get POC - handle both 'poc' and 'hvn_poc' keys
            poc = setup.get("hvn_poc", setup.get("poc", 0))

            row = [
                setup.get("ticker", ""),
                direction,
                setup.get("zone_id", "").replace(f"{setup.get('ticker', '')}_", ""),
                f"${poc:.2f}" if poc else "-",
                f"${setup.get('zone_high', 0):.2f}" if setup.get('zone_high') else "-",
                f"${setup.get('zone_low', 0):.2f}" if setup.get('zone_low') else "-",
                f"${setup.get('target', 0):.2f}" if setup.get('target') else "-",
                f"{rr:.1f}:1" if rr else "-",
                tier,
                conf_str
            ]
            data.append(row)

            # Color by direction
            if "Bull" in direction or "LONG" in direction.upper():
                colors.append(COLORS['bull'])
            elif "Bear" in direction or "SHORT" in direction.upper():
                colors.append(COLORS['bear'])
            else:
                colors.append(None)

        self.populate_table(table, data, colors)

    def _update_risk_table(self, all_setups: List[Dict]):
        """Update the risk/position sizing table."""
        if not all_setups:
            self.populate_table(self.risk_table, [["No setups", "-", "-", "-", "-", "-", "-"]])
            return

        data = []
        colors = []
        risk_amount = 20.0  # Fixed risk per trade

        for setup in all_setups:
            direction = self._clean_direction(setup.get("direction", "-"))
            poc = setup.get("hvn_poc", setup.get("poc", 0))
            zone_high = setup.get("zone_high", 0)
            zone_low = setup.get("zone_low", 0)

            if not zone_high or not zone_low:
                continue

            # Calculate entry and stop
            if "Bull" in direction or "LONG" in direction.upper():
                entry = zone_low  # Enter at zone low for long
                stop = zone_low - (zone_high - zone_low)  # Stop below zone
            else:
                entry = zone_high  # Enter at zone high for short
                stop = zone_high + (zone_high - zone_low)  # Stop above zone

            # Calculate risk and shares
            risk_per_share = abs(entry - stop)
            if risk_per_share > 0:
                shares = int(risk_amount / risk_per_share)
                position_value = shares * entry
            else:
                shares = 0
                position_value = 0

            row = [
                setup.get("ticker", ""),
                direction,
                f"${entry:.2f}",
                f"${stop:.2f}",
                f"${risk_amount:.2f}",
                str(shares),
                f"${position_value:.2f}"
            ]
            data.append(row)

            # Color by share count
            if shares >= 100:
                colors.append(COLORS['status_complete'])
            elif shares >= 50:
                colors.append(COLORS['tier_t2'])
            else:
                colors.append(COLORS['status_error'])

        if data:
            self.populate_table(self.risk_table, data, colors)
        else:
            self.populate_table(self.risk_table, [["No setups", "-", "-", "-", "-", "-", "-"]])

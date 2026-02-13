"""
Bar Data Tab
Epoch Trading System v2.0 - XIII Trading LLC

Ticker Structure, OHLC data, ATR, Camarilla pivots, Options levels, HVN POCs.
"""

from typing import Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.tabs.base_tab import BaseTab
from ui.styles import COLORS


class BarDataTab(BaseTab):
    """
    Bar Data Tab

    Displays:
    - Ticker Structure (ALL tickers with Strong/Weak levels)
    - Monthly/Weekly/Daily OHLC candles (per ticker)
    - ATR values (M1, M5, M15, H1, D1) (per ticker)
    - Overnight High/Low
    - Camarilla pivots (Daily, Weekly, Monthly) (per ticker)
    - Options levels (top 10) (per ticker)
    - HVN POC prices (10 per ticker)
    """

    def _setup_ui(self):
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("BAR DATA")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Ticker Structure section (ALL tickers - no selector needed)
        ticker_structure_section = self._create_ticker_structure_section()
        layout.addWidget(ticker_structure_section)

        # Monthly Metrics section (ALL tickers)
        monthly_metrics_section = self._create_monthly_metrics_section()
        layout.addWidget(monthly_metrics_section)

        # Weekly Metrics section (ALL tickers)
        weekly_metrics_section = self._create_weekly_metrics_section()
        layout.addWidget(weekly_metrics_section)

        # Daily Metrics section (ALL tickers)
        daily_metrics_section = self._create_daily_metrics_section()
        layout.addWidget(daily_metrics_section)

        # Time Based HVN section (ALL tickers)
        time_based_hvn_section = self._create_time_based_hvn_section()
        layout.addWidget(time_based_hvn_section)

        # ON + Options Metrics section (ALL tickers)
        on_options_section = self._create_on_options_section()
        layout.addWidget(on_options_section)

        # Additional Metrics section (ALL tickers) - Camarilla pivots
        additional_metrics_section = self._create_additional_metrics_section()
        layout.addWidget(additional_metrics_section)

        # Ticker Details header
        detail_title = QLabel("TICKER DETAILS")
        detail_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(detail_title)

        # Container for dynamically created per-ticker detail sections
        self.ticker_details_layout = QVBoxLayout()
        self.ticker_details_layout.setSpacing(20)
        layout.addLayout(self.ticker_details_layout)

        # Placeholder for when no results exist
        self.details_placeholder = QLabel("Run analysis to see ticker details")
        self.details_placeholder.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 20px;")
        self.details_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.details_placeholder)

        # Track dynamically created detail widgets for cleanup
        self.ticker_detail_widgets = []

        layout.addStretch()

    def _create_ticker_structure_section(self) -> QFrame:
        """Create Ticker Structure section showing ALL tickers with Strong/Weak levels."""
        frame, content_layout = self.create_section_frame("TICKER STRUCTURE")

        # Headers matching V1: Ticker_ID, Ticker, Date, Price, D1_Strong, D1_Weak, H4_Strong, H4_Weak, H1_Strong, H1_Weak, M15_Strong, M15_Weak
        headers = [
            "Ticker_ID", "Ticker", "Date", "Price",
            "D1_Strong", "D1_Weak", "H4_Strong", "H4_Weak",
            "H1_Strong", "H1_Weak", "M15_Strong", "M15_Weak"
        ]
        self.ticker_structure_table = self.create_table(headers)
        self.ticker_structure_table.setMinimumHeight(200)
        content_layout.addWidget(self.ticker_structure_table)

        return frame

    def _create_monthly_metrics_section(self) -> QFrame:
        """Create Monthly Metrics section showing ALL tickers with M1 OHLC data."""
        frame, content_layout = self.create_section_frame("MONTHLY METRICS")

        # Headers: Ticker_ID, Ticker, Date, M1_01 (Open), M1_02 (High), M1_03 (Low), M1_04 (Close),
        #          M1_PO (Prior Open), M1_PH (Prior High), M1_PL (Prior Low), M1_PC (Prior Close)
        headers = [
            "Ticker_ID", "Ticker", "Date",
            "M1_01", "M1_02", "M1_03", "M1_04",
            "M1_PO", "M1_PH", "M1_PL", "M1_PC"
        ]
        self.monthly_metrics_table = self.create_table(headers)
        self.monthly_metrics_table.setMinimumHeight(200)
        content_layout.addWidget(self.monthly_metrics_table)

        return frame

    def _create_weekly_metrics_section(self) -> QFrame:
        """Create Weekly Metrics section showing ALL tickers with W1 OHLC data."""
        frame, content_layout = self.create_section_frame("WEEKLY METRICS")

        # Headers: Ticker_ID, Ticker, Date, W1_01 (Open), W1_02 (High), W1_03 (Low), W1_04 (Close),
        #          W1_PO (Prior Open), W1_PH (Prior High), W1_PL (Prior Low), W1_PC (Prior Close)
        headers = [
            "Ticker_ID", "Ticker", "Date",
            "W1_01", "W1_02", "W1_03", "W1_04",
            "W1_PO", "W1_PH", "W1_PL", "W1_PC"
        ]
        self.weekly_metrics_table = self.create_table(headers)
        self.weekly_metrics_table.setMinimumHeight(200)
        content_layout.addWidget(self.weekly_metrics_table)

        return frame

    def _create_daily_metrics_section(self) -> QFrame:
        """Create Daily Metrics section showing ALL tickers with D1 OHLC data."""
        frame, content_layout = self.create_section_frame("DAILY METRICS")

        # Headers: Ticker_ID, Ticker, Date, D1_01 (Open), D1_02 (High), D1_03 (Low), D1_04 (Close),
        #          D1_PO (Prior Open), D1_PH (Prior High), D1_PL (Prior Low), D1_PC (Prior Close)
        headers = [
            "Ticker_ID", "Ticker", "Date",
            "D1_01", "D1_02", "D1_03", "D1_04",
            "D1_PO", "D1_PH", "D1_PL", "D1_PC"
        ]
        self.daily_metrics_table = self.create_table(headers)
        self.daily_metrics_table.setMinimumHeight(200)
        content_layout.addWidget(self.daily_metrics_table)

        return frame

    def _create_time_based_hvn_section(self) -> QFrame:
        """Create Time Based HVN section showing ALL tickers with HVN POC prices."""
        frame, content_layout = self.create_section_frame("TIME BASED HVN")

        # Headers: Ticker_ID, Ticker, Date, Anchor_Date, HVN POC1 through HVN POC10
        headers = [
            "Ticker_ID", "Ticker", "Date", "Anchor_Date",
            "HVN POC1", "HVN POC2", "HVN POC3", "HVN POC4", "HVN POC5",
            "HVN POC6", "HVN POC7", "HVN POC8", "HVN POC9", "HVN POC10"
        ]
        self.time_based_hvn_table = self.create_table(headers)
        self.time_based_hvn_table.setMinimumHeight(200)
        content_layout.addWidget(self.time_based_hvn_table)

        return frame

    def _create_on_options_section(self) -> QFrame:
        """Create ON + Options Metrics section showing ALL tickers."""
        frame, content_layout = self.create_section_frame("ON + OPTIONS METRICS")

        # Headers: Ticker_ID, Ticker, Date, D1_ONH, D1_ONL, OP_01-OP_10
        headers = [
            "Ticker_ID", "Ticker", "Date",
            "D1_ONH", "D1_ONL",
            "OP_01", "OP_02", "OP_03", "OP_04", "OP_05",
            "OP_06", "OP_07", "OP_08", "OP_09", "OP_10",
        ]
        self.on_options_table = self.create_table(headers)
        self.on_options_table.setMinimumHeight(200)
        content_layout.addWidget(self.on_options_table)

        return frame

    def _create_additional_metrics_section(self) -> QFrame:
        """Create Additional Metrics section showing ALL tickers with Camarilla pivots."""
        frame, content_layout = self.create_section_frame("ADDITIONAL METRICS")

        # Headers: Ticker_ID, Ticker, Date, D1_S6, D1_S4, D1_S3, D1_R3, D1_R4, D1_R6,
        #          W1_S6, W1_S4, W1_S3, W1_R3, W1_R4, W1_R6, M1_S6, M1_S4, M1_S3, M1_R3, M1_R4, M1_R6
        headers = [
            "Ticker_ID", "Ticker", "Date",
            "D1_S6", "D1_S4", "D1_S3", "D1_R3", "D1_R4", "D1_R6",
            "W1_S6", "W1_S4", "W1_S3", "W1_R3", "W1_R4", "W1_R6",
            "M1_S6", "M1_S4", "M1_S3", "M1_R3", "M1_R4", "M1_R6"
        ]
        self.additional_metrics_table = self.create_table(headers)
        self.additional_metrics_table.setMinimumHeight(200)
        content_layout.addWidget(self.additional_metrics_table)

        return frame

    def _create_ticker_detail_section(self, ticker: str) -> tuple:
        """
        Create a full detail section for a single ticker.

        Returns:
            tuple: (frame, tables_dict) where tables_dict has keys:
                   'ohlc', 'atr', 'cam', 'poc'
        """
        # Outer frame for the whole ticker
        frame = QFrame()
        frame.setObjectName("sectionFrame")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(12, 12, 12, 12)
        frame_layout.setSpacing(12)

        # Ticker header
        ticker_label = QLabel(ticker)
        ticker_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        ticker_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        frame_layout.addWidget(ticker_label)

        tables = {}

        # OHLC table
        ohlc_header = QLabel("OHLC DATA")
        ohlc_header.setObjectName("sectionLabel")
        ohlc_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        frame_layout.addWidget(ohlc_header)

        ohlc_table = self.create_table(["Timeframe", "Open", "High", "Low", "Close", "Change %"])
        frame_layout.addWidget(ohlc_table)
        tables['ohlc'] = ohlc_table

        # ATR table
        atr_header = QLabel("ATR VALUES")
        atr_header.setObjectName("sectionLabel")
        atr_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        frame_layout.addWidget(atr_header)

        atr_table = self.create_table(["Timeframe", "ATR", "ATR %"])
        frame_layout.addWidget(atr_table)
        tables['atr'] = atr_table

        # Camarilla table
        cam_header = QLabel("CAMARILLA PIVOTS")
        cam_header.setObjectName("sectionLabel")
        cam_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        frame_layout.addWidget(cam_header)

        cam_table = self.create_table(["Level", "Daily", "Weekly", "Monthly"])
        frame_layout.addWidget(cam_table)
        tables['cam'] = cam_table

        # HVN POC table
        poc_header = QLabel("HVN POC PRICES")
        poc_header.setObjectName("sectionLabel")
        poc_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        frame_layout.addWidget(poc_header)

        poc_table = self.create_table(["Rank", "POC Price", "Volume", "Distance from Price"])
        frame_layout.addWidget(poc_table)
        tables['poc'] = poc_table

        return frame, tables

    def on_results_updated(self, results: Dict[str, Any]):
        """Handle results update."""
        if not results.get("run_complete"):
            return

        # Get all results
        all_results = results.get("index", []) + results.get("custom", [])

        # Update Ticker Structure table (ALL tickers)
        self._update_ticker_structure_table(all_results)

        # Update Monthly Metrics table (ALL tickers)
        self._update_monthly_metrics_table(all_results)

        # Update Weekly Metrics table (ALL tickers)
        self._update_weekly_metrics_table(all_results)

        # Update Daily Metrics table (ALL tickers)
        self._update_daily_metrics_table(all_results)

        # Update Time Based HVN table (ALL tickers)
        self._update_time_based_hvn_table(all_results)

        # Update ON + Options Metrics table (ALL tickers)
        self._update_on_options_table(all_results)

        # Update Additional Metrics table (ALL tickers)
        self._update_additional_metrics_table(all_results)

        # Update per-ticker detail sections
        self._update_ticker_details(all_results)

    def _update_ticker_structure_table(self, all_results: List[Dict]):
        """Update the Ticker Structure table with ALL tickers."""
        table_data = []

        for r in all_results:
            if not r.get("success"):
                continue

            ticker = r.get("ticker", "")
            analysis_date = r.get("analysis_date", "")
            price = r.get("price", 0)

            # Format date as MM-DD-YY
            if analysis_date:
                try:
                    from datetime import datetime
                    if isinstance(analysis_date, str):
                        dt = datetime.fromisoformat(analysis_date)
                        date_str = dt.strftime("%m-%d-%y")
                    else:
                        date_str = str(analysis_date)
                except:
                    date_str = str(analysis_date)
            else:
                date_str = "-"

            # Generate ticker_id as TICKER_MMDDYY
            ticker_id = f"{ticker}_{date_str.replace('-', '')}" if date_str != "-" else ticker

            # Get market structure data
            market_structure = r.get("market_structure", {})

            # Extract Strong/Weak levels from market_structure
            # Market structure has nested timeframe objects: d1, h4, h1, m15
            # Each has: direction, strong, weak
            d1 = market_structure.get("d1", {})
            h4 = market_structure.get("h4", {})
            h1 = market_structure.get("h1", {})
            m15 = market_structure.get("m15", {})

            d1_strong = d1.get("strong") if d1 else None
            d1_weak = d1.get("weak") if d1 else None
            h4_strong = h4.get("strong") if h4 else None
            h4_weak = h4.get("weak") if h4 else None
            h1_strong = h1.get("strong") if h1 else None
            h1_weak = h1.get("weak") if h1 else None
            m15_strong = m15.get("strong") if m15 else None
            m15_weak = m15.get("weak") if m15 else None

            # Format values
            def fmt(val):
                if val is None:
                    return "-"
                return f"{val:.2f}"

            row = [
                ticker_id,
                ticker,
                date_str,
                f"{price:.2f}" if price else "-",
                fmt(d1_strong),
                fmt(d1_weak),
                fmt(h4_strong),
                fmt(h4_weak),
                fmt(h1_strong),
                fmt(h1_weak),
                fmt(m15_strong),
                fmt(m15_weak),
            ]
            table_data.append(row)

        if table_data:
            self.populate_table(self.ticker_structure_table, table_data)
        else:
            self.populate_table(self.ticker_structure_table, [["No data"] + ["-"] * 11])

    def _update_monthly_metrics_table(self, all_results: List[Dict]):
        """Update the Monthly Metrics table with ALL tickers."""
        table_data = []

        for r in all_results:
            if not r.get("success"):
                continue

            ticker = r.get("ticker", "")
            analysis_date = r.get("analysis_date", "")

            # Format date as MM-DD-YY
            if analysis_date:
                try:
                    from datetime import datetime
                    if isinstance(analysis_date, str):
                        dt = datetime.fromisoformat(analysis_date)
                        date_str = dt.strftime("%m-%d-%y")
                    else:
                        date_str = str(analysis_date)
                except:
                    date_str = str(analysis_date)
            else:
                date_str = "-"

            # Generate ticker_id as TICKER_MMDDYY
            ticker_id = f"{ticker}_{date_str.replace('-', '')}" if date_str != "-" else ticker

            # Get bar_data for monthly metrics
            bar_data = r.get("bar_data", {})

            # Current month OHLC (M1_01=Open, M1_02=High, M1_03=Low, M1_04=Close)
            m1_current = bar_data.get("m1_current", {})
            m1_01 = m1_current.get("open") if m1_current else None
            m1_02 = m1_current.get("high") if m1_current else None
            m1_03 = m1_current.get("low") if m1_current else None
            m1_04 = m1_current.get("close") if m1_current else None

            # Prior month OHLC (M1_PO=Prior Open, M1_PH=Prior High, M1_PL=Prior Low, M1_PC=Prior Close)
            m1_prior = bar_data.get("m1_prior", {})
            m1_po = m1_prior.get("open") if m1_prior else None
            m1_ph = m1_prior.get("high") if m1_prior else None
            m1_pl = m1_prior.get("low") if m1_prior else None
            m1_pc = m1_prior.get("close") if m1_prior else None

            # Format values
            def fmt(val):
                if val is None:
                    return "-"
                return f"{val:.2f}"

            row = [
                ticker_id,
                ticker,
                date_str,
                fmt(m1_01),
                fmt(m1_02),
                fmt(m1_03),
                fmt(m1_04),
                fmt(m1_po),
                fmt(m1_ph),
                fmt(m1_pl),
                fmt(m1_pc),
            ]
            table_data.append(row)

        if table_data:
            self.populate_table(self.monthly_metrics_table, table_data)
        else:
            self.populate_table(self.monthly_metrics_table, [["No data"] + ["-"] * 10])

    def _update_weekly_metrics_table(self, all_results: List[Dict]):
        """Update the Weekly Metrics table with ALL tickers."""
        table_data = []

        for r in all_results:
            if not r.get("success"):
                continue

            ticker = r.get("ticker", "")
            analysis_date = r.get("analysis_date", "")

            # Format date as MM-DD-YY
            if analysis_date:
                try:
                    from datetime import datetime
                    if isinstance(analysis_date, str):
                        dt = datetime.fromisoformat(analysis_date)
                        date_str = dt.strftime("%m-%d-%y")
                    else:
                        date_str = str(analysis_date)
                except:
                    date_str = str(analysis_date)
            else:
                date_str = "-"

            # Generate ticker_id as TICKER_MMDDYY
            ticker_id = f"{ticker}_{date_str.replace('-', '')}" if date_str != "-" else ticker

            # Get bar_data for weekly metrics
            bar_data = r.get("bar_data", {})

            # Current week OHLC (W1_01=Open, W1_02=High, W1_03=Low, W1_04=Close)
            w1_current = bar_data.get("w1_current", {})
            w1_01 = w1_current.get("open") if w1_current else None
            w1_02 = w1_current.get("high") if w1_current else None
            w1_03 = w1_current.get("low") if w1_current else None
            w1_04 = w1_current.get("close") if w1_current else None

            # Prior week OHLC (W1_PO=Prior Open, W1_PH=Prior High, W1_PL=Prior Low, W1_PC=Prior Close)
            w1_prior = bar_data.get("w1_prior", {})
            w1_po = w1_prior.get("open") if w1_prior else None
            w1_ph = w1_prior.get("high") if w1_prior else None
            w1_pl = w1_prior.get("low") if w1_prior else None
            w1_pc = w1_prior.get("close") if w1_prior else None

            # Format values
            def fmt(val):
                if val is None:
                    return "-"
                return f"{val:.2f}"

            row = [
                ticker_id,
                ticker,
                date_str,
                fmt(w1_01),
                fmt(w1_02),
                fmt(w1_03),
                fmt(w1_04),
                fmt(w1_po),
                fmt(w1_ph),
                fmt(w1_pl),
                fmt(w1_pc),
            ]
            table_data.append(row)

        if table_data:
            self.populate_table(self.weekly_metrics_table, table_data)
        else:
            self.populate_table(self.weekly_metrics_table, [["No data"] + ["-"] * 10])

    def _update_daily_metrics_table(self, all_results: List[Dict]):
        """Update the Daily Metrics table with ALL tickers."""
        table_data = []

        for r in all_results:
            if not r.get("success"):
                continue

            ticker = r.get("ticker", "")
            analysis_date = r.get("analysis_date", "")

            # Format date as MM-DD-YY
            if analysis_date:
                try:
                    from datetime import datetime
                    if isinstance(analysis_date, str):
                        dt = datetime.fromisoformat(analysis_date)
                        date_str = dt.strftime("%m-%d-%y")
                    else:
                        date_str = str(analysis_date)
                except:
                    date_str = str(analysis_date)
            else:
                date_str = "-"

            # Generate ticker_id as TICKER_MMDDYY
            ticker_id = f"{ticker}_{date_str.replace('-', '')}" if date_str != "-" else ticker

            # Get bar_data for daily metrics
            bar_data = r.get("bar_data", {})

            # Current day OHLC (D1_01=Open, D1_02=High, D1_03=Low, D1_04=Close)
            d1_current = bar_data.get("d1_current", {})
            d1_01 = d1_current.get("open") if d1_current else None
            d1_02 = d1_current.get("high") if d1_current else None
            d1_03 = d1_current.get("low") if d1_current else None
            d1_04 = d1_current.get("close") if d1_current else None

            # Prior day OHLC (D1_PO=Prior Open, D1_PH=Prior High, D1_PL=Prior Low, D1_PC=Prior Close)
            d1_prior = bar_data.get("d1_prior", {})
            d1_po = d1_prior.get("open") if d1_prior else None
            d1_ph = d1_prior.get("high") if d1_prior else None
            d1_pl = d1_prior.get("low") if d1_prior else None
            d1_pc = d1_prior.get("close") if d1_prior else None

            # Format values
            def fmt(val):
                if val is None:
                    return "-"
                return f"{val:.2f}"

            row = [
                ticker_id,
                ticker,
                date_str,
                fmt(d1_01),
                fmt(d1_02),
                fmt(d1_03),
                fmt(d1_04),
                fmt(d1_po),
                fmt(d1_ph),
                fmt(d1_pl),
                fmt(d1_pc),
            ]
            table_data.append(row)

        if table_data:
            self.populate_table(self.daily_metrics_table, table_data)
        else:
            self.populate_table(self.daily_metrics_table, [["No data"] + ["-"] * 10])

    def _update_time_based_hvn_table(self, all_results: List[Dict]):
        """Update the Time Based HVN table with ALL tickers."""
        table_data = []

        for r in all_results:
            if not r.get("success"):
                continue

            ticker = r.get("ticker", "")
            analysis_date = r.get("analysis_date", "")
            anchor_date = r.get("anchor_date", "")

            # Format analysis date as MM-DD-YY
            if analysis_date:
                try:
                    from datetime import datetime
                    if isinstance(analysis_date, str):
                        dt = datetime.fromisoformat(analysis_date)
                        date_str = dt.strftime("%m-%d-%y")
                    else:
                        date_str = str(analysis_date)
                except:
                    date_str = str(analysis_date)
            else:
                date_str = "-"

            # Format anchor date as MM-DD-YY
            if anchor_date:
                try:
                    from datetime import datetime
                    if isinstance(anchor_date, str):
                        dt = datetime.fromisoformat(anchor_date)
                        anchor_str = dt.strftime("%m-%d-%y")
                    else:
                        anchor_str = str(anchor_date)
                except:
                    anchor_str = str(anchor_date)
            else:
                anchor_str = "-"

            # Generate ticker_id as TICKER_MMDDYY
            ticker_id = f"{ticker}_{date_str.replace('-', '')}" if date_str != "-" else ticker

            # Get hvn_result for POC prices
            hvn_result = r.get("hvn_result", {})
            pocs = hvn_result.get("pocs", [])

            # Format POC values (first 10)
            def fmt(val):
                if val is None:
                    return "-"
                return f"{val:.2f}"

            # Extract POC prices (up to 10)
            poc_prices = []
            for i in range(10):
                if i < len(pocs):
                    poc = pocs[i]
                    poc_price = poc.get("price") if isinstance(poc, dict) else None
                    poc_prices.append(fmt(poc_price))
                else:
                    poc_prices.append("-")

            row = [
                ticker_id,
                ticker,
                date_str,
                anchor_str,
            ] + poc_prices
            table_data.append(row)

        if table_data:
            self.populate_table(self.time_based_hvn_table, table_data)
        else:
            self.populate_table(self.time_based_hvn_table, [["No data"] + ["-"] * 13])

    def _update_on_options_table(self, all_results: List[Dict]):
        """Update the ON + Options Metrics table with ALL tickers."""
        table_data = []

        for r in all_results:
            if not r.get("success"):
                continue

            ticker = r.get("ticker", "")
            analysis_date = r.get("analysis_date", "")

            # Format date as MM-DD-YY
            if analysis_date:
                try:
                    from datetime import datetime
                    if isinstance(analysis_date, str):
                        dt = datetime.fromisoformat(analysis_date)
                        date_str = dt.strftime("%m-%d-%y")
                    else:
                        date_str = str(analysis_date)
                except:
                    date_str = str(analysis_date)
            else:
                date_str = "-"

            # Generate ticker_id as TICKER_MMDDYY
            ticker_id = f"{ticker}_{date_str.replace('-', '')}" if date_str != "-" else ticker

            # Get bar_data for overnight values
            bar_data = r.get("bar_data", {})

            # Overnight High/Low (D1_ONH, D1_ONL)
            d1_onh = bar_data.get("overnight_high")
            d1_onl = bar_data.get("overnight_low")

            # Options levels (OP_01 through OP_10)
            options_levels = bar_data.get("options_levels", [])

            # Format values
            def fmt(val):
                if val is None:
                    return "-"
                return f"{val:.2f}"

            # Extract options prices (up to 10)
            op_prices = []
            for i in range(10):
                if i < len(options_levels):
                    op = options_levels[i]
                    # Options level could be a dict with 'strike' or just a price value
                    if isinstance(op, dict):
                        op_price = op.get("strike") or op.get("price")
                    else:
                        op_price = op
                    op_prices.append(fmt(op_price))
                else:
                    op_prices.append("-")

            row = [
                ticker_id,
                ticker,
                date_str,
                fmt(d1_onh),
                fmt(d1_onl),
            ] + op_prices
            table_data.append(row)

        if table_data:
            self.populate_table(self.on_options_table, table_data)
        else:
            self.populate_table(self.on_options_table, [["No data"] + ["-"] * 14])

    def _update_additional_metrics_table(self, all_results: List[Dict]):
        """Update the Additional Metrics table with ALL tickers (Camarilla pivots)."""
        table_data = []

        for r in all_results:
            if not r.get("success"):
                continue

            ticker = r.get("ticker", "")
            analysis_date = r.get("analysis_date", "")

            # Format date as MM-DD-YY
            if analysis_date:
                try:
                    from datetime import datetime
                    if isinstance(analysis_date, str):
                        dt = datetime.fromisoformat(analysis_date)
                        date_str = dt.strftime("%m-%d-%y")
                    else:
                        date_str = str(analysis_date)
                except:
                    date_str = str(analysis_date)
            else:
                date_str = "-"

            # Generate ticker_id as TICKER_MMDDYY
            ticker_id = f"{ticker}_{date_str.replace('-', '')}" if date_str != "-" else ticker

            # Get bar_data for Camarilla pivots
            bar_data = r.get("bar_data", {})

            # Camarilla pivot data
            cam_daily = bar_data.get("camarilla_daily", {})
            cam_weekly = bar_data.get("camarilla_weekly", {})
            cam_monthly = bar_data.get("camarilla_monthly", {})

            # Format values
            def fmt(val):
                if val is None:
                    return "-"
                return f"{val:.2f}"

            # Extract Camarilla levels: S6, S4, S3, R3, R4, R6
            d1_s6 = cam_daily.get("s6") if cam_daily else None
            d1_s4 = cam_daily.get("s4") if cam_daily else None
            d1_s3 = cam_daily.get("s3") if cam_daily else None
            d1_r3 = cam_daily.get("r3") if cam_daily else None
            d1_r4 = cam_daily.get("r4") if cam_daily else None
            d1_r6 = cam_daily.get("r6") if cam_daily else None

            w1_s6 = cam_weekly.get("s6") if cam_weekly else None
            w1_s4 = cam_weekly.get("s4") if cam_weekly else None
            w1_s3 = cam_weekly.get("s3") if cam_weekly else None
            w1_r3 = cam_weekly.get("r3") if cam_weekly else None
            w1_r4 = cam_weekly.get("r4") if cam_weekly else None
            w1_r6 = cam_weekly.get("r6") if cam_weekly else None

            m1_s6 = cam_monthly.get("s6") if cam_monthly else None
            m1_s4 = cam_monthly.get("s4") if cam_monthly else None
            m1_s3 = cam_monthly.get("s3") if cam_monthly else None
            m1_r3 = cam_monthly.get("r3") if cam_monthly else None
            m1_r4 = cam_monthly.get("r4") if cam_monthly else None
            m1_r6 = cam_monthly.get("r6") if cam_monthly else None

            row = [
                ticker_id,
                ticker,
                date_str,
                fmt(d1_s6),
                fmt(d1_s4),
                fmt(d1_s3),
                fmt(d1_r3),
                fmt(d1_r4),
                fmt(d1_r6),
                fmt(w1_s6),
                fmt(w1_s4),
                fmt(w1_s3),
                fmt(w1_r3),
                fmt(w1_r4),
                fmt(w1_r6),
                fmt(m1_s6),
                fmt(m1_s4),
                fmt(m1_s3),
                fmt(m1_r3),
                fmt(m1_r4),
                fmt(m1_r6),
            ]
            table_data.append(row)

        if table_data:
            self.populate_table(self.additional_metrics_table, table_data)
        else:
            self.populate_table(self.additional_metrics_table, [["No data"] + ["-"] * 20])

    def _update_ticker_details(self, all_results: List[Dict]):
        """Build per-ticker detail sections for every successful ticker."""
        # Remove old detail widgets
        for widget in self.ticker_detail_widgets:
            self.ticker_details_layout.removeWidget(widget)
            widget.deleteLater()
        self.ticker_detail_widgets.clear()

        successful = [r for r in all_results if r.get("success")]

        if not successful:
            self.details_placeholder.show()
            return

        self.details_placeholder.hide()

        for ticker_data in successful:
            ticker = ticker_data.get("ticker", "")
            frame, tables = self._create_ticker_detail_section(ticker)
            self._populate_ticker_detail(ticker_data, tables)
            self.ticker_details_layout.addWidget(frame)
            self.ticker_detail_widgets.append(frame)

    def _populate_ticker_detail(self, ticker_data: Dict, tables: Dict):
        """Populate the four detail tables for a single ticker."""
        price = ticker_data.get("price", 0)
        bar_data = ticker_data.get("bar_data", {})

        # --- OHLC ---
        ohlc_data = []
        timeframes = [
            ("Monthly Current", "m1_current"),
            ("Monthly Prior", "m1_prior"),
            ("Weekly Current", "w1_current"),
            ("Weekly Prior", "w1_prior"),
            ("Daily Current", "d1_current"),
            ("Daily Prior", "d1_prior"),
        ]
        for tf_label, tf_key in timeframes:
            tf_data = bar_data.get(tf_key, {})
            if tf_data:
                o = tf_data.get("open", 0) or 0
                h = tf_data.get("high", 0) or 0
                l = tf_data.get("low", 0) or 0
                c = tf_data.get("close", 0) or 0
                change = ((c - o) / o * 100) if o else 0
                ohlc_data.append([tf_label, f"${o:.2f}", f"${h:.2f}", f"${l:.2f}", f"${c:.2f}", f"{change:+.2f}%"])
            else:
                ohlc_data.append([tf_label, "-", "-", "-", "-", "-"])
        self.populate_table(tables['ohlc'], ohlc_data if ohlc_data else [["No data", "-", "-", "-", "-", "-"]])

        # --- ATR ---
        atr_data = []
        for tf in ["M1", "M5", "M15", "H1", "D1"]:
            atr = bar_data.get(f"{tf.lower()}_atr", 0) or 0
            if atr and price:
                atr_pct = (atr / price) * 100
                atr_data.append([tf, f"${atr:.4f}", f"{atr_pct:.2f}%"])
            else:
                atr_data.append([tf, "-", "-"])
        self.populate_table(tables['atr'], atr_data)

        # --- Camarilla ---
        cam_data = []
        cam_daily = bar_data.get("camarilla_daily", {})
        cam_weekly = bar_data.get("camarilla_weekly", {})
        cam_monthly = bar_data.get("camarilla_monthly", {})

        for level in ["s6", "s4", "s3", "r3", "r4", "r6"]:
            daily = cam_daily.get(level)
            weekly = cam_weekly.get(level)
            monthly = cam_monthly.get(level)
            cam_data.append([
                level.upper(),
                f"${daily:.2f}" if daily else "-",
                f"${weekly:.2f}" if weekly else "-",
                f"${monthly:.2f}" if monthly else "-"
            ])
        self.populate_table(tables['cam'], cam_data)

        # --- HVN POCs ---
        hvn_result = ticker_data.get("hvn_result", {})
        pocs = hvn_result.get("pocs", [])
        poc_data = []
        for i, poc in enumerate(pocs[:10], 1):
            poc_price = poc.get("price", 0)
            volume = poc.get("volume", 0)
            distance = abs(poc_price - price) if price else 0
            poc_data.append([
                f"POC {i}",
                f"${poc_price:.2f}",
                f"{volume:,.0f}",
                f"${distance:.2f}"
            ])
        if not poc_data:
            poc_data = [["No POCs", "-", "-", "-"]]
        self.populate_table(tables['poc'], poc_data)

"""
Database Export Tab
Epoch Trading System v2.0 - XIII Trading LLC

Supabase export with terminal output (like DOW Batch Analyzer).
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTextEdit, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.tabs.base_tab import BaseTab
from ui.styles import COLORS
from config import DB_CONFIG


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles date and datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


def safe_float(value, default=None) -> Optional[float]:
    """Safely convert value to float, returning default if None or invalid."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


class ExportWorker(QThread):
    """Worker thread for database export."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, results: Dict[str, Any]):
        super().__init__()
        self.results = results

    def run(self):
        """Run the export."""
        try:
            import psycopg2
            from psycopg2.extras import execute_values

            self.progress.emit("Connecting to Supabase...")

            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            stats = {
                "tickers": 0,
                "zones": 0,
                "setups": 0,
                "bar_data": 0,
                "hvn_pocs": 0,
                "errors": []
            }

            analysis_date = self.results.get("analysis_date")
            all_results = self.results.get("index", []) + self.results.get("custom", [])

            # Ensure daily_sessions record exists (required due to foreign key constraint)
            self.progress.emit("Ensuring daily session record exists...")
            self._ensure_daily_session(cursor, analysis_date, all_results)
            conn.commit()

            self.progress.emit(f"Processing {len(all_results)} tickers...")

            # Assign ticker_id positions (t1, t2, etc.)
            ticker_positions = {}
            for i, r in enumerate(all_results, 1):
                if r.get("success"):
                    ticker = r.get("ticker", "")
                    ticker_positions[ticker] = f"t{i}"

            for r in all_results:
                if not r.get("success"):
                    continue

                ticker = r.get("ticker", "")
                ticker_id = ticker_positions.get(ticker, f"t{len(ticker_positions) + 1}")
                self.progress.emit(f"  Exporting {ticker} ({ticker_id})...")

                try:
                    # Export bar data
                    bar_data = r.get("bar_data", {})
                    if bar_data:
                        self._export_bar_data(cursor, ticker, ticker_id, analysis_date, bar_data)
                        stats["bar_data"] += 1

                    # Export HVN POCs
                    hvn_result = r.get("hvn_result", {})
                    pocs = hvn_result.get("pocs", []) if hvn_result else []
                    if pocs:
                        self._export_hvn_pocs(cursor, ticker, ticker_id, analysis_date, hvn_result)
                        stats["hvn_pocs"] += 1

                    # Export zones
                    zones = r.get("filtered_zones", [])
                    for zone in zones:
                        self._export_zone(cursor, ticker, ticker_id, analysis_date, zone, r.get("bar_data", {}))
                        stats["zones"] += 1

                    # Export setups
                    if r.get("primary_setup"):
                        self._export_setup(cursor, ticker, ticker_id, analysis_date, r["primary_setup"], "PRIMARY", r)
                        stats["setups"] += 1
                    if r.get("secondary_setup"):
                        self._export_setup(cursor, ticker, ticker_id, analysis_date, r["secondary_setup"], "SECONDARY", r)
                        stats["setups"] += 1

                    stats["tickers"] += 1
                    conn.commit()

                except Exception as e:
                    stats["errors"].append(f"{ticker}: {str(e)}")
                    conn.rollback()
                    self.progress.emit(f"    ERROR: {str(e)}")

            cursor.close()
            conn.close()

            self.finished.emit(stats)

        except Exception as e:
            self.error.emit(str(e))

    def _export_bar_data(self, cursor, ticker: str, ticker_id: str, analysis_date, bar_data: Dict):
        """Export bar data to database matching the actual schema."""
        # Extract nested OHLC data
        m1_current = bar_data.get("m1_current", {})
        m1_prior = bar_data.get("m1_prior", {})
        w1_current = bar_data.get("w1_current", {})
        w1_prior = bar_data.get("w1_prior", {})
        d1_current = bar_data.get("d1_current", {})
        d1_prior = bar_data.get("d1_prior", {})

        # Extract Camarilla levels
        cam_daily = bar_data.get("camarilla_daily", {})
        cam_weekly = bar_data.get("camarilla_weekly", {})
        cam_monthly = bar_data.get("camarilla_monthly", {})

        # Extract options levels (list of up to 10 values)
        options = bar_data.get("options_levels", [])
        # Pad to 10 if needed
        while len(options) < 10:
            options.append(None)

        query = """
        INSERT INTO bar_data (
            date, ticker_id, ticker, price,
            m1_open, m1_high, m1_low, m1_close,
            m1_prior_open, m1_prior_high, m1_prior_low, m1_prior_close,
            w1_open, w1_high, w1_low, w1_close,
            w1_prior_open, w1_prior_high, w1_prior_low, w1_prior_close,
            d1_open, d1_high, d1_low, d1_close,
            d1_prior_open, d1_prior_high, d1_prior_low, d1_prior_close,
            d1_overnight_high, d1_overnight_low,
            op_01, op_02, op_03, op_04, op_05, op_06, op_07, op_08, op_09, op_10,
            m5_atr, m15_atr, h1_atr, d1_atr,
            d1_cam_s6, d1_cam_s4, d1_cam_s3, d1_cam_r3, d1_cam_r4, d1_cam_r6,
            w1_cam_s6, w1_cam_s4, w1_cam_s3, w1_cam_r3, w1_cam_r4, w1_cam_r6,
            m1_cam_s6, m1_cam_s4, m1_cam_s3, m1_cam_r3, m1_cam_r4, m1_cam_r6
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (date, ticker_id) DO UPDATE SET
            ticker = EXCLUDED.ticker,
            price = EXCLUDED.price,
            m1_open = EXCLUDED.m1_open, m1_high = EXCLUDED.m1_high,
            m1_low = EXCLUDED.m1_low, m1_close = EXCLUDED.m1_close,
            m1_prior_open = EXCLUDED.m1_prior_open, m1_prior_high = EXCLUDED.m1_prior_high,
            m1_prior_low = EXCLUDED.m1_prior_low, m1_prior_close = EXCLUDED.m1_prior_close,
            w1_open = EXCLUDED.w1_open, w1_high = EXCLUDED.w1_high,
            w1_low = EXCLUDED.w1_low, w1_close = EXCLUDED.w1_close,
            w1_prior_open = EXCLUDED.w1_prior_open, w1_prior_high = EXCLUDED.w1_prior_high,
            w1_prior_low = EXCLUDED.w1_prior_low, w1_prior_close = EXCLUDED.w1_prior_close,
            d1_open = EXCLUDED.d1_open, d1_high = EXCLUDED.d1_high,
            d1_low = EXCLUDED.d1_low, d1_close = EXCLUDED.d1_close,
            d1_prior_open = EXCLUDED.d1_prior_open, d1_prior_high = EXCLUDED.d1_prior_high,
            d1_prior_low = EXCLUDED.d1_prior_low, d1_prior_close = EXCLUDED.d1_prior_close,
            d1_overnight_high = EXCLUDED.d1_overnight_high, d1_overnight_low = EXCLUDED.d1_overnight_low,
            op_01 = EXCLUDED.op_01, op_02 = EXCLUDED.op_02, op_03 = EXCLUDED.op_03,
            op_04 = EXCLUDED.op_04, op_05 = EXCLUDED.op_05, op_06 = EXCLUDED.op_06,
            op_07 = EXCLUDED.op_07, op_08 = EXCLUDED.op_08, op_09 = EXCLUDED.op_09,
            op_10 = EXCLUDED.op_10,
            m5_atr = EXCLUDED.m5_atr, m15_atr = EXCLUDED.m15_atr,
            h1_atr = EXCLUDED.h1_atr, d1_atr = EXCLUDED.d1_atr,
            d1_cam_s6 = EXCLUDED.d1_cam_s6, d1_cam_s4 = EXCLUDED.d1_cam_s4,
            d1_cam_s3 = EXCLUDED.d1_cam_s3, d1_cam_r3 = EXCLUDED.d1_cam_r3,
            d1_cam_r4 = EXCLUDED.d1_cam_r4, d1_cam_r6 = EXCLUDED.d1_cam_r6,
            w1_cam_s6 = EXCLUDED.w1_cam_s6, w1_cam_s4 = EXCLUDED.w1_cam_s4,
            w1_cam_s3 = EXCLUDED.w1_cam_s3, w1_cam_r3 = EXCLUDED.w1_cam_r3,
            w1_cam_r4 = EXCLUDED.w1_cam_r4, w1_cam_r6 = EXCLUDED.w1_cam_r6,
            m1_cam_s6 = EXCLUDED.m1_cam_s6, m1_cam_s4 = EXCLUDED.m1_cam_s4,
            m1_cam_s3 = EXCLUDED.m1_cam_s3, m1_cam_r3 = EXCLUDED.m1_cam_r3,
            m1_cam_r4 = EXCLUDED.m1_cam_r4, m1_cam_r6 = EXCLUDED.m1_cam_r6,
            updated_at = NOW()
        """

        values = (
            analysis_date, ticker_id, ticker, safe_float(bar_data.get("price")),
            # Monthly current OHLC
            safe_float(m1_current.get("open")), safe_float(m1_current.get("high")),
            safe_float(m1_current.get("low")), safe_float(m1_current.get("close")),
            # Monthly prior OHLC
            safe_float(m1_prior.get("open")), safe_float(m1_prior.get("high")),
            safe_float(m1_prior.get("low")), safe_float(m1_prior.get("close")),
            # Weekly current OHLC
            safe_float(w1_current.get("open")), safe_float(w1_current.get("high")),
            safe_float(w1_current.get("low")), safe_float(w1_current.get("close")),
            # Weekly prior OHLC
            safe_float(w1_prior.get("open")), safe_float(w1_prior.get("high")),
            safe_float(w1_prior.get("low")), safe_float(w1_prior.get("close")),
            # Daily current OHLC
            safe_float(d1_current.get("open")), safe_float(d1_current.get("high")),
            safe_float(d1_current.get("low")), safe_float(d1_current.get("close")),
            # Daily prior OHLC
            safe_float(d1_prior.get("open")), safe_float(d1_prior.get("high")),
            safe_float(d1_prior.get("low")), safe_float(d1_prior.get("close")),
            # Overnight
            safe_float(bar_data.get("overnight_high")), safe_float(bar_data.get("overnight_low")),
            # Options levels (10)
            safe_float(options[0] if len(options) > 0 else None),
            safe_float(options[1] if len(options) > 1 else None),
            safe_float(options[2] if len(options) > 2 else None),
            safe_float(options[3] if len(options) > 3 else None),
            safe_float(options[4] if len(options) > 4 else None),
            safe_float(options[5] if len(options) > 5 else None),
            safe_float(options[6] if len(options) > 6 else None),
            safe_float(options[7] if len(options) > 7 else None),
            safe_float(options[8] if len(options) > 8 else None),
            safe_float(options[9] if len(options) > 9 else None),
            # ATR values
            safe_float(bar_data.get("m5_atr")), safe_float(bar_data.get("m15_atr")),
            safe_float(bar_data.get("h1_atr")), safe_float(bar_data.get("d1_atr")),
            # Daily Camarilla
            safe_float(cam_daily.get("s6")), safe_float(cam_daily.get("s4")),
            safe_float(cam_daily.get("s3")), safe_float(cam_daily.get("r3")),
            safe_float(cam_daily.get("r4")), safe_float(cam_daily.get("r6")),
            # Weekly Camarilla
            safe_float(cam_weekly.get("s6")), safe_float(cam_weekly.get("s4")),
            safe_float(cam_weekly.get("s3")), safe_float(cam_weekly.get("r3")),
            safe_float(cam_weekly.get("r4")), safe_float(cam_weekly.get("r6")),
            # Monthly Camarilla
            safe_float(cam_monthly.get("s6")), safe_float(cam_monthly.get("s4")),
            safe_float(cam_monthly.get("s3")), safe_float(cam_monthly.get("r3")),
            safe_float(cam_monthly.get("r4")), safe_float(cam_monthly.get("r6")),
        )

        cursor.execute(query, values)

    def _export_hvn_pocs(self, cursor, ticker: str, ticker_id: str, analysis_date, hvn_result: Dict):
        """Export HVN POCs to database."""
        pocs = hvn_result.get("pocs", [])
        epoch_start_date = hvn_result.get("start_date")

        # Convert start_date string to date if needed
        if isinstance(epoch_start_date, str):
            from datetime import datetime as dt
            epoch_start_date = dt.strptime(epoch_start_date, '%Y-%m-%d').date()

        # Build POC values (poc_1 through poc_10)
        poc_values = [None] * 10
        for poc in pocs[:10]:
            rank = poc.get("rank", 0)
            if 1 <= rank <= 10:
                poc_values[rank - 1] = safe_float(poc.get("price"))

        query = """
        INSERT INTO hvn_pocs (
            date, ticker_id, ticker, epoch_start_date,
            poc_1, poc_2, poc_3, poc_4, poc_5, poc_6, poc_7, poc_8, poc_9, poc_10
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (date, ticker_id) DO UPDATE SET
            ticker = EXCLUDED.ticker,
            epoch_start_date = EXCLUDED.epoch_start_date,
            poc_1 = EXCLUDED.poc_1, poc_2 = EXCLUDED.poc_2, poc_3 = EXCLUDED.poc_3,
            poc_4 = EXCLUDED.poc_4, poc_5 = EXCLUDED.poc_5, poc_6 = EXCLUDED.poc_6,
            poc_7 = EXCLUDED.poc_7, poc_8 = EXCLUDED.poc_8, poc_9 = EXCLUDED.poc_9,
            poc_10 = EXCLUDED.poc_10,
            updated_at = NOW()
        """

        cursor.execute(query, (
            analysis_date, ticker_id, ticker, epoch_start_date,
            poc_values[0], poc_values[1], poc_values[2], poc_values[3], poc_values[4],
            poc_values[5], poc_values[6], poc_values[7], poc_values[8], poc_values[9]
        ))

    def _export_zone(self, cursor, ticker: str, ticker_id: str, analysis_date, zone: Dict, bar_data: Dict):
        """Export a zone to database."""
        query = """
        INSERT INTO zones (
            date, zone_id, ticker_id, ticker, price,
            hvn_poc, zone_high, zone_low,
            direction, rank, score, overlap_count, confluences,
            is_filtered
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s
        )
        ON CONFLICT (date, zone_id) DO UPDATE SET
            ticker_id = EXCLUDED.ticker_id,
            ticker = EXCLUDED.ticker,
            price = EXCLUDED.price,
            hvn_poc = EXCLUDED.hvn_poc,
            zone_high = EXCLUDED.zone_high,
            zone_low = EXCLUDED.zone_low,
            direction = EXCLUDED.direction,
            rank = EXCLUDED.rank,
            score = EXCLUDED.score,
            overlap_count = EXCLUDED.overlap_count,
            confluences = EXCLUDED.confluences,
            is_filtered = EXCLUDED.is_filtered,
            updated_at = NOW()
        """

        # Get confluences as string
        confluences = zone.get("confluences", [])
        if isinstance(confluences, list):
            confluences_str = ", ".join(confluences)
        else:
            confluences_str = str(confluences) if confluences else ""

        cursor.execute(query, (
            analysis_date,
            zone.get("zone_id", ""),
            ticker_id,
            ticker,
            safe_float(zone.get("price", bar_data.get("price"))),
            safe_float(zone.get("hvn_poc")),
            safe_float(zone.get("zone_high")),
            safe_float(zone.get("zone_low")),
            zone.get("direction", ""),
            zone.get("rank", ""),
            safe_float(zone.get("score")),
            zone.get("overlaps", 0),
            confluences_str,
            True  # If it's in filtered_zones, it passed filtering
        ))

    def _export_setup(self, cursor, ticker: str, ticker_id: str, analysis_date, setup: Dict, setup_type: str, result: Dict):
        """Export a setup to database."""
        # Generate PineScript strings
        primary = result.get("primary_setup")
        secondary = result.get("secondary_setup")
        hvn_result = result.get("hvn_result", {})
        pocs = hvn_result.get("pocs", []) if hvn_result else []

        # Generate pinescript_6: pri_high,pri_low,pri_target,sec_high,sec_low,sec_target
        pri_high = safe_float(primary.get("zone_high")) if primary else 0
        pri_low = safe_float(primary.get("zone_low")) if primary else 0
        pri_target = safe_float(primary.get("target")) if primary else 0
        sec_high = safe_float(secondary.get("zone_high")) if secondary else 0
        sec_low = safe_float(secondary.get("zone_low")) if secondary else 0
        sec_target = safe_float(secondary.get("target")) if secondary else 0

        pinescript_6 = f"{pri_high or 0},{pri_low or 0},{pri_target or 0},{sec_high or 0},{sec_low or 0},{sec_target or 0}"

        # Generate pinescript_16: pinescript_6 + 10 POCs
        poc_prices = [safe_float(p.get("price")) or 0 for p in pocs[:10]]
        while len(poc_prices) < 10:
            poc_prices.append(0)
        pinescript_16 = pinescript_6 + "," + ",".join(str(p) for p in poc_prices)

        query = """
        INSERT INTO setups (
            date, ticker_id, setup_type, ticker,
            direction, zone_id, hvn_poc, zone_high, zone_low,
            target_id, target_price, risk_reward,
            pinescript_6, pinescript_16
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s
        )
        ON CONFLICT (date, ticker_id, setup_type) DO UPDATE SET
            ticker = EXCLUDED.ticker,
            direction = EXCLUDED.direction,
            zone_id = EXCLUDED.zone_id,
            hvn_poc = EXCLUDED.hvn_poc,
            zone_high = EXCLUDED.zone_high,
            zone_low = EXCLUDED.zone_low,
            target_id = EXCLUDED.target_id,
            target_price = EXCLUDED.target_price,
            risk_reward = EXCLUDED.risk_reward,
            pinescript_6 = EXCLUDED.pinescript_6,
            pinescript_16 = EXCLUDED.pinescript_16,
            updated_at = NOW()
        """

        cursor.execute(query, (
            analysis_date,
            ticker_id,
            setup_type,
            ticker,
            setup.get("direction", ""),
            setup.get("zone_id", ""),
            safe_float(setup.get("hvn_poc")),
            safe_float(setup.get("zone_high")),
            safe_float(setup.get("zone_low")),
            setup.get("target_id", ""),
            safe_float(setup.get("target")),
            safe_float(setup.get("risk_reward")),
            pinescript_6,
            pinescript_16
        ))

    def _ensure_daily_session(self, cursor, analysis_date, all_results: List[Dict]):
        """
        Ensure a daily_sessions record exists for the analysis date.
        This is required because bar_data, hvn_pocs, zones, and setups
        have foreign key constraints referencing daily_sessions.date.
        """
        # Build tickers list
        tickers = [r.get("ticker", "") for r in all_results if r.get("success")]
        tickers_str = ",".join(tickers) if tickers else ""
        ticker_count = len(tickers)

        query = """
        INSERT INTO daily_sessions (
            date, tickers_analyzed, ticker_count, export_source, export_version
        ) VALUES (
            %s, %s, %s, %s, %s
        )
        ON CONFLICT (date) DO UPDATE SET
            tickers_analyzed = EXCLUDED.tickers_analyzed,
            ticker_count = EXCLUDED.ticker_count,
            export_source = EXCLUDED.export_source,
            export_version = EXCLUDED.export_version,
            updated_at = NOW()
        """

        cursor.execute(query, (
            analysis_date,
            tickers_str,
            ticker_count,
            "epoch_v2_app",
            "2.0"
        ))


class DatabaseExportTab(BaseTab):
    """
    Database Export Tab

    Features:
    - Export to Supabase button
    - Terminal output showing progress
    - Stats summary
    - Clear database option
    """

    def __init__(self, analysis_results):
        self._worker = None
        super().__init__(analysis_results)

    def _setup_ui(self):
        """Set up the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("DATABASE EXPORT")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Control section
        control_section = self._create_control_section()
        layout.addWidget(control_section)

        # Progress section
        progress_section = self._create_progress_section()
        layout.addWidget(progress_section)

        # Terminal section
        terminal_section = self._create_terminal_section()
        layout.addWidget(terminal_section)

        # Stats section
        stats_section = self._create_stats_section()
        layout.addWidget(stats_section)

        layout.addStretch()

    def _create_control_section(self) -> QFrame:
        """Create the control buttons section."""
        frame = QFrame()
        frame.setObjectName("sectionFrame")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Export button
        self.export_button = QPushButton("EXPORT TO SUPABASE")
        self.export_button.setObjectName("exportButton")
        self.export_button.clicked.connect(self._on_export_clicked)
        layout.addWidget(self.export_button)

        # Clear database button
        self.clear_button = QPushButton("CLEAR DATABASE")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.clicked.connect(self._on_clear_clicked)
        layout.addWidget(self.clear_button)

        layout.addStretch()

        # Status indicator
        self.status_indicator = QLabel("Ready")
        self.status_indicator.setStyleSheet(f"color: {COLORS['status_ready']}; font-weight: bold;")
        layout.addWidget(self.status_indicator)

        return frame

    def _create_progress_section(self) -> QFrame:
        """Create progress bar section."""
        frame = QFrame()
        frame.setObjectName("sectionFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("Waiting...")
        self.progress_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.progress_label)

        return frame

    def _create_terminal_section(self) -> QFrame:
        """Create terminal output section."""
        frame = QFrame()
        frame.setObjectName("terminalFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(12, 8, 12, 8)

        header_label = QLabel("EXPORT LOG")
        header_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold;")
        header.addWidget(header_label)

        header.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedSize(60, 24)
        clear_btn.clicked.connect(self._clear_terminal)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        # Terminal
        self.terminal = QTextEdit()
        self.terminal.setObjectName("terminalOutput")
        self.terminal.setReadOnly(True)
        self.terminal.setMinimumHeight(300)
        layout.addWidget(self.terminal)

        # Welcome message
        self._log("EPOCH Database Export")
        self._log("=" * 50)
        self._log("Run analysis first, then click EXPORT TO SUPABASE.")
        self._log("")

        return frame

    def _create_stats_section(self) -> QFrame:
        """Create export stats section."""
        frame, content_layout = self.create_section_frame("EXPORT STATISTICS")

        # Stats grid
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(30)

        self.stat_labels = {}
        stats = [
            ("tickers", "Tickers"),
            ("zones", "Zones"),
            ("setups", "Setups"),
            ("bar_data", "Bar Data"),
            ("hvn_pocs", "HVN POCs"),
        ]

        for key, label in stats:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(0, 0, 0, 0)
            stat_layout.setSpacing(4)

            label_widget = QLabel(label)
            label_widget.setStyleSheet(f"color: {COLORS['text_secondary']};")
            stat_layout.addWidget(label_widget)

            value_widget = QLabel("0")
            value_widget.setStyleSheet("font-size: 16pt; font-weight: bold;")
            stat_layout.addWidget(value_widget)

            self.stat_labels[key] = value_widget
            stats_layout.addWidget(stat_widget)

        stats_layout.addStretch()
        content_layout.addLayout(stats_layout)

        return frame

    def _on_export_clicked(self):
        """Handle export button click."""
        results = self.get_results()

        if not results.get("run_complete"):
            QMessageBox.warning(
                self, "No Data",
                "Please run analysis first before exporting."
            )
            return

        # Confirm export
        reply = QMessageBox.question(
            self, "Confirm Export",
            "Export analysis results to Supabase?\n\nThis will overwrite existing data for this date.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Start export
        self._log("")
        self._log("=" * 50)
        self._log("STARTING EXPORT")
        self._log("=" * 50)

        self.export_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.status_indicator.setText("Exporting...")
        self.status_indicator.setStyleSheet(f"color: {COLORS['status_running']}; font-weight: bold;")
        self.progress_bar.setMaximum(0)  # Indeterminate

        self._worker = ExportWorker(results)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_clear_clicked(self):
        """Handle clear database button click."""
        reply = QMessageBox.question(
            self, "Clear Database",
            "This will delete ALL analysis data from the database.\n\nAre you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            import psycopg2

            self._log("\n[DB] Connecting to database...")

            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Clear tables (adjust based on actual schema)
            tables = ["setups", "zones", "hvn_pocs", "bar_data"]
            total_deleted = 0

            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    cursor.execute(f"DELETE FROM {table}")
                    total_deleted += count
                    self._log(f"[DB] Cleared {count} rows from {table}")
                except Exception as e:
                    self._log(f"[DB] Error clearing {table}: {e}")

            conn.commit()
            cursor.close()
            conn.close()

            self._log(f"\n[DB] Total: {total_deleted} rows deleted", COLORS['status_complete'])

        except Exception as e:
            self._log(f"[DB] Error: {str(e)}", COLORS['status_error'])

    def _on_progress(self, message: str):
        """Handle progress update."""
        self._log(message)
        self.progress_label.setText(message)

    def _on_finished(self, stats: Dict):
        """Handle export completion."""
        self._worker = None

        # Update stats
        for key, value in stats.items():
            if key in self.stat_labels:
                self.stat_labels[key].setText(str(value))

        # Log summary
        self._log("")
        self._log("=" * 50)
        self._log("EXPORT COMPLETE", COLORS['status_complete'])
        self._log(f"  Tickers: {stats.get('tickers', 0)}")
        self._log(f"  Zones: {stats.get('zones', 0)}")
        self._log(f"  Setups: {stats.get('setups', 0)}")
        self._log(f"  Bar Data: {stats.get('bar_data', 0)}")
        self._log(f"  HVN POCs: {stats.get('hvn_pocs', 0)}")

        if stats.get("errors"):
            self._log(f"\n  Errors: {len(stats['errors'])}", COLORS['status_error'])
            for err in stats["errors"]:
                self._log(f"    - {err}", COLORS['status_error'])

        self._log("=" * 50)

        # Reset UI
        self.export_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.status_indicator.setText("Complete")
        self.status_indicator.setStyleSheet(f"color: {COLORS['status_complete']}; font-weight: bold;")
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(100)

    def _on_error(self, error_msg: str):
        """Handle export error."""
        self._worker = None
        self._log(f"\n[ERROR] {error_msg}", COLORS['status_error'])

        self.export_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.status_indicator.setText("Error")
        self.status_indicator.setStyleSheet(f"color: {COLORS['status_error']}; font-weight: bold;")
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        QMessageBox.critical(self, "Export Error", f"Export failed:\n\n{error_msg}")

    def _log(self, message: str, color: str = None):
        """Log message to terminal."""
        if color:
            self.terminal.append(f'<span style="color: {color};">{message}</span>')
        else:
            self.terminal.append(message)

        # Scroll to bottom
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.terminal.setTextCursor(cursor)

    def _clear_terminal(self):
        """Clear the terminal."""
        self.terminal.clear()
        self._log("Terminal cleared.")

    def on_results_updated(self, results: Dict[str, Any]):
        """Handle results update."""
        if results.get("run_complete"):
            self._log("\n[*] Analysis results ready for export.")

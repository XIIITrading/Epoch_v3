"""
Journal Processor GUI - Orchestrates 8 secondary processors.
Epoch Trading System v2.0 - XIII Trading LLC

Pattern: Follow FIFO GUI style with terminal output and progress bar.
"""

import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox, QCheckBox,
    QTextEdit, QProgressBar, QGridLayout,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QTextCursor

from styles import DARK_STYLESHEET

# ---------------------------------------------------------------------------
# Ensure processor directory is on sys.path so imports like
#   from j_m1_bars.storage import JM1BarsStorage
# work from any working directory.
# ---------------------------------------------------------------------------
_PROC_DIR = Path(__file__).resolve().parent.parent / "processor"
if str(_PROC_DIR) not in sys.path:
    sys.path.insert(0, str(_PROC_DIR))


# =============================================================================
# Processor definitions
# =============================================================================

PROCESSORS = [
    {
        "id": 1,
        "label": "Proc 1: j_m1_bars (Polygon M1 bars)",
        "table": "j_m1_bars",
    },
    {
        "id": 2,
        "label": "Proc 2: j_m1_indicator_bars (22 indicators)",
        "table": "j_m1_indicator_bars",
    },
    {
        "id": 3,
        "label": "Proc 3: j_m1_atr_stop (M1 ATR stops)",
        "table": "j_m1_atr_stop",
    },
    {
        "id": 4,
        "label": "Proc 4: j_m5_atr_stop (M5 ATR stops)",
        "table": "j_m5_atr_stop",
    },
    {
        "id": 5,
        "label": "Proc 5: j_trades_m5_r_win (consolidation)",
        "table": "j_trades_m5_r_win",
    },
    {
        "id": 6,
        "label": "Proc 6: j_m1_trade_indicator (entry snapshot)",
        "table": "j_m1_trade_indicator",
    },
    {
        "id": 7,
        "label": "Proc 7: j_m1_ramp_up_indicator (25 bars before)",
        "table": "j_m1_ramp_up_indicator",
    },
    {
        "id": 8,
        "label": "Proc 8: j_m1_post_trade_indicator (25 bars after)",
        "table": "j_m1_post_trade_indicator",
    },
]


# =============================================================================
# ProcessorThread -- runs checked processors in dependency order
# =============================================================================

class ProcessorThread(QThread):
    """Runs the selected processors sequentially in a background thread."""

    log_message = pyqtSignal(str)
    progress_update = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(dict)             # results summary

    def __init__(self, checked_ids: List[int], parent=None):
        super().__init__(parent)
        self.checked_ids = sorted(checked_ids)  # dependency order
        self._stop_flag = False

    def request_stop(self):
        """Set stop flag -- checked between processors."""
        self._stop_flag = True

    def run(self):
        results: Dict[int, str] = {}
        total = len(self.checked_ids)

        for idx, proc_id in enumerate(self.checked_ids):
            if self._stop_flag:
                self.log_message.emit("\n[STOP] Pipeline stopped by user.")
                break

            self.progress_update.emit(idx, total)
            self.log_message.emit(
                f"\n{'='*60}\n"
                f"  PROCESSOR {proc_id} / {total}  "
                f"({PROCESSORS[proc_id - 1]['label']})\n"
                f"{'='*60}"
            )

            try:
                self._run_processor(proc_id)
                results[proc_id] = "OK"
            except Exception as exc:
                tb = traceback.format_exc()
                self.log_message.emit(f"\n[ERROR] Processor {proc_id} failed:\n{tb}")
                results[proc_id] = f"ERROR: {exc}"

        self.progress_update.emit(total, total)
        self.finished.emit(results)

    # --------------------------------------------------------------------- #
    def _run_processor(self, proc_id: int):
        """Import and execute a single processor."""
        cb = self.log_message.emit

        if proc_id == 1:
            from j_m1_bars.storage import JM1BarsStorage
            storage = JM1BarsStorage()
            storage.run_batch_storage(callback=cb)

        elif proc_id == 2:
            from j_m1_indicator_bars.calculator import JM1IndicatorBarsPopulator
            populator = JM1IndicatorBarsPopulator()
            populator.run_batch_population(callback=cb)

        elif proc_id == 3:
            from j_m1_atr_stop.calculator import JM1AtrStopCalculator
            calc = JM1AtrStopCalculator()
            calc.run_batch_calculation(callback=cb)

        elif proc_id == 4:
            from j_m5_atr_stop.calculator import JM5AtrStopCalculator
            calc = JM5AtrStopCalculator()
            calc.run_batch_calculation(callback=cb)

        elif proc_id == 5:
            from j_trades_m5_r_win.calculator import JTradesM5RWinCalculator
            calc = JTradesM5RWinCalculator()
            calc.run_batch_calculation(callback=cb)

        elif proc_id == 6:
            from j_m1_trade_indicator.populator import JM1TradeIndicatorPopulator
            pop = JM1TradeIndicatorPopulator()
            pop.run_batch_population(callback=cb)

        elif proc_id == 7:
            from j_m1_ramp_up_indicator.populator import JM1RampUpIndicatorPopulator
            pop = JM1RampUpIndicatorPopulator()
            pop.run_batch_population(callback=cb)

        elif proc_id == 8:
            from j_m1_post_trade_indicator.populator import JM1PostTradeIndicatorPopulator
            pop = JM1PostTradeIndicatorPopulator()
            pop.run_batch_population(callback=cb)

        else:
            cb(f"[WARN] Unknown processor id: {proc_id}")


# =============================================================================
# StatusThread -- queries row counts for the 8 j_ tables
# =============================================================================

class StatusThread(QThread):
    """Queries row counts for each journal table in a background thread."""

    log_message = pyqtSignal(str)
    finished = pyqtSignal()

    def run(self):
        import psycopg2
        from db_config import DB_CONFIG

        tables = [
            ("journal_trades", "journal_trades"),
        ] + [
            (p["table"], p["label"]) for p in PROCESSORS
        ]

        try:
            self.log_message.emit("\n[STATUS] Connecting to database...")
            conn = psycopg2.connect(**DB_CONFIG)
            self.log_message.emit("[STATUS] Connected.\n")

            self.log_message.emit(f"  {'Table':<35} {'Rows':>10}")
            self.log_message.emit(f"  {'-'*35} {'-'*10}")

            for table_name, label in tables:
                try:
                    with conn.cursor() as cur:
                        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cur.fetchone()[0]
                    self.log_message.emit(f"  {table_name:<35} {count:>10,}")
                except Exception as e:
                    self.log_message.emit(f"  {table_name:<35} {'ERROR':>10}  ({e})")
                    conn.rollback()

            conn.close()
            self.log_message.emit("\n[STATUS] Done.")

        except Exception as e:
            self.log_message.emit(f"\n[STATUS] Connection error: {e}")

        self.finished.emit()


# =============================================================================
# ProcessorWindow -- main GUI
# =============================================================================

class ProcessorWindow(QMainWindow):
    """
    Journal Processor Pipeline GUI.

    Features:
    - 8 processor checkboxes (2 columns of 4)
    - RUN PIPELINE / STATUS / STOP buttons
    - Terminal output with timestamped logging
    - Progress bar
    """

    def __init__(self):
        super().__init__()

        self._processor_thread = None
        self._status_thread = None
        self._checkboxes: Dict[int, QCheckBox] = {}

        self._setup_ui()

    # =========================================================================
    # UI setup
    # =========================================================================

    def _setup_ui(self):
        self.setWindowTitle("Epoch Journal Processor")
        self.setMinimumSize(900, 700)
        self.resize(900, 700)
        self.setStyleSheet(DARK_STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 15)
        layout.setSpacing(12)

        # Title
        title = QLabel("Journal Processor Pipeline")
        title.setObjectName("titleLabel")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Processors group
        layout.addWidget(self._create_processor_group())

        # Button row
        layout.addLayout(self._create_button_row())

        # Terminal
        layout.addWidget(self._create_terminal(), stretch=1)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Welcome text
        self._print_welcome()

    def _create_processor_group(self) -> QGroupBox:
        """Create the Processors group box with 8 checkboxes in 2 columns."""
        group = QGroupBox("Processors")
        grid = QGridLayout(group)
        grid.setSpacing(8)

        for i, proc in enumerate(PROCESSORS):
            cb = QCheckBox(proc["label"])
            cb.setChecked(True)
            self._checkboxes[proc["id"]] = cb

            row = i % 4
            col = i // 4
            grid.addWidget(cb, row, col)

        return group

    def _create_button_row(self) -> QHBoxLayout:
        """Create the RUN / STATUS / STOP button row."""
        layout = QHBoxLayout()
        layout.setSpacing(12)

        self.run_btn = QPushButton("RUN PIPELINE")
        self.run_btn.setFixedHeight(38)
        self.run_btn.setMinimumWidth(140)
        self.run_btn.clicked.connect(self._on_run_clicked)

        self.status_btn = QPushButton("STATUS")
        self.status_btn.setObjectName("statusBtn")
        self.status_btn.setFixedHeight(38)
        self.status_btn.setMinimumWidth(100)
        self.status_btn.clicked.connect(self._on_status_clicked)

        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setFixedHeight(38)
        self.stop_btn.setMinimumWidth(100)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop_clicked)

        layout.addWidget(self.run_btn)
        layout.addWidget(self.status_btn)
        layout.addWidget(self.stop_btn)
        layout.addStretch()

        return layout

    def _create_terminal(self) -> QTextEdit:
        """Create the read-only terminal output widget."""
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFont(QFont("Consolas", 10))
        return self.terminal

    # =========================================================================
    # Helpers
    # =========================================================================

    def _print_welcome(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.terminal.setPlainText(
            f"{'='*60}\n"
            f"  EPOCH JOURNAL PROCESSOR PIPELINE\n"
            f"  8 Secondary Processors (dependency order)\n"
            f"  Epoch Trading System - XIII Trading LLC\n"
            f"{'='*60}\n"
            f"  Session started: {now}\n"
            f"{'='*60}\n\n"
            f"  Check the processors you want to run and click RUN PIPELINE.\n"
            f"  Use STATUS to query row counts for all journal tables.\n\n"
            f"  Pipeline order:\n"
            f"    1. j_m1_bars          - Fetch M1 bars from Polygon\n"
            f"    2. j_m1_indicator_bars - Calculate 22 indicators\n"
            f"    3. j_m1_atr_stop      - M1 ATR stop simulation\n"
            f"    4. j_m5_atr_stop      - M5 ATR stop simulation\n"
            f"    5. j_trades_m5_r_win  - Consolidation / denormalization\n"
            f"    6. j_m1_trade_indicator   - Entry bar snapshot\n"
            f"    7. j_m1_ramp_up_indicator - 25 bars before entry\n"
            f"    8. j_m1_post_trade_indicator - 25 bars after entry\n\n"
        )

    def _append_log(self, text: str):
        """Append a timestamped line to the terminal."""
        ts = datetime.now().strftime("%H:%M:%S")
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(f"[{ts}] {text}\n")
        self.terminal.setTextCursor(cursor)
        self.terminal.ensureCursorVisible()

    def _get_checked_ids(self) -> List[int]:
        """Return sorted list of checked processor IDs."""
        return sorted(
            pid for pid, cb in self._checkboxes.items() if cb.isChecked()
        )

    def _set_running_state(self, running: bool):
        """Toggle UI enabled state during pipeline execution."""
        self.run_btn.setEnabled(not running)
        self.status_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        for cb in self._checkboxes.values():
            cb.setEnabled(not running)

    # =========================================================================
    # Button handlers
    # =========================================================================

    @pyqtSlot()
    def _on_run_clicked(self):
        checked = self._get_checked_ids()
        if not checked:
            self._append_log("[WARN] No processors selected.")
            return

        self._set_running_state(True)
        self.progress_bar.setValue(0)

        labels = ", ".join(str(i) for i in checked)
        self._append_log(f"Starting pipeline with processors: {labels}")

        self._processor_thread = ProcessorThread(checked)
        self._processor_thread.log_message.connect(self._on_thread_log)
        self._processor_thread.progress_update.connect(self._on_progress)
        self._processor_thread.finished.connect(self._on_pipeline_finished)
        self._processor_thread.start()

    @pyqtSlot()
    def _on_status_clicked(self):
        if self._status_thread and self._status_thread.isRunning():
            return

        self.status_btn.setEnabled(False)
        self._status_thread = StatusThread()
        self._status_thread.log_message.connect(self._on_thread_log)
        self._status_thread.finished.connect(self._on_status_finished)
        self._status_thread.start()

    @pyqtSlot()
    def _on_stop_clicked(self):
        if self._processor_thread and self._processor_thread.isRunning():
            self._append_log("[STOP] Stop requested -- will halt after current processor.")
            self._processor_thread.request_stop()

    # =========================================================================
    # Thread signal handlers
    # =========================================================================

    @pyqtSlot(str)
    def _on_thread_log(self, message: str):
        """Append thread log messages with timestamp."""
        ts = datetime.now().strftime("%H:%M:%S")
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(f"[{ts}] {message}\n")
        self.terminal.setTextCursor(cursor)
        self.terminal.ensureCursorVisible()

    @pyqtSlot(int, int)
    def _on_progress(self, current: int, total: int):
        if total > 0:
            pct = int((current / total) * 100)
            self.progress_bar.setValue(pct)

    @pyqtSlot(dict)
    def _on_pipeline_finished(self, results: dict):
        self._set_running_state(False)
        self.progress_bar.setValue(100)

        self._append_log(f"\n{'='*60}")
        self._append_log("  PIPELINE COMPLETE")
        self._append_log(f"{'='*60}")

        ok_count = sum(1 for v in results.values() if v == "OK")
        err_count = sum(1 for v in results.values() if v != "OK")

        for proc_id, status in sorted(results.items()):
            label = PROCESSORS[proc_id - 1]["label"]
            self._append_log(f"  {label}: {status}")

        self._append_log(f"\n  Summary: {ok_count} succeeded, {err_count} failed")
        self._append_log(f"{'='*60}\n")

    @pyqtSlot()
    def _on_status_finished(self):
        self.status_btn.setEnabled(True)

    # =========================================================================
    # Window close
    # =========================================================================

    def closeEvent(self, event):
        """Stop running threads on window close."""
        if self._processor_thread and self._processor_thread.isRunning():
            self._processor_thread.request_stop()
            self._processor_thread.wait(5000)
        if self._status_thread and self._status_thread.isRunning():
            self._status_thread.wait(3000)
        event.accept()

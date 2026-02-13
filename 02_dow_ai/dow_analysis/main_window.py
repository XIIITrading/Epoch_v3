"""
DOW AI Analysis Window
Epoch Trading System v3.0 - XIII Trading LLC

Main window with batch size selector and terminal-style output.

MODES:
- Production (Default): Pass 2 only -> ai_predictions table (weekly runs)
- Validation: Dual-pass -> dual_pass_analysis table (monthly validation)
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QFrame, QTextEdit,
    QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QProcess, pyqtSlot
from PyQt6.QtGui import QFont, QTextCursor
import psycopg2

from styles import DARK_STYLESHEET, COLORS

# Database config
DB_CONFIG = {
    "host": "db.pdbmcskznoaiybdiobje.supabase.co",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "guid-saltation-covet",
    "sslmode": "require"
}


class DOWAnalysisWindow(QMainWindow):
    """
    Main window for DOW AI Analysis tool v3.0.

    Features:
    - Production Mode (Default): Pass 2 only -> ai_predictions (weekly)
    - Validation Mode: Dual-pass -> dual_pass_analysis (monthly)
    - Batch size selector (20, 50, 100, 250, 500, ALL)
    - Run/Stop controls
    - Terminal output (80% of screen)
    - Progress tracking
    """

    BATCH_SIZES = ["20", "50", "100", "250", "500", "ALL"]

    def __init__(self):
        super().__init__()

        # Process for running batch analysis
        self._process: Optional[QProcess] = None
        self._is_running = False
        self._trades_processed = 0
        self._trades_total = 0

        self._setup_ui()

    def _setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("DOW AI DUAL-PASS ANALYZER v3.0")
        self.setMinimumSize(1200, 900)
        self.resize(1400, 1000)

        # Apply dark theme
        self.setStyleSheet(DARK_STYLESHEET)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 15)
        main_layout.setSpacing(15)

        # Header
        header = self._create_header()
        main_layout.addLayout(header)

        # Control panel (takes ~20% of space)
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)

        # Terminal output (takes ~80% of space)
        terminal_frame = self._create_terminal()
        main_layout.addWidget(terminal_frame, stretch=8)

        # Status bar
        status_bar = self._create_status_bar()
        main_layout.addWidget(status_bar)

    def _create_header(self) -> QHBoxLayout:
        """Create the header layout."""
        layout = QHBoxLayout()

        # Title
        title = QLabel("DOW AI BATCH ANALYZER")
        title.setObjectName("headerLabel")
        font = QFont("Segoe UI", 18)
        font.setBold(True)
        title.setFont(font)

        # Version
        version = QLabel("v3.0 DUAL-PASS")
        version.setStyleSheet(f"color: {COLORS['text_muted']};")
        font = QFont("Consolas", 12)
        version.setFont(font)

        layout.addWidget(title)
        layout.addWidget(version)
        layout.addStretch()

        return layout

    def _create_control_panel(self) -> QFrame:
        """Create the control panel with batch size selector and run button."""
        frame = QFrame()
        frame.setObjectName("controlPanel")
        frame.setFixedHeight(130)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 25)
        layout.setSpacing(30)

        # Batch Size Selection
        batch_layout = QVBoxLayout()
        batch_label = QLabel("BATCH SIZE")
        batch_label.setObjectName("sectionLabel")

        self.batch_combo = QComboBox()
        for size in self.BATCH_SIZES:
            self.batch_combo.addItem(f"{size} trades", size)
        self.batch_combo.setCurrentIndex(0)  # Default to 50
        self.batch_combo.setMinimumWidth(150)

        batch_layout.addWidget(batch_label)
        batch_layout.addWidget(self.batch_combo)
        layout.addLayout(batch_layout)

        # Mode Selection
        mode_layout = QVBoxLayout()
        mode_label = QLabel("MODE")
        mode_label.setObjectName("sectionLabel")

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Production (Pass 2 -> ai_predictions)", "production")
        self.mode_combo.addItem("Validation (Dual-Pass -> dual_pass_analysis)", "validation")
        self.mode_combo.addItem("Dry Run (Preview)", "dry")
        self.mode_combo.setMinimumWidth(280)

        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)

        layout.addStretch()

        # Progress
        progress_layout = QVBoxLayout()
        progress_label = QLabel("PROGRESS")
        progress_label.setObjectName("sectionLabel")

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setFixedHeight(25)

        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)

        layout.addSpacing(20)

        # Control Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.clear_db_button = QPushButton("CLEAR DB")
        self.clear_db_button.setObjectName("clearDbButton")
        self.clear_db_button.clicked.connect(self._on_clear_db_clicked)

        self.run_button = QPushButton("RUN ANALYSIS")
        self.run_button.setObjectName("runButton")
        self.run_button.clicked.connect(self._on_run_clicked)

        self.stop_button = QPushButton("STOP")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.stop_button.setEnabled(False)

        button_layout.addWidget(self.clear_db_button)
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)

        return frame

    def _create_terminal(self) -> QFrame:
        """Create the terminal output panel."""
        frame = QFrame()
        frame.setObjectName("terminalFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Terminal header
        header = QHBoxLayout()
        header.setContentsMargins(15, 10, 15, 5)

        terminal_title = QLabel("TERMINAL OUTPUT")
        terminal_title.setObjectName("sectionLabel")
        terminal_title.setFont(QFont("Consolas", 11))

        self.terminal_status = QLabel("Ready")
        self.terminal_status.setStyleSheet(f"color: {COLORS['status_ready']};")
        self.terminal_status.setFont(QFont("Consolas", 10))

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedSize(60, 25)
        clear_btn.clicked.connect(self._clear_terminal)

        header.addWidget(terminal_title)
        header.addStretch()
        header.addWidget(self.terminal_status)
        header.addSpacing(15)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        # Terminal text area
        self.terminal = QTextEdit()
        self.terminal.setObjectName("terminalOutput")
        self.terminal.setReadOnly(True)
        self.terminal.setFont(QFont("Consolas", 10))

        # Welcome message
        self._print_welcome()

        layout.addWidget(self.terminal)

        return frame

    def _create_status_bar(self) -> QFrame:
        """Create the status bar."""
        frame = QFrame()
        frame.setObjectName("statusBar")
        frame.setFixedHeight(35)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 5, 15, 5)

        self.status_label = QLabel("Status: Ready")
        self.status_label.setObjectName("statusLabel")

        self.time_label = QLabel("")
        self.time_label.setObjectName("statusLabel")

        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.time_label)

        return frame

    def _print_welcome(self):
        """Print welcome message to terminal."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.terminal.setPlainText(
            f"{'='*70}\n"
            f"  DOW AI BATCH ANALYZER v3.0\n"
            f"  Epoch Trading System - XIII Trading LLC\n"
            f"{'='*70}\n"
            f"  Session started: {now}\n"
            f"{'='*70}\n\n"
            f"  Select batch size and mode, then click RUN ANALYSIS.\n\n"
            f"  AVAILABLE MODES:\n\n"
            f"    PRODUCTION (Default - Weekly Runs):\n"
            f"      - Pass 2 only (with backtested context)\n"
            f"      - Stores to ai_predictions table\n"
            f"      - Feeds Training Module\n"
            f"      - Cost: ~$0.008/trade\n\n"
            f"    VALIDATION (Monthly Runs):\n"
            f"      - Dual-pass (Pass 1 + Pass 2)\n"
            f"      - Stores to dual_pass_analysis table\n"
            f"      - Validates that Pass 2 context improves accuracy\n"
            f"      - Cost: ~$0.016/trade\n\n"
            f"    DRY RUN:\n"
            f"      - Preview what would be processed\n"
            f"      - No API calls, no database writes\n\n"
        )

    def _append_terminal(self, text: str, color: str = None):
        """Append text to terminal with optional color."""
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        if color:
            html = f'<span style="color: {color};">{text}</span>'
            cursor.insertHtml(html + "<br>")
        else:
            cursor.insertText(text + "\n")

        self.terminal.setTextCursor(cursor)
        self.terminal.ensureCursorVisible()

    def _clear_terminal(self):
        """Clear terminal and show welcome message."""
        self._print_welcome()

    @pyqtSlot()
    def _on_clear_db_clicked(self):
        """Handle Clear Database button click."""
        reply = QMessageBox.question(
            self,
            "Clear Analysis Results",
            "This will delete ALL records from dual_pass_analysis table.\n\nAre you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._append_terminal("\n[DB] Connecting to database...")
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Get count before delete
            cursor.execute("SELECT COUNT(*) FROM dual_pass_analysis")
            count = cursor.fetchone()[0]

            # Delete all records
            cursor.execute("DELETE FROM dual_pass_analysis")
            conn.commit()

            cursor.close()
            conn.close()

            self._append_terminal(f"[DB] Cleared {count} records from dual_pass_analysis", COLORS['status_complete'])
            self._update_status(f"Database cleared ({count} records)")

        except Exception as e:
            self._append_terminal(f"[DB] Error: {str(e)}", COLORS['status_error'])
            self._update_status("Database error")

    def _update_status(self, message: str):
        """Update status bar."""
        self.status_label.setText(f"Status: {message}")
        self.time_label.setText(datetime.now().strftime("%H:%M:%S"))

    @pyqtSlot()
    def _on_run_clicked(self):
        """Handle Run button click."""
        if self._is_running:
            return

        # Get selected options
        batch_size = self.batch_combo.currentData()
        mode = self.mode_combo.currentData()

        # Build command based on mode
        batch_analyzer_dir = Path(__file__).parent.parent / "batch_analyzer"

        if mode == "production":
            # Production mode: Pass 2 only -> ai_predictions
            script_path = batch_analyzer_dir / "scripts" / "batch_analyze_production.py"
        else:
            # Validation/Dry run: Dual-pass -> dual_pass_analysis
            script_path = batch_analyzer_dir / "scripts" / "batch_analyze_v3.py"

        if not script_path.exists():
            QMessageBox.critical(
                self,
                "Error",
                f"Batch analyzer script not found:\n{script_path}"
            )
            return

        # Build arguments - use -u for unbuffered output
        args = ["-u", str(script_path), "--save-results"]

        # Add limit (handle "ALL" case)
        if batch_size != "ALL":
            args.extend(["--limit", batch_size])

        if mode == "dry":
            args.append("--dry-run")

        # Start process
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._on_process_output)
        self._process.finished.connect(self._on_process_finished)
        self._process.errorOccurred.connect(self._on_process_error)

        # Set environment to ensure unbuffered output
        from PyQt6.QtCore import QProcessEnvironment
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUNBUFFERED", "1")
        self._process.setProcessEnvironment(env)

        # Log start
        mode_name = self.mode_combo.currentText()
        self._append_terminal(f"\n{'='*70}")
        self._append_terminal(f"Starting v3.0 dual-pass analysis: {batch_size} trades ({mode_name})")
        self._append_terminal(f"Script: {script_path}")
        self._append_terminal(f"{'='*70}\n")

        # Start
        self._process.start(sys.executable, args)

        # Update UI state
        self._is_running = True
        self._trades_processed = 0
        self._trades_total = int(batch_size)
        self.progress_bar.setValue(0)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.batch_combo.setEnabled(False)
        self.mode_combo.setEnabled(False)
        self.terminal_status.setText("Running...")
        self.terminal_status.setStyleSheet(f"color: {COLORS['status_running']};")
        self._update_status("Running batch analysis...")

    @pyqtSlot()
    def _on_stop_clicked(self):
        """Handle Stop button click."""
        if self._process and self._is_running:
            self._append_terminal("\n[!] Stopping analysis...", COLORS['status_error'])
            self._process.kill()

    @pyqtSlot()
    def _on_process_output(self):
        """Handle process output."""
        if not self._process:
            return

        # Read all available output
        data = self._process.readAllStandardOutput()
        if not data:
            return

        text = bytes(data).decode('utf-8', errors='replace')

        for line in text.splitlines():
            line = line.rstrip()
            if not line:
                continue

            # Parse progress from output like "[1/50]"
            if line.startswith("[") and "/" in line and "]" in line:
                try:
                    bracket_content = line.split("]")[0].replace("[", "")
                    if "/" in bracket_content:
                        parts = bracket_content.split("/")
                        current = int(parts[0])
                        total = int(parts[1])
                        self._trades_processed = current
                        self._trades_total = total
                        progress = int((current / total) * 100)
                        self.progress_bar.setValue(progress)
                        self._update_status(f"Processing trade {current}/{total}")
                except (ValueError, IndexError):
                    pass

            # Color output based on content
            if "ERROR" in line or "Error" in line or "Traceback" in line:
                self._append_terminal(line, COLORS['status_error'])
            elif "[OK]" in line or "Complete" in line or "Done!" in line:
                self._append_terminal(line, COLORS['status_complete'])
            elif "WRONG" in line or "DISAGREE" in line:
                self._append_terminal(line, "#ff9800")  # Orange
            elif "WIN" in line or "AGREE" in line:
                self._append_terminal(line, COLORS['status_complete'])
            elif "LOSS" in line:
                self._append_terminal(line, "#ff9800")  # Orange
            elif "Pass 1:" in line or "Pass 2:" in line:
                # Color pass results based on decision
                if "TRADE" in line and "NO_TRADE" not in line:
                    self._append_terminal(line, COLORS['status_complete'])
                elif "NO_TRADE" in line:
                    self._append_terminal(line, "#ff9800")  # Orange
                else:
                    self._append_terminal(line)
            else:
                self._append_terminal(line)

    @pyqtSlot(int, QProcess.ExitStatus)
    def _on_process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        """Handle process completion."""
        self._is_running = False
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.batch_combo.setEnabled(True)
        self.mode_combo.setEnabled(True)

        if exit_code == 0:
            self.progress_bar.setValue(100)
            self.terminal_status.setText("Complete")
            self.terminal_status.setStyleSheet(f"color: {COLORS['status_complete']};")
            self._append_terminal(f"\n{'='*70}")
            self._append_terminal("Analysis complete!", COLORS['status_complete'])
            self._update_status("Analysis complete")
        else:
            self.terminal_status.setText("Stopped")
            self.terminal_status.setStyleSheet(f"color: {COLORS['status_error']};")
            self._append_terminal(f"\n[!] Process exited with code {exit_code}", COLORS['status_error'])
            self._update_status(f"Stopped (exit code: {exit_code})")

    @pyqtSlot(QProcess.ProcessError)
    def _on_process_error(self, error: QProcess.ProcessError):
        """Handle process error."""
        self._is_running = False
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.batch_combo.setEnabled(True)
        self.mode_combo.setEnabled(True)

        self.terminal_status.setText("Error")
        self.terminal_status.setStyleSheet(f"color: {COLORS['status_error']};")

        error_messages = {
            QProcess.ProcessError.FailedToStart: "Failed to start process",
            QProcess.ProcessError.Crashed: "Process crashed",
            QProcess.ProcessError.Timedout: "Process timed out",
            QProcess.ProcessError.WriteError: "Write error",
            QProcess.ProcessError.ReadError: "Read error",
            QProcess.ProcessError.UnknownError: "Unknown error"
        }

        msg = error_messages.get(error, "Unknown error")
        self._append_terminal(f"\n[!] Error: {msg}", COLORS['status_error'])
        self._update_status(f"Error: {msg}")

    def closeEvent(self, event):
        """Handle window close."""
        if self._process and self._is_running:
            reply = QMessageBox.question(
                self,
                "Analysis Running",
                "Analysis is still running. Stop and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._process.kill()
                self._process.waitForFinished(3000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

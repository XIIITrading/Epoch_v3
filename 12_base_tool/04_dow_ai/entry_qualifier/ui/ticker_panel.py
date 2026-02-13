"""
Ticker Panel Widget
Epoch Trading System v1 - XIII Trading LLC

Individual ticker panel displaying rolling indicator data.
"""
import sys
from pathlib import Path

# Ensure entry_qualifier is at the front of sys.path
_entry_qualifier_dir = str(Path(__file__).parent.parent.resolve())
if _entry_qualifier_dir not in sys.path:
    sys.path.insert(0, _entry_qualifier_dir)
elif sys.path[0] != _entry_qualifier_dir:
    sys.path.remove(_entry_qualifier_dir)
    sys.path.insert(0, _entry_qualifier_dir)

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QFrame, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from typing import List, Optional

from eq_config import ROLLING_BARS, MILLION_THRESHOLD, THOUSAND_THRESHOLD
from ui.styles import COLORS, get_delta_style


class TickerPanel(QFrame):
    """
    Panel widget for displaying a single ticker's rolling data.

    Displays a table with 5 rows and 26 columns (25 rolling bars + label column).
    Rows: Candle Range, Vol Delta, Vol ROC, SMA Config, H1 Structure
    """

    # Signal emitted when remove button is clicked
    remove_requested = pyqtSignal(str)  # ticker

    # Row indices (top to bottom)
    ROW_CANDLE_RANGE = 0
    ROW_VOL_DELTA = 1
    ROW_VOL_ROC = 2
    ROW_SMA_CONFIG = 3
    ROW_H1_STRUCTURE = 4

    NUM_ROWS = 5

    # Row labels
    ROW_LABELS = {
        ROW_CANDLE_RANGE: 'Candle %',
        ROW_VOL_DELTA: 'Vol Δ',
        ROW_VOL_ROC: 'Vol ROC',
        ROW_SMA_CONFIG: 'SMA',
        ROW_H1_STRUCTURE: 'H1 Struct'
    }

    def __init__(self, ticker: str = None, parent=None):
        super().__init__(parent)
        self.ticker = ticker
        self._bars_data: List[dict] = []

        self.setObjectName("tickerPanel")
        self._setup_ui()

    def _setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header row with ticker name and remove button
        header_layout = QHBoxLayout()

        self.ticker_label = QLabel(self.ticker or "No Ticker Configured")
        self.ticker_label.setObjectName("tickerLabel")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.ticker_label.setFont(font)

        self.remove_btn = QPushButton("\u2715")  # X symbol
        self.remove_btn.setObjectName("removeButton")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        self.remove_btn.setToolTip("Remove ticker")

        header_layout.addWidget(self.ticker_label)
        header_layout.addStretch()
        header_layout.addWidget(self.remove_btn)

        layout.addLayout(header_layout)

        # Create the data table
        self._create_table()
        layout.addWidget(self.table)

        # Show placeholder if no ticker
        if not self.ticker:
            self._show_placeholder()

    def _create_table(self):
        """Create the data table widget."""
        # 5 rows, 26 columns (1 label + 25 data)
        self.table = QTableWidget(self.NUM_ROWS, ROLLING_BARS + 1)
        self.table.setMinimumHeight(160)
        self.table.setMaximumHeight(200)

        # Set up headers: label column first (empty), then 0 to -24 (left to right, newest to oldest)
        headers = [''] + [str(-i) for i in range(ROLLING_BARS)]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setVerticalHeaderLabels([''] * self.NUM_ROWS)

        # Hide vertical header
        self.table.verticalHeader().setVisible(False)

        # Configure horizontal header
        h_header = self.table.horizontalHeader()
        h_header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        h_header.setMinimumSectionSize(40)

        # Set first column (label column) to fixed width
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 90)

        # Disable editing and selection
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Initialize cells
        self._initialize_cells()

    def _initialize_cells(self):
        """Initialize all cells with default values."""
        cell_font = QFont("Segoe UI", 10)  # 10pt font for table cells

        for row in range(self.NUM_ROWS):
            for col in range(ROLLING_BARS + 1):
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFont(cell_font)

                if col == 0:
                    # Label column (first column)
                    item.setText(self.ROW_LABELS.get(row, ''))
                    item.setForeground(QColor(COLORS['text_secondary']))
                else:
                    # Data column - show dash for empty
                    item.setText('-')
                    item.setForeground(QColor(COLORS['text_muted']))

                self.table.setItem(row, col, item)

    def _show_placeholder(self):
        """Show placeholder state when no ticker is configured."""
        self.ticker_label.setText("No Ticker Configured")
        self.ticker_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        self.remove_btn.hide()
        self.table.setEnabled(False)

    def set_ticker(self, ticker: str):
        """Set the ticker for this panel."""
        self.ticker = ticker.upper().strip() if ticker else None

        if self.ticker:
            self.ticker_label.setText(self.ticker)
            self.ticker_label.setStyleSheet(f"color: {COLORS['text_primary']};")
            self.remove_btn.show()
            self.table.setEnabled(True)
        else:
            self._show_placeholder()

    def update_data(self, bars: List[dict]):
        """
        Update the panel with new bar data.

        Args:
            bars: List of processed bar dictionaries with keys:
                  timestamp, open, high, low, close, volume,
                  raw_delta, roll_delta, candle_range_pct, is_absorption
        """
        self._bars_data = bars

        # Take the most recent ROLLING_BARS
        display_bars = bars[-ROLLING_BARS:] if len(bars) >= ROLLING_BARS else bars

        # Calculate offset if we have fewer bars than columns
        # Data columns start at index 1 (column 0 is the label column)
        offset = ROLLING_BARS - len(display_bars)

        # Clear cells after the available data (data columns start at 1)
        # With reversed order, empty cells are at the end (higher column indices)
        for row in range(self.NUM_ROWS):
            for col in range(len(display_bars) + 1, ROLLING_BARS + 1):
                item = self.table.item(row, col)
                if item:
                    item.setText('-')
                    item.setForeground(QColor(COLORS['text_muted']))
                    item.setBackground(QColor(COLORS['bg_cell']))

        # Update data cells (data columns start at 1, newest first)
        # Reverse the display_bars so most recent (index -1) maps to column 1
        for i, bar in enumerate(reversed(display_bars)):
            col = i + 1  # +1 because column 0 is the label column

            # Check if this is an absorption zone (should dim entire column)
            is_absorption = bar.get('is_absorption', False)

            # Get indicator values
            candle_range_pct = bar.get('candle_range_pct', 0)
            roll_delta = bar.get('roll_delta')
            volume_roc = bar.get('volume_roc')

            # Update Candle Range % (Row 0)
            self._update_candle_range_cell(col, candle_range_pct, is_absorption)

            # Update Vol Delta (Row 1) - using roll_delta as primary
            self._update_delta_cell(self.ROW_VOL_DELTA, col, roll_delta, is_absorption)

            # Update Vol ROC (Row 2)
            self._update_volume_roc_cell(col, volume_roc, is_absorption)

            # Update SMA Config (Row 3)
            sma_display = bar.get('sma_display')
            sma_config = bar.get('sma_config')
            self._update_sma_cell(col, sma_display, sma_config, is_absorption)

            # Update H1 Structure (Row 4)
            h1_display = bar.get('h1_display')
            h1_structure = bar.get('h1_structure')
            self._update_h1_structure_cell(col, h1_display, h1_structure, is_absorption)

    def _update_delta_cell(self, row: int, col: int, value: Optional[float], is_absorption: bool = False):
        """Update a delta cell with conditional formatting."""
        item = self.table.item(row, col)
        if not item:
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, col, item)

        # Apply dimmed styling for absorption zones
        if is_absorption:
            item.setBackground(QColor(COLORS['dimmed_bg']))
            if value is None:
                item.setText('-')
            else:
                item.setText(self._format_number(value))
            item.setForeground(QColor(COLORS['dimmed_text']))
            return

        # Reset background
        item.setBackground(QColor(COLORS['bg_cell']))

        if value is None:
            item.setText('-')
            item.setForeground(QColor(COLORS['text_muted']))
            return

        # Format the value
        formatted = self._format_number(value)
        item.setText(formatted)

        # Apply conditional text color
        if value > 0:
            item.setForeground(QColor(COLORS['positive']))
        elif value < 0:
            item.setForeground(QColor(COLORS['negative']))
        else:
            item.setForeground(QColor(COLORS['neutral']))

    def _update_candle_range_cell(self, col: int, value: float, is_absorption: bool = False):
        """Update the candle range cell with percentage formatting."""
        item = self.table.item(self.ROW_CANDLE_RANGE, col)
        if not item:
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(self.ROW_CANDLE_RANGE, col, item)

        # Format as percentage with 2 decimal places
        formatted = f"{value:.2f}%"
        item.setText(formatted)

        # Apply dimmed styling for absorption zones
        if is_absorption:
            item.setBackground(QColor(COLORS['dimmed_bg']))
            item.setForeground(QColor(COLORS['dimmed_text']))
        else:
            item.setBackground(QColor(COLORS['bg_cell']))
            # Use positive color for good range, neutral for borderline
            if value >= 0.15:
                item.setForeground(QColor(COLORS['positive']))
            elif value >= 0.12:
                item.setForeground(QColor(COLORS['neutral']))
            else:
                item.setForeground(QColor(COLORS['negative']))

    def _update_volume_roc_cell(self, col: int, value: Optional[float], is_absorption: bool = False):
        """Update the volume ROC cell with percentage formatting."""
        item = self.table.item(self.ROW_VOL_ROC, col)
        if not item:
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(self.ROW_VOL_ROC, col, item)

        # Apply dimmed styling for absorption zones
        if is_absorption:
            item.setBackground(QColor(COLORS['dimmed_bg']))
            if value is None:
                item.setText('-')
            else:
                item.setText(f"{value:+.0f}%")
            item.setForeground(QColor(COLORS['dimmed_text']))
            return

        # Reset background
        item.setBackground(QColor(COLORS['bg_cell']))

        if value is None:
            item.setText('-')
            item.setForeground(QColor(COLORS['text_muted']))
            return

        # Format as percentage with sign
        formatted = f"{value:+.0f}%"
        item.setText(formatted)

        # Color coding: green if >= 30% (elevated), otherwise neutral
        if value >= 30:
            item.setForeground(QColor(COLORS['positive']))
        elif value >= 0:
            item.setForeground(QColor(COLORS['neutral']))
        else:
            item.setForeground(QColor(COLORS['negative']))

    def _update_sma_cell(self, col: int, display: Optional[str], config, is_absorption: bool = False):
        """Update the SMA config cell."""
        item = self.table.item(self.ROW_SMA_CONFIG, col)
        if not item:
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(self.ROW_SMA_CONFIG, col, item)

        # Apply dimmed styling for absorption zones
        if is_absorption:
            item.setBackground(QColor(COLORS['dimmed_bg']))
            item.setText(display if display else '-')
            item.setForeground(QColor(COLORS['dimmed_text']))
            return

        # Reset background
        item.setBackground(QColor(COLORS['bg_cell']))

        if display is None:
            item.setText('-')
            item.setForeground(QColor(COLORS['text_muted']))
            return

        item.setText(display)

        # Color based on config: green for BULL, red for BEAR
        # Import check for enum comparison
        if config is not None:
            config_value = config.value if hasattr(config, 'value') else str(config)
            if config_value == 'BULL':
                item.setForeground(QColor(COLORS['positive']))
            elif config_value == 'BEAR':
                item.setForeground(QColor(COLORS['negative']))
            else:
                item.setForeground(QColor(COLORS['neutral']))
        else:
            item.setForeground(QColor(COLORS['text_primary']))

    def _update_h1_structure_cell(self, col: int, display: Optional[str], structure, is_absorption: bool = False):
        """Update the H1 structure cell."""
        item = self.table.item(self.ROW_H1_STRUCTURE, col)
        if not item:
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(self.ROW_H1_STRUCTURE, col, item)

        # Apply dimmed styling for absorption zones
        if is_absorption:
            item.setBackground(QColor(COLORS['dimmed_bg']))
            item.setText(display if display else '-')
            item.setForeground(QColor(COLORS['dimmed_text']))
            return

        # Reset background
        item.setBackground(QColor(COLORS['bg_cell']))

        if display is None:
            item.setText('-')
            item.setForeground(QColor(COLORS['text_muted']))
            return

        item.setText(display)

        # Color based on structure
        # Per spec: NEUTRAL is the best condition, highlight it
        if structure is not None:
            struct_value = structure.value if hasattr(structure, 'value') else str(structure)
            if struct_value == 'NEUT':
                # NEUTRAL is preferred - use a highlight color (cyan/teal)
                item.setForeground(QColor('#00BCD4'))  # Cyan for best condition
            elif struct_value == 'BULL':
                item.setForeground(QColor(COLORS['positive']))
            elif struct_value == 'BEAR':
                item.setForeground(QColor(COLORS['negative']))
            else:
                item.setForeground(QColor(COLORS['neutral']))
        else:
            item.setForeground(QColor(COLORS['text_primary']))

    def _format_number(self, value: float) -> str:
        """
        Format a number for display.

        Formats:
        - >= 1,000,000: X.XM (rounded to whole number for abbreviation)
        - >= 1,000: Xk (rounded to whole number)
        - < 1,000: Whole number
        - Negative: Prefix with -
        - Positive: Prefix with +
        """
        if value == 0:
            return '0'

        sign = '+' if value > 0 else ''
        abs_value = abs(value)

        if abs_value >= MILLION_THRESHOLD:
            # Format as millions (whole number)
            formatted = f"{sign}{int(value / MILLION_THRESHOLD)}M"
        elif abs_value >= THOUSAND_THRESHOLD:
            # Format as thousands (whole number)
            formatted = f"{sign}{int(value / THOUSAND_THRESHOLD)}k"
        else:
            # Whole number
            formatted = f"{sign}{int(value)}"

        return formatted

    def clear_data(self):
        """Clear all data cells (on error or ticker removal)."""
        for row in range(self.NUM_ROWS):
            # Data columns start at 1 (column 0 is the label column)
            for col in range(1, ROLLING_BARS + 1):
                item = self.table.item(row, col)
                if item:
                    item.setText('-')
                    item.setForeground(QColor(COLORS['text_muted']))
                    item.setBackground(QColor(COLORS['bg_cell']))

    def show_error(self, message: str):
        """Display error state (blank cells, show message in label)."""
        self.clear_data()
        # Could add error indicator to UI here if needed

    def _on_remove_clicked(self):
        """Handle remove button click."""
        if self.ticker:
            self.remove_requested.emit(self.ticker)

    def get_ticker(self) -> Optional[str]:
        """Get the current ticker."""
        return self.ticker

    def has_ticker(self) -> bool:
        """Check if a ticker is configured."""
        return self.ticker is not None and len(self.ticker) > 0

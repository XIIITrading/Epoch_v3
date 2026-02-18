"""
TradingView Dark Theme Stylesheet
Epoch Trading System v2.0 - XIII Trading LLC

Dark theme for the Journal Processor GUI.
"""

DARK_STYLESHEET = """
QMainWindow { background-color: #1e222d; }
QWidget { background-color: #1e222d; color: #d1d4dc; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
QGroupBox { border: 1px solid #363a45; border-radius: 4px; margin-top: 8px; padding-top: 16px; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #00bcd4; }
QPushButton { background-color: #2962ff; color: white; border: none; border-radius: 4px; padding: 8px 16px; font-weight: bold; }
QPushButton:hover { background-color: #1e88e5; }
QPushButton:disabled { background-color: #363a45; color: #787b86; }
QPushButton#stopBtn { background-color: #f44336; }
QPushButton#stopBtn:hover { background-color: #d32f2f; }
QPushButton#statusBtn { background-color: #363a45; }
QPushButton#statusBtn:hover { background-color: #434651; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; }
QCheckBox::indicator:checked { background-color: #2962ff; border: 1px solid #2962ff; border-radius: 3px; }
QCheckBox::indicator:unchecked { background-color: #2a2e39; border: 1px solid #363a45; border-radius: 3px; }
QTextEdit { background-color: #131722; color: #d1d4dc; border: 1px solid #363a45; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 12px; }
QProgressBar { background-color: #2a2e39; border: 1px solid #363a45; border-radius: 4px; height: 20px; text-align: center; color: white; }
QProgressBar::chunk { background-color: #2962ff; border-radius: 3px; }
QLabel#titleLabel { font-size: 18px; font-weight: bold; color: #00bcd4; }
"""

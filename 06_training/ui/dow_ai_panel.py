"""
Epoch Trading System - DOW AI Panel
AI prediction display + copy-paste prompt sections.
"""

import logging
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QApplication
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from typing import Dict, Any, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.trade import TradeWithMetrics, TradeAnalysis
from components.dow_ai.data_fetcher import DOWAIDataFetcher
from components.dow_ai.prompt_generator import generate_pre_trade_prompt, generate_post_trade_prompt

logger = logging.getLogger(__name__)


# =============================================================================
# AI PREDICTION DISPLAY
# =============================================================================

class AIPredictionDisplay(QFrame):
    """Renders AI prediction from ai_predictions table."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background-color: #1a1a2e; border: 1px solid #333; border-radius: 8px; padding: 12px;")
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Decision + confidence
        self._decision_label = QLabel("--")
        self._decision_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._decision_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._decision_label)

        self._confidence_label = QLabel("Confidence: --")
        self._confidence_label.setFont(QFont("Segoe UI", 10))
        self._confidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._confidence_label.setStyleSheet("color: #888888;")
        layout.addWidget(self._confidence_label)

        self._meta_label = QLabel("")
        self._meta_label.setFont(QFont("Segoe UI", 10))
        self._meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._meta_label.setStyleSheet("color: #666666;")
        layout.addWidget(self._meta_label)

        # Reasoning (collapsed)
        self._reasoning_btn = QPushButton("> Reasoning")
        self._reasoning_btn.setCheckable(True)
        self._reasoning_btn.setChecked(False)
        self._reasoning_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #888;
                border: none; text-align: left; font-size: 10pt;
            }
        """)
        self._reasoning_btn.toggled.connect(self._toggle_reasoning)
        layout.addWidget(self._reasoning_btn)

        self._reasoning_text = QLabel("")
        self._reasoning_text.setWordWrap(True)
        self._reasoning_text.setVisible(False)
        self._reasoning_text.setStyleSheet("color: #aaaaaa; font-style: italic; padding: 4px;")
        layout.addWidget(self._reasoning_text)

        # Extracted indicators
        self._indicators_label = QLabel("")
        self._indicators_label.setWordWrap(True)
        self._indicators_label.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(self._indicators_label)

        # Outcome tracking
        self._outcome_label = QLabel("")
        self._outcome_label.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(self._outcome_label)

        # Version/model
        self._version_label = QLabel("")
        self._version_label.setFont(QFont("Segoe UI", 10))
        self._version_label.setStyleSheet("color: #555555;")
        layout.addWidget(self._version_label)

    def _toggle_reasoning(self, checked: bool):
        self._reasoning_text.setVisible(checked)
        arrow = "v" if checked else ">"
        self._reasoning_btn.setText(f"{arrow} Reasoning")

    def update_prediction(self, pred: Optional[Dict[str, Any]]):
        """Update display from prediction dict."""
        if not pred:
            self._decision_label.setText("No AI Prediction")
            self._decision_label.setStyleSheet("color: #555555;")
            self._confidence_label.setText("")
            self._meta_label.setText("")
            self._indicators_label.setText("")
            self._outcome_label.setText("")
            self._version_label.setText("")
            self._reasoning_text.setText("")
            return

        prediction = pred.get('prediction', 'N/A')
        confidence = pred.get('confidence', 'N/A')

        # Decision color
        dec_colors = {'TRADE': '#4CAF50', 'NO_TRADE': '#FF5252'}
        dec_color = dec_colors.get(prediction, '#888888')

        # Correctness badge
        is_correct = pred.get('prediction_correct')
        badge = ""
        if is_correct is True:
            badge = "  [CORRECT]"
        elif is_correct is False:
            badge = "  [WRONG]"

        self._decision_label.setText(f"{prediction}{badge}")
        self._decision_label.setStyleSheet(f"color: {dec_color}; font-weight: bold;")

        # Confidence
        conf_colors = {'HIGH': '#4CAF50', 'MEDIUM': '#FFD700', 'LOW': '#FF9800'}
        conf_color = conf_colors.get(confidence, '#888888')
        self._confidence_label.setText(f"Confidence: {confidence}")
        self._confidence_label.setStyleSheet(f"color: {conf_color};")

        # Meta
        self._meta_label.setText(
            f"{pred.get('direction', '')} | {pred.get('model', '')} | {pred.get('zone_type', '')}"
        )

        # Reasoning
        reasoning = pred.get('reasoning')
        if reasoning:
            self._reasoning_text.setText(reasoning)
            self._reasoning_btn.setVisible(True)
        else:
            self._reasoning_btn.setVisible(False)

        # Indicators
        candle_pct = pred.get('candle_pct')
        vol_delta = pred.get('vol_delta')
        vol_roc = pred.get('vol_roc')
        sma = pred.get('sma')
        h1_struct = pred.get('h1_struct')

        candle_str = f"{candle_pct:.2f}%" if candle_pct is not None else "N/A"
        vol_roc_str = f"{vol_roc:+.0f}%" if vol_roc is not None else "N/A"
        vol_delta_str = _format_vol_delta(vol_delta)

        self._indicators_label.setText(
            f"Candle %: {candle_str} ({pred.get('candle_status', 'N/A')})\n"
            f"Vol Delta: {vol_delta_str} ({pred.get('vol_delta_status', 'N/A')})\n"
            f"Vol ROC: {vol_roc_str} ({pred.get('vol_roc_status', 'N/A')})\n"
            f"SMA: {sma or 'N/A'} | H1 Structure: {h1_struct or 'N/A'}"
        )

        # Outcome
        actual_outcome = pred.get('actual_outcome')
        if actual_outcome:
            actual_pnl_r = pred.get('actual_pnl_r')
            pnl_str = f"{actual_pnl_r:+.2f}R" if actual_pnl_r is not None else "N/A"
            outcome_color = "#4CAF50" if actual_outcome in ('WIN', 'winner') else "#FF5252"
            self._outcome_label.setText(f"Actual: {actual_outcome.upper()} ({pnl_str})")
            self._outcome_label.setStyleSheet(f"color: {outcome_color};")
        else:
            self._outcome_label.setText("")

        # Version
        self._version_label.setText(
            f"v{pred.get('prompt_version', 'N/A')} | {pred.get('model_used', 'N/A')}"
        )


# =============================================================================
# DOW AI PROMPT SECTION
# =============================================================================

class DOWAIPromptSection(QFrame):
    """Copy-paste prompt section for DOW AI analysis."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title_text = title
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Toggle
        self._toggle_btn = QPushButton(f"> {self._title_text}")
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setChecked(False)
        self._toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a4e; color: #e0e0e0;
                border: 1px solid #333; border-radius: 4px;
                padding: 6px; text-align: left; font-weight: bold;
            }
            QPushButton:checked { background-color: #3a3a5e; }
        """)
        self._toggle_btn.toggled.connect(self._toggle_content)
        layout.addWidget(self._toggle_btn)

        # Content
        self._content = QFrame()
        self._content.setVisible(False)
        content_layout = QVBoxLayout(self._content)

        # Existing analysis indicator
        self._existing_label = QLabel("")
        self._existing_label.setStyleSheet("color: #4CAF50;")
        self._existing_label.setVisible(False)
        content_layout.addWidget(self._existing_label)

        # Warnings
        self._warnings_label = QLabel("")
        self._warnings_label.setWordWrap(True)
        self._warnings_label.setStyleSheet("color: #FFC107;")
        self._warnings_label.setVisible(False)
        content_layout.addWidget(self._warnings_label)

        # Prompt display
        prompt_label = QLabel("Prompt:")
        prompt_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        prompt_label.setStyleSheet("color: #e0e0e0;")
        content_layout.addWidget(prompt_label)

        self._prompt_text = QTextEdit()
        self._prompt_text.setReadOnly(True)
        self._prompt_text.setMaximumHeight(250)
        self._prompt_text.setStyleSheet("""
            QTextEdit {
                background-color: #16213e; color: #e0e0e0;
                border: 1px solid #333; border-radius: 4px; padding: 6px;
                font-family: Consolas; font-size: 10pt;
            }
        """)
        content_layout.addWidget(self._prompt_text)

        # Copy button
        self._copy_btn = QPushButton("Copy to Clipboard")
        self._copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white;
                border: none; border-radius: 4px; padding: 8px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self._copy_btn.clicked.connect(self._copy_prompt)
        content_layout.addWidget(self._copy_btn)

        # Prompt stats
        self._stats_label = QLabel("")
        self._stats_label.setFont(QFont("Segoe UI", 10))
        self._stats_label.setStyleSheet("color: #555555;")
        content_layout.addWidget(self._stats_label)

        # Response paste area
        resp_label = QLabel("Paste Claude's Response:")
        resp_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        resp_label.setStyleSheet("color: #e0e0e0;")
        content_layout.addWidget(resp_label)

        self._response_text = QTextEdit()
        self._response_text.setMaximumHeight(200)
        self._response_text.setPlaceholderText("Paste Claude's response here...")
        self._response_text.setStyleSheet("""
            QTextEdit {
                background-color: #16213e; color: #e0e0e0;
                border: 1px solid #333; border-radius: 4px; padding: 6px;
            }
        """)
        content_layout.addWidget(self._response_text)

        # Save button
        self._save_btn = QPushButton("Save Analysis")
        self._save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; color: white;
                border: none; border-radius: 4px; padding: 8px;
            }
            QPushButton:hover { background-color: #1E88E5; }
            QPushButton:disabled { background-color: #555555; }
        """)
        content_layout.addWidget(self._save_btn)

        layout.addWidget(self._content)

        # Store references for save handler
        self._supabase = None
        self._trade_id = None
        self._mode = None

        self._save_btn.clicked.connect(self._save_analysis)

    def _toggle_content(self, checked: bool):
        self._content.setVisible(checked)
        arrow = "v" if checked else ">"
        has_check = " [Saved]" if self._existing_label.isVisible() else ""
        self._toggle_btn.setText(f"{arrow} {self._title_text}{has_check}")

    def _copy_prompt(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._prompt_text.toPlainText())
        self._copy_btn.setText("Copied!")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self._copy_btn.setText("Copy to Clipboard"))

    def _save_analysis(self):
        response = self._response_text.toPlainText().strip()
        if not response or not self._supabase or not self._trade_id:
            return

        try:
            success = self._supabase.upsert_analysis(
                trade_id=self._trade_id,
                analysis_type=self._mode,
                response_text=response,
                prompt_text=self._prompt_text.toPlainText()
            )
            if success:
                self._existing_label.setText("Analysis saved")
                self._existing_label.setVisible(True)
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")

    def update_prompt(
        self,
        prompt: str,
        trade_id: str,
        mode: str,
        supabase_client,
        existing_analysis: Optional[TradeAnalysis] = None,
        warnings: list = None
    ):
        """Set the prompt text and configure save handler."""
        self._prompt_text.setPlainText(prompt)
        self._trade_id = trade_id
        self._mode = mode
        self._supabase = supabase_client

        # Stats
        self._stats_label.setText(
            f"Prompt: {len(prompt):,} chars | {len(prompt.split()):,} words"
        )

        # Existing analysis
        if existing_analysis:
            self._existing_label.setText("Analysis saved")
            self._existing_label.setVisible(True)
            self._response_text.setPlainText(existing_analysis.response_text)
        else:
            self._existing_label.setVisible(False)
            self._response_text.clear()

        # Warnings
        if warnings:
            self._warnings_label.setText("Missing data:\n- " + "\n- ".join(warnings))
            self._warnings_label.setVisible(True)
        else:
            self._warnings_label.setVisible(False)

    def clear(self):
        self._prompt_text.clear()
        self._response_text.clear()
        self._existing_label.setVisible(False)
        self._warnings_label.setVisible(False)
        self._toggle_btn.setChecked(False)


# =============================================================================
# MAIN DOW AI PANEL
# =============================================================================

class DOWAIPanel(QFrame):
    """Complete DOW AI section: prediction display + pre/post trade prompts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # AI Prediction detail (collapsible)
        self._prediction_toggle = QPushButton("> DOW AI Prediction Detail")
        self._prediction_toggle.setCheckable(True)
        self._prediction_toggle.setChecked(False)
        self._prediction_toggle.setStyleSheet("""
            QPushButton {
                background-color: #2a2a4e; color: #e0e0e0;
                border: 1px solid #333; border-radius: 4px;
                padding: 6px; text-align: left; font-weight: bold;
            }
            QPushButton:checked { background-color: #3a3a5e; }
        """)
        self._prediction_toggle.toggled.connect(self._toggle_prediction)
        layout.addWidget(self._prediction_toggle)

        self._prediction_display = AIPredictionDisplay()
        self._prediction_display.setVisible(False)
        layout.addWidget(self._prediction_display)

        # Post-trade review prompt
        self._post_trade_section = DOWAIPromptSection("DOW AI Post-Trade Review")
        layout.addWidget(self._post_trade_section)

    def _toggle_prediction(self, checked: bool):
        self._prediction_display.setVisible(checked)
        arrow = "v" if checked else ">"
        self._prediction_toggle.setText(f"{arrow} DOW AI Prediction Detail")

    def update_trade(
        self,
        trade: TradeWithMetrics,
        events: Dict,
        supabase_client,
        ai_prediction: Optional[Dict] = None,
        mode: str = 'post_trade'
    ):
        """Update all DOW AI sections for a trade."""
        # Update prediction display
        self._prediction_display.update_prediction(ai_prediction)
        self._prediction_toggle.setVisible(ai_prediction is not None)

        # Generate post-trade prompt
        try:
            zone_type = trade.zone_type or 'PRIMARY'
            fetcher = DOWAIDataFetcher(supabase_client)
            context = fetcher.fetch_all_context(
                ticker=trade.ticker,
                trade_date=trade.date,
                zone_type=zone_type
            )

            warnings = []
            if context.get('bar_data') is None:
                warnings.append("Bar data (ATR, Camarilla) not found")
            if context.get('hvn_pocs') is None:
                warnings.append("HVN POC levels not found")
            if context.get('market_structure') is None:
                warnings.append("Market structure data not found")
            if context.get('setup') is None:
                warnings.append("Setup data not found")

            prompt = generate_post_trade_prompt(trade, events, context)

            existing = None
            try:
                existing = supabase_client.fetch_analysis(trade.trade_id, 'post_trade')
            except Exception:
                pass

            self._post_trade_section.update_prompt(
                prompt=prompt,
                trade_id=trade.trade_id,
                mode='post_trade',
                supabase_client=supabase_client,
                existing_analysis=existing,
                warnings=warnings
            )
        except Exception as e:
            logger.error(f"Failed to generate DOW AI prompt: {e}")

    def clear(self):
        self._prediction_display.update_prediction(None)
        self._post_trade_section.clear()
        self._prediction_toggle.setChecked(False)


def _format_vol_delta(value) -> str:
    if value is None:
        return 'N/A'
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:+,.1f}M"
    elif abs(value) >= 1_000:
        return f"{value/1_000:+,.0f}K"
    return f"{value:+,.0f}"

"""
Epoch Trading System - Indicator Refinement Panel
Continuation (0-10) and Rejection (0-11) scores with component indicators.
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QPushButton, QTextEdit
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from typing import Dict, Any, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.trade import TradeWithMetrics


# =============================================================================
# COLOR HELPERS
# =============================================================================

def _score_color(score: Optional[int], max_score: int) -> str:
    if score is None:
        return "#888888"
    pct = score / max_score
    if pct >= 0.8:
        return "#00C853"
    elif pct >= 0.6:
        return "#8BC34A"
    elif pct >= 0.4:
        return "#FFC107"
    elif pct >= 0.2:
        return "#FF9800"
    return "#FF1744"


def _label_color(label: Optional[str]) -> str:
    if not label:
        return "#888888"
    l = label.upper()
    if l == 'STRONG':
        return "#00C853"
    elif l == 'GOOD':
        return "#8BC34A"
    elif l == 'WEAK':
        return "#FF9800"
    elif l == 'AVOID':
        return "#FF1744"
    return "#888888"


def _bool_icon(value: Optional[bool]) -> str:
    if value is None:
        return "?"
    return "Y" if value else "N"


def _bool_color(value: Optional[bool]) -> str:
    if value is None:
        return "#888888"
    return "#00C853" if value else "#FF1744"


# =============================================================================
# INDICATOR ROW WIDGET
# =============================================================================

class IndicatorRow(QFrame):
    """Single indicator display with name, score, and detail labels."""

    def __init__(self, name: str, max_score: int, parent=None):
        super().__init__(parent)
        self._max_score = max_score
        self.setStyleSheet("background-color: #16213e; border-radius: 4px; padding: 4px;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self._name_label = QLabel(name)
        self._name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._name_label.setStyleSheet("color: #e0e0e0;")
        self._name_label.setFixedWidth(200)
        layout.addWidget(self._name_label)

        self._score_label = QLabel(f"0/{max_score}")
        self._score_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._score_label.setFixedWidth(60)
        layout.addWidget(self._score_label)

        self._detail_label = QLabel("")
        self._detail_label.setFont(QFont("Segoe UI", 10))
        self._detail_label.setStyleSheet("color: #aaaaaa;")
        layout.addWidget(self._detail_label, 1)

    def update(self, score: int, details: str):
        color = _score_color(score, self._max_score)
        self._score_label.setText(f"{score}/{self._max_score}")
        self._score_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self._detail_label.setText(details)


# =============================================================================
# MAIN PANEL
# =============================================================================

class IndicatorPanel(QFrame):
    """Indicator Refinement panel with Continuation and Rejection scores."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Collapsible toggle
        self._toggle_btn = QPushButton("> Indicator Refinement Analysis")
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

        # Content frame
        self._content = QFrame()
        self._content.setVisible(False)
        content_layout = QVBoxLayout(self._content)
        content_layout.setSpacing(6)

        # Header row: trade type + composite scores
        header_row = QHBoxLayout()

        self._type_label = QLabel("Trade Type: --")
        self._type_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._type_label.setStyleSheet("color: #e0e0e0;")
        header_row.addWidget(self._type_label)

        header_row.addStretch()

        self._cont_score_label = QLabel("Continuation: --/10")
        self._cont_score_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header_row.addWidget(self._cont_score_label)

        self._rej_score_label = QLabel("Rejection: --/11")
        self._rej_score_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header_row.addWidget(self._rej_score_label)

        content_layout.addLayout(header_row)

        # Continuation indicators
        cont_title = QLabel("Continuation Indicators (0-10 pts)")
        cont_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        cont_title.setStyleSheet("color: #4CAF50;")
        content_layout.addWidget(cont_title)

        self._cont_rows = {}
        cont_indicators = [
            ('mtf', 'CONT-01: MTF Alignment', 4),
            ('sma_mom', 'CONT-02: SMA Momentum', 2),
            ('vol_thrust', 'CONT-03: Volume Thrust', 2),
            ('pullback', 'CONT-04: Pullback Quality', 2),
        ]
        for key, name, max_score in cont_indicators:
            row = IndicatorRow(name, max_score)
            content_layout.addWidget(row)
            self._cont_rows[key] = row

        # Rejection indicators
        rej_title = QLabel("Rejection Indicators (0-11 pts)")
        rej_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        rej_title.setStyleSheet("color: #FF9800;")
        content_layout.addWidget(rej_title)

        self._rej_rows = {}
        rej_indicators = [
            ('struct_div', 'REJ-01: Structure Divergence', 2),
            ('sma_exhst', 'REJ-02: SMA Exhaustion', 3),
            ('delta_abs', 'REJ-03: Delta Absorption', 2),
            ('vol_climax', 'REJ-04: Volume Climax', 2),
            ('cvd_extr', 'REJ-05: CVD Extreme', 2),
        ]
        for key, name, max_score in rej_indicators:
            row = IndicatorRow(name, max_score)
            content_layout.addWidget(row)
            self._rej_rows[key] = row

        # Monte AI prompt section
        self._prompt_btn = QPushButton("> Monte AI Analysis Prompt")
        self._prompt_btn.setCheckable(True)
        self._prompt_btn.setChecked(False)
        self._prompt_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a4e; color: #e0e0e0;
                border: 1px solid #333; border-radius: 4px;
                padding: 4px; text-align: left;
            }
            QPushButton:checked { background-color: #3a3a5e; }
        """)
        self._prompt_btn.toggled.connect(self._toggle_prompt)
        content_layout.addWidget(self._prompt_btn)

        self._prompt_text = QTextEdit()
        self._prompt_text.setReadOnly(True)
        self._prompt_text.setVisible(False)
        self._prompt_text.setMaximumHeight(300)
        self._prompt_text.setStyleSheet("""
            QTextEdit {
                background-color: #16213e; color: #e0e0e0;
                border: 1px solid #333; border-radius: 4px; padding: 6px;
                font-family: Consolas; font-size: 10pt;
            }
        """)
        content_layout.addWidget(self._prompt_text)

        layout.addWidget(self._content)

    def _toggle_content(self, checked: bool):
        self._content.setVisible(checked)
        arrow = "v" if checked else ">"
        self._toggle_btn.setText(f"{arrow} Indicator Refinement Analysis")

    def _toggle_prompt(self, checked: bool):
        self._prompt_text.setVisible(checked)
        arrow = "v" if checked else ">"
        self._prompt_btn.setText(f"{arrow} Monte AI Analysis Prompt")

    def update_refinement(self, refinement: Optional[Dict[str, Any]], trade: TradeWithMetrics = None):
        """Update panel from refinement data dict."""
        if not refinement:
            self._type_label.setText("No indicator refinement data available")
            return

        trade_type = refinement.get('trade_type', 'UNKNOWN')
        is_cont = trade_type == 'CONTINUATION'
        model = refinement.get('model', 'N/A')
        direction = refinement.get('direction', 'N/A')

        type_color = "#4CAF50" if is_cont else "#FF9800"
        self._type_label.setText(f"Trade Type: {trade_type} ({model}) | {direction}")
        self._type_label.setStyleSheet(f"color: {type_color}; font-weight: bold;")

        # Composite scores
        cont_score = refinement.get('continuation_score', 0)
        cont_label = refinement.get('continuation_label', 'UNKNOWN')
        cont_color = _score_color(cont_score, 10)
        cont_lbl_color = _label_color(cont_label)
        highlight = "border: 2px solid #4CAF50; border-radius: 6px; padding: 4px;" if is_cont else ""
        self._cont_score_label.setText(f"Continuation: {cont_score}/10 ({cont_label})")
        self._cont_score_label.setStyleSheet(f"color: {cont_color}; font-weight: bold; {highlight}")

        rej_score = refinement.get('rejection_score', 0)
        rej_label = refinement.get('rejection_label', 'UNKNOWN')
        rej_color = _score_color(rej_score, 11)
        highlight = "border: 2px solid #FF9800; border-radius: 6px; padding: 4px;" if not is_cont else ""
        self._rej_score_label.setText(f"Rejection: {rej_score}/11 ({rej_label})")
        self._rej_score_label.setStyleSheet(f"color: {rej_color}; font-weight: bold; {highlight}")

        # Continuation indicators
        self._cont_rows['mtf'].update(
            refinement.get('mtf_align_score', 0),
            f"H4: {_bool_icon(refinement.get('mtf_h4_aligned'))} | "
            f"H1: {_bool_icon(refinement.get('mtf_h1_aligned'))} | "
            f"M15: {_bool_icon(refinement.get('mtf_m15_aligned'))} | "
            f"M5: {_bool_icon(refinement.get('mtf_m5_aligned'))}"
        )

        spread = refinement.get('sma_spread')
        spread_str = f"{spread:.4f}" if spread is not None else "-"
        roc = refinement.get('sma_spread_roc')
        roc_str = f"{roc:+.1f}%" if roc is not None else "-"
        self._cont_rows['sma_mom'].update(
            refinement.get('sma_mom_score', 0),
            f"Spread: {spread_str} | ROC: {roc_str} | "
            f"Aligned: {_bool_icon(refinement.get('sma_spread_aligned'))} | "
            f"Expanding: {_bool_icon(refinement.get('sma_spread_expanding'))}"
        )

        vol_roc = refinement.get('vol_roc')
        vol_roc_str = f"{vol_roc:+.1f}%" if vol_roc is not None else "-"
        delta_5 = refinement.get('vol_delta_5')
        delta_str = f"{delta_5:+.0f}" if delta_5 is not None else "-"
        self._cont_rows['vol_thrust'].update(
            refinement.get('vol_thrust_score', 0),
            f"Vol ROC: {vol_roc_str} (Strong: {_bool_icon(refinement.get('vol_roc_strong'))}) | "
            f"Delta 5-bar: {delta_str} (Aligned: {_bool_icon(refinement.get('vol_delta_aligned'))})"
        )

        ratio = refinement.get('pullback_delta_ratio')
        ratio_str = f"{ratio:.2f}" if ratio is not None else "-"
        self._cont_rows['pullback'].update(
            refinement.get('pullback_score', 0),
            f"In Pullback: {_bool_icon(refinement.get('in_pullback'))} | Delta Ratio: {ratio_str}"
        )

        # Rejection indicators
        self._rej_rows['struct_div'].update(
            refinement.get('struct_div_score', 0),
            f"HTF Aligned: {_bool_icon(refinement.get('htf_aligned'))} | "
            f"LTF Divergent: {_bool_icon(refinement.get('ltf_divergent'))}"
        )

        self._rej_rows['sma_exhst'].update(
            refinement.get('sma_exhst_score', 0),
            f"Contracting: {_bool_icon(refinement.get('sma_spread_contracting'))} | "
            f"Very Tight: {_bool_icon(refinement.get('sma_spread_very_tight'))} | "
            f"Tight: {_bool_icon(refinement.get('sma_spread_tight'))}"
        )

        abs_ratio = refinement.get('absorption_ratio')
        abs_str = f"{abs_ratio:.2f}" if abs_ratio is not None else "-"
        self._rej_rows['delta_abs'].update(
            refinement.get('delta_abs_score', 0),
            f"Absorption Ratio: {abs_str}"
        )

        self._rej_rows['vol_climax'].update(
            refinement.get('vol_climax_score', 0),
            f"Vol ROC Q5 (>50%): {_bool_icon(refinement.get('vol_roc_q5'))} | "
            f"Declining: {_bool_icon(refinement.get('vol_declining'))}"
        )

        cvd_slope = refinement.get('cvd_slope')
        slope_str = f"{cvd_slope:.6f}" if cvd_slope is not None else "-"
        cvd_norm = refinement.get('cvd_slope_normalized')
        norm_str = f"{cvd_norm:.4f}" if cvd_norm is not None else "-"
        self._rej_rows['cvd_extr'].update(
            refinement.get('cvd_extr_score', 0),
            f"CVD Slope: {slope_str} (Norm: {norm_str}) | "
            f"Extreme: {_bool_icon(refinement.get('cvd_extreme'))}"
        )

        # Generate prompt text
        if trade:
            self._prompt_text.setPlainText(_generate_monte_prompt(trade, refinement))

    def clear(self):
        """Reset panel."""
        self._type_label.setText("Trade Type: --")
        self._cont_score_label.setText("Continuation: --/10")
        self._rej_score_label.setText("Rejection: --/11")
        self._prompt_text.clear()
        self._toggle_btn.setChecked(False)


def _generate_monte_prompt(trade: TradeWithMetrics, refinement: Dict[str, Any]) -> str:
    """Generate Monte AI analysis prompt."""
    trade_type = refinement.get('trade_type', 'UNKNOWN')
    model = refinement.get('model', 'N/A')
    direction = refinement.get('direction', 'N/A')
    cont_score = refinement.get('continuation_score', 0)
    cont_label = refinement.get('continuation_label', 'UNKNOWN')
    rej_score = refinement.get('rejection_score', 0)
    rej_label = refinement.get('rejection_label', 'UNKNOWN')

    cont_details = f"""
CONTINUATION INDICATORS (Score: {cont_score}/10 - {cont_label}):
- CONT-01 MTF Alignment: {refinement.get('mtf_align_score', 'N/A')}/4
  H4: {'Aligned' if refinement.get('mtf_h4_aligned') else 'Not Aligned'}
  H1: {'Aligned' if refinement.get('mtf_h1_aligned') else 'Not Aligned'}
  M15: {'Aligned' if refinement.get('mtf_m15_aligned') else 'Not Aligned'}
  M5: {'Aligned' if refinement.get('mtf_m5_aligned') else 'Not Aligned'}
- CONT-02 SMA Momentum: {refinement.get('sma_mom_score', 'N/A')}/2
  Spread: {refinement.get('sma_spread', 'N/A')}, ROC: {refinement.get('sma_spread_roc', 'N/A')}%
- CONT-03 Volume Thrust: {refinement.get('vol_thrust_score', 'N/A')}/2
  Vol ROC: {refinement.get('vol_roc', 'N/A')}%, Delta 5-bar: {refinement.get('vol_delta_5', 'N/A')}
- CONT-04 Pullback Quality: {refinement.get('pullback_score', 'N/A')}/2
  In Pullback: {refinement.get('in_pullback', 'N/A')}, Delta Ratio: {refinement.get('pullback_delta_ratio', 'N/A')}
"""

    rej_details = f"""
REJECTION INDICATORS (Score: {rej_score}/11 - {rej_label}):
- REJ-01 Structure Divergence: {refinement.get('struct_div_score', 'N/A')}/2
  HTF Aligned: {refinement.get('htf_aligned', 'N/A')}, LTF Divergent: {refinement.get('ltf_divergent', 'N/A')}
- REJ-02 SMA Exhaustion: {refinement.get('sma_exhst_score', 'N/A')}/3
  Contracting: {refinement.get('sma_spread_contracting', 'N/A')}, Very Tight: {refinement.get('sma_spread_very_tight', 'N/A')}
- REJ-03 Delta Absorption: {refinement.get('delta_abs_score', 'N/A')}/2
  Absorption Ratio: {refinement.get('absorption_ratio', 'N/A')}
- REJ-04 Volume Climax: {refinement.get('vol_climax_score', 'N/A')}/2
  Vol ROC Q5: {refinement.get('vol_roc_q5', 'N/A')}, Declining: {refinement.get('vol_declining', 'N/A')}
- REJ-05 CVD Extreme: {refinement.get('cvd_extr_score', 'N/A')}/2
  CVD Slope: {refinement.get('cvd_slope', 'N/A')}, Extreme: {refinement.get('cvd_extreme', 'N/A')}
"""

    is_cont = trade_type == 'CONTINUATION'
    primary_score = cont_score if is_cont else rej_score
    primary_label = cont_label if is_cont else rej_label
    style = 'with-trend' if is_cont else 'counter-trend/exhaustion'

    entry_str = f"${trade.entry_price:.2f}" if trade.entry_price else "N/A"

    return f"""EPOCH INDICATOR REFINEMENT ANALYSIS

Trade: {trade.trade_id}
Date: {trade.date}
Ticker: {trade.ticker}
Model: {model}
Direction: {direction}
Trade Type: {trade_type}
Entry Price: {entry_str}

{cont_details}
{rej_details}

ANALYSIS REQUEST:
1. Score Interpretation: Is the {'continuation' if is_cont else 'rejection'} score of {primary_score} appropriate for this {style} trade?
2. Key Strengths: Which indicators contributed most positively?
3. Key Weaknesses: Which indicators suggest caution?
4. Trade Qualification: Based on the label ({primary_label}), would you have taken this trade?
5. Learning Points: What can be learned from this indicator configuration?
"""

"""
Notion page content generators — one function per section.

Each function returns a string of Notion-flavored Markdown for one section
of the per-trade journal page. The page_builder.py orchestrator concatenates
all 10 sections into the final page content.

Formatting helpers replicate the logic from components/rampup_chart.py
(lines 223-278) but produce text for markdown tables instead of Plotly.
"""

from typing import Dict, List, Optional
from decimal import Decimal
from .config import (
    ABSORPTION_THRESHOLD,
    NORMAL_THRESHOLD,
    VOL_ROC_ELEVATED,
    SMA_WIDE_SPREAD,
    CVD_RISING,
    CVD_FALLING,
    get_health_label,
)


# =============================================================================
# VALUE FORMATTING HELPERS
# =============================================================================

def _to_float(val) -> Optional[float]:
    """Safely convert a value to float."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _to_int(val) -> Optional[int]:
    """Safely convert a value to int."""
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def fmt_price(val) -> str:
    """Format as $XXX.XX or N/A."""
    f = _to_float(val)
    return f"${f:.2f}" if f is not None else "N/A"


def fmt_r(val) -> str:
    """Format as +X.XXR or N/A."""
    f = _to_float(val)
    return f"{f:+.2f}R" if f is not None else "N/A"


def fmt_time(val) -> str:
    """Format time as HH:MM ET or N/A."""
    if val is None:
        return "N/A"
    s = str(val)
    return f"{s[:5]} ET" if len(s) >= 5 else f"{s} ET"


def fmt_pct(val, decimals: int = 2) -> str:
    """Format as X.XX% or N/A."""
    f = _to_float(val)
    return f"{f:.{decimals}f}%" if f is not None else "N/A"


def fmt_int(val) -> str:
    """Format as integer or N/A."""
    i = _to_int(val)
    return str(i) if i is not None else "N/A"


def fmt_vol_delta(val) -> str:
    """Format volume delta with K/M suffixes. Matches rampup_chart.py."""
    f = _to_float(val)
    if f is None:
        return "—"
    prefix = '+' if f > 0 else ''
    abs_val = abs(f)
    if abs_val >= 1_000_000:
        return f"{prefix}{f/1_000_000:.1f}M"
    elif abs_val >= 1_000:
        return f"{prefix}{f/1_000:.0f}K"
    return f"{prefix}{f:.0f}"


def fmt_vol_roc(val) -> str:
    """Format volume ROC as +XX%."""
    f = _to_float(val)
    if f is None:
        return "—"
    prefix = '+' if f > 0 else ''
    return f"{prefix}{f:.0f}%"


def fmt_sma_config(sma_spread, close) -> str:
    """Format SMA config as B0.18% or S0.12%. Matches rampup_chart.py."""
    spread = _to_float(sma_spread)
    close_f = _to_float(close)
    if spread is None or close_f is None or close_f == 0:
        return "—"
    config = 'B' if spread > 0 else 'S'
    spread_pct = abs(spread) / close_f * 100
    return f"{config}{spread_pct:.2f}%"


def fmt_structure(val) -> str:
    """Format structure label: BULL/BEAR/NEUT or N/A."""
    if val is None:
        return "N/A"
    s = str(val).upper()
    if 'BULL' in s:
        return "BULL"
    elif 'BEAR' in s:
        return "BEAR"
    elif 'NEUT' in s:
        return "NEUT"
    return s[:6]


# =============================================================================
# SIGNAL CLASSIFICATION HELPERS
# =============================================================================

def _candle_signal(cr_pct) -> str:
    """Classify candle range % into signal emoji + label."""
    f = _to_float(cr_pct)
    if f is None:
        return "— N/A"
    if f >= NORMAL_THRESHOLD:
        return "NORMAL"
    elif f >= ABSORPTION_THRESHOLD:
        return "LOW"
    else:
        return "ABSORPTION"


def _vol_delta_signal(vol_delta, direction: str) -> str:
    """Classify volume delta alignment."""
    f = _to_float(vol_delta)
    if f is None:
        return "— N/A"
    if direction == 'LONG':
        return "Aligned" if f > 0 else "Misaligned"
    else:
        return "Aligned" if f < 0 else "Misaligned"


def _vol_roc_signal(vol_roc) -> str:
    """Classify volume ROC level."""
    f = _to_float(vol_roc)
    if f is None:
        return "— N/A"
    if f >= VOL_ROC_ELEVATED:
        return "Elevated"
    elif f >= 0:
        return "Normal"
    else:
        return "Low"


def _sma_spread_signal(sma_spread, close) -> str:
    """Classify SMA spread width."""
    spread = _to_float(sma_spread)
    close_f = _to_float(close)
    if spread is None or close_f is None or close_f == 0:
        return "— N/A"
    spread_pct = abs(spread) / close_f * 100
    return "Wide" if spread_pct >= SMA_WIDE_SPREAD else "Narrow"


def _h1_signal(h1_structure) -> str:
    """Classify H1 structure for edge."""
    if h1_structure is None:
        return "— N/A"
    s = str(h1_structure).upper()
    if 'NEUT' in s:
        return "NEUTRAL (Edge)"
    return s


def _cvd_signal(cvd_slope, direction: str) -> str:
    """Classify CVD slope alignment."""
    f = _to_float(cvd_slope)
    if f is None:
        return "— N/A"
    if direction == 'LONG':
        return "Aligned" if f > CVD_RISING else "Misaligned"
    else:
        return "Aligned" if f < CVD_FALLING else "Misaligned"


def _vwap_signal(vwap, close, direction: str) -> str:
    """Classify VWAP position alignment."""
    vwap_f = _to_float(vwap)
    close_f = _to_float(close)
    if vwap_f is None or close_f is None:
        return "— N/A"
    if direction == 'LONG':
        return "Aligned" if close_f > vwap_f else "Misaligned"
    else:
        return "Aligned" if close_f < vwap_f else "Misaligned"


# =============================================================================
# SECTION 1: TRADE SUMMARY
# =============================================================================

def section_trade_summary(trade: Dict) -> str:
    """Section 1: Trade Summary + Tags. Always shown."""
    symbol = trade.get('symbol', 'N/A')
    trade_date = str(trade.get('trade_date', 'N/A'))
    direction = trade.get('direction', 'N/A')
    model = trade.get('model') or 'Not Set'
    account = trade.get('account') or ''
    outcome = trade.get('outcome', 'N/A')
    pnl_dollars = trade.get('pnl_dollars')
    pnl_r = trade.get('pnl_r')
    duration = trade.get('duration_seconds')

    pnl_d_str = f"{float(pnl_dollars):+.2f} pts" if pnl_dollars is not None else "N/A"
    pnl_r_str = fmt_r(pnl_r)
    dur_str = f"{int(duration) // 60}m {int(duration) % 60}s" if duration else "N/A"
    acct_str = f" | {account}" if account else ""

    return f"""# Trade Summary

**{symbol}** | {trade_date} | {model} | {direction}{acct_str}

| Field | Value |
|-------|-------|
| Entry Price | {fmt_price(trade.get('entry_price'))} |
| Entry Time | {fmt_time(trade.get('entry_time'))} |
| Exit Price | {fmt_price(trade.get('exit_price'))} |
| Exit Time | {fmt_time(trade.get('exit_time'))} |
| Duration | {dur_str} |
| **Outcome** | **{outcome}** |
| **P&L** | **{pnl_r_str}** ({pnl_d_str}) |

> Add tags above in database properties to group this trade with similar setups. Use tags like "Clean Entry", "H1 Neutral Edge", "Pattern Example" etc.

---"""


# =============================================================================
# SECTION 2: RISK MANAGEMENT
# =============================================================================

def section_risk_management(trade: Dict, r_events: List[Dict]) -> str:
    """Section 2: Risk Management. Requires stop_price."""
    stop_price = trade.get('stop_price')
    if stop_price is None:
        return """# Risk Management

> This section will be populated after trade review. Set **stop_price** in the Streamlit review page.

---"""

    entry_price = float(trade.get('entry_price', 0))
    stop_p = float(stop_price)
    direction = trade.get('direction', '').upper()
    stop_distance = abs(entry_price - stop_p)

    # Calculate R-level prices
    if direction == 'LONG':
        r1 = entry_price + stop_distance
        r2 = entry_price + 2 * stop_distance
        r3 = entry_price + 3 * stop_distance
    else:
        r1 = entry_price - stop_distance
        r2 = entry_price - 2 * stop_distance
        r3 = entry_price - 3 * stop_distance

    # Check R-level hits from events
    def _r_hit(event_type):
        for e in r_events:
            if e.get('event_type') == event_type:
                return f"{fmt_time(e.get('time'))}"
        return None

    r1_hit = _r_hit('R1')
    r2_hit = _r_hit('R2')
    r3_hit = _r_hit('R3')

    r1_mark = f"Reached {r1_hit}" if r1_hit else "Not reached"
    r2_mark = f"Reached {r2_hit}" if r2_hit else "Not reached"
    r3_mark = f"Reached {r3_hit}" if r3_hit else "Not reached"

    stop_dist_pct = (stop_distance / entry_price * 100) if entry_price else 0

    # Minutes to R1
    min_to_r1 = "N/A"
    if r1_hit:
        entry_time = trade.get('entry_time')
        for e in r_events:
            if e.get('event_type') == 'R1' and entry_time and e.get('time'):
                try:
                    from datetime import datetime as dt, date as d_type
                    et = dt.combine(d_type.today(), entry_time)
                    rt = dt.combine(d_type.today(), e['time'])
                    mins = int((rt - et).total_seconds() / 60)
                    min_to_r1 = f"{mins} minutes"
                except Exception:
                    pass

    return f"""# Risk Management

| Level | Price | Notes |
|-------|-------|-------|
| Stop | {fmt_price(stop_p)} | Risk: {fmt_price(stop_distance)}/share ({stop_dist_pct:.2f}%) |
| Entry | {fmt_price(entry_price)} | — |
| 1R Target | {fmt_price(r1)} | {r1_mark} |
| 2R Target | {fmt_price(r2)} | {r2_mark} |
| 3R Target | {fmt_price(r3)} | {r3_mark} |

**Time to R1:** {min_to_r1}
**Stop Distance:** {stop_dist_pct:.2f}%

---"""


# =============================================================================
# SECTION 3: ZONE CONTEXT
# =============================================================================

def section_zone_context(zone: Optional[Dict], entry_bar: Optional[Dict]) -> str:
    """Section 3: Zone Context. Requires zone_id."""
    if zone is None:
        return """# Zone Context

> This section will be populated after trade review. Set **zone_id** in the Streamlit review page.

---"""

    # Market structure from entry bar (if available)
    structure_rows = ""
    if entry_bar:
        structure_rows = f"""
**Market Structure at Entry:**

| Timeframe | Direction |
|-----------|-----------|
| H4 | {fmt_structure(entry_bar.get('h4_structure'))} |
| H1 | {fmt_structure(entry_bar.get('h1_structure'))} |
| M15 | {fmt_structure(entry_bar.get('m15_structure'))} |
| M5 | {fmt_structure(entry_bar.get('m5_structure'))} |"""

    return f"""# Zone Context

| Field | Value |
|-------|-------|
| Zone ID | {zone.get('zone_id', 'N/A')} |
| Zone High | {fmt_price(zone.get('zone_high'))} |
| Zone POC | {fmt_price(zone.get('hvn_poc'))} |
| Zone Low | {fmt_price(zone.get('zone_low'))} |
| Zone Rank | {zone.get('rank', 'N/A')} |
| Zone Score | {zone.get('score', 'N/A')} |
| Setup Type | {zone.get('setup_type', 'N/A')} |
{structure_rows}

---"""


# =============================================================================
# SECTION 4: INDICATOR SNAPSHOT AT ENTRY
# =============================================================================

def section_indicator_snapshot(entry_bar: Optional[Dict], trade: Dict) -> str:
    """Section 4: Indicator Snapshot at Entry. Requires entry indicator bar."""
    if entry_bar is None:
        return """# Indicator Snapshot at Entry

> No M1 indicator data found at entry time. Run the M1 populator to generate indicator bars.

---"""

    direction = trade.get('direction', '').upper()
    close = entry_bar.get('close')
    cr_pct = entry_bar.get('candle_range_pct')
    vol_delta = entry_bar.get('vol_delta')
    vol_roc = entry_bar.get('vol_roc')
    sma_spread = entry_bar.get('sma_spread')
    h1 = entry_bar.get('h1_structure')
    cvd = entry_bar.get('cvd_slope')
    vwap = entry_bar.get('vwap')
    health = entry_bar.get('health_score')
    long_s = entry_bar.get('long_score')
    short_s = entry_bar.get('short_score')

    return f"""# Indicator Snapshot at Entry

| Indicator | Value | Signal |
|-----------|-------|--------|
| Candle Range % | {fmt_pct(cr_pct)} | {_candle_signal(cr_pct)} |
| Volume Delta | {fmt_vol_delta(vol_delta)} | {_vol_delta_signal(vol_delta, direction)} |
| Volume ROC | {fmt_vol_roc(vol_roc)} | {_vol_roc_signal(vol_roc)} |
| SMA Config | {fmt_sma_config(sma_spread, close)} | {_sma_spread_signal(sma_spread, close)} |
| H1 Structure | {fmt_structure(h1)} | {_h1_signal(h1)} |
| CVD Slope | {_to_float(cvd) if _to_float(cvd) is not None else 'N/A'} | {_cvd_signal(cvd, direction)} |
| VWAP Position | {fmt_price(vwap)} | {_vwap_signal(vwap, close, direction)} |
| **Health Score** | **{fmt_int(health)}/10** | **{get_health_label(health)}** |
| LONG Score | {fmt_int(long_s)}/7 | — |
| SHORT Score | {fmt_int(short_s)}/7 | — |

---"""


# =============================================================================
# SECTION 5: EXCURSION ANALYSIS
# =============================================================================

def section_excursion_analysis(mfe_mae: Optional[Dict], trade: Dict) -> str:
    """Section 5: Excursion Analysis. Requires MFE/MAE data (needs stop_price)."""
    if mfe_mae is None:
        return """# Excursion Analysis

> This section requires **stop_price** to calculate MFE/MAE in R-multiples. Set stop_price in the Streamlit review page.

---"""

    mfe_before = "Yes" if mfe_mae.get('mfe_before_mae') else "No"
    dur = mfe_mae.get('duration_minutes')
    dur_str = f"{dur} minutes" if dur is not None else "N/A"
    eff = mfe_mae.get('efficiency_pct')
    eff_str = f"{eff}%" if eff is not None else "N/A"

    return f"""# Excursion Analysis

| Metric | R-Multiple | Price | Time |
|--------|-----------|-------|------|
| MFE (Best) | +{mfe_mae.get('mfe_r', 0):.2f}R | {fmt_price(mfe_mae.get('mfe_price'))} | {fmt_time(mfe_mae.get('mfe_time'))} |
| MAE (Worst) | -{mfe_mae.get('mae_r', 0):.2f}R | {fmt_price(mfe_mae.get('mae_price'))} | {fmt_time(mfe_mae.get('mae_time'))} |

**MFE before MAE:** {mfe_before}
**Trade Duration:** {dur_str}
**Edge Efficiency:** {eff_str} (Actual R / MFE R x 100)

---"""


# =============================================================================
# SECTION 6: R-LEVEL PROGRESSION
# =============================================================================

def section_r_level_progression(r_events: List[Dict]) -> str:
    """Section 6: R-Level Progression. Requires r_events (needs stop_price)."""
    if not r_events:
        return """# R-Level Progression

> This section requires **stop_price** to calculate R-level crossings. Set stop_price in the Streamlit review page.

---"""

    rows = []
    for e in r_events:
        etype = e.get('event_type', '')
        t = fmt_time(e.get('time'))
        p = fmt_price(e.get('price'))
        r_mult = f"{e.get('r_multiple', 0):+.1f}R"
        health = e.get('health_score')
        h_str = f"{health}/10" if health is not None else "N/A"
        delta = e.get('health_delta')
        d_str = f"{delta:+d}" if delta is not None else "—"
        status = e.get('status', '—')
        rows.append(f"| {etype} | {t} | {p} | {r_mult} | {h_str} | {d_str} | {status} |")

    table_rows = "\n".join(rows)

    return f"""# R-Level Progression

| Event | Time | Price | R-Multiple | Health | Delta | Status |
|-------|------|-------|------------|--------|-------|--------|
{table_rows}

---"""


# =============================================================================
# SECTION 7: M1 RAMP-UP (15 bars before entry)
# =============================================================================

def section_m1_rampup(ramp_bars: List[Dict]) -> str:
    """Section 7: M1 Ramp-Up. Shows 15 M1 bars before entry with indicators."""
    if not ramp_bars:
        return """# M1 Ramp-Up (Before Entry)

> No M1 indicator bars found before entry. Run the M1 populator to generate indicator bars.

---"""

    rows = []
    count = len(ramp_bars)
    for i, bar in enumerate(ramp_bars):
        bar_num = -(count - i)  # -15, -14, ... -1
        t = str(bar.get('bar_time', ''))[:5]
        cr = _to_float(bar.get('candle_range_pct'))
        cr_str = f"{cr:.2f}%" if cr is not None else "—"
        # Flag absorption bars
        if cr is not None and cr < ABSORPTION_THRESHOLD:
            cr_str += " !"

        vd = fmt_vol_delta(bar.get('vol_delta'))
        vroc = fmt_vol_roc(bar.get('vol_roc'))
        sma = fmt_sma_config(bar.get('sma_spread'), bar.get('close'))
        h1 = fmt_structure(bar.get('h1_structure'))
        ls = fmt_int(bar.get('long_score'))
        ss = fmt_int(bar.get('short_score'))

        rows.append(f"| {bar_num} | {t} | {cr_str} | {vd} | {vroc} | {sma} | {h1} | {ls}/7 | {ss}/7 |")

    table_rows = "\n".join(rows)

    return f"""# M1 Ramp-Up (Before Entry)

| Bar | Time | Candle% | Vol Delta | VROC | SMA | H1 | LONG | SHORT |
|-----|------|---------|-----------|------|-----|-----|------|-------|
{table_rows}

> Bars marked with **!** are in the absorption zone (candle range < 0.12%).

---"""


# =============================================================================
# SECTION 8: INDICATOR REFINEMENT
# =============================================================================

def section_indicator_refinement(trade: Dict) -> str:
    """Section 8: Indicator Refinement. Placeholder until backtest data matching is implemented."""
    model = trade.get('model')
    if model is None:
        return """# Indicator Refinement

> This section will be populated after trade review. Set **model** in the Streamlit review page.

---"""

    # Determine trade type from model
    model_upper = str(model).upper()
    if model_upper in ('EPCH1', 'EPCH3'):
        trade_type = "CONTINUATION"
        score_table = """| Component | Score | Detail |
|-----------|-------|--------|
| CONT-01: MTF Alignment | —/4 | Pending backtest match |
| CONT-02: SMA Momentum | —/2 | Pending backtest match |
| CONT-03: Volume Thrust | —/2 | Pending backtest match |
| CONT-04: Pullback Quality | —/2 | Pending backtest match |
| **TOTAL** | **—/10** | **Pending** |"""
    else:
        trade_type = "REJECTION"
        score_table = """| Component | Score | Detail |
|-----------|-------|--------|
| REJ-01: Structure Divergence | —/2 | Pending backtest match |
| REJ-02: SMA Exhaustion | —/3 | Pending backtest match |
| REJ-03: Delta Absorption | —/2 | Pending backtest match |
| REJ-04: Volume Climax | —/2 | Pending backtest match |
| REJ-05: CVD Extreme | —/2 | Pending backtest match |
| **TOTAL** | **—/11** | **Pending** |"""

    return f"""# Indicator Refinement

**Trade Type:** {trade_type}
**Model:** {model}

{score_table}

> Refinement scores will be populated when backtest trade matching is implemented. This links journal trades to backtest secondary processor data.

---"""


# =============================================================================
# SECTION 9: CHARTS (Manual Paste)
# =============================================================================

def section_charts() -> str:
    """Section 9: Charts. Static callout placeholders for manual screenshots."""
    return """# Charts

> **M5 Execution Chart**
> Paste your TradingView M5 screenshot here showing entry, exit, and R-levels.

> **M15 Structure Chart**
> Paste your TradingView M15 screenshot here showing zone context.

> **H1 Context Chart**
> Paste your TradingView H1 screenshot here showing macro structure.

> **Footprint / Bookmap** *(Optional)*
> Paste Bookmap or footprint screenshot here.

---"""


# =============================================================================
# SECTION 10: TRADE ASSESSMENT (from flashcard review)
# =============================================================================

def section_trade_assessment(review: Optional[Dict] = None) -> str:
    """Section 10: Trade Assessment. Shows flashcard review checkboxes and assessment."""
    if review is None:
        return """# Trade Assessment

> This section will be populated after completing the flashcard review in the Streamlit training app.

---"""

    # Good/Bad trade
    good_trade = review.get('good_trade', False)
    assessment = "GOOD TRADE" if good_trade else "BAD TRADE"

    # Actual outcome
    actual_outcome = review.get('actual_outcome', 'N/A')
    outcome_str = actual_outcome.upper() if actual_outcome else 'N/A'

    # Helper for boolean display
    def _check(val):
        return "Yes" if val else "No"

    # Accuracy
    accuracy = _check(review.get('accuracy', False))
    tape_confirm = _check(review.get('tape_confirmation', False))

    # Signal
    signal_aligned = _check(review.get('signal_aligned', False))
    confirmation_req = _check(review.get('confirmation_required', False))

    # Stop placement
    prior_candle = _check(review.get('prior_candle_stop', False))
    two_candle = _check(review.get('two_candle_stop', False))
    atr_stop = _check(review.get('atr_stop', False))
    zone_edge = _check(review.get('zone_edge_stop', False))

    # Context
    with_trend = _check(review.get('with_trend', False))
    counter_trend = _check(review.get('counter_trend', False))
    stopped_wick = _check(review.get('stopped_by_wick', False))

    # Entry attempt
    attempt = review.get('entry_attempt')
    attempt_str = "N/A"
    if attempt == 1:
        attempt_str = "1st"
    elif attempt == 2:
        attempt_str = "2nd"
    elif attempt == 3:
        attempt_str = "3rd"

    return f"""# Trade Assessment

**{assessment}** | Outcome: {outcome_str}

| Category | Check | Value |
|----------|-------|-------|
| **Accuracy** | Accuracy | {accuracy} |
| | Tape Confirmation | {tape_confirm} |
| **Signal** | Signal Aligned | {signal_aligned} |
| | Confirmation Required | {confirmation_req} |
| **Stop Placement** | Prior Candle | {prior_candle} |
| | Two Candle | {two_candle} |
| | ATR Stop | {atr_stop} |
| | Zone Edge | {zone_edge} |
| **Context** | With Trend | {with_trend} |
| | Counter Trend | {counter_trend} |
| | Stopped by Wick | {stopped_wick} |
| **Entry** | Entry Attempt | {attempt_str} |

---"""


# =============================================================================
# SECTION 11: JOURNAL NOTES (from flashcard review)
# =============================================================================

def section_journal_notes(review: Optional[Dict] = None) -> str:
    """Section 11: Journal Notes. Populated from flashcard review if available."""
    if review is None:
        return """# Journal Notes

> What did I learn from this trade?
> *(Complete the flashcard review to populate this section)*

> What would I do differently?
> *(Complete the flashcard review to populate this section)*

> Pattern recognition notes
> *(Complete the flashcard review to populate this section)*

> Additional observations
> *(Complete the flashcard review to populate this section)*"""

    notes = review.get('notes', '') or ''
    notes_diff = review.get('notes_differently', '') or ''
    notes_pattern = review.get('notes_pattern', '') or ''
    notes_obs = review.get('notes_observations', '') or ''

    # Use actual content or placeholder
    notes_str = notes if notes.strip() else "*(No notes recorded)*"
    diff_str = notes_diff if notes_diff.strip() else "*(No notes recorded)*"
    pattern_str = notes_pattern if notes_pattern.strip() else "*(No notes recorded)*"
    obs_str = notes_obs if notes_obs.strip() else "*(No notes recorded)*"

    return f"""# Journal Notes

> **What did I learn from this trade?**
> {notes_str}

> **What would I do differently?**
> {diff_str}

> **Pattern recognition notes**
> {pattern_str}

> **Additional observations**
> {obs_str}"""

"""
DOW AI Prompt Generator - Creates copy-paste prompts for Claude Desktop.

Generates structured prompts for:
1. Pre-trade entry evaluation
2. Post-trade review (exit signal analysis and refinement)
"""

from datetime import date, datetime, time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.trade import TradeWithMetrics, Zone
from config import DB_CONFIG


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

PRE_TRADE_PROMPT_TEMPLATE = """You are DOW, an AI trading assistant for the Epoch Trading System.

══════════════════════════════════════════════════════════════════════════════
                         PRE-TRADE ENTRY ANALYSIS
══════════════════════════════════════════════════════════════════════════════

TRADE CONTEXT:
- Ticker: {ticker}
- Date: {trade_date}
- Direction: {direction}
- Model: {model}
- Zone Type: {zone_type}
- Entry Price: ${entry_price:.2f}
- Entry Time: {entry_time}

ZONE DATA:
- Zone Range: ${zone_low:.2f} - ${zone_high:.2f}
- Zone POC: ${zone_poc:.2f}
- Zone Rank: {zone_rank}
- Zone Tier: {zone_tier}
- Zone Score: {zone_score}

STOP & TARGETS:
- Stop Price: ${stop_price:.2f}
- Risk per Share: ${risk:.2f}
- Target (3R): ${target_3r}
- Target (Calc): ${target_calc}
- Target Used: ${target_used}

MODEL CLASSIFICATION:
- Code: {model}
- Type: {trade_type}
- Logic: {model_logic}

══════════════════════════════════════════════════════════════════════════════
                         MARKET STRUCTURE AT ENTRY
══════════════════════════════════════════════════════════════════════════════

{structure_section}

══════════════════════════════════════════════════════════════════════════════
                         INDICATOR SNAPSHOT AT ENTRY
══════════════════════════════════════════════════════════════════════════════

{indicators_section}

══════════════════════════════════════════════════════════════════════════════
                         M1 RAMP-UP (Bars Before Entry)
══════════════════════════════════════════════════════════════════════════════

{rampup_section}

══════════════════════════════════════════════════════════════════════════════
                         SUPPORTING LEVELS
══════════════════════════════════════════════════════════════════════════════

{levels_section}

══════════════════════════════════════════════════════════════════════════════
                         ANALYSIS REQUEST
══════════════════════════════════════════════════════════════════════════════

Please analyze this {direction} entry and provide:

1. **ENTRY QUALITY ASSESSMENT**
   - Does the market structure across M5/M15/H1/H4 support this {direction} trade?
   - Is the entry health score ({entry_health}/10) acceptable?
   - Are the SMAs aligned with the trade direction?

2. **ZONE INTERACTION**
   - Is price respecting the zone POC (${zone_poc:.2f})?
   - Is the entry positioned well within the zone?

3. **CONFIRMATION SIGNALS**
   - What additional confirmation would strengthen this entry?
   - What would invalidate this setup?

4. **KEY INSIGHTS**
   - Are there any red flags that suggest this trade should be avoided?
   - What patterns should inform future entries?

Provide a confidence rating: HIGH / MEDIUM / LOW with reasoning.
"""


POST_TRADE_PROMPT_TEMPLATE = """You are DOW, an AI trading assistant for the Epoch Trading System.

══════════════════════════════════════════════════════════════════════════════
                         POST-TRADE REVIEW ANALYSIS
══════════════════════════════════════════════════════════════════════════════

TRADE SUMMARY:
- Ticker: {ticker}
- Date: {trade_date}
- Direction: {direction}
- Model: {model}
- Outcome: {outcome} ({pnl_r:+.2f}R / {pnl_points:+.2f} pts)

EXECUTION:
- Entry: ${entry_price:.2f} at {entry_time}
- Exit: ${exit_price:.2f} at {exit_time}
- Exit Reason: {exit_reason}
- Duration: {duration}

RISK MANAGEMENT (Stop = Zone + 5% Buffer):
- Stop Price: ${stop_price:.2f}
- Risk per Share: ${risk_per_share:.2f}
- 1R Target: ${r1_price:.2f}
- 2R Target: ${r2_price:.2f}
- 3R Target: ${r3_price:.2f}

PERFORMANCE METRICS (R-Multiple Based):
- P&L: {pnl_r:+.2f}R ({pnl_points:+.2f} pts)
- MFE: +{mfe_r:.2f}R (+{mfe_points:.2f} pts) at bar {mfe_bars} ({mfe_time})
- MAE: {mae_r:.2f}R ({mae_points:.2f} pts) at bar {mae_bars} ({mae_time})
- Edge Efficiency: {edge_efficiency:.1f}%

R-LEVEL CROSSINGS:
{r_level_crossings_section}

ZONE CONTEXT:
- Zone Range: ${zone_low:.2f} - ${zone_high:.2f}
- Zone POC: ${zone_poc:.2f}

══════════════════════════════════════════════════════════════════════════════
                         INDICATOR COMPARISON (Entry → Exit)
══════════════════════════════════════════════════════════════════════════════

{event_comparison_section}

══════════════════════════════════════════════════════════════════════════════
                         SUPPORTING LEVELS
══════════════════════════════════════════════════════════════════════════════

{levels_section}

══════════════════════════════════════════════════════════════════════════════
                         REVIEW ANALYSIS REQUEST
══════════════════════════════════════════════════════════════════════════════

Please analyze this completed trade and provide insights on:

1. **ENTRY QUALITY REVIEW**
   - Was this a good trade to enter based on the available data?
   - Entry Health: {entry_health}/10 → Exit Health: {exit_health}/10
   - What signals at entry indicated this would be a {outcome}?

2. **R-LEVEL PROGRESSION ANALYSIS**
   - Did the trade reach 1R? 2R? 3R? At what health scores?
   - R-Level Progression: {r_level_summary}
   - What indicators supported/opposed continuation at each R-level?

3. **EXIT TIMING ANALYSIS**
   - MFE reached +{mfe_r:.2f}R (+{mfe_points:.2f} pts) but exited at {pnl_r:+.2f}R ({pnl_points:+.2f} pts)
   - Edge Efficiency: {edge_efficiency:.1f}% (captured {pnl_r:+.2f}R of {mfe_r:.2f}R available)
   - What indicators at MFE ({mfe_time}) suggested profit-taking?
   - Were there exit signals before the actual exit that were missed?

4. **STRUCTURE DEGRADATION**
   - Compare structure at ENTRY vs EXIT: Did the trend persist or reverse?
   - At what point did structure suggest the trade was weakening?
   - Health progression: Entry {entry_health} → MAE {mae_health} → MFE {mfe_health} → Exit {exit_health}

5. **REFINEMENT SUGGESTIONS**
   - What exit rules would have improved this trade's outcome?
   - Should partial exits be taken at specific R-levels based on health?
   - What indicator thresholds should be added to the algorithm?

6. **PATTERN RECOGNITION**
   - What makes this trade pattern recognizable for future reference?
   - Key lesson: [One sentence summary]

Provide specific, actionable refinements for the trading algorithm.
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_model_logic(model: str, direction: str) -> tuple:
    """
    Determine trade type and logic based on model.

    Returns:
        (trade_type, model_logic, flow_expectation)
    """
    model_upper = (model or 'EPCH1').upper()
    direction_upper = (direction or 'LONG').upper()

    if model_upper in ['EPCH1', 'EPCH3']:
        # Continuation trades
        trade_type = 'CONTINUATION'
        if direction_upper == 'LONG':
            model_logic = "Trading WITH bullish zone direction"
            flow_expectation = "buying pressure (positive delta, ask absorption)"
        else:
            model_logic = "Trading WITH bearish zone direction"
            flow_expectation = "selling pressure (negative delta, bid absorption)"
    else:
        # Reversal trades (EPCH2, EPCH4)
        trade_type = 'REVERSAL'
        if direction_upper == 'LONG':
            model_logic = "Trading AGAINST bearish zone for mean reversion"
            flow_expectation = "exhaustion of sellers (delta shift, absorption)"
        else:
            model_logic = "Trading AGAINST bullish zone for mean reversion"
            flow_expectation = "exhaustion of buyers (delta shift, absorption)"

    return trade_type, model_logic, flow_expectation


def _format_structure_section(events: Dict[str, Dict], direction: str) -> str:
    """Format market structure table from entry events."""
    if not events or 'ENTRY' not in events:
        return "Market structure data not available."

    entry = events['ENTRY']

    lines = [
        "Timeframe    Structure    Aligned?",
        "─────────────────────────────────────",
    ]

    direction_upper = (direction or 'LONG').upper()

    for tf in ['M5', 'M15', 'H1', 'H4']:
        key = f'{tf.lower()}_structure'
        structure = entry.get(key, '-')
        if structure:
            if direction_upper == 'LONG':
                aligned = '✓' if structure.upper() == 'BULL' else '✗' if structure.upper() == 'BEAR' else '~'
            else:
                aligned = '✓' if structure.upper() == 'BEAR' else '✗' if structure.upper() == 'BULL' else '~'
            lines.append(f"{tf:<12} {structure:<12} {aligned}")
        else:
            lines.append(f"{tf:<12} {'N/A':<12} -")

    return "\n".join(lines)


def _format_indicators_section(events: Dict[str, Dict]) -> str:
    """Format indicator snapshot from entry events."""
    if not events or 'ENTRY' not in events:
        return "Indicator data not available."

    entry = events['ENTRY']

    lines = []

    # VWAP
    vwap = entry.get('vwap')
    if vwap:
        lines.append(f"VWAP: ${float(vwap):.2f}")

    # SMAs
    sma9 = entry.get('sma9')
    sma21 = entry.get('sma21')
    sma_spread = entry.get('sma_spread')
    sma_momentum = entry.get('sma_momentum', '-')
    if sma9 and sma21:
        lines.append(f"SMA9: ${float(sma9):.2f} | SMA21: ${float(sma21):.2f}")
        if sma_spread:
            lines.append(f"SMA Spread: {float(sma_spread):.2f} ({sma_momentum})")

    # Volume
    vol_roc = entry.get('vol_roc')
    vol_delta = entry.get('vol_delta')
    if vol_roc is not None:
        lines.append(f"Volume ROC: {float(vol_roc):+.1f}%")
    if vol_delta is not None:
        lines.append(f"Volume Delta: {int(vol_delta):+,}")

    # Health
    health = entry.get('health_score')
    if health is not None:
        lines.append(f"Entry Health Score: {health}/10")

    return "\n".join(lines) if lines else "Indicator data not available."


def _format_event_comparison(events: Dict[str, Dict], direction: str) -> str:
    """Format comparison table of all events (v2.2.0 - includes R-level crossings)."""
    if not events:
        return "Event data not available."

    # Build column headers dynamically based on available events
    event_order = ['ENTRY']
    if 'R1_CROSS' in events:
        event_order.append('R1_CROSS')
    if 'R2_CROSS' in events:
        event_order.append('R2_CROSS')
    if 'R3_CROSS' in events:
        event_order.append('R3_CROSS')
    event_order.extend(['MAE', 'MFE', 'EXIT'])

    # Column labels
    col_labels = {
        'ENTRY': 'Entry',
        'R1_CROSS': '1R',
        'R2_CROSS': '2R',
        'R3_CROSS': '3R',
        'MAE': 'MAE',
        'MFE': 'MFE',
        'EXIT': 'Exit'
    }

    # Build header
    header_parts = ["Metric         "]
    separator_parts = ["───────────────"]
    for evt in event_order:
        header_parts.append(f" │ {col_labels[evt]:<8}")
        separator_parts.append("┼──────────")

    lines = [
        "".join(header_parts),
        "".join(separator_parts),
    ]

    def get_val(event_type: str, key: str, fmt: str = 's') -> str:
        if event_type not in events:
            return '-'
        val = events[event_type].get(key)
        if val is None:
            return '-'
        if fmt == 'price':
            return f"${float(val):.2f}"
        elif fmt == 'pts':
            return f"{float(val):+.2f}"
        elif fmt == 'pct':
            return f"{float(val):+.1f}%"
        elif fmt == 'int':
            return f"{int(val):+,}"
        elif fmt == 'health':
            return f"{val}/10"
        elif fmt == 'time':
            if hasattr(val, 'strftime'):
                return val.strftime("%H:%M")
            return str(val)[:5]
        return str(val) if val else '-'

    # Add rows
    metrics = [
        ('Time', 'event_time', 'time'),
        ('Price', 'price_at_event', 'price'),
        ('Points', 'points_at_event', 'pts'),
        ('Health', 'health_score', 'health'),
        ('H Delta', 'health_delta', 'int'),
        ('VWAP', 'vwap', 'price'),
        ('SMA9', 'sma9', 'price'),
        ('SMA21', 'sma21', 'price'),
        ('SMA Mom', 'sma_momentum_label', 's'),
        ('Vol ROC', 'vol_roc', 'pct'),
        ('M5 Struct', 'm5_structure', 's'),
        ('M15 Struct', 'm15_structure', 's'),
        ('H1 Struct', 'h1_structure', 's'),
        ('H4 Struct', 'h4_structure', 's'),
    ]

    for label, key, fmt in metrics:
        row_parts = [f"{label:<15}"]
        for evt in event_order:
            val = get_val(evt, key, fmt)
            row_parts.append(f" │ {val:<8}")
        lines.append("".join(row_parts))

    return "\n".join(lines)


def _format_r_level_crossings_section(trade: 'TradeWithMetrics') -> str:
    """Format R-level crossings section for DOW AI post-trade prompt."""
    lines = []

    if trade.r1_crossed:
        r1_time = trade.r1_time.strftime("%H:%M") if trade.r1_time else "N/A"
        r1_health = f"H:{trade.r1_health}" if trade.r1_health is not None else ""
        r1_delta = ""
        if trade.r1_health_delta is not None:
            delta_sign = "+" if trade.r1_health_delta >= 0 else ""
            r1_delta = f" ({delta_sign}{trade.r1_health_delta})"
        lines.append(f"- 1R Hit: {r1_time} at ${trade.r1_price:.2f} | {r1_health}{r1_delta}")
    else:
        lines.append("- 1R Hit: No")

    if trade.r2_crossed:
        r2_time = trade.r2_time.strftime("%H:%M") if trade.r2_time else "N/A"
        r2_health = f"H:{trade.r2_health}" if trade.r2_health is not None else ""
        r2_delta = ""
        if trade.r2_health_delta is not None:
            delta_sign = "+" if trade.r2_health_delta >= 0 else ""
            r2_delta = f" ({delta_sign}{trade.r2_health_delta})"
        lines.append(f"- 2R Hit: {r2_time} at ${trade.r2_price:.2f} | {r2_health}{r2_delta}")
    else:
        lines.append("- 2R Hit: No")

    if trade.r3_crossed:
        r3_time = trade.r3_time.strftime("%H:%M") if trade.r3_time else "N/A"
        r3_health = f"H:{trade.r3_health}" if trade.r3_health is not None else ""
        r3_delta = ""
        if trade.r3_health_delta is not None:
            delta_sign = "+" if trade.r3_health_delta >= 0 else ""
            r3_delta = f" ({delta_sign}{trade.r3_health_delta})"
        lines.append(f"- 3R Hit: {r3_time} at ${trade.r3_price:.2f} | {r3_health}{r3_delta}")
    else:
        lines.append("- 3R Hit: No")

    return "\n".join(lines)


def _get_r_level_summary(trade: 'TradeWithMetrics') -> str:
    """Get a summary string of R-level progression."""
    levels_hit = []
    if trade.r1_crossed:
        levels_hit.append("1R")
    if trade.r2_crossed:
        levels_hit.append("2R")
    if trade.r3_crossed:
        levels_hit.append("3R")

    if not levels_hit:
        return "No R-levels reached"

    return " → ".join(levels_hit)


def _fetch_m1_rampup_bars(ticker: str, trade_date: date, entry_time: time, num_bars: int = 15) -> List[Dict]:
    """
    Fetch M1 indicator bars from database for ramp-up display.

    Args:
        ticker: Stock symbol
        trade_date: Trading date
        entry_time: Entry time
        num_bars: Number of bars before entry to fetch

    Returns:
        List of bar dictionaries (oldest first)
    """
    query = """
        SELECT
            bar_time,
            open,
            high,
            low,
            close,
            volume,
            vwap,
            sma9,
            sma21,
            sma_spread,
            vol_delta,
            vol_roc,
            h1_structure,
            candle_range_pct,
            long_score,
            short_score
        FROM m1_indicator_bars
        WHERE ticker = %s
          AND bar_date = %s
          AND bar_time < %s
        ORDER BY bar_time DESC
        LIMIT %s
    """

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (ticker, trade_date, entry_time, num_bars))
            rows = cur.fetchall()
        conn.close()

        if not rows:
            return []

        # Reverse to get chronological order (oldest first)
        return [dict(row) for row in reversed(rows)]

    except Exception as e:
        print(f"Error fetching M1 ramp-up bars: {e}")
        return []


def _format_rampup_section(ticker: str, trade_date: date, entry_time: time) -> str:
    """Format M1 ramp-up bars for DOW AI prompt with full candle data and indicators."""
    bars = _fetch_m1_rampup_bars(ticker, trade_date, entry_time, num_bars=15)

    if not bars:
        return "M1 ramp-up data not available."

    lines = []

    # =========================================================================
    # SECTION 1: M1 CANDLE DATA (OHLCV)
    # =========================================================================
    lines.append("CANDLE DATA (15 M1 Bars Before Entry):")
    lines.append("Bar │ Time  │   Open   │   High   │    Low   │  Close   │ Change │  Volume")
    lines.append("────┼───────┼──────────┼──────────┼──────────┼──────────┼────────┼─────────")

    prev_close = None
    for i, bar in enumerate(bars, 1):
        bar_time = bar.get('bar_time')
        time_str = bar_time.strftime('%H:%M') if hasattr(bar_time, 'strftime') else str(bar_time)[:5]

        open_p = float(bar.get('open', 0))
        high_p = float(bar.get('high', 0))
        low_p = float(bar.get('low', 0))
        close_p = float(bar.get('close', 0))
        volume = bar.get('volume', 0)

        # Calculate bar change (close vs previous close)
        if prev_close is not None and prev_close != 0:
            change = ((close_p - prev_close) / prev_close) * 100
            change_str = f"{change:+.2f}%"
        else:
            change_str = "-"
        prev_close = close_p

        # Format volume (abbreviated)
        if volume >= 1000000:
            vol_str = f"{volume/1000000:.1f}M"
        elif volume >= 1000:
            vol_str = f"{volume/1000:.0f}K"
        else:
            vol_str = str(volume)

        # Candle type indicator
        candle_type = "▲" if close_p > open_p else "▼" if close_p < open_p else "─"

        lines.append(
            f"{i:>2}{candle_type} │ {time_str} │ {open_p:>8.2f} │ {high_p:>8.2f} │ {low_p:>8.2f} │ {close_p:>8.2f} │ {change_str:>6} │ {vol_str:>7}"
        )

    # Price range summary
    all_highs = [float(b.get('high', 0)) for b in bars]
    all_lows = [float(b.get('low', 0)) for b in bars]
    first_open = float(bars[0].get('open', 0)) if bars else 0
    last_close = float(bars[-1].get('close', 0)) if bars else 0

    lines.append("")
    lines.append(f"Range: ${min(all_lows):.2f} - ${max(all_highs):.2f} | Net Move: {((last_close - first_open) / first_open * 100) if first_open else 0:+.2f}%")

    # =========================================================================
    # SECTION 2: INDICATOR DATA
    # =========================================================================
    lines.append("")
    lines.append("INDICATOR DATA:")
    lines.append("Time  │ Cndl% │ VolDelta │ VolROC │ SMA  │ H1  │ LONG │ SHORT")
    lines.append("──────┼───────┼──────────┼────────┼──────┼─────┼──────┼──────")

    for bar in bars:
        bar_time = bar.get('bar_time')
        time_str = bar_time.strftime('%H:%M') if hasattr(bar_time, 'strftime') else str(bar_time)[:5]

        # Candle range %
        candle_pct = bar.get('candle_range_pct')
        candle_str = f"{float(candle_pct):.2f}" if candle_pct is not None else "-"

        # Volume delta (abbreviated)
        vol_delta = bar.get('vol_delta')
        if vol_delta is not None:
            vol_delta = float(vol_delta)
            if abs(vol_delta) >= 1000000:
                delta_str = f"{vol_delta/1000000:+.1f}M"
            elif abs(vol_delta) >= 1000:
                delta_str = f"{vol_delta/1000:+.0f}K"
            else:
                delta_str = f"{vol_delta:+.0f}"
        else:
            delta_str = "-"

        # Volume ROC
        vol_roc = bar.get('vol_roc')
        roc_str = f"{float(vol_roc):+.0f}%" if vol_roc is not None else "-"

        # SMA config (B=Bull, S=Bear + spread %)
        sma_spread = bar.get('sma_spread')
        close = bar.get('close')
        if sma_spread is not None and close is not None and float(close) > 0:
            config = 'B' if float(sma_spread) > 0 else 'S'
            spread_pct = abs(float(sma_spread)) / float(close) * 100
            sma_str = f"{config}{spread_pct:.2f}"
        else:
            sma_str = "-"

        # H1 Structure (using triangle symbols)
        h1_struct = bar.get('h1_structure')
        if h1_struct == 'BULL':
            h1_str = "▲"
        elif h1_struct == 'BEAR':
            h1_str = "▼"
        else:
            h1_str = "-"

        # LONG score (0-7)
        long_score = bar.get('long_score')
        long_str = str(int(long_score)) if long_score is not None else "-"

        # SHORT score (0-7)
        short_score = bar.get('short_score')
        short_str = str(int(short_score)) if short_score is not None else "-"

        lines.append(
            f"{time_str} │ {candle_str:>5} │ {delta_str:>8} │ {roc_str:>6} │ {sma_str:>4} │ {h1_str:>3} │ {long_str:>4} │ {short_str:>5}"
        )

    # =========================================================================
    # SECTION 3: PRICE ACTION SUMMARY
    # =========================================================================
    lines.append("")
    lines.append("PRICE ACTION ANALYSIS:")

    # Count bullish/bearish candles
    bullish_candles = sum(1 for b in bars if float(b.get('close', 0)) > float(b.get('open', 0)))
    bearish_candles = sum(1 for b in bars if float(b.get('close', 0)) < float(b.get('open', 0)))
    doji_candles = len(bars) - bullish_candles - bearish_candles

    lines.append(f"- Candle Types: {bullish_candles} bullish (▲), {bearish_candles} bearish (▼), {doji_candles} doji (─)")

    # Count consecutive candles at end
    if bars:
        last_type = "BULL" if float(bars[-1].get('close', 0)) > float(bars[-1].get('open', 0)) else "BEAR"
        consecutive = 1
        for i in range(len(bars) - 2, -1, -1):
            bar_type = "BULL" if float(bars[i].get('close', 0)) > float(bars[i].get('open', 0)) else "BEAR"
            if bar_type == last_type:
                consecutive += 1
            else:
                break
        lines.append(f"- Final Momentum: {consecutive} consecutive {last_type} candles")

    # SMA position at end
    if bars:
        last_bar = bars[-1]
        last_close = float(last_bar.get('close', 0))
        sma9 = float(last_bar.get('sma9', 0)) if last_bar.get('sma9') else None
        sma21 = float(last_bar.get('sma21', 0)) if last_bar.get('sma21') else None
        vwap = float(last_bar.get('vwap', 0)) if last_bar.get('vwap') else None

        if sma9 and sma21:
            sma_relation = "SMA9 > SMA21 (bullish)" if sma9 > sma21 else "SMA9 < SMA21 (bearish)"
            price_vs_sma = "above" if last_close > sma9 else "below"
            lines.append(f"- SMA Config: {sma_relation}, Price {price_vs_sma} SMA9")

        if vwap:
            vwap_position = "above" if last_close > vwap else "below"
            lines.append(f"- VWAP: ${vwap:.2f}, Price {vwap_position} VWAP")

    # H1 Structure summary
    h1_bull = sum(1 for b in bars if b.get('h1_structure') == 'BULL')
    h1_bear = sum(1 for b in bars if b.get('h1_structure') == 'BEAR')
    h1_neut = len(bars) - h1_bull - h1_bear
    lines.append(f"- H1 Structure: {h1_bull} BULL / {h1_bear} BEAR / {h1_neut} NEUTRAL")

    # Average scores
    long_scores = [b.get('long_score') for b in bars if b.get('long_score') is not None]
    short_scores = [b.get('short_score') for b in bars if b.get('short_score') is not None]
    avg_long = sum(long_scores) / len(long_scores) if long_scores else 0
    avg_short = sum(short_scores) / len(short_scores) if short_scores else 0

    # Score trend (last 5 vs first 5)
    if len(long_scores) >= 10:
        first_5_long = sum(long_scores[:5]) / 5
        last_5_long = sum(long_scores[-5:]) / 5
        long_trend = "improving" if last_5_long > first_5_long else "degrading" if last_5_long < first_5_long else "stable"
    else:
        long_trend = "N/A"

    if len(short_scores) >= 10:
        first_5_short = sum(short_scores[:5]) / 5
        last_5_short = sum(short_scores[-5:]) / 5
        short_trend = "improving" if last_5_short > first_5_short else "degrading" if last_5_short < first_5_short else "stable"
    else:
        short_trend = "N/A"

    lines.append(f"- Avg LONG Score: {avg_long:.1f}/7 (trend: {long_trend})")
    lines.append(f"- Avg SHORT Score: {avg_short:.1f}/7 (trend: {short_trend})")

    # Candle range quality
    good_candles = sum(1 for b in bars if b.get('candle_range_pct') is not None and float(b.get('candle_range_pct')) >= 0.15)
    lines.append(f"- Candle Quality: {good_candles}/{len(bars)} bars with range >= 0.15% (tradeable)")

    return "\n".join(lines)


def _format_levels_section(context: Dict[str, Any]) -> str:
    """Format supporting levels section."""
    lines = []

    bar_data = context.get('bar_data')
    hvn_pocs = context.get('hvn_pocs')
    market_structure = context.get('market_structure')

    # ATR
    if bar_data and bar_data.d1_atr:
        lines.append(f"D1 ATR: ${bar_data.d1_atr:.2f}")
        if bar_data.m5_atr:
            lines.append(f"M5 ATR: ${bar_data.m5_atr:.2f}")

    # Camarilla
    if bar_data and bar_data.d1_cam_s3:
        lines.append("")
        lines.append("DAILY CAMARILLA:")
        lines.append(f"  R6: ${bar_data.d1_cam_r6:.2f}" if bar_data.d1_cam_r6 else "  R6: N/A")
        lines.append(f"  R4: ${bar_data.d1_cam_r4:.2f}" if bar_data.d1_cam_r4 else "  R4: N/A")
        lines.append(f"  R3: ${bar_data.d1_cam_r3:.2f}" if bar_data.d1_cam_r3 else "  R3: N/A")
        lines.append(f"  S3: ${bar_data.d1_cam_s3:.2f}" if bar_data.d1_cam_s3 else "  S3: N/A")
        lines.append(f"  S4: ${bar_data.d1_cam_s4:.2f}" if bar_data.d1_cam_s4 else "  S4: N/A")
        lines.append(f"  S6: ${bar_data.d1_cam_s6:.2f}" if bar_data.d1_cam_s6 else "  S6: N/A")

    # HVN POCs
    if hvn_pocs and hvn_pocs.pocs:
        lines.append("")
        lines.append("HVN POC LEVELS (Top 5):")
        for i, poc in enumerate(hvn_pocs.pocs[:5], 1):
            lines.append(f"  POC {i}: ${poc:.2f}")

    # Market Structure Levels
    if market_structure:
        lines.append("")
        lines.append("STRUCTURE LEVELS:")
        if market_structure.h4_strong:
            lines.append(f"  H4 Strong (Invalidation): ${market_structure.h4_strong:.2f}")
        if market_structure.h4_weak:
            lines.append(f"  H4 Weak (Target): ${market_structure.h4_weak:.2f}")
        if market_structure.h1_strong:
            lines.append(f"  H1 Strong: ${market_structure.h1_strong:.2f}")
        if market_structure.h1_weak:
            lines.append(f"  H1 Weak: ${market_structure.h1_weak:.2f}")

    # Options levels
    if bar_data and bar_data.options_levels:
        lines.append("")
        lines.append("OPTIONS LEVELS:")
        for i, level in enumerate(bar_data.options_levels[:5], 1):
            lines.append(f"  OP{i}: ${level:.2f}")

    if not lines:
        return "Supporting level data not available."

    return "\n".join(lines)


# =============================================================================
# MAIN GENERATOR FUNCTIONS
# =============================================================================

def generate_pre_trade_prompt(
    trade: TradeWithMetrics,
    events: Dict[str, Dict],
    context: Dict[str, Any]
) -> str:
    """
    Generate pre-trade analysis prompt for Claude Desktop.

    Args:
        trade: TradeWithMetrics object
        events: Dict of optimal_trade events (ENTRY, MFE, MAE, EXIT)
        context: Dict with bar_data, hvn_pocs, market_structure, setup

    Returns:
        Formatted prompt string ready for copy-paste
    """
    # Extract trade info
    ticker = trade.ticker
    trade_date = trade.date.strftime("%Y-%m-%d") if trade.date else "N/A"
    direction = trade.direction or "LONG"
    model = trade.model or "EPCH1"
    zone_type = trade.zone_type or "PRIMARY"

    # Entry info
    entry_price = trade.entry_price or 0
    entry_time = trade.entry_time.strftime("%H:%M:%S") if trade.entry_time else "N/A"

    # Zone info
    zone_high = trade.zone_high or 0
    zone_low = trade.zone_low or 0
    zone_poc = trade.trade.zone_mid or ((zone_high + zone_low) / 2 if zone_high and zone_low else 0)
    zone_rank = trade.zone_rank or "N/A"
    zone_tier = trade.zone_tier or "N/A"
    zone_score = f"{trade.zone_score:.1f}" if trade.zone_score else "N/A"

    # Stop and targets
    stop_price = trade.trade.stop_price or 0
    risk = trade.trade.risk or abs(entry_price - stop_price)
    target_3r = f"${trade.trade.target_3r:.2f}" if trade.trade.target_3r else "N/A"
    target_calc = f"${trade.trade.target_calc:.2f}" if trade.trade.target_calc else "N/A"
    target_used = f"${trade.trade.target_used:.2f}" if trade.trade.target_used else "N/A"

    # Model logic
    trade_type, model_logic, flow_expectation = _get_model_logic(model, direction)

    # Health
    entry_health = trade.entry_health if trade.entry_health is not None else "N/A"

    # Format sections
    structure_section = _format_structure_section(events, direction)
    indicators_section = _format_indicators_section(events)
    levels_section = _format_levels_section(context)

    # Format M1 ramp-up section
    rampup_section = _format_rampup_section(ticker, trade.date, trade.entry_time) if trade.entry_time else "M1 ramp-up data not available."

    return PRE_TRADE_PROMPT_TEMPLATE.format(
        ticker=ticker,
        trade_date=trade_date,
        direction=direction,
        model=model,
        zone_type=zone_type,
        entry_price=entry_price,
        entry_time=entry_time,
        zone_low=zone_low,
        zone_high=zone_high,
        zone_poc=zone_poc,
        zone_rank=zone_rank,
        zone_tier=zone_tier,
        zone_score=zone_score,
        stop_price=stop_price,
        risk=risk,
        target_3r=target_3r,
        target_calc=target_calc,
        target_used=target_used,
        trade_type=trade_type,
        model_logic=model_logic,
        structure_section=structure_section,
        indicators_section=indicators_section,
        rampup_section=rampup_section,
        levels_section=levels_section,
        entry_health=entry_health,
    )


def generate_post_trade_prompt(
    trade: TradeWithMetrics,
    events: Dict[str, Dict],
    context: Dict[str, Any]
) -> str:
    """
    Generate post-trade review prompt for Claude Desktop.

    Args:
        trade: TradeWithMetrics object
        events: Dict of optimal_trade events (ENTRY, MFE, MAE, EXIT, R1_CROSS, R2_CROSS, R3_CROSS)
        context: Dict with bar_data, hvn_pocs, market_structure, setup

    Returns:
        Formatted prompt string ready for copy-paste
    """
    # Extract trade info
    ticker = trade.ticker
    trade_date = trade.date.strftime("%Y-%m-%d") if trade.date else "N/A"
    direction = trade.direction or "LONG"
    model = trade.model or "EPCH1"

    # Use R-multiple based outcome (aligned with System Analysis)
    outcome = trade.outcome_r or ("WINNER" if trade.is_winner else "LOSER")

    # Execution
    entry_price = float(trade.entry_price or 0)
    exit_price = float(trade.exit_price or 0)
    entry_time = trade.entry_time.strftime("%H:%M:%S") if trade.entry_time else "N/A"
    exit_time = trade.exit_time.strftime("%H:%M:%S") if trade.exit_time else "N/A"
    exit_reason = trade.exit_reason or "N/A"

    # Duration
    duration_mins = trade.duration_minutes
    if duration_mins:
        if duration_mins >= 60:
            duration = f"{duration_mins // 60}h {duration_mins % 60}m"
        else:
            duration = f"{duration_mins}m"
    else:
        duration = "N/A"

    # R-multiple based metrics
    stop_price = float(trade.default_stop_price or 0)
    risk_per_share = float(trade.risk_per_share or 0)
    r1_price = float(trade.r1_price or 0)
    r2_price = float(trade.r2_price or 0)
    r3_price = float(trade.r3_price or 0)

    # P&L in R-multiples and points
    pnl_r = float(trade.pnl_r or 0)
    pnl_points = float(trade.pnl_points or 0)

    # MFE/MAE in R-multiples and points
    mfe_r = float(trade.mfe_r or 0)
    mfe_points = float(trade.mfe_points or 0)
    mfe_bars = trade.mfe_bars or 0
    mfe_time = trade.mfe_time.strftime("%H:%M") if trade.mfe_time else "N/A"

    mae_r = float(trade.mae_r or 0)
    mae_points = float(trade.mae_points or 0)
    mae_bars = trade.mae_bars or 0
    mae_time = trade.mae_time.strftime("%H:%M") if trade.mae_time else "N/A"

    # Edge efficiency (R-based)
    edge_efficiency = (pnl_r / mfe_r * 100) if mfe_r and mfe_r > 0 else 0

    # Zone info
    zone_high = float(trade.zone_high or 0)
    zone_low = float(trade.zone_low or 0)
    zone_poc = float(trade.trade.zone_mid or ((zone_high + zone_low) / 2 if zone_high and zone_low else 0))

    # Health scores
    entry_health = trade.entry_health if trade.entry_health is not None else "N/A"
    mae_health = trade.mae_health if trade.mae_health is not None else "N/A"
    mfe_health = trade.mfe_health if trade.mfe_health is not None else "N/A"
    exit_health = trade.exit_health if trade.exit_health is not None else "N/A"

    # Format sections
    event_comparison_section = _format_event_comparison(events, direction)
    levels_section = _format_levels_section(context)
    r_level_crossings_section = _format_r_level_crossings_section(trade)
    r_level_summary = _get_r_level_summary(trade)

    return POST_TRADE_PROMPT_TEMPLATE.format(
        ticker=ticker,
        trade_date=trade_date,
        direction=direction,
        model=model,
        outcome=outcome,
        pnl_r=pnl_r,
        pnl_points=pnl_points,
        entry_price=entry_price,
        exit_price=exit_price,
        entry_time=entry_time,
        exit_time=exit_time,
        exit_reason=exit_reason,
        duration=duration,
        stop_price=stop_price,
        risk_per_share=risk_per_share,
        r1_price=r1_price,
        r2_price=r2_price,
        r3_price=r3_price,
        mfe_r=mfe_r,
        mfe_points=mfe_points,
        mfe_bars=mfe_bars,
        mfe_time=mfe_time,
        mae_r=mae_r,
        mae_points=mae_points,
        mae_bars=mae_bars,
        mae_time=mae_time,
        edge_efficiency=edge_efficiency,
        zone_low=zone_low,
        zone_high=zone_high,
        zone_poc=zone_poc,
        entry_health=entry_health,
        mae_health=mae_health,
        mfe_health=mfe_health,
        exit_health=exit_health,
        event_comparison_section=event_comparison_section,
        levels_section=levels_section,
        r_level_crossings_section=r_level_crossings_section,
        r_level_summary=r_level_summary,
    )

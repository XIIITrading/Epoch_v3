"""
Market Structure Fractal Visualizer
====================================
GROW-3 Prototype — 5-Candle Williams Fractal with BOS/ChoCH

Renders a candlestick chart with:
- Fractal markers (green circle = bullish/long, red circle = bearish/short)
- Break labels (x = CHoCH, o = BOS)
- Strong level (solid line) and Weak level (dotted line)

Usage:
    python app.py SPY D1           # Daily SPY
    python app.py AAPL W1          # Weekly AAPL
    python app.py QQQ H4           # 4-hour QQQ
    python app.py SPY D1 --lookback 500
"""

import sys
import argparse
from pathlib import Path
from datetime import date, timedelta

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ---------------------------------------------------------------------------
# Shared infrastructure (installed as editable: pip install -e 00_shared)
# ---------------------------------------------------------------------------
from shared.data.polygon import PolygonClient
from shared.indicators.structure import detect_fractals
from shared.charts.colors import EPOCH_DARK

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FRACTAL_P = 2  # Bars each side — classic 5-candle Williams fractal

LOOKBACK_DEFAULTS = {
    "W1": 730, "D1": 365, "H4": 120, "H1": 60, "M15": 20,
    "w1": 730, "d1": 365, "h4": 120, "h1": 60, "m15": 20,
}

COLORS = {
    "bg": EPOCH_DARK["background"],
    "candle_up": EPOCH_DARK["candle_up"],
    "candle_down": EPOCH_DARK["candle_down"],
    "bull": EPOCH_DARK["bull"],
    "bear": EPOCH_DARK["bear"],
    "text": EPOCH_DARK["text"],
    "text_muted": EPOCH_DARK["text_muted"],
    "grid": EPOCH_DARK["grid"],
}


# =========================================================================
# DATA FETCHING
# =========================================================================

def fetch_data(ticker: str, timeframe: str, lookback_days: int = None) -> pd.DataFrame:
    """Fetch OHLCV data from Polygon.io."""
    lookback = lookback_days or LOOKBACK_DEFAULTS.get(timeframe.upper(), 365)
    end = date.today()
    start = end - timedelta(days=lookback)

    client = PolygonClient()
    df = client.get_bars(ticker.upper(), timeframe, start, end)
    client.close()

    if df.empty:
        print(f"No data returned for {ticker} {timeframe}")
        sys.exit(1)

    # Filter outlier bars before any calculations (bad Polygon data)
    median_close = df["close"].median()
    lo, hi = median_close * 0.7, median_close * 1.3
    mask = (
        (df["open"] > lo) & (df["open"] < hi) &
        (df["high"] > lo) & (df["high"] < hi) &
        (df["low"] > lo) & (df["low"] < hi) &
        (df["close"] > lo) & (df["close"] < hi)
    )
    if mask.sum() < len(df):
        bad_count = (~mask).sum()
        print(f"  Filtered {bad_count} outlier bar(s) from raw data")
        df = df[mask].reset_index(drop=True)

    print(f"Fetched {len(df)} bars for {ticker} {timeframe} ({start} to {end})")
    return df


# =========================================================================
# FRACTAL DETECTION (5-candle Williams)
# =========================================================================

def detect_williams_fractals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect 5-candle Williams fractals (2 bars each side).

    Adds columns: bearish_fractal, bullish_fractal
    - bearish_fractal = local high (fractal high) — short signal
    - bullish_fractal = local low (fractal low) — long signal
    """
    p = FRACTAL_P
    n = len(df)
    bearish = np.zeros(n, dtype=bool)
    bullish = np.zeros(n, dtype=bool)

    if n >= 2 * p + 1:
        for i in range(p, n - p):
            # Bearish fractal (local high)
            if all(df["high"].iloc[i] > df["high"].iloc[i - j] for j in range(1, p + 1)) and \
               all(df["high"].iloc[i] > df["high"].iloc[i + j] for j in range(1, p + 1)):
                bearish[i] = True

            # Bullish fractal (local low)
            if all(df["low"].iloc[i] < df["low"].iloc[i - j] for j in range(1, p + 1)) and \
               all(df["low"].iloc[i] < df["low"].iloc[i + j] for j in range(1, p + 1)):
                bullish[i] = True

    df = df.copy()
    df["bearish_fractal"] = bearish
    df["bullish_fractal"] = bullish
    return df


# =========================================================================
# BOS / ChoCH STATE MACHINE
# =========================================================================

def calculate_structure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the BOS/ChoCH state machine on fractal data.

    Ported from 01_application/calculators/market_structure.py.

    Adds columns:
        upper_fractal_value, lower_fractal_value,
        structure (1=bull, -1=bear, 0=neutral),
        structure_label ('BOS', 'ChoCH', or ''),
        bull_continuation_high, bear_continuation_low
    """
    df = df.copy()
    n = len(df)

    df["upper_fractal_value"] = np.nan
    df["lower_fractal_value"] = np.nan
    df["structure"] = 0
    df["structure_label"] = ""
    df["bull_continuation_high"] = np.nan
    df["bear_continuation_low"] = np.nan
    # Track the anchor bar index and price for each break (for drawing lines)
    df["break_anchor_bar"] = -1
    df["break_anchor_price"] = np.nan

    upper_value = None
    upper_crossed = False
    upper_bar = -1
    lower_value = None
    lower_crossed = False
    lower_bar = -1
    current_structure = 0
    bull_cont_high = None
    bear_cont_low = None

    for i in range(n):
        close = df["close"].iloc[i]
        high = df["high"].iloc[i]
        low = df["low"].iloc[i]

        # New fractal resets crossed flag
        if df["bearish_fractal"].iloc[i]:
            upper_value = high
            upper_crossed = False
            upper_bar = i
        if df["bullish_fractal"].iloc[i]:
            lower_value = low
            lower_crossed = False
            lower_bar = i

        df.iloc[i, df.columns.get_loc("upper_fractal_value")] = upper_value
        df.iloc[i, df.columns.get_loc("lower_fractal_value")] = lower_value

        # Bullish break: close > upper fractal
        if upper_value is not None and not upper_crossed:
            if close > upper_value:
                label = "ChoCH" if current_structure == -1 else "BOS"
                df.iloc[i, df.columns.get_loc("structure_label")] = label
                df.iloc[i, df.columns.get_loc("break_anchor_bar")] = upper_bar
                df.iloc[i, df.columns.get_loc("break_anchor_price")] = upper_value
                current_structure = 1
                upper_crossed = True
                bull_cont_high = high

        # Bearish break: close < lower fractal
        if lower_value is not None and not lower_crossed:
            if close < lower_value:
                label = "ChoCH" if current_structure == 1 else "BOS"
                df.iloc[i, df.columns.get_loc("structure_label")] = label
                df.iloc[i, df.columns.get_loc("break_anchor_bar")] = lower_bar
                df.iloc[i, df.columns.get_loc("break_anchor_price")] = lower_value
                current_structure = -1
                lower_crossed = True
                bear_cont_low = low

        # Track continuation levels
        if current_structure == 1:
            if bull_cont_high is None or high > bull_cont_high:
                bull_cont_high = high
        elif current_structure == -1:
            if bear_cont_low is None or low < bear_cont_low:
                bear_cont_low = low

        df.iloc[i, df.columns.get_loc("structure")] = current_structure
        df.iloc[i, df.columns.get_loc("bull_continuation_high")] = bull_cont_high
        df.iloc[i, df.columns.get_loc("bear_continuation_low")] = bear_cont_low

    return df


# =========================================================================
# CHART RENDERER
# =========================================================================

def render_chart(df: pd.DataFrame, ticker: str, timeframe: str,
                 num_fractals: int = 5, save_path: str = None):
    """
    Render candlestick chart with fractal markers, BOS/ChoCH labels,
    and strong/weak level lines.
    """
    # Limit to visible bars (last portion for readability)
    max_bars = min(len(df), 120)
    df_vis = df.iloc[-max_bars:].copy().reset_index(drop=True)


    fig, ax = plt.subplots(figsize=(16, 9), facecolor=COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])

    # ----- Candlesticks -----
    body_width = 0.6
    for i, (_, bar) in enumerate(df_vis.iterrows()):
        o, h, l, c = bar["open"], bar["high"], bar["low"], bar["close"]
        color = COLORS["candle_up"] if c >= o else COLORS["candle_down"]

        # Wick
        ax.plot([i, i], [l, h], color=color, linewidth=0.8, zorder=2)
        # Body
        body_bottom = min(o, c)
        body_height = abs(c - o) or (h - l) * 0.01  # tiny body for dojis
        rect = mpatches.Rectangle(
            (i - body_width / 2, body_bottom), body_width, body_height,
            facecolor=color, edgecolor=color, linewidth=0.5, zorder=3,
        )
        ax.add_patch(rect)

    # ----- Pixel offset in price units -----
    price_range = df_vis["high"].max() - df_vis["low"].min()
    px_offset = price_range * 0.012  # ~10px visual offset from candle

    # ----- Fractal markers (last N of each type) -----
    bearish_idxs = df_vis.index[df_vis["bearish_fractal"]].tolist()
    bullish_idxs = df_vis.index[df_vis["bullish_fractal"]].tolist()

    recent_bearish = bearish_idxs[-num_fractals:]
    recent_bullish = bullish_idxs[-num_fractals:]

    for idx in recent_bearish:
        ax.plot(
            idx, df_vis.at[idx, "high"] + px_offset,
            marker="o", color=COLORS["bear"], markersize=5,
            markeredgecolor=COLORS["bear"], markerfacecolor=COLORS["bear"],
            zorder=5, alpha=0.9,
        )

    for idx in recent_bullish:
        ax.plot(
            idx, df_vis.at[idx, "low"] - px_offset,
            marker="o", color=COLORS["bull"], markersize=5,
            markeredgecolor=COLORS["bull"], markerfacecolor=COLORS["bull"],
            zorder=5, alpha=0.9,
        )

    # ----- BOS / ChoCH lines and markers -----
    # First visible bar's original df index (for anchor bar remapping)
    vis_start = len(df) - len(df_vis)

    for i, (_, bar) in enumerate(df_vis.iterrows()):
        label = bar["structure_label"]
        if not label:
            continue

        structure = bar["structure"]
        anchor_bar_abs = int(bar["break_anchor_bar"])
        anchor_price = bar["break_anchor_price"]
        # Remap absolute bar index to visible index
        anchor_bar_vis = anchor_bar_abs - vis_start

        # Draw horizontal line from anchor fractal to break bar
        if pd.notna(anchor_price) and anchor_bar_vis >= 0:
            line_style = ":" if label == "ChoCH" else "-"
            ax.plot(
                [anchor_bar_vis, i], [anchor_price, anchor_price],
                color="white", linestyle=line_style, linewidth=1.0,
                alpha=0.7, zorder=4,
            )
            # Label centered above the line
            mid_x = (anchor_bar_vis + i) / 2
            ax.annotate(
                label.upper() if label == "ChoCH" else label,
                (mid_x, anchor_price), textcoords="offset points",
                xytext=(0, 8), ha="center", fontsize=6, fontweight="bold",
                color="white", alpha=0.8, zorder=7,
            )

        # Marker at the break candle, offset from the high/low
        clr = COLORS["bull"] if structure == 1 else COLORS["bear"]
        if structure == 1:
            marker_y = df_vis.at[i, "low"] - px_offset
        else:
            marker_y = df_vis.at[i, "high"] + px_offset

        if label == "ChoCH":
            ax.plot(
                i, marker_y, marker="x", color=clr, markersize=5,
                markeredgewidth=1.5, zorder=6,
            )
        elif label == "BOS":
            ax.plot(
                i, marker_y, marker="o", color=clr, markersize=5,
                markeredgewidth=1.2, markerfacecolor="none", zorder=6,
            )

    # ----- Strong / Weak level lines -----
    last_row = df_vis.iloc[-1]
    current_structure = int(last_row["structure"])

    if current_structure == 1:  # Bull
        strong_level = last_row["lower_fractal_value"]
        weak_level = last_row["bull_continuation_high"]
        line_color = COLORS["bull"]
        strong_label = "Strong (Support)"
        weak_label = "Weak (Target)"
    elif current_structure == -1:  # Bear
        strong_level = last_row["upper_fractal_value"]
        weak_level = last_row["bear_continuation_low"]
        line_color = COLORS["bear"]
        strong_label = "Strong (Resistance)"
        weak_label = "Weak (Target)"
    else:
        strong_level = None
        weak_level = None
        line_color = COLORS["text_muted"]
        strong_label = ""
        weak_label = ""

    x_max = len(df_vis)

    if strong_level is not None and pd.notna(strong_level):
        ax.axhline(
            strong_level, color=line_color, linestyle="-", linewidth=1.5,
            alpha=0.8, zorder=4,
        )
        ax.text(
            x_max + 0.5, strong_level,
            f"  {strong_label}: ${strong_level:.2f}",
            color=line_color, fontsize=8, va="center", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor=COLORS["bg"],
                      edgecolor=line_color, alpha=0.85),
            zorder=8,
        )

    if weak_level is not None and pd.notna(weak_level):
        ax.axhline(
            weak_level, color=line_color, linestyle=":", linewidth=1.5,
            alpha=0.6, zorder=4,
        )
        ax.text(
            x_max + 0.5, weak_level,
            f"  {weak_label}: ${weak_level:.2f}",
            color=line_color, fontsize=8, va="center",
            bbox=dict(boxstyle="round,pad=0.2", facecolor=COLORS["bg"],
                      edgecolor=line_color, alpha=0.85),
            zorder=8,
        )

    # ----- Axis styling -----
    ax.set_xlim(-1, x_max + 12)
    price_min = df_vis["low"].min()
    price_max = df_vis["high"].max()
    padding = (price_max - price_min) * 0.04
    ax.set_ylim(price_min - padding, price_max + padding)

    ax.tick_params(colors=COLORS["text_muted"], labelsize=8)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:.2f}"))
    ax.grid(True, alpha=0.15, color=COLORS["grid"], linewidth=0.5)

    # X-axis: show dates at intervals
    n_ticks = min(12, len(df_vis))
    tick_step = max(1, len(df_vis) // n_ticks)
    tick_positions = list(range(0, len(df_vis), tick_step))
    tick_labels = []
    for pos in tick_positions:
        ts = df_vis.iloc[pos]["timestamp"]
        if hasattr(ts, "strftime"):
            if timeframe.upper() in ("W1", "D1"):
                tick_labels.append(ts.strftime("%b %d"))
            else:
                tick_labels.append(ts.strftime("%m/%d %H:%M"))
        else:
            tick_labels.append(str(pos))
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=7,
                       color=COLORS["text_muted"])

    for spine in ax.spines.values():
        spine.set_color(COLORS["grid"])

    # ----- Title -----
    structure_str = {1: "BULL", -1: "BEAR", 0: "NEUTRAL"}.get(current_structure, "?")
    structure_color = COLORS["bull"] if current_structure == 1 else (
        COLORS["bear"] if current_structure == -1 else COLORS["text_muted"]
    )

    fig.suptitle(
        f"{ticker.upper()} {timeframe.upper()} — Market Structure",
        color=COLORS["text"], fontsize=14, fontweight="bold", y=0.97,
    )
    ax.set_title(
        f"Direction: {structure_str}  |  Williams 5-Candle Fractals  |  "
        f"Showing last {num_fractals} fractals",
        color=structure_color, fontsize=10, pad=8,
    )

    # ----- Legend -----
    legend_elements = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS["bull"],
                   markersize=5, label="Bullish Fractal (Long)", linestyle="None"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS["bear"],
                   markersize=5, label="Bearish Fractal (Short)", linestyle="None"),
        plt.Line2D([0], [0], color="white", linewidth=1.0,
                   linestyle="-", label="BOS Line"),
        plt.Line2D([0], [0], color="white", linewidth=1.0,
                   linestyle=":", label="CHoCH Line"),
        plt.Line2D([0], [0], color=COLORS["text"], linewidth=1.5,
                   linestyle="-", label="Strong Level"),
        plt.Line2D([0], [0], color=COLORS["text"], linewidth=1.5,
                   linestyle=":", label="Weak Level"),
    ]
    ax.legend(
        handles=legend_elements, loc="upper left", fontsize=7,
        facecolor=COLORS["bg"], edgecolor=COLORS["grid"],
        labelcolor=COLORS["text"],
    )

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    if save_path:
        fig.savefig(save_path, dpi=150, facecolor=COLORS["bg"],
                    bbox_inches="tight")
        print(f"Chart saved to {save_path}")
        plt.close(fig)
    else:
        plt.show()


# =========================================================================
# MAIN
# =========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Market Structure Fractal Visualizer (GROW-3 Prototype)"
    )
    parser.add_argument("ticker", help="Stock ticker (e.g. SPY, AAPL, QQQ)")
    parser.add_argument(
        "timeframe", nargs="?", default="D1",
        help="Timeframe: W1, D1, H4, H1, M15 (default: D1)",
    )
    parser.add_argument(
        "--lookback", type=int, default=None,
        help="Lookback days (default: auto based on timeframe)",
    )
    parser.add_argument(
        "--fractals", type=int, default=5,
        help="Number of recent fractals to show (default: 5)",
    )
    parser.add_argument(
        "--save", type=str, default=None,
        help="Save chart to PNG file instead of displaying",
    )
    args = parser.parse_args()

    # 1. Fetch data
    print(f"Fetching {args.ticker.upper()} {args.timeframe.upper()} data...")
    df = fetch_data(args.ticker, args.timeframe, args.lookback)

    # 2. Detect fractals
    print("Detecting Williams fractals (5-candle)...")
    df = detect_williams_fractals(df)

    frac_high_count = df["bearish_fractal"].sum()
    frac_low_count = df["bullish_fractal"].sum()
    print(f"  Found {frac_high_count} fractal highs, {frac_low_count} fractal lows")

    # 3. Calculate structure (BOS/ChoCH)
    print("Calculating market structure (BOS/ChoCH)...")
    df = calculate_structure(df)

    bos_count = (df["structure_label"] == "BOS").sum()
    choch_count = (df["structure_label"] == "ChoCH").sum()
    print(f"  Found {bos_count} BOS, {choch_count} CHoCH breaks")

    current = int(df["structure"].iloc[-1])
    print(f"  Current structure: {['NEUTRAL', 'BULL'][current] if current >= 0 else 'BEAR'}")

    # 4. Render chart
    print("Rendering chart...")
    render_chart(df, args.ticker, args.timeframe, args.fractals, args.save)


if __name__ == "__main__":
    main()

"""
Test script to fetch 5 sample trades with entry indicators for DOW AI testing.
"""

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": "db.pdbmcskznoaiybdiobje.supabase.co",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "guid-saltation-covet",
    "sslmode": "require"
}

def fetch_test_trades(limit: int = 5):
    """Fetch trades with entry indicators - mix of winners and losers."""

    query = """
    SELECT
        t.trade_id,
        t.date,
        t.ticker,
        t.direction,
        t.model,
        t.zone_type,
        t.entry_price,
        t.entry_time,
        t.exit_price,
        t.pnl_r,
        t.is_winner,
        -- Entry indicators
        ei.health_score,
        ei.health_label,
        ei.structure_score,
        ei.volume_score,
        ei.price_score,
        ei.h4_structure,
        ei.h1_structure,
        ei.m15_structure,
        ei.m5_structure,
        ei.vol_roc,
        ei.vol_delta,
        ei.cvd_slope,
        ei.sma_alignment,
        ei.sma_momentum_label,
        ei.vwap_position,
        ei.h4_structure_healthy,
        ei.h1_structure_healthy,
        ei.m15_structure_healthy,
        ei.m5_structure_healthy,
        ei.vol_roc_healthy,
        ei.vol_delta_healthy,
        ei.cvd_slope_healthy,
        ei.sma_alignment_healthy,
        ei.sma_momentum_healthy,
        ei.vwap_healthy
    FROM trades t
    JOIN entry_indicators ei ON t.trade_id = ei.trade_id
    WHERE ei.health_score IS NOT NULL
    ORDER BY RANDOM()
    LIMIT %s
    """

    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (limit,))
        trades = [dict(row) for row in cur.fetchall()]
    conn.close()

    return trades


def fetch_m1_rampup(ticker: str, trade_date, entry_time, num_bars: int = 15):
    """Fetch M1 bars before entry for ramp-up display."""

    query = """
    SELECT
        bar_time,
        open, high, low, close, volume,
        candle_range_pct,
        vol_delta,
        vol_roc,
        sma_spread,
        h1_structure,
        long_score,
        short_score
    FROM m1_indicator_bars
    WHERE ticker = %s
      AND bar_date = %s
      AND bar_time < %s
    ORDER BY bar_time DESC
    LIMIT %s
    """

    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (ticker, trade_date, entry_time, num_bars))
        bars = [dict(row) for row in cur.fetchall()]
    conn.close()

    # Reverse to chronological order
    return list(reversed(bars))


def format_trade_for_display(trade: dict, m1_bars: list) -> str:
    """Format a trade and its indicators for display."""

    lines = []
    lines.append("=" * 70)
    lines.append(f"TRADE: {trade['trade_id']}")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"TICKER: {trade['ticker']} | DIRECTION: {trade['direction']}")
    lines.append(f"Date: {trade['date']} | Entry: {trade['entry_time']} @ ${float(trade['entry_price']):.2f}")
    lines.append(f"Model: {trade['model']} | Zone: {trade['zone_type']}")
    lines.append("")
    lines.append(f"ACTUAL OUTCOME: {'WIN' if trade['is_winner'] else 'LOSS'} ({float(trade['pnl_r'] or 0):+.2f}R)")
    lines.append("")
    lines.append("-" * 40)
    lines.append("ENTRY INDICATORS (from entry_indicators table):")
    lines.append("-" * 40)
    lines.append(f"Health Score: {trade['health_score']}/10 ({trade['health_label']})")
    lines.append(f"  Structure: {trade['structure_score']}/4 | Volume: {trade['volume_score']}/3 | Price: {trade['price_score']}/3")
    lines.append("")
    lines.append("Structure:")
    lines.append(f"  H4: {trade['h4_structure']} ({'Y' if trade['h4_structure_healthy'] else 'N'})")
    lines.append(f"  H1: {trade['h1_structure']} ({'Y' if trade['h1_structure_healthy'] else 'N'})")
    lines.append(f"  M15: {trade['m15_structure']} ({'Y' if trade['m15_structure_healthy'] else 'N'})")
    lines.append(f"  M5: {trade['m5_structure']} ({'Y' if trade['m5_structure_healthy'] else 'N'})")
    lines.append("")
    lines.append("Volume:")
    vol_roc = float(trade['vol_roc']) if trade['vol_roc'] else 0
    vol_delta = float(trade['vol_delta']) if trade['vol_delta'] else 0
    cvd_slope = float(trade['cvd_slope']) if trade['cvd_slope'] else 0
    lines.append(f"  Vol ROC: {vol_roc:+.1f}% ({'Y' if trade['vol_roc_healthy'] else 'N'})")
    lines.append(f"  Vol Delta: {vol_delta:+,.0f} ({'Y' if trade['vol_delta_healthy'] else 'N'})")
    lines.append(f"  CVD Slope: {cvd_slope:.4f} ({'Y' if trade['cvd_slope_healthy'] else 'N'})")
    lines.append("")
    lines.append("Price/SMA:")
    lines.append(f"  SMA Alignment: {trade['sma_alignment']} ({'Y' if trade['sma_alignment_healthy'] else 'N'})")
    lines.append(f"  SMA Momentum: {trade['sma_momentum_label']} ({'Y' if trade['sma_momentum_healthy'] else 'N'})")
    lines.append(f"  VWAP Position: {trade['vwap_position']} ({'Y' if trade['vwap_healthy'] else 'N'})")

    if m1_bars:
        lines.append("")
        lines.append("-" * 40)
        lines.append(f"M1 RAMP-UP ({len(m1_bars)} bars before entry):")
        lines.append("-" * 40)
        lines.append("Time  | Close    | Cndl%  | VolDelta | H1  | L/S")
        lines.append("-" * 50)
        for bar in m1_bars[-5:]:  # Show last 5 bars
            bar_time = bar['bar_time']
            time_str = bar_time.strftime('%H:%M') if hasattr(bar_time, 'strftime') else str(bar_time)[:5]
            close = float(bar['close'])
            candle_pct = float(bar['candle_range_pct'] or 0)
            vol_d = float(bar['vol_delta'] or 0)
            h1 = bar['h1_structure'] or '-'
            long_s = bar['long_score'] or 0
            short_s = bar['short_score'] or 0
            lines.append(f"{time_str} | ${close:>7.2f} | {candle_pct:>5.2f}% | {vol_d:>+8.0f} | {h1:>3} | {long_s}/{short_s}")

    return "\n".join(lines)


if __name__ == "__main__":
    print("Fetching 5 test trades...")
    trades = fetch_test_trades(5)

    for trade in trades:
        m1_bars = fetch_m1_rampup(
            trade['ticker'],
            trade['date'],
            trade['entry_time']
        )
        print(format_trade_for_display(trade, m1_bars))
        print("\n")

"""
Deep dive: Health Score STRONG (8-10) edge
Cross-tabulated by Direction, Zone Type, and Entry Model
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=RealDictCursor)

DATE_FILTER = "m.date >= CURRENT_DATE - INTERVAL '30 days'"

print("=" * 70)
print("  HEALTH SCORE STRONG (8-10) - DEEP DIVE")
print("  Period: Last 30 days | Source: trades_m5_r_win")
print("=" * 70)


# ---- Q1: By Direction ----
print()
print("  Q1: STRONG Health by Direction (LONG vs SHORT)")
print("  " + "-" * 60)

cur.execute(f"""
    SELECT
        m.direction,
        COUNT(*) as total,
        SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
        ROUND(SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
              / NULLIF(COUNT(*), 0) * 100, 1) as win_rate,
        ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r
    FROM trades_m5_r_win m
    LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
    WHERE ei.health_score >= 8 AND {DATE_FILTER}
    GROUP BY m.direction ORDER BY m.direction
""")
strong_dir = cur.fetchall()

cur.execute(f"""
    SELECT m.direction,
        COUNT(*) as total,
        ROUND(SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
              / NULLIF(COUNT(*), 0) * 100, 1) as baseline_wr
    FROM trades_m5_r_win m WHERE {DATE_FILTER}
    GROUP BY m.direction
""")
base_dir = {r["direction"]: r for r in cur.fetchall()}

header = f"  {'Direction':<10} {'Trades':>7} {'Wins':>6} {'WR':>8} {'Baseline':>10} {'Effect':>8} {'Avg R':>8}"
print(header)
print("  " + "-" * len(header.strip()))
for r in strong_dir:
    d = r["direction"]
    wr = float(r["win_rate"])
    bwr = float(base_dir.get(d, {}).get("baseline_wr", 0))
    effect = round(wr - bwr, 1)
    print(f"  {d:<10} {r['total']:>7} {r['wins']:>6} {wr:>7.1f}% {bwr:>9.1f}% {effect:>+7.1f}pp {float(r['avg_r']):>+7.3f}")


# ---- Q2: By Zone Type ----
print()
print("  Q2a: STRONG Health by Zone Type (Primary vs Secondary)")
print("  " + "-" * 60)

cur.execute(f"""
    SELECT
        m.zone_type,
        COUNT(*) as total,
        SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
        ROUND(SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
              / NULLIF(COUNT(*), 0) * 100, 1) as win_rate,
        ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r
    FROM trades_m5_r_win m
    LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
    WHERE ei.health_score >= 8 AND {DATE_FILTER}
    GROUP BY m.zone_type ORDER BY m.zone_type
""")
strong_zone = cur.fetchall()

cur.execute(f"""
    SELECT m.zone_type,
        ROUND(SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
              / NULLIF(COUNT(*), 0) * 100, 1) as baseline_wr
    FROM trades_m5_r_win m WHERE {DATE_FILTER}
    GROUP BY m.zone_type
""")
base_zone = {r["zone_type"]: float(r["baseline_wr"]) for r in cur.fetchall()}

header = f"  {'Zone Type':<12} {'Trades':>7} {'Wins':>6} {'WR':>8} {'Baseline':>10} {'Effect':>8} {'Avg R':>8}"
print(header)
print("  " + "-" * len(header.strip()))
for r in strong_zone:
    zt = r["zone_type"] or "NULL"
    wr = float(r["win_rate"])
    bwr = base_zone.get(r["zone_type"], 0)
    effect = round(wr - bwr, 1)
    print(f"  {zt:<12} {r['total']:>7} {r['wins']:>6} {wr:>7.1f}% {bwr:>9.1f}% {effect:>+7.1f}pp {float(r['avg_r']):>+7.3f}")


# ---- Q2b: By Stop Distance Bucket ----
print()
print("  Q2b: STRONG Health by Stop Distance (zone tightness)")
print("  " + "-" * 60)

cur.execute(f"""
    SELECT
        CASE
            WHEN m.stop_distance_pct < 0.12 THEN 'TIGHT (<0.12%%)'
            WHEN m.stop_distance_pct < 0.25 THEN 'NORMAL (0.12-0.25%%)'
            WHEN m.stop_distance_pct < 0.50 THEN 'WIDE (0.25-0.50%%)'
            ELSE 'VERY WIDE (>=0.50%%)'
        END as bucket,
        COUNT(*) as total,
        SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
        ROUND(SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
              / NULLIF(COUNT(*), 0) * 100, 1) as win_rate
    FROM trades_m5_r_win m
    LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
    WHERE ei.health_score >= 8 AND {DATE_FILTER}
    GROUP BY bucket ORDER BY bucket
""")
rows = cur.fetchall()

header = f"  {'Zone Size':<22} {'Trades':>7} {'Wins':>6} {'WR':>8}"
print(header)
print("  " + "-" * len(header.strip()))
for r in rows:
    print(f"  {r['bucket']:<22} {r['total']:>7} {r['wins']:>6} {float(r['win_rate']):>7.1f}%")


# ---- Q3: By Entry Model ----
print()
print("  Q3: STRONG Health by Entry Model")
print("  " + "-" * 60)

cur.execute(f"""
    SELECT
        m.model,
        CASE
            WHEN m.model IN ('EPCH1', 'EPCH3') THEN 'CONTINUATION'
            ELSE 'REJECTION'
        END as model_type,
        COUNT(*) as total,
        SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
        ROUND(SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
              / NULLIF(COUNT(*), 0) * 100, 1) as win_rate,
        ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r
    FROM trades_m5_r_win m
    LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
    WHERE ei.health_score >= 8 AND {DATE_FILTER}
    GROUP BY m.model, model_type ORDER BY m.model
""")
strong_model = cur.fetchall()

cur.execute(f"""
    SELECT m.model,
        ROUND(SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
              / NULLIF(COUNT(*), 0) * 100, 1) as baseline_wr
    FROM trades_m5_r_win m WHERE {DATE_FILTER}
    GROUP BY m.model
""")
base_model = {r["model"]: float(r["baseline_wr"]) for r in cur.fetchall()}

header = f"  {'Model':<8} {'Type':<14} {'Trades':>7} {'Wins':>6} {'WR':>8} {'Baseline':>10} {'Effect':>8} {'Avg R':>8}"
print(header)
print("  " + "-" * len(header.strip()))
for r in strong_model:
    m = r["model"]
    wr = float(r["win_rate"])
    bwr = base_model.get(m, 0)
    effect = round(wr - bwr, 1)
    print(f"  {m:<8} {r['model_type']:<14} {r['total']:>7} {r['wins']:>6} {wr:>7.1f}% {bwr:>9.1f}% {effect:>+7.1f}pp {float(r['avg_r']):>+7.3f}")


# Continuation vs Rejection summary
print()
print("  Grouped: Continuation vs Rejection")
print("  " + "-" * 60)

cur.execute(f"""
    SELECT
        CASE
            WHEN m.model IN ('EPCH1', 'EPCH3') THEN 'CONTINUATION'
            ELSE 'REJECTION'
        END as model_type,
        COUNT(*) as total,
        SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END) as wins,
        ROUND(SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
              / NULLIF(COUNT(*), 0) * 100, 1) as win_rate,
        ROUND(AVG(m.pnl_r)::numeric, 3) as avg_r
    FROM trades_m5_r_win m
    LEFT JOIN entry_indicators ei ON m.trade_id = ei.trade_id
    WHERE ei.health_score >= 8 AND {DATE_FILTER}
    GROUP BY model_type ORDER BY model_type
""")
rows = cur.fetchall()

cur.execute(f"""
    SELECT
        CASE
            WHEN m.model IN ('EPCH1', 'EPCH3') THEN 'CONTINUATION'
            ELSE 'REJECTION'
        END as model_type,
        ROUND(SUM(CASE WHEN m.is_winner THEN 1 ELSE 0 END)::numeric
              / NULLIF(COUNT(*), 0) * 100, 1) as baseline_wr
    FROM trades_m5_r_win m WHERE {DATE_FILTER}
    GROUP BY model_type
""")
base_mt = {r["model_type"]: float(r["baseline_wr"]) for r in cur.fetchall()}

header = f"  {'Type':<14} {'Trades':>7} {'Wins':>6} {'WR':>8} {'Baseline':>10} {'Effect':>8} {'Avg R':>8}"
print(header)
print("  " + "-" * len(header.strip()))
for r in rows:
    mt = r["model_type"]
    wr = float(r["win_rate"])
    bwr = base_mt.get(mt, 0)
    effect = round(wr - bwr, 1)
    print(f"  {mt:<14} {r['total']:>7} {r['wins']:>6} {wr:>7.1f}% {bwr:>9.1f}% {effect:>+7.1f}pp {float(r['avg_r']):>+7.3f}")

print()
print("=" * 70)
conn.close()

"""
Fix: Delete all j_m1_indicator_bars and downstream tables so the processor
pipeline can re-compute with corrected M5/M15 structure detection.

The M5/M15 structure was being computed via the backtest's HTFBarFetcher
(Polygon API) which has UTC/ET timezone issues. The fix computes M5/M15
structure locally from M1 bars, same as the ATR fix.

Run: python fix_reprocess_indicators.py
Then re-run the processor pipeline (Proc 2 onward).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "processor"))
import psycopg2
from db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

print("=" * 60)
print("FIX: Delete all indicator data for re-processing")
print("(M5/M15 structure fix)")
print("=" * 60)

# Delete in reverse dependency order (Proc 8 -> Proc 2)
tables_to_clean = [
    "j_m1_post_trade_indicator",
    "j_m1_ramp_up_indicator",
    "j_m1_trade_indicator",
    "j_trades_m5_r_win",
    "j_m5_atr_stop",
    "j_m1_atr_stop",
    "j_m1_indicator_bars",
]

for table in tables_to_clean:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        if count > 0:
            cur.execute(f"DELETE FROM {table}")
            print(f"  Deleted {count} rows from {table}")
        else:
            print(f"  {table}: no rows to delete")
    except Exception as e:
        print(f"  {table}: ERROR - {e}")
        conn.rollback()

conn.commit()
conn.close()

print()
print("Done. Now re-run the processor pipeline (all 8 processors).")
print("Proc 1 (j_m1_bars) will be skipped since raw bars are intact.")
print("Procs 2-8 will re-compute all data with corrected M5/M15 structure.")
print("=" * 60)

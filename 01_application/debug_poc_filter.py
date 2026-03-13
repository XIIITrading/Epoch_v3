"""Debug script: Compare raw HVN POCs vs filtered zones for TSLA on 2026-03-12.
Shows which POC lines would be drawn before and after the L3+ filter fix."""

import sys
sys.path.insert(0, r"C:\XIIITradingSystems\Epoch_v3")

from shared.data.supabase import SupabaseClient
from datetime import date

SESSION_DATE = date(2026, 3, 12)
TICKER = "TSLA"

client = SupabaseClient(session_date=SESSION_DATE, verbose=False)
if not client.connect():
    print("Connection failed")
    sys.exit(1)

# 1) Raw HVN POCs (what was being drawn before the fix)
pocs = client.get_hvn_pocs(ticker=TICKER)
print(f"=== RAW HVN POCs (all from hvn_pocs table) ===")
if pocs:
    for i, p in enumerate(pocs):
        print(f"  POC{i+1}: ${p:.2f}")
else:
    print("  No POCs found")

# 2) Filtered zones (L3+ only, from zones table)
zones_df = client.get_zones(ticker=TICKER)
print(f"\n=== FILTERED ZONES (L3+ stored in zones table) ===")
filtered_poc_prices = set()
if zones_df is not None and not zones_df.empty:
    for _, z in zones_df.iterrows():
        poc = z.get('hvn_poc', 0)
        score = z.get('score', 0)
        rank = z.get('rank', '?')
        zone_id = z.get('zone_id', '?')
        print(f"  {zone_id:12s} | POC: ${poc:>8.2f} | Score: {score:>5.1f} | Rank: {rank}")
        if poc > 0:
            filtered_poc_prices.add(round(poc, 2))
else:
    print("  No zones found")

# 3) Compare: which POCs pass the filter
print(f"\n=== COMPARISON ===")
print(f"  Raw POCs:      {len(pocs) if pocs else 0}")
print(f"  Filtered zones: {len(filtered_poc_prices)}")
print(f"\n  POC lines that SHOULD be drawn (L3+ match):")
if pocs:
    for i, p in enumerate(pocs):
        match = round(p, 2) in filtered_poc_prices
        marker = "DRAW" if match else "SKIP"
        print(f"    POC{i+1}: ${p:.2f}  --> {marker}")

# 4) Setups
primary = client.get_primary_zone(TICKER)
secondary = client.get_secondary_zone(TICKER)
print(f"\n=== SETUPS ===")
if primary:
    print(f"  PRIMARY:   POC: ${primary.get('hvn_poc',0):.2f} | Range: ${primary.get('zone_low',0):.2f}-${primary.get('zone_high',0):.2f}")
if secondary:
    print(f"  SECONDARY: POC: ${secondary.get('hvn_poc',0):.2f} | Range: ${secondary.get('zone_low',0):.2f}-${secondary.get('zone_high',0):.2f}")

client.close()

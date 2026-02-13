"""
TSLA Comparison Script - Run analysis and output results for comparison.
"""
from datetime import date
from calculators.bar_data import calculate_bar_data
from calculators.hvn_identifier import calculate_hvn
from calculators.zone_calculator import calculate_zones
from calculators.zone_filter import filter_zones
from calculators.market_structure import calculate_market_structure
from calculators.setup_analyzer import analyze_setups

ticker = 'TSLA'
anchor_date = date(2025, 11, 21)
analysis_date = date.today()

print('='*80)
print(f'STREAMLIT TOOL (05_analysis_tool) - TSLA Analysis')
print(f'Anchor Date: {anchor_date}')
print(f'Analysis Date: {analysis_date}')
print('='*80)

# Market Structure
print('\n--- MARKET STRUCTURE ---')
ms = calculate_market_structure(ticker, analysis_date)
print(f'Price: ${ms.price:.2f}')
print(f'D1:  {ms.d1.direction.value:8} | Strong: {str(round(ms.d1.strong, 2)) if ms.d1.strong else "N/A":>10} | Weak: {str(round(ms.d1.weak, 2)) if ms.d1.weak else "N/A":>10}')
print(f'H4:  {ms.h4.direction.value:8} | Strong: {str(round(ms.h4.strong, 2)) if ms.h4.strong else "N/A":>10} | Weak: {str(round(ms.h4.weak, 2)) if ms.h4.weak else "N/A":>10}')
print(f'H1:  {ms.h1.direction.value:8} | Strong: {str(round(ms.h1.strong, 2)) if ms.h1.strong else "N/A":>10} | Weak: {str(round(ms.h1.weak, 2)) if ms.h1.weak else "N/A":>10}')
print(f'M15: {ms.m15.direction.value:8} | Strong: {str(round(ms.m15.strong, 2)) if ms.m15.strong else "N/A":>10} | Weak: {str(round(ms.m15.weak, 2)) if ms.m15.weak else "N/A":>10}')
print(f'Composite: {ms.composite.value}')

# Bar Data
print('\n--- BAR DATA (ATR Values) ---')
bar_data = calculate_bar_data(ticker, analysis_date)
print(f'M5 ATR:  ${bar_data.m5_atr:.4f}' if bar_data.m5_atr else 'M5 ATR: N/A')
print(f'M15 ATR: ${bar_data.m15_atr:.4f}' if bar_data.m15_atr else 'M15 ATR: N/A')
print(f'H1 ATR:  ${bar_data.h1_atr:.4f}' if bar_data.h1_atr else 'H1 ATR: N/A')
print(f'D1 ATR:  ${bar_data.d1_atr:.4f}' if bar_data.d1_atr else 'D1 ATR: N/A')

print('\n--- BAR DATA (Daily OHLC) ---')
if bar_data.d1_current and bar_data.d1_current.open:
    print(f'Current: O=${bar_data.d1_current.open:.2f} H=${bar_data.d1_current.high:.2f} L=${bar_data.d1_current.low:.2f} C=${bar_data.d1_current.close:.2f}')
else:
    print('Current: N/A (market closed)')
if bar_data.d1_prior and bar_data.d1_prior.open:
    print(f'Prior:   O=${bar_data.d1_prior.open:.2f} H=${bar_data.d1_prior.high:.2f} L=${bar_data.d1_prior.low:.2f} C=${bar_data.d1_prior.close:.2f}')
else:
    print('Prior: N/A')

print('\n--- BAR DATA (Camarilla Daily) ---')
cam = bar_data.camarilla_daily
if cam and cam.r6:
    print(f'R6=${cam.r6:.2f} R4=${cam.r4:.2f} R3=${cam.r3:.2f}')
    print(f'S3=${cam.s3:.2f} S4=${cam.s4:.2f} S6=${cam.s6:.2f}')
else:
    print('Camarilla: N/A')

# HVN POCs (using D1 ATR for overlap threshold - matches original system)
print('\n--- HVN POCs ---')
hvn = calculate_hvn(ticker, anchor_date, analysis_date, bar_data.d1_atr)
print(f'Date Range: {hvn.start_date} to {hvn.end_date}')
print(f'Bars Analyzed: {hvn.bars_analyzed}')
print(f'ATR Used: ${hvn.atr_used:.4f}' if hvn.atr_used else 'ATR Used: N/A')
for poc in sorted(hvn.pocs, key=lambda x: x.rank):
    print(f'  POC{poc.rank:2d}: ${poc.price:.2f} (vol: {poc.volume:,.0f})')

# Zones
print('\n--- RAW ZONES ---')
raw_zones = calculate_zones(bar_data, hvn)
for z in raw_zones:
    print(f'  {z.zone_id}: POC=${z.hvn_poc:.2f} | Range=[${z.zone_low:.2f}-${z.zone_high:.2f}] | Score={z.score:.1f} | Rank={z.rank.value}')
    print(f'         Confluences: {z.confluences_str}')

# Filtered Zones
print('\n--- FILTERED ZONES ---')
filtered = filter_zones(raw_zones, bar_data, ms.composite)
for z in filtered:
    bull_mark = '[BULL]' if z.is_bull_poc else ''
    bear_mark = '[BEAR]' if z.is_bear_poc else ''
    print(f'  {z.zone_id}: POC=${z.hvn_poc:.2f} | Tier={z.tier.value} | ATR Dist={z.atr_distance:.2f} {bull_mark}{bear_mark}')

# Setup Analysis (Session 10 addition)
print('\n--- SETUP ANALYSIS ---')
primary_setup, secondary_setup = analyze_setups(filtered, hvn, bar_data, ms.composite)

print(f'\nComposite Direction: {ms.composite.value}')

if primary_setup:
    print(f'\nPRIMARY SETUP (with-trend):')
    print(f'  Direction: {primary_setup.direction.value}')
    print(f'  Zone ID:   {primary_setup.zone_id}')
    print(f'  HVN POC:   ${primary_setup.hvn_poc:.2f}')
    print(f'  Zone:      ${primary_setup.zone_low:.2f} - ${primary_setup.zone_high:.2f}')
    print(f'  Tier:      {primary_setup.tier.value}')
    print(f'  Target ID: {primary_setup.target_id}')
    print(f'  Target:    ${primary_setup.target:.2f}')
    print(f'  R:R:       {primary_setup.risk_reward:.2f}')
    print(f'  Setup String: {primary_setup.setup_string}')
else:
    print('\nPRIMARY SETUP: N/A')

if secondary_setup:
    print(f'\nSECONDARY SETUP (counter-trend):')
    print(f'  Direction: {secondary_setup.direction.value}')
    print(f'  Zone ID:   {secondary_setup.zone_id}')
    print(f'  HVN POC:   ${secondary_setup.hvn_poc:.2f}')
    print(f'  Zone:      ${secondary_setup.zone_low:.2f} - ${secondary_setup.zone_high:.2f}')
    print(f'  Tier:      {secondary_setup.tier.value}')
    print(f'  Target ID: {secondary_setup.target_id}')
    print(f'  Target:    ${secondary_setup.target:.2f}')
    print(f'  R:R:       {secondary_setup.risk_reward:.2f}')
    print(f'  Setup String: {secondary_setup.setup_string}')
else:
    print('\nSECONDARY SETUP: N/A')

# Generate combined PineScript strings
from core.data_models import generate_pinescript_6, generate_pinescript_16

pocs = hvn_result.get_poc_prices() if hvn_result else []
pinescript_6 = generate_pinescript_6(primary_setup, secondary_setup)
pinescript_16 = generate_pinescript_16(primary_setup, secondary_setup, pocs)

print(f'\nPINESCRIPT EXPORT:')
print(f'  PineScript_6:  {pinescript_6}')
print(f'  PineScript_16: {pinescript_16}')

print('\n' + '='*80)

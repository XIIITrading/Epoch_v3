"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 06: ZONE RESULTS
Configuration File
================================================================================
Organization: XIII Trading LLC
Module Path: C:\XIIITradingSystems\Epoch\02_zone_system\06_zone_results
Version: 1.1 - Updated for Proximity-Based Selection with Tier Classification
================================================================================

CHANGES FROM V1.0:
- VALID_RANKS now includes ALL ranks (L1-L5) - no filtering by rank
- Added TIER_MAPPING to classify zones by quality tier (T1/T2/T3)
- Primary/Secondary selection is now proximity-based (closest to price)
- Tier indicates confluence quality, not selection priority
================================================================================
"""

# ==============================================================================
# EXCEL CONFIGURATION
# ==============================================================================

EXCEL_FILEPATH = r"C:\XIIITradingSystems\Epoch\epoch_v1.xlsm"

# Worksheet names
WORKSHEET_RAW_ZONES = "raw_zones"
WORKSHEET_BAR_DATA = "bar_data"
WORKSHEET_ZONE_RESULTS = "zone_results"

# ==============================================================================
# ATR PROXIMITY THRESHOLDS
# ==============================================================================

# Zones within this many ATR of current price = Group 1 (immediate relevance)
ATR_GROUP_1_THRESHOLD = 1.0

# Zones within this many ATR of current price = Group 2 (near-term relevance)
ATR_GROUP_2_THRESHOLD = 2.0

# Zones beyond ATR_GROUP_2_THRESHOLD are excluded from output

# ==============================================================================
# TIER CLASSIFICATION (NEW IN V1.1)
# ==============================================================================
# Maps L1-L5 confluence ranks to T1/T2/T3 quality tiers
# T1 = Lower confluence quality (L1, L2)
# T2 = Medium confluence quality (L3)
# T3 = High confluence quality (L4, L5)

TIER_MAPPING = {
    'L1': 'T1',
    'L2': 'T1',
    'L3': 'T2',
    'L4': 'T3',
    'L5': 'T3'
}

# Tier descriptions for output/reporting
TIER_DESCRIPTIONS = {
    'T1': 'Lower Quality',
    'T2': 'Medium Quality',
    'T3': 'High Quality'
}

# ==============================================================================
# FILTERING PARAMETERS
# ==============================================================================

# V1.1 CHANGE: Now includes ALL ranks - no filtering by rank
# Selection is proximity-based, tier indicates quality
VALID_RANKS = ['L1', 'L2', 'L3', 'L4', 'L5']

# Maximum zones to keep per ticker after overlap elimination
MAX_ZONES_PER_TICKER = 10

# ==============================================================================
# BAR_DATA CELL REFERENCES
# ==============================================================================

# Ticker structure section (for current price)
TICKER_STRUCTURE_START_ROW = 4
TICKER_STRUCTURE_END_ROW = 13
PRICE_COLUMN = "E"

# On/Options metrics section (for d1_atr)
ON_OPTIONS_START_ROW = 73
ON_OPTIONS_END_ROW = 82
D1_ATR_COLUMN = "T"

# Ticker ID column (to match zones to bar_data rows)
TICKER_ID_COLUMN = "B"

# ==============================================================================
# RAW_ZONES COLUMN MAPPING
# ==============================================================================

RAW_ZONES_COLUMNS = {
    'ticker_id': 'A',
    'ticker': 'B',
    'date': 'C',
    'price': 'D',
    'direction': 'E',
    'zone_id': 'F',
    'hvn_poc': 'G',
    'zone_high': 'H',
    'zone_low': 'I',
    'overlaps': 'J',
    'score': 'K',
    'rank': 'L',
    'confluences': 'M'
}

# Data starts at row 2 (row 1 is headers)
RAW_ZONES_DATA_START_ROW = 2

# ==============================================================================
# ZONE_RESULTS OUTPUT MAPPING
# ==============================================================================

# V1.1 CHANGE: Added tier column (N), shifted setup columns to O-T
ZONE_RESULTS_COLUMNS = {
    # Zone data (A-M) - written by Module 06
    'ticker_id': 'A',
    'ticker': 'B',
    'date': 'C',
    'price': 'D',
    'direction': 'E',
    'zone_id': 'F',
    'hvn_poc': 'G',
    'zone_high': 'H',
    'zone_low': 'I',
    'overlaps': 'J',
    'score': 'K',
    'rank': 'L',
    'confluences': 'M',
    'tier': 'N'  # NEW: Quality tier (T1/T2/T3)
}

# Setup Analysis columns (O-T) - written by Module 07
# V1.1 CHANGE: Shifted from N-S to O-T to accommodate tier column
ZONE_RESULTS_SETUP_COLUMNS = {
    'epch_bull': 'O',
    'epch_bear': 'P',
    'epch_bull_price': 'Q',
    'epch_bear_price': 'R',
    'epch_bull_target': 'S',
    'epch_bear_target': 'T'
}

# Data starts at row 2 (row 1 is headers)
ZONE_RESULTS_DATA_START_ROW = 2

# ==============================================================================
# LOGGING / VERBOSE OUTPUT
# ==============================================================================

VERBOSE = True
"""
================================================================================
EPOCH TRADING SYSTEM - MODULE 07: SETUP ANALYSIS
Configuration File
================================================================================
Organization: XIII Trading LLC
Module Path: C:\XIIITradingSystems\Epoch\02_zone_system\07_setup_analysis
Version: 1.1 - Updated for Proximity-Based Selection with Tier Classification
================================================================================

VERSION 1.1 CHANGES:
- VALID_RANKS now includes ALL ranks (L1-L5) - no filtering by rank
- Added TIER_MAPPING and TIER_DESCRIPTIONS
- zone_results input columns now include tier (column N)
- Setup columns shifted from N-S to O-T
- Analysis worksheet columns updated to include tier
================================================================================
"""

# ==============================================================================
# EXCEL CONFIGURATION
# ==============================================================================

EXCEL_FILEPATH = r"C:\XIIITradingSystems\Epoch\epoch_v1.xlsm"

# Worksheet names
WORKSHEET_ZONE_RESULTS = "zone_results"
WORKSHEET_BAR_DATA = "bar_data"
WORKSHEET_MARKET_OVERVIEW = "market_overview"
WORKSHEET_ANALYSIS = "Analysis"

# ==============================================================================
# TARGET SELECTION PARAMETERS
# ==============================================================================

# Minimum R:R for POC-based target selection
# POC must be at least this many R from zone edge to qualify
MIN_RR_THRESHOLD = 3.0

# Default R:R for calculated target when no POC meets threshold
# If no POC meets 3R, calculate target at this R level
DEFAULT_RR_CALC = 4.0

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

TIER_DESCRIPTIONS = {
    'T1': 'Lower Quality',
    'T2': 'Medium Quality',
    'T3': 'High Quality'
}

# ==============================================================================
# VALID RANKS - V1.1: NOW INCLUDES ALL RANKS
# ==============================================================================
# Selection is proximity-based, tier indicates quality

VALID_RANKS = ['L1', 'L2', 'L3', 'L4', 'L5']

# ==============================================================================
# ZONE_RESULTS WORKSHEET - COLUMN MAPPING
# ==============================================================================

# V1.1: Columns A-N zone data (written by Module 06), includes tier at column N
ZONE_RESULTS_INPUT_COLUMNS = {
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

# V1.1: Columns O-T setup analysis (written by Module 07), shifted from N-S
ZONE_RESULTS_SETUP_COLUMNS = {
    'epch_bull': 'O',
    'epch_bear': 'P',
    'epch_bull_price': 'Q',
    'epch_bear_price': 'R',
    'epch_bull_target': 'S',
    'epch_bear_target': 'T'
}

ZONE_RESULTS_DATA_START_ROW = 2

# ==============================================================================
# BAR_DATA WORKSHEET - CELL REFERENCES
# ==============================================================================

# Ticker structure section (for current price and ticker_id)
TICKER_STRUCTURE_START_ROW = 4
TICKER_STRUCTURE_END_ROW = 13
TICKER_ID_COLUMN = "B"
PRICE_COLUMN = "E"

# Time HVN section (for target selection - 10 POCs per ticker)
TIME_HVN_START_ROW = 59
TIME_HVN_END_ROW = 68
HVN_POC_COLUMNS = {
    'hvn_poc1': 'F',
    'hvn_poc2': 'G',
    'hvn_poc3': 'H',
    'hvn_poc4': 'I',
    'hvn_poc5': 'J',
    'hvn_poc6': 'K',
    'hvn_poc7': 'L',
    'hvn_poc8': 'M',
    'hvn_poc9': 'N',
    'hvn_poc10': 'O'
}

# ==============================================================================
# MARKET_OVERVIEW WORKSHEET - CELL REFERENCES
# ==============================================================================

# Ticker structure section (for direction)
MO_TICKER_STRUCTURE_START_ROW = 36
MO_TICKER_STRUCTURE_END_ROW = 45
MO_TICKER_ID_COLUMN = "B"
MO_COMPOSITE_COLUMN = "R"  # Direction: Bull, Bull+, Bear, Bear+

# ==============================================================================
# ANALYSIS WORKSHEET - CELL REFERENCES
# ==============================================================================

# V1.1: Added tier column, expanded column ranges

# Primary section (with tier)
ANALYSIS_PRIMARY_HEADER_ROW = 30
ANALYSIS_PRIMARY_START_ROW = 31
ANALYSIS_PRIMARY_END_ROW = 40
ANALYSIS_PRIMARY_COLUMNS = {
    'ticker': 'B',
    'direction': 'C',
    'ticker_id': 'D',
    'zone_id': 'E',
    'hvn_poc': 'F',
    'zone_high': 'G',
    'zone_low': 'H',
    'tier': 'I',      # NEW: Quality tier
    'target_id': 'J',
    'target': 'K',
    'r_r': 'L'
}

# Secondary section (with tier)
ANALYSIS_SECONDARY_HEADER_ROW = 30
ANALYSIS_SECONDARY_START_ROW = 31
ANALYSIS_SECONDARY_END_ROW = 40
ANALYSIS_SECONDARY_COLUMNS = {
    'ticker': 'N',
    'direction': 'O',
    'ticker_id': 'P',
    'zone_id': 'Q',
    'hvn_poc': 'R',
    'zone_high': 'S',
    'zone_low': 'T',
    'tier': 'U',      # NEW: Quality tier
    'target_id': 'V',
    'target': 'W',
    'r_r': 'X'
}

# ==============================================================================
# LOGGING / VERBOSE OUTPUT
# ==============================================================================

VERBOSE = True
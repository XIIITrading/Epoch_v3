# epoch_config.py - Configuration for Epoch Trading System Raw Zones Module
# Organization: XIII Trading LLC
# Module: 05_raw_zones

"""
KEY DIFFERENCE FROM MERIDIAN:
- Meridian: Base score from HVN_TIMEFRAME_WEIGHTS (d120=3, d90=2, d60=1, etc.)
- Epoch: Base score from volume rank (poc1=3.0, poc2=2.5, poc3=2.0, ... poc10=0.1)
"""

# =============================================================================
# EPOCH POC BASE WEIGHTS (Volume-based ranking)
# =============================================================================
# Higher volume POCs get higher base scores
EPOCH_POC_BASE_WEIGHTS = {
    'hvn_poc1': 3.0,   # Highest volume = highest base
    'hvn_poc2': 2.5,
    'hvn_poc3': 2.0,
    'hvn_poc4': 1.5,
    'hvn_poc5': 1.0,
    'hvn_poc6': 0.8,
    'hvn_poc7': 0.6,
    'hvn_poc8': 0.4,
    'hvn_poc9': 0.2,
    'hvn_poc10': 0.1   # Lowest volume = lowest base
}

# =============================================================================
# ZONE WEIGHTS (from Meridian config.py)
# =============================================================================
ZONE_WEIGHTS = {
    # Monthly Levels
    'm1_01': {'weight': 3.0, 'category': 'm1', 'zone_atr': 'm15', 'con_type': 'monthly_level'},
    'm1_02': {'weight': 3.0, 'category': 'm1', 'zone_atr': 'm15', 'con_type': 'monthly_level'},
    'm1_03': {'weight': 3.0, 'category': 'm1', 'zone_atr': 'm15', 'con_type': 'monthly_level'},
    'm1_04': {'weight': 3.0, 'category': 'm1', 'zone_atr': 'm15', 'con_type': 'monthly_level'},

    # Weekly Levels
    'w1_01': {'weight': 2.0, 'category': 'w1', 'zone_atr': 'm15', 'con_type': 'weekly_level'},
    'w1_02': {'weight': 2.0, 'category': 'w1', 'zone_atr': 'm15', 'con_type': 'weekly_level'},
    'w1_03': {'weight': 2.0, 'category': 'w1', 'zone_atr': 'm15', 'con_type': 'weekly_level'},
    'w1_04': {'weight': 2.0, 'category': 'w1', 'zone_atr': 'm15', 'con_type': 'weekly_level'},

    # Daily Levels
    'd1_01': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm15', 'con_type': 'daily_level'},
    'd1_02': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm15', 'con_type': 'daily_level'},
    'd1_03': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm15', 'con_type': 'daily_level'},
    'd1_04': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm15', 'con_type': 'daily_level'},

    # Prior Period Levels - Daily
    'd1_po': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm15', 'con_type': 'prior_daily'},
    'd1_ph': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm15', 'con_type': 'prior_daily'},
    'd1_pl': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm15', 'con_type': 'prior_daily'},
    'd1_pc': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm15', 'con_type': 'prior_daily'},
    'd1_onh': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm15', 'con_type': 'prior_daily'},
    'd1_onl': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm15', 'con_type': 'prior_daily'},

    # Prior Period Levels - Weekly
    'w1_po': {'weight': 2.0, 'category': 'w1', 'zone_atr': 'm15', 'con_type': 'prior_weekly'},
    'w1_ph': {'weight': 2.0, 'category': 'w1', 'zone_atr': 'm15', 'con_type': 'prior_weekly'},
    'w1_pl': {'weight': 2.0, 'category': 'w1', 'zone_atr': 'm15', 'con_type': 'prior_weekly'},
    'w1_pc': {'weight': 2.0, 'category': 'w1', 'zone_atr': 'm15', 'con_type': 'prior_weekly'},

    # Prior Period Levels - Monthly
    'm1_po': {'weight': 3.0, 'category': 'm1', 'zone_atr': 'm15', 'con_type': 'prior_monthly'},
    'm1_ph': {'weight': 3.0, 'category': 'm1', 'zone_atr': 'm15', 'con_type': 'prior_monthly'},
    'm1_pl': {'weight': 3.0, 'category': 'm1', 'zone_atr': 'm15', 'con_type': 'prior_monthly'},
    'm1_pc': {'weight': 3.0, 'category': 'm1', 'zone_atr': 'm15', 'con_type': 'prior_monthly'},

    # Options Levels - Strong weight as they act as magnets
    'op_01': {'weight': 2.5, 'category': 'opt', 'zone_atr': 'm5', 'con_type': 'options_level'},
    'op_02': {'weight': 2.5, 'category': 'opt', 'zone_atr': 'm5', 'con_type': 'options_level'},
    'op_03': {'weight': 2.0, 'category': 'opt', 'zone_atr': 'm5', 'con_type': 'options_level'},
    'op_04': {'weight': 2.0, 'category': 'opt', 'zone_atr': 'm5', 'con_type': 'options_level'},
    'op_05': {'weight': 1.5, 'category': 'opt', 'zone_atr': 'm5', 'con_type': 'options_level'},
    'op_06': {'weight': 1.5, 'category': 'opt', 'zone_atr': 'm5', 'con_type': 'options_level'},
    'op_07': {'weight': 1.0, 'category': 'opt', 'zone_atr': 'm5', 'con_type': 'options_level'},
    'op_08': {'weight': 1.0, 'category': 'opt', 'zone_atr': 'm5', 'con_type': 'options_level'},
    'op_09': {'weight': 0.5, 'category': 'opt', 'zone_atr': 'm5', 'con_type': 'options_level'},
    'op_10': {'weight': 0.5, 'category': 'opt', 'zone_atr': 'm5', 'con_type': 'options_level'},

    # Market Structure Levels
    'd1_s': {'weight': 1.5, 'category': 'd1', 'zone_atr': 'm5', 'con_type': 'market_structure_daily'},
    'd1_w': {'weight': 1.5, 'category': 'd1', 'zone_atr': 'm5', 'con_type': 'market_structure_daily'},
    'h4_s': {'weight': 1.25, 'category': 'h4', 'zone_atr': 'm5', 'con_type': 'market_structure_h4'},
    'h4_w': {'weight': 1.25, 'category': 'h4', 'zone_atr': 'm5', 'con_type': 'market_structure_h4'},
    'h1_s': {'weight': 1.0, 'category': 'h1', 'zone_atr': 'm5', 'con_type': 'market_structure_hourly'},
    'h1_w': {'weight': 1.0, 'category': 'h1', 'zone_atr': 'm5', 'con_type': 'market_structure_hourly'},
    'm15_s': {'weight': 0.75, 'category': 'm15', 'zone_atr': 'm5', 'con_type': 'market_structure_m15'},
    'm15_w': {'weight': 0.75, 'category': 'm15', 'zone_atr': 'm5', 'con_type': 'market_structure_m15'},
}

# =============================================================================
# CAMARILLA LEVEL WEIGHTS
# =============================================================================
CAM_WEIGHTS = {
    # Daily Camarilla
    'd1_s6': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm5', 'con_type': 'daily_cam'},
    'd1_s4': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm5', 'con_type': 'daily_cam'},
    'd1_s3': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm5', 'con_type': 'daily_cam'},
    'd1_r3': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm5', 'con_type': 'daily_cam'},
    'd1_r4': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm5', 'con_type': 'daily_cam'},
    'd1_r6': {'weight': 1.0, 'category': 'd1', 'zone_atr': 'm5', 'con_type': 'daily_cam'},

    # Weekly Camarilla
    'w1_s6': {'weight': 2.0, 'category': 'w1', 'zone_atr': 'm5', 'con_type': 'weekly_cam'},
    'w1_s4': {'weight': 2.0, 'category': 'w1', 'zone_atr': 'm5', 'con_type': 'weekly_cam'},
    'w1_s3': {'weight': 2.0, 'category': 'w1', 'zone_atr': 'm5', 'con_type': 'weekly_cam'},
    'w1_r3': {'weight': 2.0, 'category': 'w1', 'zone_atr': 'm5', 'con_type': 'weekly_cam'},
    'w1_r4': {'weight': 2.0, 'category': 'w1', 'zone_atr': 'm5', 'con_type': 'weekly_cam'},
    'w1_r6': {'weight': 2.0, 'category': 'w1', 'zone_atr': 'm5', 'con_type': 'weekly_cam'},

    # Monthly Camarilla
    'm1_s6': {'weight': 3.0, 'category': 'm1', 'zone_atr': 'm5', 'con_type': 'monthly_cam'},
    'm1_s4': {'weight': 3.0, 'category': 'm1', 'zone_atr': 'm5', 'con_type': 'monthly_cam'},
    'm1_s3': {'weight': 3.0, 'category': 'm1', 'zone_atr': 'm5', 'con_type': 'monthly_cam'},
    'm1_r3': {'weight': 3.0, 'category': 'm1', 'zone_atr': 'm5', 'con_type': 'monthly_cam'},
    'm1_r4': {'weight': 3.0, 'category': 'm1', 'zone_atr': 'm5', 'con_type': 'monthly_cam'},
    'm1_r6': {'weight': 3.0, 'category': 'm1', 'zone_atr': 'm5', 'con_type': 'monthly_cam'},
}

# =============================================================================
# BUCKET WEIGHTS (Maximum contribution per confluence category)
# =============================================================================
BUCKET_WEIGHTS = {
    'monthly_level': 3.0,
    'weekly_level': 2.0,
    'daily_level': 1.0,
    'daily_cam': 1.0,
    'weekly_cam': 2.0,
    'monthly_cam': 3.0,
    'prior_daily': 1.0,
    'prior_weekly': 2.0,
    'prior_monthly': 3.0,
    'options_level': 2.5,
    'market_structure_daily': 1.5,
    'market_structure_h4': 1.25,
    'market_structure_hourly': 1.0,
    'market_structure_m15': 0.75,
}

# =============================================================================
# L1-L5 RANKING THRESHOLDS
# =============================================================================
# Using percentage of maximum possible score
# Max possible = sum(BUCKET_WEIGHTS) + max(EPOCH_POC_BASE_WEIGHTS) ≈ 24 + 3 = 27
RANKING_THRESHOLDS = {
    'L5': 0.60,  # 60%+ of max = BEST (score >= ~16)
    'L4': 0.40,  # 40-60% (score >= ~11)
    'L3': 0.25,  # 25-40% (score >= ~7)
    'L2': 0.10,  # 10-25% (score >= ~3)
    'L1': 0.00   # 0-10% = WORST (score < ~3)
}

# Alternative: Fixed score thresholds (simpler, may work better in practice)
RANKING_SCORE_THRESHOLDS = {
    'L5': 12.0,  # Score >= 12 = L5 (BEST)
    'L4': 9.0,   # Score >= 9 = L4
    'L3': 6.0,   # Score >= 6 = L3
    'L2': 3.0,   # Score >= 3 = L2
    'L1': 0.0    # Score < 3 = L1 (WORST)
}

# =============================================================================
# EXCEL CONFIGURATION
# =============================================================================
EXCEL_FILEPATH = r"C:\XIIITradingSystems\Epoch\epoch_v1.xlsm"
VERBOSE = True

# =============================================================================
# ZONE NAME MAPPING (for readable confluence output)
# =============================================================================
ZONE_NAME_MAP = {
    # Monthly OHLC
    'm1_01': 'M Open', 'm1_02': 'M High', 'm1_03': 'M Low', 'm1_04': 'M Close',
    'm1_po': 'PM Open', 'm1_ph': 'PM High', 'm1_pl': 'PM Low', 'm1_pc': 'PM Close',
    
    # Weekly OHLC
    'w1_01': 'W Open', 'w1_02': 'W High', 'w1_03': 'W Low', 'w1_04': 'W Close',
    'w1_po': 'PW Open', 'w1_ph': 'PW High', 'w1_pl': 'PW Low', 'w1_pc': 'PW Close',
    
    # Daily OHLC
    'd1_01': 'D Open', 'd1_02': 'D High', 'd1_03': 'D Low', 'd1_04': 'D Close',
    'd1_po': 'PD Open', 'd1_ph': 'PD High', 'd1_pl': 'PD Low', 'd1_pc': 'PD Close',
    'd1_onh': 'ON High', 'd1_onl': 'ON Low',
    
    # Camarilla Levels
    'd1_s6': 'D S6', 'd1_s4': 'D S4', 'd1_s3': 'D S3',
    'd1_r3': 'D R3', 'd1_r4': 'D R4', 'd1_r6': 'D R6',
    'w1_s6': 'W S6', 'w1_s4': 'W S4', 'w1_s3': 'W S3',
    'w1_r3': 'W R3', 'w1_r4': 'W R4', 'w1_r6': 'W R6',
    'm1_s6': 'M S6', 'm1_s4': 'M S4', 'm1_s3': 'M S3',
    'm1_r3': 'M R3', 'm1_r4': 'M R4', 'm1_r6': 'M R6',
    
    # Options Levels
    'op_01': 'OP1', 'op_02': 'OP2', 'op_03': 'OP3', 'op_04': 'OP4', 'op_05': 'OP5',
    'op_06': 'OP6', 'op_07': 'OP7', 'op_08': 'OP8', 'op_09': 'OP9', 'op_10': 'OP10',
    
    # Market Structure Levels
    'd1_s': 'D1 Strong', 'd1_w': 'D1 Weak',
    'h4_s': 'H4 Strong', 'h4_w': 'H4 Weak',
    'h1_s': 'H1 Strong', 'h1_w': 'H1 Weak',
    'm15_s': 'M15 Strong', 'm15_w': 'M15 Weak',
}

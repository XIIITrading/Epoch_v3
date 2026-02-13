"""
Module 10: Configuration
Paths, API keys, and Excel cell mappings for analysis export.

UPDATED: V1.1 compatibility - Tier column added, secondary section shifted
"""
import os
from pathlib import Path

# =============================================================================
# PATHS - Updated to match your renamed directory
# =============================================================================
EPOCH_BASE = Path(r"C:\XIIITradingSystems\Epoch")
EXCEL_WORKBOOK = EPOCH_BASE / "epoch_v1.xlsm"
OUTPUT_DIR = EPOCH_BASE / "02_zone_system" / "10_results_analysis" / "exports"
DATABASE_PATH = EPOCH_BASE / "02_zone_system" / "10_results_analysis" / "epoch_history.db"

# =============================================================================
# API KEYS
# =============================================================================
POLYGON_API_KEY = "f4vzZl0gWXkv9hiKJprpsVRqbwrydf4_"

# =============================================================================
# EXCEL SHEET NAMES (lowercase as they appear in workbook)
# =============================================================================
SHEET_ANALYSIS = "analysis"
SHEET_BACKTEST = "backtest"
SHEET_MARKET = "market_overview"
SHEET_ENTRY_EVENTS = "entry_events"
SHEET_EXIT_EVENTS = "exit_events"
SHEET_OPTIMAL_TRADE = "optimal_trade"

# =============================================================================
# EXCEL CELL MAPPINGS - ANALYSIS SHEET (V1.1 - WITH TIER COLUMN)
# =============================================================================
# V1.1 Headers: Ticker, Direction, Ticker ID, Zone ID, HVN POC, 
#               Zone High, Zone Low, Tier, Target ID, Target, R:R

# Primary zones: B31:L40 (11 columns with Tier)
ANALYSIS_PRIMARY = {
    "start_row": 31,
    "end_row": 40,
    "ticker": "B",        # Column B
    "direction": "C",     # Column C
    "ticker_id": "D",     # Column D
    "zone_id": "E",       # Column E
    "hvn_poc": "F",       # Column F
    "zone_high": "G",     # Column G
    "zone_low": "H",      # Column H
    "tier": "I",          # Column I (NEW in V1.1)
    "target_id": "J",     # Column J (was I)
    "target": "K",        # Column K (was J)
    "rr_ratio": "L",      # Column L (was K)
}

# Secondary zones: N31:X40 (11 columns with Tier) - SHIFTED FROM M TO N
ANALYSIS_SECONDARY = {
    "start_row": 31,
    "end_row": 40,
    "ticker": "N",        # Column N (was M)
    "direction": "O",     # Column O (was N)
    "ticker_id": "P",     # Column P (was O)
    "zone_id": "Q",       # Column Q (was P)
    "hvn_poc": "R",       # Column R (was Q)
    "zone_high": "S",     # Column S (was R)
    "zone_low": "T",      # Column T (was S)
    "tier": "U",          # Column U (NEW in V1.1)
    "target_id": "V",     # Column V (was T)
    "target": "W",        # Column W (was U)
    "rr_ratio": "X",      # Column X (was V)
}

# =============================================================================
# EXCEL CELL MAPPINGS - MARKET OVERVIEW SHEET
# =============================================================================
# User tickers section (rows 36-45)
MARKET_OVERVIEW = {
    "user_start_row": 36,
    "user_end_row": 45,
    "ticker_id": "B",
    "ticker": "C",
    "date": "D",
    "price": "E",
    "d1_dir": "F",
    "h4_dir": "I",
    "h1_dir": "L",
    "m15_dir": "O",
    "composite": "R",
}

# =============================================================================
# EXCEL CELL MAPPINGS - BACKTEST SHEET (v2.3 - trade_id in column A)
# =============================================================================
# Trade Log: Columns A-U, starting row 3
# v2.3: Added trade_id in column A, all others shifted right by 1
BACKTEST_TRADES = {
    "start_row": 3,
    "max_rows": 100,
    "trade_id": "A",      # v2.3: NEW - format: ticker_MMDDYY_model_HHMM
    "date": "B",          # v2.3: Was A
    "ticker": "C",        # v2.3: Was B
    "model": "D",         # v2.3: Was C
    "zone_type": "E",     # v2.3: Was D
    "direction": "F",     # v2.3: Was E
    "zone_high": "G",     # v2.3: Was F
    "zone_low": "H",      # v2.3: Was G
    "entry_price": "I",   # v2.3: Was H
    "entry_time": "J",    # v2.3: Was I
    "stop_price": "K",    # v2.3: Was J
    "target_3r": "L",     # v2.3: Was K (renamed from target_2r)
    "target_calc": "M",   # v2.3: Was L (was target_3r)
    "target_used": "N",   # v2.3: Was M (was target_calc)
    "exit_price": "O",    # v2.3: Was N
    "exit_time": "P",     # v2.3: Was O
    "exit_reason": "Q",   # v2.3: Was P
    "pnl_dollars": "R",   # v2.3: Was Q
    "pnl_r": "S",         # v2.3: Was R
    "risk": "T",          # v2.3: NEW
    "is_win": "U",        # v2.3: Was S
}

# No-Trade Log: Columns AA-AN, starting row 3
# Note: No-trade log format unchanged in v2.3
BACKTEST_NO_TRADES = {
    "start_row": 3,
    "max_rows": 100,
    "date": "AA",
    "ticker": "AB",
    "model": "AC",
    "zone_type": "AD",
    "direction": "AE",
    "zone_high": "AF",
    "zone_low": "AG",
    "reason": "AH",
    "day_high": "AI",
    "day_low": "AJ",
    "day_open": "AK",
    "day_close": "AL",
    "zone_touched": "AM",
    "bars_in_zone": "AN",
}

# =============================================================================
# MODEL DEFINITIONS
# =============================================================================
MODEL_NAMES = {
    "1": "EPCH1",
    "2": "EPCH2",
    "3": "EPCH3",
    "4": "EPCH4",
    "EPCH1": "EPCH1",
    "EPCH2": "EPCH2",
    "EPCH3": "EPCH3",
    "EPCH4": "EPCH4",
}

MODEL_DESCRIPTIONS = {
    "EPCH1": "Primary Zone Breakout - Trade break of primary zone in composite direction",
    "EPCH2": "Primary Zone Rejection - Trade rejection at primary zone against composite",
    "EPCH3": "Secondary Zone Breakout - Trade break of secondary zone in composite direction",
    "EPCH4": "Secondary Zone Rejection - Trade rejection at secondary zone against composite",
}

# =============================================================================
# TIER DEFINITIONS (V1.1)
# =============================================================================
TIER_NAMES = {
    "T1": "Tier 1 - Premium",
    "T2": "Tier 2 - Standard", 
    "T3": "Tier 3 - Marginal",
}

TIER_DESCRIPTIONS = {
    "T1": "High confluence, strong alignment",
    "T2": "Moderate confluence",
    "T3": "Lower confluence, use caution",
}

# =============================================================================
# WIN DETECTION
# =============================================================================
WIN_VALUES = ["W", "Win", "WIN", "w", "win", True, 1, "1", "TRUE", "True"]
LOSS_VALUES = ["L", "Loss", "LOSS", "l", "loss", False, 0, "0", "FALSE", "False"]

# =============================================================================
# POLYGON API SETTINGS
# =============================================================================
POLYGON_BASE_URL = "https://api.polygon.io"
MARKET_OPEN_ET = "09:30"
MARKET_CLOSE_ET = "16:00"

# Tickers to fetch for market context
MARKET_TICKERS = ["SPY", "QQQ", "VIX"]

# =============================================================================
# EXCEL CELL MAPPINGS - ENTRY_EVENTS SHEET (v3 lean - 34 columns)
# =============================================================================
# Join key + enrichment data only (no backtest duplication)
ENTRY_EVENTS = {
    "start_row": 2,
    "max_rows": 200,
    # Column A: Join Key
    "trade_id": "A",
    # Columns B-H: Entry Price Position (7)
    "entry_vwap": "B",
    "entry_vs_vwap": "C",
    "entry_sma9": "D",
    "entry_vs_sma9": "E",
    "entry_sma21": "F",
    "entry_vs_sma21": "G",
    "sma9_vs_sma21": "H",
    # Columns I-P: Entry Volume Analysis (8)
    "entry_volume": "I",
    "avg_volume_5": "J",
    "volume_delta_pct": "K",
    "volume_trend": "L",
    "relative_volume": "M",
    "prior_bar_qual": "N",
    "vol_delta_class": "O",
    "vol_delta_value": "P",
    # Columns Q-X: Multi-Timeframe Structure (8)
    "m5_structure": "Q",
    "m15_structure": "R",
    "h1_structure": "S",
    "h4_structure": "T",
    "structure_align": "U",
    "dominant_struct": "V",
    "m5_last_break": "W",
    "m15_last_break": "X",
    # Columns Y-AB: Entry Health Score (4)
    "health_score": "Y",
    "health_max": "Z",
    "health_pct": "AA",
    "health_label": "AB",
    # Columns AC-AE: Alignment Flags (3)
    "vwap_aligned": "AC",
    "trend_aligned": "AD",
    "structure_aligned": "AE",
    # Columns AF-AH: Processing Metadata (3)
    "enrichment_time": "AF",
    "status": "AG",
    "error": "AH",
}

# =============================================================================
# EXCEL CELL MAPPINGS - EXIT_EVENTS SHEET (v2 lean - 18 columns)
# =============================================================================
# Multiple rows per trade (event timeline)
EXIT_EVENTS = {
    "start_row": 2,
    "max_rows": 1000,  # Can have many events
    # Column A: Join Key (not unique - multiple events per trade)
    "trade_id": "A",
    # Columns B-E: Event Timing (4)
    "event_seq": "B",
    "event_time": "C",
    "bars_from_entry": "D",
    "bars_from_mfe": "E",
    # Columns F-H: Event Details (3)
    "event_type": "F",
    "from_state": "G",
    "to_state": "H",
    # Columns I-L: Position at Event (4)
    "price_at_event": "I",
    "r_at_event": "J",
    "health_score": "K",
    "health_delta": "L",
    # Columns M-R: Indicator Values at Event (6)
    "vwap": "M",
    "sma9": "N",
    "sma21": "O",
    "volume": "P",
    "swing_high": "Q",
    "swing_low": "R",
}

# =============================================================================
# EXCEL CELL MAPPINGS - OPTIMAL_TRADE SHEET
# =============================================================================
# Best theoretical exit for each trade
OPTIMAL_TRADE = {
    "start_row": 2,
    "max_rows": 200,
    "trade_id": "A",
    "optimal_exit_price": "B",
    "optimal_exit_time": "C",
    "optimal_exit_reason": "D",
    "optimal_pnl_r": "E",
    "mfe_price": "F",
    "mfe_time": "G",
    "mfe_r": "H",
    "mae_price": "I",
    "mae_time": "J",
    "mae_r": "K",
    "capture_efficiency": "L",  # actual_r / optimal_r
    "notes": "M",
}
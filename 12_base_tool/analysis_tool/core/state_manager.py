"""
Session State Manager for Streamlit Application.

Manages all session state for the Epoch Analysis Tool.
Provides clean API for accessing and modifying state.
"""
import streamlit as st
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from config.settings import INDEX_TICKERS, MAX_TICKERS

# Eastern Time zone for market hours
ET_TIMEZONE = ZoneInfo("America/New_York")


def init_session_state():
    """Initialize all session state variables with defaults."""

    # Ticker inputs (10 rows, each with ticker and anchor_date)
    if "ticker_rows" not in st.session_state:
        st.session_state.ticker_rows = [
            {"ticker": "", "anchor_date": None}
            for _ in range(MAX_TICKERS)
        ]

    # Index ticker results (SPY, QQQ, DIA with prior month anchor)
    if "index_results" not in st.session_state:
        st.session_state.index_results = []

    # Analysis results storage
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = {}

    # Pipeline state
    if "run_requested" not in st.session_state:
        st.session_state.run_requested = False

    if "pipeline_stage" not in st.session_state:
        st.session_state.pipeline_stage = None

    if "pipeline_progress" not in st.session_state:
        st.session_state.pipeline_progress = 0.0

    if "pipeline_status" not in st.session_state:
        st.session_state.pipeline_status = ""

    # Current ticker being processed
    if "current_ticker" not in st.session_state:
        st.session_state.current_ticker = None

    # Errors
    if "errors" not in st.session_state:
        st.session_state.errors = []


def get_state(key: str, default: Any = None) -> Any:
    """
    Get a value from session state.

    Args:
        key: The state key to retrieve
        default: Default value if key doesn't exist

    Returns:
        The state value or default
    """
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    """
    Set a value in session state.

    Args:
        key: The state key to set
        value: The value to store
    """
    st.session_state[key] = value


def update_ticker_row(index: int, ticker: str = None, anchor_date: date = None) -> None:
    """
    Update a specific ticker row.

    Args:
        index: Row index (0-9)
        ticker: Ticker symbol (optional)
        anchor_date: Anchor date for HVN calculation (optional)
    """
    if 0 <= index < MAX_TICKERS:
        if ticker is not None:
            st.session_state.ticker_rows[index]["ticker"] = ticker.upper().strip()
        if anchor_date is not None:
            st.session_state.ticker_rows[index]["anchor_date"] = anchor_date


def get_ticker_rows() -> List[Dict]:
    """
    Get all ticker rows.

    Returns:
        List of 10 ticker row dictionaries
    """
    return st.session_state.get("ticker_rows", [])


def get_valid_ticker_inputs() -> List[Dict]:
    """
    Get only valid ticker inputs (with both ticker and anchor_date).

    Returns:
        List of valid ticker input dictionaries
    """
    rows = get_ticker_rows()
    return [
        row for row in rows
        if row.get("ticker") and row.get("anchor_date")
    ]


def clear_results() -> None:
    """Clear all analysis results."""
    st.session_state.analysis_results = {}
    st.session_state.index_results = []
    st.session_state.errors = []


def update_pipeline_progress(stage: str, progress: float, status: str = "") -> None:
    """
    Update pipeline progress state and print to terminal.

    Args:
        stage: Current pipeline stage name
        progress: Progress percentage (0.0 to 1.0)
        status: Optional status message
    """
    st.session_state.pipeline_stage = stage
    st.session_state.pipeline_progress = progress
    st.session_state.pipeline_status = status

    # Terminal output for Claude Code visibility
    progress_pct = int(progress * 100)
    stage_display = stage.replace("_", " ").title()

    if stage == "complete":
        print(f"\n{'='*60}")
        print(f"[COMPLETE] {status}")
        print(f"{'='*60}\n")
    else:
        print(f"[{progress_pct:3d}%] [{stage_display}] {status}")


def add_error(error: str) -> None:
    """Add an error message to the error list and print to terminal."""
    if "errors" not in st.session_state:
        st.session_state.errors = []
    st.session_state.errors.append(error)

    # Terminal output for error visibility
    print(f"\n[ERROR] {error}\n")


def get_errors() -> List[str]:
    """Get all error messages."""
    return st.session_state.get("errors", [])


def clear_errors() -> None:
    """Clear all error messages."""
    st.session_state.errors = []


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_prior_month_anchor(reference_date: date = None) -> date:
    """
    Get the prior month anchor date (last day of previous month).

    Args:
        reference_date: Reference date (defaults to today)

    Returns:
        Last day of the previous month
    """
    ref = reference_date or date.today()
    first_of_month = ref.replace(day=1)
    return first_of_month - timedelta(days=1)


def get_prior_week_anchor(reference_date: date = None) -> date:
    """
    Get the prior week anchor date (previous Friday).

    Args:
        reference_date: Reference date (defaults to today)

    Returns:
        Previous Friday's date
    """
    ref = reference_date or date.today()
    # weekday(): Monday=0, Tuesday=1, ..., Friday=4, Saturday=5, Sunday=6
    days_since_friday = (ref.weekday() - 4) % 7
    if days_since_friday == 0:
        days_since_friday = 7  # If today is Friday, go to last Friday
    return ref - timedelta(days=days_since_friday)


def get_prior_day_anchor(reference_date: date = None) -> date:
    """
    Get the prior day anchor date (previous trading day).

    Note: This is a simplified version that returns yesterday.
    For production, you'd want to check NYSE calendar for holidays.

    Args:
        reference_date: Reference date (defaults to today)

    Returns:
        Previous trading day
    """
    ref = reference_date or date.today()
    prior = ref - timedelta(days=1)

    # Skip weekends
    while prior.weekday() >= 5:  # Saturday=5, Sunday=6
        prior -= timedelta(days=1)

    return prior


def get_ytd_anchor(reference_date: date = None) -> date:
    """
    Get the YTD anchor date (January 1 of current year).

    Args:
        reference_date: Reference date (defaults to today)

    Returns:
        January 1 of the reference year
    """
    ref = reference_date or date.today()
    return date(ref.year, 1, 1)


def get_anchor_date(preset: str, reference_date: date = None) -> date:
    """
    Get anchor date from preset name.

    Args:
        preset: Preset name ('prior_day', 'prior_week', 'prior_month', 'ytd')
        reference_date: Reference date (defaults to today)

    Returns:
        Calculated anchor date

    Raises:
        ValueError: If preset is unknown
    """
    preset = preset.lower().replace(" ", "_")

    if preset == "prior_day":
        return get_prior_day_anchor(reference_date)
    elif preset == "prior_week":
        return get_prior_week_anchor(reference_date)
    elif preset == "prior_month":
        return get_prior_month_anchor(reference_date)
    elif preset == "ytd":
        return get_ytd_anchor(reference_date)
    else:
        raise ValueError(f"Unknown anchor preset: {preset}")


# Available anchor presets for batch mode
ANCHOR_PRESETS = ["Prior Day", "Prior Week", "Prior Month", "YTD"]


def get_index_ticker_inputs() -> List[Dict]:
    """
    Get index ticker inputs with prior month anchor.

    Returns:
        List of index ticker input dictionaries
    """
    anchor = get_prior_month_anchor()
    today = date.today()

    return [
        {
            "ticker": ticker,
            "anchor_date": anchor,
            "analysis_date": today,
            "is_index": True
        }
        for ticker in INDEX_TICKERS
    ]


# =============================================================================
# MARKET TIME MODE FUNCTIONS
# =============================================================================

def get_market_time_mode() -> str:
    """
    Get the current market time mode.

    Returns:
        'Live', 'Pre-Market', or 'Post-Market'
    """
    return get_state("market_time_mode", "Live")


def get_market_end_timestamp(analysis_date: date = None) -> Optional[datetime]:
    """
    Get the end timestamp based on market time mode.

    Args:
        analysis_date: The analysis date (defaults to today)

    Returns:
        Timezone-aware datetime for the end cutoff, or None for Live mode.
        - Live: Returns None (use current time)
        - Pre-Market: Returns 09:01 ET on analysis_date
        - Post-Market: Returns 16:01 ET on analysis_date
    """
    mode = get_market_time_mode()
    analysis_date = analysis_date or date.today()

    if mode == "Live":
        return None  # No cutoff - use current time

    elif mode == "Pre-Market":
        # 09:01 ET = last complete bar is 08:00-09:00
        return datetime(
            analysis_date.year,
            analysis_date.month,
            analysis_date.day,
            9, 1, 0,
            tzinfo=ET_TIMEZONE
        )

    elif mode == "Post-Market":
        # 16:01 ET = last complete bar is 15:00-16:00
        return datetime(
            analysis_date.year,
            analysis_date.month,
            analysis_date.day,
            16, 1, 0,
            tzinfo=ET_TIMEZONE
        )

    return None


def get_market_end_timestamp_ms(analysis_date: date = None) -> Optional[int]:
    """
    Get the end timestamp in milliseconds for Polygon API.

    Args:
        analysis_date: The analysis date (defaults to today)

    Returns:
        Unix timestamp in milliseconds, or None for Live mode
    """
    end_dt = get_market_end_timestamp(analysis_date)
    if end_dt is None:
        return None
    return int(end_dt.timestamp() * 1000)


def get_market_end_iso(analysis_date: date = None) -> Optional[str]:
    """
    Get the end timestamp as ISO format string for Polygon API.

    Args:
        analysis_date: The analysis date (defaults to today)

    Returns:
        ISO format datetime string (e.g., '2024-01-15T09:01:00-05:00'), or None for Live mode
    """
    end_dt = get_market_end_timestamp(analysis_date)
    if end_dt is None:
        return None
    return end_dt.isoformat()


# =============================================================================
# CACHE MANAGEMENT FUNCTIONS
# =============================================================================

def clear_all_caches() -> Dict[str, int]:
    """
    Clear all caches (file cache and session state).

    Returns:
        Dictionary with counts of cleared items
    """
    from data.cache_manager import cache

    counts = {
        "file_cache": 0,
        "session_state": 0
    }

    # Clear file-based cache
    try:
        counts["file_cache"] = cache.clear("*")
    except Exception as e:
        print(f"Error clearing file cache: {e}")

    # Clear analysis-related session state
    keys_to_clear = [
        "analysis_results",
        "index_results",
        "run_requested",
        "pipeline_stage",
        "pipeline_progress",
        "pipeline_status",
        "current_ticker",
        "errors"
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
            counts["session_state"] += 1

    # Re-initialize defaults
    init_session_state()

    return counts


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Dictionary with cache stats
    """
    from data.cache_manager import cache
    return cache.get_cache_stats()

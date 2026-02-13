"""
Notion page builder — orchestrates data fetching and content generation.

Takes a trade row dict (from journal_trades), fetches all supporting data
via NotionDataFetcher, and produces a (properties, content) tuple ready
for the notion-create-pages MCP call.
"""

from typing import Dict, Tuple, Optional, List, Set
import logging

from .data_fetcher import NotionDataFetcher
from .config import NOTION_DATA_SOURCE_ID
from .content_sections import (
    section_trade_summary,
    section_risk_management,
    section_zone_context,
    section_indicator_snapshot,
    section_excursion_analysis,
    section_r_level_progression,
    section_m1_rampup,
    section_indicator_refinement,
    section_charts,
    section_trade_assessment,
    section_journal_notes,
)

logger = logging.getLogger(__name__)


class NotionPageBuilder:
    """
    Builds complete Notion page for a single trade.

    Workflow:
        1. Receive trade row dict from journal_trades
        2. Fetch indicator bar at entry time
        3. Fetch 15 ramp-up bars
        4. Fetch zone data (if zone_id set)
        5. Calculate MFE/MAE (if stop_price set)
        6. Calculate R-level events (if stop_price set)
        7. Build properties dict for Notion
        8. Build content string (10 sections concatenated)
        9. Return (properties, content) tuple

    Usage:
        with NotionDataFetcher() as fetcher:
            builder = NotionPageBuilder(fetcher)
            properties, content = builder.build_page(trade_row)
    """

    # Pre-seeded ticker options in the Notion database.
    # New tickers need to be added via notion-update-data-source before page creation.
    KNOWN_TICKERS: Set[str] = {
        "AMD", "META", "MSFT", "SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "GOOG"
    }

    def __init__(self, fetcher: NotionDataFetcher):
        self.fetcher = fetcher
        self._known_tickers = set(self.KNOWN_TICKERS)
        self._pending_tickers: Set[str] = set()  # tickers that need adding

    def get_pending_tickers(self) -> Set[str]:
        """Return tickers that need to be added to the Notion database as select options."""
        return self._pending_tickers.copy()

    def register_ticker(self, ticker: str):
        """Mark a ticker as known (already exists in Notion database options)."""
        self._known_tickers.add(ticker.upper())
        self._pending_tickers.discard(ticker.upper())

    def collect_unknown_tickers(self, trades: List[Dict]) -> Set[str]:
        """
        Scan a list of trades and identify tickers not yet in the Notion database.
        Returns the set of unknown tickers that need to be added.
        """
        unknown = set()
        for trade in trades:
            ticker = trade.get('symbol', '').upper()
            if ticker and ticker not in self._known_tickers:
                unknown.add(ticker)
                self._pending_tickers.add(ticker)
        return unknown

    def build_page(self, trade: Dict) -> Tuple[Dict, str]:
        """
        Build Notion page properties and content for a single trade.

        Args:
            trade: Dict from journal_trades table (via fetch_trade or fetch_trades_by_date)

        Returns:
            (properties_dict, content_markdown_string)
        """
        trade_id = trade.get('trade_id', 'UNKNOWN')
        ticker = trade.get('symbol', '')
        trade_date = trade.get('trade_date')
        entry_time = trade.get('entry_time')
        exit_time = trade.get('exit_time')
        zone_id = trade.get('zone_id')

        # --- Fetch supporting data ---

        # Entry indicator bar
        entry_bar = None
        if ticker and trade_date and entry_time:
            try:
                entry_bar = self.fetcher.fetch_entry_indicator_bar(ticker, trade_date, entry_time)
            except Exception as e:
                logger.warning(f"[{trade_id}] Failed to fetch entry bar: {e}")

        # Ramp-up bars (15 before entry)
        ramp_bars = []
        if ticker and trade_date and entry_time:
            try:
                ramp_bars = self.fetcher.fetch_ramp_up_bars(ticker, trade_date, entry_time, 15)
            except Exception as e:
                logger.warning(f"[{trade_id}] Failed to fetch ramp-up bars: {e}")

        # Zone data
        zone = None
        if zone_id and ticker and trade_date:
            try:
                zone = self.fetcher.fetch_zone_data(zone_id, ticker, trade_date)
            except Exception as e:
                logger.warning(f"[{trade_id}] Failed to fetch zone data: {e}")

        # MFE/MAE (requires stop_price)
        mfe_mae = None
        if trade.get('stop_price') is not None:
            try:
                mfe_mae = self.fetcher.calculate_mfe_mae(trade)
            except Exception as e:
                logger.warning(f"[{trade_id}] Failed to calculate MFE/MAE: {e}")

        # R-level events (requires stop_price)
        r_events = []
        if trade.get('stop_price') is not None:
            try:
                r_events = self.fetcher.calculate_r_level_events(trade)
            except Exception as e:
                logger.warning(f"[{trade_id}] Failed to calculate R-level events: {e}")

        # Trade review (from flashcard training system)
        review = None
        try:
            review = self.fetcher.fetch_trade_review(trade_id)
        except Exception as e:
            logger.warning(f"[{trade_id}] Failed to fetch trade review: {e}")

        # --- Build properties ---
        properties = self._build_properties(trade, entry_bar, review)

        # --- Build content ---
        content = self._build_content(trade, entry_bar, ramp_bars, zone, mfe_mae, r_events, review)

        return properties, content

    def _build_properties(self, trade: Dict, entry_bar: Optional[Dict], review: Optional[Dict] = None) -> Dict:
        """
        Map trade data to Notion database property values.

        Property format follows the Notion MCP create-pages spec:
        - title: string
        - date: "date:{name}:start", "date:{name}:is_datetime"
        - select: string value
        - number: float value
        - checkbox: "__YES__" or "__NO__"
        - multi_select: skip (empty, user fills manually)
        """
        props = {}

        # Title (Trade ID)
        props["Trade ID"] = trade.get('trade_id', 'UNKNOWN')

        # Date
        trade_date = trade.get('trade_date')
        if trade_date:
            props["date:Date:start"] = str(trade_date)
            props["date:Date:is_datetime"] = 0

        # Ticker (select — will auto-create option if new)
        ticker = trade.get('symbol')
        if ticker:
            props["Ticker"] = ticker

        # Model (select — may be None for unreviewed trades)
        model = trade.get('model')
        if model:
            props["Model"] = model

        # Direction (select)
        direction = trade.get('direction')
        if direction:
            props["Direction"] = direction.upper()

        # Outcome (select)
        outcome = trade.get('outcome')
        if outcome and outcome in ('WIN', 'LOSS'):
            props["Outcome"] = outcome

        # P&L (R) (number)
        pnl_r = trade.get('pnl_r')
        if pnl_r is not None:
            try:
                props["P&L (R)"] = round(float(pnl_r), 2)
            except (TypeError, ValueError):
                pass

        # Health at Entry (number from entry indicator bar)
        if entry_bar and entry_bar.get('health_score') is not None:
            try:
                props["Health at Entry"] = int(entry_bar['health_score'])
            except (TypeError, ValueError):
                pass

        # Reviewed (checkbox — mark as reviewed if review data exists)
        if review:
            props["Reviewed"] = "__YES__"
        else:
            props["Reviewed"] = "__NO__"

        return props

    def _build_content(
        self,
        trade: Dict,
        entry_bar: Optional[Dict],
        ramp_bars: List[Dict],
        zone: Optional[Dict],
        mfe_mae: Optional[Dict],
        r_events: List[Dict],
        review: Optional[Dict] = None,
    ) -> str:
        """
        Assemble all 11 sections into a single Notion markdown string.
        Each section function handles its own gate conditions (showing
        placeholder callouts when data is missing).
        """
        sections = [
            section_trade_summary(trade),
            section_risk_management(trade, r_events),
            section_zone_context(zone, entry_bar),
            section_indicator_snapshot(entry_bar, trade),
            section_excursion_analysis(mfe_mae, trade),
            section_r_level_progression(r_events),
            section_m1_rampup(ramp_bars),
            section_indicator_refinement(trade),
            section_charts(),
            section_trade_assessment(review),
            section_journal_notes(review),
        ]

        return "\n\n".join(sections)

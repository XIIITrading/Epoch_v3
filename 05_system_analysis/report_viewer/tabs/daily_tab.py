"""
EPOCH TRADING SYSTEM - Daily Tab
XIII Trading LLC

Single-day analysis filtered by anchor date.
"""
from tabs.filtered_tab import FilteredTab


class DailyTab(FilteredTab):
    def __init__(self):
        super().__init__(tab_label="Daily")

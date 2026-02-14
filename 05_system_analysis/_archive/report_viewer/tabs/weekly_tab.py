"""
EPOCH TRADING SYSTEM - Weekly Tab
XIII Trading LLC

7-day rolling analysis ending at anchor date.
"""
from tabs.filtered_tab import FilteredTab


class WeeklyTab(FilteredTab):
    def __init__(self):
        super().__init__(tab_label="Weekly")

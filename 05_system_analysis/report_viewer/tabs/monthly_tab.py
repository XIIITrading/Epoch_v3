"""
EPOCH TRADING SYSTEM - Monthly Tab
XIII Trading LLC

30-day rolling analysis ending at anchor date.
"""
from tabs.filtered_tab import FilteredTab


class MonthlyTab(FilteredTab):
    def __init__(self):
        super().__init__(tab_label="Monthly")

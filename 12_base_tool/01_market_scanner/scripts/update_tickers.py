#!/usr/bin/env python
"""
Script to update ticker lists from various sources.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from data import ticker_manager, TickerList

def fetch_sp500_from_wikipedia():
    """Fetch current S&P 500 list from Wikipedia."""
    print("Fetching S&P 500 list from Wikipedia...")
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    
    try:
        tables = pd.read_html(url)
        df = tables[0]
        
        # Extract and clean tickers
        tickers = df['Symbol'].str.strip().tolist()
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        tickers = sorted(tickers)
        
        print(f"Successfully fetched {len(tickers)} tickers")
        return tickers
        
    except Exception as e:
        print(f"Error fetching S&P 500 list: {e}")
        return None

def main():
    """Main update function."""
    parser = argparse.ArgumentParser(description='Update ticker lists')
    parser.add_argument('--list', type=str, default='sp500',
                       choices=['sp500', 'nasdaq100', 'russell2000', 'dow30'],
                       help='Ticker list to update')
    
    args = parser.parse_args()
    
    print(f"Updating {args.list.upper()} ticker list")
    print("=" * 50)
    
    # Get current tickers
    try:
        current_tickers = ticker_manager.get_tickers(TickerList(args.list), check_staleness=False)
        print(f"Current list has {len(current_tickers)} tickers")
    except:
        current_tickers = []
        print("No existing ticker list found")
    
    # Fetch new tickers based on list type
    if args.list == 'sp500':
        new_tickers = fetch_sp500_from_wikipedia()
    else:
        print(f"Update method for {args.list} not implemented yet")
        return
    
    if not new_tickers:
        print("Failed to fetch new ticker list")
        return
    
    # Compare lists
    current_set = set(current_tickers)
    new_set = set(new_tickers)
    
    added = new_set - current_set
    removed = current_set - new_set
    
    print("\nChanges detected:")
    print("=" * 50)
    
    if added:
        print(f"\nAdded ({len(added)} tickers):")
        for ticker in sorted(added):
            print(f"  + {ticker}")
    
    if removed:
        print(f"\nRemoved ({len(removed)} tickers):")
        for ticker in sorted(removed):
            print(f"  - {ticker}")
    
    if not added and not removed:
        print("\nNo changes detected - list is up to date!")
        return
    
    # Confirm update
    response = input("\nApply these changes? (y/n): ").lower().strip()
    if response == 'y':
        ticker_manager.update_tickers(TickerList(args.list), new_tickers)
        print(f"\n✅ {args.list.upper()} list updated successfully!")
        print(f"   Total tickers: {len(new_tickers)}")
    else:
        print("\nUpdate cancelled.")

if __name__ == "__main__":
    main()
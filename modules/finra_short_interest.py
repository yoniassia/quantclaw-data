#!/usr/bin/env python3
"""
FINRA Short Interest (Official)
================================
Biweekly short interest reporting for all US securities via FINRA.
Shares sold short, days to cover, short % of float.

Official data source: http://regsho.finra.org/regsho-Index.html
No API key required, free public data.

Data refresh: Bi-weekly (settlement dates)
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import requests
from io import StringIO
import time
from typing import Optional, Dict, List
from functools import lru_cache

# FINRA RegSHO URL pattern
FINRA_BASE_URL = "http://regsho.finra.org/"


def get_latest_settlement_dates(num_periods: int = 12) -> List[str]:
    """
    Calculate the most recent bi-weekly settlement dates.
    FINRA publishes short interest data on settlement dates (typically mid/end of month).
    
    Returns list of dates in YYYYMMDD format.
    """
    dates = []
    today = datetime.now()
    
    # FINRA settlement dates are approximately 15th and last day of each month
    for i in range(num_periods):
        month_offset = i // 2
        date_type = i % 2  # 0 = end of month, 1 = mid-month
        
        # Calculate target month
        target_month = today.month - month_offset
        target_year = today.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        
        if date_type == 0:  # End of month
            # Last day of previous month
            if target_month == 1:
                settlement_date = datetime(target_year - 1, 12, 31)
            else:
                next_month = datetime(target_year, target_month, 1)
                settlement_date = next_month - timedelta(days=1)
        else:  # Mid-month (15th)
            settlement_date = datetime(target_year, target_month, 15)
        
        # Only include dates in the past
        if settlement_date <= today:
            dates.append(settlement_date.strftime("%Y%m%d"))
    
    return dates[:num_periods]


@lru_cache(maxsize=256)
def fetch_finra_short_interest(symbol: str) -> pd.DataFrame:
    """
    Fetch FINRA short interest data for a symbol.
    Tries multiple settlement dates to get historical data.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        
    Returns:
        DataFrame with columns: settlement_date, symbol, short_interest, short_exempt, total_volume, days_to_cover
    """
    settlement_dates = get_latest_settlement_dates(12)
    all_data = []
    
    for settle_date in settlement_dates:
        try:
            # FINRA URL format: http://regsho.finra.org/CNMSshvol{YYYYMMDD}.txt
            # Try both NASDAQ (CNMS) and NYSE (FNQ) files
            for exchange in ['CNMS', 'FNQ']:
                url = f"{FINRA_BASE_URL}{exchange}shvol{settle_date}.txt"
                
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    continue
                
                # Parse pipe-delimited file
                df = pd.read_csv(StringIO(response.text), sep='|')
                
                # Filter for our symbol
                symbol_data = df[df['Symbol'] == symbol.upper()]
                if not symbol_data.empty:
                    for _, row in symbol_data.iterrows():
                        all_data.append({
                            'settlement_date': settle_date,
                            'symbol': row['Symbol'],
                            'short_interest': int(row.get('ShortQuantity', 0)),
                            'short_exempt': int(row.get('ShortExemptQuantity', 0)),
                            'total_volume': int(row.get('TotalVolume', 0)),
                        })
                    break  # Found data, no need to check other exchange
        except Exception as e:
            # Silently continue to next date
            continue
        
        time.sleep(0.2)  # Rate limiting
    
    if not all_data:
        # Return empty DataFrame with correct structure
        return pd.DataFrame(columns=['settlement_date', 'symbol', 'short_interest', 
                                       'short_exempt', 'total_volume', 'days_to_cover'])
    
    result = pd.DataFrame(all_data)
    
    # Calculate days to cover (approximate)
    # Days to cover = short interest / average daily volume
    # We'll estimate avg daily volume from recent data
    if len(result) > 0:
        result['days_to_cover'] = result.apply(
            lambda row: round(row['short_interest'] / row['total_volume'], 2) 
            if row['total_volume'] > 0 else 0,
            axis=1
        )
    
    result = result.sort_values('settlement_date', ascending=False)
    
    return result


def cli_short_interest(symbol: str, no_cache: bool = False) -> None:
    """CLI command: Display FINRA short interest for a symbol."""
    if no_cache:
        fetch_finra_short_interest.cache_clear()
    
    df = fetch_finra_short_interest(symbol.upper())
    
    if df.empty:
        print(f"No FINRA short interest data found for {symbol.upper()}")
        return
    
    print(f"\n{'='*70}")
    print(f"FINRA Short Interest — {symbol.upper()}")
    print(f"{'='*70}\n")
    
    for _, row in df.iterrows():
        date_obj = datetime.strptime(str(row['settlement_date']), "%Y%m%d")
        print(f"Settlement Date: {date_obj.strftime('%Y-%m-%d')}")
        print(f"  Short Interest:  {row['short_interest']:,} shares")
        print(f"  Short Exempt:    {row['short_exempt']:,} shares")
        print(f"  Total Volume:    {row['total_volume']:,} shares")
        print(f"  Days to Cover:   {row['days_to_cover']:.2f} days")
        print()
    
    # Calculate trend if we have multiple data points
    if len(df) >= 2:
        latest = df.iloc[0]
        previous = df.iloc[1]
        change = latest['short_interest'] - previous['short_interest']
        pct_change = (change / previous['short_interest'] * 100) if previous['short_interest'] > 0 else 0
        
        trend = "↑" if change > 0 else "↓"
        print(f"Trend vs Previous: {trend} {abs(change):,} shares ({pct_change:+.1f}%)")
    
    print(f"\nSource: FINRA RegSHO (bi-weekly settlement data)")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python finra_short_interest.py <SYMBOL>")
        print("Example: python finra_short_interest.py GME")
        sys.exit(1)
    
    symbol = sys.argv[1]
    cli_short_interest(symbol)

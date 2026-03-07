#!/usr/bin/env python3
"""
OpenInsider API — Insider Trading Activity Module

Core OpenInsider integration for tracking insider trading activity including:
- Latest insider buys and sells
- Insider activity by ticker
- Cluster buys (multiple insiders buying same stock)
- SEC Form 4 filings tracking

Source: https://openinsider.com
Category: Insider Trading & Corporate Actions
Free tier: True (no API key required, scraper-based)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# OpenInsider Configuration
OPENINSIDER_BASE_URL = "http://openinsider.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


def parse_insider_table(html: str) -> List[Dict]:
    """
    Parse OpenInsider HTML table into structured data.
    
    Args:
        html: Raw HTML content containing insider trading table
    
    Returns:
        List of dicts with insider trading data
    
    Example:
        >>> trades = parse_insider_table(html_content)
        >>> print(f"Found {len(trades)} trades")
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', {'class': 'tinytable'})
        
        if not table:
            return []
        
        # Check if table has company name column by counting header columns
        # Normalize header text to handle non-breaking spaces
        header_row = table.find('tr')
        headers = [th.text.strip().replace('\xa0', ' ') for th in header_row.find_all('th')]
        has_company = 'Company Name' in headers
        
        trades = []
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 12:
                continue
            
            try:
                if has_company:
                    # Format with company name column (buy/sell screeners)
                    # [0]=X, [1]=Filing, [2]=Trade, [3]=Ticker, [4]=Company,
                    # [5]=Insider, [6]=Title, [7]=Type, [8]=Price, [9]=Qty,
                    # [10]=Owned, [11]=ΔOwn, [12]=Value
                    filing_date = cols[1].text.strip()
                    trade_date = cols[2].text.strip()
                    ticker_elem = cols[3].find('a')
                    ticker = ticker_elem.text.strip() if ticker_elem else cols[3].text.strip()
                    company_elem = cols[4].find('a')
                    company = company_elem.text.strip() if company_elem else cols[4].text.strip()
                    insider_elem = cols[5].find('a')
                    insider = insider_elem.text.strip() if insider_elem else cols[5].text.strip()
                    title = cols[6].text.strip()
                    trade_type = cols[7].text.strip()
                    price = cols[8].text.strip()
                    qty = cols[9].text.strip()
                    owned = cols[10].text.strip()
                    delta_own = cols[11].text.strip()
                    value = cols[12].text.strip()
                else:
                    # Format without company name (ticker-specific screener)
                    # [0]=X, [1]=Filing, [2]=Trade, [3]=Ticker, [4]=Insider,
                    # [5]=Title, [6]=Type, [7]=Price, [8]=Qty, [9]=Owned,
                    # [10]=ΔOwn, [11]=Value
                    filing_date = cols[1].text.strip()
                    trade_date = cols[2].text.strip()
                    ticker_elem = cols[3].find('a')
                    ticker = ticker_elem.text.strip() if ticker_elem else cols[3].text.strip()
                    company = ''  # No company column in this format
                    insider_elem = cols[4].find('a')
                    insider = insider_elem.text.strip() if insider_elem else cols[4].text.strip()
                    title = cols[5].text.strip()
                    trade_type = cols[6].text.strip()
                    price = cols[7].text.strip()
                    qty = cols[8].text.strip()
                    owned = cols[9].text.strip()
                    delta_own = cols[10].text.strip()
                    value = cols[11].text.strip()
                
                trade = {
                    'filing_date': filing_date,
                    'trade_date': trade_date,
                    'ticker': ticker,
                    'company': company,
                    'insider_name': insider,
                    'insider_title': title,
                    'trade_type': trade_type,
                    'price': price,
                    'qty': qty,
                    'owned': owned,
                    'delta_own': delta_own,
                    'value': value
                }
                trades.append(trade)
                
            except Exception as e:
                # Skip malformed rows
                continue
        
        return trades
        
    except Exception as e:
        return []


def get_latest_buys(days: int = 7, min_value: int = 0) -> List[Dict]:
    """
    Get recent insider purchase transactions.
    
    Args:
        days: Number of days to look back (default: 7)
        min_value: Minimum transaction value in USD (default: 0)
    
    Returns:
        List of insider buy transactions
    
    Example:
        >>> buys = get_latest_buys(days=7)
        >>> print(f"Found {len(buys)} insider buys")
    """
    try:
        url = f"{OPENINSIDER_BASE_URL}/screener"
        params = {
            's': '',
            'o': '',
            'pl': '',
            'ph': '',
            'st': 0,
            'fd': days,
            'td': 0,
            'ta': 1,  # 1 = buys
            'hd': 0,
            'is498': 'true'
        }
        
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        trades = parse_insider_table(response.text)
        
        # Filter by minimum value if specified
        if min_value > 0:
            filtered_trades = []
            for trade in trades:
                try:
                    value_str = trade.get('value', '').replace(',', '').replace('$', '').replace('+', '')
                    if value_str and float(value_str) >= min_value:
                        filtered_trades.append(trade)
                except:
                    continue
            trades = filtered_trades
        
        return trades
        
    except requests.exceptions.RequestException as e:
        return [{'error': str(e)}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}'}]


def get_latest_sells(days: int = 7, min_value: int = 0) -> List[Dict]:
    """
    Get recent insider sale transactions.
    
    Args:
        days: Number of days to look back (default: 7)
        min_value: Minimum transaction value in USD (default: 0)
    
    Returns:
        List of insider sell transactions
    
    Example:
        >>> sells = get_latest_sells(days=7)
        >>> print(f"Found {len(sells)} insider sells")
    """
    try:
        url = f"{OPENINSIDER_BASE_URL}/screener"
        params = {
            's': '',
            'o': '',
            'pl': '',
            'ph': '',
            'st': 0,
            'fd': days,
            'td': 0,
            'ta': 2,  # 2 = sells
            'hd': 0,
            'is498': 'true'
        }
        
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        trades = parse_insider_table(response.text)
        
        # Filter by minimum value if specified
        if min_value > 0:
            filtered_trades = []
            for trade in trades:
                try:
                    value_str = trade.get('value', '').replace(',', '').replace('$', '').replace('-', '')
                    if value_str and abs(float(value_str)) >= min_value:
                        filtered_trades.append(trade)
                except:
                    continue
            trades = filtered_trades
        
        return trades
        
    except requests.exceptions.RequestException as e:
        return [{'error': str(e)}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}'}]


def get_insider_activity(ticker: str = 'AAPL', days: int = 365) -> List[Dict]:
    """
    Get insider trading activity for a specific stock ticker.
    
    Args:
        ticker: Stock ticker symbol (default: 'AAPL')
        days: Number of days to look back (default: 365)
    
    Returns:
        List of insider trades for the specified ticker
    
    Example:
        >>> activity = get_insider_activity('AAPL', days=90)
        >>> print(f"AAPL had {len(activity)} insider trades in 90 days")
    """
    try:
        url = f"{OPENINSIDER_BASE_URL}/screener"
        params = {
            's': ticker.upper(),
            'o': '',
            'pl': '',
            'ph': '',
            'st': 0,
            'fd': days
        }
        
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        trades = parse_insider_table(response.text)
        
        # Add ticker metadata
        for trade in trades:
            trade['query_ticker'] = ticker.upper()
            trade['query_days'] = days
        
        return trades
        
    except requests.exceptions.RequestException as e:
        return [{'error': str(e), 'ticker': ticker}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}', 'ticker': ticker}]


def get_cluster_buys() -> List[Dict]:
    """
    Get cluster buys (multiple insiders buying the same stock).
    
    Returns:
        List of stocks with multiple insider buys
    
    Example:
        >>> clusters = get_cluster_buys()
        >>> print(f"Found {len(clusters)} cluster buy signals")
    """
    try:
        url = f"{OPENINSIDER_BASE_URL}/latest-cluster-buys"
        
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        trades = parse_insider_table(response.text)
        
        # Add cluster metadata
        for trade in trades:
            trade['is_cluster_buy'] = True
        
        return trades
        
    except requests.exceptions.RequestException as e:
        return [{'error': str(e)}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}'}]


# Convenience exports
__all__ = [
    'get_latest_buys',
    'get_latest_sells',
    'get_insider_activity',
    'get_cluster_buys',
    'parse_insider_table'
]

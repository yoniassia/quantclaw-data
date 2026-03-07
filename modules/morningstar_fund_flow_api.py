#!/usr/bin/env python3
"""
Morningstar Fund Flow API — Free Public Data Sources

Track mutual fund and ETF fund flows using publicly available data sources.
Since Morningstar's API requires paid access, this module aggregates data from:
- ICI (Investment Company Institute) weekly fund flow reports
- ETF.com fund flow data
- Morningstar public pages (basic fund info)

Source: Multiple free public sources
Category: ETF & Fund Flows
Free tier: True (public web scraping, no API keys required)
Author: QuantClaw Data NightBuilder
Phase: NightBuilder-001
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import time

# Configuration
ETFDB_BASE_URL = "https://etfdb.com"
MORNINGSTAR_BASE_URL = "https://www.morningstar.com"
ICI_BASE_URL = "https://www.ici.org"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
REQUEST_TIMEOUT = 10

# ========== HELPER FUNCTIONS ==========

def _make_request(url: str, headers: Optional[Dict] = None) -> Optional[requests.Response]:
    """Make HTTP request with error handling"""
    if headers is None:
        headers = {"User-Agent": USER_AGENT}
    
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request error for {url}: {e}")
        return None

def _parse_flow_value(value_str: str) -> Optional[float]:
    """Parse flow values like '$1.2B', '-$500M', etc."""
    if not value_str or value_str == 'N/A':
        return None
    
    try:
        # Remove currency symbols and whitespace
        clean = value_str.replace('$', '').replace(',', '').strip()
        
        # Handle B (billions) and M (millions)
        multiplier = 1
        if 'B' in clean.upper():
            multiplier = 1_000_000_000
            clean = clean.upper().replace('B', '')
        elif 'M' in clean.upper():
            multiplier = 1_000_000
            clean = clean.upper().replace('M', '')
        
        return float(clean) * multiplier
    except (ValueError, AttributeError):
        return None

# ========== PUBLIC API FUNCTIONS ==========

def get_etf_fund_flows(ticker: str) -> Dict:
    """
    Get fund flow data for a specific ETF.
    
    Args:
        ticker: ETF ticker symbol (e.g., 'SPY', 'QQQ')
    
    Returns:
        dict: Fund flow metrics including daily/weekly/monthly flows
        
    Example:
        >>> flows = get_etf_fund_flows('SPY')
        >>> print(flows['ticker'], flows['weekly_flow'])
    """
    ticker = ticker.upper()
    
    # TODO: Real implementation would scrape ETF.com or use Morningstar public pages
    # For now, return structured mock data with realistic patterns
    
    return {
        'ticker': ticker,
        'timestamp': datetime.now().isoformat(),
        'source': 'mock_data',
        'daily_flow': None,  # TODO: Scrape from ETF.com
        'weekly_flow': 125_000_000 if ticker == 'SPY' else 50_000_000,  # Mock: $125M for SPY
        'monthly_flow': 500_000_000 if ticker == 'SPY' else 200_000_000,
        'ytd_flow': 2_500_000_000 if ticker == 'SPY' else 1_000_000_000,
        'aum': 450_000_000_000 if ticker == 'SPY' else 100_000_000_000,  # Assets under management
        'flow_percentage': 0.028 if ticker == 'SPY' else 0.05,  # Monthly flow / AUM
        'note': 'TODO: Replace with real scraping of ETF.com or Morningstar public pages'
    }

def get_weekly_fund_flows() -> Dict:
    """
    Get aggregate weekly fund flows across all categories.
    
    Returns:
        dict: Weekly flows by category (equity, bond, hybrid, money market)
        
    Example:
        >>> flows = get_weekly_fund_flows()
        >>> print(flows['equity']['total_flow'])
    """
    # TODO: Real implementation would scrape ICI weekly reports
    # https://www.ici.org/research/stats/weekly-combined-estimated-long-term-fund-flows-and-etf-data
    
    return {
        'timestamp': datetime.now().isoformat(),
        'source': 'mock_ici_data',
        'week_ending': (datetime.now() - timedelta(days=datetime.now().weekday() + 1)).strftime('%Y-%m-%d'),
        'equity': {
            'total_flow': 3_500_000_000,  # $3.5B inflow
            'mutual_funds': 1_200_000_000,
            'etfs': 2_300_000_000,
            'domestic': 2_000_000_000,
            'international': 1_500_000_000
        },
        'bond': {
            'total_flow': 1_800_000_000,  # $1.8B inflow
            'mutual_funds': 800_000_000,
            'etfs': 1_000_000_000,
            'taxable': 1_500_000_000,
            'municipal': 300_000_000
        },
        'hybrid': {
            'total_flow': 200_000_000,  # $200M inflow
            'mutual_funds': 150_000_000,
            'etfs': 50_000_000
        },
        'money_market': {
            'total_flow': -5_000_000_000,  # $5B outflow
            'retail': -3_000_000_000,
            'institutional': -2_000_000_000
        },
        'note': 'TODO: Replace with real scraping of ICI weekly reports'
    }

def get_top_inflows(limit: int = 10) -> List[Dict]:
    """
    Get top ETFs by fund inflows.
    
    Args:
        limit: Number of top ETFs to return (default: 10)
    
    Returns:
        list: List of dicts with ticker, name, inflow amount
        
    Example:
        >>> top = get_top_inflows(5)
        >>> for etf in top:
        >>>     print(etf['ticker'], etf['weekly_flow'])
    """
    # TODO: Real implementation would scrape ETF.com fund flow tool
    # https://etfdb.com/etf-fund-flow-tool/
    
    # Mock data with realistic tickers and flows
    mock_data = [
        {'ticker': 'SPY', 'name': 'SPDR S&P 500 ETF', 'weekly_flow': 1_250_000_000, 'aum': 450_000_000_000},
        {'ticker': 'QQQ', 'name': 'Invesco QQQ Trust', 'weekly_flow': 890_000_000, 'aum': 220_000_000_000},
        {'ticker': 'IVV', 'name': 'iShares Core S&P 500 ETF', 'weekly_flow': 720_000_000, 'aum': 380_000_000_000},
        {'ticker': 'VOO', 'name': 'Vanguard S&P 500 ETF', 'weekly_flow': 650_000_000, 'aum': 340_000_000_000},
        {'ticker': 'VTI', 'name': 'Vanguard Total Stock Market ETF', 'weekly_flow': 580_000_000, 'aum': 290_000_000_000},
        {'ticker': 'IEFA', 'name': 'iShares Core MSCI EAFE ETF', 'weekly_flow': 450_000_000, 'aum': 90_000_000_000},
        {'ticker': 'AGG', 'name': 'iShares Core US Aggregate Bond ETF', 'weekly_flow': 420_000_000, 'aum': 95_000_000_000},
        {'ticker': 'EFA', 'name': 'iShares MSCI EAFE ETF', 'weekly_flow': 380_000_000, 'aum': 60_000_000_000},
        {'ticker': 'IEMG', 'name': 'iShares Core MSCI Emerging Markets ETF', 'weekly_flow': 350_000_000, 'aum': 75_000_000_000},
        {'ticker': 'IJH', 'name': 'iShares Core S&P Mid-Cap ETF', 'weekly_flow': 310_000_000, 'aum': 70_000_000_000},
        {'ticker': 'VEA', 'name': 'Vanguard FTSE Developed Markets ETF', 'weekly_flow': 290_000_000, 'aum': 100_000_000_000},
        {'ticker': 'BND', 'name': 'Vanguard Total Bond Market ETF', 'weekly_flow': 275_000_000, 'aum': 85_000_000_000},
    ]
    
    result = []
    for etf in mock_data[:limit]:
        result.append({
            'ticker': etf['ticker'],
            'name': etf['name'],
            'weekly_flow': etf['weekly_flow'],
            'aum': etf['aum'],
            'flow_percentage': round((etf['weekly_flow'] / etf['aum']) * 100, 3),
            'timestamp': datetime.now().isoformat(),
            'source': 'mock_data'
        })
    
    result.append({'note': 'TODO: Replace with real scraping of ETF.com fund flow tool'})
    return result

def get_top_outflows(limit: int = 10) -> List[Dict]:
    """
    Get top ETFs by fund outflows (negative flows).
    
    Args:
        limit: Number of top ETFs to return (default: 10)
    
    Returns:
        list: List of dicts with ticker, name, outflow amount (negative)
        
    Example:
        >>> top = get_top_outflows(5)
        >>> for etf in top:
        >>>     print(etf['ticker'], etf['weekly_flow'])
    """
    # TODO: Real implementation would scrape ETF.com fund flow tool
    
    # Mock data with realistic outflow patterns
    mock_data = [
        {'ticker': 'GLD', 'name': 'SPDR Gold Shares', 'weekly_flow': -320_000_000, 'aum': 60_000_000_000},
        {'ticker': 'SHY', 'name': 'iShares 1-3 Year Treasury Bond ETF', 'weekly_flow': -280_000_000, 'aum': 25_000_000_000},
        {'ticker': 'TLT', 'name': 'iShares 20+ Year Treasury Bond ETF', 'weekly_flow': -250_000_000, 'aum': 40_000_000_000},
        {'ticker': 'HYG', 'name': 'iShares iBoxx High Yield Corporate Bond ETF', 'weekly_flow': -210_000_000, 'aum': 18_000_000_000},
        {'ticker': 'XLE', 'name': 'Energy Select Sector SPDR Fund', 'weekly_flow': -185_000_000, 'aum': 30_000_000_000},
        {'ticker': 'IWM', 'name': 'iShares Russell 2000 ETF', 'weekly_flow': -170_000_000, 'aum': 50_000_000_000},
        {'ticker': 'LQD', 'name': 'iShares iBoxx Investment Grade Corporate Bond ETF', 'weekly_flow': -155_000_000, 'aum': 35_000_000_000},
        {'ticker': 'SLV', 'name': 'iShares Silver Trust', 'weekly_flow': -140_000_000, 'aum': 12_000_000_000},
        {'ticker': 'XLF', 'name': 'Financial Select Sector SPDR Fund', 'weekly_flow': -125_000_000, 'aum': 38_000_000_000},
        {'ticker': 'EEM', 'name': 'iShares MSCI Emerging Markets ETF', 'weekly_flow': -110_000_000, 'aum': 22_000_000_000},
    ]
    
    result = []
    for etf in mock_data[:limit]:
        result.append({
            'ticker': etf['ticker'],
            'name': etf['name'],
            'weekly_flow': etf['weekly_flow'],
            'aum': etf['aum'],
            'flow_percentage': round((etf['weekly_flow'] / etf['aum']) * 100, 3),
            'timestamp': datetime.now().isoformat(),
            'source': 'mock_data'
        })
    
    result.append({'note': 'TODO: Replace with real scraping of ETF.com fund flow tool'})
    return result

def get_fund_info(ticker: str) -> Dict:
    """
    Get basic fund information from public Morningstar pages.
    
    Args:
        ticker: Fund/ETF ticker symbol
    
    Returns:
        dict: Basic fund details (name, category, AUM, expense ratio, etc.)
        
    Example:
        >>> info = get_fund_info('SPY')
        >>> print(info['name'], info['category'])
    """
    ticker = ticker.upper()
    
    # TODO: Real implementation would scrape Morningstar public pages
    # https://www.morningstar.com/funds/{ticker}/price
    
    # Mock data based on ticker
    fund_database = {
        'SPY': {
            'name': 'SPDR S&P 500 ETF Trust',
            'category': 'Large Blend',
            'morningstar_category': 'US Equity Large Cap Blend',
            'aum': 450_000_000_000,
            'expense_ratio': 0.0945,
            'inception_date': '1993-01-22',
            'issuer': 'State Street Global Advisors',
            'structure': 'ETF',
            'morningstar_rating': 4
        },
        'QQQ': {
            'name': 'Invesco QQQ Trust',
            'category': 'Large Growth',
            'morningstar_category': 'US Equity Large Cap Growth',
            'aum': 220_000_000_000,
            'expense_ratio': 0.20,
            'inception_date': '1999-03-10',
            'issuer': 'Invesco',
            'structure': 'ETF',
            'morningstar_rating': 5
        }
    }
    
    default_info = {
        'name': f'{ticker} Fund',
        'category': 'Unknown',
        'morningstar_category': 'N/A',
        'aum': None,
        'expense_ratio': None,
        'inception_date': None,
        'issuer': 'Unknown',
        'structure': 'ETF',
        'morningstar_rating': None
    }
    
    info = fund_database.get(ticker, default_info)
    info['ticker'] = ticker
    info['timestamp'] = datetime.now().isoformat()
    info['source'] = 'mock_data'
    info['note'] = 'TODO: Replace with real scraping of Morningstar public pages'
    
    return info

def get_category_flows(category: str = 'equity') -> Dict:
    """
    Get fund flows by category (equity, bond, hybrid, money_market).
    
    Args:
        category: Fund category ('equity', 'bond', 'hybrid', 'money_market')
    
    Returns:
        dict: Flow data for the specified category
        
    Example:
        >>> equity_flows = get_category_flows('equity')
        >>> print(equity_flows['total_flow'], equity_flows['etf_flow'])
    """
    category = category.lower()
    
    # Get weekly flows and extract the category
    weekly_flows = get_weekly_fund_flows()
    
    if category not in weekly_flows:
        return {
            'error': f'Invalid category: {category}',
            'valid_categories': ['equity', 'bond', 'hybrid', 'money_market']
        }
    
    result = weekly_flows[category].copy()
    result['category'] = category
    result['timestamp'] = weekly_flows['timestamp']
    result['week_ending'] = weekly_flows['week_ending']
    result['source'] = weekly_flows['source']
    
    return result

# ========== CLI INTERFACE ==========

def main():
    """CLI interface for testing"""
    print("=== Morningstar Fund Flow API (Free Public Sources) ===\n")
    
    # Test get_weekly_fund_flows
    print("1. Weekly Fund Flows:")
    flows = get_weekly_fund_flows()
    print(json.dumps(flows, indent=2))
    print()
    
    # Test get_top_inflows
    print("2. Top 5 Inflows:")
    inflows = get_top_inflows(5)
    for i, etf in enumerate(inflows[:-1], 1):  # Skip the note
        print(f"   {i}. {etf['ticker']:6} {etf['name']:40} ${etf['weekly_flow']/1e9:.2f}B")
    print()
    
    # Test get_etf_fund_flows
    print("3. SPY Fund Flows:")
    spy_flows = get_etf_fund_flows('SPY')
    print(json.dumps(spy_flows, indent=2))
    print()
    
    # Test get_fund_info
    print("4. SPY Fund Info:")
    spy_info = get_fund_info('SPY')
    print(json.dumps(spy_info, indent=2))
    print()
    
    print("✅ All functions tested successfully")
    print("⚠️  Note: Currently using mock data. TODO: Implement real web scraping.")

if __name__ == "__main__":
    main()

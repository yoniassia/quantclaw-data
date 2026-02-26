#!/usr/bin/env python3
"""
BSE/NSE India Exchange Data
Bombay Stock Exchange (BSE) and National Stock Exchange (NSE) of India
Fetches Sensex, Nifty indices, FII/DII flows, and market statistics
Data source: Free APIs via Yahoo Finance + NSE India public data
"""

import yfinance as yf
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import sys
from typing import Dict, List, Optional

# NSE/BSE index symbols for Yahoo Finance
INDEX_SYMBOLS = {
    'SENSEX': '^BSESN',  # BSE Sensex 30
    'NIFTY50': '^NSEI',  # NSE Nifty 50
    'NIFTY_NEXT50': '^NSEMDCP50',  # Nifty Next 50
    'NIFTY_BANK': '^NSEBANK',  # Nifty Bank index
    'NIFTY_IT': 'NIFTY_IT.NS',  # Nifty IT index
    'BSE_MIDCAP': '^BSEMID',  # BSE Midcap
    'BSE_SMALLCAP': '^BSESML',  # BSE Smallcap
}

NSE_BASE_URL = "https://www.nseindia.com"
BSE_BASE_URL = "https://www.bseindia.com"

def get_index_data(index_name: str = 'NIFTY50', period: str = '1d') -> Dict:
    """
    Fetch Indian index data via Yahoo Finance
    
    Args:
        index_name: One of SENSEX, NIFTY50, NIFTY_NEXT50, NIFTY_BANK, etc.
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    
    Returns:
        Dictionary with index data
    """
    if index_name not in INDEX_SYMBOLS:
        return {
            'error': f'Unknown index: {index_name}',
            'available': list(INDEX_SYMBOLS.keys())
        }
    
    symbol = INDEX_SYMBOLS[index_name]
    
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        info = ticker.info
        
        if hist.empty:
            return {
                'error': 'No data available',
                'symbol': symbol,
                'index': index_name
            }
        
        latest = hist.iloc[-1]
        previous = hist.iloc[-2] if len(hist) > 1 else latest
        
        return {
            'index': index_name,
            'symbol': symbol,
            'current_price': round(latest['Close'], 2),
            'open': round(latest['Open'], 2),
            'high': round(latest['High'], 2),
            'low': round(latest['Low'], 2),
            'previous_close': round(previous['Close'], 2),
            'change': round(latest['Close'] - previous['Close'], 2),
            'change_pct': round((latest['Close'] - previous['Close']) / previous['Close'] * 100, 2),
            'volume': int(latest['Volume']),
            'date': latest.name.strftime('%Y-%m-%d'),
            'year_high': round(info.get('fiftyTwoWeekHigh', 0), 2) if info else 0,
            'year_low': round(info.get('fiftyTwoWeekLow', 0), 2) if info else 0,
            'pe_ratio': round(info.get('trailingPE', 0), 2) if info else None,
            'dividend_yield': round(info.get('dividendYield', 0) * 100, 2) if info and info.get('dividendYield') else None,
            'market_cap': info.get('marketCap') if info else None,
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'symbol': symbol,
            'index': index_name
        }

def get_sensex() -> Dict:
    """Get BSE Sensex 30 index data"""
    return get_index_data('SENSEX')

def get_nifty() -> Dict:
    """Get NSE Nifty 50 index data"""
    return get_index_data('NIFTY50')

def get_nifty_bank() -> Dict:
    """Get Nifty Bank index data"""
    return get_index_data('NIFTY_BANK')

def get_nifty_it() -> Dict:
    """Get Nifty IT index data"""
    return get_index_data('NIFTY_IT')

def get_all_indices(period: str = '1d') -> Dict:
    """
    Get all major Indian indices in one call
    """
    indices = {}
    for name in INDEX_SYMBOLS.keys():
        indices[name] = get_index_data(name, period)
    
    return {
        'timestamp': datetime.now().isoformat(),
        'period': period,
        'indices': indices
    }

def get_fii_dii_flows_synthetic() -> Dict:
    """
    Get FII/DII flows (Foreign Institutional Investors / Domestic Institutional Investors)
    
    NOTE: Real FII/DII data requires NSE authenticated API or scraping.
    This provides synthetic/estimated data based on market movements.
    For production, integrate with NSE official data or paid data providers.
    """
    try:
        # Get Nifty and Sensex recent performance as proxy
        nifty = get_index_data('NIFTY50', period='5d')
        sensex = get_index_data('SENSEX', period='5d')
        
        # Synthetic estimation based on price movements
        # (In production, use actual NSE FII/DII data from authenticated sources)
        nifty_change = nifty.get('change_pct', 0)
        
        # Rough estimation: strong positive = FII buying, negative = selling
        fii_estimate = nifty_change * 500  # Rough INR crores proxy
        dii_estimate = -nifty_change * 300  # DIIs often opposite to FIIs
        
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'fii_equity_flows_cr': round(fii_estimate, 2),
            'dii_equity_flows_cr': round(dii_estimate, 2),
            'net_flows_cr': round(fii_estimate + dii_estimate, 2),
            'nifty_change_pct': nifty_change,
            'sensex_change_pct': sensex.get('change_pct', 0),
            'note': 'Synthetic estimate based on market movements. Use NSE official data for accuracy.',
            'data_source': 'Estimated from index movements (not official NSE data)'
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'note': 'FII/DII data unavailable. Requires NSE authenticated API.'
        }

def get_market_breadth_synthetic() -> Dict:
    """
    Market breadth indicators: advances/declines, delivery percentage
    
    NOTE: Real breadth data requires NSE/BSE live feeds.
    This provides synthetic estimates based on index sector performance.
    """
    try:
        # Get multiple indices to estimate breadth
        nifty = get_index_data('NIFTY50', period='1d')
        nifty_bank = get_index_data('NIFTY_BANK', period='1d')
        nifty_it = get_index_data('NIFTY_IT', period='1d')
        
        # Count positive vs negative sectors
        indices = [nifty, nifty_bank, nifty_it]
        advances = sum(1 for idx in indices if idx.get('change_pct', 0) > 0)
        declines = sum(1 for idx in indices if idx.get('change_pct', 0) < 0)
        unchanged = sum(1 for idx in indices if idx.get('change_pct', 0) == 0)
        
        # Synthetic delivery percentage (typically 35-65%)
        avg_change = sum(idx.get('change_pct', 0) for idx in indices) / len(indices)
        delivery_pct = 50 + (avg_change * 2)  # Rough proxy
        delivery_pct = max(20, min(80, delivery_pct))  # Clamp to realistic range
        
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'advances': advances,
            'declines': declines,
            'unchanged': unchanged,
            'advance_decline_ratio': round(advances / max(declines, 1), 2),
            'delivery_percentage': round(delivery_pct, 2),
            'note': 'Synthetic breadth based on sector indices. Use NSE/BSE live data for accuracy.',
            'data_source': 'Estimated from sector performance'
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'note': 'Market breadth data unavailable'
        }

def get_top_gainers(index: str = 'NIFTY50', limit: int = 10) -> List[Dict]:
    """
    Get top gainers from an index
    
    NOTE: This requires NSE live data or paid API.
    Returns placeholder structure for now.
    """
    return [
        {
            'symbol': f'STOCK{i}',
            'company': f'Company {i}',
            'ltp': 1000 + i * 100,
            'change_pct': 10 - i * 0.5,
            'volume': 1000000 * i,
            'note': 'Placeholder - integrate NSE API for real data'
        }
        for i in range(1, min(limit + 1, 11))
    ]

def get_top_losers(index: str = 'NIFTY50', limit: int = 10) -> List[Dict]:
    """
    Get top losers from an index
    
    NOTE: This requires NSE live data or paid API.
    Returns placeholder structure for now.
    """
    return [
        {
            'symbol': f'STOCK{i}',
            'company': f'Company {i}',
            'ltp': 1000 - i * 100,
            'change_pct': -(10 - i * 0.5),
            'volume': 1000000 * i,
            'note': 'Placeholder - integrate NSE API for real data'
        }
        for i in range(1, min(limit + 1, 11))
    ]

def get_most_active(index: str = 'NIFTY50', limit: int = 10) -> List[Dict]:
    """
    Get most active stocks by volume
    
    NOTE: This requires NSE live data or paid API.
    Returns placeholder structure for now.
    """
    return [
        {
            'symbol': f'ACTIVE{i}',
            'company': f'Active Company {i}',
            'ltp': 1000 + i * 50,
            'change_pct': 5 - i * 0.3,
            'volume': 10000000 * (11 - i),  # Higher volume first
            'value_cr': round((1000 + i * 50) * 10000000 * (11 - i) / 10000000, 2),
            'note': 'Placeholder - integrate NSE API for real data'
        }
        for i in range(1, min(limit + 1, 11))
    ]

def get_market_status() -> Dict:
    """
    Check if Indian stock markets are currently open
    """
    now = datetime.now()
    
    # IST timezone (UTC+5:30)
    # Market hours: 9:15 AM to 3:30 PM IST, Monday-Friday
    # Excluding holidays (simplified - real implementation should check holiday calendar)
    
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    hour = now.hour
    minute = now.minute
    
    is_weekend = weekday >= 5  # Saturday or Sunday
    
    # Market open: 9:15-15:30 IST
    market_open_time = 9 * 60 + 15  # 9:15 AM in minutes
    market_close_time = 15 * 60 + 30  # 3:30 PM in minutes
    current_time = hour * 60 + minute
    
    is_market_hours = (
        not is_weekend and
        market_open_time <= current_time <= market_close_time
    )
    
    if is_weekend:
        status = 'closed_weekend'
        message = 'Market closed - Weekend'
    elif current_time < market_open_time:
        status = 'pre_market'
        message = f'Pre-market - Opens at 9:15 AM IST'
    elif current_time > market_close_time:
        status = 'closed'
        message = f'Market closed - Opens at 9:15 AM IST tomorrow'
    else:
        status = 'open'
        message = 'Market is open'
    
    return {
        'status': status,
        'is_open': is_market_hours,
        'message': message,
        'current_time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'market_hours': '9:15 AM - 3:30 PM IST (Mon-Fri)',
        'timezone': 'IST (UTC+5:30)',
        'note': 'Holiday calendar not checked. May show open on market holidays.'
    }

def get_market_dashboard() -> Dict:
    """
    Comprehensive Indian stock market dashboard
    """
    return {
        'timestamp': datetime.now().isoformat(),
        'market_status': get_market_status(),
        'indices': {
            'sensex': get_sensex(),
            'nifty50': get_nifty(),
            'nifty_bank': get_nifty_bank(),
            'nifty_it': get_nifty_it(),
        },
        'flows': get_fii_dii_flows_synthetic(),
        'breadth': get_market_breadth_synthetic(),
        'exchange': 'BSE/NSE',
        'country': 'India',
        'currency': 'INR',
        'note': 'Using free data sources. Upgrade to NSE/BSE official feeds for real-time accuracy.'
    }

if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd in ['india-sensex', 'sensex']:
            print(json.dumps(get_sensex(), indent=2))
        elif cmd in ['india-nifty', 'nifty']:
            print(json.dumps(get_nifty(), indent=2))
        elif cmd in ['india-nifty-bank', 'nifty-bank']:
            print(json.dumps(get_nifty_bank(), indent=2))
        elif cmd in ['india-nifty-it', 'nifty-it']:
            print(json.dumps(get_nifty_it(), indent=2))
        elif cmd in ['india-all-indices', 'all-indices']:
            period = sys.argv[2] if len(sys.argv) > 2 else '1d'
            print(json.dumps(get_all_indices(period), indent=2))
        elif cmd in ['india-fii-dii', 'fii-dii']:
            print(json.dumps(get_fii_dii_flows_synthetic(), indent=2))
        elif cmd in ['india-breadth', 'breadth']:
            print(json.dumps(get_market_breadth_synthetic(), indent=2))
        elif cmd in ['india-gainers', 'gainers']:
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            print(json.dumps(get_top_gainers(limit=limit), indent=2))
        elif cmd in ['india-losers', 'losers']:
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            print(json.dumps(get_top_losers(limit=limit), indent=2))
        elif cmd in ['india-active', 'active']:
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            print(json.dumps(get_most_active(limit=limit), indent=2))
        elif cmd in ['india-market-status', 'status']:
            print(json.dumps(get_market_status(), indent=2))
        elif cmd in ['india-market-dashboard', 'dashboard']:
            print(json.dumps(get_market_dashboard(), indent=2))
        else:
            print(f"Unknown command: {cmd}")
            print("Available: india-sensex, india-nifty, india-nifty-bank, india-nifty-it, india-all-indices,")
            print("           india-fii-dii, india-breadth, india-gainers, india-losers, india-active,")
            print("           india-market-status, india-market-dashboard")
            sys.exit(1)
    else:
        # Default: market dashboard
        print(json.dumps(get_market_dashboard(), indent=2))

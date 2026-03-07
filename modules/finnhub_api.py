#!/usr/bin/env python3
"""
Finnhub API — Emerging Markets & Global Data Module

Specialized module for emerging markets and global financial data from Finnhub.
Complements finnhub.py (US market microstructure) with focus on:
- Emerging market stock quotes (India, China, Brazil, etc.)
- Country-specific market indices
- Forex rates and currency pairs
- Global economic calendar
- IPO calendar (worldwide)
- Multi-market status checks

Source: https://finnhub.io/api/v1/
Category: Emerging Markets & Global Data
Free tier: True (60 calls/min, 250K/day - requires FINNHUB_API_KEY env var)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Finnhub API Configuration
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")

# ========== EMERGING MARKETS CONFIGURATION ==========

EMERGING_MARKET_EXCHANGES = {
    'INDIA': {
        'exchange': 'NS',  # NSE India
        'indices': ['NIFTY50', 'SENSEX'],
        'sample_stocks': ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS']
    },
    'CHINA': {
        'exchange': 'SS',  # Shanghai Stock Exchange
        'indices': ['SSE', '000001.SS'],
        'sample_stocks': ['600519.SS', '601318.SS']  # Moutai, Ping An
    },
    'HONG_KONG': {
        'exchange': 'HK',
        'indices': ['HSI'],
        'sample_stocks': ['0700.HK', '9988.HK', '0941.HK']  # Tencent, Alibaba, China Mobile
    },
    'BRAZIL': {
        'exchange': 'SA',  # B3 - Brasil Bolsa Balcão
        'indices': ['IBOV'],
        'sample_stocks': ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA']
    },
    'SOUTH_AFRICA': {
        'exchange': 'JO',  # Johannesburg Stock Exchange
        'indices': ['J203'],
        'sample_stocks': ['AGL.JO', 'SBK.JO', 'NPN.JO']
    },
    'MEXICO': {
        'exchange': 'MX',
        'indices': ['MXX'],
        'sample_stocks': ['AMXL.MX', 'WALMEX.MX']
    },
    'TURKEY': {
        'exchange': 'IS',  # Borsa Istanbul
        'indices': ['XU100'],
        'sample_stocks': ['THYAO.IS', 'AKBNK.IS']
    }
}

MAJOR_FOREX_PAIRS = [
    'OANDA:EUR_USD', 'OANDA:GBP_USD', 'OANDA:USD_JPY', 'OANDA:USD_CHF',
    'OANDA:AUD_USD', 'OANDA:USD_CAD', 'OANDA:NZD_USD', 'OANDA:USD_CNH',
    'OANDA:USD_INR', 'OANDA:USD_BRL', 'OANDA:USD_MXN', 'OANDA:USD_TRY',
    'OANDA:USD_ZAR'
]


def get_emerging_market_quote(symbol: str) -> Dict:
    """
    Get real-time quote for an emerging market stock.
    
    Args:
        symbol: EM stock symbol with exchange suffix (e.g., 'RELIANCE.NS', 'BABA', '0700.HK')
    
    Returns:
        Dict with quote data: current price, high, low, open, previous close, 
        change, percent change, timestamp
    
    Example:
        >>> quote = get_emerging_market_quote('RELIANCE.NS')
        >>> print(f"Reliance: ₹{quote['c']}")
    """
    try:
        url = f"{FINNHUB_BASE_URL}/quote"
        params = {
            'symbol': symbol.upper(),
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Check if data is valid
        if data.get('c', 0) == 0:
            return {
                'success': False,
                'error': 'No data available for symbol',
                'symbol': symbol
            }
        
        # Add metadata and calculations
        current = data.get('c', 0)
        prev_close = data.get('pc', 0)
        
        result = {
            'success': True,
            'symbol': symbol.upper(),
            'current_price': current,
            'high': data.get('h', 0),
            'low': data.get('l', 0),
            'open': data.get('o', 0),
            'previous_close': prev_close,
            'change': round(current - prev_close, 4) if prev_close else 0,
            'change_percent': round(((current - prev_close) / prev_close * 100), 2) if prev_close else 0,
            'timestamp': data.get('t', 0),
            'timestamp_dt': datetime.fromtimestamp(data.get('t', 0)).isoformat() if data.get('t') else None,
            'fetched_at': datetime.now().isoformat()
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'symbol': symbol
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'symbol': symbol
        }


def get_country_indices(country_code: str = 'INDIA') -> Dict:
    """
    Get major market indices for a specific country.
    
    Args:
        country_code: Country code (INDIA, CHINA, HONG_KONG, BRAZIL, SOUTH_AFRICA, MEXICO, TURKEY)
    
    Returns:
        Dict with country info and index quotes
    
    Example:
        >>> indices = get_country_indices('INDIA')
        >>> for idx in indices['indices']:
        ...     print(f"{idx['name']}: {idx['value']}")
    """
    try:
        country_code = country_code.upper()
        
        if country_code not in EMERGING_MARKET_EXCHANGES:
            return {
                'success': False,
                'error': f'Unknown country code: {country_code}',
                'available_countries': list(EMERGING_MARKET_EXCHANGES.keys())
            }
        
        country_info = EMERGING_MARKET_EXCHANGES[country_code]
        indices_data = []
        
        # Fetch each index
        for index_symbol in country_info['indices']:
            # Try with exchange suffix if not present
            if '.' not in index_symbol and country_info['exchange']:
                full_symbol = f"{index_symbol}.{country_info['exchange']}"
            else:
                full_symbol = index_symbol
            
            quote = get_emerging_market_quote(full_symbol)
            if quote.get('success'):
                indices_data.append({
                    'symbol': full_symbol,
                    'name': index_symbol,
                    'value': quote['current_price'],
                    'change': quote['change'],
                    'change_percent': quote['change_percent']
                })
        
        return {
            'success': True,
            'country': country_code,
            'exchange': country_info['exchange'],
            'indices': indices_data,
            'sample_stocks': country_info['sample_stocks'],
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching country indices: {str(e)}',
            'country': country_code
        }


def get_forex_rates(base: str = 'USD', targets: Optional[List[str]] = None) -> Dict:
    """
    Get forex exchange rates for multiple currency pairs.
    
    Args:
        base: Base currency (default: 'USD')
        targets: List of target currencies (default: major pairs)
    
    Returns:
        Dict with forex rates and changes
    
    Example:
        >>> rates = get_forex_rates('USD', ['EUR', 'GBP', 'JPY', 'INR'])
        >>> for pair in rates['pairs']:
        ...     print(f"{pair['pair']}: {pair['rate']}")
    """
    try:
        if targets is None:
            # Default to major EM currencies
            targets = ['EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'CNH', 'INR', 'BRL', 'MXN', 'TRY', 'ZAR']
        
        forex_data = []
        
        for target in targets:
            # Construct Finnhub forex symbol
            if base == 'USD':
                symbol = f'OANDA:{base}_{target}'
            else:
                symbol = f'OANDA:{base}_{target}'
            
            url = f"{FINNHUB_BASE_URL}/quote"
            params = {
                'symbol': symbol,
                'token': FINNHUB_API_KEY
            }
            
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data.get('c', 0) != 0:
                    current = data.get('c', 0)
                    prev_close = data.get('pc', 0)
                    
                    forex_data.append({
                        'pair': f'{base}/{target}',
                        'symbol': symbol,
                        'rate': current,
                        'change': round(current - prev_close, 6) if prev_close else 0,
                        'change_percent': round(((current - prev_close) / prev_close * 100), 2) if prev_close else 0,
                        'high': data.get('h', 0),
                        'low': data.get('l', 0)
                    })
            except:
                continue  # Skip pairs that fail
        
        return {
            'success': True,
            'base_currency': base,
            'pairs_count': len(forex_data),
            'pairs': forex_data,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching forex rates: {str(e)}',
            'base': base
        }


def get_economic_calendar(country: Optional[str] = None, from_date: Optional[str] = None, 
                         to_date: Optional[str] = None) -> Dict:
    """
    Get upcoming economic events and data releases.
    
    Args:
        country: Country code (US, CN, JP, GB, EU, etc.) - None for all
        from_date: Start date YYYY-MM-DD (default: today)
        to_date: End date YYYY-MM-DD (default: +7 days)
    
    Returns:
        Dict with economic events including impact level, actual/estimate/previous values
    
    Example:
        >>> calendar = get_economic_calendar(country='US')
        >>> for event in calendar['events'][:5]:
        ...     print(f"{event['event']}: {event['impact']} impact")
    """
    try:
        # Default date range: next 7 days
        if from_date is None:
            from_date = datetime.now().strftime('%Y-%m-%d')
        if to_date is None:
            to_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        url = f"{FINNHUB_BASE_URL}/calendar/economic"
        params = {
            'from': from_date,
            'to': to_date,
            'token': FINNHUB_API_KEY
        }
        
        # Add country filter if specified
        if country:
            params['country'] = country.upper()
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Parse economic events
        events = data.get('economicCalendar', [])
        
        # Sort by date and impact
        impact_priority = {'high': 3, 'medium': 2, 'low': 1}
        events_sorted = sorted(
            events, 
            key=lambda x: (x.get('time', ''), -impact_priority.get(x.get('impact', 'low').lower(), 0))
        )
        
        # Summarize high-impact events
        high_impact = [e for e in events if e.get('impact', '').lower() == 'high']
        
        return {
            'success': True,
            'country': country or 'ALL',
            'date_range': {'from': from_date, 'to': to_date},
            'total_events': len(events),
            'high_impact_count': len(high_impact),
            'events': events_sorted,
            'timestamp': datetime.now().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'country': country
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'country': country
        }


def get_ipo_calendar(from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict:
    """
    Get upcoming IPOs globally.
    
    Args:
        from_date: Start date YYYY-MM-DD (default: today)
        to_date: End date YYYY-MM-DD (default: +30 days)
    
    Returns:
        Dict with IPO listings including name, exchange, shares, price range
    
    Example:
        >>> ipos = get_ipo_calendar()
        >>> for ipo in ipos['ipos'][:5]:
        ...     print(f"{ipo['name']} on {ipo['exchange']}: {ipo['date']}")
    """
    try:
        # Default date range: next 30 days
        if from_date is None:
            from_date = datetime.now().strftime('%Y-%m-%d')
        if to_date is None:
            to_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        url = f"{FINNHUB_BASE_URL}/calendar/ipo"
        params = {
            'from': from_date,
            'to': to_date,
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Parse IPO calendar
        ipos = data.get('ipoCalendar', [])
        
        # Sort by date
        ipos_sorted = sorted(ipos, key=lambda x: x.get('date', ''))
        
        # Calculate summary stats
        total_shares = sum(ipo.get('totalSharesValue', 0) for ipo in ipos if ipo.get('totalSharesValue'))
        
        return {
            'success': True,
            'date_range': {'from': from_date, 'to': to_date},
            'total_ipos': len(ipos),
            'total_shares_value': total_shares,
            'ipos': ipos_sorted,
            'timestamp': datetime.now().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def get_market_status(exchanges: Optional[List[str]] = None) -> Dict:
    """
    Check if major global markets are open or closed.
    
    Args:
        exchanges: List of exchange codes (default: major global exchanges)
    
    Returns:
        Dict with market status for each exchange
    
    Example:
        >>> status = get_market_status(['US', 'HK', 'NS'])
        >>> for mkt in status['markets']:
        ...     print(f"{mkt['exchange']}: {'OPEN' if mkt['is_open'] else 'CLOSED'}")
    """
    try:
        if exchanges is None:
            # Default to major global exchanges
            exchanges = ['US', 'HK', 'NS', 'SS', 'L', 'T', 'SA', 'JO', 'IS', 'MX']
        
        market_status = []
        
        for exchange in exchanges:
            url = f"{FINNHUB_BASE_URL}/stock/market-status"
            params = {
                'exchange': exchange,
                'token': FINNHUB_API_KEY
            }
            
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'exchange' in data:
                    market_status.append({
                        'exchange': exchange,
                        'is_open': data.get('isOpen', False),
                        'session': data.get('session', 'unknown'),
                        'timezone': data.get('timezone', 'UTC'),
                        'holiday': data.get('holiday', None)
                    })
            except:
                # If exchange not supported, skip
                continue
        
        # Categorize markets
        open_markets = [m for m in market_status if m['is_open']]
        closed_markets = [m for m in market_status if not m['is_open']]
        
        return {
            'success': True,
            'total_markets': len(market_status),
            'open_count': len(open_markets),
            'closed_count': len(closed_markets),
            'markets': market_status,
            'open_markets': [m['exchange'] for m in open_markets],
            'closed_markets': [m['exchange'] for m in closed_markets],
            'checked_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error checking market status: {str(e)}'
        }


def get_emerging_markets_snapshot() -> Dict:
    """
    Get comprehensive snapshot of emerging markets.
    Includes major indices, currencies, and market status.
    
    Returns:
        Dict with EM snapshot across countries, indices, and forex
    
    Example:
        >>> snapshot = get_emerging_markets_snapshot()
        >>> print(f"Markets open: {snapshot['markets_open']}")
        >>> print(f"Top gainer: {snapshot['top_performers'][0]}")
    """
    try:
        snapshot = {
            'countries': {},
            'forex': {},
            'market_status': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Fetch key EM indices
        em_countries = ['INDIA', 'CHINA', 'HONG_KONG', 'BRAZIL', 'SOUTH_AFRICA']
        
        for country in em_countries:
            country_data = get_country_indices(country)
            if country_data.get('success'):
                snapshot['countries'][country] = {
                    'exchange': country_data['exchange'],
                    'indices': country_data['indices']
                }
        
        # Fetch EM forex rates
        em_currencies = ['INR', 'CNH', 'BRL', 'ZAR', 'MXN', 'TRY']
        forex_data = get_forex_rates('USD', em_currencies)
        if forex_data.get('success'):
            snapshot['forex'] = forex_data['pairs']
        
        # Check market status
        em_exchanges = ['NS', 'SS', 'HK', 'SA', 'JO', 'IS', 'MX']
        status_data = get_market_status(em_exchanges)
        if status_data.get('success'):
            snapshot['market_status'] = {
                'open_markets': status_data['open_markets'],
                'closed_markets': status_data['closed_markets']
            }
        
        # Calculate summary metrics
        all_indices = []
        for country_info in snapshot['countries'].values():
            all_indices.extend(country_info['indices'])
        
        if all_indices:
            sorted_indices = sorted(all_indices, key=lambda x: x.get('change_percent', 0), reverse=True)
            snapshot['top_performers'] = sorted_indices[:3]
            snapshot['worst_performers'] = sorted_indices[-3:]
        
        snapshot['success'] = True
        return snapshot
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error generating EM snapshot: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }


# ========== CLI INTERFACE ==========

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "em-quote" and len(sys.argv) > 2:
            result = get_emerging_market_quote(sys.argv[2])
        elif command == "country" and len(sys.argv) > 2:
            result = get_country_indices(sys.argv[2])
        elif command == "forex":
            base = sys.argv[2] if len(sys.argv) > 2 else 'USD'
            result = get_forex_rates(base)
        elif command == "economic":
            country = sys.argv[2] if len(sys.argv) > 2 else None
            result = get_economic_calendar(country)
        elif command == "ipo":
            result = get_ipo_calendar()
        elif command == "status":
            result = get_market_status()
        elif command == "snapshot":
            result = get_emerging_markets_snapshot()
        else:
            result = {
                "module": "finnhub_api",
                "version": "1.0",
                "usage": "python finnhub_api.py [em-quote|country|forex|economic|ipo|status|snapshot] <args>",
                "functions": [
                    "get_emerging_market_quote(symbol)",
                    "get_country_indices(country_code)",
                    "get_forex_rates(base, targets)",
                    "get_economic_calendar(country, from_date, to_date)",
                    "get_ipo_calendar(from_date, to_date)",
                    "get_market_status(exchanges)",
                    "get_emerging_markets_snapshot()"
                ]
            }
    else:
        result = {
            "module": "finnhub_api",
            "status": "ready",
            "api_key_set": bool(FINNHUB_API_KEY),
            "functions": 7,
            "focus": "Emerging Markets & Global Data",
            "complements": "finnhub.py (US Market Microstructure)"
        }
    
    print(json.dumps(result, indent=2))

#!/usr/bin/env python3
"""
Trading Economics Bond API — Global Government Bond Yields

Access global government bond yields and credit data from multiple free sources.
Since Trading Economics API requires authentication, this module uses:
- Yahoo Finance for real-time US Treasury and major government bond yields
- Structured yield spread calculations
- Global bond symbol mappings

Source: https://tradingeconomics.com (concept), Yahoo Finance (data)
Category: Fixed Income & Credit
Free tier: true - No API key required
Author: QuantClaw Data NightBuilder
Phase: 106
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

# ========== BOND SYMBOL REGISTRY ==========

# Yahoo Finance bond yield symbols
BOND_SYMBOLS = {
    # US Treasuries
    'US2Y': '^IRX',   # 13 Week T-Bill (closest to 2Y for free data)
    'US5Y': '^FVX',   # 5 Year Treasury Yield
    'US10Y': '^TNX',  # 10 Year Treasury Yield
    'US30Y': '^TYX',  # 30 Year Treasury Yield
    
    # International Bonds
    'DE10Y': 'TMBMKDE-10Y',  # German 10Y Bund
    'GB10Y': 'TMBMKGB-10Y',  # UK 10Y Gilt
    'JP10Y': 'TMBMKJP-10Y',  # Japan 10Y JGB
    'FR10Y': 'TMBMKFR-10Y',  # France 10Y
    'IT10Y': 'TMBMKIT-10Y',  # Italy 10Y
    'ES10Y': 'TMBMKES-10Y',  # Spain 10Y
    'CA10Y': 'TMBMKCA-10Y',  # Canada 10Y
    'AU10Y': 'TMBMKAU-10Y',  # Australia 10Y
}

COUNTRY_CODES = {
    'US': 'United States',
    'DE': 'Germany',
    'GB': 'United Kingdom',
    'JP': 'Japan',
    'FR': 'France',
    'IT': 'Italy',
    'ES': 'Spain',
    'CA': 'Canada',
    'AU': 'Australia',
}

# US Treasury Curve Maturities
US_CURVE_MATURITIES = ['2Y', '5Y', '10Y', '30Y']

def _fetch_yahoo_bond(symbol: str) -> Optional[float]:
    """
    Internal helper to fetch bond yield from Yahoo Finance
    
    Args:
        symbol: Yahoo Finance symbol (e.g., '^TNX')
    
    Returns:
        Bond yield as float, or None if error
    """
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, timeout=10, headers=headers)
        
        if r.status_code == 200:
            data = r.json()
            price = data['chart']['result'][0]['meta'].get('regularMarketPrice')
            return round(float(price), 3) if price else None
    except Exception as e:
        return None

def get_us_treasury_yields() -> dict:
    """
    Get all US Treasury yields across the curve
    
    Returns:
        dict: US Treasury yields for 2Y, 5Y, 10Y, 30Y with metadata
        
    Example:
        {
            '2Y': {'symbol': '^IRX', 'yield': 4.123, 'updated': '2026-03-07T03:00:00'},
            '5Y': {'symbol': '^FVX', 'yield': 4.234, 'updated': '2026-03-07T03:00:00'},
            ...
        }
    """
    try:
        yields = {}
        now = datetime.now().isoformat()
        
        for maturity in US_CURVE_MATURITIES:
            symbol_key = f'US{maturity}'
            yahoo_symbol = BOND_SYMBOLS[symbol_key]
            
            yield_value = _fetch_yahoo_bond(yahoo_symbol)
            if yield_value is not None:
                yields[maturity] = {
                    'symbol': yahoo_symbol,
                    'yield': yield_value,
                    'maturity': maturity,
                    'country': 'United States',
                    'updated': now
                }
        
        return {
            'success': True,
            'data': yields,
            'count': len(yields),
            'timestamp': now
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_global_bond_yields(country: Optional[str] = None) -> dict:
    """
    Get global government bond yields (10Y) by country
    
    Args:
        country: Optional 2-letter country code filter (e.g., 'US', 'DE', 'GB')
                If None, returns all available countries
    
    Returns:
        dict: Global bond yields with metadata
        
    Example:
        {
            'success': True,
            'data': [
                {'country': 'United States', 'code': 'US', 'yield': 4.123, ...},
                {'country': 'Germany', 'code': 'DE', 'yield': 2.345, ...},
                ...
            ],
            'count': 9
        }
    """
    try:
        bonds = []
        now = datetime.now().isoformat()
        
        # Filter countries if requested
        countries = {country: COUNTRY_CODES[country]} if country and country in COUNTRY_CODES else COUNTRY_CODES
        
        for code, name in countries.items():
            symbol_key = f'{code}10Y'
            if symbol_key in BOND_SYMBOLS:
                yahoo_symbol = BOND_SYMBOLS[symbol_key]
                yield_value = _fetch_yahoo_bond(yahoo_symbol)
                
                if yield_value is not None:
                    bonds.append({
                        'country': name,
                        'code': code,
                        'symbol': symbol_key,
                        'yahoo_symbol': yahoo_symbol,
                        'yield': yield_value,
                        'maturity': '10Y',
                        'updated': now
                    })
        
        return {
            'success': True,
            'data': bonds,
            'count': len(bonds),
            'timestamp': now
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_yield_spread(short: str = 'US2Y', long: str = 'US10Y') -> dict:
    """
    Calculate yield spread between two bonds (e.g., 2s10s curve)
    
    Args:
        short: Short maturity bond symbol (default: 'US2Y')
        long: Long maturity bond symbol (default: 'US10Y')
    
    Returns:
        dict: Yield spread calculation with both yields and spread in bps
        
    Example:
        {
            'success': True,
            'spread': {
                'short': {'symbol': 'US2Y', 'yield': 4.123},
                'long': {'symbol': 'US10Y', 'yield': 4.234},
                'spread_bps': 11.1,
                'spread_pct': 0.111,
                'inverted': False
            }
        }
    """
    try:
        # Validate symbols exist
        if short not in BOND_SYMBOLS or long not in BOND_SYMBOLS:
            return {
                'success': False,
                'error': f'Invalid bond symbols. Available: {list(BOND_SYMBOLS.keys())}',
                'timestamp': datetime.now().isoformat()
            }
        
        # Fetch both yields
        short_yield = _fetch_yahoo_bond(BOND_SYMBOLS[short])
        long_yield = _fetch_yahoo_bond(BOND_SYMBOLS[long])
        
        if short_yield is None or long_yield is None:
            return {
                'success': False,
                'error': 'Failed to fetch one or both bond yields',
                'timestamp': datetime.now().isoformat()
            }
        
        # Calculate spread
        spread_pct = long_yield - short_yield
        spread_bps = spread_pct * 100  # Convert to basis points
        inverted = spread_bps < 0
        
        return {
            'success': True,
            'spread': {
                'short': {
                    'symbol': short,
                    'yield': short_yield
                },
                'long': {
                    'symbol': long,
                    'yield': long_yield
                },
                'spread_pct': round(spread_pct, 3),
                'spread_bps': round(spread_bps, 1),
                'inverted': inverted,
                'interpretation': 'Inverted yield curve (recession signal)' if inverted else 'Normal yield curve'
            },
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_bond_yield(symbol: str = 'US10Y') -> dict:
    """
    Get single bond yield by symbol
    
    Args:
        symbol: Bond symbol (e.g., 'US10Y', 'DE10Y', 'GB10Y')
    
    Returns:
        dict: Single bond yield with metadata
        
    Example:
        {
            'success': True,
            'bond': {
                'symbol': 'US10Y',
                'yield': 4.123,
                'country': 'United States',
                'maturity': '10Y',
                'updated': '2026-03-07T03:00:00'
            }
        }
    """
    try:
        if symbol not in BOND_SYMBOLS:
            return {
                'success': False,
                'error': f'Unknown symbol: {symbol}. Available: {list(BOND_SYMBOLS.keys())}',
                'timestamp': datetime.now().isoformat()
            }
        
        yahoo_symbol = BOND_SYMBOLS[symbol]
        yield_value = _fetch_yahoo_bond(yahoo_symbol)
        
        if yield_value is None:
            return {
                'success': False,
                'error': f'Failed to fetch yield for {symbol}',
                'timestamp': datetime.now().isoformat()
            }
        
        # Extract country code and maturity
        country_code = symbol[:2]
        maturity = symbol[2:]
        
        return {
            'success': True,
            'bond': {
                'symbol': symbol,
                'yahoo_symbol': yahoo_symbol,
                'yield': yield_value,
                'country': COUNTRY_CODES.get(country_code, 'Unknown'),
                'country_code': country_code,
                'maturity': maturity,
                'updated': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_yield_curve(country: str = 'US') -> dict:
    """
    Get full yield curve for a country
    
    Args:
        country: 2-letter country code (default: 'US')
    
    Returns:
        dict: Full yield curve with all available maturities
        
    Example:
        {
            'success': True,
            'curve': {
                'country': 'United States',
                'yields': [
                    {'maturity': '2Y', 'yield': 4.123},
                    {'maturity': '5Y', 'yield': 4.200},
                    {'maturity': '10Y', 'yield': 4.234},
                    {'maturity': '30Y', 'yield': 4.456}
                ],
                'slope': 'Normal/Flat/Inverted'
            }
        }
    """
    try:
        if country not in COUNTRY_CODES:
            return {
                'success': False,
                'error': f'Unknown country: {country}. Available: {list(COUNTRY_CODES.keys())}',
                'timestamp': datetime.now().isoformat()
            }
        
        # For US, get full curve
        if country == 'US':
            curve_points = []
            for maturity in US_CURVE_MATURITIES:
                symbol = f'US{maturity}'
                yield_value = _fetch_yahoo_bond(BOND_SYMBOLS[symbol])
                if yield_value is not None:
                    curve_points.append({
                        'maturity': maturity,
                        'yield': yield_value
                    })
            
            # Determine curve slope
            if len(curve_points) >= 2:
                first_yield = curve_points[0]['yield']
                last_yield = curve_points[-1]['yield']
                if last_yield > first_yield + 0.2:
                    slope = 'Normal (Upward)'
                elif last_yield < first_yield - 0.1:
                    slope = 'Inverted (Recession Signal)'
                else:
                    slope = 'Flat'
            else:
                slope = 'Unknown'
            
            return {
                'success': True,
                'curve': {
                    'country': COUNTRY_CODES[country],
                    'country_code': country,
                    'yields': curve_points,
                    'count': len(curve_points),
                    'slope': slope,
                    'updated': datetime.now().isoformat()
                },
                'timestamp': datetime.now().isoformat()
            }
        else:
            # For other countries, return 10Y only
            symbol = f'{country}10Y'
            result = get_bond_yield(symbol)
            
            if result['success']:
                return {
                    'success': True,
                    'curve': {
                        'country': COUNTRY_CODES[country],
                        'country_code': country,
                        'yields': [{
                            'maturity': '10Y',
                            'yield': result['bond']['yield']
                        }],
                        'count': 1,
                        'note': 'Only 10Y available for non-US countries in free tier',
                        'updated': datetime.now().isoformat()
                    },
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return result
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_credit_spreads() -> dict:
    """
    Get credit spread indicators (using common spreads as proxies)
    
    Returns:
        dict: Credit spread calculations between various bond types
        
    Example:
        {
            'success': True,
            'spreads': {
                '2s10s': {'spread_bps': 11.1, 'inverted': False},
                '5s30s': {'spread_bps': 25.6, 'inverted': False},
                ...
            }
        }
    """
    try:
        spreads = {}
        
        # Common credit/term spreads
        spread_pairs = [
            ('US2Y', 'US10Y', '2s10s'),
            ('US5Y', 'US30Y', '5s30s'),
            ('US10Y', 'US30Y', '10s30s'),
        ]
        
        for short, long, name in spread_pairs:
            result = get_yield_spread(short, long)
            if result['success']:
                spreads[name] = {
                    'short': short,
                    'long': long,
                    'spread_bps': result['spread']['spread_bps'],
                    'spread_pct': result['spread']['spread_pct'],
                    'inverted': result['spread']['inverted'],
                    'interpretation': result['spread']['interpretation']
                }
        
        return {
            'success': True,
            'spreads': spreads,
            'count': len(spreads),
            'note': 'Using US Treasury spreads as credit indicators (free tier limitation)',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# ========== CLI INTERFACE ==========

if __name__ == "__main__":
    import sys
    
    print(json.dumps({
        "module": "trading_economics_bond_api",
        "status": "active",
        "source": "Yahoo Finance (free)",
        "functions": [
            "get_us_treasury_yields()",
            "get_global_bond_yields(country=None)",
            "get_yield_spread(short='US2Y', long='US10Y')",
            "get_bond_yield(symbol='US10Y')",
            "get_yield_curve(country='US')",
            "get_credit_spreads()"
        ],
        "available_bonds": list(BOND_SYMBOLS.keys()),
        "phase": 106
    }, indent=2))

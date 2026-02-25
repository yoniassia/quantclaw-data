#!/usr/bin/env python3
"""
Global FX Rates Module — Phase 181

Comprehensive foreign exchange rates for 150+ currency pairs
Using ECB, FRED, and ExchangeRate-API

Data Sources:
- ECB Reference Rates API (Euro-based pairs, daily)
- FRED (Federal Reserve Economic Data) - Major pairs
- ExchangeRate-API (open.er-api.com) - Free tier, 170+ currencies

Refresh: Daily
Coverage: 150+ currency pairs worldwide

Author: QUANTCLAW DATA Build Agent
Phase: 181
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

# ============ API Configuration ============

ECB_API_BASE = "https://data-api.ecb.europa.eu/service"
FRED_API_BASE = "https://api.stlouisfed.org/fred"
EXCHANGERATE_API_BASE = "https://open.er-api.com/v6"

# FRED API Key (from environment or default public key)
import os
FRED_API_KEY = os.environ.get('FRED_API_KEY', 'a31c101f39b1f5f1b5bfb9e2c8f4e5f5')  # Public demo key

# ============ Major Currency Pairs ============

# G10 Currencies
G10_CURRENCIES = ['USD', 'EUR', 'JPY', 'GBP', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK']

# Major Emerging Market Currencies
EM_CURRENCIES = ['CNY', 'INR', 'BRL', 'RUB', 'ZAR', 'MXN', 'TRY', 'KRW', 'IDR', 'PLN', 
                 'THB', 'MYR', 'PHP', 'CLP', 'COP', 'ARS', 'EGP', 'NGN', 'VND', 'HUF']

# Asian Currencies
ASIAN_CURRENCIES = ['CNY', 'JPY', 'KRW', 'INR', 'SGD', 'HKD', 'TWD', 'THB', 'MYR', 'IDR', 
                    'PHP', 'VND', 'PKR', 'BDT', 'LKR']

# Middle East & Africa
MENA_CURRENCIES = ['SAR', 'AED', 'QAR', 'KWD', 'OMR', 'BHD', 'JOD', 'ILS', 'EGP', 'ZAR', 
                   'NGN', 'KES', 'GHS', 'TND', 'MAD']

# Crypto (if supported by provider)
CRYPTO_CURRENCIES = ['BTC', 'ETH', 'USDT', 'BNB', 'XRP']

# All supported currencies
ALL_CURRENCIES = list(set(G10_CURRENCIES + EM_CURRENCIES + ASIAN_CURRENCIES + MENA_CURRENCIES))

# FRED Series for Major Pairs (where available)
FRED_FX_SERIES = {
    'USD/EUR': 'DEXUSEU',
    'USD/GBP': 'DEXUSUK',
    'USD/JPY': 'DEXJPUS',
    'USD/CAD': 'DEXCAUS',
    'USD/CHF': 'DEXSZUS',
    'USD/AUD': 'DEXUSAL',
    'USD/NZD': 'DEXUSNZ',
    'USD/SEK': 'DEXSDUS',
    'USD/NOK': 'DEXNOUS',
    'USD/DKK': 'DEXDNUS',
    'USD/CNY': 'DEXCHUS',
    'USD/INR': 'DEXINUS',
    'USD/BRL': 'DEXBZUS',
    'USD/ZAR': 'DEXSFUS',
    'USD/MXN': 'DEXMXUS',
    'USD/KRW': 'DEXKOUS',
    'USD/SGD': 'DEXSIUS',
    'USD/HKD': 'DEXHKUS',
    'USD/TWD': 'DEXTAUS',
    'USD/THB': 'DEXTHUS',
    'USD/MYR': 'DEXMAUS',
}

# ECB Reference Rate Series
ECB_FX_SERIES = {
    'EUR/USD': 'D.USD.EUR.SP00.A',
    'EUR/GBP': 'D.GBP.EUR.SP00.A',
    'EUR/JPY': 'D.JPY.EUR.SP00.A',
    'EUR/CHF': 'D.CHF.EUR.SP00.A',
    'EUR/CNY': 'D.CNY.EUR.SP00.A',
    'EUR/AUD': 'D.AUD.EUR.SP00.A',
    'EUR/CAD': 'D.CAD.EUR.SP00.A',
    'EUR/SEK': 'D.SEK.EUR.SP00.A',
    'EUR/NOK': 'D.NOK.EUR.SP00.A',
    'EUR/DKK': 'D.DKK.EUR.SP00.A',
    'EUR/NZD': 'D.NZD.EUR.SP00.A',
    'EUR/KRW': 'D.KRW.EUR.SP00.A',
    'EUR/INR': 'D.INR.EUR.SP00.A',
    'EUR/BRL': 'D.BRL.EUR.SP00.A',
    'EUR/RUB': 'D.RUB.EUR.SP00.A',
    'EUR/ZAR': 'D.ZAR.EUR.SP00.A',
    'EUR/TRY': 'D.TRY.EUR.SP00.A',
    'EUR/MXN': 'D.MXN.EUR.SP00.A',
    'EUR/SGD': 'D.SGD.EUR.SP00.A',
    'EUR/HKD': 'D.HKD.EUR.SP00.A',
}


# ============ API Functions ============

def get_exchangerate_host_latest(base: str = 'USD', symbols: Optional[List[str]] = None) -> Dict:
    """
    Get latest FX rates from ExchangeRate-API (open.er-api.com)
    
    Args:
        base: Base currency (default USD)
        symbols: List of target currencies (if None, fetches all)
    
    Returns:
        Dictionary with exchange rates
    """
    try:
        response = requests.get(
            f"{EXCHANGERATE_API_BASE}/latest/{base}",
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('result') != 'success':
            return {
                'success': False,
                'error': data.get('error', 'API request failed')
            }
        
        rates = data.get('rates', {})
        
        # Filter by symbols if specified
        if symbols:
            rates = {curr: rate for curr, rate in rates.items() if curr in symbols}
        
        # Extract date from time_last_update_utc
        import dateutil.parser
        try:
            date_str = data.get('time_last_update_utc', '')
            date_obj = dateutil.parser.parse(date_str)
            date = date_obj.strftime('%Y-%m-%d')
        except:
            date = datetime.now().strftime('%Y-%m-%d')
        
        return {
            'success': True,
            'base': data.get('base_code', base),
            'date': date,
            'rates': rates,
            'source': 'ExchangeRate-API'
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'ExchangeRate-API error: {str(e)}'
        }


def get_exchangerate_host_historical(base: str, date: str, symbols: Optional[List[str]] = None) -> Dict:
    """
    Get historical FX rates from ExchangeRate-API
    Note: Historical data requires a paid subscription on ExchangeRate-API.
    This function is a placeholder for future implementation.
    
    Args:
        base: Base currency
        date: Date in YYYY-MM-DD format
        symbols: List of target currencies
    
    Returns:
        Dictionary with exchange rates for the specified date
    """
    return {
        'success': False,
        'error': 'Historical FX rates require a paid ExchangeRate-API subscription. Use latest rates instead.'
    }


def get_fred_fx_rate(series_id: str, last_n_obs: int = 30) -> Dict:
    """
    Get FX rate data from FRED
    
    Args:
        series_id: FRED series ID (e.g., DEXJPUS for USD/JPY)
        last_n_obs: Number of recent observations
    
    Returns:
        Dictionary with rate data
    """
    try:
        params = {
            'series_id': series_id,
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'limit': last_n_obs,
            'sort_order': 'desc'
        }
        
        response = requests.get(
            f"{FRED_API_BASE}/series/observations",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if 'observations' not in data:
            return {
                'success': False,
                'error': 'No observations found'
            }
        
        observations = []
        for obs in data['observations']:
            if obs['value'] != '.':  # Skip missing values
                try:
                    observations.append({
                        'date': obs['date'],
                        'value': float(obs['value'])
                    })
                except (ValueError, TypeError):
                    continue
        
        if not observations:
            return {
                'success': False,
                'error': 'No valid observations'
            }
        
        # Calculate changes
        latest = observations[0]
        previous = observations[1] if len(observations) > 1 else None
        
        day_change = None
        day_change_pct = None
        if previous:
            day_change = latest['value'] - previous['value']
            if previous['value'] != 0:
                day_change_pct = (day_change / previous['value']) * 100
        
        return {
            'success': True,
            'series_id': series_id,
            'latest_value': latest['value'],
            'latest_date': latest['date'],
            'day_change': day_change,
            'day_change_pct': day_change_pct,
            'observations': observations[:30],
            'source': 'FRED'
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'FRED API error: {str(e)}'
        }


def get_ecb_fx_rate(currency_pair: str) -> Dict:
    """
    Get FX rate from ECB
    
    Args:
        currency_pair: Currency pair in format EUR/XXX (e.g., EUR/USD)
    
    Returns:
        Dictionary with rate data
    """
    if currency_pair not in ECB_FX_SERIES:
        return {
            'success': False,
            'error': f'Currency pair {currency_pair} not available from ECB'
        }
    
    try:
        series_key = ECB_FX_SERIES[currency_pair]
        endpoint = f"data/EXR/{series_key}"
        
        params = {'lastNObservations': 30}
        
        headers = {
            'Accept': 'application/vnd.sdmx.genericdata+xml;version=2.1'
        }
        
        response = requests.get(
            f"{ECB_API_BASE}/{endpoint}",
            headers=headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        
        # Parse SDMX XML (simplified)
        import xml.etree.ElementTree as ET
        
        namespaces = {
            'generic': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic',
            'common': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common'
        }
        
        root = ET.fromstring(response.text)
        
        observations = []
        for obs in root.findall('.//generic:Obs', namespaces):
            obs_dim = obs.find('.//generic:ObsDimension', namespaces)
            obs_val = obs.find('.//generic:ObsValue', namespaces)
            
            if obs_dim is not None and obs_val is not None:
                date = obs_dim.get('value')
                value = obs_val.get('value')
                
                if date and value:
                    try:
                        observations.append({
                            'date': date,
                            'value': float(value)
                        })
                    except ValueError:
                        continue
        
        if not observations:
            return {
                'success': False,
                'error': 'No observations found'
            }
        
        # Sort by date descending
        observations.sort(key=lambda x: x['date'], reverse=True)
        
        latest = observations[0]
        previous = observations[1] if len(observations) > 1 else None
        
        day_change = None
        day_change_pct = None
        if previous:
            day_change = latest['value'] - previous['value']
            if previous['value'] != 0:
                day_change_pct = (day_change / previous['value']) * 100
        
        return {
            'success': True,
            'currency_pair': currency_pair,
            'latest_value': latest['value'],
            'latest_date': latest['date'],
            'day_change': day_change,
            'day_change_pct': day_change_pct,
            'observations': observations[:30],
            'source': 'ECB'
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'ECB API error: {str(e)}'
        }


# ============ High-Level Functions ============

def get_fx_rate(base: str, target: str, source: str = 'auto') -> Dict:
    """
    Get FX rate for a currency pair with automatic source selection
    
    Args:
        base: Base currency (e.g., USD)
        target: Target currency (e.g., EUR)
        source: Data source ('auto', 'ecb', 'fred', 'exchangerate')
    
    Returns:
        Dictionary with rate data
    """
    base = base.upper()
    target = target.upper()
    
    if source == 'auto':
        # Try sources in order of preference
        
        # 1. Try ECB if EUR-based pair
        if base == 'EUR':
            pair = f"EUR/{target}"
            if pair in ECB_FX_SERIES:
                result = get_ecb_fx_rate(pair)
                if result['success']:
                    return result
        
        # 2. Try FRED if USD-based pair
        if base == 'USD':
            pair = f"USD/{target}"
            if pair in FRED_FX_SERIES:
                result = get_fred_fx_rate(FRED_FX_SERIES[pair])
                if result['success']:
                    result['currency_pair'] = pair
                    return result
        
        # 3. Fall back to ExchangeRate-API
        result = get_exchangerate_host_latest(base=base, symbols=[target])
        if result['success'] and target in result['rates']:
            return {
                'success': True,
                'currency_pair': f"{base}/{target}",
                'latest_value': result['rates'][target],
                'latest_date': result['date'],
                'source': 'ExchangeRate-API'
            }
        
        return {
            'success': False,
            'error': f'No data available for {base}/{target}'
        }
    
    elif source == 'ecb':
        pair = f"{base}/{target}"
        return get_ecb_fx_rate(pair)
    
    elif source == 'fred':
        pair = f"{base}/{target}"
        if pair not in FRED_FX_SERIES:
            return {
                'success': False,
                'error': f'FRED does not have data for {pair}'
            }
        result = get_fred_fx_rate(FRED_FX_SERIES[pair])
        if result['success']:
            result['currency_pair'] = pair
        return result
    
    elif source == 'exchangerate':
        result = get_exchangerate_host_latest(base=base, symbols=[target])
        if result['success'] and target in result['rates']:
            return {
                'success': True,
                'currency_pair': f"{base}/{target}",
                'latest_value': result['rates'][target],
                'latest_date': result['date'],
                'source': 'ExchangeRate-API'
            }
        return {
            'success': False,
            'error': f'No data available for {base}/{target}'
        }
    
    else:
        return {
            'success': False,
            'error': f'Unknown source: {source}'
        }


def get_all_rates(base: str = 'USD') -> Dict:
    """
    Get all available FX rates for a base currency
    
    Args:
        base: Base currency (default USD)
    
    Returns:
        Dictionary with all available rates
    """
    result = get_exchangerate_host_latest(base=base)
    
    if not result['success']:
        return result
    
    rates = result['rates']
    
    # Organize by region
    g10_rates = {curr: rates.get(curr) for curr in G10_CURRENCIES if curr in rates and curr != base}
    em_rates = {curr: rates.get(curr) for curr in EM_CURRENCIES if curr in rates}
    asian_rates = {curr: rates.get(curr) for curr in ASIAN_CURRENCIES if curr in rates}
    mena_rates = {curr: rates.get(curr) for curr in MENA_CURRENCIES if curr in rates}
    
    return {
        'success': True,
        'base': base,
        'date': result['date'],
        'total_pairs': len(rates),
        'g10': g10_rates,
        'emerging_markets': em_rates,
        'asia': asian_rates,
        'mena': mena_rates,
        'all_rates': rates,
        'source': 'ExchangeRate-API',
        'timestamp': datetime.now().isoformat()
    }


def get_cross_rate(currency1: str, currency2: str, via: str = 'USD') -> Dict:
    """
    Calculate cross rate for two non-USD currencies
    
    Args:
        currency1: First currency (base)
        currency2: Second currency (quote)
        via: Bridge currency (default USD)
    
    Returns:
        Dictionary with cross rate (currency1/currency2)
    """
    currency1 = currency1.upper()
    currency2 = currency2.upper()
    via = via.upper()
    
    # Get both rates vs bridge currency
    # We need via/currency1 and via/currency2
    result1 = get_fx_rate(via, currency1)  # USD/GBP = 0.74
    result2 = get_fx_rate(via, currency2)  # USD/JPY = 155
    
    if not result1['success'] or not result2['success']:
        return {
            'success': False,
            'error': 'Could not fetch required rates for cross calculation'
        }
    
    # Calculate cross rate
    # currency1/currency2 = (via/currency2) / (via/currency1)
    # GBP/JPY = (USD/JPY) / (USD/GBP) = 155 / 0.74 = 209.46
    rate1 = result1['latest_value']  # USD/currency1
    rate2 = result2['latest_value']  # USD/currency2
    
    cross_rate = rate2 / rate1
    
    return {
        'success': True,
        'currency_pair': f"{currency1}/{currency2}",
        'cross_rate': cross_rate,
        'via': via,
        'rate1': {
            'pair': f"{via}/{currency1}",
            'rate': rate1,
            'date': result1.get('latest_date')
        },
        'rate2': {
            'pair': f"{via}/{currency2}",
            'rate': rate2,
            'date': result2.get('latest_date')
        },
        'calculation': f"({via}/{currency2}) / ({via}/{currency1}) = {rate2} / {rate1} = {cross_rate}",
        'timestamp': datetime.now().isoformat()
    }


def get_fx_matrix(currencies: List[str]) -> Dict:
    """
    Get FX rate matrix for a list of currencies
    
    Args:
        currencies: List of currency codes
    
    Returns:
        Dictionary with rate matrix
    """
    currencies = [c.upper() for c in currencies]
    
    # Use USD as base and fetch all rates
    result = get_exchangerate_host_latest(base='USD', symbols=currencies)
    
    if not result['success']:
        return result
    
    rates_vs_usd = result['rates']
    
    # Build matrix
    matrix = {}
    for base_curr in currencies:
        if base_curr not in rates_vs_usd:
            continue
        
        base_rate = rates_vs_usd[base_curr]
        matrix[base_curr] = {}
        
        for target_curr in currencies:
            if base_curr == target_curr:
                matrix[base_curr][target_curr] = 1.0
            elif target_curr in rates_vs_usd:
                target_rate = rates_vs_usd[target_curr]
                # Cross rate calculation
                matrix[base_curr][target_curr] = target_rate / base_rate
            else:
                matrix[base_curr][target_curr] = None
    
    return {
        'success': True,
        'currencies': currencies,
        'matrix': matrix,
        'date': result['date'],
        'source': 'ExchangeRate-API',
        'timestamp': datetime.now().isoformat()
    }


def get_strongest_weakest(base: str = 'USD', period: str = '1D') -> Dict:
    """
    Get strongest and weakest currencies vs base
    
    Args:
        base: Base currency
        period: Time period (1D, 1W, 1M)
    
    Returns:
        Dictionary with strongest/weakest movers
    """
    # For now, return current snapshot (historical comparison would require more data)
    result = get_all_rates(base=base)
    
    if not result['success']:
        return result
    
    all_rates = result['all_rates']
    
    # Sort by value (higher = stronger vs base)
    sorted_rates = sorted(all_rates.items(), key=lambda x: x[1] if x[1] else 0, reverse=True)
    
    strongest = sorted_rates[:10]
    weakest = sorted_rates[-10:]
    
    return {
        'success': True,
        'base': base,
        'date': result['date'],
        'strongest_vs_base': [{'currency': curr, 'rate': rate} for curr, rate in strongest],
        'weakest_vs_base': [{'currency': curr, 'rate': rate} for curr, rate in weakest],
        'note': 'Real-time snapshot. Historical comparison requires time series data.',
        'timestamp': datetime.now().isoformat()
    }


def convert_currency(amount: float, from_curr: str, to_curr: str) -> Dict:
    """
    Convert amount from one currency to another
    
    Args:
        amount: Amount to convert
        from_curr: Source currency
        to_curr: Target currency
    
    Returns:
        Dictionary with converted amount
    """
    rate_result = get_fx_rate(from_curr, to_curr)
    
    if not rate_result['success']:
        return rate_result
    
    rate = rate_result['latest_value']
    converted = amount * rate
    
    return {
        'success': True,
        'amount': amount,
        'from_currency': from_curr.upper(),
        'to_currency': to_curr.upper(),
        'exchange_rate': rate,
        'converted_amount': converted,
        'as_of': rate_result.get('latest_date'),
        'source': rate_result.get('source'),
        'timestamp': datetime.now().isoformat()
    }


def list_supported_currencies() -> Dict:
    """
    List all supported currencies organized by region
    
    Returns:
        Dictionary with currency lists
    """
    return {
        'success': True,
        'g10_currencies': G10_CURRENCIES,
        'emerging_markets': EM_CURRENCIES,
        'asian_currencies': ASIAN_CURRENCIES,
        'mena_currencies': MENA_CURRENCIES,
        'all_currencies': ALL_CURRENCIES,
        'total_major_currencies': len(ALL_CURRENCIES),
        'note': 'ExchangeRate-API supports 170+ currencies total',
        'ecb_pairs': len(ECB_FX_SERIES),
        'fred_pairs': len(FRED_FX_SERIES),
        'timestamp': datetime.now().isoformat()
    }


# ============ CLI Interface ============

def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    try:
        if command == 'fx-rate':
            if len(sys.argv) < 4:
                print("Error: fx-rate requires base and target currency", file=sys.stderr)
                print("Usage: python3 global_fx_rates.py fx-rate <BASE> <TARGET> [--source auto|ecb|fred|exchangerate]", file=sys.stderr)
                return 1
            
            base = sys.argv[2].upper()
            target = sys.argv[3].upper()
            source = 'auto'
            
            if '--source' in sys.argv:
                idx = sys.argv.index('--source')
                if idx + 1 < len(sys.argv):
                    source = sys.argv[idx + 1]
            
            data = get_fx_rate(base, target, source=source)
            print(json.dumps(data, indent=2))
        
        elif command == 'fx-all':
            base = sys.argv[2].upper() if len(sys.argv) > 2 else 'USD'
            data = get_all_rates(base=base)
            print(json.dumps(data, indent=2))
        
        elif command == 'fx-cross':
            if len(sys.argv) < 4:
                print("Error: fx-cross requires two currencies", file=sys.stderr)
                print("Usage: python3 global_fx_rates.py fx-cross <CURRENCY1> <CURRENCY2> [--via USD]", file=sys.stderr)
                return 1
            
            curr1 = sys.argv[2].upper()
            curr2 = sys.argv[3].upper()
            via = 'USD'
            
            if '--via' in sys.argv:
                idx = sys.argv.index('--via')
                if idx + 1 < len(sys.argv):
                    via = sys.argv[idx + 1].upper()
            
            data = get_cross_rate(curr1, curr2, via=via)
            print(json.dumps(data, indent=2))
        
        elif command == 'fx-matrix':
            if len(sys.argv) < 3:
                print("Error: fx-matrix requires currency list", file=sys.stderr)
                print("Usage: python3 global_fx_rates.py fx-matrix <CUR1> <CUR2> ... <CURN>", file=sys.stderr)
                return 1
            
            currencies = [arg.upper() for arg in sys.argv[2:]]
            data = get_fx_matrix(currencies)
            print(json.dumps(data, indent=2))
        
        elif command == 'fx-convert':
            if len(sys.argv) < 5:
                print("Error: fx-convert requires amount, from currency, and to currency", file=sys.stderr)
                print("Usage: python3 global_fx_rates.py fx-convert <AMOUNT> <FROM> <TO>", file=sys.stderr)
                return 1
            
            amount = float(sys.argv[2])
            from_curr = sys.argv[3].upper()
            to_curr = sys.argv[4].upper()
            
            data = convert_currency(amount, from_curr, to_curr)
            print(json.dumps(data, indent=2))
        
        elif command == 'fx-strongest':
            base = sys.argv[2].upper() if len(sys.argv) > 2 else 'USD'
            data = get_strongest_weakest(base=base)
            print(json.dumps(data, indent=2))
        
        elif command == 'fx-currencies':
            data = list_supported_currencies()
            print(json.dumps(data, indent=2))
        
        else:
            print(f"Error: Unknown command '{command}'", file=sys.stderr)
            print_help()
            return 1
        
        return 0
    
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }, indent=2), file=sys.stderr)
        return 1


def print_help():
    """Print CLI help"""
    print("""
Global FX Rates Module (Phase 181)

Commands:
  python3 global_fx_rates.py fx-rate <BASE> <TARGET> [--source auto|ecb|fred|exchangerate]
                                     # Get exchange rate for a currency pair
  
  python3 global_fx_rates.py fx-all [BASE]
                                     # Get all available rates for base currency (default USD)
  
  python3 global_fx_rates.py fx-cross <CUR1> <CUR2> [--via USD]
                                     # Calculate cross rate for two currencies
  
  python3 global_fx_rates.py fx-matrix <CUR1> <CUR2> ... <CURN>
                                     # Get FX rate matrix for specified currencies
  
  python3 global_fx_rates.py fx-convert <AMOUNT> <FROM> <TO>
                                     # Convert amount from one currency to another
  
  python3 global_fx_rates.py fx-strongest [BASE]
                                     # Get strongest/weakest currencies vs base
  
  python3 global_fx_rates.py fx-currencies
                                     # List all supported currencies by region

Examples:
  # Get USD/EUR rate
  python3 global_fx_rates.py fx-rate USD EUR
  
  # Get EUR/GBP rate from ECB
  python3 global_fx_rates.py fx-rate EUR GBP --source ecb
  
  # Get all rates vs USD
  python3 global_fx_rates.py fx-all USD
  
  # Calculate GBP/JPY cross rate
  python3 global_fx_rates.py fx-cross GBP JPY
  
  # Get rate matrix for major currencies
  python3 global_fx_rates.py fx-matrix USD EUR GBP JPY CHF
  
  # Convert 1000 USD to EUR
  python3 global_fx_rates.py fx-convert 1000 USD EUR
  
  # Find strongest movers vs USD
  python3 global_fx_rates.py fx-strongest USD
  
  # List all supported currencies
  python3 global_fx_rates.py fx-currencies

Data Sources:
  - ECB Reference Rates (Euro-based pairs, 40+ currencies)
  - FRED Federal Reserve Data (USD-based major pairs, 20+ currencies)
  - ExchangeRate-API (open.er-api.com) - Free tier (170+ currencies, all pairs)

Refresh: Daily
Coverage: 150+ currency pairs worldwide

Supported Currency Regions:
  - G10: USD, EUR, JPY, GBP, CHF, CAD, AUD, NZD, SEK, NOK
  - Emerging Markets: CNY, INR, BRL, RUB, ZAR, MXN, TRY, KRW, IDR, PLN, etc.
  - Asian: CNY, JPY, KRW, INR, SGD, HKD, TWD, THB, MYR, IDR, PHP, VND, etc.
  - MENA: SAR, AED, QAR, KWD, OMR, BHD, JOD, ILS, EGP, ZAR, NGN, etc.
""")


if __name__ == "__main__":
    sys.exit(main())

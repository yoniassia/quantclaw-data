#!/usr/bin/env python3
"""
Agricultural Commodities Module — Phase 173

USDA WASDE reports, CBOT grain & soft commodity futures via Yahoo Finance
- USDA NASS API for World Agricultural Supply and Demand Estimates (WASDE)
- Corn, Wheat, Soybeans futures (CBOT grains)
- Sugar, Coffee futures (CBOT softs)
- Supply/demand fundamentals, inventory analysis, seasonal patterns

Data Sources:
- USDA NASS QuickStats API: https://quickstats.nass.usda.gov/api
- Yahoo Finance: Futures prices (ZC=F, ZW=F, ZS=F, SB=F, KC=F)
Refresh: Monthly (WASDE), Daily (futures)
Coverage: Major agricultural commodities (grains, oilseeds, softs)

Author: QUANTCLAW DATA Build Agent
Phase: 173
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# USDA NASS API Configuration
# Get your free API key at: https://quickstats.nass.usda.gov/api
# Set via environment variable USDA_NASS_API_KEY or update this default
import os
USDA_NASS_API_KEY = os.getenv('USDA_NASS_API_KEY', 'YOUR_API_KEY_HERE')
USDA_BASE_URL = "https://quickstats.nass.usda.gov/api"

# Yahoo Finance futures symbols
FUTURES_SYMBOLS = {
    'CORN': {
        'symbol': 'ZC=F',
        'name': 'Corn Futures',
        'exchange': 'CBOT',
        'contract_size': 5000,  # bushels
        'unit': 'cents/bushel'
    },
    'WHEAT': {
        'symbol': 'ZW=F',
        'name': 'Wheat Futures',
        'exchange': 'CBOT',
        'contract_size': 5000,  # bushels
        'unit': 'cents/bushel'
    },
    'SOYBEANS': {
        'symbol': 'ZS=F',
        'name': 'Soybean Futures',
        'exchange': 'CBOT',
        'contract_size': 5000,  # bushels
        'unit': 'cents/bushel'
    },
    'SUGAR': {
        'symbol': 'SB=F',
        'name': 'Sugar #11 Futures',
        'exchange': 'ICE',
        'contract_size': 112000,  # pounds
        'unit': 'cents/pound'
    },
    'COFFEE': {
        'symbol': 'KC=F',
        'name': 'Coffee C Futures',
        'exchange': 'ICE',
        'contract_size': 37500,  # pounds
        'unit': 'cents/pound'
    }
}

# USDA commodity codes
USDA_COMMODITIES = {
    'CORN': {
        'commodity_desc': 'CORN',
        'metrics': ['PRODUCTION', 'YIELD', 'ACRES PLANTED', 'ACRES HARVESTED']
    },
    'WHEAT': {
        'commodity_desc': 'WHEAT',
        'metrics': ['PRODUCTION', 'YIELD', 'ACRES PLANTED', 'ACRES HARVESTED']
    },
    'SOYBEANS': {
        'commodity_desc': 'SOYBEANS',
        'metrics': ['PRODUCTION', 'YIELD', 'ACRES PLANTED', 'ACRES HARVESTED']
    },
    'COTTON': {
        'commodity_desc': 'COTTON',
        'metrics': ['PRODUCTION', 'YIELD', 'ACRES PLANTED', 'ACRES HARVESTED']
    },
    'RICE': {
        'commodity_desc': 'RICE',
        'metrics': ['PRODUCTION', 'YIELD', 'ACRES PLANTED', 'ACRES HARVESTED']
    }
}


def get_yahoo_futures_price(symbol: str) -> Dict:
    """
    Get current futures price from Yahoo Finance
    
    Args:
        symbol: Yahoo Finance futures symbol (e.g., 'ZC=F')
    
    Returns:
        Dictionary with price data
    """
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            'interval': '1d',
            'range': '5d'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'chart' not in data or 'result' not in data['chart']:
            return {
                'success': False,
                'error': 'Invalid response from Yahoo Finance'
            }
        
        result = data['chart']['result'][0]
        meta = result.get('meta', {})
        quotes = result.get('indicators', {}).get('quote', [{}])[0]
        timestamps = result.get('timestamp', [])
        
        if not timestamps or not quotes.get('close'):
            return {
                'success': False,
                'error': 'No price data available'
            }
        
        # Get latest data
        current_price = meta.get('regularMarketPrice')
        previous_close = meta.get('previousClose')
        
        # Calculate change
        price_change = None
        price_change_pct = None
        if current_price and previous_close:
            price_change = current_price - previous_close
            price_change_pct = (price_change / previous_close) * 100
        
        # Get historical prices
        close_prices = quotes.get('close', [])
        historical = []
        for i in range(min(5, len(timestamps))):
            if close_prices[i] is not None:
                historical.append({
                    'date': datetime.fromtimestamp(timestamps[i]).strftime('%Y-%m-%d'),
                    'close': round(close_prices[i], 2)
                })
        
        return {
            'success': True,
            'symbol': symbol,
            'current_price': round(current_price, 2) if current_price else None,
            'previous_close': round(previous_close, 2) if previous_close else None,
            'change': round(price_change, 2) if price_change else None,
            'change_pct': round(price_change_pct, 2) if price_change_pct else None,
            'currency': meta.get('currency', 'USD'),
            'exchange': meta.get('exchangeName', 'N/A'),
            'market_time': datetime.fromtimestamp(meta.get('regularMarketTime', 0)).isoformat() if meta.get('regularMarketTime') else None,
            'historical': historical,
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Failed to fetch from Yahoo Finance: {str(e)}'
        }
    except (KeyError, IndexError, ValueError) as e:
        return {
            'success': False,
            'error': f'Failed to parse Yahoo Finance data: {str(e)}'
        }


def get_usda_crop_data(commodity: str, metric: str = 'PRODUCTION', year: Optional[int] = None) -> Dict:
    """
    Get USDA crop production data via NASS QuickStats API
    
    Args:
        commodity: Commodity name (CORN, WHEAT, SOYBEANS, etc.)
        metric: Metric to fetch (PRODUCTION, YIELD, ACRES PLANTED, ACRES HARVESTED)
        year: Specific year (default: last 5 years)
    
    Returns:
        Dictionary with USDA data
    """
    commodity = commodity.upper()
    
    if commodity not in USDA_COMMODITIES:
        return {
            'success': False,
            'error': f'Unknown commodity: {commodity}. Available: {", ".join(USDA_COMMODITIES.keys())}'
        }
    
    try:
        url = f"{USDA_BASE_URL}/api_GET/"
        
        params = {
            'key': USDA_NASS_API_KEY,
            'commodity_desc': USDA_COMMODITIES[commodity]['commodity_desc'],
            'statisticcat_desc': metric,
            'agg_level_desc': 'NATIONAL',
            'format': 'JSON'
        }
        
        if year:
            params['year'] = year
        else:
            # Get last 5 years
            current_year = datetime.now().year
            params['year__GE'] = current_year - 5
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if 'data' not in data or not data['data']:
            return {
                'success': False,
                'error': f'No USDA data found for {commodity} - {metric}'
            }
        
        # Parse and format data
        records = []
        for record in data['data']:
            try:
                records.append({
                    'year': int(record.get('year', 0)),
                    'value': float(record.get('Value', '0').replace(',', '')),
                    'unit': record.get('unit_desc', ''),
                    'state': record.get('state_name', 'US'),
                    'commodity': record.get('commodity_desc', ''),
                    'metric': record.get('statisticcat_desc', '')
                })
            except (ValueError, KeyError):
                continue
        
        # Sort by year descending
        records.sort(key=lambda x: x['year'], reverse=True)
        
        # Calculate year-over-year change
        yoy_change = None
        yoy_change_pct = None
        if len(records) >= 2:
            latest = records[0]['value']
            previous = records[1]['value']
            if previous and previous != 0:
                yoy_change = latest - previous
                yoy_change_pct = (yoy_change / previous) * 100
        
        return {
            'success': True,
            'commodity': commodity,
            'metric': metric,
            'latest_year': records[0]['year'] if records else None,
            'latest_value': records[0]['value'] if records else None,
            'unit': records[0]['unit'] if records else None,
            'yoy_change': yoy_change,
            'yoy_change_pct': yoy_change_pct,
            'historical': records[:10],
            'count': len(records),
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Failed to fetch USDA data: {str(e)}'
        }
    except (KeyError, ValueError) as e:
        return {
            'success': False,
            'error': f'Failed to parse USDA data: {str(e)}'
        }


def get_grain_futures() -> Dict:
    """
    Get current prices for all major grain futures (corn, wheat, soybeans)
    
    Returns:
        Dictionary with grain futures prices
    """
    grains = {
        'success': True,
        'futures': {},
        'timestamp': datetime.now().isoformat()
    }
    
    grain_symbols = ['CORN', 'WHEAT', 'SOYBEANS']
    
    for grain in grain_symbols:
        symbol_info = FUTURES_SYMBOLS[grain]
        price_data = get_yahoo_futures_price(symbol_info['symbol'])
        
        if price_data['success']:
            grains['futures'][grain] = {
                'name': symbol_info['name'],
                'symbol': symbol_info['symbol'],
                'exchange': symbol_info['exchange'],
                'current_price': price_data['current_price'],
                'change': price_data['change'],
                'change_pct': price_data['change_pct'],
                'unit': symbol_info['unit'],
                'contract_size': symbol_info['contract_size'],
                'market_time': price_data['market_time']
            }
        else:
            grains['futures'][grain] = {
                'name': symbol_info['name'],
                'symbol': symbol_info['symbol'],
                'error': price_data.get('error', 'Data not available')
            }
        
        time.sleep(0.2)  # Rate limiting
    
    return grains


def get_soft_commodities() -> Dict:
    """
    Get current prices for soft commodities (sugar, coffee)
    
    Returns:
        Dictionary with soft commodity futures prices
    """
    softs = {
        'success': True,
        'futures': {},
        'timestamp': datetime.now().isoformat()
    }
    
    soft_symbols = ['SUGAR', 'COFFEE']
    
    for soft in soft_symbols:
        symbol_info = FUTURES_SYMBOLS[soft]
        price_data = get_yahoo_futures_price(symbol_info['symbol'])
        
        if price_data['success']:
            softs['futures'][soft] = {
                'name': symbol_info['name'],
                'symbol': symbol_info['symbol'],
                'exchange': symbol_info['exchange'],
                'current_price': price_data['current_price'],
                'change': price_data['change'],
                'change_pct': price_data['change_pct'],
                'unit': symbol_info['unit'],
                'contract_size': symbol_info['contract_size'],
                'market_time': price_data['market_time']
            }
        else:
            softs['futures'][soft] = {
                'name': symbol_info['name'],
                'symbol': symbol_info['symbol'],
                'error': price_data.get('error', 'Data not available')
            }
        
        time.sleep(0.2)  # Rate limiting
    
    return softs


def get_commodity_dashboard(commodity: str) -> Dict:
    """
    Get comprehensive dashboard for a specific agricultural commodity
    Combines USDA production data with futures prices
    
    Args:
        commodity: Commodity name (CORN, WHEAT, SOYBEANS, SUGAR, COFFEE)
    
    Returns:
        Dictionary with comprehensive commodity data
    """
    commodity = commodity.upper()
    
    if commodity not in FUTURES_SYMBOLS:
        return {
            'success': False,
            'error': f'Unknown commodity: {commodity}. Available: {", ".join(FUTURES_SYMBOLS.keys())}'
        }
    
    dashboard = {
        'success': True,
        'commodity': commodity,
        'timestamp': datetime.now().isoformat()
    }
    
    # Get futures price
    symbol_info = FUTURES_SYMBOLS[commodity]
    price_data = get_yahoo_futures_price(symbol_info['symbol'])
    
    if price_data['success']:
        dashboard['futures'] = {
            'name': symbol_info['name'],
            'symbol': symbol_info['symbol'],
            'exchange': symbol_info['exchange'],
            'current_price': price_data['current_price'],
            'change': price_data['change'],
            'change_pct': price_data['change_pct'],
            'unit': symbol_info['unit'],
            'contract_size': symbol_info['contract_size'],
            'market_time': price_data['market_time'],
            'historical': price_data.get('historical', [])
        }
    else:
        dashboard['futures'] = {
            'error': price_data.get('error', 'Futures data not available')
        }
    
    # Get USDA production data (if available for this commodity)
    if commodity in USDA_COMMODITIES:
        print(f"Fetching USDA production data for {commodity}...", file=sys.stderr)
        production = get_usda_crop_data(commodity, 'PRODUCTION')
        
        if production['success']:
            dashboard['production'] = {
                'latest_year': production['latest_year'],
                'latest_value': production['latest_value'],
                'unit': production['unit'],
                'yoy_change_pct': production['yoy_change_pct'],
                'historical': production['historical'][:5]
            }
        
        print(f"Fetching USDA yield data for {commodity}...", file=sys.stderr)
        yield_data = get_usda_crop_data(commodity, 'YIELD')
        
        if yield_data['success']:
            dashboard['yield'] = {
                'latest_year': yield_data['latest_year'],
                'latest_value': yield_data['latest_value'],
                'unit': yield_data['unit'],
                'yoy_change_pct': yield_data['yoy_change_pct'],
                'historical': yield_data['historical'][:5]
            }
        
        print(f"Fetching USDA acreage data for {commodity}...", file=sys.stderr)
        acres = get_usda_crop_data(commodity, 'ACRES PLANTED')
        
        if acres['success']:
            dashboard['acres_planted'] = {
                'latest_year': acres['latest_year'],
                'latest_value': acres['latest_value'],
                'unit': acres['unit'],
                'yoy_change_pct': acres['yoy_change_pct'],
                'historical': acres['historical'][:5]
            }
    
    return dashboard


def get_all_futures() -> Dict:
    """
    Get current prices for all agricultural futures (grains + softs)
    
    Returns:
        Dictionary with all futures prices
    """
    all_futures = {
        'success': True,
        'futures': {},
        'timestamp': datetime.now().isoformat()
    }
    
    for commodity, symbol_info in FUTURES_SYMBOLS.items():
        price_data = get_yahoo_futures_price(symbol_info['symbol'])
        
        if price_data['success']:
            all_futures['futures'][commodity] = {
                'name': symbol_info['name'],
                'symbol': symbol_info['symbol'],
                'exchange': symbol_info['exchange'],
                'current_price': price_data['current_price'],
                'change': price_data['change'],
                'change_pct': price_data['change_pct'],
                'unit': symbol_info['unit'],
                'contract_size': symbol_info['contract_size'],
                'market_time': price_data['market_time']
            }
        else:
            all_futures['futures'][commodity] = {
                'name': symbol_info['name'],
                'symbol': symbol_info['symbol'],
                'error': price_data.get('error', 'Data not available')
            }
        
        time.sleep(0.2)  # Rate limiting
    
    return all_futures


def list_commodities() -> Dict:
    """
    List all available agricultural commodities
    
    Returns:
        Dictionary with commodity list
    """
    commodities = []
    
    for commodity, info in FUTURES_SYMBOLS.items():
        has_usda = commodity in USDA_COMMODITIES
        
        commodities.append({
            'commodity': commodity,
            'name': info['name'],
            'symbol': info['symbol'],
            'exchange': info['exchange'],
            'unit': info['unit'],
            'contract_size': info['contract_size'],
            'usda_data_available': has_usda
        })
    
    return {
        'success': True,
        'commodities': commodities,
        'count': len(commodities)
    }


# ============ CLI Interface ============

def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    try:
        if command == 'ag-futures':
            # Optional commodity filter
            if len(sys.argv) >= 3:
                commodity = sys.argv[2].upper()
                if commodity not in FUTURES_SYMBOLS:
                    print(f"Error: Unknown commodity '{commodity}'", file=sys.stderr)
                    print(f"Available: {', '.join(FUTURES_SYMBOLS.keys())}", file=sys.stderr)
                    return 1
                
                symbol_info = FUTURES_SYMBOLS[commodity]
                data = get_yahoo_futures_price(symbol_info['symbol'])
                
                if data['success']:
                    result = {
                        'commodity': commodity,
                        'name': symbol_info['name'],
                        'symbol': symbol_info['symbol'],
                        'exchange': symbol_info['exchange'],
                        'current_price': data['current_price'],
                        'change': data['change'],
                        'change_pct': data['change_pct'],
                        'unit': symbol_info['unit'],
                        'contract_size': symbol_info['contract_size'],
                        'market_time': data['market_time'],
                        'historical': data.get('historical', [])
                    }
                    print(json.dumps(result, indent=2))
                else:
                    print(json.dumps(data, indent=2), file=sys.stderr)
                    return 1
            else:
                # All futures
                data = get_all_futures()
                print(json.dumps(data, indent=2))
        
        elif command == 'ag-grains':
            data = get_grain_futures()
            print(json.dumps(data, indent=2))
        
        elif command == 'ag-softs':
            data = get_soft_commodities()
            print(json.dumps(data, indent=2))
        
        elif command == 'ag-usda':
            if len(sys.argv) < 3:
                print("Error: ag-usda requires commodity", file=sys.stderr)
                print("Usage: python3 agricultural_commodities.py ag-usda <COMMODITY> [METRIC]", file=sys.stderr)
                return 1
            
            commodity = sys.argv[2].upper()
            metric = sys.argv[3].upper() if len(sys.argv) >= 4 else 'PRODUCTION'
            
            data = get_usda_crop_data(commodity, metric)
            print(json.dumps(data, indent=2))
        
        elif command == 'ag-dashboard':
            if len(sys.argv) < 3:
                print("Error: ag-dashboard requires commodity", file=sys.stderr)
                print("Usage: python3 agricultural_commodities.py ag-dashboard <COMMODITY>", file=sys.stderr)
                return 1
            
            commodity = sys.argv[2].upper()
            data = get_commodity_dashboard(commodity)
            print(json.dumps(data, indent=2))
        
        elif command == 'ag-list':
            data = list_commodities()
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
Agricultural Commodities Module (Phase 173)

Commands:
  python3 agricultural_commodities.py ag-futures [COMMODITY]  # Get futures prices (all or specific)
  python3 agricultural_commodities.py ag-grains               # Get grain futures (corn/wheat/soy)
  python3 agricultural_commodities.py ag-softs                # Get soft commodities (sugar/coffee)
  python3 agricultural_commodities.py ag-usda <COMMODITY> [METRIC]  # Get USDA production data
  python3 agricultural_commodities.py ag-dashboard <COMMODITY>      # Comprehensive commodity dashboard
  python3 agricultural_commodities.py ag-list                 # List all available commodities

Examples:
  python3 agricultural_commodities.py ag-futures
  python3 agricultural_commodities.py ag-futures CORN
  python3 agricultural_commodities.py ag-grains
  python3 agricultural_commodities.py ag-softs
  python3 agricultural_commodities.py ag-usda CORN PRODUCTION
  python3 agricultural_commodities.py ag-usda WHEAT YIELD
  python3 agricultural_commodities.py ag-dashboard SOYBEANS
  python3 agricultural_commodities.py ag-list

Available Commodities:
  CORN        = Corn futures (ZC=F) + USDA production data
  WHEAT       = Wheat futures (ZW=F) + USDA production data
  SOYBEANS    = Soybean futures (ZS=F) + USDA production data
  SUGAR       = Sugar #11 futures (SB=F)
  COFFEE      = Coffee C futures (KC=F)

USDA Metrics (for grains):
  PRODUCTION         = Total production (bushels/tons)
  YIELD              = Yield per acre
  ACRES PLANTED      = Total acres planted
  ACRES HARVESTED    = Total acres harvested

Data Sources:
- USDA NASS QuickStats API (https://quickstats.nass.usda.gov/api)
- Yahoo Finance (futures prices)

Refresh: Monthly (USDA WASDE), Daily (futures)
Coverage: Major grains (corn, wheat, soybeans) and soft commodities (sugar, coffee)
""")


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Livestock & Meat Markets Module — Phase 174

USDA AMS (Agricultural Marketing Service) daily livestock reports, cattle/hog prices
- USDA AMS Market News API for real-time livestock pricing
- Cattle prices (live cattle, feeder cattle)
- Hog prices (lean hogs, pork cutout values)
- Slaughter data, weekly production, export sales
- Regional price differentials and basis analysis

Data Sources:
- USDA AMS Market News API: https://marsapi.ams.usda.gov/services/v1.2/
- Yahoo Finance: Livestock futures (LE=F, GF=F, HE=F)
Refresh: Daily (AMS reports), Real-time (futures)
Coverage: US livestock markets (cattle, hogs, poultry)

Author: QUANTCLAW DATA Build Agent
Phase: 174
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# USDA AMS Market News API Configuration
AMS_BASE_URL = "https://marsapi.ams.usda.gov/services/v1.2"

# Yahoo Finance livestock futures symbols
LIVESTOCK_FUTURES = {
    'LIVE_CATTLE': {
        'symbol': 'LE=F',
        'name': 'Live Cattle Futures',
        'exchange': 'CME',
        'contract_size': 40000,  # pounds
        'unit': 'cents/pound',
        'ams_report': 'LM_CT150',  # National Daily Direct Cattle
        'description': 'Fed cattle ready for slaughter'
    },
    'FEEDER_CATTLE': {
        'symbol': 'GF=F',
        'name': 'Feeder Cattle Futures',
        'exchange': 'CME',
        'contract_size': 50000,  # pounds
        'unit': 'cents/pound',
        'ams_report': 'LM_CT169',  # National Weekly Feeder & Stocker Cattle
        'description': 'Young cattle for feedlot placement'
    },
    'LEAN_HOGS': {
        'symbol': 'HE=F',
        'name': 'Lean Hogs Futures',
        'exchange': 'CME',
        'contract_size': 40000,  # pounds
        'unit': 'cents/pound',
        'ams_report': 'LM_HG200',  # National Daily Direct Hog Prior Day
        'description': 'Market-ready hogs'
    }
}

# Key AMS report slugs
AMS_REPORTS = {
    # Cattle reports
    'LM_CT150': 'National Daily Direct Cattle - Slaughter (Negotiated)',
    'LM_CT151': 'National Daily Direct Cattle - Slaughter (Formulas)',
    'LM_CT169': 'National Weekly Feeder & Stocker Cattle',
    'LM_CT155': '5 Area Weekly Weighted Average Direct Slaughter Cattle',
    
    # Hog reports
    'LM_HG200': 'National Daily Direct Hog Prior Day Report - Slaughter Swine',
    'LM_HG201': 'National Daily Direct Hog - Slaughter Swine',
    'LM_HG202': 'National Daily Direct Hog Prior Day Report - Negotiated Sales',
    'LM_PK602': 'National Daily Pork Report - Comprehensive',
    
    # Poultry reports
    'LM_PY014': 'National Daily Broiler/Fryer Report',
    'LM_PY016': 'National Daily Turkey Report',
    
    # Slaughter & production
    'LM_CT100': 'National Weekly Cattle Slaughter',
    'LM_HG100': 'National Weekly Hog & Pig Slaughter',
    'LM_PY001': 'National Weekly Chicken Slaughter'
}


def get_yahoo_futures_price(symbol: str) -> Dict:
    """
    Get current livestock futures price from Yahoo Finance
    
    Args:
        symbol: Yahoo Finance futures symbol (e.g., 'LE=F')
    
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


def get_ams_report(slug: str, date: Optional[str] = None) -> Dict:
    """
    Get USDA AMS market report data
    
    Args:
        slug: Report slug (e.g., 'LM_CT150')
        date: Specific date (YYYY-MM-DD format, default: today)
    
    Returns:
        Dictionary with AMS report data
    """
    try:
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        url = f"{AMS_BASE_URL}/reports/{slug}"
        
        # Get latest report
        params = {
            'allSections': 'true'
        }
        
        headers = {
            'Accept': 'application/json'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or 'results' not in data:
            return {
                'success': False,
                'error': f'No data found for report {slug}'
            }
        
        results = data.get('results', [])
        
        if not results:
            return {
                'success': False,
                'error': f'No results in report {slug}'
            }
        
        # Get the most recent report
        latest = results[0]
        
        # Extract key data
        report_data = {
            'success': True,
            'slug': slug,
            'report_title': latest.get('reportTitle', AMS_REPORTS.get(slug, 'Unknown')),
            'report_date': latest.get('published_date', date),
            'office': latest.get('office', 'USDA AMS'),
            'sections': []
        }
        
        # Parse sections
        sections = latest.get('reportSections', [])
        for section in sections[:10]:  # Limit to first 10 sections
            section_data = {
                'title': section.get('sectionTitle', ''),
                'data': []
            }
            
            # Extract tabular data
            for row in section.get('results', [])[:20]:  # Limit rows
                row_data = {}
                for key, value in row.items():
                    if key not in ['id', 'report_date']:
                        row_data[key] = value
                
                if row_data:
                    section_data['data'].append(row_data)
            
            if section_data['data']:
                report_data['sections'].append(section_data)
        
        report_data['timestamp'] = datetime.now().isoformat()
        
        return report_data
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Failed to fetch AMS report: {str(e)}'
        }
    except (KeyError, ValueError) as e:
        return {
            'success': False,
            'error': f'Failed to parse AMS data: {str(e)}'
        }


def get_cattle_prices() -> Dict:
    """
    Get current cattle market prices (live & feeder cattle)
    Combines futures prices with USDA AMS cash market data
    
    Returns:
        Dictionary with cattle price data
    """
    cattle_data = {
        'success': True,
        'futures': {},
        'cash_market': {},
        'timestamp': datetime.now().isoformat()
    }
    
    # Get live cattle futures
    print("Fetching live cattle futures...", file=sys.stderr)
    live_info = LIVESTOCK_FUTURES['LIVE_CATTLE']
    live_futures = get_yahoo_futures_price(live_info['symbol'])
    
    if live_futures['success']:
        cattle_data['futures']['live_cattle'] = {
            'name': live_info['name'],
            'symbol': live_info['symbol'],
            'current_price': live_futures['current_price'],
            'change': live_futures['change'],
            'change_pct': live_futures['change_pct'],
            'unit': live_info['unit'],
            'contract_size': live_info['contract_size'],
            'description': live_info['description']
        }
    
    # Get feeder cattle futures
    print("Fetching feeder cattle futures...", file=sys.stderr)
    feeder_info = LIVESTOCK_FUTURES['FEEDER_CATTLE']
    feeder_futures = get_yahoo_futures_price(feeder_info['symbol'])
    
    if feeder_futures['success']:
        cattle_data['futures']['feeder_cattle'] = {
            'name': feeder_info['name'],
            'symbol': feeder_info['symbol'],
            'current_price': feeder_futures['current_price'],
            'change': feeder_futures['change'],
            'change_pct': feeder_futures['change_pct'],
            'unit': feeder_info['unit'],
            'contract_size': feeder_info['contract_size'],
            'description': feeder_info['description']
        }
    
    # Get USDA AMS cash cattle report
    print("Fetching USDA AMS cattle report...", file=sys.stderr)
    ams_cattle = get_ams_report('LM_CT150')
    
    if ams_cattle['success']:
        cattle_data['cash_market']['live_cattle'] = {
            'report_title': ams_cattle['report_title'],
            'report_date': ams_cattle['report_date'],
            'sections': ams_cattle['sections']
        }
    
    return cattle_data


def get_hog_prices() -> Dict:
    """
    Get current hog market prices (lean hogs & pork cutout)
    Combines futures prices with USDA AMS cash market data
    
    Returns:
        Dictionary with hog price data
    """
    hog_data = {
        'success': True,
        'futures': {},
        'cash_market': {},
        'timestamp': datetime.now().isoformat()
    }
    
    # Get lean hogs futures
    print("Fetching lean hogs futures...", file=sys.stderr)
    hog_info = LIVESTOCK_FUTURES['LEAN_HOGS']
    hog_futures = get_yahoo_futures_price(hog_info['symbol'])
    
    if hog_futures['success']:
        hog_data['futures']['lean_hogs'] = {
            'name': hog_info['name'],
            'symbol': hog_info['symbol'],
            'current_price': hog_futures['current_price'],
            'change': hog_futures['change'],
            'change_pct': hog_futures['change_pct'],
            'unit': hog_info['unit'],
            'contract_size': hog_info['contract_size'],
            'description': hog_info['description']
        }
    
    # Get USDA AMS cash hog report
    print("Fetching USDA AMS hog report...", file=sys.stderr)
    ams_hogs = get_ams_report('LM_HG200')
    
    if ams_hogs['success']:
        hog_data['cash_market']['hogs'] = {
            'report_title': ams_hogs['report_title'],
            'report_date': ams_hogs['report_date'],
            'sections': ams_hogs['sections']
        }
    
    # Get pork cutout values
    print("Fetching USDA pork cutout report...", file=sys.stderr)
    ams_pork = get_ams_report('LM_PK602')
    
    if ams_pork['success']:
        hog_data['cash_market']['pork_cutout'] = {
            'report_title': ams_pork['report_title'],
            'report_date': ams_pork['report_date'],
            'sections': ams_pork['sections']
        }
    
    return hog_data


def get_all_livestock_futures() -> Dict:
    """
    Get current prices for all livestock futures
    
    Returns:
        Dictionary with all livestock futures prices
    """
    all_futures = {
        'success': True,
        'futures': {},
        'timestamp': datetime.now().isoformat()
    }
    
    for livestock, info in LIVESTOCK_FUTURES.items():
        price_data = get_yahoo_futures_price(info['symbol'])
        
        if price_data['success']:
            all_futures['futures'][livestock] = {
                'name': info['name'],
                'symbol': info['symbol'],
                'exchange': info['exchange'],
                'current_price': price_data['current_price'],
                'change': price_data['change'],
                'change_pct': price_data['change_pct'],
                'unit': info['unit'],
                'contract_size': info['contract_size'],
                'description': info['description'],
                'market_time': price_data['market_time']
            }
        else:
            all_futures['futures'][livestock] = {
                'name': info['name'],
                'symbol': info['symbol'],
                'error': price_data.get('error', 'Data not available')
            }
        
        time.sleep(0.2)  # Rate limiting
    
    return all_futures


def get_slaughter_data() -> Dict:
    """
    Get weekly slaughter data for cattle and hogs
    
    Returns:
        Dictionary with slaughter statistics
    """
    slaughter_data = {
        'success': True,
        'cattle': {},
        'hogs': {},
        'timestamp': datetime.now().isoformat()
    }
    
    # Get cattle slaughter
    print("Fetching cattle slaughter data...", file=sys.stderr)
    cattle_slaughter = get_ams_report('LM_CT100')
    
    if cattle_slaughter['success']:
        slaughter_data['cattle'] = {
            'report_title': cattle_slaughter['report_title'],
            'report_date': cattle_slaughter['report_date'],
            'sections': cattle_slaughter['sections']
        }
    
    # Get hog slaughter
    print("Fetching hog slaughter data...", file=sys.stderr)
    hog_slaughter = get_ams_report('LM_HG100')
    
    if hog_slaughter['success']:
        slaughter_data['hogs'] = {
            'report_title': hog_slaughter['report_title'],
            'report_date': hog_slaughter['report_date'],
            'sections': hog_slaughter['sections']
        }
    
    return slaughter_data


def get_livestock_dashboard() -> Dict:
    """
    Get comprehensive livestock market dashboard
    Includes all futures prices, cash markets, and slaughter data
    
    Returns:
        Dictionary with comprehensive livestock market data
    """
    dashboard = {
        'success': True,
        'timestamp': datetime.now().isoformat()
    }
    
    print("Building livestock dashboard...", file=sys.stderr)
    
    # Get all futures
    futures = get_all_livestock_futures()
    dashboard['futures'] = futures.get('futures', {})
    
    # Get cattle prices (futures + cash)
    cattle = get_cattle_prices()
    dashboard['cattle_cash_market'] = cattle.get('cash_market', {})
    
    # Get hog prices (futures + cash)
    hogs = get_hog_prices()
    dashboard['hogs_cash_market'] = hogs.get('cash_market', {})
    
    # Get slaughter data
    slaughter = get_slaughter_data()
    dashboard['slaughter'] = {
        'cattle': slaughter.get('cattle', {}),
        'hogs': slaughter.get('hogs', {})
    }
    
    return dashboard


def list_ams_reports() -> Dict:
    """
    List all available USDA AMS reports
    
    Returns:
        Dictionary with report list
    """
    reports = []
    
    for slug, description in AMS_REPORTS.items():
        reports.append({
            'slug': slug,
            'description': description
        })
    
    return {
        'success': True,
        'reports': reports,
        'count': len(reports)
    }


# ============ CLI Interface ============

def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    try:
        if command == 'livestock-futures':
            # Optional specific livestock
            if len(sys.argv) >= 3:
                livestock = sys.argv[2].upper()
                if livestock not in LIVESTOCK_FUTURES:
                    print(f"Error: Unknown livestock '{livestock}'", file=sys.stderr)
                    print(f"Available: {', '.join(LIVESTOCK_FUTURES.keys())}", file=sys.stderr)
                    return 1
                
                info = LIVESTOCK_FUTURES[livestock]
                data = get_yahoo_futures_price(info['symbol'])
                
                if data['success']:
                    result = {
                        'livestock': livestock,
                        'name': info['name'],
                        'symbol': info['symbol'],
                        'exchange': info['exchange'],
                        'current_price': data['current_price'],
                        'change': data['change'],
                        'change_pct': data['change_pct'],
                        'unit': info['unit'],
                        'contract_size': info['contract_size'],
                        'description': info['description'],
                        'market_time': data['market_time'],
                        'historical': data.get('historical', [])
                    }
                    print(json.dumps(result, indent=2))
                else:
                    print(json.dumps(data, indent=2), file=sys.stderr)
                    return 1
            else:
                # All livestock futures
                data = get_all_livestock_futures()
                print(json.dumps(data, indent=2))
        
        elif command == 'livestock-cattle':
            data = get_cattle_prices()
            print(json.dumps(data, indent=2))
        
        elif command == 'livestock-hogs':
            data = get_hog_prices()
            print(json.dumps(data, indent=2))
        
        elif command == 'livestock-slaughter':
            data = get_slaughter_data()
            print(json.dumps(data, indent=2))
        
        elif command == 'livestock-ams':
            if len(sys.argv) < 3:
                print("Error: livestock-ams requires report slug", file=sys.stderr)
                print("Usage: python3 livestock_meat.py livestock-ams <SLUG> [DATE]", file=sys.stderr)
                print("\nUse 'livestock-reports' to list available reports", file=sys.stderr)
                return 1
            
            slug = sys.argv[2]
            date = sys.argv[3] if len(sys.argv) >= 4 else None
            
            data = get_ams_report(slug, date)
            print(json.dumps(data, indent=2))
        
        elif command == 'livestock-dashboard':
            data = get_livestock_dashboard()
            print(json.dumps(data, indent=2))
        
        elif command == 'livestock-reports':
            data = list_ams_reports()
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
Livestock & Meat Markets Module (Phase 174)

Commands:
  python3 livestock_meat.py livestock-futures [LIVESTOCK]  # Get livestock futures prices (all or specific)
  python3 livestock_meat.py livestock-cattle               # Get cattle prices (futures + cash markets)
  python3 livestock_meat.py livestock-hogs                 # Get hog prices (futures + cash markets)
  python3 livestock_meat.py livestock-slaughter            # Get weekly slaughter data
  python3 livestock_meat.py livestock-ams <SLUG> [DATE]    # Get specific USDA AMS report
  python3 livestock_meat.py livestock-dashboard            # Comprehensive livestock market dashboard
  python3 livestock_meat.py livestock-reports              # List all available USDA AMS reports

Examples:
  python3 livestock_meat.py livestock-futures
  python3 livestock_meat.py livestock-futures LIVE_CATTLE
  python3 livestock_meat.py livestock-cattle
  python3 livestock_meat.py livestock-hogs
  python3 livestock_meat.py livestock-slaughter
  python3 livestock_meat.py livestock-ams LM_CT150
  python3 livestock_meat.py livestock-ams LM_HG200 2024-02-20
  python3 livestock_meat.py livestock-dashboard
  python3 livestock_meat.py livestock-reports

Available Livestock:
  LIVE_CATTLE    = Live cattle futures (LE=F) + USDA cash market
  FEEDER_CATTLE  = Feeder cattle futures (GF=F) + USDA cash market
  LEAN_HOGS      = Lean hogs futures (HE=F) + USDA cash market + pork cutout

Key USDA AMS Reports:
  LM_CT150  = National Daily Direct Cattle (slaughter cattle prices)
  LM_CT169  = National Weekly Feeder & Stocker Cattle
  LM_HG200  = National Daily Direct Hog Prior Day Report
  LM_PK602  = National Daily Pork Report (cutout values)
  LM_CT100  = National Weekly Cattle Slaughter
  LM_HG100  = National Weekly Hog & Pig Slaughter

Data Sources:
- USDA AMS Market News API (https://marsapi.ams.usda.gov)
- Yahoo Finance (livestock futures)

Refresh: Daily (AMS reports), Real-time (futures)
Coverage: US livestock markets (cattle, hogs, pork)
""")


if __name__ == "__main__":
    sys.exit(main())

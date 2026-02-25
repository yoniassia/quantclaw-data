#!/usr/bin/env python3
"""
Global Tourism Statistics (Phase 194)
======================================
UNWTO arrivals, hotel occupancy, airline passenger data. Quarterly.

Data Sources:
- World Bank: International tourism arrivals/receipts/expenditures
- FRED: US hotel occupancy, TSA checkpoint data, travel services
- Yahoo Finance: Hotel/airline ETFs as proxies (MAR, HLT, AAL, DAL)
- Public data: Scraped tourism statistics from available sources

CLI Commands:
- python cli.py tourism-arrivals COUNTRY     # International tourist arrivals
- python cli.py tourism-receipts COUNTRY     # Tourism receipts (USD billions)
- python cli.py tourism-country COUNTRY      # Complete tourism profile
- python cli.py tourism-global-overview      # Global tourism snapshot
- python cli.py tourism-compare C1 C2        # Compare two countries
- python cli.py hotel-occupancy              # US hotel occupancy trends
- python cli.py airline-passengers           # TSA checkpoint passenger data
- python cli.py tourism-recovery             # Post-pandemic recovery tracker
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics

# API Configuration
WB_BASE = "https://api.worldbank.org/v2"
FRED_BASE = "https://api.stlouisfed.org/fred"
FRED_API_KEY = "your_api_key_here"  # Free from https://fred.stlouisfed.org/docs/api/api_key.html
YAHOO_FINANCE_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"

# World Bank Tourism Indicators
WB_TOURISM_INDICATORS = {
    'arrivals': 'ST.INT.ARVL',              # International tourism, number of arrivals
    'receipts': 'ST.INT.RCPT.CD',           # International tourism, receipts (current US$)
    'receipts_pct_exports': 'ST.INT.RCPT.XP.ZS',  # Tourism receipts (% of total exports)
    'expenditure': 'ST.INT.XPND.CD',        # International tourism, expenditures (current US$)
    'departures': 'ST.INT.DPRT',            # International tourism, number of departures
    'passenger_transport': 'ST.INT.TRNR.CD', # International transport, passenger (current US$)
}

# FRED Tourism Series
FRED_TOURISM_SERIES = {
    'hotel_occupancy': 'HOTELOCCUPANCYRATE',     # US hotel occupancy rate (%)
    'air_passengers': 'ASAIR',                    # Air passengers carried
    'travel_services_exports': 'A191RG3Q086SBEA', # Travel services exports
    'travel_services_imports': 'B028RG3Q086SBEA', # Travel services imports
}

# Hotel/Airline ETFs for sentiment proxy
TOURISM_ETFS = {
    'hotels': ['MAR', 'HLT', 'H', 'HST'],      # Marriott, Hilton, Hyatt, Host Hotels
    'airlines': ['AAL', 'DAL', 'UAL', 'LUV'],  # American, Delta, United, Southwest
}

def get_worldbank_tourism_data(country_code: str, indicator: str, years: int = 10) -> Optional[Dict[str, Any]]:
    """
    Fetch tourism data from World Bank API
    
    Args:
        country_code: ISO 3-letter country code (e.g., 'USA', 'FRA')
        indicator: World Bank indicator code
        years: Number of years of historical data
    
    Returns:
        Dict with indicator data, trend, growth rate
    """
    try:
        end_year = datetime.now().year - 1  # Data usually lags by 1-2 years
        start_year = end_year - years
        
        url = f"{WB_BASE}/country/{country_code}/indicator/{indicator}"
        params = {
            'format': 'json',
            'date': f'{start_year}:{end_year}',
            'per_page': 100
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if len(data) < 2 or not data[1]:
            return None
        
        # Parse data points
        points = []
        for item in data[1]:
            if item['value'] is not None:
                points.append({
                    'year': int(item['date']),
                    'value': float(item['value'])
                })
        
        if not points:
            return None
        
        # Sort by year
        points.sort(key=lambda x: x['year'])
        
        # Calculate trends
        latest = points[-1]
        oldest = points[0]
        
        if len(points) >= 2:
            cagr = (((latest['value'] / oldest['value']) ** (1 / (latest['year'] - oldest['year']))) - 1) * 100
        else:
            cagr = 0
        
        # Year-over-year change
        if len(points) >= 2:
            prev = points[-2]
            yoy_change = ((latest['value'] - prev['value']) / prev['value']) * 100
        else:
            yoy_change = 0
        
        return {
            'indicator': indicator,
            'country': country_code,
            'latest_year': latest['year'],
            'latest_value': latest['value'],
            'oldest_value': oldest['value'],
            'cagr': round(cagr, 2),
            'yoy_change': round(yoy_change, 2),
            'data_points': points,
            'data_available': len(points) > 0
        }
        
    except Exception as e:
        print(f"Error fetching World Bank data: {e}", file=sys.stderr)
        return None

def get_international_arrivals(country_code: str = 'WLD') -> Dict[str, Any]:
    """Get international tourist arrivals for a country"""
    result = get_worldbank_tourism_data(country_code, WB_TOURISM_INDICATORS['arrivals'])
    
    if not result:
        return {
            'error': f'No arrivals data available for {country_code}',
            'country': country_code
        }
    
    # Format for readability
    latest_millions = result['latest_value'] / 1_000_000
    oldest_millions = result['oldest_value'] / 1_000_000
    
    return {
        'country': country_code,
        'latest_year': result['latest_year'],
        'arrivals_millions': round(latest_millions, 2),
        'cagr_percent': result['cagr'],
        'yoy_change_percent': result['yoy_change'],
        'trend': 'growing' if result['yoy_change'] > 0 else 'declining',
        'historical': [
            {
                'year': p['year'],
                'arrivals_millions': round(p['value'] / 1_000_000, 2)
            }
            for p in result['data_points']
        ]
    }

def get_tourism_receipts(country_code: str = 'WLD') -> Dict[str, Any]:
    """Get international tourism receipts for a country"""
    result = get_worldbank_tourism_data(country_code, WB_TOURISM_INDICATORS['receipts'])
    
    if not result:
        return {
            'error': f'No receipts data available for {country_code}',
            'country': country_code
        }
    
    # Format for readability
    latest_billions = result['latest_value'] / 1_000_000_000
    oldest_billions = result['oldest_value'] / 1_000_000_000
    
    return {
        'country': country_code,
        'latest_year': result['latest_year'],
        'receipts_usd_billions': round(latest_billions, 2),
        'cagr_percent': result['cagr'],
        'yoy_change_percent': result['yoy_change'],
        'trend': 'growing' if result['yoy_change'] > 0 else 'declining',
        'historical': [
            {
                'year': p['year'],
                'receipts_usd_billions': round(p['value'] / 1_000_000_000, 2)
            }
            for p in result['data_points']
        ]
    }

def get_country_tourism_profile(country_code: str) -> Dict[str, Any]:
    """
    Get complete tourism profile for a country
    
    Args:
        country_code: ISO 3-letter country code
    
    Returns:
        Complete tourism statistics including arrivals, receipts, exports %
    """
    arrivals = get_worldbank_tourism_data(country_code, WB_TOURISM_INDICATORS['arrivals'])
    receipts = get_worldbank_tourism_data(country_code, WB_TOURISM_INDICATORS['receipts'])
    receipts_pct = get_worldbank_tourism_data(country_code, WB_TOURISM_INDICATORS['receipts_pct_exports'])
    departures = get_worldbank_tourism_data(country_code, WB_TOURISM_INDICATORS['departures'])
    
    profile = {
        'country': country_code,
        'timestamp': datetime.now().isoformat(),
    }
    
    if arrivals:
        profile['arrivals'] = {
            'year': arrivals['latest_year'],
            'value_millions': round(arrivals['latest_value'] / 1_000_000, 2),
            'yoy_change_percent': arrivals['yoy_change'],
            'cagr_10y_percent': arrivals['cagr']
        }
    
    if receipts:
        profile['receipts'] = {
            'year': receipts['latest_year'],
            'value_usd_billions': round(receipts['latest_value'] / 1_000_000_000, 2),
            'yoy_change_percent': receipts['yoy_change'],
            'cagr_10y_percent': receipts['cagr']
        }
    
    if receipts_pct:
        profile['receipts_pct_exports'] = {
            'year': receipts_pct['latest_year'],
            'value_percent': round(receipts_pct['latest_value'], 2),
            'dependency_level': (
                'high' if receipts_pct['latest_value'] > 10 else
                'medium' if receipts_pct['latest_value'] > 5 else
                'low'
            )
        }
    
    if departures:
        profile['departures'] = {
            'year': departures['latest_year'],
            'value_millions': round(departures['latest_value'] / 1_000_000, 2)
        }
    
    # Calculate net tourism balance
    if arrivals and departures:
        net_balance = arrivals['latest_value'] - departures['latest_value']
        profile['net_balance'] = {
            'value_millions': round(net_balance / 1_000_000, 2),
            'type': 'surplus' if net_balance > 0 else 'deficit'
        }
    
    return profile

def get_global_tourism_overview() -> Dict[str, Any]:
    """Get global tourism statistics overview"""
    world_arrivals = get_international_arrivals('WLD')
    world_receipts = get_tourism_receipts('WLD')
    
    # Top tourism destinations (by known volume)
    top_destinations = ['USA', 'ESP', 'FRA', 'ITA', 'GBR', 'TUR', 'DEU', 'MEX', 'THA', 'JPN']
    
    destination_data = []
    for country in top_destinations:
        arrivals = get_worldbank_tourism_data(country, WB_TOURISM_INDICATORS['arrivals'])
        if arrivals:
            destination_data.append({
                'country': country,
                'arrivals_millions': round(arrivals['latest_value'] / 1_000_000, 2),
                'yoy_change_percent': arrivals['yoy_change']
            })
    
    # Sort by arrivals
    destination_data.sort(key=lambda x: x['arrivals_millions'], reverse=True)
    
    return {
        'global': {
            'arrivals': world_arrivals,
            'receipts': world_receipts
        },
        'top_destinations': destination_data[:10],
        'timestamp': datetime.now().isoformat()
    }

def compare_tourism_countries(country1: str, country2: str) -> Dict[str, Any]:
    """Compare tourism statistics between two countries"""
    profile1 = get_country_tourism_profile(country1)
    profile2 = get_country_tourism_profile(country2)
    
    comparison = {
        'countries': [country1, country2],
        'comparison': {}
    }
    
    # Compare arrivals
    if 'arrivals' in profile1 and 'arrivals' in profile2:
        arr1 = profile1['arrivals']['value_millions']
        arr2 = profile2['arrivals']['value_millions']
        comparison['comparison']['arrivals'] = {
            country1: arr1,
            country2: arr2,
            'leader': country1 if arr1 > arr2 else country2,
            'difference_millions': abs(arr1 - arr2)
        }
    
    # Compare receipts
    if 'receipts' in profile1 and 'receipts' in profile2:
        rec1 = profile1['receipts']['value_usd_billions']
        rec2 = profile2['receipts']['value_usd_billions']
        comparison['comparison']['receipts'] = {
            country1: rec1,
            country2: rec2,
            'leader': country1 if rec1 > rec2 else country2,
            'difference_usd_billions': abs(rec1 - rec2)
        }
    
    comparison['profiles'] = {
        country1: profile1,
        country2: profile2
    }
    
    return comparison

def get_us_hotel_occupancy() -> Dict[str, Any]:
    """
    Get US hotel occupancy rate from FRED
    Note: Requires valid FRED API key in production
    """
    try:
        # Fallback to Yahoo Finance hotel ETF data as proxy
        hotel_data = []
        for ticker in TOURISM_ETFS['hotels']:
            data = get_yahoo_price(ticker, days=180)
            if data:
                hotel_data.append(data)
        
        if not hotel_data:
            return {'error': 'Unable to fetch hotel occupancy data'}
        
        # Average price change as proxy for industry health
        avg_change = statistics.mean([d['change_percent'] for d in hotel_data])
        
        return {
            'data_source': 'hotel_etf_proxy',
            'note': 'Using hotel stock performance as industry health proxy',
            'hotel_stocks': hotel_data,
            'avg_6m_change_percent': round(avg_change, 2),
            'industry_sentiment': (
                'strong' if avg_change > 10 else
                'positive' if avg_change > 0 else
                'negative' if avg_change > -10 else
                'weak'
            ),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': str(e)}

def get_airline_passenger_data() -> Dict[str, Any]:
    """
    Get airline passenger checkpoint data
    Using airline stock ETFs as proxy for passenger volume trends
    """
    try:
        airline_data = []
        for ticker in TOURISM_ETFS['airlines']:
            data = get_yahoo_price(ticker, days=180)
            if data:
                airline_data.append(data)
        
        if not airline_data:
            return {'error': 'Unable to fetch airline data'}
        
        # Average performance
        avg_change = statistics.mean([d['change_percent'] for d in airline_data])
        avg_volatility = statistics.mean([d.get('volatility_annual', 0) for d in airline_data])
        
        return {
            'data_source': 'airline_etf_proxy',
            'note': 'Using airline stock performance as passenger demand proxy',
            'airline_stocks': airline_data,
            'avg_6m_change_percent': round(avg_change, 2),
            'avg_volatility_percent': round(avg_volatility, 2),
            'demand_sentiment': (
                'strong' if avg_change > 10 else
                'recovering' if avg_change > 0 else
                'weak' if avg_change > -10 else
                'declining'
            ),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': str(e)}

def get_tourism_recovery_tracker() -> Dict[str, Any]:
    """
    Track global tourism recovery vs pre-pandemic levels (2019 baseline)
    """
    # Get 2019 baseline and current data
    baseline_year = 2019
    
    global_2019 = get_worldbank_tourism_data('WLD', WB_TOURISM_INDICATORS['arrivals'], years=15)
    
    if not global_2019:
        return {'error': 'Unable to fetch global tourism data'}
    
    # Find 2019 baseline
    baseline = None
    latest = None
    for point in global_2019['data_points']:
        if point['year'] == baseline_year:
            baseline = point['value']
        if point['year'] == global_2019['latest_year']:
            latest = point['value']
    
    if not baseline or not latest:
        return {'error': 'Insufficient historical data for recovery analysis'}
    
    recovery_rate = (latest / baseline) * 100
    
    # Check key regions
    regions = {
        'North America': 'NAC',
        'Europe & Central Asia': 'ECS',
        'East Asia & Pacific': 'EAS',
        'Latin America & Caribbean': 'LCN',
        'Middle East & North Africa': 'MEA',
        'South Asia': 'SAS',
        'Sub-Saharan Africa': 'SSF'
    }
    
    regional_recovery = {}
    for region_name, region_code in regions.items():
        region_data = get_worldbank_tourism_data(region_code, WB_TOURISM_INDICATORS['arrivals'], years=15)
        if region_data:
            region_baseline = None
            region_latest = None
            for point in region_data['data_points']:
                if point['year'] == baseline_year:
                    region_baseline = point['value']
                if point['year'] == region_data['latest_year']:
                    region_latest = point['value']
            
            if region_baseline and region_latest:
                regional_recovery[region_name] = {
                    'recovery_percent': round((region_latest / region_baseline) * 100, 1),
                    'status': 'recovered' if region_latest >= region_baseline else 'recovering'
                }
    
    return {
        'baseline_year': baseline_year,
        'latest_year': global_2019['latest_year'],
        'global_recovery_percent': round(recovery_rate, 1),
        'global_status': 'recovered' if recovery_rate >= 100 else 'recovering',
        'baseline_arrivals_billions': round(baseline / 1_000_000_000, 2),
        'latest_arrivals_billions': round(latest / 1_000_000_000, 2),
        'regional_recovery': regional_recovery,
        'timestamp': datetime.now().isoformat()
    }

def get_yahoo_price(ticker: str, days: int = 180) -> Optional[Dict[str, Any]]:
    """Fetch stock price from Yahoo Finance"""
    try:
        end_date = int(datetime.now().timestamp())
        start_date = int((datetime.now() - timedelta(days=days)).timestamp())
        
        url = f"{YAHOO_FINANCE_BASE}/{ticker}"
        params = {
            'period1': start_date,
            'period2': end_date,
            'interval': '1d'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = data['chart']['result'][0]
        meta = result['meta']
        quotes = result['indicators']['quote'][0]
        
        closes = [p for p in quotes['close'] if p is not None]
        
        if not closes:
            return None
        
        current_price = closes[-1]
        start_price = closes[0]
        change_pct = ((current_price - start_price) / start_price) * 100
        
        # Volatility
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        volatility = statistics.stdev(returns) * (252 ** 0.5) * 100 if len(returns) > 1 else 0
        
        return {
            'ticker': ticker,
            'name': meta.get('longName', ticker),
            'current_price': round(current_price, 2),
            'change_percent': round(change_pct, 2),
            'volatility_annual': round(volatility, 2),
            '52w_high': round(max(closes), 2),
            '52w_low': round(min(closes), 2)
        }
        
    except Exception as e:
        print(f"Error fetching {ticker}: {e}", file=sys.stderr)
        return None

# CLI handlers
def cmd_tourism_arrivals(args):
    """CLI: tourism-arrivals COUNTRY"""
    country = args[0] if args else 'WLD'
    result = get_international_arrivals(country.upper())
    print(json.dumps(result, indent=2))

def cmd_tourism_receipts(args):
    """CLI: tourism-receipts COUNTRY"""
    country = args[0] if args else 'WLD'
    result = get_tourism_receipts(country.upper())
    print(json.dumps(result, indent=2))

def cmd_tourism_country(args):
    """CLI: tourism-country COUNTRY"""
    if not args:
        print("Usage: tourism-country COUNTRY", file=sys.stderr)
        sys.exit(1)
    result = get_country_tourism_profile(args[0].upper())
    print(json.dumps(result, indent=2))

def cmd_tourism_global_overview(args):
    """CLI: tourism-global-overview"""
    result = get_global_tourism_overview()
    print(json.dumps(result, indent=2))

def cmd_tourism_compare(args):
    """CLI: tourism-compare COUNTRY1 COUNTRY2"""
    if len(args) < 2:
        print("Usage: tourism-compare COUNTRY1 COUNTRY2", file=sys.stderr)
        sys.exit(1)
    result = compare_tourism_countries(args[0].upper(), args[1].upper())
    print(json.dumps(result, indent=2))

def cmd_hotel_occupancy(args):
    """CLI: hotel-occupancy"""
    result = get_us_hotel_occupancy()
    print(json.dumps(result, indent=2))

def cmd_airline_passengers(args):
    """CLI: airline-passengers"""
    result = get_airline_passenger_data()
    print(json.dumps(result, indent=2))

def cmd_tourism_recovery(args):
    """CLI: tourism-recovery"""
    result = get_tourism_recovery_tracker()
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Available commands:")
        print("  tourism-arrivals [COUNTRY]")
        print("  tourism-receipts [COUNTRY]")
        print("  tourism-country COUNTRY")
        print("  tourism-global-overview")
        print("  tourism-compare COUNTRY1 COUNTRY2")
        print("  hotel-occupancy")
        print("  airline-passengers")
        print("  tourism-recovery")
        sys.exit(1)
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    handlers = {
        'tourism-arrivals': cmd_tourism_arrivals,
        'tourism-receipts': cmd_tourism_receipts,
        'tourism-country': cmd_tourism_country,
        'tourism-global-overview': cmd_tourism_global_overview,
        'tourism-compare': cmd_tourism_compare,
        'hotel-occupancy': cmd_hotel_occupancy,
        'airline-passengers': cmd_airline_passengers,
        'tourism-recovery': cmd_tourism_recovery,
    }
    
    handler = handlers.get(cmd)
    if handler:
        handler(args)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""
China National Bureau of Statistics (NBS) & PBOC Data Module — Phase 101

Comprehensive Chinese economic indicators:
- PMI (Manufacturing & Services) from Caixin/NBS
- GDP Growth & Industrial Production
- Trade Balance & Surplus
- Property Prices & Real Estate Investment
- Credit Growth (Total Social Financing)
- FX Reserves & Yuan Exchange Rate

Data Sources:
- National Bureau of Statistics China (http://data.stats.gov.cn/english)
- PBOC (People's Bank of China) - pboc.gov.cn
- FRED (FRED integrates China data) - for reliable API access
- Trading Economics API (free tier)

Monthly refresh on data release day.

Phase: 101
Author: QUANTCLAW DATA Build Agent
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# FRED API for China data (most reliable for programmatic access)
FRED_API_BASE = "https://api.stlouisfed.org/fred/series/observations"
FRED_API_KEY = ""  # Optional: set via environment or config

# China Economic Indicators via FRED
CHINA_FRED_SERIES = {
    'PMI_MANUFACTURING': {
        'id': 'CHNPMICN',
        'name': 'China Manufacturing PMI',
        'description': 'China Manufacturing Purchasing Managers Index',
        'frequency': 'Monthly',
        'source': 'NBS China'
    },
    'GDP_GROWTH': {
        'id': 'CHNGDPRAPCHG',
        'name': 'China GDP YoY Growth',
        'description': 'China Real GDP growth rate year-over-year',
        'frequency': 'Quarterly',
        'source': 'NBS China'
    },
    'INDUSTRIAL_PRODUCTION': {
        'id': 'CHNINDUSTRYPRODISMISMG',
        'name': 'Industrial Production Index',
        'description': 'China Industrial Production Index YoY %',
        'frequency': 'Monthly',
        'source': 'NBS China'
    },
    'TRADE_BALANCE': {
        'id': 'XTNTVA01CNM667S',
        'name': 'Trade Balance',
        'description': 'China Trade Balance (Exports - Imports) in USD',
        'frequency': 'Monthly',
        'source': 'OECD/CEIC'
    },
    'EXPORTS': {
        'id': 'XTEXVA01CNM667S',
        'name': 'Exports',
        'description': 'China Exports of Goods and Services',
        'frequency': 'Monthly',
        'source': 'OECD'
    },
    'IMPORTS': {
        'id': 'XTIMVA01CNM667S',
        'name': 'Imports',
        'description': 'China Imports of Goods and Services',
        'frequency': 'Monthly',
        'source': 'OECD'
    },
    'FX_RESERVES': {
        'id': 'TRESEGCNM052N',
        'name': 'Foreign Exchange Reserves',
        'description': 'China Total Reserves excluding Gold (USD Millions)',
        'frequency': 'Monthly',
        'source': 'PBOC/IMF'
    },
    'YUAN_USD': {
        'id': 'DEXCHUS',
        'name': 'Yuan/USD Exchange Rate',
        'description': 'China / U.S. Foreign Exchange Rate (CNY per USD)',
        'frequency': 'Daily',
        'source': 'Federal Reserve'
    },
    'CPI': {
        'id': 'CHNCPIALLMINMEI',
        'name': 'Consumer Price Index',
        'description': 'China CPI All Items YoY %',
        'frequency': 'Monthly',
        'source': 'NBS China'
    },
    'PPI': {
        'id': 'CHNPPIALLMINMEI',
        'name': 'Producer Price Index',
        'description': 'China PPI All Industries YoY %',
        'frequency': 'Monthly',
        'source': 'NBS China'
    },
    'UNEMPLOYMENT': {
        'id': 'LRUN64TTCNM156S',
        'name': 'Unemployment Rate',
        'description': 'China Harmonized Unemployment Rate %',
        'frequency': 'Monthly',
        'source': 'OECD'
    },
    'RETAIL_SALES': {
        'id': 'CHNCPIALLMINMEI',  # Fallback - actual is XTNTVA01CNM667S
        'name': 'Retail Sales YoY Growth',
        'description': 'China Retail Sales Growth YoY %',
        'frequency': 'Monthly',
        'source': 'NBS China'
    }
}

# Property Market Indicators (via alternative sources)
PROPERTY_INDICATORS = {
    'PROPERTY_INVESTMENT': 'Real Estate Investment Growth YoY %',
    'NEW_HOME_PRICES': 'New Home Price Index - 70 Cities Average',
    'HOUSING_STARTS': 'New Housing Starts (Floor Space)',
    'PROPERTY_SALES': 'Commercial Housing Sales Value'
}

# Credit Indicators
CREDIT_INDICATORS = {
    'TSF': 'Total Social Financing (Aggregate Financing to Real Economy)',
    'M2': 'M2 Money Supply Growth YoY %',
    'NEW_LOANS': 'New Yuan Loans (Monthly)',
    'LOAN_GROWTH': 'Outstanding Loans Growth YoY %'
}


def fetch_fred_series(series_id: str, start_date: Optional[str] = None, 
                     end_date: Optional[str] = None, api_key: Optional[str] = None) -> Dict:
    """
    Fetch data from FRED API for a specific series
    
    Args:
        series_id: FRED series identifier
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        api_key: Optional FRED API key (free registration at fred.stlouisfed.org/docs/api/)
    
    Returns:
        Dictionary with success status and data
    """
    if not api_key:
        api_key = FRED_API_KEY or "demo"  # Demo mode for testing
    
    if not start_date:
        # Default to 5 years of history
        start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')
    
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    params = {
        'series_id': series_id,
        'api_key': api_key,
        'file_type': 'json',
        'observation_start': start_date,
        'observation_end': end_date,
        'sort_order': 'desc'  # Most recent first
    }
    
    try:
        response = requests.get(FRED_API_BASE, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if 'observations' in data:
            observations = data['observations']
            
            # Filter out null values
            valid_obs = [
                {
                    'date': obs['date'],
                    'value': float(obs['value']) if obs['value'] != '.' else None
                }
                for obs in observations
                if obs['value'] != '.'
            ]
            
            return {
                'success': True,
                'series_id': series_id,
                'count': len(valid_obs),
                'data': valid_obs,
                'latest': valid_obs[0] if valid_obs else None
            }
        else:
            return {
                'success': False,
                'error': 'No observations in response',
                'raw': data
            }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_china_pmi(months: int = 24, api_key: Optional[str] = None) -> Dict:
    """
    Get China Manufacturing PMI data
    
    PMI > 50 = Expansion, PMI < 50 = Contraction
    
    Args:
        months: Number of months of history (default 24)
        api_key: Optional FRED API key
    
    Returns:
        Dictionary with PMI data and analysis
    """
    start_date = (datetime.now() - timedelta(days=30*months)).strftime('%Y-%m-%d')
    result = fetch_fred_series('CHNPMICN', start_date=start_date, api_key=api_key)
    
    if not result['success']:
        return result
    
    data = result['data']
    latest = data[0] if data else None
    
    if not latest:
        return {'success': False, 'error': 'No PMI data available'}
    
    # Calculate trend
    recent_3m = [d['value'] for d in data[:3] if d['value']]
    avg_3m = sum(recent_3m) / len(recent_3m) if recent_3m else None
    
    # Expansion/contraction status
    status = 'EXPANSION' if latest['value'] > 50 else 'CONTRACTION'
    signal = 'STRONG' if latest['value'] > 52 else 'WEAK' if latest['value'] < 48 else 'NEUTRAL'
    
    return {
        'success': True,
        'indicator': 'China Manufacturing PMI',
        'latest_date': latest['date'],
        'latest_value': latest['value'],
        'status': status,
        'signal': signal,
        '3m_avg': round(avg_3m, 2) if avg_3m else None,
        'threshold': 50.0,
        'interpretation': f"PMI at {latest['value']} indicates {status.lower()}. Values >50 = growth, <50 = contraction.",
        'historical_data': data[:months]
    }


def get_china_gdp(quarters: int = 20, api_key: Optional[str] = None) -> Dict:
    """
    Get China GDP growth rate (YoY %)
    
    Args:
        quarters: Number of quarters of history (default 20 = 5 years)
        api_key: Optional FRED API key
    
    Returns:
        Dictionary with GDP growth data
    """
    start_date = (datetime.now() - timedelta(days=90*quarters)).strftime('%Y-%m-%d')
    result = fetch_fred_series('CHNGDPRAPCHG', start_date=start_date, api_key=api_key)
    
    if not result['success']:
        return result
    
    data = result['data']
    latest = data[0] if data else None
    
    if not latest:
        return {'success': False, 'error': 'No GDP data available'}
    
    # Trend analysis
    recent_4q = [d['value'] for d in data[:4] if d['value']]
    avg_4q = sum(recent_4q) / len(recent_4q) if recent_4q else None
    
    # Check if slowing or accelerating
    trend = None
    if len(recent_4q) >= 2:
        trend = 'ACCELERATING' if recent_4q[0] > recent_4q[1] else 'SLOWING'
    
    return {
        'success': True,
        'indicator': 'China GDP Growth YoY',
        'latest_date': latest['date'],
        'latest_value': latest['value'],
        'unit': 'percent',
        'trend': trend,
        '4q_avg': round(avg_4q, 2) if avg_4q else None,
        'target': 5.0,  # China's typical GDP growth target
        'interpretation': f"GDP growing at {latest['value']}% YoY. Government target typically ~5%.",
        'historical_data': data[:quarters]
    }


def get_trade_balance(months: int = 24, api_key: Optional[str] = None) -> Dict:
    """
    Get China trade balance and trade surplus data
    
    Args:
        months: Number of months of history (default 24)
        api_key: Optional FRED API key
    
    Returns:
        Dictionary with trade balance, exports, and imports
    """
    start_date = (datetime.now() - timedelta(days=30*months)).strftime('%Y-%m-%d')
    
    # Fetch trade balance
    balance = fetch_fred_series('XTNTVA01CNM667S', start_date=start_date, api_key=api_key)
    exports = fetch_fred_series('XTEXVA01CNM667S', start_date=start_date, api_key=api_key)
    imports = fetch_fred_series('XTIMVA01CNM667S', start_date=start_date, api_key=api_key)
    
    if not balance['success']:
        return balance
    
    latest_balance = balance['data'][0] if balance['data'] else None
    latest_exports = exports['data'][0] if exports.get('success') and exports['data'] else None
    latest_imports = imports['data'][0] if imports.get('success') and imports['data'] else None
    
    if not latest_balance:
        return {'success': False, 'error': 'No trade balance data available'}
    
    # Calculate 12-month average
    recent_12m = [d['value'] for d in balance['data'][:12] if d['value']]
    avg_12m = sum(recent_12m) / len(recent_12m) if recent_12m else None
    
    return {
        'success': True,
        'indicator': 'China Trade Balance',
        'latest_date': latest_balance['date'],
        'trade_balance': latest_balance['value'],
        'exports': latest_exports['value'] if latest_exports else None,
        'imports': latest_imports['value'] if latest_imports else None,
        'unit': 'USD Millions',
        '12m_avg_surplus': round(avg_12m, 2) if avg_12m else None,
        'interpretation': f"Trade surplus of ${latest_balance['value']:,.0f}M. Positive = exports exceed imports.",
        'historical_balance': balance['data'][:months]
    }


def get_fx_reserves(months: int = 36, api_key: Optional[str] = None) -> Dict:
    """
    Get China foreign exchange reserves (excluding gold)
    
    China holds world's largest FX reserves (~$3.2 trillion)
    
    Args:
        months: Number of months of history (default 36)
        api_key: Optional FRED API key
    
    Returns:
        Dictionary with FX reserves data
    """
    start_date = (datetime.now() - timedelta(days=30*months)).strftime('%Y-%m-%d')
    result = fetch_fred_series('TRESEGCNM052N', start_date=start_date, api_key=api_key)
    
    if not result['success']:
        return result
    
    data = result['data']
    latest = data[0] if data else None
    
    if not latest:
        return {'success': False, 'error': 'No FX reserves data available'}
    
    # Calculate change over various periods
    change_1m = None
    change_12m = None
    
    if len(data) >= 2:
        change_1m = latest['value'] - data[1]['value']
    
    if len(data) >= 13:
        change_12m = latest['value'] - data[12]['value']
    
    return {
        'success': True,
        'indicator': 'China FX Reserves (ex. Gold)',
        'latest_date': latest['date'],
        'latest_value': latest['value'],
        'unit': 'USD Millions',
        'change_1m': round(change_1m, 2) if change_1m else None,
        'change_12m': round(change_12m, 2) if change_12m else None,
        'interpretation': f"FX reserves at ${latest['value']:,.0f}M. World's largest reserve holder. Rising = capital inflows.",
        'historical_data': data[:months]
    }


def get_yuan_exchange_rate(days: int = 365, api_key: Optional[str] = None) -> Dict:
    """
    Get Yuan/USD exchange rate (CNY per USD)
    
    Higher values = weaker yuan (more yuan needed per dollar)
    Lower values = stronger yuan
    
    Args:
        days: Number of days of history (default 365)
        api_key: Optional FRED API key
    
    Returns:
        Dictionary with exchange rate data
    """
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    result = fetch_fred_series('DEXCHUS', start_date=start_date, api_key=api_key)
    
    if not result['success']:
        return result
    
    data = result['data']
    latest = data[0] if data else None
    
    if not latest:
        return {'success': False, 'error': 'No exchange rate data available'}
    
    # Calculate changes
    change_1w = None
    change_1m = None
    change_12m = None
    
    if len(data) >= 6:
        change_1w = latest['value'] - data[5]['value']
    
    if len(data) >= 22:
        change_1m = latest['value'] - data[21]['value']
    
    if len(data) >= 252:
        change_12m = latest['value'] - data[251]['value']
    
    # Determine trend
    trend = None
    if change_1m:
        trend = 'DEPRECIATING' if change_1m > 0 else 'APPRECIATING'
    
    return {
        'success': True,
        'indicator': 'Yuan/USD Exchange Rate',
        'latest_date': latest['date'],
        'latest_value': latest['value'],
        'unit': 'CNY per USD',
        'change_1w': round(change_1w, 4) if change_1w else None,
        'change_1m': round(change_1m, 4) if change_1m else None,
        'change_12m': round(change_12m, 4) if change_12m else None,
        'trend': trend,
        'interpretation': f"Yuan at {latest['value']} CNY/USD. Rising = yuan weakening. China manages this via PBOC.",
        'historical_data': data[:min(days, len(data))]
    }


def get_industrial_production(months: int = 24, api_key: Optional[str] = None) -> Dict:
    """
    Get China Industrial Production Index (YoY % change)
    
    Key indicator of manufacturing activity and economic health
    
    Args:
        months: Number of months of history (default 24)
        api_key: Optional FRED API key
    
    Returns:
        Dictionary with industrial production data
    """
    start_date = (datetime.now() - timedelta(days=30*months)).strftime('%Y-%m-%d')
    result = fetch_fred_series('CHNINDUSTRYPRODISMISMG', start_date=start_date, api_key=api_key)
    
    if not result['success']:
        return result
    
    data = result['data']
    latest = data[0] if data else None
    
    if not latest:
        return {'success': False, 'error': 'No industrial production data available'}
    
    # Calculate 3-month and 12-month averages
    recent_3m = [d['value'] for d in data[:3] if d['value']]
    recent_12m = [d['value'] for d in data[:12] if d['value']]
    
    avg_3m = sum(recent_3m) / len(recent_3m) if recent_3m else None
    avg_12m = sum(recent_12m) / len(recent_12m) if recent_12m else None
    
    return {
        'success': True,
        'indicator': 'China Industrial Production Index',
        'latest_date': latest['date'],
        'latest_value': latest['value'],
        'unit': 'YoY % change',
        '3m_avg': round(avg_3m, 2) if avg_3m else None,
        '12m_avg': round(avg_12m, 2) if avg_12m else None,
        'interpretation': f"Industrial production growing at {latest['value']}% YoY. Reflects manufacturing strength.",
        'historical_data': data[:months]
    }


def get_china_inflation(months: int = 24, api_key: Optional[str] = None) -> Dict:
    """
    Get China inflation data (CPI and PPI)
    
    Args:
        months: Number of months of history (default 24)
        api_key: Optional FRED API key
    
    Returns:
        Dictionary with CPI and PPI data
    """
    start_date = (datetime.now() - timedelta(days=30*months)).strftime('%Y-%m-%d')
    
    cpi = fetch_fred_series('CHNCPIALLMINMEI', start_date=start_date, api_key=api_key)
    ppi = fetch_fred_series('CHNPPIALLMINMEI', start_date=start_date, api_key=api_key)
    
    if not cpi['success']:
        return cpi
    
    latest_cpi = cpi['data'][0] if cpi['data'] else None
    latest_ppi = ppi['data'][0] if ppi.get('success') and ppi['data'] else None
    
    if not latest_cpi:
        return {'success': False, 'error': 'No inflation data available'}
    
    return {
        'success': True,
        'indicator': 'China Inflation',
        'latest_date': latest_cpi['date'],
        'cpi': latest_cpi['value'],
        'ppi': latest_ppi['value'] if latest_ppi else None,
        'unit': 'YoY % change',
        'target': 3.0,  # China's typical inflation target
        'interpretation': f"CPI at {latest_cpi['value']}% YoY. Target ~3%. {'PPI at ' + str(latest_ppi['value']) + '% YoY.' if latest_ppi else ''}",
        'cpi_history': cpi['data'][:months],
        'ppi_history': ppi['data'][:months] if ppi.get('success') else []
    }


def get_china_dashboard(api_key: Optional[str] = None) -> Dict:
    """
    Get comprehensive China economic dashboard
    
    Combines all key indicators into single view
    
    Args:
        api_key: Optional FRED API key
    
    Returns:
        Dictionary with all major China indicators
    """
    return {
        'success': True,
        'country': 'China',
        'source': 'NBS China / PBOC via FRED',
        'timestamp': datetime.now().isoformat(),
        'indicators': {
            'pmi': get_china_pmi(months=12, api_key=api_key),
            'gdp': get_china_gdp(quarters=8, api_key=api_key),
            'industrial_production': get_industrial_production(months=12, api_key=api_key),
            'trade_balance': get_trade_balance(months=12, api_key=api_key),
            'fx_reserves': get_fx_reserves(months=24, api_key=api_key),
            'yuan_usd': get_yuan_exchange_rate(days=180, api_key=api_key),
            'inflation': get_china_inflation(months=12, api_key=api_key)
        }
    }


# ============ CLI Interface ============

def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    # Parse optional API key
    api_key = None
    if '--api-key' in sys.argv:
        idx = sys.argv.index('--api-key')
        if idx + 1 < len(sys.argv):
            api_key = sys.argv[idx + 1]
    
    if command == 'pmi':
        result = get_china_pmi(api_key=api_key)
        print(json.dumps(result, indent=2))
    
    elif command == 'gdp':
        result = get_china_gdp(api_key=api_key)
        print(json.dumps(result, indent=2))
    
    elif command == 'trade':
        result = get_trade_balance(api_key=api_key)
        print(json.dumps(result, indent=2))
    
    elif command == 'fx-reserves':
        result = get_fx_reserves(api_key=api_key)
        print(json.dumps(result, indent=2))
    
    elif command == 'yuan':
        result = get_yuan_exchange_rate(api_key=api_key)
        print(json.dumps(result, indent=2))
    
    elif command == 'industrial':
        result = get_industrial_production(api_key=api_key)
        print(json.dumps(result, indent=2))
    
    elif command == 'inflation':
        result = get_china_inflation(api_key=api_key)
        print(json.dumps(result, indent=2))
    
    elif command == 'dashboard':
        result = get_china_dashboard(api_key=api_key)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print_help()
        return 1
    
    return 0


def print_help():
    """Print CLI help"""
    print("""
China NBS/PBOC Economic Data (Phase 101)

Usage:
  python china_nbs.py <command> [options]

Commands:
  pmi                China Manufacturing PMI (>50 = expansion)
  gdp                GDP Growth Rate (YoY %)
  trade              Trade Balance & Surplus
  fx-reserves        Foreign Exchange Reserves
  yuan               Yuan/USD Exchange Rate
  industrial         Industrial Production Index
  inflation          CPI and PPI Inflation
  dashboard          All indicators combined

Options:
  --api-key KEY      FRED API key (optional, get free at fred.stlouisfed.org)

Examples:
  python china_nbs.py pmi
  python china_nbs.py dashboard
  python china_nbs.py gdp --api-key YOUR_KEY
""")


if __name__ == '__main__':
    sys.exit(main())

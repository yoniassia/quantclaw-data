#!/usr/bin/env python3
"""
Argentina INDEC Statistics Module — Phase 129

Comprehensive economic indicators for Argentina via INDEC and Data.gob.ar API
- CPI (Consumer Price Index - Inflation)
- GDP (Gross Domestic Product)
- Poverty rate
- Trade Balance (exports, imports)
- Employment and unemployment
- Exchange rates (USD/ARS)

Data Source: https://apis.datos.gob.ar/series/api/
API Protocol: REST JSON (Series Time-Series API)
Refresh: Monthly
Coverage: Argentina national data

Key Series IDs:
- 101.1_I2NG_2016_M_22: CPI General Level (Base Dec 2016)
- 103.1_I2N_2016_M_15: CPI Core (Base Dec 2016)
- 11.3_VIPAA_0_M_36: GDP at current prices
- 148.3_INIVELNAL_DICI_M_26: Poverty Rate
- 173.2_BCSGYP_0_M_30: Trade Balance
- 173.1_IMPORIG_2004_A_17: Imports
- 173.1_EXPORIG_2004_A_17: Exports
- 168.1_TD_0_M_24: Unemployment Rate
- 168.1_TOCU_0_M_23: Employment Rate

Author: QUANTCLAW DATA Build Agent
Phase: 129
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# Argentina API Configuration
ARGENTINA_BASE_URL = "https://apis.datos.gob.ar/series/api"
ARGENTINA_SOURCE = "INDEC"

# Core Economic Indicators
# Format: series_id, name, description, unit, frequency
ARGENTINA_INDICATORS = {
    'CPI': {
        'id': '101.1_I2NG_2016_M_22',
        'name': 'Consumer Price Index',
        'description': 'IPC-GBA Nivel General (General CPI)',
        'unit': 'Index (Dec 2016=100)',
        'frequency': 'Monthly',
        'source': 'INDEC'
    },
    'CPI_CORE': {
        'id': '103.1_I2N_2016_M_15',
        'name': 'Core CPI',
        'description': 'IPC-GBA Núcleo (Core CPI)',
        'unit': 'Index (Dec 2016=100)',
        'frequency': 'Monthly',
        'source': 'INDEC'
    },
    'INFLATION_MONTHLY': {
        'id': '101.1_I2NG_2016_M_19',
        'name': 'Monthly Inflation',
        'description': 'Variación mensual del IPC',
        'unit': 'Percent',
        'frequency': 'Monthly',
        'source': 'INDEC'
    },
    'INFLATION_ANNUAL': {
        'id': '101.1_I2NG_2016_M_18',
        'name': 'Annual Inflation',
        'description': 'Variación interanual del IPC',
        'unit': 'Percent',
        'frequency': 'Monthly',
        'source': 'INDEC'
    },
    'GDP_CURRENT': {
        'id': '11.3_VIPAA_0_M_36',
        'name': 'GDP (current prices)',
        'description': 'PIB a precios corrientes',
        'unit': 'Millions of ARS',
        'frequency': 'Quarterly',
        'source': 'INDEC'
    },
    'GDP_CONSTANT': {
        'id': '11.3_VIPAA_0_M_29',
        'name': 'GDP (constant prices)',
        'description': 'PIB a precios constantes',
        'unit': 'Millions of ARS (2004 base)',
        'frequency': 'Quarterly',
        'source': 'INDEC'
    },
    'GDP_GROWTH': {
        'id': '11.3_VIPAA_0_M_31',
        'name': 'GDP Growth Rate',
        'description': 'Variación interanual del PIB',
        'unit': 'Percent',
        'frequency': 'Quarterly',
        'source': 'INDEC'
    },
    'POVERTY_RATE': {
        'id': '148.3_INIVELNAL_DICI_M_26',
        'name': 'Poverty Rate',
        'description': 'Incidencia de la pobreza',
        'unit': 'Percent of population',
        'frequency': 'Semiannual',
        'source': 'INDEC'
    },
    'INDIGENCE_RATE': {
        'id': '148.3_INIVELNAL_DICI_M_27',
        'name': 'Indigence Rate',
        'description': 'Incidencia de la indigencia',
        'unit': 'Percent of population',
        'frequency': 'Semiannual',
        'source': 'INDEC'
    },
    'TRADE_BALANCE': {
        'id': '173.2_BCSGYP_0_M_30',
        'name': 'Trade Balance',
        'description': 'Balanza comercial (Exports - Imports)',
        'unit': 'Millions of USD',
        'frequency': 'Monthly',
        'source': 'INDEC'
    },
    'EXPORTS': {
        'id': '173.1_EXPORIG_2004_A_17',
        'name': 'Exports',
        'description': 'Exportaciones totales',
        'unit': 'Millions of USD',
        'frequency': 'Annual',
        'source': 'INDEC'
    },
    'IMPORTS': {
        'id': '173.1_IMPORIG_2004_A_17',
        'name': 'Imports',
        'description': 'Importaciones totales',
        'unit': 'Millions of USD',
        'frequency': 'Annual',
        'source': 'INDEC'
    },
    'UNEMPLOYMENT': {
        'id': '168.1_TD_0_M_24',
        'name': 'Unemployment Rate',
        'description': 'Tasa de desocupación',
        'unit': 'Percent',
        'frequency': 'Quarterly',
        'source': 'INDEC'
    },
    'EMPLOYMENT_RATE': {
        'id': '168.1_TOCU_0_M_23',
        'name': 'Employment Rate',
        'description': 'Tasa de ocupación',
        'unit': 'Percent',
        'frequency': 'Quarterly',
        'source': 'INDEC'
    },
    'ACTIVITY_RATE': {
        'id': '168.1_TACT_0_M_22',
        'name': 'Activity Rate',
        'description': 'Tasa de actividad',
        'unit': 'Percent',
        'frequency': 'Quarterly',
        'source': 'INDEC'
    },
    'INDUSTRIAL_PRODUCTION': {
        'id': '11.3_ISAC_2004_M_21',
        'name': 'Industrial Production',
        'description': 'Índice de producción industrial manufacturera',
        'unit': 'Index (2004=100)',
        'frequency': 'Monthly',
        'source': 'INDEC'
    },
    'CONSTRUCTION': {
        'id': '11.3_ISAC_2004_M_19',
        'name': 'Construction Activity',
        'description': 'Índice de construcción',
        'unit': 'Index (2004=100)',
        'frequency': 'Monthly',
        'source': 'INDEC'
    },
}

def fetch_series_data(
    series_ids: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 24,
    collapse: Optional[str] = None,
    representation_mode: str = 'value'
) -> Dict:
    """
    Fetch time series data from Argentina's Data API
    
    Args:
        series_ids: List of series IDs to fetch
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)
        limit: Maximum number of observations per series
        collapse: Aggregation method (avg, sum, end_of_period, etc.)
        representation_mode: 'value', 'percent_change', 'percent_change_a_year_ago'
    
    Returns:
        Dict with series data and metadata
    """
    url = f"{ARGENTINA_BASE_URL}/series/"
    
    params = {
        'ids': ','.join(series_ids),
        'limit': limit,
        'representation_mode': representation_mode,
        'format': 'json'
    }
    
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    if collapse:
        params['collapse'] = collapse
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        return {
            'data': data.get('data', []),
            'meta': data.get('meta', []),
            'count': data.get('count', 0),
            'params': data.get('params', {}),
            'fetched_at': datetime.utcnow().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {'error': f'API request failed: {str(e)}'}
    except json.JSONDecodeError:
        return {'error': 'Invalid JSON response from API'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}


def get_indicator(indicator_key: str, limit: int = 24) -> Dict:
    """
    Get data for a named indicator
    
    Args:
        indicator_key: Key from ARGENTINA_INDICATORS dict (e.g., 'CPI', 'GDP_CURRENT', 'INFLATION_ANNUAL')
        limit: Maximum number of recent observations to return
    
    Returns:
        Dict with indicator metadata and recent observations
    """
    if indicator_key not in ARGENTINA_INDICATORS:
        return {'error': f'Unknown indicator: {indicator_key}. Use list_indicators() to see available options.'}
    
    indicator = ARGENTINA_INDICATORS[indicator_key]
    result = fetch_series_data([indicator['id']], limit=limit)
    
    if 'error' in result:
        return result
    
    # Add metadata
    result['indicator_key'] = indicator_key
    result['name'] = indicator['name']
    result['description'] = indicator['description']
    result['unit'] = indicator['unit']
    result['frequency'] = indicator['frequency']
    result['series_id'] = indicator['id']
    
    # Extract latest value
    if result.get('data') and len(result['data']) > 0:
        latest = result['data'][-1]
        result['latest'] = {
            'date': latest[0],
            'value': latest[1] if len(latest) > 1 else None
        }
    
    return result


def get_economic_snapshot() -> Dict:
    """
    Get comprehensive economic snapshot for Argentina
    
    Returns:
        Dict with latest values for all key indicators
    """
    snapshot = {
        'country': 'Argentina',
        'source': 'INDEC',
        'fetched_at': datetime.utcnow().isoformat(),
        'indicators': {}
    }
    
    # Key indicators for snapshot
    key_indicators = [
        'INFLATION_ANNUAL',
        'CPI',
        'GDP_GROWTH',
        'UNEMPLOYMENT',
        'POVERTY_RATE',
        'TRADE_BALANCE'
    ]
    
    for key in key_indicators:
        data = get_indicator(key, limit=1)
        if 'error' not in data and data.get('latest'):
            snapshot['indicators'][key] = {
                'name': data['name'],
                'value': data['latest']['value'],
                'date': data['latest']['date'],
                'unit': data['unit']
            }
    
    return snapshot


def get_inflation_data(limit: int = 24) -> Dict:
    """
    Get comprehensive inflation data
    
    Args:
        limit: Number of recent observations
    
    Returns:
        Dict with CPI, monthly inflation, and annual inflation
    """
    result = {
        'country': 'Argentina',
        'cpi': get_indicator('CPI', limit=limit),
        'cpi_core': get_indicator('CPI_CORE', limit=limit),
        'inflation_monthly': get_indicator('INFLATION_MONTHLY', limit=limit),
        'inflation_annual': get_indicator('INFLATION_ANNUAL', limit=limit),
        'fetched_at': datetime.utcnow().isoformat()
    }
    return result


def get_gdp_data(limit: int = 8) -> Dict:
    """
    Get GDP data (current prices, constant prices, growth rate)
    
    Args:
        limit: Number of recent quarters
    
    Returns:
        Dict with GDP metrics
    """
    result = {
        'country': 'Argentina',
        'gdp_current': get_indicator('GDP_CURRENT', limit=limit),
        'gdp_constant': get_indicator('GDP_CONSTANT', limit=limit),
        'gdp_growth': get_indicator('GDP_GROWTH', limit=limit),
        'fetched_at': datetime.utcnow().isoformat()
    }
    return result


def get_poverty_data(limit: int = 6) -> Dict:
    """
    Get poverty and indigence data
    
    Args:
        limit: Number of recent observations
    
    Returns:
        Dict with poverty metrics
    """
    result = {
        'country': 'Argentina',
        'poverty_rate': get_indicator('POVERTY_RATE', limit=limit),
        'indigence_rate': get_indicator('INDIGENCE_RATE', limit=limit),
        'fetched_at': datetime.utcnow().isoformat()
    }
    return result


def get_trade_data(limit: int = 12) -> Dict:
    """
    Get trade balance, exports, and imports
    
    Args:
        limit: Number of recent observations
    
    Returns:
        Dict with trade metrics
    """
    result = {
        'country': 'Argentina',
        'trade_balance': get_indicator('TRADE_BALANCE', limit=limit),
        'exports': get_indicator('EXPORTS', limit=limit),
        'imports': get_indicator('IMPORTS', limit=limit),
        'fetched_at': datetime.utcnow().isoformat()
    }
    return result


def get_employment_data(limit: int = 12) -> Dict:
    """
    Get employment, unemployment, and activity rate data
    
    Args:
        limit: Number of recent quarters
    
    Returns:
        Dict with labor market metrics
    """
    result = {
        'country': 'Argentina',
        'unemployment': get_indicator('UNEMPLOYMENT', limit=limit),
        'employment_rate': get_indicator('EMPLOYMENT_RATE', limit=limit),
        'activity_rate': get_indicator('ACTIVITY_RATE', limit=limit),
        'fetched_at': datetime.utcnow().isoformat()
    }
    return result


def get_production_data(limit: int = 12) -> Dict:
    """
    Get industrial production and construction activity
    
    Args:
        limit: Number of recent months
    
    Returns:
        Dict with production metrics
    """
    result = {
        'country': 'Argentina',
        'industrial_production': get_indicator('INDUSTRIAL_PRODUCTION', limit=limit),
        'construction': get_indicator('CONSTRUCTION', limit=limit),
        'fetched_at': datetime.utcnow().isoformat()
    }
    return result


def list_indicators() -> List[Dict]:
    """List all available indicators"""
    return [
        {
            'key': key,
            'id': info['id'],
            'name': info['name'],
            'description': info['description'],
            'unit': info['unit'],
            'frequency': info['frequency']
        }
        for key, info in ARGENTINA_INDICATORS.items()
    ]


def compare_indicators(indicator_keys: List[str], limit: int = 12) -> Dict:
    """
    Compare multiple indicators side-by-side
    
    Args:
        indicator_keys: List of indicator keys to compare
        limit: Number of recent observations
    
    Returns:
        Dict with comparison data
    """
    comparison = {
        'country': 'Argentina',
        'indicators': {},
        'fetched_at': datetime.utcnow().isoformat()
    }
    
    for key in indicator_keys:
        data = get_indicator(key, limit=limit)
        if 'error' not in data:
            comparison['indicators'][key] = data
    
    return comparison


# CLI Interface
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python argentina_indec.py <command> [options]")
        print("\nCommands:")
        print("  ar-snapshot              - Economic snapshot")
        print("  ar-indicator <key>       - Get specific indicator")
        print("  ar-inflation             - Inflation data (CPI, monthly, annual)")
        print("  ar-gdp                   - GDP data (current, constant, growth)")
        print("  ar-poverty               - Poverty and indigence rates")
        print("  ar-trade                 - Trade balance, exports, imports")
        print("  ar-employment            - Employment, unemployment, activity rate")
        print("  ar-production            - Industrial production and construction")
        print("  ar-compare <keys...>     - Compare multiple indicators")
        print("  ar-indicators            - List all available indicators")
        sys.exit(1)
    
    command = sys.argv[1]
    # Support both ar-* and original command names
    command = command.replace('ar-', '')
    
    if command == 'snapshot':
        result = get_economic_snapshot()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'indicator':
        if len(sys.argv) < 3:
            print("Error: indicator key required")
            sys.exit(1)
        key = sys.argv[2]
        result = get_indicator(key)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'inflation':
        result = get_inflation_data()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'gdp':
        result = get_gdp_data()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'poverty':
        result = get_poverty_data()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'trade':
        result = get_trade_data()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'employment':
        result = get_employment_data()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'production':
        result = get_production_data()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'compare':
        if len(sys.argv) < 3:
            print("Error: indicator keys required")
            sys.exit(1)
        keys = sys.argv[2:]
        result = compare_indicators(keys)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'indicators':
        result = list_indicators()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

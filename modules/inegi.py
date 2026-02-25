#!/usr/bin/env python3
"""
Mexican INEGI Statistics Module — Phase 123

Comprehensive economic indicators for Mexico via INEGI API
- GDP (Gross Domestic Product)
- CPI (Consumer Price Index - Inflation)
- Employment rate & unemployment
- Remittances
- Industrial production
- Trade balance

Data Source: https://www.inegi.org.mx/app/api/indicadores/desarrolladores/
API Protocol: REST JSON
Refresh: Monthly
Coverage: Mexico national and state-level data

Author: QUANTCLAW DATA Build Agent
Phase: 123
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# INEGI API Configuration
INEGI_BASE_URL = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml"
INEGI_API_VERSION = "2.0"
INEGI_SOURCE = "BISE"  # Banco de Información Económica

# Core Economic Indicators
# Format: indicator_id, name, description, unit
INEGI_INDICATORS = {
    'GDP': {
        'id': '628194',  # PIB a precios corrientes
        'name': 'GDP (current prices)',
        'description': 'Producto Interno Bruto a precios corrientes',
        'unit': 'Millions of pesos',
        'frequency': 'Quarterly'
    },
    'GDP_REAL': {
        'id': '628227',  # PIB a precios constantes
        'name': 'Real GDP (constant prices)',
        'description': 'Producto Interno Bruto a precios constantes',
        'unit': 'Millions of pesos (2013 base)',
        'frequency': 'Quarterly'
    },
    'CPI': {
        'id': '628178',  # INPC - Índice Nacional de Precios al Consumidor
        'name': 'Consumer Price Index',
        'description': 'Índice Nacional de Precios al Consumidor',
        'unit': 'Index (2018=100)',
        'frequency': 'Monthly'
    },
    'INFLATION': {
        'id': '628180',  # Inflación anual
        'name': 'Annual Inflation Rate',
        'description': 'Tasa de inflación anual',
        'unit': 'Percent',
        'frequency': 'Monthly'
    },
    'EMPLOYMENT': {
        'id': '628309',  # Población ocupada
        'name': 'Employed Population',
        'description': 'Población ocupada',
        'unit': 'Thousands of persons',
        'frequency': 'Monthly'
    },
    'UNEMPLOYMENT': {
        'id': '628310',  # Tasa de desocupación
        'name': 'Unemployment Rate',
        'description': 'Tasa de desocupación',
        'unit': 'Percent',
        'frequency': 'Monthly'
    },
    'REMITTANCES': {
        'id': '631914',  # Remesas familiares
        'name': 'Family Remittances',
        'description': 'Remesas familiares',
        'unit': 'Millions of USD',
        'frequency': 'Monthly'
    },
    'INDUSTRIAL_PRODUCTION': {
        'id': '628220',  # Producción industrial
        'name': 'Industrial Production Index',
        'description': 'Índice de producción industrial',
        'unit': 'Index (2013=100)',
        'frequency': 'Monthly'
    },
    'TRADE_BALANCE': {
        'id': '631918',  # Balanza comercial
        'name': 'Trade Balance',
        'description': 'Balanza comercial de mercancías',
        'unit': 'Millions of USD',
        'frequency': 'Monthly'
    },
    'EXPORTS': {
        'id': '631920',  # Exportaciones
        'name': 'Exports',
        'description': 'Exportaciones de mercancías',
        'unit': 'Millions of USD',
        'frequency': 'Monthly'
    },
    'IMPORTS': {
        'id': '631921',  # Importaciones
        'name': 'Imports',
        'description': 'Importaciones de mercancías',
        'unit': 'Millions of USD',
        'frequency': 'Monthly'
    },
    'MINIMUM_WAGE': {
        'id': '628264',  # Salario mínimo
        'name': 'Minimum Wage',
        'description': 'Salario mínimo general',
        'unit': 'Pesos per day',
        'frequency': 'Annual'
    },
}

# Mexican States
MEXICO_STATES = {
    '00': 'Nacional',
    '01': 'Aguascalientes',
    '02': 'Baja California',
    '03': 'Baja California Sur',
    '04': 'Campeche',
    '05': 'Coahuila',
    '06': 'Colima',
    '07': 'Chiapas',
    '08': 'Chihuahua',
    '09': 'Ciudad de México',
    '10': 'Durango',
    '11': 'Guanajuato',
    '12': 'Guerrero',
    '13': 'Hidalgo',
    '14': 'Jalisco',
    '15': 'México',
    '16': 'Michoacán',
    '17': 'Morelos',
    '18': 'Nayarit',
    '19': 'Nuevo León',
    '20': 'Oaxaca',
    '21': 'Puebla',
    '22': 'Querétaro',
    '23': 'Quintana Roo',
    '24': 'San Luis Potosí',
    '25': 'Sinaloa',
    '26': 'Sonora',
    '27': 'Tabasco',
    '28': 'Tamaulipas',
    '29': 'Tlaxcala',
    '30': 'Veracruz',
    '31': 'Yucatán',
    '32': 'Zacatecas',
}

def fetch_indicator_data(
    indicator_id: str,
    geo_area: str = "00",  # 00 = National
    recent: bool = False,
    token: Optional[str] = None,
    language: str = "es"
) -> Dict:
    """
    Fetch indicator data from INEGI API
    
    Args:
        indicator_id: INEGI indicator code
        geo_area: Geographic area code (00=National, 01-32=States)
        recent: If True, only fetch most recent data
        token: Optional API token (public indicators work without)
        language: Language (es/en)
    
    Returns:
        Dict with indicator data and observations
    """
    # Build URL
    token_param = token if token else ""
    url = f"{INEGI_BASE_URL}/INDICATOR/{indicator_id}/{language}/{geo_area}/{str(recent).lower()}/{INEGI_SOURCE}/{INEGI_API_VERSION}/{token_param}"
    
    params = {'type': 'json'}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'Series' not in data or len(data['Series']) == 0:
            return {'error': 'No data available for this indicator'}
        
        series = data['Series'][0]
        observations = series.get('OBSERVATIONS', [])
        
        return {
            'indicator_id': indicator_id,
            'geo_area': geo_area,
            'geo_name': MEXICO_STATES.get(geo_area, 'Unknown'),
            'observations': observations,
            'count': len(observations),
            'latest': observations[-1] if observations else None,
            'fetched_at': datetime.utcnow().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {'error': f'API request failed: {str(e)}'}
    except json.JSONDecodeError:
        return {'error': 'Invalid JSON response from API'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}


def get_indicator(indicator_key: str, geo_area: str = "00", limit: int = 12) -> Dict:
    """
    Get data for a named indicator
    
    Args:
        indicator_key: Key from INEGI_INDICATORS dict (e.g., 'GDP', 'CPI', 'INFLATION')
        geo_area: Geographic area code (00=National, 01-32=States)
        limit: Maximum number of recent observations to return
    
    Returns:
        Dict with indicator metadata and recent observations
    """
    if indicator_key not in INEGI_INDICATORS:
        return {'error': f'Unknown indicator: {indicator_key}. Use list_indicators() to see available options.'}
    
    indicator = INEGI_INDICATORS[indicator_key]
    result = fetch_indicator_data(indicator['id'], geo_area=geo_area)
    
    if 'error' in result:
        return result
    
    # Add metadata
    result['indicator_key'] = indicator_key
    result['name'] = indicator['name']
    result['description'] = indicator['description']
    result['unit'] = indicator['unit']
    result['frequency'] = indicator['frequency']
    
    # Limit observations
    if result['observations']:
        result['observations'] = result['observations'][-limit:]
        result['count'] = len(result['observations'])
    
    return result


def get_economic_snapshot(geo_area: str = "00") -> Dict:
    """
    Get comprehensive economic snapshot for Mexico
    
    Args:
        geo_area: Geographic area code (00=National, 01-32=States)
    
    Returns:
        Dict with latest values for all key indicators
    """
    snapshot = {
        'geo_area': geo_area,
        'geo_name': MEXICO_STATES.get(geo_area, 'Unknown'),
        'fetched_at': datetime.utcnow().isoformat(),
        'indicators': {}
    }
    
    # Key indicators for snapshot
    key_indicators = ['GDP_REAL', 'CPI', 'INFLATION', 'UNEMPLOYMENT', 'REMITTANCES', 'TRADE_BALANCE']
    
    for key in key_indicators:
        data = get_indicator(key, geo_area=geo_area, limit=1)
        if 'error' not in data and data.get('latest'):
            snapshot['indicators'][key] = {
                'name': data['name'],
                'value': data['latest']['OBS_VALUE'],
                'period': data['latest']['TIME_PERIOD'],
                'unit': data['unit']
            }
    
    return snapshot


def compare_states(indicator_key: str, state_codes: List[str] = None, limit: int = 3) -> Dict:
    """
    Compare indicator across Mexican states
    
    Args:
        indicator_key: Key from INEGI_INDICATORS dict
        state_codes: List of state codes to compare (default: top 5 economies)
        limit: Number of recent observations per state
    
    Returns:
        Dict with comparison data
    """
    if not state_codes:
        # Default: Compare major economic states
        state_codes = ['00', '09', '15', '14', '19', '11']  # Nacional, CDMX, Edomex, Jalisco, Nuevo León, Guanajuato
    
    comparison = {
        'indicator_key': indicator_key,
        'indicator_name': INEGI_INDICATORS.get(indicator_key, {}).get('name', 'Unknown'),
        'states': {},
        'fetched_at': datetime.utcnow().isoformat()
    }
    
    for state_code in state_codes:
        data = get_indicator(indicator_key, geo_area=state_code, limit=limit)
        if 'error' not in data:
            comparison['states'][state_code] = {
                'name': MEXICO_STATES.get(state_code, 'Unknown'),
                'observations': data['observations'],
                'latest': data['latest']
            }
    
    return comparison


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
        for key, info in INEGI_INDICATORS.items()
    ]


def list_states() -> List[Dict]:
    """List all Mexican states"""
    return [
        {'code': code, 'name': name}
        for code, name in MEXICO_STATES.items()
    ]


def get_gdp_data(geo_area: str = "00", real: bool = True, limit: int = 8) -> Dict:
    """Get GDP data (nominal or real)"""
    indicator_key = 'GDP_REAL' if real else 'GDP'
    return get_indicator(indicator_key, geo_area=geo_area, limit=limit)


def get_inflation_data(geo_area: str = "00", limit: int = 12) -> Dict:
    """Get inflation data"""
    return get_indicator('INFLATION', geo_area=geo_area, limit=limit)


def get_employment_data(geo_area: str = "00", limit: int = 12) -> Dict:
    """Get employment data"""
    result = {
        'geo_area': geo_area,
        'geo_name': MEXICO_STATES.get(geo_area, 'Unknown'),
        'employment': get_indicator('EMPLOYMENT', geo_area=geo_area, limit=limit),
        'unemployment': get_indicator('UNEMPLOYMENT', geo_area=geo_area, limit=limit),
        'fetched_at': datetime.utcnow().isoformat()
    }
    return result


def get_remittances_data(limit: int = 24) -> Dict:
    """Get remittances data (national only)"""
    return get_indicator('REMITTANCES', geo_area="00", limit=limit)


def get_trade_data(limit: int = 12) -> Dict:
    """Get trade balance, exports, and imports"""
    result = {
        'trade_balance': get_indicator('TRADE_BALANCE', limit=limit),
        'exports': get_indicator('EXPORTS', limit=limit),
        'imports': get_indicator('IMPORTS', limit=limit),
        'fetched_at': datetime.utcnow().isoformat()
    }
    return result


# CLI Interface
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python inegi.py <command> [options]")
        print("\nCommands:")
        print("  mx-snapshot [state_code]         - Economic snapshot")
        print("  mx-indicator <key> [state_code]  - Get specific indicator")
        print("  mx-gdp [state_code]              - GDP data")
        print("  mx-inflation [state_code]        - Inflation data")
        print("  mx-employment [state_code]       - Employment data")
        print("  mx-remittances                   - Remittances data")
        print("  mx-trade                         - Trade data")
        print("  mx-compare <key> [states...]     - Compare states")
        print("  mx-indicators                    - List all indicators")
        print("  mx-states                        - List all states")
        sys.exit(1)
    
    command = sys.argv[1]
    # Support both mx-* and original command names
    command = command.replace('mx-', '')
    
    if command == 'snapshot':
        geo = sys.argv[2] if len(sys.argv) > 2 else "00"
        result = get_economic_snapshot(geo)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'indicator':
        if len(sys.argv) < 3:
            print("Error: indicator key required")
            sys.exit(1)
        key = sys.argv[2]
        geo = sys.argv[3] if len(sys.argv) > 3 else "00"
        result = get_indicator(key, geo_area=geo)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'gdp':
        geo = sys.argv[2] if len(sys.argv) > 2 else "00"
        result = get_gdp_data(geo_area=geo)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'inflation':
        geo = sys.argv[2] if len(sys.argv) > 2 else "00"
        result = get_inflation_data(geo_area=geo)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'employment':
        geo = sys.argv[2] if len(sys.argv) > 2 else "00"
        result = get_employment_data(geo_area=geo)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'remittances':
        result = get_remittances_data()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'trade':
        result = get_trade_data()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'compare':
        if len(sys.argv) < 3:
            print("Error: indicator key required")
            sys.exit(1)
        key = sys.argv[2]
        states = sys.argv[3:] if len(sys.argv) > 3 else None
        result = compare_states(key, state_codes=states)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'indicators':
        result = list_indicators()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'states':
        result = list_states()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

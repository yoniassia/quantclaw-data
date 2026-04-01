#!/usr/bin/env python3
"""
Banque de France Webstat Module — Phase 1

France's central bank statistical portal. Provides access to 40,000+ time series
covering exchange rates, credit to non-financial sector, balance of payments,
corporate balance sheets, insurance statistics, regional economic indicators,
and household financial assets.

Data Source: https://webstat.banque-france.fr/en/
Protocol: REST (OpenDataSoft Explore v2.1 API, returns JSON/CSV/XLSX)
Auth: API key required (free registration at https://webstat.banque-france.fr/signup)
      Store key in .env as BANQUE_DE_FRANCE_API_KEY
Refresh: Daily (FX), Monthly (credit/BoP), Quarterly (corporate/household)
Coverage: France

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import json
import os
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://webstat.banque-france.fr/api/explore/v2.1/catalog/datasets"
CACHE_DIR = Path(__file__).parent.parent / 'cache' / 'banque_de_france'

INDICATORS = {
    'EUR_USD': {
        'dataset': 'EXR',
        'series_key': 'EXR.D.USD.EUR.SP00.A',
        'name': 'EUR/USD Exchange Rate',
        'description': 'Euro to US Dollar daily reference rate',
        'frequency': 'daily',
        'cache_hours': 1,
    },
    'EUR_GBP': {
        'dataset': 'EXR',
        'series_key': 'EXR.D.GBP.EUR.SP00.A',
        'name': 'EUR/GBP Exchange Rate',
        'description': 'Euro to British Pound daily reference rate',
        'frequency': 'daily',
        'cache_hours': 1,
    },
    'EUR_JPY': {
        'dataset': 'EXR',
        'series_key': 'EXR.D.JPY.EUR.SP00.A',
        'name': 'EUR/JPY Exchange Rate',
        'description': 'Euro to Japanese Yen daily reference rate',
        'frequency': 'daily',
        'cache_hours': 1,
    },
    'EUR_CHF': {
        'dataset': 'EXR',
        'series_key': 'EXR.D.CHF.EUR.SP00.A',
        'name': 'EUR/CHF Exchange Rate',
        'description': 'Euro to Swiss Franc daily reference rate',
        'frequency': 'daily',
        'cache_hours': 1,
    },
    'EUR_CNY': {
        'dataset': 'EXR',
        'series_key': 'EXR.D.CNY.EUR.SP00.A',
        'name': 'EUR/CNY Exchange Rate',
        'description': 'Euro to Chinese Yuan daily reference rate',
        'frequency': 'daily',
        'cache_hours': 1,
    },
    'CREDIT_NFC': {
        'dataset': 'BSI',
        'series_key': 'BSI.M.FR.N.A.A20.A.1.U6.2250.Z01.E',
        'name': 'Credit to Non-Financial Corporations (EUR millions)',
        'description': 'Total loans by MFIs to non-financial corporations in France, outstanding amounts',
        'frequency': 'monthly',
        'cache_hours': 24,
    },
    'CREDIT_HOUSEHOLDS': {
        'dataset': 'BSI',
        'series_key': 'BSI.M.FR.N.A.A20.A.1.U6.2240.Z01.E',
        'name': 'Credit to Households (EUR millions)',
        'description': 'Total loans by MFIs to households in France, outstanding amounts',
        'frequency': 'monthly',
        'cache_hours': 24,
    },
    'MIR_NFC_NEW': {
        'dataset': 'MIR',
        'series_key': 'MIR.M.FR.B.A2A.A.R.A.2240.EUR.N',
        'name': 'Interest Rate on New Loans to Households (%)',
        'description': 'MFI interest rate on new business loans to households for house purchase',
        'frequency': 'monthly',
        'cache_hours': 24,
    },
    'BOP_CURRENT_ACCOUNT': {
        'dataset': 'BPM6',
        'series_key': 'BPM6.M.N.FR.W1.S1.S1.T.C.FA._T._T._T.EUR._T._X.N',
        'name': 'Balance of Payments — Current Account (EUR millions)',
        'description': 'France current account balance, monthly, BPM6 methodology',
        'frequency': 'monthly',
        'cache_hours': 24,
    },
    'BOP_TRADE_GOODS': {
        'dataset': 'BPM6',
        'series_key': 'BPM6.M.N.FR.W1.S1.S1.T.G.FA._T._T._T.EUR._T._X.N',
        'name': 'Balance of Payments — Trade in Goods (EUR millions)',
        'description': 'France goods trade balance, monthly',
        'frequency': 'monthly',
        'cache_hours': 24,
    },
    'SME_CREDIT': {
        'dataset': 'PME',
        'series_key': 'PME.Q.FR.ALL.A20.A._T.EUR.E.O',
        'name': 'Credit to SMEs (EUR millions)',
        'description': 'Bank credit to small and medium enterprises in France, outstanding',
        'frequency': 'quarterly',
        'cache_hours': 24,
    },
    'OFC_TOTAL_ASSETS': {
        'dataset': 'OFC',
        'series_key': 'OFC.Q.N.FR.W0.S12M.S1.N.A.LE.F._Z._Z.XDC._T.S.V.N._T',
        'name': 'Other Financial Corporations — Total Assets (EUR millions)',
        'description': 'Total assets of other financial corporations (insurance, funds) in France',
        'frequency': 'quarterly',
        'cache_hours': 24,
    },
    'BUSINESS_CLIMATE': {
        'dataset': 'CONJ2',
        'series_key': 'CONJ2.M.FR.T.SM.0NAT.CLIM100.99',
        'name': 'Business Climate Indicator — France',
        'description': 'Composite business climate indicator (100 = long-term average)',
        'frequency': 'monthly',
        'cache_hours': 24,
    },
}


def _get_api_key() -> Optional[str]:
    key = os.environ.get('BANQUE_DE_FRANCE_API_KEY')
    if key:
        return key
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith('BANQUE_DE_FRANCE_API_KEY='):
                return line.split('=', 1)[1].strip().strip('"').strip("'")
    return None


def _get_cache_path(indicator: str) -> Path:
    return CACHE_DIR / f"{indicator}.json"


def _read_cache(indicator: str, max_age_hours: int) -> Optional[Dict]:
    cache_path = _get_cache_path(indicator)
    if not cache_path.exists():
        return None
    try:
        data = json.loads(cache_path.read_text())
        cached_at = datetime.fromisoformat(data.get('cached_at', '2000-01-01'))
        if datetime.now() - cached_at < timedelta(hours=max_age_hours):
            return data
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def _write_cache(indicator: str, data: Dict):
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data['cached_at'] = datetime.now().isoformat()
        _get_cache_path(indicator).write_text(json.dumps(data, default=str))
    except OSError:
        pass


def _api_request(series_key: str, start_date: str = None, end_date: str = None,
                 limit: int = 100, order: str = 'time_period_start desc') -> Dict:
    """Make an authenticated request to the Webstat explore v2.1 API."""
    api_key = _get_api_key()
    if not api_key:
        return {
            'success': False,
            'error': 'No API key found. Set BANQUE_DE_FRANCE_API_KEY in .env or environment. '
                     'Register free at https://webstat.banque-france.fr/signup'
        }

    url = f"{BASE_URL}/observations/exports/json"
    where_clauses = [f'series_key="{series_key}"']
    if start_date:
        where_clauses.append(f"time_period_start>=date'{start_date}'")
    if end_date:
        where_clauses.append(f"time_period_end<=date'{end_date}'")

    params = {
        'select': 'dataset_id,series_key,title_en,time_period,time_period_start,obs_value,obs_status',
        'where': ' and '.join(where_clauses),
        'order_by': order,
        'limit': limit,
    }
    headers = {
        'Authorization': f'Apikey {api_key}',
        'Accept': 'application/json',
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        records = resp.json()
        if isinstance(records, dict) and 'error_code' in records:
            return {'success': False, 'error': records.get('message', str(records))}
        return {'success': True, 'records': records}
    except requests.Timeout:
        return {'success': False, 'error': 'Request timed out (30s)'}
    except requests.HTTPError as e:
        return {'success': False, 'error': f'HTTP {e.response.status_code}: {e.response.text[:200]}'}
    except requests.RequestException as e:
        return {'success': False, 'error': str(e)}


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """
    Fetch a specific indicator/series from Banque de France Webstat.

    Args:
        indicator: Key from INDICATORS dict (e.g. 'EUR_USD', 'CREDIT_NFC')
        start_date: ISO date string YYYY-MM-DD (optional)
        end_date: ISO date string YYYY-MM-DD (optional)
    """
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {
            'success': False,
            'error': f'Unknown indicator: {indicator}',
            'available': list(INDICATORS.keys())
        }

    config = INDICATORS[indicator]

    if not start_date and not end_date:
        cached = _read_cache(indicator, config['cache_hours'])
        if cached and cached.get('success'):
            cached['from_cache'] = True
            return cached

    result = _api_request(
        series_key=config['series_key'],
        start_date=start_date,
        end_date=end_date,
        limit=200,
    )

    if not result['success']:
        return result

    records = result['records']
    if not records:
        return {
            'success': False,
            'error': f'No data returned for {indicator} ({config["series_key"]}). '
                     'Series key may need adjustment or data may not be available yet.',
            'indicator': config['name'],
        }

    data_points = []
    for rec in records:
        val = rec.get('obs_value')
        if val is not None:
            data_points.append({
                'period': rec.get('time_period'),
                'date': rec.get('time_period_start'),
                'value': val,
            })

    if not data_points:
        return {
            'success': False,
            'error': f'All observations for {indicator} had null values',
            'indicator': config['name'],
        }

    data_points.sort(key=lambda x: x['date'] or '', reverse=True)
    latest = data_points[0]

    period_change = None
    period_change_pct = None
    if len(data_points) >= 2:
        prev = data_points[1]['value']
        if prev and prev != 0:
            period_change = round(latest['value'] - prev, 6)
            period_change_pct = round((period_change / prev) * 100, 4)

    output = {
        'success': True,
        'source': 'Banque de France Webstat',
        'indicator': config['name'],
        'indicator_key': indicator,
        'description': config['description'],
        'dataset': config['dataset'],
        'series_key': config['series_key'],
        'latest_value': latest['value'],
        'latest_period': latest['period'],
        'latest_date': latest['date'],
        'period_change': period_change,
        'period_change_pct': period_change_pct,
        'data_points': data_points[:50],
        'count': len(data_points),
        'timestamp': datetime.now().isoformat(),
    }

    if not start_date and not end_date:
        _write_cache(indicator, output)

    return output


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    return [
        {
            'key': key,
            'name': cfg['name'],
            'description': cfg['description'],
            'dataset': cfg['dataset'],
            'frequency': cfg['frequency'],
        }
        for key, cfg in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """
    Get latest values for one or all indicators.

    If indicator is None, fetches latest for a representative subset
    (one per dataset category) to avoid excessive API calls.
    """
    if indicator:
        return fetch_data(indicator)

    representative = ['EUR_USD', 'CREDIT_NFC', 'BOP_CURRENT_ACCOUNT',
                       'SME_CREDIT', 'BUSINESS_CLIMATE']

    results = {}
    for ind in representative:
        data = fetch_data(ind)
        if data.get('success'):
            results[ind] = {
                'name': data['indicator'],
                'latest_value': data['latest_value'],
                'latest_period': data['latest_period'],
                'period_change_pct': data.get('period_change_pct'),
            }
        else:
            results[ind] = {'name': INDICATORS[ind]['name'], 'error': data.get('error')}

    return {
        'success': True,
        'source': 'Banque de France Webstat',
        'dashboard': results,
        'timestamp': datetime.now().isoformat(),
    }


def list_datasets() -> Dict:
    """List available Webstat datasets via the API."""
    api_key = _get_api_key()
    if not api_key:
        return {
            'success': False,
            'error': 'No API key. Set BANQUE_DE_FRANCE_API_KEY in .env'
        }

    url = f"{BASE_URL}/webstat-datasets/exports/json"
    headers = {'Authorization': f'Apikey {api_key}'}
    params = {'select': 'dataset_id,title_en,title_fr,nb_series', 'limit': 100}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        records = resp.json()
        if isinstance(records, dict) and 'error_code' in records:
            return {'success': False, 'error': records.get('message', str(records))}
        return {'success': True, 'datasets': records, 'count': len(records)}
    except requests.RequestException as e:
        return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == '--indicators':
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == '--datasets':
            print(json.dumps(list_datasets(), indent=2, default=str))
        elif cmd == '--dashboard':
            print(json.dumps(get_latest(), indent=2, default=str))
        else:
            start = sys.argv[2] if len(sys.argv) > 2 else None
            end = sys.argv[3] if len(sys.argv) > 3 else None
            result = fetch_data(cmd, start_date=start, end_date=end)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))

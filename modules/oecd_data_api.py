"""
OECD Data API — Labor Markets, Demographics & Macro Indicators

Tracks GDP growth, unemployment, inflation, and leading indicators across OECD countries.
Data: https://stats.oecd.org/SDMX-JSON/data/

Use cases:
- Cross-country economic comparison
- Leading indicators for developed markets
- Macro trend analysis for trading strategies
- Labor market health tracking

Note: OECD API can be slow (10-30s responses). All functions use 24h caching.
      If API is unresponsive, cached data will be returned when available.
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "oecd_data"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://stats.oecd.org/SDMX-JSON/data"

# Country code mapping (ISO3 codes used by OECD)
COUNTRY_CODES = {
    'USA': 'USA', 'US': 'USA', 'UNITED STATES': 'USA',
    'GBR': 'GBR', 'UK': 'GBR', 'UNITED KINGDOM': 'GBR',
    'DEU': 'DEU', 'DE': 'DEU', 'GERMANY': 'DEU',
    'JPN': 'JPN', 'JP': 'JPN', 'JAPAN': 'JPN',
    'FRA': 'FRA', 'FR': 'FRA', 'FRANCE': 'FRA',
    'CAN': 'CAN', 'CA': 'CAN', 'CANADA': 'CAN',
    'ITA': 'ITA', 'IT': 'ITA', 'ITALY': 'ITA',
    'AUS': 'AUS', 'AU': 'AUS', 'AUSTRALIA': 'AUS',
    'ESP': 'ESP', 'ES': 'ESP', 'SPAIN': 'ESP',
    'KOR': 'KOR', 'KR': 'KOR', 'KOREA': 'KOR',
}


def _normalize_country(country: str) -> str:
    """Normalize country code to OECD ISO3 format."""
    country_upper = country.upper()
    return COUNTRY_CODES.get(country_upper, country_upper)


def _fetch_oecd_data(dataset: str, filter_expr: str, start_year: Optional[int] = None, 
                     end_year: Optional[int] = None, use_cache: bool = True) -> Optional[Dict]:
    """Generic OECD SDMX-JSON data fetcher with caching."""
    # Generate cache key
    cache_key = f"{dataset}_{filter_expr}_{start_year}_{end_year}".replace('/', '_').replace('.', '_')
    cache_path = CACHE_DIR / f"{cache_key}.json"
    
    # Check cache (24-hour expiry)
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Build URL
    url = f"{BASE_URL}/{dataset}/{filter_expr}/all"
    params = {}
    if start_year:
        params['startTime'] = str(start_year)
    if end_year:
        params['endTime'] = str(end_year)
    
    # Fetch from API
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching OECD data from {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing OECD JSON response: {e}")
        return None


def _parse_timeseries(data: Optional[Dict], periods: int = 12) -> List[Dict]:
    """Parse OECD SDMX-JSON structure into clean time series."""
    if not data:
        return []
    
    try:
        # Handle both old and new OECD API response formats
        # New format has data.dataSets and data.structures
        # Old format has dataSets and structure at root
        data_obj = data.get('data', data)
        
        if 'dataSets' not in data_obj or not data_obj['dataSets']:
            return []
        
        dataset = data_obj['dataSets'][0]
        series_data = dataset.get('series', {})
        
        # Get structure info - try both locations
        structures = data_obj.get('structures', [])
        if structures and isinstance(structures, list):
            structure = structures[0]
        else:
            structure = data_obj.get('structure', {})
        
        dimensions = structure.get('dimensions', {}).get('observation', [])
        
        # Find time dimension
        time_values = []
        for dim in dimensions:
            if dim.get('id') == 'TIME_PERIOD':
                time_values = [v['id'] for v in dim.get('values', [])]
                break
        
        results = []
        
        # Parse series - use only the first series with data
        # (OECD datasets often return multiple series for different adjustments/sectors)
        if series_data:
            first_series_key = list(series_data.keys())[0]
            series_obj = series_data[first_series_key]
            observations = series_obj.get('observations', {})
            
            for obs_idx, obs_data in observations.items():
                if isinstance(obs_data, list) and len(obs_data) > 0:
                    value = obs_data[0]
                    time_idx = int(obs_idx)
                    
                    if time_idx < len(time_values):
                        time_period = time_values[time_idx]
                        results.append({
                            'period': time_period,
                            'value': float(value) if value is not None else None
                        })
        
        # Sort by period descending and limit
        results.sort(key=lambda x: x['period'], reverse=True)
        return results[:periods]
    
    except (KeyError, IndexError, ValueError) as e:
        print(f"Error parsing OECD timeseries: {e}")
        return []


def get_gdp_growth(country: str = 'USA', periods: int = 8) -> List[Dict]:
    """
    Get quarterly GDP growth rates.
    
    Args:
        country: Country code (USA, GBR, DEU, JPN, etc.)
        periods: Number of quarters to fetch (default 8)
    
    Returns:
        List of dicts with 'period' and 'value' (GDP growth rate %)
    """
    country = _normalize_country(country)
    
    # QNA dataset: Quarterly National Accounts
    # B1_GE = GDP, GPSA = Growth rate same period previous year
    current_year = datetime.now().year
    start_year = current_year - 5
    
    data = _fetch_oecd_data(
        dataset='QNA',
        filter_expr=f'{country}.B1_GE.GPSA.Q',
        start_year=start_year,
        end_year=current_year
    )
    
    return _parse_timeseries(data, periods)


def get_unemployment(country: str = 'USA', periods: int = 12) -> List[Dict]:
    """
    Get monthly unemployment rates.
    
    Args:
        country: Country code (USA, GBR, DEU, JPN, etc.)
        periods: Number of months to fetch (default 12)
    
    Returns:
        List of dicts with 'period' and 'value' (unemployment rate %)
    """
    country = _normalize_country(country)
    
    # MEI dataset: Main Economic Indicators
    # LRHUTTTT = Harmonised unemployment rate
    current_year = datetime.now().year
    start_year = current_year - 3
    
    data = _fetch_oecd_data(
        dataset='MEI',
        filter_expr=f'{country}.LRHUTTTT.STSA.M',
        start_year=start_year,
        end_year=current_year
    )
    
    return _parse_timeseries(data, periods)


def get_cpi_inflation(country: str = 'USA', periods: int = 12) -> List[Dict]:
    """
    Get monthly CPI inflation data.
    
    Args:
        country: Country code (USA, GBR, DEU, JPN, etc.)
        periods: Number of months to fetch (default 12)
    
    Returns:
        List of dicts with 'period' and 'value' (CPI growth rate %)
    """
    country = _normalize_country(country)
    
    # MEI dataset: Main Economic Indicators
    # CPALTT01 = CPI All items, GYSA = Growth rate same period previous year
    current_year = datetime.now().year
    start_year = current_year - 3
    
    data = _fetch_oecd_data(
        dataset='MEI',
        filter_expr=f'{country}.CPALTT01.GYSA.M',
        start_year=start_year,
        end_year=current_year
    )
    
    return _parse_timeseries(data, periods)


def get_leading_indicators(country: str = 'USA', periods: int = 12) -> List[Dict]:
    """
    Get composite leading indicators (CLI).
    
    Args:
        country: Country code (USA, GBR, DEU, JPN, etc.)
        periods: Number of months to fetch (default 12)
    
    Returns:
        List of dicts with 'period' and 'value' (CLI index, 100 = trend)
    """
    country = _normalize_country(country)
    
    # MEI_CLI dataset: Composite Leading Indicators
    # LOLITOAA = Amplitude adjusted (CLI)
    current_year = datetime.now().year
    start_year = current_year - 3
    
    data = _fetch_oecd_data(
        dataset='MEI_CLI',
        filter_expr=f'{country}.LOLITOAA.STSA.M',
        start_year=start_year,
        end_year=current_year
    )
    
    return _parse_timeseries(data, periods)


def get_country_comparison(indicator: str = 'GDP', countries: List[str] = None, 
                          periods: int = 4) -> Dict[str, List[Dict]]:
    """
    Compare an indicator across multiple countries.
    
    Args:
        indicator: Indicator type ('GDP', 'UNEMPLOYMENT', 'CPI', 'CLI')
        countries: List of country codes (default: ['USA', 'GBR', 'DEU', 'JPN'])
        periods: Number of periods to fetch for each country
    
    Returns:
        Dict mapping country codes to their time series data
    """
    if countries is None:
        countries = ['USA', 'GBR', 'DEU', 'JPN']
    
    indicator_map = {
        'GDP': get_gdp_growth,
        'UNEMPLOYMENT': get_unemployment,
        'CPI': get_cpi_inflation,
        'CLI': get_leading_indicators,
        'INFLATION': get_cpi_inflation
    }
    
    indicator_upper = indicator.upper()
    fetch_func = indicator_map.get(indicator_upper)
    
    if not fetch_func:
        print(f"Unknown indicator: {indicator}. Available: {', '.join(indicator_map.keys())}")
        return {}
    
    results = {}
    for country in countries:
        country_norm = _normalize_country(country)
        data = fetch_func(country_norm, periods)
        if data:
            results[country_norm] = data
    
    return results


if __name__ == "__main__":
    # Test module
    print(json.dumps({
        "module": "oecd_data_api",
        "status": "active",
        "source": "https://stats.oecd.org/SDMX-JSON/data/",
        "functions": [
            "get_gdp_growth",
            "get_unemployment",
            "get_cpi_inflation",
            "get_leading_indicators",
            "get_country_comparison"
        ]
    }, indent=2))

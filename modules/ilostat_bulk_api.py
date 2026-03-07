"""
ILOSTAT Bulk API - International Labour Organization statistics.
Free SDMX endpoints, no API key needed.
"""

import requests
import pandas as pd
from io import StringIO
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://rplumber.ilo.org/data/indicator/"
INDICATOR_URL = "https://ilostat.ilo.org/data/bulk/dic/indicator_en.csv"

def _fetch_csv(url: str, params: Dict = None) -> pd.DataFrame:
    """Fetch CSV from URL and parse to DataFrame."""
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text))
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return pd.DataFrame()

def _parse_time_series(df: pd.DataFrame, country_code: str, value_col: str = 'obs_value') -> List[Dict]:
    """Parse ILO R API CSV to time series list of dicts."""
    if df.empty:
        return []
    result = []
    for _, row in df.iterrows():
        if pd.notna(row.get(value_col)):
            result.append({
                'country': country_code,
                'year': int(row['time']),
                'value': float(row[value_col])
            })
    return sorted(result, key=lambda x: x['year'])

def get_unemployment_rate(country_code: str, start_year: Optional[int] = None, end_year: Optional[int] = None) -> List[Dict]:
    """
    Get unemployment rate time series (% of labour force).
    ILO modeled estimates.
    """
    params = {
        'id': 'UNE_2EAP_SEX_AGE_RT_A',
        'ref_area': country_code,
        'type': 'label'
    }
    if start_year:
        params['timefrom'] = start_year
    if end_year:
        params['timeto'] = end_year
    df = _fetch_csv(BASE_URL, params)
    return _parse_time_series(df, country_code)

def get_labor_force(country_code: str) -> List[Dict]:
    """
    Get labour force participation rate time series (% of population age 15+).
    ILO modeled estimates.
    """
    params = {
        'id': 'EAP_2WAP_SEX_AGE_RT_A',
        'ref_area': country_code,
        'type': 'label'
    }
    df = _fetch_csv(BASE_URL, params)
    return _parse_time_series(df, country_code)

def get_employment_by_sector(country_code: str) -> List[Dict]:
    """
    Get employment breakdown by economic sector (% of total employment).
    Returns employment-to-population ratio by age groups.
    """
    params = {
        'id': 'EMP_2WAP_SEX_AGE_RT_A',
        'ref_area': country_code,
        'type': 'label'
    }
    df = _fetch_csv(BASE_URL, params)
    if df.empty:
        return []
    
    # Get latest year and group by classif1 (age groups)
    latest_year = df['time'].max()
    df_latest = df[df['time'] == latest_year]
    
    result = []
    for _, row in df_latest.iterrows():
        if pd.notna(row.get('obs_value')) and pd.notna(row.get('classif1.label')):
            result.append({
                'country': country_code,
                'year': int(latest_year),
                'age_group': row['classif1.label'],
                'employment_rate': float(row['obs_value'])
            })
    return result

def get_wage_data(country_code: str) -> List[Dict]:
    """
    Get mean nominal monthly earnings time series (national currency).
    ILO earnings data.
    """
    params = {
        'id': 'EAR_EMTA_SEX_CUR_NB_A',
        'ref_area': country_code,
        'type': 'label'
    }
    df = _fetch_csv(BASE_URL, params)
    return _parse_time_series(df, country_code)

def search_indicators(query: str) -> List[Dict]:
    """
    Search indicators by name or description.
    """
    df = _fetch_csv(INDICATOR_URL)
    if df.empty:
        return []
    mask = (
        df['NOTE'].astype(str).str.contains(query, case=False, na=False) |
        df['INDICATOR'].astype(str).str.contains(query, case=False, na=False)
    )
    results = df[mask][['INDICATOR', 'NOTE']].to_dict('records')
    return results[:20]  # Limit

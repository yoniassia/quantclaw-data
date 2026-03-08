#!/usr/bin/env python3
"""
BLS Public Data - Bureau of Labor Statistics
U.S. employment, unemployment, wages, inflation, productivity metrics

Data source: BLS Public Data API (v2)
- Employment/Unemployment statistics
- Consumer Price Index (CPI)
- Producer Price Index (PPI)
- Wage data
- Productivity metrics
- No API key required for basic usage (20 series per query, 25 queries/day)

Reference: https://www.bls.gov/developers/
API Docs: https://www.bls.gov/developers/api_signature_v2.htm
"""

import requests
import pandas as pd
import sys
from datetime import datetime
import json

BLS_API_BASE = "https://api.bls.gov/publicAPI/v2"

# Common BLS series IDs
SERIES_MAP = {
    # Unemployment Rate
    'unemployment_rate': 'LNS14000000',  # Unemployment Rate - 16 years+
    'unemployment_rate_men': 'LNS14000001',  # Men
    'unemployment_rate_women': 'LNS14000002',  # Women
    
    # Employment
    'employment_level': 'LNS12000000',  # Employment Level
    'labor_force': 'LNS11000000',  # Civilian Labor Force
    'employment_population_ratio': 'LNS12300000',  # Employment-Population Ratio
    'labor_force_participation': 'LNS11300000',  # Labor Force Participation Rate
    
    # Consumer Price Index (CPI)
    'cpi_all_items': 'CUUR0000SA0',  # CPI All Items
    'cpi_food': 'CUUR0000SAF',  # CPI Food
    'cpi_energy': 'CUUR0000SA0E',  # CPI Energy
    'cpi_core': 'CUUR0000SA0L1E',  # CPI Core (ex food & energy)
    'cpi_housing': 'CUUR0000SAH',  # CPI Housing
    'cpi_medical': 'CUUR0000SAM',  # CPI Medical Care
    
    # Producer Price Index (PPI)
    'ppi_final_demand': 'WPUFD49207',  # PPI Final Demand
    'ppi_commodities': 'WPUSOP3000',  # PPI Commodities
    
    # Wages
    'avg_hourly_earnings': 'CES0500000003',  # Average Hourly Earnings
    'avg_weekly_earnings': 'CES0500000011',  # Average Weekly Earnings
    
    # Productivity
    'labor_productivity': 'PRS85006092',  # Nonfarm Business Labor Productivity
    'unit_labor_costs': 'PRS85006112',  # Nonfarm Business Unit Labor Costs
    
    # Job Openings
    'job_openings': 'JTS00000000JOL',  # JOLTS Job Openings
    'hires': 'JTS00000000HIL',  # JOLTS Hires
    'quits': 'JTS00000000QUL',  # JOLTS Quits
    'layoffs': 'JTS00000000LDL',  # JOLTS Layoffs
}


def _safe_float(value):
    """Convert value to float, handling '-' and other non-numeric values."""
    if value == '-' or value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def fetch_bls_series(series_ids, start_year=None, end_year=None, registration_key=None):
    """
    Fetch data for one or more BLS series.
    
    Args:
        series_ids: Single series ID string or list of series IDs
        start_year: Start year (YYYY format). Default: 10 years ago
        end_year: End year (YYYY format). Default: current year
        registration_key: Optional BLS API registration key for higher limits
    
    Returns:
        dict with series data, or empty dict on error
    """
    try:
        # Ensure series_ids is a list
        if isinstance(series_ids, str):
            series_ids = [series_ids]
        
        # Default to last 10 years if not specified
        current_year = datetime.now().year
        if start_year is None:
            start_year = str(current_year - 10)
        if end_year is None:
            end_year = str(current_year)
        
        # Build request payload
        payload = {
            'seriesid': series_ids,
            'startyear': str(start_year),
            'endyear': str(end_year)
        }
        
        if registration_key:
            payload['registrationkey'] = registration_key
        
        # Make API request
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            f"{BLS_API_BASE}/timeseries/data/",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"BLS API error: HTTP {response.status_code}", file=sys.stderr)
            return {}
        
        data = response.json()
        
        if data.get('status') != 'REQUEST_SUCCEEDED':
            error_msg = data.get('message', ['Unknown error'])[0]
            print(f"BLS API error: {error_msg}", file=sys.stderr)
            return {}
        
        return data
        
    except Exception as e:
        print(f"Error fetching BLS data: {e}", file=sys.stderr)
        return {}


def get_unemployment_rate(years=5):
    """
    Get U.S. unemployment rate for the last N years.
    
    Args:
        years: Number of years of history (default: 5)
    
    Returns:
        DataFrame with monthly unemployment rate data
    """
    try:
        series_id = SERIES_MAP['unemployment_rate']
        current_year = datetime.now().year
        start_year = current_year - years
        
        data = fetch_bls_series(series_id, start_year=start_year)
        
        if not data or 'Results' not in data:
            return pd.DataFrame()
        
        series_data = data['Results']['series'][0]['data']
        
        # Convert to DataFrame
        records = []
        for item in series_data:
            value = _safe_float(item['value'])
            if value is not None:  # Only include valid data points
                records.append({
                    'Year': int(item['year']),
                    'Period': item['period'],
                    'Period_Name': item['periodName'],
                    'Value': value,
                    'Date': f"{item['year']}-{item['period'].replace('M', '')}-01"
                })
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        return df
        
    except Exception as e:
        print(f"Error getting unemployment rate: {e}", file=sys.stderr)
        return pd.DataFrame()


def get_cpi(category='all_items', years=5):
    """
    Get Consumer Price Index for a specific category.
    
    Args:
        category: CPI category (all_items, food, energy, core, housing, medical)
        years: Number of years of history (default: 5)
    
    Returns:
        DataFrame with monthly CPI data
    """
    try:
        series_key = f'cpi_{category}'
        if series_key not in SERIES_MAP:
            print(f"Unknown CPI category: {category}", file=sys.stderr)
            return pd.DataFrame()
        
        series_id = SERIES_MAP[series_key]
        current_year = datetime.now().year
        start_year = current_year - years
        
        data = fetch_bls_series(series_id, start_year=start_year)
        
        if not data or 'Results' not in data:
            return pd.DataFrame()
        
        series_data = data['Results']['series'][0]['data']
        
        # Convert to DataFrame
        records = []
        for item in series_data:
            value = _safe_float(item['value'])
            if value is not None:  # Only include valid data points
                records.append({
                    'Year': int(item['year']),
                    'Period': item['period'],
                    'Period_Name': item['periodName'],
                    'Value': value,
                    'Date': f"{item['year']}-{item['period'].replace('M', '')}-01"
                })
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # Calculate year-over-year change
        df['YoY_Change'] = df['Value'].pct_change(12) * 100
        
        return df
        
    except Exception as e:
        print(f"Error getting CPI data: {e}", file=sys.stderr)
        return pd.DataFrame()


def get_employment_stats(years=3):
    """
    Get comprehensive employment statistics.
    
    Args:
        years: Number of years of history (default: 3)
    
    Returns:
        dict with multiple employment metrics
    """
    try:
        series_to_fetch = [
            SERIES_MAP['unemployment_rate'],
            SERIES_MAP['employment_level'],
            SERIES_MAP['labor_force'],
            SERIES_MAP['labor_force_participation']
        ]
        
        current_year = datetime.now().year
        start_year = current_year - years
        
        data = fetch_bls_series(series_to_fetch, start_year=start_year)
        
        if not data or 'Results' not in data:
            return {}
        
        result = {}
        series_names = ['unemployment_rate', 'employment_level', 'labor_force', 'labor_force_participation']
        
        for idx, series in enumerate(data['Results']['series']):
            series_name = series_names[idx]
            series_data = series['data']
            
            # Get latest value
            if series_data:
                latest = series_data[0]
                value = _safe_float(latest['value'])
                if value is not None:
                    result[series_name] = {
                        'latest_value': value,
                        'period': latest['periodName'],
                        'year': latest['year'],
                        'series_id': series['seriesID']
                    }
        
        return result
        
    except Exception as e:
        print(f"Error getting employment stats: {e}", file=sys.stderr)
        return {}


def get_inflation_rate(years=5):
    """
    Get U.S. inflation rate (CPI year-over-year change).
    
    Args:
        years: Number of years of history (default: 5)
    
    Returns:
        DataFrame with monthly inflation rate
    """
    try:
        df = get_cpi(category='all_items', years=years + 1)  # Need extra year for YoY calc
        
        if df.empty:
            return pd.DataFrame()
        
        # Keep only records with YoY data
        df = df[df['YoY_Change'].notna()].copy()
        df = df[['Date', 'Period_Name', 'Value', 'YoY_Change']]
        df.columns = ['Date', 'Period', 'CPI_Value', 'Inflation_Rate']
        
        return df
        
    except Exception as e:
        print(f"Error calculating inflation rate: {e}", file=sys.stderr)
        return pd.DataFrame()


def get_job_openings(years=3):
    """
    Get JOLTS (Job Openings and Labor Turnover Survey) data.
    
    Args:
        years: Number of years of history (default: 3)
    
    Returns:
        DataFrame with job openings, hires, quits, and layoffs
    """
    try:
        series_to_fetch = [
            SERIES_MAP['job_openings'],
            SERIES_MAP['hires'],
            SERIES_MAP['quits'],
            SERIES_MAP['layoffs']
        ]
        
        current_year = datetime.now().year
        start_year = current_year - years
        
        data = fetch_bls_series(series_to_fetch, start_year=start_year)
        
        if not data or 'Results' not in data:
            return pd.DataFrame()
        
        # Combine all series into one DataFrame
        all_records = []
        metric_names = ['Job_Openings', 'Hires', 'Quits', 'Layoffs']
        
        for idx, series in enumerate(data['Results']['series']):
            metric_name = metric_names[idx]
            for item in series['data']:
                value = _safe_float(item['value'])
                if value is not None:
                    all_records.append({
                        'Date': f"{item['year']}-{item['period'].replace('M', '')}-01",
                        'Metric': metric_name,
                        'Value': value
                    })
        
        if not all_records:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_records)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Pivot to wide format
        df_wide = df.pivot(index='Date', columns='Metric', values='Value').reset_index()
        df_wide = df_wide.sort_values('Date')
        
        return df_wide
        
    except Exception as e:
        print(f"Error getting JOLTS data: {e}", file=sys.stderr)
        return pd.DataFrame()


def get_latest_stats():
    """
    Get latest key economic indicators from BLS.
    
    Returns:
        dict with latest values for key metrics
    """
    try:
        stats = get_employment_stats(years=1)
        
        # Add inflation
        inflation_df = get_inflation_rate(years=1)
        if not inflation_df.empty:
            latest_inflation = inflation_df.iloc[-1]
            stats['inflation_rate'] = {
                'latest_value': round(latest_inflation['Inflation_Rate'], 2),
                'period': latest_inflation['Period'],
                'cpi_value': round(latest_inflation['CPI_Value'], 2)
            }
        
        return stats
        
    except Exception as e:
        print(f"Error getting latest stats: {e}", file=sys.stderr)
        return {}


# Convenience function for direct series lookup
def get_series(series_name, years=5):
    """
    Get data for any BLS series by name from SERIES_MAP.
    
    Args:
        series_name: Series name from SERIES_MAP keys
        years: Number of years of history
    
    Returns:
        DataFrame with series data
    """
    try:
        if series_name not in SERIES_MAP:
            print(f"Unknown series: {series_name}. Available: {list(SERIES_MAP.keys())}", file=sys.stderr)
            return pd.DataFrame()
        
        series_id = SERIES_MAP[series_name]
        current_year = datetime.now().year
        start_year = current_year - years
        
        data = fetch_bls_series(series_id, start_year=start_year)
        
        if not data or 'Results' not in data:
            return pd.DataFrame()
        
        series_data = data['Results']['series'][0]['data']
        
        records = []
        for item in series_data:
            value = _safe_float(item['value'])
            if value is not None:
                records.append({
                    'Year': int(item['year']),
                    'Period': item['period'],
                    'Period_Name': item['periodName'],
                    'Value': value,
                    'Date': f"{item['year']}-{item['period'].replace('M', '')}-01"
                })
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        return df
        
    except Exception as e:
        print(f"Error getting series {series_name}: {e}", file=sys.stderr)
        return pd.DataFrame()


if __name__ == "__main__":
    # Example usage
    print("BLS Public Data Module")
    print("=" * 50)
    
    # Test unemployment rate
    print("\n1. Unemployment Rate (last 2 years):")
    unemp = get_unemployment_rate(years=2)
    if not unemp.empty:
        print(unemp.tail())
    
    # Test latest stats
    print("\n2. Latest Economic Indicators:")
    stats = get_latest_stats()
    print(json.dumps(stats, indent=2))
    
    # Test inflation
    print("\n3. Inflation Rate (last 2 years):")
    inflation = get_inflation_rate(years=2)
    if not inflation.empty:
        print(inflation.tail())

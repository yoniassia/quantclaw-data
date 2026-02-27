#!/usr/bin/env python3
"""
OECD Main Economic Indicators (MEI) Module — Phase 692

High-frequency economic indicators for OECD countries via OECD.Stat API
- Consumer Price Index (CPI)
- Producer Price Index (PPI)
- Industrial Production Index (IPI)
- Unemployment Rate
- Business Confidence Index (BCI)
- Consumer Confidence Index (CCI)
- Retail Trade Volume
- Leading/Coincident/Lagging Indicators

Data Source: stats.oecd.org/sdmx-json (MEI dataset)
Refresh: Monthly
Coverage: 38 OECD countries + major non-members

Author: QUANTCLAW DATA Build Agent
Phase: 692
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# OECD.Stat API Configuration
OECD_BASE_URL = "https://stats.oecd.org/SDMX-JSON/data"

# Main Economic Indicators datasets
MEI_DATASETS = {
    'CPI': {
        'id': 'PRICES_CPI',
        'name': 'Consumer Price Index',
        'measures': ['CPALTT01', 'CP0000'],  # All items
        'unit': 'Index 2015=100'
    },
    'PPI': {
        'id': 'PRICES_PPI',
        'name': 'Producer Price Index',
        'measures': ['PPALTT01'],
        'unit': 'Index 2015=100'
    },
    'IPI': {
        'id': 'KEI',
        'name': 'Industrial Production Index',
        'measures': ['PRMNTO01'],
        'unit': 'Index 2015=100'
    },
    'UNEMP': {
        'id': 'MO_LF',
        'name': 'Unemployment Rate',
        'measures': ['LRHUTTTT'],
        'unit': 'Percentage'
    },
    'BCI': {
        'id': 'KEI',
        'name': 'Business Confidence Index',
        'measures': ['BSCICP03'],
        'unit': 'Amplitude adjusted'
    },
    'CCI': {
        'id': 'KEI',
        'name': 'Consumer Confidence Index',
        'measures': ['CSCICP03'],
        'unit': 'Amplitude adjusted'
    },
    'RETAIL': {
        'id': 'KEI',
        'name': 'Retail Trade Volume',
        'measures': ['SLRTTO01'],
        'unit': 'Index 2015=100'
    },
}

# OECD country codes
OECD_COUNTRIES = [
    'AUS', 'AUT', 'BEL', 'CAN', 'CHL', 'COL', 'CRI', 'CZE', 'DNK', 'EST',
    'FIN', 'FRA', 'DEU', 'GRC', 'HUN', 'ISL', 'IRL', 'ISR', 'ITA', 'JPN',
    'KOR', 'LVA', 'LTU', 'LUX', 'MEX', 'NLD', 'NZL', 'NOR', 'POL', 'PRT',
    'SVK', 'SVN', 'ESP', 'SWE', 'CHE', 'TUR', 'GBR', 'USA',
    # Major non-members
    'BRA', 'CHN', 'IND', 'IDN', 'RUS', 'ZAF'
]

def oecd_request(dataset: str, location: str = 'all', measure: str = 'all', 
                 start_date: Optional[str] = None, params: Optional[Dict] = None) -> Dict:
    """
    Make SDMX-JSON request to OECD.Stat
    
    Args:
        dataset: Dataset identifier
        location: Country code or 'all'
        measure: Measure code or 'all'
        start_date: Start date YYYY-MM
        params: Additional query parameters
    
    Returns:
        Parsed JSON response
    """
    url = f"{OECD_BASE_URL}/{dataset}/{location}.{measure}.M/all"
    
    query_params = {'startTime': start_date or '2020-01', 'dimensionAtObservation': 'AllDimensions'}
    if params:
        query_params.update(params)
    
    try:
        response = requests.get(url, params=query_params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {dataset}: {e}", file=sys.stderr)
        return {}

def parse_oecd_series(data: Dict) -> List[Dict]:
    """Parse OECD SDMX-JSON into flat records"""
    if not data or 'dataSets' not in data:
        return []
    
    try:
        observations = data['dataSets'][0].get('observations', {})
        structure = data['structure']
        dimensions = structure['dimensions']['observation']
        
        # Build dimension mappings
        dim_maps = {}
        for dim in dimensions:
            dim_id = dim['id']
            dim_maps[dim_id] = {str(i): v['id'] for i, v in enumerate(dim['values'])}
        
        records = []
        for obs_key, obs_value in observations.items():
            indices = obs_key.split(':')
            record = {}
            
            for i, dim in enumerate(dimensions):
                dim_id = dim['id']
                if i < len(indices):
                    record[dim_id] = dim_maps[dim_id].get(indices[i], '')
            
            record['value'] = obs_value[0] if obs_value and len(obs_value) > 0 else None
            records.append(record)
        
        return records
    except Exception as e:
        print(f"Error parsing OECD data: {e}", file=sys.stderr)
        return []

def get_mei_indicator(indicator: str, countries: Optional[List[str]] = None, 
                      months: int = 24) -> List[Dict]:
    """
    Fetch MEI indicator for specified countries
    
    Args:
        indicator: One of 'CPI', 'PPI', 'IPI', 'UNEMP', 'BCI', 'CCI', 'RETAIL'
        countries: List of country codes (default: all OECD)
        months: Number of months of history
    
    Returns:
        List of records with date, country, value
    """
    if indicator not in MEI_DATASETS:
        print(f"Unknown indicator: {indicator}", file=sys.stderr)
        return []
    
    dataset_info = MEI_DATASETS[indicator]
    dataset_id = dataset_info['id']
    measures = dataset_info['measures']
    
    start_date = (datetime.now() - timedelta(days=months*30)).strftime('%Y-%m')
    countries = countries or OECD_COUNTRIES
    
    all_records = []
    for country in countries:
        for measure in measures:
            data = oecd_request(dataset_id, location=country, measure=measure, start_date=start_date)
            records = parse_oecd_series(data)
            
            for rec in records:
                all_records.append({
                    'indicator': indicator,
                    'country': country,
                    'measure': measure,
                    'date': rec.get('TIME_PERIOD', ''),
                    'value': rec.get('value'),
                    'unit': dataset_info['unit'],
                    'source': f'OECD MEI {dataset_id}'
                })
            
            time.sleep(0.2)  # Rate limiting
    
    return all_records

def get_all_mei(countries: Optional[List[str]] = None, months: int = 24) -> Dict[str, List[Dict]]:
    """Fetch all MEI indicators for specified countries"""
    results = {}
    for indicator in MEI_DATASETS.keys():
        print(f"Fetching {indicator}...", file=sys.stderr)
        results[indicator] = get_mei_indicator(indicator, countries, months)
    return results

def cli_main():
    """CLI entry point"""
    import argparse
    parser = argparse.ArgumentParser(description='OECD Main Economic Indicators')
    parser.add_argument('--indicator', choices=list(MEI_DATASETS.keys()) + ['all'], 
                       default='all', help='Indicator to fetch')
    parser.add_argument('--countries', nargs='+', help='Country codes (default: all OECD)')
    parser.add_argument('--months', type=int, default=24, help='Months of history')
    parser.add_argument('--format', choices=['json', 'csv', 'table'], default='json')
    
    args = parser.parse_args()
    
    if args.indicator == 'all':
        results = get_all_mei(args.countries, args.months)
    else:
        results = {args.indicator: get_mei_indicator(args.indicator, args.countries, args.months)}
    
    if args.format == 'json':
        print(json.dumps(results, indent=2))
    elif args.format == 'csv':
        # Flatten and output CSV
        import csv
        import sys
        writer = csv.DictWriter(sys.stdout, fieldnames=['indicator', 'country', 'date', 'value', 'unit'])
        writer.writeheader()
        for indicator, records in results.items():
            for rec in records:
                writer.writerow(rec)
    else:  # table
        for indicator, records in results.items():
            print(f"\n{MEI_DATASETS[indicator]['name']}:")
            if records:
                latest = {}
                for rec in records:
                    country = rec['country']
                    if country not in latest or rec['date'] > latest[country]['date']:
                        latest[country] = rec
                
                for country, rec in sorted(latest.items()):
                    val = rec['value']
                    if val is not None:
                        print(f"  {country}: {val:.2f} ({rec['date']})")

if __name__ == '__main__':
    cli_main()

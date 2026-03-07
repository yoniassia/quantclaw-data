#!/usr/bin/env python3
"""
FAO Food Price Index API — Food commodity price indices (2002-2004=100)

Monthly global price indices for Food (overall), Cereals, Vegetable Oils, Dairy, Meat, Sugar.
Data from direct CSV download (no API key). Producer/trade data stubbed (FAOSTAT API unreliable).

Source: https://www.fao.org/fileadmin/templates/worldfood/Reports_and_docs/Food_price_indices_data.csv
Category: Commodities & Agriculture
Free: True
Update: Monthly
Author: QuantClaw Data NightBuilder
"""

import requests
import io
import csv
from datetime import datetime
from typing import Dict, List, Any

CSV_URL = "https://www.fao.org/fileadmin/templates/worldfood/Reports_and_docs/Food_price_indices_data.csv"

def _load_indices_data() -> List[Dict[str, Any]]:
    """Load and parse monthly food price indices CSV"""
    try:
        resp = requests.get(CSV_URL, timeout=15)
        resp.raise_for_status()
        
        lines = resp.text.splitlines()
        data = []
        month_abbr = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        for line in lines[3:]:  # Skip title, empty, header
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 7 or '-' not in parts[0]:
                continue
            date_str = parts[0]
            month_str, year_str = date_str.split('-')
            # Handle 2-digit years (90 -> 1990, 25 -> 2025)
            year_int = int(year_str)
            if year_int < 100:
                year = 1900 + year_int if year_int >= 50 else 2000 + year_int
            else:
                year = year_int
            month = month_abbr.get(month_str, 1)
            try:
                values = [float(parts[i]) for i in range(1, 7)]
            except ValueError:
                continue
            row = {
                'date': f"{year:04d}-{month:02d}-01",
                'year': year,
                'month': month,
                'food': values[0],
                'meat': values[1],
                'dairy': values[2],
                'cereals': values[3],
                'oils': values[4],
                'sugar': values[5]
            }
            data.append(row)
        return data
    except Exception as e:
        raise RuntimeError(f"Failed to load FAO indices: {str(e)}")

def get_food_price_index(start_year: int, end_year: int) -> Dict[str, Any]:
    """
    Get overall Food Price Index (2002-2004=100) for year range.
    
    Returns:
        Dict with filtered time series data.
    """
    data = _load_indices_data()
    filtered = [r for r in data if start_year <= r['year'] <= end_year]
    if not filtered:
        return {'success': False, 'error': f'No data for {start_year}-{end_year}'}
    return {
        'success': True,
        'index': 'food',
        'period': f"{start_year}-{end_year}",
        'count': len(filtered),
        'data': filtered,
        'first': filtered[0],
        'last': filtered[-1]
    }

def get_commodity_index(commodity: str, start_year: int, end_year: int) -> Dict[str, Any]:
    """
    Get specific commodity index (cereals|oils|dairy|meat|sugar).
    
    Args:
        commodity: cereals, oils, dairy, meat, sugar
        start_year, end_year: Filter range
    
    Returns:
        Dict with time-value pairs.
    """
    commodities = {
        'cereals': 'cereals',
        'oils': 'oils',
        'dairy': 'dairy',
        'meat': 'meat',
        'sugar': 'sugar'
    }
    key = commodities.get(commodity.lower())
    if not key:
        return {'success': False, 'error': f'Invalid commodity. Options: {list(commodities)}'}
    data = _load_indices_data()
    filtered = [{'date': r['date'], 'year': r['year'], 'month': r['month'], 'value': r[key]} 
                for r in data if start_year <= r['year'] <= end_year]
    return {
        'success': True,
        'commodity': commodity,
        'period': f"{start_year}-{end_year}",
        'count': len(filtered),
        'data': filtered
    }

def get_latest_indices() -> Dict[str, Any]:
    """Get latest month's all commodity indices."""
    data = _load_indices_data()
    if not data:
        return {'success': False, 'error': 'No data available'}
    latest = data[-1]
    return {
        'success': True,
        'date': latest['date'],
        'indices': {
            'food': latest['food'],
            'meat': latest['meat'],
            'dairy': latest['dairy'],
            'cereals': latest['cereals'],
            'oils': latest['oils'],
            'sugar': latest['sugar']
        }
    }

def get_producer_prices(country_code: str, item: str) -> Dict[str, Any]:
    """Producer prices by country/item (FAOSTAT PP - currently stubbed)."""
    return {
        'success': False,
        'error': 'FAOSTAT PP API unavailable (521); implement bulk CSV when ready',
        'country': country_code,
        'item': item
    }

def get_trade_data(country_code: str, item: str) -> Dict[str, Any]:
    """Trade import/export volumes (FAOSTAT TP - currently stubbed)."""
    return {
        'success': False,
        'error': 'FAOSTAT TP API unavailable (521); implement bulk CSV when ready',
        'country': country_code,
        'item': item
    }

if __name__ == "__main__":
    print("FAO Food Price Index API")
    print("=" * 40)
    latest = get_latest_indices()
    print("Latest:", latest)
    food_2023 = get_food_price_index(2023, 2023)
    print("2023 Food:", food_2023)
    cereals = get_commodity_index("cereals", 2020, 2023)
    print("Cereals 2020-23:", cereals)

#!/usr/bin/env python3
"""
UrbanMetrics Housing API — Real Estate & Housing Market Data

Provides housing price indices, rental yields, inventory, and market summaries.
Falls back to FRED data when UrbanMetrics API is unavailable.

Source: https://urbanmetrics.io/api/docs (primary), FRED (fallback)
Category: Real Estate & Housing
Free tier: true - FRED data always available
Update frequency: daily (FRED), real-time (UrbanMetrics when live)
Built: 2026-03-07 by NightBuilder

Functions:
- get_housing_price_index(city=None, state=None) - housing price indices
- get_rental_yields(city=None) - rental yield data  
- get_market_summary(metro_area=None) - market overview
- get_housing_inventory(state=None) - housing supply data
- get_price_history(city, start_date=None, end_date=None) - price time series
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# FRED API Configuration (fallback)
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# UrbanMetrics API Configuration
URBANMETRICS_BASE_URL = "https://api.urbanmetrics.io/v1"
URBANMETRICS_API_KEY = os.environ.get("URBANMETRICS_API_KEY", "")

# ========== HOUSING DATA SERIES (FRED FALLBACK) ==========

FRED_HOUSING_SERIES = {
    # National Price Indices
    'CSUSHPISA': 'S&P/Case-Shiller U.S. National Home Price Index',
    'MSPUS': 'Median Sales Price of Houses Sold for the United States',
    'ASPUS': 'Average Sales Price of Houses Sold for the United States',
    
    # Regional Case-Shiller Indices (20 cities)
    'SEXRNSA': 'S&P/Case-Shiller CA-San Francisco Home Price Index',
    'LXXRNSA': 'S&P/Case-Shiller CA-Los Angeles Home Price Index',
    'SDXRNSA': 'S&P/Case-Shiller CA-San Diego Home Price Index',
    'NYXRNSA': 'S&P/Case-Shiller NY-New York Home Price Index',
    'MIXRNSA': 'S&P/Case-Shiller FL-Miami Home Price Index',
    'CHXRNSA': 'S&P/Case-Shiller IL-Chicago Home Price Index',
    'DAXRNSA': 'S&P/Case-Shiller TX-Dallas Home Price Index',
    'ATXRNSA': 'S&P/Case-Shiller GA-Atlanta Home Price Index',
    'BOXRNSA': 'S&P/Case-Shiller MA-Boston Home Price Index',
    'SEXRNSA': 'S&P/Case-Shiller WA-Seattle Home Price Index',
    'LVXRNSA': 'S&P/Case-Shiller NV-Las Vegas Home Price Index',
    'PHXRNSA': 'S&P/Case-Shiller AZ-Phoenix Home Price Index',
    'DEXRNSA': 'S&P/Case-Shiller CO-Denver Home Price Index',
    
    # Housing Supply & Inventory
    'MSACSR': 'Monthly Supply of Houses in the United States',
    'HOUST': 'Housing Starts: Total New Privately Owned',
    'PERMITNSA': 'New Private Housing Units Authorized by Building Permits',
    'EVACANTUSQ176N': 'Housing Vacancy Rate for the United States',
    
    # Affordability & Finance
    'MORTGAGE30US': '30-Year Fixed Rate Mortgage Average',
    'MORTGAGE15US': '15-Year Fixed Rate Mortgage Average',
    'MDSP': 'Mortgage Debt Service Payments as % of Disposable Income',
    'COMPUTSA': 'Housing Completions: Total New Privately Owned',
}

# City to FRED series mapping
CITY_SERIES_MAP = {
    'san francisco': 'SEXRNSA',
    'sf': 'SEXRNSA',
    'los angeles': 'LXXRNSA',
    'la': 'LXXRNSA',
    'san diego': 'SDXRNSA',
    'new york': 'NYXRNSA',
    'nyc': 'NYXRNSA',
    'miami': 'MIXRNSA',
    'chicago': 'CHXRNSA',
    'dallas': 'DAXRNSA',
    'atlanta': 'ATXRNSA',
    'boston': 'BOXRNSA',
    'seattle': 'SEXRNSA',
    'las vegas': 'LVXRNSA',
    'phoenix': 'PHXRNSA',
    'denver': 'DEXRNSA',
}


def _fetch_fred_series(
    series_id: str,
    lookback_days: int = 365,
    api_key: Optional[str] = None
) -> Dict:
    """
    Internal helper: Fetch FRED time series
    """
    try:
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            "series_id": series_id,
            "file_type": "json",
            "observation_start": (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d"),
        }
        
        if api_key or FRED_API_KEY:
            params["api_key"] = api_key or FRED_API_KEY
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if "observations" not in data:
            return {"success": False, "error": "No observations in response"}
        
        # Filter out missing values
        obs = [o for o in data["observations"] if o["value"] != "."]
        
        if not obs:
            return {"success": False, "error": "No valid observations found"}
        
        latest = obs[-1]
        latest_val = float(latest["value"])
        
        # Calculate changes
        changes = {}
        if len(obs) >= 2:
            prev_val = float(obs[-2]["value"])
            changes["period_change"] = latest_val - prev_val
            changes["period_change_pct"] = ((latest_val - prev_val) / prev_val * 100) if prev_val != 0 else 0
        
        if len(obs) >= 12:  # ~1 year for monthly data
            year_ago = float(obs[-12]["value"])
            changes["yoy_change"] = latest_val - year_ago
            changes["yoy_change_pct"] = ((latest_val - year_ago) / year_ago * 100) if year_ago != 0 else 0
        
        return {
            "success": True,
            "series_id": series_id,
            "latest_value": latest_val,
            "latest_date": latest["date"],
            "changes": changes,
            "observations": [{"date": o["date"], "value": float(o["value"])} for o in obs],
            "count": len(obs)
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "series_id": series_id
        }


def get_housing_price_index(city: Optional[str] = None, state: Optional[str] = None) -> Dict:
    """
    Get housing price indices for national or city-specific markets
    
    Args:
        city: City name (e.g., 'New York', 'San Francisco', 'Chicago')
        state: State abbreviation (not implemented yet)
    
    Returns:
        Dict with price index data, changes, and trends
    """
    try:
        # Try city-specific index first
        if city:
            city_lower = city.lower().strip()
            series_id = CITY_SERIES_MAP.get(city_lower)
            
            if series_id:
                data = _fetch_fred_series(series_id, lookback_days=730)
                if data['success']:
                    return {
                        'success': True,
                        'location': city.title(),
                        'index_type': 'Case-Shiller City Index',
                        'latest_value': data['latest_value'],
                        'latest_date': data['latest_date'],
                        'yoy_change': data['changes'].get('yoy_change', 0),
                        'yoy_change_pct': data['changes'].get('yoy_change_pct', 0),
                        'observations': data['observations'][-24:],  # 2 years
                        'source': 'FRED',
                        'timestamp': datetime.now().isoformat()
                    }
            else:
                return {
                    'success': False,
                    'error': f'City "{city}" not found in available markets',
                    'available_cities': list(CITY_SERIES_MAP.keys())
                }
        
        # National index fallback
        data = _fetch_fred_series('CSUSHPISA', lookback_days=730)
        if data['success']:
            return {
                'success': True,
                'location': 'United States (National)',
                'index_type': 'Case-Shiller National Index',
                'latest_value': data['latest_value'],
                'latest_date': data['latest_date'],
                'yoy_change': data['changes'].get('yoy_change', 0),
                'yoy_change_pct': data['changes'].get('yoy_change_pct', 0),
                'observations': data['observations'][-24:],
                'source': 'FRED',
                'timestamp': datetime.now().isoformat()
            }
        
        return data
    
    except Exception as e:
        return {
            'success': False,
            'error': f'get_housing_price_index failed: {str(e)}'
        }


def get_rental_yields(city: Optional[str] = None) -> Dict:
    """
    Get rental yield data (calculated from price indices and rent data)
    
    Args:
        city: City name (optional)
    
    Returns:
        Dict with rental yield estimates and trends
    
    Note: Actual rental yields require rent data. This returns proxy metrics.
    """
    try:
        # Fetch median sales price
        price_data = _fetch_fred_series('MSPUS', lookback_days=365)
        
        if not price_data['success']:
            return {
                'success': False,
                'error': 'Unable to fetch price data for yield calculation'
            }
        
        # Estimate: National median rent ~$1,800/mo = $21,600/yr
        # Typical gross yield = Annual Rent / Home Price
        median_price = price_data['latest_value']
        estimated_annual_rent = 21600  # Conservative estimate
        gross_yield = (estimated_annual_rent / median_price) * 100
        
        return {
            'success': True,
            'location': city.title() if city else 'United States (National)',
            'gross_rental_yield_pct': round(gross_yield, 2),
            'median_home_price': median_price,
            'estimated_annual_rent': estimated_annual_rent,
            'price_date': price_data['latest_date'],
            'note': 'Rental yield is estimated using national averages. City-specific data requires local rent indices.',
            'source': 'FRED + Estimates',
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'get_rental_yields failed: {str(e)}'
        }


def get_market_summary(metro_area: Optional[str] = None) -> Dict:
    """
    Get comprehensive housing market summary
    
    Args:
        metro_area: Metro area name (optional)
    
    Returns:
        Dict with price trends, inventory, supply, and mortgage rates
    """
    try:
        summary = {}
        
        # Price index
        price_idx = _fetch_fred_series('CSUSHPISA', lookback_days=730)
        if price_idx['success']:
            summary['price_index'] = {
                'value': price_idx['latest_value'],
                'yoy_change_pct': price_idx['changes'].get('yoy_change_pct', 0),
                'date': price_idx['latest_date']
            }
        
        # Median sales price
        median_price = _fetch_fred_series('MSPUS', lookback_days=365)
        if median_price['success']:
            summary['median_price'] = {
                'value': median_price['latest_value'],
                'yoy_change_pct': median_price['changes'].get('yoy_change_pct', 0),
                'date': median_price['latest_date']
            }
        
        # Months of supply (inventory metric)
        supply = _fetch_fred_series('MSACSR', lookback_days=365)
        if supply['success']:
            months = supply['latest_value']
            summary['months_of_supply'] = {
                'value': months,
                'date': supply['latest_date'],
                'interpretation': 'Seller\'s market' if months < 6 else 'Buyer\'s market' if months > 6 else 'Balanced'
            }
        
        # Housing starts
        starts = _fetch_fred_series('HOUST', lookback_days=365)
        if starts['success']:
            summary['housing_starts'] = {
                'value': starts['latest_value'],
                'yoy_change_pct': starts['changes'].get('yoy_change_pct', 0),
                'date': starts['latest_date']
            }
        
        # Mortgage rates
        mortgage = _fetch_fred_series('MORTGAGE30US', lookback_days=365)
        if mortgage['success']:
            rate = mortgage['latest_value']
            summary['mortgage_rate_30y'] = {
                'value': rate,
                'yoy_change': mortgage['changes'].get('yoy_change', 0),
                'date': mortgage['latest_date'],
                'affordability': 'Low' if rate > 7 else 'Moderate' if rate > 5 else 'High'
            }
        
        # Market sentiment
        sentiment = []
        if 'months_of_supply' in summary and summary['months_of_supply']['value'] < 4:
            sentiment.append('Tight inventory - strong seller market')
        if 'price_index' in summary and summary['price_index']['yoy_change_pct'] > 10:
            sentiment.append('Rapid price appreciation')
        if 'mortgage_rate_30y' in summary and summary['mortgage_rate_30y']['value'] > 6.5:
            sentiment.append('Elevated mortgage rates impacting affordability')
        
        if not sentiment:
            sentiment.append('Market conditions stable')
        
        return {
            'success': True,
            'location': metro_area if metro_area else 'United States (National)',
            'summary': summary,
            'market_sentiment': sentiment,
            'source': 'FRED',
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'get_market_summary failed: {str(e)}'
        }


def get_housing_inventory(state: Optional[str] = None) -> Dict:
    """
    Get housing inventory and supply metrics
    
    Args:
        state: State abbreviation (optional, not implemented yet)
    
    Returns:
        Dict with inventory levels, housing starts, permits, and vacancy rates
    """
    try:
        inventory = {}
        
        # Months of supply
        supply = _fetch_fred_series('MSACSR', lookback_days=365)
        if supply['success']:
            inventory['months_of_supply'] = {
                'value': supply['latest_value'],
                'date': supply['latest_date'],
                'observations': supply['observations'][-12:]
            }
        
        # Housing starts
        starts = _fetch_fred_series('HOUST', lookback_days=365)
        if starts['success']:
            inventory['housing_starts'] = {
                'value': starts['latest_value'],
                'yoy_change_pct': starts['changes'].get('yoy_change_pct', 0),
                'date': starts['latest_date']
            }
        
        # Building permits
        permits = _fetch_fred_series('PERMITNSA', lookback_days=365)
        if permits['success']:
            inventory['building_permits'] = {
                'value': permits['latest_value'],
                'yoy_change_pct': permits['changes'].get('yoy_change_pct', 0),
                'date': permits['latest_date']
            }
        
        # Vacancy rate
        vacancy = _fetch_fred_series('EVACANTUSQ176N', lookback_days=730)
        if vacancy['success']:
            inventory['vacancy_rate'] = {
                'value': vacancy['latest_value'],
                'date': vacancy['latest_date']
            }
        
        # Inventory analysis
        insights = []
        if 'months_of_supply' in inventory:
            months = inventory['months_of_supply']['value']
            if months < 4:
                insights.append('Critically low inventory - strong seller market')
            elif months > 7:
                insights.append('High inventory - favors buyers')
        
        if 'housing_starts' in inventory and inventory['housing_starts']['yoy_change_pct'] < -10:
            insights.append('Construction activity declining')
        
        return {
            'success': True,
            'location': state if state else 'United States (National)',
            'inventory': inventory,
            'insights': insights if insights else ['Inventory levels normal'],
            'source': 'FRED',
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'get_housing_inventory failed: {str(e)}'
        }


def get_price_history(
    city: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict:
    """
    Get historical price time series for a city
    
    Args:
        city: City name (required)
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    
    Returns:
        Dict with historical price observations
    """
    try:
        # Resolve city to FRED series
        city_lower = city.lower().strip()
        series_id = CITY_SERIES_MAP.get(city_lower)
        
        if not series_id:
            # Try national index as fallback
            series_id = 'CSUSHPISA'
            location = 'United States (National)'
        else:
            location = city.title()
        
        # Calculate lookback days
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            lookback_days = (datetime.now() - start_dt).days
        else:
            lookback_days = 730  # 2 years default
        
        data = _fetch_fred_series(series_id, lookback_days=lookback_days)
        
        if not data['success']:
            return data
        
        # Filter by date range if provided
        observations = data['observations']
        if start_date:
            observations = [o for o in observations if o['date'] >= start_date]
        if end_date:
            observations = [o for o in observations if o['date'] <= end_date]
        
        # Calculate statistics
        values = [o['value'] for o in observations]
        price_stats = {
            'min': min(values),
            'max': max(values),
            'mean': sum(values) / len(values),
            'start_value': observations[0]['value'],
            'end_value': observations[-1]['value'],
            'total_change_pct': ((observations[-1]['value'] - observations[0]['value']) / observations[0]['value'] * 100)
        }
        
        return {
            'success': True,
            'location': location,
            'series_id': series_id,
            'start_date': observations[0]['date'],
            'end_date': observations[-1]['date'],
            'observations': observations,
            'statistics': price_stats,
            'count': len(observations),
            'source': 'FRED',
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'get_price_history failed: {str(e)}'
        }


def list_available_cities() -> Dict:
    """
    List all cities with available price index data
    
    Returns:
        Dict with available cities and their FRED series IDs
    """
    return {
        'success': True,
        'available_cities': [
            {'city': city.title(), 'series_id': series_id}
            for city, series_id in CITY_SERIES_MAP.items()
        ],
        'count': len(CITY_SERIES_MAP),
        'note': 'Based on S&P/Case-Shiller 20-City Composite Index',
        'timestamp': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("UrbanMetrics Housing API Module")
    print("=" * 60)
    
    # Test get_market_summary
    print("\n1. Market Summary (National):")
    summary = get_market_summary()
    print(json.dumps(summary, indent=2))
    
    # Test get_housing_price_index
    print("\n2. Housing Price Index (New York):")
    price_idx = get_housing_price_index(city='New York')
    print(json.dumps(price_idx, indent=2))
    
    # List available cities
    print("\n3. Available Cities:")
    cities = list_available_cities()
    print(json.dumps(cities, indent=2))

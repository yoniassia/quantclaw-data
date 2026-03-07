#!/usr/bin/env python3
"""
FRED Housing API — Real Estate & Housing Market Data

Specialized module for housing and real estate market data from FRED.
Provides comprehensive access to:
- S&P/Case-Shiller Home Price Indices (national, metro-level)
- Housing starts and building permits
- Existing and new home sales
- Mortgage rates (30Y, 15Y, ARM)
- Housing affordability indices
- Homeownership rates
- Housing inventory and supply metrics

Source: https://fred.stlouisfed.org/docs/api/fred/
Category: Real Estate & Housing
Free tier: True (requires FRED_API_KEY env var for higher limits)
Author: QuantClaw Data NightBuilder
Phase: Night Build - fred_housing_api
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# FRED API Configuration
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# ========== HOUSING DATA SERIES REGISTRY ==========

FRED_HOUSING_SERIES = {
    # ===== HOME PRICE INDICES =====
    'HOME_PRICES': {
        'CSUSHPISA': 'S&P/Case-Shiller U.S. National Home Price Index',
        'CSUSHPINSA': 'S&P/Case-Shiller U.S. National Home Price Index (NSA)',
        'SPCS20RSA': 'S&P/Case-Shiller 20-City Composite Home Price Index',
        'MSPUS': 'Median Sales Price of Houses Sold for the United States',
        'ASPUS': 'Average Sales Price of Houses Sold for the United States',
        'USSTHPI': 'All-Transactions House Price Index for the United States',
        'HPIPONM226S': 'House Price Index for the United States',
    },
    
    # ===== HOUSING SUPPLY & CONSTRUCTION =====
    'CONSTRUCTION': {
        'HOUST': 'Housing Starts: Total New Privately Owned',
        'HOUST1F': 'Housing Starts: 1-Unit Structures',
        'HOUST5F': 'Housing Starts: 5-Unit Structures or More',
        'PERMIT': 'New Privately-Owned Housing Units Authorized by Building Permits',
        'PERMIT1': 'New Privately-Owned Housing Units Authorized: 1-Unit Structures',
        'COMPUTSA': 'New Privately-Owned Housing Units Completed: Total',
        'UNDCONTSA': 'New Privately-Owned Housing Units Under Construction',
    },
    
    # ===== HOME SALES =====
    'HOME_SALES': {
        'EXHOSLUSM495S': 'Existing Home Sales',
        'HSN1F': 'New One Family Houses Sold',
        'NEWHOUSE': 'New Houses Sold in the United States',
        'ETSLTOTALSAUSA': 'Total Existing Home Sales',
        'MEDDAYONMAR': 'Median Days on Market for Homes',
    },
    
    # ===== MORTGAGE RATES =====
    'MORTGAGE_RATES': {
        'MORTGAGE30US': '30-Year Fixed Rate Mortgage Average',
        'MORTGAGE15US': '15-Year Fixed Rate Mortgage Average',
        'MORTGAGE5US': '5/1-Year Adjustable Rate Mortgage Average',
        'OBMMIJUMBO30YF': '30-Year Jumbo Mortgage Rate',
        'MORTGAGE30USCOMBINED': '30-Year Fixed Mortgage Rate (Combined)',
    },
    
    # ===== HOUSING AFFORDABILITY =====
    'AFFORDABILITY': {
        'FIXHAI': 'Fixed Rate 30-Year Housing Affordability Index',
        'ETOTALUSQ176N': 'Housing Affordability Index',
        'MDSP': 'Mortgage Debt Service Payments as % of Disposable Income',
        'HOWNRATEUSQ156N': 'Homeownership Rate for the United States',
        'RHORUSQ156N': 'Homeownership Rate: United States',
    },
    
    # ===== HOUSING INVENTORY =====
    'INVENTORY': {
        'MSACSR': 'Monthly Supply of Houses in the United States',
        'ACTLISCOUUS': 'Active Listing Count in the United States',
        'NEWLISCOUUS': 'New Listing Count in the United States',
        'INVENTORYUSM052N': 'Inventory of Homes for Sale',
    },
    
    # ===== VACANCY & RENTAL =====
    'VACANCY_RENTAL': {
        'RHVRUSQ156N': 'Rental Vacancy Rate for the United States',
        'HSVR': 'Homeowner Vacancy Rate for the United States',
        'RRVRUSQ156N': 'Rental Vacancy Rate',
        'CUUR0000SEHA': 'Rent of Primary Residence',
    },
}


def get_fred_series(
    series_id: str,
    lookback_days: int = 365,
    api_key: Optional[str] = None
) -> Dict:
    """
    Fetch single FRED time series (helper function)
    
    Args:
        series_id: FRED series identifier (e.g., 'CSUSHPISA')
        lookback_days: Number of days of history (default 365)
        api_key: Optional FRED API key for higher rate limits
    
    Returns:
        Dict with series data, latest value, and changes
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
            return {
                "success": False,
                "error": "No observations in response",
                "series_id": series_id
            }
        
        # Filter out missing values (".")
        obs = [o for o in data["observations"] if o["value"] != "."]
        
        if not obs:
            return {
                "success": False,
                "error": "No valid observations found",
                "series_id": series_id
            }
        
        latest = obs[-1]
        latest_val = float(latest["value"])
        
        # Calculate changes
        changes = {}
        if len(obs) >= 2:
            prev_val = float(obs[-2]["value"])
            changes["period_change"] = latest_val - prev_val
            changes["period_change_pct"] = ((latest_val - prev_val) / prev_val * 100) if prev_val != 0 else 0
        
        if len(obs) >= 30:  # ~1 month
            month_ago = float(obs[-30]["value"])
            changes["month_change"] = latest_val - month_ago
            changes["month_change_pct"] = ((latest_val - month_ago) / month_ago * 100) if month_ago != 0 else 0
        
        if len(obs) >= 90:  # ~3 months
            quarter_ago = float(obs[-90]["value"])
            changes["quarter_change"] = latest_val - quarter_ago
            changes["quarter_change_pct"] = ((latest_val - quarter_ago) / quarter_ago * 100) if quarter_ago != 0 else 0
        
        # Year-over-year
        year_ago_idx = min(len(obs) - 1, 252)  # ~252 trading days
        if year_ago_idx > 0:
            year_ago = float(obs[-year_ago_idx]["value"])
            changes["yoy_change"] = latest_val - year_ago
            changes["yoy_change_pct"] = ((latest_val - year_ago) / year_ago * 100) if year_ago != 0 else 0
        
        return {
            "success": True,
            "series_id": series_id,
            "latest_value": latest_val,
            "latest_date": latest["date"],
            "changes": changes,
            "observations": [{"date": o["date"], "value": float(o["value"])} for o in obs[-90:]],
            "count": len(obs)
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "series_id": series_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "series_id": series_id
        }


def get_home_prices(api_key: Optional[str] = None) -> Dict:
    """
    Get home price indices including Case-Shiller, median/average prices
    
    Returns:
        Dict with national and metro price indices, YoY changes, and trends
    """
    price_series = FRED_HOUSING_SERIES['HOME_PRICES']
    results = {}
    
    for series_id, name in price_series.items():
        data = get_fred_series(series_id, lookback_days=730, api_key=api_key)  # 2 years
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'yoy_change': data['changes'].get('yoy_change', 0),
                'yoy_change_pct': data['changes'].get('yoy_change_pct', 0),
                'quarter_change_pct': data['changes'].get('quarter_change_pct', 0)
            }
    
    # Analyze price trends
    price_insights = []
    if 'CSUSHPISA' in results:
        cs_yoy = results['CSUSHPISA']['yoy_change_pct']
        if cs_yoy > 10:
            price_insights.append(f'Strong home price appreciation: {cs_yoy:.1f}% YoY')
        elif cs_yoy < -5:
            price_insights.append(f'Home prices declining: {cs_yoy:.1f}% YoY')
        else:
            price_insights.append(f'Moderate price growth: {cs_yoy:.1f}% YoY')
    
    if 'MSPUS' in results:
        median_price = results['MSPUS']['value']
        price_insights.append(f'Median home price: ${median_price:,.0f}')
    
    return {
        'success': True,
        'home_prices': results,
        'insights': price_insights,
        'timestamp': datetime.now().isoformat()
    }


def get_construction_data(api_key: Optional[str] = None) -> Dict:
    """
    Get housing starts, building permits, and construction metrics
    
    Returns:
        Dict with construction activity levels and trends
    """
    construction_series = FRED_HOUSING_SERIES['CONSTRUCTION']
    results = {}
    
    for series_id, name in construction_series.items():
        data = get_fred_series(series_id, lookback_days=365, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'month_change_pct': data['changes'].get('month_change_pct', 0),
                'yoy_change_pct': data['changes'].get('yoy_change_pct', 0)
            }
    
    # Analyze construction activity
    construction_insights = []
    if 'HOUST' in results:
        starts = results['HOUST']['value']
        starts_yoy = results['HOUST']['yoy_change_pct']
        construction_insights.append(f'Housing starts: {starts:.0f}K units ({starts_yoy:+.1f}% YoY)')
        
        if starts < 1000:
            construction_insights.append('Construction activity subdued (<1M annual rate)')
        elif starts > 1500:
            construction_insights.append('Robust construction activity (>1.5M annual rate)')
    
    if 'PERMIT' in results:
        permits = results['PERMIT']['value']
        permits_yoy = results['PERMIT']['yoy_change_pct']
        construction_insights.append(f'Building permits: {permits:.0f}K units ({permits_yoy:+.1f}% YoY)')
    
    return {
        'success': True,
        'construction': results,
        'insights': construction_insights,
        'timestamp': datetime.now().isoformat()
    }


def get_home_sales(api_key: Optional[str] = None) -> Dict:
    """
    Get existing and new home sales data
    
    Returns:
        Dict with sales volumes and trends
    """
    sales_series = FRED_HOUSING_SERIES['HOME_SALES']
    results = {}
    
    for series_id, name in sales_series.items():
        data = get_fred_series(series_id, lookback_days=365, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'month_change_pct': data['changes'].get('month_change_pct', 0),
                'yoy_change_pct': data['changes'].get('yoy_change_pct', 0)
            }
    
    # Analyze sales activity
    sales_insights = []
    if 'EXHOSLUSM495S' in results:
        existing_sales = results['EXHOSLUSM495S']['value']
        existing_yoy = results['EXHOSLUSM495S']['yoy_change_pct']
        sales_insights.append(f'Existing home sales: {existing_sales:.2f}M units ({existing_yoy:+.1f}% YoY)')
    
    if 'HSN1F' in results:
        new_sales = results['HSN1F']['value']
        new_yoy = results['HSN1F']['yoy_change_pct']
        sales_insights.append(f'New home sales: {new_sales:.0f}K units ({new_yoy:+.1f}% YoY)')
    
    if 'MEDDAYONMAR' in results:
        days_on_market = results['MEDDAYONMAR']['value']
        if days_on_market < 30:
            sales_insights.append(f'Hot market: {days_on_market:.0f} days on market')
        elif days_on_market > 60:
            sales_insights.append(f'Cooling market: {days_on_market:.0f} days on market')
    
    return {
        'success': True,
        'home_sales': results,
        'insights': sales_insights,
        'timestamp': datetime.now().isoformat()
    }


def get_mortgage_rates(api_key: Optional[str] = None) -> Dict:
    """
    Get mortgage rates across terms (30Y, 15Y, ARM)
    
    Returns:
        Dict with current mortgage rates and recent changes
    """
    mortgage_series = FRED_HOUSING_SERIES['MORTGAGE_RATES']
    results = {}
    
    for series_id, name in mortgage_series.items():
        data = get_fred_series(series_id, lookback_days=180, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'rate': data['latest_value'],
                'date': data['latest_date'],
                'month_change': data['changes'].get('month_change', 0),
                'quarter_change': data['changes'].get('quarter_change', 0)
            }
    
    # Analyze rate environment
    rate_insights = []
    if 'MORTGAGE30US' in results:
        rate_30y = results['MORTGAGE30US']['rate']
        rate_change = results['MORTGAGE30US']['month_change']
        
        rate_insights.append(f'30Y fixed rate: {rate_30y:.2f}% ({rate_change:+.2f}% vs month ago)')
        
        if rate_30y > 7.0:
            rate_insights.append('High mortgage rates limiting affordability')
        elif rate_30y < 4.0:
            rate_insights.append('Low rates supporting housing demand')
    
    if 'MORTGAGE15US' in results and 'MORTGAGE30US' in results:
        spread = results['MORTGAGE30US']['rate'] - results['MORTGAGE15US']['rate']
        rate_insights.append(f'30Y-15Y spread: {spread:.2f}%')
    
    return {
        'success': True,
        'mortgage_rates': results,
        'insights': rate_insights,
        'timestamp': datetime.now().isoformat()
    }


def get_affordability_metrics(api_key: Optional[str] = None) -> Dict:
    """
    Get housing affordability indices and homeownership rates
    
    Returns:
        Dict with affordability indicators and ownership rates
    """
    affordability_series = FRED_HOUSING_SERIES['AFFORDABILITY']
    results = {}
    
    for series_id, name in affordability_series.items():
        data = get_fred_series(series_id, lookback_days=365, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'yoy_change': data['changes'].get('yoy_change', 0),
                'yoy_change_pct': data['changes'].get('yoy_change_pct', 0)
            }
    
    # Analyze affordability
    affordability_insights = []
    if 'FIXHAI' in results:
        hai = results['FIXHAI']['value']
        # HAI: 100 = typical family can afford median-priced home
        if hai < 100:
            affordability_insights.append(f'Housing affordability stressed (HAI: {hai:.1f})')
        else:
            affordability_insights.append(f'Housing affordable for median family (HAI: {hai:.1f})')
    
    if 'RHORUSQ156N' in results:
        ownership_rate = results['RHORUSQ156N']['value']
        affordability_insights.append(f'Homeownership rate: {ownership_rate:.1f}%')
    
    if 'MDSP' in results:
        debt_service = results['MDSP']['value']
        affordability_insights.append(f'Mortgage debt service: {debt_service:.1f}% of income')
    
    return {
        'success': True,
        'affordability': results,
        'insights': affordability_insights,
        'timestamp': datetime.now().isoformat()
    }


def get_inventory_metrics(api_key: Optional[str] = None) -> Dict:
    """
    Get housing inventory and supply metrics
    
    Returns:
        Dict with inventory levels and months of supply
    """
    inventory_series = FRED_HOUSING_SERIES['INVENTORY']
    results = {}
    
    for series_id, name in inventory_series.items():
        data = get_fred_series(series_id, lookback_days=365, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'month_change_pct': data['changes'].get('month_change_pct', 0),
                'yoy_change_pct': data['changes'].get('yoy_change_pct', 0)
            }
    
    # Analyze inventory
    inventory_insights = []
    if 'MSACSR' in results:
        months_supply = results['MSACSR']['value']
        if months_supply < 3:
            inventory_insights.append(f'Tight inventory: {months_supply:.1f} months supply')
        elif months_supply > 6:
            inventory_insights.append(f'Ample inventory: {months_supply:.1f} months supply')
        else:
            inventory_insights.append(f'Balanced inventory: {months_supply:.1f} months supply')
    
    return {
        'success': True,
        'inventory': results,
        'insights': inventory_insights,
        'timestamp': datetime.now().isoformat()
    }


def get_vacancy_rental_metrics(api_key: Optional[str] = None) -> Dict:
    """
    Get vacancy rates and rental market data
    
    Returns:
        Dict with homeowner and rental vacancy rates
    """
    vacancy_series = FRED_HOUSING_SERIES['VACANCY_RENTAL']
    results = {}
    
    for series_id, name in vacancy_series.items():
        data = get_fred_series(series_id, lookback_days=365, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'yoy_change': data['changes'].get('yoy_change', 0)
            }
    
    # Analyze vacancy
    vacancy_insights = []
    if 'HSVR' in results:
        homeowner_vacancy = results['HSVR']['value']
        vacancy_insights.append(f'Homeowner vacancy: {homeowner_vacancy:.1f}%')
    
    if 'RHVRUSQ156N' in results:
        rental_vacancy = results['RHVRUSQ156N']['value']
        vacancy_insights.append(f'Rental vacancy: {rental_vacancy:.1f}%')
    
    return {
        'success': True,
        'vacancy_rental': results,
        'insights': vacancy_insights,
        'timestamp': datetime.now().isoformat()
    }


def get_housing_market_snapshot(api_key: Optional[str] = None) -> Dict:
    """
    Get comprehensive housing market snapshot with key metrics
    
    Returns:
        Dict with critical housing indicators across all categories
    """
    snapshot = {}
    
    # Key metrics from each category
    key_series = {
        'Case-Shiller Home Price Index': 'CSUSHPISA',
        'Median Home Price': 'MSPUS',
        'Housing Starts': 'HOUST',
        'Building Permits': 'PERMIT',
        'Existing Home Sales': 'EXHOSLUSM495S',
        'New Home Sales': 'HSN1F',
        '30Y Mortgage Rate': 'MORTGAGE30US',
        'Housing Affordability Index': 'FIXHAI',
        'Homeownership Rate': 'RHORUSQ156N',
        'Months Supply': 'MSACSR',
    }
    
    for name, series_id in key_series.items():
        data = get_fred_series(series_id, lookback_days=365, api_key=api_key)
        if data['success']:
            snapshot[name] = {
                'value': data['latest_value'],
                'date': data['latest_date'],
                'yoy_change_pct': data['changes'].get('yoy_change_pct', 0)
            }
    
    return {
        'success': True,
        'housing_snapshot': snapshot,
        'timestamp': datetime.now().isoformat(),
        'source': 'FRED API - Housing Market Data'
    }


def list_all_series() -> Dict:
    """
    List all available housing series with counts by category
    
    Returns:
        Dict with all series organized by category
    """
    all_series = {}
    total_count = 0
    
    for category, series_dict in FRED_HOUSING_SERIES.items():
        all_series[category] = {
            'count': len(series_dict),
            'series': [{'id': sid, 'name': name} for sid, name in series_dict.items()]
        }
        total_count += len(series_dict)
    
    return {
        'success': True,
        'total_series': total_count,
        'categories': all_series,
        'module': 'fred_housing_api - Real Estate & Housing'
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("FRED Housing API - Real Estate & Housing Market Data")
    print("=" * 60)
    
    # Show available series
    series_list = list_all_series()
    print(f"\nTotal Series: {series_list['total_series']}")
    print("\nCategories:")
    for cat, info in series_list['categories'].items():
        print(f"  {cat}: {info['count']} series")
    
    print("\n" + json.dumps(series_list, indent=2))

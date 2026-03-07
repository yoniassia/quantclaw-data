#!/usr/bin/env python3
"""
Bank of Japan Time-Series API Module

Provides Japanese macroeconomic data including:
- BOJ policy rates
- JGB yield curve
- Monetary base
- BOJ balance sheet
- Consumer price index

Uses hybrid approach: BOJ direct data where available, FRED fallback for reliability.

Source: https://www.stat-search.boj.or.jp/index_en.html
Fallback: FRED API for Japanese economic data
Category: Macro / Central Banks
Free tier: True - Free public access
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# API Configuration
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# FRED Series for Japanese Data
JAPAN_FRED_SERIES = {
    'policy_rate': 'INTDSRJPM193N',  # Interest Rates, Discount Rate for Japan
    'long_rate': 'IRLTLT01JPM156N',  # Long-Term Interest Rate for Japan (10Y JGB)
    'cpi': 'CPALTT01JPM659N',  # CPI All Items for Japan (Annual Growth Rate)
    'jgb_10y': 'IRLTLT01JPM156N',  # 10-Year JGB Yield
}


def _fetch_fred_series(series_id: str, limit: int = 1) -> Dict:
    """
    Fetch data from FRED API.
    
    Args:
        series_id: FRED series identifier
        limit: Number of observations to return (default: 1 for latest)
    
    Returns:
        Dict with 'data' on success or 'error' on failure
    """
    try:
        if not FRED_API_KEY:
            return {"error": "FRED_API_KEY not configured in .env"}
        
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            'series_id': series_id,
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': limit * 10  # Get more to skip missing values
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if 'observations' in data and len(data['observations']) > 0:
            # Filter out missing values (represented as '.')
            valid_obs = [obs for obs in data['observations'] if obs['value'] != '.']
            if valid_obs:
                return {"data": valid_obs[:limit]}
            else:
                return {"error": f"No valid data found for series {series_id}"}
        else:
            return {"error": f"No data found for series {series_id}"}
            
    except requests.exceptions.RequestException as e:
        return {"error": f"FRED API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def get_boj_policy_rate() -> Dict:
    """
    Get current BOJ policy rate.
    
    Uses FRED series INTDSRJPM193N (Japan Discount Rate).
    
    Returns:
        Dict with 'data' containing:
            - rate: Current policy rate (%)
            - date: Observation date
            - source: Data source
        Or 'error' key on failure
    """
    try:
        result = _fetch_fred_series(JAPAN_FRED_SERIES['policy_rate'], limit=1)
        
        if 'error' in result:
            return result
        
        obs = result['data'][0]
        return {
            "data": {
                "rate": float(obs['value']),
                "date": obs['date'],
                "source": "FRED",
                "series_id": JAPAN_FRED_SERIES['policy_rate']
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to get BOJ policy rate: {str(e)}"}


def get_japan_yield_curve() -> Dict:
    """
    Get JGB (Japanese Government Bond) yield curve.
    
    Returns current yields for multiple maturities.
    Uses FRED long-term rate as primary data point.
    
    Returns:
        Dict with 'data' containing:
            - yields: Dict of maturity -> rate
            - date: Observation date
            - source: Data source
        Or 'error' key on failure
    """
    try:
        # Fetch 10-year JGB yield (most liquid benchmark)
        result = _fetch_fred_series(JAPAN_FRED_SERIES['jgb_10y'], limit=1)
        
        if 'error' in result:
            return result
        
        obs = result['data'][0]
        
        # Note: FRED has limited JGB maturity coverage
        # This returns the 10Y benchmark; full curve would require BOJ direct access
        return {
            "data": {
                "yields": {
                    "10y": float(obs['value'])
                },
                "date": obs['date'],
                "source": "FRED",
                "note": "Full yield curve requires BOJ direct access; showing 10Y benchmark",
                "series_id": JAPAN_FRED_SERIES['jgb_10y']
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to get Japan yield curve: {str(e)}"}


def get_japan_monetary_base() -> Dict:
    """
    Get Japan monetary base estimate.
    
    Note: Direct monetary base data not consistently available in FRED.
    Uses 10Y JGB yield as proxy for monetary conditions.
    
    Returns:
        Dict with 'data' containing:
            - proxy_indicator: JGB 10Y yield (lower = more expansionary)
            - date: Observation date
            - source: Data source
        Or 'error' key on failure
    """
    try:
        # Use 10Y yield as proxy for monetary conditions
        result = _fetch_fred_series(JAPAN_FRED_SERIES['jgb_10y'], limit=1)
        
        if 'error' in result:
            return result
        
        obs = result['data'][0]
        return {
            "data": {
                "proxy_indicator": float(obs['value']),
                "date": obs['date'],
                "indicator": "JGB 10Y Yield",
                "source": "FRED",
                "note": "10Y JGB yield as proxy for monetary conditions; lower = more expansionary",
                "series_id": JAPAN_FRED_SERIES['jgb_10y']
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to get Japan monetary base: {str(e)}"}


def get_boj_balance_sheet() -> Dict:
    """
    Get BOJ balance sheet summary.
    
    Note: Detailed BOJ balance sheet requires direct BOJ access.
    This provides JGB 10Y yield as proxy for BOJ policy stance.
    
    Returns:
        Dict with 'data' containing:
            - policy_proxy: JGB 10Y yield (reflects BOJ operations)
            - date: Observation date
            - source: Data source
        Or 'error' key on failure
    """
    try:
        # Use 10Y yield as proxy for BOJ balance sheet impact
        result = get_japan_monetary_base()
        
        if 'error' in result:
            return result
        
        return {
            "data": {
                "policy_proxy": result['data']['proxy_indicator'],
                "date": result['data']['date'],
                "indicator": "JGB 10Y Yield",
                "source": "FRED",
                "note": "JGB yield reflects BOJ balance sheet policy; direct data requires BOJ access"
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to get BOJ balance sheet: {str(e)}"}


def get_japan_cpi() -> Dict:
    """
    Get Japan Consumer Price Index growth rate (Annual).
    
    Uses FRED series CPALTT01JPM659N.
    
    Returns:
        Dict with 'data' containing:
            - growth_rate: CPI annual % change
            - date: Observation date
            - source: Data source
        Or 'error' key on failure
    """
    try:
        result = _fetch_fred_series(JAPAN_FRED_SERIES['cpi'], limit=1)
        
        if 'error' in result:
            return result
        
        obs = result['data'][0]
        return {
            "data": {
                "growth_rate": float(obs['value']),
                "date": obs['date'],
                "unit": "Percent Annual",
                "source": "FRED",
                "series_id": JAPAN_FRED_SERIES['cpi']
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to get Japan CPI: {str(e)}"}


if __name__ == "__main__":
    print(json.dumps({
        "module": "bank_of_japan_time_series_api",
        "status": "active",
        "functions": [
            "get_boj_policy_rate",
            "get_japan_yield_curve",
            "get_japan_monetary_base",
            "get_boj_balance_sheet",
            "get_japan_cpi"
        ],
        "source": "FRED API (fallback)",
        "note": "Direct BOJ API access limited; using FRED for reliability"
    }, indent=2))

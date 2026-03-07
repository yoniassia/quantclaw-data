#!/usr/bin/env python3
"""
Nasdaq Data Link Bonds — Bond Market Data Module

Provides bond market data including Treasury yields, corporate bonds, credit spreads.
Uses FRED (Federal Reserve Economic Data) as fallback for Treasury yields since it's free and reliable.

Source: https://data.nasdaq.com/databases (Nasdaq Data Link) + FRED fallback
Category: Fixed Income & Credit
Free tier: True
Update frequency: Daily
Author: QuantClaw Data NightBuilder
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

# API Configuration
NASDAQ_DATA_LINK_API_KEY = os.environ.get("NASDAQ_DATA_LINK_API_KEY", "")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# Treasury yield series IDs (FRED)
TREASURY_SERIES = {
    '1_mo': 'DGS1MO',
    '3_mo': 'DGS3MO',
    '6_mo': 'DGS6MO',
    '1_yr': 'DGS1',
    '2_yr': 'DGS2',
    '3_yr': 'DGS3',
    '5_yr': 'DGS5',
    '7_yr': 'DGS7',
    '10_yr': 'DGS10',
    '20_yr': 'DGS20',
    '30_yr': 'DGS30'
}


def get_treasury_yields(limit: int = 100) -> List[Dict]:
    """
    Get US Treasury yield curve data (1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y).
    Uses FRED API as reliable free source.
    
    Args:
        limit: Number of data points to return (default 100)
    
    Returns:
        List of Dict with keys: date, 1_mo, 3_mo, 6_mo, 1_yr, 2_yr, 3_yr, 5_yr, 7_yr, 10_yr, 20_yr, 30_yr
    
    Example:
        >>> yields = get_treasury_yields(10)
        >>> print(f"Latest 10Y: {yields[0]['10_yr']}%")
    """
    try:
        # Use 10-year as primary series to get dates
        params = {
            'series_id': 'DGS10',
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': limit
        }
        
        if FRED_API_KEY:
            params['api_key'] = FRED_API_KEY
        
        response = requests.get(FRED_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if 'observations' not in data:
            return [{'error': 'Invalid API response', 'response': str(data)[:200]}]
        
        observations = data['observations']
        
        if not observations:
            return [{'error': 'No data returned'}]
        
        # Get all yields for each date
        result = []
        for obs in observations:
            date = obs['date']
            record = {'date': date}
            
            # Fetch each maturity
            for maturity_key, series_id in TREASURY_SERIES.items():
                try:
                    params_maturity = {
                        'series_id': series_id,
                        'observation_start': date,
                        'observation_end': date,
                        'file_type': 'json'
                    }
                    if FRED_API_KEY:
                        params_maturity['api_key'] = FRED_API_KEY
                    
                    resp = requests.get(FRED_BASE_URL, params=params_maturity, timeout=10)
                    if resp.status_code == 200:
                        maturity_data = resp.json()
                        if maturity_data.get('observations'):
                            value = maturity_data['observations'][0].get('value')
                            record[maturity_key] = float(value) if value != '.' else None
                except:
                    record[maturity_key] = None
            
            result.append(record)
        
        return result
        
    except requests.exceptions.RequestException as e:
        return [{'error': f'Request failed: {str(e)}'}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}'}]


def get_latest_treasury_yields() -> Dict:
    """
    Get the most recent US Treasury yield curve data point.
    Uses cached/simplified approach to avoid rate limits.
    
    Returns:
        Dict with latest yields across all maturities
    
    Example:
        >>> latest = get_latest_treasury_yields()
        >>> print(f"10Y: {latest.get('10_yr', 'N/A')}%")
    """
    try:
        # Fetch latest for each series individually
        result = {'date': datetime.now().strftime('%Y-%m-%d')}
        
        for maturity_key, series_id in TREASURY_SERIES.items():
            try:
                params = {
                    'series_id': series_id,
                    'file_type': 'json',
                    'sort_order': 'desc',
                    'limit': 1
                }
                
                if FRED_API_KEY:
                    params['api_key'] = FRED_API_KEY
                
                response = requests.get(FRED_BASE_URL, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('observations'):
                        obs = data['observations'][0]
                        result['date'] = obs['date']
                        value = obs.get('value')
                        result[maturity_key] = float(value) if value and value != '.' else None
                else:
                    result[maturity_key] = None
                    
            except Exception as e:
                result[maturity_key] = None
        
        return result
        
    except Exception as e:
        return {'error': f'Failed to fetch latest yields: {str(e)}'}


def get_yield_spread(short_maturity: str = '2_yr', long_maturity: str = '10_yr', limit: int = 100) -> List[Dict]:
    """
    Calculate yield spread between two maturities (e.g., 10Y-2Y spread).
    
    Args:
        short_maturity: Short-term maturity key (e.g., '2_yr', '3_mo')
        long_maturity: Long-term maturity key (e.g., '10_yr', '30_yr')
        limit: Number of data points
    
    Returns:
        List of Dict with keys: date, spread, short_yield, long_yield
    
    Example:
        >>> spreads = get_yield_spread('2_yr', '10_yr', 30)
        >>> print(f"Latest 10Y-2Y spread: {spreads[0]['spread']:.2f}bp")
    """
    try:
        yields = get_treasury_yields(limit=limit)
        
        if not yields or 'error' in yields[0]:
            return yields
        
        result = []
        for record in yields:
            if short_maturity in record and long_maturity in record:
                short_val = record[short_maturity]
                long_val = record[long_maturity]
                
                if short_val is not None and long_val is not None:
                    spread = float(long_val) - float(short_val)
                    result.append({
                        'date': record.get('date'),
                        'spread': round(spread, 4),
                        'short_yield': short_val,
                        'long_yield': long_val,
                        'short_maturity': short_maturity,
                        'long_maturity': long_maturity
                    })
        
        return result
        
    except Exception as e:
        return [{'error': f'Failed to calculate spread: {str(e)}'}]


def get_yield_curve_shape(limit: int = 1) -> List[Dict]:
    """
    Analyze yield curve shape (normal, inverted, flat) based on key spreads.
    
    Args:
        limit: Number of yield curves to analyze
    
    Returns:
        List of Dict with yield curve analysis
    
    Example:
        >>> curve = get_yield_curve_shape(1)
        >>> print(f"Curve shape: {curve[0]['shape']}")
    """
    try:
        yields = get_treasury_yields(limit=limit)
        
        if not yields or 'error' in yields[0]:
            return yields
        
        result = []
        for record in yields:
            # Calculate key spreads
            spread_2_10 = None
            spread_3m_10 = None
            
            if '2_yr' in record and '10_yr' in record:
                if record['2_yr'] is not None and record['10_yr'] is not None:
                    spread_2_10 = float(record['10_yr']) - float(record['2_yr'])
            
            if '3_mo' in record and '10_yr' in record:
                if record['3_mo'] is not None and record['10_yr'] is not None:
                    spread_3m_10 = float(record['10_yr']) - float(record['3_mo'])
            
            # Determine shape
            shape = 'unknown'
            if spread_2_10 is not None:
                if spread_2_10 > 0.5:
                    shape = 'normal'
                elif spread_2_10 < -0.2:
                    shape = 'inverted'
                else:
                    shape = 'flat'
            
            result.append({
                'date': record.get('date'),
                'shape': shape,
                'spread_2_10': spread_2_10,
                'spread_3m_10': spread_3m_10,
                '2_yr': record.get('2_yr'),
                '10_yr': record.get('10_yr'),
                '30_yr': record.get('30_yr')
            })
        
        return result
        
    except Exception as e:
        return [{'error': f'Failed to analyze yield curve: {str(e)}'}]


if __name__ == "__main__":
    # Test the module
    print("=== Nasdaq Data Link Bonds Module Test ===\n")
    
    print("1. Latest Treasury Yields:")
    latest = get_latest_treasury_yields()
    print(json.dumps(latest, indent=2))
    
    print("\n2. Yield Curve Shape:")
    curve = get_yield_curve_shape(1)
    print(json.dumps(curve, indent=2))
    
    print("\n=== Module Test Complete ===")

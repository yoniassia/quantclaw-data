#!/usr/bin/env python3
"""
Alpha Vantage Treasury Yields Module

Real-time and historical U.S. Treasury yield data across various maturities.
Includes daily yields for bonds like 2-year, 5-year, 10-year, and 30-year Treasuries,
useful for tracking interest rate trends and fixed income analysis.

Source: https://www.alphavantage.co/documentation/#treasury-yield
Category: Fixed Income & Credit
Free tier: 500 API calls per day, 5 calls per minute
Author: QuantClaw Data NightBuilder
Phase: 106
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

# Alpha Vantage API Configuration
AV_BASE_URL = "https://www.alphavantage.co/query"
AV_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")

# Valid maturity options
VALID_MATURITIES = ['3month', '2year', '5year', '7year', '10year', '30year']
VALID_INTERVALS = ['daily', 'weekly', 'monthly']


def get_treasury_yield(
    maturity: str = '10year',
    interval: str = 'daily',
    api_key: Optional[str] = None
) -> Dict:
    """
    Fetch Treasury yield data for a specific maturity
    
    Args:
        maturity: Treasury maturity (3month, 2year, 5year, 7year, 10year, 30year)
        interval: Data interval (daily, weekly, monthly)
        api_key: Optional Alpha Vantage API key
    
    Returns:
        Dict with yield data, latest value, and changes
    """
    try:
        # Validate inputs
        if maturity not in VALID_MATURITIES:
            return {
                "success": False,
                "error": f"Invalid maturity. Must be one of: {', '.join(VALID_MATURITIES)}",
                "maturity": maturity
            }
        
        if interval not in VALID_INTERVALS:
            return {
                "success": False,
                "error": f"Invalid interval. Must be one of: {', '.join(VALID_INTERVALS)}",
                "interval": interval
            }
        
        params = {
            "function": "TREASURY_YIELD",
            "interval": interval,
            "maturity": maturity,
            "apikey": api_key or AV_API_KEY
        }
        
        response = requests.get(AV_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API error messages
        if "Error Message" in data:
            return {
                "success": False,
                "error": data["Error Message"],
                "maturity": maturity
            }
        
        if "Note" in data:
            return {
                "success": False,
                "error": "API rate limit reached. Note: " + data["Note"],
                "maturity": maturity
            }
        
        if "data" not in data:
            return {
                "success": False,
                "error": "No data in response",
                "maturity": maturity,
                "response": data
            }
        
        observations = data["data"]
        
        if not observations:
            return {
                "success": False,
                "error": "No observations found",
                "maturity": maturity
            }
        
        # Parse observations (Alpha Vantage returns newest first)
        parsed_obs = []
        for obs in observations:
            try:
                parsed_obs.append({
                    "date": obs["date"],
                    "value": float(obs["value"])
                })
            except (KeyError, ValueError):
                continue
        
        if not parsed_obs:
            return {
                "success": False,
                "error": "No valid observations after parsing",
                "maturity": maturity
            }
        
        # Latest value is first in Alpha Vantage response
        latest = parsed_obs[0]
        latest_val = latest["value"]
        
        # Calculate changes
        changes = {}
        if len(parsed_obs) >= 2:
            prev_val = parsed_obs[1]["value"]
            changes["period_change"] = round(latest_val - prev_val, 4)
            changes["period_change_bps"] = round((latest_val - prev_val) * 100, 2)
        
        if len(parsed_obs) >= 5:  # ~1 week for daily
            week_ago = parsed_obs[4]["value"]
            changes["week_change"] = round(latest_val - week_ago, 4)
            changes["week_change_bps"] = round((latest_val - week_ago) * 100, 2)
        
        if len(parsed_obs) >= 22:  # ~1 month for daily
            month_ago = parsed_obs[21]["value"]
            changes["month_change"] = round(latest_val - month_ago, 4)
            changes["month_change_bps"] = round((latest_val - month_ago) * 100, 2)
        
        return {
            "success": True,
            "maturity": maturity,
            "interval": interval,
            "latest_value": latest_val,
            "latest_date": latest["date"],
            "changes": changes,
            "observations": parsed_obs[:90],  # Last 90 data points
            "count": len(parsed_obs),
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "maturity": maturity
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "maturity": maturity
        }


def get_yield_curve(
    interval: str = 'daily',
    api_key: Optional[str] = None
) -> Dict:
    """
    Fetch multiple Treasury yields to construct a yield curve
    
    Args:
        interval: Data interval (daily, weekly, monthly)
        api_key: Optional Alpha Vantage API key
    
    Returns:
        Dict with yield curve data across all maturities
    """
    try:
        curve = {}
        errors = []
        
        # Fetch all standard maturities (skip 3month and 7year for key curve points)
        key_maturities = ['2year', '5year', '10year', '30year']
        
        for maturity in key_maturities:
            result = get_treasury_yield(maturity, interval, api_key)
            
            if result['success']:
                curve[maturity] = {
                    'yield': result['latest_value'],
                    'date': result['latest_date'],
                    'change_bps': result['changes'].get('period_change_bps', 0)
                }
            else:
                errors.append(f"{maturity}: {result.get('error', 'Unknown error')}")
        
        if not curve:
            return {
                "success": False,
                "error": "Failed to fetch any maturities",
                "errors": errors
            }
        
        # Calculate curve characteristics
        curve_analysis = {}
        
        if '2year' in curve and '10year' in curve:
            spread_2_10 = round(curve['10year']['yield'] - curve['2year']['yield'], 4)
            curve_analysis['2y_10y_spread'] = spread_2_10
            curve_analysis['2y_10y_spread_bps'] = round(spread_2_10 * 100, 2)
            
            if spread_2_10 < 0:
                curve_analysis['curve_shape'] = 'Inverted (2-10)'
            elif spread_2_10 < 0.2:
                curve_analysis['curve_shape'] = 'Flat'
            else:
                curve_analysis['curve_shape'] = 'Normal (upward sloping)'
        
        if '10year' in curve and '30year' in curve:
            spread_10_30 = round(curve['30year']['yield'] - curve['10year']['yield'], 4)
            curve_analysis['10y_30y_spread'] = spread_10_30
            curve_analysis['10y_30y_spread_bps'] = round(spread_10_30 * 100, 2)
        
        return {
            "success": True,
            "interval": interval,
            "yield_curve": curve,
            "curve_analysis": curve_analysis,
            "errors": errors if errors else None,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_yield_spread(
    short_maturity: str = '2year',
    long_maturity: str = '10year',
    interval: str = 'daily',
    api_key: Optional[str] = None
) -> Dict:
    """
    Calculate spread between two Treasury maturities
    
    Args:
        short_maturity: Shorter maturity (e.g., '2year')
        long_maturity: Longer maturity (e.g., '10year')
        interval: Data interval (daily, weekly, monthly)
        api_key: Optional Alpha Vantage API key
    
    Returns:
        Dict with spread data and historical changes
    """
    try:
        # Fetch both maturities
        short_result = get_treasury_yield(short_maturity, interval, api_key)
        long_result = get_treasury_yield(long_maturity, interval, api_key)
        
        if not short_result['success']:
            return {
                "success": False,
                "error": f"Failed to fetch {short_maturity}: {short_result.get('error', 'Unknown')}",
                "short_maturity": short_maturity
            }
        
        if not long_result['success']:
            return {
                "success": False,
                "error": f"Failed to fetch {long_maturity}: {long_result.get('error', 'Unknown')}",
                "long_maturity": long_maturity
            }
        
        # Calculate current spread
        short_yield = short_result['latest_value']
        long_yield = long_result['latest_value']
        current_spread = round(long_yield - short_yield, 4)
        current_spread_bps = round(current_spread * 100, 2)
        
        # Calculate historical spreads for trend analysis
        historical_spreads = []
        short_obs = {obs['date']: obs['value'] for obs in short_result['observations']}
        
        for long_obs in long_result['observations'][:30]:  # Last 30 periods
            date = long_obs['date']
            if date in short_obs:
                spread = round(long_obs['value'] - short_obs[date], 4)
                historical_spreads.append({
                    'date': date,
                    'spread': spread,
                    'spread_bps': round(spread * 100, 2)
                })
        
        # Trend analysis
        trend_analysis = {}
        if len(historical_spreads) >= 2:
            recent_spread = historical_spreads[0]['spread']
            older_spread = historical_spreads[-1]['spread']
            spread_change = round(recent_spread - older_spread, 4)
            
            trend_analysis['period_change'] = spread_change
            trend_analysis['period_change_bps'] = round(spread_change * 100, 2)
            
            if spread_change < -0.1:
                trend_analysis['trend'] = 'Flattening'
            elif spread_change > 0.1:
                trend_analysis['trend'] = 'Steepening'
            else:
                trend_analysis['trend'] = 'Stable'
        
        # Interpretation
        interpretation = []
        if current_spread < 0:
            interpretation.append('Inverted yield curve - recession signal')
        elif current_spread < 0.25:
            interpretation.append('Very flat curve - economic uncertainty')
        elif current_spread > 2.0:
            interpretation.append('Steep curve - strong growth expectations')
        else:
            interpretation.append('Normal curve shape')
        
        return {
            "success": True,
            "short_maturity": short_maturity,
            "long_maturity": long_maturity,
            "interval": interval,
            "short_yield": short_yield,
            "long_yield": long_yield,
            "current_spread": current_spread,
            "current_spread_bps": current_spread_bps,
            "historical_spreads": historical_spreads,
            "trend_analysis": trend_analysis,
            "interpretation": interpretation,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_historical_yields(
    maturity: str = '10year',
    start_date: Optional[str] = None,
    interval: str = 'daily',
    api_key: Optional[str] = None
) -> Dict:
    """
    Get historical Treasury yield data for a specific maturity
    
    Args:
        maturity: Treasury maturity (3month, 2year, 5year, 7year, 10year, 30year)
        start_date: Start date in YYYY-MM-DD format (optional, filters observations)
        interval: Data interval (daily, weekly, monthly)
        api_key: Optional Alpha Vantage API key
    
    Returns:
        Dict with full historical data and statistics
    """
    try:
        # Fetch all available data
        result = get_treasury_yield(maturity, interval, api_key)
        
        if not result['success']:
            return result
        
        observations = result['observations']
        
        # Filter by start_date if provided
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                observations = [
                    obs for obs in observations 
                    if datetime.strptime(obs['date'], "%Y-%m-%d") >= start_dt
                ]
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid start_date format. Use YYYY-MM-DD",
                    "start_date": start_date
                }
        
        if not observations:
            return {
                "success": False,
                "error": "No observations in date range",
                "maturity": maturity,
                "start_date": start_date
            }
        
        # Calculate statistics
        values = [obs['value'] for obs in observations]
        
        stats = {
            'count': len(values),
            'current': values[0],
            'high': round(max(values), 4),
            'low': round(min(values), 4),
            'mean': round(sum(values) / len(values), 4),
            'range': round(max(values) - min(values), 4),
            'range_bps': round((max(values) - min(values)) * 100, 2)
        }
        
        # Find high and low dates
        for obs in observations:
            if obs['value'] == stats['high']:
                stats['high_date'] = obs['date']
            if obs['value'] == stats['low']:
                stats['low_date'] = obs['date']
        
        return {
            "success": True,
            "maturity": maturity,
            "interval": interval,
            "start_date": start_date or observations[-1]['date'],
            "end_date": observations[0]['date'],
            "statistics": stats,
            "observations": observations,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_treasury_snapshot(api_key: Optional[str] = None) -> Dict:
    """
    Get quick snapshot of key Treasury yields
    
    Returns:
        Dict with current yields for 2Y, 10Y, 30Y and key spreads
    """
    try:
        snapshot = {}
        key_maturities = ['2year', '10year', '30year']
        
        for maturity in key_maturities:
            result = get_treasury_yield(maturity, 'daily', api_key)
            if result['success']:
                snapshot[maturity] = {
                    'yield': result['latest_value'],
                    'date': result['latest_date'],
                    'change_bps': result['changes'].get('period_change_bps', 0)
                }
        
        # Calculate key spreads
        spreads = {}
        if '2year' in snapshot and '10year' in snapshot:
            spreads['2y_10y'] = round(
                (snapshot['10year']['yield'] - snapshot['2year']['yield']) * 100, 2
            )
        
        if '10year' in snapshot and '30year' in snapshot:
            spreads['10y_30y'] = round(
                (snapshot['30year']['yield'] - snapshot['10year']['yield']) * 100, 2
            )
        
        return {
            "success": True,
            "snapshot": snapshot,
            "spreads_bps": spreads,
            "timestamp": datetime.now().isoformat(),
            "source": "Alpha Vantage Treasury Yields API"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Alpha Vantage Treasury Yields Module")
    print("=" * 60)
    
    # Quick snapshot
    snapshot = get_treasury_snapshot()
    print("\nTreasury Yields Snapshot:")
    print(json.dumps(snapshot, indent=2))

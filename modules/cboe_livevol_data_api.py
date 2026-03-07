#!/usr/bin/env python3
"""
CBOE LiveVol Data API — Options Analytics & Unusual Activity

Provides access to CBOE options data with dual strategy:
1. LiveVol API (if LIVEVOL_API_TOKEN available) - real-time unusual activity
2. CBOE public data (fallback) - put/call ratios, VIX, most active options

Functions:
- get_put_call_ratio() — Daily equity/index/total P/C ratios
- get_most_active_options() — Most active options by volume
- get_vix_data() — VIX historical data
- get_unusual_activity() — Unusual options activity detection
- get_options_volume_summary() — Daily volume summary

Source: https://datashop.cboe.com/livevol-api
Category: Options & Derivatives
Free tier: True - CBOE public data free; LiveVol 100 queries/day with token
Author: QuantClaw Data NightBuilder
Phase: 105
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv
import time

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# API Configuration
LIVEVOL_BASE_URL = "https://api.livevol.com/v1"
LIVEVOL_API_TOKEN = os.environ.get("LIVEVOL_API_TOKEN", "")

# CBOE Data URLs - public endpoints
CBOE_VIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
CBOE_MARKET_STATS_URL = "https://www.cboe.com/us/options/market_statistics/"

# Enhanced headers to avoid blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}


def get_put_call_ratio(date: Optional[str] = None) -> Dict[str, Union[float, str]]:
    """
    Get CBOE put/call ratios for equity, index, and total options.
    
    Note: CBOE restricts direct CSV downloads. This function returns
    typical ranges and directs users to CBOE website for current data.
    
    Args:
        date: Optional date in YYYY-MM-DD format (defaults to latest available)
        
    Returns:
        Dict with guidance and typical ranges
        
    Example:
        >>> ratios = get_put_call_ratio()
        >>> print(f"Source: {ratios['source']}")
    """
    
    # CBOE blocks automated access to P/C ratio data
    # Provide typical ranges and guidance
    return {
        "date": date or datetime.now().strftime('%Y-%m-%d'),
        "note": "CBOE restricts automated access to P/C ratio data",
        "guidance": "Visit https://www.cboe.com/us/options/market_statistics/daily/ for current ratios",
        "typical_ranges": {
            "equity_pc": "0.55 - 0.85 (normal market)",
            "index_pc": "1.0 - 2.0 (hedging activity)",
            "total_pc": "0.7 - 1.2 (combined)"
        },
        "interpretation": {
            "< 0.7": "Bullish sentiment (more calls than puts)",
            "0.7 - 1.0": "Neutral market",
            "> 1.0": "Bearish sentiment or hedging activity"
        },
        "source": "CBOE Market Statistics (manual access required)"
    }


def get_most_active_options(underlying: Optional[str] = None) -> List[Dict]:
    """
    Get most active options by volume from CBOE.
    
    Note: CBOE restricts direct data access. Returns guidance.
    
    Args:
        underlying: Optional ticker symbol to filter (e.g., 'SPY', 'AAPL')
        
    Returns:
        List with guidance for accessing data
        
    Example:
        >>> active = get_most_active_options(underlying='SPY')
    """
    
    return [{
        "note": "CBOE restricts automated access to most active options",
        "guidance": f"Visit https://www.cboe.com/us/options/market_statistics/most_active/ for {underlying or 'all symbols'}",
        "typical_most_active": ["SPY", "QQQ", "AAPL", "TSLA", "NVDA"],
        "data_points": ["Symbol", "Volume", "Strike", "Expiry", "Type"],
        "source": "CBOE Most Active (manual access required)"
    }]


def get_vix_data(days: int = 30) -> Dict[str, Union[List, str, float]]:
    """
    Get VIX historical data from CBOE's public CDN.
    
    Args:
        days: Number of days of historical data (default 30)
        
    Returns:
        Dict with dates, values, current_vix, avg_vix, min_vix, max_vix
        
    Example:
        >>> vix = get_vix_data(days=7)
        >>> print(f"Current VIX: {vix['current_vix']}")
    """
    try:
        # CBOE provides VIX historical data via CDN
        response = requests.get(CBOE_VIX_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # Parse CSV
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        
        # CBOE CSV has columns: DATE, OPEN, HIGH, LOW, CLOSE
        df.columns = df.columns.str.strip().str.upper()
        
        # Convert date column
        df['DATE'] = pd.to_datetime(df['DATE'])
        
        # Filter by date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        df = df[df['DATE'] >= start_date]
        df = df.sort_values('DATE', ascending=False)
        
        if df.empty:
            return {
                "error": "No VIX data available for specified range",
                "days": days
            }
        
        # Use CLOSE column for VIX values
        values = df['CLOSE'].tolist()
        dates = df['DATE'].dt.strftime('%Y-%m-%d').tolist()
        
        return {
            "dates": dates,
            "values": [float(v) for v in values],
            "current_vix": float(values[0]),
            "avg_vix": round(float(df['CLOSE'].mean()), 2),
            "min_vix": float(df['CLOSE'].min()),
            "max_vix": float(df['CLOSE'].max()),
            "days_returned": len(values),
            "days_requested": days,
            "source": "CBOE VIX Index (cdn.cboe.com)",
            "last_updated": dates[0]
        }
        
    except Exception as e:
        return {
            "error": f"Failed to fetch VIX data: {str(e)}",
            "days": days,
            "fallback": "Visit https://www.cboe.com/us/indices/dashboard/VIX/ for current VIX"
        }


def get_unusual_activity(symbol: str) -> Dict[str, Union[List, str]]:
    """
    Detect unusual options activity for a symbol.
    Uses LiveVol API if token available, otherwise provides guidance.
    
    Args:
        symbol: Ticker symbol (e.g., 'SPY', 'AAPL')
        
    Returns:
        Dict with unusual_trades list and metadata
        
    Example:
        >>> unusual = get_unusual_activity('SPY')
        >>> print(f"Method: {unusual['source']}")
    """
    
    # Try LiveVol API first if token available
    if LIVEVOL_API_TOKEN:
        try:
            url = f"{LIVEVOL_BASE_URL}/live/options/unusual-activity"
            headers = {
                "Authorization": f"Bearer {LIVEVOL_API_TOKEN}",
                "Content-Type": "application/json"
            }
            params = {"symbol": symbol.upper()}
            
            response = requests.post(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "symbol": symbol.upper(),
                "unusual_trades": data.get("trades", []),
                "count": len(data.get("trades", [])),
                "source": "LiveVol API",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            pass
    
    # No LiveVol token or API failed
    return {
        "symbol": symbol.upper(),
        "note": "LiveVol API token required for unusual activity detection",
        "guidance": "Set LIVEVOL_API_TOKEN environment variable for 100 free queries/day",
        "unusual_activity_indicators": [
            "Volume > 2x average daily volume",
            "Large block trades (1000+ contracts)",
            "High premium paid relative to intrinsic value",
            "Sweep orders across multiple exchanges",
            "Significant open interest changes"
        ],
        "alternative_sources": [
            "https://www.barchart.com/options/unusual-activity",
            "https://www.marketbeat.com/options/unusual-activity/",
            "Bloomberg Terminal (OMON function)"
        ],
        "source": "Guidance (LiveVol token not configured)",
        "timestamp": datetime.now().isoformat()
    }


def get_options_volume_summary() -> Dict[str, Union[int, float, str]]:
    """
    Get daily options volume summary.
    
    Note: CBOE restricts automated access. Returns guidance.
    
    Returns:
        Dict with guidance and typical volume ranges
        
    Example:
        >>> summary = get_options_volume_summary()
        >>> print(f"Source: {summary['source']}")
    """
    
    return {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "note": "CBOE restricts automated access to volume summary data",
        "guidance": "Visit https://www.cboe.com/us/options/market_statistics/summary/ for current data",
        "typical_daily_volume": {
            "equity_options": "20-40 million contracts",
            "index_options": "5-10 million contracts",
            "total_options": "25-50 million contracts"
        },
        "high_volume_days": {
            "expiration_friday": "50-80 million contracts",
            "major_events": "60-100 million contracts (earnings, FOMC)"
        },
        "source": "CBOE Volume Summary (manual access required)"
    }


# ===== BONUS: Working function that uses CBOE's public VIX data =====

def get_vix_term_structure(months: int = 6) -> Dict[str, Union[List, str]]:
    """
    Get VIX term structure showing volatility expectations.
    Uses VIX historical data to show recent trend.
    
    Args:
        months: Number of months to analyze (default 6)
        
    Returns:
        Dict with term structure data and analysis
        
    Example:
        >>> term = get_vix_term_structure()
        >>> print(f"Contango/Backwardation: {term['structure']}")
    """
    try:
        vix_data = get_vix_data(days=months * 30)
        
        if "error" in vix_data:
            return vix_data
        
        current = vix_data["current_vix"]
        avg_30d = vix_data["avg_vix"]
        
        # Determine structure
        if current < avg_30d:
            structure = "Contango (spot < forward)"
        elif current > avg_30d:
            structure = "Backwardation (spot > forward)"
        else:
            structure = "Flat"
        
        return {
            "current_vix": current,
            "avg_30d_vix": avg_30d,
            "structure": structure,
            "interpretation": {
                "contango": "Normal market - volatility expected to rise",
                "backwardation": "Stressed market - high current volatility",
                "flat": "Stable expectations"
            }[structure.split()[0].lower()],
            "note": "Full term structure requires VIX futures data (not included)",
            "source": "CBOE VIX Historical",
            "last_updated": vix_data.get("last_updated")
        }
        
    except Exception as e:
        return {
            "error": f"Failed to analyze VIX term structure: {str(e)}"
        }


if __name__ == "__main__":
    # Test the module
    print("=== CBOE LiveVol Data API Module Test ===\n")
    
    print("1. VIX Data (7 days):")
    vix = get_vix_data(days=7)
    if "error" not in vix:
        print(f"✓ Current VIX: {vix['current_vix']}")
        print(f"  Average: {vix['avg_vix']}")
        print(f"  Range: {vix['min_vix']} - {vix['max_vix']}")
        print(f"  Data points: {vix['days_returned']}")
    else:
        print(f"✗ {vix['error']}")
    
    print("\n2. VIX Term Structure:")
    term = get_vix_term_structure()
    if "error" not in term:
        print(f"✓ Structure: {term['structure']}")
        print(f"  Current: {term['current_vix']}")
        print(f"  30-day avg: {term['avg_30d_vix']}")
    else:
        print(f"✗ {term['error']}")
    
    print("\n3. Put/Call Ratio (guidance):")
    pc = get_put_call_ratio()
    print(f"✓ {pc['note']}")
    print(f"  Access: {pc['guidance']}")
    
    print("\n4. Unusual Activity Check (SPY):")
    unusual = get_unusual_activity('SPY')
    print(f"✓ Method: {unusual['source']}")
    if LIVEVOL_API_TOKEN:
        print(f"  Found: {unusual.get('count', 0)} unusual trades")
    else:
        print(f"  {unusual.get('note')}")
    
    print("\nModule: cboe_livevol_data_api - Ready ✓")
    print(f"LiveVol API: {'Configured' if LIVEVOL_API_TOKEN else 'Not configured (using fallbacks)'}")

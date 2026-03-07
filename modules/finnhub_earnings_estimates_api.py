#!/usr/bin/env python3
"""
Finnhub Earnings Estimates API — Analyst Consensus & Earnings Data Module

Comprehensive earnings and analyst consensus data including:
- EPS estimates (consensus forecasts)
- Revenue estimates (consensus forecasts)
- Historical earnings (actual vs estimates)
- Analyst recommendations (buy/hold/sell breakdown)
- Price targets (analyst consensus)
- Rating changes (upgrades/downgrades)

Source: https://finnhub.io/docs/api/earnings-estimates
Category: Fundamental Data & Analyst Consensus
Free tier: True (requires FINNHUB_API_KEY env var)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Finnhub API Configuration
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")


def get_eps_estimates(symbol: str = 'AAPL', freq: str = 'quarterly') -> Dict:
    """
    Get EPS (Earnings Per Share) consensus estimates for a symbol.
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
        freq: Frequency - 'quarterly' or 'annual' (default: 'quarterly')
    
    Returns:
        Dict with keys: data (list of estimates with period, epsAvg, epsHigh, epsLow, numberAnalysts),
                       symbol, freq
    
    Example:
        >>> eps = get_eps_estimates('TSLA', freq='quarterly')
        >>> print(f"Next quarter EPS estimate: ${eps['data'][0]['epsAvg']}")
    """
    try:
        url = f"{FINNHUB_BASE_URL}/stock/eps-estimate"
        params = {
            'symbol': symbol,
            'freq': freq,
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "symbol": symbol, "freq": freq}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "symbol": symbol}


def get_revenue_estimates(symbol: str = 'AAPL', freq: str = 'quarterly') -> Dict:
    """
    Get revenue consensus estimates for a symbol.
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
        freq: Frequency - 'quarterly' or 'annual' (default: 'quarterly')
    
    Returns:
        Dict with keys: data (list of estimates with period, revenueAvg, revenueHigh, revenueLow, numberAnalysts),
                       symbol, freq
    
    Example:
        >>> rev = get_revenue_estimates('AAPL', freq='annual')
        >>> print(f"Next year revenue estimate: ${rev['data'][0]['revenueAvg']}M")
    """
    try:
        url = f"{FINNHUB_BASE_URL}/stock/revenue-estimate"
        params = {
            'symbol': symbol,
            'freq': freq,
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "symbol": symbol, "freq": freq}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "symbol": symbol}


def get_earnings_history(symbol: str = 'AAPL') -> List[Dict]:
    """
    Get historical earnings data (actual vs estimated).
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
    
    Returns:
        List of dicts with keys: actual, estimate, period, quarter, year, symbol
    
    Example:
        >>> history = get_earnings_history('TSLA')
        >>> latest = history[0]
        >>> print(f"Latest: Actual ${latest['actual']} vs Estimate ${latest['estimate']}")
    """
    try:
        url = f"{FINNHUB_BASE_URL}/stock/earnings"
        params = {
            'symbol': symbol,
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        return [{"error": str(e), "symbol": symbol}]
    except Exception as e:
        return [{"error": f"Unexpected error: {str(e)}", "symbol": symbol}]


def get_analyst_recommendations(symbol: str = 'AAPL') -> List[Dict]:
    """
    Get analyst recommendation trends (buy/hold/sell breakdown).
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
    
    Returns:
        List of dicts with keys: buy, hold, sell, strongBuy, strongSell, period, symbol
    
    Example:
        >>> recs = get_analyst_recommendations('AAPL')
        >>> latest = recs[0]
        >>> print(f"Buy: {latest['buy']}, Hold: {latest['hold']}, Sell: {latest['sell']}")
    """
    try:
        url = f"{FINNHUB_BASE_URL}/stock/recommendation"
        params = {
            'symbol': symbol,
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        return [{"error": str(e), "symbol": symbol}]
    except Exception as e:
        return [{"error": f"Unexpected error: {str(e)}", "symbol": symbol}]


def get_price_targets(symbol: str = 'AAPL') -> Dict:
    """
    Get analyst price target consensus.
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
    
    Returns:
        Dict with keys: targetHigh, targetLow, targetMean, targetMedian, lastUpdated, symbol
    
    Example:
        >>> targets = get_price_targets('TSLA')
        >>> print(f"Price target: ${targets['targetMean']} (Range: ${targets['targetLow']}-${targets['targetHigh']})")
    """
    try:
        url = f"{FINNHUB_BASE_URL}/stock/price-target"
        params = {
            'symbol': symbol,
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "symbol": symbol}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "symbol": symbol}


def get_rating_changes(symbol: str = 'AAPL', from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict]:
    """
    Get recent analyst rating changes (upgrades/downgrades).
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
        from_date: Start date in YYYY-MM-DD format (optional)
        to_date: End date in YYYY-MM-DD format (optional)
    
    Returns:
        List of dicts with keys: symbol, gradeTime, company, fromGrade, toGrade, action
    
    Example:
        >>> changes = get_rating_changes('AAPL')
        >>> for change in changes[:3]:
        ...     print(f"{change['company']}: {change['fromGrade']} → {change['toGrade']}")
    """
    try:
        url = f"{FINNHUB_BASE_URL}/stock/upgrade-downgrade"
        params = {
            'symbol': symbol,
            'token': FINNHUB_API_KEY
        }
        
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        return [{"error": str(e), "symbol": symbol}]
    except Exception as e:
        return [{"error": f"Unexpected error: {str(e)}", "symbol": symbol}]


if __name__ == "__main__":
    print("Finnhub Earnings Estimates API Module")
    print("=" * 50)
    
    # Test EPS estimates
    print("\n1. EPS Estimates (AAPL):")
    eps = get_eps_estimates('AAPL')
    if 'error' not in eps and 'data' in eps and len(eps['data']) > 0:
        print(f"   Next period EPS: ${eps['data'][0].get('epsAvg', 'N/A')}")
    else:
        print(f"   {eps}")
    
    # Test price targets
    print("\n2. Price Targets (AAPL):")
    targets = get_price_targets('AAPL')
    if 'error' not in targets and 'targetMean' in targets:
        print(f"   Mean target: ${targets.get('targetMean', 'N/A')}")
        print(f"   Range: ${targets.get('targetLow', 'N/A')} - ${targets.get('targetHigh', 'N/A')}")
    else:
        print(f"   {targets}")

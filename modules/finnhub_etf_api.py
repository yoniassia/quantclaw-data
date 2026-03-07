#!/usr/bin/env python3
"""
Finnhub ETF API — ETF Holdings, Profiles & Exposure Analysis

Provides comprehensive ETF data including:
- ETF holdings and portfolio composition
- ETF profile metadata (expense ratios, AUM, etc.)
- Sector exposure breakdowns
- Country/geographic exposure
- ETF search capabilities

Source: https://finnhub.io/docs/api/etf-holdings
Category: ETF & Fund Flows
Free tier: True (60 API calls per minute with free key)
Update frequency: Daily for holdings, real-time for quotes
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Finnhub API Configuration
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")

# ========== ETF HOLDINGS ==========

def get_etf_holdings(symbol: str) -> Dict[str, Any]:
    """
    Get ETF holdings and portfolio composition.
    
    Args:
        symbol: ETF ticker symbol (e.g., 'SPY', 'QQQ')
        
    Returns:
        Dict with ETF holdings data including:
        - symbol: ETF symbol
        - atDate: Holdings as-of date
        - holdings: List of holdings with weights and shares
        
    Example:
        >>> holdings = get_etf_holdings('SPY')
        >>> print(f"SPY has {len(holdings.get('holdings', []))} holdings")
    """
    if not FINNHUB_API_KEY:
        return {
            "error": "FINNHUB_API_KEY not set in .env",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        url = f"{FINNHUB_BASE_URL}/etf/holdings"
        params = {
            "symbol": symbol.upper(),
            "token": FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        data["_fetched_at"] = datetime.utcnow().isoformat()
        data["_symbol"] = symbol.upper()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {
            "error": f"API request failed: {str(e)}",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }
    except json.JSONDecodeError as e:
        return {
            "error": f"Invalid JSON response: {str(e)}",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }


# ========== ETF PROFILE ==========

def get_etf_profile(symbol: str) -> Dict[str, Any]:
    """
    Get ETF profile metadata including expense ratio, AUM, description.
    
    Args:
        symbol: ETF ticker symbol (e.g., 'SPY', 'QQQ')
        
    Returns:
        Dict with ETF profile data including:
        - symbol: ETF symbol
        - name: Full ETF name
        - description: ETF description
        - expenseRatio: Annual expense ratio
        - aum: Assets under management
        - etfCompany: Issuing company
        
    Example:
        >>> profile = get_etf_profile('QQQ')
        >>> print(f"{profile.get('name')}: {profile.get('description')}")
    """
    if not FINNHUB_API_KEY:
        return {
            "error": "FINNHUB_API_KEY not set in .env",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        url = f"{FINNHUB_BASE_URL}/etf/profile"
        params = {
            "symbol": symbol.upper(),
            "token": FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        data["_fetched_at"] = datetime.utcnow().isoformat()
        data["_symbol"] = symbol.upper()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {
            "error": f"API request failed: {str(e)}",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }
    except json.JSONDecodeError as e:
        return {
            "error": f"Invalid JSON response: {str(e)}",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }


# ========== ETF SECTOR EXPOSURE ==========

def get_etf_sector_exposure(symbol: str) -> Dict[str, Any]:
    """
    Get ETF sector exposure breakdown.
    
    Args:
        symbol: ETF ticker symbol (e.g., 'SPY', 'XLK')
        
    Returns:
        Dict with sector exposure data including:
        - symbol: ETF symbol
        - sectorExposure: List of sectors with exposure percentages
        
    Example:
        >>> sectors = get_etf_sector_exposure('SPY')
        >>> for sector in sectors.get('sectorExposure', []):
        ...     print(f"{sector['sector']}: {sector['exposure']}%")
    """
    if not FINNHUB_API_KEY:
        return {
            "error": "FINNHUB_API_KEY not set in .env",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        url = f"{FINNHUB_BASE_URL}/etf/sector"
        params = {
            "symbol": symbol.upper(),
            "token": FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        data["_fetched_at"] = datetime.utcnow().isoformat()
        data["_symbol"] = symbol.upper()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {
            "error": f"API request failed: {str(e)}",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }
    except json.JSONDecodeError as e:
        return {
            "error": f"Invalid JSON response: {str(e)}",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }


# ========== ETF COUNTRY EXPOSURE ==========

def get_etf_country_exposure(symbol: str) -> Dict[str, Any]:
    """
    Get ETF country/geographic exposure breakdown.
    
    Args:
        symbol: ETF ticker symbol (e.g., 'SPY', 'EEM')
        
    Returns:
        Dict with country exposure data including:
        - symbol: ETF symbol
        - countryExposure: List of countries with exposure percentages
        
    Example:
        >>> countries = get_etf_country_exposure('EEM')
        >>> for country in countries.get('countryExposure', []):
        ...     print(f"{country['country']}: {country['exposure']}%")
    """
    if not FINNHUB_API_KEY:
        return {
            "error": "FINNHUB_API_KEY not set in .env",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        url = f"{FINNHUB_BASE_URL}/etf/country"
        params = {
            "symbol": symbol.upper(),
            "token": FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        data["_fetched_at"] = datetime.utcnow().isoformat()
        data["_symbol"] = symbol.upper()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {
            "error": f"API request failed: {str(e)}",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }
    except json.JSONDecodeError as e:
        return {
            "error": f"Invalid JSON response: {str(e)}",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }


# ========== ETF SEARCH ==========

def search_etfs(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for ETFs by name, symbol, or description.
    
    Note: This is a utility function that searches common ETFs.
    For production use, integrate with Finnhub symbol search API.
    
    Args:
        query: Search query (symbol or name fragment)
        limit: Maximum number of results to return
        
    Returns:
        List of matching ETF symbols and names
        
    Example:
        >>> results = search_etfs('tech')
        >>> for etf in results:
        ...     print(f"{etf['symbol']}: {etf['name']}")
    """
    # Common ETFs registry for basic search functionality
    # In production, use Finnhub symbol search API endpoint
    common_etfs = [
        {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust"},
        {"symbol": "QQQ", "name": "Invesco QQQ Trust"},
        {"symbol": "IWM", "name": "iShares Russell 2000 ETF"},
        {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF"},
        {"symbol": "VOO", "name": "Vanguard S&P 500 ETF"},
        {"symbol": "DIA", "name": "SPDR Dow Jones Industrial Average ETF"},
        {"symbol": "EEM", "name": "iShares MSCI Emerging Markets ETF"},
        {"symbol": "GLD", "name": "SPDR Gold Trust"},
        {"symbol": "TLT", "name": "iShares 20+ Year Treasury Bond ETF"},
        {"symbol": "XLF", "name": "Financial Select Sector SPDR Fund"},
        {"symbol": "XLE", "name": "Energy Select Sector SPDR Fund"},
        {"symbol": "XLK", "name": "Technology Select Sector SPDR Fund"},
        {"symbol": "XLV", "name": "Health Care Select Sector SPDR Fund"},
        {"symbol": "XLP", "name": "Consumer Staples Select Sector SPDR Fund"},
        {"symbol": "XLY", "name": "Consumer Discretionary Select Sector SPDR Fund"},
        {"symbol": "XLI", "name": "Industrial Select Sector SPDR Fund"},
        {"symbol": "XLU", "name": "Utilities Select Sector SPDR Fund"},
        {"symbol": "XLRE", "name": "Real Estate Select Sector SPDR Fund"},
        {"symbol": "XLB", "name": "Materials Select Sector SPDR Fund"},
        {"symbol": "VTV", "name": "Vanguard Value ETF"},
        {"symbol": "VUG", "name": "Vanguard Growth ETF"},
        {"symbol": "VIG", "name": "Vanguard Dividend Appreciation ETF"},
        {"symbol": "VYM", "name": "Vanguard High Dividend Yield ETF"},
        {"symbol": "ARKK", "name": "ARK Innovation ETF"},
        {"symbol": "ARKG", "name": "ARK Genomic Revolution ETF"},
        {"symbol": "ARKW", "name": "ARK Next Generation Internet ETF"},
        {"symbol": "ICLN", "name": "iShares Global Clean Energy ETF"},
        {"symbol": "TAN", "name": "Invesco Solar ETF"},
        {"symbol": "LIT", "name": "Global X Lithium & Battery Tech ETF"},
        {"symbol": "SOXX", "name": "iShares Semiconductor ETF"},
    ]
    
    query_lower = query.lower()
    results = []
    
    for etf in common_etfs:
        if (query_lower in etf["symbol"].lower() or 
            query_lower in etf["name"].lower()):
            results.append(etf)
            if len(results) >= limit:
                break
    
    return results


# ========== UTILITY FUNCTIONS ==========

def get_etf_summary(symbol: str) -> Dict[str, Any]:
    """
    Get comprehensive ETF summary combining profile, holdings count, and exposures.
    
    Args:
        symbol: ETF ticker symbol
        
    Returns:
        Dict with combined ETF data from multiple endpoints
        
    Example:
        >>> summary = get_etf_summary('SPY')
        >>> print(json.dumps(summary, indent=2))
    """
    profile = get_etf_profile(symbol)
    holdings = get_etf_holdings(symbol)
    sectors = get_etf_sector_exposure(symbol)
    countries = get_etf_country_exposure(symbol)
    
    return {
        "symbol": symbol.upper(),
        "profile": profile,
        "holdings_count": len(holdings.get("holdings", [])),
        "top_holdings": holdings.get("holdings", [])[:10] if "holdings" in holdings else [],
        "sector_exposure": sectors.get("sectorExposure", []),
        "country_exposure": countries.get("countryExposure", []),
        "fetched_at": datetime.utcnow().isoformat()
    }


# ========== MODULE INFO ==========

def module_info() -> Dict[str, Any]:
    """Return module metadata and available functions."""
    return {
        "module": "finnhub_etf_api",
        "version": "1.0.0",
        "source": "https://finnhub.io/docs/api/etf-holdings",
        "category": "ETF & Fund Flows",
        "free_tier": True,
        "rate_limit": "60 calls/minute",
        "api_key_set": bool(FINNHUB_API_KEY),
        "functions": [
            "get_etf_holdings",
            "get_etf_profile",
            "get_etf_sector_exposure",
            "get_etf_country_exposure",
            "search_etfs",
            "get_etf_summary"
        ],
        "author": "QuantClaw Data NightBuilder",
        "generated": "2026-03-06"
    }


if __name__ == "__main__":
    print(json.dumps(module_info(), indent=2))

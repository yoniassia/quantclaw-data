#!/usr/bin/env python3
"""
Finnhub ETF Flows API — ETF Holdings, Profile & Composition Analysis

Provides real-time and historical ETF data including:
- Holdings composition and changes
- ETF profile (expense ratio, AUM, inception date)
- Sector exposure breakdown
- Country/region exposure

Source: https://finnhub.io/docs/api/etf-flows
Category: ETF & Fund Flows
Free tier: True - 60 calls per minute, API key required
Author: QuantClaw Data NightBuilder
Phase: NightBuilder-105
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Finnhub API Configuration
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")


def get_etf_holdings(symbol: str) -> Dict:
    """
    Get ETF holdings/composition for a given symbol.
    
    Args:
        symbol: ETF ticker symbol (e.g., 'SPY', 'QQQ')
    
    Returns:
        Dict with 'data' key containing holdings list on success,
        or 'error' key with error message on failure.
    
    Example:
        >>> result = get_etf_holdings('SPY')
        >>> if 'data' in result:
        ...     print(f"Found {len(result['data'])} holdings")
    """
    if not FINNHUB_API_KEY:
        return {"error": "FINNHUB_API_KEY not found in environment"}
    
    try:
        url = f"{FINNHUB_BASE_URL}/etf/holdings"
        params = {
            "symbol": symbol.upper(),
            "token": FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Finnhub returns {"holdings": [...], "symbol": "SPY", ...}
        if isinstance(data, dict) and "holdings" in data:
            return {
                "data": data,
                "symbol": symbol.upper(),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {"data": data}
            
    except requests.exceptions.Timeout:
        return {"error": f"Request timeout for {symbol}"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error for {symbol}: {e.response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed for {symbol}: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": f"Invalid JSON response for {symbol}"}
    except Exception as e:
        return {"error": f"Unexpected error for {symbol}: {str(e)}"}


def get_etf_profile(symbol: str) -> Dict:
    """
    Get ETF profile information including expense ratio, AUM, inception date.
    
    Args:
        symbol: ETF ticker symbol (e.g., 'SPY', 'QQQ')
    
    Returns:
        Dict with 'data' key containing profile info on success,
        or 'error' key with error message on failure.
    
    Example:
        >>> result = get_etf_profile('SPY')
        >>> if 'data' in result:
        ...     print(f"Expense ratio: {result['data'].get('expenseRatio', 'N/A')}")
    """
    if not FINNHUB_API_KEY:
        return {"error": "FINNHUB_API_KEY not found in environment"}
    
    try:
        url = f"{FINNHUB_BASE_URL}/etf/profile"
        params = {
            "symbol": symbol.upper(),
            "token": FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "data": data,
            "symbol": symbol.upper(),
            "timestamp": datetime.utcnow().isoformat()
        }
            
    except requests.exceptions.Timeout:
        return {"error": f"Request timeout for {symbol}"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error for {symbol}: {e.response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed for {symbol}: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": f"Invalid JSON response for {symbol}"}
    except Exception as e:
        return {"error": f"Unexpected error for {symbol}: {str(e)}"}


def get_etf_sector_exposure(symbol: str) -> Dict:
    """
    Get ETF sector exposure breakdown.
    
    Args:
        symbol: ETF ticker symbol (e.g., 'SPY', 'QQQ')
    
    Returns:
        Dict with 'data' key containing sector exposure on success,
        or 'error' key with error message on failure.
    
    Example:
        >>> result = get_etf_sector_exposure('SPY')
        >>> if 'data' in result:
        ...     for sector in result['data']:
        ...         print(f"{sector['sector']}: {sector['exposure']}%")
    """
    if not FINNHUB_API_KEY:
        return {"error": "FINNHUB_API_KEY not found in environment"}
    
    try:
        url = f"{FINNHUB_BASE_URL}/etf/sector"
        params = {
            "symbol": symbol.upper(),
            "token": FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Finnhub returns {"sectorExposure": [...], "symbol": "SPY"}
        if isinstance(data, dict) and "sectorExposure" in data:
            return {
                "data": data,
                "symbol": symbol.upper(),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {"data": data}
            
    except requests.exceptions.Timeout:
        return {"error": f"Request timeout for {symbol}"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error for {symbol}: {e.response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed for {symbol}: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": f"Invalid JSON response for {symbol}"}
    except Exception as e:
        return {"error": f"Unexpected error for {symbol}: {str(e)}"}


def get_etf_country_exposure(symbol: str) -> Dict:
    """
    Get ETF country/region exposure breakdown.
    
    Args:
        symbol: ETF ticker symbol (e.g., 'SPY', 'QQQ')
    
    Returns:
        Dict with 'data' key containing country exposure on success,
        or 'error' key with error message on failure.
    
    Example:
        >>> result = get_etf_country_exposure('SPY')
        >>> if 'data' in result:
        ...     for country in result['data']:
        ...         print(f"{country['country']}: {country['exposure']}%")
    """
    if not FINNHUB_API_KEY:
        return {"error": "FINNHUB_API_KEY not found in environment"}
    
    try:
        url = f"{FINNHUB_BASE_URL}/etf/country"
        params = {
            "symbol": symbol.upper(),
            "token": FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Finnhub returns {"countryExposure": [...], "symbol": "SPY"}
        if isinstance(data, dict) and "countryExposure" in data:
            return {
                "data": data,
                "symbol": symbol.upper(),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {"data": data}
            
    except requests.exceptions.Timeout:
        return {"error": f"Request timeout for {symbol}"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error for {symbol}: {e.response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed for {symbol}: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": f"Invalid JSON response for {symbol}"}
    except Exception as e:
        return {"error": f"Unexpected error for {symbol}: {str(e)}"}


if __name__ == "__main__":
    # Quick module test
    print(json.dumps({
        "module": "finnhub_etf_flows_api",
        "status": "ready",
        "functions": [
            "get_etf_holdings",
            "get_etf_profile",
            "get_etf_sector_exposure",
            "get_etf_country_exposure"
        ],
        "api_key_configured": bool(FINNHUB_API_KEY),
        "source": "https://finnhub.io/docs/api/etf-flows"
    }, indent=2))

#!/usr/bin/env python3
"""
OpenFIGI Identifier Mapping Module

Maps financial security identifiers across different systems (FIGI, ISIN, CUSIP, SEDOL, ticker).
Bloomberg-backed service for standardized security identification.

Functions:
- map_ticker_to_figi() — Map ticker symbol to FIGI identifiers
- map_isin_to_figi() — Map ISIN to FIGI identifiers
- batch_map() — Batch mapping of multiple identifiers
- get_figi_details() — Get detailed information for a FIGI

Source: https://api.openfigi.com/v3/mapping
Category: Security Identifiers
Free tier: True (10 requests/min, 100 IDs per request, no API key required)
Author: QuantClaw Data NightBuilder
"""

import json
import requests
from typing import Dict, List, Optional, Union
from datetime import datetime

# OpenFIGI API Configuration
OPENFIGI_BASE_URL = "https://api.openfigi.com/v3"
OPENFIGI_MAPPING_ENDPOINT = f"{OPENFIGI_BASE_URL}/mapping"

# Rate limits (free tier)
RATE_LIMIT_PER_MIN = 10
MAX_IDS_PER_REQUEST = 100


def map_ticker_to_figi(
    ticker: str,
    exchange_code: Optional[str] = None,
    security_type: Optional[str] = None
) -> Dict:
    """
    Map ticker symbol to FIGI identifiers
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        exchange_code: Optional exchange code (e.g., 'US', 'LN', 'TK')
        security_type: Optional security type (e.g., 'Common Stock', 'ADR')
    
    Returns:
        Dict with FIGI mapping results including multiple identifier types
    
    Example:
        >>> result = map_ticker_to_figi('AAPL', exchange_code='US')
        >>> print(result['data'][0]['figi'])
        'BBG000B9XRY4'
    """
    try:
        payload = {
            "idType": "TICKER",
            "idValue": ticker.upper()
        }
        
        if exchange_code:
            payload["exchCode"] = exchange_code.upper()
        
        if security_type:
            payload["securityType"] = security_type
        
        response = requests.post(
            OPENFIGI_MAPPING_ENDPOINT,
            json=[payload],
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        
        # API returns array, first element is our result
        if not data or len(data) == 0:
            return {
                "success": False,
                "error": "No response from API",
                "ticker": ticker
            }
        
        result = data[0]
        
        # Check for errors in response
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "ticker": ticker
            }
        
        # Check if we got data
        if "data" not in result or len(result["data"]) == 0:
            return {
                "success": False,
                "error": "No mapping found",
                "ticker": ticker,
                "exchange_code": exchange_code
            }
        
        # Extract all identifiers from first match
        first_match = result["data"][0]
        
        return {
            "success": True,
            "ticker": ticker,
            "exchange_code": exchange_code,
            "figi": first_match.get("figi"),
            "composite_figi": first_match.get("compositeFIGI"),
            "share_class_figi": first_match.get("shareClassFIGI"),
            "security_type": first_match.get("securityType"),
            "market_sector": first_match.get("marketSector"),
            "name": first_match.get("name"),
            "exchange_name": first_match.get("exchCode"),
            "identifiers": {
                "isin": first_match.get("securityDescription"),
                "cusip": first_match.get("securityDescription2"),
                "sedol": first_match.get("securityDescription3")
            },
            "total_matches": len(result["data"]),
            "all_matches": result["data"],
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "ticker": ticker
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "ticker": ticker
        }


def map_isin_to_figi(isin: str) -> Dict:
    """
    Map ISIN (International Securities Identification Number) to FIGI
    
    Args:
        isin: ISIN code (e.g., 'US0378331005' for Apple)
    
    Returns:
        Dict with FIGI mapping results
    
    Example:
        >>> result = map_isin_to_figi('US0378331005')
        >>> print(result['figi'])
        'BBG000B9XRY4'
    """
    try:
        payload = {
            "idType": "ID_ISIN",
            "idValue": isin.upper()
        }
        
        response = requests.post(
            OPENFIGI_MAPPING_ENDPOINT,
            json=[payload],
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        
        if not data or len(data) == 0:
            return {
                "success": False,
                "error": "No response from API",
                "isin": isin
            }
        
        result = data[0]
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "isin": isin
            }
        
        if "data" not in result or len(result["data"]) == 0:
            return {
                "success": False,
                "error": "No mapping found",
                "isin": isin
            }
        
        first_match = result["data"][0]
        
        return {
            "success": True,
            "isin": isin,
            "figi": first_match.get("figi"),
            "composite_figi": first_match.get("compositeFIGI"),
            "name": first_match.get("name"),
            "ticker": first_match.get("ticker"),
            "exchange_code": first_match.get("exchCode"),
            "security_type": first_match.get("securityType"),
            "market_sector": first_match.get("marketSector"),
            "total_matches": len(result["data"]),
            "all_matches": result["data"],
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "isin": isin
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "isin": isin
        }


def batch_map(identifiers: List[Dict[str, str]]) -> Dict:
    """
    Batch mapping of multiple identifiers in a single API call
    
    Args:
        identifiers: List of identifier dicts, each containing:
            - idType: Type of identifier ('TICKER', 'ID_ISIN', 'ID_CUSIP', etc.)
            - idValue: The identifier value
            - exchCode: (optional) Exchange code
            - securityType: (optional) Security type
    
    Returns:
        Dict with results for all identifiers
    
    Example:
        >>> ids = [
        ...     {"idType": "TICKER", "idValue": "AAPL", "exchCode": "US"},
        ...     {"idType": "TICKER", "idValue": "MSFT", "exchCode": "US"}
        ... ]
        >>> result = batch_map(ids)
        >>> print(len(result['results']))
        2
    """
    try:
        # Validate input
        if not identifiers or not isinstance(identifiers, list):
            return {
                "success": False,
                "error": "identifiers must be a non-empty list"
            }
        
        # Check batch size limit
        if len(identifiers) > MAX_IDS_PER_REQUEST:
            return {
                "success": False,
                "error": f"Batch size {len(identifiers)} exceeds max {MAX_IDS_PER_REQUEST}",
                "max_allowed": MAX_IDS_PER_REQUEST
            }
        
        # Ensure all identifiers have required fields
        for idx, id_obj in enumerate(identifiers):
            if "idType" not in id_obj or "idValue" not in id_obj:
                return {
                    "success": False,
                    "error": f"Identifier at index {idx} missing required fields (idType, idValue)"
                }
        
        response = requests.post(
            OPENFIGI_MAPPING_ENDPOINT,
            json=identifiers,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        
        if not data or not isinstance(data, list):
            return {
                "success": False,
                "error": "Invalid response format from API"
            }
        
        # Process all results
        results = []
        success_count = 0
        error_count = 0
        
        for idx, result in enumerate(data):
            original_request = identifiers[idx]
            
            if "error" in result:
                results.append({
                    "success": False,
                    "error": result["error"],
                    "request": original_request
                })
                error_count += 1
            elif "data" in result and len(result["data"]) > 0:
                first_match = result["data"][0]
                results.append({
                    "success": True,
                    "request": original_request,
                    "figi": first_match.get("figi"),
                    "composite_figi": first_match.get("compositeFIGI"),
                    "name": first_match.get("name"),
                    "ticker": first_match.get("ticker"),
                    "exchange_code": first_match.get("exchCode"),
                    "security_type": first_match.get("securityType"),
                    "total_matches": len(result["data"]),
                    "all_matches": result["data"]
                })
                success_count += 1
            else:
                results.append({
                    "success": False,
                    "error": "No mapping found",
                    "request": original_request
                })
                error_count += 1
        
        return {
            "success": True,
            "total_requested": len(identifiers),
            "success_count": success_count,
            "error_count": error_count,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "total_requested": len(identifiers) if identifiers else 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "total_requested": len(identifiers) if identifiers else 0
        }


def get_figi_details(figi_id: str) -> Dict:
    """
    Get detailed information for a specific FIGI identifier
    Uses reverse mapping to retrieve full security details
    
    Args:
        figi_id: FIGI identifier (e.g., 'BBG000B9XRY4')
    
    Returns:
        Dict with security details
    
    Example:
        >>> result = get_figi_details('BBG000B9XRY4')
        >>> print(result['name'])
        'APPLE INC'
    """
    try:
        payload = {
            "idType": "ID_BB_GLOBAL",
            "idValue": figi_id.upper()
        }
        
        response = requests.post(
            OPENFIGI_MAPPING_ENDPOINT,
            json=[payload],
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        
        if not data or len(data) == 0:
            return {
                "success": False,
                "error": "No response from API",
                "figi": figi_id
            }
        
        result = data[0]
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "figi": figi_id
            }
        
        if "data" not in result or len(result["data"]) == 0:
            return {
                "success": False,
                "error": "No details found",
                "figi": figi_id
            }
        
        details = result["data"][0]
        
        return {
            "success": True,
            "figi": figi_id,
            "composite_figi": details.get("compositeFIGI"),
            "share_class_figi": details.get("shareClassFIGI"),
            "name": details.get("name"),
            "ticker": details.get("ticker"),
            "exchange_code": details.get("exchCode"),
            "exchange_name": details.get("name"),
            "security_type": details.get("securityType"),
            "security_type_2": details.get("securityType2"),
            "market_sector": details.get("marketSector"),
            "metadata": details,
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "figi": figi_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "figi": figi_id
        }


def get_module_info() -> Dict:
    """
    Get module information and usage statistics
    
    Returns:
        Dict with module metadata
    """
    return {
        "module": "openfigi_fundamentals_feed",
        "description": "OpenFIGI security identifier mapping",
        "source": "https://api.openfigi.com/v3/mapping",
        "functions": [
            "map_ticker_to_figi",
            "map_isin_to_figi",
            "batch_map",
            "get_figi_details"
        ],
        "rate_limits": {
            "requests_per_minute": RATE_LIMIT_PER_MIN,
            "max_ids_per_request": MAX_IDS_PER_REQUEST
        },
        "free_tier": True,
        "api_key_required": False,
        "supported_id_types": [
            "TICKER",
            "ID_ISIN",
            "ID_BB_GLOBAL",
            "ID_CUSIP",
            "ID_SEDOL",
            "ID_BB_UNIQUE",
            "ID_COMMON",
            "ID_WERTPAPIER"
        ]
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("OpenFIGI Identifier Mapping Module")
    print("=" * 60)
    
    # Show module info
    info = get_module_info()
    print("\n" + json.dumps(info, indent=2))
    
    print("\n" + "=" * 60)
    print("Example: Map ticker AAPL to FIGI")
    print("=" * 60)
    result = map_ticker_to_figi("AAPL", exchange_code="US")
    print(json.dumps(result, indent=2))

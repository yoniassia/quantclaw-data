"""
OpenFIGI API - Bloomberg-backed security identifier mapping
Source: https://www.openfigi.com/api
Category: Reference Data
Frequency: On-demand
Rate Limit: 10 req/min, 100 identifiers per request (free tier, no API key)

Map tickers, ISINs, CUSIPs to FIGI codes and security metadata.
Essential infrastructure for cross-referencing data across sources.
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

# Constants
BASE_URL = "https://api.openfigi.com/v3/mapping"
HEADERS = {
    "Content-Type": "application/json"
}
TIMEOUT = 10
MAX_BATCH_SIZE = 100


def _post_mapping(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Internal function to POST mapping requests to OpenFIGI API.
    
    Args:
        jobs: List of mapping job dictionaries
        
    Returns:
        List of result dictionaries from API
        
    Raises:
        Exception: On API errors or network issues
    """
    try:
        response = requests.post(
            BASE_URL,
            headers=HEADERS,
            json=jobs,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"OpenFIGI API error: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse OpenFIGI response: {str(e)}")


def _extract_result(api_response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract first valid result from API response."""
    if not api_response:
        return None
    if "error" in api_response:
        return None
    if "data" in api_response and len(api_response["data"]) > 0:
        return api_response["data"][0]
    return None


def map_ticker(ticker: str, exchange_code: Optional[str] = None) -> Dict[str, Any]:
    """
    Map a ticker symbol to FIGI and security metadata.
    
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT")
        exchange_code: Optional exchange MIC code (e.g., "US", "UN" for NASDAQ)
        
    Returns:
        Dictionary containing:
            - figi: The FIGI identifier
            - name: Security name
            - ticker: Ticker symbol
            - exchCode: Exchange code
            - marketSector: Market sector (Equity, Curncy, etc.)
            - securityType: Security type
            - securityDescription: Full security description
            
    Example:
        >>> result = map_ticker("AAPL")
        >>> print(result['figi'], result['name'])
    """
    job = {"idType": "TICKER", "idValue": ticker}
    if exchange_code:
        job["exchCode"] = exchange_code
    
    try:
        results = _post_mapping([job])
        data = _extract_result(results[0] if results else None)
        
        if not data:
            return {
                "error": "No mapping found",
                "ticker": ticker,
                "exchange_code": exchange_code
            }
        
        return {
            "figi": data.get("figi"),
            "name": data.get("name"),
            "ticker": data.get("ticker"),
            "exchCode": data.get("exchCode"),
            "marketSector": data.get("marketSector"),
            "securityType": data.get("securityType"),
            "securityDescription": data.get("securityDescription"),
            "compositeFIGI": data.get("compositeFIGI"),
            "shareClassFIGI": data.get("shareClassFIGI")
        }
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def map_tickers(tickers_list: List[str]) -> List[Dict[str, Any]]:
    """
    Batch map multiple tickers to FIGI and metadata.
    
    Args:
        tickers_list: List of ticker symbols (max 100)
        
    Returns:
        List of dictionaries with mapping results for each ticker
        
    Example:
        >>> results = map_tickers(["AAPL", "MSFT", "TSLA"])
        >>> for r in results: print(r['ticker'], r.get('figi'))
    """
    if len(tickers_list) > MAX_BATCH_SIZE:
        raise ValueError(f"Maximum batch size is {MAX_BATCH_SIZE} tickers")
    
    jobs = [{"idType": "TICKER", "idValue": ticker} for ticker in tickers_list]
    
    try:
        results = _post_mapping(jobs)
        output = []
        
        for i, ticker in enumerate(tickers_list):
            if i < len(results):
                data = _extract_result(results[i])
                if data:
                    output.append({
                        "ticker": ticker,
                        "figi": data.get("figi"),
                        "name": data.get("name"),
                        "exchCode": data.get("exchCode"),
                        "marketSector": data.get("marketSector"),
                        "securityType": data.get("securityType"),
                        "compositeFIGI": data.get("compositeFIGI")
                    })
                else:
                    output.append({"ticker": ticker, "error": "No mapping found"})
            else:
                output.append({"ticker": ticker, "error": "No response"})
        
        return output
    except Exception as e:
        return [{"ticker": t, "error": str(e)} for t in tickers_list]


def get_figi(ticker: str) -> Optional[str]:
    """
    Get just the FIGI code for a ticker (simplified interface).
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        FIGI string or None if not found
        
    Example:
        >>> figi = get_figi("AAPL")
        >>> print(figi)  # BBG000B9XRY4
    """
    result = map_ticker(ticker)
    return result.get("figi") if "error" not in result else None


def map_isin(isin: str) -> Dict[str, Any]:
    """
    Map an ISIN to FIGI and security metadata.
    
    Args:
        isin: International Securities Identification Number
        
    Returns:
        Dictionary with FIGI and security details
        
    Example:
        >>> result = map_isin("US0378331005")  # Apple
        >>> print(result['name'])
    """
    job = {"idType": "ID_ISIN", "idValue": isin}
    
    try:
        results = _post_mapping([job])
        data = _extract_result(results[0] if results else None)
        
        if not data:
            return {"error": "No mapping found", "isin": isin}
        
        return {
            "isin": isin,
            "figi": data.get("figi"),
            "name": data.get("name"),
            "ticker": data.get("ticker"),
            "exchCode": data.get("exchCode"),
            "marketSector": data.get("marketSector"),
            "securityType": data.get("securityType"),
            "compositeFIGI": data.get("compositeFIGI")
        }
    except Exception as e:
        return {"error": str(e), "isin": isin}


def map_cusip(cusip: str) -> Dict[str, Any]:
    """
    Map a CUSIP to FIGI and security metadata.
    
    Args:
        cusip: Committee on Uniform Securities Identification Procedures number
        
    Returns:
        Dictionary with FIGI and security details
        
    Example:
        >>> result = map_cusip("037833100")  # Apple
        >>> print(result['name'])
    """
    job = {"idType": "ID_CUSIP", "idValue": cusip}
    
    try:
        results = _post_mapping([job])
        data = _extract_result(results[0] if results else None)
        
        if not data:
            return {"error": "No mapping found", "cusip": cusip}
        
        return {
            "cusip": cusip,
            "figi": data.get("figi"),
            "name": data.get("name"),
            "ticker": data.get("ticker"),
            "exchCode": data.get("exchCode"),
            "marketSector": data.get("marketSector"),
            "securityType": data.get("securityType"),
            "compositeFIGI": data.get("compositeFIGI")
        }
    except Exception as e:
        return {"error": str(e), "cusip": cusip}


def search_securities(query: str) -> List[Dict[str, Any]]:
    """
    Search for securities by name or partial identifier.
    Note: This uses ticker search - for more advanced search, use the mapping API with partial matches.
    
    Args:
        query: Search query (company name or partial ticker)
        
    Returns:
        List of matching securities with metadata
        
    Example:
        >>> results = search_securities("Apple")
        >>> for r in results: print(r['ticker'], r['name'])
    """
    # OpenFIGI doesn't have a dedicated search endpoint in the free tier
    # We use the mapping endpoint with the query as a ticker
    # This is a best-effort implementation
    try:
        result = map_ticker(query)
        if "error" not in result and result.get("figi"):
            return [result]
        return []
    except Exception as e:
        return []


if __name__ == "__main__":
    # Quick test
    print("Testing OpenFIGI module...")
    result = map_ticker("AAPL")
    print(f"AAPL FIGI: {result.get('figi')}")
    print(f"Name: {result.get('name')}")

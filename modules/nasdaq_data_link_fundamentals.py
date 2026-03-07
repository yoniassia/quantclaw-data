#!/usr/bin/env python3
"""
Nasdaq Data Link Fundamentals Module
Company fundamentals, earnings estimates, and financial ratios from Nasdaq Data Link (formerly Quandl).
Uses free tier datasets including Sharadar SF1, Zacks estimates, and other providers.
"""

import os
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

BASE_URL = "https://data.nasdaq.com/api/v3"

def _get_api_key() -> Optional[str]:
    """Get API key from environment variables"""
    return os.environ.get("NASDAQ_DATA_LINK_API_KEY") or os.environ.get("QUANDL_API_KEY")

def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Make request to Nasdaq Data Link API with error handling
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        
    Returns:
        Response data as dictionary
    """
    api_key = _get_api_key()
    if params is None:
        params = {}
    
    if api_key:
        params["api_key"] = api_key
    
    url = f"{BASE_URL}/{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"error": "Dataset not found", "status_code": 404}
        elif e.response.status_code == 429:
            return {"error": "Rate limit exceeded", "status_code": 429}
        else:
            return {"error": f"HTTP error: {e}", "status_code": e.response.status_code}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "status_code": None}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "status_code": None}

def get_company_fundamentals(ticker: str, dimension: str = "MRQ") -> Dict[str, Any]:
    """
    Get company fundamental data from Sharadar SF1 dataset
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        dimension: Time dimension - MRQ (Most Recent Quarter), MRT (Most Recent Trailing 12 Months), ARQ (As Reported Quarterly), ART (As Reported Trailing 12 Months)
        
    Returns:
        Dictionary with fundamental metrics including revenue, EPS, margins, etc.
    """
    # SF1 database uses format: SF1/{TICKER}_{DIMENSION}
    dataset_code = f"SF1/{ticker}_{dimension}"
    endpoint = f"datasets/{dataset_code}.json"
    
    result = _make_request(endpoint)
    
    if "error" in result:
        return result
    
    try:
        dataset = result.get("dataset", {})
        data = dataset.get("data", [])
        column_names = dataset.get("column_names", [])
        
        if not data:
            return {"error": "No data available", "ticker": ticker}
        
        # Get most recent data point
        latest = data[0]
        
        # Create dict mapping column names to values
        fundamentals = dict(zip(column_names, latest))
        
        return {
            "ticker": ticker,
            "dimension": dimension,
            "date": fundamentals.get("Date", fundamentals.get("date")),
            "data": fundamentals,
            "source": "Nasdaq Data Link (Sharadar SF1)"
        }
    except Exception as e:
        return {"error": f"Failed to parse response: {str(e)}", "ticker": ticker}

def get_earnings_per_share(ticker: str) -> Dict[str, Any]:
    """
    Get earnings per share (EPS) data
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with EPS data including historical values
    """
    # Try SF1 dataset for EPS
    dataset_code = f"SF1/{ticker}_EPS_MRQ"
    endpoint = f"datasets/{dataset_code}.json"
    
    result = _make_request(endpoint)
    
    if "error" in result:
        return result
    
    try:
        dataset = result.get("dataset", {})
        data = dataset.get("data", [])
        
        if not data:
            return {"error": "No EPS data available", "ticker": ticker}
        
        return {
            "ticker": ticker,
            "metric": "EPS",
            "latest_value": data[0][1] if len(data[0]) > 1 else None,
            "latest_date": data[0][0] if len(data[0]) > 0 else None,
            "historical_data": data[:10],  # Last 10 data points
            "source": "Nasdaq Data Link"
        }
    except Exception as e:
        return {"error": f"Failed to parse EPS data: {str(e)}", "ticker": ticker}

def get_revenue(ticker: str, dimension: str = "MRQ") -> Dict[str, Any]:
    """
    Get company revenue data
    
    Args:
        ticker: Stock ticker symbol
        dimension: Time dimension (MRQ, MRT, ARQ, ART)
        
    Returns:
        Dictionary with revenue data
    """
    dataset_code = f"SF1/{ticker}_REVENUE_{dimension}"
    endpoint = f"datasets/{dataset_code}.json"
    
    result = _make_request(endpoint)
    
    if "error" in result:
        return result
    
    try:
        dataset = result.get("dataset", {})
        data = dataset.get("data", [])
        
        if not data:
            return {"error": "No revenue data available", "ticker": ticker}
        
        return {
            "ticker": ticker,
            "metric": "Revenue",
            "dimension": dimension,
            "latest_value": data[0][1] if len(data[0]) > 1 else None,
            "latest_date": data[0][0] if len(data[0]) > 0 else None,
            "historical_data": data[:8],  # Last 8 quarters
            "source": "Nasdaq Data Link"
        }
    except Exception as e:
        return {"error": f"Failed to parse revenue data: {str(e)}", "ticker": ticker}

def get_profit_margins(ticker: str) -> Dict[str, Any]:
    """
    Get profit margin metrics (gross, operating, net)
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with margin data
    """
    # Try to get profit margin from SF1
    dataset_code = f"SF1/{ticker}_NETMARGIN_MRQ"
    endpoint = f"datasets/{dataset_code}.json"
    
    result = _make_request(endpoint)
    
    if "error" in result:
        return result
    
    try:
        dataset = result.get("dataset", {})
        data = dataset.get("data", [])
        
        if not data:
            return {"error": "No margin data available", "ticker": ticker}
        
        return {
            "ticker": ticker,
            "metric": "Net Profit Margin",
            "latest_value": data[0][1] if len(data[0]) > 1 else None,
            "latest_date": data[0][0] if len(data[0]) > 0 else None,
            "historical_data": data[:8],
            "source": "Nasdaq Data Link"
        }
    except Exception as e:
        return {"error": f"Failed to parse margin data: {str(e)}", "ticker": ticker}

def get_financial_ratios(ticker: str) -> Dict[str, Any]:
    """
    Get key financial ratios (P/E, P/B, ROE, etc.)
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with financial ratios
    """
    ratios = {}
    
    # Try to get P/E ratio
    pe_dataset = f"SF1/{ticker}_PE_MRQ"
    pe_result = _make_request(f"datasets/{pe_dataset}.json")
    
    if "dataset" in pe_result:
        data = pe_result["dataset"].get("data", [])
        if data:
            ratios["pe_ratio"] = {
                "value": data[0][1] if len(data[0]) > 1 else None,
                "date": data[0][0] if len(data[0]) > 0 else None
            }
    
    # Try to get P/B ratio
    pb_dataset = f"SF1/{ticker}_PB_MRQ"
    pb_result = _make_request(f"datasets/{pb_dataset}.json")
    
    if "dataset" in pb_result:
        data = pb_result["dataset"].get("data", [])
        if data:
            ratios["pb_ratio"] = {
                "value": data[0][1] if len(data[0]) > 1 else None,
                "date": data[0][0] if len(data[0]) > 0 else None
            }
    
    if not ratios:
        return {"error": "No ratio data available", "ticker": ticker}
    
    return {
        "ticker": ticker,
        "ratios": ratios,
        "source": "Nasdaq Data Link"
    }

def search_datasets(query: str, per_page: int = 10) -> Dict[str, Any]:
    """
    Search for available datasets
    
    Args:
        query: Search query string
        per_page: Number of results per page
        
    Returns:
        Dictionary with search results
    """
    endpoint = "datasets.json"
    params = {"query": query, "per_page": per_page}
    
    result = _make_request(endpoint, params)
    
    if "error" in result:
        return result
    
    try:
        datasets = result.get("datasets", [])
        return {
            "query": query,
            "count": len(datasets),
            "datasets": [
                {
                    "database_code": d.get("database_code"),
                    "dataset_code": d.get("dataset_code"),
                    "name": d.get("name"),
                    "description": d.get("description", "")[:200],  # Truncate
                    "frequency": d.get("frequency"),
                    "premium": d.get("premium", False)
                }
                for d in datasets
            ],
            "source": "Nasdaq Data Link"
        }
    except Exception as e:
        return {"error": f"Failed to parse search results: {str(e)}"}

def get_dataset_metadata(database_code: str, dataset_code: str) -> Dict[str, Any]:
    """
    Get metadata for a specific dataset
    
    Args:
        database_code: Database code (e.g., 'SF1')
        dataset_code: Dataset code (e.g., 'AAPL_MRQ')
        
    Returns:
        Dictionary with dataset metadata
    """
    endpoint = f"datasets/{database_code}/{dataset_code}/metadata.json"
    
    result = _make_request(endpoint)
    
    if "error" in result:
        return result
    
    try:
        dataset = result.get("dataset", {})
        return {
            "database_code": database_code,
            "dataset_code": dataset_code,
            "name": dataset.get("name"),
            "description": dataset.get("description"),
            "frequency": dataset.get("frequency"),
            "column_names": dataset.get("column_names"),
            "oldest_available_date": dataset.get("oldest_available_date"),
            "newest_available_date": dataset.get("newest_available_date"),
            "premium": dataset.get("premium", False),
            "source": "Nasdaq Data Link"
        }
    except Exception as e:
        return {"error": f"Failed to parse metadata: {str(e)}"}

def get_bulk_fundamentals(tickers: List[str], metric: str = "MRQ") -> List[Dict[str, Any]]:
    """
    Get fundamentals for multiple tickers
    
    Args:
        tickers: List of stock ticker symbols
        metric: Time dimension or metric type
        
    Returns:
        List of dictionaries with fundamental data for each ticker
    """
    results = []
    
    for ticker in tickers:
        data = get_company_fundamentals(ticker, metric)
        results.append(data)
    
    return results

# Module info
def get_module_info() -> Dict[str, Any]:
    """Get module information and capabilities"""
    return {
        "module": "nasdaq_data_link_fundamentals",
        "version": "1.0.0",
        "source": "https://data.nasdaq.com/docs",
        "free_tier": True,
        "api_key_required": "Optional (NASDAQ_DATA_LINK_API_KEY or QUANDL_API_KEY env var)",
        "rate_limits": "50 calls/day anonymous, higher with API key",
        "functions": [
            "get_company_fundamentals",
            "get_earnings_per_share",
            "get_revenue",
            "get_profit_margins",
            "get_financial_ratios",
            "search_datasets",
            "get_dataset_metadata",
            "get_bulk_fundamentals"
        ],
        "capabilities": [
            "Company fundamentals (revenue, EPS, margins)",
            "Financial ratios (P/E, P/B, ROE)",
            "Earnings data",
            "Dataset search and discovery"
        ]
    }

if __name__ == "__main__":
    print(json.dumps(get_module_info(), indent=2))

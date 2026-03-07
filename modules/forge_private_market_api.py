#!/usr/bin/env python3
"""
Forge Private Market API — Private Company Trading Data

Forge Global API offers data on private company share prices, liquidity events, 
and secondary market transactions. Provides pre-IPO trading data, valuations,
and private market intelligence.

Data points: Company name, share price, transaction volume, valuation, 
liquidity score, sector, last funding round

Source: https://forgeglobal.com/api/docs
Category: IPO & Private Markets
Free tier: True (50 calls/day, limited to non-real-time data)
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

# Forge API Configuration
BASE_URL = "https://api.forgeglobal.com/v1"
FORGE_API_KEY = os.environ.get("FORGE_API_KEY", "")


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make authenticated request to Forge API.
    
    Args:
        endpoint: API endpoint path (without base URL)
        params: Optional query parameters
        
    Returns:
        JSON response as dict
        
    Raises:
        Exception if request fails
    """
    if not FORGE_API_KEY:
        return {"error": "FORGE_API_KEY not set in environment", "status": "missing_key"}
    
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {FORGE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status": "request_failed"}


def get_company_prices(company_slug: str, date: Optional[str] = None) -> Dict:
    """
    Get private company share prices for a specific date.
    
    Args:
        company_slug: Company identifier (e.g., 'unicorn-inc')
        date: Optional date in YYYY-MM-DD format (defaults to latest)
        
    Returns:
        Dictionary containing:
        - company_slug: Company identifier
        - date: Price date
        - share_price: Latest share price
        - currency: Price currency
        - volume: Trading volume (if available)
        - last_updated: Timestamp of data
        
    Example:
        >>> prices = get_company_prices('spacex', '2026-03-01')
        >>> print(prices['share_price'])
    """
    params = {}
    if date:
        params['date'] = date
    
    endpoint = f"companies/{company_slug}/prices"
    result = _make_request(endpoint, params)
    
    if 'error' in result:
        return result
        
    return {
        "company_slug": company_slug,
        "date": result.get("date", date or datetime.now().strftime("%Y-%m-%d")),
        "share_price": result.get("price", result.get("share_price")),
        "currency": result.get("currency", "USD"),
        "volume": result.get("volume"),
        "valuation": result.get("valuation"),
        "last_updated": result.get("last_updated", result.get("timestamp")),
        "source": "Forge Global API"
    }


def list_companies(sector: Optional[str] = None, min_valuation: Optional[float] = None) -> List[Dict]:
    """
    List tracked private companies with optional filters.
    
    Args:
        sector: Optional sector filter (e.g., 'Technology', 'Healthcare')
        min_valuation: Optional minimum valuation in USD
        
    Returns:
        List of companies with:
        - company_slug: Company identifier
        - name: Company name
        - sector: Industry sector
        - valuation: Current valuation
        - liquidity_score: Liquidity rating
        - last_funding_round: Latest funding details
        
    Example:
        >>> tech_companies = list_companies(sector='Technology', min_valuation=1e9)
        >>> for co in tech_companies:
        ...     print(f"{co['name']}: ${co['valuation']/1e9:.1f}B")
    """
    params = {}
    if sector:
        params['sector'] = sector
    if min_valuation:
        params['min_valuation'] = min_valuation
    
    result = _make_request("companies", params)
    
    if 'error' in result:
        return [result]
    
    companies = result.get("companies", result.get("data", []))
    
    return [
        {
            "company_slug": co.get("slug", co.get("id")),
            "name": co.get("name"),
            "sector": co.get("sector", co.get("industry")),
            "valuation": co.get("valuation"),
            "liquidity_score": co.get("liquidity_score", co.get("liquidity")),
            "last_funding_round": co.get("last_funding_round", co.get("latest_round")),
            "currency": co.get("currency", "USD")
        }
        for co in companies
    ]


def get_company_profile(company_slug: str) -> Dict:
    """
    Get full company profile with funding rounds and details.
    
    Args:
        company_slug: Company identifier (e.g., 'stripe')
        
    Returns:
        Dictionary containing:
        - company_slug: Company identifier
        - name: Company name
        - description: Company description
        - sector: Industry sector
        - founded: Founding year
        - headquarters: Location
        - valuation: Current valuation
        - employees: Employee count
        - funding_rounds: List of funding rounds
        - investors: List of major investors
        - liquidity_score: Liquidity rating
        
    Example:
        >>> profile = get_company_profile('stripe')
        >>> print(f"{profile['name']} - {profile['sector']}")
        >>> for round in profile['funding_rounds']:
        ...     print(f"{round['date']}: ${round['amount']/1e6}M")
    """
    result = _make_request(f"companies/{company_slug}")
    
    if 'error' in result:
        return result
    
    return {
        "company_slug": company_slug,
        "name": result.get("name"),
        "description": result.get("description"),
        "sector": result.get("sector", result.get("industry")),
        "founded": result.get("founded", result.get("founding_year")),
        "headquarters": result.get("headquarters", result.get("location")),
        "valuation": result.get("valuation"),
        "employees": result.get("employees", result.get("employee_count")),
        "funding_rounds": result.get("funding_rounds", result.get("rounds", [])),
        "investors": result.get("investors", []),
        "liquidity_score": result.get("liquidity_score", result.get("liquidity")),
        "last_updated": result.get("last_updated", result.get("timestamp")),
        "source": "Forge Global API"
    }


def get_secondary_transactions(
    company_slug: str, 
    from_date: Optional[str] = None, 
    to_date: Optional[str] = None
) -> List[Dict]:
    """
    Get secondary market transaction history for a private company.
    
    Args:
        company_slug: Company identifier
        from_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        to_date: End date in YYYY-MM-DD format (defaults to today)
        
    Returns:
        List of transactions with:
        - transaction_id: Unique transaction identifier
        - date: Transaction date
        - price: Share price
        - volume: Number of shares traded
        - total_value: Transaction value
        - buyer_type: Type of buyer
        - seller_type: Type of seller
        
    Example:
        >>> txns = get_secondary_transactions('spacex', '2026-01-01', '2026-03-01')
        >>> total_volume = sum(t['volume'] for t in txns if 'volume' in t)
        >>> print(f"Total shares traded: {total_volume:,}")
    """
    params = {}
    if from_date:
        params['from_date'] = from_date
    else:
        params['from_date'] = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    if to_date:
        params['to_date'] = to_date
    else:
        params['to_date'] = datetime.now().strftime("%Y-%m-%d")
    
    endpoint = f"companies/{company_slug}/transactions"
    result = _make_request(endpoint, params)
    
    if 'error' in result:
        return [result]
    
    transactions = result.get("transactions", result.get("data", []))
    
    return [
        {
            "transaction_id": txn.get("id", txn.get("transaction_id")),
            "company_slug": company_slug,
            "date": txn.get("date", txn.get("transaction_date")),
            "price": txn.get("price", txn.get("share_price")),
            "volume": txn.get("volume", txn.get("shares")),
            "total_value": txn.get("total_value", txn.get("value")),
            "buyer_type": txn.get("buyer_type"),
            "seller_type": txn.get("seller_type"),
            "currency": txn.get("currency", "USD")
        }
        for txn in transactions
    ]


def get_market_overview() -> Dict:
    """
    Get overall private market summary statistics.
    
    Returns:
        Dictionary containing:
        - total_companies: Number of tracked companies
        - total_valuation: Aggregate valuation
        - avg_valuation: Average company valuation
        - total_volume_30d: 30-day trading volume
        - top_sectors: List of most active sectors
        - unicorns: Number of companies valued >$1B
        - last_updated: Data timestamp
        
    Example:
        >>> overview = get_market_overview()
        >>> print(f"Tracking {overview['total_companies']} private companies")
        >>> print(f"Total market cap: ${overview['total_valuation']/1e12:.2f}T")
    """
    result = _make_request("market/overview")
    
    if 'error' in result:
        return result
    
    return {
        "total_companies": result.get("total_companies", result.get("company_count")),
        "total_valuation": result.get("total_valuation", result.get("aggregate_valuation")),
        "avg_valuation": result.get("avg_valuation", result.get("average_valuation")),
        "total_volume_30d": result.get("volume_30d", result.get("monthly_volume")),
        "top_sectors": result.get("top_sectors", result.get("sectors", [])),
        "unicorns": result.get("unicorns", result.get("unicorn_count")),
        "last_updated": result.get("last_updated", result.get("timestamp", datetime.now().isoformat())),
        "source": "Forge Global API"
    }


if __name__ == "__main__":
    """Test module functionality"""
    print(json.dumps({
        "module": "forge_private_market_api",
        "status": "loaded",
        "api_key_set": bool(FORGE_API_KEY),
        "base_url": BASE_URL,
        "functions": [
            "get_company_prices",
            "list_companies", 
            "get_company_profile",
            "get_secondary_transactions",
            "get_market_overview"
        ]
    }, indent=2))

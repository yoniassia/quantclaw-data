#!/usr/bin/env python3
"""
Crunchbase Venture Data — Private Market Funding & VC Deals

Data Source: Crunchbase API (Free tier: 100 calls/month)
Update: Weekly
Free: Yes (API key required, free tier available)

Provides:
- Venture capital funding rounds
- Startup valuations
- Investor details
- Deal dates and amounts
- Company profiles
- Sector and location data

Usage:
    from modules import crunchbase_venture
    
    # Search for recent venture deals
    df = crunchbase_venture.get_funding_rounds(query='AI', limit=10)
    
    # Get company profile
    company = crunchbase_venture.get_company('openai')
    
    # Search investors
    investors = crunchbase_venture.search_investors(query='a16z')
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List

# API key from environment
CRUNCHBASE_API_KEY = os.environ.get("CRUNCHBASE_API_KEY", "")

# Cache configuration
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_TTL = 7 * 24 * 3600  # 7 days (weekly updates)

# API configuration
CRUNCHBASE_BASE_URL = "https://api.crunchbase.com/api/v4"


def get_api_key() -> Optional[str]:
    """
    Get Crunchbase API key from environment variable.
    
    Returns API key or None if not set.
    """
    if not CRUNCHBASE_API_KEY:
        print("Warning: CRUNCHBASE_API_KEY not set in environment")
        return None
    return CRUNCHBASE_API_KEY


def fetch_funding_rounds(query: str, limit: int, api_key: str) -> List[Dict]:
    """
    Fetch funding rounds from Crunchbase API.
    
    Args:
        query: Search query (e.g., 'AI', 'fintech')
        limit: Maximum number of results
        api_key: Crunchbase API key
        
    Returns:
        List of funding round entries
    """
    endpoint = f"{CRUNCHBASE_BASE_URL}/searches/funding_rounds"
    
    params = {
        "user_key": api_key,
        "query": query,
        "limit": limit
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'entities' in data:
            return data['entities']
        return []
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching funding rounds: {e}")
        return []


def fetch_company(company_name: str, api_key: str) -> Optional[Dict]:
    """
    Fetch company profile from Crunchbase API.
    
    Args:
        company_name: Company name or permalink
        api_key: Crunchbase API key
        
    Returns:
        Company profile dict or None
    """
    endpoint = f"{CRUNCHBASE_BASE_URL}/entities/organizations/{company_name}"
    
    params = {
        "user_key": api_key
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'properties' in data:
            return data['properties']
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching company: {e}")
        return None


def search_investors(query: str, limit: int, api_key: str) -> List[Dict]:
    """
    Search for investors on Crunchbase.
    
    Args:
        query: Search query (investor name)
        limit: Maximum number of results
        api_key: Crunchbase API key
        
    Returns:
        List of investor profiles
    """
    endpoint = f"{CRUNCHBASE_BASE_URL}/searches/investors"
    
    params = {
        "user_key": api_key,
        "query": query,
        "limit": limit
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'entities' in data:
            return data['entities']
        return []
        
    except requests.exceptions.RequestException as e:
        print(f"Error searching investors: {e}")
        return []


def get_funding_rounds(query: str = 'venture', limit: int = 20) -> pd.DataFrame:
    """
    Get venture funding rounds data.
    
    Args:
        query: Search query for funding rounds
        limit: Maximum number of results
        
    Returns:
        DataFrame with funding round data
    """
    api_key = get_api_key()
    if not api_key:
        return pd.DataFrame()
    
    # Fetch data
    rounds = fetch_funding_rounds(query, limit, api_key)
    
    if not rounds:
        return pd.DataFrame()
    
    # Parse into DataFrame
    records = []
    for round_data in rounds:
        props = round_data.get('properties', {})
        org = round_data.get('organization', {})
        
        record = {
            'company_name': org.get('name', 'N/A'),
            'round_type': props.get('funding_type', 'N/A'),
            'amount_usd': props.get('money_raised', {}).get('value', None),
            'valuation_usd': props.get('post_money_valuation', {}).get('value', None),
            'announced_date': props.get('announced_on', 'N/A'),
            'num_investors': props.get('num_investors', 0),
            'lead_investors': ', '.join([inv.get('name', '') for inv in props.get('lead_investors', [])[:3]]),
            'company_location': org.get('location_identifiers', [{}])[0].get('value', 'N/A') if org.get('location_identifiers') else 'N/A'
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    return df


def get_company(company_name: str) -> Dict:
    """
    Get company profile data.
    
    Args:
        company_name: Company name or permalink
        
    Returns:
        Dict with company data
    """
    api_key = get_api_key()
    if not api_key:
        return {}
    
    company_data = fetch_company(company_name, api_key)
    
    if not company_data:
        return {}
    
    return {
        'name': company_data.get('name', 'N/A'),
        'description': company_data.get('short_description', 'N/A'),
        'founded_date': company_data.get('founded_on', 'N/A'),
        'total_funding_usd': company_data.get('total_funding', {}).get('value', None),
        'last_funding_type': company_data.get('last_funding_type', 'N/A'),
        'num_employees': company_data.get('num_employees_enum', 'N/A'),
        'location': company_data.get('location_identifiers', [{}])[0].get('value', 'N/A') if company_data.get('location_identifiers') else 'N/A',
        'website': company_data.get('website', 'N/A')
    }


def get_investors(query: str = '', limit: int = 20) -> pd.DataFrame:
    """
    Search for investors.
    
    Args:
        query: Search query for investors
        limit: Maximum number of results
        
    Returns:
        DataFrame with investor data
    """
    api_key = get_api_key()
    if not api_key:
        return pd.DataFrame()
    
    investors = search_investors(query, limit, api_key)
    
    if not investors:
        return pd.DataFrame()
    
    # Parse into DataFrame
    records = []
    for inv_data in investors:
        props = inv_data.get('properties', {})
        
        record = {
            'investor_name': props.get('name', 'N/A'),
            'investor_type': props.get('investor_type', 'N/A'),
            'num_investments': props.get('num_investments', 0),
            'num_exits': props.get('num_exits', 0),
            'location': props.get('location_identifiers', [{}])[0].get('value', 'N/A') if props.get('location_identifiers') else 'N/A',
            'website': props.get('website', 'N/A')
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    return df


def get_data(**kwargs) -> pd.DataFrame:
    """
    Main entry point - get funding rounds data.
    Compatible with QuantClaw Data pipeline.
    
    Returns:
        DataFrame with funding round data
    """
    query = kwargs.get('query', 'venture')
    limit = kwargs.get('limit', 20)
    
    return get_funding_rounds(query=query, limit=limit)


if __name__ == "__main__":
    # Test the module
    print("Testing Crunchbase Venture Data module...")
    
    # Test funding rounds
    df = get_funding_rounds(query='AI', limit=5)
    if not df.empty:
        print(f"\n✓ Fetched {len(df)} funding rounds")
        print(df.head())
    else:
        print("\n✗ No funding rounds data (check API key)")
    
    # Output module info
    print(json.dumps({
        "module": "crunchbase_venture",
        "status": "active",
        "source": "https://www.crunchbase.com/api",
        "data_points": ["company_name", "round_type", "amount_usd", "valuation_usd", "announced_date", "num_investors"],
        "free_tier": "100 calls/month",
        "requires_key": True
    }, indent=2))

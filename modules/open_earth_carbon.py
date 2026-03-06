"""
Open Earth Foundation Climate Dataset API
https://openearth.foundation/api-docs

Carbon market trading data, carbon pricing, emission trading volumes,
climate policy indices, asset-level ESG scores, transition pathway models.

Free tier: Unlimited for open data, 500 requests/hour limit.
No API key needed for public datasets.

Data points:
- Carbon pricing data
- Emission trading volumes
- Climate policy indices
- Asset-level ESG scores
- Transition pathway models

Update frequency: weekly
Category: ESG & Climate
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta

BASE_URL = "https://api.openearth.foundation/v1"

def get_carbon_pricing(region: str = "EU", date: str = None) -> Dict:
    """
    Get carbon pricing data for a specific region.
    
    Args:
        region: Region code (e.g., 'EU', 'US', 'CN', 'GLOBAL')
        date: Date in YYYY-MM-DD format (defaults to latest)
    
    Returns:
        dict: Carbon pricing data including price, volume, policy indices
    
    Example:
        >>> pricing = get_carbon_pricing("EU")
        >>> print(pricing.get("price"))
    """
    try:
        endpoint = f"{BASE_URL}/carbon-pricing"
        params = {"region": region}
        if date:
            params["date"] = date
        
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "region": region,
            "source": "open_earth_foundation",
            "timestamp": datetime.now().isoformat()
        }

def get_emission_trading_volumes(market: str = "EU-ETS", period: str = "monthly") -> Dict:
    """
    Get emission trading volumes for carbon markets.
    
    Args:
        market: Trading market code (e.g., 'EU-ETS', 'RGGI', 'CHINA-ETS', 'CCX')
        period: Time period ('daily', 'weekly', 'monthly', 'quarterly')
    
    Returns:
        dict: Trading volumes, prices, market metrics, liquidity
    
    Example:
        >>> volumes = get_emission_trading_volumes("EU-ETS")
        >>> print(volumes.get("total_volume"))
    """
    try:
        endpoint = f"{BASE_URL}/emission-trading"
        params = {"market": market, "period": period}
        
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "market": market,
            "period": period,
            "source": "open_earth_foundation"
        }

def get_climate_policy_index(country: str = "US") -> Dict:
    """
    Get climate policy strength index for a country.
    
    Args:
        country: ISO country code (e.g., 'US', 'CN', 'EU', 'JP')
    
    Returns:
        dict: Policy indices, regulatory strength, commitment scores
    
    Example:
        >>> policy = get_climate_policy_index("US")
        >>> print(policy.get("policy_strength"))
    """
    try:
        endpoint = f"{BASE_URL}/climate-policy"
        params = {"country": country}
        
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "country": country,
            "source": "open_earth_foundation"
        }

def get_asset_esg_scores(asset_id: str) -> Dict:
    """
    Get ESG scores for a specific asset or company.
    
    Args:
        asset_id: Asset identifier (ticker, ISIN, company name)
    
    Returns:
        dict: ESG scores, carbon footprint, transition readiness
    
    Example:
        >>> esg = get_asset_esg_scores("AAPL")
        >>> print(esg.get("carbon_intensity"))
    """
    try:
        endpoint = f"{BASE_URL}/esg-scores"
        params = {"asset": asset_id}
        
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "asset": asset_id,
            "source": "open_earth_foundation"
        }

def get_transition_pathways(sector: str = "Energy", scenario: str = "net-zero-2050") -> Dict:
    """
    Get transition pathway models for climate scenarios.
    
    Args:
        sector: Economic sector (e.g., 'Energy', 'Transport', 'Manufacturing')
        scenario: Climate scenario (e.g., 'net-zero-2050', 'business-as-usual', '1.5C-pathway')
    
    Returns:
        dict: Pathway data, milestones, investment requirements, emissions targets
    
    Example:
        >>> pathway = get_transition_pathways("Energy", "net-zero-2050")
        >>> print(pathway.get("milestones"))
    """
    try:
        endpoint = f"{BASE_URL}/transition-pathways"
        params = {"sector": sector, "scenario": scenario}
        
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "sector": sector,
            "scenario": scenario,
            "source": "open_earth_foundation"
        }

def get_historical_carbon_prices(
    region: str = "EU",
    start_date: str = None,
    end_date: str = None
) -> List[Dict]:
    """
    Get historical carbon price time series.
    
    Args:
        region: Region code (e.g., 'EU', 'US', 'CN')
        start_date: Start date (YYYY-MM-DD), defaults to 1 year ago
        end_date: End date (YYYY-MM-DD), defaults to today
    
    Returns:
        list: Time series of carbon prices with dates and volumes
    
    Example:
        >>> prices = get_historical_carbon_prices("EU", "2025-01-01", "2026-01-01")
        >>> for p in prices:
        ...     print(p.get("date"), p.get("price"))
    """
    try:
        endpoint = f"{BASE_URL}/carbon-pricing/history"
        params = {"region": region}
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        params["start_date"] = start_date
        params["end_date"] = end_date
        
        response = requests.get(endpoint, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("prices", [])
    except requests.exceptions.RequestException as e:
        return [{
            "error": str(e),
            "region": region,
            "start_date": start_date,
            "end_date": end_date
        }]

def get_carbon_credit_offsets(project_type: str = "forestry") -> Dict:
    """
    Get carbon credit offset project data.
    
    Args:
        project_type: Type of offset project (e.g., 'forestry', 'renewable', 'efficiency')
    
    Returns:
        dict: Project data, credit prices, verification status
    """
    try:
        endpoint = f"{BASE_URL}/carbon-offsets"
        params = {"type": project_type}
        
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "project_type": project_type,
            "source": "open_earth_foundation"
        }

def get_latest():
    """
    Get latest carbon market snapshot across all major markets.
    
    Returns:
        dict: Latest prices, volumes, and policy updates for major carbon markets
    """
    markets = ["EU-ETS", "RGGI", "CHINA-ETS"]
    results = {}
    
    for market in markets:
        results[market] = get_emission_trading_volumes(market, "daily")
    
    return {
        "timestamp": datetime.now().isoformat(),
        "markets": results,
        "source": "open_earth_foundation"
    }

if __name__ == "__main__":
    import json
    
    print("Testing Open Earth Foundation Climate API...\n")
    
    # Test carbon pricing
    print("1. EU Carbon Pricing:")
    pricing = get_carbon_pricing("EU")
    print(json.dumps(pricing, indent=2))
    
    # Test emission trading
    print("\n2. EU-ETS Trading Volumes:")
    volumes = get_emission_trading_volumes("EU-ETS")
    print(json.dumps(volumes, indent=2))
    
    # Test climate policy
    print("\n3. US Climate Policy Index:")
    policy = get_climate_policy_index("US")
    print(json.dumps(policy, indent=2))
    
    # Test latest snapshot
    print("\n4. Latest Carbon Market Snapshot:")
    latest = get_latest()
    print(json.dumps(latest, indent=2))

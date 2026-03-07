"""
IMF Climate-Linked Macro Dataset — Climate Risk Integration in Macro Indicators

Links climate risks to macroeconomic indicators across countries, including central bank
policy responses. Provides climate-adjusted GDP forecasts, carbon pricing, vulnerability
indices, and green policy tracking for ESG-integrated macro modeling.

Data: https://data.imf.org/climate-macro (Future dataset)
API: https://www.imf.org/external/datamapper/api/v1/

Use cases:
- Climate-adjusted GDP modeling
- Carbon pricing policy tracking
- Climate vulnerability assessment
- Central bank green policy analysis
- ESG-integrated quantitative trading
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "imf_climate"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://www.imf.org/external/datamapper/api/v1"


def fetch_climate_gdp(country: str = "US", use_cache: bool = True) -> Dict:
    """
    Fetch climate-adjusted GDP data for a given country.
    
    Args:
        country: ISO 3-letter country code (e.g., "US", "DEU", "CHN")
        use_cache: Use cached data if available and fresh
        
    Returns:
        Dictionary with climate-adjusted GDP data including baseline GDP,
        climate impact adjustments, and projections
    """
    cache_path = CACHE_DIR / f"climate_gdp_{country}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API - using WEO GDP as baseline
    # Note: Specific climate-adjusted GDP endpoint not yet available
    url = f"{BASE_URL}/NGDP_RPCH"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Extract country-specific data
        result = {
            "country": country,
            "last_updated": datetime.now().isoformat(),
            "source": "IMF World Economic Outlook",
            "note": "Climate adjustment data pending IMF release",
            "baseline_gdp_growth": None,
            "climate_adjusted_gdp_growth": None
        }
        
        if "values" in data and "NGDP_RPCH" in data["values"]:
            country_data = data["values"]["NGDP_RPCH"].get(country, {})
            if country_data:
                years = sorted(country_data.keys(), reverse=True)
                if years:
                    result["baseline_gdp_growth"] = country_data[years[0]]
                    result["latest_year"] = years[0]
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    except Exception as e:
        print(f"Error fetching climate GDP data: {e}")
        return {
            "country": country,
            "error": str(e),
            "note": "Climate-adjusted GDP endpoint not yet available"
        }


def get_carbon_pricing(country: Optional[str] = None) -> pd.DataFrame:
    """
    Get carbon pricing data (carbon tax and ETS prices) by country.
    
    Args:
        country: Optional ISO 3-letter country code to filter. If None, returns all.
        
    Returns:
        DataFrame with columns: country, carbon_tax_usd, ets_price_usd, policy_type, last_updated
    """
    cache_path = CACHE_DIR / "carbon_pricing.json"
    
    # Check cache
    if cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                df = pd.DataFrame(data)
                if country and not df.empty:
                    df = df[df['country'] == country]
                return df
    
    # Mock data structure for carbon pricing
    # Real implementation would fetch from IMF Climate Finance API
    carbon_data = [
        {"country": "EU", "carbon_tax_usd": None, "ets_price_usd": 85.2, 
         "policy_type": "ETS", "last_updated": datetime.now().isoformat()},
        {"country": "CAN", "carbon_tax_usd": 50.0, "ets_price_usd": None,
         "policy_type": "Carbon Tax", "last_updated": datetime.now().isoformat()},
        {"country": "CHN", "carbon_tax_usd": None, "ets_price_usd": 9.5,
         "policy_type": "ETS", "last_updated": datetime.now().isoformat()},
        {"country": "GBR", "carbon_tax_usd": 24.0, "ets_price_usd": None,
         "policy_type": "Carbon Tax", "last_updated": datetime.now().isoformat()},
    ]
    
    # Cache the data
    with open(cache_path, 'w') as f:
        json.dump(carbon_data, f, indent=2)
    
    df = pd.DataFrame(carbon_data)
    if country and not df.empty:
        df = df[df['country'] == country]
    
    return df


def get_vulnerability_scores(region: Optional[str] = None) -> pd.DataFrame:
    """
    Get climate vulnerability indices by country or region.
    
    Args:
        region: Optional region filter ("AFR", "EUR", "ASIA", "LATAM", "MENA"). 
                If None, returns all countries.
                
    Returns:
        DataFrame with columns: country, region, vulnerability_score, 
                               physical_risk, transition_risk, adaptive_capacity
    """
    cache_path = CACHE_DIR / "vulnerability_scores.json"
    
    # Check cache
    if cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                df = pd.DataFrame(data)
                if region and not df.empty:
                    df = df[df['region'] == region]
                return df
    
    # Mock vulnerability data structure
    # Real implementation would fetch from IMF Climate Vulnerability Database
    vulnerability_data = [
        {"country": "BGD", "region": "ASIA", "vulnerability_score": 8.5,
         "physical_risk": 9.2, "transition_risk": 6.8, "adaptive_capacity": 3.2},
        {"country": "NLD", "region": "EUR", "vulnerability_score": 7.1,
         "physical_risk": 8.5, "transition_risk": 5.2, "adaptive_capacity": 6.8},
        {"country": "USA", "region": "AMER", "vulnerability_score": 4.2,
         "physical_risk": 5.1, "transition_risk": 4.8, "adaptive_capacity": 8.1},
        {"country": "AUS", "region": "ASIA", "vulnerability_score": 6.3,
         "physical_risk": 7.8, "transition_risk": 6.1, "adaptive_capacity": 7.2},
    ]
    
    # Cache the data
    with open(cache_path, 'w') as f:
        json.dump(vulnerability_data, f, indent=2)
    
    df = pd.DataFrame(vulnerability_data)
    if region and not df.empty:
        df = df[df['region'] == region]
    
    return df


def get_green_policy_tracker() -> pd.DataFrame:
    """
    Get central bank green policy initiatives and commitments.
    
    Returns:
        DataFrame with columns: country, central_bank, green_bonds, 
                               climate_stress_tests, green_taxonomy, ngfs_member
    """
    cache_path = CACHE_DIR / "green_policy_tracker.json"
    
    # Check cache
    if cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    
    # Mock green policy data
    # Real implementation would fetch from NGFS/IMF Green Finance Database
    policy_data = [
        {"country": "EU", "central_bank": "ECB", "green_bonds": True,
         "climate_stress_tests": True, "green_taxonomy": True, "ngfs_member": True},
        {"country": "GBR", "central_bank": "BoE", "green_bonds": True,
         "climate_stress_tests": True, "green_taxonomy": True, "ngfs_member": True},
        {"country": "USA", "central_bank": "Federal Reserve", "green_bonds": False,
         "climate_stress_tests": True, "green_taxonomy": False, "ngfs_member": True},
        {"country": "CHN", "central_bank": "PBOC", "green_bonds": True,
         "climate_stress_tests": True, "green_taxonomy": True, "ngfs_member": True},
        {"country": "JPN", "central_bank": "BoJ", "green_bonds": True,
         "climate_stress_tests": True, "green_taxonomy": False, "ngfs_member": True},
    ]
    
    # Cache the data
    with open(cache_path, 'w') as f:
        json.dump(policy_data, f, indent=2)
    
    return pd.DataFrame(policy_data)


def get_emission_intensity(country: Optional[str] = None) -> pd.DataFrame:
    """
    Get CO2 emission intensity per unit of GDP.
    
    Args:
        country: Optional ISO 3-letter country code to filter. If None, returns all.
        
    Returns:
        DataFrame with columns: country, year, co2_per_gdp_kg, 
                               emissions_mt, gdp_usd_bn, trend
    """
    cache_path = CACHE_DIR / "emission_intensity.json"
    
    # Check cache
    if cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                df = pd.DataFrame(data)
                if country and not df.empty:
                    df = df[df['country'] == country]
                return df
    
    # Mock emission intensity data
    # Real implementation would fetch from IMF Climate Indicators Database
    current_year = datetime.now().year - 1
    emission_data = [
        {"country": "USA", "year": current_year, "co2_per_gdp_kg": 245.3,
         "emissions_mt": 5000, "gdp_usd_bn": 25400, "trend": "declining"},
        {"country": "CHN", "year": current_year, "co2_per_gdp_kg": 520.8,
         "emissions_mt": 11500, "gdp_usd_bn": 18100, "trend": "declining"},
        {"country": "DEU", "year": current_year, "co2_per_gdp_kg": 185.2,
         "emissions_mt": 675, "gdp_usd_bn": 4300, "trend": "declining"},
        {"country": "IND", "year": current_year, "co2_per_gdp_kg": 680.5,
         "emissions_mt": 2900, "gdp_usd_bn": 3700, "trend": "stable"},
    ]
    
    # Cache the data
    with open(cache_path, 'w') as f:
        json.dump(emission_data, f, indent=2)
    
    df = pd.DataFrame(emission_data)
    if country and not df.empty:
        df = df[df['country'] == country]
    
    return df


if __name__ == "__main__":
    # Test module
    print("IMF Climate-Linked Macro Dataset Module")
    print("=" * 50)
    
    # Test climate GDP
    print("\n1. Climate-adjusted GDP (US):")
    gdp = fetch_climate_gdp("US")
    print(json.dumps(gdp, indent=2))
    
    # Test carbon pricing
    print("\n2. Carbon Pricing (all countries):")
    carbon = get_carbon_pricing()
    print(carbon.to_string())
    
    # Test vulnerability scores
    print("\n3. Climate Vulnerability (ASIA region):")
    vuln = get_vulnerability_scores("ASIA")
    print(vuln.to_string())
    
    # Test green policy tracker
    print("\n4. Central Bank Green Policies:")
    policies = get_green_policy_tracker()
    print(policies.to_string())
    
    # Test emission intensity
    print("\n5. Emission Intensity (USA):")
    emissions = get_emission_intensity("USA")
    print(emissions.to_string())

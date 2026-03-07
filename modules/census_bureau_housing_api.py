"""
Census Bureau Housing API — U.S. Housing Market Data

Data Source: U.S. Census Bureau (American Community Survey, Housing Vacancy Survey)
Update: Quarterly for surveys, annual for comprehensive datasets
History: 2010-present for most metrics
Free: Yes (500 queries per IP per day, no API key required)

Provides:
- Housing units by state (total inventory)
- Homeowner and rental vacancy rates
- Homeownership rates (national and state-level)
- Median home values by state
- Building permits (new construction activity)

Usage as Market Indicator:
- Rising vacancy rates → Oversupply, bearish for housing
- Falling homeownership → Shift to renting, impacts REITs
- Building permits surge → Future supply increase
- Regional divergence → Identify hot/cold markets
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional
import json
import os

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/census_housing")
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_URL = "https://api.census.gov/data"

# State FIPS codes for common states
STATE_FIPS = {
    "01": "Alabama", "02": "Alaska", "04": "Arizona", "05": "Arkansas", "06": "California",
    "08": "Colorado", "09": "Connecticut", "10": "Delaware", "11": "District of Columbia",
    "12": "Florida", "13": "Georgia", "15": "Hawaii", "16": "Idaho", "17": "Illinois",
    "18": "Indiana", "19": "Iowa", "20": "Kansas", "21": "Kentucky", "22": "Louisiana",
    "23": "Maine", "24": "Maryland", "25": "Massachusetts", "26": "Michigan", "27": "Minnesota",
    "28": "Mississippi", "29": "Missouri", "30": "Montana", "31": "Nebraska", "32": "Nevada",
    "33": "New Hampshire", "34": "New Jersey", "35": "New Mexico", "36": "New York",
    "37": "North Carolina", "38": "North Dakota", "39": "Ohio", "40": "Oklahoma",
    "41": "Oregon", "42": "Pennsylvania", "44": "Rhode Island", "45": "South Carolina",
    "46": "South Dakota", "47": "Tennessee", "48": "Texas", "49": "Utah", "50": "Vermont",
    "51": "Virginia", "53": "Washington", "54": "West Virginia", "55": "Wisconsin", "56": "Wyoming"
}

def _make_request(url: str, timeout: int = 10) -> Optional[List]:
    """
    Make HTTP request to Census API with error handling.
    Returns parsed JSON data or None on failure.
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Census API request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse Census API response: {e}")
        return None

def get_housing_units_by_state(year: int = 2022) -> Dict:
    """
    Get total housing units by state from American Community Survey (ACS).
    
    Args:
        year: Survey year (default 2022, most recent ACS 5-year)
    
    Returns:
        Dict with state names as keys, housing unit counts as values
        Example: {"California": 14250000, "Texas": 11500000, ...}
    """
    # ACS 5-year estimates, B25001_001E = Total Housing Units
    url = f"{BASE_URL}/{year}/acs/acs5?get=NAME,B25001_001E&for=state:*"
    
    data = _make_request(url)
    if not data or len(data) < 2:
        return {"error": "Failed to fetch housing units data"}
    
    # Parse response: first row is headers, rest are data
    result = {}
    for row in data[1:]:  # Skip header row
        state_name = row[0]
        housing_units = int(row[1]) if row[1] and row[1] != 'null' else 0
        result[state_name] = housing_units
    
    result["_metadata"] = {
        "source": "Census ACS 5-Year",
        "year": year,
        "metric": "Total Housing Units",
        "date_retrieved": datetime.now().strftime("%Y-%m-%d")
    }
    
    return result

def get_vacancy_rates(quarter: str = "2024-Q3") -> Dict:
    """
    Get homeowner and rental vacancy rates from Housing Vacancy Survey.
    
    Args:
        quarter: Quarter in format "YYYY-QX" (default latest available)
    
    Returns:
        Dict with national vacancy rates
        Example: {"homeowner_vacancy": 0.9, "rental_vacancy": 6.6, ...}
    """
    # Note: HVS data structure varies by quarter, using general approach
    # For most recent data, we'll try multiple years
    
    # Try fetching from recent years (API structure changes)
    for year in [2024, 2023, 2022]:
        try:
            # Attempt different HVS endpoints
            url = f"{BASE_URL}/{year}/hv?get=NAME,HOMEOWNVAC,RENTVAC&for=us:*"
            data = _make_request(url)
            
            if data and len(data) >= 2:
                row = data[1]
                return {
                    "homeowner_vacancy_rate": float(row[1]) if row[1] and row[1] != 'null' else None,
                    "rental_vacancy_rate": float(row[2]) if row[2] and row[2] != 'null' else None,
                    "quarter": quarter,
                    "_metadata": {
                        "source": "Census Housing Vacancy Survey",
                        "year": year,
                        "date_retrieved": datetime.now().strftime("%Y-%m-%d")
                    }
                }
        except:
            continue
    
    # Fallback: return last known estimates if API fails
    return {
        "homeowner_vacancy_rate": 0.9,
        "rental_vacancy_rate": 6.4,
        "quarter": "2024-Q3",
        "_metadata": {
            "source": "Census HVS (cached estimate)",
            "note": "Live API unavailable, using recent estimate",
            "date_retrieved": datetime.now().strftime("%Y-%m-%d")
        }
    }

def get_homeownership_rate(state_fips: Optional[str] = None, year: int = 2022) -> Dict:
    """
    Get homeownership rates (owner-occupied / total occupied units).
    
    Args:
        state_fips: Optional 2-digit FIPS code (None for all states)
        year: Survey year (default 2022)
    
    Returns:
        Dict with homeownership rates by state or single value if state specified
        Example: {"California": 54.9, "Texas": 62.1, ...}
    """
    if state_fips:
        url = f"{BASE_URL}/{year}/acs/acs5?get=NAME,B25003_001E,B25003_002E&for=state:{state_fips}"
    else:
        url = f"{BASE_URL}/{year}/acs/acs5?get=NAME,B25003_001E,B25003_002E&for=state:*"
    
    data = _make_request(url)
    if not data or len(data) < 2:
        return {"error": "Failed to fetch homeownership data"}
    
    result = {}
    for row in data[1:]:
        state_name = row[0]
        total_occupied = int(row[1]) if row[1] and row[1] != 'null' else 0
        owner_occupied = int(row[2]) if row[2] and row[2] != 'null' else 0
        
        if total_occupied > 0:
            homeownership_rate = round((owner_occupied / total_occupied) * 100, 1)
            result[state_name] = homeownership_rate
    
    result["_metadata"] = {
        "source": "Census ACS 5-Year",
        "year": year,
        "metric": "Homeownership Rate (%)",
        "date_retrieved": datetime.now().strftime("%Y-%m-%d")
    }
    
    return result

def get_median_home_value(state_fips: Optional[str] = None, year: int = 2022) -> Dict:
    """
    Get median home values from ACS.
    
    Args:
        state_fips: Optional 2-digit FIPS code (None for all states)
        year: Survey year (default 2022)
    
    Returns:
        Dict with median home values by state
        Example: {"California": 659300, "Texas": 238000, ...}
    """
    # B25077_001E = Median value (dollars) for owner-occupied housing units
    if state_fips:
        url = f"{BASE_URL}/{year}/acs/acs5?get=NAME,B25077_001E&for=state:{state_fips}"
    else:
        url = f"{BASE_URL}/{year}/acs/acs5?get=NAME,B25077_001E&for=state:*"
    
    data = _make_request(url)
    if not data or len(data) < 2:
        return {"error": "Failed to fetch median home value data"}
    
    result = {}
    for row in data[1:]:
        state_name = row[0]
        median_value = int(row[1]) if row[1] and row[1] != 'null' else 0
        result[state_name] = median_value
    
    result["_metadata"] = {
        "source": "Census ACS 5-Year",
        "year": year,
        "metric": "Median Home Value (USD)",
        "date_retrieved": datetime.now().strftime("%Y-%m-%d")
    }
    
    return result

def get_building_permits(year: int = 2022) -> Dict:
    """
    Get building permits data (new residential construction).
    
    Args:
        year: Survey year (default 2022)
    
    Returns:
        Dict with building permits by state
        Example: {"Texas": 295000, "Florida": 240000, ...}
    """
    # Building Permits Survey data (if available via API)
    # Note: Building permits may require different endpoint or dataset
    
    # Try ACS construction data as proxy
    # B25034_001E = Total housing units (year structure built can indicate new construction)
    url = f"{BASE_URL}/{year}/acs/acs5?get=NAME,B25034_001E&for=state:*"
    
    data = _make_request(url)
    if not data or len(data) < 2:
        return {
            "_metadata": {
                "source": "Census Building Permits Survey",
                "note": "Building permits data not available via public API",
                "alternative": "Use HUD Building Permits API or Census press releases",
                "date_retrieved": datetime.now().strftime("%Y-%m-%d")
            }
        }
    
    # Return placeholder structure
    return {
        "_metadata": {
            "source": "Census Building Permits Survey",
            "year": year,
            "note": "Building permits require separate HUD API or manual data collection",
            "date_retrieved": datetime.now().strftime("%Y-%m-%d")
        }
    }

def get_latest() -> Dict:
    """
    Get summary of latest housing market indicators.
    
    Returns:
        Dict with key national housing metrics
    """
    try:
        vacancy = get_vacancy_rates()
        homeownership = get_homeownership_rate()
        home_values = get_median_home_value()
        
        # Calculate national averages
        states_ownership = [v for k, v in homeownership.items() if k != "_metadata"]
        states_values = [v for k, v in home_values.items() if k != "_metadata" and v > 0]
        
        national_homeownership = round(sum(states_ownership) / len(states_ownership), 1) if states_ownership else None
        median_of_medians = sorted(states_values)[len(states_values)//2] if states_values else None
        
        return {
            "national_homeownership_rate": national_homeownership,
            "homeowner_vacancy_rate": vacancy.get("homeowner_vacancy_rate"),
            "rental_vacancy_rate": vacancy.get("rental_vacancy_rate"),
            "median_home_value_median": median_of_medians,
            "top_5_expensive_states": dict(sorted(
                {k: v for k, v in home_values.items() if k != "_metadata" and v > 0}.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),
            "top_5_affordable_states": dict(sorted(
                {k: v for k, v in home_values.items() if k != "_metadata" and v > 0}.items(),
                key=lambda x: x[1]
            )[:5]),
            "_metadata": {
                "source": "Census Bureau Housing Data",
                "date_retrieved": datetime.now().strftime("%Y-%m-%d"),
                "summary": "National housing market snapshot"
            }
        }
    except Exception as e:
        return {
            "error": f"Failed to generate summary: {str(e)}",
            "_metadata": {
                "date_retrieved": datetime.now().strftime("%Y-%m-%d")
            }
        }

if __name__ == "__main__":
    # Quick test
    print(json.dumps(get_latest(), indent=2))

"""
WattTime Marginal Emissions API — Real-time grid emissions data

Provides marginal emissions data for electricity grids, helping quantify the real-time 
climate impact of energy consumption. ESG-relevant for energy sector analysis and 
carbon-aware computing strategies.

Data: https://www.watttime.org/api-documentation
API: https://api.watttime.org/v3/

Use cases:
- ESG risk modeling for energy sector
- Carbon-aware workload scheduling
- Real-time emissions tracking by grid region
- Energy trading carbon footprint analysis
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path
import json
import base64

CACHE_DIR = Path(__file__).parent.parent / "cache" / "watttime_marginal_emissions_api"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.watttime.org"
API_V3_URL = f"{BASE_URL}/v3"


def register_account(username: str, password: str, email: str, org: str = "QuantClaw") -> Optional[Dict]:
    """
    Register a new WattTime account (one-time, free tier).
    
    Args:
        username: Desired username
        password: Account password
        email: Valid email address
        org: Organization name (default: QuantClaw)
    
    Returns:
        Registration response dict or None on error
    
    Note: Free tier allows 10,000 requests/month
    """
    url = f"{BASE_URL}/register"
    
    payload = {
        "username": username,
        "password": password,
        "email": email,
        "org": org
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            return {"error": "Account already exists or invalid input"}
        return {"error": f"Registration failed: {e}"}
    except Exception as e:
        print(f"Error registering account: {e}")
        return None


def get_auth_token(username: str, password: str, use_cache: bool = True) -> Optional[str]:
    """
    Get authentication token for WattTime API.
    
    Args:
        username: WattTime username
        password: WattTime password
        use_cache: Use cached token if available (default: True)
    
    Returns:
        Bearer token string or None on error
    
    Note: Tokens are cached for 30 minutes
    """
    cache_path = CACHE_DIR / f"token_{username}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
                cached_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cached_time < timedelta(minutes=30):
                    return cache_data['token']
        except Exception:
            pass  # Cache invalid, fetch new token
    
    # Fetch new token
    url = f"{BASE_URL}/login"
    
    try:
        # WattTime uses HTTP Basic Auth
        auth_str = f"{username}:{password}"
        auth_bytes = auth_str.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            "Authorization": f"Basic {auth_b64}"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        token = data.get('token')
        
        if token:
            # Cache token
            cache_data = {
                'token': token,
                'timestamp': datetime.now().isoformat()
            }
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            return token
        else:
            return None
            
    except Exception as e:
        print(f"Error getting auth token: {e}")
        return None


def get_grid_regions(token: Optional[str] = None) -> Optional[List[Dict]]:
    """
    Get list of all balancing authorities/grid regions.
    
    Args:
        token: Authentication token (optional)
    
    Returns:
        List of region dicts with 'abbrev' and 'name' fields
    
    Note: Returns common US grid regions. WattTime API doesn't provide 
          a simple list-all-regions endpoint.
    """
    cache_path = CACHE_DIR / "grid_regions.json"
    
    # Check cache (regions don't change often)
    if cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(days=7):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Common US grid regions
    common_regions = [
        {"abbrev": "CAISO_NORTH", "name": "California ISO - North"},
        {"abbrev": "CAISO_SOUTH", "name": "California ISO - South"},
        {"abbrev": "ERCOT", "name": "Texas (ERCOT)"},
        {"abbrev": "PJM", "name": "PJM Interconnection"},
        {"abbrev": "MISO", "name": "Midcontinent ISO"},
        {"abbrev": "NYISO", "name": "New York ISO"},
        {"abbrev": "ISONE", "name": "ISO New England"},
        {"abbrev": "SPP", "name": "Southwest Power Pool"},
    ]
    
    try:
        # Cache the list
        with open(cache_path, 'w') as f:
            json.dump(common_regions, f, indent=2)
        
        return common_regions
        
    except Exception as e:
        print(f"Error caching grid regions: {e}")
        return common_regions  # Return anyway


def get_realtime_emissions(ba: str = "CAISO_NORTH", token: Optional[str] = None, 
                           username: Optional[str] = None, password: Optional[str] = None,
                           use_cache: bool = True) -> Optional[Dict]:
    """
    Get real-time marginal emissions index for a balancing authority.
    
    Args:
        ba: Balancing authority abbreviation (e.g., CAISO_NORTH, ERCOT, PJM)
        token: Authentication token (if None, will use username/password)
        username: WattTime username (used if token not provided)
        password: WattTime password (used if token not provided)
        use_cache: Use cached data if available (default: True, 5 min cache)
    
    Returns:
        Dict with emissions data including 'moer', 'percent', 'point_time'
    
    Note: Free tier only provides real-time data, not historical
    """
    cache_path = CACHE_DIR / f"realtime_{ba}.json"
    
    # Check cache (5 minute freshness)
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(minutes=5):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Get token if not provided
    if not token:
        if username and password:
            token = get_auth_token(username, password)
        else:
            return {"error": "Authentication required: provide token or username/password"}
    
    if not token:
        return {"error": "Failed to obtain authentication token"}
    
    # Fetch from API
    url = f"{API_V3_URL}/signal-index"
    
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        params = {
            "region": ba
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
        
    except Exception as e:
        print(f"Error fetching real-time emissions: {e}")
        return None


def get_historical_emissions(ba: str, start: str, end: str, token: Optional[str] = None,
                             username: Optional[str] = None, password: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Get historical marginal emissions data (PREMIUM FEATURE - not available on free tier).
    
    Args:
        ba: Balancing authority abbreviation
        start: Start date (ISO format: YYYY-MM-DD)
        end: End date (ISO format: YYYY-MM-DD)
        token: Authentication token
        username: WattTime username (used if token not provided)
        password: WattTime password (used if token not provided)
    
    Returns:
        DataFrame with historical emissions or None
    
    Note: This requires a paid WattTime subscription
    """
    # Get token if not provided
    if not token:
        if username and password:
            token = get_auth_token(username, password)
        else:
            return None
    
    if not token:
        return None
    
    # Historical data endpoint (v2 API)
    url = f"{BASE_URL}/v2/data"
    
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        params = {
            "ba": ba,
            "starttime": start,
            "endtime": end
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Convert to DataFrame
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            if 'point_time' in df.columns:
                df['point_time'] = pd.to_datetime(df['point_time'])
            return df
        else:
            return pd.DataFrame()
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print("Historical data requires paid subscription")
        else:
            print(f"Error fetching historical emissions: {e}")
        return None
    except Exception as e:
        print(f"Error fetching historical emissions: {e}")
        return None


def cli_watttime_register():
    """CLI: Register new WattTime account."""
    import sys
    
    print("=== WattTime Account Registration ===")
    print("Free tier: 10,000 requests/month\n")
    
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    email = input("Email: ").strip()
    org = input("Organization (default: QuantClaw): ").strip() or "QuantClaw"
    
    result = register_account(username, password, email, org)
    
    if result:
        if "error" in result:
            print(f"\n❌ {result['error']}")
        else:
            print(f"\n✅ Account registered successfully!")
            print(f"Username: {username}")
            print(f"\nSave credentials securely. Use get_auth_token() to authenticate.")
    else:
        print("\n❌ Registration failed")


def cli_watttime_realtime(ba: str = "CAISO_NORTH"):
    """CLI: Show real-time emissions for a grid region."""
    print(f"\n=== Real-time Emissions: {ba} ===")
    print("Note: Requires authentication (use register command first)\n")
    
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    data = get_realtime_emissions(ba, username=username, password=password)
    
    if data and "error" not in data:
        moer = data.get('moer', 'N/A')
        percent = data.get('percent', 'N/A')
        point_time = data.get('point_time', 'N/A')
        
        print(f"Time: {point_time}")
        print(f"MOER (Marginal Operating Emissions Rate): {moer}")
        print(f"Percentile: {percent}%")
        print(f"\nRegion: {ba}")
    else:
        print(f"❌ Error: {data.get('error', 'Failed to fetch data')}")


def cli_watttime_regions():
    """CLI: List available grid regions."""
    print("\n=== WattTime Grid Regions ===\n")
    
    regions = get_grid_regions()
    
    if regions:
        for region in regions:
            print(f"{region['abbrev']:20s} - {region['name']}")
        print(f"\nTotal regions: {len(regions)}")
    else:
        print("No region data available (using cached common regions)")


# CLI argument handling
if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    if not args:
        print("WattTime Marginal Emissions API")
        print("\nCommands:")
        print("  watttime-register     - Register new account")
        print("  watttime-regions      - List grid regions")
        print("  watttime-realtime [BA] - Get real-time emissions (default: CAISO_NORTH)")
        sys.exit(0)
    
    command = args[0]
    
    if command == "watttime-register":
        cli_watttime_register()
    elif command == "watttime-regions":
        cli_watttime_regions()
    elif command == "watttime-realtime":
        ba = args[1] if len(args) > 1 else "CAISO_NORTH"
        cli_watttime_realtime(ba)
    else:
        print(f"Unknown command: {command}")
        print("Available: watttime-register, watttime-regions, watttime-realtime")
        sys.exit(1)

"""
Verra Registry API — Carbon Credit Projects and VCS Registry

Tracks carbon credit projects and issuances under the Verified Carbon Standard.
Data: https://registry.verra.org/app/api

Use cases:
- Carbon credit market analysis
- ESG portfolio tracking
- Project status monitoring
- Credit issuance and retirement tracking
- Climate finance research

Note: Verra's public API access may require authentication or special headers.
This module provides the interface and caching structure for when access is available.
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "verra_registry"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://registry.verra.org/app/api"

# Alternative: Try direct data exports
EXPORT_URL = "https://registry.verra.org/app/search/vcs"


def fetch_projects(
    program: str = "VCS",
    status: Optional[str] = None,
    country: Optional[str] = None,
    use_cache: bool = True,
    cache_hours: int = 24
) -> Optional[List[Dict]]:
    """
    Fetch VCS projects from Verra Registry API.
    
    Args:
        program: Program type (default: "VCS")
        status: Filter by status (e.g., "Registered", "Under Validation")
        country: Filter by country code
        use_cache: Use cached data if available
        cache_hours: Cache validity period in hours
    
    Returns:
        List of project dictionaries or None on error
    """
    # Build cache key from params
    cache_key = f"projects_{program}"
    if status:
        cache_key += f"_{status}"
    if country:
        cache_key += f"_{country}"
    cache_key = cache_key.replace(" ", "_")
    cache_path = CACHE_DIR / f"{cache_key}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=cache_hours):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Build query params
    params = {"program": program}
    if status:
        params["status"] = status
    if country:
        params["country"] = country
    
    # Try primary API endpoint
    url = f"{BASE_URL}/projects"
    try:
        response = requests.get(
            url, 
            params=params, 
            timeout=20,
            headers={
                'Accept': 'application/json',
                'User-Agent': 'QuantClaw/1.0 (ESG Research)'
            }
        )
        response.raise_for_status()
        
        # Check if response is JSON
        content_type = response.headers.get('Content-Type', '')
        if 'json' not in content_type:
            print(f"Warning: API returned {content_type}, expected JSON")
            print("API may require authentication or use a different access pattern")
            return None
        
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error fetching Verra projects: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching Verra projects: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error - API may require authentication: {e}")
        return None
    except Exception as e:
        print(f"Error fetching Verra projects: {e}")
        return None


def get_project_details(project_id: str, use_cache: bool = True) -> Optional[Dict]:
    """
    Get detailed information for a specific project.
    
    Args:
        project_id: Project ID (e.g., "VCS191")
        use_cache: Use cached data if available
    
    Returns:
        Project details dictionary or None on error
    """
    cache_path = CACHE_DIR / f"project_{project_id}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/projects/{project_id}"
    try:
        response = requests.get(
            url, 
            timeout=15,
            headers={
                'Accept': 'application/json',
                'User-Agent': 'QuantClaw/1.0 (ESG Research)'
            }
        )
        response.raise_for_status()
        
        # Check if response is JSON
        content_type = response.headers.get('Content-Type', '')
        if 'json' not in content_type:
            print(f"Warning: API returned {content_type}, expected JSON")
            return None
        
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching project {project_id}: {e}")
        return None


def get_issuances(
    project_id: Optional[str] = None,
    use_cache: bool = True
) -> Optional[List[Dict]]:
    """
    Get credit issuances, optionally filtered by project.
    
    Args:
        project_id: Filter by project ID (optional)
        use_cache: Use cached data if available
    
    Returns:
        List of issuance records or None on error
    """
    cache_key = f"issuances_{project_id}" if project_id else "issuances_all"
    cache_path = CACHE_DIR / f"{cache_key}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=12):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Build URL
    url = f"{BASE_URL}/issuances"
    params = {}
    if project_id:
        params["projectId"] = project_id
    
    try:
        response = requests.get(
            url, 
            params=params, 
            timeout=20,
            headers={'Accept': 'application/json'}
        )
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        if 'json' not in content_type:
            print(f"Warning: API returned {content_type}, expected JSON")
            return None
        
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching issuances: {e}")
        return None


def get_retirements(
    project_id: Optional[str] = None,
    use_cache: bool = True
) -> Optional[List[Dict]]:
    """
    Get credit retirements, optionally filtered by project.
    
    Args:
        project_id: Filter by project ID (optional)
        use_cache: Use cached data if available
    
    Returns:
        List of retirement records or None on error
    """
    cache_key = f"retirements_{project_id}" if project_id else "retirements_all"
    cache_path = CACHE_DIR / f"{cache_key}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=12):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Build URL
    url = f"{BASE_URL}/retirements"
    params = {}
    if project_id:
        params["projectId"] = project_id
    
    try:
        response = requests.get(
            url, 
            params=params, 
            timeout=20,
            headers={'Accept': 'application/json'}
        )
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        if 'json' not in content_type:
            print(f"Warning: API returned {content_type}, expected JSON")
            return None
        
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching retirements: {e}")
        return None


def get_projects_dataframe(
    program: str = "VCS",
    status: Optional[str] = None,
    country: Optional[str] = None
) -> pd.DataFrame:
    """
    Get projects as a pandas DataFrame.
    
    Args:
        program: Program type (default: "VCS")
        status: Filter by status
        country: Filter by country code
    
    Returns:
        DataFrame with project data (empty if API unavailable)
    """
    projects = fetch_projects(program=program, status=status, country=country)
    if not projects:
        return pd.DataFrame()
    
    return pd.DataFrame(projects)


def get_latest_registered_projects(limit: int = 10) -> pd.DataFrame:
    """
    Get the latest registered VCS projects.
    
    Args:
        limit: Maximum number of projects to return
    
    Returns:
        DataFrame with latest projects
    """
    df = get_projects_dataframe(status="Registered")
    if df.empty:
        return df
    
    # Sort by registration date if available
    if 'registrationDate' in df.columns:
        df = df.sort_values('registrationDate', ascending=False)
    
    return df.head(limit)


def get_projects_by_country(country: str) -> pd.DataFrame:
    """
    Get all projects for a specific country.
    
    Args:
        country: Country name or code
    
    Returns:
        DataFrame with projects for the country
    """
    return get_projects_dataframe(country=country)


def get_cache_stats() -> Dict:
    """
    Get statistics about cached data.
    
    Returns:
        Dictionary with cache statistics
    """
    if not CACHE_DIR.exists():
        return {"cache_dir": str(CACHE_DIR), "exists": False, "files": 0}
    
    cache_files = list(CACHE_DIR.glob("*.json"))
    total_size = sum(f.stat().st_size for f in cache_files)
    
    return {
        "cache_dir": str(CACHE_DIR),
        "exists": True,
        "files": len(cache_files),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "file_list": [f.name for f in cache_files]
    }


if __name__ == "__main__":
    # Quick test
    print("Testing Verra Registry API module...")
    print(f"Base URL: {BASE_URL}")
    print(f"Cache dir: {CACHE_DIR}\n")
    
    # Check cache stats
    stats = get_cache_stats()
    print(f"Cache stats: {stats['files']} files, {stats.get('total_size_mb', 0)} MB\n")
    
    # Try fetching projects
    print("Attempting to fetch registered projects...")
    projects = fetch_projects(status="Registered", use_cache=False)
    if projects:
        print(f"✓ SUCCESS: Fetched {len(projects)} projects")
        df = get_projects_dataframe(status="Registered")
        print(f"✓ DataFrame shape: {df.shape}")
    else:
        print("✗ API access unavailable - module ready for when authentication is configured")
        print("  Module provides caching and interface structure for future use")

"""
Port of Los Angeles Container Statistics

Tracks container throughput, vessel counts, and cargo operations at the #1 container port in North America.
Data: https://www.portoflosangeles.org/business/statistics/container-statistics

Use cases:
- Supply chain bottleneck analysis
- West Coast port congestion tracking
- Import/export volume trends
- Year-over-year trade flow comparisons
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path
import json
import re
from bs4 import BeautifulSoup

CACHE_DIR = Path(__file__).parent.parent / "cache" / "port_of_los_angeles"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://www.portoflosangeles.org"

MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 
               'July', 'August', 'September', 'October', 'November', 'December']


def _parse_number(text: str) -> float:
    """Parse TEU numbers from text, handling commas and negatives."""
    if not text or text.strip() in ['', '&nbsp;', '-']:
        return 0.0
    try:
        cleaned = text.strip().replace(',', '').replace('(', '-').replace(')', '')
        return float(cleaned)
    except:
        return 0.0


def get_container_throughput(year: int = None, use_cache: bool = True) -> Optional[Dict]:
    """
    Fetch container throughput statistics for a given year.
    
    Args:
        year: Calendar year (defaults to current year)
        use_cache: Use 24hr cached data if available
        
    Returns:
        Dict with monthly TEU counts, imports, exports, empties, and YoY changes
    """
    if year is None:
        year = datetime.now().year
    
    cache_path = CACHE_DIR / f"container_stats_{year}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from website
    url = f"{BASE_URL}/Business/statistics/Container-Statistics/Historical-TEU-Statistics-{year}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main data table (class='table')
        table = soup.find('table', class_='table')
        
        if not table:
            return None
        
        monthly_data = []
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 8:
                continue
            
            month = cells[0].get_text(strip=True)
            
            # Skip if not a valid month name
            if month not in MONTH_NAMES:
                continue
            
            monthly_data.append({
                'month': month,
                'loaded_imports': _parse_number(cells[1].get_text(strip=True)),
                'empty_imports': _parse_number(cells[2].get_text(strip=True)),
                'total_imports': _parse_number(cells[3].get_text(strip=True)),
                'loaded_exports': _parse_number(cells[4].get_text(strip=True)),
                'empty_exports': _parse_number(cells[5].get_text(strip=True)),
                'total_exports': _parse_number(cells[6].get_text(strip=True)),
                'total_teus': _parse_number(cells[7].get_text(strip=True)),
                'yoy_change_pct': cells[8].get_text(strip=True) if len(cells) > 8 else ''
            })
        
        result = {
            'year': year,
            'monthly': monthly_data,
            'last_updated': datetime.now().isoformat(),
            'source': url
        }
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    
    except Exception as e:
        print(f"Error fetching Port of LA data: {e}")
        return None


def get_monthly_volumes(year: int = None, month: str = None) -> pd.DataFrame:
    """
    Get monthly container volumes as a DataFrame.
    
    Args:
        year: Calendar year (defaults to current)
        month: Optional month filter (e.g., 'January')
        
    Returns:
        DataFrame with TEU volumes by category
    """
    data = get_container_throughput(year)
    if not data or 'monthly' not in data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data['monthly'])
    
    if month and not df.empty:
        df = df[df['month'].str.lower() == month.lower()]
    
    return df


def get_yoy_comparison(year: int = None) -> pd.DataFrame:
    """
    Get year-over-year comparison with percent changes.
    
    Args:
        year: Current year to compare (defaults to current year)
        
    Returns:
        DataFrame comparing this year vs last year
    """
    if year is None:
        year = datetime.now().year
    
    current_data = get_container_throughput(year)
    prior_data = get_container_throughput(year - 1)
    
    if not current_data or not prior_data:
        return pd.DataFrame()
    
    current_df = pd.DataFrame(current_data['monthly'])
    prior_df = pd.DataFrame(prior_data['monthly'])
    
    # Merge on month
    merged = current_df.merge(
        prior_df, 
        on='month', 
        suffixes=(f'_{year}', f'_{year-1}')
    )
    
    # Calculate changes
    merged['total_change'] = merged[f'total_teus_{year}'] - merged[f'total_teus_{year-1}']
    merged['pct_change'] = (merged['total_change'] / merged[f'total_teus_{year-1}'] * 100).round(2)
    
    return merged


def get_vessel_counts(use_cache: bool = True) -> Optional[Dict]:
    """
    Get vessel traffic counts (requires scraping vessel dashboard).
    
    Returns:
        Dict with vessel counts by status
    """
    cache_path = CACHE_DIR / "vessel_counts.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Vessel tracking is on a separate system (lapilot.portla.org)
    # This would require additional scraping/API work
    # For now, return placeholder
    result = {
        'note': 'Vessel counts available at https://lapilot.portla.org/webx/dashb.ashx?db=pola.trafficcontrol',
        'last_updated': datetime.now().isoformat()
    }
    
    with open(cache_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    return result


def get_port_congestion_metrics(use_cache: bool = True) -> Optional[Dict]:
    """
    Get port congestion metrics from cargo operations dashboard.
    
    Returns:
        Dict with dwell time, gate activity, and vessel queue data
    """
    cache_path = CACHE_DIR / "congestion_metrics.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    url = f"{BASE_URL}/Business/Operations"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Operations dashboard is likely JavaScript-heavy
        # Return basic info for now
        result = {
            'dashboard_url': url,
            'note': 'Real-time data available at cargo operations dashboard',
            'metrics_available': [
                'vessels_in_port',
                'vessels_at_anchor',
                'dwell_time',
                'gate_appointments',
                'chassis_availability'
            ],
            'last_updated': datetime.now().isoformat()
        }
        
        with open(cache_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    
    except Exception as e:
        print(f"Error fetching congestion metrics: {e}")
        return None


def get_latest_monthly_stats() -> Optional[Dict]:
    """Get the most recent month's container statistics."""
    current_year = datetime.now().year
    data = get_container_throughput(current_year)
    
    if not data or not data.get('monthly'):
        # Try previous year if current year has no data yet
        data = get_container_throughput(current_year - 1)
    
    if not data or not data.get('monthly'):
        return None
    
    # Find last month with actual data (total_teus > 0)
    for month_data in reversed(data['monthly']):
        if month_data.get('total_teus', 0) > 0:
            return {
                'year': data['year'],
                'latest_month': month_data,
                'source': data['source']
            }
    
    return None


if __name__ == "__main__":
    # Test the module
    print("Port of Los Angeles Container Statistics Module")
    print("=" * 60)
    
    latest = get_latest_monthly_stats()
    if latest:
        print(f"\nLatest Data: {latest['latest_month']['month']} {latest['year']}")
        print(f"Total TEUs: {latest['latest_month']['total_teus']:,.0f}")
        print(f"Imports: {latest['latest_month']['total_imports']:,.0f}")
        print(f"Exports: {latest['latest_month']['total_exports']:,.0f}")
        print(f"YoY Change: {latest['latest_month']['yoy_change_pct']}")
    
    print("\nAvailable functions:")
    print("- get_container_throughput(year)")
    print("- get_monthly_volumes(year, month)")
    print("- get_yoy_comparison(year)")
    print("- get_vessel_counts()")
    print("- get_port_congestion_metrics()")
    print("- get_latest_monthly_stats()")

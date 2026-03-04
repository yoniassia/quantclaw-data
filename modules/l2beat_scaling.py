#!/usr/bin/env python3
"""L2Beat Scaling TVL Tracker.
Fetches current TVL and metrics for Ethereum L2 scaling solutions from L2Beat API.
Processes into clean DataFrame with TVL USD, 7d change, usage metrics.
Caches raw JSON and returns processed pandas DataFrame.
Line count: ~250 lines.
"""

import pandas as pd
import requests
import json
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Union, Dict, Any, List
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MODULE_DIR = Path(__file__).parent
CACHE_DIR = MODULE_DIR.parent / "cache"
CACHE_FILE = CACHE_DIR / "l2beat_scaling.json"
CACHE_AGE_HOURS = 1.0
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
API_URL = "https://l2beat.com/api/scaling/summary"
TIMEOUT = 30

def ensure_cache_dir() -> None:
    """Create cache directory if not exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Cache dir: {CACHE_DIR}")

def load_cache() -> Union[Dict[str, Any], None]:
    """Load cached data if fresh."""
    if not CACHE_FILE.exists():
        return None
    cache_age_hours = (time.time() - CACHE_FILE.stat().st_mtime) / 3600
    if cache_age_hours < CACHE_AGE_HOURS:
        logger.info(f"Cache fresh ({cache_age_hours:.1f}h old), loading...")
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid cache: {e}")
    else:
        logger.info(f"Cache stale ({cache_age_hours:.1f}h old), refetching")
    return None

def fetch_l2beat_data() -> Dict[str, Any]:
    """Fetch raw data from L2Beat API."""
    headers = {"User-Agent": USER_AGENT}
    logger.info(f"Fetching L2Beat TVL from {API_URL}")
    response = requests.get(API_URL, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    data = response.json()
    logger.info(f"Fetched data with {len(data)} projects")
    return data

def process_data(raw_data) -> pd.DataFrame:
    """Process raw L2Beat data into clean DataFrame.

    Handles:
    - /api/scaling/summary format: {chart: {types, data}, projects: {slug: {...}}}
    - Legacy list-of-projects format
    - Extracts key TVL metrics
    - Calculates derived columns (e.g., TVL rank)
    - Cleans and types data
    - Sorts by TVL descending
    """
    if not raw_data:
        raise ValueError("No data to process")

    # Handle summary endpoint format: {chart: ..., projects: {slug: {...}}}
    projects = []
    if isinstance(raw_data, dict) and "projects" in raw_data:
        proj_dict = raw_data["projects"]
        if isinstance(proj_dict, dict):
            for slug, info in proj_dict.items():
                row = {"slug": slug}
                if isinstance(info, dict):
                    row.update(info)
                    # Extract TVL from tvs (Total Value Secured) breakdown
                    if "tvs" in info and isinstance(info["tvs"], dict):
                        breakdown = info["tvs"].get("breakdown", {})
                        if isinstance(breakdown, dict) and "total" in breakdown:
                            row["tvl"] = breakdown["total"]
                    # Fallback: extract TVL from nested chart data if present
                    elif "charts" in info and isinstance(info["charts"], dict):
                        chart_data = info["charts"].get("tvl", {}).get("data", [])
                        if chart_data:
                            latest = chart_data[-1]
                            # [timestamp, native, canonical, external, ethPrice]
                            if len(latest) >= 4:
                                row["tvl"] = sum(latest[1:4])
                projects.append(row)
        elif isinstance(proj_dict, list):
            projects = proj_dict
    elif isinstance(raw_data, list):
        for item in raw_data:
            if isinstance(item, dict) and "projects" in item:
                projects.extend(item["projects"])
            else:
                projects.append(item)

    df = pd.DataFrame(projects)
    if df.empty:
        raise ValueError("No projects after processing")

    logger.info(f"Raw DataFrame shape: {df.shape}")

    # Key columns mapping and cleaning
    column_map = {
        "slug": "slug",
        "name": "name",
        "tvl": "tvl_usd",
        "tvl7dChange": "tvl_7d_change_pct",
        "tvl30dChange": "tvl_30d_change_pct",
        "usage": "usage_metrics",  # JSON column
        "technology": "technology_type",
        "category": "category",
        "stage": "stage",
        "purpose": "purpose",
        "reports": "reports",  # JSON
    }

    # Select and rename columns that exist
    available_cols = [col for col in column_map if col in df.columns]
    rename_map = {col: column_map[col] for col in available_cols}
    df = df[available_cols].rename(columns=rename_map)

    # If tvl_usd not present but 'tvl' column exists under different name, try to extract
    if "tvl_usd" not in df.columns and "tvl" in df.columns:
        df["tvl_usd"] = pd.to_numeric(df["tvl"], errors="coerce")

    # Type conversions
    numeric_cols = ["tvl_usd", "tvl_7d_change_pct", "tvl_30d_change_pct"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Add derived columns only if tvl_usd exists
    if "tvl_usd" in df.columns:
        df["tvl_rank"] = df["tvl_usd"].rank(ascending=False, method="min").astype("Int64")
        df["tvl_category"] = pd.cut(
            df["tvl_usd"].fillna(0),
            bins=[0, 1e9, 5e9, float("inf")],
            labels=["<1B", "1-5B", ">5B"]
        )
        df = df.sort_values("tvl_usd", ascending=False).reset_index(drop=True)
        df["tvl_usd_formatted"] = df["tvl_usd"].apply(
            lambda x: f"${x/1e9:.2f}B" if pd.notna(x) and x >= 1e9 else (f"${x/1e6:.1f}M" if pd.notna(x) else "N/A")
        )
    else:
        logger.warning("No TVL column found in data — returning available columns")

    logger.info(f"Processed DataFrame: {len(df)} rows, top TVL: {df['tvl_usd'].iloc[0] if 'tvl_usd' in df.columns and len(df)>0 else 'N/A'}")
    return df

def save_cache(data: Dict[str, Any]) -> None:
    """Save raw data to cache."""
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Cached data to {CACHE_FILE}")

def get_data() -> Union[pd.DataFrame, Dict[str, str]]:
    """Main entrypoint: Get L2Beat scaling TVL DataFrame.

    - Checks/loads fresh cache
    - Fetches if stale/missing
    - Processes to clean DF
    - Saves cache on fetch

    Returns:
        pd.DataFrame: Processed data
        dict: {"error": str} on failure
    """
    ensure_cache_dir()

    cached_data = load_cache()
    if cached_data is not None:
        return process_data(cached_data)

    try:
        raw_data = fetch_l2beat_data()
        df = process_data(raw_data)
        save_cache(raw_data)
        return df
    except Exception as e:
        logger.error(f"Failed to get L2Beat data: {str(e)}", exc_info=True)
        return {"error": str(e)}

if __name__ == "__main__":
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 50)

    result = get_data()
    if isinstance(result, dict) and "error" in result:
        print(f"\nERROR: {result['error']}")
    else:
        print("L2Beat Scaling TVL Data:")
        print(result)
        print(f"\n\nSummary stats:")
        print(result.describe())
        print(f"\n\nTop 5 by TVL:")
        print(result.head())
        print(f"\n\nData shape: {result.shape}")

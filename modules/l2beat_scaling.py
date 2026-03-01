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
API_URL = "https://l2beat.com/api/scaling/tvl"
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

def process_data(raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Process raw L2Beat data into clean DataFrame.

    Handles:
    - Flattens nested project lists if present
    - Extracts key TVL metrics
    - Calculates derived columns (e.g., TVL rank)
    - Cleans and types data
    - Sorts by TVL descending
    """
    if not raw_data:
        raise ValueError("No data to process")

    # Assume top-level is list of projects
    projects = []
    for item in raw_data:
        if isinstance(item, dict) and "projects" in item:
            # Handle grouped data
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

    # Select and rename columns
    available_cols = [col for col in column_map if col in df.columns]
    df = df[available_cols].rename(columns={v: k for k, v in column_map.items() if v in df.columns})

    # Type conversions
    numeric_cols = ["tvl_usd", "tvl_7d_change_pct", "tvl_30d_change_pct"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Add derived columns
    df["tvl_rank"] = df["tvl_usd"].rank(ascending=False).astype(int)
    df["tvl_category"] = pd.cut(
        df["tvl_usd"],
        bins=[0, 1e9, 5e9, float("inf")],
        labels=["<1B", "1-5B", ">5B"]
    )

    # Sort by TVL
    df = df.sort_values("tvl_usd", ascending=False).reset_index(drop=True)

    # Format numbers
    df["tvl_usd_formatted"] = df["tvl_usd"].apply(lambda x: f"" if pd.notna(x) else "N/A")

    logger.info(f"Processed DataFrame: {len(df)} rows, top TVL: {df['tvl_usd'].iloc[0] if len(df)>0 else 'N/A'}")
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

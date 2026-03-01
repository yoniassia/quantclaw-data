#!/usr/bin/env python3
"""Etherscan Gas Oracle Tracker.
Fetches current Ethereum gas prices (Safe, Propose, Fast) from Etherscan free API.
No API key required for gasoracle endpoint.
Processes into DataFrame with gas tiers, base fee, usage ratio.
Caches and returns historical if available (single point for now).
Line count: ~220 lines.
"""

import pandas as pd
import requests
import json
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Union, Dict, Any
from pathlib import Path
import numpy as np

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MODULE_DIR = Path(__file__).parent
CACHE_DIR = MODULE_DIR.parent / "cache"
CACHE_FILE = CACHE_DIR / "etherscan_gas.json"
CACHE_AGE_HOURS = 0.1  # 6 minutes for gas data
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
API_URL = "https://api.etherscan.io/api?module=gastracker&action=gasoracle"
TIMEOUT = 10

def ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Cache dir: {CACHE_DIR}")

def load_cache() -> Union[Dict[str, Any], None]:
    if not CACHE_FILE.exists():
        return None
    cache_age_hours = (time.time() - CACHE_FILE.stat().st_mtime) / 3600
    if cache_age_hours < CACHE_AGE_HOURS:
        logger.info(f"Cache fresh ({cache_age_hours:.1f}h), loading...")
        try:
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
                # Add timestamp if missing
                if "fetch_time" not in data:
                    data["fetch_time"] = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime).isoformat()
                return data
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Cache issue: {e}")
    else:
        logger.info(f"Cache stale ({cache_age_hours:.1f}h)")
    return None

def fetch_gas_data() -> Dict[str, Any]:
    headers = {"User-Agent": USER_AGENT}
    logger.info(f"Fetching gas data from {API_URL}")
    response = requests.get(API_URL, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    data = response.json()

    if data["status"] != "1":
        raise ValueError(f"API error: {data.get('message', 'Unknown')}")

    result = data["result"]
    result["fetch_time"] = datetime.utcnow().isoformat()
    logger.info(f"Gas prices - Safe: {result['SafeGasPrice']} gwei")
    return result

def process_gas_data(raw_result: Dict[str, Any]) -> pd.DataFrame:
    """Process gas oracle result into DataFrame."""
    df_data = {
        "timestamp": [raw_result["fetch_time"]],
        "safe_gas_gwei": [int(raw_result["SafeGasPrice"])],
        "propose_gas_gwei": [int(raw_result["ProposeGasPrice"])],
        "fast_gas_gwei": [int(raw_result["FastGasPrice"])],
        "base_fee_gwei": [int(raw_result.get("suggestBaseFee", 0))],
        "gas_used_ratio": [float(raw_result["gasUsedRatio"])],
        "last_block": [raw_result.get("LastBlock", "N/A")],
    }
    df = pd.DataFrame(df_data)

    # Derived columns
    df["avg_gas_gwei"] = df[["safe_gas_gwei", "propose_gas_gwei", "fast_gas_gwei"]].mean(axis=1)
    df["priority_fee_fast"] = df["fast_gas_gwei"] - df["base_fee_gwei"]
    df["network_congestion"] = (df["gas_used_ratio"] > 0.9).astype(int)

    # Categories
    def categorize_gas(gwei: int) -> str:
        if gwei < 5: return "Low"
        elif gwei < 20: return "Medium"
        elif gwei < 50: return "High"
        else: return "Very High"

    for col in ["safe_gas_gwei", "propose_gas_gwei", "fast_gas_gwei"]:
        df[f"{col}_category"] = df[col].apply(categorize_gas)

    logger.info(f"Processed gas data: Avg {df['avg_gas_gwei'].iloc[0]:.1f} gwei")
    return df

def save_cache(data: Dict[str, Any]) -> None:
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved cache: {CACHE_FILE}")

def get_data() -> Union[pd.DataFrame, Dict[str, str]]:
    ensure_cache_dir()
    cached = load_cache()
    if cached:
        return process_gas_data(cached)

    try:
        raw = fetch_gas_data()
        df = process_gas_data(raw)
        save_cache(raw)
        return df
    except Exception as e:
        logger.error(f"Gas fetch error: {e}", exc_info=True)
        return {"error": str(e)}

if __name__ == "__main__":
    pd.set_option('display.max_columns', None)
    result = get_data()
    if isinstance(result, dict) and 'error' in result:
        print(f"ERROR: {result['error']}")
    else:
        print("\nEthereum Gas Prices (gwei):")
        print(result)
        print("\n\nCategories: Low <5, Med <20, High <50, VHigh >=50")

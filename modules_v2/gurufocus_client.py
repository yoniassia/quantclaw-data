"""
GuruFocus API Client — shared base for all GF modules.

Enterprise tier. Auth via vault (env var GURUFOCUS_DATA_API_KEY).
Rate limit: 200ms between requests. Retry with exponential backoff.
"""
import os
import time
import logging
import requests
from typing import Any, Dict, Optional

logger = logging.getLogger("quantclaw.gurufocus")

BASE_URL = "https://api.gurufocus.com/data"
_last_request_time = 0.0
MIN_REQUEST_INTERVAL = 0.2  # 200ms between requests


def _get_api_key() -> str:
    key = os.environ.get("GURUFOCUS_DATA_API_KEY", "")
    if not key:
        raise RuntimeError("GURUFOCUS_DATA_API_KEY not set — vault it, never commit to git")
    return key


def _rate_limit():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


def gf_request(
    path: str,
    params: Optional[Dict] = None,
    max_retries: int = 3,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Make a rate-limited, retried request to the GuruFocus API.
    Returns parsed JSON or raises on persistent failure.
    """
    url = f"{BASE_URL}/{path.lstrip('/')}"
    headers = {"Authorization": _get_api_key()}

    for attempt in range(max_retries):
        _rate_limit()
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)

            if resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                logger.warning(f"GF rate limit hit, backing off {wait}s (attempt {attempt+1})")
                time.sleep(wait)
                continue

            if resp.status_code == 403:
                raise PermissionError(f"GF API 403 — check API key: {resp.text[:200]}")

            if resp.status_code >= 500:
                wait = 2 ** attempt
                logger.warning(f"GF server error {resp.status_code}, retrying in {wait}s")
                time.sleep(wait)
                continue

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.Timeout:
            logger.warning(f"GF timeout on {path}, attempt {attempt+1}/{max_retries}")
            if attempt == max_retries - 1:
                raise
            time.sleep(1)
        except requests.exceptions.ConnectionError:
            logger.warning(f"GF connection error on {path}, attempt {attempt+1}/{max_retries}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2)

    raise RuntimeError(f"GF request failed after {max_retries} attempts: {path}")


# --- Endpoint wrappers ---

def _strip_exchange(symbol: str) -> str:
    """Strip exchange prefix (e.g. NAS:AAPL → AAPL) for endpoints where plain ticker is safer."""
    return symbol.split(":")[-1] if ":" in symbol else symbol


def get_fundamentals(symbol: str) -> Dict:
    return gf_request(f"stocks/{_strip_exchange(symbol)}/fundamentals")

def get_rankings(symbol: str) -> Dict:
    return gf_request(f"stocks/{_strip_exchange(symbol)}/rankings")

def get_profile(symbol: str) -> Dict:
    return gf_request(f"stocks/{_strip_exchange(symbol)}/profile")

def get_valuations(symbol: str) -> Dict:
    return gf_request(f"stocks/{_strip_exchange(symbol)}/valuations")

def get_segment(symbol: str) -> Dict:
    return gf_request(f"stocks/{_strip_exchange(symbol)}/segment")

def get_news(symbol: str) -> Dict:
    return gf_request(f"stocks/{_strip_exchange(symbol)}/news")

def get_guru_list(page: int = 1, per_page: int = 100) -> Dict:
    return gf_request("gurus/list", params={"page": page, "per_page": per_page})

def get_guru_data(guru_id: str) -> Dict:
    return gf_request(f"gurus/{guru_id}")

def get_insider_data(date: str) -> Dict:
    return gf_request(f"insiders/{date}")

def get_etf_data(symbol: str) -> Dict:
    return gf_request(f"etf/{symbol}")

def get_fund_letters(quarter: str) -> Dict:
    return gf_request(f"fund_letter/{quarter}")

def get_stocks_by_region(region: str) -> Dict:
    return gf_request(f"stocks/{region}")

def get_data_packages() -> Dict:
    return gf_request("download/list")

def get_download_url(package_id: str) -> Dict:
    return gf_request(f"download/{package_id}")

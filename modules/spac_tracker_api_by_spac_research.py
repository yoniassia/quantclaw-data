"""
SPAC Tracker — SPAC Research (spacresearch.com)

Data Source: SPAC Research (https://spacresearch.com)
Update: Real-time (announcements), daily (metrics)
Free tier: 200 calls/hour, free for non-commercial use with registration
History: 2017-present (modern SPAC era)

Provides:
- Active SPAC listings with ticker, sponsor, trust size
- Merger/DA announcements and target companies
- Redemption percentages and warrant details
- Post-merger (de-SPAC) performance tracking
- SPAC pipeline and IPO stats

Usage as Indicators:
- High SPAC issuance → risk appetite / speculative froth
- Rising redemption rates → investor skepticism
- Post-merger performance → de-SPAC quality signal
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os
import time

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://api.spacresearch.com"
WEB_URL = "https://spacresearch.com"

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/spac_research")
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Optional API token from environment (free tier registration)
API_TOKEN = os.environ.get("SPAC_RESEARCH_API_KEY", "")


def _get_headers() -> Dict[str, str]:
    """Build request headers, include auth token if available."""
    h = dict(HEADERS)
    if API_TOKEN:
        h["Authorization"] = f"Bearer {API_TOKEN}"
    return h


def _cache_get(key: str, max_age_hours: float = 1.0) -> Optional[Any]:
    """Read from disk cache if fresh enough."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if not os.path.exists(path):
        return None
    age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
    if age > timedelta(hours=max_age_hours):
        return None
    with open(path) as f:
        return json.load(f)


def _cache_set(key: str, data: Any) -> None:
    """Write data to disk cache."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _api_get(endpoint: str, params: Optional[Dict] = None, timeout: int = 15) -> Dict:
    """
    Make authenticated GET to SPAC Research API.
    Returns parsed JSON or error dict.
    """
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = requests.get(url, headers=_get_headers(), params=params or {}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {resp.status_code}", "detail": str(e), "url": url}
    except requests.exceptions.ConnectionError:
        return {"error": "connection_failed", "detail": "Could not reach spacresearch.com API", "url": url}
    except requests.exceptions.Timeout:
        return {"error": "timeout", "detail": f"Request timed out after {timeout}s", "url": url}
    except Exception as e:
        return {"error": "unknown", "detail": str(e), "url": url}


def _scrape_table(path: str, cache_key: str, cache_hours: float = 1.0) -> List[Dict]:
    """
    Scrape a SPAC Research web page table as fallback when API is unavailable.
    Returns list of row dicts or empty list on failure.
    """
    cached = _cache_get(cache_key, cache_hours)
    if cached is not None:
        return cached

    url = f"{WEB_URL}/{path}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        text = resp.text

        # Try pandas HTML table parsing
        try:
            import pandas as pd
            tables = pd.read_html(text)
            if tables:
                df = tables[0]
                data = df.to_dict(orient="records")
                _cache_set(cache_key, data)
                return data
        except ImportError:
            pass
        except ValueError:
            pass

        # Fallback: basic BeautifulSoup parsing
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, "html.parser")
            table = soup.find("table")
            if not table:
                return []
            headers_tags = table.find_all("th")
            col_names = [th.get_text(strip=True) for th in headers_tags]
            rows = []
            for tr in table.find_all("tr")[1:]:
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if cells and len(cells) == len(col_names):
                    rows.append(dict(zip(col_names, cells)))
            if rows:
                _cache_set(cache_key, rows)
            return rows
        except ImportError:
            return []

    except Exception:
        return []


# ===================================================================
# Public API Functions
# ===================================================================

def get_active_spacs(year: Optional[int] = None, limit: int = 50) -> List[Dict]:
    """
    Get list of active SPACs (pre-merger, searching for targets).

    Args:
        year: Filter by IPO year (default: current year)
        limit: Max results to return

    Returns:
        List of dicts with keys: ticker, name, sponsor, trust_size,
        ipo_date, status, unit_price, common_price
    """
    yr = year or datetime.now().year
    cache_key = f"active_spacs_{yr}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached[:limit]

    # Try API first
    data = _api_get("/spacs", params={"status": "active", "year": yr, "limit": limit})
    if "error" not in data:
        result = data if isinstance(data, list) else data.get("data", data.get("results", []))
        _cache_set(cache_key, result)
        return result[:limit]

    # Fallback: scrape
    rows = _scrape_table("spacs", cache_key)
    return rows[:limit]


def get_spac_by_ticker(ticker: str) -> Dict:
    """
    Get detailed SPAC info by ticker symbol.

    Args:
        ticker: SPAC ticker (e.g. 'PSTH', 'IPOF')

    Returns:
        Dict with: ticker, name, sponsor, trust_size, trust_per_share,
        ipo_date, target, merger_date, status, warrants, redemption_pct
    """
    ticker = ticker.upper().strip()
    cache_key = f"spac_detail_{ticker}"
    cached = _cache_get(cache_key, max_age_hours=0.5)
    if cached is not None:
        return cached

    data = _api_get(f"/spacs/{ticker}")
    if "error" not in data:
        _cache_set(cache_key, data)
        return data

    # Fallback: search in active list
    all_spacs = get_active_spacs(limit=500)
    for s in all_spacs:
        t = s.get("ticker", s.get("Ticker", s.get("Symbol", ""))).upper()
        if t == ticker:
            _cache_set(cache_key, s)
            return s

    return {"error": "not_found", "ticker": ticker, "detail": "SPAC not found"}


def get_merger_announcements(
    status: str = "definitive_agreement",
    year: Optional[int] = None,
    limit: int = 50
) -> List[Dict]:
    """
    Get SPAC merger announcements (LOI or DA).

    Args:
        status: 'definitive_agreement', 'letter_of_intent', or 'all'
        year: Filter year (default: current)
        limit: Max results

    Returns:
        List of dicts: spac_ticker, target_company, announcement_date,
        merger_date, deal_value, status
    """
    yr = year or datetime.now().year
    cache_key = f"mergers_{status}_{yr}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached[:limit]

    data = _api_get("/mergers", params={"status": status, "year": yr, "limit": limit})
    if "error" not in data:
        result = data if isinstance(data, list) else data.get("data", data.get("results", []))
        _cache_set(cache_key, result)
        return result[:limit]

    rows = _scrape_table("merger-tracker", cache_key)
    return rows[:limit]


def get_redemption_data(year: Optional[int] = None, limit: int = 50) -> List[Dict]:
    """
    Get SPAC redemption rates (% of shares redeemed at merger vote).

    High redemption rates (>80%) signal investor skepticism about the deal.

    Args:
        year: Filter year
        limit: Max results

    Returns:
        List of dicts: ticker, target, redemption_pct, trust_remaining,
        merger_date, trust_size
    """
    yr = year or datetime.now().year
    cache_key = f"redemptions_{yr}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached[:limit]

    data = _api_get("/redemptions", params={"year": yr, "limit": limit})
    if "error" not in data:
        result = data if isinstance(data, list) else data.get("data", data.get("results", []))
        _cache_set(cache_key, result)
        return result[:limit]

    rows = _scrape_table("redemptions", cache_key)
    return rows[:limit]


def get_warrant_data(ticker: str) -> Dict:
    """
    Get warrant details for a specific SPAC.

    Args:
        ticker: SPAC ticker (e.g. 'PSTH')

    Returns:
        Dict with: warrant_ticker, strike_price, expiration,
        warrant_price, exercise_ratio, redemption_terms
    """
    ticker = ticker.upper().strip()
    cache_key = f"warrant_{ticker}"
    cached = _cache_get(cache_key, max_age_hours=2.0)
    if cached is not None:
        return cached

    data = _api_get(f"/warrants/{ticker}")
    if "error" not in data:
        _cache_set(cache_key, data)
        return data

    return {
        "error": "not_found",
        "ticker": ticker,
        "detail": "Warrant data not available. Try get_spac_by_ticker() for basic info."
    }


def get_post_merger_performance(
    period_days: int = 90,
    year: Optional[int] = None,
    limit: int = 50
) -> List[Dict]:
    """
    Get de-SPAC performance (stock returns after merger completion).

    Args:
        period_days: Performance window (30, 90, 180, 365)
        year: Merger completion year
        limit: Max results

    Returns:
        List of dicts: ticker, former_spac, target_company,
        merger_date, return_pct, current_price, ipo_price
    """
    yr = year or datetime.now().year
    cache_key = f"despac_perf_{period_days}d_{yr}"
    cached = _cache_get(cache_key, max_age_hours=6.0)
    if cached is not None:
        return cached[:limit]

    data = _api_get("/performance", params={
        "period": period_days, "year": yr, "limit": limit
    })
    if "error" not in data:
        result = data if isinstance(data, list) else data.get("data", data.get("results", []))
        _cache_set(cache_key, result)
        return result[:limit]

    rows = _scrape_table("performance", cache_key, cache_hours=6.0)
    return rows[:limit]


def get_spac_pipeline_stats(year: Optional[int] = None) -> Dict:
    """
    Get aggregate SPAC pipeline statistics.

    Args:
        year: Stats year (default: current)

    Returns:
        Dict with: total_ipos, total_trust_value, avg_trust_size,
        mergers_completed, mergers_pending, liquidations,
        avg_redemption_pct, avg_post_merger_return
    """
    yr = year or datetime.now().year
    cache_key = f"pipeline_stats_{yr}"
    cached = _cache_get(cache_key, max_age_hours=12.0)
    if cached is not None:
        return cached

    data = _api_get("/stats", params={"year": yr})
    if "error" not in data:
        _cache_set(cache_key, data)
        return data

    return {
        "year": yr,
        "source": "spacresearch.com",
        "error": "stats_unavailable",
        "detail": "API/scrape failed. Register at spacresearch.com for API access."
    }


def search_spacs(query: str, limit: int = 20) -> List[Dict]:
    """
    Search SPACs by name, ticker, sponsor, or target company.

    Args:
        query: Search term
        limit: Max results

    Returns:
        List of matching SPAC dicts
    """
    cache_key = f"search_{query.lower().replace(' ', '_')[:30]}"
    cached = _cache_get(cache_key, max_age_hours=0.25)
    if cached is not None:
        return cached[:limit]

    data = _api_get("/search", params={"q": query, "limit": limit})
    if "error" not in data:
        result = data if isinstance(data, list) else data.get("data", data.get("results", []))
        _cache_set(cache_key, result)
        return result[:limit]

    # Fallback: filter active SPACs locally
    all_spacs = get_active_spacs(limit=500)
    q = query.lower()
    matches = []
    for s in all_spacs:
        searchable = json.dumps(s).lower()
        if q in searchable:
            matches.append(s)
    if matches:
        _cache_set(cache_key, matches)
    return matches[:limit]


def get_spac_ipo_calendar(months_ahead: int = 3) -> List[Dict]:
    """
    Get upcoming SPAC IPO calendar (filed / expected to price).

    Args:
        months_ahead: Look-ahead window in months (1-12)

    Returns:
        List of dicts: name, expected_date, trust_size, sponsor,
        underwriter, status
    """
    cache_key = f"ipo_calendar_{months_ahead}m"
    cached = _cache_get(cache_key, max_age_hours=4.0)
    if cached is not None:
        return cached

    data = _api_get("/ipo-calendar", params={"months": months_ahead})
    if "error" not in data:
        result = data if isinstance(data, list) else data.get("data", data.get("results", []))
        _cache_set(cache_key, result)
        return result

    rows = _scrape_table("ipo-calendar", cache_key, cache_hours=4.0)
    return rows


# ===================================================================
# Convenience / Quant Signal Functions
# ===================================================================

def get_spac_sentiment_signals() -> Dict:
    """
    Derive aggregate SPAC market sentiment signals.

    Returns:
        Dict with:
        - avg_redemption_pct: Higher = more skepticism
        - despac_avg_return: Post-merger avg return
        - pipeline_health: 'hot' / 'neutral' / 'cold'
        - signal_summary: Human-readable assessment
    """
    stats = get_spac_pipeline_stats()
    redemptions = get_redemption_data(limit=20)
    performance = get_post_merger_performance(period_days=90, limit=20)

    # Calculate average redemption
    redemption_values = []
    for r in redemptions:
        pct = r.get("redemption_pct", r.get("Redemption %", r.get("Redemption", None)))
        if pct is not None:
            try:
                val = float(str(pct).replace("%", "").strip())
                redemption_values.append(val)
            except (ValueError, TypeError):
                pass

    avg_redemption = sum(redemption_values) / len(redemption_values) if redemption_values else None

    # Calculate average post-merger return
    return_values = []
    for p in performance:
        ret = p.get("return_pct", p.get("Return", p.get("Performance", None)))
        if ret is not None:
            try:
                val = float(str(ret).replace("%", "").replace("+", "").strip())
                return_values.append(val)
            except (ValueError, TypeError):
                pass

    avg_return = sum(return_values) / len(return_values) if return_values else None

    # Determine pipeline health
    pipeline_health = "unknown"
    if avg_redemption is not None:
        if avg_redemption > 80:
            pipeline_health = "cold"
        elif avg_redemption > 50:
            pipeline_health = "neutral"
        else:
            pipeline_health = "hot"

    signal = {
        "timestamp": datetime.now().isoformat(),
        "avg_redemption_pct": round(avg_redemption, 1) if avg_redemption else None,
        "despac_avg_return_90d": round(avg_return, 2) if avg_return else None,
        "pipeline_health": pipeline_health,
        "sample_size_redemptions": len(redemption_values),
        "sample_size_performance": len(return_values),
        "signal_summary": (
            f"SPAC market is {pipeline_health}. "
            f"Avg redemption: {round(avg_redemption,1) if avg_redemption else 'N/A'}%, "
            f"Avg 90d de-SPAC return: {round(avg_return,1) if avg_return else 'N/A'}%."
        ),
        "source": "spacresearch.com"
    }
    return signal


# ===================================================================
# Module metadata
# ===================================================================

MODULE_INFO = {
    "name": "spac_tracker_api_by_spac_research",
    "source": "https://spacresearch.com",
    "category": "IPO & Private Markets",
    "update_frequency": "real-time",
    "free_tier": True,
    "rate_limit": "200 calls/hour",
    "requires_key": False,  # Key optional, enhances access
    "env_var": "SPAC_RESEARCH_API_KEY",
    "functions": [
        "get_active_spacs",
        "get_spac_by_ticker",
        "get_merger_announcements",
        "get_redemption_data",
        "get_warrant_data",
        "get_post_merger_performance",
        "get_spac_pipeline_stats",
        "search_spacs",
        "get_spac_ipo_calendar",
        "get_spac_sentiment_signals",
    ]
}


if __name__ == "__main__":
    print(json.dumps(MODULE_INFO, indent=2))
    print("\n--- Testing get_active_spacs() ---")
    result = get_active_spacs(limit=3)
    print(json.dumps(result[:3] if result else {"status": "no data (API may require registration)"}, indent=2, default=str))

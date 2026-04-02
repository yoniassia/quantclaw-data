#!/usr/bin/env python3
"""
GDELT Global Event Database Module

The world's largest open database of human society — monitors broadcast, print,
and web news from nearly every country in 100+ languages. Provides real-time
geopolitical risk signals, country-level sentiment, event frequency data,
and media coverage analysis for financial markets.

Data Source: https://api.gdeltproject.org/api/v2/doc/doc
Protocol: REST (GET with query parameters)
Auth: None (fully open, no key required)
Formats: JSON
Rate limits: Fair use (~5s between requests)
Coverage: Global, 100+ languages, updates every 15 minutes

Author: QUANTCLAW DATA Build Agent
Initiative: 0047
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "gdelt_global_events"
CACHE_TTL_HOURS = 1
REQUEST_TIMEOUT = 45
REQUEST_DELAY = 6

# GDELT uses FIPS 10-4 country codes (NOT ISO 3166)
FIPS_CODES = {
    "US": "United States", "CH": "China", "RS": "Russia", "UK": "United Kingdom",
    "GM": "Germany", "FR": "France", "JA": "Japan", "IN": "India",
    "BR": "Brazil", "AS": "Australia", "CA": "Canada", "KS": "South Korea",
    "SA": "Saudi Arabia", "IR": "Iran", "IS": "Israel", "TU": "Turkey",
    "MX": "Mexico", "SF": "South Africa", "NI": "Nigeria", "EG": "Egypt",
    "UP": "Ukraine", "PL": "Poland", "TW": "Taiwan", "TH": "Thailand",
    "ID": "Indonesia", "AR": "Argentina", "IT": "Italy", "SP": "Spain",
    "NL": "Netherlands", "SW": "Sweden", "SZ": "Switzerland", "NO": "Norway",
    "PK": "Pakistan", "DA": "Denmark", "FI": "Finland", "BE": "Belgium",
}

ISO_TO_FIPS = {
    "CN": "CH", "RU": "RS", "GB": "UK", "DE": "GM", "JP": "JA",
    "AU": "AS", "KR": "KS", "TR": "TU", "ZA": "SF", "NG": "NI",
    "UA": "UP", "ES": "SP", "SE": "SW", "DK": "DA",
}

FIPS_NAMES_TO_CODES = {v.lower(): k for k, v in FIPS_CODES.items()}

CONFLICT_THEMES = [
    "TERROR", "KILL", "PROTEST", "MILITARY", "ARMED_CONFLICT",
    "CRISISLEX_CRISISLEXREC", "MANMADE_DISASTER",
]

ECON_THEMES = [
    "ECON_BANKRUPTCY", "ECON_COST_OF_LIVING", "ECON_DEBT",
    "ECON_INFLATION", "ECON_INTEREST_RATE", "ECON_STOCKMARKET",
    "ECON_TRADE", "ECON_SUBSIDIES", "ECON_CURRENCY",
    "ECON_HOUSING_PRICES", "ECON_EARNINGSREPORT",
]

INDICATORS = {
    # --- Geopolitical Risk (single-theme queries for reliability) ---
    "PROTEST_ACTIVITY_GLOBAL": {
        "query": "theme:PROTEST",
        "mode": "timelinevol",
        "name": "Global Protest Activity Index",
        "description": "Volume intensity of protest-related media coverage worldwide",
        "frequency": "hourly",
        "unit": "volume %",
        "timespan": "7d",
    },
    "PROTEST_SENTIMENT": {
        "query": "theme:PROTEST",
        "mode": "timelinetone",
        "name": "Global Protest Sentiment (average tone)",
        "description": "Average media tone for protest coverage; more negative = more hostile events",
        "frequency": "hourly",
        "unit": "tone score",
        "timespan": "7d",
    },
    "MILITARY_ACTIVITY_GLOBAL": {
        "query": "theme:MILITARY",
        "mode": "timelinevol",
        "name": "Global Military Activity Index",
        "description": "Volume intensity of military-related media coverage worldwide",
        "frequency": "hourly",
        "unit": "volume %",
        "timespan": "7d",
    },
    "TERROR_THREAT_GLOBAL": {
        "query": "theme:TERROR",
        "mode": "timelinevol",
        "name": "Global Terror Threat Index",
        "description": "Volume intensity of terrorism-related media coverage worldwide",
        "frequency": "hourly",
        "unit": "volume %",
        "timespan": "7d",
    },
    "ARMED_CONFLICT_VOL": {
        "query": "theme:ARMED_CONFLICT",
        "mode": "timelinevol",
        "name": "Armed Conflict Media Volume",
        "description": "Volume intensity of armed conflict coverage in global media",
        "frequency": "hourly",
        "unit": "volume %",
        "timespan": "7d",
    },
    # --- Economic Themes ---
    "INFLATION_MEDIA_VOL": {
        "query": "theme:ECON_INFLATION",
        "mode": "timelinevol",
        "name": "Inflation Media Coverage Volume",
        "description": "Volume intensity of inflation-related articles in global media",
        "frequency": "hourly",
        "unit": "volume %",
        "timespan": "7d",
    },
    "INFLATION_SENTIMENT": {
        "query": "theme:ECON_INFLATION",
        "mode": "timelinetone",
        "name": "Inflation Media Sentiment",
        "description": "Average tone of inflation-related media coverage",
        "frequency": "hourly",
        "unit": "tone score",
        "timespan": "7d",
    },
    "INTEREST_RATE_MEDIA_VOL": {
        "query": "theme:ECON_INTEREST_RATE",
        "mode": "timelinevol",
        "name": "Interest Rate Media Coverage Volume",
        "description": "Volume intensity of interest rate articles in global media",
        "frequency": "hourly",
        "unit": "volume %",
        "timespan": "7d",
    },
    "TRADE_MEDIA_VOL": {
        "query": "theme:ECON_TRADE",
        "mode": "timelinevol",
        "name": "Trade Policy Media Volume",
        "description": "Volume intensity of trade policy media coverage (tariffs, agreements, disputes)",
        "frequency": "hourly",
        "unit": "volume %",
        "timespan": "7d",
    },
    "TRADE_SENTIMENT": {
        "query": "theme:ECON_TRADE",
        "mode": "timelinetone",
        "name": "Trade Policy Sentiment",
        "description": "Average media tone for trade policy coverage",
        "frequency": "hourly",
        "unit": "tone score",
        "timespan": "7d",
    },
    "STOCKMARKET_MEDIA_VOL": {
        "query": "theme:ECON_STOCKMARKET",
        "mode": "timelinevol",
        "name": "Stock Market Media Coverage Volume",
        "description": "Volume intensity of stock market / equity coverage in global media",
        "frequency": "hourly",
        "unit": "volume %",
        "timespan": "7d",
    },
    "STOCKMARKET_SENTIMENT": {
        "query": "theme:ECON_STOCKMARKET",
        "mode": "timelinetone",
        "name": "Stock Market Media Sentiment",
        "description": "Average media tone for stock market coverage; negative = bearish tone",
        "frequency": "hourly",
        "unit": "tone score",
        "timespan": "7d",
    },
    "BANKRUPTCY_MEDIA_VOL": {
        "query": "theme:ECON_BANKRUPTCY",
        "mode": "timelinevol",
        "name": "Bankruptcy / Default Media Volume",
        "description": "Volume intensity of bankruptcy and default coverage — stress signal",
        "frequency": "hourly",
        "unit": "volume %",
        "timespan": "7d",
    },
    # --- Commodity / Disruption ---
    "SANCTIONS_MEDIA_VOL": {
        "query": "sanctions",
        "mode": "timelinevol",
        "name": "Sanctions Media Coverage Volume",
        "description": "Volume intensity of sanctions-related media coverage",
        "frequency": "hourly",
        "unit": "volume %",
        "timespan": "7d",
    },
}


def _resolve_country(code_or_name: str) -> str:
    """Resolve country input (FIPS, ISO, or name) to FIPS two-letter code."""
    upper = code_or_name.upper().strip()
    if upper in FIPS_CODES:
        return upper
    if upper in ISO_TO_FIPS:
        return ISO_TO_FIPS[upper]
    lower = code_or_name.lower().strip()
    if lower in FIPS_NAMES_TO_CODES:
        return FIPS_NAMES_TO_CODES[lower]
    for name, code in FIPS_NAMES_TO_CODES.items():
        if lower in name or name in lower:
            return code
    return upper


def _cache_path(key: str, params_hash: str) -> Path:
    safe = key.replace("/", "_").replace(" ", "_")[:80]
    return CACHE_DIR / f"{safe}_{params_hash}.json"


def _params_hash(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def _read_cache(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(hours=CACHE_TTL_HOURS):
            return data
    except (json.JSONDecodeError, ValueError, OSError):
        pass
    return None


def _write_cache(path: Path, data: Dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        to_write = {**data, "_cached_at": datetime.now().isoformat()}
        path.write_text(json.dumps(to_write, default=str))
    except OSError:
        pass


def _api_request(query: str, mode: str, timespan: str = "7d",
                 fmt: str = "json", maxrecords: int = 250) -> Dict:
    """Make a single GDELT DOC API request."""
    params = {
        "query": query,
        "mode": mode,
        "format": fmt,
        "timespan": timespan,
    }
    if mode == "artlist":
        params["maxrecords"] = maxrecords
        params["sort"] = "datedesc"
    try:
        resp = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        text = resp.text.strip()
        if not text or text.startswith("Please limit"):
            return {"success": False, "error": "Rate limited — retry after delay"}
        data = resp.json()
        if not data:
            return {"success": False, "error": "Empty response from GDELT"}
        return {"success": True, "data": data}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out (GDELT can be slow)"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except (json.JSONDecodeError, ValueError):
        return {"success": False, "error": "Invalid JSON response"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _api_request_with_retry(query: str, mode: str, timespan: str = "7d",
                            fmt: str = "json", maxrecords: int = 250,
                            retries: int = 2) -> Dict:
    """Request with retry on rate limiting."""
    for attempt in range(retries + 1):
        result = _api_request(query, mode, timespan, fmt, maxrecords)
        if result["success"]:
            return result
        if "Rate limited" in result.get("error", "") and attempt < retries:
            time.sleep(REQUEST_DELAY * (attempt + 1))
            continue
        return result
    return result


def _parse_timeline(raw: Dict) -> List[Dict]:
    """Extract date/value pairs from timeline response."""
    try:
        timeline = raw.get("timeline", [])
        if not timeline:
            return []
        series = timeline[0]
        data_points = series.get("data", [])
        results = []
        for dp in data_points:
            results.append({
                "date": dp["date"],
                "value": dp["value"],
            })
        return results
    except (KeyError, IndexError, TypeError):
        return []


def _aggregate_timeline(points: List[Dict]) -> Dict:
    """Compute summary statistics from a timeline."""
    if not points:
        return {}
    values = [p["value"] for p in points]
    n = len(values)
    mean_val = sum(values) / n
    sorted_vals = sorted(values)
    median_val = sorted_vals[n // 2] if n % 2 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2

    recent_24h = values[-24:] if len(values) >= 24 else values
    recent_mean = sum(recent_24h) / len(recent_24h)

    return {
        "current": round(values[-1], 4),
        "mean_7d": round(mean_val, 4),
        "median_7d": round(median_val, 4),
        "min_7d": round(min(values), 4),
        "max_7d": round(max(values), 4),
        "std_7d": round((sum((v - mean_val) ** 2 for v in values) / n) ** 0.5, 4),
        "mean_24h": round(recent_mean, 4),
        "latest_date": points[-1]["date"],
        "data_points": n,
    }


def _parse_articles(raw: Dict) -> List[Dict]:
    """Extract article metadata from artlist response."""
    articles = raw.get("articles", [])
    return [
        {
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "date": a.get("seendate", ""),
            "domain": a.get("domain", ""),
            "language": a.get("language", ""),
            "source_country": a.get("sourcecountry", ""),
        }
        for a in articles
    ]


# ── Public API ──────────────────────────────────────────────────────────────


def fetch_data(indicator: str) -> Dict:
    """Fetch a specific pre-defined indicator."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}",
                "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_key = {"indicator": indicator}
    cp = _cache_path(indicator, _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request_with_retry(cfg["query"], cfg["mode"], cfg.get("timespan", "7d"))
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": result["error"]}

    points = _parse_timeline(result["data"])
    if not points:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": "No data points returned"}

    stats = _aggregate_timeline(points)
    series_name = result["data"].get("timeline", [{}])[0].get("series", cfg["mode"])

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "series": series_name,
        "summary": stats,
        "timeline": [{"date": p["date"], "value": round(p["value"], 4)} for p in points[-72:]],
        "query": cfg["query"],
        "source": "GDELT Project DOC 2.0 API",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "mode": v["mode"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all indicators."""
    if indicator:
        return fetch_data(indicator)

    results = {}
    errors = []
    for key in INDICATORS:
        data = fetch_data(key)
        if data.get("success"):
            results[key] = {
                "name": data["name"],
                "current": data["summary"]["current"],
                "mean_7d": data["summary"]["mean_7d"],
                "unit": data["unit"],
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "GDELT Project — Global Event Database",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def country_risk(country: str, timespan: str = "7d") -> Dict:
    """
    Geopolitical risk index for a specific country.
    Combines conflict theme volume + sentiment for the given country.
    """
    code = _resolve_country(country)
    country_name = FIPS_CODES.get(code, code)

    cache_key = {"cmd": "country_risk", "country": code, "timespan": timespan}
    cp = _cache_path(f"country_risk_{code}", _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    vol_q = f"sourcecountry:{code}"
    tone_q = f"sourcecountry:{code}"

    vol_result = _api_request_with_retry(vol_q, "timelinevol", timespan)
    time.sleep(REQUEST_DELAY)
    tone_result = _api_request_with_retry(tone_q, "timelinetone", timespan)

    vol_points = _parse_timeline(vol_result.get("data", {})) if vol_result["success"] else []
    tone_points = _parse_timeline(tone_result.get("data", {})) if tone_result["success"] else []

    if not vol_points and not tone_points:
        return {"success": False, "country": code, "country_name": country_name,
                "error": "No data returned for this country"}

    vol_stats = _aggregate_timeline(vol_points) if vol_points else {}
    tone_stats = _aggregate_timeline(tone_points) if tone_points else {}

    risk_score = None
    if vol_stats and tone_stats:
        vol_z = (vol_stats["current"] - vol_stats["mean_7d"]) / max(vol_stats["std_7d"], 0.001)
        tone_z = (tone_stats["mean_7d"] - tone_stats["current"]) / max(abs(tone_stats["std_7d"]), 0.001)
        risk_score = round(50 + 10 * (vol_z + tone_z) / 2, 2)
        risk_score = max(0, min(100, risk_score))

    response = {
        "success": True,
        "country": code,
        "country_name": country_name,
        "risk_score": risk_score,
        "risk_interpretation": _interpret_risk(risk_score) if risk_score is not None else None,
        "conflict_volume": vol_stats,
        "conflict_sentiment": tone_stats,
        "volume_timeline": [{"date": p["date"], "value": round(p["value"], 4)} for p in vol_points[-48:]],
        "tone_timeline": [{"date": p["date"], "value": round(p["value"], 4)} for p in tone_points[-48:]],
        "source": "GDELT Project DOC 2.0 API",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def tension(country_a: str, country_b: str, timespan: str = "7d") -> Dict:
    """
    Bilateral tension score between two countries.
    Measures tone of media from country A mentioning country B (and vice versa).
    """
    code_a = _resolve_country(country_a)
    code_b = _resolve_country(country_b)
    name_a = FIPS_CODES.get(code_a, code_a)
    name_b = FIPS_CODES.get(code_b, code_b)

    cache_key = {"cmd": "tension", "a": code_a, "b": code_b, "timespan": timespan}
    cp = _cache_path(f"tension_{code_a}_{code_b}", _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    q_a_about_b = f'sourcecountry:{code_a} "{name_b}"'
    q_b_about_a = f'sourcecountry:{code_b} "{name_a}"'

    r_ab = _api_request_with_retry(q_a_about_b, "timelinetone", timespan)
    time.sleep(REQUEST_DELAY)
    r_ba = _api_request_with_retry(q_b_about_a, "timelinetone", timespan)
    time.sleep(REQUEST_DELAY)

    vol_ab = _api_request_with_retry(q_a_about_b, "timelinevol", timespan)

    tone_ab = _parse_timeline(r_ab.get("data", {})) if r_ab["success"] else []
    tone_ba = _parse_timeline(r_ba.get("data", {})) if r_ba["success"] else []
    vol_ab_pts = _parse_timeline(vol_ab.get("data", {})) if vol_ab["success"] else []

    if not tone_ab and not tone_ba:
        return {"success": False, "pair": f"{code_a}-{code_b}",
                "error": "No bilateral data returned"}

    stats_ab = _aggregate_timeline(tone_ab) if tone_ab else {}
    stats_ba = _aggregate_timeline(tone_ba) if tone_ba else {}
    vol_stats = _aggregate_timeline(vol_ab_pts) if vol_ab_pts else {}

    combined_tone = None
    if stats_ab and stats_ba:
        combined_tone = round((stats_ab.get("mean_7d", 0) + stats_ba.get("mean_7d", 0)) / 2, 4)
    elif stats_ab:
        combined_tone = stats_ab.get("mean_7d")
    elif stats_ba:
        combined_tone = stats_ba.get("mean_7d")

    tension_score = None
    if combined_tone is not None:
        tension_score = round(max(0, min(100, 50 - combined_tone * 10)), 2)

    response = {
        "success": True,
        "pair": f"{code_a}-{code_b}",
        "country_a": {"code": code_a, "name": name_a},
        "country_b": {"code": code_b, "name": name_b},
        "tension_score": tension_score,
        "tension_interpretation": _interpret_tension(tension_score) if tension_score is not None else None,
        "combined_avg_tone": combined_tone,
        f"{code_a}_about_{code_b}": {
            "tone_stats": stats_ab,
            "timeline": [{"date": p["date"], "value": round(p["value"], 4)} for p in tone_ab[-48:]],
        },
        f"{code_b}_about_{code_a}": {
            "tone_stats": stats_ba,
            "timeline": [{"date": p["date"], "value": round(p["value"], 4)} for p in tone_ba[-48:]],
        },
        "coverage_volume": vol_stats,
        "source": "GDELT Project DOC 2.0 API",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def topic_sentiment(topic: str, timespan: str = "7d") -> Dict:
    """
    Media sentiment and volume for an arbitrary topic/keyword.
    Useful for tracking central bank, sanctions, trade war, etc.
    """
    cache_key = {"cmd": "topic", "topic": topic, "timespan": timespan}
    cp = _cache_path(f"topic_{topic[:40]}", _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    vol_result = _api_request_with_retry(topic, "timelinevol", timespan)
    time.sleep(REQUEST_DELAY)
    tone_result = _api_request_with_retry(topic, "timelinetone", timespan)
    time.sleep(REQUEST_DELAY)
    art_result = _api_request_with_retry(topic, "artlist", timespan, maxrecords=10)

    vol_points = _parse_timeline(vol_result.get("data", {})) if vol_result["success"] else []
    tone_points = _parse_timeline(tone_result.get("data", {})) if tone_result["success"] else []
    articles = _parse_articles(art_result.get("data", {})) if art_result["success"] else []

    if not vol_points and not tone_points:
        return {"success": False, "topic": topic,
                "error": "No data returned for this topic"}

    vol_stats = _aggregate_timeline(vol_points) if vol_points else {}
    tone_stats = _aggregate_timeline(tone_points) if tone_points else {}

    response = {
        "success": True,
        "topic": topic,
        "volume": vol_stats,
        "sentiment": tone_stats,
        "volume_timeline": [{"date": p["date"], "value": round(p["value"], 4)} for p in vol_points[-72:]],
        "tone_timeline": [{"date": p["date"], "value": round(p["value"], 4)} for p in tone_points[-72:]],
        "recent_articles": articles[:10],
        "source": "GDELT Project DOC 2.0 API",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def articles_search(query: str, maxrecords: int = 25, timespan: str = "7d") -> Dict:
    """Search for articles matching a query."""
    cache_key = {"cmd": "articles", "query": query, "max": maxrecords, "timespan": timespan}
    cp = _cache_path(f"articles_{query[:40]}", _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request_with_retry(query, "artlist", timespan, maxrecords=maxrecords)
    if not result["success"]:
        return {"success": False, "query": query, "error": result["error"]}

    articles = _parse_articles(result["data"])
    if not articles:
        return {"success": False, "query": query, "error": "No articles found"}

    response = {
        "success": True,
        "query": query,
        "articles": articles,
        "count": len(articles),
        "source": "GDELT Project DOC 2.0 API",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


# ── Helpers ─────────────────────────────────────────────────────────────────


def _interpret_risk(score: float) -> str:
    if score >= 75:
        return "ELEVATED — significantly above-normal geopolitical risk"
    if score >= 60:
        return "HIGH — above-normal geopolitical activity"
    if score >= 40:
        return "MODERATE — normal range of geopolitical activity"
    if score >= 25:
        return "LOW — below-normal geopolitical activity"
    return "MINIMAL — very low geopolitical activity"


def _interpret_tension(score: float) -> str:
    if score >= 75:
        return "SEVERE — strongly negative bilateral media tone"
    if score >= 60:
        return "HIGH — predominantly negative bilateral coverage"
    if score >= 40:
        return "MODERATE — mixed bilateral media tone"
    if score >= 25:
        return "LOW — generally neutral-to-positive coverage"
    return "MINIMAL — positive bilateral media tone"


# ── CLI ─────────────────────────────────────────────────────────────────────


def _print_help():
    print("""
GDELT Global Event Database Module (Initiative 0047)

Usage:
  python gdelt_global_events.py                             # Global geopolitical risk summary (first 3 indicators)
  python gdelt_global_events.py <INDICATOR>                 # Fetch specific indicator
  python gdelt_global_events.py list                        # List available indicators
  python gdelt_global_events.py country_risk <CC>           # Country risk index (e.g. CN, US, RU)
  python gdelt_global_events.py tension <CC1> <CC2>         # Bilateral tension (e.g. US CN)
  python gdelt_global_events.py topic "<query>"             # Topic sentiment (e.g. "central bank")
  python gdelt_global_events.py articles "<query>"          # Search articles

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print(f"""
Countries: {', '.join(f'{k}={v}' for k, v in list(FIPS_CODES.items())[:10])} ...
Source: {BASE_URL}
Rate limit: ~5s between requests (module handles automatically)
Cache: {CACHE_TTL_HOURS}h TTL
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "country_risk":
            if len(sys.argv) < 3:
                print("Usage: python gdelt_global_events.py country_risk <COUNTRY_CODE>")
                sys.exit(1)
            print(json.dumps(country_risk(sys.argv[2]), indent=2, default=str))
        elif cmd == "tension":
            if len(sys.argv) < 4:
                print("Usage: python gdelt_global_events.py tension <CC1> <CC2>")
                sys.exit(1)
            print(json.dumps(tension(sys.argv[2], sys.argv[3]), indent=2, default=str))
        elif cmd == "topic":
            if len(sys.argv) < 3:
                print("Usage: python gdelt_global_events.py topic \"<query>\"")
                sys.exit(1)
            print(json.dumps(topic_sentiment(" ".join(sys.argv[2:])), indent=2, default=str))
        elif cmd == "articles":
            if len(sys.argv) < 3:
                print("Usage: python gdelt_global_events.py articles \"<query>\"")
                sys.exit(1)
            print(json.dumps(articles_search(" ".join(sys.argv[2:])), indent=2, default=str))
        elif cmd.upper() in INDICATORS:
            print(json.dumps(fetch_data(cmd), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        print("Fetching global geopolitical risk summary (3 key indicators)...")
        summary_keys = ["PROTEST_ACTIVITY_GLOBAL", "MILITARY_ACTIVITY_GLOBAL", "PROTEST_SENTIMENT"]
        results = {}
        errors = []
        for key in summary_keys:
            data = fetch_data(key)
            if data.get("success"):
                results[key] = {
                    "name": data["name"],
                    "current": data["summary"]["current"],
                    "mean_7d": data["summary"]["mean_7d"],
                    "mean_24h": data["summary"]["mean_24h"],
                    "unit": data["unit"],
                }
            else:
                errors.append({"indicator": key, "error": data.get("error", "unknown")})
            time.sleep(REQUEST_DELAY)
        output = {
            "success": True,
            "source": "GDELT Project — Global Event Database",
            "indicators": results,
            "errors": errors if errors else None,
            "count": len(results),
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(output, indent=2, default=str))

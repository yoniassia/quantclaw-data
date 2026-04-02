#!/usr/bin/env python3
"""
OpenAlex Scholarly Research Module

Free, open catalog of 250M+ scholarly works, 100K+ journals, 100M+ authors.
Tracks research publications, citations, institutional affiliations, and topic
trends across all scientific disciplines. Alternative data for corporate R&D
output, pharma pipeline signals, technology trend detection, and university-
industry knowledge transfer.

Data Source: https://api.openalex.org
Protocol: REST (JSON)
Auth: None (polite pool with email for faster rate limits)
Refresh: Daily
Coverage: Global scholarly output

Author: QUANTCLAW DATA Build Agent
Initiative: 0060
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://api.openalex.org"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "openalex_research"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.12
POLITE_EMAIL = "data@quantclaw.org"

HEADERS = {
    "Accept": "application/json",
    "User-Agent": f"QuantClawData/1.0 (mailto:{POLITE_EMAIL})",
}

COMPANY_ROR = {
    "pfizer": {"ror": "https://ror.org/01xdqrp08", "name": "Pfizer", "ticker": "PFE"},
    "novartis": {"ror": "https://ror.org/02f9zrr09", "name": "Novartis", "ticker": "NVS"},
    "roche": {"ror": "https://ror.org/00by1q217", "name": "Roche", "ticker": "RHHBY"},
    "google": {"ror": "https://ror.org/00njsd438", "name": "Google Research", "ticker": "GOOGL"},
    "microsoft": {"ror": "https://ror.org/00d0nc645", "name": "Microsoft Research", "ticker": "MSFT"},
    "nvidia": {"ror": "https://ror.org/03fhm3131", "name": "NVIDIA", "ticker": "NVDA"},
    "samsung": {"ror": "https://ror.org/03wnk9277", "name": "Samsung Research", "ticker": "005930.KS"},
    "tsmc": {"ror": "https://ror.org/02s1m8p66", "name": "TSMC", "ticker": "TSM"},
}

INDICATORS = {
    "PFIZER_RD": {
        "type": "institution",
        "ror": "https://ror.org/01xdqrp08",
        "name": "Pfizer R&D Output (works/year)",
        "description": "Annual publication count from Pfizer-affiliated researchers",
        "frequency": "yearly",
        "unit": "publications",
    },
    "NOVARTIS_RD": {
        "type": "institution",
        "ror": "https://ror.org/02f9zrr09",
        "name": "Novartis R&D Output (works/year)",
        "description": "Annual publication count from Novartis-affiliated researchers",
        "frequency": "yearly",
        "unit": "publications",
    },
    "ROCHE_RD": {
        "type": "institution",
        "ror": "https://ror.org/00by1q217",
        "name": "Roche R&D Output (works/year)",
        "description": "Annual publication count from Roche-affiliated researchers",
        "frequency": "yearly",
        "unit": "publications",
    },
    "GOOGLE_RD": {
        "type": "institution",
        "ror": "https://ror.org/00njsd438",
        "name": "Google Research Output (works/year)",
        "description": "Annual publication count from Google Research",
        "frequency": "yearly",
        "unit": "publications",
    },
    "MICROSOFT_RD": {
        "type": "institution",
        "ror": "https://ror.org/00d0nc645",
        "name": "Microsoft Research Output (works/year)",
        "description": "Annual publication count from Microsoft Research",
        "frequency": "yearly",
        "unit": "publications",
    },
    "NVIDIA_RD": {
        "type": "institution",
        "ror": "https://ror.org/03fhm3131",
        "name": "NVIDIA Research Output (works/year)",
        "description": "Annual publication count from NVIDIA-affiliated researchers",
        "frequency": "yearly",
        "unit": "publications",
    },
    "TOPIC_MACHINE_LEARNING": {
        "type": "topic_search",
        "keyword": "machine learning",
        "name": "Machine Learning Publication Trend",
        "description": "Annual publication count for machine learning research",
        "frequency": "yearly",
        "unit": "publications",
    },
    "TOPIC_GLP1": {
        "type": "topic_search",
        "keyword": "GLP-1 receptor agonist",
        "name": "GLP-1 Drug Target Research Trend",
        "description": "Annual publication count for GLP-1 receptor agonist research",
        "frequency": "yearly",
        "unit": "publications",
    },
    "TOPIC_GENE_EDITING": {
        "type": "topic_search",
        "keyword": "CRISPR gene editing",
        "name": "CRISPR Gene Editing Research Trend",
        "description": "Annual publication count for CRISPR gene editing research",
        "frequency": "yearly",
        "unit": "publications",
    },
    "TOPIC_QUANTUM_COMPUTING": {
        "type": "topic_search",
        "keyword": "quantum computing",
        "name": "Quantum Computing Research Trend",
        "description": "Annual publication count for quantum computing research",
        "frequency": "yearly",
        "unit": "publications",
    },
    "TOPIC_SOLID_STATE_BATTERY": {
        "type": "topic_search",
        "keyword": "solid state battery",
        "name": "Solid-State Battery Research Trend",
        "description": "Annual publication count for solid-state battery research",
        "frequency": "yearly",
        "unit": "publications",
    },
}


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _cache_path(key: str, params_hash: str) -> Path:
    safe = key.replace("/", "_").replace(":", "_")
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
        data["_cached_at"] = datetime.now().isoformat()
        path.write_text(json.dumps(data, default=str))
    except OSError:
        pass


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _api_get(endpoint: str, params: dict = None) -> Dict:
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    if params is None:
        params = {}
    params["mailto"] = POLITE_EMAIL
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _paginated_get(endpoint: str, params: dict = None, max_results: int = 200) -> List[Dict]:
    """Cursor-paginated fetch. Returns list of result items."""
    if params is None:
        params = {}
    params["per_page"] = min(max_results, 200)
    items = []
    cursor = "*"

    while cursor and len(items) < max_results:
        params["cursor"] = cursor
        result = _api_get(endpoint, params)
        if not result["success"]:
            break
        data = result["data"]
        batch = data.get("results", [])
        if not batch:
            break
        items.extend(batch)
        meta = data.get("meta", {})
        cursor = meta.get("next_cursor")
        time.sleep(REQUEST_DELAY)

    return items[:max_results]


# ---------------------------------------------------------------------------
# Core data functions
# ---------------------------------------------------------------------------

def _get_institution_by_ror(ror_id: str) -> Optional[Dict]:
    """Resolve a ROR ID to an OpenAlex institution record."""
    result = _api_get("institutions", {"filter": f"ror:{ror_id}", "per_page": 1})
    if result["success"] and result["data"].get("results"):
        return result["data"]["results"][0]
    return None


def _search_institution(name: str) -> Optional[Dict]:
    """Search for an institution by name."""
    result = _api_get("institutions", {"search": name, "per_page": 1})
    if result["success"] and result["data"].get("results"):
        return result["data"]["results"][0]
    return None


def _yearly_counts_by_institution(ror_id: str, years: int = 6) -> List[Dict]:
    """Get publication counts grouped by year for an institution."""
    current_year = datetime.now().year
    start_year = current_year - years + 1
    year_range = f"{start_year}-{current_year}"
    result = _api_get("works", {
        "filter": f"authorships.institutions.ror:{ror_id},publication_year:{year_range}",
        "group_by": "publication_year",
    })
    if not result["success"]:
        return []
    groups = result["data"].get("group_by", [])
    counts = [{"year": int(g["key"]), "count": g["count"]} for g in groups if g.get("key")]
    counts.sort(key=lambda x: x["year"])
    return counts


def _yearly_counts_by_keyword(keyword: str, years: int = 6) -> List[Dict]:
    """Get publication counts grouped by year for a keyword search."""
    current_year = datetime.now().year
    start_year = current_year - years + 1
    year_range = f"{start_year}-{current_year}"
    result = _api_get("works", {
        "filter": f"default.search:{keyword},publication_year:{year_range}",
        "group_by": "publication_year",
    })
    if not result["success"]:
        return []
    groups = result["data"].get("group_by", [])
    counts = [{"year": int(g["key"]), "count": g["count"]} for g in groups if g.get("key")]
    counts.sort(key=lambda x: x["year"])
    return counts


def _top_works_by_institution(ror_id: str, year: int = None, limit: int = 10) -> List[Dict]:
    """Fetch top-cited works from an institution, optionally filtered by year."""
    filt = f"authorships.institutions.ror:{ror_id}"
    if year:
        filt += f",publication_year:{year}"
    result = _api_get("works", {
        "filter": filt,
        "sort": "cited_by_count:desc",
        "per_page": limit,
    })
    if not result["success"]:
        return []
    works = []
    for w in result["data"].get("results", []):
        works.append(_extract_work(w))
    return works


def _top_works_by_keyword(keyword: str, year: int = None, limit: int = 10) -> List[Dict]:
    """Fetch top-cited works for a keyword, optionally filtered by year."""
    filt = f"default.search:{keyword}"
    if year:
        filt += f",publication_year:{year}"
    result = _api_get("works", {
        "filter": filt,
        "sort": "cited_by_count:desc",
        "per_page": limit,
    })
    if not result["success"]:
        return []
    return [_extract_work(w) for w in result["data"].get("results", [])]


def _extract_work(w: Dict) -> Dict:
    """Extract structured fields from an OpenAlex work object."""
    institutions = []
    for authorship in (w.get("authorships") or [])[:5]:
        for inst in (authorship.get("institutions") or []):
            name = inst.get("display_name")
            if name and name not in institutions:
                institutions.append(name)

    topics = []
    for t in (w.get("topics") or [])[:3]:
        tname = t.get("display_name")
        if tname:
            topics.append(tname)

    source_name = None
    primary_loc = w.get("primary_location") or {}
    src = primary_loc.get("source") or {}
    source_name = src.get("display_name")

    return {
        "work_id": w.get("id", ""),
        "title": w.get("title", ""),
        "publication_date": w.get("publication_date", ""),
        "publication_year": w.get("publication_year"),
        "cited_by_count": w.get("cited_by_count", 0),
        "institutions": institutions,
        "topics": topics,
        "source": source_name,
        "doi": w.get("doi"),
        "type": w.get("type"),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_data(indicator: str, **kwargs) -> Dict:
    """Fetch a specific indicator series."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_key = {"indicator": indicator, **kwargs}
    cp = _cache_path(indicator, _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    if cfg["type"] == "institution":
        yearly = _yearly_counts_by_institution(cfg["ror"])
    elif cfg["type"] == "topic_search":
        yearly = _yearly_counts_by_keyword(cfg["keyword"])
    else:
        return {"success": False, "error": f"Unknown indicator type: {cfg['type']}"}

    if not yearly:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No data returned"}

    latest = yearly[-1]
    prev = yearly[-2] if len(yearly) >= 2 else None
    yoy_change = yoy_change_pct = None
    if prev and prev["count"] > 0:
        yoy_change = latest["count"] - prev["count"]
        yoy_change_pct = round((yoy_change / prev["count"]) * 100, 2)

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": latest["count"],
        "latest_period": str(latest["year"]),
        "yoy_change": yoy_change,
        "yoy_change_pct": yoy_change_pct,
        "data_points": [{"period": str(y["year"]), "value": y["count"]} for y in yearly],
        "total_observations": len(yearly),
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_available_indicators() -> List[Dict]:
    """Return list of all available indicators."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "type": v["type"],
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
                "value": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
                "yoy_change_pct": data.get("yoy_change_pct"),
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "OpenAlex Scholarly Research",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_institution(name_or_key: str) -> Dict:
    """Get institution research profile by company key or name search."""
    key = name_or_key.lower().strip()
    cp = _cache_path(f"inst_{key}", _params_hash({"institution": key}))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    inst = None
    ror_id = None
    if key in COMPANY_ROR:
        ror_id = COMPANY_ROR[key]["ror"]
        inst = _get_institution_by_ror(ror_id)
    else:
        inst = _search_institution(name_or_key)
        if inst:
            ror_id = inst.get("ror")

    if not inst:
        return {"success": False, "error": f"Institution not found: {name_or_key}",
                "available_companies": list(COMPANY_ROR.keys())}

    ror_for_query = ror_id or inst.get("ror", "")
    time.sleep(REQUEST_DELAY)
    yearly = _yearly_counts_by_institution(ror_for_query) if ror_for_query else []
    time.sleep(REQUEST_DELAY)
    top_works = _top_works_by_institution(ror_for_query, limit=5) if ror_for_query else []

    summary = inst.get("summary_stats", {})
    counts_by_year = inst.get("counts_by_year", [])

    yoy_change = yoy_change_pct = None
    if len(yearly) >= 2:
        latest_c = yearly[-1]["count"]
        prev_c = yearly[-2]["count"]
        if prev_c > 0:
            yoy_change = latest_c - prev_c
            yoy_change_pct = round((yoy_change / prev_c) * 100, 2)

    response = {
        "success": True,
        "institution": {
            "openalex_id": inst.get("id", ""),
            "display_name": inst.get("display_name", ""),
            "ror": ror_id,
            "country_code": inst.get("country_code", ""),
            "type": inst.get("type", ""),
            "works_count": inst.get("works_count", 0),
            "cited_by_count": inst.get("cited_by_count", 0),
            "h_index": summary.get("h_index"),
            "i10_index": summary.get("i10_index"),
            "2yr_mean_citedness": summary.get("2yr_mean_citedness"),
        },
        "yearly_output": yearly,
        "yoy_change": yoy_change,
        "yoy_change_pct": yoy_change_pct,
        "top_works": top_works,
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_topic(keyword: str) -> Dict:
    """Get publication trend for a topic/keyword."""
    key = keyword.lower().strip()
    cp = _cache_path(f"topic_{key}", _params_hash({"topic": key}))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    yearly = _yearly_counts_by_keyword(keyword)
    if not yearly:
        return {"success": False, "error": f"No results for topic: {keyword}"}

    time.sleep(REQUEST_DELAY)
    top_works = _top_works_by_keyword(keyword, limit=5)

    time.sleep(REQUEST_DELAY)
    current_year = datetime.now().year
    inst_result = _api_get("works", {
        "filter": f"default.search:{keyword},publication_year:{current_year}",
        "group_by": "authorships.institutions.id",
    })
    top_institutions = []
    if inst_result["success"]:
        for g in (inst_result["data"].get("group_by") or [])[:10]:
            top_institutions.append({
                "institution": g.get("key_display_name", g.get("key", "")),
                "works_count": g.get("count", 0),
            })

    latest = yearly[-1]
    prev = yearly[-2] if len(yearly) >= 2 else None
    yoy_change = yoy_change_pct = None
    if prev and prev["count"] > 0:
        yoy_change = latest["count"] - prev["count"]
        yoy_change_pct = round((yoy_change / prev["count"]) * 100, 2)

    total_count = sum(y["count"] for y in yearly)

    response = {
        "success": True,
        "topic": keyword,
        "total_works": total_count,
        "yearly_trend": yearly,
        "latest_year": latest["year"],
        "latest_count": latest["count"],
        "yoy_change": yoy_change,
        "yoy_change_pct": yoy_change_pct,
        "top_institutions": top_institutions,
        "top_works": top_works,
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


TRENDING_KEYWORDS = [
    "large language model", "GLP-1 receptor agonist", "solid state battery",
    "quantum computing", "CRISPR gene editing", "CAR-T cell therapy",
    "mRNA vaccine", "nuclear fusion energy", "autonomous driving",
    "digital twin", "federated learning", "neuromorphic computing",
    "perovskite solar cell", "protein structure prediction",
    "carbon capture", "synthetic biology", "PFAS remediation",
    "robotic surgery", "brain-computer interface", "generative AI",
    "antibody drug conjugate", "small modular reactor",
    "single cell RNA sequencing", "graph neural network",
    "weight loss drug", "humanoid robot", "spatial computing",
    "6G wireless", "biodegradable plastic", "KRAS inhibitor",
]


def get_trending_topics(limit: int = 20) -> Dict:
    """Detect fastest-growing research topics by comparing full-year publication counts."""
    cp = _cache_path("trending", _params_hash({"limit": limit, "v": 2}))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    current_year = datetime.now().year
    year_a = current_year - 1
    year_b = current_year - 2

    trending = []
    for kw in TRENDING_KEYWORDS:
        counts = _yearly_counts_by_keyword(kw, years=3)
        by_year = {c["year"]: c["count"] for c in counts}
        count_a = by_year.get(year_a, 0)
        count_b = by_year.get(year_b, 0)
        count_current = by_year.get(current_year, 0)

        growth_pct = None
        if count_b > 0:
            growth_pct = round(((count_a - count_b) / count_b) * 100, 2)

        trending.append({
            "keyword": kw,
            f"works_{year_a}": count_a,
            f"works_{year_b}": count_b,
            f"works_{current_year}_partial": count_current,
            "yoy_growth_pct": growth_pct,
        })
        time.sleep(REQUEST_DELAY)

    trending = [t for t in trending if t.get("yoy_growth_pct") is not None]
    trending.sort(key=lambda x: x["yoy_growth_pct"], reverse=True)
    trending = trending[:limit]

    response = {
        "success": True,
        "trending_topics": trending,
        "count": len(trending),
        "methodology": f"YoY growth comparing {year_a} vs {year_b} (full years)",
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def company_compare(*company_keys: str) -> Dict:
    """Head-to-head R&D comparison of pre-configured companies."""
    if not company_keys:
        return {"success": False, "error": "Provide at least one company key",
                "available": list(COMPANY_ROR.keys())}

    companies = []
    errors = []
    for key in company_keys:
        key = key.lower().strip()
        if key not in COMPANY_ROR:
            errors.append(f"Unknown company: {key}")
            continue
        info = COMPANY_ROR[key]

        yearly = _yearly_counts_by_institution(info["ror"])
        time.sleep(REQUEST_DELAY)

        inst = _get_institution_by_ror(info["ror"])
        time.sleep(REQUEST_DELAY)

        summary = (inst.get("summary_stats", {}) if inst else {})
        latest = yearly[-1] if yearly else {"year": None, "count": 0}
        prev = yearly[-2] if len(yearly) >= 2 else None
        yoy_pct = None
        if prev and prev["count"] > 0:
            yoy_pct = round(((latest["count"] - prev["count"]) / prev["count"]) * 100, 2)

        companies.append({
            "key": key,
            "name": info["name"],
            "ticker": info["ticker"],
            "ror": info["ror"],
            "total_works": inst.get("works_count", 0) if inst else 0,
            "total_citations": inst.get("cited_by_count", 0) if inst else 0,
            "h_index": summary.get("h_index"),
            "2yr_mean_citedness": summary.get("2yr_mean_citedness"),
            "latest_year": latest["year"],
            "latest_year_works": latest["count"],
            "yoy_change_pct": yoy_pct,
            "yearly_output": yearly,
        })

    companies.sort(key=lambda x: x.get("latest_year_works", 0), reverse=True)

    return {
        "success": True,
        "comparison": companies,
        "count": len(companies),
        "errors": errors if errors else None,
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }


def get_country_innovation(limit: int = 20) -> Dict:
    """Country-level research output rankings."""
    cp = _cache_path("country_innovation", _params_hash({"limit": limit}))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    current_year = datetime.now().year
    result = _api_get("works", {
        "filter": f"publication_year:{current_year}",
        "group_by": "authorships.institutions.country_code",
    })
    if not result["success"]:
        return {"success": False, "error": result["error"]}

    groups = result["data"].get("group_by", [])
    if not groups:
        return {"success": False, "error": "No country data returned"}

    countries = []
    for g in groups:
        raw_key = g.get("key", "")
        if not raw_key or raw_key == "unknown":
            continue
        code = raw_key.split("/")[-1] if "/" in raw_key else raw_key
        countries.append({
            "country_code": code,
            "country_name": g.get("key_display_name", code),
            "works_count": g.get("count", 0),
            "year": current_year,
        })

    countries.sort(key=lambda x: x["works_count"], reverse=True)
    countries = countries[:limit]

    total = sum(c["works_count"] for c in countries)
    for c in countries:
        c["share_pct"] = round((c["works_count"] / total) * 100, 2) if total > 0 else 0

    response = {
        "success": True,
        "year": current_year,
        "countries": countries,
        "count": len(countries),
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_help():
    print(f"""
OpenAlex Scholarly Research Module (Initiative 0060)

Usage:
  python openalex_research.py                                   # Research trend summary (all indicators)
  python openalex_research.py <INDICATOR>                       # Fetch specific indicator
  python openalex_research.py list                              # List available indicators
  python openalex_research.py institution <name|key>            # Institution R&D profile
  python openalex_research.py topic "<keyword>"                 # Topic/keyword publication trend
  python openalex_research.py trending                          # Fastest-growing research topics
  python openalex_research.py company_compare <key1> <key2> ... # Head-to-head R&D comparison
  python openalex_research.py country_innovation                # Country-level output rankings

Pre-configured Companies:""")
    for key, info in COMPANY_ROR.items():
        print(f"  {key:<15s} {info['name']:<25s} ({info['ticker']})")
    print(f"""
Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Auth: None (polite pool with email for faster rate limits)
Docs: https://docs.openalex.org/
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ("--help", "-h", "help"):
            _print_help()

        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))

        elif cmd == "institution":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Usage: institution <name|key>", "available": list(COMPANY_ROR.keys())}))
            else:
                name = " ".join(sys.argv[2:])
                print(json.dumps(get_institution(name), indent=2, default=str))

        elif cmd == "topic":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Usage: topic <keyword>"}))
            else:
                keyword = " ".join(sys.argv[2:])
                print(json.dumps(get_topic(keyword), indent=2, default=str))

        elif cmd == "trending":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            print(json.dumps(get_trending_topics(limit), indent=2, default=str))

        elif cmd == "company_compare":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Usage: company_compare <key1> <key2> ...",
                                  "available": list(COMPANY_ROR.keys())}))
            else:
                print(json.dumps(company_compare(*sys.argv[2:]), indent=2, default=str))

        elif cmd == "country_innovation":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            print(json.dumps(get_country_innovation(limit), indent=2, default=str))

        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        print("Fetching all indicators (this may take a moment)...")
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))

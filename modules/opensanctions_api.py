#!/usr/bin/env python3
"""
OpenSanctions Global Database API Module

Aggregated sanctions lists, politically exposed persons (PEPs), and criminal
watchlists from 80+ official sources worldwide. Covers OFAC SDN, EU Consolidated
List, UN Security Council, UK HMT, and dozens more. Entity search, fuzzy matching,
dataset metadata, country-level exposure, and vessel/aircraft sanctions queries.

Data Source: https://api.opensanctions.org
Protocol: REST (JSON)
Auth: API key via Authorization header (OPENSANCTIONS_API_KEY)
Rate Limits: 50 req/day (free), 500/day (registered non-commercial)
Formats: FollowTheMoney entity format → simplified JSON

Author: QUANTCLAW DATA Build Agent
Initiative: 0064
"""

import json
import os
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://api.opensanctions.org"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "opensanctions_api"
CACHE_TTL_SEARCH = 6      # hours — search results and entity lookups
CACHE_TTL_STATS = 24       # hours — dataset catalog and aggregate statistics
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5        # conservative: stay well within rate limits

API_KEY = os.getenv("OPENSANCTIONS_API_KEY", "")

SCHEMA_TYPES = ["Person", "Company", "Organization", "LegalEntity", "Vessel", "Aircraft"]

DATASET_SCOPES = {
    "default": "All OpenSanctions data (sanctions + PEPs + crime)",
    "sanctions": "International sanctions lists only",
    "peps": "Politically exposed persons only",
    "crime": "Crime-related watchlists",
}

INDICATORS = {
    "ENTITY_SEARCH": {
        "name": "Entity Search (Sanctions/PEPs/Watchlists)",
        "description": "Search entities by name across 80+ sanctions, PEP, and watchlist datasets",
        "endpoint": "search",
        "frequency": "on-demand",
        "unit": "entities",
    },
    "ENTITY_MATCH": {
        "name": "Fuzzy Entity Matching (Compliance Screening)",
        "description": "Multi-property fuzzy matching for compliance screening (name, DOB, nationality)",
        "endpoint": "match",
        "frequency": "on-demand",
        "unit": "match score 0-1",
    },
    "ENTITY_DETAIL": {
        "name": "Entity Detail (Full Record)",
        "description": "Full entity record with all properties, datasets, sanctions details, and relationships",
        "endpoint": "entities",
        "frequency": "on-demand",
        "unit": "entity",
    },
    "DATASET_CATALOG": {
        "name": "Dataset Catalog (All Sanctions Lists)",
        "description": "Metadata for all sanctions/PEP/watchlist datasets: entity counts, coverage, update dates",
        "endpoint": "catalog",
        "frequency": "daily",
        "unit": "datasets",
    },
    "COUNTRY_EXPOSURE": {
        "name": "Country Sanctions Exposure",
        "description": "Sanctioned entity counts by country jurisdiction (Russia, Iran, DPRK, etc.)",
        "endpoint": "search",
        "frequency": "on-demand",
        "unit": "entities by country",
    },
    "PEP_SEARCH": {
        "name": "Politically Exposed Persons Search",
        "description": "Search PEPs by name, country, or position across all PEP datasets",
        "endpoint": "search",
        "frequency": "on-demand",
        "unit": "entities",
    },
    "VESSEL_SANCTIONS": {
        "name": "Sanctioned Vessels",
        "description": "Ships and maritime vessels on international sanctions lists",
        "endpoint": "search",
        "frequency": "on-demand",
        "unit": "vessels",
    },
    "NEW_DESIGNATIONS": {
        "name": "Recent Designations (New Sanctions)",
        "description": "Entities recently added to sanctions lists — signals escalation events",
        "endpoint": "search",
        "frequency": "daily",
        "unit": "entities",
    },
}


# --- Caching ---

def _cache_path(key: str, params_hash: str) -> Path:
    safe = key.replace("/", "_").replace(" ", "_")
    return CACHE_DIR / f"{safe}_{params_hash}.json"


def _params_hash(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _read_cache(path: Path, ttl_hours: int) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(hours=ttl_hours):
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


# --- API helpers ---

def _get_session() -> requests.Session:
    s = requests.Session()
    if API_KEY:
        s.headers["Authorization"] = f"ApiKey {API_KEY}"
    s.headers["Accept"] = "application/json"
    return s


def _api_get(path: str, params: dict = None) -> Dict:
    url = f"{BASE_URL}{path}"
    try:
        session = _get_session()
        resp = session.get(url, params=params or {}, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 429:
            return {"success": False, "error": "Rate limit exceeded (429). Try again later or use cached data."}
        if resp.status_code == 401:
            return {"success": False, "error": "Authentication failed. Set OPENSANCTIONS_API_KEY in .env"}
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


def _api_post(path: str, json_body: dict, params: dict = None) -> Dict:
    url = f"{BASE_URL}{path}"
    try:
        session = _get_session()
        resp = session.post(url, json=json_body, params=params or {}, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 429:
            return {"success": False, "error": "Rate limit exceeded (429). Try again later or use cached data."}
        if resp.status_code == 401:
            return {"success": False, "error": "Authentication failed. Set OPENSANCTIONS_API_KEY in .env"}
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


# --- Entity parsing (FollowTheMoney → simplified JSON) ---

def _simplify_entity(entity: Dict) -> Dict:
    """Convert FollowTheMoney entity format to simplified, readable JSON."""
    props = entity.get("properties", {})

    def _first(key: str) -> Optional[str]:
        vals = props.get(key, [])
        return vals[0] if vals else None

    def _all(key: str) -> List[str]:
        return props.get(key, [])

    schema = entity.get("schema", "Thing")
    simplified = {
        "id": entity.get("id"),
        "caption": entity.get("caption"),
        "schema": schema,
        "datasets": entity.get("datasets", []),
        "first_seen": entity.get("first_seen"),
        "last_seen": entity.get("last_seen"),
        "last_change": entity.get("last_change"),
        "topics": _all("topics") or entity.get("topics", []),
        "countries": _all("country") or _all("jurisdiction") or _all("nationality"),
        "score": entity.get("score"),
    }

    if schema == "Person":
        simplified.update({
            "name": _first("name"),
            "birth_date": _first("birthDate"),
            "nationality": _all("nationality"),
            "position": _first("position"),
            "gender": _first("gender"),
        })
    elif schema in ("Company", "Organization", "LegalEntity"):
        simplified.update({
            "name": _first("name"),
            "jurisdiction": _first("jurisdiction"),
            "registration_number": _first("registrationNumber"),
            "incorporation_date": _first("incorporationDate"),
        })
    elif schema == "Vessel":
        simplified.update({
            "name": _first("name"),
            "imo_number": _first("imoNumber"),
            "mmsi": _first("mmsiNumber"),
            "flag": _first("flag"),
            "vessel_type": _first("type"),
            "tonnage": _first("tonnage"),
        })
    elif schema == "Aircraft":
        simplified.update({
            "name": _first("name"),
            "registration": _first("registrationNumber"),
            "model": _first("model"),
            "serial_number": _first("serialNumber"),
        })
    else:
        simplified["name"] = _first("name") or entity.get("caption")

    return {k: v for k, v in simplified.items() if v is not None}


# --- Core API functions ---

def search_entities(query: str, schema: str = None, dataset: str = "default",
                    limit: int = 20, countries: List[str] = None,
                    topics: List[str] = None, changed_since: str = None) -> Dict:
    """Search entities by name across all sanctions/PEP/watchlist datasets."""
    cache_key = f"search_{dataset}_{schema or 'all'}"
    cache_params = {"q": query, "schema": schema, "limit": limit,
                    "countries": countries, "topics": topics, "changed_since": changed_since}
    cp = _cache_path(cache_key, _params_hash(cache_params))
    cached = _read_cache(cp, CACHE_TTL_SEARCH)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {"q": query, "limit": limit}
    if schema:
        params["schema"] = schema
    if countries:
        for c in countries:
            params.setdefault("countries", [])
            params["countries"].append(c.lower())
    if topics:
        params["topics"] = topics
    if changed_since:
        params["changed_since"] = changed_since

    result = _api_get(f"/search/{dataset}", params)
    if not result["success"]:
        return {"success": False, "query": query, "error": result["error"]}

    data = result["data"]
    results = data.get("results", [])
    facets = data.get("facets", {})

    entities = [_simplify_entity(e) for e in results]

    response = {
        "success": True,
        "query": query,
        "dataset": dataset,
        "schema_filter": schema,
        "total": data.get("total", {}).get("value", len(entities)),
        "returned": len(entities),
        "entities": entities,
        "facets": {
            "countries": {b["name"]: b["count"] for b in facets.get("countries", {}).get("values", [])},
            "topics": {b["name"]: b["count"] for b in facets.get("topics", {}).get("values", [])},
            "datasets": {b["name"]: b["count"] for b in facets.get("datasets", {}).get("values", [])},
        },
        "source": f"{BASE_URL}/search/{dataset}",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def match_entity(schema: str, properties: Dict[str, List[str]],
                 dataset: str = "default", threshold: float = 0.5, limit: int = 10) -> Dict:
    """Fuzzy multi-property matching for compliance screening."""
    cache_key = f"match_{dataset}_{schema}"
    cache_params = {"schema": schema, "properties": properties, "threshold": threshold}
    cp = _cache_path(cache_key, _params_hash(cache_params))
    cached = _read_cache(cp, CACHE_TTL_SEARCH)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    query = {"schema": schema, "properties": properties}
    body = {"queries": {"q": query}}
    params = {"threshold": threshold, "limit": limit}

    result = _api_post(f"/match/{dataset}", body, params)
    if not result["success"]:
        return {"success": False, "error": result["error"]}

    data = result["data"]
    q_response = data.get("responses", {}).get("q", {})
    results = q_response.get("results", [])

    entities = [_simplify_entity(e) for e in results]

    response = {
        "success": True,
        "schema": schema,
        "properties": properties,
        "dataset": dataset,
        "threshold": threshold,
        "total_matches": len(entities),
        "matches": entities,
        "source": f"{BASE_URL}/match/{dataset}",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_entity(entity_id: str, nested: bool = True) -> Dict:
    """Retrieve full entity detail by ID."""
    cache_key = f"entity_{entity_id}"
    cp = _cache_path(cache_key, _params_hash({"nested": nested}))
    cached = _read_cache(cp, CACHE_TTL_SEARCH)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {"nested": str(nested).lower()}
    result = _api_get(f"/entities/{entity_id}", params)
    if not result["success"]:
        return {"success": False, "entity_id": entity_id, "error": result["error"]}

    entity = result["data"]
    simplified = _simplify_entity(entity)

    props = entity.get("properties", {})
    simplified["all_names"] = props.get("name", []) + props.get("alias", []) + props.get("weakAlias", [])
    simplified["addresses"] = props.get("address", [])
    simplified["id_numbers"] = props.get("idNumber", [])

    referents = entity.get("referents", [])
    if referents:
        simplified["referents"] = referents

    response = {
        "success": True,
        "entity": simplified,
        "source": f"{BASE_URL}/entities/{entity_id}",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_datasets() -> Dict:
    """List all available datasets with metadata."""
    cp = _cache_path("catalog", _params_hash({}))
    cached = _read_cache(cp, CACHE_TTL_STATS)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get("/catalog")
    if not result["success"]:
        return {"success": False, "error": result["error"]}

    data = result["data"]
    datasets = []
    for ds in data.get("datasets", []):
        children = ds.get("children") or []
        ds_type = "collection" if children else "source"
        datasets.append({
            "name": ds.get("name"),
            "title": ds.get("title"),
            "type": ds_type,
            "entity_count": ds.get("entity_count") or ds.get("thing_count"),
            "updated_at": ds.get("last_export") or ds.get("updated_at"),
            "summary": ds.get("summary", "")[:200] if ds.get("summary") else None,
            "children_count": len(children) if ds_type == "collection" else None,
        })

    datasets.sort(key=lambda d: d.get("entity_count") or 0, reverse=True)

    response = {
        "success": True,
        "total_datasets": len(datasets),
        "datasets": datasets,
        "source": f"{BASE_URL}/catalog",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_statistics() -> Dict:
    """Aggregate statistics from dataset catalog."""
    ds_result = get_datasets()
    if not ds_result.get("success"):
        return ds_result

    datasets = ds_result.get("datasets", [])
    sources = [d for d in datasets if d.get("type") == "source"]
    collections = [d for d in datasets if d.get("type") == "collection"]

    total_entities = sum(d.get("entity_count") or 0 for d in collections if d.get("name") == "default")
    sanctions_entities = sum(d.get("entity_count") or 0 for d in collections if d.get("name") == "sanctions")
    pep_entities = sum(d.get("entity_count") or 0 for d in collections if d.get("name") == "peps")

    top_sources = sorted(sources, key=lambda d: d.get("entity_count") or 0, reverse=True)[:20]

    return {
        "success": True,
        "total_entities": total_entities,
        "sanctions_entities": sanctions_entities,
        "pep_entities": pep_entities,
        "total_source_datasets": len(sources),
        "total_collections": len(collections),
        "top_sources": [{
            "name": s["name"],
            "title": s.get("title"),
            "entities": s.get("entity_count"),
            "updated": s.get("updated_at"),
        } for s in top_sources],
        "source": f"{BASE_URL}/catalog",
        "timestamp": datetime.now().isoformat(),
    }


def get_country_exposure(country_code: str, dataset: str = "default", limit: int = 50) -> Dict:
    """Get sanctioned entities for a specific country."""
    cache_key = f"country_{country_code}_{dataset}"
    cp = _cache_path(cache_key, _params_hash({"limit": limit}))
    cached = _read_cache(cp, CACHE_TTL_SEARCH)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {
        "q": "",
        "countries": country_code.lower(),
        "limit": limit,
        "topics": "sanction",
    }

    result = _api_get(f"/search/{dataset}", params)
    if not result["success"]:
        return {"success": False, "country": country_code, "error": result["error"]}

    data = result["data"]
    results = data.get("results", [])
    facets = data.get("facets", {})

    entities = [_simplify_entity(e) for e in results]

    schema_breakdown = {}
    for e in entities:
        s = e.get("schema", "Unknown")
        schema_breakdown[s] = schema_breakdown.get(s, 0) + 1

    response = {
        "success": True,
        "country": country_code.upper(),
        "dataset": dataset,
        "total_sanctioned": data.get("total", {}).get("value", len(entities)),
        "returned": len(entities),
        "schema_breakdown": schema_breakdown,
        "entities": entities,
        "dataset_coverage": {b["name"]: b["count"]
                            for b in facets.get("datasets", {}).get("values", [])},
        "source": f"{BASE_URL}/search/{dataset}",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_vessels(dataset: str = "sanctions", limit: int = 50) -> Dict:
    """Get sanctioned vessels across all datasets."""
    cache_key = f"vessels_{dataset}"
    cp = _cache_path(cache_key, _params_hash({"limit": limit}))
    cached = _read_cache(cp, CACHE_TTL_SEARCH)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {"q": "", "schema": "Vessel", "limit": limit}

    result = _api_get(f"/search/{dataset}", params)
    if not result["success"]:
        return {"success": False, "error": result["error"]}

    data = result["data"]
    results = data.get("results", [])
    facets = data.get("facets", {})

    entities = [_simplify_entity(e) for e in results]

    flag_breakdown = {}
    for e in entities:
        flags = e.get("countries", [])
        for f in flags:
            flag_breakdown[f] = flag_breakdown.get(f, 0) + 1

    response = {
        "success": True,
        "schema": "Vessel",
        "dataset": dataset,
        "total_vessels": data.get("total", {}).get("value", len(entities)),
        "returned": len(entities),
        "flag_breakdown": flag_breakdown,
        "vessels": entities,
        "dataset_coverage": {b["name"]: b["count"]
                            for b in facets.get("datasets", {}).get("values", [])},
        "source": f"{BASE_URL}/search/{dataset}",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_peps(query: str = "", country: str = None, limit: int = 20) -> Dict:
    """Search politically exposed persons."""
    params_dict = {"q": query, "country": country, "limit": limit}
    cache_key = "peps_search"
    cp = _cache_path(cache_key, _params_hash(params_dict))
    cached = _read_cache(cp, CACHE_TTL_SEARCH)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {"q": query, "schema": "Person", "limit": limit, "topics": "role.pep"}
    if country:
        params["countries"] = country.lower()

    result = _api_get("/search/peps", params)
    if not result["success"]:
        return {"success": False, "query": query, "error": result["error"]}

    data = result["data"]
    results = data.get("results", [])
    facets = data.get("facets", {})

    entities = [_simplify_entity(e) for e in results]

    response = {
        "success": True,
        "query": query or "(all PEPs)",
        "country_filter": country,
        "total": data.get("total", {}).get("value", len(entities)),
        "returned": len(entities),
        "entities": entities,
        "country_facets": {b["name"]: b["count"]
                          for b in facets.get("countries", {}).get("values", [])},
        "source": f"{BASE_URL}/search/peps",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_new_designations(days: int = 30, dataset: str = "sanctions", limit: int = 50) -> Dict:
    """Find entities recently added to sanctions lists (escalation detection)."""
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    cache_key = f"new_designations_{dataset}_{days}d"
    cp = _cache_path(cache_key, _params_hash({"since": since_date, "limit": limit}))
    cached = _read_cache(cp, CACHE_TTL_SEARCH)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {
        "q": "",
        "limit": limit,
        "changed_since": since_date,
        "sort": "first_seen:desc",
    }

    result = _api_get(f"/search/{dataset}", params)
    if not result["success"]:
        return {"success": False, "error": result["error"]}

    data = result["data"]
    results = data.get("results", [])
    facets = data.get("facets", {})

    entities = [_simplify_entity(e) for e in results]

    response = {
        "success": True,
        "period": f"last {days} days",
        "since_date": since_date,
        "dataset": dataset,
        "total_new": data.get("total", {}).get("value", len(entities)),
        "returned": len(entities),
        "entities": entities,
        "country_breakdown": {b["name"]: b["count"]
                              for b in facets.get("countries", {}).get("values", [])},
        "dataset_breakdown": {b["name"]: b["count"]
                              for b in facets.get("datasets", {}).get("values", [])},
        "source": f"{BASE_URL}/search/{dataset}",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


# --- Standard module interface ---

def fetch_data(indicator: str, **kwargs) -> Dict:
    """Fetch a specific indicator. Dispatches to the appropriate function."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}",
                "available": list(INDICATORS.keys())}

    if indicator == "ENTITY_SEARCH":
        query = kwargs.get("query", kwargs.get("q", ""))
        schema = kwargs.get("schema")
        if not query:
            return {"success": False, "error": "search requires a 'query' parameter"}
        return search_entities(query, schema=schema,
                               limit=kwargs.get("limit", 20),
                               countries=kwargs.get("countries"),
                               topics=kwargs.get("topics"))

    elif indicator == "ENTITY_MATCH":
        schema = kwargs.get("schema", "Person")
        properties = kwargs.get("properties", {})
        if not properties:
            return {"success": False, "error": "match requires 'properties' dict"}
        return match_entity(schema, properties,
                            threshold=kwargs.get("threshold", 0.5),
                            limit=kwargs.get("limit", 10))

    elif indicator == "ENTITY_DETAIL":
        entity_id = kwargs.get("entity_id", "")
        if not entity_id:
            return {"success": False, "error": "entity requires 'entity_id' parameter"}
        return get_entity(entity_id)

    elif indicator == "DATASET_CATALOG":
        return get_datasets()

    elif indicator == "COUNTRY_EXPOSURE":
        country = kwargs.get("country", "")
        if not country:
            return {"success": False, "error": "country requires 'country' code (e.g. RU, IR, KP)"}
        return get_country_exposure(country, limit=kwargs.get("limit", 50))

    elif indicator == "PEP_SEARCH":
        return get_peps(query=kwargs.get("query", ""),
                        country=kwargs.get("country"),
                        limit=kwargs.get("limit", 20))

    elif indicator == "VESSEL_SANCTIONS":
        return get_vessels(limit=kwargs.get("limit", 50))

    elif indicator == "NEW_DESIGNATIONS":
        return get_new_designations(days=kwargs.get("days", 30),
                                     limit=kwargs.get("limit", 50))

    return {"success": False, "error": f"Unhandled indicator: {indicator}"}


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "endpoint": v["endpoint"],
            "frequency": v["frequency"],
            "unit": v["unit"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest data for one indicator, or a summary of dataset statistics."""
    if indicator:
        return fetch_data(indicator)

    stats = get_statistics()
    return stats


# --- CLI ---

def _print_help():
    print("""
OpenSanctions Global Database API Module (Initiative 0064)

Usage:
  python opensanctions_api.py                                   # Dataset statistics summary
  python opensanctions_api.py search "Rosneft"                  # Search entity by name
  python opensanctions_api.py search "Gazprombank" Company      # Search companies only
  python opensanctions_api.py entity Q7397                      # Entity detail by ID
  python opensanctions_api.py match Person "Vladimir Putin"     # Fuzzy match a person
  python opensanctions_api.py datasets                          # List all sanctions datasets
  python opensanctions_api.py stats                             # Aggregate statistics
  python opensanctions_api.py country RU                        # Russia sanctions exposure
  python opensanctions_api.py country IR                        # Iran sanctions exposure
  python opensanctions_api.py vessels                           # Sanctioned vessels list
  python opensanctions_api.py peps                              # PEP search (all)
  python opensanctions_api.py peps "Putin" RU                   # PEP search by name+country
  python opensanctions_api.py new 30                            # New designations (last 30 days)
  python opensanctions_api.py list                              # List available indicators

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Auth: OPENSANCTIONS_API_KEY from environment
Rate Limits: 50 req/day (free), 500/day (registered)
Cache: {CACHE_TTL_SEARCH}h (search), {CACHE_TTL_STATS}h (statistics)
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd in ("--help", "-h", "help"):
        _print_help()

    elif cmd == "list":
        print(json.dumps(get_available_indicators(), indent=2, default=str))

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: opensanctions_api.py search <query> [schema]")
            sys.exit(1)
        query = sys.argv[2]
        schema = sys.argv[3] if len(sys.argv) > 3 else None
        result = search_entities(query, schema=schema)
        print(json.dumps(result, indent=2, default=str))

    elif cmd == "entity":
        if len(sys.argv) < 3:
            print("Usage: opensanctions_api.py entity <entity_id>")
            sys.exit(1)
        result = get_entity(sys.argv[2])
        print(json.dumps(result, indent=2, default=str))

    elif cmd == "match":
        if len(sys.argv) < 4:
            print("Usage: opensanctions_api.py match <schema> <name> [country]")
            sys.exit(1)
        schema = sys.argv[2]
        name = sys.argv[3]
        props = {"name": [name]}
        if len(sys.argv) > 4:
            if schema == "Person":
                props["nationality"] = [sys.argv[4]]
            else:
                props["jurisdiction"] = [sys.argv[4]]
        result = match_entity(schema, props)
        print(json.dumps(result, indent=2, default=str))

    elif cmd == "datasets":
        result = get_datasets()
        print(json.dumps(result, indent=2, default=str))

    elif cmd == "stats":
        result = get_statistics()
        print(json.dumps(result, indent=2, default=str))

    elif cmd == "country":
        if len(sys.argv) < 3:
            print("Usage: opensanctions_api.py country <country_code>")
            sys.exit(1)
        result = get_country_exposure(sys.argv[2])
        print(json.dumps(result, indent=2, default=str))

    elif cmd == "vessels":
        result = get_vessels()
        print(json.dumps(result, indent=2, default=str))

    elif cmd == "peps":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        country = sys.argv[3] if len(sys.argv) > 3 else None
        result = get_peps(query=query, country=country)
        print(json.dumps(result, indent=2, default=str))

    elif cmd == "new":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        result = get_new_designations(days=days)
        print(json.dumps(result, indent=2, default=str))

    else:
        result = fetch_data(cmd)
        print(json.dumps(result, indent=2, default=str))

#!/usr/bin/env python3
"""
GLEIF LEI Registry Module

Global Legal Entity Identifier Foundation — the authoritative registry of
Legal Entity Identifiers (LEIs). Provides entity lookup, relationship mapping,
and corporate hierarchy data for 3M+ entities worldwide.

Data Source: https://api.gleif.org/api/v1
Protocol: REST (JSON:API specification)
Auth: None (fully open, no key required)
Rate Limits: Fair use
Coverage: Global (2.5M+ active entities across all jurisdictions)

Author: QUANTCLAW DATA Build Agent
"""

import json
import sys
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://api.gleif.org/api/v1"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "gleif_lei"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30

INDICATORS = {
    "TOTAL_ACTIVE": {
        "filter": {"entity.status": "ACTIVE"},
        "name": "Total Active LEIs",
        "description": "Total number of active Legal Entity Identifiers globally",
        "unit": "entities",
    },
    "TOTAL_LAPSED": {
        "filter": {"registration.status": "LAPSED"},
        "name": "Total Lapsed LEIs",
        "description": "LEI registrations that have lapsed (not renewed)",
        "unit": "entities",
    },
    "US_ENTITIES": {
        "filter": {"entity.legalAddress.country": "US"},
        "name": "US-Registered Entities",
        "description": "Legal entities registered in the United States",
        "unit": "entities",
    },
    "GB_ENTITIES": {
        "filter": {"entity.legalAddress.country": "GB"},
        "name": "UK-Registered Entities",
        "description": "Legal entities registered in the United Kingdom",
        "unit": "entities",
    },
    "DE_ENTITIES": {
        "filter": {"entity.legalAddress.country": "DE"},
        "name": "Germany-Registered Entities",
        "description": "Legal entities registered in Germany",
        "unit": "entities",
    },
    "JP_ENTITIES": {
        "filter": {"entity.legalAddress.country": "JP"},
        "name": "Japan-Registered Entities",
        "description": "Legal entities registered in Japan",
        "unit": "entities",
    },
    "FR_ENTITIES": {
        "filter": {"entity.legalAddress.country": "FR"},
        "name": "France-Registered Entities",
        "description": "Legal entities registered in France",
        "unit": "entities",
    },
    "CN_ENTITIES": {
        "filter": {"entity.legalAddress.country": "CN"},
        "name": "China-Registered Entities",
        "description": "Legal entities registered in China",
        "unit": "entities",
    },
    "CA_ENTITIES": {
        "filter": {"entity.legalAddress.country": "CA"},
        "name": "Canada-Registered Entities",
        "description": "Legal entities registered in Canada",
        "unit": "entities",
    },
    "LU_ENTITIES": {
        "filter": {"entity.legalAddress.country": "LU"},
        "name": "Luxembourg-Registered Entities",
        "description": "Legal entities registered in Luxembourg (fund domicile hub)",
        "unit": "entities",
    },
}


def _cache_path(key: str, params_hash: str) -> Path:
    safe = key.replace("/", "_").replace(" ", "_")
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


def _api_get(endpoint: str, params: Optional[Dict] = None) -> Dict:
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        if status == 404:
            return {"success": False, "error": "Not found (HTTP 404)", "status": 404}
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_entity(record: Dict) -> Dict:
    """Extract structured entity data from a JSON:API lei-record."""
    attrs = record.get("attributes", {})
    entity = attrs.get("entity", {})
    registration = attrs.get("registration", {})
    legal_addr = entity.get("legalAddress", {})
    hq_addr = entity.get("headquartersAddress", {})

    other_names = []
    for n in entity.get("otherNames", []):
        other_names.append({"name": n.get("name"), "type": n.get("type")})

    return {
        "lei": attrs.get("lei"),
        "legal_name": (entity.get("legalName") or {}).get("name"),
        "other_names": other_names if other_names else None,
        "jurisdiction": entity.get("jurisdiction"),
        "country": legal_addr.get("country"),
        "region": legal_addr.get("region"),
        "city": legal_addr.get("city"),
        "postal_code": legal_addr.get("postalCode"),
        "legal_address": ", ".join(filter(None, legal_addr.get("addressLines", []))),
        "hq_country": hq_addr.get("country"),
        "hq_city": hq_addr.get("city"),
        "hq_address": ", ".join(filter(None, hq_addr.get("addressLines", []))),
        "status": entity.get("status"),
        "category": entity.get("category"),
        "registered_as": entity.get("registeredAs"),
        "legal_form_id": (entity.get("legalForm") or {}).get("id"),
        "creation_date": entity.get("creationDate"),
        "registration_status": registration.get("status"),
        "initial_registration": registration.get("initialRegistrationDate"),
        "last_update": registration.get("lastUpdateDate"),
        "next_renewal": registration.get("nextRenewalDate"),
        "managing_lou": registration.get("managingLou"),
    }


def _parse_pagination(meta: Dict) -> Optional[Dict]:
    pag = meta.get("pagination")
    if not pag:
        return None
    return {
        "current_page": pag.get("currentPage"),
        "per_page": pag.get("perPage"),
        "total": pag.get("total"),
        "last_page": pag.get("lastPage"),
    }


# --- Core API Functions ---


def fetch_data(indicator: str) -> Dict:
    """Fetch a count-based indicator (total entities matching a filter)."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_key = {"indicator": indicator}
    cp = _cache_path(indicator, _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {"page[size]": 1}
    for k, v in cfg["filter"].items():
        params[f"filter[{k}]"] = v

    result = _api_get("lei-records", params)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    pagination = _parse_pagination(result["data"].get("meta", {}))
    total = pagination["total"] if pagination else 0

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "value": total,
        "filters": cfg["filter"],
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


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
                "value": data["value"],
                "unit": data["unit"],
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})

    return {
        "success": True,
        "source": "GLEIF LEI Registry",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "unit": v["unit"],
            "filter": v["filter"],
        }
        for k, v in INDICATORS.items()
    ]


def search_entity(name: str, page: int = 1, page_size: int = 10) -> Dict:
    """Search entities by legal name (fuzzy match)."""
    cache_key = {"search": name, "page": page, "size": page_size}
    cp = _cache_path(f"search_{name}", _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {
        "filter[entity.legalName]": name,
        "page[size]": page_size,
        "page[number]": page,
    }
    result = _api_get("lei-records", params)
    if not result["success"]:
        return {"success": False, "query": name, "error": result["error"]}

    raw = result["data"]
    entities = [_parse_entity(r) for r in raw.get("data", [])]
    pagination = _parse_pagination(raw.get("meta", {}))

    response = {
        "success": True,
        "query": name,
        "results": entities,
        "pagination": pagination,
        "result_count": len(entities),
        "total_matches": pagination["total"] if pagination else len(entities),
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def lookup_lei(lei: str) -> Dict:
    """Look up a specific entity by LEI code."""
    cache_key = {"lei": lei}
    cp = _cache_path(f"lei_{lei}", _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get(f"lei-records/{lei}")
    if not result["success"]:
        return {"success": False, "lei": lei, "error": result["error"]}

    raw = result["data"]
    entity = _parse_entity(raw.get("data", {}))
    relationships = list((raw.get("data", {}).get("relationships", {})).keys())

    response = {
        "success": True,
        "entity": entity,
        "available_relationships": relationships,
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def search_by_registration(registration_id: str, page: int = 1, page_size: int = 10) -> Dict:
    """Search entities by registration number (e.g. company house number)."""
    cache_key = {"reg": registration_id, "page": page, "size": page_size}
    cp = _cache_path(f"reg_{registration_id}", _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {
        "filter[entity.registeredAs]": registration_id,
        "page[size]": page_size,
        "page[number]": page,
    }
    result = _api_get("lei-records", params)
    if not result["success"]:
        return {"success": False, "registration_id": registration_id, "error": result["error"]}

    raw = result["data"]
    entities = [_parse_entity(r) for r in raw.get("data", [])]
    pagination = _parse_pagination(raw.get("meta", {}))

    response = {
        "success": True,
        "registration_id": registration_id,
        "results": entities,
        "pagination": pagination,
        "result_count": len(entities),
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def autocomplete(query: str) -> Dict:
    """Autocomplete entity search (fast typeahead)."""
    cache_key = {"autocomplete": query}
    cp = _cache_path(f"ac_{query}", _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get("autocompletions", {"field": "fulltext", "q": query})
    if not result["success"]:
        return {"success": False, "query": query, "error": result["error"]}

    raw = result["data"]
    suggestions = []
    for item in raw.get("data", []):
        attrs = item.get("attributes", {})
        rel = item.get("relationships", {}).get("lei-records", {}).get("data", {})
        suggestions.append({
            "name": attrs.get("value"),
            "lei": rel.get("id"),
        })

    response = {
        "success": True,
        "query": query,
        "suggestions": suggestions,
        "count": len(suggestions),
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_direct_parent(lei: str) -> Dict:
    """Get the direct parent entity of a given LEI."""
    cache_key = {"direct_parent": lei}
    cp = _cache_path(f"dp_{lei}", _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get(f"lei-records/{lei}/direct-parent")
    if not result["success"]:
        if result.get("status") == 404:
            return {"success": True, "lei": lei, "direct_parent": None, "note": "No parent relationship reported"}
        return {"success": False, "lei": lei, "error": result["error"]}

    raw = result["data"]
    parent = _parse_entity(raw.get("data", {}))

    response = {
        "success": True,
        "lei": lei,
        "direct_parent": parent,
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_ultimate_parent(lei: str) -> Dict:
    """Get the ultimate parent entity of a given LEI."""
    cache_key = {"ultimate_parent": lei}
    cp = _cache_path(f"up_{lei}", _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get(f"lei-records/{lei}/ultimate-parent")
    if not result["success"]:
        if result.get("status") == 404:
            return {"success": True, "lei": lei, "ultimate_parent": None, "note": "No ultimate parent reported (may be top-level entity)"}
        return {"success": False, "lei": lei, "error": result["error"]}

    raw = result["data"]
    parent = _parse_entity(raw.get("data", {}))

    response = {
        "success": True,
        "lei": lei,
        "ultimate_parent": parent,
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_direct_children(lei: str, page: int = 1, page_size: int = 20) -> Dict:
    """Get direct child entities (subsidiaries) of a given LEI."""
    cache_key = {"children": lei, "page": page, "size": page_size}
    cp = _cache_path(f"ch_{lei}", _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get(f"lei-records/{lei}/direct-children", {
        "page[size]": page_size,
        "page[number]": page,
    })
    if not result["success"]:
        if result.get("status") == 404:
            return {"success": True, "lei": lei, "children": [], "note": "No child relationships reported"}
        return {"success": False, "lei": lei, "error": result["error"]}

    raw = result["data"]
    children = [_parse_entity(r) for r in raw.get("data", [])]
    pagination = _parse_pagination(raw.get("meta", {}))

    response = {
        "success": True,
        "lei": lei,
        "children": children,
        "pagination": pagination,
        "child_count": len(children),
        "total_children": pagination["total"] if pagination else len(children),
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_hierarchy(lei: str) -> Dict:
    """Build corporate hierarchy: ultimate parent → direct parent → entity → direct children."""
    entity_result = lookup_lei(lei)
    if not entity_result.get("success"):
        return entity_result

    entity = entity_result["entity"]
    ultimate = get_ultimate_parent(lei)
    direct = get_direct_parent(lei)
    children = get_direct_children(lei, page_size=50)

    hierarchy = {
        "success": True,
        "lei": lei,
        "entity": entity,
        "ultimate_parent": ultimate.get("ultimate_parent") if ultimate.get("success") else None,
        "direct_parent": direct.get("direct_parent") if direct.get("success") else None,
        "direct_children": children.get("children", []) if children.get("success") else [],
        "total_children": children.get("total_children", 0) if children.get("success") else 0,
        "is_top_level": direct.get("direct_parent") is None,
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    return hierarchy


def jurisdiction_stats(country_code: str, page: int = 1, page_size: int = 10) -> Dict:
    """Get entities for a specific jurisdiction/country with count."""
    country_code = country_code.upper()
    cache_key = {"jurisdiction": country_code, "page": page, "size": page_size}
    cp = _cache_path(f"jur_{country_code}", _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {
        "filter[entity.legalAddress.country]": country_code,
        "page[size]": page_size,
        "page[number]": page,
    }
    result = _api_get("lei-records", params)
    if not result["success"]:
        return {"success": False, "country": country_code, "error": result["error"]}

    raw = result["data"]
    entities = [_parse_entity(r) for r in raw.get("data", [])]
    pagination = _parse_pagination(raw.get("meta", {}))

    response = {
        "success": True,
        "country": country_code,
        "total_entities": pagination["total"] if pagination else len(entities),
        "sample_entities": entities,
        "pagination": pagination,
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


# --- CLI ---


def _print_help():
    print("""
GLEIF LEI Registry Module

Usage:
  python gleif_lei.py                                  # Summary stats (total active LEIs, by country)
  python gleif_lei.py search "Apple Inc"               # Search by company name
  python gleif_lei.py lookup HWUPKR0MPOU8FGXBT394     # Lookup by LEI code
  python gleif_lei.py hierarchy HWUPKR0MPOU8FGXBT394   # Parent/child tree
  python gleif_lei.py jurisdiction US                   # Country-level stats + sample
  python gleif_lei.py autocomplete "Goldman"            # Fast typeahead search
  python gleif_lei.py registration 806592               # Search by registration number
  python gleif_lei.py parent HWUPKR0MPOU8FGXBT394      # Direct parent lookup
  python gleif_lei.py ultimate HWUPKR0MPOU8FGXBT394    # Ultimate parent lookup
  python gleif_lei.py children 8I5DZWZKVSZI1NUHU748    # Direct subsidiaries
  python gleif_lei.py list                              # List available indicators

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<20s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: REST (JSON:API)
Auth: None (open access)
Coverage: Global (3M+ entities)
""")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
    elif args[0] in ("--help", "-h", "help"):
        _print_help()
    elif args[0] == "list":
        print(json.dumps(get_available_indicators(), indent=2, default=str))
    elif args[0] == "search" and len(args) > 1:
        query = " ".join(args[1:])
        print(json.dumps(search_entity(query), indent=2, default=str))
    elif args[0] == "lookup" and len(args) > 1:
        print(json.dumps(lookup_lei(args[1]), indent=2, default=str))
    elif args[0] == "hierarchy" and len(args) > 1:
        print(json.dumps(get_hierarchy(args[1]), indent=2, default=str))
    elif args[0] == "jurisdiction" and len(args) > 1:
        print(json.dumps(jurisdiction_stats(args[1]), indent=2, default=str))
    elif args[0] == "autocomplete" and len(args) > 1:
        query = " ".join(args[1:])
        print(json.dumps(autocomplete(query), indent=2, default=str))
    elif args[0] == "registration" and len(args) > 1:
        print(json.dumps(search_by_registration(args[1]), indent=2, default=str))
    elif args[0] == "parent" and len(args) > 1:
        print(json.dumps(get_direct_parent(args[1]), indent=2, default=str))
    elif args[0] == "ultimate" and len(args) > 1:
        print(json.dumps(get_ultimate_parent(args[1]), indent=2, default=str))
    elif args[0] == "children" and len(args) > 1:
        print(json.dumps(get_direct_children(args[1]), indent=2, default=str))
    elif args[0].upper() in INDICATORS:
        print(json.dumps(fetch_data(args[0]), indent=2, default=str))
    else:
        print(f"Unknown command: {args[0]}")
        _print_help()
        sys.exit(1)

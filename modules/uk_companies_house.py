#!/usr/bin/env python3
"""
UK Companies House Module

Structured data on 5M+ UK-registered companies: profiles, officers, filing
history, charges (secured debt), insolvency proceedings, and persons with
significant control (PSC). High-value alternative data for corporate governance
screening, credit risk assessment, and M&A signal detection.

Data Source: https://api.company-information.service.gov.uk
Protocol: REST (JSON)
Auth: API key via HTTP Basic (key as username, empty password)
Rate Limits: 600 requests per 5 minutes
Coverage: All UK-registered companies

Author: QUANTCLAW DATA Build Agent
Initiative: 0067
"""

import json
import sys
import time
import hashlib
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://api.company-information.service.gov.uk"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "uk_companies_house"

CACHE_TTL_SEARCH = 1       # hours — search results
CACHE_TTL_PROFILE = 6      # hours — company profiles
CACHE_TTL_HISTORY = 24     # hours — filings, charges, historical data

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RATE_LIMIT_WINDOW = 300    # 5 minutes in seconds
RATE_LIMIT_MAX = 600

INDICATORS = {
    "COMPANY_SEARCH": {
        "name": "Company Search",
        "description": "Search UK companies by name or number",
        "endpoint": "/search/companies",
        "frequency": "on-demand",
        "unit": "results",
    },
    "COMPANY_PROFILE": {
        "name": "Company Profile",
        "description": "Full company profile: status, SIC codes, addresses, filing dates",
        "endpoint": "/company/{company_number}",
        "frequency": "on-demand",
        "unit": "profile",
    },
    "OFFICERS": {
        "name": "Company Officers",
        "description": "Current and resigned officers (directors, secretaries) with appointment dates",
        "endpoint": "/company/{company_number}/officers",
        "frequency": "on-demand",
        "unit": "officers",
    },
    "FILING_HISTORY": {
        "name": "Filing History",
        "description": "All filed documents with dates and categories",
        "endpoint": "/company/{company_number}/filing-history",
        "frequency": "on-demand",
        "unit": "filings",
    },
    "CHARGES": {
        "name": "Charges (Secured Debt)",
        "description": "Secured charges: mortgages, debentures, liens with creation/satisfaction dates",
        "endpoint": "/company/{company_number}/charges",
        "frequency": "on-demand",
        "unit": "charges",
    },
    "INSOLVENCY": {
        "name": "Insolvency Proceedings",
        "description": "Insolvency cases and practitioner details",
        "endpoint": "/company/{company_number}/insolvency",
        "frequency": "on-demand",
        "unit": "cases",
    },
    "PSC": {
        "name": "Persons with Significant Control",
        "description": "Beneficial owners with >25% control — ownership, voting rights, influence",
        "endpoint": "/company/{company_number}/persons-with-significant-control",
        "frequency": "on-demand",
        "unit": "persons",
    },
    "OFFICER_SEARCH": {
        "name": "Officer Search",
        "description": "Search directors/officers across all UK companies",
        "endpoint": "/search/officers",
        "frequency": "on-demand",
        "unit": "results",
    },
    "DISQUALIFIED_OFFICERS": {
        "name": "Disqualified Directors",
        "description": "Lookup disqualified directors — regulatory action signal",
        "endpoint": "/search/disqualified-officers",
        "frequency": "on-demand",
        "unit": "results",
    },
    "SECTOR_SEARCH": {
        "name": "Sector Search (SIC Code)",
        "description": "Companies by SIC code — sector composition analysis",
        "endpoint": "/advanced-search/companies",
        "frequency": "on-demand",
        "unit": "companies",
    },
}

COMPANY_STATUS_MAP = {
    "active": "Active",
    "dissolved": "Dissolved",
    "liquidation": "Liquidation",
    "receivership": "Receivership",
    "administration": "Administration",
    "voluntary-arrangement": "Voluntary Arrangement (CVA)",
    "converted-closed": "Converted/Closed",
    "insolvency-proceedings": "Insolvency Proceedings",
    "registered": "Registered",
    "removed": "Removed",
    "open": "Open (LLP/LP)",
    "closed": "Closed",
}


def _get_api_key() -> Optional[str]:
    key = os.environ.get("UK_COMPANIES_HOUSE_API_KEY")
    if key:
        return key
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("UK_COMPANIES_HOUSE_API_KEY="):
                val = line.split("=", 1)[1].strip().strip("'\"")
                if val:
                    return val
    return None


def _cache_path(prefix: str, params_hash: str) -> Path:
    safe = prefix.replace("/", "_").replace(" ", "_")
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


def _api_request(endpoint: str, params: Optional[Dict] = None, retries: int = MAX_RETRIES) -> Dict:
    """Make authenticated request to Companies House API with rate-limit backoff."""
    api_key = _get_api_key()
    if not api_key:
        return {
            "success": False,
            "error": "UK_COMPANIES_HOUSE_API_KEY not set. Get a free key at https://developer.company-information.service.gov.uk/",
        }

    url = f"{BASE_URL}{endpoint}"
    auth = (api_key, "")  # Basic auth: key as username, empty password

    for attempt in range(retries):
        try:
            resp = requests.get(url, auth=auth, params=params, timeout=REQUEST_TIMEOUT)

            if resp.status_code == 429:
                wait = min(2 ** attempt * 5, 60)
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    try:
                        wait = int(retry_after)
                    except ValueError:
                        pass
                if attempt < retries - 1:
                    time.sleep(wait)
                    continue
                return {"success": False, "error": "Rate limited (600 req/5min). Try again later."}

            if resp.status_code == 401:
                return {"success": False, "error": "Invalid API key (HTTP 401)"}
            if resp.status_code == 404:
                return {"success": False, "error": "Not found (HTTP 404)"}

            resp.raise_for_status()
            return {"success": True, "data": resp.json()}

        except requests.Timeout:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"success": False, "error": "Request timed out"}
        except requests.ConnectionError:
            return {"success": False, "error": "Connection failed"}
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            return {"success": False, "error": f"HTTP {status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "Max retries exceeded"}


def _paginate(endpoint: str, params: Optional[Dict] = None, max_pages: int = 10) -> Dict:
    """Fetch all pages from a paginated endpoint."""
    all_items = []
    params = dict(params or {})
    params.setdefault("items_per_page", 100)
    start_index = 0

    for _ in range(max_pages):
        params["start_index"] = start_index
        result = _api_request(endpoint, params)
        if not result["success"]:
            if all_items:
                break
            return result

        data = result["data"]
        items = data.get("items", [])
        if not items:
            break

        all_items.extend(items)
        total = data.get("total_results", len(all_items))
        start_index += len(items)

        if start_index >= total:
            break
        time.sleep(0.5)

    return {"success": True, "items": all_items, "total_results": len(all_items)}


def _classify_status(status: str) -> str:
    return COMPANY_STATUS_MAP.get(status, status.replace("-", " ").title() if status else "Unknown")


# ── Public API ──────────────────────────────────────────────────────────


def search_companies(query: str, items_per_page: int = 20) -> Dict:
    """Search companies by name or number."""
    cp = _cache_path("search", _params_hash({"q": query, "n": items_per_page}))
    cached = _read_cache(cp, CACHE_TTL_SEARCH)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request("/search/companies", {"q": query, "items_per_page": items_per_page})
    if not result["success"]:
        return {"success": False, "query": query, "error": result["error"]}

    data = result["data"]
    companies = []
    for item in data.get("items", []):
        companies.append({
            "company_number": item.get("company_number"),
            "title": item.get("title"),
            "company_status": _classify_status(item.get("company_status", "")),
            "company_type": item.get("company_type"),
            "date_of_creation": item.get("date_of_creation"),
            "date_of_cessation": item.get("date_of_cessation"),
            "address_snippet": item.get("address_snippet"),
            "sic_codes": item.get("sic_codes"),
        })

    response = {
        "success": True,
        "query": query,
        "total_results": data.get("total_results", 0),
        "companies": companies,
        "count": len(companies),
        "source": f"{BASE_URL}/search/companies",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def get_company_profile(company_number: str) -> Dict:
    """Get full company profile by company number."""
    company_number = company_number.strip().upper()
    cp = _cache_path("profile", _params_hash({"cn": company_number}))
    cached = _read_cache(cp, CACHE_TTL_PROFILE)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(f"/company/{company_number}")
    if not result["success"]:
        return {"success": False, "company_number": company_number, "error": result["error"]}

    d = result["data"]
    addr = d.get("registered_office_address", {})

    response = {
        "success": True,
        "company_number": d.get("company_number"),
        "company_name": d.get("company_name"),
        "company_status": _classify_status(d.get("company_status", "")),
        "company_status_detail": d.get("company_status_detail"),
        "company_type": d.get("type"),
        "date_of_creation": d.get("date_of_creation"),
        "date_of_cessation": d.get("date_of_cessation"),
        "sic_codes": d.get("sic_codes", []),
        "registered_office": {
            "address_line_1": addr.get("address_line_1"),
            "address_line_2": addr.get("address_line_2"),
            "locality": addr.get("locality"),
            "region": addr.get("region"),
            "postal_code": addr.get("postal_code"),
            "country": addr.get("country"),
        },
        "accounts": d.get("accounts", {}),
        "confirmation_statement": d.get("confirmation_statement", {}),
        "has_been_liquidated": d.get("has_been_liquidated", False),
        "has_insolvency_history": d.get("has_insolvency_history", False),
        "has_charges": d.get("has_charges", False),
        "jurisdiction": d.get("jurisdiction"),
        "last_full_members_list_date": d.get("last_full_members_list_date"),
        "can_file": d.get("can_file", False),
        "source": f"{BASE_URL}/company/{company_number}",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def get_officers(company_number: str, include_resigned: bool = True) -> Dict:
    """Get officers (directors, secretaries) for a company."""
    company_number = company_number.strip().upper()
    cp = _cache_path("officers", _params_hash({"cn": company_number, "resigned": include_resigned}))
    cached = _read_cache(cp, CACHE_TTL_PROFILE)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {}
    if not include_resigned:
        params["register_view"] = "true"

    result = _paginate(f"/company/{company_number}/officers", params)
    if not result["success"]:
        return {"success": False, "company_number": company_number, "error": result["error"]}

    officers = []
    active_count = 0
    resigned_count = 0
    for item in result["items"]:
        resigned = item.get("resigned_on")
        if resigned:
            resigned_count += 1
        else:
            active_count += 1

        officers.append({
            "name": item.get("name"),
            "officer_role": item.get("officer_role"),
            "appointed_on": item.get("appointed_on"),
            "resigned_on": resigned,
            "nationality": item.get("nationality"),
            "country_of_residence": item.get("country_of_residence"),
            "occupation": item.get("occupation"),
            "date_of_birth": item.get("date_of_birth"),
        })

    response = {
        "success": True,
        "company_number": company_number,
        "officers": officers,
        "total_results": result["total_results"],
        "active_count": active_count,
        "resigned_count": resigned_count,
        "source": f"{BASE_URL}/company/{company_number}/officers",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def get_filing_history(company_number: str, category: str = None, items_per_page: int = 50) -> Dict:
    """Get filing history for a company, optionally filtered by category."""
    company_number = company_number.strip().upper()
    cp = _cache_path("filings", _params_hash({"cn": company_number, "cat": category}))
    cached = _read_cache(cp, CACHE_TTL_HISTORY)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {"items_per_page": items_per_page}
    if category:
        params["category"] = category

    result = _paginate(f"/company/{company_number}/filing-history", params, max_pages=5)
    if not result["success"]:
        return {"success": False, "company_number": company_number, "error": result["error"]}

    filings = []
    categories = {}
    for item in result["items"]:
        cat = item.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
        filings.append({
            "date": item.get("date"),
            "category": cat,
            "subcategory": item.get("subcategory"),
            "type": item.get("type"),
            "description": item.get("description"),
            "barcode": item.get("barcode"),
            "paper_filed": item.get("paper_filed", False),
        })

    response = {
        "success": True,
        "company_number": company_number,
        "filings": filings,
        "total_results": result["total_results"],
        "category_breakdown": categories,
        "source": f"{BASE_URL}/company/{company_number}/filing-history",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def get_charges(company_number: str) -> Dict:
    """Get charges (secured debt) for a company."""
    company_number = company_number.strip().upper()
    cp = _cache_path("charges", _params_hash({"cn": company_number}))
    cached = _read_cache(cp, CACHE_TTL_HISTORY)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _paginate(f"/company/{company_number}/charges")
    if not result["success"]:
        return {"success": False, "company_number": company_number, "error": result["error"]}

    charges = []
    outstanding = 0
    satisfied = 0
    for item in result["items"]:
        status = item.get("status", "")
        if status == "satisfied" or status == "fully-satisfied":
            satisfied += 1
        else:
            outstanding += 1

        persons_entitled = item.get("persons_entitled", [])
        charges.append({
            "charge_number": item.get("charge_number"),
            "status": status,
            "created_on": item.get("created_on"),
            "delivered_on": item.get("delivered_on"),
            "satisfied_on": item.get("satisfied_on"),
            "classification": item.get("classification", {}).get("description"),
            "particulars": item.get("particulars", {}).get("description"),
            "persons_entitled": [p.get("name") for p in persons_entitled] if persons_entitled else [],
            "secured_details": item.get("secured_details", {}).get("description"),
        })

    response = {
        "success": True,
        "company_number": company_number,
        "charges": charges,
        "total_results": result["total_results"],
        "outstanding_count": outstanding,
        "satisfied_count": satisfied,
        "source": f"{BASE_URL}/company/{company_number}/charges",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def get_insolvency(company_number: str) -> Dict:
    """Get insolvency proceedings for a company."""
    company_number = company_number.strip().upper()
    cp = _cache_path("insolvency", _params_hash({"cn": company_number}))
    cached = _read_cache(cp, CACHE_TTL_HISTORY)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(f"/company/{company_number}/insolvency")
    if not result["success"]:
        return {"success": False, "company_number": company_number, "error": result["error"]}

    data = result["data"]
    cases = []
    for case in data.get("cases", []):
        practitioners = []
        for p in case.get("practitioners", []):
            addr = p.get("address", {})
            practitioners.append({
                "name": p.get("name"),
                "role": p.get("role"),
                "appointed_on": p.get("appointed_on"),
                "ceased_to_act_on": p.get("ceased_to_act_on"),
                "address": f"{addr.get('address_line_1', '')}, {addr.get('locality', '')}, {addr.get('postal_code', '')}".strip(", "),
            })

        dates = []
        for d in case.get("dates", []):
            dates.append({"type": d.get("type"), "date": d.get("date")})

        cases.append({
            "case_number": case.get("number"),
            "type": case.get("type"),
            "dates": dates,
            "notes": case.get("notes", []),
            "practitioners": practitioners,
        })

    response = {
        "success": True,
        "company_number": company_number,
        "cases": cases,
        "total_cases": len(cases),
        "source": f"{BASE_URL}/company/{company_number}/insolvency",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def get_psc(company_number: str) -> Dict:
    """Get persons with significant control (beneficial owners)."""
    company_number = company_number.strip().upper()
    cp = _cache_path("psc", _params_hash({"cn": company_number}))
    cached = _read_cache(cp, CACHE_TTL_PROFILE)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _paginate(f"/company/{company_number}/persons-with-significant-control")
    if not result["success"]:
        return {"success": False, "company_number": company_number, "error": result["error"]}

    pscs = []
    for item in result["items"]:
        natures = item.get("natures_of_control", [])
        pscs.append({
            "name": item.get("name"),
            "kind": item.get("kind"),
            "nationality": item.get("nationality"),
            "country_of_residence": item.get("country_of_residence"),
            "notified_on": item.get("notified_on"),
            "ceased_on": item.get("ceased_on"),
            "natures_of_control": natures,
            "name_elements": item.get("name_elements"),
            "date_of_birth": item.get("date_of_birth"),
        })

    response = {
        "success": True,
        "company_number": company_number,
        "persons_with_significant_control": pscs,
        "total_results": result["total_results"],
        "active_count": sum(1 for p in pscs if not p.get("ceased_on")),
        "ceased_count": sum(1 for p in pscs if p.get("ceased_on")),
        "source": f"{BASE_URL}/company/{company_number}/persons-with-significant-control",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def search_officers(query: str, items_per_page: int = 20) -> Dict:
    """Search officers (directors) across all UK companies."""
    cp = _cache_path("officer_search", _params_hash({"q": query, "n": items_per_page}))
    cached = _read_cache(cp, CACHE_TTL_SEARCH)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request("/search/officers", {"q": query, "items_per_page": items_per_page})
    if not result["success"]:
        return {"success": False, "query": query, "error": result["error"]}

    data = result["data"]
    officers = []
    for item in data.get("items", []):
        appointments = item.get("appointment_count", 0)
        officers.append({
            "title": item.get("title"),
            "date_of_birth": item.get("date_of_birth"),
            "address_snippet": item.get("address_snippet"),
            "appointment_count": appointments,
            "links": item.get("links", {}),
        })

    response = {
        "success": True,
        "query": query,
        "total_results": data.get("total_results", 0),
        "officers": officers,
        "count": len(officers),
        "source": f"{BASE_URL}/search/officers",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def search_disqualified_officers(query: str, items_per_page: int = 20) -> Dict:
    """Search disqualified directors."""
    cp = _cache_path("disqualified", _params_hash({"q": query, "n": items_per_page}))
    cached = _read_cache(cp, CACHE_TTL_SEARCH)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request("/search/disqualified-officers", {"q": query, "items_per_page": items_per_page})
    if not result["success"]:
        return {"success": False, "query": query, "error": result["error"]}

    data = result["data"]
    officers = []
    for item in data.get("items", []):
        officers.append({
            "title": item.get("title"),
            "date_of_birth": item.get("date_of_birth"),
            "address_snippet": item.get("address_snippet"),
            "description": item.get("description"),
            "links": item.get("links", {}),
        })

    response = {
        "success": True,
        "query": query,
        "total_results": data.get("total_results", 0),
        "officers": officers,
        "count": len(officers),
        "source": f"{BASE_URL}/search/disqualified-officers",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def search_by_sic_code(sic_code: str, incorporated_from: str = None, incorporated_to: str = None) -> Dict:
    """Search companies by SIC code (sector analysis)."""
    cp = _cache_path("sector", _params_hash({"sic": sic_code, "from": incorporated_from, "to": incorporated_to}))
    cached = _read_cache(cp, CACHE_TTL_SEARCH)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {"sic_codes": sic_code}
    if incorporated_from:
        params["incorporated_from"] = incorporated_from
    if incorporated_to:
        params["incorporated_to"] = incorporated_to

    result = _api_request("/advanced-search/companies", params)
    if not result["success"]:
        return {"success": False, "sic_code": sic_code, "error": result["error"]}

    data = result["data"]
    companies = []
    status_breakdown = {}
    for item in data.get("items", []):
        status = _classify_status(item.get("company_status", ""))
        status_breakdown[status] = status_breakdown.get(status, 0) + 1
        companies.append({
            "company_number": item.get("company_number"),
            "company_name": item.get("company_name"),
            "company_status": status,
            "company_type": item.get("company_type"),
            "date_of_creation": item.get("date_of_creation"),
            "date_of_cessation": item.get("date_of_cessation"),
            "sic_codes": item.get("sic_codes"),
        })

    response = {
        "success": True,
        "sic_code": sic_code,
        "total_results": data.get("total_results", data.get("hits", len(companies))),
        "companies": companies,
        "count": len(companies),
        "status_breakdown": status_breakdown,
        "source": f"{BASE_URL}/advanced-search/companies",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


# ── Standard module interface ───────────────────────────────────────────


def fetch_data(indicator: str, **kwargs) -> Dict:
    """Fetch data for a specific indicator. Kwargs vary by indicator type."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    dispatch = {
        "COMPANY_SEARCH": lambda: search_companies(kwargs.get("query", ""), kwargs.get("items_per_page", 20)),
        "COMPANY_PROFILE": lambda: get_company_profile(kwargs.get("company_number", "")),
        "OFFICERS": lambda: get_officers(kwargs.get("company_number", "")),
        "FILING_HISTORY": lambda: get_filing_history(kwargs.get("company_number", ""), kwargs.get("category")),
        "CHARGES": lambda: get_charges(kwargs.get("company_number", "")),
        "INSOLVENCY": lambda: get_insolvency(kwargs.get("company_number", "")),
        "PSC": lambda: get_psc(kwargs.get("company_number", "")),
        "OFFICER_SEARCH": lambda: search_officers(kwargs.get("query", ""), kwargs.get("items_per_page", 20)),
        "DISQUALIFIED_OFFICERS": lambda: search_disqualified_officers(kwargs.get("query", ""), kwargs.get("items_per_page", 20)),
        "SECTOR_SEARCH": lambda: search_by_sic_code(kwargs.get("sic_code", ""), kwargs.get("incorporated_from"), kwargs.get("incorporated_to")),
    }

    handler = dispatch.get(indicator)
    if handler:
        return handler()
    return {"success": False, "error": f"No handler for indicator: {indicator}"}


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
    """Get summary statistics — searches a sample of well-known companies."""
    if indicator:
        return fetch_data(indicator)

    sample_companies = [
        ("00445790", "Barclays Bank PLC"),
        ("02121934", "Vodafone Group PLC"),
        ("00102498", "BP PLC"),
    ]

    summaries = []
    errors = []
    for cn, name in sample_companies:
        data = get_company_profile(cn)
        if data.get("success"):
            summaries.append({
                "company_number": cn,
                "name": data.get("company_name", name),
                "status": data.get("company_status"),
                "sic_codes": data.get("sic_codes"),
                "has_charges": data.get("has_charges"),
                "has_insolvency_history": data.get("has_insolvency_history"),
            })
        else:
            errors.append({"company_number": cn, "name": name, "error": data.get("error", "unknown")})
        time.sleep(0.5)

    return {
        "success": True,
        "source": "UK Companies House",
        "base_url": BASE_URL,
        "sample_profiles": summaries,
        "errors": errors if errors else None,
        "count": len(summaries),
        "indicators_available": len(INDICATORS),
        "timestamp": datetime.now().isoformat(),
    }


# ── CLI ─────────────────────────────────────────────────────────────────


def _print_help():
    print("""
UK Companies House Module — Initiative 0067

Usage:
  python uk_companies_house.py                                    Summary statistics
  python uk_companies_house.py search "Barclays"                  Search companies by name
  python uk_companies_house.py company 09740322                   Company profile by number
  python uk_companies_house.py officers 09740322                  Officers for a company
  python uk_companies_house.py filings 09740322                   Filing history
  python uk_companies_house.py charges 09740322                   Charges (secured debt)
  python uk_companies_house.py insolvency 09740322                Insolvency proceedings
  python uk_companies_house.py psc 09740322                       Persons with significant control
  python uk_companies_house.py search_officers "John Smith"       Search directors
  python uk_companies_house.py disqualified "John Smith"          Disqualified directors
  python uk_companies_house.py sector 6411                        Companies by SIC code
  python uk_companies_house.py list                               List available indicators

Data Source: https://api.company-information.service.gov.uk
Auth: UK_COMPANIES_HOUSE_API_KEY (free key from developer portal)
Rate Limits: 600 requests / 5 minutes

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print()


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
            print("Usage: python uk_companies_house.py search <query>")
            sys.exit(1)
        query = " ".join(sys.argv[2:])
        print(json.dumps(search_companies(query), indent=2, default=str))

    elif cmd == "company":
        if len(sys.argv) < 3:
            print("Usage: python uk_companies_house.py company <company_number>")
            sys.exit(1)
        print(json.dumps(get_company_profile(sys.argv[2]), indent=2, default=str))

    elif cmd == "officers":
        if len(sys.argv) < 3:
            print("Usage: python uk_companies_house.py officers <company_number>")
            sys.exit(1)
        print(json.dumps(get_officers(sys.argv[2]), indent=2, default=str))

    elif cmd == "filings":
        if len(sys.argv) < 3:
            print("Usage: python uk_companies_house.py filings <company_number>")
            sys.exit(1)
        print(json.dumps(get_filing_history(sys.argv[2]), indent=2, default=str))

    elif cmd == "charges":
        if len(sys.argv) < 3:
            print("Usage: python uk_companies_house.py charges <company_number>")
            sys.exit(1)
        print(json.dumps(get_charges(sys.argv[2]), indent=2, default=str))

    elif cmd == "insolvency":
        if len(sys.argv) < 3:
            print("Usage: python uk_companies_house.py insolvency <company_number>")
            sys.exit(1)
        print(json.dumps(get_insolvency(sys.argv[2]), indent=2, default=str))

    elif cmd == "psc":
        if len(sys.argv) < 3:
            print("Usage: python uk_companies_house.py psc <company_number>")
            sys.exit(1)
        print(json.dumps(get_psc(sys.argv[2]), indent=2, default=str))

    elif cmd == "search_officers":
        if len(sys.argv) < 3:
            print("Usage: python uk_companies_house.py search_officers <name>")
            sys.exit(1)
        query = " ".join(sys.argv[2:])
        print(json.dumps(search_officers(query), indent=2, default=str))

    elif cmd == "disqualified":
        if len(sys.argv) < 3:
            print("Usage: python uk_companies_house.py disqualified <name>")
            sys.exit(1)
        query = " ".join(sys.argv[2:])
        print(json.dumps(search_disqualified_officers(query), indent=2, default=str))

    elif cmd == "sector":
        if len(sys.argv) < 3:
            print("Usage: python uk_companies_house.py sector <sic_code>")
            sys.exit(1)
        incorporated_from = sys.argv[3] if len(sys.argv) > 3 else None
        incorporated_to = sys.argv[4] if len(sys.argv) > 4 else None
        print(json.dumps(search_by_sic_code(sys.argv[2], incorporated_from, incorporated_to), indent=2, default=str))

    else:
        result = fetch_data(cmd)
        print(json.dumps(result, indent=2, default=str))

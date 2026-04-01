#!/usr/bin/env python3
"""
USPTO PatentsView Module — Patent Grants & Applications Data

U.S. patent grants and applications data via the USPTO Open Data Portal (ODP).
Tracks corporate innovation pipelines, technology trends, and R&D intensity
by sector. Patent filings are leading indicators for pharma pipelines,
semiconductor roadmaps, and tech M&A targets.

Data Source: https://api.uspto.gov/api/v1 (USPTO Open Data Portal)
Protocol: REST (GET with Lucene/Solr query syntax)
Auth: API key required — set USPTO_ODP_API_KEY env var
      Register at https://data.uspto.gov/apis/getting-started
Rate limits: 45 requests/minute
Refresh: Daily (patent data updated daily on ODP)

Note: PatentsView (search.patentsview.org) migrated to the USPTO ODP on
      March 20, 2026. This module uses the new ODP API.

Author: QUANTCLAW DATA Build Agent
Initiative: 0046
"""

import json
import os
import sys
import time
import hashlib
import requests
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://api.uspto.gov/api/v1"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "patentsview_uspto"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
RATE_LIMIT_PER_MIN = 45
RATE_LIMIT_DELAY = 60.0 / RATE_LIMIT_PER_MIN  # ~1.33s between requests
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0

TICKER_TO_ASSIGNEE = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft",
    "GOOG": "Google",
    "GOOGL": "Google",
    "AMZN": "Amazon",
    "META": "Meta Platforms",
    "NVDA": "NVIDIA",
    "TSLA": "Tesla",
    "IBM": "International Business Machines",
    "INTC": "Intel",
    "QCOM": "Qualcomm",
    "AMD": "Advanced Micro Devices",
    "ORCL": "Oracle",
    "CRM": "Salesforce",
    "CSCO": "Cisco",
    "TXN": "Texas Instruments",
    "AVGO": "Broadcom",
    "MU": "Micron Technology",
    "PFE": "Pfizer",
    "JNJ": "Johnson & Johnson",
    "MRK": "Merck",
    "ABBV": "AbbVie",
    "LLY": "Eli Lilly",
    "BMY": "Bristol-Myers Squibb",
    "GILD": "Gilead Sciences",
    "AMGN": "Amgen",
    "BA": "Boeing",
    "GE": "General Electric",
    "CAT": "Caterpillar",
    "MMM": "3M",
    "HON": "Honeywell",
    "RTX": "Raytheon",
    "LMT": "Lockheed Martin",
    "F": "Ford",
    "GM": "General Motors",
    "TSMC": "Taiwan Semiconductor",
    "SAP": "SAP",
    "SONY": "Sony",
    "SAMSUNG": "Samsung",
}

CPC_CLASS_NAMES = {
    "A61K": "Pharma Preparations",
    "A61B": "Medical Diagnostics & Surgery",
    "A61P": "Therapeutic Activity",
    "G06F": "Digital Computing",
    "G06N": "AI & Machine Learning",
    "G06Q": "Business Methods & Fintech",
    "G06T": "Image Processing",
    "G06V": "Computer Vision",
    "H01L": "Semiconductors",
    "H04L": "Telecom & Networking",
    "H04W": "Wireless Communications",
    "H04N": "Image & Video Transmission",
    "H01M": "Batteries & Fuel Cells",
    "H02J": "Power Distribution",
    "B60L": "Electric Vehicles",
    "C07K": "Peptides & Proteins",
    "C12N": "Genetic Engineering",
    "C12Q": "Bioassays & Diagnostics",
    "F03D": "Wind Power",
    "H02S": "Solar Cells",
    "G16H": "Healthcare Informatics",
    "G16B": "Bioinformatics",
}

INDICATORS = {
    "PATENT_SEARCH": {
        "name": "Patent Application Search",
        "description": "Search USPTO patent applications by keyword, assignee, or CPC class",
        "frequency": "daily",
        "unit": "patents",
    },
    "PATENT_GRANTS_BY_ASSIGNEE": {
        "name": "Patent Grants by Assignee",
        "description": "Patent filing count and details for a specific company/assignee",
        "frequency": "daily",
        "unit": "patents",
    },
    "TOP_ASSIGNEES": {
        "name": "Top Patent Assignees",
        "description": "Most active patent filers in recent filings",
        "frequency": "daily",
        "unit": "patents",
    },
    "TECH_TRENDS": {
        "name": "Technology Trend by CPC Class",
        "description": "Patent activity for a specific CPC technology classification",
        "frequency": "daily",
        "unit": "patents",
    },
    "PATENT_DETAIL": {
        "name": "Single Patent Detail",
        "description": "Full metadata for a specific patent by application or grant number",
        "frequency": "on-demand",
        "unit": "patent",
    },
}


def _get_api_key() -> Optional[str]:
    return os.environ.get("USPTO_ODP_API_KEY")


def _cache_path(indicator: str, params_hash: str) -> Path:
    safe = indicator.replace("/", "_").replace(" ", "_")
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


def _api_request(endpoint: str, params: Optional[Dict] = None, method: str = "GET") -> Dict:
    """Make an authenticated request to the ODP API with rate limiting and retries."""
    api_key = _get_api_key()
    if not api_key:
        return {
            "success": False,
            "error": "USPTO_ODP_API_KEY not set. Register at https://data.uspto.gov/apis/getting-started",
        }

    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Accept": "application/json",
        "X-API-KEY": api_key,
        "User-Agent": "QuantClaw-Data/1.0",
    }

    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(RATE_LIMIT_DELAY)
            if method == "GET":
                resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            else:
                resp = requests.post(url, headers=headers, json=params, timeout=REQUEST_TIMEOUT)

            if resp.status_code == 429:
                wait = RETRY_BACKOFF * (attempt + 1) * 2
                time.sleep(wait)
                continue

            if resp.status_code == 403:
                return {"success": False, "error": "API key invalid or expired (HTTP 403)"}
            if resp.status_code == 401:
                return {"success": False, "error": "Authentication failed (HTTP 401)"}

            resp.raise_for_status()
            return {"success": True, "data": resp.json()}

        except requests.Timeout:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF * (attempt + 1))
                continue
            return {"success": False, "error": "Request timed out after retries"}
        except requests.ConnectionError:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF * (attempt + 1))
                continue
            return {"success": False, "error": "Connection failed after retries"}
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            return {"success": False, "error": f"HTTP {status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "Max retries exceeded (rate limited)"}


def _resolve_assignee(name_or_ticker: str) -> str:
    """Resolve a ticker symbol to an assignee name, or return as-is."""
    upper = name_or_ticker.upper()
    return TICKER_TO_ASSIGNEE.get(upper, name_or_ticker)


def _extract_patent_fields(app: Dict) -> Dict:
    """Extract structured fields from an ODP patent application response."""
    result = {
        "application_number": app.get("applicationNumberText", ""),
        "filing_date": app.get("filingDate", ""),
        "patent_title": "",
        "assignee": "",
        "cpc_classes": [],
        "status": app.get("applicationStatusDescriptionText", ""),
        "grant_date": "",
        "patent_number": "",
    }

    inv_bag = app.get("inventionTitleBag", {})
    titles = inv_bag.get("inventionTitle", []) if isinstance(inv_bag, dict) else []
    if titles and isinstance(titles, list) and len(titles) > 0:
        first = titles[0]
        result["patent_title"] = first.get("inventionTitleText", "") if isinstance(first, dict) else str(first)
    elif isinstance(inv_bag, str):
        result["patent_title"] = inv_bag

    party_bag = app.get("applicantBag", {})
    applicants = party_bag.get("applicant", []) if isinstance(party_bag, dict) else []
    if applicants and isinstance(applicants, list):
        for a in applicants:
            contact = a.get("contactBag", {}) if isinstance(a, dict) else {}
            contacts = contact.get("contact", []) if isinstance(contact, dict) else []
            if contacts and isinstance(contacts, list):
                first_contact = contacts[0] if contacts else {}
                name = first_contact.get("organizationNameText", "") or first_contact.get("personFullName", "")
                if name:
                    result["assignee"] = name
                    break

    assign_bag = app.get("assignmentBag", {})
    if isinstance(assign_bag, dict):
        assignments = assign_bag.get("assignment", [])
        if assignments and isinstance(assignments, list):
            first_assign = assignments[0] if assignments else {}
            assignee_bag = first_assign.get("assigneeBag", {}) if isinstance(first_assign, dict) else {}
            assignees = assignee_bag.get("assignee", []) if isinstance(assignee_bag, dict) else []
            if assignees and isinstance(assignees, list):
                first_ae = assignees[0] if assignees else {}
                result["assignee"] = first_ae.get("assigneeNameText", result["assignee"])

    cpc_bag = app.get("cpcClassificationBag", {})
    cpcs = cpc_bag.get("cpcClassification", []) if isinstance(cpc_bag, dict) else []
    if cpcs and isinstance(cpcs, list):
        for c in cpcs:
            if isinstance(c, dict):
                section = c.get("cpcClassificationText", "") or c.get("cpcSectionCode", "")
                if section:
                    result["cpc_classes"].append(section)
            elif isinstance(c, str):
                result["cpc_classes"].append(c)

    grant_bag = app.get("patentGrantIdentification", {})
    if isinstance(grant_bag, dict):
        result["grant_date"] = grant_bag.get("grantDate", "")
        result["patent_number"] = grant_bag.get("patentNumber", "")

    event_bag = app.get("eventDataBag", {})
    if isinstance(event_bag, dict):
        events = event_bag.get("eventData", [])
        if events and isinstance(events, list):
            last = events[-1] if events else {}
            if isinstance(last, dict):
                result["grant_date"] = result["grant_date"] or last.get("eventDate", "")

    return result


def search_patents(query: str, rows: int = 25, start: int = 0) -> Dict:
    """Search patent applications using Lucene/Solr query syntax."""
    cache_params = {"q": query, "rows": rows, "start": start}
    cp = _cache_path("search", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {"searchText": query, "rows": rows, "start": start}
    result = _api_request("/patent/applications/search", params=params)
    if not result["success"]:
        return {"success": False, "query": query, "error": result["error"]}

    data = result["data"]

    patents = []
    results_bag = data.get("patentFileWrapperSearchResults", [])
    if not isinstance(results_bag, list):
        results_bag = data.get("results", [])
    if not isinstance(results_bag, list):
        for key in data:
            if isinstance(data[key], list):
                results_bag = data[key]
                break

    if isinstance(results_bag, list):
        for app in results_bag:
            if isinstance(app, dict):
                patents.append(_extract_patent_fields(app))

    total = data.get("recordTotalQuantity", data.get("totalCount", len(patents)))

    response = {
        "success": True,
        "indicator": "PATENT_SEARCH",
        "query": query,
        "total_results": total,
        "returned": len(patents),
        "start": start,
        "patents": patents,
        "source": f"{BASE_URL}/patent/applications/search",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def patent_grants_by_assignee(assignee_or_ticker: str, rows: int = 25) -> Dict:
    """Get patent filings for a specific assignee (company name or ticker)."""
    assignee = _resolve_assignee(assignee_or_ticker)
    query = f'assigneeEntityName:"{assignee}"'

    cache_params = {"assignee": assignee, "rows": rows}
    cp = _cache_path("grants_by_assignee", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = search_patents(query, rows=rows)
    if not result.get("success"):
        return {
            "success": False,
            "assignee": assignee,
            "ticker_input": assignee_or_ticker,
            "error": result.get("error", "Search failed"),
        }

    cpc_counter = Counter()
    for p in result.get("patents", []):
        for cpc in p.get("cpc_classes", []):
            cpc_4 = cpc[:4] if len(cpc) >= 4 else cpc
            cpc_counter[cpc_4] += 1

    top_cpc = [
        {"cpc_class": k, "name": CPC_CLASS_NAMES.get(k, ""), "count": v}
        for k, v in cpc_counter.most_common(10)
    ]

    response = {
        "success": True,
        "indicator": "PATENT_GRANTS_BY_ASSIGNEE",
        "assignee": assignee,
        "ticker_input": assignee_or_ticker,
        "total_filings": result.get("total_results", 0),
        "returned": result.get("returned", 0),
        "top_cpc_classes": top_cpc,
        "patents": result.get("patents", []),
        "source": f"{BASE_URL}/patent/applications/search",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def tech_trends(cpc_class: str, rows: int = 25) -> Dict:
    """Get patent activity for a specific CPC technology classification."""
    cpc_upper = cpc_class.upper()
    query = f'cpcClassificationBag:"{cpc_upper}"'

    cache_params = {"cpc": cpc_upper, "rows": rows}
    cp = _cache_path("tech_trends", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = search_patents(query, rows=rows)
    if not result.get("success"):
        return {
            "success": False,
            "cpc_class": cpc_upper,
            "error": result.get("error", "Search failed"),
        }

    assignee_counter = Counter()
    for p in result.get("patents", []):
        a = p.get("assignee", "Unknown")
        if a:
            assignee_counter[a] += 1

    top_assignees = [
        {"assignee": k, "count": v}
        for k, v in assignee_counter.most_common(15)
    ]

    response = {
        "success": True,
        "indicator": "TECH_TRENDS",
        "cpc_class": cpc_upper,
        "cpc_name": CPC_CLASS_NAMES.get(cpc_upper, ""),
        "total_patents": result.get("total_results", 0),
        "returned": result.get("returned", 0),
        "top_assignees_in_class": top_assignees,
        "patents": result.get("patents", []),
        "source": f"{BASE_URL}/patent/applications/search",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def top_assignees(rows: int = 100) -> Dict:
    """Get top patent assignees from recent filings."""
    cache_params = {"cmd": "top_assignees", "rows": rows}
    cp = _cache_path("top_assignees", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    query = "*:*"
    result = search_patents(query, rows=rows)
    if not result.get("success"):
        return {"success": False, "error": result.get("error", "Search failed")}

    assignee_counter = Counter()
    for p in result.get("patents", []):
        a = p.get("assignee", "")
        if a:
            assignee_counter[a] += 1

    ranked = [
        {"rank": i + 1, "assignee": k, "patent_count": v}
        for i, (k, v) in enumerate(assignee_counter.most_common(50))
    ]

    response = {
        "success": True,
        "indicator": "TOP_ASSIGNEES",
        "total_patents_sampled": result.get("total_results", 0),
        "unique_assignees": len(assignee_counter),
        "top_assignees": ranked,
        "source": f"{BASE_URL}/patent/applications/search",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_patent_detail(patent_number: str) -> Dict:
    """Get full details for a specific patent by application or grant number."""
    clean = patent_number.replace(",", "").replace(" ", "").replace("/", "")

    cache_params = {"patent": clean}
    cp = _cache_path("patent_detail", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(f"/patent/applications/{clean}/")
    if not result["success"]:
        result2 = search_patents(f'patentNumber:"{patent_number}"', rows=1)
        if result2.get("success") and result2.get("patents"):
            patent_data = result2["patents"][0]
            response = {
                "success": True,
                "indicator": "PATENT_DETAIL",
                "patent": patent_data,
                "source": "search_fallback",
                "timestamp": datetime.now().isoformat(),
            }
            _write_cache(cp, response)
            return response
        return {"success": False, "patent_number": patent_number, "error": result["error"]}

    data = result["data"]
    patent_data = _extract_patent_fields(data) if isinstance(data, dict) else data

    response = {
        "success": True,
        "indicator": "PATENT_DETAIL",
        "patent": patent_data,
        "raw_fields": list(data.keys()) if isinstance(data, dict) else [],
        "source": f"{BASE_URL}/patent/applications/{clean}/",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def fetch_data(indicator: str, **kwargs) -> Dict:
    """Fetch a specific indicator with optional parameters."""
    indicator_upper = indicator.upper()

    if indicator_upper == "PATENT_SEARCH":
        query = kwargs.get("query", "*:*")
        rows = int(kwargs.get("rows", 25))
        return search_patents(query, rows=rows)
    elif indicator_upper == "PATENT_GRANTS_BY_ASSIGNEE":
        assignee = kwargs.get("assignee", "")
        if not assignee:
            return {"success": False, "error": "assignee parameter required"}
        return patent_grants_by_assignee(assignee)
    elif indicator_upper == "TOP_ASSIGNEES":
        return top_assignees()
    elif indicator_upper == "TECH_TRENDS":
        cpc = kwargs.get("cpc_class", "")
        if not cpc:
            return {"success": False, "error": "cpc_class parameter required"}
        return tech_trends(cpc)
    elif indicator_upper == "PATENT_DETAIL":
        patent_num = kwargs.get("patent_number", "")
        if not patent_num:
            return {"success": False, "error": "patent_number parameter required"}
        return get_patent_detail(patent_num)
    else:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest data for one or all indicators. Without API key, returns indicator list."""
    if indicator:
        return fetch_data(indicator)

    api_key = _get_api_key()
    if not api_key:
        return {
            "success": False,
            "source": "USPTO Open Data Portal (PatentsView)",
            "error": "USPTO_ODP_API_KEY not set. Register at https://data.uspto.gov/apis/getting-started",
            "available_indicators": list(INDICATORS.keys()),
            "ticker_map_sample": dict(list(TICKER_TO_ASSIGNEE.items())[:10]),
            "cpc_classes": CPC_CLASS_NAMES,
        }

    result = search_patents("*:*", rows=5)
    return {
        "success": result.get("success", False),
        "source": "USPTO Open Data Portal (PatentsView)",
        "latest_patents": result.get("patents", []),
        "total_available": result.get("total_results", 0),
        "available_indicators": list(INDICATORS.keys()),
        "error": result.get("error"),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
USPTO PatentsView Module (Initiative 0046)
Data Source: USPTO Open Data Portal (https://api.uspto.gov/api/v1)

Setup:
  export USPTO_ODP_API_KEY=your-key
  Register at https://data.uspto.gov/apis/getting-started

Usage:
  python patentsview_uspto.py                                  # Latest patent data
  python patentsview_uspto.py list                             # List indicators
  python patentsview_uspto.py search <query>                   # Search patents
  python patentsview_uspto.py patent_grants_by_assignee <name> # Patents by company/ticker
  python patentsview_uspto.py tech_trends <CPC_CLASS>          # e.g., H01L (semiconductors)
  python patentsview_uspto.py top_assignees                    # Most active filers
  python patentsview_uspto.py detail <patent_number>           # Single patent detail
  python patentsview_uspto.py tickers                          # Show ticker->assignee map
  python patentsview_uspto.py cpc_classes                      # Show CPC class names

Ticker Examples: AAPL, MSFT, GOOG, NVDA, PFE, IBM
CPC Examples: H01L (semiconductors), A61K (pharma), G06N (AI/ML), G06F (computing)
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "tickers":
            print(json.dumps(TICKER_TO_ASSIGNEE, indent=2, default=str))
        elif cmd == "cpc_classes":
            print(json.dumps(CPC_CLASS_NAMES, indent=2, default=str))
        elif cmd == "search":
            query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "*:*"
            print(json.dumps(search_patents(query), indent=2, default=str))
        elif cmd == "patent_grants_by_assignee":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Usage: patent_grants_by_assignee <name_or_ticker>"}, indent=2))
            else:
                assignee = " ".join(sys.argv[2:])
                print(json.dumps(patent_grants_by_assignee(assignee), indent=2, default=str))
        elif cmd == "tech_trends":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Usage: tech_trends <CPC_CLASS>", "classes": CPC_CLASS_NAMES}, indent=2))
            else:
                print(json.dumps(tech_trends(sys.argv[2]), indent=2, default=str))
        elif cmd == "top_assignees":
            print(json.dumps(top_assignees(), indent=2, default=str))
        elif cmd == "detail":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Usage: detail <patent_number>"}, indent=2))
            else:
                print(json.dumps(get_patent_detail(sys.argv[2]), indent=2, default=str))
        else:
            result = fetch_data(cmd, **dict(
                zip(sys.argv[2::2], sys.argv[3::2])
            )) if len(sys.argv) > 2 else get_latest(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))

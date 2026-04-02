#!/usr/bin/env python3
"""
European Patent Office — Open Patent Services (OPS) Module

Global patent data from 100+ patent authorities via EPO's DOCDB database.
Search patents by keyword/applicant/IPC class, resolve patent families,
track EP register status, and detect technology filing trends.

Data Source: https://ops.epo.org/3.2/rest-services
Protocol: REST (OAuth2 client credentials)
Auth: EPO_CONSUMER_KEY + EPO_CONSUMER_SECRET from .env
Refresh: 24h cache (patent data is static once published)
Coverage: Worldwide (100M+ patent documents)

Author: QUANTCLAW DATA Build Agent
Initiative: 0053
"""

import json
import sys
import time
import hashlib
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

BASE_URL = "https://ops.epo.org/3.2/rest-services"
AUTH_URL = "https://ops.epo.org/3.2/auth/accesstoken"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "epo_ops"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
RATE_LIMIT_RPS = 10
MIN_REQUEST_INTERVAL = 1.0 / RATE_LIMIT_RPS

NS = {
    "ops": "http://ops.epo.org",
    "ex": "http://www.epo.org/exchange",
    "reg": "http://www.epo.org/register",
}

_token_cache: Dict = {"access_token": None, "expires_at": 0}
_last_request_time: float = 0.0

INDICATORS = {
    "PATENT_SEARCH": {
        "name": "Patent Full-Text Search",
        "description": "Search worldwide patents by keyword in title/abstract",
        "endpoint": "published-data/search",
        "frequency": "on-demand",
        "unit": "patent documents",
    },
    "APPLICANT_FILINGS": {
        "name": "Applicant Patent Filings",
        "description": "Patents filed by a specific applicant/company",
        "endpoint": "published-data/search",
        "frequency": "on-demand",
        "unit": "patent documents",
    },
    "PATENT_FAMILY": {
        "name": "Patent Family Members",
        "description": "Cross-office filings for the same invention (EP/WO/US/JP/CN)",
        "endpoint": "family/publication/epodoc",
        "frequency": "on-demand",
        "unit": "family members",
    },
    "EP_REGISTER": {
        "name": "EP Register Status",
        "description": "European patent register: grant status, opposition, procedural data",
        "endpoint": "register/publication/epodoc",
        "frequency": "on-demand",
        "unit": "status record",
    },
    "IPC_TRENDS": {
        "name": "Technology Sector Filing Trends",
        "description": "Patent filing volume by IPC class at EPO over time",
        "endpoint": "published-data/search",
        "frequency": "on-demand",
        "unit": "filing counts",
    },
    "RECENT_GRANTS": {
        "name": "Recent EP Patent Grants",
        "description": "Recently granted European patents",
        "endpoint": "published-data/search",
        "frequency": "weekly",
        "unit": "patent documents",
    },
}


# ---------------------------------------------------------------------------
# Credentials & Auth
# ---------------------------------------------------------------------------

def _load_credentials() -> Tuple[Optional[str], Optional[str]]:
    key = os.environ.get("EPO_CONSUMER_KEY")
    secret = os.environ.get("EPO_CONSUMER_SECRET")
    if key and secret:
        return key, secret

    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k == "EPO_CONSUMER_KEY":
                key = v
            elif k == "EPO_CONSUMER_SECRET":
                secret = v
    return key, secret


def _get_access_token() -> Optional[str]:
    global _token_cache

    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    key, secret = _load_credentials()
    if not key or not secret:
        return None

    try:
        resp = requests.post(
            AUTH_URL,
            data={"grant_type": "client_credentials"},
            auth=(key, secret),
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        token_data = resp.json()
        _token_cache["access_token"] = token_data["access_token"]
        _token_cache["expires_at"] = time.time() + int(token_data.get("expires_in", 1200))
        return _token_cache["access_token"]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Rate limiting & caching
# ---------------------------------------------------------------------------

def _rate_limit():
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


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


# ---------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------

def _api_get(endpoint: str, params: dict = None) -> Dict:
    token = _get_access_token()
    if not token:
        return {
            "success": False,
            "error": "No EPO credentials. Set EPO_CONSUMER_KEY and EPO_CONSUMER_SECRET in .env",
        }

    _rate_limit()

    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/xml",
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)

        if resp.status_code == 403:
            retry_after = resp.headers.get("Retry-After", "5")
            try:
                wait = min(int(retry_after), 30)
            except ValueError:
                wait = 5
            time.sleep(wait)
            resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)

        if resp.status_code == 404:
            return {"success": False, "error": "Not found (HTTP 404)"}

        resp.raise_for_status()
        return {"success": True, "data": resp.text}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        body = ""
        if e.response is not None:
            body = e.response.text[:300]
        return {"success": False, "error": f"HTTP {status}: {body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# XML parsers
# ---------------------------------------------------------------------------

def _fmt_date(raw: str) -> str:
    if raw and len(raw) == 8:
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


def _parse_exchange_document(doc) -> Optional[Dict]:
    try:
        entry = {
            "country": doc.get("country", ""),
            "doc_number": doc.get("doc-number", ""),
            "kind": doc.get("kind", ""),
        }
        entry["doc_id"] = f"{entry['country']}{entry['doc_number']}{entry['kind']}"

        family_id = doc.get("family-id", "")
        if family_id:
            entry["family_id"] = family_id

        biblio = doc.find(".//ex:bibliographic-data", NS)
        if biblio is None:
            return entry

        for title_el in biblio.findall(".//ex:invention-title", NS):
            lang = title_el.get("lang", "")
            if lang == "en" or not entry.get("title"):
                if title_el.text:
                    entry["title"] = title_el.text.strip()

        applicants = []
        for app in biblio.findall(".//ex:applicant", NS):
            name_el = app.find(".//ex:name", NS)
            if name_el is not None and name_el.text:
                applicants.append(name_el.text.strip())
        if applicants:
            entry["applicants"] = applicants

        ipcs = []
        for ipc in biblio.findall(".//ex:classifications-ipcr/ex:classification-ipcr/ex:text", NS):
            if ipc.text:
                ipcs.append(ipc.text.strip().split()[0])
        if not ipcs:
            for ipc in biblio.findall(".//ex:classification-ipc/ex:text", NS):
                if ipc.text:
                    ipcs.append(ipc.text.strip())
        if ipcs:
            entry["ipc_classes"] = list(dict.fromkeys(ipcs))[:5]

        pub_ref = biblio.find(".//ex:publication-reference/ex:document-id[@document-id-type='epodoc']", NS)
        if pub_ref is None:
            pub_ref = biblio.find(".//ex:publication-reference/ex:document-id", NS)
        if pub_ref is not None:
            date_el = pub_ref.find("ex:date", NS)
            if date_el is not None and date_el.text:
                entry["publication_date"] = _fmt_date(date_el.text.strip())

        app_ref = biblio.find(".//ex:application-reference/ex:document-id[@document-id-type='epodoc']", NS)
        if app_ref is None:
            app_ref = biblio.find(".//ex:application-reference/ex:document-id", NS)
        if app_ref is not None:
            date_el = app_ref.find("ex:date", NS)
            if date_el is not None and date_el.text:
                entry["application_date"] = _fmt_date(date_el.text.strip())

        return entry
    except Exception:
        return None


def _parse_search_results(xml_text: str) -> List[Dict]:
    results = []
    try:
        root = ET.fromstring(xml_text)
        search_result = root.find(".//ops:search-result", NS)
        if search_result is None:
            return results
        for doc in search_result.findall(".//ex:exchange-document", NS):
            entry = _parse_exchange_document(doc)
            if entry:
                results.append(entry)
    except ET.ParseError:
        pass
    return results


def _get_total_count(xml_text: str) -> int:
    try:
        root = ET.fromstring(xml_text)
        sr = root.find(".//ops:search-result", NS)
        if sr is not None:
            return int(sr.get("total-result-count", "0"))
        biblio_search = root.find(".//ops:biblio-search", NS)
        if biblio_search is not None:
            return int(biblio_search.get("total-result-count", "0"))
    except (ET.ParseError, ValueError):
        pass
    return 0


def _parse_biblio_response(xml_text: str) -> List[Dict]:
    results = []
    try:
        root = ET.fromstring(xml_text)
        for doc in root.findall(".//ex:exchange-document", NS):
            entry = _parse_exchange_document(doc)
            if entry:
                results.append(entry)
    except ET.ParseError:
        pass
    return results


def _parse_family_response(xml_text: str) -> Dict:
    members = []
    try:
        root = ET.fromstring(xml_text)
        for member in root.findall(".//ops:patent-family/ops:family-member", NS):
            pub = member.find(
                ".//ex:publication-reference/ex:document-id[@document-id-type='epodoc']", NS
            )
            if pub is None:
                pub = member.find(".//ex:publication-reference/ex:document-id", NS)
            if pub is None:
                continue

            country = pub.findtext("ex:country", "", NS)
            number = pub.findtext("ex:doc-number", "", NS)
            kind = pub.findtext("ex:kind", "", NS)
            date_text = pub.findtext("ex:date", "", NS)

            members.append({
                "country": country,
                "doc_number": number,
                "kind": kind,
                "doc_id": f"{country}{number}{kind}",
                "publication_date": _fmt_date(date_text),
            })
    except ET.ParseError:
        pass

    return {
        "members": members,
        "family_size": len(members),
        "jurisdictions": sorted(set(m["country"] for m in members if m["country"])),
    }


def _parse_register_response(xml_text: str) -> Dict:
    result: Dict = {}
    try:
        root = ET.fromstring(xml_text)
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag == "status" and elem.text and "status" not in result:
                result["status"] = elem.text.strip()
            elif tag == "invention-title" and elem.text:
                lang = elem.get("lang", "")
                if lang == "en" or "title" not in result:
                    result["title"] = elem.text.strip()
            elif tag == "name" and elem.text and "applicant" not in result:
                result["applicant"] = elem.text.strip()
            elif tag == "date-of-filing-of-opposition" and elem.text:
                result["opposition_date"] = _fmt_date(elem.text.strip())
            elif tag == "date" and elem.text and "effective_date" not in result:
                result["effective_date"] = _fmt_date(elem.text.strip())
    except ET.ParseError:
        pass
    return result


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------

def search_patents(query: str, max_results: int = 25) -> Dict:
    """Search patents by keyword in title/abstract."""
    cache_params = {"type": "search", "query": query, "max": max_results}
    cp = _cache_path("search", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    cql = f'ta="{query}"'
    result = _api_get(
        "published-data/search/full-cycle",
        params={"q": cql, "Range": f"1-{min(max_results, 100)}"},
    )
    if not result["success"]:
        return {"success": False, "error": result["error"], "query": query}

    patents = _parse_search_results(result["data"])
    total = _get_total_count(result["data"])

    response = {
        "success": True,
        "indicator": "PATENT_SEARCH",
        "query": query,
        "total_results": total,
        "returned": len(patents),
        "patents": patents,
        "source": "EPO Open Patent Services",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def search_applicant(applicant: str, max_results: int = 25) -> Dict:
    """Search patents by applicant name."""
    cache_params = {"type": "applicant", "applicant": applicant, "max": max_results}
    cp = _cache_path("applicant", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    cql = f'pa="{applicant}"'
    result = _api_get(
        "published-data/search/full-cycle",
        params={"q": cql, "Range": f"1-{min(max_results, 100)}"},
    )
    if not result["success"]:
        return {"success": False, "error": result["error"], "applicant": applicant}

    patents = _parse_search_results(result["data"])
    total = _get_total_count(result["data"])

    response = {
        "success": True,
        "indicator": "APPLICANT_FILINGS",
        "applicant": applicant,
        "total_filings": total,
        "returned": len(patents),
        "patents": patents,
        "source": "EPO Open Patent Services",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def get_patent_family(doc_id: str) -> Dict:
    """Get patent family members for a document."""
    cache_params = {"type": "family", "doc_id": doc_id}
    cp = _cache_path("family", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get(f"family/publication/epodoc/{doc_id}")
    if not result["success"]:
        return {"success": False, "error": result["error"], "doc_id": doc_id}

    family = _parse_family_response(result["data"])

    response = {
        "success": True,
        "indicator": "PATENT_FAMILY",
        "doc_id": doc_id,
        "family_size": family["family_size"],
        "jurisdictions": family["jurisdictions"],
        "members": family["members"],
        "source": "EPO Open Patent Services",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def get_patent_biblio(doc_id: str) -> Dict:
    """Get bibliographic data for a specific patent."""
    cache_params = {"type": "biblio", "doc_id": doc_id}
    cp = _cache_path("biblio", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get(f"published-data/publication/epodoc/{doc_id}/biblio")
    if not result["success"]:
        return {"success": False, "error": result["error"], "doc_id": doc_id}

    patents = _parse_biblio_response(result["data"])

    response = {
        "success": True,
        "indicator": "PATENT_BIBLIO",
        "doc_id": doc_id,
        "data": patents[0] if patents else {},
        "source": "EPO Open Patent Services",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def get_register_status(doc_id: str) -> Dict:
    """Get EP register status for a European patent."""
    cache_params = {"type": "register", "doc_id": doc_id}
    cp = _cache_path("register", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get(f"register/publication/epodoc/{doc_id}/biblio")
    if not result["success"]:
        return {"success": False, "error": result["error"], "doc_id": doc_id}

    reg_info = _parse_register_response(result["data"])

    response = {
        "success": True,
        "indicator": "EP_REGISTER",
        "doc_id": doc_id,
        "register": reg_info,
        "source": "EPO Open Patent Services — Register",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def search_ipc_class(ipc_class: str, max_results: int = 25) -> Dict:
    """Search patents by IPC/CPC class with filing trend data."""
    cache_params = {"type": "ipc_trends", "ipc": ipc_class, "max": max_results}
    cp = _cache_path("ipc_trends", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    current_year = datetime.now().year
    yearly_counts: Dict[str, int] = {}

    cql = f'ic="{ipc_class}"'
    result = _api_get(
        "published-data/search/full-cycle",
        params={"q": cql, "Range": f"1-{min(max_results, 100)}"},
    )
    if not result["success"]:
        return {"success": False, "error": result["error"], "ipc_class": ipc_class}

    patents = _parse_search_results(result["data"])
    total = _get_total_count(result["data"])

    for year_offset in range(5):
        year = current_year - year_offset
        year_cql = f'ic="{ipc_class}" and pd within "{year}0101 {year}1231"'
        yr_result = _api_get(
            "published-data/search",
            params={"q": year_cql, "Range": "1-1"},
        )
        if yr_result["success"]:
            yearly_counts[str(year)] = _get_total_count(yr_result["data"])
        _rate_limit()

    response = {
        "success": True,
        "indicator": "IPC_TRENDS",
        "ipc_class": ipc_class,
        "total_results": total,
        "yearly_filing_counts": yearly_counts,
        "returned": len(patents),
        "recent_patents": patents,
        "source": "EPO Open Patent Services",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def get_recent_grants(max_results: int = 25) -> Dict:
    """Get recently published European patents."""
    cache_params = {"type": "recent_grants", "max": max_results}
    cp = _cache_path("recent_grants", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    today = datetime.now()
    month_ago = today - timedelta(days=30)
    date_from = month_ago.strftime("%Y%m%d")
    date_to = today.strftime("%Y%m%d")

    cql = f'pn=EP and pd within "{date_from} {date_to}"'
    result = _api_get(
        "published-data/search/full-cycle",
        params={"q": cql, "Range": f"1-{min(max_results, 100)}"},
    )
    if not result["success"]:
        return {"success": False, "error": result["error"]}

    patents = _parse_search_results(result["data"])
    total = _get_total_count(result["data"])

    response = {
        "success": True,
        "indicator": "RECENT_GRANTS",
        "date_range": {"from": _fmt_date(date_from), "to": _fmt_date(date_to)},
        "total_results": total,
        "returned": len(patents),
        "patents": patents,
        "source": "EPO Open Patent Services",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


# ---------------------------------------------------------------------------
# Standard module interface
# ---------------------------------------------------------------------------

def fetch_data(indicator: str, **kwargs) -> Dict:
    """Fetch data for a specific indicator."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }

    dispatch = {
        "PATENT_SEARCH": lambda: search_patents(
            kwargs.get("query", ""), kwargs.get("max_results", 25)
        ),
        "APPLICANT_FILINGS": lambda: search_applicant(
            kwargs.get("applicant", ""), kwargs.get("max_results", 25)
        ),
        "PATENT_FAMILY": lambda: get_patent_family(kwargs.get("doc_id", "")),
        "EP_REGISTER": lambda: get_register_status(kwargs.get("doc_id", "")),
        "IPC_TRENDS": lambda: search_ipc_class(
            kwargs.get("ipc_class", ""), kwargs.get("max_results", 25)
        ),
        "RECENT_GRANTS": lambda: get_recent_grants(kwargs.get("max_results", 25)),
    }
    return dispatch[indicator]()


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
    """Get latest data — defaults to recent EP grants summary."""
    if indicator:
        return fetch_data(indicator)
    return get_recent_grants()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_help():
    print("""
European Patent Office — Open Patent Services (OPS) Module

Usage:
  python epo_ops.py                                    # Recent EP patent publications
  python epo_ops.py search "autonomous driving"        # Full-text patent search
  python epo_ops.py applicant "Samsung"                # Patents by applicant
  python epo_ops.py family EP3456789                   # Patent family members
  python epo_ops.py biblio EP3456789                   # Bibliographic data
  python epo_ops.py register EP3456789                 # EP register status
  python epo_ops.py tech_trends H01L                   # IPC class filing trends
  python epo_ops.py list                               # List available indicators

Environment:
  EPO_CONSUMER_KEY      OAuth2 consumer key  (register at developers.epo.org)
  EPO_CONSUMER_SECRET   OAuth2 consumer secret

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<22s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: REST + OAuth2
Coverage: 100M+ patents from 100+ authorities
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "search":
            query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
            if not query:
                print(json.dumps({"success": False, "error": "Usage: epo_ops.py search <query>"}, indent=2))
            else:
                print(json.dumps(search_patents(query), indent=2, default=str))
        elif cmd == "applicant":
            name = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
            if not name:
                print(json.dumps({"success": False, "error": "Usage: epo_ops.py applicant <name>"}, indent=2))
            else:
                print(json.dumps(search_applicant(name), indent=2, default=str))
        elif cmd == "family":
            doc_id = sys.argv[2] if len(sys.argv) > 2 else ""
            if not doc_id:
                print(json.dumps({"success": False, "error": "Usage: epo_ops.py family <doc_id>"}, indent=2))
            else:
                print(json.dumps(get_patent_family(doc_id), indent=2, default=str))
        elif cmd == "biblio":
            doc_id = sys.argv[2] if len(sys.argv) > 2 else ""
            if not doc_id:
                print(json.dumps({"success": False, "error": "Usage: epo_ops.py biblio <doc_id>"}, indent=2))
            else:
                print(json.dumps(get_patent_biblio(doc_id), indent=2, default=str))
        elif cmd == "register":
            doc_id = sys.argv[2] if len(sys.argv) > 2 else ""
            if not doc_id:
                print(json.dumps({"success": False, "error": "Usage: epo_ops.py register <doc_id>"}, indent=2))
            else:
                print(json.dumps(get_register_status(doc_id), indent=2, default=str))
        elif cmd in ("tech_trends", "tech-trends", "ipc"):
            ipc = sys.argv[2] if len(sys.argv) > 2 else ""
            if not ipc:
                print(json.dumps({"success": False, "error": "Usage: epo_ops.py tech_trends <IPC_CLASS>"}, indent=2))
            else:
                print(json.dumps(search_ipc_class(ipc), indent=2, default=str))
        else:
            result = fetch_data(cmd.upper())
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))

#!/usr/bin/env python3
"""
FCA UK Financial Services Register Module

UK Financial Conduct Authority public register: authorized firms, approved
individuals, collective investment schemes, regulated markets, permissions,
and disciplinary history.

Data Source: https://register.fca.org.uk/services/V0.1
Protocol: REST JSON (FCA Register API V0.1)
Auth: API key + email (free at https://register.fca.org.uk/Developer/s/)
Env: FCA_API_KEY, FCA_API_EMAIL in .env
Coverage: United Kingdom

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import json
import os
import sys
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://register.fca.org.uk/services/V0.1"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "fca_uk"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30

INDICATORS = {
    "FIRM_SEARCH": {
        "endpoint": "search",
        "search_type": "firm",
        "name": "Firm Search",
        "description": "Search FCA-authorized firms by name or FRN",
        "query_label": "firm name or FRN",
    },
    "INDIVIDUAL_SEARCH": {
        "endpoint": "search",
        "search_type": "individual",
        "name": "Individual Search",
        "description": "Search approved/prohibited individuals by name",
        "query_label": "individual name",
    },
    "FUND_SEARCH": {
        "endpoint": "search",
        "search_type": "fund",
        "name": "Fund / CIS Search",
        "description": "Search collective investment schemes by name or PRN",
        "query_label": "fund name or PRN",
    },
    "FIRM_DETAILS": {
        "endpoint": "firm",
        "name": "Firm Details by FRN",
        "description": "Full regulatory details for a firm (status, type, Companies House number)",
        "query_label": "FRN (e.g. 122702)",
    },
    "FIRM_PERMISSIONS": {
        "endpoint": "firm_sub",
        "sub_path": "Permissions",
        "name": "Firm Permissions",
        "description": "Regulated activities and permissions granted to a firm",
        "query_label": "FRN",
    },
    "FIRM_INDIVIDUALS": {
        "endpoint": "firm_sub",
        "sub_path": "Individuals",
        "name": "Firm Individuals",
        "description": "Approved individuals and controlled functions at a firm",
        "query_label": "FRN",
    },
    "FIRM_PASSPORTS": {
        "endpoint": "firm_sub",
        "sub_path": "Passports",
        "name": "Firm Passports",
        "description": "Cross-border passporting permissions for a firm",
        "query_label": "FRN",
    },
    "FIRM_DISCIPLINARY": {
        "endpoint": "firm_sub",
        "sub_path": "DisciplinaryHistory",
        "name": "Firm Disciplinary History",
        "description": "Enforcement actions, fines, and disciplinary measures",
        "query_label": "FRN",
    },
    "FIRM_REQUIREMENTS": {
        "endpoint": "firm_sub",
        "sub_path": "Requirements",
        "name": "Firm Requirements",
        "description": "Regulatory requirements and conditions imposed on a firm",
        "query_label": "FRN",
    },
    "FIRM_ADDRESSES": {
        "endpoint": "firm_sub",
        "sub_path": "Address",
        "name": "Firm Addresses",
        "description": "Registered addresses, phone numbers, and websites",
        "query_label": "FRN",
    },
    "FIRM_EXCLUSIONS": {
        "endpoint": "firm_sub",
        "sub_path": "Exclusions",
        "name": "Firm Exclusions",
        "description": "PSD2 and payment service exclusions for a firm",
        "query_label": "FRN",
    },
    "INDIVIDUAL_DETAILS": {
        "endpoint": "individual",
        "name": "Individual Details by IRN",
        "description": "Controlled functions and history for an approved individual",
        "query_label": "IRN (e.g. MXC29012)",
    },
    "REGULATED_MARKETS": {
        "endpoint": "regulated_markets",
        "name": "UK Regulated Markets",
        "description": "FCA-recognized regulated exchanges and trading venues",
        "query_label": None,
    },
}


def _load_env():
    """Load .env from project root if vars not already set."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env()


def _get_credentials():
    return os.environ.get("FCA_API_KEY", ""), os.environ.get("FCA_API_EMAIL", "")


def _check_auth() -> Optional[Dict]:
    api_key, api_email = _get_credentials()
    if not api_key or not api_email:
        return {
            "success": False,
            "error": "FCA API credentials not configured",
            "setup": (
                "1. Register at https://register.fca.org.uk/Developer/s/\n"
                "2. Add to .env:\n"
                "   FCA_API_KEY=<your_api_key>\n"
                "   FCA_API_EMAIL=<your_signup_email>"
            ),
        }
    return None


def _auth_headers() -> Dict[str, str]:
    api_key, api_email = _get_credentials()
    return {
        "Accept": "application/json",
        "X-Auth-Email": api_email,
        "X-Auth-Key": api_key,
    }


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


def _build_url(cfg: dict, query: str = None) -> str:
    ep = cfg["endpoint"]
    if ep == "search":
        return f"{BASE_URL}/Search"
    elif ep == "firm":
        return f"{BASE_URL}/Firm/{query}"
    elif ep == "firm_sub":
        return f"{BASE_URL}/Firm/{query}/{cfg['sub_path']}"
    elif ep == "individual":
        return f"{BASE_URL}/Individuals/{query}"
    elif ep == "regulated_markets":
        return f"{BASE_URL}/RegulatedMarkets"
    return BASE_URL


def _build_params(cfg: dict, query: str = None) -> dict:
    if cfg["endpoint"] == "search" and query:
        return {"q": query, "type": cfg["search_type"]}
    return {}


def _api_request(url: str, params: dict = None) -> Dict:
    try:
        resp = requests.get(
            url, headers=_auth_headers(), params=params, timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        return {"success": True, "raw": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        if status in (401, 403):
            return {
                "success": False,
                "error": f"Authentication failed (HTTP {status}). Check FCA_API_KEY and FCA_API_EMAIL.",
            }
        if status == 404:
            return {"success": False, "error": "Resource not found (HTTP 404)"}
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_response(raw: dict) -> dict:
    """Parse FCA API response envelope: Status / Message / Data / ResultInfo."""
    data = raw.get("Data") or raw.get("data")
    status = raw.get("Status") or raw.get("status", "")
    message = raw.get("Message") or raw.get("message", "")
    result_info = raw.get("ResultInfo") or raw.get("resultinfo")
    records = data if isinstance(data, list) else ([data] if data else [])
    return {
        "api_status": status,
        "api_message": message,
        "records": records,
        "result_info": result_info,
    }


def fetch_data(indicator: str, query: str = None) -> Dict:
    """Fetch data for a specific indicator with optional query."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }

    cfg = INDICATORS[indicator]

    if cfg.get("query_label") and not query:
        return {
            "success": False,
            "error": f"Query required for {indicator}",
            "hint": f"Provide: {cfg['query_label']}",
        }

    auth_err = _check_auth()
    if auth_err:
        return auth_err

    cache_key = {"indicator": indicator, "query": query}
    cp = _cache_path(indicator, _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    url = _build_url(cfg, query)
    params = _build_params(cfg, query)
    result = _api_request(url, params)

    if not result["success"]:
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "query": query,
            "error": result["error"],
        }

    parsed = _parse_response(result["raw"])
    records = parsed["records"]

    if not records:
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "query": query,
            "error": "No records found",
            "api_message": parsed["api_message"],
        }

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "query": query,
        "record_count": len(records),
        "records": records[:50],
        "result_info": parsed["result_info"],
        "api_status": parsed["api_status"],
        "source": url,
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
            "query_label": v.get("query_label"),
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get module info or fetch a specific indicator."""
    if indicator:
        return fetch_data(indicator)
    api_key, api_email = _get_credentials()
    return {
        "success": True,
        "source": "FCA UK Financial Services Register",
        "base_url": BASE_URL,
        "auth_configured": bool(api_key and api_email),
        "indicators": get_available_indicators(),
        "count": len(INDICATORS),
        "timestamp": datetime.now().isoformat(),
    }


def search_firm(query: str) -> Dict:
    """Search for firms by name or FRN."""
    return fetch_data("FIRM_SEARCH", query)


def search_individual(query: str) -> Dict:
    """Search for individuals by name."""
    return fetch_data("INDIVIDUAL_SEARCH", query)


def firm_status(frn: str) -> Dict:
    """Quick status check for a firm by FRN."""
    result = fetch_data("FIRM_DETAILS", frn)
    if not result.get("success"):
        return result
    records = result.get("records", [])
    if not records:
        return {"success": False, "error": "No firm data returned", "frn": frn}
    firm = records[0]
    return {
        "success": True,
        "frn": frn,
        "name": firm.get("Organisation Name", ""),
        "status": firm.get("Status", ""),
        "status_effective_date": firm.get("Status Effective Date", ""),
        "business_type": firm.get("Business Type", ""),
        "companies_house": firm.get("Companies House Number", ""),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
FCA UK Financial Services Register Module

Usage:
  python fca_uk.py                                    # Module info + auth status
  python fca_uk.py list                               # List available indicators
  python fca_uk.py FIRM_SEARCH "barclays bank"        # Search firms by name
  python fca_uk.py FIRM_DETAILS 122702                # Firm details by FRN
  python fca_uk.py INDIVIDUAL_SEARCH "mark carney"    # Search individuals
  python fca_uk.py INDIVIDUAL_DETAILS MXC29012        # Individual by IRN
  python fca_uk.py FIRM_PERMISSIONS 122702            # Firm permissions
  python fca_uk.py FIRM_DISCIPLINARY 122702           # Disciplinary history
  python fca_uk.py FIRM_PASSPORTS 122702              # Passport permissions
  python fca_uk.py REGULATED_MARKETS                  # UK regulated exchanges
  python fca_uk.py status 122702                      # Quick firm status check

Setup:
  1. Register at https://register.fca.org.uk/Developer/s/
  2. Add to .env:
     FCA_API_KEY=<your_api_key>
     FCA_API_EMAIL=<your_signup_email>

Indicators:""")
    for key, cfg in INDICATORS.items():
        label = cfg.get("query_label", "")
        lbl = f"  [{label}]" if label else ""
        print(f"  {key:<25s} {cfg['name']}{lbl}")
    print(f"""
Source: {BASE_URL}
Protocol: REST JSON (FCA Register API V0.1)
Coverage: United Kingdom
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "status" and len(sys.argv) > 2:
            print(json.dumps(firm_status(sys.argv[2]), indent=2, default=str))
        else:
            query = sys.argv[2] if len(sys.argv) > 2 else None
            result = fetch_data(cmd, query)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))

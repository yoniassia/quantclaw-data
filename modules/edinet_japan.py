#!/usr/bin/env python3
"""
EDINET Japan Securities Filings Module

Japan's Electronic Disclosure for Investors' NETwork (EDINET) — operated by
the Financial Services Agency (FSA). Provides access to securities filings
including annual reports (有価証券報告書), quarterly reports, large shareholding
reports, and tender offer filings.

Data Source: https://api.edinet-fsa.go.jp/api/v2
Protocol: REST (JSON metadata, ZIP documents)
Auth: API key (Subscription-Key), free registration
Refresh: Daily (filings published continuously)
Coverage: All Japanese listed companies

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import json
import sys
import os
import time
import hashlib
import zipfile
import io
import csv
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://api.edinet-fsa.go.jp/api/v2"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "edinet_japan"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 3.5

API_KEY = os.environ.get("EDINET_API_KEY", "")

DOC_TYPE_CODES = {
    "120": "Annual Securities Report (有価証券報告書)",
    "130": "Amended Annual Securities Report (訂正有価証券報告書)",
    "140": "Quarterly Securities Report (四半期報告書)",
    "150": "Amended Quarterly Report (訂正四半期報告書)",
    "160": "Semi-Annual Report (半期報告書)",
    "170": "Amended Semi-Annual Report (訂正半期報告書)",
    "030": "Securities Registration Statement (有価証券届出書)",
    "040": "Amended Securities Registration (訂正有価証券届出書)",
    "350": "Large Shareholding Report (大量保有報告書)",
    "360": "Amended Large Shareholding Report (訂正大量保有報告書)",
    "250": "Tender Offer Notification (公開買付届出書)",
    "260": "Amended Tender Offer Notification (訂正公開買付届出書)",
}

INDICATORS = {
    "ANNUAL_REPORTS": {
        "doc_type_code": "120",
        "name": "Annual Securities Reports (有価証券報告書)",
        "description": "Annual financial reports filed by Japanese listed companies (Yuho)",
        "frequency": "annual",
    },
    "QUARTERLY_REPORTS": {
        "doc_type_code": "140",
        "name": "Quarterly Securities Reports (四半期報告書)",
        "description": "Quarterly financial reports from Japanese listed companies",
        "frequency": "quarterly",
    },
    "SEMIANNUAL_REPORTS": {
        "doc_type_code": "160",
        "name": "Semi-Annual Reports (半期報告書)",
        "description": "Semi-annual financial reports from Japanese listed companies",
        "frequency": "semiannual",
    },
    "LARGE_SHAREHOLDING": {
        "doc_type_code": "350",
        "name": "Large Shareholding Reports (大量保有報告書)",
        "description": "Reports on large shareholding positions (5%+ ownership)",
        "frequency": "event-driven",
    },
    "TENDER_OFFERS": {
        "doc_type_code": "250",
        "name": "Tender Offer Notifications (公開買付届出書)",
        "description": "Tender offer / takeover bid filings",
        "frequency": "event-driven",
    },
    "SECURITIES_REGISTRATION": {
        "doc_type_code": "030",
        "name": "Securities Registration Statements (有価証券届出書)",
        "description": "New securities registration filings (IPOs, offerings)",
        "frequency": "event-driven",
    },
    "ALL_FILINGS": {
        "doc_type_code": None,
        "name": "All Filings (全書類)",
        "description": "All document types filed on the specified date",
        "frequency": "daily",
    },
}


def _check_api_key() -> Optional[Dict]:
    if not API_KEY:
        return {
            "success": False,
            "error": "EDINET_API_KEY not set",
            "hint": "Register free at https://disclosure.edinet-fsa.go.jp — then set EDINET_API_KEY in .env",
        }
    return None


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
        path.write_text(json.dumps(data, default=str, ensure_ascii=False))
    except OSError:
        pass


def _api_request(endpoint: str, params: dict) -> Dict:
    """Make authenticated request to EDINET API."""
    key_err = _check_api_key()
    if key_err:
        return key_err

    params["Subscription-Key"] = API_KEY
    url = f"{BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if "json" in content_type or "text" in content_type:
            body = resp.json()
            sc = body.get("statusCode")
            if sc and sc != 200:
                return {"success": False, "error": body.get("message", f"API error (code {sc})")}
            return {"success": True, "data": body}
        return {"success": True, "data": resp.content, "binary": True}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        if status == 400:
            return {"success": False, "error": "Bad request — check date format (YYYY-MM-DD)"}
        if status == 401:
            return {"success": False, "error": "Invalid or expired API key"}
        if status == 404:
            return {"success": False, "error": "Not found (HTTP 404)"}
        if status == 429:
            return {"success": False, "error": "Rate limited — increase delay between requests"}
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _filter_results(results: List[Dict], doc_type_code: Optional[str] = None,
                    company_query: Optional[str] = None) -> List[Dict]:
    filtered = results
    if doc_type_code:
        filtered = [r for r in filtered if r.get("docTypeCode") == doc_type_code]
    if company_query:
        q = company_query.lower()
        filtered = [
            r for r in filtered
            if q in (r.get("filerName") or "").lower()
            or q in (r.get("edinetCode") or "").lower()
            or q in (r.get("secCode") or "").lower()
            or q in (r.get("docDescription") or "").lower()
        ]
    return filtered


def _format_document(doc: Dict) -> Dict:
    dtc = doc.get("docTypeCode", "")
    return {
        "doc_id": doc.get("docID"),
        "edinet_code": doc.get("edinetCode"),
        "sec_code": doc.get("secCode"),
        "filer_name": doc.get("filerName"),
        "doc_description": doc.get("docDescription"),
        "doc_type_code": dtc,
        "doc_type_name": DOC_TYPE_CODES.get(dtc, f"Type {dtc}"),
        "submit_date": doc.get("submitDateTime"),
        "period_start": doc.get("periodStart"),
        "period_end": doc.get("periodEnd"),
        "has_xbrl": doc.get("xbrlFlag") == "1",
        "has_pdf": doc.get("pdfFlag") == "1",
        "has_csv": doc.get("csvFlag") == "1",
        "has_english": doc.get("englishFlag") == "1",
    }


def _fetch_date_range(start_date: str, end_date: str, doc_type_code: Optional[str] = None,
                      company_query: Optional[str] = None, max_days: int = 30) -> tuple:
    """Fetch and filter documents across a date range. Returns (docs, error_or_None)."""
    all_docs = []
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    days_fetched = 0

    while current <= end and days_fetched < max_days:
        date_str = current.strftime("%Y-%m-%d")
        result = _api_request("documents.json", {"date": date_str, "type": 2})

        if not result.get("success"):
            if not all_docs:
                return [], result.get("error", "API request failed")
            break

        data = result["data"]
        if isinstance(data, dict):
            meta = data.get("metadata", {})
            if meta.get("status") != "200":
                msg = meta.get("message", "Unknown error")
                if not all_docs:
                    return [], f"EDINET API error: {msg}"
                break

            results = data.get("results") or []
            filtered = _filter_results(results, doc_type_code, company_query)
            all_docs.extend([_format_document(d) for d in filtered])

        current += timedelta(days=1)
        days_fetched += 1
        if current <= end:
            time.sleep(REQUEST_DELAY)

    return all_docs, None


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch filings for a given indicator (document category) and date range."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }

    cfg = INDICATORS[indicator]
    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")
    if not end_date:
        end_date = start_date

    cache_params = {"indicator": indicator, "start": start_date, "end": end_date}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    all_docs, err = _fetch_date_range(start_date, end_date, cfg["doc_type_code"])

    if err and not all_docs:
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": err,
        }

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "filings": all_docs[:100],
        "count": len(all_docs),
        "date_range": {"start": start_date, "end": end_date},
        "source": BASE_URL,
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
            "doc_type_code": v["doc_type_code"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest filings for one or all indicator categories."""
    today = datetime.now().strftime("%Y-%m-%d")

    if indicator:
        return fetch_data(indicator, start_date=today)

    results = {}
    errors = []
    for key in INDICATORS:
        data = fetch_data(key, start_date=today)
        if data.get("success"):
            results[key] = {
                "name": data["name"],
                "count": data["count"],
                "date": today,
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "EDINET Japan (FSA)",
        "indicators": results,
        "errors": errors if errors else None,
        "date": today,
        "timestamp": datetime.now().isoformat(),
    }


def search_company(query: str, date: str = None, days_back: int = 7) -> Dict:
    """Search recent filings by company name, EDINET code, or securities code."""
    key_err = _check_api_key()
    if key_err:
        return key_err

    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    cache_params = {"search": query, "date": date, "days": days_back}
    cp = _cache_path("search", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    end_dt = datetime.strptime(date, "%Y-%m-%d")
    start_dt = end_dt - timedelta(days=days_back - 1)
    start_str = start_dt.strftime("%Y-%m-%d")

    matches, err = _fetch_date_range(start_str, date, company_query=query, max_days=days_back)

    if err and not matches:
        return {"success": False, "query": query, "error": err}

    response = {
        "success": True,
        "query": query,
        "filings": matches[:50],
        "count": len(matches),
        "search_range_days": days_back,
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def download_document(doc_id: str, doc_type: int = 5) -> Dict:
    """
    Download a document by ID.
    doc_type: 1=XBRL ZIP, 2=PDF, 3=Attachments, 4=English, 5=CSV (XBRL→CSV)
    """
    key_err = _check_api_key()
    if key_err:
        return key_err

    cache_params = {"doc_id": doc_id, "type": doc_type}
    cp = _cache_path(f"doc_{doc_id}", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(f"documents/{doc_id}", {"type": doc_type})
    if not result.get("success"):
        return {"success": False, "doc_id": doc_id, "error": result.get("error", "Download failed")}

    content = result.get("data")
    if not result.get("binary") or not isinstance(content, bytes):
        return {"success": False, "doc_id": doc_id, "error": "Unexpected response format (expected ZIP)"}

    save_dir = CACHE_DIR / "documents" / doc_id
    save_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            zf.extractall(save_dir)
            file_list = zf.namelist()
    except zipfile.BadZipFile:
        return {"success": False, "doc_id": doc_id, "error": "Downloaded file is not a valid ZIP"}

    parsed_data = []
    if doc_type == 5:
        csv_dir = save_dir / "XBRL_TO_CSV"
        if csv_dir.exists():
            for csv_file in sorted(csv_dir.glob("*.csv")):
                try:
                    text = csv_file.read_text(encoding="utf-16")
                    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
                    rows = [dict(row) for row in reader]
                    parsed_data.append({
                        "file": csv_file.name,
                        "rows": len(rows),
                        "sample": rows[:10],
                    })
                except Exception:
                    parsed_data.append({"file": csv_file.name, "error": "Failed to parse"})

    response = {
        "success": True,
        "doc_id": doc_id,
        "doc_type": doc_type,
        "files": file_list[:50],
        "file_count": len(file_list),
        "save_path": str(save_dir),
        "csv_data": parsed_data if parsed_data else None,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


# --- CLI ---

def _print_help():
    print("""
EDINET Japan Securities Filings Module

Usage:
  python edinet_japan.py                               # Today's filings (all types)
  python edinet_japan.py <INDICATOR>                    # Fetch indicator for today
  python edinet_japan.py <INDICATOR> <DATE>             # Filings for date (YYYY-MM-DD)
  python edinet_japan.py <INDICATOR> <START> <END>      # Date range query
  python edinet_japan.py list                           # List available indicators
  python edinet_japan.py search <COMPANY>               # Search by company name/code
  python edinet_japan.py download <DOC_ID> [TYPE]       # Download document (type 1-5)

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print(f"""
Document download types:
  1 = XBRL (ZIP)   2 = PDF   3 = Attachments   4 = English   5 = CSV

Source: {BASE_URL}
Auth: Subscription-Key (set EDINET_API_KEY in .env)
Coverage: All Japanese securities filings
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str, ensure_ascii=False))
        elif cmd == "search":
            if len(sys.argv) < 3:
                print("Usage: python edinet_japan.py search <COMPANY_NAME>")
                sys.exit(1)
            query = " ".join(sys.argv[2:])
            result = search_company(query)
            print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
        elif cmd == "download":
            if len(sys.argv) < 3:
                print("Usage: python edinet_japan.py download <DOC_ID> [TYPE]")
                sys.exit(1)
            doc_id = sys.argv[2]
            dtype = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            result = download_document(doc_id, dtype)
            print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
        else:
            indicator = cmd.upper()
            start = sys.argv[2] if len(sys.argv) > 2 else None
            end = sys.argv[3] if len(sys.argv) > 3 else None
            result = fetch_data(indicator, start_date=start, end_date=end)
            print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str, ensure_ascii=False))

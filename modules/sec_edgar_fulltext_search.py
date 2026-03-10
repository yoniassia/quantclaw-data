"""
SEC EDGAR Full-Text Search — Search across all SEC filings by keyword

Data Source: SEC EDGAR EFTS (Electronic Full-Text Search)
Endpoint: https://efts.sec.gov/LATEST/search-index
Update: Real-time (new filings indexed within minutes)
Free: Yes — no API key, no registration (10 req/sec limit)
User-Agent: Required per SEC fair access policy

Provides:
- Full-text search across all SEC filings (10-K, 10-Q, 8-K, etc.)
- Filter by form type, date range, CIK, SIC code, state
- Company name, CIK, accession number, filing date
- Aggregations by form type, entity, SIC, state
- Direct links to filing documents on EDGAR

Usage:
    from modules.sec_edgar_fulltext_search import *
    
    # Search for "material weakness" in 10-K filings
    results = search_filings("material weakness", forms=["10-K"])
    
    # Search a specific company's filings
    results = search_company_filings("AAPL", "risk factors")
    
    # Get recent 8-K filings mentioning "acquisition"
    results = search_filings("acquisition", forms=["8-K"], days_back=30)
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import time
import os

# --- Config ---
BASE_URL = "https://efts.sec.gov/LATEST/search-index"
SUBMISSIONS_URL = "https://data.sec.gov/submissions"
USER_AGENT = "QuantClaw/1.0 quant@moneyclaw.com"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}
CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/sec_efts")
os.makedirs(CACHE_DIR, exist_ok=True)

# Rate limiting
_last_request_time = 0
_MIN_INTERVAL = 0.12  # ~8 req/sec to stay under 10/sec limit


def _rate_limit():
    """Enforce rate limiting per SEC fair access policy."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request_time = time.time()


def _build_query(
    query: str,
    forms: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    ciks: Optional[List[str]] = None,
    sics: Optional[List[str]] = None,
    states: Optional[List[str]] = None,
    exact_phrase: bool = True,
) -> dict:
    """Build Elasticsearch query body for EFTS search."""
    must = []
    filters = []

    # Text query
    if exact_phrase:
        must.append({"match_phrase": {"doc_text": query}})
    else:
        must.append({"match": {"doc_text": query}})

    # Date range filter
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["gte"] = start_date
        if end_date:
            date_filter["lte"] = end_date
        filters.append({"range": {"file_date": date_filter}})

    # Form type filter
    if forms:
        filters.append({"terms": {"root_forms": forms}})

    # CIK filter
    if ciks:
        filters.append({"terms": {"ciks": ciks}})

    # SIC filter
    if sics:
        filters.append({"terms": {"sics": sics}})

    # State filter
    if states:
        filters.append({"terms": {"biz_states": states}})

    return {
        "bool": {
            "must": must,
            "filter": filters,
            "must_not": [],
            "should": [],
        }
    }


def search_filings(
    query: str,
    forms: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    days_back: Optional[int] = None,
    ciks: Optional[List[str]] = None,
    sics: Optional[List[str]] = None,
    states: Optional[List[str]] = None,
    exact_phrase: bool = True,
    size: int = 20,
    offset: int = 0,
    include_aggregations: bool = True,
) -> Dict:
    """
    Search SEC EDGAR filings by keyword with optional filters.

    Args:
        query: Search term (e.g. "material weakness", "risk factors")
        forms: Filter by form types (e.g. ["10-K", "10-Q", "8-K"])
        start_date: Start date YYYY-MM-DD
        end_date: End date YYYY-MM-DD
        days_back: Alternative to start/end — search last N days
        ciks: Filter by CIK numbers (zero-padded 10-digit strings)
        sics: Filter by SIC codes
        states: Filter by business states (2-letter codes)
        exact_phrase: If True, search exact phrase; if False, match any words
        size: Number of results (max 100)
        offset: Pagination offset
        include_aggregations: Include facet counts by form, entity, SIC, state

    Returns:
        Dict with keys: total, hits (list of filing dicts), aggregations, query_info
    """
    if days_back and not start_date:
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    es_query = _build_query(
        query, forms, start_date, end_date, ciks, sics, states, exact_phrase
    )

    body = {
        "_source": {"exclude": ["doc_text"]},
        "query": es_query,
        "from": offset,
        "size": min(size, 100),
    }

    if include_aggregations:
        body["aggregations"] = {
            "form_filter": {"terms": {"field": "root_forms", "size": 20}},
            "entity_filter": {"terms": {"field": "display_names.raw", "size": 20}},
            "sic_filter": {"terms": {"field": "sics", "size": 20}},
            "biz_states_filter": {"terms": {"field": "biz_states", "size": 20}},
        }

    _rate_limit()
    try:
        params = {"q": f'"{query}"' if exact_phrase else query}
        if forms:
            params["forms"] = ",".join(forms)
        if start_date or end_date:
            params["dateRange"] = "custom"
            if start_date:
                params["startdt"] = start_date
            if end_date:
                params["enddt"] = end_date
        if ciks:
            params["ciks"] = ",".join(ciks)
        if sics:
            params["sics"] = ",".join(sics)
        if states:
            params["biz_states"] = ",".join(states)
        params["from"] = offset
        params["size"] = min(size, 100)

        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "total": 0, "hits": [], "aggregations": {}}

    # Parse results
    hits = []
    for hit in data.get("hits", {}).get("hits", []):
        src = hit.get("_source", {})
        filing = {
            "id": hit.get("_id", ""),
            "score": hit.get("_score", 0),
            "accession_number": src.get("adsh", ""),
            "form_type": src.get("form", ""),
            "file_date": src.get("file_date", ""),
            "period_ending": src.get("period_ending"),
            "companies": [],
            "file_type": src.get("file_type", ""),
            "file_description": src.get("file_description", ""),
            "items": src.get("items", []),
            "sic_codes": src.get("sics", []),
            "business_locations": src.get("biz_locations", []),
            "filing_url": _build_filing_url(src.get("adsh", "")),
        }
        # Parse company info from parallel arrays
        cik_list = src.get("ciks", [])
        name_list = src.get("display_names", [])
        for i in range(len(cik_list)):
            company = {"cik": cik_list[i]}
            if i < len(name_list):
                company["name"] = name_list[i]
            filing["companies"].append(company)

        hits.append(filing)

    # Parse aggregations
    aggs = {}
    raw_aggs = data.get("aggregations", {})
    for key in ["form_filter", "entity_filter", "sic_filter", "biz_states_filter"]:
        if key in raw_aggs:
            aggs[key] = [
                {"value": b["key"], "count": b["doc_count"]}
                for b in raw_aggs[key].get("buckets", [])
            ]

    total_info = data.get("hits", {}).get("total", {})
    total = total_info.get("value", 0) if isinstance(total_info, dict) else total_info

    return {
        "total": total,
        "total_relation": total_info.get("relation", "eq") if isinstance(total_info, dict) else "eq",
        "hits": hits,
        "aggregations": aggs,
        "query_info": {
            "query": query,
            "forms": forms,
            "date_range": f"{start_date} to {end_date}",
            "exact_phrase": exact_phrase,
            "offset": offset,
            "size": size,
        },
    }


def search_company_filings(
    ticker_or_cik: str,
    query: str,
    forms: Optional[List[str]] = None,
    days_back: int = 365,
    size: int = 20,
) -> Dict:
    """
    Search filings for a specific company by ticker or CIK.

    Args:
        ticker_or_cik: Ticker symbol (e.g. "AAPL") or CIK number
        query: Search term within that company's filings
        forms: Optional form type filter
        days_back: How far back to search (default 365 days)
        size: Number of results

    Returns:
        Dict with total, hits, aggregations
    """
    cik = _resolve_cik(ticker_or_cik)
    if not cik:
        return {"error": f"Could not resolve CIK for '{ticker_or_cik}'", "total": 0, "hits": []}

    return search_filings(
        query=query,
        forms=forms,
        days_back=days_back,
        ciks=[cik],
        size=size,
    )


def count_filings(
    query: str,
    forms: Optional[List[str]] = None,
    days_back: int = 90,
) -> Dict:
    """
    Get count of filings matching a search term, broken down by form type.

    Args:
        query: Search term
        forms: Optional form type filter
        days_back: How far back to search

    Returns:
        Dict with total count and breakdown by form type
    """
    result = search_filings(
        query=query,
        forms=forms,
        days_back=days_back,
        size=0,
        include_aggregations=True,
    )
    return {
        "query": query,
        "total": result.get("total", 0),
        "by_form": result.get("aggregations", {}).get("form_filter", []),
        "by_state": result.get("aggregations", {}).get("biz_states_filter", []),
        "date_range": result.get("query_info", {}).get("date_range", ""),
    }


def get_filing_document_url(accession_number: str, filename: Optional[str] = None) -> str:
    """
    Build URL to access a filing document on EDGAR.

    Args:
        accession_number: e.g. "0001193125-26-039477"
        filename: Optional specific file within the filing

    Returns:
        URL string to the filing on EDGAR
    """
    clean = accession_number.replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{clean[:10]}/{accession_number}"
    if filename:
        return f"{base}/{filename}"
    return f"{base}/"


def search_risk_factors(
    ticker_or_cik: Optional[str] = None,
    days_back: int = 365,
    size: int = 10,
) -> Dict:
    """
    Search for "risk factors" disclosures in 10-K and 10-Q filings.

    Args:
        ticker_or_cik: Optional company filter
        days_back: How far back to search
        size: Number of results

    Returns:
        Dict with matching filings containing risk factor discussions
    """
    if ticker_or_cik:
        return search_company_filings(
            ticker_or_cik, "risk factors", forms=["10-K", "10-Q"], days_back=days_back, size=size
        )
    return search_filings(
        "risk factors", forms=["10-K", "10-Q"], days_back=days_back, size=size
    )


def search_material_weakness(days_back: int = 180, size: int = 20) -> Dict:
    """
    Find filings mentioning "material weakness" — key audit red flag.

    Args:
        days_back: How far back to search
        size: Number of results

    Returns:
        Dict with filings mentioning material weakness
    """
    return search_filings(
        "material weakness",
        forms=["10-K", "10-K/A", "8-K"],
        days_back=days_back,
        size=size,
    )


def search_acquisition_announcements(days_back: int = 90, size: int = 20) -> Dict:
    """
    Find 8-K filings mentioning acquisitions or mergers.

    Args:
        days_back: How far back to search
        size: Number of results

    Returns:
        Dict with 8-K filings about acquisitions
    """
    return search_filings(
        "acquisition agreement",
        forms=["8-K"],
        days_back=days_back,
        size=size,
    )


def search_insider_trading_mentions(
    ticker_or_cik: Optional[str] = None, days_back: int = 180, size: int = 20
) -> Dict:
    """
    Search for filings mentioning insider stock transactions.

    Args:
        ticker_or_cik: Optional company filter
        days_back: How far back to search
        size: Number of results

    Returns:
        Dict with matching filings
    """
    if ticker_or_cik:
        return search_company_filings(
            ticker_or_cik, "insider trading policy", days_back=days_back, size=size
        )
    return search_filings("insider trading policy", days_back=days_back, size=size)


def _resolve_cik(ticker_or_cik: str) -> Optional[str]:
    """Resolve a ticker symbol to a zero-padded CIK number."""
    # If already a CIK (numeric), zero-pad it
    if ticker_or_cik.isdigit():
        return ticker_or_cik.zfill(10)

    # Try SEC company tickers endpoint
    cache_file = os.path.join(CACHE_DIR, "company_tickers.json")
    tickers_data = None

    # Use cache if fresh (< 24h)
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400:
            try:
                with open(cache_file) as f:
                    tickers_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

    if not tickers_data:
        try:
            _rate_limit()
            resp = requests.get(
                "https://www.sec.gov/files/company_tickers.json",
                headers=HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            tickers_data = resp.json()
            with open(cache_file, "w") as f:
                json.dump(tickers_data, f)
        except Exception:
            return None

    ticker_upper = ticker_or_cik.upper()
    for entry in tickers_data.values():
        if entry.get("ticker", "").upper() == ticker_upper:
            return str(entry["cik_str"]).zfill(10)

    return None


def _build_filing_url(accession_number: str) -> str:
    """Build EDGAR filing URL from accession number."""
    if not accession_number:
        return ""
    clean = accession_number.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{clean}/{accession_number}-index.htm"


# --- Module info ---
def get_module_info() -> Dict:
    """Return module metadata."""
    return {
        "module": "sec_edgar_fulltext_search",
        "source": "https://efts.sec.gov/LATEST/search-index",
        "category": "Earnings & Fundamentals",
        "requires_api_key": False,
        "rate_limit": "10 req/sec",
        "update_frequency": "real-time",
        "functions": [
            "search_filings",
            "search_company_filings",
            "count_filings",
            "get_filing_document_url",
            "search_risk_factors",
            "search_material_weakness",
            "search_acquisition_announcements",
            "search_insider_trading_mentions",
            "get_module_info",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(get_module_info(), indent=2))

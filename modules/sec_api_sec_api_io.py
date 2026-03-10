#!/usr/bin/env python3
"""
SEC API (sec-api.io) — SEC EDGAR Filings & Company Data

Search, filter and retrieve SEC EDGAR filings, company info, CIK/ticker mappings,
and XBRL financial data. Uses SEC's free EDGAR APIs (data.sec.gov, efts.sec.gov)
as primary data source — no API key required. Optionally uses sec-api.io enhanced
endpoints if SEC_API_IO_KEY is set in environment.

Source: https://sec-api.io/docs + https://data.sec.gov
Category: SEC Filings & Regulatory
Free tier: True - SEC EDGAR APIs are fully free (10 req/sec with User-Agent)
Update frequency: Real-time (new filings indexed within seconds)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# ─── Configuration ───────────────────────────────────────────────────────────

SEC_EDGAR_BASE = "https://data.sec.gov"
EFTS_BASE = "https://efts.sec.gov/LATEST"
SEC_API_IO_BASE = "https://api.sec-api.io"

# sec-api.io API key (optional — enhances search if set)
SEC_API_IO_KEY = os.environ.get("SEC_API_IO_KEY", "")

# SEC EDGAR requires a descriptive User-Agent (fair-use policy)
HEADERS = {
    "User-Agent": "QuantClaw/1.0 dataclaw@moneyclaw.com",
    "Accept": "application/json",
}

# ─── Helpers ─────────────────────────────────────────────────────────────────


def _pad_cik(cik: str) -> str:
    """Pad CIK to 10 digits with leading zeros."""
    return str(cik).lstrip("0").zfill(10)


def _edgar_get(path: str, params: Optional[Dict] = None, timeout: int = 15) -> Dict:
    """GET request to SEC EDGAR data.sec.gov with proper headers."""
    url = f"{SEC_EDGAR_BASE}{path}"
    resp = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _efts_search(params: Dict, timeout: int = 15) -> Dict:
    """Search EDGAR Full-Text Search System (EFTS)."""
    url = f"{EFTS_BASE}/search-index"
    resp = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


# ─── Company Information ─────────────────────────────────────────────────────


def get_company_info(cik: str) -> Dict:
    """Get company details by CIK number.

    Returns entity name, type, SIC code, tickers, exchanges, addresses,
    and metadata from SEC EDGAR submissions endpoint.

    Args:
        cik: Central Index Key (e.g. '320193' for Apple, '789019' for Microsoft)

    Returns:
        Dict with company information including name, tickers, SIC, addresses.

    Example:
        >>> info = get_company_info('320193')
        >>> info['name']
        'Apple Inc.'
    """
    try:
        padded = _pad_cik(cik)
        data = _edgar_get(f"/submissions/CIK{padded}.json")
        return {
            "cik": data.get("cik", ""),
            "name": data.get("name", ""),
            "entity_type": data.get("entityType", ""),
            "sic": data.get("sic", ""),
            "sic_description": data.get("sicDescription", ""),
            "tickers": data.get("tickers", []),
            "exchanges": data.get("exchanges", []),
            "ein": data.get("ein", ""),
            "category": data.get("category", ""),
            "fiscal_year_end": data.get("fiscalYearEnd", ""),
            "state_of_incorporation": data.get("stateOfIncorporation", ""),
            "phone": data.get("phone", ""),
            "website": data.get("website", ""),
            "addresses": {
                "business": data.get("addresses", {}).get("business", {}),
                "mailing": data.get("addresses", {}).get("mailing", {}),
            },
            "source": "sec_edgar",
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "cik": cik}


def resolve_ticker_to_cik(ticker: str) -> Dict:
    """Resolve a stock ticker symbol to its CIK number using SEC's company tickers file.

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL', 'MSFT', 'TSLA')

    Returns:
        Dict with cik, name, ticker, and exchange if found.

    Example:
        >>> result = resolve_ticker_to_cik('AAPL')
        >>> result['cik']
        '320193'
    """
    try:
        url = f"{SEC_EDGAR_BASE}/submissions/CIK-lookup-data.txt"
        # Use the company tickers JSON which is more reliable
        resp = requests.get(
            f"https://www.sec.gov/files/company_tickers.json",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        ticker_upper = ticker.upper().strip()
        for entry in data.values():
            if entry.get("ticker", "").upper() == ticker_upper:
                return {
                    "cik": str(entry.get("cik_str", "")),
                    "name": entry.get("title", ""),
                    "ticker": entry.get("ticker", ""),
                    "found": True,
                    "source": "sec_company_tickers",
                }

        return {
            "ticker": ticker,
            "found": False,
            "message": f"Ticker '{ticker}' not found in SEC company tickers",
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "ticker": ticker}


# ─── Filing Search & Retrieval ───────────────────────────────────────────────


def get_recent_filings(
    cik: str,
    form_type: Optional[str] = None,
    limit: int = 20,
) -> List[Dict]:
    """Get recent SEC filings for a company by CIK.

    Retrieves filing metadata from SEC EDGAR submissions endpoint including
    form type, filing date, accession number, and document URLs.

    Args:
        cik: Central Index Key (e.g. '320193' for Apple)
        form_type: Filter by form type (e.g. '10-K', '10-Q', '8-K'). None = all.
        limit: Maximum number of filings to return (default 20)

    Returns:
        List of dicts with filing metadata.

    Example:
        >>> filings = get_recent_filings('320193', form_type='10-K', limit=5)
        >>> filings[0]['form_type']
        '10-K'
    """
    try:
        padded = _pad_cik(cik)
        data = _edgar_get(f"/submissions/CIK{padded}.json")
        recent = data.get("filings", {}).get("recent", {})

        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])
        descriptions = recent.get("primaryDocDescription", [])
        periods = recent.get("reportDate", [])

        results = []
        for i in range(len(forms)):
            if form_type and forms[i] != form_type:
                continue

            accession_clean = accessions[i].replace("-", "")
            filing_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{cik.lstrip('0')}/{accession_clean}/{primary_docs[i]}"
            )

            results.append({
                "form_type": forms[i],
                "filing_date": dates[i] if i < len(dates) else "",
                "accession_number": accessions[i],
                "primary_document": primary_docs[i] if i < len(primary_docs) else "",
                "description": descriptions[i] if i < len(descriptions) else "",
                "report_date": periods[i] if i < len(periods) else "",
                "filing_url": filing_url,
                "index_url": (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{cik.lstrip('0')}/{accession_clean}/"
                ),
            })

            if len(results) >= limit:
                break

        return results
    except requests.exceptions.RequestException as e:
        return [{"error": str(e), "cik": cik}]


def search_filings(
    query: str,
    form_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10,
) -> Dict:
    """Full-text search across SEC EDGAR filings using EFTS.

    Searches filing content and metadata. Supports keyword and phrase queries.

    Args:
        query: Search query (e.g. 'artificial intelligence', 'AAPL', '"risk factors"')
        form_type: Filter by form type (e.g. '10-K', '8-K'). Comma-separated for multiple.
        start_date: Start date filter (YYYY-MM-DD)
        end_date: End date filter (YYYY-MM-DD)
        limit: Max results (default 10, max 100)

    Returns:
        Dict with total count and list of matching filings.

    Example:
        >>> results = search_filings('artificial intelligence', form_type='10-K', limit=5)
        >>> results['total']
        10000
    """
    try:
        params = {
            "q": query,
            "from": 0,
            "size": min(limit, 100),
        }
        if form_type:
            params["forms"] = form_type
        if start_date and end_date:
            params["dateRange"] = "custom"
            params["startdt"] = start_date
            params["enddt"] = end_date

        data = _efts_search(params)
        hits = data.get("hits", {})
        total_info = hits.get("total", {})
        total = total_info.get("value", 0) if isinstance(total_info, dict) else total_info

        results = []
        for hit in hits.get("hits", []):
            src = hit.get("_source", {})
            display_names = src.get("display_names", [])
            ciks = src.get("ciks", [])
            accession = src.get("adsh", "")

            results.append({
                "entity": display_names[0] if display_names else "",
                "cik": ciks[0] if ciks else "",
                "form_type": src.get("form", ""),
                "file_date": src.get("file_date", ""),
                "period_ending": src.get("period_ending", ""),
                "accession_number": accession,
                "file_type": src.get("file_type", ""),
                "file_description": src.get("file_description", ""),
                "sic": src.get("sics", [""])[0] if src.get("sics") else "",
                "location": src.get("biz_locations", [""])[0] if src.get("biz_locations") else "",
            })

        return {
            "query": query,
            "total": total,
            "returned": len(results),
            "filings": results,
            "source": "sec_efts",
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "query": query}


# ─── XBRL Financial Data ────────────────────────────────────────────────────


def get_company_facts(cik: str) -> Dict:
    """Get all XBRL financial facts for a company (income, balance sheet, cash flow).

    Returns structured financial data from all SEC filings with XBRL tags.
    Covers US-GAAP and IFRS taxonomies.

    Args:
        cik: Central Index Key (e.g. '320193' for Apple)

    Returns:
        Dict with taxonomy -> concept -> units -> time series data.

    Example:
        >>> facts = get_company_facts('320193')
        >>> list(facts['facts'].keys())
        ['dei', 'us-gaap']
    """
    try:
        padded = _pad_cik(cik)
        data = _edgar_get(f"/api/xbrl/companyfacts/CIK{padded}.json")
        return {
            "cik": data.get("cik", ""),
            "entity_name": data.get("entityName", ""),
            "facts": {
                taxonomy: {
                    concept: {
                        "label": details.get("label", ""),
                        "description": details.get("description", ""),
                        "units": {
                            unit: len(values)
                            for unit, values in details.get("units", {}).items()
                        },
                    }
                    for concept, details in concepts.items()
                }
                for taxonomy, concepts in data.get("facts", {}).items()
            },
            "source": "sec_xbrl",
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "cik": cik}


def get_financial_metric(
    cik: str,
    concept: str,
    taxonomy: str = "us-gaap",
    unit: str = "USD",
    limit: int = 20,
) -> List[Dict]:
    """Get time series of a specific XBRL financial metric for a company.

    Retrieves historical values for concepts like Revenue, NetIncomeLoss,
    Assets, etc. from SEC XBRL filings.

    Args:
        cik: Central Index Key (e.g. '320193' for Apple)
        concept: XBRL concept name (e.g. 'Revenues', 'NetIncomeLoss', 'Assets')
        taxonomy: XBRL taxonomy ('us-gaap', 'ifrs-full', 'dei')
        unit: Unit of measurement ('USD', 'shares', 'USD/shares', 'pure')
        limit: Max data points to return (default 20, most recent first)

    Returns:
        List of dicts with value, period, form type, filing date.

    Example:
        >>> revenue = get_financial_metric('320193', 'Revenues', limit=8)
        >>> revenue[0]['val']
        391035000000
    """
    try:
        padded = _pad_cik(cik)
        data = _edgar_get(f"/api/xbrl/companyfacts/CIK{padded}.json")

        facts = data.get("facts", {}).get(taxonomy, {}).get(concept, {})
        if not facts:
            return [{"error": f"Concept '{taxonomy}:{concept}' not found for CIK {cik}"}]

        unit_data = facts.get("units", {}).get(unit, [])
        if not unit_data:
            available_units = list(facts.get("units", {}).keys())
            return [{"error": f"Unit '{unit}' not found. Available: {available_units}"}]

        # Sort by end date descending, take most recent
        sorted_data = sorted(unit_data, key=lambda x: x.get("end", ""), reverse=True)

        results = []
        for entry in sorted_data[:limit]:
            results.append({
                "val": entry.get("val"),
                "start": entry.get("start", ""),
                "end": entry.get("end", ""),
                "filed": entry.get("filed", ""),
                "form": entry.get("form", ""),
                "accession": entry.get("accn", ""),
                "fiscal_year": entry.get("fy", ""),
                "fiscal_period": entry.get("fp", ""),
                "frame": entry.get("frame", ""),
            })

        return results
    except requests.exceptions.RequestException as e:
        return [{"error": str(e), "cik": cik}]


# ─── Bulk / Aggregate Endpoints ──────────────────────────────────────────────


def get_company_concept(
    cik: str,
    concept: str,
    taxonomy: str = "us-gaap",
) -> Dict:
    """Get all filings of a specific concept for one company.

    More focused than get_company_facts — returns full time series
    for a single concept with all units and data points.

    Args:
        cik: Central Index Key
        concept: XBRL concept (e.g. 'AccountsPayableCurrent')
        taxonomy: 'us-gaap', 'ifrs-full', or 'dei'

    Returns:
        Dict with entity name, concept info, and all data points by unit.
    """
    try:
        padded = _pad_cik(cik)
        data = _edgar_get(
            f"/api/xbrl/companyconcept/CIK{padded}/{taxonomy}/{concept}.json"
        )
        return {
            "cik": data.get("cik", ""),
            "entity_name": data.get("entityName", ""),
            "taxonomy": data.get("taxonomy", ""),
            "tag": data.get("tag", ""),
            "label": data.get("label", ""),
            "description": data.get("description", ""),
            "units": {
                unit: [
                    {
                        "val": entry.get("val"),
                        "end": entry.get("end", ""),
                        "start": entry.get("start", ""),
                        "filed": entry.get("filed", ""),
                        "form": entry.get("form", ""),
                    }
                    for entry in entries
                ]
                for unit, entries in data.get("units", {}).items()
            },
            "source": "sec_xbrl_concept",
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "cik": cik, "concept": concept}


def get_frames(
    taxonomy: str = "us-gaap",
    concept: str = "Revenues",
    unit: str = "USD",
    frame: str = "CY2024Q3I",
) -> Dict:
    """Get a specific XBRL frame — all company values for a concept in a period.

    Useful for cross-sectional analysis (e.g. revenue of all companies in Q3 2024).

    Args:
        taxonomy: 'us-gaap', 'ifrs-full', or 'dei'
        concept: XBRL concept (e.g. 'Revenues', 'Assets', 'NetIncomeLoss')
        unit: Unit ('USD', 'shares', 'pure')
        frame: Period frame (e.g. 'CY2024Q3I' for Q3 2024 instant,
               'CY2024Q3' for Q3 2024 duration)

    Returns:
        Dict with frame metadata and list of all companies' values.

    Example:
        >>> frame = get_frames('us-gaap', 'Revenues', 'USD', 'CY2024Q3I')
        >>> len(frame['data'])  # number of companies reporting
        4500
    """
    try:
        data = _edgar_get(
            f"/api/xbrl/frames/{taxonomy}/{concept}/{unit}/{frame}.json"
        )
        return {
            "taxonomy": data.get("taxonomy", ""),
            "tag": data.get("tag", ""),
            "label": data.get("label", ""),
            "description": data.get("description", ""),
            "unit": unit,
            "frame": frame,
            "total_companies": len(data.get("data", [])),
            "data": [
                {
                    "cik": entry.get("cik"),
                    "entity_name": entry.get("entityName", ""),
                    "val": entry.get("val"),
                    "accession": entry.get("accn", ""),
                    "filed": entry.get("filed", ""),
                }
                for entry in data.get("data", [])[:100]  # cap at 100 for sanity
            ],
            "source": "sec_xbrl_frames",
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "frame": frame, "concept": concept}


# ─── Enhanced sec-api.io Endpoints (requires API key) ────────────────────────


def secapi_query_filings(
    query: Dict,
    sort: Optional[List] = None,
    start: int = 0,
    size: int = 10,
) -> Dict:
    """Search SEC filings via sec-api.io Query API (requires SEC_API_IO_KEY).

    Supports complex Elasticsearch-style queries with 20+ search parameters.
    Falls back to EFTS search if no API key is set.

    Args:
        query: Elasticsearch query dict. Example:
               {"query": {"query_string": {"query": "formType:\\"10-K\\" AND ticker:AAPL"}},
                "from": "0", "size": "10"}
        sort: Sort criteria (e.g. [{"filedAt": {"order": "desc"}}])
        start: Pagination offset
        size: Results per page (max 50)

    Returns:
        Dict with total count and matched filings.
    """
    if not SEC_API_IO_KEY:
        return {
            "error": "SEC_API_IO_KEY not set. Use search_filings() for free EFTS search.",
            "hint": "Set SEC_API_IO_KEY env var with your sec-api.io API key",
        }

    try:
        payload = {
            "query": query.get("query", query),
            "from": str(start),
            "size": str(min(size, 50)),
        }
        if sort:
            payload["sort"] = sort

        resp = requests.post(
            SEC_API_IO_BASE,
            json=payload,
            headers={
                "Authorization": SEC_API_IO_KEY,
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        filings = data.get("filings", [])
        return {
            "total": data.get("total", {}).get("value", len(filings)),
            "returned": len(filings),
            "filings": filings,
            "source": "sec_api_io",
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def secapi_map_ticker(ticker: str) -> Dict:
    """Map ticker to company details via sec-api.io Mapping API (requires API key).

    Falls back to resolve_ticker_to_cik() if no key is set.

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL')

    Returns:
        Dict with CIK, name, CUSIP, exchange, sector, industry, etc.
    """
    if not SEC_API_IO_KEY:
        return resolve_ticker_to_cik(ticker)

    try:
        resp = requests.get(
            f"{SEC_API_IO_BASE.replace('api.', 'api.')}/mapping/ticker/{ticker}",
            params={"token": SEC_API_IO_KEY},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and data:
            return {**data[0], "source": "sec_api_io_mapping", "found": True}
        return {"ticker": ticker, "found": False, "source": "sec_api_io_mapping"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "ticker": ticker}


# ─── Convenience / High-Level Functions ──────────────────────────────────────


def get_10k_filings(ticker: str, limit: int = 5) -> List[Dict]:
    """Get recent 10-K (annual report) filings for a ticker.

    Convenience function that resolves ticker → CIK → recent 10-K filings.

    Args:
        ticker: Stock ticker (e.g. 'AAPL', 'MSFT', 'TSLA')
        limit: Number of filings to return

    Returns:
        List of 10-K filing metadata dicts.

    Example:
        >>> filings = get_10k_filings('AAPL', limit=3)
        >>> filings[0]['form_type']
        '10-K'
    """
    resolved = resolve_ticker_to_cik(ticker)
    if not resolved.get("found"):
        return [{"error": f"Could not resolve ticker '{ticker}' to CIK", **resolved}]

    cik = resolved["cik"]
    return get_recent_filings(cik, form_type="10-K", limit=limit)


def get_10q_filings(ticker: str, limit: int = 5) -> List[Dict]:
    """Get recent 10-Q (quarterly report) filings for a ticker.

    Args:
        ticker: Stock ticker (e.g. 'AAPL', 'MSFT')
        limit: Number of filings to return

    Returns:
        List of 10-Q filing metadata dicts.
    """
    resolved = resolve_ticker_to_cik(ticker)
    if not resolved.get("found"):
        return [{"error": f"Could not resolve ticker '{ticker}' to CIK", **resolved}]

    cik = resolved["cik"]
    return get_recent_filings(cik, form_type="10-Q", limit=limit)


def get_insider_filings(ticker: str, limit: int = 20) -> List[Dict]:
    """Get recent insider trading filings (Form 4) for a ticker.

    Args:
        ticker: Stock ticker (e.g. 'AAPL')
        limit: Number of filings to return

    Returns:
        List of Form 4 filing metadata dicts.
    """
    resolved = resolve_ticker_to_cik(ticker)
    if not resolved.get("found"):
        return [{"error": f"Could not resolve ticker '{ticker}' to CIK", **resolved}]

    cik = resolved["cik"]
    return get_recent_filings(cik, form_type="4", limit=limit)


def get_revenue_history(ticker: str, limit: int = 12) -> List[Dict]:
    """Get revenue history for a ticker from XBRL data.

    Tries multiple common revenue concept names used in SEC filings.

    Args:
        ticker: Stock ticker (e.g. 'AAPL')
        limit: Number of data points

    Returns:
        List of dicts with revenue values and periods.
    """
    resolved = resolve_ticker_to_cik(ticker)
    if not resolved.get("found"):
        return [{"error": f"Could not resolve ticker '{ticker}'"}]

    cik = resolved["cik"]

    # Try common revenue concepts (companies use different tags)
    for concept in [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "NetRevenues",
    ]:
        result = get_financial_metric(cik, concept, limit=limit)
        if result and not (len(result) == 1 and "error" in result[0]):
            return result

    return [{"error": f"No revenue data found for {ticker} (CIK: {cik})"}]


def get_net_income_history(ticker: str, limit: int = 12) -> List[Dict]:
    """Get net income history for a ticker from XBRL data.

    Args:
        ticker: Stock ticker (e.g. 'AAPL')
        limit: Number of data points

    Returns:
        List of dicts with net income values and periods.
    """
    resolved = resolve_ticker_to_cik(ticker)
    if not resolved.get("found"):
        return [{"error": f"Could not resolve ticker '{ticker}'"}]

    cik = resolved["cik"]

    for concept in ["NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic"]:
        result = get_financial_metric(cik, concept, limit=limit)
        if result and not (len(result) == 1 and "error" in result[0]):
            return result

    return [{"error": f"No net income data found for {ticker}"}]


# ─── Module Metadata ─────────────────────────────────────────────────────────

__all__ = [
    "get_company_info",
    "resolve_ticker_to_cik",
    "get_recent_filings",
    "search_filings",
    "get_company_facts",
    "get_financial_metric",
    "get_company_concept",
    "get_frames",
    "secapi_query_filings",
    "secapi_map_ticker",
    "get_10k_filings",
    "get_10q_filings",
    "get_insider_filings",
    "get_revenue_history",
    "get_net_income_history",
]

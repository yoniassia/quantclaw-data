#!/usr/bin/env python3
"""
SEC-API.io — SEC EDGAR filings search, IPO prospectuses, insider trading, institutional holdings.
Source: https://sec-api.io/docs
Category: IPO & Private Markets

Provides access to 18M+ SEC EDGAR filings via the sec-api.io Query API.
Free tier: 100 queries/day, no payment needed.
Requires API token set via SEC_API_IO_TOKEN env var or passed directly.

Sample: search_filings(form_type="S-1", date_from="2024-01-01", date_to="2024-12-31")
"""

import os
import json
import requests
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# API configuration
BASE_URL = "https://efts.sec.gov/LATEST/search-index"
QUERY_API_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_FULL_TEXT_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"

# sec-api.io endpoint (requires token for full features)
SEC_API_QUERY_URL = "https://api.sec-api.io"

# Free EDGAR EFTS endpoint (no token needed)
EDGAR_EFTS_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_FTS_URL = "https://efts.sec.gov/LATEST/search-index"

# SEC EDGAR free endpoints (no API key needed)
SEC_EDGAR_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_EDGAR_TICKERS = "https://www.sec.gov/files/company_tickers.json"
SEC_EDGAR_FULL_TEXT = "https://efts.sec.gov/LATEST/search-index"

# EDGAR full-text search (completely free, no token)
EDGAR_FT_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"

USER_AGENT = "QuantClaw/1.0 (quant@moneyclaw.com)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}

# Rate limiting
_last_request_time = 0
_MIN_INTERVAL = 0.15  # 150ms between requests


def _rate_limit():
    """Enforce rate limiting between requests."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request_time = time.time()


def _get_token() -> Optional[str]:
    """Get sec-api.io API token from environment."""
    return os.environ.get("SEC_API_IO_TOKEN", os.environ.get("SEC_API_TOKEN"))


def _get_cik(ticker: str) -> Optional[str]:
    """Resolve ticker to 10-digit CIK number using SEC EDGAR."""
    _rate_limit()
    try:
        resp = requests.get(SEC_EDGAR_TICKERS, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        ticker_upper = ticker.upper()
        for entry in data.values():
            if isinstance(entry, dict) and entry.get("ticker") == ticker_upper:
                return str(entry["cik_str"]).zfill(10)
        return None
    except Exception:
        return None


# ─── SEC-API.io Query API (needs token, 100 free/day) ───

def search_filings(
    form_type: str = "S-1",
    date_from: str = None,
    date_to: str = None,
    ticker: str = None,
    company_name: str = None,
    size: int = 10,
    start: int = 0,
    token: str = None
) -> Dict[str, Any]:
    """
    Search SEC filings via sec-api.io Query API.

    Args:
        form_type: Filing type (S-1, 10-K, 10-Q, 8-K, 4, 13F-HR, etc.)
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        ticker: Company ticker symbol
        company_name: Company name to search
        size: Number of results (max 50)
        start: Offset for pagination
        token: API token (or uses SEC_API_IO_TOKEN env var)

    Returns:
        Dict with 'filings' list and 'total' count
    """
    api_token = token or _get_token()
    if not api_token:
        # Fall back to free EDGAR search
        return search_filings_edgar_free(
            form_type=form_type, date_from=date_from, date_to=date_to,
            ticker=ticker, company_name=company_name, size=size
        )

    # Build Lucene query string
    query_parts = []
    if form_type:
        query_parts.append(f'formType:"{form_type}"')
    if date_from or date_to:
        df = date_from or "1993-01-01"
        dt = date_to or datetime.now().strftime("%Y-%m-%d")
        query_parts.append(f"filedAt:{{{df} TO {dt}}}")
    if ticker:
        query_parts.append(f'ticker:"{ticker.upper()}"')
    if company_name:
        query_parts.append(f'companyName:"{company_name}"')

    query_string = " AND ".join(query_parts) if query_parts else "*"

    payload = {
        "query": {"query_string": {"query": query_string}},
        "from": str(start),
        "size": str(min(size, 50)),
        "sort": [{"filedAt": {"order": "desc"}}]
    }

    _rate_limit()
    try:
        resp = requests.post(
            f"{SEC_API_QUERY_URL}?token={api_token}",
            json=payload,
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()

        total = data.get("total", {}).get("value", 0)
        filings = data.get("filings", [])

        results = []
        for f in filings:
            results.append({
                "companyName": f.get("companyName", ""),
                "ticker": f.get("ticker", ""),
                "cik": f.get("cik", ""),
                "formType": f.get("formType", ""),
                "filedAt": f.get("filedAt", ""),
                "periodOfReport": f.get("periodOfReport", ""),
                "description": f.get("description", ""),
                "linkToFiling": f.get("linkToFiling", ""),
                "linkToFilingDetails": f.get("linkToFilingDetails", ""),
            })

        return {"total": total, "filings": results, "source": "sec-api.io"}

    except requests.exceptions.HTTPError as e:
        if e.response and e.response.status_code == 403:
            return search_filings_edgar_free(
                form_type=form_type, date_from=date_from, date_to=date_to,
                ticker=ticker, company_name=company_name, size=size
            )
        return {"error": str(e), "filings": [], "total": 0}
    except Exception as e:
        return {"error": str(e), "filings": [], "total": 0}


# ─── Free EDGAR Endpoints (no API key needed) ───

def search_filings_edgar_free(
    form_type: str = "S-1",
    date_from: str = None,
    date_to: str = None,
    ticker: str = None,
    company_name: str = None,
    size: int = 10
) -> Dict[str, Any]:
    """
    Search SEC filings using free EDGAR full-text search (EFTS).
    No API key required. Covers recent filings.

    Args:
        form_type: Filing type (S-1, 10-K, 10-Q, 8-K, etc.)
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        ticker: Company ticker
        company_name: Company name
        size: Number of results

    Returns:
        Dict with 'filings' list and 'total' count
    """
    url = "https://efts.sec.gov/LATEST/search-index"
    params = {
        "q": company_name or ticker or "*",
        "forms": form_type,
        "dateRange": "custom",
    }
    if date_from:
        params["startdt"] = date_from
    if date_to:
        params["enddt"] = date_to

    # Use the correct EDGAR EFTS endpoint
    # q parameter is full-text search in document content; use form type as query when no specific search
    params_efts = {"forms": form_type}
    if date_from:
        params_efts["startdt"] = date_from
    if date_to:
        params_efts["enddt"] = date_to
    if company_name:
        params_efts["q"] = f'"{company_name}"'
    elif ticker:
        params_efts["q"] = ticker.upper()
    else:
        # Search for the form type name in text to get relevant results
        params_efts["q"] = f'"{form_type}"'

    _rate_limit()
    try:
        resp = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params=params_efts,
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])
        total_obj = data.get("hits", {}).get("total", {})
        total = total_obj.get("value", len(hits)) if isinstance(total_obj, dict) else total_obj

        filings = []
        for hit in hits[:size]:
            src = hit.get("_source", {})
            display_names = src.get("display_names", [])
            company = display_names[0] if display_names else ""
            filings.append({
                "companyName": company,
                "formType": src.get("form", src.get("file_type", "")),
                "filedAt": src.get("file_date", ""),
                "description": src.get("file_description", ""),
                "accessionNumber": src.get("adsh", hit.get("_id", "")),
                "rootForm": src.get("root_forms", [""])[0] if src.get("root_forms") else "",
            })
        return {"total": total, "filings": filings, "source": "edgar-efts-free"}
    except Exception:
        pass

    # Fallback: EDGAR full-text search API
    return _search_edgar_fulltext(form_type, date_from, date_to, ticker, company_name, size)


def _search_edgar_fulltext(
    form_type: str = None,
    date_from: str = None,
    date_to: str = None,
    ticker: str = None,
    company_name: str = None,
    size: int = 10
) -> Dict[str, Any]:
    """Fallback: use EDGAR full-text search at efts.sec.gov."""
    params = {}
    if form_type:
        params["forms"] = form_type
    if date_from:
        params["startdt"] = date_from
    if date_to:
        params["enddt"] = date_to
    if company_name:
        params["q"] = f'"{company_name}"'
    elif ticker:
        params["q"] = ticker.upper()

    _rate_limit()
    try:
        resp = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params=params,
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])
        total = data.get("hits", {}).get("total", {}).get("value", len(hits))

        filings = []
        for hit in hits[:size]:
            src = hit.get("_source", {})
            filings.append({
                "companyName": src.get("entity_name", ""),
                "formType": src.get("file_type", ""),
                "filedAt": src.get("file_date", ""),
                "accessionNumber": hit.get("_id", ""),
            })

        return {"total": total, "filings": filings, "source": "edgar-fulltext-free"}
    except Exception as e:
        return {"error": str(e), "filings": [], "total": 0, "source": "edgar-fulltext-free"}


def get_ipo_filings(
    date_from: str = None,
    date_to: str = None,
    ticker: str = None,
    size: int = 10,
    token: str = None
) -> Dict[str, Any]:
    """
    Get IPO-related filings (S-1, S-1/A, 424B4).

    Args:
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        ticker: Filter by ticker
        size: Number of results
        token: API token (optional)

    Returns:
        Dict with S-1 and 424B4 filings
    """
    if not date_from:
        date_from = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = datetime.now().strftime("%Y-%m-%d")

    s1_filings = search_filings(
        form_type="S-1", date_from=date_from, date_to=date_to,
        ticker=ticker, size=size, token=token
    )
    prospectus_filings = search_filings(
        form_type="424B4", date_from=date_from, date_to=date_to,
        ticker=ticker, size=size, token=token
    )

    return {
        "s1_filings": s1_filings.get("filings", []),
        "s1_total": s1_filings.get("total", 0),
        "prospectus_filings": prospectus_filings.get("filings", []),
        "prospectus_total": prospectus_filings.get("total", 0),
        "date_range": {"from": date_from, "to": date_to},
        "source": s1_filings.get("source", "unknown"),
    }


def get_company_filings_by_ticker(
    ticker: str,
    form_type: str = None,
    size: int = 20
) -> Dict[str, Any]:
    """
    Get all recent filings for a company by ticker using free EDGAR API.
    No API key needed.

    Args:
        ticker: Company ticker symbol (e.g., AAPL, TSLA)
        form_type: Optional filter by form type
        size: Number of results to return

    Returns:
        Dict with company info and filings list
    """
    cik = _get_cik(ticker)
    if not cik:
        return {"error": f"Ticker '{ticker}' not found", "filings": []}

    _rate_limit()
    try:
        url = SEC_EDGAR_SUBMISSIONS.format(cik=cik)
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        company_info = {
            "name": data.get("name", ""),
            "cik": cik,
            "ticker": ticker.upper(),
            "sic": data.get("sic", ""),
            "sicDescription": data.get("sicDescription", ""),
            "stateOfIncorporation": data.get("stateOfIncorporation", ""),
            "fiscalYearEnd": data.get("fiscalYearEnd", ""),
        }

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])
        descriptions = recent.get("primaryDocDescription", [])

        filings = []
        for i in range(min(len(forms), 200)):
            if form_type and forms[i] != form_type:
                continue
            filing = {
                "formType": forms[i],
                "filedAt": dates[i] if i < len(dates) else "",
                "accessionNumber": accessions[i] if i < len(accessions) else "",
                "primaryDocument": primary_docs[i] if i < len(primary_docs) else "",
                "description": descriptions[i] if i < len(descriptions) else "",
            }
            # Build link to filing
            if filing["accessionNumber"]:
                acc_no_dash = filing["accessionNumber"].replace("-", "")
                filing["linkToFiling"] = (
                    f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}"
                    f"/{acc_no_dash}/{filing['primaryDocument']}"
                )
            filings.append(filing)
            if len(filings) >= size:
                break

        return {
            "company": company_info,
            "filings": filings,
            "total": len(filings),
            "source": "edgar-submissions-free",
        }

    except Exception as e:
        return {"error": str(e), "filings": [], "total": 0}


def get_insider_trading(
    ticker: str = None,
    date_from: str = None,
    date_to: str = None,
    size: int = 10,
    token: str = None
) -> Dict[str, Any]:
    """
    Get insider trading filings (Form 4).

    Args:
        ticker: Company ticker
        date_from: Start date
        date_to: End date
        size: Number of results
        token: API token (optional)

    Returns:
        Dict with insider trading filings
    """
    return search_filings(
        form_type="4", date_from=date_from, date_to=date_to,
        ticker=ticker, size=size, token=token
    )


def get_institutional_holdings(
    ticker: str = None,
    date_from: str = None,
    date_to: str = None,
    size: int = 10,
    token: str = None
) -> Dict[str, Any]:
    """
    Get institutional holdings filings (Form 13F-HR).

    Args:
        ticker: Company ticker
        date_from: Start date
        date_to: End date
        size: Number of results
        token: API token (optional)

    Returns:
        Dict with 13F filings
    """
    return search_filings(
        form_type="13F-HR", date_from=date_from, date_to=date_to,
        ticker=ticker, size=size, token=token
    )


def get_annual_reports(
    ticker: str = None,
    date_from: str = None,
    date_to: str = None,
    size: int = 10,
    token: str = None
) -> Dict[str, Any]:
    """
    Get annual reports (Form 10-K).

    Args:
        ticker: Company ticker
        date_from: Start date
        date_to: End date
        size: Number of results
        token: API token (optional)

    Returns:
        Dict with 10-K filings
    """
    return search_filings(
        form_type="10-K", date_from=date_from, date_to=date_to,
        ticker=ticker, size=size, token=token
    )


def get_quarterly_reports(
    ticker: str = None,
    date_from: str = None,
    date_to: str = None,
    size: int = 10,
    token: str = None
) -> Dict[str, Any]:
    """
    Get quarterly reports (Form 10-Q).

    Args:
        ticker: Company ticker
        date_from: Start date
        date_to: End date
        size: Number of results
        token: API token (optional)

    Returns:
        Dict with 10-Q filings
    """
    return search_filings(
        form_type="10-Q", date_from=date_from, date_to=date_to,
        ticker=ticker, size=size, token=token
    )


def get_8k_events(
    ticker: str = None,
    date_from: str = None,
    date_to: str = None,
    size: int = 10,
    token: str = None
) -> Dict[str, Any]:
    """
    Get material event filings (Form 8-K).

    Args:
        ticker: Company ticker
        date_from: Start date
        date_to: End date
        size: Number of results
        token: API token (optional)

    Returns:
        Dict with 8-K filings
    """
    return search_filings(
        form_type="8-K", date_from=date_from, date_to=date_to,
        ticker=ticker, size=size, token=token
    )


def get_private_placements(
    date_from: str = None,
    date_to: str = None,
    company_name: str = None,
    size: int = 10,
    token: str = None
) -> Dict[str, Any]:
    """
    Get private placement filings (Form D).

    Args:
        date_from: Start date
        date_to: End date
        company_name: Company name
        size: Number of results
        token: API token (optional)

    Returns:
        Dict with Form D filings
    """
    return search_filings(
        form_type="D", date_from=date_from, date_to=date_to,
        company_name=company_name, size=size, token=token
    )


def list_form_types() -> List[str]:
    """
    List common SEC filing form types.

    Returns:
        List of common form type strings with descriptions
    """
    return [
        "S-1 — Registration Statement (IPO)",
        "S-1/A — Amendment to S-1",
        "424B4 — Final Prospectus",
        "10-K — Annual Report",
        "10-Q — Quarterly Report",
        "8-K — Current Report (Material Events)",
        "4 — Insider Trading (Statement of Changes)",
        "3 — Initial Statement of Beneficial Ownership",
        "5 — Annual Statement of Beneficial Ownership",
        "13F-HR — Institutional Holdings",
        "13D — Activist Investor Ownership (>5%)",
        "13G — Passive Investor Ownership (>5%)",
        "D — Private Placement / Exempt Offering",
        "DEF 14A — Definitive Proxy Statement",
        "SC 13D — Schedule 13D (Beneficial Ownership)",
        "SC 13G — Schedule 13G (Passive Ownership)",
        "144 — Notice of Proposed Sale of Securities",
    ]


if __name__ == "__main__":
    print("=== SEC-API.io Module Test ===")
    print(f"Functions: {[f for f in dir() if not f.startswith('_') and callable(eval(f))]}")

    # Test free EDGAR search for company filings
    print("\n--- Testing get_company_filings_by_ticker('AAPL') ---")
    result = get_company_filings_by_ticker("AAPL", form_type="10-K", size=3)
    print(json.dumps(result, indent=2, default=str)[:1500])

    # Test IPO filings search
    print("\n--- Testing get_ipo_filings ---")
    ipo = get_ipo_filings(date_from="2024-01-01", date_to="2025-12-31", size=3)
    print(json.dumps(ipo, indent=2, default=str)[:1500])

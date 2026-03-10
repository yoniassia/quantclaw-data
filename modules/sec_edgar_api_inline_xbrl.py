#!/usr/bin/env python3
"""
SEC EDGAR API (Inline XBRL) — Company Filings & Structured Financial Data

Data Source: SEC EDGAR (data.sec.gov, efts.sec.gov)
Update: Real-time as filings are submitted, daily indexes
Free: Yes — No API key required, public access
Rate Limit: 10 requests/second, must include User-Agent with contact email

Provides:
- Company submissions metadata (filings history)
- Company facts (XBRL financial data: revenue, assets, EPS, etc.)
- Company concept lookups (single XBRL tag across time)
- Full-text search of filings (EFTS)
- CIK ↔ ticker resolution

Usage:
- Pull structured financials (revenue, net income, EPS) without scraping
- Track insider filings (Form 4), quarterly/annual reports (10-Q, 10-K)
- Search filings by keyword
- Build fundamental datasets for backtesting
"""

import requests
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# --- Configuration ---
CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/sec_edgar")
os.makedirs(CACHE_DIR, exist_ok=True)

# SEC requires a descriptive User-Agent with contact info
HEADERS = {
    "User-Agent": "QuantClaw/1.0 (quantclaw@moneyclaw.com)",
    "Accept-Encoding": "gzip, deflate",
}

# Base URLs
SUBMISSIONS_BASE = "https://data.sec.gov/submissions"
COMPANY_FACTS_BASE = "https://data.sec.gov/api/xbrl/companyfacts"
COMPANY_CONCEPT_BASE = "https://data.sec.gov/api/xbrl/companyconcept"
EFTS_BASE = "https://efts.sec.gov/LATEST/search-index"
EDGAR_SEARCH_BASE = "https://efts.sec.gov/LATEST"
TICKER_URL = "https://www.sec.gov/files/company_tickers.json"

# Common XBRL tags for financial data
COMMON_XBRL_TAGS = {
    "revenue": ("us-gaap", "Revenues"),
    "revenue_alt": ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
    "net_income": ("us-gaap", "NetIncomeLoss"),
    "total_assets": ("us-gaap", "Assets"),
    "total_liabilities": ("us-gaap", "Liabilities"),
    "stockholders_equity": ("us-gaap", "StockholdersEquity"),
    "eps_basic": ("us-gaap", "EarningsPerShareBasic"),
    "eps_diluted": ("us-gaap", "EarningsPerShareDiluted"),
    "operating_income": ("us-gaap", "OperatingIncomeLoss"),
    "cash": ("us-gaap", "CashAndCashEquivalentsAtCarryingValue"),
    "shares_outstanding": ("dei", "EntityCommonStockSharesOutstanding"),
    "long_term_debt": ("us-gaap", "LongTermDebt"),
    "gross_profit": ("us-gaap", "GrossProfit"),
    "total_revenue": ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
    "operating_expenses": ("us-gaap", "OperatingExpenses"),
    "cost_of_revenue": ("us-gaap", "CostOfRevenue"),
    "research_development": ("us-gaap", "ResearchAndDevelopmentExpense"),
}

# --- Internal Helpers ---

def _format_cik(cik: str) -> str:
    """Pad CIK to 10 digits with leading zeros."""
    cik_clean = str(cik).strip().lstrip("0")
    return cik_clean.zfill(10)


def _sec_request(url: str, timeout: int = 15) -> dict:
    """Make a rate-limited request to SEC EDGAR with proper headers."""
    time.sleep(0.12)  # Stay under 10 req/s
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {resp.status_code}: {str(e)}", "url": url}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "url": url}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "url": url}


def _get_cache(key: str, max_age_hours: int = 24) -> Optional[dict]:
    """Read from file cache if fresh enough."""
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(cache_file):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if age < timedelta(hours=max_age_hours):
            with open(cache_file) as f:
                return json.load(f)
    return None


def _set_cache(key: str, data: dict):
    """Write data to file cache."""
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    with open(cache_file, "w") as f:
        json.dump(data, f, indent=2, default=str)


# --- Ticker / CIK Resolution ---

def get_ticker_to_cik_map() -> Dict[str, str]:
    """
    Get mapping of stock tickers to CIK numbers.
    Uses SEC's official company_tickers.json.
    
    Returns:
        Dict mapping uppercase tickers to CIK strings (zero-padded to 10 digits)
    
    Example:
        >>> m = get_ticker_to_cik_map()
        >>> m["AAPL"]
        '0000320193'
    """
    cached = _get_cache("ticker_cik_map", max_age_hours=168)  # 1 week
    if cached:
        return cached

    data = _sec_request(TICKER_URL)
    if "error" in data:
        return data

    mapping = {}
    for entry in data.values():
        ticker = entry.get("ticker", "").upper()
        cik = _format_cik(str(entry.get("cik_str", "")))
        if ticker:
            mapping[ticker] = cik

    _set_cache("ticker_cik_map", mapping)
    return mapping


def resolve_ticker_to_cik(ticker: str) -> str:
    """
    Resolve a stock ticker to its SEC CIK number.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

    Returns:
        CIK string zero-padded to 10 digits, or error dict
    
    Example:
        >>> resolve_ticker_to_cik("AAPL")
        '0000320193'
    """
    mapping = get_ticker_to_cik_map()
    if "error" in mapping:
        return mapping
    cik = mapping.get(ticker.upper())
    if not cik:
        return {"error": f"Ticker '{ticker}' not found in SEC database"}
    return cik


# --- Company Submissions ---

def get_company_submissions(cik: str) -> Dict:
    """
    Get company filing submissions metadata from EDGAR.
    Includes company info + recent filings list.

    Args:
        cik: CIK number (e.g., '0000320193') or ticker (e.g., 'AAPL')

    Returns:
        Dict with keys: name, cik, tickers, exchanges, sic, sicDescription,
        category, fiscalYearEnd, filings (recent + older)
    
    Example:
        >>> data = get_company_submissions("AAPL")
        >>> data["name"]
        'Apple Inc.'
    """
    if not cik.isdigit():
        cik = resolve_ticker_to_cik(cik)
        if isinstance(cik, dict):
            return cik

    cik_padded = _format_cik(cik)
    cache_key = f"submissions_{cik_padded}"
    cached = _get_cache(cache_key, max_age_hours=12)
    if cached:
        return cached

    url = f"{SUBMISSIONS_BASE}/CIK{cik_padded}.json"
    data = _sec_request(url)
    if "error" not in data:
        _set_cache(cache_key, data)
    return data


def get_company_info(cik: str) -> Dict:
    """
    Get basic company information from EDGAR.

    Args:
        cik: CIK number or ticker symbol

    Returns:
        Dict with: name, cik, tickers, exchanges, sic, sicDescription,
        category, fiscalYearEnd, stateOfIncorporation, ein
    
    Example:
        >>> info = get_company_info("MSFT")
        >>> info["name"]
        'MICROSOFT CORP'
    """
    subs = get_company_submissions(cik)
    if "error" in subs:
        return subs

    return {
        "name": subs.get("name"),
        "cik": subs.get("cik"),
        "entityType": subs.get("entityType"),
        "tickers": subs.get("tickers", []),
        "exchanges": subs.get("exchanges", []),
        "sic": subs.get("sic"),
        "sicDescription": subs.get("sicDescription"),
        "category": subs.get("category"),
        "fiscalYearEnd": subs.get("fiscalYearEnd"),
        "stateOfIncorporation": subs.get("stateOfIncorporation"),
        "ein": subs.get("ein"),
        "phone": subs.get("phone"),
        "website": subs.get("website"),
    }


def get_recent_filings(cik: str, form_type: Optional[str] = None, limit: int = 20) -> List[Dict]:
    """
    Get recent filings for a company.

    Args:
        cik: CIK number or ticker symbol
        form_type: Filter by form type (e.g., '10-K', '10-Q', '8-K', '4')
        limit: Max number of filings to return

    Returns:
        List of dicts with: accessionNumber, form, filingDate, primaryDocument, etc.
    
    Example:
        >>> filings = get_recent_filings("AAPL", form_type="10-K", limit=5)
        >>> len(filings) > 0
        True
    """
    subs = get_company_submissions(cik)
    if "error" in subs:
        return subs

    recent = subs.get("filings", {}).get("recent", {})
    if not recent:
        return {"error": "No recent filings found"}

    # Build list of filings from parallel arrays
    keys = list(recent.keys())
    count = len(recent.get("accessionNumber", []))
    filings = []
    for i in range(count):
        filing = {k: recent[k][i] for k in keys if i < len(recent[k])}
        if form_type and filing.get("form") != form_type:
            continue
        filings.append(filing)
        if len(filings) >= limit:
            break

    return filings


# --- Company Facts (XBRL Financial Data) ---

def get_company_facts(cik: str) -> Dict:
    """
    Get ALL XBRL facts for a company (all financial data reported in XBRL).
    This is the core endpoint for structured financial data.

    Args:
        cik: CIK number or ticker symbol

    Returns:
        Dict with 'facts' key containing us-gaap, dei, and other taxonomies,
        each with XBRL tags and their reported values across all filings
    
    Example:
        >>> facts = get_company_facts("AAPL")
        >>> "us-gaap" in facts.get("facts", {})
        True
    """
    if not cik.isdigit():
        cik = resolve_ticker_to_cik(cik)
        if isinstance(cik, dict):
            return cik

    cik_padded = _format_cik(cik)
    cache_key = f"facts_{cik_padded}"
    cached = _get_cache(cache_key, max_age_hours=24)
    if cached:
        return cached

    url = f"{COMPANY_FACTS_BASE}/CIK{cik_padded}.json"
    data = _sec_request(url, timeout=30)
    if "error" not in data:
        _set_cache(cache_key, data)
    return data


def get_company_concept(cik: str, taxonomy: str, tag: str) -> Dict:
    """
    Get a single XBRL concept/tag for a company across all filings.
    Useful for tracking one metric (e.g., Revenue) over time.

    Args:
        cik: CIK number or ticker symbol
        taxonomy: XBRL taxonomy (e.g., 'us-gaap', 'dei')
        tag: XBRL tag name (e.g., 'Revenues', 'Assets')

    Returns:
        Dict with 'units' containing time-series data for the concept
    
    Example:
        >>> data = get_company_concept("AAPL", "us-gaap", "Revenues")
        >>> "units" in data
        True
    """
    if not cik.isdigit():
        cik = resolve_ticker_to_cik(cik)
        if isinstance(cik, dict):
            return cik

    cik_padded = _format_cik(cik)
    cache_key = f"concept_{cik_padded}_{taxonomy}_{tag}"
    cached = _get_cache(cache_key, max_age_hours=24)
    if cached:
        return cached

    url = f"{COMPANY_CONCEPT_BASE}/CIK{cik_padded}/{taxonomy}/{tag}.json"
    data = _sec_request(url)
    if "error" not in data:
        _set_cache(cache_key, data)
    return data


# --- High-Level Financial Extraction ---

def get_financial_metric(cik: str, metric: str, periods: int = 20) -> List[Dict]:
    """
    Get a specific financial metric over time using common XBRL tag mapping.

    Args:
        cik: CIK number or ticker symbol
        metric: One of: revenue, net_income, total_assets, total_liabilities,
                stockholders_equity, eps_basic, eps_diluted, operating_income,
                cash, shares_outstanding, long_term_debt, gross_profit,
                operating_expenses, cost_of_revenue, research_development
        periods: Number of recent data points to return

    Returns:
        List of dicts with: end (date), val, form, filed, fy, fp
    
    Example:
        >>> data = get_financial_metric("AAPL", "revenue", periods=8)
        >>> len(data) > 0
        True
    """
    if metric not in COMMON_XBRL_TAGS:
        return {"error": f"Unknown metric '{metric}'. Available: {list(COMMON_XBRL_TAGS.keys())}"}

    # For revenue, try the modern tag first (more data for recent filings)
    if metric == "revenue":
        taxonomy, tag = COMMON_XBRL_TAGS["revenue_alt"]
        concept = get_company_concept(cik, taxonomy, tag)
        if "error" in concept:
            taxonomy, tag = COMMON_XBRL_TAGS["revenue"]
            concept = get_company_concept(cik, taxonomy, tag)
            if "error" in concept:
                return concept
    else:
        taxonomy, tag = COMMON_XBRL_TAGS[metric]
        concept = get_company_concept(cik, taxonomy, tag)
        if "error" in concept:
            return concept

    units = concept.get("units", {})
    # Get USD values first, fall back to shares or other units
    values = units.get("USD", units.get("USD/shares", units.get("shares", [])))
    if not values:
        # Try first available unit
        for unit_key, unit_vals in units.items():
            values = unit_vals
            break

    if not values:
        return []

    # Filter to 10-K and 10-Q filings, deduplicate by end date + form
    seen = set()
    filtered = []
    for v in values:
        form = v.get("form", "")
        if form not in ("10-K", "10-Q", "10-K/A", "10-Q/A"):
            continue
        key = (v.get("end"), form)
        if key in seen:
            continue
        seen.add(key)
        filtered.append({
            "end": v.get("end"),
            "val": v.get("val"),
            "form": form,
            "filed": v.get("filed"),
            "fy": v.get("fy"),
            "fp": v.get("fp"),
            "accn": v.get("accn"),
        })

    # Sort by end date descending, return most recent
    filtered.sort(key=lambda x: x.get("end", ""), reverse=True)
    return filtered[:periods]


def get_financials_summary(cik: str) -> Dict:
    """
    Get a summary of key financial metrics for a company.
    Pulls latest values for revenue, net income, EPS, assets, etc.

    Args:
        cik: CIK number or ticker symbol

    Returns:
        Dict with company info and latest financial metrics
    
    Example:
        >>> summary = get_financials_summary("MSFT")
        >>> "company" in summary
        True
    """
    info = get_company_info(cik)
    if "error" in info:
        return info

    metrics = {}
    for metric_name in ["revenue", "net_income", "eps_diluted", "total_assets",
                         "total_liabilities", "cash", "operating_income"]:
        data = get_financial_metric(cik, metric_name, periods=1)
        if isinstance(data, list) and data:
            metrics[metric_name] = {
                "value": data[0].get("val"),
                "date": data[0].get("end"),
                "form": data[0].get("form"),
            }
        elif isinstance(data, dict) and "error" in data:
            metrics[metric_name] = {"error": data["error"]}
        else:
            metrics[metric_name] = {"value": None}

    return {
        "company": info,
        "latest_financials": metrics,
        "retrieved_at": datetime.now().isoformat(),
    }


# --- Full-Text Search ---

def search_filings(query: str, date_range: Optional[str] = None,
                   forms: Optional[List[str]] = None, limit: int = 10) -> Dict:
    """
    Full-text search across all EDGAR filings.

    Args:
        query: Search text (e.g., 'artificial intelligence revenue')
        date_range: Date filter as 'YYYY-MM-DD,YYYY-MM-DD' (start,end)
        forms: List of form types to filter (e.g., ['10-K', '10-Q'])
        limit: Max results (max 100)

    Returns:
        Dict with 'hits' containing matched filings with snippets
    
    Example:
        >>> results = search_filings("artificial intelligence", forms=["10-K"], limit=5)
        >>> "hits" in results
        True
    """
    params = {
        "q": query,
        "dateRange": "custom" if date_range else None,
        "startdt": date_range.split(",")[0] if date_range else None,
        "enddt": date_range.split(",")[1] if date_range and "," in date_range else None,
        "forms": ",".join(forms) if forms else None,
    }
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    url = f"{EDGAR_SEARCH_BASE}/search-index"
    try:
        time.sleep(0.12)
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        # Fallback to EFTS full-text search
        url2 = f"https://efts.sec.gov/LATEST/search-index"
        params2 = {"q": query, "forms": ",".join(forms) if forms else None}
        params2 = {k: v for k, v in params2.items() if v is not None}
        try:
            time.sleep(0.12)
            resp2 = requests.get(url2, params=params2, headers=HEADERS, timeout=15)
            resp2.raise_for_status()
            return resp2.json()
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}


def get_xbrl_tags_list(cik: str) -> List[str]:
    """
    List all available XBRL tags for a company.
    Useful for discovering what financial data points are available.

    Args:
        cik: CIK number or ticker symbol

    Returns:
        List of XBRL tag names available for the company
    
    Example:
        >>> tags = get_xbrl_tags_list("AAPL")
        >>> "Revenues" in tags or "Assets" in tags
        True
    """
    facts = get_company_facts(cik)
    if "error" in facts:
        return facts

    tags = []
    for taxonomy, taxonomy_data in facts.get("facts", {}).items():
        for tag_name in taxonomy_data.keys():
            tags.append(f"{taxonomy}:{tag_name}")
    return sorted(tags)


# --- Filing Document Access ---

def get_filing_document_url(cik: str, accession_number: str, primary_document: str) -> str:
    """
    Construct URL to access a specific filing document on EDGAR.

    Args:
        cik: CIK number or ticker
        accession_number: Filing accession number (e.g., '0000320193-23-000106')
        primary_document: Document filename (e.g., 'aapl-20230930.htm')

    Returns:
        Full URL to the filing document
    """
    if not cik.isdigit():
        cik = resolve_ticker_to_cik(cik)
        if isinstance(cik, dict):
            return cik

    cik_padded = _format_cik(cik)
    accession_clean = accession_number.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik_padded}/{accession_clean}/{primary_document}"


if __name__ == "__main__":
    print(json.dumps({
        "module": "sec_edgar_api_inline_xbrl",
        "status": "active",
        "source": "https://www.sec.gov/edgar/sec-api-documentation",
        "functions": [
            "get_ticker_to_cik_map", "resolve_ticker_to_cik",
            "get_company_submissions", "get_company_info", "get_recent_filings",
            "get_company_facts", "get_company_concept",
            "get_financial_metric", "get_financials_summary",
            "search_filings", "get_xbrl_tags_list", "get_filing_document_url",
        ],
    }, indent=2))

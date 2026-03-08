#!/usr/bin/env python3
"""
SEC EDGAR Filings Module (sec-api.io alternative)
Access SEC EDGAR filings, company data, insider trades, and XBRL financials.

Uses free SEC EDGAR public APIs (no API key required):
- data.sec.gov/submissions — Company filings metadata
- efts.sec.gov/LATEST/search-index — Full-text search across filings
- data.sec.gov/api/xbrl — XBRL financial data (companyfacts, companyconcept)
- SEC company tickers mapping

Commands:
- sec-filings <ticker> [--form-type 10-K|10-Q|8-K|4] [--limit N]
- sec-company-info <ticker>
- sec-search <query> [--forms FORMS] [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]
- sec-xbrl-facts <ticker> [--concept CONCEPT]
- sec-insider-filings <ticker> [--limit N]
- sec-recent-filings [--form-type TYPE] [--limit N]
- sec-ticker-to-cik <ticker>
"""

import sys
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus, urlencode

# ─── Configuration ───────────────────────────────────────────────────────────

EDGAR_SUBMISSIONS_BASE = "https://data.sec.gov/submissions"
EDGAR_XBRL_BASE = "https://data.sec.gov/api/xbrl"
EFTS_SEARCH_BASE = "https://efts.sec.gov/LATEST/search-index"
EDGAR_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# SEC requires a User-Agent with contact info
HEADERS = {
    "User-Agent": "QuantClaw/1.0 (quantclaw@moneyclaw.com)",
    "Accept": "application/json",
}

# Rate limiting: SEC allows max 10 req/sec
_last_request_time = 0
RATE_LIMIT_DELAY = 0.12  # ~8 req/sec to stay safe

# Cache for ticker -> CIK mapping
_ticker_cik_cache: Dict[str, str] = {}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _rate_limit():
    """Enforce SEC rate limiting."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < RATE_LIMIT_DELAY:
        time.sleep(RATE_LIMIT_DELAY - elapsed)
    _last_request_time = time.time()


def _get(url: str, params: Optional[dict] = None, timeout: int = 15) -> dict:
    """Make a rate-limited GET request to SEC APIs."""
    _rate_limit()
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {resp.status_code}: {str(e)}", "url": url}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "url": url}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "url": url}


def _pad_cik(cik: str) -> str:
    """Pad CIK to 10 digits with leading zeros."""
    return cik.lstrip("0").zfill(10)


# ─── Ticker / CIK Resolution ────────────────────────────────────────────────

def ticker_to_cik(ticker: str) -> Dict[str, Any]:
    """
    Resolve a stock ticker to its SEC CIK number.

    Args:
        ticker: Stock ticker symbol (e.g., 'TSLA', 'AAPL')

    Returns:
        Dict with cik, name, ticker fields or error
    """
    ticker = ticker.upper().strip()

    # Check cache
    if ticker in _ticker_cik_cache:
        return {"ticker": ticker, "cik": _ticker_cik_cache[ticker], "source": "cache"}

    data = _get(COMPANY_TICKERS_URL)
    if "error" in data:
        return data

    for entry in data.values():
        if entry.get("ticker", "").upper() == ticker:
            cik = _pad_cik(str(entry["cik_str"]))
            _ticker_cik_cache[ticker] = cik
            return {
                "ticker": ticker,
                "cik": cik,
                "name": entry.get("title", ""),
            }

    return {"error": f"Ticker '{ticker}' not found in SEC database"}


def cik_to_ticker(cik: str) -> Dict[str, Any]:
    """
    Resolve a CIK number to its stock ticker.

    Args:
        cik: SEC CIK number (e.g., '0001318605')

    Returns:
        Dict with cik, ticker, name fields or error
    """
    cik_num = int(cik.lstrip("0"))
    data = _get(COMPANY_TICKERS_URL)
    if "error" in data:
        return data

    for entry in data.values():
        if entry.get("cik_str") == cik_num:
            return {
                "cik": _pad_cik(str(cik_num)),
                "ticker": entry.get("ticker", ""),
                "name": entry.get("title", ""),
            }

    return {"error": f"CIK '{cik}' not found"}


# ─── Company Info ────────────────────────────────────────────────────────────

def get_company_info(ticker: str) -> Dict[str, Any]:
    """
    Get detailed company information from SEC EDGAR.

    Args:
        ticker: Stock ticker symbol (e.g., 'TSLA')

    Returns:
        Dict with company details: name, CIK, SIC, addresses, former names, etc.
    """
    resolved = ticker_to_cik(ticker)
    if "error" in resolved:
        return resolved

    cik = resolved["cik"]
    data = _get(f"{EDGAR_SUBMISSIONS_BASE}/CIK{cik}.json")
    if "error" in data:
        return data

    return {
        "ticker": ticker.upper(),
        "cik": data.get("cik", ""),
        "name": data.get("name", ""),
        "entity_type": data.get("entityType", ""),
        "sic": data.get("sic", ""),
        "sic_description": data.get("sicDescription", ""),
        "category": data.get("category", ""),
        "fiscal_year_end": data.get("fiscalYearEnd", ""),
        "state_of_incorporation": data.get("stateOfIncorporation", ""),
        "phone": data.get("phone", ""),
        "tickers": data.get("tickers", []),
        "exchanges": data.get("exchanges", []),
        "ein": data.get("ein", ""),
        "addresses": data.get("addresses", {}),
        "former_names": data.get("formerNames", []),
    }


# ─── Filings ─────────────────────────────────────────────────────────────────

def get_filings(
    ticker: str,
    form_type: Optional[str] = None,
    limit: int = 20,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get SEC filings for a company.

    Args:
        ticker: Stock ticker symbol
        form_type: Filter by form type (e.g., '10-K', '10-Q', '8-K', '4')
        limit: Maximum number of filings to return
        start_date: Filter filings after this date (YYYY-MM-DD)
        end_date: Filter filings before this date (YYYY-MM-DD)

    Returns:
        List of filing dicts with accession_number, form, date, description, urls
    """
    resolved = ticker_to_cik(ticker)
    if "error" in resolved:
        return [resolved]

    cik = resolved["cik"]
    data = _get(f"{EDGAR_SUBMISSIONS_BASE}/CIK{cik}.json")
    if "error" in data:
        return [data]

    recent = data.get("filings", {}).get("recent", {})
    if not recent:
        return [{"error": "No recent filings found"}]

    accessions = recent.get("accessionNumber", [])
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    descriptions = recent.get("primaryDocDescription", [])
    doc_names = recent.get("primaryDocument", [])

    results = []
    cik_raw = cik.lstrip("0")

    for i in range(len(accessions)):
        form = forms[i] if i < len(forms) else ""
        date = dates[i] if i < len(dates) else ""

        # Apply filters
        if form_type and form.upper() != form_type.upper():
            continue
        if start_date and date < start_date:
            continue
        if end_date and date > end_date:
            continue

        acc_no = accessions[i]
        acc_no_dashes = acc_no.replace("-", "")
        doc = doc_names[i] if i < len(doc_names) else ""
        desc = descriptions[i] if i < len(descriptions) else ""

        filing = {
            "accession_number": acc_no,
            "form_type": form,
            "filing_date": date,
            "description": desc,
            "document": doc,
            "filing_url": f"https://www.sec.gov/Archives/edgar/data/{cik_raw}/{acc_no_dashes}/{doc}",
            "index_url": f"https://www.sec.gov/Archives/edgar/data/{cik_raw}/{acc_no_dashes}/",
        }
        results.append(filing)

        if len(results) >= limit:
            break

    return results


def get_recent_filings(
    form_type: str = "10-K",
    limit: int = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search for recent filings across all companies using EDGAR full-text search.

    Args:
        form_type: Form type to search for (e.g., '10-K', '10-Q', '8-K')
        limit: Maximum results (max 50)
        start_date: Start date filter (YYYY-MM-DD)
        end_date: End date filter (YYYY-MM-DD)

    Returns:
        List of filing dicts with company, form, date, and filing details
    """
    params = {"forms": form_type, "q": "*"}
    if start_date and end_date:
        params["dateRange"] = "custom"
        params["startdt"] = start_date
        params["enddt"] = end_date

    data = _get(EFTS_SEARCH_BASE, params=params)
    if "error" in data:
        return [data]

    hits = data.get("hits", {}).get("hits", [])
    results = []

    for hit in hits[:min(limit, 50)]:
        src = hit.get("_source", {})
        results.append({
            "company": (src.get("display_names") or ["Unknown"])[0],
            "cik": (src.get("ciks") or [""])[0],
            "form_type": src.get("form", ""),
            "filing_date": src.get("file_date", ""),
            "period_ending": src.get("period_ending", ""),
            "accession_number": src.get("adsh", ""),
            "file_type": src.get("file_type", ""),
            "sic": (src.get("sics") or [""])[0],
            "location": (src.get("biz_locations") or [""])[0],
        })

    return results


# ─── Full-Text Search ────────────────────────────────────────────────────────

def search_filings(
    query: str,
    forms: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Full-text search across SEC EDGAR filings content.

    Args:
        query: Search query (supports quoted phrases and boolean operators)
        forms: Comma-separated form types (e.g., '10-K,10-Q')
        start_date: Start date filter (YYYY-MM-DD)
        end_date: End date filter (YYYY-MM-DD)
        limit: Maximum results (max 50)

    Returns:
        List of matching filing dicts
    """
    params = {"q": query}
    if forms:
        params["forms"] = forms
    if start_date and end_date:
        params["dateRange"] = "custom"
        params["startdt"] = start_date
        params["enddt"] = end_date

    data = _get(EFTS_SEARCH_BASE, params=params)
    if "error" in data:
        return [data]

    total = data.get("hits", {}).get("total", {}).get("value", 0)
    hits = data.get("hits", {}).get("hits", [])
    results = []

    for hit in hits[:min(limit, 50)]:
        src = hit.get("_source", {})
        results.append({
            "company": (src.get("display_names") or ["Unknown"])[0],
            "cik": (src.get("ciks") or [""])[0],
            "form_type": src.get("form", ""),
            "filing_date": src.get("file_date", ""),
            "period_ending": src.get("period_ending", ""),
            "accession_number": src.get("adsh", ""),
            "file_type": src.get("file_type", ""),
            "relevance_score": hit.get("_score", 0),
        })

    return results if results else [{"info": f"No results for query: {query}", "total": total}]


# ─── XBRL Financial Data ────────────────────────────────────────────────────

def get_company_facts(ticker: str) -> Dict[str, Any]:
    """
    Get all XBRL financial facts for a company (revenue, net income, assets, etc).

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with taxonomy -> concept -> units -> time series data
    """
    resolved = ticker_to_cik(ticker)
    if "error" in resolved:
        return resolved

    cik = resolved["cik"]
    data = _get(f"{EDGAR_XBRL_BASE}/companyfacts/CIK{cik}.json")
    if "error" in data:
        return data

    # Summarize available facts
    facts = data.get("facts", {})
    summary = {
        "ticker": ticker.upper(),
        "cik": cik,
        "entity_name": data.get("entityName", ""),
        "taxonomies": {},
    }

    for taxonomy, concepts in facts.items():
        concept_list = []
        for concept_name, concept_data in concepts.items():
            units = list(concept_data.get("units", {}).keys())
            concept_list.append({
                "concept": concept_name,
                "label": concept_data.get("label", ""),
                "units": units,
            })
        summary["taxonomies"][taxonomy] = {
            "concept_count": len(concept_list),
            "concepts": concept_list[:50],  # First 50 to keep response manageable
        }

    return summary


def get_financial_concept(
    ticker: str,
    concept: str = "Revenue",
    taxonomy: str = "us-gaap",
) -> Dict[str, Any]:
    """
    Get time series data for a specific XBRL financial concept.

    Common concepts: Revenue, NetIncomeLoss, Assets, Liabilities,
    StockholdersEquity, EarningsPerShareBasic, OperatingIncomeLoss,
    CashAndCashEquivalentsAtCarryingValue, LongTermDebt

    Args:
        ticker: Stock ticker symbol
        concept: XBRL concept name (e.g., 'Revenue', 'NetIncomeLoss')
        taxonomy: XBRL taxonomy (default: 'us-gaap')

    Returns:
        Dict with time series data for the concept
    """
    resolved = ticker_to_cik(ticker)
    if "error" in resolved:
        return resolved

    cik = resolved["cik"]
    url = f"{EDGAR_XBRL_BASE}/companyconcept/CIK{cik}/{taxonomy}/{concept}.json"
    data = _get(url)
    if "error" in data:
        return data

    result = {
        "ticker": ticker.upper(),
        "cik": cik,
        "entity_name": data.get("entityName", ""),
        "concept": concept,
        "taxonomy": taxonomy,
        "label": data.get("label", ""),
        "description": data.get("description", ""),
        "data": {},
    }

    for unit, entries in data.get("units", {}).items():
        # Get most recent entries, prefer annual (10-K) filings
        annual = [e for e in entries if e.get("form") in ("10-K", "10-K/A")]
        quarterly = [e for e in entries if e.get("form") in ("10-Q", "10-Q/A")]

        result["data"][unit] = {
            "annual": [
                {
                    "period_end": e.get("end", ""),
                    "value": e.get("val"),
                    "filed": e.get("filed", ""),
                    "form": e.get("form", ""),
                    "fiscal_year": e.get("fy"),
                    "fiscal_period": e.get("fp", ""),
                    "accession": e.get("accn", ""),
                }
                for e in sorted(annual, key=lambda x: x.get("end", ""), reverse=True)[:20]
            ],
            "quarterly": [
                {
                    "period_end": e.get("end", ""),
                    "value": e.get("val"),
                    "filed": e.get("filed", ""),
                    "form": e.get("form", ""),
                    "fiscal_year": e.get("fy"),
                    "fiscal_period": e.get("fp", ""),
                }
                for e in sorted(quarterly, key=lambda x: x.get("end", ""), reverse=True)[:20]
            ],
        }

    return result


# ─── Insider Trading Filings ────────────────────────────────────────────────

def get_insider_filings(ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get insider trading filings (Form 3, 4, 5) for a company.

    Args:
        ticker: Stock ticker symbol
        limit: Maximum number of filings

    Returns:
        List of insider filing dicts
    """
    return get_filings(ticker, form_type="4", limit=limit)


def get_institutional_filings(ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get institutional holdings filings (Form 13F) for a company.

    Args:
        ticker: Stock ticker symbol
        limit: Maximum number of filings

    Returns:
        List of 13F filing dicts
    """
    return get_filings(ticker, form_type="13F-HR", limit=limit)


# ─── Key Financial Metrics (Convenience) ─────────────────────────────────────

def get_revenue_history(ticker: str) -> Dict[str, Any]:
    """
    Get revenue history from XBRL data.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with annual and quarterly revenue data
    """
    # Try multiple possible concept names
    for concept in ["Revenue", "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                     "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax"]:
        result = get_financial_concept(ticker, concept=concept)
        if "error" not in result and result.get("data"):
            return result
    return {"error": f"No revenue data found for {ticker}"}


def get_net_income_history(ticker: str) -> Dict[str, Any]:
    """
    Get net income history from XBRL data.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with annual and quarterly net income data
    """
    for concept in ["NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic"]:
        result = get_financial_concept(ticker, concept=concept)
        if "error" not in result and result.get("data"):
            return result
    return {"error": f"No net income data found for {ticker}"}


def get_eps_history(ticker: str) -> Dict[str, Any]:
    """
    Get earnings per share history from XBRL data.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with annual and quarterly EPS data
    """
    return get_financial_concept(ticker, concept="EarningsPerShareBasic")


def get_total_assets(ticker: str) -> Dict[str, Any]:
    """
    Get total assets history from XBRL data.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with annual and quarterly total assets data
    """
    return get_financial_concept(ticker, concept="Assets")


def get_shares_outstanding(ticker: str) -> Dict[str, Any]:
    """
    Get shares outstanding history from XBRL data.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with shares outstanding data
    """
    for concept in ["CommonStockSharesOutstanding", "EntityCommonStockSharesOutstanding",
                     "SharesOutstanding"]:
        result = get_financial_concept(ticker, concept=concept, taxonomy="dei" if "Entity" in concept else "us-gaap")
        if "error" not in result and result.get("data"):
            return result
    return {"error": f"No shares outstanding data found for {ticker}"}


# ─── Module Info ─────────────────────────────────────────────────────────────

def module_info() -> Dict[str, Any]:
    """Return module metadata."""
    return {
        "name": "secapiio",
        "description": "SEC EDGAR Filings — company info, filings search, XBRL financials, insider trades",
        "source": "SEC EDGAR (data.sec.gov, efts.sec.gov)",
        "api_key_required": False,
        "rate_limit": "10 req/sec (SEC policy)",
        "functions": [
            "ticker_to_cik", "cik_to_ticker", "get_company_info",
            "get_filings", "get_recent_filings", "search_filings",
            "get_company_facts", "get_financial_concept",
            "get_insider_filings", "get_institutional_filings",
            "get_revenue_history", "get_net_income_history",
            "get_eps_history", "get_total_assets", "get_shares_outstanding",
            "module_info",
        ],
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        ticker = sys.argv[2] if len(sys.argv) > 2 else "TSLA"
        if cmd == "info":
            print(json.dumps(get_company_info(ticker), indent=2))
        elif cmd == "filings":
            form = sys.argv[3] if len(sys.argv) > 3 else None
            print(json.dumps(get_filings(ticker, form_type=form, limit=5), indent=2))
        elif cmd == "search":
            print(json.dumps(search_filings(ticker, limit=5), indent=2))
        elif cmd == "revenue":
            print(json.dumps(get_revenue_history(ticker), indent=2))
        elif cmd == "facts":
            print(json.dumps(get_company_facts(ticker), indent=2))
        else:
            print(json.dumps(module_info(), indent=2))
    else:
        print(json.dumps(module_info(), indent=2))

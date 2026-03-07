#!/usr/bin/env python3
"""
SEC EDGAR API v2 — Company Filings & Insider Trading

Access SEC EDGAR filings, company submissions, insider trading (Form 4),
13F institutional holdings, and full-text filing search. All endpoints
are free with no API key required - just proper User-Agent header.

Source: https://www.sec.gov/edgar/api-docs
Category: Government & Regulatory
Free tier: True (no API key needed, just User-Agent)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# SEC EDGAR API Configuration
SEC_DATA_BASE = "https://data.sec.gov"
SEC_SEARCH_BASE = "https://efts.sec.gov/LATEST"
SEC_BROWSE_BASE = "https://www.sec.gov/cgi-bin/browse-edgar"
SEC_USER_AGENT = "QuantClaw/1.0 (quant@moneyclaw.com)"

# Cache for ticker-to-CIK mappings
_TICKER_CIK_CACHE = None
_CACHE_TIMESTAMP = None
_CACHE_TTL = timedelta(hours=24)


def _get_headers() -> Dict[str, str]:
    """
    Get required headers for SEC API requests
    SEC requires User-Agent header per their policy
    """
    return {
        "User-Agent": SEC_USER_AGENT,
        "Accept": "application/json"
    }


def _pad_cik(cik: Union[str, int]) -> str:
    """
    Pad CIK to 10 digits with leading zeros
    SEC API requires CIK in format: CIK0000000000
    
    Args:
        cik: CIK number as string or int
        
    Returns:
        Padded CIK string (10 digits)
    """
    cik_str = str(cik).lstrip('0')
    return cik_str.zfill(10)


def _load_ticker_cik_map() -> Dict[str, int]:
    """
    Load SEC's company tickers JSON file (cached for 24h)
    Maps ticker symbols to CIK numbers
    
    Returns:
        Dict mapping ticker (uppercase) to CIK number
    """
    global _TICKER_CIK_CACHE, _CACHE_TIMESTAMP
    
    # Return cached if still valid
    if _TICKER_CIK_CACHE and _CACHE_TIMESTAMP:
        if datetime.now() - _CACHE_TIMESTAMP < _CACHE_TTL:
            return _TICKER_CIK_CACHE
    
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        response = requests.get(url, headers=_get_headers(), timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Convert to ticker -> CIK mapping
        ticker_map = {}
        for entry in data.values():
            ticker = entry.get('ticker', '').upper()
            cik = entry.get('cik_str')
            if ticker and cik:
                ticker_map[ticker] = cik
        
        _TICKER_CIK_CACHE = ticker_map
        _CACHE_TIMESTAMP = datetime.now()
        
        return ticker_map
    
    except Exception as e:
        # Return empty dict if fetch fails, don't crash
        return {}


def resolve_ticker_to_cik(ticker: str) -> Optional[str]:
    """
    Resolve stock ticker to CIK number
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        
    Returns:
        CIK number as string, or None if not found
    """
    ticker = ticker.upper().strip()
    
    # Check if already a CIK (numeric)
    if ticker.isdigit():
        return _pad_cik(ticker)
    
    # Load ticker map
    ticker_map = _load_ticker_cik_map()
    
    if ticker in ticker_map:
        return _pad_cik(ticker_map[ticker])
    
    return None


def get_company_submissions(ticker_or_cik: str) -> Dict:
    """
    Get company's recent filings and submission history
    
    Args:
        ticker_or_cik: Stock ticker (e.g., 'AAPL') or CIK number
        
    Returns:
        Dict with company info and recent filings list
    """
    try:
        # Resolve to CIK
        if ticker_or_cik.isdigit():
            cik = _pad_cik(ticker_or_cik)
        else:
            cik = resolve_ticker_to_cik(ticker_or_cik)
            if not cik:
                return {
                    "success": False,
                    "error": f"Ticker '{ticker_or_cik}' not found",
                    "ticker": ticker_or_cik
                }
        
        url = f"{SEC_DATA_BASE}/submissions/CIK{cik}.json"
        response = requests.get(url, headers=_get_headers(), timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract company info
        company_info = {
            "cik": data.get("cik"),
            "name": data.get("name"),
            "ticker": data.get("tickers", [None])[0] if data.get("tickers") else None,
            "sic": data.get("sic"),
            "sic_description": data.get("sicDescription"),
            "category": data.get("category"),
            "fiscal_year_end": data.get("fiscalYearEnd"),
            "state_of_incorporation": data.get("stateOfIncorporation"),
            "business_address": data.get("addresses", {}).get("business"),
            "mailing_address": data.get("addresses", {}).get("mailing"),
        }
        
        # Extract recent filings
        filings = data.get("filings", {}).get("recent", {})
        recent_filings = []
        
        if filings and "form" in filings:
            for i in range(min(20, len(filings["form"]))):
                filing = {
                    "form": filings["form"][i],
                    "filing_date": filings["filingDate"][i],
                    "accession_number": filings["accessionNumber"][i],
                    "primary_document": filings.get("primaryDocument", [None] * len(filings["form"]))[i],
                    "primary_doc_description": filings.get("primaryDocDescription", [None] * len(filings["form"]))[i],
                }
                recent_filings.append(filing)
        
        return {
            "success": True,
            "company": company_info,
            "recent_filings": recent_filings,
            "filings_count": len(recent_filings),
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "error": f"Company not found: {ticker_or_cik}",
                "ticker_or_cik": ticker_or_cik
            }
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "ticker_or_cik": ticker_or_cik
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ticker_or_cik": ticker_or_cik
        }


def get_company_facts(ticker_or_cik: str) -> Dict:
    """
    Get company's XBRL financial data (balance sheet, income statement facts)
    
    Args:
        ticker_or_cik: Stock ticker (e.g., 'AAPL') or CIK number
        
    Returns:
        Dict with XBRL financial facts organized by taxonomy
    """
    try:
        # Resolve to CIK
        if ticker_or_cik.isdigit():
            cik = _pad_cik(ticker_or_cik)
        else:
            cik = resolve_ticker_to_cik(ticker_or_cik)
            if not cik:
                return {
                    "success": False,
                    "error": f"Ticker '{ticker_or_cik}' not found",
                    "ticker": ticker_or_cik
                }
        
        url = f"{SEC_DATA_BASE}/api/xbrl/companyfacts/CIK{cik}.json"
        response = requests.get(url, headers=_get_headers(), timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract key facts
        company_info = {
            "cik": data.get("cik"),
            "name": data.get("entityName"),
        }
        
        # Parse facts by taxonomy (us-gaap, dei, etc.)
        facts_summary = {}
        facts_data = data.get("facts", {})
        
        for taxonomy, concepts in facts_data.items():
            facts_summary[taxonomy] = {
                "concepts_count": len(concepts),
                "concepts": list(concepts.keys())[:20]  # First 20 concepts
            }
        
        # Extract some key financial metrics if available
        key_metrics = {}
        us_gaap = facts_data.get("us-gaap", {})
        
        key_concepts = [
            "Assets",
            "Liabilities",
            "StockholdersEquity",
            "Revenues",
            "NetIncomeLoss",
            "EarningsPerShareBasic",
            "EarningsPerShareDiluted",
            "OperatingIncomeLoss",
            "CashAndCashEquivalentsAtCarryingValue",
        ]
        
        for concept in key_concepts:
            if concept in us_gaap:
                units_data = us_gaap[concept].get("units", {})
                # Get USD values if available
                if "USD" in units_data:
                    values = units_data["USD"]
                    if values:
                        latest = max(values, key=lambda x: x.get("end", ""))
                        key_metrics[concept] = {
                            "value": latest.get("val"),
                            "end_date": latest.get("end"),
                            "fiscal_year": latest.get("fy"),
                            "fiscal_period": latest.get("fp"),
                            "form": latest.get("form")
                        }
        
        return {
            "success": True,
            "company": company_info,
            "taxonomies": facts_summary,
            "key_metrics": key_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "error": f"Company facts not found: {ticker_or_cik}",
                "ticker_or_cik": ticker_or_cik
            }
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "ticker_or_cik": ticker_or_cik
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ticker_or_cik": ticker_or_cik
        }


def search_filings(
    query: str,
    form_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    entity: Optional[str] = None
) -> List[Dict]:
    """
    Full-text search of SEC EDGAR filings
    
    Args:
        query: Search keywords
        form_type: Filter by form type (e.g., '10-K', '8-K', '4')
        date_from: Start date YYYY-MM-DD
        date_to: End date YYYY-MM-DD
        entity: Company name or ticker to filter
        
    Returns:
        List of matching filings with metadata
    """
    try:
        # Build query string
        q_parts = [query]
        if form_type:
            q_parts.append(f"form:{form_type}")
        if entity:
            q_parts.append(f"entity:{entity}")
        
        q_string = " AND ".join(q_parts)
        
        params = {
            "q": q_string,
            "dateRange": "custom" if (date_from or date_to) else "all",
        }
        
        if date_from:
            params["startdt"] = date_from
        if date_to:
            params["enddt"] = date_to
        
        url = f"{SEC_SEARCH_BASE}/search-index"
        response = requests.get(url, params=params, headers=_get_headers(), timeout=20)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract hits
        hits = data.get("hits", {}).get("hits", [])
        results = []
        
        for hit in hits[:50]:  # Limit to 50 results
            source = hit.get("_source", {})
            result = {
                "company": source.get("display_names", [""])[0] if source.get("display_names") else None,
                "cik": source.get("ciks", [""])[0] if source.get("ciks") else None,
                "form": source.get("form"),
                "filing_date": source.get("file_date"),
                "file_number": source.get("file_num"),
                "film_number": source.get("film_num"),
                "description": source.get("file_description"),
                "size": source.get("file_size"),
            }
            results.append(result)
        
        return results
    
    except requests.HTTPError as e:
        return []
    except Exception as e:
        return []


def get_insider_trades(ticker: str, limit: int = 50) -> List[Dict]:
    """
    Get insider trading activity (Form 4 filings)
    
    Args:
        ticker: Stock ticker symbol
        limit: Maximum number of trades to return (default 50)
        
    Returns:
        List of recent insider trades from Form 4 filings
    """
    try:
        # Search for Form 4 filings for this ticker
        results = search_filings(
            query=ticker,
            form_type="4",
            date_from=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
            date_to=datetime.now().strftime("%Y-%m-%d")
        )
        
        insider_trades = []
        
        for filing in results[:limit]:
            trade = {
                "company": filing["company"],
                "cik": filing["cik"],
                "filing_date": filing["filing_date"],
                "form": filing["form"],
                "description": filing["description"],
                "file_number": filing["file_number"],
            }
            insider_trades.append(trade)
        
        return insider_trades
    
    except Exception as e:
        return []


def get_recent_filings_by_form(
    form_type: str,
    days_back: int = 7,
    limit: int = 20
) -> List[Dict]:
    """
    Get recent filings of a specific form type
    
    Args:
        form_type: Form type (e.g., '10-K', '8-K', '13F', 'DEF 14A')
        days_back: Number of days to look back (default 7)
        limit: Maximum results to return
        
    Returns:
        List of recent filings matching form type
    """
    date_from = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    date_to = datetime.now().strftime("%Y-%m-%d")
    
    results = search_filings(
        query="*",
        form_type=form_type,
        date_from=date_from,
        date_to=date_to
    )
    
    return results[:limit]


def get_company_overview(ticker_or_cik: str) -> Dict:
    """
    Get comprehensive company overview combining submissions and facts
    
    Args:
        ticker_or_cik: Stock ticker or CIK number
        
    Returns:
        Dict with company profile, recent filings, and key financials
    """
    overview = {
        "ticker_or_cik": ticker_or_cik,
        "timestamp": datetime.now().isoformat()
    }
    
    # Get submissions
    submissions = get_company_submissions(ticker_or_cik)
    if submissions.get("success"):
        overview["company"] = submissions["company"]
        overview["recent_filings"] = submissions["recent_filings"][:5]
    else:
        overview["error"] = submissions.get("error")
        return overview
    
    # Get financial facts
    facts = get_company_facts(ticker_or_cik)
    if facts.get("success"):
        overview["key_financials"] = facts.get("key_metrics", {})
        overview["taxonomies"] = facts.get("taxonomies", {})
    
    return overview


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("SEC EDGAR API v2 - Company Filings & Insider Trading")
    print("=" * 70)
    
    # Test with Apple
    ticker = "AAPL"
    print(f"\n1. Resolving ticker: {ticker}")
    cik = resolve_ticker_to_cik(ticker)
    print(f"   CIK: {cik}")
    
    print(f"\n2. Getting company submissions for {ticker}...")
    submissions = get_company_submissions(ticker)
    if submissions.get("success"):
        print(f"   Company: {submissions['company']['name']}")
        print(f"   Ticker: {submissions['company']['ticker']}")
        print(f"   SIC: {submissions['company']['sic_description']}")
        print(f"   Recent filings: {submissions['filings_count']}")
        if submissions['recent_filings']:
            print(f"\n   Latest filing:")
            latest = submissions['recent_filings'][0]
            print(f"     Form: {latest['form']}")
            print(f"     Date: {latest['filing_date']}")
            print(f"     Description: {latest['primary_doc_description']}")
    else:
        print(f"   Error: {submissions.get('error')}")
    
    print(f"\n3. Getting company facts (XBRL) for {ticker}...")
    facts = get_company_facts(ticker)
    if facts.get("success"):
        print(f"   Company: {facts['company']['name']}")
        print(f"   Taxonomies: {list(facts['taxonomies'].keys())}")
        if facts['key_metrics']:
            print(f"\n   Key Metrics:")
            for concept, data in list(facts['key_metrics'].items())[:3]:
                print(f"     {concept}: {data['value']:,} ({data['end_date']})")
    else:
        print(f"   Error: {facts.get('error')}")
    
    print(f"\n4. Searching for recent 8-K filings...")
    filings = get_recent_filings_by_form("8-K", days_back=3, limit=5)
    print(f"   Found {len(filings)} recent 8-K filings")
    if filings:
        for i, filing in enumerate(filings[:3], 1):
            print(f"\n   {i}. {filing['company']}")
            print(f"      Date: {filing['filing_date']}")
            print(f"      CIK: {filing['cik']}")
    
    print(f"\n5. Checking insider trades for {ticker}...")
    trades = get_insider_trades(ticker, limit=5)
    print(f"   Found {len(trades)} Form 4 filings")
    if trades:
        for i, trade in enumerate(trades[:3], 1):
            print(f"\n   {i}. {trade['company']}")
            print(f"      Date: {trade['filing_date']}")
            print(f"      Description: {trade['description']}")
    
    print("\n" + "=" * 70)
    print("Module: sec_edgar_api_v2.py")
    print("Functions: resolve_ticker_to_cik, get_company_submissions, get_company_facts,")
    print("           search_filings, get_insider_trades, get_recent_filings_by_form,")
    print("           get_company_overview")
    print("=" * 70)

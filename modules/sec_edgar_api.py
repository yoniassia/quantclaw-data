#!/usr/bin/env python3
"""
SEC EDGAR API — free access to company filings, XBRL financials, insider transactions, institutional holdings.
Source: https://www.sec.gov/edgar/sec-api-documentation
Sample endpoint: https://data.sec.gov/submissions/CIK0000000001.json
Category: Earnings & Fundamentals
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from requests.exceptions import RequestException, HTTPError

USER_AGENT = "QuantClaw/1.0 (quant@moneyclaw.com)"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

def get_cik(ticker: str) -> Optional[str]:
    """Retrieve 10-digit CIK for a given ticker symbol."""
    try:
        resp = requests.get(TICKERS_URL, headers={"User-Agent": USER_AGENT}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        ticker_upper = ticker.upper()
        for entry in data.values():
            if isinstance(entry, dict) and entry.get("ticker") == ticker_upper:
                cik = str(entry["cik_str"]).zfill(10)
                time.sleep(0.1)  # Rate limit
                return cik
        return None
    except (RequestException, KeyError, ValueError) as e:
        raise ValueError(f"Failed to fetch CIK for '{ticker}': {str(e)}")

def get_company_submissions(cik: str) -> Dict[str, Any]:
    """Fetch company submissions/filings data."""
    url = SUBMISSIONS_URL.format(cik=cik)
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        resp.raise_for_status()
        time.sleep(0.1)
        return resp.json()
    except RequestException as e:
        raise ValueError(f"Failed to fetch submissions for CIK {cik}: {str(e)}")

def get_company_filings(ticker: str) -> List[Dict[str, Any]]:
    """
    Get recent filings for a company by ticker.
    Returns list of dicts with form, filingDate, reportDate, accessionNumber, primaryDocument.
    """
    cik = get_cik(ticker)
    if not cik:
        return []
    subs = get_company_submissions(cik)
    recent = subs.get("filings", {}).get("recent", {})
    filings = []
    form_list = recent.get("form", [])
    max_len = min(1000, len(form_list))
    acc_list = recent.get("accessionNumber", [])
    filing_date_list = recent.get("filingDate", [])
    report_date_list = recent.get("reportDate", [])
    prim_doc_list = recent.get("primaryDocument", [])
    for i in range(max_len):
        filing = {
            "form": form_list[i],
            "accessionNumber": acc_list[i] if i < len(acc_list) else None,
            "filingDate": filing_date_list[i] if i < len(filing_date_list) else None,
            "primaryDocument": prim_doc_list[i] if i < len(prim_doc_list) else None,
        }
        if i < len(report_date_list):
            filing["reportDate"] = report_date_list[i]
        filings.append(filing)
    return filings[:50]  # Recent 50

def get_insider_transactions(ticker: str) -> List[Dict[str, Any]]:
    """Get recent insider transactions (filter Form 4,3,5)."""
    filings = get_company_filings(ticker)
    insider_forms = {"4", "3", "5"}
    return [f for f in filings if f.get("form", "") in insider_forms][:20]

def get_institutional_holdings(ticker: str) -> List[Dict[str, Any]]:
    """Get recent 13F institutional holdings filings."""
    filings = get_company_filings(ticker)
    holdings_forms = {"13F-HR", "13F-NT", "13F-HR/A", "SC 13G", "SC 13D"}
    return [f for f in filings if f.get("form", "") in holdings_forms][:20]

def get_company_facts(ticker: str) -> Dict[str, List[str]]:
    """Get XBRL company facts structure (keys under us-gaap/dei)."""
    cik = get_cik(ticker)
    if not cik:
        return {}
    url = COMPANYFACTS_URL.format(cik=cik)
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        resp.raise_for_status()
        facts_data = resp.json().get("facts", {})
        time.sleep(0.1)
        return {
            "us_gaap_keys": list(facts_data.get("us-gaap", {}).keys())[:20],
            "dei_keys": list(facts_data.get("dei", {}).keys())[:20]
        }
    except RequestException as e:
        raise ValueError(f"Failed to fetch company facts for '{ticker}' (CIK {cik}): {str(e)}")

def search_filings(query: str) -> List[Dict[str, str]]:
    """Search filings/companies by ticker or company name snippet."""
    try:
        resp = requests.get(TICKERS_URL, headers={"User-Agent": USER_AGENT}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        q_upper = query.upper()
        matches = []
        for entry in data.values():
            if isinstance(entry, dict):
                ticker = entry.get("ticker", "")
                title = entry.get("title", "")
                if q_upper in ticker or q_upper in title:
                    matches.append({
                        "ticker": ticker,
                        "name": title,
                        "cik": str(entry.get("cik_str", "")).zfill(10)
                    })
        time.sleep(0.1)
        return matches[:10]
    except RequestException as e:
        raise ValueError(f"Failed to search filings for '{query}': {str(e)}")

if __name__ == "__main__":
    print(json.dumps({"module": "sec_edgar_api", "status": "ready"}, indent=2))

#!/usr/bin/env python3
"""
SEC EDGAR XBRL API v2 — SEC Filings & Financial Statements
Access structured XBRL financial data from SEC EDGAR filings.
Company facts, specific concepts (Revenue, EPS), CIK lookup, summaries, filing history.

Source: https://www.sec.gov/api/xbrl
Category: Earnings & Fundamentals
Free tier: true - No API key, User-Agent required, 10 req/sec limit.
"""

import requests
import json
import time
from typing import Dict, Optional, List, Any
from pathlib import Path

USER_AGENT = "QuantClaw/1.0 (quantclaw@moneyclaw.com)"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
XBRL_FACTS_BASE = "https://data.sec.gov/api/xbrl/companyfacts"
XBRL_CONCEPT_BASE = "https://data.sec.gov/api/xbrl/companyconcept"
SUBMISSIONS_BASE = "https://data.sec.gov/submissions"

def _make_request(url: str) -> Optional[Dict[str, Any]]:
    """Helper: Make SEC API request with User-Agent and rate limiting."""
    headers = {"User-Agent": USER_AGENT}
    try:
        time.sleep(0.1)  # Respect 10 req/sec limit
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def _get_ticker_info(ticker: str) -> Optional[Dict[str, str]]:
    """Get CIK and name from ticker."""
    data = _make_request(TICKERS_URL)
    if not data:
        return None
    ticker_upper = ticker.upper()
    for _, v in data.items():
        if v.get("ticker", "").upper() == ticker_upper:
            return {"cik": str(v["cik_str"]), "name": v["title"]}
    return None

def resolve_cik(cik_or_ticker: str) -> Optional[str]:
    """Resolve CIK from string (10-digit or ticker)."""
    if len(cik_or_ticker) == 10 and cik_or_ticker.isdigit():
        return cik_or_ticker
    if info := _get_ticker_info(cik_or_ticker):
        return info["cik"]
    return None

def get_company_facts(cik_or_ticker: str) -> Dict[str, Any]:
    """Full company financial facts from XBRL."""
    cik = resolve_cik(cik_or_ticker)
    if not cik:
        return {"success": False, "error": "Invalid CIK or ticker"}
    url = f"{XBRL_FACTS_BASE}/CIK{cik.zfill(10)}.json"
    data = _make_request(url)
    if data:
        return {"success": True, "cik": cik, "entity": data.get("entityData", {}), "facts": data.get("facts", {})}
    return {"success": False, "error": "Failed to fetch facts", "cik": cik}

def get_company_concept(cik_or_ticker: str, taxonomy: str, concept: str) -> Dict[str, Any]:
    """Specific XBRL concept (e.g., 'us-gaap', 'Revenue')."""
    cik = resolve_cik(cik_or_ticker)
    if not cik:
        return {"success": False, "error": "Invalid CIK or ticker"}
    url = f"{XBRL_CONCEPT_BASE}/CIK{cik.zfill(10)}/{taxonomy}/{concept}.json"
    data = _make_request(url)
    if data:
        return {"success": True, "cik": cik, "taxonomy": taxonomy, "concept": concept, "data": data}
    return {"success": False, "error": "Failed to fetch concept", "cik": cik}

def search_company(query: str) -> List[Dict[str, str]]:
    """Search companies by name or ticker, return top 10 CIKs."""
    data = _make_request(TICKERS_URL)
    if not data:
        return []
    q_upper = query.upper()
    results = []
    for _, v in data.items():
        ticker = v.get("ticker", "").upper()
        title = v.get("title", "").upper()
        if q_upper in ticker or q_upper in title:
            results.append({
                "cik": str(v["cik_str"]),
                "ticker": v["ticker"],
                "name": v["title"]
            })
        if len(results) >= 10:
            break
    return results

def get_financials_summary(cik_or_ticker: str) -> Dict[str, Any]:
    """Key financials: Revenue, Net Income, EPS (latest 4 periods)."""
    facts = get_company_facts(cik_or_ticker)
    if not facts.get("success"):
        return facts
    data = facts["facts"]
    summary = {}
    key_concepts = {
        "Revenue": "Revenues",
        "NetIncome": "NetIncomeLoss",
        "EPS": "EarningsPerShareBasic"
    }
    for label, concept in key_concepts.items():
        if "us-gaap" in data and concept in data["us-gaap"]:
            concept_facts = data["us-gaap"][concept].get("facts", {})
            all_facts = []
            for form, fact_list in concept_facts.items():
                all_facts.extend(fact_list)
            # Sort by end date desc, take latest 4
            recent = sorted(all_facts, key=lambda f: f.get("end", ""), reverse=True)[:4]
            summary[label] = [{"period": f.get("end"), "value": f.get("v"), "form": f.get("form"), "accn": f.get("accn")} for f in recent]
    return {"success": True, "cik": facts["cik"], "financials": summary}

def get_filing_history(cik_or_ticker: str, form_type: Optional[str] = None) -> List[Dict[str, str]]:
    """Recent filings, filtered by form_type (e.g., '10-K')."""
    cik = resolve_cik(cik_or_ticker)
    if not cik:
        return []
    url = f"{SUBMISSIONS_BASE}/CIK{cik.zfill(10)}.json"
    data = _make_request(url)
    if not data or "filings" not in data:
        return []
    recent_filings = data["filings"]["recent"]
    forms = recent_filings["form"]
    num_filings = len(forms)
    results = []
    for i in range(num_filings):
        form = forms[i]
        if form_type is None or form == form_type:
            # Safe access to fields
            filing_date = recent_filings.get("filingDate", [""] * num_filings)[i]
            period_key = "periodOfReport" if "periodOfReport" in recent_filings else "reportDate"
            period = recent_filings.get(period_key, [""] * num_filings)[i]
            accession = recent_filings.get("accessionNumber", [""] * num_filings)[i]
            primary_doc = recent_filings.get("primaryDocument", [""] * num_filings)[i]
            results.append({
                "form": form,
                "filedAt": filing_date,
                "period": period,
                "accessionNumber": accession,
                "primaryDocument": primary_doc
            })
        if len(results) >= 50:
            break
    return results

if __name__ == "__main__":
    print(json.dumps({"module": "sec_edgar_xbrl_api_v2", "status": "ready", "functions": ["get_company_facts", "get_company_concept", "search_company", "get_financials_summary", "get_filing_history"]}, indent=2))

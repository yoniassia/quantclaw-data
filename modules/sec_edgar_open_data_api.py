#!/usr/bin/env python3
"""
SEC EDGAR Open Data API — Company Filings & Insider Transactions

The SEC's official open data API provides access to EDGAR filings, including:
- Company submissions and filing history
- Financial facts (XBRL data)
- Insider transactions (Form 4)
- Institutional holdings (13F)
- Real-time filing updates

Source: https://www.sec.gov/edgar/sec-api-documentation
Category: Insider & Institutional
Free tier: True (no API key required, 10 requests/second limit)
Update frequency: Real-time as filings are submitted
Author: QuantClaw Data NightBuilder
"""

import json
import requests
from datetime import datetime
from typing import Dict, List, Optional

# SEC API Configuration
SEC_BASE_URL = "https://data.sec.gov"
SEC_USER_AGENT = "QuantClaw Data quantclaw@moneyclaw.com"  # Required by SEC API

# Common headers required by SEC
SEC_HEADERS = {
    "User-Agent": SEC_USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov"
}


def _make_sec_request(url: str, timeout: int = 15) -> Dict:
    """
    Helper function to make SEC API requests with proper headers
    
    Args:
        url: Full URL to request
        timeout: Request timeout in seconds
    
    Returns:
        Dict with response data or error
    """
    try:
        response = requests.get(url, headers=SEC_HEADERS, timeout=timeout)
        response.raise_for_status()
        return {
            "success": True,
            "data": response.json()
        }
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}"
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"JSON decode error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _format_cik(cik: str) -> str:
    """
    Format CIK to 10-digit zero-padded string
    
    Args:
        cik: CIK number (with or without leading zeros)
    
    Returns:
        10-digit zero-padded CIK string
    """
    # Remove any non-numeric characters
    cik_clean = ''.join(filter(str.isdigit, str(cik)))
    return cik_clean.zfill(10)


def ticker_to_cik(ticker: str) -> Dict:
    """
    Convert stock ticker to CIK number
    Uses SEC's company tickers JSON mapping
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        Dict with CIK, company name, and exchange info
    """
    try:
        # Note: This endpoint is on www.sec.gov, not data.sec.gov
        url = "https://www.sec.gov/files/company_tickers.json"
        response = requests.get(url, headers={"User-Agent": SEC_USER_AGENT}, timeout=15)
        response.raise_for_status()
        result = {
            "success": True,
            "data": response.json()
        }
        
        if not result["success"]:
            return result
        
        tickers_data = result["data"]
        ticker_upper = ticker.upper().strip()
        
        # Search through all companies
        for company_id, company_info in tickers_data.items():
            if company_info.get("ticker", "").upper() == ticker_upper:
                cik = _format_cik(company_info["cik_str"])
                return {
                    "success": True,
                    "ticker": ticker_upper,
                    "cik": cik,
                    "company_name": company_info.get("title", ""),
                    "exchange": company_info.get("exchange", ""),
                    "timestamp": datetime.now().isoformat()
                }
        
        return {
            "success": False,
            "error": f"Ticker '{ticker}' not found in SEC database",
            "ticker": ticker_upper
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ticker": ticker
        }


def search_companies(query: str, limit: int = 20) -> Dict:
    """
    Search for companies by name or ticker
    
    Args:
        query: Search term (company name or ticker)
        limit: Maximum number of results to return
    
    Returns:
        Dict with matching companies and their CIKs
    """
    try:
        # Note: This endpoint is on www.sec.gov, not data.sec.gov
        url = "https://www.sec.gov/files/company_tickers.json"
        response = requests.get(url, headers={"User-Agent": SEC_USER_AGENT}, timeout=15)
        response.raise_for_status()
        result = {
            "success": True,
            "data": response.json()
        }
        
        if not result["success"]:
            return result
        
        tickers_data = result["data"]
        query_lower = query.lower().strip()
        matches = []
        
        for company_id, company_info in tickers_data.items():
            company_name = company_info.get("title", "").lower()
            ticker = company_info.get("ticker", "").lower()
            
            # Match on ticker or company name
            if query_lower in company_name or query_lower in ticker:
                matches.append({
                    "cik": _format_cik(company_info["cik_str"]),
                    "ticker": company_info.get("ticker", ""),
                    "company_name": company_info.get("title", ""),
                    "exchange": company_info.get("exchange", "")
                })
            
            if len(matches) >= limit:
                break
        
        return {
            "success": True,
            "query": query,
            "results": matches,
            "count": len(matches),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


def get_company_submissions(cik: str) -> Dict:
    """
    Get all submissions/filings for a company by CIK
    
    Args:
        cik: Company CIK number (e.g., '0000320193' for Apple)
    
    Returns:
        Dict with company info and recent filings
    """
    try:
        formatted_cik = _format_cik(cik)
        url = f"{SEC_BASE_URL}/submissions/CIK{formatted_cik}.json"
        result = _make_sec_request(url)
        
        if not result["success"]:
            return result
        
        data = result["data"]
        
        # Extract key company information
        company_info = {
            "cik": formatted_cik,
            "name": data.get("name", ""),
            "tickers": data.get("tickers", []),
            "exchanges": data.get("exchanges", []),
            "sic": data.get("sic", ""),
            "sic_description": data.get("sicDescription", ""),
            "category": data.get("category", ""),
            "fiscal_year_end": data.get("fiscalYearEnd", ""),
            "state_of_incorporation": data.get("stateOfIncorporation", ""),
            "addresses": {
                "mailing": data.get("addresses", {}).get("mailing", {}),
                "business": data.get("addresses", {}).get("business", {})
            }
        }
        
        # Extract recent filings
        recent_filings = data.get("filings", {}).get("recent", {})
        filings_list = []
        
        if recent_filings:
            accession_numbers = recent_filings.get("accessionNumber", [])
            filing_dates = recent_filings.get("filingDate", [])
            report_dates = recent_filings.get("reportDate", [])
            forms = recent_filings.get("form", [])
            primary_docs = recent_filings.get("primaryDocument", [])
            
            # Combine into list of filing objects (limit to 50 most recent)
            for i in range(min(50, len(accession_numbers))):
                filings_list.append({
                    "accession_number": accession_numbers[i],
                    "filing_date": filing_dates[i],
                    "report_date": report_dates[i] if i < len(report_dates) else None,
                    "form": forms[i],
                    "primary_document": primary_docs[i] if i < len(primary_docs) else None,
                    "filing_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={formatted_cik}&type={forms[i]}&dateb=&owner=exclude&count=40"
                })
        
        return {
            "success": True,
            "company": company_info,
            "recent_filings": filings_list[:50],
            "total_filings": len(filings_list),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "cik": cik
        }


def get_company_facts(cik: str) -> Dict:
    """
    Get company financial facts (XBRL data) by CIK
    
    Args:
        cik: Company CIK number
    
    Returns:
        Dict with financial facts and metrics
    """
    try:
        formatted_cik = _format_cik(cik)
        url = f"{SEC_BASE_URL}/api/xbrl/companyfacts/CIK{formatted_cik}.json"
        result = _make_sec_request(url)
        
        if not result["success"]:
            return result
        
        data = result["data"]
        
        # Extract company info
        company_info = {
            "cik": formatted_cik,
            "name": data.get("entityName", "")
        }
        
        # Extract facts by taxonomy (US-GAAP, IFRS, DEI, etc.)
        facts_summary = {}
        all_facts = data.get("facts", {})
        
        for taxonomy, facts_data in all_facts.items():
            facts_summary[taxonomy] = {
                "count": len(facts_data),
                "concepts": list(facts_data.keys())[:20]  # First 20 concepts
            }
        
        # Extract key financial metrics if available (US-GAAP)
        key_metrics = {}
        us_gaap = all_facts.get("us-gaap", {})
        
        key_concepts = [
            "Assets", "Liabilities", "StockholdersEquity",
            "Revenues", "NetIncomeLoss", "EarningsPerShareBasic",
            "CashAndCashEquivalentsAtCarryingValue", "LongTermDebt"
        ]
        
        for concept in key_concepts:
            if concept in us_gaap:
                concept_data = us_gaap[concept]
                # Get most recent value
                units = concept_data.get("units", {})
                for unit_type, values in units.items():
                    if values:
                        latest = values[-1]  # Most recent value
                        key_metrics[concept] = {
                            "value": latest.get("val"),
                            "end_date": latest.get("end"),
                            "filed": latest.get("filed"),
                            "form": latest.get("form"),
                            "unit": unit_type
                        }
                        break
        
        return {
            "success": True,
            "company": company_info,
            "facts_summary": facts_summary,
            "key_metrics": key_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "cik": cik
        }


def get_recent_filings(cik: str, form_type: Optional[str] = None, limit: int = 20) -> Dict:
    """
    Get recent filings for a company, optionally filtered by form type
    
    Args:
        cik: Company CIK number
        form_type: Optional form type filter (e.g., '10-K', '10-Q', '8-K', '4')
        limit: Maximum number of filings to return
    
    Returns:
        Dict with filtered recent filings
    """
    try:
        # Get all submissions first
        submissions = get_company_submissions(cik)
        
        if not submissions["success"]:
            return submissions
        
        all_filings = submissions["recent_filings"]
        
        # Filter by form type if specified
        if form_type:
            form_type_upper = form_type.upper().strip()
            filtered_filings = [
                f for f in all_filings 
                if f["form"].upper() == form_type_upper
            ]
        else:
            filtered_filings = all_filings
        
        return {
            "success": True,
            "company_name": submissions["company"]["name"],
            "cik": submissions["company"]["cik"],
            "form_type": form_type if form_type else "ALL",
            "filings": filtered_filings[:limit],
            "count": len(filtered_filings[:limit]),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "cik": cik,
            "form_type": form_type
        }


def get_insider_filings(cik: str, limit: int = 20) -> Dict:
    """
    Get insider transaction filings (Form 3, 4, 5) for a company
    Form 4 = Insider trades (buys/sells)
    Form 3 = Initial beneficial ownership
    Form 5 = Annual statement of changes
    
    Args:
        cik: Company CIK number
        limit: Maximum number of filings to return
    
    Returns:
        Dict with insider transaction filings
    """
    try:
        # Get all submissions
        submissions = get_company_submissions(cik)
        
        if not submissions["success"]:
            return submissions
        
        all_filings = submissions["recent_filings"]
        
        # Filter for insider forms (3, 4, 5)
        insider_forms = ['3', '4', '5']
        insider_filings = [
            f for f in all_filings 
            if f["form"] in insider_forms
        ]
        
        # Categorize by form type
        categorized = {
            "form_3": [],  # Initial ownership
            "form_4": [],  # Transactions (buys/sells)
            "form_5": []   # Annual statements
        }
        
        for filing in insider_filings[:limit]:
            form_num = filing["form"]
            if form_num == "3":
                categorized["form_3"].append(filing)
            elif form_num == "4":
                categorized["form_4"].append(filing)
            elif form_num == "5":
                categorized["form_5"].append(filing)
        
        return {
            "success": True,
            "company_name": submissions["company"]["name"],
            "cik": submissions["company"]["cik"],
            "insider_filings": categorized,
            "total_insider_filings": len(insider_filings),
            "form_4_count": len(categorized["form_4"]),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "cik": cik
        }


def get_latest() -> Dict:
    """
    Get latest market-wide filing activity
    Returns sample of recent filings across all companies
    
    Returns:
        Dict with recent filing activity summary
    """
    try:
        # For demo purposes, get Apple's recent filings as sample
        # In production, you'd want to track multiple companies or use RSS feeds
        sample_cik = "0000320193"  # Apple
        submissions = get_company_submissions(sample_cik)
        
        if not submissions["success"]:
            return {
                "success": True,
                "message": "Latest filings endpoint - sample data",
                "sample_company": "Apple Inc.",
                "recent_filings": []
            }
        
        return {
            "success": True,
            "message": "Latest filings (sample from Apple Inc.)",
            "sample_company": submissions["company"]["name"],
            "recent_filings": submissions["recent_filings"][:10],
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("SEC EDGAR Open Data API - Company Filings & Insider Trades")
    print("=" * 60)
    
    # Example 1: Convert ticker to CIK
    print("\n1. Ticker to CIK (AAPL):")
    result = ticker_to_cik("AAPL")
    print(json.dumps(result, indent=2))
    
    # Example 2: Get company submissions
    if result["success"]:
        cik = result["cik"]
        print(f"\n2. Company Submissions (CIK {cik}):")
        submissions = get_company_submissions(cik)
        print(json.dumps({
            "success": submissions["success"],
            "company_name": submissions.get("company", {}).get("name"),
            "total_filings": submissions.get("total_filings"),
            "recent_filings_sample": submissions.get("recent_filings", [])[:3]
        }, indent=2))
        
        # Example 3: Get insider filings
        print(f"\n3. Insider Filings (Form 4 - Trades):")
        insider = get_insider_filings(cik, limit=5)
        print(json.dumps({
            "success": insider["success"],
            "form_4_count": insider.get("form_4_count"),
            "recent_form_4": insider.get("insider_filings", {}).get("form_4", [])[:2]
        }, indent=2))

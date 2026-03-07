"""
Nasdaq Data Link 13F Dataset — Institutional Holdings via SEC EDGAR

Data Source: SEC EDGAR 13F Filings (Free API)
Update: Quarterly (45 days after quarter end)
History: 2013-present via SEC API
Free: Yes (SEC public API, no key required)

Provides:
- Institutional holdings by CIK/name
- Top holders for any stock symbol
- Portfolio changes quarter-over-quarter
- Institution search and lookup

13F Filing Rules:
- Filed by institutions managing >$100M in securities
- Reports long positions only (no shorts)
- Filed within 45 days of quarter end
- Positions as of last day of quarter

Usage:
- Track smart money (hedge funds, pension funds)
- Identify accumulation/distribution patterns
- Monitor institutional sentiment by stock
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import re

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/13f")
os.makedirs(CACHE_DIR, exist_ok=True)

# SEC API endpoints
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_COMPANY_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"

# SEC requires User-Agent per their policy
HEADERS = {
    "User-Agent": "QuantClaw quantclaw@example.com",
    "Accept": "application/json"
}

def normalize_cik(cik: str) -> str:
    """Convert CIK to 10-digit zero-padded format required by SEC API"""
    cik_digits = re.sub(r'\D', '', str(cik))
    return cik_digits.zfill(10)

def search_institutions(query: str) -> List[Dict]:
    """
    Search for institutions by name using SEC EDGAR company search.
    
    Args:
        query: Institution name (e.g., "berkshire", "blackrock")
    
    Returns:
        List of matching institutions with CIK and name
    """
    cache_file = os.path.join(CACHE_DIR, f"search_{query.lower().replace(' ', '_')}.json")
    
    # Check cache (refresh monthly)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=30):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        params = {
            "q": query,
            "from": 0,
            "size": 20
        }
        
        response = requests.get(
            SEC_COMPANY_SEARCH_URL,
            params=params,
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        results = []
        seen_ciks = set()
        
        for hit in hits:
            source = hit.get("_source", {})
            
            # Extract CIK and name
            ciks = source.get("ciks", [])
            display_names = source.get("display_names", [])
            
            if ciks and display_names:
                cik = normalize_cik(ciks[0])
                # Parse name from display format: "COMPANY NAME (TICKER) (CIK 0001234567)"
                raw_name = display_names[0]
                # Extract company name before first parenthesis
                name = raw_name.split("(")[0].strip()
                
                # Deduplicate by CIK
                if cik not in seen_ciks and name:
                    seen_ciks.add(cik)
                    results.append({
                        "cik": cik,
                        "name": name,
                        "type": "Institution"
                    })
        
        # Cache results
        with open(cache_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        return results
        
    except Exception as e:
        print(f"❌ Error searching institutions: {e}")
        return []

def get_cik_from_name(name: str) -> Optional[str]:
    """Helper: Get CIK from institution name"""
    results = search_institutions(name)
    if results:
        return results[0]["cik"]
    return None

def get_institution_info(cik_or_name: str) -> Dict:
    """
    Get institution basic info and recent filings.
    
    Args:
        cik_or_name: CIK number or institution name
    
    Returns:
        Dict with institution details and filings
    """
    # If name provided, resolve to CIK
    if not cik_or_name.isdigit():
        cik = get_cik_from_name(cik_or_name)
        if not cik:
            return {"error": f"Institution not found: {cik_or_name}"}
    else:
        cik = normalize_cik(cik_or_name)
    
    cache_file = os.path.join(CACHE_DIR, f"institution_{cik}.json")
    
    # Check cache (refresh weekly)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=7):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        url = SEC_SUBMISSIONS_URL.format(cik=cik)
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract 13F filings
        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        filing_dates = filings.get("filingDate", [])
        accession_numbers = filings.get("accessionNumber", [])
        
        f13_filings = []
        for i, form in enumerate(forms):
            if "13F" in form:
                f13_filings.append({
                    "form": form,
                    "filing_date": filing_dates[i],
                    "accession_number": accession_numbers[i],
                    "period_of_report": filings.get("reportDate", [""])[i]
                })
        
        result = {
            "cik": cik,
            "name": data.get("name", ""),
            "filing_count_13f": len(f13_filings),
            "latest_13f_filing": f13_filings[0] if f13_filings else None,
            "recent_13f_filings": f13_filings[:4],  # Last 4 quarters
            "retrieved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
        
    except Exception as e:
        print(f"❌ Error fetching institution info: {e}")
        return {"error": str(e), "cik": cik}

def get_13f_holdings(cik_or_name: str) -> Dict:
    """
    Get institutional holdings from latest 13F filing.
    
    Args:
        cik_or_name: CIK number or institution name
    
    Returns:
        Dict with holdings data from most recent 13F
    """
    info = get_institution_info(cik_or_name)
    
    if "error" in info:
        return info
    
    if not info.get("latest_13f_filing"):
        return {
            "cik": info["cik"],
            "name": info["name"],
            "error": "No 13F filings found"
        }
    
    latest = info["latest_13f_filing"]
    
    return {
        "cik": info["cik"],
        "institution": info["name"],
        "filing_date": latest["filing_date"],
        "period_ending": latest["period_of_report"],
        "form": latest["form"],
        "note": "Detailed holdings require parsing XML/HTML from SEC EDGAR filing. Use accession_number to fetch full filing.",
        "accession_number": latest["accession_number"],
        "filing_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={info['cik']}&type=13F&dateb=&owner=exclude&count=10"
    }

def get_portfolio_changes(cik_or_name: str, quarters: int = 2) -> Dict:
    """
    Analyze portfolio changes over recent quarters.
    
    Args:
        cik_or_name: CIK number or institution name
        quarters: Number of recent quarters to analyze
    
    Returns:
        Dict with quarter-over-quarter filing comparison
    """
    info = get_institution_info(cik_or_name)
    
    if "error" in info:
        return info
    
    recent_filings = info.get("recent_13f_filings", [])[:quarters]
    
    if len(recent_filings) < 2:
        return {
            "cik": info["cik"],
            "institution": info["name"],
            "error": f"Need at least 2 filings for comparison, found {len(recent_filings)}"
        }
    
    return {
        "cik": info["cik"],
        "institution": info["name"],
        "quarters_analyzed": len(recent_filings),
        "filings": recent_filings,
        "note": "Full position-level changes require parsing individual 13F XML filings from SEC EDGAR",
        "analysis_url": f"https://whalewisdom.com/filer/{info['name'].lower().replace(' ', '-')}#tabholdings_tab_link"
    }

def get_top_holders(symbol: str) -> Dict:
    """
    Get top institutional holders for a stock symbol.
    
    Args:
        symbol: Stock ticker (e.g., "AAPL")
    
    Returns:
        Dict with top institutional holders
    
    Note: This requires cross-referencing 13F filings with stock holdings.
          For production use, consider using:
          - WhaleWisdom API
          - Financial Datasets API (institutionalHolders endpoint)
          - Nasdaq Data Link premium tier
    """
    
    # This is a placeholder - full implementation requires:
    # 1. Search all 13F filers
    # 2. Download and parse each 13F XML
    # 3. Extract positions matching the symbol
    # 4. Aggregate and rank by shares/value
    
    return {
        "symbol": symbol.upper(),
        "note": "Top holders by stock requires parsing all 13F filings (computationally intensive)",
        "alternative_sources": [
            "WhaleWisdom API (free tier available)",
            "Financial Datasets API - /institutionalHolders endpoint",
            "Nasdaq Data Link premium tier",
            "Yahoo Finance holders page (scraping)"
        ],
        "example_manual_lookup": f"https://whalewisdom.com/stock/{symbol.lower()}",
        "sec_search": f"https://www.sec.gov/cgi-bin/browse-edgar?company={symbol}&type=13F&dateb=&owner=exclude&action=getcompany"
    }

# === CLI Commands ===

def cli_search(query: str):
    """Search for institutions"""
    results = search_institutions(query)
    
    print(f"\n🔍 Institution Search: '{query}'")
    print("=" * 70)
    
    if not results:
        print("No results found")
        return
    
    print(f"Found {len(results)} institutions:\n")
    for i, inst in enumerate(results[:10], 1):
        print(f"{i}. {inst['name']}")
        print(f"   CIK: {inst['cik']}")
        print()

def cli_info(cik_or_name: str):
    """Show institution info and recent filings"""
    info = get_institution_info(cik_or_name)
    
    if "error" in info:
        print(f"❌ {info['error']}")
        return
    
    print(f"\n🏦 {info['name']}")
    print("=" * 70)
    print(f"CIK: {info['cik']}")
    print(f"Total 13F Filings: {info['filing_count_13f']}")
    
    if info.get("latest_13f_filing"):
        latest = info["latest_13f_filing"]
        print(f"\n📊 Latest Filing:")
        print(f"   Form: {latest['form']}")
        print(f"   Filed: {latest['filing_date']}")
        print(f"   Period: {latest['period_of_report']}")
    
    print(f"\n📁 Recent 13F Filings:")
    for filing in info.get("recent_13f_filings", [])[:4]:
        print(f"   • {filing['filing_date']} — {filing['form']} (Period: {filing['period_of_report']})")

def cli_holdings(cik_or_name: str):
    """Show latest 13F holdings"""
    holdings = get_13f_holdings(cik_or_name)
    
    if "error" in holdings:
        print(f"❌ {holdings['error']}")
        return
    
    print(f"\n📊 Latest 13F Holdings")
    print("=" * 70)
    print(f"Institution: {holdings['institution']}")
    print(f"Filing Date: {holdings['filing_date']}")
    print(f"Period Ending: {holdings['period_ending']}")
    print(f"\n{holdings['note']}")
    print(f"\nView full filing: {holdings['filing_url']}")

def cli_changes(cik_or_name: str, quarters: int = 2):
    """Show portfolio changes"""
    changes = get_portfolio_changes(cik_or_name, quarters)
    
    if "error" in changes:
        print(f"❌ {changes['error']}")
        return
    
    print(f"\n📈 Portfolio Changes — {changes['institution']}")
    print("=" * 70)
    print(f"Quarters Analyzed: {changes['quarters_analyzed']}\n")
    
    for i, filing in enumerate(changes.get("filings", []), 1):
        print(f"Q{i}: {filing['filing_date']} — Period: {filing['period_of_report']}")
    
    print(f"\n{changes['note']}")

def cli_top_holders(symbol: str):
    """Show top holders for a stock"""
    holders = get_top_holders(symbol)
    
    print(f"\n🏆 Top Institutional Holders: {holders['symbol']}")
    print("=" * 70)
    print(f"{holders['note']}\n")
    
    print("Alternative Data Sources:")
    for source in holders.get("alternative_sources", []):
        print(f"  • {source}")
    
    print(f"\nManual lookup: {holders['example_manual_lookup']}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "search" and len(sys.argv) > 2:
            cli_search(sys.argv[2])
        elif command == "info" and len(sys.argv) > 2:
            cli_info(sys.argv[2])
        elif command == "holdings" and len(sys.argv) > 2:
            cli_holdings(sys.argv[2])
        elif command == "changes" and len(sys.argv) > 2:
            quarters = int(sys.argv[3]) if len(sys.argv) > 3 else 2
            cli_changes(sys.argv[2], quarters)
        elif command == "holders" and len(sys.argv) > 2:
            cli_top_holders(sys.argv[2])
        else:
            print("Usage: python nasdaq_data_link_13f_dataset.py <command> <args>")
            print("\nCommands:")
            print("  search <query>         - Search institutions")
            print("  info <cik_or_name>     - Show institution info")
            print("  holdings <cik_or_name> - Show latest 13F holdings")
            print("  changes <cik_or_name> [quarters] - Show portfolio changes")
            print("  holders <symbol>       - Show top holders for stock")
    else:
        # Demo
        cli_search("berkshire")

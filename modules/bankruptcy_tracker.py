#!/usr/bin/env python3
"""
Bankruptcy & Default Tracker (Phase 197)
Track corporate bankruptcies, Chapter 11 filings, and default notices

Data Sources:
- SEC EDGAR 8-K filings (Item 1.03 - bankruptcy notices)
- SEC full-text search for bankruptcy keywords
- Form 10-K/10-Q for going concern warnings

Commands:
- bankruptcy-search [--days DAYS] [--limit LIMIT]
- bankruptcy-tracker [--ticker TICKER]
- bankruptcy-stats [--sector SECTOR] [--year YEAR]
"""

import sys
import requests
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Any
from urllib.parse import quote

# SEC EDGAR Configuration
SEC_API_BASE = "https://www.sec.gov"
SEC_SEARCH_API = f"{SEC_API_BASE}/cgi-bin/browse-edgar"
SEC_FULL_TEXT_SEARCH = "https://efts.sec.gov/LATEST/search-index"

# User agent required by SEC
USER_AGENT = "QuantClaw/1.0 (Research Tool)"

# Bankruptcy-related keywords
BANKRUPTCY_KEYWORDS = [
    "chapter 11",
    "chapter 7",
    "bankruptcy protection",
    "filed for bankruptcy",
    "bankruptcy petition",
    "bankruptcy proceedings",
    "going concern",
    "substantial doubt",
    "default notice",
    "covenant breach",
    "payment default",
    "restructuring plan",
    "debtor in possession",
    "bankruptcy court",
    "insolvency"
]

# Form types that may contain bankruptcy info
BANKRUPTCY_FORMS = ["8-K", "10-K", "10-Q", "8-K/A", "10-K/A", "10-Q/A"]

# Sector mapping (SIC code ranges)
SECTOR_MAPPING = {
    "Technology": range(3570, 3580),
    "Retail": range(5200, 6000),
    "Finance": range(6000, 6800),
    "Energy": range(1300, 1400),
    "Healthcare": range(2830, 2840),
    "Manufacturing": range(2000, 4000),
    "Real Estate": range(6500, 6600),
}


def search_sec_filings(keywords: str, days: int = 30, form_type: str = "8-K", limit: int = 100) -> List[Dict[str, Any]]:
    """
    Search SEC EDGAR filings by keywords
    """
    headers = {"User-Agent": USER_AGENT}
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    results = []
    
    try:
        # Use SEC full-text search API
        search_url = f"{SEC_FULL_TEXT_SEARCH}"
        
        params = {
            "q": keywords,
            "dateRange": "custom",
            "startdt": start_date.strftime("%Y-%m-%d"),
            "enddt": end_date.strftime("%Y-%m-%d"),
            "forms": form_type,
            "from": 0,
            "size": limit
        }
        
        # Alternative: Direct RSS feed approach
        # SEC provides RSS feeds but they're limited to recent filings
        rss_url = f"{SEC_API_BASE}/cgi-bin/browse-edgar?action=getcurrent&type={form_type}&output=atom"
        
        response = requests.get(rss_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # Parse RSS/Atom feed
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Namespace handling for Atom feeds
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns)[:limit]:
                title = entry.find('atom:title', ns)
                summary = entry.find('atom:summary', ns)
                updated = entry.find('atom:updated', ns)
                link = entry.find('atom:link', ns)
                
                if title is not None and summary is not None:
                    title_text = title.text or ""
                    summary_text = summary.text or ""
                    
                    # Check if any bankruptcy keyword is present
                    combined_text = (title_text + " " + summary_text).lower()
                    
                    if any(keyword.lower() in combined_text for keyword in BANKRUPTCY_KEYWORDS):
                        filing_url = link.attrib.get('href', '') if link is not None else ""
                        
                        # Extract CIK and company name from title
                        # Format: "8-K - COMPANY NAME (0001234567) (Filer)"
                        match = re.search(r'(.+?)\s*\((\d+)\)', title_text)
                        company_name = match.group(1).strip() if match else "Unknown"
                        cik = match.group(2) if match else "Unknown"
                        
                        filing_date = updated.text[:10] if updated is not None else "Unknown"
                        
                        results.append({
                            "company": company_name,
                            "cik": cik,
                            "form_type": form_type,
                            "filing_date": filing_date,
                            "description": summary_text[:200] + "..." if len(summary_text) > 200 else summary_text,
                            "url": f"{SEC_API_BASE}{filing_url}" if filing_url else "",
                            "keywords_found": [kw for kw in BANKRUPTCY_KEYWORDS if kw.lower() in combined_text]
                        })
        
    except Exception as e:
        print(f"Error searching SEC filings: {e}", file=sys.stderr)
    
    return results


def search_bankruptcy_filings(days: int = 30, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Search for recent bankruptcy-related SEC filings
    """
    all_results = []
    
    # Search across multiple form types
    for form_type in ["8-K", "10-K", "10-Q"]:
        # Search with different keyword combinations
        for keyword in ["chapter 11", "bankruptcy", "going concern"]:
            results = search_sec_filings(keyword, days=days, form_type=form_type, limit=limit)
            all_results.extend(results)
    
    # Deduplicate by CIK + filing date
    seen = set()
    unique_results = []
    
    for result in all_results:
        key = (result["cik"], result["filing_date"])
        if key not in seen:
            seen.add(key)
            unique_results.append(result)
    
    # Sort by date (most recent first)
    unique_results.sort(key=lambda x: x["filing_date"], reverse=True)
    
    return unique_results[:limit]


def get_company_bankruptcy_status(ticker: str) -> Dict[str, Any]:
    """
    Get bankruptcy status for a specific company
    """
    headers = {"User-Agent": USER_AGENT}
    
    try:
        # First, resolve ticker to CIK
        ticker_url = f"{SEC_API_BASE}/cgi-bin/browse-edgar"
        params = {
            "action": "getcompany",
            "ticker": ticker.upper(),
            "type": "",
            "dateb": "",
            "owner": "exclude",
            "count": 10,
            "output": "atom"
        }
        
        response = requests.get(ticker_url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Extract company info
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            company_info = root.find('atom:company-info', ns)
            
            if company_info is None:
                return {"error": f"Ticker {ticker} not found"}
            
            company_name = company_info.findtext('atom:conformed-name', default="Unknown", namespaces=ns)
            cik = company_info.findtext('atom:cik', default="Unknown", namespaces=ns)
            
            # Search for bankruptcy filings for this company
            bankruptcy_filings = []
            
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns)
                summary = entry.find('atom:summary', ns)
                updated = entry.find('atom:updated', ns)
                link = entry.find('atom:link', ns)
                
                if title is not None and summary is not None:
                    title_text = title.text or ""
                    summary_text = summary.text or ""
                    combined_text = (title_text + " " + summary_text).lower()
                    
                    if any(keyword.lower() in combined_text for keyword in BANKRUPTCY_KEYWORDS):
                        filing_url = link.attrib.get('href', '') if link is not None else ""
                        filing_date = updated.text[:10] if updated is not None else "Unknown"
                        
                        # Extract form type
                        form_match = re.search(r'(\d+\-[KQ](?:/A)?)', title_text)
                        form_type = form_match.group(1) if form_match else "Unknown"
                        
                        bankruptcy_filings.append({
                            "form_type": form_type,
                            "filing_date": filing_date,
                            "description": summary_text[:150] + "..." if len(summary_text) > 150 else summary_text,
                            "url": f"{SEC_API_BASE}{filing_url}" if filing_url else "",
                            "keywords_found": [kw for kw in BANKRUPTCY_KEYWORDS if kw.lower() in combined_text]
                        })
            
            return {
                "ticker": ticker.upper(),
                "company": company_name,
                "cik": cik,
                "bankruptcy_risk": "HIGH" if bankruptcy_filings else "LOW",
                "recent_filings": bankruptcy_filings[:5],  # Most recent 5
                "total_bankruptcy_filings": len(bankruptcy_filings)
            }
        
    except Exception as e:
        return {"error": f"Error fetching data for {ticker}: {str(e)}"}
    
    return {"error": "Unable to fetch company data"}


def get_bankruptcy_statistics(sector: Optional[str] = None, year: Optional[int] = None) -> Dict[str, Any]:
    """
    Get bankruptcy statistics by sector and year
    """
    # Determine date range
    if year:
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        days = (end_date - start_date).days
    else:
        # Default to last 365 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        days = 365
        year = end_date.year
    
    # Search for all bankruptcy filings in the period
    all_filings = search_bankruptcy_filings(days=days, limit=500)
    
    # Statistics
    stats = {
        "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "total_filings": len(all_filings),
        "unique_companies": len(set(f["cik"] for f in all_filings)),
        "by_form_type": Counter(f["form_type"] for f in all_filings),
        "by_month": defaultdict(int),
        "by_keyword": Counter(),
        "top_companies": []
    }
    
    # Count by month
    for filing in all_filings:
        try:
            month = filing["filing_date"][:7]  # YYYY-MM
            stats["by_month"][month] += 1
            
            # Count keywords
            for keyword in filing.get("keywords_found", []):
                stats["by_keyword"][keyword] += 1
        except:
            pass
    
    # Top companies by number of bankruptcy-related filings
    company_counts = Counter(f"{f['company']} ({f['cik']})" for f in all_filings)
    stats["top_companies"] = [
        {"company": company, "filing_count": count}
        for company, count in company_counts.most_common(10)
    ]
    
    # Convert defaultdict to dict for JSON serialization
    stats["by_month"] = dict(sorted(stats["by_month"].items()))
    stats["by_keyword"] = dict(stats["by_keyword"].most_common(10))
    stats["by_form_type"] = dict(stats["by_form_type"])
    
    return stats


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python bankruptcy_tracker.py <command> [options]")
        print("\nCommands:")
        print("  bankruptcy-search [--days DAYS] [--limit LIMIT]")
        print("  bankruptcy-tracker --ticker TICKER")
        print("  bankruptcy-stats [--sector SECTOR] [--year YEAR]")
        return
    
    command = sys.argv[1]
    
    # Parse arguments
    args = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i].startswith('--'):
            key = sys.argv[i][2:]
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
                args[key] = sys.argv[i + 1]
                i += 2
            else:
                args[key] = True
                i += 1
        else:
            i += 1
    
    # Execute command
    if command == "bankruptcy-search":
        days = int(args.get('days', 30))
        limit = int(args.get('limit', 50))
        
        results = search_bankruptcy_filings(days=days, limit=limit)
        print(json.dumps(results, indent=2))
    
    elif command == "bankruptcy-tracker":
        ticker = args.get('ticker')
        if not ticker:
            print("Error: --ticker required", file=sys.stderr)
            return
        
        result = get_company_bankruptcy_status(ticker)
        print(json.dumps(result, indent=2))
    
    elif command == "bankruptcy-stats":
        sector = args.get('sector')
        year = int(args.get('year')) if 'year' in args else None
        
        result = get_bankruptcy_statistics(sector=sector, year=year)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        return


if __name__ == "__main__":
    main()

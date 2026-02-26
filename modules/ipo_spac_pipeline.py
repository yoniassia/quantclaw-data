"""
IPO & SPAC Pipeline Tracker — Module #215

Tracks upcoming IPOs, recent listings, and SPAC lifecycle events using
free SEC EDGAR data and public filing feeds. Monitors S-1/F-1 filings,
SPAC merger votes, redemption rates, and de-SPAC performance.
"""

import json
import datetime
import urllib.request
from typing import Dict, List, Optional


SEC_EDGAR_BASE = "https://efts.sec.gov/LATEST"
SEC_FULL_TEXT = "https://efts.sec.gov/LATEST/search-index"
HEADERS = {"User-Agent": "QuantClaw/1.0 quant@moneyclaw.com"}


def search_sec_filings(
    form_type: str = "S-1",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 20,
) -> List[Dict]:
    """
    Search SEC EDGAR for IPO-related filings (S-1, S-1/A, F-1, SPAC S-4).
    
    Args:
        form_type: SEC form type to search (S-1, F-1, S-4, 424B4, etc.)
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        query: Optional text search within filings
        limit: Max results to return
        
    Returns:
        List of filing dicts with company, date, form type, URL.
    """
    params = [f"forms={form_type}"]
    if date_from:
        params.append(f"dateRange=custom&startdt={date_from}")
    if date_to:
        params.append(f"enddt={date_to}")
    if query:
        params.append(f"q={urllib.request.quote(query)}")
    
    url = f"{SEC_EDGAR_BASE}/search-index?{'&'.join(params)}&from=0&size={limit}"
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            hits = data.get("hits", {}).get("hits", [])
            results = []
            for hit in hits:
                src = hit.get("_source", {})
                results.append({
                    "company": src.get("entity_name", "Unknown"),
                    "cik": src.get("entity_id"),
                    "form_type": src.get("form_type", form_type),
                    "filed_date": src.get("file_date"),
                    "description": src.get("file_description", ""),
                    "url": f"https://www.sec.gov/Archives/edgar/data/{src.get('entity_id', '')}/{src.get('adsh', '').replace('-', '')}",
                })
            return results
    except Exception as e:
        return [{"error": str(e)}]


def get_recent_ipos(days: int = 30) -> List[Dict]:
    """
    Fetch recent IPO filings from SEC EDGAR (S-1 and F-1 forms).
    
    Args:
        days: Look back this many days.
        
    Returns:
        List of recent IPO filing dicts.
    """
    date_from = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    s1_filings = search_sec_filings("S-1", date_from=date_from)
    f1_filings = search_sec_filings("F-1", date_from=date_from)
    
    all_filings = s1_filings + f1_filings
    all_filings.sort(key=lambda x: x.get("filed_date", ""), reverse=True)
    return all_filings


def get_spac_filings(days: int = 30) -> List[Dict]:
    """
    Search for SPAC-related SEC filings (S-4 merger proxies, DEFM14A).
    
    Args:
        days: Look back this many days.
        
    Returns:
        List of SPAC merger filing dicts.
    """
    date_from = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    s4 = search_sec_filings("S-4", date_from=date_from, query="SPAC OR blank check")
    proxy = search_sec_filings("DEFM14A", date_from=date_from, query="business combination")
    
    all_filings = s4 + proxy
    all_filings.sort(key=lambda x: x.get("filed_date", ""), reverse=True)
    return all_filings


def calculate_spac_metrics(
    trust_value: float,
    share_price: float,
    shares_outstanding: float,
    redemption_rate: float = 0.0,
) -> Dict:
    """
    Calculate key SPAC valuation metrics.
    
    Args:
        trust_value: Total cash in trust (millions).
        share_price: Current trading price per share.
        shares_outstanding: Total shares outstanding (millions).
        redemption_rate: Expected/actual redemption rate (0-1).
        
    Returns:
        Dict with trust per share, premium/discount, implied valuation.
    """
    trust_per_share = trust_value / shares_outstanding if shares_outstanding else 0
    premium_discount = ((share_price / trust_per_share) - 1) * 100 if trust_per_share else 0
    remaining_trust = trust_value * (1 - redemption_rate)
    
    return {
        "trust_value_mm": trust_value,
        "trust_per_share": round(trust_per_share, 2),
        "share_price": share_price,
        "premium_discount_pct": round(premium_discount, 2),
        "redemption_rate_pct": round(redemption_rate * 100, 2),
        "remaining_trust_mm": round(remaining_trust, 2),
        "market_cap_mm": round(share_price * shares_outstanding, 2),
    }


def ipo_pipeline_summary() -> Dict:
    """
    Generate a summary of the current IPO and SPAC pipeline.
    
    Returns:
        Dict with counts and recent filings for IPOs and SPACs.
    """
    recent_ipos = get_recent_ipos(30)
    recent_spacs = get_spac_filings(30)
    
    return {
        "as_of": datetime.datetime.now().isoformat(),
        "ipo_filings_30d": len([f for f in recent_ipos if "error" not in f]),
        "spac_filings_30d": len([f for f in recent_spacs if "error" not in f]),
        "recent_ipos": recent_ipos[:10],
        "recent_spacs": recent_spacs[:10],
        "note": "Data sourced from SEC EDGAR full-text search",
    }

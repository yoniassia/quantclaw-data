"""
SEC EDGAR Company Facts API — XBRL Financial Statement Data

Data Source: U.S. Securities and Exchange Commission
Update: Real-time as filings are submitted
History: All public company filings (10-K, 10-Q, 8-K)
Free: Yes (no API key required, polite crawling expected)

Provides:
- Complete XBRL financial facts for any public company
- Historical data across all fiscal periods
- Quarterly and annual financial statements
- Assets, liabilities, equity, revenue, expenses, etc.
- Data from 10-K, 10-Q regulatory filings

Usage:
- get_company_facts(cik) → All financial facts for a company
- get_company_concept(cik, concept) → Specific metric over time
- Common concepts: Assets, Liabilities, Revenue, NetIncomeLoss, etc.

SEC Policy: Must set User-Agent header identifying requester
"""

import requests
from typing import Dict, List, Optional
import json
import time

# SEC requires User-Agent header
USER_AGENT = "QuantClaw Data quantclaw@moneyclaw.com"
BASE_URL = "https://data.sec.gov/api/xbrl"

# Rate limiting: SEC requests polite crawling (max 10 requests/second)
REQUEST_DELAY = 0.11  # 110ms between requests


def _make_sec_request(url: str) -> Dict:
    """
    Make SEC API request with required User-Agent header.
    Implements polite rate limiting.
    
    Args:
        url: Full API endpoint URL
        
    Returns:
        Parsed JSON response
        
    Raises:
        requests.HTTPError: On API errors
    """
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/json'
    }
    
    time.sleep(REQUEST_DELAY)  # Polite rate limiting
    
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    
    return response.json()


def normalize_cik(cik: str) -> str:
    """
    Normalize CIK to 10-digit zero-padded format.
    
    Args:
        cik: CIK as string or integer (e.g., "320193" or "0000320193")
        
    Returns:
        10-digit zero-padded CIK string
    """
    # Remove CIK prefix if present
    cik_str = str(cik).upper().replace('CIK', '')
    # Pad to 10 digits
    return cik_str.zfill(10)


def get_company_facts(cik: str) -> Dict:
    """
    Get all XBRL financial facts for a company.
    
    Returns complete set of financial data from all filings,
    including balance sheet, income statement, cash flow, etc.
    
    Args:
        cik: Company CIK number (e.g., "0000320193" for Apple)
        
    Returns:
        Dict with structure:
        {
            "cik": "0000320193",
            "entityName": "Apple Inc.",
            "facts": {
                "us-gaap": {
                    "Assets": {...},
                    "Liabilities": {...},
                    "Revenue": {...},
                    ...
                },
                "dei": {...}  # Document and Entity Information
            }
        }
        
    Example:
        >>> facts = get_company_facts("0000320193")
        >>> facts["entityName"]
        "Apple Inc."
        >>> revenue = facts["facts"]["us-gaap"]["Revenues"]
    """
    cik_normalized = normalize_cik(cik)
    url = f"{BASE_URL}/companyfacts/CIK{cik_normalized}.json"
    
    try:
        data = _make_sec_request(url)
        return data
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            raise ValueError(f"Company with CIK {cik_normalized} not found")
        raise


def get_company_concept(cik: str, taxonomy: str, concept: str) -> Dict:
    """
    Get a specific financial concept for a company across all periods.
    
    Args:
        cik: Company CIK number
        taxonomy: Taxonomy (usually "us-gaap" for US GAAP)
        concept: Concept tag (e.g., "Assets", "Revenue", "NetIncomeLoss")
        
    Returns:
        Dict with structure:
        {
            "cik": "0000320193",
            "taxonomy": "us-gaap",
            "tag": "Assets",
            "label": "Assets",
            "description": "Sum of carrying amounts...",
            "entityName": "Apple Inc.",
            "units": {
                "USD": [
                    {"end": "2023-09-30", "val": 352755000000, "form": "10-K", ...},
                    {"end": "2022-09-24", "val": 352583000000, "form": "10-K", ...},
                    ...
                ]
            }
        }
        
    Example:
        >>> assets = get_company_concept("0000320193", "us-gaap", "Assets")
        >>> latest = assets["units"]["USD"][0]
        >>> print(f"Latest assets: ${latest['val']:,.0f}")
    """
    cik_normalized = normalize_cik(cik)
    url = f"{BASE_URL}/companyconcept/CIK{cik_normalized}/{taxonomy}/{concept}.json"
    
    try:
        data = _make_sec_request(url)
        return data
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            raise ValueError(f"Concept {taxonomy}:{concept} not found for CIK {cik_normalized}")
        raise


def get_latest_value(cik: str, taxonomy: str, concept: str, unit: str = "USD") -> Optional[Dict]:
    """
    Get the most recent value for a specific financial concept.
    
    Args:
        cik: Company CIK number
        taxonomy: Taxonomy (usually "us-gaap")
        concept: Concept tag (e.g., "Assets", "Revenue")
        unit: Unit of measurement (default: "USD")
        
    Returns:
        Dict with latest value:
        {
            "value": 352755000000,
            "end_date": "2023-09-30",
            "filed": "2023-11-03",
            "form": "10-K",
            "fiscal_year": 2023,
            "fiscal_period": "FY"
        }
        
    Example:
        >>> latest_assets = get_latest_value("0000320193", "us-gaap", "Assets")
        >>> print(f"Latest assets: ${latest_assets['value']:,.0f}")
    """
    data = get_company_concept(cik, taxonomy, concept)
    
    if unit not in data.get("units", {}):
        return None
    
    values = data["units"][unit]
    
    if not values:
        return None
    
    # Sort by filed date (most recent first)
    sorted_values = sorted(values, key=lambda x: x.get("filed", ""), reverse=True)
    latest = sorted_values[0]
    
    return {
        "value": latest.get("val"),
        "end_date": latest.get("end"),
        "filed": latest.get("filed"),
        "form": latest.get("form"),
        "fiscal_year": latest.get("fy"),
        "fiscal_period": latest.get("fp"),
        "accn": latest.get("accn")  # Accession number
    }


def get_annual_values(cik: str, taxonomy: str, concept: str, unit: str = "USD", limit: int = 10) -> List[Dict]:
    """
    Get annual (10-K) values for a financial concept.
    
    Args:
        cik: Company CIK number
        taxonomy: Taxonomy (usually "us-gaap")
        concept: Concept tag
        unit: Unit of measurement (default: "USD")
        limit: Max number of years to return
        
    Returns:
        List of dicts, most recent first:
        [
            {"value": 352755000000, "end_date": "2023-09-30", "fiscal_year": 2023, ...},
            {"value": 352583000000, "end_date": "2022-09-24", "fiscal_year": 2022, ...},
            ...
        ]
        
    Example:
        >>> revenue_history = get_annual_values("0000320193", "us-gaap", "Revenues", limit=5)
        >>> for year in revenue_history:
        >>>     print(f"{year['fiscal_year']}: ${year['value']:,.0f}")
    """
    data = get_company_concept(cik, taxonomy, concept)
    
    if unit not in data.get("units", {}):
        return []
    
    values = data["units"][unit]
    
    # Filter for annual reports (10-K) only
    annual = [v for v in values if v.get("form") == "10-K" and v.get("fp") == "FY"]
    
    # Sort by fiscal year descending
    sorted_annual = sorted(annual, key=lambda x: x.get("fy", 0), reverse=True)
    
    results = []
    for item in sorted_annual[:limit]:
        results.append({
            "value": item.get("val"),
            "end_date": item.get("end"),
            "filed": item.get("filed"),
            "form": item.get("form"),
            "fiscal_year": item.get("fy"),
            "fiscal_period": item.get("fp"),
            "accn": item.get("accn")
        })
    
    return results


def get_quarterly_values(cik: str, taxonomy: str, concept: str, unit: str = "USD", limit: int = 8) -> List[Dict]:
    """
    Get quarterly (10-Q) values for a financial concept.
    
    Args:
        cik: Company CIK number
        taxonomy: Taxonomy (usually "us-gaap")
        concept: Concept tag
        unit: Unit of measurement (default: "USD")
        limit: Max number of quarters to return
        
    Returns:
        List of dicts, most recent first
        
    Example:
        >>> quarterly_revenue = get_quarterly_values("0000320193", "us-gaap", "Revenues", limit=4)
    """
    data = get_company_concept(cik, taxonomy, concept)
    
    if unit not in data.get("units", {}):
        return []
    
    values = data["units"][unit]
    
    # Filter for quarterly reports (10-Q)
    quarterly = [v for v in values if v.get("form") == "10-Q"]
    
    # Sort by filed date descending
    sorted_quarterly = sorted(quarterly, key=lambda x: x.get("filed", ""), reverse=True)
    
    results = []
    for item in sorted_quarterly[:limit]:
        results.append({
            "value": item.get("val"),
            "end_date": item.get("end"),
            "filed": item.get("filed"),
            "form": item.get("form"),
            "fiscal_year": item.get("fy"),
            "fiscal_period": item.get("fp"),
            "accn": item.get("accn")
        })
    
    return results


# Common US-GAAP concepts for quick access
COMMON_CONCEPTS = {
    "assets": "Assets",
    "liabilities": "Liabilities",
    "equity": "StockholdersEquity",
    "revenue": "Revenues",
    "net_income": "NetIncomeLoss",
    "cash": "Cash",
    "debt": "LongTermDebt",
    "operating_income": "OperatingIncomeLoss",
    "gross_profit": "GrossProfit",
    "eps_basic": "EarningsPerShareBasic",
    "eps_diluted": "EarningsPerShareDiluted"
}


if __name__ == "__main__":
    # Example: Apple Inc. (CIK 0000320193)
    print("SEC EDGAR Company Facts API - Example Usage\n")
    
    cik = "0000320193"  # Apple
    
    # Get company info
    facts = get_company_facts(cik)
    print(f"Company: {facts['entityName']}")
    print(f"CIK: {facts['cik']}\n")
    
    # Get latest assets
    latest_assets = get_latest_value(cik, "us-gaap", "Assets")
    if latest_assets:
        print(f"Latest Assets: ${latest_assets['value']:,.0f}")
        print(f"As of: {latest_assets['end_date']}")
        print(f"Form: {latest_assets['form']}\n")
    
    # Get revenue history
    revenue_history = get_annual_values(cik, "us-gaap", "Revenues", limit=3)
    print("Annual Revenue (last 3 years):")
    for year in revenue_history:
        print(f"  FY{year['fiscal_year']}: ${year['value']:,.0f} ({year['end_date']})")

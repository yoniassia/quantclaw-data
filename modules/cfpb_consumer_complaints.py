#!/usr/bin/env python3
"""
CFPB Consumer Complaints Module

Access the Consumer Financial Protection Bureau complaint database.
Provides insights into consumer sentiment, company complaint patterns,
and financial product issues — useful as alternative data for financial
institution risk assessment.

Data Source: consumerfinance.gov/data-research/consumer-complaints
API: Open, no authentication required
Refresh: Daily
Coverage: 5M+ complaints since 2011, all US financial institutions

Author: QUANTCLAW DATA NightBuilder
Built: 2026-03-06
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter

BASE_URL = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1"


def _search(params: Dict) -> Dict:
    """Make a search request to CFPB API."""
    try:
        resp = requests.get(f"{BASE_URL}/", params=params, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response"}


def search_complaints(
    company: Optional[str] = None,
    product: Optional[str] = None,
    issue: Optional[str] = None,
    state: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    size: int = 10
) -> Dict:
    """Search consumer complaints with filters.

    Args:
        company: Company name (e.g., 'Bank of America', 'JPMorgan Chase')
        product: Product type (e.g., 'Credit card', 'Mortgage')
        issue: Issue keyword
        state: US state abbreviation (e.g., 'CA', 'NY')
        date_from: Start date YYYY-MM-DD
        date_to: End date YYYY-MM-DD
        size: Number of results (max 100)

    Returns dict with total hits and complaint records.
    """
    params = {"size": min(size, 100), "sort": "created_date_desc"}
    if company:
        params["search_term"] = company
    if product:
        params["product"] = product
    if issue:
        params["search_term"] = issue
    if state:
        params["state"] = state
    if date_from:
        params["date_received_min"] = date_from
    if date_to:
        params["date_received_max"] = date_to

    result = _search(params)
    if "error" in result:
        return result

    hits = result.get("hits", {})
    total = hits.get("total", {}).get("value", 0)
    complaints = []
    for hit in hits.get("hits", []):
        src = hit.get("_source", {})
        complaints.append({
            "date_received": src.get("date_received"),
            "product": src.get("product"),
            "sub_product": src.get("sub_product"),
            "issue": src.get("issue"),
            "sub_issue": src.get("sub_issue"),
            "company": src.get("company"),
            "state": src.get("state"),
            "company_response": src.get("company_response"),
            "timely_response": src.get("timely"),
            "consumer_disputed": src.get("consumer_disputed"),
            "complaint_id": src.get("complaint_id"),
        })

    return {"total": total, "returned": len(complaints), "complaints": complaints}


def get_company_complaint_count(company: str, days: int = 90) -> Dict:
    """Get total complaint count for a company over recent period.

    Args:
        company: Company name
        days: Lookback period in days

    Returns dict with total complaints and breakdown by product.
    """
    date_from = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    params = {
        "search_term": company,
        "date_received_min": date_from,
        "size": 0,
    }
    result = _search(params)
    if "error" in result:
        return result

    total = result.get("hits", {}).get("total", {}).get("value", 0)

    # Get product breakdown via aggregation
    params["size"] = 100
    detail_result = _search(params)
    products = Counter()
    if "hits" in detail_result:
        for hit in detail_result.get("hits", {}).get("hits", []):
            prod = hit.get("_source", {}).get("product", "Unknown")
            products[prod] += 1

    return {
        "search_term": company,
        "period_days": days,
        "total_complaints": total,
        "product_breakdown": dict(products.most_common(10)),
        "date_from": date_from,
        "timestamp": datetime.utcnow().isoformat()
    }


def compare_companies(companies: List[str], days: int = 90) -> List[Dict]:
    """Compare complaint volumes across multiple companies.

    Args:
        companies: List of company names
        days: Lookback period

    Returns sorted list of companies with complaint counts.
    """
    results = []
    for company in companies:
        data = get_company_complaint_count(company, days)
        if "error" not in data:
            results.append(data)
    results.sort(key=lambda x: x.get("total_complaints", 0), reverse=True)
    return results


def get_product_trends(product: str, months: int = 6) -> List[Dict]:
    """Get monthly complaint trends for a product category.

    Args:
        product: Product name (e.g., 'Mortgage', 'Credit card')
        months: Number of months to look back

    Returns list of monthly complaint counts.
    """
    trends = []
    now = datetime.utcnow()
    for i in range(months):
        month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1)

        params = {
            "product": product,
            "date_received_min": month_start.strftime("%Y-%m-%d"),
            "date_received_max": month_end.strftime("%Y-%m-%d"),
            "size": 0
        }
        result = _search(params)
        total = result.get("hits", {}).get("total", {}).get("value", 0) if "error" not in result else 0
        trends.append({
            "month": month_start.strftime("%Y-%m"),
            "complaints": total
        })

    trends.reverse()
    return trends


def get_state_hotspots(product: Optional[str] = None, days: int = 30) -> List[Dict]:
    """Get states with most complaints (potential regulatory risk signals).

    Args:
        product: Optional product filter
        days: Lookback period

    Returns top 10 states by complaint volume.
    """
    date_from = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    params = {
        "date_received_min": date_from,
        "size": 100,
    }
    if product:
        params["product"] = product

    result = _search(params)
    if "error" in result:
        return [result]

    states = Counter()
    for hit in result.get("hits", {}).get("hits", []):
        state = hit.get("_source", {}).get("state", "Unknown")
        if state:
            states[state] += 1

    return [{"state": s, "complaints": c} for s, c in states.most_common(10)]


def get_bank_risk_score(company: str) -> Dict:
    """Calculate a simple complaint-based risk indicator for a financial institution.

    Higher score = more complaint activity relative to baseline.
    Useful as alternative data signal for bank stocks.

    Args:
        company: Company name (e.g., 'Wells Fargo', 'Citibank')
    """
    recent = get_company_complaint_count(company, days=30)
    baseline = get_company_complaint_count(company, days=365)

    if "error" in recent or "error" in baseline:
        return {"error": "Could not calculate risk score", $"company": company}

    recent_count = recent.get("total_complaints", 0)
    baseline_count = baseline.get("total_complaints", 0)
    monthly_avg = baseline_count / 12 if baseline_count > 0 else 1

    ratio = recent_count / monthly_avg if monthly_avg > 0 else 0

    if ratio > 2.0:
        risk_level = "HIGH"
    elif ratio > 1.3:
        risk_level = "ELEVATED"
    elif ratio > 0.7:
        risk_level = "NORMAL"
    else:
        risk_level = "LOW"

    return {
        "search_term": company,
        "recent_30d": recent_count,
        "monthly_avg_12m": round(monthly_avg, 1),
        "ratio": round(ratio, 2),
        "risk_level": risk_level,
        "top_products": recent.get("product_breakdown", {}),
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    print("=== CFPB Consumer Complaints Module ===")
    result = search_complaints(company="Bank of America", size=2)
    print(f"Total complaints: {result.get('total', 'N/A')}")
    if result.get("complaints"):
        print(f"Latest: {result['complaints'][0].get('product')} - {result['complaints'][0].get('issue')}")

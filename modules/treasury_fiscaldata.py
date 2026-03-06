#!/usr/bin/env python3
"""
Treasury FiscalData API — Federal Financial Data & Sovereign Debt Analytics

Data Sources:
- Public Debt: Total public debt outstanding (v2 API)
- Exchange Rates: Treasury reporting rates for foreign currency conversion (v1 API)
- Revenue Collections: Federal tax receipts and revenue by source (v1 API)
- Operating Cash: Daily government cash balance (v1 API)
- Interest Rates: Average interest rates on Treasury securities (v2 API)

Source: https://fiscaldata.treasury.gov/api-documentation
Category: Government & Regulatory
Free tier: Fully free with no rate limits
Update frequency: Daily

Author: NightBuilder
Phase: DevClaw Auto-Build
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

BASE_URL_V1 = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1"
BASE_URL_V2 = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2"


def get_public_debt(lookback_days: int = 365) -> Dict:
    """
    Get total public debt outstanding to the penny (V2 API)
    
    Returns:
        Dict with debt figures, composition, and latest summary
    """
    try:
        url = f"{BASE_URL_V2}/accounting/od/debt_to_penny"
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        
        params = {
            "page[size]": 100,
            "filter": f"record_date:gte:{start_date}",
            "sort": "-record_date"
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        records = data.get("data", [])
        
        if not records:
            return {"success": False, "error": "No data returned"}
        
        latest = records[0]
        
        # Find record from ~365 days ago for YoY calc
        year_ago = None
        target_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        for record in records:
            if record["record_date"] <= target_date:
                year_ago = record
                break
        
        result = {
            "success": True,
            "data": records,
            "latest_date": latest.get("record_date"),
            "total_debt_usd": float(latest.get("tot_pub_debt_out_amt", 0)),
            "public_debt_usd": float(latest.get("debt_held_public_amt", 0)),
            "intragovernmental_usd": float(latest.get("intragov_hold_amt", 0)),
            "source": "treasury.gov/fiscaldata"
        }
        
        if year_ago:
            result["yoy_change_usd"] = result["total_debt_usd"] - float(year_ago.get("tot_pub_debt_out_amt", 0))
            result["yoy_change_pct"] = (result["yoy_change_usd"] / float(year_ago.get("tot_pub_debt_out_amt", 1))) * 100
        
        return result
    
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def get_exchange_rates(record_date: Optional[str] = None) -> Dict:
    """
    Get Treasury reporting exchange rates for foreign currencies (V1 API)
    
    Args:
        record_date: Date in YYYY-MM-DD format (defaults to 2024-09-30)
    
    Returns:
        Dict with exchange rates by currency
    """
    try:
        url = f"{BASE_URL_V1}/accounting/od/rates_of_exchange"
        
        if record_date is None:
            record_date = "2024-09-30"  # Known good quarter end
        
        params = {
            "filter": f"record_date:eq:{record_date}",
            "page[size]": 200
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "data": data.get("data", []),
            "record_date": record_date,
            "source": "treasury.gov/fiscaldata"
        }
    
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def get_revenue_collections(fiscal_year: Optional[int] = None) -> Dict:
    """
    Get federal revenue collections by source (MTS Table 5, V1 API)
    
    Args:
        fiscal_year: Fiscal year (defaults to current)
    
    Returns:
        Dict with revenue data by classification
    """
    try:
        url = f"{BASE_URL_V1}/accounting/mts/mts_table_5"
        
        if fiscal_year is None:
            fiscal_year = datetime.now().year
        
        params = {
            "filter": f"record_fiscal_year:eq:{fiscal_year}",
            "page[size]": 200,
            "sort": "-record_date"
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "data": data.get("data", []),
            "fiscal_year": fiscal_year,
            "source": "treasury.gov/fiscaldata"
        }
    
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def get_operating_cash_balance(lookback_days: int = 90) -> Dict:
    """
    Get daily U.S. government operating cash balance (V1 API)
    
    Returns:
        Dict with operating cash levels
    """
    try:
        url = f"{BASE_URL_V1}/accounting/dts/operating_cash_balance"
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        
        params = {
            "filter": f"record_date:gte:{start_date}",
            "page[size]": 100,
            "sort": "-record_date"
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "data": data.get("data", []),
            "source": "treasury.gov/fiscaldata"
        }
    
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def get_avg_interest_rates(lookback_days: int = 90) -> Dict:
    """
    Get average interest rates on U.S. Treasury securities (V2 API)
    
    Returns:
        Dict with treasury rates by security type
    """
    try:
        url = f"{BASE_URL_V2}/accounting/od/avg_interest_rates"
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        
        params = {
            "filter": f"record_date:gte:{start_date}",
            "page[size]": 200,
            "sort": "-record_date"
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "data": data.get("data", []),
            "source": "treasury.gov/fiscaldata"
        }
    
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def get_debt_summary() -> Dict:
    """
    Get comprehensive debt summary with latest figures
    Convenience wrapper around get_public_debt
    
    Returns:
        Dict with debt metrics and YoY growth
    """
    return get_public_debt(lookback_days=400)


# CLI test
if __name__ == "__main__":
    print("Treasury FiscalData API Module Test\n")
    
    # Test 1: Public Debt Summary
    print("=== Public Debt Summary ===")
    debt = get_debt_summary()
    if debt.get("success"):
        print(f"Date: {debt['latest_date']}")
        print(f"Total Debt: ${debt['total_debt_usd']:,.0f}")
        if 'yoy_change_usd' in debt:
            print(f"YoY Change: ${debt['yoy_change_usd']:,.0f} ({debt['yoy_change_pct']:.2f}%)")
    else:
        print(f"Error: {debt.get('error')}")
    
    # Test 2: Exchange Rates
    print("\n=== Exchange Rates (Sept 2024) ===")
    fx = get_exchange_rates()
    if fx["success"] and fx["data"]:
        for record in fx["data"][:5]:
            print(f"{record['country_currency_desc']}: {record['exchange_rate']}")
    
    # Test 3: Operating Cash
    print("\n=== Operating Cash Balance (Last 3 Days) ===")
    cash = get_operating_cash_balance(lookback_days=7)
    if cash["success"] and cash["data"]:
        for record in cash["data"][:3]:
            bal = record.get('close_today_bal')
            if bal and bal != 'null':
                print(f"{record['record_date']}: ${float(bal):,.0f}")
    
    # Test 4: Avg Interest Rates
    print("\n=== Recent Treasury Interest Rates ===")
    rates = get_avg_interest_rates(lookback_days=7)
    if rates["success"] and rates["data"]:
        for record in rates["data"][:5]:
            print(f"{record['record_date']}: {record.get('security_desc', 'Unknown')} = {record.get('avg_interest_rate_amt', 'N/A')}%")
    
    print("\n✅ Module test complete")

"""
U.S. Treasury Fiscal Data API Module

Source: fiscaldata.treasury.gov
Category: Government Finance
Frequency: Daily, Monthly
Description: Official U.S. government financial data including debt, revenue, 
             spending, interest rates, and Treasury operations.
API: fiscaldata.treasury.gov/api-documentation/ - No authentication required
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import json

# API Configuration
FISCAL_DATA_BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

# Major datasets
DATASETS = {
    "debt_to_penny": "v2/accounting/od/debt_to_penny",
    "avg_interest_rates": "v2/accounting/od/avg_interest_rates",
    "daily_treasury_statement": "v1/accounting/dts/dts_table_1",
    "monthly_treasury_statement": "v1/accounting/mts/mts_table_5",
    "treasury_offset_program": "v1/debt/top/top_federal",
    "gift_contributions": "v2/accounting/od/gift_contributions",
    "gold_reserve": "v1/accounting/od/gold_reserve",
    "schedule_d": "v1/accounting/od/schedule_d",
    "slgs_statistics": "v2/accounting/od/slgs_statistics",
}


def get_national_debt(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 1
) -> Dict:
    """
    Get U.S. national debt (Debt to the Penny).
    
    Args:
        start_date: Start date YYYY-MM-DD (default: latest)
        end_date: End date YYYY-MM-DD (default: today)
        limit: Number of records to return (default: 1 for latest)
        
    Returns:
        {
            "success": True,
            "date": "2026-03-07",
            "total_debt": 35234567890123.45,
            "public_debt": 28456789012345.67,
            "intragovernmental_debt": 6777778877777.78,
            "records": [...]
        }
    """
    try:
        url = f"{FISCAL_DATA_BASE}/{DATASETS['debt_to_penny']}"
        
        params = {
            "sort": "-record_date",
            "page[size]": limit,
            "fields": "record_date,tot_pub_debt_out_amt,intragov_hold_amt,debt_held_public_amt"
        }
        
        if start_date:
            params["filter"] = f"record_date:gte:{start_date}"
        if end_date:
            if "filter" in params:
                params["filter"] += f",record_date:lte:{end_date}"
            else:
                params["filter"] = f"record_date:lte:{end_date}"
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("data"):
            return {"success": False, "error": "No debt data available"}
        
        records = data["data"]
        latest = records[0]
        
        return {
            "success": True,
            "date": latest.get("record_date"),
            "total_debt": float(latest.get("tot_pub_debt_out_amt", 0)),
            "public_debt": float(latest.get("debt_held_public_amt", 0)),
            "intragovernmental_debt": float(latest.get("intragov_hold_amt", 0)),
            "records": records,
            "count": len(records),
            "source": "U.S. Treasury Fiscal Data API"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching national debt: {str(e)}"
        }


def get_treasury_interest_rates(
    security_type: Optional[str] = None,
    limit: int = 100
) -> Dict:
    """
    Get average interest rates on U.S. Treasury securities.
    
    Args:
        security_type: Filter by security type (e.g., "Treasury Bills", "Treasury Notes")
        limit: Number of records to return
        
    Returns:
        {
            "success": True,
            "date": "2026-02-28",
            "rates": [{
                "security_type": "Treasury Bills",
                "security_desc": "3-Month",
                "avg_interest_rate": 5.23,
                "record_date": "2026-02-28"
            }, ...]
        }
    """
    try:
        url = f"{FISCAL_DATA_BASE}/{DATASETS['avg_interest_rates']}"
        
        params = {
            "sort": "-record_date",
            "page[size]": limit
        }
        
        if security_type:
            params["filter"] = f"security_type_desc:eq:{security_type}"
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("data"):
            return {"success": False, "error": "No interest rate data available"}
        
        records = data["data"]
        
        # Parse and format rates
        rates = []
        for record in records:
            rates.append({
                "security_type": record.get("security_type_desc"),
                "security_desc": record.get("security_desc"),
                "avg_interest_rate": float(record.get("avg_interest_rate_amt", 0)),
                "record_date": record.get("record_date")
            })
        
        return {
            "success": True,
            "date": records[0].get("record_date") if records else None,
            "rates": rates,
            "count": len(rates),
            "source": "U.S. Treasury Fiscal Data API"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching interest rates: {str(e)}"
        }


def get_daily_treasury_statement(
    table_name: str = "dts_table_1",
    record_date: Optional[str] = None,
    limit: int = 10
) -> Dict:
    """
    Get Daily Treasury Statement data (receipts, outlays, deficit/surplus).
    
    Args:
        table_name: DTS table name (default: dts_table_1 - Operating Cash Balance)
        record_date: Specific date YYYY-MM-DD (optional)
        limit: Number of records
        
    Returns:
        {
            "success": True,
            "data": [...],
            "summary": {...}
        }
    """
    try:
        url = f"{FISCAL_DATA_BASE}/v1/accounting/dts/{table_name}"
        
        params = {
            "sort": "-record_date",
            "page[size]": limit
        }
        
        if record_date:
            params["filter"] = f"record_date:eq:{record_date}"
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("data"):
            return {"success": False, "error": "No DTS data available"}
        
        records = data["data"]
        
        return {
            "success": True,
            "table": table_name,
            "data": records,
            "count": len(records),
            "source": "U.S. Treasury Daily Treasury Statement"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching DTS: {str(e)}"
        }


def get_monthly_treasury_statement(
    fiscal_year: Optional[int] = None,
    fiscal_month: Optional[int] = None,
    limit: int = 12
) -> Dict:
    """
    Get Monthly Treasury Statement (revenue and outlays by category).
    
    Args:
        fiscal_year: Fiscal year (e.g., 2026)
        fiscal_month: Fiscal month (1-12)
        limit: Number of records
        
    Returns:
        {
            "success": True,
            "data": [...],
            "summary": {...}
        }
    """
    try:
        url = f"{FISCAL_DATA_BASE}/{DATASETS['monthly_treasury_statement']}"
        
        params = {
            "sort": "-record_date",
            "page[size]": limit
        }
        
        filters = []
        if fiscal_year:
            filters.append(f"record_fiscal_year:eq:{fiscal_year}")
        if fiscal_month:
            filters.append(f"record_fiscal_month:eq:{fiscal_month}")
        
        if filters:
            params["filter"] = ",".join(filters)
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("data"):
            return {"success": False, "error": "No MTS data available"}
        
        records = data["data"]
        
        return {
            "success": True,
            "data": records,
            "count": len(records),
            "source": "U.S. Treasury Monthly Treasury Statement"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching MTS: {str(e)}"
        }


def get_treasury_offset_program(
    fiscal_year: Optional[int] = None,
    limit: int = 100
) -> Dict:
    """
    Get Treasury Offset Program data (federal debt collection).
    
    Args:
        fiscal_year: Fiscal year (optional)
        limit: Number of records
        
    Returns:
        {
            "success": True,
            "data": [...],
            "total_offsets": 12345678.90
        }
    """
    try:
        url = f"{FISCAL_DATA_BASE}/{DATASETS['treasury_offset_program']}"
        
        params = {
            "sort": "-reporting_date",
            "page[size]": limit
        }
        
        if fiscal_year:
            params["filter"] = f"reporting_fiscal_year:eq:{fiscal_year}"
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("data"):
            return {"success": False, "error": "No TOP data available"}
        
        records = data["data"]
        
        # Calculate total offsets
        total_offsets = sum(
            float(r.get("total_offset_amt", 0)) 
            for r in records 
            if r.get("total_offset_amt")
        )
        
        return {
            "success": True,
            "data": records,
            "total_offsets": total_offsets,
            "count": len(records),
            "source": "U.S. Treasury Offset Program"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching TOP data: {str(e)}"
        }


def get_gift_contributions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
) -> Dict:
    """
    Get gift contributions to reduce debt held by the public.
    
    Args:
        start_date: Start date YYYY-MM-DD
        end_date: End date YYYY-MM-DD
        limit: Number of records
        
    Returns:
        {
            "success": True,
            "total_contributions": 12345.67,
            "data": [...]
        }
    """
    try:
        url = f"{FISCAL_DATA_BASE}/{DATASETS['gift_contributions']}"
        
        params = {
            "sort": "-record_date",
            "page[size]": limit
        }
        
        filters = []
        if start_date:
            filters.append(f"record_date:gte:{start_date}")
        if end_date:
            filters.append(f"record_date:lte:{end_date}")
        
        if filters:
            params["filter"] = ",".join(filters)
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("data"):
            return {"success": False, "error": "No gift contribution data available"}
        
        records = data["data"]
        
        # Calculate total contributions
        total = sum(
            float(r.get("gift_contrib_curr_month_amt", 0)) 
            for r in records 
            if r.get("gift_contrib_curr_month_amt")
        )
        
        return {
            "success": True,
            "total_contributions": total,
            "data": records,
            "count": len(records),
            "source": "U.S. Treasury Gift Contributions"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching gift contributions: {str(e)}"
        }


def get_gold_reserve(limit: int = 10) -> Dict:
    """
    Get U.S. gold reserve holdings and value.
    
    Args:
        limit: Number of records
        
    Returns:
        {
            "success": True,
            "date": "2026-02-28",
            "fine_troy_ounces": 261498926.24,
            "book_value": 11041051546.75,
            "data": [...]
        }
    """
    try:
        url = f"{FISCAL_DATA_BASE}/{DATASETS['gold_reserve']}"
        
        params = {
            "sort": "-record_date",
            "page[size]": limit
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("data"):
            return {"success": False, "error": "No gold reserve data available"}
        
        records = data["data"]
        latest = records[0]
        
        return {
            "success": True,
            "date": latest.get("record_date"),
            "fine_troy_ounces": float(latest.get("fine_troy_ounces", 0)),
            "book_value": float(latest.get("book_value_amt", 0)),
            "data": records,
            "count": len(records),
            "source": "U.S. Treasury Gold Reserve"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching gold reserve: {str(e)}"
        }


def get_fiscal_summary(fiscal_year: Optional[int] = None) -> Dict:
    """
    Get comprehensive fiscal summary (debt, revenue, spending).
    
    Args:
        fiscal_year: Fiscal year (default: current)
        
    Returns:
        {
            "success": True,
            "fiscal_year": 2026,
            "debt": {...},
            "revenue": {...},
            "spending": {...}
        }
    """
    try:
        if not fiscal_year:
            # Current fiscal year (Oct 1 - Sep 30)
            now = datetime.now()
            fiscal_year = now.year if now.month >= 10 else now.year - 1
        
        # Get debt
        debt_data = get_national_debt(limit=1)
        
        # Get monthly statement for revenue/spending
        mts_data = get_monthly_treasury_statement(fiscal_year=fiscal_year)
        
        summary = {
            "success": True,
            "fiscal_year": fiscal_year,
            "debt": debt_data if debt_data.get("success") else None,
            "monthly_statement": mts_data if mts_data.get("success") else None,
            "source": "U.S. Treasury Fiscal Data API"
        }
        
        return summary
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching fiscal summary: {str(e)}"
        }


def search_datasets(query: str = "") -> Dict:
    """
    Search available Treasury datasets.
    
    Args:
        query: Search query (optional)
        
    Returns:
        {
            "success": True,
            "datasets": {...}
        }
    """
    try:
        filtered = {}
        
        for name, endpoint in DATASETS.items():
            if not query or query.lower() in name.lower():
                filtered[name] = {
                    "endpoint": endpoint,
                    "url": f"{FISCAL_DATA_BASE}/{endpoint}"
                }
        
        return {
            "success": True,
            "datasets": filtered,
            "count": len(filtered),
            "source": "U.S. Treasury Fiscal Data API"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error searching datasets: {str(e)}"
        }


# Convenience exports
__all__ = [
    "get_national_debt",
    "get_treasury_interest_rates",
    "get_daily_treasury_statement",
    "get_monthly_treasury_statement",
    "get_treasury_offset_program",
    "get_gift_contributions",
    "get_gold_reserve",
    "get_fiscal_summary",
    "search_datasets"
]

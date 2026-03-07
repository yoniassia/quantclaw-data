"""
FiscalData Treasury API — U.S. Treasury Financial Data

Data Source: U.S. Department of the Treasury
Update: Daily (most datasets)
History: Varies by dataset (some go back to 1790s)
Free: Yes (no API key required)

Provides:
- Federal debt (total public debt outstanding)
- Daily Treasury Statement (revenue, spending, operating cash)
- Treasury yields and interest rates
- Exchange rates
- Federal account balances
- Revenue and spending by category

API Documentation: https://fiscaldata.treasury.gov/api-documentation/

Key Datasets:
- Debt to the Penny (daily total debt)
- Daily Treasury Statement (cash flow)
- Average Interest Rates
- Treasury Reporting Rates of Exchange
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/fiscaldata")
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make request to FiscalData API with error handling.
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        
    Returns:
        Parsed JSON response
    """
    url = f"{BASE_URL}/{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "endpoint": endpoint}

def get_total_debt(limit: int = 10) -> Dict:
    """
    Get total U.S. public debt outstanding (Debt to the Penny).
    Updated daily.
    
    Args:
        limit: Number of records to return (default 10)
        
    Returns:
        Dict with data and metadata
    """
    endpoint = "v2/accounting/od/debt_to_penny"
    params = {
        "sort": "-record_date",
        "page[size]": limit
    }
    
    result = _make_request(endpoint, params)
    
    if "error" not in result and "data" in result:
        # Parse and format
        formatted_data = []
        for record in result.get("data", []):
            formatted_data.append({
                "date": record.get("record_date"),
                "total_debt": float(record.get("tot_pub_debt_out_amt", 0)),
                "debt_held_public": float(record.get("debt_held_public_amt", 0)),
                "intragovt_holdings": float(record.get("intragov_hold_amt", 0))
            })
        
        return {
            "data": formatted_data,
            "source": "Treasury Debt to the Penny",
            "updated": datetime.now().isoformat()
        }
    
    return result

def get_latest_debt() -> Dict:
    """
    Get the most recent total U.S. public debt figure.
    
    Returns:
        Dict with latest debt data
    """
    result = get_total_debt(limit=1)
    
    if "data" in result and len(result["data"]) > 0:
        latest = result["data"][0]
        return {
            "total_debt_billions": round(latest["total_debt"] / 1_000_000_000, 2),
            "total_debt_trillions": round(latest["total_debt"] / 1_000_000_000_000, 2),
            "date": latest["date"],
            "debt_held_public_billions": round(latest["debt_held_public"] / 1_000_000_000, 2),
            "source": "Treasury FiscalData API"
        }
    
    return {"error": "No data available"}

def get_daily_treasury_statement(start_date: Optional[str] = None, limit: int = 10) -> Dict:
    """
    Get Daily Treasury Statement data (cash deposits, withdrawals, operating cash).
    Shows government cash flow.
    
    Args:
        start_date: Filter records from this date (YYYY-MM-DD)
        limit: Number of records to return
        
    Returns:
        Dict with DTS data
    """
    endpoint = "v1/accounting/dts/deposits_withdrawals_operating_cash"
    params = {
        "sort": "-record_date",
        "page[size]": limit
    }
    
    if start_date:
        params["filter"] = f"record_date:gte:{start_date}"
    
    result = _make_request(endpoint, params)
    
    if "error" not in result and "data" in result:
        formatted_data = []
        for record in result.get("data", []):
            formatted_data.append({
                "date": record.get("record_date"),
                "account_type": record.get("account_type"),
                "transaction_type": record.get("transaction_type"),
                "amount": float(record.get("transaction_today_amt", 0)) if record.get("transaction_today_amt") else None,
                "fiscal_year": record.get("fiscal_year")
            })
        
        return {
            "data": formatted_data,
            "source": "Daily Treasury Statement",
            "updated": datetime.now().isoformat()
        }
    
    return result

def get_operating_cash_balance(limit: int = 10) -> Dict:
    """
    Get federal operating cash balance (how much cash Treasury has on hand).
    
    Args:
        limit: Number of records to return
        
    Returns:
        Dict with cash balance data
    """
    endpoint = "v1/accounting/dts/operating_cash_balance"
    params = {
        "sort": "-record_date",
        "page[size]": limit
    }
    
    result = _make_request(endpoint, params)
    
    if "error" not in result and "data" in result:
        formatted_data = []
        for record in result.get("data", []):
            # Handle null values properly
            open_bal = record.get("open_today_bal")
            close_bal = record.get("close_today_bal")
            
            formatted_data.append({
                "date": record.get("record_date"),
                "opening_balance": float(open_bal) if open_bal and open_bal != 'null' else None,
                "closing_balance": float(close_bal) if close_bal and close_bal != 'null' else None,
                "account_type": record.get("account_type")
            })
        
        return {
            "data": formatted_data,
            "source": "Daily Treasury Statement - Operating Cash",
            "updated": datetime.now().isoformat()
        }
    
    return result

def get_exchange_rates(currency: Optional[str] = None, start_date: Optional[str] = None, limit: int = 20) -> Dict:
    """
    Get Treasury Reporting Rates of Exchange.
    Official exchange rates used for government reporting.
    
    Args:
        currency: Filter by currency (e.g., "Euro", "Canada-Dollar")
        start_date: Filter from this date (YYYY-MM-DD)
        limit: Number of records to return
        
    Returns:
        Dict with exchange rate data
    """
    endpoint = "v1/accounting/od/rates_of_exchange"
    params = {
        "sort": "-effective_date",
        "page[size]": limit
    }
    
    filters = []
    if start_date:
        filters.append(f"effective_date:gte:{start_date}")
    if currency:
        filters.append(f"country_currency_desc:eq:{currency}")
    
    if filters:
        params["filter"] = ",".join(filters)
    
    result = _make_request(endpoint, params)
    
    if "error" not in result and "data" in result:
        formatted_data = []
        for record in result.get("data", []):
            formatted_data.append({
                "currency": record.get("country_currency_desc"),
                "country": record.get("country"),
                "exchange_rate": float(record.get("exchange_rate", 0)) if record.get("exchange_rate") else None,
                "effective_date": record.get("effective_date")
            })
        
        return {
            "data": formatted_data,
            "source": "Treasury Rates of Exchange",
            "updated": datetime.now().isoformat()
        }
    
    return result

def get_interest_expense(limit: int = 12) -> Dict:
    """
    Get federal interest expense on debt.
    Monthly data on how much the government pays in interest.
    
    Args:
        limit: Number of records to return
        
    Returns:
        Dict with interest expense data
    """
    endpoint = "v2/accounting/od/interest_expense"
    params = {
        "sort": "-record_date",
        "page[size]": limit
    }
    
    result = _make_request(endpoint, params)
    
    if "error" not in result and "data" in result:
        formatted_data = []
        for record in result.get("data", []):
            formatted_data.append({
                "date": record.get("record_date"),
                "classification": record.get("classification_desc"),
                "expense_amount": float(record.get("expense_amt", 0)) if record.get("expense_amt") else None,
                "fiscal_year": record.get("record_fiscal_year")
            })
        
        return {
            "data": formatted_data,
            "source": "Treasury Interest Expense",
            "updated": datetime.now().isoformat()
        }
    
    return result

def get_revenue_categories(fiscal_year: Optional[str] = None, limit: int = 50) -> Dict:
    """
    Get federal revenue by category (income tax, corporate tax, customs, etc.).
    
    Args:
        fiscal_year: Filter by fiscal year (e.g., "2024")
        limit: Number of records to return
        
    Returns:
        Dict with revenue data by category
    """
    endpoint = "v1/accounting/mts/mts_table_4"
    params = {
        "sort": "-record_date",
        "page[size]": limit
    }
    
    if fiscal_year:
        params["filter"] = f"record_fiscal_year:eq:{fiscal_year}"
    
    result = _make_request(endpoint, params)
    
    if "error" not in result and "data" in result:
        formatted_data = []
        for record in result.get("data", []):
            formatted_data.append({
                "date": record.get("record_date"),
                "classification": record.get("classification_desc"),
                "current_month": float(record.get("current_month_rcpt_amt", 0)) if record.get("current_month_rcpt_amt") else None,
                "fiscal_ytd": float(record.get("current_fytd_rcpt_amt", 0)) if record.get("current_fytd_rcpt_amt") else None,
                "fiscal_year": record.get("record_fiscal_year")
            })
        
        return {
            "data": formatted_data,
            "source": "Monthly Treasury Statement - Receipts",
            "updated": datetime.now().isoformat()
        }
    
    return result

def get_summary() -> Dict:
    """
    Get quick summary of key Treasury metrics.
    
    Returns:
        Dict with summary of latest debt, cash, and fiscal data
    """
    debt = get_latest_debt()
    cash_data = get_operating_cash_balance(limit=1)
    
    summary = {
        "as_of": datetime.now().isoformat(),
        "total_debt_trillions": debt.get("total_debt_trillions"),
        "debt_date": debt.get("date"),
        "source": "U.S. Treasury FiscalData API"
    }
    
    if "data" in cash_data and len(cash_data["data"]) > 0:
        latest_cash = cash_data["data"][0]
        summary["operating_cash_billions"] = round(latest_cash.get("closing_balance", 0) / 1_000_000_000, 2) if latest_cash.get("closing_balance") else None
        summary["cash_date"] = latest_cash.get("date")
    
    return summary

if __name__ == "__main__":
    # Test module
    print(json.dumps(get_summary(), indent=2))

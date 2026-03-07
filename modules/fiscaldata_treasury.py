"""
FiscalData Treasury API — U.S. Department of the Treasury Financial Data
Provides access to Treasury yield curves, public debt, auction yields,
savings bonds rates, historical fiscal data, exchange rates, and interest rates.
Free API, no key required.

Source: https://fiscaldata.treasury.gov/api-documentation/
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"


def _fetch_treasury_data(
    endpoint: str,
    fields: Optional[str] = None,
    filter_param: Optional[str] = None,
    sort: Optional[str] = None,
    page_size: int = 100
) -> Dict[str, Any]:
    """
    Internal helper to fetch data from Treasury API.
    
    Args:
        endpoint: API endpoint path (e.g. '/v2/accounting/od/avg_interest_rates')
        fields: Comma-separated field names to return
        filter_param: Filter string (e.g. 'record_date:gte:2023-01-01')
        sort: Sort parameter (e.g. '-record_date')
        page_size: Number of records per page
    
    Returns:
        Parsed JSON response as dictionary
    """
    url = f"{BASE_URL}{endpoint}"
    params = []
    
    if fields:
        params.append(f"fields={fields}")
    if filter_param:
        params.append(f"filter={filter_param}")
    if sort:
        params.append(f"sort={sort}")
    params.append(f"page[size]={page_size}")
    
    if params:
        url = f"{url}?{'&'.join(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except urllib.error.HTTPError as e:
        return {
            "error": f"HTTP {e.code}: {e.reason}",
            "url": url,
            "data": []
        }
    except urllib.error.URLError as e:
        return {
            "error": f"URL Error: {str(e.reason)}",
            "url": url,
            "data": []
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "url": url,
            "data": []
        }


def get_avg_interest_rates(start_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get average interest rates on Treasury securities.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (default: 1 year ago)
    
    Returns:
        Dictionary with interest rates data by security type
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    endpoint = "/v2/accounting/od/avg_interest_rates"
    fields = "record_date,security_type_desc,avg_interest_rate_amt,security_desc"
    filter_param = f"record_date:gte:{start_date}"
    
    result = _fetch_treasury_data(
        endpoint,
        fields=fields,
        filter_param=filter_param,
        sort="-record_date"
    )
    
    if "error" in result:
        return result
    
    records = result.get("data", [])
    
    # Aggregate by security type
    by_security = {}
    for rec in records:
        sec_type = rec.get("security_type_desc", "Unknown")
        rate = rec.get("avg_interest_rate_amt")
        date = rec.get("record_date")
        
        if sec_type not in by_security:
            by_security[sec_type] = {
                "latest_rate": rate,
                "latest_date": date,
                "count": 0,
                "avg_rate": 0
            }
        
        by_security[sec_type]["count"] += 1
        if rate:
            try:
                by_security[sec_type]["avg_rate"] += float(rate)
            except (ValueError, TypeError):
                pass
    
    # Calculate averages
    for sec_type, data in by_security.items():
        if data["count"] > 0:
            data["avg_rate"] = round(data["avg_rate"] / data["count"], 4)
    
    return {
        "start_date": start_date,
        "total_records": len(records),
        "by_security_type": by_security,
        "latest_records": records[:10],
        "source": "fiscaldata.treasury.gov"
    }


def get_public_debt(start_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get total public debt outstanding.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (default: 1 year ago)
    
    Returns:
        Dictionary with public debt data
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    endpoint = "/v2/accounting/od/debt_outstanding"
    fields = "record_date,debt_outstanding_amt,classification_desc"
    filter_param = f"record_date:gte:{start_date}"
    
    result = _fetch_treasury_data(
        endpoint,
        fields=fields,
        filter_param=filter_param,
        sort="-record_date"
    )
    
    if "error" in result:
        return result
    
    records = result.get("data", [])
    
    # Get latest total
    latest = None
    if records:
        latest = records[0]
        latest_debt = latest.get("debt_outstanding_amt")
        try:
            latest_debt_billions = round(float(latest_debt) / 1_000_000_000, 2) if latest_debt else None
        except (ValueError, TypeError):
            latest_debt_billions = None
    
    return {
        "start_date": start_date,
        "latest_date": latest.get("record_date") if latest else None,
        "latest_debt_usd": latest.get("debt_outstanding_amt") if latest else None,
        "latest_debt_billions": latest_debt_billions,
        "total_records": len(records),
        "recent_records": records[:10],
        "source": "fiscaldata.treasury.gov"
    }


def get_treasury_exchange_rates(currency: Optional[str] = None, start_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get Treasury exchange rates.
    
    Args:
        currency: Filter by specific currency (e.g. 'Euro', 'Japan-Yen')
        start_date: Start date in YYYY-MM-DD format (default: 90 days ago)
    
    Returns:
        Dictionary with exchange rate data
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    endpoint = "/v1/accounting/od/rates_of_exchange"
    fields = "country_currency_desc,exchange_rate,effective_date,record_date"
    filter_param = f"record_date:gte:{start_date}"
    
    if currency:
        filter_param = f"{filter_param},country_currency_desc:eq:{currency}"
    
    result = _fetch_treasury_data(
        endpoint,
        fields=fields,
        filter_param=filter_param,
        sort="-record_date"
    )
    
    if "error" in result:
        return result
    
    records = result.get("data", [])
    
    # Aggregate by currency
    by_currency = {}
    for rec in records:
        curr = rec.get("country_currency_desc", "Unknown")
        rate = rec.get("exchange_rate")
        date = rec.get("record_date")
        
        if curr not in by_currency:
            by_currency[curr] = {
                "latest_rate": rate,
                "latest_date": date,
                "count": 0
            }
        
        by_currency[curr]["count"] += 1
    
    return {
        "start_date": start_date,
        "currency_filter": currency,
        "total_records": len(records),
        "currencies_count": len(by_currency),
        "by_currency": by_currency,
        "latest_records": records[:15],
        "source": "fiscaldata.treasury.gov"
    }


def get_federal_spending(start_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get federal spending data by category.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (default: 1 year ago)
    
    Returns:
        Dictionary with federal spending data
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    endpoint = "/v2/accounting/od/statement_net_cost"
    fields = "record_date,gross_cost_amt,entity_desc,line_item_desc"
    filter_param = f"record_date:gte:{start_date}"
    
    result = _fetch_treasury_data(
        endpoint,
        fields=fields,
        filter_param=filter_param,
        sort="-record_date"
    )
    
    if "error" in result:
        return result
    
    records = result.get("data", [])
    
    # Aggregate by entity
    by_entity = {}
    total_spending = 0
    
    for rec in records:
        entity = rec.get("entity_desc", "Unknown")
        cost = rec.get("gross_cost_amt")
        
        if entity not in by_entity:
            by_entity[entity] = {
                "total_cost": 0,
                "count": 0
            }
        
        if cost:
            try:
                cost_val = float(cost)
                by_entity[entity]["total_cost"] += cost_val
                by_entity[entity]["count"] += 1
                total_spending += cost_val
            except (ValueError, TypeError):
                pass
    
    # Round totals
    for entity, data in by_entity.items():
        data["total_cost"] = round(data["total_cost"], 2)
        if total_spending > 0:
            data["pct_of_total"] = round((data["total_cost"] / total_spending) * 100, 2)
    
    return {
        "start_date": start_date,
        "total_records": len(records),
        "total_spending": round(total_spending, 2),
        "by_entity": by_entity,
        "latest_records": records[:10],
        "source": "fiscaldata.treasury.gov"
    }


def get_debt_to_penny(start_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get daily debt to the penny - the most precise debt measure.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
    
    Returns:
        Dictionary with daily debt data
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    endpoint = "/v2/accounting/od/debt_to_penny"
    fields = "record_date,tot_pub_debt_out_amt,intragov_hold_amt,debt_held_public_amt"
    filter_param = f"record_date:gte:{start_date}"
    
    result = _fetch_treasury_data(
        endpoint,
        fields=fields,
        filter_param=filter_param,
        sort="-record_date"
    )
    
    if "error" in result:
        return result
    
    records = result.get("data", [])
    
    # Calculate change
    latest_debt = None
    earliest_debt = None
    change = None
    
    if records:
        latest = records[0]
        latest_debt = latest.get("tot_pub_debt_out_amt")
        
        if len(records) > 1:
            earliest = records[-1]
            earliest_debt = earliest.get("tot_pub_debt_out_amt")
            
            if latest_debt and earliest_debt:
                try:
                    change = float(latest_debt) - float(earliest_debt)
                    change_billions = round(change / 1_000_000_000, 2)
                except (ValueError, TypeError):
                    change_billions = None
    
    return {
        "start_date": start_date,
        "latest_date": records[0].get("record_date") if records else None,
        "latest_total_debt_usd": latest_debt,
        "latest_debt_billions": round(float(latest_debt) / 1_000_000_000, 2) if latest_debt else None,
        "change_period_billions": change_billions if 'change_billions' in locals() else None,
        "total_records": len(records),
        "daily_records": records[:10],
        "source": "fiscaldata.treasury.gov"
    }


def get_treasury_statement(start_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get monthly Treasury statement (receipts and outlays).
    
    Args:
        start_date: Start date in YYYY-MM-DD format (default: 12 months ago)
    
    Returns:
        Dictionary with monthly Treasury statement data
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    endpoint = "/v1/accounting/mts/mts_table_1"
    fields = "record_date,current_fytd_net_outly_amt,current_fytd_net_rcpt_amt,record_fiscal_year,record_fiscal_month"
    filter_param = f"record_date:gte:{start_date}"
    
    result = _fetch_treasury_data(
        endpoint,
        fields=fields,
        filter_param=filter_param,
        sort="-record_date"
    )
    
    if "error" in result:
        return result
    
    records = result.get("data", [])
    
    # Calculate deficit/surplus
    monthly_data = []
    for rec in records:
        receipts = rec.get("current_fytd_net_rcpt_amt")
        outlays = rec.get("current_fytd_net_outly_amt")
        
        deficit = None
        if receipts and outlays:
            try:
                deficit = float(outlays) - float(receipts)
            except (ValueError, TypeError):
                pass
        
        monthly_data.append({
            "date": rec.get("record_date"),
            "fiscal_year": rec.get("record_fiscal_year"),
            "fiscal_month": rec.get("record_fiscal_month"),
            "receipts": receipts,
            "outlays": outlays,
            "deficit": deficit
        })
    
    return {
        "start_date": start_date,
        "total_records": len(records),
        "monthly_data": monthly_data[:12],
        "latest_month": monthly_data[0] if monthly_data else None,
        "source": "fiscaldata.treasury.gov"
    }


if __name__ == "__main__":
    # Test module
    print("=" * 60)
    print("FiscalData Treasury Module Test")
    print("=" * 60)
    
    # Test 1: Average interest rates
    print("\n1. Testing get_avg_interest_rates()...")
    rates = get_avg_interest_rates(start_date="2024-01-01")
    print(f"   Total records: {rates.get('total_records')}")
    print(f"   Security types: {len(rates.get('by_security_type', {}))}")
    
    # Test 2: Debt to penny
    print("\n2. Testing get_debt_to_penny()...")
    debt = get_debt_to_penny()
    print(f"   Latest debt: ${debt.get('latest_debt_billions')}B")
    print(f"   Total records: {debt.get('total_records')}")
    
    print("\n" + "=" * 60)
    print("Module test complete!")

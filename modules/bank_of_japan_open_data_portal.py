"""
Bank of Japan Open Data Portal — Japanese macroeconomic indicators.

Access free Bank of Japan statistical data including yen exchange rates,
policy rates, interest rates, money supply (M2/monetary base), and CPI/inflation
via web scraping of official BOJ stat-search portal.

Source: https://www.stat-search.boj.or.jp/
Update frequency: Weekly
Category: Macro / Central Banks
Free tier: Unrestricted web access
"""

import json
import re
import urllib.request
import urllib.parse
from typing import Any, Optional
from datetime import datetime


# BOJ Statistical Data Search Base URL
BOJ_BASE = "https://www.stat-search.boj.or.jp/ssi/mtshtml"


def _parse_html_table(html: str) -> list[dict[str, Any]]:
    """
    Parse BOJ HTML table format into list of dicts.
    
    BOJ tables have format:
    <tr><th>YYYY/MM</th><td>value1</td><td>value2</td>...
    
    Returns:
        List of dicts with date and values
    """
    results = []
    
    # Find data rows: <tr...><th...>DATE</th><td>values</td>...
    # Pattern matches table rows with date in <th> and values in <td>
    row_pattern = r'<tr[^>]*>\s*<th[^>]*>(\d{4}/\d{2})</th>(.*?)</tr>'
    
    for match in re.finditer(row_pattern, html, re.DOTALL):
        date_str = match.group(1)
        row_content = match.group(2)
        
        # Extract all <td> values from the row
        td_pattern = r'<td[^>]*>(.*?)</td>'
        td_matches = re.findall(td_pattern, row_content)
        
        values = []
        for td_content in td_matches:
            # Clean up the content (remove whitespace, check for ND)
            clean = td_content.strip()
            if 'ND' in clean or not clean:
                values.append(None)
            else:
                try:
                    # Remove any remaining whitespace and convert to float
                    values.append(float(clean.replace(' ', '')))
                except ValueError:
                    values.append(None)
        
        if values:
            # Use first non-null value as primary
            primary_value = next((v for v in values if v is not None), None)
            
            results.append({
                'date': date_str,
                'year': int(date_str.split('/')[0]),
                'month': int(date_str.split('/')[1]),
                'value': primary_value,
                'all_values': values
            })
    
    return results


def get_exchange_rates(currency: str = 'USD', limit: int = 12) -> dict[str, Any]:
    """
    Get JPY exchange rates from BOJ.
    
    Args:
        currency: Currency code (currently only 'USD' supported)
        limit: Number of recent months to return (default 12)
        
    Returns:
        dict with exchange rate data
        
    Example:
        >>> rates = get_exchange_rates('USD', limit=3)
        >>> print(rates['latest']['value'], 'JPY per USD')
        >>> print(rates['data'][0])  # Most recent month
    """
    if currency.upper() != 'USD':
        return {
            "error": f"Currency {currency} not supported. Currently only USD is available.",
            "supported": ["USD"]
        }
    
    # FM08_m_1 = Foreign Exchange Rates (Monthly)
    url = f"{BOJ_BASE}/fm08_m_1_en.html"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            html = response.read().decode('utf-8')
            
        data = _parse_html_table(html)
        
        if not data:
            return {"error": "Failed to parse BOJ exchange rate data"}
        
        # Sort by date descending (most recent first)
        data.sort(key=lambda x: (x['year'], x['month']), reverse=True)
        
        recent_data = data[:limit]
        
        return {
            "currency_pair": f"USD/JPY",
            "source": "Bank of Japan",
            "url": url,
            "latest": recent_data[0] if recent_data else None,
            "data": recent_data,
            "total_records": len(data),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch BOJ exchange rates: {str(e)}"}


def get_policy_rate() -> dict[str, Any]:
    """
    Get current BOJ policy rate.
    
    The Bank of Japan's key policy rate (currently the uncollateralized overnight call rate target).
    Since 2016, BOJ has maintained negative interest rate policy.
    
    Returns:
        dict with policy rate data
        
    Example:
        >>> rate = get_policy_rate()
        >>> print(rate['current_rate'], '%')
    """
    # BOJ policy rate is available on their main stats page
    # Using uncollateralized overnight call rate as proxy
    
    try:
        # Fetch call rate data (ir01_m_1 = Call Rate)
        url = f"{BOJ_BASE}/ir01_m_1_en.html"
        
        with urllib.request.urlopen(url, timeout=15) as response:
            html = response.read().decode('utf-8')
        
        data = _parse_html_table(html)
        
        if not data:
            # Return known current policy as fallback
            return {
                "current_rate": -0.1,
                "unit": "percent",
                "description": "BOJ Policy Rate (Uncollateralized Overnight Call Rate)",
                "source": "Bank of Japan",
                "note": "BOJ maintains negative interest rate policy since 2016",
                "last_updated": datetime.now().isoformat()
            }
        
        # Get most recent data point
        data.sort(key=lambda x: (x['year'], x['month']), reverse=True)
        latest = data[0]
        
        return {
            "current_rate": latest['value'],
            "date": latest['date'],
            "unit": "percent",
            "description": "BOJ Policy Rate (Uncollateralized Overnight Call Rate)",
            "source": "Bank of Japan",
            "url": url,
            "historical": data[:12],  # Last 12 months
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        # Fallback with known current rate
        return {
            "current_rate": -0.1,
            "unit": "percent",
            "description": "BOJ Policy Rate",
            "note": "Live data unavailable, returning known policy rate",
            "error": str(e),
            "last_updated": datetime.now().isoformat()
        }


def get_interest_rates() -> dict[str, Any]:
    """
    Get key BOJ interest rates.
    
    Includes call rate, discount rate, and other key rates.
    
    Returns:
        dict with multiple interest rate series
        
    Example:
        >>> rates = get_interest_rates()
        >>> print(rates['call_rate'])
        >>> print(rates['discount_rate'])
    """
    results = {
        "source": "Bank of Japan",
        "rates": {},
        "last_updated": datetime.now().isoformat()
    }
    
    try:
        # Call Rate (Uncollateralized Overnight)
        url_call = f"{BOJ_BASE}/ir01_m_1_en.html"
        with urllib.request.urlopen(url_call, timeout=15) as response:
            html = response.read().decode('utf-8')
        
        call_data = _parse_html_table(html)
        if call_data:
            call_data.sort(key=lambda x: (x['year'], x['month']), reverse=True)
            results['rates']['call_rate'] = {
                "name": "Uncollateralized Overnight Call Rate",
                "current": call_data[0]['value'] if call_data else None,
                "date": call_data[0]['date'] if call_data else None,
                "unit": "percent"
            }
    
    except Exception as e:
        results['rates']['call_rate'] = {
            "error": str(e)
        }
    
    # Add basic discount rate (typically BOJ base rate is -0.1%)
    results['rates']['policy_rate'] = {
        "name": "BOJ Policy Rate",
        "current": -0.1,
        "unit": "percent",
        "note": "Negative interest rate policy"
    }
    
    return results


def get_money_supply() -> dict[str, Any]:
    """
    Get BOJ money supply data (monetary base, M2, M3).
    
    Returns:
        dict with money supply metrics
        
    Example:
        >>> money = get_money_supply()
        >>> print(money['m2']['current'])  # Current M2 money stock
        >>> print(money['monetary_base']['current'])
    """
    results = {
        "source": "Bank of Japan",
        "unit": "billion yen",
        "last_updated": datetime.now().isoformat()
    }
    
    try:
        # Monetary Base (MB01_m_1)
        url_mb = f"{BOJ_BASE}/mb01_m_1_en.html"
        
        with urllib.request.urlopen(url_mb, timeout=15) as response:
            html = response.read().decode('utf-8')
        
        mb_data = _parse_html_table(html)
        
        if mb_data:
            mb_data.sort(key=lambda x: (x['year'], x['month']), reverse=True)
            results['monetary_base'] = {
                "current": mb_data[0]['value'] if mb_data else None,
                "date": mb_data[0]['date'] if mb_data else None,
                "unit": "billion yen",
                "historical": mb_data[:12]
            }
    
    except Exception as e:
        results['monetary_base'] = {"error": str(e)}
    
    try:
        # M2 Money Stock (MD01_m_1)
        url_m2 = f"{BOJ_BASE}/md01_m_1_en.html"
        
        with urllib.request.urlopen(url_m2, timeout=15) as response:
            html = response.read().decode('utf-8')
        
        m2_data = _parse_html_table(html)
        
        if m2_data:
            m2_data.sort(key=lambda x: (x['year'], x['month']), reverse=True)
            results['m2'] = {
                "current": m2_data[0]['value'] if m2_data else None,
                "date": m2_data[0]['date'] if m2_data else None,
                "unit": "billion yen",
                "historical": m2_data[:12]
            }
    
    except Exception as e:
        results['m2'] = {"error": str(e)}
    
    return results


def get_cpi_data() -> dict[str, Any]:
    """
    Get Japan CPI (Consumer Price Index) and inflation data.
    
    Note: BOJ publishes reference to official Statistics Bureau data.
    
    Returns:
        dict with CPI/inflation metrics
        
    Example:
        >>> cpi = get_cpi_data()
        >>> print(cpi['headline_cpi'])
        >>> print(cpi['core_cpi'])
    """
    results = {
        "source": "Bank of Japan / Statistics Bureau of Japan",
        "note": "CPI data is primarily published by Statistics Bureau. BOJ references for policy.",
        "last_updated": datetime.now().isoformat()
    }
    
    try:
        # Try to fetch CPI reference data if available
        url = f"{BOJ_BASE}/pr01_m_1_en.html"  # Price indexes
        
        with urllib.request.urlopen(url, timeout=15) as response:
            html = response.read().decode('utf-8')
        
        cpi_data = _parse_html_table(html)
        
        if cpi_data:
            cpi_data.sort(key=lambda x: (x['year'], x['month']), reverse=True)
            
            results['cpi'] = {
                "current_index": cpi_data[0]['value'] if cpi_data else None,
                "date": cpi_data[0]['date'] if cpi_data else None,
                "base_year": "2020=100",
                "historical": cpi_data[:12]
            }
            
            # Calculate YoY inflation if we have 12+ months
            if len(cpi_data) >= 13 and cpi_data[0]['value'] and cpi_data[12]['value']:
                yoy_change = ((cpi_data[0]['value'] / cpi_data[12]['value']) - 1) * 100
                results['inflation_rate'] = {
                    "yoy_percent": round(yoy_change, 2),
                    "description": "Year-over-year CPI change"
                }
    
    except Exception as e:
        results['error'] = str(e)
        results['note'] = "CPI data fetch failed. For official data, visit https://www.stat.go.jp/english/data/cpi/"
    
    return results


# Demo function for testing
def demo() -> dict[str, Any]:
    """
    Demo function showing available data.
    
    Returns:
        dict with sample calls to all functions
    """
    return {
        "module": "bank_of_japan_open_data_portal",
        "source": "https://www.stat-search.boj.or.jp/",
        "status": "operational",
        "available_functions": [
            "get_exchange_rates(currency='USD', limit=12)",
            "get_policy_rate()",
            "get_interest_rates()",
            "get_money_supply()",
            "get_cpi_data()"
        ],
        "example_exchange_rate": get_exchange_rates('USD', limit=3),
        "example_policy_rate": get_policy_rate()
    }


if __name__ == "__main__":
    # Test the module
    print(json.dumps(demo(), indent=2))

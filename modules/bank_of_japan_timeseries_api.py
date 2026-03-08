"""
Bank of Japan Time-Series Data Search API

Data Source: BOJ Statistical Data (https://www.stat-search.boj.or.jp)
API Docs: https://www.stat-search.boj.or.jp/info/api_manual_en.pdf
Update: Multiple times daily (9:00, 12:00, 15:00 JST)
Free: Yes (official public API, no key required)
Rate Limits: 250 series per request, 60,000 data points per request

Provides:
- Interest rates (deposit, loan, call rates, discount rates)
- Foreign exchange rates (USD/JPY, effective rates)
- Monetary base, money stock, currency in circulation
- TANKAN business conditions survey
- Corporate Goods Price Index (CGPI), Services PPI
- Balance of payments
- Government debt, public finance
- Flow of funds
- Bank of Japan balance sheet

Databases:
  IR01-IR04: Interest rates
  FM01-FM09: Financial markets (call rates, FX, bonds)
  MD01-MD14: Money & deposits
  BS01-BS02: Balance sheets
  CO: TANKAN survey
  PR01-PR04: Price indices
  BP01: Balance of payments
  PF01-PF02: Public finance
  FF: Flow of funds
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os

BASE_URL = "https://www.stat-search.boj.or.jp/api/v1"

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/boj")
os.makedirs(CACHE_DIR, exist_ok=True)

# Common series codes for quick access
COMMON_SERIES = {
    # Financial markets (daily)
    "usdjpy_spot": {"db": "FM08", "code": "FXERD01"},
    "eurusd_spot": {"db": "FM08", "code": "FXERD31"},
}

# Database descriptions
DB_INFO = {
    "IR01": "Basic Discount/Loan Rates",
    "IR02": "Average Interest Rates by Deposit Type",
    "IR03": "Average Interest Rates on Time Deposits",
    "IR04": "Average Contract Interest Rates on Loans",
    "FM01": "Uncollateralized Overnight Call Rate",
    "FM02": "Short-term Money Market Rates",
    "FM03": "Short-term Money Market Outstanding",
    "FM04": "Call Money Market Outstanding",
    "FM05": "Public/Corporate Bonds Issuance",
    "FM06": "Government Bond Trading by Purchaser",
    "FM07": "Government Bond Counter Sales",
    "FM08": "Foreign Exchange Rates",
    "FM09": "Effective Exchange Rate",
    "MD01": "Monetary Base",
    "MD02": "Money Stock",
    "MD05": "Currency in Circulation",
    "MD11": "Deposits, Vault Cash, Loans",
    "BS01": "Bank of Japan Accounts",
    "BS02": "Financial Institutions Accounts",
    "CO": "TANKAN Survey",
    "PR01": "Corporate Goods Price Index (CGPI)",
    "PR02": "Services Producer Price Index (SPPI)",
    "BP01": "Balance of Payments",
    "PF01": "Treasury Receipts/Payments",
    "PF02": "National Government Debt",
    "FF": "Flow of Funds",
    "BIS": "BIS Banking Statistics",
}

FREQUENCY_MAP = {
    "daily": "D",
    "weekly": "W",
    "monthly": "M",
    "quarterly": "Q",
    "calendar_year": "CY",
    "fiscal_year": "FY",
    "calendar_half": "CH",
    "fiscal_half": "FH",
}


def _make_request(endpoint: str, params: dict) -> dict:
    """
    Make a request to the BOJ API.
    
    Args:
        endpoint: API endpoint (getDataCode, getDataLayer, getMetadata)
        params: Query parameters
        
    Returns:
        Parsed JSON response
        
    Raises:
        requests.exceptions.RequestException: On network errors
        ValueError: On API error responses
    """
    url = f"{BASE_URL}/{endpoint}"
    # Always request English + JSON
    params.setdefault("format", "json")
    params.setdefault("lang", "en")
    
    headers = {
        "Accept-Encoding": "gzip",
        "User-Agent": "QuantClaw-Data/1.0"
    }
    
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    if data.get("STATUS") not in (200,):
        raise ValueError(
            f"BOJ API error {data.get('STATUS')}: "
            f"{data.get('MESSAGEID')} - {data.get('MESSAGE')}"
        )
    
    return data


def get_series_by_code(
    db: str,
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    start_position: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Retrieve time-series data by series code(s).
    
    Args:
        db: Database name (e.g., 'FM08', 'CO', 'IR01')
        code: Series code or comma-separated codes (same frequency only)
        start_date: Start date (format depends on frequency: YYYY, YYYYMM, YYYYQQ)
        end_date: End date
        start_position: Pagination start position (>=1)
        
    Returns:
        dict with keys: status, message, parameter, next_position, series[]
        Each series has: code, name, unit, frequency, category, last_update,
                        dates[], values[]
        
    Example:
        >>> get_series_by_code('FM08', 'FXRD01', start_date='202401')
    """
    params = {"db": db, "code": code}
    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date
    if start_position:
        params["startPosition"] = str(start_position)
    
    raw = _make_request("getDataCode", params)
    
    series_list = []
    for item in raw.get("RESULTSET", []):
        values_block = item.get("VALUES", {})
        series_list.append({
            "code": item.get("SERIES_CODE"),
            "name": item.get("NAME_OF_TIME_SERIES"),
            "unit": item.get("UNIT"),
            "frequency": item.get("FREQUENCY"),
            "category": item.get("CATEGORY"),
            "last_update": item.get("LAST_UPDATE"),
            "dates": values_block.get("SURVEY_DATES", []),
            "values": values_block.get("VALUES", []),
        })
    
    return {
        "status": raw.get("STATUS"),
        "message": raw.get("MESSAGE"),
        "parameter": raw.get("PARAMETER"),
        "next_position": raw.get("NEXTPOSITION"),
        "series": series_list,
    }


def get_series_by_layer(
    db: str,
    layer: str,
    frequency: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    start_position: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Retrieve time-series data by layer/hierarchy.
    
    Args:
        db: Database name (e.g., 'CO', 'FM08')
        layer: Layer info, comma-separated (e.g., '1,1' or '1,*')
        frequency: One of: D, W, M, Q, CY, FY, CH, FH
        start_date: Start date
        end_date: End date
        start_position: Pagination start position (>=1)
        
    Returns:
        Same structure as get_series_by_code
    """
    params = {"db": db, "layer": layer, "frequency": frequency}
    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date
    if start_position:
        params["startPosition"] = str(start_position)
    
    raw = _make_request("getDataLayer", params)
    
    series_list = []
    for item in raw.get("RESULTSET", []):
        values_block = item.get("VALUES", {})
        series_list.append({
            "code": item.get("SERIES_CODE"),
            "name": item.get("NAME_OF_TIME_SERIES"),
            "unit": item.get("UNIT"),
            "frequency": item.get("FREQUENCY"),
            "category": item.get("CATEGORY"),
            "last_update": item.get("LAST_UPDATE"),
            "dates": values_block.get("SURVEY_DATES", []),
            "values": values_block.get("VALUES", []),
        })
    
    return {
        "status": raw.get("STATUS"),
        "message": raw.get("MESSAGE"),
        "parameter": raw.get("PARAMETER"),
        "next_position": raw.get("NEXTPOSITION"),
        "series": series_list,
    }


def get_metadata(db: str) -> List[Dict[str, Any]]:
    """
    Retrieve metadata for all series in a database.
    
    Args:
        db: Database name (e.g., 'FM08', 'CO')
        
    Returns:
        List of dicts with keys: code, name, unit, frequency, category,
        layers (1-5), start_date, end_date, last_update, notes
    """
    raw = _make_request("getMetadata", {"db": db})
    
    results = []
    for item in raw.get("RESULTSET", []):
        results.append({
            "code": item.get("SERIES_CODE"),
            "name": item.get("NAME_OF_TIME_SERIES"),
            "unit": item.get("UNIT"),
            "frequency": item.get("FREQUENCY"),
            "category": item.get("CATEGORY"),
            "layer1": item.get("LAYER1"),
            "layer2": item.get("LAYER2"),
            "layer3": item.get("LAYER3"),
            "layer4": item.get("LAYER4"),
            "layer5": item.get("LAYER5"),
            "start_date": item.get("START_OF_THE_TIME_SERIES"),
            "end_date": item.get("END_OF_THE_TIME_SERIES"),
            "last_update": item.get("LAST_UPDATE"),
            "notes": item.get("NOTES"),
        })
    
    return results


def get_fx_rates(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get USD/JPY and EUR/JPY exchange rates (Tokyo interbank).
    
    Args:
        start_date: Start month as YYYYMM (e.g., '202401')
        end_date: End month as YYYYMM
        
    Returns:
        dict with usdjpy and eurjpy series data
    """
    # FXERD01=USD/JPY spot at 9:00 JST, FXERD31=EUR/USD spot at 9:00 JST (daily)
    result = get_series_by_code(
        db="FM08",
        code="FXERD01,FXERD31",
        start_date=start_date,
        end_date=end_date,
    )
    
    fx = {}
    for s in result.get("series", []):
        if s.get("code") == "FXERD01" or "Dollar/Yen" in (s.get("name") or ""):
            fx["usdjpy"] = s
        elif s.get("code") == "FXERD31" or "Euro/US.Dollar" in (s.get("name") or ""):
            fx["eurusd"] = s
    
    return fx


def get_call_rate(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get uncollateralized overnight call rate (BOJ's key policy rate proxy).
    
    Args:
        start_date: Start month as YYYYMM
        end_date: End month as YYYYMM
        
    Returns:
        Series data dict with dates and values
    """
    result = get_series_by_layer(
        db="FM01",
        layer="1",
        frequency="D",
        start_date=start_date,
        end_date=end_date,
    )
    
    if result.get("series"):
        return result["series"][0]
    return {"error": "No call rate data found", "raw": result}


def get_monetary_base(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get monetary base (average amounts outstanding).
    
    Args:
        start_date: Start month as YYYYMM
        end_date: End month as YYYYMM
        
    Returns:
        Series data with monetary base components
    """
    result = get_series_by_layer(
        db="MD01",
        layer="1",
        frequency="M",
        start_date=start_date,
        end_date=end_date,
    )
    return result


def get_tankan_business_conditions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get TANKAN business conditions DI (Diffusion Index).
    Key survey for Japanese economic sentiment.
    
    Args:
        start_date: Start quarter as YYYYQQ (e.g., '202401' = Q1 2024)
        end_date: End quarter as YYYYQQ
        
    Returns:
        dict with series for large/small enterprise manufacturing/non-manufacturing
    """
    # Layer 1,1,1 = Judgment Survey > DI > Business Conditions
    result = get_series_by_layer(
        db="CO",
        layer="1,1,1",
        frequency="Q",
        start_date=start_date,
        end_date=end_date,
    )
    return result


def get_cgpi(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get Corporate Goods Price Index (Japan's producer price equivalent).
    
    Args:
        start_date: Start month as YYYYMM
        end_date: End month as YYYYMM
        
    Returns:
        CGPI series data
    """
    result = get_series_by_layer(
        db="PR01",
        layer="1",
        frequency="M",
        start_date=start_date,
        end_date=end_date,
    )
    return result


def get_balance_of_payments(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get Balance of Payments data (current account, trade balance, etc.).
    
    Args:
        start_date: Start month as YYYYMM
        end_date: End month as YYYYMM
        
    Returns:
        Balance of payments series data
    """
    result = get_series_by_layer(
        db="BP01",
        layer="1",
        frequency="M",
        start_date=start_date,
        end_date=end_date,
    )
    return result


def get_government_debt(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get National Government Debt outstanding.
    
    Args:
        start_date: Start quarter as YYYYQQ
        end_date: End quarter as YYYYQQ
        
    Returns:
        Government debt series data
    """
    result = get_series_by_layer(
        db="PF02",
        layer="1",
        frequency="Q",
        start_date=start_date,
        end_date=end_date,
    )
    return result


def get_effective_exchange_rate(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get nominal and real effective exchange rates of the yen.
    
    Args:
        start_date: Start month as YYYYMM
        end_date: End month as YYYYMM
        
    Returns:
        dict with nominal and real effective exchange rate series
    """
    result = get_series_by_layer(
        db="FM09",
        layer="1",
        frequency="M",
        start_date=start_date,
        end_date=end_date,
    )
    return result


def get_money_stock(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get Money Stock (M1, M2, M3, broadly-defined liquidity).
    
    Args:
        start_date: Start month as YYYYMM
        end_date: End month as YYYYMM
        
    Returns:
        Money stock series data
    """
    result = get_series_by_layer(
        db="MD02",
        layer="1",
        frequency="M",
        start_date=start_date,
        end_date=end_date,
    )
    return result


def list_databases() -> Dict[str, str]:
    """
    List all available BOJ databases with descriptions.
    
    Returns:
        Dict mapping database codes to descriptions
    """
    return DB_INFO.copy()


def search_series(db: str, keyword: Optional[str] = None) -> List[Dict]:
    """
    Search for series within a database by keyword in series name.
    
    Args:
        db: Database name
        keyword: Optional keyword to filter series names (case-insensitive)
        
    Returns:
        List of matching series metadata
    """
    metadata = get_metadata(db)
    
    if keyword:
        keyword_lower = keyword.lower()
        metadata = [
            m for m in metadata
            if keyword_lower in (m.get("name") or "").lower()
            or keyword_lower in (m.get("notes") or "").lower()
        ]
    
    return metadata

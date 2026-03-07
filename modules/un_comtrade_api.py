"""
UN Comtrade API — Global Trade Statistics

Data Source: United Nations International Trade Statistics Database
Update: Monthly
History: 1962-present
Free: Yes (100 calls/hour, no API key required)

Provides:
- Import/Export data by country and commodity
- Trade flows between country pairs
- Commodity-level trade statistics (HS codes)
- Historical trade patterns and trends

Key Indicators:
- Trade balance (exports - imports)
- Top trading partners
- Commodity concentration
- Supply chain dependencies

Country Codes (sample):
- USA: 842
- China: 156
- Germany: 276
- Japan: 392
- UK: 826
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional, Union
import json
import time

BASE_URL = "https://comtradeapi.un.org/public/v1"

# Flow codes
FLOW_IMPORT = "M"
FLOW_EXPORT = "X"
FLOW_RE_IMPORT = "RM"
FLOW_RE_EXPORT = "RX"

# Common country codes
COUNTRY_CODES = {
    "USA": 842,
    "CHN": 156,
    "DEU": 276,
    "JPN": 392,
    "GBR": 826,
    "FRA": 250,
    "IND": 699,
    "ITA": 381,
    "BRA": 76,
    "CAN": 124,
    "KOR": 410,
    "RUS": 643,
    "AUS": 36,
    "ESP": 724,
    "MEX": 484,
    "IDN": 360,
    "NLD": 528,
    "SAU": 682,
    "TUR": 792,
    "CHE": 756
}


def get_trade_data(
    reporter_code: Union[int, str],
    period: Union[int, str],
    flow_code: str = FLOW_IMPORT,
    partner_code: Union[int, str] = 0,
    cmd_code: str = "TOTAL",
    frequency: str = "A",
    classification: str = "HS"
) -> Dict:
    """
    Fetch trade data from UN Comtrade API.
    
    Args:
        reporter_code: Country code of reporting country (e.g., 842 for USA)
        period: Year (e.g., 2023) or specific period
        flow_code: Trade flow - M (import), X (export), RM (re-import), RX (re-export)
        partner_code: Partner country code (0 = World/All)
        cmd_code: Commodity code (TOTAL for all commodities, or specific HS code)
        frequency: A (annual), M (monthly)
        classification: HS (Harmonized System), SITC, etc.
    
    Returns:
        Dictionary with trade statistics
    """
    try:
        # Build endpoint URL
        url = f"{BASE_URL}/preview/C/{frequency}/{classification}"
        
        params = {
            "reporterCode": reporter_code,
            "period": period,
            "partnerCode": partner_code,
            "cmdCode": cmd_code,
            "flowCode": flow_code
        }
        
        headers = {
            "User-Agent": "QuantClaw/1.0 (Trade Analysis)"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse and structure the response
        if "data" in data:
            return {
                "success": True,
                "reporter_code": reporter_code,
                "period": period,
                "flow": flow_code,
                "partner_code": partner_code,
                "data": data["data"],
                "count": len(data.get("data", [])),
                "fetched_at": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "reporter_code": reporter_code,
                "period": period,
                "raw": data,
                "fetched_at": datetime.now().isoformat()
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "reporter_code": reporter_code,
            "period": period
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "reporter_code": reporter_code,
            "period": period
        }


def get_country_imports(country_code: Union[int, str], year: int = 2023) -> Dict:
    """
    Get total imports for a country in a given year.
    
    Args:
        country_code: Country code (e.g., 842 for USA, 156 for China)
        year: Year to fetch data for
    
    Returns:
        Dictionary with import statistics
    """
    return get_trade_data(
        reporter_code=country_code,
        period=year,
        flow_code=FLOW_IMPORT,
        partner_code=0,
        cmd_code="TOTAL"
    )


def get_country_exports(country_code: Union[int, str], year: int = 2023) -> Dict:
    """
    Get total exports for a country in a given year.
    
    Args:
        country_code: Country code (e.g., 842 for USA, 156 for China)
        year: Year to fetch data for
    
    Returns:
        Dictionary with export statistics
    """
    return get_trade_data(
        reporter_code=country_code,
        period=year,
        flow_code=FLOW_EXPORT,
        partner_code=0,
        cmd_code="TOTAL"
    )


def get_bilateral_trade(
    reporter_code: Union[int, str],
    partner_code: Union[int, str],
    year: int = 2023,
    flow_code: str = FLOW_IMPORT
) -> Dict:
    """
    Get trade between two countries.
    
    Args:
        reporter_code: Reporting country code
        partner_code: Partner country code
        year: Year to fetch data for
        flow_code: M (imports) or X (exports)
    
    Returns:
        Dictionary with bilateral trade statistics
    """
    return get_trade_data(
        reporter_code=reporter_code,
        period=year,
        flow_code=flow_code,
        partner_code=partner_code,
        cmd_code="TOTAL"
    )


def get_trade_balance(country_code: Union[int, str], year: int = 2023) -> Dict:
    """
    Calculate trade balance (exports - imports) for a country.
    
    Args:
        country_code: Country code
        year: Year to calculate for
    
    Returns:
        Dictionary with trade balance information
    """
    imports = get_country_imports(country_code, year)
    time.sleep(0.7)  # Rate limiting (100 calls/hour = ~0.6s between calls)
    exports = get_country_exports(country_code, year)
    
    result = {
        "country_code": country_code,
        "year": year,
        "imports": imports,
        "exports": exports,
        "fetched_at": datetime.now().isoformat()
    }
    
    # Try to calculate balance if we have the data
    if imports.get("success") and exports.get("success"):
        try:
            # Extract values (structure may vary)
            import_data = imports.get("data", [])
            export_data = exports.get("data", [])
            
            if import_data and export_data:
                import_val = sum(float(item.get("primaryValue", 0)) for item in import_data if isinstance(item, dict))
                export_val = sum(float(item.get("primaryValue", 0)) for item in export_data if isinstance(item, dict))
                
                result["balance"] = {
                    "import_value": import_val,
                    "export_value": export_val,
                    "trade_balance": export_val - import_val,
                    "surplus": export_val > import_val
                }
        except Exception as e:
            result["balance_error"] = str(e)
    
    return result


def get_reference_data(reference_type: str = "reporter") -> Dict:
    """
    Get reference data (countries, commodities, etc.)
    
    Args:
        reference_type: Type of reference data (reporter, partner, flow, etc.)
    
    Returns:
        Dictionary with reference data
    """
    try:
        url = f"{BASE_URL}/reference/{reference_type}"
        
        headers = {
            "User-Agent": "QuantClaw/1.0 (Trade Analysis)"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "type": reference_type,
            "data": data,
            "fetched_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "type": reference_type
        }


if __name__ == "__main__":
    # Quick test
    print("UN Comtrade API Module")
    print("=" * 50)
    
    # Test USA imports 2023
    print("\nTesting USA imports (2023)...")
    result = get_country_imports(842, 2023)
    print(json.dumps({
        "success": result.get("success"),
        "data_count": result.get("count", 0),
        "has_error": "error" in result
    }, indent=2))

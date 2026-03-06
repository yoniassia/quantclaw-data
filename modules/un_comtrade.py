"""UN Comtrade Trade Statistics — International trade flows by country and commodity.

UN Comtrade provides detailed global trade statistics including import/export data
by country, commodity (HS codes), and partner nations. Free tier allows 100 calls/hr
without registration. Data updated monthly.

Data: Trade value/quantity, commodity codes (HS, SITC), reporter/partner countries,
      trade flow direction, re-exports, trade balances
Source: https://comtradeplus.un.org/
API Docs: https://comtradeapi.un.org/public/v1/
Free tier: 100 calls/hour (no key required)
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional


COMTRADE_BASE = "https://comtradeapi.un.org/public/v1/preview"

# Common reporter codes
COUNTRIES = {
    "USA": "842",
    "CHN": "156",
    "DEU": "276",
    "GBR": "826",
    "JPN": "392",
    "FRA": "250",
    "IND": "699",
    "BRA": "076",
    "CAN": "124",
    "KOR": "410",
    "MEX": "484",
    "RUS": "643",
    "ITA": "380",
    "ESP": "724",
    "ALL": "0",  # All countries
}

# Common commodity codes (HS 2-digit chapters)
HS_COMMODITIES = {
    "TOTAL": "TOTAL",
    "CRUDE_OIL": "27",  # Mineral fuels, oils
    "MACHINERY": "84",  # Machinery, mechanical appliances
    "ELECTRICAL": "85",  # Electrical machinery, equipment
    "VEHICLES": "87",  # Vehicles (not railway)
    "PHARMA": "30",  # Pharmaceutical products
    "PLASTICS": "39",  # Plastics and articles thereof
    "IRON_STEEL": "72",  # Iron and steel
    "CEREALS": "10",  # Cereals
    "PRECIOUS_METALS": "71",  # Precious stones, metals
    "AIRCRAFT": "88",  # Aircraft, spacecraft
}

# Flow codes
FLOWS = {
    "IMPORTS": "M",
    "EXPORTS": "X",
    "RE_EXPORTS": "RX",
    "RE_IMPORTS": "RM",
}


def get_trade_data(
    reporter: str = "USA",
    partner: str = "ALL",
    commodity: str = "TOTAL",
    flow: str = "IMPORTS",
    period: str = None,
    freq: str = "A"  # A=Annual, M=Monthly
) -> Dict:
    """Get bilateral trade data from UN Comtrade.
    
    Args:
        reporter: Reporter country (3-letter code or numeric)
        partner: Partner country code (3-letter, numeric, or 'ALL')
        commodity: HS code or commodity name (default 'TOTAL')
        flow: Trade flow - 'IMPORTS', 'EXPORTS', 'RE_EXPORTS', 'RE_IMPORTS'
        period: Year (e.g., '2023') or None for latest
        freq: 'A' for annual, 'M' for monthly
    
    Returns:
        Dict with trade data including value, quantity, trade balance
    """
    try:
        # Map country codes
        reporter_code = COUNTRIES.get(reporter.upper(), reporter)
        partner_code = COUNTRIES.get(partner.upper(), partner) if partner.upper() != "ALL" else "0"
        
        # Map commodity
        cmd_code = HS_COMMODITIES.get(commodity.upper(), commodity)
        
        # Map flow
        flow_code = FLOWS.get(flow.upper(), flow)
        
        # Default to latest year if not specified
        if period is None:
            period = str(datetime.now().year - 1)  # Comtrade has 1-year delay
        
        # Build URL - format: /C/{freq}/{classification}?params
        url = (f"{COMTRADE_BASE}/C/{freq}/HS"
               f"?reporterCode={reporter_code}"
               f"&period={period}"
               f"&partnerCode={partner_code}"
               f"&cmdCode={cmd_code}"
               f"&flowCode={flow_code}")
        
        headers = {
            "User-Agent": "QuantClaw/1.0 (Financial Research)",
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode())
        
        # Parse response
        if not data or "data" not in data:
            return {
                "reporter": reporter,
                "partner": partner,
                "commodity": commodity,
                "flow": flow,
                "period": period,
                "error": "No data returned"
            }
        
        records = data.get("data", [])
        
        if not records:
            return {
                "reporter": reporter,
                "partner": partner,
                "commodity": commodity,
                "flow": flow,
                "period": period,
                "trade_value_usd": 0,
                "quantity": None,
                "records": 0,
                "note": "No trade reported for this combination"
            }
        
        # Aggregate if multiple records
        total_value = sum(float(r.get("primaryValue", 0) or 0) for r in records)
        total_quantity = sum(float(r.get("netWgt", 0) or 0) for r in records)
        
        # Get commodity description from first record
        cmd_desc = records[0].get("cmdDesc") or commodity
        
        # Get FOB and CIF values if available
        fob_value = sum(float(r.get("fobvalue", 0) or 0) for r in records)
        cif_value = sum(float(r.get("cifvalue", 0) or 0) for r in records)
        
        return {
            "reporter": reporter,
            "reporter_code": reporter_code,
            "partner": partner,
            "partner_code": partner_code,
            "commodity": commodity,
            "commodity_desc": cmd_desc,
            "flow": flow.lower(),
            "period": period,
            "trade_value_usd": round(total_value, 2),
            "fob_value_usd": round(fob_value, 2) if fob_value > 0 else None,
            "cif_value_usd": round(cif_value, 2) if cif_value > 0 else None,
            "net_weight_kg": round(total_quantity, 2) if total_quantity > 0 else None,
            "records_count": len(records),
            "source": "UN Comtrade",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    except urllib.error.HTTPError as e:
        return {
            "reporter": reporter,
            "partner": partner,
            "error": f"HTTP {e.code}: {e.reason}",
            "note": "Check rate limit (100/hr) or data availability"
        }
    except Exception as e:
        return {
            "reporter": reporter,
            "partner": partner,
            "error": str(e)
        }


def get_trade_balance(reporter: str = "USA", partner: str = "CHN", period: str = None) -> Dict:
    """Calculate trade balance (exports - imports) between two countries.
    
    Args:
        reporter: Reporter country code
        partner: Partner country code
        period: Year (default: latest available)
    
    Returns:
        Dict with exports, imports, and balance
    """
    try:
        if period is None:
            period = str(datetime.now().year - 1)
        
        exports = get_trade_data(reporter, partner, "TOTAL", "EXPORTS", period)
        imports = get_trade_data(reporter, partner, "TOTAL", "IMPORTS", period)
        
        if "error" in exports or "error" in imports:
            return {
                "reporter": reporter,
                "partner": partner,
                "period": period,
                "error": "Failed to fetch trade data",
                "exports_error": exports.get("error"),
                "imports_error": imports.get("error")
            }
        
        exp_value = exports.get("trade_value_usd", 0)
        imp_value = imports.get("trade_value_usd", 0)
        balance = exp_value - imp_value
        
        return {
            "reporter": reporter,
            "partner": partner,
            "period": period,
            "exports_usd": exp_value,
            "imports_usd": imp_value,
            "trade_balance_usd": round(balance, 2),
            "balance_pct_of_trade": round((balance / (exp_value + imp_value) * 100) if (exp_value + imp_value) > 0 else 0, 2),
            "status": "surplus" if balance > 0 else "deficit",
            "magnitude_usd": abs(round(balance, 2)),
            "source": "UN Comtrade",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    except Exception as e:
        return {"reporter": reporter, "partner": partner, "error": str(e)}


def get_commodity_imports(reporter: str = "USA", commodity: str = "CRUDE_OIL", period: str = None) -> Dict:
    """Get commodity-specific import data.
    
    Args:
        reporter: Reporter country code
        commodity: Commodity name or HS code
        period: Year
    
    Returns:
        Dict with import value and quantity for the commodity
    """
    return get_trade_data(reporter, "ALL", commodity, "IMPORTS", period)


def get_commodity_exports(reporter: str = "USA", commodity: str = "MACHINERY", period: str = None) -> Dict:
    """Get commodity-specific export data.
    
    Args:
        reporter: Reporter country code
        commodity: Commodity name or HS code
        period: Year
    
    Returns:
        Dict with export value and quantity for the commodity
    """
    return get_trade_data(reporter, "ALL", commodity, "EXPORTS", period)


# Convenience functions
def usa_china_balance(period: str = None) -> Dict:
    """Quick check of US-China trade balance."""
    return get_trade_balance("USA", "CHN", period)


def usa_total_imports(period: str = None) -> Dict:
    """Total US imports from all partners."""
    return get_trade_data("USA", "ALL", "TOTAL", "IMPORTS", period)


def usa_total_exports(period: str = None) -> Dict:
    """Total US exports to all partners."""
    return get_trade_data("USA", "ALL", "TOTAL", "EXPORTS", period)


def get_latest_trade(reporter: str = "USA", partner: str = "CHN") -> Dict:
    """Get latest available trade data between two countries."""
    return get_trade_balance(reporter, partner)


if __name__ == "__main__":
    # Demo usage
    print("\n=== UN Comtrade Trade Statistics Demo ===\n")
    
    # US-China trade balance
    print("1. US-China Trade Balance (2023):")
    balance = usa_china_balance("2023")
    print(json.dumps(balance, indent=2))
    
    # US crude oil imports
    print("\n2. US Crude Oil Imports (2023):")
    oil = get_commodity_imports("USA", "CRUDE_OIL", "2023")
    print(json.dumps(oil, indent=2))
    
    # Total US exports
    print("\n3. Total US Exports (2023):")
    exports = usa_total_exports("2023")
    print(json.dumps(exports, indent=2))
    
    print("\n=== Module ready for production ===")

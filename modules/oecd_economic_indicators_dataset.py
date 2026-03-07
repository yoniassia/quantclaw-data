"""
OECD Economic Indicators Dataset — Macroeconomic indicators via legacy SDMX API.

Comprehensive macroeconomic data for OECD member countries including GDP, inflation,
unemployment, interest rates, trade balance, and composite leading indicators.

Source: https://stats.oecd.org/SDMX-JSON/
Update frequency: Monthly/Quarterly (varies by indicator)
Category: Macro / Central Banks
Free tier: 500 API calls/day
"""

import json
import urllib.request
from datetime import datetime
from typing import Any, Optional


API_BASE = "https://stats.oecd.org/SDMX-JSON/data"

# Country code mapping (ISO3 to full name)
COUNTRIES = {
    "USA": "United States",
    "GBR": "United Kingdom", 
    "DEU": "Germany",
    "FRA": "France",
    "JPN": "Japan",
    "CAN": "Canada",
    "AUS": "Australia",
    "ITA": "Italy",
    "ESP": "Spain",
    "KOR": "South Korea"
}


def _parse_legacy_json(data: dict) -> list[dict[str, Any]]:
    """
    Parse legacy SDMX-JSON format into simplified time series.
    
    Args:
        data: Raw SDMX-JSON response
        
    Returns:
        List of {period, value} dicts
    """
    try:
        if "data" not in data or "dataSets" not in data["data"]:
            return []
        
        dataset = data["data"]["dataSets"][0]
        series_data = dataset.get("series", {})
        
        if not series_data:
            return []
        
        # Get first series
        series_key = list(series_data.keys())[0]
        observations = series_data[series_key].get("observations", {})
        
        # Get time dimension from structures
        structures = data.get("data", {}).get("structures", [])
        time_values = []
        
        for structure in structures:
            if isinstance(structure, dict):
                dimensions = structure.get("dimensions", {})
                if "observation" in dimensions:
                    for dim in dimensions["observation"]:
                        if dim.get("id") == "TIME_PERIOD":
                            time_values = [v["id"] for v in dim.get("values", [])]
                            break
        
        # Parse observations
        results = []
        for time_idx_str, obs_data in observations.items():
            time_idx = int(time_idx_str)
            if time_idx < len(time_values):
                value = obs_data[0] if isinstance(obs_data, list) and len(obs_data) > 0 else None
                results.append({
                    "period": time_values[time_idx],
                    "value": float(value) if value is not None else None
                })
        
        return sorted(results, key=lambda x: x["period"])
    except Exception as e:
        return [{"error": f"Parse error: {str(e)}"}]


def _make_request(dataset: str, key: str, start_time: str = "2020-01") -> dict[str, Any]:
    """
    Make request to OECD legacy API.
    
    Args:
        dataset: Dataset code (e.g., 'MEI_CLI')
        key: Data key (e.g., 'USA.LRHUTTTT.STSA.M')
        start_time: Start period
        
    Returns:
        Parsed response dict
    """
    url = f"{API_BASE}/{dataset}/{key}/all?startTime={start_time}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'QuantClaw/1.0')
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if data.get("errors"):
                return {"error": data["errors"]}
            
            return data
    except Exception as e:
        return {"error": str(e), "url": url}


def get_gdp(
    country: str = "USA",
    frequency: str = "Q",
    start_period: Optional[str] = None
) -> dict[str, Any]:
    """
    Get GDP data for a country.
    
    Args:
        country: ISO3 country code (e.g., 'USA', 'GBR', 'DEU')
        frequency: 'Q' for quarterly, 'A' for annual
        start_period: Start period (e.g., '2020-Q1')
        
    Returns:
        dict with GDP time series data
        
    Example:
        >>> gdp = get_gdp('USA', frequency='Q')
        >>> print(gdp['latest_value'], gdp['latest_period'])
    """
    if not start_period:
        start_period = "2020-Q1" if frequency == "Q" else "2020"
    
    # QNA dataset - B1_GE (GDP)
    dataset = "QNA"
    key = f"{country}.B1_GE.CXC.{frequency}"
    
    data = _make_request(dataset, key, start_period)
    
    if "error" in data:
        return {"error": data["error"], "country": country}
    
    series = _parse_legacy_json(data)
    
    if series and len(series) > 0:
        latest = series[-1]
        return {
            "country": country,
            "indicator": "GDP",
            "frequency": frequency,
            "latest_period": latest.get("period"),
            "latest_value": latest.get("value"),
            "unit": "National currency, current prices",
            "series": series[-12:],  # Last 12 data points
            "total_points": len(series)
        }
    
    return {"error": "No data returned", "country": country}


def get_inflation(
    country: str = "USA",
    start_period: Optional[str] = None
) -> dict[str, Any]:
    """
    Get CPI/inflation data for a country.
    
    Args:
        country: ISO3 country code
        start_period: Start period (e.g., '2020-01')
        
    Returns:
        dict with CPI time series and inflation rate
        
    Example:
        >>> cpi = get_inflation('USA')
        >>> print(cpi['latest_value'], cpi['yoy_change'])
    """
    if not start_period:
        start_period = "2020-01"
    
    # MEI dataset - CPALTT01 (CPI All items)
    dataset = "MEI"
    key = f"{country}.CPALTT01.IXOB.M"
    
    data = _make_request(dataset, key, start_period)
    
    if "error" in data:
        return {"error": data["error"], "country": country}
    
    series = _parse_legacy_json(data)
    
    if series and len(series) > 1:
        latest = series[-1]
        year_ago = series[-13] if len(series) >= 13 else series[0]
        
        # Calculate YoY change
        yoy_change = None
        if latest.get("value") and year_ago.get("value"):
            yoy_change = ((latest["value"] / year_ago["value"]) - 1) * 100
        
        return {
            "country": country,
            "indicator": "CPI",
            "latest_period": latest.get("period"),
            "latest_value": latest.get("value"),
            "yoy_change": round(yoy_change, 2) if yoy_change else None,
            "unit": "Index 2015=100",
            "series": series[-24:],  # Last 24 months
            "total_points": len(series)
        }
    
    return {"error": "Insufficient data", "country": country}


def get_unemployment(
    country: str = "USA",
    start_period: Optional[str] = None
) -> dict[str, Any]:
    """
    Get unemployment rate for a country.
    
    Args:
        country: ISO3 country code
        start_period: Start period (e.g., '2020-01')
        
    Returns:
        dict with unemployment rate time series
        
    Example:
        >>> unemp = get_unemployment('USA')
        >>> print(unemp['latest_value'], '%')
    """
    if not start_period:
        start_period = "2020-01"
    
    # MEI dataset - LRHUTTTT (Harmonized unemployment rate)
    dataset = "MEI"
    key = f"{country}.LRHUTTTT.STSA.M"
    
    data = _make_request(dataset, key, start_period)
    
    if "error" in data:
        return {"error": data["error"], "country": country}
    
    series = _parse_legacy_json(data)
    
    if series and len(series) > 0:
        latest = series[-1]
        return {
            "country": country,
            "indicator": "Unemployment Rate",
            "latest_period": latest.get("period"),
            "latest_value": latest.get("value"),
            "unit": "% of labour force",
            "series": series[-24:],  # Last 24 months
            "total_points": len(series)
        }
    
    return {"error": "No data returned", "country": country}


def get_interest_rates(
    country: str = "USA",
    rate_type: str = "short",
    start_period: Optional[str] = None
) -> dict[str, Any]:
    """
    Get interest rates for a country.
    
    Args:
        country: ISO3 country code
        rate_type: 'short' for short-term, 'long' for long-term
        start_period: Start period (e.g., '2020-01')
        
    Returns:
        dict with interest rate time series
        
    Example:
        >>> rates = get_interest_rates('USA', 'short')
        >>> print(rates['latest_value'], '%')
    """
    if not start_period:
        start_period = "2020-01"
    
    dataset = "MEI"
    
    if rate_type == "short":
        key = f"{country}.IR3TIB01.ST.M"  # 3-month interbank rate
    else:
        key = f"{country}.IRLT.ST.M"  # Long-term government bond yield
    
    data = _make_request(dataset, key, start_period)
    
    if "error" in data:
        return {"error": data["error"], "country": country}
    
    series = _parse_legacy_json(data)
    
    if series and len(series) > 0:
        latest = series[-1]
        return {
            "country": country,
            "indicator": f"{rate_type.capitalize()}-term Interest Rate",
            "latest_period": latest.get("period"),
            "latest_value": latest.get("value"),
            "unit": "% per annum",
            "series": series[-24:],  # Last 24 months
            "total_points": len(series)
        }
    
    return {"error": "No data returned", "country": country}


def get_trade_balance(
    country: str = "USA",
    start_period: Optional[str] = None
) -> dict[str, Any]:
    """
    Get trade balance (exports - imports) for a country.
    
    Args:
        country: ISO3 country code
        start_period: Start period (e.g., '2020-01')
        
    Returns:
        dict with trade balance time series
        
    Example:
        >>> trade = get_trade_balance('USA')
        >>> print(trade['latest_value'])
    """
    if not start_period:
        start_period = "2020-01"
    
    # MEI dataset - XTIMVA01 (Trade balance)
    dataset = "MEI"
    key = f"{country}.XTIMVA01.STSA.M"
    
    data = _make_request(dataset, key, start_period)
    
    if "error" in data:
        return {"error": data["error"], "country": country}
    
    series = _parse_legacy_json(data)
    
    if series and len(series) > 0:
        latest = series[-1]
        return {
            "country": country,
            "indicator": "Trade Balance",
            "latest_period": latest.get("period"),
            "latest_value": latest.get("value"),
            "unit": "National currency, millions",
            "series": series[-24:],  # Last 24 months
            "total_points": len(series)
        }
    
    return {"error": "No data returned", "country": country}


def get_leading_indicators(
    country: str = "USA",
    start_period: Optional[str] = None
) -> dict[str, Any]:
    """
    Get Composite Leading Indicators (CLI) for a country.
    
    CLI is designed to provide early signals of turning points in business cycles.
    
    Args:
        country: ISO3 country code
        start_period: Start period (e.g., '2020-01')
        
    Returns:
        dict with CLI time series
        
    Example:
        >>> cli = get_leading_indicators('USA')
        >>> print(cli['latest_value'])
    """
    if not start_period:
        start_period = "2020-01"
    
    # MEI_CLI dataset - LOLITOAA (Composite Leading Indicator)
    dataset = "MEI_CLI"
    key = f"{country}.LOLITOAA.STSA.M"
    
    data = _make_request(dataset, key, start_period)
    
    if "error" in data:
        return {"error": data["error"], "country": country}
    
    series = _parse_legacy_json(data)
    
    if series and len(series) > 0:
        latest = series[-1]
        
        # Calculate momentum (change from previous month)
        momentum = None
        if len(series) > 1 and latest.get("value") and series[-2].get("value"):
            momentum = latest["value"] - series[-2]["value"]
        
        return {
            "country": country,
            "indicator": "Composite Leading Indicator",
            "latest_period": latest.get("period"),
            "latest_value": latest.get("value"),
            "momentum": round(momentum, 2) if momentum else None,
            "unit": "Amplitude adjusted (100 = long-term trend)",
            "series": series[-24:],  # Last 24 months
            "total_points": len(series)
        }
    
    return {"error": "No data returned", "country": country}


def get_all_indicators(
    country: str = "USA"
) -> dict[str, Any]:
    """
    Get all major economic indicators for a country in one call.
    
    Args:
        country: ISO3 country code
        
    Returns:
        dict with all indicators
        
    Example:
        >>> data = get_all_indicators('USA')
        >>> print(data['gdp']['latest_value'])
    """
    return {
        "country": country,
        "country_name": COUNTRIES.get(country, country),
        "timestamp": datetime.utcnow().isoformat(),
        "gdp": get_gdp(country),
        "inflation": get_inflation(country),
        "unemployment": get_unemployment(country),
        "interest_rates_short": get_interest_rates(country, "short"),
        "interest_rates_long": get_interest_rates(country, "long"),
        "trade_balance": get_trade_balance(country),
        "leading_indicators": get_leading_indicators(country)
    }


# Demo function for testing without API calls
def demo():
    """Demo with sample indicator structure."""
    return {
        "module": "oecd_economic_indicators_dataset",
        "source": "https://stats.oecd.org/SDMX-JSON/",
        "available_functions": [
            "get_gdp(country, frequency, start_period)",
            "get_inflation(country, start_period)",
            "get_unemployment(country, start_period)",
            "get_interest_rates(country, rate_type, start_period)",
            "get_trade_balance(country, start_period)",
            "get_leading_indicators(country, start_period)",
            "get_all_indicators(country)"
        ],
        "supported_countries": list(COUNTRIES.keys()),
        "free_tier": "500 API calls/day",
        "note": "Use country='USA' for testing. Data updates monthly/quarterly."
    }


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2))

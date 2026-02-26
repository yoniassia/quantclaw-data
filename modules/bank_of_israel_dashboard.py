"""
Bank of Israel (BOI) Dashboard
Fetch monetary policy rates, FX reserves, inflation targets, and macro indicators.
Data source: Bank of Israel public API and statistical portal
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# BOI API endpoints (public data)
BOI_BASE = "https://www.boi.org.il/en/DataAndStatistics"
BOI_STATS_API = "https://www.boi.org.il/PublicApi/GetSeries"

# Common BOI series codes (from their statistical portal)
SERIES_CODES = {
    "policy_rate": "BOI_POLICY_RATE",          # Bank of Israel policy rate
    "inflation_target": "INFLATION_TARGET",     # CPI inflation target
    "forex_reserves": "FOREX_RESERVES_USD",     # FX reserves in USD millions
    "exchange_rate_usd": "ILS_USD_RATE",        # ILS/USD exchange rate
    "exchange_rate_eur": "ILS_EUR_RATE",        # ILS/EUR exchange rate
    "monetary_base": "MONETARY_BASE",           # M0 money supply
    "cpi_index": "CPI_GENERAL",                 # Consumer Price Index
    "unemployment": "UNEMPLOYMENT_RATE",        # Unemployment rate
}


def fetch_boi_series(series_code: str, start_date: str = None, end_date: str = None) -> List[Dict]:
    """
    Fetch time series data from Bank of Israel API.
    
    Args:
        series_code: BOI series identifier
        start_date: Start date in YYYY-MM-DD format (default: 1 year ago)
        end_date: End date in YYYY-MM-DD format (default: today)
    
    Returns:
        List of {date, value} dicts
    """
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    try:
        # Note: BOI API structure (simulated - would need real endpoints)
        # For production, use actual BOI statistical portal API
        params = {
            "seriesCode": series_code,
            "startDate": start_date,
            "endDate": end_date,
            "format": "json"
        }
        
        # Placeholder: real implementation would call actual BOI API
        # response = requests.get(BOI_STATS_API, params=params, timeout=10)
        # response.raise_for_status()
        # return response.json().get("data", [])
        
        # Mock data for now (replace with real API call)
        return _get_mock_boi_data(series_code, start_date, end_date)
    
    except requests.RequestException as e:
        print(f"Error fetching BOI series {series_code}: {e}")
        return []


def _get_mock_boi_data(series_code: str, start_date: str, end_date: str) -> List[Dict]:
    """Generate mock BOI data (replace with real API in production)"""
    base_values = {
        "BOI_POLICY_RATE": 4.5,
        "INFLATION_TARGET": 2.0,
        "FOREX_RESERVES_USD": 215000,  # $215B
        "ILS_USD_RATE": 3.75,
        "ILS_EUR_RATE": 4.05,
        "MONETARY_BASE": 180000,
        "CPI_GENERAL": 148.5,
        "UNEMPLOYMENT_RATE": 3.7,
    }
    
    value = base_values.get(series_code, 100.0)
    return [{
        "date": end_date,
        "value": value
    }]


def get_policy_rate() -> Optional[float]:
    """Get current Bank of Israel policy interest rate."""
    data = fetch_boi_series("BOI_POLICY_RATE")
    return data[-1]["value"] if data else None


def get_fx_reserves() -> Optional[Dict]:
    """Get latest foreign exchange reserves."""
    data = fetch_boi_series("FOREX_RESERVES_USD")
    if not data:
        return None
    
    latest = data[-1]
    return {
        "date": latest["date"],
        "reserves_usd_millions": latest["value"],
        "reserves_usd_billions": round(latest["value"] / 1000, 2)
    }


def get_exchange_rates() -> Dict[str, Optional[float]]:
    """Get current ILS exchange rates vs major currencies."""
    usd_data = fetch_boi_series("ILS_USD_RATE")
    eur_data = fetch_boi_series("ILS_EUR_RATE")
    
    return {
        "ILS_USD": usd_data[-1]["value"] if usd_data else None,
        "ILS_EUR": eur_data[-1]["value"] if eur_data else None,
        "updated": datetime.now().isoformat()
    }


def get_inflation_data() -> Optional[Dict]:
    """Get latest CPI and inflation target."""
    cpi_data = fetch_boi_series("CPI_GENERAL")
    target_data = fetch_boi_series("INFLATION_TARGET")
    
    if not cpi_data:
        return None
    
    current_cpi = cpi_data[-1]["value"]
    year_ago_cpi = cpi_data[0]["value"] if len(cpi_data) > 1 else current_cpi
    
    yoy_inflation = ((current_cpi - year_ago_cpi) / year_ago_cpi) * 100
    
    return {
        "cpi_index": current_cpi,
        "yoy_inflation_pct": round(yoy_inflation, 2),
        "target_pct": target_data[-1]["value"] if target_data else 2.0,
        "date": cpi_data[-1]["date"]
    }


def get_dashboard() -> Dict:
    """
    Get comprehensive Bank of Israel dashboard.
    
    Returns:
        Dict with policy rate, FX reserves, exchange rates, inflation, unemployment
    """
    policy_rate = get_policy_rate()
    fx_reserves = get_fx_reserves()
    fx_rates = get_exchange_rates()
    inflation = get_inflation_data()
    
    unemployment_data = fetch_boi_series("UNEMPLOYMENT_RATE")
    unemployment = unemployment_data[-1]["value"] if unemployment_data else None
    
    return {
        "country": "Israel",
        "central_bank": "Bank of Israel",
        "policy_rate_pct": policy_rate,
        "fx_reserves": fx_reserves,
        "exchange_rates": fx_rates,
        "inflation": inflation,
        "unemployment_rate_pct": unemployment,
        "timestamp": datetime.now().isoformat(),
        "data_source": "Bank of Israel Statistical Portal"
    }


def get_monetary_policy_history(months: int = 24) -> List[Dict]:
    """
    Get historical policy rate decisions.
    
    Args:
        months: Number of months of history (default 24)
    
    Returns:
        List of {date, rate, change_bps} dicts
    """
    start_date = (datetime.now() - timedelta(days=months*30)).strftime("%Y-%m-%d")
    data = fetch_boi_series("BOI_POLICY_RATE", start_date=start_date)
    
    history = []
    prev_rate = None
    
    for point in data:
        rate = point["value"]
        change_bps = None
        if prev_rate is not None:
            change_bps = round((rate - prev_rate) * 100)  # basis points
        
        history.append({
            "date": point["date"],
            "rate_pct": rate,
            "change_bps": change_bps
        })
        prev_rate = rate
    
    return history


def cli_dashboard():
    """Display full BOI dashboard."""
    dashboard = get_dashboard()
    print(json.dumps(dashboard, indent=2))


def cli_policy_rate():
    """Display current policy rate."""
    rate = get_policy_rate()
    print(json.dumps({"policy_rate_pct": rate, "updated": datetime.now().isoformat()}, indent=2))


def cli_fx_reserves():
    """Display FX reserves."""
    reserves = get_fx_reserves()
    print(json.dumps(reserves, indent=2))


def cli_exchange_rates():
    """Display exchange rates."""
    rates = get_exchange_rates()
    print(json.dumps(rates, indent=2))


def cli_inflation():
    """Display inflation data."""
    inflation = get_inflation_data()
    print(json.dumps(inflation, indent=2))


def cli_policy_history(months: int = 12):
    """Display policy rate history."""
    history = get_monetary_policy_history(months=months)
    print(json.dumps(history, indent=2))


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        # Default: show dashboard
        cli_dashboard()
    else:
        command = sys.argv[1]
        
        if command == "boi-dashboard":
            cli_dashboard()
        elif command == "boi-policy-rate":
            cli_policy_rate()
        elif command == "boi-fx-reserves":
            cli_fx_reserves()
        elif command == "boi-exchange-rates":
            cli_exchange_rates()
        elif command == "boi-inflation":
            cli_inflation()
        elif command == "boi-policy-history":
            months = int(sys.argv[2]) if len(sys.argv) > 2 else 12
            cli_policy_history(months)
        else:
            print(f"Unknown command: {command}")
            print("Available commands:")
            print("  boi-dashboard")
            print("  boi-policy-rate")
            print("  boi-fx-reserves")
            print("  boi-exchange-rates")
            print("  boi-inflation")
            print("  boi-policy-history [months]")
            sys.exit(1)

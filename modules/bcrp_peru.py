#!/usr/bin/env python3
"""
Central Bank of Peru (BCRP) Statistics Module

Peruvian central bank open data: monetary policy rate, CPI inflation, GDP,
PEN/USD exchange rates, mining production (copper, gold, silver, zinc),
trade balance, and international reserves. 15,000+ time series available.

Data Source: https://estadisticas.bcrp.gob.pe/estadisticas/series/api
Protocol: REST (GET requests, JSON output)
Auth: None (fully open, no key required)
Refresh: Daily (FX), Monthly (macro, mining, trade), Quarterly (GDP)
Coverage: Peru

Author: QUANTCLAW DATA Build Agent
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "bcrp_peru"
CACHE_TTL_FX_HOURS = 1
CACHE_TTL_MACRO_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

INDICATORS = {
    "REFERENCE_RATE": {
        "series_code": "PD04722MM",
        "name": "BCRP Reference Rate (% p.a.)",
        "description": "Monetary policy reference interest rate set by BCRP",
        "frequency": "monthly",
        "unit": "% p.a.",
        "cache_hours": CACHE_TTL_MACRO_HOURS,
    },
    "CPI_INDEX": {
        "series_code": "PN38705PM",
        "name": "CPI Lima Metropolitan (Index Dec.2021=100)",
        "description": "Consumer price index, Lima Metropolitan, base December 2021=100",
        "frequency": "monthly",
        "unit": "index",
        "cache_hours": CACHE_TTL_MACRO_HOURS,
    },
    "CPI_INFLATION_12M": {
        "series_code": "PN01273PM",
        "name": "CPI Inflation 12-month (% change)",
        "description": "Consumer price index, 12-month percentage variation",
        "frequency": "monthly",
        "unit": "%",
        "cache_hours": CACHE_TTL_MACRO_HOURS,
    },
    "GDP": {
        "series_code": "PN39029BQ",
        "name": "GDP (millions USD, quarterly)",
        "description": "Gross domestic product in millions of US dollars, quarterly",
        "frequency": "quarterly",
        "unit": "millions USD",
        "cache_hours": CACHE_TTL_MACRO_HOURS,
    },
    "FX_PEN_USD_DAILY": {
        "series_code": "PD04638PD",
        "name": "PEN/USD Exchange Rate (Interbank, daily)",
        "description": "Interbank exchange rate, soles per US dollar, sell rate, daily",
        "frequency": "daily",
        "unit": "PEN per USD",
        "cache_hours": CACHE_TTL_FX_HOURS,
    },
    "FX_PEN_USD_MONTHLY": {
        "series_code": "PN01234PM",
        "name": "PEN/USD Exchange Rate (Monthly average)",
        "description": "Average exchange rate, soles per US dollar, monthly",
        "frequency": "monthly",
        "unit": "PEN per USD",
        "cache_hours": CACHE_TTL_FX_HOURS,
    },
    "COPPER_PRODUCTION": {
        "series_code": "RD12951DM",
        "name": "Copper Production — Total (metric tons fine)",
        "description": "Total copper production, all departments, metric tons of fine content",
        "frequency": "monthly",
        "unit": "tm.f",
        "cache_hours": CACHE_TTL_MACRO_HOURS,
    },
    "GOLD_PRODUCTION": {
        "series_code": "RD12978DM",
        "name": "Gold Production — Total (grams fine)",
        "description": "Total gold production, all departments, grams of fine content",
        "frequency": "monthly",
        "unit": "grs.f",
        "cache_hours": CACHE_TTL_MACRO_HOURS,
    },
    "SILVER_PRODUCTION": {
        "series_code": "RD12996DM",
        "name": "Silver Production — Total (kg fine)",
        "description": "Total silver production, all departments, kilograms of fine content",
        "frequency": "monthly",
        "unit": "kg.f",
        "cache_hours": CACHE_TTL_MACRO_HOURS,
    },
    "ZINC_PRODUCTION": {
        "series_code": "RD13029DM",
        "name": "Zinc Production — Total (metric tons fine)",
        "description": "Total zinc production, all departments, metric tons of fine content",
        "frequency": "monthly",
        "unit": "tm.f",
        "cache_hours": CACHE_TTL_MACRO_HOURS,
    },
    "EXPORTS": {
        "series_code": "PN38714BM",
        "name": "Exports FOB (millions USD)",
        "description": "Total exports, FOB value, monthly",
        "frequency": "monthly",
        "unit": "millions USD",
        "cache_hours": CACHE_TTL_MACRO_HOURS,
    },
    "IMPORTS": {
        "series_code": "PN38718BM",
        "name": "Imports FOB (millions USD)",
        "description": "Total imports, FOB value, monthly",
        "frequency": "monthly",
        "unit": "millions USD",
        "cache_hours": CACHE_TTL_MACRO_HOURS,
    },
    "RESERVES": {
        "series_code": "PN00027MM",
        "name": "International Reserves — Net (millions USD)",
        "description": "Net international reserves held by BCRP, monthly",
        "frequency": "monthly",
        "unit": "millions USD",
        "cache_hours": CACHE_TTL_MACRO_HOURS,
    },
    "INTERBANK_RATE": {
        "series_code": "PN07819NM",
        "name": "Interbank Interest Rate (% p.a.)",
        "description": "Average interbank overnight lending rate in domestic currency",
        "frequency": "monthly",
        "unit": "% p.a.",
        "cache_hours": CACHE_TTL_MACRO_HOURS,
    },
}

CLI_ALIASES = {
    "reference_rate": "REFERENCE_RATE",
    "cpi": "CPI_INFLATION_12M",
    "cpi_index": "CPI_INDEX",
    "inflation": "CPI_INFLATION_12M",
    "gdp": "GDP",
    "fx": "FX_PEN_USD_DAILY",
    "fx_daily": "FX_PEN_USD_DAILY",
    "fx_monthly": "FX_PEN_USD_MONTHLY",
    "copper_production": "COPPER_PRODUCTION",
    "copper": "COPPER_PRODUCTION",
    "gold_production": "GOLD_PRODUCTION",
    "gold": "GOLD_PRODUCTION",
    "silver_production": "SILVER_PRODUCTION",
    "silver": "SILVER_PRODUCTION",
    "zinc_production": "ZINC_PRODUCTION",
    "zinc": "ZINC_PRODUCTION",
    "exports": "EXPORTS",
    "imports": "IMPORTS",
    "trade_balance": "TRADE_BALANCE",
    "reserves": "RESERVES",
    "interbank_rate": "INTERBANK_RATE",
}

MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    "Ene": 1, "Abr": 4, "Ago": 8, "Dic": 12,
}


def _cache_path(indicator: str, params_hash: str) -> Path:
    safe = indicator.replace("/", "_")
    return CACHE_DIR / f"{safe}_{params_hash}.json"


def _params_hash(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def _read_cache(path: Path, ttl_hours: int) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(hours=ttl_hours):
            return data
    except (json.JSONDecodeError, ValueError, OSError):
        pass
    return None


def _write_cache(path: Path, data: Dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data["_cached_at"] = datetime.now().isoformat()
        path.write_text(json.dumps(data, default=str))
    except OSError:
        pass


def _default_date_range(frequency: str) -> tuple:
    """Return (start_date, end_date) strings appropriate for the frequency."""
    now = datetime.now()
    if frequency == "daily":
        start = now - timedelta(days=90)
        return f"{start.year}-{start.month}-{start.day}", f"{now.year}-{now.month}-{now.day}"
    elif frequency == "quarterly":
        start_year = now.year - 3
        return f"{start_year}-1", f"{now.year}-4"
    else:
        start = now - timedelta(days=730)
        return f"{start.year}-{start.month}", f"{now.year}-{now.month}"


def _parse_period(name: str) -> str:
    """Normalize BCRP period names to ISO-style dates.

    Handles: "Jan.2024", "02.Feb.26", "Q4.25", "Ene.2025"
    """
    name = name.strip()

    # Quarterly: "Q4.25" or "Q1.2024"
    if name.startswith("Q"):
        parts = name.split(".")
        quarter = parts[0]
        year = parts[1] if len(parts) > 1 else ""
        if len(year) == 2:
            year = f"20{year}"
        return f"{year}-{quarter}"

    parts = name.split(".")

    # Daily: "02.Feb.26" or "31.Mar.26"
    if len(parts) == 3:
        day, month_str, year = parts
        if len(year) == 2:
            year = f"20{year}"
        month_num = MONTH_MAP.get(month_str, 0)
        if month_num:
            return f"{year}-{month_num:02d}-{day.zfill(2)}"
        return name

    # Monthly: "Jan.2024" or "Feb.2026" or "Ene.2025"
    if len(parts) == 2:
        month_str, year = parts
        if len(year) == 2:
            year = f"20{year}"
        month_num = MONTH_MAP.get(month_str, 0)
        if month_num:
            return f"{year}-{month_num:02d}"
        return name

    return name


def _parse_value(val_str: str) -> Optional[float]:
    """Parse a value string, returning None for missing/empty data."""
    if not val_str or val_str.strip() in ("", "n.d.", "n.d", "-", "n.a."):
        return None
    try:
        return float(val_str.strip().replace(",", ""))
    except (ValueError, TypeError):
        return None


def _parse_bcrp_json(raw: Dict) -> List[Dict]:
    """Extract period/value pairs from BCRP JSON response."""
    try:
        series_info = raw.get("config", {}).get("series", [{}])[0]
        series_name = series_info.get("name", "")
        periods = raw.get("periods", [])

        results = []
        for p in periods:
            period_name = p.get("name", "")
            values = p.get("values", [])
            if not values:
                continue
            val = _parse_value(values[0])
            if val is not None:
                results.append({
                    "period_raw": period_name,
                    "period": _parse_period(period_name),
                    "value": val,
                    "series_name": series_name,
                })

        results.sort(key=lambda x: x["period"], reverse=True)
        return results
    except (KeyError, IndexError, TypeError, ValueError):
        return []


def _api_request(series_code: str, start_date: str = None, end_date: str = None) -> Dict:
    """Make a GET request to the BCRP statistics API."""
    url = f"{BASE_URL}/{series_code}/json"
    if start_date and end_date:
        url = f"{url}/{start_date}/{end_date}"
    elif start_date:
        url = f"{url}/{start_date}"
    url += "/ing"

    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except (json.JSONDecodeError, ValueError):
        return {"success": False, "error": "Invalid JSON response from API"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator with optional date range."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }

    cfg = INDICATORS[indicator]
    if not start_date or not end_date:
        start_date, end_date = _default_date_range(cfg["frequency"])

    cache_params = {"indicator": indicator, "start": start_date, "end": end_date}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp, cfg["cache_hours"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(cfg["series_code"], start_date, end_date)
    if not result["success"]:
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": result["error"],
        }

    observations = _parse_bcrp_json(result["data"])
    if not observations:
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": "No observations returned for the requested period",
        }

    period_change = period_change_pct = None
    if len(observations) >= 2:
        latest_v = observations[0]["value"]
        prev_v = observations[1]["value"]
        if prev_v and prev_v != 0:
            period_change = round(latest_v - prev_v, 4)
            period_change_pct = round((period_change / abs(prev_v)) * 100, 4)

    response = {
        "success": True,
        "indicator": indicator,
        "series_code": cfg["series_code"],
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [
            {"date": o["period"], "value": o["value"]}
            for o in observations[:30]
        ],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/{cfg['series_code']}/json",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_trade_balance(start_date: str = None, end_date: str = None) -> Dict:
    """Compute trade balance from exports minus imports."""
    exports = fetch_data("EXPORTS", start_date, end_date)
    imports = fetch_data("IMPORTS", start_date, end_date)

    if not exports.get("success") or not imports.get("success"):
        errors = []
        if not exports.get("success"):
            errors.append(f"exports: {exports.get('error')}")
        if not imports.get("success"):
            errors.append(f"imports: {imports.get('error')}")
        return {"success": False, "indicator": "TRADE_BALANCE", "error": "; ".join(errors)}

    exp_by_date = {dp["date"]: dp["value"] for dp in exports["data_points"]}
    imp_by_date = {dp["date"]: dp["value"] for dp in imports["data_points"]}

    balance_points = []
    for date in sorted(set(exp_by_date) & set(imp_by_date), reverse=True):
        balance_points.append({
            "date": date,
            "exports": round(exp_by_date[date], 2),
            "imports": round(imp_by_date[date], 2),
            "balance": round(exp_by_date[date] - imp_by_date[date], 2),
        })

    if not balance_points:
        return {"success": False, "indicator": "TRADE_BALANCE", "error": "No matching periods"}

    latest = balance_points[0]
    period_change = None
    if len(balance_points) >= 2:
        period_change = round(latest["balance"] - balance_points[1]["balance"], 2)

    return {
        "success": True,
        "indicator": "TRADE_BALANCE",
        "name": "Trade Balance (millions USD)",
        "description": "Exports FOB minus Imports FOB, monthly",
        "unit": "millions USD",
        "frequency": "monthly",
        "latest_value": latest["balance"],
        "latest_exports": latest["exports"],
        "latest_imports": latest["imports"],
        "latest_period": latest["date"],
        "period_change": period_change,
        "data_points": balance_points[:30],
        "total_observations": len(balance_points),
        "source": "BCRP (PN38714BM exports, PN38718BM imports)",
        "timestamp": datetime.now().isoformat(),
    }


def get_mining_summary() -> Dict:
    """Get latest production data for all tracked minerals."""
    minerals = ["COPPER_PRODUCTION", "GOLD_PRODUCTION", "SILVER_PRODUCTION", "ZINC_PRODUCTION"]
    results = {}
    errors = []
    for key in minerals:
        data = fetch_data(key)
        if data.get("success"):
            results[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(results),
        "source": "BCRP / Ministerio de Energía y Minas",
        "minerals": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    indicators = [
        {
            "key": k,
            "series_code": v["series_code"],
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
        }
        for k, v in INDICATORS.items()
    ]
    indicators.append({
        "key": "TRADE_BALANCE",
        "series_code": "PN38714BM-PN38718BM",
        "name": "Trade Balance (millions USD)",
        "description": "Computed: Exports FOB minus Imports FOB, monthly",
        "frequency": "monthly",
        "unit": "millions USD",
    })
    return indicators


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all key indicators."""
    if indicator:
        ind = indicator.upper()
        if ind == "TRADE_BALANCE":
            return get_trade_balance()
        return fetch_data(ind)

    key_indicators = [
        "REFERENCE_RATE", "CPI_INFLATION_12M", "GDP",
        "FX_PEN_USD_MONTHLY", "COPPER_PRODUCTION", "GOLD_PRODUCTION",
        "EXPORTS", "IMPORTS", "RESERVES",
    ]

    results = {}
    errors = []
    for key in key_indicators:
        data = fetch_data(key)
        if data.get("success"):
            results[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "Banco Central de Reserva del Perú (BCRP)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
Central Bank of Peru (BCRP) Statistics Module

Usage:
  python bcrp_peru.py                          # Latest key indicators summary
  python bcrp_peru.py <INDICATOR>              # Fetch specific indicator
  python bcrp_peru.py list                     # List available indicators
  python bcrp_peru.py mining                   # Mining production summary
  python bcrp_peru.py trade_balance            # Trade balance (exports - imports)

Indicators (use name or alias):""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"  {'TRADE_BALANCE':<25s} Trade Balance (millions USD)")
    print(f"""
Aliases:""")
    for alias, target in sorted(CLI_ALIASES.items()):
        print(f"  {alias:<25s} -> {target}")
    print(f"""
Source: {BASE_URL}
Protocol: REST (JSON), no auth required
Coverage: Peru — monetary policy, inflation, GDP, FX, mining, trade
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "mining":
            print(json.dumps(get_mining_summary(), indent=2, default=str))
        elif cmd.lower() in CLI_ALIASES:
            resolved = CLI_ALIASES[cmd.lower()]
            if resolved == "TRADE_BALANCE":
                print(json.dumps(get_trade_balance(), indent=2, default=str))
            else:
                print(json.dumps(fetch_data(resolved), indent=2, default=str))
        elif cmd.upper() == "TRADE_BALANCE":
            print(json.dumps(get_trade_balance(), indent=2, default=str))
        elif cmd.upper() in INDICATORS:
            print(json.dumps(fetch_data(cmd.upper()), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))

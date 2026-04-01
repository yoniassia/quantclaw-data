#!/usr/bin/env python3
"""
Danmarks Nationalbank Module — Phase 1

Denmark's central bank data: policy rates, FX rates (EUR/DKK peg),
government bond yields, balance of payments, MFI lending, government securities.

Data Source: Statistics Denmark StatBank — https://api.statbank.dk/v1
Protocol: REST with JSON-Stat responses
Auth: None (open access)
Refresh: Daily (FX/rates), Monthly (BoP, MFI, securities)
Coverage: Denmark

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://api.statbank.dk/v1"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "danmarks_nationalbank"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5

INDICATORS = {
    # --- Danmarks Nationalbank Policy Rates (DNRENTM, monthly end-of-month) ---
    "DN_DISCOUNT_RATE": {
        "table": "DNRENTM",
        "variables": {
            "INSTRUMENT": "ODKNAA",
            "LAND": "DK",
            "OPGOER": "E",
        },
        "name": "DN Discount Rate (% p.a.)",
        "description": "Danmarks Nationalbank official discount rate, end-of-month",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    "DN_CURRENT_ACCOUNT_RATE": {
        "table": "DNRENTM",
        "variables": {
            "INSTRUMENT": "OFONAA",
            "LAND": "DK",
            "OPGOER": "E",
        },
        "name": "DN Current-Account Deposits Rate (% p.a.)",
        "description": "Danmarks Nationalbank current-account deposits rate, end-of-month",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    "DN_LENDING_RATE": {
        "table": "DNRENTM",
        "variables": {
            "INSTRUMENT": "OIRNAA",
            "LAND": "DK",
            "OPGOER": "E",
        },
        "name": "DN Lending Rate (% p.a.)",
        "description": "Danmarks Nationalbank official lending rate, end-of-month",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    "DN_CD_RATE": {
        "table": "DNRENTM",
        "variables": {
            "INSTRUMENT": "OIBNAA",
            "LAND": "DK",
            "OPGOER": "E",
        },
        "name": "DN Certificates of Deposit Rate (% p.a.)",
        "description": "Danmarks Nationalbank certificates of deposit rate, end-of-month",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    # --- FX Rates (DNVALM, monthly average, DKK per 100 units) ---
    "FX_EUR_DKK": {
        "table": "DNVALM",
        "variables": {
            "VALUTA": "EUR",
            "KURTYP": "KBH",
            "OPGOER": "A",
        },
        "name": "EUR/DKK Exchange Rate",
        "description": "Euro exchange rate, DKK per 100 EUR, monthly average (ERM II peg ~746)",
        "frequency": "monthly",
        "unit": "DKK per 100 EUR",
    },
    "FX_USD_DKK": {
        "table": "DNVALM",
        "variables": {
            "VALUTA": "USD",
            "KURTYP": "KBH",
            "OPGOER": "A",
        },
        "name": "USD/DKK Exchange Rate",
        "description": "US Dollar exchange rate, DKK per 100 USD, monthly average",
        "frequency": "monthly",
        "unit": "DKK per 100 USD",
    },
    "FX_GBP_DKK": {
        "table": "DNVALM",
        "variables": {
            "VALUTA": "GBP",
            "KURTYP": "KBH",
            "OPGOER": "A",
        },
        "name": "GBP/DKK Exchange Rate",
        "description": "British Pound exchange rate, DKK per 100 GBP, monthly average",
        "frequency": "monthly",
        "unit": "DKK per 100 GBP",
    },
    "FX_JPY_DKK": {
        "table": "DNVALM",
        "variables": {
            "VALUTA": "JPY",
            "KURTYP": "KBH",
            "OPGOER": "A",
        },
        "name": "JPY/DKK Exchange Rate",
        "description": "Japanese Yen exchange rate, DKK per 100 JPY, monthly average",
        "frequency": "monthly",
        "unit": "DKK per 100 JPY",
    },
    "FX_CHF_DKK": {
        "table": "DNVALM",
        "variables": {
            "VALUTA": "CHF",
            "KURTYP": "KBH",
            "OPGOER": "A",
        },
        "name": "CHF/DKK Exchange Rate",
        "description": "Swiss Franc exchange rate, DKK per 100 CHF, monthly average",
        "frequency": "monthly",
        "unit": "DKK per 100 CHF",
    },
    "FX_NOK_DKK": {
        "table": "DNVALM",
        "variables": {
            "VALUTA": "NOK",
            "KURTYP": "KBH",
            "OPGOER": "A",
        },
        "name": "NOK/DKK Exchange Rate",
        "description": "Norwegian Krone exchange rate, DKK per 100 NOK, monthly average",
        "frequency": "monthly",
        "unit": "DKK per 100 NOK",
    },
    "FX_SEK_DKK": {
        "table": "DNVALM",
        "variables": {
            "VALUTA": "SEK",
            "KURTYP": "KBH",
            "OPGOER": "A",
        },
        "name": "SEK/DKK Exchange Rate",
        "description": "Swedish Krona exchange rate, DKK per 100 SEK, monthly average",
        "frequency": "monthly",
        "unit": "DKK per 100 SEK",
    },
    # --- Government Bond Yields (MPK3, monthly) ---
    "GOVT_BOND_YIELD": {
        "table": "MPK3",
        "variables": {
            "TYPE": "5500701003",
        },
        "name": "Government Bonds Redemption Yield (%)",
        "description": "Danish government bonds, average redemption yield, monthly",
        "frequency": "monthly",
        "unit": "%",
    },
    "GOVT_BOND_10Y": {
        "table": "MPK3",
        "variables": {
            "TYPE": "5500701004",
        },
        "name": "10-Year Government Bond Yield (%)",
        "description": "Danish 10-year central government bond, redemption yield, monthly",
        "frequency": "monthly",
        "unit": "%",
    },
    "MORTGAGE_BOND_YIELD": {
        "table": "MPK3",
        "variables": {
            "TYPE": "5500701001",
        },
        "name": "Unit Mortgage Bonds Redemption Yield (%)",
        "description": "Danish unit mortgage bonds, redemption yield, monthly",
        "frequency": "monthly",
        "unit": "%",
    },
    # --- Balance of Payments (BBM, monthly, SA, DKK mn) ---
    "BOP_CURRENT_ACCOUNT": {
        "table": "BBM",
        "variables": {
            "POST": "1",
            "INDUDBOP": "N",
            "LAND": "W1",
            "ENHED": "93",
            "SÆSON": "2",
        },
        "name": "Current Account Balance (DKK mn)",
        "description": "Denmark current account net balance, seasonally adjusted, monthly",
        "frequency": "monthly",
        "unit": "DKK mn",
    },
    "BOP_GOODS": {
        "table": "BBM",
        "variables": {
            "POST": "1.A.A",
            "INDUDBOP": "N",
            "LAND": "W1",
            "ENHED": "93",
            "SÆSON": "2",
        },
        "name": "Goods Trade Balance (DKK mn)",
        "description": "Denmark goods trade (FOB) net balance, seasonally adjusted, monthly",
        "frequency": "monthly",
        "unit": "DKK mn",
    },
    "BOP_SERVICES": {
        "table": "BBM",
        "variables": {
            "POST": "1.A.B",
            "INDUDBOP": "N",
            "LAND": "W1",
            "ENHED": "93",
            "SÆSON": "2",
        },
        "name": "Services Trade Balance (DKK mn)",
        "description": "Denmark services trade net balance, seasonally adjusted, monthly",
        "frequency": "monthly",
        "unit": "DKK mn",
    },
    "BOP_PRIMARY_INCOME": {
        "table": "BBM",
        "variables": {
            "POST": "1.B",
            "INDUDBOP": "N",
            "LAND": "W1",
            "ENHED": "93",
            "SÆSON": "2",
        },
        "name": "Primary Income Balance (DKK mn)",
        "description": "Denmark primary income net balance, seasonally adjusted, monthly",
        "frequency": "monthly",
        "unit": "DKK mn",
    },
    # --- MFI Balance Sheet / Lending (DNRUUM, monthly, DKK mn) ---
    "MFI_LOANS_TOTAL": {
        "table": "DNRUUM",
        "variables": {
            "INSTRNAT": "AL00",
            "DATA": "GNSB",
            "INDSEK": "1000",
            "VALUTA": "Z01",
            "LØBETID1": "ALLE",
            "FORMÅL": "ALLE",
        },
        "name": "MFI Total Domestic Loans (DKK mn)",
        "description": "Outstanding domestic loans from MFI sector, all sectors, all currencies",
        "frequency": "monthly",
        "unit": "DKK mn",
    },
    "MFI_LOANS_NFC": {
        "table": "DNRUUM",
        "variables": {
            "INSTRNAT": "AL00",
            "DATA": "GNSB",
            "INDSEK": "1100",
            "VALUTA": "Z01",
            "LØBETID1": "ALLE",
            "FORMÅL": "ALLE",
        },
        "name": "MFI Loans to Non-Financial Corporates (DKK mn)",
        "description": "Outstanding domestic loans to non-financial corporations, all currencies",
        "frequency": "monthly",
        "unit": "DKK mn",
    },
    "MFI_LOANS_HOUSEHOLDS": {
        "table": "DNRUUM",
        "variables": {
            "INSTRNAT": "AL00",
            "DATA": "GNSB",
            "INDSEK": "1400",
            "VALUTA": "Z01",
            "LØBETID1": "ALLE",
            "FORMÅL": "ALLE",
        },
        "name": "MFI Loans to Households (DKK mn)",
        "description": "Outstanding domestic loans to households, all currencies",
        "frequency": "monthly",
        "unit": "DKK mn",
    },
    "MFI_LENDING_RATE": {
        "table": "DNRUUM",
        "variables": {
            "INSTRNAT": "AL00",
            "DATA": "EFFR",
            "INDSEK": "1000",
            "VALUTA": "Z01",
            "LØBETID1": "ALLE",
            "FORMÅL": "ALLE",
        },
        "name": "MFI Average Lending Rate (%)",
        "description": "Annualised agreed rate on outstanding domestic loans, all sectors",
        "frequency": "monthly",
        "unit": "%",
    },
    # --- Government Securities (DNVPSP, monthly, DKK mn market value) ---
    "GOVT_SECURITIES_TOTAL": {
        "table": "DNVPSP",
        "variables": {
            "DATA": "BEH",
            "PAPIR": "OBLTOT",
            "LØBETID2": "A0",
            "INVSEKTOR": "100",
            "VALUTA": "Z01",
        },
        "name": "Government Debt Securities Outstanding (DKK mn)",
        "description": "Total Danish government debt securities, market value stock, all holders",
        "frequency": "monthly",
        "unit": "DKK mn",
    },
    "GOVT_BONDS_STOCK": {
        "table": "DNVPSP",
        "variables": {
            "DATA": "BEH",
            "PAPIR": "OBLSTAT",
            "LØBETID2": "A0",
            "INVSEKTOR": "100",
            "VALUTA": "Z01",
        },
        "name": "Government Bonds Outstanding (DKK mn)",
        "description": "Danish government bonds, market value stock, all holders",
        "frequency": "monthly",
        "unit": "DKK mn",
    },
}


def _cache_path(indicator: str, params_hash: str) -> Path:
    safe = indicator.replace("/", "_")
    return CACHE_DIR / f"{safe}_{params_hash}.json"


def _params_hash(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def _read_cache(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(hours=CACHE_TTL_HOURS):
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


def _generate_time_codes(n_months: int) -> List[str]:
    """Generate a list of the last n_months month codes like 2026M03.
    Ends at previous month since current month data is typically not yet published."""
    now = datetime.now().replace(day=1) - timedelta(days=1)  # last day of prev month
    codes = []
    year, month = now.year, now.month
    for _ in range(n_months):
        codes.append(f"{year}M{month:02d}")
        month -= 1
        if month < 1:
            month = 12
            year -= 1
    return list(reversed(codes))


def _parse_jsonstat(raw: Dict, cfg: Dict) -> List[Dict]:
    """Extract time-period/value pairs from a JSON-Stat response."""
    try:
        ds = raw.get("dataset", {})
        values = ds.get("value", [])
        if not values:
            return []

        dim_info = ds.get("dimension", {})
        dim_ids = dim_info.get("id", [])
        dim_sizes = dim_info.get("size", [])

        time_key = "Tid"
        time_dim = dim_info.get(time_key, {})
        time_index = time_dim.get("category", {}).get("index", {})
        time_labels = time_dim.get("category", {}).get("label", {})

        time_pos = dim_ids.index(time_key) if time_key in dim_ids else -1
        if time_pos < 0:
            return []

        stride = 1
        for i in range(time_pos + 1, len(dim_sizes)):
            stride *= dim_sizes[i]

        pre_stride = 1
        for i in range(0, time_pos):
            pre_stride *= dim_sizes[i]

        sorted_times = sorted(time_index.items(), key=lambda x: x[1])

        results = []
        for time_code, time_idx in sorted_times:
            val_idx = time_idx * stride
            if val_idx < len(values) and values[val_idx] is not None:
                results.append({
                    "time_period": time_code,
                    "value": float(values[val_idx]),
                })

        results.sort(key=lambda x: x["time_period"], reverse=True)
        return results
    except (KeyError, IndexError, TypeError, ValueError):
        return []


_table_time_cache: Dict[str, List[str]] = {}


def _get_available_times(table: str) -> List[str]:
    """Fetch and cache available time codes for a table."""
    if table in _table_time_cache:
        return _table_time_cache[table]
    try:
        resp = requests.post(
            f"{BASE_URL}/tableinfo",
            json={"table": table, "lang": "en"},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            info = resp.json()
            for v in info.get("variables", []):
                if v["id"] == "Tid":
                    codes = [val["id"] for val in v.get("values", [])]
                    _table_time_cache[table] = codes
                    return codes
    except Exception:
        pass
    return []


def _api_request(table: str, variables: Dict, n_periods: int = 36) -> Dict:
    """Fetch data from StatBank API using JSONSTAT format."""
    desired = set(_generate_time_codes(n_periods))
    available = _get_available_times(table)
    time_codes = [t for t in available if t in desired] if available else list(desired)
    time_codes.sort()

    if not time_codes:
        return {"success": False, "error": "No valid time periods found for table"}

    var_list = []
    for code, value in variables.items():
        var_list.append({"code": code, "values": [value]})
    var_list.append({"code": "Tid", "values": time_codes})

    payload = {
        "table": table,
        "format": "JSONSTAT",
        "lang": "en",
        "variables": var_list,
        "valuePresentation": "Value",
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/data",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            try:
                err = resp.json()
                return {"success": False, "error": f"{err.get('errorTypeCode', 'HTTP')}: {err.get('message', resp.status_code)}"}
            except ValueError:
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        data = resp.json()
        if "errorTypeCode" in data:
            return {"success": False, "error": f"{data.get('errorTypeCode')}: {data.get('message', '')}"}
        return {"success": True, "data": data}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator/series with optional date range."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "start": start_date, "end": end_date}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    n_periods = 36

    result = _api_request(cfg["table"], cfg["variables"], n_periods=n_periods)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_jsonstat(result["data"], cfg)
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations returned"}

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
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["time_period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [{"period": o["time_period"], "value": o["value"]} for o in observations[:30]],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/data ({cfg['table']})",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "table": v["table"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all indicators."""
    if indicator:
        return fetch_data(indicator)

    results = {}
    errors = []
    for key in INDICATORS:
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
        "source": "Danmarks Nationalbank via StatBank Denmark",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_policy_rates() -> Dict:
    """Get current Danmarks Nationalbank policy rates."""
    rate_keys = ["DN_DISCOUNT_RATE", "DN_CURRENT_ACCOUNT_RATE", "DN_LENDING_RATE", "DN_CD_RATE"]
    rates = {}
    for key in rate_keys:
        data = fetch_data(key)
        if data.get("success"):
            rates[key] = {
                "name": data["name"],
                "rate": data["latest_value"],
                "period": data["latest_period"],
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(rates),
        "rates": rates,
        "timestamp": datetime.now().isoformat(),
    }


def get_fx_rates() -> Dict:
    """Get current DKK exchange rates vs major currencies."""
    fx_keys = [k for k in INDICATORS if k.startswith("FX_")]
    rates = {}
    for key in fx_keys:
        data = fetch_data(key)
        if data.get("success"):
            rates[key] = {
                "name": data["name"],
                "rate": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(rates),
        "rates": rates,
        "timestamp": datetime.now().isoformat(),
    }


def get_bond_yields() -> Dict:
    """Get Danish government bond yields."""
    yield_keys = ["GOVT_BOND_YIELD", "GOVT_BOND_10Y", "MORTGAGE_BOND_YIELD"]
    yields = {}
    for key in yield_keys:
        data = fetch_data(key)
        if data.get("success"):
            yields[key] = {
                "name": data["name"],
                "yield_pct": data["latest_value"],
                "period": data["latest_period"],
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(yields),
        "yields": yields,
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
Danmarks Nationalbank Module (Phase 1)

Usage:
  python danmarks_nationalbank.py                     # Latest values for all indicators
  python danmarks_nationalbank.py <INDICATOR>          # Fetch specific indicator
  python danmarks_nationalbank.py list                 # List available indicators
  python danmarks_nationalbank.py policy-rates         # DN policy rates
  python danmarks_nationalbank.py fx-rates             # DKK exchange rates
  python danmarks_nationalbank.py bond-yields          # Government bond yields

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: REST (JSON-Stat)
Coverage: Denmark
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "policy-rates":
            print(json.dumps(get_policy_rates(), indent=2, default=str))
        elif cmd == "fx-rates":
            print(json.dumps(get_fx_rates(), indent=2, default=str))
        elif cmd == "bond-yields":
            print(json.dumps(get_bond_yields(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))

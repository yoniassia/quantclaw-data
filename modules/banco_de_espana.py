#!/usr/bin/env python3
"""
Banco de España Module — Phase 1

Spain's central bank statistical data: Euribor rates, MFI lending/deposit rates,
mortgage reference rates, balance of payments, and housing market indicators.

Data Source: https://app.bde.es/bierest/resources/srdatosapp/
Protocol: REST JSON (BdE proprietary BIEST API)
Auth: None (open access)
Refresh: Monthly (rates, BoP), Quarterly (housing)
Coverage: Spain / Euro Area

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

BASE_URL = "https://app.bde.es/bierest/resources/srdatosapp"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "banco_de_espana"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.25

RANGE_BY_FREQ = {
    "D": "36M",
    "M": "60M",
    "Q": "60M",
    "A": "MAX",
}

INDICATORS = {
    # --- Euribor Reference Rates (monthly) ---
    "EURIBOR_1W": {
        "series": "D_1NBAS972",
        "name": "Euribor 1-Week (%)",
        "description": "Official mortgage market reference rate, 1-week Euribor",
        "frequency": "M",
        "unit": "%",
    },
    "EURIBOR_3M": {
        "series": "D_1NBAD972",
        "name": "Euribor 3-Month (%)",
        "description": "Official mortgage market reference rate, 3-month Euribor",
        "frequency": "M",
        "unit": "%",
    },
    "EURIBOR_6M": {
        "series": "D_1NBAE972",
        "name": "Euribor 6-Month (%)",
        "description": "Official mortgage market reference rate, 6-month Euribor",
        "frequency": "M",
        "unit": "%",
    },
    "EURIBOR_12M": {
        "series": "D_1NBAF472",
        "name": "Euribor 12-Month (%)",
        "description": "Official mortgage market reference rate, 12-month Euribor",
        "frequency": "M",
        "unit": "%",
    },
    # --- MFI Lending Rates — New Business (monthly) ---
    "MORTGAGE_RATE_NEW": {
        "series": "DN_1TI2T0135",
        "name": "Mortgage Rate — New Business (%)",
        "description": "NEDR on new housing loans to households, all initial rate fixation periods",
        "frequency": "M",
        "unit": "%",
    },
    "CONSUMER_CREDIT_RATE": {
        "series": "DN_1TI2T0138",
        "name": "Consumer Credit Rate — New Business (%)",
        "description": "NEDR on new consumer credit to households",
        "frequency": "M",
        "unit": "%",
    },
    "NFC_LENDING_RATE": {
        "series": "DN_1TI2T0144",
        "name": "NFC Lending Rate — New Business (%)",
        "description": "NEDR on new total loans to non-financial corporations",
        "frequency": "M",
        "unit": "%",
    },
    # --- Deposit Rates (monthly) ---
    "HOUSEHOLD_DEPOSIT_TERM": {
        "series": "DN_1TI2T0024",
        "name": "Household Term Deposit Rate — New Business (%)",
        "description": "NEDR on new term deposits from households, weighted average",
        "frequency": "M",
        "unit": "%",
    },
    "HOUSEHOLD_DEPOSIT_SIGHT": {
        "series": "DN_1TI1T0010",
        "name": "Household Overnight Deposit Rate (%)",
        "description": "NEDR on outstanding overnight deposits from households",
        "frequency": "M",
        "unit": "%",
    },
    # --- Mortgage Reference & Outstanding (monthly) ---
    "IRPH_MORTGAGE_REF": {
        "series": "D_1T9H0000",
        "name": "IRPH — Official Mortgage Reference Rate (%)",
        "description": "Weighted average rate on housing loans >3yr, all Spanish credit institutions",
        "frequency": "M",
        "unit": "%",
    },
    "MORTGAGE_RATE_OUTSTANDING": {
        "series": "DN_1TI1T0050",
        "name": "Mortgage Rate — Outstanding Stock (%)",
        "description": "NEDR on outstanding housing loan stock to households, weighted average",
        "frequency": "M",
        "unit": "%",
    },
    # --- Balance of Payments (monthly, EUR mn) ---
    "BOP_CURRENT_ACCOUNT": {
        "series": "DEEM.N.ES.W1.S1.S1.T.B.CA._Z._Z._Z.EUR._T._X.N.ALL",
        "name": "BoP — Current Account Balance (EUR mn)",
        "description": "Spain current account balance, all countries, monthly",
        "frequency": "M",
        "unit": "EUR mn",
    },
    "BOP_GOODS_SERVICES": {
        "series": "DEEM.N.ES.W1.S1.S1.T.B.GS._Z._Z._Z.EUR._T._X.N.ALL",
        "name": "BoP — Goods & Services Balance (EUR mn)",
        "description": "Spain goods and services trade balance, monthly",
        "frequency": "M",
        "unit": "EUR mn",
    },
    "BOP_INCOME": {
        "series": "DEEM.N.ES.W1.S1.S1.T.B.IN._Z._Z._Z.EUR._T._X.N.ALL",
        "name": "BoP — Primary & Secondary Income Balance (EUR mn)",
        "description": "Spain primary and secondary income balance, monthly",
        "frequency": "M",
        "unit": "EUR mn",
    },
    "BOP_CAPITAL_ACCOUNT": {
        "series": "DEEM.N.ES.W1.S1.S1.T.B.KA._Z._Z._Z.EUR._T._X.N.ALL",
        "name": "BoP — Capital Account Balance (EUR mn)",
        "description": "Spain capital account balance, monthly",
        "frequency": "M",
        "unit": "EUR mn",
    },
    "BOP_FINANCIAL_ACCOUNT": {
        "series": "DEEM.N.ES.W1.S1.S1.T.N.FA._T.F._Z.EUR._T._X.N.ALL",
        "name": "BoP — Financial Account Net (EUR mn)",
        "description": "Spain financial account net change (assets minus liabilities), monthly",
        "frequency": "M",
        "unit": "EUR mn",
    },
    # --- Housing Market (quarterly, EUR/m²) ---
    "HOUSING_PRICE_M2": {
        "series": "DHIVTNOAPLPMMUVT_RLI.T",
        "name": "Housing Price — Average Free Housing (EUR/m²)",
        "description": "Average appraised price per m² of free (non-subsidised) housing, national total",
        "frequency": "Q",
        "unit": "EUR/m²",
    },
    "HOUSING_PRICE_NEW": {
        "series": "DHIVTNOAPLPMMUVT_VVN_RLI.T",
        "name": "Housing Price — New Build (EUR/m²)",
        "description": "Average appraised price per m² of new free housing (≤5 years), national total",
        "frequency": "Q",
        "unit": "EUR/m²",
    },
    "HOUSING_PRICE_USED": {
        "series": "DHIVTNOAPLPMMUVT_VVU_RLI.T",
        "name": "Housing Price — Second Hand (EUR/m²)",
        "description": "Average appraised price per m² of used free housing (>5 years), national total",
        "frequency": "Q",
        "unit": "EUR/m²",
    },
}


def _cache_path(indicator: str, params_hash: str) -> Path:
    safe = indicator.replace("/", "_").replace(".", "_")
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


def _api_latest(series_codes: List[str]) -> Dict:
    """Fetch latest values via the 'favoritas' endpoint."""
    url = f"{BASE_URL}/favoritas"
    params = {"idioma": "en", "series": ",".join(series_codes)}
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _api_series(series_code: str, rango: str) -> Dict:
    """Fetch full time series via the 'listaSeries' endpoint."""
    url = f"{BASE_URL}/listaSeries"
    params = {"idioma": "en", "series": series_code, "rango": rango}
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, dict) and payload.get("errNum"):
            return {"success": False, "error": payload.get("errMsgUsr", "API error")}
        return {"success": True, "data": payload}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_series(raw_list: list) -> List[Dict]:
    """Extract date/value pairs from listaSeries response."""
    if not raw_list or not isinstance(raw_list, list):
        return []
    try:
        series_obj = raw_list[0]
        fechas = series_obj.get("fechas", [])
        valores = series_obj.get("valores", [])
        results = []
        for date_str, val in zip(fechas, valores):
            if val is not None:
                period = date_str[:10]
                results.append({"time_period": period, "value": float(val)})
        return results
    except (KeyError, IndexError, TypeError, ValueError):
        return []


def fetch_data(indicator: str, rango: str = None) -> Dict:
    """Fetch a specific indicator with full time series."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    if rango is None:
        rango = RANGE_BY_FREQ.get(cfg["frequency"], "60M")

    cache_params = {"indicator": indicator, "rango": rango}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_series(cfg["series"], rango)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_series(result["data"])
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
        "source": f"{BASE_URL}/listaSeries?idioma=en&series={cfg['series']}&rango={rango}",
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
            "series": v["series"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all indicators."""
    if indicator:
        return fetch_data(indicator)

    all_codes = {k: cfg["series"] for k, cfg in INDICATORS.items()}
    batch_size = 10
    keys = list(all_codes.keys())
    results = {}
    errors = []

    for i in range(0, len(keys), batch_size):
        batch_keys = keys[i:i + batch_size]
        batch_codes = [all_codes[k] for k in batch_keys]
        resp = _api_latest(batch_codes)

        if not resp["success"]:
            for k in batch_keys:
                errors.append({"indicator": k, "error": resp.get("error", "unknown")})
            continue

        code_to_key = {all_codes[k]: k for k in batch_keys}
        for item in resp["data"]:
            code = item.get("serie")
            if not code or code not in code_to_key:
                continue
            key = code_to_key[code]
            cfg = INDICATORS[key]
            results[key] = {
                "name": cfg["name"],
                "value": item.get("valor"),
                "period": item.get("fechaValor", "")[:10],
                "unit": cfg["unit"],
                "trend": item.get("tendencia"),
            }
            code_to_key.pop(code, None)

        for leftover_code, leftover_key in code_to_key.items():
            errors.append({"indicator": leftover_key, "error": "Not found in API response"})

        if i + batch_size < len(keys):
            time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "Banco de España (BdE)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_interest_rates() -> Dict:
    """Get all current interest rate indicators."""
    rate_keys = [k for k in INDICATORS if k.startswith(("EURIBOR_", "MORTGAGE_", "CONSUMER_", "NFC_", "HOUSEHOLD_", "IRPH_"))]
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
        "count": len(rates),
        "timestamp": datetime.now().isoformat(),
    }


def get_bop_summary() -> Dict:
    """Get current balance of payments summary."""
    bop_keys = [k for k in INDICATORS if k.startswith("BOP_")]
    bop = {}
    for key in bop_keys:
        data = fetch_data(key)
        if data.get("success"):
            bop[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(bop),
        "bop": bop,
        "count": len(bop),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
Banco de España Module (Phase 1)

Usage:
  python banco_de_espana.py                         # Latest values for all indicators
  python banco_de_espana.py <INDICATOR>              # Fetch specific indicator
  python banco_de_espana.py list                     # List available indicators
  python banco_de_espana.py rates                    # All interest rates
  python banco_de_espana.py bop                      # Balance of payments summary

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: BdE BIEST JSON API
Coverage: Spain / Euro Area
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "rates":
            print(json.dumps(get_interest_rates(), indent=2, default=str))
        elif cmd == "bop":
            print(json.dumps(get_bop_summary(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))

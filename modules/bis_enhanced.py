#!/usr/bin/env python3
"""
BIS Enhanced Module — Derivatives, FX Turnover, Debt Securities, Payments

Six BIS datasets via SDMX v2 API:
  1. OTC derivatives outstanding (WS_OTC_DERIV2) — semiannual
  2. Exchange-traded derivatives (WS_XTD_DERIV) — quarterly
  3. OTC derivatives turnover / FX turnover survey (WS_DER_OTC_TOV) — triennial
  4. International debt securities (WS_NA_SEC_DSS) — quarterly
  5. CPMI cashless payments (WS_CPMI_CASHLESS) — annual
  6. CPMI macro indicators (WS_CPMI_MACRO) — annual

Data Source: https://stats.bis.org/api/v2
Protocol: BIS SDMX REST API v2 (CSV output)
Auth: None (open access)
Coverage: Global / 60+ countries

Author: QUANTCLAW DATA Build Agent
Initiative: 0038
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://stats.bis.org/api/v2"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "bis_enhanced"
CACHE_TTL_HOURS = 12
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

# Each indicator maps to a BIS SDMX dataflow + series key.
# CSV columns vary per dataflow; the parser extracts TIME_PERIOD and OBS_VALUE.
INDICATORS = {
    # --- OTC Derivatives Outstanding (WS_OTC_DERIV2, semiannual) ---
    "OTC_NOTIONAL_TOTAL": {
        "dataflow": "WS_OTC_DERIV2",
        "version": "1.0",
        "key": "H.A.T.T.5J.A.5J.A.TO1.TO1.A.A.3.A",
        "name": "OTC Derivatives — Total Notional Outstanding (USD bn)",
        "description": "Gross notional amounts outstanding, all OTC derivatives, all reporting countries",
        "frequency": "semiannual",
        "unit": "USD bn",
    },
    "OTC_NOTIONAL_SWAPS": {
        "dataflow": "WS_OTC_DERIV2",
        "version": "1.0",
        "key": "H.A.S.T.5J.A.5J.A.TO1.TO1.A.A.3.A",
        "name": "OTC Derivatives — Swaps Notional Outstanding (USD bn)",
        "description": "Gross notional amounts outstanding, swaps only, all reporting countries",
        "frequency": "semiannual",
        "unit": "USD bn",
    },
    "OTC_GMV_TOTAL": {
        "dataflow": "WS_OTC_DERIV2",
        "version": "1.0",
        "key": "H.B.U.T.5J.K.5J.A.TO1.TO1.A.A.3.A",
        "name": "OTC Derivatives — Gross Market Value (USD bn)",
        "description": "Gross positive market values, all instruments, all reporting dealers",
        "frequency": "semiannual",
        "unit": "USD bn",
    },
    "OTC_NOTIONAL_NFC": {
        "dataflow": "WS_OTC_DERIV2",
        "version": "1.0",
        "key": "H.C.U.T.5J.N.5J.A.TO1.TO1.A.A.3.A",
        "name": "OTC Derivatives — Non-Financial Counterparties (USD bn)",
        "description": "Notional outstanding with non-financial counterparties",
        "frequency": "semiannual",
        "unit": "USD bn",
    },

    # --- Exchange-Traded Derivatives (WS_XTD_DERIV, quarterly) ---
    "XTD_OI_FX": {
        "dataflow": "WS_XTD_DERIV",
        "version": "1.0",
        "key": "Q.U.B.T.TO1.8K",
        "name": "Exchange-Traded Derivatives — FX Open Interest (USD mn)",
        "description": "Open interest, foreign exchange contracts, all exchanges worldwide",
        "frequency": "quarterly",
        "unit": "USD mn",
    },
    "XTD_OI_IR": {
        "dataflow": "WS_XTD_DERIV",
        "version": "1.0",
        "key": "Q.U.C.T.TO1.8K",
        "name": "Exchange-Traded Derivatives — Interest Rate Open Interest (USD mn)",
        "description": "Open interest, interest rate contracts, all exchanges worldwide",
        "frequency": "quarterly",
        "unit": "USD mn",
    },
    "XTD_OI_EQUITY": {
        "dataflow": "WS_XTD_DERIV",
        "version": "1.0",
        "key": "Q.U.I.T.TO1.8K",
        "name": "Exchange-Traded Derivatives — Equity Open Interest (USD mn)",
        "description": "Open interest, equity index contracts, all exchanges worldwide",
        "frequency": "quarterly",
        "unit": "USD mn",
    },
    "XTD_OI_COMMODITY": {
        "dataflow": "WS_XTD_DERIV",
        "version": "1.0",
        "key": "Q.U.J.T.TO1.8K",
        "name": "Exchange-Traded Derivatives — Commodity Open Interest (USD mn)",
        "description": "Open interest, commodity contracts, all exchanges worldwide",
        "frequency": "quarterly",
        "unit": "USD mn",
    },
    "XTD_TURNOVER_FX": {
        "dataflow": "WS_XTD_DERIV",
        "version": "1.0",
        "key": "Q.A.B.T.TO1.8K",
        "name": "Exchange-Traded Derivatives — FX Turnover (USD mn)",
        "description": "Turnover, foreign exchange contracts, all exchanges worldwide",
        "frequency": "quarterly",
        "unit": "USD mn",
    },

    # --- OTC Derivatives Turnover / FX Turnover Survey (WS_DER_OTC_TOV, triennial) ---
    "FX_TURNOVER_TOTAL": {
        "dataflow": "WS_DER_OTC_TOV",
        "version": "1.0",
        "key": "A.U.K.D.5J.A.5J.A.TO1.TO1.A.A.3.B",
        "name": "FX Turnover — Daily Average Total (USD mn)",
        "description": "Daily average FX turnover, all instruments, all reporting countries (triennial survey)",
        "frequency": "triennial",
        "unit": "USD mn",
    },
    "IR_DERIV_TURNOVER": {
        "dataflow": "WS_DER_OTC_TOV",
        "version": "1.0",
        "key": "A.U.M.D.5J.A.5J.A.TO1.TO1.A.A.3.B",
        "name": "OTC IR Derivatives — Daily Average Turnover (USD mn)",
        "description": "Daily average OTC interest rate derivatives turnover, all reporting countries",
        "frequency": "triennial",
        "unit": "USD mn",
    },
    "FX_TURNOVER_SPOT": {
        "dataflow": "WS_DER_OTC_TOV",
        "version": "1.0",
        "key": "A.U.H.B.5J.A.5J.A.TO1.TO1.J.A.3.B",
        "name": "FX Spot Turnover — Daily Average (USD mn)",
        "description": "Daily average FX spot transactions, all reporting countries",
        "frequency": "triennial",
        "unit": "USD mn",
    },

    # --- International Debt Securities (WS_NA_SEC_DSS, quarterly) ---
    "DEBT_SEC_US": {
        "dataflow": "WS_NA_SEC_DSS",
        "version": "1.0",
        "key": "Q.N.US.XW.S1.S1.N.L.LE.F3.T._Z.USD._T.N.V.N._T",
        "name": "Debt Securities Outstanding — United States (USD bn)",
        "description": "All debt securities issued by US residents, all markets, nominal value",
        "frequency": "quarterly",
        "unit": "USD bn",
    },
    "DEBT_SEC_GB": {
        "dataflow": "WS_NA_SEC_DSS",
        "version": "1.0",
        "key": "Q.N.GB.XW.S1.S1.N.L.LE.F3.T._Z.USD._T.N.V.N._T",
        "name": "Debt Securities Outstanding — United Kingdom (USD bn)",
        "description": "All debt securities issued by UK residents, all markets, nominal value",
        "frequency": "quarterly",
        "unit": "USD bn",
    },
    "DEBT_SEC_JP": {
        "dataflow": "WS_NA_SEC_DSS",
        "version": "1.0",
        "key": "Q.N.JP.XW.S1.S1.N.L.LE.F3.T._Z.USD._T.N.V.N._T",
        "name": "Debt Securities Outstanding — Japan (USD bn)",
        "description": "All debt securities issued by JP residents, all markets, nominal value",
        "frequency": "quarterly",
        "unit": "USD bn",
    },
    "DEBT_SEC_CN": {
        "dataflow": "WS_NA_SEC_DSS",
        "version": "1.0",
        "key": "Q.N.CN.XW.S1.S1.N.L.LE.F3.T._Z.USD._T.N.V.N._T",
        "name": "Debt Securities Outstanding — China (USD bn)",
        "description": "All debt securities issued by CN residents, all markets, nominal value",
        "frequency": "quarterly",
        "unit": "USD bn",
    },
    "DEBT_SEC_DE": {
        "dataflow": "WS_NA_SEC_DSS",
        "version": "1.0",
        "key": "Q.N.DE.XW.S1.S1.N.L.LE.F3.T._Z.USD._T.N.V.N._T",
        "name": "Debt Securities Outstanding — Germany (USD bn)",
        "description": "All debt securities issued by DE residents, all markets, nominal value",
        "frequency": "quarterly",
        "unit": "USD bn",
    },

    # --- CPMI Cashless Payments (WS_CPMI_CASHLESS, annual) ---
    "CPMI_CASHLESS_US_VALUE": {
        "dataflow": "WS_CPMI_CASHLESS",
        "version": "1.0",
        "key": "A.US.V.A.A.Z.Z.A.A.Z.A.A",
        "name": "CPMI Cashless Payments — US Total Value (USD mn)",
        "description": "Total value of cashless payments, United States",
        "frequency": "annual",
        "unit": "USD mn",
    },
    "CPMI_CASHLESS_GB_VALUE": {
        "dataflow": "WS_CPMI_CASHLESS",
        "version": "1.0",
        "key": "A.GB.V.A.A.Z.Z.A.A.Z.A.A",
        "name": "CPMI Cashless Payments — UK Total Value (GBP mn)",
        "description": "Total value of cashless payments, United Kingdom",
        "frequency": "annual",
        "unit": "GBP mn",
    },
    "CPMI_CASHLESS_CN_VALUE": {
        "dataflow": "WS_CPMI_CASHLESS",
        "version": "1.0",
        "key": "A.CN.V.A.A.Z.Z.A.A.Z.A.A",
        "name": "CPMI Cashless Payments — China Total Value (CNY mn)",
        "description": "Total value of cashless payments, China",
        "frequency": "annual",
        "unit": "CNY mn",
    },

    # --- CPMI Macro (WS_CPMI_MACRO, annual) ---
    "CPMI_MACRO_US_POP": {
        "dataflow": "WS_CPMI_MACRO",
        "version": "1.0",
        "key": "A.UBBA.US.R2",
        "name": "CPMI Macro — US Population (thousands)",
        "description": "United States population, CPMI reporting",
        "frequency": "annual",
        "unit": "thousands",
    },
    "CPMI_MACRO_US_BANKNOTES": {
        "dataflow": "WS_CPMI_MACRO",
        "version": "1.0",
        "key": "A.BDCA.US.01",
        "name": "CPMI Macro — US Banknotes & Coins in Circulation (USD)",
        "description": "Total banknotes and coins in circulation, United States",
        "frequency": "annual",
        "unit": "USD",
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


def _parse_csv(text: str) -> List[Dict]:
    """Parse BIS SDMX CSV response into time-period/value pairs.

    BIS CSV has a header row. Rows without a TIME_PERIOD or OBS_VALUE
    are metadata stubs (series attributes) and are skipped.
    """
    lines = text.strip().splitlines()
    if len(lines) < 2:
        return []

    header = lines[0].split(",")
    try:
        tp_idx = header.index("TIME_PERIOD")
        ov_idx = header.index("OBS_VALUE")
    except ValueError:
        return []

    title_idx = None
    for candidate in ("TITLE_TS", "TITLE"):
        if candidate in header:
            title_idx = header.index(candidate)
            break

    unit_idx = header.index("UNIT_MEASURE") if "UNIT_MEASURE" in header else None
    mult_idx = header.index("UNIT_MULT") if "UNIT_MULT" in header else None
    status_idx = header.index("OBS_STATUS") if "OBS_STATUS" in header else None

    results = []
    for line in lines[1:]:
        cols = line.split(",")
        if len(cols) <= max(tp_idx, ov_idx):
            continue

        tp = cols[tp_idx].strip()
        ov = cols[ov_idx].strip()
        if not tp or not ov or ov == "NaN":
            continue

        try:
            value = float(ov)
        except ValueError:
            continue

        entry = {"time_period": tp, "value": value}
        if title_idx is not None and title_idx < len(cols) and cols[title_idx].strip():
            entry["title"] = cols[title_idx].strip().strip('"')
        if unit_idx is not None and unit_idx < len(cols) and cols[unit_idx].strip():
            entry["unit_measure"] = cols[unit_idx].strip()
        if mult_idx is not None and mult_idx < len(cols) and cols[mult_idx].strip():
            entry["unit_mult"] = cols[mult_idx].strip()
        if status_idx is not None and status_idx < len(cols) and cols[status_idx].strip():
            entry["obs_status"] = cols[status_idx].strip()

        results.append(entry)

    results.sort(key=lambda x: x["time_period"], reverse=True)
    return results


def _api_request(dataflow: str, version: str, key: str, last_n: int = 20) -> Dict:
    """Fetch data from BIS SDMX v2 API in CSV format."""
    url = f"{BASE_URL}/data/dataflow/BIS/{dataflow}/{version}/{key}"
    params = {"lastNObservations": last_n}
    headers = {"Accept": "application/vnd.sdmx.data+csv"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 404:
            return {"success": False, "error": "Series not found (HTTP 404)"}
        if "ErrorMessage" in resp.text and "No results" in resp.text:
            return {"success": False, "error": "No results for query"}
        resp.raise_for_status()
        return {"success": True, "text": resp.text}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
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

    last_n = 20
    extra = {}
    if start_date:
        extra["startPeriod"] = start_date
    if end_date:
        extra["endPeriod"] = end_date

    result = _api_request(cfg["dataflow"], cfg["version"], cfg["key"], last_n=last_n)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_csv(result["text"])
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations parsed"}

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
        "data_points": [{"period": o["time_period"], "value": o["value"]} for o in observations[:20]],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/data/dataflow/BIS/{cfg['dataflow']}/{cfg['version']}/{cfg['key']}",
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
            "dataflow": v["dataflow"],
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
        "source": "BIS Enhanced (Derivatives + FX Turnover + Debt + Payments)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_derivatives_dashboard() -> Dict:
    """Snapshot of OTC + exchange-traded derivatives markets."""
    otc_keys = ["OTC_NOTIONAL_TOTAL", "OTC_NOTIONAL_SWAPS", "OTC_GMV_TOTAL", "OTC_NOTIONAL_NFC"]
    xtd_keys = ["XTD_OI_FX", "XTD_OI_IR", "XTD_OI_EQUITY", "XTD_OI_COMMODITY"]

    dash: Dict = {"otc": {}, "exchange_traded": {}, "errors": []}
    for key in otc_keys + xtd_keys:
        data = fetch_data(key)
        bucket = "otc" if key.startswith("OTC_") else "exchange_traded"
        if data.get("success"):
            dash[bucket][key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
            }
        else:
            dash["errors"].append({"indicator": key, "error": data.get("error")})
        time.sleep(REQUEST_DELAY)

    dash["success"] = bool(dash["otc"] or dash["exchange_traded"])
    dash["timestamp"] = datetime.now().isoformat()
    if not dash["errors"]:
        dash.pop("errors")
    return dash


def get_debt_securities_comparison() -> Dict:
    """Compare debt securities outstanding across major economies."""
    keys = ["DEBT_SEC_US", "DEBT_SEC_GB", "DEBT_SEC_JP", "DEBT_SEC_CN", "DEBT_SEC_DE"]
    comparison = {"countries": {}, "errors": []}
    for key in keys:
        data = fetch_data(key)
        if data.get("success"):
            comparison["countries"][key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
            }
        else:
            comparison["errors"].append({"indicator": key, "error": data.get("error")})
        time.sleep(REQUEST_DELAY)

    comparison["success"] = bool(comparison["countries"])
    comparison["timestamp"] = datetime.now().isoformat()
    if not comparison["errors"]:
        comparison.pop("errors")
    return comparison


# --- CLI ---

def _print_help():
    print("""
BIS Enhanced Module — Derivatives, FX Turnover, Debt Securities, Payments
Initiative 0038

Usage:
  python bis_enhanced.py                          # Latest values for all indicators
  python bis_enhanced.py <INDICATOR>               # Fetch specific indicator
  python bis_enhanced.py list                      # List available indicators
  python bis_enhanced.py derivatives               # Derivatives market dashboard
  python bis_enhanced.py debt-securities           # Debt securities comparison
  python bis_enhanced.py datasets                  # Show covered datasets

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print(f"""
Datasets:
  WS_OTC_DERIV2      OTC derivatives outstanding (semiannual)
  WS_XTD_DERIV       Exchange-traded derivatives (quarterly)
  WS_DER_OTC_TOV     FX + OTC IR derivatives turnover (triennial)
  WS_NA_SEC_DSS      Debt securities statistics (quarterly)
  WS_CPMI_CASHLESS   CPMI cashless payments (annual)
  WS_CPMI_MACRO      CPMI macro indicators (annual)

Source: {BASE_URL}
Coverage: Global / 60+ countries
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "derivatives":
            print(json.dumps(get_derivatives_dashboard(), indent=2, default=str))
        elif cmd == "debt-securities":
            print(json.dumps(get_debt_securities_comparison(), indent=2, default=str))
        elif cmd == "datasets":
            seen = {}
            for cfg in INDICATORS.values():
                df = cfg["dataflow"]
                if df not in seen:
                    seen[df] = {"dataflow": df, "version": cfg["version"], "frequency": cfg["frequency"], "indicators": 0}
                seen[df]["indicators"] += 1
            print(json.dumps(list(seen.values()), indent=2))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))

#!/usr/bin/env python3
"""
National Bank of Belgium (NBB.Stat) SDMX Module

Belgium's central bank statistical data: balance of payments, HICP inflation,
financial accounts, international investment position, government finance,
monetary aggregates, and business surveys.

Data Source: https://nsidisseminate-stat.nbb.be/rest (NSI Disseminate — .Stat Suite)
Protocol: SDMX 2.1 REST (SDMX-JSON)
Auth: None (open access, requires Origin header)
Refresh: Monthly (most series), Quarterly (IIP, financial accounts, govt finance)
Coverage: Belgium / Euro Area

Author: QUANTCLAW DATA Build Agent
Initiative: 0016
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://nsidisseminate-stat.nbb.be/rest"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "nbb_belgium"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

HEADERS = {
    "Accept": "application/json",
    "Origin": "https://dataexplorer.nbb.be",
    "Referer": "https://dataexplorer.nbb.be/",
}

AGENCY = "BE2"

INDICATORS = {
    # --- Balance of Payments (DF_BOPBPM6, monthly, EUR mn) ---
    "BOP_CURRENT_ACCOUNT": {
        "dataflow": "DF_BOPBPM6",
        "key": "993.04.M",
        "name": "Current Account Balance (EUR mn)",
        "description": "Belgium current account balance, net, monthly",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    "BOP_GOODS_TRADE": {
        "dataflow": "DF_BOPBPM6",
        "key": "100.04.M",
        "name": "Goods Trade Balance (EUR mn)",
        "description": "Belgium goods trade balance, net, monthly",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    "BOP_SERVICES": {
        "dataflow": "DF_BOPBPM6",
        "key": "200.04.M",
        "name": "Services Balance (EUR mn)",
        "description": "Belgium services balance, net, monthly",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    "BOP_PRIMARY_INCOME": {
        "dataflow": "DF_BOPBPM6",
        "key": "300.04.M",
        "name": "Primary Income Balance (EUR mn)",
        "description": "Belgium primary income balance, net, monthly",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    "BOP_CAPITAL_ACCOUNT": {
        "dataflow": "DF_BOPBPM6",
        "key": "994.04.M",
        "name": "Capital Account Balance (EUR mn)",
        "description": "Belgium capital account balance, net, monthly",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    "BOP_FINANCIAL_ACCOUNT": {
        "dataflow": "DF_BOPBPM6",
        "key": "995.04.M",
        "name": "Financial Account Balance (EUR mn)",
        "description": "Belgium financial account balance, net, monthly",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    # --- HICP Inflation (DF_HICP, monthly, %) ---
    "HICP_TOTAL_YOY": {
        "dataflow": "DF_HICP",
        "key": "M.BE.000000.2015.HCP.GROWTH_RATE",
        "name": "HICP Total YoY (%)",
        "description": "Harmonised Index of Consumer Prices, all items, year-on-year change, Belgium",
        "frequency": "monthly",
        "unit": "%",
    },
    "HICP_CORE_YOY": {
        "dataflow": "DF_HICP",
        "key": "M.BE.XEF000.2015.HCP.GROWTH_RATE",
        "name": "HICP Core (ex food & energy) YoY (%)",
        "description": "HICP excluding food and energy, year-on-year change, Belgium",
        "frequency": "monthly",
        "unit": "%",
    },
    "HICP_ENERGY_YOY": {
        "dataflow": "DF_HICP",
        "key": "M.BE.NRGY00.2015.HCP.GROWTH_RATE",
        "name": "HICP Energy YoY (%)",
        "description": "HICP energy component, year-on-year change, Belgium",
        "frequency": "monthly",
        "unit": "%",
    },
    "HICP_SERVICES_YOY": {
        "dataflow": "DF_HICP",
        "key": "M.BE.SERV00.2015.HCP.GROWTH_RATE",
        "name": "HICP Services YoY (%)",
        "description": "HICP services component, year-on-year change, Belgium",
        "frequency": "monthly",
        "unit": "%",
    },
    "HICP_INDEX": {
        "dataflow": "DF_HICP",
        "key": "M.BE.000000.2015.HCP.INDICES",
        "name": "HICP Index (2015=100)",
        "description": "Harmonised Index of Consumer Prices, all items, index level, Belgium",
        "frequency": "monthly",
        "unit": "Index 2015=100",
    },
    # --- Financial Accounts (DF_FINACC2010, quarterly) ---
    "HH_FINANCIAL_WEALTH": {
        "dataflow": "DF_FINACC2010",
        "key": "Q.LE.S14.Y.N",
        "name": "Household Financial Wealth Net (EUR mn)",
        "description": "Household (S.14) net financial wealth, quarterly, Belgium",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    "ECONOMY_NET_FINANCIAL": {
        "dataflow": "DF_FINACC2010",
        "key": "Q.LE.S1.Y.N",
        "name": "Total Economy Net Financial Position (EUR mn)",
        "description": "Total Belgian economy (S.1) net financial position, quarterly",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    # --- International Investment Position (DF_IIP, quarterly) ---
    "IIP_NET_POSITION": {
        "dataflow": "DF_IIP",
        "key": "S1.S1.N.FA__T_F__Z__T.Q",
        "name": "Net International Investment Position (EUR mn)",
        "description": "Total economy net IIP (financial account), quarterly, Belgium",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    "IIP_PORTFOLIO_NET": {
        "dataflow": "DF_IIP",
        "key": "S1.S1.N.FA_P_F__Z__T.Q",
        "name": "Portfolio Investment Net IIP (EUR mn)",
        "description": "Net portfolio investment position, quarterly, Belgium",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    # --- Government Finance (DF_FINGOV, quarterly) ---
    "GOV_NET_LENDING": {
        "dataflow": "DF_FINGOV",
        "key": "Q.F.S1300.F.B9F",
        "name": "General Govt Net Lending/Borrowing (EUR mn)",
        "description": "General government consolidated net lending (+) or borrowing (-), quarterly",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    "GOV_TOTAL_LIABILITIES": {
        "dataflow": "DF_FINGOV",
        "key": "Q.LE.S1300.F.FL",
        "name": "General Govt Total Financial Liabilities (EUR mn)",
        "description": "General government consolidated total financial liabilities (debt stock), quarterly",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    "GOV_DEBT_SECURITIES": {
        "dataflow": "DF_FINGOV",
        "key": "Q.LE.S1300.F3.FL",
        "name": "Govt Debt Securities Outstanding (EUR mn)",
        "description": "General government consolidated debt securities (bonds) outstanding, quarterly",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    # --- Monetary Aggregates (DF_MONAGG, monthly, EUR bn) ---
    "M1_EUROAREA": {
        "dataflow": "DF_MONAGG",
        "key": "M.M10.U2",
        "name": "M1 Money Supply — Euro Area (EUR bn)",
        "description": "Euro Area M1 narrow money (currency in circulation + overnight deposits)",
        "frequency": "monthly",
        "unit": "EUR bn",
    },
    "M3_EUROAREA": {
        "dataflow": "DF_MONAGG",
        "key": "M.M30.U2",
        "name": "M3 Money Supply — Euro Area (EUR bn)",
        "description": "Euro Area M3 broad money aggregate",
        "frequency": "monthly",
        "unit": "EUR bn",
    },
    # --- Business Surveys (DF_BUSSURVM, monthly, index) ---
    "BUSSURVEY_SYNTHETIC": {
        "dataflow": "DF_BUSSURVM",
        "key": "M.SYNC.BE.A999.S",
        "name": "Business Survey Synthetic Curve",
        "description": "NBB overall business confidence synthetic curve, Belgium total, seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index",
    },
    "BUSSURVEY_MANUFACTURING": {
        "dataflow": "DF_BUSSURVM",
        "key": "M.SYNC.BE.M000.S",
        "name": "Business Survey — Manufacturing",
        "description": "NBB business confidence synthetic curve, manufacturing industry, seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index",
    },
    "BUSSURVEY_TRADE": {
        "dataflow": "DF_BUSSURVM",
        "key": "M.SYNC.BE.T000.S",
        "name": "Business Survey — Trade",
        "description": "NBB business confidence synthetic curve, trade sector, seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index",
    },
    "BUSSURVEY_SERVICES": {
        "dataflow": "DF_BUSSURVM",
        "key": "M.SYNC.BE.S000.S",
        "name": "Business Survey — Business Services",
        "description": "NBB business confidence synthetic curve, business-related services, seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index",
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


def _parse_sdmx_json(raw: Dict) -> List[Dict]:
    """Extract time-period/value pairs from NBB .Stat Suite SDMX-JSON response.

    NBB uses dimensionAtObservation=AllDimensions, so all dimensions are encoded
    in the colon-separated observation key. The TIME_PERIOD dimension is always
    the last one in the key.
    """
    try:
        datasets = raw.get("dataSets", [])
        if not datasets:
            return []

        structure = raw.get("structure", {})
        obs_dims = structure.get("dimensions", {}).get("observation", [])
        if not obs_dims:
            return []

        time_dim_idx = None
        time_values = []
        for i, d in enumerate(obs_dims):
            if d["id"] == "TIME_PERIOD":
                time_dim_idx = i
                time_values = d["values"]
                break

        if time_dim_idx is None:
            return []

        obs_attrs = structure.get("attributes", {}).get("observation", [])
        unit_mult_idx = None
        unit_mult_values = []
        for i, a in enumerate(obs_attrs):
            if a["id"] == "UNIT_MULT":
                unit_mult_idx = i
                unit_mult_values = a["values"]
                break

        results = []
        observations = datasets[0].get("observations", {})
        for key, vals in observations.items():
            if vals[0] is None:
                continue
            dim_indices = key.split(":")
            time_idx = int(dim_indices[time_dim_idx])
            if time_idx >= len(time_values):
                continue

            period = time_values[time_idx]["id"]
            value = float(vals[0])
            results.append({"time_period": period, "value": value})

        results.sort(key=lambda x: x["time_period"], reverse=True)
        return results
    except (KeyError, IndexError, TypeError, ValueError):
        return []


def _api_request(dataflow: str, key: str, last_n: int = 24) -> Dict:
    url = f"{BASE_URL}/data/{AGENCY},{dataflow},1.0/{key}"
    params = {
        "lastNObservations": last_n,
        "dimensionAtObservation": "AllDimensions",
    }
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 404:
            body = resp.text.strip()
            if "NoRecordsFound" in body:
                return {"success": False, "error": "No records found for this series"}
            return {"success": False, "error": f"Series not found (HTTP 404)"}
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


def discover_dataflows() -> Dict:
    """Discover all available dataflows from NBB.Stat."""
    url = f"{BASE_URL}/dataflow"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        refs = data.get("references", {})
        flows = []
        for urn, info in refs.items():
            if "Dataflow" not in urn:
                continue
            fid = info.get("id", "")
            names = info.get("names", {})
            name_en = names.get("en", names.get("en-GB", next(iter(names.values()), "")))
            flows.append({"id": fid, "name": name_en})
        flows.sort(key=lambda x: x["id"])
        return {"success": True, "dataflows": flows, "count": len(flows)}
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

    last_n = 60 if cfg["frequency"] == "monthly" else 24

    result = _api_request(cfg["dataflow"], cfg["key"], last_n=last_n)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_sdmx_json(result["data"])
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
        "source": f"{BASE_URL}/data/{AGENCY},{cfg['dataflow']},1.0/{cfg['key']}",
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
        "source": "National Bank of Belgium (NBB.Stat)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
National Bank of Belgium (NBB.Stat) SDMX Module

Usage:
  python nbb_belgium.py                         # Latest values for all indicators
  python nbb_belgium.py <INDICATOR>              # Fetch specific indicator
  python nbb_belgium.py list                     # List available indicators
  python nbb_belgium.py dataflows                # Discover all NBB.Stat dataflows

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: SDMX 2.1 REST (JSON) via .Stat Suite NSI
Coverage: Belgium / Euro Area
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "dataflows":
            print(json.dumps(discover_dataflows(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))

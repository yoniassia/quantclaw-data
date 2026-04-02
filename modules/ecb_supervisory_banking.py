#!/usr/bin/env python3
"""
ECB Supervisory Banking Statistics (SSM Data) Module

Aggregated prudential data for significant banks under ECB direct supervision
(~110 banking groups, 82% of Euro area banking assets). Covers capital adequacy
(CET1, Tier 1), non-performing loan ratios, profitability (ROE, ROA),
liquidity (LCR, NSFR), leverage, and operational efficiency metrics.

Data Source: https://data-api.ecb.europa.eu/service
Dataflow: CBD2 (Consolidated Banking Data)
Protocol: SDMX 2.1 REST — CSV format (bypasses WAF on JSON key paths)
Auth: None (public access)
Refresh: Quarterly (~3 month publication lag)
Coverage: Euro Area aggregate + 30 individual countries

Author: QUANTCLAW DATA Build Agent
Initiative: 0070
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from io import StringIO
import csv

BASE_URL = "https://data-api.ecb.europa.eu/service"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "ecb_supervisory_banking"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

# CBD2 key template: FREQ.REF_AREA.COUNT_AREA.CB_REP_SECTOR.BS_COUNT_SECTOR.
#   BS_NFC_ACTIVITY.CB_SECTOR_SIZE.CB_REP_FRAMEWRK.CB_ITEM.CB_PORTFOLIO.
#   CB_EXP_TYPE.CB_VAL_METHOD.MATURITY_RES.DATA_TYPE.CURRENCY_TRANS.UNIT_MEASURE
#
# Standard key for aggregate data:
#   Q.{area}.W0.{sector}._Z._Z.A.{fw}.{item}._Z._Z._Z._Z._Z._Z.{unit}

INDICATORS = {
    "CET1_RATIO": {
        "cb_item": "I4008",
        "framework": "A",
        "unit_measure": "PC",
        "name": "Common Equity Tier 1 (CET1) Ratio (%)",
        "description": "CET1 capital / risk-weighted assets — core solvency metric for banks",
        "unit": "%",
        "category": "capital_adequacy",
    },
    "TIER1_RATIO": {
        "cb_item": "I4002",
        "framework": "A",
        "unit_measure": "PC",
        "name": "Tier 1 Capital Ratio (%)",
        "description": "Tier 1 capital (CET1 + AT1) / risk-weighted assets",
        "unit": "%",
        "category": "capital_adequacy",
    },
    "TOTAL_CAPITAL_RATIO": {
        "cb_item": "I4001",
        "framework": "A",
        "unit_measure": "PC",
        "name": "Total Capital Ratio / Solvency Ratio (%)",
        "description": "Total own funds / total risk exposure — overall capital buffer",
        "unit": "%",
        "category": "capital_adequacy",
    },
    "NPL_RATIO": {
        "cb_item": "I3632",
        "framework": "F",
        "unit_measure": "PC",
        "name": "Non-Performing Loans Ratio (%)",
        "description": "Gross non-performing loans and advances / total gross loans and advances",
        "unit": "%",
        "category": "asset_quality",
    },
    "NPE_RATIO": {
        "cb_item": "I3614",
        "framework": "A",
        "unit_measure": "PC",
        "name": "Non-Performing Exposures Ratio (%)",
        "description": "Gross non-performing debt instruments / total gross debt instruments",
        "unit": "%",
        "category": "asset_quality",
    },
    "NPL_COVERAGE": {
        "cb_item": "I3617",
        "framework": "A",
        "unit_measure": "PC",
        "name": "NPL Coverage Ratio (%)",
        "description": "Total accumulated impairment / gross non-performing debt instruments",
        "unit": "%",
        "category": "asset_quality",
    },
    "ROE": {
        "cb_item": "I2003",
        "framework": "A",
        "unit_measure": "PC",
        "name": "Return on Equity (%)",
        "description": "Net income / shareholders' equity — bank profitability core metric",
        "unit": "%",
        "category": "profitability",
    },
    "ROA": {
        "cb_item": "I2004",
        "framework": "A",
        "unit_measure": "PC",
        "name": "Return on Assets (%)",
        "description": "Net income / total assets — efficiency measure",
        "unit": "%",
        "category": "profitability",
    },
    "COST_TO_INCOME": {
        "cb_item": "I2100",
        "framework": "A",
        "unit_measure": "PC",
        "name": "Cost-to-Income Ratio (%)",
        "description": "Operating expenses / operating income — operational efficiency",
        "unit": "%",
        "category": "profitability",
    },
    "LEVERAGE_RATIO": {
        "cb_item": "I3400",
        "framework": "A",
        "unit_measure": "PN",
        "name": "Leverage Ratio (Assets / Equity)",
        "description": "Total assets / total equity — equity multiplier leverage measure",
        "unit": "ratio",
        "category": "capital_adequacy",
    },
    "LCR": {
        "cb_item": "I3017",
        "framework": "A",
        "unit_measure": "PC",
        "name": "Liquidity Coverage Ratio (%)",
        "description": "HQLA / 30-day net outflows — short-term liquidity stress resilience",
        "unit": "%",
        "category": "liquidity",
    },
    "NSFR": {
        "cb_item": "I3214",
        "framework": "A",
        "unit_measure": "PC",
        "name": "Net Stable Funding Ratio (%)",
        "description": "Available stable funding / required stable funding — structural liquidity",
        "unit": "%",
        "category": "liquidity",
    },
    "LOAN_TO_DEPOSIT": {
        "cb_item": "I3006",
        "framework": "A",
        "unit_measure": "PC",
        "name": "Loan-to-Deposit Ratio (%)",
        "description": "Total loans / total deposits — funding structure indicator",
        "unit": "%",
        "category": "liquidity",
    },
    "RWA_DENSITY": {
        "cb_item": "I4011",
        "framework": "A",
        "unit_measure": "PC",
        "name": "Risk-Weighted Asset Density (%)",
        "description": "Risk-weighted assets / total assets — risk profile indicator",
        "unit": "%",
        "category": "capital_adequacy",
    },
}

COUNTRIES = {
    "U2": "Euro Area",
    "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "CY": "Cyprus",
    "CZ": "Czech Republic", "DE": "Germany", "DK": "Denmark", "EE": "Estonia",
    "ES": "Spain", "FI": "Finland", "FR": "France", "GB": "United Kingdom",
    "GR": "Greece", "HR": "Croatia", "HU": "Hungary", "IE": "Ireland",
    "IT": "Italy", "LT": "Lithuania", "LU": "Luxembourg", "LV": "Latvia",
    "MT": "Malta", "NL": "Netherlands", "NO": "Norway", "PL": "Poland",
    "PT": "Portugal", "RO": "Romania", "SE": "Sweden", "SI": "Slovenia",
    "SK": "Slovakia",
}

# Sector codes to try in priority order (broadest coverage first)
SECTOR_PRIORITY = ["66", "67", "57", "47", "11"]


def _cache_path(name: str) -> Path:
    safe = name.replace("/", "_").replace(":", "_")
    return CACHE_DIR / f"{safe}.json"


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


def _build_key(area: str, cb_item: str, framework: str, unit_measure: str, sector: str) -> str:
    """Build 16-dimension CBD2 SDMX series key."""
    return f"Q.{area}.W0.{sector}._Z._Z.A.{framework}.{cb_item}._Z._Z._Z._Z._Z._Z.{unit_measure}"


def _fetch_csv(key: str, last_n: int = 20, start_period: str = None) -> Dict:
    """Fetch CBD2 data via CSV format (bypasses ECB WAF on JSON key paths)."""
    url = f"{BASE_URL}/data/CBD2/{key}"
    params = {"format": "csvdata", "lastNObservations": last_n}
    if start_period:
        params["startPeriod"] = start_period
    headers = {"User-Agent": "QuantClaw-Data/1.0"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 404:
            return {"success": False, "error": "Series not found (HTTP 404)"}
        resp.raise_for_status()
        return {"success": True, "data": resp.text}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_csv(csv_text: str) -> List[Dict]:
    """Parse ECB CSV data response into time-series observations."""
    reader = csv.DictReader(StringIO(csv_text))
    observations = []
    for row in reader:
        period = row.get("TIME_PERIOD", "")
        value_str = row.get("OBS_VALUE", "")
        if period and value_str:
            try:
                observations.append({
                    "period": period,
                    "value": float(value_str),
                })
            except (ValueError, TypeError):
                continue
    observations.sort(key=lambda x: x["period"], reverse=True)
    return observations


def _fetch_indicator_for_area(indicator_key: str, area: str) -> Tuple[List[Dict], Optional[str]]:
    """Fetch indicator data trying multiple sector codes for robustness."""
    cfg = INDICATORS[indicator_key]
    cb_item = cfg["cb_item"]
    framework = cfg["framework"]
    unit_measure = cfg["unit_measure"]

    for sector in SECTOR_PRIORITY:
        key = _build_key(area, cb_item, framework, unit_measure, sector)
        result = _fetch_csv(key, last_n=20)
        if result["success"]:
            observations = _parse_csv(result["data"])
            if observations:
                return observations, None
        time.sleep(REQUEST_DELAY)

    return [], f"No data for {area} across all bank sectors"


def _compute_changes(data_points: List[Dict]) -> Tuple[Optional[float], Optional[float]]:
    """Compute period-over-period change and percentage change."""
    if len(data_points) < 2:
        return None, None
    latest = data_points[0]["value"]
    prev = data_points[1]["value"]
    if prev is None or prev == 0:
        return None, None
    change = round(latest - prev, 4)
    change_pct = round((change / abs(prev)) * 100, 4)
    return change, change_pct


def _detect_trend(data_points: List[Dict], threshold_pct: float = 5.0) -> Optional[str]:
    """Flag significant quarter-over-quarter changes."""
    if len(data_points) < 2:
        return None
    latest = data_points[0]["value"]
    prev = data_points[1]["value"]
    if prev is None or prev == 0:
        return None
    change_pct = ((latest - prev) / abs(prev)) * 100
    if abs(change_pct) >= threshold_pct:
        direction = "IMPROVING" if change_pct > 0 else "DETERIORATING"
        return f"{direction} ({change_pct:+.1f}% QoQ)"
    return None


def fetch_data(indicator: str, country: str = "U2", start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator for a given country."""
    indicator = indicator.upper()
    country = country.upper()

    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]

    cp = _cache_path(f"ind_{indicator}_{country}_{_params_hash({'s': start_date, 'e': end_date})}")
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    data_points, error = _fetch_indicator_for_area(indicator, country)

    if not data_points:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "country": country, "country_name": COUNTRIES.get(country, country),
                "error": error or "No observations returned"}

    if start_date:
        data_points = [d for d in data_points if d["period"] >= start_date]
    if end_date:
        data_points = [d for d in data_points if d["period"] <= end_date]

    if not data_points:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": "No data in requested date range"}

    change, change_pct = _compute_changes(data_points)
    trend = _detect_trend(data_points)

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "category": cfg["category"],
        "frequency": "quarterly",
        "country": country,
        "country_name": COUNTRIES.get(country, country),
        "latest_value": data_points[0]["value"],
        "latest_period": data_points[0]["period"],
        "period_change": change,
        "period_change_pct": change_pct,
        "trend_alert": trend,
        "data_points": data_points[:20],
        "total_observations": len(data_points),
        "dataflow": "CBD2",
        "source": f"{BASE_URL}/data/CBD2",
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
            "unit": v["unit"],
            "category": v["category"],
            "cb_item": v["cb_item"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None, country: str = "U2") -> Dict:
    """Get latest values for one or all indicators for a given country."""
    if indicator:
        return fetch_data(indicator, country=country)

    results = {}
    errors = []
    for key in INDICATORS:
        data = fetch_data(key, country=country)
        if data.get("success"):
            results[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
                "category": data["category"],
                "period_change": data.get("period_change"),
                "trend_alert": data.get("trend_alert"),
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})

    return {
        "success": True,
        "source": "ECB Supervisory Banking Statistics (CBD2)",
        "country": country,
        "country_name": COUNTRIES.get(country, country),
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_country_overview(country: str) -> Dict:
    """Get all available banking metrics for a specific country."""
    return get_latest(country=country.upper())


def compare_countries(indicator: str, countries: List[str]) -> Dict:
    """Cross-country comparison for a specific indicator."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    comparison = []
    for c in countries:
        c = c.upper()
        data = fetch_data(indicator, country=c)
        if data.get("success"):
            comparison.append({
                "country": c,
                "country_name": COUNTRIES.get(c, c),
                "latest_value": data["latest_value"],
                "latest_period": data["latest_period"],
                "period_change": data.get("period_change"),
                "period_change_pct": data.get("period_change_pct"),
            })
        else:
            comparison.append({
                "country": c,
                "country_name": COUNTRIES.get(c, c),
                "latest_value": None,
                "error": data.get("error", "No data"),
            })

    comparison.sort(key=lambda x: x.get("latest_value") or -999, reverse=True)

    return {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "unit": cfg["unit"],
        "comparison": comparison,
        "country_count": len(comparison),
        "timestamp": datetime.now().isoformat(),
    }


def get_dataflows() -> Dict:
    """List ECB banking-related dataflows."""
    url = f"{BASE_URL}/dataflow/ECB"
    headers = {
        "Accept": "application/vnd.sdmx.structure+xml;version=2.1",
        "User-Agent": "QuantClaw-Data/1.0",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()

        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.text)

        banking_keywords = ["bank", "supervis", "consolidat", "cbd", "capital",
                            "prudent", "ssm", "lending", "risk"]
        flows = []
        for elem in root.iter():
            if "Dataflow" in elem.tag and elem.attrib.get("id"):
                fid = elem.attrib.get("id", "")
                name = ""
                for child in elem:
                    if "Name" in child.tag:
                        name = child.text or ""
                        break
                if any(kw in (fid + name).lower() for kw in banking_keywords):
                    flows.append({"id": fid, "name": name})

        return {"success": True, "dataflows": flows, "count": len(flows)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- CLI ---

def _print_help():
    print("""
ECB Supervisory Banking Statistics (Initiative 0070)
Consolidated Banking Data (CBD2) — Capital, NPL, Profitability, Liquidity

Usage:
  python ecb_supervisory_banking.py                          # Euro area banking overview
  python ecb_supervisory_banking.py <INDICATOR>              # Specific indicator (Euro area)
  python ecb_supervisory_banking.py cet1                     # CET1 ratio trend
  python ecb_supervisory_banking.py npl                      # NPL ratio
  python ecb_supervisory_banking.py roe                      # Return on equity
  python ecb_supervisory_banking.py lcr                      # Liquidity coverage ratio
  python ecb_supervisory_banking.py leverage                 # Leverage ratio
  python ecb_supervisory_banking.py country DE               # Germany banking metrics
  python ecb_supervisory_banking.py country IT               # Italy banking metrics
  python ecb_supervisory_banking.py compare cet1 DE FR IT ES # Cross-country CET1 comparison
  python ecb_supervisory_banking.py dataflows                # List ECB banking dataflows
  python ecb_supervisory_banking.py list                     # List available indicators

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}/data/CBD2
Protocol: SDMX 2.1 REST (CSV format)
Coverage: Euro Area + 30 countries (quarterly)
""")


CLI_ALIASES = {
    "cet1": "CET1_RATIO",
    "tier1": "TIER1_RATIO",
    "capital": "TOTAL_CAPITAL_RATIO",
    "solvency": "TOTAL_CAPITAL_RATIO",
    "npl": "NPL_RATIO",
    "npe": "NPE_RATIO",
    "npl_coverage": "NPL_COVERAGE",
    "coverage": "NPL_COVERAGE",
    "roe": "ROE",
    "roa": "ROA",
    "cost_to_income": "COST_TO_INCOME",
    "cost-to-income": "COST_TO_INCOME",
    "leverage": "LEVERAGE_RATIO",
    "lcr": "LCR",
    "nsfr": "NSFR",
    "loan_to_deposit": "LOAN_TO_DEPOSIT",
    "rwa": "RWA_DENSITY",
}


def _resolve_indicator(name: str) -> str:
    """Resolve CLI alias or indicator name."""
    lower = name.lower().replace("-", "_")
    if lower in CLI_ALIASES:
        return CLI_ALIASES[lower]
    upper = name.upper()
    if upper in INDICATORS:
        return upper
    return upper


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
    elif args[0] in ("--help", "-h", "help"):
        _print_help()
    elif args[0] == "list":
        print(json.dumps(get_available_indicators(), indent=2, default=str))
    elif args[0] == "dataflows":
        print(json.dumps(get_dataflows(), indent=2, default=str))
    elif args[0] == "country":
        country = args[1] if len(args) > 1 else "U2"
        print(json.dumps(get_country_overview(country), indent=2, default=str))
    elif args[0] == "compare":
        if len(args) < 3:
            print('Usage: compare <indicator> <country1> <country2> ...')
            sys.exit(1)
        indicator = _resolve_indicator(args[1])
        countries = [c.upper() for c in args[2:]]
        print(json.dumps(compare_countries(indicator, countries), indent=2, default=str))
    else:
        indicator = _resolve_indicator(args[0])
        country = args[1].upper() if len(args) > 1 else "U2"
        result = fetch_data(indicator, country=country)
        print(json.dumps(result, indent=2, default=str))

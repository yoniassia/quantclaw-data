#!/usr/bin/env python3
"""
CBS Netherlands StatLine Module — Phase 1

Netherlands' official statistics: GDP growth, CPI inflation, labour market,
housing prices, foreign trade, government finance, and consumer/producer confidence.

Data Source: https://opendata.cbs.nl/ODataApi/odata/ (OData v3)
Protocol: OData REST (JSON)
Auth: None (open access)
Refresh: Monthly (most), Quarterly (GDP, housing, gov finance)
Coverage: Netherlands

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

BASE_URL = "https://opendata.cbs.nl/ODataApi/odata"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "cbs_netherlands"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.25

INDICATORS = {
    "GDP_GROWTH_YOY": {
        "table": "85880ENG",
        "name": "GDP Volume Growth YoY (%)",
        "description": "Quarterly GDP volume change vs same quarter previous year",
        "frequency": "quarterly",
        "unit": "%",
        "filters": {"TypeOfData": "A045299"},
        "value_field": "GrossDomesticProduct_2",
    },
    "GDP_GROWTH_QOQ": {
        "table": "85880ENG",
        "name": "GDP Volume Growth QoQ (%)",
        "description": "Quarterly GDP volume change vs previous quarter",
        "frequency": "quarterly",
        "unit": "%",
        "filters": {"TypeOfData": "A045300"},
        "value_field": "GrossDomesticProduct_2",
    },
    "CPI_INDEX": {
        "table": "86141ENG",
        "name": "Consumer Price Index (2025=100)",
        "description": "Netherlands CPI, all expenditure categories, base year 2025",
        "frequency": "monthly",
        "unit": "index (2025=100)",
        "filters": {"ExpenditureCategories": "T001112  "},
        "value_field": "CPI_1",
    },
    "CPI_ANNUAL_CHANGE": {
        "table": "86141ENG",
        "name": "CPI Annual Rate of Change (%)",
        "description": "Year-on-year change in consumer prices",
        "frequency": "monthly",
        "unit": "%",
        "filters": {"ExpenditureCategories": "T001112  "},
        "value_field": "AnnualRateOfChangeCPI_5",
    },
    "UNEMPLOYMENT_RATE": {
        "table": "80590eng",
        "name": "Unemployment Rate — Seasonally Adjusted (%)",
        "description": "ILO unemployment rate, age 15-75, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "filters": {"Sex": "T001038", "Age": "52052   "},
        "value_field": "SeasonallyAdjusted_8",
    },
    "EMPLOYED_LABOUR_FORCE": {
        "table": "80590eng",
        "name": "Employed Labour Force — Seasonally Adjusted (x1000)",
        "description": "Employed persons age 15-75, seasonally adjusted, in thousands",
        "frequency": "monthly",
        "unit": "x1000 persons",
        "filters": {"Sex": "T001038", "Age": "52052   "},
        "value_field": "SeasonallyAdjusted_4",
    },
    "HOUSE_PRICE_INDEX": {
        "table": "85822ENG",
        "name": "House Price Index (2020=100)",
        "description": "Price index for new and existing owner-occupied dwellings",
        "frequency": "quarterly",
        "unit": "index (2020=100)",
        "filters": {"TypeOfDwelling": "T001407"},
        "value_field": "PriceIndex_1",
    },
    "HOUSE_PRICE_CHANGE_YOY": {
        "table": "85822ENG",
        "name": "House Price Annual Change (%)",
        "description": "Year-on-year change in owner-occupied dwelling prices",
        "frequency": "quarterly",
        "unit": "%",
        "filters": {"TypeOfDwelling": "T001407"},
        "value_field": "ChangesComparedToThePreviousYear_3",
    },
    "TRADE_BALANCE": {
        "table": "85427ENG",
        "name": "Trade Balance — Goods (EUR mn)",
        "description": "Monthly goods trade balance, all countries, all SITC categories",
        "frequency": "monthly",
        "unit": "EUR mn",
        "filters": {"Countries": "T001047", "SITC": "T001082"},
        "value_field": "TradeBalance_5",
    },
    "EXPORTS": {
        "table": "85427ENG",
        "name": "Total Exports — Goods (EUR mn)",
        "description": "Monthly total export value of goods",
        "frequency": "monthly",
        "unit": "EUR mn",
        "filters": {"Countries": "T001047", "SITC": "T001082"},
        "value_field": "TotalExportValue_2",
    },
    "IMPORTS": {
        "table": "85427ENG",
        "name": "Total Imports — Goods (EUR mn)",
        "description": "Monthly total import value of goods",
        "frequency": "monthly",
        "unit": "EUR mn",
        "filters": {"Countries": "T001047", "SITC": "T001082"},
        "value_field": "TotalImportValue_1",
    },
    "GOV_BALANCE_PCT_GDP": {
        "table": "85968ENG",
        "name": "Government Balance (% of GDP)",
        "description": "General government sector balance as percentage of GDP",
        "frequency": "quarterly",
        "unit": "% of GDP",
        "filters": {},
        "value_field": "BalanceOfTheGeneralGovernmentSector_14",
    },
    "GOV_DEBT_PCT_GDP": {
        "table": "85968ENG",
        "name": "Government Debt EMU (% of GDP)",
        "description": "Maastricht/EMU government debt as percentage of GDP",
        "frequency": "quarterly",
        "unit": "% of GDP",
        "filters": {},
        "value_field": "GovernmentDebtEMU_15",
    },
    "CONSUMER_CONFIDENCE": {
        "table": "83693ENG",
        "name": "Consumer Confidence Indicator",
        "description": "Composite sentiment indicator, seasonally adjusted (-100 to +100)",
        "frequency": "monthly",
        "unit": "index points",
        "filters": {},
        "value_field": "ConsumerConfidence_1",
    },
    "ECONOMIC_CLIMATE": {
        "table": "83693ENG",
        "name": "Economic Climate Indicator",
        "description": "Sub-indicator of consumer confidence on economic outlook",
        "frequency": "monthly",
        "unit": "index points",
        "filters": {},
        "value_field": "EconomicClimate_2",
    },
    "PRODUCER_CONFIDENCE": {
        "table": "81234eng",
        "name": "Producer Confidence — Manufacturing",
        "description": "Sentiment indicator for manufacturing industry, seasonally adjusted",
        "frequency": "monthly",
        "unit": "index points",
        "filters": {
            "SectorBranchesSIC2008": "307500",
            "Margins": "MW00000",
            "SeasonalAdjustment": "A042500",
        },
        "value_field": "ProducerConfidence_1",
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


def _build_odata_filter(filters: Dict[str, str], start_period: str = None) -> str:
    """Build OData $filter string from dimension filters and optional start period."""
    parts = []
    for dim, val in filters.items():
        parts.append(f"{dim} eq '{val}'")
    if start_period:
        parts.append(f"Periods ge '{start_period}'")
    return " and ".join(parts) if parts else ""


def _parse_period(period_str: str) -> str:
    """Convert CBS period codes to readable format. E.g. 2025KW03 -> 2025-Q3, 2025MM06 -> 2025-06."""
    p = period_str.strip()
    if "KW" in p:
        year, q = p.split("KW")
        return f"{year}-Q{int(q)}"
    if "MM" in p:
        year, m = p.split("MM")
        return f"{year}-{m}"
    if "JJ" in p:
        return p.replace("JJ00", "")
    return p


def _period_sort_key(period_str: str) -> str:
    """Generate a sortable key from CBS period codes."""
    p = period_str.strip()
    if "KW" in p:
        year, q = p.split("KW")
        return f"{year}-{int(q):02d}Q"
    if "MM" in p:
        year, m = p.split("MM")
        return f"{year}-{m}M"
    if "JJ" in p:
        return p.replace("JJ00", "-99Y")
    return p


def _api_request(table: str, filters: Dict[str, str], value_field: str,
                 select_fields: List[str] = None, start_period: str = None,
                 max_pages: int = 5) -> Dict:
    """Fetch data from CBS OData v3 with pagination support."""
    url = f"{BASE_URL}/{table}/TypedDataSet"
    params = {"$format": "json"}

    odata_filter = _build_odata_filter(filters, start_period)
    if odata_filter:
        params["$filter"] = odata_filter

    fields = ["Periods", value_field]
    if select_fields:
        fields = list(set(fields + select_fields))
    params["$select"] = ",".join(fields)

    all_records = []
    page = 0

    while url and page < max_pages:
        try:
            if page == 0:
                resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            else:
                resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except requests.Timeout:
            return {"success": False, "error": "Request timed out"}
        except requests.ConnectionError:
            return {"success": False, "error": "Connection failed"}
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            return {"success": False, "error": f"HTTP {status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

        records = data.get("value", [])
        all_records.extend(records)
        url = data.get("odata.nextLink")
        page += 1

    return {"success": True, "data": all_records}


def _extract_observations(records: List[Dict], value_field: str) -> List[Dict]:
    """Extract and sort time-period/value pairs, filtering out nulls and annual totals."""
    results = []
    for rec in records:
        period = rec.get("Periods", "")
        val = rec.get(value_field)
        if val is None or period.strip().endswith("JJ00"):
            continue
        results.append({
            "period_raw": period.strip(),
            "period": _parse_period(period),
            "value": float(val),
        })

    results.sort(key=lambda x: _period_sort_key(x["period_raw"]), reverse=True)
    return results


def discover_catalog(query: str = None, language: str = "en") -> Dict:
    """Search the CBS OData catalog for available tables."""
    url = f"https://opendata.cbs.nl/ODataCatalog/Tables"
    params = {"$format": "json", "$filter": f"Language eq '{language}'"}
    if query:
        params["$filter"] += f" and substringof('{query}', Title)"

    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

    tables = []
    for item in data.get("value", []):
        tables.append({
            "id": item.get("Identifier", ""),
            "title": item.get("Title", ""),
            "frequency": item.get("Frequency", ""),
            "modified": item.get("Modified", ""),
        })

    return {"success": True, "tables": tables, "count": len(tables)}


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

    result = _api_request(
        table=cfg["table"],
        filters=cfg["filters"],
        value_field=cfg["value_field"],
        start_period=start_date,
    )
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _extract_observations(result["data"], cfg["value_field"])
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
        "latest_period": observations[0]["period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [{"period": o["period"], "value": o["value"]} for o in observations[:30]],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/{cfg['table']}/TypedDataSet",
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
        "source": "CBS Netherlands StatLine",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_macro_snapshot() -> Dict:
    """Get a concise macro-economic snapshot of the Netherlands."""
    keys = [
        "GDP_GROWTH_YOY", "CPI_ANNUAL_CHANGE", "UNEMPLOYMENT_RATE",
        "CONSUMER_CONFIDENCE", "TRADE_BALANCE", "GOV_BALANCE_PCT_GDP",
    ]
    snapshot = {}
    for key in keys:
        data = fetch_data(key)
        if data.get("success"):
            snapshot[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(snapshot),
        "country": "Netherlands",
        "snapshot": snapshot,
        "count": len(snapshot),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print(f"""
CBS Netherlands StatLine Module (Phase 1)

Usage:
  python cbs_netherlands.py                          # Latest values for all indicators
  python cbs_netherlands.py <INDICATOR>              # Fetch specific indicator
  python cbs_netherlands.py list                     # List available indicators
  python cbs_netherlands.py snapshot                 # Netherlands macro snapshot
  python cbs_netherlands.py catalog [QUERY]          # Search CBS table catalog

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<28s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: OData v3 REST (JSON)
Coverage: Netherlands
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "snapshot":
            print(json.dumps(get_macro_snapshot(), indent=2, default=str))
        elif cmd == "catalog":
            query = sys.argv[2] if len(sys.argv) > 2 else None
            print(json.dumps(discover_catalog(query), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))

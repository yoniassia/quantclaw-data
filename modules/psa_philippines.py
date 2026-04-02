#!/usr/bin/env python3
"""
Philippine Statistics Authority (PSA) OpenSTAT Module

Philippine macroeconomic data: GDP growth, CPI inflation, unemployment,
OFW compensation inflows (remittance proxy), merchandise trade balance,
agricultural crop production, and Producer Price Index.

Data Source: https://openstat.psa.gov.ph/PXWeb/api/v1/en/
Protocol: PxWeb REST API (POST JSON queries, GET for metadata)
Auth: None (fully open, no key required)
Refresh: Monthly/Quarterly depending on indicator
Coverage: Philippines

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

BASE_URL = "https://openstat.psa.gov.ph/PXWeb/api/v1/en"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "psa_philippines"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5

MONTH_TO_NUM = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    "january": "01", "february": "02", "march": "03", "april": "04",
    "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}

INDICATORS = {
    "gdp": {
        "name": "GDP Growth Rate (Real, Quarterly)",
        "description": "Year-on-year quarterly real GDP growth at constant 2018 prices, expenditure approach",
        "table": "DB/2B/NA/QT/1SUM/0022B5CEXQ2.px",
        "filters": {
            "Type of Expenditure": ["16"],
            "Type of Valuation": ["1"],
        },
        "time_dims": ["Year", "Period"],
        "date_type": "year_pair_quarterly",
        "frequency": "quarterly",
        "unit": "% YoY",
    },
    "cpi": {
        "name": "CPI Inflation Rate (All Items, YoY)",
        "description": "Monthly year-on-year CPI change for all income households, all items (2018=100)",
        "table": "DB/2M/PI/CPI/2018NEW/0012M4ACP23.px",
        "filters": {
            "Geolocation": ["0"],
            "Commodity Description": ["0"],
        },
        "time_dims": ["Year", "Period"],
        "date_type": "year_monthly",
        "frequency": "monthly",
        "unit": "% YoY",
    },
    "unemployment": {
        "name": "Unemployment Rate",
        "description": "Labor Force Survey unemployment rate, both sexes, all ages",
        "table": "DB/1B/LFS/0021B3GKEI2.px",
        "filters": {
            "Rates": ["2"],
            "Sex": ["0"],
        },
        "time_dims": ["Year", "Month"],
        "date_type": "year_monthly",
        "frequency": "quarterly",
        "unit": "%",
    },
    "remittances": {
        "name": "OFW Compensation Inflows (NPI)",
        "description": "Quarterly compensation inflow from overseas Filipino workers via National Accounts Net Primary Income, current prices",
        "table": "DB/2B/NA/QT/1SUM/0092B5CNPQ1.px",
        "filters": {
            "NPI": ["1"],
            "Type of Valuation": ["0"],
        },
        "time_dims": ["Year", "Period"],
        "date_type": "year_quarterly",
        "frequency": "quarterly",
        "unit": "Million PHP",
    },
    "trade": {
        "name": "Merchandise Trade Balance",
        "description": "Monthly merchandise exports, imports, and balance of trade in goods (FOB value)",
        "table": "DB/2L/IMT/SUM/0012L4DFTS0.px",
        "filters": {
            "Variables": ["0", "1", "2"],
        },
        "time_dims": ["Year", "Month"],
        "date_type": "year_monthly",
        "category_dims": ["Variables"],
        "frequency": "monthly",
        "unit": "Million USD",
    },
    "agriculture": {
        "name": "Major Crop Production",
        "description": "Annual volume of production for key Philippine crops (national total)",
        "table": "DB/2E/CS/0142E4EVCP1.px",
        "filters": {
            "Crop": ["0", "1", "17", "28", "36", "41", "44", "45"],
            "Geolocation": ["0"],
            "Period": ["6"],
        },
        "time_dims": ["Year"],
        "date_type": "year_only",
        "category_dims": ["Crop"],
        "frequency": "annual",
        "unit": "Metric Tons",
    },
    "ppi": {
        "name": "PPI Manufacturing (YoY Growth)",
        "description": "Producer Price Index year-on-year growth rate for manufacturing sector (2018=100)",
        "table": "DB/2M/PI/PPI/PPIM/0012M4CPPI2.px",
        "filters": {
            "Industry Group/Division": ["0"],
            "Item": ["1"],
        },
        "time_dims": ["Year", "Month"],
        "date_type": "year_monthly",
        "frequency": "quarterly",
        "unit": "% YoY",
    },
}


# --- Caching ---

def _cache_path(indicator: str, params_hash: str) -> Path:
    safe = indicator.replace("/", "_").replace(" ", "_")
    return CACHE_DIR / f"{safe}_{params_hash}.json"


def _params_hash(params: Any) -> str:
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


# --- Date Normalization ---

def _normalize_date(labels: List[str], date_type: str) -> Optional[str]:
    """Convert PxWeb dimension labels to a sortable date string.

    Skips aggregates (Annual, Ave, Total) so only actual periods are returned.
    """
    if not labels:
        return None

    if date_type == "year_pair_quarterly":
        year_label = labels[0]
        period_label = labels[1] if len(labels) > 1 else ""
        parts = year_label.split("-")
        year = parts[-1].strip() if len(parts) == 2 else year_label.strip()
        if period_label.startswith("Q"):
            return f"{year}-{period_label}"
        return None

    if date_type == "year_quarterly":
        year_label = labels[0].strip()
        period_label = labels[1] if len(labels) > 1 else ""
        if period_label.startswith("Q"):
            return f"{year_label}-{period_label}"
        return None

    if date_type == "year_monthly":
        year_label = labels[0].strip()
        if len(labels) > 1:
            month_num = MONTH_TO_NUM.get(labels[1].strip().lower())
            if month_num:
                return f"{year_label}-{month_num}"
            return None
        return year_label

    if date_type == "year_only":
        return labels[0].strip()

    return None


# --- PxWeb API ---

def _parse_json_response(resp: requests.Response) -> Any:
    """Parse JSON from a response, handling UTF-8 BOM that PSA API returns."""
    text = resp.text.lstrip("\ufeff")
    return json.loads(text)


def _get_table_metadata(table_path: str) -> Optional[Dict]:
    """GET table metadata to discover dimensions and value codes."""
    url = f"{BASE_URL}/{table_path}"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT,
                            headers={"User-Agent": "QuantClaw-Data/1.0"})
        resp.raise_for_status()
        meta = _parse_json_response(resp)
        if isinstance(meta, dict) and "variables" in meta:
            result = {"title": meta.get("title", ""), "variables": {}}
            for var in meta["variables"]:
                result["variables"][var["code"]] = {
                    "values": var["values"],
                    "valueTexts": var["valueTexts"],
                    "is_time": var.get("time", False),
                }
            return result
    except Exception:
        pass
    return None


def _post_query(table_path: str, query_body: Dict) -> Optional[Dict]:
    """POST a PxWeb query and return parsed JSON response."""
    url = f"{BASE_URL}/{table_path}"
    try:
        resp = requests.post(url, json=query_body, timeout=REQUEST_TIMEOUT,
                             headers={"User-Agent": "QuantClaw-Data/1.0",
                                      "Content-Type": "application/json"})
        resp.raise_for_status()
        data = _parse_json_response(resp)
        if isinstance(data, dict) and "error" in data:
            return None
        return data
    except Exception:
        pass
    return None


def _build_query(metadata: Dict, config: Dict) -> Dict:
    """Build PxWeb POST body from table metadata and indicator config.

    Filtered dimensions use explicit item selection. Time dimensions
    include all values, limited to the most recent 10 years for the
    year-level dimension to keep response sizes reasonable.
    """
    filters = config["filters"]
    time_dims = config["time_dims"]

    query = []
    for dim_code, dim_info in metadata["variables"].items():
        if dim_code in filters:
            query.append({
                "code": dim_code,
                "selection": {"filter": "item", "values": filters[dim_code]},
            })
        elif dim_code in time_dims:
            values = dim_info["values"]
            if "year" in dim_code.lower() and len(values) > 10:
                values = values[-10:]
            query.append({
                "code": dim_code,
                "selection": {"filter": "item", "values": values},
            })

    return {"query": query, "response": {"format": "json"}}


def _resolve_label(dim_code: str, idx: str, metadata: Dict) -> str:
    """Look up the human-readable label for a dimension value index."""
    if dim_code in metadata["variables"]:
        var_info = metadata["variables"][dim_code]
        try:
            pos = var_info["values"].index(idx)
            return var_info["valueTexts"][pos]
        except (ValueError, IndexError):
            pass
    return idx


def _parse_response(raw: Dict, metadata: Dict, config: Dict) -> List[Dict]:
    """Parse PxWeb JSON response into structured records."""
    if not raw or "data" not in raw:
        return []

    columns = raw.get("columns", [])
    dim_codes = [c["code"] for c in columns if c["type"] in ("d", "t")]
    time_dims = config["time_dims"]
    filters = config["filters"]
    category_dims = config.get("category_dims", [])
    date_type = config["date_type"]
    table_title = metadata.get("title", config["table"])

    records = []
    for row in raw.get("data", []):
        val_str = row["values"][0] if row.get("values") else None
        if not val_str or val_str.strip() in (".", "..", "...", ""):
            continue
        try:
            value = float(val_str)
        except (ValueError, TypeError):
            continue

        key_map = dict(zip(dim_codes, row.get("key", [])))

        time_labels = [_resolve_label(td, key_map[td], metadata)
                       for td in time_dims if td in key_map]
        date_str = _normalize_date(time_labels, date_type)
        if not date_str:
            continue

        category = {}
        for cd in category_dims:
            if cd in key_map:
                category[cd] = _resolve_label(cd, key_map[cd], metadata)

        record = {
            "date": date_str,
            "value": value,
            "indicator": config["name"],
            "unit": config["unit"],
            "source": f"PSA OpenSTAT: {table_title}",
            "table_id": config["table"],
        }
        if category:
            record["category"] = (list(category.values())[0]
                                  if len(category) == 1 else category)
        records.append(record)

    records.sort(key=lambda x: x["date"], reverse=True)
    return records


# --- Public API ---

def fetch_data(indicator: str) -> Dict:
    """Fetch data for a specific PSA indicator."""
    indicator = indicator.lower()
    if indicator not in INDICATORS:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }

    config = INDICATORS[indicator]

    cp = _cache_path(indicator, _params_hash({"indicator": indicator}))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    metadata = _get_table_metadata(config["table"])
    if not metadata:
        return {
            "success": False,
            "indicator": indicator,
            "name": config["name"],
            "error": "Failed to retrieve table metadata from PSA OpenSTAT",
        }

    query_body = _build_query(metadata, config)
    raw = _post_query(config["table"], query_body)
    if not raw:
        return {
            "success": False,
            "indicator": indicator,
            "name": config["name"],
            "error": "Failed to fetch data from PSA OpenSTAT",
        }

    records = _parse_response(raw, metadata, config)
    if not records:
        return {
            "success": False,
            "indicator": indicator,
            "name": config["name"],
            "error": "No valid observations returned",
        }

    period_change = period_change_pct = None
    if not config.get("category_dims") and len(records) >= 2:
        latest_v = records[0]["value"]
        prev_v = records[1]["value"]
        if prev_v and prev_v != 0:
            period_change = round(latest_v - prev_v, 4)
            period_change_pct = round((period_change / abs(prev_v)) * 100, 4)

    response = {
        "success": True,
        "indicator": indicator,
        "name": config["name"],
        "description": config["description"],
        "unit": config["unit"],
        "frequency": config["frequency"],
        "latest_value": records[0]["value"],
        "latest_period": records[0]["date"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": records[:30],
        "total_observations": len(records),
        "source": f"PSA OpenSTAT ({BASE_URL})",
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
        "source": "Philippine Statistics Authority (PSA) OpenSTAT",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
Philippine Statistics Authority (PSA) OpenSTAT Module

Usage:
  python psa_philippines.py                    # Latest key indicators summary
  python psa_philippines.py <indicator>         # Fetch specific indicator
  python psa_philippines.py list                # List available indicators

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<18s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: PxWeb REST API (POST JSON queries)
Coverage: Philippines
Auth: None required
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))

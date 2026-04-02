#!/usr/bin/env python3
"""
ILO ILOSTAT SDMX Module — Global Labour Market Statistics

Comprehensive global labour market data from the International Labour Organization:
unemployment rates, employment by sector, wages, labour productivity, working poverty,
informal employment, labour force participation, NEET rates, hours worked, and gender pay gap.
Covers 230+ countries with 100+ indicators from 1947 to present.

Data Source: https://sdmx.ilo.org/rest
Protocol: SDMX 2.1 REST (SDMX-JSON)
Auth: None (open access)
Refresh: Annual / Quarterly (ILO modelled estimates + national survey data)
Coverage: Global (230+ countries)

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

BASE_URL = "https://sdmx.ilo.org/rest"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "ilostat_labour"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5

SDMX_JSON_ACCEPT = "application/vnd.sdmx.data+json;version=1.0.0-wd"
SDMX_STRUCT_ACCEPT = "application/vnd.sdmx.structure+json;version=1.0.0-wd"

# Dimension key templates: dots separate positional dimensions per DSD
# {country} is always pos 0, FREQ (A=annual) is pos 1
INDICATORS = {
    "UNEMPLOYMENT": {
        "dataflow": "DF_UNE_2EAP_SEX_AGE_RT",
        "version": "1.0",
        "key_template": "{country}.A.UNE_2EAP_RT.{sex}.{age}",
        "default_dims": {"sex": "SEX_T", "age": "AGE_YTHADULT_YGE15"},
        "name": "Unemployment Rate (%)",
        "description": "Harmonized unemployment rate by sex and age — ILO modelled estimates",
        "unit": "%",
        "frequency": "annual",
    },
    "YOUTH_UNEMPLOYMENT": {
        "dataflow": "DF_UNE_2EAP_SEX_AGE_RT",
        "version": "1.0",
        "key_template": "{country}.A.UNE_2EAP_RT.{sex}.AGE_YTHADULT_Y15-24",
        "default_dims": {"sex": "SEX_T"},
        "name": "Youth Unemployment Rate, 15-24 (%)",
        "description": "Unemployment rate for ages 15-24 — political instability predictor",
        "unit": "%",
        "frequency": "annual",
    },
    "PARTICIPATION": {
        "dataflow": "DF_EAP_2WAP_SEX_AGE_RT",
        "version": "1.0",
        "key_template": "{country}.A.EAP_2WAP_RT.{sex}.{age}",
        "default_dims": {"sex": "SEX_T", "age": "AGE_YTHADULT_YGE15"},
        "name": "Labour Force Participation Rate (%)",
        "description": "Working-age population in labour force — ILO modelled estimates",
        "unit": "%",
        "frequency": "annual",
    },
    "EMPLOYMENT_BY_SECTOR": {
        "dataflow": "DF_EMP_TEMP_SEX_ECO_NB",
        "version": "1.0",
        "key_template": "{country}.A..{sex}.{sector}",
        "default_dims": {"sex": "SEX_T", "sector": "ECO_SECTOR_AGR+ECO_SECTOR_IND+ECO_SECTOR_SER+ECO_SECTOR_TOTAL"},
        "name": "Employment by Sector (thousands)",
        "description": "Employment by economic sector — agriculture, industry, services",
        "unit": "thousands",
        "frequency": "annual",
    },
    "WAGES": {
        "dataflow": "DF_EAR_EMTA_SEX_NB",
        "version": "1.0",
        "key_template": "{country}.A..{sex}",
        "default_dims": {"sex": "SEX_T"},
        "name": "Average Monthly Earnings (local currency)",
        "description": "Average monthly earnings of employees by sex",
        "unit": "local currency",
        "frequency": "annual",
    },
    "WAGES_BY_SECTOR": {
        "dataflow": "DF_EAR_EMTA_SEX_ECO_CUR_NB",
        "version": "1.0",
        "key_template": "{country}.A..{sex}.{sector}.{currency}",
        "default_dims": {"sex": "SEX_T", "sector": "ECO_SECTOR_TOTAL", "currency": "CUR_TYPE_LCU"},
        "name": "Average Monthly Earnings by Sector (local currency)",
        "description": "Average monthly earnings by sex, economic activity and currency",
        "unit": "local currency",
        "frequency": "annual",
    },
    "PRODUCTIVITY": {
        "dataflow": "DF_GDP_211P_NOC_NB",
        "version": "1.0",
        "key_template": "{country}.A.",
        "default_dims": {},
        "name": "Labour Productivity — GDP per Worker (2017 PPP $)",
        "description": "Output per worker, GDP constant 2017 international $ at PPP",
        "unit": "2017 PPP $",
        "frequency": "annual",
    },
    "WORKING_POVERTY": {
        "dataflow": "DF_SDG_0111_SEX_AGE_RT",
        "version": "1.0",
        "key_template": "{country}.A..{sex}.{age}",
        "default_dims": {"sex": "SEX_T", "age": "AGE_YTHADULT_YGE15"},
        "name": "Working Poverty Rate (%)",
        "description": "Employed persons living below US$2.15 PPP/day — SDG 1.1.1",
        "unit": "%",
        "frequency": "annual",
    },
    "INFORMAL_EMPLOYMENT": {
        "dataflow": "DF_SDG_0831_SEX_ECO_RT",
        "version": "1.0",
        "key_template": "{country}.A..{sex}.ECO_SECTOR_TOTAL",
        "default_dims": {"sex": "SEX_T"},
        "name": "Informal Employment Rate (%)",
        "description": "Proportion of informal employment — SDG 8.3.1",
        "unit": "%",
        "frequency": "annual",
    },
    "NEET": {
        "dataflow": "DF_EIP_2EET_SEX_RT",
        "version": "1.0",
        "key_template": "{country}.A..{sex}",
        "default_dims": {"sex": "SEX_T"},
        "name": "NEET Rate — Youth Not in Employment/Education/Training (%)",
        "description": "Share of youth not in employment, education or training — ILO modelled estimates",
        "unit": "%",
        "frequency": "annual",
    },
    "HOURS_WORKED": {
        "dataflow": "DF_HOW_XEES_SEX_NB",
        "version": "1.0",
        "key_template": "{country}.A..{sex}",
        "default_dims": {"sex": "SEX_T"},
        "name": "Mean Weekly Hours Worked per Employee",
        "description": "Mean weekly hours actually worked per employee by sex",
        "unit": "hours/week",
        "frequency": "annual",
    },
    "GENDER_PAY_GAP": {
        "dataflow": "DF_EAR_GGAP_OCU_RT",
        "version": "1.0",
        "key_template": "{country}.A..OCU_ISCO08_TOTAL",
        "default_dims": {},
        "name": "Gender Pay Gap (%)",
        "description": "Gender wage gap — all occupations",
        "unit": "%",
        "frequency": "annual",
    },
}

COUNTRY_ALIASES = {
    "US": "USA", "UK": "GBR", "DE": "DEU", "FR": "FRA", "JP": "JPN",
    "CN": "CHN", "IN": "IND", "BR": "BRA", "MX": "MEX", "ZA": "ZAF",
    "KR": "KOR", "AU": "AUS", "CA": "CAN", "IT": "ITA", "ES": "ESP",
    "RU": "RUS", "TR": "TUR", "AR": "ARG", "ID": "IDN", "SA": "SAU",
    "NG": "NGA", "EG": "EGY", "PK": "PAK", "BD": "BGD", "VN": "VNM",
    "TH": "THA", "PH": "PHL", "MY": "MYS", "CL": "CHL", "CO": "COL",
    "PE": "PER", "NL": "NLD", "BE": "BEL", "SE": "SWE", "CH": "CHE",
    "AT": "AUT", "PL": "POL", "CZ": "CZE", "RO": "ROU", "GR": "GRC",
    "PT": "PRT", "DK": "DNK", "NO": "NOR", "FI": "FIN", "IE": "IRL",
    "NZ": "NZL", "SG": "SGP", "HK": "HKG", "TW": "TWN", "IL": "ISR",
    "AE": "ARE", "KE": "KEN", "GH": "GHA", "ET": "ETH", "TZ": "TZA",
}

SECTOR_NAMES = {
    "ECO_SECTOR_TOTAL": "Total",
    "ECO_SECTOR_AGR": "Agriculture",
    "ECO_SECTOR_IND": "Industry",
    "ECO_SECTOR_SER": "Services",
    "ECO_SECTOR_NAG": "Non-agriculture",
}


def _resolve_country(code: str) -> str:
    code = code.upper()
    return COUNTRY_ALIASES.get(code, code)


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


def _parse_sdmx_json(raw: Dict, indicator_cfg: Dict) -> List[Dict]:
    """Extract time-series observations from ILO SDMX-JSON response."""
    try:
        structure = raw["data"]["structure"]
        datasets = raw["data"]["dataSets"]
        if not datasets:
            return []

        series_dims = structure["dimensions"]["series"]
        obs_dims = structure["dimensions"]["observation"]
        time_values = obs_dims[0]["values"]

        series_attrs = structure.get("attributes", {}).get("series", [])
        obs_attrs = structure.get("attributes", {}).get("observation", [])

        unit_idx = next((i for i, a in enumerate(series_attrs) if a["id"] == "UNIT_MEASURE"), None)

        source_idx = next((i for i, a in enumerate(obs_attrs) if a["id"] == "SOURCE"), None)

        results = []
        for series_key, series_data in datasets[0].get("series", {}).items():
            dim_indices = [int(x) for x in series_key.split(":")]
            dim_labels = {}
            for i, idx in enumerate(dim_indices):
                if i < len(series_dims):
                    dim = series_dims[i]
                    if idx < len(dim["values"]):
                        dim_labels[dim["id"]] = dim["values"][idx]["id"]
                        dim_labels[f"{dim['id']}_name"] = dim["values"][idx].get("name", dim["values"][idx]["id"])

            unit = None
            if unit_idx is not None:
                attr_val = series_data.get("attributes", [None] * (unit_idx + 1))[unit_idx]
                if isinstance(attr_val, int) and attr_val < len(series_attrs[unit_idx].get("values", [])):
                    unit = series_attrs[unit_idx]["values"][attr_val].get("name")

            for obs_idx, obs_vals in series_data.get("observations", {}).items():
                idx = int(obs_idx)
                if idx < len(time_values) and obs_vals and obs_vals[0] is not None:
                    obs_record = {
                        "time_period": time_values[idx]["id"],
                        "value": float(obs_vals[0]),
                        **dim_labels,
                    }
                    if unit:
                        obs_record["unit"] = unit

                    if source_idx is not None and len(obs_vals) > source_idx + 1:
                        src_val = obs_vals[source_idx + 1] if source_idx + 1 < len(obs_vals) else None
                        if isinstance(src_val, int) and src_val < len(obs_attrs[source_idx].get("values", [])):
                            obs_record["source_detail"] = obs_attrs[source_idx]["values"][src_val].get("name")

                    results.append(obs_record)

        results.sort(key=lambda x: x["time_period"], reverse=True)
        return results
    except (KeyError, IndexError, TypeError, ValueError):
        return []


def _api_request(dataflow: str, key: str, version: str = "1.0",
                 start_period: str = None, end_period: str = None,
                 last_n: int = 15) -> Dict:
    url = f"{BASE_URL}/data/ILO,{dataflow},{version}/{key}"
    params = {}
    if last_n and not start_period:
        params["lastNObservations"] = last_n
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period
    headers = {"Accept": SDMX_JSON_ACCEPT}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        body = ""
        try:
            body = e.response.text[:200] if e.response is not None else ""
        except Exception:
            pass
        if status == 404:
            return {"success": False, "error": f"No data found (HTTP 404). {body}".strip()}
        return {"success": False, "error": f"HTTP {status}: {body}".strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _build_key(indicator: str, country: str = None, **overrides) -> str:
    cfg = INDICATORS[indicator]
    template = cfg["key_template"]
    dims = {**cfg["default_dims"], **overrides}
    dims["country"] = _resolve_country(country) if country else ""
    return template.format(**dims)


def fetch_data(indicator: str, country: str = None,
               start_period: str = None, end_period: str = None,
               sex: str = None, age: str = None, sector: str = None,
               currency: str = None, last_n: int = 15) -> Dict:
    """Fetch a specific indicator with optional country/dimension filters."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}",
                "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]

    overrides = {}
    if sex:
        overrides["sex"] = sex
    if age:
        overrides["age"] = age
    if sector:
        overrides["sector"] = sector
    if currency:
        overrides["currency"] = currency

    key = _build_key(indicator, country, **overrides)

    cache_params = {"indicator": indicator, "key": key, "start": start_period, "end": end_period, "last_n": last_n}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(cfg["dataflow"], key, cfg["version"],
                          start_period=start_period, end_period=end_period,
                          last_n=last_n)

    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "country": _resolve_country(country) if country else "ALL",
                "error": result["error"]}

    observations = _parse_sdmx_json(result["data"], cfg)
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "country": _resolve_country(country) if country else "ALL",
                "error": "No observations returned"}

    has_multiple_series = len(set(
        tuple((k, v) for k, v in o.items() if k not in ("time_period", "value", "unit", "source_detail"))
        for o in observations
    )) > 1

    if has_multiple_series:
        grouped = {}
        for obs in observations:
            eco = obs.get("ECO", obs.get("REF_AREA", "ALL"))
            eco_name = obs.get("ECO_name", obs.get("REF_AREA_name", eco))
            label = SECTOR_NAMES.get(eco, eco_name)
            if label not in grouped:
                grouped[label] = []
            grouped[label].append({"period": obs["time_period"], "value": obs["value"]})

        for g in grouped.values():
            g.sort(key=lambda x: x["period"], reverse=True)

        response = {
            "success": True,
            "indicator": indicator,
            "name": cfg["name"],
            "description": cfg["description"],
            "unit": cfg["unit"],
            "frequency": cfg["frequency"],
            "country": _resolve_country(country) if country else "ALL",
            "series": {k: v[:15] for k, v in grouped.items()},
            "series_count": len(grouped),
            "source": f"{BASE_URL}/data/ILO,{cfg['dataflow']},{cfg['version']}/{key}",
            "timestamp": datetime.now().isoformat(),
        }
    else:
        latest = observations[0]
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
            "country": latest.get("REF_AREA", _resolve_country(country) if country else "ALL"),
            "country_name": latest.get("REF_AREA_name", ""),
            "latest_value": latest["value"],
            "latest_period": latest["time_period"],
            "period_change": period_change,
            "period_change_pct": period_change_pct,
            "data_points": [{"period": o["time_period"], "value": o["value"]} for o in observations[:30]],
            "total_observations": len(observations),
            "source": f"{BASE_URL}/data/ILO,{cfg['dataflow']},{cfg['version']}/{key}",
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


def get_latest(indicator: str = None, country: str = None) -> Dict:
    """Get latest values for one or all indicators."""
    if indicator:
        return fetch_data(indicator, country)

    summary_indicators = [
        "UNEMPLOYMENT", "YOUTH_UNEMPLOYMENT", "PARTICIPATION",
        "PRODUCTIVITY", "NEET", "HOURS_WORKED",
    ]
    country = country or "USA"
    results = {}
    errors = []
    for key in summary_indicators:
        data = fetch_data(key, country)
        if data.get("success") and "latest_value" in data:
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
        "source": "ILO ILOSTAT SDMX",
        "country": _resolve_country(country),
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_dataflows(search: str = None) -> Dict:
    """List available ILOSTAT dataflows (100+ indicators)."""
    cache_params = {"action": "dataflows", "search": search}
    cp = _cache_path("_dataflows", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    url = f"{BASE_URL}/dataflow/ILO"
    headers = {"Accept": SDMX_STRUCT_ACCEPT}
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

    dataflows = data.get("data", {}).get("dataflows", [])
    results = []
    for df in dataflows:
        dfid = df.get("id", "")
        names = df.get("names", df.get("name", {}))
        name_en = names.get("en", "") if isinstance(names, dict) else str(names)
        if search:
            if search.lower() not in name_en.lower() and search.upper() not in dfid:
                continue
        results.append({"id": dfid, "name": name_en})

    response = {
        "success": True,
        "dataflows": results,
        "count": len(results),
        "search": search,
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def get_country_comparison(indicator: str, countries: List[str]) -> Dict:
    """Compare an indicator across multiple countries."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}"}

    comparison = {}
    errors = []
    for c in countries:
        data = fetch_data(indicator, c)
        if data.get("success") and "latest_value" in data:
            comparison[_resolve_country(c)] = {
                "value": data["latest_value"],
                "period": data["latest_period"],
                "country_name": data.get("country_name", ""),
            }
        else:
            errors.append({"country": _resolve_country(c), "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "indicator": indicator,
        "name": INDICATORS[indicator]["name"],
        "unit": INDICATORS[indicator]["unit"],
        "comparison": comparison,
        "errors": errors if errors else None,
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
ILO ILOSTAT SDMX Module — Global Labour Market Statistics

Usage:
  python ilostat_labour.py                                  # Summary for USA (default)
  python ilostat_labour.py unemployment US                  # US unemployment rate
  python ilostat_labour.py youth_unemployment ZA            # South Africa youth unemployment
  python ilostat_labour.py participation BR                 # Brazil labour force participation
  python ilostat_labour.py employment_by_sector IN          # India employment by sector
  python ilostat_labour.py wages DE                         # Germany mean wages
  python ilostat_labour.py productivity JP                  # Japan labour productivity
  python ilostat_labour.py working_poverty IN               # India working poverty rate
  python ilostat_labour.py informal_employment MX           # Mexico informal employment
  python ilostat_labour.py neet ZA                          # South Africa NEET rate
  python ilostat_labour.py hours_worked US                  # USA hours worked
  python ilostat_labour.py gender_pay_gap US                # USA gender pay gap
  python ilostat_labour.py compare US,DE,JP,CN              # Cross-country comparison
  python ilostat_labour.py dataflows                        # List all available indicators
  python ilostat_labour.py dataflows unemployment           # Search dataflows
  python ilostat_labour.py list                             # Module indicator list

Country codes: ISO-2 (US, DE, JP) or ISO-3 (USA, DEU, JPN) accepted.

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: SDMX 2.1 REST (JSON)
Coverage: 230+ countries, 1947–present
""")


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
        search = args[1] if len(args) > 1 else None
        result = get_dataflows(search)
        if result.get("success"):
            for df in result["dataflows"][:50]:
                print(f"  {df['id']:<45s} {df['name']}")
            print(f"\n  Total: {result['count']} dataflows" + (f" matching '{search}'" if search else ""))
        else:
            print(json.dumps(result, indent=2, default=str))
    elif args[0] == "compare":
        if len(args) < 2:
            print("Usage: python ilostat_labour.py compare US,DE,JP [indicator]")
            sys.exit(1)
        countries = args[1].split(",")
        indicator = args[2] if len(args) > 2 else "UNEMPLOYMENT"
        result = get_country_comparison(indicator, countries)
        print(json.dumps(result, indent=2, default=str))
    else:
        indicator = args[0].upper()
        country = args[1] if len(args) > 1 else None
        if indicator in INDICATORS:
            result = fetch_data(indicator, country)
        else:
            result = fetch_data(indicator, country)
        print(json.dumps(result, indent=2, default=str))

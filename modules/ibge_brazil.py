#!/usr/bin/env python3
"""
Brazil IBGE SIDRA Module — Instituto Brasileiro de Geografia e Estatística

Macro-economic indicators for Brazil: GDP, IPCA inflation, unemployment (PNAD),
industrial production (PIM-PF), and retail sales (PMC).

Data Source: https://servicodados.ibge.gov.br/api/v3/agregados
Protocol: REST (JSON)
Auth: None (open access)
Refresh: Monthly (IPCA, PIM-PF, PMC, unemployment), Quarterly (GDP)
Coverage: Brazil (national)

Author: QUANTCLAW DATA Build Agent
Initiative: 0048
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://servicodados.ibge.gov.br/api/v3/agregados"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "ibge_brazil"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5

INDICATORS = {
    "GDP_YOY": {
        "table": "5932",
        "variable": "6561",
        "name": "GDP Growth YoY (%)",
        "description": "Quarterly GDP growth rate vs same quarter previous year",
        "frequency": "quarterly",
        "unit": "%",
        "classificacao": "11255[90707]",
        "periods": 12,
    },
    "GDP_QOQ": {
        "table": "5932",
        "variable": "6564",
        "name": "GDP Growth QoQ (%)",
        "description": "Quarterly GDP growth rate vs previous quarter (seasonally adjusted)",
        "frequency": "quarterly",
        "unit": "%",
        "classificacao": "11255[90707]",
        "periods": 12,
    },
    "IPCA_MONTHLY": {
        "table": "1737",
        "variable": "63",
        "name": "IPCA Monthly Inflation (%)",
        "description": "IPCA consumer price index, monthly percentage change",
        "frequency": "monthly",
        "unit": "%",
        "classificacao": None,
        "periods": 24,
    },
    "IPCA_12M": {
        "table": "1737",
        "variable": "2265",
        "name": "IPCA 12-Month Cumulative (%)",
        "description": "IPCA consumer price index, 12-month rolling accumulation",
        "frequency": "monthly",
        "unit": "%",
        "classificacao": None,
        "periods": 24,
    },
    "IPCA_YTD": {
        "table": "1737",
        "variable": "69",
        "name": "IPCA Year-to-Date (%)",
        "description": "IPCA consumer price index, year-to-date accumulation",
        "frequency": "monthly",
        "unit": "%",
        "classificacao": None,
        "periods": 24,
    },
    "IPCA_INDEX": {
        "table": "1737",
        "variable": "2266",
        "name": "IPCA Price Index (Dec 1993=100)",
        "description": "IPCA consumer price index level, base December 1993 = 100",
        "frequency": "monthly",
        "unit": "Index",
        "classificacao": None,
        "periods": 24,
    },
    "UNEMPLOYMENT": {
        "table": "6381",
        "variable": "4099",
        "name": "Unemployment Rate — PNAD Contínua (%)",
        "description": "PNAD Contínua unemployment rate, population aged 14+",
        "frequency": "monthly",
        "unit": "%",
        "classificacao": None,
        "periods": 24,
    },
    "INDUSTRIAL_PRODUCTION": {
        "table": "8888",
        "variable": "12607",
        "name": "Industrial Production Index PIM-PF (2022=100)",
        "description": "PIM-PF seasonally adjusted index, general industry (CNAE 2.0)",
        "frequency": "monthly",
        "unit": "Index",
        "classificacao": "544[129314]",
        "periods": 24,
    },
    "RETAIL_SALES": {
        "table": "8881",
        "variable": "11709",
        "name": "Retail Sales YoY — PMC Broad (%)",
        "description": "PMC broad retail sales volume, month vs same month prior year",
        "frequency": "monthly",
        "unit": "%",
        "classificacao": "11046[56736]",
        "periods": 24,
    },
}

CLI_ALIASES = {
    "gdp": ["GDP_YOY", "GDP_QOQ"],
    "ipca": ["IPCA_MONTHLY", "IPCA_12M"],
    "inflation": ["IPCA_MONTHLY", "IPCA_12M"],
    "unemployment": ["UNEMPLOYMENT"],
    "industrial_production": ["INDUSTRIAL_PRODUCTION"],
    "industry": ["INDUSTRIAL_PRODUCTION"],
    "retail": ["RETAIL_SALES"],
    "retail_sales": ["RETAIL_SALES"],
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


def _parse_period(period_str: str, frequency: str = "monthly") -> str:
    """Convert IBGE period format to human-readable date string.

    Monthly: YYYYMM -> YYYY-MM
    Quarterly: YYYYQQ -> YYYY-QN (where QQ is 01-04)
    Annual: YYYY -> YYYY
    """
    if len(period_str) == 6:
        year = period_str[:4]
        part = period_str[4:]
        if frequency == "quarterly":
            return f"{year}-Q{int(part)}"
        return f"{year}-{part}"
    elif len(period_str) == 4:
        return period_str
    return period_str


def _build_url(table: str, variable: str) -> str:
    return f"{BASE_URL}/{table}/variaveis/{variable}"


def _api_request(table: str, variable: str, periods: int = 24,
                 classificacao: Optional[str] = None) -> Dict:
    url = _build_url(table, variable)
    params = {
        "localidades": "N1[all]",
        "periodos": f"-{periods}",
    }
    if classificacao:
        params["classificacao"] = classificacao

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
        if status == 404:
            return {"success": False, "error": f"Table/variable not found (HTTP 404)"}
        if status == 500:
            return {"success": False, "error": "IBGE server error (HTTP 500) — table may be unavailable"}
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_ibge_response(raw: list, frequency: str = "monthly") -> List[Dict]:
    """Extract period/value pairs from IBGE SIDRA JSON response."""
    results = []
    try:
        for var_block in raw:
            var_name = var_block.get("variavel", "")
            unit = var_block.get("unidade", "")
            for result_set in var_block.get("resultados", []):
                for series in result_set.get("series", []):
                    location = series.get("localidade", {}).get("nome", "Brasil")
                    for period, value in series.get("serie", {}).items():
                        if value in (None, "", "..", "...", "-"):
                            continue
                        try:
                            numeric_val = float(value)
                        except (ValueError, TypeError):
                            continue
                        results.append({
                            "period_raw": period,
                            "period": _parse_period(period, frequency),
                            "value": numeric_val,
                            "variable": var_name,
                            "unit": unit,
                            "location": location,
                        })
    except (KeyError, IndexError, TypeError, ValueError):
        pass

    results.sort(key=lambda x: x["period_raw"], reverse=True)
    return results


def fetch_data(indicator: str, periods: Optional[int] = None) -> Dict:
    """Fetch a specific indicator with optional period count."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }

    cfg = INDICATORS[indicator]
    n_periods = periods or cfg["periods"]
    cache_params = {"indicator": indicator, "periods": n_periods}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(
        cfg["table"], cfg["variable"],
        periods=n_periods,
        classificacao=cfg.get("classificacao"),
    )
    if not result["success"]:
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": result["error"],
        }

    observations = _parse_ibge_response(result["data"], frequency=cfg["frequency"])
    if not observations:
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": "No valid observations returned (all values empty or unavailable)",
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
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [
            {"period": o["period"], "value": o["value"]}
            for o in observations[:30]
        ],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/{cfg['table']}/variaveis/{cfg['variable']}",
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
            "variable": v["variable"],
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
        "source": "IBGE — Instituto Brasileiro de Geografia e Estatística",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
Brazil IBGE SIDRA Module (Initiative 0048)

Usage:
  python ibge_brazil.py                       # Latest values for all indicators
  python ibge_brazil.py <INDICATOR>           # Fetch specific indicator
  python ibge_brazil.py list                  # List available indicators
  python ibge_brazil.py gdp                   # GDP quarterly (YoY + QoQ)
  python ibge_brazil.py ipca                  # IPCA inflation (monthly + 12m)
  python ibge_brazil.py unemployment          # PNAD unemployment rate
  python ibge_brazil.py industrial_production # PIM-PF industrial output
  python ibge_brazil.py retail                # PMC retail sales

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"\nAliases: {', '.join(CLI_ALIASES.keys())}")
    print(f"\nSource: {BASE_URL}")
    print("Protocol: REST (JSON, no auth required)")
    print("Coverage: Brazil (national)")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd.lower() in CLI_ALIASES:
            keys = CLI_ALIASES[cmd.lower()]
            for key in keys:
                result = fetch_data(key)
                print(json.dumps(result, indent=2, default=str))
                if len(keys) > 1:
                    print()
                time.sleep(REQUEST_DELAY)
        elif cmd.upper() in INDICATORS:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
        else:
            print(json.dumps(
                {"success": False, "error": f"Unknown command: {cmd}",
                 "available_indicators": list(INDICATORS.keys()),
                 "available_aliases": list(CLI_ALIASES.keys())},
                indent=2,
            ))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))

#!/usr/bin/env python3
"""
IMF Enhanced Data Module — FAS + FSI + CPIS + CDIS + GFS

Five specialized IMF databases via DBnomics proxy API:
  - Financial Access Survey (FAS): banking penetration (ATMs, branches, accounts)
  - Financial Soundness Indicators (FSI): banking health (capital, NPLs, ROE/ROA)
  - Coordinated Portfolio Investment Survey (CPIS): cross-border portfolio holdings
  - Coordinated Direct Investment Survey (CDIS): cross-border FDI positions
  - Government Finance Statistics (GFS): fiscal revenue, expenditure, debt

Data Source: IMF via https://api.db.nomics.world/v22/ (DBnomics mirror)
Auth: None (open access)
Refresh: Annual (FAS, CPIS, CDIS, GFS), Quarterly (FSI)
Coverage: 190+ countries

Author: QUANTCLAW DATA Build Agent
Initiative: 0039
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

DBNOMICS_BASE = "https://api.db.nomics.world/v22"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "imf_enhanced"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

INDICATORS = {
    # ── FAS: Financial Access Survey ─────────────────────────────────
    "FAS_ATMS_PER_100K": {
        "database": "FAS",
        "series_key": "A.{country}.FCAA_NUM",
        "name": "ATMs per 100,000 Adults",
        "description": "Number of automated teller machines per 100,000 adults",
        "frequency": "annual",
        "unit": "per 100k adults",
        "category": "fas",
    },
    "FAS_BRANCHES_PER_100K": {
        "database": "FAS",
        "series_key": "A.{country}.FCBODCA_NUM",
        "name": "Commercial Bank Branches per 100,000 Adults",
        "description": "Number of commercial bank branches (excl. headquarters) per 100,000 adults",
        "frequency": "annual",
        "unit": "per 100k adults",
        "category": "fas",
    },
    "FAS_ATMS_PER_1000KM2": {
        "database": "FAS",
        "series_key": "A.{country}.FCAK_NUM",
        "name": "ATMs per 1,000 km²",
        "description": "Number of ATMs per 1,000 square kilometers",
        "frequency": "annual",
        "unit": "per 1000 km²",
        "category": "fas",
    },
    "FAS_BRANCHES_PER_1000KM2": {
        "database": "FAS",
        "series_key": "A.{country}.FCBODCK_NUM",
        "name": "Bank Branches per 1,000 km²",
        "description": "Number of commercial bank branches per 1,000 square kilometers",
        "frequency": "annual",
        "unit": "per 1000 km²",
        "category": "fas",
    },
    "FAS_DEPOSIT_ACCTS_PER_1000": {
        "database": "FAS",
        "series_key": "A.{country}.FCDODCHA_NUM",
        "name": "Deposit Accounts per 1,000 Adults",
        "description": "Household deposit accounts with commercial banks per 1,000 adults",
        "frequency": "annual",
        "unit": "per 1000 adults",
        "category": "fas",
    },
    "FAS_MOBILE_MONEY_ACTIVE": {
        "database": "FAS",
        "series_key": "A.{country}.FCMAAA_NUM",
        "name": "Active Mobile Money Accounts per 1,000 Adults",
        "description": "Number of active mobile money accounts per 1,000 adults",
        "frequency": "annual",
        "unit": "per 1000 adults",
        "category": "fas",
    },
    "FAS_MOBILE_MONEY_REGISTERED": {
        "database": "FAS",
        "series_key": "A.{country}.FCMARA_NUM",
        "name": "Registered Mobile Money Accounts per 1,000 Adults",
        "description": "Number of registered mobile money accounts per 1,000 adults",
        "frequency": "annual",
        "unit": "per 1000 adults",
        "category": "fas",
    },

    # ── FSI: Financial Soundness Indicators ──────────────────────────
    "FSI_NPL_RATIO": {
        "database": "FSI",
        "series_key": "A.{country}.FSANL_PT",
        "name": "Non-performing Loans to Total Gross Loans",
        "description": "Core FSI: ratio of non-performing loans to total gross loans for deposit takers",
        "frequency": "annual",
        "unit": "%",
        "category": "fsi",
    },
    "FSI_REGULATORY_CAPITAL": {
        "database": "FSI",
        "series_key": "A.{country}.FSKRC_PT",
        "name": "Regulatory Capital to Risk-Weighted Assets",
        "description": "Core FSI: total regulatory capital as share of risk-weighted assets",
        "frequency": "annual",
        "unit": "%",
        "category": "fsi",
    },
    "FSI_CET1_RATIO": {
        "database": "FSI",
        "series_key": "A.{country}.FSCET_PT",
        "name": "Common Equity Tier 1 to Risk-Weighted Assets",
        "description": "Core FSI: CET1 capital ratio for deposit takers",
        "frequency": "annual",
        "unit": "%",
        "category": "fsi",
    },
    "FSI_ROA": {
        "database": "FSI",
        "series_key": "A.{country}.FSERA_PT",
        "name": "Return on Assets (Deposit Takers)",
        "description": "Core FSI: deposit takers' return on assets",
        "frequency": "annual",
        "unit": "%",
        "category": "fsi",
    },
    "FSI_ROE": {
        "database": "FSI",
        "series_key": "A.{country}.FSERE_PT",
        "name": "Return on Equity (Deposit Takers)",
        "description": "Core FSI: deposit takers' return on equity",
        "frequency": "annual",
        "unit": "%",
        "category": "fsi",
    },

    # ── CPIS: Coordinated Portfolio Investment Survey ────────────────
    "CPIS_TOTAL_ASSETS": {
        "database": "CPIS",
        "series_key": "A.{country}.I_A_T_T_T_BP6_USD.T.T.W00",
        "name": "Total Portfolio Investment Assets (World)",
        "description": "Total cross-border portfolio investment asset holdings, all instruments, all holders, vs world",
        "frequency": "annual",
        "unit": "USD",
        "category": "cpis",
    },
    "CPIS_EQUITY_ASSETS": {
        "database": "CPIS",
        "series_key": "A.{country}.I_A_E_T_T_BP6_USD.T.T.W00",
        "name": "Portfolio Equity Assets (World)",
        "description": "Cross-border equity and investment fund shares holdings vs world",
        "frequency": "annual",
        "unit": "USD",
        "category": "cpis",
    },
    "CPIS_DEBT_LT_ASSETS": {
        "database": "CPIS",
        "series_key": "A.{country}.I_A_D_L_T_BP6_USD.T.T.W00",
        "name": "Portfolio Long-term Debt Assets (World)",
        "description": "Cross-border long-term debt securities holdings vs world",
        "frequency": "annual",
        "unit": "USD",
        "category": "cpis",
    },

    # ── CDIS: Coordinated Direct Investment Survey ───────────────────
    "CDIS_INWARD_EQUITY": {
        "database": "CDIS",
        "series_key": "A.{country}.IIWE_BP6_USD.W00",
        "name": "Inward FDI Equity Positions (World)",
        "description": "Inward direct investment equity positions (net) from all economies",
        "frequency": "annual",
        "unit": "USD mn",
        "category": "cdis",
    },
    "CDIS_INWARD_DEBT_ASSETS": {
        "database": "CDIS",
        "series_key": "A.{country}.IIWDA_BP6_USD.W00",
        "name": "Inward FDI Debt Assets (World)",
        "description": "Inward direct investment debt instruments assets (gross) from all economies",
        "frequency": "annual",
        "unit": "USD mn",
        "category": "cdis",
    },
    "CDIS_INWARD_DEBT_LIAB": {
        "database": "CDIS",
        "series_key": "A.{country}.IIWDL_BP6_USD.W00",
        "name": "Inward FDI Debt Liabilities (World)",
        "description": "Inward direct investment debt instruments liabilities (gross) from all economies",
        "frequency": "annual",
        "unit": "USD mn",
        "category": "cdis",
    },
    "CDIS_OUTWARD_EQUITY": {
        "database": "CDIS",
        "series_key": "A.{country}.IOWE_BP6_USD.W00",
        "name": "Outward FDI Equity Positions (World)",
        "description": "Outward direct investment equity positions (net) to all economies",
        "frequency": "annual",
        "unit": "USD mn",
        "category": "cdis",
    },
    "CDIS_OUTWARD_DEBT_ASSETS": {
        "database": "CDIS",
        "series_key": "A.{country}.IOWDA_BP6_USD.W00",
        "name": "Outward FDI Debt Assets (World)",
        "description": "Outward direct investment debt instruments assets (gross) to all economies",
        "frequency": "annual",
        "unit": "USD mn",
        "category": "cdis",
    },
    "CDIS_OUTWARD_DEBT_LIAB": {
        "database": "CDIS",
        "series_key": "A.{country}.IOWDL_BP6_USD.W00",
        "name": "Outward FDI Debt Liabilities (World)",
        "description": "Outward direct investment debt instruments liabilities (gross) to all economies",
        "frequency": "annual",
        "unit": "USD mn",
        "category": "cdis",
    },

    # ── GFS: Government Finance Statistics (Main Aggregates) ─────────
    "GFS_REVENUE": {
        "database": "GFSMAB",
        "series_key": "A.{country}.S13.XDC.G1__Z",
        "name": "General Government Revenue",
        "description": "Total general government revenue in domestic currency (billions)",
        "frequency": "annual",
        "unit": "domestic currency bn",
        "category": "gfs",
    },
    "GFS_EXPENSE": {
        "database": "GFSMAB",
        "series_key": "A.{country}.S13.XDC.G2__Z",
        "name": "General Government Expense",
        "description": "Total general government expense in domestic currency (billions)",
        "frequency": "annual",
        "unit": "domestic currency bn",
        "category": "gfs",
    },
    "GFS_TAX_REVENUE": {
        "database": "GFSMAB",
        "series_key": "A.{country}.S13.XDC.G11__Z",
        "name": "Tax Revenue",
        "description": "General government tax revenue in domestic currency (billions)",
        "frequency": "annual",
        "unit": "domestic currency bn",
        "category": "gfs",
    },
    "GFS_EXPENDITURE": {
        "database": "GFSMAB",
        "series_key": "A.{country}.S13.XDC.G2M__Z",
        "name": "Total Government Expenditure",
        "description": "General government total expenditure in domestic currency (billions)",
        "frequency": "annual",
        "unit": "domestic currency bn",
        "category": "gfs",
    },
    "GFS_SOCIAL_BENEFITS": {
        "database": "GFSMAB",
        "series_key": "A.{country}.S13.XDC.G27__Z",
        "name": "Social Benefits Expense",
        "description": "General government social benefits expense in domestic currency (billions)",
        "frequency": "annual",
        "unit": "domestic currency bn",
        "category": "gfs",
    },
    "GFS_INTEREST_EXPENSE": {
        "database": "GFSMAB",
        "series_key": "A.{country}.S13.XDC.G24__Z",
        "name": "Interest Expense",
        "description": "General government interest expense in domestic currency (billions)",
        "frequency": "annual",
        "unit": "domestic currency bn",
        "category": "gfs",
    },
    "GFS_NET_INVESTMENT": {
        "database": "GFSMAB",
        "series_key": "A.{country}.S13.XDC.G31_NG",
        "name": "Net Investment in Nonfinancial Assets",
        "description": "General government investment in nonfinancial assets in domestic currency (billions)",
        "frequency": "annual",
        "unit": "domestic currency bn",
        "category": "gfs",
    },
    "GFS_NET_LIABILITIES": {
        "database": "GFSMAB",
        "series_key": "A.{country}.S13.XDC.G33_F",
        "name": "Net Incurrence of Liabilities",
        "description": "General government net incurrence of liabilities (new borrowing) in domestic currency (billions)",
        "frequency": "annual",
        "unit": "domestic currency bn",
        "category": "gfs",
    },
}

DEFAULT_COUNTRY = "US"


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


def _fetch_dbnomics(database: str, series_code: str) -> Dict:
    """Fetch a single series from DBnomics IMF mirror."""
    url = f"{DBNOMICS_BASE}/series/IMF/{database}/{series_code}"
    params = {"observations": "1"}
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        docs = data.get("series", {}).get("docs", [])
        if not docs:
            return {"success": False, "error": "No series found"}
        series = docs[0]
        periods = series.get("period", [])
        values = series.get("value", [])
        observations = []
        for p, v in zip(periods, values):
            if v is not None and v != "NA" and v != "":
                try:
                    observations.append({"period": str(p), "value": float(v)})
                except (ValueError, TypeError):
                    continue
        if not observations:
            return {"success": False, "error": "No valid observations"}
        observations.sort(key=lambda x: x["period"], reverse=True)
        return {"success": True, "observations": observations, "series_name": series.get("series_name", "")}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_data(indicator: str, country: str = DEFAULT_COUNTRY) -> Dict:
    """Fetch a specific indicator for a given country (ISO2 code)."""
    indicator = indicator.upper()
    country = country.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_key = {"indicator": indicator, "country": country}
    cp = _cache_path(f"{indicator}_{country}", _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    series_code = cfg["series_key"].format(country=country)
    result = _fetch_dbnomics(cfg["database"], series_code)

    if not result["success"]:
        return {
            "success": False,
            "indicator": indicator,
            "country": country,
            "name": cfg["name"],
            "error": result["error"],
        }

    observations = result["observations"]
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
        "country": country,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "database": cfg["database"],
        "category": cfg["category"],
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": observations[:30],
        "total_observations": len(observations),
        "source": f"IMF {cfg['database']} via DBnomics",
        "series_key": series_code,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_available_indicators() -> List[Dict]:
    """Return all available indicators with descriptions."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "database": v["database"],
            "category": v["category"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None, country: str = DEFAULT_COUNTRY) -> Dict:
    """Get latest values for one or all indicators."""
    if indicator:
        return fetch_data(indicator, country)

    results = {}
    errors = []
    for key in INDICATORS:
        data = fetch_data(key, country)
        if data.get("success"):
            results[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
                "category": data["category"],
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "IMF Enhanced (FAS + FSI + CPIS + CDIS + GFS) via DBnomics",
        "country": country,
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_by_category(category: str, country: str = DEFAULT_COUNTRY) -> Dict:
    """Get all indicators for a specific category (fas/fsi/cpis/cdis/gfs)."""
    category = category.lower()
    valid = {"fas", "fsi", "cpis", "cdis", "gfs"}
    if category not in valid:
        return {"success": False, "error": f"Unknown category: {category}", "valid": list(valid)}

    results = {}
    errors = []
    for key, cfg in INDICATORS.items():
        if cfg["category"] != category:
            continue
        data = fetch_data(key, country)
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

    category_names = {
        "fas": "Financial Access Survey",
        "fsi": "Financial Soundness Indicators",
        "cpis": "Coordinated Portfolio Investment Survey",
        "cdis": "Coordinated Direct Investment Survey",
        "gfs": "Government Finance Statistics",
    }

    return {
        "success": True,
        "source": f"IMF {category_names[category]}",
        "country": country,
        "category": category,
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_banking_health(country: str = DEFAULT_COUNTRY) -> Dict:
    """Convenience: get FSI banking health snapshot."""
    return get_by_category("fsi", country)


def get_financial_access(country: str = DEFAULT_COUNTRY) -> Dict:
    """Convenience: get FAS financial inclusion snapshot."""
    return get_by_category("fas", country)


# --- CLI ---

def _print_help():
    print("""
IMF Enhanced Module (FAS + FSI + CPIS + CDIS + GFS)

Usage:
  python imf_enhanced.py                            # Latest values for all (US default)
  python imf_enhanced.py <INDICATOR> [COUNTRY]      # Fetch specific indicator
  python imf_enhanced.py list                       # List available indicators
  python imf_enhanced.py fas [COUNTRY]              # Financial Access Survey
  python imf_enhanced.py fsi [COUNTRY]              # Financial Soundness Indicators
  python imf_enhanced.py cpis [COUNTRY]             # Portfolio Investment Survey
  python imf_enhanced.py cdis [COUNTRY]             # Direct Investment Survey
  python imf_enhanced.py gfs [COUNTRY]              # Government Finance Statistics
  python imf_enhanced.py banking-health [COUNTRY]   # FSI banking health snapshot
  python imf_enhanced.py access [COUNTRY]           # FAS financial inclusion snapshot

Countries: ISO2 codes (US, GB, DE, JP, CN, FR, IN, BR, etc.)

Indicators:""")
    by_cat = {}
    for key, cfg in INDICATORS.items():
        by_cat.setdefault(cfg["category"].upper(), []).append((key, cfg["name"]))
    for cat in ["FAS", "FSI", "CPIS", "CDIS", "GFS"]:
        print(f"\n  [{cat}]")
        for key, name in by_cat.get(cat, []):
            print(f"    {key:<35s} {name}")
    print(f"""
Source: IMF databases via DBnomics ({DBNOMICS_BASE})
Coverage: 190+ countries, annual data
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
    elif args[0] in ("fas", "fsi", "cpis", "cdis", "gfs"):
        country = args[1] if len(args) > 1 else DEFAULT_COUNTRY
        print(json.dumps(get_by_category(args[0], country), indent=2, default=str))
    elif args[0] == "banking-health":
        country = args[1] if len(args) > 1 else DEFAULT_COUNTRY
        print(json.dumps(get_banking_health(country), indent=2, default=str))
    elif args[0] == "access":
        country = args[1] if len(args) > 1 else DEFAULT_COUNTRY
        print(json.dumps(get_financial_access(country), indent=2, default=str))
    else:
        country = args[1] if len(args) > 1 else DEFAULT_COUNTRY
        result = fetch_data(args[0], country)
        print(json.dumps(result, indent=2, default=str))

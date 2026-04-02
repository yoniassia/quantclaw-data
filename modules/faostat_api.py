#!/usr/bin/env python3
"""
UN FAO FAOSTAT Data API — Comprehensive food & agriculture statistics

Covers 245+ countries, 20,000+ indicators: crop production, trade, prices,
fertilizers, land use, emissions, food security. Annual data 1961–present.

Data Source: https://faostatservices.fao.org/api/v1
Protocol: REST with JWT Bearer token authentication
Auth: FAOSTAT_USERNAME + FAOSTAT_PASSWORD env vars (free registration)
      Register at: https://www.fao.org/faostat/en/#developer-portal
Refresh: Quarterly (annual data)
Coverage: 245 countries and territories, 1961–present

Author: QUANTCLAW DATA Build Agent
"""

import json
import sys
import os
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

BASE_URL = "https://faostatservices.fao.org/api/v1"
AUTH_URL = f"{BASE_URL}/auth/login"
LANG = "en"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "faostat_api"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 120
REQUEST_DELAY = 1.0

_token: Optional[str] = None
_token_obtained: Optional[datetime] = None
TOKEN_LIFETIME_MIN = 55


COUNTRY_CODES = {
    "US": "231", "USA": "231", "UNITED STATES": "231",
    "CN": "351", "CHN": "351", "CHINA": "351",
    "IN": "100", "IND": "100", "INDIA": "100",
    "BR": "21", "BRA": "21", "BRAZIL": "21",
    "RU": "185", "RUS": "185", "RUSSIA": "185",
    "AR": "9", "ARG": "9", "ARGENTINA": "9",
    "AU": "10", "AUS": "10", "AUSTRALIA": "10",
    "CA": "33", "CAN": "33", "CANADA": "33",
    "FR": "68", "FRA": "68", "FRANCE": "68",
    "DE": "79", "DEU": "79", "GERMANY": "79",
    "ID": "101", "IDN": "101", "INDONESIA": "101",
    "JP": "110", "JPN": "110", "JAPAN": "110",
    "MX": "138", "MEX": "138", "MEXICO": "138",
    "NG": "159", "NGA": "159", "NIGERIA": "159",
    "PK": "165", "PAK": "165", "PAKISTAN": "165",
    "TH": "216", "THA": "216", "THAILAND": "216",
    "TR": "223", "TUR": "223", "TURKEY": "223",
    "UA": "230", "UKR": "230", "UKRAINE": "230",
    "GB": "229", "GBR": "229", "UNITED KINGDOM": "229",
    "ZA": "202", "ZAF": "202", "SOUTH AFRICA": "202",
    "EG": "59", "EGY": "59", "EGYPT": "59",
    "ET": "238", "ETH": "238", "ETHIOPIA": "238",
    "VN": "237", "VNM": "237", "VIETNAM": "237",
    "PH": "171", "PHL": "171", "PHILIPPINES": "171",
    "MY": "131", "MYS": "131", "MALAYSIA": "131",
    "CO": "44", "COL": "44", "COLOMBIA": "44",
    "PE": "170", "PER": "170", "PERU": "170",
    "KE": "114", "KEN": "114", "KENYA": "114",
    "PL": "173", "POL": "173", "POLAND": "173",
    "IT": "106", "ITA": "106", "ITALY": "106",
    "ES": "203", "ESP": "203", "SPAIN": "203",
    "NL": "150", "NLD": "150", "NETHERLANDS": "150",
    "BD": "16", "BGD": "16", "BANGLADESH": "16",
    "MM": "28", "MMR": "28", "MYANMAR": "28",
    "KR": "117", "KOR": "117", "SOUTH KOREA": "117",
    "NZ": "156", "NZL": "156", "NEW ZEALAND": "156",
    "CL": "40", "CHL": "40", "CHILE": "40",
    "WORLD": "5000",
}

FAO_TO_ISO3 = {
    "231": "USA", "351": "CHN", "100": "IND", "21": "BRA", "185": "RUS",
    "9": "ARG", "10": "AUS", "33": "CAN", "68": "FRA", "79": "DEU",
    "101": "IDN", "110": "JPN", "138": "MEX", "159": "NGA", "165": "PAK",
    "216": "THA", "223": "TUR", "230": "UKR", "229": "GBR", "202": "ZAF",
    "59": "EGY", "238": "ETH", "237": "VNM", "171": "PHL", "131": "MYS",
    "44": "COL", "170": "PER", "114": "KEN", "173": "POL", "106": "ITA",
    "203": "ESP", "150": "NLD", "16": "BGD", "28": "MMR", "117": "KOR",
    "156": "NZL", "40": "CHL", "5000": "WORLD",
}

COMMODITY_CODES = {
    "WHEAT": "15", "RICE": "27", "MAIZE": "56", "CORN": "56",
    "SOYBEANS": "236", "SOYBEAN": "236", "SOYA": "236",
    "SUGARCANE": "156", "SUGAR CANE": "156",
    "OIL PALM": "254", "PALM OIL": "254", "OIL PALM FRUIT": "254",
    "BARLEY": "44", "SORGHUM": "83",
    "POTATOES": "116", "POTATO": "116",
    "CASSAVA": "125",
    "COTTON": "328", "SEED COTTON": "328",
    "COFFEE": "656", "COCOA": "661", "TEA": "667", "TOBACCO": "826",
    "CATTLE": "866", "CHICKENS": "1057", "POULTRY": "1057",
    "PIGS": "1034", "SWINE": "1034", "SHEEP": "976", "GOATS": "1016",
    "MILK": "882", "COW MILK": "882",
}

INDICATORS = {
    # --- Crop Production (QCL) ---
    "WHEAT_PRODUCTION": {
        "domain": "QCL", "item": "15", "element": "5510",
        "name": "Wheat Production (tonnes)",
        "description": "Annual wheat production quantity by country",
        "frequency": "annual", "unit": "tonnes",
    },
    "RICE_PRODUCTION": {
        "domain": "QCL", "item": "27", "element": "5510",
        "name": "Rice Paddy Production (tonnes)",
        "description": "Annual rice paddy production quantity by country",
        "frequency": "annual", "unit": "tonnes",
    },
    "MAIZE_PRODUCTION": {
        "domain": "QCL", "item": "56", "element": "5510",
        "name": "Maize (Corn) Production (tonnes)",
        "description": "Annual maize production quantity by country",
        "frequency": "annual", "unit": "tonnes",
    },
    "SOYBEANS_PRODUCTION": {
        "domain": "QCL", "item": "236", "element": "5510",
        "name": "Soybeans Production (tonnes)",
        "description": "Annual soybeans production quantity by country",
        "frequency": "annual", "unit": "tonnes",
    },
    "SUGARCANE_PRODUCTION": {
        "domain": "QCL", "item": "156", "element": "5510",
        "name": "Sugar Cane Production (tonnes)",
        "description": "Annual sugar cane production quantity by country",
        "frequency": "annual", "unit": "tonnes",
    },
    "PALM_OIL_PRODUCTION": {
        "domain": "QCL", "item": "254", "element": "5510",
        "name": "Oil Palm Fruit Production (tonnes)",
        "description": "Annual oil palm fruit production quantity by country",
        "frequency": "annual", "unit": "tonnes",
    },
    # --- Crop Yields (QCL) ---
    "WHEAT_YIELD": {
        "domain": "QCL", "item": "15", "element": "5419",
        "name": "Wheat Yield (hg/ha)",
        "description": "Annual wheat yield per hectare",
        "frequency": "annual", "unit": "hg/ha",
    },
    "RICE_YIELD": {
        "domain": "QCL", "item": "27", "element": "5419",
        "name": "Rice Yield (hg/ha)",
        "description": "Annual rice paddy yield per hectare",
        "frequency": "annual", "unit": "hg/ha",
    },
    "MAIZE_YIELD": {
        "domain": "QCL", "item": "56", "element": "5419",
        "name": "Maize Yield (hg/ha)",
        "description": "Annual maize yield per hectare",
        "frequency": "annual", "unit": "hg/ha",
    },
    # --- Area Harvested (QCL) ---
    "WHEAT_AREA": {
        "domain": "QCL", "item": "15", "element": "5312",
        "name": "Wheat Area Harvested (ha)",
        "description": "Annual wheat area harvested",
        "frequency": "annual", "unit": "ha",
    },
    # --- Livestock Inventory (QCL) ---
    "CATTLE_STOCKS": {
        "domain": "QCL", "item": "866", "element": "5111",
        "name": "Cattle Stocks (head)",
        "description": "Live cattle inventory by country",
        "frequency": "annual", "unit": "head",
    },
    "CHICKEN_STOCKS": {
        "domain": "QCL", "item": "1057", "element": "5111",
        "name": "Chicken Stocks (1000 head)",
        "description": "Live chicken inventory by country",
        "frequency": "annual", "unit": "1000 head",
    },
    "PIG_STOCKS": {
        "domain": "QCL", "item": "1034", "element": "5111",
        "name": "Pig Stocks (head)",
        "description": "Live pig inventory by country",
        "frequency": "annual", "unit": "head",
    },
    # --- Trade (TP) ---
    "WHEAT_EXPORT_QTY": {
        "domain": "TP", "item": "15", "element": "5910",
        "name": "Wheat Export Quantity (tonnes)",
        "description": "Annual wheat export quantity by country",
        "frequency": "annual", "unit": "tonnes",
    },
    "WHEAT_IMPORT_QTY": {
        "domain": "TP", "item": "15", "element": "5607",
        "name": "Wheat Import Quantity (tonnes)",
        "description": "Annual wheat import quantity by country",
        "frequency": "annual", "unit": "tonnes",
    },
    "SOYBEANS_EXPORT_QTY": {
        "domain": "TP", "item": "236", "element": "5910",
        "name": "Soybeans Export Quantity (tonnes)",
        "description": "Annual soybeans export quantity by country",
        "frequency": "annual", "unit": "tonnes",
    },
    "RICE_EXPORT_QTY": {
        "domain": "TP", "item": "27", "element": "5910",
        "name": "Rice Export Quantity (tonnes)",
        "description": "Annual rice export quantity by country",
        "frequency": "annual", "unit": "tonnes",
    },
    "MAIZE_EXPORT_QTY": {
        "domain": "TP", "item": "56", "element": "5910",
        "name": "Maize Export Quantity (tonnes)",
        "description": "Annual maize export quantity by country",
        "frequency": "annual", "unit": "tonnes",
    },
    "WHEAT_EXPORT_VAL": {
        "domain": "TP", "item": "15", "element": "5922",
        "name": "Wheat Export Value (1000 USD)",
        "description": "Annual wheat export value by country",
        "frequency": "annual", "unit": "1000 USD",
    },
    "WHEAT_IMPORT_VAL": {
        "domain": "TP", "item": "15", "element": "5608",
        "name": "Wheat Import Value (1000 USD)",
        "description": "Annual wheat import value by country",
        "frequency": "annual", "unit": "1000 USD",
    },
    # --- Producer Prices (PP) ---
    "WHEAT_PRICE_USD": {
        "domain": "PP", "item": "15", "element": "5532",
        "name": "Wheat Producer Price (USD/tonne)",
        "description": "Annual farm-gate wheat price in USD per tonne",
        "frequency": "annual", "unit": "USD/tonne",
    },
    "MAIZE_PRICE_USD": {
        "domain": "PP", "item": "56", "element": "5532",
        "name": "Maize Producer Price (USD/tonne)",
        "description": "Annual farm-gate maize price in USD per tonne",
        "frequency": "annual", "unit": "USD/tonne",
    },
    "RICE_PRICE_USD": {
        "domain": "PP", "item": "27", "element": "5532",
        "name": "Rice Producer Price (USD/tonne)",
        "description": "Annual farm-gate rice price in USD per tonne",
        "frequency": "annual", "unit": "USD/tonne",
    },
    "SOYBEANS_PRICE_USD": {
        "domain": "PP", "item": "236", "element": "5532",
        "name": "Soybeans Producer Price (USD/tonne)",
        "description": "Annual farm-gate soybeans price in USD per tonne",
        "frequency": "annual", "unit": "USD/tonne",
    },
    # --- Fertilizers by Nutrient (RFN) ---
    "NITROGEN_FERTILIZER": {
        "domain": "RFN", "item": "3102", "element": "5157",
        "name": "Nitrogen (N) Fertilizer Use (tonnes nutrient)",
        "description": "Annual nitrogen fertilizer consumption for agriculture",
        "frequency": "annual", "unit": "tonnes",
    },
    "PHOSPHATE_FERTILIZER": {
        "domain": "RFN", "item": "3103", "element": "5157",
        "name": "Phosphate (P2O5) Fertilizer Use (tonnes nutrient)",
        "description": "Annual phosphate fertilizer consumption for agriculture",
        "frequency": "annual", "unit": "tonnes",
    },
    "POTASH_FERTILIZER": {
        "domain": "RFN", "item": "3104", "element": "5157",
        "name": "Potash (K2O) Fertilizer Use (tonnes nutrient)",
        "description": "Annual potash fertilizer consumption for agriculture",
        "frequency": "annual", "unit": "tonnes",
    },
    # --- Land Use (RL) ---
    "ARABLE_LAND": {
        "domain": "RL", "item": "6621", "element": "5110",
        "name": "Arable Land (1000 ha)",
        "description": "Land under temporary crops, temporary meadows, gardens",
        "frequency": "annual", "unit": "1000 ha",
    },
    "AGRICULTURAL_LAND": {
        "domain": "RL", "item": "6610", "element": "5110",
        "name": "Agricultural Land (1000 ha)",
        "description": "Total area: arable + permanent crops + permanent meadows",
        "frequency": "annual", "unit": "1000 ha",
    },
    "FOREST_LAND": {
        "domain": "RL", "item": "6646", "element": "5110",
        "name": "Forest Land (1000 ha)",
        "description": "Land with trees >5m and canopy cover >10%, area >0.5 ha",
        "frequency": "annual", "unit": "1000 ha",
    },
    # --- Food Security (FS) ---
    "UNDERNOURISHMENT": {
        "domain": "FS", "item": "21010", "element": "6120",
        "name": "Prevalence of Undernourishment (%)",
        "description": "Pct of population with insufficient dietary energy",
        "frequency": "annual", "unit": "%",
    },
    "DIETARY_SUPPLY_ADEQUACY": {
        "domain": "FS", "item": "21001", "element": "6120",
        "name": "Average Dietary Energy Supply Adequacy (%)",
        "description": "Dietary energy supply as pct of requirement",
        "frequency": "annual", "unit": "%",
    },
    # --- Emissions (GT) ---
    "AG_EMISSIONS_TOTAL": {
        "domain": "GT", "item": "1711", "element": "7231",
        "name": "Agriculture Total Emissions (kt CO2eq)",
        "description": "Total GHG emissions from agriculture, CO2 equivalent",
        "frequency": "annual", "unit": "kilotonnes",
    },
}

DOMAIN_COMMANDS = {
    "production": {
        "domain": "QCL", "default_element": "5510",
        "description": "Crop & livestock production",
    },
    "trade": {
        "domain": "TP", "default_element": "5910",
        "description": "Import/export quantity and value",
    },
    "prices": {
        "domain": "PP", "default_element": "5532",
        "description": "Producer prices (farm-gate, USD/tonne)",
    },
    "fertilizer": {
        "domain": "RFN", "default_element": "5157",
        "description": "Fertilizer use by nutrient type",
    },
    "land_use": {
        "domain": "RL", "default_element": "5110",
        "description": "Land use area by category",
    },
    "food_security": {
        "domain": "FS", "default_element": "6120",
        "description": "Food security and nutrition indicators",
    },
    "emissions": {
        "domain": "GT", "default_element": "7231",
        "description": "Agricultural greenhouse gas emissions",
    },
}


# ── Authentication ──────────────────────────────────────────────────────────

def _get_token() -> Optional[str]:
    global _token, _token_obtained
    if _token and _token_obtained:
        elapsed = (datetime.now() - _token_obtained).total_seconds() / 60
        if elapsed < TOKEN_LIFETIME_MIN:
            return _token

    env_token = os.environ.get("FAOSTAT_TOKEN")
    if env_token:
        _token = env_token
        _token_obtained = datetime.now()
        return _token

    username = os.environ.get("FAOSTAT_USERNAME")
    password = os.environ.get("FAOSTAT_PASSWORD")
    if not username or not password:
        return None

    try:
        resp = requests.post(AUTH_URL, data={"username": username, "password": password},
                             timeout=30)
        resp.raise_for_status()
        result = resp.json()
        _token = result["AuthenticationResult"]["AccessToken"]
        _token_obtained = datetime.now()
        return _token
    except Exception:
        return None


def _auth_headers() -> Dict[str, str]:
    token = _get_token()
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _has_auth() -> bool:
    return bool(os.environ.get("FAOSTAT_TOKEN") or
                (os.environ.get("FAOSTAT_USERNAME") and os.environ.get("FAOSTAT_PASSWORD")))


# ── Caching ─────────────────────────────────────────────────────────────────

def _cache_path(key: str, params_hash: str) -> Path:
    safe = key.replace("/", "_").replace(" ", "_")
    return CACHE_DIR / f"{safe}_{params_hash}.json"


def _params_hash(params: Any) -> str:
    raw = json.dumps(params, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


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
        payload = data.copy()
        payload["_cached_at"] = datetime.now().isoformat()
        path.write_text(json.dumps(payload, default=str))
    except OSError:
        pass


# ── API Requests ────────────────────────────────────────────────────────────

def _api_get(endpoint: str, params: Optional[Dict] = None) -> Dict:
    url = f"{BASE_URL}/{LANG}/{endpoint}"
    try:
        resp = requests.get(url, params=params, headers=_auth_headers(),
                            timeout=REQUEST_TIMEOUT)
        if resp.status_code == 401:
            return {"success": False, "error": "Authentication required. Set FAOSTAT_USERNAME + FAOSTAT_PASSWORD env vars (register free at https://www.fao.org/faostat/en/#developer-portal)"}
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out (FAOSTAT can be slow for large queries)"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed — FAOSTAT API may be temporarily unavailable"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        body = ""
        try:
            body = e.response.text[:200]
        except Exception:
            pass
        return {"success": False, "error": f"HTTP {status}: {body}"}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


def _resolve_country(country_str: Optional[str]) -> Optional[str]:
    """Resolve country name/ISO2/ISO3 to FAO area code."""
    if not country_str:
        return None
    key = country_str.upper().strip()
    if key in COUNTRY_CODES:
        return COUNTRY_CODES[key]
    if key.isdigit():
        return key
    return None


def _resolve_commodity(commodity_str: Optional[str]) -> Optional[str]:
    """Resolve commodity name to FAOSTAT item code."""
    if not commodity_str:
        return None
    key = commodity_str.upper().strip()
    if key in COMMODITY_CODES:
        return COMMODITY_CODES[key]
    if key.isdigit():
        return key
    return None


# ── Data Parsing ────────────────────────────────────────────────────────────

def _parse_data_response(raw: Dict) -> List[Dict]:
    """Parse FAOSTAT API data response into clean records."""
    try:
        api_data = raw.get("data", [])
        if not api_data:
            return []

        metadata = raw.get("metadata", {})
        dsd = metadata.get("dsd", [])
        field_labels = [d.get("id", d.get("label", f"col_{i}")) for i, d in enumerate(dsd)] if dsd else []

        records = []
        for row in api_data:
            if isinstance(row, dict):
                record = _normalize_row(row)
                if record.get("Value") is not None:
                    records.append(record)
            elif isinstance(row, (list, tuple)) and field_labels:
                record = dict(zip(field_labels, row))
                record = _normalize_row(record)
                if record.get("Value") is not None:
                    records.append(record)

        records.sort(key=lambda x: str(x.get("Year", "")), reverse=True)
        return records
    except (KeyError, TypeError, ValueError):
        return []


def _normalize_row(row: Dict) -> Dict:
    """Normalize a FAOSTAT data row to consistent field names."""
    value_raw = row.get("Value", row.get("value"))
    value = None
    if value_raw is not None and str(value_raw).strip() not in ("", "None", "null"):
        try:
            value = float(str(value_raw).replace(",", ""))
        except (ValueError, TypeError):
            value = None

    area_code = str(row.get("Area Code", row.get("Area Code (FAO)", row.get("area_code", ""))))
    iso3 = FAO_TO_ISO3.get(area_code)

    return {
        "domain_code": row.get("Domain Code", row.get("domain_code", "")),
        "domain": row.get("Domain", row.get("domain", "")),
        "area_code": area_code,
        "area": row.get("Area", row.get("area", "")),
        "iso3": iso3,
        "element_code": str(row.get("Element Code", row.get("element_code", ""))),
        "element": row.get("Element", row.get("element", "")),
        "item_code": str(row.get("Item Code", row.get("item_code", ""))),
        "item": row.get("Item", row.get("item", "")),
        "year": str(row.get("Year", row.get("year", ""))),
        "unit": row.get("Unit", row.get("unit", "")),
        "Value": value,
    }


# ── Core Data Functions ─────────────────────────────────────────────────────

def fetch_data(indicator: str, country: str = None, start_year: str = None,
               end_year: str = None) -> Dict:
    """Fetch a pre-defined indicator with optional country/year filters."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}",
                "available": sorted(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    area = _resolve_country(country) if country else None

    cache_key = {"indicator": indicator, "area": area,
                 "start": start_year, "end": end_year}
    cp = _cache_path(indicator, _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {
        "element": cfg["element"],
        "item": cfg["item"],
        "show_codes": "true",
        "show_unit": "true",
        "null_values": "false",
        "output_type": "objects",
    }
    if area:
        params["area"] = area
    if start_year and end_year:
        params["year"] = [str(y) for y in range(int(start_year), int(end_year) + 1)]
    elif start_year:
        params["year"] = start_year
    elif end_year:
        params["year"] = end_year

    result = _api_get(f"data/{cfg['domain']}", params=params)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": result["error"]}

    records = _parse_data_response(result["data"])
    if not records:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": "No data returned for this query"}

    latest = records[0]
    yoy_change = yoy_pct = None
    if len(records) >= 2:
        prev = records[1]
        if latest["Value"] is not None and prev["Value"] and prev["Value"] != 0:
            yoy_change = round(latest["Value"] - prev["Value"], 2)
            yoy_pct = round((yoy_change / abs(prev["Value"])) * 100, 2)

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "domain": cfg["domain"],
        "latest_value": latest["Value"],
        "latest_year": latest["year"],
        "latest_area": latest["area"],
        "yoy_change": yoy_change,
        "yoy_change_pct": yoy_pct,
        "data_points": [
            {"year": r["year"], "area": r["area"], "area_code": r["area_code"],
             "iso3": r["iso3"], "value": r["Value"], "unit": r["unit"]}
            for r in records[:50]
        ],
        "total_records": len(records),
        "source": f"{BASE_URL}/{LANG}/data/{cfg['domain']}",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def query_domain(domain: str, item: str = None, element: str = None,
                 country: str = None, year: str = None) -> Dict:
    """Dynamic query against any FAOSTAT domain."""
    cache_key = {"domain": domain, "item": item, "element": element,
                 "country": country, "year": year}
    cp = _cache_path(f"query_{domain}", _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {
        "show_codes": "true",
        "show_unit": "true",
        "null_values": "false",
        "output_type": "objects",
    }
    if item:
        resolved_item = _resolve_commodity(item)
        params["item"] = resolved_item if resolved_item else item
    if element:
        params["element"] = element
    if country:
        area = _resolve_country(country)
        if area:
            params["area"] = area
        else:
            params["area"] = country
    if year:
        params["year"] = year

    result = _api_get(f"data/{domain}", params=params)
    if not result["success"]:
        return {"success": False, "domain": domain, "error": result["error"]}

    records = _parse_data_response(result["data"])
    if not records:
        return {"success": False, "domain": domain,
                "error": "No data returned for this query"}

    response = {
        "success": True,
        "domain": domain,
        "query": {"item": item, "element": element, "country": country, "year": year},
        "data_points": [
            {"year": r["year"], "area": r["area"], "area_code": r["area_code"],
             "iso3": r["iso3"], "item": r["item"], "element": r["element"],
             "value": r["Value"], "unit": r["unit"]}
            for r in records[:100]
        ],
        "total_records": len(records),
        "source": f"{BASE_URL}/{LANG}/data/{domain}",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_top_producers(commodity: str, element: str = "5510", year: str = None,
                      top_n: int = 10) -> Dict:
    """Get top-N producing countries for a commodity."""
    item_code = _resolve_commodity(commodity)
    if not item_code:
        return {"success": False, "error": f"Unknown commodity: {commodity}",
                "available": sorted(set(COMMODITY_CODES.keys()))}

    params = {
        "element": element,
        "item": item_code,
        "show_codes": "true",
        "show_unit": "true",
        "null_values": "false",
        "output_type": "objects",
    }
    if year:
        params["year"] = year

    cache_key = {"top": commodity, "element": element, "year": year, "n": top_n}
    cp = _cache_path(f"top_{commodity}", _params_hash(cache_key))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get("data/QCL", params=params)
    if not result["success"]:
        return {"success": False, "error": result["error"]}

    records = _parse_data_response(result["data"])
    if not records:
        return {"success": False, "error": "No data returned"}

    latest_year = max(r["year"] for r in records if r["Value"] is not None)
    latest = [r for r in records if r["year"] == latest_year and r["Value"] is not None]

    aggregates = {"5000", "5100", "5200", "5300", "5400", "5500",
                  "5707", "5801", "5815", "5817"}
    country_data = [r for r in latest if r["area_code"] not in aggregates]
    country_data.sort(key=lambda x: x["Value"], reverse=True)
    top = country_data[:top_n]

    response = {
        "success": True,
        "commodity": commodity,
        "item_code": item_code,
        "year": latest_year,
        "ranking": [
            {"rank": i + 1, "area": r["area"], "area_code": r["area_code"],
             "iso3": r["iso3"], "value": r["Value"], "unit": r["unit"]}
            for i, r in enumerate(top)
        ],
        "total_countries": len(country_data),
        "source": "FAOSTAT QCL",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


# ── Discovery Functions ─────────────────────────────────────────────────────

def list_domains() -> Dict:
    """List all available FAOSTAT domains/datasets."""
    cp = _cache_path("domains", "all")
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get("groups")
    if not result["success"]:
        return {"success": False, "error": result["error"],
                "fallback": _static_domain_list()}

    groups = result["data"].get("data", [])
    domains = []
    for group in groups:
        group_code = group.get("code", "")
        group_label = group.get("label", "")
        sub_result = _api_get(f"domains/{group_code}")
        if sub_result["success"]:
            for d in sub_result["data"].get("data", []):
                if d.get("date_update"):
                    domains.append({
                        "code": d.get("code"),
                        "label": d.get("label"),
                        "group": group_label,
                        "updated": d.get("date_update"),
                    })
        time.sleep(REQUEST_DELAY)

    response = {
        "success": True,
        "domains": domains,
        "count": len(domains),
        "source": "FAOSTAT API",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def list_domain_items(domain: str) -> Dict:
    """List available items for a domain."""
    cp = _cache_path(f"items_{domain}", "all")
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get(f"codes/items/{domain}")
    if not result["success"]:
        return {"success": False, "domain": domain, "error": result["error"]}

    items = [{"code": i["code"], "label": i["label"]}
             for i in result["data"].get("data", [])]

    response = {
        "success": True,
        "domain": domain,
        "items": items,
        "count": len(items),
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def list_domain_elements(domain: str) -> Dict:
    """List available elements for a domain."""
    cp = _cache_path(f"elements_{domain}", "all")
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get(f"codes/elements/{domain}")
    if not result["success"]:
        return {"success": False, "domain": domain, "error": result["error"]}

    elements = [{"code": e["code"], "label": e["label"]}
                for e in result["data"].get("data", [])]

    response = {
        "success": True,
        "domain": domain,
        "elements": elements,
        "count": len(elements),
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def list_domain_areas(domain: str) -> Dict:
    """List available countries/areas for a domain."""
    cp = _cache_path(f"areas_{domain}", "all")
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get(f"codes/countries/{domain}")
    if not result["success"]:
        return {"success": False, "domain": domain, "error": result["error"]}

    areas = [{"code": a["code"], "label": a["label"],
              "iso3": FAO_TO_ISO3.get(a["code"])}
             for a in result["data"].get("data", [])]

    response = {
        "success": True,
        "domain": domain,
        "areas": areas,
        "count": len(areas),
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


# ── Standard Module Interface ───────────────────────────────────────────────

def get_available_indicators() -> List[Dict]:
    """Return list of available pre-defined indicators."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "domain": v["domain"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest value(s) for one or all indicators."""
    if indicator:
        return fetch_data(indicator)

    summary = {
        "success": True,
        "source": "FAOSTAT — UN Food and Agriculture Organization",
        "api_url": BASE_URL,
        "auth_required": True,
        "auth_configured": _has_auth(),
        "indicator_count": len(INDICATORS),
        "domains_covered": sorted(set(v["domain"] for v in INDICATORS.values())),
        "domain_descriptions": {k: v["description"] for k, v in DOMAIN_COMMANDS.items()},
        "commodities_mapped": len(set(COMMODITY_CODES.values())),
        "countries_mapped": len(FAO_TO_ISO3),
        "cache_ttl_hours": CACHE_TTL_HOURS,
        "timestamp": datetime.now().isoformat(),
    }

    if not _has_auth():
        summary["auth_help"] = (
            "Set FAOSTAT_USERNAME and FAOSTAT_PASSWORD environment variables. "
            "Register free at https://www.fao.org/faostat/en/#developer-portal"
        )

    return summary


def _static_domain_list() -> List[Dict]:
    """Static fallback list of key FAOSTAT domains."""
    return [
        {"code": "QCL", "label": "Crops and livestock products", "group": "Production"},
        {"code": "QI", "label": "Production Indices", "group": "Production"},
        {"code": "QV", "label": "Value of Agricultural Production", "group": "Production"},
        {"code": "TP", "label": "Trade: Crops and livestock products", "group": "Trade"},
        {"code": "TI", "label": "Trade Indices", "group": "Trade"},
        {"code": "PP", "label": "Producer Prices", "group": "Prices"},
        {"code": "CP", "label": "Consumer Price Indices", "group": "Prices"},
        {"code": "PI", "label": "Deflators", "group": "Prices"},
        {"code": "FBS", "label": "Food Balances (2010-)", "group": "Food Balance"},
        {"code": "SCL", "label": "Supply Utilization Accounts", "group": "Food Balance"},
        {"code": "FS", "label": "Suite of Food Security Indicators", "group": "Food Security"},
        {"code": "RL", "label": "Land Use", "group": "Inputs"},
        {"code": "RFN", "label": "Fertilizers by Nutrient", "group": "Inputs"},
        {"code": "RP", "label": "Pesticides Use", "group": "Inputs"},
        {"code": "IC", "label": "Credit to Agriculture", "group": "Investment"},
        {"code": "GT", "label": "Emissions Totals", "group": "Agri-Environmental"},
        {"code": "GN", "label": "Emissions from Crop Residues", "group": "Agri-Environmental"},
        {"code": "GR", "label": "Emissions from Agriculture: Rice", "group": "Agri-Environmental"},
        {"code": "OA", "label": "Annual Population", "group": "Population"},
        {"code": "EI", "label": "Exchange Rates", "group": "Macro"},
    ]


# ── CLI ─────────────────────────────────────────────────────────────────────

def _print_help():
    print("""
UN FAO FAOSTAT Data API Module

Usage:
  python faostat_api.py                                Summary / status
  python faostat_api.py list                           List all indicators
  python faostat_api.py domains                        List FAOSTAT domains
  python faostat_api.py <INDICATOR> [COUNTRY]          Fetch pre-defined indicator
  python faostat_api.py production <commodity> [CC]    Crop/livestock production
  python faostat_api.py trade <commodity> [CC]         Trade (export quantities)
  python faostat_api.py prices <commodity> [CC]        Producer prices (USD/tonne)
  python faostat_api.py fertilizer <type> [CC]         Fertilizer use (N/P/K)
  python faostat_api.py land_use [CC]                  Land use data
  python faostat_api.py food_security [CC]             Food security indicators
  python faostat_api.py emissions [CC]                 Agricultural emissions
  python faostat_api.py top <commodity> [N]            Top-N producers

  CC = Country code (ISO2/ISO3/name), e.g. US, BRA, "CHINA"

Auth:
  Set FAOSTAT_USERNAME and FAOSTAT_PASSWORD env vars.
  Register free: https://www.fao.org/faostat/en/#developer-portal

Domains: QCL (production), TP (trade), PP (prices), RFN (fertilizer),
         RL (land use), FS (food security), GT (emissions), FBS (food balance)

Commodities: wheat, rice, maize/corn, soybeans, sugarcane, palm oil, barley,
             sorghum, potatoes, cassava, cotton, coffee, cocoa, tea, tobacco,
             cattle, chickens/poultry, pigs/swine, sheep, goats, milk
""")
    print("Pre-defined Indicators:")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print()


def _cli_domain_query(cmd: str, args: List[str]) -> Dict:
    """Handle CLI domain sub-commands like 'production wheat US'."""
    dcfg = DOMAIN_COMMANDS.get(cmd)
    if not dcfg:
        return {"success": False, "error": f"Unknown command: {cmd}"}

    domain = dcfg["domain"]
    element = dcfg["default_element"]
    item = None
    country = None

    if cmd == "fertilizer":
        fert_map = {"nitrogen": "3102", "n": "3102",
                    "phosphate": "3103", "p": "3103", "p2o5": "3103",
                    "potash": "3104", "k": "3104", "k2o": "3104"}
        if args:
            item = fert_map.get(args[0].lower(), args[0])
            if len(args) > 1:
                country = args[1]
        return query_domain(domain, item=item, element=element, country=country)

    if cmd in ("land_use", "food_security", "emissions"):
        if args:
            country = args[0]
        if cmd == "land_use":
            item = "6621"
        elif cmd == "food_security":
            item = "21010"
        elif cmd == "emissions":
            item = "1711"
        return query_domain(domain, item=item, element=element, country=country)

    if args:
        item = args[0]
        if len(args) > 1:
            country = args[1]

    return query_domain(domain, item=item, element=element, country=country)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()

        if cmd in ("--help", "-h", "help"):
            _print_help()

        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))

        elif cmd == "domains":
            domains = _static_domain_list()
            print(json.dumps({
                "success": True,
                "domains": domains,
                "count": len(domains),
                "note": "Static list — use list_domains() with auth for live data",
            }, indent=2, default=str))

        elif cmd == "top":
            commodity = sys.argv[2] if len(sys.argv) > 2 else "wheat"
            top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            print(json.dumps(get_top_producers(commodity, top_n=top_n), indent=2, default=str))

        elif cmd in DOMAIN_COMMANDS:
            result = _cli_domain_query(cmd, sys.argv[2:])
            print(json.dumps(result, indent=2, default=str))

        elif cmd.upper() in INDICATORS:
            country = sys.argv[2] if len(sys.argv) > 2 else None
            result = fetch_data(cmd, country=country)
            print(json.dumps(result, indent=2, default=str))

        else:
            result = fetch_data(cmd)
            if not result.get("success") and "Unknown indicator" in result.get("error", ""):
                result = query_domain(cmd.upper(), item=sys.argv[2] if len(sys.argv) > 2 else None,
                                      country=sys.argv[3] if len(sys.argv) > 3 else None)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))

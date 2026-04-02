#!/usr/bin/env python3
"""
ENTSO-E Transparency Platform Module — Initiative 0063

European electricity grid data: day-ahead prices, generation by fuel type,
total load (consumption), cross-border physical flows, installed capacity,
and wind/solar forecast vs actual. Covers 35 European countries/bidding zones.

Data Source: https://web-api.tp.entsoe.eu/api
Protocol: REST (XML responses)
Auth: Security token (ENTSOE_API_TOKEN, free registration)
Rate Limits: 400 requests/minute
Refresh: 1h (real-time), 6h (prices), 24h (structural)
Coverage: EU27 + UK, Norway, Switzerland

Author: QUANTCLAW DATA Build Agent
Initiative: 0063
"""

import json
import os
import sys
import time
import hashlib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_URL = "https://web-api.tp.entsoe.eu/api"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "entsoe_energy"
REQUEST_TIMEOUT = 45
REQUEST_DELAY = 0.2

CACHE_TTL = {
    "realtime": 1,
    "prices": 6,
    "structural": 24,
}

NS = {"ns": "urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0"}
NS_PRICE = {"ns": "urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3"}
NS_TRANS = {"ns": "urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0"}

EIC_DOMAINS = {
    "DE_LU": "10Y1001A1001A82H",
    "DE": "10Y1001A1001A83F",
    "FR": "10YFR-RTE------C",
    "ES": "10YES-REE------0",
    "IT_NORD": "10Y1001A1001A73I",
    "IT_CNOR": "10Y1001A1001A70O",
    "IT_CSUD": "10Y1001A1001A71M",
    "IT_SUD": "10Y1001A1001A788",
    "IT_SICI": "10Y1001A1001A74G",
    "IT_SARD": "10Y1001A1001A75E",
    "NL": "10YNL----------L",
    "BE": "10YBE----------2",
    "AT": "10YAT-APG------L",
    "PL": "10YPL-AREA-----S",
    "CZ": "10YCZ-CEPS-----N",
    "DK_1": "10YDK-1--------W",
    "DK_2": "10YDK-2--------M",
    "FI": "10YFI-1--------U",
    "SE_1": "10Y1001A1001A44P",
    "SE_2": "10Y1001A1001A45N",
    "SE_3": "10Y1001A1001A46L",
    "SE_4": "10Y1001A1001A47J",
    "NO_1": "10YNO-1--------2",
    "NO_2": "10YNO-2--------T",
    "NO_3": "10YNO-3--------J",
    "NO_4": "10YNO-4--------9",
    "NO_5": "10Y1001A1001A48H",
    "GB": "10YGB----------A",
    "CH": "10YCH-SWISSGRIDZ",
    "PT": "10YPT-REN------W",
    "IE": "10YIE-1001A00010",
    "GR": "10YGR-HTSO-----Y",
    "RO": "10YRO-TEL------P",
    "BG": "10YCA-BULGARIA-R",
    "HU": "10YHU-MAVIR----U",
    "SK": "10YSK-SEPS-----K",
    "SI": "10YSI-ELES-----O",
    "HR": "10YHR-HEP------M",
    "RS": "10YCS-SERBIATSOV",
    "BA": "10YBA-JPCC-----D",
    "ME": "10YCS-CG-TSO---S",
    "MK": "10YMK-MEPSO----8",
    "AL": "10YAL-KESH-----5",
    "LT": "10YLT-1001A0008Q",
    "LV": "10YLV-1001A00074",
    "EE": "10Y1001A1001A39I",
    "LU": "10YLU-CEGEDEL-NQ",
}

PSRTYPE_MAP = {
    "B01": "Biomass",
    "B02": "Fossil Brown coal/Lignite",
    "B03": "Fossil Coal-derived gas",
    "B04": "Fossil Gas",
    "B05": "Fossil Hard coal",
    "B06": "Fossil Oil",
    "B07": "Fossil Oil shale",
    "B08": "Fossil Peat",
    "B09": "Geothermal",
    "B10": "Hydro Pumped Storage",
    "B11": "Hydro Run-of-river and poundage",
    "B12": "Hydro Water Reservoir",
    "B13": "Marine",
    "B14": "Nuclear",
    "B15": "Other renewable",
    "B16": "Solar",
    "B17": "Waste",
    "B18": "Wind Offshore",
    "B19": "Wind Onshore",
    "B20": "Other",
}

INDICATORS = {
    "PRICES_DAY_AHEAD": {
        "name": "Day-Ahead Electricity Prices",
        "description": "Hourly day-ahead market clearing prices by bidding zone (EUR/MWh)",
        "document_type": "A44",
        "cache_category": "prices",
        "unit": "EUR/MWh",
    },
    "GENERATION_PER_TYPE": {
        "name": "Actual Generation per Production Type",
        "description": "Hourly electricity generation breakdown by fuel source (wind, solar, nuclear, gas, coal, hydro)",
        "document_type": "A75",
        "process_type": "A16",
        "cache_category": "realtime",
        "unit": "MW",
    },
    "TOTAL_LOAD": {
        "name": "Actual Total Load",
        "description": "Actual electricity consumption (demand) by country, hourly resolution",
        "document_type": "A65",
        "process_type": "A16",
        "cache_category": "realtime",
        "unit": "MW",
    },
    "CROSS_BORDER_FLOWS": {
        "name": "Cross-Border Physical Flows",
        "description": "Physical electricity transfers between countries/bidding zones",
        "document_type": "A11",
        "cache_category": "realtime",
        "unit": "MW",
    },
    "INSTALLED_CAPACITY": {
        "name": "Installed Generation Capacity per Type",
        "description": "Total installed generation capacity by fuel type per bidding zone",
        "document_type": "A68",
        "process_type": "A33",
        "cache_category": "structural",
        "unit": "MW",
    },
    "GENERATION_FORECAST": {
        "name": "Day-Ahead Generation Forecast (Wind/Solar)",
        "description": "Forecasted wind and solar generation for the next day",
        "document_type": "A69",
        "process_type": "A01",
        "cache_category": "prices",
        "unit": "MW",
    },
}


def _get_token() -> str:
    return os.environ.get("ENTSOE_API_TOKEN", "").strip()


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H00")


def _default_period() -> Tuple[str, str]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=48)
    return _format_dt(start), _format_dt(now)


def _cache_path(key: str, params_hash: str) -> Path:
    safe = key.replace("/", "_").replace(" ", "_")
    return CACHE_DIR / f"{safe}_{params_hash}.json"


def _params_hash(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def _read_cache(path: Path, ttl_hours: int) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(hours=ttl_hours):
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


def _resolve_domain(zone: str) -> Optional[str]:
    zone = zone.upper().replace("-", "_")
    return EIC_DOMAINS.get(zone)


def _api_request(params: dict) -> Dict:
    token = _get_token()
    if not token:
        return {"success": False, "error": "ENTSOE_API_TOKEN not set. Register at https://transparency.entsoe.eu/"}
    params["securityToken"] = token
    try:
        resp = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 401:
            return {"success": False, "error": "Invalid API token (HTTP 401)"}
        if resp.status_code == 400:
            reason = _extract_xml_error(resp.text)
            return {"success": False, "error": f"Bad request: {reason}"}
        if resp.status_code == 409:
            return {"success": False, "error": "Too many requests (HTTP 409). Rate limit exceeded."}
        resp.raise_for_status()
        return {"success": True, "xml": resp.text}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _extract_xml_error(xml_text: str) -> str:
    try:
        root = ET.fromstring(xml_text)
        for elem in root.iter():
            if "Reason" in elem.tag and elem.text:
                return elem.text.strip()
            if "text" in elem.tag and elem.text:
                return elem.text.strip()
    except ET.ParseError:
        pass
    return "Unknown error"


def _find_ns(root: ET.Element) -> dict:
    """Dynamically detect the XML namespace from the root element."""
    tag = root.tag
    if tag.startswith("{"):
        ns_uri = tag[1:tag.index("}")]
        return {"ns": ns_uri}
    return {}


def _parse_timeseries(xml_text: str) -> List[Dict]:
    """Generic parser: extract all TimeSeries with their points from ENTSO-E XML."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    ns = _find_ns(root)
    prefix = f"{{{ns['ns']}}}" if ns else ""

    all_series = []
    for ts in root.iter(f"{prefix}TimeSeries"):
        series_meta = {}
        for child in ts:
            tag = child.tag.replace(prefix, "")
            if tag == "Period":
                continue
            if tag == "MktPSRType":
                psr_el = child.find(f"{prefix}psrType")
                if psr_el is not None and psr_el.text:
                    series_meta["psr_type"] = psr_el.text
                    series_meta["psr_name"] = PSRTYPE_MAP.get(psr_el.text, psr_el.text)
            elif child.text and child.text.strip():
                series_meta[tag] = child.text.strip()

        for period in ts.iter(f"{prefix}Period"):
            start_el = period.find(f"{prefix}timeInterval/{prefix}start")
            res_el = period.find(f"{prefix}resolution")
            period_start = start_el.text if start_el is not None else None
            resolution = res_el.text if res_el is not None else "PT60M"

            res_minutes = 60
            if resolution == "PT15M":
                res_minutes = 15
            elif resolution == "PT30M":
                res_minutes = 30

            for point in period.iter(f"{prefix}Point"):
                pos_el = point.find(f"{prefix}position")
                qty_el = point.find(f"{prefix}quantity")
                price_el = point.find(f"{prefix}price.amount")
                if pos_el is None:
                    continue
                position = int(pos_el.text)
                value = None
                if price_el is not None and price_el.text:
                    value = float(price_el.text)
                elif qty_el is not None and qty_el.text:
                    value = float(qty_el.text)
                if value is None:
                    continue

                if period_start:
                    try:
                        base = datetime.fromisoformat(period_start.replace("Z", "+00:00"))
                        point_time = base + timedelta(minutes=res_minutes * (position - 1))
                        ts_str = point_time.strftime("%Y-%m-%dT%H:%M:%SZ")
                    except (ValueError, TypeError):
                        ts_str = f"P{position}"
                else:
                    ts_str = f"P{position}"

                all_series.append({
                    **series_meta,
                    "datetime": ts_str,
                    "position": position,
                    "value": value,
                    "resolution": resolution,
                })

    all_series.sort(key=lambda x: x.get("datetime", ""))
    return all_series


# ──────────────────────────── Data Fetchers ────────────────────────────

def fetch_prices(zone: str = "DE_LU", period_start: str = None, period_end: str = None) -> Dict:
    """Fetch day-ahead electricity prices for a bidding zone."""
    eic = _resolve_domain(zone)
    if not eic:
        return {"success": False, "error": f"Unknown zone: {zone}", "available_zones": list(EIC_DOMAINS.keys())}

    if not period_start or not period_end:
        period_start, period_end = _default_period()

    cache_key = f"prices_{zone}"
    cp = _cache_path(cache_key, _params_hash({"z": zone, "s": period_start, "e": period_end}))
    cached = _read_cache(cp, CACHE_TTL["prices"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request({
        "documentType": "A44",
        "in_Domain": eic,
        "out_Domain": eic,
        "periodStart": period_start,
        "periodEnd": period_end,
    })
    if not result["success"]:
        return {"success": False, "indicator": "PRICES_DAY_AHEAD", "zone": zone, "error": result["error"]}

    points = _parse_timeseries(result["xml"])
    if not points:
        return {"success": False, "indicator": "PRICES_DAY_AHEAD", "zone": zone, "error": "No price data returned"}

    prices = [{"datetime": p["datetime"], "value": p["value"], "unit": "EUR/MWh"} for p in points]
    latest = prices[-1] if prices else None
    avg_price = round(sum(p["value"] for p in prices) / len(prices), 2) if prices else None
    max_price = max(p["value"] for p in prices) if prices else None
    min_price = min(p["value"] for p in prices) if prices else None

    response = {
        "success": True,
        "indicator": "PRICES_DAY_AHEAD",
        "name": "Day-Ahead Electricity Prices",
        "zone": zone,
        "eic_code": eic,
        "unit": "EUR/MWh",
        "latest_price": latest["value"] if latest else None,
        "latest_datetime": latest["datetime"] if latest else None,
        "avg_price": avg_price,
        "max_price": max_price,
        "min_price": min_price,
        "data_points": prices[-48:],
        "total_points": len(prices),
        "period_start": period_start,
        "period_end": period_end,
        "source": "ENTSO-E Transparency Platform",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def fetch_generation(zone: str = "DE_LU", period_start: str = None, period_end: str = None) -> Dict:
    """Fetch actual generation per production type."""
    eic = _resolve_domain(zone)
    if not eic:
        return {"success": False, "error": f"Unknown zone: {zone}", "available_zones": list(EIC_DOMAINS.keys())}

    if not period_start or not period_end:
        period_start, period_end = _default_period()

    cache_key = f"generation_{zone}"
    cp = _cache_path(cache_key, _params_hash({"z": zone, "s": period_start, "e": period_end}))
    cached = _read_cache(cp, CACHE_TTL["realtime"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request({
        "documentType": "A75",
        "processType": "A16",
        "in_Domain": eic,
        "periodStart": period_start,
        "periodEnd": period_end,
    })
    if not result["success"]:
        return {"success": False, "indicator": "GENERATION_PER_TYPE", "zone": zone, "error": result["error"]}

    points = _parse_timeseries(result["xml"])
    if not points:
        return {"success": False, "indicator": "GENERATION_PER_TYPE", "zone": zone, "error": "No generation data returned"}

    by_type = {}
    latest_dt = max(p["datetime"] for p in points)
    for p in points:
        psr = p.get("psr_name", p.get("psr_type", "Unknown"))
        if psr not in by_type:
            by_type[psr] = []
        by_type[psr].append({"datetime": p["datetime"], "value": p["value"]})

    latest_mix = {}
    for p in points:
        if p["datetime"] == latest_dt:
            psr = p.get("psr_name", p.get("psr_type", "Unknown"))
            latest_mix[psr] = p["value"]

    total_gen = sum(latest_mix.values()) if latest_mix else 0
    mix_pct = {}
    if total_gen > 0:
        mix_pct = {k: round(v / total_gen * 100, 1) for k, v in latest_mix.items()}

    response = {
        "success": True,
        "indicator": "GENERATION_PER_TYPE",
        "name": "Actual Generation per Production Type",
        "zone": zone,
        "eic_code": eic,
        "unit": "MW",
        "latest_datetime": latest_dt,
        "total_generation_mw": round(total_gen, 1),
        "latest_mix_mw": dict(sorted(latest_mix.items(), key=lambda x: -x[1])),
        "latest_mix_pct": dict(sorted(mix_pct.items(), key=lambda x: -x[1])),
        "fuel_types": list(by_type.keys()),
        "generation_by_type": {k: v[-24:] for k, v in by_type.items()},
        "total_points": len(points),
        "period_start": period_start,
        "period_end": period_end,
        "source": "ENTSO-E Transparency Platform",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def fetch_load(zone: str = "DE_LU", period_start: str = None, period_end: str = None) -> Dict:
    """Fetch actual total electricity load (consumption)."""
    eic = _resolve_domain(zone)
    if not eic:
        return {"success": False, "error": f"Unknown zone: {zone}", "available_zones": list(EIC_DOMAINS.keys())}

    if not period_start or not period_end:
        period_start, period_end = _default_period()

    cache_key = f"load_{zone}"
    cp = _cache_path(cache_key, _params_hash({"z": zone, "s": period_start, "e": period_end}))
    cached = _read_cache(cp, CACHE_TTL["realtime"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request({
        "documentType": "A65",
        "processType": "A16",
        "outBiddingZone_Domain": eic,
        "periodStart": period_start,
        "periodEnd": period_end,
    })
    if not result["success"]:
        return {"success": False, "indicator": "TOTAL_LOAD", "zone": zone, "error": result["error"]}

    points = _parse_timeseries(result["xml"])
    if not points:
        return {"success": False, "indicator": "TOTAL_LOAD", "zone": zone, "error": "No load data returned"}

    load_data = [{"datetime": p["datetime"], "value": p["value"], "unit": "MW"} for p in points]
    latest = load_data[-1] if load_data else None
    values = [p["value"] for p in load_data]
    avg_load = round(sum(values) / len(values), 1) if values else None
    peak_load = max(values) if values else None
    min_load = min(values) if values else None

    response = {
        "success": True,
        "indicator": "TOTAL_LOAD",
        "name": "Actual Total Load (Consumption)",
        "zone": zone,
        "eic_code": eic,
        "unit": "MW",
        "latest_load_mw": latest["value"] if latest else None,
        "latest_datetime": latest["datetime"] if latest else None,
        "avg_load_mw": avg_load,
        "peak_load_mw": peak_load,
        "min_load_mw": min_load,
        "data_points": load_data[-48:],
        "total_points": len(load_data),
        "period_start": period_start,
        "period_end": period_end,
        "source": "ENTSO-E Transparency Platform",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def fetch_cross_border(from_zone: str = "DE_LU", to_zone: str = "FR",
                       period_start: str = None, period_end: str = None) -> Dict:
    """Fetch cross-border physical electricity flows."""
    from_eic = _resolve_domain(from_zone)
    to_eic = _resolve_domain(to_zone)
    if not from_eic:
        return {"success": False, "error": f"Unknown zone: {from_zone}", "available_zones": list(EIC_DOMAINS.keys())}
    if not to_eic:
        return {"success": False, "error": f"Unknown zone: {to_zone}", "available_zones": list(EIC_DOMAINS.keys())}

    if not period_start or not period_end:
        period_start, period_end = _default_period()

    cache_key = f"xborder_{from_zone}_{to_zone}"
    cp = _cache_path(cache_key, _params_hash({"f": from_zone, "t": to_zone, "s": period_start, "e": period_end}))
    cached = _read_cache(cp, CACHE_TTL["realtime"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request({
        "documentType": "A11",
        "in_Domain": from_eic,
        "out_Domain": to_eic,
        "periodStart": period_start,
        "periodEnd": period_end,
    })
    if not result["success"]:
        return {"success": False, "indicator": "CROSS_BORDER_FLOWS", "from": from_zone, "to": to_zone, "error": result["error"]}

    points = _parse_timeseries(result["xml"])
    if not points:
        return {"success": False, "indicator": "CROSS_BORDER_FLOWS", "from": from_zone, "to": to_zone, "error": "No flow data returned"}

    flows = [{"datetime": p["datetime"], "value": p["value"], "unit": "MW"} for p in points]
    latest = flows[-1] if flows else None
    values = [f["value"] for f in flows]
    avg_flow = round(sum(values) / len(values), 1) if values else None

    response = {
        "success": True,
        "indicator": "CROSS_BORDER_FLOWS",
        "name": f"Physical Flows {from_zone} → {to_zone}",
        "from_zone": from_zone,
        "to_zone": to_zone,
        "from_eic": from_eic,
        "to_eic": to_eic,
        "unit": "MW",
        "latest_flow_mw": latest["value"] if latest else None,
        "latest_datetime": latest["datetime"] if latest else None,
        "avg_flow_mw": avg_flow,
        "max_flow_mw": max(values) if values else None,
        "min_flow_mw": min(values) if values else None,
        "data_points": flows[-48:],
        "total_points": len(flows),
        "period_start": period_start,
        "period_end": period_end,
        "source": "ENTSO-E Transparency Platform",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def fetch_wind_solar(zone: str = "DE_LU", period_start: str = None, period_end: str = None) -> Dict:
    """Fetch wind/solar generation with forecast comparison."""
    eic = _resolve_domain(zone)
    if not eic:
        return {"success": False, "error": f"Unknown zone: {zone}", "available_zones": list(EIC_DOMAINS.keys())}

    if not period_start or not period_end:
        period_start, period_end = _default_period()

    cache_key = f"windsolar_{zone}"
    cp = _cache_path(cache_key, _params_hash({"z": zone, "s": period_start, "e": period_end}))
    cached = _read_cache(cp, CACHE_TTL["realtime"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    actual_result = _api_request({
        "documentType": "A75",
        "processType": "A16",
        "in_Domain": eic,
        "periodStart": period_start,
        "periodEnd": period_end,
    })

    time.sleep(REQUEST_DELAY)

    forecast_result = _api_request({
        "documentType": "A69",
        "processType": "A01",
        "in_Domain": eic,
        "periodStart": period_start,
        "periodEnd": period_end,
    })

    wind_solar_types = {"B16", "B18", "B19"}
    actual_points = _parse_timeseries(actual_result.get("xml", "")) if actual_result.get("success") else []
    forecast_points = _parse_timeseries(forecast_result.get("xml", "")) if forecast_result.get("success") else []

    actual_ws = [p for p in actual_points if p.get("psr_type") in wind_solar_types]
    forecast_ws = forecast_points

    actual_by_dt = {}
    for p in actual_ws:
        dt = p["datetime"]
        psr = p.get("psr_name", p.get("psr_type", "Renewable"))
        if dt not in actual_by_dt:
            actual_by_dt[dt] = {}
        actual_by_dt[dt][psr] = p["value"]

    forecast_by_dt = {}
    for p in forecast_ws:
        dt = p["datetime"]
        forecast_by_dt[dt] = forecast_by_dt.get(dt, 0) + p["value"]

    combined = []
    all_dts = sorted(set(list(actual_by_dt.keys()) + list(forecast_by_dt.keys())))
    for dt in all_dts:
        actual_total = sum(actual_by_dt.get(dt, {}).values())
        forecast_total = forecast_by_dt.get(dt, None)
        entry = {
            "datetime": dt,
            "actual_mw": round(actual_total, 1) if actual_by_dt.get(dt) else None,
            "forecast_mw": round(forecast_total, 1) if forecast_total is not None else None,
        }
        if entry["actual_mw"] and entry["forecast_mw"]:
            entry["error_mw"] = round(entry["actual_mw"] - entry["forecast_mw"], 1)
            entry["error_pct"] = round(entry["error_mw"] / entry["forecast_mw"] * 100, 1) if entry["forecast_mw"] != 0 else None
        combined.append(entry)

    latest_actual = {}
    if actual_ws:
        latest_dt = max(p["datetime"] for p in actual_ws)
        for p in actual_ws:
            if p["datetime"] == latest_dt:
                psr = p.get("psr_name", p.get("psr_type", "Unknown"))
                latest_actual[psr] = p["value"]

    response = {
        "success": True,
        "indicator": "WIND_SOLAR",
        "name": "Wind & Solar Generation (Actual vs Forecast)",
        "zone": zone,
        "eic_code": eic,
        "unit": "MW",
        "latest_breakdown_mw": latest_actual,
        "latest_total_mw": round(sum(latest_actual.values()), 1) if latest_actual else None,
        "comparison": combined[-48:],
        "total_points": len(combined),
        "actual_available": bool(actual_ws),
        "forecast_available": bool(forecast_ws),
        "period_start": period_start,
        "period_end": period_end,
        "source": "ENTSO-E Transparency Platform",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def fetch_capacity(zone: str = "DE_LU", year: int = None) -> Dict:
    """Fetch installed generation capacity per type."""
    eic = _resolve_domain(zone)
    if not eic:
        return {"success": False, "error": f"Unknown zone: {zone}", "available_zones": list(EIC_DOMAINS.keys())}

    if not year:
        year = datetime.now().year

    period_start = f"{year}01010000"
    period_end = f"{year}12312300"

    cache_key = f"capacity_{zone}_{year}"
    cp = _cache_path(cache_key, _params_hash({"z": zone, "y": year}))
    cached = _read_cache(cp, CACHE_TTL["structural"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request({
        "documentType": "A68",
        "processType": "A33",
        "in_Domain": eic,
        "periodStart": period_start,
        "periodEnd": period_end,
    })
    if not result["success"]:
        return {"success": False, "indicator": "INSTALLED_CAPACITY", "zone": zone, "error": result["error"]}

    points = _parse_timeseries(result["xml"])
    if not points:
        return {"success": False, "indicator": "INSTALLED_CAPACITY", "zone": zone, "error": "No capacity data returned"}

    capacity = {}
    for p in points:
        psr = p.get("psr_name", p.get("psr_type", "Unknown"))
        if psr not in capacity or p["value"] > capacity[psr]:
            capacity[psr] = p["value"]

    total = sum(capacity.values())
    capacity_pct = {}
    if total > 0:
        capacity_pct = {k: round(v / total * 100, 1) for k, v in capacity.items()}

    response = {
        "success": True,
        "indicator": "INSTALLED_CAPACITY",
        "name": "Installed Generation Capacity per Type",
        "zone": zone,
        "eic_code": eic,
        "year": year,
        "unit": "MW",
        "total_capacity_mw": round(total, 1),
        "capacity_by_type_mw": dict(sorted(capacity.items(), key=lambda x: -x[1])),
        "capacity_by_type_pct": dict(sorted(capacity_pct.items(), key=lambda x: -x[1])),
        "fuel_types_count": len(capacity),
        "source": "ENTSO-E Transparency Platform",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def fetch_nuclear(zone: str = "FR", period_start: str = None, period_end: str = None) -> Dict:
    """Fetch nuclear generation data (actual output as proxy for availability)."""
    eic = _resolve_domain(zone)
    if not eic:
        return {"success": False, "error": f"Unknown zone: {zone}", "available_zones": list(EIC_DOMAINS.keys())}

    if not period_start or not period_end:
        period_start, period_end = _default_period()

    cache_key = f"nuclear_{zone}"
    cp = _cache_path(cache_key, _params_hash({"z": zone, "s": period_start, "e": period_end}))
    cached = _read_cache(cp, CACHE_TTL["realtime"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request({
        "documentType": "A75",
        "processType": "A16",
        "in_Domain": eic,
        "periodStart": period_start,
        "periodEnd": period_end,
    })
    if not result["success"]:
        return {"success": False, "indicator": "NUCLEAR", "zone": zone, "error": result["error"]}

    points = _parse_timeseries(result["xml"])
    nuclear_points = [p for p in points if p.get("psr_type") == "B14"]

    if not nuclear_points:
        return {"success": False, "indicator": "NUCLEAR", "zone": zone, "error": "No nuclear generation data (zone may not have nuclear plants)"}

    nuc_data = [{"datetime": p["datetime"], "value": p["value"], "unit": "MW"} for p in nuclear_points]
    latest = nuc_data[-1] if nuc_data else None
    values = [d["value"] for d in nuc_data]
    avg_output = round(sum(values) / len(values), 1) if values else None
    peak_output = max(values) if values else None
    min_output = min(values) if values else None

    cap_data = fetch_capacity(zone)
    installed_nuclear = None
    availability_pct = None
    if cap_data.get("success"):
        installed_nuclear = cap_data.get("capacity_by_type_mw", {}).get("Nuclear")
        if installed_nuclear and latest:
            availability_pct = round(latest["value"] / installed_nuclear * 100, 1)

    response = {
        "success": True,
        "indicator": "NUCLEAR",
        "name": "Nuclear Generation & Availability",
        "zone": zone,
        "eic_code": eic,
        "unit": "MW",
        "latest_output_mw": latest["value"] if latest else None,
        "latest_datetime": latest["datetime"] if latest else None,
        "avg_output_mw": avg_output,
        "peak_output_mw": peak_output,
        "min_output_mw": min_output,
        "installed_capacity_mw": installed_nuclear,
        "availability_pct": availability_pct,
        "data_points": nuc_data[-48:],
        "total_points": len(nuc_data),
        "period_start": period_start,
        "period_end": period_end,
        "source": "ENTSO-E Transparency Platform",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


# ──────────────────────────── Generic Interface ────────────────────────────

def fetch_data(indicator: str, zone: str = "DE_LU", **kwargs) -> Dict:
    """Fetch a specific indicator."""
    indicator = indicator.upper()
    dispatch = {
        "PRICES_DAY_AHEAD": lambda: fetch_prices(zone, **kwargs),
        "PRICES": lambda: fetch_prices(zone, **kwargs),
        "GENERATION_PER_TYPE": lambda: fetch_generation(zone, **kwargs),
        "GENERATION": lambda: fetch_generation(zone, **kwargs),
        "TOTAL_LOAD": lambda: fetch_load(zone, **kwargs),
        "LOAD": lambda: fetch_load(zone, **kwargs),
        "CROSS_BORDER_FLOWS": lambda: fetch_cross_border(zone, kwargs.get("to_zone", "FR"), **{k: v for k, v in kwargs.items() if k != "to_zone"}),
        "CROSS_BORDER": lambda: fetch_cross_border(zone, kwargs.get("to_zone", "FR"), **{k: v for k, v in kwargs.items() if k != "to_zone"}),
        "INSTALLED_CAPACITY": lambda: fetch_capacity(zone, kwargs.get("year")),
        "CAPACITY": lambda: fetch_capacity(zone, kwargs.get("year")),
        "GENERATION_FORECAST": lambda: fetch_wind_solar(zone, **kwargs),
        "WIND_SOLAR": lambda: fetch_wind_solar(zone, **kwargs),
        "NUCLEAR": lambda: fetch_nuclear(zone, **kwargs),
    }
    if indicator not in dispatch:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}
    return dispatch[indicator]()


def get_available_indicators() -> List[Dict]:
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "unit": v["unit"],
            "cache_ttl_hours": CACHE_TTL[v["cache_category"]],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(zone: str = None) -> Dict:
    """Get a summary of major European electricity metrics."""
    target_zone = zone or "DE_LU"
    results = {}
    errors = []

    for label, fn in [
        ("prices", lambda: fetch_prices(target_zone)),
        ("load", lambda: fetch_load(target_zone)),
        ("generation", lambda: fetch_generation(target_zone)),
    ]:
        try:
            data = fn()
            if data.get("success"):
                results[label] = data
            else:
                errors.append({"category": label, "error": data.get("error", "unknown")})
        except Exception as e:
            errors.append({"category": label, "error": str(e)})
        time.sleep(REQUEST_DELAY)

    summary = {"zone": target_zone}
    if "prices" in results:
        summary["latest_price_eur_mwh"] = results["prices"].get("latest_price")
        summary["avg_price_eur_mwh"] = results["prices"].get("avg_price")
    if "load" in results:
        summary["latest_load_mw"] = results["load"].get("latest_load_mw")
        summary["peak_load_mw"] = results["load"].get("peak_load_mw")
    if "generation" in results:
        summary["total_generation_mw"] = results["generation"].get("total_generation_mw")
        summary["generation_mix_pct"] = results["generation"].get("latest_mix_pct")

    return {
        "success": True,
        "source": "ENTSO-E Transparency Platform",
        "summary": summary,
        "errors": errors if errors else None,
        "available_zones": list(EIC_DOMAINS.keys()),
        "timestamp": datetime.now().isoformat(),
    }


# ──────────────────────────── CLI ────────────────────────────

def _print_help():
    print("""
ENTSO-E Transparency Platform Module (Initiative 0063)
European Electricity Grid Data — 35 Countries/Bidding Zones

Usage:
  python entsoe_energy.py                              # Summary for DE_LU
  python entsoe_energy.py prices DE_LU                 # Day-ahead prices Germany
  python entsoe_energy.py generation FR                # Generation mix France
  python entsoe_energy.py load ES                      # Electricity load Spain
  python entsoe_energy.py cross_border DE_LU FR        # Physical flows DE→FR
  python entsoe_energy.py wind_solar DE_LU             # Wind/solar actual vs forecast
  python entsoe_energy.py capacity PL                  # Installed capacity Poland
  python entsoe_energy.py nuclear FR                   # Nuclear availability France
  python entsoe_energy.py list                         # List indicators
  python entsoe_energy.py zones                        # List available zones

Bidding Zones:""")
    zones_per_line = 8
    zone_list = list(EIC_DOMAINS.keys())
    for i in range(0, len(zone_list), zones_per_line):
        print(f"  {', '.join(zone_list[i:i+zones_per_line])}")
    print(f"""
Source: {BASE_URL}
Protocol: REST (XML)
Auth: ENTSOE_API_TOKEN (register at https://transparency.entsoe.eu/)
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
    elif args[0] == "zones":
        print(json.dumps(EIC_DOMAINS, indent=2))
    elif args[0] == "prices":
        zone = args[1] if len(args) > 1 else "DE_LU"
        print(json.dumps(fetch_prices(zone), indent=2, default=str))
    elif args[0] == "generation":
        zone = args[1] if len(args) > 1 else "DE_LU"
        print(json.dumps(fetch_generation(zone), indent=2, default=str))
    elif args[0] == "load":
        zone = args[1] if len(args) > 1 else "DE_LU"
        print(json.dumps(fetch_load(zone), indent=2, default=str))
    elif args[0] == "cross_border":
        from_z = args[1] if len(args) > 1 else "DE_LU"
        to_z = args[2] if len(args) > 2 else "FR"
        print(json.dumps(fetch_cross_border(from_z, to_z), indent=2, default=str))
    elif args[0] == "wind_solar":
        zone = args[1] if len(args) > 1 else "DE_LU"
        print(json.dumps(fetch_wind_solar(zone), indent=2, default=str))
    elif args[0] == "capacity":
        zone = args[1] if len(args) > 1 else "DE_LU"
        print(json.dumps(fetch_capacity(zone), indent=2, default=str))
    elif args[0] == "nuclear":
        zone = args[1] if len(args) > 1 else "FR"
        print(json.dumps(fetch_nuclear(zone), indent=2, default=str))
    else:
        result = fetch_data(args[0], args[1] if len(args) > 1 else "DE_LU")
        print(json.dumps(result, indent=2, default=str))

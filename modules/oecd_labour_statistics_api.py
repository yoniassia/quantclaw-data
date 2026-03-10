#!/usr/bin/env python3
"""
OECD Labour Statistics API — QuantClaw Data Module
Provides access to OECD labour market data via the SDMX REST API.
Covers unemployment rates, employment indicators, average wages, working hours,
gender wage gaps, minimum wages, and population data for all OECD member countries.

Source: https://sdmx.oecd.org/public/rest/
Category: Labor & Demographics
Free tier: true; no API key required, rate limited
Update frequency: monthly/quarterly/annual depending on indicator
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional


BASE_URL = "https://sdmx.oecd.org/public/rest/data"
TIMEOUT = 30

# Agency and dataflow mappings for labour statistics
# Format: (agency, dataflow_id, version, num_dimensions)
DATAFLOWS = {
    # Labour Force Statistics (agency: OECD.SDD.TPS) — 9 dims
    "unemployment_indicators": ("OECD.SDD.TPS", "DSD_LFS@DF_IALFS_INDIC", "1.0", 9),
    "employment_levels": ("OECD.SDD.TPS", "DSD_LFS@DF_IALFS_INDIC", "1.0", 9),
    # Employment & Earnings (agency: OECD.ELS.SAE)
    "average_wages": ("OECD.ELS.SAE", "DSD_EARNINGS@AV_AN_WAGE", "1.0", 9),
    "gender_wage_gap": ("OECD.ELS.SAE", "DSD_EARNINGS@GENDER_WAGE_GAP", "1.0", 7),
    "minimum_wages_real": ("OECD.ELS.SAE", "DSD_EARNINGS@RMW", "1.0", 7),
    "hours_worked": ("OECD.ELS.SAE", "DSD_HW@DF_AVG_ANN_HRS_WKD", "1.0", 13),
    "unemployment_duration": ("OECD.ELS.SAE", "DSD_DUR@DF_AVD_DUR", "1.0", 7),
    "trade_union_density": ("OECD.ELS.SAE", "DSD_TUD_CBC@DF_TUD", "1.0", 3),
    "population": ("OECD.ELS.SAE", "DSD_POPULATION@DF_POP_ALL", "1.0", 7),
}

# Common OECD country codes
COUNTRY_CODES = {
    "USA": "USA", "US": "USA",
    "GBR": "GBR", "UK": "GBR",
    "DEU": "DEU", "GERMANY": "DEU",
    "FRA": "FRA", "FRANCE": "FRA",
    "JPN": "JPN", "JAPAN": "JPN",
    "CAN": "CAN", "CANADA": "CAN",
    "AUS": "AUS", "AUSTRALIA": "AUS",
    "KOR": "KOR", "KOREA": "KOR",
    "MEX": "MEX", "MEXICO": "MEX",
    "ITA": "ITA", "ITALY": "ITA",
    "ESP": "ESP", "SPAIN": "ESP",
    "NLD": "NLD", "NETHERLANDS": "NLD",
    "CHE": "CHE", "SWITZERLAND": "CHE",
    "SWE": "SWE", "SWEDEN": "SWE",
    "NOR": "NOR", "NORWAY": "NOR",
    "DNK": "DNK", "DENMARK": "DNK",
    "FIN": "FIN", "FINLAND": "FIN",
    "IRL": "IRL", "IRELAND": "IRL",
    "NZL": "NZL",
    "POL": "POL", "POLAND": "POL",
    "TUR": "TUR", "TURKEY": "TUR", "TÜR": "TUR",
    "ISR": "ISR", "ISRAEL": "ISR",
    "OECD": "OECD",
}


def _resolve_country(country: str) -> str:
    """Resolve country name/alias to OECD 3-letter code."""
    upper = country.upper().strip()
    return COUNTRY_CODES.get(upper, upper)


def _wildcard_key(country: str, ndims: int) -> str:
    """Build a wildcard key with country in first position and dots for remaining dims."""
    cc = _resolve_country(country)
    return cc + "." * (ndims - 1)


def _fetch_sdmx(agency: str, dataflow: str, version: str, key: str,
                 start_period: Optional[str] = None, end_period: Optional[str] = None) -> dict:
    """
    Fetch data from OECD SDMX REST API in JSON format.

    Args:
        agency: OECD agency ID (e.g. 'OECD.SDD.TPS')
        dataflow: Dataflow ID (e.g. 'DSD_LFS@DF_IALFS_INDIC')
        version: Version string (e.g. '1.0')
        key: Dimension filter key (dot-separated, use empty for wildcard)
        start_period: Start period filter (e.g. '2020')
        end_period: End period filter (e.g. '2024')

    Returns:
        Parsed JSON response dict
    """
    url = f"{BASE_URL}/{agency},{dataflow},{version}/{key}"
    params = {"format": "jsondata"}
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period

    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        if resp.status_code in (404, 422):
            return {"error": f"No data found for query: {key} (HTTP {resp.status_code})", "status": resp.status_code}
        raise
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "status": 0}


def _parse_series(data: dict) -> List[Dict]:
    """
    Parse SDMX JSON data response into a list of series with observations.

    Returns list of dicts with dimension labels and time-series observations.
    """
    if "error" in data:
        return [data]

    try:
        datasets = data["data"]["dataSets"]
        structures = data["data"]["structures"]
    except (KeyError, TypeError):
        return [{"error": "Unexpected API response format"}]

    if not datasets or not structures:
        return [{"error": "Empty response from API"}]

    ds = datasets[0]
    struct = structures[0]

    # Build dimension value lookups
    series_dims = struct.get("dimensions", {}).get("series", [])
    obs_dims = struct.get("dimensions", {}).get("observation", [])

    # Get time period values from observation dimension
    time_values = []
    for od in obs_dims:
        if od.get("id") == "TIME_PERIOD":
            time_values = [v["id"] for v in od.get("values", [])]
            break

    results = []
    for series_key, series_data in ds.get("series", {}).items():
        # Decode series dimensions
        parts = series_key.split(":")
        labels = {}
        for i, p in enumerate(parts):
            if i < len(series_dims):
                dim = series_dims[i]
                vals = dim.get("values", [])
                idx = int(p)
                if idx < len(vals):
                    labels[dim["id"]] = vals[idx]["id"]
                    # Also store human-readable name if available
                    name = vals[idx].get("name", vals[idx]["id"])
                    if name != vals[idx]["id"]:
                        labels[f"{dim['id']}_name"] = name

        # Parse observations
        observations = {}
        for obs_key, obs_val in series_data.get("observations", {}).items():
            idx = int(obs_key)
            period = time_values[idx] if idx < len(time_values) else str(idx)
            value = obs_val[0] if obs_val else None
            observations[period] = value

        # Sort by period
        sorted_obs = dict(sorted(observations.items()))

        results.append({
            "dimensions": labels,
            "observations": sorted_obs,
            "count": len(sorted_obs),
        })

    return results


def get_unemployment_rate(country: str = "USA", start_year: int = 2020,
                          end_year: Optional[int] = None,
                          frequency: str = "M",
                          seasonally_adjusted: bool = True) -> Dict:
    """
    Get unemployment rate for a country.

    Args:
        country: Country code or name (e.g. 'USA', 'GBR', 'Germany')
        start_year: Start year for data
        end_year: End year (default: current year)
        frequency: 'M' (monthly), 'Q' (quarterly), 'A' (annual)
        seasonally_adjusted: Whether to get seasonally adjusted data

    Returns:
        Dict with unemployment rate time series
    """
    cc = _resolve_country(country)
    end_year = end_year or datetime.now().year
    adj = "Y" if seasonally_adjusted else "N"

    agency, df, ver, ndims = DATAFLOWS["unemployment_indicators"]
    # Key: REF_AREA.MEASURE.UNIT_MEASURE.TRANSFORMATION.ADJUSTMENT.SEX.AGE.ACTIVITY.FREQ
    key = f"{cc}.UNE_LF_M.PT_LF_SUB._Z.{adj}._T.Y_GE15._Z.{frequency}"

    data = _fetch_sdmx(agency, df, ver, key, str(start_year), str(end_year))
    series = _parse_series(data)

    if not series or (len(series) == 1 and "error" in series[0]):
        # Fallback: broader age filter
        key = f"{cc}.UNE_LF_M" + "." * (ndims - 2) + frequency
        data = _fetch_sdmx(agency, df, ver, key, str(start_year), str(end_year))
        series = _parse_series(data)

    return {
        "indicator": "Unemployment Rate",
        "country": cc,
        "frequency": frequency,
        "seasonally_adjusted": seasonally_adjusted,
        "unit": "% of labour force",
        "series": series,
        "source": "OECD Labour Force Statistics",
    }


def get_employment_rate(country: str = "USA", start_year: int = 2020,
                        end_year: Optional[int] = None,
                        frequency: str = "A") -> Dict:
    """
    Get employment-to-population ratio for a country (working-age 15-64).

    Args:
        country: Country code or name
        start_year: Start year
        end_year: End year (default: current)
        frequency: 'M', 'Q', or 'A'

    Returns:
        Dict with employment rate time series
    """
    cc = _resolve_country(country)
    end_year = end_year or datetime.now().year

    agency, df, ver, ndims = DATAFLOWS["employment_levels"]
    # EMP_WAP = employment-to-population ratio
    key = f"{cc}.EMP_WAP.PT_WAP_SUB._Z.Y._T.Y15T64._Z.{frequency}"

    data = _fetch_sdmx(agency, df, ver, key, str(start_year), str(end_year))
    series = _parse_series(data)

    return {
        "indicator": "Employment Rate (15-64)",
        "country": cc,
        "frequency": frequency,
        "unit": "% of working-age population",
        "series": series,
        "source": "OECD Labour Force Statistics",
    }


def get_average_wages(country: str = "USA", start_year: int = 2015,
                      end_year: Optional[int] = None) -> Dict:
    """
    Get average annual wages (constant prices, national currency & USD PPP).

    Args:
        country: Country code or name
        start_year: Start year
        end_year: End year

    Returns:
        Dict with average wage time series
    """
    cc = _resolve_country(country)
    end_year = end_year or datetime.now().year

    agency, df, ver, ndims = DATAFLOWS["average_wages"]
    # Try broad key — dataflow structure varies
    key = _wildcard_key(cc, ndims)

    data = _fetch_sdmx(agency, df, ver, key, str(start_year), str(end_year))
    series = _parse_series(data)

    return {
        "indicator": "Average Annual Wages",
        "country": cc,
        "unit": "USD PPP / National Currency",
        "series": series,
        "source": "OECD Earnings Database",
    }


def get_gender_wage_gap(country: str = "USA", start_year: int = 2015,
                        end_year: Optional[int] = None) -> Dict:
    """
    Get gender wage gap (median earnings difference as % of male median).

    Args:
        country: Country code or name
        start_year: Start year
        end_year: End year

    Returns:
        Dict with gender wage gap time series
    """
    cc = _resolve_country(country)
    end_year = end_year or datetime.now().year

    agency, df, ver, ndims = DATAFLOWS["gender_wage_gap"]
    key = _wildcard_key(cc, ndims)

    data = _fetch_sdmx(agency, df, ver, key, str(start_year), str(end_year))
    series = _parse_series(data)

    return {
        "indicator": "Gender Wage Gap",
        "country": cc,
        "unit": "% difference (median earnings)",
        "series": series,
        "source": "OECD Earnings Database",
    }


def get_minimum_wages(country: str = "USA", start_year: int = 2015,
                      end_year: Optional[int] = None) -> Dict:
    """
    Get real minimum wages at constant prices (2022 USD PPP).

    Args:
        country: Country code or name
        start_year: Start year
        end_year: End year

    Returns:
        Dict with minimum wage time series
    """
    cc = _resolve_country(country)
    end_year = end_year or datetime.now().year

    agency, df, ver, ndims = DATAFLOWS["minimum_wages_real"]
    key = _wildcard_key(cc, ndims)

    data = _fetch_sdmx(agency, df, ver, key, str(start_year), str(end_year))
    series = _parse_series(data)

    return {
        "indicator": "Real Minimum Wages",
        "country": cc,
        "unit": "2022 USD PPP (constant prices)",
        "series": series,
        "source": "OECD Earnings Database",
    }


def get_hours_worked(country: str = "USA", start_year: int = 2015,
                     end_year: Optional[int] = None) -> Dict:
    """
    Get average annual hours actually worked per worker.

    Args:
        country: Country code or name
        start_year: Start year
        end_year: End year

    Returns:
        Dict with hours worked time series
    """
    cc = _resolve_country(country)
    end_year = end_year or datetime.now().year

    agency, df, ver, ndims = DATAFLOWS["hours_worked"]
    key = _wildcard_key(cc, ndims)

    data = _fetch_sdmx(agency, df, ver, key, str(start_year), str(end_year))
    series = _parse_series(data)

    return {
        "indicator": "Average Annual Hours Worked",
        "country": cc,
        "unit": "Hours per worker",
        "series": series,
        "source": "OECD Hours Worked Database",
    }


def get_labour_force_participation(country: str = "USA", start_year: int = 2020,
                                    end_year: Optional[int] = None,
                                    frequency: str = "A") -> Dict:
    """
    Get labour force participation rate (15-64 age group).

    Args:
        country: Country code or name
        start_year: Start year
        end_year: End year
        frequency: 'M', 'Q', or 'A'

    Returns:
        Dict with participation rate time series
    """
    cc = _resolve_country(country)
    end_year = end_year or datetime.now().year

    agency, df, ver, ndims = DATAFLOWS["employment_levels"]
    # LF participation = LF / WAP
    key = f"{cc}.LF.PS._Z.Y._T.Y15T64._Z.{frequency}"

    data = _fetch_sdmx(agency, df, ver, key, str(start_year), str(end_year))
    series = _parse_series(data)

    return {
        "indicator": "Labour Force Participation",
        "country": cc,
        "frequency": frequency,
        "unit": "Thousands / Rate",
        "series": series,
        "source": "OECD Labour Force Statistics",
    }


def get_trade_union_density(country: str = "USA", start_year: int = 2010,
                            end_year: Optional[int] = None) -> Dict:
    """
    Get trade union density (% of employees who are union members).

    Args:
        country: Country code or name
        start_year: Start year
        end_year: End year

    Returns:
        Dict with union density time series
    """
    cc = _resolve_country(country)
    end_year = end_year or datetime.now().year

    agency, df, ver, ndims = DATAFLOWS["trade_union_density"]
    key = _wildcard_key(cc, ndims)

    data = _fetch_sdmx(agency, df, ver, key, str(start_year), str(end_year))
    series = _parse_series(data)

    return {
        "indicator": "Trade Union Density",
        "country": cc,
        "unit": "% of employees",
        "series": series,
        "source": "OECD Trade Union Database",
    }


def compare_countries(countries: List[str], indicator: str = "unemployment",
                      start_year: int = 2020,
                      end_year: Optional[int] = None) -> Dict:
    """
    Compare a labour indicator across multiple countries.

    Args:
        countries: List of country codes/names (e.g. ['USA', 'GBR', 'DEU'])
        indicator: One of 'unemployment', 'employment', 'wages', 'hours'
        start_year: Start year
        end_year: End year

    Returns:
        Dict with comparison data for all countries
    """
    func_map = {
        "unemployment": get_unemployment_rate,
        "employment": get_employment_rate,
        "wages": get_average_wages,
        "hours": get_hours_worked,
    }

    if indicator not in func_map:
        return {"error": f"Unknown indicator '{indicator}'. Use: {list(func_map.keys())}"}

    func = func_map[indicator]
    results = {}
    for c in countries:
        try:
            results[_resolve_country(c)] = func(c, start_year, end_year)
        except Exception as e:
            results[_resolve_country(c)] = {"error": str(e)}

    return {
        "comparison": indicator,
        "countries": list(results.keys()),
        "data": results,
        "source": "OECD",
    }


def list_available_indicators() -> Dict:
    """
    List all available OECD labour indicators in this module.

    Returns:
        Dict with indicator names, descriptions, and dataflow IDs
    """
    return {
        "indicators": {
            "unemployment_rate": {
                "function": "get_unemployment_rate",
                "description": "Unemployment rate as % of labour force",
                "frequency": "Monthly / Quarterly / Annual",
                "dataflow": "DSD_LFS@DF_IALFS_INDIC",
            },
            "employment_rate": {
                "function": "get_employment_rate",
                "description": "Employment-to-population ratio (15-64)",
                "frequency": "Monthly / Quarterly / Annual",
                "dataflow": "DSD_LFS@DF_IALFS_INDIC",
            },
            "labour_force_participation": {
                "function": "get_labour_force_participation",
                "description": "Labour force participation rate (15-64)",
                "frequency": "Monthly / Quarterly / Annual",
                "dataflow": "DSD_LFS@DF_IALFS_INDIC",
            },
            "average_wages": {
                "function": "get_average_wages",
                "description": "Average annual wages in USD PPP",
                "frequency": "Annual",
                "dataflow": "DSD_EARNINGS@AV_AN_WAGE",
            },
            "gender_wage_gap": {
                "function": "get_gender_wage_gap",
                "description": "Gender wage gap (% difference in median earnings)",
                "frequency": "Annual",
                "dataflow": "DSD_EARNINGS@GENDER_WAGE_GAP",
            },
            "minimum_wages": {
                "function": "get_minimum_wages",
                "description": "Real minimum wages (2022 USD PPP)",
                "frequency": "Annual",
                "dataflow": "DSD_EARNINGS@RMW",
            },
            "hours_worked": {
                "function": "get_hours_worked",
                "description": "Average annual hours worked per worker",
                "frequency": "Annual",
                "dataflow": "DSD_HW@DF_AVG_ANN_HRS_WKD",
            },
            "trade_union_density": {
                "function": "get_trade_union_density",
                "description": "Trade union membership as % of employees",
                "frequency": "Annual",
                "dataflow": "DSD_TUD_CBC@DF_TUD",
            },
        },
        "compare_function": "compare_countries",
        "supported_countries": list(COUNTRY_CODES.keys()),
        "source": "OECD SDMX REST API (https://sdmx.oecd.org/public/rest/)",
    }


if __name__ == "__main__":
    print(json.dumps({
        "module": "oecd_labour_statistics_api",
        "status": "active",
        "source": "https://data.oecd.org/api/",
        "functions": 10,
        "indicators": list(list_available_indicators()["indicators"].keys()),
    }, indent=2))

#!/usr/bin/env python3
"""
ILOSTAT API — Global labor market statistics from the International Labour Organization.
Covers employment, unemployment, wages, labor force participation, and informal sector
data for 200+ countries via the ILO SDMX REST API (free, no API key required).

Source: https://ilostat.ilo.org/data/
Category: Labor & Demographics
Free tier: true - Unlimited access, no API key needed
Update frequency: quarterly
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional


BASE_URL = "https://sdmx.ilo.org/rest"
TIMEOUT = 30

# Key dataflow IDs for common indicators
DATAFLOWS = {
    "employment": "DF_EMP_TEMP_SEX_AGE_NB",
    "unemployment_rate": "DF_UNE_2EAP_SEX_AGE_RT",
    "labor_force": "DF_EAP_TEAP_SEX_AGE_NB",
    "labor_force_participation_rate": "DF_EAP_2WAP_SEX_AGE_RT",
    "population": "DF_CLD_TPOP_SEX_AGE_NB",
    "exchange_rate": "DF_CCF_XOXR_CUR_RT",
    "mean_weekly_earnings": "DF_EAR_INEE_NOC_NB",
}

# Common age group codes
AGE_GROUPS = {
    "total": "AGE_AGGREGATE_TOTAL",
    "15+": "AGE_YTHADULT_YGE15",
    "15-24": "AGE_YTHADULT_Y15-24",
    "25+": "AGE_YTHADULT_YGE25",
    "15-64": "AGE_YTHADULT_Y15-64",
    "youth": "AGE_YTHADULT_Y15-24",
    "adult": "AGE_YTHADULT_YGE25",
}

SEX_CODES = {
    "total": "SEX_T",
    "male": "SEX_M",
    "female": "SEX_F",
}


def _parse_sdmx_json(data: dict) -> List[Dict]:
    """
    Parse SDMX-JSON 2.0 response into a flat list of observation dicts.

    Args:
        data: Raw JSON response from ILOSTAT SDMX API.

    Returns:
        List of dicts with keys: country, indicator, sex, age, year, value, unit.
    """
    results = []
    try:
        dataset = data["data"]["dataSets"][0]
        structure = data["data"]["structures"][0]
        series_dims = structure["dimensions"].get("series", [])
        obs_dims = structure["dimensions"].get("observation", [])

        # Build lookup maps for dimension values
        series_lookup = []
        for dim in series_dims:
            series_lookup.append({
                "id": dim["id"],
                "values": {i: v for i, v in enumerate(dim.get("values", []))}
            })

        obs_lookup = []
        for dim in obs_dims:
            obs_lookup.append({
                "id": dim["id"],
                "values": {i: v for i, v in enumerate(dim.get("values", []))}
            })

        # Get unit info from series attributes
        unit = None
        series_attrs = structure.get("attributes", {}).get("series", [])
        for attr in series_attrs:
            if attr["id"] == "UNIT_MEASURE":
                vals = attr.get("values", [])
                if vals:
                    unit = vals[0].get("name", vals[0].get("id"))
                break

        for series_key, series_data in dataset.get("series", {}).items():
            # Parse series key "0:0:0:0:0" into dimension indices
            indices = [int(x) for x in series_key.split(":")]

            # Resolve series dimension values
            row_base = {}
            for i, idx in enumerate(indices):
                if i < len(series_lookup):
                    dim = series_lookup[i]
                    val = dim["values"].get(idx, {})
                    dim_id = dim["id"]
                    if dim_id == "REF_AREA":
                        row_base["country"] = val.get("id", "")
                        row_base["country_name"] = val.get("name", "")
                    elif dim_id == "MEASURE":
                        row_base["indicator"] = val.get("id", "")
                        row_base["indicator_name"] = val.get("name", "")
                    elif dim_id == "SEX":
                        row_base["sex"] = val.get("name", val.get("id", ""))
                    elif dim_id == "AGE":
                        row_base["age_group"] = val.get("name", val.get("id", ""))
                    elif dim_id == "FREQ":
                        row_base["frequency"] = val.get("id", "")

            if unit:
                row_base["unit"] = unit

            # Parse observations
            for obs_key, obs_vals in series_data.get("observations", {}).items():
                obs_idx = int(obs_key)
                row = dict(row_base)

                # Resolve observation dimensions (typically TIME_PERIOD)
                for j, obs_dim in enumerate(obs_lookup):
                    if obs_dim["id"] == "TIME_PERIOD":
                        time_val = obs_dim["values"].get(obs_idx, {})
                        row["year"] = time_val.get("id", "")

                # First element of obs_vals is always the value
                if obs_vals and obs_vals[0] is not None:
                    row["value"] = obs_vals[0]
                    results.append(row)

    except (KeyError, IndexError, TypeError):
        pass

    return results


def _fetch_data(dataflow: str, country: str = "", freq: str = "A",
                sex: str = "SEX_T", age: str = "", measure: str = "",
                start_period: str = "", end_period: str = "",
                last_n: int = 0) -> List[Dict]:
    """
    Fetch data from ILOSTAT SDMX API.

    Args:
        dataflow: Dataflow ID (e.g. 'DF_EMP_TEMP_SEX_AGE_NB').
        country: ISO3 country code (e.g. 'USA', 'GBR'). Empty = all.
        freq: Frequency code ('A'=annual, 'Q'=quarterly, 'M'=monthly).
        sex: Sex filter ('SEX_T', 'SEX_M', 'SEX_F').
        age: Age group code. Empty = wildcard.
        measure: Measure code. Empty = wildcard.
        start_period: Start year (e.g. '2010').
        end_period: End year (e.g. '2023').
        last_n: Return only last N observations per series.

    Returns:
        List of observation dicts.
    """
    # Build the key: REF_AREA.FREQ.MEASURE.SEX.AGE
    key = f"{country}.{freq}.{measure}.{sex}.{age}"
    url = f"{BASE_URL}/data/ILO,{dataflow},1.0/{key}"

    params = {"format": "jsondata"}
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period
    if last_n > 0:
        params["lastNObservations"] = str(last_n)

    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return _parse_sdmx_json(resp.json())
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 404:
            return []  # No data available for this query
        raise RuntimeError(f"ILOSTAT API error {resp.status_code}: {resp.text[:200]}") from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"ILOSTAT API request failed: {e}") from e


def get_unemployment_rate(country: str = "USA", sex: str = "total",
                          age: str = "15+", start_year: str = "",
                          end_year: str = "", last_n: int = 10) -> List[Dict]:
    """
    Get unemployment rate (% of labor force) by country.

    Args:
        country: ISO3 country code (e.g. 'USA', 'GBR', 'DEU').
        sex: 'total', 'male', or 'female'.
        age: Age group - 'total', '15+', '15-24', '25+', '15-64'.
        start_year: Start year filter (e.g. '2015').
        end_year: End year filter (e.g. '2023').
        last_n: Number of most recent observations (default 10).

    Returns:
        List of dicts with year, value (%), country, etc.

    Example:
        >>> get_unemployment_rate('USA', last_n=3)
        [{'country': 'USA', 'year': '2025', 'value': 4.198, ...}, ...]
    """
    sex_code = SEX_CODES.get(sex, sex)
    age_code = AGE_GROUPS.get(age, age)
    return _fetch_data(
        DATAFLOWS["unemployment_rate"],
        country=country, sex=sex_code, age=age_code,
        start_period=start_year, end_period=end_year, last_n=last_n
    )


def get_employment(country: str = "USA", sex: str = "total",
                   age: str = "total", start_year: str = "",
                   end_year: str = "", last_n: int = 10) -> List[Dict]:
    """
    Get total employment numbers (thousands) by country.

    Args:
        country: ISO3 country code.
        sex: 'total', 'male', or 'female'.
        age: Age group - 'total', '15+', '15-24', '25+'.
        start_year: Start year filter.
        end_year: End year filter.
        last_n: Number of most recent observations.

    Returns:
        List of dicts with year, value (thousands), country, etc.
    """
    sex_code = SEX_CODES.get(sex, sex)
    age_code = AGE_GROUPS.get(age, age)
    return _fetch_data(
        DATAFLOWS["employment"],
        country=country, sex=sex_code, age=age_code,
        start_period=start_year, end_period=end_year, last_n=last_n
    )


def get_labor_force_participation(country: str = "USA", sex: str = "total",
                                   age: str = "15+", start_year: str = "",
                                   end_year: str = "", last_n: int = 10) -> List[Dict]:
    """
    Get labor force participation rate (% of working-age population).

    Args:
        country: ISO3 country code.
        sex: 'total', 'male', or 'female'.
        age: Age group - '15+', '15-24', '25+', '15-64'.
        start_year: Start year filter.
        end_year: End year filter.
        last_n: Number of most recent observations.

    Returns:
        List of dicts with year, value (%), country, etc.
    """
    sex_code = SEX_CODES.get(sex, sex)
    age_code = AGE_GROUPS.get(age, age)
    return _fetch_data(
        DATAFLOWS["labor_force_participation_rate"],
        country=country, sex=sex_code, age=age_code,
        start_period=start_year, end_period=end_year, last_n=last_n
    )


def get_labor_force(country: str = "USA", sex: str = "total",
                    age: str = "total", start_year: str = "",
                    end_year: str = "", last_n: int = 10) -> List[Dict]:
    """
    Get labor force size (thousands) by country.

    Args:
        country: ISO3 country code.
        sex: 'total', 'male', or 'female'.
        age: Age group.
        start_year: Start year filter.
        end_year: End year filter.
        last_n: Number of most recent observations.

    Returns:
        List of dicts with year, value (thousands), country, etc.
    """
    sex_code = SEX_CODES.get(sex, sex)
    age_code = AGE_GROUPS.get(age, age)
    return _fetch_data(
        DATAFLOWS["labor_force"],
        country=country, sex=sex_code, age=age_code,
        start_period=start_year, end_period=end_year, last_n=last_n
    )


def get_population(country: str = "USA", sex: str = "total",
                   age: str = "total", last_n: int = 10) -> List[Dict]:
    """
    Get total population (thousands) by country.

    Args:
        country: ISO3 country code.
        sex: 'total', 'male', or 'female'.
        age: Age group.
        last_n: Number of most recent observations.

    Returns:
        List of dicts with year, value (thousands), country, etc.
    """
    sex_code = SEX_CODES.get(sex, sex)
    age_code = AGE_GROUPS.get(age, age)
    return _fetch_data(
        DATAFLOWS["population"],
        country=country, sex=sex_code, age=age_code, last_n=last_n
    )


def compare_countries(countries: List[str], indicator: str = "unemployment_rate",
                      sex: str = "total", age: str = "15+",
                      last_n: int = 5) -> Dict:
    """
    Compare an indicator across multiple countries.

    Args:
        countries: List of ISO3 country codes (e.g. ['USA', 'GBR', 'DEU']).
        indicator: One of 'unemployment_rate', 'employment',
                   'labor_force_participation_rate', 'labor_force', 'population'.
        sex: 'total', 'male', or 'female'.
        age: Age group code.
        last_n: Number of most recent observations per country.

    Returns:
        Dict mapping country code to list of observations.

    Example:
        >>> compare_countries(['USA', 'GBR', 'DEU'], 'unemployment_rate', last_n=3)
    """
    func_map = {
        "unemployment_rate": get_unemployment_rate,
        "employment": get_employment,
        "labor_force_participation_rate": get_labor_force_participation,
        "labor_force": get_labor_force,
        "population": get_population,
    }
    func = func_map.get(indicator)
    if not func:
        raise ValueError(f"Unknown indicator: {indicator}. Use one of: {list(func_map.keys())}")

    results = {}
    for c in countries:
        try:
            results[c] = func(country=c, sex=sex, age=age, last_n=last_n)
        except Exception as e:
            results[c] = {"error": str(e)}
    return results


def list_available_dataflows(search: str = "") -> List[Dict]:
    """
    List available ILOSTAT dataflows (datasets).

    Args:
        search: Optional search term to filter dataflow names.

    Returns:
        List of dicts with id, name, description for each dataflow.
    """
    url = f"{BASE_URL}/dataflow/ILO"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        text = resp.text

        # Parse XML for dataflow IDs and names
        import re
        flows = []
        # Extract dataflow blocks
        pattern = r'<structure:Dataflow id="([^"]+)"[^>]*>.*?<common:Name xml:lang="en">([^<]+)</common:Name>'
        for match in re.finditer(pattern, text, re.DOTALL):
            flow_id, name = match.group(1), match.group(2)
            if search and search.lower() not in name.lower() and search.lower() not in flow_id.lower():
                continue
            flows.append({"id": flow_id, "name": name})

        return flows

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to list dataflows: {e}") from e


def get_country_data_summary(country: str = "USA", last_n: int = 3) -> Dict:
    """
    Get a summary of key labor indicators for a country.

    Args:
        country: ISO3 country code.
        last_n: Number of recent observations per indicator.

    Returns:
        Dict with keys: unemployment_rate, employment, labor_force_participation,
        each containing recent data points.
    """
    summary = {
        "country": country,
        "retrieved_at": datetime.utcnow().isoformat(),
        "indicators": {}
    }

    indicators = {
        "unemployment_rate": get_unemployment_rate,
        "employment": get_employment,
        "labor_force_participation": get_labor_force_participation,
    }

    for name, func in indicators.items():
        try:
            data = func(country=country, last_n=last_n)
            summary["indicators"][name] = data
        except Exception as e:
            summary["indicators"][name] = {"error": str(e)}

    return summary


def fetch_raw(dataflow: str, key: str = "", start_period: str = "",
              end_period: str = "", last_n: int = 10) -> List[Dict]:
    """
    Fetch raw data from any ILOSTAT dataflow.

    Args:
        dataflow: Full dataflow ID (e.g. 'DF_EMP_TEMP_SEX_AGE_NB').
        key: SDMX key filter (e.g. 'USA.A..SEX_T.AGE_AGGREGATE_TOTAL').
        start_period: Start period filter.
        end_period: End period filter.
        last_n: Number of most recent observations.

    Returns:
        List of parsed observation dicts.
    """
    url = f"{BASE_URL}/data/ILO,{dataflow},1.0/{key}"
    params = {"format": "jsondata"}
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period
    if last_n > 0:
        params["lastNObservations"] = str(last_n)

    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return _parse_sdmx_json(resp.json())
    except requests.exceptions.HTTPError:
        if resp.status_code == 404:
            return []
        raise
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"ILOSTAT API request failed: {e}") from e


if __name__ == "__main__":
    # Quick test
    print("=== USA Unemployment Rate (last 3 years) ===")
    data = get_unemployment_rate("USA", last_n=3)
    print(json.dumps(data, indent=2))

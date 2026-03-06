#!/usr/bin/env python3
"""oecd_cli — OECD Composite Leading Indicators. Source: https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_CLI. Free."""
import requests
import json
import os
import time
from datetime import datetime
import pandas as pd
import io

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# Map common ticker-style country codes to ISO 3-letter
COUNTRY_MAP = {
    "USA": "USA", "US": "USA", "GBR": "GBR", "UK": "GBR", "GB": "GBR",
    "DEU": "DEU", "DE": "DEU", "FRA": "FRA", "FR": "FRA",
    "JPN": "JPN", "JP": "JPN", "CHN": "CHN", "CN": "CHN",
    "CAN": "CAN", "CA": "CAN", "AUS": "AUS", "AU": "AUS",
    "ITA": "ITA", "IT": "ITA", "ESP": "ESP", "ES": "ESP",
    "KOR": "KOR", "KR": "KOR", "BRA": "BRA", "BR": "BRA",
    "IND": "IND", "IN": "IND", "MEX": "MEX", "MX": "MEX",
}

def get_data(ticker="USA", **kwargs):
    """
    Fetch OECD CLI (Composite Leading Indicator) data.
    ticker: country code e.g. 'USA', 'GBR', 'DEU'.
    Returns DataFrame with TIME_PERIOD, OBS_VALUE, COUNTRY columns.
    """
    country = COUNTRY_MAP.get(ticker.upper(), ticker.upper())
    module_name = __name__.split('.')[-1]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{country}.json")

    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400 * 7:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    try:
        url = (
            "https://sdmx.oecd.org/public/rest/data/"
            "OECD.SDD.STES,DSD_STES@DF_CLI,/all"
            "?startPeriod=2010-01&format=csvfilewithlabels"
        )
        resp = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()

        df = pd.read_csv(io.StringIO(resp.text))

        # Filter to monthly CLI amplitude-adjusted index
        mask = (
            (df['FREQ'] == 'M') &
            (df['MEASURE'].isin(['CLI', 'BCICP'])) &
            (df['TRANSFORMATION'] == 'IX')
        )
        df = df[mask][['REF_AREA', 'Reference area', 'TIME_PERIOD', 'OBS_VALUE']].copy()
        df.columns = ['COUNTRY_CODE', 'COUNTRY', 'TIME_PERIOD', 'OBS_VALUE']

        # Filter to requested country
        country_df = df[df['COUNTRY_CODE'] == country].copy()
        if country_df.empty:
            # Try matching on country name
            country_df = df[df['COUNTRY'].str.upper().str.contains(country)].copy()

        if country_df.empty:
            return pd.DataFrame({"error": [f"No CLI data found for {ticker}"]})

        country_df['TIME_PERIOD'] = pd.to_datetime(country_df['TIME_PERIOD'])
        country_df['OBS_VALUE'] = pd.to_numeric(country_df['OBS_VALUE'], errors='coerce')
        country_df = country_df.sort_values('TIME_PERIOD').reset_index(drop=True)
        country_df['fetch_time'] = datetime.now().isoformat()

        cache_data = country_df.to_dict('records')
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, default=str)
        return country_df

    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "USA"
    result = get_data(ticker)
    print(result.to_json(orient='records', date_format='iso'))

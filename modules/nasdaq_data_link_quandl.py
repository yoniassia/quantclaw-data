"""
Nasdaq Data Link (Quandl) — Free Economic & Financial Datasets

Data Source: Nasdaq Data Link (formerly Quandl)
API Docs: https://docs.data.nasdaq.com/docs/getting-started
Update: Daily (most datasets)
Free: Yes — free datasets available without API key (rate-limited to ~50/day)
         With free API key: higher limits on free datasets

Provides:
- Time-series dataset fetching (any database/dataset code)
- Free economic data (FRED via Quandl mirror, ECB, etc.)
- CFTC Commitment of Traders data
- Dataset metadata and search
- Emerging market indicators
- Commodity futures data

Popular FREE databases:
- FRED: US Federal Reserve Economic Data
- ECB: European Central Bank
- CFTC: Commitment of Traders
- USTREASURY: US Treasury Yield Curve
- ODA: IMF Cross Country Macro (Open Data for Africa)
- WORLDBANK: World Bank Global Development Indicators
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

BASE_URL = "https://data.nasdaq.com/api/v3"

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/nasdaq_data_link")
os.makedirs(CACHE_DIR, exist_ok=True)

# Well-known FREE datasets for quick access
FREE_DATASETS = {
    # US Treasury
    "us_yield_curve": ("USTREASURY", "YIELD"),
    "us_real_yield": ("USTREASURY", "REALYIELD"),
    "us_bills": ("USTREASURY", "BILLRATES"),
    # FRED popular series (mirrored on Nasdaq Data Link)
    "fed_funds_rate": ("FRED", "FEDFUNDS"),
    "us_gdp": ("FRED", "GDP"),
    "us_cpi": ("FRED", "CPIAUCSL"),
    "us_unemployment": ("FRED", "UNRATE"),
    "us_m2_money": ("FRED", "M2SL"),
    "us_industrial_production": ("FRED", "INDPRO"),
    "us_retail_sales": ("FRED", "RSXFS"),
    "us_housing_starts": ("FRED", "HOUST"),
    "us_10y_treasury": ("FRED", "DGS10"),
    "us_2y_treasury": ("FRED", "DGS2"),
    "us_30y_mortgage": ("FRED", "MORTGAGE30US"),
    # ECB
    "ecb_deposit_rate": ("ECB", "FM_M_U2_EUR_4F_MM_EONIA_HSTA"),
    # Commodities
    "gold_london_fix": ("LBMA", "GOLD"),
    "silver_london_fix": ("LBMA", "SILVER"),
    # Emerging markets (ODA - IMF Open Data for Africa)
    "brazil_gdp": ("ODA", "BRA_NGDPD"),
    "india_gdp": ("ODA", "IND_NGDPD"),
    "china_gdp": ("ODA", "CHN_NGDPD"),
    "brazil_inflation": ("ODA", "BRA_PCPIPCH"),
    "india_inflation": ("ODA", "IND_PCPIPCH"),
    "china_inflation": ("ODA", "CHN_PCPIPCH"),
    # CFTC
    "cftc_gold_futures": ("CFTC", "088691_FO_ALL"),
    "cftc_crude_oil": ("CFTC", "067651_FO_ALL"),
}


def _get_api_key() -> Optional[str]:
    """
    Try to load Nasdaq Data Link API key from environment or config file.
    Returns None if not found (still works for many free datasets).
    """
    key = os.environ.get("NASDAQ_DATA_LINK_API_KEY") or os.environ.get("QUANDL_API_KEY")
    if key:
        return key

    key_file = os.path.expanduser("~/.quantclaw/keys/nasdaq_data_link.key")
    if os.path.exists(key_file):
        with open(key_file) as f:
            return f.read().strip()

    return None


def _cache_path(name: str) -> str:
    """Generate cache file path for a given dataset name."""
    safe = name.replace("/", "_").replace("\\", "_")
    return os.path.join(CACHE_DIR, f"{safe}.json")


def _read_cache(name: str, max_age_hours: int = 12) -> Optional[dict]:
    """Read from cache if fresh enough."""
    path = _cache_path(name)
    if not os.path.exists(path):
        return None
    age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
    if age > timedelta(hours=max_age_hours):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _write_cache(name: str, data: dict) -> None:
    """Write data to cache."""
    try:
        with open(_cache_path(name), "w") as f:
            json.dump(data, f, indent=2, default=str)
    except IOError:
        pass


def get_dataset(database_code: str, dataset_code: str,
                start_date: Optional[str] = None,
                end_date: Optional[str] = None,
                limit: Optional[int] = None,
                order: str = "desc",
                column_index: Optional[int] = None,
                collapse: Optional[str] = None,
                transform: Optional[str] = None) -> Dict:
    """
    Fetch a time-series dataset from Nasdaq Data Link.

    Args:
        database_code: Database code (e.g., 'FRED', 'USTREASURY', 'ODA')
        dataset_code: Dataset code within the database (e.g., 'GDP', 'YIELD')
        start_date: Start date 'YYYY-MM-DD' (optional)
        end_date: End date 'YYYY-MM-DD' (optional)
        limit: Max number of rows to return (optional)
        order: 'asc' or 'desc' (default: desc = most recent first)
        column_index: Return only specific column (1-indexed, optional)
        collapse: Frequency collapse: 'daily','weekly','monthly','quarterly','annual'
        transform: Data transform: 'diff','rdiff','rdiff_from','cumul','normalize'

    Returns:
        dict with keys: name, description, column_names, data, frequency,
                        newest_date, oldest_date, database_code, dataset_code
    """
    cache_key = f"{database_code}_{dataset_code}_{start_date}_{end_date}_{limit}_{collapse}"
    cached = _read_cache(cache_key)
    if cached:
        return cached

    url = f"{BASE_URL}/datasets/{database_code}/{dataset_code}.json"
    params = {"order": order}

    api_key = _get_api_key()
    if api_key:
        params["api_key"] = api_key

    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if limit:
        params["limit"] = limit
    if column_index is not None:
        params["column_index"] = column_index
    if collapse:
        params["collapse"] = collapse
    if transform:
        params["transform"] = transform

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        raw = resp.json()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        if status == 404:
            return {"error": f"Dataset {database_code}/{dataset_code} not found", "status": 404}
        if status == 429:
            return {"error": "Rate limit exceeded. Consider adding an API key.", "status": 429}
        if status == 403:
            return {"error": "Premium dataset — requires subscription", "status": 403}
        return {"error": str(e), "status": status}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

    ds = raw.get("dataset", {})
    result = {
        "name": ds.get("name", ""),
        "description": ds.get("description", "")[:500],
        "database_code": ds.get("database_code", database_code),
        "dataset_code": ds.get("dataset_code", dataset_code),
        "frequency": ds.get("frequency", ""),
        "column_names": ds.get("column_names", []),
        "newest_date": ds.get("newest_available_date", ""),
        "oldest_date": ds.get("oldest_available_date", ""),
        "data": ds.get("data", []),
        "row_count": len(ds.get("data", [])),
        "fetched_at": datetime.now().isoformat(),
    }

    _write_cache(cache_key, result)
    return result


def get_dataset_metadata(database_code: str, dataset_code: str) -> Dict:
    """
    Fetch metadata only (no data) for a dataset.

    Args:
        database_code: Database code
        dataset_code: Dataset code

    Returns:
        dict with name, description, frequency, column_names, date range, premium flag
    """
    url = f"{BASE_URL}/datasets/{database_code}/{dataset_code}/metadata.json"
    params = {}
    api_key = _get_api_key()
    if api_key:
        params["api_key"] = api_key

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        raw = resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

    ds = raw.get("dataset", {})
    return {
        "name": ds.get("name", ""),
        "description": ds.get("description", "")[:500],
        "database_code": ds.get("database_code", ""),
        "dataset_code": ds.get("dataset_code", ""),
        "frequency": ds.get("frequency", ""),
        "type": ds.get("type", ""),
        "premium": ds.get("premium", False),
        "column_names": ds.get("column_names", []),
        "newest_date": ds.get("newest_available_date", ""),
        "oldest_date": ds.get("oldest_available_date", ""),
    }


def search_datasets(query: str, database_code: Optional[str] = None,
                     page: int = 1, per_page: int = 10) -> List[Dict]:
    """
    Search for datasets on Nasdaq Data Link.

    Args:
        query: Search query string
        database_code: Restrict search to a specific database (optional)
        page: Page number (default 1)
        per_page: Results per page (default 10, max 100)

    Returns:
        List of dicts with id, name, database_code, dataset_code, description, frequency, premium
    """
    url = f"{BASE_URL}/datasets.json"
    params = {"query": query, "page": page, "per_page": per_page}

    if database_code:
        params["database_code"] = database_code

    api_key = _get_api_key()
    if api_key:
        params["api_key"] = api_key

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        raw = resp.json()
    except requests.exceptions.RequestException as e:
        return [{"error": str(e)}]

    results = []
    for ds in raw.get("datasets", []):
        results.append({
            "name": ds.get("name", ""),
            "database_code": ds.get("database_code", ""),
            "dataset_code": ds.get("dataset_code", ""),
            "description": (ds.get("description") or "")[:200],
            "frequency": ds.get("frequency", ""),
            "premium": ds.get("premium", False),
            "newest_date": ds.get("newest_available_date", ""),
        })

    return results


def get_quick(indicator: str, limit: int = 10) -> Dict:
    """
    Quick access to popular free datasets by friendly name.

    Args:
        indicator: One of the keys from FREE_DATASETS, e.g.:
            'us_gdp', 'fed_funds_rate', 'us_cpi', 'us_unemployment',
            'us_yield_curve', 'gold_london_fix', 'brazil_gdp',
            'india_gdp', 'china_gdp', 'brazil_inflation', etc.
        limit: Number of data points to return (default 10)

    Returns:
        dict with dataset info and data rows.
        Use list_indicators() to see all available shortcuts.
    """
    if indicator not in FREE_DATASETS:
        return {
            "error": f"Unknown indicator '{indicator}'",
            "available": list(FREE_DATASETS.keys()),
        }

    db, ds = FREE_DATASETS[indicator]
    return get_dataset(db, ds, limit=limit)


def list_indicators() -> Dict[str, str]:
    """
    List all available quick-access indicator names and their dataset codes.

    Returns:
        dict mapping indicator name → 'DATABASE/DATASET' string
    """
    return {k: f"{v[0]}/{v[1]}" for k, v in FREE_DATASETS.items()}


def get_us_yield_curve(limit: int = 30) -> Dict:
    """
    Fetch US Treasury Yield Curve rates.

    Returns daily yields for 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y.

    Args:
        limit: Number of trading days to return (default 30)

    Returns:
        dict with column_names and data rows (most recent first)
    """
    return get_dataset("USTREASURY", "YIELD", limit=limit)


def get_fred_series(series_code: str, start_date: Optional[str] = None,
                     limit: int = 50, collapse: Optional[str] = None) -> Dict:
    """
    Fetch a FRED series from Nasdaq Data Link's FRED mirror.

    Popular series codes:
        GDP, CPIAUCSL, UNRATE, FEDFUNDS, M2SL, DGS10, DGS2,
        MORTGAGE30US, INDPRO, RSXFS, HOUST, PAYEMS, T10YIE

    Args:
        series_code: FRED series code (e.g., 'GDP', 'UNRATE')
        start_date: Start date 'YYYY-MM-DD' (optional)
        limit: Max rows (default 50)
        collapse: Frequency: 'monthly', 'quarterly', 'annual' (optional)

    Returns:
        dict with FRED series data
    """
    return get_dataset("FRED", series_code, start_date=start_date,
                       limit=limit, collapse=collapse)


def get_emerging_market_data(country_code: str, indicator: str = "NGDPD",
                              limit: int = 20) -> Dict:
    """
    Fetch emerging market macro indicators from IMF Open Data (ODA database).

    Args:
        country_code: 3-letter ISO code: BRA (Brazil), IND (India), CHN (China),
                      RUS (Russia), ZAF (South Africa), MEX (Mexico), IDN (Indonesia)
        indicator: IMF indicator code:
            NGDPD = GDP (current USD billions)
            NGDPDPC = GDP per capita
            PCPIPCH = Inflation (CPI % change)
            LUR = Unemployment rate
            BCA = Current account balance
            GGXWDG_NGDP = Gov debt (% of GDP)
        limit: Number of data points (default 20)

    Returns:
        dict with macro data for the country
    """
    dataset_code = f"{country_code}_{indicator}"
    return get_dataset("ODA", dataset_code, limit=limit)


def get_commodity_data(commodity: str = "gold", limit: int = 30) -> Dict:
    """
    Fetch London precious metals fixing prices.

    Args:
        commodity: 'gold' or 'silver'
        limit: Number of data points (default 30)

    Returns:
        dict with daily price fixing data
    """
    code_map = {"gold": "GOLD", "silver": "SILVER"}
    dataset = code_map.get(commodity.lower())
    if not dataset:
        return {"error": f"Unknown commodity '{commodity}'. Use 'gold' or 'silver'."}
    return get_dataset("LBMA", dataset, limit=limit)


def compare_indicators(indicators: List[str], limit: int = 10) -> List[Dict]:
    """
    Fetch multiple quick indicators side-by-side for comparison.

    Args:
        indicators: List of indicator names from FREE_DATASETS
        limit: Data points per indicator (default 10)

    Returns:
        List of dataset results, one per indicator
    """
    results = []
    for ind in indicators:
        data = get_quick(ind, limit=limit)
        data["indicator_key"] = ind
        results.append(data)
    return results


if __name__ == "__main__":
    print(json.dumps({
        "module": "nasdaq_data_link_quandl",
        "status": "ready",
        "source": "https://data.nasdaq.com/docs",
        "functions": [
            "get_dataset", "get_dataset_metadata", "search_datasets",
            "get_quick", "list_indicators", "get_us_yield_curve",
            "get_fred_series", "get_emerging_market_data",
            "get_commodity_data", "compare_indicators"
        ],
        "free_indicators": len(FREE_DATASETS),
    }, indent=2))

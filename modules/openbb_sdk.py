"""
OpenBB SDK — Unified Financial Data Access (Lightweight)

Provides OpenBB-style unified access to free financial data sources without
requiring the full openbb pip package or paid API keys. Wraps the same free
data providers that OpenBB Platform aggregates:

- SEC EDGAR: Company filings, insider trades, institutional holdings
- FRED (no key): Select economic indicators via alternative endpoints
- EconDB: Macro indicators (no key required)
- OECD: International economic data
- SEC Company Search & CIK resolution

Source: https://docs.openbb.co/
Category: Quant Tools & ML
Free tier: True (all endpoints used are free/no-key)
Update frequency: real-time/daily
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/openbb_sdk")
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "QuantClaw/1.0 (quant data platform; support@moneyclaw.com)",
    "Accept": "application/json",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cache_get(key: str, max_age_hours: int = 24) -> Optional[Any]:
    """Read from disk cache if fresh enough."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(path):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
        if age < timedelta(hours=max_age_hours):
            with open(path) as f:
                return json.load(f)
    return None


def _cache_set(key: str, data: Any) -> None:
    """Write to disk cache."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _get(url: str, params: Optional[dict] = None, timeout: int = 15) -> requests.Response:
    """GET with standard headers and timeout."""
    return requests.get(url, headers=HEADERS, params=params, timeout=timeout)


# ---------------------------------------------------------------------------
# SEC EDGAR — Company Filings & Data
# ---------------------------------------------------------------------------

def sec_cik_lookup(ticker: str) -> Dict:
    """
    Resolve a stock ticker to its SEC CIK number.

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL')

    Returns:
        dict with cik, name, ticker
    """
    cache_key = f"cik_{ticker.upper()}"
    cached = _cache_get(cache_key, max_age_hours=168)  # CIKs don't change
    if cached:
        return cached

    url = "https://efts.sec.gov/LATEST/search-index?q=%22{}%22&dateRange=custom&startdt=2020-01-01&enddt=2026-12-31&forms=10-K" .format(ticker.upper())
    # Better approach: use the company tickers JSON
    tickers_url = "https://www.sec.gov/files/company_tickers.json"
    try:
        resp = _get(tickers_url)
        resp.raise_for_status()
        data = resp.json()
        for entry in data.values():
            if entry.get("ticker", "").upper() == ticker.upper():
                result = {
                    "cik": str(entry["cik_str"]).zfill(10),
                    "cik_raw": entry["cik_str"],
                    "name": entry["title"],
                    "ticker": entry["ticker"],
                    "source": "sec_edgar",
                }
                _cache_set(cache_key, result)
                return result
        return {"error": f"Ticker {ticker} not found in SEC database"}
    except Exception as e:
        return {"error": str(e), "source": "sec_edgar"}


def sec_company_filings(ticker: str, filing_type: str = "10-K", limit: int = 5) -> List[Dict]:
    """
    Get recent SEC filings for a company.

    Args:
        ticker: Stock ticker (e.g. 'AAPL')
        filing_type: Filing type filter (10-K, 10-Q, 8-K, etc.)
        limit: Max filings to return

    Returns:
        List of filing dicts with date, type, url, description
    """
    cik_data = sec_cik_lookup(ticker)
    if "error" in cik_data:
        return [cik_data]

    cik = cik_data["cik"]
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        resp = _get(url)
        resp.raise_for_status()
        data = resp.json()

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        descriptions = recent.get("primaryDocDescription", [])
        docs = recent.get("primaryDocument", [])

        results = []
        for i, form in enumerate(forms):
            if filing_type and form != filing_type:
                continue
            if len(results) >= limit:
                break
            acc_clean = accessions[i].replace("-", "")
            results.append({
                "form": form,
                "date": dates[i],
                "description": descriptions[i] if i < len(descriptions) else "",
                "url": f"https://www.sec.gov/Archives/edgar/data/{cik_data['cik_raw']}/{acc_clean}/{docs[i]}",
                "accession": accessions[i],
            })

        return results if results else [{"info": f"No {filing_type} filings found for {ticker}"}]
    except Exception as e:
        return [{"error": str(e)}]


def sec_insider_trades(ticker: str, limit: int = 10) -> List[Dict]:
    """
    Get recent insider trades (Form 4) for a company via SEC EDGAR.

    Args:
        ticker: Stock ticker (e.g. 'AAPL')
        limit: Max results

    Returns:
        List of insider trade filings
    """
    return sec_company_filings(ticker, filing_type="4", limit=limit)


def sec_company_facts(ticker: str) -> Dict:
    """
    Get structured company financial facts from SEC XBRL data.
    Includes revenue, net income, assets, etc. across all reported periods.

    Args:
        ticker: Stock ticker (e.g. 'AAPL')

    Returns:
        dict with company facts summary (latest values for key metrics)
    """
    cik_data = sec_cik_lookup(ticker)
    if "error" in cik_data:
        return cik_data

    cik = cik_data["cik"]
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

    cache_key = f"facts_{ticker.upper()}"
    cached = _cache_get(cache_key, max_age_hours=24)
    if cached:
        return cached

    try:
        resp = _get(url)
        resp.raise_for_status()
        data = resp.json()

        us_gaap = data.get("facts", {}).get("us-gaap", {})

        # Extract latest values for key metrics
        key_metrics = [
            "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
            "NetIncomeLoss", "Assets", "Liabilities",
            "StockholdersEquity", "EarningsPerShareBasic",
            "EarningsPerShareDiluted", "OperatingIncomeLoss",
            "CashAndCashEquivalentsAtCarryingValue",
        ]

        summary = {
            "company": cik_data["name"],
            "ticker": ticker.upper(),
            "cik": cik,
            "metrics": {},
            "source": "sec_xbrl",
        }

        for metric in key_metrics:
            if metric in us_gaap:
                units = us_gaap[metric].get("units", {})
                # Get USD values (or shares for EPS)
                for unit_key in ["USD", "USD/shares"]:
                    if unit_key in units:
                        entries = units[unit_key]
                        # Get most recent 10-K entry
                        annual = [e for e in entries if e.get("form") == "10-K"]
                        if annual:
                            latest = sorted(annual, key=lambda x: x.get("end", ""))[-1]
                            summary["metrics"][metric] = {
                                "value": latest["val"],
                                "unit": unit_key,
                                "period_end": latest.get("end"),
                                "filed": latest.get("filed"),
                            }
                        break

        _cache_set(cache_key, summary)
        return summary
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# World Bank — Macro Economic Indicators (No API Key)
# ---------------------------------------------------------------------------

# Common World Bank indicator codes
WB_INDICATORS = {
    "gdp": "NY.GDP.MKTP.CD",           # GDP (current US$)
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",  # GDP growth (annual %)
    "gdp_per_capita": "NY.GDP.PCAP.CD",  # GDP per capita (current US$)
    "cpi": "FP.CPI.TOTL.ZG",            # Inflation, consumer prices (annual %)
    "unemployment": "SL.UEM.TOTL.ZS",    # Unemployment (% of labor force)
    "population": "SP.POP.TOTL",         # Population, total
    "trade_pct_gdp": "NE.TRD.GNFS.ZS",  # Trade (% of GDP)
    "interest_rate": "FR.INR.RINR",      # Real interest rate (%)
    "fdi": "BX.KLT.DINV.WD.GD.ZS",      # FDI net inflows (% of GDP)
    "govt_debt": "GC.DOD.TOTL.GD.ZS",   # Central govt debt (% of GDP)
    "current_account": "BN.CAB.XOKA.GD.ZS",  # Current account (% of GDP)
    "exports": "NE.EXP.GNFS.CD",        # Exports (current US$)
}


def worldbank_indicator(indicator: str, country: str = "US",
                        years: int = 10) -> Dict:
    """
    Fetch a World Bank economic indicator. No API key required.

    Args:
        indicator: WB indicator code (e.g. 'NY.GDP.MKTP.CD') or
                   shorthand key from WB_INDICATORS (e.g. 'gdp', 'cpi')
        country: 2-letter ISO country code (US, GB, DE, JP, CN, etc.)
        years: Number of years of history

    Returns:
        dict with indicator metadata and recent values
    """
    # Resolve shorthand
    code = WB_INDICATORS.get(indicator.lower(), indicator)
    cache_key = f"wb_{code}_{country}"
    cached = _cache_get(cache_key, max_age_hours=24)
    if cached:
        return cached

    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{code}"
    params = {"format": "json", "per_page": years, "mrv": years}

    try:
        resp = _get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        if len(data) < 2 or not data[1]:
            return {"error": f"No data for {code} / {country}", "source": "worldbank"}

        meta = data[0]
        records = data[1]

        values = []
        for rec in records:
            if rec.get("value") is not None:
                values.append({
                    "year": rec["date"],
                    "value": rec["value"],
                })

        result = {
            "indicator": code,
            "indicator_name": records[0].get("indicator", {}).get("value", ""),
            "country": records[0].get("country", {}).get("value", ""),
            "country_code": country.upper(),
            "total_records": meta.get("total", 0),
            "recent_values": sorted(values, key=lambda x: x["year"]),
            "source": "worldbank",
        }

        _cache_set(cache_key, result)
        return result
    except Exception as e:
        return {"error": str(e), "indicator": code, "source": "worldbank"}


def worldbank_search(query: str, limit: int = 10) -> List[Dict]:
    """
    Search World Bank indicators by keyword.

    Args:
        query: Search term (e.g. 'GDP', 'inflation', 'unemployment')
        limit: Max results

    Returns:
        List of matching indicators
    """
    url = "https://api.worldbank.org/v2/indicator"
    params = {"format": "json", "per_page": limit, "source": "2"}

    try:
        resp = _get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        if len(data) < 2:
            return [{"error": "No results"}]

        results = []
        query_lower = query.lower()
        for item in data[1]:
            name = item.get("name", "")
            if query_lower in name.lower() or query_lower in item.get("id", "").lower():
                results.append({
                    "id": item.get("id", ""),
                    "name": name,
                    "source": item.get("source", {}).get("value", ""),
                    "topic": item.get("topics", [{}])[0].get("value", "") if item.get("topics") else "",
                })
                if len(results) >= limit:
                    break

        # If filtering returned nothing, return all
        if not results:
            for item in data[1][:limit]:
                results.append({
                    "id": item.get("id", ""),
                    "name": item.get("name", ""),
                    "source": item.get("source", {}).get("value", ""),
                })

        return results
    except Exception as e:
        return [{"error": str(e)}]


# ---------------------------------------------------------------------------
# OECD — International Economic Data (No API Key)
# ---------------------------------------------------------------------------

def oecd_indicator(dataset: str = "QNA", country: str = "USA",
                   subject: str = "B1_GE", measure: str = "GPSA",
                   frequency: str = "Q", limit: int = 20) -> Dict:
    """
    Fetch OECD economic indicator data.

    Common datasets:
        QNA = Quarterly National Accounts (GDP)
        PRICES_CPI = Consumer Prices
        KEI = Key Economic Indicators
        STLABOUR = Short-Term Labour Market

    Args:
        dataset: OECD dataset code
        country: 3-letter country code (USA, GBR, DEU, JPN, etc.)
        subject: Subject/variable code (B1_GE=GDP, CPALTT01=CPI)
        measure: Measure code (GPSA=growth rate seasonally adjusted)
        frequency: Q=quarterly, M=monthly, A=annual
        limit: Recent periods to return

    Returns:
        dict with indicator values
    """
    cache_key = f"oecd_{dataset}_{country}_{subject}_{frequency}"
    cached = _cache_get(cache_key, max_age_hours=24)
    if cached:
        return cached

    # OECD SDMX JSON API
    url = f"https://sdmx.oecd.org/public/rest/data/OECD.SDD.SNAS,DSD_NAMAIN10@DF_QNA_EXPENDITURE_CAPITA/{country}.{frequency}.{subject}.{measure}"
    # Simpler approach: use the stats.oecd.org JSON endpoint
    url2 = f"https://stats.oecd.org/SDMX-JSON/data/{dataset}/{country}.{subject}.{measure}.{frequency}/all"

    try:
        resp = _get(url2, params={"lastNObservations": limit})
        if resp.status_code != 200:
            # Fallback to newer API
            resp = _get(url, params={"lastNObservations": limit, "format": "jsondata"})

        resp.raise_for_status()
        data = resp.json()

        # Parse SDMX-JSON structure
        observations = {}
        structure = data.get("structure", data.get("data", {}))
        datasets = data.get("dataSets", [])

        if datasets:
            series_data = datasets[0].get("series", {})
            for series_key, series_val in series_data.items():
                obs = series_val.get("observations", {})
                for period_idx, values in obs.items():
                    observations[period_idx] = values[0] if values else None

        result = {
            "dataset": dataset,
            "country": country,
            "subject": subject,
            "measure": measure,
            "frequency": frequency,
            "observations": observations,
            "count": len(observations),
            "source": "oecd",
        }

        if observations:
            _cache_set(cache_key, result)
        return result
    except Exception as e:
        return {"error": str(e), "source": "oecd", "dataset": dataset}


# ---------------------------------------------------------------------------
# SEC Full-Text Search (EFTS)
# ---------------------------------------------------------------------------

def sec_full_text_search(query: str, forms: str = "10-K,10-Q",
                         date_start: str = "2024-01-01",
                         limit: int = 10) -> List[Dict]:
    """
    Full-text search across all SEC EDGAR filings.

    Args:
        query: Search term (company name, keyword, etc.)
        forms: Comma-separated form types to search
        date_start: Start date (YYYY-MM-DD)
        limit: Max results

    Returns:
        List of matching filings
    """
    url = "https://efts.sec.gov/LATEST/search-index"
    params = {
        "q": query,
        "forms": forms,
        "dateRange": "custom",
        "startdt": date_start,
        "enddt": datetime.now().strftime("%Y-%m-%d"),
    }

    try:
        resp = _get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for hit in data.get("hits", {}).get("hits", [])[:limit]:
            src = hit.get("_source", {})
            results.append({
                "entity": src.get("entity_name", ""),
                "form": src.get("form_type", ""),
                "date": src.get("file_date", ""),
                "description": src.get("display_names", [""])[0] if src.get("display_names") else "",
                "url": f"https://www.sec.gov/Archives/edgar/data/{src.get('entity_id', '')}/{src.get('file_num', '')}",
            })
        return results if results else [{"info": f"No filings found for '{query}'"}]
    except Exception as e:
        return [{"error": str(e)}]


# ---------------------------------------------------------------------------
# Convenience / Unified Functions
# ---------------------------------------------------------------------------

def get_company_overview(ticker: str) -> Dict:
    """
    Get a comprehensive company overview combining SEC data.
    Unified view of filings, financial facts, and insider activity.

    Args:
        ticker: Stock ticker (e.g. 'AAPL')

    Returns:
        dict with company overview
    """
    facts = sec_company_facts(ticker)
    recent_10k = sec_company_filings(ticker, "10-K", limit=3)
    recent_10q = sec_company_filings(ticker, "10-Q", limit=3)
    insider = sec_insider_trades(ticker, limit=5)

    return {
        "ticker": ticker.upper(),
        "company": facts.get("company", ""),
        "financial_facts": facts.get("metrics", {}),
        "recent_annual_filings": recent_10k,
        "recent_quarterly_filings": recent_10q,
        "recent_insider_filings": insider,
        "source": "openbb_sdk_module",
        "retrieved_at": datetime.now().isoformat(),
    }


def get_macro_snapshot(country: str = "US") -> Dict:
    """
    Get a macro economic snapshot for a country using World Bank data.

    Args:
        country: 2-letter country code (US, GB, DE, JP, CN, etc.)

    Returns:
        dict with key macro indicators and their latest values
    """
    indicator_keys = ["gdp", "gdp_growth", "gdp_per_capita", "cpi",
                      "unemployment", "population", "trade_pct_gdp"]

    snapshot = {
        "country": country.upper(),
        "indicators": {},
        "retrieved_at": datetime.now().isoformat(),
        "source": "worldbank",
    }

    for key in indicator_keys:
        data = worldbank_indicator(key, country, years=5)
        if "error" not in data and data.get("recent_values"):
            latest = data["recent_values"][-1]
            snapshot["indicators"][key] = {
                "name": data.get("indicator_name", ""),
                "latest_value": latest.get("value"),
                "latest_year": latest.get("year"),
            }
        else:
            snapshot["indicators"][key] = {
                "status": "unavailable",
                "detail": data.get("error", ""),
            }

    return snapshot


if __name__ == "__main__":
    print(json.dumps({
        "module": "openbb_sdk",
        "status": "active",
        "source": "https://docs.openbb.co/",
        "functions": [
            "sec_cik_lookup", "sec_company_filings", "sec_insider_trades",
            "sec_company_facts", "sec_full_text_search",
            "worldbank_indicator", "worldbank_search",
            "oecd_indicator",
            "get_company_overview", "get_macro_snapshot",
        ],
    }, indent=2))

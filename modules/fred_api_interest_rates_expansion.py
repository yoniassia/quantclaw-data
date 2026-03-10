#!/usr/bin/env python3
"""
FRED API Interest Rates Expansion — Central Bank Rates, Treasury Yields & Carry Trade Analytics

Expanded interest rate module focusing on:
- Global central bank policy rates (Fed, ECB, BoE, BoJ, BoC, RBA, SNB)
- Full US Treasury yield curve (1m to 30y)
- Real yields (TIPS) and breakeven inflation
- Yield curve slope & inversion signals
- Carry trade rate differentials
- Interest rate regime detection
- Historical rate comparisons

Complements: fred_interest_rates_expansion.py (swap rates, forward rates)
Complements: fred_api.py (corporate bonds, credit spreads)

Source: https://fred.stlouisfed.org/docs/api/fred.html
Category: FX & Rates
Free tier: True (FRED_API_KEY env var, free registration)
Update frequency: Daily for most series
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# ============================================================
# Configuration
# ============================================================

FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

CACHE_DIR = Path.home() / ".quantclaw" / "cache" / "fred_rates_expansion"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CACHE_TTL_HOURS = 4  # 4-hour cache for rate data

# ============================================================
# Series Registries
# ============================================================

# US Treasury Yield Curve — nominal constant maturity
US_TREASURY_SERIES = {
    "1M":  "DGS1MO",
    "3M":  "DGS3MO",
    "6M":  "DGS6MO",
    "1Y":  "DGS1",
    "2Y":  "DGS2",
    "3Y":  "DGS3",
    "5Y":  "DGS5",
    "7Y":  "DGS7",
    "10Y": "DGS10",
    "20Y": "DGS20",
    "30Y": "DGS30",
}

# TIPS (Real Yields)
TIPS_SERIES = {
    "5Y":  "DFII5",
    "7Y":  "DFII7",
    "10Y": "DFII10",
    "20Y": "DFII20",
    "30Y": "DFII30",
}

# Breakeven Inflation Rates
BREAKEVEN_SERIES = {
    "5Y":  "T5YIE",
    "10Y": "T10YIE",
    "30Y": "T30YIEM",  # 30-year monthly
}

# Central Bank Policy Rates
CENTRAL_BANK_RATES = {
    "US_FED_UPPER":   "DFEDTARU",   # Fed Funds Target Upper
    "US_FED_LOWER":   "DFEDTARL",   # Fed Funds Target Lower
    "US_FED_EFF":     "DFF",        # Effective Fed Funds Rate
    "ECB_MAIN":       "ECBMRRFR",   # ECB Main Refinancing Rate
    "ECB_DEPOSIT":    "ECBDFR",     # ECB Deposit Facility Rate
    "UK_BOE":         "IUDSOIA",    # BoE Official Bank Rate (daily SONIA)
    "JAPAN_BOJ":      "IRSTCB01JPM156N",  # BoJ policy rate (monthly)
    "CANADA_BOC":     "IRSTCB01CAM156N",  # BoC rate (monthly)
    "AUSTRALIA_RBA":  "IRSTCB01AUM156N",  # RBA rate (monthly)
    "SWITZERLAND_SNB":"IRSTCB01CHM156N",  # SNB rate (monthly)
}

# Key benchmark rates
BENCHMARK_RATES = {
    "SOFR":           "SOFR",       # Secured Overnight Financing Rate
    "PRIME":          "DPRIME",     # US Prime Rate
    "DISCOUNT":       "DPCREDIT",   # Discount Window Primary Credit Rate
    "MORTGAGE_30Y":   "MORTGAGE30US",  # 30-Year Fixed Rate Mortgage
    "MORTGAGE_15Y":   "MORTGAGE15US",  # 15-Year Fixed Rate Mortgage
}


# ============================================================
# Core API Helpers
# ============================================================

def _fred_get(endpoint: str, params: dict) -> dict:
    """
    Make a FRED API request with standard params.

    Args:
        endpoint: API endpoint path (e.g., 'series/observations')
        params: Query parameters

    Returns:
        JSON response as dict

    Raises:
        requests.HTTPError: On API error
        ValueError: If no API key configured
    """
    if not FRED_API_KEY:
        raise ValueError(
            "FRED_API_KEY not set. Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html"
        )
    params["api_key"] = FRED_API_KEY
    params["file_type"] = "json"
    url = f"{FRED_BASE_URL}/{endpoint}"
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _get_series_observations(
    series_id: str,
    limit: int = 10,
    sort_order: str = "desc",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict]:
    """
    Fetch observations for a FRED series.

    Args:
        series_id: FRED series ID
        limit: Max observations to return
        sort_order: 'asc' or 'desc'
        start_date: YYYY-MM-DD start
        end_date: YYYY-MM-DD end

    Returns:
        List of {'date': str, 'value': float} dicts (missing values filtered)
    """
    params = {
        "series_id": series_id,
        "limit": limit,
        "sort_order": sort_order,
    }
    if start_date:
        params["observation_start"] = start_date
    if end_date:
        params["observation_end"] = end_date

    data = _fred_get("series/observations", params)
    observations = []
    for obs in data.get("observations", []):
        val = obs.get("value", ".")
        if val != ".":
            try:
                observations.append({
                    "date": obs["date"],
                    "value": float(val),
                })
            except (ValueError, TypeError):
                continue
    return observations


def _cached_fetch(cache_key: str, fetcher, ttl_hours: int = CACHE_TTL_HOURS):
    """Simple file-based cache wrapper."""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if age < timedelta(hours=ttl_hours):
            with open(cache_file) as f:
                return json.load(f)
    result = fetcher()
    with open(cache_file, "w") as f:
        json.dump(result, f, indent=2, default=str)
    return result


# ============================================================
# Public Functions
# ============================================================

def get_interest_rates() -> Dict:
    """
    Get current key US interest rates snapshot.

    Returns:
        Dict with fed_funds, sofr, prime, discount, mortgage rates and metadata.

    Example:
        >>> data = get_interest_rates()
        >>> print(data['fed_funds_effective'])
        {'date': '2026-03-06', 'value': 4.33}
    """
    def _fetch():
        rates = {}

        # Fed Funds
        for key, series_id in [
            ("fed_funds_upper", "DFEDTARU"),
            ("fed_funds_lower", "DFEDTARL"),
            ("fed_funds_effective", "DFF"),
        ]:
            obs = _get_series_observations(series_id, limit=1)
            rates[key] = obs[0] if obs else None

        # Benchmark rates
        for key, series_id in BENCHMARK_RATES.items():
            obs = _get_series_observations(series_id, limit=1)
            rates[key.lower()] = obs[0] if obs else None

        rates["_meta"] = {
            "source": "FRED (Federal Reserve Economic Data)",
            "fetched_at": datetime.utcnow().isoformat(),
            "description": "Key US interest rates snapshot",
        }
        return rates

    return _cached_fetch("interest_rates_snapshot", _fetch)


def get_treasury_yields(maturities: Optional[List[str]] = None) -> Dict:
    """
    Get current US Treasury yields across the curve.

    Args:
        maturities: List of maturities to fetch (e.g., ['2Y', '10Y', '30Y']).
                    If None, fetches all available maturities.

    Returns:
        Dict mapping maturity labels to latest yield observations.

    Example:
        >>> yields = get_treasury_yields(['2Y', '10Y'])
        >>> print(yields['10Y'])
        {'date': '2026-03-06', 'value': 4.25}
    """
    targets = maturities or list(US_TREASURY_SERIES.keys())

    def _fetch():
        result = {}
        for mat in targets:
            series_id = US_TREASURY_SERIES.get(mat)
            if not series_id:
                result[mat] = {"error": f"Unknown maturity: {mat}"}
                continue
            obs = _get_series_observations(series_id, limit=1)
            result[mat] = obs[0] if obs else None
        result["_meta"] = {
            "source": "FRED US Treasury Constant Maturity",
            "fetched_at": datetime.utcnow().isoformat(),
        }
        return result

    cache_key = "treasury_yields_" + "_".join(sorted(targets))
    return _cached_fetch(cache_key, _fetch)


def get_yield_curve() -> Dict:
    """
    Build the full US Treasury yield curve with slope metrics.

    Returns:
        Dict with 'curve' (maturity→yield), 'slope_2s10s', 'slope_3m10y',
        'inverted' flag, and metadata.

    Example:
        >>> yc = get_yield_curve()
        >>> print(yc['slope_2s10s'])
        -0.15
    """
    def _fetch():
        curve = {}
        for mat, series_id in US_TREASURY_SERIES.items():
            obs = _get_series_observations(series_id, limit=1)
            if obs:
                curve[mat] = obs[0]["value"]

        # Slope calculations
        slope_2s10s = None
        slope_3m10y = None
        if "2Y" in curve and "10Y" in curve:
            slope_2s10s = round(curve["10Y"] - curve["2Y"], 4)
        if "3M" in curve and "10Y" in curve:
            slope_3m10y = round(curve["10Y"] - curve["3M"], 4)

        inverted = False
        if slope_2s10s is not None and slope_2s10s < 0:
            inverted = True
        if slope_3m10y is not None and slope_3m10y < 0:
            inverted = True

        return {
            "curve": curve,
            "slope_2s10s": slope_2s10s,
            "slope_3m10y": slope_3m10y,
            "inverted": inverted,
            "_meta": {
                "source": "FRED US Treasury Constant Maturity",
                "fetched_at": datetime.utcnow().isoformat(),
                "description": "Full yield curve with inversion detection",
            },
        }

    return _cached_fetch("yield_curve_full", _fetch)


def get_real_yields(maturities: Optional[List[str]] = None) -> Dict:
    """
    Get TIPS (real) yields and breakeven inflation rates.

    Args:
        maturities: List like ['5Y', '10Y', '30Y']. None = all.

    Returns:
        Dict with 'real_yields', 'breakeven_inflation', and 'inflation_premium' per maturity.
    """
    targets = maturities or ["5Y", "10Y", "30Y"]

    def _fetch():
        result = {"real_yields": {}, "breakeven_inflation": {}, "inflation_premium": {}}
        for mat in targets:
            # TIPS real yield
            tips_id = TIPS_SERIES.get(mat)
            if tips_id:
                obs = _get_series_observations(tips_id, limit=1)
                result["real_yields"][mat] = obs[0] if obs else None

            # Breakeven
            be_id = BREAKEVEN_SERIES.get(mat)
            if be_id:
                obs = _get_series_observations(be_id, limit=1)
                result["breakeven_inflation"][mat] = obs[0] if obs else None

            # Inflation premium = nominal - real
            nom_id = US_TREASURY_SERIES.get(mat)
            if nom_id and tips_id:
                nom_obs = _get_series_observations(nom_id, limit=1)
                tips_obs = _get_series_observations(tips_id, limit=1)
                if nom_obs and tips_obs:
                    premium = round(nom_obs[0]["value"] - tips_obs[0]["value"], 4)
                    result["inflation_premium"][mat] = {
                        "date": nom_obs[0]["date"],
                        "value": premium,
                    }

        result["_meta"] = {
            "source": "FRED TIPS & Breakeven Inflation",
            "fetched_at": datetime.utcnow().isoformat(),
        }
        return result

    cache_key = "real_yields_" + "_".join(sorted(targets))
    return _cached_fetch(cache_key, _fetch)


def get_central_bank_rates(countries: Optional[List[str]] = None) -> Dict:
    """
    Get latest central bank policy rates across major economies.

    Args:
        countries: Filter list, e.g. ['US', 'ECB', 'UK']. None = all.
                   Keys match CENTRAL_BANK_RATES prefixes.

    Returns:
        Dict mapping rate names to latest observations.

    Example:
        >>> rates = get_central_bank_rates(['US'])
        >>> print(rates['US_FED_EFF'])
        {'date': '2026-03-06', 'value': 4.33}
    """
    def _fetch():
        result = {}
        for name, series_id in CENTRAL_BANK_RATES.items():
            if countries:
                prefix = name.split("_")[0]
                if prefix not in countries and name not in countries:
                    # Also try matching country part like "US" from "US_FED_UPPER"
                    if not any(name.startswith(c) for c in countries):
                        continue
            obs = _get_series_observations(series_id, limit=1)
            result[name] = obs[0] if obs else None
        result["_meta"] = {
            "source": "FRED Central Bank Policy Rates",
            "fetched_at": datetime.utcnow().isoformat(),
        }
        return result

    cache_key = "central_bank_" + ("_".join(sorted(countries)) if countries else "all")
    return _cached_fetch(cache_key, _fetch)


def get_rate_differential(country_a: str = "US", country_b: str = "ECB") -> Dict:
    """
    Calculate interest rate differential between two central banks (carry trade signal).

    Args:
        country_a: First country key (e.g., 'US')
        country_b: Second country key (e.g., 'ECB', 'UK', 'JAPAN')

    Returns:
        Dict with rate_a, rate_b, differential, carry_direction.
    """
    # Map country short codes to their effective rate series
    country_to_series = {
        "US":          "DFF",
        "ECB":         "ECBDFR",
        "UK":          "IUDSOIA",
        "JAPAN":       "IRSTCB01JPM156N",
        "CANADA":      "IRSTCB01CAM156N",
        "AUSTRALIA":   "IRSTCB01AUM156N",
        "SWITZERLAND": "IRSTCB01CHM156N",
    }

    series_a = country_to_series.get(country_a.upper())
    series_b = country_to_series.get(country_b.upper())
    if not series_a:
        return {"error": f"Unknown country: {country_a}. Valid: {list(country_to_series.keys())}"}
    if not series_b:
        return {"error": f"Unknown country: {country_b}. Valid: {list(country_to_series.keys())}"}

    obs_a = _get_series_observations(series_a, limit=1)
    obs_b = _get_series_observations(series_b, limit=1)

    if not obs_a or not obs_b:
        return {"error": "Could not fetch rates for one or both countries"}

    rate_a = obs_a[0]["value"]
    rate_b = obs_b[0]["value"]
    diff = round(rate_a - rate_b, 4)

    return {
        "country_a": country_a.upper(),
        "rate_a": rate_a,
        "rate_a_date": obs_a[0]["date"],
        "country_b": country_b.upper(),
        "rate_b": rate_b,
        "rate_b_date": obs_b[0]["date"],
        "differential": diff,
        "carry_direction": f"Long {country_a.upper()} / Short {country_b.upper()}" if diff > 0
                          else f"Long {country_b.upper()} / Short {country_a.upper()}",
        "_meta": {
            "source": "FRED",
            "description": "Rate differential for carry trade analysis",
            "fetched_at": datetime.utcnow().isoformat(),
        },
    }


def get_rate_history(
    series_id: str,
    start_date: str = "2020-01-01",
    end_date: Optional[str] = None,
    limit: int = 500,
) -> Dict:
    """
    Get historical observations for any FRED rate series.

    Args:
        series_id: FRED series ID (e.g., 'DGS10', 'DFF')
        start_date: Start date YYYY-MM-DD
        end_date: End date YYYY-MM-DD (default: today)
        limit: Max observations

    Returns:
        Dict with 'series_id', 'observations' list, 'stats' (min/max/avg/latest).
    """
    end_date = end_date or datetime.utcnow().strftime("%Y-%m-%d")
    obs = _get_series_observations(
        series_id, limit=limit, sort_order="asc",
        start_date=start_date, end_date=end_date,
    )
    if not obs:
        return {"series_id": series_id, "observations": [], "stats": None}

    values = [o["value"] for o in obs]
    stats = {
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "avg": round(sum(values) / len(values), 4),
        "latest": obs[-1],
        "count": len(obs),
        "start": obs[0]["date"],
        "end": obs[-1]["date"],
    }
    return {
        "series_id": series_id,
        "observations": obs,
        "stats": stats,
        "_meta": {
            "source": "FRED",
            "fetched_at": datetime.utcnow().isoformat(),
        },
    }


def get_rate_regime() -> Dict:
    """
    Classify the current interest rate environment/regime.

    Returns:
        Dict with regime classification, supporting indicators, and yield curve status.

    Regimes: 'tightening', 'easing', 'neutral', 'crisis'
    """
    def _fetch():
        # Get Fed Funds rate + 6-month history
        ff_hist = _get_series_observations("DFF", limit=130, sort_order="desc")
        if not ff_hist:
            return {"error": "Could not fetch Fed Funds data"}

        current = ff_hist[0]["value"]
        # ~6 months ago
        past = ff_hist[-1]["value"] if len(ff_hist) > 120 else ff_hist[-1]["value"]

        # Yield curve
        obs_2y = _get_series_observations("DGS2", limit=1)
        obs_10y = _get_series_observations("DGS10", limit=1)
        slope = None
        if obs_2y and obs_10y:
            slope = round(obs_10y[0]["value"] - obs_2y[0]["value"], 4)

        # VIX-like stress? Use TEDRATE as proxy
        ted_obs = _get_series_observations("TEDRATE", limit=1)
        ted_rate = ted_obs[0]["value"] if ted_obs else None

        # Regime classification
        rate_change = round(current - past, 4)
        if rate_change > 0.5:
            regime = "tightening"
        elif rate_change < -0.5:
            regime = "easing"
        elif ted_rate and ted_rate > 1.0:
            regime = "crisis"
        else:
            regime = "neutral"

        return {
            "regime": regime,
            "fed_funds_current": current,
            "fed_funds_6m_ago": past,
            "rate_change_6m": rate_change,
            "yield_curve_2s10s": slope,
            "curve_inverted": slope is not None and slope < 0,
            "ted_spread": ted_rate,
            "_meta": {
                "source": "FRED",
                "fetched_at": datetime.utcnow().isoformat(),
                "description": "Interest rate regime classification",
            },
        }

    return _cached_fetch("rate_regime", _fetch)


def get_mortgage_rates() -> Dict:
    """
    Get current US mortgage rates (30Y and 15Y fixed).

    Returns:
        Dict with mortgage_30y, mortgage_15y, spread_to_10y.
    """
    def _fetch():
        m30 = _get_series_observations("MORTGAGE30US", limit=1)
        m15 = _get_series_observations("MORTGAGE15US", limit=1)
        t10 = _get_series_observations("DGS10", limit=1)

        spread = None
        if m30 and t10:
            spread = round(m30[0]["value"] - t10[0]["value"], 4)

        return {
            "mortgage_30y": m30[0] if m30 else None,
            "mortgage_15y": m15[0] if m15 else None,
            "treasury_10y": t10[0] if t10 else None,
            "spread_30y_to_10y": spread,
            "_meta": {
                "source": "FRED (Freddie Mac Primary Mortgage Survey)",
                "fetched_at": datetime.utcnow().isoformat(),
            },
        }

    return _cached_fetch("mortgage_rates", _fetch)


def get_sofr_rate(history_days: int = 30) -> Dict:
    """
    Get SOFR (Secured Overnight Financing Rate) with recent history.

    Args:
        history_days: Number of days of history (default 30).

    Returns:
        Dict with current rate, history, and stats.
    """
    start = (datetime.utcnow() - timedelta(days=history_days + 10)).strftime("%Y-%m-%d")
    obs = _get_series_observations("SOFR", limit=history_days, sort_order="desc", start_date=start)
    if not obs:
        return {"error": "Could not fetch SOFR data"}

    values = [o["value"] for o in obs]
    return {
        "current": obs[0],
        "history": obs[:10],  # Last 10 for summary
        "stats": {
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "avg": round(sum(values) / len(values), 4),
            "count": len(obs),
        },
        "_meta": {
            "source": "FRED SOFR",
            "fetched_at": datetime.utcnow().isoformat(),
        },
    }


def search_fred_series(query: str, limit: int = 10) -> List[Dict]:
    """
    Search FRED for series matching a query.

    Args:
        query: Search text (e.g., 'interest rate brazil')
        limit: Max results

    Returns:
        List of dicts with series_id, title, frequency, units, last_updated.
    """
    data = _fred_get("series/search", {
        "search_text": query,
        "limit": limit,
        "order_by": "popularity",
        "sort_order": "desc",
    })
    results = []
    for s in data.get("seriess", []):
        results.append({
            "series_id": s.get("id"),
            "title": s.get("title"),
            "frequency": s.get("frequency"),
            "units": s.get("units"),
            "last_updated": s.get("last_updated"),
            "popularity": s.get("popularity"),
        })
    return results


def list_available_series() -> Dict:
    """
    List all pre-configured FRED series available in this module.

    Returns:
        Dict mapping category names to their series registries.
    """
    return {
        "us_treasury_yields": US_TREASURY_SERIES,
        "tips_real_yields": TIPS_SERIES,
        "breakeven_inflation": BREAKEVEN_SERIES,
        "central_bank_rates": CENTRAL_BANK_RATES,
        "benchmark_rates": BENCHMARK_RATES,
    }


# ============================================================
# Module entry point
# ============================================================

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("=== Interest Rates Snapshot ===")
        rates = get_interest_rates()
        print(json.dumps(rates, indent=2, default=str))
        print("\n=== Treasury Yields (2Y, 10Y, 30Y) ===")
        yields = get_treasury_yields(["2Y", "10Y", "30Y"])
        print(json.dumps(yields, indent=2, default=str))
    else:
        print(json.dumps({
            "module": "fred_api_interest_rates_expansion",
            "status": "ready",
            "functions": 12,
            "source": "https://fred.stlouisfed.org/docs/api/fred.html",
        }, indent=2))

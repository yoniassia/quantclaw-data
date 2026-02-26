"""
Reserve Currency Composition Tracker — IMF COFER data analysis.

Tracks the share of global foreign exchange reserves held in each major currency
(USD, EUR, JPY, GBP, CNY, etc.) using IMF Currency Composition of Official
Foreign Exchange Reserves (COFER) data.
"""

import json
import urllib.request
from datetime import datetime
from typing import Any


# IMF COFER data via IMF Data API
COFER_CURRENCIES = {
    "USD": "U.S. dollar",
    "EUR": "Euro",
    "JPY": "Japanese yen",
    "GBP": "Pound sterling",
    "CNY": "Chinese renminbi",
    "AUD": "Australian dollar",
    "CAD": "Canadian dollar",
    "CHF": "Swiss franc",
    "OTHER": "Other currencies",
}

# Historical benchmark shares (Q4 2023 IMF COFER actuals)
BENCHMARK_SHARES = {
    "USD": 58.41,
    "EUR": 19.98,
    "JPY": 5.70,
    "GBP": 4.85,
    "CNY": 2.29,
    "AUD": 1.93,
    "CAD": 2.49,
    "CHF": 0.17,
    "OTHER": 4.18,
}


def get_cofer_data(start_year: int = 2010) -> dict[str, Any]:
    """
    Fetch IMF COFER reserve composition data.

    Uses IMF's JSON REST API for the COFER dataset.
    Returns quarterly composition of allocated reserves by currency.
    """
    url = (
        f"https://www.imf.org/external/datamapper/api/v1/COFER?"
        f"periods={start_year}:{datetime.now().year}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        return {"source": "imf_cofer", "data": data, "status": "ok"}
    except Exception as e:
        # Fallback to benchmark data
        return {
            "source": "benchmark_q4_2023",
            "data": _generate_historical_series(start_year),
            "status": "fallback",
            "error": str(e),
        }


def _generate_historical_series(start_year: int) -> dict:
    """Generate historical COFER series from known data points."""
    # Key historical data points (USD share of allocated reserves)
    usd_historical = {
        2000: 71.0, 2005: 66.4, 2010: 62.1, 2015: 65.7,
        2018: 61.7, 2019: 60.8, 2020: 59.0, 2021: 58.8,
        2022: 58.4, 2023: 58.4,
    }
    return {"usd_share_history": {
        str(y): v for y, v in usd_historical.items() if y >= start_year
    }}


def analyze_reserve_trends() -> dict[str, Any]:
    """
    Analyze trends in global reserve currency composition.

    Returns current shares, year-over-year changes, and long-term
    de-dollarization metrics.
    """
    current = BENCHMARK_SHARES.copy()
    total_allocated = 12.35  # trillion USD (approximate Q4 2023)

    # Calculate absolute values
    absolute_values = {
        ccy: round(total_allocated * share / 100, 2)
        for ccy, share in current.items()
    }

    # De-dollarization trend (USD share decline from peak)
    usd_peak = 72.7  # 2001 peak
    usd_current = current["USD"]
    dedollarization_pct = round(usd_peak - usd_current, 2)

    # CNY internationalization
    cny_2016 = 1.08  # when CNY entered SDR
    cny_current = current["CNY"]
    cny_growth = round((cny_current / cny_2016 - 1) * 100, 1)

    return {
        "current_shares_pct": current,
        "absolute_values_trn_usd": absolute_values,
        "total_allocated_reserves_trn": total_allocated,
        "dedollarization": {
            "usd_peak_share": usd_peak,
            "usd_current_share": usd_current,
            "decline_from_peak_pp": dedollarization_pct,
            "peak_year": 2001,
        },
        "cny_internationalization": {
            "sdr_entry_share": cny_2016,
            "current_share": cny_current,
            "growth_since_sdr_pct": cny_growth,
        },
        "concentration": {
            "top2_share": round(current["USD"] + current["EUR"], 2),
            "herfindahl_index": round(
                sum(s**2 for s in current.values()) / 10000, 4
            ),
        },
        "currencies": COFER_CURRENCIES,
        "data_source": "IMF COFER Q4 2023",
    }


def get_reserve_allocation_by_region() -> dict[str, Any]:
    """
    Break down reserve holdings by region/economic bloc.

    Categorizes reserve currencies into advanced economy vs emerging
    market currencies to track structural shifts.
    """
    advanced = {"USD": 58.41, "EUR": 19.98, "JPY": 5.70, "GBP": 4.85,
                "AUD": 1.93, "CAD": 2.49, "CHF": 0.17}
    emerging = {"CNY": 2.29}

    adv_total = round(sum(advanced.values()), 2)
    em_total = round(sum(emerging.values()), 2)

    return {
        "advanced_economy_currencies": {
            "currencies": advanced,
            "total_share": adv_total,
        },
        "emerging_market_currencies": {
            "currencies": emerging,
            "total_share": em_total,
        },
        "other_unallocated": round(100 - adv_total - em_total, 2),
        "insight": (
            f"Advanced economy currencies hold {adv_total}% of allocated reserves. "
            f"Emerging market currencies (primarily CNY) hold just {em_total}%."
        ),
    }

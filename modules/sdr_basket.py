"""
SDR Basket Analyzer — IMF Special Drawing Rights composition and valuation.

Analyzes the IMF's SDR basket composition, calculates theoretical SDR values,
tracks currency weight changes across quinquennial reviews, and monitors
SDR allocations to member countries.
"""

import json
import urllib.request
from datetime import datetime
from typing import Any


# SDR basket weights (effective August 1, 2022 — next review ~2027)
SDR_WEIGHTS = {
    "USD": {"weight": 43.38, "units": 0.57813, "name": "U.S. Dollar"},
    "EUR": {"weight": 29.31, "units": 0.37379, "name": "Euro"},
    "CNY": {"weight": 12.28, "units": 1.0993, "name": "Chinese Renminbi"},
    "JPY": {"weight": 7.59, "units": 11.900, "name": "Japanese Yen"},
    "GBP": {"weight": 7.44, "units": 0.080870, "name": "Pound Sterling"},
}

# Historical SDR weight evolution
WEIGHT_HISTORY = {
    "2016": {"USD": 41.73, "EUR": 30.93, "CNY": 10.92, "JPY": 8.33, "GBP": 8.09},
    "2022": {"USD": 43.38, "EUR": 29.31, "CNY": 12.28, "JPY": 7.59, "GBP": 7.44},
}

# Total SDR allocations (billions)
TOTAL_SDR_ALLOCATED = 660.7  # billion SDR (after Aug 2021 general allocation)


def get_sdr_composition() -> dict[str, Any]:
    """
    Return current SDR basket composition with weights and currency units.

    Shows the five currencies in the SDR basket, their percentage weights,
    and the fixed number of currency units per SDR.
    """
    return {
        "basket": SDR_WEIGHTS,
        "effective_date": "2022-08-01",
        "next_review": "2027 (approximate)",
        "total_currencies": len(SDR_WEIGHTS),
        "description": (
            "The SDR is an international reserve asset created by the IMF. "
            "Its value is based on a basket of five major currencies."
        ),
    }


def calculate_sdr_value(exchange_rates: dict[str, float] | None = None) -> dict[str, Any]:
    """
    Calculate the SDR value in USD given exchange rates.

    If no rates provided, fetches approximate current rates.
    The SDR value = sum of (currency units × exchange rate vs USD) for each component.

    Args:
        exchange_rates: Dict mapping currency to USD rate (e.g., {"EUR": 1.08}).
                       For JPY, provide USDJPY (e.g., 150.0).
    """
    if exchange_rates is None:
        exchange_rates = _fetch_approximate_rates()

    # Convert all to "per USD" for calculation
    contributions = {}
    total_usd = 0.0

    for ccy, info in SDR_WEIGHTS.items():
        units = info["units"]
        if ccy == "USD":
            usd_value = units
        elif ccy in ("JPY", "CNY"):
            # These are quoted as USDXXX, so divide
            rate = exchange_rates.get(ccy, 1.0)
            usd_value = units / rate if rate != 0 else 0
        else:
            # EUR, GBP quoted as XXXUSD
            rate = exchange_rates.get(ccy, 1.0)
            usd_value = units * rate

        contributions[ccy] = round(usd_value, 6)
        total_usd += usd_value

    return {
        "sdr_value_usd": round(total_usd, 6),
        "currency_contributions_usd": contributions,
        "exchange_rates_used": exchange_rates,
        "calculation_time": datetime.utcnow().isoformat(),
    }


def _fetch_approximate_rates() -> dict[str, float]:
    """Fetch approximate FX rates from a free API."""
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        rates = data.get("rates", {})
        return {
            "EUR": 1 / rates.get("EUR", 0.92),
            "GBP": 1 / rates.get("GBP", 0.79),
            "JPY": rates.get("JPY", 150.0),
            "CNY": rates.get("CNY", 7.25),
        }
    except Exception:
        return {"EUR": 1.08, "GBP": 1.27, "JPY": 150.0, "CNY": 7.25}


def analyze_sdr_weight_changes() -> dict[str, Any]:
    """
    Analyze how SDR basket weights have changed across reviews.

    Compares the 2016 and 2022 reviews, showing which currencies
    gained or lost weight in the basket.
    """
    changes = {}
    w2016 = WEIGHT_HISTORY["2016"]
    w2022 = WEIGHT_HISTORY["2022"]

    for ccy in w2022:
        old = w2016.get(ccy, 0)
        new = w2022[ccy]
        changes[ccy] = {
            "weight_2016": old,
            "weight_2022": new,
            "change_pp": round(new - old, 2),
            "direction": "increased" if new > old else "decreased",
        }

    return {
        "review_comparison": changes,
        "key_insight": (
            "USD and CNY weights increased in the 2022 review, "
            "while EUR, JPY, and GBP weights decreased."
        ),
        "total_sdr_allocated_bn": TOTAL_SDR_ALLOCATED,
        "aug_2021_allocation_bn": 456.5,  # largest ever general allocation
    }


def get_sdr_allocation_stats() -> dict[str, Any]:
    """
    Return statistics on SDR allocations to IMF member countries.
    """
    return {
        "total_allocated_bn_sdr": TOTAL_SDR_ALLOCATED,
        "approximate_usd_value_bn": round(TOTAL_SDR_ALLOCATED * 1.33, 1),
        "member_countries": 190,
        "general_allocations": [
            {"year": 1970, "amount_bn": 9.3},
            {"year": 1979, "amount_bn": 12.1},
            {"year": 2009, "amount_bn": 182.6},
            {"year": 2021, "amount_bn": 456.5},
        ],
        "largest_holders": [
            {"country": "United States", "share_pct": 17.4},
            {"country": "Japan", "share_pct": 6.5},
            {"country": "China", "share_pct": 6.4},
            {"country": "Germany", "share_pct": 5.6},
            {"country": "France", "share_pct": 4.2},
            {"country": "United Kingdom", "share_pct": 4.2},
        ],
    }

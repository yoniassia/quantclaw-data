"""
Live Forex Cross Rates Matrix — 150+ currency pairs.

Builds a cross-rate matrix for major and exotic currencies,
computes triangular arbitrage opportunities, and tracks
carry trade differentials. Uses free FX data sources.
"""

import json
import urllib.request
from datetime import datetime
from itertools import combinations
from typing import Any

MAJOR_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD"]
EM_CURRENCIES = ["BRL", "MXN", "ZAR", "TRY", "INR", "CNY", "KRW", "SGD", "HKD", "SEK", "NOK", "PLN"]


def get_exchange_rates(base: str = "USD", currencies: list[str] | None = None) -> dict[str, Any]:
    """Fetch current exchange rates from free API."""
    if currencies is None:
        currencies = MAJOR_CURRENCIES + EM_CURRENCIES
    url = f"https://open.er-api.com/v6/latest/{base}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        rates = {k: v for k, v in data.get("rates", {}).items() if k in currencies or k == base}
        rates[base] = 1.0
        return {
            "base": base,
            "rates": rates,
            "pairs_count": len(rates),
            "timestamp": data.get("time_last_update_utc", datetime.utcnow().isoformat())
        }
    except Exception as e:
        return {"base": base, "error": str(e)}


def build_cross_rate_matrix(currencies: list[str] | None = None) -> dict[str, Any]:
    """Build NxN cross-rate matrix for given currencies."""
    if currencies is None:
        currencies = MAJOR_CURRENCIES
    data = get_exchange_rates("USD", currencies)
    if "error" in data:
        return data

    rates = data["rates"]
    matrix = {}
    for base in currencies:
        if base not in rates:
            continue
        row = {}
        for quote in currencies:
            if quote not in rates:
                continue
            if base == quote:
                row[quote] = 1.0
            else:
                row[quote] = round(rates[quote] / rates[base], 6)
        matrix[base] = row

    return {
        "currencies": currencies,
        "matrix": matrix,
        "pairs_count": len(currencies) * (len(currencies) - 1),
        "timestamp": datetime.utcnow().isoformat()
    }


def find_triangular_arbitrage(currencies: list[str] | None = None, threshold_pct: float = 0.1) -> list[dict[str, Any]]:
    """Detect triangular arbitrage opportunities across currency triples."""
    if currencies is None:
        currencies = MAJOR_CURRENCIES
    cross = build_cross_rate_matrix(currencies)
    if "error" in cross:
        return []

    matrix = cross["matrix"]
    opportunities = []

    for a, b, c in combinations(currencies, 3):
        if a not in matrix or b not in matrix or c not in matrix:
            continue
        try:
            rate_ab = matrix[a].get(b, 0)
            rate_bc = matrix[b].get(c, 0)
            rate_ca = matrix[c].get(a, 0)
            if rate_ab == 0 or rate_bc == 0 or rate_ca == 0:
                continue
            product = rate_ab * rate_bc * rate_ca
            profit_pct = (product - 1) * 100
            if abs(profit_pct) > threshold_pct:
                opportunities.append({
                    "triangle": f"{a}->{b}->{c}->{a}",
                    "product": round(product, 6),
                    "profit_pct": round(profit_pct, 4),
                    "rates": {"ab": rate_ab, "bc": rate_bc, "ca": rate_ca}
                })
        except (KeyError, ZeroDivisionError):
            continue

    opportunities.sort(key=lambda x: abs(x["profit_pct"]), reverse=True)
    return opportunities[:10]


def get_carry_trade_pairs() -> list[dict[str, Any]]:
    """Estimate carry trade attractiveness based on rate differentials."""
    # Approximate central bank rates (updated periodically)
    policy_rates = {
        "USD": 5.25, "EUR": 4.50, "GBP": 5.25, "JPY": 0.25,
        "CHF": 1.50, "AUD": 4.35, "CAD": 5.00, "NZD": 5.50,
        "BRL": 10.50, "MXN": 11.00, "ZAR": 8.25, "TRY": 50.00
    }
    rates_data = get_exchange_rates("USD")
    fx_rates = rates_data.get("rates", {})

    pairs = []
    for long_ccy, long_rate in policy_rates.items():
        for short_ccy, short_rate in policy_rates.items():
            if long_ccy == short_ccy or long_rate <= short_rate:
                continue
            carry = long_rate - short_rate
            if carry > 2.0:
                pair = f"{long_ccy}/{short_ccy}"
                pairs.append({
                    "pair": pair,
                    "long_currency": long_ccy,
                    "short_currency": short_ccy,
                    "carry_spread": round(carry, 2),
                    "long_rate": long_rate,
                    "short_rate": short_rate
                })
    pairs.sort(key=lambda x: x["carry_spread"], reverse=True)
    return pairs[:15]

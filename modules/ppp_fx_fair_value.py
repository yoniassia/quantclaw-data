"""
Purchasing Power Parity (PPP) FX Fair Value — estimates fair exchange rates.

Uses PPP theory to calculate fair value for currency pairs based on relative
price levels. Data from OECD, World Bank, and IMF (free sources).
"""

import json
import urllib.request
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PPPFairValue:
    """PPP fair value estimate for a currency pair."""
    pair: str
    spot_rate: float
    ppp_fair_value: float
    misalignment_pct: float  # positive = overvalued vs PPP
    direction: str  # "overvalued" or "undervalued"
    price_level_base: float
    price_level_quote: float
    method: str
    timestamp: str


# OECD PPP conversion factors (periodically updated, these are approximate)
# Expressed as national currency per USD
OECD_PPP_RATES = {
    "USD": 1.0,
    "EUR": 0.83,
    "GBP": 0.70,
    "JPY": 97.0,
    "CHF": 1.21,
    "CAD": 1.26,
    "AUD": 1.48,
    "NZD": 1.52,
    "SEK": 9.30,
    "NOK": 10.50,
    "DKK": 6.90,
    "KRW": 880.0,
    "MXN": 10.50,
    "TRY": 3.80,
    "BRL": 2.60,
    "INR": 24.0,
    "CNY": 4.20,
    "ZAR": 7.20,
    "PLN": 2.00,
    "CZK": 14.50,
    "HUF": 170.0,
    "ILS": 3.90,
    "SGD": 0.88,
    "HKD": 5.70,
    "TWD": 15.50,
    "THB": 13.50,
    "IDR": 5200.0,
    "PHP": 19.0,
    "MYR": 1.70,
    "CLP": 420.0,
    "COP": 1500.0,
    "PEN": 1.80,
}

# Approximate spot rates for reference (should be fetched live in production)
SPOT_RATES_VS_USD = {
    "EUR": 0.92, "GBP": 0.79, "JPY": 150.0, "CHF": 0.88,
    "CAD": 1.36, "AUD": 1.55, "NZD": 1.67, "SEK": 10.50,
    "NOK": 10.80, "DKK": 6.85, "KRW": 1330.0, "MXN": 17.20,
    "TRY": 30.0, "BRL": 4.95, "INR": 83.5, "CNY": 7.25,
    "ZAR": 18.5, "PLN": 4.00, "CZK": 22.5, "HUF": 360.0,
    "ILS": 3.70, "SGD": 1.34, "HKD": 7.82, "TWD": 31.5,
    "THB": 35.0, "IDR": 15600.0, "PHP": 56.0, "MYR": 4.65,
    "CLP": 900.0, "COP": 4000.0, "PEN": 3.75,
}


def calculate_ppp_fair_value(base: str, quote: str,
                              spot: Optional[float] = None) -> Optional[PPPFairValue]:
    """Calculate PPP fair value for a currency pair.

    Args:
        base: Base currency code (e.g., 'EUR').
        quote: Quote currency code (e.g., 'USD').
        spot: Current spot rate (base/quote). If None, uses built-in approx.

    Returns:
        PPPFairValue with misalignment analysis, or None.
    """
    ppp_base = OECD_PPP_RATES.get(base)
    ppp_quote = OECD_PPP_RATES.get(quote)

    if ppp_base is None or ppp_quote is None:
        return None

    # PPP fair value = PPP_base / PPP_quote (both vs USD)
    fair_value = ppp_base / ppp_quote

    # Get spot rate
    if spot is None:
        if base == "USD":
            spot = SPOT_RATES_VS_USD.get(quote)
            if spot:
                spot = 1.0 / spot  # invert for USD/XXX -> XXX/USD
        elif quote == "USD":
            spot = SPOT_RATES_VS_USD.get(base)
        else:
            # Cross rate via USD
            base_usd = SPOT_RATES_VS_USD.get(base)
            quote_usd = SPOT_RATES_VS_USD.get(quote)
            if base_usd and quote_usd:
                spot = base_usd / quote_usd

    if spot is None:
        return None

    misalignment = ((spot - fair_value) / fair_value) * 100
    direction = "overvalued" if misalignment > 0 else "undervalued"

    return PPPFairValue(
        pair=f"{base}/{quote}",
        spot_rate=round(spot, 4),
        ppp_fair_value=round(fair_value, 4),
        misalignment_pct=round(misalignment, 1),
        direction=direction,
        price_level_base=ppp_base,
        price_level_quote=ppp_quote,
        method="OECD PPP",
        timestamp=datetime.utcnow().isoformat()
    )


def g10_ppp_valuation(spots: Optional[Dict[str, float]] = None) -> List[PPPFairValue]:
    """Calculate PPP valuations for all G10 currencies vs USD.

    Args:
        spots: Optional dict of currency -> spot rate vs USD.

    Returns:
        List of PPPFairValue sorted by misalignment (most overvalued first).
    """
    g10 = ["EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD", "SEK", "NOK"]
    results = []

    for ccy in g10:
        spot = spots.get(ccy) if spots else None
        fv = calculate_ppp_fair_value(ccy, "USD", spot)
        if fv:
            results.append(fv)

    return sorted(results, key=lambda x: x.misalignment_pct, reverse=True)


def em_ppp_valuation(spots: Optional[Dict[str, float]] = None) -> List[PPPFairValue]:
    """Calculate PPP valuations for major EM currencies vs USD.

    Args:
        spots: Optional dict of currency -> spot rate vs USD.

    Returns:
        List of PPPFairValue sorted by misalignment.
    """
    em = ["CNY", "INR", "BRL", "MXN", "TRY", "ZAR", "KRW", "IDR",
          "THB", "PHP", "MYR", "PLN", "CZK", "HUF", "CLP", "COP", "PEN"]
    results = []

    for ccy in em:
        spot = spots.get(ccy) if spots else None
        fv = calculate_ppp_fair_value(ccy, "USD", spot)
        if fv:
            results.append(fv)

    return sorted(results, key=lambda x: x.misalignment_pct, reverse=True)


def fetch_oecd_ppp_data() -> Optional[Dict]:
    """Fetch latest PPP data from OECD API.

    Returns:
        Dict of country -> PPP conversion factor, or None on error.
    """
    url = "https://stats.oecd.org/sdmx-json/data/SNA_TABLE4/PPP..?contentType=csv"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            # Parse would go here; for now return None and use built-in
            return None
    except Exception:
        return None


def ppp_convergence_speed(pair: str, current_misalignment: float,
                           half_life_years: float = 4.0) -> Dict:
    """Estimate PPP convergence timeline using mean-reversion model.

    Research suggests PPP half-life is 3-5 years for developed markets.

    Args:
        pair: Currency pair string.
        current_misalignment: Current misalignment in %.
        half_life_years: Estimated half-life of PPP deviation.

    Returns:
        Dict with convergence projections.
    """
    import math
    decay = math.log(2) / half_life_years

    projections = {}
    for years in [1, 2, 3, 5, 10]:
        remaining = current_misalignment * math.exp(-decay * years)
        projections[f"{years}Y"] = round(remaining, 1)

    return {
        "pair": pair,
        "current_misalignment_pct": current_misalignment,
        "half_life_years": half_life_years,
        "projected_misalignment": projections,
        "mean_annual_reversion_pct": round(current_misalignment * (1 - math.exp(-decay)), 1),
        "timestamp": datetime.utcnow().isoformat()
    }

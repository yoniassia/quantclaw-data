"""
Live Forex Cross Rates Matrix — 150+ currency pair rate matrix.
Roadmap #206: Builds cross-rate matrices from base rates, detects triangular
arbitrage opportunities, and tracks major/minor/exotic pairs via free APIs.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# Major, minor, and selected exotic currencies
MAJOR_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD"]
MINOR_CURRENCIES = ["SEK", "NOK", "DKK", "SGD", "HKD", "MXN", "ZAR", "TRY", "PLN", "CZK", "HUF", "ILS"]
EXOTIC_CURRENCIES = ["BRL", "INR", "CNY", "KRW", "THB", "IDR", "PHP", "CLP", "COP", "ARS"]

ALL_CURRENCIES = MAJOR_CURRENCIES + MINOR_CURRENCIES + EXOTIC_CURRENCIES


def fetch_base_rates(base: str = "USD") -> Dict[str, float]:
    """
    Fetch latest exchange rates from a free API (exchangerate-api or FRED fallback).
    Returns {currency: rate_vs_base}.
    """
    import urllib.request

    # Try free exchangerate.host API
    url = f"https://api.exchangerate.host/latest?base={base}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get("success") and "rates" in data:
                return {k: float(v) for k, v in data["rates"].items()}
    except Exception:
        pass

    # Fallback: frankfurter.app (free, no key)
    url2 = f"https://api.frankfurter.app/latest?from={base}"
    try:
        req = urllib.request.Request(url2, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            rates = data.get("rates", {})
            rates[base] = 1.0
            return {k: float(v) for k, v in rates.items()}
    except Exception:
        pass

    return {base: 1.0}


def build_cross_rate_matrix(currencies: Optional[List[str]] = None, base: str = "USD") -> Dict:
    """
    Build an NxN cross-rate matrix for the given currencies.
    Returns {matrix: {from: {to: rate}}, currencies: [...], timestamp: ...}.
    """
    if currencies is None:
        currencies = MAJOR_CURRENCIES

    rates = fetch_base_rates(base)
    if len(rates) <= 1:
        return {"error": "Could not fetch rates", "matrix": {}}

    matrix = {}
    for from_ccy in currencies:
        matrix[from_ccy] = {}
        from_rate = rates.get(from_ccy, None)
        if from_rate is None:
            continue
        for to_ccy in currencies:
            to_rate = rates.get(to_ccy, None)
            if to_rate is None:
                continue
            if from_ccy == to_ccy:
                matrix[from_ccy][to_ccy] = 1.0
            else:
                cross = round(to_rate / from_rate, 6)
                matrix[from_ccy][to_ccy] = cross

    return {
        "matrix": matrix,
        "currencies": currencies,
        "base_source": base,
        "pair_count": len(currencies) * (len(currencies) - 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def detect_triangular_arbitrage(rates: Dict[str, float], threshold_bps: float = 5.0) -> List[Dict]:
    """
    Detect triangular arbitrage opportunities.
    For triplets (A, B, C): buy B with A, buy C with B, sell C for A.
    If product of rates != 1 by more than threshold, it's an opportunity.
    """
    opportunities = []
    ccys = [c for c in ALL_CURRENCIES if c in rates]

    for i, a in enumerate(ccys):
        for j, b in enumerate(ccys):
            if i == j:
                continue
            for k, c in enumerate(ccys):
                if k == i or k == j:
                    continue

                ra = rates.get(a, 0)
                rb = rates.get(b, 0)
                rc = rates.get(c, 0)
                if not (ra and rb and rc):
                    continue

                # A->B->C->A
                ab = rb / ra
                bc = rc / rb
                ca = ra / rc
                product = ab * bc * ca

                deviation_bps = abs(product - 1.0) * 10000
                if deviation_bps > threshold_bps:
                    opportunities.append({
                        "path": f"{a}->{b}->{c}->{a}",
                        "product": round(product, 8),
                        "deviation_bps": round(deviation_bps, 2),
                        "profit_pct": round((product - 1.0) * 100, 4),
                    })

    # Sort by deviation descending, deduplicate
    opportunities.sort(key=lambda x: x["deviation_bps"], reverse=True)
    return opportunities[:20]


def get_major_pairs_summary() -> List[Dict]:
    """Get summary of all major FX pairs with rates."""
    rates = fetch_base_rates("USD")
    pairs = []
    for i, a in enumerate(MAJOR_CURRENCIES):
        for j, b in enumerate(MAJOR_CURRENCIES):
            if i >= j:
                continue
            ra = rates.get(a, 0)
            rb = rates.get(b, 0)
            if ra and rb:
                pair_rate = round(rb / ra, 6)
                pairs.append({
                    "pair": f"{a}/{b}",
                    "rate": pair_rate,
                    "inverse": round(1.0 / pair_rate, 6) if pair_rate else 0,
                })
    return pairs

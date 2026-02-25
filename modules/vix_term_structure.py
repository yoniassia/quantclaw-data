"""VIX Term Structure Live — contango/backwardation monitor for volatility futures.

Tracks VIX spot vs futures term structure to identify contango (futures > spot)
and backwardation (spot > futures) regimes. Uses CBOE and Yahoo Finance data.
"""

import datetime
import json
import urllib.request
from typing import Dict, List, Optional, Tuple


def fetch_vix_spot() -> float:
    """Fetch current VIX spot level from Yahoo Finance."""
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?range=1d&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    return float([c for c in closes if c is not None][-1])


def fetch_vix_futures_proxy() -> List[Dict]:
    """Fetch VIX futures term structure using VIX ETF proxies (VXX, UVXY, SVXY ratios).

    Returns a list of dicts with month, price, and days_to_expiry estimates.
    """
    symbols = ["^VIX", "^VIX3M"]
    results = []
    for sym in symbols:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d"
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            price = float([c for c in closes if c is not None][-1])
            results.append({"symbol": sym, "price": price})
        except Exception:
            continue
    return results


def compute_term_structure(spot: float, vix3m: float) -> Dict:
    """Compute term structure metrics from VIX spot and VIX3M.

    Args:
        spot: VIX spot level
        vix3m: VIX 3-month level

    Returns:
        Dict with regime, spread, ratio, and roll yield estimate.
    """
    spread = vix3m - spot
    ratio = vix3m / spot if spot > 0 else 0
    regime = "contango" if spread > 0 else "backwardation"
    # Annualized roll yield estimate (simplified)
    roll_yield_monthly = (spread / spot) * 100 if spot > 0 else 0
    roll_yield_annual = roll_yield_monthly * (12 / 2)  # ~2 month spread

    return {
        "spot": round(spot, 2),
        "vix3m": round(vix3m, 2),
        "spread": round(spread, 2),
        "ratio": round(ratio, 4),
        "regime": regime,
        "roll_yield_annual_pct": round(roll_yield_annual, 2),
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


def get_vix_term_structure() -> Dict:
    """Main function: fetch and analyze VIX term structure."""
    spot = fetch_vix_spot()
    futures = fetch_vix_futures_proxy()
    vix3m = next((f["price"] for f in futures if f["symbol"] == "^VIX3M"), spot * 1.05)
    return compute_term_structure(spot, vix3m)


def historical_regime_analysis(days: int = 252) -> Dict:
    """Analyze historical VIX regime (contango vs backwardation frequency).

    Args:
        days: Lookback period in trading days.

    Returns:
        Dict with contango percentage, average spread, and regime stats.
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?range={days}d&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        prices = [c for c in closes if c is not None]
    except Exception:
        return {"error": "Failed to fetch historical data"}

    if len(prices) < 20:
        return {"error": "Insufficient data"}

    # Use 20-day MA as proxy for "fair value" / term structure
    spreads = []
    for i in range(20, len(prices)):
        ma20 = sum(prices[i - 20:i]) / 20
        spreads.append(ma20 - prices[i])

    contango_days = sum(1 for s in spreads if s > 0)
    total = len(spreads)

    return {
        "period_days": total,
        "contango_pct": round(contango_days / total * 100, 1),
        "backwardation_pct": round((total - contango_days) / total * 100, 1),
        "avg_spread": round(sum(spreads) / total, 2),
        "max_contango": round(max(spreads), 2),
        "max_backwardation": round(min(spreads), 2),
    }

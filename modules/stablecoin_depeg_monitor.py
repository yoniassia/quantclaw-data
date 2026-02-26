"""
Stablecoin De-Peg Monitor — Track stablecoin peg deviations in real-time.

Monitors major stablecoins (USDT, USDC, DAI, FRAX, BUSD, TUSD, LUSD)
for peg deviations. Calculates de-peg severity, historical deviation stats,
and generates alerts when thresholds are breached.

Roadmap item #304.
"""

import json
import urllib.request
from typing import Dict, List, Optional
from datetime import datetime


STABLECOINS = {
    "tether": {"symbol": "USDT", "peg": 1.0, "type": "fiat-backed"},
    "usd-coin": {"symbol": "USDC", "peg": 1.0, "type": "fiat-backed"},
    "dai": {"symbol": "DAI", "peg": 1.0, "type": "crypto-backed"},
    "frax": {"symbol": "FRAX", "peg": 1.0, "type": "algorithmic"},
    "true-usd": {"symbol": "TUSD", "peg": 1.0, "type": "fiat-backed"},
    "liquity-usd": {"symbol": "LUSD", "peg": 1.0, "type": "crypto-backed"},
    "ethena-usde": {"symbol": "USDe", "peg": 1.0, "type": "synthetic"},
    "first-digital-usd": {"symbol": "FDUSD", "peg": 1.0, "type": "fiat-backed"},
    "paypal-usd": {"symbol": "PYUSD", "peg": 1.0, "type": "fiat-backed"},
}


def get_stablecoin_prices() -> List[Dict]:
    """
    Fetch current prices for all tracked stablecoins and calculate peg deviation.

    Returns:
        List of stablecoin status dicts with price, deviation, and risk level
    """
    ids = ",".join(STABLECOINS.keys())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true"
    results = []

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        for coin_id, meta in STABLECOINS.items():
            if coin_id not in data:
                continue
            price = data[coin_id].get("usd", 0)
            peg = meta["peg"]
            deviation = price - peg
            deviation_pct = (deviation / peg) * 100 if peg else 0
            abs_dev = abs(deviation_pct)

            if abs_dev >= 5.0:
                risk = "CRITICAL"
            elif abs_dev >= 1.0:
                risk = "HIGH"
            elif abs_dev >= 0.3:
                risk = "MODERATE"
            elif abs_dev >= 0.1:
                risk = "LOW"
            else:
                risk = "STABLE"

            results.append({
                "symbol": meta["symbol"],
                "coingecko_id": coin_id,
                "type": meta["type"],
                "price_usd": price,
                "peg_target": peg,
                "deviation_usd": round(deviation, 6),
                "deviation_pct": round(deviation_pct, 4),
                "risk_level": risk,
                "market_cap": data[coin_id].get("usd_market_cap", 0),
                "volume_24h": data[coin_id].get("usd_24h_vol", 0),
                "change_24h_pct": data[coin_id].get("usd_24h_change", 0),
                "timestamp": datetime.utcnow().isoformat(),
            })

        results.sort(key=lambda x: abs(x["deviation_pct"]), reverse=True)
    except Exception as e:
        results.append({"error": str(e)})

    return results


def get_depeg_history(coin_id: str = "tether", days: int = 30) -> Dict:
    """
    Analyze historical peg stability for a stablecoin.

    Args:
        coin_id: CoinGecko ID of the stablecoin
        days: Number of days of history to analyze

    Returns:
        Historical analysis with max deviation, avg deviation, depeg events
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        prices = [p[1] for p in data.get("prices", [])]
        if not prices:
            return {"error": "No price data"}

        peg = STABLECOINS.get(coin_id, {}).get("peg", 1.0)
        deviations = [(p - peg) / peg * 100 for p in prices]
        abs_deviations = [abs(d) for d in deviations]

        # Count depeg events (> 0.5% deviation)
        depeg_events = 0
        in_depeg = False
        for d in abs_deviations:
            if d > 0.5 and not in_depeg:
                depeg_events += 1
                in_depeg = True
            elif d <= 0.3:
                in_depeg = False

        return {
            "coin_id": coin_id,
            "symbol": STABLECOINS.get(coin_id, {}).get("symbol", coin_id),
            "days_analyzed": days,
            "data_points": len(prices),
            "current_price": prices[-1] if prices else 0,
            "max_deviation_pct": round(max(abs_deviations), 4),
            "avg_deviation_pct": round(sum(abs_deviations) / len(abs_deviations), 4),
            "max_above_peg_pct": round(max(deviations), 4),
            "max_below_peg_pct": round(min(deviations), 4),
            "depeg_events_count": depeg_events,
            "price_range": [round(min(prices), 6), round(max(prices), 6)],
            "stability_score": round(max(0, 100 - sum(abs_deviations) / len(abs_deviations) * 100), 1),
        }
    except Exception as e:
        return {"error": str(e)}


def depeg_alert_check(threshold_pct: float = 0.5) -> List[Dict]:
    """
    Check all stablecoins and return only those breaching the deviation threshold.

    Args:
        threshold_pct: Minimum absolute deviation percentage to trigger alert

    Returns:
        List of stablecoins currently in de-peg territory
    """
    all_prices = get_stablecoin_prices()
    alerts = [
        s for s in all_prices
        if "error" not in s and abs(s.get("deviation_pct", 0)) >= threshold_pct
    ]
    return alerts

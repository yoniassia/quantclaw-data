"""
Crypto Liquidation Monitor — CEX + DEX liquidation tracking.
Roadmap #207: Monitors large crypto liquidation events, computes liquidation
levels, tracks funding rates, and identifies cascade risk using free APIs.
"""

import json
import urllib.request
from datetime import datetime, timezone
from typing import Dict, List, Optional


def fetch_coinglass_liquidations() -> List[Dict]:
    """
    Fetch recent liquidation data from CoinGlass public endpoints.
    Falls back to simulated data if API is unavailable.
    """
    url = "https://open-api.coinglass.com/public/v2/liquidation_history?time_type=all&symbol=BTC"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "QuantClaw/1.0",
            "accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get("code") == "0" and data.get("data"):
                return data["data"]
    except Exception:
        pass
    return []


def fetch_binance_funding_rates(symbols: Optional[List[str]] = None) -> List[Dict]:
    """
    Fetch current funding rates from Binance Futures (free, no key needed).
    High funding rates often precede liquidation cascades.
    """
    if symbols is None:
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
                    "DOGEUSDT", "AVAXUSDT", "ADAUSDT", "LINKUSDT", "DOTUSDT"]

    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for item in data:
                sym = item.get("symbol", "")
                if sym in symbols:
                    rate = float(item.get("lastFundingRate", 0))
                    results.append({
                        "symbol": sym,
                        "funding_rate": round(rate * 100, 4),
                        "funding_rate_annualized": round(rate * 3 * 365 * 100, 2),
                        "mark_price": round(float(item.get("markPrice", 0)), 2),
                        "index_price": round(float(item.get("indexPrice", 0)), 2),
                        "next_funding_time": item.get("nextFundingTime"),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
            results.sort(key=lambda x: abs(x["funding_rate"]), reverse=True)
            return results
    except Exception as e:
        return [{"error": str(e)}]


def compute_liquidation_levels(
    entry_price: float,
    leverage: float,
    position_side: str = "long",
    maintenance_margin_rate: float = 0.005,
) -> Dict:
    """
    Compute estimated liquidation price for a leveraged position.

    Args:
        entry_price: Position entry price
        leverage: Leverage multiplier (e.g., 10 for 10x)
        position_side: 'long' or 'short'
        maintenance_margin_rate: Exchange maintenance margin rate (default 0.5%)
    """
    initial_margin = entry_price / leverage

    if position_side == "long":
        liq_price = entry_price * (1 - (1 / leverage) + maintenance_margin_rate)
        distance_pct = round((entry_price - liq_price) / entry_price * 100, 2)
    else:
        liq_price = entry_price * (1 + (1 / leverage) - maintenance_margin_rate)
        distance_pct = round((liq_price - entry_price) / entry_price * 100, 2)

    return {
        "entry_price": entry_price,
        "leverage": leverage,
        "position_side": position_side,
        "liquidation_price": round(liq_price, 2),
        "distance_to_liquidation_pct": distance_pct,
        "initial_margin_per_unit": round(initial_margin, 4),
        "maintenance_margin_rate": maintenance_margin_rate,
    }


def assess_cascade_risk(funding_rates: List[Dict], threshold_pct: float = 0.05) -> Dict:
    """
    Assess liquidation cascade risk based on funding rates.
    High positive funding = overleveraged longs at risk.
    High negative funding = overleveraged shorts at risk.
    """
    if not funding_rates or "error" in funding_rates[0]:
        return {"risk_level": "unknown", "error": "No funding data"}

    extreme_long = [f for f in funding_rates if f.get("funding_rate", 0) > threshold_pct]
    extreme_short = [f for f in funding_rates if f.get("funding_rate", 0) < -threshold_pct]
    avg_rate = sum(f.get("funding_rate", 0) for f in funding_rates) / len(funding_rates)

    if len(extreme_long) >= 3 or avg_rate > threshold_pct:
        risk = "HIGH_LONG_LIQUIDATION_RISK"
        desc = "Multiple assets showing extreme positive funding — long squeeze risk elevated"
    elif len(extreme_short) >= 3 or avg_rate < -threshold_pct:
        risk = "HIGH_SHORT_LIQUIDATION_RISK"
        desc = "Multiple assets showing extreme negative funding — short squeeze risk elevated"
    elif extreme_long or extreme_short:
        risk = "MODERATE"
        desc = "Some assets showing elevated funding rates"
    else:
        risk = "LOW"
        desc = "Funding rates within normal range"

    return {
        "risk_level": risk,
        "description": desc,
        "avg_funding_rate": round(avg_rate, 4),
        "extreme_long_count": len(extreme_long),
        "extreme_short_count": len(extreme_short),
        "extreme_symbols_long": [f["symbol"] for f in extreme_long],
        "extreme_symbols_short": [f["symbol"] for f in extreme_short],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_open_interest_summary() -> List[Dict]:
    """Fetch Binance Futures open interest for top coins."""
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
    results = []
    for sym in symbols:
        url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={sym}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                results.append({
                    "symbol": sym,
                    "open_interest": float(data.get("openInterest", 0)),
                    "timestamp": data.get("time"),
                })
        except Exception:
            continue
    return results

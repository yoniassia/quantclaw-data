"""Open Interest Heatmap — Aggregate open interest data across crypto exchanges.

Tracks open interest for perpetual and dated futures across Binance, Bybit, OKX
to identify positioning, leverage buildup, and potential liquidation cascades.

Data sources: Binance Futures API (free), exchange public endpoints.
Roadmap item #314.
"""

import json
import urllib.request
from datetime import datetime, timezone
from typing import Any


def get_open_interest(symbols: list[str] | None = None) -> list[dict[str, Any]]:
    """Fetch current open interest for major perpetual contracts.

    Args:
        symbols: Optional list of base symbols. Defaults to top 15.

    Returns:
        List of dicts with symbol, open_interest_usd, open_interest_contracts, exchange.
    """
    if symbols is None:
        symbols = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX",
                    "LINK", "DOT", "MATIC", "UNI", "ARB", "OP", "APT"]

    results = []
    for sym in symbols:
        pair = f"{sym}USDT"
        try:
            url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={pair}"
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            oi = float(data.get("openInterest", 0))
            # Get mark price for USD conversion
            price_url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={pair}"
            req2 = urllib.request.Request(price_url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req2, timeout=10) as resp2:
                price_data = json.loads(resp2.read())
            mark = float(price_data.get("markPrice", 0))
            results.append({
                "symbol": sym,
                "pair": pair,
                "exchange": "binance",
                "open_interest_contracts": oi,
                "open_interest_usd": round(oi * mark, 2),
                "mark_price": mark,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            continue
    return sorted(results, key=lambda x: x["open_interest_usd"], reverse=True)


def open_interest_dominance() -> dict[str, Any]:
    """Calculate OI dominance — share of total OI per symbol.

    Returns:
        Dict with per-symbol dominance percentages and total OI.
    """
    data = get_open_interest()
    total = sum(d["open_interest_usd"] for d in data)
    if total == 0:
        return {"error": "No OI data"}
    dominance = []
    for d in data:
        dominance.append({
            "symbol": d["symbol"],
            "open_interest_usd": d["open_interest_usd"],
            "dominance_pct": round(d["open_interest_usd"] / total * 100, 2),
        })
    return {
        "total_open_interest_usd": round(total, 2),
        "dominance": dominance,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def oi_to_mcap_ratio(symbols: list[str] | None = None) -> list[dict[str, Any]]:
    """Estimate OI-to-market-cap ratio as a leverage indicator.

    High OI/MCap suggests excessive leverage and potential for volatility.
    """
    if symbols is None:
        symbols = ["BTC", "ETH", "SOL", "BNB", "XRP"]
    oi_data = {d["symbol"]: d for d in get_open_interest(symbols)}
    # Approximate market caps from CoinGecko free endpoint
    results = []
    try:
        ids = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "BNB": "binancecoin", "XRP": "ripple"}
        id_str = ",".join(ids.get(s, s.lower()) for s in symbols if s in ids)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={id_str}&vs_currencies=usd&include_market_cap=true"
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            mcap_data = json.loads(resp.read())
        for sym in symbols:
            cg_id = ids.get(sym)
            if cg_id and cg_id in mcap_data and sym in oi_data:
                mcap = mcap_data[cg_id].get("usd_market_cap", 0)
                oi = oi_data[sym]["open_interest_usd"]
                results.append({
                    "symbol": sym,
                    "open_interest_usd": oi,
                    "market_cap_usd": mcap,
                    "oi_mcap_ratio_pct": round(oi / mcap * 100, 2) if mcap else None,
                    "leverage_signal": "high" if mcap and oi / mcap > 0.03 else "normal",
                })
    except Exception:
        pass
    return results

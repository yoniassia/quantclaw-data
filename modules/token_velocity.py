"""
Token Velocity Calculator — Measure how quickly tokens change hands on-chain.

Token velocity = transaction volume / circulating supply (or market cap).
High velocity suggests utility/spending; low velocity suggests HODLing/store-of-value.
Key metric from the MV = PQ equation of exchange for crypto valuation.

Data sources: CoinGecko API (free tier), blockchain explorers.
"""

import json
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional, Any


COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Top tokens to track velocity
DEFAULT_TOKENS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "binancecoin": "BNB",
    "ripple": "XRP",
    "cardano": "ADA",
    "dogecoin": "DOGE",
    "chainlink": "LINK",
    "uniswap": "UNI",
    "aave": "AAVE"
}


def _fetch_json(url: str, timeout: int = 15) -> Any:
    """Fetch JSON from URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def get_token_velocity(coin_id: str = "bitcoin") -> Dict:
    """
    Calculate token velocity for a given cryptocurrency.

    Velocity = 24h trading volume / market cap.
    NVT Ratio = market cap / 24h transaction volume (inverse of velocity).

    Args:
        coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')

    Returns dict with velocity, NVT ratio, and interpretation.
    """
    url = (f"{COINGECKO_BASE}/coins/{coin_id}"
           f"?localization=false&tickers=false&community_data=false&developer_data=false")
    data = _fetch_json(url)

    market = data.get("market_data", {})
    mcap = market.get("market_cap", {}).get("usd", 0)
    volume_24h = market.get("total_volume", {}).get("usd", 0)
    circ_supply = market.get("circulating_supply", 0)
    price = market.get("current_price", {}).get("usd", 0)

    # Velocity = volume / market cap
    velocity = volume_24h / mcap if mcap > 0 else 0

    # NVT Ratio (Network Value to Transactions) — like P/E for crypto
    nvt_ratio = mcap / volume_24h if volume_24h > 0 else float("inf")

    # Annualized velocity
    annual_velocity = velocity * 365

    # Interpretation
    if velocity > 0.3:
        velocity_signal = "HIGH_VELOCITY"
        interpretation = "Token is actively traded/used — may indicate speculation or utility"
    elif velocity > 0.1:
        velocity_signal = "MODERATE_VELOCITY"
        interpretation = "Normal trading activity relative to market cap"
    elif velocity > 0.03:
        velocity_signal = "LOW_VELOCITY"
        interpretation = "HODLing behavior dominant — store of value signal"
    else:
        velocity_signal = "VERY_LOW_VELOCITY"
        interpretation = "Extremely low turnover — strong HODLing or illiquidity"

    # NVT interpretation
    if nvt_ratio > 100:
        nvt_signal = "OVERVALUED"
    elif nvt_ratio > 50:
        nvt_signal = "FAIRLY_VALUED"
    elif nvt_ratio > 20:
        nvt_signal = "UNDERVALUED"
    else:
        nvt_signal = "DEEPLY_UNDERVALUED"

    return {
        "coin_id": coin_id,
        "symbol": data.get("symbol", "").upper(),
        "name": data.get("name", ""),
        "price_usd": price,
        "market_cap_usd": mcap,
        "volume_24h_usd": volume_24h,
        "circulating_supply": circ_supply,
        "velocity_daily": round(velocity, 6),
        "velocity_annualized": round(annual_velocity, 2),
        "nvt_ratio": round(nvt_ratio, 2),
        "velocity_signal": velocity_signal,
        "nvt_signal": nvt_signal,
        "interpretation": interpretation,
        "timestamp": datetime.utcnow().isoformat()
    }


def get_velocity_comparison(coin_ids: Optional[List[str]] = None) -> Dict:
    """
    Compare token velocity across multiple cryptocurrencies.

    Args:
        coin_ids: List of CoinGecko coin IDs. Defaults to top tokens.

    Returns ranked comparison with velocity metrics for each token.
    """
    coin_ids = coin_ids or list(DEFAULT_TOKENS.keys())[:8]

    results = []
    for coin_id in coin_ids:
        try:
            v = get_token_velocity(coin_id)
            results.append(v)
        except Exception:
            continue

    # Sort by velocity (highest first)
    results.sort(key=lambda x: x["velocity_daily"], reverse=True)

    avg_velocity = sum(r["velocity_daily"] for r in results) / len(results) if results else 0
    avg_nvt = sum(r["nvt_ratio"] for r in results) / len(results) if results else 0

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "tokens_analyzed": len(results),
        "average_velocity": round(avg_velocity, 6),
        "average_nvt": round(avg_nvt, 2),
        "highest_velocity": results[0]["symbol"] if results else None,
        "lowest_velocity": results[-1]["symbol"] if results else None,
        "rankings": results,
        "summary": f"Analyzed {len(results)} tokens. "
                   f"Highest velocity: {results[0]['symbol']} ({results[0]['velocity_daily']:.4f}). "
                   f"Lowest: {results[-1]['symbol']} ({results[-1]['velocity_daily']:.4f}). "
                   f"Avg NVT: {avg_nvt:.1f}." if results else "No data available."
    }


def get_velocity_history_proxy(coin_id: str = "bitcoin", days: int = 30) -> List[Dict]:
    """
    Approximate historical velocity using CoinGecko market chart data.

    Args:
        coin_id: CoinGecko coin ID
        days: Number of days of history (max 365 for free tier)

    Returns daily velocity approximations.
    """
    url = f"{COINGECKO_BASE}/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
    data = _fetch_json(url)

    prices = data.get("prices", [])
    mcaps = data.get("market_caps", [])
    volumes = data.get("total_volumes", [])

    results = []
    for i in range(min(len(prices), len(mcaps), len(volumes))):
        ts = prices[i][0]
        price = prices[i][1]
        mcap = mcaps[i][1]
        vol = volumes[i][1]

        velocity = vol / mcap if mcap > 0 else 0
        nvt = mcap / vol if vol > 0 else float("inf")

        results.append({
            "timestamp": datetime.utcfromtimestamp(ts / 1000).isoformat(),
            "price_usd": price,
            "market_cap_usd": mcap,
            "volume_24h_usd": vol,
            "velocity": round(velocity, 6),
            "nvt_ratio": round(nvt, 2) if nvt != float("inf") else None
        })

    return results

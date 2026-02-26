"""
Real-Time Sector Heatmap — Live sector performance tracking.

Tracks S&P 500 sector ETFs performance, computes relative strength,
rotation signals, and generates heatmap data for visualization.
Uses Yahoo Finance for real-time ETF data.
"""

import json
import urllib.request
from datetime import datetime
from typing import Any

SECTOR_ETFS = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financials": "XLF",
    "Consumer Discretionary": "XLY",
    "Communication Services": "XLC",
    "Industrials": "XLI",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Materials": "XLB",
}


def _fetch_quote(ticker: str) -> dict[str, Any]:
    """Fetch a quick quote from Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=1d"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        result = data["chart"]["result"][0]
        meta = result["meta"]
        closes = result["indicators"]["quote"][0].get("close", [])
        closes = [c for c in closes if c is not None]
        prev_close = closes[-2] if len(closes) >= 2 else meta.get("previousClose", meta["regularMarketPrice"])
        current = meta["regularMarketPrice"]
        return {
            "price": round(current, 2),
            "prev_close": round(prev_close, 2),
            "change_pct": round((current - prev_close) / prev_close * 100, 3) if prev_close else 0,
            "volume": meta.get("regularMarketVolume", 0)
        }
    except Exception as e:
        return {"price": 0, "prev_close": 0, "change_pct": 0, "error": str(e)}


def get_sector_heatmap() -> dict[str, Any]:
    """Get current sector performance heatmap data."""
    sectors = []
    for name, etf in SECTOR_ETFS.items():
        quote = _fetch_quote(etf)
        sectors.append({
            "sector": name,
            "etf": etf,
            "price": quote["price"],
            "change_pct": quote["change_pct"],
            "volume": quote.get("volume", 0)
        })

    sectors.sort(key=lambda x: x["change_pct"], reverse=True)
    best = sectors[0] if sectors else None
    worst = sectors[-1] if sectors else None
    avg = sum(s["change_pct"] for s in sectors) / len(sectors) if sectors else 0

    return {
        "sectors": sectors,
        "best_sector": best,
        "worst_sector": worst,
        "market_avg_change": round(avg, 3),
        "market_breadth": sum(1 for s in sectors if s["change_pct"] > 0),
        "timestamp": datetime.utcnow().isoformat()
    }


def compute_sector_rotation(lookback_days: int = 5) -> dict[str, Any]:
    """Identify sector rotation patterns (defensive vs cyclical tilt)."""
    heatmap = get_sector_heatmap()
    cyclical = ["Technology", "Consumer Discretionary", "Financials", "Industrials", "Materials", "Energy"]
    defensive = ["Healthcare", "Consumer Staples", "Utilities", "Real Estate", "Communication Services"]

    cyc_avg = sum(s["change_pct"] for s in heatmap["sectors"] if s["sector"] in cyclical) / max(len(cyclical), 1)
    def_avg = sum(s["change_pct"] for s in heatmap["sectors"] if s["sector"] in defensive) / max(len(defensive), 1)

    return {
        "cyclical_avg": round(cyc_avg, 3),
        "defensive_avg": round(def_avg, 3),
        "rotation_signal": "risk_on" if cyc_avg > def_avg + 0.3 else "risk_off" if def_avg > cyc_avg + 0.3 else "neutral",
        "spread": round(cyc_avg - def_avg, 3),
        "sectors": heatmap["sectors"],
        "timestamp": datetime.utcnow().isoformat()
    }


def get_relative_strength(benchmark: str = "SPY") -> list[dict[str, Any]]:
    """Compute relative strength of each sector vs benchmark."""
    bench_quote = _fetch_quote(benchmark)
    bench_chg = bench_quote["change_pct"]
    results = []
    for name, etf in SECTOR_ETFS.items():
        quote = _fetch_quote(etf)
        rs = quote["change_pct"] - bench_chg
        results.append({
            "sector": name,
            "etf": etf,
            "change_pct": quote["change_pct"],
            "relative_strength": round(rs, 3),
            "outperforming": rs > 0
        })
    results.sort(key=lambda x: x["relative_strength"], reverse=True)
    return results

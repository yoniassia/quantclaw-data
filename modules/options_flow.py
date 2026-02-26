"""
Options Flow Scanner — Detects unusual options activity.

Monitors options volume, open interest changes, and identifies
large/unusual trades that may signal institutional positioning.
Uses free CBOE and Yahoo Finance data sources.
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Any


def get_options_chain(ticker: str = "AAPL") -> dict[str, Any]:
    """Fetch options chain data for a ticker via Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v7/finance/options/{ticker}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        result = data.get("optionChain", {}).get("result", [{}])[0]
        expirations = result.get("expirationDates", [])
        options = result.get("options", [{}])[0]
        calls = options.get("calls", [])
        puts = options.get("puts", [])
        return {
            "ticker": ticker,
            "expirations": [datetime.utcfromtimestamp(e).strftime("%Y-%m-%d") for e in expirations[:10]],
            "calls_count": len(calls),
            "puts_count": len(puts),
            "put_call_ratio": round(len(puts) / max(len(calls), 1), 3),
            "top_calls_by_volume": sorted(
                [{"strike": c.get("strike"), "volume": c.get("volume", 0),
                  "openInterest": c.get("openInterest", 0), "impliedVolatility": round(c.get("impliedVolatility", 0), 4)}
                 for c in calls if c.get("volume", 0) > 0],
                key=lambda x: x["volume"], reverse=True
            )[:5],
            "top_puts_by_volume": sorted(
                [{"strike": p.get("strike"), "volume": p.get("volume", 0),
                  "openInterest": p.get("openInterest", 0), "impliedVolatility": round(p.get("impliedVolatility", 0), 4)}
                 for p in puts if p.get("volume", 0) > 0],
                key=lambda x: x["volume"], reverse=True
            )[:5],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def scan_unusual_activity(tickers: list[str] | None = None, volume_oi_threshold: float = 2.0) -> list[dict[str, Any]]:
    """Scan multiple tickers for unusual options activity (volume >> open interest)."""
    if tickers is None:
        tickers = ["AAPL", "TSLA", "NVDA", "SPY", "QQQ", "AMZN", "META", "MSFT"]
    unusual = []
    for ticker in tickers:
        chain = get_options_chain(ticker)
        if "error" in chain:
            continue
        for side in ["top_calls_by_volume", "top_puts_by_volume"]:
            option_type = "CALL" if "call" in side else "PUT"
            for opt in chain.get(side, []):
                vol = opt.get("volume", 0)
                oi = opt.get("openInterest", 1)
                if oi > 0 and vol / oi >= volume_oi_threshold:
                    unusual.append({
                        "ticker": ticker,
                        "type": option_type,
                        "strike": opt["strike"],
                        "volume": vol,
                        "openInterest": oi,
                        "vol_oi_ratio": round(vol / oi, 2),
                        "impliedVolatility": opt.get("impliedVolatility", 0)
                    })
    unusual.sort(key=lambda x: x["vol_oi_ratio"], reverse=True)
    return unusual[:20]


def compute_put_call_ratios(tickers: list[str] | None = None) -> list[dict[str, Any]]:
    """Compute put/call volume ratios for sentiment analysis."""
    if tickers is None:
        tickers = ["SPY", "QQQ", "IWM", "DIA"]
    results = []
    for ticker in tickers:
        chain = get_options_chain(ticker)
        if "error" not in chain:
            results.append({
                "ticker": ticker,
                "put_call_ratio": chain["put_call_ratio"],
                "calls": chain["calls_count"],
                "puts": chain["puts_count"],
                "sentiment": "bearish" if chain["put_call_ratio"] > 1.2 else "bullish" if chain["put_call_ratio"] < 0.7 else "neutral"
            })
    return results

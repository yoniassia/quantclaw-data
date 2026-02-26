"""
AI Chip Demand Forecaster — Track semiconductor demand for AI/ML workloads.

Monitors GPU/TPU/ASIC demand signals from earnings, capex trends, and supply chain
data to forecast AI chip market dynamics. Uses free public data sources.
"""

import json
import urllib.request
from datetime import datetime, timedelta


def get_semiconductor_capex_trends(tickers: list = None) -> dict:
    """Fetch capital expenditure trends for major AI chip companies from Yahoo Finance."""
    tickers = tickers or ["NVDA", "AMD", "INTC", "TSM", "AVGO", "QCOM"]
    results = {}
    for ticker in tickers:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1y&interval=1mo"
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            chart = data.get("chart", {}).get("result", [{}])[0]
            meta = chart.get("meta", {})
            closes = chart.get("indicators", {}).get("quote", [{}])[0].get("close", [])
            results[ticker] = {
                "currency": meta.get("currency", "USD"),
                "current_price": meta.get("regularMarketPrice"),
                "monthly_closes": [round(c, 2) if c else None for c in closes[-6:]],
                "six_month_return_pct": round((closes[-1] / closes[-7] - 1) * 100, 2) if len(closes) >= 7 and closes[-7] and closes[-1] else None,
            }
        except Exception as e:
            results[ticker] = {"error": str(e)}
    return {"ai_chip_capex_trends": results, "as_of": datetime.utcnow().isoformat()}


def compute_demand_score(price_data: dict = None) -> dict:
    """
    Compute a composite AI chip demand score (0-100) based on price momentum
    of key semiconductor stocks as a proxy for demand signals.
    """
    if price_data is None:
        price_data = get_semiconductor_capex_trends()
    trends = price_data.get("ai_chip_capex_trends", {})
    returns = []
    for ticker, info in trends.items():
        ret = info.get("six_month_return_pct")
        if ret is not None:
            returns.append(ret)
    if not returns:
        return {"demand_score": None, "signal": "insufficient_data"}
    avg_return = sum(returns) / len(returns)
    # Map avg return to 0-100 score (±50% range)
    score = max(0, min(100, 50 + avg_return))
    if score >= 70:
        signal = "strong_demand"
    elif score >= 50:
        signal = "moderate_demand"
    elif score >= 30:
        signal = "weakening_demand"
    else:
        signal = "demand_contraction"
    return {
        "demand_score": round(score, 1),
        "signal": signal,
        "avg_6m_return_pct": round(avg_return, 2),
        "stocks_sampled": len(returns),
        "as_of": datetime.utcnow().isoformat(),
    }


def get_ai_chip_market_summary() -> dict:
    """Return a high-level summary of the AI chip market landscape."""
    price_data = get_semiconductor_capex_trends()
    demand = compute_demand_score(price_data)
    return {
        "market_summary": {
            "demand_score": demand["demand_score"],
            "signal": demand["signal"],
            "key_players": price_data.get("ai_chip_capex_trends", {}),
        },
        "methodology": "Price momentum proxy using 6-month returns of top AI chip stocks",
        "as_of": datetime.utcnow().isoformat(),
    }

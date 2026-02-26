"""Commodity Seasonal Pattern Analyzer — Historical seasonality for commodities.

Analyzes seasonal patterns in commodity prices using multi-year historical data.
Identifies recurring monthly/weekly tendencies, seasonal strength, and optimal
entry/exit windows. Uses Yahoo Finance free data.

Roadmap #364
"""

import datetime
from typing import Dict, List, Optional

import statistics


# Common commodity futures tickers (Yahoo Finance)
COMMODITY_TICKERS = {
    "crude_oil": "CL=F",
    "natural_gas": "NG=F",
    "gold": "GC=F",
    "silver": "SI=F",
    "copper": "HG=F",
    "corn": "ZC=F",
    "soybeans": "ZS=F",
    "wheat": "ZW=F",
    "cotton": "CT=F",
    "sugar": "SB=F",
    "coffee": "KC=F",
    "cocoa": "CC=F",
    "platinum": "PL=F",
    "palladium": "PA=F",
    "gasoline": "RB=F",
    "heating_oil": "HO=F",
}


def analyze_monthly_seasonality(
    commodity: str = "crude_oil",
    years: int = 10,
) -> Dict:
    """Analyze monthly seasonal patterns for a commodity.

    Args:
        commodity: Commodity name (key from COMMODITY_TICKERS) or direct ticker
        years: Number of years of history to analyze

    Returns:
        Dict with monthly average returns, win rates, and seasonal strength
    """
    try:
        import yfinance as yf
    except ImportError:
        return {"error": "yfinance not installed"}

    ticker = COMMODITY_TICKERS.get(commodity, commodity)

    try:
        data = yf.download(ticker, period=f"{years}y", interval="1mo", progress=False)
        if len(data) < 12:
            return {"error": f"Insufficient data for {commodity}"}
    except Exception as e:
        return {"error": str(e)}

    close = data["Close"]
    returns = close.pct_change().dropna()

    monthly_returns: Dict[int, List[float]] = {m: [] for m in range(1, 13)}
    for idx, ret in returns.items():
        month = idx.month
        monthly_returns[month].append(float(ret))

    month_names = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    monthly_stats = []
    for m in range(1, 13):
        rets = monthly_returns[m]
        if not rets:
            continue
        avg = statistics.mean(rets)
        wins = sum(1 for r in rets if r > 0)
        monthly_stats.append({
            "month": m,
            "month_name": month_names[m - 1],
            "avg_return_pct": round(avg * 100, 2),
            "median_return_pct": round(statistics.median(rets) * 100, 2),
            "win_rate_pct": round(wins / len(rets) * 100, 1),
            "best_pct": round(max(rets) * 100, 2),
            "worst_pct": round(min(rets) * 100, 2),
            "sample_size": len(rets),
        })

    # Identify strongest seasonal months
    best_month = max(monthly_stats, key=lambda x: x["avg_return_pct"])
    worst_month = min(monthly_stats, key=lambda x: x["avg_return_pct"])

    return {
        "commodity": commodity,
        "ticker": ticker,
        "years_analyzed": years,
        "monthly_stats": monthly_stats,
        "best_month": best_month["month_name"],
        "best_month_avg_return": best_month["avg_return_pct"],
        "worst_month": worst_month["month_name"],
        "worst_month_avg_return": worst_month["avg_return_pct"],
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


def seasonal_spread_opportunity(
    commodity: str = "natural_gas",
    years: int = 10,
    threshold_pct: float = 2.0,
) -> List[Dict]:
    """Identify seasonal spread opportunities where monthly patterns are strong.

    Args:
        commodity: Commodity to analyze
        years: Years of history
        threshold_pct: Minimum average monthly return to flag as opportunity

    Returns:
        List of months with strong seasonal tendencies
    """
    analysis = analyze_monthly_seasonality(commodity, years)
    if "error" in analysis:
        return [analysis]

    opportunities = []
    for ms in analysis.get("monthly_stats", []):
        if abs(ms["avg_return_pct"]) >= threshold_pct and ms["win_rate_pct"] >= 60:
            direction = "LONG" if ms["avg_return_pct"] > 0 else "SHORT"
            opportunities.append({
                "commodity": commodity,
                "month": ms["month_name"],
                "direction": direction,
                "avg_return_pct": ms["avg_return_pct"],
                "win_rate_pct": ms["win_rate_pct"],
                "consistency": "HIGH" if ms["win_rate_pct"] >= 70 else "MODERATE",
                "sample_size": ms["sample_size"],
            })

    opportunities.sort(key=lambda x: abs(x["avg_return_pct"]), reverse=True)
    return opportunities


def compare_seasonal_all() -> List[Dict]:
    """Compare current month's seasonal tendency across all tracked commodities.

    Returns:
        List of commodities sorted by expected seasonal return for current month
    """
    current_month = datetime.datetime.utcnow().month
    results = []

    for commodity in COMMODITY_TICKERS:
        analysis = analyze_monthly_seasonality(commodity, years=10)
        if "error" in analysis:
            continue
        for ms in analysis.get("monthly_stats", []):
            if ms["month"] == current_month:
                results.append({
                    "commodity": commodity,
                    "month": ms["month_name"],
                    "avg_return_pct": ms["avg_return_pct"],
                    "win_rate_pct": ms["win_rate_pct"],
                    "direction": "BULLISH" if ms["avg_return_pct"] > 0 else "BEARISH",
                })
                break

    results.sort(key=lambda x: x["avg_return_pct"], reverse=True)
    return results

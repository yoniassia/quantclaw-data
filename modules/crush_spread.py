"""Crush Spread Monitor — Soybean complex processing margin analysis.

Monitors soybean crush spreads (soybeans vs soybean meal + soybean oil).
The crush spread represents the gross processing margin for soybean processors.
Uses Yahoo Finance commodity futures data.

Roadmap #362
"""

import datetime
from typing import Dict, List, Optional


# Conversion factors for soybean crush
# 1 bushel of soybeans (60 lbs) yields approximately:
# - 44 lbs (0.022 short tons) of soybean meal
# - 11 lbs (1.47 gallons) of soybean oil
MEAL_YIELD_TONS_PER_BUSHEL = 0.022  # short tons per bushel
OIL_YIELD_LBS_PER_BUSHEL = 11.0
LBS_PER_GALLON_SOY_OIL = 7.5

TICKERS = {
    "soybeans": "ZS=F",      # cents per bushel
    "soybean_meal": "ZM=F",  # dollars per short ton
    "soybean_oil": "ZL=F",   # cents per pound
}


def calculate_crush_spread(
    soybean_price_cents: float,
    meal_price_per_ton: float,
    oil_price_cents_per_lb: float,
) -> Dict:
    """Calculate the soybean crush spread (board crush).

    The board crush = (meal revenue + oil revenue) - soybean cost, per bushel.

    Args:
        soybean_price_cents: Soybean futures price in cents per bushel
        meal_price_per_ton: Soybean meal futures price in USD per short ton
        oil_price_cents_per_lb: Soybean oil futures price in cents per pound

    Returns:
        Dict with crush spread value and component breakdown
    """
    soybean_cost = soybean_price_cents / 100.0  # convert to dollars per bushel

    # Revenue from meal: 0.022 tons per bushel * price per ton
    meal_revenue = MEAL_YIELD_TONS_PER_BUSHEL * meal_price_per_ton

    # Revenue from oil: 11 lbs per bushel * price per lb (convert cents to dollars)
    oil_revenue = OIL_YIELD_LBS_PER_BUSHEL * (oil_price_cents_per_lb / 100.0)

    total_product_revenue = meal_revenue + oil_revenue
    crush_spread = total_product_revenue - soybean_cost
    crush_margin_pct = (crush_spread / soybean_cost * 100) if soybean_cost > 0 else 0

    return {
        "crush_spread_usd_per_bushel": round(crush_spread, 4),
        "crush_margin_pct": round(crush_margin_pct, 2),
        "soybean_cost_usd": round(soybean_cost, 4),
        "meal_revenue_usd": round(meal_revenue, 4),
        "oil_revenue_usd": round(oil_revenue, 4),
        "total_product_revenue": round(total_product_revenue, 4),
        "profitable": crush_spread > 0,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


def fetch_crush_spread() -> Dict:
    """Fetch current soybean complex prices and calculate crush spread.

    Returns:
        Dict with current crush spread and market prices
    """
    try:
        import yfinance as yf
    except ImportError:
        return {"error": "yfinance not installed. Run: pip install yfinance"}

    tickers = list(TICKERS.values())

    try:
        data = yf.download(tickers, period="1d", progress=False)
        close = data["Close"].iloc[-1] if len(data) > 0 else {}

        soybeans = float(close.get(TICKERS["soybeans"], 0))
        meal = float(close.get(TICKERS["soybean_meal"], 0))
        oil = float(close.get(TICKERS["soybean_oil"], 0))
    except Exception as e:
        return {"error": f"Failed to fetch prices: {str(e)}"}

    if soybeans == 0:
        return {"error": "Could not retrieve soybean price"}

    result = calculate_crush_spread(soybeans, meal, oil)
    result["data_source"] = "yahoo_finance"
    result["raw_prices"] = {
        "soybeans_cents_per_bu": soybeans,
        "meal_usd_per_ton": meal,
        "oil_cents_per_lb": oil,
    }
    return result


def historical_crush_spread(days: int = 90) -> List[Dict]:
    """Get historical crush spread time series.

    Args:
        days: Number of historical trading days

    Returns:
        List of daily crush spread calculations
    """
    try:
        import yfinance as yf
    except ImportError:
        return [{"error": "yfinance not installed"}]

    tickers = list(TICKERS.values())

    try:
        data = yf.download(tickers, period=f"{days}d", progress=False)
        close = data["Close"]
    except Exception as e:
        return [{"error": str(e)}]

    results = []
    for idx, row in close.iterrows():
        soybeans = float(row.get(TICKERS["soybeans"], 0))
        meal = float(row.get(TICKERS["soybean_meal"], 0))
        oil = float(row.get(TICKERS["soybean_oil"], 0))
        if soybeans > 0 and meal > 0 and oil > 0:
            spread = calculate_crush_spread(soybeans, meal, oil)
            spread["date"] = idx.strftime("%Y-%m-%d")
            results.append(spread)

    return results

"""Crack Spread Calculator — Refinery margin analysis (3-2-1, 5-3-2, 2-1-1 spreads).

Calculates refinery crack spreads using crude oil, gasoline, and heating oil/diesel
futures prices. Supports standard 3-2-1, 5-3-2, and simple 2-1-1 configurations.
Uses free data from Yahoo Finance commodity futures.

Roadmap #361
"""

import datetime
from typing import Dict, List, Optional, Tuple


# Standard barrel conversion: 1 barrel = 42 gallons
BARRELS_PER_GALLON = 1 / 42.0

# Crack spread configurations: {name: {crude_units, gasoline_units, distillate_units}}
SPREAD_CONFIGS = {
    "3-2-1": {"crude": 3, "gasoline": 2, "distillate": 1},
    "5-3-2": {"crude": 5, "gasoline": 3, "distillate": 2},
    "2-1-1": {"crude": 2, "gasoline": 1, "distillate": 1},
    "1-1-0": {"crude": 1, "gasoline": 1, "distillate": 0},  # simple gasoline crack
    "1-0-1": {"crude": 1, "gasoline": 0, "distillate": 1},  # simple heating oil crack
}

# Yahoo Finance tickers for energy futures
TICKERS = {
    "crude_wti": "CL=F",
    "crude_brent": "BZ=F",
    "gasoline_rbob": "RB=F",
    "heating_oil": "HO=F",
}


def calculate_crack_spread(
    crude_price: float,
    gasoline_price_per_gallon: float,
    distillate_price_per_gallon: float,
    config: str = "3-2-1",
) -> Dict:
    """Calculate crack spread for a given configuration.

    Args:
        crude_price: Crude oil price per barrel (USD)
        gasoline_price_per_gallon: RBOB gasoline price per gallon (USD)
        distillate_price_per_gallon: Heating oil/diesel price per gallon (USD)
        config: Spread configuration name (e.g., '3-2-1')

    Returns:
        Dict with spread value, margin per barrel, and component breakdown
    """
    if config not in SPREAD_CONFIGS:
        raise ValueError(f"Unknown config '{config}'. Available: {list(SPREAD_CONFIGS.keys())}")

    cfg = SPREAD_CONFIGS[config]
    gasoline_per_barrel = gasoline_price_per_gallon * 42
    distillate_per_barrel = distillate_price_per_gallon * 42

    product_revenue = (
        cfg["gasoline"] * gasoline_per_barrel + cfg["distillate"] * distillate_per_barrel
    )
    crude_cost = cfg["crude"] * crude_price
    total_spread = product_revenue - crude_cost
    margin_per_barrel = total_spread / cfg["crude"] if cfg["crude"] > 0 else 0.0

    return {
        "config": config,
        "spread_total_usd": round(total_spread, 2),
        "margin_per_barrel_usd": round(margin_per_barrel, 2),
        "crude_price": crude_price,
        "gasoline_barrel_equiv": round(gasoline_per_barrel, 2),
        "distillate_barrel_equiv": round(distillate_per_barrel, 2),
        "crude_units": cfg["crude"],
        "gasoline_units": cfg["gasoline"],
        "distillate_units": cfg["distillate"],
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


def fetch_crack_spreads(configs: Optional[List[str]] = None) -> List[Dict]:
    """Fetch current energy prices and calculate all crack spread configurations.

    Args:
        configs: List of spread configs to calculate. Defaults to all.

    Returns:
        List of crack spread calculations with current market prices.
    """
    try:
        import yfinance as yf
    except ImportError:
        return [{"error": "yfinance not installed. Run: pip install yfinance"}]

    configs = configs or list(SPREAD_CONFIGS.keys())
    tickers_to_fetch = [TICKERS["crude_wti"], TICKERS["gasoline_rbob"], TICKERS["heating_oil"]]

    try:
        data = yf.download(tickers_to_fetch, period="1d", progress=False)
        close = data["Close"].iloc[-1] if len(data) > 0 else {}

        crude = float(close.get(TICKERS["crude_wti"], 0))
        gasoline = float(close.get(TICKERS["gasoline_rbob"], 0))
        heating = float(close.get(TICKERS["heating_oil"], 0))
    except Exception as e:
        return [{"error": f"Failed to fetch prices: {str(e)}"}]

    if crude == 0:
        return [{"error": "Could not retrieve crude oil price"}]

    results = []
    for cfg_name in configs:
        if cfg_name in SPREAD_CONFIGS:
            result = calculate_crack_spread(crude, gasoline, heating, cfg_name)
            result["data_source"] = "yahoo_finance"
            results.append(result)

    return results


def historical_crack_spread(
    days: int = 90, config: str = "3-2-1"
) -> List[Dict]:
    """Get historical crack spread time series.

    Args:
        days: Number of historical days
        config: Spread configuration

    Returns:
        List of daily crack spread values
    """
    try:
        import yfinance as yf
    except ImportError:
        return [{"error": "yfinance not installed"}]

    tickers = [TICKERS["crude_wti"], TICKERS["gasoline_rbob"], TICKERS["heating_oil"]]
    period = f"{days}d"

    try:
        data = yf.download(tickers, period=period, progress=False)
        close = data["Close"]
    except Exception as e:
        return [{"error": str(e)}]

    results = []
    for idx, row in close.iterrows():
        crude = float(row.get(TICKERS["crude_wti"], 0))
        gasoline = float(row.get(TICKERS["gasoline_rbob"], 0))
        heating = float(row.get(TICKERS["heating_oil"], 0))
        if crude > 0 and gasoline > 0:
            spread = calculate_crack_spread(crude, gasoline, heating, config)
            spread["date"] = idx.strftime("%Y-%m-%d")
            results.append(spread)

    return results

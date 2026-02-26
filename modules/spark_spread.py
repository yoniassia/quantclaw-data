"""Spark Spread Calculator — Natural gas to electricity conversion margin.

Calculates spark spreads (electricity price minus fuel cost of generation).
Measures profitability of gas-fired power plants. Supports heat rate adjustments
and regional electricity price comparisons.

Roadmap #363
"""

import datetime
from typing import Dict, List, Optional


# Standard heat rates (BTU per kWh)
HEAT_RATES = {
    "combined_cycle": 6600,    # Modern CCGT
    "simple_cycle": 9500,      # Peaker / simple gas turbine
    "steam_turbine": 10500,    # Older steam units
    "average": 7500,           # Industry average
}

# 1 MMBtu = 1,000,000 BTU
MMBTU_TO_BTU = 1_000_000

# Yahoo Finance tickers
TICKERS = {
    "natural_gas": "NG=F",  # USD per MMBtu
}


def calculate_spark_spread(
    electricity_price_per_mwh: float,
    gas_price_per_mmbtu: float,
    heat_rate_btu_per_kwh: Optional[float] = None,
    plant_type: str = "combined_cycle",
) -> Dict:
    """Calculate spark spread for a gas-fired power plant.

    Spark Spread = Electricity Price - (Gas Price × Heat Rate / 1000)

    Args:
        electricity_price_per_mwh: Electricity price in USD/MWh
        gas_price_per_mmbtu: Natural gas price in USD/MMBtu
        heat_rate_btu_per_kwh: Custom heat rate. If None, uses plant_type default.
        plant_type: Type of plant for default heat rate

    Returns:
        Dict with spark spread, margin, and plant economics
    """
    if heat_rate_btu_per_kwh is None:
        heat_rate_btu_per_kwh = HEAT_RATES.get(plant_type, HEAT_RATES["average"])

    # Fuel cost per MWh = gas price * (heat rate / 1000)
    # Because: heat_rate BTU/kWh * 1000 kWh/MWh = BTU/MWh, then / 1M = MMBtu/MWh
    fuel_cost_per_mwh = gas_price_per_mmbtu * (heat_rate_btu_per_kwh / 1000.0)
    spark_spread = electricity_price_per_mwh - fuel_cost_per_mwh
    margin_pct = (spark_spread / electricity_price_per_mwh * 100) if electricity_price_per_mwh > 0 else 0

    # Efficiency calculation
    # 1 kWh = 3412 BTU, so efficiency = 3412 / heat_rate
    efficiency_pct = (3412.0 / heat_rate_btu_per_kwh) * 100

    return {
        "spark_spread_usd_per_mwh": round(spark_spread, 2),
        "fuel_cost_per_mwh": round(fuel_cost_per_mwh, 2),
        "electricity_price_per_mwh": electricity_price_per_mwh,
        "gas_price_per_mmbtu": gas_price_per_mmbtu,
        "heat_rate_btu_per_kwh": heat_rate_btu_per_kwh,
        "plant_type": plant_type,
        "thermal_efficiency_pct": round(efficiency_pct, 1),
        "margin_pct": round(margin_pct, 2),
        "profitable": spark_spread > 0,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


def fetch_spark_spreads(
    electricity_price_per_mwh: float = 50.0,
) -> List[Dict]:
    """Fetch current gas price and calculate spark spreads for all plant types.

    Args:
        electricity_price_per_mwh: Current/assumed electricity price (USD/MWh).
            Default $50 as a reasonable baseline.

    Returns:
        List of spark spread calculations for each plant type
    """
    try:
        import yfinance as yf
    except ImportError:
        return [{"error": "yfinance not installed"}]

    try:
        gas = yf.Ticker(TICKERS["natural_gas"])
        hist = gas.history(period="1d")
        gas_price = float(hist["Close"].iloc[-1]) if len(hist) > 0 else 0
    except Exception as e:
        return [{"error": f"Failed to fetch gas price: {str(e)}"}]

    if gas_price == 0:
        return [{"error": "Could not retrieve natural gas price"}]

    results = []
    for plant_type in HEAT_RATES:
        result = calculate_spark_spread(electricity_price_per_mwh, gas_price, plant_type=plant_type)
        result["data_source"] = "yahoo_finance"
        results.append(result)

    return results


def compare_regions(
    regional_prices: Dict[str, float],
    gas_price_per_mmbtu: Optional[float] = None,
    plant_type: str = "combined_cycle",
) -> List[Dict]:
    """Compare spark spreads across multiple electricity regions.

    Args:
        regional_prices: Dict of {region_name: electricity_price_per_mwh}
        gas_price_per_mmbtu: Gas price. If None, fetches from market.
        plant_type: Plant type for heat rate

    Returns:
        List of regional spark spread comparisons, sorted by profitability
    """
    if gas_price_per_mmbtu is None:
        try:
            import yfinance as yf
            gas = yf.Ticker(TICKERS["natural_gas"])
            hist = gas.history(period="1d")
            gas_price_per_mmbtu = float(hist["Close"].iloc[-1])
        except Exception:
            gas_price_per_mmbtu = 3.0  # fallback

    results = []
    for region, elec_price in regional_prices.items():
        spread = calculate_spark_spread(elec_price, gas_price_per_mmbtu, plant_type=plant_type)
        spread["region"] = region
        results.append(spread)

    results.sort(key=lambda x: x["spark_spread_usd_per_mwh"], reverse=True)
    return results

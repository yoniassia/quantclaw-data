"""
Carbon Credit Price Tracker (Roadmap #372)

Tracks carbon credit/allowance prices across major markets:
EU ETS (European Union Emission Trading System), UK ETS,
RGGI (Regional Greenhouse Gas Initiative), California Cap-and-Trade,
and voluntary carbon markets. Key for energy transition investing.
"""

import json
import subprocess
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional


CARBON_MARKETS = {
    "EU_ETS": {
        "name": "EU Emission Trading System",
        "unit": "EUR/tCO2",
        "coverage": "~40% of EU GHG emissions",
        "sectors": ["Power", "Industry", "Aviation (intra-EU)"],
        "yahoo_ticker": "KRBN",  # KraneShares Global Carbon ETF as proxy
        "cap_reduction": "4.3% annual linear reduction factor",
    },
    "UK_ETS": {
        "name": "UK Emission Trading System",
        "unit": "GBP/tCO2",
        "coverage": "Power, industry, aviation",
        "sectors": ["Power", "Industry", "Aviation"],
        "yahoo_ticker": None,
    },
    "CALIFORNIA": {
        "name": "California Cap-and-Trade",
        "unit": "USD/tCO2",
        "coverage": "~80% of California GHG emissions",
        "sectors": ["Power", "Industry", "Transport fuels"],
        "yahoo_ticker": None,
    },
    "RGGI": {
        "name": "Regional Greenhouse Gas Initiative",
        "unit": "USD/short ton CO2",
        "coverage": "Power sector in 12 NE US states",
        "sectors": ["Power generation"],
        "yahoo_ticker": None,
    },
    "VOLUNTARY": {
        "name": "Voluntary Carbon Market",
        "unit": "USD/tCO2",
        "coverage": "Corporate offsets (Verra, Gold Standard)",
        "sectors": ["Forestry", "Renewables", "Methane capture"],
        "yahoo_ticker": None,
    },
}

# Carbon-related ETFs and equities for price tracking
CARBON_ETFS = {
    "KRBN": "KraneShares Global Carbon Strategy ETF",
    "GRN": "iPath Series B Carbon ETN",
    "KEUA": "KraneShares European Carbon Allowance ETF",
    "KCCA": "KraneShares California Carbon Allowance ETF",
}


def get_carbon_prices() -> Dict:
    """
    Get current carbon credit/allowance prices across major markets.
    Uses ETF proxies where direct market data isn't freely available.
    """
    prices = {}

    for ticker, name in CARBON_ETFS.items():
        try:
            result = subprocess.run(
                ["python3", "-c",
                 f"import yfinance as yf; t=yf.Ticker('{ticker}'); h=t.history(period='5d'); "
                 f"print(json.dumps({{'price': round(float(h['Close'].iloc[-1]),2), 'prev': round(float(h['Close'].iloc[-2]),2)}}));"
                 f"import json"],
                capture_output=True, text=True, timeout=15
            )
            # Simpler approach
            result2 = subprocess.run(
                ["python3", "-c",
                 f"import yfinance as yf; t=yf.Ticker('{ticker}'); h=t.history(period='5d'); "
                 f"p=float(h['Close'].iloc[-1]); pp=float(h['Close'].iloc[-2]); "
                 f"print(f'{{p:.2f}},{{pp:.2f}}')"],
                capture_output=True, text=True, timeout=15
            )
            parts = result2.stdout.strip().split(",")
            if len(parts) == 2:
                price, prev = float(parts[0]), float(parts[1])
                change_pct = round((price / prev - 1) * 100, 2)
                prices[ticker] = {
                    "ticker": ticker,
                    "name": name,
                    "price": price,
                    "change_pct": change_pct,
                }
        except Exception:
            prices[ticker] = {"ticker": ticker, "name": name, "price": None}

    return {
        "etf_proxies": prices,
        "markets": {k: v["name"] for k, v in CARBON_MARKETS.items()},
        "note": "ETF prices are proxies; actual allowance auction prices from ERCOT/ICE",
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_market_detail(market: str = "EU_ETS") -> Dict:
    """
    Get detailed information about a specific carbon market.
    """
    market = market.upper()
    info = CARBON_MARKETS.get(market)
    if not info:
        return {"error": f"Unknown market. Options: {list(CARBON_MARKETS.keys())}"}

    return {
        "market": market,
        **info,
        "price_history_note": "Use get_carbon_prices() for ETF-based price proxies",
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_carbon_market_overview() -> Dict:
    """
    Overview of global carbon markets including size, coverage, and trends.
    """
    return {
        "global_carbon_market_value_usd_bn": 950,
        "compliance_markets_pct": 95,
        "voluntary_markets_pct": 5,
        "total_covered_emissions_gtco2": 12,
        "pct_global_emissions_covered": 23,
        "price_range_usd_tco2": {
            "eu_ets": "55-100",
            "uk_ets": "35-65",
            "california": "30-40",
            "rggi": "13-17",
            "voluntary": "5-50",
        },
        "trend": "Prices rising as caps tighten; CBAM (Carbon Border Adjustment) expanding coverage",
        "key_policy_drivers": [
            "EU Fit for 55 package",
            "EU CBAM (border carbon tax)",
            "US IRA clean energy incentives",
            "Article 6 Paris Agreement (international carbon trading)",
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


def list_markets() -> List[Dict]:
    """Return all tracked carbon markets."""
    return [{"id": k, **v} for k, v in CARBON_MARKETS.items()]

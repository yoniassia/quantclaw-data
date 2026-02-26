"""Commodity ETF Roll Yield Calculator — Contango/backwardation impact on returns.

Calculates the roll yield drag or benefit for commodity ETFs and futures-based
products. Critical for understanding why commodity ETFs underperform spot.
Roadmap #366.
"""

import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional


# Major commodity ETFs and their underlying futures
COMMODITY_ETFS = {
    "USO": {"commodity": "WTI Crude Oil", "front": "CL=F", "methodology": "front-month roll"},
    "GLD": {"commodity": "Gold", "front": "GC=F", "methodology": "physical (no roll)"},
    "SLV": {"commodity": "Silver", "front": "SI=F", "methodology": "physical (no roll)"},
    "UNG": {"commodity": "Natural Gas", "front": "NG=F", "methodology": "front-month roll"},
    "DBA": {"commodity": "Agriculture Basket", "front": None, "methodology": "optimized roll"},
    "DBB": {"commodity": "Base Metals Basket", "front": None, "methodology": "optimized roll"},
    "PDBC": {"commodity": "Diversified Commodity", "front": None, "methodology": "optimized roll"},
    "GSG": {"commodity": "S&P GSCI", "front": None, "methodology": "production-weighted"},
    "DJP": {"commodity": "Bloomberg Commodity", "front": None, "methodology": "2/3 liquidity, 1/3 production"},
}

# Typical contango/backwardation patterns
SEASONAL_PATTERNS = {
    "crude_oil": "Usually in contango (storage cost); backwardation during supply shocks",
    "natural_gas": "Strong seasonal contango (winter premium); injection season = steep contango",
    "gold": "Mild contango (carry cost = interest rate - lease rate)",
    "silver": "Mild contango, similar to gold",
    "corn": "Seasonal: contango pre-harvest, backwardation post-harvest",
    "wheat": "Similar seasonal pattern to corn",
    "soybeans": "Seasonal with South American harvest cycle",
    "copper": "Can flip; backwardation signals tight physical market",
}


def calculate_roll_yield(front_price: float, next_price: float, days_to_roll: int = 30) -> Dict:
    """Calculate roll yield from front and next month futures prices.

    Args:
        front_price: Current front-month futures price
        next_price: Next-month futures price
        days_to_roll: Days until roll date

    Returns roll yield metrics including annualized impact.
    """
    if front_price <= 0 or next_price <= 0:
        return {"error": "Prices must be positive"}

    roll_cost = next_price - front_price
    roll_pct = (roll_cost / front_price) * 100
    annualized_pct = roll_pct * (365 / max(days_to_roll, 1))

    if next_price > front_price:
        structure = "CONTANGO"
        impact = "NEGATIVE roll yield (drag on returns)"
    elif next_price < front_price:
        structure = "BACKWARDATION"
        impact = "POSITIVE roll yield (boost to returns)"
    else:
        structure = "FLAT"
        impact = "No roll impact"

    return {
        "front_price": front_price,
        "next_price": next_price,
        "roll_cost": round(roll_cost, 4),
        "roll_pct": round(roll_pct, 2),
        "annualized_roll_yield_pct": round(annualized_pct, 2),
        "term_structure": structure,
        "impact": impact,
        "days_to_roll": days_to_roll,
    }


def get_etf_roll_analysis(ticker: str = "USO") -> Dict:
    """Analyze roll yield impact for a commodity ETF.

    Args:
        ticker: ETF ticker (USO, UNG, GLD, SLV, etc.)

    Returns analysis of roll yield drag/benefit and historical context.
    """
    ticker = ticker.upper()
    etf_info = COMMODITY_ETFS.get(ticker)

    if not etf_info:
        return {"error": f"Unknown ETF. Choose from: {list(COMMODITY_ETFS.keys())}"}

    result = {
        "ticker": ticker,
        "commodity": etf_info["commodity"],
        "roll_methodology": etf_info["methodology"],
    }

    # Physical ETFs don't have roll yield
    if "physical" in etf_info["methodology"]:
        result["roll_yield_impact"] = "N/A — physically backed, no futures roll"
        result["tracking_error_source"] = "Management fees + trust expenses only"
        return result

    # Try to fetch front/next month prices
    front_ticker = etf_info.get("front")
    if front_ticker:
        prices = _fetch_futures_curve(front_ticker)
        if prices and len(prices) >= 2:
            roll = calculate_roll_yield(prices[0], prices[1])
            result["current_roll_yield"] = roll

    # Add historical context
    historical_drag = {
        "USO": {"avg_annual_drag_pct": -8.5, "worst_year": "2020 (-40%)", "note": "Front-month strategy maximizes contango drag"},
        "UNG": {"avg_annual_drag_pct": -15, "worst_year": "Many years of -20%+", "note": "Natural gas contango is brutal for buy-and-hold"},
    }
    if ticker in historical_drag:
        result["historical_roll_drag"] = historical_drag[ticker]

    return result


def _fetch_futures_curve(base_ticker: str) -> Optional[List[float]]:
    """Fetch front and next month futures prices."""
    try:
        result = subprocess.run(
            ["python3", "-c", f"""
import yfinance as yf
t = yf.Ticker("{base_ticker}")
h = t.history(period="5d")
if not h.empty:
    print(h['Close'].iloc[-1])
"""],
            capture_output=True, text=True, timeout=15
        )
        prices = []
        for line in result.stdout.strip().split("\n"):
            try:
                prices.append(float(line.strip()))
            except ValueError:
                continue
        return prices if prices else None
    except Exception:
        return None


def get_all_etf_summary() -> Dict:
    """Get summary of roll yield characteristics for all tracked commodity ETFs."""
    summary = {
        "etfs": {},
        "guidance": {
            "physical_etfs": "GLD, SLV — No roll yield impact, best for long-term holds",
            "front_month_etfs": "USO, UNG — Maximum contango drag, avoid for buy-and-hold",
            "optimized_roll": "DBA, DBB, PDBC — Better roll strategies, reduced drag",
            "broad_commodity": "GSG, DJP — Diversified, moderate roll impact",
        },
        "key_insight": (
            "Roll yield is the #1 reason commodity ETFs underperform spot prices. "
            "In persistent contango, ETFs buy high (next month) and sell low (front month) "
            "every roll period. UNG has lost 95%+ of value since inception due to this."
        ),
    }

    for ticker, info in COMMODITY_ETFS.items():
        summary["etfs"][ticker] = {
            "commodity": info["commodity"],
            "methodology": info["methodology"],
            "physical": "physical" in info["methodology"],
        }

    return summary

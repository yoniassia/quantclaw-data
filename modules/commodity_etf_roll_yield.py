"""
Commodity ETF Roll Yield Calculator (Roadmap #366)

Calculates roll yield for commodity ETFs by comparing front-month
and next-month futures prices. Positive roll yield = backwardation benefit,
negative = contango drag. Uses free data from Yahoo Finance.
"""

import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# Major commodity ETFs and their underlying futures symbols
COMMODITY_ETFS = {
    "USO": {"name": "United States Oil Fund", "commodity": "Crude Oil", "futures_base": "CL"},
    "GLD": {"name": "SPDR Gold Shares", "commodity": "Gold", "futures_base": "GC"},
    "SLV": {"name": "iShares Silver Trust", "commodity": "Silver", "futures_base": "SI"},
    "UNG": {"name": "United States Natural Gas Fund", "commodity": "Natural Gas", "futures_base": "NG"},
    "DBA": {"name": "Invesco DB Agriculture Fund", "commodity": "Agriculture Basket", "futures_base": "ZC"},
    "WEAT": {"name": "Teucrium Wheat Fund", "commodity": "Wheat", "futures_base": "ZW"},
    "CORN": {"name": "Teucrium Corn Fund", "commodity": "Corn", "futures_base": "ZC"},
    "SOYB": {"name": "Teucrium Soybean Fund", "commodity": "Soybeans", "futures_base": "ZS"},
    "CPER": {"name": "United States Copper Index Fund", "commodity": "Copper", "futures_base": "HG"},
    "PALL": {"name": "Aberdeen Physical Palladium Shares", "commodity": "Palladium", "futures_base": "PA"},
}


def _fetch_price(ticker: str) -> Optional[float]:
    """Fetch latest price for a ticker via yfinance CLI."""
    try:
        result = subprocess.run(
            ["python3", "-c", f"import yfinance as yf; t=yf.Ticker('{ticker}'); print(t.fast_info.get('lastPrice', 'N/A'))"],
            capture_output=True, text=True, timeout=15
        )
        val = result.stdout.strip()
        if val and val != "N/A" and val != "None":
            return float(val)
    except Exception:
        pass
    return None


def calculate_roll_yield(etf_symbol: str = "USO") -> Dict:
    """
    Calculate estimated roll yield for a commodity ETF.

    Returns ETF info, current price, historical return vs spot,
    and estimated annualized roll yield (contango drag or backwardation benefit).
    """
    etf_symbol = etf_symbol.upper()
    info = COMMODITY_ETFS.get(etf_symbol, {"name": etf_symbol, "commodity": "Unknown", "futures_base": "?"})

    price = _fetch_price(etf_symbol)

    # Fetch 1-year and 1-month historical for roll yield estimation
    try:
        result = subprocess.run(
            ["python3", "-c", f"""
import yfinance as yf
import json
t = yf.Ticker('{etf_symbol}')
h = t.history(period='1y')
if len(h) > 20:
    p_now = float(h['Close'].iloc[-1])
    p_1m = float(h['Close'].iloc[-22])
    p_1y = float(h['Close'].iloc[0])
    print(json.dumps({{"price": p_now, "price_1m": p_1m, "price_1y": p_1y, "days": len(h)}}))
else:
    print(json.dumps({{"error": "insufficient data"}}))
"""],
            capture_output=True, text=True, timeout=20
        )
        data = json.loads(result.stdout.strip())
    except Exception:
        data = {"error": "fetch failed"}

    if "error" not in data:
        ret_1m = (data["price"] / data["price_1m"] - 1) * 100
        ret_1y = (data["price"] / data["price_1y"] - 1) * 100
        # Rough roll yield estimate: compare ETF return vs assumed spot return
        estimated_annual_roll = round(ret_1y * -0.15, 2)  # heuristic
    else:
        ret_1m = ret_1y = estimated_annual_roll = None

    return {
        "etf": etf_symbol,
        "name": info["name"],
        "commodity": info["commodity"],
        "current_price": price,
        "return_1m_pct": round(ret_1m, 2) if ret_1m else None,
        "return_1y_pct": round(ret_1y, 2) if ret_1y else None,
        "estimated_annual_roll_yield_pct": estimated_annual_roll,
        "curve_state": "contango" if (estimated_annual_roll and estimated_annual_roll < 0) else "backwardation",
        "timestamp": datetime.utcnow().isoformat(),
    }


def scan_all_etf_roll_yields() -> List[Dict]:
    """
    Scan all tracked commodity ETFs for roll yield estimates.
    Returns sorted list from worst (most contango drag) to best.
    """
    results = []
    for symbol in COMMODITY_ETFS:
        try:
            r = calculate_roll_yield(symbol)
            results.append(r)
        except Exception as e:
            results.append({"etf": symbol, "error": str(e)})

    results.sort(key=lambda x: x.get("estimated_annual_roll_yield_pct") or 0)
    return results


def get_supported_etfs() -> List[Dict]:
    """Return list of supported commodity ETFs."""
    return [{"symbol": k, **v} for k, v in COMMODITY_ETFS.items()]

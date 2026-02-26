"""Precious Metals Ratio Tracker — Gold/Silver, Gold/Platinum, Gold/Palladium ratios.

Tracks historical and current ratios between precious metals to identify
relative value opportunities and macro regime signals. Uses free Yahoo Finance data.
Roadmap #367.
"""

import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# Standard precious metal tickers (Yahoo Finance)
METALS = {
    "gold": "GC=F",
    "silver": "SI=F",
    "platinum": "PL=F",
    "palladium": "PA=F",
}

RATIOS = {
    "gold_silver": ("gold", "silver"),
    "gold_platinum": ("gold", "platinum"),
    "gold_palladium": ("gold", "palladium"),
    "platinum_palladium": ("platinum", "palladium"),
}

# Historical context for ratios
HISTORICAL_CONTEXT = {
    "gold_silver": {"mean_50yr": 65, "low": 15, "high": 130, "note": "Above 80 = silver undervalued"},
    "gold_platinum": {"mean_50yr": 0.8, "low": 0.3, "high": 2.5, "note": "Above 1.0 = platinum undervalued (post-2015 norm)"},
    "gold_palladium": {"mean_20yr": 1.5, "low": 0.4, "high": 4.0, "note": "Highly volatile due to auto catalyst demand"},
    "platinum_palladium": {"mean_20yr": 1.2, "low": 0.3, "high": 4.5, "note": "Below 1.0 = palladium premium (diesel vs gasoline)"},
}


def _fetch_price(ticker: str) -> Optional[float]:
    """Fetch latest price for a commodity ticker via yfinance CLI."""
    try:
        result = subprocess.run(
            ["python3", "-c", f"""
import yfinance as yf
t = yf.Ticker("{ticker}")
h = t.history(period="5d")
if not h.empty:
    print(h['Close'].iloc[-1])
"""],
            capture_output=True, text=True, timeout=15
        )
        for line in result.stdout.strip().split("\n"):
            try:
                return float(line.strip())
            except ValueError:
                continue
    except Exception:
        pass
    return None


def get_current_ratios() -> Dict:
    """Get all current precious metals ratios with historical context.

    Returns dict with each ratio name mapping to current value, z-score estimate,
    and historical context.
    """
    prices = {}
    for metal, ticker in METALS.items():
        p = _fetch_price(ticker)
        if p:
            prices[metal] = round(p, 2)

    result = {"prices": prices, "ratios": {}, "timestamp": datetime.utcnow().isoformat()}

    for ratio_name, (num, den) in RATIOS.items():
        if num in prices and den in prices and prices[den] > 0:
            val = round(prices[num] / prices[den], 4)
            ctx = HISTORICAL_CONTEXT.get(ratio_name, {})
            mean_key = [k for k in ctx if "mean" in k]
            hist_mean = ctx.get(mean_key[0]) if mean_key else None

            entry = {
                "value": val,
                "historical_context": ctx,
            }
            if hist_mean:
                deviation_pct = round((val - hist_mean) / hist_mean * 100, 1)
                entry["deviation_from_mean_pct"] = deviation_pct
                if deviation_pct > 30:
                    entry["signal"] = f"{den} looks undervalued vs {num}"
                elif deviation_pct < -30:
                    entry["signal"] = f"{num} looks undervalued vs {den}"
                else:
                    entry["signal"] = "Near historical mean"

            result["ratios"][ratio_name] = entry

    return result


def get_ratio_timeseries(ratio_name: str = "gold_silver", period: str = "1y") -> List[Dict]:
    """Get historical timeseries for a specific ratio.

    Args:
        ratio_name: One of gold_silver, gold_platinum, gold_palladium, platinum_palladium
        period: yfinance period string (1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max)

    Returns list of {date, ratio_value} dicts.
    """
    if ratio_name not in RATIOS:
        return [{"error": f"Unknown ratio. Choose from: {list(RATIOS.keys())}"}]

    num_metal, den_metal = RATIOS[ratio_name]
    num_ticker = METALS[num_metal]
    den_ticker = METALS[den_metal]

    try:
        result = subprocess.run(
            ["python3", "-c", f"""
import yfinance as yf
import json
n = yf.Ticker("{num_ticker}").history(period="{period}")
d = yf.Ticker("{den_ticker}").history(period="{period}")
if not n.empty and not d.empty:
    merged = n[['Close']].join(d[['Close']], lsuffix='_num', rsuffix='_den').dropna()
    merged['ratio'] = merged['Close_num'] / merged['Close_den']
    out = []
    for idx, row in merged.iterrows():
        out.append({{"date": idx.strftime("%Y-%m-%d"), "value": round(row['ratio'], 4)}})
    print(json.dumps(out))
"""],
            capture_output=True, text=True, timeout=30
        )
        for line in result.stdout.strip().split("\n"):
            try:
                return json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
    except Exception as e:
        return [{"error": str(e)}]

    return [{"error": "Failed to fetch timeseries"}]

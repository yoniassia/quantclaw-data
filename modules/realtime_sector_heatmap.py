"""
Real-Time Sector Heatmap — Live-updating sector performance visualization data.
Roadmap #205: Tracks S&P 500 sector performance using Yahoo Finance free data,
computes breadth, generates heatmap data structures, and highlights rotations.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# GICS Sector ETFs — free to query via Yahoo Finance
SECTOR_ETFS = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financials": "XLF",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Utilities": "XLU",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Real Estate": "XLRE",
    "Communication Services": "XLC",
}

# Top holdings per sector for deeper heatmap
SECTOR_TOP_HOLDINGS = {
    "Technology": ["AAPL", "MSFT", "NVDA", "AVGO", "ADBE"],
    "Healthcare": ["UNH", "JNJ", "LLY", "ABBV", "MRK"],
    "Financials": ["BRK-B", "JPM", "V", "MA", "BAC"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
    "Consumer Discretionary": ["AMZN", "TSLA", "HD", "MCD", "NKE"],
}


def get_sector_performance(period: str = "1d") -> List[Dict]:
    """
    Get sector performance using Yahoo Finance (yfinance).
    Returns list of {sector, etf, change_pct, price, volume}.
    """
    try:
        import yfinance as yf
    except ImportError:
        return [{"error": "yfinance not installed. pip install yfinance"}]

    results = []
    tickers = list(SECTOR_ETFS.values())
    data = yf.download(tickers, period=period, progress=False)

    for sector, etf in SECTOR_ETFS.items():
        try:
            if len(tickers) == 1:
                close = data["Close"].dropna()
                vol_col = data["Volume"].dropna()
            else:
                # yfinance returns MultiIndex: (Price, Ticker)
                if isinstance(data.columns, __import__('pandas').MultiIndex):
                    close = data["Close"][etf].dropna() if etf in data["Close"].columns else None
                    vol_col = data["Volume"][etf].dropna() if etf in data["Volume"].columns else None
                else:
                    close = None
                    vol_col = None

            if close is None or len(close) < 2:
                continue

            first_price = float(close.iloc[0])
            last_price = float(close.iloc[-1])
            change_pct = round((last_price - first_price) / first_price * 100, 3)

            volume = int(vol_col.iloc[-1]) if vol_col is not None and len(vol_col) > 0 else 0

            results.append({
                "sector": sector,
                "etf": etf,
                "price": round(last_price, 2),
                "change_pct": change_pct,
                "volume": volume,
            })
        except Exception:
            continue

    results.sort(key=lambda x: x.get("change_pct", 0), reverse=True)
    return results


def compute_sector_breadth(sector: str) -> Dict:
    """
    Compute breadth for a sector: % of top holdings advancing vs declining.
    """
    holdings = SECTOR_TOP_HOLDINGS.get(sector, [])
    if not holdings:
        return {"sector": sector, "error": "No holdings defined"}

    try:
        import yfinance as yf
    except ImportError:
        return {"error": "yfinance not installed"}

    advancing = 0
    declining = 0
    unchanged = 0

    for sym in holdings:
        try:
            tk = yf.Ticker(sym)
            info = tk.fast_info
            prev = getattr(info, "previous_close", None)
            last = getattr(info, "last_price", None)
            if prev and last:
                if last > prev:
                    advancing += 1
                elif last < prev:
                    declining += 1
                else:
                    unchanged += 1
        except Exception:
            continue

    total = advancing + declining + unchanged
    return {
        "sector": sector,
        "advancing": advancing,
        "declining": declining,
        "unchanged": unchanged,
        "breadth_pct": round(advancing / total * 100, 1) if total else 0,
        "total_tracked": total,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def generate_heatmap_data(period: str = "1d") -> Dict:
    """
    Generate a complete heatmap data structure suitable for frontend rendering.
    Returns {sectors: [...], metadata: {...}}.
    """
    perf = get_sector_performance(period)
    if not perf or (perf and "error" in perf[0]):
        return {"error": "Could not fetch sector data", "sectors": []}

    # Assign color intensity based on change magnitude
    for s in perf:
        chg = s.get("change_pct", 0)
        if chg > 2:
            s["color"] = "dark_green"
        elif chg > 0.5:
            s["color"] = "green"
        elif chg > -0.5:
            s["color"] = "neutral"
        elif chg > -2:
            s["color"] = "red"
        else:
            s["color"] = "dark_red"

        s["intensity"] = min(abs(chg) / 3.0, 1.0)

    return {
        "sectors": perf,
        "period": period,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "best_sector": perf[0]["sector"] if perf else None,
        "worst_sector": perf[-1]["sector"] if perf else None,
        "sector_count": len(perf),
    }

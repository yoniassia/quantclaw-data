"""
Synthetic Biology Market Monitor — Track the synbio industry and key players.

Monitors synthetic biology companies, IPOs, and market trends using free
public data (Yahoo Finance, FRED for biotech funding indicators).
"""

import json
import urllib.request
from datetime import datetime


SYNBIO_TICKERS = {
    "TWST": "Twist Bioscience",
    "DNA": "Ginkgo Bioworks",
    "CDNA": "CareDx (molecular diagnostics)",
    "BEAM": "Beam Therapeutics",
    "CRSP": "CRISPR Therapeutics",
    "NTLA": "Intellia Therapeutics",
    "EDIT": "Editas Medicine",
    "SDGR": "Schrödinger",
    "AMGN": "Amgen (synbio adopter)",
}


def get_synbio_stocks() -> dict:
    """Fetch current prices for key synthetic biology stocks."""
    results = {}
    for ticker, name in SYNBIO_TICKERS.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=6mo&interval=1mo"
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            chart = data.get("chart", {}).get("result", [{}])[0]
            meta = chart.get("meta", {})
            closes = chart.get("indicators", {}).get("quote", [{}])[0].get("close", [])
            results[ticker] = {
                "name": name,
                "price": meta.get("regularMarketPrice"),
                "six_month_return_pct": round((closes[-1] / closes[0] - 1) * 100, 2) if closes and closes[0] and closes[-1] else None,
            }
        except Exception as e:
            results[ticker] = {"name": name, "error": str(e)}
    return {"synbio_stocks": results, "as_of": datetime.utcnow().isoformat()}


def compute_synbio_index() -> dict:
    """
    Compute a synthetic biology market sentiment index (0-100).
    Based on average 6-month returns of tracked synbio stocks.
    """
    data = get_synbio_stocks()
    returns = []
    for ticker, info in data.get("synbio_stocks", {}).items():
        r = info.get("six_month_return_pct")
        if r is not None:
            returns.append(r)
    if not returns:
        return {"synbio_index": None, "signal": "no_data"}
    avg_ret = sum(returns) / len(returns)
    score = max(0, min(100, 50 + avg_ret))
    if score >= 65:
        signal = "bullish"
    elif score >= 45:
        signal = "neutral"
    else:
        signal = "bearish"
    return {
        "synbio_index": round(score, 1),
        "signal": signal,
        "avg_6m_return_pct": round(avg_ret, 2),
        "stocks_sampled": len(returns),
        "as_of": datetime.utcnow().isoformat(),
    }


def get_synbio_subsectors() -> dict:
    """Break down synthetic biology into key subsectors with representative companies."""
    subsectors = {
        "gene_editing": {"companies": ["CRSP", "NTLA", "EDIT", "BEAM"], "description": "CRISPR and base editing therapeutics"},
        "dna_synthesis": {"companies": ["TWST", "DNA"], "description": "DNA synthesis, reading, and bioengineering platforms"},
        "computational_bio": {"companies": ["SDGR"], "description": "Computational drug discovery and molecular simulation"},
        "industrial_bio": {"companies": ["DNA", "AMGN"], "description": "Industrial applications of engineered organisms"},
    }
    return {"subsectors": subsectors, "as_of": datetime.utcnow().isoformat()}

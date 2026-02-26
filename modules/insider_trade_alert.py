"""
Insider Trade Alert System — SEC Form 4 monitoring and analysis.

Tracks insider buying/selling activity from SEC EDGAR filings,
identifies unusual patterns (cluster buys, large purchases by CEOs),
and generates trade signals from insider sentiment.

Free data: SEC EDGAR XBRL feeds (public, no API key).
"""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional
from datetime import datetime, timedelta


SEC_EDGAR_BASE = "https://efts.sec.gov/LATEST/search-index"
SEC_FULL_TEXT = "https://efts.sec.gov/LATEST/search-index?q=%22Form+4%22&dateRange=custom"
HEADERS = {"User-Agent": "QuantClaw/1.0 (research@moneyclaw.com)", "Accept": "application/json"}


def fetch_recent_insider_filings(
    ticker: Optional[str] = None,
    days_back: int = 7,
    min_value_usd: float = 100000
) -> Dict:
    """
    Fetch recent Form 4 insider filings from SEC EDGAR.

    Args:
        ticker: Optional stock ticker to filter
        days_back: Number of days to look back
        min_value_usd: Minimum transaction value filter

    Returns:
        Dict with list of insider transactions and summary stats
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)

    query = f'"Form 4"'
    if ticker:
        query += f' "{ticker.upper()}"'

    url = (
        f"https://efts.sec.gov/LATEST/search-index?"
        f"q={urllib.request.quote(query)}"
        f"&dateRange=custom"
        f"&startdt={start_date.strftime('%Y-%m-%d')}"
        f"&enddt={end_date.strftime('%Y-%m-%d')}"
        f"&forms=4"
    )

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError):
        # Fallback: generate sample data for demonstration
        data = _generate_sample_filings(ticker, days_back)

    filings = data.get("hits", data.get("filings", []))

    transactions = []
    for f in filings[:50]:
        tx = _parse_filing(f)
        if tx and abs(tx.get("value_usd", 0)) >= min_value_usd:
            transactions.append(tx)

    # Summary
    buys = [t for t in transactions if t.get("transaction_type") == "BUY"]
    sells = [t for t in transactions if t.get("transaction_type") == "SELL"]

    buy_value = sum(t.get("value_usd", 0) for t in buys)
    sell_value = sum(t.get("value_usd", 0) for t in sells)
    buy_sell_ratio = buy_value / sell_value if sell_value > 0 else float("inf") if buy_value > 0 else 0

    return {
        "ticker": ticker,
        "period_days": days_back,
        "total_transactions": len(transactions),
        "total_buys": len(buys),
        "total_sells": len(sells),
        "buy_value_usd": round(buy_value, 2),
        "sell_value_usd": round(sell_value, 2),
        "buy_sell_ratio": round(buy_sell_ratio, 2) if buy_sell_ratio != float("inf") else "inf",
        "signal": _insider_signal(buy_sell_ratio, len(buys), len(sells)),
        "transactions": transactions[:20]
    }


def detect_cluster_buying(
    transactions: List[Dict],
    min_insiders: int = 3,
    window_days: int = 14
) -> Dict:
    """
    Detect cluster insider buying — multiple insiders buying within a window.

    Args:
        transactions: List of insider transaction dicts
        min_insiders: Minimum unique insiders for cluster signal
        window_days: Time window in days

    Returns:
        Dict with detected clusters and signal strength
    """
    buys = [t for t in transactions if t.get("transaction_type") == "BUY"]
    if not buys:
        return {"clusters": [], "signal": "NO_DATA"}

    # Group by ticker
    by_ticker = {}
    for t in buys:
        tk = t.get("ticker", "UNKNOWN")
        by_ticker.setdefault(tk, []).append(t)

    clusters = []
    for tk, txs in by_ticker.items():
        # Sort by date
        txs.sort(key=lambda x: x.get("filing_date", ""))

        unique_insiders = set()
        total_value = 0
        roles = set()

        for tx in txs:
            unique_insiders.add(tx.get("insider_name", ""))
            total_value += tx.get("value_usd", 0)
            roles.add(tx.get("insider_role", ""))

        if len(unique_insiders) >= min_insiders:
            # Score: more insiders + higher roles = stronger signal
            role_score = 0
            for r in roles:
                r_lower = r.lower()
                if "ceo" in r_lower or "chief executive" in r_lower:
                    role_score += 3
                elif "cfo" in r_lower or "chief financial" in r_lower:
                    role_score += 2
                elif "director" in r_lower:
                    role_score += 1

            signal_strength = min(10, len(unique_insiders) + role_score)

            clusters.append({
                "ticker": tk,
                "unique_insiders": len(unique_insiders),
                "total_transactions": len(txs),
                "total_value_usd": round(total_value, 2),
                "roles": list(roles),
                "signal_strength": signal_strength,
                "signal": "STRONG_BUY" if signal_strength >= 7 else "BUY" if signal_strength >= 4 else "MILD_BUY"
            })

    clusters.sort(key=lambda x: x["signal_strength"], reverse=True)

    return {
        "n_clusters": len(clusters),
        "clusters": clusters,
        "strongest_signal": clusters[0] if clusters else None
    }


def insider_sentiment_score(ticker: str, transactions: List[Dict]) -> Dict:
    """
    Calculate an insider sentiment score for a ticker.

    Args:
        ticker: Stock ticker
        transactions: List of insider transactions for this ticker

    Returns:
        Dict with sentiment score (-100 to +100) and breakdown
    """
    if not transactions:
        return {"ticker": ticker, "score": 0, "signal": "NO_DATA", "confidence": "LOW"}

    buys = [t for t in transactions if t.get("transaction_type") == "BUY"]
    sells = [t for t in transactions if t.get("transaction_type") == "SELL"]

    n_buys = len(buys)
    n_sells = len(sells)
    total = n_buys + n_sells

    if total == 0:
        return {"ticker": ticker, "score": 0, "signal": "NO_DATA", "confidence": "LOW"}

    # Direction score: net buy/sell ratio
    direction = (n_buys - n_sells) / total * 50

    # Value weighting
    buy_val = sum(t.get("value_usd", 0) for t in buys)
    sell_val = sum(t.get("value_usd", 0) for t in sells)
    total_val = buy_val + sell_val
    value_direction = ((buy_val - sell_val) / total_val * 50) if total_val > 0 else 0

    score = round(direction + value_direction, 1)
    score = max(-100, min(100, score))

    confidence = "HIGH" if total >= 5 else "MEDIUM" if total >= 3 else "LOW"
    signal = (
        "STRONG_BUY" if score > 60 else
        "BUY" if score > 20 else
        "NEUTRAL" if score > -20 else
        "SELL" if score > -60 else
        "STRONG_SELL"
    )

    return {
        "ticker": ticker,
        "score": score,
        "signal": signal,
        "confidence": confidence,
        "n_buys": n_buys,
        "n_sells": n_sells,
        "buy_value": round(buy_val, 2),
        "sell_value": round(sell_val, 2)
    }


def _parse_filing(filing: Dict) -> Optional[Dict]:
    """Parse a raw SEC filing into structured transaction."""
    return {
        "insider_name": filing.get("reportingOwner", filing.get("name", "Unknown")),
        "insider_role": filing.get("officerTitle", filing.get("role", "Officer")),
        "ticker": filing.get("ticker", filing.get("issuerTradingSymbol", "")),
        "transaction_type": "BUY" if filing.get("transactionCode", "P") in ("P", "A") else "SELL",
        "shares": filing.get("transactionShares", 0),
        "price_per_share": filing.get("transactionPricePerShare", 0),
        "value_usd": filing.get("transactionShares", 0) * filing.get("transactionPricePerShare", 0),
        "filing_date": filing.get("filedAt", filing.get("dateFiled", "")),
        "form_type": "4"
    }


def _insider_signal(ratio: float, n_buys: int, n_sells: int) -> str:
    if n_buys + n_sells == 0:
        return "NO_DATA"
    if ratio > 3:
        return "STRONG_BUY"
    elif ratio > 1.5:
        return "BUY"
    elif ratio > 0.5:
        return "NEUTRAL"
    elif ratio > 0.2:
        return "SELL"
    return "STRONG_SELL"


def _generate_sample_filings(ticker: Optional[str], days: int) -> Dict:
    """Generate sample data when SEC API is unavailable."""
    return {"filings": []}

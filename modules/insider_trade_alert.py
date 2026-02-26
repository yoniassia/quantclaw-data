"""
Insider Trade Alert System — Monitor SEC Form 4 filings for insider trading activity.

Tracks insider buying/selling patterns using SEC EDGAR XBRL data,
identifies unusual insider activity clusters, and scores conviction levels.
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional


SEC_EDGAR_BASE = "https://efts.sec.gov/LATEST/search-index"
SEC_FULL_TEXT = "https://efts.sec.gov/LATEST/search-index"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions"


def get_recent_insider_filings(
    symbol: Optional[str] = None, days: int = 7, limit: int = 50
) -> Dict:
    """
    Fetch recent Form 4 insider trading filings from SEC EDGAR.

    Args:
        symbol: Optional ticker to filter
        days: Number of days to look back
        limit: Max number of filings to return

    Returns:
        Dict with recent insider filings and summary statistics
    """
    try:
        # Use EDGAR full-text search for Form 4 filings
        query = f"formType:\"4\" {symbol}" if symbol else 'formType:"4"'
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        url = (
            f"https://efts.sec.gov/LATEST/search-index?"
            f"q={urllib.request.quote(query)}"
            f"&dateRange=custom&startdt={date_from}"
            f"&enddt={datetime.now().strftime('%Y-%m-%d')}"
            f"&forms=4&from=0&size={limit}"
        )

        req = urllib.request.Request(url, headers={
            "User-Agent": "QuantClaw research@quantclaw.com",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        hits = data.get("hits", {}).get("hits", [])
        filings = []
        for hit in hits[:limit]:
            src = hit.get("_source", {})
            filings.append({
                "filing_date": src.get("file_date"),
                "company": src.get("display_names", [None])[0] if src.get("display_names") else None,
                "ticker": src.get("tickers", [symbol])[0] if src.get("tickers") else symbol,
                "form_type": src.get("form_type"),
                "url": f"https://www.sec.gov/Archives/{src.get('file_name', '')}",
            })

        return {
            "query": symbol or "ALL",
            "period_days": days,
            "total_found": data.get("hits", {}).get("total", {}).get("value", 0),
            "filings": filings,
            "source": "SEC EDGAR",
        }

    except Exception as e:
        return _fallback_edgar_search(symbol, days, str(e))


def _fallback_edgar_search(symbol: Optional[str], days: int, error: str) -> Dict:
    """Fallback using EDGAR full-text search API."""
    try:
        query = f'"{symbol}" "form 4"' if symbol else '"form 4"'
        url = (
            f"https://efts.sec.gov/LATEST/search-index?"
            f"q={urllib.request.quote(query)}&forms=4"
        )
        req = urllib.request.Request(url, headers={
            "User-Agent": "QuantClaw research@quantclaw.com",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        total = data.get("hits", {}).get("total", {}).get("value", 0)
        return {
            "query": symbol or "ALL",
            "total_form4_filings": total,
            "primary_error": error,
            "source": "SEC EDGAR (fallback)",
        }
    except Exception:
        return {"error": error, "fallback_error": "Both EDGAR endpoints unavailable"}


def analyze_insider_activity(transactions: List[Dict]) -> Dict:
    """
    Analyze a list of insider transactions to detect patterns.

    Scores conviction level based on buy/sell ratios, cluster buying,
    and transaction sizes relative to holdings.

    Args:
        transactions: List of dicts with keys:
            - type: 'BUY' or 'SELL'
            - shares: number of shares
            - price: transaction price
            - insider_name: name of insider
            - insider_title: title (CEO, CFO, Director, etc.)
            - date: transaction date string

    Returns:
        Dict with insider activity analysis and conviction score
    """
    if not transactions:
        return {"error": "No transactions provided"}

    buys = [t for t in transactions if t.get("type", "").upper() == "BUY"]
    sells = [t for t in transactions if t.get("type", "").upper() == "SELL"]

    buy_volume = sum(t.get("shares", 0) for t in buys)
    sell_volume = sum(t.get("shares", 0) for t in sells)
    buy_value = sum(t.get("shares", 0) * t.get("price", 0) for t in buys)
    sell_value = sum(t.get("shares", 0) * t.get("price", 0) for t in sells)

    # Unique insiders
    buy_insiders = list(set(t.get("insider_name", "Unknown") for t in buys))
    sell_insiders = list(set(t.get("insider_name", "Unknown") for t in sells))

    # C-suite activity (higher conviction signal)
    c_suite_titles = {"CEO", "CFO", "COO", "CTO", "President", "Chairman"}
    c_suite_buys = [
        t for t in buys
        if any(title in t.get("insider_title", "") for title in c_suite_titles)
    ]

    # Cluster buying detection (3+ insiders buying within same period)
    cluster_buy = len(buy_insiders) >= 3

    # Conviction scoring (0-100)
    score = 50  # neutral
    if buy_volume > sell_volume * 2:
        score += 20
    elif sell_volume > buy_volume * 2:
        score -= 20
    if cluster_buy:
        score += 15
    if c_suite_buys:
        score += 10
    if buy_value > 1_000_000:
        score += 5
    score = max(0, min(100, score))

    signal = (
        "STRONG BUY" if score >= 80 else
        "BUY" if score >= 65 else
        "NEUTRAL" if score >= 40 else
        "SELL" if score >= 25 else "STRONG SELL"
    )

    return {
        "total_transactions": len(transactions),
        "buys": {
            "count": len(buys),
            "total_shares": buy_volume,
            "total_value": round(buy_value, 2),
            "unique_insiders": buy_insiders,
        },
        "sells": {
            "count": len(sells),
            "total_shares": sell_volume,
            "total_value": round(sell_value, 2),
            "unique_insiders": sell_insiders,
        },
        "c_suite_buys": len(c_suite_buys),
        "cluster_buying": cluster_buy,
        "conviction_score": score,
        "signal": signal,
        "interpretation": {
            "STRONG BUY": "Multiple insiders aggressively buying — high conviction bullish",
            "BUY": "Net insider buying with meaningful size",
            "NEUTRAL": "Mixed insider activity — no clear direction",
            "SELL": "Net insider selling dominates",
            "STRONG SELL": "Heavy insider selling — potential red flag",
        }[signal],
    }


def get_insider_buy_sell_ratio(symbol: str, api_key: Optional[str] = None) -> Dict:
    """
    Calculate insider buy/sell ratio for a symbol using Financial Datasets API.

    Args:
        symbol: Stock ticker
        api_key: Financial Datasets API key

    Returns:
        Dict with buy/sell ratio and trend
    """
    if not api_key:
        return {
            "symbol": symbol,
            "note": "Provide Financial Datasets API key for insider trade data",
            "alternative": "Use get_recent_insider_filings() for SEC EDGAR data",
        }

    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        url = (
            f"https://api.financialdatasets.ai/insider-trades"
            f"?ticker={symbol}&start_date={start_date}&end_date={end_date}"
        )
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "QuantClaw/1.0",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        trades = data.get("insider_trades", [])
        buys = sum(1 for t in trades if t.get("transaction_type") in ("P", "A"))
        sells = sum(1 for t in trades if t.get("transaction_type") in ("S", "D"))

        ratio = buys / sells if sells > 0 else float("inf") if buys > 0 else 0

        return {
            "symbol": symbol,
            "period": f"{start_date} to {end_date}",
            "total_filings": len(trades),
            "buys": buys,
            "sells": sells,
            "buy_sell_ratio": round(ratio, 2) if ratio != float("inf") else "INF",
            "signal": "BULLISH" if ratio > 1.5 else ("BEARISH" if ratio < 0.5 else "NEUTRAL"),
            "source": "Financial Datasets API",
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}

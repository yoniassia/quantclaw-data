"""
StockAnalysis.com — Comprehensive Stock Fundamentals & Analyst Data

Data Source: stockanalysis.com (JSON API + page scraping)
Update frequency: Real-time / Daily
Category: Fundamentals, Analyst Estimates, Dividends, Price History
Free: Yes (no API key required)

Provides:
- Company overview (market cap, PE, EPS, sector, description)
- Income statement financials (annual, multi-year)
- Analyst price targets & ratings consensus
- Dividend history & yield data
- Historical price data (daily/monthly)
- Revenue & EPS forecasts

Usage:
    >>> from modules.stockanalysis_com import *
    >>> overview = get_overview("AAPL")
    >>> financials = get_financials("AAPL")
    >>> forecast = get_forecast("AAPL")
"""

import json
import re
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional


API_BASE = "https://stockanalysis.com/api/symbol/s"
WEB_BASE = "https://stockanalysis.com/stocks"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


def _fetch_json(url: str, timeout: int = 15) -> dict:
    """Internal: fetch JSON from stockanalysis.com API."""
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if isinstance(data, dict) and data.get("status") == 200:
        return data.get("data", data)
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return data


def _fetch_html(url: str, timeout: int = 15) -> str:
    """Internal: fetch raw HTML from stockanalysis.com."""
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def _parse_number(val: str) -> Optional[float]:
    """Parse strings like '3.78T', '435.62B', '14.68B', '32.65' into floats."""
    if val is None:
        return None
    val = str(val).strip().replace(",", "").replace("$", "").replace("%", "")
    if not val or val.lower() in ("n/a", "-", ""):
        return None
    multipliers = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}
    suffix = val[-1].upper()
    if suffix in multipliers:
        try:
            return float(val[:-1]) * multipliers[suffix]
        except ValueError:
            return None
    try:
        return float(val)
    except ValueError:
        return None


# ─── PUBLIC FUNCTIONS ─────────────────────────────────────────────────────────


def get_overview(ticker: str) -> Dict[str, Any]:
    """
    Get company overview: market cap, revenue, EPS, PE, sector, description, etc.

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL', 'MSFT')

    Returns:
        dict with keys: ticker, market_cap, revenue, net_income, eps, pe_ratio,
        forward_pe, dividend, beta, analyst_rating, price_target, sector,
        industry, employees, exchange, description, fetched_at

    Example:
        >>> data = get_overview("AAPL")
        >>> print(data["market_cap"], data["pe_ratio"])
    """
    ticker = ticker.upper().strip()
    url = f"{API_BASE}/{ticker}/overview"
    try:
        raw = _fetch_json(url)
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

    # Parse info table into dict
    info = {}
    for item in raw.get("infoTable", []):
        info[item.get("t", "").lower()] = item.get("v")

    # Parse target string like "297.10 (+15.4%)"
    target_str = raw.get("target", "")
    target_price = None
    target_upside = None
    if target_str:
        m = re.match(r"([\d.]+)\s*\(([+-]?[\d.]+)%\)", target_str)
        if m:
            target_price = float(m.group(1))
            target_upside = float(m.group(2))

    return {
        "ticker": ticker,
        "market_cap": raw.get("marketCap"),
        "market_cap_num": _parse_number(raw.get("marketCap")),
        "revenue": raw.get("revenue"),
        "revenue_type": raw.get("revenue_type"),
        "net_income": raw.get("netIncome"),
        "shares_out": raw.get("sharesOut"),
        "eps": _parse_number(raw.get("eps")),
        "pe_ratio": _parse_number(raw.get("peRatio")),
        "forward_pe": _parse_number(raw.get("forwardPE")),
        "dividend": raw.get("dividend"),
        "ex_dividend_date": raw.get("exDividendDate"),
        "beta": _parse_number(raw.get("beta")),
        "analyst_rating": raw.get("analysts"),
        "price_target": target_price,
        "price_target_upside_pct": target_upside,
        "earnings_date": raw.get("earningsDate"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "employees": info.get("employees"),
        "exchange": info.get("stock exchange"),
        "ipo_date": info.get("ipo date"),
        "website": info.get("website"),
        "description": raw.get("description"),
        "financial_intro": raw.get("financialIntro"),
        "financial_chart": raw.get("financialChart", []),
        "fetched_at": datetime.utcnow().isoformat(),
    }


def get_financials(ticker: str) -> Dict[str, Any]:
    """
    Get income statement financials by scraping the financials page.
    Returns multi-year annual data (revenue, net income, EPS, margins, etc.)

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL')

    Returns:
        dict with keys: ticker, periods (list of period labels),
        metrics (dict of metric_name -> list of values), fetched_at

    Example:
        >>> fin = get_financials("MSFT")
        >>> print(fin["metrics"]["Revenue"])
    """
    ticker = ticker.upper().strip()
    url = f"{WEB_BASE}/{ticker.lower()}/financials/"
    try:
        html = _fetch_html(url)
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

    # Extract the text content — look for financial rows
    # The page renders a table; we parse the readable text
    from html.parser import HTMLParser
    import io

    class TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text_parts = []
            self._skip = False

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style"):
                self._skip = True

        def handle_endtag(self, tag):
            if tag in ("script", "style"):
                self._skip = False

        def handle_data(self, data):
            if not self._skip:
                self.text_parts.append(data)

    extractor = TextExtractor()
    extractor.feed(html)
    text = " ".join(extractor.text_parts)

    # Parse known metric rows
    metrics = {}
    metric_patterns = [
        "Revenue", "Revenue Growth", "Cost of Revenue", "Gross Profit",
        "Operating Income", "Net Income", "Net Income Growth",
        "EPS (Basic)", "EPS (Diluted)", "EPS Growth",
        "Free Cash Flow", "Free Cash Flow Growth", "Free Cash Flow Per Share",
        "Dividends Per Share", "Dividend Growth",
        "Gross Margin", "Operating Margin", "Profit Margin", "FCF Margin",
        "EBITDA", "EBITDA Margin", "EBIT", "EBIT Margin",
        "Effective Tax Rate", "Shares Outstanding (Diluted)",
    ]

    # Try to extract rows: metric name followed by numbers
    for metric in metric_patterns:
        # Escape special chars for regex
        escaped = re.escape(metric)
        # Match metric name then capture numbers (with optional negative, commas, decimals, %)
        pattern = escaped + r'\s+([-\d,.%]+(?:\s+[-\d,.%]+)*)'
        match = re.search(pattern, text)
        if match:
            raw_vals = match.group(1).strip()
            values = re.findall(r'-?[\d,.]+%?', raw_vals)
            # Clean values
            cleaned = []
            for v in values:
                v_clean = v.replace(",", "").replace("%", "")
                try:
                    cleaned.append(float(v_clean))
                except ValueError:
                    cleaned.append(v)
            if cleaned:
                metrics[metric] = cleaned

    # Try to extract period headers
    period_match = re.search(r'(TTM\s*(?:FY\s+\d{4}\s*)+)', text)
    periods = []
    if period_match:
        periods = re.findall(r'TTM|FY\s+\d{4}', period_match.group(1))

    return {
        "ticker": ticker,
        "periods": periods,
        "metrics": metrics,
        "metric_count": len(metrics),
        "fetched_at": datetime.utcnow().isoformat(),
    }


def get_dividend(ticker: str) -> Dict[str, Any]:
    """
    Get dividend data: yield, payout ratio, history, growth rate.

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL')

    Returns:
        dict with keys: ticker, yield, annual_dividend, ex_dividend_date,
        frequency, payout_ratio, growth, years_paying, buyback_yield,
        total_return, history (list of dicts), fetched_at

    Example:
        >>> div = get_dividend("AAPL")
        >>> print(div["yield"], div["payout_ratio"])
    """
    ticker = ticker.upper().strip()
    url = f"{API_BASE}/{ticker}/dividend"
    try:
        raw = _fetch_json(url)
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

    info = raw.get("infoTable", {})
    history = raw.get("history", [])

    # Parse history into clean dicts
    clean_history = []
    for h in history:
        clean_history.append({
            "ex_date": h.get("dt"),
            "amount": h.get("amt", "").replace("$", ""),
            "record_date": h.get("record"),
            "pay_date": h.get("pay"),
        })

    return {
        "ticker": ticker,
        "yield": info.get("yield"),
        "annual_dividend": info.get("annual"),
        "ex_dividend_date": info.get("exdiv"),
        "frequency": info.get("frequency"),
        "payout_ratio": info.get("payoutRatio"),
        "dividend_growth": info.get("growth"),
        "years_paying": _parse_number(info.get("years")),
        "buyback_yield": info.get("buybackYield"),
        "total_return": info.get("totalReturn"),
        "info_box": raw.get("infoBox"),
        "history": clean_history[:20],  # last 20 entries
        "fetched_at": datetime.utcnow().isoformat(),
    }


def get_price_history(
    ticker: str,
    period: str = "monthly",
) -> Dict[str, Any]:
    """
    Get historical price data (OHLCV).

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL')
        period: 'monthly' (default) or 'daily'

    Returns:
        dict with keys: ticker, period, data (list of price bars), count, fetched_at
        Each bar: {date, open, high, low, close, adj_close, volume, change_pct}

    Example:
        >>> hist = get_price_history("AAPL", period="monthly")
        >>> print(hist["data"][0])  # most recent bar
    """
    ticker = ticker.upper().strip()
    p_param = period if period in ("monthly", "daily") else "monthly"
    url = f"{API_BASE}/{ticker}/history?p={p_param}"
    try:
        raw = _fetch_json(url)
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

    bars = raw.get("data", [])
    clean_bars = []
    for bar in bars:
        clean_bars.append({
            "date": bar.get("t"),
            "open": bar.get("o"),
            "high": bar.get("h"),
            "low": bar.get("l"),
            "close": bar.get("c"),
            "adj_close": bar.get("a"),
            "volume": bar.get("v"),
            "change_pct": bar.get("ch"),
        })

    return {
        "ticker": ticker,
        "period": p_param,
        "data": clean_bars,
        "count": len(clean_bars),
        "fetched_at": datetime.utcnow().isoformat(),
    }


def get_forecast(ticker: str) -> Dict[str, Any]:
    """
    Get analyst price targets, ratings consensus, and revenue/EPS forecasts
    by scraping the forecast page.

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL')

    Returns:
        dict with keys: ticker, current_price, analyst_count, consensus,
        price_target_avg, price_target_low, price_target_high,
        target_upside_pct, ratings_breakdown, revenue_estimates,
        eps_estimates, fetched_at

    Example:
        >>> fc = get_forecast("AAPL")
        >>> print(fc["consensus"], fc["price_target_avg"])
    """
    ticker = ticker.upper().strip()
    url = f"{WEB_BASE}/{ticker.lower()}/forecast/"
    try:
        html = _fetch_html(url)
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

    from html.parser import HTMLParser

    class TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text_parts = []
            self._skip = False
        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style"):
                self._skip = True
        def handle_endtag(self, tag):
            if tag in ("script", "style"):
                self._skip = False
        def handle_data(self, data):
            if not self._skip:
                self.text_parts.append(data)

    ext = TextExtractor()
    ext.feed(html)
    text = " ".join(ext.text_parts)

    result = {"ticker": ticker}

    # Current price
    price_m = re.search(r'(\d+\.\d+)\s+[+-]?\d+\.\d+\s+\([+-]?\d+\.\d+%\)\s+At close', text)
    if price_m:
        result["current_price"] = float(price_m.group(1))

    # Consensus summary
    cons_m = re.search(r'(\d+)\s+analysts?\s+.*?consensus\s+rating\s+of\s+"(\w+)"', text, re.IGNORECASE)
    if cons_m:
        result["analyst_count"] = int(cons_m.group(1))
        result["consensus"] = cons_m.group(2)

    # Price targets
    avg_m = re.search(r'average\s+price\s+target\s+of\s+\$?([\d,.]+)', text, re.IGNORECASE)
    if avg_m:
        result["price_target_avg"] = float(avg_m.group(1).replace(",", ""))

    upside_m = re.search(r'forecasts?\s+a?\s*([\d.]+)%\s+(increase|decrease)', text, re.IGNORECASE)
    if upside_m:
        pct = float(upside_m.group(1))
        result["target_upside_pct"] = pct if upside_m.group(2).lower() == "increase" else -pct

    low_m = re.search(r'lowest\s+target\s+is\s+\$?([\d,.]+)', text, re.IGNORECASE)
    if low_m:
        result["price_target_low"] = float(low_m.group(1).replace(",", ""))

    high_m = re.search(r'highest\s+is\s+\$?([\d,.]+)', text, re.IGNORECASE)
    if high_m:
        result["price_target_high"] = float(high_m.group(1).replace(",", ""))

    # Ratings breakdown
    ratings = {}
    for rating in ("Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"):
        rm = re.search(re.escape(rating) + r'\s+([\d\s]+?)(?:Buy|Hold|Sell|Strong|Total)', text)
        if rm:
            nums = re.findall(r'\d+', rm.group(1))
            if nums:
                ratings[rating] = int(nums[-1])  # latest month
    if ratings:
        result["ratings_breakdown"] = ratings

    # Revenue estimates from table
    rev_m = re.search(r'Revenue\s+([\d.]+[BM](?:\s*[\d.]+[BM])*)', text)
    if rev_m:
        result["revenue_estimates"] = re.findall(r'[\d.]+[BM]', rev_m.group(0))

    # EPS estimates
    eps_m = re.search(r'EPS\s+([\d.]+(?:\s+[\d.]+)*)', text)
    if eps_m:
        vals = re.findall(r'[\d.]+', eps_m.group(1))
        try:
            result["eps_estimates"] = [float(v) for v in vals]
        except ValueError:
            pass

    result["fetched_at"] = datetime.utcnow().isoformat()
    return result


def get_key_metrics(ticker: str) -> Dict[str, Any]:
    """
    Get key metrics by combining overview data with computed fields.
    Quick snapshot for screening/comparison.

    Args:
        ticker: Stock ticker symbol

    Returns:
        dict with essential valuation and profitability metrics

    Example:
        >>> m = get_key_metrics("MSFT")
        >>> print(m["pe_ratio"], m["analyst_rating"])
    """
    overview = get_overview(ticker)
    if "error" in overview:
        return overview

    return {
        "ticker": ticker,
        "market_cap": overview.get("market_cap"),
        "pe_ratio": overview.get("pe_ratio"),
        "forward_pe": overview.get("forward_pe"),
        "eps": overview.get("eps"),
        "beta": overview.get("beta"),
        "dividend": overview.get("dividend"),
        "analyst_rating": overview.get("analyst_rating"),
        "price_target": overview.get("price_target"),
        "price_target_upside_pct": overview.get("price_target_upside_pct"),
        "sector": overview.get("sector"),
        "industry": overview.get("industry"),
        "fetched_at": datetime.utcnow().isoformat(),
    }


def compare_stocks(tickers: List[str]) -> List[Dict[str, Any]]:
    """
    Compare multiple stocks side by side on key metrics.

    Args:
        tickers: List of ticker symbols (e.g. ['AAPL', 'MSFT', 'GOOGL'])

    Returns:
        List of key metrics dicts, one per ticker

    Example:
        >>> results = compare_stocks(["AAPL", "MSFT", "GOOGL"])
        >>> for r in results: print(r["ticker"], r["pe_ratio"])
    """
    return [get_key_metrics(t) for t in tickers]


# Module-level exports
__all__ = [
    "get_overview",
    "get_financials",
    "get_dividend",
    "get_price_history",
    "get_forecast",
    "get_key_metrics",
    "compare_stocks",
]

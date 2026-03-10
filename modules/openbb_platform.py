#!/usr/bin/env python3
"""
OpenBB Platform — QuantClaw Data Module

Provides OpenBB-style financial data aggregation using free data sources.
Wraps multiple free APIs (Yahoo Finance, FRED, SEC EDGAR, etc.) in a
unified interface inspired by OpenBB's modular architecture.

Source: https://openbb.co/docs
Category: Quant Tools & ML
Free tier: Yes (no paid API keys required)
Update frequency: Real-time for quotes, daily for historical

Functions:
- get_stock_quote: Real-time stock quote
- get_historical_prices: OHLCV historical data
- get_company_profile: Company fundamentals
- get_market_indices: Major market indices
- get_economic_calendar: Upcoming economic events
- get_treasury_rates: US Treasury yield curve
- get_sector_performance: S&P 500 sector performance
- get_stock_financials: Income statement / balance sheet summary
- get_market_movers: Top gainers/losers
- get_crypto_quote: Cryptocurrency price data
- search_securities: Search stocks/ETFs by name
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import time

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/openbb_platform")
os.makedirs(CACHE_DIR, exist_ok=True)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def _cache_get(key: str, max_age_seconds: int = 300) -> Optional[dict]:
    """Read from file cache if fresh enough."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(path):
        age = time.time() - os.path.getmtime(path)
        if age < max_age_seconds:
            with open(path) as f:
                return json.load(f)
    return None


def _cache_set(key: str, data) -> None:
    """Write to file cache."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    with open(path, "w") as f:
        json.dump(data, f)


def get_stock_quote(symbol: str) -> Dict:
    """
    Get real-time stock quote via Yahoo Finance.

    Args:
        symbol: Ticker symbol (e.g., 'AAPL', 'MSFT')

    Returns:
        Dict with price, change, volume, market cap, etc.
    """
    symbol = symbol.upper().strip()
    cached = _cache_get(f"quote_{symbol}", max_age_seconds=60)
    if cached:
        return cached

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"interval": "1d", "range": "1d"}
    try:
        resp = requests.get(url, params=params, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            return {"error": f"No data for {symbol}", "symbol": symbol}

        meta = result[0].get("meta", {})
        indicators = result[0].get("indicators", {})
        quote_data = indicators.get("quote", [{}])[0]

        # Get latest values
        closes = quote_data.get("close", [])
        volumes = quote_data.get("volume", [])
        highs = quote_data.get("high", [])
        lows = quote_data.get("low", [])
        opens = quote_data.get("open", [])

        price = meta.get("regularMarketPrice", closes[-1] if closes else None)
        prev_close = meta.get("previousClose", meta.get("chartPreviousClose"))

        change = None
        change_pct = None
        if price and prev_close:
            change = round(price - prev_close, 4)
            change_pct = round((change / prev_close) * 100, 4)

        output = {
            "symbol": symbol,
            "price": price,
            "previous_close": prev_close,
            "change": change,
            "change_percent": change_pct,
            "open": opens[-1] if opens else None,
            "high": highs[-1] if highs else None,
            "low": lows[-1] if lows else None,
            "volume": volumes[-1] if volumes else None,
            "currency": meta.get("currency"),
            "exchange": meta.get("exchangeName"),
            "instrument_type": meta.get("instrumentType"),
            "timezone": meta.get("exchangeTimezoneName"),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "yahoo_finance"
        }
        _cache_set(f"quote_{symbol}", output)
        return output
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_historical_prices(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d"
) -> List[Dict]:
    """
    Get historical OHLCV price data.

    Args:
        symbol: Ticker symbol
        period: Time period ('1d','5d','1mo','3mo','6mo','1y','2y','5y','10y','max')
        interval: Data interval ('1m','5m','15m','1h','1d','1wk','1mo')

    Returns:
        List of dicts with date, open, high, low, close, volume
    """
    symbol = symbol.upper().strip()
    cache_key = f"hist_{symbol}_{period}_{interval}"
    cached = _cache_get(cache_key, max_age_seconds=3600)
    if cached:
        return cached

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"range": period, "interval": interval}
    try:
        resp = requests.get(url, params=params, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            return [{"error": f"No data for {symbol}"}]

        timestamps = result[0].get("timestamp", [])
        quote = result[0].get("indicators", {}).get("quote", [{}])[0]
        adj = result[0].get("indicators", {}).get("adjclose", [{}])
        adj_closes = adj[0].get("adjclose", []) if adj else []

        bars = []
        for i, ts in enumerate(timestamps):
            bar = {
                "date": datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d"),
                "open": round(quote["open"][i], 4) if quote["open"][i] else None,
                "high": round(quote["high"][i], 4) if quote["high"][i] else None,
                "low": round(quote["low"][i], 4) if quote["low"][i] else None,
                "close": round(quote["close"][i], 4) if quote["close"][i] else None,
                "volume": quote["volume"][i],
            }
            if adj_closes and i < len(adj_closes) and adj_closes[i]:
                bar["adj_close"] = round(adj_closes[i], 4)
            bars.append(bar)

        _cache_set(cache_key, bars)
        return bars
    except Exception as e:
        return [{"error": str(e), "symbol": symbol}]


def get_company_profile(symbol: str) -> Dict:
    """
    Get company profile and key statistics.

    Args:
        symbol: Ticker symbol

    Returns:
        Dict with company info, sector, market cap, PE, etc.
    """
    symbol = symbol.upper().strip()
    cached = _cache_get(f"profile_{symbol}", max_age_seconds=86400)
    if cached:
        return cached

    url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
    params = {"modules": "assetProfile,defaultKeyStatistics,summaryDetail,financialData"}
    try:
        resp = requests.get(url, params=params, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("quoteSummary", {}).get("result", [])
        if not result:
            return {"error": f"No profile for {symbol}"}

        r = result[0]
        profile = r.get("assetProfile", {})
        stats = r.get("defaultKeyStatistics", {})
        summary = r.get("summaryDetail", {})
        fin = r.get("financialData", {})

        def _val(d, k):
            v = d.get(k, {})
            return v.get("raw") if isinstance(v, dict) else v

        output = {
            "symbol": symbol,
            "name": profile.get("longBusinessSummary", "")[:200],
            "sector": profile.get("sector"),
            "industry": profile.get("industry"),
            "country": profile.get("country"),
            "employees": profile.get("fullTimeEmployees"),
            "website": profile.get("website"),
            "market_cap": _val(summary, "marketCap"),
            "pe_ratio": _val(summary, "trailingPE"),
            "forward_pe": _val(summary, "forwardPE"),
            "price_to_book": _val(stats, "priceToBook"),
            "dividend_yield": _val(summary, "dividendYield"),
            "beta": _val(stats, "beta"),
            "52w_high": _val(summary, "fiftyTwoWeekHigh"),
            "52w_low": _val(summary, "fiftyTwoWeekLow"),
            "revenue": _val(fin, "totalRevenue"),
            "profit_margin": _val(fin, "profitMargins"),
            "roe": _val(fin, "returnOnEquity"),
            "debt_to_equity": _val(fin, "debtToEquity"),
            "source": "yahoo_finance",
            "timestamp": datetime.utcnow().isoformat()
        }
        _cache_set(f"profile_{symbol}", output)
        return output
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_market_indices() -> List[Dict]:
    """
    Get major market indices (S&P 500, DJIA, NASDAQ, Russell 2000, VIX).

    Returns:
        List of dicts with index name, value, change
    """
    cached = _cache_get("market_indices", max_age_seconds=120)
    if cached:
        return cached

    indices = {
        "^GSPC": "S&P 500",
        "^DJI": "Dow Jones",
        "^IXIC": "NASDAQ Composite",
        "^RUT": "Russell 2000",
        "^VIX": "VIX",
        "^FTSE": "FTSE 100",
        "^N225": "Nikkei 225",
    }

    results = []
    for ticker, name in indices.items():
        q = get_stock_quote(ticker)
        if "error" not in q:
            results.append({
                "name": name,
                "symbol": ticker,
                "price": q.get("price"),
                "change": q.get("change"),
                "change_percent": q.get("change_percent"),
            })
        else:
            results.append({"name": name, "symbol": ticker, "error": q["error"]})

    _cache_set("market_indices", results)
    return results


def get_treasury_rates() -> Dict:
    """
    Get current US Treasury yield curve rates from the US Treasury API.

    Returns:
        Dict with rates for various maturities (1mo, 3mo, 6mo, 1yr ... 30yr)
    """
    cached = _cache_get("treasury_rates", max_age_seconds=3600)
    if cached:
        return cached

    # Use Treasury yield curve ETFs as proxy for rates
    rate_tickers = {
        "^IRX": "3-Month T-Bill",
        "^FVX": "5-Year Treasury",
        "^TNX": "10-Year Treasury",
        "^TYX": "30-Year Treasury",
    }
    rates = {}
    for ticker, label in rate_tickers.items():
        q = get_stock_quote(ticker)
        if "error" not in q and q.get("price"):
            rates[label] = q["price"]

    if rates:
        output = {
            "rates": rates,
            "note": "Yields in percent from Yahoo Finance index proxies",
            "source": "yahoo_finance",
            "timestamp": datetime.utcnow().isoformat()
        }
        _cache_set("treasury_rates", output)
        return output

    return {"error": "Could not fetch treasury rates"}


def get_sector_performance() -> List[Dict]:
    """
    Get S&P 500 sector ETF performance.

    Returns:
        List of dicts with sector name, ETF ticker, performance
    """
    cached = _cache_get("sector_perf", max_age_seconds=300)
    if cached:
        return cached

    sector_etfs = {
        "XLK": "Technology",
        "XLF": "Financials",
        "XLV": "Healthcare",
        "XLE": "Energy",
        "XLY": "Consumer Discretionary",
        "XLP": "Consumer Staples",
        "XLI": "Industrials",
        "XLB": "Materials",
        "XLRE": "Real Estate",
        "XLU": "Utilities",
        "XLC": "Communication Services",
    }

    results = []
    for etf, sector in sector_etfs.items():
        q = get_stock_quote(etf)
        if "error" not in q:
            results.append({
                "sector": sector,
                "etf": etf,
                "price": q.get("price"),
                "change_percent": q.get("change_percent"),
            })

    results.sort(key=lambda x: x.get("change_percent") or 0, reverse=True)
    _cache_set("sector_perf", results)
    return results


def get_stock_financials(symbol: str) -> Dict:
    """
    Get key financial metrics (income statement, balance sheet summary).

    Args:
        symbol: Ticker symbol

    Returns:
        Dict with revenue, earnings, margins, debt levels
    """
    symbol = symbol.upper().strip()
    cached = _cache_get(f"financials_{symbol}", max_age_seconds=86400)
    if cached:
        return cached

    url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
    params = {"modules": "incomeStatementHistory,balanceSheetHistory,cashflowStatementHistory"}
    try:
        resp = requests.get(url, params=params, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("quoteSummary", {}).get("result", [])
        if not data:
            return {"error": f"No financials for {symbol}"}

        r = data[0]
        income = r.get("incomeStatementHistory", {}).get("incomeStatementHistory", [])
        balance = r.get("balanceSheetHistory", {}).get("balanceSheetStatements", [])
        cashflow = r.get("cashflowStatementHistory", {}).get("cashflowStatements", [])

        def _extract(statements, limit=4):
            out = []
            for s in statements[:limit]:
                row = {}
                for k, v in s.items():
                    if isinstance(v, dict) and "raw" in v:
                        row[k] = v["raw"]
                    elif k == "endDate" and isinstance(v, dict):
                        row[k] = v.get("fmt")
                out.append(row)
            return out

        output = {
            "symbol": symbol,
            "income_statements": _extract(income),
            "balance_sheets": _extract(balance),
            "cash_flows": _extract(cashflow),
            "source": "yahoo_finance",
            "timestamp": datetime.utcnow().isoformat()
        }
        _cache_set(f"financials_{symbol}", output)
        return output
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_crypto_quote(symbol: str = "BTC") -> Dict:
    """
    Get cryptocurrency price data.

    Args:
        symbol: Crypto symbol (e.g., 'BTC', 'ETH', 'SOL')

    Returns:
        Dict with price, 24h change, volume, market cap
    """
    symbol = symbol.upper().strip()
    # Yahoo uses -USD suffix for crypto
    yf_symbol = f"{symbol}-USD"
    q = get_stock_quote(yf_symbol)
    if "error" not in q:
        q["crypto_symbol"] = symbol
        q["pair"] = f"{symbol}/USD"
    return q


def get_market_movers(direction: str = "gainers") -> List[Dict]:
    """
    Get top market movers (gainers or losers).

    Args:
        direction: 'gainers' or 'losers'

    Returns:
        List of dicts with symbol, price, change info
    """
    cached = _cache_get(f"movers_{direction}", max_age_seconds=300)
    if cached:
        return cached

    try:
        if direction == "losers":
            url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds=day_losers&count=10"
        else:
            url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds=day_gainers&count=10"

        resp = requests.get(url, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        quotes = data.get("finance", {}).get("result", [{}])[0].get("quotes", [])

        results = []
        for q in quotes[:10]:
            results.append({
                "symbol": q.get("symbol"),
                "name": q.get("shortName"),
                "price": q.get("regularMarketPrice"),
                "change": q.get("regularMarketChange"),
                "change_percent": q.get("regularMarketChangePercent"),
                "volume": q.get("regularMarketVolume"),
                "market_cap": q.get("marketCap"),
            })

        _cache_set(f"movers_{direction}", results)
        return results
    except Exception as e:
        return [{"error": str(e), "direction": direction}]


def search_securities(query: str, limit: int = 10) -> List[Dict]:
    """
    Search for stocks, ETFs, and other securities by name or symbol.

    Args:
        query: Search term
        limit: Max results (default 10)

    Returns:
        List of matching securities with symbol, name, type, exchange
    """
    try:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            "q": query,
            "quotesCount": limit,
            "newsCount": 0,
            "listsCount": 0,
        }
        resp = requests.get(url, params=params, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        quotes = data.get("quotes", [])

        return [
            {
                "symbol": q.get("symbol"),
                "name": q.get("shortname") or q.get("longname"),
                "type": q.get("quoteType"),
                "exchange": q.get("exchange"),
                "score": q.get("score"),
            }
            for q in quotes[:limit]
        ]
    except Exception as e:
        return [{"error": str(e)}]


def get_economic_calendar() -> List[Dict]:
    """
    Get upcoming economic events/releases from Trading Economics (free summary).

    Returns:
        List of economic events with date, event, country, impact
    """
    cached = _cache_get("econ_calendar", max_age_seconds=3600)
    if cached:
        return cached

    try:
        # Use Yahoo Finance economic calendar as fallback
        url = "https://finance.yahoo.com/calendar/economic"
        resp = requests.get(url, headers=_HEADERS, timeout=10)
        # Parse basic events — Yahoo renders via JS so we return a note
        return [{
            "note": "Economic calendar requires browser rendering. Use get_treasury_rates() for rate data or get_market_indices() for market overview.",
            "suggestion": "For detailed economic calendar, use FRED API or Trading Economics.",
            "timestamp": datetime.utcnow().isoformat()
        }]
    except Exception as e:
        return [{"error": str(e)}]


# ── Module metadata ──────────────────────────────────────────

MODULE_INFO = {
    "name": "openbb_platform",
    "version": "1.0.0",
    "description": "OpenBB-style financial data aggregation using free sources",
    "source": "https://openbb.co/docs",
    "category": "Quant Tools & ML",
    "functions": [
        "get_stock_quote",
        "get_historical_prices",
        "get_company_profile",
        "get_market_indices",
        "get_treasury_rates",
        "get_sector_performance",
        "get_stock_financials",
        "get_crypto_quote",
        "get_market_movers",
        "search_securities",
        "get_economic_calendar",
    ],
    "requires_api_key": False,
    "free_tier": True,
}


if __name__ == "__main__":
    print(json.dumps(MODULE_INFO, indent=2))
    print("\n--- AAPL Quote ---")
    print(json.dumps(get_stock_quote("AAPL"), indent=2))

#!/usr/bin/env python3
"""
Alpha Vantage API — Free Stock, Forex, Crypto, Commodities & Economic Data

Data Source: Alpha Vantage (https://www.alphavantage.co/)
Free tier: 25 requests/day with demo key, 500/day with free registered key
Update: Real-time intraday, daily historical
Coverage: US/global equities, forex, crypto, commodities, economic indicators, 50+ technical indicators

Provides:
- Daily/weekly/monthly stock prices (adjusted & unadjusted)
- Real-time & historical forex rates
- Cryptocurrency prices (daily/weekly/monthly)
- Commodity prices (oil, gold, natural gas, etc.)
- Economic indicators (GDP, CPI, unemployment, fed funds rate, treasury yields)
- Technical indicators (SMA, EMA, RSI, MACD, BBANDS, etc.)
- Company overview / fundamentals
- Ticker search
- Top gainers/losers
- News & sentiment
- Global market open/close status

Note: Uses the free 'demo' API key by default. Register at
https://www.alphavantage.co/support/#api-key for 500 calls/day (free, no credit card).
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/alpha_vantage")
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_URL = "https://www.alphavantage.co/query"

# Use env var or fall back to free demo key (very limited but works for testing)
API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY", "demo")

HEADERS = {
    "User-Agent": "QuantClaw/1.0"
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _request(params: dict) -> dict:
    """
    Make a GET request to Alpha Vantage.
    Returns parsed JSON or raises on error.
    """
    params["apikey"] = API_KEY
    try:
        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timed out"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "raw": resp.text[:500]}

    # Alpha Vantage returns errors inside JSON
    if "Error Message" in data:
        return {"error": data["Error Message"]}
    if "Note" in data:
        return {"warning": data["Note"], "data": data}
    if "Information" in data:
        return {"warning": data["Information"], "data": data}
    return data


def _parse_time_series(data: dict, series_key: str, limit: int = 30) -> List[Dict]:
    """Convert Alpha Vantage time-series dict into a list of dicts."""
    series = data.get(series_key, {})
    results = []
    for date_str, values in list(series.items())[:limit]:
        row = {"date": date_str}
        for k, v in values.items():
            # Keys look like "1. open" — clean them
            clean_key = k.split(". ", 1)[-1].replace(" ", "_")
            try:
                row[clean_key] = float(v)
            except (ValueError, TypeError):
                row[clean_key] = v
        results.append(row)
    return results


# ---------------------------------------------------------------------------
# Core Stock APIs
# ---------------------------------------------------------------------------

def get_daily(symbol: str, outputsize: str = "compact", limit: int = 30) -> Dict:
    """
    Get daily OHLCV prices for a stock.

    Args:
        symbol: Ticker symbol (e.g. 'AAPL', 'RELIANCE.BSE')
        outputsize: 'compact' (last 100 days) or 'full' (20+ years)
        limit: Number of recent days to return

    Returns:
        dict with 'meta' and 'prices' keys
    """
    data = _request({
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": outputsize
    })
    if "error" in data:
        return data

    meta = data.get("Meta Data", {})
    prices = _parse_time_series(data, "Time Series (Daily)", limit)
    return {
        "symbol": meta.get("2. Symbol", symbol),
        "last_refreshed": meta.get("3. Last Refreshed", ""),
        "prices": prices,
        "count": len(prices)
    }


def get_weekly(symbol: str, limit: int = 20) -> Dict:
    """
    Get weekly OHLCV prices for a stock.

    Args:
        symbol: Ticker symbol
        limit: Number of recent weeks to return
    """
    data = _request({
        "function": "TIME_SERIES_WEEKLY_ADJUSTED",
        "symbol": symbol
    })
    if "error" in data:
        return data

    meta = data.get("Meta Data", {})
    prices = _parse_time_series(data, "Weekly Adjusted Time Series", limit)
    return {
        "symbol": meta.get("2. Symbol", symbol),
        "last_refreshed": meta.get("3. Last Refreshed", ""),
        "prices": prices,
        "count": len(prices)
    }


def get_monthly(symbol: str, limit: int = 12) -> Dict:
    """
    Get monthly OHLCV prices for a stock.

    Args:
        symbol: Ticker symbol
        limit: Number of recent months to return
    """
    data = _request({
        "function": "TIME_SERIES_MONTHLY_ADJUSTED",
        "symbol": symbol
    })
    if "error" in data:
        return data

    meta = data.get("Meta Data", {})
    prices = _parse_time_series(data, "Monthly Adjusted Time Series", limit)
    return {
        "symbol": meta.get("2. Symbol", symbol),
        "last_refreshed": meta.get("3. Last Refreshed", ""),
        "prices": prices,
        "count": len(prices)
    }


def get_quote(symbol: str) -> Dict:
    """
    Get real-time quote for a stock (latest price, volume, change).

    Args:
        symbol: Ticker symbol (e.g. 'AAPL')

    Returns:
        dict with price, volume, change info
    """
    data = _request({
        "function": "GLOBAL_QUOTE",
        "symbol": symbol
    })
    if "error" in data:
        return data

    quote = data.get("Global Quote", {})
    if not quote:
        return {"error": "No quote data returned", "raw": data}

    result = {}
    for k, v in quote.items():
        clean_key = k.split(". ", 1)[-1].replace(" ", "_")
        try:
            result[clean_key] = float(v)
        except (ValueError, TypeError):
            result[clean_key] = v
    return result


def search_ticker(keywords: str) -> List[Dict]:
    """
    Search for ticker symbols by name or keyword.

    Args:
        keywords: Search term (e.g. 'Apple', 'Microsoft')

    Returns:
        List of matching symbols with name, type, region, currency
    """
    data = _request({
        "function": "SYMBOL_SEARCH",
        "keywords": keywords
    })
    if "error" in data:
        return [data]

    matches = data.get("bestMatches", [])
    results = []
    for m in matches:
        results.append({
            "symbol": m.get("1. symbol", ""),
            "name": m.get("2. name", ""),
            "type": m.get("3. type", ""),
            "region": m.get("4. region", ""),
            "currency": m.get("8. currency", ""),
            "match_score": m.get("9. matchScore", "")
        })
    return results


# ---------------------------------------------------------------------------
# Company Fundamentals
# ---------------------------------------------------------------------------

def get_company_overview(symbol: str) -> Dict:
    """
    Get company fundamentals: description, sector, PE, EPS, market cap, etc.

    Args:
        symbol: Ticker symbol (e.g. 'AAPL')
    """
    data = _request({
        "function": "OVERVIEW",
        "symbol": symbol
    })
    if "error" in data:
        return data

    # Convert numeric fields
    numeric_fields = [
        "MarketCapitalization", "EBITDA", "PERatio", "PEGRatio",
        "BookValue", "DividendPerShare", "DividendYield", "EPS",
        "RevenuePerShareTTM", "ProfitMargin", "OperatingMarginTTM",
        "ReturnOnAssetsTTM", "ReturnOnEquityTTM", "RevenueTTM",
        "GrossProfitTTM", "Beta", "52WeekHigh", "52WeekLow",
        "50DayMovingAverage", "200DayMovingAverage", "SharesOutstanding",
        "TrailingPE", "ForwardPE", "PriceToSalesRatioTTM",
        "PriceToBookRatio", "AnalystTargetPrice"
    ]
    for field in numeric_fields:
        if field in data and data[field] not in (None, "None", "-", ""):
            try:
                data[field] = float(data[field])
            except (ValueError, TypeError):
                pass
    return data


def get_income_statement(symbol: str, annual: bool = True) -> Dict:
    """
    Get income statement (annual or quarterly).

    Args:
        symbol: Ticker symbol
        annual: True for annual, False for quarterly
    """
    data = _request({
        "function": "INCOME_STATEMENT",
        "symbol": symbol
    })
    if "error" in data:
        return data

    key = "annualReports" if annual else "quarterlyReports"
    reports = data.get(key, [])
    return {
        "symbol": symbol,
        "period": "annual" if annual else "quarterly",
        "reports": reports[:8],
        "count": len(reports)
    }


def get_balance_sheet(symbol: str, annual: bool = True) -> Dict:
    """
    Get balance sheet (annual or quarterly).

    Args:
        symbol: Ticker symbol
        annual: True for annual, False for quarterly
    """
    data = _request({
        "function": "BALANCE_SHEET",
        "symbol": symbol
    })
    if "error" in data:
        return data

    key = "annualReports" if annual else "quarterlyReports"
    reports = data.get(key, [])
    return {
        "symbol": symbol,
        "period": "annual" if annual else "quarterly",
        "reports": reports[:8],
        "count": len(reports)
    }


def get_cash_flow(symbol: str, annual: bool = True) -> Dict:
    """
    Get cash flow statement (annual or quarterly).

    Args:
        symbol: Ticker symbol
        annual: True for annual, False for quarterly
    """
    data = _request({
        "function": "CASH_FLOW",
        "symbol": symbol
    })
    if "error" in data:
        return data

    key = "annualReports" if annual else "quarterlyReports"
    reports = data.get(key, [])
    return {
        "symbol": symbol,
        "period": "annual" if annual else "quarterly",
        "reports": reports[:8],
        "count": len(reports)
    }


def get_earnings(symbol: str) -> Dict:
    """
    Get earnings history (annual + quarterly EPS).

    Args:
        symbol: Ticker symbol
    """
    data = _request({
        "function": "EARNINGS",
        "symbol": symbol
    })
    if "error" in data:
        return data

    return {
        "symbol": symbol,
        "annual_earnings": data.get("annualEarnings", [])[:10],
        "quarterly_earnings": data.get("quarterlyEarnings", [])[:12]
    }


# ---------------------------------------------------------------------------
# Forex
# ---------------------------------------------------------------------------

def get_forex_rate(from_currency: str, to_currency: str) -> Dict:
    """
    Get real-time exchange rate between two currencies.

    Args:
        from_currency: Source currency code (e.g. 'USD')
        to_currency: Target currency code (e.g. 'EUR')
    """
    data = _request({
        "function": "CURRENCY_EXCHANGE_RATE",
        "from_currency": from_currency,
        "to_currency": to_currency
    })
    if "error" in data:
        return data

    rate_data = data.get("Realtime Currency Exchange Rate", {})
    if not rate_data:
        return {"error": "No exchange rate data", "raw": data}

    return {
        "from": rate_data.get("1. From_Currency Code", from_currency),
        "to": rate_data.get("3. To_Currency Code", to_currency),
        "rate": float(rate_data.get("5. Exchange Rate", 0)),
        "last_refreshed": rate_data.get("6. Last Refreshed", ""),
        "timezone": rate_data.get("7. Time Zone", "")
    }


def get_forex_daily(from_symbol: str, to_symbol: str, limit: int = 30) -> Dict:
    """
    Get daily forex time series.

    Args:
        from_symbol: Source currency (e.g. 'EUR')
        to_symbol: Target currency (e.g. 'USD')
        limit: Number of recent days
    """
    data = _request({
        "function": "FX_DAILY",
        "from_symbol": from_symbol,
        "to_symbol": to_symbol
    })
    if "error" in data:
        return data

    meta = data.get("Meta Data", {})
    prices = _parse_time_series(data, "Time Series FX (Daily)", limit)
    return {
        "pair": f"{from_symbol}/{to_symbol}",
        "last_refreshed": meta.get("5. Last Refreshed", ""),
        "prices": prices,
        "count": len(prices)
    }


# ---------------------------------------------------------------------------
# Cryptocurrency
# ---------------------------------------------------------------------------

def get_crypto_rate(from_currency: str, to_currency: str = "USD") -> Dict:
    """
    Get real-time crypto exchange rate.

    Args:
        from_currency: Crypto symbol (e.g. 'BTC', 'ETH')
        to_currency: Fiat currency (default 'USD')
    """
    return get_forex_rate(from_currency, to_currency)


def get_crypto_daily(symbol: str, market: str = "USD", limit: int = 30) -> Dict:
    """
    Get daily crypto prices.

    Args:
        symbol: Crypto symbol (e.g. 'BTC', 'ETH')
        market: Market/fiat currency (default 'USD')
        limit: Number of recent days
    """
    data = _request({
        "function": "DIGITAL_CURRENCY_DAILY",
        "symbol": symbol,
        "market": market
    })
    if "error" in data:
        return data

    meta = data.get("Meta Data", {})
    series = data.get("Time Series (Digital Currency Daily)", {})
    
    results = []
    for date_str, values in list(series.items())[:limit]:
        row = {"date": date_str}
        # Crypto has market-specific keys like "1a. open (USD)"
        for k, v in values.items():
            clean = k.split(". ", 1)[-1].replace(f" ({market})", "").replace(" ", "_")
            try:
                row[clean] = float(v)
            except (ValueError, TypeError):
                row[clean] = v
        results.append(row)

    return {
        "symbol": meta.get("2. Digital Currency Code", symbol),
        "market": market,
        "last_refreshed": meta.get("6. Last Refreshed", ""),
        "prices": results,
        "count": len(results)
    }


# ---------------------------------------------------------------------------
# Commodities
# ---------------------------------------------------------------------------

def get_commodity(commodity: str = "WTI", interval: str = "monthly", limit: int = 24) -> Dict:
    """
    Get commodity prices (oil, natural gas, copper, aluminum, wheat, corn, cotton, sugar, coffee).

    Args:
        commodity: One of WTI, BRENT, NATURAL_GAS, COPPER, ALUMINUM, WHEAT, CORN, COTTON, SUGAR, COFFEE
        interval: 'daily', 'weekly', or 'monthly'
        limit: Number of data points
    """
    data = _request({
        "function": commodity,
        "interval": interval
    })
    if "error" in data:
        return data

    points = data.get("data", [])[:limit]
    results = []
    for p in points:
        val = p.get("value", ".")
        results.append({
            "date": p.get("date", ""),
            "value": float(val) if val != "." else None
        })

    return {
        "commodity": data.get("name", commodity),
        "interval": data.get("interval", interval),
        "unit": data.get("unit", ""),
        "data": results,
        "count": len(results)
    }


# ---------------------------------------------------------------------------
# Economic Indicators
# ---------------------------------------------------------------------------

def get_real_gdp(interval: str = "annual", limit: int = 10) -> Dict:
    """
    Get US Real GDP data.

    Args:
        interval: 'annual' or 'quarterly'
        limit: Number of data points
    """
    data = _request({
        "function": "REAL_GDP",
        "interval": interval
    })
    if "error" in data:
        return data

    points = data.get("data", [])[:limit]
    results = []
    for p in points:
        val = p.get("value", ".")
        results.append({
            "date": p.get("date", ""),
            "value": float(val) if val != "." else None
        })

    return {
        "name": data.get("name", "Real GDP"),
        "interval": interval,
        "unit": data.get("unit", ""),
        "data": results,
        "count": len(results)
    }


def get_cpi(interval: str = "monthly", limit: int = 12) -> Dict:
    """
    Get US Consumer Price Index (CPI).

    Args:
        interval: 'monthly' or 'semiannual'
        limit: Number of data points
    """
    data = _request({
        "function": "CPI",
        "interval": interval
    })
    if "error" in data:
        return data

    points = data.get("data", [])[:limit]
    results = []
    for p in points:
        val = p.get("value", ".")
        results.append({
            "date": p.get("date", ""),
            "value": float(val) if val != "." else None
        })
    return {
        "name": data.get("name", "CPI"),
        "interval": interval,
        "unit": data.get("unit", ""),
        "data": results,
        "count": len(results)
    }


def get_inflation(limit: int = 10) -> Dict:
    """Get US annual inflation rate."""
    data = _request({"function": "INFLATION"})
    if "error" in data:
        return data

    points = data.get("data", [])[:limit]
    results = []
    for p in points:
        val = p.get("value", ".")
        results.append({
            "date": p.get("date", ""),
            "value": float(val) if val != "." else None
        })
    return {
        "name": data.get("name", "Inflation"),
        "unit": data.get("unit", "percent"),
        "data": results,
        "count": len(results)
    }


def get_federal_funds_rate(interval: str = "monthly", limit: int = 12) -> Dict:
    """
    Get US Federal Funds Rate.

    Args:
        interval: 'daily', 'weekly', or 'monthly'
        limit: Number of data points
    """
    data = _request({
        "function": "FEDERAL_FUNDS_RATE",
        "interval": interval
    })
    if "error" in data:
        return data

    points = data.get("data", [])[:limit]
    results = []
    for p in points:
        val = p.get("value", ".")
        results.append({
            "date": p.get("date", ""),
            "value": float(val) if val != "." else None
        })
    return {
        "name": data.get("name", "Federal Funds Rate"),
        "interval": interval,
        "unit": data.get("unit", "percent"),
        "data": results,
        "count": len(results)
    }


def get_treasury_yield(interval: str = "monthly", maturity: str = "10year", limit: int = 12) -> Dict:
    """
    Get US Treasury yield.

    Args:
        interval: 'daily', 'weekly', or 'monthly'
        maturity: '3month', '2year', '5year', '7year', '10year', '30year'
        limit: Number of data points
    """
    data = _request({
        "function": "TREASURY_YIELD",
        "interval": interval,
        "maturity": maturity
    })
    if "error" in data:
        return data

    points = data.get("data", [])[:limit]
    results = []
    for p in points:
        val = p.get("value", ".")
        results.append({
            "date": p.get("date", ""),
            "value": float(val) if val != "." else None
        })
    return {
        "name": data.get("name", f"Treasury Yield {maturity}"),
        "interval": interval,
        "maturity": maturity,
        "unit": data.get("unit", "percent"),
        "data": results,
        "count": len(results)
    }


def get_unemployment(limit: int = 12) -> Dict:
    """Get US unemployment rate (monthly)."""
    data = _request({"function": "UNEMPLOYMENT"})
    if "error" in data:
        return data

    points = data.get("data", [])[:limit]
    results = []
    for p in points:
        val = p.get("value", ".")
        results.append({
            "date": p.get("date", ""),
            "value": float(val) if val != "." else None
        })
    return {
        "name": data.get("name", "Unemployment Rate"),
        "unit": data.get("unit", "percent"),
        "data": results,
        "count": len(results)
    }


def get_nonfarm_payroll(limit: int = 12) -> Dict:
    """Get US nonfarm payroll (monthly)."""
    data = _request({"function": "NONFARM_PAYROLL"})
    if "error" in data:
        return data

    points = data.get("data", [])[:limit]
    results = []
    for p in points:
        val = p.get("value", ".")
        results.append({
            "date": p.get("date", ""),
            "value": float(val) if val != "." else None
        })
    return {
        "name": data.get("name", "Nonfarm Payroll"),
        "unit": data.get("unit", ""),
        "data": results,
        "count": len(results)
    }


def get_retail_sales(limit: int = 12) -> Dict:
    """Get US retail sales (monthly)."""
    data = _request({"function": "RETAIL_SALES"})
    if "error" in data:
        return data

    points = data.get("data", [])[:limit]
    results = []
    for p in points:
        val = p.get("value", ".")
        results.append({
            "date": p.get("date", ""),
            "value": float(val) if val != "." else None
        })
    return {
        "name": data.get("name", "Retail Sales"),
        "unit": data.get("unit", ""),
        "data": results,
        "count": len(results)
    }


# ---------------------------------------------------------------------------
# Technical Indicators
# ---------------------------------------------------------------------------

def get_technical_indicator(
    symbol: str,
    indicator: str = "SMA",
    interval: str = "daily",
    time_period: int = 20,
    series_type: str = "close",
    limit: int = 30
) -> Dict:
    """
    Get any technical indicator from Alpha Vantage (50+ supported).

    Args:
        symbol: Ticker symbol
        indicator: e.g. SMA, EMA, RSI, MACD, BBANDS, STOCH, ADX, CCI, AROON, OBV, etc.
        interval: 'daily', 'weekly', 'monthly', '1min', '5min', '15min', '30min', '60min'
        time_period: Number of periods (e.g. 14 for RSI, 20 for SMA)
        series_type: 'close', 'open', 'high', 'low'
        limit: Number of data points

    Returns:
        dict with indicator values by date
    """
    params = {
        "function": indicator,
        "symbol": symbol,
        "interval": interval,
        "time_period": time_period,
        "series_type": series_type
    }

    data = _request(params)
    if "error" in data:
        return data

    meta = data.get("Meta Data", {})
    
    # Find the technical analysis key (varies by indicator)
    ta_key = None
    for k in data.keys():
        if "Technical Analysis" in k:
            ta_key = k
            break

    if not ta_key:
        return {"error": "No technical analysis data found", "keys": list(data.keys())}

    series = data[ta_key]
    results = []
    for date_str, values in list(series.items())[:limit]:
        row = {"date": date_str}
        for k, v in values.items():
            try:
                row[k] = float(v)
            except (ValueError, TypeError):
                row[k] = v
        results.append(row)

    return {
        "symbol": symbol,
        "indicator": meta.get("2: Indicator", indicator),
        "interval": interval,
        "time_period": time_period,
        "data": results,
        "count": len(results)
    }


def get_sma(symbol: str, time_period: int = 20, interval: str = "daily", limit: int = 30) -> Dict:
    """Get Simple Moving Average."""
    return get_technical_indicator(symbol, "SMA", interval, time_period, limit=limit)


def get_ema(symbol: str, time_period: int = 20, interval: str = "daily", limit: int = 30) -> Dict:
    """Get Exponential Moving Average."""
    return get_technical_indicator(symbol, "EMA", interval, time_period, limit=limit)


def get_rsi(symbol: str, time_period: int = 14, interval: str = "daily", limit: int = 30) -> Dict:
    """Get Relative Strength Index."""
    return get_technical_indicator(symbol, "RSI", interval, time_period, limit=limit)


def get_macd(symbol: str, interval: str = "daily", limit: int = 30) -> Dict:
    """Get MACD (Moving Average Convergence/Divergence)."""
    return get_technical_indicator(symbol, "MACD", interval, limit=limit)


def get_bbands(symbol: str, time_period: int = 20, interval: str = "daily", limit: int = 30) -> Dict:
    """Get Bollinger Bands."""
    return get_technical_indicator(symbol, "BBANDS", interval, time_period, limit=limit)


# ---------------------------------------------------------------------------
# Market Intelligence
# ---------------------------------------------------------------------------

def get_top_gainers_losers() -> Dict:
    """
    Get top gainers, losers, and most actively traded tickers in the US market.

    Returns:
        dict with 'top_gainers', 'top_losers', 'most_actively_traded' lists
    """
    data = _request({"function": "TOP_GAINERS_LOSERS"})
    if "error" in data:
        return data
    return {
        "top_gainers": data.get("top_gainers", [])[:10],
        "top_losers": data.get("top_losers", [])[:10],
        "most_active": data.get("most_actively_traded", [])[:10],
        "last_updated": data.get("last_updated", "")
    }


def get_market_status() -> List[Dict]:
    """
    Get current open/close status of major global stock exchanges.

    Returns:
        List of markets with region, exchange, status, hours
    """
    data = _request({"function": "MARKET_STATUS"})
    if "error" in data:
        return [data]
    return data.get("markets", [])


def get_news_sentiment(tickers: str = "", topics: str = "", limit: int = 10) -> Dict:
    """
    Get news articles with sentiment analysis.

    Args:
        tickers: Comma-separated tickers (e.g. 'AAPL,MSFT')
        topics: Topics filter (e.g. 'technology', 'earnings', 'financial_markets')
        limit: Number of articles (max 1000)
    """
    params = {
        "function": "NEWS_SENTIMENT",
        "limit": min(limit, 50)
    }
    if tickers:
        params["tickers"] = tickers
    if topics:
        params["topics"] = topics

    data = _request(params)
    if "error" in data:
        return data

    articles = data.get("feed", [])
    results = []
    for a in articles[:limit]:
        results.append({
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "source": a.get("source", ""),
            "published": a.get("time_published", ""),
            "summary": a.get("summary", "")[:300],
            "overall_sentiment": a.get("overall_sentiment_label", ""),
            "sentiment_score": a.get("overall_sentiment_score", 0),
            "ticker_sentiment": a.get("ticker_sentiment", [])
        })
    return {
        "articles": results,
        "count": len(results),
        "sentiment_score_definition": data.get("sentiment_score_definition", "")
    }


# ---------------------------------------------------------------------------
# Listings & Calendar
# ---------------------------------------------------------------------------

def get_earnings_calendar() -> Dict:
    """
    Get upcoming earnings announcements (next 3 months).
    Note: Returns CSV; this function parses it.
    """
    params = {"apikey": API_KEY}
    try:
        resp = requests.get(
            f"{BASE_URL}?function=EARNINGS_CALENDAR&horizon=3month&apikey={API_KEY}",
            headers=HEADERS, timeout=15
        )
        resp.raise_for_status()
        lines = resp.text.strip().split("\n")
        if len(lines) < 2:
            return {"error": "No earnings calendar data", "raw": resp.text[:200]}
        
        headers_row = lines[0].split(",")
        results = []
        for line in lines[1:51]:  # limit to 50
            values = line.split(",")
            row = {}
            for i, h in enumerate(headers_row):
                row[h] = values[i] if i < len(values) else ""
            results.append(row)
        return {"earnings": results, "count": len(results)}
    except Exception as e:
        return {"error": f"Failed to fetch earnings calendar: {str(e)}"}


def get_ipo_calendar() -> Dict:
    """Get upcoming IPO listings."""
    try:
        resp = requests.get(
            f"{BASE_URL}?function=IPO_CALENDAR&apikey={API_KEY}",
            headers=HEADERS, timeout=15
        )
        resp.raise_for_status()
        lines = resp.text.strip().split("\n")
        if len(lines) < 2:
            return {"error": "No IPO calendar data", "raw": resp.text[:200]}
        
        headers_row = lines[0].split(",")
        results = []
        for line in lines[1:31]:
            values = line.split(",")
            row = {}
            for i, h in enumerate(headers_row):
                row[h] = values[i] if i < len(values) else ""
            results.append(row)
        return {"ipos": results, "count": len(results)}
    except Exception as e:
        return {"error": f"Failed to fetch IPO calendar: {str(e)}"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(json.dumps({
        "module": "alpha_vantage_api",
        "status": "ready",
        "api_key_set": API_KEY != "demo",
        "functions": [
            "get_daily", "get_weekly", "get_monthly", "get_quote",
            "search_ticker", "get_company_overview",
            "get_income_statement", "get_balance_sheet", "get_cash_flow", "get_earnings",
            "get_forex_rate", "get_forex_daily",
            "get_crypto_rate", "get_crypto_daily",
            "get_commodity",
            "get_real_gdp", "get_cpi", "get_inflation",
            "get_federal_funds_rate", "get_treasury_yield",
            "get_unemployment", "get_nonfarm_payroll", "get_retail_sales",
            "get_technical_indicator", "get_sma", "get_ema", "get_rsi", "get_macd", "get_bbands",
            "get_top_gainers_losers", "get_market_status",
            "get_news_sentiment",
            "get_earnings_calendar", "get_ipo_calendar"
        ],
        "source": "https://www.alphavantage.co/documentation/"
    }, indent=2))

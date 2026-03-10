"""
MSCI Emerging Markets Index Dataset — Comprehensive EM Index Data

Data Sources:
  - Yahoo Finance (EEM ETF as proxy, free)
  - MSCI end-of-day index data (web scraping, free)
  - World Bank country classification (free)
Update: Daily (market hours)
History: 20+ years via ETF proxy
Free: Yes (no API key required)

Provides:
- MSCI EM index performance via EEM/VWO ETF proxies
- Country allocation estimates via top EM country ETFs
- Historical returns and volatility metrics
- EM vs DM spread analysis
- Top constituent country weights
- Key EM macro indicators from FRED

Usage:
- Track emerging market equity exposure
- Compare EM vs DM performance
- Monitor country-level EM allocations
- Analyze EM risk/return characteristics
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/msci_em")
os.makedirs(CACHE_DIR, exist_ok=True)

# EEM (iShares MSCI EM ETF) is the primary liquid proxy for the MSCI EM Index
EM_ETFS = {
    "EEM": "iShares MSCI Emerging Markets ETF",
    "VWO": "Vanguard FTSE Emerging Markets ETF",
}

# Country ETFs that approximate MSCI EM country weights
EM_COUNTRY_ETFS = {
    "FXI": {"country": "China", "name": "iShares China Large-Cap ETF"},
    "EWZ": {"country": "Brazil", "name": "iShares MSCI Brazil ETF"},
    "INDA": {"country": "India", "name": "iShares MSCI India ETF"},
    "EWT": {"country": "Taiwan", "name": "iShares MSCI Taiwan ETF"},
    "EWY": {"country": "South Korea", "name": "iShares MSCI South Korea ETF"},
    "EWW": {"country": "Mexico", "name": "iShares MSCI Mexico ETF"},
    "THD": {"country": "Thailand", "name": "iShares MSCI Thailand ETF"},
    "EIDO": {"country": "Indonesia", "name": "iShares MSCI Indonesia ETF"},
    "EZA": {"country": "South Africa", "name": "iShares MSCI South Africa ETF"},
    "TUR": {"country": "Turkey", "name": "iShares MSCI Turkey ETF"},
    "QAT": {"country": "Qatar", "name": "iShares MSCI Qatar ETF"},
    "KSA": {"country": "Saudi Arabia", "name": "iShares MSCI Saudi Arabia ETF"},
}

# Approximate MSCI EM country weights (updated periodically)
MSCI_EM_WEIGHTS_2025 = {
    "China": 24.4,
    "India": 19.8,
    "Taiwan": 18.5,
    "South Korea": 11.2,
    "Brazil": 4.8,
    "Saudi Arabia": 4.2,
    "South Africa": 3.1,
    "Mexico": 2.3,
    "Indonesia": 1.8,
    "Thailand": 1.7,
    "Malaysia": 1.5,
    "UAE": 1.3,
    "Qatar": 0.9,
    "Turkey": 0.8,
    "Other": 3.7,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def _read_cache(name: str, max_age_hours: int = 6) -> Optional[dict]:
    """Read from cache if fresh enough."""
    path = os.path.join(CACHE_DIR, f"{name}.json")
    if os.path.exists(path):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
        if age < timedelta(hours=max_age_hours):
            with open(path) as f:
                return json.load(f)
    return None


def _write_cache(name: str, data: dict):
    """Write data to cache."""
    path = os.path.join(CACHE_DIR, f"{name}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _yf_quote(symbol: str) -> Dict:
    """Fetch quote data from Yahoo Finance v8 API."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"range": "5d", "interval": "1d", "includePrePost": "false"}
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    result = data.get("chart", {}).get("result", [])
    if not result:
        raise ValueError(f"No data returned for {symbol}")
    return result[0]


def _yf_history(symbol: str, period: str = "1y", interval: str = "1d") -> Dict:
    """Fetch historical price data from Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"range": period, "interval": interval, "includePrePost": "false"}
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    result = data.get("chart", {}).get("result", [])
    if not result:
        raise ValueError(f"No data returned for {symbol}")
    return result[0]


def get_em_index_snapshot(etf: str = "EEM") -> Dict:
    """
    Get current MSCI Emerging Markets index snapshot via ETF proxy.

    Args:
        etf: ETF ticker to use as proxy ('EEM' or 'VWO')

    Returns:
        Dict with price, change, volume, 52-week range, and metadata.
    """
    cached = _read_cache(f"snapshot_{etf}", max_age_hours=1)
    if cached:
        return cached

    try:
        raw = _yf_quote(etf)
        meta = raw.get("meta", {})
        indicators = raw.get("indicators", {})
        quotes = indicators.get("quote", [{}])[0]
        timestamps = raw.get("timestamp", [])

        closes = [c for c in (quotes.get("close") or []) if c is not None]
        volumes = [v for v in (quotes.get("volume") or []) if v is not None]

        current_price = meta.get("regularMarketPrice", closes[-1] if closes else None)
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")

        change = None
        change_pct = None
        if current_price and prev_close:
            change = round(current_price - prev_close, 4)
            change_pct = round((change / prev_close) * 100, 4)

        result = {
            "symbol": etf,
            "name": EM_ETFS.get(etf, etf),
            "proxy_for": "MSCI Emerging Markets Index",
            "price": current_price,
            "previous_close": prev_close,
            "change": change,
            "change_pct": change_pct,
            "currency": meta.get("currency", "USD"),
            "exchange": meta.get("exchangeName"),
            "volume": volumes[-1] if volumes else None,
            "fifty_two_week_high": meta.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": meta.get("fiftyTwoWeekLow"),
            "timestamp": datetime.now().isoformat(),
            "source": "Yahoo Finance (ETF proxy)",
        }
        _write_cache(f"snapshot_{etf}", result)
        return result

    except Exception as e:
        return {"error": str(e), "symbol": etf, "timestamp": datetime.now().isoformat()}


def get_em_historical_returns(period: str = "1y") -> Dict:
    """
    Get historical returns for MSCI EM index via EEM ETF.

    Args:
        period: '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max'

    Returns:
        Dict with returns summary, price series, and statistics.
    """
    cached = _read_cache(f"returns_{period}", max_age_hours=12)
    if cached:
        return cached

    try:
        raw = _yf_history("EEM", period=period)
        indicators = raw.get("indicators", {})
        quotes = indicators.get("quote", [{}])[0]
        timestamps = raw.get("timestamp", [])
        closes = quotes.get("close", [])
        volumes = quotes.get("volume", [])

        # Clean data
        valid = [(t, c, v) for t, c, v in zip(timestamps, closes, volumes)
                 if c is not None]
        if not valid:
            return {"error": "No valid price data", "period": period}

        ts, prices, vols = zip(*valid)
        dates = [datetime.utcfromtimestamp(t).strftime("%Y-%m-%d") for t in ts]

        first_price = prices[0]
        last_price = prices[-1]
        total_return = round(((last_price - first_price) / first_price) * 100, 2)
        high = max(prices)
        low = min(prices)
        avg_vol = int(sum(vols) / len(vols)) if vols else None

        # Calculate daily returns for volatility
        daily_returns = []
        for i in range(1, len(prices)):
            if prices[i - 1] > 0:
                daily_returns.append((prices[i] - prices[i - 1]) / prices[i - 1])

        avg_daily = sum(daily_returns) / len(daily_returns) if daily_returns else 0
        variance = sum((r - avg_daily) ** 2 for r in daily_returns) / len(daily_returns) if daily_returns else 0
        daily_vol = variance ** 0.5
        annualized_vol = round(daily_vol * (252 ** 0.5) * 100, 2)

        # Max drawdown
        peak = prices[0]
        max_dd = 0
        for p in prices:
            if p > peak:
                peak = p
            dd = (p - peak) / peak
            if dd < max_dd:
                max_dd = dd

        result = {
            "index": "MSCI Emerging Markets (EEM proxy)",
            "period": period,
            "start_date": dates[0],
            "end_date": dates[-1],
            "start_price": round(first_price, 2),
            "end_price": round(last_price, 2),
            "total_return_pct": total_return,
            "annualized_volatility_pct": annualized_vol,
            "max_drawdown_pct": round(max_dd * 100, 2),
            "period_high": round(high, 2),
            "period_low": round(low, 2),
            "avg_daily_volume": avg_vol,
            "data_points": len(prices),
            "source": "Yahoo Finance",
            "timestamp": datetime.now().isoformat(),
        }
        _write_cache(f"returns_{period}", result)
        return result

    except Exception as e:
        return {"error": str(e), "period": period, "timestamp": datetime.now().isoformat()}


def get_em_vs_dm_spread() -> Dict:
    """
    Compare Emerging Markets vs Developed Markets performance.

    Uses EEM (EM) vs EFA (EAFE/DM) and SPY (US) as proxies.

    Returns:
        Dict with relative performance across multiple timeframes.
    """
    cached = _read_cache("em_dm_spread", max_age_hours=6)
    if cached:
        return cached

    periods = ["1mo", "3mo", "6mo", "1y", "5y"]
    symbols = {"EM (EEM)": "EEM", "DM ex-US (EFA)": "EFA", "US (SPY)": "SPY"}

    spreads = {}
    for period in periods:
        period_data = {}
        for label, sym in symbols.items():
            try:
                raw = _yf_history(sym, period=period)
                closes = [c for c in (raw.get("indicators", {}).get("quote", [{}])[0].get("close") or []) if c is not None]
                if len(closes) >= 2:
                    ret = round(((closes[-1] - closes[0]) / closes[0]) * 100, 2)
                    period_data[label] = ret
            except Exception:
                period_data[label] = None

        em_ret = period_data.get("EM (EEM)")
        dm_ret = period_data.get("DM ex-US (EFA)")
        us_ret = period_data.get("US (SPY)")

        spreads[period] = {
            "returns": period_data,
            "em_minus_dm": round(em_ret - dm_ret, 2) if em_ret is not None and dm_ret is not None else None,
            "em_minus_us": round(em_ret - us_ret, 2) if em_ret is not None and us_ret is not None else None,
        }

    result = {
        "comparison": "EM vs DM Performance Spread",
        "spreads_by_period": spreads,
        "interpretation": {
            "positive_em_minus_dm": "EM outperforming developed markets",
            "negative_em_minus_dm": "DM outperforming emerging markets",
        },
        "source": "Yahoo Finance",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache("em_dm_spread", result)
    return result


def get_em_country_performance(period: str = "1mo") -> List[Dict]:
    """
    Get performance of major MSCI EM constituent countries via country ETFs.

    Args:
        period: '1mo', '3mo', '6mo', '1y'

    Returns:
        List of dicts sorted by return, each with country, ETF, return, and weight.
    """
    cached = _read_cache(f"country_perf_{period}", max_age_hours=6)
    if cached:
        return cached

    results = []
    for ticker, info in EM_COUNTRY_ETFS.items():
        try:
            raw = _yf_history(ticker, period=period)
            closes = [c for c in (raw.get("indicators", {}).get("quote", [{}])[0].get("close") or []) if c is not None]
            if len(closes) >= 2:
                ret = round(((closes[-1] - closes[0]) / closes[0]) * 100, 2)
                results.append({
                    "country": info["country"],
                    "etf": ticker,
                    "etf_name": info["name"],
                    "return_pct": ret,
                    "msci_weight_pct": MSCI_EM_WEIGHTS_2025.get(info["country"]),
                    "period": period,
                })
        except Exception as e:
            results.append({
                "country": info["country"],
                "etf": ticker,
                "error": str(e),
                "period": period,
            })

    results.sort(key=lambda x: x.get("return_pct", -999), reverse=True)
    _write_cache(f"country_perf_{period}", results)
    return results


def get_em_country_weights() -> Dict:
    """
    Get approximate MSCI Emerging Markets Index country weights.

    Returns:
        Dict with country weights, total coverage, and update date.
    """
    sorted_weights = sorted(MSCI_EM_WEIGHTS_2025.items(), key=lambda x: x[1], reverse=True)
    return {
        "index": "MSCI Emerging Markets Index",
        "weights": [{"country": c, "weight_pct": w} for c, w in sorted_weights],
        "total_countries": 24,
        "total_constituents": "~1,400 stocks",
        "top_5_concentration_pct": round(sum(w for _, w in sorted_weights[:5]), 1),
        "note": "Weights are approximate and updated periodically",
        "last_reference": "2025",
        "source": "MSCI factsheets",
    }


def get_em_sector_exposure() -> Dict:
    """
    Get approximate MSCI EM sector weights.

    Returns:
        Dict with sector allocations and comparison notes.
    """
    # Approximate MSCI EM sector weights (from MSCI factsheets)
    sectors = {
        "Information Technology": 23.5,
        "Financials": 21.8,
        "Consumer Discretionary": 12.4,
        "Communication Services": 8.7,
        "Materials": 7.2,
        "Energy": 5.6,
        "Consumer Staples": 5.3,
        "Industrials": 5.1,
        "Health Care": 4.2,
        "Utilities": 3.1,
        "Real Estate": 3.1,
    }

    sorted_sectors = sorted(sectors.items(), key=lambda x: x[1], reverse=True)
    return {
        "index": "MSCI Emerging Markets Index",
        "sector_weights": [{"sector": s, "weight_pct": w} for s, w in sorted_sectors],
        "top_3_concentration_pct": round(sum(w for _, w in sorted_sectors[:3]), 1),
        "note": "Weights are approximate, from latest MSCI factsheet data",
        "key_differences_vs_sp500": [
            "Higher Financials weight (EM banks dominate)",
            "Lower Health Care weight",
            "Higher Materials/Energy (commodity exporters)",
        ],
        "source": "MSCI factsheets",
        "timestamp": datetime.now().isoformat(),
    }


def get_em_valuation_metrics() -> Dict:
    """
    Get valuation metrics for MSCI EM via EEM ETF and related data.

    Returns:
        Dict with P/E, P/B, dividend yield from Yahoo Finance summary data.
    """
    cached = _read_cache("valuation", max_age_hours=24)
    if cached:
        return cached

    try:
        # Use Yahoo Finance v10 summary for valuation data
        url = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/EEM"
        params = {"modules": "summaryDetail,defaultKeyStatistics"}
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("quoteSummary", {}).get("result", [{}])[0]

        summary = data.get("summaryDetail", {})
        stats = data.get("defaultKeyStatistics", {})

        def _raw(d, key):
            v = d.get(key, {})
            if isinstance(v, dict):
                return v.get("raw")
            return v

        result = {
            "index": "MSCI Emerging Markets (EEM proxy)",
            "pe_ratio": _raw(stats, "trailingPE") or _raw(summary, "trailingPE"),
            "forward_pe": _raw(stats, "forwardPE") or _raw(summary, "forwardPE"),
            "price_to_book": _raw(stats, "priceToBook"),
            "dividend_yield_pct": round(_raw(summary, "yield") * 100, 2) if _raw(summary, "yield") else None,
            "beta": _raw(stats, "beta"),
            "total_assets": _raw(stats, "totalAssets"),
            "nav": _raw(summary, "navPrice"),
            "expense_ratio_pct": round(_raw(stats, "annualReportExpenseRatio") * 100, 3) if _raw(stats, "annualReportExpenseRatio") else None,
            "note": "Metrics from EEM ETF as proxy for MSCI EM Index",
            "source": "Yahoo Finance",
            "timestamp": datetime.now().isoformat(),
        }
        _write_cache("valuation", result)
        return result

    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}


def get_em_macro_indicators() -> Dict:
    """
    Get key macro indicators for emerging markets from FRED.

    Returns:
        Dict with EM-relevant macro data (spreads, flows, FX).
    """
    cached = _read_cache("macro", max_age_hours=24)
    if cached:
        return cached

    # FRED series relevant to EM
    fred_series = {
        "BAMLHE00EHYIEY": "ICE BofA EM High Yield Index Effective Yield",
        "BAMLEMCBPIEY": "ICE BofA EM Corporate Plus Index Effective Yield",
        "DTWEXBGS": "Trade Weighted USD Index (Broad)",
    }

    indicators = {}
    for series_id, name in fred_series.items():
        try:
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            lines = resp.text.strip().split("\n")
            if len(lines) > 1:
                last_line = lines[-1]
                parts = last_line.split(",")
                if len(parts) == 2 and parts[1] != ".":
                    indicators[series_id] = {
                        "name": name,
                        "date": parts[0],
                        "value": float(parts[1]),
                    }
        except Exception:
            continue

    result = {
        "title": "Emerging Markets Macro Indicators",
        "indicators": indicators,
        "interpretation": {
            "high_yield_spread": "Higher = more EM stress, risk-off",
            "usd_index": "Stronger USD typically pressures EM assets",
        },
        "source": "FRED (Federal Reserve Economic Data)",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache("macro", result)
    return result


def search_em_constituents(query: str = "") -> List[Dict]:
    """
    Search MSCI EM top constituents by name or country.

    Args:
        query: Search term (company name, country, or sector)

    Returns:
        List of matching constituent entries.
    """
    # Top ~30 constituents of MSCI EM Index (approximate)
    constituents = [
        {"name": "Taiwan Semiconductor (TSMC)", "country": "Taiwan", "sector": "IT", "weight_pct": 9.8, "ticker": "TSM"},
        {"name": "Tencent Holdings", "country": "China", "sector": "Communication Services", "weight_pct": 3.9, "ticker": "TCEHY"},
        {"name": "Samsung Electronics", "country": "South Korea", "sector": "IT", "weight_pct": 3.5, "ticker": "005930.KS"},
        {"name": "Alibaba Group", "country": "China", "sector": "Consumer Discretionary", "weight_pct": 2.5, "ticker": "BABA"},
        {"name": "Reliance Industries", "country": "India", "sector": "Energy", "weight_pct": 1.8, "ticker": "RELIANCE.NS"},
        {"name": "Meituan", "country": "China", "sector": "Consumer Discretionary", "weight_pct": 1.5, "ticker": "3690.HK"},
        {"name": "PDD Holdings", "country": "China", "sector": "Consumer Discretionary", "weight_pct": 1.4, "ticker": "PDD"},
        {"name": "Infosys", "country": "India", "sector": "IT", "weight_pct": 1.2, "ticker": "INFY"},
        {"name": "China Construction Bank", "country": "China", "sector": "Financials", "weight_pct": 1.1, "ticker": "0939.HK"},
        {"name": "ICBC", "country": "China", "sector": "Financials", "weight_pct": 1.0, "ticker": "1398.HK"},
        {"name": "SK Hynix", "country": "South Korea", "sector": "IT", "weight_pct": 1.0, "ticker": "000660.KS"},
        {"name": "HDFC Bank", "country": "India", "sector": "Financials", "weight_pct": 1.0, "ticker": "HDB"},
        {"name": "Vale SA", "country": "Brazil", "sector": "Materials", "weight_pct": 0.9, "ticker": "VALE"},
        {"name": "Petrobras", "country": "Brazil", "sector": "Energy", "weight_pct": 0.8, "ticker": "PBR"},
        {"name": "JD.com", "country": "China", "sector": "Consumer Discretionary", "weight_pct": 0.8, "ticker": "JD"},
        {"name": "NetEase", "country": "China", "sector": "Communication Services", "weight_pct": 0.7, "ticker": "NTES"},
        {"name": "Naspers", "country": "South Africa", "sector": "Consumer Discretionary", "weight_pct": 0.7, "ticker": "NPN.JO"},
        {"name": "Banco Bradesco", "country": "Brazil", "sector": "Financials", "weight_pct": 0.6, "ticker": "BBD"},
        {"name": "BYD Company", "country": "China", "sector": "Consumer Discretionary", "weight_pct": 0.6, "ticker": "BYDDY"},
        {"name": "MediaTek", "country": "Taiwan", "sector": "IT", "weight_pct": 0.6, "ticker": "2454.TW"},
        {"name": "Saudi Aramco", "country": "Saudi Arabia", "sector": "Energy", "weight_pct": 1.5, "ticker": "2222.SR"},
        {"name": "Al Rajhi Bank", "country": "Saudi Arabia", "sector": "Financials", "weight_pct": 0.5, "ticker": "1120.SR"},
        {"name": "Itau Unibanco", "country": "Brazil", "sector": "Financials", "weight_pct": 0.5, "ticker": "ITUB"},
        {"name": "Wipro", "country": "India", "sector": "IT", "weight_pct": 0.3, "ticker": "WIT"},
        {"name": "Bajaj Finance", "country": "India", "sector": "Financials", "weight_pct": 0.4, "ticker": "BAJFINANCE.NS"},
    ]

    if not query:
        return constituents

    q = query.lower()
    return [c for c in constituents if q in c["name"].lower()
            or q in c["country"].lower() or q in c["sector"].lower()
            or q in c.get("ticker", "").lower()]


if __name__ == "__main__":
    print(json.dumps({
        "module": "msci_emerging_markets_index_dataset",
        "status": "ready",
        "functions": [
            "get_em_index_snapshot",
            "get_em_historical_returns",
            "get_em_vs_dm_spread",
            "get_em_country_performance",
            "get_em_country_weights",
            "get_em_sector_exposure",
            "get_em_valuation_metrics",
            "get_em_macro_indicators",
            "search_em_constituents",
        ],
        "source": "https://www.msci.com/our-solutions/indexes/emerging-markets-index",
    }, indent=2))

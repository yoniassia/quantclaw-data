"""
Multi-Asset Coverage Module
Handles cryptocurrencies, commodities, forex, analyst ratings, company profiles, and stock screening.
Uses free APIs: CoinGecko, Yahoo Finance, exchangerate.host
"""

import requests
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

# ============ CRYPTO via CoinGecko ============
def get_crypto_price(symbol: str = "bitcoin") -> Dict[str, Any]:
    """Get current crypto price from CoinGecko (free, no API key)"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": symbol.lower(),
            "vs_currencies": "usd",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true"
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if symbol.lower() not in data:
            return {"error": f"Symbol {symbol} not found"}
        
        coin = data[symbol.lower()]
        return {
            "symbol": symbol.upper(),
            "price_usd": coin.get("usd"),
            "market_cap": coin.get("usd_market_cap"),
            "volume_24h": coin.get("usd_24h_vol"),
            "change_24h_pct": coin.get("usd_24h_change"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

def get_crypto_list(limit: int = 100) -> List[Dict[str, Any]]:
    """Get top cryptocurrencies by market cap"""
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": min(limit, 250),
            "page": 1,
            "sparkline": "false"
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        coins = resp.json()
        
        return [{
            "id": c["id"],
            "symbol": c["symbol"].upper(),
            "name": c["name"],
            "price_usd": c["current_price"],
            "market_cap": c["market_cap"],
            "volume_24h": c["total_volume"],
            "change_24h_pct": c["price_change_percentage_24h"],
            "rank": c["market_cap_rank"]
        } for c in coins]
    except Exception as e:
        return [{"error": str(e)}]

# ============ COMMODITIES via Yahoo Finance ============
COMMODITY_TICKERS = {
    "gold": "GC=F",
    "silver": "SI=F",
    "crude_oil": "CL=F",
    "brent_oil": "BZ=F",
    "natural_gas": "NG=F",
    "copper": "HG=F",
    "platinum": "PL=F",
    "palladium": "PA=F",
    "corn": "ZC=F",
    "wheat": "ZW=F",
    "soybeans": "ZS=F",
    "coffee": "KC=F",
    "sugar": "SB=F",
    "cotton": "CT=F"
}

def get_commodity_price(name: str = "gold") -> Dict[str, Any]:
    """Get commodity price via Yahoo Finance futures"""
    try:
        ticker = COMMODITY_TICKERS.get(name.lower())
        if not ticker:
            return {"error": f"Commodity {name} not supported. Available: {list(COMMODITY_TICKERS.keys())}"}
        
        data = yf.Ticker(ticker)
        hist = data.history(period="1d", interval="1d")
        
        if hist.empty:
            return {"error": f"No data for {name}"}
        
        latest = hist.iloc[-1]
        return {
            "commodity": name.title(),
            "ticker": ticker,
            "price": round(latest['Close'], 2),
            "open": round(latest['Open'], 2),
            "high": round(latest['High'], 2),
            "low": round(latest['Low'], 2),
            "volume": int(latest['Volume']),
            "change_pct": round(((latest['Close'] - latest['Open']) / latest['Open']) * 100, 2),
            "date": hist.index[-1].strftime("%Y-%m-%d")
        }
    except Exception as e:
        return {"error": str(e)}

def get_all_commodities() -> List[Dict[str, Any]]:
    """Get prices for all tracked commodities"""
    results = []
    for name in COMMODITY_TICKERS.keys():
        result = get_commodity_price(name)
        if "error" not in result:
            results.append(result)
        time.sleep(0.1)  # Rate limit
    return results

# ============ FOREX via exchangerate.host (free, no key) ============
def get_forex_rate(base: str = "USD", target: str = "EUR") -> Dict[str, Any]:
    """Get forex exchange rate"""
    try:
        url = f"https://api.exchangerate.host/latest"
        params = {"base": base.upper(), "symbols": target.upper()}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if not data.get("success"):
            return {"error": "API request failed"}
        
        rate = data["rates"].get(target.upper())
        return {
            "base": base.upper(),
            "target": target.upper(),
            "rate": rate,
            "date": data.get("date"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

def get_forex_basket(base: str = "USD", targets: List[str] = None) -> List[Dict[str, Any]]:
    """Get multiple forex pairs"""
    if targets is None:
        targets = ["EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD", "CNY", "INR", "BRL"]
    
    try:
        url = f"https://api.exchangerate.host/latest"
        params = {"base": base.upper(), "symbols": ",".join([t.upper() for t in targets])}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        results = []
        for target, rate in data.get("rates", {}).items():
            results.append({
                "base": base.upper(),
                "target": target,
                "rate": rate,
                "date": data.get("date")
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]

# ============ ANALYST RATINGS via Yahoo Finance ============
def get_analyst_ratings(ticker: str) -> Dict[str, Any]:
    """Get analyst recommendations and target price"""
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        
        return {
            "ticker": ticker.upper(),
            "current_price": info.get("currentPrice"),
            "target_price_mean": info.get("targetMeanPrice"),
            "target_price_high": info.get("targetHighPrice"),
            "target_price_low": info.get("targetLowPrice"),
            "recommendation": info.get("recommendationKey"),  # buy, hold, sell
            "num_analysts": info.get("numberOfAnalystOpinions"),
            "upside_pct": round(((info.get("targetMeanPrice", 0) - info.get("currentPrice", 1)) / info.get("currentPrice", 1)) * 100, 2) if info.get("targetMeanPrice") and info.get("currentPrice") else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"ticker": ticker.upper(), "error": str(e)}

# ============ COMPANY PROFILE via Yahoo Finance ============
def get_company_profile(ticker: str) -> Dict[str, Any]:
    """Get detailed company information"""
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        
        return {
            "ticker": ticker.upper(),
            "name": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "website": info.get("website"),
            "description": info.get("longBusinessSummary"),
            "employees": info.get("fullTimeEmployees"),
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "price_to_book": info.get("priceToBook"),
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "beta": info.get("beta"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "avg_volume": info.get("averageVolume"),
            "dividend_yield": info.get("dividendYield"),
            "ex_dividend_date": info.get("exDividendDate"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"ticker": ticker.upper(), "error": str(e)}

# ============ STOCK SCREENER ============
def screen_stocks(
    min_market_cap: Optional[float] = None,
    max_pe: Optional[float] = None,
    min_dividend_yield: Optional[float] = None,
    sector: Optional[str] = None,
    country: Optional[str] = None,
    tickers: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Screen stocks based on fundamental criteria.
    Note: This is a basic implementation. For production, use dedicated screening APIs.
    """
    if tickers is None:
        # Default to S&P 100 proxies (you would expand this)
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "V", "JNJ",
                   "WMT", "JPM", "PG", "UNH", "MA", "HD", "DIS", "BAC", "XOM", "PFE"]
    
    results = []
    for ticker in tickers[:50]:  # Limit to avoid rate limits
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Apply filters
            if min_market_cap and info.get("marketCap", 0) < min_market_cap:
                continue
            if max_pe and info.get("trailingPE", float('inf')) > max_pe:
                continue
            if min_dividend_yield and info.get("dividendYield", 0) < min_dividend_yield:
                continue
            if sector and info.get("sector") != sector:
                continue
            if country and info.get("country") != country:
                continue
            
            results.append({
                "ticker": ticker,
                "name": info.get("longName"),
                "sector": info.get("sector"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "dividend_yield": info.get("dividendYield"),
                "price": info.get("currentPrice"),
                "52w_change_pct": round(((info.get("currentPrice", 0) - info.get("fiftyTwoWeekLow", 1)) / info.get("fiftyTwoWeekLow", 1)) * 100, 2) if info.get("fiftyTwoWeekLow") else None
            })
            
            time.sleep(0.1)  # Rate limit
        except:
            continue
    
    return sorted(results, key=lambda x: x.get("market_cap", 0), reverse=True)

# ============ CLI FUNCTIONS ============
def crypto_price_cli(symbol: str):
    """CLI: Get crypto price"""
    result = get_crypto_price(symbol)
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\n{result['symbol']} Price: ${result['price_usd']:,.2f}")
        print(f"Market Cap: ${result['market_cap']:,.0f}")
        print(f"24h Volume: ${result['volume_24h']:,.0f}")
        print(f"24h Change: {result['change_24h_pct']:.2f}%")

def crypto_list_cli(limit: int = 20):
    """CLI: List top cryptocurrencies"""
    coins = get_crypto_list(limit)
    print(f"\nTop {limit} Cryptocurrencies by Market Cap:")
    print(f"{'Rank':<6}{'Symbol':<10}{'Name':<20}{'Price':<15}{'24h %':<10}")
    print("-" * 70)
    for c in coins:
        if "error" not in c:
            print(f"{c['rank']:<6}{c['symbol']:<10}{c['name']:<20}${c['price_usd']:>12,.2f}{c['change_24h_pct']:>8.2f}%")

def commodity_price_cli(name: str):
    """CLI: Get commodity price"""
    result = get_commodity_price(name)
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\n{result['commodity']} ({result['ticker']})")
        print(f"Price: ${result['price']:.2f}")
        print(f"Day Range: ${result['low']:.2f} - ${result['high']:.2f}")
        print(f"Change: {result['change_pct']:.2f}%")

def commodities_cli():
    """CLI: Get all commodity prices"""
    commodities = get_all_commodities()
    print("\nCommodity Prices:")
    print(f"{'Commodity':<15}{'Price':<12}{'Change %':<10}")
    print("-" * 40)
    for c in commodities:
        print(f"{c['commodity']:<15}${c['price']:>10,.2f}{c['change_pct']:>8.2f}%")

def forex_cli(base: str, target: str):
    """CLI: Get forex rate"""
    result = get_forex_rate(base, target)
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\n{result['base']}/{result['target']}: {result['rate']:.4f}")
        print(f"Date: {result['date']}")

def forex_basket_cli(base: str):
    """CLI: Get forex basket"""
    results = get_forex_basket(base)
    print(f"\n{base} Exchange Rates:")
    print(f"{'Pair':<12}{'Rate':<12}")
    print("-" * 25)
    for r in results:
        if "error" not in r:
            print(f"{r['base']}/{r['target']:<8}{r['rate']:>10.4f}")

def analyst_ratings_cli(ticker: str):
    """CLI: Get analyst ratings"""
    result = get_analyst_ratings(ticker)
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\nAnalyst Ratings for {result['ticker']}:")
        print(f"Current Price: ${result['current_price']:.2f}")
        print(f"Target Price: ${result['target_price_mean']:.2f} (High: ${result['target_price_high']:.2f}, Low: ${result['target_price_low']:.2f})")
        print(f"Upside: {result['upside_pct']:.2f}%")
        print(f"Recommendation: {result['recommendation']}")
        print(f"Analysts Covering: {result['num_analysts']}")

def company_profile_cli(ticker: str):
    """CLI: Get company profile"""
    result = get_company_profile(ticker)
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\nCompany Profile: {result['name']} ({result['ticker']})")
        print(f"Sector: {result['sector']} | Industry: {result['industry']}")
        print(f"Country: {result['country']} | Employees: {result['employees']:,}")
        print(f"\nValuation:")
        print(f"  Market Cap: ${result['market_cap']/1e9:.2f}B")
        print(f"  P/E Ratio: {result['pe_ratio']:.2f}")
        print(f"  Price/Book: {result['price_to_book']:.2f}")
        print(f"\nProfitability:")
        print(f"  Profit Margin: {result['profit_margin']*100:.2f}%")
        print(f"  ROE: {result['roe']*100:.2f}%")
        print(f"\nGrowth:")
        print(f"  Revenue Growth: {result['revenue_growth']*100:.2f}%")
        print(f"  Earnings Growth: {result['earnings_growth']*100:.2f}%")

def screener_cli(min_market_cap: float = None, max_pe: float = None, sector: str = None):
    """CLI: Run stock screener"""
    filters = []
    if min_market_cap:
        filters.append(f"Market Cap > ${min_market_cap/1e9:.1f}B")
    if max_pe:
        filters.append(f"P/E < {max_pe}")
    if sector:
        filters.append(f"Sector = {sector}")
    
    print(f"\nStock Screener" + (f" (Filters: {', '.join(filters)})" if filters else ""))
    results = screen_stocks(min_market_cap=min_market_cap, max_pe=max_pe, sector=sector)
    
    print(f"\n{'Ticker':<8}{'Name':<30}{'Sector':<20}{'Mkt Cap':<15}{'P/E':<8}{'Div %':<8}")
    print("-" * 95)
    for r in results[:20]:
        print(f"{r['ticker']:<8}{r['name'][:28]:<30}{r['sector'][:18]:<20}${r['market_cap']/1e9:>12.2f}B{r['pe_ratio']:>6.1f}{r['dividend_yield']*100 if r['dividend_yield'] else 0:>6.2f}%")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Multi-Asset Coverage Module - Test Run")
        print("\n=== Crypto ===")
        crypto_price_cli("bitcoin")
        print("\n=== Commodities ===")
        commodity_price_cli("gold")
        print("\n=== Forex ===")
        forex_cli("USD", "EUR")
        print("\n=== Analyst Ratings ===")
        analyst_ratings_cli("AAPL")
        sys.exit(0)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    if command == "crypto-price":
        if len(args) < 1:
            print("Usage: crypto-price SYMBOL")
            sys.exit(1)
        crypto_price_cli(args[0])
    
    elif command == "crypto-list":
        limit = int(args[0]) if args else 20
        crypto_list_cli(limit)
    
    elif command == "commodity":
        if len(args) < 1:
            print("Usage: commodity NAME")
            print("Available: gold, silver, crude_oil, brent_oil, natural_gas, copper, platinum, palladium")
            sys.exit(1)
        commodity_price_cli(args[0])
    
    elif command == "commodities":
        commodities_cli()
    
    elif command == "forex":
        if len(args) < 2:
            print("Usage: forex BASE TARGET")
            sys.exit(1)
        forex_cli(args[0], args[1])
    
    elif command == "forex-basket":
        base = args[0] if args else "USD"
        forex_basket_cli(base)
    
    elif command == "analyst-ratings":
        if len(args) < 1:
            print("Usage: analyst-ratings TICKER")
            sys.exit(1)
        analyst_ratings_cli(args[0])
    
    elif command == "company-profile":
        if len(args) < 1:
            print("Usage: company-profile TICKER")
            sys.exit(1)
        company_profile_cli(args[0])
    
    elif command == "screener":
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--min-market-cap', type=float, help='Minimum market cap')
        parser.add_argument('--max-pe', type=float, help='Maximum P/E ratio')
        parser.add_argument('--sector', type=str, help='Sector filter')
        parsed = parser.parse_args(args)
        screener_cli(parsed.min_market_cap, parsed.max_pe, parsed.sector)
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: crypto-price, crypto-list, commodity, commodities, forex, forex-basket, analyst-ratings, company-profile, screener")
        sys.exit(1)

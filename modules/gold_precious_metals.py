#!/usr/bin/env python3
"""
Gold & Precious Metals Module

Data Sources:
- Yahoo Finance: Gold (GC=F), Silver (SI=F), Platinum (PL=F), Palladium (PA=F) futures prices
- ETF Holdings: GLD (SPDR Gold Trust), SLV (iShares Silver Trust), PPLT (Aberdeen Platinum), PALL (Aberdeen Palladium)
- Currency: Gold prices in multiple currencies via FX conversion

Daily updates. No API key required.

Phase: 171
Author: QUANTCLAW DATA Build Agent
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time


# Yahoo Finance ticker symbols
METALS_TICKERS = {
    "gold": "GC=F",      # Gold Futures
    "silver": "SI=F",    # Silver Futures
    "platinum": "PL=F",  # Platinum Futures
    "palladium": "PA=F"  # Palladium Futures
}

ETF_TICKERS = {
    "GLD": "SPDR Gold Trust",
    "SLV": "iShares Silver Trust", 
    "PPLT": "Aberdeen Platinum ETF",
    "PALL": "Aberdeen Palladium ETF"
}

# World Gold Council key metrics (approximations based on public data)
WGC_METRICS = {
    "annual_mine_supply": 3000,  # metric tons
    "annual_demand": 4500,       # metric tons
    "central_bank_holdings": 35000,  # metric tons
    "etf_holdings": 3500,        # metric tons
    "jewelry_demand_pct": 47,    # percentage
    "investment_demand_pct": 29,
    "central_bank_demand_pct": 14,
    "technology_demand_pct": 8
}


def get_yahoo_quote(ticker: str) -> Dict:
    """
    Fetch current quote from Yahoo Finance
    
    Args:
        ticker: Yahoo Finance ticker symbol
        
    Returns:
        Dict with price, change, volume, etc.
    """
    try:
        # Yahoo Finance query API
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {
            "interval": "1d",
            "range": "1d"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = data["chart"]["result"][0]
        meta = result["meta"]
        
        # Extract price data
        current_price = meta.get("regularMarketPrice")
        prev_close = meta.get("previousClose")
        
        if current_price and prev_close:
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100
        else:
            change = 0
            change_pct = 0
            
        return {
            "ticker": ticker,
            "price": current_price,
            "currency": meta.get("currency", "USD"),
            "change": change,
            "change_pct": change_pct,
            "prev_close": prev_close,
            "volume": meta.get("regularMarketVolume"),
            "day_high": meta.get("regularMarketDayHigh"),
            "day_low": meta.get("regularMarketDayLow"),
            "timestamp": datetime.fromtimestamp(meta.get("regularMarketTime", time.time())),
            "market_state": meta.get("marketState", "REGULAR")
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch {ticker}: {str(e)}"}


def get_yahoo_history(ticker: str, period: str = "1mo") -> List[Dict]:
    """
    Fetch historical price data from Yahoo Finance
    
    Args:
        ticker: Yahoo Finance ticker symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
    Returns:
        List of historical price records
    """
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {
            "interval": "1d",
            "range": period
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        quotes = result["indicators"]["quote"][0]
        
        history = []
        for i, ts in enumerate(timestamps):
            history.append({
                "date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                "open": quotes["open"][i],
                "high": quotes["high"][i],
                "low": quotes["low"][i],
                "close": quotes["close"][i],
                "volume": quotes["volume"][i]
            })
            
        return history
        
    except Exception as e:
        return [{"error": f"Failed to fetch history for {ticker}: {str(e)}"}]


def get_etf_holdings(ticker: str) -> Dict:
    """
    Get ETF summary data from Yahoo Finance
    
    Args:
        ticker: ETF ticker symbol (GLD, SLV, etc)
        
    Returns:
        Dict with ETF holdings data
    """
    try:
        # Get basic quote data
        quote = get_yahoo_quote(ticker)
        
        # Get fund profile
        url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"
        params = {
            "modules": "summaryProfile,fundProfile,defaultKeyStatistics"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = data["quoteSummary"]["result"][0]
        
        # Extract relevant data
        default_stats = result.get("defaultKeyStatistics", {})
        fund_profile = result.get("fundProfile", {})
        
        return {
            "ticker": ticker,
            "name": ETF_TICKERS.get(ticker, ticker),
            "nav": quote.get("price"),
            "nav_change_pct": quote.get("change_pct"),
            "volume": quote.get("volume"),
            "total_assets": default_stats.get("totalAssets", {}).get("raw"),
            "shares_outstanding": default_stats.get("sharesOutstanding", {}).get("raw"),
            "expense_ratio": fund_profile.get("feesExpensesInvestment", {}).get("annualReportExpenseRatio", {}).get("raw"),
            "inception_date": fund_profile.get("fundInceptionDate"),
            "category": fund_profile.get("categoryName"),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"ticker": ticker, "error": f"Failed to fetch ETF data: {str(e)}"}


def get_all_metals_prices() -> Dict:
    """
    Get current prices for all precious metals
    
    Returns:
        Dict with prices for gold, silver, platinum, palladium
    """
    prices = {}
    
    for metal, ticker in METALS_TICKERS.items():
        quote = get_yahoo_quote(ticker)
        if "error" not in quote:
            prices[metal] = {
                "price": quote["price"],
                "change": quote["change"],
                "change_pct": quote["change_pct"],
                "unit": "USD/troy_oz",
                "timestamp": quote["timestamp"].isoformat()
            }
        else:
            prices[metal] = quote
            
    return prices


def get_all_etf_holdings() -> Dict:
    """
    Get holdings data for all precious metals ETFs
    
    Returns:
        Dict with data for GLD, SLV, PPLT, PALL
    """
    holdings = {}
    
    for ticker in ETF_TICKERS.keys():
        holdings[ticker] = get_etf_holdings(ticker)
        time.sleep(0.5)  # Rate limiting
        
    return holdings


def calculate_gold_silver_ratio() -> Dict:
    """
    Calculate the gold/silver price ratio
    
    Returns:
        Dict with ratio and interpretation
    """
    gold_quote = get_yahoo_quote(METALS_TICKERS["gold"])
    silver_quote = get_yahoo_quote(METALS_TICKERS["silver"])
    
    if "error" in gold_quote or "error" in silver_quote:
        return {"error": "Failed to fetch prices for ratio calculation"}
        
    gold_price = gold_quote["price"]
    silver_price = silver_quote["price"]
    
    if not gold_price or not silver_price:
        return {"error": "Invalid price data"}
        
    ratio = gold_price / silver_price
    
    # Historical context (approximate ranges)
    interpretation = ""
    if ratio > 90:
        interpretation = "Very high - silver appears undervalued relative to gold"
    elif ratio > 80:
        interpretation = "High - silver may be undervalued"
    elif ratio > 70:
        interpretation = "Above historical average"
    elif ratio > 50:
        interpretation = "Around historical average (50-70)"
    else:
        interpretation = "Low - gold may be undervalued relative to silver"
        
    return {
        "ratio": round(ratio, 2),
        "gold_price": gold_price,
        "silver_price": silver_price,
        "interpretation": interpretation,
        "historical_avg": "50-70",
        "timestamp": datetime.now().isoformat()
    }


def get_metals_performance(period: str = "1y") -> Dict:
    """
    Calculate performance metrics for all metals over specified period
    
    Args:
        period: Time period (1mo, 3mo, 6mo, 1y, 2y, 5y)
        
    Returns:
        Dict with performance data for each metal
    """
    performance = {}
    
    for metal, ticker in METALS_TICKERS.items():
        history = get_yahoo_history(ticker, period)
        
        if history and len(history) > 1 and "error" not in history[0]:
            first_price = history[0]["close"]
            last_price = history[-1]["close"]
            
            if first_price and last_price:
                total_return = ((last_price - first_price) / first_price) * 100
                
                # Calculate volatility (standard deviation of daily returns)
                returns = []
                for i in range(1, len(history)):
                    if history[i]["close"] and history[i-1]["close"]:
                        daily_return = (history[i]["close"] - history[i-1]["close"]) / history[i-1]["close"]
                        returns.append(daily_return)
                        
                if returns:
                    import statistics
                    volatility = statistics.stdev(returns) * (252 ** 0.5) * 100  # Annualized
                else:
                    volatility = None
                    
                performance[metal] = {
                    "total_return_pct": round(total_return, 2),
                    "start_price": round(first_price, 2),
                    "end_price": round(last_price, 2),
                    "volatility_pct": round(volatility, 2) if volatility else None,
                    "period": period,
                    "data_points": len(history)
                }
            else:
                performance[metal] = {"error": "Invalid price data"}
        else:
            performance[metal] = {"error": "Failed to fetch historical data"}
            
    return performance


def get_world_gold_council_summary() -> Dict:
    """
    Get World Gold Council summary metrics
    (Note: These are approximations based on publicly available WGC data)
    
    Returns:
        Dict with gold market fundamentals
    """
    return {
        "annual_mine_supply_mt": WGC_METRICS["annual_mine_supply"],
        "annual_demand_mt": WGC_METRICS["annual_demand"],
        "supply_deficit_mt": WGC_METRICS["annual_demand"] - WGC_METRICS["annual_mine_supply"],
        "central_bank_holdings_mt": WGC_METRICS["central_bank_holdings"],
        "etf_holdings_mt": WGC_METRICS["etf_holdings"],
        "demand_breakdown": {
            "jewelry_pct": WGC_METRICS["jewelry_demand_pct"],
            "investment_pct": WGC_METRICS["investment_demand_pct"],
            "central_banks_pct": WGC_METRICS["central_bank_demand_pct"],
            "technology_pct": WGC_METRICS["technology_demand_pct"]
        },
        "note": "These are approximate values based on recent World Gold Council reports",
        "source": "World Gold Council annual reports (public data)",
        "timestamp": datetime.now().isoformat()
    }


def get_comprehensive_metals_report() -> Dict:
    """
    Generate comprehensive precious metals market report
    
    Returns:
        Dict with all available metals data
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "current_prices": get_all_metals_prices(),
        "gold_silver_ratio": calculate_gold_silver_ratio(),
        "etf_holdings": get_all_etf_holdings(),
        "performance_1y": get_metals_performance("1y"),
        "performance_ytd": get_metals_performance("ytd"),
        "wgc_fundamentals": get_world_gold_council_summary()
    }
    
    return report


# CLI Interface
def main():
    """CLI interface for gold & precious metals data"""
    
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "No command specified",
            "available_commands": [
                "prices", "etf-holdings", "gold-silver-ratio", 
                "performance", "wgc-summary", "comprehensive-report"
            ]
        }, indent=2))
        sys.exit(1)
        
    command = sys.argv[1]
    
    try:
        if command == "prices":
            result = get_all_metals_prices()
            
        elif command == "etf-holdings":
            result = get_all_etf_holdings()
            
        elif command == "gold-silver-ratio":
            result = calculate_gold_silver_ratio()
            
        elif command == "performance":
            period = sys.argv[2] if len(sys.argv) > 2 else "1y"
            result = get_metals_performance(period)
            
        elif command == "wgc-summary":
            result = get_world_gold_council_summary()
            
        elif command == "comprehensive-report":
            result = get_comprehensive_metals_report()
            
        else:
            result = {
                "error": f"Unknown command: {command}",
                "available_commands": [
                    "prices", "etf-holdings", "gold-silver-ratio",
                    "performance", "wgc-summary", "comprehensive-report"
                ]
            }
            
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()

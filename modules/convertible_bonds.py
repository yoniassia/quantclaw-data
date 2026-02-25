#!/usr/bin/env python3
"""
Convertible Bond Arbitrage (Phase 64)
======================================
Conversion premium analysis, implied volatility, delta hedging opportunities

Data Sources:
- FRED: Treasury yields, credit spreads
- Yahoo Finance: Stock prices, volatility
- SEC EDGAR: Convertible bond prospectuses

CLI Commands:
- python cli.py convertible-scan           # Scan for convertible bond opportunities
- python cli.py conversion-premium TSLA    # Conversion premium analysis
- python cli.py convertible-arb MSTR       # Arbitrage opportunity analysis
- python cli.py convertible-greeks COIN    # Delta/gamma for convertible positions
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics
import math

# API Configuration
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
YAHOO_FINANCE_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"
SEC_EDGAR_BASE = "https://www.sec.gov/cgi-bin/browse-edgar"

# Known convertible bond issuers (simplified database)
# In production, this would be fetched from a real-time database
CONVERTIBLE_ISSUERS = {
    "TSLA": {
        "bonds": [
            {"cusip": "88160RAH4", "maturity": "2024-03-01", "coupon": 1.25, "conversion_price": 359.87, "par": 1000},
            {"cusip": "88160RAK7", "maturity": "2024-08-15", "coupon": 2.00, "conversion_price": 309.83, "par": 1000}
        ]
    },
    "MSTR": {
        "bonds": [
            {"cusip": "55277VAA0", "maturity": "2027-06-15", "coupon": 0.00, "conversion_price": 397.99, "par": 1000},
            {"cusip": "55277VAB8", "maturity": "2028-02-15", "coupon": 0.625, "conversion_price": 143.25, "par": 1000}
        ]
    },
    "COIN": {
        "bonds": [
            {"cusip": "19260QAA7", "maturity": "2026-05-01", "coupon": 0.50, "conversion_price": 345.92, "par": 1000},
            {"cusip": "19260QAB5", "maturity": "2030-06-01", "coupon": 0.25, "conversion_price": 267.86, "par": 1000}
        ]
    },
    "SNAP": {
        "bonds": [
            {"cusip": "83304AAA9", "maturity": "2026-05-01", "coupon": 0.00, "conversion_price": 12.02, "par": 1000}
        ]
    },
    "UBER": {
        "bonds": [
            {"cusip": "90353TAA8", "maturity": "2025-12-15", "coupon": 0.00, "conversion_price": 55.36, "par": 1000}
        ]
    },
    "ROKU": {
        "bonds": [
            {"cusip": "77543RAA1", "maturity": "2026-12-01", "coupon": 0.00, "conversion_price": 114.26, "par": 1000}
        ]
    },
    "ZM": {
        "bonds": [
            {"cusip": "98980LAA0", "maturity": "2026-05-15", "coupon": 0.00, "conversion_price": 109.38, "par": 1000}
        ]
    }
}

def get_stock_data(ticker: str, period: str = "1mo") -> Dict[str, Any]:
    """Fetch stock price and volatility from Yahoo Finance"""
    try:
        url = f"{YAHOO_FINANCE_BASE}/{ticker}"
        params = {
            "range": period,
            "interval": "1d",
            "indicators": "quote",
            "includeTimestamps": "true"
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = data['chart']['result'][0]
        quote = result['indicators']['quote'][0]
        
        # Get current price
        close_prices = [p for p in quote['close'] if p is not None]
        current_price = close_prices[-1] if close_prices else 0
        
        # Calculate historical volatility (annualized)
        if len(close_prices) > 1:
            returns = [math.log(close_prices[i]/close_prices[i-1]) for i in range(1, len(close_prices))]
            volatility = statistics.stdev(returns) * math.sqrt(252)  # Annualize
        else:
            volatility = 0.3  # Default 30% volatility
        
        # Get volume data
        volumes = [v for v in quote['volume'] if v is not None]
        avg_volume = statistics.mean(volumes) if volumes else 0
        
        return {
            "ticker": ticker,
            "current_price": round(current_price, 2),
            "historical_volatility": round(volatility * 100, 2),  # As percentage
            "avg_volume": int(avg_volume),
            "data_points": len(close_prices)
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "current_price": 0,
            "historical_volatility": 30.0,
            "avg_volume": 0,
            "error": str(e)
        }

def get_treasury_yield() -> float:
    """Get current 10-year Treasury yield from FRED (no API key needed for public data)"""
    try:
        # Using public DGS10 series (10-Year Treasury Constant Maturity Rate)
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"
        response = requests.get(url, timeout=10)
        
        # Parse CSV
        lines = response.text.strip().split('\n')
        # Get the last valid data point
        for line in reversed(lines[1:]):  # Skip header
            parts = line.split(',')
            if len(parts) == 2 and parts[1] != '.' and parts[1]:
                return float(parts[1]) / 100  # Convert percentage to decimal
        
        return 0.045  # Default 4.5% if fetch fails
    except:
        return 0.045

def calculate_conversion_premium(stock_price: float, conversion_price: float, bond_price: float = 100.0, par: float = 1000) -> Dict[str, Any]:
    """
    Calculate conversion premium and parity
    
    Conversion Ratio = Par Value / Conversion Price
    Conversion Value = Stock Price × Conversion Ratio
    Conversion Premium = (Bond Price - Conversion Value) / Conversion Value × 100
    """
    conversion_ratio = par / conversion_price
    conversion_value = stock_price * conversion_ratio
    parity = conversion_value / par * 100  # As percentage of par
    
    # Bond price is typically quoted as percentage of par
    bond_value = par * (bond_price / 100)
    premium = ((bond_value - conversion_value) / conversion_value) * 100 if conversion_value > 0 else 0
    
    return {
        "conversion_ratio": round(conversion_ratio, 4),
        "conversion_value": round(conversion_value, 2),
        "parity": round(parity, 2),
        "conversion_premium_pct": round(premium, 2),
        "bond_value": round(bond_value, 2),
        "in_the_money": stock_price > conversion_price
    }

def calculate_implied_volatility(premium_pct: float, time_to_maturity_years: float, risk_free_rate: float) -> float:
    """
    Simplified implied volatility calculation from conversion premium
    
    Higher premium suggests higher implied volatility
    This is a simplified model; real convertible bond pricing uses more complex models
    """
    # Rough approximation: premium relates to option value
    # Higher premium = higher implied vol
    # Typical relationship: premium% ≈ 0.4 × σ × sqrt(T)
    
    if time_to_maturity_years <= 0:
        return 0
    
    # Solve for σ (implied volatility)
    implied_vol = (premium_pct / 40) / math.sqrt(time_to_maturity_years)
    
    # Clamp to reasonable range (10% to 150%)
    return max(10, min(150, implied_vol))

def calculate_greeks(stock_price: float, conversion_price: float, volatility: float, 
                    time_to_maturity: float, risk_free_rate: float) -> Dict[str, float]:
    """
    Calculate delta and gamma for convertible bond
    
    Simplified Black-Scholes approach treating conversion option as call option
    """
    if time_to_maturity <= 0:
        # At maturity
        delta = 1.0 if stock_price > conversion_price else 0.0
        gamma = 0.0
    else:
        # Black-Scholes d1 and d2
        sigma = volatility / 100  # Convert percentage to decimal
        sqrt_t = math.sqrt(time_to_maturity)
        
        d1 = (math.log(stock_price / conversion_price) + (risk_free_rate + 0.5 * sigma**2) * time_to_maturity) / (sigma * sqrt_t)
        d2 = d1 - sigma * sqrt_t
        
        # Delta: N(d1) where N is cumulative normal distribution
        # Approximation of N(d1)
        delta = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))
        
        # Gamma: n(d1) / (S × σ × sqrt(T))
        # where n is the standard normal PDF
        n_d1 = (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1**2)
        gamma = n_d1 / (stock_price * sigma * sqrt_t)
        
    return {
        "delta": round(delta, 4),
        "gamma": round(gamma, 6),
        "interpretation": {
            "delta": f"{delta*100:.1f}% equity sensitivity",
            "gamma": "Rate of delta change per $1 stock move"
        }
    }

def scan_convertible_opportunities() -> Dict[str, Any]:
    """
    Scan for convertible bond arbitrage opportunities
    
    Looks for:
    - High conversion premium (expensive)
    - Low conversion premium (cheap)
    - High implied volatility vs realized
    """
    results = []
    risk_free_rate = get_treasury_yield()
    
    print(f"📊 Scanning convertible bond opportunities...")
    print(f"Risk-free rate: {risk_free_rate*100:.2f}%\n")
    
    for ticker, data in CONVERTIBLE_ISSUERS.items():
        stock_data = get_stock_data(ticker)
        stock_price = stock_data["current_price"]
        realized_vol = stock_data["historical_volatility"]
        
        if stock_price == 0:
            continue
        
        for bond in data["bonds"]:
            # Calculate time to maturity
            maturity_date = datetime.strptime(bond["maturity"], "%Y-%m-%d")
            time_to_maturity = (maturity_date - datetime.now()).days / 365.25
            
            if time_to_maturity < 0:
                continue  # Skip expired bonds
            
            # Calculate conversion metrics
            conversion_metrics = calculate_conversion_premium(
                stock_price, 
                bond["conversion_price"],
                100.0,  # Assume trading at par
                bond["par"]
            )
            
            # Calculate implied volatility from premium
            implied_vol = calculate_implied_volatility(
                conversion_metrics["conversion_premium_pct"],
                time_to_maturity,
                risk_free_rate
            )
            
            # Determine opportunity
            vol_spread = implied_vol - realized_vol
            
            opportunity_type = "none"
            if vol_spread > 10:
                opportunity_type = "sell_vol"  # Implied > realized, sell convertible
            elif vol_spread < -10:
                opportunity_type = "buy_vol"  # Implied < realized, buy convertible
            elif conversion_metrics["conversion_premium_pct"] < 5 and conversion_metrics["in_the_money"]:
                opportunity_type = "cheap_itm"  # In the money with low premium
            
            results.append({
                "ticker": ticker,
                "coupon": bond["coupon"],
                "maturity": bond["maturity"],
                "stock_price": stock_price,
                "conversion_price": bond["conversion_price"],
                "premium_pct": conversion_metrics["conversion_premium_pct"],
                "in_the_money": conversion_metrics["in_the_money"],
                "realized_vol": realized_vol,
                "implied_vol": round(implied_vol, 2),
                "vol_spread": round(vol_spread, 2),
                "opportunity": opportunity_type,
                "time_to_maturity_years": round(time_to_maturity, 2)
            })
    
    # Sort by opportunity attractiveness (vol spread magnitude)
    results.sort(key=lambda x: abs(x["vol_spread"]), reverse=True)
    
    return {
        "scan_time": datetime.now().isoformat(),
        "risk_free_rate": round(risk_free_rate * 100, 2),
        "opportunities_found": len([r for r in results if r["opportunity"] != "none"]),
        "total_scanned": len(results),
        "results": results
    }

def analyze_conversion_premium(ticker: str) -> Dict[str, Any]:
    """
    Detailed conversion premium analysis for a specific ticker
    """
    ticker = ticker.upper()
    
    if ticker not in CONVERTIBLE_ISSUERS:
        return {
            "error": f"No convertible bond data available for {ticker}",
            "available_tickers": list(CONVERTIBLE_ISSUERS.keys())
        }
    
    stock_data = get_stock_data(ticker, period="3mo")
    stock_price = stock_data["current_price"]
    risk_free_rate = get_treasury_yield()
    
    bonds_analysis = []
    
    for bond in CONVERTIBLE_ISSUERS[ticker]["bonds"]:
        maturity_date = datetime.strptime(bond["maturity"], "%Y-%m-%d")
        time_to_maturity = (maturity_date - datetime.now()).days / 365.25
        
        if time_to_maturity < 0:
            continue
        
        conversion_metrics = calculate_conversion_premium(
            stock_price,
            bond["conversion_price"],
            100.0,  # Assume par
            bond["par"]
        )
        
        implied_vol = calculate_implied_volatility(
            conversion_metrics["conversion_premium_pct"],
            time_to_maturity,
            risk_free_rate
        )
        
        bonds_analysis.append({
            "cusip": bond.get("cusip", "N/A"),
            "maturity": bond["maturity"],
            "coupon": bond["coupon"],
            "conversion_price": bond["conversion_price"],
            "conversion_ratio": conversion_metrics["conversion_ratio"],
            "conversion_value": conversion_metrics["conversion_value"],
            "parity": conversion_metrics["parity"],
            "premium_pct": conversion_metrics["conversion_premium_pct"],
            "in_the_money": conversion_metrics["in_the_money"],
            "implied_volatility": round(implied_vol, 2),
            "time_to_maturity_years": round(time_to_maturity, 2)
        })
    
    return {
        "ticker": ticker,
        "stock_price": stock_price,
        "historical_volatility": stock_data["historical_volatility"],
        "risk_free_rate": round(risk_free_rate * 100, 2),
        "bonds": bonds_analysis,
        "analysis_time": datetime.now().isoformat()
    }

def analyze_arbitrage_opportunity(ticker: str) -> Dict[str, Any]:
    """
    Identify specific arbitrage opportunities for a ticker
    
    Strategies:
    1. Conversion arbitrage: Buy bond, short stock
    2. Volatility arbitrage: Implied vs realized vol
    3. Credit arbitrage: Convertible vs straight bond
    """
    ticker = ticker.upper()
    
    if ticker not in CONVERTIBLE_ISSUERS:
        return {
            "error": f"No convertible bond data available for {ticker}",
            "available_tickers": list(CONVERTIBLE_ISSUERS.keys())
        }
    
    stock_data = get_stock_data(ticker, period="3mo")
    stock_price = stock_data["current_price"]
    realized_vol = stock_data["historical_volatility"]
    risk_free_rate = get_treasury_yield()
    
    arbitrage_opportunities = []
    
    for bond in CONVERTIBLE_ISSUERS[ticker]["bonds"]:
        maturity_date = datetime.strptime(bond["maturity"], "%Y-%m-%d")
        time_to_maturity = (maturity_date - datetime.now()).days / 365.25
        
        if time_to_maturity < 0:
            continue
        
        conversion_metrics = calculate_conversion_premium(
            stock_price,
            bond["conversion_price"],
            100.0,
            bond["par"]
        )
        
        implied_vol = calculate_implied_volatility(
            conversion_metrics["conversion_premium_pct"],
            time_to_maturity,
            risk_free_rate
        )
        
        greeks = calculate_greeks(
            stock_price,
            bond["conversion_price"],
            realized_vol,
            time_to_maturity,
            risk_free_rate
        )
        
        # Identify arbitrage strategies
        strategies = []
        
        # 1. Conversion Arbitrage (if deeply ITM with low premium)
        if conversion_metrics["in_the_money"] and conversion_metrics["conversion_premium_pct"] < 5:
            profit_potential = conversion_metrics["conversion_value"] - 1000  # vs par
            strategies.append({
                "type": "conversion_arbitrage",
                "action": "Buy bond, short stock at conversion ratio",
                "potential_profit_per_bond": round(profit_potential, 2),
                "risk": "Stock price volatility, conversion restrictions",
                "delta_hedge_ratio": greeks["delta"]
            })
        
        # 2. Volatility Arbitrage
        vol_spread = implied_vol - realized_vol
        if abs(vol_spread) > 10:
            if vol_spread > 10:
                strategies.append({
                    "type": "volatility_arbitrage",
                    "action": "Sell convertible (implied vol rich), buy stock, delta hedge",
                    "vol_spread": round(vol_spread, 2),
                    "implied_vol": round(implied_vol, 2),
                    "realized_vol": realized_vol,
                    "potential": "Capture vol premium decay"
                })
            else:
                strategies.append({
                    "type": "volatility_arbitrage",
                    "action": "Buy convertible (implied vol cheap), short stock, delta hedge",
                    "vol_spread": round(vol_spread, 2),
                    "implied_vol": round(implied_vol, 2),
                    "realized_vol": realized_vol,
                    "potential": "Profit from realized > implied vol"
                })
        
        # 3. Gamma Trading (if high gamma)
        if greeks["gamma"] > 0.001:
            strategies.append({
                "type": "gamma_trading",
                "action": "Buy convertible, delta hedge, rebalance on moves",
                "gamma": greeks["gamma"],
                "delta": greeks["delta"],
                "potential": "Profit from rebalancing as stock moves"
            })
        
        arbitrage_opportunities.append({
            "maturity": bond["maturity"],
            "conversion_price": bond["conversion_price"],
            "strategies": strategies,
            "greeks": greeks,
            "conversion_metrics": conversion_metrics
        })
    
    return {
        "ticker": ticker,
        "stock_price": stock_price,
        "realized_volatility": realized_vol,
        "opportunities": arbitrage_opportunities,
        "total_strategies": sum(len(opp["strategies"]) for opp in arbitrage_opportunities),
        "analysis_time": datetime.now().isoformat()
    }

def calculate_convertible_greeks(ticker: str) -> Dict[str, Any]:
    """
    Calculate delta and gamma for all convertible bonds of a ticker
    
    Used for delta hedging and risk management
    """
    ticker = ticker.upper()
    
    if ticker not in CONVERTIBLE_ISSUERS:
        return {
            "error": f"No convertible bond data available for {ticker}",
            "available_tickers": list(CONVERTIBLE_ISSUERS.keys())
        }
    
    stock_data = get_stock_data(ticker, period="1mo")
    stock_price = stock_data["current_price"]
    realized_vol = stock_data["historical_volatility"]
    risk_free_rate = get_treasury_yield()
    
    greeks_analysis = []
    
    for bond in CONVERTIBLE_ISSUERS[ticker]["bonds"]:
        maturity_date = datetime.strptime(bond["maturity"], "%Y-%m-%d")
        time_to_maturity = (maturity_date - datetime.now()).days / 365.25
        
        if time_to_maturity < 0:
            continue
        
        greeks = calculate_greeks(
            stock_price,
            bond["conversion_price"],
            realized_vol,
            time_to_maturity,
            risk_free_rate
        )
        
        conversion_metrics = calculate_conversion_premium(
            stock_price,
            bond["conversion_price"],
            100.0,
            bond["par"]
        )
        
        # Calculate hedge ratios
        # For $1M notional of bonds
        notional = 1_000_000
        num_bonds = notional / bond["par"]
        shares_to_hedge = num_bonds * conversion_metrics["conversion_ratio"] * greeks["delta"]
        
        greeks_analysis.append({
            "maturity": bond["maturity"],
            "conversion_price": bond["conversion_price"],
            "stock_price": stock_price,
            "delta": greeks["delta"],
            "gamma": greeks["gamma"],
            "in_the_money": conversion_metrics["in_the_money"],
            "hedge_example": {
                "bond_notional": notional,
                "shares_to_short": int(shares_to_hedge),
                "hedge_cost": round(shares_to_hedge * stock_price, 2),
                "rebalance_frequency": "Daily if gamma > 0.01, else weekly"
            },
            "sensitivity": {
                "delta_interpretation": greeks["interpretation"]["delta"],
                "price_move_$1": round(greeks["delta"] * conversion_metrics["conversion_ratio"], 2),
                "gamma_impact": f"Delta changes by {greeks['gamma']:.4f} per $1 stock move"
            }
        })
    
    return {
        "ticker": ticker,
        "stock_price": stock_price,
        "realized_volatility": realized_vol,
        "risk_free_rate": round(risk_free_rate * 100, 2),
        "greeks": greeks_analysis,
        "portfolio_delta": round(sum(g["delta"] for g in greeks_analysis) / len(greeks_analysis), 4) if greeks_analysis else 0,
        "analysis_time": datetime.now().isoformat()
    }

def print_scan_results(data: Dict[str, Any]):
    """Pretty print scan results"""
    print(f"\n🔍 CONVERTIBLE BOND OPPORTUNITY SCAN")
    print(f"{'='*70}")
    print(f"Scan Time: {data['scan_time']}")
    print(f"Risk-Free Rate: {data['risk_free_rate']}%")
    print(f"Opportunities Found: {data['opportunities_found']} / {data['total_scanned']}\n")
    
    # Group by opportunity type
    buy_vol = [r for r in data['results'] if r['opportunity'] == 'buy_vol']
    sell_vol = [r for r in data['results'] if r['opportunity'] == 'sell_vol']
    cheap_itm = [r for r in data['results'] if r['opportunity'] == 'cheap_itm']
    
    if buy_vol:
        print(f"\n📈 BUY VOLATILITY (Implied < Realized):")
        for r in buy_vol:
            print(f"  {r['ticker']} {r['maturity'][:10]} | Premium: {r['premium_pct']:+.1f}% | Vol Spread: {r['vol_spread']:+.1f}%")
            print(f"    Stock: ${r['stock_price']:.2f} | Conv: ${r['conversion_price']:.2f} | Realized: {r['realized_vol']:.1f}% | Implied: {r['implied_vol']:.1f}%")
    
    if sell_vol:
        print(f"\n📉 SELL VOLATILITY (Implied > Realized):")
        for r in sell_vol:
            print(f"  {r['ticker']} {r['maturity'][:10]} | Premium: {r['premium_pct']:+.1f}% | Vol Spread: {r['vol_spread']:+.1f}%")
            print(f"    Stock: ${r['stock_price']:.2f} | Conv: ${r['conversion_price']:.2f} | Realized: {r['realized_vol']:.1f}% | Implied: {r['implied_vol']:.1f}%")
    
    if cheap_itm:
        print(f"\n💰 CHEAP IN-THE-MONEY:")
        for r in cheap_itm:
            print(f"  {r['ticker']} {r['maturity'][:10]} | Premium: {r['premium_pct']:+.1f}%")
            print(f"    Stock: ${r['stock_price']:.2f} | Conv: ${r['conversion_price']:.2f}")

def print_premium_analysis(data: Dict[str, Any]):
    """Pretty print conversion premium analysis"""
    print(f"\n📊 CONVERSION PREMIUM ANALYSIS: {data['ticker']}")
    print(f"{'='*70}")
    print(f"Stock Price: ${data['stock_price']:.2f}")
    print(f"Historical Volatility: {data['historical_volatility']:.1f}%")
    print(f"Risk-Free Rate: {data['risk_free_rate']:.2f}%\n")
    
    for bond in data['bonds']:
        itm_status = "✅ IN THE MONEY" if bond['in_the_money'] else "❌ OUT OF THE MONEY"
        print(f"  Maturity: {bond['maturity'][:10]} | Coupon: {bond['coupon']:.2f}%")
        print(f"  Conversion Price: ${bond['conversion_price']:.2f} | {itm_status}")
        print(f"  Conversion Ratio: {bond['conversion_ratio']:.4f} shares per bond")
        print(f"  Conversion Value: ${bond['conversion_value']:.2f}")
        print(f"  Parity: {bond['parity']:.2f}%")
        print(f"  Conversion Premium: {bond['premium_pct']:+.2f}%")
        print(f"  Implied Volatility: {bond['implied_volatility']:.1f}%")
        print(f"  Time to Maturity: {bond['time_to_maturity_years']:.2f} years")
        print()

def print_arbitrage_analysis(data: Dict[str, Any]):
    """Pretty print arbitrage opportunity analysis"""
    print(f"\n⚡ ARBITRAGE OPPORTUNITIES: {data['ticker']}")
    print(f"{'='*70}")
    print(f"Stock Price: ${data['stock_price']:.2f}")
    print(f"Realized Volatility: {data['realized_volatility']:.1f}%")
    print(f"Total Strategies: {data['total_strategies']}\n")
    
    for opp in data['opportunities']:
        print(f"  Bond Maturity: {opp['maturity'][:10]} | Conversion: ${opp['conversion_price']:.2f}")
        print(f"  Delta: {opp['greeks']['delta']:.4f} | Gamma: {opp['greeks']['gamma']:.6f}")
        
        if opp['strategies']:
            print(f"  Strategies:")
            for strat in opp['strategies']:
                print(f"    🎯 {strat['type'].upper().replace('_', ' ')}")
                print(f"       {strat['action']}")
                if 'vol_spread' in strat:
                    print(f"       Vol Spread: {strat['vol_spread']:+.1f}% (Implied: {strat['implied_vol']:.1f}% vs Realized: {strat['realized_vol']:.1f}%)")
                if 'potential_profit_per_bond' in strat:
                    print(f"       Potential Profit: ${strat['potential_profit_per_bond']:.2f} per bond")
        else:
            print(f"  No attractive strategies at current levels")
        print()

def print_greeks_analysis(data: Dict[str, Any]):
    """Pretty print greeks analysis"""
    print(f"\n🎲 CONVERTIBLE GREEKS: {data['ticker']}")
    print(f"{'='*70}")
    print(f"Stock Price: ${data['stock_price']:.2f}")
    print(f"Realized Volatility: {data['realized_volatility']:.1f}%")
    print(f"Portfolio Delta: {data['portfolio_delta']:.4f}\n")
    
    for g in data['greeks']:
        itm_status = "✅ ITM" if g['in_the_money'] else "❌ OTM"
        print(f"  Maturity: {g['maturity'][:10]} | Conversion: ${g['conversion_price']:.2f} | {itm_status}")
        print(f"  Delta: {g['delta']:.4f} ({g['sensitivity']['delta_interpretation']})")
        print(f"  Gamma: {g['gamma']:.6f} ({g['sensitivity']['gamma_impact']})")
        print(f"  Price Sensitivity: ${g['sensitivity']['price_move_$1']:.2f} per $1 stock move")
        print(f"\n  Hedge Example ($1M notional):")
        print(f"    Short {g['hedge_example']['shares_to_short']:,} shares")
        print(f"    Hedge Cost: ${g['hedge_example']['hedge_cost']:,.2f}")
        print(f"    Rebalance: {g['hedge_example']['rebalance_frequency']}")
        print()

def main():
    if len(sys.argv) < 2:
        print("Usage: python convertible_bonds.py <command> [args]")
        print("\nCommands:")
        print("  convertible-scan                    # Scan for opportunities")
        print("  conversion-premium TICKER           # Premium analysis")
        print("  convertible-arb TICKER              # Arbitrage opportunities")
        print("  convertible-greeks TICKER           # Delta/gamma analysis")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "convertible-scan":
            result = scan_convertible_opportunities()
            print_scan_results(result)
            
        elif command == "conversion-premium":
            if len(sys.argv) < 3:
                print("Error: Please provide a ticker symbol")
                print("Example: python cli.py conversion-premium TSLA")
                sys.exit(1)
            ticker = sys.argv[2]
            result = analyze_conversion_premium(ticker)
            if "error" in result:
                print(f"Error: {result['error']}")
                print(f"Available tickers: {', '.join(result['available_tickers'])}")
            else:
                print_premium_analysis(result)
            
        elif command == "convertible-arb":
            if len(sys.argv) < 3:
                print("Error: Please provide a ticker symbol")
                print("Example: python cli.py convertible-arb MSTR")
                sys.exit(1)
            ticker = sys.argv[2]
            result = analyze_arbitrage_opportunity(ticker)
            if "error" in result:
                print(f"Error: {result['error']}")
                print(f"Available tickers: {', '.join(result['available_tickers'])}")
            else:
                print_arbitrage_analysis(result)
            
        elif command == "convertible-greeks":
            if len(sys.argv) < 3:
                print("Error: Please provide a ticker symbol")
                print("Example: python cli.py convertible-greeks COIN")
                sys.exit(1)
            ticker = sys.argv[2]
            result = calculate_convertible_greeks(ticker)
            if "error" in result:
                print(f"Error: {result['error']}")
                print(f"Available tickers: {', '.join(result['available_tickers'])}")
            else:
                print_greeks_analysis(result)
        
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

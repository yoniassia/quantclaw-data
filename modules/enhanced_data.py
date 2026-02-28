"""
Enhanced Market Data — Options Greeks, Earnings Calendar, Dividends, ETF Holdings
Phase 2: Combines options chains, earnings events, dividend data, and ETF composition.
Free sources: Yahoo Finance, CBOE, SEC N-PORT filings
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from scipy.stats import norm
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class OptionsGreeks:
    """Black-Scholes options pricing and Greeks calculation"""
    
    @staticmethod
    def d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d1 for Black-Scholes"""
        if T <= 0 or sigma <= 0:
            return 0.0
        return (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    
    @staticmethod
    def d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d2 for Black-Scholes"""
        if T <= 0 or sigma <= 0:
            return 0.0
        return OptionsGreeks.d1(S, K, T, r, sigma) - sigma * np.sqrt(T)
    
    @staticmethod
    def call_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Black-Scholes call option price"""
        if T <= 0:
            return max(S - K, 0)
        d1 = OptionsGreeks.d1(S, K, T, r, sigma)
        d2 = OptionsGreeks.d2(S, K, T, r, sigma)
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    
    @staticmethod
    def put_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Black-Scholes put option price"""
        if T <= 0:
            return max(K - S, 0)
        d1 = OptionsGreeks.d1(S, K, T, r, sigma)
        d2 = OptionsGreeks.d2(S, K, T, r, sigma)
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    @staticmethod
    def delta_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Call option delta"""
        if T <= 0:
            return 1.0 if S > K else 0.0
        d1 = OptionsGreeks.d1(S, K, T, r, sigma)
        return norm.cdf(d1)
    
    @staticmethod
    def delta_put(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Put option delta"""
        if T <= 0:
            return -1.0 if S < K else 0.0
        d1 = OptionsGreeks.d1(S, K, T, r, sigma)
        return norm.cdf(d1) - 1
    
    @staticmethod
    def gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Option gamma (same for calls and puts)"""
        if T <= 0 or sigma <= 0:
            return 0.0
        d1 = OptionsGreeks.d1(S, K, T, r, sigma)
        return norm.pdf(d1) / (S * sigma * np.sqrt(T))
    
    @staticmethod
    def vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Option vega (same for calls and puts)"""
        if T <= 0:
            return 0.0
        d1 = OptionsGreeks.d1(S, K, T, r, sigma)
        return S * norm.pdf(d1) * np.sqrt(T) / 100  # Per 1% change in IV
    
    @staticmethod
    def theta_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Call option theta (time decay)"""
        if T <= 0:
            return 0.0
        d1 = OptionsGreeks.d1(S, K, T, r, sigma)
        d2 = OptionsGreeks.d2(S, K, T, r, sigma)
        theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                 - r * K * np.exp(-r * T) * norm.cdf(d2))
        return theta / 365  # Per day
    
    @staticmethod
    def theta_put(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Put option theta (time decay)"""
        if T <= 0:
            return 0.0
        d1 = OptionsGreeks.d1(S, K, T, r, sigma)
        d2 = OptionsGreeks.d2(S, K, T, r, sigma)
        theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                 + r * K * np.exp(-r * T) * norm.cdf(-d2))
        return theta / 365  # Per day
    
    @staticmethod
    def rho_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Call option rho (interest rate sensitivity)"""
        if T <= 0:
            return 0.0
        d2 = OptionsGreeks.d2(S, K, T, r, sigma)
        return K * T * np.exp(-r * T) * norm.cdf(d2) / 100  # Per 1% change
    
    @staticmethod
    def rho_put(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Put option rho (interest rate sensitivity)"""
        if T <= 0:
            return 0.0
        d2 = OptionsGreeks.d2(S, K, T, r, sigma)
        return -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100  # Per 1% change


def get_options_chain(ticker: str, risk_free_rate: float = 0.05) -> Dict[str, Any]:
    """
    Fetch options chain with calculated Greeks using Black-Scholes
    
    Args:
        ticker: Stock symbol
        risk_free_rate: Annual risk-free rate for Greeks calculation
        
    Returns:
        Dict with calls, puts, and greeks
    """
    try:
        stock = yf.Ticker(ticker)
        current_price = stock.history(period="1d")['Close'].iloc[-1]
        
        # Get all expiration dates
        expirations = stock.options
        if not expirations:
            return {"error": "No options available"}
        
        all_calls = []
        all_puts = []
        
        for exp_date in expirations[:6]:  # First 6 expirations
            # Calculate time to expiration in years
            exp_dt = datetime.strptime(exp_date, '%Y-%m-%d')
            days_to_exp = (exp_dt - datetime.now()).days
            T = max(days_to_exp / 365.0, 0.001)  # Avoid zero
            
            # Get chain
            opt_chain = stock.option_chain(exp_date)
            
            # Process calls
            calls = opt_chain.calls.copy()
            calls['expiration'] = exp_date
            calls['daysToExp'] = days_to_exp
            calls['T'] = T
            
            # Calculate Greeks for each strike
            for idx, row in calls.iterrows():
                strike = row['strike']
                iv = row.get('impliedVolatility', 0.3)  # Default 30% if missing
                
                calls.at[idx, 'delta'] = OptionsGreeks.delta_call(current_price, strike, T, risk_free_rate, iv)
                calls.at[idx, 'gamma'] = OptionsGreeks.gamma(current_price, strike, T, risk_free_rate, iv)
                calls.at[idx, 'vega'] = OptionsGreeks.vega(current_price, strike, T, risk_free_rate, iv)
                calls.at[idx, 'theta'] = OptionsGreeks.theta_call(current_price, strike, T, risk_free_rate, iv)
                calls.at[idx, 'rho'] = OptionsGreeks.rho_call(current_price, strike, T, risk_free_rate, iv)
            
            all_calls.append(calls)
            
            # Process puts
            puts = opt_chain.puts.copy()
            puts['expiration'] = exp_date
            puts['daysToExp'] = days_to_exp
            puts['T'] = T
            
            for idx, row in puts.iterrows():
                strike = row['strike']
                iv = row.get('impliedVolatility', 0.3)
                
                puts.at[idx, 'delta'] = OptionsGreeks.delta_put(current_price, strike, T, risk_free_rate, iv)
                puts.at[idx, 'gamma'] = OptionsGreeks.gamma(current_price, strike, T, risk_free_rate, iv)
                puts.at[idx, 'vega'] = OptionsGreeks.vega(current_price, strike, T, risk_free_rate, iv)
                puts.at[idx, 'theta'] = OptionsGreeks.theta_put(current_price, strike, T, risk_free_rate, iv)
                puts.at[idx, 'rho'] = OptionsGreeks.rho_put(current_price, strike, T, risk_free_rate, iv)
            
            all_puts.append(puts)
        
        calls_df = pd.concat(all_calls, ignore_index=True) if all_calls else pd.DataFrame()
        puts_df = pd.concat(all_puts, ignore_index=True) if all_puts else pd.DataFrame()
        
        return {
            "ticker": ticker,
            "currentPrice": float(current_price),
            "expirations": list(expirations),
            "calls": calls_df.to_dict('records') if not calls_df.empty else [],
            "puts": puts_df.to_dict('records') if not puts_df.empty else [],
            "callsCount": len(calls_df),
            "putsCount": len(puts_df),
        }
        
    except Exception as e:
        logger.error(f"Options chain error for {ticker}: {e}")
        return {"error": str(e)}


def get_earnings_calendar(ticker: Optional[str] = None, days_ahead: int = 30) -> List[Dict[str, Any]]:
    """
    Get upcoming earnings dates from Yahoo Finance
    
    Args:
        ticker: Optional specific ticker, otherwise gets market-wide calendar
        days_ahead: Days to look ahead
        
    Returns:
        List of earnings events
    """
    try:
        if ticker:
            # Single ticker earnings date
            stock = yf.Ticker(ticker)
            info = stock.info
            earnings_date = info.get('earningsDate')
            
            if earnings_date:
                # Yahoo returns list of possible dates
                if isinstance(earnings_date, list):
                    earnings_date = earnings_date[0] if earnings_date else None
                
                if earnings_date:
                    return [{
                        "ticker": ticker,
                        "company": info.get('longName', ticker),
                        "earningsDate": earnings_date.strftime('%Y-%m-%d') if hasattr(earnings_date, 'strftime') else str(earnings_date),
                        "estimate": info.get('earningsQuarterlyGrowth'),
                    }]
            return []
        
        else:
            # Market-wide calendar (limited free data)
            # Use popular tickers as proxy
            popular_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 
                             'TSLA', 'NVDA', 'JPM', 'V', 'WMT']
            
            calendar = []
            end_date = datetime.now() + timedelta(days=days_ahead)
            
            for ticker_sym in popular_tickers:
                try:
                    stock = yf.Ticker(ticker_sym)
                    info = stock.info
                    earnings_date = info.get('earningsDate')
                    
                    if earnings_date:
                        if isinstance(earnings_date, list):
                            earnings_date = earnings_date[0]
                        
                        if isinstance(earnings_date, datetime) and earnings_date <= end_date:
                            calendar.append({
                                "ticker": ticker_sym,
                                "company": info.get('longName', ticker_sym),
                                "earningsDate": earnings_date.strftime('%Y-%m-%d'),
                                "marketCap": info.get('marketCap'),
                            })
                except:
                    continue
            
            return sorted(calendar, key=lambda x: x.get('earningsDate', ''))
    
    except Exception as e:
        logger.error(f"Earnings calendar error: {e}")
        return []


def get_dividend_data(ticker: str) -> Dict[str, Any]:
    """
    Get historical dividends and forward dividend yield
    
    Args:
        ticker: Stock symbol
        
    Returns:
        Dividend history and metrics
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get dividend history
        dividends = stock.dividends
        
        if dividends.empty:
            return {
                "ticker": ticker,
                "hasDividends": False,
                "message": "No dividend history"
            }
        
        # Calculate metrics
        latest_div = dividends.iloc[-1]
        div_history = dividends.tail(20).to_dict()
        
        # Annualized forward yield
        forward_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
        
        # Calculate growth rate (last 5 years)
        if len(dividends) >= 5:
            idx_5y = -20 if len(dividends) >= 20 else 0
            div_5y_ago = dividends.iloc[idx_5y]
            date_5y_ago = dividends.index[idx_5y]
            years = (dividends.index[-1] - date_5y_ago).days / 365.25
            if years > 0 and div_5y_ago > 0:
                cagr = ((latest_div / div_5y_ago) ** (1 / years) - 1) * 100
            else:
                cagr = None
        else:
            cagr = None
        
        return {
            "ticker": ticker,
            "hasDividends": True,
            "latestDividend": float(latest_div),
            "latestDate": str(dividends.index[-1].date()),
            "forwardYield": float(forward_yield),
            "payoutRatio": info.get('payoutRatio'),
            "dividendCAGR": float(cagr) if cagr else None,
            "exDividendDate": info.get('exDividendDate'),
            "dividendHistory": {str(k.date()): float(v) for k, v in div_history.items()},
            "totalPayments": len(dividends),
        }
        
    except Exception as e:
        logger.error(f"Dividend data error for {ticker}: {e}")
        return {"error": str(e)}


def get_etf_holdings(ticker: str, top_n: int = 50) -> Dict[str, Any]:
    """
    Get ETF holdings from Yahoo Finance
    
    Args:
        ticker: ETF symbol
        top_n: Number of top holdings to return
        
    Returns:
        ETF holdings and composition
    """
    try:
        etf = yf.Ticker(ticker)
        info = etf.info
        
        # Check if it's actually an ETF
        if info.get('quoteType') != 'ETF':
            return {
                "ticker": ticker,
                "isETF": False,
                "message": f"{ticker} is not an ETF"
            }
        
        # Get holdings (yfinance limitation: holdings data sparse)
        # For full holdings, would need SEC N-PORT filings scraping
        holdings = {}
        
        # Get sector weighting if available
        sector_weights = info.get('sectorWeightings', {})
        
        # Get top holdings if available
        try:
            # This is limited in yfinance free tier
            holdings_df = etf.get_holdings()
            if holdings_df is not None and not holdings_df.empty:
                holdings = holdings_df.head(top_n).to_dict('records')
        except:
            holdings = []
        
        return {
            "ticker": ticker,
            "isETF": True,
            "name": info.get('longName'),
            "totalAssets": info.get('totalAssets'),
            "ytdReturn": info.get('ytdReturn'),
            "expenseRatio": info.get('annualReportExpenseRatio'),
            "category": info.get('category'),
            "sectorWeightings": sector_weights,
            "topHoldings": holdings,
            "holdingsCount": len(holdings),
        }
        
    except Exception as e:
        logger.error(f"ETF holdings error for {ticker}: {e}")
        return {"error": str(e)}


# CLI integration
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "Usage: python enhanced_data.py <command> <ticker> [options]",
            "commands": {
                "options": "Get options chain with Greeks",
                "earnings": "Get earnings calendar",
                "dividends": "Get dividend history",
                "etf-holdings": "Get ETF composition"
            }
        }))
        sys.exit(1)
    
    command = sys.argv[1].lower()
    ticker = sys.argv[2].upper() if len(sys.argv) > 2 else None
    
    if command in ("options", "options-greeks"):
        if not ticker:
            result = {"error": "Ticker required"}
        else:
            result = get_options_chain(ticker)
    elif command in ("earnings", "earnings-calendar"):
        if ticker and ticker != "ALL":
            result = get_earnings_calendar(ticker)
        else:
            result = get_earnings_calendar()
    elif command == "dividends":
        if not ticker:
            result = {"error": "Ticker required"}
        else:
            result = get_dividend_data(ticker)
    elif command == "etf-holdings":
        if not ticker:
            result = {"error": "Ticker required"}
        else:
            result = get_etf_holdings(ticker)
    else:
        result = {"error": f"Unknown command: {command}"}
    
    print(json.dumps(result, indent=2, default=str))

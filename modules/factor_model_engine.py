#!/usr/bin/env python3
"""
Factor Model Engine — Momentum, value, quality, size, volatility factor scoring

Implements classic Fama-French style factors plus quality and volatility:
- Momentum: 12-month price momentum (excluding most recent month)
- Value: P/B, P/E, P/S, EV/EBITDA ratios
- Quality: ROE, ROA, profit margins, debt/equity
- Size: Market cap ranking
- Volatility: Historical volatility, beta

Data sources: Yahoo Finance (yfinance)
No API key required.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


def calculate_momentum(ticker: str, period_months: int = 12, exclude_recent: int = 1) -> Optional[float]:
    """
    Calculate price momentum (total return) over specified period.
    
    Args:
        ticker: Stock ticker symbol
        period_months: Lookback period in months (default 12)
        exclude_recent: Months to exclude from end (default 1 to avoid reversal)
    
    Returns:
        Momentum score (percentage return) or None if data unavailable
    """
    try:
        stock = yf.Ticker(ticker)
        end_date = datetime.now() - timedelta(days=exclude_recent * 30)
        start_date = end_date - timedelta(days=period_months * 30)
        
        hist = stock.history(start=start_date, end=end_date)
        if len(hist) < 2:
            return None
        
        momentum = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
        return round(momentum, 2)
    except Exception as e:
        print(f"⚠️  Momentum calculation failed for {ticker}: {e}")
        return None


def calculate_value_factors(ticker: str) -> Dict[str, Optional[float]]:
    """
    Calculate value factor metrics from fundamentals.
    
    Returns:
        Dict with P/E, P/B, P/S, EV/EBITDA, Dividend Yield
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            'PE': info.get('trailingPE'),
            'PB': info.get('priceToBook'),
            'PS': info.get('priceToSalesTrailing12Months'),
            'EV_EBITDA': info.get('enterpriseToEbitda'),
            'DivYield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else None
        }
    except Exception as e:
        print(f"⚠️  Value factors failed for {ticker}: {e}")
        return {'PE': None, 'PB': None, 'PS': None, 'EV_EBITDA': None, 'DivYield': None}


def calculate_quality_factors(ticker: str) -> Dict[str, Optional[float]]:
    """
    Calculate quality metrics from financials.
    
    Returns:
        Dict with ROE, ROA, Profit Margin, Debt/Equity, Current Ratio
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            'ROE': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else None,
            'ROA': info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else None,
            'ProfitMargin': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else None,
            'DebtToEquity': info.get('debtToEquity'),
            'CurrentRatio': info.get('currentRatio')
        }
    except Exception as e:
        print(f"⚠️  Quality factors failed for {ticker}: {e}")
        return {'ROE': None, 'ROA': None, 'ProfitMargin': None, 'DebtToEquity': None, 'CurrentRatio': None}


def calculate_size_factor(ticker: str) -> Optional[float]:
    """
    Calculate size factor (market cap in billions).
    
    Returns:
        Market cap in billions USD
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get('marketCap')
        
        if market_cap:
            return round(market_cap / 1e9, 2)
        return None
    except Exception as e:
        print(f"⚠️  Size calculation failed for {ticker}: {e}")
        return None


def calculate_volatility_factors(ticker: str, period_days: int = 252) -> Dict[str, Optional[float]]:
    """
    Calculate volatility and risk metrics.
    
    Args:
        ticker: Stock ticker
        period_days: Lookback period (default 252 = 1 year)
    
    Returns:
        Dict with historical volatility (annualized %), beta
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get historical prices
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days + 30)
        hist = stock.history(start=start_date, end=end_date)
        
        if len(hist) < 20:
            return {'Volatility': None, 'Beta': None}
        
        # Calculate daily returns
        returns = hist['Close'].pct_change().dropna()
        
        # Annualized volatility
        volatility = returns.std() * np.sqrt(252) * 100
        
        # Beta (vs SPY)
        try:
            spy = yf.download('^GSPC', start=start_date, end=end_date, progress=False)
            if len(spy) > 20:
                spy_returns = spy['Close'].pct_change().dropna()
                # Align dates
                combined = pd.concat([returns, spy_returns], axis=1, join='inner')
                combined.columns = ['stock', 'spy']
                
                if len(combined) > 20:
                    covariance = combined['stock'].cov(combined['spy'])
                    market_var = combined['spy'].var()
                    beta = covariance / market_var if market_var > 0 else None
                else:
                    beta = None
            else:
                beta = None
        except:
            beta = None
        
        return {
            'Volatility': round(volatility, 2) if not np.isnan(volatility) else None,
            'Beta': round(beta, 2) if beta and not np.isnan(beta) else None
        }
    except Exception as e:
        print(f"⚠️  Volatility calculation failed for {ticker}: {e}")
        return {'Volatility': None, 'Beta': None}


def get_factor_scores(ticker: str, verbose: bool = True) -> Dict:
    """
    Calculate all factor scores for a given ticker.
    
    Args:
        ticker: Stock ticker symbol
        verbose: Print progress messages
    
    Returns:
        Dict with all factor scores
    """
    if verbose:
        print(f"\n🔍 Analyzing factor scores for {ticker.upper()}...")
    
    scores = {
        'ticker': ticker.upper(),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Momentum
    if verbose:
        print("  📈 Calculating momentum...")
    scores['momentum_12m'] = calculate_momentum(ticker, 12, 1)
    
    # Value
    if verbose:
        print("  💰 Calculating value factors...")
    value = calculate_value_factors(ticker)
    scores.update(value)
    
    # Quality
    if verbose:
        print("  ⭐ Calculating quality factors...")
    quality = calculate_quality_factors(ticker)
    scores.update(quality)
    
    # Size
    if verbose:
        print("  📏 Calculating size factor...")
    scores['MarketCap'] = calculate_size_factor(ticker)
    
    # Volatility
    if verbose:
        print("  📊 Calculating volatility factors...")
    volatility = calculate_volatility_factors(ticker)
    scores.update(volatility)
    
    if verbose:
        print("  ✅ Factor analysis complete!\n")
    
    return scores


def compare_factors(tickers: List[str], sort_by: str = 'momentum_12m') -> pd.DataFrame:
    """
    Calculate and compare factor scores across multiple stocks.
    
    Args:
        tickers: List of ticker symbols
        sort_by: Column to sort by (default: momentum_12m)
    
    Returns:
        DataFrame with factor scores for all tickers
    """
    print(f"\n🔬 Running factor analysis on {len(tickers)} stocks...\n")
    
    results = []
    for ticker in tickers:
        scores = get_factor_scores(ticker, verbose=False)
        results.append(scores)
        print(f"  ✅ {ticker.upper()}")
    
    df = pd.DataFrame(results)
    
    # Sort by specified column if exists
    if sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=False)
    
    print(f"\n✅ Factor comparison complete!\n")
    return df


def print_factor_report(scores: Dict, detailed: bool = True):
    """
    Print formatted factor analysis report.
    
    Args:
        scores: Factor scores dict from get_factor_scores()
        detailed: Show detailed metrics
    """
    ticker = scores['ticker']
    print(f"\n{'='*60}")
    print(f"  FACTOR ANALYSIS: {ticker}")
    print(f"  {scores['timestamp']}")
    print(f"{'='*60}\n")
    
    # Momentum
    print("📈 MOMENTUM")
    print(f"   12-Month Return (ex-1mo): {scores['momentum_12m']:.2f}%" if scores['momentum_12m'] else "   Data unavailable")
    
    # Value
    print("\n💰 VALUE")
    print(f"   P/E Ratio:      {scores['PE']:.2f}" if scores['PE'] else "   P/E:      N/A")
    print(f"   P/B Ratio:      {scores['PB']:.2f}" if scores['PB'] else "   P/B:      N/A")
    print(f"   P/S Ratio:      {scores['PS']:.2f}" if scores['PS'] else "   P/S:      N/A")
    print(f"   EV/EBITDA:      {scores['EV_EBITDA']:.2f}" if scores['EV_EBITDA'] else "   EV/EBITDA: N/A")
    print(f"   Div Yield:      {scores['DivYield']:.2f}%" if scores['DivYield'] else "   Div Yield: N/A")
    
    # Quality
    print("\n⭐ QUALITY")
    print(f"   ROE:            {scores['ROE']:.2f}%" if scores['ROE'] else "   ROE:      N/A")
    print(f"   ROA:            {scores['ROA']:.2f}%" if scores['ROA'] else "   ROA:      N/A")
    print(f"   Profit Margin:  {scores['ProfitMargin']:.2f}%" if scores['ProfitMargin'] else "   Margin:   N/A")
    print(f"   Debt/Equity:    {scores['DebtToEquity']:.2f}" if scores['DebtToEquity'] else "   D/E:      N/A")
    print(f"   Current Ratio:  {scores['CurrentRatio']:.2f}" if scores['CurrentRatio'] else "   Current:  N/A")
    
    # Size
    print("\n📏 SIZE")
    print(f"   Market Cap:     ${scores['MarketCap']:.2f}B" if scores['MarketCap'] else "   Market Cap: N/A")
    
    # Volatility
    print("\n📊 VOLATILITY & RISK")
    print(f"   Ann. Volatility: {scores['Volatility']:.2f}%" if scores['Volatility'] else "   Volatility: N/A")
    print(f"   Beta (vs SPY):   {scores['Beta']:.2f}" if scores['Beta'] else "   Beta:       N/A")
    
    print(f"\n{'='*60}\n")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python factor_model_engine.py factors <TICKER>")
        print("  python factor_model_engine.py factor-compare <TICKER1,TICKER2,...>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command in ['factors', 'factor-score'] and len(sys.argv) >= 3:
        # Single ticker - detailed report
        ticker = sys.argv[2]
        scores = get_factor_scores(ticker)
        print_factor_report(scores)
    
    elif command == 'factor-compare' and len(sys.argv) >= 3:
        # Multiple tickers - comparison table
        tickers_str = sys.argv[2]
        tickers = [t.strip().upper() for t in tickers_str.split(',')]
        df = compare_factors(tickers)
        print(df.to_string(index=False))
    
    else:
        print("Error: Invalid usage")
        print("\nUsage:")
        print("  python factor_model_engine.py factors <TICKER>")
        print("  python factor_model_engine.py factor-compare <TICKER1,TICKER2,...>")
        sys.exit(1)

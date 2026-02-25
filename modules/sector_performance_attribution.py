#!/usr/bin/env python3
"""
Sector Performance Attribution — Phase 60

Decompose portfolio returns into:
1. Allocation Effect — did you pick the right sectors?
2. Selection Effect — did you pick the right stocks within sectors?
3. Interaction Effect — combination of both

Uses Brinson-Fachler attribution model with free data from yfinance.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json


# Sector ETF mapping — use sector SPDRs as benchmarks
SECTOR_ETFS = {
    'Technology': 'XLK',
    'Financials': 'XLF',
    'Healthcare': 'XLC',
    'Consumer Discretionary': 'XLY',
    'Consumer Staples': 'XLP',
    'Energy': 'XLE',
    'Industrials': 'XLI',
    'Materials': 'XLB',
    'Real Estate': 'XLRE',
    'Utilities': 'XLU',
    'Communication Services': 'XLC'
}

# Benchmark index
BENCHMARK_ETF = 'SPY'  # S&P 500


def get_stock_sector(ticker: str) -> Optional[str]:
    """Get the sector for a stock ticker using yfinance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        sector = info.get('sector', None)
        return sector
    except Exception as e:
        print(f"Error getting sector for {ticker}: {e}")
        return None


def get_returns_data(tickers: List[str], period: str = '1y') -> pd.DataFrame:
    """
    Fetch price data and calculate returns for a list of tickers.
    
    Args:
        tickers: List of stock tickers
        period: Time period (1mo, 3mo, 6mo, 1y, 2y, 5y)
    
    Returns:
        DataFrame with returns for each ticker
    """
    try:
        data = yf.download(tickers, period=period, interval='1d', progress=False, auto_adjust=True)
        
        if len(tickers) == 1:
            # Single ticker — yfinance returns different structure
            prices = data['Close']
        else:
            prices = data['Close']
        
        # Calculate total returns
        returns = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
        
        return returns
    except Exception as e:
        print(f"Error fetching returns data: {e}")
        return pd.Series()


def get_sector_benchmark_returns(sector: str, period: str = '1y') -> float:
    """Get benchmark returns for a sector using sector ETFs."""
    etf = SECTOR_ETFS.get(sector, BENCHMARK_ETF)
    try:
        returns = get_returns_data([etf], period)
        if isinstance(returns, pd.Series):
            return float(returns.iloc[0]) if len(returns) > 0 else 0.0
        else:
            return float(returns) if not np.isnan(returns) else 0.0
    except:
        return 0.0


def calculate_brinson_fachler_attribution(
    portfolio: Dict[str, float],  # {ticker: weight}
    benchmark_weights: Dict[str, float],  # {sector: weight}
    period: str = '1y'
) -> Dict:
    """
    Calculate Brinson-Fachler performance attribution.
    
    Formula:
    - Allocation Effect = Σ(w_p,i - w_b,i) × R_b,i
    - Selection Effect = Σw_b,i × (R_p,i - R_b,i)
    - Interaction Effect = Σ(w_p,i - w_b,i) × (R_p,i - R_b,i)
    
    Where:
    - w_p,i = portfolio weight in sector i
    - w_b,i = benchmark weight in sector i
    - R_p,i = portfolio return in sector i
    - R_b,i = benchmark return in sector i
    """
    
    # Get tickers from portfolio
    tickers = list(portfolio.keys())
    
    # Fetch returns for all tickers
    ticker_returns = get_returns_data(tickers, period)
    if ticker_returns.empty:
        return {"error": "Could not fetch returns data"}
    
    # Get sectors for each ticker
    ticker_sectors = {}
    for ticker in tickers:
        sector = get_stock_sector(ticker)
        if sector:
            ticker_sectors[ticker] = sector
        else:
            ticker_sectors[ticker] = 'Unknown'
    
    # Calculate portfolio sector weights and returns
    portfolio_sectors = {}
    for ticker, weight in portfolio.items():
        sector = ticker_sectors.get(ticker, 'Unknown')
        if sector not in portfolio_sectors:
            portfolio_sectors[sector] = {'weight': 0.0, 'tickers': []}
        portfolio_sectors[sector]['weight'] += weight
        portfolio_sectors[sector]['tickers'].append(ticker)
    
    # Calculate sector-level returns for portfolio
    sector_data = []
    for sector, data in portfolio_sectors.items():
        # Weight-averaged returns within sector
        sector_return = 0.0
        sector_weight_sum = 0.0
        for ticker in data['tickers']:
            ticker_weight = portfolio[ticker]
            ticker_return = ticker_returns.get(ticker, 0)
            if isinstance(ticker_return, (pd.Series, pd.DataFrame)):
                ticker_return = float(ticker_return.iloc[0]) if len(ticker_return) > 0 else 0.0
            sector_return += ticker_weight * ticker_return
            sector_weight_sum += ticker_weight
        
        if sector_weight_sum > 0:
            sector_return = sector_return / sector_weight_sum
        
        # Get benchmark return for this sector
        benchmark_return = get_sector_benchmark_returns(sector, period)
        benchmark_weight = benchmark_weights.get(sector, 1.0 / len(SECTOR_ETFS))
        
        sector_data.append({
            'sector': sector,
            'portfolio_weight': data['weight'],
            'benchmark_weight': benchmark_weight,
            'portfolio_return': sector_return,
            'benchmark_return': benchmark_return
        })
    
    # Calculate attribution effects
    allocation_effect = 0.0
    selection_effect = 0.0
    interaction_effect = 0.0
    
    for s in sector_data:
        w_p = s['portfolio_weight']
        w_b = s['benchmark_weight']
        r_p = s['portfolio_return']
        r_b = s['benchmark_return']
        
        # Brinson-Fachler formulas
        allocation = (w_p - w_b) * r_b
        selection = w_b * (r_p - r_b)
        interaction = (w_p - w_b) * (r_p - r_b)
        
        allocation_effect += allocation
        selection_effect += selection
        interaction_effect += interaction
    
    # Calculate total portfolio return
    portfolio_return = sum([
        portfolio[ticker] * (ticker_returns.get(ticker, 0) if not isinstance(ticker_returns.get(ticker, 0), pd.Series) else ticker_returns.get(ticker, 0).iloc[0])
        for ticker in tickers
    ])
    
    # Get benchmark return
    benchmark_return_data = get_returns_data([BENCHMARK_ETF], period)
    benchmark_return = float(benchmark_return_data) if not isinstance(benchmark_return_data, pd.Series) else float(benchmark_return_data.iloc[0])
    
    # Active return
    active_return = portfolio_return - benchmark_return
    
    return {
        'period': period,
        'portfolio_return_pct': round(portfolio_return, 2),
        'benchmark_return_pct': round(benchmark_return, 2),
        'active_return_pct': round(active_return, 2),
        'attribution': {
            'allocation_effect_pct': round(allocation_effect, 2),
            'selection_effect_pct': round(selection_effect, 2),
            'interaction_effect_pct': round(interaction_effect, 2),
            'total_effect_pct': round(allocation_effect + selection_effect + interaction_effect, 2)
        },
        'sector_breakdown': sector_data,
        'interpretation': generate_interpretation(allocation_effect, selection_effect, interaction_effect, active_return)
    }


def generate_interpretation(allocation: float, selection: float, interaction: float, active_return: float) -> List[str]:
    """Generate human-readable interpretation of attribution results."""
    insights = []
    
    # Overall performance
    if active_return > 0:
        insights.append(f"✓ Portfolio outperformed benchmark by {abs(active_return):.2f}%")
    else:
        insights.append(f"✗ Portfolio underperformed benchmark by {abs(active_return):.2f}%")
    
    # Allocation effect
    if abs(allocation) > 0.5:
        if allocation > 0:
            insights.append(f"✓ Strong sector allocation (+{allocation:.2f}%) — picked the right sectors")
        else:
            insights.append(f"✗ Poor sector allocation ({allocation:.2f}%) — overweight in wrong sectors")
    else:
        insights.append("○ Neutral sector allocation — sector bets had minimal impact")
    
    # Selection effect
    if abs(selection) > 0.5:
        if selection > 0:
            insights.append(f"✓ Excellent stock selection (+{selection:.2f}%) — picked winners within sectors")
        else:
            insights.append(f"✗ Poor stock selection ({selection:.2f}%) — picked losers within sectors")
    else:
        insights.append("○ Neutral stock selection — stock picks matched sector benchmarks")
    
    # Interaction effect
    if abs(interaction) > 0.3:
        if interaction > 0:
            insights.append(f"✓ Positive interaction (+{interaction:.2f}%) — strong combination of both")
        else:
            insights.append(f"○ Negative interaction ({interaction:.2f}%) — conflicting strategies")
    
    # Dominant effect
    effects = {'Allocation': allocation, 'Selection': selection, 'Interaction': interaction}
    dominant = max(effects, key=lambda k: abs(effects[k]))
    if abs(effects[dominant]) > 1.0:
        insights.append(f"📊 Primary driver: {dominant} effect ({effects[dominant]:.2f}%)")
    
    return insights


def run_attribution(portfolio: Dict[str, float], period: str = '1y') -> Dict:
    """
    Main function to run sector performance attribution.
    
    Args:
        portfolio: Dict of {ticker: weight} (weights should sum to 1.0)
        period: Analysis period (1mo, 3mo, 6mo, 1y, 2y, 5y)
    
    Returns:
        Attribution results with allocation/selection/interaction effects
    """
    # S&P 500 sector weights (approximate, as of 2024)
    benchmark_weights = {
        'Technology': 0.28,
        'Financials': 0.13,
        'Healthcare': 0.13,
        'Consumer Discretionary': 0.11,
        'Communication Services': 0.09,
        'Industrials': 0.08,
        'Consumer Staples': 0.06,
        'Energy': 0.04,
        'Utilities': 0.03,
        'Real Estate': 0.03,
        'Materials': 0.02
    }
    
    return calculate_brinson_fachler_attribution(portfolio, benchmark_weights, period)


def analyze_single_stock_attribution(ticker: str, period: str = '1y') -> Dict:
    """Analyze attribution for a single stock vs its sector benchmark."""
    sector = get_stock_sector(ticker)
    if not sector:
        return {"error": f"Could not determine sector for {ticker}"}
    
    # Create single-stock portfolio
    portfolio = {ticker: 1.0}
    
    # Run attribution
    result = run_attribution(portfolio, period)
    result['ticker'] = ticker
    result['sector'] = sector
    
    return result


if __name__ == "__main__":
    # Test with sample portfolio
    test_portfolio = {
        'AAPL': 0.25,
        'MSFT': 0.25,
        'GOOGL': 0.20,
        'JPM': 0.15,
        'JNJ': 0.15
    }
    
    print("=== Sector Performance Attribution Test ===\n")
    result = run_attribution(test_portfolio, period='1y')
    print(json.dumps(result, indent=2))

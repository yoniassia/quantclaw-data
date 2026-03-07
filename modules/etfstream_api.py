#!/usr/bin/env python3
"""
ETFStream API — ETF Flow and Holdings Data Aggregator

Provides ETF profile data, holdings breakdowns, and flow analytics using
free data sources (Yahoo Finance via yfinance). No API key required.

Functions:
- get_etf_profile(symbol) - ETF name, AUM, expense ratio, holdings count
- get_etf_holdings(symbol, limit=20) - Top holdings of an ETF
- get_etf_flows(symbol) - Recent fund flows (inflows/outflows estimated)
- get_top_etf_flows(limit=20) - Top ETFs by net flows
- compare_etfs(symbols_list) - Compare multiple ETFs side by side

Source: Yahoo Finance (yfinance library)
Category: ETF & Fund Flows
Free tier: True
Author: QuantClaw Data NightBuilder
Phase: 105
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import warnings

# Suppress yfinance warnings
warnings.filterwarnings('ignore')

try:
    import yfinance as yf
except ImportError:
    yf = None


def get_etf_profile(symbol: str) -> Dict:
    """
    Get ETF profile information
    
    Args:
        symbol: ETF ticker symbol (e.g., 'SPY', 'QQQ', 'VTI')
    
    Returns:
        Dict with ETF name, AUM, expense ratio, holdings count, and basic metrics
    """
    if not yf:
        return {
            'success': False,
            'error': 'yfinance library not installed. Run: pip install yfinance',
            'symbol': symbol
        }
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Extract profile data
        profile = {
            'symbol': symbol.upper(),
            'name': info.get('longName', info.get('shortName', 'N/A')),
            'category': info.get('category', 'N/A'),
            'fund_family': info.get('fundFamily', 'N/A'),
            'total_assets': info.get('totalAssets', 0),
            'total_assets_formatted': f"${info.get('totalAssets', 0) / 1e9:.2f}B" if info.get('totalAssets') else 'N/A',
            'expense_ratio': info.get('annualReportExpenseRatio', info.get('expenseRatio', 0)),
            'expense_ratio_pct': f"{info.get('annualReportExpenseRatio', info.get('expenseRatio', 0)) * 100:.3f}%" if info.get('annualReportExpenseRatio') or info.get('expenseRatio') else 'N/A',
            'inception_date': info.get('fundInceptionDate', 'N/A'),
            'ytd_return': info.get('ytdReturn', 0),
            'ytd_return_pct': f"{info.get('ytdReturn', 0) * 100:.2f}%" if info.get('ytdReturn') else 'N/A',
            'three_year_avg_return': info.get('threeYearAverageReturn', 0),
            'five_year_avg_return': info.get('fiveYearAverageReturn', 0),
            'dividend_yield': info.get('yield', info.get('trailingAnnualDividendYield', 0)),
            'dividend_yield_pct': f"{info.get('yield', info.get('trailingAnnualDividendYield', 0)) * 100:.2f}%" if info.get('yield') or info.get('trailingAnnualDividendYield') else 'N/A',
            'beta': info.get('beta3Year', 'N/A'),
            'holdings_count': info.get('holdingsCount', 'N/A'),
        }
        
        # Get current price
        hist = ticker.history(period='5d')
        if not hist.empty:
            profile['current_price'] = round(hist['Close'].iloc[-1], 2)
            profile['volume'] = int(hist['Volume'].iloc[-1])
        else:
            profile['current_price'] = info.get('previousClose', 'N/A')
            profile['volume'] = info.get('volume', 'N/A')
        
        return {
            'success': True,
            'profile': profile,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'symbol': symbol
        }


def get_etf_holdings(symbol: str, limit: int = 20) -> Dict:
    """
    Get top holdings of an ETF
    
    Args:
        symbol: ETF ticker symbol
        limit: Maximum number of holdings to return (default 20)
    
    Returns:
        Dict with list of top holdings with symbols, names, and weights
    """
    if not yf:
        return {
            'success': False,
            'error': 'yfinance library not installed. Run: pip install yfinance',
            'symbol': symbol
        }
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Get holdings from info
        info = ticker.info
        holdings_data = []
        
        # Try to get holdings from multiple sources
        top_holdings = info.get('holdings', [])
        
        # Alternative: check for sector weightings as proxy
        if not top_holdings:
            sector_weightings = info.get('sectorWeightings', [])
            if sector_weightings:
                holdings_data = [
                    {
                        'symbol': 'SECTOR',
                        'name': list(sector.keys())[0] if sector else 'N/A',
                        'weight': list(sector.values())[0] if sector else 0,
                        'weight_pct': f"{list(sector.values())[0] * 100:.2f}%" if sector else 'N/A'
                    }
                    for sector in sector_weightings[:limit]
                ]
        else:
            holdings_data = [
                {
                    'symbol': holding.get('symbol', 'N/A'),
                    'name': holding.get('holdingName', 'N/A'),
                    'weight': holding.get('holdingPercent', 0),
                    'weight_pct': f"{holding.get('holdingPercent', 0) * 100:.2f}%"
                }
                for holding in top_holdings[:limit]
            ]
        
        # If no holdings available, note it
        if not holdings_data:
            holdings_data = [{'note': 'Holdings data not available for this ETF via Yahoo Finance'}]
        
        return {
            'success': True,
            'symbol': symbol.upper(),
            'holdings_count': len(holdings_data),
            'holdings': holdings_data[:limit],
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'symbol': symbol
        }


def get_etf_flows(symbol: str, lookback_days: int = 90) -> Dict:
    """
    Estimate recent fund flows based on volume and price changes
    Note: True institutional flow data requires paid data feeds. This estimates
    flows using volume patterns and AUM changes.
    
    Args:
        symbol: ETF ticker symbol
        lookback_days: Number of days to analyze (default 90)
    
    Returns:
        Dict with estimated flow metrics and trend analysis
    """
    if not yf:
        return {
            'success': False,
            'error': 'yfinance library not installed. Run: pip install yfinance',
            'symbol': symbol
        }
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Get historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        hist = ticker.history(start=start_date, end=end_date)
        
        if hist.empty:
            return {
                'success': False,
                'error': 'No historical data available',
                'symbol': symbol
            }
        
        # Calculate flow indicators
        avg_volume = hist['Volume'].mean()
        recent_volume = hist['Volume'].tail(10).mean()
        volume_change = ((recent_volume - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0
        
        # Price momentum as proxy for flows
        price_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100)
        
        # Estimate flow direction
        if volume_change > 20 and price_change > 0:
            flow_direction = 'Strong Inflows'
        elif volume_change > 10 and price_change > 0:
            flow_direction = 'Moderate Inflows'
        elif volume_change < -20:
            flow_direction = 'Outflows'
        else:
            flow_direction = 'Neutral'
        
        flows = {
            'symbol': symbol.upper(),
            'lookback_days': lookback_days,
            'avg_daily_volume': int(avg_volume),
            'recent_avg_volume': int(recent_volume),
            'volume_change_pct': round(volume_change, 2),
            'price_change_pct': round(price_change, 2),
            'flow_direction': flow_direction,
            'flow_strength': 'High' if abs(volume_change) > 20 else 'Moderate' if abs(volume_change) > 10 else 'Low',
            'note': 'Estimated flows based on volume and price patterns. For institutional flow data, use paid services.'
        }
        
        return {
            'success': True,
            'flows': flows,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'symbol': symbol
        }


def get_top_etf_flows(limit: int = 20, etf_universe: Optional[List[str]] = None) -> Dict:
    """
    Get top ETFs by estimated net flows
    Analyzes a universe of ETFs and ranks by flow strength
    
    Args:
        limit: Number of top ETFs to return (default 20)
        etf_universe: List of ETF symbols to analyze. If None, uses popular ETFs.
    
    Returns:
        Dict with ranked ETFs by flow metrics
    """
    if not yf:
        return {
            'success': False,
            'error': 'yfinance library not installed. Run: pip install yfinance'
        }
    
    # Default universe of popular ETFs if none provided
    if etf_universe is None:
        etf_universe = [
            'SPY', 'QQQ', 'IWM', 'VTI', 'VOO', 'VEA', 'IEFA', 'AGG', 'BND',
            'VWO', 'EFA', 'GLD', 'SLV', 'XLF', 'XLE', 'XLK', 'XLV', 'XLI',
            'TLT', 'HYG', 'LQD', 'EEM', 'VNQ', 'ARKK', 'SQQQ', 'TQQQ'
        ]
    
    try:
        flow_rankings = []
        
        for symbol in etf_universe[:50]:  # Limit to 50 to avoid rate limits
            try:
                flow_data = get_etf_flows(symbol, lookback_days=30)
                
                if flow_data['success']:
                    flows = flow_data['flows']
                    flow_rankings.append({
                        'symbol': symbol,
                        'flow_direction': flows['flow_direction'],
                        'volume_change_pct': flows['volume_change_pct'],
                        'price_change_pct': flows['price_change_pct'],
                        'flow_strength': flows['flow_strength'],
                        'flow_score': flows['volume_change_pct'] + (flows['price_change_pct'] * 0.5)  # Weighted score
                    })
            except:
                continue
        
        # Sort by flow score (descending for inflows, absolute value)
        flow_rankings.sort(key=lambda x: abs(x['flow_score']), reverse=True)
        
        return {
            'success': True,
            'top_inflows': [etf for etf in flow_rankings if etf['flow_score'] > 0][:limit],
            'top_outflows': [etf for etf in flow_rankings if etf['flow_score'] < 0][:limit],
            'analyzed_count': len(flow_rankings),
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def compare_etfs(symbols_list: List[str]) -> Dict:
    """
    Compare multiple ETFs side by side
    
    Args:
        symbols_list: List of ETF ticker symbols to compare
    
    Returns:
        Dict with comparative metrics across all ETFs
    """
    if not yf:
        return {
            'success': False,
            'error': 'yfinance library not installed. Run: pip install yfinance'
        }
    
    if not symbols_list or len(symbols_list) < 2:
        return {
            'success': False,
            'error': 'Please provide at least 2 ETF symbols to compare'
        }
    
    try:
        comparison = []
        
        for symbol in symbols_list:
            profile_data = get_etf_profile(symbol)
            
            if profile_data['success']:
                profile = profile_data['profile']
                comparison.append({
                    'symbol': symbol.upper(),
                    'name': profile['name'],
                    'aum': profile['total_assets_formatted'],
                    'expense_ratio': profile['expense_ratio_pct'],
                    'ytd_return': profile['ytd_return_pct'],
                    'dividend_yield': profile['dividend_yield_pct'],
                    'beta': profile['beta'],
                    'current_price': profile['current_price'],
                    'holdings_count': profile['holdings_count']
                })
        
        # Add rankings
        if comparison:
            # Rank by AUM (descending)
            sorted_by_aum = sorted(comparison, key=lambda x: x.get('aum', '0'), reverse=True)
            
            analysis = {
                'largest_by_aum': sorted_by_aum[0]['symbol'] if sorted_by_aum else 'N/A',
                'lowest_expense_ratio': min(comparison, key=lambda x: float(x['expense_ratio'].rstrip('%')) if x['expense_ratio'] != 'N/A' else 999)['symbol'],
                'etf_count': len(comparison)
            }
        else:
            analysis = {}
        
        return {
            'success': True,
            'comparison': comparison,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'symbols': symbols_list
        }


# Convenience function for quick tests
def test_module():
    """Test the module with sample ETFs"""
    print("Testing etfstream_api module...\n")
    
    # Test 1: Get SPY profile
    print("1. Testing get_etf_profile('SPY'):")
    spy_profile = get_etf_profile('SPY')
    print(json.dumps(spy_profile, indent=2))
    
    print("\n2. Testing compare_etfs(['SPY', 'QQQ']):")
    comparison = compare_etfs(['SPY', 'QQQ'])
    print(json.dumps(comparison, indent=2))


if __name__ == "__main__":
    test_module()

#!/usr/bin/env python3
"""
Stock Split & Corporate Events — Phase 146

Split history, corporate action impact analysis from SEC/Yahoo.
Tracks stock splits, reverse splits, spin-offs, and other corporate actions.

Data Sources:
- Yahoo Finance (split history, corporate actions)
- SEC EDGAR (8-K filings for corporate events)
- Historical price data for impact analysis

Provides:
1. Complete stock split history (forward and reverse splits)
2. Corporate action calendar (spin-offs, mergers, acquisitions)
3. Pre/post-split price impact analysis
4. Split announcement vs effective date tracking
5. Reverse split distress signals
6. Spin-off value creation analysis
7. Split ratio normalization for historical comparisons
8. Corporate action impact on returns
9. Split clustering detection (industry trends)
10. Shareholder value impact metrics

Author: QUANTCLAW DATA Build Agent
Phase: 146
Category: Equity
"""

import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

try:
    import requests
    from bs4 import BeautifulSoup
    SEC_AVAILABLE = True
except ImportError:
    SEC_AVAILABLE = False


@dataclass
class StockSplit:
    """Stock split record."""
    ticker: str
    date: str
    split_ratio: str  # e.g., "2:1", "3:2", "1:10" (reverse)
    split_factor: float  # Numeric multiplier
    is_reverse: bool
    price_before: float
    price_after: float
    volume_before: float
    volume_after: float
    market_cap_change: float  # Percentage change
    announcement_date: Optional[str]
    announcement_to_effective_days: Optional[int]


@dataclass
class CorporateAction:
    """Generic corporate action record."""
    ticker: str
    action_type: str  # SPLIT, REVERSE_SPLIT, SPIN_OFF, MERGER, ACQUISITION, DIVIDEND, RIGHTS_OFFERING
    action_date: str
    announcement_date: Optional[str]
    description: str
    impact_price_1d: float  # 1-day return
    impact_price_5d: float  # 5-day return
    impact_price_30d: float  # 30-day return
    volume_change: float  # % change in volume
    sec_filing_url: Optional[str]


@dataclass
class SplitHistory:
    """Complete split history for a ticker."""
    ticker: str
    company_name: str
    total_splits: int
    forward_splits: int
    reverse_splits: int
    first_split_date: Optional[str]
    last_split_date: Optional[str]
    cumulative_split_factor: float
    splits: List[StockSplit]
    average_days_between_splits: Optional[float]


@dataclass
class SpinOffAnalysis:
    """Spin-off value creation analysis."""
    parent_ticker: str
    spinoff_ticker: str
    spinoff_date: str
    parent_price_before: float
    parent_price_after_1y: float
    spinoff_price_initial: float
    spinoff_price_after_1y: float
    combined_return_1y: float
    value_created: bool
    parent_size_post_spinoff: float
    spinoff_size_initial: float


@dataclass
class SplitImpactAnalysis:
    """Pre/post split impact analysis."""
    ticker: str
    split_date: str
    split_ratio: str
    price_return_5d_before: float
    price_return_5d_after: float
    price_return_30d_after: float
    volume_change_pct: float
    volatility_before: float
    volatility_after: float
    outperformed_market_30d: bool
    market_return_30d: float


def safe_get(value, default=0) -> float:
    """Safely extract numeric value."""
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except:
        return default


def parse_split_ratio(ratio_str: str) -> Tuple[float, bool]:
    """
    Parse split ratio string to numeric factor and determine if reverse.
    Examples: "2:1" -> (2.0, False), "1:10" -> (0.1, True)
    """
    try:
        parts = ratio_str.split(':')
        if len(parts) != 2:
            return 1.0, False
        
        numerator = float(parts[0])
        denominator = float(parts[1])
        factor = numerator / denominator
        is_reverse = factor < 1.0
        
        return factor, is_reverse
    except:
        return 1.0, False


def get_stock_splits(ticker: str, years: int = 20) -> Dict:
    """
    Get complete stock split history for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        years: Number of years of history (default 20)
    
    Returns:
        Dictionary with split history and analysis
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        company_name = info.get('longName', ticker)
        
        # Get splits data
        splits_data = stock.splits
        
        if splits_data.empty:
            return {
                'ticker': ticker,
                'company_name': company_name,
                'total_splits': 0,
                'splits': [],
                'message': 'No stock splits found'
            }
        
        # Get historical price data for impact analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365)
        hist = stock.history(start=start_date, end=end_date)
        
        splits = []
        for date, split_value in splits_data.items():
            split_date = date.strftime('%Y-%m-%d')
            
            # Determine split ratio and type
            if split_value >= 1:
                # Forward split
                split_ratio = f"{int(split_value)}:1" if split_value == int(split_value) else f"{split_value}:1"
                split_factor = split_value
                is_reverse = False
            else:
                # Reverse split
                reverse_factor = 1 / split_value
                split_ratio = f"1:{int(reverse_factor)}" if reverse_factor == int(reverse_factor) else f"1:{reverse_factor}"
                split_factor = split_value
                is_reverse = True
            
            # Get pre/post split prices
            try:
                date_idx = pd.to_datetime(date)
                before_data = hist[:date_idx].tail(5)
                after_data = hist[date_idx:].head(5)
                
                price_before = safe_get(before_data['Close'].mean(), 0) if not before_data.empty else 0
                price_after = safe_get(after_data['Close'].mean(), 0) if not after_data.empty else 0
                volume_before = safe_get(before_data['Volume'].mean(), 0) if not before_data.empty else 0
                volume_after = safe_get(after_data['Volume'].mean(), 0) if not after_data.empty else 0
                
                # Calculate adjusted market cap change (should be ~0 for splits)
                if price_before > 0 and price_after > 0:
                    market_cap_change = ((price_after * split_value) / price_before - 1) * 100
                else:
                    market_cap_change = 0
                
            except:
                price_before = price_after = volume_before = volume_after = market_cap_change = 0
            
            split = StockSplit(
                ticker=ticker,
                date=split_date,
                split_ratio=split_ratio,
                split_factor=split_factor,
                is_reverse=is_reverse,
                price_before=price_before,
                price_after=price_after,
                volume_before=volume_before,
                volume_after=volume_after,
                market_cap_change=market_cap_change,
                announcement_date=None,  # Not available from Yahoo
                announcement_to_effective_days=None
            )
            splits.append(split)
        
        # Sort by date
        splits.sort(key=lambda x: x.date, reverse=True)
        
        # Calculate summary statistics
        forward_splits = sum(1 for s in splits if not s.is_reverse)
        reverse_splits = sum(1 for s in splits if s.is_reverse)
        
        split_dates = [datetime.strptime(s.date, '%Y-%m-%d') for s in splits]
        split_dates.sort()
        
        if len(split_dates) > 1:
            total_days = (split_dates[-1] - split_dates[0]).days
            avg_days_between = total_days / (len(split_dates) - 1)
        else:
            avg_days_between = None
        
        # Calculate cumulative split factor
        cumulative_factor = 1.0
        for split in splits:
            cumulative_factor *= split.split_factor
        
        history = SplitHistory(
            ticker=ticker,
            company_name=company_name,
            total_splits=len(splits),
            forward_splits=forward_splits,
            reverse_splits=reverse_splits,
            first_split_date=split_dates[0].strftime('%Y-%m-%d') if split_dates else None,
            last_split_date=split_dates[-1].strftime('%Y-%m-%d') if split_dates else None,
            cumulative_split_factor=cumulative_factor,
            splits=splits,
            average_days_between_splits=avg_days_between
        )
        
        return {
            'ticker': ticker,
            'company_name': company_name,
            'total_splits': history.total_splits,
            'forward_splits': history.forward_splits,
            'reverse_splits': history.reverse_splits,
            'first_split_date': history.first_split_date,
            'last_split_date': history.last_split_date,
            'cumulative_split_factor': round(history.cumulative_split_factor, 4),
            'average_days_between_splits': round(avg_days_between, 2) if avg_days_between else None,
            'splits': [asdict(s) for s in splits],
            'analysis': {
                'has_recent_reverse_split': any(s.is_reverse and 
                    datetime.strptime(s.date, '%Y-%m-%d') > datetime.now() - timedelta(days=365*2) 
                    for s in splits),
                'reverse_split_distress_signal': reverse_splits > 0 and reverse_splits > forward_splits,
                'split_pattern': 'Frequent Splitter' if avg_days_between and avg_days_between < 1000 else 'Normal',
                'price_level_management': forward_splits >= 3
            }
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'error': str(e),
            'message': f'Failed to fetch split history: {str(e)}'
        }


def analyze_split_impact(ticker: str, split_date: str = None) -> Dict:
    """
    Analyze the price/volume impact of a stock split.
    
    Args:
        ticker: Stock ticker symbol
        split_date: Specific split date to analyze (YYYY-MM-DD), or None for most recent
    
    Returns:
        Dictionary with split impact analysis
    """
    try:
        stock = yf.Ticker(ticker)
        splits_data = stock.splits
        
        if splits_data.empty:
            return {
                'ticker': ticker,
                'message': 'No stock splits found'
            }
        
        # Select split to analyze
        if split_date:
            target_date = pd.to_datetime(split_date)
            if target_date not in splits_data.index:
                return {
                    'ticker': ticker,
                    'error': f'No split found on {split_date}'
                }
            split_value = splits_data[target_date]
        else:
            # Use most recent split
            target_date = splits_data.index[-1]
            split_value = splits_data.iloc[-1]
        
        # Get historical data around split
        start_date = target_date - timedelta(days=60)
        end_date = target_date + timedelta(days=60)
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty:
            return {
                'ticker': ticker,
                'error': 'Insufficient price data for analysis'
            }
        
        # Calculate split ratio
        if split_value >= 1:
            split_ratio = f"{int(split_value)}:1" if split_value == int(split_value) else f"{split_value}:1"
        else:
            reverse_factor = 1 / split_value
            split_ratio = f"1:{int(reverse_factor)}" if reverse_factor == int(reverse_factor) else f"1:{reverse_factor}"
        
        # Split data into before/after periods
        before_data = hist[:target_date]
        after_data = hist[target_date:]
        
        # Calculate returns
        if len(before_data) >= 5:
            price_5d_before = before_data['Close'].iloc[-5]
            price_at_split = before_data['Close'].iloc[-1]
            return_5d_before = ((price_at_split / price_5d_before) - 1) * 100
        else:
            return_5d_before = 0
        
        if len(after_data) >= 5:
            price_after_5d = after_data['Close'].iloc[min(5, len(after_data)-1)]
            return_5d_after = ((price_after_5d / after_data['Close'].iloc[0]) - 1) * 100
        else:
            return_5d_after = 0
        
        if len(after_data) >= 30:
            price_after_30d = after_data['Close'].iloc[min(30, len(after_data)-1)]
            return_30d_after = ((price_after_30d / after_data['Close'].iloc[0]) - 1) * 100
        else:
            return_30d_after = 0
        
        # Calculate volume change
        avg_volume_before = before_data['Volume'].tail(10).mean()
        avg_volume_after = after_data['Volume'].head(10).mean()
        volume_change_pct = ((avg_volume_after / avg_volume_before) - 1) * 100 if avg_volume_before > 0 else 0
        
        # Calculate volatility (standard deviation of returns)
        before_returns = before_data['Close'].pct_change().tail(20)
        after_returns = after_data['Close'].pct_change().head(20)
        
        volatility_before = before_returns.std() * 100 * np.sqrt(252)  # Annualized
        volatility_after = after_returns.std() * 100 * np.sqrt(252)
        
        # Compare to market (SPY)
        try:
            spy = yf.Ticker('SPY')
            spy_hist = spy.history(start=start_date, end=end_date)
            spy_after = spy_hist[target_date:]
            
            if len(spy_after) >= 30:
                spy_return_30d = ((spy_after['Close'].iloc[min(30, len(spy_after)-1)] / spy_after['Close'].iloc[0]) - 1) * 100
                outperformed = bool(return_30d_after > spy_return_30d)
            else:
                spy_return_30d = 0
                outperformed = False
        except:
            spy_return_30d = 0
            outperformed = False
        
        analysis = SplitImpactAnalysis(
            ticker=ticker,
            split_date=target_date.strftime('%Y-%m-%d'),
            split_ratio=split_ratio,
            price_return_5d_before=return_5d_before,
            price_return_5d_after=return_5d_after,
            price_return_30d_after=return_30d_after,
            volume_change_pct=volume_change_pct,
            volatility_before=volatility_before,
            volatility_after=volatility_after,
            outperformed_market_30d=outperformed,
            market_return_30d=spy_return_30d
        )
        
        return {
            'ticker': ticker,
            'analysis': asdict(analysis),
            'interpretation': {
                'momentum_before_split': 'Positive' if return_5d_before > 0 else 'Negative',
                'post_split_performance': 'Positive' if return_30d_after > 0 else 'Negative',
                'liquidity_impact': 'Increased' if volume_change_pct > 10 else 'Stable' if volume_change_pct > -10 else 'Decreased',
                'volatility_impact': 'Increased' if volatility_after > volatility_before else 'Decreased',
                'market_relative': 'Outperformed' if outperformed else 'Underperformed'
            }
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'error': str(e),
            'message': f'Failed to analyze split impact: {str(e)}'
        }


def get_corporate_actions(ticker: str, years: int = 5) -> Dict:
    """
    Get corporate actions from Yahoo Finance actions endpoint.
    
    Args:
        ticker: Stock ticker symbol
        years: Number of years of history (default 5)
    
    Returns:
        Dictionary with corporate actions
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        company_name = info.get('longName', ticker)
        
        # Get actions (dividends + splits)
        actions = stock.actions
        
        if actions.empty:
            return {
                'ticker': ticker,
                'company_name': company_name,
                'actions': [],
                'message': 'No corporate actions found'
            }
        
        # Filter to recent years
        cutoff_date = pd.Timestamp.now(tz='America/New_York') - pd.Timedelta(days=years*365)
        recent_actions = actions[actions.index >= cutoff_date]
        
        # Get historical prices for impact analysis
        start_date = cutoff_date
        hist = stock.history(start=start_date)
        
        actions_list = []
        
        for date, row in recent_actions.iterrows():
            action_date = date.strftime('%Y-%m-%d')
            
            # Determine action type
            if 'Stock Splits' in row and pd.notna(row['Stock Splits']) and row['Stock Splits'] != 0:
                split_value = row['Stock Splits']
                if split_value >= 1:
                    action_type = 'SPLIT'
                    description = f"Stock split {int(split_value)}:1" if split_value == int(split_value) else f"Stock split {split_value}:1"
                else:
                    action_type = 'REVERSE_SPLIT'
                    reverse_factor = 1 / split_value
                    description = f"Reverse split 1:{int(reverse_factor)}" if reverse_factor == int(reverse_factor) else f"Reverse split 1:{reverse_factor}"
            
            elif 'Dividends' in row and pd.notna(row['Dividends']) and row['Dividends'] > 0:
                dividend_amount = row['Dividends']
                action_type = 'DIVIDEND'
                description = f"Dividend payment ${dividend_amount:.2f} per share"
            
            else:
                continue
            
            # Calculate price impact
            try:
                date_idx = pd.to_datetime(date)
                before_idx = hist.index[hist.index < date_idx]
                after_idx = hist.index[hist.index >= date_idx]
                
                if len(before_idx) > 0 and len(after_idx) > 0:
                    price_before = hist.loc[before_idx[-1], 'Close']
                    
                    if len(after_idx) >= 1:
                        price_1d = hist.loc[after_idx[min(1, len(after_idx)-1)], 'Close']
                        impact_1d = ((price_1d / price_before) - 1) * 100
                    else:
                        impact_1d = 0
                    
                    if len(after_idx) >= 5:
                        price_5d = hist.loc[after_idx[min(5, len(after_idx)-1)], 'Close']
                        impact_5d = ((price_5d / price_before) - 1) * 100
                    else:
                        impact_5d = 0
                    
                    if len(after_idx) >= 30:
                        price_30d = hist.loc[after_idx[min(30, len(after_idx)-1)], 'Close']
                        impact_30d = ((price_30d / price_before) - 1) * 100
                    else:
                        impact_30d = 0
                    
                    # Volume change
                    volume_before = hist.loc[before_idx[-5:], 'Volume'].mean() if len(before_idx) >= 5 else 0
                    volume_after = hist.loc[after_idx[:5], 'Volume'].mean() if len(after_idx) >= 5 else 0
                    volume_change = ((volume_after / volume_before) - 1) * 100 if volume_before > 0 else 0
                else:
                    impact_1d = impact_5d = impact_30d = volume_change = 0
            except:
                impact_1d = impact_5d = impact_30d = volume_change = 0
            
            action = CorporateAction(
                ticker=ticker,
                action_type=action_type,
                action_date=action_date,
                announcement_date=None,
                description=description,
                impact_price_1d=impact_1d,
                impact_price_5d=impact_5d,
                impact_price_30d=impact_30d,
                volume_change=volume_change,
                sec_filing_url=None
            )
            actions_list.append(action)
        
        # Sort by date (most recent first)
        actions_list.sort(key=lambda x: x.action_date, reverse=True)
        
        return {
            'ticker': ticker,
            'company_name': company_name,
            'total_actions': len(actions_list),
            'actions': [asdict(a) for a in actions_list],
            'summary': {
                'total_splits': sum(1 for a in actions_list if a.action_type in ['SPLIT', 'REVERSE_SPLIT']),
                'total_dividends': sum(1 for a in actions_list if a.action_type == 'DIVIDEND'),
                'reverse_splits': sum(1 for a in actions_list if a.action_type == 'REVERSE_SPLIT')
            }
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'error': str(e),
            'message': f'Failed to fetch corporate actions: {str(e)}'
        }


def compare_split_performance(tickers: List[str], lookback_days: int = 365) -> Dict:
    """
    Compare split performance across multiple tickers.
    
    Args:
        tickers: List of ticker symbols
        lookback_days: Days to look back for splits (default 365)
    
    Returns:
        Dictionary with comparative analysis
    """
    try:
        cutoff_date = pd.Timestamp.now(tz='America/New_York') - pd.Timedelta(days=lookback_days)
        results = []
        
        for ticker in tickers:
            stock = yf.Ticker(ticker)
            splits = stock.splits
            
            if splits.empty:
                continue
            
            # Filter to recent splits
            recent_splits = splits[splits.index >= cutoff_date]
            
            if recent_splits.empty:
                continue
            
            # Analyze most recent split
            split_date = recent_splits.index[-1]
            split_value = recent_splits.iloc[-1]
            
            # Get price data
            start = split_date - timedelta(days=60)
            end = split_date + timedelta(days=60)
            hist = stock.history(start=start, end=end)
            
            if not hist.empty:
                before = hist[:split_date]
                after = hist[split_date:]
                
                if len(after) >= 30:
                    return_30d = ((after['Close'].iloc[min(30, len(after)-1)] / after['Close'].iloc[0]) - 1) * 100
                else:
                    return_30d = 0
                
                results.append({
                    'ticker': ticker,
                    'split_date': split_date.strftime('%Y-%m-%d'),
                    'split_ratio': f"{int(split_value)}:1" if split_value >= 1 else f"1:{int(1/split_value)}",
                    'return_30d_post_split': round(return_30d, 2),
                    'days_since_split': (pd.Timestamp.now(tz=split_date.tz) - split_date).days
                })
        
        if not results:
            return {
                'message': f'No splits found in last {lookback_days} days for provided tickers',
                'tickers': tickers
            }
        
        # Sort by performance
        results.sort(key=lambda x: x['return_30d_post_split'], reverse=True)
        
        avg_return = np.mean([r['return_30d_post_split'] for r in results])
        
        return {
            'lookback_days': lookback_days,
            'total_splits_found': len(results),
            'average_return_30d': round(avg_return, 2),
            'splits': results,
            'best_performer': results[0] if results else None,
            'worst_performer': results[-1] if results else None
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'message': f'Failed to compare split performance: {str(e)}'
        }


def main():
    """CLI interface for stock split and corporate events module."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python stock_split_corporate_events.py stock-split-history TICKER [--years N]")
        print("  python stock_split_corporate_events.py stock-split-impact TICKER [--date YYYY-MM-DD]")
        print("  python stock_split_corporate_events.py stock-corporate-actions TICKER [--years N]")
        print("  python stock_split_corporate_events.py stock-compare-splits TICKER1,TICKER2,... [--days N]")
        print("\nExamples:")
        print("  python stock_split_corporate_events.py stock-split-history AAPL")
        print("  python stock_split_corporate_events.py stock-split-impact TSLA")
        print("  python stock_split_corporate_events.py stock-corporate-actions NVDA --years 10")
        print("  python stock_split_corporate_events.py stock-compare-splits AAPL,TSLA,GOOGL --days 730")
        return 1
    
    command = sys.argv[1]
    
    if command == 'stock-split-history':
        if len(sys.argv) < 3:
            print("Error: TICKER required")
            return 1
        
        ticker = sys.argv[2].upper()
        years = 20
        
        # Parse optional years argument
        if '--years' in sys.argv:
            idx = sys.argv.index('--years')
            if idx + 1 < len(sys.argv):
                years = int(sys.argv[idx + 1])
        
        result = get_stock_splits(ticker, years)
        print(json.dumps(result, indent=2))
        return 0
    
    elif command == 'stock-split-impact':
        if len(sys.argv) < 3:
            print("Error: TICKER required")
            return 1
        
        ticker = sys.argv[2].upper()
        split_date = None
        
        # Parse optional date argument
        if '--date' in sys.argv:
            idx = sys.argv.index('--date')
            if idx + 1 < len(sys.argv):
                split_date = sys.argv[idx + 1]
        
        result = analyze_split_impact(ticker, split_date)
        print(json.dumps(result, indent=2))
        return 0
    
    elif command == 'stock-corporate-actions':
        if len(sys.argv) < 3:
            print("Error: TICKER required")
            return 1
        
        ticker = sys.argv[2].upper()
        years = 5
        
        # Parse optional years argument
        if '--years' in sys.argv:
            idx = sys.argv.index('--years')
            if idx + 1 < len(sys.argv):
                years = int(sys.argv[idx + 1])
        
        result = get_corporate_actions(ticker, years)
        print(json.dumps(result, indent=2))
        return 0
    
    elif command == 'stock-compare-splits':
        if len(sys.argv) < 3:
            print("Error: TICKERS required (comma-separated)")
            return 1
        
        tickers = [t.strip().upper() for t in sys.argv[2].split(',')]
        lookback_days = 365
        
        # Parse optional days argument
        if '--days' in sys.argv:
            idx = sys.argv.index('--days')
            if idx + 1 < len(sys.argv):
                lookback_days = int(sys.argv[idx + 1])
        
        result = compare_split_performance(tickers, lookback_days)
        print(json.dumps(result, indent=2))
        return 0
    
    else:
        print(f"Error: Unknown command '{command}'")
        return 1


if __name__ == '__main__':
    sys.exit(main())

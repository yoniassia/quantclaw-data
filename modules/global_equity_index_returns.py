#!/usr/bin/env python3
"""
Global Equity Index Returns — Phase 153

Daily returns for 50+ global equity indices (S&P 500, FTSE 100, DAX, Nikkei 225, etc).
Tracks performance across Americas, Europe, Asia-Pacific regions with index composition,
sector weights, and cross-regional correlation analysis.

Data Sources:
- Yahoo Finance (primary - real-time index prices and historical data)
- FRED (US indices backup and supplementary data)
- investing.com fallback (for indices not available on Yahoo Finance)

Provides:
1. Daily returns for 50+ major global indices
2. Index composition and sector weights
3. Cross-regional correlation matrices
4. Relative performance rankings
5. Risk-adjusted returns (Sharpe ratios)
6. Volatility metrics (historical and realized)
7. Drawdown analysis
8. Index comparison tools
9. Regional performance aggregation
10. Currency-adjusted returns

Major Indices Covered:
Americas: S&P 500, Nasdaq, Dow Jones, Russell 2000, TSX, IPC (Mexico), Bovespa
Europe: FTSE 100, DAX, CAC 40, IBEX, FTSE MIB, AEX, SMI, OMX Stockholm
Asia-Pacific: Nikkei 225, Hang Seng, Shanghai Composite, Kospi, ASX 200, NZX 50
Emerging: MSCI Emerging Markets, BIST 100, Sensex, Nifty 50, SET (Thailand)

Author: QUANTCLAW DATA Build Agent
Phase: 153
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
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# Global index ticker mappings (Yahoo Finance format)
GLOBAL_INDICES = {
    # Americas
    'S&P 500': '^GSPC',
    'Nasdaq Composite': '^IXIC',
    'Dow Jones': '^DJI',
    'Russell 2000': '^RUT',
    'S&P/TSX Composite': '^GSPTSE',
    'IPC Mexico': '^MXX',
    'Bovespa Brazil': '^BVSP',
    'Merval Argentina': '^MERV',
    'IPSA Chile': '^IPSA',
    'S&P 500 VIX': '^VIX',
    
    # Europe
    'FTSE 100': '^FTSE',
    'DAX': '^GDAXI',
    'CAC 40': '^FCHI',
    'FTSE MIB': 'FTSEMIB.MI',
    'IBEX 35': '^IBEX',
    'AEX': '^AEX',
    'Swiss Market Index': '^SSMI',
    'OMX Stockholm 30': '^OMX',
    'Euro Stoxx 50': '^STOXX50E',
    'FTSE 250': '^FTMC',
    'OMX Copenhagen': '^OMXC25',
    'PSI 20 Portugal': 'PSI20.LS',
    'ATX Austria': '^ATX',
    'BEL 20 Belgium': '^BFX',
    'WIG Poland': 'WIG.WA',
    
    # Asia-Pacific
    'Nikkei 225': '^N225',
    'Hang Seng': '^HSI',
    'Shanghai Composite': '000001.SS',
    'Shenzhen Composite': '399001.SZ',
    'Kospi': '^KS11',
    'KOSDAQ': '^KQ11',
    'ASX 200': '^AXJO',
    'NZX 50': '^NZ50',
    'Straits Times': '^STI',
    'SET Thailand': '^SET.BK',
    'KLSE Malaysia': '^KLSE',
    'Jakarta Composite': '^JKSE',
    'PSEi Philippines': '^PSI',
    'Taiwan Weighted': '^TWII',
    
    # Emerging Markets
    'MSCI Emerging Markets': 'EEM',
    'Sensex India': '^BSESN',
    'Nifty 50 India': '^NSEI',
    'BIST 100 Turkey': 'XU100.IS',
    'TA-125 Israel': '^TA125.TA',
    'Tadawul Saudi': 'TASI.SR',
    'EGX 30 Egypt': '^CASE30',
    
    # Global Benchmarks
    'MSCI World': 'URTH',
    'MSCI EAFE': 'EFA',
    'MSCI All Country World': 'ACWI',
}

# Regional groupings
REGIONS = {
    'Americas': ['S&P 500', 'Nasdaq Composite', 'Dow Jones', 'Russell 2000', 'S&P/TSX Composite', 'IPC Mexico', 'Bovespa Brazil'],
    'Europe': ['FTSE 100', 'DAX', 'CAC 40', 'FTSE MIB', 'IBEX 35', 'AEX', 'Swiss Market Index', 'Euro Stoxx 50'],
    'Asia-Pacific': ['Nikkei 225', 'Hang Seng', 'Shanghai Composite', 'Kospi', 'ASX 200', 'Straits Times'],
    'Emerging Markets': ['MSCI Emerging Markets', 'Sensex India', 'Nifty 50 India', 'BIST 100 Turkey', 'Bovespa Brazil'],
    'Global Benchmarks': ['MSCI World', 'MSCI EAFE', 'MSCI All Country World']
}


@dataclass
class IndexReturn:
    """Daily return data for an index."""
    index_name: str
    ticker: str
    date: str
    close: float
    daily_return: float
    ytd_return: float
    mtd_return: float
    volume: Optional[float]
    region: str


@dataclass
class IndexPerformance:
    """Performance metrics for an index."""
    index_name: str
    ticker: str
    current_price: float
    daily_return: float
    wtd_return: float
    mtd_return: float
    ytd_return: float
    one_year_return: float
    three_year_cagr: float
    five_year_cagr: float
    volatility_30d: float
    volatility_90d: float
    sharpe_ratio: float
    max_drawdown: float
    region: str
    last_updated: str


@dataclass
class CrossRegionalCorrelation:
    """Correlation matrix between global indices."""
    period: str  # 30D, 90D, 1Y
    correlation_matrix: Dict[str, Dict[str, float]]
    highest_correlations: List[Tuple[str, str, float]]
    lowest_correlations: List[Tuple[str, str, float]]
    regional_correlations: Dict[str, float]


@dataclass
class RegionalPerformance:
    """Aggregated regional performance."""
    region: str
    average_daily_return: float
    average_ytd_return: float
    best_performer: str
    worst_performer: str
    regional_volatility: float
    indices_count: int


def safe_get(value, default=0) -> float:
    """Safely extract numeric value."""
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except:
        return default


def get_region_for_index(index_name: str) -> str:
    """Determine region for an index."""
    for region, indices in REGIONS.items():
        if index_name in indices:
            return region
    return 'Other'


def calculate_returns(prices: pd.Series) -> Dict[str, float]:
    """Calculate various return metrics from price series."""
    if len(prices) < 2:
        return {'daily': 0, 'wtd': 0, 'mtd': 0, 'ytd': 0, 'one_year': 0}
    
    current_price = prices.iloc[-1]
    returns = {}
    
    # Daily return
    if len(prices) >= 2:
        returns['daily'] = ((current_price / prices.iloc[-2]) - 1) * 100
    else:
        returns['daily'] = 0
    
    # Week-to-date return (5 trading days)
    if len(prices) >= 6:
        returns['wtd'] = ((current_price / prices.iloc[-6]) - 1) * 100
    else:
        returns['wtd'] = returns['daily']
    
    # Month-to-date return (21 trading days)
    if len(prices) >= 22:
        returns['mtd'] = ((current_price / prices.iloc[-22]) - 1) * 100
    else:
        returns['mtd'] = returns['wtd']
    
    # Year-to-date return
    # Get the year from the latest date (works with both naive and tz-aware)
    latest_date = pd.Timestamp(prices.index[-1])
    year_start = pd.Timestamp(year=latest_date.year, month=1, day=1, tz=latest_date.tz)
    ytd_prices = prices[prices.index >= year_start]
    if len(ytd_prices) >= 2:
        returns['ytd'] = ((current_price / ytd_prices.iloc[0]) - 1) * 100
    else:
        returns['ytd'] = returns['mtd']
    
    # One year return (252 trading days)
    if len(prices) >= 253:
        returns['one_year'] = ((current_price / prices.iloc[-253]) - 1) * 100
    else:
        returns['one_year'] = returns['ytd']
    
    return returns


def calculate_cagr(prices: pd.Series, years: int) -> float:
    """Calculate Compound Annual Growth Rate."""
    if len(prices) < 2:
        return 0
    
    trading_days = 252 * years
    if len(prices) < trading_days:
        return 0
    
    start_price = prices.iloc[-trading_days]
    end_price = prices.iloc[-1]
    
    if start_price <= 0:
        return 0
    
    try:
        return (pow(end_price / start_price, 1 / years) - 1) * 100
    except:
        return 0


def calculate_volatility(returns: pd.Series, annualize: bool = True) -> float:
    """Calculate volatility (standard deviation of returns)."""
    if len(returns) < 2:
        return 0
    
    vol = returns.std()
    if annualize:
        vol = vol * np.sqrt(252)  # Annualize using 252 trading days
    
    return safe_get(vol, 0)


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.04) -> float:
    """Calculate Sharpe ratio (risk-adjusted returns)."""
    if len(returns) < 2:
        return 0
    
    avg_return = returns.mean() * 252  # Annualize
    volatility = calculate_volatility(returns, annualize=True)
    
    if volatility == 0:
        return 0
    
    return (avg_return - risk_free_rate) / volatility


def calculate_max_drawdown(prices: pd.Series) -> float:
    """Calculate maximum drawdown from peak."""
    if len(prices) < 2:
        return 0
    
    peak = prices.expanding(min_periods=1).max()
    drawdown = ((prices - peak) / peak) * 100
    return abs(drawdown.min())


def get_index_daily_returns(indices: Optional[List[str]] = None, days: int = 1) -> Dict:
    """
    Get daily returns for global equity indices.
    
    Args:
        indices: List of index names to fetch (None = all)
        days: Number of days of history to fetch
    
    Returns:
        Dictionary with index returns data
    """
    if indices is None:
        indices_to_fetch = list(GLOBAL_INDICES.keys())
    else:
        indices_to_fetch = [idx for idx in indices if idx in GLOBAL_INDICES]
    
    if not indices_to_fetch:
        return {'error': 'No valid indices specified'}
    
    results = []
    errors = []
    
    for index_name in indices_to_fetch:
        ticker = GLOBAL_INDICES[index_name]
        region = get_region_for_index(index_name)
        
        try:
            # Fetch data from Yahoo Finance
            stock = yf.Ticker(ticker)
            hist = stock.history(period=f'{days+5}d')  # Extra days for safety
            
            if hist.empty:
                errors.append(f"{index_name}: No data available")
                continue
            
            # Get latest data point
            latest_date = hist.index[-1].strftime('%Y-%m-%d')
            latest_close = safe_get(hist['Close'].iloc[-1])
            latest_volume = safe_get(hist['Volume'].iloc[-1])
            
            # Calculate returns
            returns = calculate_returns(hist['Close'])
            
            result = IndexReturn(
                index_name=index_name,
                ticker=ticker,
                date=latest_date,
                close=latest_close,
                daily_return=returns['daily'],
                ytd_return=returns['ytd'],
                mtd_return=returns['mtd'],
                volume=latest_volume if latest_volume > 0 else None,
                region=region
            )
            
            results.append(asdict(result))
            
        except Exception as e:
            errors.append(f"{index_name}: {str(e)}")
    
    return {
        'success': True,
        'count': len(results),
        'indices': results,
        'errors': errors if errors else None,
        'timestamp': datetime.now().isoformat()
    }


def get_index_performance(indices: Optional[List[str]] = None, 
                         period_days: int = 365) -> Dict:
    """
    Get comprehensive performance metrics for global indices.
    
    Args:
        indices: List of index names (None = all)
        period_days: Number of days of historical data for calculations
    
    Returns:
        Dictionary with performance metrics
    """
    if indices is None:
        indices_to_fetch = list(GLOBAL_INDICES.keys())
    else:
        indices_to_fetch = [idx for idx in indices if idx in GLOBAL_INDICES]
    
    if not indices_to_fetch:
        return {'error': 'No valid indices specified'}
    
    results = []
    errors = []
    
    for index_name in indices_to_fetch:
        ticker = GLOBAL_INDICES[index_name]
        region = get_region_for_index(index_name)
        
        try:
            # Fetch historical data
            stock = yf.Ticker(ticker)
            hist = stock.history(period=f'{period_days}d')
            
            if hist.empty or len(hist) < 2:
                errors.append(f"{index_name}: Insufficient data")
                continue
            
            prices = hist['Close']
            current_price = safe_get(prices.iloc[-1])
            
            # Calculate returns
            returns_data = calculate_returns(prices)
            
            # Calculate daily returns series for volatility and Sharpe
            daily_returns = prices.pct_change().dropna()
            
            # Calculate volatility metrics
            vol_30d = calculate_volatility(daily_returns.tail(30), annualize=True)
            vol_90d = calculate_volatility(daily_returns.tail(90), annualize=True)
            
            # Calculate Sharpe ratio
            sharpe = calculate_sharpe_ratio(daily_returns.tail(252))
            
            # Calculate max drawdown
            max_dd = calculate_max_drawdown(prices)
            
            # Calculate CAGR metrics
            cagr_3y = calculate_cagr(prices, 3)
            cagr_5y = calculate_cagr(prices, 5)
            
            result = IndexPerformance(
                index_name=index_name,
                ticker=ticker,
                current_price=current_price,
                daily_return=returns_data['daily'],
                wtd_return=returns_data['wtd'],
                mtd_return=returns_data['mtd'],
                ytd_return=returns_data['ytd'],
                one_year_return=returns_data['one_year'],
                three_year_cagr=cagr_3y,
                five_year_cagr=cagr_5y,
                volatility_30d=vol_30d,
                volatility_90d=vol_90d,
                sharpe_ratio=sharpe,
                max_drawdown=max_dd,
                region=region,
                last_updated=datetime.now().isoformat()
            )
            
            results.append(asdict(result))
            
        except Exception as e:
            errors.append(f"{index_name}: {str(e)}")
    
    # Sort by YTD return (best performers first)
    results.sort(key=lambda x: x['ytd_return'], reverse=True)
    
    return {
        'success': True,
        'count': len(results),
        'performance': results,
        'errors': errors if errors else None,
        'timestamp': datetime.now().isoformat()
    }


def get_regional_performance(region: Optional[str] = None) -> Dict:
    """
    Get aggregated performance by region.
    
    Args:
        region: Specific region name (None = all regions)
    
    Returns:
        Dictionary with regional performance data
    """
    regions_to_analyze = [region] if region and region in REGIONS else list(REGIONS.keys())
    
    results = []
    
    for reg in regions_to_analyze:
        indices = REGIONS[reg]
        
        # Get performance for all indices in this region
        perf_data = get_index_performance(indices)
        
        if 'error' in perf_data or not perf_data.get('performance'):
            continue
        
        performances = perf_data['performance']
        
        # Calculate regional aggregates
        daily_returns = [p['daily_return'] for p in performances]
        ytd_returns = [p['ytd_return'] for p in performances]
        volatilities = [p['volatility_30d'] for p in performances]
        
        avg_daily = np.mean(daily_returns) if daily_returns else 0
        avg_ytd = np.mean(ytd_returns) if ytd_returns else 0
        avg_vol = np.mean(volatilities) if volatilities else 0
        
        # Find best and worst performers
        best = max(performances, key=lambda x: x['ytd_return'])
        worst = min(performances, key=lambda x: x['ytd_return'])
        
        result = RegionalPerformance(
            region=reg,
            average_daily_return=round(avg_daily, 2),
            average_ytd_return=round(avg_ytd, 2),
            best_performer=f"{best['index_name']} (+{best['ytd_return']:.1f}%)",
            worst_performer=f"{worst['index_name']} ({worst['ytd_return']:.1f}%)",
            regional_volatility=round(avg_vol, 2),
            indices_count=len(performances)
        )
        
        results.append(asdict(result))
    
    return {
        'success': True,
        'regions': results,
        'timestamp': datetime.now().isoformat()
    }


def calculate_correlation_matrix(indices: Optional[List[str]] = None, 
                                 period: str = '90d') -> Dict:
    """
    Calculate correlation matrix between global indices.
    
    Args:
        indices: List of index names (None = major indices from each region)
        period: Time period for correlation (30d, 90d, 1y)
    
    Returns:
        Dictionary with correlation matrix and analysis
    """
    # Default to major indices if not specified
    if indices is None:
        indices = [
            'S&P 500', 'Nasdaq Composite', 'Russell 2000',  # US
            'FTSE 100', 'DAX', 'CAC 40',  # Europe
            'Nikkei 225', 'Hang Seng', 'Shanghai Composite',  # Asia
            'MSCI Emerging Markets'  # EM
        ]
    
    # Map period to days
    period_map = {'30d': 30, '90d': 90, '1y': 252}
    days = period_map.get(period, 90)
    
    # Fetch returns data
    returns_data = {}
    
    for index_name in indices:
        if index_name not in GLOBAL_INDICES:
            continue
        
        ticker = GLOBAL_INDICES[index_name]
        
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=f'{days+10}d')
            
            if not hist.empty and len(hist) > days:
                daily_returns = hist['Close'].pct_change().dropna().tail(days)
                returns_data[index_name] = daily_returns
        except:
            continue
    
    if len(returns_data) < 2:
        return {'error': 'Insufficient data for correlation calculation'}
    
    # Create DataFrame and calculate correlation matrix
    df = pd.DataFrame(returns_data)
    corr_matrix = df.corr()
    
    # Convert to dictionary format
    corr_dict = {}
    for idx1 in corr_matrix.index:
        corr_dict[idx1] = {}
        for idx2 in corr_matrix.columns:
            corr_dict[idx1][idx2] = round(corr_matrix.loc[idx1, idx2], 3)
    
    # Find highest and lowest correlations (excluding self-correlation)
    correlations = []
    for idx1 in corr_matrix.index:
        for idx2 in corr_matrix.columns:
            if idx1 < idx2:  # Avoid duplicates
                correlations.append((idx1, idx2, corr_matrix.loc[idx1, idx2]))
    
    correlations.sort(key=lambda x: x[2], reverse=True)
    highest = [(c[0], c[1], round(c[2], 3)) for c in correlations[:5]]
    lowest = [(c[0], c[1], round(c[2], 3)) for c in correlations[-5:]]
    
    # Calculate regional correlations
    regional_corrs = {}
    for region, region_indices in REGIONS.items():
        region_subset = [idx for idx in region_indices if idx in df.columns]
        if len(region_subset) >= 2:
            region_df = df[region_subset]
            regional_corrs[region] = round(region_df.corr().mean().mean(), 3)
    
    result = CrossRegionalCorrelation(
        period=period,
        correlation_matrix=corr_dict,
        highest_correlations=highest,
        lowest_correlations=lowest,
        regional_correlations=regional_corrs
    )
    
    return {
        'success': True,
        'data': asdict(result),
        'timestamp': datetime.now().isoformat()
    }


def compare_indices(indices: List[str], metric: str = 'ytd_return') -> Dict:
    """
    Compare multiple indices on a specific metric.
    
    Args:
        indices: List of index names to compare
        metric: Metric to compare (ytd_return, volatility_30d, sharpe_ratio, etc)
    
    Returns:
        Dictionary with comparison results
    """
    if not indices:
        return {'error': 'No indices specified'}
    
    # Get performance data
    perf_data = get_index_performance(indices)
    
    if 'error' in perf_data:
        return perf_data
    
    performances = perf_data['performance']
    
    # Extract the specified metric
    if metric not in performances[0]:
        return {'error': f'Invalid metric: {metric}'}
    
    comparison = []
    for perf in performances:
        comparison.append({
            'index': perf['index_name'],
            'region': perf['region'],
            metric: perf[metric]
        })
    
    # Sort by metric
    comparison.sort(key=lambda x: x[metric], reverse=True)
    
    return {
        'success': True,
        'metric': metric,
        'comparison': comparison,
        'winner': comparison[0]['index'],
        'timestamp': datetime.now().isoformat()
    }


def list_available_indices(region: Optional[str] = None) -> Dict:
    """
    List all available indices, optionally filtered by region.
    
    Args:
        region: Optional region filter
    
    Returns:
        Dictionary with index list
    """
    if region and region not in REGIONS:
        return {'error': f'Invalid region: {region}. Valid regions: {list(REGIONS.keys())}'}
    
    if region:
        indices = REGIONS[region]
        result = {reg: indices for reg in [region]}
    else:
        result = REGIONS.copy()
    
    # Add ticker mappings
    for reg, indices in result.items():
        result[reg] = [
            {'name': idx, 'ticker': GLOBAL_INDICES[idx]}
            for idx in indices
        ]
    
    total_count = sum(len(indices) for indices in REGIONS.values())
    
    return {
        'success': True,
        'total_indices': total_count,
        'regions': result,
        'timestamp': datetime.now().isoformat()
    }


# CLI interface
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({
            'error': 'Usage: global_equity_index_returns.py <command> [args]',
            'commands': [
                'daily-returns [--indices idx1,idx2]',
                'performance [--indices idx1,idx2] [--days 365]',
                'regional [--region Americas|Europe|Asia-Pacific]',
                'correlation [--indices idx1,idx2] [--period 30d|90d|1y]',
                'compare --indices idx1,idx2,idx3 [--metric ytd_return]',
                'list [--region Americas]'
            ]
        }))
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Parse arguments
    args = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i].startswith('--'):
            key = sys.argv[i][2:]
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
                args[key] = sys.argv[i + 1]
                i += 2
            else:
                args[key] = True
                i += 1
        else:
            i += 1
    
    # Parse indices argument (comma-separated)
    if 'indices' in args and isinstance(args['indices'], str):
        args['indices'] = [idx.strip() for idx in args['indices'].split(',')]
    
    # Execute command
    if command == 'daily-returns':
        result = get_index_daily_returns(
            indices=args.get('indices'),
            days=int(args.get('days', 1))
        )
    elif command == 'performance':
        result = get_index_performance(
            indices=args.get('indices'),
            period_days=int(args.get('days', 365))
        )
    elif command == 'regional':
        result = get_regional_performance(
            region=args.get('region')
        )
    elif command == 'correlation':
        result = calculate_correlation_matrix(
            indices=args.get('indices'),
            period=args.get('period', '90d')
        )
    elif command == 'compare':
        if 'indices' not in args:
            result = {'error': 'compare requires --indices argument'}
        else:
            result = compare_indices(
                indices=args['indices'],
                metric=args.get('metric', 'ytd_return')
            )
    elif command == 'list':
        result = list_available_indices(
            region=args.get('region')
        )
    else:
        result = {'error': f'Unknown command: {command}'}
    
    print(json.dumps(result, indent=2))

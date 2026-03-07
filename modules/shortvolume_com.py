#!/usr/bin/env python3
"""
ShortVolume.com / FINRA Short Sale Volume Module

Daily short sale volume data from FINRA Trade Reporting Facility.
Tracks short volume, total volume, and short volume ratios for stocks
traded on NASDAQ, NYSE, and OTC markets.

Data Source: https://cdn.finra.org/equity/regsho/daily/
Reference: https://shortvolume.com
Category: Market Data / Short Selling
Free tier: True (no API key required)
Author: QuantClaw Data NightBuilder
Phase: NightBuilder
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from statistics import mean

# FINRA CDN base URL for short volume data
FINRA_BASE_URL = "https://cdn.finra.org/equity/regsho/daily"

# User agent to avoid being blocked
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def _fetch_finra_file(date: datetime) -> Optional[str]:
    """
    Fetch FINRA short volume file for a specific date (helper function)
    
    Args:
        date: datetime object for the date to fetch
    
    Returns:
        File content as string, or None if not available
    """
    date_str = date.strftime("%Y%m%d")
    # CNMS = Consolidated (all markets: NYSE, NASDAQ, OTC)
    url = f"{FINRA_BASE_URL}/CNMSshvol{date_str}.txt"
    
    try:
        response = requests.get(
            url,
            headers={'User-Agent': USER_AGENT},
            timeout=15
        )
        
        if response.status_code == 200:
            return response.text
        else:
            return None
    
    except requests.RequestException:
        return None
    except Exception:
        return None


def _parse_finra_line(line: str) -> Optional[Dict]:
    """
    Parse a single line from FINRA short volume file
    
    Format: Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market
    
    Args:
        line: Single line from FINRA file
    
    Returns:
        Dict with parsed data or None if invalid
    """
    try:
        parts = line.strip().split('|')
        if len(parts) != 6:
            return None
        
        date_str, symbol, short_vol, short_exempt, total_vol, market = parts
        
        # Skip header line
        if symbol == 'Symbol':
            return None
        
        short_volume = float(short_vol)
        total_volume = float(total_vol)
        short_ratio = (short_volume / total_volume * 100) if total_volume > 0 else 0
        
        return {
            'date': date_str,
            'symbol': symbol,
            'short_volume': round(short_volume),
            'short_exempt_volume': round(float(short_exempt)),
            'total_volume': round(total_volume),
            'short_ratio': round(short_ratio, 2),
            'market': market
        }
    
    except (ValueError, ZeroDivisionError):
        return None
    except Exception:
        return None


def get_short_volume(ticker: str, date: Optional[datetime] = None) -> Dict:
    """
    Get current/latest short volume data for a ticker
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        date: Optional specific date (defaults to most recent available)
    
    Returns:
        Dict with short volume, total volume, and ratio
        
    Example:
        >>> data = get_short_volume('AAPL')
        >>> print(f"Short ratio: {data['short_ratio']}%")
    """
    ticker = ticker.upper().strip()
    
    # Try multiple recent dates (markets closed on weekends)
    if date is None:
        dates_to_try = [datetime.now() - timedelta(days=i) for i in range(10)]
    else:
        dates_to_try = [date]
    
    for try_date in dates_to_try:
        content = _fetch_finra_file(try_date)
        
        if content:
            lines = content.strip().split('\n')
            
            # Search for ticker
            for line in lines:
                if f"|{ticker}|" in line:
                    parsed = _parse_finra_line(line)
                    if parsed:
                        return {
                            'success': True,
                            'ticker': ticker,
                            'date': parsed['date'],
                            'short_volume': parsed['short_volume'],
                            'short_exempt_volume': parsed['short_exempt_volume'],
                            'total_volume': parsed['total_volume'],
                            'short_ratio': parsed['short_ratio'],
                            'market': parsed['market'],
                            'interpretation': _interpret_short_ratio(parsed['short_ratio'])
                        }
    
    return {
        'success': False,
        'error': f'No data found for {ticker} in recent dates',
        'ticker': ticker
    }


def get_short_volume_history(ticker: str, days: int = 30) -> Dict:
    """
    Get historical short volume data for a ticker
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days of history (default 30)
    
    Returns:
        Dict with historical data and trend analysis
        
    Example:
        >>> history = get_short_volume_history('TSLA', days=60)
        >>> print(f"Average short ratio: {history['avg_short_ratio']}%")
    """
    ticker = ticker.upper().strip()
    history = []
    
    # Fetch data for requested days (with buffer for weekends/holidays)
    for i in range(min(days * 2, 90)):  # Cap at 90 days to avoid too many requests
        check_date = datetime.now() - timedelta(days=i)
        content = _fetch_finra_file(check_date)
        
        if content:
            lines = content.strip().split('\n')
            
            for line in lines:
                if f"|{ticker}|" in line:
                    parsed = _parse_finra_line(line)
                    if parsed:
                        history.append(parsed)
                        break
        
        # Stop once we have enough trading days
        if len(history) >= days:
            break
    
    if not history:
        return {
            'success': False,
            'error': f'No historical data found for {ticker}',
            'ticker': ticker
        }
    
    # Calculate statistics
    short_ratios = [d['short_ratio'] for d in history]
    short_volumes = [d['short_volume'] for d in history]
    
    trend_analysis = _analyze_trend(short_ratios)
    
    return {
        'success': True,
        'ticker': ticker,
        'days_found': len(history),
        'data': history,
        'avg_short_ratio': round(mean(short_ratios), 2),
        'min_short_ratio': round(min(short_ratios), 2),
        'max_short_ratio': round(max(short_ratios), 2),
        'avg_short_volume': round(mean(short_volumes)),
        'trend': trend_analysis,
        'latest': history[0] if history else None
    }


def get_most_shorted(date: Optional[datetime] = None, limit: int = 50) -> Dict:
    """
    Get top most-shorted stocks by short volume ratio
    
    Args:
        date: Optional specific date (defaults to most recent)
        limit: Number of top stocks to return (default 50)
    
    Returns:
        Dict with top shorted stocks ranked by short ratio
        
    Example:
        >>> top_shorted = get_most_shorted(limit=20)
        >>> for stock in top_shorted['stocks'][:5]:
        ...     print(f"{stock['symbol']}: {stock['short_ratio']}%")
    """
    if date is None:
        dates_to_try = [datetime.now() - timedelta(days=i) for i in range(10)]
    else:
        dates_to_try = [date]
    
    for try_date in dates_to_try:
        content = _fetch_finra_file(try_date)
        
        if content:
            lines = content.strip().split('\n')
            stocks = []
            
            for line in lines[1:]:  # Skip header
                parsed = _parse_finra_line(line)
                if parsed and parsed['total_volume'] >= 100000:  # Min volume filter
                    stocks.append(parsed)
            
            # Sort by short ratio descending
            stocks.sort(key=lambda x: x['short_ratio'], reverse=True)
            
            return {
                'success': True,
                'date': try_date.strftime("%Y%m%d"),
                'total_stocks': len(stocks),
                'stocks': stocks[:limit],
                'avg_short_ratio': round(mean([s['short_ratio'] for s in stocks]), 2) if stocks else 0
            }
    
    return {
        'success': False,
        'error': 'No data available for recent dates'
    }


def get_short_volume_batch(tickers: List[str], date: Optional[datetime] = None) -> Dict:
    """
    Batch lookup for multiple tickers (efficient single file fetch)
    
    Args:
        tickers: List of ticker symbols
        date: Optional specific date (defaults to most recent)
    
    Returns:
        Dict with data for all tickers
        
    Example:
        >>> batch = get_short_volume_batch(['AAPL', 'TSLA', 'NVDA'])
        >>> for ticker, data in batch['results'].items():
        ...     print(f"{ticker}: {data['short_ratio']}%")
    """
    tickers = [t.upper().strip() for t in tickers]
    
    if date is None:
        dates_to_try = [datetime.now() - timedelta(days=i) for i in range(10)]
    else:
        dates_to_try = [date]
    
    for try_date in dates_to_try:
        content = _fetch_finra_file(try_date)
        
        if content:
            lines = content.strip().split('\n')
            results = {}
            
            for line in lines:
                for ticker in tickers:
                    if f"|{ticker}|" in line:
                        parsed = _parse_finra_line(line)
                        if parsed:
                            results[ticker] = {
                                'short_volume': parsed['short_volume'],
                                'total_volume': parsed['total_volume'],
                                'short_ratio': parsed['short_ratio'],
                                'date': parsed['date'],
                                'market': parsed['market']
                            }
            
            if results:
                return {
                    'success': True,
                    'date': try_date.strftime("%Y%m%d"),
                    'tickers_found': len(results),
                    'tickers_requested': len(tickers),
                    'results': results,
                    'missing': [t for t in tickers if t not in results]
                }
    
    return {
        'success': False,
        'error': 'No data found for any tickers',
        'tickers': tickers
    }


def calculate_short_squeeze_score(ticker: str, days: int = 30) -> Dict:
    """
    Calculate short squeeze potential score based on short volume trends
    
    Score factors:
    - Current short ratio (higher = more squeeze potential)
    - Short ratio trend (increasing = higher risk)
    - Short volume volatility (higher = more unstable)
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days for trend analysis (default 30)
    
    Returns:
        Dict with squeeze score (0-100) and component analysis
        
    Example:
        >>> score = calculate_short_squeeze_score('GME')
        >>> print(f"Squeeze score: {score['squeeze_score']}/100")
        >>> print(f"Risk level: {score['risk_level']}")
    """
    history = get_short_volume_history(ticker, days=days)
    
    if not history['success']:
        return {
            'success': False,
            'error': f'Cannot calculate score - no data for {ticker}',
            'ticker': ticker
        }
    
    current_ratio = history['latest']['short_ratio']
    avg_ratio = history['avg_short_ratio']
    trend = history['trend']
    
    # Score components (0-100 each)
    ratio_score = min(current_ratio * 2, 100)  # >50% ratio = max score
    trend_score = 0
    
    if trend['direction'] == 'increasing':
        trend_score = 70
    elif trend['direction'] == 'stable':
        trend_score = 50
    else:
        trend_score = 30
    
    # Volatility score (higher volatility = higher squeeze potential)
    volatility = history['max_short_ratio'] - history['min_short_ratio']
    volatility_score = min(volatility * 5, 100)
    
    # Weighted average
    squeeze_score = (ratio_score * 0.5 + trend_score * 0.3 + volatility_score * 0.2)
    
    # Classify risk
    if squeeze_score >= 70:
        risk_level = 'HIGH'
        interpretation = 'Strong short squeeze potential'
    elif squeeze_score >= 50:
        risk_level = 'MODERATE'
        interpretation = 'Moderate short pressure'
    elif squeeze_score >= 30:
        risk_level = 'LOW'
        interpretation = 'Low short squeeze risk'
    else:
        risk_level = 'MINIMAL'
        interpretation = 'Minimal short pressure'
    
    return {
        'success': True,
        'ticker': ticker,
        'squeeze_score': round(squeeze_score, 1),
        'risk_level': risk_level,
        'interpretation': interpretation,
        'components': {
            'ratio_score': round(ratio_score, 1),
            'trend_score': round(trend_score, 1),
            'volatility_score': round(volatility_score, 1)
        },
        'current_short_ratio': current_ratio,
        'avg_short_ratio': avg_ratio,
        'trend': trend['direction'],
        'days_analyzed': history['days_found']
    }


# ========== HELPER FUNCTIONS ==========

def _interpret_short_ratio(ratio: float) -> str:
    """Interpret short volume ratio"""
    if ratio >= 60:
        return 'Extremely high short volume (>60%)'
    elif ratio >= 50:
        return 'Very high short volume (50-60%)'
    elif ratio >= 40:
        return 'High short volume (40-50%)'
    elif ratio >= 30:
        return 'Moderate short volume (30-40%)'
    elif ratio >= 20:
        return 'Normal short volume (20-30%)'
    else:
        return 'Low short volume (<20%)'


def _analyze_trend(values: List[float]) -> Dict:
    """Analyze trend in short ratios"""
    if len(values) < 3:
        return {'direction': 'unknown', 'strength': 0}
    
    # Simple linear regression slope
    n = len(values)
    x = list(range(n))
    mean_x = mean(x)
    mean_y = mean(values)
    
    numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
    
    slope = numerator / denominator if denominator != 0 else 0
    
    # Classify trend
    if abs(slope) < 0.1:
        direction = 'stable'
    elif slope > 0:
        direction = 'increasing'
    else:
        direction = 'decreasing'
    
    return {
        'direction': direction,
        'strength': round(abs(slope), 3),
        'slope': round(slope, 3)
    }


if __name__ == "__main__":
    # CLI demonstration
    import json
    
    print("=" * 60)
    print("ShortVolume.com / FINRA Short Sale Volume Module")
    print("=" * 60)
    
    # Test get_short_volume
    print("\n1. Get short volume for AAPL:")
    aapl = get_short_volume('AAPL')
    print(json.dumps(aapl, indent=2))
    
    # Test batch lookup
    print("\n2. Batch lookup (AAPL, TSLA, NVDA):")
    batch = get_short_volume_batch(['AAPL', 'TSLA', 'NVDA'])
    print(json.dumps(batch, indent=2))
    
    # Test squeeze score
    print("\n3. Short squeeze score for TSLA:")
    squeeze = calculate_short_squeeze_score('TSLA', days=20)
    print(json.dumps(squeeze, indent=2))
    
    # Test most shorted
    print("\n4. Top 10 most shorted stocks:")
    top = get_most_shorted(limit=10)
    if top['success']:
        for i, stock in enumerate(top['stocks'][:10], 1):
            print(f"  {i}. {stock['symbol']}: {stock['short_ratio']}% "
                  f"({stock['short_volume']:,} / {stock['total_volume']:,})")

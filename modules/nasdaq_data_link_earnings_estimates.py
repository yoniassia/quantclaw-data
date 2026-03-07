#!/usr/bin/env python3
"""
Nasdaq Data Link Earnings Estimates

Provides earnings estimates, revisions, and surprises data from Nasdaq Data Link (formerly Quandl).
Uses the Zacks earnings datasets for comprehensive earnings intelligence.

Key datasets:
- ZACKS/EE: Earnings estimates by ticker
- ZACKS/ER: Earnings revisions
- ZACKS/ES: Earnings surprises
- ZACKS/FC: Forward consensus estimates

Source: https://data.nasdaq.com/docs
Category: Earnings & Fundamentals
Free tier: True - 10,000 rows per day with API key
Update frequency: Daily
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

# Load .env from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Nasdaq Data Link Configuration
NASDAQ_BASE_URL = "https://data.nasdaq.com/api/v3"
NASDAQ_API_KEY = os.environ.get("NASDAQ_DATA_LINK_API_KEY", "")

# Dataset codes
DATASETS = {
    'earnings_estimates': 'ZACKS/EE',
    'earnings_revisions': 'ZACKS/ER',
    'earnings_surprises': 'ZACKS/ES',
    'forward_consensus': 'ZACKS/FC'
}


def get_earnings_estimates(ticker: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch earnings estimates for a stock.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        
    Returns:
        dict: Earnings estimates data with metadata
        
    Example:
        >>> data = get_earnings_estimates('AAPL')
        >>> print(data['dataset']['data'][:2])
    """
    try:
        dataset_code = f"ZACKS/{ticker}"
        url = f"{NASDAQ_BASE_URL}/datasets/{dataset_code}.json"
        
        params = {}
        if NASDAQ_API_KEY:
            params['api_key'] = NASDAQ_API_KEY
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            'ticker': ticker,
            'dataset': data.get('dataset', {}),
            'estimates_count': len(data.get('dataset', {}).get('data', [])),
            'fetched_at': datetime.now().isoformat(),
            'success': True
        }
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {
                'ticker': ticker,
                'error': f'Dataset not found for ticker {ticker}',
                'success': False
            }
        return {
            'ticker': ticker,
            'error': f'HTTP error: {str(e)}',
            'success': False
        }
    except Exception as e:
        return {
            'ticker': ticker,
            'error': str(e),
            'success': False
        }


def get_earnings_revisions(ticker: str, limit: int = 100) -> Dict[str, Any]:
    """
    Fetch recent earnings estimate revisions for a stock.
    
    Args:
        ticker: Stock ticker symbol
        limit: Maximum number of revision records to return
        
    Returns:
        dict: Earnings revision history with change indicators
    """
    try:
        # Use the generic estimates endpoint but focus on revision dates
        dataset_code = f"ZACKS/{ticker}"
        url = f"{NASDAQ_BASE_URL}/datasets/{dataset_code}.json"
        
        params = {'rows': limit}
        if NASDAQ_API_KEY:
            params['api_key'] = NASDAQ_API_KEY
            
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        dataset = data.get('dataset', {})
        
        # Calculate revisions from sequential data points
        revisions = []
        raw_data = dataset.get('data', [])
        
        for i in range(len(raw_data) - 1):
            current = raw_data[i]
            previous = raw_data[i + 1]
            
            # Assuming data format: [date, eps_estimate, revenue_estimate, ...]
            if len(current) >= 2 and len(previous) >= 2:
                revision = {
                    'date': current[0],
                    'current_estimate': current[1] if len(current) > 1 else None,
                    'previous_estimate': previous[1] if len(previous) > 1 else None,
                    'change': (current[1] - previous[1]) if (len(current) > 1 and len(previous) > 1 and current[1] and previous[1]) else None
                }
                revisions.append(revision)
        
        return {
            'ticker': ticker,
            'revisions': revisions[:limit],
            'total_revisions': len(revisions),
            'column_names': dataset.get('column_names', []),
            'fetched_at': datetime.now().isoformat(),
            'success': True
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'error': str(e),
            'success': False
        }


def get_earnings_surprises(ticker: str, limit: int = 20) -> Dict[str, Any]:
    """
    Fetch historical earnings surprises (actual vs estimate).
    
    Args:
        ticker: Stock ticker symbol
        limit: Number of quarters to retrieve
        
    Returns:
        dict: Historical earnings surprises with beat/miss indicators
    """
    try:
        # Try to fetch from earnings surprises dataset
        dataset_code = f"ZACKS/ES_{ticker}"
        url = f"{NASDAQ_BASE_URL}/datasets/{dataset_code}.json"
        
        params = {'rows': limit}
        if NASDAQ_API_KEY:
            params['api_key'] = NASDAQ_API_KEY
            
        response = requests.get(url, params=params, timeout=10)
        
        # If ES dataset doesn't exist, fall back to main dataset
        if response.status_code == 404:
            dataset_code = f"ZACKS/{ticker}"
            url = f"{NASDAQ_BASE_URL}/datasets/{dataset_code}.json"
            response = requests.get(url, params=params, timeout=10)
            
        response.raise_for_status()
        
        data = response.json()
        dataset = data.get('dataset', {})
        
        surprises = []
        for row in dataset.get('data', [])[:limit]:
            if len(row) >= 3:
                surprise_data = {
                    'date': row[0],
                    'estimate': row[1] if len(row) > 1 else None,
                    'actual': row[2] if len(row) > 2 else None,
                    'surprise': (row[2] - row[1]) if (len(row) > 2 and row[1] and row[2]) else None,
                    'beat': (row[2] > row[1]) if (len(row) > 2 and row[1] and row[2]) else None
                }
                surprises.append(surprise_data)
        
        return {
            'ticker': ticker,
            'surprises': surprises,
            'total_quarters': len(surprises),
            'beats': sum(1 for s in surprises if s.get('beat')),
            'misses': sum(1 for s in surprises if s.get('beat') == False),
            'fetched_at': datetime.now().isoformat(),
            'success': True
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'error': str(e),
            'success': False
        }


def search_estimates(query: str, per_page: int = 10) -> List[Dict[str, Any]]:
    """
    Search available earnings estimate datasets.
    
    Args:
        query: Search term (ticker or company name)
        per_page: Results per page
        
    Returns:
        list: Available datasets matching the query
    """
    try:
        url = f"{NASDAQ_BASE_URL}/datasets.json"
        
        params = {
            'query': query,
            'database_code': 'ZACKS',
            'per_page': per_page
        }
        if NASDAQ_API_KEY:
            params['api_key'] = NASDAQ_API_KEY
            
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        datasets = data.get('datasets', [])
        
        results = []
        for ds in datasets:
            results.append({
                'dataset_code': ds.get('dataset_code'),
                'name': ds.get('name'),
                'description': ds.get('description'),
                'frequency': ds.get('frequency'),
                'newest_available_date': ds.get('newest_available_date'),
                'oldest_available_date': ds.get('oldest_available_date')
            })
        
        return results
        
    except Exception as e:
        return [{
            'error': str(e),
            'query': query,
            'success': False
        }]


def get_estimate_momentum(ticker: str, lookback_days: int = 90) -> Dict[str, Any]:
    """
    Calculate earnings estimate revision momentum.
    
    Analyzes trend in estimate revisions over specified period to determine
    whether analysts are getting more bullish or bearish.
    
    Args:
        ticker: Stock ticker symbol
        lookback_days: Days to analyze for momentum
        
    Returns:
        dict: Momentum metrics (upgrades, downgrades, net revision direction)
    """
    try:
        # Get recent revisions
        cutoff_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        estimates = get_earnings_estimates(ticker, start_date=cutoff_date)
        
        if not estimates.get('success'):
            return {
                'ticker': ticker,
                'error': estimates.get('error', 'Failed to fetch estimates'),
                'success': False
            }
        
        data_points = estimates.get('dataset', {}).get('data', [])
        
        if len(data_points) < 2:
            return {
                'ticker': ticker,
                'momentum': 'insufficient_data',
                'data_points': len(data_points),
                'success': True
            }
        
        # Calculate momentum metrics
        upgrades = 0
        downgrades = 0
        total_change = 0
        
        for i in range(len(data_points) - 1):
            current = data_points[i]
            previous = data_points[i + 1]
            
            if len(current) >= 2 and len(previous) >= 2:
                curr_val = current[1]
                prev_val = previous[1]
                
                if curr_val and prev_val:
                    change = curr_val - prev_val
                    total_change += change
                    
                    if change > 0:
                        upgrades += 1
                    elif change < 0:
                        downgrades += 1
        
        net_revisions = upgrades - downgrades
        momentum_score = total_change / len(data_points) if data_points else 0
        
        # Determine momentum direction
        if net_revisions > 2:
            direction = 'bullish'
        elif net_revisions < -2:
            direction = 'bearish'
        else:
            direction = 'neutral'
        
        return {
            'ticker': ticker,
            'lookback_days': lookback_days,
            'upgrades': upgrades,
            'downgrades': downgrades,
            'net_revisions': net_revisions,
            'momentum_score': round(momentum_score, 4),
            'direction': direction,
            'data_points_analyzed': len(data_points),
            'period_start': data_points[-1][0] if data_points else None,
            'period_end': data_points[0][0] if data_points else None,
            'fetched_at': datetime.now().isoformat(),
            'success': True
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'error': str(e),
            'success': False
        }


if __name__ == "__main__":
    # Test module functionality
    print("=" * 60)
    print("Nasdaq Data Link Earnings Estimates Module")
    print("=" * 60)
    
    test_ticker = "AAPL"
    
    print(f"\n1. Testing get_earnings_estimates('{test_ticker}')...")
    estimates = get_earnings_estimates(test_ticker)
    print(json.dumps({
        'ticker': estimates.get('ticker'),
        'success': estimates.get('success'),
        'estimates_count': estimates.get('estimates_count'),
        'error': estimates.get('error')
    }, indent=2))
    
    print(f"\n2. Testing get_earnings_revisions('{test_ticker}')...")
    revisions = get_earnings_revisions(test_ticker, limit=5)
    print(json.dumps({
        'ticker': revisions.get('ticker'),
        'success': revisions.get('success'),
        'total_revisions': revisions.get('total_revisions'),
        'error': revisions.get('error')
    }, indent=2))
    
    print(f"\n3. Testing get_earnings_surprises('{test_ticker}')...")
    surprises = get_earnings_surprises(test_ticker, limit=5)
    print(json.dumps({
        'ticker': surprises.get('ticker'),
        'success': surprises.get('success'),
        'beats': surprises.get('beats'),
        'misses': surprises.get('misses'),
        'error': surprises.get('error')
    }, indent=2))
    
    print(f"\n4. Testing search_estimates('{test_ticker}')...")
    search_results = search_estimates(test_ticker, per_page=3)
    print(f"Found {len(search_results)} datasets")
    
    print(f"\n5. Testing get_estimate_momentum('{test_ticker}')...")
    momentum = get_estimate_momentum(test_ticker)
    print(json.dumps({
        'ticker': momentum.get('ticker'),
        'success': momentum.get('success'),
        'direction': momentum.get('direction'),
        'net_revisions': momentum.get('net_revisions'),
        'error': momentum.get('error')
    }, indent=2))
    
    print("\n" + "=" * 60)
    print("Module test complete")
    print("=" * 60)

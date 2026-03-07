#!/usr/bin/env python3
"""
Nasdaq Data Link (Quandl) — Earnings Revisions API Module

Core Nasdaq Data Link integration for earnings estimate data including:
- EPS estimate revisions and momentum
- Earnings surprise history
- Consensus estimates (EPS/revenue)
- Revision breadth analysis
- Earnings yield and growth metrics

Source: https://data.nasdaq.com/docs/earnings-revisions-api
Category: Fundamental Analysis & Estimates
Free tier: True (requires NASDAQ_DATA_LINK_API_KEY env var)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Nasdaq Data Link API Configuration
NASDAQ_BASE_URL = "https://data.nasdaq.com/api/v3"
NASDAQ_API_KEY = os.environ.get("NASDAQ_DATA_LINK_API_KEY", "")


def get_earnings_revisions(symbol: str = 'MSFT') -> Dict:
    """
    Get EPS estimate revisions for a ticker.
    
    Args:
        symbol: Stock ticker symbol (default: 'MSFT')
    
    Returns:
        Dict with revision data including up/down estimates, dates, and analyst counts
    
    Example:
        >>> revisions = get_earnings_revisions('AAPL')
        >>> print(f"Symbol: {revisions.get('symbol', 'N/A')}")
    """
    try:
        # ZEST is the Zacks Earnings Surprises & Revisions database
        url = f"{NASDAQ_BASE_URL}/datasets/ZEST/{symbol}_REVISIONS"
        params = {
            'api_key': NASDAQ_API_KEY,
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'symbol': symbol,
                'dataset': data.get('dataset', {}),
                'revisions': data.get('dataset', {}).get('data', []),
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'error': f'API request failed with status {response.status_code}',
                'symbol': symbol,
                'message': response.text
            }
    
    except requests.exceptions.RequestException as e:
        return {
            'error': 'Request failed',
            'symbol': symbol,
            'details': str(e)
        }
    except Exception as e:
        return {
            'error': 'Unexpected error',
            'symbol': symbol,
            'details': str(e)
        }


def get_estimate_momentum(symbol: str = 'MSFT') -> Dict:
    """
    Get estimate revision momentum/trend for a ticker.
    
    Args:
        symbol: Stock ticker symbol (default: 'MSFT')
    
    Returns:
        Dict with momentum indicators, trend direction, and revision velocity
    
    Example:
        >>> momentum = get_estimate_momentum('AAPL')
        >>> print(f"Momentum: {momentum.get('trend', 'N/A')}")
    """
    try:
        # Use ZEST momentum indicators
        url = f"{NASDAQ_BASE_URL}/datasets/ZEST/{symbol}_MOMENTUM"
        params = {
            'api_key': NASDAQ_API_KEY,
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            dataset = data.get('dataset', {})
            raw_data = dataset.get('data', [])
            
            # Calculate momentum from recent revisions
            momentum_score = 'neutral'
            if raw_data and len(raw_data) > 0:
                recent_data = raw_data[0] if isinstance(raw_data[0], list) else []
                if len(recent_data) > 1:
                    # Simple momentum: positive if value > 0
                    value = recent_data[1] if len(recent_data) > 1 else 0
                    if isinstance(value, (int, float)):
                        momentum_score = 'positive' if value > 0 else 'negative' if value < 0 else 'neutral'
            
            return {
                'symbol': symbol,
                'momentum_score': momentum_score,
                'dataset': dataset,
                'data': raw_data[:10],  # Recent 10 data points
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'error': f'API request failed with status {response.status_code}',
                'symbol': symbol,
                'message': response.text
            }
    
    except requests.exceptions.RequestException as e:
        return {
            'error': 'Request failed',
            'symbol': symbol,
            'details': str(e)
        }
    except Exception as e:
        return {
            'error': 'Unexpected error',
            'symbol': symbol,
            'details': str(e)
        }


def get_earnings_surprise_history(symbol: str = 'MSFT', periods: int = 8) -> Dict:
    """
    Get historical earnings surprises for a ticker.
    
    Args:
        symbol: Stock ticker symbol (default: 'MSFT')
        periods: Number of quarters to retrieve (default: 8)
    
    Returns:
        Dict with earnings surprise history including actual vs. estimate
    
    Example:
        >>> surprises = get_earnings_surprise_history('AAPL', periods=4)
        >>> print(f"Last {len(surprises.get('data', []))} quarters")
    """
    try:
        # ZEST earnings surprises dataset
        url = f"{NASDAQ_BASE_URL}/datasets/ZEST/{symbol}_SURPRISE"
        params = {
            'api_key': NASDAQ_API_KEY,
            'rows': periods
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            dataset = data.get('dataset', {})
            
            return {
                'symbol': symbol,
                'periods': periods,
                'dataset': dataset,
                'surprise_history': dataset.get('data', [])[:periods],
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'error': f'API request failed with status {response.status_code}',
                'symbol': symbol,
                'message': response.text
            }
    
    except requests.exceptions.RequestException as e:
        return {
            'error': 'Request failed',
            'symbol': symbol,
            'details': str(e)
        }
    except Exception as e:
        return {
            'error': 'Unexpected error',
            'symbol': symbol,
            'details': str(e)
        }


def get_consensus_estimates(symbol: str = 'MSFT') -> Dict:
    """
    Get current consensus EPS and revenue estimates for a ticker.
    
    Args:
        symbol: Stock ticker symbol (default: 'MSFT')
    
    Returns:
        Dict with consensus estimates including mean, median, high, low analyst estimates
    
    Example:
        >>> consensus = get_consensus_estimates('AAPL')
        >>> print(f"Consensus EPS: {consensus.get('mean_eps', 'N/A')}")
    """
    try:
        # ZEST consensus estimates
        url = f"{NASDAQ_BASE_URL}/datasets/ZEST/{symbol}_CONSENSUS"
        params = {
            'api_key': NASDAQ_API_KEY,
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            dataset = data.get('dataset', {})
            raw_data = dataset.get('data', [])
            
            # Extract consensus metrics
            consensus_data = {}
            if raw_data and len(raw_data) > 0:
                latest = raw_data[0] if isinstance(raw_data[0], list) else []
                column_names = dataset.get('column_names', [])
                
                # Map columns to values
                for idx, col_name in enumerate(column_names):
                    if idx < len(latest):
                        consensus_data[col_name.lower().replace(' ', '_')] = latest[idx]
            
            return {
                'symbol': symbol,
                'consensus': consensus_data,
                'dataset': dataset,
                'raw_data': raw_data[:5],  # Latest 5 periods
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'error': f'API request failed with status {response.status_code}',
                'symbol': symbol,
                'message': response.text
            }
    
    except requests.exceptions.RequestException as e:
        return {
            'error': 'Request failed',
            'symbol': symbol,
            'details': str(e)
        }
    except Exception as e:
        return {
            'error': 'Unexpected error',
            'symbol': symbol,
            'details': str(e)
        }


def get_revision_breadth(symbol: str = 'MSFT') -> Dict:
    """
    Get up vs down revisions ratio (revision breadth) for a ticker.
    
    Args:
        symbol: Stock ticker symbol (default: 'MSFT')
    
    Returns:
        Dict with revision breadth metrics including up/down ratio and trend
    
    Example:
        >>> breadth = get_revision_breadth('AAPL')
        >>> print(f"Up/Down ratio: {breadth.get('ratio', 'N/A')}")
    """
    try:
        # ZEST revision breadth
        url = f"{NASDAQ_BASE_URL}/datasets/ZEST/{symbol}_BREADTH"
        params = {
            'api_key': NASDAQ_API_KEY,
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            dataset = data.get('dataset', {})
            raw_data = dataset.get('data', [])
            
            # Calculate breadth ratio
            breadth_metrics = {}
            if raw_data and len(raw_data) > 0:
                latest = raw_data[0] if isinstance(raw_data[0], list) else []
                
                # Assume structure: [date, up_revisions, down_revisions, ...]
                if len(latest) >= 3:
                    up = latest[1] if isinstance(latest[1], (int, float)) else 0
                    down = latest[2] if isinstance(latest[2], (int, float)) else 0
                    
                    breadth_metrics = {
                        'up_revisions': up,
                        'down_revisions': down,
                        'ratio': round(up / down, 2) if down > 0 else None,
                        'net_revisions': up - down,
                        'trend': 'bullish' if up > down else 'bearish' if down > up else 'neutral'
                    }
            
            return {
                'symbol': symbol,
                'breadth': breadth_metrics,
                'dataset': dataset,
                'raw_data': raw_data[:10],
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'error': f'API request failed with status {response.status_code}',
                'symbol': symbol,
                'message': response.text
            }
    
    except requests.exceptions.RequestException as e:
        return {
            'error': 'Request failed',
            'symbol': symbol,
            'details': str(e)
        }
    except Exception as e:
        return {
            'error': 'Unexpected error',
            'symbol': symbol,
            'details': str(e)
        }


# Module metadata
__all__ = [
    'get_earnings_revisions',
    'get_estimate_momentum',
    'get_earnings_surprise_history',
    'get_consensus_estimates',
    'get_revision_breadth'
]

__version__ = '1.0.0'
__author__ = 'QuantClaw Data NightBuilder'

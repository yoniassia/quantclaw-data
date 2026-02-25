#!/usr/bin/env python3
"""
Multi-Source Data Reconciliation — Phase 84

When multiple sources provide the same data (price, earnings, etc.):
1. Automatically compare and validate across sources
2. Flag discrepancies and inconsistencies
3. Use voting/confidence scoring to pick the best source
4. Track source reliability over time

Data sources:
- Yahoo Finance (yfinance) — free, real-time prices
- SEC EDGAR — official filings, most authoritative but delayed
- Financial Datasets API — paid but comprehensive
- CoinGecko — crypto prices (free tier)
- FRED — macro economic data (free)

Confidence scoring based on:
- Data freshness (newer = better)
- Source authority (official > aggregator)
- Historical accuracy (tracked over time)
- Consistency with other sources
- Update frequency
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import json
import os
from collections import defaultdict
import requests


# Source reliability scores (updated dynamically over time)
# Higher score = more reliable
SOURCE_RELIABILITY = {
    'sec_edgar': 95,  # Official government filings
    'financial_datasets': 85,  # Paid, curated data
    'yfinance': 75,  # Free, real-time but sometimes stale
    'coingecko': 70,  # Good for crypto
    'fred': 90,  # Official Federal Reserve data
    'manual': 100  # Human-verified data
}

# Freshness weights — how much to penalize old data
FRESHNESS_DECAY = {
    'price': timedelta(minutes=15),  # Price data stale after 15 min
    'earnings': timedelta(days=1),  # Earnings stale after 1 day
    'financials': timedelta(days=90),  # Quarterly data OK for 90 days
    'macro': timedelta(days=7)  # Macro data OK for 1 week
}

# Cache directory for reliability tracking
CACHE_DIR = os.path.expanduser("~/.financial-data-pipeline/reconciliation")
os.makedirs(CACHE_DIR, exist_ok=True)


def get_price_from_yfinance(ticker: str) -> Optional[Dict[str, Any]]:
    """Get current price from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period='1d')
        
        if hist.empty:
            return None
        
        return {
            'source': 'yfinance',
            'ticker': ticker,
            'price': float(hist['Close'].iloc[-1]),
            'timestamp': datetime.now(),
            'volume': int(hist['Volume'].iloc[-1]),
            'market_cap': info.get('marketCap', None),
            'currency': info.get('currency', 'USD')
        }
    except Exception as e:
        print(f"[yfinance] Error fetching {ticker}: {e}")
        return None


def get_price_from_financial_datasets(ticker: str, api_key: str = None) -> Optional[Dict[str, Any]]:
    """
    Get price from Financial Datasets API.
    API key should be in ~/.credentials/financial-datasets.json
    """
    if not api_key:
        creds_path = os.path.expanduser("~/.openclaw/workspace/.credentials/financial-datasets.json")
        if os.path.exists(creds_path):
            with open(creds_path, 'r') as f:
                creds = json.load(f)
                api_key = creds.get('api_key')
    
    if not api_key:
        return None
    
    try:
        url = f"https://api.financialdatasets.ai/prices/snapshot"
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
        params = {'ticker': ticker}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        return {
            'source': 'financial_datasets',
            'ticker': ticker,
            'price': float(data.get('price', 0)),
            'timestamp': datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat())),
            'volume': data.get('volume'),
            'market_cap': data.get('market_cap'),
            'currency': data.get('currency', 'USD')
        }
    except Exception as e:
        print(f"[financial_datasets] Error fetching {ticker}: {e}")
        return None


def get_crypto_price_from_coingecko(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get crypto price from CoinGecko (free API).
    
    Args:
        symbol: Crypto symbol (e.g., 'bitcoin', 'ethereum')
    """
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': symbol.lower(),
            'vs_currencies': 'usd',
            'include_market_cap': 'true',
            'include_24hr_vol': 'true',
            'include_last_updated_at': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if symbol.lower() not in data:
            return None
        
        coin_data = data[symbol.lower()]
        
        return {
            'source': 'coingecko',
            'ticker': symbol.upper(),
            'price': float(coin_data['usd']),
            'timestamp': datetime.fromtimestamp(coin_data['last_updated_at']),
            'volume': coin_data.get('usd_24h_vol'),
            'market_cap': coin_data.get('usd_market_cap'),
            'currency': 'USD'
        }
    except Exception as e:
        print(f"[coingecko] Error fetching {symbol}: {e}")
        return None


def calculate_confidence_score(
    data: Dict[str, Any],
    data_type: str = 'price',
    consensus_value: float = None
) -> float:
    """
    Calculate confidence score for a data point.
    
    Args:
        data: Data dict with 'source', 'timestamp', 'price', etc.
        data_type: Type of data ('price', 'earnings', 'financials', 'macro')
        consensus_value: Median value from all sources (for consistency check)
    
    Returns:
        Confidence score (0-100)
    """
    score = 0.0
    
    # 1. Base reliability score from source (40% weight)
    source = data.get('source', 'unknown')
    reliability = SOURCE_RELIABILITY.get(source, 50)
    score += reliability * 0.4
    
    # 2. Freshness score (30% weight)
    timestamp = data.get('timestamp', datetime.now())
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)
    
    age = datetime.now() - timestamp
    max_age = FRESHNESS_DECAY.get(data_type, timedelta(days=1))
    
    if age < max_age:
        freshness = 100 * (1 - (age.total_seconds() / max_age.total_seconds()))
    else:
        freshness = 0
    
    score += freshness * 0.3
    
    # 3. Consistency with consensus (30% weight)
    if consensus_value is not None and 'price' in data:
        value = data['price']
        if consensus_value > 0:
            deviation = abs(value - consensus_value) / consensus_value
            consistency = max(0, 100 * (1 - deviation * 10))  # 10% deviation = 0 score
        else:
            consistency = 50  # Can't judge consistency if consensus is 0
        
        score += consistency * 0.3
    else:
        # No consensus to compare — use average of other components
        score = score / 0.7
    
    return min(100, max(0, score))


def reconcile_prices(ticker: str, sources: List[str] = None) -> Dict[str, Any]:
    """
    Fetch price from multiple sources and reconcile.
    
    Args:
        ticker: Stock/crypto ticker symbol
        sources: List of sources to try (default: all available)
    
    Returns:
        Dict with reconciled price, confidence score, and source breakdown
    """
    if sources is None:
        sources = ['yfinance', 'financial_datasets']
    
    # Fetch from all sources
    results = []
    
    if 'yfinance' in sources:
        yf_data = get_price_from_yfinance(ticker)
        if yf_data:
            results.append(yf_data)
    
    if 'financial_datasets' in sources:
        fd_data = get_price_from_financial_datasets(ticker)
        if fd_data:
            results.append(fd_data)
    
    # For crypto, try CoinGecko
    if 'coingecko' in sources or (len(results) == 0 and ticker.lower() in ['bitcoin', 'ethereum', 'btc', 'eth']):
        # Map common crypto symbols
        crypto_map = {'btc': 'bitcoin', 'eth': 'ethereum'}
        symbol = crypto_map.get(ticker.lower(), ticker.lower())
        
        cg_data = get_crypto_price_from_coingecko(symbol)
        if cg_data:
            results.append(cg_data)
    
    if not results:
        return {
            'error': f'No data available for {ticker} from any source',
            'ticker': ticker,
            'sources_attempted': sources
        }
    
    # Calculate consensus (median price)
    prices = [r['price'] for r in results if 'price' in r]
    consensus_price = float(np.median(prices)) if prices else 0
    
    # Calculate confidence scores for each source
    for result in results:
        result['confidence'] = calculate_confidence_score(result, 'price', consensus_price)
    
    # Pick best source (highest confidence)
    best_source = max(results, key=lambda x: x.get('confidence', 0))
    
    # Flag discrepancies (>1% deviation from consensus)
    discrepancies = []
    for result in results:
        deviation = abs(result['price'] - consensus_price) / consensus_price if consensus_price > 0 else 0
        if deviation > 0.01:  # 1% threshold
            discrepancies.append({
                'source': result['source'],
                'price': result['price'],
                'deviation_pct': deviation * 100,
                'confidence': result['confidence']
            })
    
    return {
        'ticker': ticker,
        'reconciled_price': best_source['price'],
        'consensus_price': consensus_price,
        'best_source': best_source['source'],
        'confidence': best_source['confidence'],
        'timestamp': best_source['timestamp'].isoformat(),
        'all_sources': [
            {
                'source': r['source'],
                'price': r['price'],
                'confidence': r['confidence'],
                'timestamp': r['timestamp'].isoformat()
            }
            for r in results
        ],
        'discrepancies': discrepancies if discrepancies else None,
        'discrepancy_count': len(discrepancies),
        'sources_checked': len(results)
    }


def reconcile_financials(ticker: str, sources: List[str] = None) -> Dict[str, Any]:
    """
    Reconcile financial statement data from multiple sources.
    
    Args:
        ticker: Stock ticker
        sources: List of sources (default: ['yfinance', 'sec_edgar'])
    
    Returns:
        Reconciled financials with confidence scores
    """
    if sources is None:
        sources = ['yfinance', 'sec_edgar']
    
    results = []
    
    # Yahoo Finance
    if 'yfinance' in sources:
        try:
            stock = yf.Ticker(ticker)
            financials = stock.financials
            
            if not financials.empty:
                latest = financials.iloc[:, 0]  # Most recent quarter
                
                results.append({
                    'source': 'yfinance',
                    'revenue': float(latest.get('Total Revenue', 0)),
                    'net_income': float(latest.get('Net Income', 0)),
                    'total_assets': None,  # Not in income statement
                    'timestamp': datetime.now()
                })
        except Exception as e:
            print(f"[yfinance] Error fetching financials for {ticker}: {e}")
    
    # SEC EDGAR would go here (not implemented in this demo)
    # if 'sec_edgar' in sources:
    #     edgar_data = fetch_from_edgar(ticker)
    #     if edgar_data:
    #         results.append(edgar_data)
    
    if not results:
        return {
            'error': f'No financial data available for {ticker}',
            'ticker': ticker
        }
    
    # For now, just return the single source (would reconcile if we had multiple)
    return {
        'ticker': ticker,
        'reconciled_financials': results[0],
        'sources_checked': len(results)
    }


def track_source_accuracy(source: str, data_type: str, was_accurate: bool):
    """
    Track source accuracy over time to adjust reliability scores.
    
    Args:
        source: Source name (e.g., 'yfinance')
        data_type: Type of data (e.g., 'price')
        was_accurate: Whether the data was accurate
    """
    tracking_file = os.path.join(CACHE_DIR, 'source_accuracy.json')
    
    # Load existing tracking data
    if os.path.exists(tracking_file):
        with open(tracking_file, 'r') as f:
            tracking = json.load(f)
    else:
        tracking = {}
    
    key = f"{source}:{data_type}"
    
    if key not in tracking:
        tracking[key] = {
            'total': 0,
            'accurate': 0,
            'accuracy_rate': 0.0
        }
    
    tracking[key]['total'] += 1
    if was_accurate:
        tracking[key]['accurate'] += 1
    
    tracking[key]['accuracy_rate'] = tracking[key]['accurate'] / tracking[key]['total']
    
    # Save updated tracking
    with open(tracking_file, 'w') as f:
        json.dump(tracking, f, indent=2)


def get_source_reliability_report() -> Dict[str, Any]:
    """
    Get reliability report for all sources based on historical accuracy.
    
    Returns:
        Dict with accuracy stats for each source
    """
    tracking_file = os.path.join(CACHE_DIR, 'source_accuracy.json')
    
    if not os.path.exists(tracking_file):
        return {'error': 'No tracking data available yet'}
    
    with open(tracking_file, 'r') as f:
        tracking = json.load(f)
    
    # Format for readability
    report = {}
    for key, stats in tracking.items():
        source, data_type = key.split(':')
        
        if source not in report:
            report[source] = {}
        
        report[source][data_type] = {
            'accuracy_rate': f"{stats['accuracy_rate'] * 100:.2f}%",
            'total_checks': stats['total'],
            'accurate_count': stats['accurate']
        }
    
    return report


def compare_sources(ticker: str, data_type: str = 'price') -> Dict[str, Any]:
    """
    Compare all available sources for a ticker and show detailed breakdown.
    
    Args:
        ticker: Stock/crypto ticker
        data_type: Type of data to compare ('price', 'financials')
    
    Returns:
        Detailed comparison with recommendations
    """
    if data_type == 'price':
        reconciliation = reconcile_prices(ticker, sources=['yfinance', 'financial_datasets', 'coingecko'])
    elif data_type == 'financials':
        reconciliation = reconcile_financials(ticker)
    else:
        return {'error': f'Unsupported data type: {data_type}'}
    
    return {
        'ticker': ticker,
        'data_type': data_type,
        'comparison': reconciliation,
        'recommendation': f"Use {reconciliation.get('best_source', 'unknown')} for {ticker} {data_type} data",
        'confidence_level': 'HIGH' if reconciliation.get('confidence', 0) > 80 else 'MEDIUM' if reconciliation.get('confidence', 0) > 60 else 'LOW'
    }


def batch_reconcile(tickers: List[str], data_type: str = 'price') -> Dict[str, Any]:
    """
    Reconcile data for multiple tickers at once.
    
    Args:
        tickers: List of ticker symbols
        data_type: Type of data ('price', 'financials')
    
    Returns:
        Dict with reconciliation results for all tickers
    """
    results = {}
    
    for ticker in tickers:
        if data_type == 'price':
            results[ticker] = reconcile_prices(ticker)
        elif data_type == 'financials':
            results[ticker] = reconcile_financials(ticker)
    
    # Summary stats
    total = len(tickers)
    with_discrepancies = sum(1 for r in results.values() if r.get('discrepancy_count', 0) > 0)
    high_confidence = sum(1 for r in results.values() if r.get('confidence', 0) > 80)
    
    return {
        'results': results,
        'summary': {
            'total_tickers': total,
            'with_discrepancies': with_discrepancies,
            'high_confidence_count': high_confidence,
            'discrepancy_rate': f"{(with_discrepancies / total * 100):.1f}%",
            'high_confidence_rate': f"{(high_confidence / total * 100):.1f}%"
        }
    }


if __name__ == "__main__":
    # Example usage
    print("=== Multi-Source Price Reconciliation ===\n")
    
    # Test with AAPL
    result = reconcile_prices('AAPL')
    print(json.dumps(result, indent=2, default=str))
    
    print("\n=== Source Comparison ===\n")
    comparison = compare_sources('AAPL', 'price')
    print(json.dumps(comparison, indent=2, default=str))
    
    print("\n=== Batch Reconciliation ===\n")
    batch = batch_reconcile(['AAPL', 'MSFT', 'GOOGL'], 'price')
    print(json.dumps(batch['summary'], indent=2))

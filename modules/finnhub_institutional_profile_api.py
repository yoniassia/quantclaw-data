"""
Finnhub Insider Transactions API — Track Smart Money & Institutional Activity

Data Source: Finnhub.io (SEC Form 4 filings)
Update: Real-time (within hours of SEC filing)
History: 1+ years of insider activity
Free: Yes (60 calls/min, 250K/day with free API key)

Provides:
- Insider transactions (buys, sells, grants) by symbol
- Filing dates, transaction dates, share counts
- Transaction codes (P=purchase, S=sale, A=award, M=exercise, G=gift)
- Derivative vs direct ownership tracking
- Executive & board member activity

Usage:
- Track insider buying/selling sentiment
- Monitor executive compensation (stock grants)
- Identify potential insider trading signals
- Detect unusual accumulation or distribution

Transaction Codes:
- P = Purchase (bullish)
- S = Sale (bearish, but often routine)
- A = Award/Grant (compensation, neutral)
- M = Option Exercise (neutral-bullish)
- G = Gift (neutral, estate planning)
- F = Tax withholding (neutral)

Note: Institutional portfolio/13F data requires premium Finnhub subscription.
This module focuses on insider transactions (free tier).
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/finnhub")
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_URL = "https://finnhub.io/api/v1"
API_KEY = os.getenv("FINNHUB_API_KEY", "")

# Transaction code meanings
TRANSACTION_CODES = {
    'P': 'Purchase',
    'S': 'Sale',
    'A': 'Award/Grant',
    'M': 'Option Exercise',
    'G': 'Gift',
    'F': 'Tax Withholding',
    'C': 'Conversion',
    'D': 'Disposition',
    'I': 'Discretionary Transaction'
}

def _make_request(endpoint: str, params: Dict) -> Optional[Dict]:
    """
    Make authenticated request to Finnhub API with error handling.
    
    Args:
        endpoint: API endpoint path (e.g., '/stock/insider-transactions')
        params: Query parameters (excluding token)
        
    Returns:
        JSON response dict or None on error
    """
    if not API_KEY:
        raise ValueError("FINNHUB_API_KEY not found in environment. Get free key at https://finnhub.io")
    
    params['token'] = API_KEY
    url = f"{BASE_URL}{endpoint}"
    
    try:
        headers = {'User-Agent': 'QuantClaw/1.0'}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Finnhub returns {"error": "..."} on API errors
        if isinstance(data, dict) and 'error' in data:
            print(f"Finnhub API error: {data['error']}")
            return None
            
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {endpoint}: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON response from {endpoint}")
        return None


def get_insider_transactions(symbol: str, from_date: str = None, to_date: str = None, cache_hours: int = 24) -> Optional[Dict]:
    """
    Get insider trading transactions for a stock symbol.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA')
        from_date: Start date YYYY-MM-DD (default: 1 year ago)
        to_date: End date YYYY-MM-DD (default: today)
        cache_hours: Cache validity in hours (default 24)
        
    Returns:
        Dict with:
        - data: List of transactions with name, change, share, transactionCode, filingDate
        - symbol: Stock ticker
        
    Example:
        >>> txns = get_insider_transactions('AAPL')
        >>> recent_buys = [t for t in txns['data'] if t['transactionCode'] == 'P']
    """
    # Default date range: last 365 days
    if not to_date:
        to_date = datetime.now().strftime('%Y-%m-%d')
    if not from_date:
        from_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    cache_key = f"{symbol}_{from_date}_{to_date}"
    cache_file = os.path.join(CACHE_DIR, f"insider_{cache_key}.json")
    
    # Check cache
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(hours=cache_hours):
            with open(cache_file) as f:
                return json.load(f)
    
    # Fetch from API (Finnhub ignores date params on free tier, returns recent data)
    data = _make_request('/stock/insider-transactions', {'symbol': symbol.upper()})
    
    if data and isinstance(data, dict) and 'data' in data:
        # Add metadata
        data['_fetched'] = datetime.now().isoformat()
        data['_from_date'] = from_date
        data['_to_date'] = to_date
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        return data
    
    return None


def analyze_insider_sentiment(symbol: str, days: int = 90) -> Dict:
    """
    Analyze insider buying/selling sentiment over recent period.
    
    Args:
        symbol: Stock ticker
        days: Number of days to analyze (default 90)
        
    Returns:
        Dict with:
        - symbol: Ticker
        - total_transactions: Count of all transactions
        - purchases: Count and total shares purchased
        - sales: Count and total shares sold
        - net_insider_shares: Net change (purchases - sales)
        - sentiment: 'bullish', 'bearish', or 'neutral'
        - top_buyers: List of top 3 insider buyers
        - top_sellers: List of top 3 insider sellers
    """
    data = get_insider_transactions(symbol)
    
    if not data or 'data' not in data:
        return {
            'error': 'No insider transaction data available',
            'symbol': symbol
        }
    
    transactions = data['data']
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Filter to recent transactions
    recent = [
        t for t in transactions 
        if t.get('filingDate') and datetime.strptime(t['filingDate'][:10], '%Y-%m-%d') >= cutoff_date
    ]
    
    # Analyze by transaction type
    purchases = [t for t in recent if t.get('transactionCode') == 'P']
    sales = [t for t in recent if t.get('transactionCode') == 'S']
    
    total_purchased = sum(t.get('change', 0) for t in purchases if t.get('change', 0) > 0)
    total_sold = sum(abs(t.get('change', 0)) for t in sales if t.get('change', 0) < 0)
    
    # Aggregate by name for top buyers/sellers
    from collections import defaultdict
    buyer_totals = defaultdict(int)
    seller_totals = defaultdict(int)
    
    for t in purchases:
        if t.get('change', 0) > 0:
            buyer_totals[t.get('name', 'Unknown')] += t['change']
    
    for t in sales:
        if t.get('change', 0) < 0:
            seller_totals[t.get('name', 'Unknown')] += abs(t['change'])
    
    top_buyers = sorted(buyer_totals.items(), key=lambda x: x[1], reverse=True)[:3]
    top_sellers = sorted(seller_totals.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # Determine sentiment
    net_shares = total_purchased - total_sold
    if net_shares > 0 and total_purchased > total_sold * 2:
        sentiment = 'bullish'
    elif net_shares < 0 and total_sold > total_purchased * 2:
        sentiment = 'bearish'
    else:
        sentiment = 'neutral'
    
    return {
        'symbol': symbol.upper(),
        'period_days': days,
        'total_transactions': len(recent),
        'purchases': {
            'count': len(purchases),
            'total_shares': int(total_purchased)
        },
        'sales': {
            'count': len(sales),
            'total_shares': int(total_sold)
        },
        'net_insider_shares': int(net_shares),
        'sentiment': sentiment,
        'top_buyers': [{'name': name, 'shares': shares} for name, shares in top_buyers],
        'top_sellers': [{'name': name, 'shares': shares} for name, shares in top_sellers],
        '_fetched': data.get('_fetched')
    }


def get_recent_insider_activity(symbol: str, limit: int = 10) -> List[Dict]:
    """
    Get most recent insider transactions for a stock.
    
    Args:
        symbol: Stock ticker
        limit: Number of recent transactions to return (default 10)
        
    Returns:
        List of recent transactions, sorted by filing date descending
    """
    data = get_insider_transactions(symbol)
    
    if not data or 'data' not in data:
        return []
    
    transactions = data['data']
    
    # Sort by filing date descending
    sorted_txns = sorted(
        transactions,
        key=lambda t: t.get('filingDate', ''),
        reverse=True
    )
    
    # Enrich with human-readable transaction codes
    for txn in sorted_txns[:limit]:
        code = txn.get('transactionCode', '')
        txn['transactionType'] = TRANSACTION_CODES.get(code, 'Unknown')
    
    return sorted_txns[:limit]


def detect_unusual_insider_activity(symbol: str, threshold_shares: int = 10000) -> Dict:
    """
    Detect unusual insider buying patterns (large purchases).
    
    Args:
        symbol: Stock ticker
        threshold_shares: Minimum shares for "unusual" activity (default 10,000)
        
    Returns:
        Dict with unusual transactions (large purchases or sales)
    """
    data = get_insider_transactions(symbol)
    
    if not data or 'data' not in data:
        return {'error': 'No data available', 'symbol': symbol}
    
    transactions = data['data']
    
    # Find large purchases (positive change >= threshold)
    large_purchases = [
        t for t in transactions
        if t.get('transactionCode') == 'P' and t.get('change', 0) >= threshold_shares
    ]
    
    # Find large sales (negative change <= -threshold)
    large_sales = [
        t for t in transactions
        if t.get('transactionCode') == 'S' and t.get('change', 0) <= -threshold_shares
    ]
    
    return {
        'symbol': symbol.upper(),
        'threshold_shares': threshold_shares,
        'large_purchases': len(large_purchases),
        'large_sales': len(large_sales),
        'unusual_purchases': [
            {
                'name': t.get('name'),
                'shares': t.get('change'),
                'date': t.get('filingDate'),
                'price': t.get('transactionPrice', 0)
            }
            for t in sorted(large_purchases, key=lambda x: x.get('change', 0), reverse=True)[:5]
        ],
        'unusual_sales': [
            {
                'name': t.get('name'),
                'shares': abs(t.get('change', 0)),
                'date': t.get('filingDate'),
                'price': t.get('transactionPrice', 0)
            }
            for t in sorted(large_sales, key=lambda x: x.get('change', 0))[:5]
        ]
    }


def get_latest():
    """
    Get latest insider activity for demo/testing.
    Returns sentiment analysis for AAPL.
    """
    return analyze_insider_sentiment('AAPL', days=90)


# Convenience exports
fetch_data = get_insider_transactions


if __name__ == "__main__":
    # Test with AAPL insider activity
    print("=== Finnhub Insider Transactions API Module ===\n")
    
    # Test 1: Insider sentiment analysis
    print("1. AAPL Insider Sentiment (90 days)")
    sentiment = analyze_insider_sentiment('AAPL', days=90)
    print(json.dumps(sentiment, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Recent insider activity
    print("2. Recent AAPL Insider Transactions (Last 5)")
    recent = get_recent_insider_activity('AAPL', limit=5)
    if recent:
        for i, txn in enumerate(recent, 1):
            change_str = f"+{txn.get('change', 0)}" if txn.get('change', 0) > 0 else str(txn.get('change', 0))
            print(f"{i}. {txn.get('name', 'Unknown')} | {txn.get('transactionType', 'Unknown')} | {change_str} shares | {txn.get('filingDate', 'N/A')}")
    else:
        print("No recent transactions found")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Unusual activity detection
    print("3. Unusual AAPL Insider Activity (>10K shares)")
    unusual = detect_unusual_insider_activity('AAPL', threshold_shares=10000)
    print(f"Large Purchases: {unusual.get('large_purchases', 0)}")
    print(f"Large Sales: {unusual.get('large_sales', 0)}")
    
    if unusual.get('unusual_purchases'):
        print("\nTop Unusual Purchases:")
        for p in unusual['unusual_purchases'][:3]:
            print(f"  - {p['name']}: {p['shares']:,} shares on {p['date']}")

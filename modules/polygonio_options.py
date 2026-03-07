#!/usr/bin/env python3
"""
Polygon.io Options Module — QuantClaw Data
Comprehensive options data including chains, snapshots, aggregates, trades, and quotes for US markets.

Data includes:
- Options chain: Full chain of calls/puts with strikes, expirations
- Snapshots: Real-time snapshot of all options for underlying
- Aggregates: OHLCV bars for specific options contracts
- Trades: Recent trade data for options contracts
- Quotes: Latest bid/ask quotes for options contracts

Usage:
  python modules/polygonio_options.py --ticker AAPL
  python modules/polygonio_options.py --ticker SPY --json

Data source: https://polygon.io/docs/options/getting-started
API Key: Set POLYGON_API_KEY environment variable
Free tier: 5 API calls/minute, 1000 messages/day
"""

import requests
import argparse
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class PolygonOptions:
    """Polygon.io Options API client for comprehensive options data"""
    
    BASE_URL = "https://api.polygon.io"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Polygon.io Options client.
        
        Args:
            api_key: Polygon.io API key. If None, reads from POLYGON_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get('POLYGON_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantClaw/1.0'
        })
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make authenticated request to Polygon.io API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            API response as dict, or dict with 'error' key on failure
        """
        if not self.api_key:
            return {
                'error': 'API key not found',
                'message': 'Set POLYGON_API_KEY environment variable or pass api_key to constructor',
                'status': 'missing_credentials'
            }
        
        if params is None:
            params = {}
        
        params['apiKey'] = self.api_key
        
        try:
            url = f"{self.BASE_URL}{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            
            # Handle rate limiting
            if response.status_code == 429:
                return {
                    'error': 'Rate limit exceeded',
                    'message': 'Free tier: 5 calls/minute. Wait and retry.',
                    'status': 'rate_limited'
                }
            
            response.raise_for_status()
            data = response.json()
            
            # Check for API-level errors
            if data.get('status') == 'ERROR':
                return {
                    'error': 'API error',
                    'message': data.get('error', 'Unknown API error'),
                    'status': 'api_error'
                }
            
            return data
            
        except requests.RequestException as e:
            return {
                'error': 'HTTP error',
                'message': str(e),
                'status': 'http_error'
            }
        except json.JSONDecodeError as e:
            return {
                'error': 'Invalid JSON response',
                'message': str(e),
                'status': 'json_error'
            }
        except Exception as e:
            return {
                'error': 'Unexpected error',
                'message': str(e),
                'status': 'unknown_error'
            }
    
    def get_options_chain(self, ticker: str, expiration_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get full options chain for a ticker.
        
        Args:
            ticker: Underlying stock ticker (e.g., 'AAPL')
            expiration_date: Optional expiration date filter (YYYY-MM-DD)
            
        Returns:
            Dict with:
            - ticker: Underlying ticker
            - results: List of options contracts
            - count: Number of contracts
            - timestamp: Query timestamp
        """
        ticker = ticker.upper().strip()
        
        params = {
            'underlying_ticker': ticker,
            'limit': 1000
        }
        
        if expiration_date:
            params['expiration_date'] = expiration_date
        
        endpoint = "/v3/reference/options/contracts"
        data = self._make_request(endpoint, params)
        
        if 'error' in data:
            data['ticker'] = ticker
            return data
        
        return {
            'ticker': ticker,
            'results': data.get('results', []),
            'count': len(data.get('results', [])),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_options_snapshot(self, ticker: str) -> Dict[str, Any]:
        """
        Get real-time snapshot of all options for an underlying ticker.
        
        Args:
            ticker: Underlying stock ticker (e.g., 'AAPL')
            
        Returns:
            Dict with:
            - ticker: Underlying ticker
            - results: List of option snapshots with greeks, bid/ask, volume
            - count: Number of options
            - timestamp: Query timestamp
        """
        ticker = ticker.upper().strip()
        
        endpoint = f"/v3/snapshot/options/{ticker}"
        data = self._make_request(endpoint)
        
        if 'error' in data:
            data['ticker'] = ticker
            return data
        
        return {
            'ticker': ticker,
            'results': data.get('results', []),
            'count': len(data.get('results', [])),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_options_aggregates(
        self, 
        options_ticker: str,
        from_date: str,
        to_date: str,
        timespan: str = 'day',
        multiplier: int = 1
    ) -> Dict[str, Any]:
        """
        Get OHLCV aggregate bars for a specific options contract.
        
        Args:
            options_ticker: Options contract ticker (e.g., 'O:AAPL250117C00150000')
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            timespan: Bar size ('minute', 'hour', 'day', 'week', 'month', 'quarter', 'year')
            multiplier: Size of timespan multiplier (e.g., 5 for 5-minute bars)
            
        Returns:
            Dict with:
            - ticker: Options contract ticker
            - results: List of OHLCV bars
            - count: Number of bars
            - timespan: Bar timespan
            - timestamp: Query timestamp
        """
        options_ticker = options_ticker.upper().strip()
        
        endpoint = f"/v2/aggs/ticker/{options_ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        data = self._make_request(endpoint)
        
        if 'error' in data:
            data['ticker'] = options_ticker
            return data
        
        return {
            'ticker': options_ticker,
            'results': data.get('results', []),
            'count': data.get('resultsCount', 0),
            'timespan': timespan,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_options_trades(
        self, 
        options_ticker: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get recent trade data for a specific options contract.
        
        Args:
            options_ticker: Options contract ticker (e.g., 'O:AAPL250117C00150000')
            limit: Maximum number of trades to return (1-50000)
            
        Returns:
            Dict with:
            - ticker: Options contract ticker
            - results: List of trades with price, size, timestamp
            - count: Number of trades
            - timestamp: Query timestamp
        """
        options_ticker = options_ticker.upper().strip()
        
        endpoint = f"/v3/trades/{options_ticker}"
        params = {'limit': min(limit, 50000)}
        
        data = self._make_request(endpoint, params)
        
        if 'error' in data:
            data['ticker'] = options_ticker
            return data
        
        return {
            'ticker': options_ticker,
            'results': data.get('results', []),
            'count': len(data.get('results', [])),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_options_quotes(
        self, 
        options_ticker: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get latest bid/ask quotes for a specific options contract.
        
        Args:
            options_ticker: Options contract ticker (e.g., 'O:AAPL250117C00150000')
            limit: Maximum number of quotes to return (1-50000)
            
        Returns:
            Dict with:
            - ticker: Options contract ticker
            - results: List of quotes with bid/ask prices and sizes
            - count: Number of quotes
            - timestamp: Query timestamp
        """
        options_ticker = options_ticker.upper().strip()
        
        endpoint = f"/v3/quotes/{options_ticker}"
        params = {'limit': min(limit, 50000)}
        
        data = self._make_request(endpoint, params)
        
        if 'error' in data:
            data['ticker'] = options_ticker
            return data
        
        return {
            'ticker': options_ticker,
            'results': data.get('results', []),
            'count': len(data.get('results', [])),
            'timestamp': datetime.utcnow().isoformat()
        }

def main():
    parser = argparse.ArgumentParser(
        description='Polygon.io Options — Comprehensive Options Data'
    )
    parser.add_argument('--ticker', type=str, required=True,
                       help='Stock ticker symbol')
    parser.add_argument('--json', action='store_true',
                       help='Output raw JSON')
    
    args = parser.parse_args()
    
    client = PolygonOptions()
    
    # Get options chain
    chain = client.get_options_chain(args.ticker)
    
    if args.json:
        print(json.dumps(chain, indent=2))
        return
    
    if 'error' in chain:
        print(f"❌ Error: {chain['error']}")
        print(f"   {chain['message']}")
        sys.exit(1)
    
    # Pretty print
    print(f"\n{'='*60}")
    print(f"📊 {chain['ticker']} — Polygon.io Options Chain")
    print(f"{'='*60}\n")
    
    print(f"Total contracts: {chain['count']}")
    
    if chain['count'] > 0:
        print(f"\nFirst 5 contracts:")
        for i, contract in enumerate(chain['results'][:5]):
            print(f"\n{i+1}. {contract.get('ticker', 'N/A')}")
            print(f"   Type: {contract.get('contract_type', 'N/A')}")
            print(f"   Strike: ${contract.get('strike_price', 0):.2f}")
            print(f"   Expiration: {contract.get('expiration_date', 'N/A')}")
    
    print(f"\nLast updated: {chain['timestamp']}")
    print()

if __name__ == '__main__':
    main()

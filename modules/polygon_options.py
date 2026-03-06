#!/usr/bin/env python3
"""
Polygon.io Options API Module
Real-time and historical options data for US equities including chains, snapshots, and Greeks.

Data includes:
- Options snapshots (bid/ask, volume, Greeks)
- Options chains (all strikes/expiries for underlying)
- Historical options prices and volume
- Implied volatility and Greeks (delta, gamma, theta, vega)

Free tier: 5 API calls per minute, basic endpoints
Source: https://polygon.io/docs/options/getting-started
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class PolygonOptions:
    """Polygon.io Options Data API Client"""
    
    BASE_URL = "https://api.polygon.io"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Polygon Options client.
        
        Args:
            api_key: Polygon.io API key (optional for demo, required for real use)
        """
        self.api_key = api_key or "demo"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantClaw-Data/1.0'
        })
    
    def get_options_snapshot(self, underlying_ticker: str) -> Dict[str, Any]:
        """
        Get snapshot of all options for an underlying ticker.
        
        Returns current bid/ask, volume, Greeks for all active options.
        
        Args:
            underlying_ticker: Stock ticker (e.g., 'AAPL')
            
        Returns:
            Dict with options snapshot data including contracts, greeks, prices
        """
        ticker = underlying_ticker.upper().strip()
        
        try:
            url = f"{self.BASE_URL}/v3/snapshot/options/{ticker}"
            params = {'apiKey': self.api_key}
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'ERROR':
                return {
                    'error': data.get('error', 'Unknown error'),
                    'ticker': ticker,
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            results = data.get('results', [])
            
            return {
                'ticker': ticker,
                'count': len(results),
                'options': results,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'error': f'Request failed: {str(e)}',
                'ticker': ticker,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'error': f'Error: {str(e)}',
                'ticker': ticker,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_options_chain(self, underlying_ticker: str, expiration_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get full options chain for a ticker.
        
        Args:
            underlying_ticker: Stock ticker (e.g., 'TSLA')
            expiration_date: Optional expiration date filter (YYYY-MM-DD)
            
        Returns:
            Dict with calls and puts data
        """
        ticker = underlying_ticker.upper().strip()
        
        try:
            # Use snapshot endpoint as proxy for chain data
            snapshot_data = self.get_options_snapshot(ticker)
            
            if 'error' in snapshot_data:
                return snapshot_data
            
            options = snapshot_data.get('options', [])
            
            # Filter by expiration if provided
            if expiration_date:
                options = [opt for opt in options if expiration_date in opt.get('details', {}).get('expiration_date', '')]
            
            # Separate calls and puts
            calls = [opt for opt in options if opt.get('details', {}).get('contract_type') == 'call']
            puts = [opt for opt in options if opt.get('details', {}).get('contract_type') == 'put']
            
            return {
                'ticker': ticker,
                'expiration_date': expiration_date,
                'calls': calls,
                'puts': puts,
                'call_count': len(calls),
                'put_count': len(puts),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'error': f'Error: {str(e)}',
                'ticker': ticker,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_option_contract(self, contract_symbol: str) -> Dict[str, Any]:
        """
        Get specific option contract details.
        
        Args:
            contract_symbol: Full option symbol (e.g., 'O:AAPL241018C00250000')
            
        Returns:
            Dict with contract details, Greeks, prices
        """
        try:
            url = f"{self.BASE_URL}/v3/snapshot/options/{contract_symbol}"
            params = {'apiKey': self.api_key}
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'ERROR':
                return {
                    'error': data.get('error', 'Unknown error'),
                    'contract': contract_symbol,
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            result = data.get('results', {})
            
            return {
                'contract': contract_symbol,
                'details': result.get('details', {}),
                'greeks': result.get('greeks', {}),
                'last_quote': result.get('last_quote', {}),
                'last_trade': result.get('last_trade', {}),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'error': f'Request failed: {str(e)}',
                'contract': contract_symbol,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'error': f'Error: {str(e)}',
                'contract': contract_symbol,
                'timestamp': datetime.utcnow().isoformat()
            }


def get_options_snapshot(ticker: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to get options snapshot.
    
    Args:
        ticker: Stock ticker
        api_key: Optional Polygon.io API key
        
    Returns:
        Options snapshot data
    """
    client = PolygonOptions(api_key)
    return client.get_options_snapshot(ticker)


def get_options_chain(ticker: str, expiration: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to get options chain.
    
    Args:
        ticker: Stock ticker
        expiration: Optional expiration date (YYYY-MM-DD)
        api_key: Optional Polygon.io API key
        
    Returns:
        Options chain with calls and puts
    """
    client = PolygonOptions(api_key)
    return client.get_options_chain(ticker, expiration)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Polygon.io Options Data")
    parser.add_argument('--ticker', type=str, default='AAPL', help='Stock ticker')
    parser.add_argument('--api-key', type=str, help='Polygon.io API key')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    
    args = parser.parse_args()
    
    client = PolygonOptions(args.api_key)
    data = client.get_options_snapshot(args.ticker)
    
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(f"Polygon.io Options for {args.ticker}")
        print(f"Count: {data.get('count', 0)}")
        if 'error' in data:
            print(f"Error: {data['error']}")
        else:
            print(f"Retrieved {len(data.get('options', []))} options contracts")

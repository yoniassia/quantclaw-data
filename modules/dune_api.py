#!/usr/bin/env python3
"""
Dune Analytics API — On-Chain Data Queries
Query blockchain data via SQL-like queries covering Ethereum and other EVM chains.

Features:
- Execute custom Dune queries with parameters
- Poll for query execution status and results
- Get cached results without re-executing
- Pre-built helpers for common DeFi queries (DEX volume, top tokens, whale transactions)

Data source: https://api.dune.com/api/v1/
Free tier: 1,000 query units/month, 10 queries/minute
"""

import os
import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

class DuneAPI:
    """
    Dune Analytics API client for blockchain data queries.
    
    Requires DUNE_API_KEY environment variable.
    """
    
    BASE_URL = "https://api.dune.com/api/v1"
    
    # Popular community query IDs for common use cases
    POPULAR_QUERIES = {
        'dex_volume_ethereum': 3238619,  # DEX trading volume on Ethereum
        'top_tokens_uniswap': 3671913,   # Top tokens by volume on Uniswap
        'whale_transfers': 3287471,      # Large ETH transfers
        'gas_tracker': 3236491,          # Gas prices over time
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Dune API client.
        
        Args:
            api_key: Dune API key (defaults to DUNE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('DUNE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "DUNE_API_KEY not found. Get one at https://dune.com/settings/api"
            )
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-Dune-API-Key': self.api_key,
            'Content-Type': 'application/json'
        })
    
    def execute_query(self, query_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a saved Dune query.
        
        Args:
            query_id: The Dune query ID
            params: Optional query parameters as key-value dict
        
        Returns:
            Dict with execution_id and state, or error
        """
        try:
            url = f"{self.BASE_URL}/query/{query_id}/execute"
            
            payload = {}
            if params:
                # Convert params to Dune format
                payload['query_parameters'] = params
            
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'execution_id': data.get('execution_id'),
                'state': data.get('state', 'QUERY_STATE_PENDING'),
                'query_id': query_id,
                'submitted_at': datetime.utcnow().isoformat(),
                'success': True
            }
            
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                return {'error': 'Invalid API key', 'success': False}
            elif e.response.status_code == 429:
                return {'error': 'Rate limit exceeded (10/min)', 'success': False}
            else:
                return {'error': f'HTTP {e.response.status_code}: {str(e)}', 'success': False}
        except Exception as e:
            return {'error': f'Execution error: {str(e)}', 'success': False}
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get the status of a query execution.
        
        Args:
            execution_id: The execution ID from execute_query
        
        Returns:
            Dict with state and metadata
        """
        try:
            url = f"{self.BASE_URL}/execution/{execution_id}/status"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'execution_id': execution_id,
                'state': data.get('state', 'UNKNOWN'),
                'query_id': data.get('query_id'),
                'is_execution_finished': data.get('is_execution_finished', False),
                'success': True
            }
            
        except requests.HTTPError as e:
            return {'error': f'HTTP {e.response.status_code}: {str(e)}', 'success': False}
        except Exception as e:
            return {'error': f'Status check error: {str(e)}', 'success': False}
    
    def get_query_results(self, execution_id: str, poll: bool = True, max_wait: int = 300) -> Dict[str, Any]:
        """
        Get results from a query execution. Optionally polls until complete.
        
        Args:
            execution_id: The execution ID from execute_query
            poll: Whether to poll until execution completes (default True)
            max_wait: Maximum seconds to wait if polling (default 300)
        
        Returns:
            Dict with rows, metadata, or error
        """
        start_time = time.time()
        
        while True:
            try:
                # Check status first
                status = self.get_execution_status(execution_id)
                
                if not status.get('success'):
                    return status
                
                state = status.get('state', '')
                
                # If failed, return error
                if 'FAILED' in state or 'CANCELLED' in state:
                    return {'error': f'Query execution {state}', 'success': False}
                
                # If complete, fetch results
                if status.get('is_execution_finished'):
                    url = f"{self.BASE_URL}/execution/{execution_id}/results"
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    return {
                        'execution_id': execution_id,
                        'query_id': status.get('query_id'),
                        'rows': data.get('result', {}).get('rows', []),
                        'metadata': data.get('result', {}).get('metadata', {}),
                        'row_count': len(data.get('result', {}).get('rows', [])),
                        'fetched_at': datetime.utcnow().isoformat(),
                        'success': True
                    }
                
                # If not polling, return status
                if not poll:
                    return {
                        'state': state,
                        'is_complete': False,
                        'message': 'Query still executing',
                        'success': False
                    }
                
                # Check timeout
                if time.time() - start_time > max_wait:
                    return {
                        'error': f'Query timeout after {max_wait}s',
                        'state': state,
                        'success': False
                    }
                
                # Wait before next poll
                time.sleep(2)
                
            except requests.HTTPError as e:
                return {'error': f'HTTP {e.response.status_code}: {str(e)}', 'success': False}
            except Exception as e:
                return {'error': f'Results fetch error: {str(e)}', 'success': False}
    
    def get_latest_results(self, query_id: int, limit: int = 1000) -> Dict[str, Any]:
        """
        Get cached results from the latest query execution without re-running.
        
        Args:
            query_id: The Dune query ID
            limit: Max rows to return (default 1000)
        
        Returns:
            Dict with rows and metadata, or error
        """
        try:
            url = f"{self.BASE_URL}/query/{query_id}/results"
            params = {'limit': limit}
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'query_id': query_id,
                'rows': data.get('result', {}).get('rows', []),
                'metadata': data.get('result', {}).get('metadata', {}),
                'row_count': len(data.get('result', {}).get('rows', [])),
                'is_cached': True,
                'fetched_at': datetime.utcnow().isoformat(),
                'success': True
            }
            
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return {'error': 'Query not found or no results available', 'success': False}
            else:
                return {'error': f'HTTP {e.response.status_code}: {str(e)}', 'success': False}
        except Exception as e:
            return {'error': f'Fetch error: {str(e)}', 'success': False}
    
    def get_popular_queries(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List popular community queries.
        
        Args:
            category: Optional filter by category
        
        Returns:
            List of dicts with query info
        """
        queries = []
        
        for name, query_id in self.POPULAR_QUERIES.items():
            if category and category.lower() not in name.lower():
                continue
            
            queries.append({
                'name': name,
                'query_id': query_id,
                'url': f'https://dune.com/queries/{query_id}'
            })
        
        return queries
    
    # ==================== Pre-built Query Helpers ====================
    
    def get_dex_volume(self, chain: str = "ethereum", days: int = 7) -> Dict[str, Any]:
        """
        Get DEX trading volume for a chain over N days.
        
        Args:
            chain: Blockchain name (ethereum, polygon, arbitrum, etc.)
            days: Number of days to look back
        
        Returns:
            Dict with volume data or error
        """
        # Use popular DEX volume query
        query_id = self.POPULAR_QUERIES.get('dex_volume_ethereum')
        
        if not query_id:
            return {'error': 'DEX volume query not configured', 'success': False}
        
        # Execute with parameters
        execution = self.execute_query(query_id, {
            'blockchain': chain,
            'days': days
        })
        
        if not execution.get('success'):
            return execution
        
        # Get results
        results = self.get_query_results(execution['execution_id'])
        
        if results.get('success'):
            # Add context
            results['chain'] = chain
            results['days'] = days
        
        return results
    
    def get_top_tokens_by_volume(self, chain: str = "ethereum", limit: int = 20) -> Dict[str, Any]:
        """
        Get top tokens by trading volume on a chain.
        
        Args:
            chain: Blockchain name
            limit: Number of top tokens to return
        
        Returns:
            Dict with token volume data or error
        """
        # Use popular top tokens query
        query_id = self.POPULAR_QUERIES.get('top_tokens_uniswap')
        
        if not query_id:
            return {'error': 'Top tokens query not configured', 'success': False}
        
        execution = self.execute_query(query_id, {
            'blockchain': chain,
            'limit': limit
        })
        
        if not execution.get('success'):
            return execution
        
        results = self.get_query_results(execution['execution_id'])
        
        if results.get('success'):
            results['chain'] = chain
            results['limit'] = limit
            
            # Sort by volume if available
            if results.get('rows'):
                results['rows'] = results['rows'][:limit]
        
        return results
    
    def get_whale_transactions(self, min_value_usd: float = 1000000, hours: int = 24) -> Dict[str, Any]:
        """
        Get large (whale) transactions above a USD threshold.
        
        Args:
            min_value_usd: Minimum transaction value in USD
            hours: Hours to look back
        
        Returns:
            Dict with whale transaction data or error
        """
        query_id = self.POPULAR_QUERIES.get('whale_transfers')
        
        if not query_id:
            return {'error': 'Whale transactions query not configured', 'success': False}
        
        execution = self.execute_query(query_id, {
            'min_value_usd': min_value_usd,
            'hours': hours
        })
        
        if not execution.get('success'):
            return execution
        
        results = self.get_query_results(execution['execution_id'])
        
        if results.get('success'):
            results['min_value_usd'] = min_value_usd
            results['hours'] = hours
        
        return results

def main():
    """CLI interface for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Dune Analytics API Client')
    parser.add_argument('--query-id', type=int, help='Query ID to execute')
    parser.add_argument('--latest', type=int, help='Get latest results for query ID')
    parser.add_argument('--popular', action='store_true', help='List popular queries')
    parser.add_argument('--dex-volume', action='store_true', help='Get DEX volume')
    parser.add_argument('--chain', default='ethereum', help='Blockchain (default: ethereum)')
    parser.add_argument('--json', action='store_true', help='Output raw JSON')
    
    args = parser.parse_args()
    
    try:
        dune = DuneAPI()
        
        if args.popular:
            queries = dune.get_popular_queries()
            print(json.dumps(queries, indent=2))
        
        elif args.latest:
            results = dune.get_latest_results(args.latest)
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                if results.get('success'):
                    print(f"✅ Got {results['row_count']} rows from query {results['query_id']}")
                    if results['rows']:
                        print(f"Sample: {results['rows'][0]}")
                else:
                    print(f"❌ {results.get('error')}")
        
        elif args.dex_volume:
            results = dune.get_dex_volume(chain=args.chain)
            print(json.dumps(results, indent=2))
        
        elif args.query_id:
            execution = dune.execute_query(args.query_id)
            if execution.get('success'):
                print(f"✅ Execution ID: {execution['execution_id']}")
                results = dune.get_query_results(execution['execution_id'])
                print(json.dumps(results, indent=2))
            else:
                print(f"❌ {execution.get('error')}")
        
        else:
            parser.print_help()
    
    except ValueError as e:
        print(f"❌ Config error: {e}")
        print("Set DUNE_API_KEY environment variable")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()

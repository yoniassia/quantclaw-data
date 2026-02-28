#!/usr/bin/env python3
"""
OpenFIGI Identifier Mapping
Bloomberg-backed ticker→FIGI/ISIN/CUSIP mapping service
10 requests/min limit, no API key required
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from pathlib import Path

# Cache configuration
CACHE_DIR = Path.home() / ".cache" / "quantclaw" / "openfigi"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DURATION = timedelta(days=7)  # FIGI mappings are stable
RATE_LIMIT_DELAY = 6.0  # 10 req/min = 1 req per 6 seconds

# API configuration
BASE_URL = "https://api.openfigi.com/v3/mapping"
BATCH_SIZE = 100  # Max jobs per request


class OpenFIGIClient:
    """Client for OpenFIGI API with caching and rate limiting"""
    
    def __init__(self):
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Enforce rate limiting (10 req/min)"""
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def _get_cache_path(self, identifier: str, id_type: str) -> Path:
        """Generate cache file path for identifier"""
        safe_name = f"{id_type}_{identifier}".replace("/", "_").replace(":", "_")
        return CACHE_DIR / f"{safe_name}.json"
    
    def _load_from_cache(self, identifier: str, id_type: str) -> Optional[Dict]:
        """Load mapping from cache if fresh"""
        cache_path = self._get_cache_path(identifier, id_type)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)
            
            # Check if cache is fresh
            cached_time = datetime.fromisoformat(cached['cached_at'])
            if datetime.now() - cached_time < CACHE_DURATION:
                return cached['data']
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
        
        return None
    
    def _save_to_cache(self, identifier: str, id_type: str, data: Dict):
        """Save mapping to cache"""
        cache_path = self._get_cache_path(identifier, id_type)
        with open(cache_path, 'w') as f:
            json.dump({
                'cached_at': datetime.now().isoformat(),
                'data': data
            }, f, indent=2)
    
    def map_identifier(
        self,
        identifier: str,
        id_type: str = "TICKER",
        exchange_code: Optional[str] = None,
        mic_code: Optional[str] = None,
        currency: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Map a single identifier to FIGI/ISIN/CUSIP
        
        Args:
            identifier: The identifier to map (e.g., "AAPL", "US0378331005")
            id_type: Type of identifier - TICKER, ISIN, CUSIP, SEDOL, etc.
            exchange_code: Optional exchange code (e.g., "US" for NYSE/NASDAQ)
            mic_code: Optional market identifier code
            currency: Optional currency code
            
        Returns:
            Dict with mapping results including FIGI, name, ticker, exchange, etc.
        """
        # Check cache first
        cache_key = f"{identifier}_{exchange_code or ''}_{mic_code or ''}"
        cached = self._load_from_cache(cache_key, id_type)
        if cached:
            return cached
        
        # Build request payload
        job = {"idType": id_type, "idValue": identifier}
        if exchange_code:
            job["exchCode"] = exchange_code
        if mic_code:
            job["micCode"] = mic_code
        if currency:
            job["currency"] = currency
        
        # Make API request
        self._rate_limit()
        response = requests.post(
            BASE_URL,
            json=[job],
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        results = response.json()
        
        # Parse results
        if not results or 'error' in results[0]:
            error_msg = results[0].get('error', 'Unknown error') if results else 'No results'
            result = {
                'success': False,
                'error': error_msg,
                'identifier': identifier,
                'id_type': id_type
            }
        else:
            # Take first match
            data = results[0]['data'][0] if results[0].get('data') else {}
            result = {
                'success': True,
                'figi': data.get('figi'),
                'composite_figi': data.get('compositeFIGI'),
                'share_class_figi': data.get('shareClassFIGI'),
                'name': data.get('name'),
                'ticker': data.get('ticker'),
                'exchange_code': data.get('exchCode'),
                'mic_code': data.get('micCode'),
                'currency': data.get('currency'),
                'market_sector': data.get('marketSector'),
                'security_type': data.get('securityType'),
                'security_type2': data.get('securityType2'),
                'metadata': data.get('metadata', {}),
                'identifier': identifier,
                'id_type': id_type
            }
        
        # Cache the result
        self._save_to_cache(cache_key, id_type, result)
        
        return result
    
    def batch_map(
        self,
        identifiers: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Map multiple identifiers in a single request (max 100)
        
        Args:
            identifiers: List of dicts with keys: idValue, idType, exchCode (optional)
            
        Returns:
            List of mapping results
        """
        if len(identifiers) > BATCH_SIZE:
            raise ValueError(f"Batch size exceeds limit of {BATCH_SIZE}")
        
        # Check cache for all identifiers
        results = []
        uncached_jobs = []
        uncached_indices = []
        
        for idx, job in enumerate(identifiers):
            cache_key = f"{job['idValue']}_{job.get('exchCode', '')}"
            cached = self._load_from_cache(cache_key, job['idType'])
            if cached:
                results.append(cached)
            else:
                results.append(None)  # Placeholder
                uncached_jobs.append(job)
                uncached_indices.append(idx)
        
        # Fetch uncached identifiers
        if uncached_jobs:
            self._rate_limit()
            response = requests.post(
                BASE_URL,
                json=uncached_jobs,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            batch_results = response.json()
            
            # Parse and cache results
            for job_idx, api_result in enumerate(batch_results):
                result_idx = uncached_indices[job_idx]
                job = uncached_jobs[job_idx]
                
                if 'error' in api_result or not api_result.get('data'):
                    error_msg = api_result.get('error', 'No results')
                    result = {
                        'success': False,
                        'error': error_msg,
                        'identifier': job['idValue'],
                        'id_type': job['idType']
                    }
                else:
                    data = api_result['data'][0]
                    result = {
                        'success': True,
                        'figi': data.get('figi'),
                        'composite_figi': data.get('compositeFIGI'),
                        'share_class_figi': data.get('shareClassFIGI'),
                        'name': data.get('name'),
                        'ticker': data.get('ticker'),
                        'exchange_code': data.get('exchCode'),
                        'mic_code': data.get('micCode'),
                        'currency': data.get('currency'),
                        'market_sector': data.get('marketSector'),
                        'security_type': data.get('securityType'),
                        'security_type2': data.get('securityType2'),
                        'metadata': data.get('metadata', {}),
                        'identifier': job['idValue'],
                        'id_type': job['idType']
                    }
                
                # Cache and store result
                cache_key = f"{job['idValue']}_{job.get('exchCode', '')}"
                self._save_to_cache(cache_key, job['idType'], result)
                results[result_idx] = result
        
        return results
    
    def ticker_to_figi(self, ticker: str, exchange: Optional[str] = None) -> Optional[str]:
        """Convenience method: ticker → FIGI"""
        result = self.map_identifier(ticker, "TICKER", exchange_code=exchange)
        return result.get('figi') if result.get('success') else None
    
    def figi_to_isin(self, figi: str) -> Optional[str]:
        """Convenience method: FIGI → ISIN"""
        result = self.map_identifier(figi, "ID_BB_GLOBAL")
        if result.get('success') and result.get('metadata'):
            return result['metadata'].get('isin')
        return None
    
    def ticker_to_cusip(self, ticker: str, exchange: Optional[str] = None) -> Optional[str]:
        """Convenience method: ticker → CUSIP"""
        result = self.map_identifier(ticker, "TICKER", exchange_code=exchange)
        if result.get('success') and result.get('metadata'):
            return result['metadata'].get('cusip')
        return None


def map_ticker(ticker: str, exchange: Optional[str] = None, output_format: str = "json") -> str:
    """
    CLI wrapper: Map ticker to all identifiers
    
    Args:
        ticker: Stock ticker symbol
        exchange: Optional exchange code (US, LN, etc.)
        output_format: json or table
        
    Returns:
        Formatted output string
    """
    client = OpenFIGIClient()
    result = client.map_identifier(ticker, "TICKER", exchange_code=exchange)
    
    if output_format == "json":
        return json.dumps(result, indent=2)
    else:
        if not result.get('success'):
            return f"❌ Error: {result.get('error', 'Unknown error')}"
        
        output = f"""
✅ {result.get('name', 'N/A')} ({ticker})

🔑 Identifiers:
   FIGI:           {result.get('figi', 'N/A')}
   Composite FIGI: {result.get('composite_figi', 'N/A')}
   Share Class:    {result.get('share_class_figi', 'N/A')}
   ISIN:           {result.get('metadata', {}).get('isin', 'N/A')}
   CUSIP:          {result.get('metadata', {}).get('cusip', 'N/A')}
   SEDOL:          {result.get('metadata', {}).get('sedol', 'N/A')}

📊 Market Info:
   Exchange:       {result.get('exchange_code', 'N/A')}
   MIC Code:       {result.get('mic_code', 'N/A')}
   Currency:       {result.get('currency', 'N/A')}
   Sector:         {result.get('market_sector', 'N/A')}
   Security Type:  {result.get('security_type', 'N/A')} / {result.get('security_type2', 'N/A')}
"""
        return output.strip()


def batch_map_tickers(tickers: List[str], exchange: Optional[str] = None) -> str:
    """
    CLI wrapper: Map multiple tickers in batch
    
    Args:
        tickers: List of ticker symbols
        exchange: Optional exchange code for all tickers
        
    Returns:
        JSON string with all results
    """
    client = OpenFIGIClient()
    
    jobs = [
        {"idValue": ticker, "idType": "TICKER", "exchCode": exchange}
        if exchange else {"idValue": ticker, "idType": "TICKER"}
        for ticker in tickers
    ]
    
    results = client.batch_map(jobs)
    return json.dumps(results, indent=2)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python openfigi_mapping.py <ticker> [exchange]")
        print("Example: python openfigi_mapping.py AAPL US")
        sys.exit(1)
    
    ticker = sys.argv[1]
    exchange = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(map_ticker(ticker, exchange, output_format="table"))

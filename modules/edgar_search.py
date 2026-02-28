#!/usr/bin/env python3
"""
SEC EDGAR Full-Text Search Module
Phase 706 — Full-text search across all SEC filings

REST API: https://efts.sec.gov/LATEST/search-index
Rate limit: 10 requests/second
No API key required
Features:
- Full-text search across all SEC filings
- NLP on 10-K/10-Q narratives
- Keyword alerts
- Entity search (company, person, CIK)
- Date range filtering
"""

import requests
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class EdgarSearch:
    """SEC EDGAR Full-Text Search via official REST API"""
    
    BASE_URL = "https://efts.sec.gov/LATEST/search-index"
    RATE_LIMIT = 0.1  # 10 req/sec = 0.1s between requests
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantClaw edgar-search/1.0 (support@quantclaw.ai)',
            'Accept': 'application/json'
        })
        self.last_request = 0
        
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request
        if elapsed < self.RATE_LIMIT:
            time.sleep(self.RATE_LIMIT - elapsed)
        self.last_request = time.time()
        
    def search(
        self,
        query: str,
        entity: Optional[str] = None,
        cik: Optional[str] = None,
        filing_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> Dict:
        """
        Full-text search SEC EDGAR filings
        
        Args:
            query: Search keywords (e.g., "climate risk", "supply chain disruption")
            entity: Company name filter
            cik: CIK number filter (leading zeros optional)
            filing_type: Filing form type (e.g., "10-K", "8-K", "DEF 14A")
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
            limit: Max results (default 100, max 500)
            
        Returns:
            {
                "hits": int,
                "filings": [
                    {
                        "cik": str,
                        "entity": str,
                        "form": str,
                        "filing_date": str,
                        "accession": str,
                        "url": str,
                        "snippet": str,
                        "relevance": float
                    }
                ]
            }
        """
        self._rate_limit()
        
        params = {
            'q': query,
            'dateRange': 'all'
        }
        
        if entity:
            params['entityName'] = entity
        if cik:
            params['ciks'] = cik.lstrip('0')
        if filing_type:
            params['forms'] = filing_type
        if start_date and end_date:
            params['dateRange'] = 'custom'
            params['startdt'] = start_date
            params['enddt'] = end_date
            
        params['page'] = 1
        params['from'] = 0
        params['size'] = min(limit, 500)
        
        try:
            resp = self.session.get(self.BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            return {
                'hits': data.get('hits', {}).get('total', {}).get('value', 0),
                'filings': self._parse_results(data.get('hits', {}).get('hits', []))
            }
        except Exception as e:
            return {'error': str(e), 'hits': 0, 'filings': []}
            
    def _parse_results(self, hits: List[Dict]) -> List[Dict]:
        """Parse EDGAR search results"""
        filings = []
        for hit in hits:
            source = hit.get('_source', {})
            filings.append({
                'cik': source.get('ciks', [''])[0],
                'entity': source.get('display_names', [''])[0],
                'form': source.get('form', ''),
                'filing_date': source.get('file_date', ''),
                'accession': source.get('accession_number', ''),
                'url': f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={source.get('ciks', [''])[0]}&accession_number={source.get('accession_number', '')}&xbrl_type=v",
                'snippet': hit.get('highlight', {}).get('text', [''])[0] if 'highlight' in hit else '',
                'relevance': hit.get('_score', 0)
            })
        return filings
        
    def search_risk_factors(self, ticker: str, keywords: List[str] = None, years: int = 3) -> List[Dict]:
        """Search Item 1A Risk Factors in 10-K filings"""
        if keywords is None:
            keywords = ['climate', 'cybersecurity', 'supply chain', 'recession', 
                       'pandemic', 'regulation', 'competition', 'litigation']
                       
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365*years)).strftime('%Y-%m-%d')
        
        results = []
        for keyword in keywords:
            query = f'"{keyword}" AND "Item 1A" AND "Risk Factors"'
            resp = self.search(query=query, entity=ticker, filing_type='10-K',
                             start_date=start_date, end_date=end_date, limit=50)
            for filing in resp.get('filings', []):
                filing['keyword'] = keyword
                results.append(filing)
        return results


def search_edgar(query: str, **kwargs) -> Dict:
    """Convenience function for quick searches"""
    edgar = EdgarSearch()
    return edgar.search(query, **kwargs)


def main():
    """CLI for SEC EDGAR full-text search"""
    import argparse
    parser = argparse.ArgumentParser(description='SEC EDGAR Full-Text Search')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--ticker', help='Company ticker/name filter')
    parser.add_argument('--form', help='Filing type (10-K, 8-K, etc)')
    parser.add_argument('--limit', type=int, default=20, help='Max results')
    args = parser.parse_args()
    
    edgar = EdgarSearch()
    results = edgar.search(query=args.query, entity=args.ticker, filing_type=args.form, limit=args.limit)
    
    print(f"\n🔍 EDGAR Search Results")
    print(f"Query: {args.query}")
    print(f"Total hits: {results['hits']}")
    print(f"Showing: {len(results['filings'])}\n")
    
    for filing in results['filings']:
        print(f"📄 {filing['entity']} ({filing['cik']})")
        print(f"   Form: {filing['form']} | Date: {filing['filing_date']}")
        print(f"   Relevance: {filing['relevance']:.2f}")
        print(f"   Snippet: {filing['snippet'][:200]}...")
        print(f"   URL: {filing['url']}\n")


if __name__ == '__main__':
    main()

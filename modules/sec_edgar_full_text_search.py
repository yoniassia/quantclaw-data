"""
SEC EDGAR Full-Text Search Module
Bloomberg EDGAR<GO> Replacement

Full-text search across all SEC filings via official SEC EDGAR API.
Supports NLP on 10-K/10-Q narratives, keyword alerts, risk factor extraction.

REST API: 10 req/sec, no API key required.
Endpoint: https://efts.sec.gov/LATEST/search-index

Features:
- Full-text search across all filing types (10-K, 10-Q, 8-K, DEF 14A, 13D/F, etc)
- Keyword highlighting, proximity search, phrase matching
- Date range filtering, entity/CIK filtering
- Risk factor extraction from 10-K Item 1A
- MD&A sentiment analysis from 10-K/10-Q Item 7
- Extract management tone, forward guidance, business outlook
- Real-time filing alerts based on keyword patterns

Data Sources:
- SEC EDGAR Full Text Search API (https://www.sec.gov/edgar/search-and-access)
- No API key required (user-agent identification only)
- Rate limit: 10 requests/second (honor via delay)

Author: QuantClaw Night Builder
Created: 2026-02-28
"""

import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import re

class SECEdgarFullTextSearch:
    """SEC EDGAR Full-Text Search Client"""
    
    BASE_URL = "https://efts.sec.gov/LATEST/search-index"
    USER_AGENT = "QuantClaw Data Platform contact@moneyclaw.com"
    RATE_LIMIT_DELAY = 0.11  # 10 req/sec = 0.1s, add margin → 0.11s
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
            "Host": "efts.sec.gov"
        })
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limit of 10 req/sec"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def search(
        self,
        query: str,
        entity: Optional[str] = None,
        ciks: Optional[List[str]] = None,
        forms: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        start_index: int = 0,
        count: int = 100
    ) -> Dict[str, Any]:
        """
        Full-text search across SEC filings
        
        Args:
            query: Search query string (keywords, phrases in quotes, boolean ops)
            entity: Company name or ticker filter
            ciks: List of CIK numbers to filter
            forms: Filing types to filter (e.g., ['10-K', '10-Q', '8-K'])
            from_date: Start date YYYY-MM-DD
            to_date: End date YYYY-MM-DD
            start_index: Pagination offset
            count: Results per page (max 100)
        
        Returns:
            {
                'query': str,
                'total_hits': int,
                'results': [
                    {
                        'cik': str,
                        'entity': str,
                        'form': str,
                        'file_date': str,
                        'file_num': str,
                        'url': str,
                        'highlights': [str],  # matching snippets
                        'accession_number': str
                    },
                    ...
                ],
                'took_ms': int
            }
        """
        self._rate_limit()
        
        # Build query parameters
        params = {
            'q': query,
            'from': start_index,
            'size': min(count, 100)
        }
        
        if entity:
            params['entityName'] = entity
        
        if ciks:
            params['ciks'] = ','.join(ciks)
        
        if forms:
            params['forms'] = ','.join(forms)
        
        if from_date:
            params['dateRange'] = 'custom'
            params['startdt'] = from_date
        
        if to_date:
            if 'dateRange' not in params:
                params['dateRange'] = 'custom'
            params['enddt'] = to_date
        
        try:
            resp = self.session.get(self.BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            results = []
            for hit in data.get('hits', {}).get('hits', []):
                source = hit.get('_source', {})
                highlights = hit.get('highlight', {})
                
                result = {
                    'cik': source.get('ciks', [''])[0],
                    'entity': source.get('display_names', [''])[0],
                    'form': source.get('file_type', ''),
                    'file_date': source.get('file_date', ''),
                    'file_num': source.get('file_num', ''),
                    'accession_number': source.get('adsh', ''),
                    'url': f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={source.get('ciks', [''])[0]}&accession_number={source.get('adsh', '')}&xbrl_type=v",
                    'highlights': []
                }
                
                # Extract highlights from various fields
                for field, snippets in highlights.items():
                    result['highlights'].extend(snippets)
                
                results.append(result)
            
            return {
                'query': query,
                'total_hits': data.get('hits', {}).get('total', {}).get('value', 0),
                'results': results,
                'took_ms': data.get('took', 0)
            }
        
        except Exception as e:
            return {
                'query': query,
                'error': str(e),
                'total_hits': 0,
                'results': []
            }
    
    def search_risk_factors(
        self,
        ticker_or_entity: str,
        keywords: Optional[List[str]] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search Item 1A Risk Factors from 10-K filings
        
        Args:
            ticker_or_entity: Company ticker or name
            keywords: Optional keywords to filter (e.g., ['litigation', 'cybersecurity'])
            year: Fiscal year (optional)
        
        Returns:
            {
                'entity': str,
                'filings': [
                    {
                        'fiscal_year': int,
                        'file_date': str,
                        'url': str,
                        'risk_factors': [str],  # extracted paragraphs
                        'keyword_matches': {keyword: int}
                    }
                ]
            }
        """
        # Build search query for Item 1A risk factors
        query = f'"Item 1A" AND "Risk Factors"'
        if keywords:
            query += ' AND (' + ' OR '.join(f'"{kw}"' for kw in keywords) + ')'
        
        from_date = f"{year}-01-01" if year else None
        to_date = f"{year}-12-31" if year else None
        
        results = self.search(
            query=query,
            entity=ticker_or_entity,
            forms=['10-K'],
            from_date=from_date,
            to_date=to_date,
            count=10
        )
        
        filings = []
        for hit in results['results']:
            # Extract risk factor text from highlights
            risk_factors = []
            keyword_matches = {kw: 0 for kw in (keywords or [])}
            
            for snippet in hit['highlights']:
                # Clean HTML tags
                clean_snippet = re.sub(r'<[^>]+>', '', snippet)
                risk_factors.append(clean_snippet)
                
                # Count keyword matches
                for kw in (keywords or []):
                    keyword_matches[kw] += clean_snippet.lower().count(kw.lower())
            
            filing = {
                'fiscal_year': int(hit['file_date'][:4]) if hit['file_date'] else None,
                'file_date': hit['file_date'],
                'url': hit['url'],
                'risk_factors': risk_factors,
                'keyword_matches': keyword_matches
            }
            filings.append(filing)
        
        return {
            'entity': ticker_or_entity,
            'total_filings': results['total_hits'],
            'filings': filings
        }
    
    def search_mda(
        self,
        ticker_or_entity: str,
        keywords: Optional[List[str]] = None,
        quarters: int = 4
    ) -> Dict[str, Any]:
        """
        Search MD&A (Item 7 from 10-K, Item 2 from 10-Q)
        
        Args:
            ticker_or_entity: Company ticker or name
            keywords: Optional keywords (e.g., ['margins', 'headwinds', 'growth'])
            quarters: Number of recent quarters to fetch
        
        Returns:
            {
                'entity': str,
                'filings': [
                    {
                        'form': str,  # '10-K' or '10-Q'
                        'period': str,
                        'file_date': str,
                        'url': str,
                        'mda_excerpts': [str],
                        'sentiment_keywords': {
                            'positive': [str],
                            'negative': [str],
                            'uncertain': [str]
                        }
                    }
                ]
            }
        """
        # Search for MD&A sections
        query = '"Management\'s Discussion" OR "MD&A"'
        if keywords:
            query += ' AND (' + ' OR '.join(f'"{kw}"' for kw in keywords) + ')'
        
        # Fetch recent filings
        results = self.search(
            query=query,
            entity=ticker_or_entity,
            forms=['10-K', '10-Q'],
            count=quarters * 2  # Over-fetch to ensure coverage
        )
        
        # Sentiment lexicons (simplified)
        positive_words = ['growth', 'strong', 'improved', 'increased', 'gains', 'expansion', 'profitable']
        negative_words = ['decline', 'weak', 'decreased', 'losses', 'challenges', 'headwinds', 'risk']
        uncertain_words = ['may', 'could', 'uncertain', 'volatile', 'potential', 'depends']
        
        filings = []
        for hit in results['results'][:quarters]:
            excerpts = [re.sub(r'<[^>]+>', '', s) for s in hit['highlights']]
            
            # Sentiment analysis
            full_text = ' '.join(excerpts).lower()
            sentiment = {
                'positive': [w for w in positive_words if w in full_text],
                'negative': [w for w in negative_words if w in full_text],
                'uncertain': [w for w in uncertain_words if w in full_text]
            }
            
            filing = {
                'form': hit['form'],
                'period': hit['file_date'][:7] if hit['file_date'] else '',  # YYYY-MM
                'file_date': hit['file_date'],
                'url': hit['url'],
                'mda_excerpts': excerpts,
                'sentiment_keywords': sentiment
            }
            filings.append(filing)
        
        return {
            'entity': ticker_or_entity,
            'total_filings': results['total_hits'],
            'filings': filings
        }
    
    def keyword_alert(
        self,
        keywords: List[str],
        forms: Optional[List[str]] = None,
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """
        Real-time keyword alert across recent filings
        
        Args:
            keywords: List of keywords to monitor
            forms: Filing types to monitor (default: all)
            hours_back: How far back to search (default: 24 hours)
        
        Returns:
            {
                'keywords': [str],
                'time_range': str,
                'alerts': [
                    {
                        'keyword': str,
                        'entity': str,
                        'form': str,
                        'file_date': str,
                        'url': str,
                        'snippet': str
                    }
                ]
            }
        """
        from_date = (datetime.now() - timedelta(hours=hours_back)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        alerts = []
        for keyword in keywords:
            results = self.search(
                query=f'"{keyword}"',
                forms=forms,
                from_date=from_date,
                to_date=to_date,
                count=100
            )
            
            for hit in results['results']:
                # Find best snippet containing keyword
                best_snippet = ''
                for snippet in hit['highlights']:
                    if keyword.lower() in snippet.lower():
                        best_snippet = re.sub(r'<[^>]+>', '', snippet)
                        break
                
                alert = {
                    'keyword': keyword,
                    'entity': hit['entity'],
                    'cik': hit['cik'],
                    'form': hit['form'],
                    'file_date': hit['file_date'],
                    'url': hit['url'],
                    'snippet': best_snippet
                }
                alerts.append(alert)
        
        return {
            'keywords': keywords,
            'time_range': f'{from_date} to {to_date}',
            'total_alerts': len(alerts),
            'alerts': alerts
        }

# CLI interface
if __name__ == "__main__":
    import sys
    
    client = SECEdgarFullTextSearch()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python sec_edgar_full_text_search.py [edgar-]search <query> [--entity AAPL] [--forms 10-K,10-Q]")
        print("  python sec_edgar_full_text_search.py [edgar-]risk-factors <entity> [--keywords litigation,cyber]")
        print("  python sec_edgar_full_text_search.py [edgar-]mda <entity> [--quarters 4]")
        print("  python sec_edgar_full_text_search.py [edgar-]alert <keywords> [--hours 24]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Map edgar-* commands to base commands for cli.py compatibility
    command_map = {
        'edgar-search': 'search',
        'edgar-risk-factors': 'risk-factors',
        'edgar-mda': 'mda',
        'edgar-alert': 'alert'
    }
    if command in command_map:
        command = command_map[command]
    
    if command == "search":
        query = sys.argv[2]
        entity = None
        forms = None
        
        for i, arg in enumerate(sys.argv[3:], 3):
            if arg == "--entity" and i+1 < len(sys.argv):
                entity = sys.argv[i+1]
            elif arg == "--forms" and i+1 < len(sys.argv):
                forms = sys.argv[i+1].split(',')
        
        results = client.search(query, entity=entity, forms=forms)
        print(json.dumps(results, indent=2))
    
    elif command == "risk-factors":
        entity = sys.argv[2]
        keywords = None
        
        for i, arg in enumerate(sys.argv[3:], 3):
            if arg == "--keywords" and i+1 < len(sys.argv):
                keywords = sys.argv[i+1].split(',')
        
        results = client.search_risk_factors(entity, keywords=keywords)
        print(json.dumps(results, indent=2))
    
    elif command == "mda":
        entity = sys.argv[2]
        quarters = 4
        
        for i, arg in enumerate(sys.argv[3:], 3):
            if arg == "--quarters" and i+1 < len(sys.argv):
                quarters = int(sys.argv[i+1])
        
        results = client.search_mda(entity, quarters=quarters)
        print(json.dumps(results, indent=2))
    
    elif command == "alert":
        keywords = sys.argv[2].split(',')
        hours = 24
        
        for i, arg in enumerate(sys.argv[3:], 3):
            if arg == "--hours" and i+1 < len(sys.argv):
                hours = int(sys.argv[i+1])
        
        results = client.keyword_alert(keywords, hours_back=hours)
        print(json.dumps(results, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

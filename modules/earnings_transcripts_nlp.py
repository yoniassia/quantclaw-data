#!/usr/bin/env python3
"""
Earnings Transcripts NLP Module
Parse 8-K/call transcripts, extract key quotes, guidance changes, management sentiment.
Uses SEC EDGAR for 8-K filings, BeautifulSoup for HTML parsing, TextBlob/VADER for sentiment.
"""

import requests
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
try:
    from textblob import TextBlob
    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False
    print("Warning: textblob not installed. Using fallback sentiment. Install: pip install textblob", file=__import__('sys').stderr)

class EarningsTranscriptsNLP:
    """Parse and analyze earnings call transcripts from SEC 8-K filings."""
    
    BASE_URL = "https://www.sec.gov"
    HEADERS = {
        "User-Agent": "QuantClawData Research/1.0 (data@quantclaw.com)",
        "Accept": "application/json"
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.cache = {}
    
    def get_recent_8k(self, ticker: str, days: int = 90) -> List[Dict]:
        """Fetch recent 8-K filings for a ticker."""
        # Search SEC EDGAR for company CIK
        cik = self._get_cik(ticker)
        if not cik:
            return []
        
        # Get submissions
        url = f"{self.BASE_URL}/cgi-bin/browse-edgar"
        params = {
            "action": "getcompany",
            "CIK": cik,
            "type": "8-K",
            "dateb": "",
            "owner": "exclude",
            "count": 100,
            "output": "atom"
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            
            # Parse Atom XML
            from xml.etree import ElementTree as ET
            root = ET.fromstring(resp.content)
            
            filings = []
            for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                filing_date = entry.find('.//{http://www.w3.org/2005/Atom}updated').text
                link = entry.find('.//{http://www.w3.org/2005/Atom}link[@rel="alternate"]').get('href')
                
                filing_dt = datetime.strptime(filing_date[:10], '%Y-%m-%d')
                if (datetime.now() - filing_dt).days <= days:
                    filings.append({
                        'date': filing_date[:10],
                        'url': link,
                        'ticker': ticker
                    })
            
            return filings
        except Exception as e:
            print(f"Error fetching 8-K for {ticker}: {e}")
            return []
    
    def _get_cik(self, ticker: str) -> Optional[str]:
        """Lookup CIK from ticker using SEC company tickers JSON."""
        if ticker in self.cache:
            return self.cache[ticker]
        
        try:
            url = f"{self.BASE_URL}/files/company_tickers.json"
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            
            data = resp.json()
            for company in data.values():
                if company['ticker'].upper() == ticker.upper():
                    cik = str(company['cik_str']).zfill(10)
                    self.cache[ticker] = cik
                    return cik
            return None
        except Exception as e:
            print(f"Error looking up CIK for {ticker}: {e}")
            return None
    
    def extract_transcript(self, filing_url: str) -> Optional[str]:
        """Extract full text from 8-K filing HTML."""
        try:
            # Get filing index page
            resp = self.session.get(filing_url, timeout=10)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Find main document link (usually .htm file)
            doc_link = None
            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 3 and 'htm' in cells[2].text.lower():
                    link = cells[2].find('a')
                    if link:
                        doc_link = self.BASE_URL + link.get('href')
                        break
            
            if not doc_link:
                return None
            
            # Fetch actual document
            doc_resp = self.session.get(doc_link, timeout=10)
            doc_resp.raise_for_status()
            
            doc_soup = BeautifulSoup(doc_resp.content, 'html.parser')
            
            # Extract text (remove scripts, styles)
            for script in doc_soup(['script', 'style']):
                script.decompose()
            
            text = doc_soup.get_text()
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            text = '\n'.join(line for line in lines if line)
            
            return text
        except Exception as e:
            print(f"Error extracting transcript from {filing_url}: {e}")
            return None
    
    def extract_key_quotes(self, transcript: str, max_quotes: int = 10) -> List[Dict]:
        """Extract key statements using heuristics (long sentences, executive names)."""
        quotes = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', transcript)
        
        # Filter for substantive sentences (20-200 words, contains key terms)
        key_terms = ['guidance', 'outlook', 'expect', 'forecast', 'revenue', 'earnings', 'margin', 'growth']
        
        for sent in sentences:
            words = sent.split()
            if 20 <= len(words) <= 200:
                sent_lower = sent.lower()
                if any(term in sent_lower for term in key_terms):
                    # Check for sentiment
                    if HAS_TEXTBLOB:
                        blob = TextBlob(sent)
                        sentiment = blob.sentiment.polarity
                    else:
                        sentiment = self._simple_sentiment(sent_lower)
                    
                    quotes.append({
                        'text': sent.strip(),
                        'sentiment': round(sentiment, 3),
                        'length': len(words)
                    })
        
        # Sort by absolute sentiment magnitude
        quotes.sort(key=lambda x: abs(x['sentiment']), reverse=True)
        
        return quotes[:max_quotes]
    
    def _simple_sentiment(self, text: str) -> float:
        """Fallback sentiment using keyword counts."""
        positive_words = ['growth', 'strong', 'increase', 'beat', 'exceed', 'positive', 'improve', 'gain', 'success', 'optimistic']
        negative_words = ['decline', 'weak', 'miss', 'below', 'concern', 'negative', 'decrease', 'loss', 'challenge', 'difficult']
        
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        total = pos_count + neg_count
        if total == 0:
            return 0.0
        
        return (pos_count - neg_count) / total * 0.5  # Scale to [-0.5, 0.5]
    
    def detect_guidance_changes(self, transcript: str) -> Dict:
        """Detect guidance revisions using keyword patterns."""
        patterns = {
            'raise': r'(rais|increas|upward|above|exceed|higher).*guidance',
            'lower': r'(lower|reduc|downward|below|under|decreas).*guidance',
            'reaffirm': r'(reaffirm|maintain|reiterat|confirm).*guidance',
            'withdraw': r'(withdraw|suspend|remov).*guidance'
        }
        
        text_lower = transcript.lower()
        
        results = {}
        for action, pattern in patterns.items():
            matches = re.findall(pattern, text_lower)
            results[action] = len(matches)
        
        # Determine net direction
        if results['raise'] > results['lower']:
            results['net_direction'] = 'positive'
        elif results['lower'] > results['raise']:
            results['net_direction'] = 'negative'
        elif results['reaffirm'] > 0:
            results['net_direction'] = 'neutral'
        else:
            results['net_direction'] = 'unknown'
        
        return results
    
    def analyze_sentiment(self, transcript: str) -> Dict:
        """Overall sentiment analysis of transcript using TextBlob."""
        if HAS_TEXTBLOB:
            blob = TextBlob(transcript)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
        else:
            polarity = self._simple_sentiment(transcript.lower())
            subjectivity = 0.5  # Default
        
        return {
            'polarity': round(polarity, 3),
            'subjectivity': round(subjectivity, 3),
            'interpretation': self._interpret_sentiment(polarity)
        }
    
    def _interpret_sentiment(self, polarity: float) -> str:
        """Map polarity to verbal interpretation."""
        if polarity > 0.3:
            return 'very_positive'
        elif polarity > 0.1:
            return 'positive'
        elif polarity > -0.1:
            return 'neutral'
        elif polarity > -0.3:
            return 'negative'
        else:
            return 'very_negative'
    
    def full_analysis(self, ticker: str, days: int = 90) -> Dict:
        """Complete NLP analysis for a ticker's recent earnings."""
        filings = self.get_recent_8k(ticker, days)
        
        if not filings:
            return {'error': f'No 8-K filings found for {ticker} in last {days} days'}
        
        results = []
        for filing in filings[:3]:  # Analyze most recent 3
            transcript = self.extract_transcript(filing['url'])
            if not transcript:
                continue
            
            analysis = {
                'date': filing['date'],
                'url': filing['url'],
                'key_quotes': self.extract_key_quotes(transcript),
                'guidance_changes': self.detect_guidance_changes(transcript),
                'sentiment': self.analyze_sentiment(transcript)
            }
            results.append(analysis)
        
        return {
            'ticker': ticker,
            'filings_analyzed': len(results),
            'results': results,
            'generated_at': datetime.now().isoformat()
        }


def cli():
    """Command-line interface for earnings transcript analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Earnings Transcript NLP Analysis')
    parser.add_argument('command', help='Command: earnings-nlp|earnings-sentiment|earnings-quotes|earnings-guidance')
    parser.add_argument('ticker', nargs='?', help='Stock ticker symbol')
    parser.add_argument('--days', type=int, default=90, help='Look back days for 8-K filings')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # Validate ticker for commands that need it
    if not args.ticker and args.command in ['earnings-nlp', 'earnings-sentiment', 'earnings-quotes', 'earnings-guidance']:
        parser.error(f"ticker required for {args.command}")
    
    analyzer = EarningsTranscriptsNLP()
    
    # Route to specific analysis
    if args.command == 'earnings-nlp':
        result = analyzer.full_analysis(args.ticker.upper(), args.days)
        if args.json:
            print(json.dumps(result, indent=2))
            return
        
        if 'error' in result:
            print(f"Error: {result['error']}")
            return
        
        print(f"\n=== Earnings Transcript Analysis: {args.ticker} ===\n")
        print(f"Analyzed {result['filings_analyzed']} recent filings:\n")
        
        for i, analysis in enumerate(result['results'], 1):
            print(f"Filing #{i} ({analysis['date']}):")
            print(f"  Overall Sentiment: {analysis['sentiment']['interpretation']} "
                  f"(polarity: {analysis['sentiment']['polarity']})")
            
            guidance = analysis['guidance_changes']
            print(f"  Guidance Direction: {guidance['net_direction']}")
            print(f"    Raises: {guidance['raise']}, Lowers: {guidance['lower']}, "
                  f"Reaffirms: {guidance['reaffirm']}")
            
            print(f"\n  Top Key Quotes:")
            for j, quote in enumerate(analysis['key_quotes'][:3], 1):
                print(f"    {j}. [{quote['sentiment']:+.2f}] {quote['text'][:120]}...")
            print()
    
    elif args.command == 'earnings-sentiment':
        result = analyzer.full_analysis(args.ticker.upper(), args.days)
        if 'error' in result:
            print(f"Error: {result['error']}")
            return
        
        print(f"\n=== Sentiment Summary: {args.ticker} ===\n")
        for analysis in result['results']:
            sent = analysis['sentiment']
            print(f"{analysis['date']}: {sent['interpretation'].upper()} (polarity: {sent['polarity']:+.2f})")
    
    elif args.command == 'earnings-quotes':
        result = analyzer.full_analysis(args.ticker.upper(), args.days)
        if 'error' in result:
            print(f"Error: {result['error']}")
            return
        
        print(f"\n=== Key Quotes: {args.ticker} ===\n")
        for i, analysis in enumerate(result['results'], 1):
            print(f"\nFiling {analysis['date']}:")
            for j, quote in enumerate(analysis['key_quotes'][:5], 1):
                print(f"  {j}. [{quote['sentiment']:+.2f}] {quote['text']}")
    
    elif args.command == 'earnings-guidance':
        result = analyzer.full_analysis(args.ticker.upper(), args.days)
        if 'error' in result:
            print(f"Error: {result['error']}")
            return
        
        print(f"\n=== Guidance Changes: {args.ticker} ===\n")
        for analysis in result['results']:
            guidance = analysis['guidance_changes']
            print(f"{analysis['date']}: {guidance['net_direction'].upper()}")
            print(f"  Raises: {guidance['raise']}, Lowers: {guidance['lower']}, "
                  f"Reaffirms: {guidance['reaffirm']}, Withdrawals: {guidance['withdraw']}")


if __name__ == '__main__':
    cli()

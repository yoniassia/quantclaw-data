#!/usr/bin/env python3
"""
StockAnalysis.com — EPS Estimates & Revisions Scraper
Critical module for Alpha Picker V3 EPS estimate revision signal.

Usage:
  python modules/stockanalysiscom.py --ticker AAPL --json

Data source: https://stockanalysis.com/stocks/{ticker}/forecast/
"""

import requests
from bs4 import BeautifulSoup
import argparse
import json
import sys
from datetime import datetime
from typing import Dict, Any
import re
import time

class StockAnalysisScraper:
    """Scrape StockAnalysis.com for EPS estimates, revisions, and fundamentals"""
    
    BASE_URL = "https://stockanalysis.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml',
        })
    
    def get_forecast(self, ticker: str) -> Dict[str, Any]:
        """Get EPS/revenue forecasts and analyst data"""
        ticker = ticker.upper().strip()
        
        try:
            url = f"{self.BASE_URL}/stocks/{ticker.lower()}/forecast/"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for valid page (title contains ticker)
            title = soup.find('title')
            if not title or ticker not in title.get_text().upper():
                return {'error': f'Ticker {ticker} not found or invalid page', 'ticker': ticker}
            
            data = {
                'ticker': ticker,
                'price_target': {},
                'analyst_consensus': {},
                'eps_estimates': {},
                'revenue_estimates': {},
                'recent_ratings': [],
                'timestamp': datetime.utcnow().isoformat(),
                'source': url
            }
            
            # Extract price target from text
            text_content = soup.get_text()
            
            # Look for analyst count and average target
            analyst_match = re.search(r'(\d+)\s+analysts.*?average price target[^$]*\$([0-9,]+\.?\d*)', text_content, re.I)
            if analyst_match:
                data['price_target']['analyst_count'] = int(analyst_match.group(1))
                data['price_target']['average'] = float(analyst_match.group(2).replace(',', ''))
            
            # Look for low/high targets
            low_match = re.search(r'lowest target.*?\$([0-9,]+)', text_content, re.I)
            high_match = re.search(r'highest.*?\$([0-9,]+)', text_content, re.I)
            
            if low_match:
                data['price_target']['low'] = float(low_match.group(1).replace(',', ''))
            if high_match:
                data['price_target']['high'] = float(high_match.group(1).replace(',', ''))
            
            # Extract consensus rating
            consensus_match = re.search(r'Analyst Consensus:\s*<span[^>]*>(.*?)</span>', response.text)
            if consensus_match:
                data['analyst_consensus']['rating'] = consensus_match.group(1).strip()
            
            # Try to extract JSON-LD data (Svelte apps often embed data)
            json_ld = soup.find_all('script', type='application/ld+json')
            for script in json_ld:
                try:
                    ld_data = json.loads(script.string)
                    if ld_data.get('@type') == 'AggregateRating':
                        data['analyst_consensus']['score'] = ld_data.get('ratingValue')
                        data['analyst_consensus']['count'] = ld_data.get('ratingCount')
                except:
                    pass
            
            # Look for EPS/Revenue data in text
            eps_this_year = re.search(r'EPS This Year[^0-9]+([\d.]+)', text_content)
            eps_next_year = re.search(r'EPS Next Year[^0-9]+([\d.]+)', text_content)
            
            if eps_this_year:
                data['eps_estimates']['current_year'] = float(eps_this_year.group(1))
            if eps_next_year:
                data['eps_estimates']['next_year'] = float(eps_next_year.group(1))
            
            # Revenue estimates (in billions)
            rev_this = re.search(r'Revenue This Year[^0-9]+([\d.]+)B', text_content)
            rev_next = re.search(r'Revenue Next Year[^0-9]+([\d.]+)B', text_content)
            
            if rev_this:
                data['revenue_estimates']['current_year'] = float(rev_this.group(1)) * 1e9
            if rev_next:
                data['revenue_estimates']['next_year'] = float(rev_next.group(1)) * 1e9
            
            return data
            
        except requests.RequestException as e:
            return {'error': f'HTTP error: {str(e)}', 'ticker': ticker}
        except Exception as e:
            return {'error': f'Parse error: {str(e)}', 'ticker': ticker}
    
    def get_all_data(self, ticker: str) -> Dict[str, Any]:
        """Get all available forecast data"""
        return self.get_forecast(ticker)


def main():
    parser = argparse.ArgumentParser(description='StockAnalysis.com EPS Estimates Scraper')
    parser.add_argument('--ticker', '-t', required=True, help='Stock ticker symbol')
    parser.add_argument('--json', '-j', action='store_true', help='Output JSON format')
    
    args = parser.parse_args()
    
    scraper = StockAnalysisScraper()
    data = scraper.get_forecast(args.ticker)
    
    if args.json:
        print(json.dumps(data, indent=2, default=str))
    else:
        if 'error' in data:
            print(f"❌ Error: {data['error']}", file=sys.stderr)
            sys.exit(1)
        
        print(f"\n📊 StockAnalysis.com — {data['ticker']}")
        print("=" * 60)
        
        if data.get('price_target'):
            pt = data['price_target']
            print("\n🎯 Price Target:")
            if 'analyst_count' in pt:
                print(f"  Analysts: {pt['analyst_count']}")
            if 'average' in pt:
                print(f"  Average: ${pt['average']:.2f}")
            if 'low' in pt:
                print(f"  Low: ${pt['low']:.2f}")
            if 'high' in pt:
                print(f"  High: ${pt['high']:.2f}")
        
        if data.get('analyst_consensus'):
            cons = data['analyst_consensus']
            print("\n👥 Analyst Consensus:")
            if 'rating' in cons:
                print(f"  Rating: {cons['rating']}")
            if 'score' in cons:
                print(f"  Score: {cons['score']}/5")
        
        if data.get('eps_estimates'):
            eps = data['eps_estimates']
            print("\n📈 EPS Estimates:")
            for period, value in eps.items():
                print(f"  {period.replace('_', ' ').title()}: ${value:.2f}")
        
        if data.get('revenue_estimates'):
            rev = data['revenue_estimates']
            print("\n💰 Revenue Estimates:")
            for period, value in rev.items():
                print(f"  {period.replace('_', ' ').title()}: ${value/1e9:.2f}B")


if __name__ == '__main__':
    main()

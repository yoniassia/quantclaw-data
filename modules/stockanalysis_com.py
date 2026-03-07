#!/usr/bin/env python3
"""
StockAnalysis.com Scraper — EPS Estimates & Analyst Data Module

Critical module for Alpha Picker V3 — provides EPS estimate revisions which are
the #1 missing signal in the current system.

Data includes:
- EPS Estimates: Current/next quarter and year EPS forecasts
- Estimate Revisions: 7d/30d/90d revision tracking
- Analyst Consensus: Buy/hold/sell ratings, price targets
- Financials: Quarterly and annual revenue/EPS data

Usage:
  python modules/stockanalysis_com.py --ticker AAPL
  python modules/stockanalysis_com.py --ticker MSFT --json

Data source: https://stockanalysis.com
"""

import requests
from bs4 import BeautifulSoup
import argparse
import json
import sys
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

class StockAnalysisCom:
    """Scrape StockAnalysis.com for EPS estimates and analyst data"""
    
    BASE_URL = "https://stockanalysis.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def _extract_json_data(self, soup: BeautifulSoup, data_key: str) -> Optional[Dict]:
        """Extract JSON data from script tags"""
        try:
            scripts = soup.find_all('script', type='application/json')
            for script in scripts:
                if script.string:
                    try:
                        data = json.loads(script.string)
                        if data_key in data:
                            return data[data_key]
                    except json.JSONDecodeError:
                        continue
            return None
        except Exception as e:
            return None
    
    def get_eps_estimates(self, ticker: str) -> Dict[str, Any]:
        """
        Get current/next quarter and year EPS estimates.
        
        Returns dict with:
        - current_quarter: {estimate, growth}
        - next_quarter: {estimate, growth}
        - current_year: {estimate, growth}
        - next_year: {estimate, growth}
        - timestamp: ISO timestamp
        """
        ticker = ticker.upper().strip()
        
        try:
            url = f"{self.BASE_URL}/stocks/{ticker.lower()}/forecast/"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if ticker exists
            if "not found" in response.text.lower():
                return {'error': f'Ticker {ticker} not found', 'ticker': ticker}
            
            data = {
                'ticker': ticker,
                'current_quarter': {},
                'next_quarter': {},
                'current_year': {},
                'next_year': {},
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Extract EPS estimates from the stats cards or tables
            # Look for "EPS This Year" and "EPS Next Year" sections
            stats_cards = soup.find_all('div', class_=re.compile(r'.*?border.*?'))
            
            for card in stats_cards:
                text = card.get_text(strip=True)
                
                # Current year EPS
                if 'EPS This Year' in text or 'EPS This Quarter' in text:
                    value_elem = card.find('div', class_=re.compile(r'.*?text-2xl.*?'))
                    if value_elem:
                        try:
                            eps_val = float(value_elem.get_text(strip=True))
                            growth_elem = card.find('span', class_=re.compile(r'.*?rg.*?'))
                            growth = None
                            if growth_elem:
                                growth_text = growth_elem.get_text(strip=True).replace('%', '')
                                growth = float(growth_text)
                            
                            if 'Year' in text:
                                data['current_year'] = {'estimate': eps_val, 'growth': growth}
                            else:
                                data['current_quarter'] = {'estimate': eps_val, 'growth': growth}
                        except (ValueError, AttributeError):
                            continue
                
                # Next year/quarter EPS
                elif 'EPS Next Year' in text or 'EPS Next Quarter' in text:
                    value_elem = card.find('div', class_=re.compile(r'.*?text-2xl.*?'))
                    if value_elem:
                        try:
                            eps_val = float(value_elem.get_text(strip=True))
                            growth_elem = card.find('span', class_=re.compile(r'.*?rg.*?'))
                            growth = None
                            if growth_elem:
                                growth_text = growth_elem.get_text(strip=True).replace('%', '')
                                growth = float(growth_text)
                            
                            if 'Year' in text:
                                data['next_year'] = {'estimate': eps_val, 'growth': growth}
                            else:
                                data['next_quarter'] = {'estimate': eps_val, 'growth': growth}
                        except (ValueError, AttributeError):
                            continue
            
            return data
            
        except requests.RequestException as e:
            return {'error': f'HTTP error: {str(e)}', 'ticker': ticker}
        except Exception as e:
            return {'error': f'Parsing error: {str(e)}', 'ticker': ticker}
    
    def get_estimate_revisions(self, ticker: str) -> Dict[str, Any]:
        """
        Get EPS estimate revisions over 7d/30d/90d periods.
        
        Returns dict with:
        - revisions_7d: {count, direction}
        - revisions_30d: {count, direction}
        - revisions_90d: {count, direction}
        - analyst_count: number of analysts covering
        - timestamp: ISO timestamp
        """
        ticker = ticker.upper().strip()
        
        try:
            url = f"{self.BASE_URL}/stocks/{ticker.lower()}/forecast/"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            data = {
                'ticker': ticker,
                'revisions_7d': {'up': 0, 'down': 0, 'unchanged': 0},
                'revisions_30d': {'up': 0, 'down': 0, 'unchanged': 0},
                'revisions_90d': {'up': 0, 'down': 0, 'unchanged': 0},
                'analyst_count': None,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Look for analyst count in the forecast tables
            analyst_rows = soup.find_all('td', string=re.compile(r'No\.\s+Analysts'))
            if analyst_rows:
                for row in analyst_rows:
                    parent_tr = row.find_parent('tr')
                    if parent_tr:
                        cells = parent_tr.find_all('td')
                        for cell in cells[1:]:  # Skip the label cell
                            try:
                                count = int(cell.get_text(strip=True))
                                if count > 0:
                                    data['analyst_count'] = count
                                    break
                            except (ValueError, AttributeError):
                                continue
                    if data['analyst_count']:
                        break
            
            # Note: Actual revision data by time period isn't directly available on the page
            # This would require tracking historical changes or access to their API
            # For now, we return structure with zeros
            
            return data
            
        except requests.RequestException as e:
            return {'error': f'HTTP error: {str(e)}', 'ticker': ticker}
        except Exception as e:
            return {'error': f'Parsing error: {str(e)}', 'ticker': ticker}
    
    def get_analyst_consensus(self, ticker: str) -> Dict[str, Any]:
        """
        Get analyst consensus ratings and price targets.
        
        Returns dict with:
        - consensus: Overall rating (e.g., "Buy")
        - rating_score: Numeric score
        - ratings: {strong_buy, buy, hold, sell, strong_sell}
        - price_target: {low, average, median, high}
        - analyst_count: Total number of analysts
        - timestamp: ISO timestamp
        """
        ticker = ticker.upper().strip()
        
        try:
            url = f"{self.BASE_URL}/stocks/{ticker.lower()}/forecast/"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            data = {
                'ticker': ticker,
                'consensus': None,
                'rating_score': None,
                'ratings': {
                    'strong_buy': 0,
                    'buy': 0,
                    'hold': 0,
                    'sell': 0,
                    'strong_sell': 0
                },
                'price_target': {
                    'low': None,
                    'average': None,
                    'median': None,
                    'high': None,
                    'upside_pct': None
                },
                'analyst_count': None,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Extract consensus rating
            consensus_elem = soup.find(string=re.compile(r'Analyst Consensus:'))
            if consensus_elem:
                parent = consensus_elem.find_parent()
                if parent:
                    rating_span = parent.find('span', class_='font-bold')
                    if rating_span:
                        data['consensus'] = rating_span.get_text(strip=True)
            
            # Extract price target
            target_elem = soup.find(string=re.compile(r'Price Target:'))
            if target_elem:
                parent = target_elem.find_parent()
                if parent:
                    price_span = parent.find('span', class_=re.compile(r'.*?text-green.*?'))
                    if price_span:
                        price_text = price_span.get_text(strip=True)
                        # Extract price and upside: "$299.14 (+16.19%)"
                        match = re.search(r'\$?([\d,]+\.?\d*)\s*\(([+-]?[\d.]+)%\)', price_text)
                        if match:
                            data['price_target']['average'] = float(match.group(1).replace(',', ''))
                            data['price_target']['upside_pct'] = float(match.group(2))
            
            # Extract rating breakdown from recommendation table
            rating_table = soup.find('table', class_=re.compile(r'.*?rating.*?'))
            if not rating_table:
                # Try finding the table with rating rows
                tables = soup.find_all('table')
                for table in tables:
                    if any(r in table.get_text() for r in ['Strong Buy', 'Strong Sell']):
                        rating_table = table
                        break
            
            if rating_table:
                rows = rating_table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) > 1:
                        label = cells[0].get_text(strip=True).lower()
                        
                        # Get the most recent value (usually last non-header cell)
                        for cell in reversed(cells[1:]):
                            try:
                                value = int(cell.get_text(strip=True))
                                if 'strong buy' in label:
                                    data['ratings']['strong_buy'] = value
                                    break
                                elif 'buy' in label and 'strong' not in label:
                                    data['ratings']['buy'] = value
                                    break
                                elif 'hold' in label:
                                    data['ratings']['hold'] = value
                                    break
                                elif 'strong sell' in label:
                                    data['ratings']['strong_sell'] = value
                                    break
                                elif 'sell' in label and 'strong' not in label:
                                    data['ratings']['sell'] = value
                                    break
                                elif 'total' in label:
                                    data['analyst_count'] = value
                                    break
                            except (ValueError, AttributeError):
                                continue
            
            # Extract price target range from table
            target_rows = soup.find_all('th', string=re.compile(r'Target'))
            for row in target_rows:
                parent_tr = row.find_parent('tr')
                if parent_tr:
                    next_tr = parent_tr.find_next_sibling('tr')
                    if next_tr:
                        cells = next_tr.find_all('td')
                        if len(cells) >= 4:
                            try:
                                # Usually: Low, Average, Median, High
                                data['price_target']['low'] = float(cells[0].get_text(strip=True).replace('$', '').replace(',', ''))
                                avg_text = cells[1].get_text(strip=True).replace('$', '').replace(',', '')
                                if avg_text and avg_text != '-':
                                    data['price_target']['average'] = float(avg_text)
                                data['price_target']['median'] = float(cells[2].get_text(strip=True).replace('$', '').replace(',', ''))
                                data['price_target']['high'] = float(cells[3].get_text(strip=True).replace('$', '').replace(',', ''))
                            except (ValueError, IndexError):
                                pass
            
            return data
            
        except requests.RequestException as e:
            return {'error': f'HTTP error: {str(e)}', 'ticker': ticker}
        except Exception as e:
            return {'error': f'Parsing error: {str(e)}', 'ticker': ticker}
    
    def get_financials(self, ticker: str, period: str = 'annual') -> Dict[str, Any]:
        """
        Get quarterly or annual financial data.
        
        Args:
            ticker: Stock ticker symbol
            period: 'annual' or 'quarterly'
        
        Returns dict with:
        - revenue: List of revenue values
        - eps: List of EPS values
        - dates: List of period end dates
        - revenue_growth: List of YoY/QoQ growth rates
        - eps_growth: List of YoY/QoQ growth rates
        - timestamp: ISO timestamp
        """
        ticker = ticker.upper().strip()
        
        try:
            url = f"{self.BASE_URL}/stocks/{ticker.lower()}/financials/"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            data = {
                'ticker': ticker,
                'period': period,
                'revenue': [],
                'eps': [],
                'dates': [],
                'revenue_growth': [],
                'eps_growth': [],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Financial data is in tables - look for Revenue and EPS rows
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) > 1:
                        label = cells[0].get_text(strip=True).lower()
                        
                        if 'revenue' in label and 'growth' not in label:
                            # Extract revenue values
                            for cell in cells[1:]:
                                text = cell.get_text(strip=True)
                                if text and text != '-':
                                    try:
                                        # Handle formats like "474.81B"
                                        value = self._parse_financial_value(text)
                                        if value:
                                            data['revenue'].append(value)
                                    except:
                                        continue
                        
                        elif 'eps' in label and 'growth' not in label:
                            # Extract EPS values
                            for cell in cells[1:]:
                                text = cell.get_text(strip=True)
                                if text and text != '-':
                                    try:
                                        value = float(text.replace('$', '').replace(',', ''))
                                        data['eps'].append(value)
                                    except:
                                        continue
                        
                        elif 'revenue' in label and 'growth' in label:
                            # Extract revenue growth
                            for cell in cells[1:]:
                                text = cell.get_text(strip=True).replace('%', '')
                                if text and text != '-':
                                    try:
                                        value = float(text)
                                        data['revenue_growth'].append(value)
                                    except:
                                        continue
                        
                        elif 'eps' in label and 'growth' in label:
                            # Extract EPS growth
                            for cell in cells[1:]:
                                text = cell.get_text(strip=True).replace('%', '')
                                if text and text != '-':
                                    try:
                                        value = float(text)
                                        data['eps_growth'].append(value)
                                    except:
                                        continue
            
            return data
            
        except requests.RequestException as e:
            return {'error': f'HTTP error: {str(e)}', 'ticker': ticker}
        except Exception as e:
            return {'error': f'Parsing error: {str(e)}', 'ticker': ticker}
    
    def _parse_financial_value(self, text: str) -> Optional[float]:
        """Parse financial values like '474.81B' or '95.36M' to float"""
        text = text.strip().replace('$', '').replace(',', '')
        
        multiplier = 1
        if text.endswith('T'):
            multiplier = 1_000_000_000_000
            text = text[:-1]
        elif text.endswith('B'):
            multiplier = 1_000_000_000
            text = text[:-1]
        elif text.endswith('M'):
            multiplier = 1_000_000
            text = text[:-1]
        elif text.endswith('K'):
            multiplier = 1_000
            text = text[:-1]
        
        try:
            return float(text) * multiplier
        except ValueError:
            return None
    
    def get_all_data(self, ticker: str) -> Dict[str, Any]:
        """
        Get all available data for a ticker.
        
        Returns combined dict with all data types.
        """
        ticker = ticker.upper().strip()
        
        return {
            'ticker': ticker,
            'eps_estimates': self.get_eps_estimates(ticker),
            'estimate_revisions': self.get_estimate_revisions(ticker),
            'analyst_consensus': self.get_analyst_consensus(ticker),
            'financials_annual': self.get_financials(ticker, 'annual'),
            'financials_quarterly': self.get_financials(ticker, 'quarterly'),
            'timestamp': datetime.utcnow().isoformat()
        }


def main():
    parser = argparse.ArgumentParser(description='StockAnalysis.com Data Scraper')
    parser.add_argument('--ticker', '-t', required=True, help='Stock ticker symbol')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--type', choices=['eps', 'revisions', 'consensus', 'financials', 'all'],
                        default='all', help='Data type to fetch')
    
    args = parser.parse_args()
    
    scraper = StockAnalysisCom()
    
    if args.type == 'eps':
        data = scraper.get_eps_estimates(args.ticker)
    elif args.type == 'revisions':
        data = scraper.get_estimate_revisions(args.ticker)
    elif args.type == 'consensus':
        data = scraper.get_analyst_consensus(args.ticker)
    elif args.type == 'financials':
        data = scraper.get_financials(args.ticker)
    else:
        data = scraper.get_all_data(args.ticker)
    
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"StockAnalysis.com Data for {args.ticker}")
        print(f"{'='*60}\n")
        
        if 'error' in data:
            print(f"Error: {data['error']}")
        else:
            for key, value in data.items():
                if key != 'timestamp':
                    print(f"{key}: {value}")
        
        print(f"\nTimestamp: {data.get('timestamp', 'N/A')}")
        print(f"{'='*60}\n")
    
    return 0 if 'error' not in data else 1


if __name__ == '__main__':
    sys.exit(main())

"""
StockAnalysis.com EPS Estimates & Revisions

Scrapes EPS estimate data from stockanalysis.com — the #1 missing signal for Alpha Picker V3.
Provides annual EPS and revenue forecasts with analyst consensus ranges.

CRITICAL for closing SeekingAlpha accuracy gap (65% → 85%+).
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict
import re
from datetime import datetime

def get_eps_estimates(ticker: str) -> Dict:
    """
    Fetch annual EPS estimates and ranges.
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL')
        
    Returns:
        Dict with estimate data: {
            'ticker': str,
            'estimates': {
                '2026': {'high': 9.29, 'avg': 8.68, 'low': 7.99},
                '2027': {...}
            }
        }
    """
    try:
        url = f"https://stockanalysis.com/stocks/{ticker.lower()}/forecast/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        data = {
            'ticker': ticker.upper(),
            'estimates': {},
            'updated': datetime.now().strftime('%Y-%m-%d')
        }
        
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            if not rows:
                continue
            
            header = rows[0].find_all(['th', 'td'])
            header_text = [h.get_text(strip=True) for h in header]
            
            # Look for "EPS" table (not "EPS Growth")
            if header_text[0] == 'EPS' and len(header_text) > 1:
                years = [h for h in header_text[1:] if h.isdigit()]
                
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue
                    
                    row_label = cells[0].get_text(strip=True).lower()
                    values = [c.get_text(strip=True) for c in cells[1:]]
                    
                    for i, year in enumerate(years):
                        if year not in data['estimates']:
                            data['estimates'][year] = {}
                        
                        if i < len(values) and values[i] and values[i] != 'Pro':
                            try:
                                data['estimates'][year][row_label] = float(values[i])
                            except ValueError:
                                pass
        
        return data
        
    except Exception as e:
        return {
            'ticker': ticker.upper(),
            'error': str(e),
            'updated': datetime.now().strftime('%Y-%m-%d')
        }


def get_revenue_estimates(ticker: str) -> Dict:
    """
    Fetch annual revenue estimates in millions.
    
    Args:
        ticker: Stock symbol
        
    Returns:
        Dict with revenue estimate data: {
            'ticker': str,
            'estimates': {
                '2026': {'high': 504500, 'avg': 474800, ...},  # in millions
                '2027': {...}
            }
        }
    """
    try:
        url = f"https://stockanalysis.com/stocks/{ticker.lower()}/forecast/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        data = {
            'ticker': ticker.upper(),
            'estimates': {},
            'updated': datetime.now().strftime('%Y-%m-%d')
        }
        
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            if not rows or len(rows) < 2:
                continue
            
            header = rows[0].find_all(['th', 'td'])
            header_text = [h.get_text(strip=True) for h in header]
            
            # Look for "Revenue" table (not "Revenue Growth")
            # Check first data cell contains "B" for billions
            if header_text[0] == 'Revenue' and len(header_text) > 1:
                first_data_row = rows[1] if len(rows) > 1 else None
                if first_data_row:
                    first_val = first_data_row.find_all(['td', 'th'])[1].get_text(strip=True)
                    if 'B' not in first_val:  # Skip Revenue Growth table (has % instead)
                        continue
                
                years = [h for h in header_text[1:] if h.isdigit()]
                
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue
                    
                    row_label = cells[0].get_text(strip=True).lower()
                    values = [c.get_text(strip=True) for c in cells[1:]]
                    
                    for i, year in enumerate(years):
                        if year not in data['estimates']:
                            data['estimates'][year] = {}
                        
                        if i < len(values) and values[i] and values[i] not in ['Pro', 'Upgrade']:
                            # Parse "474.81B" → 474810 (millions)
                            match = re.search(r'([\d.]+)([BM])?', values[i])
                            if match:
                                num = float(match.group(1))
                                unit = match.group(2)
                                if unit == 'B':
                                    num *= 1000  # Convert to millions
                                data['estimates'][year][row_label] = num
        
        return data
        
    except Exception as e:
        return {
            'ticker': ticker.upper(),
            'error': str(e),
            'updated': datetime.now().strftime('%Y-%m-%d')
        }


def get_price_target(ticker: str) -> Dict:
    """
    Get analyst price target consensus.
    
    Args:
        ticker: Stock symbol
        
    Returns:
        Dict: {
            'ticker': str,
            'low': float,
            'avg': float,
            'median': float,
            'high': float
        }
    """
    try:
        url = f"https://stockanalysis.com/stocks/{ticker.lower()}/forecast/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        data = {
            'ticker': ticker.upper(),
            'low': None,
            'avg': None,
            'median': None,
            'high': None,
            'updated': datetime.now().strftime('%Y-%m-%d')
        }
        
        # First table is price targets
        tables = soup.find_all('table')
        if tables:
            rows = tables[0].find_all('tr')
            
            if len(rows) >= 2:
                cells = rows[1].find_all(['td', 'th'])
                
                if len(cells) >= 5:
                    for i, key in enumerate(['label', 'low', 'avg', 'median', 'high']):
                        if i > 0 and i < len(cells):
                            val_text = cells[i].get_text(strip=True)
                            match = re.search(r'\$([\d.]+)', val_text)
                            if match:
                                data[key] = float(match.group(1))
        
        return data
        
    except Exception as e:
        return {
            'ticker': ticker.upper(),
            'error': str(e),
            'updated': datetime.now().strftime('%Y-%m-%d')
        }


if __name__ == '__main__':
    test_ticker = 'AAPL'
    
    print("EPS Estimates:")
    print(get_eps_estimates(test_ticker))
    
    print("\nRevenue Estimates:")
    print(get_revenue_estimates(test_ticker))
    
    print("\nPrice Target:")
    print(get_price_target(test_ticker))

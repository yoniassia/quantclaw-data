#!/usr/bin/env python3
"""
Finviz Stock Screener — Phase 701
Consolidated fundamentals + technicals + insider data for 8000+ stocks via scraping.

Data includes:
- Fundamentals: P/E, P/B, PEG, Debt/Eq, ROE, ROA, profit margin
- Technicals: RSI, ATR, 50/200 SMA, price vs MA, volume
- Insider: Insider ownership %, insider transactions, institutional ownership %
- Analyst: Target price, recommendation (1-5 scale), analyst count
- Performance: YTD, 1M, 3M, 6M, 1Y returns
- Short: Short float %, short ratio

Usage:
  python modules/finviz_screener.py --ticker AAPL
  python modules/finviz_screener.py --ticker TSLA --json

Data source: https://finviz.com/quote.ashx?t={ticker}
"""

import requests
from bs4 import BeautifulSoup
import argparse
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import re

class FinvizScreener:
    """Scrape Finviz for comprehensive stock data"""
    
    BASE_URL = "https://finviz.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_stock_data(self, ticker: str) -> Dict[str, Any]:
        """
        Get comprehensive stock data from Finviz.
        
        Returns dict with:
        - fundamentals: {pe, pb, peg, debt_eq, roe, roa, profit_margin, ...}
        - technicals: {rsi, atr, sma50, sma200, price_vs_sma50, ...}
        - insider: {insider_own_pct, insider_trans, inst_own_pct, inst_trans}
        - analyst: {target_price, recommendation, analyst_count}
        - performance: {ytd, m1, m3, m6, y1}
        - short: {short_float_pct, short_ratio}
        - valuation: {market_cap, enterprise_value, revenue, earnings}
        - timestamp: ISO timestamp
        """
        ticker = ticker.upper().strip()
        
        try:
            url = f"{self.BASE_URL}/quote.ashx?t={ticker}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if ticker is valid
            if "not found" in response.text.lower() or soup.find(string=re.compile(r'No such ticker', re.I)):
                return {'error': f'Ticker {ticker} not found', 'ticker': ticker}
            
            data = {
                'ticker': ticker,
                'fundamentals': {},
                'technicals': {},
                'insider': {},
                'analyst': {},
                'performance': {},
                'short': {},
                'valuation': {},
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Parse the main data table (snapshot-table2)
            table = soup.find('table', class_='snapshot-table2')
            if not table:
                return {'error': 'Could not find data table', 'ticker': ticker}
            
            # Extract all key-value pairs from the table
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                for i in range(0, len(cells) - 1, 2):
                    if i + 1 < len(cells):
                        key = cells[i].get_text(strip=True)
                        value = cells[i+1].get_text(strip=True)
                        
                        # Map to data structure
                        self._parse_field(key, value, data)
            
            return data
            
        except requests.RequestException as e:
            return {'error': f'HTTP error: {str(e)}', 'ticker': ticker}
        except Exception as e:
            return {'error': f'Parsing error: {str(e)}', 'ticker': ticker}
    
    def _parse_field(self, key: str, value: str, data: Dict):
        """Parse a field and add to appropriate data section"""
        # Fundamentals
        if key == 'P/E':
            data['fundamentals']['pe'] = self._parse_float(value)
        elif key == 'P/B':
            data['fundamentals']['pb'] = self._parse_float(value)
        elif key == 'PEG':
            data['fundamentals']['peg'] = self._parse_float(value)
        elif key == 'Debt/Eq':
            data['fundamentals']['debt_eq'] = self._parse_float(value)
        elif key == 'ROE':
            data['fundamentals']['roe'] = self._parse_pct(value)
        elif key == 'ROA':
            data['fundamentals']['roa'] = self._parse_pct(value)
        elif key == 'Profit Margin' or key == 'Profit M':
            data['fundamentals']['profit_margin'] = self._parse_pct(value)
        elif key == 'Oper. Margin':
            data['fundamentals']['operating_margin'] = self._parse_pct(value)
        elif key == 'Gross Margin':
            data['fundamentals']['gross_margin'] = self._parse_pct(value)
        elif key == 'Dividend' or key == 'Dividend %':
            data['fundamentals']['dividend_yield'] = self._parse_pct(value)
        elif key == 'EPS (ttm)':
            data['fundamentals']['eps_ttm'] = self._parse_float(value)
        elif key == 'EPS next Y':
            data['fundamentals']['eps_next_year'] = self._parse_float(value)
        
        # Technicals
        elif key == 'RSI (14)':
            data['technicals']['rsi_14'] = self._parse_float(value)
        elif key == 'ATR':
            data['technicals']['atr'] = self._parse_float(value)
        elif key == 'SMA50':
            data['technicals']['sma50'] = self._parse_float(value)
        elif key == 'SMA200':
            data['technicals']['sma200'] = self._parse_float(value)
        elif key == 'Price':
            data['technicals']['price'] = self._parse_float(value)
        elif key == 'Change':
            data['technicals']['change_pct'] = self._parse_pct(value)
        elif key == 'Volume':
            data['technicals']['volume'] = self._parse_volume(value)
        elif key == 'Avg Volume':
            data['technicals']['avg_volume'] = self._parse_volume(value)
        elif key == 'Beta':
            data['technicals']['beta'] = self._parse_float(value)
        
        # Insider & Institutional
        elif key == 'Insider Own':
            data['insider']['insider_own_pct'] = self._parse_pct(value)
        elif key == 'Insider Trans':
            data['insider']['insider_trans'] = value
        elif key == 'Inst Own':
            data['insider']['inst_own_pct'] = self._parse_pct(value)
        elif key == 'Inst Trans':
            data['insider']['inst_trans'] = value
        
        # Analyst
        elif key == 'Target Price':
            data['analyst']['target_price'] = self._parse_float(value)
        elif key == 'Recom':
            data['analyst']['recommendation'] = self._parse_float(value)
        
        # Performance
        elif key == 'Perf Week':
            data['performance']['week'] = self._parse_pct(value)
        elif key == 'Perf Month':
            data['performance']['month'] = self._parse_pct(value)
        elif key == 'Perf Quarter' or key == 'Perf Quart':
            data['performance']['quarter'] = self._parse_pct(value)
        elif key == 'Perf Half Y':
            data['performance']['half_year'] = self._parse_pct(value)
        elif key == 'Perf Year':
            data['performance']['year'] = self._parse_pct(value)
        elif key == 'Perf YTD':
            data['performance']['ytd'] = self._parse_pct(value)
        
        # Short Interest
        elif key == 'Short Float' or key == 'Short Float%':
            data['short']['short_float_pct'] = self._parse_pct(value)
        elif key == 'Short Ratio':
            data['short']['short_ratio'] = self._parse_float(value)
        
        # Valuation
        elif key == 'Market Cap':
            data['valuation']['market_cap'] = self._parse_volume(value)
        elif key == 'Income':
            data['valuation']['income'] = self._parse_volume(value)
        elif key == 'Sales':
            data['valuation']['sales'] = self._parse_volume(value)
        elif key == 'Book/sh':
            data['valuation']['book_per_share'] = self._parse_float(value)
        elif key == 'Cash/sh':
            data['valuation']['cash_per_share'] = self._parse_float(value)
        elif key == 'EPS next Q':
            data['valuation']['eps_next_quarter'] = self._parse_float(value)
    
    def _parse_float(self, text: str) -> Optional[float]:
        """Parse float from text"""
        if not text or text == '-':
            return None
        try:
            return float(text.replace(',', '').replace('%', '').strip())
        except ValueError:
            return None
    
    def _parse_pct(self, text: str) -> Optional[float]:
        """Parse percentage to decimal (e.g., '5.2%' -> 5.2)"""
        if not text or text == '-':
            return None
        try:
            return float(text.replace('%', '').replace(',', '').strip())
        except ValueError:
            return None
    
    def _parse_volume(self, text: str) -> Optional[float]:
        """Parse volume/market cap with B/M/K suffixes"""
        if not text or text == '-':
            return None
        
        clean = text.replace(',', '').strip()
        multiplier = 1.0
        
        if clean.endswith('B'):
            multiplier = 1e9
            clean = clean[:-1]
        elif clean.endswith('M'):
            multiplier = 1e6
            clean = clean[:-1]
        elif clean.endswith('K'):
            multiplier = 1e3
            clean = clean[:-1]
        
        try:
            return float(clean) * multiplier
        except ValueError:
            return None

def main():
    parser = argparse.ArgumentParser(
        description='Finviz Stock Screener — Comprehensive Stock Data'
    )
    parser.add_argument('--ticker', type=str, required=True,
                       help='Stock ticker symbol')
    parser.add_argument('--json', action='store_true',
                       help='Output raw JSON')
    
    args = parser.parse_args()
    
    screener = FinvizScreener()
    data = screener.get_stock_data(args.ticker)
    
    if args.json:
        print(json.dumps(data, indent=2))
        return
    
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
        sys.exit(1)
    
    # Pretty print
    print(f"\n{'='*60}")
    print(f"📊 {data['ticker']} — Finviz Screener Data")
    print(f"{'='*60}\n")
    
    # Fundamentals
    fund = data.get('fundamentals', {})
    if fund:
        print("💰 Fundamentals:")
        if fund.get('pe'):
            print(f"  P/E:             {fund['pe']:.2f}")
        if fund.get('pb'):
            print(f"  P/B:             {fund['pb']:.2f}")
        if fund.get('eps_ttm'):
            print(f"  EPS (TTM):       ${fund['eps_ttm']:.2f}")
        if fund.get('roe'):
            print(f"  ROE:             {fund['roe']:.1f}%")
        if fund.get('debt_eq'):
            print(f"  Debt/Equity:     {fund['debt_eq']:.2f}")
        print()
    
    # Technicals
    tech = data.get('technicals', {})
    if tech:
        print("📈 Technicals:")
        if tech.get('price'):
            print(f"  Price:           ${tech['price']:.2f}")
        if tech.get('rsi_14'):
            print(f"  RSI(14):         {tech['rsi_14']:.1f}")
        if tech.get('beta'):
            print(f"  Beta:            {tech['beta']:.2f}")
        print()
    
    # Short Interest
    short = data.get('short', {})
    if short:
        print("🔻 Short Interest:")
        if short.get('short_float_pct'):
            print(f"  Short Float:     {short['short_float_pct']:.2f}%")
        if short.get('short_ratio'):
            print(f"  Short Ratio:     {short['short_ratio']:.1f}")
        print()
    
    # Performance
    perf = data.get('performance', {})
    if perf:
        print("📊 Performance:")
        if perf.get('ytd'):
            print(f"  YTD:             {perf['ytd']:+.2f}%")
        if perf.get('year'):
            print(f"  1 Year:          {perf['year']:+.2f}%")
        print()
    
    print(f"Last updated: {data['timestamp']}")
    print()

if __name__ == '__main__':
    main()

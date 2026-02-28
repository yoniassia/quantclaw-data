"""
OpenInsider SEC Form 4 Insider Trading Tracker
Real-time insider trading filings from openinsider.com
No API key required — web scraping

Data points:
- Filing date, trade date, ticker, insider name, title
- Transaction type (Buy/Sell/Option Exercise)
- Price, shares, dollar value
- Ownership stake change
- Cluster buy detection (multiple insiders buying same stock)

Source: http://openinsider.com
Last update: 2026-02-28
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional
import json


class OpenInsiderTracker:
    """OpenInsider.com SEC Form 4 insider trading scraper"""
    
    BASE_URL = "http://openinsider.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_latest_filings(self, days: int = 7, min_value: int = 25000) -> pd.DataFrame:
        """
        Get latest insider purchases
        
        Args:
            days: Look back period (default 7)
            min_value: Minimum transaction value in USD (default $25k)
        
        Returns:
            DataFrame with filing details
        """
        url = f"{self.BASE_URL}/latest-insider-purchases"
        
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            table = soup.find('table', class_='tinytable')
            
            if not table:
                return pd.DataFrame()
            
            rows = []
            for tr in table.find_all('tr')[1:]:  # Skip header
                cols = tr.find_all('td')
                if len(cols) < 11:
                    continue
                
                # Parse data
                filing_date = cols[1].text.strip()
                trade_date = cols[2].text.strip()
                ticker = cols[3].text.strip()
                company = cols[4].text.strip()
                insider = cols[5].text.strip()
                title = cols[6].text.strip()
                trade_type = cols[7].text.strip()
                price = cols[8].text.strip()
                qty = cols[9].text.strip()
                owned = cols[10].text.strip()
                value = cols[11].text.strip() if len(cols) > 11 else ""
                
                # Convert value to int for filtering
                try:
                    value_int = int(value.replace('$', '').replace(',', '').replace('+', ''))
                except:
                    value_int = 0
                
                if value_int < min_value:
                    continue
                
                rows.append({
                    'filing_date': filing_date,
                    'trade_date': trade_date,
                    'ticker': ticker,
                    'company': company,
                    'insider_name': insider,
                    'title': title,
                    'trade_type': trade_type,
                    'price': price,
                    'shares': qty,
                    'shares_owned': owned,
                    'value_usd': value,
                    'value_int': value_int
                })
            
            df = pd.DataFrame(rows)
            
            # Filter by date
            if not df.empty and days:
                cutoff = datetime.now() - timedelta(days=days)
                df['filing_dt'] = pd.to_datetime(df['filing_date'], errors='coerce')
                df = df[df['filing_dt'] >= cutoff]
                df = df.drop('filing_dt', axis=1)
            
            return df.sort_values('value_int', ascending=False)
            
        except Exception as e:
            print(f"Error scraping OpenInsider: {e}")
            return pd.DataFrame()
    
    def detect_cluster_buys(self, days: int = 30, min_insiders: int = 2) -> pd.DataFrame:
        """
        Detect cluster buying — multiple insiders buying same stock
        Strong bullish signal
        
        Args:
            days: Look back period
            min_insiders: Minimum number of insiders (default 2)
        
        Returns:
            DataFrame with ticker, insider_count, total_value, avg_price
        """
        df = self.get_latest_filings(days=days, min_value=0)
        
        if df.empty:
            return pd.DataFrame()
        
        # Group by ticker and count unique insiders
        clusters = df.groupby('ticker').agg({
            'insider_name': 'nunique',
            'value_int': 'sum',
            'price': lambda x: pd.to_numeric(x.str.replace('$', '').str.replace(',', ''), errors='coerce').mean(),
            'company': 'first'
        }).reset_index()
        
        clusters.columns = ['ticker', 'insider_count', 'total_value_usd', 'avg_price', 'company']
        
        # Filter by minimum insiders
        clusters = clusters[clusters['insider_count'] >= min_insiders]
        clusters = clusters.sort_values('insider_count', ascending=False)
        
        return clusters
    
    def get_top_insider_trades(self, limit: int = 50) -> pd.DataFrame:
        """
        Get highest-value insider purchases
        
        Args:
            limit: Maximum number of trades to return
        
        Returns:
            DataFrame sorted by transaction value
        """
        url = f"{self.BASE_URL}/top-insider-purchases-by-dollar-value"
        
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            table = soup.find('table', class_='tinytable')
            
            if not table:
                return pd.DataFrame()
            
            rows = []
            for tr in table.find_all('tr')[1:limit+1]:
                cols = tr.find_all('td')
                if len(cols) < 11:
                    continue
                
                rows.append({
                    'filing_date': cols[1].text.strip(),
                    'trade_date': cols[2].text.strip(),
                    'ticker': cols[3].text.strip(),
                    'company': cols[4].text.strip(),
                    'insider_name': cols[5].text.strip(),
                    'title': cols[6].text.strip(),
                    'trade_type': cols[7].text.strip(),
                    'price': cols[8].text.strip(),
                    'shares': cols[9].text.strip(),
                    'shares_owned': cols[10].text.strip(),
                    'value_usd': cols[11].text.strip() if len(cols) > 11 else ""
                })
            
            return pd.DataFrame(rows)
            
        except Exception as e:
            print(f"Error scraping top trades: {e}")
            return pd.DataFrame()
    
    def get_ticker_insider_history(self, ticker: str, days: int = 90) -> pd.DataFrame:
        """
        Get all insider trades for a specific ticker
        
        Args:
            ticker: Stock ticker symbol
            days: Look back period
        
        Returns:
            DataFrame with all insider trades for the ticker
        """
        url = f"{self.BASE_URL}/screener?s={ticker.upper()}"
        
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            table = soup.find('table', class_='tinytable')
            
            if not table:
                return pd.DataFrame()
            
            rows = []
            for tr in table.find_all('tr')[1:]:
                cols = tr.find_all('td')
                if len(cols) < 11:
                    continue
                
                rows.append({
                    'filing_date': cols[1].text.strip(),
                    'trade_date': cols[2].text.strip(),
                    'ticker': cols[3].text.strip(),
                    'company': cols[4].text.strip(),
                    'insider_name': cols[5].text.strip(),
                    'title': cols[6].text.strip(),
                    'trade_type': cols[7].text.strip(),
                    'price': cols[8].text.strip(),
                    'shares': cols[9].text.strip(),
                    'shares_owned': cols[10].text.strip(),
                    'value_usd': cols[11].text.strip() if len(cols) > 11 else ""
                })
            
            df = pd.DataFrame(rows)
            
            # Filter by date
            if not df.empty and days:
                cutoff = datetime.now() - timedelta(days=days)
                df['filing_dt'] = pd.to_datetime(df['filing_date'], errors='coerce')
                df = df[df['filing_dt'] >= cutoff]
                df = df.drop('filing_dt', axis=1)
            
            return df
            
        except Exception as e:
            print(f"Error scraping ticker {ticker}: {e}")
            return pd.DataFrame()
    
    def analyze_insider_sentiment(self, ticker: str, days: int = 90) -> Dict:
        """
        Analyze buy/sell sentiment for a ticker
        
        Args:
            ticker: Stock ticker
            days: Look back period
        
        Returns:
            Dict with buy_count, sell_count, net_sentiment, total_buy_value, total_sell_value
        """
        df = self.get_ticker_insider_history(ticker, days)
        
        if df.empty:
            return {
                'ticker': ticker,
                'buy_count': 0,
                'sell_count': 0,
                'net_sentiment': 'neutral',
                'total_buy_value': 0,
                'total_sell_value': 0,
                'confidence': 'low'
            }
        
        # Classify trades
        buys = df[df['trade_type'].str.contains('P-Purchase', case=False, na=False)]
        sells = df[df['trade_type'].str.contains('S-Sale', case=False, na=False)]
        
        # Calculate values
        try:
            buy_value = buys['value_usd'].str.replace('$', '').str.replace(',', '').str.replace('+', '').astype(float).sum()
            sell_value = sells['value_usd'].str.replace('$', '').str.replace(',', '').str.replace('+', '').astype(float).sum()
        except:
            buy_value = 0
            sell_value = 0
        
        buy_count = len(buys)
        sell_count = len(sells)
        
        # Determine sentiment
        if buy_count > sell_count * 2 or buy_value > sell_value * 2:
            sentiment = 'bullish'
            confidence = 'high' if buy_count >= 3 else 'medium'
        elif sell_count > buy_count * 2 or sell_value > buy_value * 2:
            sentiment = 'bearish'
            confidence = 'high' if sell_count >= 3 else 'medium'
        else:
            sentiment = 'neutral'
            confidence = 'low'
        
        return {
            'ticker': ticker.upper(),
            'buy_count': buy_count,
            'sell_count': sell_count,
            'net_sentiment': sentiment,
            'total_buy_value': f"${buy_value:,.0f}",
            'total_sell_value': f"${sell_value:,.0f}",
            'confidence': confidence,
            'days_analyzed': days
        }


def main():
    """CLI dispatcher"""
    import sys
    
    if len(sys.argv) < 2:
        print("Error: Missing command")
        return 1
    
    command = sys.argv[1]
    tracker = OpenInsiderTracker()
    
    try:
        if command == 'insider-latest':
            days = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 7
            min_value = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 25000
            
            # Check for flags
            if '--days' in sys.argv:
                days_idx = sys.argv.index('--days')
                if days_idx + 1 < len(sys.argv):
                    days = int(sys.argv[days_idx + 1])
            if '--min-value' in sys.argv:
                val_idx = sys.argv.index('--min-value')
                if val_idx + 1 < len(sys.argv):
                    min_value = int(sys.argv[val_idx + 1])
            
            df = tracker.get_latest_filings(days=days, min_value=min_value)
            if df.empty:
                print(f"No insider purchases found in last {days} days with min value ${min_value:,}")
                return 0
            
            print(f"\n{'='*80}")
            print(f"LATEST INSIDER PURCHASES (Last {days} Days, Min ${min_value:,})")
            print(f"{'='*80}\n")
            
            for _, row in df.head(20).iterrows():
                print(f"📈 {row['ticker']} - {row['company']}")
                print(f"   Insider: {row['insider_name']} ({row['title']})")
                print(f"   Trade: {row['value_usd']} @ {row['price']}/share ({row['shares']} shares)")
                print(f"   Filed: {row['filing_date']} | Trade Date: {row['trade_date']}")
                print(f"   Now Owns: {row['shares_owned']} shares\n")
        
        elif command == 'insider-clusters':
            days = 30
            min_insiders = 2
            
            if '--days' in sys.argv:
                days_idx = sys.argv.index('--days')
                if days_idx + 1 < len(sys.argv):
                    days = int(sys.argv[days_idx + 1])
            if '--min-insiders' in sys.argv:
                min_idx = sys.argv.index('--min-insiders')
                if min_idx + 1 < len(sys.argv):
                    min_insiders = int(sys.argv[min_idx + 1])
            
            df = tracker.detect_cluster_buys(days=days, min_insiders=min_insiders)
            if df.empty:
                print(f"No cluster buys detected (min {min_insiders} insiders in last {days} days)")
                return 0
            
            print(f"\n{'='*80}")
            print(f"CLUSTER BUYING DETECTED (Last {days} Days)")
            print(f"{'='*80}\n")
            
            for _, row in df.head(15).iterrows():
                print(f"🔥 {row['ticker']} - {row['company']}")
                print(f"   {row['insider_count']} insiders bought")
                print(f"   Total Value: ${row['total_value_usd']:,.0f}")
                print(f"   Avg Price: ${row['avg_price']:.2f}\n")
        
        elif command == 'insider-top':
            limit = 50
            if '--limit' in sys.argv:
                limit_idx = sys.argv.index('--limit')
                if limit_idx + 1 < len(sys.argv):
                    limit = int(sys.argv[limit_idx + 1])
            
            df = tracker.get_top_insider_trades(limit=limit)
            if df.empty:
                print("No top insider trades found")
                return 0
            
            print(f"\n{'='*80}")
            print(f"TOP INSIDER PURCHASES BY DOLLAR VALUE")
            print(f"{'='*80}\n")
            
            for _, row in df.head(limit).iterrows():
                print(f"💰 {row['ticker']} - {row['company']}")
                print(f"   Insider: {row['insider_name']} ({row['title']})")
                print(f"   Value: {row['value_usd']} @ {row['price']}/share")
                print(f"   Filed: {row['filing_date']}\n")
        
        elif command == 'insider-ticker':
            if len(sys.argv) < 3:
                print("Error: Missing ticker symbol")
                print("Usage: python cli.py insider-ticker TICKER [--days 90]")
                return 1
            
            ticker = sys.argv[2].upper()
            days = 90
            
            if '--days' in sys.argv:
                days_idx = sys.argv.index('--days')
                if days_idx + 1 < len(sys.argv):
                    days = int(sys.argv[days_idx + 1])
            
            df = tracker.get_ticker_insider_history(ticker, days=days)
            if df.empty:
                print(f"No insider trades found for {ticker} in last {days} days")
                return 0
            
            print(f"\n{'='*80}")
            print(f"{ticker} INSIDER TRADING HISTORY (Last {days} Days)")
            print(f"{'='*80}\n")
            
            for _, row in df.iterrows():
                print(f"{row['trade_type']} | {row['insider_name']} ({row['title']})")
                print(f"   {row['value_usd']} @ {row['price']}/share ({row['shares']} shares)")
                print(f"   Filed: {row['filing_date']} | Trade: {row['trade_date']}\n")
        
        elif command == 'insider-sentiment':
            if len(sys.argv) < 3:
                print("Error: Missing ticker symbol")
                print("Usage: python cli.py insider-sentiment TICKER [--days 90]")
                return 1
            
            ticker = sys.argv[2].upper()
            days = 90
            
            if '--days' in sys.argv:
                days_idx = sys.argv.index('--days')
                if days_idx + 1 < len(sys.argv):
                    days = int(sys.argv[days_idx + 1])
            
            result = tracker.analyze_insider_sentiment(ticker, days=days)
            
            print(f"\n{'='*80}")
            print(f"{ticker} INSIDER SENTIMENT ANALYSIS")
            print(f"{'='*80}\n")
            print(json.dumps(result, indent=2))
            print()
            
            # Visual indicator
            if result['net_sentiment'] == 'bullish':
                print("📈 Signal: BULLISH - Insiders are buying")
            elif result['net_sentiment'] == 'bearish':
                print("📉 Signal: BEARISH - Insiders are selling")
            else:
                print("➡️  Signal: NEUTRAL - Mixed insider activity")
        
        else:
            print(f"Unknown command: {command}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())

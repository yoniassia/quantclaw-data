#!/usr/bin/env python3
"""
QUANTCLAW DATA — Secondary Offering Monitor (Phase 149)
Follow-on offerings, shelf registrations from SEC S-3/424B filings

Data Sources:
- SEC EDGAR RSS: Real-time filing notifications
- SEC EDGAR API: S-3, 424B filings for secondary offerings
- Yahoo Finance: Stock prices and volume impact

CLI:
  python cli.py secondary-recent [--days 7]              # Recent secondary offerings
  python cli.py secondary-by-ticker TICKER [--days 30]   # Offerings for specific ticker
  python cli.py secondary-shelf-status TICKER            # Check shelf registration status
  python cli.py secondary-impact TICKER                  # Analyze price impact of offerings
  python cli.py secondary-upcoming                       # Upcoming offerings (filed but not priced)
  python cli.py secondary-search [KEYWORD]               # Search offerings by keyword
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
import yfinance as yf
import requests
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET
import re
from collections import defaultdict

class SecondaryOfferingMonitor:
    """Track secondary offerings and shelf registrations from SEC filings"""
    
    # SEC EDGAR RSS feed for recent filings
    SEC_RSS_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
    SEC_API_BASE = "https://www.sec.gov"
    
    # Form types for secondary offerings
    SECONDARY_FORMS = {
        'S-3': 'Shelf registration - enables future securities offerings',
        'S-3/A': 'Amendment to shelf registration',
        '424B5': 'Prospectus supplement - pricing of offering',
        '424B2': 'Prospectus supplement - base prospectus filing',
        '424B3': 'Prospectus supplement - pricing amendment',
        'S-3ASR': 'Automatic shelf registration (well-known seasoned issuer)',
        'FWP': 'Free writing prospectus - marketing materials'
    }
    
    def __init__(self):
        self.sec_headers = {
            'User-Agent': 'QuantClaw Data quantclaw@example.com'
        }
    
    def get_recent_filings(self, days: int = 7, form_type: Optional[str] = None) -> List[Dict]:
        """Get recent secondary offering filings from SEC EDGAR
        
        Args:
            days: Number of days to look back
            form_type: Filter by specific form (S-3, 424B5, etc)
        
        Returns:
            List of filing dicts with ticker, form, date, description
        """
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        filings = []
        
        # Query SEC EDGAR for each relevant form type
        forms_to_check = [form_type] if form_type else list(self.SECONDARY_FORMS.keys())
        
        for form in forms_to_check:
            try:
                # SEC EDGAR company search endpoint
                params = {
                    'action': 'getcompany',
                    'type': form,
                    'dateb': end_date.strftime('%Y%m%d'),
                    'datea': start_date.strftime('%Y%m%d'),
                    'owner': 'exclude',
                    'output': 'atom',
                    'count': 100
                }
                
                response = requests.get(
                    self.SEC_RSS_URL,
                    params=params,
                    headers=self.sec_headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    # Parse RSS feed
                    root = ET.fromstring(response.content)
                    
                    # Extract entries (filings)
                    ns = {'atom': 'http://www.w3.org/2005/Atom'}
                    
                    for entry in root.findall('atom:entry', ns):
                        try:
                            title = entry.find('atom:title', ns).text
                            filing_date = entry.find('atom:updated', ns).text[:10]
                            summary = entry.find('atom:summary', ns).text if entry.find('atom:summary', ns) is not None else ''
                            link = entry.find('atom:link', ns).attrib.get('href', '')
                            
                            # Extract company name and ticker from title
                            # Title format: "COMPANY NAME (TICKER) - Form Type"
                            match = re.match(r'(.+?)\s+\(([A-Z]{1,5})\)', title)
                            if match:
                                company_name = match.group(1).strip()
                                ticker = match.group(2).strip()
                            else:
                                company_name = title
                                ticker = 'N/A'
                            
                            filings.append({
                                'ticker': ticker,
                                'company': company_name,
                                'form_type': form,
                                'filing_date': filing_date,
                                'description': self.SECONDARY_FORMS.get(form, 'Secondary offering filing'),
                                'url': link,
                                'summary': summary[:200] if summary else ''
                            })
                        except Exception as e:
                            continue
                
            except Exception as e:
                # If one form fails, continue with others
                continue
        
        # Sort by date (most recent first)
        filings.sort(key=lambda x: x['filing_date'], reverse=True)
        
        return filings
    
    def get_ticker_filings(self, ticker: str, days: int = 30) -> List[Dict]:
        """Get all secondary offering filings for a specific ticker
        
        Args:
            ticker: Stock ticker symbol
            days: Days to look back
        
        Returns:
            List of filings for the ticker
        """
        
        all_filings = self.get_recent_filings(days=days)
        
        # Filter for ticker
        ticker_filings = [f for f in all_filings if f['ticker'].upper() == ticker.upper()]
        
        return ticker_filings
    
    def check_shelf_status(self, ticker: str) -> Dict:
        """Check if company has active shelf registration
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dict with shelf status and details
        """
        
        # Look for S-3 or S-3ASR filings in past 3 years (shelf expires after 3 years)
        filings = self.get_ticker_filings(ticker, days=365*3)
        
        # Find most recent S-3 or S-3ASR
        shelf_filings = [f for f in filings if f['form_type'] in ['S-3', 'S-3ASR', 'S-3/A']]
        
        if not shelf_filings:
            return {
                'ticker': ticker,
                'has_shelf': False,
                'status': 'No active shelf registration found',
                'last_shelf_filing': None
            }
        
        most_recent_shelf = shelf_filings[0]
        filing_date = datetime.strptime(most_recent_shelf['filing_date'], '%Y-%m-%d')
        days_since_filing = (datetime.now() - filing_date).days
        
        # Check if expired (3 years = 1095 days)
        is_active = days_since_filing < 1095
        
        # Look for recent 424B filings (actual offerings off the shelf)
        recent_offerings = [f for f in filings if f['form_type'].startswith('424B')]
        
        return {
            'ticker': ticker,
            'has_shelf': True,
            'is_active': is_active,
            'form_type': most_recent_shelf['form_type'],
            'filing_date': most_recent_shelf['filing_date'],
            'days_since_filing': days_since_filing,
            'expires_date': (filing_date + timedelta(days=1095)).strftime('%Y-%m-%d'),
            'days_until_expiry': 1095 - days_since_filing if is_active else 0,
            'recent_offerings': len(recent_offerings),
            'last_offering_date': recent_offerings[0]['filing_date'] if recent_offerings else None,
            'url': most_recent_shelf['url']
        }
    
    def analyze_price_impact(self, ticker: str, filing_date: Optional[str] = None) -> Dict:
        """Analyze stock price impact of secondary offering
        
        Args:
            ticker: Stock ticker symbol
            filing_date: Date of filing (YYYY-MM-DD), if None uses most recent offering
        
        Returns:
            Dict with price impact analysis
        """
        
        try:
            # Get stock data
            stock = yf.Ticker(ticker)
            
            # If no filing date provided, find most recent 424B filing
            if not filing_date:
                recent_offerings = self.get_ticker_filings(ticker, days=90)
                pricing_filings = [f for f in recent_offerings if f['form_type'].startswith('424B')]
                
                if not pricing_filings:
                    return {
                        'error': f'No recent secondary offerings found for {ticker}',
                        'ticker': ticker
                    }
                
                filing_date = pricing_filings[0]['filing_date']
            
            # Get price data around filing date
            filing_dt = datetime.strptime(filing_date, '%Y-%m-%d')
            start_date = filing_dt - timedelta(days=30)
            end_date = filing_dt + timedelta(days=30)
            
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                return {
                    'error': 'No price data available',
                    'ticker': ticker,
                    'filing_date': filing_date
                }
            
            # Find price on filing date (or closest date)
            filing_price = None
            for date_offset in range(5):  # Check up to 5 days forward
                check_date = filing_dt + timedelta(days=date_offset)
                date_str = check_date.strftime('%Y-%m-%d')
                if date_str in hist.index.strftime('%Y-%m-%d'):
                    filing_price = float(hist.loc[hist.index.strftime('%Y-%m-%d') == date_str, 'Close'].iloc[0])
                    break
            
            if filing_price is None:
                return {
                    'error': 'Could not find price data for filing date',
                    'ticker': ticker,
                    'filing_date': filing_date
                }
            
            # Calculate pre-filing average (20 days before)
            pre_filing = hist[hist.index < filing_dt]
            if len(pre_filing) >= 5:
                pre_avg = float(pre_filing['Close'].tail(20).mean())
                pre_volume_avg = float(pre_filing['Volume'].tail(20).mean())
            else:
                pre_avg = filing_price
                pre_volume_avg = 0
            
            # Calculate post-filing performance
            post_filing = hist[hist.index >= filing_dt]
            if len(post_filing) >= 5:
                # 1-day, 5-day, 20-day returns
                returns = {}
                for days in [1, 5, 20]:
                    if len(post_filing) > days:
                        future_price = float(post_filing['Close'].iloc[days])
                        returns[f'{days}d'] = ((future_price - filing_price) / filing_price) * 100
                
                # Volume spike on filing day
                filing_volume = float(post_filing['Volume'].iloc[0]) if len(post_filing) > 0 else 0
                volume_spike_pct = ((filing_volume - pre_volume_avg) / pre_volume_avg * 100) if pre_volume_avg > 0 else 0
            else:
                returns = {}
                volume_spike_pct = 0
            
            # Initial impact (filing price vs pre-filing avg)
            initial_impact_pct = ((filing_price - pre_avg) / pre_avg) * 100
            
            return {
                'ticker': ticker,
                'filing_date': filing_date,
                'filing_price': round(filing_price, 2),
                'pre_filing_avg_20d': round(pre_avg, 2),
                'initial_impact_pct': round(initial_impact_pct, 2),
                'volume_spike_pct': round(volume_spike_pct, 2),
                'returns': {k: round(v, 2) for k, v in returns.items()},
                'dilution_estimate': self._estimate_dilution(ticker, filing_date)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'ticker': ticker,
                'filing_date': filing_date
            }
    
    def _estimate_dilution(self, ticker: str, filing_date: str) -> str:
        """Estimate dilution from offering (simplified)"""
        
        # This is a simplified estimate
        # Real dilution requires parsing prospectus for share count
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            shares_outstanding = info.get('sharesOutstanding', 0)
            
            if shares_outstanding > 0:
                # Typical secondary is 3-7% of shares outstanding
                typical_dilution_pct = 5.0
                return f"~{typical_dilution_pct}% (typical secondary offering)"
            else:
                return "Unknown"
        except:
            return "Unknown"
    
    def get_upcoming_offerings(self) -> List[Dict]:
        """Find offerings that are filed but not yet priced
        
        Returns:
            List of upcoming offerings (S-3 filed recently but no 424B yet)
        """
        
        # Get recent S-3 filings (past 60 days)
        recent_s3 = self.get_recent_filings(days=60, form_type='S-3')
        
        upcoming = []
        
        for filing in recent_s3:
            ticker = filing['ticker']
            if ticker == 'N/A':
                continue
            
            # Check if there's a recent 424B (pricing) for this ticker
            all_filings = self.get_ticker_filings(ticker, days=60)
            pricing_filings = [f for f in all_filings if f['form_type'].startswith('424B')]
            
            # If S-3 filed but no 424B yet, it's upcoming
            if not pricing_filings:
                # Get current stock info
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    current_price = info.get('currentPrice', 0)
                    market_cap = info.get('marketCap', 0)
                    
                    upcoming.append({
                        'ticker': ticker,
                        'company': filing['company'],
                        's3_filing_date': filing['filing_date'],
                        'current_price': current_price,
                        'market_cap': market_cap,
                        'days_since_s3': (datetime.now() - datetime.strptime(filing['filing_date'], '%Y-%m-%d')).days,
                        'url': filing['url']
                    })
                except:
                    continue
        
        # Sort by most recent S-3 filing
        upcoming.sort(key=lambda x: x['s3_filing_date'], reverse=True)
        
        return upcoming
    
    def search_offerings(self, keyword: Optional[str] = None, days: int = 30) -> List[Dict]:
        """Search secondary offerings by keyword
        
        Args:
            keyword: Search term (company name, ticker)
            days: Days to look back
        
        Returns:
            List of matching filings
        """
        
        all_filings = self.get_recent_filings(days=days)
        
        if not keyword:
            return all_filings
        
        keyword_lower = keyword.lower()
        
        # Filter by keyword in ticker or company name
        matches = [
            f for f in all_filings
            if keyword_lower in f['ticker'].lower() or keyword_lower in f['company'].lower()
        ]
        
        return matches


# CLI Commands

def secondary_recent_cmd(args):
    """Show recent secondary offerings"""
    monitor = SecondaryOfferingMonitor()
    filings = monitor.get_recent_filings(days=args.days)
    
    if not filings:
        print(f"No secondary offering filings found in past {args.days} days")
        return 0
    
    print(f"\nRecent Secondary Offerings (Past {args.days} Days)")
    print("=" * 110)
    print(f"{'DATE':<12} {'TICKER':<8} {'COMPANY':<35} {'FORM':<10} {'TYPE':<30}")
    print("=" * 110)
    
    for filing in filings:
        company_short = filing['company'][:34] if len(filing['company']) > 34 else filing['company']
        form_desc = filing['description'][:29] if len(filing['description']) > 29 else filing['description']
        
        print(f"{filing['filing_date']:<12} {filing['ticker']:<8} {company_short:<35} "
              f"{filing['form_type']:<10} {form_desc:<30}")
    
    print(f"\nTotal: {len(filings)} filings")
    
    # Summary by form type
    form_counts = defaultdict(int)
    for f in filings:
        form_counts[f['form_type']] += 1
    
    print("\nBreakdown by Form Type:")
    for form, count in sorted(form_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {form}: {count}")
    
    return 0


def secondary_by_ticker_cmd(args):
    """Show secondary offerings for specific ticker"""
    monitor = SecondaryOfferingMonitor()
    filings = monitor.get_ticker_filings(args.ticker, days=args.days)
    
    if not filings:
        print(f"No secondary offering filings found for {args.ticker} in past {args.days} days")
        return 0
    
    print(f"\nSecondary Offerings: {args.ticker}")
    print("=" * 100)
    
    for filing in filings:
        print(f"\nDate: {filing['filing_date']}")
        print(f"Form: {filing['form_type']}")
        print(f"Description: {filing['description']}")
        print(f"URL: {filing['url']}")
        if filing['summary']:
            print(f"Summary: {filing['summary']}")
    
    print(f"\nTotal: {len(filings)} filings")
    
    return 0


def secondary_shelf_status_cmd(args):
    """Check shelf registration status"""
    monitor = SecondaryOfferingMonitor()
    result = monitor.check_shelf_status(args.ticker)
    
    print(f"\nShelf Registration Status: {args.ticker}")
    print("=" * 70)
    
    if not result['has_shelf']:
        print(f"Status: {result['status']}")
        return 0
    
    status_text = "ACTIVE ✓" if result['is_active'] else "EXPIRED ✗"
    print(f"Status: {status_text}")
    print(f"Form Type: {result['form_type']}")
    print(f"Filing Date: {result['filing_date']}")
    print(f"Days Since Filing: {result['days_since_filing']}")
    
    if result['is_active']:
        print(f"Expires: {result['expires_date']} ({result['days_until_expiry']} days)")
    
    print(f"\nOfferings Off This Shelf: {result['recent_offerings']}")
    if result['last_offering_date']:
        print(f"Most Recent Offering: {result['last_offering_date']}")
    
    print(f"\nSEC Filing: {result['url']}")
    
    return 0


def secondary_impact_cmd(args):
    """Analyze price impact of secondary offering"""
    monitor = SecondaryOfferingMonitor()
    result = monitor.analyze_price_impact(args.ticker)
    
    if 'error' in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1
    
    print(f"\nSecondary Offering Price Impact: {result['ticker']}")
    print("=" * 70)
    print(f"Filing Date: {result['filing_date']}")
    print(f"Filing Price: ${result['filing_price']:.2f}")
    print(f"Pre-Filing Avg (20d): ${result['pre_filing_avg_20d']:.2f}")
    print(f"Initial Impact: {result['initial_impact_pct']:+.2f}%")
    print(f"Volume Spike: {result['volume_spike_pct']:+.2f}%")
    
    print(f"\nPost-Filing Returns:")
    for period, return_pct in result['returns'].items():
        print(f"  {period}: {return_pct:+.2f}%")
    
    print(f"\nEstimated Dilution: {result['dilution_estimate']}")
    
    # Interpretation
    if result['initial_impact_pct'] < -5:
        print("\n⚠️  Significant negative price reaction to offering")
    elif result['initial_impact_pct'] > 0:
        print("\n✓ Positive price reaction (strong demand signal)")
    
    return 0


def secondary_upcoming_cmd(args):
    """Show upcoming secondary offerings"""
    monitor = SecondaryOfferingMonitor()
    upcoming = monitor.get_upcoming_offerings()
    
    if not upcoming:
        print("No upcoming secondary offerings found (S-3 filed but not yet priced)")
        return 0
    
    print(f"\nUpcoming Secondary Offerings (S-3 Filed, Not Yet Priced)")
    print("=" * 100)
    print(f"{'TICKER':<8} {'COMPANY':<35} {'S-3 DATE':<12} {'DAYS AGO':<10} {'PRICE':<10} {'MKT CAP':<12}")
    print("=" * 100)
    
    for offering in upcoming:
        company_short = offering['company'][:34] if len(offering['company']) > 34 else offering['company']
        market_cap_str = f"${offering['market_cap']/1e9:.2f}B" if offering['market_cap'] > 0 else 'N/A'
        
        print(f"{offering['ticker']:<8} {company_short:<35} {offering['s3_filing_date']:<12} "
              f"{offering['days_since_s3']:<10} ${offering['current_price']:<9.2f} {market_cap_str:<12}")
    
    print(f"\nTotal: {len(upcoming)} upcoming offerings")
    print("\nNote: These companies have filed shelf registrations but haven't priced offerings yet.")
    print("Watch for 424B5 filings which indicate imminent pricing.")
    
    return 0


def secondary_search_cmd(args):
    """Search secondary offerings by keyword"""
    monitor = SecondaryOfferingMonitor()
    results = monitor.search_offerings(keyword=args.keyword, days=args.days)
    
    if not results:
        print(f"No offerings found matching '{args.keyword}'")
        return 0
    
    print(f"\nSecondary Offering Search: '{args.keyword or 'all'}'")
    print("=" * 100)
    print(f"{'DATE':<12} {'TICKER':<8} {'COMPANY':<35} {'FORM':<10}")
    print("=" * 100)
    
    for filing in results:
        company_short = filing['company'][:34] if len(filing['company']) > 34 else filing['company']
        print(f"{filing['filing_date']:<12} {filing['ticker']:<8} {company_short:<35} {filing['form_type']:<10}")
    
    print(f"\nTotal: {len(results)} results")
    
    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Secondary Offering Monitor')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # secondary-recent
    recent_parser = subparsers.add_parser('secondary-recent', help='Recent secondary offerings')
    recent_parser.add_argument('--days', type=int, default=7, help='Days to look back (default: 7)')
    
    # secondary-by-ticker
    ticker_parser = subparsers.add_parser('secondary-by-ticker', help='Offerings for specific ticker')
    ticker_parser.add_argument('ticker', help='Stock ticker symbol')
    ticker_parser.add_argument('--days', type=int, default=30, help='Days to look back (default: 30)')
    
    # secondary-shelf-status
    shelf_parser = subparsers.add_parser('secondary-shelf-status', help='Check shelf registration status')
    shelf_parser.add_argument('ticker', help='Stock ticker symbol')
    
    # secondary-impact
    impact_parser = subparsers.add_parser('secondary-impact', help='Analyze price impact')
    impact_parser.add_argument('ticker', help='Stock ticker symbol')
    
    # secondary-upcoming
    subparsers.add_parser('secondary-upcoming', help='Upcoming offerings')
    
    # secondary-search
    search_parser = subparsers.add_parser('secondary-search', help='Search offerings')
    search_parser.add_argument('keyword', nargs='?', help='Search keyword (optional)')
    search_parser.add_argument('--days', type=int, default=30, help='Days to look back (default: 30)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to command handlers
    if args.command == 'secondary-recent':
        return secondary_recent_cmd(args)
    elif args.command == 'secondary-by-ticker':
        return secondary_by_ticker_cmd(args)
    elif args.command == 'secondary-shelf-status':
        return secondary_shelf_status_cmd(args)
    elif args.command == 'secondary-impact':
        return secondary_impact_cmd(args)
    elif args.command == 'secondary-upcoming':
        return secondary_upcoming_cmd(args)
    elif args.command == 'secondary-search':
        return secondary_search_cmd(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())

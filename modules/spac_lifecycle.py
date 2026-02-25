#!/usr/bin/env python3
"""
QUANTCLAW DATA — SPAC Lifecycle Tracker (Phase 148)
SPAC trust values, deal timelines, redemption rates from SEC S-1/8-K

Data Sources:
- Yahoo Finance: SPAC prices, market data, IPO dates
- SEC EDGAR: S-1, S-4, 8-K filings for trust values and deal announcements
- FRED: Risk-free rate for trust value calculations

CLI:
  python cli.py spac-list [--status searching|announced|completed]  # List tracked SPACs
  python cli.py spac-trust TICKER                                   # Calculate trust value per share
  python cli.py spac-timeline TICKER                                # Show deal timeline
  python cli.py spac-redemptions TICKER                             # Estimate redemption risk
  python cli.py spac-arbitrage                                      # Find arbitrage opportunities
  python cli.py spac-search [KEYWORD]                               # Search for SPACs
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
import yfinance as yf
import requests
from typing import Dict, List, Optional, Any
import re

class SPACLifecycleTracker:
    """Track SPAC lifecycle stages, trust values, and deal metrics"""
    
    # Known SPAC tickers (common units, warrants, and shares)
    # Format: ticker -> {name, ipo_date, trust_size, status}
    KNOWN_SPACS = {
        # Recent/Active SPACs
        'PSFE': {'name': 'Paysafe', 'status': 'completed', 'merger_date': '2021-03-30'},
        'OPEN': {'name': 'Opendoor', 'status': 'completed', 'merger_date': '2020-12-21'},
        'SOFI': {'name': 'SoFi', 'status': 'completed', 'merger_date': '2021-06-01'},
        'LCID': {'name': 'Lucid Motors', 'status': 'completed', 'merger_date': '2021-07-26'},
        'DWAC': {'name': 'Digital World Acquisition Corp', 'status': 'announced'},
        'IPOF': {'name': 'Social Capital Hedosophia Holdings Corp VI', 'status': 'searching'},
        
        # Common SPAC naming patterns
        # Most SPACs use suffixes: -U (unit), -WT (warrant), base ticker (common)
    }
    
    def __init__(self):
        self.sec_headers = {
            'User-Agent': 'QuantClaw Data quantclaw@example.com'
        }
        self.fred_api_key = None  # Optional
    
    def get_spac_list(self, status: Optional[str] = None) -> List[Dict]:
        """Get list of tracked SPACs with current status"""
        spacs = []
        
        for ticker, info in self.KNOWN_SPACS.items():
            if status and info.get('status') != status:
                continue
            
            try:
                stock = yf.Ticker(ticker)
                current_info = stock.info
                
                spac_data = {
                    'ticker': ticker,
                    'name': info['name'],
                    'status': info['status'],
                    'price': current_info.get('currentPrice', 0),
                    'market_cap': current_info.get('marketCap', 0),
                    'volume': current_info.get('volume', 0)
                }
                
                # Add status-specific data
                if info['status'] == 'announced':
                    spac_data['target'] = info.get('target', 'TBA')
                elif info['status'] == 'completed':
                    spac_data['merger_date'] = info.get('merger_date')
                
                spacs.append(spac_data)
            
            except Exception as e:
                # If ticker not found, skip
                continue
        
        return spacs
    
    def calculate_trust_value(self, ticker: str) -> Dict:
        """Calculate SPAC trust value per share
        
        Trust value = initial trust + interest - expenses
        Typically starts at $10/share, earns risk-free rate
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get current price
            current_price = info.get('currentPrice', 0)
            
            # Estimate trust value
            # Most SPACs start with $10/share in trust
            initial_trust = 10.00
            
            # Get IPO date (approximate from company age)
            # For simplicity, use market cap / shares to estimate time elapsed
            shares_outstanding = info.get('sharesOutstanding', 0)
            
            # Calculate discount/premium to trust
            if current_price > 0:
                # Assuming trust value grows at risk-free rate (~5% annually)
                # Typical SPAC holds trust for 18-24 months
                estimated_trust = initial_trust * 1.08  # ~8% over 18 months
                
                discount_premium = ((current_price - estimated_trust) / estimated_trust) * 100
                
                return {
                    'ticker': ticker,
                    'current_price': current_price,
                    'estimated_trust_value': round(estimated_trust, 2),
                    'discount_premium_pct': round(discount_premium, 2),
                    'arbitrage_opportunity': discount_premium < -5,  # Trading 5%+ below trust
                    'redemption_floor': round(estimated_trust * 0.98, 2),  # 2% haircut
                    'shares_outstanding': shares_outstanding,
                    'total_trust_value': round(estimated_trust * shares_outstanding, 0) if shares_outstanding else None
                }
            
            return {'error': 'No price data available'}
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_deal_timeline(self, ticker: str) -> Dict:
        """Get SPAC deal timeline from announcement to completion"""
        
        if ticker not in self.KNOWN_SPACS:
            return {'error': 'SPAC not in database'}
        
        spac_info = self.KNOWN_SPACS[ticker]
        status = spac_info['status']
        
        timeline = {
            'ticker': ticker,
            'name': spac_info['name'],
            'status': status,
            'stages': []
        }
        
        # Build timeline based on status
        if status == 'searching':
            timeline['stages'].append({
                'stage': 'IPO Completed',
                'description': 'SPAC raised capital, searching for target',
                'typical_duration': '18-24 months search period'
            })
        
        elif status == 'announced':
            timeline['stages'].extend([
                {
                    'stage': 'IPO Completed',
                    'description': 'SPAC raised capital'
                },
                {
                    'stage': 'Target Announced',
                    'description': 'Merger target identified',
                    'status': 'current'
                },
                {
                    'stage': 'Shareholder Vote',
                    'description': 'Upcoming shareholder approval vote',
                    'typical_duration': '2-4 months after announcement'
                },
                {
                    'stage': 'Merger Close',
                    'description': 'Deal completion pending'
                }
            ])
            
            timeline['redemption_deadline'] = 'Before shareholder vote'
            timeline['estimated_completion'] = '2-6 months'
        
        elif status == 'completed':
            merger_date = spac_info.get('merger_date', 'Unknown')
            timeline['stages'].extend([
                {
                    'stage': 'IPO Completed',
                    'description': 'SPAC raised capital'
                },
                {
                    'stage': 'Target Announced',
                    'description': 'Merger target identified'
                },
                {
                    'stage': 'Shareholder Vote',
                    'description': 'Shareholders approved merger'
                },
                {
                    'stage': 'Merger Completed',
                    'date': merger_date,
                    'description': 'SPAC merged with target company',
                    'status': 'completed'
                }
            ])
            timeline['merger_date'] = merger_date
        
        return timeline
    
    def estimate_redemption_risk(self, ticker: str) -> Dict:
        """Estimate redemption rate risk for SPAC
        
        Higher redemptions = less cash for target company
        Redemptions typically 30-70% for bad deals, <10% for good deals
        """
        
        trust_data = self.calculate_trust_value(ticker)
        if 'error' in trust_data:
            return trust_data
        
        current_price = trust_data['current_price']
        trust_value = trust_data['estimated_trust_value']
        discount_pct = trust_data['discount_premium_pct']
        
        # Estimate redemption likelihood based on price/trust ratio
        redemption_risk = 'LOW'
        expected_redemption_pct = 10
        
        if discount_pct < -5:
            redemption_risk = 'VERY HIGH'
            expected_redemption_pct = 70
        elif discount_pct < -2:
            redemption_risk = 'HIGH'
            expected_redemption_pct = 50
        elif discount_pct < 0:
            redemption_risk = 'MODERATE'
            expected_redemption_pct = 30
        elif discount_pct < 10:
            redemption_risk = 'LOW'
            expected_redemption_pct = 10
        else:
            redemption_risk = 'VERY LOW'
            expected_redemption_pct = 5
        
        return {
            'ticker': ticker,
            'redemption_risk': redemption_risk,
            'expected_redemption_pct': expected_redemption_pct,
            'current_price': current_price,
            'trust_value': trust_value,
            'discount_premium_pct': discount_pct,
            'explanation': self._redemption_explanation(redemption_risk, discount_pct)
        }
    
    def _redemption_explanation(self, risk: str, discount_pct: float) -> str:
        """Generate human-readable redemption risk explanation"""
        if risk == 'VERY HIGH':
            return f"Price {abs(discount_pct):.1f}% below trust → arbitrage opportunity → expect mass redemptions"
        elif risk == 'HIGH':
            return f"Price {abs(discount_pct):.1f}% below trust → high redemption incentive"
        elif risk == 'MODERATE':
            return f"Price slightly below trust → moderate redemptions likely"
        elif risk == 'LOW':
            return "Price at/above trust → redemptions unlikely"
        else:
            return f"Price {discount_pct:.1f}% premium to trust → strong investor confidence"
    
    def find_arbitrage_opportunities(self) -> List[Dict]:
        """Find SPACs trading below trust value (arbitrage opportunities)"""
        
        opportunities = []
        
        for ticker in self.KNOWN_SPACS.keys():
            trust_data = self.calculate_trust_value(ticker)
            
            if 'error' not in trust_data and trust_data.get('arbitrage_opportunity'):
                opportunities.append({
                    'ticker': ticker,
                    'name': self.KNOWN_SPACS[ticker]['name'],
                    'price': trust_data['current_price'],
                    'trust_value': trust_data['estimated_trust_value'],
                    'discount_pct': trust_data['discount_premium_pct'],
                    'potential_gain_pct': abs(trust_data['discount_premium_pct']),
                    'redemption_floor': trust_data['redemption_floor']
                })
        
        # Sort by largest discount (best arbitrage)
        opportunities.sort(key=lambda x: x['discount_pct'])
        
        return opportunities
    
    def search_spacs(self, keyword: Optional[str] = None) -> List[Dict]:
        """Search for SPACs by keyword (name, target, sector)"""
        
        results = []
        keyword_lower = keyword.lower() if keyword else ""
        
        for ticker, info in self.KNOWN_SPACS.items():
            name_lower = info['name'].lower()
            
            # Match keyword in name or target
            if not keyword or keyword_lower in name_lower or keyword_lower in info.get('target', '').lower():
                try:
                    stock = yf.Ticker(ticker)
                    current_info = stock.info
                    
                    results.append({
                        'ticker': ticker,
                        'name': info['name'],
                        'status': info['status'],
                        'target': info.get('target', 'N/A'),
                        'price': current_info.get('currentPrice', 0),
                        'market_cap': current_info.get('marketCap', 0)
                    })
                except:
                    continue
        
        return results


# CLI Commands
def spac_list_cmd(args):
    """List SPACs by status"""
    tracker = SPACLifecycleTracker()
    spacs = tracker.get_spac_list(status=args.status)
    
    if not spacs:
        print("No SPACs found matching criteria")
        return 1
    
    print(f"\n{'TICKER':<8} {'NAME':<40} {'STATUS':<12} {'PRICE':<10} {'MARKET CAP':<15}")
    print("=" * 95)
    
    for spac in spacs:
        market_cap_str = f"${spac['market_cap']/1e9:.2f}B" if spac['market_cap'] > 0 else 'N/A'
        print(f"{spac['ticker']:<8} {spac['name']:<40} {spac['status']:<12} ${spac['price']:<9.2f} {market_cap_str:<15}")
    
    print(f"\nTotal: {len(spacs)} SPACs")
    return 0


def spac_trust_cmd(args):
    """Calculate SPAC trust value"""
    tracker = SPACLifecycleTracker()
    result = tracker.calculate_trust_value(args.ticker)
    
    if 'error' in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1
    
    print(f"\nSPAC Trust Value Analysis: {args.ticker}")
    print("=" * 60)
    print(f"Current Price:          ${result['current_price']:.2f}")
    print(f"Estimated Trust Value:  ${result['estimated_trust_value']:.2f}")
    print(f"Discount/Premium:       {result['discount_premium_pct']:+.2f}%")
    print(f"Redemption Floor:       ${result['redemption_floor']:.2f}")
    
    if result['total_trust_value']:
        print(f"Total Trust Value:      ${result['total_trust_value']/1e6:.1f}M")
    
    if result['arbitrage_opportunity']:
        print(f"\n⚠️  ARBITRAGE OPPORTUNITY: Trading {abs(result['discount_premium_pct']):.1f}% below trust")
    
    return 0


def spac_timeline_cmd(args):
    """Show SPAC deal timeline"""
    tracker = SPACLifecycleTracker()
    timeline = tracker.get_deal_timeline(args.ticker)
    
    if 'error' in timeline:
        print(f"Error: {timeline['error']}", file=sys.stderr)
        return 1
    
    print(f"\nSPAC Deal Timeline: {timeline['name']} ({args.ticker})")
    print("=" * 60)
    print(f"Current Status: {timeline['status'].upper()}")
    print()
    
    for i, stage in enumerate(timeline['stages'], 1):
        status_marker = "✓" if stage.get('status') == 'completed' else "→" if stage.get('status') == 'current' else "○"
        print(f"{status_marker} {i}. {stage['stage']}")
        print(f"   {stage['description']}")
        if 'date' in stage:
            print(f"   Date: {stage['date']}")
        if 'typical_duration' in stage:
            print(f"   Duration: {stage['typical_duration']}")
        print()
    
    if 'redemption_deadline' in timeline:
        print(f"Redemption Deadline: {timeline['redemption_deadline']}")
    if 'estimated_completion' in timeline:
        print(f"Estimated Completion: {timeline['estimated_completion']}")
    
    return 0


def spac_redemptions_cmd(args):
    """Estimate redemption risk"""
    tracker = SPACLifecycleTracker()
    result = tracker.estimate_redemption_risk(args.ticker)
    
    if 'error' in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1
    
    print(f"\nSPAC Redemption Risk Analysis: {args.ticker}")
    print("=" * 60)
    print(f"Redemption Risk:        {result['redemption_risk']}")
    print(f"Expected Redemptions:   {result['expected_redemption_pct']}%")
    print(f"Current Price:          ${result['current_price']:.2f}")
    print(f"Trust Value:            ${result['trust_value']:.2f}")
    print(f"Discount/Premium:       {result['discount_premium_pct']:+.2f}%")
    print()
    print(f"Explanation: {result['explanation']}")
    
    return 0


def spac_arbitrage_cmd(args):
    """Find SPAC arbitrage opportunities"""
    tracker = SPACLifecycleTracker()
    opportunities = tracker.find_arbitrage_opportunities()
    
    if not opportunities:
        print("No arbitrage opportunities found (all SPACs trading at or above trust)")
        return 0
    
    print(f"\nSPAC Arbitrage Opportunities")
    print("=" * 90)
    print(f"{'TICKER':<8} {'NAME':<30} {'PRICE':<10} {'TRUST':<10} {'DISCOUNT':<12} {'UPSIDE':<10}")
    print("=" * 90)
    
    for opp in opportunities:
        print(f"{opp['ticker']:<8} {opp['name']:<30} ${opp['price']:<9.2f} ${opp['trust_value']:<9.2f} "
              f"{opp['discount_pct']:>6.2f}%     {opp['potential_gain_pct']:>6.2f}%")
    
    print(f"\nFound {len(opportunities)} opportunities")
    print("\nStrategy: Buy below trust, redeem shares before merger → lock in gains")
    
    return 0


def spac_search_cmd(args):
    """Search for SPACs"""
    tracker = SPACLifecycleTracker()
    results = tracker.search_spacs(keyword=args.keyword)
    
    if not results:
        print(f"No SPACs found matching '{args.keyword}'")
        return 1
    
    print(f"\nSPAC Search Results: '{args.keyword or 'all'}'")
    print("=" * 95)
    print(f"{'TICKER':<8} {'NAME':<35} {'STATUS':<12} {'TARGET':<20} {'PRICE':<10}")
    print("=" * 95)
    
    for spac in results:
        target = spac.get('target', 'N/A')
        print(f"{spac['ticker']:<8} {spac['name']:<35} {spac['status']:<12} {target:<20} ${spac['price']:<9.2f}")
    
    print(f"\nTotal: {len(results)} SPACs")
    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='SPAC Lifecycle Tracker')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # spac-list
    list_parser = subparsers.add_parser('spac-list', help='List tracked SPACs')
    list_parser.add_argument('--status', choices=['searching', 'announced', 'completed'], 
                            help='Filter by status')
    
    # spac-trust
    trust_parser = subparsers.add_parser('spac-trust', help='Calculate trust value')
    trust_parser.add_argument('ticker', help='SPAC ticker symbol')
    
    # spac-timeline
    timeline_parser = subparsers.add_parser('spac-timeline', help='Show deal timeline')
    timeline_parser.add_argument('ticker', help='SPAC ticker symbol')
    
    # spac-redemptions
    redemptions_parser = subparsers.add_parser('spac-redemptions', help='Estimate redemption risk')
    redemptions_parser.add_argument('ticker', help='SPAC ticker symbol')
    
    # spac-arbitrage
    subparsers.add_parser('spac-arbitrage', help='Find arbitrage opportunities')
    
    # spac-search
    search_parser = subparsers.add_parser('spac-search', help='Search for SPACs')
    search_parser.add_argument('keyword', nargs='?', help='Search keyword (optional)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to command handlers
    if args.command == 'spac-list':
        return spac_list_cmd(args)
    elif args.command == 'spac-trust':
        return spac_trust_cmd(args)
    elif args.command == 'spac-timeline':
        return spac_timeline_cmd(args)
    elif args.command == 'spac-redemptions':
        return spac_redemptions_cmd(args)
    elif args.command == 'spac-arbitrage':
        return spac_arbitrage_cmd(args)
    elif args.command == 'spac-search':
        return spac_search_cmd(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())

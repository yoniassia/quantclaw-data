#!/usr/bin/env python3
"""
QUANTCLAW DATA — Share Buyback Analysis (Phase 56)
Authorization vs execution, dilution impact, return on buyback calculation

Data Sources:
- Yahoo Finance: shares outstanding history, financial statements
- SEC EDGAR: 10-Q buyback disclosures, 10-K annual reports

CLI:
  python cli.py buyback-analysis AAPL      # Full buyback report
  python cli.py share-count-trend MSFT     # Shares outstanding over time
  python cli.py buyback-yield GOOGL        # Buyback yield calculation
  python cli.py dilution-impact META       # SBC dilution analysis
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
import yfinance as yf
import requests
from typing import Dict, List, Optional, Any
import re

class ShareBuybackAnalyzer:
    """Analyze share buybacks, dilution, and buyback ROI"""
    
    def __init__(self):
        self.sec_headers = {
            'User-Agent': 'QuantClaw Data quantclaw@example.com'
        }
    
    def get_share_count_history(self, ticker: str) -> List[Dict]:
        """Get shares outstanding history from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            
            # Get quarterly data
            quarterly_shares = []
            
            # Try to get from quarterly financials
            if hasattr(stock, 'quarterly_financials'):
                qf = stock.quarterly_financials
                if qf is not None and not qf.empty:
                    for col in qf.columns:
                        date_str = col.strftime('%Y-%m-%d') if hasattr(col, 'strftime') else str(col)
                        quarterly_shares.append({
                            'date': date_str,
                            'shares': None  # Will get from info
                        })
            
            # Get current shares outstanding
            info = stock.info
            current_shares = info.get('sharesOutstanding', 0)
            
            # Get historical shares from quarterly balance sheet
            quarterly_bs = stock.quarterly_balance_sheet
            shares_data = []
            
            if quarterly_bs is not None and not quarterly_bs.empty:
                # Look for 'Ordinary Shares Number' or 'Share Issued'
                share_keys = ['Ordinary Shares Number', 'Share Issued', 'Common Stock Shares Outstanding']
                
                for key in share_keys:
                    if key in quarterly_bs.index:
                        for col in quarterly_bs.columns:
                            date_str = col.strftime('%Y-%m-%d') if hasattr(col, 'strftime') else str(col)
                            shares = quarterly_bs.loc[key, col]
                            if shares and shares > 0:
                                shares_data.append({
                                    'date': date_str,
                                    'shares': int(shares)
                                })
                        break
            
            # If no historical data, use current
            if not shares_data and current_shares:
                shares_data.append({
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'shares': current_shares
                })
            
            # Sort by date (newest first)
            shares_data.sort(key=lambda x: x['date'], reverse=True)
            
            return shares_data
            
        except Exception as e:
            print(f"Error fetching share count for {ticker}: {e}", file=sys.stderr)
            return []
    
    def calculate_share_change(self, shares_history: List[Dict]) -> Dict:
        """Calculate share count changes and trends"""
        if len(shares_history) < 2:
            return {'error': 'Insufficient data'}
        
        recent = shares_history[0]['shares']
        older = shares_history[-1]['shares']
        
        change_abs = recent - older
        change_pct = ((recent - older) / older * 100) if older else 0
        
        # Calculate quarter-over-quarter changes
        qoq_changes = []
        for i in range(len(shares_history) - 1):
            curr = shares_history[i]['shares']
            prev = shares_history[i + 1]['shares']
            if curr and prev:
                qoq_pct = ((curr - prev) / prev * 100)
                qoq_changes.append({
                    'period': f"{shares_history[i+1]['date']} to {shares_history[i]['date']}",
                    'change_pct': round(qoq_pct, 2),
                    'change_abs': curr - prev
                })
        
        return {
            'current_shares': recent,
            'earliest_shares': older,
            'total_change_abs': change_abs,
            'total_change_pct': round(change_pct, 2),
            'qoq_changes': qoq_changes,
            'trend': 'buyback' if change_abs < 0 else 'dilution'
        }
    
    def get_buyback_info_from_financials(self, ticker: str) -> Dict:
        """Get buyback information from cash flow statement"""
        try:
            stock = yf.Ticker(ticker)
            
            # Get cash flow statement (quarterly)
            cf = stock.quarterly_cashflow
            
            buybacks = []
            if cf is not None and not cf.empty:
                # Look for repurchase of common stock
                buyback_keys = [
                    'Repurchase Of Capital Stock',
                    'Stock Repurchased',
                    'Common Stock Repurchased'
                ]
                
                for key in buyback_keys:
                    if key in cf.index:
                        for col in cf.columns:
                            date_str = col.strftime('%Y-%m-%d') if hasattr(col, 'strftime') else str(col)
                            amount = cf.loc[key, col]
                            if amount and abs(amount) > 0:
                                buybacks.append({
                                    'date': date_str,
                                    'amount': abs(int(amount))  # Make positive
                                })
                        break
            
            # Get stock-based compensation
            sbc_amounts = []
            if cf is not None and not cf.empty:
                sbc_keys = [
                    'Stock Based Compensation',
                    'Share Based Compensation'
                ]
                
                for key in sbc_keys:
                    if key in cf.index:
                        for col in cf.columns:
                            date_str = col.strftime('%Y-%m-%d') if hasattr(col, 'strftime') else str(col)
                            amount = cf.loc[key, col]
                            if amount and amount > 0:
                                sbc_amounts.append({
                                    'date': date_str,
                                    'amount': int(amount)
                                })
                        break
            
            return {
                'buybacks': sorted(buybacks, key=lambda x: x['date'], reverse=True),
                'stock_based_comp': sorted(sbc_amounts, key=lambda x: x['date'], reverse=True)
            }
            
        except Exception as e:
            print(f"Error fetching buyback info for {ticker}: {e}", file=sys.stderr)
            return {'buybacks': [], 'stock_based_comp': []}
    
    def calculate_buyback_yield(self, ticker: str) -> Dict:
        """Calculate buyback yield (buybacks / market cap)"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            market_cap = info.get('marketCap', 0)
            
            # Get recent buybacks (TTM)
            buyback_info = self.get_buyback_info_from_financials(ticker)
            buybacks = buyback_info.get('buybacks', [])
            
            # Sum last 4 quarters (TTM)
            ttm_buybacks = sum(b['amount'] for b in buybacks[:4])
            
            buyback_yield = (ttm_buybacks / market_cap * 100) if market_cap else 0
            
            # Also get dividend yield for comparison
            dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
            
            total_shareholder_yield = buyback_yield + dividend_yield
            
            return {
                'ticker': ticker,
                'market_cap': market_cap,
                'ttm_buybacks': ttm_buybacks,
                'buyback_yield_pct': round(buyback_yield, 2),
                'dividend_yield_pct': round(dividend_yield, 2),
                'total_shareholder_yield_pct': round(total_shareholder_yield, 2),
                'quarterly_buybacks': buybacks[:4]
            }
            
        except Exception as e:
            print(f"Error calculating buyback yield for {ticker}: {e}", file=sys.stderr)
            return {'error': str(e)}
    
    def analyze_dilution_impact(self, ticker: str) -> Dict:
        """Analyze dilution from stock-based compensation vs buybacks"""
        try:
            # Get shares outstanding history
            shares_history = self.get_share_count_history(ticker)
            share_changes = self.calculate_share_change(shares_history)
            
            # Get buyback and SBC data
            fin_data = self.get_buyback_info_from_financials(ticker)
            buybacks = fin_data.get('buybacks', [])
            sbc = fin_data.get('stock_based_comp', [])
            
            # Calculate net dilution (SBC - Buybacks)
            ttm_buybacks = sum(b['amount'] for b in buybacks[:4])
            ttm_sbc = sum(s['amount'] for s in sbc[:4])
            
            net_dilution = ttm_sbc - ttm_buybacks
            
            # Get stock info
            stock = yf.Ticker(ticker)
            info = stock.info
            market_cap = info.get('marketCap', 0)
            
            dilution_pct = (net_dilution / market_cap * 100) if market_cap else 0
            
            # Calculate effectiveness (what % of SBC is offset by buybacks)
            buyback_effectiveness = (ttm_buybacks / ttm_sbc * 100) if ttm_sbc else 0
            
            return {
                'ticker': ticker,
                'ttm_stock_based_comp': ttm_sbc,
                'ttm_buybacks': ttm_buybacks,
                'net_dilution': net_dilution,
                'dilution_pct': round(dilution_pct, 2),
                'buyback_effectiveness_pct': round(buyback_effectiveness, 2),
                'share_count_trend': share_changes.get('trend'),
                'share_change_pct': share_changes.get('total_change_pct'),
                'analysis': {
                    'buybacks_exceed_sbc': ttm_buybacks > ttm_sbc,
                    'net_reduction': net_dilution < 0,
                    'effectiveness_rating': 'High' if buyback_effectiveness > 100 else 'Medium' if buyback_effectiveness > 50 else 'Low'
                }
            }
            
        except Exception as e:
            print(f"Error analyzing dilution for {ticker}: {e}", file=sys.stderr)
            return {'error': str(e)}
    
    def calculate_buyback_roi(self, ticker: str) -> Dict:
        """Calculate return on buyback (theoretical vs actual)"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get historical price data
            hist = stock.history(period='2y')
            
            # Get buyback data
            fin_data = self.get_buyback_info_from_financials(ticker)
            buybacks = fin_data.get('buybacks', [])
            
            if not buybacks:
                return {'error': 'No buyback data available'}
            
            # Calculate average buyback price (estimate based on quarter midpoint)
            buyback_analysis = []
            
            for bb in buybacks[:4]:  # Last 4 quarters
                try:
                    quarter_date = datetime.strptime(bb['date'], '%Y-%m-%d')
                    
                    # Get price around that date
                    start = quarter_date - timedelta(days=45)
                    end = quarter_date + timedelta(days=45)
                    
                    mask = (hist.index >= start) & (hist.index <= end)
                    quarter_prices = hist[mask]['Close']
                    
                    if len(quarter_prices) > 0:
                        avg_price = quarter_prices.mean()
                        shares_bought = bb['amount'] / avg_price if avg_price else 0
                        
                        buyback_analysis.append({
                            'quarter': bb['date'],
                            'amount': bb['amount'],
                            'est_avg_price': round(float(avg_price), 2),
                            'est_shares_bought': int(shares_bought)
                        })
                except:
                    continue
            
            # Current price
            current_price = info.get('currentPrice', hist['Close'].iloc[-1] if len(hist) > 0 else 0)
            
            # Calculate theoretical ROI
            total_invested = sum(b['amount'] for b in buyback_analysis)
            total_shares = sum(b['est_shares_bought'] for b in buyback_analysis)
            avg_cost = total_invested / total_shares if total_shares else 0
            
            theoretical_gain = (current_price - avg_cost) / avg_cost * 100 if avg_cost else 0
            
            return {
                'ticker': ticker,
                'current_price': round(float(current_price), 2),
                'total_invested_ttm': total_invested,
                'est_shares_repurchased': total_shares,
                'avg_buyback_price': round(float(avg_cost), 2),
                'theoretical_roi_pct': round(theoretical_gain, 2),
                'quarterly_breakdown': buyback_analysis,
                'note': 'ROI is theoretical - assumes buybacks at avg quarterly price'
            }
            
        except Exception as e:
            print(f"Error calculating buyback ROI for {ticker}: {e}", file=sys.stderr)
            return {'error': str(e)}
    
    def full_buyback_report(self, ticker: str) -> Dict:
        """Comprehensive buyback analysis report"""
        print(f"Generating full buyback analysis for {ticker}...", file=sys.stderr)
        
        # Get all components
        shares_history = self.get_share_count_history(ticker)
        share_changes = self.calculate_share_change(shares_history)
        buyback_yield = self.calculate_buyback_yield(ticker)
        dilution = self.analyze_dilution_impact(ticker)
        roi = self.calculate_buyback_roi(ticker)
        
        return {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'share_count': {
                'history': shares_history[:8],  # Last 2 years
                'analysis': share_changes
            },
            'buyback_yield': buyback_yield,
            'dilution_analysis': dilution,
            'buyback_roi': roi,
            'summary': {
                'is_reducing_shares': share_changes.get('trend') == 'buyback',
                'buyback_yield': buyback_yield.get('buyback_yield_pct', 0),
                'total_shareholder_yield': buyback_yield.get('total_shareholder_yield_pct', 0),
                'buyback_effectiveness': dilution.get('buyback_effectiveness_pct', 0),
                'theoretical_roi': roi.get('theoretical_roi_pct', 0)
            }
        }

def main():
    parser = argparse.ArgumentParser(description='Share Buyback Analysis')
    parser.add_argument('command', choices=[
        'buyback-analysis',
        'share-count-trend',
        'buyback-yield',
        'dilution-impact'
    ])
    parser.add_argument('ticker', nargs='?', help='Stock ticker symbol')
    
    args = parser.parse_args()
    
    analyzer = ShareBuybackAnalyzer()
    
    if args.command == 'buyback-analysis':
        if not args.ticker:
            print("Error: ticker required for buyback-analysis", file=sys.stderr)
            sys.exit(1)
        result = analyzer.full_buyback_report(args.ticker.upper())
        
    elif args.command == 'share-count-trend':
        if not args.ticker:
            print("Error: ticker required for share-count-trend", file=sys.stderr)
            sys.exit(1)
        shares_history = analyzer.get_share_count_history(args.ticker.upper())
        share_changes = analyzer.calculate_share_change(shares_history)
        result = {
            'ticker': args.ticker.upper(),
            'shares_history': shares_history,
            'analysis': share_changes
        }
        
    elif args.command == 'buyback-yield':
        if not args.ticker:
            print("Error: ticker required for buyback-yield", file=sys.stderr)
            sys.exit(1)
        result = analyzer.calculate_buyback_yield(args.ticker.upper())
        
    elif args.command == 'dilution-impact':
        if not args.ticker:
            print("Error: ticker required for dilution-impact", file=sys.stderr)
            sys.exit(1)
        result = analyzer.analyze_dilution_impact(args.ticker.upper())
    
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Tax Loss Harvesting Module - Phase 55
Identify opportunities, track wash sale rules, estimate tax savings
Uses Yahoo Finance for free price data and historical returns
"""

import sys
import json
from datetime import datetime, timedelta
import yfinance as yf
from collections import defaultdict

SECTOR_MAPPING = {
    # Technology
    'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology', 'META': 'Technology',
    'NVDA': 'Technology', 'AMD': 'Technology', 'INTC': 'Technology', 'CRM': 'Technology',
    'ORCL': 'Technology', 'ADBE': 'Technology', 'CSCO': 'Technology', 'AVGO': 'Technology',
    
    # Consumer Cyclical
    'AMZN': 'Consumer Cyclical', 'TSLA': 'Consumer Cyclical', 'HD': 'Consumer Cyclical',
    'NKE': 'Consumer Cyclical', 'MCD': 'Consumer Cyclical', 'SBUX': 'Consumer Cyclical',
    'TGT': 'Consumer Cyclical', 'LOW': 'Consumer Cyclical',
    
    # Healthcare
    'JNJ': 'Healthcare', 'UNH': 'Healthcare', 'PFE': 'Healthcare', 'ABBV': 'Healthcare',
    'TMO': 'Healthcare', 'ABT': 'Healthcare', 'DHR': 'Healthcare', 'CVS': 'Healthcare',
    
    # Financial Services
    'JPM': 'Financial Services', 'BAC': 'Financial Services', 'WFC': 'Financial Services',
    'GS': 'Financial Services', 'MS': 'Financial Services', 'C': 'Financial Services',
    'BLK': 'Financial Services', 'SCHW': 'Financial Services',
    
    # Communication Services
    'DIS': 'Communication Services', 'NFLX': 'Communication Services', 'CMCSA': 'Communication Services',
    'T': 'Communication Services', 'VZ': 'Communication Services',
    
    # Energy
    'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy', 'SLB': 'Energy',
    
    # Consumer Defensive
    'PG': 'Consumer Defensive', 'KO': 'Consumer Defensive', 'PEP': 'Consumer Defensive',
    'WMT': 'Consumer Defensive', 'COST': 'Consumer Defensive',
    
    # Industrials
    'BA': 'Industrials', 'CAT': 'Industrials', 'GE': 'Industrials', 'HON': 'Industrials',
    'UPS': 'Industrials', 'RTX': 'Industrials',
}

SECTOR_REPLACEMENTS = {
    'Technology': ['QQQ', 'VGT', 'XLK', 'IGV', 'SMH'],
    'Consumer Cyclical': ['XLY', 'VCR', 'FDIS'],
    'Healthcare': ['XLV', 'VHT', 'IHI', 'IBB'],
    'Financial Services': ['XLF', 'VFH', 'KRE'],
    'Communication Services': ['XLC', 'VOX'],
    'Energy': ['XLE', 'VDE', 'IEO'],
    'Consumer Defensive': ['XLP', 'VDC'],
    'Industrials': ['XLI', 'VIS'],
}

def get_sector(ticker):
    """Get sector for a ticker"""
    if ticker in SECTOR_MAPPING:
        return SECTOR_MAPPING[ticker]
    
    # Try to fetch from Yahoo Finance
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info.get('sector', 'Unknown')
    except:
        return 'Unknown'

def get_ytd_return(ticker):
    """Calculate YTD return for a ticker"""
    try:
        year_start = datetime(datetime.now().year, 1, 1)
        stock = yf.Ticker(ticker)
        hist = stock.history(start=year_start, end=datetime.now())
        
        if len(hist) < 2:
            return None
        
        start_price = hist['Close'].iloc[0]
        end_price = hist['Close'].iloc[-1]
        ytd_return = ((end_price - start_price) / start_price) * 100
        
        return {
            'ytd_return_pct': round(ytd_return, 2),
            'start_price': round(start_price, 2),
            'current_price': round(end_price, 2),
            'start_date': hist.index[0].strftime('%Y-%m-%d'),
            'current_date': hist.index[-1].strftime('%Y-%m-%d')
        }
    except Exception as e:
        return None

def scan_portfolio(tickers):
    """Scan portfolio for tax loss harvesting candidates"""
    candidates = []
    
    for ticker in tickers:
        ytd_data = get_ytd_return(ticker)
        
        if ytd_data is None:
            continue
        
        if ytd_data['ytd_return_pct'] < 0:  # Only losses
            sector = get_sector(ticker)
            candidates.append({
                'ticker': ticker,
                'sector': sector,
                **ytd_data,
                'tlh_score': abs(ytd_data['ytd_return_pct'])  # Higher loss = better TLH candidate
            })
    
    # Sort by TLH score (biggest losses first)
    candidates.sort(key=lambda x: x['tlh_score'], reverse=True)
    
    return candidates

def check_wash_sale(ticker, sale_date_str):
    """Check if selling on a given date would trigger wash sale rule"""
    try:
        sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d')
    except ValueError:
        return {'error': 'Invalid date format. Use YYYY-MM-DD'}
    
    # Wash sale window: 30 days before and 30 days after
    window_start = sale_date - timedelta(days=30)
    window_end = sale_date + timedelta(days=30)
    
    try:
        stock = yf.Ticker(ticker)
        # Get price history for the wash sale window
        hist = stock.history(start=window_start, end=window_end)
        
        if len(hist) == 0:
            return {'error': f'No price data available for {ticker}'}
        
        sale_price = None
        if sale_date.strftime('%Y-%m-%d') in [d.strftime('%Y-%m-%d') for d in hist.index]:
            sale_idx = [i for i, d in enumerate(hist.index) if d.strftime('%Y-%m-%d') == sale_date.strftime('%Y-%m-%d')][0]
            sale_price = hist['Close'].iloc[sale_idx]
        
        return {
            'ticker': ticker,
            'sale_date': sale_date_str,
            'sale_price': round(sale_price, 2) if sale_price else None,
            'wash_sale_window': {
                'start': window_start.strftime('%Y-%m-%d'),
                'end': window_end.strftime('%Y-%m-%d')
            },
            'warning': '⚠️  Do not repurchase this security within the wash sale window',
            'safe_to_buy_after': window_end.strftime('%Y-%m-%d'),
            'days_until_safe': (window_end - datetime.now()).days if window_end > datetime.now() else 0
        }
    except Exception as e:
        return {'error': str(e)}

def estimate_tax_savings(ticker, cost_basis, shares, tax_rate=0.25):
    """Estimate potential tax savings from harvesting losses"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='1d')
        
        if len(hist) == 0:
            return {'error': f'No price data available for {ticker}'}
        
        current_price = hist['Close'].iloc[-1]
        
        # Calculate loss
        total_cost = cost_basis * shares
        current_value = current_price * shares
        capital_loss = total_cost - current_value
        
        if capital_loss <= 0:
            return {
                'ticker': ticker,
                'message': '✅ No loss to harvest - position is in profit',
                'cost_basis': cost_basis,
                'current_price': round(current_price, 2),
                'gain': round(-capital_loss, 2),
                'gain_pct': round((current_price - cost_basis) / cost_basis * 100, 2)
            }
        
        # Tax savings (can offset capital gains or up to $3k ordinary income)
        tax_savings = capital_loss * tax_rate
        
        # Calculate breakeven if we assume immediate repurchase after wash sale window
        # (this is a simplification - actual wash sale rules are complex)
        
        return {
            'ticker': ticker,
            'position': {
                'shares': shares,
                'cost_basis': cost_basis,
                'current_price': round(current_price, 2),
                'total_cost': round(total_cost, 2),
                'current_value': round(current_value, 2)
            },
            'loss_analysis': {
                'capital_loss': round(capital_loss, 2),
                'loss_pct': round((capital_loss / total_cost) * 100, 2),
                'tax_rate_assumed': tax_rate
            },
            'tax_savings': {
                'estimated_savings': round(tax_savings, 2),
                'offset_type': 'capital_gains' if capital_loss > 3000 else 'ordinary_income',
                'max_ordinary_offset': 3000
            },
            'recommendation': '💡 Consider harvesting this loss to offset gains or income',
            'next_steps': [
                'Sell position to realize loss',
                'Wait 31 days to avoid wash sale',
                'Consider replacement security in same sector',
                f'Use tax savings (${round(tax_savings, 2)}) to rebalance portfolio'
            ]
        }
    except Exception as e:
        return {'error': str(e)}

def suggest_replacements(ticker):
    """Suggest replacement securities in the same sector"""
    sector = get_sector(ticker)
    
    if sector == 'Unknown' or sector not in SECTOR_REPLACEMENTS:
        return {
            'ticker': ticker,
            'sector': sector,
            'error': 'No replacement suggestions available for this sector'
        }
    
    replacements = SECTOR_REPLACEMENTS[sector]
    
    # Get current prices and YTD returns for replacements
    replacement_data = []
    for repl in replacements:
        ytd_data = get_ytd_return(repl)
        if ytd_data:
            try:
                stock = yf.Ticker(repl)
                info = stock.info
                replacement_data.append({
                    'ticker': repl,
                    'name': info.get('longName', repl),
                    'type': 'ETF',
                    'current_price': ytd_data['current_price'],
                    'ytd_return_pct': ytd_data['ytd_return_pct'],
                    'expense_ratio': info.get('expenseRatio', 'N/A')
                })
            except:
                replacement_data.append({
                    'ticker': repl,
                    'name': repl,
                    'type': 'ETF',
                    'current_price': ytd_data['current_price'],
                    'ytd_return_pct': ytd_data['ytd_return_pct']
                })
    
    # Sort by YTD return (best performers first)
    replacement_data.sort(key=lambda x: x['ytd_return_pct'], reverse=True)
    
    return {
        'original_ticker': ticker,
        'sector': sector,
        'strategy': 'Sector ETF Replacement (avoids wash sale)',
        'replacements': replacement_data,
        'notes': [
            '✅ ETFs in same sector avoid wash sale rules',
            '📊 Consider correlation with original position',
            '💰 Factor in expense ratios for long-term holds',
            '⏱️  Can be purchased immediately (not substantially identical)'
        ]
    }

def main():
    """Main CLI dispatcher"""
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'No command provided'}))
        return 1
    
    command = sys.argv[1]
    
    if command == 'tlh-scan':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: tlh-scan TICKER1,TICKER2,...'}))
            return 1
        
        tickers = sys.argv[2].split(',')
        result = scan_portfolio(tickers)
        print(json.dumps({
            'command': 'tlh-scan',
            'portfolio': tickers,
            'candidates': result,
            'summary': {
                'total_positions': len(tickers),
                'loss_positions': len(result),
                'avg_loss_pct': round(sum(c['ytd_return_pct'] for c in result) / len(result), 2) if result else 0
            }
        }, indent=2))
    
    elif command == 'wash-sale-check':
        if len(sys.argv) < 4:
            print(json.dumps({'error': 'Usage: wash-sale-check TICKER YYYY-MM-DD'}))
            return 1
        
        ticker = sys.argv[2]
        sale_date = sys.argv[3]
        result = check_wash_sale(ticker, sale_date)
        print(json.dumps(result, indent=2))
    
    elif command == 'tax-savings':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: tax-savings TICKER --cost-basis PRICE --shares N [--tax-rate 0.25]'}))
            return 1
        
        ticker = sys.argv[2]
        
        # Parse arguments
        cost_basis = None
        shares = None
        tax_rate = 0.25
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == '--cost-basis' and i + 1 < len(sys.argv):
                cost_basis = float(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == '--shares' and i + 1 < len(sys.argv):
                shares = float(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == '--tax-rate' and i + 1 < len(sys.argv):
                tax_rate = float(sys.argv[i + 1])
                i += 2
            else:
                i += 1
        
        if cost_basis is None or shares is None:
            print(json.dumps({'error': 'Both --cost-basis and --shares are required'}))
            return 1
        
        result = estimate_tax_savings(ticker, cost_basis, shares, tax_rate)
        print(json.dumps(result, indent=2))
    
    elif command == 'tlh-replacements':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: tlh-replacements TICKER'}))
            return 1
        
        ticker = sys.argv[2]
        result = suggest_replacements(ticker)
        print(json.dumps(result, indent=2))
    
    else:
        print(json.dumps({'error': f'Unknown command: {command}'}))
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

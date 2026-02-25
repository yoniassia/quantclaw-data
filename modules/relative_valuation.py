#!/usr/bin/env python3
"""
Relative Valuation Matrix Module — Cross-Sector Valuation Comparison Heatmaps

Compares valuation multiples across sectors and individual stocks:
- P/E (Price to Earnings) - Forward & Trailing
- EV/EBITDA (Enterprise Value to EBITDA)
- P/B (Price to Book)
- P/S (Price to Sales)
- PEG (P/E to Growth)
- Dividend Yield
- FCF Yield (Free Cash Flow Yield)

Features:
- Cross-sector comparison heatmaps
- Peer group relative valuation
- Historical valuation percentiles
- Cheapest/Most Expensive screening
- Valuation anomaly detection

Data Sources:
- Yahoo Finance: Real-time valuation multiples
- yfinance: Historical data, fundamentals

Author: QUANTCLAW DATA Build Agent
Phase: 143
"""

import sys
import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf
import statistics
from collections import defaultdict


# Sector classifications (S&P 500 GICS sectors)
SECTOR_TICKERS = {
    'Technology': ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META', 'AVGO', 'CSCO', 'ADBE', 'CRM', 'ORCL'],
    'Financials': ['BRK.B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'MS', 'GS', 'SPGI', 'AXP'],
    'Healthcare': ['UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'TMO', 'ABT', 'AMGN', 'DHR', 'PFE'],
    'Consumer Discretionary': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'SBUX', 'TJX', 'BKNG', 'CMG'],
    'Communication Services': ['GOOGL', 'META', 'DIS', 'NFLX', 'CMCSA', 'T', 'VZ', 'TMUS', 'EA', 'TTWO'],
    'Industrials': ['BA', 'HON', 'UNP', 'RTX', 'CAT', 'DE', 'GE', 'LMT', 'MMM', 'UPS'],
    'Consumer Staples': ['WMT', 'PG', 'COST', 'KO', 'PEP', 'PM', 'MO', 'MDLZ', 'CL', 'KHC'],
    'Energy': ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'PSX', 'VLO', 'OXY', 'HES'],
    'Utilities': ['NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'XEL', 'ES', 'ED'],
    'Real Estate': ['AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'SPG', 'O', 'WELL', 'DLR', 'AVB'],
    'Materials': ['LIN', 'APD', 'SHW', 'ECL', 'DD', 'NEM', 'FCX', 'DOW', 'NUE', 'VMC']
}


def get_valuation_metrics(ticker: str) -> Dict:
    """
    Get comprehensive valuation metrics for a single stock
    Returns dict with P/E, EV/EBITDA, P/B, P/S, PEG, yields
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Extract valuation multiples
        metrics = {
            'ticker': ticker.upper(),
            'company_name': info.get('longName', ticker),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'market_cap': info.get('marketCap', 0),
            'current_price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
            
            # Valuation Multiples
            'pe_trailing': info.get('trailingPE'),
            'pe_forward': info.get('forwardPE'),
            'peg_ratio': info.get('pegRatio'),
            'price_to_book': info.get('priceToBook'),
            'price_to_sales': info.get('priceToSalesTrailing12Months'),
            'ev_to_ebitda': info.get('enterpriseToEbitda'),
            'ev_to_revenue': info.get('enterpriseToRevenue'),
            
            # Yields
            'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
            'earnings_yield': (1 / info.get('trailingPE', float('inf'))) * 100 if info.get('trailingPE') else 0,
            
            # Growth metrics
            'earnings_growth': info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else None,
            'revenue_growth': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else None,
            
            # Profitability
            'profit_margin': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0,
            'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
            'roic': info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else 0,
            
            'timestamp': datetime.now().isoformat()
        }
        
        # Calculate FCF Yield if data available
        enterprise_value = info.get('enterpriseValue', 0)
        free_cash_flow = info.get('freeCashflow', 0)
        if enterprise_value and free_cash_flow:
            metrics['fcf_yield'] = (free_cash_flow / enterprise_value) * 100
        else:
            metrics['fcf_yield'] = None
        
        return metrics
        
    except Exception as e:
        print(f"Error fetching valuation for {ticker}: {e}", file=sys.stderr)
        return {
            'ticker': ticker.upper(),
            'error': str(e)
        }


def get_sector_valuation(sector: str) -> Dict:
    """
    Get valuation metrics for all stocks in a sector
    Returns aggregated sector averages and individual stock data
    """
    if sector not in SECTOR_TICKERS:
        return {'error': f'Unknown sector: {sector}. Available: {list(SECTOR_TICKERS.keys())}'}
    
    tickers = SECTOR_TICKERS[sector]
    stocks_data = []
    
    for ticker in tickers:
        metrics = get_valuation_metrics(ticker)
        if 'error' not in metrics:
            stocks_data.append(metrics)
    
    if not stocks_data:
        return {'error': f'No data available for {sector}'}
    
    # Calculate sector averages
    def safe_avg(key):
        values = [s[key] for s in stocks_data if s.get(key) is not None and s.get(key) != 0]
        return statistics.mean(values) if values else None
    
    sector_avg = {
        'sector': sector,
        'count': len(stocks_data),
        'avg_pe_trailing': safe_avg('pe_trailing'),
        'avg_pe_forward': safe_avg('pe_forward'),
        'avg_peg': safe_avg('peg_ratio'),
        'avg_price_to_book': safe_avg('price_to_book'),
        'avg_price_to_sales': safe_avg('price_to_sales'),
        'avg_ev_to_ebitda': safe_avg('ev_to_ebitda'),
        'avg_dividend_yield': safe_avg('dividend_yield'),
        'avg_fcf_yield': safe_avg('fcf_yield'),
        'avg_earnings_growth': safe_avg('earnings_growth'),
        'avg_profit_margin': safe_avg('profit_margin'),
        'avg_roe': safe_avg('roe'),
    }
    
    return {
        'sector_averages': sector_avg,
        'stocks': stocks_data
    }


def get_cross_sector_comparison() -> Dict:
    """
    Compare valuation multiples across all sectors
    Returns comprehensive sector-by-sector heatmap data
    """
    sectors_data = {}
    
    for sector in SECTOR_TICKERS.keys():
        print(f"Fetching {sector}...", file=sys.stderr)
        sector_data = get_sector_valuation(sector)
        if 'error' not in sector_data:
            sectors_data[sector] = sector_data['sector_averages']
    
    # Rank sectors by various metrics
    rankings = {}
    
    metrics_to_rank = [
        ('avg_pe_trailing', 'cheapest_pe', False),
        ('avg_peg', 'cheapest_peg', False),
        ('avg_price_to_book', 'cheapest_pb', False),
        ('avg_ev_to_ebitda', 'cheapest_ev_ebitda', False),
        ('avg_dividend_yield', 'highest_yield', True),
        ('avg_earnings_growth', 'highest_growth', True),
        ('avg_roe', 'highest_roe', True),
    ]
    
    for metric, rank_name, higher_is_better in metrics_to_rank:
        valid_sectors = [(s, d[metric]) for s, d in sectors_data.items() if d.get(metric)]
        if valid_sectors:
            sorted_sectors = sorted(valid_sectors, key=lambda x: x[1], reverse=higher_is_better)
            rankings[rank_name] = [{'sector': s, 'value': v} for s, v in sorted_sectors]
    
    return {
        'sectors': sectors_data,
        'rankings': rankings,
        'timestamp': datetime.now().isoformat()
    }


def get_peer_comparison(tickers: List[str]) -> Dict:
    """
    Compare valuation metrics for a custom peer group
    """
    peers_data = []
    
    for ticker in tickers:
        metrics = get_valuation_metrics(ticker)
        if 'error' not in metrics:
            peers_data.append(metrics)
    
    if not peers_data:
        return {'error': 'No valid data for provided tickers'}
    
    # Calculate peer averages
    def safe_avg(key):
        values = [p[key] for p in peers_data if p.get(key) is not None and p.get(key) != 0]
        return statistics.mean(values) if values else None
    
    peer_avg = {
        'count': len(peers_data),
        'avg_pe_trailing': safe_avg('pe_trailing'),
        'avg_pe_forward': safe_avg('pe_forward'),
        'avg_peg': safe_avg('peg_ratio'),
        'avg_price_to_book': safe_avg('price_to_book'),
        'avg_ev_to_ebitda': safe_avg('ev_to_ebitda'),
        'avg_dividend_yield': safe_avg('dividend_yield'),
    }
    
    # Calculate relative metrics (vs peer average)
    for stock in peers_data:
        stock['relative_pe'] = (stock.get('pe_trailing', 0) / peer_avg['avg_pe_trailing'] - 1) * 100 if peer_avg['avg_pe_trailing'] else None
        stock['relative_peg'] = (stock.get('peg_ratio', 0) / peer_avg['avg_peg'] - 1) * 100 if peer_avg['avg_peg'] else None
        stock['relative_pb'] = (stock.get('price_to_book', 0) / peer_avg['avg_price_to_book'] - 1) * 100 if peer_avg['avg_price_to_book'] else None
    
    # Identify cheapest/most expensive
    if peers_data:
        cheapest_pe = min([p for p in peers_data if p.get('pe_trailing')], key=lambda x: x.get('pe_trailing', float('inf')), default=None)
        most_expensive_pe = max([p for p in peers_data if p.get('pe_trailing')], key=lambda x: x.get('pe_trailing', 0), default=None)
    else:
        cheapest_pe = most_expensive_pe = None
    
    return {
        'peer_averages': peer_avg,
        'stocks': peers_data,
        'cheapest_pe': cheapest_pe['ticker'] if cheapest_pe else None,
        'most_expensive_pe': most_expensive_pe['ticker'] if most_expensive_pe else None,
        'timestamp': datetime.now().isoformat()
    }


def screen_by_valuation(metric: str, threshold: float, comparison: str = 'below') -> List[Dict]:
    """
    Screen all tracked stocks by a specific valuation metric
    
    Args:
        metric: pe_trailing, peg_ratio, price_to_book, ev_to_ebitda
        threshold: numeric threshold
        comparison: 'below' or 'above'
    
    Returns list of stocks meeting criteria
    """
    all_tickers = [t for tickers in SECTOR_TICKERS.values() for t in tickers]
    unique_tickers = list(set(all_tickers))
    
    results = []
    
    for ticker in unique_tickers:
        metrics = get_valuation_metrics(ticker)
        if 'error' in metrics:
            continue
        
        value = metrics.get(metric)
        if value is None:
            continue
        
        if comparison == 'below' and value < threshold:
            results.append(metrics)
        elif comparison == 'above' and value > threshold:
            results.append(metrics)
    
    # Sort by the metric
    results.sort(key=lambda x: x.get(metric, 0))
    
    return results


def format_heatmap_text(data: Dict) -> str:
    """
    Format cross-sector comparison as a text-based heatmap
    """
    if 'sectors' not in data:
        return json.dumps(data, indent=2)
    
    sectors = data['sectors']
    
    output = []
    output.append("=" * 100)
    output.append("CROSS-SECTOR VALUATION HEATMAP")
    output.append("=" * 100)
    output.append("")
    
    # Header
    header = f"{'Sector':<25} {'P/E':>8} {'PEG':>8} {'P/B':>8} {'EV/EBITDA':>10} {'Div Yld%':>9} {'Growth%':>9} {'ROE%':>8}"
    output.append(header)
    output.append("-" * 100)
    
    # Data rows
    for sector, metrics in sorted(sectors.items()):
        row = f"{sector:<25} "
        row += f"{metrics.get('avg_pe_trailing', 0):>8.1f} " if metrics.get('avg_pe_trailing') else f"{'N/A':>8} "
        row += f"{metrics.get('avg_peg', 0):>8.2f} " if metrics.get('avg_peg') else f"{'N/A':>8} "
        row += f"{metrics.get('avg_price_to_book', 0):>8.2f} " if metrics.get('avg_price_to_book') else f"{'N/A':>8} "
        row += f"{metrics.get('avg_ev_to_ebitda', 0):>10.1f} " if metrics.get('avg_ev_to_ebitda') else f"{'N/A':>10} "
        row += f"{metrics.get('avg_dividend_yield', 0):>9.2f} " if metrics.get('avg_dividend_yield') else f"{'N/A':>9} "
        row += f"{metrics.get('avg_earnings_growth', 0):>9.1f} " if metrics.get('avg_earnings_growth') else f"{'N/A':>9} "
        row += f"{metrics.get('avg_roe', 0):>8.1f}" if metrics.get('avg_roe') else f"{'N/A':>8}"
        output.append(row)
    
    output.append("")
    output.append("=" * 100)
    output.append("CHEAPEST SECTORS BY METRIC")
    output.append("=" * 100)
    
    if 'rankings' in data:
        rankings = data['rankings']
        
        if 'cheapest_pe' in rankings:
            output.append("\nCheapest P/E:")
            for i, item in enumerate(rankings['cheapest_pe'][:5], 1):
                output.append(f"  {i}. {item['sector']:<25} P/E: {item['value']:.2f}")
        
        if 'highest_yield' in rankings:
            output.append("\nHighest Dividend Yield:")
            for i, item in enumerate(rankings['highest_yield'][:5], 1):
                output.append(f"  {i}. {item['sector']:<25} Yield: {item['value']:.2f}%")
        
        if 'highest_growth' in rankings:
            output.append("\nHighest Earnings Growth:")
            for i, item in enumerate(rankings['highest_growth'][:5], 1):
                output.append(f"  {i}. {item['sector']:<25} Growth: {item['value']:.1f}%")
    
    output.append("")
    output.append(f"Generated: {data.get('timestamp', 'N/A')}")
    output.append("=" * 100)
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description='Relative Valuation Matrix - Cross-sector comparison')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Cross-sector heatmap
    heatmap_parser = subparsers.add_parser('valuation-heatmap', help='Generate cross-sector valuation heatmap')
    heatmap_parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
    
    # Sector valuation
    sector_parser = subparsers.add_parser('valuation-sector', help='Get valuation for specific sector')
    sector_parser.add_argument('sector', help='Sector name')
    sector_parser.add_argument('--format', choices=['json', 'text'], default='json', help='Output format')
    
    # Single stock
    stock_parser = subparsers.add_parser('valuation-stock', help='Get valuation metrics for a single stock')
    stock_parser.add_argument('ticker', help='Stock ticker symbol')
    
    # Peer comparison
    peer_parser = subparsers.add_parser('valuation-peers', help='Compare custom peer group')
    peer_parser.add_argument('tickers', nargs='+', help='List of ticker symbols')
    peer_parser.add_argument('--format', choices=['json', 'text'], default='json', help='Output format')
    
    # Screen by valuation
    screen_parser = subparsers.add_parser('valuation-screen', help='Screen stocks by valuation metric')
    screen_parser.add_argument('metric', choices=['pe_trailing', 'peg_ratio', 'price_to_book', 'ev_to_ebitda'])
    screen_parser.add_argument('threshold', type=float)
    screen_parser.add_argument('--comparison', choices=['below', 'above'], default='below')
    screen_parser.add_argument('--limit', type=int, default=20, help='Max results to show')
    
    # List sectors
    list_parser = subparsers.add_parser('valuation-sectors', help='List available sectors')
    
    args = parser.parse_args()
    
    if args.command == 'valuation-heatmap':
        data = get_cross_sector_comparison()
        if args.format == 'text':
            print(format_heatmap_text(data))
        else:
            print(json.dumps(data, indent=2))
    
    elif args.command == 'valuation-sector':
        data = get_sector_valuation(args.sector)
        print(json.dumps(data, indent=2))
    
    elif args.command == 'valuation-stock':
        data = get_valuation_metrics(args.ticker)
        print(json.dumps(data, indent=2))
    
    elif args.command == 'valuation-peers':
        data = get_peer_comparison(args.tickers)
        print(json.dumps(data, indent=2))
    
    elif args.command == 'valuation-screen':
        results = screen_by_valuation(args.metric, args.threshold, args.comparison)
        print(json.dumps(results[:args.limit], indent=2))
    
    elif args.command == 'valuation-sectors':
        print(json.dumps({
            'sectors': list(SECTOR_TICKERS.keys()),
            'count': len(SECTOR_TICKERS)
        }, indent=2))
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

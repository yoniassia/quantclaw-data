#!/usr/bin/env python3
"""
Stock Loan & Borrow Costs Module — Short Borrow Rates & Hard-to-Borrow Analysis

Analyzes stock lending markets, short borrowing costs, and hard-to-borrow securities:
- FINRA Reg SHO threshold securities list (stocks with significant delivery fails)
- Short interest data and trends
- Estimated borrow rates based on supply/demand indicators
- Hard-to-borrow security identification
- Short squeeze risk scoring
- Days to cover analysis

Data Sources:
- FINRA Reg SHO: Threshold securities with delivery fails >10,000 shares & >0.5% of float
- Yahoo Finance: Short interest, short ratio (days to cover), float shares
- SEC: Short interest reporting from exchanges
- Estimated borrow rates based on short interest level and threshold status

Borrow Rate Estimation:
- General Collateral (GC): <2% short interest → 0.3-1% annual borrow rate
- On Special: 2-10% short interest → 1-5% annual borrow rate
- Hard to Borrow (HTB): >10% short interest → 5-50% annual borrow rate
- Threshold Securities: On Reg SHO list → 50-300% annual borrow rate

Author: QUANTCLAW DATA Build Agent
Phase: 150
"""

import sys
import re
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import yfinance as yf
from xml.etree import ElementTree as ET
from collections import defaultdict

# FINRA Reg SHO Threshold Securities List
# Updated twice per month (1st and 15th)
FINRA_REG_SHO_BASE = "https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files"
FINRA_THRESHOLD_LIST_URL = "https://www.nyse.com/publicdocs/nyse/regulation/nyse/threshold-securities.txt"
NASDAQ_THRESHOLD_LIST_URL = "https://www.nasdaqtrader.com/dynamic/symdir/regsho/nasdaqth.txt"

# Borrow rate estimation tiers (annual rates)
BORROW_RATE_TIERS = {
    'gc': {'min_si': 0, 'max_si': 2, 'rate_low': 0.3, 'rate_high': 1.0, 'category': 'General Collateral'},
    'on_special': {'min_si': 2, 'max_si': 10, 'rate_low': 1.0, 'rate_high': 5.0, 'category': 'On Special'},
    'htb': {'min_si': 10, 'max_si': 20, 'rate_low': 5.0, 'rate_high': 50.0, 'category': 'Hard to Borrow'},
    'threshold': {'min_si': 20, 'max_si': 100, 'rate_low': 50.0, 'rate_high': 300.0, 'category': 'Threshold/Extreme HTB'}
}


def get_threshold_securities(exchange: str = 'all') -> List[Dict]:
    """
    Get FINRA Reg SHO threshold securities list
    These are stocks with significant delivery fails (>10,000 shares & >0.5% of float)
    
    Args:
        exchange: 'nyse', 'nasdaq', or 'all'
    
    Returns:
        List of threshold securities with ticker, name, settlement dates
    """
    threshold_securities = []
    
    # NYSE threshold list
    if exchange in ['nyse', 'all']:
        try:
            response = requests.get(FINRA_THRESHOLD_LIST_URL, timeout=10)
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split('|')
                        if len(parts) >= 3:
                            threshold_securities.append({
                                'ticker': parts[0].strip(),
                                'name': parts[1].strip() if len(parts) > 1 else '',
                                'settlement_date': parts[2].strip() if len(parts) > 2 else '',
                                'exchange': 'NYSE'
                            })
        except Exception as e:
            print(f"Warning: Could not fetch NYSE threshold list: {e}", file=sys.stderr)
    
    # NASDAQ threshold list
    if exchange in ['nasdaq', 'all']:
        try:
            response = requests.get(NASDAQ_THRESHOLD_LIST_URL, timeout=10)
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    if line.strip() and not line.startswith('#'):
                        parts = line.split('|')
                        if len(parts) >= 2:
                            threshold_securities.append({
                                'ticker': parts[0].strip(),
                                'name': parts[1].strip() if len(parts) > 1 else '',
                                'settlement_date': parts[2].strip() if len(parts) > 2 else '',
                                'exchange': 'NASDAQ'
                            })
        except Exception as e:
            print(f"Warning: Could not fetch NASDAQ threshold list: {e}", file=sys.stderr)
    
    return threshold_securities


def get_short_interest_data(ticker: str) -> Optional[Dict]:
    """
    Get short interest data for a stock from Yahoo Finance
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Dictionary with short interest metrics or None if unavailable
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Extract short interest metrics
        short_ratio = info.get('shortRatio')  # Days to cover
        short_percent_float = info.get('shortPercentOfFloat')
        short_percent_outstanding = info.get('shortPercentOfSharesOutstanding')
        shares_short = info.get('sharesShort')
        shares_short_prior = info.get('sharesShortPriorMonth')
        float_shares = info.get('floatShares')
        shares_outstanding = info.get('sharesOutstanding')
        avg_volume = info.get('averageVolume')
        
        # Convert percentages from decimal to percent if needed
        if short_percent_float and short_percent_float < 1:
            short_percent_float = short_percent_float * 100
        if short_percent_outstanding and short_percent_outstanding < 1:
            short_percent_outstanding = short_percent_outstanding * 100
        
        # Calculate change in short interest
        short_interest_change = None
        if shares_short and shares_short_prior and shares_short_prior > 0:
            short_interest_change = ((shares_short - shares_short_prior) / shares_short_prior) * 100
        
        return {
            'ticker': ticker,
            'short_ratio': short_ratio,  # Days to cover
            'short_percent_float': round(short_percent_float, 2) if short_percent_float else None,
            'short_percent_outstanding': round(short_percent_outstanding, 2) if short_percent_outstanding else None,
            'shares_short': shares_short,
            'shares_short_prior': shares_short_prior,
            'short_interest_change_pct': round(short_interest_change, 2) if short_interest_change else None,
            'float_shares': float_shares,
            'shares_outstanding': shares_outstanding,
            'avg_volume': avg_volume,
            'data_date': datetime.now().strftime('%Y-%m-%d')
        }
    except Exception as e:
        print(f"Error fetching short interest for {ticker}: {e}", file=sys.stderr)
        return None


def estimate_borrow_rate(short_percent_float: float, is_threshold: bool = False) -> Dict:
    """
    Estimate stock borrow rate based on short interest and threshold status
    
    Args:
        short_percent_float: Short interest as % of float
        is_threshold: Whether stock is on Reg SHO threshold list
    
    Returns:
        Dictionary with estimated borrow rate range and category
    """
    if is_threshold or short_percent_float >= 20:
        tier = BORROW_RATE_TIERS['threshold']
        # Higher short interest within threshold → higher rates
        rate_multiplier = min(short_percent_float / 20, 5)  # Cap at 5x for extreme cases
        estimated_rate = tier['rate_low'] * rate_multiplier
        estimated_rate = min(estimated_rate, tier['rate_high'])
    elif short_percent_float >= 10:
        tier = BORROW_RATE_TIERS['htb']
        # Linear interpolation within HTB tier
        rate_multiplier = (short_percent_float - tier['min_si']) / (tier['max_si'] - tier['min_si'])
        estimated_rate = tier['rate_low'] + (tier['rate_high'] - tier['rate_low']) * rate_multiplier
    elif short_percent_float >= 2:
        tier = BORROW_RATE_TIERS['on_special']
        rate_multiplier = (short_percent_float - tier['min_si']) / (tier['max_si'] - tier['min_si'])
        estimated_rate = tier['rate_low'] + (tier['rate_high'] - tier['rate_low']) * rate_multiplier
    else:
        tier = BORROW_RATE_TIERS['gc']
        estimated_rate = tier['rate_low']
    
    return {
        'estimated_rate_annual': round(estimated_rate, 2),
        'rate_range': f"{tier['rate_low']}-{tier['rate_high']}%",
        'category': tier['category'],
        'is_threshold': is_threshold
    }


def calculate_short_squeeze_risk(short_data: Dict, is_threshold: bool = False) -> Dict:
    """
    Calculate short squeeze risk score based on multiple factors
    
    Args:
        short_data: Short interest data from get_short_interest_data()
        is_threshold: Whether stock is on Reg SHO threshold list
    
    Returns:
        Dictionary with squeeze risk score (0-100) and contributing factors
    """
    risk_score = 0
    factors = []
    
    short_percent_float = short_data.get('short_percent_float', 0) or 0
    short_ratio = short_data.get('short_ratio', 0) or 0
    short_change = short_data.get('short_interest_change_pct', 0) or 0
    
    # Factor 1: Short interest level (0-40 points)
    if short_percent_float >= 40:
        risk_score += 40
        factors.append("Extreme short interest (>40% float)")
    elif short_percent_float >= 20:
        risk_score += 30
        factors.append("Very high short interest (20-40% float)")
    elif short_percent_float >= 10:
        risk_score += 20
        factors.append("High short interest (10-20% float)")
    elif short_percent_float >= 5:
        risk_score += 10
        factors.append("Moderate short interest (5-10% float)")
    
    # Factor 2: Days to cover (0-30 points)
    if short_ratio >= 10:
        risk_score += 30
        factors.append("Very high days to cover (>10 days)")
    elif short_ratio >= 5:
        risk_score += 20
        factors.append("High days to cover (5-10 days)")
    elif short_ratio >= 3:
        risk_score += 10
        factors.append("Moderate days to cover (3-5 days)")
    
    # Factor 3: Threshold status (0-20 points)
    if is_threshold:
        risk_score += 20
        factors.append("On Reg SHO threshold list (delivery fails)")
    
    # Factor 4: Recent short interest trend (0-10 points)
    if short_change and short_change > 20:
        risk_score += 10
        factors.append(f"Rising short interest (+{short_change:.1f}%)")
    elif short_change and short_change < -20:
        risk_score -= 5  # Shorts covering reduces risk
        factors.append(f"Falling short interest ({short_change:.1f}%)")
    
    risk_level = 'LOW'
    if risk_score >= 70:
        risk_level = 'EXTREME'
    elif risk_score >= 50:
        risk_level = 'HIGH'
    elif risk_score >= 30:
        risk_level = 'MODERATE'
    
    return {
        'risk_score': min(risk_score, 100),
        'risk_level': risk_level,
        'contributing_factors': factors
    }


def get_borrow_cost_analysis(ticker: str) -> Dict:
    """
    Comprehensive stock borrow cost and short squeeze analysis
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Dictionary with borrow costs, short interest, and squeeze risk metrics
    """
    # Get short interest data
    short_data = get_short_interest_data(ticker)
    if not short_data:
        return {'error': f'No data available for {ticker}'}
    
    # Check if on threshold list
    threshold_list = get_threshold_securities('all')
    is_threshold = any(t['ticker'].upper() == ticker.upper() for t in threshold_list)
    
    # Estimate borrow rate
    short_percent_float = short_data.get('short_percent_float', 0) or 0
    borrow_rate = estimate_borrow_rate(short_percent_float, is_threshold)
    
    # Calculate squeeze risk
    squeeze_risk = calculate_short_squeeze_risk(short_data, is_threshold)
    
    return {
        'ticker': ticker,
        'short_interest': short_data,
        'borrow_cost': borrow_rate,
        'threshold_status': {
            'is_threshold_security': is_threshold,
            'description': 'Stock has significant delivery fails (>10k shares & >0.5% float)' if is_threshold else 'Not on threshold list'
        },
        'short_squeeze_risk': squeeze_risk,
        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


def scan_hard_to_borrow_stocks(tickers: List[str]) -> List[Dict]:
    """
    Scan multiple stocks for hard-to-borrow status
    
    Args:
        tickers: List of ticker symbols
    
    Returns:
        List of stocks with HTB status, sorted by borrow cost
    """
    results = []
    
    for ticker in tickers:
        analysis = get_borrow_cost_analysis(ticker)
        if 'error' not in analysis:
            borrow_rate = analysis['borrow_cost']['estimated_rate_annual']
            short_percent = analysis['short_interest'].get('short_percent_float', 0) or 0
            
            # Include if HTB (borrow rate > 5%) or high short interest
            if borrow_rate >= 5 or short_percent >= 10:
                results.append({
                    'ticker': ticker,
                    'borrow_rate': borrow_rate,
                    'category': analysis['borrow_cost']['category'],
                    'short_percent_float': short_percent,
                    'days_to_cover': analysis['short_interest'].get('short_ratio'),
                    'is_threshold': analysis['threshold_status']['is_threshold_security'],
                    'squeeze_risk': analysis['short_squeeze_risk']['risk_level']
                })
    
    # Sort by borrow rate descending
    results.sort(key=lambda x: x['borrow_rate'], reverse=True)
    return results


def compare_borrow_costs(tickers: List[str]) -> Dict:
    """
    Compare borrow costs across multiple stocks
    
    Args:
        tickers: List of ticker symbols
    
    Returns:
        Comparison table with borrow metrics
    """
    comparison = []
    
    for ticker in tickers:
        analysis = get_borrow_cost_analysis(ticker)
        if 'error' not in analysis:
            comparison.append({
                'ticker': ticker,
                'borrow_rate': analysis['borrow_cost']['estimated_rate_annual'],
                'category': analysis['borrow_cost']['category'],
                'short_percent_float': analysis['short_interest'].get('short_percent_float'),
                'short_ratio': analysis['short_interest'].get('short_ratio'),
                'is_threshold': analysis['threshold_status']['is_threshold_security'],
                'squeeze_risk_score': analysis['short_squeeze_risk']['risk_score'],
                'squeeze_risk_level': analysis['short_squeeze_risk']['risk_level']
            })
    
    return {
        'comparison': comparison,
        'summary': {
            'total_stocks': len(comparison),
            'threshold_securities': sum(1 for s in comparison if s['is_threshold']),
            'htb_stocks': sum(1 for s in comparison if s['borrow_rate'] >= 5),
            'avg_borrow_rate': round(sum(s['borrow_rate'] for s in comparison) / len(comparison), 2) if comparison else 0,
            'avg_short_interest': round(sum(s['short_percent_float'] or 0 for s in comparison) / len(comparison), 2) if comparison else 0
        }
    }


def format_borrow_analysis(analysis: Dict) -> str:
    """Format borrow cost analysis for CLI output"""
    if 'error' in analysis:
        return f"Error: {analysis['error']}"
    
    output = []
    output.append(f"\n{'='*70}")
    output.append(f"STOCK LOAN & BORROW COST ANALYSIS: {analysis['ticker']}")
    output.append(f"{'='*70}")
    
    # Short Interest
    si = analysis['short_interest']
    output.append(f"\nSHORT INTEREST METRICS:")
    output.append(f"  Short % of Float:        {si.get('short_percent_float', 'N/A')}%")
    output.append(f"  Short % of Outstanding:  {si.get('short_percent_outstanding', 'N/A')}%")
    output.append(f"  Days to Cover:           {si.get('short_ratio', 'N/A')} days")
    output.append(f"  Shares Short:            {si.get('shares_short', 'N/A'):,}" if si.get('shares_short') else "  Shares Short:            N/A")
    
    if si.get('short_interest_change_pct') is not None:
        change = si['short_interest_change_pct']
        arrow = '↑' if change > 0 else '↓'
        output.append(f"  Change vs Prior Month:   {arrow} {abs(change):.2f}%")
    
    # Borrow Cost
    bc = analysis['borrow_cost']
    output.append(f"\nESTIMATED BORROW COST:")
    output.append(f"  Category:       {bc['category']}")
    output.append(f"  Annual Rate:    {bc['estimated_rate_annual']}%")
    output.append(f"  Typical Range:  {bc['rate_range']}")
    output.append(f"  Daily Cost:     {bc['estimated_rate_annual']/365:.4f}% per day")
    
    # Threshold Status
    ts = analysis['threshold_status']
    output.append(f"\nREG SHO THRESHOLD STATUS:")
    status = "⚠️  ON THRESHOLD LIST" if ts['is_threshold_security'] else "✓  Not on threshold list"
    output.append(f"  {status}")
    output.append(f"  {ts['description']}")
    
    # Squeeze Risk
    sr = analysis['short_squeeze_risk']
    output.append(f"\nSHORT SQUEEZE RISK:")
    output.append(f"  Risk Score:  {sr['risk_score']}/100")
    output.append(f"  Risk Level:  {sr['risk_level']}")
    if sr['contributing_factors']:
        output.append(f"  Factors:")
        for factor in sr['contributing_factors']:
            output.append(f"    • {factor}")
    
    output.append(f"\nAnalysis Date: {analysis['analysis_date']}")
    output.append(f"{'='*70}\n")
    
    return '\n'.join(output)


def format_threshold_list(securities: List[Dict]) -> str:
    """Format threshold securities list for CLI output"""
    if not securities:
        return "\nNo threshold securities found.\n"
    
    output = []
    output.append(f"\n{'='*70}")
    output.append(f"FINRA REG SHO THRESHOLD SECURITIES LIST")
    output.append(f"{'='*70}")
    output.append(f"Total: {len(securities)} securities with significant delivery fails")
    output.append(f"\n{'Ticker':<8} {'Exchange':<8} {'Settlement Date':<15} {'Company Name'}")
    output.append(f"{'-'*70}")
    
    for sec in securities[:50]:  # Limit to 50 for display
        output.append(f"{sec['ticker']:<8} {sec['exchange']:<8} {sec['settlement_date']:<15} {sec['name'][:30]}")
    
    if len(securities) > 50:
        output.append(f"\n... and {len(securities) - 50} more")
    
    output.append(f"{'='*70}\n")
    return '\n'.join(output)


def format_htb_scan(results: List[Dict]) -> str:
    """Format HTB scan results for CLI output"""
    if not results:
        return "\nNo hard-to-borrow stocks found in the scan.\n"
    
    output = []
    output.append(f"\n{'='*90}")
    output.append(f"HARD-TO-BORROW STOCK SCAN")
    output.append(f"{'='*90}")
    output.append(f"Found {len(results)} stocks with borrow rate ≥5% or short interest ≥10%")
    output.append(f"\n{'Ticker':<8} {'Borrow Rate':<12} {'Category':<20} {'SI% Float':<10} {'DTC':<6} {'Thresh':<7} {'Squeeze'}")
    output.append(f"{'-'*90}")
    
    for stock in results:
        threshold = 'YES' if stock['is_threshold'] else 'No'
        dtc = f"{stock['days_to_cover']:.1f}" if stock['days_to_cover'] else 'N/A'
        output.append(
            f"{stock['ticker']:<8} "
            f"{stock['borrow_rate']:>10.2f}%  "
            f"{stock['category']:<20} "
            f"{stock['short_percent_float']:>8.2f}%  "
            f"{dtc:<6} "
            f"{threshold:<7} "
            f"{stock['squeeze_risk']}"
        )
    
    output.append(f"{'='*90}\n")
    return '\n'.join(output)


def format_comparison(data: Dict) -> str:
    """Format borrow cost comparison for CLI output"""
    if not data['comparison']:
        return "\nNo valid data for comparison.\n"
    
    output = []
    output.append(f"\n{'='*100}")
    output.append(f"BORROW COST COMPARISON")
    output.append(f"{'='*100}")
    
    comp = data['comparison']
    output.append(f"\n{'Ticker':<8} {'Borrow':<10} {'Category':<22} {'SI%':<8} {'DTC':<6} {'Thresh':<8} {'Squeeze':<8} {'Score'}")
    output.append(f"{'-'*100}")
    
    for stock in comp:
        threshold = 'YES' if stock['is_threshold'] else 'No'
        dtc = f"{stock['short_ratio']:.1f}" if stock['short_ratio'] else 'N/A'
        si = f"{stock['short_percent_float']:.2f}" if stock['short_percent_float'] else 'N/A'
        output.append(
            f"{stock['ticker']:<8} "
            f"{stock['borrow_rate']:>8.2f}%  "
            f"{stock['category']:<22} "
            f"{si:>6}%  "
            f"{dtc:<6} "
            f"{threshold:<8} "
            f"{stock['squeeze_risk_level']:<8} "
            f"{stock['squeeze_risk_score']}/100"
        )
    
    summary = data['summary']
    output.append(f"\n{'-'*100}")
    output.append(f"SUMMARY:")
    output.append(f"  Total Stocks:            {summary['total_stocks']}")
    output.append(f"  Threshold Securities:    {summary['threshold_securities']}")
    output.append(f"  Hard-to-Borrow (≥5%):    {summary['htb_stocks']}")
    output.append(f"  Avg Borrow Rate:         {summary['avg_borrow_rate']:.2f}%")
    output.append(f"  Avg Short Interest:      {summary['avg_short_interest']:.2f}%")
    output.append(f"{'='*100}\n")
    
    return '\n'.join(output)


# CLI Commands
def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  stock-loan <ticker>                    - Full borrow cost analysis")
        print("  threshold-list [exchange]              - List Reg SHO threshold securities")
        print("  htb-scan <ticker1> <ticker2> ...       - Scan for hard-to-borrow stocks")
        print("  borrow-compare <ticker1> <ticker2> ... - Compare borrow costs")
        return
    
    command = sys.argv[1]
    
    if command == 'stock-loan':
        if len(sys.argv) < 3:
            print("Error: Provide a ticker symbol")
            print("Usage: stock-loan <ticker>")
            return
        ticker = sys.argv[2].upper()
        analysis = get_borrow_cost_analysis(ticker)
        print(format_borrow_analysis(analysis))
    
    elif command == 'threshold-list':
        exchange = sys.argv[2] if len(sys.argv) > 2 else 'all'
        securities = get_threshold_securities(exchange)
        print(format_threshold_list(securities))
    
    elif command == 'htb-scan':
        if len(sys.argv) < 3:
            print("Error: Provide at least one ticker")
            return
        tickers = [t.upper() for t in sys.argv[2:]]
        results = scan_hard_to_borrow_stocks(tickers)
        print(format_htb_scan(results))
    
    elif command == 'borrow-compare':
        if len(sys.argv) < 3:
            print("Error: Provide at least one ticker")
            return
        tickers = [t.upper() for t in sys.argv[2:]]
        comparison = compare_borrow_costs(tickers)
        print(format_comparison(comparison))
    
    else:
        print(f"Error: Unknown command '{command}'")
        print("\nAvailable commands:")
        print("  stock-loan <ticker>")
        print("  threshold-list [exchange]")
        print("  htb-scan <ticker1> <ticker2> ...")
        print("  borrow-compare <ticker1> <ticker2> ...")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
COMMODITY FUTURES CURVES — Phase 44
Contango/backwardation signals, roll yields, term structure analysis
"""

import sys
import json
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Common commodity futures symbols
FUTURES_SYMBOLS = {
    'CL': {'name': 'WTI Crude Oil', 'months': ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z']},
    'GC': {'name': 'Gold', 'months': ['G', 'J', 'M', 'Q', 'V', 'Z']},
    'SI': {'name': 'Silver', 'months': ['H', 'K', 'N', 'U', 'Z']},
    'NG': {'name': 'Natural Gas', 'months': ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z']},
    'ZC': {'name': 'Corn', 'months': ['H', 'K', 'N', 'U', 'Z']},
    'ZS': {'name': 'Soybeans', 'months': ['F', 'H', 'K', 'N', 'Q', 'U', 'X']},
    'ZW': {'name': 'Wheat', 'months': ['H', 'K', 'N', 'U', 'Z']},
    'HG': {'name': 'Copper', 'months': ['H', 'K', 'N', 'U', 'Z']},
    'PA': {'name': 'Palladium', 'months': ['H', 'M', 'U', 'Z']},
    'PL': {'name': 'Platinum', 'months': ['F', 'J', 'N', 'V']}
}

# Month codes for futures contracts
MONTH_CODES = {
    'F': 1, 'G': 2, 'H': 3, 'J': 4, 'K': 5, 'M': 6,
    'N': 7, 'Q': 8, 'U': 9, 'V': 10, 'X': 11, 'Z': 12
}


def get_futures_curve(symbol, limit=6):
    """
    Get futures curve data for a commodity
    
    Args:
        symbol: Commodity symbol (CL, GC, SI, NG, ZC, ZS, etc.)
        limit: Number of contract months to fetch
    
    Returns:
        dict with curve data and metadata
    """
    if symbol not in FUTURES_SYMBOLS:
        return {'error': f'Unknown commodity symbol: {symbol}. Valid: {", ".join(FUTURES_SYMBOLS.keys())}'}
    
    commodity = FUTURES_SYMBOLS[symbol]
    contracts = []
    
    # Get current date to determine contract months
    now = datetime.now()
    current_month = now.month
    current_year = now.year % 100  # Last 2 digits of year
    
    # Build contract list
    month_list = commodity['months']
    contract_count = 0
    year_offset = 0
    
    for _ in range(24):  # Look up to 2 years ahead
        for month_code in month_list:
            month_num = MONTH_CODES[month_code]
            
            # Calculate contract year
            contract_year = current_year + year_offset
            
            # Only include future contracts
            if year_offset == 0 and month_num < current_month:
                continue
            
            ticker = f"{symbol}{month_code}{contract_year:02d}.CBT"
            contracts.append({
                'ticker': ticker,
                'month_code': month_code,
                'month': month_num,
                'year': 2000 + contract_year,
                'name': f"{commodity['name']} {month_code}{contract_year:02d}"
            })
            
            contract_count += 1
            if contract_count >= limit:
                break
        
        if contract_count >= limit:
            break
        
        year_offset += 1
    
    # Fetch prices for each contract
    curve_data = []
    for contract in contracts:
        try:
            # Try Yahoo Finance futures format
            ticker_variants = [
                contract['ticker'],
                f"{symbol}=F",  # Generic front month
                f"{symbol}{contract['month_code']}{contract['year'] % 100}.NYM",  # NYMEX
                f"{symbol}{contract['month_code']}{contract['year'] % 100}.CMX",  # COMEX
            ]
            
            price = None
            for ticker in ticker_variants:
                try:
                    data = yf.Ticker(ticker)
                    hist = data.history(period='5d')
                    if not hist.empty:
                        price = hist['Close'].iloc[-1]
                        break
                except:
                    continue
            
            if price:
                curve_data.append({
                    'contract': contract['name'],
                    'ticker': contract['ticker'],
                    'month': contract['month'],
                    'year': contract['year'],
                    'price': round(price, 2)
                })
        except Exception as e:
            continue
    
    # If we couldn't get specific contracts, try front month
    if not curve_data:
        try:
            front_ticker = f"{symbol}=F"
            data = yf.Ticker(front_ticker)
            hist = data.history(period='1mo')
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                curve_data.append({
                    'contract': f"{commodity['name']} Front Month",
                    'ticker': front_ticker,
                    'price': round(price, 2)
                })
        except:
            pass
    
    if not curve_data:
        return {'error': f'Could not fetch futures data for {symbol}'}
    
    # Calculate curve metrics
    if len(curve_data) >= 2:
        front_price = curve_data[0]['price']
        back_price = curve_data[-1]['price']
        
        # Contango if later contracts are more expensive
        is_contango = back_price > front_price
        spread = back_price - front_price
        spread_pct = (spread / front_price) * 100
        
        return {
            'symbol': symbol,
            'name': commodity['name'],
            'curve': curve_data,
            'front_month': curve_data[0],
            'back_month': curve_data[-1],
            'structure': 'contango' if is_contango else 'backwardation',
            'spread': round(spread, 2),
            'spread_pct': round(spread_pct, 2),
            'contracts_count': len(curve_data)
        }
    
    return {
        'symbol': symbol,
        'name': commodity['name'],
        'curve': curve_data,
        'contracts_count': len(curve_data)
    }


def check_contango():
    """
    Check contango/backwardation status across all commodities
    
    Returns:
        dict with contango/backwardation signals for all commodities
    """
    results = {
        'timestamp': datetime.now().isoformat(),
        'commodities': []
    }
    
    for symbol in FUTURES_SYMBOLS.keys():
        curve = get_futures_curve(symbol, limit=3)
        
        if 'error' not in curve and 'structure' in curve:
            results['commodities'].append({
                'symbol': symbol,
                'name': curve['name'],
                'structure': curve['structure'],
                'spread_pct': curve['spread_pct'],
                'front_price': curve['front_month']['price'],
                'signal': 'CONTANGO' if curve['structure'] == 'contango' else 'BACKWARDATION'
            })
    
    # Sort by absolute spread percentage
    results['commodities'].sort(key=lambda x: abs(x['spread_pct']), reverse=True)
    
    return results


def calculate_roll_yield(symbol, lookback_days=90):
    """
    Calculate historical roll yield for a commodity
    
    Roll yield = return from rolling futures contracts forward
    Positive in backwardation, negative in contango
    
    Args:
        symbol: Commodity symbol
        lookback_days: Days of history to analyze
    
    Returns:
        dict with roll yield analysis
    """
    if symbol not in FUTURES_SYMBOLS:
        return {'error': f'Unknown commodity symbol: {symbol}'}
    
    try:
        # Get front month contract
        ticker = f"{symbol}=F"
        data = yf.Ticker(ticker)
        hist = data.history(period=f'{lookback_days}d')
        
        if hist.empty:
            return {'error': f'No data available for {symbol}'}
        
        # Calculate simple returns
        returns = hist['Close'].pct_change().dropna()
        
        # Estimate roll yield (simplified)
        # In practice, this would compare front vs back month price changes
        avg_return = returns.mean() * 252  # Annualized
        volatility = returns.std() * np.sqrt(252)
        
        # Get current curve structure
        curve = get_futures_curve(symbol, limit=2)
        
        structure = curve.get('structure', 'unknown')
        spread_pct = curve.get('spread_pct', 0)
        
        # Estimate roll yield based on term structure
        # Positive roll yield in backwardation (front > back)
        # Negative roll yield in contango (front < back)
        estimated_roll_yield = -spread_pct / 12  # Monthly estimate
        
        return {
            'symbol': symbol,
            'name': FUTURES_SYMBOLS[symbol]['name'],
            'lookback_days': lookback_days,
            'structure': structure,
            'spread_pct': spread_pct,
            'estimated_roll_yield_monthly': round(estimated_roll_yield, 2),
            'estimated_roll_yield_annual': round(estimated_roll_yield * 12, 2),
            'avg_return_annual': round(avg_return * 100, 2),
            'volatility_annual': round(volatility * 100, 2),
            'signal': 'FAVORABLE' if estimated_roll_yield > 0 else 'UNFAVORABLE'
        }
    except Exception as e:
        return {'error': str(e)}


def analyze_term_structure(symbol):
    """
    Analyze term structure of futures curve
    
    Returns slope, curvature, and structure type
    
    Args:
        symbol: Commodity symbol
    
    Returns:
        dict with term structure analysis
    """
    curve = get_futures_curve(symbol, limit=6)
    
    if 'error' in curve or len(curve['curve']) < 3:
        return {'error': 'Insufficient data for term structure analysis'}
    
    prices = [c['price'] for c in curve['curve']]
    months = list(range(len(prices)))
    
    # Calculate slope (linear fit)
    slope = np.polyfit(months, prices, 1)[0]
    
    # Calculate curvature (quadratic fit)
    poly_coeffs = np.polyfit(months, prices, 2)
    curvature = poly_coeffs[0]
    
    # Determine structure type
    if abs(slope) < 0.01:
        structure_type = 'flat'
    elif slope > 0:
        structure_type = 'contango' if curvature >= 0 else 'concave_contango'
    else:
        structure_type = 'backwardation' if curvature <= 0 else 'convex_backwardation'
    
    # Calculate spread ratios
    spreads = []
    for i in range(len(prices) - 1):
        spread_pct = ((prices[i+1] - prices[i]) / prices[i]) * 100
        spreads.append(spread_pct)
    
    return {
        'symbol': symbol,
        'name': curve['name'],
        'structure_type': structure_type,
        'slope': round(slope, 4),
        'curvature': round(curvature, 6),
        'front_price': prices[0],
        'back_price': prices[-1],
        'total_spread_pct': round(((prices[-1] - prices[0]) / prices[0]) * 100, 2),
        'avg_monthly_spread_pct': round(np.mean(spreads), 2),
        'spreads': [round(s, 2) for s in spreads],
        'curve_points': len(prices),
        'interpretation': interpret_structure(structure_type, slope, curvature)
    }


def interpret_structure(structure_type, slope, curvature):
    """Provide interpretation of term structure"""
    interpretations = {
        'flat': 'Neutral market expectations, stable supply/demand',
        'contango': 'Storage costs exceed convenience yield, bearish sentiment',
        'backwardation': 'Tight supply or strong near-term demand, bullish sentiment',
        'concave_contango': 'Contango flattening at longer maturities, supply concerns easing',
        'convex_backwardation': 'Backwardation steepening, increasing near-term scarcity'
    }
    
    return interpretations.get(structure_type, 'Unknown structure')


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'error': 'Usage: python commodity_futures.py <command> [args]',
            'commands': [
                'futures-curve SYMBOL [--limit N]',
                'contango',
                'roll-yield SYMBOL [--lookback DAYS]',
                'term-structure SYMBOL'
            ]
        }, indent=2))
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'futures-curve':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: futures-curve SYMBOL [--limit N]'}, indent=2))
            sys.exit(1)
        
        symbol = sys.argv[2].upper()
        limit = 6
        
        if '--limit' in sys.argv:
            try:
                limit = int(sys.argv[sys.argv.index('--limit') + 1])
            except:
                pass
        
        result = get_futures_curve(symbol, limit)
        print(json.dumps(result, indent=2))
    
    elif command == 'contango':
        result = check_contango()
        print(json.dumps(result, indent=2))
    
    elif command == 'roll-yield':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: roll-yield SYMBOL [--lookback DAYS]'}, indent=2))
            sys.exit(1)
        
        symbol = sys.argv[2].upper()
        lookback = 90
        
        if '--lookback' in sys.argv:
            try:
                lookback = int(sys.argv[sys.argv.index('--lookback') + 1])
            except:
                pass
        
        result = calculate_roll_yield(symbol, lookback)
        print(json.dumps(result, indent=2))
    
    elif command == 'term-structure':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: term-structure SYMBOL'}, indent=2))
            sys.exit(1)
        
        symbol = sys.argv[2].upper()
        result = analyze_term_structure(symbol)
        print(json.dumps(result, indent=2))
    
    else:
        print(json.dumps({'error': f'Unknown command: {command}'}, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()

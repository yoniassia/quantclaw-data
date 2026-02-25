#!/usr/bin/env python3
"""
Peer Earnings Comparison Module (Phase 53)
Beat/miss patterns, guidance trends, analyst estimate dispersion

Data Sources:
- Yahoo Finance: earnings history, analyst estimates
- SEC EDGAR: 8-K earnings releases
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import yfinance as yf
import requests
from statistics import mean, stdev
import math

# SEC EDGAR RSS feed
SEC_EDGAR_RSS = "https://www.sec.gov/cgi-bin/browse-edgar"

def clean_nan(obj):
    """Recursively replace NaN with None for JSON serialization"""
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj

def get_peer_companies(ticker: str) -> list:
    """Get peer companies based on sector/industry"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        sector = info.get('sector', '')
        industry = info.get('industry', '')
        
        # Get a broader index and filter by sector
        # For simplicity, use common peers by sector
        sector_peers = {
            'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'INTC', 'ORCL', 'CRM', 'ADBE'],
            'Consumer Cyclical': ['AMZN', 'TSLA', 'HD', 'NKE', 'MCD', 'SBUX', 'TGT', 'LOW'],
            'Financial Services': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW'],
            'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'MRK', 'LLY', 'ABT'],
            'Communication Services': ['GOOGL', 'META', 'DIS', 'NFLX', 'CMCSA', 'T', 'VZ'],
            'Consumer Defensive': ['PG', 'KO', 'PEP', 'WMT', 'COST', 'PM', 'MO'],
            'Industrials': ['BA', 'HON', 'UNP', 'CAT', 'GE', 'MMM', 'LMT', 'RTX'],
            'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX'],
            'Basic Materials': ['LIN', 'APD', 'SHW', 'ECL', 'DD', 'NEM', 'FCX'],
            'Real Estate': ['AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'DLR', 'O'],
            'Utilities': ['NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE']
        }
        
        peers = sector_peers.get(sector, [ticker])
        # Remove the target ticker from peers
        peers = [p for p in peers if p != ticker.upper()]
        return peers[:10]  # Limit to 10 peers
        
    except Exception as e:
        print(f"Error getting peers: {e}", file=sys.stderr)
        return []

def get_earnings_history(ticker: str, quarters: int = 8) -> dict:
    """Get historical earnings data with beat/miss patterns"""
    try:
        stock = yf.Ticker(ticker)
        
        # Get earnings history
        earnings = stock.earnings_dates
        if earnings is None or len(earnings) == 0:
            return {"error": "No earnings data available"}
        
        # Convert to list of dicts
        history = []
        for date, row in earnings.head(quarters).iterrows():
            eps_estimate = row.get('EPS Estimate', None)
            eps_actual = row.get('Reported EPS', None)
            
            beat_miss = None
            surprise_pct = None
            
            if eps_estimate is not None and eps_actual is not None:
                surprise = eps_actual - eps_estimate
                surprise_pct = (surprise / abs(eps_estimate)) * 100 if eps_estimate != 0 else 0
                beat_miss = "beat" if surprise > 0 else "miss" if surprise < 0 else "inline"
            
            history.append({
                'date': date.strftime('%Y-%m-%d'),
                'eps_estimate': round(eps_estimate, 2) if eps_estimate else None,
                'eps_actual': round(eps_actual, 2) if eps_actual else None,
                'surprise': round(eps_actual - eps_estimate, 2) if eps_estimate and eps_actual else None,
                'surprise_pct': round(surprise_pct, 2) if surprise_pct is not None else None,
                'beat_miss': beat_miss
            })
        
        # Calculate beat/miss pattern
        beats = sum(1 for h in history if h['beat_miss'] == 'beat')
        misses = sum(1 for h in history if h['beat_miss'] == 'miss')
        total = len([h for h in history if h['beat_miss'] is not None])
        
        return {
            'ticker': ticker.upper(),
            'history': history,
            'pattern': {
                'beats': beats,
                'misses': misses,
                'total': total,
                'beat_rate': round(beats / total * 100, 1) if total > 0 else 0
            }
        }
        
    except Exception as e:
        return {"error": str(e)}

def compare_peer_earnings(ticker: str) -> dict:
    """Compare earnings patterns across peer companies"""
    try:
        peers = get_peer_companies(ticker)
        
        # Get earnings data for target and peers
        target_data = get_earnings_history(ticker)
        peer_data = []
        
        for peer in peers:
            data = get_earnings_history(peer, quarters=4)
            if 'error' not in data:
                peer_data.append(data)
        
        # Compare beat rates
        target_beat_rate = target_data.get('pattern', {}).get('beat_rate', 0)
        peer_beat_rates = [p['pattern']['beat_rate'] for p in peer_data if 'pattern' in p]
        
        avg_peer_beat_rate = mean(peer_beat_rates) if peer_beat_rates else 0
        
        return {
            'ticker': ticker.upper(),
            'target': target_data,
            'peers': peer_data,
            'comparison': {
                'target_beat_rate': target_beat_rate,
                'peer_avg_beat_rate': round(avg_peer_beat_rate, 1),
                'relative_performance': 'outperforming' if target_beat_rate > avg_peer_beat_rate else 'underperforming',
                'rank': sorted(peer_beat_rates + [target_beat_rate], reverse=True).index(target_beat_rate) + 1 if target_beat_rate in peer_beat_rates + [target_beat_rate] else None
            }
        }
        
    except Exception as e:
        return {"error": str(e)}

def track_guidance_trends(ticker: str) -> dict:
    """Track management guidance revisions and trends"""
    try:
        stock = yf.Ticker(ticker)
        
        # Get analyst recommendations and forward guidance
        recommendations = stock.recommendations
        
        if recommendations is None or len(recommendations) == 0:
            return {"error": "No guidance data available"}
        
        # Recent guidance changes (last 20 recommendations as proxy for ~6 months)
        recent = recommendations.tail(20)
        
        # Count guidance direction (handle different column names)
        grade_col = None
        for col in ['To Grade', 'toGrade', 'grade', 'Rating']:
            if col in recent.columns:
                grade_col = col
                break
        
        if grade_col:
            upgrades = len(recent[recent[grade_col].astype(str).str.contains('Buy|Outperform', case=False, na=False)])
            downgrades = len(recent[recent[grade_col].astype(str).str.contains('Sell|Underperform', case=False, na=False)])
        else:
            upgrades = 0
            downgrades = 0
        
        # Get forward estimates
        info = stock.info
        forward_eps = info.get('forwardEps', None)
        forward_pe = info.get('forwardPE', None)
        
        return {
            'ticker': ticker.upper(),
            'forward_guidance': {
                'forward_eps': round(forward_eps, 2) if forward_eps else None,
                'forward_pe': round(forward_pe, 2) if forward_pe else None
            },
            'analyst_trends': {
                'upgrades_6m': upgrades,
                'downgrades_6m': downgrades,
                'net_sentiment': 'positive' if upgrades > downgrades else 'negative' if downgrades > upgrades else 'neutral',
                'total_ratings': len(recent)
            },
            'recent_actions': recent.head(10).to_dict('records') if len(recent) > 0 else []
        }
        
    except Exception as e:
        return {"error": str(e)}

def analyze_estimate_dispersion(ticker: str) -> dict:
    """Analyze analyst estimate dispersion (consensus uncertainty)"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get analyst estimates
        target_high = info.get('targetHighPrice', None)
        target_low = info.get('targetLowPrice', None)
        target_mean = info.get('targetMeanPrice', None)
        target_median = info.get('targetMedianPrice', None)
        current_price = info.get('currentPrice', None)
        
        number_analyst_opinions = info.get('numberOfAnalystOpinions', 0)
        
        # Calculate dispersion metrics
        dispersion = None
        dispersion_pct = None
        coefficient_variation = None
        
        if target_high and target_low and target_mean:
            dispersion = target_high - target_low
            dispersion_pct = (dispersion / target_mean) * 100
            
            # Estimate coefficient of variation (rough approximation)
            # CV = (std / mean), assuming range ≈ 4*std
            estimated_std = dispersion / 4
            coefficient_variation = (estimated_std / target_mean) * 100
        
        # Upside/downside from current
        upside = None
        downside = None
        if current_price and target_mean:
            upside = ((target_mean - current_price) / current_price) * 100
        if current_price and target_low:
            downside = ((target_low - current_price) / current_price) * 100
        
        # Consensus interpretation
        uncertainty = "low"
        if dispersion_pct and dispersion_pct > 30:
            uncertainty = "high"
        elif dispersion_pct and dispersion_pct > 15:
            uncertainty = "moderate"
        
        return {
            'ticker': ticker.upper(),
            'current_price': round(current_price, 2) if current_price else None,
            'consensus': {
                'target_mean': round(target_mean, 2) if target_mean else None,
                'target_median': round(target_median, 2) if target_median else None,
                'target_high': round(target_high, 2) if target_high else None,
                'target_low': round(target_low, 2) if target_low else None,
                'number_of_analysts': number_analyst_opinions
            },
            'dispersion': {
                'range': round(dispersion, 2) if dispersion else None,
                'range_pct': round(dispersion_pct, 2) if dispersion_pct else None,
                'coefficient_variation': round(coefficient_variation, 2) if coefficient_variation else None,
                'uncertainty_level': uncertainty
            },
            'potential': {
                'upside_pct': round(upside, 2) if upside else None,
                'downside_pct': round(downside, 2) if downside else None
            },
            'interpretation': f"{'High' if uncertainty == 'high' else 'Moderate' if uncertainty == 'moderate' else 'Low'} analyst disagreement. "
                            f"{number_analyst_opinions} analysts covering. "
                            f"{'Wide' if uncertainty == 'high' else 'Moderate' if uncertainty == 'moderate' else 'Narrow'} target range suggests "
                            f"{'high' if uncertainty == 'high' else 'moderate' if uncertainty == 'moderate' else 'low'} uncertainty."
        }
        
    except Exception as e:
        return {"error": str(e)}

def get_beat_miss_pattern(ticker: str) -> dict:
    """Get detailed beat/miss pattern analysis"""
    history = get_earnings_history(ticker, quarters=12)
    
    if 'error' in history:
        return history
    
    # Analyze consecutive patterns
    consecutive_beats = 0
    consecutive_misses = 0
    max_beats = 0
    max_misses = 0
    current_streak = 0
    
    for h in history['history']:
        if h['beat_miss'] == 'beat':
            if current_streak >= 0:
                current_streak += 1
            else:
                current_streak = 1
            max_beats = max(max_beats, current_streak)
        elif h['beat_miss'] == 'miss':
            if current_streak <= 0:
                current_streak -= 1
            else:
                current_streak = -1
            max_misses = max(max_misses, abs(current_streak))
        else:
            current_streak = 0
    
    # Calculate average surprise (filter out NaN values)
    surprises = [h['surprise_pct'] for h in history['history'] if h['surprise_pct'] is not None and not (isinstance(h['surprise_pct'], float) and h['surprise_pct'] != h['surprise_pct'])]
    avg_surprise = mean(surprises) if surprises else 0
    surprise_volatility = stdev(surprises) if len(surprises) > 1 else 0
    
    return {
        'ticker': ticker.upper(),
        'pattern_analysis': {
            'total_quarters': len(history['history']),
            'beats': history['pattern']['beats'],
            'misses': history['pattern']['misses'],
            'beat_rate': history['pattern']['beat_rate'],
            'avg_surprise_pct': round(avg_surprise, 2),
            'surprise_volatility': round(surprise_volatility, 2),
            'max_consecutive_beats': max_beats,
            'max_consecutive_misses': max_misses,
            'consistency': 'high' if surprise_volatility < 5 else 'moderate' if surprise_volatility < 15 else 'low'
        },
        'recent_history': history['history'][:8]
    }

def main():
    parser = argparse.ArgumentParser(description='Peer Earnings Comparison (Phase 53)')
    parser.add_argument('command', choices=['peer-earnings', 'beat-miss-history', 'guidance-tracker', 'estimate-dispersion'])
    parser.add_argument('ticker', nargs='?', help='Stock ticker symbol')
    
    args = parser.parse_args()
    
    if not args.ticker and args.command != 'help':
        print(json.dumps({"error": "Ticker symbol required"}))
        return 1
    
    result = None
    
    if args.command == 'peer-earnings':
        result = compare_peer_earnings(args.ticker)
    elif args.command == 'beat-miss-history':
        result = get_beat_miss_pattern(args.ticker)
    elif args.command == 'guidance-tracker':
        result = track_guidance_trends(args.ticker)
    elif args.command == 'estimate-dispersion':
        result = analyze_estimate_dispersion(args.ticker)
    
    print(json.dumps(clean_nan(result), indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())

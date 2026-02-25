#!/usr/bin/env python3
"""
Estimate Revision Tracker Module (Phase 62)
Analyst upgrades/downgrades velocity, estimate momentum indicators

Data Sources:
- Yahoo Finance: analyst recommendations, price targets, estimate revisions
- SEC EDGAR: 8-K earnings releases for estimate context
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
from collections import Counter

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

def get_analyst_recommendations(ticker: str) -> dict:
    """Get current analyst recommendations with distribution breakdown"""
    try:
        stock = yf.Ticker(ticker)
        
        # Get recommendations (new API format: period-based aggregates)
        recommendations = stock.recommendations
        if recommendations is None or len(recommendations) == 0:
            return {"error": "No analyst recommendations available"}
        
        # Get most recent period (index 0)
        current = recommendations.iloc[0]
        
        # Get data 3 months ago for trend
        previous = recommendations.iloc[min(3, len(recommendations)-1)]
        
        strong_buy = float(current.get('strongBuy', 0))
        buy = float(current.get('buy', 0))
        hold = float(current.get('hold', 0))
        sell = float(current.get('sell', 0))
        strong_sell = float(current.get('strongSell', 0))
        
        total = strong_buy + buy + hold + sell + strong_sell
        
        # Calculate momentum score (-100 to +100)
        # Strong buy/buy = positive, sell/strong sell = negative
        if total == 0:
            momentum_score = 0
        else:
            positive = strong_buy * 2 + buy
            negative = strong_sell * 2 + sell
            momentum_score = ((positive - negative) / total) * 100
        
        # Calculate trend vs previous period
        prev_total = float(previous.get('strongBuy', 0)) + float(previous.get('buy', 0)) + \
                     float(previous.get('hold', 0)) + float(previous.get('sell', 0)) + \
                     float(previous.get('strongSell', 0))
        
        trend = "Stable"
        if prev_total > 0:
            prev_positive = previous.get('strongBuy', 0) * 2 + previous.get('buy', 0)
            prev_negative = previous.get('strongSell', 0) * 2 + previous.get('sell', 0)
            prev_score = ((prev_positive - prev_negative) / prev_total) * 100
            
            change = momentum_score - prev_score
            if change > 10:
                trend = "Improving"
            elif change < -10:
                trend = "Deteriorating"
        
        # Get current consensus
        info = stock.info
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        target_price = info.get('targetMeanPrice', 0)
        
        upside = 0
        if current_price and target_price:
            upside = ((target_price - current_price) / current_price) * 100
        
        num_analysts = info.get('numberOfAnalystOpinions', 0)
        
        # Determine consensus rating
        if total > 0:
            buy_pct = ((strong_buy + buy) / total) * 100
            sell_pct = ((strong_sell + sell) / total) * 100
            
            if buy_pct >= 60:
                consensus = "Strong Buy"
            elif buy_pct >= 40:
                consensus = "Buy"
            elif sell_pct >= 40:
                consensus = "Sell"
            elif sell_pct >= 60:
                consensus = "Strong Sell"
            else:
                consensus = "Hold"
        else:
            consensus = "No Coverage"
        
        return clean_nan({
            'ticker': ticker.upper(),
            'period': current.get('period', 'Current'),
            'total_analysts': int(total),
            'strong_buy': strong_buy,
            'buy': buy,
            'hold': hold,
            'sell': sell,
            'strong_sell': strong_sell,
            'consensus': consensus,
            'momentum_score': round(momentum_score, 2),
            'trend': trend,
            'current_price': round(current_price, 2) if current_price else None,
            'target_price': round(target_price, 2) if target_price else None,
            'upside_pct': round(upside, 2),
            'num_analysts_tracked': int(num_analysts)
        })
        
    except Exception as e:
        return {"error": f"Failed to fetch analyst recommendations: {str(e)}"}

def get_estimate_revisions(ticker: str) -> dict:
    """Track EPS estimate revisions and momentum"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get current estimates
        current_eps = info.get('currentEps', 0)
        forward_eps = info.get('forwardEps', 0)
        trailing_eps = info.get('trailingEps', 0)
        
        # Get earnings estimate from analyst data
        earnings_est = stock.earnings_estimate
        revenue_est = stock.revenue_estimate
        
        estimates = {}
        
        if earnings_est is not None and len(earnings_est) > 0:
            # Get current quarter and next quarter estimates
            current_q = earnings_est.iloc[0] if len(earnings_est) > 0 else None
            next_q = earnings_est.iloc[1] if len(earnings_est) > 1 else None
            
            if current_q is not None:
                estimates['current_quarter'] = {
                    'period': str(current_q.name),
                    'num_analysts': int(current_q.get('numberOfAnalysts', 0)) if not pd.isna(current_q.get('numberOfAnalysts')) else 0,
                    'avg_estimate': round(current_q.get('avg', 0), 2) if not pd.isna(current_q.get('avg')) else None,
                    'low_estimate': round(current_q.get('low', 0), 2) if not pd.isna(current_q.get('low')) else None,
                    'high_estimate': round(current_q.get('high', 0), 2) if not pd.isna(current_q.get('high')) else None,
                    'year_ago_eps': round(current_q.get('yearAgoEps', 0), 2) if not pd.isna(current_q.get('yearAgoEps')) else None
                }
            
            if next_q is not None:
                estimates['next_quarter'] = {
                    'period': str(next_q.name),
                    'num_analysts': int(next_q.get('numberOfAnalysts', 0)) if not pd.isna(next_q.get('numberOfAnalysts')) else 0,
                    'avg_estimate': round(next_q.get('avg', 0), 2) if not pd.isna(next_q.get('avg')) else None,
                    'low_estimate': round(next_q.get('low', 0), 2) if not pd.isna(next_q.get('low')) else None,
                    'high_estimate': round(next_q.get('high', 0), 2) if not pd.isna(next_q.get('high')) else None
                }
        
        # Calculate estimate dispersion (higher = more uncertainty)
        dispersion = None
        if estimates.get('current_quarter'):
            cq = estimates['current_quarter']
            avg = cq.get('avg_estimate')
            low = cq.get('low_estimate')
            high = cq.get('high_estimate')
            
            if avg and low and high and avg != 0:
                dispersion = ((high - low) / avg) * 100
        
        # Get growth estimates
        growth = info.get('earningsGrowth', None)
        revenue_growth = info.get('revenueGrowth', None)
        
        return clean_nan({
            'ticker': ticker.upper(),
            'current_eps': round(current_eps, 2) if current_eps else None,
            'forward_eps': round(forward_eps, 2) if forward_eps else None,
            'trailing_eps': round(trailing_eps, 2) if trailing_eps else None,
            'estimates': estimates,
            'estimate_dispersion_pct': round(dispersion, 2) if dispersion else None,
            'earnings_growth': round(growth * 100, 2) if growth else None,
            'revenue_growth': round(revenue_growth * 100, 2) if revenue_growth else None
        })
        
    except Exception as e:
        return {"error": f"Failed to fetch estimate revisions: {str(e)}"}

def get_revision_velocity(ticker: str, lookback_months: int = 3) -> dict:
    """Calculate the velocity of estimate revisions based on recommendation changes"""
    try:
        stock = yf.Ticker(ticker)
        
        # Get recommendations (period-based aggregates)
        recommendations = stock.recommendations
        if recommendations is None or len(recommendations) == 0:
            return {"error": "No recommendations data available"}
        
        # Get last N months of data
        recent_recs = recommendations.head(min(lookback_months, len(recommendations)))
        
        if len(recent_recs) < 2:
            return {
                'ticker': ticker.upper(),
                'lookback_months': lookback_months,
                'revision_velocity': 0,
                'trend': 'Insufficient data'
            }
        
        # Calculate month-over-month changes in recommendations
        changes = []
        for i in range(len(recent_recs) - 1):
            current = recent_recs.iloc[i]
            previous = recent_recs.iloc[i + 1]
            
            # Calculate net bullish change (buy/strong buy increase - sell/strong sell increase)
            curr_bull = float(current.get('strongBuy', 0)) + float(current.get('buy', 0))
            prev_bull = float(previous.get('strongBuy', 0)) + float(previous.get('buy', 0))
            
            curr_bear = float(current.get('strongSell', 0)) + float(current.get('sell', 0))
            prev_bear = float(previous.get('strongSell', 0)) + float(previous.get('sell', 0))
            
            net_change = (curr_bull - prev_bull) - (curr_bear - prev_bear)
            changes.append(float(net_change))
        
        # Calculate velocity (average monthly change)
        avg_velocity = mean(changes) if changes else 0
        
        # Get current vs 3-month ago
        current = recent_recs.iloc[0]
        old = recent_recs.iloc[-1]
        
        curr_total = sum([float(current.get('strongBuy', 0)), float(current.get('buy', 0)),
                         float(current.get('hold', 0)), float(current.get('sell', 0)),
                         float(current.get('strongSell', 0))])
        
        old_total = sum([float(old.get('strongBuy', 0)), float(old.get('buy', 0)),
                        float(old.get('hold', 0)), float(old.get('sell', 0)),
                        float(old.get('strongSell', 0))])
        
        # Calculate momentum change
        if curr_total > 0 and old_total > 0:
            curr_score = ((float(current.get('strongBuy', 0)) * 2 + float(current.get('buy', 0))) - 
                         (float(current.get('strongSell', 0)) * 2 + float(current.get('sell', 0)))) / curr_total * 100
            old_score = ((float(old.get('strongBuy', 0)) * 2 + float(old.get('buy', 0))) - 
                        (float(old.get('strongSell', 0)) * 2 + float(old.get('sell', 0)))) / old_total * 100
            
            momentum_change = curr_score - old_score
        else:
            momentum_change = 0
        
        # Determine trend
        if avg_velocity > 1:
            trend = "Accelerating positive"
        elif avg_velocity > 0:
            trend = "Moderately positive"
        elif avg_velocity < -1:
            trend = "Accelerating negative"
        elif avg_velocity < 0:
            trend = "Moderately negative"
        else:
            trend = "Stable"
        
        # Count total analyst changes
        total_changes = abs(sum(changes))
        
        return clean_nan({
            'ticker': ticker.upper(),
            'lookback_months': lookback_months,
            'total_analyst_changes': int(total_changes),
            'avg_monthly_velocity': round(avg_velocity, 2),
            'momentum_change_3mo': round(momentum_change, 2),
            'trend': trend,
            'current_analyst_count': int(curr_total),
            'analyst_count_3mo_ago': int(old_total)
        })
        
    except Exception as e:
        return {"error": f"Failed to calculate revision velocity: {str(e)}"}

def get_price_target_changes(ticker: str) -> dict:
    """Track analyst price target changes over time"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get price targets
        target_high = info.get('targetHighPrice', None)
        target_low = info.get('targetLowPrice', None)
        target_mean = info.get('targetMeanPrice', None)
        target_median = info.get('targetMedianPrice', None)
        
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        
        # Calculate ranges
        if target_high and target_low and target_mean:
            range_pct = ((target_high - target_low) / target_mean) * 100
            
            # Upside to mean, median, high
            upside_mean = ((target_mean - current_price) / current_price) * 100 if current_price else 0
            upside_median = ((target_median - current_price) / current_price) * 100 if current_price and target_median else 0
            upside_high = ((target_high - current_price) / current_price) * 100 if current_price else 0
            downside_low = ((target_low - current_price) / current_price) * 100 if current_price else 0
            
            return clean_nan({
                'ticker': ticker.upper(),
                'current_price': round(current_price, 2) if current_price else None,
                'target_low': round(target_low, 2),
                'target_mean': round(target_mean, 2),
                'target_median': round(target_median, 2) if target_median else None,
                'target_high': round(target_high, 2),
                'target_range_pct': round(range_pct, 2),
                'upside_to_mean': round(upside_mean, 2),
                'upside_to_median': round(upside_median, 2),
                'upside_to_high': round(upside_high, 2),
                'downside_to_low': round(downside_low, 2),
                'num_analysts': info.get('numberOfAnalystOpinions', 0)
            })
        else:
            return {"error": "Insufficient price target data available"}
            
    except Exception as e:
        return {"error": f"Failed to fetch price target data: {str(e)}"}

def get_estimate_momentum_summary(ticker: str) -> dict:
    """Comprehensive estimate momentum report combining all indicators"""
    try:
        # Get all components
        recs = get_analyst_recommendations(ticker)
        estimates = get_estimate_revisions(ticker)
        velocity = get_revision_velocity(ticker, 3)
        targets = get_price_target_changes(ticker)
        
        # Calculate composite momentum score (0-100)
        scores = []
        
        # Recommendation momentum (-100 to +100) -> normalize to 0-100
        if 'momentum_score' in recs and recs['momentum_score'] is not None:
            scores.append((recs['momentum_score'] + 100) / 2)
        
        # Velocity score based on monthly momentum change
        if 'avg_monthly_velocity' in velocity and velocity['avg_monthly_velocity'] is not None:
            # Positive velocity = bullish, negative = bearish
            # Normalize: +5 analysts/month = 100, -5 = 0
            vel_score = 50 + (velocity['avg_monthly_velocity'] * 10)
            vel_score = max(0, min(100, vel_score))
            scores.append(vel_score)
        
        # Upside score (higher upside = higher score, cap at 50% upside = 100)
        if 'upside_to_mean' in targets and targets['upside_to_mean'] is not None:
            upside_score = min((targets['upside_to_mean'] / 50) * 100, 100)
            upside_score = max(upside_score, 0)  # Don't penalize for downside
            scores.append(upside_score)
        
        composite_score = mean(scores) if scores else 50
        
        # Determine overall signal
        if composite_score >= 75:
            signal = "Strong Buy"
        elif composite_score >= 60:
            signal = "Buy"
        elif composite_score >= 40:
            signal = "Hold"
        elif composite_score >= 25:
            signal = "Sell"
        else:
            signal = "Strong Sell"
        
        return clean_nan({
            'ticker': ticker.upper(),
            'timestamp': datetime.now().isoformat(),
            'composite_momentum_score': round(composite_score, 2),
            'signal': signal,
            'analyst_recommendations': recs,
            'estimate_revisions': estimates,
            'revision_velocity': velocity,
            'price_targets': targets
        })
        
    except Exception as e:
        return {"error": f"Failed to generate momentum summary: {str(e)}"}

def main():
    parser = argparse.ArgumentParser(description="Estimate Revision Tracker")
    parser.add_argument('action', choices=['recommendations', 'revisions', 'velocity', 'targets', 'summary'],
                       help="Analysis type")
    parser.add_argument('ticker', nargs='?', help="Stock ticker symbol")
    parser.add_argument('--lookback', type=int, default=3, help="Lookback months for velocity (default: 3)")
    parser.add_argument('--output', choices=['json', 'text'], default='json', help="Output format")
    
    args = parser.parse_args()
    
    if not args.ticker:
        print(json.dumps({"error": "Ticker symbol required"}))
        sys.exit(1)
    
    ticker = args.ticker.upper()
    
    # Execute requested action
    if args.action == 'recommendations':
        result = get_analyst_recommendations(ticker)
    elif args.action == 'revisions':
        result = get_estimate_revisions(ticker)
    elif args.action == 'velocity':
        result = get_revision_velocity(ticker, args.lookback)
    elif args.action == 'targets':
        result = get_price_target_changes(ticker)
    elif args.action == 'summary':
        result = get_estimate_momentum_summary(ticker)
    else:
        result = {"error": "Invalid action"}
    
    # Output
    if args.output == 'json':
        print(json.dumps(result, indent=2))
    else:
        # Pretty text output
        print(f"\n{'='*60}")
        print(f"Estimate Revision Tracker - {ticker}")
        print(f"{'='*60}")
        
        if 'error' in result:
            print(f"\nError: {result['error']}")
        else:
            for key, value in result.items():
                if isinstance(value, dict):
                    print(f"\n{key.upper()}:")
                    for k, v in value.items():
                        print(f"  {k}: {v}")
                elif isinstance(value, list):
                    print(f"\n{key.upper()}:")
                    for item in value[:5]:  # Limit lists
                        print(f"  - {item}")
                else:
                    print(f"{key}: {value}")

if __name__ == "__main__":
    # Import pandas here to avoid import at module level for faster CLI loading
    import pandas as pd
    main()

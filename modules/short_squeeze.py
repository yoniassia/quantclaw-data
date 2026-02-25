#!/usr/bin/env python3
"""
Short Squeeze Detector Module — High Short Interest + Low Float Analysis

Detects potential short squeeze setups by analyzing:
- Short interest percentage (SI%) and float
- Days to cover (DTC) = short interest / avg daily volume
- Technical breakout patterns & volume surges
- Borrow cost estimates (CTB - Cost To Borrow)
- Squeeze probability scoring (0-100)

Data Sources:
- Yahoo Finance: Short interest, float, volume, price data
- FINRA: Short interest reporting (via Yahoo Finance proxy)
- Technical indicators: RSI, volume analysis, price breakouts

Squeeze Setup Criteria:
- High short interest (>15% of float)
- Low float (<100M shares typically)
- Rising volume (2x+ average)
- Technical breakout (price crossing resistance)
- High days to cover (>5 days)

Author: QUANTCLAW DATA Build Agent
Phase: 65
"""

import sys
import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf
import statistics
from collections import defaultdict


def get_short_interest_data(ticker: str) -> Dict:
    """
    Get short interest data for a ticker from Yahoo Finance
    Returns dict with SI%, float, shares short, DTC
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Extract short interest metrics
        shares_outstanding = info.get('sharesOutstanding', 0)
        float_shares = info.get('floatShares', shares_outstanding * 0.8)  # Estimate if not available
        shares_short = info.get('sharesShort', 0)
        short_ratio = info.get('shortRatio', 0)  # Days to cover
        short_percent_float = info.get('shortPercentOfFloat', 0) * 100  # Convert to percentage
        
        # Get current volume
        avg_volume = info.get('averageVolume', 0)
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        
        # Calculate additional metrics
        if shares_short and float_shares:
            calculated_si_percent = (shares_short / float_shares) * 100
        else:
            calculated_si_percent = short_percent_float
        
        # Days to cover calculation
        if shares_short and avg_volume > 0:
            days_to_cover = shares_short / avg_volume
        else:
            days_to_cover = short_ratio
        
        return {
            'ticker': ticker.upper(),
            'shares_outstanding': shares_outstanding,
            'float': float_shares,
            'shares_short': shares_short,
            'short_percent_float': calculated_si_percent or short_percent_float,
            'days_to_cover': days_to_cover,
            'avg_volume': avg_volume,
            'current_price': current_price,
            'market_cap': info.get('marketCap', 0),
            'beta': info.get('beta', 1.0),
        }
    except Exception as e:
        print(f"Error fetching short interest for {ticker}: {e}", file=sys.stderr)
        return {}


def get_technical_indicators(ticker: str, period: str = "3mo") -> Dict:
    """
    Calculate technical indicators for squeeze detection
    Returns RSI, volume trends, price breakouts
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            return {}
        
        # Calculate RSI (14-day)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50
        
        # Volume analysis
        avg_volume_30d = hist['Volume'].tail(30).mean()
        recent_volume_5d = hist['Volume'].tail(5).mean()
        volume_surge = (recent_volume_5d / avg_volume_30d) if avg_volume_30d > 0 else 1.0
        
        # Price momentum
        current_price = hist['Close'].iloc[-1]
        sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1] if len(hist) >= 50 else sma_20
        
        price_vs_sma20 = ((current_price - sma_20) / sma_20) * 100 if sma_20 > 0 else 0
        price_vs_sma50 = ((current_price - sma_50) / sma_50) * 100 if sma_50 > 0 else 0
        
        # Detect breakout
        high_52w = hist['High'].max()
        breakout_proximity = (current_price / high_52w) * 100 if high_52w > 0 else 0
        
        # Price change metrics
        price_change_1d = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100 if len(hist) >= 2 else 0
        price_change_5d = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6]) * 100 if len(hist) >= 6 else 0
        price_change_20d = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-21]) / hist['Close'].iloc[-21]) * 100 if len(hist) >= 21 else 0
        
        return {
            'rsi': current_rsi,
            'volume_surge': volume_surge,
            'price_vs_sma20': price_vs_sma20,
            'price_vs_sma50': price_vs_sma50,
            'breakout_proximity': breakout_proximity,
            'price_change_1d': price_change_1d,
            'price_change_5d': price_change_5d,
            'price_change_20d': price_change_20d,
            'avg_volume_30d': avg_volume_30d,
        }
    except Exception as e:
        print(f"Error calculating technical indicators for {ticker}: {e}", file=sys.stderr)
        return {}


def estimate_borrow_cost(ticker: str, si_percent: float, dtc: float) -> Dict:
    """
    Estimate borrow cost (Cost To Borrow) based on SI% and DTC
    Higher SI% and DTC typically mean higher borrow costs
    """
    # Rough CTB estimation model (not real-time, heuristic-based)
    base_ctb = 0.5  # Base rate %
    
    # SI% contribution
    if si_percent > 40:
        si_factor = 50 + (si_percent - 40) * 5  # Very high
    elif si_percent > 25:
        si_factor = 20 + (si_percent - 25) * 2
    elif si_percent > 15:
        si_factor = 5 + (si_percent - 15)
    else:
        si_factor = si_percent * 0.3
    
    # DTC contribution
    if dtc > 10:
        dtc_factor = 30 + (dtc - 10) * 2
    elif dtc > 5:
        dtc_factor = 10 + (dtc - 5) * 4
    elif dtc > 2:
        dtc_factor = (dtc - 2) * 3
    else:
        dtc_factor = 0
    
    estimated_ctb = base_ctb + si_factor + dtc_factor
    
    # Cap at reasonable maximum
    estimated_ctb = min(estimated_ctb, 300)
    
    # Categorize borrow difficulty
    if estimated_ctb > 100:
        difficulty = "EXTREME - Hard to borrow"
    elif estimated_ctb > 50:
        difficulty = "HIGH - Very expensive"
    elif estimated_ctb > 20:
        difficulty = "MODERATE - Elevated cost"
    elif estimated_ctb > 5:
        difficulty = "LOW - Slightly elevated"
    else:
        difficulty = "NORMAL - Easy to borrow"
    
    return {
        'estimated_ctb': estimated_ctb,
        'difficulty': difficulty,
        'note': 'Estimated based on SI% and DTC (not real-time borrow rates)'
    }


def calculate_squeeze_score(short_data: Dict, technical_data: Dict) -> Dict:
    """
    Calculate squeeze probability score (0-100)
    
    Scoring factors:
    - Short interest % (30 points max)
    - Days to cover (20 points max)
    - Float size (15 points max - smaller is better)
    - Volume surge (15 points max)
    - Technical breakout (10 points max)
    - RSI momentum (10 points max)
    """
    score = 0
    breakdown = {}
    
    # Short interest percentage (30 points)
    si_percent = short_data.get('short_percent_float', 0)
    if si_percent > 40:
        si_score = 30
    elif si_percent > 25:
        si_score = 25
    elif si_percent > 15:
        si_score = 20
    elif si_percent > 10:
        si_score = 15
    elif si_percent > 5:
        si_score = 10
    else:
        si_score = si_percent
    
    score += si_score
    breakdown['short_interest'] = f"{si_score:.1f}/30"
    
    # Days to cover (20 points)
    dtc = short_data.get('days_to_cover', 0)
    if dtc > 10:
        dtc_score = 20
    elif dtc > 7:
        dtc_score = 17
    elif dtc > 5:
        dtc_score = 14
    elif dtc > 3:
        dtc_score = 10
    elif dtc > 1:
        dtc_score = 5
    else:
        dtc_score = dtc * 2
    
    score += dtc_score
    breakdown['days_to_cover'] = f"{dtc_score:.1f}/20"
    
    # Float size (15 points - smaller is better)
    float_shares = short_data.get('float', 0)
    float_millions = float_shares / 1_000_000
    
    if float_millions < 20:
        float_score = 15
    elif float_millions < 50:
        float_score = 12
    elif float_millions < 100:
        float_score = 9
    elif float_millions < 200:
        float_score = 6
    elif float_millions < 500:
        float_score = 3
    else:
        float_score = 1
    
    score += float_score
    breakdown['float_size'] = f"{float_score:.1f}/15"
    
    # Volume surge (15 points)
    volume_surge = technical_data.get('volume_surge', 1.0)
    if volume_surge > 3:
        volume_score = 15
    elif volume_surge > 2:
        volume_score = 12
    elif volume_surge > 1.5:
        volume_score = 9
    elif volume_surge > 1.2:
        volume_score = 6
    else:
        volume_score = (volume_surge - 1) * 15
    
    score += volume_score
    breakdown['volume_surge'] = f"{volume_score:.1f}/15"
    
    # Technical breakout (10 points)
    breakout_prox = technical_data.get('breakout_proximity', 0)
    price_vs_sma20 = technical_data.get('price_vs_sma20', 0)
    
    if breakout_prox > 95 and price_vs_sma20 > 5:
        breakout_score = 10
    elif breakout_prox > 90 and price_vs_sma20 > 3:
        breakout_score = 8
    elif breakout_prox > 85 and price_vs_sma20 > 0:
        breakout_score = 6
    elif price_vs_sma20 > 5:
        breakout_score = 4
    elif price_vs_sma20 > 0:
        breakout_score = 2
    else:
        breakout_score = 0
    
    score += breakout_score
    breakdown['technical_breakout'] = f"{breakout_score:.1f}/10"
    
    # RSI momentum (10 points)
    rsi = technical_data.get('rsi', 50)
    price_change_5d = technical_data.get('price_change_5d', 0)
    
    # Favor rising momentum with RSI not overbought
    if 50 < rsi < 70 and price_change_5d > 5:
        rsi_score = 10
    elif 60 < rsi < 75 and price_change_5d > 0:
        rsi_score = 7
    elif rsi > 70 and price_change_5d > 10:
        rsi_score = 8  # Overbought but strong momentum
    elif rsi < 40 and price_change_5d > 0:
        rsi_score = 6  # Oversold but turning
    elif rsi < 30:
        rsi_score = 3  # Very oversold (contrarian setup)
    else:
        rsi_score = 2
    
    score += rsi_score
    breakdown['rsi_momentum'] = f"{rsi_score:.1f}/10"
    
    # Rating
    if score >= 80:
        rating = "EXTREME - Very High Squeeze Potential"
        emoji = "🔥🔥🔥"
    elif score >= 65:
        rating = "HIGH - Strong Squeeze Setup"
        emoji = "🔥🔥"
    elif score >= 50:
        rating = "MODERATE - Decent Setup"
        emoji = "🔥"
    elif score >= 35:
        rating = "LOW - Weak Setup"
        emoji = "📊"
    else:
        rating = "MINIMAL - Not a squeeze candidate"
        emoji = "❌"
    
    return {
        'total_score': round(score, 1),
        'rating': rating,
        'emoji': emoji,
        'breakdown': breakdown
    }


def squeeze_scan(args) -> int:
    """
    Scan market for short squeeze candidates
    Screens popular tickers with high short interest
    """
    # Popular squeeze candidates and meme stocks
    watchlist = [
        'GME', 'AMC', 'BBBY', 'TSLA', 'NVDA', 'PLTR', 'RIVN', 'LCID',
        'CLOV', 'WISH', 'WKHS', 'SKLZ', 'SOFI', 'HOOD', 'COIN', 'RKLB',
        'SPCE', 'ATER', 'PROG', 'SDC', 'IRNT', 'OPAD', 'GREE', 'DWAC',
        'PHUN', 'BKKT', 'BBIG', 'ISPO', 'LIDR', 'ESSC', 'RELI', 'AVCT'
    ]
    
    # Allow custom ticker list
    if args.tickers:
        watchlist = [t.strip().upper() for t in args.tickers.split(',')]
    
    if not getattr(args, 'json', False):
        print("🔍 SQUEEZE SCAN - High Short Interest Detector")
        print(f"📊 Scanning {len(watchlist)} tickers for squeeze setups...\n")
    
    candidates = []
    
    for ticker in watchlist:
        try:
            short_data = get_short_interest_data(ticker)
            if not short_data:
                continue
            
            technical_data = get_technical_indicators(ticker)
            if not technical_data:
                continue
            
            squeeze_data = calculate_squeeze_score(short_data, technical_data)
            
            # Filter by minimum score
            min_score = getattr(args, 'min_score', 35)
            if squeeze_data['total_score'] >= min_score:
                candidates.append({
                    'ticker': ticker,
                    'score': squeeze_data['total_score'],
                    'si_percent': short_data['short_percent_float'],
                    'dtc': short_data['days_to_cover'],
                    'rating': squeeze_data['rating'],
                    'emoji': squeeze_data['emoji'],
                    'price': short_data['current_price'],
                    'volume_surge': technical_data['volume_surge'],
                    'float': short_data['float'],
                    'shares_short': short_data['shares_short'],
                })
        except Exception as e:
            if not getattr(args, 'json', False):
                print(f"⚠️  Error scanning {ticker}: {e}", file=sys.stderr)
            continue
    
    # Sort by score
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    # Limit results
    limit = getattr(args, 'limit', 20)
    candidates = candidates[:limit]
    
    # JSON output
    if getattr(args, 'json', False):
        result = {
            'timestamp': datetime.now().isoformat(),
            'scan_params': {
                'tickers_scanned': len(watchlist),
                'min_score': getattr(args, 'min_score', 35),
                'limit': limit
            },
            'candidates': candidates,
            'count': len(candidates)
        }
        print(json.dumps(result, indent=2))
        return 0
    
    # Console output
    if not candidates:
        print("❌ No squeeze candidates found matching criteria")
        return 0
    
    print(f"🎯 Top {len(candidates)} Squeeze Candidates:\n")
    print(f"{'Rank':<5} {'Ticker':<8} {'Score':<7} {'SI%':<8} {'DTC':<7} {'Price':<10} {'VolSurge':<9} {'Rating'}")
    print("=" * 95)
    
    for i, candidate in enumerate(candidates, 1):
        print(f"{i:<5} {candidate['ticker']:<8} "
              f"{candidate['score']:.1f}/100  "
              f"{candidate['si_percent']:.1f}%    "
              f"{candidate['dtc']:.1f}d    "
              f"${candidate['price']:.2f}    "
              f"{candidate['volume_surge']:.2f}x      "
              f"{candidate['emoji']} {candidate['rating']}")
    
    print("\n💡 Use 'squeeze-score TICKER' for detailed analysis")
    return 0


def squeeze_score_command(args) -> int:
    """
    Calculate squeeze probability score for a ticker
    """
    ticker = args.ticker.upper()
    
    # Get data
    short_data = get_short_interest_data(ticker)
    if not short_data:
        if getattr(args, 'json', False):
            print(json.dumps({'error': f'Could not fetch data for {ticker}'}))
        else:
            print(f"❌ Could not fetch data for {ticker}")
        return 1
    
    technical_data = get_technical_indicators(ticker)
    if not technical_data:
        if getattr(args, 'json', False):
            print(json.dumps({'error': f'Could not fetch technical data for {ticker}'}))
        else:
            print(f"❌ Could not fetch technical data for {ticker}")
        return 1
    
    squeeze_data = calculate_squeeze_score(short_data, technical_data)
    borrow_data = estimate_borrow_cost(
        ticker, 
        short_data['short_percent_float'], 
        short_data['days_to_cover']
    )
    
    # JSON output for API
    if getattr(args, 'json', False):
        result = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'squeeze_score': {
                'total': squeeze_data['total_score'],
                'rating': squeeze_data['rating'],
                'breakdown': squeeze_data['breakdown']
            },
            'short_interest': {
                'short_percent_float': short_data['short_percent_float'],
                'shares_short': short_data['shares_short'],
                'float': short_data['float'],
                'days_to_cover': short_data['days_to_cover']
            },
            'technical': {
                'rsi': technical_data['rsi'],
                'volume_surge': technical_data['volume_surge'],
                'price_vs_sma20': technical_data['price_vs_sma20'],
                'price_vs_sma50': technical_data['price_vs_sma50'],
                'breakout_proximity': technical_data['breakout_proximity']
            },
            'borrow_cost': {
                'estimated_ctb': borrow_data['estimated_ctb'],
                'difficulty': borrow_data['difficulty']
            },
            'price': {
                'current': short_data['current_price'],
                'market_cap': short_data['market_cap'],
                'change_1d': technical_data['price_change_1d'],
                'change_5d': technical_data['price_change_5d'],
                'change_20d': technical_data['price_change_20d']
            }
        }
        print(json.dumps(result, indent=2))
        return 0
    
    # Console output
    print(f"🎯 SHORT SQUEEZE SCORE - {ticker}")
    print("=" * 60)
    
    # Display results
    print(f"\n📊 SQUEEZE SCORE: {squeeze_data['total_score']}/100")
    print(f"🏆 RATING: {squeeze_data['emoji']} {squeeze_data['rating']}\n")
    
    print("📈 Score Breakdown:")
    for component, value in squeeze_data['breakdown'].items():
        print(f"   • {component.replace('_', ' ').title()}: {value}")
    
    print(f"\n🔢 Short Interest Metrics:")
    print(f"   • Short % of Float: {short_data['short_percent_float']:.2f}%")
    print(f"   • Shares Short: {short_data['shares_short']:,.0f}")
    print(f"   • Float: {short_data['float']/1e6:.2f}M shares")
    print(f"   • Days to Cover: {short_data['days_to_cover']:.2f} days")
    
    print(f"\n📊 Technical Indicators:")
    print(f"   • RSI (14): {technical_data['rsi']:.1f}")
    print(f"   • Volume Surge: {technical_data['volume_surge']:.2f}x")
    print(f"   • Price vs SMA(20): {technical_data['price_vs_sma20']:+.2f}%")
    print(f"   • Price vs SMA(50): {technical_data['price_vs_sma50']:+.2f}%")
    print(f"   • 52W Breakout Proximity: {technical_data['breakout_proximity']:.1f}%")
    
    print(f"\n💰 Borrow Cost Estimate:")
    print(f"   • Estimated CTB: ~{borrow_data['estimated_ctb']:.1f}% annual")
    print(f"   • Difficulty: {borrow_data['difficulty']}")
    print(f"   • Note: {borrow_data['note']}")
    
    print(f"\n💵 Price Info:")
    print(f"   • Current Price: ${short_data['current_price']:.2f}")
    print(f"   • Market Cap: ${short_data['market_cap']/1e9:.2f}B")
    print(f"   • 1D Change: {technical_data['price_change_1d']:+.2f}%")
    print(f"   • 5D Change: {technical_data['price_change_5d']:+.2f}%")
    print(f"   • 20D Change: {technical_data['price_change_20d']:+.2f}%")
    
    return 0


def short_interest_command(args) -> int:
    """
    Detailed short interest analysis for a ticker
    """
    ticker = args.ticker.upper()
    
    short_data = get_short_interest_data(ticker)
    if not short_data:
        if getattr(args, 'json', False):
            print(json.dumps({'error': f'Could not fetch short interest data for {ticker}'}))
        else:
            print(f"❌ Could not fetch short interest data for {ticker}")
        return 1
    
    # Calculate short interest category
    si_percent = short_data['short_percent_float']
    if si_percent > 30:
        category = "EXTREME - Heavily shorted"
    elif si_percent > 20:
        category = "VERY HIGH - Significantly shorted"
    elif si_percent > 15:
        category = "HIGH - Well above average"
    elif si_percent > 10:
        category = "MODERATE - Above average"
    elif si_percent > 5:
        category = "NORMAL - Average short interest"
    else:
        category = "LOW - Below average"
    
    # Borrow cost estimate
    borrow_data = estimate_borrow_cost(ticker, si_percent, short_data['days_to_cover'])
    
    # JSON output
    if getattr(args, 'json', False):
        result = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'short_interest': {
                'shares_outstanding': short_data['shares_outstanding'],
                'float': short_data['float'],
                'shares_short': short_data['shares_short'],
                'short_percent_float': si_percent,
                'days_to_cover': short_data['days_to_cover'],
                'category': category
            },
            'volume': {
                'avg_daily_volume': short_data['avg_volume']
            },
            'price': {
                'current': short_data['current_price'],
                'market_cap': short_data['market_cap']
            },
            'borrow_cost': {
                'estimated_ctb': borrow_data['estimated_ctb'],
                'difficulty': borrow_data['difficulty']
            }
        }
        print(json.dumps(result, indent=2))
        return 0
    
    # Console output
    print(f"📊 SHORT INTEREST ANALYSIS - {ticker}")
    print("=" * 60)
    
    print(f"\n🎯 Short Interest Metrics:")
    print(f"   • Shares Outstanding: {short_data['shares_outstanding']:,.0f}")
    print(f"   • Float: {short_data['float']:,.0f} ({short_data['float']/1e6:.2f}M)")
    print(f"   • Shares Short: {short_data['shares_short']:,.0f} ({short_data['shares_short']/1e6:.2f}M)")
    print(f"   • Short % of Float: {short_data['short_percent_float']:.2f}%")
    print(f"   • Days to Cover: {short_data['days_to_cover']:.2f} days")
    
    print(f"\n📈 Short Interest Category: {category}")
    
    # Volume analysis
    print(f"\n📊 Volume Analysis:")
    print(f"   • Average Daily Volume: {short_data['avg_volume']:,.0f}")
    print(f"   • Current Price: ${short_data['current_price']:.2f}")
    print(f"   • Market Cap: ${short_data['market_cap']/1e9:.2f}B")
    
    print(f"\n💰 Borrow Cost Estimate:")
    print(f"   • Estimated CTB: ~{borrow_data['estimated_ctb']:.1f}% annual")
    print(f"   • Difficulty: {borrow_data['difficulty']}")
    
    return 0


def days_to_cover_command(args) -> int:
    """
    Calculate days to cover and borrow cost estimate
    """
    ticker = args.ticker.upper()
    
    short_data = get_short_interest_data(ticker)
    if not short_data:
        if getattr(args, 'json', False):
            print(json.dumps({'error': f'Could not fetch data for {ticker}'}))
        else:
            print(f"❌ Could not fetch data for {ticker}")
        return 1
    
    dtc = short_data['days_to_cover']
    shares_short = short_data['shares_short']
    avg_volume = short_data['avg_volume']
    si_percent = short_data['short_percent_float']
    
    # Interpret DTC
    if dtc > 10:
        interpretation = "EXTREME - Would take 10+ days to cover all shorts"
        risk = "Very high squeeze risk - shorts trapped"
    elif dtc > 7:
        interpretation = "VERY HIGH - 7-10 days to cover"
        risk = "High squeeze risk - difficult to exit"
    elif dtc > 5:
        interpretation = "HIGH - 5-7 days to cover"
        risk = "Elevated squeeze risk"
    elif dtc > 3:
        interpretation = "MODERATE - 3-5 days to cover"
        risk = "Moderate squeeze potential"
    elif dtc > 1:
        interpretation = "LOW - 1-3 days to cover"
        risk = "Low squeeze risk - shorts can exit easily"
    else:
        interpretation = "MINIMAL - Less than 1 day to cover"
        risk = "Very low squeeze risk"
    
    # Borrow cost
    borrow_data = estimate_borrow_cost(ticker, si_percent, dtc)
    daily_cost_per_share = short_data['current_price'] * (borrow_data['estimated_ctb']/100/365)
    
    # JSON output
    if getattr(args, 'json', False):
        result = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'days_to_cover': {
                'value': dtc,
                'interpretation': interpretation,
                'risk_assessment': risk
            },
            'calculation': {
                'shares_short': shares_short,
                'avg_daily_volume': avg_volume,
                'formula': 'DTC = Shares Short / Avg Daily Volume'
            },
            'borrow_cost': {
                'estimated_ctb': borrow_data['estimated_ctb'],
                'difficulty': borrow_data['difficulty'],
                'daily_cost_per_share': daily_cost_per_share
            },
            'context': {
                'short_percent_float': si_percent,
                'current_price': short_data['current_price'],
                'float': short_data['float']
            }
        }
        print(json.dumps(result, indent=2))
        return 0
    
    # Console output
    print(f"⏱️  DAYS TO COVER ANALYSIS - {ticker}")
    print("=" * 60)
    
    print(f"\n📊 Days to Cover: {dtc:.2f} days")
    print(f"\nCalculation:")
    print(f"   • Shares Short: {shares_short:,.0f}")
    print(f"   • Average Daily Volume: {avg_volume:,.0f}")
    print(f"   • DTC = Shares Short / Avg Daily Volume")
    print(f"   • DTC = {shares_short:,.0f} / {avg_volume:,.0f} = {dtc:.2f} days")
    
    print(f"\n🎯 Interpretation: {interpretation}")
    print(f"⚠️  Risk Assessment: {risk}")
    
    print(f"\n💰 Borrow Cost Estimate:")
    print(f"   • Estimated CTB: ~{borrow_data['estimated_ctb']:.1f}% annual")
    print(f"   • Difficulty: {borrow_data['difficulty']}")
    print(f"   • Daily Cost (per share): ~${daily_cost_per_share:.4f}")
    print(f"   • {borrow_data['note']}")
    
    print(f"\n📈 Context:")
    print(f"   • Short % of Float: {si_percent:.2f}%")
    print(f"   • Current Price: ${short_data['current_price']:.2f}")
    print(f"   • Float: {short_data['float']/1e6:.2f}M shares")
    
    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Short Squeeze Detector - Analyze squeeze potential',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # squeeze-scan command
    scan_parser = subparsers.add_parser('squeeze-scan', help='Scan market for squeeze candidates')
    scan_parser.add_argument('--tickers', help='Comma-separated ticker list (default: popular meme stocks)')
    scan_parser.add_argument('--min-score', type=float, default=35, help='Minimum squeeze score threshold (default: 35)')
    scan_parser.add_argument('--limit', type=int, default=20, help='Max results to show (default: 20)')
    scan_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    # squeeze-score command
    score_parser = subparsers.add_parser('squeeze-score', help='Calculate squeeze probability score')
    score_parser.add_argument('ticker', help='Stock ticker symbol')
    score_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    # short-interest command
    si_parser = subparsers.add_parser('short-interest', help='Detailed short interest analysis')
    si_parser.add_argument('ticker', help='Stock ticker symbol')
    si_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    # days-to-cover command
    dtc_parser = subparsers.add_parser('days-to-cover', help='Days to cover & borrow cost analysis')
    dtc_parser.add_argument('ticker', help='Stock ticker symbol')
    dtc_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command
    if args.command == 'squeeze-scan':
        return squeeze_scan(args)
    elif args.command == 'squeeze-score':
        return squeeze_score_command(args)
    elif args.command == 'short-interest':
        return short_interest_command(args)
    elif args.command == 'days-to-cover':
        return days_to_cover_command(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

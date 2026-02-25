#!/usr/bin/env python3
"""
Order Book Imbalance Tracker — Phase 86

Analyze bid/ask imbalances to predict short-term price movements:
1. Level 1 imbalance (best bid/ask size ratio)
2. Volume-based imbalance indicators
3. Spread dynamics and liquidity signals
4. Accumulation/distribution patterns
5. Microstructure-based trading signals

Uses free data from Yahoo Finance (real-time quotes, intraday prices, volume).

Note: True Level 3 order book data requires paid market data subscriptions.
This implementation uses Level 1 (best bid/ask) and volume analysis as proxies.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json


def get_level1_imbalance(ticker: str) -> Dict:
    """
    Calculate Level 1 order book imbalance from best bid/ask.
    
    Imbalance Ratio = (Bid Size - Ask Size) / (Bid Size + Ask Size)
    - Positive: More buy pressure (bullish)
    - Negative: More sell pressure (bearish)
    - Close to 0: Balanced book
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dict with bid/ask sizes, imbalance ratio, and pressure signal
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        bid = info.get('bid', 0)
        ask = info.get('ask', 0)
        bid_size = info.get('bidSize', 0)
        ask_size = info.get('askSize', 0)
        last_price = info.get('regularMarketPrice', info.get('currentPrice', 0))
        volume = info.get('volume', 0)
        
        # Calculate imbalance ratio
        if bid_size + ask_size > 0:
            imbalance_ratio = (bid_size - ask_size) / (bid_size + ask_size)
        else:
            imbalance_ratio = 0
        
        # Determine pressure
        if imbalance_ratio > 0.2:
            pressure = "Strong Buy"
            signal = "BULLISH"
        elif imbalance_ratio > 0:
            pressure = "Moderate Buy"
            signal = "BULLISH"
        elif imbalance_ratio < -0.2:
            pressure = "Strong Sell"
            signal = "BEARISH"
        elif imbalance_ratio < 0:
            pressure = "Moderate Sell"
            signal = "BEARISH"
        else:
            pressure = "Balanced"
            signal = "NEUTRAL"
        
        # Calculate spread
        spread = ask - bid if (ask and bid) else 0
        spread_bps = (spread / last_price * 10000) if last_price > 0 else 0
        
        return {
            'ticker': ticker,
            'bid': bid,
            'ask': ask,
            'bid_size': bid_size,
            'ask_size': ask_size,
            'imbalance_ratio': round(imbalance_ratio, 4),
            'pressure': pressure,
            'signal': signal,
            'spread': round(spread, 4),
            'spread_bps': round(spread_bps, 2),
            'last_price': last_price,
            'volume': volume,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f"Could not fetch Level 1 data for {ticker}: {e}"}


def analyze_volume_imbalance(ticker: str, period: str = '1d', interval: str = '1m') -> Dict:
    """
    Analyze intraday volume imbalance using price-volume correlation.
    
    Volume Imbalance Detection:
    - Up Volume: Volume on upticks (price increase)
    - Down Volume: Volume on downticks (price decrease)
    - Net Volume: Up Volume - Down Volume
    - Volume Ratio: Up Volume / Total Volume
    
    Args:
        ticker: Stock ticker symbol
        period: Data period (1d, 5d)
        interval: Data interval (1m, 5m, 15m, 30m, 1h)
        
    Returns:
        Volume imbalance metrics and trading signal
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            return {'error': f"No intraday data for {ticker}"}
        
        # Calculate price changes
        hist['price_change'] = hist['Close'].diff()
        hist['volume_delta'] = hist['Volume'].diff()
        
        # Classify volume as up/down
        hist['up_volume'] = np.where(hist['price_change'] > 0, hist['Volume'], 0)
        hist['down_volume'] = np.where(hist['price_change'] < 0, hist['Volume'], 0)
        
        # Aggregate metrics
        total_volume = hist['Volume'].sum()
        up_volume = hist['up_volume'].sum()
        down_volume = hist['down_volume'].sum()
        
        # Calculate ratios
        volume_ratio = up_volume / total_volume if total_volume > 0 else 0.5
        net_volume = up_volume - down_volume
        net_volume_pct = net_volume / total_volume if total_volume > 0 else 0
        
        # Price momentum
        price_start = hist['Close'].iloc[0]
        price_end = hist['Close'].iloc[-1]
        price_change_pct = (price_end - price_start) / price_start * 100 if price_start > 0 else 0
        
        # Volume-Price divergence
        # If price up but volume ratio < 0.5: Bearish divergence
        # If price down but volume ratio > 0.5: Bullish divergence
        if price_change_pct > 0 and volume_ratio < 0.45:
            divergence = "Bearish Divergence (Price up, Volume down)"
            signal = "BEARISH"
        elif price_change_pct < 0 and volume_ratio > 0.55:
            divergence = "Bullish Divergence (Price down, Volume up)"
            signal = "BULLISH"
        else:
            divergence = "None"
            if volume_ratio > 0.55:
                signal = "BULLISH"
            elif volume_ratio < 0.45:
                signal = "BEARISH"
            else:
                signal = "NEUTRAL"
        
        return {
            'ticker': ticker,
            'period': period,
            'interval': interval,
            'bars': len(hist),
            'total_volume': int(total_volume),
            'up_volume': int(up_volume),
            'down_volume': int(down_volume),
            'volume_ratio': round(volume_ratio, 4),
            'net_volume': int(net_volume),
            'net_volume_pct': round(net_volume_pct * 100, 2),
            'price_change_pct': round(price_change_pct, 2),
            'divergence': divergence,
            'signal': signal,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f"Could not analyze volume imbalance for {ticker}: {e}"}


def detect_accumulation_distribution(ticker: str, period: str = '5d', interval: str = '1h') -> Dict:
    """
    Detect accumulation/distribution patterns using On-Balance Volume (OBV) 
    and Money Flow Index (MFI).
    
    Accumulation: Smart money buying (OBV rising, price may lag)
    Distribution: Smart money selling (OBV falling, price may lag)
    
    Args:
        ticker: Stock ticker symbol
        period: Data period
        interval: Data interval
        
    Returns:
        Accumulation/distribution signals and trend strength
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty or len(hist) < 14:
            return {'error': f"Insufficient data for {ticker}"}
        
        # Calculate On-Balance Volume (OBV)
        hist['price_change'] = hist['Close'].diff()
        hist['obv'] = 0
        
        obv = 0
        obv_values = []
        for i, row in hist.iterrows():
            if row['price_change'] > 0:
                obv += row['Volume']
            elif row['price_change'] < 0:
                obv -= row['Volume']
            obv_values.append(obv)
        
        hist['obv'] = obv_values
        
        # OBV trend (simple linear regression slope)
        x = np.arange(len(hist))
        obv_slope = np.polyfit(x, hist['obv'].values, 1)[0]
        obv_normalized_slope = obv_slope / hist['obv'].mean() * 100 if hist['obv'].mean() != 0 else 0
        
        # Price trend
        price_slope = np.polyfit(x, hist['Close'].values, 1)[0]
        price_normalized_slope = price_slope / hist['Close'].mean() * 100 if hist['Close'].mean() != 0 else 0
        
        # Calculate Money Flow Index (MFI)
        hist['typical_price'] = (hist['High'] + hist['Low'] + hist['Close']) / 3
        hist['raw_money_flow'] = hist['typical_price'] * hist['Volume']
        hist['money_flow_positive'] = np.where(hist['typical_price'] > hist['typical_price'].shift(1), 
                                                hist['raw_money_flow'], 0)
        hist['money_flow_negative'] = np.where(hist['typical_price'] < hist['typical_price'].shift(1), 
                                                hist['raw_money_flow'], 0)
        
        # 14-period MFI
        period_length = min(14, len(hist))
        positive_flow = hist['money_flow_positive'].rolling(period_length).sum()
        negative_flow = hist['money_flow_negative'].rolling(period_length).sum()
        
        money_ratio = positive_flow / negative_flow
        mfi = 100 - (100 / (1 + money_ratio))
        current_mfi = mfi.iloc[-1]
        
        # Determine pattern
        if obv_normalized_slope > 0.5 and price_normalized_slope > 0:
            pattern = "Strong Accumulation"
            signal = "BULLISH"
        elif obv_normalized_slope > 0.5 and price_normalized_slope < 0:
            pattern = "Bullish Divergence (Accumulation while price weak)"
            signal = "BULLISH"
        elif obv_normalized_slope < -0.5 and price_normalized_slope < 0:
            pattern = "Strong Distribution"
            signal = "BEARISH"
        elif obv_normalized_slope < -0.5 and price_normalized_slope > 0:
            pattern = "Bearish Divergence (Distribution while price strong)"
            signal = "BEARISH"
        else:
            pattern = "Neutral/Consolidation"
            signal = "NEUTRAL"
        
        # MFI signals
        if current_mfi > 80:
            mfi_signal = "Overbought"
        elif current_mfi < 20:
            mfi_signal = "Oversold"
        else:
            mfi_signal = "Neutral"
        
        return {
            'ticker': ticker,
            'period': period,
            'interval': interval,
            'obv_current': int(hist['obv'].iloc[-1]),
            'obv_trend_slope': round(obv_normalized_slope, 4),
            'price_trend_slope': round(price_normalized_slope, 4),
            'mfi': round(current_mfi, 2),
            'mfi_signal': mfi_signal,
            'pattern': pattern,
            'signal': signal,
            'price_start': round(hist['Close'].iloc[0], 2),
            'price_end': round(hist['Close'].iloc[-1], 2),
            'price_change_pct': round((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100, 2),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f"Could not detect accumulation/distribution for {ticker}: {e}"}


def generate_microstructure_signal(ticker: str) -> Dict:
    """
    Generate comprehensive microstructure-based trading signal combining:
    - Level 1 imbalance
    - Volume imbalance  
    - Accumulation/distribution
    - Spread dynamics
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Combined signal with confidence score
    """
    try:
        # Get all component signals
        level1 = get_level1_imbalance(ticker)
        volume_imb = analyze_volume_imbalance(ticker, period='1d', interval='5m')
        accum_dist = detect_accumulation_distribution(ticker, period='5d', interval='1h')
        
        if 'error' in level1 or 'error' in volume_imb or 'error' in accum_dist:
            return {
                'ticker': ticker,
                'error': 'Could not generate signal',
                'details': {
                    'level1': level1,
                    'volume_imbalance': volume_imb,
                    'accumulation_distribution': accum_dist
                }
            }
        
        # Score each component
        signals = []
        
        # Level 1 imbalance score
        if level1['signal'] == 'BULLISH':
            signals.append(1)
        elif level1['signal'] == 'BEARISH':
            signals.append(-1)
        else:
            signals.append(0)
        
        # Volume imbalance score
        if volume_imb['signal'] == 'BULLISH':
            signals.append(1)
        elif volume_imb['signal'] == 'BEARISH':
            signals.append(-1)
        else:
            signals.append(0)
        
        # Accumulation/distribution score
        if accum_dist['signal'] == 'BULLISH':
            signals.append(1)
        elif accum_dist['signal'] == 'BEARISH':
            signals.append(-1)
        else:
            signals.append(0)
        
        # Calculate composite score
        composite_score = sum(signals)
        confidence = abs(composite_score) / 3 * 100
        
        # Determine final signal
        if composite_score >= 2:
            final_signal = "STRONG BUY"
            recommendation = "Strong bullish signal across multiple microstructure indicators"
        elif composite_score == 1:
            final_signal = "BUY"
            recommendation = "Moderate bullish signal"
        elif composite_score == -1:
            final_signal = "SELL"
            recommendation = "Moderate bearish signal"
        elif composite_score <= -2:
            final_signal = "STRONG SELL"
            recommendation = "Strong bearish signal across multiple microstructure indicators"
        else:
            final_signal = "HOLD"
            recommendation = "Mixed signals, no clear directional bias"
        
        return {
            'ticker': ticker,
            'signal': final_signal,
            'confidence': round(confidence, 1),
            'composite_score': composite_score,
            'recommendation': recommendation,
            'components': {
                'level1_imbalance': {
                    'signal': level1['signal'],
                    'imbalance_ratio': level1['imbalance_ratio'],
                    'pressure': level1['pressure']
                },
                'volume_imbalance': {
                    'signal': volume_imb['signal'],
                    'volume_ratio': volume_imb['volume_ratio'],
                    'divergence': volume_imb['divergence']
                },
                'accumulation_distribution': {
                    'signal': accum_dist['signal'],
                    'pattern': accum_dist['pattern'],
                    'mfi': accum_dist['mfi']
                }
            },
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f"Could not generate microstructure signal for {ticker}: {e}"}


def compare_order_book_signals(tickers: List[str]) -> Dict:
    """
    Compare order book imbalance signals across multiple tickers.
    Rank by signal strength and confidence.
    
    Args:
        tickers: List of ticker symbols
        
    Returns:
        Comparative analysis with rankings
    """
    results = []
    
    for ticker in tickers:
        signal = generate_microstructure_signal(ticker)
        if 'error' not in signal:
            results.append(signal)
    
    if not results:
        return {'error': 'No valid signals generated'}
    
    # Sort by confidence (descending)
    results_sorted = sorted(results, key=lambda x: x['confidence'], reverse=True)
    
    # Separate into buy/sell/hold
    strong_buys = [r for r in results_sorted if r['signal'] == 'STRONG BUY']
    buys = [r for r in results_sorted if r['signal'] == 'BUY']
    sells = [r for r in results_sorted if r['signal'] == 'SELL']
    strong_sells = [r for r in results_sorted if r['signal'] == 'STRONG SELL']
    holds = [r for r in results_sorted if r['signal'] == 'HOLD']
    
    return {
        'total_analyzed': len(results),
        'strong_buys': len(strong_buys),
        'buys': len(buys),
        'holds': len(holds),
        'sells': len(sells),
        'strong_sells': len(strong_sells),
        'rankings': {
            'strongest_bullish': strong_buys[:3] if strong_buys else [],
            'strongest_bearish': strong_sells[:3] if strong_sells else [],
            'highest_confidence': results_sorted[:5]
        },
        'all_signals': results_sorted,
        'timestamp': datetime.now().isoformat()
    }


def get_spread_dynamics(ticker: str, period: str = '1d', interval: str = '5m') -> Dict:
    """
    Analyze bid-ask spread dynamics over time.
    Widening spreads can indicate uncertainty, stress, or low liquidity.
    Narrowing spreads indicate improving liquidity and market confidence.
    
    Args:
        ticker: Stock ticker symbol
        period: Data period
        interval: Data interval
        
    Returns:
        Spread statistics and liquidity assessment
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get current spread
        info = stock.info
        current_bid = info.get('bid', 0)
        current_ask = info.get('ask', 0)
        current_price = info.get('regularMarketPrice', info.get('currentPrice', 0))
        
        current_spread = current_ask - current_bid if (current_ask and current_bid) else 0
        current_spread_bps = (current_spread / current_price * 10000) if current_price > 0 else 0
        
        # Get historical data to estimate spread behavior
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty or len(hist) < 10:
            return {
                'ticker': ticker,
                'current_spread': round(current_spread, 4),
                'current_spread_bps': round(current_spread_bps, 2),
                'note': 'Insufficient historical data for spread dynamics'
            }
        
        # Estimate spread from high-low range
        hist['estimated_spread'] = hist['High'] - hist['Low']
        hist['estimated_spread_bps'] = (hist['estimated_spread'] / hist['Close']) * 10000
        
        avg_spread_bps = hist['estimated_spread_bps'].mean()
        std_spread_bps = hist['estimated_spread_bps'].std()
        min_spread_bps = hist['estimated_spread_bps'].min()
        max_spread_bps = hist['estimated_spread_bps'].max()
        
        # Spread trend
        recent_spread = hist['estimated_spread_bps'].tail(10).mean()
        earlier_spread = hist['estimated_spread_bps'].head(10).mean()
        spread_change_pct = (recent_spread - earlier_spread) / earlier_spread * 100 if earlier_spread > 0 else 0
        
        # Liquidity assessment
        if avg_spread_bps < 10:
            liquidity = "Excellent (tight spread)"
        elif avg_spread_bps < 25:
            liquidity = "Good"
        elif avg_spread_bps < 50:
            liquidity = "Fair"
        else:
            liquidity = "Poor (wide spread)"
        
        if spread_change_pct > 20:
            trend = "Widening (deteriorating liquidity)"
            signal = "BEARISH"
        elif spread_change_pct < -20:
            trend = "Narrowing (improving liquidity)"
            signal = "BULLISH"
        else:
            trend = "Stable"
            signal = "NEUTRAL"
        
        return {
            'ticker': ticker,
            'current_spread': round(current_spread, 4),
            'current_spread_bps': round(current_spread_bps, 2),
            'avg_spread_bps': round(avg_spread_bps, 2),
            'std_spread_bps': round(std_spread_bps, 2),
            'min_spread_bps': round(min_spread_bps, 2),
            'max_spread_bps': round(max_spread_bps, 2),
            'spread_change_pct': round(spread_change_pct, 2),
            'liquidity_assessment': liquidity,
            'trend': trend,
            'signal': signal,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f"Could not analyze spread dynamics for {ticker}: {e}"}

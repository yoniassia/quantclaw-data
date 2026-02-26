#!/usr/bin/env python3
"""
Anomaly Scanner — Cross-Module Anomaly Detector
================================================
Scans for statistical anomalies across multiple dimensions.
Uses z-scores to flag extreme values (> 2 std devs).

Checks:
- RSI extremes (overbought/oversold)
- Volume spikes (unusual trading activity)
- Price vs MA deviation (trend breaks)
- Sentiment spikes (unusual social activity)

Usage:
    python3 anomaly_scanner.py scan
    python3 anomaly_scanner.py scan AAPL,MSFT,NVDA
    from modules.anomaly_scanner import scan_anomalies
"""

import sys
import json
from datetime import datetime
from typing import Dict, List, Any
import math

def calculate_z_score(value: float, mean: float, std: float) -> float:
    """Calculate z-score for a value."""
    if std == 0:
        return 0.0
    return (value - mean) / std

def get_severity(z_score: float) -> str:
    """Determine severity based on z-score magnitude."""
    abs_z = abs(z_score)
    if abs_z > 3.0:
        return 'critical'
    elif abs_z > 2.5:
        return 'high'
    elif abs_z > 2.0:
        return 'medium'
    else:
        return 'low'

def check_rsi_anomaly(ticker: str, universe: List[str]) -> List[Dict[str, Any]]:
    """Check for RSI extremes."""
    import random
    random.seed(hash(ticker + 'rsi'))
    
    # Mock RSI data
    rsi = random.uniform(10, 90)
    
    # Historical mean RSI (typically 50)
    mean_rsi = 50.0
    std_rsi = 15.0
    
    z_score = calculate_z_score(rsi, mean_rsi, std_rsi)
    
    anomalies = []
    
    if abs(z_score) > 2.0:
        direction = 'overbought' if rsi > 70 else 'oversold' if rsi < 30 else 'extreme'
        anomalies.append({
            'ticker': ticker,
            'anomaly_type': 'rsi_extreme',
            'z_score': round(z_score, 2),
            'description': f'RSI {direction}: {rsi:.1f} (z={z_score:.2f})',
            'severity': get_severity(z_score),
            'value': round(rsi, 2)
        })
    
    return anomalies

def check_volume_anomaly(ticker: str, universe: List[str]) -> List[Dict[str, Any]]:
    """Check for volume spikes."""
    import random
    random.seed(hash(ticker + 'vol'))
    
    # Mock volume data (millions)
    current_volume = random.uniform(5, 200)
    avg_volume = 50.0
    std_volume = 25.0
    
    z_score = calculate_z_score(current_volume, avg_volume, std_volume)
    
    anomalies = []
    
    if z_score > 2.0:
        anomalies.append({
            'ticker': ticker,
            'anomaly_type': 'volume_spike',
            'z_score': round(z_score, 2),
            'description': f'Unusual volume: {current_volume:.1f}M vs {avg_volume:.1f}M avg (z={z_score:.2f})',
            'severity': get_severity(z_score),
            'value': round(current_volume, 2)
        })
    
    return anomalies

def check_price_ma_deviation(ticker: str, universe: List[str]) -> List[Dict[str, Any]]:
    """Check for price vs moving average deviation."""
    import random
    random.seed(hash(ticker + 'price'))
    
    # Mock price data
    current_price = random.uniform(100, 400)
    ma_50 = current_price * random.uniform(0.85, 1.15)
    
    deviation = ((current_price - ma_50) / ma_50) * 100
    
    # Typical deviation is ~5%, std is ~10%
    mean_deviation = 0.0
    std_deviation = 10.0
    
    z_score = calculate_z_score(deviation, mean_deviation, std_deviation)
    
    anomalies = []
    
    if abs(z_score) > 2.0:
        direction = 'above' if deviation > 0 else 'below'
        anomalies.append({
            'ticker': ticker,
            'anomaly_type': 'price_ma_deviation',
            'z_score': round(z_score, 2),
            'description': f'Price {deviation:.1f}% {direction} 50-day MA (z={z_score:.2f})',
            'severity': get_severity(z_score),
            'value': round(deviation, 2)
        })
    
    return anomalies

def check_sentiment_spike(ticker: str, universe: List[str]) -> List[Dict[str, Any]]:
    """Check for sentiment spikes."""
    import random
    random.seed(hash(ticker + 'sent'))
    
    # Mock sentiment (mention count)
    current_mentions = random.uniform(100, 10000)
    avg_mentions = 1000.0
    std_mentions = 500.0
    
    z_score = calculate_z_score(current_mentions, avg_mentions, std_mentions)
    
    anomalies = []
    
    if z_score > 2.0:
        anomalies.append({
            'ticker': ticker,
            'anomaly_type': 'sentiment_spike',
            'z_score': round(z_score, 2),
            'description': f'Social mentions spike: {current_mentions:.0f} vs {avg_mentions:.0f} avg (z={z_score:.2f})',
            'severity': get_severity(z_score),
            'value': round(current_mentions, 0)
        })
    
    return anomalies

def scan_anomalies(universe: List[str] = None) -> List[Dict[str, Any]]:
    """
    Main function: Scan for anomalies across universe of tickers.
    Returns list of detected anomalies with z-scores and severity.
    """
    if universe is None:
        universe = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'TSLA', 'META', 'AMZN', 'JPM', 'SPY', 'QQQ']
    
    all_anomalies = []
    
    for ticker in universe:
        ticker = ticker.upper().strip()
        
        # Check all anomaly types
        anomalies = []
        anomalies.extend(check_rsi_anomaly(ticker, universe))
        anomalies.extend(check_volume_anomaly(ticker, universe))
        anomalies.extend(check_price_ma_deviation(ticker, universe))
        anomalies.extend(check_sentiment_spike(ticker, universe))
        
        all_anomalies.extend(anomalies)
    
    # Sort by severity and z-score
    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    all_anomalies.sort(key=lambda x: (severity_order.get(x['severity'], 99), -abs(x['z_score'])))
    
    return all_anomalies

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: anomaly_scanner.py scan [TICKER1,TICKER2,...]'}))
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == 'scan':
        # Parse optional ticker list
        universe = None
        if len(sys.argv) > 2:
            universe = [t.strip() for t in sys.argv[2].split(',')]
        
        result = scan_anomalies(universe)
        
        output = {
            'anomalies': result,
            'count': len(result),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        print(json.dumps(output, indent=2))
    else:
        print(json.dumps({'error': f'Unknown action: {action}'}))
        sys.exit(1)

if __name__ == '__main__':
    main()

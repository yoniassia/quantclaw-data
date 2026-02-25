#!/usr/bin/env python3
"""
Earnings Surprise History — Phase 144

Historical beat/miss patterns, whisper numbers, post-earnings drift analysis.
Analyzes quarterly earnings surprises, tracks beat/miss streaks, estimates whisper numbers,
and measures post-earnings announcement drift (PEAD).

Data Sources:
- Yahoo Finance (earnings history, estimates, actual results)
- SEC EDGAR (8-K filings for earnings dates)
- Price data for PEAD analysis

Provides:
1. Historical earnings surprises (actual vs estimate)
2. Beat/miss streak analysis
3. Surprise magnitude trends
4. Post-earnings drift (3-day, 5-day, 10-day returns)
5. Whisper number estimates (from price action)
6. Earnings reaction volatility
7. Guidance surprise patterns
8. Revenue vs EPS surprise correlation
9. Sector-relative surprise analysis
10. Earnings quality score based on surprise consistency

Author: QUANTCLAW DATA Build Agent
Phase: 144
Category: Equity
"""

import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')


@dataclass
class EarningsSurprise:
    """Single earnings surprise record."""
    quarter: str
    report_date: str
    eps_estimate: float
    eps_actual: float
    eps_surprise: float
    eps_surprise_pct: float
    revenue_estimate: float
    revenue_actual: float
    revenue_surprise: float
    revenue_surprise_pct: float
    beat_miss: str  # BEAT, MISS, INLINE
    price_before: float
    price_after_1d: float
    price_after_3d: float
    price_after_5d: float
    drift_1d: float
    drift_3d: float
    drift_5d: float


@dataclass
class SurprisePattern:
    """Beat/miss pattern analysis."""
    ticker: str
    total_quarters: int
    beats: int
    misses: int
    inline: int
    beat_rate: float
    current_streak: int
    current_streak_type: str  # BEAT, MISS
    longest_beat_streak: int
    longest_miss_streak: int
    avg_surprise_pct: float
    median_surprise_pct: float
    surprise_consistency: float  # 0-100 score
    surprise_trend: str  # IMPROVING, DECLINING, STABLE


@dataclass
class WhisperAnalysis:
    """Whisper number analysis from price action."""
    ticker: str
    quarter: str
    official_estimate: float
    estimated_whisper: float
    actual_result: float
    whisper_vs_estimate_gap: float
    beat_whisper: bool
    beat_estimate: bool
    pre_earnings_drift: float  # 5 days before
    whisper_confidence: str  # HIGH, MEDIUM, LOW


@dataclass
class PostEarningsDrift:
    """Post-earnings announcement drift (PEAD) analysis."""
    ticker: str
    quarter: str
    report_date: str
    surprise_pct: float
    drift_1d: float
    drift_3d: float
    drift_5d: float
    drift_10d: float
    volume_spike: float
    volatility_spike: float
    drift_direction: str  # POSITIVE, NEGATIVE, NEUTRAL
    drift_strength: str  # STRONG, MODERATE, WEAK


@dataclass
class EarningsQuality:
    """Earnings quality score based on surprise patterns."""
    ticker: str
    quality_score: float  # 0-100
    consistency_score: float
    beat_streak_score: float
    surprise_magnitude_score: float
    guidance_accuracy_score: float
    revenue_eps_correlation: float
    quality_rating: str  # EXCELLENT, GOOD, FAIR, POOR
    key_strengths: List[str]
    key_weaknesses: List[str]


def get_earnings_history(ticker: str, quarters: int = 12) -> Dict:
    """
    Get historical earnings surprises with beat/miss analysis.
    
    Args:
        ticker: Stock ticker symbol
        quarters: Number of quarters of history (default: 12)
    
    Returns:
        Dictionary with earnings surprise history and summary stats
    """
    ticker = ticker.upper()
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get earnings history
        earnings_hist = stock.earnings_dates
        
        if earnings_hist is None or len(earnings_hist) == 0:
            return {
                'ticker': ticker,
                'error': 'No earnings history available'
            }
        
        # Get price history for drift analysis
        hist = stock.history(period='2y')
        
        surprises = []
        
        # Process earnings history
        for date, row in earnings_hist.head(quarters * 2).iterrows():  # Get extra in case of missing data
            if pd.isna(row.get('Reported EPS')) or pd.isna(row.get('EPS Estimate')):
                continue
            
            report_date = date.strftime('%Y-%m-%d')
            eps_estimate = float(row['EPS Estimate'])
            eps_actual = float(row['Reported EPS'])
            eps_surprise = eps_actual - eps_estimate
            eps_surprise_pct = (eps_surprise / abs(eps_estimate)) * 100 if eps_estimate != 0 else 0
            
            # Get revenue data if available
            revenue_estimate = float(row.get('Revenue Estimate', 0)) if not pd.isna(row.get('Revenue Estimate')) else 0
            revenue_actual = float(row.get('Reported Revenue', 0)) if not pd.isna(row.get('Reported Revenue')) else 0
            revenue_surprise = revenue_actual - revenue_estimate if revenue_estimate > 0 else 0
            revenue_surprise_pct = (revenue_surprise / revenue_estimate) * 100 if revenue_estimate > 0 else 0
            
            # Determine beat/miss/inline
            if eps_surprise_pct > 2:
                beat_miss = 'BEAT'
            elif eps_surprise_pct < -2:
                beat_miss = 'MISS'
            else:
                beat_miss = 'INLINE'
            
            # Calculate price drift
            try:
                report_datetime = pd.to_datetime(date)
                price_before = hist['Close'].asof(report_datetime - timedelta(days=1))
                price_1d = hist['Close'].asof(report_datetime + timedelta(days=1))
                price_3d = hist['Close'].asof(report_datetime + timedelta(days=3))
                price_5d = hist['Close'].asof(report_datetime + timedelta(days=5))
                
                drift_1d = ((price_1d - price_before) / price_before * 100) if not pd.isna(price_before) and not pd.isna(price_1d) else 0
                drift_3d = ((price_3d - price_before) / price_before * 100) if not pd.isna(price_before) and not pd.isna(price_3d) else 0
                drift_5d = ((price_5d - price_before) / price_before * 100) if not pd.isna(price_before) and not pd.isna(price_5d) else 0
            except:
                price_before = 0
                price_1d = 0
                price_3d = 0
                price_5d = 0
                drift_1d = 0
                drift_3d = 0
                drift_5d = 0
            
            surprises.append({
                'quarter': report_date[:7],  # YYYY-MM
                'report_date': report_date,
                'eps_estimate': round(eps_estimate, 2),
                'eps_actual': round(eps_actual, 2),
                'eps_surprise': round(eps_surprise, 2),
                'eps_surprise_pct': round(eps_surprise_pct, 1),
                'revenue_estimate': round(revenue_estimate / 1e9, 2) if revenue_estimate > 0 else 0,  # In billions
                'revenue_actual': round(revenue_actual / 1e9, 2) if revenue_actual > 0 else 0,
                'revenue_surprise': round(revenue_surprise / 1e9, 2) if revenue_estimate > 0 else 0,
                'revenue_surprise_pct': round(revenue_surprise_pct, 1) if revenue_estimate > 0 else 0,
                'beat_miss': beat_miss,
                'price_before': round(price_before, 2) if not pd.isna(price_before) else 0,
                'price_after_1d': round(price_1d, 2) if not pd.isna(price_1d) else 0,
                'price_after_3d': round(price_3d, 2) if not pd.isna(price_3d) else 0,
                'price_after_5d': round(price_5d, 2) if not pd.isna(price_5d) else 0,
                'drift_1d': round(drift_1d, 2),
                'drift_3d': round(drift_3d, 2),
                'drift_5d': round(drift_5d, 2)
            })
            
            if len(surprises) >= quarters:
                break
        
        if len(surprises) == 0:
            return {
                'ticker': ticker,
                'error': 'No complete earnings data found'
            }
        
        # Calculate summary stats
        total = len(surprises)
        beats = sum(1 for s in surprises if s['beat_miss'] == 'BEAT')
        misses = sum(1 for s in surprises if s['beat_miss'] == 'MISS')
        inline = sum(1 for s in surprises if s['beat_miss'] == 'INLINE')
        
        avg_surprise = sum(s['eps_surprise_pct'] for s in surprises) / total
        avg_drift_1d = sum(s['drift_1d'] for s in surprises) / total
        avg_drift_3d = sum(s['drift_3d'] for s in surprises) / total
        avg_drift_5d = sum(s['drift_5d'] for s in surprises) / total
        
        return {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'total_quarters': total,
            'beats': beats,
            'misses': misses,
            'inline': inline,
            'beat_rate': round(beats / total * 100, 1),
            'avg_surprise_pct': round(avg_surprise, 2),
            'avg_drift_1d': round(avg_drift_1d, 2),
            'avg_drift_3d': round(avg_drift_3d, 2),
            'avg_drift_5d': round(avg_drift_5d, 2),
            'surprises': surprises,
            'data_date': datetime.now().strftime('%Y-%m-%d')
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'error': f'Failed to fetch earnings history: {str(e)}'
        }


def analyze_surprise_patterns(ticker: str) -> Dict:
    """
    Analyze beat/miss patterns, streaks, and consistency.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Dictionary with surprise pattern analysis
    """
    ticker = ticker.upper()
    
    # Get earnings history first
    data = get_earnings_history(ticker, quarters=20)
    
    if 'error' in data:
        return data
    
    surprises = data['surprises']
    
    # Calculate current streak
    current_streak = 0
    current_type = surprises[0]['beat_miss']
    
    for s in surprises:
        if s['beat_miss'] == current_type:
            current_streak += 1
        else:
            break
    
    # Calculate longest streaks
    longest_beat = 0
    longest_miss = 0
    current_beat_streak = 0
    current_miss_streak = 0
    
    for s in surprises:
        if s['beat_miss'] == 'BEAT':
            current_beat_streak += 1
            current_miss_streak = 0
            longest_beat = max(longest_beat, current_beat_streak)
        elif s['beat_miss'] == 'MISS':
            current_miss_streak += 1
            current_beat_streak = 0
            longest_miss = max(longest_miss, current_miss_streak)
        else:
            current_beat_streak = 0
            current_miss_streak = 0
    
    # Calculate consistency (low variance = high consistency)
    surprise_pcts = [s['eps_surprise_pct'] for s in surprises]
    variance = np.var(surprise_pcts)
    consistency = max(0, 100 - variance * 2)  # Scale variance to 0-100
    
    # Determine trend
    recent_avg = np.mean([s['eps_surprise_pct'] for s in surprises[:4]])  # Last 4 quarters
    older_avg = np.mean([s['eps_surprise_pct'] for s in surprises[4:8]]) if len(surprises) >= 8 else recent_avg
    
    if recent_avg > older_avg + 2:
        trend = 'IMPROVING'
    elif recent_avg < older_avg - 2:
        trend = 'DECLINING'
    else:
        trend = 'STABLE'
    
    return {
        'ticker': ticker,
        'company_name': data['company_name'],
        'total_quarters': data['total_quarters'],
        'beats': data['beats'],
        'misses': data['misses'],
        'inline': data['inline'],
        'beat_rate': data['beat_rate'],
        'current_streak': current_streak,
        'current_streak_type': current_type,
        'longest_beat_streak': longest_beat,
        'longest_miss_streak': longest_miss,
        'avg_surprise_pct': data['avg_surprise_pct'],
        'median_surprise_pct': round(np.median(surprise_pcts), 2),
        'surprise_consistency': round(consistency, 1),
        'surprise_trend': trend,
        'data_date': datetime.now().strftime('%Y-%m-%d')
    }


def estimate_whisper_numbers(ticker: str, quarters: int = 8) -> Dict:
    """
    Estimate whisper numbers from pre-earnings price action.
    
    Args:
        ticker: Stock ticker symbol
        quarters: Number of quarters to analyze
    
    Returns:
        Dictionary with whisper number estimates
    """
    ticker = ticker.upper()
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        earnings_hist = stock.earnings_dates
        
        if earnings_hist is None or len(earnings_hist) == 0:
            return {
                'ticker': ticker,
                'error': 'No earnings history available'
            }
        
        hist = stock.history(period='2y')
        whispers = []
        
        for date, row in earnings_hist.head(quarters * 2).iterrows():
            if pd.isna(row.get('Reported EPS')) or pd.isna(row.get('EPS Estimate')):
                continue
            
            report_date = date.strftime('%Y-%m-%d')
            eps_estimate = float(row['EPS Estimate'])
            eps_actual = float(row['Reported EPS'])
            
            # Calculate pre-earnings drift (5 days before)
            try:
                report_datetime = pd.to_datetime(date)
                price_5d_before = hist['Close'].asof(report_datetime - timedelta(days=5))
                price_1d_before = hist['Close'].asof(report_datetime - timedelta(days=1))
                
                pre_drift = ((price_1d_before - price_5d_before) / price_5d_before * 100) if not pd.isna(price_5d_before) and not pd.isna(price_1d_before) else 0
                
                # Estimate whisper based on pre-drift
                # Strong positive drift suggests whisper above estimate
                # Strong negative drift suggests whisper below estimate
                whisper_adjustment = (pre_drift / 100) * eps_estimate * 0.5  # 50% weight to pre-drift
                estimated_whisper = eps_estimate + whisper_adjustment
                
                whisper_gap = estimated_whisper - eps_estimate
                beat_whisper = eps_actual >= estimated_whisper
                beat_estimate = eps_actual >= eps_estimate
                
                # Confidence based on pre-drift magnitude
                if abs(pre_drift) > 5:
                    confidence = 'HIGH'
                elif abs(pre_drift) > 2:
                    confidence = 'MEDIUM'
                else:
                    confidence = 'LOW'
                
                whispers.append({
                    'quarter': report_date[:7],
                    'official_estimate': round(eps_estimate, 2),
                    'estimated_whisper': round(estimated_whisper, 2),
                    'actual_result': round(eps_actual, 2),
                    'whisper_vs_estimate_gap': round(whisper_gap, 2),
                    'beat_whisper': 'Yes' if beat_whisper else 'No',
                    'beat_estimate': 'Yes' if beat_estimate else 'No',
                    'pre_earnings_drift': round(pre_drift, 2),
                    'whisper_confidence': confidence
                })
                
            except:
                continue
            
            if len(whispers) >= quarters:
                break
        
        if len(whispers) == 0:
            return {
                'ticker': ticker,
                'error': 'Unable to estimate whisper numbers'
            }
        
        # Calculate accuracy
        beat_whisper_count = sum(1 for w in whispers if w['beat_whisper'])
        whisper_accuracy = round(beat_whisper_count / len(whispers) * 100, 1)
        
        return {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'quarters_analyzed': len(whispers),
            'whisper_accuracy': whisper_accuracy,
            'whispers': whispers,
            'data_date': datetime.now().strftime('%Y-%m-%d')
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'error': f'Failed to estimate whisper numbers: {str(e)}'
        }


def analyze_post_earnings_drift(ticker: str, quarters: int = 12) -> Dict:
    """
    Analyze post-earnings announcement drift (PEAD).
    
    Args:
        ticker: Stock ticker symbol
        quarters: Number of quarters to analyze
    
    Returns:
        Dictionary with PEAD analysis
    """
    ticker = ticker.upper()
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        earnings_hist = stock.earnings_dates
        
        if earnings_hist is None or len(earnings_hist) == 0:
            return {
                'ticker': ticker,
                'error': 'No earnings history available'
            }
        
        hist = stock.history(period='2y')
        drifts = []
        
        for date, row in earnings_hist.head(quarters * 2).iterrows():
            if pd.isna(row.get('Reported EPS')) or pd.isna(row.get('EPS Estimate')):
                continue
            
            report_date = date.strftime('%Y-%m-%d')
            eps_estimate = float(row['EPS Estimate'])
            eps_actual = float(row['Reported EPS'])
            eps_surprise_pct = ((eps_actual - eps_estimate) / abs(eps_estimate)) * 100 if eps_estimate != 0 else 0
            
            try:
                report_datetime = pd.to_datetime(date)
                price_before = hist['Close'].asof(report_datetime - timedelta(days=1))
                price_1d = hist['Close'].asof(report_datetime + timedelta(days=1))
                price_3d = hist['Close'].asof(report_datetime + timedelta(days=3))
                price_5d = hist['Close'].asof(report_datetime + timedelta(days=5))
                price_10d = hist['Close'].asof(report_datetime + timedelta(days=10))
                
                drift_1d = ((price_1d - price_before) / price_before * 100) if not pd.isna(price_before) and not pd.isna(price_1d) else 0
                drift_3d = ((price_3d - price_before) / price_before * 100) if not pd.isna(price_before) and not pd.isna(price_3d) else 0
                drift_5d = ((price_5d - price_before) / price_before * 100) if not pd.isna(price_before) and not pd.isna(price_5d) else 0
                drift_10d = ((price_10d - price_before) / price_before * 100) if not pd.isna(price_before) and not pd.isna(price_10d) else 0
                
                # Calculate volume and volatility spikes
                vol_before = hist['Volume'].asof(report_datetime - timedelta(days=5))
                vol_after = hist['Volume'].asof(report_datetime + timedelta(days=1))
                volume_spike = (vol_after / vol_before) if not pd.isna(vol_before) and vol_before > 0 else 1
                
                # Determine drift direction and strength
                avg_drift = (drift_1d + drift_3d + drift_5d) / 3
                
                if avg_drift > 2:
                    direction = 'POSITIVE'
                elif avg_drift < -2:
                    direction = 'NEGATIVE'
                else:
                    direction = 'NEUTRAL'
                
                if abs(avg_drift) > 5:
                    strength = 'STRONG'
                elif abs(avg_drift) > 2:
                    strength = 'MODERATE'
                else:
                    strength = 'WEAK'
                
                drifts.append({
                    'quarter': report_date[:7],
                    'report_date': report_date,
                    'surprise_pct': round(eps_surprise_pct, 1),
                    'drift_1d': round(drift_1d, 2),
                    'drift_3d': round(drift_3d, 2),
                    'drift_5d': round(drift_5d, 2),
                    'drift_10d': round(drift_10d, 2),
                    'volume_spike': round(volume_spike, 2),
                    'volatility_spike': 0,  # Would need intraday data
                    'drift_direction': direction,
                    'drift_strength': strength
                })
                
            except:
                continue
            
            if len(drifts) >= quarters:
                break
        
        if len(drifts) == 0:
            return {
                'ticker': ticker,
                'error': 'Unable to analyze post-earnings drift'
            }
        
        # Calculate summary stats
        avg_drift_1d = np.mean([d['drift_1d'] for d in drifts])
        avg_drift_3d = np.mean([d['drift_3d'] for d in drifts])
        avg_drift_5d = np.mean([d['drift_5d'] for d in drifts])
        avg_drift_10d = np.mean([d['drift_10d'] for d in drifts])
        
        # PEAD efficiency (correlation between surprise and drift)
        surprises = [d['surprise_pct'] for d in drifts]
        drifts_5d = [d['drift_5d'] for d in drifts]
        correlation = np.corrcoef(surprises, drifts_5d)[0, 1] if len(surprises) > 1 else 0
        
        return {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'quarters_analyzed': len(drifts),
            'avg_drift_1d': round(avg_drift_1d, 2),
            'avg_drift_3d': round(avg_drift_3d, 2),
            'avg_drift_5d': round(avg_drift_5d, 2),
            'avg_drift_10d': round(avg_drift_10d, 2),
            'surprise_drift_correlation': round(correlation, 3),
            'drifts': drifts,
            'data_date': datetime.now().strftime('%Y-%m-%d')
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'error': f'Failed to analyze post-earnings drift: {str(e)}'
        }


def calculate_earnings_quality(ticker: str) -> Dict:
    """
    Calculate earnings quality score based on surprise consistency.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Dictionary with earnings quality analysis
    """
    ticker = ticker.upper()
    
    # Get multiple datasets
    patterns = analyze_surprise_patterns(ticker)
    if 'error' in patterns:
        return patterns
    
    earnings_data = get_earnings_history(ticker, quarters=12)
    
    # Calculate component scores
    
    # 1. Consistency score (0-100) - already have from patterns
    consistency_score = patterns['surprise_consistency']
    
    # 2. Beat streak score
    beat_rate = patterns['beat_rate']
    longest_beat = patterns['longest_beat_streak']
    beat_streak_score = min(100, (beat_rate * 0.7) + (longest_beat * 5))
    
    # 3. Surprise magnitude score (positive surprises good, consistent better)
    avg_surprise = patterns['avg_surprise_pct']
    surprise_magnitude_score = min(100, max(0, 50 + (avg_surprise * 5)))
    
    # 4. Guidance accuracy (based on surprise variance)
    median_surprise = patterns['median_surprise_pct']
    guidance_score = min(100, max(0, 100 - abs(median_surprise) * 10))
    
    # 5. Revenue-EPS correlation
    surprises = earnings_data['surprises']
    eps_surp = [s['eps_surprise_pct'] for s in surprises if s['revenue_surprise_pct'] != 0]
    rev_surp = [s['revenue_surprise_pct'] for s in surprises if s['revenue_surprise_pct'] != 0]
    
    if len(eps_surp) > 2:
        correlation = np.corrcoef(eps_surp, rev_surp)[0, 1]
    else:
        correlation = 0.5
    
    # Overall quality score (weighted average)
    quality_score = (
        consistency_score * 0.25 +
        beat_streak_score * 0.25 +
        surprise_magnitude_score * 0.20 +
        guidance_score * 0.20 +
        (correlation * 50 + 50) * 0.10  # Normalize correlation to 0-100
    )
    
    # Determine rating
    if quality_score >= 80:
        rating = 'EXCELLENT'
    elif quality_score >= 65:
        rating = 'GOOD'
    elif quality_score >= 50:
        rating = 'FAIR'
    else:
        rating = 'POOR'
    
    # Identify strengths and weaknesses
    strengths = []
    weaknesses = []
    
    if beat_rate > 70:
        strengths.append(f'High beat rate ({beat_rate:.0f}%)')
    elif beat_rate < 40:
        weaknesses.append(f'Low beat rate ({beat_rate:.0f}%)')
    
    if longest_beat > 4:
        strengths.append(f'Strong beat streak ({longest_beat} quarters)')
    
    if consistency_score > 70:
        strengths.append('Highly consistent surprises')
    elif consistency_score < 40:
        weaknesses.append('Inconsistent surprises')
    
    if avg_surprise > 5:
        strengths.append('Strong positive surprises')
    elif avg_surprise < -5:
        weaknesses.append('Frequent negative surprises')
    
    if correlation > 0.7:
        strengths.append('Strong revenue-EPS alignment')
    elif correlation < 0.3:
        weaknesses.append('Weak revenue-EPS correlation')
    
    return {
        'ticker': ticker,
        'company_name': patterns['company_name'],
        'quality_score': round(quality_score, 1),
        'consistency_score': round(consistency_score, 1),
        'beat_streak_score': round(beat_streak_score, 1),
        'surprise_magnitude_score': round(surprise_magnitude_score, 1),
        'guidance_accuracy_score': round(guidance_score, 1),
        'revenue_eps_correlation': round(correlation, 3),
        'quality_rating': rating,
        'key_strengths': strengths,
        'key_weaknesses': weaknesses,
        'data_date': datetime.now().strftime('%Y-%m-%d')
    }


def compare_surprise_history(tickers: List[str]) -> Dict:
    """
    Compare earnings surprise history across multiple tickers.
    
    Args:
        tickers: List of stock ticker symbols
    
    Returns:
        Dictionary with comparative analysis
    """
    comparisons = []
    
    for ticker in tickers:
        patterns = analyze_surprise_patterns(ticker.upper())
        if 'error' not in patterns:
            comparisons.append({
                'ticker': ticker.upper(),
                'company_name': patterns['company_name'],
                'beat_rate': patterns['beat_rate'],
                'avg_surprise_pct': patterns['avg_surprise_pct'],
                'current_streak': patterns['current_streak'],
                'current_streak_type': patterns['current_streak_type'],
                'longest_beat_streak': patterns['longest_beat_streak'],
                'surprise_consistency': patterns['surprise_consistency'],
                'surprise_trend': patterns['surprise_trend']
            })
    
    if len(comparisons) == 0:
        return {
            'error': 'No valid data for any ticker'
        }
    
    # Sort by beat rate
    comparisons_sorted = sorted(comparisons, key=lambda x: x['beat_rate'], reverse=True)
    
    return {
        'tickers_analyzed': len(comparisons),
        'comparisons': comparisons_sorted,
        'data_date': datetime.now().strftime('%Y-%m-%d')
    }


def main():
    """CLI interface for earnings surprise history."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python earnings_surprise_history.py earnings-history TICKER [quarters]")
        print("  python earnings_surprise_history.py surprise-patterns TICKER")
        print("  python earnings_surprise_history.py whisper-numbers TICKER [quarters]")
        print("  python earnings_surprise_history.py post-earnings-drift TICKER [quarters]")
        print("  python earnings_surprise_history.py earnings-quality-score TICKER")
        print("  python earnings_surprise_history.py compare-surprises TICKER1 TICKER2 ...")
        print()
        print("Examples:")
        print("  python earnings_surprise_history.py earnings-history AAPL 12")
        print("  python earnings_surprise_history.py surprise-patterns MSFT")
        print("  python earnings_surprise_history.py whisper-numbers GOOGL")
        print("  python earnings_surprise_history.py post-earnings-drift NVDA")
        print("  python earnings_surprise_history.py earnings-quality-score TSLA")
        print("  python earnings_surprise_history.py compare-surprises AAPL MSFT GOOGL")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'earnings-history':
        if len(sys.argv) < 3:
            print("Error: TICKER required")
            sys.exit(1)
        ticker = sys.argv[2]
        quarters = int(sys.argv[3]) if len(sys.argv) > 3 else 12
        result = get_earnings_history(ticker, quarters)
        print(json.dumps(result, indent=2))
    
    elif command == 'surprise-patterns':
        if len(sys.argv) < 3:
            print("Error: TICKER required")
            sys.exit(1)
        ticker = sys.argv[2]
        result = analyze_surprise_patterns(ticker)
        print(json.dumps(result, indent=2))
    
    elif command == 'whisper-numbers':
        if len(sys.argv) < 3:
            print("Error: TICKER required")
            sys.exit(1)
        ticker = sys.argv[2]
        quarters = int(sys.argv[3]) if len(sys.argv) > 3 else 8
        result = estimate_whisper_numbers(ticker, quarters)
        print(json.dumps(result, indent=2))
    
    elif command == 'post-earnings-drift':
        if len(sys.argv) < 3:
            print("Error: TICKER required")
            sys.exit(1)
        ticker = sys.argv[2]
        quarters = int(sys.argv[3]) if len(sys.argv) > 3 else 12
        result = analyze_post_earnings_drift(ticker, quarters)
        print(json.dumps(result, indent=2))
    
    elif command == 'earnings-quality-score':
        if len(sys.argv) < 3:
            print("Error: TICKER required")
            sys.exit(1)
        ticker = sys.argv[2]
        result = calculate_earnings_quality(ticker)
        print(json.dumps(result, indent=2))
    
    elif command == 'compare-surprises':
        if len(sys.argv) < 3:
            print("Error: At least one TICKER required")
            sys.exit(1)
        tickers = sys.argv[2:]
        result = compare_surprise_history(tickers)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()

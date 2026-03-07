#!/usr/bin/env python3
"""
AAII Sentiment Survey — Individual Investor Sentiment Module

Weekly sentiment survey from American Association of Individual Investors (AAII).
Measures bullish, bearish, and neutral sentiment among individual investors.
Classic contrarian indicator — extreme readings often precede market reversals.

Data Points:
- Bullish % (expect market up over next 6 months)
- Bearish % (expect market down)
- Neutral % (expect no change)
- Bull-Bear Spread (key contrarian signal)
- Historical averages (38.0% bullish, 30.5% bearish, 31.5% neutral since 1987)

Updated: Weekly (Thursday)
History: 35+ years (since 1987)
Source: https://www.aaii.com/sentimentsurvey
Category: Alternative Data — Social & Sentiment
Free tier: True (web scraping, no API key needed)
Author: QuantClaw Data NightBuilder
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# Constants
AAII_URL = "https://www.aaii.com/sentimentsurvey"
HISTORICAL_AVERAGES = {
    'bullish': 38.0,
    'bearish': 30.5,
    'neutral': 31.5
}

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Simple in-memory cache to avoid rate limiting
_CACHE = {}
_CACHE_DURATION = timedelta(hours=1)  # AAII updates weekly, 1hr cache is fine


def get_current_sentiment() -> Dict:
    """
    Get current AAII investor sentiment readings
    
    Scrapes the latest weekly sentiment survey results from AAII.com.
    Returns bullish, bearish, neutral percentages and bull-bear spread.
    
    Note: AAII.com has rate limiting. Results are cached for 1 hour.
    Data updates weekly (Thursday), so frequent requests are unnecessary.
    
    Returns:
        Dict with current sentiment data and contrarian signal interpretation
        
    Example:
        >>> data = get_current_sentiment()
        >>> print(f"Bullish: {data['bullish']}%")
        >>> print(f"Signal: {data['contrarian_signal']}")
    """
    # Check cache first
    if 'sentiment' in _CACHE:
        cached_time = _CACHE.get('timestamp')
        if cached_time and datetime.now() - cached_time < _CACHE_DURATION:
            result = _CACHE['sentiment'].copy()
            result['cached'] = True
            result['cache_age_minutes'] = int((datetime.now() - cached_time).total_seconds() / 60)
            return result
    
    try:
        # Add small delay to be respectful
        time.sleep(1)
        # Use comprehensive headers to avoid 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(AAII_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        # Extract all percentage values
        all_percentages = re.findall(r'(\d+\.?\d*)\s*%', text)
        
        if not all_percentages or len(all_percentages) < 3:
            return {
                "success": False,
                "error": "Could not find sufficient percentage data on page",
                "found_values": len(all_percentages)
            }
        
        # Convert to floats
        percentages = [float(p) for p in all_percentages]
        
        # Look for the pattern around "Sentiment Votes"
        # The data typically appears as: Bullish, Neutral, Bearish in sequence
        sentiment_data = {}
        
        # Find position of keywords to understand data structure
        bullish_idx = text.find('Bullish')
        neutral_idx = text.find('Neutral')
        bearish_idx = text.find('Bearish')
        
        if bullish_idx > 0 and neutral_idx > bullish_idx and bearish_idx > neutral_idx:
            # Keywords are in order - extract first 3 meaningful percentages after "Sentiment Votes"
            sentiment_votes_idx = text.find('Sentiment Votes')
            
            if sentiment_votes_idx > 0:
                # Extract substring after "Sentiment Votes"
                relevant_text = text[sentiment_votes_idx:sentiment_votes_idx+500]
                relevant_pcts = re.findall(r'(\d+\.?\d*)\s*%', relevant_text)
                
                if len(relevant_pcts) >= 3:
                    # First 3 percentages after Sentiment Votes are typically: Bullish, Neutral, Bearish
                    sentiment_data['bullish'] = float(relevant_pcts[0])
                    sentiment_data['neutral'] = float(relevant_pcts[1])
                    sentiment_data['bearish'] = float(relevant_pcts[2])
        
        # Fallback: use first 3 percentages that aren't the historical averages
        if not sentiment_data or len(sentiment_data) < 3:
            # Filter out historical averages (38.0, 30.5, 31.5)
            filtered = [p for p in percentages if not any(abs(p - avg) < 0.5 for avg in HISTORICAL_AVERAGES.values())]
            
            if len(filtered) >= 3:
                sentiment_data = {
                    'bullish': filtered[0],
                    'neutral': filtered[1],
                    'bearish': filtered[2]
                }
        
        if not sentiment_data or len(sentiment_data) < 3:
            return {
                "success": False,
                "error": "Could not extract complete sentiment data from page",
                "partial_data": sentiment_data,
                "all_percentages": percentages[:10]
            }
        
        # Calculate bull-bear spread
        bull_bear_spread = sentiment_data['bullish'] - sentiment_data['bearish']
        
        # Generate contrarian signal
        contrarian_signal = _interpret_sentiment(
            sentiment_data['bullish'],
            sentiment_data['bearish'],
            bull_bear_spread
        )
        
        # Calculate deviations from historical averages
        deviations = {
            'bullish_deviation': sentiment_data['bullish'] - HISTORICAL_AVERAGES['bullish'],
            'bearish_deviation': sentiment_data['bearish'] - HISTORICAL_AVERAGES['bearish'],
            'neutral_deviation': sentiment_data['neutral'] - HISTORICAL_AVERAGES['neutral']
        }
        
        result = {
            "success": True,
            "bullish": sentiment_data['bullish'],
            "bearish": sentiment_data['bearish'],
            "neutral": sentiment_data['neutral'],
            "bull_bear_spread": round(bull_bear_spread, 1),
            "historical_averages": HISTORICAL_AVERAGES,
            "deviations": deviations,
            "contrarian_signal": contrarian_signal,
            "timestamp": datetime.now().isoformat(),
            "source": "AAII Sentiment Survey",
            "url": AAII_URL,
            "cached": False
        }
        
        # Cache the result
        _CACHE['sentiment'] = result.copy()
        _CACHE['timestamp'] = datetime.now()
        
        return result
        
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def _interpret_sentiment(bullish: float, bearish: float, spread: float) -> Dict:
    """
    Interpret sentiment as a contrarian indicator
    
    Args:
        bullish: Current bullish percentage
        bearish: Current bearish percentage
        spread: Bull-bear spread
        
    Returns:
        Dict with signal strength and interpretation
    """
    signal = "NEUTRAL"
    strength = "Moderate"
    interpretation = "Sentiment within normal ranges"
    
    # Extreme bullish = contrarian bearish signal (market may be topping)
    if bullish > 50:
        signal = "BEARISH"
        strength = "Strong"
        interpretation = "Extreme bullish sentiment - potential market top ahead"
    elif bullish > 45:
        signal = "BEARISH"
        strength = "Moderate"
        interpretation = "Elevated bullish sentiment - caution warranted"
    
    # Extreme bearish = contrarian bullish signal (market may be bottoming)
    elif bearish > 50:
        signal = "BULLISH"
        strength = "Strong"
        interpretation = "Extreme bearish sentiment - potential market bottom"
    elif bearish > 45:
        signal = "BULLISH"
        strength = "Moderate"
        interpretation = "Elevated bearish sentiment - buying opportunity may be forming"
    
    # Bull-bear spread analysis
    elif spread > 30:
        signal = "BEARISH"
        strength = "Strong"
        interpretation = "Very high bull-bear spread - excessive optimism"
    elif spread > 20:
        signal = "BEARISH"
        strength = "Moderate"
        interpretation = "Elevated bull-bear spread - optimism high"
    elif spread < -30:
        signal = "BULLISH"
        strength = "Strong"
        interpretation = "Very negative bull-bear spread - extreme pessimism"
    elif spread < -20:
        signal = "BULLISH"
        strength = "Moderate"
        interpretation = "Negative bull-bear spread - pessimism elevated"
    
    return {
        "signal": signal,
        "strength": strength,
        "interpretation": interpretation,
        "note": "Contrarian indicator - signals suggest opposite market direction"
    }


def get_sentiment_summary() -> Dict:
    """
    Get comprehensive sentiment summary with analysis
    
    Returns current sentiment, historical context, contrarian signals,
    and interpretation for investors.
    
    Returns:
        Dict with full sentiment analysis and actionable insights
    """
    sentiment = get_current_sentiment()
    
    if not sentiment.get('success'):
        return sentiment
    
    # Build comprehensive summary
    summary = {
        "success": True,
        "current_sentiment": {
            "bullish": sentiment['bullish'],
            "bearish": sentiment['bearish'],
            "neutral": sentiment['neutral'],
            "bull_bear_spread": sentiment['bull_bear_spread']
        },
        "historical_context": {
            "averages": sentiment['historical_averages'],
            "deviations": sentiment['deviations'],
            "interpretation": _contextualize_deviations(sentiment['deviations'])
        },
        "contrarian_analysis": sentiment['contrarian_signal'],
        "key_insights": _generate_insights(sentiment),
        "timestamp": sentiment['timestamp'],
        "source": sentiment['source']
    }
    
    return summary


def _contextualize_deviations(deviations: Dict) -> str:
    """Generate human-readable interpretation of deviations from historical averages"""
    bull_dev = deviations['bullish_deviation']
    bear_dev = deviations['bearish_deviation']
    
    if abs(bull_dev) < 5 and abs(bear_dev) < 5:
        return "Sentiment near historical averages - normal market conditions"
    elif bull_dev > 10:
        return f"Bullish sentiment {bull_dev:+.1f}pp above average - excessive optimism"
    elif bear_dev > 10:
        return f"Bearish sentiment {bear_dev:+.1f}pp above average - excessive pessimism"
    elif bull_dev < -10:
        return f"Bullish sentiment {bull_dev:+.1f}pp below average - unusual lack of optimism"
    else:
        return f"Sentiment moderately deviated from averages (Bull: {bull_dev:+.1f}pp, Bear: {bear_dev:+.1f}pp)"


def _generate_insights(sentiment: Dict) -> List[str]:
    """Generate list of key insights for investors"""
    insights = []
    
    bullish = sentiment['bullish']
    bearish = sentiment['bearish']
    spread = sentiment['bull_bear_spread']
    signal = sentiment['contrarian_signal']
    
    # Add signal strength insight
    insights.append(f"{signal['strength']} {signal['signal']} contrarian signal")
    
    # Add specific observations
    if bullish > 50 or bearish > 50:
        insights.append("Extreme sentiment reading - historically significant")
    
    if abs(spread) > 25:
        insights.append(f"Bull-bear spread at {spread:.1f}pp - sentiment highly skewed")
    
    # Add historical context
    bull_dev = sentiment['deviations']['bullish_deviation']
    bear_dev = sentiment['deviations']['bearish_deviation']
    
    if abs(bull_dev) > 10 or abs(bear_dev) > 10:
        insights.append("Significant deviation from 35-year historical averages")
    
    # Add interpretation
    insights.append(signal['interpretation'])
    
    return insights


def get_sentiment_history(weeks: int = 52) -> Dict:
    """
    Get historical sentiment data (placeholder for future implementation)
    
    Args:
        weeks: Number of weeks of history to retrieve (default 52)
        
    Returns:
        Dict indicating feature not yet implemented
        
    Note:
        Historical data download feature to be implemented.
        AAII may provide CSV/Excel downloads of historical data.
    """
    return {
        "success": False,
        "error": "Historical data retrieval not yet implemented",
        "note": "Visit https://www.aaii.com/sentimentsurvey for historical charts",
        "requested_weeks": weeks
    }


def check_extreme_sentiment() -> Dict:
    """
    Check if current sentiment shows extreme readings
    
    Returns:
        Dict with extreme reading flags and warnings
    """
    sentiment = get_current_sentiment()
    
    if not sentiment.get('success'):
        return sentiment
    
    extremes = {
        "success": True,
        "is_extreme": False,
        "extreme_type": None,
        "warnings": []
    }
    
    bullish = sentiment['bullish']
    bearish = sentiment['bearish']
    spread = sentiment['bull_bear_spread']
    
    # Check for extreme bullish
    if bullish > 50:
        extremes['is_extreme'] = True
        extremes['extreme_type'] = 'EXTREME_BULLISH'
        extremes['warnings'].append(
            f"Bullish sentiment at {bullish:.1f}% - historically associated with market tops"
        )
    
    # Check for extreme bearish
    if bearish > 50:
        extremes['is_extreme'] = True
        extremes['extreme_type'] = 'EXTREME_BEARISH'
        extremes['warnings'].append(
            f"Bearish sentiment at {bearish:.1f}% - historically associated with market bottoms"
        )
    
    # Check spread extremes
    if spread > 30:
        extremes['is_extreme'] = True
        extremes['warnings'].append(
            f"Bull-bear spread at {spread:.1f}pp - excessive optimism warning"
        )
    elif spread < -30:
        extremes['is_extreme'] = True
        extremes['warnings'].append(
            f"Bull-bear spread at {spread:.1f}pp - extreme pessimism warning"
        )
    
    if not extremes['is_extreme']:
        extremes['warnings'].append("No extreme sentiment readings detected")
    
    extremes['current_readings'] = {
        'bullish': bullish,
        'bearish': bearish,
        'spread': spread
    }
    
    return extremes


# Aliases for convenience
get_sentiment = get_current_sentiment
check_extremes = check_extreme_sentiment


if __name__ == "__main__":
    import json
    
    print("=" * 70)
    print("AAII Investor Sentiment Survey - Alternative Data Module")
    print("=" * 70)
    
    # Get current sentiment
    print("\n1. Current Sentiment:")
    sentiment = get_current_sentiment()
    print(json.dumps(sentiment, indent=2))
    
    # Get full summary
    print("\n2. Comprehensive Summary:")
    summary = get_sentiment_summary()
    print(json.dumps(summary, indent=2))
    
    # Check for extremes
    print("\n3. Extreme Sentiment Check:")
    extremes = check_extreme_sentiment()
    print(json.dumps(extremes, indent=2))

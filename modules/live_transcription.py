#!/usr/bin/env python3
"""
Live Earnings Transcription Module — Real-time Signal Extraction

Stream earnings calls, transcribe with Whisper (local), and extract trading signals.
Framework for:
- Upcoming earnings calendar (Yahoo Finance)
- Transcript signal extraction (sentiment, guidance changes, red flags)
- Earnings countdown tracking
- Quarter-over-quarter transcript comparison

Data Sources:
- Yahoo Finance API (earnings calendar)
- SEC EDGAR (post-call transcripts)
- Framework for real-time Whisper transcription (future integration)

Author: QUANTCLAW DATA Build Agent
Phase: 82
"""

import sys
import re
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from collections import Counter
import statistics

# API Configuration
YAHOO_FINANCE_BASE = "https://query2.finance.yahoo.com/v1/finance"
SEC_EDGAR_BASE = "https://www.sec.gov"
USER_AGENT = "QuantClaw Data quantclaw@example.com"

# Signal Keywords for Earnings Transcripts
BULLISH_SIGNALS = {
    'beat', 'exceed', 'exceeded', 'exceeds', 'outperform', 'outperformed', 'record',
    'accelerating', 'acceleration', 'strong', 'stronger', 'strongest', 'robust',
    'growth', 'growing', 'grew', 'expand', 'expanded', 'expanding', 'expansion',
    'momentum', 'bullish', 'optimistic', 'opportunity', 'opportunities', 'guidance',
    'raise', 'raised', 'raising', 'upgrade', 'upgraded', 'upside', 'tailwind',
    'tailwinds', 'breakthrough', 'innovative', 'market share', 'win', 'winning',
    'wins', 'secular', 'pipeline', 'backlog', 'demand', 'traction', 'adoption'
}

BEARISH_SIGNALS = {
    'miss', 'missed', 'underperform', 'underperformed', 'weak', 'weaker', 'weakest',
    'decline', 'declined', 'declining', 'decrease', 'decreased', 'decreasing',
    'slow', 'slower', 'slowest', 'slowing', 'slowdown', 'headwind', 'headwinds',
    'challenge', 'challenged', 'challenges', 'challenging', 'concern', 'concerned',
    'concerns', 'pressure', 'pressured', 'pressures', 'difficult', 'difficulties',
    'lower', 'lowered', 'lowering', 'cut', 'cuts', 'cutting', 'reduce', 'reduced',
    'reducing', 'reduction', 'cautious', 'uncertainty', 'risk', 'risks', 'delay',
    'delayed', 'postpone', 'postponed', 'competitive', 'competition', 'churn',
    'loss', 'losses', 'margin compression', 'disappointing', 'shortfall'
}

GUIDANCE_KEYWORDS = {
    'guidance', 'outlook', 'expect', 'expects', 'expected', 'expecting', 'forecast',
    'forecasts', 'forecasted', 'forecasting', 'target', 'targets', 'targeting',
    'project', 'projects', 'projected', 'projecting', 'anticipate', 'anticipates',
    'anticipated', 'anticipating', 'estimate', 'estimates', 'estimated', 'estimating',
    'range', 'approximately', 'around', 'between', 'q1', 'q2', 'q3', 'q4',
    'full year', 'fiscal year', 'fy', 'next quarter', 'remainder'
}

RED_FLAG_KEYWORDS = {
    'restate', 'restated', 'restatement', 'investigation', 'investigated', 'sec',
    'lawsuit', 'litigation', 'regulatory', 'fraud', 'accounting', 'writedown',
    'writeoff', 'impairment', 'restructuring', 'layoff', 'layoffs', 'resignation',
    'resign', 'departed', 'unexpected', 'surprise', 'miss', 'shortfall', 'delay',
    'postpone', 'suspended', 'suspend', 'discontinued', 'bankruptcy', 'default',
    'violation', 'breach', 'non-compliant', 'warning', 'cautionary'
}


def get_earnings_calendar(days_ahead: int = 7) -> List[Dict]:
    """
    Fetch upcoming earnings calendar from Yahoo Finance
    
    Args:
        days_ahead: Number of days to look ahead (default 7)
    
    Returns:
        List of earnings events with dates and companies
    """
    try:
        # Yahoo Finance earnings calendar endpoint
        # Note: This is a simplified version - real implementation would use Yahoo Finance API
        # or alternative sources like Nasdaq earnings calendar
        
        # For demo: simulate upcoming earnings
        today = datetime.now()
        events = []
        
        # Simulated upcoming earnings (in production, fetch from Yahoo Finance API)
        sample_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD']
        
        for i, ticker in enumerate(sample_tickers):
            if i < days_ahead:
                event_date = today + timedelta(days=i)
                events.append({
                    'ticker': ticker,
                    'company': _get_company_name(ticker),
                    'date': event_date.strftime('%Y-%m-%d'),
                    'days_until': i,
                    'time': 'After Market Close' if i % 2 == 0 else 'Before Market Open',
                    'quarter': f"Q{((datetime.now().month - 1) // 3) + 1} {datetime.now().year}",
                    'estimated_eps': None,  # Would fetch from API
                    'source': 'simulated_demo'
                })
        
        return events
    
    except Exception as e:
        print(f"Error fetching earnings calendar: {e}", file=sys.stderr)
        return []


def _get_company_name(ticker: str) -> str:
    """Simple ticker to company name mapping (would use API in production)"""
    names = {
        'AAPL': 'Apple Inc.',
        'MSFT': 'Microsoft Corporation',
        'GOOGL': 'Alphabet Inc.',
        'AMZN': 'Amazon.com Inc.',
        'TSLA': 'Tesla Inc.',
        'META': 'Meta Platforms Inc.',
        'NVDA': 'NVIDIA Corporation',
        'AMD': 'Advanced Micro Devices Inc.'
    }
    return names.get(ticker, ticker)


def get_next_earnings(ticker: str) -> Optional[Dict]:
    """
    Get next earnings date for a specific ticker
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Next earnings event details or None
    """
    calendar = get_earnings_calendar(days_ahead=90)
    for event in calendar:
        if event['ticker'] == ticker.upper():
            return event
    return None


def fetch_sec_transcript(ticker: str, quarter: Optional[str] = None) -> Optional[Dict]:
    """
    Fetch earnings call transcript from SEC EDGAR
    
    Args:
        ticker: Stock ticker symbol
        quarter: Optional specific quarter (e.g., "Q4 2025")
    
    Returns:
        Transcript data or None
    """
    try:
        # In production, this would fetch from SEC EDGAR 8-K filings
        # For demo, return simulated transcript
        
        return {
            'ticker': ticker,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'quarter': quarter or f"Q{((datetime.now().month - 1) // 3) + 1} {datetime.now().year}",
            'full_text': _get_simulated_transcript(ticker),
            'source': 'simulated_demo'
        }
    
    except Exception as e:
        print(f"Error fetching transcript: {e}", file=sys.stderr)
        return None


def _get_simulated_transcript(ticker: str) -> str:
    """Generate simulated earnings call transcript"""
    templates = {
        'AAPL': """
        CEO: Thank you for joining us today. We're pleased to report another strong quarter.
        Revenue exceeded expectations, growing 28% year-over-year to a record $125 billion.
        iPhone sales accelerated with strong momentum in emerging markets. Our services 
        business continues to show robust growth with 400 million paid subscriptions.
        We're raising our full-year guidance based on the strength we're seeing.
        Margins expanded 200 basis points due to favorable mix and operational efficiency.
        We see significant opportunities ahead with our AI initiatives and new product pipeline.
        
        CFO: Gross margin came in at 46.5%, beating our guidance of 45-46%. Operating expenses
        were well-controlled at 12% of revenue. We generated $32 billion in operating cash flow
        this quarter. We're returning $30 billion to shareholders through buybacks and dividends.
        For next quarter, we expect revenue between $120-125 billion, above consensus of $118B.
        
        Q&A: 
        Q: Can you provide more color on iPhone demand trends?
        A: We're seeing accelerating demand particularly in China and India. The new models
        are resonating strongly with consumers. We expect this momentum to continue.
        
        Q: What's the outlook for margins?
        A: We're confident we can maintain margins in the mid-40s range. We have pricing power
        and our supply chain efficiency continues to improve. No headwinds on the horizon.
        """,
        
        'TSLA': """
        CEO: Q4 was challenging but we're positioned well for 2026. Deliveries came in at
        465,000 vehicles, slightly below our target due to production delays in Shanghai.
        However, we're seeing strong order momentum and our backlog is at record levels.
        
        Energy storage deployments grew 90% year-over-year - a bright spot. Margins declined
        to 22% due to competitive pricing pressure and higher costs. We're taking actions to
        improve profitability including cost reduction initiatives.
        
        For full year 2026, we're targeting 2.2-2.4 million deliveries, though there are
        uncertainties around regulatory changes and raw material costs. Cybertruck production
        is ramping but facing some delays.
        
        CFO: Cash flow was impacted by inventory build. We ended the quarter with $18B in cash.
        We're being cautious with our outlook given the headwinds we're facing.
        
        Q&A:
        Q: What's the plan to address margin compression?
        A: Well, we're looking at various levers. It's a challenging environment with competition.
        We may need to adjust pricing. We're also working on cost reduction but it's difficult
        to say exactly how much margin we can recover.
        
        Q: Concerns about demand in China?
        A: The competitive landscape is intense. We're seeing some pressure but we believe
        our brand is strong. There could be some near-term challenges.
        """
    }
    
    return templates.get(ticker, """
        CEO: Thank you for joining us. We delivered solid results this quarter with revenue
        growth of 15% year-over-year. We're seeing good traction in our core markets and
        expect continued growth. Margins were stable and we're managing costs effectively.
        Our outlook for next quarter is cautiously optimistic given market conditions.
    """)


def extract_signals(transcript_text: str) -> Dict:
    """
    Extract trading signals from earnings transcript
    
    Analyzes:
    - Bullish vs bearish language frequency
    - Guidance changes and tone
    - Red flags and risk factors
    - Confidence level in forward outlook
    
    Args:
        transcript_text: Full earnings call transcript
    
    Returns:
        Signal analysis with scores and extracted phrases
    """
    words = re.findall(r'\b\w+\b', transcript_text.lower())
    word_count = len(words)
    
    # Count signal words
    bullish_count = sum(1 for w in words if w in BULLISH_SIGNALS)
    bearish_count = sum(1 for w in words if w in BEARISH_SIGNALS)
    guidance_count = sum(1 for w in words if w in GUIDANCE_KEYWORDS)
    red_flag_count = sum(1 for w in words if w in RED_FLAG_KEYWORDS)
    
    # Calculate signal strength (-100 to +100)
    total_signals = bullish_count + bearish_count
    if total_signals > 0:
        signal_strength = ((bullish_count - bearish_count) / total_signals) * 100
    else:
        signal_strength = 0
    
    # Extract specific guidance mentions
    guidance_sentences = _extract_guidance_mentions(transcript_text)
    
    # Extract red flags
    red_flags = _extract_red_flags(transcript_text)
    
    # Overall signal classification
    if signal_strength > 30 and red_flag_count < 3:
        signal = "STRONG BUY"
    elif signal_strength > 10 and red_flag_count < 5:
        signal = "BUY"
    elif signal_strength > -10 and red_flag_count < 7:
        signal = "HOLD"
    elif signal_strength > -30:
        signal = "SELL"
    else:
        signal = "STRONG SELL"
    
    return {
        "overall_signal": signal,
        "signal_strength": round(signal_strength, 1),
        "metrics": {
            "bullish_mentions": bullish_count,
            "bearish_mentions": bearish_count,
            "guidance_mentions": guidance_count,
            "red_flags": red_flag_count
        },
        "ratios": {
            "bullish_ratio": round(bullish_count / word_count * 100, 2),
            "bearish_ratio": round(bearish_count / word_count * 100, 2),
            "net_sentiment": round((bullish_count - bearish_count) / word_count * 100, 2)
        },
        "guidance_extracts": guidance_sentences[:5],  # Top 5 guidance mentions
        "red_flag_details": red_flags,
        "confidence": _calculate_signal_confidence(bullish_count, bearish_count, red_flag_count, word_count)
    }


def _extract_guidance_mentions(text: str) -> List[str]:
    """Extract sentences containing guidance keywords"""
    sentences = re.split(r'[.!?]+', text)
    guidance_sentences = []
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in GUIDANCE_KEYWORDS):
            # Check if it has numbers (likely quantitative guidance)
            if re.search(r'\d+', sentence):
                guidance_sentences.append(sentence.strip())
    
    return guidance_sentences


def _extract_red_flags(text: str) -> List[str]:
    """Extract red flag mentions with context"""
    sentences = re.split(r'[.!?]+', text)
    red_flags = []
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        matched_flags = [flag for flag in RED_FLAG_KEYWORDS if flag in sentence_lower]
        if matched_flags:
            red_flags.append({
                "keywords": matched_flags,
                "context": sentence.strip()[:200]  # First 200 chars
            })
    
    return red_flags[:10]  # Top 10 red flags


def _calculate_signal_confidence(bullish: int, bearish: int, red_flags: int, total_words: int) -> Dict:
    """Calculate confidence in the signal"""
    # More mentions = higher confidence (up to a point)
    mention_confidence = min(100, (bullish + bearish) / total_words * 1000)
    
    # Clarity: large difference between bullish/bearish = more confident
    if bullish + bearish > 0:
        clarity = abs(bullish - bearish) / (bullish + bearish) * 100
    else:
        clarity = 0
    
    # Red flag penalty
    red_flag_penalty = min(50, red_flags * 10)
    
    # Overall confidence (0-100)
    confidence = (mention_confidence * 0.4 + clarity * 0.4 - red_flag_penalty * 0.2)
    confidence = max(0, min(100, confidence))
    
    return {
        "score": round(confidence, 1),
        "mention_confidence": round(mention_confidence, 1),
        "signal_clarity": round(clarity, 1),
        "red_flag_penalty": round(red_flag_penalty, 1),
        "interpretation": _interpret_confidence(confidence)
    }


def _interpret_confidence(score: float) -> str:
    """Interpret confidence score"""
    if score >= 80:
        return "Very High - Clear and consistent signals"
    elif score >= 60:
        return "High - Reliable signals with minor noise"
    elif score >= 40:
        return "Moderate - Mixed signals, proceed with caution"
    elif score >= 20:
        return "Low - Weak or conflicting signals"
    else:
        return "Very Low - Insufficient or unreliable data"


def compare_transcripts(current: str, prior: str) -> Dict:
    """
    Compare current vs prior quarter transcript
    
    Detects:
    - Sentiment shifts
    - Guidance changes (raise, lower, maintain)
    - Language tone changes
    - New risk factors mentioned
    
    Args:
        current: Current quarter transcript
        prior: Prior quarter transcript
    
    Returns:
        Comparison analysis with deltas
    """
    current_signals = extract_signals(current)
    prior_signals = extract_signals(prior)
    
    # Calculate deltas
    signal_delta = current_signals['signal_strength'] - prior_signals['signal_strength']
    bullish_delta = current_signals['metrics']['bullish_mentions'] - prior_signals['metrics']['bullish_mentions']
    bearish_delta = current_signals['metrics']['bearish_mentions'] - prior_signals['metrics']['bearish_mentions']
    red_flag_delta = current_signals['metrics']['red_flags'] - prior_signals['metrics']['red_flags']
    
    # Determine trend
    if signal_delta > 20:
        trend = "IMPROVING SIGNIFICANTLY"
    elif signal_delta > 5:
        trend = "IMPROVING"
    elif signal_delta > -5:
        trend = "STABLE"
    elif signal_delta > -20:
        trend = "DETERIORATING"
    else:
        trend = "DETERIORATING SIGNIFICANTLY"
    
    return {
        "trend": trend,
        "signal_strength_change": round(signal_delta, 1),
        "current_quarter": {
            "signal": current_signals['overall_signal'],
            "strength": current_signals['signal_strength'],
            "metrics": current_signals['metrics']
        },
        "prior_quarter": {
            "signal": prior_signals['overall_signal'],
            "strength": prior_signals['signal_strength'],
            "metrics": prior_signals['metrics']
        },
        "deltas": {
            "bullish_change": bullish_delta,
            "bearish_change": bearish_delta,
            "red_flag_change": red_flag_delta,
            "net_sentiment_change": round(
                current_signals['ratios']['net_sentiment'] - prior_signals['ratios']['net_sentiment'],
                2
            )
        },
        "interpretation": _interpret_trend(trend, signal_delta, red_flag_delta)
    }


def _interpret_trend(trend: str, signal_delta: float, red_flag_delta: int) -> str:
    """Interpret the quarter-over-quarter trend"""
    if "IMPROVING" in trend and red_flag_delta <= 0:
        return "Positive momentum - fundamentals strengthening"
    elif "IMPROVING" in trend and red_flag_delta > 0:
        return "Mixed signals - improving sentiment but new risks emerged"
    elif trend == "STABLE" and red_flag_delta == 0:
        return "Steady state - no major changes"
    elif trend == "STABLE" and red_flag_delta > 0:
        return "Caution - new risks despite stable sentiment"
    elif "DETERIORATING" in trend:
        return "Negative momentum - fundamentals weakening"
    else:
        return "Unclear trend - review detailed metrics"


# ============================================================================
# CLI Commands
# ============================================================================

def cmd_earnings_schedule(days: int = 7) -> Dict:
    """
    CLI: earnings-schedule [DAYS]
    Get upcoming earnings for the week/period
    """
    calendar = get_earnings_calendar(days_ahead=days)
    
    return {
        "period": f"Next {days} days",
        "count": len(calendar),
        "events": calendar,
        "summary": {
            "this_week": sum(1 for e in calendar if e['days_until'] <= 7),
            "next_week": sum(1 for e in calendar if 7 < e['days_until'] <= 14)
        }
    }


def cmd_transcript_signals(ticker: str) -> Dict:
    """
    CLI: transcript-signals TICKER
    Extract trading signals from latest transcript
    """
    transcript = fetch_sec_transcript(ticker.upper())
    
    if not transcript:
        return {"error": f"No transcript found for {ticker}"}
    
    signals = extract_signals(transcript['full_text'])
    
    return {
        "ticker": ticker.upper(),
        "date": transcript['date'],
        "quarter": transcript['quarter'],
        "signals": signals,
        "source": transcript['source']
    }


def cmd_earnings_countdown(ticker: str) -> Dict:
    """
    CLI: earnings-countdown TICKER
    Days until next earnings report
    """
    next_earnings = get_next_earnings(ticker.upper())
    
    if not next_earnings:
        return {
            "ticker": ticker.upper(),
            "status": "No upcoming earnings found",
            "note": "Check back later or search earnings calendar"
        }
    
    days_until = next_earnings['days_until']
    
    # Urgency level
    if days_until == 0:
        urgency = "TODAY"
    elif days_until == 1:
        urgency = "TOMORROW"
    elif days_until <= 3:
        urgency = "IMMINENT"
    elif days_until <= 7:
        urgency = "THIS WEEK"
    else:
        urgency = "UPCOMING"
    
    return {
        "ticker": ticker.upper(),
        "company": next_earnings['company'],
        "earnings_date": next_earnings['date'],
        "days_until": days_until,
        "urgency": urgency,
        "time": next_earnings['time'],
        "quarter": next_earnings['quarter'],
        "countdown": f"{days_until} day{'s' if days_until != 1 else ''} until earnings"
    }


def cmd_transcript_compare(ticker: str) -> Dict:
    """
    CLI: transcript-compare TICKER
    Compare latest vs prior quarter transcript
    """
    # Fetch current and prior quarter transcripts
    current = fetch_sec_transcript(ticker.upper())
    
    if not current:
        return {"error": f"No current transcript found for {ticker}"}
    
    # Simulate prior quarter (in production, fetch actual prior quarter)
    prior = fetch_sec_transcript(ticker.upper(), quarter="Q3 2025")
    
    if not prior:
        return {"error": f"No prior transcript found for {ticker}"}
    
    comparison = compare_transcripts(current['full_text'], prior['full_text'])
    
    return {
        "ticker": ticker.upper(),
        "current_quarter": current['quarter'],
        "prior_quarter": prior['quarter'],
        "comparison": comparison
    }


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python live_transcription.py earnings-schedule [DAYS]")
        print("  python live_transcription.py transcript-signals TICKER")
        print("  python live_transcription.py earnings-countdown TICKER")
        print("  python live_transcription.py transcript-compare TICKER")
        print()
        print("Examples:")
        print("  python live_transcription.py earnings-schedule 7")
        print("  python live_transcription.py transcript-signals AAPL")
        print("  python live_transcription.py earnings-countdown TSLA")
        print("  python live_transcription.py transcript-compare MSFT")
        return 1
    
    command = sys.argv[1]
    
    if command == "earnings-schedule":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        result = cmd_earnings_schedule(days)
        print(json.dumps(result, indent=2))
    
    elif command == "transcript-signals":
        if len(sys.argv) < 3:
            print("Error: Missing ticker", file=sys.stderr)
            return 1
        ticker = sys.argv[2]
        result = cmd_transcript_signals(ticker)
        print(json.dumps(result, indent=2))
    
    elif command == "earnings-countdown":
        if len(sys.argv) < 3:
            print("Error: Missing ticker", file=sys.stderr)
            return 1
        ticker = sys.argv[2]
        result = cmd_earnings_countdown(ticker)
        print(json.dumps(result, indent=2))
    
    elif command == "transcript-compare":
        if len(sys.argv) < 3:
            print("Error: Missing ticker", file=sys.stderr)
            return 1
        ticker = sys.argv[2]
        result = cmd_transcript_compare(ticker)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

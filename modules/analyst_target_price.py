#!/usr/bin/env python3
"""
Analyst Target Price Tracker Module — Consensus Targets, Bull/Bear Cases, Revision Velocity

Tracks analyst price targets and recommendations:
- Consensus price targets (mean, median)
- Bull case (high target) and Bear case (low target)
- Target vs current price upside/downside
- Recommendation distribution (buy/hold/sell)
- Revision velocity (upgrades/downgrades in recent periods)
- Target price changes over time
- Analyst coverage trends

Data Sources: Yahoo Finance (analyst_price_targets, recommendations, upgrades_downgrades)

Author: QUANTCLAW DATA Build Agent
Phase: 145
"""

import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def safe_get_value(value, default=0) -> float:
    """Safely extract numeric value"""
    try:
        if value is None:
            return default
        return float(value)
    except:
        return default

def get_consensus_targets(ticker: str) -> Dict:
    """
    Get current analyst consensus price targets
    
    Returns:
    - Consensus mean and median targets
    - Bull case (high) and bear case (low)
    - Current price
    - Upside/downside potential
    - Number of analysts covering
    """
    ticker = ticker.upper()
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get price targets
        targets = stock.analyst_price_targets
        current_price = safe_get_value(targets.get('current', info.get('currentPrice', 0)))
        
        target_mean = safe_get_value(targets.get('mean', info.get('targetMeanPrice', 0)))
        target_median = safe_get_value(targets.get('median', info.get('targetMedianPrice', 0)))
        target_high = safe_get_value(targets.get('high', info.get('targetHighPrice', 0)))
        target_low = safe_get_value(targets.get('low', info.get('targetLowPrice', 0)))
        
        num_analysts = info.get('numberOfAnalystOpinions', 0)
        
        # Calculate upside/downside
        if current_price > 0:
            mean_upside = ((target_mean - current_price) / current_price) * 100
            median_upside = ((target_median - current_price) / current_price) * 100
            bull_upside = ((target_high - current_price) / current_price) * 100
            bear_downside = ((target_low - current_price) / current_price) * 100
        else:
            mean_upside = median_upside = bull_upside = bear_downside = 0
        
        # Determine assessment
        if mean_upside > 30:
            assessment = "Strong Buy - Significant upside"
            color = "green"
        elif mean_upside > 15:
            assessment = "Buy - Moderate upside"
            color = "green"
        elif mean_upside > 5:
            assessment = "Hold - Slight upside"
            color = "yellow"
        elif mean_upside > -5:
            assessment = "Hold - Fairly valued"
            color = "yellow"
        elif mean_upside > -15:
            assessment = "Sell - Slight downside"
            color = "red"
        else:
            assessment = "Strong Sell - Significant downside"
            color = "red"
        
        return {
            "ticker": ticker,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_price": round(current_price, 2),
            "consensus": {
                "mean_target": round(target_mean, 2),
                "median_target": round(target_median, 2),
                "mean_upside_pct": round(mean_upside, 2),
                "median_upside_pct": round(median_upside, 2)
            },
            "bull_case": {
                "high_target": round(target_high, 2),
                "upside_pct": round(bull_upside, 2)
            },
            "bear_case": {
                "low_target": round(target_low, 2),
                "downside_pct": round(bear_downside, 2)
            },
            "coverage": {
                "num_analysts": num_analysts
            },
            "assessment": {
                "rating": assessment,
                "color": color
            },
            "interpretation": {
                "mean_upside": f"Consensus target implies {mean_upside:.1f}% {'upside' if mean_upside > 0 else 'downside'}",
                "bull_case": f"Most optimistic analyst sees {bull_upside:.1f}% upside",
                "bear_case": f"Most pessimistic analyst sees {bear_downside:.1f}% {'downside' if bear_downside < 0 else 'upside'}"
            }
        }
        
    except Exception as e:
        return {
            "error": f"Failed to get consensus targets for {ticker}: {str(e)}",
            "ticker": ticker
        }

def get_recommendation_distribution(ticker: str) -> Dict:
    """
    Get analyst recommendation distribution
    
    Returns:
    - Current recommendations (strong buy, buy, hold, sell, strong sell)
    - Historical recommendation trends (past 4 months)
    - Recommendation mean score
    - Recommendation changes over time
    """
    ticker = ticker.upper()
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        recs = stock.recommendations
        
        if recs is None or recs.empty:
            return {
                "error": f"No recommendation data available for {ticker}",
                "ticker": ticker
            }
        
        # Get current period recommendations
        current = recs.iloc[0] if not recs.empty else None
        
        if current is None:
            return {
                "error": f"No current recommendations for {ticker}",
                "ticker": ticker
            }
        
        strong_buy = int(current.get('strongBuy', 0))
        buy = int(current.get('buy', 0))
        hold = int(current.get('hold', 0))
        sell = int(current.get('sell', 0))
        strong_sell = int(current.get('strongSell', 0))
        
        total = strong_buy + buy + hold + sell + strong_sell
        
        # Calculate percentages
        if total > 0:
            strong_buy_pct = (strong_buy / total) * 100
            buy_pct = (buy / total) * 100
            hold_pct = (hold / total) * 100
            sell_pct = (sell / total) * 100
            strong_sell_pct = (strong_sell / total) * 100
            
            # Calculate bullish percentage (strong buy + buy)
            bullish_pct = strong_buy_pct + buy_pct
        else:
            strong_buy_pct = buy_pct = hold_pct = sell_pct = strong_sell_pct = bullish_pct = 0
        
        # Get recommendation mean (1=Strong Buy, 5=Strong Sell)
        rec_mean = safe_get_value(info.get('recommendationMean', 0))
        rec_key = info.get('recommendationKey', 'none')
        
        # Determine overall sentiment
        if rec_mean < 2.0:
            sentiment = "Very Bullish"
            sentiment_color = "green"
        elif rec_mean < 2.5:
            sentiment = "Bullish"
            sentiment_color = "green"
        elif rec_mean < 3.5:
            sentiment = "Neutral"
            sentiment_color = "yellow"
        elif rec_mean < 4.0:
            sentiment = "Bearish"
            sentiment_color = "red"
        else:
            sentiment = "Very Bearish"
            sentiment_color = "red"
        
        # Historical trend (compare current vs 3 months ago)
        trend = "stable"
        trend_description = "No significant change"
        
        if len(recs) >= 4:
            prev = recs.iloc[3]
            prev_strong_buy = int(prev.get('strongBuy', 0))
            prev_buy = int(prev.get('buy', 0))
            prev_total = prev_strong_buy + int(prev.get('hold', 0)) + int(prev.get('sell', 0)) + int(prev.get('strongSell', 0))
            
            if prev_total > 0:
                prev_bullish_pct = ((prev_strong_buy + prev_buy) / prev_total) * 100
                change = bullish_pct - prev_bullish_pct
                
                if change > 10:
                    trend = "improving"
                    trend_description = f"Bullish recommendations increased {change:.1f}% in 3 months"
                elif change < -10:
                    trend = "deteriorating"
                    trend_description = f"Bullish recommendations decreased {abs(change):.1f}% in 3 months"
        
        # Get historical recommendations
        historical = []
        for i in range(min(4, len(recs))):
            row = recs.iloc[i]
            period = row.get('period', f'{i}m')
            historical.append({
                "period": period,
                "strongBuy": int(row.get('strongBuy', 0)),
                "buy": int(row.get('buy', 0)),
                "hold": int(row.get('hold', 0)),
                "sell": int(row.get('sell', 0)),
                "strongSell": int(row.get('strongSell', 0))
            })
        
        return {
            "ticker": ticker,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_distribution": {
                "strong_buy": strong_buy,
                "buy": buy,
                "hold": hold,
                "sell": sell,
                "strong_sell": strong_sell,
                "total": total
            },
            "percentages": {
                "strong_buy_pct": round(strong_buy_pct, 1),
                "buy_pct": round(buy_pct, 1),
                "hold_pct": round(hold_pct, 1),
                "sell_pct": round(sell_pct, 1),
                "strong_sell_pct": round(strong_sell_pct, 1),
                "bullish_pct": round(bullish_pct, 1)
            },
            "recommendation_mean": {
                "score": round(rec_mean, 2),
                "rating": rec_key,
                "interpretation": "1=Strong Buy, 2=Buy, 3=Hold, 4=Sell, 5=Strong Sell"
            },
            "sentiment": {
                "overall": sentiment,
                "color": sentiment_color
            },
            "trend": {
                "direction": trend,
                "description": trend_description
            },
            "historical": historical
        }
        
    except Exception as e:
        return {
            "error": f"Failed to get recommendations for {ticker}: {str(e)}",
            "ticker": ticker
        }

def get_revision_velocity(ticker: str, days: int = 90) -> Dict:
    """
    Track analyst target price revision velocity
    
    Analyzes upgrades/downgrades over specified period to measure:
    - Number of upgrades vs downgrades
    - Price target increases vs decreases
    - Momentum of analyst sentiment
    - Recent revision activity
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days to analyze (default 90)
    """
    ticker = ticker.upper()
    
    try:
        stock = yf.Ticker(ticker)
        upgrades = stock.upgrades_downgrades
        
        if upgrades is None or upgrades.empty:
            return {
                "error": f"No upgrade/downgrade data available for {ticker}",
                "ticker": ticker
            }
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # upgrades_downgrades index is GradeDate
        recent = upgrades[upgrades.index >= cutoff_date]
        
        if recent.empty:
            return {
                "ticker": ticker,
                "period_days": days,
                "total_revisions": 0,
                "upgrades": 0,
                "downgrades": 0,
                "target_increases": 0,
                "target_decreases": 0,
                "net_sentiment": "neutral",
                "velocity": "low",
                "message": f"No analyst revisions in the past {days} days"
            }
        
        # Count upgrades vs downgrades
        upgrades_count = 0
        downgrades_count = 0
        maintained_count = 0
        target_increases = 0
        target_decreases = 0
        
        for idx, row in recent.iterrows():
            action = str(row.get('Action', '')).lower()
            from_grade = str(row.get('FromGrade', '')).lower()
            to_grade = str(row.get('ToGrade', '')).lower()
            price_action = str(row.get('priceTargetAction', '')).lower()
            
            # Check if upgrade or downgrade
            if action == 'up' or 'upgrade' in action:
                upgrades_count += 1
            elif action == 'down' or 'downgrade' in action:
                downgrades_count += 1
            elif action == 'main' or 'maintains' in action:
                maintained_count += 1
            else:
                # Try to infer from grade changes
                buy_grades = ['buy', 'strong buy', 'outperform', 'overweight']
                sell_grades = ['sell', 'strong sell', 'underperform', 'underweight']
                
                from_is_buy = any(g in from_grade for g in buy_grades)
                to_is_buy = any(g in to_grade for g in buy_grades)
                from_is_sell = any(g in from_grade for g in sell_grades)
                to_is_sell = any(g in to_grade for g in sell_grades)
                
                if not from_is_buy and to_is_buy:
                    upgrades_count += 1
                elif not from_is_sell and to_is_sell:
                    downgrades_count += 1
            
            # Check price target changes
            if 'raise' in price_action or 'increase' in price_action:
                target_increases += 1
            elif 'lower' in price_action or 'decrease' in price_action or 'cut' in price_action:
                target_decreases += 1
        
        total_revisions = len(recent)
        
        # Calculate net sentiment
        net_upgrades = upgrades_count - downgrades_count
        net_target_changes = target_increases - target_decreases
        
        # Determine overall sentiment
        if net_upgrades > 3 or net_target_changes > 3:
            net_sentiment = "bullish"
            sentiment_color = "green"
        elif net_upgrades > 0 or net_target_changes > 0:
            net_sentiment = "slightly_bullish"
            sentiment_color = "green"
        elif net_upgrades < -3 or net_target_changes < -3:
            net_sentiment = "bearish"
            sentiment_color = "red"
        elif net_upgrades < 0 or net_target_changes < 0:
            net_sentiment = "slightly_bearish"
            sentiment_color = "red"
        else:
            net_sentiment = "neutral"
            sentiment_color = "yellow"
        
        # Determine velocity (activity level)
        revisions_per_month = (total_revisions / days) * 30
        
        if revisions_per_month > 10:
            velocity = "very_high"
            velocity_description = "Very active analyst coverage"
        elif revisions_per_month > 5:
            velocity = "high"
            velocity_description = "Active analyst coverage"
        elif revisions_per_month > 2:
            velocity = "moderate"
            velocity_description = "Moderate analyst coverage"
        else:
            velocity = "low"
            velocity_description = "Low analyst activity"
        
        # Get recent revisions
        recent_revisions = []
        for idx, row in recent.head(10).iterrows():
            recent_revisions.append({
                "date": idx.strftime("%Y-%m-%d"),
                "firm": str(row.get('Firm', 'Unknown')),
                "action": str(row.get('Action', '')),
                "to_grade": str(row.get('ToGrade', '')),
                "from_grade": str(row.get('FromGrade', '')),
                "price_target": safe_get_value(row.get('currentPriceTarget', 0)),
                "prior_target": safe_get_value(row.get('priorPriceTarget', 0))
            })
        
        return {
            "ticker": ticker,
            "period_days": days,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_revisions": total_revisions,
                "upgrades": upgrades_count,
                "downgrades": downgrades_count,
                "maintained": maintained_count,
                "target_increases": target_increases,
                "target_decreases": target_decreases,
                "net_upgrades": net_upgrades,
                "net_target_changes": net_target_changes
            },
            "sentiment": {
                "net_sentiment": net_sentiment,
                "color": sentiment_color,
                "description": f"{net_upgrades:+d} net upgrades, {net_target_changes:+d} net target increases"
            },
            "velocity": {
                "level": velocity,
                "description": velocity_description,
                "revisions_per_month": round(revisions_per_month, 1)
            },
            "recent_revisions": recent_revisions,
            "interpretation": {
                "positive_signals": f"{upgrades_count} upgrades, {target_increases} target increases",
                "negative_signals": f"{downgrades_count} downgrades, {target_decreases} target decreases",
                "momentum": f"{'Positive' if net_upgrades > 0 else 'Negative' if net_upgrades < 0 else 'Neutral'} analyst momentum"
            }
        }
        
    except Exception as e:
        return {
            "error": f"Failed to get revision velocity for {ticker}: {str(e)}",
            "ticker": ticker
        }

def get_target_summary(ticker: str) -> Dict:
    """
    Comprehensive analyst target price summary
    
    Combines:
    - Consensus targets (mean, median, high, low)
    - Recommendation distribution
    - Recent revision velocity (90 days)
    - Overall analyst outlook
    """
    ticker = ticker.upper()
    
    try:
        # Get all components
        targets = get_consensus_targets(ticker)
        recommendations = get_recommendation_distribution(ticker)
        revisions = get_revision_velocity(ticker, days=90)
        
        if "error" in targets:
            return targets
        
        # Combine into unified summary
        return {
            "ticker": ticker,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_price": targets["current_price"],
            "consensus_targets": targets["consensus"],
            "bull_bear_cases": {
                "bull_case": targets["bull_case"],
                "bear_case": targets["bear_case"]
            },
            "recommendation_distribution": {
                "current": recommendations.get("current_distribution", {}),
                "percentages": recommendations.get("percentages", {}),
                "mean_score": recommendations.get("recommendation_mean", {})
            } if "error" not in recommendations else None,
            "revision_velocity_90d": {
                "summary": revisions.get("summary", {}),
                "sentiment": revisions.get("sentiment", {}),
                "velocity": revisions.get("velocity", {})
            } if "error" not in revisions else None,
            "overall_outlook": {
                "target_assessment": targets["assessment"]["rating"],
                "sentiment": recommendations.get("sentiment", {}).get("overall", "N/A") if "error" not in recommendations else "N/A",
                "revision_momentum": revisions.get("sentiment", {}).get("net_sentiment", "N/A") if "error" not in revisions else "N/A"
            },
            "key_metrics": {
                "mean_upside_pct": targets["consensus"]["mean_upside_pct"],
                "num_analysts": targets["coverage"]["num_analysts"],
                "bullish_analysts_pct": recommendations.get("percentages", {}).get("bullish_pct", 0) if "error" not in recommendations else 0,
                "net_upgrades_90d": revisions.get("summary", {}).get("net_upgrades", 0) if "error" not in revisions else 0
            }
        }
        
    except Exception as e:
        return {
            "error": f"Failed to generate target summary for {ticker}: {str(e)}",
            "ticker": ticker
        }

def compare_targets(tickers: List[str]) -> Dict:
    """
    Compare analyst targets across multiple stocks
    
    Useful for:
    - Sector comparison
    - Stock selection
    - Relative value analysis
    """
    results = []
    
    for ticker in tickers:
        ticker = ticker.upper()
        summary = get_target_summary(ticker)
        
        if "error" not in summary:
            results.append({
                "ticker": ticker,
                "current_price": summary["current_price"],
                "mean_target": summary["consensus_targets"]["mean_target"],
                "mean_upside_pct": summary["consensus_targets"]["mean_upside_pct"],
                "bull_upside_pct": summary["bull_bear_cases"]["bull_case"]["upside_pct"],
                "bear_downside_pct": summary["bull_bear_cases"]["bear_case"]["downside_pct"],
                "num_analysts": summary["key_metrics"]["num_analysts"],
                "bullish_analysts_pct": summary["key_metrics"]["bullish_analysts_pct"],
                "net_upgrades_90d": summary["key_metrics"]["net_upgrades_90d"]
            })
    
    if not results:
        return {
            "error": "No valid data for any ticker",
            "tickers": tickers
        }
    
    # Sort by mean upside
    results.sort(key=lambda x: x["mean_upside_pct"], reverse=True)
    
    return {
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "comparison": results,
        "best_upside": results[0] if results else None,
        "worst_upside": results[-1] if results else None,
        "interpretation": "Stocks ranked by analyst consensus upside potential (mean target vs current price)"
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: analyst_target_price.py <command> [args]",
            "commands": {
                "analyst-consensus": "Get consensus price targets - analyst_target_price.py analyst-consensus <ticker>",
                "analyst-recs": "Get recommendation distribution - analyst_target_price.py analyst-recs <ticker>",
                "analyst-revisions": "Get revision velocity - analyst_target_price.py analyst-revisions <ticker> [days]",
                "analyst-summary": "Get comprehensive summary - analyst_target_price.py analyst-summary <ticker>",
                "analyst-compare": "Compare targets - analyst_target_price.py analyst-compare <ticker1> <ticker2> ...",
                "consensus": "(alias for analyst-consensus)",
                "recommendations": "(alias for analyst-recs)",
                "revisions": "(alias for analyst-revisions)",
                "summary": "(alias for analyst-summary)",
                "compare": "(alias for analyst-compare)"
            }
        }))
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Support both new names and legacy names for backward compatibility
    if command in ["consensus", "analyst-consensus"]:
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Ticker required"}))
            sys.exit(1)
        result = get_consensus_targets(sys.argv[2])
    
    elif command in ["recommendations", "analyst-recs"]:
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Ticker required"}))
            sys.exit(1)
        result = get_recommendation_distribution(sys.argv[2])
    
    elif command in ["revisions", "analyst-revisions"]:
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Ticker required"}))
            sys.exit(1)
        ticker = sys.argv[2]
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 90
        result = get_revision_velocity(ticker, days)
    
    elif command in ["summary", "analyst-summary"]:
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Ticker required"}))
            sys.exit(1)
        result = get_target_summary(sys.argv[2])
    
    elif command in ["compare", "analyst-compare"]:
        if len(sys.argv) < 3:
            print(json.dumps({"error": "At least one ticker required"}))
            sys.exit(1)
        tickers = sys.argv[2:]
        result = compare_targets(tickers)
    
    else:
        result = {
            "error": f"Unknown command: {command}",
            "available": ["analyst-consensus", "analyst-recs", "analyst-revisions", "analyst-summary", "analyst-compare"],
            "aliases": ["consensus", "recommendations", "revisions", "summary", "compare"]
        }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

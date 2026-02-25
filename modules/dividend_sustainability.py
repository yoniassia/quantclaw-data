#!/usr/bin/env python3
"""
Dividend Sustainability Module — Payout Ratio Trends, FCF Coverage, Dividend Cut Probability

Analyzes dividend sustainability indicators to assess dividend safety:
- Payout ratio trends (dividends / earnings)
- Free cash flow (FCF) dividend coverage
- Dividend growth rate and consistency
- Dividend Aristocrat qualification check (25+ years of increases)
- Probability of dividend cut based on fundamentals
- Historical dividend history and ex-dates

Data Sources: Yahoo Finance (dividend history, financial statements, cash flow)

Author: QUANTCLAW DATA Build Agent
Phase: 57
"""

import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yfinance as yf
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

def calculate_payout_ratio(dividends: float, earnings: float) -> float:
    """
    Calculate Payout Ratio
    Payout Ratio = (Total Dividends Paid / Net Income) × 100
    
    Sustainable range: 30-60% for most companies
    >80% = high risk, <30% = room to grow
    """
    if earnings <= 0:
        return 0 if dividends == 0 else 999  # 999 indicates paying dividends with no earnings
    return (dividends / earnings) * 100

def calculate_fcf_coverage(dividends: float, free_cash_flow: float) -> float:
    """
    Calculate FCF Dividend Coverage
    FCF Coverage = Free Cash Flow / Total Dividends Paid
    
    >1.5 = excellent coverage
    1.0-1.5 = adequate coverage
    <1.0 = dividend at risk (paying more than FCF generates)
    """
    if dividends <= 0:
        return 0
    return free_cash_flow / dividends

def calculate_dividend_growth_rate(dividend_history: List[float]) -> float:
    """
    Calculate Compound Annual Growth Rate (CAGR) for dividends
    """
    if len(dividend_history) < 2:
        return 0
    
    oldest = dividend_history[-1]
    newest = dividend_history[0]
    years = len(dividend_history) - 1
    
    if oldest <= 0:
        return 0
    
    try:
        cagr = (pow(newest / oldest, 1 / years) - 1) * 100
        return cagr
    except:
        return 0

def check_dividend_aristocrat(ticker_obj) -> Dict:
    """
    Check if company qualifies as Dividend Aristocrat
    Requirements:
    - S&P 500 member (we can't verify, so we skip this)
    - 25+ consecutive years of dividend increases
    """
    try:
        # Get dividend history
        dividends = ticker_obj.dividends
        
        if len(dividends) == 0:
            return {
                "is_aristocrat": False,
                "consecutive_years": 0,
                "reason": "No dividend history"
            }
        
        # Group by year and sum annual dividends
        annual_dividends = dividends.resample('YE').sum()
        
        if len(annual_dividends) < 25:
            return {
                "is_aristocrat": False,
                "consecutive_years": len(annual_dividends),
                "reason": f"Only {len(annual_dividends)} years of dividend history (need 25+)"
            }
        
        # Check for consecutive increases
        consecutive_increases = 0
        for i in range(len(annual_dividends) - 1):
            if annual_dividends.iloc[-(i+1)] > annual_dividends.iloc[-(i+2)]:
                consecutive_increases += 1
            else:
                break
        
        is_aristocrat = consecutive_increases >= 25
        
        return {
            "is_aristocrat": is_aristocrat,
            "consecutive_years": consecutive_increases,
            "reason": f"{consecutive_increases} consecutive years of dividend increases" if is_aristocrat else f"Only {consecutive_increases} consecutive years"
        }
        
    except Exception as e:
        return {
            "is_aristocrat": False,
            "consecutive_years": 0,
            "reason": f"Analysis failed: {str(e)}"
        }

def dividend_health_report(ticker: str) -> Dict:
    """
    Comprehensive dividend sustainability report
    
    Analyzes:
    1. Current dividend yield
    2. Payout ratio trends (5 years)
    3. FCF coverage trends
    4. Dividend growth rate (CAGR)
    5. Dividend Aristocrat status
    6. Cut probability score
    """
    ticker = ticker.upper()
    
    try:
        # Fetch data using yfinance
        stock = yf.Ticker(ticker)
        
        # Get current info
        info = stock.info
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
        trailing_annual_dividend = info.get('trailingAnnualDividendRate', 0)
        
        # Get financials
        income_stmt = stock.financials.T  # Transpose to have dates as rows
        cashflow = stock.cashflow.T
        
        if income_stmt.empty or cashflow.empty:
            return {
                "error": f"No historical financial data available for {ticker}",
                "ticker": ticker
            }
        
        # Sort by date (most recent first)
        income_stmt = income_stmt.sort_index(ascending=False)
        cashflow = cashflow.sort_index(ascending=False)
        
        # Analyze last 5 years (or available periods)
        num_periods = min(5, len(income_stmt))
        
        payout_ratio_trend = []
        fcf_coverage_trend = []
        annual_dividends_paid = []
        
        for i in range(num_periods):
            try:
                # Extract metrics
                net_income = safe_get_value(income_stmt.iloc[i].get('Net Income', 0))
                
                # Get cashflow metrics (try to match date)
                try:
                    cf_row = cashflow.loc[income_stmt.index[i]]
                except:
                    # If exact date match fails, use closest date
                    if i < len(cashflow):
                        cf_row = cashflow.iloc[i]
                    else:
                        cf_row = None
                
                if cf_row is not None:
                    operating_cash_flow = safe_get_value(cf_row.get('Operating Cash Flow', 
                                                         cf_row.get('Total Cash From Operating Activities', 0)))
                    capex = abs(safe_get_value(cf_row.get('Capital Expenditure', 
                                               cf_row.get('Capital Expenditures', 0))))
                    dividends_paid = abs(safe_get_value(cf_row.get('Dividends Paid', 
                                                        cf_row.get('Cash Dividends Paid', 0))))
                else:
                    operating_cash_flow = capex = dividends_paid = 0
                
                # Calculate free cash flow
                free_cash_flow = operating_cash_flow - capex
                
                # Calculate ratios
                payout_ratio = calculate_payout_ratio(dividends_paid, net_income)
                fcf_coverage = calculate_fcf_coverage(dividends_paid, free_cash_flow)
                
                payout_ratio_trend.append(payout_ratio)
                fcf_coverage_trend.append(fcf_coverage)
                annual_dividends_paid.append(dividends_paid)
                
            except Exception as e:
                continue
        
        # Get dividend history for growth rate
        dividends = stock.dividends
        if len(dividends) > 0:
            # Group by year and calculate annual totals
            annual_divs = dividends.resample('YE').sum()
            dividend_growth_rate = calculate_dividend_growth_rate(annual_divs.tolist()[:10])  # Last 10 years
        else:
            dividend_growth_rate = 0
        
        # Check Dividend Aristocrat status
        aristocrat_status = check_dividend_aristocrat(stock)
        
        # Calculate cut probability score (0-100, higher = more likely to cut)
        cut_probability = 0
        risk_factors = []
        
        # Factor 1: High payout ratio (>80%)
        current_payout = payout_ratio_trend[0] if payout_ratio_trend else 0
        if current_payout > 100:
            cut_probability += 40
            risk_factors.append({
                "factor": "Payout ratio > 100%",
                "severity": "critical",
                "value": f"{current_payout:.1f}%",
                "impact": "Paying more than earnings"
            })
        elif current_payout > 80:
            cut_probability += 25
            risk_factors.append({
                "factor": "High payout ratio",
                "severity": "high",
                "value": f"{current_payout:.1f}%",
                "impact": "Limited room for earnings decline"
            })
        
        # Factor 2: Poor FCF coverage (<1.0)
        current_fcf_coverage = fcf_coverage_trend[0] if fcf_coverage_trend else 0
        if current_fcf_coverage < 0.5:
            cut_probability += 35
            risk_factors.append({
                "factor": "Severely inadequate FCF coverage",
                "severity": "critical",
                "value": f"{current_fcf_coverage:.2f}x",
                "impact": "Dividend consuming more than half of FCF"
            })
        elif current_fcf_coverage < 1.0:
            cut_probability += 20
            risk_factors.append({
                "factor": "Inadequate FCF coverage",
                "severity": "high",
                "value": f"{current_fcf_coverage:.2f}x",
                "impact": "Dividend exceeds free cash flow"
            })
        elif current_fcf_coverage < 1.5:
            cut_probability += 10
            risk_factors.append({
                "factor": "Marginal FCF coverage",
                "severity": "medium",
                "value": f"{current_fcf_coverage:.2f}x",
                "impact": "Limited cushion for business headwinds"
            })
        
        # Factor 3: Declining payout ratio trend (increasing = warning)
        if len(payout_ratio_trend) >= 3:
            recent_avg = sum(payout_ratio_trend[:2]) / 2
            older_avg = sum(payout_ratio_trend[-2:]) / 2
            
            if recent_avg > older_avg + 20:
                cut_probability += 15
                risk_factors.append({
                    "factor": "Rising payout ratio trend",
                    "severity": "medium",
                    "value": f"+{recent_avg - older_avg:.1f} pp",
                    "impact": "Earnings declining faster than dividends"
                })
        
        # Factor 4: Negative dividend growth
        if dividend_growth_rate < 0:
            cut_probability += 10
            risk_factors.append({
                "factor": "Negative dividend growth",
                "severity": "medium",
                "value": f"{dividend_growth_rate:.1f}%",
                "impact": "Already reducing dividends"
            })
        
        # Factor 5: No dividend history or very short history
        if len(annual_dividends_paid) < 3:
            cut_probability += 5
            risk_factors.append({
                "factor": "Short dividend history",
                "severity": "low",
                "value": f"{len(annual_dividends_paid)} years",
                "impact": "Limited track record"
            })
        
        # Cap at 100
        cut_probability = min(cut_probability, 100)
        
        # Determine overall assessment
        if cut_probability >= 70:
            sustainability = "Very High Risk"
            color = "red"
            recommendation = "Dividend cut highly likely. Avoid or sell."
        elif cut_probability >= 50:
            sustainability = "High Risk"
            color = "red"
            recommendation = "Dividend cut probable. Exercise caution."
        elif cut_probability >= 30:
            sustainability = "Moderate Risk"
            color = "yellow"
            recommendation = "Monitor closely for deterioration."
        elif cut_probability >= 15:
            sustainability = "Low Risk"
            color = "green"
            recommendation = "Dividend appears sustainable."
        else:
            sustainability = "Very Low Risk"
            color = "green"
            recommendation = "Highly sustainable dividend. Excellent income investment."
        
        return {
            "ticker": ticker,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_metrics": {
                "price": current_price,
                "annual_dividend": trailing_annual_dividend,
                "dividend_yield": round(dividend_yield, 2),
                "payout_ratio": round(current_payout, 2),
                "fcf_coverage": round(current_fcf_coverage, 2),
                "dividend_growth_rate_cagr": round(dividend_growth_rate, 2)
            },
            "dividend_aristocrat": aristocrat_status,
            "cut_probability": {
                "score": cut_probability,
                "sustainability": sustainability,
                "color": color,
                "recommendation": recommendation,
                "risk_factors": risk_factors
            },
            "historical_trends": {
                "payout_ratio": [round(p, 2) for p in payout_ratio_trend],
                "fcf_coverage": [round(f, 2) for f in fcf_coverage_trend],
                "annual_dividends_paid": [round(d, 2) for d in annual_dividends_paid]
            },
            "interpretation": {
                "payout_ratio": "30-60% is ideal. >80% is risky. >100% means paying more than earnings.",
                "fcf_coverage": ">1.5x is excellent. 1.0-1.5x is adequate. <1.0x is at risk.",
                "dividend_growth": "Positive CAGR indicates commitment to shareholders.",
                "aristocrat": "25+ years of consecutive increases = Dividend Aristocrat status."
            }
        }
        
    except Exception as e:
        return {
            "error": f"Analysis failed for {ticker}: {str(e)}",
            "ticker": ticker
        }

def payout_ratio_analysis(ticker: str) -> Dict:
    """Focused payout ratio trend analysis"""
    result = dividend_health_report(ticker)
    
    if "error" in result:
        return result
    
    payout_trend = result["historical_trends"]["payout_ratio"]
    current_payout = result["current_metrics"]["payout_ratio"]
    
    # Determine trend direction
    if len(payout_trend) >= 3:
        if payout_trend[0] > payout_trend[-1] + 10:
            trend = "increasing"
            trend_description = "Rising (⚠️ Warning)"
        elif payout_trend[0] < payout_trend[-1] - 10:
            trend = "decreasing"
            trend_description = "Declining (✓ Improving)"
        else:
            trend = "stable"
            trend_description = "Stable"
    else:
        trend = "unknown"
        trend_description = "Insufficient data"
    
    # Assessment
    if current_payout > 100:
        assessment = "Critical - Paying more than earnings"
        color = "red"
    elif current_payout > 80:
        assessment = "High Risk - Limited cushion"
        color = "red"
    elif current_payout > 60:
        assessment = "Moderate - Above ideal range"
        color = "yellow"
    elif current_payout > 30:
        assessment = "Healthy - Sustainable range"
        color = "green"
    else:
        assessment = "Conservative - Room to grow"
        color = "green"
    
    return {
        "ticker": result["ticker"],
        "current_payout_ratio": current_payout,
        "trend": trend,
        "trend_description": trend_description,
        "assessment": assessment,
        "color": color,
        "payout_ratio_history": payout_trend,
        "interpretation": "Ideal payout ratio: 30-60%. Above 80% indicates risk. Above 100% means company is paying more in dividends than it earns."
    }

def fcf_coverage_analysis(ticker: str) -> Dict:
    """Focused free cash flow dividend coverage analysis"""
    result = dividend_health_report(ticker)
    
    if "error" in result:
        return result
    
    fcf_coverage = result["current_metrics"]["fcf_coverage"]
    fcf_history = result["historical_trends"]["fcf_coverage"]
    
    # Determine trend
    if len(fcf_history) >= 3:
        if fcf_history[0] < fcf_history[-1] - 0.3:
            trend = "deteriorating"
            trend_description = "Deteriorating (⚠️ Warning)"
        elif fcf_history[0] > fcf_history[-1] + 0.3:
            trend = "improving"
            trend_description = "Improving (✓ Good)"
        else:
            trend = "stable"
            trend_description = "Stable"
    else:
        trend = "unknown"
        trend_description = "Insufficient data"
    
    # Assessment
    if fcf_coverage >= 2.0:
        assessment = "Excellent - Strong coverage"
        color = "green"
    elif fcf_coverage >= 1.5:
        assessment = "Good - Adequate cushion"
        color = "green"
    elif fcf_coverage >= 1.0:
        assessment = "Fair - Minimal cushion"
        color = "yellow"
    elif fcf_coverage >= 0.5:
        assessment = "Poor - Dividend at risk"
        color = "red"
    else:
        assessment = "Critical - Severely undercovered"
        color = "red"
    
    return {
        "ticker": result["ticker"],
        "current_fcf_coverage": round(fcf_coverage, 2),
        "trend": trend,
        "trend_description": trend_description,
        "assessment": assessment,
        "color": color,
        "fcf_coverage_history": fcf_history,
        "interpretation": "FCF Coverage >1.5x is ideal. <1.0x means dividend exceeds free cash flow. Company may be borrowing or depleting reserves to pay dividend."
    }

def dividend_cut_risk(ticker: str) -> Dict:
    """Calculate probability of dividend cut with detailed risk scoring"""
    result = dividend_health_report(ticker)
    
    if "error" in result:
        return result
    
    cut_prob = result["cut_probability"]
    
    return {
        "ticker": result["ticker"],
        "cut_probability_score": cut_prob["score"],
        "risk_level": cut_prob["sustainability"],
        "color": cut_prob["color"],
        "recommendation": cut_prob["recommendation"],
        "risk_factors": cut_prob["risk_factors"],
        "mitigating_factors": [
            {
                "factor": "Dividend Aristocrat",
                "value": result["dividend_aristocrat"]["is_aristocrat"],
                "description": result["dividend_aristocrat"]["reason"]
            },
            {
                "factor": "Dividend Growth Rate",
                "value": f"{result['current_metrics']['dividend_growth_rate_cagr']:.1f}%",
                "description": "Positive growth indicates commitment"
            }
        ],
        "key_metrics": {
            "payout_ratio": result["current_metrics"]["payout_ratio"],
            "fcf_coverage": result["current_metrics"]["fcf_coverage"],
            "yield": result["current_metrics"]["dividend_yield"]
        },
        "interpretation": "Score 0-100. <15 = very safe. 15-30 = low risk. 30-50 = moderate risk. 50-70 = high risk. >70 = cut highly likely."
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: dividend_sustainability.py <command> <ticker>",
            "commands": ["dividend-health", "payout-ratio", "fcf-coverage", "dividend-cut-risk"]
        }))
        sys.exit(1)
    
    command = sys.argv[1]
    
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": f"Ticker required for command: {command}"
        }))
        sys.exit(1)
    
    ticker = sys.argv[2].upper()
    
    if command == "dividend-health":
        result = dividend_health_report(ticker)
    elif command == "payout-ratio":
        result = payout_ratio_analysis(ticker)
    elif command == "fcf-coverage":
        result = fcf_coverage_analysis(ticker)
    elif command == "dividend-cut-risk":
        result = dividend_cut_risk(ticker)
    else:
        result = {
            "error": f"Unknown command: {command}",
            "available": ["dividend-health", "payout-ratio", "fcf-coverage", "dividend-cut-risk"]
        }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

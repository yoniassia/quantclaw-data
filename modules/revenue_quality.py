#!/usr/bin/env python3
"""
Revenue Quality Analysis Module — Cash Flow vs Earnings Divergence, DSO Trends, Channel Stuffing Detection

Analyzes revenue quality indicators to detect potential accounting manipulation:
- Cash flow from operations vs net income divergence
- Days Sales Outstanding (DSO) trend analysis
- Working capital as % of revenue monitoring
- Revenue growth vs receivables growth comparison
- Accruals ratio calculation
- Channel stuffing red flags

Data Sources: Yahoo Finance (cash flow statements, balance sheets, income statements)

Author: QUANTCLAW DATA Build Agent
Phase: 52
"""

import sys
import json
from datetime import datetime
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

def calculate_dso(receivables: float, revenue: float, days: int = 365) -> float:
    """
    Calculate Days Sales Outstanding (DSO)
    DSO = (Accounts Receivable / Revenue) × Number of Days
    
    Lower DSO is better — indicates faster cash collection
    Rising DSO can signal channel stuffing or collection problems
    """
    if revenue <= 0:
        return 0
    return (receivables / revenue) * days

def calculate_accruals_ratio(net_income: float, operating_cash_flow: float, total_assets: float) -> float:
    """
    Calculate Accruals Ratio (Sloan 1996)
    Accruals Ratio = (Net Income - Operating Cash Flow) / Total Assets
    
    High positive accruals ratio (>0.1) can indicate earnings manipulation
    """
    if total_assets <= 0:
        return 0
    return (net_income - operating_cash_flow) / total_assets

def analyze_revenue_quality(ticker: str) -> Dict:
    """
    Comprehensive revenue quality analysis
    
    Red flags detected:
    1. CFO < Net Income consistently (earnings quality issue)
    2. Rising DSO trend (potential channel stuffing)
    3. Receivables growing faster than revenue
    4. High accruals ratio (earnings manipulation risk)
    5. Working capital deterioration
    """
    ticker = ticker.upper()
    
    try:
        # Fetch data using yfinance
        stock = yf.Ticker(ticker)
        
        # Get financials
        income_stmt = stock.financials.T  # Transpose to have dates as rows
        balance_sheet = stock.balance_sheet.T
        cashflow = stock.cashflow.T
        
        if income_stmt.empty or balance_sheet.empty or cashflow.empty:
            return {
                "error": f"No historical financial data available for {ticker}",
                "ticker": ticker
            }
        
        # Sort by date (most recent first)
        income_stmt = income_stmt.sort_index(ascending=False)
        balance_sheet = balance_sheet.sort_index(ascending=False)
        cashflow = cashflow.sort_index(ascending=False)
        
        analysis_results = []
        dso_trend = []
        cfo_vs_ni_trend = []
        receivables_growth = []
        revenue_growth = []
        accruals_history = []
        
        # Analyze last 4 years (or available periods)
        num_periods = min(4, len(income_stmt))
        
        for i in range(num_periods):
            try:
                # Get the date for this period
                period_date = income_stmt.index[i].strftime('%Y-%m-%d')
                
                # Extract key metrics from income statement
                net_income = safe_get_value(income_stmt.iloc[i].get('Net Income', 0))
                revenue = safe_get_value(income_stmt.iloc[i].get('Total Revenue', 0))
                
                # Extract from balance sheet (try to match date)
                try:
                    bs_row = balance_sheet.loc[income_stmt.index[i]]
                    receivables = safe_get_value(bs_row.get('Accounts Receivable', bs_row.get('Net Receivables', 0)))
                    total_assets = safe_get_value(bs_row.get('Total Assets', 0))
                    current_assets = safe_get_value(bs_row.get('Current Assets', bs_row.get('Total Current Assets', 0)))
                    current_liabilities = safe_get_value(bs_row.get('Current Liabilities', bs_row.get('Total Current Liabilities', 0)))
                except:
                    # If exact date match fails, use closest date
                    if i < len(balance_sheet):
                        bs_row = balance_sheet.iloc[i]
                        receivables = safe_get_value(bs_row.get('Accounts Receivable', bs_row.get('Net Receivables', 0)))
                        total_assets = safe_get_value(bs_row.get('Total Assets', 0))
                        current_assets = safe_get_value(bs_row.get('Current Assets', bs_row.get('Total Current Assets', 0)))
                        current_liabilities = safe_get_value(bs_row.get('Current Liabilities', bs_row.get('Total Current Liabilities', 0)))
                    else:
                        receivables = total_assets = current_assets = current_liabilities = 0
                
                # Extract from cashflow (try to match date)
                try:
                    cf_row = cashflow.loc[income_stmt.index[i]]
                    operating_cash_flow = safe_get_value(cf_row.get('Operating Cash Flow', cf_row.get('Total Cash From Operating Activities', 0)))
                except:
                    # If exact date match fails, use closest date
                    if i < len(cashflow):
                        cf_row = cashflow.iloc[i]
                        operating_cash_flow = safe_get_value(cf_row.get('Operating Cash Flow', cf_row.get('Total Cash From Operating Activities', 0)))
                    else:
                        operating_cash_flow = 0
                
                # Calculate metrics
                dso = calculate_dso(receivables, revenue)
                accruals_ratio = calculate_accruals_ratio(net_income, operating_cash_flow, total_assets)
                cfo_to_ni_ratio = operating_cash_flow / net_income if net_income != 0 else 0
                working_capital = current_assets - current_liabilities
                working_capital_ratio = (working_capital / revenue * 100) if revenue > 0 else 0
                
                dso_trend.append(dso)
                cfo_vs_ni_trend.append(cfo_to_ni_ratio)
                accruals_history.append(accruals_ratio)
                
                # Calculate growth rates (compare to previous period)
                if i < num_periods - 1:
                    try:
                        prev_revenue = safe_get_value(income_stmt.iloc[i + 1].get('Total Revenue', 0))
                        
                        # Get previous period receivables
                        try:
                            prev_bs = balance_sheet.iloc[i + 1]
                            prev_receivables = safe_get_value(prev_bs.get('Accounts Receivable', prev_bs.get('Net Receivables', 0)))
                        except:
                            prev_receivables = 0
                        
                        rev_growth = ((revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
                        rec_growth = ((receivables - prev_receivables) / prev_receivables * 100) if prev_receivables > 0 else 0
                        
                        revenue_growth.append(rev_growth)
                        receivables_growth.append(rec_growth)
                    except:
                        pass
                
                analysis_results.append({
                    "period": period_date,
                    "revenue": revenue,
                    "net_income": net_income,
                    "operating_cash_flow": operating_cash_flow,
                    "receivables": receivables,
                    "dso": round(dso, 2),
                    "cfo_to_ni_ratio": round(cfo_to_ni_ratio, 2),
                    "accruals_ratio": round(accruals_ratio, 4),
                    "working_capital_pct_revenue": round(working_capital_ratio, 2)
                })
                
            except Exception as e:
                continue
        
        # Detect red flags
        red_flags = []
        quality_score = 100  # Start at 100, deduct points for issues
        
        # 1. CFO < Net Income consistently
        low_cfo_periods = sum(1 for ratio in cfo_vs_ni_trend if ratio < 0.8)
        if low_cfo_periods >= 2:
            red_flags.append({
                "flag": "Low Cash Conversion",
                "severity": "high",
                "description": f"Operating cash flow below 80% of net income in {low_cfo_periods} periods",
                "implication": "Earnings may be inflated with non-cash accruals"
            })
            quality_score -= 25
        
        # 2. Rising DSO trend
        if len(dso_trend) >= 3:
            dso_increasing = all(dso_trend[i] < dso_trend[i+1] for i in range(len(dso_trend)-1))
            if dso_increasing:
                dso_increase = ((dso_trend[0] - dso_trend[-1]) / dso_trend[-1] * 100)
                red_flags.append({
                    "flag": "Rising DSO Trend",
                    "severity": "medium",
                    "description": f"DSO increased by {dso_increase:.1f}% over analysis period",
                    "implication": "Potential channel stuffing or collection problems"
                })
                quality_score -= 15
        
        # 3. Receivables growing faster than revenue
        if revenue_growth and receivables_growth:
            avg_rev_growth = sum(revenue_growth) / len(revenue_growth)
            avg_rec_growth = sum(receivables_growth) / len(receivables_growth)
            
            if avg_rec_growth > avg_rev_growth + 10:  # 10% threshold
                red_flags.append({
                    "flag": "Receivables Outpacing Revenue",
                    "severity": "high",
                    "description": f"Receivables growing {avg_rec_growth:.1f}% vs revenue {avg_rev_growth:.1f}%",
                    "implication": "Aggressive revenue recognition or channel stuffing"
                })
                quality_score -= 30
        
        # 4. High accruals ratio
        recent_accruals = accruals_history[0] if accruals_history else 0
        if recent_accruals > 0.1:
            red_flags.append({
                "flag": "High Accruals Ratio",
                "severity": "high",
                "description": f"Accruals ratio of {recent_accruals:.4f} exceeds 0.1 threshold",
                "implication": "High risk of earnings manipulation (Sloan 1996)"
            })
            quality_score -= 20
        
        # 5. Deteriorating working capital
        if len(analysis_results) >= 2:
            wc_trend = [r['working_capital_pct_revenue'] for r in analysis_results]
            if wc_trend[0] < wc_trend[-1] - 5:  # 5% deterioration
                red_flags.append({
                    "flag": "Working Capital Deterioration",
                    "severity": "medium",
                    "description": f"Working capital decreased from {wc_trend[-1]:.1f}% to {wc_trend[0]:.1f}% of revenue",
                    "implication": "Potential cash flow stress or operational issues"
                })
                quality_score -= 10
        
        # Determine overall assessment
        if quality_score >= 90:
            assessment = "Excellent"
            color = "green"
        elif quality_score >= 75:
            assessment = "Good"
            color = "green"
        elif quality_score >= 60:
            assessment = "Fair"
            color = "yellow"
        elif quality_score >= 40:
            assessment = "Poor"
            color = "orange"
        else:
            assessment = "Very Poor"
            color = "red"
        
        return {
            "ticker": ticker,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "revenue_quality_score": quality_score,
            "assessment": assessment,
            "color": color,
            "red_flags": red_flags,
            "historical_metrics": analysis_results,
            "trends": {
                "dso_trend": [round(d, 2) for d in dso_trend],
                "cfo_to_ni_trend": [round(c, 2) for c in cfo_vs_ni_trend],
                "accruals_trend": [round(a, 4) for a in accruals_history],
                "revenue_growth": [round(r, 2) for r in revenue_growth],
                "receivables_growth": [round(r, 2) for r in receivables_growth]
            },
            "interpretation": {
                "dso": "Lower is better. Rising DSO may indicate channel stuffing or collection issues.",
                "cfo_to_ni": "Should be >= 1.0. Below 0.8 indicates poor cash conversion.",
                "accruals": "Above 0.1 signals high earnings manipulation risk (Sloan 1996).",
                "receivables_growth": "Should not exceed revenue growth significantly."
            }
        }
        
    except Exception as e:
        return {
            "error": f"Analysis failed for {ticker}: {str(e)}",
            "ticker": ticker
        }

def dso_trends(ticker: str) -> Dict:
    """Focused DSO trend analysis with visualization data"""
    result = analyze_revenue_quality(ticker)
    
    if "error" in result:
        return result
    
    return {
        "ticker": result["ticker"],
        "current_dso": result["historical_metrics"][0]["dso"] if result["historical_metrics"] else 0,
        "dso_history": result["trends"]["dso_trend"],
        "periods": [m["period"] for m in result["historical_metrics"]],
        "trend": "increasing" if len(result["trends"]["dso_trend"]) >= 2 and result["trends"]["dso_trend"][0] > result["trends"]["dso_trend"][-1] else "decreasing",
        "red_flags": [f for f in result["red_flags"] if "DSO" in f["flag"]]
    }

def channel_stuffing_detector(ticker: str) -> Dict:
    """
    Detect channel stuffing red flags
    
    Channel stuffing indicators:
    1. Receivables growing faster than revenue (>10% gap)
    2. Rising DSO trend
    3. Low CFO to NI ratio
    4. Q4 revenue spike followed by Q1 decline (if quarterly data available)
    """
    result = analyze_revenue_quality(ticker)
    
    if "error" in result:
        return result
    
    # Calculate channel stuffing risk score
    risk_score = 0
    indicators = []
    
    for flag in result["red_flags"]:
        if "Receivables Outpacing Revenue" in flag["flag"]:
            risk_score += 40
            indicators.append(flag)
        elif "Rising DSO" in flag["flag"]:
            risk_score += 30
            indicators.append(flag)
        elif "Low Cash Conversion" in flag["flag"]:
            risk_score += 20
            indicators.append(flag)
    
    if risk_score >= 70:
        risk_level = "High"
        color = "red"
    elif risk_score >= 40:
        risk_level = "Medium"
        color = "yellow"
    elif risk_score >= 20:
        risk_level = "Low"
        color = "orange"
    else:
        risk_level = "Minimal"
        color = "green"
    
    return {
        "ticker": result["ticker"],
        "channel_stuffing_risk": risk_level,
        "risk_score": risk_score,
        "color": color,
        "indicators": indicators,
        "current_metrics": {
            "dso": result["historical_metrics"][0]["dso"] if result["historical_metrics"] else 0,
            "cfo_to_ni_ratio": result["historical_metrics"][0]["cfo_to_ni_ratio"] if result["historical_metrics"] else 0,
            "receivables": result["historical_metrics"][0]["receivables"] if result["historical_metrics"] else 0,
            "revenue": result["historical_metrics"][0]["revenue"] if result["historical_metrics"] else 0
        },
        "interpretation": "Channel stuffing is when companies push excess inventory to distributors to inflate revenue. Watch for receivables growing faster than revenue, rising DSO, and poor cash conversion."
    }

def cash_flow_vs_earnings(ticker: str) -> Dict:
    """Analyze cash flow from operations vs net income divergence"""
    result = analyze_revenue_quality(ticker)
    
    if "error" in result:
        return result
    
    divergence_analysis = []
    
    for metric in result["historical_metrics"]:
        divergence = metric["operating_cash_flow"] - metric["net_income"]
        divergence_pct = (divergence / abs(metric["net_income"]) * 100) if metric["net_income"] != 0 else 0
        
        divergence_analysis.append({
            "period": metric["period"],
            "net_income": metric["net_income"],
            "operating_cash_flow": metric["operating_cash_flow"],
            "divergence": divergence,
            "divergence_pct": round(divergence_pct, 2),
            "quality": "Good" if metric["cfo_to_ni_ratio"] >= 1.0 else "Poor" if metric["cfo_to_ni_ratio"] < 0.8 else "Fair"
        })
    
    return {
        "ticker": result["ticker"],
        "divergence_analysis": divergence_analysis,
        "summary": {
            "avg_cfo_to_ni_ratio": round(sum(result["trends"]["cfo_to_ni_trend"]) / len(result["trends"]["cfo_to_ni_trend"]), 2) if result["trends"]["cfo_to_ni_trend"] else 0,
            "periods_with_poor_conversion": sum(1 for r in result["trends"]["cfo_to_ni_trend"] if r < 0.8),
            "interpretation": "CFO should be >= Net Income for high-quality earnings. Persistent divergence suggests earnings manipulation via accruals."
        }
    }

def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "Usage: revenue_quality.py <command> <ticker>",
            "commands": ["analyze", "dso-trends", "channel-stuffing", "cash-flow-divergence"]
        }))
        sys.exit(1)
    
    command = sys.argv[1]
    ticker = sys.argv[2].upper()
    
    if command in ["analyze", "revenue-quality"]:
        result = analyze_revenue_quality(ticker)
    elif command == "dso-trends":
        result = dso_trends(ticker)
    elif command == "channel-stuffing":
        result = channel_stuffing_detector(ticker)
    elif command == "cash-flow-divergence":
        result = cash_flow_vs_earnings(ticker)
    else:
        result = {
            "error": f"Unknown command: {command}",
            "available": ["analyze", "dso-trends", "channel-stuffing", "cash-flow-divergence"]
        }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

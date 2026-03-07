#!/usr/bin/env python3
"""
FRED API — Fixed Income & Credit Markets Module

Specialized module for fixed income and credit market data from FRED.
Complements fred_enhanced.py with focus on:
- Corporate bond spreads (ICE BofA indices)
- Credit default indicators
- Commercial paper rates  
- Detailed mortgage metrics
- Swap rates
- Loan officer survey data

Source: https://fred.stlouisfed.org/docs/api/fred.html
Category: Fixed Income & Credit
Free tier: True (requires FRED_API_KEY env var for higher limits)
Author: QuantClaw Data NightBuilder
Phase: 105
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# FRED API Configuration
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# ========== FIXED INCOME & CREDIT SERIES REGISTRY ==========

FRED_CREDIT_SERIES = {
    # ===== CORPORATE BOND SPREADS (ICE BofA Indices) =====
    'CORPORATE_SPREADS': {
        'BAMLC0A0CM': 'ICE BofA US Corporate Master Option-Adjusted Spread',
        'BAMLH0A0HYM2': 'ICE BofA US High Yield Master II Option-Adjusted Spread',
        'BAMLC0A1CAAAEY': 'ICE BofA AAA US Corporate Index Effective Yield',
        'BAMLC0A2CAAEY': 'ICE BofA AA US Corporate Index Effective Yield',
        'BAMLC0A3CAEY': 'ICE BofA A US Corporate Index Effective Yield',
        'BAMLC0A4CBBBEY': 'ICE BofA BBB US Corporate Index Effective Yield',
        'BAMLC1A0C13YEY': 'ICE BofA 1-3 Year US Corporate Index Effective Yield',
        'BAMLC2A0C35YEY': 'ICE BofA 3-5 Year US Corporate Index Effective Yield',
        'BAMLC4A0C710YEY': 'ICE BofA 7-10 Year US Corporate Index Effective Yield',
        'BAMLC7A0C1015YEY': 'ICE BofA 10-15 Year US Corporate Index Effective Yield',
        'BAMLH0A1HYBB': 'ICE BofA BB US High Yield Index Option-Adjusted Spread',
        'BAMLH0A2HYB': 'ICE BofA Single-B US High Yield Index Option-Adjusted Spread',
        'BAMLH0A3HYC': 'ICE BofA CCC & Lower US High Yield Index Option-Adjusted Spread',
    },
    
    # ===== SWAP RATES =====
    'SWAP_RATES': {
        'DSWP1': '1-Year Interest Rate Swap',
        'DSWP2': '2-Year Interest Rate Swap',
        'DSWP5': '5-Year Interest Rate Swap',
        'DSWP10': '10-Year Interest Rate Swap',
        'DSWP30': '30-Year Interest Rate Swap',
    },
    
    # ===== COMMERCIAL PAPER RATES =====
    'COMMERCIAL_PAPER': {
        'DCPF3M': '3-Month AA Financial Commercial Paper Rate',
        'DCPN3M': '3-Month AA Nonfinancial Commercial Paper Rate',
        'RIFLGFCM03_N_B': '3-Month Commercial Paper Rate',
        'RIFLGFCM06_N_B': '6-Month Commercial Paper Rate',
        'CPFF': 'Commercial Paper Outstanding',
    },
    
    # ===== MORTGAGE METRICS =====
    'MORTGAGE_METRICS': {
        'MORTGAGE30US': '30-Year Fixed Rate Mortgage Average',
        'MORTGAGE15US': '15-Year Fixed Rate Mortgage Average',
        'MORTGAGE5US': '5/1-Year Adjustable Rate Mortgage Average',
        'MORTG': 'Mortgage Debt Outstanding',
        'MBST': 'Mortgage-Backed Securities Held by Federal Reserve',
        'MDSP': 'Mortgage Debt Service Payments as % of Disposable Income',
        'HNOREMQ027S': 'Home Mortgage Debt Outstanding',
        'FDHBPIN': 'Federal Debt Held by Federal Reserve Banks',
    },
    
    # ===== CREDIT DEFAULT & RISK =====
    'CREDIT_RISK': {
        'BAMLC0A0CMEY': 'ICE BofA US Corporate Master Effective Yield',
        'BAMLH0A0HYM2EY': 'ICE BofA US High Yield Master II Effective Yield',
        'TERMCBCCALLNS': 'Bank Credit of All Commercial Banks',
        'TOTBKCR': 'Total Bank Credit at All Commercial Banks',
        'DRSFRMACBS': 'Delinquency Rate on Single-Family Residential Mortgages',
        'DRCCLACBS': 'Delinquency Rate on Credit Card Loans at All Commercial Banks',
        'DRCLACBS': 'Delinquency Rate on Consumer Loans at All Commercial Banks',
        'DRALACBS': 'Delinquency Rate on All Loans at All Commercial Banks',
    },
    
    # ===== LOAN OFFICER SURVEY (SLOOS) =====
    'LOAN_OFFICER_SURVEY': {
        'DRTSCLCC': 'Net % of Banks Tightening Standards for Commercial & Industrial Loans',
        'DRTSCILM': 'Net % of Banks Tightening Standards for C&I Loans to Large & Medium Firms',
        'DRTSCIS': 'Net % of Banks Tightening Standards for C&I Loans to Small Firms',
        'DRTSSP': 'Net % of Banks Tightening Standards for Credit Card Loans',
        'DRSDCIS': 'Delinquency Rate on Single-Family Residential Mortgages',
        'STDSLAMB': 'Net % of Banks Tightening Standards for Prime Mortgage Loans',
    },
    
    # ===== FEDERAL FUNDS & POLICY RATES =====
    'POLICY_RATES': {
        'DFF': 'Federal Funds Effective Rate',
        'DFEDTARU': 'Federal Funds Target Range - Upper Limit',
        'DFEDTARL': 'Federal Funds Target Range - Lower Limit',
        'IOER': 'Interest Rate on Excess Reserves',
        'IORB': 'Interest Rate on Reserve Balances',
        'OBFR': 'Overnight Bank Funding Rate',
        'SOFR': 'Secured Overnight Financing Rate',
    },
}


def get_fred_series(
    series_id: str,
    lookback_days: int = 365,
    api_key: Optional[str] = None
) -> Dict:
    """
    Fetch single FRED time series (helper function)
    
    Args:
        series_id: FRED series identifier (e.g., 'BAMLC0A0CM')
        lookback_days: Number of days of history (default 365)
        api_key: Optional FRED API key for higher rate limits
    
    Returns:
        Dict with series data, latest value, and changes
    """
    try:
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            "series_id": series_id,
            "file_type": "json",
            "observation_start": (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d"),
        }
        
        if api_key or FRED_API_KEY:
            params["api_key"] = api_key or FRED_API_KEY
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if "observations" not in data:
            return {
                "success": False,
                "error": "No observations in response",
                "series_id": series_id
            }
        
        # Filter out missing values (".")
        obs = [o for o in data["observations"] if o["value"] != "."]
        
        if not obs:
            return {
                "success": False,
                "error": "No valid observations found",
                "series_id": series_id
            }
        
        latest = obs[-1]
        latest_val = float(latest["value"])
        
        # Calculate changes
        changes = {}
        if len(obs) >= 2:
            prev_val = float(obs[-2]["value"])
            changes["period_change"] = latest_val - prev_val
            changes["period_change_pct"] = ((latest_val - prev_val) / prev_val * 100) if prev_val != 0 else 0
        
        if len(obs) >= 30:  # ~1 month
            month_ago = float(obs[-30]["value"])
            changes["month_change"] = latest_val - month_ago
            changes["month_change_pct"] = ((latest_val - month_ago) / month_ago * 100) if month_ago != 0 else 0
        
        if len(obs) >= 90:  # ~3 months
            quarter_ago = float(obs[-90]["value"])
            changes["quarter_change"] = latest_val - quarter_ago
            changes["quarter_change_pct"] = ((latest_val - quarter_ago) / quarter_ago * 100) if quarter_ago != 0 else 0
        
        # Year-over-year
        year_ago_idx = min(len(obs) - 1, 252)  # ~252 trading days
        if year_ago_idx > 0:
            year_ago = float(obs[-year_ago_idx]["value"])
            changes["yoy_change"] = latest_val - year_ago
            changes["yoy_change_pct"] = ((latest_val - year_ago) / year_ago * 100) if year_ago != 0 else 0
        
        return {
            "success": True,
            "series_id": series_id,
            "latest_value": latest_val,
            "latest_date": latest["date"],
            "changes": changes,
            "observations": [{"date": o["date"], "value": float(o["value"])} for o in obs[-90:]],
            "count": len(obs)
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "series_id": series_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "series_id": series_id
        }


def get_corporate_spreads(api_key: Optional[str] = None) -> Dict:
    """
    Get corporate bond spreads across ratings and maturities
    Includes ICE BofA Investment Grade and High Yield indices
    
    Returns:
        Dict with spreads by rating (AAA to CCC), yields, and risk indicators
    """
    spreads = FRED_CREDIT_SERIES['CORPORATE_SPREADS']
    results = {}
    
    for series_id, name in spreads.items():
        data = get_fred_series(series_id, lookback_days=90, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'month_change': data['changes'].get('month_change', 0),
                'month_change_pct': data['changes'].get('month_change_pct', 0)
            }
    
    # Analyze credit risk trends
    risk_indicators = []
    if 'BAMLC0A0CM' in results and 'BAMLH0A0HYM2' in results:
        ig_spread = results['BAMLC0A0CM']['value']
        hy_spread = results['BAMLH0A0HYM2']['value']
        
        if ig_spread > 200:  # 200 bps
            risk_indicators.append('Elevated Investment Grade spreads (>200bps)')
        if hy_spread > 500:  # 500 bps
            risk_indicators.append('Elevated High Yield spreads (>500bps)')
        
        # Spread widening = credit concerns
        if results['BAMLC0A0CM']['month_change'] > 20:
            risk_indicators.append('IG spreads widening rapidly')
        if results['BAMLH0A0HYM2']['month_change'] > 50:
            risk_indicators.append('HY spreads widening rapidly')
    
    return {
        'success': True,
        'corporate_spreads': results,
        'risk_indicators': risk_indicators if risk_indicators else ['Spreads stable'],
        'timestamp': datetime.now().isoformat()
    }


def get_commercial_paper_rates(api_key: Optional[str] = None) -> Dict:
    """
    Get commercial paper rates (3M, 6M financial and non-financial)
    
    Returns:
        Dict with CP rates and outstanding volumes
    """
    cp_series = FRED_CREDIT_SERIES['COMMERCIAL_PAPER']
    results = {}
    
    for series_id, name in cp_series.items():
        data = get_fred_series(series_id, lookback_days=90, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'month_change': data['changes'].get('month_change', 0)
            }
    
    # Compare financial vs non-financial CP
    analysis = []
    if 'DCPF3M' in results and 'DCPN3M' in results:
        financial_rate = results['DCPF3M']['value']
        nonfinancial_rate = results['DCPN3M']['value']
        spread = financial_rate - nonfinancial_rate
        
        analysis.append({
            'metric': 'Financial vs Non-Financial CP Spread',
            'spread_bps': round(spread * 100, 2),
            'interpretation': 'Financial stress' if spread > 0.5 else 'Normal conditions'
        })
    
    return {
        'success': True,
        'commercial_paper': results,
        'analysis': analysis,
        'timestamp': datetime.now().isoformat()
    }


def get_mortgage_metrics(api_key: Optional[str] = None) -> Dict:
    """
    Get detailed mortgage market metrics
    Includes rates, outstanding debt, Fed MBS holdings, and delinquencies
    
    Returns:
        Dict with mortgage rates, debt levels, and housing finance metrics
    """
    mortgage_series = FRED_CREDIT_SERIES['MORTGAGE_METRICS']
    results = {}
    
    for series_id, name in mortgage_series.items():
        data = get_fred_series(series_id, lookback_days=365, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'yoy_change': data['changes'].get('yoy_change', 0),
                'yoy_change_pct': data['changes'].get('yoy_change_pct', 0)
            }
    
    # Calculate mortgage affordability indicators
    insights = []
    if 'MORTGAGE30US' in results:
        rate_30y = results['MORTGAGE30US']['value']
        if rate_30y > 7.0:
            insights.append('30Y mortgage rates above 7% - affordability stress')
        elif rate_30y < 4.0:
            insights.append('30Y mortgage rates below 4% - favorable refinancing conditions')
    
    if 'MBST' in results:
        fed_mbs = results['MBST']['value']
        insights.append(f'Fed MBS holdings: ${fed_mbs:.0f}B')
    
    return {
        'success': True,
        'mortgage_metrics': results,
        'insights': insights,
        'timestamp': datetime.now().isoformat()
    }


def get_swap_rates(api_key: Optional[str] = None) -> Dict:
    """
    Get interest rate swap rates across maturities (1Y, 2Y, 5Y, 10Y, 30Y)
    
    Returns:
        Dict with swap curve and spreads to Treasuries
    """
    swap_series = FRED_CREDIT_SERIES['SWAP_RATES']
    results = {}
    
    for series_id, name in swap_series.items():
        data = get_fred_series(series_id, lookback_days=90, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'month_change': data['changes'].get('month_change', 0)
            }
    
    # Calculate swap spreads (would need Treasury data from fred_enhanced for full calc)
    swap_curve = []
    for maturity in ['1', '2', '5', '10', '30']:
        key = f'DSWP{maturity}'
        if key in results:
            swap_curve.append({
                'maturity': f'{maturity}Y',
                'rate': results[key]['value'],
                'change_1m': results[key]['month_change']
            })
    
    return {
        'success': True,
        'swap_rates': results,
        'swap_curve': swap_curve,
        'timestamp': datetime.now().isoformat()
    }


def get_credit_risk_indicators(api_key: Optional[str] = None) -> Dict:
    """
    Get credit risk and delinquency metrics
    Includes bank credit, delinquency rates across loan types
    
    Returns:
        Dict with credit quality indicators and delinquency trends
    """
    risk_series = FRED_CREDIT_SERIES['CREDIT_RISK']
    results = {}
    
    for series_id, name in risk_series.items():
        data = get_fred_series(series_id, lookback_days=365, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'yoy_change': data['changes'].get('yoy_change', 0)
            }
    
    # Assess credit quality
    quality_assessment = []
    
    delinquency_series = ['DRSFRMACBS', 'DRCCLACBS', 'DRCLACBS', 'DRALACBS']
    for series_id in delinquency_series:
        if series_id in results:
            rate = results[series_id]['value']
            name = results[series_id]['name']
            if rate > 3.0:
                quality_assessment.append(f'Elevated delinquency: {name} at {rate:.2f}%')
    
    if not quality_assessment:
        quality_assessment.append('Delinquency rates normal across loan categories')
    
    return {
        'success': True,
        'credit_risk': results,
        'quality_assessment': quality_assessment,
        'timestamp': datetime.now().isoformat()
    }


def get_loan_officer_survey(api_key: Optional[str] = None) -> Dict:
    """
    Get Senior Loan Officer Opinion Survey (SLOOS) data
    Net % of banks tightening/easing lending standards
    
    Returns:
        Dict with lending standards trends across loan types
    """
    sloos_series = FRED_CREDIT_SERIES['LOAN_OFFICER_SURVEY']
    results = {}
    
    for series_id, name in sloos_series.items():
        data = get_fred_series(series_id, lookback_days=365, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'quarter_change': data['changes'].get('quarter_change', 0)
            }
    
    # Interpret lending standards
    lending_conditions = []
    
    tightening_series = ['DRTSCLCC', 'DRTSCILM', 'DRTSCIS', 'DRTSSP']
    for series_id in tightening_series:
        if series_id in results:
            net_pct = results[series_id]['value']
            name = results[series_id]['name']
            
            if net_pct > 20:
                lending_conditions.append(f'Significant tightening: {name.split("for")[-1]}')
            elif net_pct < -20:
                lending_conditions.append(f'Easing standards: {name.split("for")[-1]}')
    
    if not lending_conditions:
        lending_conditions.append('Lending standards stable')
    
    return {
        'success': True,
        'loan_officer_survey': results,
        'lending_conditions': lending_conditions,
        'timestamp': datetime.now().isoformat()
    }


def get_policy_rates(api_key: Optional[str] = None) -> Dict:
    """
    Get Federal Reserve policy rates
    Includes Fed Funds, IOER, IORB, SOFR, OBFR
    
    Returns:
        Dict with policy rate levels and targets
    """
    policy_series = FRED_CREDIT_SERIES['POLICY_RATES']
    results = {}
    
    for series_id, name in policy_series.items():
        data = get_fred_series(series_id, lookback_days=90, api_key=api_key)
        if data['success']:
            results[series_id] = {
                'name': name,
                'value': data['latest_value'],
                'date': data['latest_date'],
                'month_change': data['changes'].get('month_change', 0)
            }
    
    # Calculate effective target rate and compare
    policy_insights = []
    
    if 'DFEDTARU' in results and 'DFEDTARL' in results:
        upper = results['DFEDTARU']['value']
        lower = results['DFEDTARL']['value']
        midpoint = (upper + lower) / 2
        policy_insights.append(f'Fed Funds Target Range: {lower:.2f}% - {upper:.2f}% (midpoint {midpoint:.2f}%)')
    
    if 'DFF' in results and 'SOFR' in results:
        dff = results['DFF']['value']
        sofr = results['SOFR']['value']
        spread = dff - sofr
        policy_insights.append(f'Fed Funds vs SOFR spread: {spread:.2f}bps')
    
    return {
        'success': True,
        'policy_rates': results,
        'policy_insights': policy_insights,
        'timestamp': datetime.now().isoformat()
    }


def get_credit_markets_snapshot(api_key: Optional[str] = None) -> Dict:
    """
    Get comprehensive fixed income & credit markets snapshot
    
    Returns:
        Dict with key metrics across all credit categories
    """
    snapshot = {}
    
    # Key metrics from each category
    key_series = {
        'IG Corporate Spread': 'BAMLC0A0CM',
        'HY Corporate Spread': 'BAMLH0A0HYM2',
        '30Y Mortgage Rate': 'MORTGAGE30US',
        '3M Commercial Paper': 'DCPF3M',
        '10Y Swap Rate': 'DSWP10',
        'Fed Funds Rate': 'DFF',
        'SOFR': 'SOFR',
        'Credit Card Delinquency': 'DRCCLACBS',
        'All Loans Delinquency': 'DRALACBS',
    }
    
    for name, series_id in key_series.items():
        data = get_fred_series(series_id, lookback_days=90, api_key=api_key)
        if data['success']:
            snapshot[name] = {
                'value': data['latest_value'],
                'date': data['latest_date'],
                'month_change': data['changes'].get('month_change', 0)
            }
    
    return {
        'success': True,
        'credit_snapshot': snapshot,
        'timestamp': datetime.now().isoformat(),
        'source': 'FRED API - Fixed Income & Credit'
    }


def list_all_series() -> Dict:
    """
    List all available series in this module with counts by category
    
    Returns:
        Dict with all series organized by category
    """
    all_series = {}
    total_count = 0
    
    for category, series_dict in FRED_CREDIT_SERIES.items():
        all_series[category] = {
            'count': len(series_dict),
            'series': [{'id': sid, 'name': name} for sid, name in series_dict.items()]
        }
        total_count += len(series_dict)
    
    return {
        'success': True,
        'total_series': total_count,
        'categories': all_series,
        'module': 'fred_api - Fixed Income & Credit'
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("FRED API - Fixed Income & Credit Markets")
    print("=" * 60)
    
    # Show available series
    series_list = list_all_series()
    print(f"\nTotal Series: {series_list['total_series']}")
    print("\nCategories:")
    for cat, info in series_list['categories'].items():
        print(f"  {cat}: {info['count']} series")
    
    print("\n" + json.dumps(series_list, indent=2))

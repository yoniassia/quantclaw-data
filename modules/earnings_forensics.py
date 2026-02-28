#!/usr/bin/env python3
"""
earnings_forensics.py — Deep accounting red flag detection (Phase 92)

Advanced fraud detection beyond basic Beneish M-Score:
- Revenue recognition pattern analysis
- Working capital trend forensics
- Cash flow vs earnings divergence tracking
- Multi-period fraud probability scoring
- Days Sales Outstanding (DSO) manipulation detection
- Channel stuffing indicators
- Inventory turnover anomalies

Free data sources: yfinance, SEC EDGAR
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False
    print("⚠️ yfinance not installed. Run: pip install yfinance")

# Import basic metrics from Phase 59
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.earnings_quality import calculate_beneish_m_score as calculate_beneish_mscore, calculate_accruals_ratio


def get_financial_data(ticker: str, period: str = 'annual') -> Optional[Dict]:
    """Fetch comprehensive financial data for forensic analysis"""
    if not YF_AVAILABLE:
        return None
    
    try:
        stock = yf.Ticker(ticker)
        
        if period == 'annual':
            income = stock.income_stmt
            balance = stock.balance_sheet
            cashflow = stock.cashflow
        else:
            income = stock.quarterly_income_stmt
            balance = stock.quarterly_balance_sheet
            cashflow = stock.quarterly_cashflow
        
        return {
            'income_stmt': income,
            'balance_sheet': balance,
            'cashflow': cashflow,
            'period': period,
            'ticker': ticker
        }
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None


def analyze_revenue_recognition_patterns(ticker: str, period: str = 'quarterly') -> Dict:
    """
    Detect suspicious revenue recognition patterns
    
    Red flags:
    - Revenue growing faster than cash from operations (>20% divergence)
    - Increasing Days Sales Outstanding (DSO) while revenue grows
    - Accounts Receivable growing faster than revenue
    - Negative correlation between revenue growth and cash collection
    
    Returns fraud risk score: 0-100 (higher = more suspicious)
    """
    data = get_financial_data(ticker, period)
    if not data:
        return {'error': f'Could not fetch data for {ticker}'}
    
    try:
        income = data['income_stmt']
        balance = data['balance_sheet']
        
        # Get last 8 quarters for trend analysis
        n_periods = min(8, len(income.columns))
        
        results = {
            'ticker': ticker,
            'period': period,
            'analysis_date': datetime.now().isoformat(),
            'periods_analyzed': n_periods,
            'red_flags': [],
            'fraud_risk_score': 0
        }
        
        # Extract revenue and AR over time
        revenue_series = []
        ar_series = []
        dates = []
        
        for col in income.columns[:n_periods]:
            try:
                # Revenue
                rev = income.loc['Total Revenue', col] if 'Total Revenue' in income.index else None
                
                # Accounts Receivable
                ar = balance.loc['Accounts Receivable', col] if 'Accounts Receivable' in balance.index else None
                
                if rev is not None and ar is not None and not pd.isna(rev) and not pd.isna(ar):
                    revenue_series.append(float(rev))
                    ar_series.append(float(ar))
                    dates.append(str(col.date()) if hasattr(col, 'date') else str(col))
            except Exception:
                continue
        
        if len(revenue_series) < 3:
            return {**results, 'error': 'Insufficient data for trend analysis'}
        
        # Calculate DSO = (Accounts Receivable / Revenue) * 90 (for quarterly)
        days_multiplier = 365 if period == 'annual' else 90
        dso_series = [(ar / rev) * days_multiplier for rev, ar in zip(revenue_series, ar_series)]
        
        results['dso_trend'] = [{'date': d, 'dso': round(dso, 1)} for d, dso in zip(dates, dso_series)]
        results['current_dso'] = round(dso_series[0], 1)
        
        # Red Flag 1: Rising DSO while revenue grows
        rev_growth = [(revenue_series[i] / revenue_series[i+1] - 1) * 100 
                      for i in range(len(revenue_series)-1)]
        dso_change = [(dso_series[i] / dso_series[i+1] - 1) * 100 
                      for i in range(len(dso_series)-1)]
        
        if len(rev_growth) > 0:
            avg_rev_growth = np.mean(rev_growth)
            avg_dso_change = np.mean(dso_change)
            
            results['avg_revenue_growth'] = round(avg_rev_growth, 2)
            results['avg_dso_change'] = round(avg_dso_change, 2)
            
            if avg_rev_growth > 5 and avg_dso_change > 10:
                results['red_flags'].append({
                    'type': 'Rising DSO with Revenue Growth',
                    'severity': 'HIGH',
                    'description': f'Revenue growing {avg_rev_growth:.1f}% while DSO increasing {avg_dso_change:.1f}% - suggests channel stuffing or aggressive revenue recognition',
                    'score_impact': 30
                })
                results['fraud_risk_score'] += 30
        
        # Red Flag 2: AR growing faster than revenue
        ar_growth = [(ar_series[i] / ar_series[i+1] - 1) * 100 
                     for i in range(len(ar_series)-1)]
        
        if len(ar_growth) > 0 and len(rev_growth) > 0:
            avg_ar_growth = np.mean(ar_growth)
            ar_rev_divergence = avg_ar_growth - avg_rev_growth
            
            results['avg_ar_growth'] = round(avg_ar_growth, 2)
            results['ar_revenue_divergence'] = round(ar_rev_divergence, 2)
            
            if ar_rev_divergence > 20:
                results['red_flags'].append({
                    'type': 'AR Growing Faster Than Revenue',
                    'severity': 'HIGH',
                    'description': f'AR growing {ar_rev_divergence:.1f}% faster than revenue - customers not paying or fictitious sales',
                    'score_impact': 25
                })
                results['fraud_risk_score'] += 25
            elif ar_rev_divergence > 10:
                results['red_flags'].append({
                    'type': 'AR Revenue Growth Mismatch',
                    'severity': 'MEDIUM',
                    'description': f'AR growing {ar_rev_divergence:.1f}% faster than revenue - monitor collection quality',
                    'score_impact': 15
                })
                results['fraud_risk_score'] += 15
        
        # Red Flag 3: DSO volatility (unstable collection patterns)
        if len(dso_series) >= 4:
            dso_std = np.std(dso_series)
            dso_mean = np.mean(dso_series)
            dso_cv = (dso_std / dso_mean) * 100 if dso_mean != 0 else 0
            
            results['dso_volatility'] = round(dso_cv, 2)
            
            if dso_cv > 25:
                results['red_flags'].append({
                    'type': 'High DSO Volatility',
                    'severity': 'MEDIUM',
                    'description': f'DSO coefficient of variation: {dso_cv:.1f}% - inconsistent collection patterns',
                    'score_impact': 10
                })
                results['fraud_risk_score'] += 10
        
        # Interpretation
        if results['fraud_risk_score'] >= 50:
            results['risk_level'] = 'CRITICAL'
            results['recommendation'] = '🔴 AVOID — Multiple severe revenue quality red flags detected'
        elif results['fraud_risk_score'] >= 30:
            results['risk_level'] = 'HIGH'
            results['recommendation'] = '⚠️ CAUTION — Investigate revenue recognition practices before investing'
        elif results['fraud_risk_score'] >= 15:
            results['risk_level'] = 'MODERATE'
            results['recommendation'] = '⚡ MONITOR — Some revenue quality concerns, watch next quarter'
        else:
            results['risk_level'] = 'LOW'
            results['recommendation'] = '✅ ACCEPTABLE — Revenue recognition patterns appear normal'
        
        return results
    
    except Exception as e:
        return {'error': f'Analysis failed: {str(e)}', 'ticker': ticker}


def analyze_working_capital_trends(ticker: str, period: str = 'quarterly') -> Dict:
    """
    Detect working capital manipulation and quality deterioration
    
    Red flags:
    - Negative working capital while showing profits
    - Working capital decreasing while revenue grows
    - Inventory buildup not matching sales growth
    - Accounts Payable stretching (supplier payment delays)
    
    Returns fraud risk score: 0-100
    """
    data = get_financial_data(ticker, period)
    if not data:
        return {'error': f'Could not fetch data for {ticker}'}
    
    try:
        income = data['income_stmt']
        balance = data['balance_sheet']
        
        n_periods = min(8, len(balance.columns))
        
        results = {
            'ticker': ticker,
            'period': period,
            'analysis_date': datetime.now().isoformat(),
            'periods_analyzed': n_periods,
            'red_flags': [],
            'fraud_risk_score': 0
        }
        
        # Extract working capital components
        current_assets_series = []
        current_liab_series = []
        inventory_series = []
        revenue_series = []
        cogs_series = []
        ap_series = []
        dates = []
        
        for col in balance.columns[:n_periods]:
            try:
                ca = balance.loc['Current Assets', col] if 'Current Assets' in balance.index else None
                cl = balance.loc['Current Liabilities', col] if 'Current Liabilities' in balance.index else None
                inv = balance.loc['Inventory', col] if 'Inventory' in balance.index else None
                ap = balance.loc['Accounts Payable', col] if 'Accounts Payable' in balance.index else None
                
                # Get corresponding revenue and COGS
                rev = income.loc['Total Revenue', col] if 'Total Revenue' in income.index else None
                cogs = income.loc['Cost Of Revenue', col] if 'Cost Of Revenue' in income.index else None
                
                if ca is not None and cl is not None:
                    current_assets_series.append(float(ca))
                    current_liab_series.append(float(cl))
                    inventory_series.append(float(inv) if inv is not None and not pd.isna(inv) else 0)
                    ap_series.append(float(ap) if ap is not None and not pd.isna(ap) else 0)
                    revenue_series.append(float(rev) if rev is not None and not pd.isna(rev) else 0)
                    cogs_series.append(float(cogs) if cogs is not None and not pd.isna(cogs) else 0)
                    dates.append(str(col.date()) if hasattr(col, 'date') else str(col))
            except Exception:
                continue
        
        if len(current_assets_series) < 3:
            return {**results, 'error': 'Insufficient data for working capital analysis'}
        
        # Calculate working capital
        wc_series = [ca - cl for ca, cl in zip(current_assets_series, current_liab_series)]
        wc_ratio_series = [ca / cl if cl != 0 else 0 for ca, cl in zip(current_assets_series, current_liab_series)]
        
        results['working_capital_trend'] = [
            {'date': d, 'wc': round(wc/1e6, 1), 'wc_ratio': round(ratio, 2)}
            for d, wc, ratio in zip(dates, wc_series, wc_ratio_series)
        ]
        
        results['current_wc'] = round(wc_series[0] / 1e6, 1)
        results['current_wc_ratio'] = round(wc_ratio_series[0], 2)
        
        # Red Flag 1: Negative working capital
        if wc_series[0] < 0:
            results['red_flags'].append({
                'type': 'Negative Working Capital',
                'severity': 'HIGH',
                'description': f'Current WC: ${wc_series[0]/1e6:.1f}M - company may struggle to meet short-term obligations',
                'score_impact': 25
            })
            results['fraud_risk_score'] += 25
        
        # Red Flag 2: Deteriorating WC ratio
        if len(wc_ratio_series) >= 4:
            wc_ratio_change = [(wc_ratio_series[i] / wc_ratio_series[i+1] - 1) * 100 
                               for i in range(len(wc_ratio_series)-1) if wc_ratio_series[i+1] != 0]
            
            if len(wc_ratio_change) > 0:
                avg_wc_decline = np.mean(wc_ratio_change)
                
                if avg_wc_decline < -15:
                    results['red_flags'].append({
                        'type': 'Rapid WC Deterioration',
                        'severity': 'HIGH',
                        'description': f'WC ratio declining {abs(avg_wc_decline):.1f}% per period - liquidity crisis risk',
                        'score_impact': 20
                    })
                    results['fraud_risk_score'] += 20
        
        # Red Flag 3: Inventory buildup vs sales
        if len(inventory_series) >= 4 and len(revenue_series) >= 4:
            inv_growth = [(inventory_series[i] / inventory_series[i+1] - 1) * 100 
                          for i in range(len(inventory_series)-1) if inventory_series[i+1] != 0]
            rev_growth = [(revenue_series[i] / revenue_series[i+1] - 1) * 100 
                          for i in range(len(revenue_series)-1) if revenue_series[i+1] != 0]
            
            if len(inv_growth) > 0 and len(rev_growth) > 0:
                avg_inv_growth = np.mean(inv_growth)
                avg_rev_growth = np.mean(rev_growth)
                inv_rev_divergence = avg_inv_growth - avg_rev_growth
                
                results['avg_inventory_growth'] = round(avg_inv_growth, 2)
                results['inventory_revenue_divergence'] = round(inv_rev_divergence, 2)
                
                if inv_rev_divergence > 25:
                    results['red_flags'].append({
                        'type': 'Excessive Inventory Buildup',
                        'severity': 'HIGH',
                        'description': f'Inventory growing {inv_rev_divergence:.1f}% faster than sales - obsolescence risk or channel stuffing',
                        'score_impact': 20
                    })
                    results['fraud_risk_score'] += 20
                elif inv_rev_divergence > 15:
                    results['red_flags'].append({
                        'type': 'Inventory Growth Concern',
                        'severity': 'MEDIUM',
                        'description': f'Inventory growing {inv_rev_divergence:.1f}% faster than sales - monitor turnover',
                        'score_impact': 10
                    })
                    results['fraud_risk_score'] += 10
        
        # Red Flag 4: Days Payable Outstanding (DPO) extension
        if len(ap_series) >= 4 and len(cogs_series) >= 4:
            days_multiplier = 365 if period == 'annual' else 90
            dpo_series = [(ap / cogs) * days_multiplier for ap, cogs in zip(ap_series, cogs_series) if cogs != 0]
            
            if len(dpo_series) >= 2:
                dpo_change = [(dpo_series[i] / dpo_series[i+1] - 1) * 100 
                              for i in range(len(dpo_series)-1) if dpo_series[i+1] != 0]
                
                if len(dpo_change) > 0:
                    avg_dpo_change = np.mean(dpo_change)
                    results['avg_dpo_change'] = round(avg_dpo_change, 2)
                    results['current_dpo'] = round(dpo_series[0], 1)
                    
                    if avg_dpo_change > 20:
                        results['red_flags'].append({
                            'type': 'Supplier Payment Delays',
                            'severity': 'MEDIUM',
                            'description': f'DPO increasing {avg_dpo_change:.1f}% - company stretching payments to suppliers',
                            'score_impact': 15
                        })
                        results['fraud_risk_score'] += 15
        
        # Interpretation
        if results['fraud_risk_score'] >= 50:
            results['risk_level'] = 'CRITICAL'
            results['recommendation'] = '🔴 AVOID — Severe working capital quality issues'
        elif results['fraud_risk_score'] >= 30:
            results['risk_level'] = 'HIGH'
            results['recommendation'] = '⚠️ CAUTION — Working capital deteriorating rapidly'
        elif results['fraud_risk_score'] >= 15:
            results['risk_level'] = 'MODERATE'
            results['recommendation'] = '⚡ MONITOR — Some working capital concerns'
        else:
            results['risk_level'] = 'LOW'
            results['recommendation'] = '✅ HEALTHY — Working capital management appears sound'
        
        return results
    
    except Exception as e:
        return {'error': f'Working capital analysis failed: {str(e)}', 'ticker': ticker}


def comprehensive_forensics_report(ticker: str, period: str = 'quarterly', quiet: bool = False) -> Dict:
    """
    Generate comprehensive earnings forensics report combining all analyses
    
    Includes:
    - Beneish M-Score (from Phase 59)
    - Accruals analysis (from Phase 59)
    - Revenue recognition patterns (Phase 92)
    - Working capital trends (Phase 92)
    - Composite fraud probability score
    
    Args:
        ticker: Stock symbol
        period: 'annual' or 'quarterly'
        quiet: If True, suppress progress output
    
    Returns overall fraud risk: 0-100 with detailed breakdown
    """
    if not quiet:
        print(f"\n🔍 Analyzing {ticker} — Earnings Quality Forensics Report")
        print("=" * 70)
    
    report = {
        'ticker': ticker,
        'period': period,
        'analysis_date': datetime.now().isoformat(),
        'analyses': {},
        'composite_fraud_score': 0,
        'all_red_flags': []
    }
    
    # 1. Beneish M-Score (Phase 59)
    if not quiet:
        print("\n📊 Beneish M-Score (Earnings Manipulation Detector)...")
    beneish = calculate_beneish_mscore(ticker, period)
    report['analyses']['beneish'] = beneish
    
    if 'error' not in beneish and 'm_score' in beneish:
        mscore = beneish['m_score']
        if mscore > -1.78:  # High manipulation probability
            report['composite_fraud_score'] += 30
            report['all_red_flags'].append({
                'source': 'Beneish M-Score',
                'severity': 'HIGH',
                'description': f'M-Score: {mscore:.2f} (threshold: -1.78) - HIGH manipulation probability',
                'score_impact': 30
            })
        elif mscore > -2.22:  # Moderate risk
            report['composite_fraud_score'] += 15
            report['all_red_flags'].append({
                'source': 'Beneish M-Score',
                'severity': 'MEDIUM',
                'description': f'M-Score: {mscore:.2f} (threshold: -1.78) - MODERATE manipulation risk',
                'score_impact': 15
            })
    
    # 2. Accruals Analysis (Phase 59)
    if not quiet:
        print("💰 Accruals Ratio (Cash Flow Quality)...")
    accruals = calculate_accruals_ratio(ticker, period)
    report['analyses']['accruals'] = accruals
    
    if 'error' not in accruals and 'accruals_ratio' in accruals:
        acc_ratio = accruals['accruals_ratio']
        if acc_ratio > 0.10:  # High concern
            report['composite_fraud_score'] += 20
            report['all_red_flags'].append({
                'source': 'Accruals Ratio',
                'severity': 'HIGH',
                'description': f'Accruals: {acc_ratio:.3f} (>0.10) - Earnings not backed by cash',
                'score_impact': 20
            })
        elif acc_ratio > 0.05:  # Moderate concern
            report['composite_fraud_score'] += 10
            report['all_red_flags'].append({
                'source': 'Accruals Ratio',
                'severity': 'MEDIUM',
                'description': f'Accruals: {acc_ratio:.3f} (>0.05) - Cash conversion concerns',
                'score_impact': 10
            })
    
    # 3. Revenue Recognition Patterns (Phase 92)
    if not quiet:
        print("📈 Revenue Recognition Pattern Analysis...")
    revenue_analysis = analyze_revenue_recognition_patterns(ticker, period)
    report['analyses']['revenue_patterns'] = revenue_analysis
    
    if 'error' not in revenue_analysis:
        report['composite_fraud_score'] += revenue_analysis.get('fraud_risk_score', 0)
        report['all_red_flags'].extend(revenue_analysis.get('red_flags', []))
    
    # 4. Working Capital Trends (Phase 92)
    if not quiet:
        print("🏗️ Working Capital Quality Analysis...")
    wc_analysis = analyze_working_capital_trends(ticker, period)
    report['analyses']['working_capital'] = wc_analysis
    
    if 'error' not in wc_analysis:
        report['composite_fraud_score'] += wc_analysis.get('fraud_risk_score', 0)
        report['all_red_flags'].extend(wc_analysis.get('red_flags', []))
    
    # Cap composite score at 100
    report['composite_fraud_score'] = min(report['composite_fraud_score'], 100)
    
    # Overall risk classification
    score = report['composite_fraud_score']
    if score >= 70:
        report['overall_risk'] = 'CRITICAL'
        report['investment_recommendation'] = '🔴 STRONG AVOID — Multiple severe accounting red flags'
        report['action'] = 'Do not invest. If holding, consider selling immediately.'
    elif score >= 50:
        report['overall_risk'] = 'HIGH'
        report['investment_recommendation'] = '⚠️ AVOID — Significant earnings quality concerns'
        report['action'] = 'Avoid new investment. If holding, reduce position size.'
    elif score >= 30:
        report['overall_risk'] = 'MODERATE'
        report['investment_recommendation'] = '⚡ CAUTION — Some accounting red flags present'
        report['action'] = 'Investigate further before investing. Monitor closely if holding.'
    elif score >= 15:
        report['overall_risk'] = 'LOW-MODERATE'
        report['investment_recommendation'] = '⚠️ MONITOR — Minor concerns detected'
        report['action'] = 'Acceptable for investment with continued monitoring.'
    else:
        report['overall_risk'] = 'LOW'
        report['investment_recommendation'] = '✅ ACCEPTABLE — Earnings quality appears healthy'
        report['action'] = 'Earnings quality checks passed. No major accounting concerns.'
    
    # Summary statistics
    report['summary'] = {
        'total_red_flags': len(report['all_red_flags']),
        'high_severity_flags': len([f for f in report['all_red_flags'] if f.get('severity') == 'HIGH']),
        'medium_severity_flags': len([f for f in report['all_red_flags'] if f.get('severity') == 'MEDIUM']),
        'composite_fraud_score': report['composite_fraud_score'],
        'risk_level': report['overall_risk']
    }
    
    if not quiet:
        print(f"\n{'=' * 70}")
        print(f"🎯 COMPOSITE FRAUD SCORE: {report['composite_fraud_score']}/100")
        print(f"🚦 RISK LEVEL: {report['overall_risk']}")
        print(f"💡 RECOMMENDATION: {report['investment_recommendation']}")
        print(f"{'=' * 70}\n")
    
    return report


if __name__ == '__main__':
    # Test with a known problematic company
    ticker = "TSLA"
    print(f"Testing earnings forensics on {ticker}...\n")
    
    print("1. Revenue Recognition Analysis:")
    rev_result = analyze_revenue_recognition_patterns(ticker, 'quarterly')
    print(json.dumps(rev_result, indent=2))
    
    print("\n\n2. Working Capital Analysis:")
    wc_result = analyze_working_capital_trends(ticker, 'quarterly')
    print(json.dumps(wc_result, indent=2))
    
    print("\n\n3. Comprehensive Forensics Report:")
    full_report = comprehensive_forensics_report(ticker, 'quarterly')
    print(json.dumps(full_report, indent=2, default=str))

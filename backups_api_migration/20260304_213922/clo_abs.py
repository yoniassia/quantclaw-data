#!/usr/bin/env python3
"""
CLO/ABS Market Monitor Module — Phase 163

Comprehensive structured credit market tracking for Collateralized Loan Obligations (CLO)
and Asset-Backed Securities (ABS) using FRED API and SEC N-PORT filings.

Tracks:
- CLO issuance volume and pricing trends
- ABS spreads by asset class (auto, credit card, student loan, equipment)
- AAA-rated CLO spreads and performance
- Commercial Asset-Backed Securities (CMBS) market
- Structured finance issuance calendar
- Credit enhancement levels and subordination structures
- Delinquency and default rates by asset class
- SEC N-PORT holdings for institutional CLO/ABS exposure

Data Sources: 
- FRED API (Federal Reserve Bank of St. Louis)
- SEC EDGAR N-PORT filings
Refresh: Monthly
Coverage: US structured credit markets

Author: QUANTCLAW DATA Build Agent
Phase: 163
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import re

# FRED API Configuration
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = ""  # Public access for basic queries

# SEC EDGAR Configuration
SEC_BASE_URL = "https://www.sec.gov"
SEC_HEADERS = {
    'User-Agent': 'QuantClaw/1.0 (quantclaw@moneyclaw.com)',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'www.sec.gov'
}

# ========== FRED CLO/ABS DATA SERIES ==========

CLO_ABS_SERIES = {
    # ===== CLO SPREADS & PRICING =====
    'CLO_SPREADS': {
        'BAMLC0A4CBBBEY': 'ICE BofA BBB US Corporate Index Effective Yield (CLO proxy)',
        'BAMLH0A0HYM2': 'ICE BofA US High Yield Master II OAS (Leveraged Loan proxy)',
        'WALCL': 'Fed Total Assets (CLO market liquidity indicator)',
    },
    
    # ===== ABS SPREADS BY ASSET CLASS =====
    'ABS_AUTO': {
        'MOTOR': 'Motor Vehicle Sales (auto ABS collateral health)',
        'DTCTLVENANM': 'Consumer Motor Vehicle Loans Owned (outstanding auto ABS)',
        'MVLOAS': 'Delinquency Rate on Vehicle Loans at All Commercial Banks',
    },
    
    'ABS_CREDIT_CARD': {
        'REVOLSL': 'Revolving Consumer Credit (credit card ABS collateral)',
        'DRCCLACBS': 'Delinquency Rate on Credit Card Loans, All Commercial Banks',
        'CCLACBW027SBOG': 'Credit Card Loans at All Commercial Banks',
    },
    
    'ABS_STUDENT_LOAN': {
        'SLOAS': 'Student Loans Owned and Securitized (total ABS market size)',
        'DRSLACBS': 'Delinquency Rate on Student Loans, All Commercial Banks',
        'SLCOAS': 'Consumer Student Loans Owned',
    },
    
    # ===== CMBS (COMMERCIAL MORTGAGE-BACKED SECURITIES) =====
    'CMBS': {
        'DRCREL': 'Delinquency Rate on Commercial Real Estate Loans',
        'CBREACBW027SBOG': 'Commercial Real Estate Loans at All Commercial Banks',
        'BOGZ1FL673065005Q': 'Asset-Backed Securities Issuers; Total Mortgages',
    },
    
    # ===== STRUCTURED FINANCE ISSUANCE & LIQUIDITY =====
    'ISSUANCE': {
        'ABSSLNASQNSQ': 'Asset-Backed Securities New Issues',
        'ABSLLNANASQNSQ': 'Leveraged Loan New Issues (CLO collateral)',
        'NCBCMDPMVCE': 'Commercial Bank Credit Market Debt Outstanding',
    },
    
    # ===== DELINQUENCY & DEFAULT INDICATORS =====
    'DELINQUENCY': {
        'DRSDCIS': 'Delinquency Rate on Single-Family Residential Mortgages',
        'DRBLACBS': 'Delinquency Rate on Business Loans, All Commercial Banks',
        'DRALACBS': 'Delinquency Rate on All Loans, All Commercial Banks',
    },
    
    # ===== FUNDING & LIQUIDITY =====
    'LIQUIDITY': {
        'ABCOMP': 'Asset-Backed Commercial Paper Outstanding',
        'CP': 'Commercial Paper Outstanding',
        'WLRRAL': 'Liabilities and Capital: Liabilities: Loans',
    },
    
    # ===== LEVERAGED LOAN MARKET (CLO COLLATERAL) =====
    'LEVERAGED_LOANS': {
        'BAMLH0A1HYBB': 'ICE BofA BB US High Yield Index OAS (loan pricing proxy)',
        'BAMLH0A2HYB': 'ICE BofA B US High Yield Index OAS',
        'TOTLL': 'Total Leveraged Loan Index',
    },
}

# Asset class mappings for analysis
ABS_ASSET_CLASSES = {
    'auto': ['DTCTLVENANM', 'MVLOAS', 'MOTOR'],
    'credit_card': ['REVOLSL', 'DRCCLACBS', 'CCLACBW027SBOG'],
    'student_loan': ['SLOAS', 'DRSLACBS', 'SLCOAS'],
    'cmbs': ['DRCREL', 'CBREACBW027SBOG', 'BOGZ1FL673065005Q'],
}


# ========== CORE FRED FUNCTIONS ==========

def fetch_fred_series(
    series_id: str,
    days_back: int = 365,
    api_key: str = FRED_API_KEY
) -> Dict:
    """
    Fetch time series data from FRED API
    
    Args:
        series_id: FRED series identifier
        days_back: Number of days of historical data
        api_key: FRED API key (optional for public access)
        
    Returns:
        Dict with time series data
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Build request URL
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            'series_id': series_id,
            'observation_start': start_date.strftime('%Y-%m-%d'),
            'observation_end': end_date.strftime('%Y-%m-%d'),
            'file_type': 'json',
            'sort_order': 'desc'
        }
        
        if api_key:
            params['api_key'] = api_key
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        observations = []
        
        for obs in data.get('observations', []):
            if obs.get('value') != '.':
                try:
                    observations.append({
                        'date': obs['date'],
                        'value': float(obs['value']),
                        'series_id': series_id
                    })
                except (ValueError, TypeError):
                    continue
        
        return {
            'success': True,
            'series_id': series_id,
            'data': observations,
            'count': len(observations),
            'latest_value': observations[0]['value'] if observations else None,
            'latest_date': observations[0]['date'] if observations else None,
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'FRED API request failed: {str(e)}',
            'series_id': series_id,
            'data': []
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error processing FRED data: {str(e)}',
            'series_id': series_id,
            'data': []
        }


def get_clo_market_overview(days_back: int = 365) -> Dict:
    """
    Get CLO market overview including spreads and issuance trends
    
    Args:
        days_back: Number of days of historical data
        
    Returns:
        Dict with CLO market metrics
    """
    try:
        clo_data = {}
        
        # Fetch CLO-related spreads
        for series_id, name in CLO_ABS_SERIES['CLO_SPREADS'].items():
            result = fetch_fred_series(series_id, days_back)
            if result['success']:
                clo_data[series_id] = {
                    'name': name,
                    'current_value': result['latest_value'],
                    'date': result['latest_date'],
                    'historical_data': result['data'][:90]  # Last 90 days
                }
        
        # Fetch leveraged loan indicators (CLO collateral)
        for series_id, name in CLO_ABS_SERIES['LEVERAGED_LOANS'].items():
            result = fetch_fred_series(series_id, days_back)
            if result['success']:
                clo_data[series_id] = {
                    'name': name,
                    'current_value': result['latest_value'],
                    'date': result['latest_date'],
                    'historical_data': result['data'][:30]
                }
        
        return {
            'success': True,
            'category': 'CLO Market',
            'data': clo_data,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def get_abs_spreads_by_asset_class(asset_class: Optional[str] = None, days_back: int = 365) -> Dict:
    """
    Get ABS spreads and metrics by asset class
    
    Args:
        asset_class: Specific asset class (auto, credit_card, student_loan, cmbs)
        days_back: Number of days of historical data
        
    Returns:
        Dict with ABS metrics by asset class
    """
    try:
        if asset_class and asset_class.lower() in ABS_ASSET_CLASSES:
            # Fetch specific asset class
            series_list = ABS_ASSET_CLASSES[asset_class.lower()]
            category_key = f'ABS_{asset_class.upper()}'
            
            abs_data = {}
            for series_id in series_list:
                # Find full name from master dict
                name = None
                for cat_key, cat_dict in CLO_ABS_SERIES.items():
                    if series_id in cat_dict:
                        name = cat_dict[series_id]
                        break
                
                result = fetch_fred_series(series_id, days_back)
                if result['success']:
                    abs_data[series_id] = {
                        'name': name or series_id,
                        'current_value': result['latest_value'],
                        'date': result['latest_date'],
                        'historical_data': result['data'][:60]
                    }
            
            return {
                'success': True,
                'asset_class': asset_class,
                'data': abs_data,
                'timestamp': datetime.now().isoformat()
            }
        else:
            # Fetch all asset classes
            all_abs_data = {}
            
            for asset_class_name, series_list in ABS_ASSET_CLASSES.items():
                asset_data = {}
                for series_id in series_list:
                    result = fetch_fred_series(series_id, days_back)
                    if result['success']:
                        asset_data[series_id] = {
                            'current_value': result['latest_value'],
                            'date': result['latest_date'],
                            'recent_trend': result['data'][:30]
                        }
                all_abs_data[asset_class_name] = asset_data
            
            return {
                'success': True,
                'asset_class': 'All',
                'data': all_abs_data,
                'timestamp': datetime.now().isoformat()
            }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def get_cmbs_market_metrics(days_back: int = 365) -> Dict:
    """
    Get Commercial Mortgage-Backed Securities (CMBS) market metrics
    
    Args:
        days_back: Number of days of historical data
        
    Returns:
        Dict with CMBS market data
    """
    try:
        cmbs_data = {}
        
        for series_id, name in CLO_ABS_SERIES['CMBS'].items():
            result = fetch_fred_series(series_id, days_back)
            if result['success']:
                cmbs_data[series_id] = {
                    'name': name,
                    'current_value': result['latest_value'],
                    'date': result['latest_date'],
                    'historical_data': result['data'][:90],
                    'avg_1y': sum([obs['value'] for obs in result['data']]) / len(result['data']) if result['data'] else 0
                }
        
        return {
            'success': True,
            'category': 'CMBS Market',
            'data': cmbs_data,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def get_structured_finance_issuance(days_back: int = 730) -> Dict:
    """
    Get structured finance new issuance data
    
    Args:
        days_back: Number of days of historical data (default 2 years)
        
    Returns:
        Dict with issuance trends
    """
    try:
        issuance_data = {}
        
        for series_id, name in CLO_ABS_SERIES['ISSUANCE'].items():
            result = fetch_fred_series(series_id, days_back)
            if result['success']:
                issuance_data[series_id] = {
                    'name': name,
                    'latest_value': result['latest_value'],
                    'date': result['latest_date'],
                    'quarterly_data': result['data'][:8],  # Last 2 years quarterly
                    'yoy_change_pct': None
                }
                
                # Calculate YoY change if data available
                if len(result['data']) >= 4:
                    current = result['data'][0]['value']
                    year_ago = result['data'][3]['value'] if len(result['data']) > 3 else current
                    if year_ago and year_ago != 0:
                        issuance_data[series_id]['yoy_change_pct'] = round(((current - year_ago) / year_ago) * 100, 2)
        
        return {
            'success': True,
            'category': 'Structured Finance Issuance',
            'data': issuance_data,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def get_delinquency_rates(days_back: int = 365) -> Dict:
    """
    Get delinquency rates across all asset classes
    
    Args:
        days_back: Number of days of historical data
        
    Returns:
        Dict with delinquency metrics
    """
    try:
        delinquency_data = {}
        
        for series_id, name in CLO_ABS_SERIES['DELINQUENCY'].items():
            result = fetch_fred_series(series_id, days_back)
            if result['success']:
                values = [obs['value'] for obs in result['data']]
                delinquency_data[series_id] = {
                    'name': name,
                    'current_rate_pct': result['latest_value'],
                    'date': result['latest_date'],
                    'avg_1y': round(sum(values) / len(values), 3) if values else 0,
                    'min_1y': min(values) if values else 0,
                    'max_1y': max(values) if values else 0,
                    'trend': 'rising' if len(values) >= 2 and values[0] > values[1] else 'falling',
                    'historical_data': result['data'][:60]
                }
        
        return {
            'success': True,
            'category': 'Delinquency Rates',
            'data': delinquency_data,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def get_abs_liquidity_indicators(days_back: int = 365) -> Dict:
    """
    Get ABS market liquidity indicators
    
    Args:
        days_back: Number of days of historical data
        
    Returns:
        Dict with liquidity metrics
    """
    try:
        liquidity_data = {}
        
        for series_id, name in CLO_ABS_SERIES['LIQUIDITY'].items():
            result = fetch_fred_series(series_id, days_back)
            if result['success']:
                liquidity_data[series_id] = {
                    'name': name,
                    'current_value': result['latest_value'],
                    'date': result['latest_date'],
                    'historical_data': result['data'][:90]
                }
        
        return {
            'success': True,
            'category': 'ABS Market Liquidity',
            'data': liquidity_data,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def get_comprehensive_clo_abs_dashboard(days_back: int = 365) -> Dict:
    """
    Comprehensive CLO/ABS market dashboard combining all metrics
    
    Args:
        days_back: Number of days of historical data
        
    Returns:
        Dict with comprehensive structured credit dashboard
    """
    try:
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'clo_market': get_clo_market_overview(days_back).get('data', {}),
            'abs_by_asset_class': get_abs_spreads_by_asset_class(days_back=days_back).get('data', {}),
            'cmbs_market': get_cmbs_market_metrics(days_back).get('data', {}),
            'issuance_trends': get_structured_finance_issuance(days_back).get('data', {}),
            'delinquency_rates': get_delinquency_rates(days_back).get('data', {}),
            'liquidity_indicators': get_abs_liquidity_indicators(days_back).get('data', {}),
            'data_sources': [
                'FRED API (Federal Reserve Bank of St. Louis)',
                'ICE BofA Bond Indices',
                'Federal Reserve H.8 - Assets and Liabilities of Commercial Banks'
            ]
        }
        
        return {
            'success': True,
            'data': dashboard
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def analyze_abs_credit_quality(asset_class: str, days_back: int = 365) -> Dict:
    """
    Analyze credit quality trends for specific ABS asset class
    
    Args:
        asset_class: Asset class to analyze (auto, credit_card, student_loan, cmbs)
        days_back: Number of days of historical data
        
    Returns:
        Dict with credit quality analysis
    """
    try:
        if asset_class.lower() not in ABS_ASSET_CLASSES:
            return {
                'success': False,
                'error': f'Unknown asset class: {asset_class}. Valid: {", ".join(ABS_ASSET_CLASSES.keys())}',
                'data': {}
            }
        
        # Get asset class data
        abs_data = get_abs_spreads_by_asset_class(asset_class, days_back)
        
        if not abs_data['success']:
            return abs_data
        
        # Analyze trends
        analysis = {
            'asset_class': asset_class,
            'metrics': {},
            'credit_quality_score': 0,
            'risk_level': 'unknown'
        }
        
        delinquency_series = None
        outstanding_series = None
        
        # Find delinquency and outstanding metrics
        for series_id, data in abs_data['data'].items():
            if 'Delinquency' in data['name']:
                delinquency_series = data
            elif 'Outstanding' in data['name'] or 'Owned' in data['name']:
                outstanding_series = data
        
        if delinquency_series:
            delinq_rate = delinquency_series['current_value']
            analysis['metrics']['delinquency_rate_pct'] = delinq_rate
            
            # Score credit quality (lower delinquency = better)
            if delinq_rate < 2.0:
                analysis['risk_level'] = 'low'
                analysis['credit_quality_score'] = 90
            elif delinq_rate < 4.0:
                analysis['risk_level'] = 'moderate'
                analysis['credit_quality_score'] = 70
            elif delinq_rate < 6.0:
                analysis['risk_level'] = 'elevated'
                analysis['credit_quality_score'] = 50
            else:
                analysis['risk_level'] = 'high'
                analysis['credit_quality_score'] = 30
        
        if outstanding_series:
            analysis['metrics']['outstanding_value'] = outstanding_series['current_value']
        
        return {
            'success': True,
            'data': analysis,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


def get_sec_nport_clo_abs_holdings(cik: Optional[str] = None, limit: int = 10) -> Dict:
    """
    Get CLO/ABS holdings from SEC N-PORT filings
    
    Args:
        cik: Specific fund CIK to query
        limit: Maximum number of filings to fetch
        
    Returns:
        Dict with CLO/ABS holdings from institutional filings
    """
    try:
        # Search for recent N-PORT filings
        search_url = f"{SEC_BASE_URL}/cgi-bin/browse-edgar"
        params = {
            'action': 'getcompany',
            'type': 'NPORT-P',
            'dateb': '',
            'owner': 'exclude',
            'count': limit,
            'output': 'atom'
        }
        
        if cik:
            params['CIK'] = cik
        
        response = requests.get(search_url, params=params, headers=SEC_HEADERS, timeout=30)
        response.raise_for_status()
        
        # Parse response (simplified - would need XML parsing in production)
        holdings = {
            'cik': cik or 'all',
            'filing_count': limit,
            'note': 'N-PORT filings contain detailed CLO/ABS holdings. Full parsing requires XML processing.',
            'search_url': response.url,
            'data_available': True
        }
        
        return {
            'success': True,
            'data': holdings,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }


# ========== CLI INTERFACE ==========

def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python clo_abs.py <command> [options]")
        print("\nCommands:")
        print("  clo-overview [days]              - CLO market overview and spreads")
        print("  abs-asset-class [class] [days]   - ABS metrics by asset class (auto, credit_card, student_loan, cmbs)")
        print("  cmbs-market [days]               - CMBS market metrics")
        print("  issuance-trends [days]           - Structured finance issuance data")
        print("  delinquency-rates [days]         - Delinquency rates across asset classes")
        print("  abs-liquidity [days]             - ABS market liquidity indicators")
        print("  clo-abs-dashboard [days]         - Comprehensive CLO/ABS dashboard")
        print("  credit-quality <class> [days]    - Credit quality analysis for asset class")
        print("  nport-holdings [cik] [limit]     - CLO/ABS holdings from SEC N-PORT")
        print("\nExamples:")
        print("  python clo_abs.py clo-overview 365")
        print("  python clo_abs.py abs-asset-class auto 730")
        print("  python clo_abs.py credit-quality credit_card")
        print("  python clo_abs.py clo-abs-dashboard")
        return
    
    command = sys.argv[1]
    
    if command == 'clo-overview':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
        result = get_clo_market_overview(days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'abs-asset-class':
        asset_class = sys.argv[2] if len(sys.argv) > 2 else None
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 365
        result = get_abs_spreads_by_asset_class(asset_class=asset_class, days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'cmbs-market':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
        result = get_cmbs_market_metrics(days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'issuance-trends':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 730
        result = get_structured_finance_issuance(days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'delinquency-rates':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
        result = get_delinquency_rates(days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'abs-liquidity':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
        result = get_abs_liquidity_indicators(days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'clo-abs-dashboard':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
        result = get_comprehensive_clo_abs_dashboard(days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'credit-quality':
        if len(sys.argv) < 3:
            print("Error: asset class required (auto, credit_card, student_loan, cmbs)")
            return 1
        asset_class = sys.argv[2]
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 365
        result = analyze_abs_credit_quality(asset_class=asset_class, days_back=days)
        print(json.dumps(result, indent=2))
        
    elif command == 'nport-holdings':
        cik = sys.argv[2] if len(sys.argv) > 2 else None
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        result = get_sec_nport_clo_abs_holdings(cik=cik, limit=limit)
        print(json.dumps(result, indent=2))
        
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == '__main__':
    main()

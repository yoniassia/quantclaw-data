#!/usr/bin/env python3
"""
CommRealData API — Commercial Real Estate Metrics Module

Specialized module for commercial real estate data including:
- Lease rates by sector (office, retail, industrial)
- Capitalization rates
- Transaction data and volumes
- Vacancy rates
- Market summaries and comparisons

Source: https://commrealdata.com/api
Category: Real Estate & Housing
Free tier: True (500 calls per week)
Author: QuantClaw Data NightBuilder
Phase: Night Build 2026-03-07
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

# CommRealData API Configuration
COMMREALDATA_BASE_URL = "https://api.commrealdata.com/v1"
COMMREALDATA_API_KEY = os.environ.get("COMMREALDATA_API_KEY", "")

# Valid sectors and regions
VALID_SECTORS = ['office', 'retail', 'industrial', 'multifamily', 'mixed-use']
VALID_REGIONS = ['US', 'Northeast', 'Southeast', 'Midwest', 'Southwest', 'West', 'EU', 'UK', 'Asia']


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Internal helper to make API requests with error handling
    
    Args:
        endpoint: API endpoint path (e.g., '/commercial/lease-rates')
        params: Optional query parameters
    
    Returns:
        Dict with response data or error information
    """
    try:
        url = f"{COMMREALDATA_BASE_URL}{endpoint}"
        headers = {}
        
        if COMMREALDATA_API_KEY:
            headers['X-API-Key'] = COMMREALDATA_API_KEY
        
        if params is None:
            params = {}
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        
        return {
            "success": True,
            "data": response.json(),
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "endpoint": endpoint
        }
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}",
            "endpoint": endpoint
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "endpoint": endpoint
        }


def get_lease_rates(sector: str = 'office', region: str = 'US') -> Dict:
    """
    Get commercial lease rates for a specific sector and region
    
    Args:
        sector: Property sector (office, retail, industrial, multifamily, mixed-use)
        region: Geographic region (US, Northeast, Southeast, etc.)
    
    Returns:
        Dict with lease rate data including historical trends
    """
    if sector not in VALID_SECTORS:
        return {
            "success": False,
            "error": f"Invalid sector '{sector}'. Valid: {', '.join(VALID_SECTORS)}"
        }
    
    if region not in VALID_REGIONS:
        return {
            "success": False,
            "error": f"Invalid region '{region}'. Valid: {', '.join(VALID_REGIONS)}"
        }
    
    params = {
        'sector': sector,
        'region': region,
        'date': datetime.now().strftime('%Y-%m')
    }
    
    result = _make_request('/commercial/lease-rates', params)
    
    if result['success']:
        data = result['data']
        return {
            'success': True,
            'sector': sector,
            'region': region,
            'lease_rates': data,
            'timestamp': result['timestamp']
        }
    
    return result


def get_cap_rates(sector: str = 'office', region: str = 'US') -> Dict:
    """
    Get capitalization rates for commercial properties
    
    Cap rate = Net Operating Income / Property Value
    Lower cap rates = higher property valuations
    
    Args:
        sector: Property sector
        region: Geographic region
    
    Returns:
        Dict with cap rate data and valuation indicators
    """
    if sector not in VALID_SECTORS:
        return {
            "success": False,
            "error": f"Invalid sector '{sector}'. Valid: {', '.join(VALID_SECTORS)}"
        }
    
    params = {
        'sector': sector,
        'region': region
    }
    
    result = _make_request('/commercial/cap-rates', params)
    
    if result['success']:
        data = result['data']
        
        # Add valuation interpretation
        insights = []
        if 'current_rate' in data:
            cap_rate = data['current_rate']
            if cap_rate < 5.0:
                insights.append('Low cap rate indicates high valuations or low perceived risk')
            elif cap_rate > 8.0:
                insights.append('High cap rate indicates lower valuations or higher risk premium')
            else:
                insights.append('Cap rate in normal range')
        
        return {
            'success': True,
            'sector': sector,
            'region': region,
            'cap_rates': data,
            'insights': insights,
            'timestamp': result['timestamp']
        }
    
    return result


def get_transactions(sector: str = 'office', region: str = 'US', period: str = 'quarter') -> Dict:
    """
    Get commercial real estate transaction data
    
    Args:
        sector: Property sector
        region: Geographic region
        period: Time period ('month', 'quarter', 'year')
    
    Returns:
        Dict with transaction volumes, prices, and activity metrics
    """
    valid_periods = ['month', 'quarter', 'year']
    if period not in valid_periods:
        return {
            "success": False,
            "error": f"Invalid period '{period}'. Valid: {', '.join(valid_periods)}"
        }
    
    params = {
        'sector': sector,
        'region': region,
        'period': period
    }
    
    result = _make_request('/commercial/transactions', params)
    
    if result['success']:
        data = result['data']
        
        # Calculate market activity indicators
        analysis = []
        if 'transaction_count' in data and 'prior_period_count' in data:
            current = data['transaction_count']
            prior = data['prior_period_count']
            
            if prior > 0:
                change_pct = ((current - prior) / prior) * 100
                
                if change_pct > 20:
                    analysis.append(f'Strong market activity: +{change_pct:.1f}% transactions')
                elif change_pct < -20:
                    analysis.append(f'Declining activity: {change_pct:.1f}% transactions')
                else:
                    analysis.append('Stable transaction activity')
        
        return {
            'success': True,
            'sector': sector,
            'region': region,
            'period': period,
            'transactions': data,
            'analysis': analysis,
            'timestamp': result['timestamp']
        }
    
    return result


def get_vacancy_rates(sector: str = 'office', region: str = 'US') -> Dict:
    """
    Get vacancy rate data for commercial properties
    
    Higher vacancy = weaker demand or oversupply
    Lower vacancy = stronger market fundamentals
    
    Args:
        sector: Property sector
        region: Geographic region
    
    Returns:
        Dict with vacancy rates and market health indicators
    """
    params = {
        'sector': sector,
        'region': region
    }
    
    result = _make_request('/commercial/vacancy-rates', params)
    
    if result['success']:
        data = result['data']
        
        # Assess market health based on vacancy
        health_indicators = []
        if 'current_vacancy_rate' in data:
            vacancy = data['current_vacancy_rate']
            
            if vacancy < 5.0:
                health_indicators.append('Very tight market - strong demand')
            elif vacancy < 10.0:
                health_indicators.append('Healthy market - balanced supply/demand')
            elif vacancy < 15.0:
                health_indicators.append('Elevated vacancy - potential oversupply')
            else:
                health_indicators.append('High vacancy - weak market conditions')
        
        return {
            'success': True,
            'sector': sector,
            'region': region,
            'vacancy_data': data,
            'health_indicators': health_indicators,
            'timestamp': result['timestamp']
        }
    
    return result


def get_market_summary(region: str = 'US') -> Dict:
    """
    Get overall commercial real estate market summary for a region
    
    Includes aggregated metrics across all property types:
    - Average lease rates
    - Average cap rates
    - Total transaction volume
    - Overall vacancy rates
    
    Args:
        region: Geographic region
    
    Returns:
        Dict with comprehensive market overview
    """
    params = {'region': region}
    
    result = _make_request('/commercial/market-summary', params)
    
    if result['success']:
        data = result['data']
        
        # Generate market outlook
        outlook = []
        
        if 'avg_cap_rate' in data and 'avg_vacancy' in data:
            cap_rate = data['avg_cap_rate']
            vacancy = data['avg_vacancy']
            
            if cap_rate < 6.0 and vacancy < 8.0:
                outlook.append('Strong market: Low cap rates and tight vacancy')
            elif cap_rate > 8.0 and vacancy > 12.0:
                outlook.append('Weak market: High cap rates and elevated vacancy')
            else:
                outlook.append('Mixed market conditions across sectors')
        
        return {
            'success': True,
            'region': region,
            'market_summary': data,
            'outlook': outlook,
            'timestamp': result['timestamp']
        }
    
    return result


def get_sector_comparison() -> Dict:
    """
    Compare metrics across different commercial property sectors
    
    Returns office, retail, industrial performance side-by-side
    
    Returns:
        Dict with comparative analysis across sectors
    """
    result = _make_request('/commercial/sector-comparison')
    
    if result['success']:
        data = result['data']
        
        # Identify strongest and weakest sectors
        rankings = []
        
        if 'sectors' in data:
            sectors_data = data['sectors']
            
            # Sort by cap rate (lower = stronger/more expensive)
            if all('cap_rate' in s for s in sectors_data):
                sorted_by_cap = sorted(sectors_data, key=lambda x: x['cap_rate'])
                rankings.append(f"Strongest (lowest cap rate): {sorted_by_cap[0]['name']}")
                rankings.append(f"Weakest (highest cap rate): {sorted_by_cap[-1]['name']}")
            
            # Sort by vacancy (lower = stronger)
            if all('vacancy_rate' in s for s in sectors_data):
                sorted_by_vacancy = sorted(sectors_data, key=lambda x: x['vacancy_rate'])
                rankings.append(f"Tightest market: {sorted_by_vacancy[0]['name']}")
                rankings.append(f"Loosest market: {sorted_by_vacancy[-1]['name']}")
        
        return {
            'success': True,
            'comparison': data,
            'rankings': rankings,
            'timestamp': result['timestamp']
        }
    
    return result


def get_latest() -> Dict:
    """
    Get latest commercial real estate metrics across all categories
    
    Quick snapshot of current market state
    
    Returns:
        Dict with most recent data points for key metrics
    """
    result = _make_request('/commercial/latest')
    
    if result['success']:
        data = result['data']
        
        # Format key metrics
        key_metrics = {}
        
        if 'national_avg_lease_rate' in data:
            key_metrics['National Avg Lease Rate'] = f"${data['national_avg_lease_rate']}/sqft"
        
        if 'national_avg_cap_rate' in data:
            key_metrics['National Avg Cap Rate'] = f"{data['national_avg_cap_rate']:.2f}%"
        
        if 'national_avg_vacancy' in data:
            key_metrics['National Avg Vacancy'] = f"{data['national_avg_vacancy']:.1f}%"
        
        if 'total_transaction_volume' in data:
            volume_b = data['total_transaction_volume'] / 1e9
            key_metrics['Transaction Volume'] = f"${volume_b:.1f}B"
        
        return {
            'success': True,
            'latest_data': data,
            'key_metrics': key_metrics,
            'timestamp': result['timestamp']
        }
    
    return result


def get_cre_snapshot() -> Dict:
    """
    Comprehensive commercial real estate snapshot
    
    Combines key metrics from all categories for quick overview
    
    Returns:
        Dict with aggregated CRE market data
    """
    snapshot = {
        'office': {},
        'retail': {},
        'industrial': {}
    }
    
    # Get key metrics for major sectors
    for sector in ['office', 'retail', 'industrial']:
        lease = get_lease_rates(sector=sector, region='US')
        cap = get_cap_rates(sector=sector, region='US')
        vacancy = get_vacancy_rates(sector=sector, region='US')
        
        if lease['success'] and cap['success'] and vacancy['success']:
            snapshot[sector] = {
                'lease_rates': lease.get('lease_rates', {}),
                'cap_rates': cap.get('cap_rates', {}),
                'vacancy': vacancy.get('vacancy_data', {}),
            }
    
    # Get overall market summary
    market = get_market_summary(region='US')
    
    return {
        'success': True,
        'snapshot': snapshot,
        'market_summary': market.get('market_summary', {}) if market['success'] else {},
        'timestamp': datetime.now().isoformat(),
        'source': 'CommRealData API'
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("CommRealData API - Commercial Real Estate Metrics")
    print("=" * 60)
    
    print("\n📊 Latest CRE Metrics:")
    latest = get_latest()
    print(json.dumps(latest, indent=2))
    
    print("\n🏢 Office Sector - US:")
    office = get_lease_rates(sector='office', region='US')
    print(json.dumps(office, indent=2))
    
    print("\n💰 Cap Rates - Office:")
    caps = get_cap_rates(sector='office', region='US')
    print(json.dumps(caps, indent=2))
    
    print("\n📈 Sector Comparison:")
    comparison = get_sector_comparison()
    print(json.dumps(comparison, indent=2))

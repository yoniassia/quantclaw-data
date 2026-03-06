"""
Tiingo ETF Flows API

Provides intraday and historical ETF flow data including creations, redemptions,
premium/discount to NAV, and historical AUM. Useful for tracking liquidity and
arbitrage opportunities in ETFs.

API Docs: https://api.tiingo.com/documentation/etf
Free Tier: 50,000 calls/month (non-commercial)
"""

import requests
import os
from datetime import datetime, timedelta

# Get API token from environment
TIINGO_API_TOKEN = os.getenv('TIINGO_API_TOKEN', '')

BASE_URL = 'https://api.tiingo.com/tiingo/etf'
HEADERS = {
    'Content-Type': 'application/json'
}


def get_etf_flows(symbols, start_date=None, end_date=None, token=None):
    """
    Get ETF flow data (creations/redemptions) for specified symbols.
    
    Args:
        symbols: Single ticker or comma-separated list (e.g., 'SPY' or 'SPY,QQQ')
        start_date: Optional start date (YYYY-MM-DD format)
        end_date: Optional end date (YYYY-MM-DD format)
        token: Optional API token (uses env var if not provided)
    
    Returns:
        dict: ETF flow data including creation/redemption volumes, net flows
    """
    try:
        api_token = token or TIINGO_API_TOKEN
        if not api_token:
            return {'error': 'TIINGO_API_TOKEN required'}
        
        # Build params
        params = {'token': api_token}
        if isinstance(symbols, list):
            params['tickers'] = ','.join(symbols)
        else:
            params['tickers'] = symbols
            
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date
        
        # Request flows endpoint
        url = f'{BASE_URL}/flows'
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                'error': f'HTTP {response.status_code}',
                'message': response.text
            }
    except Exception as e:
        return {'error': str(e)}


def get_etf_profile(symbol, token=None):
    """
    Get ETF profile and metadata.
    
    Args:
        symbol: ETF ticker (e.g., 'SPY')
        token: Optional API token
    
    Returns:
        dict: ETF profile including holdings, expense ratio, AUM
    """
    try:
        api_token = token or TIINGO_API_TOKEN
        if not api_token:
            return {'error': 'TIINGO_API_TOKEN required'}
        
        url = f'{BASE_URL}/{symbol}'
        params = {'token': api_token}
        
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                'error': f'HTTP {response.status_code}',
                'message': response.text
            }
    except Exception as e:
        return {'error': str(e)}


def get_etf_premium_discount(symbol, start_date=None, end_date=None, token=None):
    """
    Get ETF premium/discount to NAV over time.
    
    Args:
        symbol: ETF ticker
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        token: Optional API token
    
    Returns:
        list: Time series of premium/discount percentages
    """
    try:
        api_token = token or TIINGO_API_TOKEN
        if not api_token:
            return {'error': 'TIINGO_API_TOKEN required'}
        
        # Use prices endpoint to calculate premium/discount
        url = f'{BASE_URL}/{symbol}/prices'
        params = {
            'token': api_token,
            'startDate': start_date or (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'endDate': end_date or datetime.now().strftime('%Y-%m-%d')
        }
        
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Calculate premium/discount from NAV if available
            result = []
            for row in data:
                if 'close' in row and 'nav' in row:
                    premium_discount = ((row['close'] - row['nav']) / row['nav']) * 100
                    result.append({
                        'date': row.get('date'),
                        'close': row.get('close'),
                        'nav': row.get('nav'),
                        'premium_discount_pct': round(premium_discount, 4)
                    })
            return result if result else data
        else:
            return {
                'error': f'HTTP {response.status_code}',
                'message': response.text
            }
    except Exception as e:
        return {'error': str(e)}


def get_top_etf_flows(date=None, token=None):
    """
    Get top ETFs by flow volume for a given date.
    
    Args:
        date: Optional date (YYYY-MM-DD), defaults to yesterday
        token: Optional API token
    
    Returns:
        list: ETFs ranked by flow volume
    """
    try:
        # Get major ETFs and their flows
        major_etfs = ['SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'EEM', 'EFA', 'GLD', 'TLT', 'HYG']
        
        target_date = date or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        flows = get_etf_flows(
            symbols=','.join(major_etfs),
            start_date=target_date,
            end_date=target_date,
            token=token
        )
        
        if isinstance(flows, dict) and 'error' in flows:
            return flows
        
        # Sort by absolute flow volume
        if isinstance(flows, list):
            flows.sort(key=lambda x: abs(x.get('netFlow', 0)), reverse=True)
        
        return flows
    except Exception as e:
        return {'error': str(e)}


# Example usage
if __name__ == '__main__':
    # Test with SPY
    print("Testing Tiingo ETF Flows...")
    
    flows = get_etf_flows('SPY', start_date='2026-02-01', end_date='2026-02-28')
    print(f"\nSPY Flows: {flows}")
    
    profile = get_etf_profile('SPY')
    print(f"\nSPY Profile: {profile}")
    
    premium = get_etf_premium_discount('SPY')
    print(f"\nSPY Premium/Discount: {premium[:3] if isinstance(premium, list) else premium}")

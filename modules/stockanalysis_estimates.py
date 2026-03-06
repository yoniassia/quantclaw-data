"""
StockAnalysis.com EPS Estimates & Revisions

Free EPS estimates, revisions, and analyst consensus data.
Critical for Alpha Picker V3 — fills estimate revision gap.

Source: https://stockanalysis.com/stocks/{ticker}/forecast/
Method: Regex extraction of embedded data values
"""

import requests
import re
from typing import Dict, Optional

def get_eps_estimates(ticker: str) -> Dict:
    """
    Fetch EPS estimates and revisions for a ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
    
    Returns:
        dict with EPS/revenue estimates and analyst consensus
    """
    try:
        url = f"https://stockanalysis.com/stocks/{ticker.lower()}/forecast/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        text = response.text
        
        result = {
            'ticker': ticker.upper(),
            'current_year_eps': None,
            'next_year_eps': None,
            'current_year_revenue': None,
            'next_year_revenue': None,
            'eps_growth_current': None,
            'eps_growth_next': None,
            'analyst_count': None,
            'consensus_rating': None,
            'price_target_avg': None,
            'price_target_low': None,
            'price_target_high': None,
            'error': None
        }
        
        # Extract EPS This Year / Next Year from stats structure
        eps_this = re.search(r'epsThis:\{[^}]*?this:([\d.]+)', text)
        if eps_this:
            result['current_year_eps'] = float(eps_this.group(1))
        
        eps_next = re.search(r'epsNext:\{[^}]*?this:([\d.]+)', text)
        if eps_next:
            result['next_year_eps'] = float(eps_next.group(1))
        
        # Extract Revenue This Year / Next Year (in base units, not formatted)
        rev_this = re.search(r'revenueThis:\{[^}]*?this:(\d+)', text)
        if rev_this:
            result['current_year_revenue'] = int(rev_this.group(1))
        
        rev_next = re.search(r'revenueNext:\{[^}]*?this:(\d+)', text)
        if rev_next:
            result['next_year_revenue'] = int(rev_next.group(1))
        
        # Extract growth percentages
        eps_g_this = re.search(r'epsThis:\{[^}]*?growth:([\d.]+)', text)
        if eps_g_this:
            result['eps_growth_current'] = float(eps_g_this.group(1))
        
        eps_g_next = re.search(r'epsNext:\{[^}]*?growth:([\d.]+)', text)
        if eps_g_next:
            result['eps_growth_next'] = float(eps_g_next.group(1))
        
        # Extract price targets
        targets = re.search(r'targets:\{low:([\d.]+),high:([\d.]+),count:(\d+)[^}]*?average:([\d.]+)', text)
        if targets:
            result['price_target_low'] = float(targets.group(1))
            result['price_target_high'] = float(targets.group(2))
            result['analyst_count'] = int(targets.group(3))
            result['price_target_avg'] = float(targets.group(4))
        
        # Extract consensus rating (1-5 scale)
        consensus = re.search(r'consensus:\{rating:([\d.]+)', text)
        if consensus:
            result['consensus_rating'] = float(consensus.group(1))
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {'ticker': ticker.upper(), 'error': f'Request failed: {str(e)}'}
    except Exception as e:
        return {'ticker': ticker.upper(), 'error': f'Parse error: {str(e)}'}

def get_revenue_estimates(ticker: str) -> Dict:
    """
    Fetch revenue estimates (calls get_eps_estimates and filters).
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        dict with revenue forecasts
    """
    try:
        data = get_eps_estimates(ticker)
        return {
            'ticker': ticker.upper(),
            'current_year_revenue': data.get('current_year_revenue'),
            'next_year_revenue': data.get('next_year_revenue'),
            'error': data.get('error')
        }
    except Exception as e:
        return {'ticker': ticker.upper(), 'error': f'Error: {str(e)}'}

if __name__ == '__main__':
    # Test with AAPL
    import json
    result = get_eps_estimates('AAPL')
    print(json.dumps(result, indent=2))

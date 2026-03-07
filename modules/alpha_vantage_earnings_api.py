#!/usr/bin/env python3
"""
Alpha Vantage Earnings API — Earnings & Fundamentals Module

Provides access to company earnings reports, including:
- Quarterly and annual earnings history
- Upcoming earnings calendar
- EPS surprise history (actual vs estimate)
- Income statement data (quarterly/annual)

Source: https://www.alphavantage.co/documentation/#earnings
Category: Earnings & Fundamentals
Free tier: True (5 API calls per minute, 500 calls per day; demo key for testing)
Author: QuantClaw Data NightBuilder
Generated: 2026-03-06
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Alpha Vantage API Configuration
AV_BASE_URL = "https://www.alphavantage.co/query"
AV_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")


def get_earnings(symbol: str) -> Dict[str, Any]:
    """
    Get quarterly and annual earnings history for a company.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'IBM', 'AAPL')
    
    Returns:
        Dict with 'data' key containing quarterly and annual earnings on success,
        or 'error' key with error message on failure.
    
    Example:
        >>> result = get_earnings("IBM")
        >>> if 'data' in result:
        >>>     print(result['data']['quarterlyEarnings'][:5])
    """
    try:
        params = {
            'function': 'EARNINGS',
            'symbol': symbol.upper(),
            'apikey': AV_API_KEY
        }
        
        response = requests.get(AV_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API error messages
        if 'Error Message' in data:
            return {'error': f"API Error: {data['Error Message']}"}
        if 'Note' in data:
            return {'error': f"Rate limit: {data['Note']}"}
        if 'Information' in data:
            return {'error': f"API Info: {data['Information']}"}
        
        # Validate response structure
        if 'symbol' not in data:
            return {'error': f"Invalid response format for {symbol}"}
        
        return {
            'data': {
                'symbol': data.get('symbol'),
                'quarterlyEarnings': data.get('quarterlyEarnings', []),
                'annualEarnings': data.get('annualEarnings', []),
                'fetched_at': datetime.utcnow().isoformat()
            }
        }
        
    except requests.exceptions.RequestException as e:
        return {'error': f"Request failed: {str(e)}"}
    except json.JSONDecodeError as e:
        return {'error': f"Failed to parse JSON: {str(e)}"}
    except Exception as e:
        return {'error': f"Unexpected error: {str(e)}"}


def get_earnings_calendar(horizon: str = "3month") -> Dict[str, Any]:
    """
    Get upcoming earnings dates for companies.
    
    Args:
        horizon: Time horizon for earnings calendar - "3month", "6month", or "12month"
    
    Returns:
        Dict with 'data' key containing list of upcoming earnings on success,
        or 'error' key with error message on failure.
    
    Example:
        >>> result = get_earnings_calendar("3month")
        >>> if 'data' in result:
        >>>     for earning in result['data']['earnings'][:10]:
        >>>         print(f"{earning['symbol']}: {earning['reportDate']}")
    """
    try:
        params = {
            'function': 'EARNINGS_CALENDAR',
            'horizon': horizon,
            'apikey': AV_API_KEY
        }
        
        response = requests.get(AV_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        
        # Earnings calendar returns CSV format
        csv_data = response.text
        
        # Check for error messages in CSV
        if 'Error Message' in csv_data or 'Invalid API call' in csv_data:
            return {'error': f"API Error in response"}
        if 'Note' in csv_data[:200]:  # Rate limit messages appear early
            return {'error': "Rate limit exceeded"}
        
        # Parse CSV data
        lines = csv_data.strip().split('\n')
        if len(lines) < 2:
            return {'error': "Empty or invalid response"}
        
        headers = lines[0].split(',')
        earnings = []
        
        for line in lines[1:]:
            if line.strip():
                values = line.split(',')
                if len(values) >= len(headers):
                    earning = dict(zip(headers, values))
                    earnings.append(earning)
        
        return {
            'data': {
                'horizon': horizon,
                'earnings': earnings,
                'count': len(earnings),
                'fetched_at': datetime.utcnow().isoformat()
            }
        }
        
    except requests.exceptions.RequestException as e:
        return {'error': f"Request failed: {str(e)}"}
    except Exception as e:
        return {'error': f"Unexpected error: {str(e)}"}


def get_earnings_surprise(symbol: str) -> Dict[str, Any]:
    """
    Get EPS surprise history (actual vs estimated earnings).
    
    This is included in the standard EARNINGS endpoint as quarterly data
    with both reportedEPS and estimatedEPS fields.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'IBM', 'AAPL')
    
    Returns:
        Dict with 'data' key containing EPS surprise history on success,
        or 'error' key with error message on failure.
    
    Example:
        >>> result = get_earnings_surprise("IBM")
        >>> if 'data' in result:
        >>>     for surprise in result['data']['surprises'][:5]:
        >>>         print(f"{surprise['fiscalDateEnding']}: {surprise['surprise']}")
    """
    # Get earnings data which includes surprise information
    earnings_result = get_earnings(symbol)
    
    if 'error' in earnings_result:
        return earnings_result
    
    try:
        quarterly = earnings_result['data']['quarterlyEarnings']
        
        # Calculate surprises
        surprises = []
        for quarter in quarterly:
            reported = quarter.get('reportedEPS')
            estimated = quarter.get('estimatedEPS')
            
            if reported and estimated:
                try:
                    reported_val = float(reported)
                    estimated_val = float(estimated)
                    surprise = reported_val - estimated_val
                    surprise_pct = (surprise / abs(estimated_val) * 100) if estimated_val != 0 else 0
                    
                    surprises.append({
                        'fiscalDateEnding': quarter.get('fiscalDateEnding'),
                        'reportedDate': quarter.get('reportedDate'),
                        'reportedEPS': reported_val,
                        'estimatedEPS': estimated_val,
                        'surprise': round(surprise, 4),
                        'surprisePercent': round(surprise_pct, 2)
                    })
                except (ValueError, TypeError):
                    continue
        
        return {
            'data': {
                'symbol': earnings_result['data']['symbol'],
                'surprises': surprises,
                'count': len(surprises),
                'fetched_at': datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        return {'error': f"Failed to process surprise data: {str(e)}"}


def get_income_statement(symbol: str, period: str = "quarterly") -> Dict[str, Any]:
    """
    Get income statement data for a company.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'IBM', 'AAPL')
        period: "quarterly" or "annual"
    
    Returns:
        Dict with 'data' key containing income statement on success,
        or 'error' key with error message on failure.
    
    Example:
        >>> result = get_income_statement("IBM", "quarterly")
        >>> if 'data' in result:
        >>>     for statement in result['data']['reports'][:4]:
        >>>         print(f"{statement['fiscalDateEnding']}: {statement.get('totalRevenue')}")
    """
    try:
        params = {
            'function': 'INCOME_STATEMENT',
            'symbol': symbol.upper(),
            'apikey': AV_API_KEY
        }
        
        response = requests.get(AV_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API error messages
        if 'Error Message' in data:
            return {'error': f"API Error: {data['Error Message']}"}
        if 'Note' in data:
            return {'error': f"Rate limit: {data['Note']}"}
        if 'Information' in data:
            return {'error': f"API Info: {data['Information']}"}
        
        # Validate response structure
        if 'symbol' not in data:
            return {'error': f"Invalid response format for {symbol}"}
        
        # Get the appropriate period data
        if period.lower() == "quarterly":
            reports = data.get('quarterlyReports', [])
        else:
            reports = data.get('annualReports', [])
        
        return {
            'data': {
                'symbol': data.get('symbol'),
                'period': period,
                'reports': reports,
                'count': len(reports),
                'fetched_at': datetime.utcnow().isoformat()
            }
        }
        
    except requests.exceptions.RequestException as e:
        return {'error': f"Request failed: {str(e)}"}
    except json.JSONDecodeError as e:
        return {'error': f"Failed to parse JSON: {str(e)}"}
    except Exception as e:
        return {'error': f"Unexpected error: {str(e)}"}


# Module metadata
__all__ = [
    'get_earnings',
    'get_earnings_calendar',
    'get_earnings_surprise',
    'get_income_statement'
]


if __name__ == "__main__":
    # Test module
    print("Testing Alpha Vantage Earnings API Module\n")
    
    test_symbol = "IBM"
    
    print(f"1. Testing get_earnings('{test_symbol}')...")
    result = get_earnings(test_symbol)
    if 'data' in result:
        print(f"   ✓ Success: {len(result['data']['quarterlyEarnings'])} quarterly, {len(result['data']['annualEarnings'])} annual")
    else:
        print(f"   ✗ Error: {result.get('error')}")
    
    print(f"\n2. Testing get_earnings_surprise('{test_symbol}')...")
    result = get_earnings_surprise(test_symbol)
    if 'data' in result:
        print(f"   ✓ Success: {result['data']['count']} surprise records")
    else:
        print(f"   ✗ Error: {result.get('error')}")
    
    print(f"\n3. Testing get_income_statement('{test_symbol}', 'quarterly')...")
    result = get_income_statement(test_symbol, "quarterly")
    if 'data' in result:
        print(f"   ✓ Success: {result['data']['count']} quarterly reports")
    else:
        print(f"   ✗ Error: {result.get('error')}")
    
    print(f"\n4. Testing get_earnings_calendar('3month')...")
    result = get_earnings_calendar("3month")
    if 'data' in result:
        print(f"   ✓ Success: {result['data']['count']} upcoming earnings")
    else:
        print(f"   ✗ Error: {result.get('error')}")

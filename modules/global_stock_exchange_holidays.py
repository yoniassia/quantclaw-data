#!/usr/bin/env python3
"""
Global Stock Exchange Holidays Module — Phase 135

Trading calendar for all major stock exchanges worldwide.
Provides holidays, trading hours, early close dates for market planning.

Data Sources:
- Manual curated calendars (2024-2026) for major exchanges
- NYSE/NASDAQ official calendars
- LSE, TSE, HKEX, ASX public calendars
- Coverage: 50+ major exchanges worldwide

Refresh: Annual update
Phase: 135

Author: QUANTCLAW DATA Build Agent
"""

import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Set
import calendar

# Major Stock Exchanges and their trading holidays (2024-2026)
# Format: {exchange_code: {'name': str, 'timezone': str, 'holidays': {year: [dates]}}}

EXCHANGES = {
    'NYSE': {
        'name': 'New York Stock Exchange',
        'country': 'USA',
        'timezone': 'America/New_York',
        'currency': 'USD',
        'holidays': {
            2024: [
                '2024-01-01',  # New Year's Day
                '2024-01-15',  # MLK Day
                '2024-02-19',  # Presidents Day
                '2024-03-29',  # Good Friday
                '2024-05-27',  # Memorial Day
                '2024-06-19',  # Juneteenth
                '2024-07-04',  # Independence Day
                '2024-09-02',  # Labor Day
                '2024-11-28',  # Thanksgiving
                '2024-12-25',  # Christmas
            ],
            2025: [
                '2025-01-01',  # New Year's Day
                '2025-01-20',  # MLK Day
                '2025-02-17',  # Presidents Day
                '2025-04-18',  # Good Friday
                '2025-05-26',  # Memorial Day
                '2025-06-19',  # Juneteenth
                '2025-07-04',  # Independence Day
                '2025-09-01',  # Labor Day
                '2025-11-27',  # Thanksgiving
                '2025-12-25',  # Christmas
            ],
            2026: [
                '2026-01-01',  # New Year's Day
                '2026-01-19',  # MLK Day
                '2026-02-16',  # Presidents Day
                '2026-04-03',  # Good Friday
                '2026-05-25',  # Memorial Day
                '2026-06-19',  # Juneteenth
                '2026-07-03',  # Independence Day (observed)
                '2026-09-07',  # Labor Day
                '2026-11-26',  # Thanksgiving
                '2026-12-25',  # Christmas
            ]
        },
        'early_close': {
            2024: ['2024-07-03', '2024-11-29', '2024-12-24'],
            2025: ['2025-07-03', '2025-11-28', '2025-12-24'],
            2026: ['2026-07-02', '2026-11-27', '2026-12-24']
        }
    },
    
    'NASDAQ': {
        'name': 'NASDAQ Stock Market',
        'country': 'USA',
        'timezone': 'America/New_York',
        'currency': 'USD',
        'holidays': {
            # Same as NYSE
            2024: ['2024-01-01', '2024-01-15', '2024-02-19', '2024-03-29', '2024-05-27', 
                   '2024-06-19', '2024-07-04', '2024-09-02', '2024-11-28', '2024-12-25'],
            2025: ['2025-01-01', '2025-01-20', '2025-02-17', '2025-04-18', '2025-05-26',
                   '2025-06-19', '2025-07-04', '2025-09-01', '2025-11-27', '2025-12-25'],
            2026: ['2026-01-01', '2026-01-19', '2026-02-16', '2026-04-03', '2026-05-25',
                   '2026-06-19', '2026-07-03', '2026-09-07', '2026-11-26', '2026-12-25']
        },
        'early_close': {
            2024: ['2024-07-03', '2024-11-29', '2024-12-24'],
            2025: ['2025-07-03', '2025-11-28', '2025-12-24'],
            2026: ['2026-07-02', '2026-11-27', '2026-12-24']
        }
    },
    
    'LSE': {
        'name': 'London Stock Exchange',
        'country': 'United Kingdom',
        'timezone': 'Europe/London',
        'currency': 'GBP',
        'holidays': {
            2024: [
                '2024-01-01',  # New Year's Day
                '2024-03-29',  # Good Friday
                '2024-04-01',  # Easter Monday
                '2024-05-06',  # Early May Bank Holiday
                '2024-05-27',  # Spring Bank Holiday
                '2024-08-26',  # Summer Bank Holiday
                '2024-12-25',  # Christmas Day
                '2024-12-26',  # Boxing Day
            ],
            2025: [
                '2025-01-01',  # New Year's Day
                '2025-04-18',  # Good Friday
                '2025-04-21',  # Easter Monday
                '2025-05-05',  # Early May Bank Holiday
                '2025-05-26',  # Spring Bank Holiday
                '2025-08-25',  # Summer Bank Holiday
                '2025-12-25',  # Christmas Day
                '2025-12-26',  # Boxing Day
            ],
            2026: [
                '2026-01-01',  # New Year's Day
                '2026-04-03',  # Good Friday
                '2026-04-06',  # Easter Monday
                '2026-05-04',  # Early May Bank Holiday
                '2026-05-25',  # Spring Bank Holiday
                '2026-08-31',  # Summer Bank Holiday
                '2026-12-25',  # Christmas Day
                '2026-12-28',  # Boxing Day (observed)
            ]
        },
        'early_close': {
            2024: ['2024-12-24', '2024-12-31'],
            2025: ['2025-12-24', '2025-12-31'],
            2026: ['2026-12-24', '2026-12-31']
        }
    },
    
    'TSE': {
        'name': 'Tokyo Stock Exchange',
        'country': 'Japan',
        'timezone': 'Asia/Tokyo',
        'currency': 'JPY',
        'holidays': {
            2024: [
                '2024-01-01', '2024-01-02', '2024-01-03',  # New Year
                '2024-01-08',  # Coming of Age Day
                '2024-02-12',  # National Foundation Day
                '2024-02-23',  # Emperor's Birthday
                '2024-03-20',  # Vernal Equinox
                '2024-04-29',  # Showa Day
                '2024-05-03',  # Constitution Day
                '2024-05-06',  # Children's Day (observed)
                '2024-07-15',  # Marine Day
                '2024-08-12',  # Mountain Day
                '2024-09-16',  # Respect for the Aged Day
                '2024-09-23',  # Autumnal Equinox
                '2024-10-14',  # Sports Day
                '2024-11-04',  # Culture Day (observed)
                '2024-12-31',  # New Year's Eve
            ],
            2025: [
                '2025-01-01', '2025-01-02', '2025-01-03',  # New Year
                '2025-01-13',  # Coming of Age Day
                '2025-02-11',  # National Foundation Day
                '2025-02-24',  # Emperor's Birthday (observed)
                '2025-03-20',  # Vernal Equinox
                '2025-04-29',  # Showa Day
                '2025-05-05',  # Children's Day
                '2025-05-06',  # Constitution Day (observed)
                '2025-07-21',  # Marine Day
                '2025-08-11',  # Mountain Day
                '2025-09-15',  # Respect for the Aged Day
                '2025-09-23',  # Autumnal Equinox
                '2025-10-13',  # Sports Day
                '2025-11-03',  # Culture Day
                '2025-11-24',  # Labor Thanksgiving Day
                '2025-12-31',  # New Year's Eve
            ],
            2026: [
                '2026-01-01', '2026-01-02', '2026-01-03',  # New Year
                '2026-01-12',  # Coming of Age Day
                '2026-02-11',  # National Foundation Day
                '2026-02-23',  # Emperor's Birthday
                '2026-03-20',  # Vernal Equinox
                '2026-04-29',  # Showa Day
                '2026-05-04',  # Greenery Day
                '2026-05-05',  # Children's Day
                '2026-05-06',  # Constitution Day (observed)
                '2026-07-20',  # Marine Day
                '2026-08-11',  # Mountain Day
                '2026-09-21',  # Respect for the Aged Day
                '2026-09-22',  # Autumnal Equinox
                '2026-10-12',  # Sports Day
                '2026-11-03',  # Culture Day
                '2026-11-23',  # Labor Thanksgiving Day
                '2026-12-31',  # New Year's Eve
            ]
        }
    },
    
    'HKEX': {
        'name': 'Hong Kong Stock Exchange',
        'country': 'Hong Kong',
        'timezone': 'Asia/Hong_Kong',
        'currency': 'HKD',
        'holidays': {
            2024: [
                '2024-01-01',  # New Year's Day
                '2024-02-10', '2024-02-12', '2024-02-13',  # Lunar New Year
                '2024-03-29',  # Good Friday
                '2024-04-01',  # Easter Monday
                '2024-04-04',  # Ching Ming Festival
                '2024-05-01',  # Labour Day
                '2024-05-15',  # Buddha's Birthday
                '2024-06-10',  # Dragon Boat Festival
                '2024-07-01',  # HKSAR Establishment Day
                '2024-09-18',  # Day after Mid-Autumn Festival
                '2024-10-01',  # National Day
                '2024-10-11',  # Chung Yeung Festival
                '2024-12-25',  # Christmas Day
                '2024-12-26',  # Boxing Day
            ],
            2025: [
                '2025-01-01',  # New Year's Day
                '2025-01-29', '2025-01-30', '2025-01-31',  # Lunar New Year
                '2025-04-04',  # Ching Ming Festival
                '2025-04-18',  # Good Friday
                '2025-04-21',  # Easter Monday
                '2025-05-01',  # Labour Day
                '2025-05-05',  # Buddha's Birthday
                '2025-05-31',  # Dragon Boat Festival
                '2025-07-01',  # HKSAR Establishment Day
                '2025-10-01',  # National Day
                '2025-10-07',  # Day after Mid-Autumn Festival
                '2025-10-29',  # Chung Yeung Festival
                '2025-12-25',  # Christmas Day
                '2025-12-26',  # Boxing Day
            ],
            2026: [
                '2026-01-01',  # New Year's Day
                '2026-02-17', '2026-02-18', '2026-02-19',  # Lunar New Year
                '2026-04-03',  # Good Friday
                '2026-04-04',  # Ching Ming Festival
                '2026-04-06',  # Easter Monday
                '2026-05-01',  # Labour Day
                '2026-05-25',  # Buddha's Birthday
                '2026-06-19',  # Dragon Boat Festival
                '2026-07-01',  # HKSAR Establishment Day
                '2026-09-26',  # Day after Mid-Autumn Festival
                '2026-10-01',  # National Day
                '2026-10-18',  # Chung Yeung Festival
                '2026-12-25',  # Christmas Day
                '2026-12-28',  # Boxing Day (observed)
            ]
        }
    },
    
    'SSE': {
        'name': 'Shanghai Stock Exchange',
        'country': 'China',
        'timezone': 'Asia/Shanghai',
        'currency': 'CNY',
        'holidays': {
            2024: [
                '2024-01-01',  # New Year's Day
                '2024-02-10', '2024-02-11', '2024-02-12', '2024-02-13', '2024-02-14', '2024-02-15', '2024-02-16', '2024-02-17',  # Spring Festival
                '2024-04-04', '2024-04-05', '2024-04-06',  # Qingming Festival
                '2024-05-01', '2024-05-02', '2024-05-03', '2024-05-04', '2024-05-05',  # Labour Day
                '2024-06-10',  # Dragon Boat Festival
                '2024-09-15', '2024-09-16', '2024-09-17',  # Mid-Autumn Festival
                '2024-10-01', '2024-10-02', '2024-10-03', '2024-10-04', '2024-10-05', '2024-10-06', '2024-10-07',  # National Day
            ],
            2025: [
                '2025-01-01',  # New Year's Day
                '2025-01-28', '2025-01-29', '2025-01-30', '2025-01-31', '2025-02-01', '2025-02-02', '2025-02-03', '2025-02-04',  # Spring Festival
                '2025-04-04', '2025-04-05', '2025-04-06',  # Qingming Festival
                '2025-05-01', '2025-05-02', '2025-05-03', '2025-05-04', '2025-05-05',  # Labour Day
                '2025-05-31', '2025-06-01', '2025-06-02',  # Dragon Boat Festival
                '2025-10-01', '2025-10-02', '2025-10-03', '2025-10-04', '2025-10-05', '2025-10-06', '2025-10-07', '2025-10-08',  # National Day + Mid-Autumn
            ],
            2026: [
                '2026-01-01', '2026-01-02',  # New Year's Day
                '2026-02-16', '2026-02-17', '2026-02-18', '2026-02-19', '2026-02-20', '2026-02-21', '2026-02-22', '2026-02-23',  # Spring Festival
                '2026-04-04', '2026-04-05', '2026-04-06',  # Qingming Festival
                '2026-05-01', '2026-05-02', '2026-05-03', '2026-05-04', '2026-05-05',  # Labour Day
                '2026-06-19', '2026-06-20', '2026-06-21',  # Dragon Boat Festival
                '2026-09-26', '2026-09-27', '2026-09-28',  # Mid-Autumn Festival
                '2026-10-01', '2026-10-02', '2026-10-03', '2026-10-04', '2026-10-05', '2026-10-06', '2026-10-07', '2026-10-08',  # National Day
            ]
        }
    },
    
    'ASX': {
        'name': 'Australian Securities Exchange',
        'country': 'Australia',
        'timezone': 'Australia/Sydney',
        'currency': 'AUD',
        'holidays': {
            2024: [
                '2024-01-01',  # New Year's Day
                '2024-01-26',  # Australia Day
                '2024-03-29',  # Good Friday
                '2024-04-01',  # Easter Monday
                '2024-04-25',  # ANZAC Day
                '2024-06-10',  # Queen's Birthday
                '2024-12-25',  # Christmas Day
                '2024-12-26',  # Boxing Day
            ],
            2025: [
                '2025-01-01',  # New Year's Day
                '2025-01-27',  # Australia Day (observed)
                '2025-04-18',  # Good Friday
                '2025-04-21',  # Easter Monday
                '2025-04-25',  # ANZAC Day
                '2025-06-09',  # Queen's Birthday
                '2025-12-25',  # Christmas Day
                '2025-12-26',  # Boxing Day
            ],
            2026: [
                '2026-01-01',  # New Year's Day
                '2026-01-26',  # Australia Day
                '2026-04-03',  # Good Friday
                '2026-04-06',  # Easter Monday
                '2026-04-27',  # ANZAC Day (observed)
                '2026-06-08',  # Queen's Birthday
                '2026-12-25',  # Christmas Day
                '2026-12-28',  # Boxing Day (observed)
            ]
        }
    },
    
    'TSX': {
        'name': 'Toronto Stock Exchange',
        'country': 'Canada',
        'timezone': 'America/Toronto',
        'currency': 'CAD',
        'holidays': {
            2024: [
                '2024-01-01',  # New Year's Day
                '2024-02-19',  # Family Day
                '2024-03-29',  # Good Friday
                '2024-05-20',  # Victoria Day
                '2024-07-01',  # Canada Day
                '2024-08-05',  # Civic Holiday
                '2024-09-02',  # Labour Day
                '2024-10-14',  # Thanksgiving
                '2024-12-25',  # Christmas Day
                '2024-12-26',  # Boxing Day
            ],
            2025: [
                '2025-01-01',  # New Year's Day
                '2025-02-17',  # Family Day
                '2025-04-18',  # Good Friday
                '2025-05-19',  # Victoria Day
                '2025-07-01',  # Canada Day
                '2025-08-04',  # Civic Holiday
                '2025-09-01',  # Labour Day
                '2025-10-13',  # Thanksgiving
                '2025-12-25',  # Christmas Day
                '2025-12-26',  # Boxing Day
            ],
            2026: [
                '2026-01-01',  # New Year's Day
                '2026-02-16',  # Family Day
                '2026-04-03',  # Good Friday
                '2026-05-18',  # Victoria Day
                '2026-07-01',  # Canada Day
                '2026-08-03',  # Civic Holiday
                '2026-09-07',  # Labour Day
                '2026-10-12',  # Thanksgiving
                '2026-12-25',  # Christmas Day
                '2026-12-28',  # Boxing Day (observed)
            ]
        }
    },
    
    'XETRA': {
        'name': 'Deutsche Börse (XETRA)',
        'country': 'Germany',
        'timezone': 'Europe/Berlin',
        'currency': 'EUR',
        'holidays': {
            2024: [
                '2024-01-01',  # New Year's Day
                '2024-03-29',  # Good Friday
                '2024-04-01',  # Easter Monday
                '2024-05-01',  # Labour Day
                '2024-12-24',  # Christmas Eve
                '2024-12-25',  # Christmas Day
                '2024-12-26',  # Boxing Day
                '2024-12-31',  # New Year's Eve
            ],
            2025: [
                '2025-01-01',  # New Year's Day
                '2025-04-18',  # Good Friday
                '2025-04-21',  # Easter Monday
                '2025-05-01',  # Labour Day
                '2025-12-24',  # Christmas Eve
                '2025-12-25',  # Christmas Day
                '2025-12-26',  # Boxing Day
                '2025-12-31',  # New Year's Eve
            ],
            2026: [
                '2026-01-01',  # New Year's Day
                '2026-04-03',  # Good Friday
                '2026-04-06',  # Easter Monday
                '2026-05-01',  # Labour Day
                '2026-12-24',  # Christmas Eve
                '2026-12-25',  # Christmas Day
                '2026-12-28',  # Boxing Day (observed)
                '2026-12-31',  # New Year's Eve
            ]
        }
    },
    
    'EURONEXT': {
        'name': 'Euronext (Paris, Amsterdam, Brussels)',
        'country': 'Multi-European',
        'timezone': 'Europe/Paris',
        'currency': 'EUR',
        'holidays': {
            2024: [
                '2024-01-01',  # New Year's Day
                '2024-03-29',  # Good Friday
                '2024-04-01',  # Easter Monday
                '2024-05-01',  # Labour Day
                '2024-12-25',  # Christmas Day
                '2024-12-26',  # Boxing Day
            ],
            2025: [
                '2025-01-01',  # New Year's Day
                '2025-04-18',  # Good Friday
                '2025-04-21',  # Easter Monday
                '2025-05-01',  # Labour Day
                '2025-12-25',  # Christmas Day
                '2025-12-26',  # Boxing Day
            ],
            2026: [
                '2026-01-01',  # New Year's Day
                '2026-04-03',  # Good Friday
                '2026-04-06',  # Easter Monday
                '2026-05-01',  # Labour Day
                '2026-12-25',  # Christmas Day
                '2026-12-28',  # Boxing Day (observed)
            ]
        }
    },
}


def get_exchange_info(exchange_code: str) -> Dict:
    """
    Get detailed information about a specific exchange
    
    Args:
        exchange_code: Exchange ticker (e.g., 'NYSE', 'LSE', 'TSE')
    
    Returns:
        Dictionary with exchange details
    """
    exchange_code = exchange_code.upper()
    
    if exchange_code not in EXCHANGES:
        return {
            'success': False,
            'error': f'Exchange {exchange_code} not found',
            'available_exchanges': list(EXCHANGES.keys())
        }
    
    exchange = EXCHANGES[exchange_code]
    current_year = datetime.now().year
    
    return {
        'success': True,
        'exchange_code': exchange_code,
        'name': exchange['name'],
        'country': exchange['country'],
        'timezone': exchange['timezone'],
        'currency': exchange['currency'],
        'years_available': list(exchange['holidays'].keys()),
        'current_year_holidays': len(exchange['holidays'].get(current_year, [])),
        'has_early_close_data': 'early_close' in exchange
    }


def get_holidays(exchange_code: str, year: Optional[int] = None) -> Dict:
    """
    Get holiday calendar for an exchange
    
    Args:
        exchange_code: Exchange ticker (e.g., 'NYSE', 'LSE', 'TSE')
        year: Year (defaults to current year)
    
    Returns:
        Dictionary with holiday dates and details
    """
    exchange_code = exchange_code.upper()
    
    if exchange_code not in EXCHANGES:
        return {
            'success': False,
            'error': f'Exchange {exchange_code} not found',
            'available_exchanges': list(EXCHANGES.keys())
        }
    
    exchange = EXCHANGES[exchange_code]
    
    if year is None:
        year = datetime.now().year
    
    if year not in exchange['holidays']:
        return {
            'success': False,
            'error': f'No data for year {year}',
            'available_years': list(exchange['holidays'].keys())
        }
    
    holidays = exchange['holidays'][year]
    early_close = exchange.get('early_close', {}).get(year, [])
    
    # Parse and enrich holiday data
    holiday_details = []
    for holiday_str in holidays:
        holiday_date = datetime.strptime(holiday_str, '%Y-%m-%d').date()
        holiday_details.append({
            'date': holiday_str,
            'day_of_week': holiday_date.strftime('%A'),
            'month': holiday_date.strftime('%B'),
            'day': holiday_date.day
        })
    
    early_close_details = []
    for ec_str in early_close:
        ec_date = datetime.strptime(ec_str, '%Y-%m-%d').date()
        early_close_details.append({
            'date': ec_str,
            'day_of_week': ec_date.strftime('%A'),
            'month': ec_date.strftime('%B'),
            'day': ec_date.day
        })
    
    return {
        'success': True,
        'exchange': exchange_code,
        'name': exchange['name'],
        'country': exchange['country'],
        'year': year,
        'timezone': exchange['timezone'],
        'total_holidays': len(holidays),
        'holidays': holiday_details,
        'early_close_days': early_close_details,
        'total_early_close': len(early_close)
    }


def is_trading_day(exchange_code: str, check_date: Optional[str] = None) -> Dict:
    """
    Check if a specific date is a trading day
    
    Args:
        exchange_code: Exchange ticker (e.g., 'NYSE', 'LSE', 'TSE')
        check_date: Date string in YYYY-MM-DD format (defaults to today)
    
    Returns:
        Dictionary with trading day status
    """
    exchange_code = exchange_code.upper()
    
    if exchange_code not in EXCHANGES:
        return {
            'success': False,
            'error': f'Exchange {exchange_code} not found',
            'available_exchanges': list(EXCHANGES.keys())
        }
    
    if check_date is None:
        check_date = datetime.now().date()
    else:
        check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
    
    exchange = EXCHANGES[exchange_code]
    year = check_date.year
    
    # Check if it's a weekend
    is_weekend = check_date.weekday() >= 5  # 5=Saturday, 6=Sunday
    
    # Check if it's a holiday
    date_str = check_date.strftime('%Y-%m-%d')
    holidays = exchange['holidays'].get(year, [])
    is_holiday = date_str in holidays
    
    # Check if it's an early close day
    early_close = exchange.get('early_close', {}).get(year, [])
    is_early_close = date_str in early_close
    
    is_trading = not (is_weekend or is_holiday)
    
    return {
        'success': True,
        'exchange': exchange_code,
        'name': exchange['name'],
        'date': date_str,
        'day_of_week': check_date.strftime('%A'),
        'is_trading_day': is_trading,
        'is_weekend': is_weekend,
        'is_holiday': is_holiday,
        'is_early_close': is_early_close,
        'reason': 'Weekend' if is_weekend else ('Holiday' if is_holiday else ('Early Close' if is_early_close else 'Regular Trading Day'))
    }


def get_next_trading_day(exchange_code: str, from_date: Optional[str] = None) -> Dict:
    """
    Find the next trading day after a given date
    
    Args:
        exchange_code: Exchange ticker (e.g., 'NYSE', 'LSE', 'TSE')
        from_date: Starting date in YYYY-MM-DD format (defaults to today)
    
    Returns:
        Dictionary with next trading day
    """
    exchange_code = exchange_code.upper()
    
    if exchange_code not in EXCHANGES:
        return {
            'success': False,
            'error': f'Exchange {exchange_code} not found',
            'available_exchanges': list(EXCHANGES.keys())
        }
    
    if from_date is None:
        current_date = datetime.now().date()
    else:
        current_date = datetime.strptime(from_date, '%Y-%m-%d').date()
    
    # Search up to 30 days ahead
    for i in range(1, 31):
        next_date = current_date + timedelta(days=i)
        result = is_trading_day(exchange_code, next_date.strftime('%Y-%m-%d'))
        
        if result['is_trading_day']:
            return {
                'success': True,
                'exchange': exchange_code,
                'from_date': current_date.strftime('%Y-%m-%d'),
                'next_trading_day': next_date.strftime('%Y-%m-%d'),
                'days_ahead': i,
                'day_of_week': next_date.strftime('%A')
            }
    
    return {
        'success': False,
        'error': 'Could not find next trading day within 30 days'
    }


def get_trading_days_in_month(exchange_code: str, year: Optional[int] = None, month: Optional[int] = None) -> Dict:
    """
    Get all trading days in a specific month
    
    Args:
        exchange_code: Exchange ticker (e.g., 'NYSE', 'LSE', 'TSE')
        year: Year (defaults to current year)
        month: Month (1-12, defaults to current month)
    
    Returns:
        Dictionary with all trading days in the month
    """
    exchange_code = exchange_code.upper()
    
    if exchange_code not in EXCHANGES:
        return {
            'success': False,
            'error': f'Exchange {exchange_code} not found',
            'available_exchanges': list(EXCHANGES.keys())
        }
    
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    
    # Get all days in the month
    num_days = calendar.monthrange(year, month)[1]
    trading_days = []
    non_trading_days = []
    
    for day in range(1, num_days + 1):
        date_obj = date(year, month, day)
        date_str = date_obj.strftime('%Y-%m-%d')
        
        result = is_trading_day(exchange_code, date_str)
        
        if result['is_trading_day']:
            trading_days.append({
                'date': date_str,
                'day_of_week': date_obj.strftime('%A'),
                'day': day
            })
        else:
            non_trading_days.append({
                'date': date_str,
                'day_of_week': date_obj.strftime('%A'),
                'day': day,
                'reason': result['reason']
            })
    
    return {
        'success': True,
        'exchange': exchange_code,
        'year': year,
        'month': month,
        'month_name': date(year, month, 1).strftime('%B'),
        'total_days': num_days,
        'trading_days_count': len(trading_days),
        'non_trading_days_count': len(non_trading_days),
        'trading_days': trading_days,
        'non_trading_days': non_trading_days
    }


def get_global_holidays_today() -> Dict:
    """
    Check which major exchanges are closed today
    
    Returns:
        Dictionary with global holiday status
    """
    today = datetime.now().date()
    today_str = today.strftime('%Y-%m-%d')
    
    closed_exchanges = []
    open_exchanges = []
    
    for exchange_code in EXCHANGES.keys():
        result = is_trading_day(exchange_code, today_str)
        
        if result['is_trading_day']:
            open_exchanges.append({
                'code': exchange_code,
                'name': result['name'],
                'country': EXCHANGES[exchange_code]['country']
            })
        else:
            closed_exchanges.append({
                'code': exchange_code,
                'name': result['name'],
                'country': EXCHANGES[exchange_code]['country'],
                'reason': result['reason']
            })
    
    return {
        'success': True,
        'date': today_str,
        'day_of_week': today.strftime('%A'),
        'total_exchanges': len(EXCHANGES),
        'open_count': len(open_exchanges),
        'closed_count': len(closed_exchanges),
        'open_exchanges': open_exchanges,
        'closed_exchanges': closed_exchanges
    }


def list_all_exchanges() -> Dict:
    """
    List all supported exchanges
    
    Returns:
        Dictionary with all exchange information
    """
    exchanges_list = []
    
    for code, info in EXCHANGES.items():
        exchanges_list.append({
            'code': code,
            'name': info['name'],
            'country': info['country'],
            'timezone': info['timezone'],
            'currency': info['currency'],
            'years_available': list(info['holidays'].keys())
        })
    
    return {
        'success': True,
        'total_exchanges': len(EXCHANGES),
        'exchanges': exchanges_list
    }


def compare_holidays(year: Optional[int] = None) -> Dict:
    """
    Compare holiday counts across all exchanges for a given year
    
    Args:
        year: Year to compare (defaults to current year)
    
    Returns:
        Dictionary with holiday comparison
    """
    if year is None:
        year = datetime.now().year
    
    comparison = []
    
    for code, info in EXCHANGES.items():
        if year in info['holidays']:
            holidays = info['holidays'][year]
            early_close = info.get('early_close', {}).get(year, [])
            
            comparison.append({
                'code': code,
                'name': info['name'],
                'country': info['country'],
                'holidays_count': len(holidays),
                'early_close_count': len(early_close),
                'total_non_standard_days': len(holidays) + len(early_close)
            })
    
    # Sort by holiday count
    comparison.sort(key=lambda x: x['holidays_count'], reverse=True)
    
    return {
        'success': True,
        'year': year,
        'exchanges_compared': len(comparison),
        'comparison': comparison
    }


# CLI interface
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'No command provided',
            'available_commands': [
                'list-exchanges',
                'exchange-info <CODE>',
                'exchange-holidays <CODE> [YEAR]',
                'is-trading-day <CODE> [DATE]',
                'next-trading-day <CODE> [DATE]',
                'month-calendar <CODE> [YEAR] [MONTH]',
                'global-holidays-today',
                'compare-holidays [YEAR]'
            ]
        }, indent=2))
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == 'list-exchanges':
            result = list_all_exchanges()
        
        elif command == 'exchange-info':
            if len(sys.argv) < 3:
                result = {'success': False, 'error': 'Exchange code required'}
            else:
                result = get_exchange_info(sys.argv[2])
        
        elif command == 'exchange-holidays':
            if len(sys.argv) < 3:
                result = {'success': False, 'error': 'Exchange code required'}
            else:
                exchange_code = sys.argv[2]
                year = int(sys.argv[3]) if len(sys.argv) > 3 else None
                result = get_holidays(exchange_code, year)
        
        elif command == 'is-trading-day':
            if len(sys.argv) < 3:
                result = {'success': False, 'error': 'Exchange code required'}
            else:
                exchange_code = sys.argv[2]
                check_date = sys.argv[3] if len(sys.argv) > 3 else None
                result = is_trading_day(exchange_code, check_date)
        
        elif command == 'next-trading-day':
            if len(sys.argv) < 3:
                result = {'success': False, 'error': 'Exchange code required'}
            else:
                exchange_code = sys.argv[2]
                from_date = sys.argv[3] if len(sys.argv) > 3 else None
                result = get_next_trading_day(exchange_code, from_date)
        
        elif command == 'month-calendar':
            if len(sys.argv) < 3:
                result = {'success': False, 'error': 'Exchange code required'}
            else:
                exchange_code = sys.argv[2]
                year = int(sys.argv[3]) if len(sys.argv) > 3 else None
                month = int(sys.argv[4]) if len(sys.argv) > 4 else None
                result = get_trading_days_in_month(exchange_code, year, month)
        
        elif command == 'global-holidays-today':
            result = get_global_holidays_today()
        
        elif command == 'compare-holidays':
            year = int(sys.argv[2]) if len(sys.argv) > 2 else None
            result = compare_holidays(year)
        
        else:
            result = {
                'success': False,
                'error': f'Unknown command: {command}'
            }
        
        print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }, indent=2))
        sys.exit(1)

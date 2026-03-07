#!/usr/bin/env python3
"""
Swiss National Bank Data Feed

Access Swiss National Bank (SNB) economic data including exchange rates,
interest rates, gold reserves, and balance sheet statistics via their
SDMX REST API.

Key data categories:
- CHF exchange rates (EUR, USD, GBP, JPY and more)
- SNB policy rates and money market rates (SARON, SOFR, etc.)
- SNB balance sheet statistics
- Monetary base

Source: https://data.snb.ch/en
API Docs: https://data.snb.ch/en/topics/snb#!/doc
Category: Macro / Central Banks
Free tier: True (no API key required)
Update frequency: Daily/Monthly
Author: QuantClaw Data NightBuilder
"""

import requests
import csv
from io import StringIO
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# SNB API Configuration
SNB_BASE_URL = "https://data.snb.ch/api/cube"
SNB_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ========== SNB DATA CUBE REGISTRY ==========

SNB_CUBES = {
    # ===== EXCHANGE RATES =====
    'EXCHANGE_RATES': {
        'devkum': 'CHF Exchange Rates (Monthly - M0: end-of-month, M1: monthly average)',
        'devkua': 'CHF Exchange Rates (Annual)',
    },
    
    # ===== INTEREST RATES =====
    'INTEREST_RATES': {
        'zimoma': 'Money Market Rates (SARON, SOFR, SONIA, EURIBOR, etc.)',
    },
    
    # ===== BALANCE SHEET =====
    'BALANCE_SHEET': {
        'snbbipo': 'SNB Balance Sheet Positions (millions CHF)',
        'snbmoba': 'SNB Monetary Base',
    },
}


def get_snb_cube_csv(cube_id: str, lang: str = 'en') -> Dict:
    """
    Fetch SNB data cube as CSV and parse
    
    Args:
        cube_id: SNB cube identifier (e.g., 'devkum', 'zimoma')
        lang: Language code ('en', 'de', 'fr', 'it')
    
    Returns:
        Dict with parsed CSV data or error
    """
    try:
        url = f"{SNB_BASE_URL}/{cube_id}/data/csv/{lang}"
        
        response = requests.get(url, headers=SNB_HEADERS, timeout=20)
        response.raise_for_status()
        
        # Parse CSV
        csv_text = response.text
        lines = csv_text.strip().split('\n')
        
        # Find where data starts (after metadata rows)
        data_start = 0
        metadata = {}
        for i, line in enumerate(lines):
            if line.startswith('"CubeId"'):
                parts = line.split(';')
                if len(parts) >= 2:
                    metadata['cube_id'] = parts[1].strip('"')
            elif line.startswith('"PublishingDate"'):
                parts = line.split(';')
                if len(parts) >= 2:
                    metadata['publishing_date'] = parts[1].strip('"')
            elif line.startswith('"Date"'):
                data_start = i
                break
        
        if data_start == 0:
            return {
                "success": False,
                "error": "Could not find data section in CSV",
                "cube_id": cube_id
            }
        
        # Parse data rows
        csv_reader = csv.DictReader(StringIO('\n'.join(lines[data_start:])), delimiter=';')
        rows = []
        for row in csv_reader:
            # Clean quotes from values
            cleaned_row = {k.strip('"'): v.strip('"') for k, v in row.items()}
            # Only include rows with values
            if cleaned_row.get('Value'):
                rows.append(cleaned_row)
        
        return {
            "success": True,
            "cube_id": cube_id,
            "metadata": metadata,
            "rows": rows,
            "count": len(rows),
            "columns": list(rows[0].keys()) if rows else []
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "cube_id": cube_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Parse error: {str(e)}",
            "cube_id": cube_id
        }


def parse_snb_value(value_str: str) -> Optional[float]:
    """
    Parse SNB value string to float
    
    Args:
        value_str: Value string from SNB CSV
    
    Returns:
        Float value or None if invalid
    """
    try:
        if not value_str or value_str == '':
            return None
        cleaned = value_str.replace("'", "").replace(",", "").strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def get_exchange_rate(currency: str = 'USD', monthly: bool = True, lookback_months: int = 12) -> Dict:
    """
    Get CHF exchange rate for specified currency
    
    Args:
        currency: Currency code (USD, EUR, GBP, JPY, etc.)
        monthly: If True, use monthly data (devkum), else annual (devkua)
        lookback_months: Months of history to include (for monthly data)
    
    Returns:
        Dict with latest rate, historical data, and changes
    """
    cube_id = 'devkum' if monthly else 'devkua'
    currency_code = f"{currency.upper()}1" if currency.upper() != 'JPY' else 'JPY100'
    
    data = get_snb_cube_csv(cube_id)
    
    if not data['success']:
        return data
    
    # Filter for specific currency and M0 (end-of-month) if monthly
    if monthly:
        filtered = [r for r in data['rows'] if r.get('D0') == 'M0' and r.get('D1') == currency_code]
    else:
        filtered = [r for r in data['rows'] if r.get('D1') == currency_code]
    
    if not filtered:
        return {
            "success": False,
            "error": f"No data found for currency {currency}",
            "cube_id": cube_id
        }
    
    # Parse values
    series = []
    for row in filtered:
        val = parse_snb_value(row.get('Value', ''))
        if val is not None:
            series.append({
                'date': row['Date'],
                'value': val
            })
    
    if not series:
        return {
            "success": False,
            "error": "No valid values found",
            "currency": currency
        }
    
    # Sort by date
    series.sort(key=lambda x: x['date'])
    
    # Get recent data
    recent = series[-lookback_months:] if lookback_months > 0 else series
    latest = recent[-1]
    
    # Calculate changes
    changes = {}
    if len(recent) >= 2:
        prev = recent[-2]['value']
        changes['period_change'] = latest['value'] - prev
        changes['period_change_pct'] = ((latest['value'] - prev) / prev * 100) if prev != 0 else 0
    
    if len(recent) >= 6:
        six_months_ago = recent[-6]['value']
        changes['6m_change'] = latest['value'] - six_months_ago
        changes['6m_change_pct'] = ((latest['value'] - six_months_ago) / six_months_ago * 100) if six_months_ago != 0 else 0
    
    if len(recent) >= 12:
        year_ago = recent[-12]['value']
        changes['yoy_change'] = latest['value'] - year_ago
        changes['yoy_change_pct'] = ((latest['value'] - year_ago) / year_ago * 100) if year_ago != 0 else 0
    
    return {
        "success": True,
        "currency_pair": f"CHF/{currency.upper()}",
        "rate_type": "Monthly (end-of-month)" if monthly else "Annual",
        "latest_rate": latest['value'],
        "latest_date": latest['date'],
        "interpretation": f"1 {currency.upper()} = {latest['value']:.5f} CHF",
        "changes": changes,
        "historical": recent[-12:],
        "source": "Swiss National Bank",
        "cube_id": cube_id,
        "timestamp": datetime.now().isoformat()
    }


def get_interest_rates(rate_type: str = 'SARON', lookback_months: int = 12) -> Dict:
    """
    Get money market interest rates from SNB
    
    Args:
        rate_type: Rate identifier (SARON, SOFR, SONIA, EURIBOR, ESTR, TONA, etc.)
        lookback_months: Months of history
    
    Returns:
        Dict with current rate and historical data
    """
    data = get_snb_cube_csv('zimoma')
    
    if not data['success']:
        return data
    
    # Filter for specific rate
    filtered = [r for r in data['rows'] if r.get('D0') == rate_type.upper()]
    
    if not filtered:
        return {
            "success": False,
            "error": f"No data found for rate type {rate_type}. Available types: SARON, SOFR, SONIA, EURIBOR, ESTR, TONA",
            "cube_id": "zimoma"
        }
    
    # Parse values
    series = []
    for row in filtered:
        val = parse_snb_value(row.get('Value', ''))
        if val is not None:
            series.append({
                'date': row['Date'],
                'value': val
            })
    
    if not series:
        return {
            "success": False,
            "error": "No valid values found",
            "rate_type": rate_type
        }
    
    series.sort(key=lambda x: x['date'])
    recent = series[-lookback_months:] if lookback_months > 0 else series
    latest = recent[-1]
    
    # Calculate changes
    changes = {}
    if len(recent) >= 2:
        prev = recent[-2]['value']
        changes['period_change'] = latest['value'] - prev
        changes['period_change_bps'] = (latest['value'] - prev) * 100
    
    if len(recent) >= 12:
        year_ago = recent[-12]['value']
        changes['yoy_change'] = latest['value'] - year_ago
        changes['yoy_change_bps'] = (latest['value'] - year_ago) * 100
    
    return {
        "success": True,
        "rate_type": rate_type.upper(),
        "latest_rate_pct": latest['value'],
        "latest_date": latest['date'],
        "changes": changes,
        "historical": recent[-12:],
        "source": "Swiss National Bank",
        "cube_id": "zimoma",
        "timestamp": datetime.now().isoformat()
    }


def get_balance_sheet(lookback_months: int = 12) -> Dict:
    """
    Get SNB balance sheet positions
    
    Args:
        lookback_months: Months of history
    
    Returns:
        Dict with balance sheet items in millions CHF
    """
    data = get_snb_cube_csv('snbbipo')
    
    if not data['success']:
        return data
    
    # Group by date, get all items for recent dates
    by_date = {}
    for row in data['rows']:
        date = row['Date']
        item = row.get('D0', '')
        val = parse_snb_value(row.get('Value', ''))
        
        if date not in by_date:
            by_date[date] = {}
        
        if val is not None:
            by_date[date][item] = val
    
    # Sort dates and get recent
    sorted_dates = sorted(by_date.keys())
    recent_dates = sorted_dates[-lookback_months:] if lookback_months > 0 else sorted_dates
    
    latest_date = recent_dates[-1]
    latest_items = by_date[latest_date]
    
    # Calculate total if 'T0' or 'T1' available (total assets/liabilities)
    total_assets = latest_items.get('T0') or latest_items.get('T1')
    
    return {
        "success": True,
        "latest_date": latest_date,
        "total_assets_chf_m": total_assets,
        "latest_positions": latest_items,
        "historical_dates": recent_dates,
        "source": "Swiss National Bank",
        "cube_id": "snbbipo",
        "note": "Values in millions CHF",
        "timestamp": datetime.now().isoformat()
    }


def get_snb_snapshot() -> Dict:
    """
    Get comprehensive SNB data snapshot
    
    Returns:
        Dict with key metrics across all categories
    """
    snapshot = {}
    
    # Exchange rates
    for currency in ['USD', 'EUR']:
        fx_data = get_exchange_rate(currency, lookback_months=3)
        if fx_data['success']:
            snapshot[f'CHF_{currency}'] = {
                'rate': fx_data['latest_rate'],
                'date': fx_data['latest_date'],
                'interpretation': fx_data['interpretation'],
                'month_change_pct': fx_data['changes'].get('period_change_pct')
            }
    
    # SARON rate (SNB's reference rate)
    saron = get_interest_rates('SARON', lookback_months=3)
    if saron['success']:
        snapshot['SARON'] = {
            'rate_pct': saron['latest_rate_pct'],
            'date': saron['latest_date'],
            'month_change_bps': saron['changes'].get('period_change_bps')
        }
    
    # Balance sheet
    bs = get_balance_sheet(lookback_months=3)
    if bs['success']:
        snapshot['balance_sheet'] = {
            'total_assets_chf_m': bs.get('total_assets_chf_m'),
            'date': bs['latest_date']
        }
    
    return {
        'success': True,
        'snb_snapshot': snapshot,
        'timestamp': datetime.now().isoformat(),
        'source': 'Swiss National Bank'
    }


def list_all_cubes() -> Dict:
    """
    List all available SNB data cubes
    
    Returns:
        Dict with all cubes organized by category
    """
    all_cubes = {}
    total_count = 0
    
    for category, cubes_dict in SNB_CUBES.items():
        all_cubes[category] = {
            'count': len(cubes_dict),
            'cubes': [{'id': cid, 'name': name} for cid, name in cubes_dict.items()]
        }
        total_count += len(cubes_dict)
    
    return {
        'success': True,
        'total_cubes': total_count,
        'categories': all_cubes,
        'module': 'swiss_national_bank_data_feed',
        'note': 'All data is freely available without API key'
    }


if __name__ == "__main__":
    import json
    
    print("=" * 60)
    print("Swiss National Bank Data Feed")
    print("=" * 60)
    
    # Show available cubes
    cubes = list_all_cubes()
    print(f"\nTotal Data Cubes: {cubes['total_cubes']}")
    print("\nCategories:")
    for cat, info in cubes['categories'].items():
        print(f"  {cat}: {info['count']} cubes")
    
    print("\n" + json.dumps(cubes, indent=2))

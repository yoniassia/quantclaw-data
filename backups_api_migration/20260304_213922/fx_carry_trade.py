#!/usr/bin/env python3
"""
FX Carry Trade Monitor Module — Phase 182

Monitor interest rate differentials and carry trade opportunities across currency pairs
Calculate carry returns, risk-adjusted carry (Sharpe ratios), and identify optimal FX carry strategies

Data Sources:
- FRED API: Major currency interest rates (3M rates for accurate carry calculation)
- Central Bank Rates module: Policy rates for 40+ central banks
- Historical FX rate data for carry return calculation

Carry Trade Logic:
- Borrow in low-yielding currency, invest in high-yielding currency
- Profit = Interest Rate Differential - FX Depreciation - Transaction Costs
- Risk-adjusted carry = (Rate Differential) / (FX Volatility)

Author: QUANTCLAW DATA Build Agent
Phase: 182
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import statistics

# FRED API Configuration
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = ""  # Public access, no key required

# Major FX pairs and their 3-month interest rate series
CURRENCY_RATES = {
    'USD': {
        'name': 'US Dollar',
        'series_id': 'DGS3MO',  # 3-Month Treasury
        'alt_series': 'DTB3',    # 3-Month T-Bill (secondary)
        'symbol': '$'
    },
    'EUR': {
        'name': 'Euro',
        'series_id': 'IR3TIB01EZM156N',  # Euro 3-Month Interbank
        'symbol': '€'
    },
    'JPY': {
        'name': 'Japanese Yen',
        'series_id': 'IR3TIB01JPM156N',  # Japan 3-Month Interbank
        'symbol': '¥'
    },
    'GBP': {
        'name': 'British Pound',
        'series_id': 'IR3TIB01GBM156N',  # UK 3-Month Interbank
        'symbol': '£'
    },
    'AUD': {
        'name': 'Australian Dollar',
        'series_id': 'IR3TIB01AUM156N',  # Australia 3-Month Interbank
        'symbol': 'A$'
    },
    'CAD': {
        'name': 'Canadian Dollar',
        'series_id': 'IR3TIB01CAM156N',  # Canada 3-Month Interbank
        'symbol': 'C$'
    },
    'CHF': {
        'name': 'Swiss Franc',
        'series_id': 'IR3TIB01CHM156N',  # Swiss 3-Month Interbank
        'symbol': 'Fr'
    },
    'NZD': {
        'name': 'New Zealand Dollar',
        'series_id': 'IR3TIB01NZM156N',  # NZ 3-Month Interbank
        'symbol': 'NZ$'
    },
    'SEK': {
        'name': 'Swedish Krona',
        'series_id': 'IR3TIB01SEM156N',  # Sweden 3-Month Interbank
        'symbol': 'kr'
    },
    'NOK': {
        'name': 'Norwegian Krone',
        'series_id': 'IR3TIB01NOM156N',  # Norway 3-Month Interbank
        'symbol': 'kr'
    }
}

# FX spot rate series (vs USD)
FX_SPOT_RATES = {
    'EUR': 'DEXUSEU',  # USD/EUR
    'JPY': 'DEXJPUS',  # USD/JPY
    'GBP': 'DEXUSUK',  # USD/GBP
    'AUD': 'DEXUSAL',  # USD/AUD
    'CAD': 'DEXCAUS',  # USD/CAD
    'CHF': 'DEXSZUS',  # USD/CHF
    'NZD': 'DEXUSNZ',  # USD/NZD
    'SEK': 'DEXSDUS',  # USD/SEK
    'NOK': 'DEXNOUS',  # USD/NOK
}


def fetch_fred_series(series_id: str, days_back: int = 90) -> Optional[List[Dict]]:
    """
    Fetch time series data from FRED
    
    Args:
        series_id: FRED series identifier
        days_back: Number of days of historical data
    
    Returns:
        List of {date, value} dicts, or None on error
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    url = f"{FRED_BASE_URL}/series/observations"
    params = {
        'series_id': series_id,
        'file_type': 'json',
        'observation_start': start_date.strftime('%Y-%m-%d'),
        'observation_end': end_date.strftime('%Y-%m-%d'),
        'sort_order': 'desc'
    }
    
    # Add API key only if configured
    if FRED_API_KEY:
        params['api_key'] = FRED_API_KEY
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'observations' in data:
            observations = []
            for obs in data['observations']:
                if obs['value'] != '.':
                    observations.append({
                        'date': obs['date'],
                        'value': float(obs['value'])
                    })
            return observations
        return None
    except Exception as e:
        print(f"Error fetching FRED series {series_id}: {e}", file=sys.stderr)
        return None


def get_current_interest_rate(currency: str) -> Optional[float]:
    """Get most recent 3-month interest rate for currency"""
    if currency not in CURRENCY_RATES:
        return None
    
    series_id = CURRENCY_RATES[currency]['series_id']
    data = fetch_fred_series(series_id, days_back=30)
    
    if data and len(data) > 0:
        return data[0]['value']
    
    # Try alternative series for USD
    if currency == 'USD' and 'alt_series' in CURRENCY_RATES[currency]:
        alt_data = fetch_fred_series(CURRENCY_RATES[currency]['alt_series'], days_back=30)
        if alt_data and len(alt_data) > 0:
            return alt_data[0]['value']
    
    return None


def get_fx_spot_rate(currency: str) -> Optional[float]:
    """Get current FX spot rate vs USD"""
    if currency == 'USD':
        return 1.0
    
    if currency not in FX_SPOT_RATES:
        return None
    
    series_id = FX_SPOT_RATES[currency]
    data = fetch_fred_series(series_id, days_back=7)
    
    if data and len(data) > 0:
        return data[0]['value']
    
    return None


def calculate_fx_volatility(currency: str, days: int = 90) -> Optional[float]:
    """Calculate annualized FX volatility from daily returns"""
    if currency == 'USD':
        return 0.0  # USD vs USD has zero volatility
    
    if currency not in FX_SPOT_RATES:
        return None
    
    series_id = FX_SPOT_RATES[currency]
    data = fetch_fred_series(series_id, days_back=days)
    
    if not data or len(data) < 20:
        return None
    
    # Calculate daily returns
    returns = []
    for i in range(len(data) - 1):
        if data[i]['value'] > 0 and data[i+1]['value'] > 0:
            ret = (data[i]['value'] - data[i+1]['value']) / data[i+1]['value']
            returns.append(ret)
    
    if len(returns) < 10:
        return None
    
    # Annualized volatility (daily std * sqrt(252 trading days))
    std_dev = statistics.stdev(returns)
    annualized_vol = std_dev * (252 ** 0.5) * 100  # As percentage
    
    return round(annualized_vol, 2)


def get_carry_trade_opportunities(min_differential: float = 1.0) -> List[Dict]:
    """
    Identify carry trade opportunities across currency pairs
    
    Args:
        min_differential: Minimum interest rate differential (in %)
    
    Returns:
        List of carry trade opportunities, sorted by risk-adjusted carry
    """
    opportunities = []
    
    # Get all current rates
    rates = {}
    for currency in CURRENCY_RATES.keys():
        rate = get_current_interest_rate(currency)
        if rate is not None:
            rates[currency] = rate
    
    # Calculate all possible pairs
    currencies = list(rates.keys())
    for i, fund_ccy in enumerate(currencies):
        for invest_ccy in currencies[i+1:]:
            # Calculate carry (borrow fund_ccy, invest invest_ccy)
            differential_1 = rates[invest_ccy] - rates[fund_ccy]
            differential_2 = rates[fund_ccy] - rates[invest_ccy]
            
            # Check both directions
            for diff, funding, investment in [
                (differential_1, fund_ccy, invest_ccy),
                (differential_2, invest_ccy, fund_ccy)
            ]:
                if diff >= min_differential:
                    # Get FX volatility
                    # For carry trade, we care about volatility of investment currency
                    vol = calculate_fx_volatility(investment)
                    
                    # Calculate risk-adjusted carry (Sharpe-like ratio)
                    risk_adjusted = diff / vol if vol and vol > 0 else 0
                    
                    opportunity = {
                        'pair': f"{funding}/{investment}",
                        'funding_currency': funding,
                        'funding_currency_name': CURRENCY_RATES[funding]['name'],
                        'funding_rate': round(rates[funding], 2),
                        'investment_currency': investment,
                        'investment_currency_name': CURRENCY_RATES[investment]['name'],
                        'investment_rate': round(rates[investment], 2),
                        'rate_differential': round(diff, 2),
                        'fx_volatility': vol,
                        'risk_adjusted_carry': round(risk_adjusted, 3) if risk_adjusted else None,
                        'annual_carry_pct': round(diff, 2)  # Simplified, assuming no FX movement
                    }
                    opportunities.append(opportunity)
    
    # Sort by risk-adjusted carry (highest first)
    opportunities.sort(key=lambda x: x['risk_adjusted_carry'] or 0, reverse=True)
    
    return opportunities


def get_rate_differential(currency1: str, currency2: str) -> Dict:
    """
    Calculate interest rate differential between two currencies
    
    Args:
        currency1: First currency code
        currency2: Second currency code
    
    Returns:
        Detailed differential analysis
    """
    rate1 = get_current_interest_rate(currency1)
    rate2 = get_current_interest_rate(currency2)
    
    if rate1 is None or rate2 is None:
        return {
            'error': 'Unable to fetch rates for one or both currencies',
            'currency1': currency1,
            'currency2': currency2
        }
    
    differential = rate2 - rate1
    
    # Get FX data
    spot1 = get_fx_spot_rate(currency1)
    spot2 = get_fx_spot_rate(currency2)
    vol1 = calculate_fx_volatility(currency1)
    vol2 = calculate_fx_volatility(currency2)
    
    # Determine carry trade direction
    if differential > 0:
        funding = currency1
        investment = currency2
        carry = differential
    else:
        funding = currency2
        investment = currency1
        carry = abs(differential)
    
    # Risk-adjusted carry
    vol = vol2 if investment == currency2 else vol1
    risk_adjusted = carry / vol if vol and vol > 0 else None
    
    return {
        'currency1': currency1,
        'currency1_name': CURRENCY_RATES[currency1]['name'],
        'currency1_rate': round(rate1, 2),
        'currency2': currency2,
        'currency2_name': CURRENCY_RATES[currency2]['name'],
        'currency2_rate': round(rate2, 2),
        'rate_differential': round(differential, 2),
        'absolute_differential': round(abs(differential), 2),
        'carry_trade_direction': f"Borrow {funding}, Invest {investment}",
        'annual_carry_pct': round(carry, 2),
        'funding_currency': funding,
        'investment_currency': investment,
        'fx_volatility': vol,
        'risk_adjusted_carry': round(risk_adjusted, 3) if risk_adjusted else None,
        'spot_rate_usd': {
            currency1: spot1,
            currency2: spot2
        }
    }


def get_top_funding_currencies(n: int = 3) -> List[Dict]:
    """Get currencies with lowest interest rates (best for funding carry trades)"""
    rates = []
    
    for currency, info in CURRENCY_RATES.items():
        rate = get_current_interest_rate(currency)
        if rate is not None:
            rates.append({
                'currency': currency,
                'name': info['name'],
                'rate': round(rate, 2),
                'symbol': info['symbol']
            })
    
    # Sort by rate (lowest first)
    rates.sort(key=lambda x: x['rate'])
    
    return rates[:n]


def get_top_investment_currencies(n: int = 3) -> List[Dict]:
    """Get currencies with highest interest rates (best for investment side)"""
    rates = []
    
    for currency, info in CURRENCY_RATES.items():
        rate = get_current_interest_rate(currency)
        if rate is not None:
            rates.append({
                'currency': currency,
                'name': info['name'],
                'rate': round(rate, 2),
                'symbol': info['symbol']
            })
    
    # Sort by rate (highest first)
    rates.sort(key=lambda x: x['rate'], reverse=True)
    
    return rates[:n]


def get_fx_carry_dashboard() -> Dict:
    """
    Comprehensive FX carry trade dashboard
    
    Returns:
        Complete overview of carry trade landscape
    """
    # Get top opportunities
    opportunities = get_carry_trade_opportunities(min_differential=0.5)
    
    # Get best funding and investment currencies
    funding = get_top_funding_currencies(3)
    investment = get_top_investment_currencies(3)
    
    # Calculate global carry trade index (average differential of top 5 trades)
    avg_carry = sum(opp['rate_differential'] for opp in opportunities[:5]) / 5 if len(opportunities) >= 5 else 0
    avg_risk_adjusted = sum(opp['risk_adjusted_carry'] for opp in opportunities[:5] if opp['risk_adjusted_carry']) / 5 if len(opportunities) >= 5 else 0
    
    return {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_opportunities': len(opportunities),
            'avg_carry_top5': round(avg_carry, 2),
            'avg_risk_adjusted_top5': round(avg_risk_adjusted, 3),
            'best_funding_currencies': [f"{c['currency']} ({c['rate']}%)" for c in funding],
            'best_investment_currencies': [f"{c['currency']} ({c['rate']}%)" for c in investment]
        },
        'top_opportunities': opportunities[:10],
        'funding_currencies': funding,
        'investment_currencies': investment,
        'all_opportunities': opportunities
    }


def main():
    """CLI interface for FX carry trade monitor"""
    if len(sys.argv) < 2:
        print("Usage: python cli.py <command> [args]")
        print("\nCommands:")
        print("  carry-opportunities [min_diff]   - List carry trade opportunities (default min_diff=1.0)")
        print("  carry-differential CUR1 CUR2     - Calculate rate differential between two currencies")
        print("  carry-dashboard                  - Full carry trade dashboard")
        print("  carry-funding [n]                - Top N funding currencies (default n=3)")
        print("  carry-investment [n]             - Top N investment currencies (default n=3)")
        print("\nAvailable currencies:", ', '.join(CURRENCY_RATES.keys()))
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command in ['opportunities', 'carry-opportunities']:
        min_diff = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
        opportunities = get_carry_trade_opportunities(min_differential=min_diff)
        print(json.dumps(opportunities, indent=2))
    
    elif command in ['differential', 'carry-differential']:
        if len(sys.argv) < 4:
            print("Error: differential requires two currency codes")
            print("Usage: python cli.py carry-differential CUR1 CUR2")
            sys.exit(1)
        
        ccy1 = sys.argv[2].upper()
        ccy2 = sys.argv[3].upper()
        
        result = get_rate_differential(ccy1, ccy2)
        print(json.dumps(result, indent=2))
    
    elif command in ['dashboard', 'carry-dashboard']:
        dashboard = get_fx_carry_dashboard()
        print(json.dumps(dashboard, indent=2))
    
    elif command in ['funding', 'carry-funding']:
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        funding = get_top_funding_currencies(n)
        print(json.dumps(funding, indent=2))
    
    elif command in ['investment', 'carry-investment']:
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        investment = get_top_investment_currencies(n)
        print(json.dumps(investment, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()

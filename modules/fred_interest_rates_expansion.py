"""
FRED Interest Rates Expansion Module

Advanced interest rate analytics beyond the base fred.py module.
Covers international benchmark rates, real rates (TIPS), rate differentials
for carry trade analysis, swap rates, forward rate expectations, and
rate regime classification.

Complements: modules/fred.py (basic yields, fed rates, inflation, credit spreads)

Data Source: Federal Reserve Bank of St. Louis (FRED)
Update: Daily to weekly depending on series
Free: Yes (API key from FRED_API_KEY env var for higher limits)
API Docs: https://fred.stlouisfed.org/docs/api/fred.html
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# FRED API Configuration
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# Cache directory
CACHE_DIR = Path.home() / ".quantclaw" / "cache" / "fred_rates"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── Series Catalogs ──────────────────────────────────────────────────────────

# International benchmark/policy rates
INTERNATIONAL_RATES = {
    'FEDFUNDS': 'US Federal Funds Rate',
    'IRSTCB01GBM156N': 'UK Bank Rate',
    'ECBMLFR': 'ECB Marginal Lending Facility Rate',
    'ECBDFR': 'ECB Deposit Facility Rate',
    'IRSTCB01JPM156N': 'Japan Policy Rate',
    'IRSTCB01CAM156N': 'Canada Policy Rate',
    'IRSTCB01AUM156N': 'Australia Policy Rate',
    'IRSTCB01CHM156N': 'Switzerland Policy Rate',
    'IRSTCB01SEQ156N': 'Sweden Policy Rate',
    'IRSTCB01NZM156N': 'New Zealand Policy Rate',
}

# TIPS / Real rates
REAL_RATE_SERIES = {
    'DFII5': '5-Year TIPS Yield',
    'DFII7': '7-Year TIPS Yield',
    'DFII10': '10-Year TIPS Yield',
    'DFII20': '20-Year TIPS Yield',
    'DFII30': '30-Year TIPS Yield',
}

# Breakeven inflation
BREAKEVEN_SERIES = {
    'T5YIE': '5-Year Breakeven Inflation',
    'T10YIE': '10-Year Breakeven Inflation',
    'T5YIFR': '5-Year, 5-Year Forward Inflation Expectation',
}

# Interbank / short-term rates
SHORT_TERM_RATES = {
    'DFF': 'Effective Federal Funds Rate',
    'DFEDTARU': 'Fed Funds Target Upper',
    'DFEDTARL': 'Fed Funds Target Lower',
    'SOFR': 'Secured Overnight Financing Rate',
    'OBFR': 'Overnight Bank Funding Rate',
    'EFFR': 'Effective Federal Funds Rate (alt)',
    'AMERIBOR': 'AMERIBOR',
}

# Extended maturity yields (incl. real)
EXTENDED_YIELDS = {
    'DGS1MO': '1-Month Treasury',
    'DGS3MO': '3-Month Treasury',
    'DGS6MO': '6-Month Treasury',
    'DGS1': '1-Year Treasury',
    'DGS2': '2-Year Treasury',
    'DGS3': '3-Year Treasury',
    'DGS5': '5-Year Treasury',
    'DGS7': '7-Year Treasury',
    'DGS10': '10-Year Treasury',
    'DGS20': '20-Year Treasury',
    'DGS30': '30-Year Treasury',
}

# Carry-trade relevant pairs (target_rate, funding_rate)
CARRY_PAIRS = {
    'US_JP': ('FEDFUNDS', 'IRSTCB01JPM156N', 'USD/JPY carry'),
    'AU_JP': ('IRSTCB01AUM156N', 'IRSTCB01JPM156N', 'AUD/JPY carry'),
    'NZ_JP': ('IRSTCB01NZM156N', 'IRSTCB01JPM156N', 'NZD/JPY carry'),
    'US_CH': ('FEDFUNDS', 'IRSTCB01CHM156N', 'USD/CHF carry'),
    'AU_US': ('IRSTCB01AUM156N', 'FEDFUNDS', 'AUD/USD carry'),
    'US_GB': ('FEDFUNDS', 'IRSTCB01GBM156N', 'USD/GBP carry'),
}


# ── Core Helpers ─────────────────────────────────────────────────────────────

def _fred_get(endpoint: str, params: dict, timeout: int = 10) -> dict:
    """Make an authenticated FRED API request."""
    params['file_type'] = 'json'
    if FRED_API_KEY:
        params['api_key'] = FRED_API_KEY
    url = f"{FRED_BASE_URL}/{endpoint}"
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _fetch_observations(series_id: str,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        limit: int = 100,
                        sort_order: str = 'desc') -> List[dict]:
    """
    Fetch observation data for a FRED series, filtering missing values.

    Returns list of {'date': str, 'value': float} sorted ascending by date.
    """
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

    try:
        data = _fred_get('series/observations', {
            'series_id': series_id,
            'observation_start': start_date,
            'observation_end': end_date,
            'limit': limit,
            'sort_order': sort_order,
        })
    except requests.exceptions.RequestException:
        return []

    observations = []
    for obs in data.get('observations', []):
        if obs.get('value', '.') != '.':
            try:
                observations.append({'date': obs['date'], 'value': float(obs['value'])})
            except (ValueError, KeyError):
                continue
    observations.sort(key=lambda x: x['date'])
    return observations


def _latest_value(series_id: str) -> Optional[float]:
    """Get the most recent non-missing value for a series."""
    obs = _fetch_observations(series_id, limit=5, sort_order='desc')
    return obs[-1]['value'] if obs else None


def _cache_key(name: str) -> Path:
    return CACHE_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.json"


def _read_cache(name: str, max_age_hours: int = 6) -> Optional[dict]:
    path = _cache_key(name)
    if path.exists():
        age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
        if age < timedelta(hours=max_age_hours):
            with open(path) as f:
                return json.load(f)
    return None


def _write_cache(name: str, data: dict) -> None:
    with open(_cache_key(name), 'w') as f:
        json.dump(data, f)


# ── Public Functions ─────────────────────────────────────────────────────────

def get_international_rates() -> Dict:
    """
    Fetch latest central bank policy rates for major economies.

    Returns:
        dict: {
            'rates': {series_id: {'name': str, 'rate': float, 'date': str}, ...},
            'highest': {'country': str, 'rate': float},
            'lowest': {'country': str, 'rate': float},
            'as_of': str,
            'source': 'FRED'
        }
    """
    cached = _read_cache('intl_rates')
    if cached:
        return cached

    rates = {}
    for sid, name in INTERNATIONAL_RATES.items():
        obs = _fetch_observations(sid, limit=5, sort_order='desc')
        if obs:
            latest = obs[-1]
            rates[sid] = {'name': name, 'rate': latest['value'], 'date': latest['date']}

    sorted_rates = sorted(rates.values(), key=lambda x: x['rate'])
    result = {
        'rates': rates,
        'highest': {'country': sorted_rates[-1]['name'], 'rate': sorted_rates[-1]['rate']} if sorted_rates else None,
        'lowest': {'country': sorted_rates[0]['name'], 'rate': sorted_rates[0]['rate']} if sorted_rates else None,
        'as_of': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'source': 'FRED',
    }
    _write_cache('intl_rates', result)
    return result


def get_real_rates() -> Dict:
    """
    Fetch TIPS (real) yields across maturities and compute breakeven inflation.

    Returns:
        dict: {
            'real_yields': {maturity: float, ...},
            'breakevens': {term: float, ...},
            'forward_inflation': float or None,
            'real_10y': float or None,
            'source': 'FRED'
        }
    """
    cached = _read_cache('real_rates')
    if cached:
        return cached

    real_yields = {}
    for sid, name in REAL_RATE_SERIES.items():
        val = _latest_value(sid)
        if val is not None:
            real_yields[name] = val

    breakevens = {}
    for sid, name in BREAKEVEN_SERIES.items():
        val = _latest_value(sid)
        if val is not None:
            breakevens[name] = val

    fwd = breakevens.get('5-Year, 5-Year Forward Inflation Expectation')

    result = {
        'real_yields': real_yields,
        'breakevens': breakevens,
        'forward_inflation': fwd,
        'real_10y': real_yields.get('10-Year TIPS Yield'),
        'source': 'FRED',
    }
    _write_cache('real_rates', result)
    return result


def get_short_term_rates() -> Dict:
    """
    Fetch key short-term / overnight funding rates (SOFR, EFFR, OBFR, etc.).

    Returns:
        dict: {
            'rates': {name: {'value': float, 'date': str}, ...},
            'fed_target_range': {'lower': float, 'upper': float} or None,
            'sofr': float or None,
            'source': 'FRED'
        }
    """
    cached = _read_cache('short_term')
    if cached:
        return cached

    rates = {}
    for sid, name in SHORT_TERM_RATES.items():
        obs = _fetch_observations(sid, limit=5, sort_order='desc')
        if obs:
            latest = obs[-1]
            rates[name] = {'value': latest['value'], 'date': latest['date']}

    lower = rates.get('Fed Funds Target Lower', {}).get('value')
    upper = rates.get('Fed Funds Target Upper', {}).get('value')

    result = {
        'rates': rates,
        'fed_target_range': {'lower': lower, 'upper': upper} if lower and upper else None,
        'sofr': rates.get('Secured Overnight Financing Rate', {}).get('value'),
        'source': 'FRED',
    }
    _write_cache('short_term', result)
    return result


def get_carry_trade_differentials() -> Dict:
    """
    Calculate interest rate differentials for common carry-trade currency pairs.

    A positive differential means the target currency yields more than the
    funding currency — indicating potential carry-trade opportunity.

    Returns:
        dict: {
            'pairs': {pair_id: {'description': str, 'target_rate': float,
                                'funding_rate': float, 'differential': float}, ...},
            'best_carry': str,
            'source': 'FRED'
        }
    """
    cached = _read_cache('carry_diff')
    if cached:
        return cached

    pairs = {}
    best_pair = None
    best_diff = -999

    for pair_id, (target_sid, funding_sid, desc) in CARRY_PAIRS.items():
        t_val = _latest_value(target_sid)
        f_val = _latest_value(funding_sid)
        if t_val is not None and f_val is not None:
            diff = round(t_val - f_val, 4)
            pairs[pair_id] = {
                'description': desc,
                'target_rate': t_val,
                'funding_rate': f_val,
                'differential': diff,
            }
            if diff > best_diff:
                best_diff = diff
                best_pair = pair_id

    result = {
        'pairs': pairs,
        'best_carry': best_pair,
        'source': 'FRED',
    }
    _write_cache('carry_diff', result)
    return result


def get_rate_history(series_id: str,
                     years: int = 5,
                     frequency: str = 'daily') -> Dict:
    """
    Fetch historical interest rate data over a given lookback period.

    Args:
        series_id: FRED series ID (e.g. 'DGS10', 'FEDFUNDS')
        years: Lookback period in years (default 5)
        frequency: 'daily', 'weekly', or 'monthly'

    Returns:
        dict: {
            'series_id': str,
            'observations': [{'date': str, 'value': float}, ...],
            'count': int,
            'min': float, 'max': float, 'mean': float,
            'current': float or None,
            'source': 'FRED'
        }
    """
    start = (datetime.now() - timedelta(days=years * 365)).strftime('%Y-%m-%d')
    obs = _fetch_observations(series_id, start_date=start, limit=10000, sort_order='asc')

    if not obs:
        return {'error': f'No data for {series_id}', 'series_id': series_id, 'source': 'FRED'}

    values = [o['value'] for o in obs]
    result = {
        'series_id': series_id,
        'observations': obs,
        'count': len(obs),
        'min': round(min(values), 4),
        'max': round(max(values), 4),
        'mean': round(sum(values) / len(values), 4),
        'current': obs[-1]['value'],
        'start_date': obs[0]['date'],
        'end_date': obs[-1]['date'],
        'source': 'FRED',
    }
    return result


def get_rate_spread(series_a: str, series_b: str,
                    years: int = 2) -> Dict:
    """
    Compute the spread (A − B) between two rate series over time.

    Useful for: 10Y-2Y spread, nominal vs real, cross-country differentials.

    Args:
        series_a: FRED series ID for the long/target leg
        series_b: FRED series ID for the short/funding leg
        years: Lookback period (default 2)

    Returns:
        dict: {
            'series_a': str, 'series_b': str,
            'spread_data': [{'date': str, 'a': float, 'b': float, 'spread': float}, ...],
            'current_spread': float,
            'avg_spread': float,
            'min_spread': float,
            'max_spread': float,
            'source': 'FRED'
        }
    """
    start = (datetime.now() - timedelta(days=years * 365)).strftime('%Y-%m-%d')
    obs_a = {o['date']: o['value'] for o in _fetch_observations(series_a, start_date=start, limit=10000)}
    obs_b = {o['date']: o['value'] for o in _fetch_observations(series_b, start_date=start, limit=10000)}

    common_dates = sorted(set(obs_a.keys()) & set(obs_b.keys()))
    if not common_dates:
        return {'error': 'No overlapping dates', 'series_a': series_a, 'series_b': series_b, 'source': 'FRED'}

    spread_data = []
    for d in common_dates:
        spread_data.append({
            'date': d,
            'a': obs_a[d],
            'b': obs_b[d],
            'spread': round(obs_a[d] - obs_b[d], 4),
        })

    spreads = [s['spread'] for s in spread_data]
    return {
        'series_a': series_a,
        'series_b': series_b,
        'spread_data': spread_data,
        'current_spread': spreads[-1],
        'avg_spread': round(sum(spreads) / len(spreads), 4),
        'min_spread': round(min(spreads), 4),
        'max_spread': round(max(spreads), 4),
        'source': 'FRED',
    }


def get_extended_yield_curve(date: Optional[str] = None) -> Dict:
    """
    Full Treasury yield curve with 11 maturities (1M through 30Y)
    plus TIPS real-yield overlay.

    Args:
        date: Date in YYYY-MM-DD format (default: latest available)

    Returns:
        dict: {
            'date': str,
            'nominal': {maturity: float, ...},
            'real': {maturity: float, ...},
            'spreads': {'10Y-2Y': float, '10Y-3M': float, '30Y-5Y': float, ...},
            'curve_slope': float,
            'inverted': bool,
            'source': 'FRED'
        }
    """
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    start = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')

    nominal = {}
    for sid, name in EXTENDED_YIELDS.items():
        obs = _fetch_observations(sid, start_date=start, end_date=date, limit=5)
        if obs:
            nominal[name] = obs[-1]['value']

    real = {}
    for sid, name in REAL_RATE_SERIES.items():
        obs = _fetch_observations(sid, start_date=start, end_date=date, limit=5)
        if obs:
            real[name] = obs[-1]['value']

    # Key spreads
    spreads = {}
    n = nominal
    if '10-Year Treasury' in n and '2-Year Treasury' in n:
        spreads['10Y-2Y'] = round(n['10-Year Treasury'] - n['2-Year Treasury'], 4)
    if '10-Year Treasury' in n and '3-Month Treasury' in n:
        spreads['10Y-3M'] = round(n['10-Year Treasury'] - n['3-Month Treasury'], 4)
    if '30-Year Treasury' in n and '5-Year Treasury' in n:
        spreads['30Y-5Y'] = round(n['30-Year Treasury'] - n['5-Year Treasury'], 4)
    if '30-Year Treasury' in n and '2-Year Treasury' in n:
        spreads['30Y-2Y'] = round(n['30-Year Treasury'] - n['2-Year Treasury'], 4)

    # Curve slope: 30Y − 1MO (full curve steepness)
    curve_slope = None
    if '30-Year Treasury' in n and '1-Month Treasury' in n:
        curve_slope = round(n['30-Year Treasury'] - n['1-Month Treasury'], 4)

    inverted = any(v < 0 for v in spreads.values())

    return {
        'date': date,
        'nominal': nominal,
        'real': real,
        'spreads': spreads,
        'curve_slope': curve_slope,
        'inverted': inverted,
        'source': 'FRED',
    }


def classify_rate_regime() -> Dict:
    """
    Classify the current interest-rate environment into a regime.

    Regimes:
        - tightening: Rates rising, curve flattening
        - easing: Rates falling, curve steepening
        - neutral: Stable rates
        - inverted: Yield curve inverted (recession signal)

    Returns:
        dict: {
            'regime': str,
            'fed_rate': float,
            'curve_10y2y': float,
            'real_10y': float,
            'signals': [str, ...],
            'source': 'FRED'
        }
    """
    cached = _read_cache('regime')
    if cached:
        return cached

    signals = []

    # Current fed rate
    fed = _latest_value('FEDFUNDS')
    # 6-month-ago fed rate
    six_mo_ago = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    fed_hist = _fetch_observations('FEDFUNDS', start_date=six_mo_ago, limit=200)
    fed_6mo = fed_hist[0]['value'] if fed_hist else None

    # 10Y-2Y spread
    spread_10y2y = None
    v10 = _latest_value('DGS10')
    v2 = _latest_value('DGS2')
    if v10 is not None and v2 is not None:
        spread_10y2y = round(v10 - v2, 4)

    # Real 10Y
    real_10y = _latest_value('DFII10')

    # Classify
    regime = 'neutral'
    if fed is not None and fed_6mo is not None:
        delta = fed - fed_6mo
        if delta > 0.25:
            regime = 'tightening'
            signals.append(f'Fed rate rose {delta:.2f}% in 6 months')
        elif delta < -0.25:
            regime = 'easing'
            signals.append(f'Fed rate fell {abs(delta):.2f}% in 6 months')
        else:
            signals.append('Fed rate stable over 6 months')

    if spread_10y2y is not None:
        if spread_10y2y < 0:
            regime = 'inverted'
            signals.append(f'10Y-2Y spread negative: {spread_10y2y}%')
        elif spread_10y2y < 0.25:
            signals.append(f'10Y-2Y spread very flat: {spread_10y2y}%')
        else:
            signals.append(f'10Y-2Y spread normal: {spread_10y2y}%')

    if real_10y is not None:
        if real_10y > 2.0:
            signals.append(f'Real 10Y yield restrictive: {real_10y}%')
        elif real_10y < 0:
            signals.append(f'Real 10Y yield negative (accommodative): {real_10y}%')

    result = {
        'regime': regime,
        'fed_rate': fed,
        'curve_10y2y': spread_10y2y,
        'real_10y': real_10y,
        'signals': signals,
        'source': 'FRED',
    }
    _write_cache('regime', result)
    return result


def search_rate_series(query: str, limit: int = 15) -> List[Dict]:
    """
    Search FRED for interest-rate-related series.

    Args:
        query: Search term (e.g. 'mortgage rate', 'euribor')
        limit: Max results (default 15)

    Returns:
        list of dict: [{'id': str, 'title': str, 'frequency': str,
                        'units': str, 'last_updated': str}, ...]
    """
    data = _fred_get('series/search', {
        'search_text': query,
        'limit': limit,
        'order_by': 'popularity',
        'sort_order': 'desc',
        'filter_variable': 'frequency',
        'filter_value': 'Daily',
    })

    results = []
    for s in data.get('seriess', []):
        results.append({
            'id': s.get('id'),
            'title': s.get('title'),
            'frequency': s.get('frequency'),
            'units': s.get('units'),
            'last_updated': s.get('last_updated'),
        })
    return results


def list_available_series() -> Dict:
    """
    Return all pre-defined series catalogs in this module.

    Returns:
        dict with keys: international_rates, real_rates, breakevens,
                        short_term_rates, extended_yields, carry_pairs
    """
    return {
        'international_rates': INTERNATIONAL_RATES,
        'real_rates': REAL_RATE_SERIES,
        'breakevens': BREAKEVEN_SERIES,
        'short_term_rates': SHORT_TERM_RATES,
        'extended_yields': EXTENDED_YIELDS,
        'carry_pairs': {k: v[2] for k, v in CARRY_PAIRS.items()},
    }


# ── CLI Quick-test ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("=== Short-term rates ===")
        st = get_short_term_rates()
        print(json.dumps({k: v for k, v in st.items() if k != 'rates'}, indent=2))
        print(f"  SOFR: {st.get('sofr')}")
        print("\n=== Rate regime ===")
        reg = classify_rate_regime()
        print(json.dumps(reg, indent=2))
    else:
        print(json.dumps({
            'module': 'fred_interest_rates_expansion',
            'functions': 10,
            'source': 'FRED',
            'status': 'ready',
        }, indent=2))

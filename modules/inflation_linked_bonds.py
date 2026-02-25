#!/usr/bin/env python3
"""
Inflation-Linked Bond Tracker Module — Phase 167

Global inflation-linked bond (linker) coverage from major issuers:
- US TIPS (Treasury Inflation-Protected Securities) via FRED
- Euro-area inflation-linked bonds via ECB SDW
- UK Index-Linked Gilts via Bank of England

Tracks:
- Real yields across maturities
- Breakeven inflation rates
- Outstanding amounts and issuance
- Market liquidity and spreads
- Cross-currency linker comparisons

Data Sources:
- FRED API (US TIPS yields and amounts outstanding)
- ECB Statistical Data Warehouse (Euro-area linkers)
- Bank of England Statistics (UK index-linked gilts)

Refresh: Daily
Coverage: Current yields + historical trends

Author: QUANTCLAW DATA Build Agent
Phase: 167
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

# ========== API CONFIGURATION ==========

# FRED API
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = ""

# ECB SDW API
ECB_BASE_URL = "https://data-api.ecb.europa.eu/service/data"
ECB_TIMEOUT = 15

# Bank of England API
BOE_BASE_URL = "https://www.bankofengland.co.uk/boeapps/database"
BOE_TIMEOUT = 15

# Load FRED API key
try:
    import os
    creds_path = os.path.expanduser('~/.openclaw/workspace/.credentials/fred-api.json')
    if os.path.exists(creds_path):
        with open(creds_path, 'r') as f:
            creds = json.load(f)
            FRED_API_KEY = creds.get('fredApiKey', '')
except:
    pass

# ========== DATA SERIES DEFINITIONS ==========

# US TIPS series from FRED
US_TIPS_SERIES = {
    'YIELDS': {
        'DFII5': '5-Year TIPS Yield',
        'DFII7': '7-Year TIPS Yield',
        'DFII10': '10-Year TIPS Yield',
        'DFII20': '20-Year TIPS Yield',
        'DFII30': '30-Year TIPS Yield',
    },
    'OUTSTANDING': {
        'MBST': 'Total Marketable Treasury Securities Outstanding',
        'GFDEBTN': 'Federal Debt Total Public Debt Outstanding',
    }
}

# ECB inflation-linked bond series
ECB_LINKER_SERIES = {
    'YIELDS': 'YC.B.U2.EUR.4F.G_N_A.SV_C_YM.ILBE_',  # Euro area inflation-linked yield curve
}

# Bank of England gilt series
BOE_GILT_SERIES = {
    'IUDLGIY': 'UK Index-Linked Gilt Yield (Long)',
    'IUDMGIY': 'UK Index-Linked Gilt Yield (Medium)',
    'IUDBEIY10': 'UK 10Y Breakeven Inflation',
}

CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
}

# ========== CORE FUNCTIONS ==========

def get_global_linker_summary() -> Dict:
    """
    Get comprehensive summary of global inflation-linked bond markets
    
    Returns:
        Dict with linker data from US, Eurozone, and UK
    """
    try:
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'markets': {}
        }
        
        # Fetch US TIPS data
        us_data = _get_us_tips_data()
        if us_data:
            result['markets']['US'] = us_data
        
        # Fetch Eurozone linker data
        euro_data = _get_euro_linker_data()
        if euro_data:
            result['markets']['EURO'] = euro_data
        
        # Fetch UK gilt data
        uk_data = _get_uk_gilt_data()
        if uk_data:
            result['markets']['UK'] = uk_data
        
        # Cross-market comparison
        result['comparison'] = _compare_global_linkers(result['markets'])
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching global linker summary: {str(e)}'
        }


def get_us_tips_yields(maturities: Optional[List[str]] = None) -> Dict:
    """
    Get current US TIPS (Treasury Inflation-Protected Securities) yields
    
    Args:
        maturities: List of maturities to fetch (5Y, 7Y, 10Y, 20Y, 30Y). None = all
        
    Returns:
        Dict with TIPS yields by maturity
    """
    try:
        if maturities is None:
            maturities = ['5Y', '7Y', '10Y', '20Y', '30Y']
        
        result = {
            'success': True,
            'currency': 'USD',
            'country': 'United States',
            'timestamp': datetime.now().isoformat(),
            'yields': {}
        }
        
        for series_id, description in US_TIPS_SERIES['YIELDS'].items():
            maturity = series_id.replace('DFII', '') + 'Y'
            
            if maturity not in maturities:
                continue
            
            data = _fetch_fred_latest(series_id)
            if data:
                result['yields'][maturity] = {
                    'value': data['value'],
                    'date': data['date'],
                    'series': series_id,
                    'description': description
                }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching US TIPS yields: {str(e)}'
        }


def get_euro_linker_yields() -> Dict:
    """
    Get Eurozone inflation-linked bond yields from ECB
    
    Returns:
        Dict with Euro-area linker yields
    """
    try:
        result = {
            'success': True,
            'currency': 'EUR',
            'country': 'Eurozone',
            'timestamp': datetime.now().isoformat(),
            'yields': {}
        }
        
        # ECB publishes AAA-rated euro area inflation-linked yield curve
        # Using ECB's ILBE (Inflation-Linked Bond Equivalent) series
        maturities = [5, 7, 10, 15, 20, 30]
        
        for maturity in maturities:
            # Construct ECB series key
            # Format: YC.B.U2.EUR.4F.G_N_A.SV_C_YM.ILBE_<maturity>
            series_key = f"YC/B.U2.EUR.4F.G_N_A.SV_C_YM.ILBE_{maturity}Y"
            
            data = _fetch_ecb_latest(series_key)
            if data:
                result['yields'][f'{maturity}Y'] = {
                    'value': data['value'],
                    'date': data['date'],
                    'description': f'{maturity}-Year Euro Inflation-Linked Yield'
                }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching Euro linker yields: {str(e)}'
        }


def get_uk_gilt_yields() -> Dict:
    """
    Get UK Index-Linked Gilt yields from Bank of England
    
    Returns:
        Dict with UK gilt yields
    """
    try:
        result = {
            'success': True,
            'currency': 'GBP',
            'country': 'United Kingdom',
            'timestamp': datetime.now().isoformat(),
            'yields': {}
        }
        
        # Bank of England publishes index-linked gilt yields
        for series_id, description in BOE_GILT_SERIES.items():
            data = _fetch_boe_latest(series_id)
            if data:
                # Parse maturity from description
                if 'Long' in description:
                    maturity = '20Y'
                elif 'Medium' in description:
                    maturity = '10Y'
                elif '10Y' in description:
                    maturity = '10Y'
                else:
                    maturity = 'N/A'
                
                result['yields'][maturity] = {
                    'value': data['value'],
                    'date': data['date'],
                    'series': series_id,
                    'description': description
                }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching UK gilt yields: {str(e)}'
        }


def compare_linker_yields(region1: str = 'US', region2: str = 'EURO') -> Dict:
    """
    Compare inflation-linked bond yields across regions
    
    Args:
        region1: First region (US, EURO, UK)
        region2: Second region (US, EURO, UK)
        
    Returns:
        Dict with yield comparison
    """
    try:
        summary = get_global_linker_summary()
        
        if not summary.get('success'):
            return summary
        
        markets = summary.get('markets', {})
        
        if region1 not in markets or region2 not in markets:
            return {
                'success': False,
                'error': f'Regions {region1} and/or {region2} not available'
            }
        
        data1 = markets[region1]
        data2 = markets[region2]
        
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'region1': {
                'code': region1,
                'currency': data1.get('currency', 'N/A'),
                'yields': data1.get('yields', {})
            },
            'region2': {
                'code': region2,
                'currency': data2.get('currency', 'N/A'),
                'yields': data2.get('yields', {})
            },
            'spreads': {}
        }
        
        # Calculate spreads for common maturities
        yields1 = data1.get('yields', {})
        yields2 = data2.get('yields', {})
        
        common_maturities = set(yields1.keys()) & set(yields2.keys())
        
        for maturity in common_maturities:
            y1 = yields1[maturity].get('value', 0)
            y2 = yields2[maturity].get('value', 0)
            spread = round(y1 - y2, 2)
            spread_bps = int(spread * 100)
            
            result['spreads'][maturity] = {
                f'{region1}_yield': y1,
                f'{region2}_yield': y2,
                'spread': spread,
                'spread_bps': spread_bps
            }
        
        # Analysis
        result['analysis'] = []
        
        if result['spreads']:
            avg_spread = sum(s['spread'] for s in result['spreads'].values()) / len(result['spreads'])
            
            if avg_spread > 1.0:
                result['analysis'].append(f'{region1} real yields significantly higher than {region2}')
            elif avg_spread < -1.0:
                result['analysis'].append(f'{region2} real yields significantly higher than {region1}')
            else:
                result['analysis'].append(f'Real yields relatively aligned between {region1} and {region2}')
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error comparing linker yields: {str(e)}'
        }


def get_linker_history(
    region: str = 'US',
    maturity: str = '10Y',
    days_back: int = 365
) -> Dict:
    """
    Get historical inflation-linked bond yields for a specific region and maturity
    
    Args:
        region: Region code (US, EURO, UK)
        maturity: Maturity (5Y, 7Y, 10Y, 20Y, 30Y)
        days_back: Historical lookback period
        
    Returns:
        Dict with time series data
    """
    try:
        result = {
            'success': True,
            'region': region,
            'maturity': maturity,
            'period_days': days_back,
            'time_series': []
        }
        
        if region == 'US':
            # Map maturity to FRED series
            series_map = {
                '5Y': 'DFII5',
                '7Y': 'DFII7',
                '10Y': 'DFII10',
                '20Y': 'DFII20',
                '30Y': 'DFII30',
            }
            
            if maturity not in series_map:
                return {'success': False, 'error': f'Invalid maturity: {maturity}'}
            
            series_id = series_map[maturity]
            history = _fetch_fred_history(series_id, days_back=days_back)
            
            if history:
                result['time_series'] = history
        
        elif region == 'EURO':
            # ECB series
            mat_num = maturity.replace('Y', '')
            series_key = f"YC/B.U2.EUR.4F.G_N_A.SV_C_YM.ILBE_{maturity}"
            history = _fetch_ecb_history(series_key, days_back=days_back)
            
            if history:
                result['time_series'] = history
        
        elif region == 'UK':
            # BOE series - simplified for now
            if maturity == '10Y':
                series_id = 'IUDMGIY'
            elif maturity == '20Y':
                series_id = 'IUDLGIY'
            else:
                return {'success': False, 'error': f'UK gilt data not available for {maturity}'}
            
            history = _fetch_boe_history(series_id, days_back=days_back)
            
            if history:
                result['time_series'] = history
        
        else:
            return {'success': False, 'error': f'Unknown region: {region}'}
        
        # Calculate statistics
        if result['time_series']:
            values = [point['value'] for point in result['time_series']]
            result['stats'] = {
                'latest': values[0],
                'average': round(sum(values) / len(values), 2),
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching linker history: {str(e)}'
        }


def analyze_real_yield_trends(days_back: int = 30) -> Dict:
    """
    Analyze recent trends in real yields across all major linker markets
    
    Args:
        days_back: Period to analyze
        
    Returns:
        Dict with trend analysis
    """
    try:
        result = {
            'success': True,
            'period_days': days_back,
            'timestamp': datetime.now().isoformat(),
            'trends': {}
        }
        
        regions = ['US', 'EURO', 'UK']
        maturities = ['10Y']  # Focus on benchmark 10Y
        
        for region in regions:
            for maturity in maturities:
                history_data = get_linker_history(region, maturity, days_back)
                
                if not history_data.get('success') or not history_data.get('time_series'):
                    continue
                
                time_series = history_data['time_series']
                
                if len(time_series) < 2:
                    continue
                
                current = time_series[0]['value']
                previous = time_series[-1]['value']
                change = round(current - previous, 2)
                change_bps = int(change * 100)
                
                key = f'{region}_{maturity}'
                result['trends'][key] = {
                    'region': region,
                    'maturity': maturity,
                    'current': current,
                    'previous': previous,
                    'change': change,
                    'change_bps': change_bps,
                    'direction': 'UP' if change > 0 else 'DOWN' if change < 0 else 'FLAT'
                }
        
        # Overall market assessment
        if result['trends']:
            changes = [t['change'] for t in result['trends'].values()]
            avg_change = sum(changes) / len(changes)
            
            result['market_trend'] = {
                'avg_change': round(avg_change, 2),
                'avg_change_bps': int(avg_change * 100)
            }
            
            if avg_change > 0.2:
                result['market_trend']['assessment'] = 'Real yields RISING globally'
            elif avg_change < -0.2:
                result['market_trend']['assessment'] = 'Real yields FALLING globally'
            else:
                result['market_trend']['assessment'] = 'Real yields STABLE'
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error analyzing real yield trends: {str(e)}'
        }


# ========== HELPER FUNCTIONS ==========

def _get_us_tips_data() -> Optional[Dict]:
    """Fetch US TIPS data from FRED"""
    try:
        data = {
            'currency': 'USD',
            'country': 'United States',
            'yields': {}
        }
        
        for series_id, description in US_TIPS_SERIES['YIELDS'].items():
            latest = _fetch_fred_latest(series_id)
            if latest:
                maturity = series_id.replace('DFII', '') + 'Y'
                data['yields'][maturity] = {
                    'value': latest['value'],
                    'date': latest['date'],
                    'description': description
                }
        
        return data if data['yields'] else None
        
    except:
        return None


def _get_euro_linker_data() -> Optional[Dict]:
    """Fetch Eurozone linker data from ECB"""
    try:
        data = {
            'currency': 'EUR',
            'country': 'Eurozone',
            'yields': {}
        }
        
        # ECB inflation-linked yields
        maturities = [5, 10, 20, 30]
        
        for maturity in maturities:
            series_key = f"YC/B.U2.EUR.4F.G_N_A.SV_C_YM.ILBE_{maturity}Y"
            latest = _fetch_ecb_latest(series_key)
            
            if latest:
                data['yields'][f'{maturity}Y'] = {
                    'value': latest['value'],
                    'date': latest['date'],
                    'description': f'{maturity}-Year Euro Inflation-Linked Yield'
                }
        
        return data if data['yields'] else None
        
    except:
        return None


def _get_uk_gilt_data() -> Optional[Dict]:
    """Fetch UK index-linked gilt data from Bank of England"""
    try:
        data = {
            'currency': 'GBP',
            'country': 'United Kingdom',
            'yields': {}
        }
        
        # Simplified - fetch representative series
        series_map = {
            '10Y': 'IUDMGIY',
            '20Y': 'IUDLGIY',
        }
        
        for maturity, series_id in series_map.items():
            latest = _fetch_boe_latest(series_id)
            if latest:
                data['yields'][maturity] = {
                    'value': latest['value'],
                    'date': latest['date'],
                    'description': f'UK {maturity} Index-Linked Gilt Yield'
                }
        
        return data if data['yields'] else None
        
    except:
        return None


def _compare_global_linkers(markets: Dict) -> Dict:
    """Compare linker yields across markets"""
    try:
        comparison = {
            'highest_real_yield': None,
            'lowest_real_yield': None,
            'spreads': {}
        }
        
        # Find highest and lowest 10Y real yields
        yields_10y = {}
        
        for region, data in markets.items():
            if '10Y' in data.get('yields', {}):
                yields_10y[region] = data['yields']['10Y']['value']
        
        if yields_10y:
            max_region = max(yields_10y, key=yields_10y.get)
            min_region = min(yields_10y, key=yields_10y.get)
            
            comparison['highest_real_yield'] = {
                'region': max_region,
                'yield': yields_10y[max_region],
                'currency': markets[max_region].get('currency', 'N/A')
            }
            
            comparison['lowest_real_yield'] = {
                'region': min_region,
                'yield': yields_10y[min_region],
                'currency': markets[min_region].get('currency', 'N/A')
            }
            
            # Calculate spread
            spread = round(yields_10y[max_region] - yields_10y[min_region], 2)
            comparison['yield_spread_10y'] = {
                'value': spread,
                'bps': int(spread * 100),
                'high': max_region,
                'low': min_region
            }
        
        return comparison
        
    except:
        return {}


def _fetch_fred_latest(series_id: str) -> Optional[Dict]:
    """Fetch latest value from FRED"""
    try:
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            'series_id': series_id,
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': 1
        }
        
        if FRED_API_KEY:
            params['api_key'] = FRED_API_KEY
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('observations'):
                obs = data['observations'][0]
                if obs['value'] != '.':
                    return {
                        'value': float(obs['value']),
                        'date': obs['date']
                    }
        
        return None
        
    except:
        return None


def _fetch_fred_history(series_id: str, days_back: int = 365) -> Optional[List[Dict]]:
    """Fetch historical data from FRED"""
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            'series_id': series_id,
            'file_type': 'json',
            'observation_start': start_date,
            'observation_end': end_date,
            'sort_order': 'desc'
        }
        
        if FRED_API_KEY:
            params['api_key'] = FRED_API_KEY
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('observations'):
                return [
                    {'date': obs['date'], 'value': float(obs['value'])}
                    for obs in data['observations']
                    if obs['value'] != '.'
                ]
        
        return None
        
    except:
        return None


def _fetch_ecb_latest(series_key: str) -> Optional[Dict]:
    """Fetch latest value from ECB SDW"""
    try:
        # ECB API format: https://data-api.ecb.europa.eu/service/data/{dataflow}/{key}
        url = f"{ECB_BASE_URL}/{series_key}"
        params = {
            'format': 'jsondata',
            'lastNObservations': 1
        }
        
        headers = {
            'Accept': 'application/json'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=ECB_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse ECB JSON structure
            if 'dataSets' in data and data['dataSets']:
                dataset = data['dataSets'][0]
                if 'series' in dataset and dataset['series']:
                    series = list(dataset['series'].values())[0]
                    if 'observations' in series and series['observations']:
                        obs_key = list(series['observations'].keys())[0]
                        value = series['observations'][obs_key][0]
                        
                        # Get date from structure
                        if 'structure' in data and 'dimensions' in data['structure']:
                            dims = data['structure']['dimensions']
                            if 'observation' in dims:
                                obs_dim = dims['observation']
                                for dim in obs_dim:
                                    if dim.get('id') == 'TIME_PERIOD':
                                        values = dim.get('values', [])
                                        if values:
                                            date_str = values[int(obs_key)].get('id', '')
                                            return {
                                                'value': float(value),
                                                'date': date_str
                                            }
        
        return None
        
    except:
        return None


def _fetch_ecb_history(series_key: str, days_back: int = 365) -> Optional[List[Dict]]:
    """Fetch historical data from ECB SDW"""
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        url = f"{ECB_BASE_URL}/{series_key}"
        params = {
            'format': 'jsondata',
            'startPeriod': start_date,
            'endPeriod': end_date
        }
        
        headers = {
            'Accept': 'application/json'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=ECB_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse ECB JSON structure
            if 'dataSets' in data and data['dataSets']:
                dataset = data['dataSets'][0]
                if 'series' in dataset and dataset['series']:
                    series = list(dataset['series'].values())[0]
                    if 'observations' in series and series['observations']:
                        # Get time dimension
                        dates = []
                        if 'structure' in data and 'dimensions' in data['structure']:
                            dims = data['structure']['dimensions']
                            if 'observation' in dims:
                                obs_dim = dims['observation']
                                for dim in obs_dim:
                                    if dim.get('id') == 'TIME_PERIOD':
                                        dates = [v['id'] for v in dim.get('values', [])]
                        
                        # Build time series
                        observations = series['observations']
                        time_series = []
                        
                        for i, (obs_key, obs_val) in enumerate(observations.items()):
                            date_str = dates[int(obs_key)] if dates and int(obs_key) < len(dates) else ''
                            time_series.append({
                                'date': date_str,
                                'value': float(obs_val[0])
                            })
                        
                        # Sort descending by date
                        time_series.sort(key=lambda x: x['date'], reverse=True)
                        
                        return time_series
        
        return None
        
    except:
        return None


def _fetch_boe_latest(series_id: str) -> Optional[Dict]:
    """Fetch latest value from Bank of England"""
    try:
        # Bank of England API format
        url = f"{BOE_BASE_URL}/csv/latest/{series_id}"
        
        response = requests.get(url, timeout=BOE_TIMEOUT)
        
        if response.status_code == 200:
            # Parse CSV response
            lines = response.text.strip().split('\n')
            
            if len(lines) >= 2:
                # Skip header, get last data line
                data_line = lines[-1]
                parts = data_line.split(',')
                
                if len(parts) >= 2:
                    date_str = parts[0].strip('"')
                    value_str = parts[1].strip('"')
                    
                    try:
                        return {
                            'value': float(value_str),
                            'date': date_str
                        }
                    except ValueError:
                        pass
        
        return None
        
    except:
        return None


def _fetch_boe_history(series_id: str, days_back: int = 365) -> Optional[List[Dict]]:
    """Fetch historical data from Bank of England"""
    try:
        # Bank of England historical data endpoint
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        url = f"{BOE_BASE_URL}/csv/{start_date}/{end_date}/{series_id}"
        
        response = requests.get(url, timeout=BOE_TIMEOUT)
        
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            
            time_series = []
            
            # Skip header line
            for line in lines[1:]:
                parts = line.split(',')
                
                if len(parts) >= 2:
                    date_str = parts[0].strip('"')
                    value_str = parts[1].strip('"')
                    
                    try:
                        time_series.append({
                            'date': date_str,
                            'value': float(value_str)
                        })
                    except ValueError:
                        continue
            
            # Sort descending by date
            time_series.sort(key=lambda x: x['date'], reverse=True)
            
            return time_series
        
        return None
        
    except:
        return None


# ========== CLI INTERFACE ==========

def main():
    """CLI interface for Inflation-Linked Bond Tracker"""
    if len(sys.argv) < 2:
        print("Usage: inflation_linked_bonds.py <command> [options]")
        print("\nCommands:")
        print("  global-summary           Get global linker market summary (US, Euro, UK)")
        print("  us-tips [maturities]     Get US TIPS yields (e.g., 5Y,10Y,30Y)")
        print("  euro-linkers             Get Eurozone inflation-linked bond yields")
        print("  uk-gilts                 Get UK index-linked gilt yields")
        print("  compare <region1> <region2>  Compare yields (e.g., US EURO)")
        print("  history <region> <maturity> [days]  Historical yields (e.g., US 10Y 365)")
        print("  trends [days]            Analyze real yield trends (default: 30)")
        return
    
    command = sys.argv[1]
    
    if command == 'global-summary':
        result = get_global_linker_summary()
        print(json.dumps(result, indent=2))
    
    elif command == 'us-tips':
        maturities = None
        if len(sys.argv) > 2:
            maturities = sys.argv[2].split(',')
        result = get_us_tips_yields(maturities)
        print(json.dumps(result, indent=2))
    
    elif command == 'euro-linkers':
        result = get_euro_linker_yields()
        print(json.dumps(result, indent=2))
    
    elif command == 'uk-gilts':
        result = get_uk_gilt_yields()
        print(json.dumps(result, indent=2))
    
    elif command == 'compare':
        if len(sys.argv) < 4:
            print("Error: Specify two regions (e.g., US EURO)")
            return
        region1 = sys.argv[2].upper()
        region2 = sys.argv[3].upper()
        result = compare_linker_yields(region1, region2)
        print(json.dumps(result, indent=2))
    
    elif command == 'history':
        if len(sys.argv) < 4:
            print("Error: Specify region and maturity (e.g., US 10Y)")
            return
        region = sys.argv[2].upper()
        maturity = sys.argv[3].upper()
        days = int(sys.argv[4]) if len(sys.argv) > 4 else 365
        result = get_linker_history(region, maturity, days)
        print(json.dumps(result, indent=2))
    
    elif command == 'trends':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        result = analyze_real_yield_trends(days_back=days)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()

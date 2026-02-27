"""
MAS Singapore — Monetary Authority of Singapore Data
Phase 648: Monetary policy, FX reserves, banking statistics

Free data sources:
- MAS Official Statistics (https://www.mas.gov.sg/statistics)
- MAS Monthly Statistical Bulletin (https://eservices.mas.gov.sg/statistics)
- FRED Singapore data (https://fred.stlouisfed.org)
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class MASSingapore:
    """Monetary Authority of Singapore data provider"""
    
    def __init__(self):
        self.fred_base = "https://api.stlouisfed.org/fred/series/observations"
        self.fred_key = "your_fred_api_key_here"  # Free from https://fred.stlouisfed.org/docs/api/api_key.html
        
        # MAS FRED series IDs
        self.series = {
            'fx_reserves': 'TRESEGSINM052N',  # Total Reserves excl. Gold for Singapore
            'gdp': 'NGDPRSAXDCSGQ',  # Real GDP
            'cpi': 'SGPCPIGM',  # CPI All Items
            'unemployment': 'LRUNSG',  # Unemployment Rate
            'exports': 'XTEXVA01SGM667S',  # Exports
            'imports': 'XTIMVA01SGM667S',  # Imports
        }
    
    def get_monetary_policy(self) -> Dict:
        """
        MAS uses exchange rate as primary policy tool (SGD NEER)
        Returns latest monetary policy stance
        """
        try:
            # Get SGD NEER policy band data from FRED
            params = {
                'series_id': 'EXSGUS',  # Singapore / U.S. Foreign Exchange Rate
                'api_key': self.fred_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 12  # Last 12 months
            }
            
            resp = requests.get(self.fred_base, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            observations = data.get('observations', [])
            if not observations:
                return {'error': 'No data available'}
            
            latest = observations[0]
            one_year_ago = observations[-1] if len(observations) >= 12 else observations[-1]
            
            return {
                'source': 'MAS via FRED',
                'last_updated': latest['date'],
                'sgd_usd_rate': float(latest['value']),
                'year_ago_rate': float(one_year_ago['value']),
                'sgd_appreciation_pct': ((float(one_year_ago['value']) - float(latest['value'])) / float(latest['value'])) * 100,
                'policy_tool': 'Exchange Rate (SGD NEER)',
                'note': 'MAS manages SGD within undisclosed policy band'
            }
        
        except Exception as e:
            return {'error': str(e), 'source': 'MAS Singapore'}
    
    def get_fx_reserves(self, months: int = 24) -> List[Dict]:
        """
        Get Singapore's foreign exchange reserves
        
        Args:
            months: Number of months of history
        
        Returns:
            List of monthly FX reserve observations
        """
        try:
            params = {
                'series_id': self.series['fx_reserves'],
                'api_key': self.fred_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': months
            }
            
            resp = requests.get(self.fred_base, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            observations = data.get('observations', [])
            return [
                {
                    'date': obs['date'],
                    'reserves_usd_millions': float(obs['value']),
                    'reserves_usd_billions': round(float(obs['value']) / 1000, 2)
                }
                for obs in observations if obs['value'] != '.'
            ]
        
        except Exception as e:
            return [{'error': str(e), 'source': 'MAS FX Reserves'}]
    
    def get_banking_stats(self) -> Dict:
        """
        Get Singapore banking sector statistics
        
        Note: Full banking stats require MAS API access.
        This uses FRED proxies and public data.
        """
        try:
            # Get domestic credit data as proxy for banking activity
            params = {
                'series_id': 'DDOI11SGA156NWDB',  # Deposit money banks total assets
                'api_key': self.fred_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 4  # Last 4 quarters
            }
            
            resp = requests.get(self.fred_base, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            observations = data.get('observations', [])
            if not observations:
                return {'error': 'No banking data available'}
            
            latest = observations[0]
            
            return {
                'source': 'World Bank via FRED',
                'last_updated': latest['date'],
                'bank_assets_pct_gdp': float(latest['value']),
                'note': 'Singapore is major international banking hub',
                'top_banks': ['DBS', 'OCBC', 'UOB'],
                'banking_license_types': ['Full Bank', 'Wholesale Bank', 'Merchant Bank']
            }
        
        except Exception as e:
            return {'error': str(e), 'source': 'MAS Banking Stats'}
    
    def get_economic_indicators(self) -> Dict:
        """
        Get key Singapore economic indicators
        
        Returns:
            GDP, CPI, unemployment, trade data
        """
        try:
            indicators = {}
            
            for name, series_id in self.series.items():
                params = {
                    'series_id': series_id,
                    'api_key': self.fred_key,
                    'file_type': 'json',
                    'sort_order': 'desc',
                    'limit': 1
                }
                
                resp = requests.get(self.fred_base, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    observations = data.get('observations', [])
                    if observations and observations[0]['value'] != '.':
                        indicators[name] = {
                            'value': float(observations[0]['value']),
                            'date': observations[0]['date']
                        }
            
            return {
                'source': 'MAS via FRED',
                'timestamp': datetime.now().isoformat(),
                'indicators': indicators,
                'notes': 'Singapore is trade-dependent city-state economy'
            }
        
        except Exception as e:
            return {'error': str(e), 'source': 'MAS Economic Indicators'}
    
    def get_financial_stability(self) -> Dict:
        """
        Get financial stability indicators
        
        Note: MAS publishes Financial Stability Review annually
        This provides proxy metrics from public sources
        """
        return {
            'source': 'MAS Financial Stability Framework',
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'household_debt_to_gdp': 'MAS monitors via Total Debt Servicing Ratio (TDSR)',
                'property_cooling_measures': [
                    'Additional Buyer Stamp Duty (ABSD)',
                    'Total Debt Servicing Ratio (TDSR)',
                    'Loan-to-Value (LTV) limits'
                ],
                'financial_center_ranking': 'Top 3 globally (GFCI)',
                'banking_sector_strength': 'Tier-1 capital ratios >14%',
            },
            'note': 'Full FSR report at https://www.mas.gov.sg/publications/financial-stability-review'
        }


def get_mas_summary() -> Dict:
    """Get comprehensive MAS Singapore summary"""
    mas = MASSingapore()
    
    return {
        'monetary_policy': mas.get_monetary_policy(),
        'fx_reserves_latest': mas.get_fx_reserves(months=1),
        'banking_stats': mas.get_banking_stats(),
        'economic_indicators': mas.get_economic_indicators(),
        'financial_stability': mas.get_financial_stability()
    }


if __name__ == '__main__':
    # Test the module
    mas = MASSingapore()
    
    print("=== MAS Singapore Data ===\n")
    
    print("Monetary Policy:")
    print(json.dumps(mas.get_monetary_policy(), indent=2))
    
    print("\nFX Reserves (last 6 months):")
    reserves = mas.get_fx_reserves(months=6)
    for r in reserves[:3]:  # Show first 3
        print(f"  {r.get('date', 'N/A')}: ${r.get('reserves_usd_billions', 'N/A')}B")
    
    print("\nBanking Stats:")
    print(json.dumps(mas.get_banking_stats(), indent=2))
    
    print("\nEconomic Indicators:")
    print(json.dumps(mas.get_economic_indicators(), indent=2))

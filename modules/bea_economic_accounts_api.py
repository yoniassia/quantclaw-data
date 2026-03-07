"""
BEA Economic Accounts API — U.S. Bureau of Economic Analysis

Comprehensive U.S. macroeconomic data from the Bureau of Economic Analysis:
- GDP (Gross Domestic Product) - NIPA Tables
- Personal Income by State/National
- International Trade Balance
- Industry Value Added
- National Income and Product Accounts (NIPA)

Data source: BEA Data API (requires free API key)
API docs: https://apps.bea.gov/api/signup/
Update frequency: Quarterly for GDP/NIPA, Monthly for trade
Coverage: Historical data back to 1929 for some series

Critical for:
- Macroeconomic modeling
- Recession forecasting
- Interest rate predictions
- Long-term strategic asset allocation
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import pandas as pd
from pathlib import Path
import json
import os


class BEAEconomicAccounts:
    """BEA Economic Accounts API data fetcher"""
    
    BASE_URL = "https://apps.bea.gov/api/data"
    CACHE_DIR = Path.home() / ".quantclaw" / "cache" / "bea_economic_accounts"
    CACHE_HOURS = 24  # Refresh daily (BEA data updates quarterly/monthly)
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize BEA API client
        
        Args:
            api_key: BEA API key. If None, reads from BEA_API_KEY env var
        """
        self.api_key = api_key or os.getenv("BEA_API_KEY")
        if not self.api_key:
            raise ValueError("BEA_API_KEY environment variable not set. Get free key at https://apps.bea.gov/api/signup/")
        
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (QuantClaw/1.0) Python/requests'
        })
    
    def _make_request(self, params: Dict) -> Dict:
        """Make API request with error handling"""
        params['UserID'] = self.api_key
        params['ResultFormat'] = 'JSON'
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if 'BEAAPI' in data and 'Error' in data['BEAAPI']:
                error = data['BEAAPI']['Error']
                raise Exception(f"BEA API Error: {error.get('APIErrorDescription', 'Unknown error')}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def _get_cached(self, cache_key: str) -> Optional[Dict]:
        """Get cached data if fresh"""
        cache_file = self.CACHE_DIR / f"{cache_key}.json"
        
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(hours=self.CACHE_HOURS):
                with open(cache_file) as f:
                    return json.load(f)
        return None
    
    def _set_cache(self, cache_key: str, data: Dict):
        """Cache data to disk"""
        cache_file = self.CACHE_DIR / f"{cache_key}.json"
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_datasets(self) -> List[Dict]:
        """
        List all available BEA datasets
        
        Returns:
            List of dataset metadata dicts
        """
        cache_key = "datasets"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            params = {'method': 'GetDataSetList'}
            result = self._make_request(params)
            
            datasets = result['BEAAPI']['Results']['Dataset']
            
            # Format output
            formatted = [
                {
                    'name': ds['DatasetName'],
                    'description': ds['DatasetDescription']
                }
                for ds in datasets
            ]
            
            self._set_cache(cache_key, formatted)
            return formatted
            
        except Exception as e:
            print(f"Error fetching datasets: {e}")
            raise
    
    def get_gdp(self, frequency: str = 'Q', year: str = 'ALL') -> pd.DataFrame:
        """
        Get GDP data from NIPA Table 1.1.1 (Percent Change from Preceding Period)
        
        Args:
            frequency: 'Q' (quarterly), 'A' (annual), 'M' (monthly)
            year: Specific year (e.g., '2024') or 'ALL' for all available
        
        Returns:
            DataFrame with GDP data
        """
        cache_key = f"gdp_{frequency}_{year}"
        cached = self._get_cached(cache_key)
        if cached:
            return pd.DataFrame(cached)
        
        try:
            params = {
                'method': 'GetData',
                'datasetname': 'NIPA',
                'TableName': 'T10101',  # Table 1.1.1 - Percent Change
                'Frequency': frequency,
                'Year': year
            }
            
            result = self._make_request(params)
            data = result['BEAAPI']['Results']['Data']
            
            df = pd.DataFrame(data)
            
            # Cache as dict for JSON serialization
            self._set_cache(cache_key, df.to_dict('records'))
            return df
            
        except Exception as e:
            print(f"Error fetching GDP: {e}")
            raise
    
    def get_personal_income(self, state: str = 'US', year: str = 'ALL') -> pd.DataFrame:
        """
        Get personal income data by state or national
        
        Args:
            state: Two-letter state code (e.g., 'CA') or 'US' for national
            year: Specific year or 'ALL'
        
        Returns:
            DataFrame with personal income data
        """
        cache_key = f"personal_income_{state}_{year}"
        cached = self._get_cached(cache_key)
        if cached:
            return pd.DataFrame(cached)
        
        try:
            params = {
                'method': 'GetData',
                'datasetname': 'Regional',
                'TableName': 'SAINC1',  # State Annual Income
                'LineCode': '1',  # Personal income
                'GeoFips': state if state != 'US' else 'STATE',
                'Year': year
            }
            
            result = self._make_request(params)
            data = result['BEAAPI']['Results']['Data']
            
            df = pd.DataFrame(data)
            
            self._set_cache(cache_key, df.to_dict('records'))
            return df
            
        except Exception as e:
            print(f"Error fetching personal income: {e}")
            raise
    
    def get_trade_balance(self, year: str = 'ALL') -> pd.DataFrame:
        """
        Get international trade balance data
        
        Args:
            year: Specific year or 'ALL'
        
        Returns:
            DataFrame with trade balance data
        """
        cache_key = f"trade_balance_{year}"
        cached = self._get_cached(cache_key)
        if cached:
            return pd.DataFrame(cached)
        
        try:
            params = {
                'method': 'GetData',
                'datasetname': 'IntlServTrade',
                'Indicator': 'BalanceGds',  # Balance on goods
                'AreaOrCountry': 'AllCountries',
                'Frequency': 'A',  # Annual
                'Year': year
            }
            
            result = self._make_request(params)
            data = result['BEAAPI']['Results']['Data']
            
            df = pd.DataFrame(data)
            
            self._set_cache(cache_key, df.to_dict('records'))
            return df
            
        except Exception as e:
            print(f"Error fetching trade balance: {e}")
            raise
    
    def get_nipa_table(self, table_name: str, frequency: str = 'Q', year: str = 'ALL') -> pd.DataFrame:
        """
        Generic NIPA (National Income and Product Accounts) table fetcher
        
        Args:
            table_name: NIPA table name (e.g., 'T10101', 'T10102')
            frequency: 'Q' (quarterly), 'A' (annual), 'M' (monthly)
            year: Specific year or 'ALL'
        
        Returns:
            DataFrame with NIPA table data
        """
        cache_key = f"nipa_{table_name}_{frequency}_{year}"
        cached = self._get_cached(cache_key)
        if cached:
            return pd.DataFrame(cached)
        
        try:
            params = {
                'method': 'GetData',
                'datasetname': 'NIPA',
                'TableName': table_name,
                'Frequency': frequency,
                'Year': year
            }
            
            result = self._make_request(params)
            data = result['BEAAPI']['Results']['Data']
            
            df = pd.DataFrame(data)
            
            self._set_cache(cache_key, df.to_dict('records'))
            return df
            
        except Exception as e:
            print(f"Error fetching NIPA table {table_name}: {e}")
            raise
    
    def get_industry_data(self, industry: str = 'ALL', year: str = 'ALL') -> pd.DataFrame:
        """
        Get industry value added data
        
        Args:
            industry: Industry code or 'ALL' for all industries
            year: Specific year or 'ALL'
        
        Returns:
            DataFrame with industry data
        """
        cache_key = f"industry_{industry}_{year}"
        cached = self._get_cached(cache_key)
        if cached:
            return pd.DataFrame(cached)
        
        try:
            params = {
                'method': 'GetData',
                'datasetname': 'GDPbyIndustry',
                'Industry': industry,
                'Frequency': 'A',  # Annual
                'Year': year,
                'TableID': '1'  # Value Added by Industry
            }
            
            result = self._make_request(params)
            data = result['BEAAPI']['Results']['Data']
            
            df = pd.DataFrame(data)
            
            self._set_cache(cache_key, df.to_dict('records'))
            return df
            
        except Exception as e:
            print(f"Error fetching industry data: {e}")
            raise


# Convenience functions for quick access
def get_datasets() -> List[Dict]:
    """Get list of available BEA datasets"""
    api = BEAEconomicAccounts()
    return api.get_datasets()


def get_gdp(frequency: str = 'Q', year: str = 'ALL') -> pd.DataFrame:
    """Get GDP data"""
    api = BEAEconomicAccounts()
    return api.get_gdp(frequency, year)


def get_personal_income(state: str = 'US', year: str = 'ALL') -> pd.DataFrame:
    """Get personal income data"""
    api = BEAEconomicAccounts()
    return api.get_personal_income(state, year)


def get_trade_balance(year: str = 'ALL') -> pd.DataFrame:
    """Get trade balance data"""
    api = BEAEconomicAccounts()
    return api.get_trade_balance(year)


def get_nipa_table(table_name: str, frequency: str = 'Q', year: str = 'ALL') -> pd.DataFrame:
    """Get NIPA table data"""
    api = BEAEconomicAccounts()
    return api.get_nipa_table(table_name, frequency, year)


def get_industry_data(industry: str = 'ALL', year: str = 'ALL') -> pd.DataFrame:
    """Get industry value added data"""
    api = BEAEconomicAccounts()
    return api.get_industry_data(industry, year)


if __name__ == "__main__":
    # Test module
    try:
        api = BEAEconomicAccounts()
        datasets = api.get_datasets()
        print(json.dumps({
            "module": "bea_economic_accounts_api",
            "status": "operational",
            "datasets_available": len(datasets),
            "functions": [
                "get_datasets",
                "get_gdp",
                "get_personal_income",
                "get_trade_balance",
                "get_nipa_table",
                "get_industry_data"
            ]
        }, indent=2))
    except Exception as e:
        print(json.dumps({
            "module": "bea_economic_accounts_api",
            "status": "error",
            "error": str(e)
        }, indent=2))

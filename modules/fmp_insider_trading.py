"""
Financial Modeling Prep (FMP) Insider Trading API
SEC Form 4 insider transaction data via FMP API

Data points:
- Transaction date, filing date
- Insider name, title, position
- Shares traded, transaction price
- Ownership percentage after transaction
- Transaction type (P=Purchase, S=Sale, A=Award, etc.)
- Company ticker and name

Source: https://financialmodelingprep.com/developer/docs/
Free tier: 250 requests/day, no credit card required
Last update: 2026-03-06
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os


class FMPInsiderTrading:
    """Financial Modeling Prep Insider Trading API client"""
    
    BASE_URL = "https://financialmodelingprep.com/api/v4"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize FMP Insider API client
        
        Args:
            api_key: FMP API key (or set FMP_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('FMP_API_KEY', 'demo')
        self.session = requests.Session()
    
    def get_insider_trades(self, symbol: str, limit: int = 100) -> pd.DataFrame:
        """
        Get insider trading transactions for a symbol
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            limit: Number of records to return (max 500)
        
        Returns:
            DataFrame with insider transaction details
        """
        url = f"{self.BASE_URL}/insider-trading"
        params = {
            'symbol': symbol.upper(),
            'limit': min(limit, 500),
            'apikey': self.api_key
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            
            # Clean and format columns
            if 'transactionDate' in df.columns:
                df['transactionDate'] = pd.to_datetime(df['transactionDate'])
            if 'filingDate' in df.columns:
                df['filingDate'] = pd.to_datetime(df['filingDate'])
            
            # Parse numeric fields
            numeric_cols = ['securitiesTransacted', 'price', 'securitiesOwned']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Calculate transaction value
            if 'securitiesTransacted' in df.columns and 'price' in df.columns:
                df['transactionValue'] = df['securitiesTransacted'] * df['price']
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching insider trades for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_recent_purchases(self, days: int = 7, min_value: int = 100000) -> pd.DataFrame:
        """
        Screen for recent significant insider purchases
        
        Args:
            days: Lookback period in days
            min_value: Minimum transaction value in USD
        
        Returns:
            DataFrame with recent insider buys
        """
        url = f"{self.BASE_URL}/insider-trading-rss-feed"
        params = {
            'limit': 500,
            'apikey': self.api_key
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            
            # Filter for purchases only
            if 'transactionType' in df.columns:
                df = df[df['transactionType'].str.upper() == 'P'].copy()
            
            # Filter by date
            if 'transactionDate' in df.columns:
                df['transactionDate'] = pd.to_datetime(df['transactionDate'])
                cutoff = datetime.now() - timedelta(days=days)
                df = df[df['transactionDate'] >= cutoff]
            
            # Calculate value and filter
            if 'securitiesTransacted' in df.columns and 'price' in df.columns:
                df['securitiesTransacted'] = pd.to_numeric(df['securitiesTransacted'], errors='coerce')
                df['price'] = pd.to_numeric(df['price'], errors='coerce')
                df['transactionValue'] = df['securitiesTransacted'] * df['price']
                df = df[df['transactionValue'] >= min_value]
            
            return df.sort_values('transactionValue', ascending=False)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching recent purchases: {e}")
            return pd.DataFrame()
    
    def get_insider_roster(self, symbol: str) -> pd.DataFrame:
        """
        Get list of insiders for a company
        
        Args:
            symbol: Stock ticker
        
        Returns:
            DataFrame with insider roster
        """
        url = f"{self.BASE_URL}/insider-roaster"
        params = {
            'symbol': symbol.upper(),
            'apikey': self.api_key
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            if not data:
                return pd.DataFrame()
            
            return pd.DataFrame(data)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching insider roster for {symbol}: {e}")
            return pd.DataFrame()


# Convenience functions for quick access
def get_insider_trades(symbol: str, limit: int = 100, api_key: Optional[str] = None) -> pd.DataFrame:
    """Get insider trades for a symbol"""
    client = FMPInsiderTrading(api_key)
    return client.get_insider_trades(symbol, limit)


def get_recent_purchases(days: int = 7, min_value: int = 100000, api_key: Optional[str] = None) -> pd.DataFrame:
    """Get recent significant insider purchases"""
    client = FMPInsiderTrading(api_key)
    return client.get_recent_purchases(days, min_value)


def get_insider_roster(symbol: str, api_key: Optional[str] = None) -> pd.DataFrame:
    """Get insider roster for a company"""
    client = FMPInsiderTrading(api_key)
    return client.get_insider_roster(symbol)


# Test/Demo
if __name__ == "__main__":
    print("Testing FMP Insider Trading API...")
    
    # Test with AAPL
    client = FMPInsiderTrading()
    df = client.get_insider_trades('AAPL', limit=10)
    
    if not df.empty:
        print(f"\nFound {len(df)} insider trades for AAPL:")
        print(df[['transactionDate', 'reportingName', 'transactionType', 'securitiesTransacted', 'price']].head())
    else:
        print("No data returned (check API key)")
    
    # Export sample
    output = {
        "module": "fmp_insider_trading",
        "status": "active",
        "source": "https://financialmodelingprep.com/developer/docs/",
        "sample_size": len(df),
        "columns": list(df.columns) if not df.empty else []
    }
    print(json.dumps(output, indent=2))

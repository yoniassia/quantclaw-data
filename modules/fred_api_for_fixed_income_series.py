"""
FRED API for Fixed Income Series — Federal Reserve Economic Data

Comprehensive fixed income data from the Federal Reserve Bank of St. Louis:
- Treasury yields (1M to 30Y)
- Corporate bond spreads (Investment Grade & High Yield)
- Mortgage rates (15Y & 30Y)
- Reference rates (SOFR, Fed Funds)
- Credit spreads

Data source: Federal Reserve Economic Data (FRED)
API: https://fred.stlouisfed.org/docs/api/fred.html
Update frequency: Daily (market days)
API key: Required (free, no rate limits) - set FRED_API_KEY env var

Free alternative to Bloomberg BTMM (Bond Market)
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pathlib import Path
import json
import os
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")


class FREDFixedIncome:
    """FRED Fixed Income Data Fetcher"""
    
    BASE_URL = "https://api.stlouisfed.org/fred"
    CACHE_DIR = Path.home() / ".quantclaw" / "cache" / "fred_fixed_income"
    CACHE_HOURS = 6  # Refresh every 6 hours (daily data updates)
    
    # Treasury Yield Series IDs
    TREASURY_SERIES = {
        "1M": "DGS1MO",
        "3M": "DGS3MO",
        "6M": "DGS6MO",
        "1Y": "DGS1",
        "2Y": "DGS2",
        "3Y": "DGS3",
        "5Y": "DGS5",
        "7Y": "DGS7",
        "10Y": "DGS10",
        "20Y": "DGS20",
        "30Y": "DGS30",
    }
    
    # Credit Spread Series IDs
    CREDIT_SERIES = {
        "AAA_CORP": "BAMLC0A1CAAAEY",  # AAA US Corporate Index OAS
        "BBB_CORP": "BAMLC0A4CBBBEY",  # BBB US Corporate Index OAS
        "IG_CORP": "BAMLC0A0CM",       # US Corporate Master OAS
        "HY_CORP": "BAMLH0A0HYM2",     # US High Yield OAS
    }
    
    # Mortgage & Reference Rates
    OTHER_SERIES = {
        "MORTGAGE_30Y": "MORTGAGE30US",
        "MORTGAGE_15Y": "MORTGAGE15US",
        "SOFR": "SOFR",
        "FED_FUNDS": "FEDFUNDS",
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize FRED Fixed Income data fetcher
        
        Args:
            api_key: FRED API key (defaults to FRED_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        if not self.api_key:
            raise ValueError("FRED_API_KEY not set. Get free key at https://fred.stlouisfed.org/docs/api/api_key.html")
        
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantClaw/1.0 (FRED Fixed Income Module)'
        })
    
    def _fetch_series_observations(
        self, 
        series_id: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch observations for a FRED series
        
        Args:
            series_id: FRED series ID
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            limit: Maximum number of observations
            
        Returns:
            List of observations with date and value
        """
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
        }
        
        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date
        if limit:
            params["limit"] = limit
            params["sort_order"] = "desc"  # Get most recent first
        
        try:
            response = self.session.get(
                f"{self.BASE_URL}/series/observations",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if "observations" not in data:
                return []
            
            # Filter out non-numeric values (., N/A, etc.)
            observations = []
            for obs in data["observations"]:
                if obs["value"] not in [".", "N/A", ""]:
                    try:
                        observations.append({
                            "date": obs["date"],
                            "value": float(obs["value"])
                        })
                    except ValueError:
                        continue
            
            return observations
            
        except Exception as e:
            print(f"Error fetching series {series_id}: {e}")
            raise
    
    def get_series(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical data for any FRED series
        
        Args:
            series_id: FRED series ID (e.g., 'DGS10' for 10Y Treasury)
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            
        Returns:
            DataFrame with date index and values
        """
        cache_key = f"{series_id}_{start_date}_{end_date}"
        cache_file = self.CACHE_DIR / f"{cache_key}.parquet"
        
        # Check cache
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(hours=self.CACHE_HOURS):
                return pd.read_parquet(cache_file)
        
        # Fetch data
        observations = self._fetch_series_observations(series_id, start_date, end_date)
        
        if not observations:
            return pd.DataFrame(columns=["date", "value"])
        
        df = pd.DataFrame(observations)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        df = df.sort_index()
        
        # Cache result
        df.to_parquet(cache_file)
        
        return df
    
    def get_treasury_yields(self) -> Dict[str, float]:
        """
        Get latest treasury yields for all maturities
        
        Returns:
            Dictionary with maturity as key and yield as value (in %)
        """
        cache_file = self.CACHE_DIR / "treasury_yields_latest.json"
        
        # Check cache
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(hours=self.CACHE_HOURS):
                with open(cache_file) as f:
                    return json.load(f)
        
        # Fetch latest for each maturity
        yields = {}
        for maturity, series_id in self.TREASURY_SERIES.items():
            try:
                obs = self._fetch_series_observations(series_id, limit=1)
                if obs:
                    yields[maturity] = {
                        "value": obs[0]["value"],
                        "date": obs[0]["date"]
                    }
            except Exception as e:
                print(f"Error fetching {maturity}: {e}")
                continue
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(yields, f, indent=2)
        
        return yields
    
    def get_yield_curve(self) -> pd.DataFrame:
        """
        Get full yield curve snapshot (latest values for all maturities)
        
        Returns:
            DataFrame with maturity and yield columns
        """
        yields = self.get_treasury_yields()
        
        if not yields:
            return pd.DataFrame(columns=["maturity", "yield", "date"])
        
        # Convert to DataFrame
        rows = []
        for maturity, data in yields.items():
            rows.append({
                "maturity": maturity,
                "yield": data["value"],
                "date": data["date"]
            })
        
        df = pd.DataFrame(rows)
        
        # Add numeric duration for sorting
        duration_map = {
            "1M": 1/12, "3M": 3/12, "6M": 6/12,
            "1Y": 1, "2Y": 2, "3Y": 3, "5Y": 5,
            "7Y": 7, "10Y": 10, "20Y": 20, "30Y": 30
        }
        df["duration_years"] = df["maturity"].map(duration_map)
        df = df.sort_values("duration_years")
        
        return df[["maturity", "yield", "date"]]
    
    def get_credit_spreads(self) -> Dict[str, Dict]:
        """
        Get latest credit spreads (OAS - Option-Adjusted Spread)
        
        Returns:
            Dictionary with spread type as key and value/date as nested dict
        """
        cache_file = self.CACHE_DIR / "credit_spreads_latest.json"
        
        # Check cache
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(hours=self.CACHE_HOURS):
                with open(cache_file) as f:
                    return json.load(f)
        
        # Fetch latest spreads
        spreads = {}
        for name, series_id in self.CREDIT_SERIES.items():
            try:
                obs = self._fetch_series_observations(series_id, limit=1)
                if obs:
                    spreads[name] = {
                        "value": obs[0]["value"],
                        "date": obs[0]["date"],
                        "unit": "basis_points"
                    }
            except Exception as e:
                print(f"Error fetching {name}: {e}")
                continue
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(spreads, f, indent=2)
        
        return spreads
    
    def get_mortgage_rates(self) -> Dict[str, Dict]:
        """
        Get latest mortgage rates (15Y and 30Y)
        
        Returns:
            Dictionary with mortgage type as key and rate/date as nested dict
        """
        cache_file = self.CACHE_DIR / "mortgage_rates_latest.json"
        
        # Check cache
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(hours=self.CACHE_HOURS):
                with open(cache_file) as f:
                    return json.load(f)
        
        # Fetch mortgage rates
        rates = {}
        for name in ["MORTGAGE_30Y", "MORTGAGE_15Y"]:
            series_id = self.OTHER_SERIES[name]
            try:
                obs = self._fetch_series_observations(series_id, limit=1)
                if obs:
                    rates[name] = {
                        "value": obs[0]["value"],
                        "date": obs[0]["date"],
                        "unit": "percent"
                    }
            except Exception as e:
                print(f"Error fetching {name}: {e}")
                continue
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(rates, f, indent=2)
        
        return rates
    
    def get_fed_funds_rate(self) -> Dict:
        """
        Get current Federal Funds Effective Rate
        
        Returns:
            Dictionary with rate value and date
        """
        cache_file = self.CACHE_DIR / "fed_funds_latest.json"
        
        # Check cache
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(hours=self.CACHE_HOURS):
                with open(cache_file) as f:
                    return json.load(f)
        
        # Fetch fed funds rate
        try:
            obs = self._fetch_series_observations(self.OTHER_SERIES["FED_FUNDS"], limit=1)
            if obs:
                result = {
                    "value": obs[0]["value"],
                    "date": obs[0]["date"],
                    "unit": "percent"
                }
                
                # Cache result
                with open(cache_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                return result
        except Exception as e:
            print(f"Error fetching Fed Funds rate: {e}")
            raise
    
    def get_sofr(self) -> Dict:
        """
        Get current SOFR (Secured Overnight Financing Rate)
        
        Returns:
            Dictionary with rate value and date
        """
        cache_file = self.CACHE_DIR / "sofr_latest.json"
        
        # Check cache
        if cache_file.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < timedelta(hours=self.CACHE_HOURS):
                with open(cache_file) as f:
                    return json.load(f)
        
        # Fetch SOFR
        try:
            obs = self._fetch_series_observations(self.OTHER_SERIES["SOFR"], limit=1)
            if obs:
                result = {
                    "value": obs[0]["value"],
                    "date": obs[0]["date"],
                    "unit": "percent"
                }
                
                # Cache result
                with open(cache_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                return result
        except Exception as e:
            print(f"Error fetching SOFR: {e}")
            raise


# Convenience functions for quick access
def get_treasury_yields() -> Dict[str, float]:
    """Get latest treasury yields for all maturities"""
    client = FREDFixedIncome()
    return client.get_treasury_yields()


def get_series(series_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """Get historical data for any FRED series"""
    client = FREDFixedIncome()
    return client.get_series(series_id, start_date, end_date)


def get_yield_curve() -> pd.DataFrame:
    """Get full yield curve snapshot"""
    client = FREDFixedIncome()
    return client.get_yield_curve()


def get_credit_spreads() -> Dict[str, Dict]:
    """Get latest credit spreads"""
    client = FREDFixedIncome()
    return client.get_credit_spreads()


def get_mortgage_rates() -> Dict[str, Dict]:
    """Get latest mortgage rates"""
    client = FREDFixedIncome()
    return client.get_mortgage_rates()


def get_fed_funds_rate() -> Dict:
    """Get current Federal Funds rate"""
    client = FREDFixedIncome()
    return client.get_fed_funds_rate()


def get_sofr() -> Dict:
    """Get current SOFR rate"""
    client = FREDFixedIncome()
    return client.get_sofr()


if __name__ == "__main__":
    # Quick test
    try:
        client = FREDFixedIncome()
        print("✅ FRED Fixed Income module initialized")
        print(f"Cache directory: {client.CACHE_DIR}")
        
        # Test treasury yields
        yields = client.get_treasury_yields()
        print(f"\n📊 Treasury Yields ({len(yields)} maturities)")
        for maturity in ["2Y", "5Y", "10Y", "30Y"]:
            if maturity in yields:
                print(f"  {maturity}: {yields[maturity]['value']}% ({yields[maturity]['date']})")
        
    except Exception as e:
        print(f"❌ Error: {e}")

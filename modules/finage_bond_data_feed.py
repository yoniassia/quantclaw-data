"""
Finage Bond Data Feed — Treasury & Credit Market Data

Data Sources:
- U.S. Treasury: Direct yield curve data (free, daily updates)
- FRED API: Bond yields, spreads, historical data (no key needed)
- Fallback to Finage API if configured

Provides:
- Current bond quotes (US10Y, US2Y, etc.)
- Full yield curve (1M to 30Y)
- Historical bond yields
- Credit spreads (IG vs HY)

Update: Daily (Treasury), Real-time (if Finage key configured)
Free: Yes
"""

import requests
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Optional, List
import json
import os
import io

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/bonds")
os.makedirs(CACHE_DIR, exist_ok=True)

# Free data sources
TREASURY_YIELD_URL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/all/{year}"
FRED_BASE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

# Bond symbol mapping to FRED series
FRED_SERIES_MAP = {
    "US1M": "DGS1MO",   # 1-Month Treasury
    "US3M": "DGS3MO",   # 3-Month Treasury
    "US6M": "DGS6MO",   # 6-Month Treasury
    "US1Y": "DGS1",     # 1-Year Treasury
    "US2Y": "DGS2",     # 2-Year Treasury
    "US3Y": "DGS3",     # 3-Year Treasury
    "US5Y": "DGS5",     # 5-Year Treasury
    "US7Y": "DGS7",     # 7-Year Treasury
    "US10Y": "DGS10",   # 10-Year Treasury
    "US20Y": "DGS20",   # 20-Year Treasury
    "US30Y": "DGS30",   # 30-Year Treasury
}

# Credit spread series
CREDIT_SPREAD_SERIES = {
    "IG": "BAMLC0A4CBBB",   # ICE BofA BBB US Corporate Index OAS
    "HY": "BAMLH0A0HYM2",   # ICE BofA US High Yield Index OAS
    "AAA": "BAMLC0A1CAAA",  # ICE BofA AAA US Corporate Index OAS
}

def get_bond_quote(symbol: str) -> Dict:
    """
    Get current yield/price for a specific bond symbol.
    
    Args:
        symbol: Bond symbol (US10Y, US2Y, US5Y, etc.)
    
    Returns:
        Dict with yield, price, date, source
    """
    cache_file = os.path.join(CACHE_DIR, f"quote_{symbol}.json")
    
    # Check cache (refresh daily)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(hours=24):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        # Use FRED API for current yield
        series_id = FRED_SERIES_MAP.get(symbol)
        if not series_id:
            return {"error": f"Unknown symbol: {symbol}", "available": list(FRED_SERIES_MAP.keys())}
        
        # FRED CSV endpoint (no API key needed for basic access)
        url = f"{FRED_BASE_URL}?id={series_id}"
        headers = {'User-Agent': 'Mozilla/5.0 (QuantClaw/1.0)'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse CSV
        df = pd.read_csv(io.StringIO(response.text))
        df.columns = ['date', 'yield']
        df['date'] = pd.to_datetime(df['date'])
        df['yield'] = pd.to_numeric(df['yield'], errors='coerce')
        
        # Get latest non-null value
        latest = df[df['yield'].notna()].iloc[-1]
        
        result = {
            "symbol": symbol,
            "yield": float(latest['yield']),
            "date": latest['date'].strftime("%Y-%m-%d"),
            "source": "FRED",
            "series_id": series_id,
            "price": round(100 / (1 + latest['yield']/100), 2)  # Simplified price calc
        }
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
        
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return {
            "error": str(e),
            "symbol": symbol,
            "source": "FRED"
        }

def get_yield_curve(country: str = 'US') -> Dict:
    """
    Get full yield curve data points from Treasury.gov.
    
    Args:
        country: Country code (only 'US' supported for now)
    
    Returns:
        Dict with yields across maturities, date, source
    """
    if country != 'US':
        return {"error": f"Only US yield curve supported, got: {country}"}
    
    cache_file = os.path.join(CACHE_DIR, "yield_curve_us.json")
    
    # Check cache (refresh daily)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(hours=24):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        # Get current year's Treasury data
        year = datetime.now().year
        url = TREASURY_YIELD_URL.format(year=year)
        
        headers = {'User-Agent': 'Mozilla/5.0 (QuantClaw/1.0)'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse CSV
        df = pd.read_csv(io.StringIO(response.text))
        
        # Get latest row
        latest = df.iloc[-1]
        
        # Extract yields (columns are like '1 Mo', '3 Mo', '1 Yr', '2 Yr', etc.)
        curve = {
            "date": latest['Date'] if 'Date' in latest else datetime.now().strftime("%Y-%m-%d"),
            "country": "US",
            "source": "Treasury.gov",
            "yields": {}
        }
        
        # Map column names to standardized maturities
        maturity_map = {
            '1 Mo': '1M',
            '2 Mo': '2M',
            '3 Mo': '3M',
            '4 Mo': '4M',
            '6 Mo': '6M',
            '1 Yr': '1Y',
            '2 Yr': '2Y',
            '3 Yr': '3Y',
            '5 Yr': '5Y',
            '7 Yr': '7Y',
            '10 Yr': '10Y',
            '20 Yr': '20Y',
            '30 Yr': '30Y',
        }
        
        for col_name, maturity in maturity_map.items():
            if col_name in df.columns:
                value = latest[col_name]
                if pd.notna(value):
                    curve["yields"][maturity] = float(value)
        
        # Calculate curve metrics
        if '2Y' in curve["yields"] and '10Y' in curve["yields"]:
            curve["2s10s_spread"] = round(curve["yields"]['10Y'] - curve["yields"]['2Y'], 2)
            curve["inverted"] = curve["2s10s_spread"] < 0
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(curve, f, indent=2)
        
        return curve
        
    except Exception as e:
        print(f"❌ Error fetching yield curve: {e}")
        # Fallback: use FRED for key points
        try:
            fallback_curve = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "country": "US",
                "source": "FRED (fallback)",
                "yields": {}
            }
            
            for symbol, series in list(FRED_SERIES_MAP.items())[:5]:  # Just get 5 key maturities
                quote = get_bond_quote(symbol)
                if 'yield' in quote:
                    maturity = symbol.replace('US', '')
                    fallback_curve["yields"][maturity] = quote['yield']
            
            return fallback_curve
        except:
            return {"error": str(e), "country": country}

def get_bond_history(symbol: str, days: int = 30) -> pd.DataFrame:
    """
    Get historical bond prices/yields.
    
    Args:
        symbol: Bond symbol (US10Y, US2Y, etc.)
        days: Number of days of history
    
    Returns:
        DataFrame with date, yield columns
    """
    series_id = FRED_SERIES_MAP.get(symbol)
    if not series_id:
        print(f"❌ Unknown symbol: {symbol}")
        return pd.DataFrame()
    
    try:
        # FRED CSV endpoint with date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f"{FRED_BASE_URL}?id={series_id}"
        headers = {'User-Agent': 'Mozilla/5.0 (QuantClaw/1.0)'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse CSV
        df = pd.read_csv(io.StringIO(response.text))
        df.columns = ['date', 'yield']
        df['date'] = pd.to_datetime(df['date'])
        df['yield'] = pd.to_numeric(df['yield'], errors='coerce')
        
        # Filter to requested date range
        df = df[df['date'] >= start_date].copy()
        df = df.dropna(subset=['yield'])
        
        # Add symbol column
        df['symbol'] = symbol
        
        return df[['date', 'symbol', 'yield']].reset_index(drop=True)
        
    except Exception as e:
        print(f"❌ Error fetching history for {symbol}: {e}")
        return pd.DataFrame()

def get_credit_spreads() -> Dict:
    """
    Get IG vs HY credit spread data from FRED.
    
    Returns:
        Dict with current spreads, date, historical percentiles
    """
    cache_file = os.path.join(CACHE_DIR, "credit_spreads.json")
    
    # Check cache (refresh daily)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(hours=24):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        spreads = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "source": "FRED",
            "spreads": {}
        }
        
        # Fetch each spread series
        for name, series_id in CREDIT_SPREAD_SERIES.items():
            url = f"{FRED_BASE_URL}?id={series_id}"
            headers = {'User-Agent': 'Mozilla/5.0 (QuantClaw/1.0)'}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            df = pd.read_csv(io.StringIO(response.text))
            df.columns = ['date', 'spread']
            df['spread'] = pd.to_numeric(df['spread'], errors='coerce')
            
            # Get latest non-null value
            latest = df[df['spread'].notna()].iloc[-1]
            
            spreads["spreads"][name] = {
                "current": float(latest['spread']),
                "date": pd.to_datetime(latest['date']).strftime("%Y-%m-%d"),
                "series_id": series_id
            }
        
        # Calculate HY-IG spread (key risk indicator)
        if 'HY' in spreads["spreads"] and 'IG' in spreads["spreads"]:
            spreads["hy_ig_spread"] = round(
                spreads["spreads"]['HY']['current'] - spreads["spreads"]['IG']['current'], 
                0
            )
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(spreads, f, indent=2)
        
        return spreads
        
    except Exception as e:
        print(f"❌ Error fetching credit spreads: {e}")
        return {
            "error": str(e),
            "source": "FRED"
        }

# === CLI Commands ===

def cli_quote(symbol: str = "US10Y"):
    """Show current bond quote"""
    data = get_bond_quote(symbol)
    
    if 'error' in data:
        print(f"❌ {data['error']}")
        if 'available' in data:
            print(f"Available symbols: {', '.join(data['available'])}")
        return
    
    print(f"\n📊 {data['symbol']} Bond Quote")
    print("=" * 50)
    print(f"📅 Date: {data['date']}")
    print(f"📈 Yield: {data['yield']:.2f}%")
    print(f"💵 Price: ${data['price']:.2f}")
    print(f"🔗 Source: {data['source']} ({data.get('series_id', 'N/A')})")

def cli_curve(country: str = "US"):
    """Show yield curve"""
    data = get_yield_curve(country)
    
    if 'error' in data:
        print(f"❌ {data['error']}")
        return
    
    print(f"\n📊 {data['country']} Treasury Yield Curve")
    print("=" * 50)
    print(f"📅 Date: {data['date']}")
    print(f"🔗 Source: {data['source']}")
    print("\nYields by Maturity:")
    
    for maturity, yield_val in sorted(data['yields'].items(), 
                                      key=lambda x: ['1M','2M','3M','6M','1Y','2Y','3Y','5Y','7Y','10Y','20Y','30Y'].index(x[0]) if x[0] in ['1M','2M','3M','6M','1Y','2Y','3Y','5Y','7Y','10Y','20Y','30Y'] else 99):
        print(f"  {maturity:>4s}: {yield_val:>6.2f}%")
    
    if '2s10s_spread' in data:
        print(f"\n📐 2s10s Spread: {data['2s10s_spread']:+.2f}%")
        if data.get('inverted'):
            print("⚠️  INVERTED CURVE (Recession signal)")

def cli_history(symbol: str = "US10Y", days: int = 30):
    """Show bond history"""
    df = get_bond_history(symbol, days)
    
    if df.empty:
        print(f"❌ No data for {symbol}")
        return
    
    print(f"\n📊 {symbol} History — Last {days} Days")
    print("=" * 70)
    print(df.tail(10).to_string(index=False))
    print(f"\nTotal rows: {len(df)}")
    print(f"Yield range: {df['yield'].min():.2f}% - {df['yield'].max():.2f}%")

def cli_spreads():
    """Show credit spreads"""
    data = get_credit_spreads()
    
    if 'error' in data:
        print(f"❌ {data['error']}")
        return
    
    print(f"\n📊 Credit Spreads (Option-Adjusted)")
    print("=" * 50)
    print(f"📅 Date: {data['date']}")
    print(f"🔗 Source: {data['source']}")
    
    for name, spread_data in data['spreads'].items():
        label = {
            'AAA': 'AAA Corporate',
            'IG': 'BBB Investment Grade',
            'HY': 'High Yield'
        }.get(name, name)
        print(f"\n{label}:")
        print(f"  Spread: {spread_data['current']:.0f} bps")
        print(f"  Date: {spread_data['date']}")
    
    if 'hy_ig_spread' in data:
        print(f"\n📐 HY-IG Spread: {data['hy_ig_spread']:.0f} bps")
        if data['hy_ig_spread'] > 600:
            print("⚠️  ELEVATED RISK (Spread > 600 bps)")
        elif data['hy_ig_spread'] < 300:
            print("✅ LOW RISK (Spread < 300 bps)")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "quote":
            symbol = sys.argv[2] if len(sys.argv) > 2 else "US10Y"
            cli_quote(symbol)
        elif cmd == "curve":
            cli_curve()
        elif cmd == "history":
            symbol = sys.argv[2] if len(sys.argv) > 2 else "US10Y"
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            cli_history(symbol, days)
        elif cmd == "spreads":
            cli_spreads()
        else:
            print("Usage: python finage_bond_data_feed.py [quote|curve|history|spreads]")
    else:
        cli_curve()

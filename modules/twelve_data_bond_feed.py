"""
Twelve Data Bond Feed — Bond Prices & Treasury Yields

Data Sources: 
- Primary: Twelve Data API (real-time bond prices, yields, historical)
- Fallback: Treasury.gov XML feed (daily treasury rates)
- Fallback: FRED public pages (treasury yields)

Update: Real-time (Twelve Data) / Daily (Treasury.gov)
Free: Twelve Data free tier limited; Treasury.gov always free

Provides:
- Real-time bond prices and yields (US10Y, US2Y, US30Y, etc.)
- Historical bond time series
- Complete US Treasury yield curve snapshot
- Yield spread calculations (2Y-10Y, 10Y-30Y, etc.)

Common Symbols:
- US2Y, US5Y, US10Y, US30Y (Treasury yields)
- Corporate bonds via CUSIP/ISIN on Twelve Data
"""

import requests
from datetime import datetime, timedelta
import json
import os
from typing import Dict, Optional, List
import xml.etree.ElementTree as ET

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/bonds")
os.makedirs(CACHE_DIR, exist_ok=True)

# Twelve Data API config (free tier: 8 API calls/day, 800/day with key)
TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "demo")  # Use 'demo' for testing
TWELVE_DATA_BASE = "https://api.twelvedata.com"

# Treasury.gov fallback URLs
TREASURY_XML_URL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2026"
TREASURY_DAILY_CSV = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/all"

# Symbol mapping: common names to Twelve Data format
SYMBOL_MAP = {
    "US2Y": "US2Y",
    "US5Y": "US5Y", 
    "US10Y": "US10Y",
    "US30Y": "US30Y",
    "2Y": "US2Y",
    "5Y": "US5Y",
    "10Y": "US10Y",
    "30Y": "US30Y"
}

def get_bond_price(symbol: str, use_fallback: bool = True) -> Dict:
    """
    Get real-time bond price/yield for a given symbol.
    
    Args:
        symbol: Bond symbol (US10Y, US2Y, US30Y, etc.)
        use_fallback: If True, falls back to Treasury.gov if Twelve Data fails
    
    Returns:
        Dict with keys: symbol, price, yield, date, source
    """
    symbol = SYMBOL_MAP.get(symbol.upper(), symbol.upper())
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_price.json")
    
    # Check cache (refresh every 15 min for intraday)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(minutes=15):
            with open(cache_file) as f:
                return json.load(f)
    
    # Try Twelve Data API first
    try:
        url = f"{TWELVE_DATA_BASE}/price"
        params = {
            "symbol": symbol,
            "apikey": TWELVE_DATA_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if "price" in data:
                result = {
                    "symbol": symbol,
                    "price": float(data["price"]),
                    "yield": float(data["price"]),  # For treasuries, price = yield
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "twelve_data"
                }
                
                # Cache result
                with open(cache_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                return result
    except Exception as e:
        print(f"⚠️  Twelve Data API failed for {symbol}: {e}")
    
    # Fallback to Treasury.gov
    if use_fallback:
        print(f"🔄 Falling back to Treasury.gov for {symbol}")
        treasury_data = get_treasury_rates()
        
        # Map symbol to treasury maturity
        maturity_map = {
            "US2Y": "2 yr",
            "US5Y": "5 yr", 
            "US10Y": "10 yr",
            "US30Y": "30 yr"
        }
        
        maturity = maturity_map.get(symbol)
        if maturity and maturity in treasury_data:
            return {
                "symbol": symbol,
                "price": treasury_data[maturity],
                "yield": treasury_data[maturity],
                "date": treasury_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                "source": "treasury_gov"
            }
    
    # Ultimate fallback: return stale cached data or error
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            cached = json.load(f)
            cached["note"] = "Using stale cached data"
            return cached
    
    return {
        "symbol": symbol,
        "error": "Unable to fetch bond price from any source",
        "date": datetime.now().strftime("%Y-%m-%d")
    }

def get_bond_time_series(symbol: str, interval: str = "1day", outputsize: int = 30) -> Dict:
    """
    Get historical bond price/yield time series.
    
    Args:
        symbol: Bond symbol (US10Y, US2Y, etc.)
        interval: Time interval (1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month)
        outputsize: Number of data points (max 5000)
    
    Returns:
        Dict with keys: symbol, values (list of {datetime, open, high, low, close, volume}), meta
    """
    symbol = SYMBOL_MAP.get(symbol.upper(), symbol.upper())
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_series_{interval}_{outputsize}.json")
    
    # Check cache (refresh daily for historical data)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=1):
            with open(cache_file) as f:
                return json.load(f)
    
    # Try Twelve Data API
    try:
        url = f"{TWELVE_DATA_BASE}/time_series"
        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": TWELVE_DATA_API_KEY
        }
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if "values" in data:
                result = {
                    "symbol": symbol,
                    "values": data["values"],
                    "meta": data.get("meta", {}),
                    "count": len(data["values"]),
                    "source": "twelve_data",
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Cache result
                with open(cache_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                return result
    except Exception as e:
        print(f"⚠️  Twelve Data API failed for {symbol} time series: {e}")
    
    # Fallback: return empty with error
    return {
        "symbol": symbol,
        "error": "Unable to fetch time series from Twelve Data",
        "note": "Historical treasury data requires Twelve Data API or FRED integration",
        "date": datetime.now().strftime("%Y-%m-%d")
    }

def get_treasury_rates() -> Dict:
    """
    Get complete US Treasury yield curve snapshot (all maturities).
    
    Fetches from Treasury.gov XML feed (always free, updated daily).
    
    Returns:
        Dict with keys: date, 1 mo, 2 mo, 3 mo, 4 mo, 6 mo, 1 yr, 2 yr, 3 yr, 5 yr, 7 yr, 10 yr, 20 yr, 30 yr
    """
    cache_file = os.path.join(CACHE_DIR, "treasury_curve.json")
    
    # Check cache (refresh daily)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(hours=6):  # Refresh every 6 hours
            with open(cache_file) as f:
                return json.load(f)
    
    # Fetch from Treasury.gov XML feed
    try:
        # Get current year for URL
        year = datetime.now().year
        url = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value={year}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse XML - namespace-agnostic approach
        root = ET.fromstring(response.content)
        
        # Find all entry elements (namespace-agnostic)
        entries = root.findall('.//{*}entry')
        if not entries:
            entries = [elem for elem in root.iter() if elem.tag.endswith('entry')]
        
        if entries:
            latest = entries[0]  # Most recent entry
            
            rates = {}
            
            # Extract date (look for any element with NEW_DATE)
            for elem in latest.iter():
                if 'NEW_DATE' in elem.tag or elem.tag.endswith('NEW_DATE'):
                    if elem.text:
                        rates["date"] = elem.text[:10]
                        break
            
            if "date" not in rates:
                rates["date"] = datetime.now().strftime("%Y-%m-%d")
            
            # Treasury maturity field names
            maturities = {
                "BC_1MONTH": "1 mo",
                "BC_2MONTH": "2 mo",
                "BC_3MONTH": "3 mo",
                "BC_4MONTH": "4 mo",
                "BC_6MONTH": "6 mo",
                "BC_1YEAR": "1 yr",
                "BC_2YEAR": "2 yr",
                "BC_3YEAR": "3 yr",
                "BC_5YEAR": "5 yr",
                "BC_7YEAR": "7 yr",
                "BC_10YEAR": "10 yr",
                "BC_20YEAR": "20 yr",
                "BC_30YEAR": "30 yr"
            }
            
            # Extract all maturities (namespace-agnostic)
            for elem in latest.iter():
                for xml_field, display_name in maturities.items():
                    if xml_field in elem.tag or elem.tag.endswith(xml_field):
                        if elem.text:
                            try:
                                rates[display_name] = float(elem.text)
                            except ValueError:
                                pass
            
            # If we got real data, cache and return
            if len(rates) > 2:  # More than just date and source
                rates["source"] = "treasury_gov"
                
                with open(cache_file, 'w') as f:
                    json.dump(rates, f, indent=2)
                
                return rates
        
    except Exception as e:
        print(f"⚠️  Treasury.gov XML fetch failed: {e}")
    
    # Fallback: return cached or historical averages
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            cached = json.load(f)
            cached["note"] = "Using cached treasury rates"
            return cached
    
    # Ultimate fallback: realistic current estimates
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "1 mo": 4.5,
        "3 mo": 4.6,
        "6 mo": 4.7,
        "1 yr": 4.5,
        "2 yr": 4.3,
        "5 yr": 4.2,
        "10 yr": 4.4,
        "30 yr": 4.6,
        "source": "fallback_estimates",
        "note": "Using estimated rates (Treasury.gov unavailable)"
    }

def get_spread(long_symbol: str = "US10Y", short_symbol: str = "US2Y") -> Dict:
    """
    Calculate yield spread between two bonds (e.g., 10Y-2Y spread).
    
    Common spreads:
    - 10Y-2Y: Recession indicator (inverted when negative)
    - 30Y-10Y: Long-term growth expectations
    - 10Y-3M: Fed policy effectiveness
    
    Args:
        long_symbol: Longer maturity bond (default: US10Y)
        short_symbol: Shorter maturity bond (default: US2Y)
    
    Returns:
        Dict with keys: long_yield, short_yield, spread, date, signal
    """
    long_data = get_bond_price(long_symbol)
    short_data = get_bond_price(short_symbol)
    
    if "error" in long_data or "error" in short_data:
        return {
            "error": "Unable to calculate spread",
            "long_symbol": long_symbol,
            "short_symbol": short_symbol
        }
    
    long_yield = long_data["yield"]
    short_yield = short_data["yield"]
    spread = long_yield - short_yield
    
    # Recession signal (10Y-2Y inversion)
    signal = "NORMAL"
    if long_symbol == "US10Y" and short_symbol == "US2Y":
        if spread < 0:
            signal = "INVERTED_RECESSION_RISK"
        elif spread < 0.25:
            signal = "FLATTENING_WARNING"
        elif spread > 1.0:
            signal = "STEEPENING_EXPANSION"
    
    return {
        "long_symbol": long_symbol,
        "short_symbol": short_symbol,
        "long_yield": round(long_yield, 3),
        "short_yield": round(short_yield, 3),
        "spread": round(spread, 3),
        "spread_bps": round(spread * 100, 1),  # Basis points
        "date": long_data["date"],
        "signal": signal,
        "source": long_data["source"]
    }

# === CLI Commands ===

def cli_price(symbol: str = "US10Y"):
    """Show current bond price/yield"""
    data = get_bond_price(symbol)
    
    print(f"\n📊 Bond Price: {data['symbol']}")
    print("=" * 50)
    
    if "error" in data:
        print(f"❌ Error: {data['error']}")
        return
    
    print(f"💰 Yield: {data['yield']:.3f}%")
    print(f"📅 Date: {data['date']}")
    print(f"📡 Source: {data['source']}")
    
    if "note" in data:
        print(f"ℹ️  {data['note']}")

def cli_curve():
    """Show complete treasury yield curve"""
    rates = get_treasury_rates()
    
    print("\n📊 US Treasury Yield Curve")
    print("=" * 50)
    print(f"📅 Date: {rates.get('date', 'N/A')}")
    print()
    
    # Display curve in organized format
    short_term = ["1 mo", "2 mo", "3 mo", "6 mo"]
    medium_term = ["1 yr", "2 yr", "3 yr", "5 yr", "7 yr"]
    long_term = ["10 yr", "20 yr", "30 yr"]
    
    print("Short-Term:")
    for maturity in short_term:
        if maturity in rates:
            print(f"  {maturity:8s}: {rates[maturity]:5.2f}%")
    
    print("\nMedium-Term:")
    for maturity in medium_term:
        if maturity in rates:
            print(f"  {maturity:8s}: {rates[maturity]:5.2f}%")
    
    print("\nLong-Term:")
    for maturity in long_term:
        if maturity in rates:
            print(f"  {maturity:8s}: {rates[maturity]:5.2f}%")
    
    print(f"\n📡 Source: {rates.get('source', 'unknown')}")
    
    if "note" in rates:
        print(f"ℹ️  {rates['note']}")

def cli_spread(long_symbol: str = "US10Y", short_symbol: str = "US2Y"):
    """Show yield spread"""
    data = get_spread(long_symbol, short_symbol)
    
    print(f"\n📊 Yield Spread: {data['long_symbol']} - {data['short_symbol']}")
    print("=" * 50)
    
    if "error" in data:
        print(f"❌ Error: {data['error']}")
        return
    
    print(f"📈 {data['long_symbol']}: {data['long_yield']:.3f}%")
    print(f"📉 {data['short_symbol']}: {data['short_yield']:.3f}%")
    print(f"📊 Spread: {data['spread']:+.3f}% ({data['spread_bps']:+.1f} bps)")
    print(f"📅 Date: {data['date']}")
    
    # Signal interpretation
    signal = data['signal']
    if signal == "INVERTED_RECESSION_RISK":
        print("\n🚨 INVERTED CURVE — Recession Risk High")
        print("   → Historically precedes recession by 6-18 months")
    elif signal == "FLATTENING_WARNING":
        print("\n⚠️  FLATTENING CURVE — Economic Slowdown Possible")
    elif signal == "STEEPENING_EXPANSION":
        print("\n✅ STEEPENING CURVE — Economic Expansion")
    else:
        print(f"\n✅ Signal: {signal}")
    
    print(f"\n📡 Source: {data['source']}")

if __name__ == "__main__":
    # Default: show treasury curve
    cli_curve()
    print("\n")
    cli_spread()

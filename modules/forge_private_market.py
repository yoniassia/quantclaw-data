"""
Forge Private Market API — Pre-IPO Secondary Market Trading Data

Data Source: Forge Global (https://forgeglobal.com)
Update: Daily
Free Tier: 50 calls/day, non-real-time data
Coverage: Private company share prices, secondary market transactions, pre-IPO valuations

Provides:
- Private company share prices
- Liquidity scores and trading volume
- Pre-IPO valuations and funding round data
- Secondary market transaction trends
- Sector breakdowns for private markets

Usage:
- Track pre-IPO valuations for exit timing
- Monitor secondary market liquidity for private holdings
- Identify arbitrage between private and expected public valuations
- Assess private market sentiment ahead of IPOs
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/forge")
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_URL = "https://api.forgeglobal.com/v1"

# Note: Requires free API token from forgeglobal.com (50 calls/day limit)
def _get_api_key() -> Optional[str]:
    """Get Forge API key from environment or config"""
    return os.getenv("FORGE_API_KEY")

def get_company_price(symbol: str, date: Optional[str] = None) -> Dict:
    """
    Get private company share price and valuation data.
    
    Args:
        symbol: Company identifier (e.g., 'stripe', 'spacex')
        date: Date in YYYY-MM-DD format (default: latest)
    
    Returns:
        Dict with share_price, market_cap, last_trade, liquidity_score
    """
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_price.json")
    
    # Check cache (refresh daily)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=1):
            with open(cache_file) as f:
                return json.load(f)
    
    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "Forge API key not configured",
            "note": "Set FORGE_API_KEY environment variable. Sign up at forgeglobal.com (free tier: 50 calls/day)",
            "symbol": symbol
        }
    
    try:
        url = f"{BASE_URL}/companies/{symbol}/prices"
        params = {"token": api_key}
        if date:
            params["date"] = date
        
        headers = {"User-Agent": "QuantClaw-Data/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            result = {
                "symbol": symbol,
                "company_name": data.get("company_name", symbol),
                "share_price": data.get("price_per_share"),
                "market_cap": data.get("valuation"),
                "last_trade_date": data.get("last_trade_date"),
                "liquidity_score": data.get("liquidity_score", 0),  # 0-100
                "sector": data.get("sector"),
                "funding_stage": data.get("stage"),  # e.g., "Series E", "Pre-IPO"
                "total_funding": data.get("total_funding_raised"),
                "last_funding_round": data.get("last_funding_round"),
                "premium_to_last_round": data.get("premium_discount_pct"),
                "timestamp": datetime.now().isoformat(),
                "source": "forge_global"
            }
            
            # Cache result
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            return result
        
        elif response.status_code == 404:
            return {
                "error": "Company not found on Forge",
                "symbol": symbol,
                "note": "Check symbol name or company may not have secondary market data"
            }
        elif response.status_code == 429:
            return {
                "error": "Rate limit exceeded",
                "symbol": symbol,
                "note": "Free tier: 50 calls/day. Wait or upgrade at forgeglobal.com"
            }
        else:
            return {
                "error": f"HTTP {response.status_code}",
                "symbol": symbol,
                "message": response.text[:200]
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "error": "Network error",
            "symbol": symbol,
            "message": str(e)
        }
    except Exception as e:
        return {
            "error": "Unexpected error",
            "symbol": symbol,
            "message": str(e)
        }

def get_trending_companies(limit: int = 10) -> List[Dict]:
    """
    Get most actively traded private companies on Forge.
    
    Args:
        limit: Number of companies to return (default 10)
    
    Returns:
        List of dicts with company data sorted by trading volume
    """
    api_key = _get_api_key()
    if not api_key:
        return [{
            "error": "Forge API key not configured",
            "note": "Set FORGE_API_KEY environment variable"
        }]
    
    try:
        url = f"{BASE_URL}/companies/trending"
        params = {"token": api_key, "limit": limit}
        headers = {"User-Agent": "QuantClaw-Data/1.0"}
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            companies = data.get("companies", [])
            
            return [
                {
                    "symbol": c.get("symbol"),
                    "company_name": c.get("name"),
                    "share_price": c.get("price"),
                    "market_cap": c.get("market_cap"),
                    "volume_30d": c.get("volume_30d"),
                    "price_change_30d_pct": c.get("price_change_pct"),
                    "liquidity_score": c.get("liquidity_score"),
                    "sector": c.get("sector")
                }
                for c in companies
            ]
        else:
            return [{
                "error": f"HTTP {response.status_code}",
                "message": response.text[:200]
            }]
            
    except Exception as e:
        return [{
            "error": "Error fetching trending companies",
            "message": str(e)
        }]

def get_sector_valuations(sector: str = "all") -> Dict:
    """
    Get aggregate valuation metrics for private market sector.
    
    Args:
        sector: Sector name (e.g., 'fintech', 'ai', 'biotech') or 'all'
    
    Returns:
        Dict with median valuation, count, liquidity trends
    """
    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "Forge API key not configured",
            "note": "Set FORGE_API_KEY environment variable"
        }
    
    try:
        url = f"{BASE_URL}/sectors/{sector}/metrics"
        params = {"token": api_key}
        headers = {"User-Agent": "QuantClaw-Data/1.0"}
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            return {
                "sector": sector,
                "company_count": data.get("total_companies"),
                "median_valuation": data.get("median_valuation"),
                "median_revenue_multiple": data.get("median_revenue_multiple"),
                "avg_liquidity_score": data.get("avg_liquidity_score"),
                "total_volume_30d": data.get("total_volume_30d"),
                "price_trend_30d_pct": data.get("price_trend_pct"),
                "ipo_pipeline_count": data.get("expected_ipos_12mo"),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "error": f"HTTP {response.status_code}",
                "sector": sector,
                "message": response.text[:200]
            }
            
    except Exception as e:
        return {
            "error": "Error fetching sector data",
            "sector": sector,
            "message": str(e)
        }

def get_liquidity_events(days: int = 30) -> List[Dict]:
    """
    Get recent liquidity events (IPO filings, acquisitions, tender offers).
    
    Args:
        days: Lookback period in days (default 30)
    
    Returns:
        List of liquidity events with company and event details
    """
    api_key = _get_api_key()
    if not api_key:
        return [{
            "error": "Forge API key not configured",
            "note": "Set FORGE_API_KEY environment variable"
        }]
    
    try:
        url = f"{BASE_URL}/events/liquidity"
        params = {"token": api_key, "days": days}
        headers = {"User-Agent": "QuantClaw-Data/1.0"}
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])
            
            return [
                {
                    "event_type": e.get("type"),  # "IPO_FILING", "ACQUISITION", "TENDER"
                    "company_symbol": e.get("symbol"),
                    "company_name": e.get("company"),
                    "event_date": e.get("date"),
                    "valuation": e.get("valuation"),
                    "details": e.get("details"),
                    "secondary_market_impact": e.get("price_change_pct")
                }
                for e in events
            ]
        else:
            return [{
                "error": f"HTTP {response.status_code}",
                "message": response.text[:200]
            }]
            
    except Exception as e:
        return [{
            "error": "Error fetching liquidity events",
            "message": str(e)
        }]

# === CLI Commands ===

def cli_price(symbol: str):
    """Show private company price and valuation"""
    data = get_company_price(symbol)
    
    if "error" in data:
        print(f"❌ {data['error']}")
        if "note" in data:
            print(f"ℹ️  {data['note']}")
        return
    
    print(f"\n💰 {data['company_name']} ({data['symbol']})")
    print("=" * 60)
    print(f"💵 Share Price: ${data['share_price']:,.2f}" if data.get('share_price') else "💵 Share Price: N/A")
    print(f"🏢 Market Cap: ${data.get('market_cap', 0)/1e9:.2f}B" if data.get('market_cap') else "🏢 Market Cap: N/A")
    print(f"📅 Last Trade: {data.get('last_trade_date', 'N/A')}")
    print(f"💧 Liquidity Score: {data.get('liquidity_score', 0)}/100")
    print(f"📊 Sector: {data.get('sector', 'N/A')}")
    print(f"🚀 Stage: {data.get('funding_stage', 'N/A')}")
    
    if data.get('premium_to_last_round'):
        prem = data['premium_to_last_round']
        emoji = "📈" if prem > 0 else "📉"
        print(f"{emoji} vs Last Round: {prem:+.1f}%")

def cli_trending():
    """Show most actively traded private companies"""
    companies = get_trending_companies(10)
    
    if companies and "error" in companies[0]:
        print(f"❌ {companies[0]['error']}")
        return
    
    print("\n🔥 Trending Private Companies (by Volume)")
    print("=" * 80)
    print(f"{'Symbol':<15} {'Price':>12} {'Mkt Cap':>12} {'30d Change':>12} {'Liquidity':>10}")
    print("-" * 80)
    
    for c in companies:
        symbol = c.get('symbol', 'N/A')
        price = f"${c.get('share_price', 0):,.0f}" if c.get('share_price') else "N/A"
        mcap = f"${c.get('market_cap', 0)/1e9:.1f}B" if c.get('market_cap') else "N/A"
        change = f"{c.get('price_change_30d_pct', 0):+.1f}%" if c.get('price_change_30d_pct') else "N/A"
        liq = f"{c.get('liquidity_score', 0)}/100"
        
        print(f"{symbol:<15} {price:>12} {mcap:>12} {change:>12} {liq:>10}")

def cli_events():
    """Show recent liquidity events"""
    events = get_liquidity_events(30)
    
    if events and "error" in events[0]:
        print(f"❌ {events[0]['error']}")
        return
    
    print("\n📋 Recent Liquidity Events (Last 30 Days)")
    print("=" * 80)
    
    for e in events:
        print(f"\n{e.get('event_type', 'N/A')}: {e.get('company_name', 'N/A')}")
        print(f"  📅 {e.get('event_date', 'N/A')}")
        print(f"  💰 Valuation: ${e.get('valuation', 0)/1e9:.2f}B" if e.get('valuation') else "  💰 Valuation: N/A")
        if e.get('secondary_market_impact'):
            print(f"  📊 Market Impact: {e['secondary_market_impact']:+.1f}%")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "price" and len(sys.argv) > 2:
            cli_price(sys.argv[2])
        elif command == "trending":
            cli_trending()
        elif command == "events":
            cli_events()
        else:
            print("Usage: python forge_private_market.py [price SYMBOL | trending | events]")
    else:
        cli_trending()

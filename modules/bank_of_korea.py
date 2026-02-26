"""
Bank of Korea (BOK) Module — Phase 635

Data Sources:
- Bank of Korea Economic Statistics System (ECOS) API (https://ecos.bok.or.kr/)
- OECD Korea data
- World Bank Korea indicators
- Trading Economics Korea data (scraping where available)

BOK Coverage:
- Base Rate: BOK Base Rate (policy rate)
- M1/M2: Monetary aggregates
- FX Reserves: Foreign exchange reserves
- Balance of Payments: Current account, capital account
- Banking: Lending rates, deposits
- Inflation: CPI, core CPI, PPI
- GDP: Real GDP growth

Note: BOK ECOS API requires free API key from https://ecos.bok.or.kr/
This module uses fallback to OECD/World Bank when BOK API key not configured.
"""

import os
import sys
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# Simple cache dictionary
_cache = {}

def fetch_json(url: str) -> Dict:
    """Fetch JSON from URL with error handling"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return {}

# BOK ECOS API (requires API key)
BOK_API_KEY = os.getenv("BOK_API_KEY", "")
BOK_BASE = f"https://ecos.bok.or.kr/api/StatisticSearch/{BOK_API_KEY}/json/en"

# Fallback: OECD Korea data
OECD_BASE = "https://stats.oecd.org/sdmx-json/data/DP_LIVE/KOR"
WB_BASE = "https://api.worldbank.org/v2/country/KOR/indicator"


def get_base_rate() -> Dict:
    """
    Get Bank of Korea base rate (policy rate).
    
    Returns:
        Dict with current and historical base rates
    """
    cache_key = "base_rate"
    if cache_key in _cache:
        return _cache[cache_key]
    
    try:
        # Try BOK API first
        if BOK_API_KEY:
            # BOK stat code 722 = Base Rate
            url = f"{BOK_BASE}/1/100/722/D/20200101/20991231"
            data = fetch_json(url)
            
            if data and "StatisticSearch" in data and "row" in data["StatisticSearch"]:
                rows = data["StatisticSearch"]["row"]
                result = {
                    "source": "Bank of Korea ECOS",
                    "indicator": "Base Rate",
                    "unit": "% per annum",
                    "data": []
                }
                
                for row in rows[-50:]:  # Last 50 observations
                    result["data"].append({
                        "date": row.get("TIME"),
                        "rate": float(row.get("DATA_VALUE", 0))
                    })
                
                if result["data"]:
                    result["current"] = result["data"][-1]
                
                _cache[cache_key] = result  # ttl=)  # 12h cache
                return result
        
        # Fallback: OECD short-term interest rates
        url = f"{OECD_BASE}.STINT.TOT.PC_PA.Q/OECD?startPeriod=2018-Q1"
        data = fetch_json(url)
        
        result = {
            "source": "OECD (Fallback)",
            "indicator": "Short-term Interest Rate",
            "unit": "% per annum",
            "data": []
        }
        
        if data and "dataSets" in data and data["dataSets"]:
            observations = data["dataSets"][0].get("observations", {})
            structure = data.get("structure", {})
            
            for key, values in observations.items():
                value = values[0] if values else None
                if value is not None:
                    result["data"].append({
                        "value": round(value, 2)
                    })
        
        if result["data"]:
            result["current"] = result["data"][-1]
        
        _cache[cache_key] = result  # ttl=)
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "source": "BOK/OECD",
            "message": "Could not fetch base rate data"
        }


def get_monetary_aggregates() -> Dict:
    """
    Get M1 and M2 money supply.
    
    Returns:
        Dict with M1, M2 data
    """
    cache_key = "monetary_aggregates"
    if cache_key in _cache:
        return _cache[cache_key]
    
    try:
        result = {
            "source": "OECD",
            "country": "Korea",
            "indicator": "Money Supply",
            "m1": {},
            "m2": {}
        }
        
        # M1
        m1_url = f"{OECD_BASE}.MABMM101.IXOBSA.Q/OECD?startPeriod=2018-Q1"
        m1_data = fetch_json(m1_url)
        
        if m1_data and "dataSets" in m1_data:
            observations = m1_data["dataSets"][0].get("observations", {})
            m1_values = []
            for key, values in observations.items():
                if values and values[0] is not None:
                    m1_values.append({"value": round(values[0], 2)})
            
            if m1_values:
                result["m1"] = {
                    "unit": "Index",
                    "data": m1_values[-12:],  # Last 12 quarters
                    "latest": m1_values[-1]
                }
        
        # M2  
        m2_url = f"{OECD_BASE}.MABMM301.IXOBSA.Q/OECD?startPeriod=2018-Q1"
        m2_data = fetch_json(m2_url)
        
        if m2_data and "dataSets" in m2_data:
            observations = m2_data["dataSets"][0].get("observations", {})
            m2_values = []
            for key, values in observations.items():
                if values and values[0] is not None:
                    m2_values.append({"value": round(values[0], 2)})
            
            if m2_values:
                result["m2"] = {
                    "unit": "Index",
                    "data": m2_values[-12:],
                    "latest": m2_values[-1]
                }
        
        _cache[cache_key] = result  # ttl=)  # 24h cache
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "source": "OECD",
            "message": "Could not fetch monetary data"
        }


def get_fx_reserves() -> Dict:
    """
    Get Korea foreign exchange reserves.
    
    Returns:
        Dict with FX reserves in USD
    """
    cache_key = "fx_reserves"
    if cache_key in _cache:
        return _cache[cache_key]
    
    try:
        # World Bank Total Reserves (includes gold)
        url = f"{WB_BASE}/FI.RES.TOTL.CD?format=json&per_page=20"
        data = fetch_json(url)
        
        result = {
            "source": "World Bank",
            "country": "Korea",
            "indicator": "Total Reserves (incl. gold)",
            "unit": "USD",
            "data": []
        }
        
        if data and len(data) > 1:
            for entry in data[1]:
                if entry.get("value"):
                    result["data"].append({
                        "year": int(entry["date"]),
                        "reserves_usd": entry["value"],
                        "reserves_billion": round(entry["value"] / 1e9, 2)
                    })
        
        result["data"].sort(key=lambda x: x["year"], reverse=True)
        
        if result["data"]:
            result["latest"] = result["data"][0]
        
        _cache[cache_key] = result  # ttl=)  # 24h cache
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "source": "World Bank",
            "message": "Could not fetch FX reserves"
        }


def get_inflation_data(years: int = 10) -> Dict:
    """
    Get Korea inflation (CPI).
    
    Args:
        years: Number of years of history
        
    Returns:
        Dict with CPI year-over-year change
    """
    cache_key = f"inflation_{years}"
    if cache_key in _cache:
        return _cache[cache_key]
    
    try:
        # World Bank CPI
        url = f"{WB_BASE}/FP.CPI.TOTL.ZG?format=json&per_page=100"
        data = fetch_json(url)
        
        result = {
            "source": "World Bank",
            "country": "Korea",
            "indicator": "Inflation (CPI)",
            "unit": "Annual %",
            "data": []
        }
        
        if data and len(data) > 1:
            for entry in data[1][:years]:
                if entry.get("value") is not None:
                    result["data"].append({
                        "year": int(entry["date"]),
                        "inflation_pct": round(entry["value"], 2)
                    })
        
        result["data"].sort(key=lambda x: x["year"], reverse=True)
        
        if result["data"]:
            result["latest"] = result["data"][0]
        
        _cache[cache_key] = result  # ttl=)  # 24h cache
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "source": "World Bank",
            "message": "Could not fetch inflation data"
        }


def get_gdp_growth(years: int = 10) -> Dict:
    """
    Get Korea GDP growth.
    
    Args:
        years: Number of years of history
        
    Returns:
        Dict with GDP growth rates
    """
    cache_key = f"gdp_{years}"
    if cache_key in _cache:
        return _cache[cache_key]
    
    try:
        # World Bank GDP growth
        url = f"{WB_BASE}/NY.GDP.MKTP.KD.ZG?format=json&per_page=100"
        data = fetch_json(url)
        
        result = {
            "source": "World Bank",
            "country": "Korea",
            "indicator": "GDP Growth",
            "unit": "Annual %",
            "data": []
        }
        
        if data and len(data) > 1:
            for entry in data[1][:years]:
                if entry.get("value") is not None:
                    result["data"].append({
                        "year": int(entry["date"]),
                        "growth_pct": round(entry["value"], 2)
                    })
        
        result["data"].sort(key=lambda x: x["year"], reverse=True)
        
        if result["data"]:
            result["latest"] = result["data"][0]
        
        _cache[cache_key] = result  # ttl=)  # 24h cache
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "source": "World Bank",
            "message": "Could not fetch GDP data"
        }


def get_current_account() -> Dict:
    """
    Get Korea current account balance.
    
    Returns:
        Dict with current account balance
    """
    cache_key = "current_account"
    if cache_key in _cache:
        return _cache[cache_key]
    
    try:
        # World Bank Current Account Balance
        url = f"{WB_BASE}/BN.CAB.XOKA.CD?format=json&per_page=20"
        data = fetch_json(url)
        
        result = {
            "source": "World Bank",
            "country": "Korea",
            "indicator": "Current Account Balance",
            "unit": "USD",
            "data": []
        }
        
        if data and len(data) > 1:
            for entry in data[1]:
                if entry.get("value") is not None:
                    result["data"].append({
                        "year": int(entry["date"]),
                        "balance_usd": entry["value"],
                        "balance_billion": round(entry["value"] / 1e9, 2)
                    })
        
        result["data"].sort(key=lambda x: x["year"], reverse=True)
        
        if result["data"]:
            result["latest"] = result["data"][0]
        
        _cache[cache_key] = result  # ttl=)  # 24h cache
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "source": "World Bank",
            "message": "Could not fetch current account data"
        }


def get_dashboard() -> Dict:
    """
    Get comprehensive Bank of Korea dashboard.
    
    Returns:
        Dict with all key BOK indicators
    """
    cache_key = "dashboard"
    if cache_key in _cache:
        return _cache[cache_key]
    
    dashboard = {
        "country": "Korea",
        "central_bank": "Bank of Korea",
        "timestamp": datetime.now().isoformat(),
        "base_rate": get_base_rate(),
        "monetary_aggregates": get_monetary_aggregates(),
        "fx_reserves": get_fx_reserves(),
        "inflation": get_inflation_data(years=5),
        "gdp": get_gdp_growth(years=5),
        "current_account": get_current_account()
    }
    
    _cache[cache_key] = dashboard  # 1h cache for dashboard
    return dashboard


if __name__ == "__main__":
    # CLI test
    print("Bank of Korea Module")
    print("=" * 50)
    
    dashboard = get_dashboard()
    
    # Print base rate
    rate = dashboard["base_rate"]
    if "current" in rate:
        print(f"\n🏦 Base Rate: {rate['current'].get('rate', rate['current'].get('value', 'N/A'))}%")
    
    # Print FX reserves
    fx = dashboard["fx_reserves"]
    if "latest" in fx and fx["latest"]:
        print(f"💱 FX Reserves: ${fx['latest']['reserves_billion']}B ({fx['latest']['year']})")
    
    # Print inflation
    infl = dashboard["inflation"]
    if "latest" in infl and infl["latest"]:
        print(f"📈 Inflation: {infl['latest']['inflation_pct']}% ({infl['latest']['year']})")
    
    # Print GDP
    gdp = dashboard["gdp"]
    if "latest" in gdp and gdp["latest"]:
        print(f"📊 GDP Growth: {gdp['latest']['growth_pct']}% ({gdp['latest']['year']})")
    
    # Print current account
    ca = dashboard["current_account"]
    if "latest" in ca and ca["latest"]:
        print(f"💰 Current Account: ${ca['latest']['balance_billion']}B ({ca['latest']['year']})")

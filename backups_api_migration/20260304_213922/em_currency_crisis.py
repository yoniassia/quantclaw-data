#!/usr/bin/env python3
"""
EM Currency Crisis Monitor Module

Monitors emerging market currency crisis indicators:
- FX Reserves (FRED, BIS, IMF)
- Current Account Balance (FRED, IMF)
- Real Effective Exchange Rates (BIS, FRED)
- Currency crisis risk scoring

Data Sources:
- FRED API (Federal Reserve Economic Data)
- BIS (Bank for International Settlements) - via FRED proxy where available
- IMF International Financial Statistics

Phase: 184
Author: QUANTCLAW DATA Build Agent
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

# FRED API Configuration
# Get free API key at: https://fredaccount.stlouisfed.org/apikeys
FRED_API_KEY = ""  # Set via environment variable FRED_API_KEY or register for free key
FRED_API_BASE = "https://api.stlouisfed.org/fred"

# Key EM Country Series IDs from FRED
EM_FX_RESERVES_SERIES = {
    # Major Emerging Markets - FX Reserves (USD Millions)
    "TRESEGBRM052N": "Brazil - Total Reserves",
    "TRESEGTOTLM052N": "Mexico - Total Reserves", 
    "TRESEGRUM052N": "Russia - Total Reserves",
    "TRESEGIDM052N": "India - Total Reserves",
    "TRESEGCNM052N": "China - Total Reserves",
    "TRESEGTRMM052N": "Turkey - Total Reserves",
    "TRESEGZAM052N": "South Africa - Total Reserves",
    "TRESEGARM052N": "Argentina - Total Reserves",
    # Additional EM economies
    "MYSFRTOTLMM052N": "Malaysia - Total Reserves",
    "THSRTOTMM052N": "Thailand - Total Reserves",
    "PHIRTOTMM052N": "Philippines - Total Reserves",
    "IDNFRTOTMM052N": "Indonesia - Total Reserves",
    "POLFRTOTMM052N": "Poland - Total Reserves",
}

# Current Account Balance Series
EM_CURRENT_ACCOUNT_SERIES = {
    "BPBLTB02BRQ188S": "Brazil - Current Account Balance",
    "BPBLTB02MXQ188S": "Mexico - Current Account Balance",
    "BPBLTB02RUQ188S": "Russia - Current Account Balance",
    "BPBLTB02INQ188S": "India - Current Account Balance",
    "BPBLTB02CNQ188S": "China - Current Account Balance",
    "BPBLTB02TRQ188S": "Turkey - Current Account Balance",
    "BPBLTB02ZAQ188S": "South Africa - Current Account Balance",
    "BPBLTB02ARQ188S": "Argentina - Current Account Balance",
}

# Real Effective Exchange Rate Series (BIS via FRED)
EM_REER_SERIES = {
    "RBRBIS": "Brazil - Real Broad Effective Exchange Rate",
    "RBMXBIS": "Mexico - Real Broad Effective Exchange Rate",
    "RBRUBIS": "Russia - Real Broad Effective Exchange Rate",
    "RBINBIS": "India - Real Broad Effective Exchange Rate",
    "RBCNBIS": "China - Real Broad Effective Exchange Rate",
    "RBTRBIS": "Turkey - Real Broad Effective Exchange Rate",
    "RBZABIS": "South Africa - Real Broad Effective Exchange Rate",
    "RBARBIS": "Argentina - Real Broad Effective Exchange Rate",
}

# Crisis Thresholds (Academic literature-based)
CRISIS_THRESHOLDS = {
    "fx_reserves_months_imports": 3.0,  # Below 3 months = high risk
    "current_account_gdp_pct": -5.0,    # Below -5% GDP = vulnerable
    "reer_deviation_pct": 20.0,          # >20% overvaluation = risk
    "fx_reserves_change_6m": -20.0,      # >20% decline in 6mo = stress
}

# Country GDP for reserve adequacy calculations (2024 est, USD Billions)
COUNTRY_GDP = {
    "Brazil": 2126,
    "Mexico": 1789,
    "Russia": 2240,
    "India": 3937,
    "China": 18532,
    "Turkey": 1108,
    "South Africa": 401,
    "Argentina": 640,
    "Malaysia": 447,
    "Thailand": 544,
    "Philippines": 469,
    "Indonesia": 1391,
    "Poland": 811,
}


def fetch_fred_series(series_id: str, start_date: Optional[str] = None, 
                     end_date: Optional[str] = None, limit: int = 1000) -> Dict:
    """
    Fetch data from FRED API
    
    Args:
        series_id: FRED series ID
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        limit: Maximum number of observations
        
    Returns:
        Dict with series data
    """
    import os
    
    # Check for API key in environment or module constant
    api_key = os.environ.get("FRED_API_KEY", FRED_API_KEY)
    if not api_key:
        return {
            "error": "FRED API key required. Set FRED_API_KEY environment variable or register for free at https://fredaccount.stlouisfed.org/apikeys"
        }
    
    url = f"{FRED_API_BASE}/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "limit": limit,
    }
    
    if start_date:
        params["observation_start"] = start_date
    if end_date:
        params["observation_end"] = end_date
        
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "observations" not in data:
            return {"error": f"No data for series {series_id}"}
            
        # Clean data
        observations = []
        for obs in data["observations"]:
            if obs["value"] != ".":
                try:
                    observations.append({
                        "date": obs["date"],
                        "value": float(obs["value"])
                    })
                except (ValueError, KeyError):
                    continue
                    
        return {
            "series_id": series_id,
            "observations": observations,
            "count": len(observations),
            "latest": observations[-1] if observations else None
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"FRED API error: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from FRED"}


def get_fx_reserves(country: str) -> Dict:
    """
    Get FX reserves for a specific EM country
    
    Args:
        country: Country name (e.g., "Brazil", "Mexico")
        
    Returns:
        Dict with FX reserves data and analysis
    """
    # Find matching series
    series_id = None
    for sid, desc in EM_FX_RESERVES_SERIES.items():
        if country.lower() in desc.lower():
            series_id = sid
            break
            
    if not series_id:
        return {"error": f"No FX reserves data available for {country}"}
        
    # Fetch last 2 years of data
    start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    data = fetch_fred_series(series_id, start_date=start_date)
    
    if "error" in data:
        return data
        
    observations = data["observations"]
    if not observations:
        return {"error": "No data available"}
        
    # Analysis
    latest = observations[-1]
    six_months_ago = next((obs for obs in reversed(observations) 
                          if (datetime.now() - datetime.strptime(obs["date"], "%Y-%m-%d")).days >= 180), 
                         observations[0])
    one_year_ago = next((obs for obs in reversed(observations) 
                        if (datetime.now() - datetime.strptime(obs["date"], "%Y-%m-%d")).days >= 365), 
                       observations[0])
    
    # Calculate changes
    change_6m_pct = ((latest["value"] - six_months_ago["value"]) / six_months_ago["value"] * 100) if six_months_ago["value"] > 0 else 0
    change_1y_pct = ((latest["value"] - one_year_ago["value"]) / one_year_ago["value"] * 100) if one_year_ago["value"] > 0 else 0
    
    # Risk scoring
    risk_level = "LOW"
    risk_factors = []
    
    if change_6m_pct < CRISIS_THRESHOLDS["fx_reserves_change_6m"]:
        risk_level = "HIGH"
        risk_factors.append(f"Reserves down {abs(change_6m_pct):.1f}% in 6 months")
    elif change_6m_pct < -10:
        risk_level = "MEDIUM"
        risk_factors.append(f"Reserves declining (-{abs(change_6m_pct):.1f}% in 6 months)")
        
    return {
        "country": country,
        "series_id": series_id,
        "latest_date": latest["date"],
        "reserves_usd_millions": latest["value"],
        "reserves_usd_billions": round(latest["value"] / 1000, 2),
        "change_6m_pct": round(change_6m_pct, 2),
        "change_1y_pct": round(change_1y_pct, 2),
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "historical_data": observations[-12:]  # Last 12 observations
    }


def get_current_account(country: str) -> Dict:
    """
    Get current account balance for a specific EM country
    
    Args:
        country: Country name
        
    Returns:
        Dict with current account data and analysis
    """
    # Find matching series
    series_id = None
    for sid, desc in EM_CURRENT_ACCOUNT_SERIES.items():
        if country.lower() in desc.lower():
            series_id = sid
            break
            
    if not series_id:
        return {"error": f"No current account data available for {country}"}
        
    # Fetch last 5 years of quarterly data
    start_date = (datetime.now() - timedelta(days=1825)).strftime("%Y-%m-%d")
    data = fetch_fred_series(series_id, start_date=start_date)
    
    if "error" in data:
        return data
        
    observations = data["observations"]
    if not observations:
        return {"error": "No data available"}
        
    latest = observations[-1]
    
    # Get GDP for the country
    gdp = COUNTRY_GDP.get(country, 0)
    ca_to_gdp = (latest["value"] / (gdp * 1000)) * 100 if gdp > 0 else 0  # Convert billions to millions
    
    # Risk scoring
    risk_level = "LOW"
    risk_factors = []
    
    if ca_to_gdp < CRISIS_THRESHOLDS["current_account_gdp_pct"]:
        risk_level = "HIGH"
        risk_factors.append(f"Large current account deficit: {ca_to_gdp:.1f}% of GDP")
    elif ca_to_gdp < -3.0:
        risk_level = "MEDIUM"
        risk_factors.append(f"Current account deficit: {ca_to_gdp:.1f}% of GDP")
        
    return {
        "country": country,
        "series_id": series_id,
        "latest_date": latest["date"],
        "balance_usd_millions": latest["value"],
        "balance_usd_billions": round(latest["value"] / 1000, 2),
        "gdp_usd_billions": gdp,
        "balance_pct_gdp": round(ca_to_gdp, 2),
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "historical_data": observations[-8:]  # Last 8 quarters
    }


def get_reer(country: str) -> Dict:
    """
    Get Real Effective Exchange Rate (REER) for a specific EM country
    
    Args:
        country: Country name
        
    Returns:
        Dict with REER data and overvaluation analysis
    """
    # Find matching series
    series_id = None
    for sid, desc in EM_REER_SERIES.items():
        if country.lower() in desc.lower():
            series_id = sid
            break
            
    if not series_id:
        return {"error": f"No REER data available for {country}"}
        
    # Fetch last 10 years for trend analysis
    start_date = (datetime.now() - timedelta(days=3650)).strftime("%Y-%m-%d")
    data = fetch_fred_series(series_id, start_date=start_date)
    
    if "error" in data:
        return data
        
    observations = data["observations"]
    if not observations:
        return {"error": "No data available"}
        
    latest = observations[-1]
    
    # Calculate 10-year average
    values = [obs["value"] for obs in observations]
    avg_10y = sum(values) / len(values)
    
    # Deviation from average
    deviation_pct = ((latest["value"] - avg_10y) / avg_10y) * 100
    
    # Risk scoring
    risk_level = "LOW"
    risk_factors = []
    
    if abs(deviation_pct) > CRISIS_THRESHOLDS["reer_deviation_pct"]:
        if deviation_pct > 0:
            risk_level = "HIGH"
            risk_factors.append(f"Currency overvalued by {deviation_pct:.1f}%")
        else:
            risk_level = "MEDIUM"
            risk_factors.append(f"Currency undervalued by {abs(deviation_pct):.1f}%")
    elif abs(deviation_pct) > 10:
        risk_level = "MEDIUM"
        risk_factors.append(f"Currency deviation: {deviation_pct:+.1f}%")
        
    return {
        "country": country,
        "series_id": series_id,
        "latest_date": latest["date"],
        "reer_index": round(latest["value"], 2),
        "reer_10y_avg": round(avg_10y, 2),
        "deviation_pct": round(deviation_pct, 2),
        "valuation": "overvalued" if deviation_pct > 10 else "undervalued" if deviation_pct < -10 else "fair",
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "historical_data": observations[-24:]  # Last 24 months
    }


def calculate_crisis_risk_score(country: str) -> Dict:
    """
    Calculate comprehensive currency crisis risk score for an EM country
    
    Combines:
    - FX reserves adequacy
    - Current account balance
    - REER overvaluation
    
    Returns:
        Dict with composite risk score and detailed breakdown
    """
    # Fetch all indicators
    fx_reserves = get_fx_reserves(country)
    current_account = get_current_account(country)
    reer = get_reer(country)
    
    # Check for errors
    errors = []
    if "error" in fx_reserves:
        errors.append(f"FX Reserves: {fx_reserves['error']}")
    if "error" in current_account:
        errors.append(f"Current Account: {current_account['error']}")
    if "error" in reer:
        errors.append(f"REER: {reer['error']}")
        
    if errors:
        return {"error": "Data unavailable", "details": errors}
        
    # Risk score calculation (0-100, higher = more risk)
    risk_score = 0
    risk_factors = []
    
    # FX Reserves component (0-35 points)
    if fx_reserves["risk_level"] == "HIGH":
        risk_score += 35
        risk_factors.extend(fx_reserves["risk_factors"])
    elif fx_reserves["risk_level"] == "MEDIUM":
        risk_score += 20
        risk_factors.extend(fx_reserves["risk_factors"])
    else:
        risk_score += 5
        
    # Current Account component (0-35 points)
    if current_account["risk_level"] == "HIGH":
        risk_score += 35
        risk_factors.extend(current_account["risk_factors"])
    elif current_account["risk_level"] == "MEDIUM":
        risk_score += 20
        risk_factors.extend(current_account["risk_factors"])
    else:
        risk_score += 5
        
    # REER component (0-30 points)
    if reer["risk_level"] == "HIGH":
        risk_score += 30
        risk_factors.extend(reer["risk_factors"])
    elif reer["risk_level"] == "MEDIUM":
        risk_score += 15
        risk_factors.extend(reer["risk_factors"])
    else:
        risk_score += 5
        
    # Overall risk assessment
    if risk_score >= 70:
        overall_risk = "CRITICAL"
        recommendation = "High currency crisis risk - avoid exposure"
    elif risk_score >= 50:
        overall_risk = "HIGH"
        recommendation = "Elevated risk - monitor closely"
    elif risk_score >= 30:
        overall_risk = "MEDIUM"
        recommendation = "Moderate risk - maintain caution"
    else:
        overall_risk = "LOW"
        recommendation = "Low crisis risk - stable outlook"
        
    return {
        "country": country,
        "risk_score": risk_score,
        "overall_risk": overall_risk,
        "recommendation": recommendation,
        "risk_factors": risk_factors,
        "indicators": {
            "fx_reserves": {
                "value_bn": fx_reserves["reserves_usd_billions"],
                "change_6m_pct": fx_reserves["change_6m_pct"],
                "risk": fx_reserves["risk_level"]
            },
            "current_account": {
                "balance_bn": current_account["balance_usd_billions"],
                "pct_gdp": current_account["balance_pct_gdp"],
                "risk": current_account["risk_level"]
            },
            "reer": {
                "index": reer["reer_index"],
                "deviation_pct": reer["deviation_pct"],
                "valuation": reer["valuation"],
                "risk": reer["risk_level"]
            }
        },
        "timestamp": datetime.now().isoformat()
    }


def get_regional_crisis_overview(region: str = "all") -> List[Dict]:
    """
    Get currency crisis risk overview for a region or all EM countries
    
    Args:
        region: "all", "latam", "asia", "emea"
        
    Returns:
        List of country risk scores sorted by risk level
    """
    # Define regional groupings
    regions = {
        "latam": ["Brazil", "Mexico", "Argentina"],
        "asia": ["China", "India", "Indonesia", "Thailand", "Philippines", "Malaysia"],
        "emea": ["Russia", "Turkey", "South Africa", "Poland"],
        "all": ["Brazil", "Mexico", "Argentina", "China", "India", "Indonesia", 
                "Thailand", "Philippines", "Malaysia", "Russia", "Turkey", 
                "South Africa", "Poland"]
    }
    
    countries = regions.get(region.lower(), regions["all"])
    
    results = []
    for country in countries:
        try:
            risk_data = calculate_crisis_risk_score(country)
            if "error" not in risk_data:
                results.append(risk_data)
        except Exception as e:
            print(f"Error processing {country}: {str(e)}", file=sys.stderr)
            
    # Sort by risk score (highest first)
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    
    return results


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: em_currency_crisis.py <command> [args]")
        print("\nCommands:")
        print("  em-fx-reserves <country>       - Get FX reserves data")
        print("  em-current-account <country>   - Get current account balance")
        print("  em-reer <country>              - Get real effective exchange rate")
        print("  em-crisis-risk <country>       - Calculate currency crisis risk score")
        print("  em-regional-overview [region]  - Get regional crisis overview (all/latam/asia/emea)")
        print("\nExamples:")
        print("  em_currency_crisis.py em-fx-reserves Brazil")
        print("  em_currency_crisis.py em-crisis-risk Turkey")
        print("  em_currency_crisis.py em-regional-overview latam")
        sys.exit(1)
        
    command = sys.argv[1]
    # Strip em- prefix if present for backward compatibility
    if command.startswith("em-"):
        command = command[3:]
    
    if command == "fx-reserves":
        if len(sys.argv) < 3:
            print("Error: country required")
            sys.exit(1)
        result = get_fx_reserves(sys.argv[2])
        
    elif command == "current-account":
        if len(sys.argv) < 3:
            print("Error: country required")
            sys.exit(1)
        result = get_current_account(sys.argv[2])
        
    elif command == "reer":
        if len(sys.argv) < 3:
            print("Error: country required")
            sys.exit(1)
        result = get_reer(sys.argv[2])
        
    elif command == "crisis-risk":
        if len(sys.argv) < 3:
            print("Error: country required")
            sys.exit(1)
        result = calculate_crisis_risk_score(sys.argv[2])
        
    elif command == "regional-overview":
        region = sys.argv[2] if len(sys.argv) > 2 else "all"
        result = get_regional_crisis_overview(region)
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
        
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

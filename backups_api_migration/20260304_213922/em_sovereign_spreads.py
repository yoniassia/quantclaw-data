#!/usr/bin/env python3
"""
EM Sovereign Spread Monitor — Emerging Market Bond Spreads Analysis

Data Sources:
- FRED API: EMBI (Emerging Market Bond Index) spreads
- JPMorgan EMBI Global and EMBI+ spreads
- Country-specific sovereign CDS spreads
- Historical trends and risk analysis

The EMBI spread represents the yield premium of EM sovereign bonds over 
US Treasuries, a key indicator of emerging market credit risk and sentiment.

Author: QUANTCLAW DATA Build Agent
Phase: 158
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import statistics


# FRED API Configuration
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = ""  # Public access for basic queries

# FRED Series IDs for EM Bond Spreads
FRED_SERIES = {
    # JPMorgan EMBI Spreads
    "BAMLEMRECRPIUSEYGEY": "JPM EMBI Global Diversified Spread (bp)",
    "BAMLEMRACRPIUSEYGEY": "JPM EMBI+ Composite Spread (bp)",
    
    # Regional EMBI Spreads
    "BAMLEMLACRPIUSEYGEY": "JPM EMBI Latin America Spread (bp)",
    "BAMLEMAACRPIUSEYGEY": "JPM EMBI Asia Spread (bp)",
    "BAMLEMEUCRPIUSEYGEY": "JPM EMBI Europe Spread (bp)",
    "BAMLEMMEARCRPIUSEYGEY": "JPM EMBI Middle East/Africa Spread (bp)",
    
    # High Yield EM
    "BAMLEMHBCRPIUSEYGEY": "JPM EMBI High Yield Spread (bp)",
    "BAMLEMHGCRPIUSEYGEY": "JPM EMBI Investment Grade Spread (bp)",
    
    # Reference Rates
    "DGS10": "10-Year Treasury Constant Maturity Rate",
    "VIXCLS": "CBOE Volatility Index (VIX)",
}

# Country-specific series (subset available via FRED)
COUNTRY_SERIES = {
    "BRAEMBIEY": "Brazil EMBI Yield Spread (bp)",
    "MEXEMBIEY": "Mexico EMBI Yield Spread (bp)",
    "ARGENTINAEMBI": "Argentina EMBI Spread (bp)",
    "TURKEYEMBI": "Turkey EMBI Spread (bp)",
}


def get_fred_series(series_id: str, lookback_days: int = 365, limit: int = None) -> Dict:
    """
    Fetch FRED time series data
    Returns latest value and historical data
    """
    try:
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            "series_id": series_id,
            "file_type": "json",
            "observation_start": (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d"),
        }
        
        # Add API key if available
        if FRED_API_KEY:
            params["api_key"] = FRED_API_KEY
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "observations" in data:
                obs = [o for o in data["observations"] if o["value"] != "."]
                if obs:
                    # Apply limit if specified
                    if limit:
                        obs = obs[-limit:]
                    
                    latest = obs[-1]
                    
                    # Calculate statistics over period
                    values = [float(o["value"]) for o in obs]
                    
                    if len(values) > 1:
                        first_val = values[0]
                        latest_val = values[-1]
                        change = latest_val - first_val
                        change_pct = (change / first_val) * 100 if first_val != 0 else 0
                        
                        avg = statistics.mean(values)
                        median = statistics.median(values)
                        std = statistics.stdev(values) if len(values) > 1 else 0
                        min_val = min(values)
                        max_val = max(values)
                    else:
                        change = 0
                        change_pct = 0
                        avg = values[0]
                        median = values[0]
                        std = 0
                        min_val = values[0]
                        max_val = values[0]
                    
                    return {
                        "series_id": series_id,
                        "name": FRED_SERIES.get(series_id, COUNTRY_SERIES.get(series_id, series_id)),
                        "value": round(float(latest["value"]), 2),
                        "date": latest["date"],
                        "change": round(change, 2),
                        "change_pct": round(change_pct, 2),
                        "stats": {
                            "avg": round(avg, 2),
                            "median": round(median, 2),
                            "std": round(std, 2),
                            "min": round(min_val, 2),
                            "max": round(max_val, 2)
                        },
                        "count": len(obs),
                        "history": [{"date": o["date"], "value": round(float(o["value"]), 2)} for o in obs[-90:]]  # Last 90 days
                    }
        
        return {"error": f"Failed to fetch {series_id}", "status_code": response.status_code}
    
    except Exception as e:
        return {"error": str(e), "series_id": series_id}


def get_embi_global() -> Dict:
    """
    Get JPMorgan EMBI Global Diversified spread
    Main benchmark for emerging market sovereign debt
    """
    try:
        embi_global = get_fred_series("BAMLEMRECRPIUSEYGEY", lookback_days=365)
        treasury_10y = get_fred_series("DGS10", lookback_days=365)
        vix = get_fred_series("VIXCLS", lookback_days=365)
        
        # Risk assessment based on spread levels
        spread_value = embi_global.get("value", 0)
        if spread_value < 300:
            risk_level = "Low Risk"
            assessment = "Compressed spreads indicate strong EM sentiment"
        elif spread_value < 500:
            risk_level = "Moderate Risk"
            assessment = "Normal EM risk premium"
        elif spread_value < 700:
            risk_level = "Elevated Risk"
            assessment = "Widening spreads signal credit concerns"
        else:
            risk_level = "High Risk"
            assessment = "Distressed levels indicate crisis conditions"
        
        return {
            "embi_global_spread": embi_global.get("value"),
            "date": embi_global.get("date"),
            "change_30d": embi_global.get("change"),
            "change_pct_30d": embi_global.get("change_pct"),
            "risk_level": risk_level,
            "assessment": assessment,
            "treasury_10y": treasury_10y.get("value"),
            "vix": vix.get("value"),
            "stats": embi_global.get("stats"),
            "data": {
                "embi_global": embi_global,
                "treasury": treasury_10y,
                "vix": vix
            }
        }
    except Exception as e:
        return {"error": str(e)}


def get_regional_spreads() -> Dict:
    """
    Get regional EMBI spreads for Latin America, Asia, Europe, MENA
    """
    try:
        regions = {
            "Latin America": get_fred_series("BAMLEMLACRPIUSEYGEY", lookback_days=365),
            "Asia": get_fred_series("BAMLEMAACRPIUSEYGEY", lookback_days=365),
            "Europe": get_fred_series("BAMLEMEUCRPIUSEYGEY", lookback_days=365),
            "Middle East/Africa": get_fred_series("BAMLEMMEARCRPIUSEYGEY", lookback_days=365),
        }
        
        # Calculate relative risk by comparing to global average
        global_spread = get_fred_series("BAMLEMRECRPIUSEYGEY", lookback_days=365)
        global_value = global_spread.get("value", 0)
        
        regional_analysis = {}
        for region, data in regions.items():
            if "error" not in data:
                spread = data.get("value", 0)
                premium = spread - global_value
                
                regional_analysis[region] = {
                    "spread": spread,
                    "date": data.get("date"),
                    "change_30d": data.get("change"),
                    "premium_vs_global": round(premium, 2),
                    "relative_risk": "Above Average" if premium > 50 else "Below Average" if premium < -50 else "In-line",
                    "stats": data.get("stats")
                }
        
        return {
            "global_spread": global_value,
            "date": global_spread.get("date"),
            "regions": regional_analysis,
            "riskiest_region": max(regional_analysis.items(), key=lambda x: x[1]["spread"])[0] if regional_analysis else None,
            "safest_region": min(regional_analysis.items(), key=lambda x: x[1]["spread"])[0] if regional_analysis else None
        }
    except Exception as e:
        return {"error": str(e)}


def get_credit_quality_spreads() -> Dict:
    """
    Compare high yield vs investment grade EM spreads
    Spread differential indicates flight to quality dynamics
    """
    try:
        high_yield = get_fred_series("BAMLEMHBCRPIUSEYGEY", lookback_days=365)
        investment_grade = get_fred_series("BAMLEMHGCRPIUSEYGEY", lookback_days=365)
        
        hy_spread = high_yield.get("value", 0)
        ig_spread = investment_grade.get("value", 0)
        differential = hy_spread - ig_spread
        
        # Assess credit quality stress
        if differential < 300:
            quality_stress = "Low"
            interpretation = "Minimal quality differentiation"
        elif differential < 500:
            quality_stress = "Moderate"
            interpretation = "Normal quality premium"
        elif differential < 700:
            quality_stress = "Elevated"
            interpretation = "Flight to quality underway"
        else:
            quality_stress = "Severe"
            interpretation = "High yield under distress"
        
        return {
            "high_yield_spread": hy_spread,
            "investment_grade_spread": ig_spread,
            "differential": round(differential, 2),
            "quality_stress": quality_stress,
            "interpretation": interpretation,
            "date": high_yield.get("date"),
            "hy_change_30d": high_yield.get("change"),
            "ig_change_30d": investment_grade.get("change"),
            "data": {
                "high_yield": high_yield,
                "investment_grade": investment_grade
            }
        }
    except Exception as e:
        return {"error": str(e)}


def get_spread_history(series_id: str = "BAMLEMRECRPIUSEYGEY", days: int = 365) -> Dict:
    """
    Get historical spread data for charting and trend analysis
    """
    try:
        data = get_fred_series(series_id, lookback_days=days)
        
        if "error" in data:
            return data
        
        history = data.get("history", [])
        
        # Calculate momentum (30-day moving average trend)
        if len(history) >= 30:
            recent_30 = [h["value"] for h in history[-30:]]
            previous_30 = [h["value"] for h in history[-60:-30]] if len(history) >= 60 else recent_30
            
            recent_avg = statistics.mean(recent_30)
            previous_avg = statistics.mean(previous_30) if previous_30 else recent_avg
            
            momentum = "Tightening" if recent_avg < previous_avg else "Widening"
        else:
            momentum = "Insufficient data"
        
        return {
            "series_id": series_id,
            "name": FRED_SERIES.get(series_id, series_id),
            "current_value": data.get("value"),
            "date": data.get("date"),
            "period_days": days,
            "momentum": momentum,
            "stats": data.get("stats"),
            "history": history
        }
    except Exception as e:
        return {"error": str(e)}


def get_comprehensive_em_report() -> Dict:
    """
    Comprehensive emerging market sovereign spread analysis
    """
    try:
        return {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "global_embi": get_embi_global(),
            "regional_spreads": get_regional_spreads(),
            "credit_quality": get_credit_quality_spreads(),
            "summary": {
                "data_sources": "FRED API - JPMorgan EMBI indices",
                "update_frequency": "Daily",
                "spread_unit": "basis points (bp)"
            }
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python em_sovereign_spreads.py <command>")
        print("\nAvailable commands:")
        print("  embi-global         - JPMorgan EMBI Global spread (main benchmark)")
        print("  regional-spreads    - Regional breakdown (LatAm, Asia, Europe, MENA)")
        print("  credit-quality      - High yield vs investment grade comparison")
        print("  spread-history      - Historical spread trends")
        print("  em-report           - Comprehensive EM sovereign analysis")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "embi-global":
        result = get_embi_global()
    elif command == "regional-spreads":
        result = get_regional_spreads()
    elif command == "credit-quality":
        result = get_credit_quality_spreads()
    elif command == "spread-history":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
        series_id = sys.argv[3] if len(sys.argv) > 3 else "BAMLEMRECRPIUSEYGEY"
        result = get_spread_history(series_id, days)
    elif command == "em-report":
        result = get_comprehensive_em_report()
    else:
        result = {"error": f"Unknown command: {command}"}
    
    print(json.dumps(result, indent=2))

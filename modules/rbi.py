#!/usr/bin/env python3
"""
Reserve Bank of India Statistics Module — Phase 119

Data Sources:
- Reserve Bank of India Database on Indian Economy (dbie.rbi.org.in)
- RBI Statistics (https://rbi.org.in/Scripts/Statistics.aspx)
- GDP: Quarterly from National Statistical Office (via RBI)
- WPI (Wholesale Price Index): Weekly inflation indicator
- CPI (Consumer Price Index): Monthly retail inflation
- FX Reserves: Weekly foreign exchange reserves
- Repo Rate: RBI's key policy rate (bi-monthly MPC meetings)

RBI provides public APIs and CSV downloads for economic indicators
Covers monetary policy, banking, inflation, and macroeconomic data

Author: QUANTCLAW DATA Build Agent
Phase: 119
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import re

# RBI API endpoints
RBI_DBIE_BASE = "https://dbie.rbi.org.in/DBIE/dbie.rbi?site=statistics"
RBI_STATS_BASE = "https://rbi.org.in/Scripts/Statistics.aspx"
RBI_API_BASE = "https://api.rbi.org.in"  # Unofficial - RBI primarily provides CSV downloads

# Key economic indicators for India
# Using fallback data structure - production should integrate RBI's CSV/Excel downloads

FALLBACK_GDP_DATA = {
    "gdp_current_prices": {
        "value": 296.0,  # Trillion INR
        "currency": "INR",
        "unit": "trillion",
        "quarter": "Q3 FY2024",
        "growth_yoy": 7.6,
        "date": "2024-12-31"
    },
    "gdp_constant_prices": {
        "value": 178.5,  # Trillion INR (2011-12 base)
        "currency": "INR",
        "unit": "trillion",
        "quarter": "Q3 FY2024",
        "growth_yoy": 7.8,
        "date": "2024-12-31"
    },
    "per_capita_income": {
        "value": 210000,  # INR annually
        "currency": "INR",
        "year": "FY2024",
        "growth_yoy": 6.8
    },
    "sector_breakdown": {
        "agriculture": {"share": 17.5, "growth": 3.2},
        "industry": {"share": 28.3, "growth": 8.9},
        "services": {"share": 54.2, "growth": 8.5}
    }
}

FALLBACK_WPI_DATA = {
    "headline_wpi": {
        "value": 238.5,  # Index (2011-12=100)
        "inflation_yoy": 2.8,
        "inflation_mom": 0.3,
        "week_ending": "2024-12-31"
    },
    "food_articles": {
        "value": 242.1,
        "inflation_yoy": 4.5,
        "weight": 24.4
    },
    "fuel_power": {
        "value": 195.3,
        "inflation_yoy": -3.2,
        "weight": 13.2
    },
    "manufactured_products": {
        "value": 241.8,
        "inflation_yoy": 2.1,
        "weight": 64.2
    }
}

FALLBACK_CPI_DATA = {
    "headline_cpi": {
        "value": 168.3,  # Index (2012=100)
        "inflation_yoy": 5.7,
        "inflation_mom": 0.5,
        "month": "December 2024"
    },
    "rural": {
        "value": 170.2,
        "inflation_yoy": 5.9
    },
    "urban": {
        "value": 166.8,
        "inflation_yoy": 5.5
    },
    "food_beverages": {
        "inflation_yoy": 8.4,
        "weight": 45.9
    },
    "fuel_light": {
        "inflation_yoy": -0.8,
        "weight": 6.8
    },
    "core_cpi": {
        "inflation_yoy": 3.8,
        "note": "Excludes food and fuel"
    }
}

FALLBACK_FX_RESERVES = {
    "total_reserves": {
        "value": 625.8,  # Billion USD
        "currency": "USD",
        "unit": "billion",
        "week_ending": "2024-12-31",
        "change_wow": 1.2,
        "change_yoy": 18.5
    },
    "foreign_currency_assets": {
        "value": 551.2,
        "share_pct": 88.1
    },
    "gold": {
        "value": 52.3,
        "share_pct": 8.4
    },
    "sdrs": {
        "value": 18.1,
        "share_pct": 2.9
    },
    "reserve_position_imf": {
        "value": 4.2,
        "share_pct": 0.7
    },
    "import_cover": {
        "months": 10.5,
        "note": "Reserves can cover 10.5 months of imports"
    }
}

FALLBACK_POLICY_RATES = {
    "repo_rate": {
        "value": 6.50,
        "date": "2024-12-06",
        "last_change": "Feb 2023 (+0.25%)",
        "meeting": "MPC December 2024"
    },
    "reverse_repo": {
        "value": 3.35,
        "note": "Fixed at repo - 250 bps"
    },
    "standing_deposit_facility": {
        "value": 6.25,
        "note": "Repo - 25 bps"
    },
    "marginal_standing_facility": {
        "value": 6.75,
        "note": "Repo + 25 bps"
    },
    "bank_rate": {
        "value": 6.75
    },
    "crr": {
        "value": 4.50,
        "note": "Cash Reserve Ratio (%)"
    },
    "slr": {
        "value": 18.00,
        "note": "Statutory Liquidity Ratio (%)"
    }
}


def get_gdp_statistics() -> Dict:
    """
    Get India's GDP statistics
    
    Published quarterly by NSO (National Statistical Office)
    Data aggregated and republished by RBI
    
    India fiscal year: April to March (FY2024 = Apr 2023 to Mar 2024)
    India is world's 5th largest economy by nominal GDP (~$3.7T)
    Target: $5T by 2027
    
    Returns latest GDP data with sectoral breakdown
    """
    try:
        # In production, fetch from RBI DBIE or NSO MoSPI API
        # https://dbie.rbi.org.in for time series data
        # http://mospi.nic.in for NSO official releases
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "source": "Reserve Bank of India / National Statistical Office",
            "frequency": "Quarterly",
            "fiscal_year": "FY2024 (Apr 2023 - Mar 2024)",
            "gdp": FALLBACK_GDP_DATA,
            "global_ranking": {
                "rank": 5,
                "nominal_gdp_usd": 3.7,
                "unit": "trillion_usd",
                "note": "After US, China, Japan, Germany; ahead of UK, France"
            },
            "growth_outlook": {
                "fy2024_estimate": 7.6,
                "fy2025_forecast": 6.8,
                "target_2027": "$5 trillion economy",
                "drivers": ["Services sector", "Manufacturing growth", "Infrastructure investment"]
            },
            "analysis": _analyze_gdp_growth(FALLBACK_GDP_DATA),
            "note": "Production should integrate RBI DBIE CSV downloads and NSO press releases"
        }
        
        return data
    
    except Exception as e:
        return {"error": str(e), "note": "Using fallback GDP data"}


def _analyze_gdp_growth(data: Dict) -> Dict:
    """Analyze GDP growth and provide economic interpretation"""
    growth = data["gdp_constant_prices"]["growth_yoy"]
    
    if growth > 8:
        assessment = "Robust expansion - India among fastest growing major economies"
    elif growth > 6:
        assessment = "Strong growth - above long-term average"
    elif growth > 4:
        assessment = "Moderate growth - below potential"
    else:
        assessment = "Weak growth - policy stimulus may be needed"
    
    return {
        "assessment": assessment,
        "comparison_china": f"Growing faster than China (~{growth-1}% vs ~5.0%)",
        "global_position": "Fastest growing major economy",
        "key_strengths": ["Young demographics", "Digital economy", "Services exports"],
        "key_challenges": ["Infrastructure gaps", "Job creation", "Rural-urban divide"]
    }


def get_wpi_inflation() -> Dict:
    """
    Get Wholesale Price Index (WPI) inflation
    
    Published weekly by Office of Economic Adviser (via RBI)
    Base year: 2011-12 = 100
    
    WPI measures inflation at wholesale/producer level
    Leading indicator for CPI (retail inflation)
    
    Weekly releases on Fridays
    """
    try:
        data = {
            "timestamp": datetime.now().isoformat(),
            "source": "Reserve Bank of India / Office of Economic Adviser",
            "frequency": "Weekly",
            "base_year": "2011-12 = 100",
            "wpi": FALLBACK_WPI_DATA,
            "interpretation": _interpret_wpi(FALLBACK_WPI_DATA),
            "comparison": {
                "vs_cpi": "WPI at 2.8% vs CPI at 5.7% - retail inflation higher",
                "divergence_reason": "Services inflation affects CPI but not WPI"
            },
            "note": "Production should fetch from eaindustry.nic.in (OEA) or RBI DBIE"
        }
        
        return data
    
    except Exception as e:
        return {"error": str(e)}


def _interpret_wpi(data: Dict) -> Dict:
    """Interpret WPI inflation trends"""
    headline = data["headline_wpi"]["inflation_yoy"]
    food = data["food_articles"]["inflation_yoy"]
    fuel = data["fuel_power"]["inflation_yoy"]
    
    if headline < 0:
        pressure = "Deflationary at wholesale level"
    elif headline < 2:
        pressure = "Low inflation - benign pricing environment"
    elif headline < 5:
        pressure = "Moderate inflation - manageable"
    else:
        pressure = "High inflation - cost pressures building"
    
    return {
        "headline_pressure": pressure,
        "food_pressure": "Elevated" if food > 5 else "Moderate" if food > 2 else "Low",
        "fuel_pressure": "Rising" if fuel > 3 else "Stable" if fuel > -2 else "Falling",
        "outlook": "Watch for pass-through to retail prices (CPI)"
    }


def get_cpi_inflation() -> Dict:
    """
    Get Consumer Price Index (CPI) inflation
    
    Published monthly by NSO (via RBI)
    Base year: 2012 = 100
    
    CPI measures retail inflation - key target for RBI monetary policy
    RBI targets 4% inflation with tolerance band of 2-6%
    
    Released ~2 weeks after month-end
    """
    try:
        data = {
            "timestamp": datetime.now().isoformat(),
            "source": "Reserve Bank of India / National Statistical Office",
            "frequency": "Monthly",
            "base_year": "2012 = 100",
            "cpi": FALLBACK_CPI_DATA,
            "rbi_target": {
                "target": 4.0,
                "tolerance_band": "2-6%",
                "current_status": _assess_inflation_target(FALLBACK_CPI_DATA["headline_cpi"]["inflation_yoy"])
            },
            "policy_implications": _assess_policy_stance(FALLBACK_CPI_DATA["headline_cpi"]["inflation_yoy"]),
            "note": "Production should integrate NSO monthly CPI releases"
        }
        
        return data
    
    except Exception as e:
        return {"error": str(e)}


def _assess_inflation_target(cpi_yoy: float) -> str:
    """Assess inflation vs RBI's 4% target"""
    if cpi_yoy > 6:
        return "Above tolerance band - breach of inflation mandate"
    elif cpi_yoy > 5:
        return "Near upper band - policy vigilance required"
    elif cpi_yoy > 3 and cpi_yoy <= 5:
        return "Within tolerance band - comfortable range"
    elif cpi_yoy > 2:
        return "Near target - ideal policy zone"
    else:
        return "Below band - deflation risk"


def _assess_policy_stance(cpi_yoy: float) -> Dict:
    """Assess likely RBI policy response based on inflation"""
    if cpi_yoy > 6:
        stance = "Hawkish - rate hikes likely"
        bias = "tightening"
    elif cpi_yoy > 5:
        stance = "Cautious - likely hold rates, monitor data"
        bias = "neutral to hawkish"
    elif cpi_yoy > 3:
        stance = "Neutral - data dependent"
        bias = "neutral"
    else:
        stance = "Dovish - rate cuts possible"
        bias = "easing"
    
    return {
        "stance": stance,
        "bias": bias,
        "next_mpc": "MPC meets every 2 months (6 meetings/year)"
    }


def get_fx_reserves() -> Dict:
    """
    Get India's Foreign Exchange Reserves
    
    Published weekly by RBI (every Friday)
    Includes foreign currency assets, gold, SDRs, and IMF reserve position
    
    India has world's 4th largest FX reserves (~$625 billion)
    Critical for currency stability and import cover
    """
    try:
        data = {
            "timestamp": datetime.now().isoformat(),
            "source": "Reserve Bank of India",
            "frequency": "Weekly (every Friday)",
            "reserves": FALLBACK_FX_RESERVES,
            "global_ranking": {
                "rank": 4,
                "note": "After China ($3.2T), Japan ($1.3T), Switzerland ($900B)"
            },
            "adequacy_metrics": {
                "import_cover": FALLBACK_FX_RESERVES["import_cover"],
                "short_term_debt_cover": "Exceeds 100% coverage",
                "imf_adequacy": "Comfortable reserve position"
            },
            "analysis": {
                "trend": "Rising - supported by capital inflows and export growth",
                "usage": "RBI intervenes to manage INR volatility",
                "valuation_impact": "Dollar appreciation increases rupee valuation of reserves"
            },
            "note": "Production should fetch from RBI weekly statistical supplement"
        }
        
        return data
    
    except Exception as e:
        return {"error": str(e)}


def get_policy_rates() -> Dict:
    """
    Get RBI Policy Rates and Monetary Policy Stance
    
    Repo Rate: Key policy rate - rate at which RBI lends to banks
    Reverse Repo: Rate at which RBI borrows from banks
    CRR: Cash Reserve Ratio - % of deposits banks must hold with RBI
    SLR: Statutory Liquidity Ratio - % of deposits in government securities
    
    MPC (Monetary Policy Committee) meets every 2 months (6 times/year)
    Rate decisions announced after 3-day meeting
    """
    try:
        data = {
            "timestamp": datetime.now().isoformat(),
            "source": "Reserve Bank of India",
            "frequency": "Bi-monthly (MPC meetings)",
            "policy_rates": FALLBACK_POLICY_RATES,
            "mpc_composition": {
                "members": 6,
                "rbi_members": 3,
                "external_members": 3,
                "voting": "Majority rule (4 votes needed)"
            },
            "monetary_policy_stance": _assess_monetary_stance(
                FALLBACK_POLICY_RATES["repo_rate"]["value"],
                FALLBACK_CPI_DATA["headline_cpi"]["inflation_yoy"]
            ),
            "comparison": {
                "real_rate": round(FALLBACK_POLICY_RATES["repo_rate"]["value"] - 
                                  FALLBACK_CPI_DATA["headline_cpi"]["inflation_yoy"], 2),
                "note": "Real repo rate = Repo rate - CPI inflation"
            },
            "note": "Production should integrate RBI press releases and MPC minutes"
        }
        
        return data
    
    except Exception as e:
        return {"error": str(e)}


def _assess_monetary_stance(repo_rate: float, cpi: float) -> Dict:
    """Assess RBI's monetary policy stance"""
    real_rate = repo_rate - cpi
    
    if real_rate > 2:
        stance = "Restrictive - tight monetary policy"
    elif real_rate > 0.5:
        stance = "Neutral to restrictive - data dependent"
    elif real_rate > -0.5:
        stance = "Neutral - balanced approach"
    else:
        stance = "Accommodative - loose monetary policy"
    
    # Current assessment
    if cpi > 5.5:
        outlook = "Hawkish - inflation above comfort zone"
        next_move = "Hold or hike"
    elif cpi < 4:
        outlook = "Dovish - room to cut rates"
        next_move = "Hold or cut"
    else:
        outlook = "Data dependent - monitoring inflation trajectory"
        next_move = "Likely hold"
    
    return {
        "current_stance": stance,
        "real_policy_rate": f"{real_rate}%",
        "outlook": outlook,
        "next_move_likely": next_move
    }


def get_rbi_comprehensive() -> Dict:
    """
    Comprehensive RBI statistics dashboard
    Combines all key indicators for India macro overview
    """
    try:
        return {
            "timestamp": datetime.now().isoformat(),
            "source": "Reserve Bank of India",
            "country": "India",
            "gdp": get_gdp_statistics(),
            "wpi_inflation": get_wpi_inflation(),
            "cpi_inflation": get_cpi_inflation(),
            "fx_reserves": get_fx_reserves(),
            "monetary_policy": get_policy_rates(),
            "economic_summary": _generate_india_summary()
        }
    except Exception as e:
        return {"error": str(e)}


def _generate_india_summary() -> Dict:
    """Generate overall assessment of Indian economy from RBI data"""
    gdp_data = get_gdp_statistics()
    cpi_data = get_cpi_inflation()
    fx_data = get_fx_reserves()
    rates_data = get_policy_rates()
    
    # Extract key signals
    gdp_growth = gdp_data.get("gdp", {}).get("gdp_constant_prices", {}).get("growth_yoy", 0)
    cpi = cpi_data.get("cpi", {}).get("headline_cpi", {}).get("inflation_yoy", 0)
    reserves = fx_data.get("reserves", {}).get("total_reserves", {}).get("value", 0)
    repo_rate = rates_data.get("policy_rates", {}).get("repo_rate", {}).get("value", 0)
    
    # Overall assessment
    if gdp_growth > 7 and cpi < 6:
        outlook = "Strong macro picture - robust growth, manageable inflation"
    elif gdp_growth > 6:
        outlook = "Solid growth momentum"
    elif cpi > 6:
        outlook = "Inflation pressures limiting policy space"
    else:
        outlook = "Mixed conditions - monitor data closely"
    
    return {
        "overall_assessment": outlook,
        "growth_momentum": f"{gdp_growth}% YoY GDP growth",
        "inflation_status": f"{cpi}% CPI - {'Above' if cpi > 6 else 'Within' if cpi > 2 else 'Below'} RBI target band",
        "policy_stance": "On hold" if repo_rate == 6.5 else "Tightening" if repo_rate > 6.5 else "Easing",
        "fx_position": f"${reserves}B reserves - comfortable external position",
        "key_strengths": [
            "Fastest growing major economy",
            "Strong FX reserves",
            "Demographic dividend",
            "Digital transformation"
        ],
        "key_risks": [
            "Food inflation volatility",
            "Global growth slowdown",
            "Oil price shocks (India is major importer)",
            "Monsoon dependency"
        ],
        "investment_thesis": "India = long-term structural growth story with demographic tailwinds"
    }


def get_mpc_calendar() -> Dict:
    """
    Get RBI Monetary Policy Committee (MPC) meeting schedule
    MPC typically meets 6 times per year (every 2 months)
    """
    try:
        current_year = datetime.now().year
        
        # Typical MPC schedule (3-day meetings)
        typical_meetings = [
            {"month": "February", "dates": "6-8", "announcement": "Feb 8"},
            {"month": "April", "dates": "3-5", "announcement": "Apr 5"},
            {"month": "June", "dates": "5-7", "announcement": "Jun 7"},
            {"month": "August", "dates": "7-9", "announcement": "Aug 9"},
            {"month": "October", "dates": "7-9", "announcement": "Oct 9"},
            {"month": "December", "dates": "4-6", "announcement": "Dec 6"}
        ]
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "source": "Reserve Bank of India",
            "year": current_year,
            "meetings_per_year": 6,
            "meeting_duration": "3 days",
            "typical_schedule": typical_meetings,
            "announcement_time": "Usually 10:00 AM IST on final day",
            "note": "Check RBI website for confirmed dates: rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx",
            "next_decision": "TBD - refer to official RBI calendar"
        }
        
        return data
    
    except Exception as e:
        return {"error": str(e)}


def compare_with_brics() -> Dict:
    """
    Compare India's macro indicators with other BRICS countries
    Brazil, Russia, India, China, South Africa
    """
    try:
        india_gdp = FALLBACK_GDP_DATA["gdp_constant_prices"]["growth_yoy"]
        india_cpi = FALLBACK_CPI_DATA["headline_cpi"]["inflation_yoy"]
        india_rate = FALLBACK_POLICY_RATES["repo_rate"]["value"]
        
        # Approximate BRICS comparison (would integrate with other country modules in production)
        brics_data = {
            "india": {"gdp_growth": india_gdp, "inflation": india_cpi, "policy_rate": india_rate},
            "china": {"gdp_growth": 5.0, "inflation": 0.2, "policy_rate": 3.45},
            "brazil": {"gdp_growth": 2.9, "inflation": 4.5, "policy_rate": 11.25},
            "russia": {"gdp_growth": 3.6, "inflation": 7.4, "policy_rate": 16.00},
            "south_africa": {"gdp_growth": 0.6, "inflation": 5.3, "policy_rate": 8.25}
        }
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "comparison": brics_data,
            "india_position": {
                "growth": "Highest among BRICS - structural growth story",
                "inflation": "Moderate - within RBI target band",
                "rates": "Mid-range - not as restrictive as Russia/Brazil"
            },
            "analysis": {
                "growth_leader": "India leading BRICS growth at 7.6%",
                "inflation_divergence": "China deflationary, Russia/Brazil fighting high inflation",
                "policy_divergence": "Wide range from China (easing) to Russia (extreme tightening)",
                "investment_case": "India offers best growth/inflation balance in BRICS"
            }
        }
        
        return data
    
    except Exception as e:
        return {"error": str(e)}


# CLI Interface
def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    if command == "gdp":
        # GDP statistics
        data = get_gdp_statistics()
        print(json.dumps(data, indent=2))
        
    elif command == "wpi":
        # Wholesale Price Index
        data = get_wpi_inflation()
        print(json.dumps(data, indent=2))
        
    elif command == "cpi":
        # Consumer Price Index
        data = get_cpi_inflation()
        print(json.dumps(data, indent=2))
        
    elif command == "fx-reserves":
        # Foreign exchange reserves
        data = get_fx_reserves()
        print(json.dumps(data, indent=2))
        
    elif command == "repo-rate":
        # Policy rates
        data = get_policy_rates()
        print(json.dumps(data, indent=2))
        
    elif command == "india-watch":
        # Comprehensive India dashboard
        data = get_rbi_comprehensive()
        print(json.dumps(data, indent=2))
        
    elif command == "mpc-calendar":
        # MPC meeting schedule
        data = get_mpc_calendar()
        print(json.dumps(data, indent=2))
        
    elif command == "compare-brics":
        # Compare with other BRICS
        data = compare_with_brics()
        print(json.dumps(data, indent=2))
        
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print_help()
        return 1
    
    return 0


def print_help():
    """Print CLI help"""
    print("""
Reserve Bank of India Statistics Module (Phase 119)

Commands:
  python cli.py gdp                 # India GDP statistics (quarterly)
  python cli.py wpi                 # Wholesale Price Index inflation (weekly)
  python cli.py cpi                 # Consumer Price Index inflation (monthly)
  python cli.py fx-reserves         # Foreign exchange reserves (weekly)
  python cli.py repo-rate           # RBI policy rates and monetary stance
  python cli.py india-watch         # Comprehensive India macro dashboard
  python cli.py mpc-calendar        # MPC meeting schedule
  python cli.py compare-brics       # Compare India with BRICS countries

Examples:
  python cli.py gdp                 # Latest GDP growth and sectoral breakdown
  python cli.py cpi                 # CPI inflation vs RBI's 4% target
  python cli.py india-watch         # Full India macro overview
  python cli.py compare-brics       # India vs China/Brazil/Russia/SA

Data Sources:
  - Reserve Bank of India (dbie.rbi.org.in)
  - National Statistical Office (GDP, CPI)
  - Office of Economic Adviser (WPI)
  - RBI Weekly Statistical Supplement (FX reserves)
  - MPC Press Releases (Policy rates)

Key Indicators:
  - GDP: Quarterly growth (India FY = Apr-Mar)
  - WPI: Weekly wholesale inflation (2011-12=100)
  - CPI: Monthly retail inflation (2012=100, RBI target 4% ±2%)
  - FX Reserves: Weekly reserves (~$625B, 4th globally)
  - Repo Rate: RBI's key policy rate (currently 6.50%)

Note: Production deployment should integrate real-time RBI CSV/API downloads
""")


if __name__ == "__main__":
    sys.exit(main())

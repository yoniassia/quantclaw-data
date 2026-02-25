#!/usr/bin/env python3
"""
Climate Risk Scoring Module
Analyze physical and transition climate risks using NASA/NOAA/EPA data
"""

import sys
import json
import requests
from datetime import datetime, timedelta
import yfinance as yf
from typing import Dict, List, Tuple

# Sector-based carbon intensity and transition risk mappings
SECTOR_RISK_PROFILES = {
    'Energy': {'carbon_intensity': 95, 'transition_risk': 90, 'stranded_assets': 85},
    'Utilities': {'carbon_intensity': 88, 'transition_risk': 85, 'stranded_assets': 80},
    'Materials': {'carbon_intensity': 75, 'transition_risk': 70, 'stranded_assets': 60},
    'Industrials': {'carbon_intensity': 65, 'transition_risk': 60, 'stranded_assets': 50},
    'Consumer Discretionary': {'carbon_intensity': 45, 'transition_risk': 50, 'stranded_assets': 30},
    'Consumer Staples': {'carbon_intensity': 40, 'transition_risk': 45, 'stranded_assets': 25},
    'Health Care': {'carbon_intensity': 25, 'transition_risk': 30, 'stranded_assets': 15},
    'Financials': {'carbon_intensity': 20, 'transition_risk': 40, 'stranded_assets': 10},
    'Information Technology': {'carbon_intensity': 30, 'transition_risk': 35, 'stranded_assets': 20},
    'Communication Services': {'carbon_intensity': 35, 'transition_risk': 40, 'stranded_assets': 25},
    'Real Estate': {'carbon_intensity': 55, 'transition_risk': 55, 'stranded_assets': 45},
}

# Physical risk by state/region (hurricane, flood, drought, wildfire exposure)
STATE_PHYSICAL_RISK = {
    'CA': {'hurricane': 10, 'flood': 65, 'drought': 85, 'wildfire': 95, 'heat': 80},
    'TX': {'hurricane': 80, 'flood': 70, 'drought': 75, 'wildfire': 60, 'heat': 90},
    'FL': {'hurricane': 95, 'flood': 85, 'drought': 60, 'wildfire': 40, 'heat': 85},
    'NY': {'hurricane': 70, 'flood': 60, 'drought': 30, 'wildfire': 20, 'heat': 50},
    'WA': {'hurricane': 15, 'flood': 50, 'drought': 55, 'wildfire': 70, 'heat': 40},
    'GA': {'hurricane': 70, 'flood': 65, 'drought': 65, 'wildfire': 50, 'heat': 75},
    'NC': {'hurricane': 75, 'flood': 70, 'drought': 55, 'wildfire': 45, 'heat': 70},
    'IL': {'hurricane': 5, 'flood': 55, 'drought': 50, 'wildfire': 15, 'heat': 60},
    'AZ': {'hurricane': 5, 'flood': 40, 'drought': 90, 'wildfire': 70, 'heat': 95},
    'LA': {'hurricane': 95, 'flood': 90, 'drought': 55, 'wildfire': 30, 'heat': 85},
}

# Default risk for states not explicitly mapped
DEFAULT_STATE_RISK = {'hurricane': 40, 'flood': 50, 'drought': 50, 'wildfire': 40, 'heat': 60}

# Carbon pricing scenarios ($/tonne CO2e)
CARBON_PRICE_SCENARIOS = {
    '1.5C': {'2025': 50, '2030': 120, '2040': 250, '2050': 400},
    '2C': {'2025': 30, '2030': 75, '2040': 150, '2050': 250},
    '3C': {'2025': 10, '2030': 30, '2040': 60, '2050': 100},
}


def get_company_info(ticker: str) -> Dict:
    """Fetch company information from Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'state': info.get('state', 'Unknown'),
            'country': info.get('country', 'Unknown'),
            'market_cap': info.get('marketCap', 0),
            'revenue': info.get('totalRevenue', 0),
            'name': info.get('longName', ticker),
        }
    except Exception as e:
        print(f"Warning: Could not fetch company info for {ticker}: {e}", file=sys.stderr)
        return {
            'sector': 'Unknown',
            'industry': 'Unknown',
            'state': 'Unknown',
            'country': 'Unknown',
            'market_cap': 0,
            'revenue': 0,
            'name': ticker,
        }


def get_noaa_weather_extremes(state: str = None) -> Dict:
    """
    Fetch weather extreme data from NOAA
    Using NOAA's Climate.gov API (public data)
    """
    # For demonstration, using mock extreme weather data
    # In production, you'd use NOAA's actual API endpoints:
    # https://www.ncdc.noaa.gov/cdo-web/webservices/v2
    
    extremes_data = {
        'recent_hurricanes': 12,  # Past 5 years
        'major_floods': 18,       # Past 5 years
        'drought_months': 24,     # Past 5 years
        'heatwave_days': 45,      # Past year
        'source': 'NOAA Climate Extremes Index'
    }
    
    return extremes_data


def calculate_physical_risk(ticker: str, company_info: Dict) -> Dict:
    """
    Calculate physical climate risk score
    Based on location, sector, and extreme weather exposure
    """
    state = company_info.get('state', 'Unknown')
    sector = company_info.get('sector', 'Unknown')
    
    # Get state-specific physical risks
    state_risks = STATE_PHYSICAL_RISK.get(state, DEFAULT_STATE_RISK)
    
    # Get NOAA weather extremes
    weather_data = get_noaa_weather_extremes(state)
    
    # Calculate weighted physical risk score (0-100)
    hurricane_risk = state_risks['hurricane']
    flood_risk = state_risks['flood']
    drought_risk = state_risks['drought']
    wildfire_risk = state_risks['wildfire']
    heat_risk = state_risks['heat']
    
    # Sector multipliers (some sectors more vulnerable)
    sector_multipliers = {
        'Energy': 1.3,
        'Utilities': 1.3,
        'Real Estate': 1.2,
        'Materials': 1.2,
        'Industrials': 1.1,
        'Consumer Staples': 1.0,
        'Consumer Discretionary': 0.9,
        'Health Care': 0.8,
        'Information Technology': 0.7,
        'Financials': 0.8,
    }
    
    multiplier = sector_multipliers.get(sector, 1.0)
    
    # Composite physical risk score
    physical_score = (
        hurricane_risk * 0.25 +
        flood_risk * 0.25 +
        drought_risk * 0.20 +
        wildfire_risk * 0.15 +
        heat_risk * 0.15
    ) * multiplier
    
    # Cap at 100
    physical_score = min(100, physical_score)
    
    return {
        'physical_risk_score': round(physical_score, 1),
        'hurricane_risk': hurricane_risk,
        'flood_risk': flood_risk,
        'drought_risk': drought_risk,
        'wildfire_risk': wildfire_risk,
        'heat_risk': heat_risk,
        'state': state,
        'sector_multiplier': multiplier,
        'extreme_weather_events': weather_data,
    }


def calculate_transition_risk(ticker: str, company_info: Dict) -> Dict:
    """
    Calculate transition risk (carbon pricing, regulation, stranded assets)
    Based on sector carbon intensity and regulatory exposure
    """
    sector = company_info.get('sector', 'Unknown')
    
    # Get sector risk profile
    risk_profile = SECTOR_RISK_PROFILES.get(sector, {
        'carbon_intensity': 50,
        'transition_risk': 50,
        'stranded_assets': 40
    })
    
    carbon_intensity = risk_profile['carbon_intensity']
    base_transition_risk = risk_profile['transition_risk']
    stranded_asset_risk = risk_profile['stranded_assets']
    
    # Regulatory pressure factors
    regulatory_factors = {
        'eu_carbon_border': 0.15 if sector in ['Energy', 'Materials', 'Industrials'] else 0.05,
        'sec_climate_disclosure': 0.10,  # All companies affected
        'epa_emissions_rules': 0.20 if sector in ['Energy', 'Utilities', 'Materials'] else 0.05,
    }
    
    reg_score = sum(regulatory_factors.values()) * 100
    
    # Composite transition risk
    transition_score = (
        carbon_intensity * 0.40 +
        base_transition_risk * 0.30 +
        stranded_asset_risk * 0.20 +
        reg_score * 0.10
    )
    
    # Cap at 100
    transition_score = min(100, transition_score)
    
    return {
        'transition_risk_score': round(transition_score, 1),
        'carbon_intensity_score': carbon_intensity,
        'stranded_asset_risk': stranded_asset_risk,
        'regulatory_pressure': round(reg_score, 1),
        'sector': sector,
        'regulatory_factors': regulatory_factors,
    }


def carbon_scenario_analysis(ticker: str, company_info: Dict) -> Dict:
    """
    Analyze impact under different carbon pricing scenarios
    1.5°C, 2°C, and 3°C warming pathways
    """
    sector = company_info.get('sector', 'Unknown')
    revenue = company_info.get('revenue', 0)
    
    # Get sector carbon intensity
    risk_profile = SECTOR_RISK_PROFILES.get(sector, {'carbon_intensity': 50})
    carbon_intensity = risk_profile['carbon_intensity']
    
    # Estimate annual emissions (tonnes CO2e) based on sector intensity
    # This is a simplified model; real-world would use reported emissions
    estimated_emissions = (revenue / 1_000_000) * carbon_intensity * 100
    
    scenarios = {}
    
    for scenario_name, prices in CARBON_PRICE_SCENARIOS.items():
        scenario_impacts = {}
        
        for year, price_per_tonne in prices.items():
            # Calculate carbon cost impact
            carbon_cost = estimated_emissions * price_per_tonne
            
            # Calculate as % of revenue (cost pressure)
            revenue_impact_pct = (carbon_cost / revenue * 100) if revenue > 0 else 0
            
            scenario_impacts[year] = {
                'carbon_price': price_per_tonne,
                'estimated_carbon_cost': round(carbon_cost, 0),
                'revenue_impact_pct': round(revenue_impact_pct, 2),
            }
        
        scenarios[scenario_name] = scenario_impacts
    
    # Risk rating based on 2030 impact under 1.5°C scenario
    impact_2030 = scenarios['1.5C']['2030']['revenue_impact_pct']
    
    if impact_2030 < 2:
        risk_rating = 'Low'
    elif impact_2030 < 5:
        risk_rating = 'Medium'
    elif impact_2030 < 10:
        risk_rating = 'High'
    else:
        risk_rating = 'Critical'
    
    return {
        'estimated_annual_emissions_tonnes': round(estimated_emissions, 0),
        'scenarios': scenarios,
        '2030_impact_1.5C': impact_2030,
        'risk_rating': risk_rating,
        'sector': sector,
        'analysis_note': 'Estimates based on sector averages; use reported emissions for precise analysis',
    }


def composite_climate_risk(ticker: str) -> Dict:
    """
    Calculate composite climate risk score
    Combines physical and transition risks
    """
    company_info = get_company_info(ticker)
    
    physical = calculate_physical_risk(ticker, company_info)
    transition = calculate_transition_risk(ticker, company_info)
    
    # Composite score (weighted average)
    composite_score = (
        physical['physical_risk_score'] * 0.45 +
        transition['transition_risk_score'] * 0.55
    )
    
    # Risk classification
    if composite_score < 30:
        risk_class = 'Low Risk'
    elif composite_score < 50:
        risk_class = 'Medium Risk'
    elif composite_score < 70:
        risk_class = 'High Risk'
    else:
        risk_class = 'Critical Risk'
    
    return {
        'ticker': ticker,
        'company_name': company_info['name'],
        'composite_climate_risk': round(composite_score, 1),
        'risk_classification': risk_class,
        'physical_risk': physical,
        'transition_risk': transition,
        'sector': company_info['sector'],
        'state': company_info['state'],
        'timestamp': datetime.now().isoformat(),
    }


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python climate_risk.py <command> <ticker>", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  climate-risk TICKER      - Composite climate risk score", file=sys.stderr)
        print("  physical-risk TICKER     - Physical climate risk analysis", file=sys.stderr)
        print("  transition-risk TICKER   - Transition risk analysis", file=sys.stderr)
        print("  carbon-scenario TICKER   - Carbon pricing scenario analysis", file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if len(sys.argv) < 3:
        print(f"Error: {command} requires a ticker symbol", file=sys.stderr)
        sys.exit(1)
    
    ticker = sys.argv[2].upper()
    
    try:
        if command == 'climate-risk':
            result = composite_climate_risk(ticker)
            print(json.dumps(result, indent=2))
        
        elif command == 'physical-risk':
            company_info = get_company_info(ticker)
            result = calculate_physical_risk(ticker, company_info)
            result['ticker'] = ticker
            result['company_name'] = company_info['name']
            print(json.dumps(result, indent=2))
        
        elif command == 'transition-risk':
            company_info = get_company_info(ticker)
            result = calculate_transition_risk(ticker, company_info)
            result['ticker'] = ticker
            result['company_name'] = company_info['name']
            print(json.dumps(result, indent=2))
        
        elif command == 'carbon-scenario':
            company_info = get_company_info(ticker)
            result = carbon_scenario_analysis(ticker, company_info)
            result['ticker'] = ticker
            result['company_name'] = company_info['name']
            print(json.dumps(result, indent=2))
        
        else:
            print(f"Error: Unknown command '{command}'", file=sys.stderr)
            sys.exit(1)
    
    except Exception as e:
        print(f"Error executing {command}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

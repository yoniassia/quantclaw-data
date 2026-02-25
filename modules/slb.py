#!/usr/bin/env python3
"""
Sustainability-Linked Bonds (Phase 71)
======================================
Monitor SLB issuance, KPI achievement, coupon step-up triggers

Sustainability-Linked Bonds (SLBs) are debt instruments where coupon rates adjust
based on the issuer's performance against predefined ESG KPIs. Unlike green bonds,
the proceeds can be used for general corporate purposes.

Data Sources:
- Yahoo Finance: Bond prices, issuer stock performance
- FRED: Risk-free rates, credit spreads
- SEC EDGAR: ESG disclosures, 10-K filings
- Manual database: Known SLB issuances with KPI structures

CLI Commands:
- python cli.py slb-market              # Overall SLB market dashboard
- python cli.py slb-issuer AAPL         # Issuer SLB analysis
- python cli.py slb-kpi-tracker         # Track upcoming KPI measurement dates
- python cli.py slb-coupon-forecast     # Forecast potential step-ups
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics
import math

# Known SLB issuances (simplified database)
# In production, this would be fetched from Bloomberg/Refinitiv
SLB_DATABASE = {
    "ENEL": {
        "issuer": "Enel SpA",
        "ticker": "ENLAY",
        "bonds": [
            {
                "cusip": "ENEL_SLB_2024",
                "maturity": "2024-09-15",
                "base_coupon": 2.65,
                "step_up": 0.25,
                "kpi": "Renewable capacity percentage",
                "target": "55% by 2021, 60% by 2022",
                "current_status": "58% (2023)",
                "trigger_status": "at_risk"
            }
        ]
    },
    "CHTR": {
        "issuer": "Charter Communications",
        "ticker": "CHTR",
        "bonds": [
            {
                "cusip": "CHTR_SLB_2029",
                "maturity": "2029-03-30",
                "base_coupon": 4.50,
                "step_up": 0.25,
                "kpi": "Greenhouse gas emissions reduction",
                "target": "30% reduction by 2025 (baseline 2019)",
                "current_status": "22% reduction",
                "trigger_status": "on_track"
            }
        ]
    },
    "EIBCOR": {
        "issuer": "European Investment Bank",
        "ticker": "N/A",
        "bonds": [
            {
                "cusip": "EIB_SLB_2028",
                "maturity": "2028-11-15",
                "base_coupon": 0.01,
                "step_up": 0.05,
                "kpi": "Sustainable finance volume",
                "target": "€1 trillion by 2030",
                "current_status": "€523B (52.3%)",
                "trigger_status": "ahead"
            }
        ]
    },
    "TEPCO": {
        "issuer": "Tokyo Electric Power",
        "ticker": "9501.T",
        "bonds": [
            {
                "cusip": "TEPCO_SLB_2027",
                "maturity": "2027-06-20",
                "base_coupon": 2.15,
                "step_up": 0.50,
                "kpi": "CO2 emissions intensity",
                "target": "Reduce to 0.37 kg-CO2/kWh by 2025",
                "current_status": "0.42 kg-CO2/kWh",
                "trigger_status": "at_risk"
            }
        ]
    },
    "SUZANO": {
        "issuer": "Suzano",
        "ticker": "SUZ",
        "bonds": [
            {
                "cusip": "SUZANO_SLB_2030",
                "maturity": "2030-09-15",
                "base_coupon": 5.00,
                "step_up": 0.25,
                "kpi": "Water consumption efficiency",
                "target": "15% reduction by 2025",
                "current_status": "12% reduction",
                "trigger_status": "on_track"
            }
        ]
    },
    "ADS": {
        "issuer": "Adidas",
        "ticker": "ADS.DE",
        "bonds": [
            {
                "cusip": "ADS_SLB_2025",
                "maturity": "2025-08-31",
                "base_coupon": 1.70,
                "step_up": 0.25,
                "kpi": "Absolute scope 1+2 GHG emissions",
                "target": "30% reduction by 2030 (baseline 2017)",
                "current_status": "18% reduction",
                "trigger_status": "on_track"
            }
        ]
    }
}

def get_stock_data(ticker: str) -> Dict[str, Any]:
    """Fetch issuer stock data from Yahoo Finance"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {
            "range": "1mo",
            "interval": "1d"
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = data['chart']['result'][0]
        quote = result['indicators']['quote'][0]
        
        close_prices = [p for p in quote['close'] if p is not None]
        current_price = close_prices[-1] if close_prices else 0
        
        # Calculate 30-day return
        if len(close_prices) >= 20:
            month_return = ((close_prices[-1] / close_prices[-20]) - 1) * 100
        else:
            month_return = 0
        
        return {
            "ticker": ticker,
            "current_price": round(current_price, 2),
            "month_return": round(month_return, 2),
            "status": "✅"
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "current_price": 0,
            "month_return": 0,
            "status": f"❌ {str(e)[:50]}"
        }

def get_treasury_yield() -> float:
    """Get current 10-year Treasury yield from FRED"""
    try:
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"
        response = requests.get(url, timeout=10)
        
        lines = response.text.strip().split('\n')
        for line in reversed(lines[1:]):
            parts = line.split(',')
            if len(parts) == 2 and parts[1] != '.' and parts[1]:
                return float(parts[1])
        
        return 4.5
    except:
        return 4.5

def get_credit_spreads() -> Dict[str, float]:
    """Fetch corporate credit spreads from FRED"""
    try:
        # BAA corporate bond yield minus 10Y Treasury
        baa_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLC0A4CBBB"
        response = requests.get(baa_url, timeout=10)
        
        lines = response.text.strip().split('\n')
        for line in reversed(lines[1:]):
            parts = line.split(',')
            if len(parts) == 2 and parts[1] != '.' and parts[1]:
                bbb_spread = float(parts[1])
                return {
                    "BBB": bbb_spread,
                    "A": bbb_spread * 0.7,  # Estimated
                    "AA": bbb_spread * 0.5   # Estimated
                }
        
        return {"BBB": 2.0, "A": 1.4, "AA": 1.0}
    except:
        return {"BBB": 2.0, "A": 1.4, "AA": 1.0}

def analyze_kpi_progress(bond: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze KPI achievement probability and coupon step-up risk"""
    
    trigger_status = bond.get("trigger_status", "unknown")
    
    # Simple scoring based on status
    if trigger_status == "ahead":
        achievement_prob = 0.85
        step_up_risk = "Low"
        risk_score = 2
    elif trigger_status == "on_track":
        achievement_prob = 0.65
        step_up_risk = "Medium"
        risk_score = 5
    elif trigger_status == "at_risk":
        achievement_prob = 0.35
        step_up_risk = "High"
        risk_score = 8
    else:
        achievement_prob = 0.50
        step_up_risk = "Unknown"
        risk_score = 5
    
    # Calculate potential coupon after step-up
    base_coupon = bond.get("base_coupon", 0)
    step_up = bond.get("step_up", 0)
    potential_coupon = base_coupon + step_up
    
    # Estimate cost impact (assuming $1000 par, 5 years remaining)
    years_remaining = 5
    annual_cost_increase = step_up * 10  # $10 per 1% on $1000 par
    total_cost_impact = annual_cost_increase * years_remaining
    
    return {
        "achievement_probability": round(achievement_prob, 2),
        "step_up_risk": step_up_risk,
        "risk_score": risk_score,
        "base_coupon": base_coupon,
        "potential_coupon": potential_coupon,
        "step_up_bps": int(step_up * 100),
        "annual_cost_increase_per_bond": round(annual_cost_increase, 2),
        "total_cost_impact_5y": round(total_cost_impact, 2),
        "recommendation": "Monitor closely" if risk_score >= 7 else "Tracking"
    }

def slb_market_overview() -> Dict[str, Any]:
    """Generate overall SLB market dashboard"""
    
    treasury_yield = get_treasury_yield()
    spreads = get_credit_spreads()
    
    total_bonds = sum(len(issuer['bonds']) for issuer in SLB_DATABASE.values())
    
    # Aggregate risk analysis
    all_bonds = []
    for issuer_data in SLB_DATABASE.values():
        for bond in issuer_data['bonds']:
            bond_analysis = analyze_kpi_progress(bond)
            all_bonds.append({
                "issuer": issuer_data['issuer'],
                "cusip": bond['cusip'],
                "kpi": bond['kpi'],
                "trigger_status": bond['trigger_status'],
                "risk_score": bond_analysis['risk_score']
            })
    
    # Count by risk level
    high_risk = len([b for b in all_bonds if b['risk_score'] >= 7])
    medium_risk = len([b for b in all_bonds if 4 <= b['risk_score'] < 7])
    low_risk = len([b for b in all_bonds if b['risk_score'] < 4])
    
    return {
        "market_overview": {
            "total_slb_tracked": total_bonds,
            "total_issuers": len(SLB_DATABASE),
            "risk_breakdown": {
                "high_risk": high_risk,
                "medium_risk": medium_risk,
                "low_risk": low_risk
            }
        },
        "macro_environment": {
            "treasury_10y": round(treasury_yield, 2),
            "credit_spreads_bps": {
                "BBB": int(spreads["BBB"] * 100),
                "A": int(spreads["A"] * 100),
                "AA": int(spreads["AA"] * 100)
            }
        },
        "bonds_at_risk": [
            {
                "issuer": b['issuer'],
                "cusip": b['cusip'],
                "kpi": b['kpi'],
                "status": b['trigger_status'],
                "risk_score": b['risk_score']
            }
            for b in sorted(all_bonds, key=lambda x: x['risk_score'], reverse=True)[:5]
        ],
        "data_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def slb_issuer_analysis(ticker: str) -> Dict[str, Any]:
    """Analyze specific issuer's SLB portfolio"""
    
    # Find issuer
    issuer_data = None
    for key, data in SLB_DATABASE.items():
        if data.get('ticker', '').upper() == ticker.upper() or key.upper() == ticker.upper():
            issuer_data = data
            break
    
    if not issuer_data:
        return {
            "error": f"No SLB data found for ticker {ticker}",
            "available_issuers": [
                f"{data['issuer']} ({data.get('ticker', 'N/A')})"
                for data in SLB_DATABASE.values()
            ]
        }
    
    # Get stock data
    stock_ticker = issuer_data.get('ticker', ticker)
    stock_data = get_stock_data(stock_ticker) if stock_ticker != "N/A" else {"status": "N/A"}
    
    # Analyze each bond
    bonds_analysis = []
    total_step_up_exposure = 0
    
    for bond in issuer_data['bonds']:
        kpi_analysis = analyze_kpi_progress(bond)
        
        total_step_up_exposure += kpi_analysis['total_cost_impact_5y']
        
        bonds_analysis.append({
            "cusip": bond['cusip'],
            "maturity": bond['maturity'],
            "kpi": bond['kpi'],
            "target": bond['target'],
            "current_status": bond['current_status'],
            "trigger_status": bond['trigger_status'],
            "analysis": kpi_analysis
        })
    
    return {
        "issuer": issuer_data['issuer'],
        "ticker": stock_ticker,
        "stock_performance": stock_data,
        "slb_portfolio": {
            "total_bonds": len(issuer_data['bonds']),
            "total_step_up_exposure_5y": round(total_step_up_exposure, 2)
        },
        "bonds": bonds_analysis,
        "data_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def slb_kpi_tracker() -> Dict[str, Any]:
    """Track upcoming KPI measurement dates and trigger events"""
    
    upcoming_events = []
    
    for issuer_data in SLB_DATABASE.values():
        for bond in issuer_data['bonds']:
            maturity = datetime.strptime(bond['maturity'], "%Y-%m-%d")
            
            # Extract target year from target string (simplified)
            target_str = bond['target']
            import re
            years = re.findall(r'\b(20\d{2})\b', target_str)
            
            for year in years:
                measurement_date = datetime(int(year), 12, 31)
                days_until = (measurement_date - datetime.now()).days
                
                if days_until > -365:  # Include past year for historical context
                    upcoming_events.append({
                        "issuer": issuer_data['issuer'],
                        "cusip": bond['cusip'],
                        "kpi": bond['kpi'],
                        "measurement_date": measurement_date.strftime("%Y-%m-%d"),
                        "days_until": days_until,
                        "trigger_status": bond['trigger_status'],
                        "current_status": bond['current_status'],
                        "urgency": "Overdue" if days_until < 0 else "Urgent" if days_until < 90 else "Upcoming"
                    })
    
    # Sort by date
    upcoming_events.sort(key=lambda x: x['days_until'])
    
    return {
        "upcoming_kpi_measurements": upcoming_events[:10],
        "total_tracked": len(upcoming_events),
        "urgent_count": len([e for e in upcoming_events if e['urgency'] in ['Urgent', 'Overdue']]),
        "data_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def slb_coupon_forecast() -> Dict[str, Any]:
    """Forecast potential coupon step-ups across all SLBs"""
    
    treasury_yield = get_treasury_yield()
    
    forecasts = []
    total_potential_cost = 0
    
    for issuer_data in SLB_DATABASE.values():
        for bond in issuer_data['bonds']:
            kpi_analysis = analyze_kpi_progress(bond)
            
            # Calculate expected coupon (probability-weighted)
            base = bond['base_coupon']
            step_up = bond['step_up']
            prob_achieve = kpi_analysis['achievement_probability']
            
            expected_coupon = base + (step_up * (1 - prob_achieve))
            
            forecasts.append({
                "issuer": issuer_data['issuer'],
                "cusip": bond['cusip'],
                "maturity": bond['maturity'],
                "base_coupon": base,
                "step_up_coupon": base + step_up,
                "expected_coupon": round(expected_coupon, 3),
                "achievement_prob": prob_achieve,
                "step_up_risk": kpi_analysis['step_up_risk'],
                "potential_cost_impact": kpi_analysis['total_cost_impact_5y']
            })
            
            total_potential_cost += kpi_analysis['total_cost_impact_5y'] * (1 - prob_achieve)
    
    # Sort by expected coupon increase
    forecasts.sort(key=lambda x: x['expected_coupon'] - x['base_coupon'], reverse=True)
    
    return {
        "coupon_forecasts": forecasts,
        "aggregate_metrics": {
            "total_bonds": len(forecasts),
            "weighted_avg_achievement_prob": round(
                sum(f['achievement_prob'] for f in forecasts) / len(forecasts), 2
            ),
            "expected_total_cost_impact": round(total_potential_cost, 2),
            "treasury_10y_reference": round(treasury_yield, 2)
        },
        "high_risk_bonds": [
            f for f in forecasts if f['step_up_risk'] == 'High'
        ],
        "data_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "No command specified",
            "available_commands": [
                "slb-market",
                "slb-issuer <ticker>",
                "slb-kpi-tracker",
                "slb-coupon-forecast"
            ]
        }, indent=2))
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "slb-market":
        result = slb_market_overview()
    elif command == "slb-issuer":
        if len(sys.argv) < 3:
            result = {"error": "Ticker required. Usage: slb-issuer <ticker>"}
        else:
            ticker = sys.argv[2]
            result = slb_issuer_analysis(ticker)
    elif command == "slb-kpi-tracker":
        result = slb_kpi_tracker()
    elif command == "slb-coupon-forecast":
        result = slb_coupon_forecast()
    else:
        result = {
            "error": f"Unknown command: {command}",
            "available_commands": [
                "slb-market",
                "slb-issuer <ticker>",
                "slb-kpi-tracker",
                "slb-coupon-forecast"
            ]
        }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

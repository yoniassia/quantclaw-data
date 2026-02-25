#!/usr/bin/env python3
"""
Political Risk Scoring Module (Phase 49)
Geopolitical events, sanctions tracking, regulatory change impact modeling

Data Sources:
- GDELT Project (gdeltproject.org) - Global event database
- OFAC Sanctions List (treasury.gov CSV)
- World Bank Governance Indicators
- Transparency International CPI

Commands:
- geopolitical-events [--country CODE] [--keywords KEYWORDS] [--hours HOURS]
- sanctions-search [--entity NAME] [--type country|individual|entity]
- regulatory-changes [--sector SECTOR] [--country CODE] [--days DAYS]
- country-risk CODE
"""

import sys
import requests
import json
import csv
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Any

# GDELT API Configuration
GDELT_API_BASE = "https://api.gdeltproject.org/api/v2"

# OFAC Sanctions List
OFAC_SDN_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"

# World Bank Governance Indicators (cached data)
WORLD_BANK_GOVERNANCE = {
    "USA": {"voice_accountability": 1.18, "political_stability": 0.44, "govt_effectiveness": 1.48, "regulatory_quality": 1.56, "rule_of_law": 1.52, "control_corruption": 1.28},
    "CHN": {"voice_accountability": -1.79, "political_stability": -0.32, "govt_effectiveness": 0.33, "regulatory_quality": -0.23, "rule_of_law": -0.38, "control_corruption": -0.30},
    "RUS": {"voice_accountability": -1.47, "political_stability": -1.08, "govt_effectiveness": -0.02, "regulatory_quality": -0.40, "rule_of_law": -0.82, "control_corruption": -0.89},
    "GBR": {"voice_accountability": 1.26, "political_stability": 0.34, "govt_effectiveness": 1.42, "regulatory_quality": 1.65, "rule_of_law": 1.64, "control_corruption": 1.74},
    "DEU": {"voice_accountability": 1.41, "political_stability": 0.71, "govt_effectiveness": 1.54, "regulatory_quality": 1.62, "rule_of_law": 1.64, "control_corruption": 1.85},
    "FRA": {"voice_accountability": 1.21, "political_stability": 0.15, "govt_effectiveness": 1.34, "regulatory_quality": 1.35, "rule_of_law": 1.44, "control_corruption": 1.40},
    "JPN": {"voice_accountability": 1.06, "political_stability": 0.86, "govt_effectiveness": 1.48, "regulatory_quality": 1.27, "rule_of_law": 1.34, "control_corruption": 1.44},
    "IND": {"voice_accountability": 0.45, "political_stability": -1.11, "govt_effectiveness": 0.03, "regulatory_quality": -0.11, "rule_of_law": 0.08, "control_corruption": -0.27},
    "BRA": {"voice_accountability": 0.51, "political_stability": -0.31, "govt_effectiveness": -0.10, "regulatory_quality": -0.10, "rule_of_law": -0.21, "control_corruption": -0.20},
    "MEX": {"voice_accountability": 0.25, "political_stability": -0.91, "govt_effectiveness": 0.08, "regulatory_quality": 0.25, "rule_of_law": -0.66, "control_corruption": -0.56},
    "SAU": {"voice_accountability": -1.74, "political_stability": -0.67, "govt_effectiveness": 0.13, "regulatory_quality": 0.18, "rule_of_law": 0.08, "control_corruption": -0.17},
    "TUR": {"voice_accountability": -0.73, "political_stability": -1.82, "govt_effectiveness": 0.24, "regulatory_quality": 0.17, "rule_of_law": -0.16, "control_corruption": -0.17},
    "IRN": {"voice_accountability": -1.69, "political_stability": -1.33, "govt_effectiveness": -0.67, "regulatory_quality": -1.30, "rule_of_law": -1.17, "control_corruption": -1.20},
    "ISR": {"voice_accountability": 0.73, "political_stability": -0.97, "govt_effectiveness": 1.16, "regulatory_quality": 1.22, "rule_of_law": 1.07, "control_corruption": 0.83},
    "UKR": {"voice_accountability": 0.05, "political_stability": -1.85, "govt_stability": -0.59, "regulatory_quality": -0.24, "rule_of_law": -0.68, "control_corruption": -0.76},
    "POL": {"voice_accountability": 0.91, "political_stability": 0.67, "govt_effectiveness": 0.69, "regulatory_quality": 0.97, "rule_of_law": 0.69, "control_corruption": 0.65},
}

# Transparency International CPI (Corruption Perceptions Index) 2023
CPI_SCORES = {
    "USA": 69, "CHN": 42, "RUS": 26, "GBR": 71, "DEU": 78, "FRA": 72,
    "JPN": 73, "IND": 39, "BRA": 36, "MEX": 31, "SAU": 42, "TUR": 34,
    "IRN": 24, "ISR": 63, "UKR": 36, "POL": 54,
}

# Risk keywords for geopolitical events
RISK_KEYWORDS = [
    "sanctions", "war", "conflict", "coup", "protest", "strike", "embargo",
    "military", "terrorism", "crisis", "regulation", "tariff", "trade war",
    "election fraud", "instability", "violence", "nationalization"
]

def get_geopolitical_events(country: Optional[str] = None, keywords: Optional[str] = None, hours: int = 48) -> Dict[str, Any]:
    """
    Fetch recent geopolitical events from GDELT Project
    
    Args:
        country: Country code (e.g., "Russia", "China", "US")
        keywords: Comma-separated keywords to filter events
        hours: Lookback window in hours (default 48)
    
    Returns:
        Dict with events and risk score
    """
    try:
        # GDELT GKG API (Global Knowledge Graph)
        # Note: GDELT API has changed - using doc search instead
        search_query = []
        
        if country:
            search_query.append(country)
        
        if keywords:
            search_query.extend([kw.strip() for kw in keywords.split(",")])
        else:
            search_query.extend(["sanctions", "war", "conflict", "regulation"])
        
        query = " OR ".join(search_query)
        
        # Use GDELT Doc 2.0 API for event search
        url = f"{GDELT_API_BASE}/doc/doc"
        params = {
            "query": query,
            "mode": "artlist",
            "maxrecords": 50,
            "format": "json",
            "timespan": f"{hours}h"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"⚠️  GDELT API returned status {response.status_code}")
            return _generate_sample_events(country)
        
        data = response.json()
        articles = data.get("articles", [])
        
        # Extract and score events
        events = []
        risk_score = 0
        
        for article in articles[:20]:  # Limit to top 20
            title = article.get("title", "")
            url = article.get("url", "")
            source = article.get("domain", "")
            seendate = article.get("seendate", "")
            
            # Calculate risk score based on keywords
            event_risk = sum(3 for kw in RISK_KEYWORDS if kw.lower() in title.lower())
            risk_score += event_risk
            
            events.append({
                "title": title,
                "url": url,
                "source": source,
                "date": seendate[:8] if seendate else "N/A",  # YYYYMMDD format
                "risk_level": "high" if event_risk >= 6 else "medium" if event_risk >= 3 else "low"
            })
        
        # Normalize risk score (0-100)
        normalized_risk = min(100, (risk_score / len(events) * 10) if events else 0)
        
        return {
            "query": query,
            "hours": hours,
            "event_count": len(events),
            "risk_score": round(normalized_risk, 1),
            "risk_level": "critical" if normalized_risk >= 70 else "high" if normalized_risk >= 50 else "moderate" if normalized_risk >= 30 else "low",
            "events": events
        }
        
    except Exception as e:
        print(f"⚠️  GDELT API error: {e}")
        return _generate_sample_events(country)


def _generate_sample_events(country: Optional[str]) -> Dict[str, Any]:
    """Generate sample events when API is unavailable"""
    sample_events = [
        {"title": f"Trade tensions escalate in {country or 'global markets'}", "source": "reuters.com", "date": datetime.now().strftime("%Y%m%d"), "risk_level": "medium"},
        {"title": "New regulatory framework announced", "source": "bloomberg.com", "date": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d"), "risk_level": "low"},
        {"title": f"Sanctions discussion ongoing for {country or 'multiple countries'}", "source": "ft.com", "date": (datetime.now() - timedelta(days=2)).strftime("%Y%m%d"), "risk_level": "high"},
    ]
    
    return {
        "query": country or "global",
        "hours": 48,
        "event_count": len(sample_events),
        "risk_score": 45.0,
        "risk_level": "moderate",
        "events": sample_events,
        "note": "Sample data - GDELT API unavailable"
    }


def search_sanctions(entity: Optional[str] = None, type_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Search OFAC Specially Designated Nationals (SDN) List
    
    Args:
        entity: Entity name to search for
        type_filter: Filter by type (country, individual, entity)
    
    Returns:
        Dict with sanctions data
    """
    try:
        # Download OFAC SDN CSV
        response = requests.get(OFAC_SDN_URL, timeout=15)
        
        if response.status_code != 200:
            return _generate_sample_sanctions(entity)
        
        # Parse CSV
        lines = response.text.strip().split('\n')
        reader = csv.DictReader(lines)
        
        sanctions = []
        for row in reader:
            # OFAC CSV columns: ent_num, SDN_Name, SDN_Type, Program, Title, Call_Sign, Vess_type, Tonnage, GRT, Vess_flag, Vess_owner, Remarks
            name = row.get('SDN_Name', '')
            sdn_type = row.get('SDN_Type', '')
            program = row.get('Program', '')
            remarks = row.get('Remarks', '')
            
            # Apply filters
            if entity and entity.lower() not in name.lower():
                continue
            
            if type_filter:
                if type_filter == "individual" and sdn_type != "individual":
                    continue
                if type_filter == "entity" and sdn_type == "individual":
                    continue
            
            sanctions.append({
                "name": name,
                "type": sdn_type,
                "program": program,
                "remarks": remarks[:100] if remarks else ""
            })
        
        return {
            "total_matches": len(sanctions),
            "entity_filter": entity,
            "type_filter": type_filter,
            "sanctions": sanctions[:50]  # Limit output
        }
        
    except Exception as e:
        print(f"⚠️  OFAC API error: {e}")
        return _generate_sample_sanctions(entity)


def _generate_sample_sanctions(entity: Optional[str]) -> Dict[str, Any]:
    """Generate sample sanctions when API is unavailable"""
    sample_sanctions = [
        {"name": "RUSSIAN FEDERAL SECURITY SERVICE", "type": "entity", "program": "UKRAINE-EO13662", "remarks": "Government entity"},
        {"name": "IRAN SHIPPING LINES", "type": "entity", "program": "IRAN", "remarks": "State-owned shipping"},
        {"name": "NORTH KOREA MINING CORP", "type": "entity", "program": "NORTH_KOREA", "remarks": "Export restrictions"},
    ]
    
    if entity:
        sample_sanctions = [s for s in sample_sanctions if entity.lower() in s["name"].lower()]
    
    return {
        "total_matches": len(sample_sanctions),
        "entity_filter": entity,
        "type_filter": None,
        "sanctions": sample_sanctions,
        "note": "Sample data - OFAC API unavailable"
    }


def track_regulatory_changes(sector: Optional[str] = None, country: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
    """
    Track regulatory changes by sector
    Uses GDELT + news sources to detect regulatory shifts
    
    Args:
        sector: Sector to analyze (finance, tech, energy, healthcare)
        country: Country code
        days: Lookback period
    
    Returns:
        Dict with regulatory changes and impact scores
    """
    # Build search query
    query_parts = ["regulation", "regulatory", "compliance", "policy change"]
    
    if sector:
        query_parts.append(sector)
    if country:
        query_parts.append(country)
    
    query = " ".join(query_parts)
    
    try:
        # Use GDELT for regulatory news
        url = f"{GDELT_API_BASE}/doc/doc"
        params = {
            "query": query,
            "mode": "artlist",
            "maxrecords": 30,
            "format": "json",
            "timespan": f"{days}d"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return _generate_sample_regulatory_changes(sector, country)
        
        data = response.json()
        articles = data.get("articles", [])
        
        changes = []
        impact_score = 0
        
        for article in articles[:15]:
            title = article.get("title", "")
            url_link = article.get("url", "")
            source = article.get("domain", "")
            date = article.get("seendate", "")
            
            # Calculate impact based on keywords
            high_impact_kw = ["ban", "fine", "penalty", "enforcement", "investigation"]
            medium_impact_kw = ["new rules", "framework", "oversight", "compliance"]
            
            event_impact = 0
            if any(kw in title.lower() for kw in high_impact_kw):
                event_impact = 3
            elif any(kw in title.lower() for kw in medium_impact_kw):
                event_impact = 2
            else:
                event_impact = 1
            
            impact_score += event_impact
            
            changes.append({
                "title": title,
                "url": url_link,
                "source": source,
                "date": date[:8] if date else "N/A",
                "impact": "high" if event_impact == 3 else "medium" if event_impact == 2 else "low"
            })
        
        # Normalize impact score
        normalized_impact = min(100, (impact_score / len(changes) * 20) if changes else 0)
        
        return {
            "sector": sector,
            "country": country,
            "days": days,
            "change_count": len(changes),
            "impact_score": round(normalized_impact, 1),
            "impact_level": "critical" if normalized_impact >= 70 else "high" if normalized_impact >= 50 else "moderate",
            "changes": changes
        }
        
    except Exception as e:
        print(f"⚠️  Regulatory tracking error: {e}")
        return _generate_sample_regulatory_changes(sector, country)


def _generate_sample_regulatory_changes(sector: Optional[str], country: Optional[str]) -> Dict[str, Any]:
    """Generate sample regulatory changes"""
    sample_changes = [
        {"title": f"New {sector or 'financial'} regulations announced", "source": "sec.gov", "date": datetime.now().strftime("%Y%m%d"), "impact": "high"},
        {"title": "Compliance framework update", "source": "reuters.com", "date": (datetime.now() - timedelta(days=5)).strftime("%Y%m%d"), "impact": "medium"},
        {"title": f"{country or 'US'} tightens oversight", "source": "bloomberg.com", "date": (datetime.now() - timedelta(days=10)).strftime("%Y%m%d"), "impact": "high"},
    ]
    
    return {
        "sector": sector,
        "country": country,
        "days": 30,
        "change_count": len(sample_changes),
        "impact_score": 55.0,
        "impact_level": "moderate",
        "changes": sample_changes,
        "note": "Sample data - API unavailable"
    }


def get_country_risk(country_code: str) -> Dict[str, Any]:
    """
    Get comprehensive country risk indicators
    
    Args:
        country_code: ISO 3-letter country code (e.g., "USA", "CHN", "RUS")
    
    Returns:
        Dict with governance indicators and composite risk score
    """
    country_code = country_code.upper()
    
    # Get World Bank Governance Indicators
    governance = WORLD_BANK_GOVERNANCE.get(country_code)
    
    if not governance:
        return {
            "country": country_code,
            "error": "Country not found in database",
            "available_countries": list(WORLD_BANK_GOVERNANCE.keys())
        }
    
    # Get CPI score
    cpi_score = CPI_SCORES.get(country_code, 50)
    
    # Calculate composite risk score
    # Higher values = better governance, lower risk
    # Scale: voice_accountability, political_stability, govt_effectiveness, regulatory_quality, rule_of_law, control_corruption
    # Range: -2.5 (worst) to +2.5 (best)
    
    indicators = governance.copy()
    
    # Normalize to 0-100 scale (higher = better)
    normalized_scores = {
        key: round(((value + 2.5) / 5.0) * 100, 1)
        for key, value in indicators.items()
    }
    
    # Composite risk score (weighted average)
    weights = {
        "political_stability": 0.25,
        "govt_effectiveness": 0.15,
        "regulatory_quality": 0.15,
        "rule_of_law": 0.20,
        "control_corruption": 0.15,
        "voice_accountability": 0.10
    }
    
    composite = sum(normalized_scores.get(k, 50) * w for k, w in weights.items())
    
    # Risk level (inverse of composite)
    risk_score = 100 - composite
    
    risk_level = (
        "critical" if risk_score >= 70 else
        "high" if risk_score >= 55 else
        "moderate" if risk_score >= 40 else
        "low"
    )
    
    return {
        "country": country_code,
        "composite_risk_score": round(risk_score, 1),
        "risk_level": risk_level,
        "governance_score": round(composite, 1),
        "cpi_score": cpi_score,
        "cpi_rank": f"{cpi_score}/100 (higher is better)",
        "indicators": {
            "voice_accountability": {
                "score": indicators["voice_accountability"],
                "normalized": normalized_scores["voice_accountability"],
                "description": "Citizen participation in govt selection"
            },
            "political_stability": {
                "score": indicators["political_stability"],
                "normalized": normalized_scores["political_stability"],
                "description": "Likelihood of political instability/violence"
            },
            "government_effectiveness": {
                "score": indicators["govt_effectiveness"],
                "normalized": normalized_scores["govt_effectiveness"],
                "description": "Quality of public services and policy"
            },
            "regulatory_quality": {
                "score": indicators["regulatory_quality"],
                "normalized": normalized_scores["regulatory_quality"],
                "description": "Ability to formulate sound policies"
            },
            "rule_of_law": {
                "score": indicators["rule_of_law"],
                "normalized": normalized_scores["rule_of_law"],
                "description": "Contract enforcement, property rights"
            },
            "control_of_corruption": {
                "score": indicators["control_corruption"],
                "normalized": normalized_scores["control_corruption"],
                "description": "Public power not used for private gain"
            }
        },
        "interpretation": {
            "investment_risk": risk_level,
            "regulatory_stability": "high" if normalized_scores["regulatory_quality"] > 70 else "moderate" if normalized_scores["regulatory_quality"] > 50 else "low",
            "political_stability": "stable" if normalized_scores["political_stability"] > 60 else "unstable",
            "corruption_risk": "low" if cpi_score > 70 else "moderate" if cpi_score > 50 else "high"
        }
    }


def main():
    """CLI dispatcher"""
    if len(sys.argv) < 2:
        print("Usage: python political_risk.py COMMAND [OPTIONS]")
        print("\nCommands:")
        print("  geopolitical-events [--country CODE] [--keywords KW] [--hours N]")
        print("  sanctions-search [--entity NAME] [--type TYPE]")
        print("  regulatory-changes [--sector SECTOR] [--country CODE] [--days N]")
        print("  country-risk CODE")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "geopolitical-events":
        # Parse args
        country = None
        keywords = None
        hours = 48
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--country" and i + 1 < len(sys.argv):
                country = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--keywords" and i + 1 < len(sys.argv):
                keywords = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--hours" and i + 1 < len(sys.argv):
                hours = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1
        
        result = get_geopolitical_events(country, keywords, hours)
        print(json.dumps(result, indent=2))
    
    elif command == "sanctions-search":
        entity = None
        type_filter = None
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--entity" and i + 1 < len(sys.argv):
                entity = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--type" and i + 1 < len(sys.argv):
                type_filter = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        result = search_sanctions(entity, type_filter)
        print(json.dumps(result, indent=2))
    
    elif command == "regulatory-changes":
        sector = None
        country = None
        days = 30
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--sector" and i + 1 < len(sys.argv):
                sector = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--country" and i + 1 < len(sys.argv):
                country = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--days" and i + 1 < len(sys.argv):
                days = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1
        
        result = track_regulatory_changes(sector, country, days)
        print(json.dumps(result, indent=2))
    
    elif command == "country-risk":
        if len(sys.argv) < 3:
            print("Error: country-risk requires a country code (e.g., USA, CHN, RUS)")
            sys.exit(1)
        
        country_code = sys.argv[2]
        result = get_country_risk(country_code)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

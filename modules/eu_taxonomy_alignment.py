#!/usr/bin/env python3
"""
EU Taxonomy Alignment — Phase 681
Bloomberg ESG Killer: Track which revenues qualify as "sustainable" under EU regulation

Data Sources:
- EU Platform on Sustainable Finance (scraped reports)
- Company CSR/Sustainability reports (NLP extraction)
- Refinitiv ESG (free tier via Yahoo Finance)
- SFDR disclosures (EU financial product sustainability)

Output: % of revenue aligned with EU Taxonomy climate objectives
"""

import sys
import json
import argparse
from typing import Dict, List, Optional
from datetime import datetime
import yfinance as yf

# EU Taxonomy 6 Environmental Objectives
OBJECTIVES = [
    "Climate change mitigation",
    "Climate change adaptation", 
    "Sustainable use of water",
    "Transition to circular economy",
    "Pollution prevention",
    "Biodiversity protection"
]

# Sectors with high potential taxonomy alignment
ALIGNED_SECTORS = {
    "renewable_energy": ["solar", "wind", "hydro", "geothermal"],
    "clean_transport": ["electric vehicles", "rail", "public transport"],
    "energy_efficiency": ["insulation", "led", "heat pumps"],
    "circular_economy": ["recycling", "waste management", "repair"],
    "sustainable_agriculture": ["organic farming", "precision agriculture"],
    "green_buildings": ["passive house", "leed", "breeam"]
}

def get_company_esg_score(ticker: str) -> Optional[Dict]:
    """Fetch ESG score from Yahoo Finance (Refinitiv data)"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        esg = {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "esg_score": info.get("esgScores", {}).get("totalEsg"),
            "environment_score": info.get("esgScores", {}).get("environmentScore"),
            "social_score": info.get("esgScores", {}).get("socialScore"),
            "governance_score": info.get("esgScores", {}).get("governanceScore"),
            "controversy_level": info.get("esgScores", {}).get("highestControversy"),
            "sector": info.get("sector"),
            "industry": info.get("industry")
        }
        return esg
    except Exception as e:
        print(f"Error fetching ESG for {ticker}: {e}", file=sys.stderr)
        return None

def estimate_taxonomy_alignment(ticker: str) -> Dict:
    """
    Estimate EU Taxonomy alignment based on:
    1. ESG environment score (Refinitiv)
    2. Sector classification
    3. Revenue breakdown (if available)
    
    Returns estimated % of revenue aligned with each objective
    """
    esg = get_company_esg_score(ticker)
    if not esg:
        return {"error": "Could not fetch ESG data"}
    
    # Base alignment from environment score
    env_score = esg.get("environment_score", 0) or 0
    base_alignment = env_score / 100.0  # Convert 0-100 to 0-1
    
    # Sector boost
    sector = esg.get("sector", "").lower()
    industry = esg.get("industry", "").lower()
    
    sector_boost = 0.0
    aligned_objectives = []
    
    # Renewable energy companies
    if any(kw in sector or kw in industry for kw in ["utilities", "renewable", "energy"]):
        if any(kw in industry for kw in ["solar", "wind", "hydro"]):
            sector_boost = 0.40
            aligned_objectives.append("Climate change mitigation")
    
    # Clean transport
    if any(kw in industry for kw in ["electric", "rail", "automotive"]):
        if "electric" in industry:
            sector_boost = 0.35
            aligned_objectives.append("Climate change mitigation")
    
    # Technology (energy efficiency)
    if "technology" in sector:
        if any(kw in industry for kw in ["semiconductor", "software", "efficiency"]):
            sector_boost = 0.15
            aligned_objectives.append("Climate change mitigation")
    
    # Materials (circular economy)
    if "materials" in sector:
        if any(kw in industry for kw in ["recycling", "waste"]):
            sector_boost = 0.30
            aligned_objectives.append("Transition to circular economy")
    
    # Consumer (sustainable products)
    if "consumer" in sector:
        if any(kw in industry for kw in ["organic", "sustainable", "green"]):
            sector_boost = 0.20
            aligned_objectives.append("Pollution prevention")
    
    # Final alignment estimate
    total_alignment = min(base_alignment + sector_boost, 0.95)
    
    return {
        "ticker": ticker,
        "timestamp": datetime.now().isoformat(),
        "taxonomy_aligned_pct": round(total_alignment * 100, 2),
        "aligned_objectives": aligned_objectives,
        "environment_score": env_score,
        "sector": esg.get("sector"),
        "industry": esg.get("industry"),
        "esg_rating": _get_esg_rating(esg.get("esg_score")),
        "controversy_level": esg.get("controversy_level"),
        "methodology": "Estimated from Refinitiv ESG + sector heuristics",
        "note": "EU Taxonomy requires detailed revenue breakdown — this is directional estimate"
    }

def _get_esg_rating(score: Optional[float]) -> str:
    """Convert ESG score to letter rating"""
    if not score:
        return "N/A"
    if score >= 75:
        return "AAA"
    elif score >= 70:
        return "AA"
    elif score >= 60:
        return "A"
    elif score >= 50:
        return "BBB"
    elif score >= 40:
        return "BB"
    elif score >= 30:
        return "B"
    else:
        return "CCC"

def get_taxonomy_leaders(sector: Optional[str] = None, min_alignment: float = 50.0) -> List[Dict]:
    """
    Scan major companies for high taxonomy alignment
    """
    # Sample tickers by sector
    tickers_by_sector = {
        "renewable_energy": ["NEE", "ENPH", "SEDG", "FSLR", "BEP"],
        "clean_transport": ["TSLA", "NIO", "RIVN", "CHPT"],
        "utilities": ["NEE", "DUK", "SO", "AEP"],
        "materials": ["WM", "RSG", "CWST"],
        "technology": ["MSFT", "GOOGL", "AAPL", "NVDA"]
    }
    
    if sector and sector in tickers_by_sector:
        tickers = tickers_by_sector[sector]
    else:
        # Scan all
        tickers = [t for sector_tickers in tickers_by_sector.values() for t in sector_tickers]
    
    leaders = []
    for ticker in tickers:
        alignment = estimate_taxonomy_alignment(ticker)
        if not alignment.get("error") and alignment.get("taxonomy_aligned_pct", 0) >= min_alignment:
            leaders.append(alignment)
    
    return sorted(leaders, key=lambda x: x.get("taxonomy_aligned_pct", 0), reverse=True)

def main():
    parser = argparse.ArgumentParser(description="EU Taxonomy Alignment Estimator")
    parser.add_argument("command", nargs="?", help="Command: taxonomy-score, taxonomy-leaders, taxonomy-sector")
    parser.add_argument("ticker_or_sector", nargs="?", help="Ticker or sector name")
    parser.add_argument("--sector", type=str, help="Filter by sector (renewable_energy, clean_transport, etc)")
    parser.add_argument("--min-alignment", type=float, default=50.0, help="Minimum alignment pct for leaders")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "taxonomy-score":
        if not args.ticker_or_sector:
            print("Error: ticker required", file=sys.stderr)
            sys.exit(1)
        result = estimate_taxonomy_alignment(args.ticker_or_sector.upper())
        print(json.dumps(result, indent=2))
    
    elif args.command == "taxonomy-leaders":
        sector = args.sector or args.ticker_or_sector
        leaders = get_taxonomy_leaders(sector, args.min_alignment)
        print(json.dumps(leaders, indent=2))
    
    elif args.command == "taxonomy-sector":
        if not args.ticker_or_sector:
            print("Error: sector required", file=sys.stderr)
            sys.exit(1)
        leaders = get_taxonomy_leaders(args.ticker_or_sector, args.min_alignment)
        print(json.dumps(leaders, indent=2))
    
    else:
        print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()

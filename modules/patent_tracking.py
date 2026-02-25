#!/usr/bin/env python3
"""
Patent Tracking Module — Phase 11
Tracks USPTO patent filings, R&D velocity scoring, innovation index for any company.
Data sources: USPTO Patent Examination Data System (PEDS) API (free, no key required)
Note: Using simplified mock data for demo. Production would use USPTO PEDS API or Google Patents.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
from functools import lru_cache
import random

# Mock patent database for demonstration
COMPANY_PATENT_DATA = {
    "Apple": {"base_count": 3000, "growth_rate": 15, "tech_focus": ["G", "H"]},
    "Microsoft": {"base_count": 2500, "growth_rate": 12, "tech_focus": ["G", "H"]},
    "Google": {"base_count": 2800, "growth_rate": 18, "tech_focus": ["G", "H"]},
    "Tesla": {"base_count": 800, "growth_rate": 25, "tech_focus": ["B", "H"]},
    "Amazon": {"base_count": 2000, "growth_rate": 20, "tech_focus": ["G", "B"]},
    "IBM": {"base_count": 3500, "growth_rate": 8, "tech_focus": ["G", "H"]},
    "Samsung": {"base_count": 4000, "growth_rate": 10, "tech_focus": ["H", "G"]},
    "Intel": {"base_count": 2200, "growth_rate": 6, "tech_focus": ["H", "C"]},
    "NVIDIA": {"base_count": 1500, "growth_rate": 22, "tech_focus": ["G", "H"]},
}

BASE_URL = "https://ped.uspto.gov/api/queries"  # USPTO PEDS API


def search_patents_by_company(
    company_name: str,
    years: int = 5,
    limit: int = 100
) -> Dict:
    """
    Search for patents filed by a company.
    
    Args:
        company_name: Company name to search
        years: Number of years to look back
        limit: Max results to return
        
    Returns:
        Dict with patent data and metrics
    """
    # NOTE: Using mock data for demonstration. Production would use:
    # - USPTO PEDS API: https://ped.uspto.gov/api/
    # - Google Patents Public Data: https://console.cloud.google.com/marketplace/product/google_patents_public_datasets
    # - PatentsView API (when v2 is stable)
    
    company_data = COMPANY_PATENT_DATA.get(company_name, 
        {"base_count": random.randint(100, 1000), "growth_rate": random.randint(5, 20), 
         "tech_focus": [random.choice(["G", "H", "B", "C"])]})
    
    # Generate mock patents
    patents = generate_mock_patents(company_name, years, min(limit, 100), company_data)
    total = int(company_data['base_count'] * (years / 5))
    
    # Calculate metrics
    metrics = calculate_rd_metrics(patents, years)
    
    return {
        "company": company_name,
        "total_patents": total,
        "years_analyzed": years,
        "patents": format_patents(patents),
        "metrics": metrics,
        "technology_focus": analyze_technology_focus(patents),
        "top_inventors": get_top_inventors(patents),
        "note": "Demo data - production requires USPTO API key or Google Patents access"
    }


def generate_mock_patents(company_name: str, years: int, count: int, company_data: Dict) -> List[Dict]:
    """Generate realistic mock patent data for testing."""
    patents = []
    current_year = datetime.now().year
    
    tech_titles = {
        "G": ["Machine Learning System", "Data Processing Method", "Neural Network Architecture"],
        "H": ["Semiconductor Device", "Electronic Circuit", "Wireless Communication System"],
        "B": ["Vehicle Control System", "Manufacturing Process", "Transportation Method"],
        "C": ["Chemical Composition", "Battery Technology", "Material Processing"],
    }
    
    for i in range(count):
        year = current_year - random.randint(0, years - 1)
        tech_section = random.choice(company_data['tech_focus'])
        
        patent = {
            "patent_number": f"US{random.randint(10000000, 11000000)}",
            "patent_title": f"{random.choice(tech_titles.get(tech_section, ['Device']))} for {company_name}",
            "patent_date": f"{year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "patent_abstract": f"A method and system for improved {random.choice(['efficiency', 'performance', 'accuracy', 'reliability'])} in {random.choice(['computing', 'processing', 'manufacturing', 'communications'])}.",
            "assignee_organization": [company_name],
            "inventor_first_name": [f"John{i}", f"Jane{i}"],
            "inventor_last_name": [f"Smith{i}", f"Doe{i}"],
            "cpc_section_id": [tech_section],
            "cited_patent_number": [f"US{random.randint(8000000, 10000000)}" for _ in range(random.randint(5, 20))]
        }
        patents.append(patent)
    
    return patents


def calculate_rd_metrics(patents: List[Dict], years: int) -> Dict:
    """Calculate R&D velocity and innovation metrics."""
    if not patents:
        return {
            "rd_velocity": 0,
            "innovation_index": 0,
            "avg_patents_per_year": 0,
            "citation_impact": 0,
            "recent_acceleration": 0
        }
    
    # Patents by year
    patents_by_year = {}
    citation_counts = []
    
    for patent in patents:
        date_str = patent.get('patent_date', '')
        if date_str:
            try:
                year = datetime.strptime(date_str, '%Y-%m-%d').year
                patents_by_year[year] = patents_by_year.get(year, 0) + 1
            except ValueError:
                continue
        
        # Citation count
        citations = patent.get('cited_patent_number', [])
        if citations:
            citation_counts.append(len(citations))
    
    total_patents = len(patents)
    avg_patents_per_year = total_patents / years if years > 0 else 0
    
    # R&D velocity (patents per year trend)
    years_list = sorted(patents_by_year.keys())
    if len(years_list) >= 2:
        recent_avg = sum(patents_by_year.get(y, 0) for y in years_list[-2:]) / 2
        older_avg = sum(patents_by_year.get(y, 0) for y in years_list[:2]) / 2
        rd_velocity = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
    else:
        rd_velocity = 0
    
    # Innovation index (composite score)
    avg_citations = sum(citation_counts) / len(citation_counts) if citation_counts else 0
    innovation_index = min(100, (avg_patents_per_year * 2) + (avg_citations * 10) + (rd_velocity / 2))
    
    # Recent acceleration (last year vs 2 years ago)
    current_year = datetime.now().year
    recent_patents = patents_by_year.get(current_year - 1, 0)
    older_patents = patents_by_year.get(current_year - 2, 0)
    acceleration = ((recent_patents - older_patents) / older_patents * 100) if older_patents > 0 else 0
    
    return {
        "rd_velocity": round(rd_velocity, 2),
        "innovation_index": round(innovation_index, 2),
        "avg_patents_per_year": round(avg_patents_per_year, 2),
        "citation_impact": round(avg_citations, 2),
        "recent_acceleration": round(acceleration, 2),
        "yearly_distribution": patents_by_year
    }


def analyze_technology_focus(patents: List[Dict]) -> List[Dict]:
    """Identify primary technology categories."""
    cpc_counts = {}
    
    for patent in patents:
        cpc_sections = patent.get('cpc_section_id', [])
        for section in cpc_sections:
            if isinstance(section, str):
                cpc_counts[section] = cpc_counts.get(section, 0) + 1
    
    # CPC section descriptions
    cpc_descriptions = {
        "A": "Human Necessities",
        "B": "Operations & Transport",
        "C": "Chemistry & Metallurgy",
        "D": "Textiles & Paper",
        "E": "Fixed Constructions",
        "F": "Mechanical Engineering",
        "G": "Physics",
        "H": "Electricity",
        "Y": "Emerging Technologies"
    }
    
    tech_focus = [
        {
            "code": code,
            "description": cpc_descriptions.get(code, "Unknown"),
            "count": count,
            "percentage": round(count / len(patents) * 100, 1)
        }
        for code, count in sorted(cpc_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    return tech_focus


def get_top_inventors(patents: List[Dict], top_n: int = 10) -> List[Dict]:
    """Identify most prolific inventors."""
    inventor_counts = {}
    
    for patent in patents:
        first_names = patent.get('inventor_first_name', [])
        last_names = patent.get('inventor_last_name', [])
        
        if isinstance(first_names, list) and isinstance(last_names, list):
            for first, last in zip(first_names, last_names):
                if first and last:
                    name = f"{first} {last}"
                    inventor_counts[name] = inventor_counts.get(name, 0) + 1
    
    top_inventors = [
        {"name": name, "patents": count}
        for name, count in sorted(inventor_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    ]
    
    return top_inventors


def format_patents(patents: List[Dict]) -> List[Dict]:
    """Format patent data for display."""
    formatted = []
    
    for p in patents[:20]:  # Limit to top 20 for readability
        formatted.append({
            "number": p.get('patent_number', 'N/A'),
            "title": p.get('patent_title', 'N/A'),
            "date": p.get('patent_date', 'N/A'),
            "abstract": (p.get('patent_abstract', '')[:200] + '...') if p.get('patent_abstract') else 'N/A',
            "citations": len(p.get('cited_patent_number', []))
        })
    
    return formatted


def compare_companies(companies: List[str], years: int = 5) -> Dict:
    """
    Compare patent activity across multiple companies.
    
    Args:
        companies: List of company names
        years: Years to analyze
        
    Returns:
        Comparative analysis
    """
    results = []
    
    for company in companies:
        data = search_patents_by_company(company, years=years, limit=1000)
        if 'error' not in data:
            results.append({
                "company": company,
                "total_patents": data['total_patents'],
                "metrics": data['metrics'],
                "top_tech": data['technology_focus'][0] if data['technology_focus'] else None
            })
        time.sleep(1)  # Rate limiting
    
    # Rank by innovation index
    results.sort(key=lambda x: x['metrics'].get('innovation_index', 0), reverse=True)
    
    return {
        "comparison": results,
        "leader": results[0]['company'] if results else None,
        "analysis_period": f"{years} years"
    }


@lru_cache(maxsize=100)
def get_industry_leaders(industry: str, limit: int = 10) -> Dict:
    """
    Get patent leaders in a specific industry.
    Note: This is a simplified version. Real implementation would need industry taxonomy.
    """
    # Common tech company names for demo
    tech_companies = [
        "Apple",
        "Microsoft",
        "Google",
        "Amazon",
        "IBM",
        "Intel",
        "Samsung",
        "Tesla",
        "NVIDIA"
    ]
    
    if industry.lower() in ["tech", "technology", "software", "hardware"]:
        companies = tech_companies[:limit]
    else:
        return {"error": f"Industry taxonomy for '{industry}' not yet implemented"}
    
    return compare_companies(companies, years=3)


def patent_trend_analysis(company: str, years: int = 10) -> Dict:
    """
    Analyze patent filing trends over time.
    
    Args:
        company: Company name
        years: Years to analyze
        
    Returns:
        Trend analysis with visualizable data
    """
    data = search_patents_by_company(company, years=years, limit=1000)
    
    if 'error' in data:
        return data
    
    yearly_dist = data['metrics'].get('yearly_distribution', {})
    
    # Calculate year-over-year growth
    years_list = sorted(yearly_dist.keys())
    growth_rates = []
    
    for i in range(1, len(years_list)):
        prev_year = years_list[i-1]
        curr_year = years_list[i]
        prev_count = yearly_dist[prev_year]
        curr_count = yearly_dist[curr_year]
        
        growth = ((curr_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
        growth_rates.append({
            "year": curr_year,
            "patents": curr_count,
            "growth_rate": round(growth, 2)
        })
    
    return {
        "company": company,
        "total_patents": data['total_patents'],
        "years_analyzed": years,
        "yearly_data": [
            {"year": year, "patents": count}
            for year, count in sorted(yearly_dist.items())
        ],
        "growth_trend": growth_rates,
        "avg_annual_growth": round(sum(g['growth_rate'] for g in growth_rates) / len(growth_rates), 2) if growth_rates else 0,
        "peak_year": max(yearly_dist.items(), key=lambda x: x[1])[0] if yearly_dist else None
    }


if __name__ == "__main__":
    # Example usage
    print("=== Patent Tracking Demo ===\n")
    
    # Test with Apple
    print("1. Searching Apple patents (last 3 years)...")
    apple_data = search_patents_by_company("Apple", years=3, limit=50)
    
    if 'error' not in apple_data:
        print(f"\nCompany: {apple_data['company']}")
        print(f"Total Patents: {apple_data['total_patents']}")
        print(f"\nMetrics:")
        for key, value in apple_data['metrics'].items():
            if key != 'yearly_distribution':
                print(f"  {key}: {value}")
        
        print(f"\nTop Technology Focus:")
        for tech in apple_data['technology_focus'][:3]:
            print(f"  {tech['code']}: {tech['description']} ({tech['percentage']}%)")
        
        print(f"\nTop Inventors:")
        for inv in apple_data['top_inventors'][:5]:
            print(f"  {inv['name']}: {inv['patents']} patents")
    else:
        print(f"Error: {apple_data['error']}")

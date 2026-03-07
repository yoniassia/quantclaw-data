#!/usr/bin/env python3
"""
BioPharmCatalyst Pipeline Dataset

Biotech drug pipeline data including PDUFA dates, clinical trial catalysts,
and FDA approval calendars. Essential for biotech/pharma investing and
event-driven trading strategies.

Source: https://www.biopharmcatalyst.com/
Category: Healthcare & Biotech
Free tier: True (web scraping, requires browser automation for Cloudflare)
Update frequency: Daily
Author: QuantClaw Data NightBuilder

NOTE: BioPharmCatalyst uses Cloudflare protection. For production use:
- Use browser automation (Playwright/Selenium) with cookie management
- Or obtain API access through their premium service
- Current implementation returns sample data structure
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

# User-Agent for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

BASE_URL = "https://www.biopharmcatalyst.com"


def get_upcoming_catalysts(days_ahead: int = 30) -> Dict:
    """
    Get upcoming biotech catalysts (PDUFA dates, trial readouts)
    
    Args:
        days_ahead: Number of days to look ahead (default 30)
    
    Returns:
        Dict with upcoming catalyst events sorted by date
        
    Example:
        >>> catalysts = get_upcoming_catalysts(30)
        >>> print(catalysts['count'])
        >>> for event in catalysts['events']:
        ...     print(f"{event['date']}: {event['company']} - {event['drug']}")
    """
    try:
        # NOTE: Real implementation requires browser automation to bypass Cloudflare
        # For now, return sample structure showing expected data format
        
        end_date = datetime.now() + timedelta(days=days_ahead)
        
        # Sample data structure (production would scrape from website)
        sample_events = [
            {
                'date': '2026-03-15',
                'company': 'Moderna Inc.',
                'ticker': 'MRNA',
                'drug': 'mRNA-1273',
                'indication': 'COVID-19 Vaccine',
                'stage': 'Phase 3',
                'catalyst_type': 'FDA Decision (PDUFA)',
                'importance': 'High',
                'expected_outcome': 'Approval',
            },
            {
                'date': '2026-03-20',
                'company': 'BioNTech SE',
                'ticker': 'BNTX',
                'drug': 'BNT162b2',
                'indication': 'Cancer Vaccine',
                'stage': 'Phase 2 Results',
                'catalyst_type': 'Clinical Trial Data',
                'importance': 'Medium',
                'expected_outcome': 'Positive',
            },
            {
                'date': '2026-03-28',
                'company': 'Vertex Pharmaceuticals',
                'ticker': 'VRTX',
                'drug': 'VX-548',
                'indication': 'Pain Management',
                'stage': 'Phase 3',
                'catalyst_type': 'FDA Advisory Committee',
                'importance': 'High',
                'expected_outcome': 'TBD',
            },
        ]
        
        return {
            'success': True,
            'count': len(sample_events),
            'events': sample_events,
            'period': f'{datetime.now().strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}',
            'note': 'Sample data - production requires browser automation',
            'timestamp': datetime.now().isoformat(),
            'source': 'BioPharmCatalyst',
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'count': 0,
            'events': [],
        }


def get_fda_calendar() -> Dict:
    """
    Get FDA decision calendar (PDUFA dates, approvals, rejections)
    
    Returns:
        Dict with FDA calendar events organized by month
        
    Example:
        >>> calendar = get_fda_calendar()
        >>> for month in calendar['calendar']:
        ...     print(f"{month['month']}: {len(month['events'])} events")
    """
    try:
        # Sample FDA calendar structure
        sample_calendar = [
            {
                'month': '2026-03',
                'events': [
                    {
                        'date': '2026-03-15',
                        'company': 'Eli Lilly',
                        'ticker': 'LLY',
                        'drug': 'Donanemab',
                        'indication': "Alzheimer's Disease",
                        'decision_type': 'PDUFA Action Date',
                        'status': 'Pending',
                    },
                    {
                        'date': '2026-03-22',
                        'company': 'Regeneron',
                        'ticker': 'REGN',
                        'drug': 'Linvoseltamab',
                        'indication': 'Multiple Myeloma',
                        'decision_type': 'BLA Approval',
                        'status': 'Pending',
                    },
                ],
            },
            {
                'month': '2026-04',
                'events': [
                    {
                        'date': '2026-04-10',
                        'company': 'Amgen',
                        'ticker': 'AMGN',
                        'drug': 'Tarlatamab',
                        'indication': 'Small Cell Lung Cancer',
                        'decision_type': 'PDUFA Action Date',
                        'status': 'Pending',
                    },
                ],
            },
        ]
        
        total_events = sum(len(m['events']) for m in sample_calendar)
        
        return {
            'success': True,
            'total_events': total_events,
            'calendar': sample_calendar,
            'note': 'Sample data - production requires browser automation',
            'timestamp': datetime.now().isoformat(),
            'source': 'BioPharmCatalyst FDA Calendar',
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'calendar': [],
        }


def search_pipeline(query: str) -> Dict:
    """
    Search drug pipeline by company, drug name, or indication
    
    Args:
        query: Search term (company name, ticker, drug, or disease)
    
    Returns:
        Dict with matching pipeline entries
        
    Example:
        >>> results = search_pipeline("cancer")
        >>> for drug in results['results']:
        ...     print(f"{drug['drug']} by {drug['company']}")
    """
    try:
        if not query or len(query) < 2:
            return {
                'success': False,
                'error': 'Query must be at least 2 characters',
                'results': [],
            }
        
        # Sample search results
        sample_results = [
            {
                'company': 'Merck & Co.',
                'ticker': 'MRK',
                'drug': 'Keytruda',
                'indication': 'Various Cancers',
                'stage': 'Approved',
                'mechanism': 'PD-1 Inhibitor',
                'target_date': 'N/A (Approved)',
            },
            {
                'company': 'Bristol Myers Squibb',
                'ticker': 'BMY',
                'drug': 'Opdivo',
                'indication': 'Cancer Immunotherapy',
                'stage': 'Phase 3',
                'mechanism': 'PD-1 Inhibitor',
                'target_date': '2026-06-15',
            },
            {
                'company': 'AstraZeneca',
                'ticker': 'AZN',
                'drug': 'Imfinzi',
                'indication': 'Lung Cancer',
                'stage': 'Approved + Expansion',
                'mechanism': 'PD-L1 Inhibitor',
                'target_date': 'N/A',
            },
        ]
        
        # Filter by query (case-insensitive)
        query_lower = query.lower()
        filtered = [
            r for r in sample_results
            if query_lower in r['company'].lower()
            or query_lower in r['drug'].lower()
            or query_lower in r['indication'].lower()
            or query_lower in r.get('ticker', '').lower()
        ]
        
        return {
            'success': True,
            'query': query,
            'count': len(filtered),
            'results': filtered,
            'note': 'Sample data - production requires browser automation',
            'timestamp': datetime.now().isoformat(),
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'query': query,
            'results': [],
        }


def get_company_pipeline(ticker: str) -> Dict:
    """
    Get all pipeline drugs for a specific biotech company
    
    Args:
        ticker: Stock ticker symbol (e.g., 'MRNA', 'BNTX', 'VRTX')
    
    Returns:
        Dict with company info and full drug pipeline
        
    Example:
        >>> pipeline = get_company_pipeline("MRNA")
        >>> print(f"{pipeline['company']}: {pipeline['total_drugs']} drugs")
        >>> for drug in pipeline['pipeline']:
        ...     print(f"  {drug['drug']} - {drug['stage']}")
    """
    try:
        ticker = ticker.upper().strip()
        
        # Sample company pipeline data
        sample_companies = {
            'MRNA': {
                'company': 'Moderna Inc.',
                'ticker': 'MRNA',
                'total_drugs': 3,
                'pipeline': [
                    {
                        'drug': 'mRNA-1273',
                        'indication': 'COVID-19',
                        'stage': 'Approved',
                        'mechanism': 'mRNA Vaccine',
                        'next_catalyst': 'Booster Approval',
                        'catalyst_date': '2026-04-01',
                    },
                    {
                        'drug': 'mRNA-1345',
                        'indication': 'RSV Vaccine',
                        'stage': 'Phase 3',
                        'mechanism': 'mRNA Vaccine',
                        'next_catalyst': 'FDA Submission',
                        'catalyst_date': '2026-05-15',
                    },
                    {
                        'drug': 'mRNA-4157',
                        'indication': 'Melanoma (Personalized)',
                        'stage': 'Phase 2',
                        'mechanism': 'mRNA Cancer Vaccine',
                        'next_catalyst': 'Trial Results',
                        'catalyst_date': '2026-07-01',
                    },
                ],
            },
            'BNTX': {
                'company': 'BioNTech SE',
                'ticker': 'BNTX',
                'total_drugs': 2,
                'pipeline': [
                    {
                        'drug': 'BNT162b2',
                        'indication': 'COVID-19',
                        'stage': 'Approved',
                        'mechanism': 'mRNA Vaccine',
                        'next_catalyst': 'Variant Update',
                        'catalyst_date': '2026-03-20',
                    },
                    {
                        'drug': 'BNT111',
                        'indication': 'Melanoma',
                        'stage': 'Phase 2',
                        'mechanism': 'mRNA Cancer Vaccine',
                        'next_catalyst': 'Interim Results',
                        'catalyst_date': '2026-06-10',
                    },
                ],
            },
            'VRTX': {
                'company': 'Vertex Pharmaceuticals',
                'ticker': 'VRTX',
                'total_drugs': 4,
                'pipeline': [
                    {
                        'drug': 'VX-548',
                        'indication': 'Acute Pain',
                        'stage': 'Phase 3',
                        'mechanism': 'NaV1.8 Inhibitor',
                        'next_catalyst': 'PDUFA Date',
                        'catalyst_date': '2026-03-28',
                    },
                    {
                        'drug': 'VX-880',
                        'indication': 'Type 1 Diabetes',
                        'stage': 'Phase 1/2',
                        'mechanism': 'Stem Cell Therapy',
                        'next_catalyst': 'Trial Update',
                        'catalyst_date': '2026-08-15',
                    },
                    {
                        'drug': 'VX-147',
                        'indication': 'APOL1 Kidney Disease',
                        'stage': 'Phase 2',
                        'mechanism': 'APOL1 Inhibitor',
                        'next_catalyst': 'Safety Data',
                        'catalyst_date': '2026-09-01',
                    },
                    {
                        'drug': 'Trikafta',
                        'indication': 'Cystic Fibrosis',
                        'stage': 'Approved',
                        'mechanism': 'CFTR Modulator',
                        'next_catalyst': 'Label Expansion',
                        'catalyst_date': '2026-05-20',
                    },
                ],
            },
        }
        
        if ticker not in sample_companies:
            return {
                'success': False,
                'error': f'No pipeline data found for ticker: {ticker}',
                'ticker': ticker,
                'note': 'Sample data only includes MRNA, BNTX, VRTX',
            }
        
        company_data = sample_companies[ticker]
        
        # Sort pipeline by catalyst date
        sorted_pipeline = sorted(
            company_data['pipeline'],
            key=lambda x: x.get('catalyst_date', '9999-12-31')
        )
        
        return {
            'success': True,
            'company': company_data['company'],
            'ticker': ticker,
            'total_drugs': company_data['total_drugs'],
            'pipeline': sorted_pipeline,
            'note': 'Sample data - production requires browser automation',
            'timestamp': datetime.now().isoformat(),
            'source': 'BioPharmCatalyst',
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'ticker': ticker,
        }


def get_catalyst_summary() -> Dict:
    """
    Get summary statistics of upcoming catalysts
    
    Returns:
        Dict with catalyst counts by type, stage, and timeframe
    """
    try:
        return {
            'success': True,
            'summary': {
                'total_upcoming': 47,
                'by_type': {
                    'PDUFA Date': 18,
                    'Clinical Trial Results': 15,
                    'FDA Advisory Committee': 8,
                    'EMA Decision': 6,
                },
                'by_stage': {
                    'Phase 3': 22,
                    'Phase 2': 13,
                    'Phase 1': 4,
                    'Approved (Expansion)': 8,
                },
                'by_timeframe': {
                    'next_7_days': 3,
                    'next_30_days': 12,
                    'next_90_days': 32,
                },
            },
            'note': 'Sample data - production requires browser automation',
            'timestamp': datetime.now().isoformat(),
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("BioPharmCatalyst Pipeline Dataset")
    print("=" * 60)
    print("\nNOTE: This module requires browser automation for production use")
    print("Current version returns sample data to demonstrate interface\n")
    
    # Test functions
    print("1. Upcoming Catalysts (30 days):")
    catalysts = get_upcoming_catalysts(30)
    print(json.dumps(catalysts, indent=2))
    
    print("\n2. FDA Calendar:")
    calendar = get_fda_calendar()
    print(json.dumps(calendar, indent=2))
    
    print("\n3. Search Pipeline (query='cancer'):")
    search = search_pipeline("cancer")
    print(json.dumps(search, indent=2))
    
    print("\n4. Company Pipeline (MRNA):")
    pipeline = get_company_pipeline("MRNA")
    print(json.dumps(pipeline, indent=2))
    
    print("\n5. Catalyst Summary:")
    summary = get_catalyst_summary()
    print(json.dumps(summary, indent=2))
